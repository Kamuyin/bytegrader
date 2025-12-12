import logging
from typing import List

from ..core.models.enum import UserRole
from ..repositories import EnrollmentRepository
from ..repositories.course import CourseRepository
from ..core.auth.decorators import permission_manager
from ..core.models.course import Course as CourseModel
from ..schemas.course import CreateCourseRequest, UpdateCourseRequest
from ..core.exceptions.database import DatabaseError


class CourseService:
    def __init__(self, repo: CourseRepository, enrollment_repo: EnrollmentRepository):
        self.repo = repo
        self.enrollment_repo = enrollment_repo
        self.log = logging.getLogger(__name__)

    def list_courses(self, user) -> List[CourseModel]:
        all_courses = self.repo.list_all()
        visible_courses: List[CourseModel] = []
        for course in all_courses:
            context = {
                'course': course,
                'enrollment': next((e for e in user.enrollments if e.course_id == course.label), None)
            }
            if permission_manager.check(user, 'course:view', context):
                try:
                    progress = self.repo.get_progress_by_user_and_course(
                        user_id=user.id,
                        course_id=course.label
                    )
                    setattr(course, 'progress', progress)
                except Exception:
                    setattr(course, 'progress', None)

                try:
                    instructors = self.enrollment_repo.list_instructors_by_course(course.label)
                    instructor_names = [instructor.full_name for instructor in instructors]
                    setattr(course, 'instructors', instructor_names)
                except Exception:
                    setattr(course, 'instructors', None)

                user_enrollment = context['enrollment']
                is_instructor = user_enrollment and user_enrollment.role == UserRole.INSTRUCTOR

                if is_instructor:
                    try:
                        student_count = self.enrollment_repo.get_student_count_by_course(course.label)
                        setattr(course, 'student_count', student_count)
                    except Exception as e:
                        setattr(course, 'student_count', None)
                else:
                    setattr(course, 'student_count', None)

                visible_courses.append(course)
        return visible_courses

    def create_course(self, request_model: 'CreateCourseRequest') -> CourseModel:
        existing = self.repo.get(request_model.label)
        if existing:
            raise DatabaseError(f"Course with label '{request_model.label}' already exists.")
        data = request_model.model_dump()
        return self.repo.create(**data)

    def update_course(self, course_id: str, request_model: UpdateCourseRequest):
        existing = self.repo.get(course_id)
        if not existing:
            raise DatabaseError(f"Course with label '{course_id}' not found.")
        data = request_model.model_dump(exclude_unset=True)
        try:
            return self.repo.update(course_id, **data)
        except Exception as e:
            raise DatabaseError(f"Course update failed: {e}")

    def delete_course(self, course_id: str) -> None:
        existing = self.repo.get(course_id)
        if not existing:
            raise DatabaseError(f"Course with label '{course_id}' not found.")
        try:
            self.repo.delete(course_id)
        except Exception as e:
            raise DatabaseError(f"Course deletion failed: {e}")