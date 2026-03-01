import re
from pdf2image import convert_from_path
import os


def pdf_first_page_to_image(
    pdf_path: str,
    output_img_path: str,
    dpi: int = 300,  # 视频素材建议300dpi（高清），可调整为200/400
    img_format: str = "png",  # 推荐png（无损），也可设为jpg
    poppler_path: str = "D:/software/poppler-25.12.0/Library/bin",  # Windows需指定Poppler的bin路径，mac/Linux无需
) -> bool:
    """
    将PDF的第一页转换为高清图片（适配AI论文视频制作）
    :param pdf_path: 输入PDF文件路径（绝对/相对）
    :param output_img_path: 输出图片路径（如：output/arxiv_2602.png）
    :param dpi: 图片分辨率（视频素材建议300dpi）
    :param img_format: 输出格式（png/jpg/bmp）
    :param poppler_path: Windows系统需指定Poppler的bin目录路径
    :return: 转换成功返回True，失败返回False
    """
    # 校验输入PDF是否存在
    if not os.path.exists(pdf_path):
        print(f"错误：PDF文件不存在 → {pdf_path}")
        return False

    # 确保输出目录存在
    output_dir = os.path.dirname(output_img_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 转换PDF第一页为图片对象（first_page=1, last_page=1 限定只取第一页）
        pages = convert_from_path(
            pdf_path=pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=1,
            poppler_path=poppler_path,
            fmt=img_format,
            thread_count=1,  # 单线程更稳定，避免多线程报错
        )

        # 校验是否提取到页面（防止PDF为空）
        if not pages:
            print(f"错误：PDF文件无页面 → {pdf_path}")
            return False

        # 保存第一页图片
        first_page = pages[0]
        first_page.save(output_img_path, img_format.upper())
        print(f"成功：PDF第一页已保存为 → {output_img_path}")
        return True

    except Exception as e:
        print(f"转换失败：{str(e)}")
        return False


def write_copy(paper) -> str:
    """
    输入的paper是一个字典，包含了论文的信息
    输出的copy是一个字符串，包含了论文的机构、贡献、个人观点的文案
    """
    arxiv_id = paper["arxiv_id"]
    first_institution = paper["first_institution"]
    note = paper["note"]

    # 论文贡献
    pattern = r"主要贡献：(.+?)(?=\s*[🔸📝🔎💡]|$)"
    match = re.search(pattern, note, re.DOTALL)  # re.DOTALL 让 . 匹配换行
    if match:
        contribution = match.group(1).strip()
        # print(contribution)
    else:
        contribution = ""

    # # 个人观点
    # pattern = r"个人观点[：:]*\s*(.+)$"
    # match = re.search(pattern, note, re.DOTALL)  # re.DOTALL 让 . 匹配换行
    # if match:
    #     option = match.group(1).strip()
    #     # print(option)
    # else:
    #     option = ""

    content = f"🔸{arxiv_id}：{contribution}"

    return content


if __name__ == "__main__":
    paper = {
        "title": "ForgeryVCR: Visual-Centric Reasoning via Efficient Forensic Tools in MLLMs for Image Forgery Detection and Localization",
        "authors": [
            "Youqi Wang",
            "Shen Chen",
            "Haowei Wang",
            "Rongxuan Peng",
            "Taiping Yao",
            "Shunquan Tan",
            "Changsheng Chen",
            "Bin Li",
            "Shouhong Ding",
        ],
        "categories": ["cs.CV"],
        "published_date": "2026-02-15",
        "arxiv_id": "2602.14098v1",
        "pdf_url": "https://arxiv.org/pdf/2602.14098v1",
        "summary": "Existing Multimodal Large Language Models (MLLMs) for image forgery detection and localization predominantly operate under a text-centric Chain-of-Thought (CoT) paradigm. However, forcing these models to textually characterize imperceptible low-level tampering traces inevitably leads to hallucinations, as linguistic modalities are insufficient to capture such fine-grained pixel-level inconsistencies. To overcome this, we propose ForgeryVCR, a framework that incorporates a forensic toolbox to materialize imperceptible traces into explicit visual intermediates via Visual-Centric Reasoning. To enable efficient tool utilization, we introduce a Strategic Tool Learning post-training paradigm, encompassing gain-driven trajectory construction for Supervised Fine-Tuning (SFT) and subsequent Reinforcement Learning (RL) optimization guided by a tool utility reward. This paradigm empowers the MLLM to act as a proactive decision-maker, learning to spontaneously invoke multi-view reasoning paths including local zoom-in for fine-grained inspection and the analysis of invisible inconsistencies in compression history, noise residuals, and frequency domains. Extensive experiments reveal that ForgeryVCR achieves state-of-the-art (SOTA) performance in both detection and localization tasks, demonstrating superior generalization and robustness with minimal tool redundancy. The project page is available at https://youqiwong.github.io/projects/ForgeryVCR/.",
        "tag": "大模型工具集",
        "success": True,
        "file_path": "./output/2026-02-15/papers\\2602.14098v1【大模型工具集-腾讯】ForgeryVCR_ Visual-Centric Reasoning via Efficient Forensic Tools in MLLMs for Image Forgery Detection and Localization.pdf",
        "institution_status": "keep",
        "institution": "腾讯、深圳大学",
        "first_institution": "腾讯",
        "institution_category": "国内工业界",
        "note": "📖标题：ForgeryVCR: Visual-Centric Reasoning via Efficient Forensic Tools in MLLMs for Image Forgery Detection and Localization\n🌐来源：arXiv, 2602.14098v1\n\n笔记标题：视觉中心推理防伪造\n\n🛎️文章简介  \n🔸研究问题：如何让多模态大语言模型在图像伪造检测与定位中避免因依赖文本推理而产生的语义幻觉？  \n🔸主要贡献：提出ForgeryVCR框架，首次在图像伪造分析中实现纯视觉中心推理（Visual-Centric Reasoning），通过 forensic 工具将不可见篡改痕迹显式转化为视觉中间表征，彻底绕过文本描述环节。\n\n📝重点思路  \n🔸构建混合取证工具箱，集成ELA（压缩异常）、FFT（频域异常）、NPP（噪声指纹）三类互补视觉算子及Zoom-In细粒度聚焦机制，将低层统计不一致性映射为高对比度、可感知的视觉图。  \n🔸设计增益驱动的轨迹合成流程：基于轻量单工具微调性能评估，筛选对每个样本具有信息增益的工具子集，并按增益排序生成单工具、多工具及无工具三类推理路径。  \n🔸提出策略性工具学习范式：先通过监督微调（SFT）教会模型工具调用语法与视觉证据累积逻辑；再以组相对策略优化（GRPO）进行强化学习，引入工具效用奖励（Rtool）引导模型仅在必要时调用工具。  \n🔸采用视觉-文本解耦架构：推理链完全由图像输入、工具调用代码、工具输出图及最终答案构成，禁用任何<think>类文本推理步骤，确保决策严格锚定于显式视觉证据。\n\n🔎分析总结  \n🔸视觉中心推理显著优于图文混合或纯文本推理：消除了语义幻觉，在检测F1和定位IoU上分别比ForgeryVCR*提升5.15%和0.57%，验证视觉证据直接驱动决策更可靠。  \n🔸工具效用奖励有效抑制冗余调用：RL阶段后，无效工具调用（如在真图上滥用Zoom-In）下降超90%，同时检测准确率反升，证明模型学会“按需取证”。  \n🔸四工具组合（ELA+FFT+NPP+Zoom-In）达到性能饱和点：添加更多工具（如DCT、CFA）仅带来<0.1%指标提升，证实所选工具覆盖压缩、频域、噪声、细节四大伪造维度且无冗余。  \n🔸框架具备强泛化与鲁棒性：在8个跨域基准上SOTA，对JPEG压缩、高斯噪声等真实退化保持稳定；BBox-IoU达0.5555，远超基线，说明定位能力源于模型自身视觉推理而非SAM2补偿。\n\n💡个人观点  \n该工作的核心创新在于颠覆了MLLM用于取证的范式——不再把视觉模型当作文本生成器的辅助编码器，而是将其重构为“视觉侦探代理”，以工具执行为动作、视觉图为观察、显式证据为推理基石。其增益驱动轨迹构造与工具效用奖励设计，为多模态推理中“何时调用何工具”这一关键难题提供了可复现、可优化的解决方案，对AI安全、可信视觉推理具有方法论启示意义。\n    ",
    }
    c = write_copy(paper)
    print(c)
