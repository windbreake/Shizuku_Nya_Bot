import socket
import requests
from colorama import Fore, init  # 添加必要的导入

# 初始化colorama
init(autoreset=True)


def check_ports():
    """检查常用端口状态"""
    ports = [5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010]
    print(Fore.CYAN + "端口检查:")
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 如果连接成功（返回0），则端口被占用；否则空闲
            if s.connect_ex(('localhost', port)) == 0:
                print(Fore.RED + f"  - 端口 {port}: {Fore.YELLOW}占用中")
            else:
                print(Fore.GREEN + f"  - 端口 {port}: {Fore.GREEN}空闲")


def make_request_and_print(url, description, headers=None):
    """发送HTTP请求并打印结果"""
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(Fore.GREEN + f"  {description}: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(Fore.RED + f"  {description}失败: {str(e)}")
        return False


def test_local_api():
    """测试本地API服务"""
    print(Fore.CYAN + "\n本地API测试:")

    # 查找可用端口
    available_port = None
    for port in range(5000, 5010):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                available_port = port
                break

    if available_port:
        print(Fore.GREEN + f"  找到可用端口: {available_port}")
        # 测试根路径
        make_request_and_print(f"http://localhost:{available_port}", "根路径状态")
        # 测试/v1/models端点
        make_request_and_print(f"http://localhost:{available_port}/v1/models", "模型列表状态")
    else:
        print(Fore.RED + "  未检测到运行中的服务 (5000-5010)")
        print(Fore.YELLOW + "  请先启动服务后再运行诊断")


def test_deepseek_api():
    """测试DeepSeek API连接"""
    print(Fore.CYAN + "\n API连通性测试:")
    try:
        from src.config import CONFIG
        headers = {"Authorization": f"Bearer {CONFIG['api']['key']}"}
        success = make_request_and_print(
            f"{CONFIG['api']['base_url']}/models",
            "API状态",
            headers
        )
        if success:
            response = requests.get(
                f"{CONFIG['api']['base_url']}/models",
                headers=headers,
                timeout=5
            )
            print(Fore.GREEN + f"  响应内容: {response.text[:200]}...")
    except Exception as e:
        print(Fore.RED + f"  API连接失败: {str(e)}")
        print(Fore.YELLOW + "  请检查网络连接或代理设置")


def full_diagnosis():
    """执行完整诊断流程"""
    print(Fore.CYAN + "=" * 50)
    print(Fore.YELLOW + "🐱 服务诊断工具")
    print(Fore.CYAN + "=" * 50)
    check_ports()
    test_local_api()
    test_deepseek_api()
    print(Fore.CYAN + "\n诊断完成! 请将结果发送给技术支持")


if __name__ == "__main__":
    full_diagnosis()
