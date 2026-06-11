from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    webhook_provider: Literal["github"] = "github"
    webhook_secret: str = Field(..., min_length=8)

    # GitHub API configuration for posting PR feedback
    github_token: str = Field(..., description="GitHub Personal Access Token with repo scope")

    jenkins_url: str = Field(..., description="Base Jenkins URL, for example http://jenkins:8080")
    jenkins_user: str
    jenkins_api_token: str
    jenkins_multibranch_job: str = Field(
        ...,
        description="Jenkins multibranch folder/job path, for example folder/my-app",
    )
    jenkins_trigger_mode: Literal["scan", "branch-build"] = "scan"
    jenkins_branch_job_prefix: str = "PR-"
    jenkins_verify_tls: bool = True
    request_timeout_seconds: int = 20

    # Jenkins polling configuration for monitoring build results
    jenkins_poll_interval_seconds: int = Field(
        default=10,
        description="How often to poll Jenkins for build status (seconds)",
    )
    jenkins_poll_timeout_seconds: int = Field(
        default=3600,
        description="Maximum time to wait for build completion (seconds)",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
