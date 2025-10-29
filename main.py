# main.py
import sys
import io
import os
from colorama import init, Fore
import socket
import requests

# 确保所有输出使用 UTF-8 编码
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置环境变量强制使用 UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

init(autoreset=True)


def check_ports():
    """检查常用端口状态"""
    ports_to_check = [
        (8888, "Web服务器"),
        (8081, "控制面板"),
        (8082, "数据库管理"),
        (8083, "日志服务"),
        (5000, "Koishi主端口"),
        (5001, "Koishi备用端口")
    ]

    print(Fore.CYAN + "端口检查:")
    for port, name in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                print(Fore.RED + f"  - {name} ({port}): {Fore.YELLOW}占用中")
            else:
                print(Fore.GREEN + f"  - {name} ({port}): {Fore.GREEN}空闲")


def test_local_api():
    """测试本地API服务"""
    print(Fore.CYAN + "\n本地API测试:")

    running_service_port = None
    for port in range(5000, 5011):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                running_service_port = port
                break

    if running_service_port:
        print(Fore.GREEN + f"  在端口 {running_service_port} 检测到运行中的服务")
        try:
            # 测试根路径
            root_response = requests.get(f"http://localhost:{running_service_port}", timeout=5)
            print(Fore.GREEN + f"  根路径状态: {root_response.status_code} - {root_response.json()}")

            # 测试/v1/models端点
            models_response = requests.get(f"http://localhost:{running_service_port}/v1/models", timeout=5)
            print(Fore.GREEN + f"  模型列表状态: {models_response.status_code} - {models_response.json()}")
        except Exception as e:
            print(Fore.RED + f"  本地API测试失败: {str(e)}")
    else:
        print(Fore.RED + "  未检测到运行中的服务 (5000-5010)")
        print(Fore.YELLOW + "  请先启动服务后再运行诊断")


def test_deepseek_api():
    """测试DeepSeek API连接"""
    print(Fore.CYAN + "\nDeepSeek API测试:")
    try:
        from src.config import CONFIG
        headers = {"Authorization": f"Bearer {CONFIG['api']['key']}"}
        response = requests.get(
            f"{CONFIG['api']['base_url']}/models",
            headers=headers,
            timeout=10
        )
        print(Fore.GREEN + f"  API状态: {response.status_code}")
        if response.status_code == 200:
            print(Fore.GREEN + f"  响应内容: {response.text[:200]}...")
        else:
            print(Fore.RED + f"  API返回错误: {response.text}")
    except Exception as e:
        print(Fore.RED + f"  API连接失败: {str(e)}")
        print(Fore.YELLOW + "  请检查网络连接、代理设置或API密钥")


def full_diagnosis():
    """执行完整诊断流程"""
    print(Fore.CYAN + "=" * 50)
    print(Fore.YELLOW + "🐱 服务诊断工具")
    print(Fore.CYAN + "=" * 50)
    check_ports()
    test_local_api()
    test_deepseek_api()
    print(Fore.CYAN + "\n诊断完成!")


def run_mode(mode):
    """根据模式编号运行相应的服务"""
    try:
        if mode == 0:
            from src.koishi_service import run_koishi_service
            run_koishi_service()
        elif mode == 1:
            from src.web_server import run_terminal_chat
            run_terminal_chat()
        elif mode == 2:
            # 沙箱模式 - 启动Web服务器并默认打开沙箱页面
            from src.web_server import run_web_server
            os.environ['DEFAULT_PAGE'] = '/sandbox'
            exit_code = run_web_server()
            sys.exit(exit_code)
        elif mode == 5:
            # 控制面板模式 - 启动Web服务器并默认打开控制面板
            from src.web_server import run_web_server
            os.environ['DEFAULT_PAGE'] = '/control_panel'
            exit_code = run_web_server()
            sys.exit(exit_code)
        else:
            print(Fore.RED + "无效的模式选择!")
    except Exception as e:
        # 添加更详细的错误信息
        import traceback
        error_trace = traceback.format_exc()
        print(Fore.RED + f"运行错误详情:\n{error_trace}")
        print(Fore.YELLOW + "请检查相关服务配置")
        sys.exit(1)


if __name__ == "__main__":
    # 打印当前编码信息用于调试
    print(f"标准输出编码: {sys.stdout.encoding}")
    print(f"标准错误编码: {sys.stderr.encoding}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    
    # 检查数据库连接
    try:
        from src.reset_database import get_connection
        conn = get_connection()
        if conn:
            print("数据库连接成功")
            conn.close()
        else:
            print("数据库连接失败")
    except Exception as e:
        print(f"数据库连接检查出错: {e}")

    if len(sys.argv) == 1:
        print(Fore.CYAN + "=" * 50)
        print(Fore.YELLOW + "🐱 ShizukuNyaBot - 运行模式选择")
        print(Fore.CYAN + "=" * 50)
        print(Fore.GREEN + "0: 映射至Koishi\\AstrBot等前端 (OpenAI API兼容)")
        print(Fore.GREEN + "1: 终端聊天模式")
        print(Fore.GREEN + "2: 沙箱聊天模式 (Web界面)")
        print(Fore.GREEN + "3: 运行服务诊断")
        print(Fore.GREEN + "5: Web控制面板")
        print(Fore.CYAN + "-" * 50)

        while True:
            try:
                # 调整可选项
                choice = input(Fore.YELLOW + "请选择模式 (0/1/2/3/5): ").strip()
                if choice in ['0', '1', '2', '3', '5']:
                    if choice == '3':
                        full_diagnosis()
                    else:
                        run_mode(int(choice))
                    break
                print(Fore.RED + "无效选择，请重新输入!")
            except UnicodeEncodeError:
                print(Fore.RED + "编码错误! 请确保终端支持UTF-8")
                break
    else:
        try:
            mode = int(sys.argv[1])
            if mode == 3:
                full_diagnosis()
            else:
                run_mode(mode)
        except (IndexError, ValueError):
            print(Fore.RED + "无效的命令行参数。请使用 0, 1, 2, 3 或 5 指定模式")
