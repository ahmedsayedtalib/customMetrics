from .views import system_metrics
from django.urls import path


urlpatterns = [
    path('metrics/',system_metrics,name='system_metrics')
]