import asyncio
from copy import deepcopy
import os
import PyPDF2
from config.LLM_Client import client_note
from config.institution import (
    foreign_industry,
    domestic_industry,
    foreign_academia,
    domestic_academia,
)  # 导入institution配置
import re
import requests
from tools.html_to_markdown import html_to_markdown

def download_and_convert(url,include_refs=False, linkify_ids=True):
    # 确保 URL 是 HTML 路径
    if "/abs/" in url:
        url = url.replace("/abs/", "/html/")
    
    # 获取原始 HTML 源码
    response = requests.get(url)
    response.raise_for_status()
    
    # 1. 初始转换
    markdown = html_to_markdown(response.text)
    
    # 2. 后处理：可选是否移除参考文献
    if not include_refs:
        # 寻找 "## References" 标记并截断
        ref_header = "## References"
        if ref_header in markdown:
            markdown = markdown.split(ref_header)[0].strip()
            # print("已移除参考文献部分。")

    # 3. 后处理：将 arXiv ID (如 2602.23361v1) 替换为完整的 HTML URL 链接
    if linkify_ids:
        arxiv_id_pattern = r'(?<!\[)(?<!/)\b(\d{4}\.\d{4,5}(v\d+)?)\b(?!\])'
        
        def replace_with_url(match):
            paper_id = match.group(1)
            return f"https://arxiv.org/html/{paper_id}"
        
        markdown = re.sub(arxiv_id_pattern, replace_with_url, markdown)
        # print("已完成 arXiv ID 链接化。")
    
    return markdown


institution = (
    list(foreign_industry.keys())
    + list(domestic_industry.keys())
    + list(foreign_academia.keys())
    + list(domestic_academia.keys())
)


async def write_note(paper: dict, model_name: str) -> str:
    pdf_url = paper.get("pdf_url", "")
    markdown_text = ""
    html_url = pdf_url.replace("/pdf/", "/html/")
    try:
        print(f"尝试通过 读取 HTML: {html_url}")
        # 直接转换字符串内容
        markdown_text = download_and_convert(html_url, include_refs=False, linkify_ids=True)
        # print("HTML 内容读取成功")
    except Exception as e:
        print(f"HTML 读取失败: {e}，回退到 PDF")

    if not markdown_text:
        file_path = paper["file_path"]
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    markdown_text += page.extract_text()
            print("PDF 内容读取成功")
        except Exception as e:
            print(f"PDF 读取失败: {e}")
        markdown_text = markdown_text.encode("utf-8", errors="replace").decode("utf-8")
    text_len = len(markdown_text.split())
    print(f"论文长度：{text_len}")
    if not markdown_text:
        print("无法读取论文内容，生成笔记失败")
        markdown_text = "无法读取论文内容，生成笔记失败"
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
                {"role": "user", "content": f"论文内容为：\n{markdown_text}"},
            ],
            max_completion_tokens=1000,
            temperature=0.5,
            extra_body={"enable_thinking": False},
        )

        content = response.choices[0].message.content.strip()
    except Exception as e:
        content = f"生成失败：{e}"
        print(f"生成笔记失败: {e}")
        raise Exception(f"生成笔记失败: {e}")
    content = f"""📖标题：{paper["title"]}\n🌐来源：arXiv, {paper["arxiv_id"]}\n\n{content}
    """
    if text_len > 129000:
        content = "论文长度超过129000，上下文截断"
    paper_ = deepcopy(paper)
    paper_["note"] = content
    paper_["markdown_text"] = markdown_text

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
