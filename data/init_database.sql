-- MySQL数据库初始化脚本
-- 用于创建基本的角色设定表和聊天记录表

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS catgirl_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE catgirl_db;

-- 创建角色信息表
CREATE TABLE IF NOT EXISTS character_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL DEFAULT '小雫',
    personality VARCHAR(500) DEFAULT NULL,
    brother_qqid VARCHAR(20) DEFAULT 'NekoSunami',
    height VARCHAR(10) DEFAULT '160cm',
    weight VARCHAR(10) DEFAULT '45kg',
    catchphrases VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_name (name)
);

-- 插入默认角色信息
INSERT INTO character_info (name, personality, brother_qqid, height, weight, catchphrases)
SELECT * FROM (SELECT '小雫', '傲娇兄控猫娘，说话风格参考碧蓝航线的雪风', 'NekoSunami', '160cm', '45kg', '喵~') AS tmp
WHERE NOT EXISTS (
    SELECT name FROM character_info WHERE name = '小雫'
) LIMIT 1;

-- 创建聊天记录表
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_input TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    image_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_id (id)
);

-- 创建索引以提高查询性能
-- 简单地尝试创建索引，如果存在则忽略错误
-- 注意：MySQL不支持CREATE INDEX IF NOT EXISTS语法
CREATE INDEX idx_chat_history_created_at ON chat_history (created_at);
CREATE INDEX idx_chat_history_user_input ON chat_history (user_input(255));