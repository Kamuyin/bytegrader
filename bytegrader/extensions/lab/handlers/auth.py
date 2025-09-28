from tornado import web
from tornado.web import HTTPError

from bytegrader.extensions.lab.handlers.base import LabBaseHandler
from bytegrader.extensions.lab.schemas.base import LabAPIResponse


class LabWhoAmIHandler(LabBaseHandler):

    @web.authenticated
    async def get(self):
        try:
            response = self.hub_client.query_hub_service(
                method='GET',
                api_path='/auth/whoami',
                params={}
            )
            resp = LabAPIResponse.parse_obj(response)
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(resp.json(by_alias=True))
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPError(status_code=500, log_message=f"Failed to request user info: {e}")