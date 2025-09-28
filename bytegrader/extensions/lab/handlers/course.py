from tornado import web
from tornado.web import HTTPError
from tornado.escape import json_decode

from bytegrader.extensions.lab.handlers.base import LabBaseHandler
from bytegrader.schemas.course import CreateCourseRequest, UpdateCourseRequest


class LabCourseListHandler(LabBaseHandler):

    @web.authenticated
    async def get(self):
        try:
            resp = await self.course_service.list_courses()
            if not resp.success:
                error_msg = resp.error or "Failed to list courses"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_header("Content-Type", "application/json")
            self.set_status(200)
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to list courses: {e}")


class LabCourseCreateHandler(LabBaseHandler):

    @web.authenticated
    async def post(self):
        try:
            body = json_decode(self.request.body)
            req_model = CreateCourseRequest.model_validate(body)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        try:
            course = await self.course_service.create_course(req_model)
            if not course.success:
                error_msg = course.error or "Failed to create course"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_header("Content-Type", "application/json")
            self.set_status(201)
            self.write(course.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to create course: {e}")


class LabCourseDeleteHandler(LabBaseHandler):

    @web.authenticated
    async def delete(self, course_id: str):
        try:
            resp = await self.course_service.delete_course(course_id)
            if not resp.success:
                error_msg = resp.error or "Failed to delete course"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_header("Content-Type", "application/json")
            self.set_status(200)
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to delete course: {e}")


class LabCourseUpdateHandler(LabBaseHandler):

    @web.authenticated
    async def patch(self, course_id: str):
        try:
            body = json_decode(self.request.body)
            req_model = UpdateCourseRequest.model_validate(body)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        try:
            course = await self.course_service.update_course(course_id, req_model)
            if not course.success:
                error_msg = course.error or "Failed to update course"
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_header("Content-Type", "application/json")
            self.set_status(200)
            self.write(course.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to update course: {e}")