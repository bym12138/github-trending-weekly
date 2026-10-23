"""规则过滤配置：想调整"什么算相关 / 什么算噪音"，改这里即可。

匹配对象 = 仓库名 + 描述 + topics（统一转小写）。
短词（如 ai、llm）按单词边界匹配，避免 "maintain" 命中 "ai"。
"""

# 抓取范围：weekly 总榜 + 这些语言的 weekly 榜（每个榜 25 个，去重后约 150~200 个候选）
LANGUAGES = [
    "",  # 总榜
    "python",
    "typescript",
    "javascript",
    "rust",
    "go",
    "jupyter-notebook",
    "java",
    "c++",
    "swift",
]

# 分类：按顺序匹配，命中第一个即归类
CATEGORIES = {
    "ai-agent": {
        "label": "🤖 AI Agent / 编程助手",
        "keywords": [
            "agent", "agents", "agentic", "mcp", "model context protocol", "claude code",
            "claude-code", "codex", "copilot", "cursor", "coding assistant", "ai coding",
            "skills", "subagent", "computer use", "browser use", "autonomous",
        ],
    },
    "ai-model": {
        "label": "🧠 模型 / 训练 / 推理",
        "keywords": [
            "llm", "llms", "language model", "inference", "fine-tune", "finetune", "fine-tuning",
            "training", "pretrain", "transformer", "transformers", "diffusion", "llama",
            "qwen", "deepseek", "mistral", "gguf", "quantization", "vllm", "cuda", "embedding",
            "embeddings", "reinforcement learning", "rlhf", "foundation model", "multimodal", "vlm", "tts", "asr",
            "speech", "text-to-speech", "speech-to-text", "machine learning", "machine-learning",
            "deep learning", "deep-learning", "neural network", "pytorch", "benchmark",
        ],
    },
    "ai-app": {
        "label": "✨ AI 应用",
        "keywords": [
            "ai", "gpt", "chatgpt", "openai", "claude", "anthropic", "gemini", "ollama",
            "rag", "prompt", "prompts", "chatbot", "generative", "genai", "aigc",
            "artificial intelligence", "image generation", "video generation", "ocr",
            "knowledge base", "vector",
        ],
    },
    "devtool": {
        "label": "🛠️ 开发者工具 / 基础设施",
        "keywords": [
            "cli", "sdk", "framework", "library", "compiler", "runtime", "database", "orm",
            "editor", "ide", "terminal", "shell", "devops", "kubernetes", "docker", "container",
            "testing", "debugger", "api", "web framework", "build tool", "bundler", "linter",
            "language server", "lsp", "git", "observability", "monitoring", "serverless",
            "react", "vue", "nextjs", "wasm", "webassembly",
            "developer tools", "developer-tools", "devtools", "code", "programming", "toolchain",
            "web development", "event streaming", "context", "plugin",
        ],
    },
    "product": {
        "label": "📦 产品 / 应用",
        "keywords": [
            "app", "desktop", "self-hosted", "selfhosted", "saas", "alternative", "productivity",
            "note", "notes", "note-taking", "browser", "extension", "dashboard", "workflow",
            "automation", "no-code", "low-code", "design", "figma", "analytics", "cms",
            "open-source alternative", "macos", "ios", "android", "mobile",
        ],
    },
}

# 噪音：命中任一即排除（优先于分类）
EXCLUDE_KEYWORDS = [
    # 翻墙 / 代理 / 机场
    "v2ray", "xray", "clash", "shadowsocks", "trojan", "vless", "vmess", "proxy subscription",
    "free proxy", "free vpn", "airport", "翻墙", "科学上网", "机场",
    # 加密货币 / 刷量
    "crypto", "blockchain", "web3", "airdrop", "nft", "defi", "token sniper", "trading bot",
    # 破解 / 外挂 / 盗版
    "crack", "cracked", "keygen", "cheat", "cheats", "aimbot", "hack tool", "bypass",
    "free download", "iptv", "piracy",
    # 纯学习资料 / 面试
    "interview", "leetcode", "cheatsheet", "roadmap", "tutorial", "course", "books",
    "教程", "面试", "学习路线",
    # 游戏 mod
    "minecraft", "mod menu",
]

# 白名单：这些 owner 的仓库直接视为相关（即使关键词没命中）
ALLOW_OWNERS = [
    "anthropics", "openai", "google", "google-deepmind", "microsoft", "meta-llama",
    "facebookresearch", "huggingface", "vercel", "langchain-ai", "deepseek-ai", "QwenLM",
]
