pipeline {
    agent any
    environment {
        GITHUB_CRED     = "github-cred"
        GITHUB_URL      = "https://github.com/ahmedsayedtalib/customMetrics.git"
        GITHUB_USER     = "ahmedsayedtalib"
        SONAR_CRED      = "sonarqube-cred"
        SONAR_URL       = "http://192.168.103.2:32000"
        DOCKER_CRED     = "docker-cred"
        DOCKER_REPO     = "ahmedsayedtalib"
        DOCKER_IMAGE    = "custommetrics"
        ARGOCD_URL      = "http://192.168.103.2:32200"
        ARGOCD_CRED     = "argocd-cred"
        KUBERNETES_CRED = "kubernetes-cred"
    }

    stages {
        stage("Checkout") {
            steps {
                git branch: 'main',credentialsId: GITHUB_CRED, url: GITHUB_URL
            }
            post {
                success { echo "✅ Git checkout completed successfully" }
                failure { echo "❌ Git checkout failed" }
            }
        }

        stage("Unit Test") {
            steps {
                script {
                    try {
                        sh """
                        pytest -v metrics/tests/root_urls.py \
                        metrics/tests/url_routing.py metrics/tests/settings_test.py \
                        metrics/tests/test_metrics.py
                        """
                    } catch (Exception e) {
                        echo "❌ Pytest execution failed: ${e}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
            post {
                success { echo "✅ Unit tests passed successfully" }
                failure { echo "❌ Unit tests failed. Check test results." }
            }
        }

        stage("Static Code Analysis") {
            steps {
                script {
                    try {
                        def sonarHome = tool "sonar-scanner"
                        withSonarQubeEnv('sonarqube') {
                            withCredentials([string(credentialsId:SONAR_CRED, variable:"SONAR_TOKEN")]) {
                                sh """
                                ${sonarHome}/bin/sonar-scanner \
                                -Dsonar.host.url=${SONAR_URL} \
                                -Dsonar.projectKey='customMetrics' \
                                -Dsonar.sources=. \
                                -Dsonar.inclusions=**/*.py \
                                -Dsonar.token=${SONAR_TOKEN}
                                """
                            }
                        }
                    } catch (Exception e) {
                        echo "❌ SonarQube scan failed: ${e}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
            post {
                success { echo "✅ SonarQube analysis completed successfully" }
                failure { echo "❌ SonarQube analysis failed" }
            }
        }

        stage("Build & Push Docker Image") {
            steps {
                script {
                    try {
                        withCredentials([usernamePassword(credentialsId:DOCKER_CRED, usernameVariable:'USER', passwordVariable:'PASSWORD')]) {
                            sh """
                            echo ${PASSWORD} | docker login -u ${USER} --password-stdin
                            docker build -t ${DOCKER_REPO}/${DOCKER_IMAGE} .
                            docker push ${DOCKER_REPO}/${DOCKER_IMAGE}
                            """
                        }
                    } catch (Exception e) {
                        echo "❌ Docker build/push failed: ${e}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
            post {
                success { echo "✅ Docker image built and pushed successfully" }
                failure { echo "❌ Docker image build/push failed" }
            }
        }

        stage("Update Kubernetes Manifest") {
            steps {
                script {
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}"
                    sh "sed -i 's|image:.*|image:${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}' k8s/rollout.yaml"
                }
            }
            post {
                success { echo "✅ Kubernetes manifest updated with image tag ${env.IMAGE_TAG}" }
                failure { echo "❌ Failed to update Kubernetes manifest" }
            }
        }

        stage("Deploy with ArgoCD") {
            steps {
                script {
                    try {
                        withCredentials([string(credentialsId:GITHUB_CRED, variable:"GITHUB_TOKEN")]) {
                            sh """
                            git config --global user.email 'Jenkins@cicd-automate.com'
                            git config --global user.name 'Jenkins CI/CD Automation'
                            git add k8s/rollout.yaml
                            git commit -m 'feat(ci):Update Image tag number to ${IMAGE_TAG} [skip ci]' || echo "No changes to commit"
                            git push https://\${GITHUB_USER}:\${GITHUB_TOKEN}@github.com/ahmedsayedtalib/customMetrics.git HEAD:main
                            """
                        }

                        withCredentials([usernamePassword(credentialsId:ARGOCD_CRED, usernameVariable:"USER", passwordVariable:"PASSWORD")]) {
                            sh """
                            argocd login ${ARGOCD_URL} --username ${USER} --password ${PASSWORD} --insecure
                            argocd app sync custommetrics --wait
                            """
                        }
                    } catch (Exception e) {
                        echo "❌ ArgoCD deployment failed: ${e}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
            post {
                success { echo "✅ ArgoCD deployment succeeded" }
                failure { echo "❌ ArgoCD deployment failed. Check ArgoCD logs." }
            }
        }

        stage("Wait for Deployment") {
            steps {
                script {
                    try {
                        withCredentials([string(credentialsId:KUBERNETES_CRED, variable:"TOKEN")]) {
                            sh """
                            export KUBECONFIG=/tmp/kubeconfig_${BUILD_NUMBER}
                            kubectl config set-cluster local --server=https://kubernetes.default.svc --insecure-skip-tls-verify=true
                            kubectl config set-credentials sa-user --token=$TOKEN
                            kubectl config set-context sa-context --cluster=local --user=sa-user --namespace=monitoring
                            kubectl config use-context sa-context

                            kubectl rollout status deployment/custommetrics -n monitoring
                            kubectl get service custommetrics -n monitoring
                            """
                        }
                    } catch (Exception e) {
                        echo "❌ Deployment is not ready: ${e}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
            post {
                success { echo "✅ Deployment verified and ready" }
                failure { echo "❌ Deployment not ready. Skipping load test" }
            }
        }

        stage("Locust Load Test") {
            steps {
                script {
                    try {
                        sh """
                        locust -f locust.py --headless -u 100 -r 10 --run-time 1m
                        """
                    } catch (Exception e) {
                        echo "❌ Locust load test failed: ${e}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
            post {
                success { echo "✅ Locust load test completed successfully" }
                failure { echo "❌ Locust load test failed or deployment not ready" }
            }
        }
    }
}
