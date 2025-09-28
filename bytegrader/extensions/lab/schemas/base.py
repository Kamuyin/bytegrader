from typing import Any, Generic, Optional, TypeVar

from pydantic.v1.generics import GenericModel

T = TypeVar("T")


class LabAPIResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def success_response(cls, data: Any) -> 'LabAPIResponse':
        return cls(success=True, data=data, error=None)

    @classmethod
    def error_response(cls, message: str) -> 'LabAPIResponse':
        return cls(success=False, data=None, error=message)
