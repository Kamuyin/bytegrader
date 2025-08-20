from datetime import datetime

from bytegrader.core.models import Submission
from bytegrader.core.models.enum import ShowSolutionsOption
from ..utils import utc_now
from ..utils.datetime import ensure_aware


def check_fetch_solution_for_student(ctx):
    assignment = ctx['assignment']
    user = ctx['user']
    db_session = ctx['db_session']
    show_solutions = assignment.show_solutions

    if show_solutions == ShowSolutionsOption.NEVER:
        return False
    elif show_solutions == ShowSolutionsOption.ALWAYS:
        return True
    elif show_solutions == ShowSolutionsOption.AFTER_DUE:
        if assignment.due_date:
            return utc_now() > ensure_aware(assignment.due_date)
        return False  # Deny if no due date
    elif show_solutions == ShowSolutionsOption.AFTER_SUBMISSION:
        return db_session.query(Submission).filter_by(user_id=user.id, assignment_id=assignment.id).first() is not None
    elif show_solutions == ShowSolutionsOption.AFTER_COMPLETION:
        submission = db_session.query(Submission).filter_by(user_id=user.id, assignment_id=assignment.id).first()
        if submission:
            if not assignment.allow_resubmission:
                return True
            return submission.total_score >= assignment.max_score
        return False
    return False


POLICY_STORE = {
    # --- Global Permissions ---
    "course:create": {
        "description": "Allows creating a new course",
        "scope": "global",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []}
        ]
    },

    # --- Course-Scoped Permissions ---
    "course:view": {
        "description": "Allows viewing course in a listing.",
        "scope": "course",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [lambda ctx: ctx.get('enrollment') is not None]},
            {"roles": ["STUDENT"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
                lambda ctx: ctx['course'].active is True,
            ]},
        ]
    },
    "course:edit": {
        "description": "Allows editing a course's details.",
        "scope": "course",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
        ],
    },
    "course:enrollments": {
        "description": "Allows viewing/modifying enrollments in a course.",
        "scope": "course",
        "rules": [
            {"roles": ["ADMIN"], "conditions": [
                lambda ctx: ctx['course'].lti_id is None,
            ]},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
                lambda ctx: ctx['course'].lti_id is None,
            ]},
        ],
    },
    "course:delete": {
        "description": "Allows deleting a course.",
        "scope": "course",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
        ],
    },
    "assignment:create": {
        "description": "Allows creating a new assignment in a course.",
        "scope": "course",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
        ]
    },

    # --- Assignment-Scoped Permissions ---
    "assignment:view": {
        "description": "Allows viewing assignment.",
        "scope": "assignment",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
            {"roles": ["STUDENT"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
                lambda ctx: ctx['assignment'].course.active is True,
                lambda ctx: ctx['assignment'].visible is True
            ]}
        ]
    },
    "assignment:fetch": {
        "description": "Allows fetching the assignment's notebooks and assets.",
        "scope": "assignment",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
            {"roles": ["STUDENT"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
                lambda ctx: ctx['assignment'].course.active is True,
                lambda ctx: ctx['assignment'].visible is True
            ]}
        ]
    },
    "assignment:fetch_solution": {
        "description": "Allows fetching the solution notebook of an assignment.",
        "scope": "assignment",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
            {"roles": ["STUDENT"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
                lambda ctx: ctx['assignment'].course.active is True,
                lambda ctx: ctx['assignment'].visible is True,
                check_fetch_solution_for_student,
            ]}
        ]
    },
    "assignment:submit": {
        "description": "Allows submitting a solution to an assignment.",
        "scope": "assignment",
        "rules": [
            {
                "roles": ["STUDENT", "INSTRUCTOR", "ADMIN"],
                "conditions": [
                    lambda ctx: ctx.get('enrollment') is not None,
                    lambda ctx: ctx['assignment'].course.active is True,
                    lambda ctx: ctx['assignment'].visible is True,
                    lambda ctx: (
                                        ctx['assignment'].due_date is None
                                        or utc_now() <= ensure_aware(ctx['assignment'].due_date)
                                ) or ctx['assignment'].allow_late_submission is True,
                    lambda ctx: ctx.get('submission') is None
                                or ctx['assignment'].allow_resubmission is True,
                ],
            },
        ],
    },
    "assignment:delete": {
        "description": "Allows deleting an assignment.",
        "scope": "assignment",
        "rules": [
            {"roles": ["ADMIN"], "conditions": []},
            {"roles": ["INSTRUCTOR"], "conditions": [
                lambda ctx: ctx.get('enrollment') is not None,
            ]},
        ],
    },
}
