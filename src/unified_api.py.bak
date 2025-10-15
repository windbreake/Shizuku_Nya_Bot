import os
import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import base64
from io import BytesIO
from PIL import Image
import time
import json

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 从配置获取API密钥和基础URL
from src.config import CONFIG

# 有效自定义API key集合（实际项目中应该从数据库或配置文件读取）
VALID_PROXY_KEYS = {'neko-proxy-key-123', '114514'}

# 中间件函数：验证自定义API key
def authenticate():
    proxy_key = request.headers.get('Authorization')
    if proxy_key:
        # 提取Bearer token
        if proxy_key.startswith('Bearer '):
            proxy_key = proxy_key[7:]  # 移除'Bearer '前缀
    
    if not proxy_key or proxy_key not in VALID_PROXY_KEYS:
        return jsonify({'error': 'Invalid API key'}), 401
    return None  # 通过验证

@app.before_request
def before_request():
    # 对于非健康检查和模型列表的请求进行身份验证
    if request.endpoint not in ['health_check', 'model_list']:
        auth_error = authenticate()
        if auth_error:
            return auth_error

@app.route('/v1/models', methods=['GET'])
def model_list():
    """返回支持的模型列表"""
    return jsonify({
        "object": "list",
        "data": [
            {"id": "neko", "object": "model", "created": int(time.time()), "owned_by": "neko"},
            {"id": "gpt-3.5-turbo", "object": "model", "created": int(time.time()), "owned_by": "neko"}
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """服务健康检查"""
    return jsonify({"status": "ok", "service": "Unified API"})

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """统一聊天完成接口"""
    try:
        data = request.json
        print(f"收到统一API请求: {data}")

        # 提取用户消息
        user_input = ""
        image_urls = []
        messages = data.get('messages', [])
        
        # 遍历所有消息，提取文本和图像URL
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', "")
                # 处理包含image_url的消息
                if isinstance(content, list):
                    # 如果是列表类型，说明包含多种类型的内容（如text和image_url）
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                            elif item.get('type') == 'image_url':
                                # 对于图片URL，提取实际URL并保存
                                image_url = item.get('image_url', {}).get('url', '')
                                if image_url:
                                    image_urls.append(image_url)
                                    text_parts.append(f'[图片: {image_url}]')
                    user_input += ''.join(text_parts)
                else:
                    # 如果是字符串类型，直接使用
                    user_input += content

        print(f"处理后用户输入: {user_input}")
        print(f"提取到图片URL: {image_urls}")

        # 处理图片（如果有的话）
        image_description = None
        if image_urls:
            # 获取第一张图片
            image_url = image_urls[0]
            try:
                # 从URL获取图片
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # 将图片转换为Base64
                image_data = base64.b64encode(response.content).decode('utf-8')
                
                # 使用阿里云通义VL MAX分析图片
                headers = {
                    "Authorization": f"Bearer {CONFIG['aliyun_api']['key']}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "qwen-vl-max",
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "image": f"data:image/jpeg;base64,{image_data}"
                                    },
                                    {
                                        "text": "请详细描述这张图片的内容"
                                    }
                                ]
                            }
                        ]
                    },
                    "parameters": {
                        "max_tokens": 300
                    }
                }

                # 发送请求到阿里云通义VL MAX API
                api_response = requests.post(
                    f"{CONFIG['aliyun_api']['base_url']}/services/aigc/multimodal-generation/generation",
                    headers=headers,
                    json=payload
                )

                if api_response.status_code == 200:
                    result = api_response.json()
                    if "output" in result and "choices" in result["output"]:
                        content = result["output"]["choices"][0]["message"]["content"]
                        # 确保返回的是字符串而不是列表
                        if isinstance(content, list):
                            # 如果是列表，提取其中的文本内容
                            text_parts = []
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    text_parts.append(item["text"])
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            image_description = " ".join(text_parts)
                        else:
                            image_description = str(content)
                        
                        user_input = f"[图片内容: {image_description}] {user_input}"
                else:
                    user_input = f"[图片分析失败] {user_input}"
                    
            except Exception as e:
                print(f"图片处理错误: {e}")
                user_input = f"[图片处理出错] {user_input}"

        # 检查是否需要网络搜索
        search_result = None
        if should_search(user_input):
            try:
                headers = {
                    "Authorization": f"Bearer {CONFIG['search_api']['key']}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "query": user_input,
                    "count": 10
                }
                
                search_response = requests.post(
                    CONFIG['search_api']['base_url'],
                    headers=headers,
                    json=payload
                )
                
                if search_response.status_code == 200:
                    result = search_response.json()
                    # 解析搜索结果
                    if "data" in result and "webPages" in result["data"] and "value" in result["data"]["webPages"]:
                        search_results = result["data"]["webPages"]["value"][:5]  # 只取前5个结果
                        formatted_results = []
                        for item in search_results:
                            name = item.get("name", "")
                            snippet = item.get("snippet", "")
                            url = item.get("url", "")
                            formatted_results.append({
                                "title": name,
                                "url": url,
                                "snippet": snippet
                            })
                        
                        # 将搜索结果转换为文本格式
                        search_result_text = "搜索结果:\n"
                        for i, item in enumerate(formatted_results, 1):
                            search_result_text += f"{i}. {item['title']}\n   {item['snippet']}\n   URL: {item['url']}\n\n"
                        
                        search_result = search_result_text
                        user_input = f"用户问题: {user_input}\n{search_result}"
            except Exception as e:
                print(f"搜索错误: {e}")

        # 使用DeepSeek API生成回复
        headers = {
            "Authorization": f"Bearer {CONFIG['api']['key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_input}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        # 检查是否需要流式响应
        stream_mode = data.get("stream", False)
        if stream_mode:
            # 对于流式响应，我们简单地返回一个模拟的流
            def generate():
                # 这里应该调用实际的流式API，但为了简化，我们模拟一个响应
                response_text = "这是来自统一API的流式响应"
                for char in response_text:
                    payload = {
                        "choices": [{
                            "delta": {"content": char},
                            "index": 0,
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                yield "data: [DONE]\n\n"
            
            return app.response_class(generate(), mimetype='text/event-stream')

        # 发送请求到DeepSeek API
        api_response = requests.post(
            f"{CONFIG['api']['base_url']}/chat/completions",
            headers=headers,
            json=payload
        )

        if api_response.status_code == 200:
            result = api_response.json()
            # 修改模型名称为neko
            result["model"] = "neko"
            return jsonify(result)
        else:
            return jsonify({
                "id": f"error-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "neko",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"出错了喵({api_response.status_code} - {api_response.text})"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"统一API错误:\n{error_trace}")
        
        # 返回错误信息但仍保持OpenAI格式
        return jsonify({
            "id": f"error-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "neko",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"出错了喵({str(e)})"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        })

def should_search(user_input):
    """判断是否需要进行搜索"""
    if not user_input:
        return False
        
    # 定义触发搜索的关键词模式
    search_keywords = [
        r'(?:(?:搜索|查|找|了解|知道|什么是|是什么|怎么样|如何|怎么|哪里|哪儿|哪个|哪些|谁是|谁的|几点|时间|日期|天气|新闻|最新|最近|现在).*)',
        r'(.*(?:天气|新闻|股价|比分|时间|日期|定义|解释|介绍|攻略|评测|比较|区别|方法|步骤|教程|怎么做).*)',
        r'(.*(?:最新|最近|现在|今天|明天|昨天|今年|去年|这个月|下个月|上个月).*)'
    ]
    
    import re
    # 检查用户输入是否包含触发搜索的关键词
    for pattern in search_keywords:
        if re.search(pattern, user_input, re.IGNORECASE):
            return True
            
    # 添加更多智能判断逻辑
    # 如果输入以"查询"、"请问"等词开头，也触发搜索
    if re.match(r'^(查询|请问|我想了解|我想知道)', user_input.strip(), re.IGNORECASE):
        return True
        
    # 如果输入包含问号且长度较短，可能是一个问题查询
    if '?' in user_input or '？' in user_input:
        return True
        
    return False

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')