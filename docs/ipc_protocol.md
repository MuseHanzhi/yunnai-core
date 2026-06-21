# IPC 协议文档

## 协议概述

IPC 协议是基于 WebSocket 的 JSON 文本通信协议，用于进程间双向通信。协议支持方法调用、事件推送、心跳检测等功能。

## 传输方式

- **传输层**：WebSocket (TCP)
- **数据格式**：JSON 文本
- **连接模式**：全双工

## 基础协议

所有消息都继承自 `BaseProtocol`：

```json
{
    "id": "消息唯一ID",
    "timestamp": 1719000000000,
    "type": "消息类型"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 消息唯一标识符 |
| `timestamp` | `integer` | 毫秒级时间戳 |
| `type` | `string` | 消息类型 |

## 消息类型

### 1. invoke-request（方法调用请求）

客户端请求服务器执行某个方法。

```json
{
    "id": "req-001",
    "timestamp": 1719000000000,
    "type": "invoke-request",
    "method": "method_name",
    "arguments": {
        "key": "value"
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `method` | `string` | 要调用的方法名 |
| `arguments` | `object` | 方法参数 |

**响应**：服务器返回 `invoke-response` 消息

---

### 2. invoke-response（方法调用响应）

服务器返回方法执行结果。

```json
{
    "id": "req-001",
    "timestamp": 1719000000000,
    "type": "invoke-response",
    "code": 0,
    "message": "success",
    "result": {
        "key": "value"
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `integer` | 状态码，0 表示成功 |
| `message` | `string` | 状态信息 |
| `result` | `any` | 方法返回值 |

**code 定义**：

| 值 | 说明 |
|------|------|
| `0` | 成功 |
| `1` | 调用异常 |
| `-1` | 其他错误 |

---

### 3. event（事件推送）

单向事件通知，发送后不等待响应。

```json
{
    "id": "evt-001",
    "timestamp": 1719000000000,
    "type": "event",
    "name": "event_name",
    "arguments": {
        "key": "value"
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 事件名称 |
| `arguments` | `object` | 事件参数 |

---

### 4. error（协议错误）

协议层错误通知。

```json
{
    "id": "req-001",
    "timestamp": 1719000000000,
    "type": "error",
    "code": 400,
    "message": "Invalid request format"
}
```

**code 定义**：

| 值 | 说明 |
|------|------|
| `400` | 无效的协议包 |
| `404` | 未找到方法处理程序 |
| `500` | 服务器内部错误 |

---

### 5. heartbeat（心跳）

用于保活检测。

```json
{
    "id": "",
    "timestamp": 1719000000000,
    "type": "heartbeat",
    "method": "ping"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `method` | `string` | `ping` 或 `pong` |

**机制**：
- 客户端发送 `ping`
- 服务器响应 `pong`
- 发送间隔：5 秒
- 超时时间：5 秒

---

## 通信流程

### 方法调用流程

```
Client                          Server
   |                               |
   |--- invoke-request ----------->|
   |    (method: "query")          |
   |                               |--- 处理请求
   |                               |
   |<-- invoke-response -----------|
   |    (code: 0, result: ...)     |
   |                               |
```

### 事件推送流程

```
Client                          Server
   |                               |
   |--- event --------------------->|
   |    (name: "on_message")        |
   |                               |
   |    (无需响应)                  |
```

### 心跳流程

```
Client                          Server
   |                               |
   |--- heartbeat (ping) --------->|
   |                               |
   |<-- heartbeat (pong) ----------|
   |                               |
```

## 错误处理

| 错误场景 | 返回 |
|----------|------|
| JSON 格式无效 | `error` with code 400 |
| 缺少必需字段 | `error` with code 400 |
| 方法不存在 | `error` with code 404 |
| 方法执行异常 | `invoke-response` with code 1 |

## WebSocket 消息示例

**方法调用**：
```json
{"id":"a1b2c3d4","timestamp":1719000000000,"type":"invoke-request","method":"get_user","arguments":{"user_id":123}}
```

**响应**：
```json
{"id":"a1b2c3d4","timestamp":1719000000000,"type":"invoke-response","code":0,"message":"success","result":{"name":"Alice"}}
```

**事件**：
```json
{"id":"e5f6g7h8","timestamp":1719000000000,"type":"event","name":"on_ready","arguments":{}}
```

**心跳**：
```json
{"id":"","timestamp":1719000000000,"type":"heartbeat","method":"ping"}
```

## 重连机制

当心跳超时时，客户端自动重连：

1. 发送 `ping`，等待 `pong`
2. 若 5 秒内未收到 `pong`，判定超时
3. 关闭当前连接，尝试重连
4. 最多重试 3 次，间隔 3 秒
5. 重连成功后继续通信
