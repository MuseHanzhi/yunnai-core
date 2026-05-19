from pydantic import BaseModel
from typing import Any, TypedDict
import asyncio

class TokenInfo(BaseModel):
    appid: str
    token: str

class InvokeRequestSession(TypedDict):
    signal: asyncio.Event
    result: Any | None
    start_time: int
    is_timeout: bool
