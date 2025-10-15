# ai_chat_system.py
# AI聊天系统核心逻辑
import threading
import base64
import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI
import openai  # 导入openai以使用Timeout异常
import sys
import os
import re

# 添加当前目录到系统路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 修复导入问题
import config
from config import CONFIG
from database import DatabaseManager


class AIChatSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.db = DatabaseManager()
        character = self.db.get_character_info()

        # 提取口癖并处理
        catchphrases = character['catchphrases'] or '喵'
        phrases_list = [phrase.strip() for phrase in catchphrases.split(',') if phrase.strip()]

        self.system_prompt = (
            f"你叫{character['name']}，是一只{character['personality']}。"
            f"你的哥哥QQ是：{character['brother_qqid']}。"
            "必须遵守以下规则：\n"
            f"1. 每句话结尾随机使用以下口癖：{catchphrases}\n"
            "2. 不使用括号描述动作神态\n"
            "3. 保持简洁可爱（回复不超过100字）\n\n"
            "示例对话：\n"
            "用户: 在干嘛？\n"
            f"你: 等哥哥消息呢{phrases_list[0] if phrases_list else '喵~'}\n"
            "用户: 喜欢哥哥吗？\n"
            f"你: 才...才不喜欢呢{phrases_list[1] if len(phrases_list) > 1 else '哒！'}"
        )

        # 使用配置中的基础URL
        self.client = OpenAI(
            api_key=CONFIG['api']['key'],
            base_url=CONFIG['api']['base_url']
        )
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def compress_image(self, base64_data):
        """压缩图片以减少大小"""
        try:
            # 提取纯base64数据
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]

            # 解码base64
            img_data = base64.b64decode(base64_data)
            img = Image.open(BytesIO(img_data))

            # 压缩图片：调整大小和质量
            max_size = 1024
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size))

            # 转换为JPEG格式减少大小
            output_buffer = BytesIO()
            img = img.convert("RGB")  # 确保是RGB格式
            img.save(output_buffer, format="JPEG", quality=85)
            compressed_data = output_buffer.getvalue()

            # 重新编码为base64
            return base64.b64encode(compressed_data).decode('utf-8')

        except Exception as e:
            print(f"图片压缩错误: {e}")
            return base64_data.split(',')[-1] if ',' in base64_data else base64_data

    def analyze_image_with_aliyun(self, image_data):
        """使用阿里云通义VL MAX分析图片"""
        try:
            # 提取纯base64数据
            if ',' in image_data:
                base64_data = image_data.split(',', 1)[1]
            else:
                base64_data = image_data

            # 构建请求头
            headers = {
                "Authorization": f"Bearer {CONFIG['aliyun_api']['key']}",
                "Content-Type": "application/json"
            }

            # 构建请求体
            payload = {
                "model": "qwen-vl-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": f"data:image/jpeg;base64,{base64_data}"
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
            response = requests.post(
                f"{CONFIG['aliyun_api']['base_url']}/services/aigc/multimodal-generation/generation",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                error_msg = f"阿里云API错误: {response.status_code} - {response.text}"
                print(f"Aliyun API Error: {error_msg}")
                return error_msg

            result = response.json()
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
                    return " ".join(text_parts)
                return str(content)
            else:
                return "无法解析图片内容"

        except Exception as e:
            error_msg = f"图片分析失败: {str(e)}"
            print(f"Image Analysis Error: {error_msg}")
            return error_msg

    def analyze_image_from_url(self, image_url):
        """通过URL获取图片并使用阿里云通义VL MAX分析图片"""
        try:
            # 从URL获取图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 将图片转换为Base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            
            # 使用现有的方法分析图片
            return self.analyze_image_with_aliyun(image_data)
            
        except Exception as e:
            error_msg = f"从URL获取图片失败: {str(e)}"
            print(f"Image URL Error: {error_msg}")
            return error_msg

    def search_with_ai_search(self, query):
        """使用AI Search API进行搜索"""
        try:
            headers = {
                "Authorization": f"Bearer {CONFIG['search_api']['key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "count": 10
            }
            
            response = requests.post(
                CONFIG['search_api']['base_url'],
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"搜索API错误: {response.status_code} - {response.text}"
                print(f"Search API Error: {error_msg}")
                return error_msg
            
            result = response.json()
            # 修复数据结构解析问题：使用webPages而不是web_pages
            if "data" in result and "webPages" in result["data"] and "value" in result["data"]["webPages"]:
                search_results = result["data"]["webPages"]["value"][:10]  # 只取前10个结果
                formatted_results = []
                for item in search_results:
                    # 使用与test_webapi.py相同的字段名，但注意API实际返回的字段名
                    name = item.get("name", "")
                    snippet = item.get("snippet", "")
                    url = item.get("url", "")
                    # 格式化搜索结果，便于AI理解
                    formatted_results.append({
                        "title": name,
                        "url": url,
                        "snippet": snippet
                    })
                
                # 将搜索结果转换为文本格式
                result_text = "搜索结果:\n"
                for i, item in enumerate(formatted_results, 1):
                    result_text += f"{i}. {item['title']}\n   {item['snippet']}\n   URL: {item['url']}\n\n"
                return result_text
            else:
                return "未找到相关搜索结果"
                
        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            print(f"Search Error: {error_msg}")
            return error_msg

    def should_search(self, user_input):
        """判断是否需要进行搜索"""
        if not user_input:
            return False
            
        # 定义触发搜索的关键词模式
        search_keywords = [
            r'(?:(?:搜索|查|找|了解|知道|什么是|是什么|怎么样|如何|怎么|哪里|哪儿|哪个|哪些|谁是|谁的|几点|时间|日期|天气|新闻|最新|最近|现在).*)',
            r'(.*(?:天气|新闻|股价|比分|时间|日期|定义|解释|介绍|攻略|评测|比较|区别|方法|步骤|教程|怎么做).*)',
            r'(.*(?:最新|最近|现在|今天|明天|昨天|今年|去年|这个月|下个月|上个月).*)'
        ]
        
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

    def chat(self, user_input, image=None):
        """处理聊天请求，支持文本和图片"""
        image_description = None
        search_result = None
        
        # 处理图片
        if image:
            # 使用阿里云通义VL MAX分析图片
            image_description = self.analyze_image_with_aliyun(image)
            # 将图片描述添加到消息历史中
            self.messages.append({
                "role": "user",
                "content": f"[图片内容]: {image_description}"
            })

        # 处理文本输入
        if user_input:
            # 判断是否需要搜索
            if self.should_search(user_input):
                print(f"检测到搜索请求: {user_input}")
                search_result = self.search_with_ai_search(user_input)
                # 将搜索结果添加到消息历史中
                search_context = f"用户问题: {user_input}\n{search_result}"
                self.messages.append({
                    "role": "user", 
                    "content": search_context
                })
                print(f"搜索结果: {search_result[:100]}...")
            else:
                self.messages.append({"role": "user", "content": user_input})
        # 如果没有文本输入但有图片
        elif not user_input and image:
            self.messages.append({"role": "user", "content": "[用户发送了一张图片]"})
        # 如果没有文本输入
        elif not user_input:
            return "请发送文本内容喵~"

        try:
            # 使用DeepSeek-Chat模型生成回复（添加超时）
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                temperature=0.7,
                max_tokens=200,
                timeout=30  # 30秒超时
            )

            ai_response = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": ai_response})

            # 保存对话记录（包括图片描述）
            self.db.save_chat(user_input or "[图片]", ai_response, image_description)

            return ai_response

        except openai.APITimeoutError:
            return "呜...思考太久超时啦Nanaoda! (>_<)"
        except Exception as e:
            return f"呜...出错啦Nanaoda! ({str(e)})"