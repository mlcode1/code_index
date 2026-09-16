# Code Index - 本地代码智能助手

基于本地大模型 + 向量数据库的代码库智能问答系统。支持多仓库索引、多模型切换，完全本地运行，保护代码隐私。

---

## ✨ 功能特点

### 核心能力
- 🚀 **多仓库支持** - 同时索引多个代码仓库，独立存储互不干扰
- 🔍 **语义搜索** - 基于向量相似度的代码检索，比关键字搜索更智能
- 🌲 **AST 语法分割** - 使用 Tree-sitter 按代码结构分割，保留完整语义
- 🔀 **混合检索** - 向量搜索 + 全文搜索双路召回，提升召回率
- 💬 **流式输出** - 实时显示生成过程，提升用户体验
- 📍 **引用溯源** - 回答标注具体文件和代码位置，便于验证

### 🔒 隐私保护
- **完全本地运行** - 代码不上传云端，向量数据库存储在本地 PostgreSQL
- **自动脱敏** - 索引时自动检测并脱敏密码、API Key、Token 等敏感信息
- **环境隔离** - 所有配置通过 `.env` 管理，不会被提交到 Git
- **灵活模型支持** - 支持任意 OpenAI 兼容接口（本地 Ollama、云端 API 均可）

---

## 📦 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 向量数据库 | PostgreSQL + pgvector | 高性能向量存储，支持 HNSW 索引 |
| 嵌入模型 | Ollama + qwen3-embedding | 本地运行，4096 维向量 |
| 代码分割 | Tree-sitter | AST 语法树分割，支持多语言 |
| 大模型 | OpenAI 兼容接口 | 支持本地 Ollama、DeepSeek、GPT 等 |
| Python 环境 | Conda base | 推荐使用 Conda 管理依赖 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd /Users/marin/PycharmProjects/code_index

# 激活 Conda base 环境
conda activate base

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```bash
# 数据库连接
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=flask_chat
PG_USER=your_username
PG_PASSWORD=your_password

# 嵌入模型（Ollama）
EMBED_API_BASE=http://localhost:11434/v1
EMBED_MODEL=qwen3-embedding:8b

# 大模型（支持多种选择）
# 本地 Ollama
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=qwen2.5-coder:14b

# 或 DeepSeek API
# LLM_API_BASE=https://api.deepseek.com/v1
# LLM_API_KEY=your_api_key
# LLM_MODEL=deepseek-chat

# 或 OpenAI API
# LLM_API_BASE=https://api.openai.com/v1
# LLM_API_KEY=your_api_key
# LLM_MODEL=gpt-4o

# 代码仓库路径（每个仓库一个环境变量）
REPO_FLASK_CHAT=/Users/marin/PycharmProjects/flask_chat
REPO_MY_PROJECT=/Users/marin/PycharmProjects/my_project
```

### 3. 配置仓库映射

编辑 `config.py` 中的 `REPOS_CONFIG`，定义仓库名称和环境变量的映射：

```python
REPOS_CONFIG = {
    "flask_chat": os.getenv("REPO_FLASK_CHAT"),
    "my_project": os.getenv("REPO_MY_PROJECT"),
}
```

### 4. 初始化数据库

```bash
python db.py init
```

这会自动创建数据库和 pgvector 扩展。

### 5. 索引代码

```bash
# 索引单个仓库
python main.py index flask_chat

# 索引多个仓库
python main.py index flask_chat
python main.py index my_project

# 强制重建索引
python main.py index flask_chat --rebuild
```

索引过程中会自动检测并脱敏敏感信息（密码、API Key、Token 等）。

### 6. 查询代码

```bash
# 交互模式（持续对话）
python main.py chat --repo flask_chat

# 单次查询
python main.py ask flask_chat "查找用户登录相关的代码"
python main.py ask my_project "数据库连接池是怎么配置的"
```

---

## 📁 项目结构

```
code_index/
├── config.py              # 配置文件（仓库映射、模型参数）
├── db.py                  # 数据库初始化和连接
├── indexer.py             # 代码索引逻辑（含隐私脱敏）
├── query.py               # 查询逻辑（含流式输出）
├── main.py                # CLI 入口
├── .env                   # 环境配置（不提交）
├── .env.example           # 配置示例
├── .gitignore             # Git 忽略规则
├── requirements.txt       # Python 依赖
└── README.md              # 本文档
```

