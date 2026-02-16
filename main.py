import os, json
from tools.find_paper import find_arxiv_papers
from tools.filter_paper import FilterPaper
from tools.download_paper import DownloadPaper
from tools.filter_institution import find_institution_batch
from tools.write_note import write_notes
import argparse

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("-d", "--date", type=str, help='日期，格式为"YYYY-MM-DD"')
args = parser.parse_args()

if not os.path.exists("./output"):
    os.makedirs("./output")


async def main(date: str, filter_llm: str, institution_llm: str, note_llm: str):
    """
    主函数，根据日期筛选大模型相关论文并生成笔记

    Args:
        date (str): 日期，格式为"YYYY-MM-DD"
        filter_llm (str):筛选是否大模型相关，调用的大模型名称
        institution_llm (str): 筛选是否指定机构，调用的大模型名称
        note_llm (str): 写笔记的大模型名称
    """
    # 创建日期目录
    if not os.path.exists(f"./output/{date}"):
        os.makedirs(f"./output/{date}")

    # =================================获取指定日期论文=================================
    if os.path.exists(f"./output/{date}/papers.json"):
        with open(f"./output/{date}/papers.json", "r", encoding="utf-8") as f:
            papers = json.load(f)
    else:
        categories = ["cs.CL", "cs.AI", "cs.LG", "cs.IR", "cs.CV"]
        papers = find_arxiv_papers(
            categories, start_time=date, end_time=date, max_results=2000
        )
        print(f"查询到 {len(papers)} 篇论文\n")
        # 指定日期的论文清单
        with open(f"./output/{date}/papers.json", "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=4)

    # =================================筛选大模型论文=================================
    print(f"开始筛选大模型相关论文")
    if os.path.exists(f"./output/{date}/papers_filter.json"):
        with open(f"./output/{date}/papers_filter.json", "r", encoding="utf-8") as f:
            papers_filter = json.load(f)
    else:
        filter = FilterPaper(model_name=filter_llm, max_concurrent=10)
        results = await filter.process_batch_llm(papers[:])
        papers_filter = []
        for res in results:
            if res["category"] != "不相关":
                papers_filter.append(res)
        print(f"筛选出 {len(papers_filter)} 篇论文\n")
        # 满足条件的论文清单
        with open(f"./output/{date}/papers_filter.json", "w", encoding="utf-8") as f:
            json.dump(papers_filter, f, ensure_ascii=False, indent=4)

    # =================================下载论文=================================
    print(f"开始下载论文")
    if os.path.exists(f"./output/{date}/downloaded.json"):
        with open(f"./output/{date}/downloaded.json", "r", encoding="utf-8") as f:
            download_info = json.load(f)
    else:
        dp = DownloadPaper(target_folder=f"./output/{date}/papers")
        download_info = dp.download_papers(papers_filter[:])
        print(f"下载完成 {len(download_info)} 篇论文\n")
        with open(
            os.path.join(f"./output/{date}", "downloaded.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(download_info, f, ensure_ascii=False, indent=4)

    # =================================机构筛选=================================
    """
    1.读取downloaded.json文件
    2.遍历每一篇论文，根据是否有institution_status字段识别是否已经经过机构筛选
    3.如果没有institution_status字段，则将其设置为pending，等待后续处理。
    4.全部处理完后，根据institution_status字段筛选出keep的论文。
    5.将筛选出的论文保存到filter_institution.json文件中。
    """
    print(f"开始根据机构筛选论文")
    if os.path.exists(f"./output/{date}/filter_institution.json"):
        with open(
            f"./output/{date}/filter_institution.json", "r", encoding="utf-8"
        ) as f:
            filter_institution = json.load(f)
    else:
        downloaded_json_path = f"./output/{date}/downloaded.json"

        # 初始化 institution_status 字段（如果不存在）
        for paper in download_info:
            if "institution_status" not in paper:
                paper["institution_status"] = "pending"

        # 保存初始化后的状态
        with open(downloaded_json_path, "w", encoding="utf-8") as f:
            json.dump(download_info, f, ensure_ascii=False, indent=4)

        # 过滤出待处理的论文
        pending_papers = [
            p for p in download_info if p.get("institution_status") == "pending"
        ]

        if pending_papers:
            print(f"待处理论文: {len(pending_papers)} 篇")
            await find_institution_batch(
                pending_papers,
                institution_llm,
                downloaded_json_path=downloaded_json_path,
            )
            # 重新加载更新后的 download_info
            with open(downloaded_json_path, "r", encoding="utf-8") as f:
                download_info = json.load(f)
        else:
            print(f"所有论文已处理完成")

        # 提取已处理的论文作为 filter_institution
        filter_institution = [
            p for p in download_info if p.get("institution_status") == "keep"
        ]
        print(f"根据机构筛选出 {len(filter_institution)} 篇论文\n")

        # 保存 filter_institution.json（用于后续步骤）
        with open(
            f"./output/{date}/filter_institution.json", "w", encoding="utf-8"
        ) as f:
            json.dump(filter_institution, f, ensure_ascii=False, indent=4)

    # =================================写笔记=================================
    if os.path.exists(f"./output/{date}/notes.json"):
        with open(f"./output/{date}/notes.json", "r", encoding="utf-8") as f:
            notes = json.load(f)
    else:
        notes = await write_notes(filter_institution, note_llm)
        print(f"写好 {len(notes)} 篇论文的笔记")
        # 满足条件的论文笔记
        with open(f"./output/{date}/notes.json", "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=4)

    with open(f"./output/{date}/notes.txt", "w", encoding="utf-8") as f:
        for note in notes:
            f.write("=" * 30 + "\n\n")
            f.write(note["institution"] + "\n\n")
            f.write(note["note"] + "\n\n")


if __name__ == "__main__":
    import asyncio

    model_name = {
        "filter": "qwen-plus",
        # "institution": "qwen2.5-72b-instruct",
        "institution": "qwen-plus",
        "note": "qwen-plus",
    }

    asyncio.run(
        main(
            args.date,
            model_name["filter"],
            model_name["institution"],
            model_name["note"],
        )
    )
