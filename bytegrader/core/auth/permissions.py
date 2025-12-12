from sqlalchemy.orm import Session

from ..models import User, Submission


class PermissionManager:
    def __init__(self, policies):
        self.policies = policies

    def get_user_role_for_course(self, user: User, course_id: str) -> str:
        if hasattr(user, 'is_admin') and user.is_admin:
            return "ADMIN"

        enrollment = next((e for e in user.enrollments if e.course_id == course_id), None)
        return enrollment.role.name if enrollment else None

    def check(self, user: User, action: str, context: dict) -> bool:
        policy = self.policies.get(action)
        if not policy:
            return False

        context['user'] = user
        scope = policy.get('scope', 'global')

        if scope == 'course':
            course = context.get('course')
            if not course:
                return False
            role = self.get_user_role_for_course(user, course.label)

        elif scope == 'assignment':
            assignment = context.get('assignment')
            if not assignment:
                return False

            db_sess = context.get('db_session')
            if db_sess:
                existing = db_sess.query(Submission).filter_by(
                    user_id=user.id, assignment_id=assignment.id
                ).first()
                context.setdefault('submission', existing)

            course = assignment.course
            context.setdefault('course', course)
            context.setdefault('enrollment', next(
                (e for e in user.enrollments if e.course_id == course.label), None
            ))
            role = self.get_user_role_for_course(user, course.label)

        else:
            role = "ADMIN" if getattr(user, 'is_admin', False) else "USER"

        if not role:
            return False

        for rule in policy['rules']:
            if role not in rule['roles']:
                continue
            try:
                if all(condition(context) for condition in rule['conditions']):
                    return True
            except (KeyError, AttributeError) as e:
                print(f"Permission check failed for action '{action}' due to missing context: {e}")
                continue

        return False

    def get_all_permissions(self, user: User, db_session: Session, resources: dict = None) -> dict:
        perms = {"global": [], "scoped": {}}
        resources = resources or {}
        user_enrollments = {e.course_id: e for e in user.enrollments}

        for action, policy in self.policies.items():
            scope = policy.get("scope", "global")

            if scope == "global":
                if self.check(user, action, {'db_session': db_session}):
                    perms["global"].append(action)

            elif scope in resources:
                for resource in resources[scope]:
                    resource_id = getattr(resource, 'label', getattr(resource, 'id', None))
                    if resource_id not in perms["scoped"]:
                        perms["scoped"][resource_id] = []

                    context = {'user': user, 'db_session': db_session}
                    if scope == 'course':
                        context['course'] = resource
                        context['enrollment'] = user_enrollments.get(resource.label)
                    elif scope == 'assignment':
                        context['assignment'] = resource
                        context['course'] = resource.course
                        context['enrollment'] = user_enrollments.get(resource.course.label)

                    if self.check(user, action, context):
                        perms["scoped"][resource_id].append(action)

        return perms
