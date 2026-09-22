"""
用户慢性病 DAO
==============
操作表: user_chronic_diseases
"""

from common.MySQLUtil import execute_query, execute_insert, execute_update


def get_diseases_by_user_id(user_id):
    """查询用户的所有慢性病记录"""
    sql = """
        SELECT disease_name, diagnosed_date, notes
        FROM user_chronic_diseases
        WHERE user_id = %s
        ORDER BY diagnosed_date DESC
    """
    return execute_query(sql, (user_id,))


def add_disease(user_id, disease_name, diagnosed_date=None, notes=None):
    """
    新增慢性病记录
    参数 diagnosed_date 设计为可选 —— 用户可能不知道确切确诊日期，允许后续补充
    """
    sql = """
        INSERT IGNORE INTO user_chronic_diseases (user_id, disease_name, diagnosed_date, notes)
        VALUES (%s, %s, %s, %s)
    """
    return execute_insert(sql, (user_id, disease_name, diagnosed_date, notes))


def delete_disease(user_id, disease_name):
    """删除慢性病记录"""
    sql = "DELETE FROM user_chronic_diseases WHERE user_id = %s AND disease_name = %s"
    return execute_update(sql, (user_id, disease_name))