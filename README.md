<div align="center">

# GEO 工具箱 · 三个 AI 搜索优化技能

**让 ChatGPT、豆包、Perplexity、文心一言 这些 AI 在回答问题时主动提到你**

[![Claude Code/Codex/Workbuddy  Skill](https://img.shields.io/badge/Claude%20Code-Skill-blue)](https://claude.ai/code) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## 一句话理解这个项目

**SEO 是让 Google 搜到你，GEO 是让 AI 在回答时"提到你"。**

越来越多的用户不再打开百度、Google，而是直接问 AI：
- "有哪些好用的国产跨境电商工具？"
- "小米和华为哪个拍照更好？"
- "帮我推荐一个适合一人公司的 AI 选品工具"

如果 AI 在回答里提到了你的竞品，但没提到你——**你就在 AI 时代"隐形"了**。

本项目提供 **3 个 GEO 工具**（也叫 Skill），从轻量到重量级，帮你把内容做得让 AI 愿意引用。

---

## 三个工具怎么选？

| 你的情况 | 推荐工具 | 触发方式 |
|---------|---------|---------|
| 想给单篇文章/网站做一次 AI 体检 | **geo-content-optimizer** | `/geo-content-optimizer 你的网址` |
| 第一次做 GEO，想要 AI 一步步带做 | **geo-optimizer** | `/geo-optimizer 我是做XX的，帮我开始` |
| 想长期做 GEO（每月看数据、接客户、运营） | **geolook** | 1 geolook skill全网深度geo调研'小米品牌'。2 启动UI网页工作台 |

> 不确定？先用 **geo-content-optimizer** 跑一次你的网址看体检报告，再决定要不要继续。

---

## 为什么这事现在很重要？

- **68%** 的 AI 回答引用来自高权威网站（BrightEdge 100 万条 AI 回答研究）
- **43%** 的引用来自带"问答"标记的页面
- **麦肯锡** 预测：2026 年 40% 的搜索将通过 AI 完成
- 现在不做 GEO ≈ 2015 年不做 SEO

---

## 工具一：geo-content-optimizer · 单页体检

**用途**：给你一个网址，30 秒后告诉你"这个页面在 AI 眼里是什么水平"。

**适合谁**：已经有官网、想看看自家页面有没有被 AI 注意到的人。

**怎么用**：

在 Claude Code/Codex/Workbuddy  里输入：

```
/geo-content-optimizer https://你的网址.com
```

**它会自动做 6 件事**：

1. 抓取你页面的标题
2. 用 Google 搜这个标题，看有哪些相关问题
3. 提取出最核心的那个搜索词
4. 拿到 Google AI 概览里 AI 写的答案
5. 把 AI 答案和你页面内容对比
6. 生成一份"差什么、补什么"的优化报告

**会输出什么**：

一份中文优化报告，放在 `output/你的域名/` 文件夹下，告诉你：

- AI 提到了哪些点，你没提到（**内容缺口**）
- AI 觉得重要的点，你说得不够（**深度不足**）
- 具体改哪几段、加哪些 FAQ、补充哪些数据

**特点**：
- 不需要 Python、不需要 API Key
- 完全靠 Claude Code/Codex/Workbuddy  自带工具
- 跑一次大约 1-2 分钟

---

## 工具二：geo-optimizer · 一步一步带你做 GEO

**用途**：GEO 全流程"陪练"，从零开始帮你把品牌内容做成 AI 喜欢的形式。

**适合谁**：第一次接触 GEO、希望 AI 引导一步步做的人。

**怎么用**：

在 Claude Code/Codex/Workbuddy  里说一句话，比如：

```
/geo-optimizer 我是做"国产积木"的，叫高砖积木，帮我系统做一下 GEO
```

或者更简单：

```
/geo-optimizer 帮我做一下 GEO
```

**它会带你这 5 件事**（按需触发，不用一次全做）：

### A. 帮你给品牌"做名片"

生成一段结构化标记（叫 Schema），告诉 AI "你是谁、做什么、解决什么问题"。

> 就像给 AI 一张你的"工商信息卡"，让 AI 介绍你时不会张冠李戴。

### B. 检查文章"AI 友不友好"

把你的文章丢给它，它会告诉你：

- 句子是不是太长（AI 读不懂长句）
- 有没有堆砌"创新、领先、卓越"这种空话
- 有没有问句、有没有具体数据

并给一份"AI 可读性评分"。

### C. 规划内容集群

帮你设计"1 个核心页 + 5-10 个子页"的内容结构，让 AI 一眼看出你们在某个领域很专业。

### D. 测试"AI 看不看得见我"

用搜索 API（默认接 Kimi，国内直连；也可选 Perplexity）模拟真实用户提问，看 AI 答案里有没有提到你的品牌。

> 第一次跑：建立"基线"（AI 引用率多少）
> 每月跑：看趋势（变好了还是变差了）
> 每季度跑：生成趋势报告

### E. 自动调起"工具一"分析 URL

如果你给了具体网址，它会自动跳到 geo-content-optimizer 做深度分析。

**特点**：

- 大部分功能零依赖（不需要 API Key）
- 只有"测 AI 看不看见我"需要 API Key（Kimi 国内可免费申请）
- 像聊天一样一步步做，不要求你懂技术

---

## 工具三：geolook · GEO 运营平台

继承和深度改造：https://github.com/aigclink/geolook

**用途**：把 GEO 当"持续生意"来做。带可视化的网页工作台，每周/每月自动跑全套流程，看数据、管任务、出给客户的交付物。

**适合谁**：

- 给客户做 GEO 服务的代理/咨询公司
- 想长期跟踪自家品牌在 AI 里表现的市场/品牌团队
- 已经知道 GEO 是什么、想要"重型武器"的人

**怎么用（3 步跑起来）**：

1. **下载项目**，安装 3 个第三方库
2. **启动skill**：全网全AI深度调研，全是图形界面
3. **配 1 个 API Key**（推荐 302.AI，一把 Key 调通 10 个 AI 平台）

详见 [geolook/README.md](skills/geolook/README.md) 里的部署教程。

**它能做什么（看界面）**：

### 现状 · AI 里你什么样

- **引擎表现**：国内 7 个 + 海外 6 个 AI 引擎，告诉你每个引擎提到你的频率、位置、引用谁
- **品牌提及分布**：你和竞品在 AI 答案里各占多少
- **竞品对比**：哪些问题被竞品"抢走"了，哪些问题只有你能答

### 诊断 · 为什么是这样

- **站点体检**：6 维打分（能不能抓到、有没有结构化、缺不缺关键内容、权威性够不够）
- **阵地地图**：告诉你应该去哪些网站/平台"留名"（知乎、小红书、维基、G2、Reddit...）
- **品牌事实库**：全公司统一口径的"品牌资料库"，所有对外内容都从这里取

### 提升 · 该做什么

- **行动计划**：自动生成带"验收标准"的任务清单（做完没做完系统说了算）
- **内容工作台**：左边给"必含要点"，右边实时打分你这篇文章"AI 愿不愿意引用"
- **资产一键生成**：把 Schema、FAQ、定义块自动生成 HTML，直接给开发部署

### 成效 · 有用没用

- **效果验收**：每条任务自动重测，做没做对系统判定
- **客户交付包**：一键打包诊断报告 + 优化方案 + 执行方案 + 任务表，直接发客户

**和前两个工具有什么不同**？

| 维度 | geo-content-optimizer | geo-optimizer | geolook |
|------|---------------------|---------------|---------|
| 适合场景 | 单页体检 | 一步步带你做 | 长期 GEO 运营 |
| 启动难度 | 一句话 | 一句话 | 装环境 + 配 Key |
| 周期性 | 单次 | 按需 | 每周/每月自动 |
| 协作能力 | 个人 | 个人 | 多项目切换 |
| 给客户交付 | 报告 | 报告 | 完整交付包 |
| 部署形式 | Claude Code/Codex/Workbuddy  内 | Claude Code/Codex/Workbuddy  内 | 本地网页工作台 |

---

## 安装

### 准备工作

1. 装好 [Claude Code/Codex/Workbuddy ](https://claude.ai/code) 并登录
2. 会基本的命令行操作（复制粘贴命令）

### 安装前两个 Skill（推荐，零成本）

把 `skills/geo-optimizer` 和 `skills/geo-content-optimizer` 整个文件夹复制到 Claude Code/Codex/Workbuddy  的 skills 目录：

- **macOS/Linux**：`~/.claude/skills/`
- **Windows**：`%USERPROFILE%\.claude\skills\`

重启 Claude Code/Codex/Workbuddy ，输入 `/geo-optimizer` 或 `/geo-content-optimizer` 就能用。

### 安装第三个 Skill（geolook，需要本地环境）

AI会自动化帮忙安装环境：Python 3.9+ 和 3 个常用库（requests、beautifulsoup4、lxml），详细步骤看 [geolook/README.md](skills/geolook/README.md)。

### 简易安装方法:
[Claude Code/Codex/Workbuddy ]直接给 github地址让AI帮忙安装 skill 则可以，不需要关心其他。

---

## 常见问题

**Q：完全不懂技术，能用吗？**

A：前两个 Skill 完全不用写代码，对话就行。geolook 稍微需要302.AI Key，但装好之后全程是浏览器界面。

**Q：必须 3 个都装吗？**

A：不用。按你的需求选一个就行：
- 只想看看自家页面怎么样 → 只装 geo-content-optimizer
- 想系统化做一下 GEO → 装 geo-optimizer
- 想长期运营或接客户 → 装 geolook

**Q：GEO 多久能见效？**

A：通常 **2-4 周** 开始在 AI 答案里看到变化。AI 引擎更新有延迟，不是改完就立刻有效果。geolook 平台的"季度报告"就是帮你看这个趋势的。

**Q：AI 引擎答案里提到我，访问量会变多吗？**

A：会，但方式不同。AI 答案里点链接来的用户更精准（他们已经看了 AI 介绍，对你有基本信任）。同时你的"品牌曝光"会变多——即使这次没点，下次看到名字更可能搜索你。

**Q：要花多少钱？**

A：
- **前两个 Skill**：基本零成本，只有"测试 AI 看不看见你"需要 API Key。Kimi 国内可申请免费额度，Perplexity 海外按量计费很便宜。
- **geolook**：开源免费，只花你 AI 引擎 API 采样费。配 302.AI 一把 Key 的话，每月几十块就够跑全平台。

**Q：GEO 和 SEO 冲突吗？**

A：不冲突，做好 GEO 通常对 SEO 也有帮助（结构化、权威性、原创数据——SEO 也喜欢）。可以一起做。

**Q：内容一定要自己写吗？**

A：不一定。geolook 里有"AI 初稿"功能，但生成的初稿**必须人工核实事实**才能用——AI 编造数字和案例是常见坑。工具帮你提效，但不能替你担责。

---

## 我应该从哪开始？

```
你是新接触 GEO
   ↓
用 geo-content-optimizer 跑一下自己官网
   ↓
看报告，了解 AI 现在怎么看你
   ↓
    ┌──────────────┬──────────────┐
    ↓              ↓              ↓
看完就完了      想自己动手     想长期运营
   ↓              ↓              ↓
 结束！       geo-optimizer    geolook
              一步步带你        自动化运营
```

---

## 项目结构

```
geo-ai-agent-main/
├── README.md                       ← 你正在看的文件
├── skills/
│   ├── geo-content-optimizer/      ← 工具一：单页体检
│   ├── geo-optimizer/              ← 工具二：全流程陪练
│   └── geolook/                    ← 工具三：GEO 运营平台
├── docs/                           ← 项目文档
└── output/                         ← 历史分析报告样例
```

---

## 致谢

- [linux.do](https://linux.do) 佬友支持
- [liang.348349.xyz](https://liang.348349.xyz/) 更多 agent 项目
- 微信公众号文章：《Reddit GEO 怎么做？10 步 AI 搜索优化框架实战版》

## License

MIT License — 自由使用、修改和分发。
