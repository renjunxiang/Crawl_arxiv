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

    async def filter_paper_rule(self, paper: dict) -> dict:
        result = deepcopy(paper)
        # 检查标题和摘要是否包含大模型相关关键词
        # 在没有大模型接口时候可以用，但容易遗漏
        title = paper.get("title", "")
        summary = paper.get("summary", "")
        context = title + " " + summary
        for kw in llm_keywords:
            if kw in context.lower():
                result.update(
                    {
                        "tag": "相关",
                        "success": True,
                    }
                )
                break
        else:
            result.update(
                {
                    "tag": "不相关",
                    "success": True,
                }
            )
        return result

    async def filter_paper_llm(self, paper: dict) -> dict:
        # 判断是否是大模型相关
        title = paper.get("title", "")
        summary = paper.get("summary", "")

        prompt = f"""
        给定如下信息：
        标题：{title}
        摘要：{summary}
        请根据论文的标题和摘要，判断这篇论文是否属于大模型(LLM)中我重点关注的研究方向，并返回一个标签。

        我重点关注的研究方向包括：
        1. 预训练算法及语料：预训练方法、预训练语料、Scaling Law等
        2. 后训练算法及数据：SFT微调、微调数据集、奖励模型(Reward Model)、RLHF/DPO/PPO等强化学习对齐方法
        3. 推理过程优化：思维链(CoT)优化、推理加速、测试时拓展(Test-time Scaling)
        4. 模型评估基准：大模型评测方法、评测数据集
        5. 大模型应用：RAG检索增强生成、Agent智能体、大模型工具集、DeepResearch
        6. 模型技术报告：知名开源模型发布(如DeepSeek、Qwen、Llama、GPT等)的技术报告
        7. 大模型安全：模型安全对齐、安全语料构建
        8. 模型架构创新：Transformer改进、MoE混合专家、高效注意力机制
        
        返回要求：
        - 如果与上述方向无关，返回"不相关"
        - 如果相关，请返回一个最能代表论文研究内容的标签，如"数学语料"、"课程学习"、"过程奖励"、"快慢思考"、"奥数基准"、"RAG检索优化"、"Agent记忆"、"DeepSeek技术报告"、"安全对齐"、"MOE架构"等，这些仅供参考，不代表绝对分类。
        - 如果同时涉及多个方向，返回一个最主要的研究内容标签
        - 只返回标签，不要有任何解释或额外内容
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
                    "tag": response.choices[0].message.content.strip(),
                    "success": True,
                }
            )

        except Exception as e:
            print(f"处理问题出错: {title}, 错误: {str(e)}")
            result.update(
                {
                    "tag": "不相关",
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


async def main():
    date_time = "2026-01-20"

    with open(f"./demo/papers_{date_time}.json", "r", encoding="utf-8") as f:
        papers = json.load(f)

    filter = FilterPaper(model_name="qwen2.5-72b-instruct", max_concurrent=10)
    results = await filter.process_batch_llm(papers)
    papers_filter = []
    for res in results:
        if res["tag"] != "不相关":
            papers_filter.append(res)
    print(f"筛选出 {len(papers_filter)} 篇论文")
    # 满足条件的论文清单
    with open(f"./output/{date}/papers_filter.json", "w", encoding="utf-8") as f:
        json.dump(papers_filter, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
