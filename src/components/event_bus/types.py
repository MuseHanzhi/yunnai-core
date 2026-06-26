from pydantic import BaseModel
from typing import Literal, TypeAlias, Union
from openai.types import CompletionUsage
from openai.types.create_embedding_response import Usage as EmbeddingUsage

class ChatModelUsage(BaseModel):
    type: Literal["chat"]
    model_name: str
    usage: CompletionUsage

class EmbeddingModelUsage(BaseModel):
    type: Literal["embedding"]
    model_name: str
    usage: EmbeddingUsage

ModelUsage: TypeAlias = Union[ChatModelUsage, EmbeddingModelUsage]
