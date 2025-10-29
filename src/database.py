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
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return connection
    except Error as e:
        print(Fore.RED + f"数据库连接错误: {e}")
        return None


def table_exists(cursor, table_name):
    """检查表是否存在
    
    Args:
        cursor: 数据库游标
        table_name (str): 表名
        
    Returns:
        bool: 表存在返回True，否则返回False
    """
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


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
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
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
            if table_exists(cursor, 'character_info'):
                # 获取第一条记录，而不是特定名称的记录
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
        finally:
            if 'cursor' in locals():
                cursor.close()

    def save_chat(self, user_input, ai_response, image_description=None):
        """保存对话记录，包括图片描述

        Args:
            user_input (str): 用户输入
            ai_response (str): AI回复
            image_description (str, optional): 图片描述
        """
        cursor = None
        try:
            print(f"开始保存聊天记录: {user_input[:20]}... -> {ai_response[:20]}...")
            cursor = self.connection.cursor()
            if table_exists(cursor, 'chat_history'):
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
        finally:
            if cursor:
                cursor.close()

    def get_chat_history(self, limit=50):
        """获取聊天历史记录
        
        Args:
            limit (int): 限制返回的记录数
            
        Returns:
            list: 聊天记录列表
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            if table_exists(cursor, 'chat_history'):
                # 改为降序，优先显示最新记录
                cursor.execute("SELECT * FROM chat_history ORDER BY id DESC LIMIT %s", (limit,))
                return cursor.fetchall()
            return []
        except Error as e:
            print(f"获取聊天记录错误: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def delete_chat_record(self, record_id):
        """删除指定聊天记录
        
        Args:
            record_id (int): 要删除的记录ID
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            if table_exists(cursor, 'chat_history'):
                cursor.execute("DELETE FROM chat_history WHERE id = %s", (record_id,))
                self.connection.commit()
        except Error as e:
            print(f"删除聊天记录错误: {e}")
        finally:
            if cursor:
                cursor.close()

    def clear_chat_history(self):
        """清空所有聊天记录"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            if table_exists(cursor, 'chat_history'):
                cursor.execute("DELETE FROM chat_history")
                self.connection.commit()
        except Error as e:
            print(f"清空聊天记录错误: {e}")
        finally:
            if cursor:
                cursor.close()

    def delete_first_n_records(self, n):
        """删除前N条记录
        
        Args:
            n (int): 要删除的记录数
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            if table_exists(cursor, 'chat_history'):
                cursor.execute("SELECT id FROM chat_history ORDER BY id ASC LIMIT %s", (n,))
                ids = [r[0] for r in cursor.fetchall()]
                if ids:
                    # 使用参数化查询避免SQL注入
                    format_strings = ','.join(['%s'] * len(ids))
                    query = f"DELETE FROM chat_history WHERE id IN ({format_strings})"
                    cursor.execute(query, tuple(ids))
                    self.connection.commit()
        except Error as e:
            print(f"删除前N条记录错误: {e}")
        finally:
            if cursor:
                cursor.close()

    def close(self):
        """关闭数据库连接"""
        if self.connection.is_connected():
            self.connection.close()
            print(Fore.YELLOW + "数据库连接已关闭")
