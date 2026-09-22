-- ============================================================
-- 基础表初始化：users + history
-- 说明：健康模块 5 张表见 init_health_tables.sql，
--       本文件必须先于健康表执行（健康表外键引用 users.user_id）。
-- 文件名按字母序排列，init_base_tables.sql 先于 init_health_tables.sql 执行。
-- ============================================================

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户id，主键自增',
    username VARCHAR(255) COMMENT '账号',
    email VARCHAR(255) COMMENT '邮箱号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 对话历史表
-- parent_id=0 表示根节点（一次对话的第一条），子节点指向其根节点的 history_id
CREATE TABLE IF NOT EXISTS history (
    history_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '对话记录保存的主键自增',
    question TEXT COMMENT '用户的问题',
    answer TEXT COMMENT 'AI的回复',
    parent_id INT DEFAULT 0 COMMENT '父节点ID（0=根节点）',
    email VARCHAR(255) COMMENT '绑定users表中的email',
    title VARCHAR(100) COMMENT '对话标题（重命名用）',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '对话时间',
    INDEX idx_email (email),
    INDEX idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史';