from common.MySQLUtil import execute_query, execute_insert, execute_update  # yllwyw 新增

def find_user_by_username(username):
    """根据用户名查询用户"""
    sql = "SELECT user_id, username, email FROM users WHERE username = %s"
    return execute_query(sql, (username,))

def find_user_by_email(email):
    """根据邮箱查询用户"""
    sql = "SELECT user_id, username, email FROM users WHERE email = %s"
    return execute_query(sql, (email,))

def insert_user(username, email):
    """插入新用户"""
    sql = "INSERT INTO users (username, email) VALUES (%s, %s)"
    return execute_insert(sql, (username, email))


# yllwyw 新增：用户注销所需数据库操作
def delete_user_by_email(email):
    sql = "DELETE FROM users WHERE email = %s"
    return execute_update(sql, (email,))
# yllwyw 新增结束
