import logging

from jupyterhub.utils import url_path_join

from bytegrader.core.utils.hub import HubApiClient
from bytegrader.extensions.lab.handlers.assignment import LabAssignmentListHandler, LabAssignmentFetchHandler, \
    LabAssignmentCreateHandler, LabAssignmentGenerateHandler, LabAssignmentDeleteHandler
from bytegrader.extensions.lab.handlers.auth import LabWhoAmIHandler
from bytegrader.extensions.lab.handlers.course import LabCourseListHandler, LabCourseCreateHandler, \
    LabCourseDeleteHandler, LabCourseUpdateHandler
from bytegrader.extensions.lab.handlers.submission import LabAssignmentSubmitHandler

HANDLERS = [
    (r"/generate_assignment", LabAssignmentGenerateHandler),
    (r"/courses", LabCourseListHandler),
    (r"/courses/create", LabCourseCreateHandler),
    (r"/courses/(?P<course_id>[^/]+)/update", LabCourseUpdateHandler),
    (r"/courses/(?P<course_id>[^/]+)/delete", LabCourseDeleteHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments", LabAssignmentListHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/create", LabAssignmentCreateHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/delete", LabAssignmentDeleteHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/fetch", LabAssignmentFetchHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/submit", LabAssignmentSubmitHandler),
    (r"/auth/whoami", LabWhoAmIHandler)
]

logger = logging.getLogger("bytegrader.labextension")


def load_jupyter_server_extension(app):
    try:
        webapp = app.web_app
        base_url = webapp.settings.get("base_url", "")
        hub_client = HubApiClient()
        webapp.settings["hub_client"] = hub_client
        webapp.add_handlers('.*$', [
            (url_path_join(base_url, 'bytegrader', path), handler)
            for path, handler in HANDLERS
        ])
        logger.info("BYTE Grader labextension loaded successfully.")
    except Exception:
        logger.error("Failed to load BYTE Grader Lab extension", exc_info=True)
