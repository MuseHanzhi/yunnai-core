# yunnai-core

一个基于 Python 的 AI Agent 核心框架，支持插件扩展、多大模型对接和 IPC 通信。

## 描述

yunnai-core 是一个轻量级的 AI Agent 开发框架，采用插件化架构设计。框架内置 LLM 客户端、IPC 通信机制、工具调用系统等核心组件，开发者可通过插件机制灵活扩展功能。

主要特性：

- **插件化架构**：通过插件系统扩展功能，支持插件间通信和生命周期钩子
- **多大模型支持**：兼容 OpenAI 接口的 LLM 提供者，包括 DeepSeek、Qwen、Kimi、Doubao 等
- **IPC 通信**：基于 WebSocket 的进程间通信机制
- **工具调用**：支持 Tool/Function Calling 功能
- **流式响应**：支持 LLM 流式输出

## 架构图

```Textile
┌─────────────────────────────────────────────────────────────┐
│                        Application                          │
│                    (核心应用类)                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PluginManager│  │  LLM Client  │  │  IPC Client  │      │
│  │  (插件管理)   │  │  (大模型)    │  │  (通信)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                        Plugins (插件)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐│
│  │  MCP    │ │  WebUI  │ │  CLI    │ │ Memory  │ │ Skill ││
│  │ Plugin  │ │ Plugin  │ │ Plugin  │ │ Plugin  │ │Plugin ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘│
├─────────────────────────────────────────────────────────────┤
│                     Components (组件)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ipc_com      │  │    llm       │  │ plugin_mgr   │      │
│  │ (通信组件)    │  │  (大模型组件) │  │  (插件管理)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                      Core (核心)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ app_context  │  │    logger    │  │    tools     │      │
│  │  (应用上下文) │  │   (日志)     │  │  (工具函数)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块说明

| 模块                | 说明                              |
| ----------------- | ------------------------------- |
| **Application**   | 核心应用类，协调各组件工作                   |
| **PluginManager** | 插件管理器，负责插件的加载、卸载和生命周期管理         |
| **LLM Client**    | 大模型客户端，对接各 LLM 提供者              |
| **IPC**           | WebSocket 通信组件，支持进程间消息传递        |
| **Tools**         | 工具函数系统，支持 Tool/Function Calling |

### 插件系统

框架提供以下内置插件：

| 插件                       | 说明                                |
| ------------------------ | --------------------------------- |
| **mcp\_plugin**          | MCP (Model Context Protocol) 协议支持 |
| **webui\_plugin**        | Web 用户界面                          |
| **cli\_plugin**          | 命令行工具集                            |
| **memory\_plugin**       | 记忆管理                              |
| **skill\_plugin**        | 技能扩展                              |
| **system\_info\_plugin** | 系统信息获取                            |

## 亮点特点

### 1. 插件化设计

- 插件独立目录，通过 `manifest.yaml` 定义元数据
- 支持 `before` / `after` 钩子注入
- 插件间可通过 IPC 机制通信

### 2. 多 LLM 支持

- 支持 DeepSeek、Qwen、Kimi、Doubao 等主流模型
- 统一的 OpenAI 兼容接口
- 流式响应支持

### 3. 灵活的配置系统

- `app_config.yaml`：应用主配置（日志、大模型、系统设置）
- `fixed_config.yaml`：固定配置（插件路径、作者信息）
- 支持环境变量配置

### 4. 完善的日志系统

- 多级别日志（debug、info、error）
- 支持控制台和文件输出
- 可配置日志格式和路径

### 5. IPC 通信

- 基于 WebSocket 的双向通信
- 支持请求/响应和事件发布/订阅模式
- 内置重连机制

## 快速开始

### 环境要求

- Python 3.10+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

在 `.env` 文件中配置 API Key：

```bash
DASHSCOPE_API_KEY=your_api_key_here
```

### 运行

```bash
python main.py
```

## 项目结构

```
yunnai-core/
├── main.py                    # 应用入口
├── app_config.yaml            # 应用配置
├── fixed_config.yaml          # 固定配置
├── requirements.txt            # 依赖
└── src/
    ├── application.py          # 核心应用类
    ├── core/                  # 核心模块
    │   ├── app_context/       # 应用上下文
    │   ├── logger/             # 日志系统
    │   └── tools/              # 工具函数
    ├── components/             # 组件
    │   ├── ipc_com/            # IPC 通信
    │   ├── llm/                # 大模型
    │   └── plugin_manager/     # 插件管理
    ├── plugins/                # 插件目录
    │   ├── mcp_plugin/         # MCP 插件
    │   ├── webui_plugin/       # WebUI 插件
    │   ├── cli_plugin/         # CLI 插件
    │   ├── memory_plugin/      # 记忆插件
    │   ├── skill_plugin/       # 技能插件
    │   └── system_info_plugin/ # 系统信息插件
    └── ipc_handlers/           # IPC 处理器
```

## License

MIT License
