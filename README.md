# ShizukuNyaBot-Python

一个基于大语言模型 API 的猫娘聊天系统，支持以下三种运行模式：
- Koishi 映射模式（FastAPI，OpenAI Chat Completion 兼容，示例为koishi，支持大部分相似平台）
- 终端聊天模式（命令行交互）
- 沙箱聊天模式（Flask + Web 前端）

---

## 目录结构

- `main.py`：入口脚本，根据参数选择模式  
- `koishi_service.py`：FastAPI 实现的 OpenAI-completion 兼容接口  
- `web_server.py`：终端模式 & Web 沙箱模式（Flask）  
- `ai_chat_system.py`：AIChatSystem 核心逻辑，封装 DeepSeek 调用及消息管理  
- `database.py`：MySQL 数据库操作（角色和聊天记录）  
- `config.py`：配置文件（API Key、Base URL、数据库连接）  
- `chat-sandbox.html`：沙箱模式的前端页面  
- `start.bat`：Windows 启动脚本，安装依赖并选择运行模式  

---

## 环境准备

1. Python ≥3.8  
2. MySQL 数据库（schema 包含 `character_info`、`chat_history` 表）  
3. 克隆或下载本项目到本地

---

## 快速开始

1. 激活虚拟环境：  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: .\venv\Scripts\activate
   ```
2. 安装依赖：  
   ```bash
   pip install fastapi uvicorn flask openai mysql-connector-python pillow colorama requests
   ```
3. 修改 `config.py` 中的 `api.key`、`api.base_url` 及数据库连接信息。  
4. 直接运行 Windows 启动器：  
   ```
   start.bat
   ```
   或者手动调用：
   ```bash
   # Koishi 模式 (OpenAI API 兼容)
   python main.py 0

   # 终端聊天模式
   python main.py 1

   # 沙箱聊天模式（打开 http://localhost:5001）
   python main.py 2
   ```

---

## 各模式说明

### 1. Koishi 映射模式  
- 启动 FastAPI 服务，监听 `/v1/chat/completions`、`/v1/models`、`/health`  
- 支持 OpenAI Chat Completion 标准参数（model、messages、stream 等）  
- 流式返回（SSE）兼容 ChatLuna，当 `stream=true` 时会以 `text/event-stream` 分块推送

### 2. 终端聊天模式  
- 纯命令行交互，输入内容后显示猫娘回复并展示响应耗时  
- 运行：`python main.py 1`

### 3. 沙箱聊天模式  
- Flask+HTML 前端，提供简单的 Web 页面用于测试（支持文本与 Base64 图片）  
- 访问 `http://localhost:5001` 并在页面中聊天  
- 运行：`python main.py 2`

---

## 数据库说明

- character_info：存储角色名称、性格、口癖等信息  
- chat_history：保存用户输入与 AI 回复，后续可扩展查询  

> 如果数据库不存在表，系统会使用默认角色配置，并在保存失败时输出警告。

---

## License

此项目仅供学习，禁止任何商用或外部分发。  
如有问题，请联系项目维护人NekoSunami。
