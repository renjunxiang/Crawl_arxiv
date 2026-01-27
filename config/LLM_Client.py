# 请修改
from openai import AsyncOpenAI  # 导入异步客户端

llm_url = "your_llm_url"
api_key = "your_api_key"

client = AsyncOpenAI(api_key=api_key, base_url=llm_url)
