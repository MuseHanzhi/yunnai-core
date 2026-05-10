# yunnai-core 插件开发文档

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [插件结构](#插件结构)
- [核心概念](#核心概念)
  - [Plugin 基类](#plugin-基类)
  - [Hook 机制](#hook-机制)
  - [生命周期钩子](#生命周期钩子)
- [开发指南](#开发指南)
  - [创建新插件](#创建新插件)
  - [manifest.yaml 配置](#manifestyaml-配置)
  - [编写插件代码](#编写插件代码)
  - [使用 Hook 装饰器](#使用-hook-装饰器)
- [高级用法](#高级用法)
  - [插件间通信](#插件间通信)
  - [访问主程序](#访问主程序)
  - [异步编程](#异步编程)
- [最佳实践](#最佳实践)
- [示例插件参考](#示例插件参考)
- [常见问题](#常见问题)

---

## 概述

yunnai-core 的插件系统基于 **Hook（钩子）机制**，允许开发者在应用程序的关键生命周期节点注入自定义逻辑。插件系统具有以下特点：

- 🎯 **非侵入式**：无需修改核心代码即可扩展功能
- 🔌 **热插拔**：支持动态加载和卸载插件
- 🔄 **生命周期管理**：提供完整的应用生命周期钩子
- 📦 **模块化设计**：每个插件独立封装，易于维护
- ⚡ **异步支持**：完全兼容 asyncio 异步编程模型

---

## 快速开始

### 1. 创建插件目录

在 `src/plugins/` 目录下创建一个新的插件文件夹，**必须以 `_plugin` 结尾**：

```bash
mkdir src/plugins/my_custom_plugin
```

### 2. 创建 manifest.yaml

在插件目录中创建 `manifest.yaml` 配置文件：

```yaml
name: "my_custom_plugin"
author: "Your Name"
version: "1.0.0"
description: "插件的简短描述"
entry: "plugin.MyCustomPlugin"
```

### 3. 创建插件主文件

创建 `plugin.py` 文件并实现插件类：

``` python
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry

class MyCustomPlugin(Plugin):
    def __init__(self):
        super().__init__()
    
    @registry.on_ready()
    def on_ready(self):
        print("我的插件已就绪！")
```

### 4. 运行测试

启动应用程序，插件将自动被加载：

```bash
# 不带 IPC URI（默认配置）
python main.py

# 或指定 IPC URI（可选）
python main.py ipc_uri=ws://localhost:6600
```

**注意**：`ipc_uri` 参数是可选的，如果不提供，系统将使用配置文件中的默认值。

---

## 插件结构

一个标准的插件目录结构如下：

```
my_custom_plugin/
├── manifest.yaml          # 插件元数据配置（必需）
├── plugin.py              # 插件主入口文件（必需）
├── README.md              # 插件说明文档（可选）
└── utils/                 # 辅助模块（可选）
    ├── helper.py
    └── __init__.py
```

**说明**：
- `manifest.yaml` 是必需的插件元数据文件，由框架读取
- 如需自定义配置管理，插件开发者可自行实现配置加载逻辑（如读取 YAML、JSON、TOML 等格式）

### 命名规范

- **目录名**：必须以下划线分隔的小写字母命名，以 `_plugin` 结尾
  - ✅ `system_info_plugin`
  - ✅ `mcp_plugin`
  - ❌ `MyPlugin`
  - ❌ `system-info`

- **类名**：使用 PascalCase（大驼峰）命名
  - ✅ `SystemInfoPlugin`
  - ✅ `MCPPlugin`

- **文件名**：使用小写字母和下划线
  - ✅ `plugin.py`
  - ✅ `helper_module.py`

---

## 核心概念

### Plugin 基类

所有插件都必须继承自 `src.plugins.plugin.Plugin` 基类：

``` python
from src.plugins.plugin import Plugin, PluginInfo

class MyPlugin(Plugin):
    info: PluginInfo  # 插件元信息（由框架自动填充）
    
    def __init__(self):
        super().__init__()
        self.enable = True  # 插件启用状态
    
    def deinit(self):
        """插件被卸载时调用"""
        pass
```

#### Plugin 基类属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `info` | `PluginInfo` | 插件元信息（name, author, version, description） |
| `enable` | `bool` | 插件是否启用，默认为 `True` |

#### PluginInfo 结构

``` python
class PluginInfo:
    name: str        # 插件名称
    author: str      # 作者
    version: str     # 版本号
    description: str # 描述
```

### Hook 机制

Hook 是插件系统的核心，允许在特定事件发生时执行自定义代码。通过 `@registry` 装饰器注册 Hook：

``` python
from src.plugins.hook_registry import registry

class MyPlugin(Plugin):
    @registry.on_ready()
    def on_ready(self):
        print("应用就绪时触发")
```

#### Hook 装饰器参数

所有 Hook 装饰器都支持 `timing` 参数，用于控制 Hook 在 **IPC（进程间通信）之前还是之后**执行：

``` python
@registry.on_message_before_send(timing="before")  # 在 IPC 通信之前执行
def hook_before(self, state: MessageState):
    pass

@registry.on_message_before_send(timing="after")   # 在 IPC 通信之后执行
def hook_after(self, state: MessageState):
    pass
```

**timing 参数说明**：
- `"before"`：Hook 在 IPC 消息发送/接收**之前**执行
- `"after"`：Hook 在 IPC 消息发送/接收**之后**执行

这种机制允许插件在 IPC 通信的不同阶段介入，实现更精细的控制逻辑。例如：
- `before` 阶段可以用于数据预处理、权限验证等
- `after` 阶段可以用于结果后处理、日志记录等

#### 指定 IPC 执行时机

``` python
# 在 IPC 通信之前执行
@registry.on_message_before_send(timing="before")
def before_ipc_hook(self, state: MessageState):
    # 在消息发送到 IPC 之前进行预处理
    state.append_dyn("[IPC前处理] ")

# 在 IPC 通信之后执行
@registry.on_message_before_send(timing="after")
def after_ipc_hook(self, state: MessageState):
    # 在消息从 IPC 返回后进行后处理
    state.append_dyn(" [IPC后处理]")
```

**timing 参数的作用**：
- `timing="before"`：Hook 在 **IPC 消息发送之前**执行
- `timing="after"`：Hook 在 **IPC 消息接收之后**执行

**典型应用场景**：
- **before 阶段**：数据预处理、参数校验、权限验证、请求拦截等
- **after 阶段**：结果后处理、响应转换、日志记录、状态更新等

**注意**：如果不指定 timing 参数，默认为 `"before"`。

### 生命周期钩子

系统提供以下生命周期钩子：

#### 1. on_app_before_initialize

**触发时机**：应用程序初始化之前

``` python
@registry.on_app_before_initialize()
def on_app_before_initialize(self, app: "Application"):
    """
    :param app: 主程序实例，可访问 llm_client, ipc_server 等组件
    """
    self.app = app
    print("应用即将初始化")
```

#### 2. on_app_after_initialized

**触发时机**：应用程序初始化完成后

``` python
@registry.on_app_after_initialized()
def on_app_after_initialized(self):
    print("应用初始化完成")
```

#### 3. on_ready

**触发时机**：IPC 连接建立后，应用完全就绪

``` python
@registry.on_ready()
def on_ready(self):
    print("应用已就绪，可以开始处理请求")
```

#### 4. on_message_before_send

**触发时机**：向 LLM 发送消息之前

``` python
from src.components.llm.message_state import MessageState

@registry.on_message_before_send()
def on_message_before_send(self, state: MessageState):
    """
    :param state: 消息状态对象，包含 prompts, messages, mcp_list 等
    """
    # 可以修改或增强消息内容
    state.append_dyn("这是动态注入的内容")
```

#### 5. on_llm_response

**触发时机**：接收到 LLM 响应时（流式和非流式）

``` python
from openai.types.chat import ChatCompletionChunk, ChatCompletion

@registry.on_llm_response()
def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion):
    """
    :param chat_completion: LLM 响应数据
    """
    if isinstance(chat_completion, ChatCompletionChunk):
        # 流式响应处理
        if chat_completion.choices[0].delta.content:
            print(chat_completion.choices[0].delta.content, end="")
    else:
        # 非流式响应处理
        print(chat_completion.choices[0].message.content)
```

⚠️ **重要提示**：在此 Hook 中不建议调用 `app.send_message()`，可能导致深度递归。如需调用 LLM，请使用 `app.llm_client.create_state()` 和 `llm_client.stream_response()`。

#### 6. on_message_after_sended

**触发时机**：消息发送完成后

``` python
@registry.on_message_after_sended()
def on_message_after_sended(self, state: MessageState):
    print("消息已发送")
```

#### 7. on_app_will_close

**触发时机**：应用即将关闭

``` python
@registry.on_app_will_close()
def on_app_will_close(self):
    print("应用即将关闭，清理资源...")
    self.cleanup()
```

---

## 开发指南

### 创建新插件

#### 步骤 1：规划插件功能

确定插件需要：
- 监听哪些生命周期事件？
- 需要访问哪些主程序组件？
- 是否需要与其他插件通信？
- 是否需要配置文件？

#### 步骤 2：创建目录结构

```bash
cd src/plugins
mkdir my_feature_plugin
cd my_feature_plugin
touch manifest.yaml plugin.py
```

#### 步骤 3：编写 manifest.yaml

```yaml
name: "my_feature_plugin"
author: "Your Name"
version: "1.0.0"
description: "实现XXX功能的插件"
entry: "plugin.MyFeaturePlugin"
```

#### 步骤 4：实现插件类

``` python
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application import Application

class MyFeaturePlugin(Plugin):
    app: "Application"
    
    def __init__(self):
        super().__init__()
        # 初始化插件状态
        self.data = {}
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        # 保存应用实例引用
        self.app = app
    
    @registry.on_ready()
    def on_ready(self):
        # 执行初始化逻辑
        print(f"插件 {self.info.name} 已就绪")
    
    def deinit(self):
        # 清理资源
        self.data.clear()
        print("插件已卸载")
```

### manifest.yaml 配置

#### 必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 插件唯一标识符 | `"system_info_plugin"` |
| `author` | string | 作者名称 | `"慕色寒枝"` |
| `version` | string | 语义化版本号 | `"1.0.0"` |
| `description` | string | 插件功能描述 | "将系统信息注入到上下文中" |
| `entry` | string | 入口类路径（模块.类名） | `"plugin.SystemInfoPlugin"` |

#### 示例配置

```
# 基础插件
name: "skill_plugin"
author: "慕色寒枝"
version: "1.0.0"
description: "添加Agent Skills支持"
entry: "plugin.SkillPlugin"

# MCP集成插件
name: "mcp_plugin"
author: "慕色寒枝"
version: "1.0.0"
description: "添加MCP支持"
entry: "plugin.MCPPlugin"
```

### 编写插件代码

#### 基本模板

``` python
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from src.components.llm.message_state import MessageState
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application import Application

class MyPlugin(Plugin):
    """插件类文档字符串"""
    
    app: "Application"  # 类型注解，便于IDE提示
    
    def __init__(self):
        """插件构造函数"""
        super().__init__()
        # 初始化插件私有变量
        self.config = {}
        self.cache = {}
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        """应用初始化前回调"""
        self.app = app
        # 加载配置文件
        self._load_config()
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        """消息发送前回调"""
        # 注入额外信息
        state.append_dyn(self._get_context())
    
    @registry.on_ready()
    def on_ready(self):
        """应用就绪回调"""
        print(f"插件 '{self.info.name}' v{self.info.version} 已加载")
    
    def deinit(self):
        """插件卸载回调"""
        # 清理资源
        self.cache.clear()
    
    def _load_config(self):
        """加载配置的辅助方法"""
        pass
    
    def _get_context(self) -> str:
        """获取上下文信息的辅助方法"""
        return ""
```

### 使用 Hook 装饰器

#### 单个 Hook

``` python
@registry.on_ready()
def on_ready(self):
    print("就绪")
```

#### 多个 Hook

``` python
@registry.on_app_before_initialize()
def on_init_before(self, app: "Application"):
    self.app = app

@registry.on_app_after_initialized()
def on_init_after(self):
    print("初始化完成")

@registry.on_message_before_send()
def on_send_before(self, state: MessageState):
    state.append_dyn("前置处理")

@registry.on_message_after_sended()
def on_send_after(self, state: MessageState):
    print("消息已发送")
```

#### 指定执行顺序

``` python
# 在其他插件之前执行
@registry.on_message_before_send(timing="before")
def early_hook(self, state: MessageState):
    state.append_dyn("[早期] ")

# 在其他插件之后执行
@registry.on_message_before_send(timing="after")
def late_hook(self, state: MessageState):
    state.append_dyn(" [晚期]")
```

---

## 高级用法

### 插件间通信

插件可以通过 `emit()` 方法进行通信：

#### 发送方

``` python
class SenderPlugin(Plugin):
    def some_method(self):
        # 调用其他插件的方法
        result = self.emit("receiver_plugin", "command_name", {
            "param1": "value1",
            "param2": 123
        })
        print(f"接收方返回: {result}")
```

#### 接收方

``` python
class ReceiverPlugin(Plugin):
    def emit(self, name: str, arguments: dict):
        """
        处理来自其他插件的调用
        
        :param name: 命令名称
        :param arguments: 参数字典
        :return: 任意类型的返回值
        """
        if name == "command_name":
            param1 = arguments.get("param1")
            param2 = arguments.get("param2")
            return f"收到: {param1}, {param2}"
        return None
```

#### 通过 PluginManager 调用

``` python
# 在插件中访问插件管理器
result = self.app.plugin_manager.emit(
    "target_plugin_name",
    "command_name",
    {"key": "value"}
)
```

### 访问主程序

#### 方式一：通过 Application 实例

在 `on_app_before_initialize` Hook 中可以获取 `Application` 实例：

```
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application import Application

class MyPlugin(Plugin):
    app: "Application"
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
        
        # 访问 LLM 客户端
        llm_client = app.llm_client
        
        # 访问 IPC 服务器
        ipc_server = app.ipc_server
        
        # 访问插件管理器
        plugin_manager = app.plugin_manager
        
        # 访问线程池
        thread_executor = app.thread_executor
        
        # 访问事件循环
        event_loop = app.event_loop
```

#### 方式二：通过应用程序上下文对象

除了直接访问 `Application` 实例外，还可以通过**应用程序上下文对象**获取以下全局资源：

- **主线程异步事件循环**：用于创建和管理异步任务
- **程序配置**：访问 `app_config.yaml` 中的配置信息
- **启动参数**：获取命令行传入的启动参数（如 `ipc_uri`）

这种方式提供了更统一的资源访问接口，推荐在需要访问全局配置或启动参数时使用。

**示例**：

```python
from src.core import app_context

class ContextPlugin(Plugin):
    @registry.on_ready()
    def on_ready(self):
        # 访问启动参数
        ipc_uri = app_context.launch_args.get("ipc_uri")
        
        # 访问程序配置
        system_config = app_context.app_config["system"]
        
        # 访问事件循环
        event_loop = app_context.event_loop
        
        print(f"IPC URI: {ipc_uri}")
        print(f"系统配置: {system_config}")
```

**注意**：
- `app_context.launch_args` 包含所有命令行启动参数
- `app_context.app_config` 包含从 `app_config.yaml` 加载的完整配置
- `app_context.event_loop` 是主线程的异步事件循环
- 如果 `ipc_uri` 未提供，`launch_args.get("ipc_uri")` 将返回 `None`，系统会使用配置文件中的默认值

#### 调用 LLM

```
from src.components.llm.message_state import MessageState

@registry.on_message_before_send()
def on_message_before_send(self, state: MessageState):
    # 创建新的消息状态
    new_state = self.app.llm_client.create_state({
        "role": "user",
        "content": [{"type": "text", "text": "你好"}]
    }, stream=True)
    
    # 流式响应
    async for chunk in self.app.llm_client.stream_response(new_state):
        print(chunk.choices[0].delta.content, end="")
    
    # 非流式响应
    completion = await self.app.llm_client.non_stream_response(new_state)
    print(completion.choices[0].message.content)
```

### 异步编程

插件完全支持 asyncio 异步编程：

#### 异步任务

```
import asyncio

class AsyncPlugin(Plugin):
    event_loop: asyncio.AbstractEventLoop
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.event_loop = app.event_loop
    
    @registry.on_ready()
    def on_ready(self):
        # 创建异步任务
        self.event_loop.create_task(self.background_task())
    
    async def background_task(self):
        """后台异步任务"""
        while True:
            await asyncio.sleep(60)  # 每分钟执行一次
            print("定时任务执行")
```

#### 异步事件

```
class EventPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.ready_event = asyncio.Event()
    
    @registry.on_ready()
    def on_ready(self):
        self.ready_event.set()
    
    async def wait_for_ready(self):
        await self.ready_event.wait()
        print("应用已就绪")
```

#### 在线程池中执行

```
from concurrent.futures import ThreadPoolExecutor

class ThreadPlugin(Plugin):
    app: "Application"
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        # 在线程池中执行 CPU 密集型任务
        future = self.app.thread_executor.submit(self.heavy_computation)
        result = future.result()
        state.append_dyn(f"计算结果: {result}")
    
    def heavy_computation(self):
        """CPU 密集型计算"""
        total = sum(range(1000000))
        return total
```

---

## 最佳实践

### 1. 错误处理

始终使用 try-except 包裹可能失败的代码：

```
@registry.on_message_before_send()
def on_message_before_send(self, state: MessageState):
    try:
        data = self.fetch_external_api()
        state.append_dyn(data)
    except Exception as e:
        # 记录错误但不中断插件执行
        print(f"插件错误: {e}")
```

### 2. 日志记录

使用项目的日志系统：

```
from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)

class MyPlugin(Plugin):
    @registry.on_ready()
    def on_ready(self):
        logger.info(f"插件 {self.info.name} 已加载")
        logger.debug("调试信息")
        logger.error("错误信息", exc_info=True)
```

### 3. 资源清理

在 `deinit()` 中清理所有资源：

```
def deinit(self):
    """插件卸载时清理资源"""
    # 关闭文件句柄
    if hasattr(self, 'file_handle'):
        self.file_handle.close()
    
    # 清空缓存
    self.cache.clear()
    
    # 取消异步任务
    if hasattr(self, 'task'):
        self.task.cancel()
    
    logger.info(f"插件 {self.info.name} 已卸载")
```

### 4. 避免递归调用

在 `on_llm_response` Hook 中不要直接调用 `app.send_message()`：

```
# ❌ 错误做法
@registry.on_llm_response()
def on_llm_response(self, chat_completion):
    self.app.send_message("新消息")  # 可能导致无限递归

# ✅ 正确做法
@registry.on_llm_response()
def on_llm_response(self, chat_completion):
    # 仅处理响应数据，不触发新的消息发送
    self.process_response(chat_completion)
```

### 5. 类型注解

为所有方法和属性添加类型注解：

```
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application import Application

class MyPlugin(Plugin):
    app: "Application"  # 类型注解
    cache: dict[str, str]  # 类型注解
    
    def process_data(self, data: str) -> dict:
        """处理数据
        
        :param data: 输入数据
        :return: 处理结果
        """
        return {"result": data}
```

### 6. 配置管理（可选）

**重要说明**：框架本身不提供统一的配置文件管理机制，插件开发者可以根据需要自行实现配置加载逻辑。

以下是一个使用 YAML 文件管理插件配置的示例（需要确保 `PyYAML` 库已安装）：

```python
import pathlib
import yaml

class ConfigPlugin(Plugin):
    def __init__(self):
        super().__init__()
        # 插件开发者自行定义配置文件路径和加载逻辑
        config_path = pathlib.Path(__file__).parent / "config.yaml"
        self.config = self._load_config(config_path)
    
    @staticmethod
    def _load_config(config_path: pathlib.Path) -> dict:
        """
        自定义配置加载方法
        
        :param config_path: 配置文件路径
        :return: 配置字典
        """
        if not config_path.exists():
            return {"default_key": "default_value"}
        
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
```

**其他配置格式选择**：
- **JSON**：使用内置的 `json` 模块
- **TOML**：使用 Python 3.11+ 的 `tomllib` 或第三方库 `tomli`
- **环境变量**：使用 `os.environ` 或 `python-dotenv`
- **应用程序上下文**：通过 `app_context.app_config` 访问全局配置

**建议**：
- 简单配置可直接硬编码在插件中
- 复杂配置可使用上述任一格式
- 敏感信息（如 API Key）建议使用环境变量

### 7. 命名冲突检测

插件名称必须唯一，系统会自动检测冲突：

```
# manifest.yaml
name: "unique_plugin_name"  # 确保全局唯一
```

### 8. 文档字符串

为所有公共方法添加文档字符串：

```
def fetch_data(self, url: str, timeout: int = 10) -> dict:
    """从外部 API 获取数据
    
    :param url: API 地址
    :param timeout: 超时时间（秒）
    :return: 响应数据字典
    :raises requests.exceptions.Timeout: 请求超时
    """
    pass
```

---

## 示例插件参考

为了帮助您快速上手，项目中已经提供了多个完整的插件示例。建议您直接查看这些示例代码来学习插件开发的最佳实践。

### 现有插件列表

在 `src/plugins/` 目录下，您可以找到以下示例插件：

1. **system_info_plugin** - 系统信息注入插件
   - 📁 位置：`src/plugins/system_info_plugin/`
   - 📝 功能：将系统时间、操作系统等信息注入到对话上下文
   - 🎯 特点：简单易懂，适合初学者

2. **cli_plugin** - 命令行交互插件
   - 📁 位置：`src/plugins/cli_plugin/`
   - 📝 功能：提供命令行 CLI 界面，支持流式输出
   - 🎯 特点：展示了异步编程、事件处理、LLM 响应处理

3. **mcp_plugin** - MCP 集成插件
   - 📁 位置：`src/plugins/mcp_plugin/`
   - 📝 功能：集成 Model Context Protocol 支持
   - 🎯 特点：展示了配置文件管理、复杂业务逻辑、插件间通信

4. **skill_plugin** - Agent Skills 支持插件
   - 📁 位置：`src/plugins/skill_plugin/`
   - 📝 功能：添加 Agent Skills 能力支持
   - 🎯 特点：展示了外部服务集成、动态数据注入

### 如何学习

**推荐学习路径**：

1. **初学者**：从 `system_info_plugin` 开始
   ```bash
   # 查看插件结构
   ls src/plugins/system_info_plugin/
   
   # 阅读源码
   cat src/plugins/system_info_plugin/plugin.py
   cat src/plugins/system_info_plugin/manifest.yaml
   ```

2. **进阶学习**：研究 `cli_plugin`
   - 学习如何处理异步任务
   - 学习如何处理流式响应
   - 学习如何使用事件同步机制

3. **高级应用**：分析 `mcp_plugin`
   - 学习配置文件管理
   - 学习复杂的业务逻辑组织
   - 学习插件间通信机制

### 关键文件说明

每个插件都包含以下关键文件：

- **manifest.yaml**：插件元数据配置（必需）
  ```yaml
  name: "插件名称"
  author: "作者"
  version: "版本号"
  description: "功能描述"
  entry: "plugin.插件类名"
  ```

- **plugin.py**：插件主实现文件（必需）
  - 继承 `Plugin` 基类
  - 使用 `@registry` 装饰器注册 Hook
  - 实现业务逻辑

- **其他文件**：根据插件需求自行添加
  - 配置文件（如 `config.yaml`、`mcp_config.toml`）
  - 辅助模块（如 `utils/`、`types.py`）
  - 文档（如 `README.md`）

### 运行示例插件

所有放置在 `src/plugins/` 目录下且符合命名规范的插件会在应用启动时自动加载：

```bash
# 启动应用，所有插件自动加载
python main.py

# 查看日志确认插件加载情况
# 日志中会显示类似信息：
# INFO: found plugin src/plugins/system_info_plugin
# INFO: loaded plugin src/plugins/system_info_plugin
```

**提示**：通过查看这些示例插件的源代码，您可以学习到：
- ✅ 正确的插件结构和命名规范
- ✅ Hook 的实际使用方法
- ✅ 异步编程模式
- ✅ 错误处理和日志记录
- ✅ 配置管理技巧
- ✅ 与其他组件的交互方式

---

## 常见问题

### Q1: 插件没有被加载？

**检查清单**：
1. 插件目录是否以 `_plugin` 结尾？
2. 是否存在 `manifest.yaml` 文件？
3. `manifest.yaml` 中的 `entry` 路径是否正确？
4. 插件类是否正确继承了 `Plugin` 基类？
5. 查看日志是否有加载错误信息

### Q2: Hook 没有触发？

**可能原因**：
1. Hook 装饰器使用错误，确保使用 `@registry.on_xxx()`
2. 方法签名不正确，检查参数类型
3. 插件的 `enable` 属性被设置为 `False`
4. Hook 名称拼写错误

### Q3: 如何调试插件？

**方法 1：使用日志**
```
from src.core.logger.logger import LogCreator
logger = LogCreator.instance.create(__name__)

@registry.on_ready()
def on_ready(self):
    logger.debug(f"插件状态: {self.some_variable}")
```

**方法 2：打印调试**
```
@registry.on_message_before_send()
def on_message_before_send(self, state: MessageState):
    print(f"[DEBUG] state.messages: {state.messages}")
```

**方法 3：异常追踪**
```
try:
    risky_operation()
except Exception as e:
    logger.error(f"错误详情: {e}", exc_info=True)  # exc_info=True 会打印堆栈跟踪
```

### Q4: 插件之间如何共享数据？

**方法 1：通过 emit 通信**
```
# 插件 A
data = self.app.plugin_manager.emit("plugin_b", "get_data", {})

# 插件 B
def emit(self, name: str, arguments: dict):
    if name == "get_data":
        return self.shared_data
```

**方法 2：通过 Application 实例**
```
# 在插件中存储共享数据
self.app.custom_shared_data = {"key": "value"}

# 在其他插件中读取
data = self.app.custom_shared_data
```

### Q5: 如何处理异步操作？

**使用事件循环**：
```
@registry.on_app_before_initialize()
def on_app_before_initialize(self, app: "Application"):
    self.event_loop = app.event_loop

@registry.on_ready()
def on_ready(self):
    # 创建异步任务
    self.event_loop.create_task(self.async_operation())

async def async_operation(self):
    await asyncio.sleep(1)
    print("异步操作完成")
```

### Q6: 插件性能优化建议？

1. **避免阻塞操作**：I/O 操作使用异步，CPU 密集型使用线程池
2. **缓存频繁访问的数据**：
   ``` python
   def __init__(self):
       super().__init__()
       self.cache = {}
   
   def get_data(self, key: str):
       if key not in self.cache:
           self.cache[key] = self.fetch_data(key)
       return self.cache[key]
   ```
3. **延迟初始化**：不在 `__init__` 中执行耗时操作
4. **限制 Hook 频率**：避免在每个消息中都执行重计算

### Q7: 如何发布插件？

1. 确保插件目录结构完整
2. 编写 README.md 说明文档
3. 添加示例配置和使用说明
4. 测试插件在不同场景下的表现
5. 打包为 ZIP 或通过 Git 仓库分发

---

## 附录

### Hook 执行顺序

对于同一个 Hook，执行顺序如下：

1. **IPC 通信前阶段**：所有 `timing="before"` 的 Hook（按插件加载顺序依次执行）
2. **IPC 通信**：执行核心的 IPC 消息发送/接收操作
3. **IPC 通信后阶段**：所有 `timing="after"` 的 Hook（按插件加载顺序依次执行）

**示例流程**（以 `on_message_before_send` 为例）：

```
用户发送消息
    ↓
[before] Plugin A 的 on_message_before_send (timing="before")
    ↓
[before] Plugin B 的 on_message_before_send (timing="before")
    ↓
IPC 发送消息到服务端
    ↓
[after]  Plugin C 的 on_message_before_send (timing="after")
    ↓
[after]  Plugin D 的 on_message_before_send (timing="after")
    ↓
消息处理完成
```

这种设计允许插件在 IPC 通信的不同阶段进行干预，实现更灵活的控制逻辑。

### 插件加载流程

```
1. 扫描 src/plugins/ 目录
2. 查找以 _plugin 结尾的子目录
3. 读取 manifest.yaml
4. 导入入口模块
5. 实例化插件类
6. 扫描并注册 Hook
7. 存储到插件管理器
```

### 相关资源

- **项目源码**：`src/plugins/` 目录下的示例插件
- **核心文件**：
  - `src/plugins/plugin.py` - Plugin 基类定义
  - `src/plugins/hook_registry.py` - Hook 装饰器
  - `src/components/plugin_manager/plugin_manager.py` - 插件管理器
  - `src/types/lifecycle_hooks.py` - Hook 类型定义
  - `src/core/app_context.py` - 应用程序上下文对象（访问全局配置和启动参数）
  
- **重要概念**：
  - **Application 实例**：通过 `on_app_before_initialize` Hook 获取，提供对核心组件的访问
  - **应用程序上下文（app_context）**：提供对事件循环、程序配置、启动参数的统一访问接口
  - **IPC timing 参数**：控制 Hook 在 IPC 通信之前或之后执行

### 更新日志

- **v1.0.0** (2026-05-10)
  - 初始版本
  - 支持 7 个生命周期 Hook
  - 支持插件间通信
  - 完整的异步支持

---

**祝开发愉快！** 🚀

如有问题，请查看项目日志文件或联系维护团队。
