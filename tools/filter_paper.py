import asyncio
from copy import deepcopy
from openai import AsyncOpenAI  # 导入异步客户端
from config.LLM_Client import client_filter
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
        请根据论文的标题和摘要，严格判断这篇论文是否属于大模型(LLM)中我重点关注的研究方向，并返回一个标签。
        判断核心：仅聚焦大模型本身相关的研究，无关内容一律判定为“不相关”，不做模糊判定。
        核心筛选原则（严格执行，缺一不可）：
        1. 必须聚焦大模型（LLM）本身，包括其训练算法、模型结构、训练数据、评估基准、通用应用及新模型发布，非大模型相关的AI研究均视为无关；
        2. 绝对排除以下内容（出现任意一种，直接返回“不相关”）：
            - 小众领域应用：考古、材料科学、哲学、医学、生物学、历史学等非通用领域的大模型应用；
            - 纯硬件相关：仅涉及硬件设计、加速器、芯片、电路等，不涉及大模型算法/结构/数据的内容；
            - 非大模型研究：传统NLP（如非LLM的文本分类、情感分析）、机器学习（非LLM的模型训练）、其他AI分支（如语音识别）；
            - 大模型延伸无关内容：仅用大模型作为工具辅助其他领域研究，未涉及大模型本身优化、改进、评估的内容；
            - 理论探讨无关：仅探讨大模型的社会影响、伦理问题、政策规范，不涉及大模型技术本身的内容。

        返回要求（严格遵守，不添加任何额外内容，宽松判定即视为错误）：
        - 若不符合核心筛选原则、超出上述8个关注方向，无论是否与AI相关，均返回"不相关"；
        - 如果相关，请返回一个最能代表论文研究内容的标签，如"数学语料"、"课程学习"、"过程奖励"、"快慢思考"、"数学评估基准"、"RAG检索优化"、"Agent记忆"、"DeepSeek技术报告"、"安全对齐"、"MOE架构"等，仅供参考，不代表绝对分类；
        - 若同时涉及多个方向，仅返回一个最主要的研究内容标签；
        - 只返回标签，不要有任何解释、补充说明、标点多余内容。
    """
        result = deepcopy(paper)
        try:
            response = await client_filter.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的论文打标器"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_completion_tokens=20,
                stream=False,
                extra_body={"enable_thinking": False},
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
