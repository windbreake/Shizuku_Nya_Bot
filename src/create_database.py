#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一键创建数据库和表的脚本
该脚本会创建 catgirl_db 数据库以及 character_info 和 chat_history 表
"""

import sys
import os
import mysql.connector
from mysql.connector import Error

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import CONFIG

def create_database():
    """创建数据库"""
    connection = None
    try:
        # 先连接到 MySQL 服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=CONFIG['database']['host'],
            user=CONFIG['database']['user'],
            password=CONFIG['database']['password']
        )
        
        cursor = connection.cursor()
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS catgirl_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("数据库 catgirl_db 创建成功或已存在")
        
    except Error as e:
        print(f"创建数据库时出错: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def create_tables():
    """创建表"""
    connection = None
    try:
        # 连接到指定数据库
        connection = mysql.connector.connect(
            host=CONFIG['database']['host'],
            user=CONFIG['database']['user'],
            password=CONFIG['database']['password'],
            database=CONFIG['database']['database']
        )
        
        cursor = connection.cursor()
        
        # 创建 character_info 表
        create_character_table_query = """
        CREATE TABLE IF NOT EXISTS character_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL DEFAULT '小雫',
            personality VARCHAR(500),
            brother_qqid VARCHAR(20) DEFAULT 'NekoSunami',
            height VARCHAR(10) DEFAULT '160cm',
            weight VARCHAR(10) DEFAULT '45kg',
            catchphrases VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_character_table_query)
        print("表 character_info 创建成功或已存在")
        
        # 创建 chat_history 表
        create_chat_table_query = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_input TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            image_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_chat_table_query)
        print("表 chat_history 创建成功或已存在")
        
        connection.commit()
        
    except Error as e:
        print(f"创建表时出错: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
    return True

def insert_default_character():
    """插入默认角色信息"""
    connection = None
    try:
        # 连接到指定数据库
        connection = mysql.connector.connect(
            host=CONFIG['database']['host'],
            user=CONFIG['database']['user'],
            password=CONFIG['database']['password'],
            database=CONFIG['database']['database']
        )
        
        cursor = connection.cursor()
        
        # 检查是否已存在角色信息
        cursor.execute("SELECT COUNT(*) FROM character_info")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # 插入默认角色信息
            insert_query = """
            INSERT INTO character_info (name, personality, brother_qqid, catchphrases)
            VALUES (%s, %s, %s, %s)
            """
            character_data = (
                '小雫',
                '傲娇兄控猫娘，说话风格参考碧蓝航线的雪风',
                'NekoSunami',
                '喵,哒,Nanaoda'
            )
            cursor.execute(insert_query, character_data)
            connection.commit()
            print("默认角色信息已插入")
        else:
            print("角色信息已存在，跳过插入默认数据")
        
    except Error as e:
        print(f"插入默认角色信息时出错: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
    return True

def main():
    print("开始创建数据库和表...")
    
    # 创建数据库
    if not create_database():
        print("创建数据库失败")
        return
    
    # 创建表
    if not create_tables():
        print("创建表失败")
        return
    
    # 插入默认角色信息
    if not insert_default_character():
        print("插入默认角色信息失败")
        return
    
    print("数据库和表创建完成!")

if __name__ == "__main__":
    main()