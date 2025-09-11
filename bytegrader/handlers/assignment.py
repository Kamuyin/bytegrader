import json
import os
import uuid

import nbformat
from tornado import web
from tornado.web import HTTPError

from .base import BaseHandler
from tornado.web import HTTPError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from ..core.auth import require_permission
from ..core.auth.decorators import permission_manager
from ..core.exceptions.database import DatabaseError
from ..schemas.assignment import AssignmentSchema, AssignmentCreateRequest, \
    AssignmentListResponse
from ..schemas.base import APIResponse, PermissionsSchema


class AssignmentCreateHandler(BaseHandler):

    @web.authenticated
    @require_permission('assignment:create')
    async def post(self, course_id, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            raise HTTPError(status_code=401, log_message="Unauthorized")

        try:
            meta_json = self.get_body_argument("metadata")
            meta = json.loads(meta_json)
            req_model = AssignmentCreateRequest.model_validate(meta)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        notebooks = self.request.files.get('notebooks')
        if not notebooks:
            raise HTTPError(status_code=400, log_message="No notebook file provided")

        assets = self.request.files.get('assets')

        try:
            self.log.info(f"Creating assignment for course {course_id} with metadata: {req_model.model_dump()}")
            assignment = self.assignment_service.create_assignment(req_model, course_id, notebooks, assets)
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Assignment already exists or conflicts with existing data")
        except DatabaseError as e:
            raise HTTPError(status_code=409, log_message=str(e))
        except Exception as e:
            raise HTTPError(status_code=500, log_message="Internal server error")

        resp_model = AssignmentSchema.model_validate(assignment)
        self.set_status(201)
        self.set_header("Content-Type", "application/json")
        self.write(APIResponse.success_response(resp_model).model_dump_json(by_alias=True))


class AssignmentListHandler(BaseHandler):

    @web.authenticated
    async def get(self, course_id):
        try:
            raw_user, user = self.resolve_current_user()
            if not raw_user or not user:
                raise HTTPError(status_code=401, log_message="Unauthorized")

            items = self.assignment_service.list_assignments(course_id, user)
            raw_assignments = self.assignment_repo.get_by_course(course_id)
            visible_ids = [a.id for a in items]
            visible_raw = [a for a in raw_assignments if a.id in visible_ids]

            with self.db_mgr.get_session() as sess:
                permissions = permission_manager.get_all_permissions(
                    user,
                    sess,
                    resources={'assignment': visible_raw}
                )

            response = AssignmentListResponse(
                assignments=items,
                permissions=PermissionsSchema.model_validate(permissions)
            )
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.write(APIResponse.success_response(response).model_dump_json(by_alias=True))
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Data conflict or constraint violation")
        except SQLAlchemyError:
            raise HTTPError(status_code=500, log_message="Internal server error")


class AssignmentFetchHandler(BaseHandler):

    @web.authenticated
    @require_permission('assignment:fetch')
    async def get(self, course_id, assignment_id, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            raise HTTPError(status_code=401, log_message="Unauthorized")

        solution_param = self.get_argument("solution", default="false").lower()
        show_solution = solution_param == 'true'

        if show_solution:
            from ..core.auth.decorators import permission_manager
            if not permission_manager.check(user, 'assignment:fetch_solution', auth_ctx):
                raise HTTPError(status_code=403, log_message="You do not have permission to view solutions")

        assignment = auth_ctx['assignment']

        try:
            notebooks, assets = self.assignment_service.fetch_assignment(assignment, show_solution)
        except PermissionError as e:
            raise HTTPError(status_code=403, log_message=str(e))

        if not assignment or assignment.course_id != course_id:
            raise HTTPError(status_code=404, log_message="Assignment not found or does not belong to this course")

        # I'm sorry for this... Please forgive me. (╯°□°）╯︵ ┻━┻
        boundary = f"bytegrader-boundary-{uuid.uuid4().hex}"
        self.set_header("Content-Type", f"multipart/mixed; boundary={boundary}")

        response_parts = []

        assignment_data = AssignmentSchema.model_validate(assignment).model_dump(mode='json')
        metadata_json = json.dumps(assignment_data)
        response_parts.append(
            f'--{boundary}\r\n'
            f'Content-Type: application/json\r\n'
            f'Content-Disposition: form-data; name="metadata"\r\n\r\n'
            f'{metadata_json}\r\n'
        )

        for name, nb in notebooks:
            notebook_json = nbformat.writes(nb)
            response_parts.append(
                f'--{boundary}\r\n'
                f'Content-Type: application/json\r\n'
                f'Content-Disposition: form-data; name="notebook"; filename="{name}"\r\n\r\n'
                f'{notebook_json}\r\n'
            )

        asset_path = self.db_mgr.config.database.asset_path
        if asset_path:
            for asset in assets:
                file_path = os.path.join(asset_path, asset.id)
                if os.path.exists(file_path):
                    # Content type (kind of useless in this case)
                    content_type = "application/octet-stream"
                    if asset.path.lower().endswith(('.jpg', '.jpeg')):
                        content_type = "image/jpeg"
                    elif asset.path.lower().endswith('.png'):
                        content_type = "image/png"
                    elif asset.path.lower().endswith('.txt'):
                        content_type = "text/plain"
                    elif asset.path.lower().endswith('.csv'):
                        content_type = "text/csv"

                    # Binary part header
                    response_parts.append(
                        f'--{boundary}\r\n'
                        f'Content-Type: {content_type}\r\n'
                        f'Content-Disposition: form-data; name="asset"; filename="{asset.path}"\r\n\r\n'
                    )

                    self.write("".join(response_parts))
                    response_parts = []

                    with open(file_path, 'rb') as f:
                        self.write(f.read())
                    self.write("\r\n")

        response_parts.append(f'--{boundary}--\r\n')
        self.write("".join(response_parts))
        await self.finish()


class AssignmentDeleteHandler(BaseHandler):

    @web.authenticated
    @require_permission('assignment:delete')
    async def delete(self, course_id, assignment_id, auth_ctx=None):
        try:
            raw_user, user = self.resolve_current_user()
            if not raw_user or not user:
                raise HTTPError(status_code=401, log_message="Unauthorized")

            self.assignment_service.delete_assignment(assignment_id, course_id)
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.write(APIResponse.success_response("Assignment deleted").model_dump_json(by_alias=True))
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Unable to delete assignment, data conflict")
        except SQLAlchemyError:
            raise HTTPError(status_code=500, log_message="Internal server error")
