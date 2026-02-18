from copy import deepcopy
import json
import requests
import time
import os
import re


class DownloadPaper:
    def __init__(self, target_folder="2099-99-99"):
        self.target_folder = target_folder
        # 创建目标文件夹（如果不存在）
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

    def download_papers(self, papers, target_folder=None):
        """
        下载PDF论文到指定文件夹

        参数:
        papers (list): 包含论文信息的列表，每个元素是一个字典，包含"pdf_url"键，值为PDF下载链接
        target_folder (str): 目标文件夹名称
        """
        if target_folder is None:
            target_folder = self.target_folder

        download_info = []
        # 遍历所有链接
        for idx, paper in enumerate(papers, 1):
            print(f"正在下载 ({idx}/{len(papers)}): {paper.get('arxiv_id', '')}")
            url = paper.get("pdf_url", "")
            title = paper.get("title", "")
            tag = paper.get("tag", "")
            arxiv_id = paper.get("arxiv_id", "")
            try:
                # 替换非法字符为 _
                invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
                sanitized = re.sub(invalid_chars, "_", title)
                # 移除首尾空格和句点（Windows 不允许文件名以空格或句点结尾）
                sanitized = sanitized.strip().strip(".")

                # 构建完整文件路径
                filename = f"{arxiv_id}【{tag}】{sanitized}.pdf"
                file_path = os.path.join(target_folder, filename)

                # 检查文件是否已存在
                if os.path.exists(file_path):
                    print(f"跳过已存在的文件: {filename}")
                else:
                    # 下载PDF
                    response = requests.get(url, stream=True)
                    response.raise_for_status()  # 检查HTTP错误

                    # 保存文件
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"下载成功: {filename}")

                paper_ = deepcopy(paper)
                paper_["file_path"] = file_path
                download_info.append(paper_)

            except Exception as e:
                print(f"下载失败 ({url}): {str(e)}")
                print(f"下载成功: {paper.get('arxiv_id', '')}")
                time.sleep(1)  # 避免请求过快

        print(
            f"\n所有下载完成! 共下载 {len(papers)} 个文件到 {os.path.abspath(target_folder)}"
        )

        return download_info
