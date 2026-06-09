/*
 * Jenkins Job DSL for creating the multibranch pipeline.
 *
 * Required Jenkins plugins:
 * - job-dsl
 * - workflow-multibranch
 * - github-branch-source
 */

def jobName = 'sample-pr-relay-multibranch'
def repoOwner = 'example-org'
def repoName = 'example-repo'
def credentialsId = 'github-repo-credentials'

multibranchPipelineJob(jobName) {
    displayName('Sample PR Relay Multibranch')
    description('Builds branches and pull requests when triggered by the webhook relay server.')

    branchSources {
        branchSource {
            source {
                github {
                    id("${repoOwner}-${repoName}")
                    repoOwner(repoOwner)
                    repository(repoName)
                    credentialsId(credentialsId)
                    configuredByUrl(false)
                    traits {
                        gitHubBranchDiscovery {
                            strategyId(1)
                        }
                        gitHubPullRequestDiscovery {
                            strategyId(1)
                        }
                        headWildcardFilter {
                            includes('*')
                            excludes('')
                        }
                    }
                }
            }
        }
    }

    factory {
        workflowBranchProjectFactory {
            scriptPath('Jenkinsfile')
        }
    }

    orphanedItemStrategy {
        discardOldItems {
            numToKeep(20)
        }
    }

    triggers {
        periodicFolderTrigger {
            interval('1d')
        }
    }
}
