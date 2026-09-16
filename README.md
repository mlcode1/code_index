# code_index 本地代码助手
基于本地大模型 + PostgreSQL/pgvector 的代码检索增强助手，支持多个代码仓库独立索引，兼容任意 OpenAI 协议大模型。

---

## 功能特点
- ✅ **多仓库支持**：同时索引多个代码仓库，数据完全隔离，随时切换查询
- ✅ **本地优先**：向量数据库用 PostgreSQL + pgvector，嵌入/大模型默认走本地 Ollama，代码不上传云端
- ✅ **语法感知分割**：用 Tree-sitter 按 AST 语法分割代码块，完整保留函数/类语义边界
- ✅ **混合搜索**：向量语义检索 + 全文关键词检索联合召回，准确率远高于纯向量搜索
- ✅ **模型无关**：支持任意 OpenAI 兼容接口的大模型（Ollama/LM Studio/vLLM/DeepSeek/通义千问/GPT 等）
- ✅ **增量友好**：每个仓库独立存储，重建索引不影响其他仓库
- ✅ **引用标注**：回答自动标注引用的代码文件路径，方便跳转核对

---

## 前置依赖
1. 本地运行 PostgreSQL 数据库，安装 pgvector 扩展
2. 本地运行 Ollama，拉取嵌入模型：
   ```bash
   ollama pull qwen3-embedding:8b
   ```
3. （可选）拉取代码大模型：
   ```bash
   ollama pull qwen2.5-coder:14b-instruct-q4_K_M
   ```

---

## 快速开始
### 1. 配置
复制 `.env.example` 为 `.env`，根据环境修改配置：
- 数据库连接信息（默认 postgres/postgres）
- 大模型 API 地址/密钥/模型名（默认本地 Ollama qwen2.5-coder）

### 2. 添加代码仓库
编辑 `config.py`，在 `REPOS_CONFIG` 里添加你要索引的仓库：
```python
REPOS_CONFIG = {
    "flask_chat": "/Users/marin/PycharmProjects/flask_chat",
    "my_project": "/Users/marin/PycharmProjects/my_project",  # 新增仓库
    "frontend": "/Users/marin/PycharmProjects/frontend",      # 可以加多个
}

# 默认查询的仓库（不传--repo参数时用这个）
DEFAULT_REPO = "flask_chat"
```

### 3. 激活虚拟环境
```bash
source venv/bin/activate
```

### 4. 初始化数据库并索引仓库
```bash
# 索引 flask_chat 仓库（第一次运行会自动创建flask_chat数据库和pgvector扩展）
python main.py index flask_chat

# 索引其他仓库
python main.py index my_project
python main.py index frontend

# 清空重建某个仓库（比如代码更新了需要重新索引）
python main.py index flask_chat --reindex
```

### 5. 查询代码
```bash
# 交互对话模式（默认查 DEFAULT_REPO）
python main.py chat

# 交互模式指定仓库
python main.py chat --repo my_project

# 直接提问（非交互）
python main.py ask "找一下用户登录相关的接口"

# 直接提问指定仓库
python main.py ask --repo frontend "登录页面在哪里"
```

---

## 切换大模型
只需要修改 `.env` 里的 `LLM_*` 配置即可，无需改代码：
```env
# 例1：本地 Ollama qwen2.5-coder（默认）
LLM_API_BASE=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5-coder:14b-instruct-q4_K_M

# 例2：LM Studio 本地运行的模型
# LLM_API_BASE=http://localhost:1234/v1
# LLM_API_KEY=dummy
# LLM_MODEL=你的模型名

# 例3：DeepSeek 云端 API（效果接近GPT-4，成本极低）
# LLM_API_BASE=https://api.deepseek.com/v1
# LLM_API_KEY=sk-xxx你的密钥
# LLM_MODEL=deepseek-coder

# 例4：OpenAI GPT-4o
# LLM_API_BASE=https://api.openai.com/v1
# LLM_API_KEY=sk-xxx你的密钥
# LLM_MODEL=gpt-4o
```

---

## 目录结构
```
code_index/
├── config.py       # 配置加载（多仓库配置在这里改）
├── db.py           # PostgreSQL/pgvector 连接和初始化
├── indexer.py      # 代码索引逻辑（按语法分割、生成向量、写入数据库）
├── query.py        # 查询逻辑（检索、上下文组装、调用大模型）
├── main.py         # CLI 命令行入口
├── requirements.txt# Python 依赖
├── .env            # 环境配置（数据库/模型）
├── .env.example    # 配置模板
└── venv/           # Python 虚拟环境
```

---

## 存储架构
每个仓库在 PostgreSQL 中对应独立的表：`code_embeddings_{repo_name}`，数据完全隔离：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 唯一ID |
| text | text | 原始代码片段（~40行/块） |
| metadata | jsonb | 仓库名、文件路径、文件名、文件类型等 |
| embedding | vector(4096) | qwen3-embedding 生成的向量 |
| text_search_tsv | tsvector | 全文检索索引 |

**检索流程**：用户问题 → 同时走向量相似度召回 + 全文关键词召回 → 结果融合排序取 Top8 → 组装上下文喂给大模型 → 输出回答并标注引用来源。

---

## 支持的规模
- 10万行级别：~2500 块，存储 ~45MB，毫秒级响应
- 100万行级别：~25000 块，存储 ~450MB，<10ms 响应
- 千万行级别：建议调大 PostgreSQL work_mem 和 HNSW 参数，仍然可以流畅使用

---

## 常见问题
**Q：怎么验证索引成功了？**
A：执行 `psql -U postgres -d flask_chat -c "SELECT COUNT(*) FROM code_embeddings_flask_chat;"` 可以看到代码块数量，说明索引成功。

**Q：代码更新了怎么增量索引？**
A：目前需要重新索引整个仓库：`python main.py index <repo_name> --reindex`，几十万行代码索引时间约几十秒。后续可以加文件监听功能自动增量更新。

**Q：回答胡说八道不准确怎么办？**
A：可以调大 `INDEX_CONFIG["top_k"]`（默认8，改为10/12），或者换更大的代码模型（比如 qwen2.5-coder:32b / deepseek-coder:33b）。

**Q：能不能跨仓库联合查询？**
A：目前是仓库隔离查询，如果需要跨仓库（比如前后端一起查）可以在 query.py 里加跨仓库召回逻辑，后续版本可以加上。
