import psutil
from django.http import HttpResponse
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

# Custom metrics
CPU_USAGE = Gauge("system_cpu_usage_percent", "Current CPU usage percentage")
MEMORY_USAGE = Gauge("system_memory_usage_percent", "Current memory usage percentage")
DISK_USAGE = Gauge("system_disk_usage_percent", "Current disk usage percentage")

MEMORY_TOTAL = Gauge("system_memory_total_gb", "Total memory in GB")
MEMORY_USED = Gauge("system_memory_used_gb", "Used memory in GB")

DISK_TOTAL = Gauge("system_disk_total_gb", "Total disk size in GB")
DISK_USED = Gauge("system_disk_used_gb", "Disk used in GB")


def system_metrics(request):
    # CPU
    CPU_USAGE.set(psutil.cpu_percent(interval=1))

    # Memory
    memory = psutil.virtual_memory()
    MEMORY_USAGE.set(memory.percent)
    MEMORY_TOTAL.set(round(memory.total / (1024 ** 3), 2))
    MEMORY_USED.set(round(memory.used / (1024 ** 3), 2))

    # Disk
    disk = psutil.disk_usage('/')
    DISK_USAGE.set(disk.percent)
    DISK_TOTAL.set(round(disk.total / (1024 ** 3), 2))
    DISK_USED.set(round(disk.used / (1024 ** 3), 2))

    # Return Prometheus metrics
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
