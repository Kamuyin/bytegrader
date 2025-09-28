from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

from bytegrader.core.models.enum import ShowSolutionsOption


class NotebookSchema(BaseModel):
    id: str
    name: str
    idx: int
    max_score: float


class SubmissionSchema(BaseModel):
    id: str
    submitted_at: datetime
    status: str
    is_late: bool
    total_score: float
    auto_score: float
    manual_score: float
    needs_manual_grading: bool
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None


class AssignmentSchema(BaseModel):
    id: str
    name: str
    description: str
    due_date: Optional[datetime] = None
    visible: bool
    created_at: datetime
    allow_resubmission: bool
    notebooks: List[NotebookSchema]
    submission: Optional[SubmissionSchema] = None
    status: Optional[str] = None


class PermissionsSchema(BaseModel):
    global_: List[str] = Field(..., alias='global')
    scoped: Dict[str, List[str]]


class AssignmentListData(BaseModel):
    assignments: List[AssignmentSchema]
    permissions: PermissionsSchema


class FileReference(BaseModel):
    rel: str  # Path in the assignment directory
    abs: str  # Real path while creation


class LabAssignmentCreateRequest(BaseModel):
    name: str
    description: str
    due_date: Optional[datetime] = None
    visible: bool
    allow_resubmission: bool
    show_solutions: ShowSolutionsOption
    lti_sync: bool

    notebooks: List[FileReference]
    assets: List[FileReference]


class LabAssignmentGenerateRequest(BaseModel):
    notebooks: List[FileReference]
    assets: List[FileReference]
