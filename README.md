# Jenkins PR Relay Multibranch Demo

This project demonstrates this flow:

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
Relay server triggers Jenkins multibranch pipeline
        |
        v
Jenkins scans PR branch and runs Jenkinsfile
```

## What Is Included

- `relay/`: FastAPI webhook relay server.
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
   - ID: `github-user-token`
   - Kind: Username with password
   - Username: your GitHub username
   - Password: a GitHub PAT
   - Required PAT permission: commit status read/write. For a classic PAT, use `repo:status` for public repositories or `repo` for private repositories. For a fine-grained PAT, grant repository access and `Commit statuses: Read and write`.

3. Create a new Jenkins item:
   - Type: `Multibranch Pipeline`
   - Branch source: your GitHub or Git repository
   - Discover branches: enabled
   - Discover pull requests: enabled
   - Script path: `Jenkinsfile`

You can also adapt `jenkins/multibranch-job-dsl.groovy` and run it from a Jenkins seed job to create the multibranch pipeline automatically.

4. Create a Jenkins API token for the relay user:
   - User menu
   - Configure
   - API Token
   - Add new token

5. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Set:

```text
WEBHOOK_SECRET=<same secret configured in the GitHub webhook>
JENKINS_URL=http://jenkins:8080
JENKINS_USER=<jenkins-user>
JENKINS_API_TOKEN=<jenkins-api-token>
JENKINS_MULTIBRANCH_JOB=<folder/job-name or job-name>
JENKINS_TRIGGER_MODE=scan
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

## Production Notes

- Put the relay behind HTTPS.
- Keep `WEBHOOK_SECRET` and `JENKINS_API_TOKEN` in a secret manager.
- Use a Jenkins service account with only the permissions required to trigger the multibranch job.
- Restrict inbound traffic to the relay where possible.
<<<<<<< HEAD
- Log delivery IDs and Jenkins queue URLs in a production implementation..
=======
- Log delivery IDs and Jenkins queue URLs in a production implementation.

>>>>>>> edac094 (test PR)
