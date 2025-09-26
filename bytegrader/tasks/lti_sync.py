import logging
from typing import Optional

from ..config.config import BYTEGraderConfig
from ..core.database.connection import DatabaseManager
from ..core.exceptions.config import ConfigurationError
from ..core.models import User, Course
from ..core.utils.lti import LTIClient, LTIError, Member
from ..repositories import EnrollmentRepository, UserRepository
from ..core.utils.lti import LTIConfig
from ..repositories.course import CourseRepository
from ..core.observability import capture_exception, set_span_attributes


class LTISyncTask:

    def __init__(
        self,
        config: BYTEGraderConfig,
        db_mgr: DatabaseManager,
        client: Optional[LTIClient] = None,
    ):
        self.config = config
        self.db_mgr = db_mgr
        self.log = logging.getLogger("LTISyncTask")

        self.enrollment_repo = EnrollmentRepository(self.db_mgr)
        self.user_repo = UserRepository(self.db_mgr)
        self.course_repo = CourseRepository(self.db_mgr)

        self.client = client
        if self.client is None and self.config.lti.enabled and self.config.lti.sync_task.enabled:
            try:
                self.client = self._create_client()
            except Exception as e:
                self.log.error(f"Failed to create LTI client: {e}")
                capture_exception(
                    e,
                    tags={
                        "component": "lti_sync_task",
                        "stage": "init_client",
                    }
                )
                raise ConfigurationError(f"Failed to create LTI client: {e}") from e

    def _capture_error(self, exc: Exception, stage: str, extra: Optional[dict] = None):
        capture_exception(
            exc,
            tags={
                "component": "lti_sync_task",
                "stage": stage,
            },
            extra=extra or {}
        )

    def _create_client(self) -> LTIClient:
        priv_key = None
        key_path = self.config.lti.key_path
        if key_path:
            try:
                with open(key_path, 'r') as f:
                    priv_key = f.read()
            except Exception as e:
                self.log.error(f"Failed to read LTI private key from {key_path}: {e}")
                self._capture_error(
                    e,
                    stage="load_private_key",
                    extra={"key_path": key_path}
                )
                raise ConfigurationError(
                    f"Failed to read LTI private key from {key_path}: {e}"
                ) from e

        lti_cfg = LTIConfig(
            client_id=self.config.lti.client_id,
            platform_url=self.config.lti.lms_url,
            token_url=self.config.lti.token_url,
            private_key=priv_key,
            platform=self.config.lti.platform,
            lms_lti_url=self.config.lti.lti_url,
            nrps_url=self.config.lti.nrps_url,
            timeout=30,
        )

        lti_cfg.validate()
        return LTIClient(lti_cfg)

    async def sync(self):
        if not self.config.lti.enabled or not self.config.lti.sync_task.enabled:
            self.log.info("LTI sync task is disabled. Skipping sync.")
            return

        if not self.client:
            self.log.error("LTI client is not initialized. Cannot perform sync.")
            return

        set_span_attributes(
            {
                "component": "lti_sync_task",
                "lti.sync.enabled": True,
            }
        )
        try:
            courses = self.course_repo.get_all()
            active_courses = [c for c in courses if c.active]

            set_span_attributes(
                {
                    "lti.sync.active_course_count": len(active_courses),
                }
            )
            for c in active_courses:
                try:
                    await self.sync_course(c.lti_id)
                except Exception as e:
                    self.log.error(f"Failed to sync course {c.label} (LTI ID: {c.lti_id}): {e}")
                    self._capture_error(
                        e,
                        stage="sync_course",
                        extra={
                            "course_label": c.label,
                            "lti_course_id": c.lti_id,
                        }
                    )
                    continue

            self.log.info("Successfully synced LTI courses.")

        except Exception as e:
            self.log.error(f"Failed to sync LTI courses: {e}")
            self._capture_error(e, stage="sync")

    async def sync_course(self, course_id: str):
        if not self.client:
            self.log.error("LTI client is not initialized. Cannot perform course sync.")
            return

        set_span_attributes(
            {
                "component": "lti_sync_task",
                "lti.course_id": course_id,
            }
        )
        try:
            members = self.client.get_memberships(course_id)

            if not members:
                self.log.warning(f"No members found for course {course_id}.")
                await self._deactivate_all_enrollments_for_course(course_id)
                return

            set_span_attributes(
                {
                    "lti.members.count": len(members),
                }
            )
            user_ids = set()

            for m in members:
                try:
                    user_ids.add(m.user_id)
                    await self._process_member(course_id, m)
                except Exception as e:
                    self.log.error(f"Failed to process member {m.user_id} for course {course_id}: {e}")
                    continue

            await self._deactivate_missing_enrollments(course_id, user_ids)
            self.log.info(f"Successfully synced course {course_id}.")

        except LTIError as e:
            self.log.error(f"LTI error while syncing course {course_id}: {e}")
            self._capture_error(
                e,
                stage="sync_course_lti",
                extra={"course_id": course_id}
            )
        except Exception as e:
            self.log.error(f"Unexpected error while syncing course {course_id}: {e}")
            self._capture_error(
                e,
                stage="sync_course_unexpected",
                extra={"course_id": course_id}
            )

    async def _process_member(self, lti_course_id: str, member: Member):
        try:
            role = "INSTRUCTOR" if member.is_instructor else "STUDENT"

            set_span_attributes(
                {
                    "component": "lti_sync_task",
                    "lti.course_id": lti_course_id,
                    "lti.member.id": member.user_id,
                    "lti.member.role": role,
                }
            )

            student = self.user_repo.get_by_lms_user_id(member.user_id)
            if not student:
                student = self.user_repo.get(member.user_id)

            if not student:
                student = await self._create_student_from_member(member)
            elif student:
                student = await self._update_student_from_member(student, member)

            if not student:
                self.log.warning(f"Student {member.user_id} not found and auto-creation is disabled")
                return

            course = self.course_repo.get_by_lti_id(lti_course_id)
            if not course:
                course = await self._create_course_from_lti(lti_course_id)

            existing_enrollment = None
            try:
                existing_enrollment = self.enrollment_repo.get_by_user_and_course(student.id, course.label)
            except Exception as e:
                self.log.warning(f"Lookup for existing enrollment failed (user={student.id}, course={course.label}): {e}")

            if existing_enrollment:
                updates = {}
                if hasattr(existing_enrollment, 'role') and str(existing_enrollment.role) != role:
                    updates['role'] = role
                if not existing_enrollment.active:
                    updates['active'] = True
                if updates:
                    updated = self.enrollment_repo.update(existing_enrollment.id, **updates)
                    if updated:
                        self.log.debug(f"Updated enrollment {existing_enrollment.id} for user {student.id} in course {course.label}: {updates}")
                else:
                    self.log.debug(f"Enrollment already up-to-date for user {student.id} in course {course.label}")
            else:
                try:
                    self.enrollment_repo.create(user_id=student.id, course_id=course.label, role=role, active=True)
                except Exception as e:
                    self.log.error(f"Failed to create enrollment for user {student.id} in course {course.label}: {e}")
                    self._capture_error(
                        e,
                        stage="create_enrollment",
                        extra={
                            "user_id": student.id,
                            "course_label": course.label,
                            "role": role,
                        }
                    )

        except Exception as e:
            self.log.error(f"Error processing member {member.user_id}: {e}")
            self._capture_error(
                e,
                stage="process_member",
                extra={
                    "member_id": member.user_id,
                    "course_id": lti_course_id,
                }
            )

    async def _deactivate_missing_enrollments(self, lti_course_id: str, current_lms_user_ids: set):
        try:
            course = self.course_repo.get_by_lti_id(lti_course_id)
            if not course:
                self.log.warning(f"Course with LTI ID {lti_course_id} not found, cannot deactivate missing enrollments")
                return

            set_span_attributes(
                {
                    "component": "lti_sync_task",
                    "lti.course_id": lti_course_id,
                    "lti.active_enrollments.count": len(current_lms_user_ids),
                }
            )
            active_enrollments = self.enrollment_repo.get_by_course(course.label)
            deactivated_count = 0

            for enrollment in active_enrollments:
                student = self.user_repo.get(enrollment.user_id)
                if student:
                    student_in_lms = (
                            student.id in current_lms_user_ids or
                            (student.lms_user_id and student.lms_user_id in current_lms_user_ids)
                    )

                    if not student_in_lms:
                        success = self.enrollment_repo.update(enrollment.id, active=False)
                        if success:
                            deactivated_count += 1
                            self.log.info(f"Deactivated enrollment for student {student.id} in course {course.label}")
                        else:
                            self.log.warning(
                                f"Failed to deactivate enrollment for student {student.id} in course {course.label}")

            if deactivated_count > 0:
                self.log.info(f"Deactivated {deactivated_count} enrollments for course {course.label}")

        except Exception as e:
            self.log.error(f"Error deactivating missing enrollments for course {lti_course_id}: {e}")
            self._capture_error(
                e,
                stage="deactivate_missing_enrollments",
                extra={"course_id": lti_course_id}
            )

    async def _deactivate_all_enrollments_for_course(self, lti_course_id: str):
        try:
            course = self.course_repo.get_by_lti_id(lti_course_id)
            if not course:
                self.log.warning(f"Course with LTI ID {lti_course_id} not found, cannot deactivate enrollments")
                return

            set_span_attributes(
                {
                    "component": "lti_sync_task",
                    "lti.course_id": lti_course_id,
                }
            )
            enrollments = self.enrollment_repo.get_by_course(course.label)
            active_enrollments = [e for e in enrollments if e.active]
            deactivated_count = 0

            for enrollment in active_enrollments:
                success = self.enrollment_repo.update(enrollment.id, active=False)
                if success:
                    deactivated_count += 1

            if deactivated_count > 0:
                self.log.warning(
                    f"Deactivated all {deactivated_count} enrollments for course {course.label} - no members found in "
                    f"LMS")

        except Exception as e:
            self.log.error(f"Error deactivating all enrollments for course {lti_course_id}: {e}")
            self._capture_error(
                e,
                stage="deactivate_all_enrollments",
                extra={"course_id": lti_course_id}
            )

    async def _create_student_from_member(self, member: Member) -> Optional[User]:
        try:
            student_id = member.user_id

            student = User(
                id=student_id,
                lms_user_id=member.user_id,
                first_name=member.given_name or "",
                last_name=member.family_name or "",
                email=member.email or "",
                active=True
            )

            created_student = self.user_repo.create_from_instance(student)
            self.log.info(f"Created student {student_id} - {member.given_name} {member.family_name}")
            return created_student

        except Exception as e:
            self.log.error(f"Failed to create student from member {member.user_id}: {e}")
            self._capture_error(
                e,
                stage="create_student",
                extra={"member_id": member.user_id}
            )
            return None

    async def _update_student_from_member(self, existing_student: User, member: Member) -> Optional[User]:
        try:
            updates = {}

            if existing_student.first_name != (member.given_name or ""):
                updates['first_name'] = member.given_name or ""

            if existing_student.last_name != (member.family_name or ""):
                updates['last_name'] = member.family_name or ""

            if member.email and existing_student.email != member.email:
                updates['email'] = member.email

            if not existing_student.lms_user_id:
                updates['lms_user_id'] = member.user_id

            if updates:
                updated_student = self.user_repo.update(existing_student.id, **updates)
                if updated_student:
                    self.log.info(f"Updated student {existing_student.id} with LTI data: {updates}")
                    return updated_student
                else:
                    self.log.warning(f"Failed to update student {existing_student.id}")

            return existing_student

        except Exception as e:
            self.log.error(f"Failed to update student {existing_student.id} from member {member.user_id}: {e}")
            self._capture_error(
                e,
                stage="update_student",
                extra={
                    "student_id": existing_student.id,
                    "member_id": member.user_id,
                }
            )
            return existing_student

    async def _create_course_from_lti(self, lti_course_id: str) -> Optional[Course]:
        try:
            course_label = f"lti_course_{lti_course_id}"

            course = Course(
                label=course_label,
                title=f"Course {lti_course_id}",
                lti_id=lti_course_id,
                active=True
            )

            created_course = self.course_repo.create_from_instance(course)
            self.log.info(f"Created course {course_label} with LTI ID {lti_course_id}")
            return created_course

        except Exception as e:
            self.log.error(f"Failed to create course with LTI ID {lti_course_id}: {e}")
            self._capture_error(
                e,
                stage="create_course",
                extra={"lti_course_id": lti_course_id}
            )
            return None
