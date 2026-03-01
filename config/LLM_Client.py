# 请修改
from openai import AsyncOpenAI  # 导入异步客户端


# 用于摘要筛选的大模型
client_filter = AsyncOpenAI(
    api_key="your_api_key",
    base_url="your_llm_url",
)

client_institution = AsyncOpenAI(
    api_key="your_api_key",
    base_url="your_llm_url",
)

# 用于笔记创作的大模型
client_note = AsyncOpenAI(
    api_key="your_api_key",
    base_url="your_llm_url",
)
