"""
모니터링 뷰
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings


@api_view(['GET'])
def monitoring_home(request):
    """모니터링 홈"""
    return Response({
        'message': 'NaruTalk 서비스 모니터링',
        'services': list(settings.MICROSERVICES.keys()),
        'endpoints': {
            'dashboard': '/monitoring/',
            'metrics': '/monitoring/metrics',
            'logs': '/monitoring/logs',
        }
    })


@api_view(['GET'])
def service_metrics(request):
    """서비스 메트릭"""
    # 실제로는 각 서비스의 메트릭을 수집해야 함
    return Response({
        'metrics': {
            'total_requests': 1000,
            'average_response_time': 150,
            'error_rate': 0.02,
            'uptime': '99.9%'
        },
        'services': {
            service: {
                'status': 'unknown',
                'requests': 0,
                'response_time': 0,
                'errors': 0
            }
            for service in settings.MICROSERVICES.keys()
        }
    })


@api_view(['GET'])
def service_logs(request):
    """서비스 로그"""
    # 실제로는 로그 파일을 읽어야 함
    return Response({
        'logs': [
            {
                'timestamp': '2024-01-01T00:00:00Z',
                'level': 'INFO',
                'service': 'router_agent',
                'message': 'Service started'
            },
            {
                'timestamp': '2024-01-01T00:01:00Z',
                'level': 'INFO',
                'service': 'document_agent',
                'message': 'Document indexed'
            }
        ]
    }) 