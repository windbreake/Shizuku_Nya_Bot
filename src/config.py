# config.py
# 集中管理配置信息

import os
import socket
import requests

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = {
    'server': {
        'port': 8888,    # Web服务器端口
        'log_file': os.path.join(PROJECT_ROOT, 'app.log'),  # 使用绝对路径
    },
    'api': {
        'key': 'sk-9f5c098328204a239c8928069a225bed',
        'base_url': 'https://api.deepseek.com/v1'
    },
    'aliyun_api': {
        'key': 'sk-a548806c16e5440e97243d782ba3dcae',
        'base_url': 'https://dashscope.aliyuncs.com/api/v1'
    },
    'search_api': {
        'key': 'sk-0f0c3eea391f468bbe7bb027a98e62f8',
        'base_url': 'https://api.bochaai.com/v1/web-search'
    },
    'database': {
        'host': 'localhost',
        'user': 'root',
        'password': '!NGC339cn',
        'database': 'catgirl_db'
    }
}

def check_service_status():
    """检查所有服务的状态"""
    results = []
    
    # 检查服务端口
    ports_to_check = [
        (8888, "Web服务器"),
        (8081, "控制面板"),
        (8082, "数据库管理"),
        (8083, "日志服务"),
        (5000, "Koishi主端口"),
        (5001, "Koishi备用端口")
    ]
    
    for port, name in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            status = "空闲" if s.connect_ex(('localhost', port)) != 0 else "占用"
            results.append(f"{name} ({port}): {status}")
    
    # 检查API密钥
    try:
        headers = {"Authorization": f"Bearer {CONFIG['api']['key']}"}
        response = requests.get(
            f"{CONFIG['api']['base_url']}/models", 
            headers=headers,
            timeout=5
        )
        api_status = "正常" if response.status_code == 200 else f"错误({response.status_code})"
        results.append(f"API状态: {api_status}")
    except Exception as e:
        results.append(f"API连接失败: {str(e)}")
    
    return "\n".join(results)
