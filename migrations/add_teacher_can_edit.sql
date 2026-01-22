-- 数据库迁移脚本：添加教师编辑权限字段
-- 日期：2026-01-21
-- 功能：为 teachers 表添加 can_edit 字段，用于控制教师是否有权限进行数据录入和评语管理

-- 添加 can_edit 字段到 teachers 表
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS can_edit BOOLEAN DEFAULT FALSE COMMENT '是否有数据编辑权限';

-- 为已授权登录的教师默认开启编辑权限
UPDATE teachers t
JOIN users u ON t.user_id = u.id
SET t.can_edit = TRUE
WHERE u.is_active = TRUE;

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_teachers_can_edit ON teachers(can_edit);
