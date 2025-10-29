"""数据库操作封装模块"""

import os
import traceback
import mysql.connector
from mysql.connector import Error
from colorama import Fore, init

from .config import CONFIG

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库文件路径
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'chat_history.db')


def get_connection():
    """获取数据库连接
    
    Returns:
        mysql.connector.connection.MySQLConnection: 数据库连接对象
    """
    try:
        connection = mysql.connector.connect(
            host=CONFIG['database']['host'],
            user=CONFIG['database']['user'],
            password=CONFIG['database']['password'],
            database=CONFIG['database']['database'],
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(Fore.RED + f"数据库连接错误: {e}")
        return None


class DatabaseManager:
    """数据库管理器类，用于处理与MySQL数据库的连接和操作"""

    def __init__(self):
        """初始化数据库连接"""
        # 初始化 colorama
        init(autoreset=True)

        try:
            self.connection = mysql.connector.connect(
                host=CONFIG['database']['host'],
                user=CONFIG['database']['user'],
                password=CONFIG['database']['password'],
                database=CONFIG['database']['database'],
                charset='utf8mb4'
            )
            print(Fore.GREEN + "数据库连接成功")
        except Error as e:
            print(Fore.RED + f"数据库连接错误: {e}")
            raise


    def get_character_info(self):
        """获取角色信息
        
        Returns:
            dict: 包含角色信息的字典
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'character_info'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM character_info LIMIT 1")
                result = cursor.fetchone()
                # 如果数据库中没有角色信息，则使用配置文件中的默认值
                return result if result else CONFIG['character']
            else:
                # 表不存在时使用配置文件中的默认值
                return CONFIG['character']
        except Error as e:
            print(Fore.RED + f"获取角色信息错误: {e}")
            # 出现异常时使用配置文件中的默认值
            return CONFIG['character']

    def save_chat(self, user_input, ai_response, image_description=None):
        """保存对话记录，包括图片描述

        Args:
            user_input (str): 用户输入
            ai_response (str): AI回复
            image_description (str, optional): 图片描述
        """
        try:
            print(f"开始保存聊天记录: {user_input[:20]}... -> {ai_response[:20]}...")
            cursor = self.connection.cursor()
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if cursor.fetchone():
                query = """
                INSERT INTO chat_history 
                (user_input, ai_response, image_description) 
                VALUES (%s, %s, %s)
                """
                cursor.execute(query, (user_input, ai_response, image_description))
                self.connection.commit()
                print(f"聊天记录已成功保存！ID: {cursor.lastrowid}")
        except Error as e:
            print(f"保存对话记录错误 [详细]: {e}")
            # 打印堆栈跟踪以获取更多信息
            traceback.print_exc()

    def close(self):
        """关闭数据库连接"""
        if self.connection.is_connected():
            self.connection.close()
            print(Fore.YELLOW + "数据库连接已关闭")