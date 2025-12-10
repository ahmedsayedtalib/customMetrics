pipeline {
    agent any 
    environment {
        GITHUB_CRED  = "github-cred"
        GITHUB_URL   = "https://github.com/ahmedsayedtalib/customMetrics.git"
        GITHUB_USER  = "ahmedsayedtalib"
        SONAR_CRED   = "sonarqube-cred"
        SONAR_URL    = "http://192.168.103.2:32000"
        DOCKER_CRED  = "docker-cred"
        DOCKER_REPO  = "ahmedsayedtalib"
        DOCKER_IMAGE = "custommetrics"
        ARGOCD_URL   = "http://192.168.103.2:32200"
        ARGOCD_CRED  = "argocd-cred" 
    }
    stages{
         stage ("Checkout") {
            steps {
                git scm
            }
         }
         stage ("Unit test") {
            steps {
                sh """
                pytest -v metrics/tests/root_urls.py \ 
                metrics/tests/url_routing.py metrics/tests/settings_test.py \
                 metrics/tests/test_metrics.py 
                """
            }
         }
         stage ("Static Code Analysis") {
            steps {
                script {
                    def sonarHome = tool "sonar-scanner"
                    withSonarQubeEnv('sonar-scanner') {
                        withCredentials([string(credentialsId:SONAR_CRED,variable:"SONAR_TOKEN")]) {
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
                }
            }
         }
         stage ("Image Build & Push to Docker Repository") {
            steps {
                script {
                withCredentials([usernamePassword(credentialsId:DOCKER_CRED,usernameVariable:'USER',passwordVariable:'PASSWORD')]) {
                    sh """
                    echo ${PASSWORD} | docker login -u ${USER} --password-stdin 
                    docker build -t ${DOCKER_REPO}/${DOCKER_IMAGE} .
                    docker push ${DOCKER_REPO}/${DOCKER_IMAGE}
                    """
                   }
                }
            }
         }
         stage ("Manifest Update Image Tag") {
            steps {
                script {
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}"
                    sh "sed -i 's|image:.*|image:${DOCKER_REPO}/${DOCKER_IMAGE}:${IMAGE_TAG}' k8s/rollout.yaml"
                }
            }
         }
         stage ("Deploy with ArgoCD") {
            steps {
                script {
                    withCredentials([string(credentialsId:GITHUB_CRED,variable:"GITHUB_TOKEN")]) {
                        sh """
                        git config --global user.email 'Jenkins@cicd-automate.com'
                        git config --global user.name 'Jenkins CI/CD Automation'
                        git add k8s/rollout.yaml
                        git commit -m 'feat(ci):Update Image tag number to ${IMAGE_TAG} [skip ci]'
                        git push https://\${GITHUB_USER}:\${GITHUB_TOKEN}@github.com/ahmedsayedtalib/customMetrics.git HEAD:main
                        """
                    }
                    withCredentials([usernamePassword(credentialsId:ARGOCD_CRED,usernameVariable:"USER",passwordVariable:"PASSWORD")]) {
                        sh """
                        argocd login ${ARGOCD_URL} --username ${USER} --password ${PASSWORD} --insecure
                        argocd app sync ${DOCKER_IMAGE} --wait
                        """
                     }
                }
            }
        }       
    }
} 
