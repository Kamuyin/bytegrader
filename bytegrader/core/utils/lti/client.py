import time
from urllib.parse import urlparse
import uuid
from typing import Dict, Any, Optional, List
import re
import logging

try:
    import jwt
    import requests

    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

from .config import LTIConfig
from .models import Assignment, Score, Member
from .exceptions import (
    LTIError,
    LTIAuthenticationError,
    LTIRequestError,
    LTIConfigurationError,
)

logger = logging.getLogger(__name__)


class LTIClient:

    def __init__(self, config: LTIConfig):
        if not HAS_DEPENDENCIES:
            raise LTIConfigurationError(
                "Required dependencies (PyJWT, requests) not installed"
            )

        config.validate()
        self.config = config
        self._access_token = None
        self._token_expiry = 0

    def _generate_client_assertion(self) -> str:
        current_time = int(time.time())

        if self.config.platform == "canvas":
            issuer = self.config.client_id
        else:
            issuer = self.config.platform_url

        payload = {
            "iss": issuer,
            "sub": self.config.client_id,
            "aud": self.config.token_url,
            "iat": current_time,
            "exp": current_time + 3600,
            "jti": str(uuid.uuid4()),
        }

        try:
            return jwt.encode(payload, self.config.private_key, algorithm="RS256")
        except Exception as e:
            raise LTIAuthenticationError(f"Failed to generate client assertion: {e}")

    def _ensure_access_token(self) -> str:
        current_time = time.time()

        if not self._access_token or current_time >= self._token_expiry:
            try:
                client_assertion = self._generate_client_assertion()

                scopes = " ".join(
                    [
                        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
                        "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                        "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                        "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
                    ]
                )

                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                data = {
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion,
                    "scope": scopes,
                }

                logger.debug(f"Requesting access token from {self.config.token_url}")
                response = requests.post(
                    self.config.token_url,
                    headers=headers,
                    data=data,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()

                token_data = response.json()
                self._access_token = token_data["access_token"]
                self._token_expiry = current_time + 3000

                logger.debug("Access token obtained successfully")

            except requests.RequestException as e:
                raise LTIAuthenticationError(f"Failed to obtain access token: {e}")

        return self._access_token

    def _make_authenticated_request(
        self,
        method: str,
        url: str,
        content_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            access_token = self._ensure_access_token()

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            }

            logger.debug(f"Making {method.upper()} request to {url}")

            kwargs = {"headers": headers, "url": url, "timeout": self.config.timeout}

            if payload:
                if method.lower() in ["post", "put"]:
                    kwargs["json"] = payload
                else:
                    kwargs["data"] = payload

            response = requests.request(method, **kwargs)
            response.raise_for_status()

            return response.json() if response.content else {}

        except requests.RequestException as e:
            raise LTIRequestError(f"Request failed: {e}")

    def _get_lineitem_path(self, course_id: str, assignment_id: str = None) -> str:
        if assignment_id and (
            assignment_id.startswith("http://") or assignment_id.startswith("https://")
        ):
            return assignment_id

        if self.config.platform == "canvas":
            base_path = f"{self.config.lms_lti_url}/{course_id}/line_items"
        else:
            base_path = f"{self.config.lms_lti_url}/{course_id}/lineitems"

        if assignment_id:
            return f"{base_path}/{assignment_id}"
        return base_path

    def _get_nrps_path(self, course_id: str) -> str:
        if self.config.nrps_url:
            if self.config.platform == "moodle":
                return f"{self.config.nrps_url}/CourseSection/{course_id}/bindings/1/memberships"
            else:
                return f"{self.config.nrps_url}/{course_id}/names_and_roles"

        if self.config.platform == "canvas":
            return f"{self.config.lms_lti_url}/{course_id}/names_and_roles"
        else:
            return f"{self.config.lms_lti_url}/CourseSection/{course_id}/bindings/1/memberships"

    def _extract_lineitem_id(self, full_id: str) -> str:
        patterns = [r"/line_items/(\d+)", r"/lineitems/(\d+)"]

        for pattern in patterns:
            match = re.search(pattern, full_id)
            if match:
                return match.group(1)

        try:
            parsed_url = urlparse(full_id)
            path_components = parsed_url.path.split("/")
            for component in path_components:
                if component.isdigit():
                    return component
        except Exception:
            pass

        raise ValueError(f"Could not extract lineitem ID from: {full_id}")

    def _parse_member_data(self, member_data: Dict[str, Any]) -> Member:
        if self.config.platform == "canvas":
            return Member(
                user_id=member_data.get("user_id"),
                name=member_data.get("name"),
                given_name=member_data.get("given_name"),
                family_name=member_data.get("family_name"),
                email=member_data.get("email"),
                username=member_data.get("ext_user_username"),
                roles=member_data.get("roles", []),
                status=member_data.get("status"),
            )
        else:
            member = member_data.get("member", member_data)
            return Member(
                user_id=member.get("userId"),
                name=member.get("name"),
                given_name=member.get("givenName"),
                family_name=member.get("familyName"),
                email=member.get("email"),
                username=member.get("ext_user_username"),
                roles=member_data.get("role", member_data.get("roles", [])),
                status=member_data.get("status"),
            )

    def get_assignments(self, course_id: str) -> List[Assignment]:
        url = self._get_lineitem_path(course_id)

        headers = {
            "Authorization": f"Bearer {self._ensure_access_token()}",
            "Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json",
            "Content-Type": "application/json",
        }

        try:
            logger.debug(f"Fetching assignments for course {course_id}")
            response = requests.get(url, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()

            assignments_data = response.json()
            assignments = []

            for item in assignments_data:
                assignment = Assignment(
                    id=item["id"],
                    label=item["label"],
                    score_maximum=item["scoreMaximum"],
                    resource_id=item.get("resourceId"),
                    tag=item.get("tag"),
                    submission_start_date_time=item.get("submissionStartDateTime"),
                    submission_end_date_time=item.get("submissionEndDateTime"),
                )

                try:
                    assignment.numeric_id = self._extract_lineitem_id(assignment.id)
                except ValueError:
                    assignment.numeric_id = None

                assignments.append(assignment)

            logger.debug(f"Retrieved {len(assignments)} assignments")
            return assignments

        except requests.RequestException as e:
            raise LTIRequestError(f"Failed to get assignments: {e}")

    def create_assignment(
        self,
        course_id: str,
        label: str,
        score_maximum: float,
        tag: str = None,
        resource_id: str = None,
        submission_start_date_time: str = None,
        submission_end_date_time: str = None,
    ) -> Assignment:
        url = self._get_lineitem_path(course_id)
        content_type = "application/vnd.ims.lis.v2.lineitem+json"

        payload = {
            "label": label,
            "scoreMaximum": score_maximum,
            "resourceId": resource_id or str(uuid.uuid4()),
        }

        if tag:
            payload["tag"] = tag

        if submission_start_date_time:
            payload["submissionStartDateTime"] = submission_start_date_time

        if submission_end_date_time:
            payload["submissionEndDateTime"] = submission_end_date_time

        logger.debug(f"Creating assignment '{label}' in course {course_id}")
        assignment_data = self._make_authenticated_request(
            "post", url, content_type, payload
        )

        assignment = Assignment(
            id=assignment_data["id"],
            label=assignment_data["label"],
            score_maximum=assignment_data["scoreMaximum"],
            resource_id=assignment_data.get("resourceId"),
            tag=assignment_data.get("tag"),
            submission_start_date_time=assignment_data.get("submissionStartDateTime"),
            submission_end_date_time=assignment_data.get("submissionEndDateTime"),
        )

        try:
            assignment.numeric_id = self._extract_lineitem_id(assignment.id)
        except ValueError:
            assignment.numeric_id = None

        logger.info(f"Created assignment '{label}' with ID {assignment.id}")
        return assignment

    def update_assignment(
        self,
        course_id: str,
        assignment_id: str,
        label: str = None,
        score_maximum: float = None,
        tag: str = None,
    ) -> Assignment:
        url = self._get_lineitem_path(course_id, assignment_id)
        content_type = "application/vnd.ims.lis.v2.lineitem+json"

        payload = {}
        if label is not None:
            payload["label"] = label
        if score_maximum is not None:
            payload["scoreMaximum"] = score_maximum
        if tag is not None:
            payload["tag"] = tag

        if not payload:
            raise ValueError("At least one update field must be provided")

        logger.debug(f"Updating assignment {assignment_id} in course {course_id}")
        assignment_data = self._make_authenticated_request(
            "put", url, content_type, payload
        )

        assignment = Assignment(
            id=assignment_data["id"],
            label=assignment_data["label"],
            score_maximum=assignment_data["scoreMaximum"],
            resource_id=assignment_data.get("resourceId"),
            tag=assignment_data.get("tag"),
        )

        try:
            assignment.numeric_id = self._extract_lineitem_id(assignment.id)
        except ValueError:
            assignment.numeric_id = None

        logger.info(f"Updated assignment {assignment_id}")
        return assignment

    def submit_score(
        self,
        course_id: str,
        assignment_id: str,
        user_id: str,
        score: float,
        score_max: float = None,
        comment: str = "",
        activity_progress: str = "Completed",
        grading_progress: str = "FullyGraded",
    ) -> Dict[str, Any]:
        # NOTE: Bug fix: previously used undefined variable 'lineitem_id' causing NameError.
        # The correct identifier is the passed in 'assignment_id'.
        lineitem_url = self._get_lineitem_path(course_id, assignment_id)

        url_parts = lineitem_url.split("?", 1)
        base_url = url_parts[0]
        query_params = url_parts[1] if len(url_parts) > 1 else ""

        url = f"{base_url}/scores"
        if query_params:
            url += f"?{query_params}"
        content_type = "application/vnd.ims.lis.v1.score+json"

        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "userId": user_id,
            "scoreGiven": score,
            "comment": comment or "",
            "activityProgress": activity_progress,
            "gradingProgress": grading_progress,
        }

        if score_max is not None:
            payload["scoreMaximum"] = score_max

        logger.debug(
            f"Submitting score {score} for user {user_id} in assignment {assignment_id}"
        )
        result = self._make_authenticated_request("post", url, content_type, payload)
        logger.info(f"Submitted score {score} for user {user_id}")

        return result

    def get_scores(
        self, course_id: str, assignment_id: str, user_id: str = None
    ) -> List[Dict[str, Any]]:
        url = f"{self._get_lineitem_path(course_id, assignment_id)}/results"

        headers = {
            "Authorization": f"Bearer {self._ensure_access_token()}",
            "Accept": "application/vnd.ims.lis.v2.resultcontainer+json",
            "Content-Type": "application/json",
        }

        if user_id:
            url += f"?user_id={user_id}"

        try:
            logger.debug(f"Fetching scores for assignment {assignment_id}")
            response = requests.get(url, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()

            scores = response.json()
            logger.debug(
                f"Retrieved {len(scores) if isinstance(scores, list) else 'unknown'} scores"
            )
            return scores

        except requests.RequestException as e:
            raise LTIRequestError(f"Failed to get scores: {e}")

    def get_assignment(self, course_id: str, assignment_id: str) -> Assignment:
        url = self._get_lineitem_path(course_id, assignment_id)

        headers = {
            "Authorization": f"Bearer {self._ensure_access_token()}",
            "Accept": "application/vnd.ims.lis.v2.lineitem+json",
        }

        try:
            logger.debug(f"Fetching assignment {assignment_id}")
            response = requests.get(url, headers=headers, timeout=self.config.timeout)

            if response.status_code == 200:
                assignment_data = response.json()
                assignment = Assignment(
                    id=assignment_data["id"],
                    label=assignment_data["label"],
                    score_maximum=assignment_data["scoreMaximum"],
                    resource_id=assignment_data.get("resourceId"),
                    tag=assignment_data.get("tag"),
                )

                try:
                    assignment.numeric_id = self._extract_lineitem_id(assignment.id)
                except ValueError:
                    assignment.numeric_id = None

                return assignment

            elif response.status_code == 400:
                error_details = response.json()
                raise LTIRequestError(
                    f"Assignment retrieval error: {error_details.get('reason', 'Unknown error')}"
                )
            else:
                response.raise_for_status()

        except requests.RequestException as e:
            raise LTIRequestError(f"Failed to get assignment: {e}")

    def delete_assignment(self, course_id: str, assignment_id: str) -> Dict[str, Any]:
        url = self._get_lineitem_path(course_id, assignment_id)
        content_type = "application/vnd.ims.lis.v2.lineitem+json"

        logger.debug(f"Deleting assignment {assignment_id}")
        result = self._make_authenticated_request("delete", url, content_type)
        logger.info(f"Deleted assignment {assignment_id}")

        return result

    def get_memberships(
        self, course_id: str, role_filter: Optional[str] = None
    ) -> List[Member]:
        url = self._get_nrps_path(course_id)

        headers = {
            "Authorization": f"Bearer {self._ensure_access_token()}",
            "Accept": "application/vnd.ims.lis.v2.membershipcontainer+json",
        }

        try:
            logger.debug(f"Fetching memberships for course {course_id} from URL: {url}")
            response = requests.get(url, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()

            data = response.json()

            memberships_data = []
            if "pageOf" in data and "membershipSubject" in data["pageOf"]:
                memberships_data = data["pageOf"]["membershipSubject"].get(
                    "membership", []
                )
            elif "members" in data:
                memberships_data = data["members"]

            members = []
            for member_data in memberships_data:
                member = self._parse_member_data(member_data)

                if role_filter:
                    if any(
                        role_filter.lower() in role.lower() for role in member.roles
                    ):
                        members.append(member)
                else:
                    members.append(member)

            logger.debug(f"Retrieved {len(members)} members")
            return members

        except requests.RequestException as e:
            raise LTIRequestError(f"NRPS request failed: {e}")

    def get_instructors(self, course_id: str) -> List[Member]:
        members = self.get_memberships(course_id)
        instructors = [member for member in members if member.is_instructor]

        logger.debug(f"Found {len(instructors)} instructors in course {course_id}")
        return instructors

    def get_students(self, course_id: str) -> List[Member]:
        members = self.get_memberships(course_id)
        students = [member for member in members if member.is_student]

        logger.debug(f"Found {len(students)} students in course {course_id}")
        return students
