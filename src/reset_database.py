# reset_database.py
import sys
import os

# 将项目根目录添加到 sys.path，以确保 'src' 模块可以被找到
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mysql.connector
from mysql.connector import Error
from src.config import CONFIG
import logging
import sys
import subprocess, os

# 配置日志输出
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_connection():
    """获取数据库连接"""
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
        logging.error(f"数据库连接失败: {e}")
        return None


def reset_chat_history(connection):
    """清空 chat_history 表"""
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM chat_history")
        connection.commit()
        logging.info("chat_history 表已清空。")
    except Error as e:
        logging.error(f"清空 chat_history 表失败: {e}")


def list_records(connection, limit, offset):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM chat_history ORDER BY id ASC LIMIT %s OFFSET %s", (limit, offset))
    return cursor.fetchall()


def delete_record(connection, record_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM chat_history WHERE id=%s", (record_id,))
    rec = cursor.fetchone()
    if not rec:
        print("记录不存在。")
        return
    print("将删除记录：", rec)
    confirm = input("确认删除？(y/n): ").strip().lower()
    if confirm == 'y':
        cursor.execute("DELETE FROM chat_history WHERE id=%s", (record_id,))
        connection.commit()
        print("已删除。")
    else:
        print("已取消。")


def paginate_and_manage_records(connection, page_size=200):
    page = 0
    while True:
        os.system('cls')  # 清屏
        records = list_records(connection, page_size, page * page_size)
        if not records:
            print("无更多记录。")
            break
        for idx, row in enumerate(records, start=1 + page * page_size):
            print(f"{idx}. {row}")
        cmd = input("[N] 下一页  [P] 上一页  [R] 刷新  [Q] 返回菜单: ").strip().lower()
        if cmd == 'n':
            page += 1
        elif cmd == 'p' and page > 0:
            page -= 1
        elif cmd == 'r':
            continue
        elif cmd == 'q':
            break
        else:
            print("无效输入。")


def delete_first_n_records(connection):
    n = input("请输入要删除的前 N 条记录的数量: ").strip()
    if not n.isdigit():
        print("请输入有效数字。")
        return
    n = int(n)
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM chat_history ORDER BY id ASC LIMIT %s", (n,))
    ids = [r[0] for r in cursor.fetchall()]
    if not ids:
        print("无可删除的记录。")
        return
    print("将删除以下 ID:", ids)
    confirm = input("确认删除？(y/n): ").strip().lower()
    if confirm == 'y':
        id_list = ",".join(str(i) for i in ids)
        cursor.execute(f"DELETE FROM chat_history WHERE id IN ({id_list})")
        connection.commit()
        print(f"已删除 {cursor.rowcount} 条记录。")
    else:
        print("已取消。")


def main():
    conn = get_connection()
    if not conn:
        print("无法连接数据库。")
        return
    try:
        while True:
            os.system('cls')  # 每次刷新前清屏
            print("\n1. 清空所有聊天记录\n2. 展示聊天记录\n3. 删除指定记录\n4. 删除前 N 条记录\n5. 退出")
            choice = input("请输入选项 [1-5]: ").strip()
            if choice == '1':
                confirm = input("警告：此操作将清空所有聊天记录，是否继续？(y/n): ").strip().lower()
                if confirm == 'y':
                    reset_chat_history(conn)
                else:
                    print("已取消清空操作。")
            elif choice == '2':
                # 在新窗口仅展示记录
                script = os.path.abspath(__file__)
                subprocess.Popen(f'start cmd /c python "{script}" --show', shell=True)
            elif choice == '3':
                rid = input("请输入要删除的记录 ID: ").strip()
                if rid.isdigit():
                    delete_record(conn, int(rid))
                else:
                    print("无效 ID。")
            elif choice == '4':
                delete_first_n_records(conn)
            elif choice == '5':
                break
            else:
                print("无效选项。")
    finally:
        conn.close()


if __name__ == "__main__":
    if "--show" in sys.argv:
        conn = get_connection()
        if conn:
            try:
                paginate_and_manage_records(conn)
            finally:
                conn.close()
        sys.exit()
    main()
