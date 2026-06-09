import hashlib
import hmac

from relay.github import parse_pull_request_event, verify_github_signature


def test_verify_github_signature_accepts_valid_signature() -> None:
    secret = "super-secret"
    body = b'{"action":"opened"}'
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    assert verify_github_signature(secret, body, f"sha256={signature}")


def test_verify_github_signature_rejects_invalid_signature() -> None:
    assert not verify_github_signature("super-secret", b"{}", "sha256=bad")


def test_parse_pull_request_event() -> None:
    event = parse_pull_request_event(
        {
            "action": "opened",
            "repository": {"full_name": "example-org/example-repo"},
            "pull_request": {
                "number": 42,
                "head": {"ref": "feature/pr-relay", "sha": "abc123"},
                "base": {"ref": "main"},
            },
        }
    )

    assert event.action == "opened"
    assert event.pr_number == 42
    assert event.source_branch == "feature/pr-relay"
    assert event.target_branch == "main"
    assert event.repo_full_name == "example-org/example-repo"
    assert event.commit_sha == "abc123"
