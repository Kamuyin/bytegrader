from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from .base import PermissionsSchema


class CourseSchema(BaseModel):
    label: str
    title: str
    lti_id: Optional[str] = None
    active: bool
    progress: Optional[float] = None
    student_count: Optional[int] = None
    instructors: Optional[List[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateCourseRequest(BaseModel):
    label: str
    title: str
    lti_id: Optional[str] = None
    active: Optional[bool] = True

    @field_validator('label')
    def check_label(cls, v):
        if not v.isalnum():
            raise ValueError("Label must be alphanumeric")
        return v


class CreateCourseResponse(BaseModel):
    course: 'CourseSchema'

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    courses: List[CourseSchema]
    permissions: PermissionsSchema


class UpdateCourseRequest(BaseModel):
    title: Optional[str] = None
    lti_id: Optional[str] = None
    active: Optional[bool] = None

    @field_validator('title')
    def check_title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title must not be empty")
        return v


class UpdateCourseResponse(BaseModel):
    course: CourseSchema

    model_config = {"from_attributes": True}