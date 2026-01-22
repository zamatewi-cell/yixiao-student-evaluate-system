-- ============================================
-- 学生综合素质评价系统 - 功能扩展数据库迁移
-- 日期：2026-01-22
-- 版本：2.0
-- ============================================

-- 1. 考试表
CREATE TABLE IF NOT EXISTS exams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '考试名称',
    exam_type ENUM('unit', 'midterm', 'final', 'other') DEFAULT 'unit' COMMENT '考试类型：单元测试/期中/期末/其他',
    semester_id INT NOT NULL COMMENT '学期ID',
    grade_id INT COMMENT '年级ID（可选，不填则全校）',
    exam_date DATE COMMENT '考试日期',
    status ENUM('draft', 'active', 'completed') DEFAULT 'draft' COMMENT '状态：草稿/进行中/已完成',
    created_by INT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试表';

-- 2. 考试科目表
CREATE TABLE IF NOT EXISTS exam_subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_name VARCHAR(50) NOT NULL COMMENT '科目名称',
    full_score DECIMAL(5,1) DEFAULT 100 COMMENT '满分',
    pass_score DECIMAL(5,1) DEFAULT 60 COMMENT '及格分',
    excellent_score DECIMAL(5,1) DEFAULT 85 COMMENT '优秀分',
    sort_order INT DEFAULT 0 COMMENT '排序',
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试科目表';

-- 3. 学生成绩表
CREATE TABLE IF NOT EXISTS exam_scores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_id INT NOT NULL COMMENT '科目ID',
    student_id INT NOT NULL COMMENT '学生ID',
    score DECIMAL(5,1) COMMENT '分数',
    class_rank INT COMMENT '班级排名',
    grade_rank INT COMMENT '年级排名',
    recorded_by INT COMMENT '录入人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_exam_subject_student (exam_id, subject_id, student_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES exam_subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生成绩表';

-- 4. 学生总分表
CREATE TABLE IF NOT EXISTS exam_totals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    student_id INT NOT NULL COMMENT '学生ID',
    total_score DECIMAL(6,1) COMMENT '总分',
    class_rank INT COMMENT '班级排名',
    grade_rank INT COMMENT '年级排名',
    subject_count INT DEFAULT 0 COMMENT '科目数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_exam_student (exam_id, student_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生总分及排名表';

-- 5. 试卷分析表
CREATE TABLE IF NOT EXISTS exam_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_id INT NOT NULL COMMENT '科目ID',
    class_id INT COMMENT '班级ID（可选，不填则为全年级）',
    teacher_id INT COMMENT '教师ID',
    analysis_content TEXT COMMENT '分析内容',
    avg_score DECIMAL(5,1) COMMENT '平均分',
    max_score DECIMAL(5,1) COMMENT '最高分',
    min_score DECIMAL(5,1) COMMENT '最低分',
    pass_count INT DEFAULT 0 COMMENT '及格人数',
    excellent_count INT DEFAULT 0 COMMENT '优秀人数',
    total_count INT DEFAULT 0 COMMENT '参考人数',
    pass_rate DECIMAL(5,2) COMMENT '及格率',
    excellent_rate DECIMAL(5,2) COMMENT '优秀率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES exam_subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='试卷分析表';

-- 6. 考勤表
CREATE TABLE IF NOT EXISTS attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    date DATE NOT NULL COMMENT '日期',
    status ENUM('present', 'absent', 'late', 'leave_early', 'sick_leave', 'personal_leave') NOT NULL DEFAULT 'present' COMMENT '状态：出勤/缺勤/迟到/早退/病假/事假',
    leave_type ENUM('sick', 'personal', 'other') COMMENT '请假类型：病假/事假/其他',
    reason VARCHAR(500) COMMENT '原因说明',
    recorded_by INT COMMENT '记录人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_student_date (student_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_date (date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考勤表';

-- 7. 教师任课表
CREATE TABLE IF NOT EXISTS teacher_subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL COMMENT '教师ID',
    class_id INT NOT NULL COMMENT '班级ID',
    subject_name VARCHAR(50) NOT NULL COMMENT '任教科目',
    semester_id INT NOT NULL COMMENT '学期ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_teacher_class_subject (teacher_id, class_id, subject_name, semester_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师任课表';

