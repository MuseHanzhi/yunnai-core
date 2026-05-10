# yunnai-core IPC 交互与连接文档

## 目录

- [概述](#概述)
- [架构设计](#架构设计)
  - [通信模式](#通信模式)
  - [消息协议](#消息协议)
  - [传输层](#传输层)
- [快速开始](#快速开始)
  - [配置 IPC](#配置-ipc)
  - [启动应用](#启动应用)
  - [客户端连接示例](#客户端连接示例)
- [核心概念](#核心概念)
  - [Event（事件）](#event事件)
  - [Invoke（调用）](#invoke调用)
  - [生命周期管理](#生命周期管理)
- [服务端 API](#服务端-api)
  - [初始化与连接](#初始化与连接)
  - [事件处理](#事件处理)
  - [Invoke 注册](#invoke-注册)
  - [发送消息](#发送消息)
- [客户端开发指南](#客户端开发指南)
  - [连接服务器](#连接服务器)
  - [监听事件](#监听事件)
  - [注册 Invoke 处理器](#注册-invoke-处理器)
  - [发送事件](#发送事件)
  - [调用 Invoke](#调用-invoke)
- [消息协议详解](#消息协议详解)
  - [Event 消息格式](#event-消息格式)
  - [Invoke Request 消息格式](#invoke-request-消息格式)
  - [Invoke Response 消息格式](#invoke-response-消息格式)
- [高级用法](#高级用法)
  - [错误处理](#错误处理)
  - [超时控制](#超时控制)
  - [心跳机制](#心跳机制)
  - [重连机制](#重连机制)
- [实际应用示例](#实际应用示例)
  - [示例 1：发送消息到智能体](#示例-1发送消息到智能体)
  - [示例 2：接收 LLM 响应](#示例-2接收-llm-响应)
  - [示例 3：远程关闭应用](#示例-3远程关闭应用)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

yunnai-core 的 **IPC（Inter-Process Communication，进程间通信）** 系统基于 **WebSocket** 协议实现，为外部客户端提供了一种与智能体核心进行实时交互的标准方式。

### 核心特性

- 🔄 **双通信模式**：支持 Event（单向事件）和 Invoke（双向请求/响应）
- ⚡ **异步处理**：完全基于 asyncio，支持高并发 I/O 操作
- 🔌 **灵活传输**：基于 WebSocket，可跨网络、跨语言通信
- ⏱️ **超时控制**：Invoke 调用自带超时机制（默认 10 秒）
- 💓 **心跳检测**：自动发送 ping 保持连接活跃
- 🔁 **自动重连**：支持配置化的断线重连策略
- 🛡️ **错误隔离**：单个消息处理失败不影响其他消息

### 应用场景

- **Web 前端集成**：通过 WebSocket 连接智能体，构建聊天界面
- **移动端 App**：实时接收智能体响应，推送通知
- **第三方服务**：远程调用智能体能力，集成到工作流
- **监控系统**：监听智能体状态，收集运行指标
- **自动化脚本**：批量发送消息，执行定时任务

---

## 架构设计

### 通信模式

IPC 系统支持两种通信模式：

#### 1. Event（事件模式）

**特点**：单向通信，无需等待响应

```
客户端                          服务端
  | --[Event: send_message]-->   |
  |                              | 处理事件
  |                              | 触发插件 Hook
  |                              | 发送消息到 LLM
```

**适用场景**：
- 发送消息到智能体
- 触发某个动作（如关闭应用）
- 通知状态变更

#### 2. Invoke（调用模式）

**特点**：双向通信，客户端发送请求并等待服务端响应

```
客户端                          服务端
  | --[Invoke: get_status]-->    |
  |                              | 执行处理函数
  | <--[Response: {data}]-----   | 返回结果
  | 解析响应                      |
```

**适用场景**：
- 查询智能体状态
- 获取配置信息
- 执行需要返回值的操作

### 消息协议

所有 IPC 消息均采用 **JSON** 格式编码，通过 WebSocket 以 **二进制帧** 传输。

消息类型由 `type` 字段区分：

| 类型 | 字段值 | 方向 | 说明 |
|------|--------|------|------|
| Event | `"event"` | 客户端 → 服务端 | 单向事件通知 |
| Invoke Request | `"invoke-req"` | 客户端 → 服务端 | 调用请求 |
| Invoke Response | `"invoke-res"` | 服务端 → 客户端 | 调用响应 |

### 传输层

IPC 系统采用分层架构：

```
┌─────────────────────────────────┐
│      IPCServer (业务层)          │
│  - 事件路由                       │
│  - Invoke 会话管理               │
│  - 超时控制                       │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   BaseTransport (抽象层)         │
│  - connect()                     │
│  - disconnect()                  │
│  - send()                        │
│  - listen()                      │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│ WebSocketTransport (实现层)      │
│  - websockets 库封装             │
│  - 连接管理                       │
│  - 心跳维护                       │
└─────────────────────────────────┘
```

当前仅实现了 **WebSocketTransport**，未来可扩展其他传输协议（如 TCP、Unix Socket）。

---

## 快速开始

### 配置 IPC

在 `app_config.yaml` 中配置 IPC 参数：

```yaml
system:
  ipc:
    enable: false              # 是否启用 IPC（启动时可通过命令行参数覆盖）
    uri: "ws://192.168.1.105:8866"  # WebSocket 服务器地址
    reconnect:
      enable: true             # 是否启用自动重连
      retry_interval: 5        # 重试间隔（秒）
      max_retry: 3             # 最大重试次数
```

**注意**：
- `enable: false` 时，IPC 服务器不会自动启动
- 可通过命令行参数 `ipc_uri` 覆盖配置文件中的 URI

### 启动应用

#### 方式 1：使用配置文件

```bash
# IPC 不会自动启动（enable: false）
python main.py
```

#### 方式 2：指定 IPC URI（推荐）

```bash
# 启动 IPC 并连接到指定地址
python main.py ipc_uri=ws://localhost:6600
```

**参数说明**：
- `ipc_uri`：WebSocket 服务器地址（可选）
- 如果不提供，系统将检查配置文件中的 `ipc.enable` 和 `ipc.uri`

### 客户端连接示例

以下是一个简单的 Python 客户端示例：

```python
import asyncio
import websockets
import json

async def client_example():
    uri = "ws://localhost:6600"
    
    async with websockets.connect(uri) as websocket:
        print("已连接到 yunnai-core")
        
        # 发送事件：向智能体发送消息
        event = {
            "name": "send_message",
            "type": "event",
            "arguments": {
                "message": "你好，请介绍一下自己",
                "model_name": "qwen3.6-plus",
                "stream": True
            }
        }
        await websocket.send(json.dumps(event))
        
        # 接收响应
        async for message in websocket:
            data = json.loads(message)
            print(f"收到: {data}")

asyncio.run(client_example())
```

---

## 核心概念

### Event（事件）

**Event** 是单向通信模式，客户端发送事件后无需等待响应。

#### 工作流程

1. 客户端发送 Event 消息
2. 服务端解析消息，查找对应的事件处理器
3. 执行处理器（同步或异步）
4. 处理器内部可能触发其他逻辑（如发送消息到 LLM）

#### 典型事件

| 事件名称 | 参数 | 说明 |
|---------|------|------|
| `send_message` | `message`, `model_name`, `stream`, `request_id` | 发送消息到智能体 |
| `close_app` | 无 | 关闭应用程序 |
| `ready` | `mcp_list`, `client_info` | 客户端就绪通知 |
| `ping` | 无 | 心跳检测 |

### Invoke（调用）

**Invoke** 是双向通信模式，客户端发送请求并等待服务端响应。

#### 工作流程

1. 客户端生成唯一的 `invoke_id`
2. 发送 Invoke Request 消息
3. 服务端创建 Future 对象，设置超时定时器
4. 服务端执行对应的处理函数
5. 服务端返回 Invoke Response 消息
6. 客户端接收响应，解析数据

#### 超时机制

- **默认超时**：10 秒（10000 毫秒）
- **超时行为**：Future 抛出 `TimeoutError`
- **会话清理**：超时后自动清理会话资源

### 生命周期管理

IPC 连接的生命周期包括以下阶段：

```
创建 IPCServer
    ↓
调用 start() 建立连接
    ↓
触发 on_ipc_ready 回调
    ↓
启动心跳任务（每 0.5 秒发送 ping）
    ↓
开始监听消息（listen）
    ↓
处理接收到的消息
    ↓
连接断开或调用 close()
    ↓
清理所有待处理的 Invoke 会话
    ↓
触发 on_ipc_error 或正常关闭
```

---

## 服务端 API

### 初始化与连接

#### 创建 IPCServer

```python
from src.components.ipc.ipc import IPCServer
import asyncio

# 创建事件循环
event_loop = asyncio.new_event_loop()

# 创建 IPC 服务器
ipc_server = IPCServer(
    uri="ws://localhost:6600",
    event_loop=event_loop
)
```

#### 配置连接回调

```python
def on_ready():
    print("IPC 连接已建立")

def on_error(error: Exception):
    print(f"IPC 连接错误: {error}")

ipc_server.on_ipc_ready = on_ready
ipc_server.on_ipc_error = on_error
```

#### 启动服务器

```python
# 异步启动
await ipc_server.start()

# 或在事件循环中创建任务
event_loop.create_task(ipc_server.start())
```

#### 关闭服务器

```python
await ipc_server.close()
```

### 事件处理

#### 注册事件处理器

```python
def handle_send_message(params: dict):
    """处理 send_message 事件"""
    message = params.get("message")
    model_name = params.get("model_name", "qwen3.6-plus")
    stream = params.get("stream", True)
    
    print(f"收到消息: {message}")
    # 执行业务逻辑...

# 注册处理器
ipc_server.on("send_message", handle_send_message)
```

#### 移除事件处理器

```python
# 移除特定处理器
ipc_server.off("send_message", handle_send_message)

# 移除该事件的所有处理器
ipc_server.off("send_message")
```

### Invoke 注册

#### 注册 Invoke 处理器

```python
def handle_get_status(params: dict) -> dict:
    """处理 get_status 调用"""
    return {
        "status": "running",
        "connected_clients": 1,
        "uptime": 3600
    }

# 注册处理器（支持同步和异步函数）
ipc_server.handle("get_status", handle_get_status)

# 异步处理器示例
async def handle_async_query(params: dict):
    await asyncio.sleep(1)  # 模拟异步操作
    return {"result": "async data"}

ipc_server.handle("async_query", handle_async_query)
```

#### 移除 Invoke 处理器

```python
ipc_server.unhandle("get_status")
```

### 发送消息

#### 发送 Event

```python
# 向客户端发送事件
await ipc_server.emit(
    "llm_response",           # 事件名称
    chat_completion={...},    # 事件参数
    request_id="req_123"
)
```

#### 常用事件

```python
# 发送 LLM 响应（流式）
await ipc_server.emit(
    "llm_response",
    chat_completion=chunk.model_dump(),
    request_id=request_id
)

# 发送应用即将关闭通知
await ipc_server.emit("on_app_will_close")

# 发送 ping 心跳
await ipc_server.emit("ping")
```

---

## 客户端开发指南

### 连接服务器

#### Python 客户端

```python
import asyncio
import websockets
import json

async def connect_ipc():
    uri = "ws://localhost:6600"
    
    try:
        async with websockets.connect(uri) as ws:
            print("连接成功")
            
            # 开始监听消息
            async for message in ws:
                data = json.loads(message)
                handle_message(data)
                
    except websockets.ConnectionClosed:
        print("连接已关闭")
    except Exception as e:
        print(f"连接失败: {e}")

def handle_message(data: dict):
    """处理接收到的消息"""
    msg_type = data.get("type")
    
    if msg_type == "event":
        handle_event(data)
    elif msg_type == "invoke-res":
        handle_invoke_response(data)

asyncio.run(connect_ipc())
```

#### JavaScript 客户端

```javascript
const ws = new WebSocket('ws://localhost:6600');

ws.onopen = () => {
    console.log('连接成功');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
};

ws.onerror = (error) => {
    console.error('连接错误:', error);
};

ws.onclose = () => {
    console.log('连接已关闭');
};

function handleMessage(data) {
    if (data.type === 'event') {
        handleEvent(data);
    } else if (data.type === 'invoke-res') {
        handleInvokeResponse(data);
    }
}
```

### 监听事件

#### 注册事件处理器

```python
def handle_llm_response(params: dict):
    """处理 LLM 响应事件"""
    chat_completion = params.get("chat_completion")
    request_id = params.get("request_id")
    
    if chat_completion:
        # 处理流式响应
        choices = chat_completion.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            content = delta.get("content", "")
            print(content, end="", flush=True)

# 注册处理器
ipc_server.on("llm_response", handle_llm_response)
```

#### 多个处理器

```python
# 可以为同一事件注册多个处理器
ipc_server.on("llm_response", handler1)
ipc_server.on("llm_response", handler2)

# 按注册顺序依次执行
```

### 注册 Invoke 处理器

#### 同步处理器

```python
def handle_get_config(params: dict) -> dict:
    """返回配置信息"""
    return {
        "model": "qwen3.6-plus",
        "stream": True,
        "temperature": 0.7
    }

ipc_server.handle("get_config", handle_get_config)
```

#### 异步处理器

```python
async def handle_fetch_data(params: dict):
    """异步获取数据"""
    url = params.get("url")
    
    # 模拟 HTTP 请求
    await asyncio.sleep(1)
    
    return {
        "status": "success",
        "data": "fetched content"
    }

ipc_server.handle("fetch_data", handle_fetch_data)
```

#### 错误处理

```python
def handle_risky_operation(params: dict):
    try:
        # 可能失败的操作
        result = perform_operation(params)
        return {"success": True, "result": result}
    except Exception as e:
        # 返回错误信息
        return {"success": False, "error": str(e)}

ipc_server.handle("risky_op", handle_risky_operation)
```

### 发送事件

#### 基本用法

```python
# 发送简单事件
await ipc_server.emit("ping")

# 发送带参数的事件
await ipc_server.emit(
    "send_message",
    message="你好",
    model_name="qwen3.6-plus",
    stream=True
)
```

#### 完整示例

```python
async def send_chat_message(message: str, model: str = "qwen3.6-plus"):
    """发送聊天消息"""
    await ipc_server.emit(
        "send_message",
        message=message,
        model_name=model,
        stream=True,
        request_id=f"msg_{int(time.time())}"
    )

# 使用
await send_chat_message("请帮我写一个 Python 函数")
```

### 调用 Invoke

#### 基本用法

```python
# 调用并等待响应
try:
    result = await ipc_server.invoke(
        "get_status",
        timeout=5000  # 自定义超时时间（毫秒）
    )
    print(f"状态: {result}")
except TimeoutError:
    print("调用超时")
except Exception as e:
    print(f"调用失败: {e}")
```

#### 带参数的调用

```python
result = await ipc_server.invoke(
    "query_database",
    table="users",
    filters={"age": {"$gt": 18}},
    limit=10
)

print(f"查询结果: {result}")
```

---

## 消息协议详解

### Event 消息格式

#### 客户端 → 服务端

```json
{
    "type": "event",
    "name": "send_message",
    "arguments": {
        "message": "你好",
        "model_name": "qwen3.6-plus",
        "stream": true,
        "request_id": "msg_123456"
    }
}
```

#### 服务端 → 客户端

```json
{
    "type": "event",
    "name": "llm_response",
    "arguments": {
        "chat_completion": {
            "id": "chatcmpl-123",
            "choices": [{
                "delta": {
                    "content": "你好！"
                },
                "finish_reason": null
            }]
        },
        "request_id": "msg_123456"
    }
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值 `"event"` |
| `name` | string | ✅ | 事件名称 |
| `arguments` | object | ❌ | 事件参数（可为空对象 `{}`） |

### Invoke Request 消息格式

#### 客户端 → 服务端

```json
{
    "type": "invoke-req",
    "id": "1234567890:get_status:0",
    "name": "get_status",
    "arguments": {
        "detail": true
    }
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值 `"invoke-req"` |
| `id` | string | ✅ | 唯一标识符（格式：`timestamp:name:index`） |
| `name` | string | ✅ | 调用的方法名称 |
| `arguments` | object | ❌ | 调用参数 |

**ID 生成规则**：

```python
invoke_id = f"{time.time()}:{name}:{invoke_num}"
# 示例: "1234567890.123:get_status:0"
```

### Invoke Response 消息格式

#### 服务端 → 客户端

**成功响应**：

```json
{
    "type": "invoke-res",
    "id": "1234567890:get_status:0",
    "name": "get_status",
    "data": {
        "status": "running",
        "uptime": 3600
    },
    "exceptMessage": null
}
```

**失败响应**：

```json
{
    "type": "invoke-res",
    "id": "1234567890:get_status:0",
    "name": "get_status",
    "data": null,
    "exceptMessage": "NoHandler: 'get_status' 该invokeIPC客户端未注册"
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值 `"invoke-res"` |
| `id` | string | ✅ | 对应的请求 ID |
| `name` | string | ✅ | 调用的方法名称 |
| `data` | any | ❌ | 返回数据（成功时有值） |
| `exceptMessage` | string/null | ✅ | 错误信息（失败时有值） |

---

## 高级用法

### 错误处理

#### 服务端错误处理

```python
def safe_handler(params: dict):
    """安全的处理器，捕获所有异常"""
    try:
        result = risky_operation(params)
        return {"success": True, "data": result}
    except ValueError as e:
        logger.warning(f"参数错误: {e}")
        return {"success": False, "error": "Invalid parameters"}
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return {"success": False, "error": "Internal server error"}

ipc_server.handle("safe_op", safe_handler)
```

#### 客户端错误处理

```python
try:
    result = await ipc_server.invoke("risky_operation")
    if result.get("success"):
        print(f"成功: {result['data']}")
    else:
        print(f"失败: {result['error']}")
except TimeoutError:
    print("操作超时，请稍后重试")
except ConnectionError:
    print("连接已断开，请重新连接")
except Exception as e:
    print(f"未知错误: {e}")
```

### 超时控制

#### 自定义超时时间

```python
# 修改默认超时时间（毫秒）
ipc_server.invoke_timeout = 30000  # 30 秒

# 调用时使用自定义超时
result = await ipc_server.invoke(
    "long_running_task",
    timeout=60000  # 60 秒
)
```

#### 超时处理策略

```python
async def invoke_with_retry(name: str, max_retries: int = 3, **kwargs):
    """带重试的 Invoke 调用"""
    for attempt in range(max_retries):
        try:
            return await ipc_server.invoke(name, **kwargs)
        except TimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"第 {attempt + 1} 次尝试超时，重试...")
                await asyncio.sleep(1)
            else:
                raise
        except ConnectionError:
            logger.error("连接断开，无法重试")
            raise

# 使用
result = await invoke_with_retry("fetch_data", max_retries=3)
```

### 心跳机制

IPC 服务器自动维护心跳：

```python
async def ping(self):
    """心跳任务，每 0.5 秒发送一次 ping"""
    while True:
        await asyncio.sleep(0.5)
        await self.emit("ping")
```

**客户端心跳处理**：

```python
last_ping_time = time.time()

def handle_ping(params: dict):
    global last_ping_time
    last_ping_time = time.time()
    print("收到心跳")

ipc_server.on("ping", handle_ping)

# 检测连接健康
async def health_check():
    while True:
        await asyncio.sleep(5)
        if time.time() - last_ping_time > 10:
            print("警告：超过 10 秒未收到心跳")
            # 触发重连或其他操作
```

### 重连机制

#### 配置重连

在 `app_config.yaml` 中配置：

```yaml
system:
  ipc:
    reconnect:
      enable: true       # 启用自动重连
      retry_interval: 5  # 重试间隔（秒）
      max_retry: 3       # 最大重试次数
```

#### 手动重连

```python
async def connect_with_retry(uri: str, max_retries: int = 3):
    """带重试的连接"""
    for attempt in range(max_retries):
        try:
            ipc_server = IPCServer(uri, event_loop)
            await ipc_server.start()
            print("连接成功")
            return ipc_server
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"第 {attempt + 1} 次连接失败: {e}，重试...")
                await asyncio.sleep(5)
            else:
                logger.error("达到最大重试次数，放弃连接")
                raise

# 使用
ipc = await connect_with_retry("ws://localhost:6600", max_retries=5)
```

---

## 实际应用示例

### 示例 1：发送消息到智能体

#### 客户端代码

```python
import asyncio
import websockets
import json

async def send_message_example():
    uri = "ws://localhost:6600"
    
    async with websockets.connect(uri) as ws:
        # 构造 send_message 事件
        event = {
            "type": "event",
            "name": "send_message",
            "arguments": {
                "message": "请帮我解释一下量子计算",
                "model_name": "qwen3.6-plus",
                "stream": True,
                "request_id": "msg_001"
            }
        }
        
        # 发送事件
        await ws.send(json.dumps(event))
        print("消息已发送")
        
        # 接收 LLM 响应
        async for message in ws:
            data = json.loads(message)
            
            if data.get("name") == "llm_response":
                args = data.get("arguments", {})
                completion = args.get("chat_completion", {})
                
                # 提取文本内容
                choices = completion.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    
                    if content:
                        print(content, end="", flush=True)
                    
                    # 检查是否结束
                    finish_reason = choices[0].get("finish_reason")
                    if finish_reason == "stop":
                        print("\n[响应完成]")
                        break

asyncio.run(send_message_example())
```

#### 服务端处理

服务端自动处理 `send_message` 事件（在 `src/ipc_handlers/modules/application_module/handler.py` 中）：

```python
def send_message(self, params: Any):
    message: MessageOptions = params
    self.event_loop.create_task(self.app.send_message(
        message['message'], 
        {
            "request_id": message.get("request_id", ""),
            "model_name": message["model_name"],
            "stream": message.get("stream", True)
        }
    ))
```

### 示例 2：接收 LLM 响应

#### 注册响应处理器

```python
from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)

class ResponseCollector:
    def __init__(self):
        self.full_response = ""
        self.is_complete = False
    
    def handle_response(self, params: dict):
        """累积 LLM 响应"""
        completion = params.get("chat_completion", {})
        choices = completion.get("choices", [])
        
        if not choices:
            return
        
        choice = choices[0]
        
        # 流式响应
        if "delta" in choice:
            content = choice["delta"].get("content", "")
            if content:
                self.full_response += content
                print(content, end="", flush=True)
        
        # 检查是否完成
        if choice.get("finish_reason") == "stop":
            self.is_complete = True
            print("\n[完整响应]:", self.full_response)
            logger.info(f"响应长度: {len(self.full_response)} 字符")

# 使用
collector = ResponseCollector()
ipc_server.on("llm_response", collector.handle_response)
```

### 示例 3：远程关闭应用

#### 客户端发送关闭命令

```python
async def shutdown_app():
    uri = "ws://localhost:6600"
    
    async with websockets.connect(uri) as ws:
        # 发送关闭事件
        event = {
            "type": "event",
            "name": "close_app",
            "arguments": {}
        }
        
        await ws.send(json.dumps(event))
        print("已发送关闭命令")

asyncio.run(shutdown_app())
```

#### 服务端处理

```python
def close_app(self, params: dict):
    """关闭应用程序"""
    logger.info("收到远程关闭命令")
    self.app.exit()
```

---

## 最佳实践

### 1. 消息幂等性

确保事件处理器可以安全地重复执行：

```python
def handle_send_message(params: dict):
    """幂等的消息处理器"""
    request_id = params.get("request_id")
    
    # 检查是否已处理
    if request_id in processed_ids:
        logger.warning(f"重复的消息 ID: {request_id}")
        return
    
    processed_ids.add(request_id)
    # 处理消息...
```

### 2. 参数验证

始终验证输入参数：

```python
def validated_handler(params: dict):
    """带参数验证的处理器"""
    # 必需参数检查
    if "message" not in params:
        raise ValueError("缺少必需参数: message")
    
    message = params["message"]
    if not isinstance(message, str) or len(message) == 0:
        raise ValueError("message 必须是非空字符串")
    
    # 可选参数设置默认值
    model_name = params.get("model_name", "qwen3.6-plus")
    stream = params.get("stream", True)
    
    # 执行业务逻辑...
```

### 3. 异步友好

优先使用异步操作，避免阻塞事件循环：

```python
# ✅ 推荐：异步处理器
async def async_handler(params: dict):
    data = await fetch_external_api(params["url"])
    return data

# ❌ 避免：同步阻塞操作
def sync_handler(params: dict):
    data = requests.get(params["url"]).json()  # 阻塞事件循环
    return data
```

如果必须使用同步操作，在线程池中执行：

```python
def blocking_handler(params: dict):
    # 在线程池中执行阻塞操作
    loop = asyncio.get_event_loop()
    result = loop.run_in_executor(None, blocking_function, params)
    return result
```

### 4. 资源清理

在连接关闭时清理资源：

```python
class ResourceManager:
    def __init__(self):
        self.connections = {}
        self.timers = []
    
    def cleanup(self):
        """清理所有资源"""
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()
        
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()

# 在连接关闭时调用
ipc_server.websocket_conn.event_bind_disconnect(
    lambda: resource_manager.cleanup()
)
```

### 5. 日志记录

详细记录关键操作：

```python
from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)

def logged_handler(params: dict):
    request_id = params.get("request_id", "unknown")
    
    logger.info(f"[{request_id}] 收到请求")
    
    try:
        result = process_request(params)
        logger.info(f"[{request_id}] 处理成功")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] 处理失败: {e}", exc_info=True)
        raise
```

### 6. 错误边界

为每个处理器设置独立的错误边界：

```python
def safe_wrapper(handler_func):
    """错误包装器"""
    def wrapper(params: dict):
        try:
            return handler_func(params)
        except Exception as e:
            logger.error(f"处理器执行失败: {e}", exc_info=True)
            return {"error": str(e)}
    return wrapper

# 使用
ipc_server.handle("risky_op", safe_wrapper(risky_handler))
```

### 7. 性能优化

#### 批量处理

```python
batch_buffer = []

def batch_handler(params: dict):
    """批量收集消息"""
    batch_buffer.append(params)
    
    if len(batch_buffer) >= 10:
        process_batch(batch_buffer)
        batch_buffer.clear()
```

#### 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query: str):
    """缓存查询结果"""
    return execute_expensive_query(query)

def handle_query(params: dict):
    result = cached_query(params["query"])
    return result
```

---

## 常见问题

### Q1: 连接失败怎么办？

**检查清单**：

1. **确认服务器地址正确**
   ```bash
   # 检查配置的 URI
   cat app_config.yaml | grep uri
   ```

2. **确认服务器正在运行**
   ```bash
   # 查看进程
   ps aux | grep main.py
   
   # 查看日志
   tail -f logs/*.log
   ```

3. **测试网络连接**
   ```bash
   # 使用 wscat 工具测试
   wscat -c ws://localhost:6600
   ```

4. **检查防火墙设置**
   ```bash
   # 确认端口未被阻止
   netstat -an | grep 6600
   ```

### Q2: Invoke 调用超时？

**可能原因**：

1. **处理函数执行时间过长**
   ```python
   # 优化：使用异步操作
   async def fast_handler(params: dict):
       # 避免阻塞操作
       result = await async_operation()
       return result
   ```

2. **增加超时时间**
   ```python
   ipc_server.invoke_timeout = 30000  # 30 秒
   ```

3. **检查是否有死锁**
   ```python
   # 避免在 Handler 中调用会阻塞的操作
   ```

### Q3: 消息丢失？

**排查步骤**：

1. **检查连接状态**
   ```python
   if not ipc_server.is_connected:
       logger.error("连接已断开")
   ```

2. **启用调试日志**
   ```yaml
   logging:
     default: "debug"
   ```

3. **确认事件名称拼写正确**
   ```python
   # 大小写敏感
   ipc_server.on("llm_response", handler)  # ✅
   ipc_server.on("LLM_Response", handler)  # ❌
   ```

### Q4: 如何处理大量并发连接？

**优化建议**：

1. **使用连接池**
   ```python
   # 限制最大连接数
   MAX_CONNECTIONS = 100
   active_connections = set()
   
   def on_connect():
       if len(active_connections) >= MAX_CONNECTIONS:
           raise Exception("达到最大连接数")
       active_connections.add(connection)
   ```

2. **限流保护**
   ```python
   from asyncio import Semaphore
   
   semaphore = Semaphore(10)  # 最多 10 个并发处理
   
   async def limited_handler(params: dict):
       async with semaphore:
           return await process(params)
   ```

3. **消息队列**
   ```python
   import asyncio
   
   message_queue = asyncio.Queue(maxsize=1000)
   
   async def queue_handler(params: dict):
       await message_queue.put(params)
   
   async def worker():
       while True:
           params = await message_queue.get()
           await process(params)
           message_queue.task_done()
   ```

### Q5: 如何实现身份验证？

**方案 1：URL 参数**

```python
# 客户端连接时携带 token
uri = "ws://localhost:6600?token=abc123"

# 服务端验证
def validate_connection(headers):
    token = headers.get("token")
    if not is_valid_token(token):
        raise Exception("无效的 token")
```

**方案 2：握手消息**

```python
# 客户端发送认证消息
auth_message = {
    "type": "event",
    "name": "authenticate",
    "arguments": {
        "username": "user1",
        "password": "pass123"
    }
}

# 服务端验证
def handle_authenticate(params: dict):
    username = params.get("username")
    password = params.get("password")
    
    if not verify_credentials(username, password):
        raise Exception("认证失败")
    
    logger.info(f"用户 {username} 认证成功")
```

### Q6: 如何监控 IPC 性能？

**添加性能指标**：

```python
import time
from collections import defaultdict

class IPCMetrics:
    def __init__(self):
        self.message_count = 0
        self.invoke_count = 0
        self.avg_response_time = 0
        self.response_times = []
    
    def record_message(self):
        self.message_count += 1
    
    def record_invoke(self, duration_ms: float):
        self.invoke_count += 1
        self.response_times.append(duration_ms)
        self.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    def get_stats(self):
        return {
            "total_messages": self.message_count,
            "total_invokes": self.invoke_count,
            "avg_response_time_ms": self.avg_response_time
        }

metrics = IPCMetrics()

# 在消息处理时记录
def monitored_handler(params: dict):
    start_time = time.time()
    metrics.record_message()
    
    result = process(params)
    
    duration_ms = (time.time() - start_time) * 1000
    metrics.record_invoke(duration_ms)
    
    return result

# 定期输出统计
async def report_metrics():
    while True:
        await asyncio.sleep(60)
        logger.info(f"IPC 统计: {metrics.get_stats()}")
```

---

## 附录

### 相关资源

- **核心文件**：
  - `src/components/ipc/ipc.py` - IPC 服务器实现
  - `src/components/ipc/types.py` - 消息类型定义
  - `src/components/ipc/transports/ws_transport.py` - WebSocket 传输层
  - `src/ipc_handlers/modules/application_module/handler.py` - 应用模块处理器

- **配置文件**：
  - `app_config.yaml` - IPC 配置（system.ipc 部分）

- **示例代码**：
  - 查看 `test/` 目录中的测试用例
  - 参考现有插件中的 IPC 使用方式

### 更新日志

- **v1.0.0** (2026-05-10)
  - 初始版本
  - 支持 Event 和 Invoke 两种通信模式
  - 基于 WebSocket 的传输层
  - 自动心跳和超时控制
  - 完整的错误处理机制

---

**祝开发愉快！** 🚀

如有问题，请查看项目日志文件或联系维护团队。
