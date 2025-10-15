# koishi_service.py
import socket
import uvicorn
from fastapi import FastAPI, Request
from .ai_chat_system import AIChatSystem
import time
import json
from fastapi.responses import StreamingResponse
# 确保正确导入 colorama
from colorama import Fore, init
from .database import DatabaseManager

init(autoreset=True)

app = FastAPI()

chat_system = AIChatSystem()
chat_system.db = DatabaseManager()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        data = await request.json()
        print(Fore.CYAN + f"收到请求: {data}")

        # 动态选择模型，后端支持 deepseek-chat / deepseek-vl / o4-mini-preview
        selected_model = data.get("model", "deepseek-chat")

        # 新增：neko 模型专属处理，直接走本地 AIChatSystem
        if selected_model == "neko":
            user_input = ""
            image_data = None
            for msg in reversed(data.get("messages", [])):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                user_input += item.get("text", "")
                            elif isinstance(item, dict) and item.get("type") == "image_url":
                                image_data = item.get("image_url", {}).get("url")
                    else:
                        user_input = content
                    break

            response_text = chat_system.chat(user_input, image=image_data)
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "neko",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # 提取用户消息
        user_input = ""
        messages = data.get('messages', [])
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_input = msg.get('content', "")
                break

        print(Fore.GREEN + f"用户输入: {user_input}")

        stream_mode = data.get("stream", False)
        if stream_mode:
            async def event_generator():
                content_accum = ""
                # 逐块请求 API 并推送
                for chunk in chat_system.client.chat.completions.create(
                        model=selected_model,
                        messages=chat_system.messages + [{"role": "user", "content": user_input}],
                        temperature=0.7, max_tokens=200, timeout=30, stream=True
                ):
                    # 修改这里，从属性读取 content
                    delta = getattr(chunk.choices[0].delta, "content", "")
                    if delta:
                        content_accum += delta
                        payload = {
                            "choices": [{
                                "delta": {"content": delta},
                                "index": 0,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(payload)}\n\n"
                chat_system.db.save_chat(user_input, content_accum)
                yield "data: [DONE]\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        # 调用 DeepSeek 接口，使用动态模型
        response = chat_system.client.chat.completions.create(
            model=selected_model,
            messages=chat_system.messages + [{"role": "user", "content": user_input}],
            temperature=0.7,
            max_tokens=200,
            timeout=30
        )
        ai_response = response.choices[0].message.content
        chat_system.messages.append({"role": "assistant", "content": ai_response})
        chat_system.db.save_chat(user_input, ai_response)

        # 提取 usage 信息
        usage_info = getattr(response, "usage", None)
        result = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": selected_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": ai_response
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": usage_info.prompt_tokens if usage_info else 0,
                "completion_tokens": usage_info.completion_tokens if usage_info else 0,
                "total_tokens": usage_info.total_tokens if usage_info else 0
            }
        }

        print(Fore.CYAN + f"发送响应: {result}")
        return result

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(Fore.RED + f"完整错误信息:\n{error_trace}")

        # 即使出现错误，也返回有效的JSON格式
        return {
            "id": f"error-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data.get("model", "deepseek-chat"),
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
        }


@app.get("/")
async def root():
    """根路径返回服务信息"""
    return {
        "service": "Koishi API Service",
        "endpoints": [
            "/v1/chat/completions (POST)",
            "/v1/models (GET)",
            "/health (GET)"
        ]
    }


@app.get("/v1/models")
async def model_list():
    """返回支持的模型列表"""
    return {
        "object": "list",
        "data": [
            {"id": "deepseek-chat", "object": "model", "created": int(time.time()), "owned_by": "local"},
            {"id": "deepseek-v1", "object": "model", "created": int(time.time()), "owned_by": "local"},
            {"id": "neko", "object": "model", "created": int(time.time()), "owned_by": "neko"}  # 添加neko模型
        ]
    }


