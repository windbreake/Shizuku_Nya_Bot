# -*- coding: utf-8 -*-
# web_server.py
import time
import socket                                    # 新增：用于创建自定义监听 socket
from colorama import init, Fore
from .ai_chat_system import AIChatSystem  # 修改导入路径
from .config import CONFIG  # 修改为直接导入
from flask import Flask, request, jsonify, send_file, send_from_directory, Response, render_template
import subprocess, threading, io
import logging, os
from logging.handlers import RotatingFileHandler
import sys
import shlex
import webbrowser
from werkzeug.serving import make_server   # 新增：使用 make_server 启动服务

init(autoreset=True)


# 终端聊天模式
def run_terminal_chat():
    """终端聊天模式"""
    chat_system = AIChatSystem()
    print(Fore.CYAN + "\n🐱 终端聊天模式已启动 (输入'exit'退出)")
    print(Fore.YELLOW + "小雫: 喵~哥哥今天想聊什么呀？")

    while True:
        user_input = input(Fore.GREEN + "你: ").strip()
        if user_input.lower() == 'exit':
            break

        start_time = time.time()
        print(Fore.YELLOW + "小雫: 思考中...", end='\r')

        # 获取回复
        response = chat_system.chat(user_input)

        # 显示回复并计算响应时间
        elapsed = time.time() - start_time
        print(Fore.YELLOW + f"小雫: {response} (响应时间: {elapsed:.2f}s)")


