import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext
from llama_index.embeddings.ollama import OllamaEmbedding  # 用专门的Ollama嵌入类，无需模型名校验
from llama_index.llms.ollama import Ollama as OllamaLLM  # LLM也用Ollama类，更稳定
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_go
import tree_sitter_java
from llama_index.core.node_parser import CodeSplitter
from db import init_pgvector, get_vector_store
from config import EMBED_CONFIG, INDEX_CONFIG, LLM_CONFIG, REPOS_CONFIG


def init_settings():
    """初始化全局设置：嵌入模型、代码分割器"""
    # 配置嵌入模型（Ollama qwen3-embedding:8b，用专门的Ollama类，无需模型名校验）
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_CONFIG["model"],
        base_url=EMBED_CONFIG["api_base"].replace("/v1", ""),  # Ollama类不需要/v1后缀
        dimensions=EMBED_CONFIG["dimensions"],
    )
    
    # 手动构建tree-sitter Python解析器（不需要联网下载语言包，用已安装的tree-sitter-python包）
    from tree_sitter import Parser, Language
    import tree_sitter_python
    py_parser = Parser(Language(tree_sitter_python.language()))
    
    # 配置代码分割器：按语法分割，保留函数/类完整结构
    Settings.text_splitter = CodeSplitter(
        language="python",
        chunk_lines=INDEX_CONFIG["chunk_lines"],
        chunk_lines_overlap=INDEX_CONFIG["chunk_lines_overlap"],
        max_chars=1500,
        parser=py_parser,  # 传入手动构建的解析器，不需要联网下载
    )


def index_code_repo(repo_name: str, reindex=False):
    """索引指定代码仓库"""
    init_settings()
    
    # 从配置获取仓库路径
    repo_path = REPOS_CONFIG.get(repo_name)
    if not repo_path:
        raise ValueError(f"❌ 仓库 '{repo_name}' 未在 config.py 的 REPOS_CONFIG 中配置")
    
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"❌ 仓库路径不存在: {repo_path}")
    
    # 初始化数据库
    init_pgvector()
    vector_store = get_vector_store(repo_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # 检查是否已经有索引，如果reindex为True则清空重新索引
    if reindex:
        vector_store.clear()
        print(f"⚠️  清空 {repo_name} 已有索引，开始重新索引")
    
    # 加载代码文件
    print(f"🔍 开始索引代码仓库: {repo_name} ({repo_path})")
    
    reader = SimpleDirectoryReader(
        input_dir=repo_path,
        recursive=True,
        exclude_hidden=True,
        exclude=INDEX_CONFIG["exclude_patterns"],
        filename_as_id=True,
        required_exts=[".py", ".js", ".ts", ".java", ".go", ".html", ".css", ".md", ".json", ".yaml", ".yml"]
    )
    
    documents = reader.load_data()
    print(f"📄 共加载 {len(documents)} 个文件")
    
    # 添加元数据：仓库名、相对路径
    for doc in documents:
        rel_path = doc.metadata["file_path"].replace(repo_path, "").lstrip("/")
        doc.metadata["repo"] = repo_name
        doc.metadata["file_path"] = rel_path
        doc.metadata["file_name"] = os.path.basename(doc.metadata["file_path"])
        doc.metadata["file_type"] = os.path.splitext(doc.metadata["file_name"])[1].lstrip(".")
    
    # 创建索引并写入PostgreSQL
    print("⚡ 正在生成向量并写入数据库...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    
    print(f"✅ 索引完成，共 {len(documents)} 个文件已写入向量数据库")
    return index


def load_existing_index(repo_name: str):
    """加载指定仓库的已有索引"""
    init_settings()
    vector_store = get_vector_store(repo_name)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    return index


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="代码仓库索引工具")
    parser.add_argument("repo_name", help="要索引的仓库名（在config.py的REPOS_CONFIG中配置）")
    parser.add_argument("--reindex", action="store_true", help="清空已有索引重新索引")
    args = parser.parse_args()
    
    index_code_repo(repo_name=args.repo_name, reindex=args.reindex)

