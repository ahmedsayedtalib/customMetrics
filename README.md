# CustomMetrics CI/CD Pipeline

This repository contains a **Jenkins pipeline** for automating the CI/CD workflow of the `customMetrics` Python project. The pipeline integrates **unit testing, static code analysis, Docker image building, Kubernetes deployment with ArgoCD**, and **performance testing with Locust**.

---

## Table of Contents

- [Pipeline Overview](#pipeline-overview)  
- [Prerequisites](#prerequisites)  
- [Environment Variables](#environment-variables)  
- [Pipeline Stages](#pipeline-stages)  
- [ArgoCD Setup](#argocd-setup)  
- [Jenkins Setup](#jenkins-setup)  
- [Locust Load Testing](#locust-load-testing)  
- [License](#license)  

---

## Pipeline Overview

The Jenkins pipeline automates the following workflow:

1. **Checkout:** Pulls the latest code from GitHub.  
2. **Unit Test:** Runs Python unit tests using `pytest`.  
3. **Static Code Analysis:** Uses SonarQube to perform code quality checks.  
4. **Build & Push Docker Image:** Builds the Docker image and pushes it to the Docker repository.  
5. **Update Kubernetes Manifest:** Updates the Kubernetes deployment manifest with the new Docker image tag.  
6. **Deploy with ArgoCD:** Pushes manifest changes to GitHub and synchronizes the application via ArgoCD.  
7. **Wait for Deployment:** Verifies that Kubernetes deployment and service are ready.  
8. **Locust Load Test:** Performs a headless load test against the deployed service.

Each stage includes **post-success and post-failure notifications** to improve traceability and debugging.

---

## Prerequisites

Before running the pipeline, ensure the following:

- **Jenkins** installed with the required plugins (`Pipeline`, `Credentials Binding`, `Git`, etc.)  
- **Python 3** installed with `pytest` and `locust`  
- **Docker** installed and configured  
- **Kubernetes cluster** (Minikube or production)  
- **ArgoCD** installed and accessible  
- **SonarQube** server for code analysis  

---

## Environment Variables

The pipeline uses the following Jenkins environment variables:

| Variable | Description |
|----------|-------------|
| `GITHUB_CRED` | Jenkins credential ID for GitHub access |
| `GITHUB_URL` | GitHub repository URL |
| `GITHUB_USER` | GitHub username |
| `SONAR_CRED` | Jenkins credential ID for SonarQube token |
| `SONAR_URL` | SonarQube server URL |
| `DOCKER_CRED` | Jenkins credential ID for Docker login |
| `DOCKER_REPO` | Docker repository username |
| `DOCKER_IMAGE` | Docker image name |
| `ARGOCD_URL` | ArgoCD server URL |
| `ARGOCD_CRED` | Jenkins credential ID for ArgoCD login |
| `KUBERNETES_CRED` | Jenkins credential ID for Kubernetes ServiceAccount token |

---

## Pipeline Stages

### 1. Checkout
Pulls the latest code from GitHub.

### 2. Unit Test
Runs `pytest` on the project's test files. Failures are marked in the build.

### 3. Static Code Analysis
Executes SonarQube scanner to verify code quality and coverage.

### 4. Build & Push Docker Image
Builds the Docker image with the Jenkins build number as a tag and pushes it to Docker Hub.

### 5. Update Kubernetes Manifest
Updates `rollout.yaml` with the newly built Docker image tag.

### 6. Deploy with ArgoCD
Commits manifest changes to GitHub and synchronizes the application using ArgoCD.

### 7. Wait for Deployment
Verifies the deployment rollout and checks that the service is available in Kubernetes.

### 8. Locust Load Test
Performs a headless Locust load test to validate application performance.

---

## ArgoCD Setup

1. Create the application in ArgoCD:

```bash
argocd app create custommetrics \
  --repo https://github.com/ahmedsayedtalib/customMetrics.git \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace monitoring \
  --sync-policy automated
