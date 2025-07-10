import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# 테스트를 위한 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app

# FastAPI 테스트 클라이언트
client = TestClient(app)

class TestAPI:
    """API 테스트 클래스"""
    
    def test_health_check(self):
        """헬스 체크 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        assert "NaruTalk AI 챗봇" in response.text
    
    def test_chat_endpoint(self):
        """채팅 엔드포인트 테스트"""
        chat_data = {
            "message": "안녕하세요",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "router_type" in data
        assert "confidence" in data
        assert isinstance(data["sources"], list)
    
    def test_chat_with_empty_message(self):
        """빈 메시지 채팅 테스트"""
        chat_data = {
            "message": "",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        # 빈 메시지에 대한 처리 확인
        assert response.status_code == 200
    
    def test_chat_qa_routing(self):
        """질문답변 라우팅 테스트"""
        chat_data = {
            "message": "회사 정책에 대해 알려주세요",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["router_type"] == "qa"
    
    def test_chat_document_search_routing(self):
        """문서검색 라우팅 테스트"""
        chat_data = {
            "message": "문서를 검색해주세요",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["router_type"] == "document_search"
    
    def test_chat_employee_info_routing(self):
        """직원정보 라우팅 테스트"""
        chat_data = {
            "message": "김현성 직원 정보를 알려주세요",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["router_type"] == "employee_info"
    
    def test_chat_general_chat_routing(self):
        """일반대화 라우팅 테스트"""
        chat_data = {
            "message": "안녕하세요",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["router_type"] == "general_chat"
    
    def test_get_router_types(self):
        """라우터 타입 조회 테스트"""
        response = client.get("/api/v1/router/types")
        assert response.status_code == 200
        
        data = response.json()
        assert "router_types" in data
        assert len(data["router_types"]) == 4
    
    def test_chat_history(self):
        """채팅 기록 조회 테스트"""
        session_id = "test_session_history"
        response = client.get(f"/api/v1/chat/history/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
    
    def test_embedding_search(self):
        """임베딩 검색 테스트"""
        search_data = {
            "query": "회사 정책",
            "limit": 3
        }
        
        response = client.post("/api/v1/embedding/search", params=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

class TestRouterIntegration:
    """라우터 통합 테스트"""
    
    def test_multiple_messages_same_session(self):
        """동일 세션에서 여러 메시지 테스트"""
        session_id = "integration_test_session"
        
        # 첫 번째 메시지 (일반 대화)
        response1 = client.post("/api/v1/chat", json={
            "message": "안녕하세요",
            "user_id": "test_user",
            "session_id": session_id
        })
        assert response1.status_code == 200
        
        # 두 번째 메시지 (질문 답변)
        response2 = client.post("/api/v1/chat", json={
            "message": "회사 정책에 대해 알려주세요",
            "user_id": "test_user",
            "session_id": session_id
        })
        assert response2.status_code == 200
        
        # 세 번째 메시지 (문서 검색)
        response3 = client.post("/api/v1/chat", json={
            "message": "문서를 찾아주세요",
            "user_id": "test_user",
            "session_id": session_id
        })
        assert response3.status_code == 200
        
        # 각 메시지의 라우터 타입 확인
        assert response1.json()["router_type"] == "general_chat"
        assert response2.json()["router_type"] == "qa"
        assert response3.json()["router_type"] == "document_search"

if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"]) 