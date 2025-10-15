import os
import socket
import requests
import json

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 从JSON文件加载配置
def load_config():
    config_path = os.path.join(PROJECT_ROOT, 'data', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载配置
CONFIG_DATA = load_config()

CONFIG = {
    'server': {
        'port': 8888,    # Web服务器端口
        'log_file': os.path.join(PROJECT_ROOT, 'app.log'),  # 使用绝对路径
    },
    'api': {
        'key': CONFIG_DATA['api_keys']['deepseek_chat']['key'],
        'base_url': CONFIG_DATA['api_keys']['deepseek_chat']['base_url']
    },
    'aliyun_api': {
        'key': CONFIG_DATA['api_keys']['image_recognition']['key'],
        'base_url': CONFIG_DATA['api_keys']['image_recognition']['base_url']
    },
    'search_api': {
        'key': CONFIG_DATA['api_keys']['search']['key'],
        'base_url': CONFIG_DATA['api_keys']['search']['base_url']
    },
    'character': CONFIG_DATA['character'],
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