import asyncio
from copy import deepcopy
import os
import re
import PyPDF2
from config.LLM_Client import client
from config.institution import (
    foreign_industry,
    domestic_industry,
    foreign_academia,
    domestic_academia,
)  # 导入institution配置
import json

# 合并机构
institution = {
    **foreign_industry,
    **domestic_industry,
    **foreign_academia,
    **domestic_academia,
}


async def find_institution(paper: dict, model_name: str) -> str:
    file_path = paper["file_path"]
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            first_page = ""
            for idx, page in enumerate(reader.pages):
                text += page.extract_text()
                if idx == 0:
                    first_page += text
                    prompt = f"""
                    请从论文的第一页中判断，论文的前两个机构是否属于我关注的机构。
                    - 第一页内容：{first_page}
                    - 我关注的机构及在论文中的名称：{institution}
                    
                    返回要求：
                    - 如果属于我关注的机构，返回机构名称，名称需要用我清单的key名称表示，多个机构用顿号间隔
                    - 如果不属于我关注的机构，返回无
                    - 只返回标签，不要有任何解释或额外内容
                    """
                    try:
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
                    except Exception as e:
                        print(f"Error: {e}")
                        return None
                    content = response.choices[0].message.content.strip()
                    paper_ = deepcopy(paper)
                    paper_["institution"] = content

                    # 取第一个机构
                    first_institution = paper_["institution"].split("、")[0]
                    # 清理机构名称中的非法字符（Windows文件名不允许的字符）
                    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
                    first_institution = re.sub(invalid_chars, "_", first_institution)
                    paper_["first_institution"] = first_institution
                    if first_institution in foreign_industry:
                        paper_["institution_category"] = "国外工业界"
                    elif first_institution in domestic_industry:
                        paper_["institution_category"] = "国内工业界"
                    elif first_institution in foreign_academia:
                        paper_["institution_category"] = "国外学术界"
                    elif first_institution in domestic_academia:
                        paper_["institution_category"] = "国内学术界"
                    else:
                        paper_["institution_category"] = "其他机构"

    except Exception as e:
        print(f"Error: {e}")
        paper_ = deepcopy(paper)
        paper_["institution"] = "无"
        paper_["first_institution"] = "无"
        paper_["institution_category"] = "无"

    return paper_


def rename_file_with_institution(paper: dict) -> dict:
    """
    将机构名称加入文件名，并更新 paper 中的 file_path
    例如: 2601.08276v1【轨迹学习】ToolACE-MCP Generalizing History-Aware Routing from MCP Tools to the Agent Web.pdf
          -> 2601.08276v1【轨迹学习-浙大】ToolACE-MCP Generalizing History-Aware Routing from MCP Tools to the Agent Web.pdf
    """
    old_file_path = paper["file_path"]
    first_institution = paper["first_institution"]

    # 如果文件名已经包含机构名称，则跳过
    if f"-{first_institution}" in old_file_path:
        print(f"文件名已包含机构名称，跳过重命名: {filename}")
        return paper

    # 解析原文件名: arxiv_id【tag】title.pdf
    filename = os.path.basename(old_file_path)
    dir_path = os.path.dirname(old_file_path)

    print(f"尝试重命名文件: {filename}")
    print(f"第一个机构名称: {first_institution}")

    # 找到【】的位置，在 tag 后添加 -机构名称
    # 原格式: arxiv_id【tag】title.pdf
    # 新格式: arxiv_id【tag-机构名称】title.pdf
    # 使用更宽松的正则：匹配 arxiv_id【tag】剩余部分.pdf
    match = re.match(r"^(.+?)【(.+?)】(.+\.pdf)$", filename)
    if match:
        arxiv_id = match.group(1)  # arxiv_id
        tag = match.group(2)  # tag
        title_part = match.group(3)  # title.pdf

        print(f"正则匹配成功: arxiv_id={arxiv_id}, tag={tag}")

        # 构建新文件名
        new_filename = f"{arxiv_id}【{tag}-{first_institution}】{title_part}"
        new_file_path = os.path.join(dir_path, new_filename)

        # 如果新文件已存在，先删除（避免冲突）
        if os.path.exists(new_file_path):
            os.remove(new_file_path)

        # 重命名文件
        os.rename(old_file_path, new_file_path)

        # 更新 paper 中的 file_path
        paper["file_path"] = new_file_path
        print(f"重命名成功: {filename} -> {new_filename}")
    else:
        print(f"文件名格式不匹配，跳过重命名: {filename}")

    return paper


async def find_institution_batch(
    papers: list, model_name: str, downloaded_json_path: str = None, max_concurrent=10
) -> None:
    """
    批量处理论文机构筛选，结果直接更新到 downloaded.json

    Args:
        papers: 论文列表（只包含待处理的论文）
        model_name: 模型名称
        downloaded_json_path: downloaded.json 的路径，用于实时更新处理状态
        max_concurrent: 最大并发数
    """
    # 使用信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(paper: dict) -> dict:
        async with semaphore:  # 限制并发数量
            return await find_institution(paper, model_name)

    # 创建任务列表
    tasks = [asyncio.create_task(bounded_task(paper)) for paper in papers]
    total = len(tasks)
    completed = 0
    # 按完成顺序收集，并打印进度
    for coro in asyncio.as_completed(tasks):
        res = await coro
        completed += 1
        print(f"【{completed}/{total}】")

        if res is None:
            continue

        if res["institution"] != "无":
            # 重命名文件，将机构名称加入文件名
            try:
                res = rename_file_with_institution(res)
            except Exception as e:
                print(f"重命名文件失败: {res.get('file_path', 'unknown')}, 错误: {e}")

            # 更新状态为已保留
            res["institution_status"] = "keep"
        else:
            file_path = res["file_path"]
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除文件失败(可能已不存在): {file_path}, 错误: {e}")
            # 更新状态为已过滤
            res["institution_status"] = "remove"

        # 实时更新 downloaded.json
        if downloaded_json_path and os.path.exists(downloaded_json_path):
            try:
                with open(downloaded_json_path, "r", encoding="utf-8") as f:
                    all_papers = json.load(f)

                # 更新对应论文的信息
                for i, p in enumerate(all_papers):
                    if p["arxiv_id"] == res["arxiv_id"]:
                        all_papers[i] = res
                        break

                with open(downloaded_json_path, "w", encoding="utf-8") as f:
                    json.dump(all_papers, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"更新 downloaded.json 失败: {e}")
