def notifyGitHubStatus(String state, String description) {
    if (!env.GIT_COMMIT?.trim()) {
        echo "Skipping GitHub status update because GIT_COMMIT is not available yet."
        return
    }

    withCredentials([usernamePassword(
        credentialsId: 'github-user-token',
        usernameVariable: 'GITHUB_USER',
        passwordVariable: 'GITHUB_TOKEN'
    )]) {
        withEnv([
            "GH_STATE=${state}",
            "GH_DESCRIPTION=${description}",
            "GH_CONTEXT=Jenkins pipeline result",
            "GH_TARGET_URL=${env.BUILD_URL ?: ''}",
            "GH_COMMIT=${env.GIT_COMMIT}",
            "GH_CHANGE_ID=${env.CHANGE_ID ?: ''}",
            "GH_REPOSITORY=tapanbhoi/jenkins_pr_relay_multibranch"
        ]) {
            sh '''
                set +x
                python3 - <<'PY'
import json
import os
import sys
import urllib.request

repo = os.environ["GH_REPOSITORY"]
commit = os.environ["GH_COMMIT"]
change_id = os.environ.get("GH_CHANGE_ID", "").strip()
headers = {
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

if change_id:
    pr_url = f"https://api.github.com/repos/{repo}/pulls/{change_id}"
    pr_request = urllib.request.Request(pr_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(pr_request, timeout=20) as response:
            pull_request = json.loads(response.read().decode("utf-8"))
        commit = pull_request["head"]["sha"]
    except Exception as exc:
        print(f"GitHub PR head lookup failed, falling back to checkout commit: {exc}", file=sys.stderr)

url = f"https://api.github.com/repos/{repo}/statuses/{commit}"
payload = {
    "state": os.environ["GH_STATE"],
    "target_url": os.environ["GH_TARGET_URL"],
    "description": os.environ["GH_DESCRIPTION"][:140],
    "context": os.environ["GH_CONTEXT"],
}
request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print(f"GitHub status update: {response.status}")
except Exception as exc:
    print(f"GitHub status update failed: {exc}", file=sys.stderr)
    sys.exit(0)
PY
            '''
        }
    }
}

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        APP_NAME = 'sample-pr-app'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git rev-parse --short HEAD'
                script {
                    notifyGitHubStatus('pending', 'Jenkins pipeline is running')
                }
            }
        }

        stage('PR Metadata') {
            when {
                changeRequest()
            }
            steps {
                echo "PR #${env.CHANGE_ID}: ${env.CHANGE_BRANCH} -> ${env.CHANGE_TARGET}"
                echo "Author: ${env.CHANGE_AUTHOR}"
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    set -eu
                    python3 --version
                    PYTHONPYCACHEPREFIX=/tmp/jenkins-pr-relay-pycache python3 -m compileall relay tests scripts
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set -eu
                    if [ -d .venv ]; then . .venv/bin/activate; fi
                    if python3 -m pytest --version >/dev/null 2>&1; then
                        python3 -m pytest -q
                    else
                        echo "pytest is not installed on this Jenkins node; syntax validation already passed."
                    fi
                '''
            }
        }
    }

    post {
        always {
            echo "Build completed for ${env.BRANCH_NAME}"
        }
        success {
            echo 'Pipeline succeeded'
            script {
                notifyGitHubStatus('success', 'Jenkins pipeline success')
            }
        }
        failure {
            echo 'Pipeline failed'
            script {
                notifyGitHubStatus('failure', 'Jenkins pipeline failed')
            }
        }
        unstable {
            echo 'Pipeline unstable'
            script {
                notifyGitHubStatus('failure', 'Jenkins pipeline unstable')
            }
        }
        aborted {
            echo 'Pipeline aborted'
            script {
                notifyGitHubStatus('error', 'Jenkins pipeline aborted')
            }
        }
    }
}
