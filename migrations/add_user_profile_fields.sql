-- 数据库迁移脚本：添加用户个人资料字段
-- 日期：2026-01-21
-- 功能：为 users 表添加 avatar 和 signature 字段，用于存储用户头像和个性签名

-- 添加 avatar 头像字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR(500) DEFAULT NULL COMMENT '用户头像URL';

-- 添加 signature 个性签名字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS signature VARCHAR(200) DEFAULT NULL COMMENT '个性签名';
