"""
마이크로서비스 간 통신을 관리하는 서비스 클라이언트
"""
import httpx
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceClient:
    """마이크로서비스 클라이언트"""
    
    def __init__(self):
        self.services = settings.MICROSERVICES
        self.timeout = 30
        self.retry_count = 3
    
    async def call_service(self, service_name: str, endpoint: str, 
                          method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """서비스 호출"""
        if service_name not in self.services:
            return {"error": f"Unknown service: {service_name}"}
        
        service_config = self.services[service_name]
        url = f"{service_config['URL']}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == 'GET':
                    response = await client.get(url, params=data)
                elif method.upper() == 'POST':
                    response = await client.post(url, json=data)
                elif method.upper() == 'PUT':
                    response = await client.put(url, json=data)
                elif method.upper() == 'DELETE':
                    response = await client.delete(url)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Service {service_name} timeout")
            return {"error": "Service timeout"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Service {service_name} HTTP error: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Service {service_name} error: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self, service_name: str) -> Dict[str, Any]:
        """서비스 헬스 체크"""
        if service_name not in self.services:
            return {"error": f"Unknown service: {service_name}"}
        
        service_config = self.services[service_name]
        endpoint = service_config['HEALTH_CHECK']
        
        return await self.call_service(service_name, endpoint, 'GET')
    
    async def health_check_all(self) -> Dict[str, Any]:
        """모든 서비스 헬스 체크"""
        results = {}
        
        for service_name in self.services:
            result = await self.health_check(service_name)
            results[service_name] = {
                "status": "healthy" if "error" not in result else "unhealthy",
                "details": result
            }
        
        return results
    
    # 각 에이전트별 특화 메소드들
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """라우터 에이전트에서 의도 분석"""
        return await self.call_service(
            'ROUTER_AGENT', 
            '/analyze', 
            'POST', 
            {"message": message}
        )
    
    async def search_documents(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """문서 검색 에이전트 호출"""
        return await self.call_service(
            'DOCUMENT_AGENT',
            '/search',
            'POST',
            {"query": query, "top_k": top_k}
        )
    
    async def analyze_employee(self, employee_id: Optional[str] = None, 
                              analysis_type: str = "general") -> Dict[str, Any]:
        """직원 분석 에이전트 호출"""
        return await self.call_service(
            'EMPLOYEE_AGENT',
            '/analyze',
            'POST',
            {"employee_id": employee_id, "analysis_type": analysis_type}
        )
    
    async def get_client_info(self, client_id: Optional[str] = None, 
                             info_type: str = "basic") -> Dict[str, Any]:
        """고객 정보 에이전트 호출"""
        return await self.call_service(
            'CLIENT_AGENT',
            '/info',
            'POST',
            {"client_id": client_id, "info_type": info_type}
        )
    
    async def general_chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """일반 대화 에이전트 호출"""
        return await self.call_service(
            'GENERAL_AGENT',
            '/chat',
            'POST',
            {"message": message, "context": context}
        )


# 전역 서비스 클라이언트 인스턴스
service_client = ServiceClient() 