import pydantic
from pydantic import BaseModel
from typing import Any, TypedDict
import asyncio


class App(BaseModel):
    appid: str
    name: str

class GatewayConfig(BaseModel):
    host: str
    port: int
    token: str
    max_count: int
    apps: list[App] = pydantic.Field(default_factory=lambda: [])

class TokenInfo(BaseModel):
    appid: str
    token: str

class InvokeRequestSession(TypedDict):
    signal: asyncio.Event
    result: Any | None
    start_time: int
    is_timeout: bool
