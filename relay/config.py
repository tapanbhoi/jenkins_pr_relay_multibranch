from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    webhook_provider: Literal["github"] = "github"
    webhook_secret: str = Field(..., min_length=8)

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