-- 8. 学生变更记录表（转班、升级、毕业等）
CREATE TABLE IF NOT EXISTS student_transfers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    transfer_type ENUM('class_transfer', 'grade_upgrade', 'graduation', 'enrollment', 'dropout') NOT NULL COMMENT '变更类型：转班/升级/毕业/入学/退学',
    from_class_id INT COMMENT '原班级ID',
    to_class_id INT COMMENT '目标班级ID',
    from_grade_id INT COMMENT '原年级ID',
    to_grade_id INT COMMENT '目标年级ID',
    transfer_date DATE NOT NULL COMMENT '变更日期',
    reason VARCHAR(500) COMMENT '变更原因',
    operated_by INT COMMENT '操作人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student_date (student_id, transfer_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生变更记录表';

-- 9. 系统备份记录表
CREATE TABLE IF NOT EXISTS system_backups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    backup_name VARCHAR(200) NOT NULL COMMENT '备份名称',
    backup_path VARCHAR(500) NOT NULL COMMENT '备份文件路径',
    backup_size BIGINT COMMENT '备份大小(字节)',
    backup_type ENUM('manual', 'auto') DEFAULT 'manual' COMMENT '备份类型：手动/自动',
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending' COMMENT '状态',
    created_by INT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL COMMENT '完成时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统备份记录表';

-- 10. 安全添加学生表新字段的存储过程
DELIMITER //
DROP PROCEDURE IF EXISTS add_student_columns//
CREATE PROCEDURE add_student_columns()
BEGIN
    -- 添加 enrollment_status 字段
    IF NOT EXISTS (SELECT * FROM information_schema.columns 
                   WHERE table_schema = DATABASE() 
                   AND table_name = 'students' 
                   AND column_name = 'enrollment_status') THEN
        ALTER TABLE students ADD COLUMN enrollment_status ENUM('enrolled', 'graduated', 'transferred', 'dropped') DEFAULT 'enrolled' COMMENT '学籍状态：在读/已毕业/已转学/已退学';
    END IF;
    
    -- 添加 enrollment_year 字段
    IF NOT EXISTS (SELECT * FROM information_schema.columns 
                   WHERE table_schema = DATABASE() 
                   AND table_name = 'students' 
                   AND column_name = 'enrollment_year') THEN
        ALTER TABLE students ADD COLUMN enrollment_year INT COMMENT '入学年份';
    END IF;
    
    -- 添加 graduation_year 字段
    IF NOT EXISTS (SELECT * FROM information_schema.columns 
                   WHERE table_schema = DATABASE() 
                   AND table_name = 'students' 
                   AND column_name = 'graduation_year') THEN
        ALTER TABLE students ADD COLUMN graduation_year INT COMMENT '毕业年份';
    END IF;
END//

DROP PROCEDURE IF EXISTS add_teacher_columns//
CREATE PROCEDURE add_teacher_columns()
BEGIN
    -- 添加 is_head_teacher 字段
    IF NOT EXISTS (SELECT * FROM information_schema.columns 
                   WHERE table_schema = DATABASE() 
                   AND table_name = 'teachers' 
                   AND column_name = 'is_head_teacher') THEN
        ALTER TABLE teachers ADD COLUMN is_head_teacher BOOLEAN DEFAULT FALSE COMMENT '是否为班主任';
    END IF;
    
    -- 添加 teacher_type 字段
    IF NOT EXISTS (SELECT * FROM information_schema.columns 
                   WHERE table_schema = DATABASE() 
                   AND table_name = 'teachers' 
                   AND column_name = 'teacher_type') THEN
        ALTER TABLE teachers ADD COLUMN teacher_type ENUM('head_teacher', 'subject_teacher', 'both') DEFAULT 'subject_teacher' COMMENT '教师类型：班主任/科任教师/两者都是';
    END IF;
END//
DELIMITER ;

-- 执行存储过程
CALL add_student_columns();
CALL add_teacher_columns();

-- 清理存储过程
DROP PROCEDURE IF EXISTS add_student_columns;
DROP PROCEDURE IF EXISTS add_teacher_columns;

-- 完成提示
SELECT '数据库迁移完成!' AS message;
