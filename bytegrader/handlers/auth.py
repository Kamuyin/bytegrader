from bytegrader.handlers.base import BaseHandler
from tornado import web
from tornado.web import HTTPError
import json

from bytegrader.schemas.base import APIResponse


class WhoAmIHandler(BaseHandler):

    @web.authenticated
    async def get(self):
        raw_user, user = self.resolve_current_user()
        if not raw_user or not user:
            raise HTTPError(status_code=401, log_message="Unauthorized")

        user_info = {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.lms_user_id,
            "is_admin": getattr(user, "is_admin", False)
        }

        response = APIResponse.success_response(user_info)
        self.set_status(200)
        self.set_header("Content-Type", "application/json")
        self.write(response.json(by_alias=True))