@app.get("/health")
async def health_check():
    """服务健康检查"""
    return {"status": "ok", "service": "Koishi API"}


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # 设置超时时间
        try:
            s.connect(("localhost", port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False
        except OSError:
            # 其他OSError也认为端口不可用
            return True


def find_available_port(start_port=5000, end_port=5100):
    """在指定范围内查找可用端口"""
    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port):
            return port
    return None


def run_koishi_service():
    """Koishi映射模式 (FastAPI服务)"""
    # 创建FastAPI应用
    fastapi_app = FastAPI()

    # 添加CORS中间件
    from fastapi.middleware.cors import CORSMiddleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    chat_system = AIChatSystem()
    chat_system.db = DatabaseManager()

    @fastapi_app.post("/v1/chat/completions")
    async def openai_api(request: Request):
        try:
            data = await request.json()
            print(Fore.CYAN + f"收到请求: {data}")

            # 动态选择模型，后端支持 deepseek-chat / deepseek-vl / o4-mini-preview
            selected_model = data.get("model", "deepseek-chat")

            # 新增：neko 模型专属处理
            if selected_model == "neko":
                user_input = ""
                image_data = None
                for msg in reversed(data.get("messages", [])):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    user_input += item.get("text", "")
                                elif isinstance(item, dict) and item.get("type") == "image_url":
                                    image_data = item.get("image_url", {}).get("url")
                        else:
                            user_input = content
                        break

                response_text = chat_system.chat(user_input, image=image_data)
                return {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "neko",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop"
                    }],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                }

            # 提取用户消息
            user_input = ""
            messages = data.get('messages', [])
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_input = msg.get('content', "")
                    break
            print(Fore.GREEN + f"用户输入: {user_input}")

            stream_mode = data.get("stream", False)
            if stream_mode:
                async def event_generator():
                    content_accum = ""
                    # 逐块请求 API 并推送
                    for chunk in chat_system.client.chat.completions.create(
                            model=selected_model,
                            messages=chat_system.messages + [{"role": "user", "content": user_input}],
                            temperature=0.7, max_tokens=200, timeout=30, stream=True
                    ):
                        # 修改这里，从属性读取 content
                        delta = getattr(chunk.choices[0].delta, "content", "")
                        if delta:
                            content_accum += delta
                            payload = {
                                "choices": [{
                                    "delta": {"content": delta},
                                    "index": 0,
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(payload)}\n\n"
                    chat_system.db.save_chat(user_input, content_accum)
                    yield "data: [DONE]\n\n"

                return StreamingResponse(event_generator(), media_type="text/event-stream")

            # 调用 DeepSeek 接口，使用动态模型
            response = chat_system.client.chat.completions.create(
                model=selected_model,
                messages=chat_system.messages + [{"role": "user", "content": user_input}],
                temperature=0.7,
                max_tokens=200,
                timeout=30
            )
            ai_response = response.choices[0].message.content
            chat_system.messages.append({"role": "assistant", "content": ai_response})
            chat_system.db.save_chat(user_input, ai_response)

            usage_info = getattr(response, "usage", None)
            result = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": selected_model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ai_response
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": usage_info.prompt_tokens if usage_info else 0,
                    "completion_tokens": usage_info.completion_tokens if usage_info else 0,
                    "total_tokens": usage_info.total_tokens if usage_info else 0
                }
            }
            print(Fore.CYAN + f"发送响应: {result}")
            return result

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(Fore.RED + f"完整错误信息:\n{error_trace}")
            return {
                "id": f"error-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": data.get("model", "deepseek-chat"),
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
            }

    @fastapi_app.get("/")
    async def root():
        """根路径返回服务信息"""
        return {
            "service": "Koishi API Service",
            "endpoints": [
                "/v1/chat/completions (POST)",
                "/v1/models (GET)",
                "/health (GET)"
            ]
        }

    @fastapi_app.get("/v1/models")
    async def model_list():
        """返回支持的模型列表"""
        return {
            "object": "list",
            "data": [
                {"id": "deepseek-chat", "object": "model", "created": int(time.time()), "owned_by": "deepseek"},
                {"id": "neko", "object": "model", "created": int(time.time()), "owned_by": "neko"},  # 添加neko模型
                {"id": "gpt-3.5-turbo", "object": "model", "created": int(time.time()), "owned_by": "neko"}
            ]
        }

    @fastapi_app.get("/health")
    async def health_check():
        """服务健康检查"""
        return {"status": "ok", "service": "Koishi API"}

    # 统一API接口，隐藏后端多个API的复杂性
    @fastapi_app.post("/v1/unified/chat/completions")
    async def unified_chat_completions(request: Request):
        """
        统一聊天完成接口
        前端可以像调用单一模型一样调用此接口，
        后端会根据内容自动决定调用哪些API（文本、图像识别、网络搜索等）
        """
        try:
            data = await request.json()
            print(Fore.CYAN + f"收到统一API请求: {data}")

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

            print(Fore.GREEN + f"处理后用户输入: {user_input}")
            print(Fore.GREEN + f"提取到图片URL: {image_urls}")

            stream_mode = data.get("stream", False)
            if stream_mode:
                async def event_generator():
                    # 调用AI聊天系统处理（会自动处理图片和搜索等）
                    # 对于流式响应，我们先生成一个完整的回复，然后逐字发送
                    if image_urls:
                        # 如果有图片URL，传递第一张图片
                        full_response = chat_system.chat(user_input, image=image_urls[0])
                    else:
                        # 否则只处理文本
                        full_response = chat_system.chat(user_input)
                    
                    # 逐字发送响应
                    for i, char in enumerate(full_response):
                        payload = {
                            "choices": [{
                                "delta": {"content": char},
                                "index": 0,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(payload)}\n\n"
                    
                    # 发送结束标记
                    yield "data: [DONE]\n\n"

                return StreamingResponse(event_generator(), media_type="text/event-stream")

            # 调用AI聊天系统处理（会自动处理图片和搜索等）
            if image_urls:
                # 如果有图片URL，传递第一张图片
                response_text = chat_system.chat(user_input, image=image_urls[0])
            else:
                # 否则只处理文本
                response_text = chat_system.chat(user_input)

            # 构造符合OpenAI格式的响应
            result = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "neko",  # 对前端隐藏真实模型，使用"neko"作为模型名称
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            print(Fore.CYAN + f"发送统一API响应: {result}")
            return result

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(Fore.RED + f"统一API错误:\n{error_trace}")
            
            # 返回错误信息但仍保持OpenAI格式
            return {
                "id": f"error-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "neko",  # 错误响应也使用"neko"作为模型名称
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
            }

    # 查找可用端口
    port = find_available_port()
    if port is None:
        print(Fore.RED + "错误: 没有找到可用端口 (5000-5100)")
        return

    print(Fore.CYAN + f"\n🚀 Koishi映射模式已启动: http://localhost:{port}/v1")
    print(Fore.YELLOW + f"请在 AstrBot 中将 API 地址设置为: http://localhost:{port}/v1")
    # 增加超时设置和响应头配置
    uvicorn.run(
        fastapi_app,
        host="127.0.0.1",  # 使用127.0.0.1而不是0.0.0.0更安全
        port=port,  # 使用找到的可用端口
        timeout_keep_alive=120,  # 增加保持连接超时
        log_level="debug"  # 开启调试日志
    )
