from tornado import web
from tornado.web import HTTPError

from bytegrader.extensions.lab.handlers.base import LabBaseHandler


class LabAssignmentSubmitHandler(LabBaseHandler):

    @web.authenticated
    async def post(self, course_id: str, assignment_id: str):
        try:
            resp = await self.submission_service.submit_assignment(course_id, assignment_id)
            if not resp.success:
                if "\"message\":" in error_msg:
                    try:
                        import json
                        nested_error = json.loads(error_msg.split(": ", 1)[1])
                        if "error" in nested_error and "message" in nested_error["error"]:
                            error_msg = nested_error["error"]["message"]
                    except:
                        pass
                raise HTTPError(status_code=500, log_message=error_msg)

            self.set_status(200)
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Assignment submission failed: {e}")