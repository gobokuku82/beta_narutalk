"""
서비스 앱 URL 설정
"""
from django.urls import path
from . import views

urlpatterns = [
    # 홈 페이지
    path('', views.home_view, name='home'),
    
    # 채팅 API
    path('api/chat', views.ChatAPIView.as_view(), name='chat'),
    path('chat', views.ChatAPIView.as_view(), name='chat_alias'),
    
    # 헬스 체크
    path('api/health', views.HealthCheckView.as_view(), name='health'),
    path('health', views.HealthCheckView.as_view(), name='health_alias'),
    
    # 서비스 관리
    path('api/service/call', views.direct_service_call, name='direct_service_call'),
    path('api/service/status', views.service_status, name='service_status'),
] 