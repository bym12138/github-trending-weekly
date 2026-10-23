# 🔥 GitHub AI 热点周榜

[![Weekly Report](https://github.com/bym12138/github-trending-weekly/actions/workflows/weekly.yml/badge.svg)](https://github.com/bym12138/github-trending-weekly/actions/workflows/weekly.yml)

每周一自动抓取 [GitHub Trending](https://github.com/trending?since=weekly) 周榜，**只保留与 AI、软件开发、产品相关的项目**，过滤掉翻墙代理、加密货币、外挂破解、教程合集等噪音，生成一份中文周报。

- ⏰ **更新时间**：每周一 北京时间 09:00（GitHub Actions 自动运行）
- 🎯 **关注方向**：AI Agent / 编程助手、模型与推理、AI 应用、开发者工具、产品
- 📦 **数据可复用**：每期都保留原始 JSON，方便做长期趋势分析

## 📑 分类说明

| 分类 | 包含内容 |
|---|---|
| 🤖 AI Agent / 编程助手 | Agent 框架、MCP、Claude Code / Codex / Cursor 插件与 Skills、Computer Use |
| 🧠 模型 / 训练 / 推理 | 开源模型、推理引擎、微调训练、语音 / 多模态模型 |
| ✨ AI 应用 | 基于大模型的应用、RAG、Chatbot、AIGC |
| 🛠️ 开发者工具 / 基础设施 | CLI、框架、数据库、编辑器、DevOps、工具链 |
| 📦 产品 / 应用 | 桌面 / 移动应用、自托管工具、效率产品、开源替代品 |

<!-- WEEKLY:START -->
## 📅 最新一期：2026-W43

> 生成于 2026-10-23 · 数据源 GitHub Trending (weekly) · 候选 138 个，相关 120 个，过滤 18 个 · 过滤方式：关键词规则

### 🔥 本周 Top 10

| # | 项目 | 简介 | 本周 ⭐ | 总 ⭐ |
|---|---|---|---|---|
| 1 | [morluto/rea](https://github.com/morluto/rea) | Reverse engineer anything with agents, from app behavior down to native binaries. | +106.3k | 367.1k |
| 2 | [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) | VoiceStudio is the open-source, fully-local ElevenLabs alternative — voice cloning, voice design, video dubbing, dictation, transcription & audiobook creation in 646 languages. | +13.6k | 81.9k |
| 3 | [stablyai/orca](https://github.com/stablyai/orca) | Orca is the place for working with a fleet of agents (e.g. Grok Bot, Claude Code). Run any coding agent with your own subscription. Available on desktop, mobile and remote runtime. | +9.4k | 102.9k |
| 4 | [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) | A coding-agent skill for multi-phase security audits with independently verified, machine-readable findings | +9.3k | 39.8k |
| 5 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Makes your AI agent think like the laziest senior dev in the room. The best code is the code you never wrote. | +9.2k | 173.7k |
| 6 | [boykopovar/AnyPS5](https://github.com/boykopovar/AnyPS5) | Tool for automatic PS5 executables porting to Linux and Windows | +8.7k | 46.9k |
| 7 | [xerj-org/xerj](https://github.com/xerj-org/xerj) | Local-first search engine and MCP server for AI agents. One Rust binary indexes code, docs, logs, JSONL/CSV and PDFs for BM25 full-text, vector and hybrid search, code search without grep, agent memory and RAG. Elasticsearch-compatible API; Corpus Hub serves hundreds of reference memory corpora. | +8.1k | 13.2k |
| 8 | [anomalyco/opencode](https://github.com/anomalyco/opencode) | The open source coding agent. | +6.8k | 220.3k |
| 9 | [storytold/artcraft](https://github.com/storytold/artcraft) | ArtCraft is an intentional crafting engine for artists, designers, and filmmakers | +6.7k | 35.7k |
| 10 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Write HTML. Render video. Built for agents. | +5.7k | 70.1k |

👉 [查看 2026-W43 完整周报（全部分类 + 已过滤项目）](reports/2026/2026-W43.md)

## 🗂️ 历史周报

- [2026-W43](reports/2026/2026-W43.md)
<!-- WEEKLY:END -->

## ⚙️ 工作原理

```
GitHub Trending 周榜（总榜 + 9 个语言榜，去重约 150 个候选）
        │
        ▼
GitHub API 补充 topics / 创建时间（🆕 标记 30 天内新项目）
        │
        ▼
过滤 + 分类 ── 有 ANTHROPIC_API_KEY → Claude 判断相关性、写中文简介和趋势观察
        │      └ 没有 / 调用失败   → 关键词规则（scripts/rules.py）
        ▼
reports/年/YYYY-Www.md（周报）  data/年/YYYY-Www.json（原始数据）  README（最新一期）
```

## 📁 目录结构

```
├── .github/workflows/weekly.yml   # 定时任务：每周一运行并提交结果
├── scripts/
│   ├── trending.py                # 抓取、过滤、生成报告
│   └── rules.py                   # 抓取范围、分类关键词、排除词、白名单
├── reports/                       # 每周中文周报（Markdown）
└── data/                          # 每周原始数据（JSON）
```

## 🛠️ 自己部署

1. Fork 本仓库
2. （可选）在 `Settings → Secrets and variables → Actions` 添加 `ANTHROPIC_API_KEY`，启用 Claude 过滤和中文总结；不配置则只用关键词规则
3. 在 `Actions` 页面启用 workflow，可手动点 `Run workflow` 立即生成一期

本地运行：

```bash
pip install -r requirements.txt
GITHUB_TOKEN=$(gh auth token) python scripts/trending.py           # 有 ANTHROPIC_API_KEY 时自动用 Claude
GITHUB_TOKEN=$(gh auth token) python scripts/trending.py --no-llm  # 只用关键词规则
```

## ✏️ 自定义过滤规则

编辑 [`scripts/rules.py`](scripts/rules.py)：

- `LANGUAGES`：抓取哪些语言的周榜
- `CATEGORIES`：各分类的关键词（按顺序匹配，命中第一个即归类）
- `EXCLUDE_KEYWORDS`：噪音关键词，命中即过滤
- `ALLOW_OWNERS`：白名单组织，直接视为相关

## 📄 License

MIT
