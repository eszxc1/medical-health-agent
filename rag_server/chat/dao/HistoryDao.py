import pymysql

from chat.utils import MySQLUtil

# 查询对话的历史记录 --- 只查询父节点（parent_id=0）
def query_history_by_id(email):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor(pymysql.cursors.DictCursor) # 加这行
    # ★ 新增：查询 title 字段
    sql = "SELECT `history_id`,`question`,`title`,`create_time` FROM `history` WHERE `parent_id`=0 AND `email`=%s;"
    cur.execute(sql, [email])
    result = cur.fetchall()
    return result


# 根据选择的历史对话id查询全部对话记录
def query_history_all_by_id(history_id):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor(pymysql.cursors.DictCursor) # 加这行
    sql = "SELECT `history_id`,`question`,`answer`,`create_time` FROM `history` WHERE history_id=%s or parent_id=%s;"
    cur.execute(sql, [history_id, history_id])
    result = cur.fetchall()
    return result


# ===== 保存对话到数据库 =====
def save_chat_result(question, answer, parent_id, email):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # ★ 修复：指定列名，避免因新增 title 字段导致列数不匹配
        sql = "INSERT INTO `history` (`question`, `answer`, `parent_id`, `email`, `create_time`) VALUES (%s, %s, %s, %s, now());"
        cur.execute(sql, [question, answer, parent_id, email])
        conn.commit()
        # 获取当前新增的对话记录的id
        history_id = cur.lastrowid
        return history_id
    except Exception as e:
        print(e)
        conn.rollback()
        return False
    finally:
        cur.close()
        MySQLUtil.close_mysql_conn(cur, conn)


# 根据邮箱和关键词搜索历史记录
def search_history_by_email_and_keyword(email, keyword):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    # 在 question 字段中进行模糊查询，并按时间倒序排列
    sql = """
        SELECT `history_id`, `question`, `title`, `create_time`
        FROM `history` 
        WHERE `email`=%s 
            AND `parent_id`=0 
            AND `history_id` IN (
                -- 子查询：找出所有包含关键词的 history_id 及其对应的 parent_id
                SELECT DISTINCT IF(`parent_id`=0, `history_id`, `parent_id`) 
                FROM `history` 
                WHERE `email`=%s AND (`question` LIKE %s OR `answer` LIKE %s)
            )
        ORDER BY `create_time` DESC;
    """
    # 使用 %keyword% 进行模糊匹配
    params = [email, email, f"%{keyword}%", f"%{keyword}%"]
    cur.execute(sql, params)
    result = cur.fetchall()
    cur.close()
    MySQLUtil.close_mysql_conn(cur, conn)
    return result
# ===== ★ 新增：根据 history_id 物理删除记录 =====
def delete_history_record(history_id):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor()
    try:
        sql = "DELETE FROM `history` WHERE `history_id` = %s"
        cur.execute(sql, [history_id])
        conn.commit()
        return True
    except Exception as e:
        print(f"删除失败: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        MySQLUtil.close_mysql_conn(cur, conn)


# ===== ★ 新增：根据 history_id 更新对话标题 =====
def update_history_title(history_id, new_title):
    conn = MySQLUtil.get_mysql_conn()
    cur = conn.cursor()
    try:
        sql = "UPDATE `history` SET `title` = %s WHERE `history_id` = %s"
        cur.execute(sql, [new_title, history_id])
        conn.commit()
        return cur.rowcount  # ★ 返回受影响行数：0 表示未找到对应记录，-1 表示异常
    except Exception as e:
        print(f"更新标题失败: {e}")
        conn.rollback()
        return -1
    finally:
        cur.close()
        MySQLUtil.close_mysql_conn(cur, conn)


if __name__ == '__main__':
    print(query_history_by_id('test@example.com'))
