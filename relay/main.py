from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from relay.config import Settings, get_settings
from relay.github import (
    ALLOWED_PULL_REQUEST_ACTIONS,
    parse_pull_request_event,
    verify_github_signature,
)
from relay.jenkins import JenkinsClient

logger = logging.getLogger(__name__)

app = FastAPI(title="Jenkins PR Relay", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    body = await request.body()
    if not verify_github_signature(settings.webhook_secret, body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitHub webhook signature",
        )

    if x_github_event != "pull_request":
        return {"accepted": False, "reason": f"Ignored GitHub event {x_github_event}"}

    payload = await request.json()
    pull_request_event = parse_pull_request_event(payload)
    if pull_request_event.action not in ALLOWED_PULL_REQUEST_ACTIONS:
        return {
            "accepted": False,
            "reason": f"Ignored pull_request action {pull_request_event.action}",
        }

    logger.info(
        "Triggering Jenkins for %s PR #%s at %s",
        pull_request_event.repo_full_name,
        pull_request_event.pr_number,
        pull_request_event.commit_sha,
    )
    result = await JenkinsClient(settings).trigger_for_pull_request(pull_request_event)
    return {
        "accepted": True,
        "repository": pull_request_event.repo_full_name,
        "pr_number": pull_request_event.pr_number,
        "source_branch": pull_request_event.source_branch,
        "target_branch": pull_request_event.target_branch,
        **result,
    }
