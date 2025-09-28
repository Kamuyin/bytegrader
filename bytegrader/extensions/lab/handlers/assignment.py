from tornado import web
from tornado.web import HTTPError
from tornado.escape import json_decode

from bytegrader.extensions.lab.handlers.base import LabBaseHandler
from bytegrader.extensions.lab.schemas.assignment import LabAssignmentCreateRequest, LabAssignmentGenerateRequest
from bytegrader.extensions.lab.schemas.base import LabAPIResponse


class LabAssignmentListHandler(LabBaseHandler):

    @web.authenticated
    async def get(self, course_id: str):
        try:
            resp = await self.assignment_service.list_assignments(course_id)
            if not resp.success:
                error_msg = resp.error or "Failed to list assignments"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(200)
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to list assignments: {e}")


class LabAssignmentFetchHandler(LabBaseHandler):

    @web.authenticated
    async def get(self, course_id: str, assignment_id: str):
        try:
            solution_param = self.get_argument("solution", default="false").lower()
            show_solution = solution_param == 'true'
            resp = await self.assignment_service.fetch_assignment(course_id, assignment_id, solution=show_solution)
            if not resp.success:
                error_msg = resp.error or "Failed to fetch assignment"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(200)
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to fetch assignment: {e}")


class LabAssignmentCreateHandler(LabBaseHandler):

    @web.authenticated
    async def post(self, course_id: str):
        try:
            body = json_decode(self.request.body)
            req_model = LabAssignmentCreateRequest.model_validate(body)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        try:
            assignment = await self.assignment_service.create_assignment(course_id, req_model)
            if not assignment.success:
                error_msg = assignment.error or "Failed to create assignment"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(201)
            self.write(assignment.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to create assignment: {e}")


class LabAssignmentDeleteHandler(LabBaseHandler):

    @web.authenticated
    async def delete(self, course_id: str, assignment_id: str):
        try:
            resp = await self.assignment_service.delete_assignment(course_id, assignment_id)
            if not resp.success:
                error_msg = resp.error or "Failed to delete assignment"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(200)
            self.write(LabAPIResponse.success_response({}).model_dump_json(
                by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to delete assignment: {e}")


class LabAssignmentGenerateHandler(LabBaseHandler):

    @web.authenticated
    async def post(self):
        try:
            body = json_decode(self.request.body)
            req_model = LabAssignmentGenerateRequest.model_validate(body)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        try:
            assignment = await self.assignment_service.generate_assignment(req_model)
            if not assignment.success:
                error_msg = assignment.error or "Failed to generate assignment"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(201)
            self.write(assignment.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to generate assignment: {e}")
