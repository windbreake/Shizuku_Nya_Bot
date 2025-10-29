"""系统诊断工具，用于检查服务状态和连接"""

import os
import socket
import sys

import requests
from colorama import Fore, init

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import CONFIG

# 初始化colorama
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
    print(Fore.YELLOW + "🐱 猫娘服务诊断工具")
    print(Fore.CYAN + "=" * 50)
    check_ports()
    test_local_api()
    test_deepseek_api()
    print(Fore.CYAN + "\n诊断完成!")


def main():
    """主函数"""
    full_diagnosis()


if __name__ == "__main__":
    main()