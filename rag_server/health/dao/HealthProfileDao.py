"""
用户健康画像 DAO
===============
操作表: user_profiles
设计模式: 延续现有 DAO 层风格 —— 函数式、pymysql DictCursor、common.MySQLUtil
"""

from common.MySQLUtil import execute_query, execute_insert, execute_update


def get_profile_by_user_id(user_id):
    """
    根据 user_id 查询用户健康画像
    返回: 单条记录 dict，或空列表
    """
    sql = "SELECT * FROM user_profiles WHERE user_id = %s"
    return execute_query(sql, (user_id,))


def create_profile(user_id, age=None, gender=None, height_cm=None, weight_kg=None,
                   blood_type=None, smoking_status=None, alcohol_consumption=None,
                   exercise_frequency=None):
    """
    创建用户健康画像（首次填写时调用）
    为什么参数使用关键字参数而非字典？
    —— 显式参数让调用方（MCP 工具 / Service 层）清楚知道需要传哪些字段，
       同时 IDE 可以给出自动补全提示，减少传参错误。
    """
    sql = """
        INSERT INTO user_profiles
            (user_id, age, gender, height_cm, weight_kg, blood_type,
             smoking_status, alcohol_consumption, exercise_frequency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_insert(sql, (
        user_id, age, gender, height_cm, weight_kg, blood_type,
        smoking_status, alcohol_consumption, exercise_frequency
    ))


def update_profile(user_id, **kwargs):
    """
    增量更新用户健康画像

    为什么用 **kwargs 动态拼接 SQL？
    —— 画像包含 10+ 个字段，Agent 每次可能只更新其中 1-2 个（如"我今年30岁了"只更新 age）。
       如果使用固定参数，每次调用都必须传全部字段，既不方便也容易误覆盖已有数据。

    安全设计:
    —— 白名单机制：只允许更新 user_profiles 表中真实存在的字段，
       防止 SQL 注入和非法字段写入。
    —— 如果 kwargs 中没有任何合法字段，返回 0（0 行受影响），调用方可据此判断。
    """
    if not kwargs:
        return 0

    # 白名单：只允许更新画像表中已定义的字段
    allowed_fields = {
        'age', 'gender', 'height_cm', 'weight_kg', 'blood_type',
        'smoking_status', 'alcohol_consumption', 'exercise_frequency'
    }

    set_clauses = []
    values = []
    for field, value in kwargs.items():
        if field in allowed_fields:
            set_clauses.append(f"`{field}` = %s")
            values.append(value)

    if not set_clauses:
        return 0

    values.append(user_id)
    sql = f"UPDATE user_profiles SET {', '.join(set_clauses)} WHERE user_id = %s"
    return execute_update(sql, tuple(values))


def upsert_profile(user_id, **kwargs):
    """
    创建或更新用户画像（ON DUPLICATE KEY UPDATE）

    为什么需要这个函数？
    —— Agent 对话中，用户可能说"我有高血压"，此时画像可能已存在（更新）或不存在（创建）。
       使用 MySQL 的 ON DUPLICATE KEY UPDATE 语法，一条 SQL 搞定两种场景，
       避免先 SELECT 再判断的两次数据库往返。

    注意: 此函数要求 user_id 列有 UNIQUE 约束（已在建表脚本中定义）。
    """
    if not kwargs:
        return 0

    allowed_fields = {
        'age', 'gender', 'height_cm', 'weight_kg', 'blood_type',
        'smoking_status', 'alcohol_consumption', 'exercise_frequency'
    }

    # 过滤出合法字段
    valid_kwargs = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not valid_kwargs:
        return 0

    columns = list(valid_kwargs.keys())
    values = [user_id] + [valid_kwargs[col] for col in columns]

    # 构建 INSERT ... ON DUPLICATE KEY UPDATE
    placeholders = ', '.join(['%s'] * (len(columns) + 1))
    update_clause = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in columns])

    sql = f"""
        INSERT INTO user_profiles (user_id, {', '.join(columns)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
    """
    return execute_update(sql, tuple(values))