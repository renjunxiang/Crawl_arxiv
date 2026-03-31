import asyncio
from copy import deepcopy
import PyPDF2
from config.LLM_Client import client_note
from config.institution import (
    foreign_industry,
    domestic_industry,
    foreign_academia,
    domestic_academia,
)  # 导入institution配置
import json

institution = (
    list(foreign_industry.keys())
    + list(domestic_industry.keys())
    + list(foreign_academia.keys())
    + list(domestic_academia.keys())
)


async def write_note(paper: dict, model_name: str) -> str:
    file_path = paper["file_path"]
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    text_len = len(text.split())
    print(f"论文长度：{text_len}")
    if text_len > 129000:
        content = "论文长度超过129000，上下文截断"

    system_message = f"""
        你是一个论文笔记助手，请阅读论文内容，严格按照格式写这篇论文的笔记，不要带有markdown格式，字数控制在900字以内。格式如下：笔记标题：（10个字左右的中文短句说明论文的贡献）\n\n🛎️文章简介\n🔸研究问题：（用一个问句描述论文试图解决什么问题）\n🔸主要贡献：（一句话回答这篇论文有什么贡献）\n\n📝重点思路 （逐条写论文的研究方法是什么，每一条都以🔸开头）\n\n🔎分析总结 （逐条写论文通过实验分析得到了哪些结论，每一条都以🔸开头）\n\n💡个人观点\n（总结论文的创新点）
    """
    try:
        response = await client_note.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_message,
                },
                {"role": "user", "content": f"论文内容为：\n{text[:129000]}"},
            ],
            max_completion_tokens=1000,
            temperature=0.5,
            extra_body={"enable_thinking": False},
        )

        content = response.choices[0].message.content.strip()
    except Exception as e:
        content = f"生成失败：{e}"
    content = f"""📖标题：{paper["title"]}\n🌐来源：arXiv, {paper["arxiv_id"]}\n\n{content}
    """
    paper_ = deepcopy(paper)
    paper_["note"] = content

    return paper_


async def write_notes(papers: list, model_name: str, max_concurrent=10) -> str:
    # 使用信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(paper: dict) -> dict:
        async with semaphore:  # 限制并发数量
            return await write_note(paper, model_name)

    # 创建任务列表
    tasks = [asyncio.create_task(bounded_task(paper)) for paper in papers]
    total = len(tasks)
    results: list[dict] = []
    completed = 0
    # 按完成顺序收集，并打印进度
    for coro in asyncio.as_completed(tasks):
        res = await coro
        completed += 1
        print(f"【{completed}/{total}】已完成")

        results.append(res)

    return results
