-- ============================================
-- 学生成长综合素质评价系统 - 完整数据库结构
-- MySQL 9.1
-- ============================================

CREATE DATABASE IF NOT EXISTS calligraphy_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE calligraphy_ai;

-- ============================================
-- 1. 用户表 (统一用户管理)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL DEFAULT 'student',
    real_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    avatar VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员账户 (密码: admin123)
INSERT INTO users (username, password_hash, role, real_name) VALUES 
('admin', '$2b$12$tCjt2HWaomLhJQ7JpBE8XOezj1DgEU4x..ObUPSOorTh7nE/vQiR2', 'admin', '系统管理员');

-- ============================================
-- 2. 学期表
-- ============================================
CREATE TABLE IF NOT EXISTS semesters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,  -- 如 "2024-2025"
    term ENUM('first', 'second') NOT NULL,  -- 第一学期/第二学期
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_current (is_current),
    UNIQUE KEY uk_year_term (academic_year, term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. 年级表
-- ============================================
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认年级
INSERT INTO grades (name, sort_order) VALUES 
('一年级', 1), ('二年级', 2), ('三年级', 3),
('四年级', 4), ('五年级', 5), ('六年级', 6);

-- ============================================
-- 4. 教师表
-- ============================================
CREATE TABLE IF NOT EXISTS teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    employee_no VARCHAR(20) UNIQUE,
    name VARCHAR(50) NOT NULL,
    gender ENUM('male', 'female') DEFAULT 'female',
    subjects VARCHAR(200),  -- 任教科目，逗号分隔
    title VARCHAR(50),  -- 职称
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. 班级表
-- ============================================
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    head_teacher_id INT,  -- 班主任
    semester_id INT,
    student_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (head_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    INDEX idx_grade (grade_id),
    UNIQUE KEY uk_grade_name (grade_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. 学生表
-- ============================================
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    student_no VARCHAR(20) NOT NULL UNIQUE,  -- 学号
    name VARCHAR(50) NOT NULL,
    gender ENUM('male', 'female') DEFAULT 'male',
    class_id INT,
    barcode VARCHAR(50),  -- 条码内容
    birth_date DATE,
    id_card VARCHAR(18),
    parent_name VARCHAR(50),
    parent_phone VARCHAR(20),
    address VARCHAR(255),
    photo VARCHAR(255),
    enrollment_date DATE,
    status ENUM('active', 'graduated', 'transferred', 'suspended') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL,
    INDEX idx_class (class_id),
    INDEX idx_barcode (barcode),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 7. 评价指标分类
-- ============================================
CREATE TABLE IF NOT EXISTS indicator_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    icon VARCHAR(50),
    color VARCHAR(20),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认分类
INSERT INTO indicator_categories (name, description, sort_order) VALUES 
('学业成绩', '语文、数学、英语等学科成绩', 1),
('体育健康', '体育成绩、体测数据、健康状况', 2),
('艺术素养', '书法、美术、音乐等艺术评价', 3),
('德育评价', '品德行为、纪律表现', 4),
('劳动实践', '家务劳动、社会实践', 5),
('传统文化', '经典诵读、国学等级', 6);

-- ============================================
-- 8. 评价指标
-- ============================================
CREATE TABLE IF NOT EXISTS indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20),  -- 指标代码
    type ENUM('score', 'level', 'number', 'boolean', 'text') NOT NULL DEFAULT 'score',
    -- score: 分数 (0-100)
    -- level: 等级 (优秀/良好/及格/不及格)
    -- number: 数值 (如跳绳个数)
    -- boolean: 是否 (是/否)
    -- text: 文字评价
    options JSON,  -- 等级选项 ["优秀","良好","及格","不及格"]
    max_score DECIMAL(5,2) DEFAULT 100,
    min_score DECIMAL(5,2) DEFAULT 0,
    weight DECIMAL(3,2) DEFAULT 1.0,  -- 权重
    description VARCHAR(255),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES indicator_categories(id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认指标
INSERT INTO indicators (category_id, name, code, type, options, sort_order) VALUES 
-- 学业成绩
(1, '语文单元考试', 'YW_DY', 'score', NULL, 1),
(1, '语文期中考试', 'YW_QZ', 'score', NULL, 2),
(1, '语文期末考试', 'YW_QM', 'score', NULL, 3),
(1, '数学单元考试', 'SX_DY', 'score', NULL, 4),
(1, '数学期中考试', 'SX_QZ', 'score', NULL, 5),
(1, '数学期末考试', 'SX_QM', 'score', NULL, 6),
(1, '英语单元考试', 'YY_DY', 'score', NULL, 7),
(1, '英语期中考试', 'YY_QZ', 'score', NULL, 8),
(1, '英语期末考试', 'YY_QM', 'score', NULL, 9),
-- 体育健康
(2, '体育成绩', 'TY_CJ', 'level', '["优秀","良好","及格","不及格"]', 1),
(2, '跳绳成绩', 'TS_CJ', 'number', NULL, 2),
(2, '体检结果', 'TJ_JG', 'level', '["优秀","良好","及格","不及格"]', 3),
(2, '是否肥胖', 'FP', 'boolean', NULL, 4),
(2, '视力情况', 'SL', 'text', NULL, 5),
-- 艺术素养
(3, '静心习字成绩', 'SF_CJ', 'score', NULL, 1),
(3, '美术成绩', 'MS_CJ', 'level', '["优秀","良好","及格","不及格"]', 2),
(3, '音乐成绩', 'YL_CJ', 'level', '["优秀","良好","及格","不及格"]', 3),
-- 德育评价
(4, '德育评价', 'DY_PJ', 'level', '["优秀","良好","及格","不及格"]', 1),
(4, '纪律表现', 'JL_BX', 'level', '["优秀","良好","及格","不及格"]', 2),
-- 劳动实践
(5, '家务劳动', 'JW_LD', 'level', '["优秀","良好","及格","不及格"]', 1),
(5, '社会实践', 'SH_SJ', 'level', '["优秀","良好","及格","不及格"]', 2),
-- 传统文化
(6, '经典等级', 'JD_DJ', 'level', '["一级","二级","三级","四级","五级"]', 1),
(6, '国学等级', 'GX_DJ', 'level', '["一级","二级","三级","四级","五级"]', 2);

-- ============================================
-- 9. 学生评价数据
-- ============================================
CREATE TABLE IF NOT EXISTS evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    indicator_id INT NOT NULL,
    semester_id INT NOT NULL,
    value VARCHAR(255),  -- 评价值(分数/等级/数值/文字)
    score DECIMAL(5,2),  -- 转换后的分数(用于统计)
    remark VARCHAR(255),
    recorded_by INT,  -- 录入教师
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id),
    UNIQUE KEY uk_student_indicator_semester (student_id, indicator_id, semester_id),
    INDEX idx_student (student_id),
    INDEX idx_semester (semester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 10. 书法批改记录 (扩展现有表)
-- ============================================
DROP TABLE IF EXISTS grading_records;
CREATE TABLE IF NOT EXISTS grading_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,  -- 关联学生
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    barcode VARCHAR(50),  -- 识别到的条码
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 评分结果
    overall_score DECIMAL(5,2),
    grade VARCHAR(20),
    char_count INT DEFAULT 0,
    
    -- AI 评语
    ai_comment TEXT,
    strengths TEXT,
    suggestions TEXT,
    
    -- 详细分数
    char_details JSON,
    
    -- 状态
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    
    -- 同步状态
    synced_to_evaluation BOOLEAN DEFAULT FALSE,
    semester_id INT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    INDEX idx_student (student_id),
    INDEX idx_barcode (barcode),
    INDEX idx_filename (filename),
    INDEX idx_upload_time (upload_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 11. 教师权限表
-- ============================================
CREATE TABLE IF NOT EXISTS teacher_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    class_id INT,  -- NULL表示所有班级
    indicator_id INT,  -- NULL表示所有指标
    can_view BOOLEAN DEFAULT TRUE,
    can_edit BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE,
    INDEX idx_teacher (teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 12. 学期评语
-- ============================================
CREATE TABLE IF NOT EXISTS semester_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester_id INT NOT NULL,
    ai_comment TEXT,  -- AI生成的评语
    teacher_comment TEXT,  -- 教师修改后的评语
    is_published BOOLEAN DEFAULT FALSE,  -- 是否发布给学生查看
    generated_at DATETIME,
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    UNIQUE KEY uk_student_semester (student_id, semester_id),
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 13. 操作日志
-- ============================================
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id INT,
    details JSON,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 14. 系统配置
-- ============================================
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认配置
INSERT INTO system_configs (config_key, config_value, description) VALUES 
('school_name', '塘厦实验小学', '学校名称'),
('scan_folder', 'E:/scanner_output', '扫描仪输出文件夹'),
('ai_api_key', 'sk-64b7fb2c08b44369981491e4c65b03f6', '千问API密钥'),
('calligraphy_indicator_id', '16', '书法成绩对应的指标ID');
