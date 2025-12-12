pipeline {
    agent any
    environment {
        GITHUB_CRED     = "github-cred"
        GITHUB_URL      = "https://github.com/ahmedsayedtalib/customMetrics.git"
        DOCKER_CRED     = "docker-cred"
        DOCKER_REPO     = "ahmedsayedtalib"
        DOCKER_IMAGE    = "custommetrics"
        ARGOCD_URL      = "http://192.168.103.2:32200"
        ARGOCD_CRED     = "argocd-cred"
        SONAR_CRED      = "sonarqube-cred"
        SONAR_URL       = "http://192.168.103.2:32000"
        IMAGE_TAG       = "${env.BUILD_NUMBER}"
        K8S_NAMESPACE   = "monitoring"
        K8S_DEPLOYMENT  = "custommetrics"
    }

    stages {

        stage("Checkout") {
            steps {
                git branch: 'main', credentialsId: GITHUB_CRED, url: GITHUB_URL
            }
        }

        stage("Build Docker Image & Unit Tests") {
            steps {
                dir('jenkinsDocker') {
                    script {
                        withCredentials([usernamePassword(credentialsId:DOCKER_CRED, usernameVariable:"USER", passwordVariable:"PASSWORD")]) {
                            sh """
                                echo ${PASSWORD} | docker login -u ${USER} --password-stdin
                                # Build test Docker image
                                docker build -t ${DOCKER_REPO}/${DOCKER_IMAGE}:test .
                                # Run unit tests inside the image
                                docker run --rm ${DOCKER_REPO}/${DOCKER_IMAGE}:test pytest metrics/tests/ --maxfail=1 --disable-warnings -v
                                # Tag production image
                                docker tag ${DOCKER_REPO}/${DOCKER_IMAGE}:test ${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}
                                # Push production image
                                docker push ${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}
                            """
                        }
                    }
                }
            }
            post {
                success { echo "✅ Docker build & unit tests succeeded" }
                failure { error "❌ Docker build or unit tests failed" }
            }
        }

        stage("Static Code Analysis") {
            steps {
                script {
                    def sonarHome = tool "sonar-scanner"
                    withSonarQubeEnv("sonarqube") {
                        withCredentials([string(credentialsId:SONAR_CRED, variable:"SONAR_TOKEN")]) {
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
        }

        stage("Update Kubernetes Manifest") {
            steps {
                sh """
                    sed -i 's|image:.*|image:${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/rollout.yaml
                """
            }
        }

        stage("Push Manifest to GitHub") {
            steps {
                script {
                    sh """
                        git config --global user.email 'jenkins@example.com'
                        git config --global user.name 'Jenkins CI/CD Automation'
                        git add k8s/rollout.yaml
                        git commit -m "feat(ci): update image tag to ${IMAGE_TAG} [skip ci]" || echo "No changes to commit"
                        git push origin main
                    """
                }
            }
        }

        stage("ArgoCD Deployment") {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId:ARGOCD_CRED, usernameVariable:"USER", passwordVariable:"PASSWORD")]) {
                        sh """
                            argocd login ${ARGOCD_URL} --username ${USER} --password ${PASSWORD} --insecure
                            argocd app sync custommetrics --wait --insecure
                        """
                    }
                }
            }
        }

        stage("Wait for Deployment") {
            steps {
                sh """
                    kubectl rollout status deployment/${K8S_DEPLOYMENT} -n ${K8S_NAMESPACE} --timeout=2m
                    kubectl get pods -n ${K8S_NAMESPACE}
                """
            }
        }

        stage("Load Testing") {
            agent {
                docker { image: "${DOCKER_REPO}/${DOCKER_IMAGE}:test" }
            }
            steps {
                sh """
                    kubectl wait --for=condition=Ready pods --all -n ${K8S_NAMESPACE} --timeout=2m
                    locust -f locust.py --headless -u 100 -r 10 --run-time 1m
                """
            }
        }

    }
}
