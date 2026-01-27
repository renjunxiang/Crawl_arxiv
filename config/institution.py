# 大模型领域知名公司（中文名称为key，论文中常见名称列表为value）
company = {
    # 国外公司
    "OpenAI": ["OpenAI"],
    "谷歌": ["Google", "Google DeepMind", "DeepMind"],  # 补充DeepMind（谷歌旗下大模型核心团队）
    "微软": ["Microsoft", "Microsoft Research", "MSR"],  # 补充微软研究院（MSR）
    "Meta": ["Facebook", "Meta", "Meta Platforms", "Facebook", "LLaMA"],  # Meta的LLaMA系列是开源大模型核心
    "英伟达": ["NVIDIA", "Nvidia Corporation"],  # 大模型算力核心供应商（GPU）
    "Allen AI": ["Allen Institute for AI", "Allen AI", "AI2"],  # 新增：知名AI研究院（Allen AI）
    "Anthropic": ["Anthropic"],  # Claude大模型所属公司
    "Mistral AI": ["Mistral AI"],  # 欧洲知名开源大模型公司
    "xAI": ["xAI", "Grok"],  # 马斯克旗下，主打Grok大模型
    "Cohere": ["Cohere", "Cohere For AI"],  # 企业级大模型头部厂商
    "Salesforce": ["Salesforce", "Einstein GPT"],  # 企业服务+大模型融合代表
     "亚马逊": ["Amazon", "Amazon Web Services", "AWS", "Amazon Bedrock", "Titan"],  # Bedrock是大模型平台
    "IBM": ["IBM", "International Business Machines", "IBM Watson", "IBM Granite"],  # Granite是IBM大模型
    "苹果": ["Apple", "Apple Inc", "Apple Intelligence"],  # 新增：苹果大模型相关（Apple Intelligence为其AI品牌）
    
    # 国内公司
    "幻方": ["DeepSeek"],  # 幻方
    "阿里": ["Alibaba", "Alibaba Group", "qwen"],  # 阿里千问大模型
    "腾讯": ["Tencent", "Tencent Holdings", "Hunyuan"],  # 腾讯混元大模型
    "字节跳动": ["ByteDance", "Douyin", "Doubao"],  # 字节跳动豆包大模型
    "华为": ["Huawei", "Huawei Technologies", "PanGu"],  # 华为盘古大模型
    "智谱AI": ["Zhipu AI", "GLM", "智谱清言"],  # 智谱GLM系列大模型
    "Minimax": ["Minimax AI", "Shanghai Minimax AI", "ABAB"],  # Minimax
    "百度": ["Baidu", "Baidu Inc", "ERNIE"],  # 文心一言（ERNIE）是百度核心大模型
    "商汤科技": ["SenseTime", "SenseTime Group"],  # 商汤日日新大模型
    "科大讯飞": ["iFLYTEK", "iFLYTEK Co., Ltd", "Spark"],  # 讯飞星火大模型
    "美团": ["Meituan", "Meituan Dianping", "美团大模型"],  # 新增：美团
    "快手": ["Kuaishou", "Kuaishou Technology", "快手AI"],  # 新增：快手
    "虾皮": ["Shopee", "Sea Limited", "Shopee AI"],  # 新增：虾皮（Sea集团旗下）
    "月之暗面": ["Moonshot AI", "Moonshot Intelligence", "Kimi"],  # Kimi所属公司
    "阶跃星辰": ["StepFun AI", "StepFun", "Yi"],  # 开源Yi系列大模型
    "中国电信": ["China Telecom", "China Telecom Corporation", "Telecom AI"],  # 新增：中国电信
}

# 大模型领域知名高校（中文名称为key，论文中常见名称列表为value）
college = {
    # 国外科研院所
    "麻省理工学院": ["Massachusetts Institute of Technology", "MIT"],  # 补充简称MIT
    "斯坦福大学": ["Stanford University"],
    "卡内基梅隆大学": ["Carnegie Mellon University", "CMU"],  # 补充简称CMU
    "加州大学伯克利分校": ["University of California, Berkeley", "UC Berkeley","UCB"],
    "加州大学圣地亚哥分校": ["University of California, San Diego", "UCSD"],
    "伊利诺伊大学香槟分校": ["University of Illinois at Urbana-Champaign", "UIUC"],
    "普林斯顿大学": ["Princeton University"],
    "华盛顿大学": ["University of Washington", "UW"],
    "哥伦比亚大学": ["Columbia University"],
    "加州理工学院": ["California Institute of Technology", "Caltech"],
    "牛津大学": ["University of Oxford"],
    "剑桥大学": ["University of Cambridge"],
    "南洋理工大学": ["Nanyang Technological University", "NTU"],
    "新加坡国立大学": ["National University of Singapore", "NUS"],
    
    # 国内科研院所
    "清华大学": ["Tsinghua University", "THU"],
    "北京大学": ["Peking University", "PKU"],
    "复旦大学": ["Fudan University", "FDU"],  # 复旦：大模型多模态/自然语言处理研究核心
    "上海交通大学": ["Shanghai Jiao Tong University", "SJTU"],
    "中国科学技术大学": ["University of Science and Technology of China", "USTC"],
    "南京大学": ["Nanjing University", "NJU"],  # 南大：自然语言处理/大模型推理优化领域领先
    "中国人民大学": ["Renmin University of China", "RUC"],  # 新增：人大
    "浙江大学": ["Zhejiang University", "ZJU"],
    "哈尔滨工业大学": ["Harbin Institute of Technology", "HIT"],
    "西安交通大学": ["Xi'an Jiaotong University", "XJTU"],
    "中国科学院": ["Chinese Academy of Sciences", "CAS"],  # 中科院：国内AI基础研究核心机构
    "中国科学院大学": ["University of Chinese Academy of Sciences", "UCAS"],  # 国科大：依托中科院的顶尖研究型大学
    "北京智源人工智能研究院": ["Beijing Academy of Artificial Intelligence", "BAAI", "智源研究院"],  # 智源
    "香港大学": ["The University of Hong Kong", "HKU"],  # 港大：论文中常用HKU简称
    "香港科技大学": ["Hong Kong University of Science and Technology", "HKUST"],
    "香港中文大学": ["The Chinese University of Hong Kong", "CUHK"],
    "香港理工大学": ["The Hong Kong Polytechnic University", "PolyU"],  # 港理工：PolyU是通用简称
    "香港城市大学": ["City University of Hong Kong", "CityU"]  # 港城市：CityU是核心简称
}