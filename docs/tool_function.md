# ToolFunction 工具函数文档

## 概述

`ToolFunction` 是框架提供的工具函数定义类，用于描述可供大模型调用的工具。

## 定义工具

```python
from src.core.tools import ToolFunction
from src.core.tools.property import PropertyMap
from src.core.tools.properties import String, Array, Integer, Number, Boolean
```

创建工具实例：

```python
tool = ToolFunction(
    name="tool_name",
    description="工具描述",
    func=handle_function,
    properties=[
        String(name="param1", description="参数1", required=True),
        Integer(name="param2", description="参数2", range=(0, 100), required=False),
        Array(name="param3", description="数组参数", item_type="string", required=False),
        Number(name="param4", description="数值参数", range=(0.0, 1.0), required=False),
        Boolean(name="param5", description="布尔参数", required=False),
    ]
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 工具名称，唯一标识 |
| `description` | `str` | 工具描述，供大模型理解用途 |
| `func` | `Callable` | 工具执行函数 |
| `properties` | `list` | 参数定义列表 |

## 参数类型

| 类型 | 说明 | 额外参数 |
|------|------|----------|
| `String` | 字符串 | `enum` 可选值列表 |
| `Integer` | 整数 | `range` 数值范围 |
| `Number` | 浮点数 | `range` 数值范围 |
| `Boolean` | 布尔值 | - |
| `Array` | 数组 | `item_type` 元素类型 |

## 工具函数签名

```python
async def handle_function(properties: PropertyMap) -> str:
    # 通过属性名获取参数值
    param1 = properties["param1"].value
    param2 = properties["param2"].value  # 自动类型转换

    # 返回字符串结果
    return "result"
```

`PropertyMap` 支持类型转换：`str()`、`int()`、`float()`、`bool()`、`list()`

## 获取工具 Schema

```python
schema = tool.get_schema()
```

返回 OpenAI Function Calling 格式的 schema：

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "工具描述",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数1"},
                "param2": {"type": "integer", "description": "参数2", "minimum": 0, "maximum": 100}
            },
            "required": ["param1"]
        }
    }
}
```

## 完整示例

```python
from src.core.tools import ToolFunction
from src.core.tools.property import PropertyMap
from src.core.tools.properties import String, Integer

async def get_user_info(properties: PropertyMap) -> str:
    user_id = int(properties["user_id"].value)
    return f"User #{user_id} info"

tool = ToolFunction(
    name="get_user_info",
    description="获取用户信息",
    func=get_user_info,
    properties=[
        Integer(name="user_id", description="用户ID", range=(1, 999999))
    ]
)

# 使用
schema = tool.get_schema()
result = await tool({"user_id": 123})
```
