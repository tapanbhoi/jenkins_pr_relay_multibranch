from relay.config import Settings
from relay.github import PullRequestEvent
from relay.jenkins import JenkinsClient


def settings(trigger_mode: str = "scan") -> Settings:
    return Settings(
        webhook_secret="super-secret",
        github_token="github-token",
        jenkins_url="http://jenkins.example",
        jenkins_user="bot",
        jenkins_api_token="token",
        jenkins_multibranch_job="folder/example-repo",
        jenkins_trigger_mode=trigger_mode,
    )


def test_scan_job_path_encodes_folder_multibranch_job() -> None:
    path = JenkinsClient._job_path(settings().jenkins_multibranch_job)

    assert path == "job/folder/job/example-repo/build"


def test_branch_build_path_uses_pr_branch_name() -> None:
    client = JenkinsClient(settings("branch-build"))
    event = PullRequestEvent(
        action="opened",
        pr_number=42,
        source_branch="feature/pr-relay",
        target_branch="main",
        repo_full_name="example-org/example-repo",
        commit_sha="abc123",
    )

    path = client._job_path(
        client.settings.jenkins_multibranch_job,
        f"{client.settings.jenkins_branch_job_prefix}{event.pr_number}",
    )

    assert path == "job/folder/job/example-repo/job/PR-42/build"
