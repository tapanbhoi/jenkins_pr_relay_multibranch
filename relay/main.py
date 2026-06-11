from __future__ import annotations

import logging

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, status

from relay.config import Settings, get_settings
from relay.github import (
    ALLOWED_PULL_REQUEST_ACTIONS,
    PullRequestEvent,
    parse_pull_request_event,
    verify_github_signature,
)
from relay.github_service import GitHubService
from relay.jenkins import JenkinsClient

logger = logging.getLogger(__name__)

app = FastAPI(title="Jenkins PR Relay", version="1.0.0")


async def run_jenkins_and_report(
    event: PullRequestEvent,
    settings: Settings,
) -> None:
    """Background task to trigger Jenkins, wait for result, and report back to PR."""
    github_service = GitHubService(settings)
    jenkins_client = JenkinsClient(settings)

    try:
        # Post initial pending status
        await github_service.update_commit_status(
            repo=event.repo_full_name,
            sha=event.commit_sha,
            state="pending",
            description="Jenkins pipeline triggered",
            target_url="",
        )

        # Trigger Jenkins build
        trigger_result = await jenkins_client.trigger_for_pull_request(event)
        queue_url = trigger_result.get("queue_url", "")

        if not queue_url:
            raise ValueError("Jenkins did not return queue URL")

        # Wait for build to start
        build_url = await jenkins_client.get_build_url_from_queue(queue_url)

        # Post comment with build URL
        await github_service.post_pr_comment(
            repo=event.repo_full_name,
            pr_number=event.pr_number,
            body=f"""## 🚀 Jenkins Pipeline Triggered

**Branch:** `{event.source_branch}`
**Commit:** `{event.commit_sha}`
**Jenkins Build:** {build_url}

Waiting for Jenkins result...
""",
        )

        # Wait for build to complete
        build_result = await jenkins_client.wait_for_build_result(build_url)

        jenkins_result = build_result["result"]
        state = "success" if jenkins_result == "SUCCESS" else "failure"

        # Update commit status with final result
        await github_service.update_commit_status(
            repo=event.repo_full_name,
            sha=event.commit_sha,
            state=state,
            description=f"Jenkins result: {jenkins_result}",
            target_url=build_url,
        )

        # Post final comment
        icon = "✅" if jenkins_result == "SUCCESS" else "❌"
        duration_min = build_result.get("duration", 0) // 60000

        await github_service.post_pr_comment(
            repo=event.repo_full_name,
            pr_number=event.pr_number,
            body=f"""## {icon} Jenkins Pipeline Completed

**Result:** {jenkins_result}
**Branch:** `{event.source_branch}`
**Commit:** `{event.commit_sha}`
**Duration:** {duration_min} minutes
**Jenkins Build:** {build_url}
""",
        )

        logger.info(
            "Jenkins pipeline completed for %s PR #%s: %s",
            event.repo_full_name,
            event.pr_number,
            jenkins_result,
        )

    except Exception as error:
        logger.exception("Failed to trigger or monitor Jenkins for PR #%s", event.pr_number)

        # Post error status
        await github_service.update_commit_status(
            repo=event.repo_full_name,
            sha=event.commit_sha,
            state="error",
            description="Relay server failed to trigger or monitor Jenkins",
            target_url="",
        )

        # Post error comment
        await github_service.post_pr_comment(
            repo=event.repo_full_name,
            pr_number=event.pr_number,
            body=f"""## ❌ Jenkins Relay Server Failed

Relay server could not complete Jenkins trigger/result tracking.

**Error:** `{error}`
""",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
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
        "Accepted PR webhook for %s PR #%s at %s",
        pull_request_event.repo_full_name,
        pull_request_event.pr_number,
        pull_request_event.commit_sha,
    )

    # Start background task to trigger Jenkins and report results
    background_tasks.add_task(run_jenkins_and_report, pull_request_event, settings)

    return {
        "accepted": True,
        "message": "Jenkins trigger started in background",
        "repository": pull_request_event.repo_full_name,
        "pr_number": pull_request_event.pr_number,
        "source_branch": pull_request_event.source_branch,
        "target_branch": pull_request_event.target_branch,
    }
