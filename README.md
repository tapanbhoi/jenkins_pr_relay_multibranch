# Jenkins PR Relay Multibranch with PR Feedback

This project demonstrates a complete webhook relay flow with PR feedback:

```text
Developer opens or updates PR
        |
        v
GitHub webhook sends pull_request event
        |
        v
Relay server validates signature and filters PR action
        |
        v
Relay server posts "pending" status to PR
        |
        v
Relay server triggers Jenkins multibranch pipeline
        |
        v
Relay server waits for Jenkins build to start
        |
        v
Relay server posts PR comment with build URL
        |
        v
Relay server polls Jenkins for build completion
        |
        v
Relay server posts final status and result comment to PR
```

## What Is Included

- `relay/`: FastAPI webhook relay server with PR feedback functionality.
  - `main.py`: Webhook endpoint and background task orchestration.
  - `github.py`: GitHub webhook signature verification and PR event parsing.
  - `github_service.py`: GitHub API client for posting PR comments and commit statuses.
  - `jenkins.py`: Jenkins API client with polling for build results.
  - `config.py`: Pydantic-based configuration management.
- `Jenkinsfile`: Pipeline definition used by the multibranch job.
- `jenkins/multibranch-job-dsl.groovy`: Jenkins Job DSL example for creating the multibranch job.
- `Dockerfile`: Container image for the relay service.
- `docker-compose.yml`: Local Jenkins plus relay stack.
- `.env.example`: Required relay configuration.
- `scripts/send_sample_github_pr_webhook.py`: Local signed webhook test helper.
- `tests/`: Unit tests for signature validation, PR parsing, and Jenkins path generation.

## Jenkins Setup

1. Install these Jenkins plugins:
   - Git
   - Pipeline
   - Multibranch Scan Webhook Trigger, optional if Jenkins also receives webhooks directly
   - GitHub Branch Source, if the repository is hosted on GitHub

2. Create a Jenkins credential for the Git repository.

3. Create a new Jenkins item:
   - Type: `Multibranch Pipeline`
   - Branch source: your GitHub or Git repository
   - Discover branches: enabled
   - Discover pull requests: enabled
   - Script path: `Jenkinsfile`

Jenkins stores discovered pull request jobs as `PR-<number>` internally, for example `PR-5`. Depending on the GitHub Branch Source plugin metadata, the Pull Requests table can show the GitHub PR title as the display name, while the job URL and full project name remain `PR-<number>`.

You can also adapt `jenkins/multibranch-job-dsl.groovy` and run it from a Jenkins seed job to create the multibranch pipeline automatically.

4. Create a Jenkins API token for the relay user:
   - User menu
   - Configure
   - API Token
   - Add new token

5. Generate a GitHub Personal Access Token:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control of private repositories)
   - Copy the token (starts with `ghp_`)

6. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Set:

```text
WEBHOOK_SECRET=<same secret configured in the GitHub webhook>
GITHUB_TOKEN=ghp_your_github_personal_access_token_here
JENKINS_URL=http://jenkins:8080
JENKINS_USER=<jenkins-user>
JENKINS_API_TOKEN=<jenkins-api-token>
JENKINS_MULTIBRANCH_JOB=torch-spyre
JENKINS_TRIGGER_MODE=scan
JENKINS_POLL_INTERVAL_SECONDS=10
JENKINS_POLL_TIMEOUT_SECONDS=3600
```

## GitHub Webhook Setup

In the GitHub repository:

1. Go to `Settings` > `Webhooks` > `Add webhook`.
2. Payload URL: `https://<relay-host>/webhooks/github`.
3. Content type: `application/json`.
4. Secret: same value as `WEBHOOK_SECRET`.
5. Events: choose `Pull requests`.

The relay accepts these PR actions:

- `opened`
- `reopened`
- `synchronize`
- `ready_for_review`

Other GitHub events and PR actions are ignored.

## Trigger Modes

Use `JENKINS_TRIGGER_MODE=scan` for the normal multibranch flow. The relay posts to:

```text
/job/<multibranch>/build
```

Jenkins then scans the repo and discovers or updates the PR branch job.

Use `JENKINS_TRIGGER_MODE=branch-build` only when Jenkins has already discovered the PR branch job. The relay posts to:

```text
/job/<multibranch>/job/PR-<number>/build
```

## Run Locally

```bash
cd jenkins_pr_relay_multibranch
cp .env.example .env
docker compose up --build
```

Open Jenkins at:

```text
http://localhost:8080
```

Open relay health check:

```text
http://localhost:8000/health
```

## Send A Sample Signed Webhook

After Jenkins and the relay are configured:

```bash
python3 scripts/send_sample_github_pr_webhook.py \
  --secret change-this-to-a-long-random-secret \
  --pr 12
```

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn relay.main:app --reload
```

## PR Feedback Features

The relay server now provides complete feedback to GitHub PRs:

1. **Commit Status Updates**: Posts "pending", "success", "failure", or "error" status to the PR commit
2. **PR Comments**: Posts comments with:
   - Initial trigger notification with build URL
   - Final result with build status, duration, and link
   - Error messages if relay fails
3. **Background Processing**: Uses FastAPI BackgroundTasks to avoid blocking webhook responses
4. **Jenkins Polling**: Monitors Jenkins queue and build status until completion

### Example PR Comment

When a PR is opened or updated, the relay posts:

```markdown
## 🚀 Jenkins Pipeline Triggered

**Branch:** `feature-branch`
**Commit:** `abc123def456`
**Jenkins Build:** https://jenkins.example.com/job/torch-spyre/job/PR-123/1/

Waiting for Jenkins result...
```

After completion:

```markdown
## ✅ Jenkins Pipeline Completed

**Result:** SUCCESS
**Branch:** `feature-branch`
**Commit:** `abc123def456`
**Duration:** 5 minutes
**Jenkins Build:** https://jenkins.example.com/job/torch-spyre/job/PR-123/1/
```

## Production Notes

- Put the relay behind HTTPS.
- Keep `WEBHOOK_SECRET`, `GITHUB_TOKEN`, and `JENKINS_API_TOKEN` in a secret manager.
- Use a Jenkins service account with only the permissions required to trigger the multibranch job.
- Use a GitHub token with minimal required scopes (`repo` for private repos, `public_repo` for public repos).
- Restrict inbound traffic to the relay where possible.
- Log delivery IDs and Jenkins queue URLs in a production implementation.
- Adjust `JENKINS_POLL_TIMEOUT_SECONDS` based on your typical build duration.


## PR Feedback Features

The relay server now provides complete feedback to GitHub PRs:

1. **Commit Status Updates**: Posts "pending", "success", "failure", or "error" status to the PR commit
2. **PR Comments**: Posts comments with:
   - Initial trigger notification with build URL
   - Final result with build status, duration, and link
   - Error messages if relay fails
3. **Background Processing**: Uses FastAPI BackgroundTasks to avoid blocking webhook responses
4. **Jenkins Polling**: Monitors Jenkins queue and build status until completion

### Example PR Comment

When a PR is opened or updated, the relay posts:

```markdown
## 🚀 Jenkins Pipeline Triggered

**Branch:** `feature-branch`  
**Commit:** `abc123def456`  
**Jenkins Build:** https://jenkins.example.com/job/torch-spyre/job/PR-123/1/

Waiting for Jenkins result...
```

After completion:

```markdown
## ✅ Jenkins Pipeline Completed

**Result:** SUCCESS  
**Branch:** `feature-branch`  
**Commit:** `abc123def456`  
**Duration:** 5 minutes  
**Jenkins Build:** https://jenkins.example.com/job/torch-spyre/job/PR-123/1/
```
