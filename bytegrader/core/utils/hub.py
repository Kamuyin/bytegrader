import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests

from ..exceptions.hub import JupyterHubEnvironmentError, ByteGraderServiceError, JupyterHubApiError

logger = logging.getLogger(__name__)

class HubApiClient:

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._api_token = None
        self._hub_api_url = None

    @property
    def api_token(self) -> str:
        if self._api_token is None:
            self._api_token = os.getenv("JUPYTERHUB_API_TOKEN")
            if not self._api_token:
                raise JupyterHubEnvironmentError(
                    "JUPYTERHUB_API_TOKEN environment variable is required"
                )
        return self._api_token

    @property
    def hub_api_url(self) -> str:
        if self._hub_api_url is None:
            self._hub_api_url = os.environ.get(
                "JUPYTERHUB_API_URL", "http://127.0.0.1:8081/hub/api"
            )
        return self._hub_api_url

    @property
    def service_url(self) -> str:
        hub_host = os.getenv("JUPYTERHUB_HOST", "127.0.0.1")

        if not hub_host:
            hub_api_url = self.hub_api_url

            if "://" in hub_api_url:
                url_parts = hub_api_url.split("://")[1]
                host_part = url_parts.split("/")[0]
                host_only = host_part.split(":")[0]
                hub_host = host_only

        constructed_url = f"http://{hub_host}:8000/services/bytegrader"
        return constructed_url

    def query_hub_service(
        self,
        method: str,
        api_path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_url = self.service_url.rstrip("/") + "/"
        path = api_path.lstrip("/")
        url = urljoin(base_url, path)

        headers = {
            "Authorization": f"token {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            logger.debug(f"Making {method} request to service: {url}")

            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            logger.debug(f"Service response status: {response.status_code}")

            if response.ok:
                try:
                    return response.json()
                except ValueError as e:
                    raise ByteGraderServiceError(
                        f"Invalid JSON response from service: {e}",
                        response.status_code,
                        response.text,
                    )

            error_msg = (
                f"Service returned status {response.status_code} "
                f"for {method} {url}"
            )
            logger.error(f"{error_msg}: {response.text}")
            raise ByteGraderServiceError(error_msg, response.status_code, response.text)

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s for {url}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error for {url}: {e}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {e}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)

    def query_hub_service_raw(
            self,
            method: str,
            api_path: str,
            data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        base_url = self.service_url.rstrip("/") + "/"
        path = api_path.lstrip("/")
        url = urljoin(base_url, path)

        headers = {
            "Authorization": f"token {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            logger.debug(f"Making {method} request to service: {url}")
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            logger.debug(f"Service response status: {response.status_code}")

            if response.ok:
                return response

            error_msg = (
                f"ByteGrader service returned status {response.status_code} "
                f"for {method} {url}"
            )
            logger.error(f"{error_msg}: {response.text}")
            raise ByteGraderServiceError(error_msg, response.status_code, response.text)

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s for {url}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error for {url}: {e}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {e}"
            logger.error(error_msg)
            raise ByteGraderServiceError(error_msg)

    def query_jupyterhub_api(
        self,
        method: str,
        api_path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_url = self.hub_api_url.rstrip("/") + "/"
        path = api_path.lstrip("/")
        url = urljoin(base_url, path)

        headers = {
            "Authorization": f"token {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            if response.ok:
                try:
                    return response.json()
                except ValueError as e:
                    raise JupyterHubApiError(
                        f"Invalid JSON response from JupyterHub API: {e}",
                        response.status_code,
                        response.text,
                    )

            error_msg = (
                f"JupyterHub API returned status {response.status_code} "
                f"for {method} {url}"
            )
            logger.error(f"{error_msg}: {response.text}")
            raise JupyterHubApiError(error_msg, response.status_code, response.text)

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s for {url}"
            logger.error(error_msg)
            raise JupyterHubApiError(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error for {url}: {e}"
            logger.error(error_msg)
            raise JupyterHubApiError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {e}"
            logger.error(error_msg)
            raise JupyterHubApiError(error_msg)

    def __enter__(self):
        return self