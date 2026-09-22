"""
疾病名称同义词字典
==================
用途：解决 MySQL 中用户记录的疾病名与 Neo4j 图谱节点名不一致导致的交叉比对失败问题。

为什么独立成配置文件？
—— 同义词需要根据实际数据逐步扩充，独立出来避免每次扩充都要改动核心工具逻辑。

映射方向：
    key = 规范名称（图谱节点常用名）
    value = 别名列表（用户可能使用的叫法）

使用方式：
    from health.disease_aliases import DISEASE_ALIASES, normalize_disease_name
"""

# 高频常见疾病别名映射（后续可逐步扩充）
DISEASE_ALIASES = {
    "高血压": ["原发性高血压", "继发性高血压", "高血压病", "血压高"],
    "糖尿病": ["2型糖尿病", "1型糖尿病", "二型糖尿病", "一型糖尿病", "血糖高"],
    "冠心病": ["冠状动脉粥样硬化性心脏病", "缺血性心脏病", "冠状动脉心脏病"],
    "胃炎": ["慢性胃炎", "浅表性胃炎", "萎缩性胃炎", "急性胃炎"],
    "胃溃疡": ["消化性溃疡", "消化道溃疡", "胃十二指肠溃疡"],
    "高脂血症": ["高血脂", "血脂异常", "高胆固醇血症", "高甘油三酯血症"],
    "痛风": ["高尿酸血症"],
    "哮喘": ["支气管哮喘", "过敏性哮喘"],
    "肾功能不全": ["慢性肾病", "慢性肾脏病", "肾衰竭", "尿毒症"],
    "肝功能不全": ["肝硬化", "肝炎", "肝功能异常"],
}


def normalize_disease_name(name):
    """
    将疾病名称规范化为标准形式。
    如果名称是某个别名，返回其规范名；否则原样返回。
    """
    if not name:
        return name
    for canonical, aliases in DISEASE_ALIASES.items():
        if name == canonical or name in aliases:
            return canonical
    return name


def is_disease_match(user_disease, graph_disease):
    """
    判断用户记录的疾病名与图谱节点名是否指向同一种疾病。

    匹配策略（从严格到宽松）：
    1. 精确匹配：两个名称完全相同
    2. 规范化匹配：通过同义词字典规范化后完全相同（如"原发性高血压"→"高血压"）
    3. 包含匹配：一方是另一方的子串（如"糖尿病"匹配"2型糖尿病"）
    """
    if not user_disease or not graph_disease:
        return False

    # 策略 1：精确匹配
    if user_disease == graph_disease:
        return True

    # 策略 2：规范化匹配
    if normalize_disease_name(user_disease) == normalize_disease_name(graph_disease):
        return True

    # 策略 3：包含匹配（双向）
    if user_disease in graph_disease or graph_disease in user_disease:
        return True

    return False