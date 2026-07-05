from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    status: int = 200
    msg: str = "success"
    data: Optional[T] = None
