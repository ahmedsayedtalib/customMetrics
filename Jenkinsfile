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

        KUBERNETES_CRED = "kubernetes-cred"

        ARGOCD_CRED     = "argocd-cred"
        ARGOCD_URL      = "https://192.168.103.2:32300"
        ARGOCD_ADDRESS  = "192.168.103.2:32300"

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
                        try {
                sh '''
                    git config user.email "jenkins@example.com"
                    git config user.name  "Jenkins CI/CD Automation"
                    git add k8s/rollout.yaml
                    git commit -m "ci: update image tag to $IMAGE_TAG [skip ci]" || echo "No changes"
                    git push https://$USER:$PASSWORD@github.com/$DOCKER_REPO/customMetrics.git main
                '''
                        }
                        catch (Exception e) {
                            echo "GitHub push failed: ${e.getMessage()}"
                            throw e
                        }
                       }
                    }
            }
            post {
                success { echo "✅ New Manifest push passed. Tag Number: ${IMAGE_TAG}" }
                failure { error "❌ New Manifest push failed" }
            }
        }
        stage("ArgoCD Sync & Deploy") {
            steps {
                script {
                withCredentials([
                    usernamePassword(
                        credentialsId: ARGOCD_CRED,
                        usernameVariable: "ARGO_USER",
                        passwordVariable: "ARGO_PASS"
                    )
                ]) {
                    try {
                    sh """
                        argocd logout ${ARGOCD_ADDRESS} || true
                        argocd login ${ARGOCD_ADDRESS} --username ${ARGO_USER} --password ${ARGO_PASS} --insecure
                        argocd app sync custommetrics --prune
                        argocd app wait custommetrics --sync --timeout 300
                    """
                    }
                    catch (Exception e) {
                        echo "Rollout Deployment Failed: ${e.getMessage()}"
                        throw e
                        currentBuild.result = 'FAILURE'
                        }
                    }
                }
            }
            post {
                success { echo "✅ ArgoCD sync succeeded" }
                failure {
                    echo "❌ ArgoCD sync failed - rolling back deployment"
                    sh "argocd app rollback custommetrics"
                    error "Deployment rollback executed"
                }
            }
        }
        stage("Verify Deployment") {
    steps {
        script {
            withCredentials([file(credentialsId: KUBERNETES_CRED, variable: 'KUBECONFIG_FILE')]) {
                try {
                    sh '''
                        export KUBECONFIG=$KUBECONFIG_FILE
                        curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
                        chmod +x kubectl-argo-rollouts-linux-amd64
                        mkdir -p $WORKSPACE/bin
                        mv kubectl-argo-rollouts-linux-amd64 $WORKSPACE/bin/kubectl-argo-rollouts
                        export PATH=$WORKSPACE/bin:$PATH
                        kubectl-argo-rollouts status custom-metrics-rollout -n monitoring --timeout 2m
                        kubectl -n monitoring get rollouts.argoproj.io
                    '''
                }
                catch (Exception e) {
                    echo "Error connecting to the cluster: ${e.getMessage()}"
                    currentBuild.result = 'UNSTABLE'
                }
            }
        }
    }
    post {
        success { echo "✅ Verifying the rollout from Kubernetes was successful" }
        failure { echo "⚠️ Could Not Verify rollout status. Please check via kubectl command" }
    }
}



       stage("Load Testing") {
    steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
            script {
                withCredentials([file(credentialsId: 'kubernetes-cred', variable: 'KUBECONFIG_FILE')]) {

                    def SERVICE_HOST = sh(
                        script: """
                            export KUBECONFIG=${KUBECONFIG_FILE}
                            kubectl get svc custom-metrics-service \
                              -n ${K8S_NAMESPACE} \
                              -o jsonpath='{.spec.clusterIP}'
                        """,
                        returnStdout: true
                    ).trim()

                    docker.image("python:3.12").inside("-u root") {
                        sh """
                            pip install --no-cache-dir locust
                            locust -f locust.py \
                              --headless \
                              -u 100 \
                              -r 10 \
                              --host=http://${SERVICE_HOST}:80 \
                              --run-time 1m
                        """
                    }
                }
            }
        }
    }
}

    }

    post {
        always { echo "🔹 Pipeline finished: ${currentBuild.fullDisplayName}" }
        failure { echo "❌ Pipeline failed: ${currentBuild.fullDisplayName}" }
        success { echo "✅ Pipeline succeeded: ${currentBuild.fullDisplayName}" }
    }
}
