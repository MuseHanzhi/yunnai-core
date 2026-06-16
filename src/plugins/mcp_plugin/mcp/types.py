from mcp.client.session import ClientSession
from mcp.types import Tool
from typing import (
    TypedDict,
    NotRequired,
    Union,
    Any,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from .mcp_client import MCPClient

class ClientInfo(TypedDict):
    name: str
    version: str

class MCPInfo(TypedDict):
    name: str
    session: ClientSession | None
    client: "MCPClient"
    tools: list[Tool]

class GetToolResult(TypedDict):
    message: str
    is_error: bool
    tools: list[Tool]

class CallResult(TypedDict):
    message: str
    is_error: bool
    content: Any

class AuthOption(TypedDict):
    callback_url: str
    redirect_uris: list[str]

class MCPStreamableHTTPOption(TypedDict):
    url: str
    enable: NotRequired[bool]
    desc: NotRequired[str]
    headers: NotRequired[dict[str, str]]
    auth: NotRequired[AuthOption]

class MCPStdioOption(TypedDict):
    command: str
    disabled: NotRequired[bool]
    desc: NotRequired[str]
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]

MCPOption = Union[MCPStreamableHTTPOption, MCPStdioOption]
