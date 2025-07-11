"""
모니터링 앱 URL 설정
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.monitoring_home, name='monitoring_home'),
    path('metrics', views.service_metrics, name='service_metrics'),
    path('logs', views.service_logs, name='service_logs'),
] 