"""AI 答案采样：把问题库打到各个引擎上，量化「品牌在 AI 答案里的可见性」。

三种采样模式，证据等级从高到低：
  api      有 API 的引擎直接跑（DeepSeek / 千问 / Kimi / 任意 OpenAI 兼容端点）
  browser  网页端/App 端由 Claude 用浏览器工具逐条采，结果 import 回来
  manual   导出问题清单，人工粘贴答案后 import

重要口径：API 结果 ≠ 网页端结果。同一产品 Web 与 App 的信源集合都有系统性差异
（CN-GEO 论文结论），所以每个平台+终端单独记录，绝不混算。

产物：work/<slug>/samples/<日期>.jsonl + work/<slug>/metrics/<日期>.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests

import geolib as G

# 平台注册表：code -> 配置。market 决定这个平台该问哪一套问题库。
# 观测集合（2026-07 定）：国内 = 智谱GLM/豆包/DeepSeek/Kimi/MiniMax/纳米AI/百度AI；
# 海外 = Gemini/ChatGPT/Claude/Grok/Perplexity。纳米AI、百度AI 无公开 API，走人工采样。
PROVIDERS = {
    # ---------------- 国内 ----------------
    "glm": {
        "name": "智谱GLM", "market": "cn",
        "base": "https://open.bigmodel.cn/api/paas/v4",
        # 采样默认用各家的轻量档：测的是「模型认不认识这个品牌」，不是推理质量，口径一致优先。
        "model": os.environ.get("GLM_MODEL", "glm-4-flash"),
        "model_env": "GLM_MODEL",
        "key_env": "ZHIPUAI_API_KEY",
        "search": False,
        "note": "OpenAI 兼容端点，不联网；智谱清言网页版联网行为需人工采",
    },
    "doubao": {
        # 火山方舟。联网要在控制台开通「内容插件」（console.volcengine.com/common-buy/CC_content_plugin）。
        # 没开通时自动降级成不联网采样，不会中断整期。
        "name": "豆包(方舟API)", "market": "cn",
        "protocol": "ark",
        "base": "https://ark.cn-beijing.volces.com/api/v3",
        "model": os.environ.get("ARK_MODEL", "doubao-seed-1-6-250615"),
        "model_env": "ARK_MODEL",
        "key_env": "ARK_API_KEY",
        "search": True,
        "note": "开通内容插件后走 responses+web_search 并返回引用；否则退回参数化知识采样",
    },
    "deepseek": {
        "name": "DeepSeek", "market": "cn",
        "base": "https://api.deepseek.com/v1",
        "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "model_env": "DEEPSEEK_MODEL",
        "key_env": "DEEPSEEK_API_KEY",
        "search": False,
        "note": "官方 API 不联网，测的是模型参数化知识里的品牌认知",
    },
    "kimi": {
        "name": "Kimi", "market": "cn",
        "base": "https://api.moonshot.cn/v1",
        "model": os.environ.get("MOONSHOT_MODEL", "kimi-k2-0905-preview"),
        "model_env": "MOONSHOT_MODEL",
        "key_env": "MOONSHOT_API_KEY",
        "search": False,
        "note": "默认不联网；需要联网请在网页端采样",
    },
    "minimax": {
        "name": "MiniMax", "market": "cn",
        "base": "https://api.minimaxi.com/v1",
        "model": os.environ.get("MINIMAX_MODEL", "MiniMax-M2"),
        "model_env": "MINIMAX_MODEL",
        "key_env": "MINIMAX_API_KEY",
        "search": False,
        "note": "OpenAI 兼容端点，不联网；海螺 AI 网页版需人工采",
    },
    # ---------------- 海外 ----------------
    "gemini": {
        "name": "Gemini", "market": "global",
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "model_env": "GEMINI_MODEL",
        "key_env": "GEMINI_API_KEY",
        "search": False,
        "note": "OpenAI 兼容端点不带 grounding；Google AI Overview 要在网页端采",
    },
    "openai": {
        "name": "OpenAI(ChatGPT)", "market": "global",
        "base": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "model_env": "OPENAI_MODEL",
        "key_env": "OPENAI_API_KEY",
        "search": False,
        "note": "Chat Completions 默认不联网；ChatGPT 网页版的搜索行为要另外采",
    },
    "claude": {
        # Anthropic 原生 Messages API：响应是 content 块列表，不是 OpenAI 的 choices，走专用协议。
        "name": "Claude", "market": "global",
        "protocol": "anthropic",
        "base": "https://api.anthropic.com/v1",
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        "model_env": "ANTHROPIC_MODEL",
        "key_env": "ANTHROPIC_API_KEY",
        "search": False,
        "note": "API 不联网；Claude 网页版（开 Web Search）需人工采",
    },
    "grok": {
        "name": "Grok", "market": "global",
        "base": "https://api.x.ai/v1",
        "model": os.environ.get("GROK_MODEL", "grok-3-mini"),
        "model_env": "GROK_MODEL",
        "key_env": "XAI_API_KEY",
        "search": False,
        "note": "xAI API，不联网；X 内嵌的 Grok 联网行为需在网页端采",
    },
    "perplexity": {
        "name": "Perplexity", "market": "global",
        "base": "https://api.perplexity.ai",
        "model": os.environ.get("PERPLEXITY_MODEL", "sonar"),
        "model_env": "PERPLEXITY_MODEL",
        "key_env": "PERPLEXITY_API_KEY",
        "search": True,
        "note": "原生联网并返回 citations，海外采样里证据质量最好的一个",
    },
}

# 没有公开联网问答 API 的平台，只能浏览器/人工采
MANUAL_ONLY = {
    "nano_ai": ("纳米AI搜索（360）", "cn"),
    "baidu": ("百度 AI 搜索", "cn"),
    "doubao_app": ("豆包 App / 网页版（与方舟 API 结果不同，需分开采）", "cn"),
    "chatgpt": ("ChatGPT 网页版（开 Search）", "global"),
    "claude_web": ("Claude 网页版（开 Web Search）", "global"),
}

# ------------------------------------------------------------ 302.AI 统一 Key 模式
# 一把 Key 跑通 9 个 LLM 平台。设 AI302AI_MODE=1 且填 AI302AI_API_KEY 后，
# sample/aggregate 全部走 https://api.302ai.cn/v1（国内端点·OpenAI 兼容 + Anthropic 兼容）。
# 默认模型按"2026-08 最新稳定 + 轻量"原则选（采样是高频轻任务）。
# 旗舰版本在 .env 里用 AI302AI_*_MODEL 覆盖即可。
# 详见 docs/302ai-integration-research.md
AI302AI_BASE = "https://api.302ai.cn/v1"
# code -> 默认模型 + 覆盖用的 env 名；未列出的平台不支持 302.AI 替代
AI302AI_PROVIDERS = {
    # GLM：智谱最新是 glm-5.2（旗舰）/ glm-4.7-flashx（轻量），采样选轻量档
    "glm":        {"model": "glm-4.7-flashx",             "model_env": "AI302AI_GLM_MODEL"},
    # Doubao：字节最新是 seed-2-1（2026-06-28），lite 太弱，选 turbo 平衡
    "doubao":     {"model": "doubao-seed-2-1-turbo-260628","model_env": "AI302AI_ARK_MODEL"},
    # DeepSeek：v4-flash 是 2026 最新轻量档（v4-pro 太重，采样不划算）
    "deepseek":   {"model": "deepseek-v4-flash",          "model_env": "AI302AI_DEEPSEEK_MODEL"},
    # Kimi：2026 月之暗面最新是 kimi-k3（已非 preview）
    "kimi":       {"model": "kimi-k3",                    "model_env": "AI302AI_KIMI_MODEL"},
    # MiniMax：M3 是我自己（跑这个 agent 的），采样用上一代 M2.7
    "minimax":    {"model": "MiniMax-M2.7",               "model_env": "AI302AI_MINIMAX_MODEL"},
    # Gemini：3.5-flash 是 2026 稳定轻量档（3.6-flash 偏新可能不稳）
    "gemini":     {"model": "gemini-3.5-flash",           "model_env": "AI302AI_GEMINI_MODEL"},
    # OpenAI：2026-03 发布的 gpt-5.4-mini 是当前最快轻量档
    "openai":     {"model": "gpt-5.4-mini",               "model_env": "AI302AI_OPENAI_MODEL"},
    # Claude：sonnet-5 是 2026 当前主力（opus-5 太贵，采样用 sonnet 够）
    "claude":     {"model": "claude-sonnet-5",            "model_env": "AI302AI_CLAUDE_MODEL"},
    # Grok：4.5 刚出（贵），4.1 是 2026 性价比档
    "grok":       {"model": "grok-4.1",                  "model_env": "AI302AI_GROK_MODEL"},
    # Perplexity：sonar 仍是 2026 基础联网档，pro/reasoning 在 .env 覆盖
    "perplexity": {"model": "sonar",                      "model_env": "AI302AI_PERPLEXITY_MODEL"},
}


def _ai302ai_enabled() -> bool:
    """302.AI 模式开关：AI302AI_MODE=1 且 Key 存在才真正开启。

    安全护栏：设了 AI302AI_MODE=1 但 Key 留空时，**不会静默失败**——
    而是警告一次并自动回退到原生 Key 模式（向下兼容）。
    重复调用只警告一次。
    """
    flag = os.environ.get("AI302AI_MODE", "").strip().lower() in ("1", "true", "yes", "on")
    if not flag:
        return False
    if not os.environ.get("AI302AI_API_KEY", "").strip():
        # 用 getattr 兜底：函数对象不能直接 .属性 = 值（首次会 AttributeError）
        if not getattr(_ai302ai_enabled, "_warned", False):
            print(
                "[geolook] ⚠  AI302AI_MODE=1 但 AI302AI_API_KEY 为空 —— "
                "302.AI 模式已自动关闭，回退到「模式 B：原生 Key」。\n"
                "[geolook]    要启用 302.AI：编辑 .env 填入 AI302AI_API_KEY=sk-...\n"
                "[geolook]    想直连原平台：把 AI302AI_MODE 改为 0，再填下方原生 Key。",
                file=sys.stderr,
            )
            _ai302ai_enabled._warned = True  # 后续调用不再警告
        return False
    return True


# ------------------------------------------------------------ 302.AI 多源搜索
# 一把 Key + 9 个搜索 provider。详见 .claude/skills/302ai-cli-skill/references/search.md
# 端点：POST https://api.302.ai/302/general/search
# 默认按市场分流：cn → bocha（中文质量好），global → tavily（英文质量好）
AI302AI_SEARCH_URL = "https://api.302ai.cn/302/general/search"
# provider -> {market, categories, time_ranges}，描述每个 provider 的能力/适配市场
AI302AI_SEARCH_PROVIDERS = {
    "bocha":          {"market": "cn",    "default_for": "cn",
                       "categories": [], "time_ranges": ["oneDay", "oneWeek", "oneMonth", "oneYear"],
                       "desc": "博查：中文搜索质量最好"},
    "tavily":         {"market": "global", "default_for": "global",
                       "categories": ["general", "news"],
                       "time_ranges": ["day", "week", "month", "year"],
                       "desc": "Tavily：英文/海外搜索质量最好"},
    "unifuncs":       {"market": "cn",
                       "categories": [],
                       "time_ranges": ["Day", "Week", "Month", "Year"],
                       "desc": "UniFuncs：中文深度调研（与问答主端共用）"},
    "perplexity":     {"market": "global",
                       "categories": [],
                       "time_ranges": [],
                       "desc": "Perplexity：直接拿搜索增强回答（与 perplexity 平台同源）"},
    "firecrawl":      {"market": "global",
                       "categories": [],
                       "time_ranges": ["day", "hour", "week", "month", "year"],
                       "desc": "Firecrawl：带整页爬取（可拿全文做内容分析）"},
    "exa":            {"market": "global",
                       "categories": ["company", "research paper", "news", "pdf", "github", "tweet", "personal site", "linkedin profile", "financial report"],
                       "time_ranges": [],
                       "desc": "Exa：高质量检索（公司/论文/GitHub/推特）"},
    "metaso":         {"market": "global",
                       "categories": ["webpage", "document", "scholar", "podcast", "video", "image"],
                       "time_ranges": [],
                       "desc": "Metaso：学术/播客/视频（深度研究）"},
    "search1_search": {"market": "global",
                       "categories": ["google", "bing", "duckduckgo", "yahoo", "youtube", "x", "reddit", "github", "arxiv", "wechat", "bilibili", "imdb", "wikipedia"],
                       "time_ranges": ["day", "month", "year"],
                       "desc": "Search1 聚合：13 个平台（google/微信/b站/github/arxiv 等）"},
    "search1_news":   {"market": "global",
                       "categories": ["google", "bing", "duckduckgo", "yahoo", "youtube", "x", "reddit", "github", "arxiv", "wechat", "bilibili", "imdb", "wikipedia"],
                       "time_ranges": ["day", "month", "year"],
                       "desc": "Search1 资讯版（同上但偏新闻）"},
}


def search(query: str, provider: str = "tavily", count: int = 5,
           category: str = None, time_range: str = None,
           include_domains: str = None, exclude_domains: str = None,
           timeout: int = 30) -> dict:
    """302.AI 多源搜索：9 个 provider，AI302AI_MODE=1 时启用。
    返回结构与 ask() 一致：{"ok", "results": [{title,url,snippet,content,...}], "provider", "count", "response_time"}。
    """
    if not _ai302ai_enabled():
        return {"ok": False, "error": "302.AI 模式未开启（需设 AI302AI_MODE=1 + AI302AI_API_KEY）", "results": []}
    if provider not in AI302AI_SEARCH_PROVIDERS:
        return {"ok": False, "error": f"未知的搜索 provider：{provider!r}，可选：{list(AI302AI_SEARCH_PROVIDERS)}", "results": []}
    body = {"query": query, "provider": provider, "max_results": count, "include_images": False}
    if category:
        body["category"] = category
    if time_range:
        body["time_range"] = time_range
    if include_domains:
        body["include_domains"] = include_domains
    if exclude_domains:
        body["exclude_domains"] = exclude_domains
    try:
        r = requests.post(
            AI302AI_SEARCH_URL,
            headers={"Authorization": f"Bearer {os.environ.get('AI302AI_API_KEY','')}", "Content-Type": "application/json"},
            json=body, timeout=timeout,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:300]}", "results": []}
        data = r.json()
        # 兼容成功格式（results[]）与原始格式（search_results[]）
        results = data.get("results") or data.get("search_results") or []
        return {
            "ok": True,
            "results": results,
            "provider": data.get("provider", provider),
            "count": data.get("count", len(results)),
            "response_time": data.get("response_time", 0),
            "request_id": data.get("request_id"),
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "results": []}


def search_default_provider(market: str) -> str:
    """按市场返回默认搜索 provider：cn→bocha，global→tavily。"""
    for code, meta in AI302AI_SEARCH_PROVIDERS.items():
        if meta.get("default_for") == market:
            return code
    return "tavily"


def search_then_ask(platform: str, question: str,
                    search_provider: str = None, count: int = 5,
                    timeout: int | None = None, **search_kwargs) -> dict:
    """先 search 再 ask：把 top N 结果作为上下文拼到 prompt，让 LLM 基于搜索结果回答。
    这是 302.AI 模式下豆包 ark 联网的替代方案。
    搜索失败会自动退回纯 LLM 调用（不阻塞业务）。

    timeout：单次 LLM 调用超时。缺省读 AI302AI_SEARCH_ASK_TIMEOUT（默认 45s）。
    历史教训：这里一度硬编码 60s，且超时重试 2 次，每题失败约 3 分钟，
    且 ask() 传进来的 timeout 被吞掉——已修复为可传参可配。
    """
    if timeout is None:
        timeout = int(os.environ.get("AI302AI_SEARCH_ASK_TIMEOUT", "45"))
    market = market_of(platform)
    if not search_provider:
        # 允许按平台/项目级别覆盖默认
        search_provider = os.environ.get("AI302AI_SEARCH_PROVIDER") or search_default_provider(market)
    sr = search(question, search_provider, count=count, **search_kwargs)
    # 直接走 chat/completions，避免再次进入 ask() 触发 ark→search_then_ask 无限递归
    p, key = _pick_endpoint(platform)
    p_no_ark = dict(p)
    p_no_ark.pop("protocol", None)  # 强制 chat 协议
    if not sr.get("ok") or not sr.get("results"):
        # 搜索失败/无结果 → 退回纯 LLM 调用（chat 协议，不走 ark）
        res = _ask_chat(p_no_ark, key, question, timeout=timeout)
        if res.get("ok"):
            res["search_provider"] = search_provider
            res["search_citations"] = []
            res["search_skipped"] = sr.get("error", "no results")
        return res
    # 把搜索结果拼成上下文字符串
    lines = []
    for i, r in enumerate(sr["results"][:count], 1):
        title = r.get("title") or ""
        url = r.get("url") or ""
        snippet = r.get("snippet") or (r.get("content") or "")[:300]
        if not snippet and not title:
            continue
        lines.append(f"[{i}] {title}\n    {url}\n    {snippet.strip()[:300]}")
    ctx = "\n\n".join(lines)
    enhanced_q = (
        f"以下是与问题相关的网络搜索结果（按相关度排序）。请基于这些结果回答问题，"
        f"必要时用 [1][2] 这样的角标引用来源。\n\n"
        f"# 搜索结果（{search_provider}）\n{ctx}\n\n"
        f"# 用户问题\n{question}"
    )
    res = _ask_chat(p_no_ark, key, enhanced_q, timeout=timeout)
    if res.get("ok"):
        res["search_provider"] = search_provider
        res["search_citations"] = [
            {"url": r.get("url"), "title": r.get("title")}
            for r in sr["results"][:count] if r.get("url")
        ]
    return res


def _pick_endpoint(platform: str) -> tuple[dict, str]:
    """返回 (运行时 p 视图, key)。
    302.AI 模式下：base 强制 AI302AI_BASE，model 用 AI302AI_*_MODEL 覆盖，protocol 沿用（ark/anthropic）。
    原版模式下：完全沿用 PROVIDERS 里的配置。
    """
    p = dict(PROVIDERS[platform])  # 复制避免污染全局
    if _ai302ai_enabled():
        a = AI302AI_PROVIDERS.get(platform)
        if a:
            p["base"] = AI302AI_BASE
            p["model"] = os.environ.get(a["model_env"], a["model"])
            key = os.environ.get("AI302AI_API_KEY", "")
            p["key_env"] = "__AI302AI__"  # 给 available()/ask() 看的占位
            return p, key
    return p, os.environ.get(p.get("key_env", ""), "")


def market_of(platform: str) -> str:
    if platform in PROVIDERS:
        return PROVIDERS[platform]["market"]
    if platform in MANUAL_ONLY:
        return MANUAL_ONLY[platform][1]
    # 未识别的平台代码（多半是笔误）：绝不默认并入国内，标记 unknown 不进任何市场统计
    G.info(f"未识别的平台代码 {platform!r}，市场标记为 unknown（不进国内/海外统计）")
    return "unknown"


def label_of(platform: str) -> str:
    if platform in PROVIDERS:
        return PROVIDERS[platform]["name"]
    if platform in MANUAL_ONLY:
        return MANUAL_ONLY[platform][0]
    return platform


def questions_for(cfg: dict, platform: str) -> list[dict]:
    """问题按市场路由：中文问题不打海外平台，英文问题不打国内平台。

    问题没写 market 的，按项目 market 处理；项目是 both 时视为通用问题，两边都问。
    """
    m = market_of(platform)
    out = []
    for q in cfg.get("questions", []):
        qm = q.get("market") or cfg.get("market", "cn")
        if qm in ("both", m):
            out.append(q)
    return out


def available(platform: str) -> bool:
    p = PROVIDERS.get(platform)
    if not p:
        return False
    if _ai302ai_enabled():
        return bool(os.environ.get("AI302AI_API_KEY")) and platform in AI302AI_PROVIDERS
    return bool(os.environ.get(p["key_env"]))


def ask_ark(p: dict, key: str, question: str, timeout: int) -> dict:
    """火山方舟。优先用 Responses API + web_search；账号没开通内容插件就降级成普通对话。"""
    H = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = requests.post(f"{p['base']}/responses", headers=H,
                          json={"model": p["model"], "input": question,
                                "tools": [{"type": "web_search"}]}, timeout=timeout)
        if r.status_code == 200:
            d = r.json()
            answer, refs = "", []
            for item in d.get("output") or []:
                for c in item.get("content") or []:
                    if c.get("type") in ("output_text", "text"):
                        answer += c.get("text", "")
                    for ann in c.get("annotations") or []:
                        if ann.get("url"):
                            refs.append({"url": ann["url"], "title": ann.get("title", "")})
                for res in item.get("results") or []:
                    if isinstance(res, dict) and res.get("url"):
                        refs.append({"url": res["url"], "title": res.get("title", "")})
            if answer:
                seen = set()
                refs = [c for c in refs if not (c["url"] in seen or seen.add(c["url"]))]
                return {"ok": True, "answer": answer, "citations": refs,
                        "raw_model": p["model"], "searched": True}
        elif "ToolNotOpen" not in r.text:
            return {"ok": False, "answer": "", "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception:  # noqa: BLE001
        pass  # 降级重试

    try:  # 降级：不联网的普通对话
        r = requests.post(f"{p['base']}/chat/completions", headers=H,
                          json={"model": p["model"],
                                "messages": [{"role": "user", "content": question}]}, timeout=timeout)
        if r.status_code != 200:
            return {"ok": False, "answer": "", "error": f"HTTP {r.status_code}: {r.text[:300]}"}
        d = r.json()
        return {"ok": True, "answer": d["choices"][0]["message"].get("content") or "",
                "citations": [], "raw_model": p["model"], "searched": False}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "answer": "", "error": f"{type(e).__name__}: {e}"}


def ask_anthropic(p: dict, key: str, question: str, timeout: int) -> dict:
    """Anthropic 原生 Messages API：响应是 content 块列表；安全分类器拒答走 stop_reason。"""
    delays = (1, 3)
    for attempt in range(len(delays) + 1):
        try:
            r = requests.post(
                f"{p['base']}/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                # max_tokens 4096：品牌认知问答的自然长度以内，同时护住 120s 请求超时
                json={"model": p["model"], "max_tokens": 4096,
                      "messages": [{"role": "user", "content": question}]},
                timeout=timeout,
            )
            if r.status_code != 200:
                if (r.status_code == 429 or r.status_code >= 500) and attempt < len(delays):
                    time.sleep(delays[attempt])
                    continue
                return {"ok": False, "answer": "", "error": f"HTTP {r.status_code}: {r.text[:300]}"}
            d = r.json()
            if d.get("stop_reason") == "refusal":
                return {"ok": False, "answer": "", "error": "安全分类器拒答（stop_reason=refusal）"}
            answer = "".join(b.get("text", "") for b in d.get("content", [])
                             if b.get("type") == "text")
            return {"ok": True, "answer": answer, "citations": [],
                    "raw_model": d.get("model", p["model"])}
        except requests.exceptions.Timeout as e:
            if attempt < len(delays):
                time.sleep(delays[attempt])
                continue
            return {"ok": False, "answer": "", "error": f"{type(e).__name__}: {e}"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "answer": "", "error": f"{type(e).__name__}: {e}"}


def ask(platform: str, question: str, timeout: int = 120) -> dict:
    p, key = _pick_endpoint(platform)
    if not key:
        if _ai302ai_enabled():
            return {"ok": False, "answer": "", "error": "缺少环境变量 AI302AI_API_KEY（或未启用 302.AI 模式）"}
        return {"ok": False, "answer": "", "error": f"缺少环境变量 {p['key_env']}"}
    if p.get("protocol") == "ark":
        # 302.AI 模式下没有 ark 协议的 Responses+web_search；
        # 自动用 search_then_ask 走"302.AI 搜索 + 任何 LLM"组合补回联网能力
        if _ai302ai_enabled():
            return search_then_ask(platform, question, timeout=timeout)
        return ask_ark(p, key, question, timeout)
    if p.get("protocol") == "anthropic":
        return ask_anthropic(p, key, question, timeout)
    return _ask_chat(p, key, question, timeout)


def _ask_chat(p: dict, key: str, question: str, timeout: int) -> dict:
    """OpenAI 兼容 chat/completions：含联网搜索结果在 search_info / search_results / citations 字段的归一化。"""
    body = {
        "model": p["model"],
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
    }
    body.update(p.get("extra", {}))
    delays = (1, 3)  # 超时/429/5xx 指数退避重试 2 次；其他错误（4xx 等）不重试
    for attempt in range(len(delays) + 1):
        try:
            r = requests.post(
                f"{p['base']}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=body,
                timeout=timeout,
            )
            if r.status_code != 200:
                err = {"ok": False, "answer": "", "error": f"HTTP {r.status_code}: {r.text[:300]}"}
                if (r.status_code == 429 or r.status_code >= 500) and attempt < len(delays):
                    time.sleep(delays[attempt])
                    continue
                return err
            data = r.json()
            msg = data["choices"][0]["message"]
            answer = msg.get("content") or ""
            # 各家把联网来源放在不同字段：千问 search_info、Perplexity citations/search_results
            refs = []
            for item in (data.get("search_info") or {}).get("search_results", []) or []:
                if item.get("url"):
                    refs.append({"url": item["url"], "title": item.get("title", "")})
            for item in data.get("search_results") or []:
                if isinstance(item, dict) and item.get("url"):
                    refs.append({"url": item["url"], "title": item.get("title", "")})
            for u in data.get("citations") or []:
                if isinstance(u, str):
                    refs.append({"url": u, "title": ""})
            seen = set()
            refs = [c for c in refs if not (c["url"] in seen or seen.add(c["url"]))]
            return {"ok": True, "answer": answer, "citations": refs, "raw_model": data.get("model", p["model"])}
        except requests.exceptions.Timeout as e:
            if attempt < len(delays):
                time.sleep(delays[attempt])
                continue
            return {"ok": False, "answer": "", "error": f"{type(e).__name__}: {e}"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "answer": "", "error": f"{type(e).__name__}: {e}"}


# ------------------------------------------------------------ 答案解析

URL_RE = re.compile(r"https?://[^\s\)\]\"'，。；]+")


def entities_of(cfg: dict) -> tuple[list[str], dict[str, list[str]]]:
    """返回 (全部候选实体名, {规范名: 别名列表})"""
    alias = {}
    b = cfg["brand"]
    alias[b["name"]] = [b["name"]] + list(b.get("aliases", []) or [])
    for c in cfg.get("competitors", []) or []:
        alias[c["name"]] = [c["name"]] + list(c.get("aliases", []) or [])
    return list(alias.keys()), alias


_LATIN = re.compile(r"[A-Za-z0-9]")
_NEG_RE = re.compile(r"不是|并非|不属于|不同于|not |isn't|aren't", re.IGNORECASE)
_SENT_END = "。！？!?\n"

# 负面语境线索：只在品牌名附近窗口内找，命中≠负面定性，只标「疑似负面」进人工复核。
# 词表故意保守——误报会浪费复核时间，漏报还有样本回放兜底。
NEG_CUES = re.compile(
    r"不推荐|避雷|缺点|劣势|投诉|差评|跑路|骗局|割韭菜|不靠谱|慎用|翻车|已倒闭|停止运营|维权|退款难"
    r"|not recommended|avoid|scam|complaints?|lawsuit|shut ?down|worse than|downsides?",
    re.IGNORECASE)


def _alias_spans(text: str, alias: str) -> list[tuple[int, int]]:
    """别名命中区间。

    边界策略（权衡）：跨文种相邻（CJK↔拉丁）是天然分词边界，不算词延续；
    只有「拉丁接拉丁」才是真延续。所以：
    - 别名的拉丁侧边缘加 lookaround 排除 [A-Za-z0-9]，防 "AIGC" 命中 "AIGCLINK"；
      CJK 侧边缘不查——「推荐AIGC」「AIGCLINK定制家很好用」都是正常命中。
    - 纯 CJK 别名保持子串匹配：中文没有空格分词，右侧是 CJK 不代表另一个词。
      残留风险：「定制家居」里的「定制家」仍会命中——靠否定语境检查挡住
      「不是定制家居」这类，其余靠 needs_review 人工兜底。
    """
    left = r"(?<![A-Za-z0-9])" if _LATIN.match(alias[0]) else ""
    right = r"(?![A-Za-z0-9])" if _LATIN.match(alias[-1]) else ""
    if left or right:
        return [m.span() for m in re.finditer(left + re.escape(alias) + right, text, re.IGNORECASE)]
    return [m.span() for m in re.finditer(re.escape(alias), text)]


def _sentence_at(text: str, pos: int) -> str:
    start = max([text.rfind(c, 0, pos) for c in _SENT_END] + [-1]) + 1
    ends = [text.find(c, pos) + 1 for c in _SENT_END if text.find(c, pos) != -1]
    return text[start:min(ends) if ends else len(text)]


def _entity_hit(text: str, aliases: list[str]) -> tuple[int, bool]:
    """返回 (首个有效命中位置, 是否有命中因否定语境被丢弃待人工确认)。"""
    hits = sorted((s, e) for a in aliases if a for s, e in _alias_spans(text, a))
    valid, negated = [], False
    for s, e in hits:
        if _NEG_RE.search(_sentence_at(text, s)):
            negated = True  # 「不是 X」里的命中不算提及，但要人工确认
        else:
            valid.append(s)
    return (min(valid) if valid else -1), negated


def first_pos(text: str, names: list[str]) -> int:
    return _entity_hit(text, names)[0]


def brand_in_question(question: str, cfg: dict) -> bool:
    """问题本身是否点名了品牌。

    点名了的话，答案必然复述品牌名，「提及率」会变成 100% 的假阳性。
    这类问题要单独归到品牌认知，不能混进可见性指标。
    """
    b = cfg["brand"]
    names = [b["name"]] + list(b.get("aliases", []) or [])
    host = urlparse(b.get("site", "")).netloc.lower().removeprefix("www.")
    if host and host in question.lower():
        return True
    return any(n and n.lower() in question.lower() for n in names)


def analyze_answer(answer: str, cfg: dict, citations: list | None = None) -> dict:
    brand = cfg["brand"]["name"]
    names, alias = entities_of(cfg)
    positions, needs_review = {}, False
    for n in names:
        pos, negated = _entity_hit(answer, alias[n])
        positions[n] = pos
        needs_review = needs_review or negated
    present = {n: p >= 0 for n, p in positions.items()}
    ordered = [n for n, p in sorted(positions.items(), key=lambda x: x[1]) if p >= 0]

    urls = [u for u in URL_RE.findall(answer)]
    for c in citations or []:
        if c.get("url"):
            urls.append(c["url"])
    domains = []
    for u in urls:
        try:
            h = urlparse(u).netloc.lower().removeprefix("www.")
            if h:
                domains.append(h)
        except Exception:  # noqa: BLE001
            pass

    own = urlparse(cfg["brand"]["site"]).netloc.lower().removeprefix("www.")

    # 疑似负面：品牌每个命中点前 80 / 后 160 字符窗口内的负面线索词
    neg = set()
    if present.get(brand):
        for a in alias[brand]:
            for s, e in _alias_spans(answer, a):
                for mm in NEG_CUES.finditer(answer[max(0, s - 80):e + 160]):
                    neg.add(mm.group(0).lower())

    return {
        "brand_mentioned": present.get(brand, False),
        "brand_rank": (ordered.index(brand) + 1) if brand in ordered else 0,
        "candidates": ordered,
        "competitors_mentioned": [n for n in names if n != brand and present.get(n)],
        "cited_domains": sorted(set(domains)),
        "own_domain_cited": any(d == own or d.endswith("." + own) for d in domains),
        "answer_chars": len(answer),
        "needs_review": needs_review or bool(neg),
        "negative_cues": sorted(neg),
    }


def dedup_rows(rows: list[dict]) -> list[dict]:
    """同日重跑/重复导入去重：按 (platform, question_id, round, sample_mode) 保留最后一条。"""
    seen: dict[tuple, dict] = {}
    for r in rows:
        seen[(r.get("platform"), r.get("question_id"), r.get("round"), r.get("sample_mode"))] = r
    return list(seen.values())


def aggregate(rows: list[dict], cfg: dict) -> dict:
    by_platform: dict[str, list[dict]] = {}
    for r in rows:
        by_platform.setdefault(r["platform"], []).append(r)

    out = {}
    for plat, all_rs in by_platform.items():
        # 点名品牌的问题（品牌验证类）不能算进可见性——答案必然复述品牌名。
        # 它们单独统计成「品牌认知」：AI 到底知不知道这个品牌、说得对不对。
        probe = [r for r in all_rs if r.get("brand_in_question")
                 or brand_in_question(r.get("question", ""), cfg)]
        rs = [r for r in all_rs if r not in probe]
        # 绝不回退：某平台只采了点名题时，可见性指标就是「未测」（None），
        # 不能把点名样本塞回去凑出 mention_rate=1.0 的假阳性。
        n = len(rs)
        market = (rs[0].get("market") if rs else None) or market_of(plat)
        mentioned = [r for r in rs if r["analysis"]["brand_mentioned"]]
        ranks = [r["analysis"]["brand_rank"] for r in mentioned if r["analysis"]["brand_rank"]]
        comp = {}
        dom = {}
        for r in rs:
            for c in r["analysis"]["competitors_mentioned"]:
                comp[c] = comp.get(c, 0) + 1
            for d in r["analysis"]["cited_domains"]:
                dom[d] = dom.get(d, 0) + 1
        out[plat] = {
            "market": market,
            "label": label_of(plat),
            "samples": n,
            "mention_rate": round(len(mentioned) / n, 3) if n else None,
            "top1_rate": round(sum(1 for r in mentioned if r["analysis"]["brand_rank"] == 1) / n, 3) if n else None,
            "top3_rate": round(sum(1 for r in mentioned if 1 <= r["analysis"]["brand_rank"] <= 3) / n, 3) if n else None,
            "avg_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
            "own_domain_cite_rate": round(sum(1 for r in rs if r["analysis"]["own_domain_cited"]) / n, 3) if n else None,
            "competitor_mentions": dict(sorted(comp.items(), key=lambda x: -x[1])),
            "top_cited_domains": dict(sorted(dom.items(), key=lambda x: -x[1])[:15]),
            # 品牌认知：直接点名品牌时，AI 认不认识、有没有引到官网
            "probe": {
                "samples": len(probe),
                "recognized_rate": round(sum(1 for r in probe if r["analysis"]["brand_mentioned"]) / len(probe), 3) if probe else None,
                "own_domain_cite_rate": round(sum(1 for r in probe if r["analysis"]["own_domain_cited"]) / len(probe), 3) if probe else None,
            },
        }
    return out


def confirm_competitors(slug: str, rows: list[dict]):
    """采样里真实出现过的竞品，把 geo.json 里对应候选的 confirmed 转正。
    只在值需要变化时才写配置（save_config 会自动备份）。"""
    seen = {c for r in rows for c in (r.get("analysis", {}).get("competitors_mentioned") or [])}
    if not seen:
        return
    cfg = G.load_config(slug)
    confirmed = []
    for c in cfg.get("competitors", []) or []:
        if c.get("confirmed") is False and c.get("name") in seen:
            c["confirmed"] = True
            confirmed.append(c["name"])
    if confirmed:
        G.save_config(slug, cfg)
        G.info("  竞品经采样确认：" + "、".join(confirmed))


# ------------------------------------------------------------ 命令


def run(slug: str, platforms: list[str] | None = None, repeat: int = 1, limit: int | None = None) -> dict:
    cfg = G.load_config(slug)
    if not cfg.get("questions"):
        G.die("geo.json 里还没有问题库，先让 Claude 生成 questions（见 SKILL.md 步骤 2）")

    plats = platforms or [p for p in cfg.get("platforms", []) if p in PROVIDERS]
    runnable = [p for p in plats if available(p)]
    skipped = [p for p in plats if not available(p)]
    if skipped:
        G.info("跳过（缺 API Key）：" + "、".join(f"{p}({PROVIDERS[p]['key_env']})" for p in skipped))
    if not runnable:
        G.info("没有可用的 API 平台。用 `geo.py sample-sheet` 导出人工/浏览器采样清单。")
        return {}

    # 任务清单：平台 × 问题 × 轮次
    jobs = []
    for plat in runnable:
        questions = questions_for(cfg, plat)
        if limit:
            questions = questions[:limit]
        if not questions:
            G.info(f"跳过 {plat}：问题库里没有 {market_of(plat)} 市场的问题")
            continue
        G.info(f"[{plat}] {market_of(plat)} 市场 · {len(questions)} 题 × {repeat} 轮")
        for q in questions:
            for k in range(repeat):
                jobs.append((plat, q, k + 1))

    pdir = G.project_dir(slug)
    path = pdir / "samples" / f"{G.today()}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)

    def one(job):
        plat, q, rnd = job
        t0 = time.monotonic()
        res = ask(plat, q["text"])
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        rec = {
            "date": G.today(), "ts": G.now_iso(),
            "platform": plat, "platform_name": PROVIDERS[plat]["name"],
            "market": market_of(plat), "terminal": "api", "sample_mode": "api",
            "evidence_level": "B_api_可复现",
            "search_enabled": res.get("searched", PROVIDERS[plat].get("search", False)),
            "question_id": q.get("id"), "question": q["text"], "round": rnd,
            "brand_in_question": brand_in_question(q["text"], cfg),
            "ok": res["ok"], "error": res.get("error"),
            "elapsed_ms": elapsed_ms,
            "answer": res.get("answer", ""), "citations": res.get("citations", []),
        }
        rec["analysis"] = analyze_answer(rec["answer"], cfg, rec["citations"]) if res["ok"] else {
            "brand_mentioned": False, "brand_rank": 0, "candidates": [],
            "competitors_mentioned": [], "cited_domains": [], "own_domain_cited": False,
            "answer_chars": 0, "needs_review": False, "negative_cues": [],
        }
        rec["needs_review"] = bool(rec["analysis"].get("needs_review"))
        return rec

    # 平台之间互不相干，并发跑；单个平台内部串行以免触发限流。
    # 推理型模型单次可达 90s，串行跑几十题会拖到一小时以上。
    rows, done, total = [], 0, len(jobs)
    lock = threading.Lock()
    fh = path.open("a", encoding="utf-8")  # 增量落盘：中途挂掉也不丢已采样本

    def worker(plat_jobs):
        nonlocal done
        out = []
        for job in plat_jobs:
            rec = one(job)
            with lock:
                done += 1
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                flag = "✓" if rec["analysis"]["brand_mentioned"] else ("✗" if not rec["ok"] else "·")
                print(f"[geo] {done:3d}/{total} {flag} [{rec['platform']}] {rec['question'][:32]}",
                      file=sys.stderr, flush=True)
            out.append(rec)
            time.sleep(0.4)
        return out

    by_plat: dict[str, list] = {}
    for job in jobs:
        by_plat.setdefault(job[0], []).append(job)
    with ThreadPoolExecutor(max_workers=max(1, len(by_plat))) as ex:
        for fut in as_completed([ex.submit(worker, v) for v in by_plat.values()]):
            try:
                rows.extend(fut.result())
            except Exception as e:  # noqa: BLE001
                G.info(f"某平台采样中断：{type(e).__name__}: {e}")
    fh.close()

    all_rows = dedup_rows(G.read_jsonl(path))
    ok_rows = [r for r in all_rows if r.get("ok")]
    metrics = {
        "slug": slug, "date": G.today(), "generated_at": G.now_iso(),
        "question_count": len(cfg.get("questions", [])), "sample_count": len(all_rows),
        "platforms": aggregate(ok_rows, cfg),
    }
    G.write_json(pdir / "metrics" / f"{G.today()}.json", metrics)
    confirm_competitors(slug, ok_rows)
    G.info(f"采样完成：{len(rows)} 条 → {path}")
    return metrics


def sheet(slug: str) -> Path:
    """导出人工/浏览器采样清单（Markdown），采完把答案粘回同一文件再 import。"""
    cfg = G.load_config(slug)
    plats = [p for p in cfg.get("platforms", []) if p in MANUAL_ONLY or not available(p)]
    lines = [
        f"# {cfg['brand']['name']} · AI 答案人工采样表 · {G.today()}",
        "",
        "用法：每个平台逐题提问，把**完整答案原文**（含引用链接）粘到对应的 ```answer 代码块里，",
        "然后运行 `python3 scripts/geo.py sample-import --slug " + slug + " --file <本文件>`。",
        "",
        "留空的题目会被跳过，不会被当成「品牌未被提及」。",
        "",
    ]
    for plat in plats:
        qs = questions_for(cfg, plat)
        if not qs:
            continue
        mk = "国内" if market_of(plat) == "cn" else "海外"
        lines += [f"## platform: {plat}", f"> {label_of(plat)}（{mk}市场 · {len(qs)} 题）", ""]
        for q in qs:
            lines += [f"### {q.get('id')} · {q['text']}", "", "```answer", "", "```", ""]
    path = G.project_dir(slug) / "samples" / f"{G.today()}-manual.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), "utf-8")
    G.info(f"采样表已导出：{path}")
    return path


def sample_import(slug: str, file: str) -> dict:
    cfg = G.load_config(slug)
    text = Path(file).read_text("utf-8")
    qmap = {q.get("id"): q["text"] for q in cfg.get("questions", [])}

    rows, platform = [], "manual"
    blocks = re.split(r"(?m)^##\s+platform:\s*(\S+)\s*$", text)
    # blocks = [前言, plat1, body1, plat2, body2, ...]
    for i in range(1, len(blocks), 2):
        platform = blocks[i].strip()
        body = blocks[i + 1]
        for m in re.finditer(r"(?ms)^###\s+(\S+)\s*·\s*(.+?)\n(.*?)```answer\n(.*?)```", body):
            qid, qtext, _, answer = m.group(1), m.group(2).strip(), m.group(3), m.group(4).strip()
            if not answer:
                continue
            rec = {
                "date": G.today(), "ts": G.now_iso(),
                "platform": platform,
                "platform_name": label_of(platform),
                "market": market_of(platform),
                "terminal": "web", "sample_mode": "manual",
                "evidence_level": "A_人工真实样本", "search_enabled": True,
                "question_id": qid, "question": qmap.get(qid, qtext), "round": 1,
                "ok": True, "error": None, "answer": answer, "citations": [],
            }
            rec["analysis"] = analyze_answer(answer, cfg)
            rec["needs_review"] = bool(rec["analysis"].get("needs_review"))
            rows.append(rec)

    if not rows:
        G.die("没解析到任何答案，检查 ```answer 代码块是否填写")
    pdir = G.project_dir(slug)
    path = pdir / "samples" / f"{G.today()}.jsonl"
    G.write_jsonl(path, G.read_jsonl(path) + rows)
    all_rows = [r for r in dedup_rows(G.read_jsonl(path)) if r.get("ok")]
    metrics = {
        "slug": slug, "date": G.today(), "generated_at": G.now_iso(),
        "question_count": len(qmap), "sample_count": len(all_rows),
        "platforms": aggregate(all_rows, cfg),
    }
    G.write_json(pdir / "metrics" / f"{G.today()}.json", metrics)
    confirm_competitors(slug, all_rows)
    G.info(f"导入 {len(rows)} 条人工样本 → {path}")
    return metrics
