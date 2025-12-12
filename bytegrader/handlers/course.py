import json

from tornado import web
from tornado.web import HTTPError
from tornado.escape import json_decode
from sqlalchemy.exc import IntegrityError

from .base import BaseHandler
from ..core.auth import require_permission
from ..core.auth.decorators import permission_manager
from ..core.exceptions.database import DatabaseError
from ..schemas.base import APIResponse
from ..schemas.course import (
    CourseSchema,
    CourseListResponse,
    PermissionsSchema,
    CreateCourseRequest,
    CreateCourseResponse, UpdateCourseResponse, UpdateCourseRequest,
)


class CourseCreateHandler(BaseHandler):

    @web.authenticated
    @require_permission('course:create')
    async def post(self, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            raise HTTPError(status_code=401, log_message="Unauthorized")

        self.set_header("Content-Type", "application/json")
        try:
            body = json_decode(self.request.body)
            req_model = CreateCourseRequest.model_validate(body)
        except Exception as e:
            raise HTTPError(status_code=400, log_message=f"Invalid request: {e}")

        try:
            course = self.course_service.create_course(req_model)
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Course with given identifier already exists")
        except DatabaseError as e:
            raise HTTPError(status_code=409, log_message=str(e))
        except Exception:
            raise HTTPError(status_code=500, log_message="Internal server error")

        course_schema = CourseSchema.model_validate(course)
        resp_model = CreateCourseResponse(course=course_schema)
        self.set_status(201)
        self.write(APIResponse.success_response(resp_model).model_dump_json(by_alias=True))


class CourseListHandler(BaseHandler):

    @web.authenticated
    async def get(self):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            self.set_status(401)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "Unauthorized"})
            return

        visible_courses = self.course_service.list_courses(user)
        with self.db_mgr.get_session() as session:
            permissions = permission_manager.get_all_permissions(
                user,
                session,
                resources={'course': visible_courses}
            )

        course_schemas = [CourseSchema.model_validate(c) for c in visible_courses]

        permissions_model = PermissionsSchema.model_validate(permissions)
        response_model = CourseListResponse(courses=course_schemas, permissions=permissions_model)
        self.set_header("Content-Type", "application/json")
        self.write(APIResponse.success_response(response_model).model_dump_json(by_alias=True))


class CourseUpdateHandler(BaseHandler):

    @web.authenticated
    @require_permission('course:edit')
    async def patch(self, course_id: str, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            self.set_status(401)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "Unauthorized"})
            return

        self.set_header("Content-Type", "application/json")
        try:
            body = json_decode(self.request.body)
            req_model = UpdateCourseRequest.model_validate(body)
        except Exception as e:
            self.set_status(400)
            self.write({"error": f"Invalid request: {e}"})
            return

        try:
            course = self.course_service.update_course(course_id, req_model)
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Course update conflicts with existing data")
        except DatabaseError as e:
            code = 404 if "not found" in str(e).lower() else 409
            raise HTTPError(status_code=code, log_message=str(e))
        except Exception:
            raise HTTPError(status_code=500, log_message="Internal server error")

        course_schema = CourseSchema.model_validate(course)
        resp_model = UpdateCourseResponse(course=course_schema)
        self.write(APIResponse.success_response(resp_model).model_dump_json(by_alias=True))


class CourseDeleteHandler(BaseHandler):

    @web.authenticated
    @require_permission('course:delete')
    async def delete(self, course_id: str, auth_ctx=None):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            self.set_status(401)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "Unauthorized"})
            return

        try:
            self.course_service.delete_course(course_id)
        except IntegrityError:
            raise HTTPError(status_code=409, log_message="Unable to delete course, it is referenced by existing records")
        except DatabaseError as e:
            code = 404 if "not found" in str(e).lower() else 409
            raise HTTPError(status_code=code, log_message=str(e))
        except Exception:
            raise HTTPError(status_code=500, log_message="Internal server error")

        self.set_status(200)
        self.set_header("Content-Type", "application/json")
        await self.finish(APIResponse.success_response("Course deleted successfully").model_dump_json(by_alias=True))
