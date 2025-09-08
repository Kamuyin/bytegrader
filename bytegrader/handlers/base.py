import logging
import json
from uuid import uuid4
from typing import Any, TYPE_CHECKING

from jupyterhub.services.auth import HubAuthenticated
from jupyterhub.utils import url_path_join
from tornado import httputil
from tornado.log import app_log
from tornado.web import HTTPError, RequestHandler

from ..core.observability import capture_exception, set_span_attributes, set_user_context
from ..core.utils.hub import HubApiClient
from ..repositories.asset import AssignmentAssetRepository
from ..repositories.assignment import AssignmentRepository
from ..repositories.course import CourseRepository
from ..repositories.submission import SubmissionRepository
from ..repositories.user import UserRepository, EnrollmentRepository
from ..services.assignment import AssignmentService
from ..services.course import CourseService
from ..services.submission import SubmissionService

if TYPE_CHECKING:
    from bytegrader.hub import BYTEGraderApplication


class BaseHandler(HubAuthenticated, RequestHandler):
    application: "BYTEGraderApplication"

    def __init__(
        self,
        application: "BYTEGraderApplication",
        request: httputil.HTTPServerRequest,
        **kwargs: Any,
    ):
        super().__init__(application, request, **kwargs)
        self.db_mgr = self.application.db_mgr
        self.config = self.settings.get("config")
        self.log = logging.getLogger(__name__)
        self.lti_client = self.application.lti_client
        self.hub_client = HubApiClient()

    def _initialize(self):
        super()._initialize()
        self.request_id = self.request.headers.get("X-Request-ID") or uuid4().hex
        self.set_header("X-Request-ID", self.request_id)
        try:
            import sentry_sdk

            sentry_sdk.set_tag("request_id", self.request_id)
            sentry_sdk.set_context(
                "http",
                {
                    "method": self.request.method,
                    "path": self.request.path,
                    "query": self.request.query,
                },
            )
        except Exception:
            pass

        set_span_attributes(
            {
                "http.request_id": self.request_id,
                "http.method": self.request.method,
                "http.target": self.request.path,
                "http.query": self.request.query or "",
            }
        )

    def resolve_current_user(self):
        raw_user = super().get_current_user()
        if not raw_user:
            self.log.warning("No current user")
            return None, None

        lms_user_name = raw_user.get("name") if isinstance(raw_user, dict) else None
        user = None
        if lms_user_name:
            user = self.user_repo.get_by_lms_user_id(lms_user_name)

        if not user:
            if not lms_user_name:
                self.log.warning("Authenticated user payload missing 'name'")
                return None, None

            try:
                hub_user = self.hub_client.query_jupyterhub_api(
                    "GET",
                    url_path_join("users", lms_user_name),
                )
            except Exception as exc:
                self.log.error(
                    "Failed to retrieve JupyterHub user %s: %s", lms_user_name, exc
                )
                capture_exception(
                    exc,
                    tags={"component": "handler_base", "stage": "fetch_hub_user"},
                    extra={"lms_user_id": lms_user_name},
                )
                return None, None

            auth_state = hub_user.get("auth_state") if isinstance(hub_user, dict) else {}
            if not isinstance(auth_state, dict):
                auth_state = {}

            user_attrs = {
                "id": lms_user_name,
                "lms_user_id": lms_user_name,
                "first_name": auth_state.get("first_name")
                or auth_state.get("given_name")
                or "",
                "last_name": auth_state.get("last_name")
                or auth_state.get("family_name")
                or "",
                "email": auth_state.get("email") or "",
                "active": True,
            }

            try:
                self.user_repo.create(**user_attrs)
                user = self.user_repo.get_by_lms_user_id(lms_user_name)
            except Exception as exc:
                self.log.error(
                    "Failed to auto-provision user %s: %s", lms_user_name, exc
                )
                capture_exception(
                    exc,
                    tags={
                        "component": "handler_base",
                        "stage": "auto_provision_user",
                    },
                    extra={"lms_user_id": lms_user_name},
                )
                return None, None

            if not user:
                self.log.error(
                    "Auto-provisioned user %s but subsequent lookup returned no record",
                    lms_user_name,
                )
                capture_exception(
                    RuntimeError("auto_provision_missing_user"),
                    tags={
                        "component": "handler_base",
                        "stage": "auto_provision_lookup",
                    },
                    extra={"lms_user_id": lms_user_name},
                )
                return None, None

            self.log.info("Provisioned user record for %s", lms_user_name)

        if user:
            setattr(user, "is_admin", raw_user.get("admin", False))
            try:
                from sentry_sdk import set_user

                set_user(
                    {
                        "id": user.id,
                        "username": getattr(user, "lms_user_id", None),
                        "is_admin": getattr(user, "is_admin", False),
                    }
                )
            except Exception:
                pass

            set_user_context(
                user_id=user.id,
                username=getattr(user, "lms_user_id", None),
                is_admin=getattr(user, "is_admin", False),
            )
        return raw_user, user

    @property
    def course_repo(self) -> CourseRepository:
        return CourseRepository(self.db_mgr)

    @property
    def course_service(self) -> CourseService:
        return CourseService(self.course_repo, self.enrollment_repo)

    @property
    def assignment_repo(self) -> AssignmentRepository:
        return AssignmentRepository(self.db_mgr)

    @property
    def assignment_service(self) -> AssignmentService:
        return AssignmentService(
            self.assignment_repo,
            self.submission_repo,
            self.asset_repo,
            self.db_mgr,
            self.lti_client,
        )

    @property
    def asset_repo(self):
        return AssignmentAssetRepository(self.db_mgr)

    @property
    def user_repo(self) -> UserRepository:
        return UserRepository(self.db_mgr)

    @property
    def enrollment_repo(self) -> "EnrollmentRepository":
        return EnrollmentRepository(self.db_mgr)

    @property
    def submission_repo(self) -> SubmissionRepository:
        return SubmissionRepository(self.db_mgr)

    @property
    def submission_service(self) -> SubmissionService:
        return SubmissionService(self.submission_repo, self.application.autograde_service)

    @property
    def db_session(self):
        return self.db_mgr.Session()
    
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.request_id = self.request.headers.get("X-Request-ID") or uuid4().hex
        self.set_header("X-Request-ID", self.request_id)

    def write_error(self, status_code: int, **kwargs):
        self.set_header("Content-Type", "application/json")
        reason = self._reason
        if "exc_info" in kwargs:
            exc_type, exc, tb = kwargs["exc_info"]
            app_log.error(f"[{self.request_id}] Unhandled exception: {exc}", exc_info=kwargs["exc_info"])
            if isinstance(exc, HTTPError) and exc.log_message:
                reason = exc.log_message
            else:
                reason = "Internal server error"
            should_capture = True
            if isinstance(exc, HTTPError) and getattr(exc, "status_code", status_code) < 500:
                should_capture = False
            if should_capture:
                capture_exception(
                    exc,
                    tags={
                        "handler": self.__class__.__name__,
                    },
                    extra={
                        "request_id": self.request_id,
                        "method": self.request.method,
                        "path": self.request.path,
                        "query": self.request.query,
                        "status_code": status_code,
                    }
                )
        set_span_attributes(
            {
                "http.status_code": status_code,
                "http.response.error_message": reason,
                "http.response.request_id": self.request_id,
            }
        )
        body = {
            "error": {
                "code": status_code,
                "message": reason,
                "request_id": self.request_id
            }
        }
        self.finish(json.dumps(body))

