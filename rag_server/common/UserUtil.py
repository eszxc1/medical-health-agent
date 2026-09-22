"""
用户身份解析工具
=================
为什么需要这个模块？
—— 现有代码中，前端和聊天流程使用 email 作为用户标识（sessionStorage 存储 email），
   但数据库设计中 user_id 才是稳定的主键。如果未来用户修改邮箱，只有 users 表需要更新，
   所有关联表（user_profiles、user_allergies 等）因为使用 user_id 做外键，不受影响。

使用方式：
    from common.UserUtil import resolve_user_id
    user_id = resolve_user_id("user@example.com")
"""

from common.MySQLUtil import execute_query


def resolve_user_id(email: str) -> int:
    """
    将 email 解析为 user_id，作为健康模块的统一身份入口。

    为什么返回 int 而不是 dict？
    —— 调用方只需要 user_id 做后续查询，直接返回整数可以让调用代码更简洁。

    为什么抛出异常而不是返回 None？
    —— 如果 email 不存在，说明前端传了无效用户，这是异常情况，应该让调用方感知并处理。

    Raises:
        ValueError: 当 email 对应的用户不存在时抛出
    """
    result = execute_query(
        "SELECT user_id FROM users WHERE email = %s", (email,)
    )
    if not result:
        raise ValueError(f"用户不存在: {email}")
    return result[0]["user_id"]