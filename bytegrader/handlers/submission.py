import json

from tornado import web
from tornado.web import HTTPError
from sqlalchemy.exc import IntegrityError
from tornado.web import HTTPError
from tornado.escape import json_decode

from .base import BaseHandler
from ..core.auth import require_permission
from ..core.auth.decorators import permission_manager
from ..core.exceptions.database import DatabaseError
from ..schemas.assignment import AssignmentSubmissionSchema
from ..schemas.base import APIResponse


class AssignmentSubmitHandler(BaseHandler):

    @web.authenticated
    @require_permission('assignment:submit')
    async def post(self, course_id: str, assignment_id: str, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            raise HTTPError(status_code=401, log_message="Unauthorized")

        notebooks = self.request.files.get('notebooks')
        if not notebooks:
            raise HTTPError(status_code=400, log_message="No notebook file provided")

        assignment = auth_ctx.get('assignment')
        if not assignment or assignment.course_id != course_id:
            raise HTTPError(status_code=404, log_message="Assignment not found")

        try:
            submission = await self.submission_service.submit_assignment(assignment, user, notebooks)
            submission_schema = AssignmentSubmissionSchema.model_validate(submission)
            self.set_status(201)
            self.set_header("Content-Type", "application/json")
            self.write(APIResponse.success_response(submission_schema).model_dump_json(by_alias=True))
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Submission conflict or invalid data")
        except DatabaseError as e:
            raise HTTPError(status_code=500, log_message="Internal server error")
        except ValueError as e:
            raise HTTPError(status_code=400, log_message=f"Invalid submission: {e}")