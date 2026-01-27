import asyncio
from copy import deepcopy
import os
import PyPDF2
from config.LLM_Client import client
from config.institution import company, college  # 导入institution配置
import json

# 合并机构
institution = {**company, **college}


async def find_institution(paper: dict, model_name: str) -> str:
    file_path = paper["file_path"]
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        first_page = ""
        for idx, page in enumerate(reader.pages):
            text += page.extract_text()
            if idx == 0:
                first_page += text
                prompt = f"""
                请从以下论文的第一页中判断论文是否属于我关注的机构，如果是则返回论文全部的机构名称（顿号间隔），否则返回无。不需要返回其他内容。
                第一页内容：{first_page}
                我关注的机构及在论文中的名称：{institution}
                """
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的论文作者机构提取助手。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_completion_tokens=100,
                    temperature=0.5,
                )
                content = response.choices[0].message.content.strip()
                paper_ = deepcopy(paper)
                paper_["institution"] = content

                return paper_


async def find_institution_batch(papers: list, model_name: str, max_concurrent=10) -> str:
    # 使用信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(paper: dict) -> dict:
        async with semaphore:  # 限制并发数量
            return await find_institution(paper, model_name)

    # 创建任务列表
    tasks = [asyncio.create_task(bounded_task(paper)) for paper in papers]
    total = len(tasks)
    results: list[dict] = []
    completed = 0
    # 按完成顺序收集，并打印进度
    for coro in asyncio.as_completed(tasks):
        res = await coro
        completed += 1
        print(f"【{completed}/{total}】")

        if res["institution"] != "无":
            results.append(res)
        else:
            file_path = res["file_path"]
            os.remove(file_path)

    return results
