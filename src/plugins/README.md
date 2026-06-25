# 插件编写流程

## 1. 创建插件目录
在当前目录下创建一个插件目录，必须以`_plugin`为后缀，例如`example_plugin`  
然后在插件目录下创建一个`manifest.yaml`插件描述文件，内容如下：
```yaml
name: "example_plugin"
author: "xxx"
version: "x.x.x"
description: "xxx"
entry: "plugin.ExamplePlugin"
type: "normal"
order: 0
```

- `name`插件名称(必须唯一，不可和其他插件重复)
- `author`插件作者
- `version`插件版本
- `description`插件描述
- `entry`插件入口类，格式必须是`(代码文件名称).(类名称)`
- `type`插件类型，可选值有`normal`、`system`， system类型的插件优先先触发Hook
- `order`插件执行顺序，默认为0，数字越小越先执行

## 2. 创建插件入口类
按照插件描述文件中的`entry`字段，创建一个插件入口类插件入口类必须继承`Plugin`类，如果需要编写`__init__`函数，需要把接收到的参数传给父类，例如：
```python
from src.plugin import Plugin
# plugin.py
class ExamplePlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 插件初始化逻辑
```


## 3. 编写插件Hook逻辑
插件Hook方法参数必须和`Plugin`类中的方法参数一致，当然方法名可以不一样，Hook支持异步，具体参数名称可以参考`src.plugin`的`Plugin`类定义

Hook方法需要通过`src.plugin.hook_registry`中的`registry`注释，示例如下
``` python
from src.plugin.hook_registry import registry  # 导入装饰器对象
from src.plugin import Plugin
# plugin.py
class ExamplePlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 插件初始化逻辑
    
    @registry.on_ready()    # 装饰方法，使其成为Hook
    def on_ready(self):
        print("程序就绪")
```

## 4. Plugin提供的属性

**Plugin**提供的属性如下
- `self.info`: 插件描述
- `self.application`: 主程序实例
- `self.config_home_path`: 插件目录
- `self.enable`: 插件状态，False时此插件下的Hook不会被触发，也就是插件开关

## 5. Plugin定义
### 1. deinit
这是插件被卸载时执行的方法，不算是hook

### 2. on_llm_response
**大模型响应时触发**  
参数列表:  
1. `chat_completion`: 符合OpenAI的响应对象 流式`ChatCompletionChunk`非流式`ChatCompletion`，给大模型发送消息时可能会出现异常，此时是`Exception`，需要结合判断

建议不要在此Hook执行的过程中调用主程序的send_message操作，因为插件机制的原因可能会导致深度递归

在此Hook中，可以收集到大模型回复的流式数据，并做相应的处理  
结合finish_reason参数可以判断大模型回复是否结束
如果需要在此调用大模型，可以访问主程序的llm_client属性，调用create_state方法创建一个MessageState对象  
然后调用lllm_client.stream_response方法获取大模型回复的流式数据，non_stream_response为非流式响应

### 3. on_message_before_send
**向智能体发送信息前触发**
参数列表:
1. `state`: 消息状态，这个对象是用于管理上下文的对象, 类型为`MessageState`，详细说明请参考 [MessageState 文档](../../docs/message_state.md)
2. `additional`: 附加信息，这个是来自application.send_message的信息，类型为`dict`

### 4. on_message_after_sended:
**向智能体发送信息后触发**
参数列表:
1. `state`: 消息状态，这个对象是用于管理上下文的对象, 类型为`MessageState`，详细说明请参考 [MessageState 文档](../../docs/message_state.md)

### 5. on_ready
**程序就绪时触发**

### 6. on_app_will_close
**程序关闭时触发**

### 7. emit
**用于插件与插件之间的通信**
参数列表:
1. `name`: 命令, 类型为`str`
2. `arguments`: 参数，类型为`dict`