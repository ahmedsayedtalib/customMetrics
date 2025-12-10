import pytest
from django.urls import reverse
from prometheus_client.parser import text_string_to_metric_families


@pytest.mark.django_db
def test_metrics_view(client):
    """Ensure /metrics returns HTTP 200 and valid Prometheus metrics."""
    url = reverse("system_metrics")
    response = client.get(url)

    # 1) Check status code
    assert response.status_code == 200

    # 2) Check content type
    assert "text/plain" in response["Content-Type"]

    # 3) Parse Prometheus metrics and ensure required metrics exist
    metric_names = []
    for family in text_string_to_metric_families(response.content.decode()):
        metric_names.append(family.name)

    assert "system_cpu_usage_percent" in metric_names
    assert "system_memory_usage_percent" in metric_names
    assert "system_disk_usage_percent" in metric_names
