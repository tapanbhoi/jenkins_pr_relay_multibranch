from __future__ import annotations

from urllib.parse import quote

import httpx

from relay.config import Settings
from relay.github import PullRequestEvent


class JenkinsClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.jenkins_url.rstrip("/")
        self.auth = (settings.jenkins_user, settings.jenkins_api_token)

    async def trigger_for_pull_request(self, event: PullRequestEvent) -> dict[str, str | int]:
        if self.settings.jenkins_trigger_mode == "branch-build":
            path = self._job_path(
                self.settings.jenkins_multibranch_job,
                f"{self.settings.jenkins_branch_job_prefix}{event.pr_number}",
            )
        else:
            path = self._job_path(self.settings.jenkins_multibranch_job)

        async with httpx.AsyncClient(
            auth=self.auth,
            timeout=self.settings.request_timeout_seconds,
            verify=self.settings.jenkins_verify_tls,
        ) as client:
            crumb_header = await self._crumb_header(client)
            response = await client.post(
                f"{self.base_url}/{path}",
                headers=crumb_header,
            )
            response.raise_for_status()

        return {
            "jenkins_status": response.status_code,
            "trigger_mode": self.settings.jenkins_trigger_mode,
            "job_path": path,
        }

    async def _crumb_header(self, client: httpx.AsyncClient) -> dict[str, str]:
        response = await client.get(f"{self.base_url}/crumbIssuer/api/json")
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        data = response.json()
        return {data["crumbRequestField"]: data["crumb"]}

    @staticmethod
    def _job_path(*jobs: str, action: str = "build") -> str:
        segments: list[str] = []
        for job in jobs:
            for piece in job.strip("/").split("/"):
                if piece:
                    segments.extend(["job", quote(piece, safe="")])
        segments.append(action)
        return "/".join(segments)
