-- ============================================================
-- 医疗健康管理模块 - 数据库初始化脚本
-- 数据库: suse_agent
-- 执行方式: mysql -u root -p suse_agent < init_health_tables.sql
-- ============================================================

-- 1. 用户健康画像表（核心表）
-- 为什么 user_id 用 UNIQUE 而非直接用 user_id 做主键？
-- —— 使用 profile_id 作为独立主键，便于未来做审计日志和版本追溯。
--    UNIQUE 约束保证一个用户只有一份画像，同时保留扩展空间。
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '画像主键ID',
    user_id INT NOT NULL UNIQUE COMMENT '关联 users 表的用户ID',
    /* 基本信息 */
    age INT COMMENT '年龄',
    gender ENUM('male', 'female', 'other') COMMENT '性别',
    height_cm DECIMAL(5,1) COMMENT '身高(cm)',
    weight_kg DECIMAL(5,1) COMMENT '体重(kg)',
    blood_type ENUM('A', 'B', 'AB', 'O') COMMENT '血型',
    /* 生活习惯 —— 使用 ENUM 而非自由文本，保证数据统计的准确性 */
    smoking_status ENUM('never', 'former', 'current') COMMENT '吸烟状态',
    alcohol_consumption ENUM('none', 'occasional', 'moderate', 'heavy') COMMENT '饮酒情况',
    exercise_frequency VARCHAR(50) COMMENT '运动频率（如"每周3次"）',
    /* 时间戳 */
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户健康画像';

-- 2. 用户过敏史（关联表）
-- 为什么拆分为独立表而非 JSON 字段？
-- —— 1) 支持 SQL 统计分析（如 COUNT 某种过敏原的用户数）
--    2) UNIQUE 约束防止重复录入
--    3) 未来可扩展 severity、reaction 等字段
CREATE TABLE IF NOT EXISTS user_allergies (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    allergy_name VARCHAR(100) NOT NULL COMMENT '过敏原名称（如"青霉素"、"花粉"）',
    severity ENUM('mild', 'moderate', 'severe') DEFAULT 'moderate' COMMENT '严重程度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_allergy (user_id, allergy_name) COMMENT '防止同一用户重复录入同一过敏原'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户过敏史';

-- 3. 用户慢性病（关联表）
-- 为什么需要 diagnosed_date 和 notes 字段？
-- —— 慢病管理需要知道确诊时间以评估病程，notes 用于记录医生的特别嘱咐
CREATE TABLE IF NOT EXISTS user_chronic_diseases (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    disease_name VARCHAR(100) NOT NULL COMMENT '疾病名称（如"高血压"、"2型糖尿病"）',
    diagnosed_date DATE COMMENT '确诊日期',
    notes VARCHAR(500) COMMENT '备注（如"血压控制稳定，每日监测"）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_disease (user_id, disease_name) COMMENT '防止同一疾病重复录入'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户慢性病';

-- 4. 用户当前用药（关联表）
-- 为什么需要 is_active 字段？
-- —— 用户可能曾经服用某种药物但已停药，我们需要区分"当前用药"和"历史用药"
--    以进行准确的药物相互作用检查
CREATE TABLE IF NOT EXISTS user_medications (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    medication_name VARCHAR(100) NOT NULL COMMENT '药物名称（如"硝苯地平"、"二甲双胍"）',
    dosage VARCHAR(100) COMMENT '剂量（如"10mg"）',
    frequency VARCHAR(100) COMMENT '服用频率（如"每日两次"）',
    started_date DATE COMMENT '开始服用日期',
    end_date DATE DEFAULT NULL COMMENT '停药日期（为 NULL 表示仍在服用）',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否仍在服用（1=是，0=已停药）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_medication (user_id, medication_name) COMMENT '防止同一药物重复录入'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户当前用药';

-- 5. 健康计划表
-- 为什么 content 使用 TEXT 而非 JSON 类型？
-- —— 1) 与现有代码风格一致（history 表的 question/answer 也是 TEXT）
--    2) Agent 生成的计划内容结构灵活，JSON Schema 约束反而限制扩展性
--    3) 应用层做序列化/反序列化更灵活
CREATE TABLE IF NOT EXISTS health_plans (
    plan_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '计划ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    plan_type ENUM('diet', 'exercise', 'medication', 'comprehensive') COMMENT '计划类型',
    title VARCHAR(200) COMMENT '计划标题（如"高血压控盐饮食计划"）',
    content TEXT COMMENT '计划详细内容（JSON 格式，由 Agent 生成）',
    start_date DATE COMMENT '计划开始日期',
    end_date DATE COMMENT '计划结束日期',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否生效中（1=是，0=已归档）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    -- ★ 补充：显式索引，优化 Agent 高频查询"某用户的所有计划"
    INDEX idx_user_id (user_id),
    INDEX idx_user_active_plans (user_id, is_active) COMMENT '覆盖索引：查询某用户的生效计划'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康计划';