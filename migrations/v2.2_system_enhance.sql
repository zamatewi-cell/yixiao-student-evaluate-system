-- ============================================
-- 学生综合素质评价系统 - V2.2系统增强迁移
-- 日期：2026-01-22
-- 版本：2.2
-- 功能：系统配置、审计日志、通知公告
-- ============================================

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '描述',
    category VARCHAR(50) DEFAULT 'other' COMMENT '分类：basic/exam/attendance/ai/system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT COMMENT '操作用户ID',
    action_type VARCHAR(50) NOT NULL COMMENT '操作类型：login/logout/create/update/delete/export/import/backup/config',
    module VARCHAR(50) COMMENT '模块：auth/student/teacher/class/exam/score/attendance/comment/system',
    description VARCHAR(500) COMMENT '操作描述',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    target_id INT COMMENT '目标记录ID',
    target_type VARCHAR(50) COMMENT '目标类型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_action (action_type),
    INDEX idx_module (module),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- 通知公告表
CREATE TABLE IF NOT EXISTS notices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT COMMENT '内容',
    notice_type ENUM('general', 'exam', 'attendance', 'activity', 'urgent') DEFAULT 'general' COMMENT '通知类型',
    target_type ENUM('all', 'teacher', 'student', 'class', 'grade') DEFAULT 'all' COMMENT '目标类型',
    target_ids VARCHAR(500) COMMENT '目标ID列表（逗号分隔）',
    is_pinned BOOLEAN DEFAULT FALSE COMMENT '是否置顶',
    view_count INT DEFAULT 0 COMMENT '阅读次数',
    valid_until DATE COMMENT '有效期至',
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft' COMMENT '状态',
    created_by INT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (notice_type),
    INDEX idx_status (status),
    INDEX idx_pinned (is_pinned),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知公告表';

-- 用户通知阅读记录表
CREATE TABLE IF NOT EXISTS notice_reads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    notice_id INT NOT NULL COMMENT '通知ID',
    user_id INT NOT NULL COMMENT '用户ID',
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_notice_user (notice_id, user_id),
    FOREIGN KEY (notice_id) REFERENCES notices(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知阅读记录表';

-- 教师任课表（增加is_active字段如果不存在）
-- 使用存储过程安全添加列
DELIMITER //
CREATE PROCEDURE add_teacher_subjects_column_if_not_exists()
BEGIN
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'teacher_subjects' 
        AND COLUMN_NAME = 'is_active'
    ) THEN
        ALTER TABLE teacher_subjects ADD COLUMN is_active BOOLEAN DEFAULT TRUE COMMENT '是否生效';
    END IF;
END //
DELIMITER ;

CALL add_teacher_subjects_column_if_not_exists();
DROP PROCEDURE IF EXISTS add_teacher_subjects_column_if_not_exists;

-- 初始化默认系统配置
INSERT IGNORE INTO system_configs (config_key, config_value, description, category) VALUES
    ('school_name', '小学', '学校名称', 'basic'),
    ('school_address', '', '学校地址', 'basic'),
    ('school_phone', '', '学校电话', 'basic'),
    ('score_pass_line', '60', '默认及格分数线', 'exam'),
    ('score_excellent_line', '85', '默认优秀分数线', 'exam'),
    ('max_score', '100', '默认满分', 'exam'),
    ('attendance_late_minutes', '10', '迟到判定时间(分钟)', 'attendance'),
    ('backup_auto_enabled', 'false', '是否启用自动备份', 'system'),
    ('backup_keep_days', '30', '备份保留天数', 'system'),
    ('session_timeout_hours', '24', '会话超时时间(小时)', 'system');

-- 完成提示
SELECT 'V2.2系统增强迁移完成!' AS message;
