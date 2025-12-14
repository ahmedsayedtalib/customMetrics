pipeline {
    agent any

    environment {
        GITHUB_CRED     = "github-cred"
        GITHUB_URL      = "https://github.com/ahmedsayedtalib/customMetrics.git"

        DOCKER_CRED     = "docker-cred"
        DOCKER_REPO     = "ahmedsayedtalib"
        DOCKER_IMAGE    = "custommetrics"

        SONAR_CRED      = "sonarqube-cred"
        SONAR_URL       = "http://192.168.103.2:32000"

        ARGOCD_CRED     = "argocd-cred"
        ARGOCD_URL      = "http://192.168.103.2:32200"

        IMAGE_TAG       = "${env.BUILD_NUMBER}"

        K8S_NAMESPACE   = "monitoring"
        K8S_DEPLOYMENT  = "custommetrics"
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {

        stage("Checkout Source Code") {
            steps {
                git branch: 'main', credentialsId: GITHUB_CRED, url: GITHUB_URL
            }
        }

        stage("Unit Tests") {
            agent {
                docker { image "python:3.12"
                args "-u root" }
            }
            steps {
                dir('jenkinsDocker') {
                    sh """
                        pip install --no-cache-dir -r requirements.txt
                        pytest ../metrics/tests/* --maxfail=1 -v
                    """
                }
            }
            post {
                success { echo "✅ Unit tests passed" }
                failure { error "❌ Unit tests failed" }
            }
        }

        stage("Static Code Analysis") {
            steps {
                script {
                    def sonarHome = tool "sonar-scanner"
                    withSonarQubeEnv("sonarqube") {
                        withCredentials([
                            string(credentialsId: SONAR_CRED, variable: "SONAR_TOKEN")
                        ]) {
                            sh """
                                ${sonarHome}/bin/sonar-scanner \
                                  -Dsonar.projectKey=customMetrics \
                                  -Dsonar.host.url=${SONAR_URL} \
                                  -Dsonar.sources=. \
                                  -Dsonar.inclusions=**/*.py \
                                  -Dsonar.token=${SONAR_TOKEN}
                            """
                        }
                    }
                }
            }
            post {
                success { echo "✅ Sonar analysis passed" }
                failure { error "❌ Sonar analysis failed" }
            }
        }

        stage("Build & Push Docker Image") {
            steps {
                    withCredentials([
                        usernamePassword(
                            credentialsId: DOCKER_CRED,
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASS'
                        )
                    ]) {
                        sh """
                            echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin
                            docker build -t ${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG} .
                            docker push ${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}
                        """
                    }
                }
            post {
                success { echo "✅ Docker image built and pushed: ${IMAGE_TAG}" }
                failure { error "❌ Docker build/push failed" }
            }
        }

        stage("Update Kubernetes Manifest") {
            steps {
                sh """
                    sed -i 's|image:.*|image: ${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/rollout.yaml
                """
            }
            post {
                success { echo "✅ Manifest updated with new image tag" }
                failure { error "❌ Failed to update manifest" }
            }
        }

        stage("Push Manifest to GitHub") {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: GITHUB_CRED,
                        usernameVariable: "USER",
                        passwordVariable: "PASSWORD"
                    )]) {
                sh """
                    git config user.email "jenkins@example.com"
                    git config user.name  "Jenkins CI/CD Automation"
                    git add k8s/rollout.yaml
                    git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]" || echo "No changes"
                    git push https://${USER}:${PASSWORD}@github.com/${DOCKER_REPO}/customMetrics.git main
                """
                       }
                    }
            post {
                success { echo "✅ Manifest pushed to GitHub" }
                failure { echo "⚠️ Failed to push manifest (manual intervention may be required)" }
                }
            }
        }
        stage("ArgoCD Sync & Deploy") {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: ARGOCD_CRED,
                        usernameVariable: "ARGO_USER",
                        passwordVariable: "ARGO_PASS"
                    )
                ]) {
                    sh """
                        argocd login ${ARGOCD_URL} --username ${ARGO_USER} --password ${ARGO_PASS} --insecure
                        argocd app sync custommetrics --wait --prune
                    """
                }
            }
            post {
                success { echo "✅ ArgoCD sync succeeded" }
                failure {
                    echo "❌ ArgoCD sync failed - rolling back deployment"
                    sh "kubectl rollout undo deployment/${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE}"
                    error "Deployment rollback executed"
                }
            }
        }

        stage("Verify Deployment") {
            steps {
                sh """
                    kubectl rollout status deployment/${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE} --timeout=2m
                    kubectl get pods -n ${K8S_NAMESPACE}
                """
            }
            post {
                success { echo "✅ Deployment verified" }
                failure {
                    echo "❌ Deployment verification failed - rolling back"
                    sh "kubectl rollout undo deployment/${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE}"
                    error "Rollback done due to failed deployment verification"
                }
            }
        }

        stage("Load Testing (Optional)") {
            agent {
                docker { image "python:3.12"
                args "-u root" 
                }
            }
            steps {
                sh """
                    pip install locust
                    locust -f locust.py --headless -u 100 -r 10 --run-time 1m
                """
            }
            post {
                success { echo "✅ Load testing completed" }
                failure { echo "⚠️ Load testing failed (non-blocking)" }
            }
        }
    }

    post {
        always { echo "🔹 Pipeline finished: ${currentBuild.fullDisplayName}" }
        failure { echo "❌ Pipeline failed: ${currentBuild.fullDisplayName}" }
        success { echo "✅ Pipeline succeeded: ${currentBuild.fullDisplayName}" }
    }
}
