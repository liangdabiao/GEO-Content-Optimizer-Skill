#!/usr/bin/env python3
"""GEO Visibility Tester - Test brand visibility in AI search engines.

Supports two backends:
  --engine perplexity  : Perplexity API (sonar-pro, single-call)
  --engine kimi        : Kimi API with built-in $web_search (multi-turn tool_calls)
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _build_prompt(keyword, query_template):
    if query_template:
        return query_template.format(keyword=keyword)
    return f"推荐{keyword}工具。告诉我你推荐了哪些工具，分别说为什么。"


def test_perplexity(brand, keyword, api_key, query_template=None):
    if requests is None:
        return {"error": "requests library not installed. Run: pip install requests"}

    prompt = _build_prompt(keyword, query_template)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers, json=payload, timeout=60,
        )
        resp.raise_for_status()
        response_text = resp.json()["choices"][0]["message"]["content"]
        mentioned = brand.lower() in response_text.lower()
        return {
            "date": datetime.now().isoformat(),
            "engine": "Perplexity",
            "keyword": keyword,
            "brand": brand,
            "cited": mentioned,
            "context": response_text[:500] if mentioned else "Not cited",
            "full_response_length": len(response_text),
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e}", "keyword": keyword}
    except Exception as e:
        return {"error": str(e), "keyword": keyword}


def test_kimi(brand, keyword, api_key, model="kimi-k2.6", base_url="https://api.moonshot.cn/v1",
              query_template=None):
    if OpenAI is None:
        return {"error": "openai library not installed. Run: pip install openai"}

    prompt = _build_prompt(keyword, query_template)
    client = OpenAI(base_url=base_url, api_key=api_key)

    messages = [
        {"role": "system", "content": "你是一个客观的产品推荐助手，请基于联网搜索结果回答问题，列出你找到的所有相关工具和品牌。"},
        {"role": "user", "content": prompt},
    ]

    tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]

    try:
        finish_reason = None
        while finish_reason is None or finish_reason == "tool_calls":
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=8192,
                tools=tools,
                extra_body={"thinking": {"type": "disabled"}},
            )
            choice = completion.choices[0]
            finish_reason = choice.finish_reason

            if finish_reason == "tool_calls":
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": choice.message.tool_calls,
                })
                for tc in choice.message.tool_calls:
                    tc_args = json.loads(tc.function.arguments)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps(tc_args, ensure_ascii=False),
                    })

        response_text = choice.message.content or ""
        mentioned = brand.lower() in response_text.lower()
        return {
            "date": datetime.now().isoformat(),
            "engine": "Kimi",
            "keyword": keyword,
            "brand": brand,
            "cited": mentioned,
            "context": response_text[:500] if mentioned else "Not cited",
            "full_response_length": len(response_text),
        }
    except Exception as e:
        return {"error": str(e), "keyword": keyword}


def save_history(result, history_file):
    history = []
    if os.path.exists(history_file):
        with open(history_file, encoding="utf-8") as f:
            history = json.load(f)
    history.append(result)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return history


ENGINES = {
    "perplexity": {"func": test_perplexity, "extra_args": []},
    "kimi": {
        "func": test_kimi,
        "extra_args": ["model", "base_url"],
    },
}


def main():
    parser = argparse.ArgumentParser(description="GEO Visibility Tester")
    parser.add_argument("--brand", required=True, help="Brand name to test")
    parser.add_argument("--keywords", nargs="+", required=True, help="Keywords to search")
    parser.add_argument("--engine", default="kimi", choices=["perplexity", "kimi"],
                        help="Search engine backend (default: kimi)")
    parser.add_argument("--api-key", help="API key (or set ENGINE_API_KEY env var)")
    parser.add_argument("--model", default="kimi-k2.6", help="Model name for Kimi backend")
    parser.add_argument("--base-url", default="https://api.moonshot.cn/v1",
                        help="API base URL for Kimi backend")
    parser.add_argument("--query", help="Custom query template (use {keyword} placeholder)")
    parser.add_argument("--history", default="visibility_history.json", help="History file path")
    parser.add_argument("--no-save", action="store_true", help="Don't save to history")
    args = parser.parse_args()

    # Resolve API key: CLI arg > env var
    api_key = args.api_key
    if not api_key:
        env_map = {"perplexity": "PERPLEXITY_API_KEY", "kimi": "KIMI_API_KEY"}
        api_key = os.environ.get(env_map[args.engine])
    if not api_key:
        print(f"Error: --api-key required or set {env_map[args.engine]} env var", file=sys.stderr)
        sys.exit(1)

    engine_conf = ENGINES[args.engine]
    test_func = engine_conf["func"]

    all_results = []
    for kw in args.keywords:
        print(f"Testing [{args.engine}]: {kw} ...", file=sys.stderr)

        kwargs = {"brand": args.brand, "keyword": kw, "api_key": api_key, "query_template": args.query}
        if args.engine == "kimi":
            kwargs["model"] = args.model
            kwargs["base_url"] = args.base_url

        result = test_func(**kwargs)

        if "error" in result:
            print(f"  Error: {result['error']}", file=sys.stderr)
        else:
            status = "CITED" if result["cited"] else "NOT CITED"
            print(f"  {status}", file=sys.stderr)
        all_results.append(result)

        if not args.no_save and "error" not in result:
            save_history(result, args.history)

    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
