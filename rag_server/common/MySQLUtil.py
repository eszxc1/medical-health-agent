import pymysql
from pymysql.cursors import DictCursor

from common.config import env, required_env

# 数据库连接配置（从环境变量读取，见 rag_server/.env.example）
DB_CONFIG = {
    'host': env('MYSQL_HOST', 'localhost'),
    'port': int(env('MYSQL_PORT', '3306')),
    'user': env('MYSQL_USER', 'root'),
    'password': required_env('MYSQL_PASSWORD'),
    'database': env('MYSQL_DATABASE', 'suse_agent'),
    'charset': 'utf8mb4'
}


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
        cursorclass=DictCursor
    )


def execute_query(sql, params=None):
    """执行查询语句，返回结果列表"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute_insert(sql, params=None):
    """执行插入语句，返回插入的自增ID"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def execute_update(sql, params=None):
    """执行更新语句，返回影响行数"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            affected_rows = cursor.execute(sql, params or ())
            conn.commit()
            return affected_rows
    finally:
        conn.close()