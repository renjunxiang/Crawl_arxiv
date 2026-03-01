import arxiv
from datetime import datetime, timezone, timedelta
import time

# 原始接口返回样例
"""
arxiv.Result(
    entry_id="http://arxiv.org/abs/2512.08343v1",
    updated=datetime.datetime(2025, 12, 9, 8, 13, 4, tzinfo=datetime.timezone.utc),
    published=datetime.datetime(2025, 12, 9, 8, 13, 4, tzinfo=datetime.timezone.utc),
    title="Soil Compaction Parameters Prediction Based on Automated Machine Learning Approach",
    authors=[
        arxiv.Result.Author("Caner Erden"),
        arxiv.Result.Author("Alparslan Serhat Demir"),
        arxiv.Result.Author("Abdullah Hulusi Kokcam"),
        arxiv.Result.Author("Talas Fikret Kurnaz"),
        arxiv.Result.Author("Ugur Dagdeviren"),
    ],
    summary="Soil compaction is critical in construction engineering to ensure the stability of structures like road embankments and earth dams. Traditional methods for determining optimum moisture content (OMC) and maximum dry density (MDD) involve labor-intensive laboratory experiments, and empirical regression models have limited applicability and accuracy across diverse soil types. In recent years, artificial intelligence (AI) and machine learning (ML) techniques have emerged as alternatives for predicting these compaction parameters. However, ML models often struggle with prediction accuracy and generalizability, particularly with heterogeneous datasets representing various soil types. This study proposes an automated machine learning (AutoML) approach to predict OMC and MDD. AutoML automates algorithm selection and hyperparameter optimization, potentially improving accuracy and scalability. Through extensive experimentation, the study found that the Extreme Gradient Boosting (XGBoost) algorithm provided the best performance, achieving R-squared values of 80.4% for MDD and 89.1% for OMC on a separate dataset. These results demonstrate the effectivening the generalization and performance of ML models. Ultimately, this research contributes to more efficient and reliable construction practices by enhancing the prediction of soil compaction parameters.",
    comment="Presented at the 13th International Symposium on Intelligent Manufacturing and Service Systems, Duzce, Turkey, Sep 25-27, 2025. Also available on Zenodo: DOI 10.5281/zenodo.17533851",
    journal_ref="Proc. of the 13th Int. Symp. on Intelligent Manufacturing and Service Systems, pp. 571-578, 2025, ISBN 978-625-00-3472-9",
    doi="10.5281/zenodo.17533851",
    primary_category="cs.AI",
    categories=["cs.AI"],
    links=[
        arxiv.Result.Link(
            "https://arxiv.org/abs/2512.08343v1",
            title=None,
            rel="alternate",
            content_type=None,
        ),
        arxiv.Result.Link(
            "https://arxiv.org/pdf/2512.08343v1",
            title="pdf",
            rel="related",
            content_type=None,
        ),
        arxiv.Result.Link(
            "https://doi.org/10.5281/zenodo.17533851",
            title="doi",
            rel="related",
            content_type=None,
        ),
    ],
)
"""


def find_arxiv_papers(
    categories=["cs.CL", "cs.AI", "cs.LG", "cs.IR", "cs.CV"],
    start_time=None,
    end_time=None,
    max_results=500,
):
    """
    从arXiv API获取符合条件的论文

    Args:
        categories (list, optional): 要搜索的分类列表，默认包含5个分类。
        start_date (datetime, optional): 开始日期，默认1月1日00:00:00 UTC。
        end_date (datetime, optional): 结束日期，默认1月3日23:59:59 UTC。

    Returns:
        list: 符合条件的论文列表，每个元素是一个字典，包含论文信息。
    """

    # 1. 定义查询类别
    # 构造查询字符串: cat:cs.CL OR cat:cs.AI ...
    # 使用括号包裹以防未来增加其他逻辑
    category_query = " OR ".join([f"cat:{cat}" for cat in categories])

    # 2. 定义时间范围 (使用 UTC 时间，因为 arXiv API 返回的是 UTC)
    # --- CHANGED: arXiv API 仅支持 submittedDate 作为日期过滤字段；格式必须是 YYYYMMDDHHMM ---
    start_dt = datetime.strptime(start_time, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )  # ADDED
    end_dt = datetime.strptime(end_time, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ) + timedelta(
        days=1
    )  # 要加24小时到结束时间

    start_str = start_dt.strftime("%Y%m%d%H%M")  # ADDED
    end_str = end_dt.strftime("%Y%m%d%H%M")  # ADDED

    date_query = f"submittedDate:[{start_str} TO {end_str}]"  # CHANGED: 生效的时间过滤

    # 组合完整查询
    query = f"({category_query}) AND ({date_query})"

    # 3. 配置 Client 和 Search
    # 即使只需要几天的论文，我们也建议设置较大的 max_results，
    # 然后通过日期判断来 break (停止) 循环，这样效率最高。
    client = arxiv.Client(page_size=100)

    search = arxiv.Search(
        query=query,
        max_results=max_results,  # 设置要获取的总量
        sort_by=arxiv.SortCriterion.SubmittedDate,  # 按提交时间排序
        sort_order=arxiv.SortOrder.Descending,  # 倒序：最新的在最前面
    )

    papers = []
    n = 0

    try:
        # 迭代获取结果
        for result in client.results(search):
            paper_info = {
                "title": result.title,  # 标题
                "authors": [author.name for author in result.authors],  # 作者列表
                "categories": result.categories,  # 分类列表
                "published_date": result.published.strftime("%Y-%m-%d"),
                "arxiv_id": result.entry_id.split("/")[-1],  # 提取arxiv ID
                "pdf_url": result.pdf_url,  # PDF链接
                "summary": result.summary,  # 摘要
            }

            papers.append(paper_info)
            n += 1
            if n % 10 == 0:
                print(f"已获取 {n} 篇论文")

            # # 打印论文信息
            # print(f"标题: {paper_info['title']}")
            # print(f"发布日期: {paper_info['published_date']}")
            # print("-" * 40)

    except Exception as e:
        print(f"查询过程中发生错误: {e}")
        return []

    # print(f"\n总共找到 {len(papers)} 篇论文")
    return papers


# 执行主程序
if __name__ == "__main__":
    import json, os

    categories = ["cs.CL", "cs.AI", "cs.LG", "cs.IR", "cs.CV"]
    date = "2026-01-20"
    if not os.path.exists("./output"):
        os.makedirs("./output")

    if not os.path.exists(f"./output/{date}"):
        os.makedirs(f"./output/{date}")

    papers = find_arxiv_papers(categories, date, date, max_results=1000)

    with open(f"./output/{date}/papers.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=4)

    print(f"搜索完成，共找到 {len(papers)} 篇符合要求的论文。")
    for paper in papers[:3]:
        print(f"标题: {paper['title']}")
        print(f"发布日期: {paper['published_date']}")
        print("-" * 40)
