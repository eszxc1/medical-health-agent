-- ============================================================
-- 迁移脚本：为 user_medications 表新增 end_date 字段
-- 用途：记录停药日期，支持精确计算"服用时长"
-- 执行方式: mysql -u root -p suse_agent < migration_add_medication_end_date.sql
-- 说明：幂等脚本，可重复执行（通过信息查询判断字段是否已存在）
-- ============================================================

-- 使用 INFORMATION_SCHEMA 判断字段是否存在，避免重复添加报错
SET @dbname = 'suse_agent';
SET @tablename = 'user_medications';
SET @columnname = 'end_date';
SET @preparedStatement = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname
       AND TABLE_NAME = @tablename
       AND COLUMN_NAME = @columnname) > 0,
    'SELECT 1',  -- 字段已存在，跳过
    'ALTER TABLE user_medications ADD COLUMN end_date DATE DEFAULT NULL COMMENT ''停药日期'' AFTER started_date'
));

PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 验证结果
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = @dbname
  AND TABLE_NAME = @tablename
  AND COLUMN_NAME IN ('started_date', 'end_date');