---

## 🔒 隐私保护机制

### 1. 文件级别过滤
- `.env` 文件不会被 Git 追踪
- `required_exts` 只索引代码文件（`.py`, `.js`, `.ts` 等）
- 自动排除 `.git`, `node_modules`, `__pycache__` 等目录

### 2. 内容级别脱敏
`indexer.py` 中的 `sanitize_sensitive_content()` 函数会自动检测并替换：

| 敏感类型 | 检测模式 | 替换为 |
|---------|---------|--------|
| 密码 | `password = "xxx"` | `password = "[REDACTED]"` |
| API Key | `api_key = "sk-xxx"` | `api_key = "[REDACTED]"` |
| Token | `Bearer eyJxxx` | `Bearer [REDACTED]` |
| 数据库连接 | `postgresql://user:pass@host` | `postgresql://user:[REDACTED]@host` |

### 3. 环境变量隔离
- 所有敏感配置通过 `.env` 管理
- 代码中不包含任何硬编码的密码、路径、API Key
- 仓库路径通过 `REPO_*` 环境变量配置

---

## 🌐 多模型支持

### 本地模型（推荐）

```bash
# 安装 Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 拉取嵌入模型
ollama pull qwen3-embedding:8b

# 拉取代码模型
ollama pull qwen2.5-coder:14b  # 推荐
ollama pull deepseek-coder:33b  # 更强但需要更多显存
```

### 云端 API

```bash
# DeepSeek（性价比高）
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=deepseek-chat

# OpenAI GPT-4o
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o

# 火山引擎
LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=your_api_key
LLM_MODEL=Qwen3.7-Max
```

---

## 🛠️ 高级配置

### 调整索引参数

```bash
# 在 .env 中配置
CHUNK_SIZE=40          # 每个代码块的最大行数
CHUNK_OVERLAP=5        # 块之间的重叠行数
```

### 调整检索参数

```bash
# 在 .env 中配置
TOP_K=8                # 返回的最相关代码块数量
MIN_SCORE=0.7          # 最小相似度阈值
```

### 多语言支持

当前支持的语言：Python, JavaScript, TypeScript, Go, Java

如需添加其他语言，编辑 `indexer.py`：

```python
from tree_sitter import Language
import tree_sitter_rust  # 添加 Rust 支持

# 在 SUPPORTED_LANGUAGES 中添加
SUPPORTED_LANGUAGES = {
    "python": Language(tree_sitter_python.language()),
    "rust": Language(tree_sitter_rust.language()),
    # ...
}
```

---

## 📊 性能参考

| 代码规模 | 索引时间 | 查询延迟 | 内存占用 |
|---------|---------|---------|---------|
| 1 万行 | ~30 秒 | <100ms | ~500MB |
| 10 万行 | ~5 分钟 | <200ms | ~2GB |
| 100 万行 | ~1 小时 | <500ms | ~10GB |

*测试环境：MacBook Pro M1, 16GB RAM, Ollama 本地运行*

---

## 🐛 常见问题

**Q: 索引时提示 "数据库连接失败"**
```bash
# 检查 PostgreSQL 是否运行
pg_isready -h localhost -p 5432

# 检查用户名密码是否正确
psql -h localhost -U your_username -d flask_chat
```

**Q: 查询时大模型调用失败**
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 检查模型是否已拉取
ollama list
```

**Q: 敏感信息没有被完全脱敏**
- 检查代码中是否有非标准格式的密码（如 `SECRET = "xxx"` 而非 `secret_key`）
- 可以在 `indexer.py` 的 `sanitize_sensitive_content()` 中添加自定义正则规则

**Q: 流式输出没有显示**
- 确保终端支持 ANSI 转义序列
- 尝试使用 `python -u main.py chat` 禁用缓冲

---

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

**注意**：提交前确保 `.env` 文件不在 Git 追踪中！

---

## 📄 许可证

MIT License

---

## 🔗 相关资源

- [Ollama](https://ollama.com/) - 本地大模型运行平台
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL 向量扩展
- [Tree-sitter](https://tree-sitter.github.io/) - 增量解析器
- [LlamaIndex](https://www.llamaindex.ai/) - RAG 框架
