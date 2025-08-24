from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path

from .exceptions import LTIConfigurationError


@dataclass
class LTIConfig:
    client_id: str
    platform_url: str
    token_url: str
    private_key: str
    platform: str

    lms_lti_url: str
    nrps_url: Optional[str] = None

    timeout: int = 30

    @classmethod
    def from_env(cls, prefix: str = "LTI_") -> "LTIConfig":
        def get_env(key: str, required: bool = True) -> Optional[str]:
            value = os.getenv(f"{prefix}{key}")
            if required and not value:
                raise LTIConfigurationError(f"Required environment variable {prefix}{key} not set")
            return value

        private_key_path = get_env("PRIVATE_KEY_PATH", required=False)
        private_key = get_env("PRIVATE_KEY", required=False)

        if private_key_path:
            try:
                private_key = Path(private_key_path).read_text()
            except Exception as e:
                raise LTIConfigurationError(f"Failed to read private key from {private_key_path}: {e}")
        elif not private_key:
            raise LTIConfigurationError("Either LTI_PRIVATE_KEY or LTI_PRIVATE_KEY_PATH must be set")

        return cls(
            client_id=get_env("CLIENT_ID"),
            platform_url=get_env("PLATFORM_URL"),
            token_url=get_env("TOKEN_URL"),
            private_key=private_key,
            platform=get_env("PLATFORM", required=False) or "canvas",
            lms_lti_url=get_env("LMS_LTI_URL"),
            nrps_url=get_env("NRPS_URL", required=False),
            timeout=int(get_env("TIMEOUT", required=False) or "30")
        )

    def validate(self) -> None:
        errors = []

        if not self.client_id:
            errors.append("client_id is required")
        if not self.platform_url:
            errors.append("platform_url is required")
        if not self.token_url:
            errors.append("token_url is required")
        if not self.private_key:
            errors.append("private_key is required")
        if not self.platform:
            errors.append("platform is required")
        elif self.platform not in ["canvas", "moodle"]:
            errors.append("platform must be 'canvas' or 'moodle'")
        if not self.lms_lti_url:
            errors.append("lms_lti_url is required")

        if self.timeout <= 0:
            errors.append("timeout must be positive")

        if errors:
            raise LTIConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")