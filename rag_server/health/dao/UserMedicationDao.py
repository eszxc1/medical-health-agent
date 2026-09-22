"""
用户用药 DAO
============
操作表: user_medications
"""

from common.MySQLUtil import execute_query, execute_insert, execute_update


def get_medications_by_user_id(user_id, active_only=True):
    """
    查询用户的用药记录
    参数 active_only: 默认 True，只查询当前正在服用的药物（is_active=1）
        —— 为什么默认只查当前用药？
           药物风险检查只关心"正在服用"的药物，历史已停药的不需要检查。
           如需查询全部用药记录（含历史），传入 active_only=False。
    """
    sql = "SELECT medication_name, dosage, frequency, started_date, end_date, is_active FROM user_medications WHERE user_id = %s"
    if active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY started_date DESC"
    return execute_query(sql, (user_id,))


def add_medication(user_id, medication_name, dosage=None, frequency=None, started_date=None):
    """
    新增或更新用药记录
    如果药物已存在（同 user_id + medication_name），则更新剂量、频率和开始日期。
    —— 使用 ON DUPLICATE KEY UPDATE 实现"存在则更新，不存在则插入"。
    ★ 关键：ON DUPLICATE KEY UPDATE 必须更新 started_date，否则用户"纠正时间"时旧日期不会被覆盖。
      同时 end_date = NULL 重置停药状态（用户重新开始吃药时应清除旧的停药日期）。
    """
    sql = """
        INSERT INTO user_medications (user_id, medication_name, dosage, frequency, started_date)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            dosage = VALUES(dosage),
            frequency = VALUES(frequency),
            started_date = VALUES(started_date),
            end_date = NULL,
            is_active = 1
    """
    return execute_insert(sql, (user_id, medication_name, dosage, frequency, started_date))


def stop_medication(user_id, medication_name, end_date=None):
    """
    停用药物（软删除：将 is_active 设为 0，并记录停药日期 end_date）
    为什么是软删除而非物理删除？
    —— 保留用药历史记录，便于未来回溯分析（如"曾经用过什么药、效果如何"）。
       物理删除会丢失这些有价值的数据。
    为什么记录 end_date？
    —— 支持精确计算"服用时长" = end_date - started_date，
       否则停药的药物无法回答"吃了多久"这类时间问题。
    """
    sql = """
        UPDATE user_medications
        SET is_active = 0, end_date = %s
        WHERE user_id = %s AND medication_name = %s
    """
    return execute_update(sql, (end_date, user_id, medication_name))