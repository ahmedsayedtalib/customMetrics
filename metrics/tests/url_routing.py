from django.urls import resolve
from metrics.views import system_metrics


def test_metrics_url_routing():
    resolver = resolve("/metrics/")
    assert resolver.func == system_metrics
