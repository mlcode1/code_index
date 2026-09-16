import os
from dotenv import load_dotenv
import ast

load_dotenv()

# PostgreSQL配置
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "database": os.getenv("PG_DATABASE", "postgres"),
}

# 嵌入模型配置（Ollama qwen3-embedding:8b）
EMBED_CONFIG = {
    "model": os.getenv("EMBED_MODEL", "qwen3-embedding:8b"),
    "api_base": os.getenv("EMBED_API_BASE", "http://localhost:11434/v1"),
    "api_key": os.getenv("EMBED_API_KEY", "ollama"),
    "dimensions": int(os.getenv("EMBED_DIM", 4096)),
}

# LLM大模型配置（支持任意OpenAI兼容接口）
LLM_CONFIG = {
    "model": os.getenv("LLM_MODEL", "qwen2.5-coder:14b-instruct-q4_K_M"),
    "api_base": os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
    "api_key": os.getenv("LLM_API_KEY", "ollama"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", 0.1)),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", 4096)),
}

# 多仓库配置（从环境变量读取路径，不在代码中硬编码本地路径，用户自定义的还是可以继续添加）
REPOS_CONFIG = {
    "flask_chat": os.getenv("REPO_FLASK_CHAT"),
    # 可以继续添加更多仓库，格式："仓库别名": "环境变量名"
    # "frontend": os.getenv("REPO_FRONTEND"),
}

# 默认查询的仓库（如果不指定--repo参数，就用这个）
DEFAULT_REPO = os.getenv("DEFAULT_REPO", "flask_chat")

# 代码索引配置
INDEX_CONFIG = {
    "exclude_patterns": ast.literal_eval(os.getenv("EXCLUDE_PATTERNS", "[]")),
    "chunk_lines": int(os.getenv("CHUNK_LINES", 40)),
    "chunk_lines_overlap": int(os.getenv("CHUNK_LINES_OVERLAP", 5)),
    "top_k": int(os.getenv("TOP_K", 8)),
}
