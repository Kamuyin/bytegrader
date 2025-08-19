import functools

from tornado.web import HTTPError

from .permissions import PermissionManager
from .policies import POLICY_STORE
from ..models import Enrollment, Assignment, Course

permission_manager = PermissionManager(POLICY_STORE)


def require_permission(action: str):

    def decorator(handler_method):
        @functools.wraps(handler_method)
        async def wrapper(self, *args, **kwargs):
            raw_user, current_user = self.resolve_current_user()
            if not raw_user or not current_user:
                raise HTTPError(401, reason="Authentication required.")

            context = {'db_session': self.db_session}
            course_id = kwargs.get('course_id')
            if course_id:
                course = self.db_session.query(Course).filter_by(label=course_id).first()
                if not course: raise HTTPError(404, reason="Course not found.")
                context['course'] = course
                context['enrollment'] = self.db_session.query(Enrollment).filter_by(user_id=current_user.id,
                                                                                    course_id=course_id).first()

            assignment_id = kwargs.get('assignment_id')
            if assignment_id:
                assignment = self.db_session.query(Assignment).filter_by(id=assignment_id).first()
                if not assignment: raise HTTPError(404, reason="Assignment not found.")
                context['assignment'] = assignment
                # If checking an assignment, we need its course context too
                if 'course' not in context:
                    context['course'] = assignment.course
                    context['enrollment'] = self.db_session.query(Enrollment).filter_by(
                        user_id=current_user.id,
                        course_id=assignment.course.label
                    ).first()

            is_allowed = permission_manager.check(current_user, action, context)

            if not is_allowed:
                raise HTTPError(403, reason=f"You do not have permission to perform this action.")

            kwargs['auth_ctx'] = context
            return await handler_method(self, *args, **kwargs)

        return wrapper

    return decorator
