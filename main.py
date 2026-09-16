#!/Users/marin/miniconda3/bin/python
import click
from colorama import init, Fore
from indexer import index_code_repo
from query import query_code

init(autoreset=True)


@click.group()
def cli():
    """代码库大模型助手 - 基于PostgreSQL+pgvector本地向量库"""
    pass


@cli.command("index", help="索引指定代码仓库")
@click.argument("repo_name", required=True)
@click.option("--reindex", is_flag=True, help="清空已有索引重新索引")
def index_cmd(repo_name, reindex):
    print(Fore.CYAN + f"🚀 开始索引仓库 {repo_name}...")
    index_code_repo(repo_name, reindex=reindex)
    print(Fore.GREEN + "✅ 索引完成！")


@cli.command("chat", help="进入交互对话模式")
@click.option("--repo", default=None, help="指定查询的仓库名（不传则用DEFAULT_REPO）")
def chat_cmd(repo):
    repo_display = repo or "默认"
    print(Fore.CYAN + f"💬 代码助手已启动（仓库：{repo_display}），输入你的问题（输入exit/q退出）：")
    while True:
        try:
            question = input(Fore.YELLOW + "\n你: ").strip()
            if question.lower() in ["exit", "q", "quit"]:
                print(Fore.CYAN + "👋 再见！")
                break
            if not question:
                continue
            query_code(question, repo_name=repo, stream=True)
        except KeyboardInterrupt:
            print(Fore.CYAN + "\n👋 再见！")
            break
        except Exception as e:
            print(Fore.RED + f"❌ 出错: {str(e)}")


@cli.command("ask", help="直接提问（非交互）")
@click.argument("question", nargs=-1, required=True)
@click.option("--repo", default=None, help="指定查询的仓库名（不传则用DEFAULT_REPO）")
def ask_cmd(question, repo):
    question = " ".join(question)
    query_code(question, repo_name=repo, stream=False)


if __name__ == "__main__":
    cli()
