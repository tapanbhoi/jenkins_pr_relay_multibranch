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
                    python3 -m compileall relay
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set -eu
                    if [ -d .venv ]; then . .venv/bin/activate; fi
                    python3 -m pytest -q
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
