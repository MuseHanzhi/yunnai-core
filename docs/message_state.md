# MessageState 类文档

## 概述

`MessageState` 是 yunnai-core 框架中用于管理大模型对话状态的核心类。它封装了与大模型交互所需的所有上下文信息，包括消息历史、模型配置、工具列表、动态提示等，并提供了状态管理和取消机制。

## 类定义

```python
class MessageState:
    def __init__(self, model_name: str, message: Message, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `model_name` | `str` | 模型名称，用于标识使用哪个大模型 |
| `message` | `Message` | 当前消息对象 |
| `messages` | `list[ChatCompletionMessageParam]` | 历史消息列表（可选） |
| `is_stream` | `bool` | 是否使用流式响应，默认为 `True` |

## 核心属性

### data 属性

`data` 是 `MessageStateData` 类型的对象，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_stream` | `bool` | 是否流式响应 |
| `canceled` | `bool` | 是否已取消 |
| `canceller` | `str \| None` | 取消操作的发起者 |
| `cancel_reason` | `str \| None` | 取消原因 |
| `output_schema` | `OutputShema \| None` | 输出格式约束 |
| `model_name` | `str` | 模型名称 |
| `message` | `Message` | 当前消息 |
| `messages` | `list[ChatCompletionMessageParam]` | 历史消息列表 |
| `extra_body` | `dict[str, Any]` | 额外请求参数 |
| `dyn_prompt` | `str` | 动态提示词 |
| `top_prompt` | `str` | 顶部提示词 |
| `mcp_list` | `list[MCPData]` | MCP 工具列表 |
| `skills` | `list[SkillData]` | 技能列表 |
| `tools` | `list[Tool]` | 工具列表 |
| `option` | `dict` | 选项配置 |
| `function_calls` | `list[ChatCompletionToolParam]` | 函数调用参数 |

### 只读属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `is_stream` | `bool` | 返回 `data.is_stream` |
| `canceled` | `bool` | 返回 `data.canceled` |
| `cancel_reason` | `str \| None` | 返回 `data.cancel_reason` |
| `canceller` | `str \| None` | 返回 `data.canceller` |

## 方法

### update(dict_data: dict)

更新状态数据，通过字典重建 `MessageStateData` 对象。

```python
def update(self, dict_data: dict):
    self.data = MessageStateData.model_validate(dict_data)
```

### to_dict()

将状态数据转换为字典格式。

```python
def to_dict(self):
    return self.data.model_dump()
```

### set_output_schema(name: str, json_schema: dict, strict: bool = True)

设置输出格式约束，用于强制大模型按照指定的 JSON Schema 格式输出。

```python
def set_output_schema(self, name: str, json_schema: dict, strict: bool = True):
    self.output_schema = OutputShema(name=name, json_schema=json_schema, strict=strict)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | Schema 名称 |
| `json_schema` | `dict` | JSON Schema 定义 |
| `strict` | `bool` | 是否严格模式，默认为 `True` |

### cancel(name: str, reason: str)

取消当前对话任务。

```python
def cancel(self, name: str, reason: str):
    _failed_reason = None
    
    if self.cancel_validate_handler:
        _failed_reason = self.cancel_validate_handler(name, reason)
    
    self.data.canceled = not bool(_failed_reason)
    if not self.data.canceled:
        raise Exception(_failed_reason)
    
    self.data.canceller = name
    self.data.cancel_reason = reason
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 取消操作的发起者名称 |
| `reason` | `str` | 取消原因 |

**注意**：如果设置了 `cancel_validate_handler`，会先调用验证函数。若验证失败（返回非空字符串），则取消操作失败并抛出异常。

### append_dyn(content: str)

追加动态提示内容。

```python
def append_dyn(self, content: str):
    prompt = content if content.endswith("\n") else content + "\n"
    self.data.dyn_prompt += prompt
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | 要追加的提示内容 |

### set_extra_body(key: str, value: Any)

设置额外的请求参数，这些参数会传递给大模型 API。

```python
def set_extra_body(self, key: str, value: Any):
    self.data.extra_body[key] = value
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `key` | `str` | 参数键 |
| `value` | `Any` | 参数值 |

## 使用示例

```python
from src.components.llm.message_state import MessageState
from src.components.llm.message.user_message import UserMessage

# 创建消息对象
user_msg = UserMessage(content="Hello, AI!")

# 创建 MessageState
state = MessageState(
    model_name="qwen",
    message=user_msg,
    is_stream=True
)

# 设置输出格式
state.set_output_schema(
    name="response_format",
    json_schema={
        "type": "object",
        "properties": {
            "answer": {"type": "string"}
        },
        "required": ["answer"]
    }
)

# 添加动态提示
state.append_dyn("请用中文回答")

# 设置额外参数
state.set_extra_body("temperature", 0.7)

# 取消任务
state.cancel("user", "用户主动取消")
```

## 状态流转

```
创建状态 → 更新状态 → 发送请求 → 接收响应 → 取消/完成
    ↓           ↓           ↓           ↓          ↓
 is_stream   extra_body   model_name  ChatCompletion  canceled
 messages    dyn_prompt   tools       is_stream       cancel_reason
```

## 相关类型

### MessageStateData

```python
class MessageStateData(BaseModel):
    is_stream: bool = True
    canceled: bool = False
    canceller: str | None = None
    cancel_reason: str | None = None
    output_schema: OutputShema | None = None
    model_name: str
    message: Message
    messages: list[ChatCompletionMessageParam] = []
    extra_body: dict[str, Any] = {}
    dyn_prompt: str = ""
    top_prompt: str = ""
    mcp_list: list[MCPData] = []
    skills: list[SkillData] = []
    tools: list[Tool] = []
    option: dict = {}
    function_calls: list[ChatCompletionToolParam] = []
```

### OutputShema

```python
class OutputShema(BaseModel):
    name: str
    json_schema: dict
    strict: bool
```

## 设计要点

1. **状态封装**：将所有与对话相关的状态集中管理，便于传递和修改
2. **取消机制**：支持可验证的取消操作，允许业务逻辑拒绝取消请求
3. **动态提示**：支持在对话过程中动态追加提示内容
4. **输出约束**：支持 JSON Schema 格式约束，确保大模型输出符合预期
5. **数据序列化**：支持与字典的相互转换，便于 IPC 传输和持久化
