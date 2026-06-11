from __future__ import annotations

import asyncio
import time
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
        """Trigger Jenkins build for a pull request and return queue URL."""
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
                follow_redirects=False,
            )
            response.raise_for_status()

            # Get queue URL from Location header
            queue_url = response.headers.get("Location", "")

        return {
            "jenkins_status": response.status_code,
            "trigger_mode": self.settings.jenkins_trigger_mode,
            "job_path": path,
            "queue_url": queue_url,
        }

    async def get_build_url_from_queue(self, queue_url: str) -> str:
        """Poll Jenkins queue until build starts and return build URL."""
        if not queue_url:
            raise ValueError("Queue URL is empty")

        queue_api = f"{queue_url.rstrip('/')}/api/json"
        timeout_at = time.time() + 120  # 2 minutes timeout for queue

        async with httpx.AsyncClient(
            auth=self.auth,
            timeout=30,
            verify=self.settings.jenkins_verify_tls,
        ) as client:
            while time.time() < timeout_at:
                try:
                    response = await client.get(queue_api)
                    response.raise_for_status()
                    data = response.json()

                    executable = data.get("executable")
                    if executable and executable.get("url"):
                        return executable["url"]

                    await asyncio.sleep(5)
                except httpx.HTTPError:
                    await asyncio.sleep(5)

        raise TimeoutError("Timed out waiting for Jenkins queue item to start build")

    async def wait_for_build_result(self, build_url: str) -> dict[str, str | int]:
        """Poll Jenkins build until completion and return result."""
        if not build_url:
            raise ValueError("Build URL is empty")

        build_api = f"{build_url.rstrip('/')}/api/json"
        timeout_at = time.time() + self.settings.jenkins_poll_timeout_seconds

        async with httpx.AsyncClient(
            auth=self.auth,
            timeout=30,
            verify=self.settings.jenkins_verify_tls,
        ) as client:
            while time.time() < timeout_at:
                try:
                    response = await client.get(build_api)
                    response.raise_for_status()
                    data = response.json()

                    if not data.get("building", True):
                        return {
                            "result": data.get("result", "UNKNOWN"),
                            "url": build_url,
                            "number": data.get("number"),
                            "duration": data.get("duration", 0),
                        }

                    await asyncio.sleep(self.settings.jenkins_poll_interval_seconds)
                except httpx.HTTPError:
                    await asyncio.sleep(self.settings.jenkins_poll_interval_seconds)

        raise TimeoutError("Timed out waiting for Jenkins build to complete")

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
