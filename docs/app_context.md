# AppContext 程序上下文文档

## 概述

`app_context` 是框架中的全局单例对象，负责管理应用程序的配置、启动参数和运行时路径。它在整个应用生命周期中保持唯一实例，所有模块通过导入它来获取配置信息。

## 核心属性

### app_config

应用程序配置，从 `app_config.yaml` 加载：

```python
app_context.app_config["logging"]   # 日志配置
app_context.app_config["system"]   # 系统配置
app_context.app_config["llm"]      # 大模型配置
```

### fixed_config

固定配置，从 `fixed_config.yaml` 加载：

```python
app_context.fixed_config.plugin_config   # 插件配置
app_context.fixed_config.system_info     # 系统信息（名称、版本）
```

### launch_args

命令行启动参数：

```python
app_context.launch_args.llm       # 指定模型
app_context.launch_args.config    # 指定配置文件路径
app_context.launch_args.ipc_url   # IPC 连接地址
app_context.launch_args.pwd      # 工作目录
```

### home_path

程序主目录：`~/.{system_info.name}/`

例如：`~/.yunnai-core/`

### data_path

数据目录：`~/.{system_info.name}/data/`

### mode

运行模式：
- `core`：内核模式（无 IPC 连接）
- `client`：客户端模式（连接 IPC）

## 使用示例

```python
from src.core.app_context import app_context

# 获取系统配置
sys_config = app_context.app_config["system"]

# 获取大模型配置
llm_config = app_context.app_config["llm"]

# 获取插件配置路径
plugin_search_path = app_context.fixed_config.plugin_config.search_path

# 获取启动参数
default_model = app_context.launch_args.llm
```

## 配置结构

```
app_config.yaml
├── logging     # 日志配置
├── system      # 系统配置（线程数、环境变量检查等）
└── llm         # 大模型配置（默认模型、模型列表）

fixed_config.yaml
├── system_info        # 系统信息
└── plugin_config      # 插件配置（搜索路径）
```

## 启动参数

命令行启动时可传入：

```bash
python main.py llm=qwen config=my_config.yaml ipc_url=ws://localhost:8866
```
