import asyncio
import os
import logging
from tornado.web import Application as WebApplication

from .autograde.service import AutogradingService
from .config.config import BYTEGraderConfig
from .core.database.connection import DatabaseManager
from .core.exceptions.config import ConfigurationError
from .core.utils.lti import LTIClient, LTIConfig
from .handlers.assignment import AssignmentCreateHandler, AssignmentListHandler, AssignmentFetchHandler, \
    AssignmentDeleteHandler
from .handlers.auth import WhoAmIHandler
from .handlers.course import CourseListHandler, CourseCreateHandler, CourseUpdateHandler, CourseDeleteHandler
from .handlers.submission import AssignmentSubmitHandler
from .tasks.lti_sync import LTISyncTask
from .tasks.scheduler import TaskScheduler

HANDLERS = [
    (r"/courses", CourseListHandler),
    (r"/courses/create", CourseCreateHandler),
    (r"/courses/(?P<course_id>[^/]+)/update", CourseUpdateHandler),
    (r"/courses/(?P<course_id>[^/]+)/delete", CourseDeleteHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments", AssignmentListHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/create", AssignmentCreateHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/delete", AssignmentDeleteHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/fetch", AssignmentFetchHandler),
    (r"/courses/(?P<course_id>[^/]+)/assignments/(?P<assignment_id>[^/]+)/submit", AssignmentSubmitHandler),
    (r"/auth/whoami", WhoAmIHandler)
]


class BYTEGraderApplication(WebApplication):
    def __init__(self,
                 handlers,
                 db_uri: str,
                 config: 'BYTEGraderConfig',
                 **settings
                 ):
        super().__init__(handlers, **settings)
        self.config = config
        self.db_mgr = DatabaseManager(db_uri, config)
        self.db_mgr.create_tables()

        if self.config.lti.enabled:
            try:
                priv_key = None
                key_path = self.config.lti.key_path
                if key_path:
                    try:
                        with open(key_path, 'r') as f:
                            priv_key = f.read()
                    except Exception as e:
                        self.log.error(f"Failed to read LTI private key from {key_path}: {e}")
                        raise ConfigurationError(
                            f"Failed to read LTI private key from {key_path}: {e}"
                        ) from e
                lti_cfg = LTIConfig(
                    client_id=self.config.lti.client_id,
                    platform_url=self.config.lti.lms_url,
                    token_url=self.config.lti.token_url,
                    private_key=priv_key,
                    platform=self.config.lti.platform,
                    lms_lti_url=self.config.lti.lti_url,
                    nrps_url=self.config.lti.nrps_url,
                    timeout=30,
                )
                self.lti_client = LTIClient(lti_cfg)
            except Exception as e:
                logging.error(f"Failed to initialize LTI client: {e}")
                self.lti_client = None
        else:
            self.lti_client = None

        self.autograde_service = AutogradingService(self.config, self.db_mgr, self.lti_client)

    def start_services(self):
        self.autograde_service.log.info("Starting autograding service...")
        loop = asyncio.get_event_loop()
        loop.create_task(self.autograde_service.start())


class BYTEGraderHubApp:
    def __init__(self, config: 'BYTEGraderConfig'):
        self.config = config
        self.log = logging.getLogger(__name__)
        self.scheduler = None

    def create_tornado_app(self, prefix: str = "") -> WebApplication:
        self.log.debug("Creating Tornado app with prefix %s", prefix)
        routes = [
            (f"{prefix.rstrip('/')}{pattern}", handler)
            for pattern, handler in HANDLERS
        ]

        if not self.config.database.uri:
            raise ValueError("Database URI is not configured. Please set the database URI in the configuration.")

        settings = {
            'cookie_secret': os.urandom(32),
            'debug': False,
            'compress_response': True,
        }

        app = BYTEGraderApplication(routes, db_uri=self.config.database.uri, config=self.config, **settings)

        loop = asyncio.get_event_loop()

        self.scheduler = TaskScheduler(self.config)

        if self.config.lti.enabled and self.config.lti.sync_task.enabled:
            lti_sync = LTISyncTask(self.config, app.db_mgr)
            loop.run_until_complete(lti_sync.sync())
            self.scheduler.add_job(
                func=lti_sync.sync,
                job_id="lti_sync",
                interval=self.config.lti.sync_task.interval,
            )
            self.log.info("LTI sync task is enabled.")

        self.scheduler.start()

        loop.call_soon(app.start_services)

        # Init assets dir
        if self.config.database.asset_path:
            asset_path = self.config.database.asset_path
            if not os.path.exists(asset_path):
                os.makedirs(asset_path, exist_ok=True)
                self.log.debug(f"Created asset directory at {asset_path}")
            else:
                self.log.debug(f"Asset directory already exists at {asset_path}")

        return app
