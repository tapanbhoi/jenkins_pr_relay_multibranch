pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        skipDefaultCheckout(true)
    }

    environment {
        APP_NAME = 'sample-pr-app'
        SOURCE_DIR = '/Users/tapanbhoi/Documents/Container/jenkins_pr_relay_multibranch'
    }

    stages {
        stage('Source') {
            steps {
                sh '''
                    set -eu
                    test -f "${SOURCE_DIR}/Jenkinsfile"
                    git -C "${SOURCE_DIR}" rev-parse --short HEAD
                '''
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
                    cd "${SOURCE_DIR}"
                    python3 --version
                    PYTHONPYCACHEPREFIX=/tmp/jenkins-pr-relay-pycache python3 -m compileall relay tests scripts
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set -eu
                    cd "${SOURCE_DIR}"
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
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}
