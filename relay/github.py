from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any


ALLOWED_PULL_REQUEST_ACTIONS = {
    "opened",
    "reopened",
    "synchronize",
    "ready_for_review",
}


@dataclass(frozen=True)
class PullRequestEvent:
    action: str
    pr_number: int
    source_branch: str
    target_branch: str
    repo_full_name: str
    commit_sha: str


def verify_github_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def parse_pull_request_event(payload: dict[str, Any]) -> PullRequestEvent:
    pull_request = payload["pull_request"]
    return PullRequestEvent(
        action=payload["action"],
        pr_number=int(pull_request["number"]),
        source_branch=pull_request["head"]["ref"],
        target_branch=pull_request["base"]["ref"],
        repo_full_name=payload["repository"]["full_name"],
        commit_sha=pull_request["head"]["sha"],
    )
