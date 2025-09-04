from typing import Optional, List

from pydantic import BaseModel, Field
from datetime import datetime

from .base import PermissionsSchema
from ..core.models.enum import ShowSolutionsOption


class AssignmentSchema(BaseModel):
    id: str
    name: str
    description: str
    due_date: Optional[datetime] = Field(default=None)
    visible: bool
    allow_resubmission: bool
    allow_late_submission: bool
    show_solutions: ShowSolutionsOption

    model_config = {"from_attributes": True}


class AssignmentCreateRequest(BaseModel):
    name: str
    description: str
    due_date: Optional[datetime] = Field(default=None)
    visible: bool
    allow_resubmission: bool
    allow_late_submission: bool
    show_solutions: ShowSolutionsOption
    lti_sync: bool


class NotebookSchema(BaseModel):
    id: str
    name: str
    idx: int
    max_score: float

    model_config = {"from_attributes": True}


class AssignmentSubmissionSchema(BaseModel):
    id: str
    submitted_at: Optional[datetime]
    status: str
    is_late: bool
    total_score: float
    auto_score: float
    manual_score: float
    needs_manual_grading: bool
    graded_at: Optional[datetime]
    graded_by: Optional[str]

    model_config = {"from_attributes": True}


class AssignmentListItemSchema(BaseModel):
    id: str
    name: str
    description: Optional[str]
    due_date: Optional[datetime]
    visible: bool
    created_at: datetime
    allow_resubmission: bool
    notebooks: List[NotebookSchema]
    submission: Optional[AssignmentSubmissionSchema]

    model_config = {"from_attributes": True}


class AssignmentListResponse(BaseModel):
    assignments: list[AssignmentListItemSchema]
    permissions: PermissionsSchema
