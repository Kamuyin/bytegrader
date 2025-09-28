import logging

from jupyter_server.base.handlers import JupyterHandler

from bytegrader.extensions.lab.services.assignment import LabAssignmentService
from bytegrader.extensions.lab.services.course import LabCourseService
import json
from uuid import uuid4
from tornado.web import HTTPError
from tornado.log import app_log
from bytegrader.extensions.lab.services.submission import LabSubmissionService

logger = logging.getLogger(__name__)


class LabBaseHandler(JupyterHandler):

    @property
    def hub_client(self):
        return self.settings.get("hub_client")

    @property
    def course_service(self) -> LabCourseService:
        return LabCourseService(self.hub_client)

    @property
    def assignment_service(self) -> LabAssignmentService:
        return LabAssignmentService(self.hub_client)

    @property
    def submission_service(self) -> LabSubmissionService:
        return LabSubmissionService(self.hub_client)
    
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
        body = {
            "error": {
                "code": status_code,
                "message": reason,
                "request_id": self.request_id
            }
        }
        self.finish(json.dumps(body))