# 沙箱聊天模式
def run_web_server():
    """沙箱聊天模式 (Flask服务 + 控制面板)"""
    port = 8888
    # 使用绝对路径指向 src/static 目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'static')
    app = Flask(
        __name__,
        static_folder=static_dir,
        static_url_path='/static',
        template_folder=base_dir  # 将模板文件夹指向 src 目录
    )
    
    # 移除下方重复定义，后续已用 app.send_static_file 统一映射
    # {
    # @app.route('/control_panel')
    # def control_panel():
    #     return send_from_directory(static_dir, 'control_panel.html')
    #
    # @app.route('/db_management')
    # def db_management():
    #     return send_from_directory(static_dir, 'db_management.html')
    #
    # @app.route('/logs')
    # def logs():
    #     return send_from_directory(static_dir, 'logs.html')
    # }
    
    chat_system = AIChatSystem()

    # 配置日志写入 app.log
    log_handler = RotatingFileHandler(CONFIG['server']['log_file'], maxBytes=1e6, backupCount=2, encoding='utf-8')
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(log_handler)

    @app.route('/')
    @app.route('/control_panel')
    def control_panel():
        return app.send_static_file('control_panel.html')

    @app.route('/sandbox')
    def sandbox_route():
        return render_template('chat-sandbox.html')

    @app.route('/chat', methods=['POST'])
    def chat_endpoint():
        try:
            data = request.get_json()
            if not data or (not data.get('message') and not data.get('image')):
                return jsonify({'success': False, 'error': '无效请求'}), 400

            response = chat_system.chat(data.get('message'), data.get('image'))
            return jsonify({'success': True, 'reply': response})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/koishi_console')
    def koishi_console():
        return app.send_static_file('koishi_console.html')

    @app.route('/terminal_page')
    def terminal_page():
        return app.send_static_file('terminal_chat.html')

    @app.route('/diagnosis_page')
    def diagnosis_page():
        return app.send_static_file('diagnosis.html')

    @app.route('/db_console')
    def db_console():
        return app.send_static_file('db_management.html')

    @app.route('/logs_page')
    def logs_page():
        return app.send_static_file('logs.html')

    @app.route('/koishi_logs')
    def koishi_logs():
        return app.send_static_file('koishi_logs.html')

    # 后端获取记录
    @app.route('/api/records')
    def api_records():
        from src.reset_database import get_connection
        conn = get_connection()
        rows = []
        if conn:
            cur = conn.cursor();
            cur.execute("SELECT * FROM chat_history ORDER BY id ASC LIMIT %s OFFSET %s",
                        (int(request.args.get('limit', 200)), int(request.args.get('offset', 0))))
            rows = cur.fetchall();
            conn.close()
        return jsonify(rows)

    @app.route('/api/delete_record', methods=['POST'])
    def api_del_record():
        data = request.get_json();
        rid = data.get('id')
        from src.reset_database import get_connection
        conn = get_connection()
        if conn:
            cur = conn.cursor();
            cur.execute("DELETE FROM chat_history WHERE id=%s", (rid,));
            conn.commit();
            conn.close()
        return jsonify({'message': 'ok'})

    @app.route('/api/clear_records', methods=['POST'])
    def api_clear():
        from src.reset_database import get_connection
        conn = get_connection()
        if conn:
            cur = conn.cursor();
            cur.execute("DELETE FROM chat_history");
            conn.commit();
            conn.close()
        return jsonify({'message': 'cleared'})

    @app.route('/api/delete_first_n', methods=['POST'])
    def api_del_n():
        data = request.get_json();
        n = data.get('n', 0)
        from src.reset_database import get_connection
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM chat_history ORDER BY id ASC LIMIT %s", (n,))
            ids = [r[0] for r in cur.fetchall()]
            if ids:
                cur.execute(f"DELETE FROM chat_history WHERE id IN ({','.join(str(i) for i in ids)})")
                conn.commit()
            conn.close()
        return jsonify({'message': 'deleted_first_n'})

    # 启动模式
    @app.route('/api/run_mode', methods=['POST'])
    def api_run_mode():
        m = request.get_json().get('mode', 0)
        # 异步调用 main.py
        threading.Thread(target=lambda: subprocess.Popen(['python', 'main.py', str(m)])).start()
        return jsonify({'message': f'mode {m} launched'})

    # 服务诊断
    @app.route('/api/diagnosis')
    def api_diag():
        try:
            # 获取项目根目录
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            main_py_path = os.path.join(base_path, 'main.py')

            # 使用 subprocess 调用 main.py 的诊断功能
            # cwd=base_path 确保 main.py 在正确的上下文中执行
            result = subprocess.check_output(
                [sys.executable, main_py_path, '3'],
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=base_path
            )
            return f"<pre>{result}</pre>"
        except subprocess.CalledProcessError as e:
            return f"<pre>诊断执行出错:\n{e.output}</pre>", 500
        except Exception as e:
            return f"<pre>未知错误: {str(e)}</pre>", 500

    # 日志尾部（演示用）
    @app.route('/api/logs')
    def api_logs():
        try:
            with open('app.log', 'r', encoding='utf-8') as f:
                return f.read()[-2000:]
        except:
            return ''

    # Koishi 日志API
    @app.route('/api/koishi_logs')
    def api_koishi_logs():
        try:
            with open('koishi.log', 'r', encoding='utf-8') as f:
                return f.read()[-2000:]
        except:
            return ''

    @app.route('/stream_logs')
    def stream_logs():
        def event_stream():
            with open('app.log', 'r', encoding='utf-8') as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        yield f"data:{line}\n\n"
                    else:
                        time.sleep(0.5)

        return Response(event_stream(), mimetype='text/event-stream')

    @app.route('/api/exec_cmd')
    def api_exec_cmd():
        cmd = request.args.get('cmd')
        if not cmd:
            return 'Missing cmd parameter', 400
        # 安全提示：生产环境要严格校验或白名单
        try:
            # shell=True 可执行字符串命令，注意安全
            output = subprocess.check_output(cmd, shell=True, cwd=base_dir,
                                             stderr=subprocess.STDOUT,
                                             encoding='utf-8')
        except subprocess.CalledProcessError as e:
            output = e.output
        # 返回 HTML 格式保留换行
        return f'<pre>{output}</pre>'

    # 批处理接口：传入 "0"~"5" 对应 start.bat 菜单项
    @app.route('/api/batch/<choice>', methods=['POST'])
    def api_batch_choice(choice):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        main_py = os.path.join(base, 'main.py')
        # 在新终端窗口执行：start "标题" cmd /k "python main.py <choice>"
        cmd = f'start \"Mode{choice}\" cmd /k \"{sys.executable}\" \"{main_py}\" {choice}'
        subprocess.Popen(cmd, shell=True, cwd=base)
        return '', 204

    # 挂载静态
    # app.static_folder 已指向 src/static

    # 定义一个函数来打开浏览器
    def open_browser():
        webbrowser.open_new_tab(f'http://localhost:{port}/sandbox')

    # 为防止调试模式下的重载器多次打开浏览器，我们只在主进程中执行此操作
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # 在服务器启动后延迟1秒打开浏览器
        threading.Timer(1, open_browser).start()

    # 启动服务
    # 使用 werkzeug.make_server 启动 Flask 服务，彻底绕过 WERKZEUG_SERVER_FD 读取
    http_server = make_server('0.0.0.0', port, app)
    print(Fore.CYAN + f"\n🌐 沙箱聊天模式已启动: http://localhost:{port}")
    http_server.serve_forever()
