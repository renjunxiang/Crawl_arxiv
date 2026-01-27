import asyncio
from copy import deepcopy
from openai import AsyncOpenAI  # 导入异步客户端
from config.LLM_Client import client
from config.LLM_Keywords import llm_keywords


class FilterPaper:
    """
    处理单篇pdf

    原始输入:
    paper_info = {
        "title": result.title,  # 标题
        "authors": [author.name for author in result.authors],  # 作者列表
        "categories": result.categories,  # 分类列表
        "published_date": result.published.strftime("%Y-%m-%d"),
        "arxiv_id": result.entry_id.split("/")[-1],  # 提取arxiv ID
        "pdf_url": result.pdf_url,  # PDF链接
        "summary": result.summary,  # 摘要
    }
    """

    def __init__(self, model_name="qwen2.5-72b-instruct", max_concurrent=10):
        self.model_name = model_name
        self.max_concurrent = max_concurrent

    async def filter_paper_llm(self, paper: dict) -> dict:
        # 判断是否是大模型相关
        title = paper.get("title", "")
        summary = paper.get("summary", "")

        prompt = f"""
        给定如下信息：
        标题：{title}
        摘要：{summary}
        请根据论文的标题和摘要，判断这篇论文是否和大模型相关，并返回一个标签，要求如下：
        1.大模型相关内容包括预训练语料、训练数据、模型训练算法、模型评估、模型安全、RAG、Agent、开源模型、模型架构等方向。
        2.如果和大模型不相关，返回“不相关”；如果和大模型相关，请返回一个论文技研究内容的短语标签，如”xx数据集“、“xx任务评测”、“模型架构”、“强化学习”等。
        3.只需要返回标签，不需要任何额外信息。
        """
        result = deepcopy(paper)
        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的论文打标器"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_completion_tokens=20,
                stream=False,
            )
            result.update(
                {
                    "category": response.choices[0].message.content.strip(),
                    "success": True,
                }
            )

        except Exception as e:
            print(f"处理问题出错: {title}, 错误: {str(e)}")
            result.update(
                {
                    "category": "不相关",
                    "success": False,
                }
            )
        finally:
            return result

    async def process_batch_llm(self, papers: list[dict]) -> list[dict]:
        """并发处理批量问题"""
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def bounded_task(paper: dict) -> dict:
            async with semaphore:  # 限制并发数量
                return await self.filter_paper_llm(paper)

        # # 思路1：创建所有任务并等待完成
        # tasks = [bounded_task(q) for q in papers]
        # results = await asyncio.gather(*tasks)

        # 思路2：逐个打印完成进度
        # 创建任务列表
        tasks = [asyncio.create_task(bounded_task(paper)) for paper in papers]
        total = len(tasks)
        results: list[dict] = []
        completed = 0
        # 按完成顺序收集，并打印进度
        for coro in asyncio.as_completed(tasks):
            res = await coro
            results.append(res)
            completed += 1
            print(f"【{completed}/{total}】")
            ## 也可以batch的打印
            # if (completed % self.max_concurrent == 0) or (completed == total):
            #     print(f"【{completed}/{total}】")

        return results
