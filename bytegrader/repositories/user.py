from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from ..core.exceptions import DatabaseError
from ..core.models import User, Enrollment
from sqlalchemy.orm import joinedload
from .base import BaseRepository
from ..core.database.connection import DatabaseManager
from ..core.models.enum import UserRole


class UserRepository(BaseRepository[User]):
    def __init__(self, db_mgr: DatabaseManager):
        super().__init__(User, db_mgr)

    def get_by_lms_user_id(self, lms_user_id: str) -> Optional[User]:
        with self.db_manager.get_session() as session:
            try:
                user = (
                    session.query(self.model)
                    .options(joinedload(self.model.enrollments))
                    .filter_by(lms_user_id=lms_user_id)
                    .first()
                )
                return user
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve User with lms_user_id {lms_user_id}: {str(e)}") from e


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, db_mgr: DatabaseManager):
        super().__init__(Enrollment, db_mgr)

    def get_by_user_and_course(self, user_id: str, course_id: str) -> Optional[Enrollment]:
        with self.db_manager.get_session() as session:
            try:
                enrollment = session.query(self.model).filter_by(
                    user_id=user_id,
                    course_id=course_id,
                    active=True
                ).first()
                return enrollment
            except SQLAlchemyError as e:
                raise DatabaseError(
                    f"Failed to retrieve Enrollment for user {user_id} in course {course_id}: {str(e)}") from e

    def get_by_course(self, course_id: str) -> list[Enrollment]:
        with self.db_manager.get_session() as session:
            try:
                enrollments = session.query(self.model).filter_by(
                    course_id=course_id,
                    active=True
                ).all()
                return enrollments
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve Enrollments for course {course_id}: {str(e)}") from e

    def list_instructors_by_course(self, course_id: str) -> list[User]:
        with self.db_manager.get_session() as session:
            try:
                instructors = (
                    session.query(User)
                    .join(Enrollment)
                    .filter(Enrollment.course_id == course_id, Enrollment.role == UserRole.INSTRUCTOR,
                            Enrollment.active == True)
                    .all()
                )
                return instructors
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve Instructors for course {course_id}: {str(e)}") from e

    def list_students_by_course(self, course_id: str) -> list[User]:
        with self.db_manager.get_session() as session:
            try:
                students = (
                    session.query(User)
                    .join(Enrollment)
                    .filter(Enrollment.course_id == course_id, Enrollment.role == UserRole.STUDENT, Enrollment.active == True)
                    .all()
                )
                return students
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve Students for course {course_id}: {str(e)}") from e

    def get_student_count_by_course(self, course_id: str) -> int:
        with self.db_manager.get_session() as session:
            try:
                count = (
                    session.query(User)
                    .join(Enrollment)
                    .filter(Enrollment.course_id == course_id, Enrollment.role == UserRole.STUDENT, Enrollment.active == True)
                    .count()
                )
                return count
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to count Students for course {course_id}: {str(e)}") from e
