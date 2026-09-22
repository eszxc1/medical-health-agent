import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from common.config import env, required_env

# 封装获取mysql连接对象
def get_mysql_conn():
    return pymysql.connect(
        host=env("MYSQL_HOST", "localhost"),  # 数据库的IP地址
        port=int(env("MYSQL_PORT", "3306")),  # 数据库的端口号
        user=env("MYSQL_USER", "root"),  # 数据库的账号
        password=required_env("MYSQL_PASSWORD"),  # 数据库的root账号对应密码
        database=env("MYSQL_DATABASE", "suse_agent"),  # 数据库的名称
        charset="utf8mb4",  # 设置数据库的编码格式
        cursorclass=pymysql.cursors.DictCursor,  # 设置游标对象返回的数据类型为字典
    )

# 封装关闭mysql连接
def close_mysql_conn(cursor, conn):
    cursor.close()  # 关闭游标对象
    conn.close()    # 关闭数据库连接