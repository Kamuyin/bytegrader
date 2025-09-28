import os.path
from urllib.parse import urljoin

import requests

from bytegrader.core.models import Submission
from bytegrader.core.utils.hub import HubApiClient
from bytegrader.extensions.lab.schemas.base import LabAPIResponse


class LabSubmissionService:
    def __init__(self, hub_client: 'HubApiClient'):
        self.hub_client = hub_client

    async def submit_assignment(self, course_id: str, assignment_id: str) -> LabAPIResponse:
        try:
            base_dir = os.path.join(os.getcwd(), 'courses', course_id, assignment_id)
            files = []
            for root, _, filenames in os.walk(base_dir):
                for fname in filenames:
                    if not fname.endswith('.ipynb'):
                        continue
                    path = os.path.join(root, fname)
                    rel = os.path.relpath(path, base_dir)
                    files.append(('notebooks', (rel, open(path, 'rb'), 'application/x-ipynb+json')))

            base_url = self.hub_client.service_url.rstrip("/") + "/"
            path = f"courses/{course_id}/assignments/{assignment_id}/submit".lstrip("/")
            url = urljoin(base_url, path)

            headers = {
                "Authorization": f"token {self.hub_client.api_token}",
            }

            resp = requests.post(
                url=url,
                files=files,
                headers=headers,
                timeout=30
            )

            if resp.ok:
                data = resp.json()
                return LabAPIResponse.parse_obj(data)
            else:
                return LabAPIResponse.error_response(f"Failed to submit assignment: {resp.text}")

        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to submit assignment: {str(e)}")