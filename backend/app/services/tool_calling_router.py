"""
Tool Calling 기반 간단한 라우터
"""
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from .database_service import DatabaseService
from .embedding_service import EmbeddingService

class ToolCallingRouter:
    def __init__(self):
        self.openai_client = OpenAI()
        self.database_service = DatabaseService()
        self.embedding_service = EmbeddingService()
        
        # 사용 가능한 도구들 정의
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "문서 검색을 수행합니다. 회사 정보, 규정, 복리후생 등을 찾을 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 키워드나 질문"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "검색 결과 개수",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_employee_data",
                    "description": "직원 데이터를 분석합니다. 근무 시간, 성과, 출퇴근 기록 등을 분석할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {
                                "type": "string",
                                "description": "직원 ID (선택사항)"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["performance", "attendance", "general"],
                                "description": "분석 유형"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_client_info",
                    "description": "고객 정보를 조회합니다. 고객 데이터, 거래 내역, 계약 정보 등을 확인할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "고객 ID (선택사항)"
                            },
                            "info_type": {
                                "type": "string",
                                "enum": ["basic", "transactions", "contracts"],
                                "description": "정보 유형"
                            }
                        },
                        "required": ["info_type"]
                    }
                }
            }
        ]
    
    async def route_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """
        메시지를 분석하고 적절한 도구를 호출하여 응답을 생성합니다.
        """
        try:
            # 1. GPT에게 의도 파악 및 도구 호출 요청
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 회사의 AI 어시스턴트입니다. 
                        사용자의 요청을 분석하고 적절한 도구를 호출해야 합니다.
                        
                        사용 가능한 도구:
                        1. search_documents: 문서 검색 (규정, 복리후생, 회사 정보 등)
                        2. analyze_employee_data: 직원 데이터 분석 (성과, 출퇴근 등)
                        3. get_client_info: 고객 정보 조회 (고객 데이터, 거래 내역 등)
                        
                        사용자의 요청에 따라 적절한 도구를 선택하고 호출하세요."""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                tools=self.tools,
                tool_choice="auto"
            )
            
            # 2. 도구 호출이 있는지 확인
            if response.choices[0].message.tool_calls:
                tool_results = []
                
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # 도구 실행
                    result = await self._execute_tool(function_name, function_args)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "function_name": function_name,
                        "result": result
                    })
                
                # 3. 도구 호출 결과를 바탕으로 최종 응답 생성
                final_response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 회사의 AI 어시스턴트입니다. 도구 호출 결과를 바탕으로 친절하고 정확한 답변을 제공하세요."
                        },
                        {
                            "role": "user",
                            "content": message
                        },
                        response.choices[0].message,
                        {
                            "role": "tool",
                            "content": json.dumps(tool_results, ensure_ascii=False),
                            "tool_call_id": tool_call.id
                        }
                    ]
                )
                
                return {
                    "response": final_response.choices[0].message.content,
                    "tool_calls": tool_results,
                    "router_type": "tool_calling"
                }
            
            else:
                # 도구 호출이 없는 경우 일반 응답
                return {
                    "response": response.choices[0].message.content,
                    "tool_calls": [],
                    "router_type": "tool_calling"
                }
                
        except Exception as e:
            return {
                "response": f"오류가 발생했습니다: {str(e)}",
                "tool_calls": [],
                "router_type": "tool_calling",
                "error": str(e)
            }
    
    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구를 실행합니다.
        """
        try:
            if function_name == "search_documents":
                return await self._search_documents(
                    function_args.get("query"),
                    function_args.get("top_k", 5)
                )
            
            elif function_name == "analyze_employee_data":
                return await self._analyze_employee_data(
                    function_args.get("employee_id"),
                    function_args.get("analysis_type")
                )
            
            elif function_name == "get_client_info":
                return await self._get_client_info(
                    function_args.get("client_id"),
                    function_args.get("info_type")
                )
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def _search_documents(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """문서 검색을 수행합니다."""
        try:
            # 임베딩 기반 검색
            results = await self.embedding_service.search_similar_documents(query, top_k)
            
            return {
                "function": "search_documents",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": f"Document search failed: {str(e)}"}
    
    async def _analyze_employee_data(self, employee_id: Optional[str], analysis_type: str) -> Dict[str, Any]:
        """직원 데이터를 분석합니다."""
        try:
            # 데이터베이스에서 직원 정보 조회
            if employee_id:
                employee_data = await self.database_service.get_employee_data(employee_id)
            else:
                employee_data = await self.database_service.get_all_employees_summary()
            
            # 분석 유형에 따른 처리
            if analysis_type == "performance":
                analysis_result = await self.database_service.analyze_employee_performance(employee_id)
            elif analysis_type == "attendance":
                analysis_result = await self.database_service.analyze_employee_attendance(employee_id)
            else:
                analysis_result = await self.database_service.get_employee_general_info(employee_id)
            
            return {
                "function": "analyze_employee_data",
                "employee_id": employee_id,
                "analysis_type": analysis_type,
                "data": employee_data,
                "analysis": analysis_result
            }
        except Exception as e:
            return {"error": f"Employee data analysis failed: {str(e)}"}
    
    async def _get_client_info(self, client_id: Optional[str], info_type: str) -> Dict[str, Any]:
        """고객 정보를 조회합니다."""
        try:
            # 데이터베이스에서 고객 정보 조회
            if client_id:
                client_data = await self.database_service.get_client_data(client_id)
            else:
                client_data = await self.database_service.get_all_clients_summary()
            
            # 정보 유형에 따른 처리
            if info_type == "basic":
                info_result = await self.database_service.get_client_basic_info(client_id)
            elif info_type == "transactions":
                info_result = await self.database_service.get_client_transactions(client_id)
            elif info_type == "contracts":
                info_result = await self.database_service.get_client_contracts(client_id)
            else:
                info_result = client_data
            
            return {
                "function": "get_client_info",
                "client_id": client_id,
                "info_type": info_type,
                "data": client_data,
                "info": info_result
            }
        except Exception as e:
            return {"error": f"Client info retrieval failed: {str(e)}"} 