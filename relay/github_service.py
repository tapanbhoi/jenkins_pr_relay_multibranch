from __future__ import annotations

import httpx

from relay.config import Settings


class GitHubService:
    """Service for interacting with GitHub API to post PR comments and commit statuses."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.token = settings.github_token
        self.base_url = "https://api.github.com"

    async def post_pr_comment(self, repo: str, pr_number: int, body: str) -> None:
        """Post a comment to a pull request."""
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={"body": body},
            )
            response.raise_for_status()

    async def update_commit_status(
        self,
        repo: str,
        sha: str,
        state: str,
        description: str,
        target_url: str = "",
        context: str = "Jenkins pipeline result",
    ) -> None:
        """Update commit status on GitHub."""
        url = f"{self.base_url}/repos/{repo}/statuses/{sha}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={
                    "state": state,
                    "description": description,
                    "context": context,
                    "target_url": target_url,
                },
            )
            response.raise_for_status()

# Made with Bob
