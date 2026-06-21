# IPC 通信文档

## 概述

IPC（进程间通信）组件基于 WebSocket 实现，支持请求/响应和事件发布/订阅两种模式。框架通过 IPC 与外部应用（如 WebUI）进行通信。

## 核心类

| 类 | 说明 |
|------|------|
| `IPC` | 主通信类，管理连接、消息收发 |
| `Protocols` | WebSocket 底层协议处理 |
| `IPCBase` | 抽象基类，定义接口 |

## 消息类型

| 类型 | 说明 | 用途 |
|------|------|------|
| `invoke-request` | 调用请求 | 请求远程方法调用，等待响应 |
| `invoke-response` | 调用响应 | 返回 invoke-request 的结果 |
| `event` | 事件推送 | 单向事件通知，无需响应 |
| `heartbeat` | 心跳 | 保活检测，自动重连 |
| `error` | 错误 | 协议错误通知 |

## 快速接入

### 1. 创建 IPC 连接

```python
from src.components.ipc_com.ipc import IPC

ipc = IPC("ws://192.168.1.105:8866")
```

### 2. 启动连接

```python
ipc.on_ready = lambda: print("连接就绪")
ipc.on_end = lambda: print("连接断开")

await ipc.start()
```

### 3. 注册事件处理

```python
# 普通事件（持续有效）
ipc.on("on_ready", lambda args: print(f"收到事件: {args}"))

# 一次性事件
ipc.on("once_event", handler, once=True)
```

### 4. 注册方法调用

```python
async def my_handler(args: dict):
    return {"result": "success"}

ipc.register_invoke("my_method", my_handler)
```

### 5. 发送事件

```python
await ipc.emit("event_name", {"key": "value"})
```

### 6. 调用远程方法

```python
# 同步调用，等待响应
result = await ipc.invoke("remote_method", {"arg": "value"}, timeout=10)
```

## IPC 在 Application 中的使用

```python
class Application:
    def __init__(self):
        self.ipc: IPC | None = self._create_ipc()

    @staticmethod
    def _create_ipc():
        ipc_url = app_context.launch_args.ipc_url
        if ipc_url is None:
            return None
        return IPC(ipc_url)

    async def initialize(self):
        if self.ipc:
            await self.ipc.start()
            # 注册事件处理
            self.ipc.on("llm_response", self._handle_llm_response)
```

## 生命周期钩子

| 钩子 | 说明 |
|------|------|
| `on_ready` | 连接建立时回调 |
| `on_end` | 连接断开时回调 |
| `on_connected` | WebSocket 连接成功 |
| `on_disconnected` | WebSocket 连接断开 |
| `on_error` | 发生错误时回调 |

## 异常类型

| 异常 | 说明 |
|------|------|
| `IPCConnectError` | 连接失败 |
| `IPCSendError` | 发送消息失败 |
| `InvokeTimeoutError` | 调用超时 |
| `IPCInvokeError` | 调用执行错误 |
| `IPCEventRequestError` | 事件请求错误 |
| `ACKTimeoutError` | ACK 超时 |

## 心跳机制

- 发送间隔：5 秒
- 超时时间：5 秒
- 超时后自动重连，最多 3 次

## 示例：完整客户端

```python
import asyncio
from src.components.ipc_com.ipc import IPC

async def main():
    ipc = IPC("ws://localhost:8866")

    ipc.on_ready = lambda: print("已连接")
    ipc.on("message", lambda args: print(f"收到: {args}"))

    async def handle_query(args):
        return {"status": "ok"}
    ipc.register_invoke("query", handle_query)

    try:
        await ipc.start()
    except Exception as e:
        print(f"连接失败: {e}")

asyncio.run(main())
```
