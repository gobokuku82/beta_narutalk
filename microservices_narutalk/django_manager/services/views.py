"""
서비스 API 뷰
"""
import json
import asyncio
import logging
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .service_client import service_client

logger = logging.getLogger(__name__)


def async_view(func):
    """비동기 뷰 데코레이터"""
    def wrapper(request, *args, **kwargs):
        return asyncio.run(func(request, *args, **kwargs))
    return wrapper


@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    """채팅 API 뷰"""
    
    @async_view
    async def post(self, request):
        """채팅 메시지 처리"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            
            if not message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # 1. 고도화된 라우터 에이전트에서 의도 분석 (GPT-4o 기반)
            logger.info(f"Processing message with GPT-4o router: {message}")
            intent_result = await service_client.analyze_intent(message)
            
            if 'error' in intent_result:
                logger.error(f"Intent analysis failed: {intent_result['error']}")
                return JsonResponse({'error': 'Intent analysis failed'}, status=500)
            
            # 2. GPT-4o 분석 결과 파싱
            intent = intent_result.get('intent', 'general_conversation')
            confidence = intent_result.get('confidence', 0.0)
            service_name = intent_result.get('service', 'general_agent')
            function_call = intent_result.get('function_call', {})
            reasoning = intent_result.get('reasoning', 'AI 분석 결과')
            
            logger.info(f"GPT-4o Analysis - Intent: {intent}, Confidence: {confidence}, Service: {service_name}")
            logger.info(f"Reasoning: {reasoning}")
            
            # 3. Function Call 기반 서비스 호출
            if intent == 'search_documents':
                args = function_call.get('arguments', {})
                result = await service_client.search_documents(
                    args.get('query', message), 
                    args.get('top_k', 5)
                )
            elif intent == 'analyze_employee_data':
                args = function_call.get('arguments', {})
                result = await service_client.analyze_employee(
                    args.get('employee_id'),
                    args.get('analysis_type', 'general')
                )
            elif intent == 'get_client_information':
                args = function_call.get('arguments', {})
                result = await service_client.get_client_info(
                    args.get('client_id'),
                    args.get('info_type', 'basic')
                )
            else:  # general_conversation
                args = function_call.get('arguments', {})
                result = await service_client.general_chat(
                    args.get('message', message),
                    args.get('context')
                )
            
            # 4. 응답 생성
            response_data = {
                'response': result.get('response', '죄송합니다. 처리 중 오류가 발생했습니다.'),
                'intent': intent,
                'confidence': confidence,
                'service_used': service_name,
                'reasoning': reasoning,
                'function_call': function_call,
                'timestamp': intent_result.get('timestamp', ''),
                'router_version': '2.0.0 (GPT-4o)'
            }
            
            # 에러가 있는 경우 포함
            if 'error' in result:
                response_data['error'] = result['error']
            
            logger.info(f"Response: {response_data}")
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Chat API error: {str(e)}")
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """헬스 체크 뷰"""
    
    @async_view
    async def get(self, request):
        """전체 서비스 헬스 체크"""
        try:
            health_results = await service_client.health_check_all()
            
            # 전체 상태 확인
            all_healthy = all(
                result['status'] == 'healthy' 
                for result in health_results.values()
            )
            
            return JsonResponse({
                'status': 'healthy' if all_healthy else 'unhealthy',
                'services': health_results,
                'timestamp': '2024-01-01T00:00:00Z'  # 실제로는 현재 시간 사용
            })
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)


@api_view(['GET'])
def home_view(request):
    """홈 페이지"""
    return Response({
        'message': 'NaruTalk 마이크로서비스 관리 시스템',
        'version': '1.0.0',
        'services': [
            'router_agent (포트: 8001)',
            'document_agent (포트: 8002)',
            'employee_agent (포트: 8003)',
            'client_agent (포트: 8004)',
            'general_agent (포트: 8005)',
        ],
        'endpoints': {
            'chat': '/api/chat',
            'health': '/api/health',
            'monitoring': '/monitoring/',
        }
    })


@api_view(['POST'])
@async_view
async def direct_service_call(request):
    """직접 서비스 호출"""
    try:
        service_name = request.data.get('service')
        endpoint = request.data.get('endpoint')
        method = request.data.get('method', 'GET')
        data = request.data.get('data', {})
        
        if not service_name or not endpoint:
            return Response({'error': 'Service and endpoint are required'}, status=400)
        
        result = await service_client.call_service(service_name, endpoint, method, data)
        return Response(result)
        
    except Exception as e:
        logger.error(f"Direct service call error: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@async_view
async def service_status(request):
    """서비스 상태 조회"""
    try:
        service_name = request.GET.get('service')
        
        if service_name:
            # 특정 서비스 상태
            if service_name.upper() not in service_client.services:
                return Response({'error': f'Unknown service: {service_name}'}, status=404)
            
            result = await service_client.health_check(service_name.upper())
            return Response({
                'service': service_name,
                'status': 'healthy' if 'error' not in result else 'unhealthy',
                'details': result
            })
        else:
            # 모든 서비스 상태
            results = await service_client.health_check_all()
            return Response(results)
            
    except Exception as e:
        logger.error(f"Service status error: {str(e)}")
        return Response({'error': str(e)}, status=500) 