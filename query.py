from llama_index.core import Settings
from llama_index.core.llms import LLM, ChatMessage, ChatResponse, CompletionResponse, LLMMetadata
from llama_index.core.llms import CustomLLM as BaseCustomLLM
from indexer import load_existing_index
from config import LLM_CONFIG, INDEX_CONFIG, REPOS_CONFIG, DEFAULT_REPO
from typing import Sequence, Any, Generator
from openai import OpenAI


class SimpleLLM(BaseCustomLLM):
    """用原生 openai SDK 调用任意 OpenAI 兼容接口，不校验模型名"""
    
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 4096
    client: Any = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, model, api_base, api_key, temperature=0.1, max_tokens=4096, **kwargs):
        super().__init__(model_name=model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        self.client = OpenAI(base_url=api_base, api_key=api_key)
    
    @property
    def _llm_type(self) -> str:
        return "simple_openai"
    
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name=self.model_name)
    
    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return CompletionResponse(text=resp.choices[0].message.content)
    
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        api_msgs = [
            {"role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
             "content": str(msg.content)}
            for msg in messages
        ]
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=api_msgs,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return ChatResponse(
            message=ChatMessage(role="assistant", content=resp.choices[0].message.content)
        )
    
    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> Generator[CompletionResponse, None, None]:
        """流式输出"""
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        accumulated_text = ""
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                accumulated_text += delta
                yield CompletionResponse(
                    text=accumulated_text,
                    delta=delta
                )
    
    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> Generator[ChatResponse, None, None]:
        """流式聊天"""
        api_msgs = [
            {"role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
             "content": str(msg.content)}
            for msg in messages
        ]
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=api_msgs,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        accumulated_text = ""
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                accumulated_text += delta
                yield ChatResponse(
                    message=ChatMessage(role="assistant", content=accumulated_text),
                    delta=delta
                )


def init_llm():
    """初始化大模型"""
    if "localhost:11434" in LLM_CONFIG["api_base"]:
        from llama_index.llms.ollama import Ollama as OllamaLLM
        Settings.llm = OllamaLLM(
            model=LLM_CONFIG["model"],
            base_url=LLM_CONFIG["api_base"].replace("/v1", ""),
            temperature=LLM_CONFIG["temperature"],
            request_timeout=300
        )
    else:
        # 用原生 openai SDK，不校验模型名
        Settings.llm = SimpleLLM(
            model=LLM_CONFIG["model"],
            api_base=LLM_CONFIG["api_base"],
            api_key=LLM_CONFIG["api_key"],
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"]
        )


def query_code(question: str, repo_name: str = None, stream: bool = True):
    """
    查询代码库
    :param question: 问题
    :param repo_name: 仓库名（不传则用DEFAULT_REPO）
    :param stream: 是否流式输出
    :return: 回答和引用来源
    """
    init_llm()
    
    # 使用默认仓库或指定仓库
    repo_name = repo_name or DEFAULT_REPO
    if repo_name not in REPOS_CONFIG:
        raise ValueError(f"❌ 仓库 '{repo_name}' 未在 config.py 的 REPOS_CONFIG 中配置")
    
    print(f"🔍 正在查询仓库: {repo_name}")
    index = load_existing_index(repo_name)
    
    query_engine = index.as_query_engine(
        similarity_top_k=INDEX_CONFIG["top_k"],
        streaming=stream,
        response_mode="compact"
    )
    
    # 自定义系统提示词，要求回答规范
    system_prompt = """
    你是一个专业的代码助手，基于提供的代码上下文回答用户问题：
    1. 如果上下文没有相关信息，请直接说"我在代码库中没有找到相关信息"，不要编造答案
    2. 回答要简洁准确，必要时可以贴代码片段
    3. 涉及到具体文件和函数时，一定要明确指出文件路径
    4. 如果需要修改代码，请给出完整可运行的修改方案
    """
    
    response = query_engine.query(f"{system_prompt}\n\n用户问题：{question}")
    
    if stream:
        print("\n🤖 回答：")
        response.print_response_stream()
    else:
        print("\n🤖 回答：")
        print(response.response)
    
    # 打印引用来源
    print("\n\n📚 引用来源：")
    sources = set()
    for node in response.source_nodes:
        file_path = node.metadata.get("repo", "") + "/" + node.metadata.get("file_path", "")
        sources.add(file_path)
    
    for source in sorted(sources):
        print(f"  - {source}")
    
    return response


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="代码查询工具")
    parser.add_argument("question", nargs="+", help="问题内容")
    parser.add_argument("--repo", help="指定查询的仓库名（不传则用默认仓库）")
    args = parser.parse_args()
    
    question = " ".join(args.question)
    query_code(question, repo_name=args.repo)

