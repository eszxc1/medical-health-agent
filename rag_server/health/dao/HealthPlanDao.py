"""
健康计划 DAO
============
操作表: health_plans
"""

from common.MySQLUtil import execute_query, execute_insert, execute_update


def get_plans_by_user_id(user_id, plan_type=None, active_only=True):
    """
    查询用户的健康计划
    参数 plan_type: 可选，筛选特定类型（diet/exercise/medication/comprehensive）
    参数 active_only: 默认 True，只查询生效中的计划
    """
    sql = "SELECT plan_id, plan_type, title, content, start_date, end_date, created_at FROM health_plans WHERE user_id = %s"
    params = [user_id]

    if plan_type:
        sql += " AND plan_type = %s"
        params.append(plan_type)
    if active_only:
        sql += " AND is_active = 1"

    sql += " ORDER BY created_at DESC"
    return execute_query(sql, tuple(params))


def save_plan(user_id, plan_type, title, content, start_date=None, end_date=None):
    """
    保存健康计划
    返回: 新增记录的 plan_id
    """
    sql = """
        INSERT INTO health_plans (user_id, plan_type, title, content, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_insert(sql, (user_id, plan_type, title, content, start_date, end_date))


def archive_plan(plan_id):
    """
    归档健康计划（软删除：将 is_active 设为 0）
    为什么归档而非删除？—— 保留历史计划供用户回顾和 Agent 分析趋势
    """
    sql = "UPDATE health_plans SET is_active = 0 WHERE plan_id = %s"
    return execute_update(sql, (plan_id,))