from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LTIUser:
    user_id: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []

    @property
    def is_instructor(self) -> bool:
        instructor_roles = [
            "instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/person#administrator"
        ]
        return any(role.lower() in instructor_role.lower() or instructor_role.lower() in role.lower()
                   for role in self.roles for instructor_role in instructor_roles)

    @property
    def is_student(self) -> bool:
        student_roles = [
            "learner",
            "student",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#learner"
        ]
        return any(role.lower() in student_role.lower() or student_role.lower() in role.lower()
                   for role in self.roles for student_role in student_roles)


@dataclass
class LTIContext:
    context_id: str
    label: Optional[str] = None
    title: Optional[str] = None
    type: List[str] = None

    def __post_init__(self):
        if self.type is None:
            self.type = []


@dataclass
class Assignment:
    id: str
    label: str
    score_maximum: float
    resource_id: Optional[str] = None
    tag: Optional[str] = None
    numeric_id: Optional[str] = None
    submission_start_date_time: Optional[str] = None
    submission_end_date_time: Optional[str] = None


@dataclass
class Score:
    user_id: str
    score_given: float
    score_maximum: float
    comment: Optional[str] = None
    activity_progress: str = "Completed"
    grading_progress: str = "FullyGraded"
    timestamp: Optional[str] = None


@dataclass
class Member:
    user_id: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = None
    status: Optional[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []

    @property
    def is_instructor(self) -> bool:
        instructor_roles = [
            "instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/person#administrator"
        ]
        return any(role.lower() in instructor_role.lower() or instructor_role.lower() in role.lower()
                   for role in self.roles for instructor_role in instructor_roles)

    @property
    def is_student(self) -> bool:
        student_roles = [
            "learner",
            "student",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#learner"
        ]
        return any(role.lower() in student_role.lower() or student_role.lower() in role.lower()
                   for role in self.roles for student_role in student_roles)