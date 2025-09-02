from typing import TypeVar, Optional, Generic, Any, List, Dict

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class APIResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def success_response(cls, data: Any) -> 'APIResponse':
        return cls(success=True, data=data, error=None)

    @classmethod
    def error_response(cls, message: str) -> 'APIResponse':
        return cls(success=False, data=None, error=message)


class PermissionsSchema(BaseModel):
    global_: List[str] = Field(..., alias="global")
    scoped: Dict[str, List[str]]
