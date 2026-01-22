-- ============================================
-- 学生综合素质评价系统 - 错题分析功能迁移
-- 日期：2026-01-22
-- 版本：2.1
-- ============================================

-- 错题记录表
CREATE TABLE IF NOT EXISTS wrong_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    exam_id INT COMMENT '考试ID',
    subject_id INT COMMENT '科目ID',
    question_number INT COMMENT '题号',
    question_content TEXT COMMENT '题目内容',
    correct_answer TEXT COMMENT '正确答案',
    student_answer TEXT COMMENT '学生答案',
    knowledge_point VARCHAR(100) COMMENT '知识点',
    error_type ENUM('calculation', 'concept', 'careless', 'unknown', 'other') DEFAULT 'unknown' COMMENT '错误类型：计算错误/概念混淆/粗心/不会/其他',
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium' COMMENT '难度',
    is_mastered BOOLEAN DEFAULT FALSE COMMENT '是否已掌握',
    master_date DATE COMMENT '掌握日期',
    recorded_by INT COMMENT '记录人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES exam_subjects(id) ON DELETE SET NULL,
    INDEX idx_student (student_id),
    INDEX idx_exam (exam_id),
    INDEX idx_knowledge_point (knowledge_point),
    INDEX idx_error_type (error_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题记录表';

-- 知识点表（可选，用于标准化知识点管理）
CREATE TABLE IF NOT EXISTS knowledge_points (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(50) NOT NULL COMMENT '学科',
    grade_id INT COMMENT '年级',
    chapter VARCHAR(100) COMMENT '章节',
    point_name VARCHAR(200) NOT NULL COMMENT '知识点名称',
    description TEXT COMMENT '描述',
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium' COMMENT '难度',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_subject (subject),
    INDEX idx_grade (grade_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点表';

-- 学生知识点掌握情况表
CREATE TABLE IF NOT EXISTS student_knowledge_mastery (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    knowledge_point_id INT COMMENT '知识点ID',
    knowledge_point_name VARCHAR(200) COMMENT '知识点名称（冗余）',
    mastery_level ENUM('not_learned', 'learning', 'mastered', 'proficient') DEFAULT 'learning' COMMENT '掌握程度',
    wrong_count INT DEFAULT 0 COMMENT '错误次数',
    correct_count INT DEFAULT 0 COMMENT '正确次数',
    last_practice_date DATE COMMENT '最后练习日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_knowledge (student_id, knowledge_point_name),
    INDEX idx_student (student_id),
    INDEX idx_mastery (mastery_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生知识点掌握情况表';

-- 完成提示
SELECT '错题分析功能数据库迁移完成!' AS message;
