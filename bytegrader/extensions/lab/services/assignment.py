import json
import logging
import os.path
import re
import shutil
import stat
import tempfile
from pathlib import Path
from urllib.parse import urljoin

import nbformat
import requests

from ..schemas.base import LabAPIResponse
from ..schemas.assignment import AssignmentListData, LabAssignmentCreateRequest, LabAssignmentGenerateRequest, \
    FileReference
from ....core.utils.hub import HubApiClient
from ....preprocessors.factory import ProcessorFactory
from ....schemas.assignment import AssignmentCreateRequest


class LabAssignmentService:

    def __init__(self, hub_client: HubApiClient):
        self.hub_client = hub_client

    async def list_assignments(self, course_id: str) -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='GET',
                api_path=f'/courses/{course_id}/assignments',
                params={}
            )
            resp = LabAPIResponse.parse_obj(response)
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to list assignments: {e}")

        if not resp.success or not resp.data:
            return resp

        assignments_data = AssignmentListData.parse_obj(resp.data)
        base = os.path.join(os.getcwd(), "courses", course_id)

        for assignment in assignments_data.assignments:
            fetched = os.path.isdir(os.path.join(base, assignment.id))
            sub = assignment.submission

            if not fetched and not sub:
                status = "NOT_STARTED"
            elif fetched and not sub:
                status = "IN_PROGRESS"
            elif sub.status == "submitted":
                status = "SUBMITTED"
            elif sub.status == "graded":
                total_max_score = sum(nb.max_score for nb in assignment.notebooks)
                if sub.total_score == total_max_score or not assignment.allow_resubmission:
                    status = "COMPLETED"
                else:
                    status = "GRADED"
            else:  # Should not happen, but just in case
                status = "IN_PROGRESS"

            assignment.status = status

        resp.data = assignments_data.model_dump(by_alias=True)
        return resp

    async def fetch_assignment(self, course_id: str, assignment_id: str, solution: bool = False) -> LabAPIResponse:
        try:
            params = {"solution": str(solution).lower()} if solution else {}
            resp = self.hub_client.query_hub_service_raw(
                method='GET',
                api_path=f'/courses/{course_id}/assignments/{assignment_id}/fetch',
                params=params
            )

            raw_bytes = resp.content
            content_type = resp.headers.get("Content-Type", "")
            match = re.search(r'boundary=([^;]+)', content_type)
            if not match:
                return LabAPIResponse.error_response("Invalid content type, missing boundary")
            boundary = match.group(1)

            base_dir = os.path.join(os.getcwd(), "courses", course_id, assignment_id)
            if solution:
                base_dir = os.path.join(base_dir, "solution")
            os.makedirs(base_dir, exist_ok=True)

            parts = raw_bytes.decode('latin1', errors='ignore').split(f'--{boundary}')

            assignment_metadata = None

            for part in parts:
                if not part.strip():
                    continue

                header_end = part.find('\r\n\r\n')
                if header_end == -1:
                    continue

                headers_text = part[:header_end]
                content = part[header_end + 4:].strip()

                headers = {}
                for line in headers_text.split('\r\n'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        headers[key.lower()] = value

                disposition = headers.get('content-disposition', '')
                name_match = re.search(r'name="([^"]+)"', disposition)
                filename_match = re.search(r'filename="([^"]+)"', disposition)

                if not name_match:
                    continue

                name = name_match.group(1)

                if name in ('notebook', 'asset') and filename_match:
                    filename = filename_match.group(1)

                    safe_path = _sanitize_path(base_dir, filename)
                    if not safe_path:
                        logging.warning(f"Skipping file due to path traversal concern: {filename}")
                        continue

                    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

                    is_binary = name == 'asset' and not headers.get('content-type', '').startswith(
                        ('text/', 'application/json'))

                    if is_binary:
                        with open(safe_path, 'wb') as f:
                            f.write(content.encode('latin1'))
                    else:
                        with open(safe_path, 'w') as f:
                            f.write(content)
                    try:
                        # Solutions must be read-only; student notebooks are writable
                        if solution:
                            Path(safe_path).chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                        else:
                            Path(safe_path).chmod(
                                stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
                            )
                    except Exception:
                        logging.warning(f"Could not adjust permissions on fetched file {safe_path}")

            return LabAPIResponse.success_response({})

        except Exception as e:
            logging.exception(f"Error fetching assignment: {e}")
            return LabAPIResponse.error_response(f"Failed to fetch assignment: {str(e)}")

    async def create_assignment(self, course_id: str, req_model: LabAssignmentCreateRequest) -> LabAPIResponse:
        files = []

        metadata = AssignmentCreateRequest(
            **req_model.model_dump(include={
                'name', 'description', 'due_date', 'visible',
                'allow_resubmission', 'show_solutions', 'lti_sync'
            }, exclude_unset=True),
            allow_late_submission=False
        )

        files.append((
            "metadata",
            (None, metadata.model_dump_json(by_alias=True), "application/json")
        ))

        base_dir = os.getcwd()

        for ref in req_model.notebooks:
            abs_p = os.path.join(base_dir, ref.abs)
            if not os.path.isfile(abs_p):
                return LabAPIResponse.error_response(f"Notebook file does not exist: {abs_p}")
            with open(abs_p, "rb") as f:
                content = f.read()
            files.append(("notebooks", (ref.rel, content, "application/octet-stream")))

        for ref in req_model.assets:
            abs_p = os.path.join(base_dir, ref.abs)
            if not os.path.isfile(abs_p):
                return LabAPIResponse.error_response(f"Asset file does not exist: {abs_p}")
            with open(abs_p, "rb") as f:
                content = f.read()
            files.append(("assets", (ref.rel, content, "application/octet-stream")))

        base = self.hub_client.service_url.rstrip("/") + "/"
        url = urljoin(base, f"courses/{course_id}/assignments/create")
        headers = {"Authorization": f"token {self.hub_client.api_token}"}
        resp = requests.post(url, files=files, headers=headers, timeout=30)

        if resp.ok:
            return LabAPIResponse.parse_obj(resp.json())
        return LabAPIResponse.error_response(f"Create failed: {resp.text}")

    async def delete_assignment(self, course_id: str, assignment_id: str) -> LabAPIResponse:
        try:
            response = self.hub_client.query_hub_service(
                method='DELETE',
                api_path=f'/courses/{course_id}/assignments/{assignment_id}/delete',
                params={}
            )
            resp = LabAPIResponse.parse_obj(response)
            return resp
        except Exception as e:
            return LabAPIResponse.error_response(f"Failed to delete assignment: {e}")

    async def generate_assignment(self, req: LabAssignmentGenerateRequest) -> LabAPIResponse:
        if not req.notebooks:
            return LabAPIResponse.error_response("No notebooks provided for generation")

        tmp_root = Path(os.getcwd()) / "tmp"
        tmp_root.mkdir(parents=True, exist_ok=True)
        base_dir = Path(tempfile.mkdtemp(prefix="bytegrader-", dir=tmp_root))
        try:
            pipeline = ProcessorFactory.create_assignment_generation_pipeline(None)
            generated = []

            for ref in req.notebooks:
                rel_pth = Path(ref.rel)
                abs_pth = Path(os.getcwd()) / ref.abs
                if not abs_pth.is_file():
                    return LabAPIResponse.error_response(f"Notebook file does not exist: {abs_pth}")

                nb = nbformat.read(str(abs_pth), nbformat.current_nbformat)
                processed_nb, _ = pipeline.process(nb, {})

                out_pth = base_dir / rel_pth
                out_pth.parent.mkdir(parents=True, exist_ok=True)
                nbformat.write(processed_nb, out_pth.open('w', encoding='utf-8'))
                try:
                    out_pth.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                except Exception:
                    logging.warning(f"Failed to set read-only permissions for {out_pth}")

                generated.append(
                    FileReference(rel=str(rel_pth), abs=str(out_pth)).model_dump(by_alias=True)
                )

            for ref in req.assets:
                rel_pth = Path(ref.rel)
                abs_pth = Path(os.getcwd()) / ref.abs
                if not abs_pth.is_file():
                    return LabAPIResponse.error_response(f"Asset file does not exist: {abs_pth}")

                out_pth = base_dir / rel_pth
                out_pth.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(abs_pth), str(out_pth))
                try:
                    out_pth.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                except Exception:
                    logging.warning(f"Failed to set read-only permissions for {out_pth}")

                generated.append(
                    FileReference(rel=str(rel_pth), abs=str(out_pth)).model_dump(by_alias=True)
                )

            rel_base_dir = base_dir.relative_to(Path(os.getcwd()))

            return LabAPIResponse.success_response({
                "base_dir": str(rel_base_dir),
                "files": generated
            })

        except Exception as e:
            shutil.rmtree(str(base_dir), ignore_errors=True)
            return LabAPIResponse.error_response(f"Failed to generate assignment: {str(e)}")


def _sanitize_path(base_dir: str | Path, user_input_path: str | Path) -> Path:
    base_dir = Path(base_dir).resolve(strict=True)
    user_input_path = Path(str(user_input_path).lstrip("/\\")).parts
    cleaned_parts = [part for part in user_input_path if part not in ("..", ".", "")]
    safe_path = base_dir.joinpath(*cleaned_parts).resolve(strict=False)
    return safe_path


