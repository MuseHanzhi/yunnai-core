# yunnai-core

<div align="center">

**基于 Python 的智能代理系统框架**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![WebSocket](https://img.shields.io/badge/Protocol-WebSocket-orange.svg)]()

</div>

## 📖 项目简介

**yunnai-core**（云乃核心）是一个功能强大的智能代理系统框架，专为自动化任务处理和智能交互场景设计。它采用模块化、插件化架构，提供多模型适配和高效的进程间通信能力。

### ✨ 核心特性

- **🔄 IPC 通信系统**：基于 WebSocket 的双向通信，支持事件模式（单向通知）和调用模式（请求/响应），内置心跳检测与超时机制
- **🤖 多模型 AI 聊天**：无缝集成主流大语言模型（Qwen、Kimi、Doubao、DeepSeek），支持流式与非流式响应
- **🔌 插件扩展机制**：动态加载插件系统，通过 Hook 机制在应用生命周期关键节点注入自定义逻辑
- **🛠️ MCP 集成**：Model Context Protocol 管理器，支持本地进程与远程 HTTP 服务，实现工具调用能力
- **⚙️ 灵活配置管理**：基于 YAML 的配置系统，支持环境变量注入与命令行参数覆盖
- **📝 完善的日志系统**：多级别日志记录，支持控制台和文件输出，便于调试与监控

## 🏗️ 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│                  Application Core                    │
├──────────────┬──────────────┬───────────────────────┤
│  Plugin      │   LLM        │   IPC Server          │
│  Manager     │   Client     │   (WebSocket)         │
├──────────────┼──────────────┼───────────────────────┤
│  Hooks       │  Adapters    │   Handlers            │
│  System      │  (Qwen/Kimi/ │   - App Module        │
│              │   Doubao/    │   - MCP Module        │
│              │   DeepSeek)  │                       │
└──────────────┴──────────────┴───────────────────────┘
         │              │               │
    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐
    │Plugins  │    │Models   │   │External │
    │         │    │         │   │Clients  │
    └─────────┘    └─────────┘   └─────────┘
```

### 设计模式

- **插件模式**：`PluginManager` 统一管理插件注册与生命周期
- **适配器模式**：`model_adapters` 封装不同 LLM 提供商接口，实现统一调用
- **观察者模式**：生命周期钩子 (`Hooks`) 在特定节点触发回调，实现解耦
- **管理器模式**：`Application` 集中管理服务状态和资源

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理工具

### 安装步骤

1. **克隆仓库**

```bash
git clone <repository-url>
cd yunnai-core
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件并配置必要的 API Key：

```env
# 必需的环境变量
DASHSCOPE_API_KEY=your_dashscope_api_key
KIMI_API_KEY=your_kimi_api_key
DOUAO_API_KEY=your_doubao_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 可选的环境变量
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
```

4. **配置应用**

编辑 `app_config.yaml` 文件，根据需要调整：
- IPC 通信配置（URI、重连策略）
- 默认 LLM 模型选择
- 日志级别和输出方式
- 插件搜索路径

### 运行应用

```bash
# 基本启动
python main.py

# 指定 IPC URI
python main.py ipc_uri=ws://localhost:6600

# 指定默认 LLM 模型
python main.py default_llm=qwen
```

## 📚 核心模块

### 1. IPC 通信模块

基于 WebSocket 实现的进程间通信系统，支持两种交互模式：

- **Event（事件）**：单向通知，无需响应
- **Invoke（调用）**：请求/响应模式，支持超时控制

详细文档请参考：[IPC 通信指南](docs/ipc_communication_guide.md)

**主要功能：**
- 自动重连机制
- 心跳保活
- 超时控制（默认 10 秒）
- 错误隔离处理

### 2. AI 聊天模块

支持多种主流大语言模型的统一接口：

| 模型 | 提供商 | 配置键 |
|------|--------|--------|
| Qwen | 阿里云 | `qwen` |
| Kimi | 月之暗面 | `kimi` |
| Doubao | 火山引擎 | `doubao` |
| DeepSeek | DeepSeek | `deepseek` |

**特性：**
- 流式与非流式响应
- 思维链控制（enable_thinking）
- 统一的 OpenAI 兼容接口
- 自动重试与错误处理

### 3. 插件系统

基于 Hook 机制的动态扩展系统，允许在不修改核心代码的情况下扩展功能。

**插件类型：**
- **CLI 插件**：命令行交互增强
- **MCP 插件**：Model Context Protocol 工具集成
- **Skill 插件**：特定技能扩展
- **System Info 插件**：系统信息监控

详细开发指南请参考：[插件开发文档](docs/plugin_development_guide.md)

**生命周期钩子：**
- `on_app_before_initialize`：应用初始化前
- `on_app_after_initialized`：应用初始化后
- `on_ready`：应用就绪
- `on_message_before_send`：消息发送前
- `on_message_after_sended`：消息发送后
- `on_llm_response`：LLM 响应时
- `on_app_will_close`：应用关闭前

### 4. MCP 管理器

Model Context Protocol 集成管理器，支持：
- 本地 MCP 服务器进程管理
- 远程 HTTP MCP 服务连接
- 工具动态发现与调用
- 错误隔离（单个 MCP 失败不影响其他服务）

### 5. 配置管理系统

灵活的配置加载机制：

```yaml
# app_config.yaml 结构
logging:          # 日志配置
system:           # 系统配置（IPC、线程池等）
llm:             # 大模型配置
plugin_config:   # 插件配置
```

**优先级顺序：**
1. 命令行参数（最高优先级）
2. 环境变量
3. YAML 配置文件（默认值）

## 💡 使用示例

### 通过 IPC 发送消息

```python
import asyncio
import websockets
import json

async def send_message():
    uri = "ws://localhost:6600"
    async with websockets.connect(uri) as websocket:
        # 发送消息到智能体
        message = {
            "type": "event",
            "name": "send_message",
            "data": {
                "message": "你好，请介绍一下自己",
                "options": {
                    "model_name": "qwen",
                    "stream": True
                }
            }
        }
        await websocket.send(json.dumps(message))
        
        # 接收 LLM 响应
        async for response in websocket:
            data = json.loads(response)
            if data["type"] == "llm_response":
                print(data["data"]["chat_completion"])

asyncio.run(send_message())
```

### 创建自定义插件

```python
# src/plugins/my_plugin/plugin.py
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import hook

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.name = "my_plugin"
    
    @hook("on_message_before_send", "before")
    async def before_send_handler(self, state, **kwargs):
        """在消息发送前处理"""
        print(f"准备发送消息: {state.user_message}")
        return state
    
    @hook("on_llm_response", "after")
    async def after_response_handler(self, chat_completion, **kwargs):
        """在 LLM 响应后处理"""
        print("收到 LLM 响应")
        return chat_completion
```

创建 `manifest.yaml`：

```yaml
name: my_plugin
version: 1.0.0
description: 我的自定义插件
author: Your Name
enabled: true
```

## 📁 项目结构

```
yunnai-core/
├── docs/                      # 文档目录
│   ├── ipc_communication_guide.md    # IPC 通信指南
│   └── plugin_development_guide.md   # 插件开发指南
├── logs/                      # 日志输出目录
├── prompts/                   # 提示词模板
├── src/                       # 源代码
│   ├── application.py         # 应用主入口
│   ├── components/            # 核心组件
│   │   ├── ipc/              # IPC 通信模块
│   │   ├── llm/              # LLM 客户端
│   │   └── plugin_manager/   # 插件管理器
│   ├── core/                 # 核心上下文
│   ├── ipc_handlers/         # IPC 处理器
│   ├── plugins/              # 插件目录
│   │   ├── cli_plugin/       # CLI 插件
│   │   ├── mcp_plugin/       # MCP 插件
│   │   ├── skill_plugin/     # 技能插件
│   │   └── system_info_plugin/  # 系统信息插件
│   ├── types/                # 类型定义
│   └── utils/                # 工具函数
├── test/                     # 测试文件
├── wakeup_models/            # 唤醒模型
├── .env                      # 环境变量配置
├── .gitignore               # Git 忽略配置
├── app_config.yaml          # 应用配置文件
├── LICENSE                  # 开源许可证
├── main.py                  # 启动脚本
└── requirements.txt         # Python 依赖
```

## 🔧 开发指南

### 添加新模型支持

1. 在 `app_config.yaml` 中添加模型配置：

```yaml
llm:
  models:
    "new_model":
      name: "model-name"
      key_name: "NEW_MODEL_API_KEY"
      base_url: "https://api.example.com/v1"
      stream: true
      extra_body: {}
```

2. 在 `.env` 文件中添加 API Key：

```env
NEW_MODEL_API_KEY=your_api_key
```

### 调试技巧

- 查看 `logs/` 目录下的日志文件
- 设置日志级别为 `debug` 获取详细信息
- 使用 `python -m pdb main.py` 进行断点调试

## ⚠️ 注意事项

1. **API Key 安全**：切勿将 `.env` 文件提交到版本控制系统
2. **路径处理**：包含 `~` 的路径需显式调用 `.expanduser()`
3. **异步编程**：避免在非主线程中直接调用 `asyncio.get_event_loop()`
4. **插件命名**：插件目录必须以 `_plugin` 结尾
5. **并发控制**：CPU 密集型任务应提交至线程池执行

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者

---

<div align="center">

**Made with ❤️ by yunnai-core Team**

</div>
