"""
用户过敏史 DAO
=============
操作表: user_allergies
"""

from common.MySQLUtil import execute_query, execute_insert, execute_update


def get_allergies_by_user_id(user_id):
    """查询用户的所有过敏记录"""
    sql = "SELECT allergy_name, severity FROM user_allergies WHERE user_id = %s ORDER BY created_at"
    return execute_query(sql, (user_id,))


def add_allergy(user_id, allergy_name, severity='moderate'):
    """
    新增过敏记录
    为什么使用 INSERT IGNORE 而非先查后插？
    —— 1) 一次数据库往返，性能更好
       2) 利用 UNIQUE 约束自动去重，避免并发场景下的竞态条件
       3) 如果记录已存在，execute_insert 返回 0，调用方可据此判断
    """
    sql = """
        INSERT IGNORE INTO user_allergies (user_id, allergy_name, severity)
        VALUES (%s, %s, %s)
    """
    return execute_insert(sql, (user_id, allergy_name, severity))


def delete_allergy(user_id, allergy_name):
    """删除过敏记录"""
    sql = "DELETE FROM user_allergies WHERE user_id = %s AND allergy_name = %s"
    return execute_update(sql, (user_id, allergy_name))