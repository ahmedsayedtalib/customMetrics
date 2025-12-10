from locust import HttpUser, task, between

class MetricsUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def get_metrics(self):
        self.client.get("/metrics/")
