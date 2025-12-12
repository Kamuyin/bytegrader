from typing import List

from ..core.models import Submission
from ..core.models.course import Course as CourseModel
from .base import BaseRepository


class CourseRepository(BaseRepository[CourseModel]):
    def __init__(self, db_manager):
        super().__init__(CourseModel, db_manager)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[CourseModel]:
        return self.get_all(skip=skip, limit=limit)

    def get_by_lti_id(self, lti_id: str) -> CourseModel:
        with self.db_manager.get_session() as session:
            course = session.query(self.model).filter_by(lti_id=lti_id).first()
            if not course:
                raise ValueError(f"Course with LTI ID {lti_id} not found.")
            return course

    def get_progress_by_user_and_course(self, user_id: str, course_id: str) -> float:
        with self.db_manager.get_session() as session:
            course = session.query(self.model).filter_by(label=course_id).first()
            if not course:
                raise ValueError(f"Course with ID {course_id} not found.")

            if not course.assignments:
                return 100.0

            completed_count = 0
            total_assignments = len(course.assignments)

            for assignment in course.assignments:
                submission = session.query(Submission).filter_by(
                    assignment_id=assignment.id,
                    user_id=user_id
                ).first()

                if submission:
                    if submission.total_score >= assignment.max_score or not assignment.allow_resubmission:
                        completed_count += 1

            progress = (completed_count / total_assignments) * 100.0
            return progress
