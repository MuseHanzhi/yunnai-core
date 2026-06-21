import subprocess
import asyncio

from src.core.tools import ToolFunction
from src.core.tools.property import PropertyMap
from src.core.tools.properties import String, Array, Number, Integer

from typing import (
    Callable,
    Coroutine,
    Any,
    TypeAlias
)

ValidateCommandHandler: TypeAlias = Callable[[str, list[str]], Coroutine[Any, Any, bool] | bool]

ERROR_TEMPLATE = "# ERROR\n<output>{message}</output>"
SUCCESS_TEMPLATE = "# SUCCESS\n<output>{message}</output>"

_tools: list[ToolFunction] = []
_validate_command_handler: ValidateCommandHandler | None = None
_safe_commands: list[str] = []

def setup(safe_commands: list[str] | None = None, validate_command_handler: ValidateCommandHandler | None = None):
    global _validate_command_handler, _safe_commands, _tools
    _safe_commands = safe_commands or []
    _validate_command_handler = validate_command_handler
    
    _tools = [
        ToolFunction(
            name="self.shell",
            description="Execute shell commands",
            func=shell,
            properties=[
                String(name="command", description="The base command to execute WITHOUT any arguments or flags (e.g., 'ls', 'git', 'python'). DO NOT include arguments here."),
                Array(
                    name="args",
                    description="List of command-line arguments. Each argument MUST be a separate string in the array. Example: ['-l', '-a', '/home/user']. NEVER put arguments inside the 'command' field.",
                    item_type="string",
                    required=False
                ),
                Number(
                    name="timeout",
                    description="Command execution timeout (in seconds), default is 0 (no timeout)",
                    range=(0, 60),
                    required=False
                )
            ]
        )
    ]

def get_tools() -> list[ToolFunction]:
    return _tools

def run_shell(cmd: str, args: list[str], timeout: float | None = None) -> str:
    try:
        # 如果 timeout 为 0 或 None，subprocess 默认不限制超时
        shell_result = subprocess.run(
            args=[cmd, *args],
            text=True,
            capture_output=True,
            timeout=timeout if timeout and timeout > 0 else None
        )
    except subprocess.TimeoutExpired:
        return ERROR_TEMPLATE.format(message=f"Execution timeout ({timeout}s)")
    except FileNotFoundError:
        return ERROR_TEMPLATE.format(
                message=f"Command '{cmd}' not found. Did you put arguments in the 'command' field? "
                    f"Please use 'command' for the base executable ONLY, and pass arguments in the 'args' array."
                    )
    except Exception as e:
        # 捕获其他可能的执行异常（如找不到命令等）
        return ERROR_TEMPLATE.format(message=str(e))
    
    if shell_result.returncode != 0 and shell_result.stderr:
        return ERROR_TEMPLATE.format(message=shell_result.stderr.strip())
    
    return SUCCESS_TEMPLATE.format(message=shell_result.stdout.strip())

async def shell(properties: PropertyMap) -> str:
    cmd = str(properties["command"] or "").strip()
    args = list(properties["args"] or [])
    timeout = properties["timeout"]  # ✅ 修复：正确提取 timeout

    if not cmd:
        return ERROR_TEMPLATE.format(message="The parameter 'command' is required")

    allow_execute = False
    
    # ✅ 修复：白名单优先放行
    if cmd in _safe_commands:
        allow_execute = True
    elif _validate_command_handler:
        call_result = _validate_command_handler(cmd, args)
        # 兼容同步和异步的验证回调
        if asyncio.iscoroutine(call_result):
            call_result = await call_result
        allow_execute = bool(call_result)
    
    if not allow_execute:
        return ERROR_TEMPLATE.format(message="The user refused to execute")
    
    # ✅ 修复：使用 asyncio.to_thread 避免阻塞事件循环
    try:
        result = await asyncio.to_thread(run_shell, cmd=cmd, args=args, timeout=float(timeout) if timeout else None)
        return result
    except Exception as e:
        return ERROR_TEMPLATE.format(message=f"Failed to execute shell: {str(e)}")
