import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from config import PG_CONFIG, EMBED_CONFIG, INDEX_CONFIG


def init_pgvector():
    """初始化pgvector扩展，如果数据库不存在则创建"""
    # 先连接默认postgres数据库检查目标库是否存在
    conn = psycopg2.connect(
        host=PG_CONFIG["host"],
        port=PG_CONFIG["port"],
        user=PG_CONFIG["user"],
        password=PG_CONFIG["password"],
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # 检查数据库是否存在
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{PG_CONFIG['database']}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {PG_CONFIG['database']}")
        print(f"✅ 创建数据库: {PG_CONFIG['database']}")
    
    cur.close()
    conn.close()
    
    # 连接目标数据库创建pgvector扩展
    conn = psycopg2.connect(**PG_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("✅ 初始化pgvector扩展完成")
    cur.close()
    conn.close()


def get_vector_store(repo_name: str):
    """获取PGVector向量存储实例，每个仓库一张独立的表"""
    table_name = f"code_embeddings_{repo_name}"
    
    # 显式提供同步和异步连接字符串
    sync_connection_string = f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
    async_connection_string = f"postgresql+asyncpg://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
    
    vector_store = PGVectorStore.from_params(
        connection_string=sync_connection_string,
        async_connection_string=async_connection_string,
        table_name=table_name,
        embed_dim=EMBED_CONFIG["dimensions"],
        hybrid_search=True, # 支持混合搜索（关键词+语义）
        text_search_config="english"
    )
    
    return vector_store


if __name__ == "__main__":
    init_pgvector()
