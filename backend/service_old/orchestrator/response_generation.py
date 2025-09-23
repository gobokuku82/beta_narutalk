from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import json
import logging
from ..utils import LLMManager, PromptTemplates

logger = logging.getLogger(__name__)

class ResponseState(TypedDict):
    response_format: str
    raw_data: Dict[str, Any]
    formatted_response: str
    citations: List[str]
    confidence_score: float

class ResponseGenerationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(ResponseState)
        self.llm_manager = LLMManager()
        self.prompt_templates = PromptTemplates()
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("format_selection", self.select_format)
        self.workflow.add_node("generate_text", self.generate_text_response)
        self.workflow.add_node("generate_table", self.generate_table_response)
        self.workflow.add_node("generate_chart", self.generate_chart_response)
        self.workflow.add_node("generate_document", self.generate_document_response)
        self.workflow.add_node("add_citations", self.add_references)
        self.workflow.add_node("final_review", self.final_quality_check)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "format_selection")
        
        self.workflow.add_conditional_edges(
            "format_selection",
            self.route_by_format,
            {
                "text": "generate_text",
                "table": "generate_table", 
                "chart": "generate_chart",
                "document": "generate_document"
            }
        )
        
        # 모든 생성 노드는 citations로
        for node in ["generate_text", "generate_table", "generate_chart", "generate_document"]:
            self.workflow.add_edge(node, "add_citations")
        
        self.workflow.add_edge("add_citations", "final_review")
        self.workflow.add_edge("final_review", END)

    # 노드 메서드들
    async def select_format(self, state: ResponseState) -> ResponseState:
        """응답 형식 선택 - 데이터 유형에 따라 자동 선택"""
        raw_data = state.get('raw_data', {})

        # 데이터 유형에 따라 최적 형식 선택
        if raw_data.get('table_data'):
            state["response_format"] = "table"
        elif raw_data.get('chart_data'):
            state["response_format"] = "chart"
        elif raw_data.get('requires_document'):
            state["response_format"] = "document"
        else:
            state["response_format"] = "text"

        logger.info(f"Response format selected: {state['response_format']}")
        return state

    async def generate_text_response(self, state: ResponseState) -> ResponseState:
        """텍스트 응답 생성 - LLM 활용"""
        try:
            raw_data = state.get('raw_data', {})

            # 원본 쿼리와 분석 결과 추출
            original_query = raw_data.get('original_query', '사용자 질문')
            analysis_results = raw_data.get('analysis_results', {})

            # 프롬프트 생성
            prompt = self.prompt_templates.get_prompt(
                category="response_generation",
                version="v1",
                original_query=original_query,
                analysis_results=json.dumps(analysis_results, ensure_ascii=False, indent=2),
                additional_info=""
            )

            # LLM 호출
            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai",
                category="response_generation",
                temperature=0.7
            )

            state["formatted_response"] = response['content']
            logger.info(f"Text response generated: {len(response['content'])} chars")

        except Exception as e:
            logger.error(f"Text response generation failed: {e}")
            state["formatted_response"] = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

        return state

    async def generate_table_response(self, state: ResponseState) -> ResponseState:
        """테이블 응답 생성 - LLM 기반 포맷팅"""
        try:
            raw_data = state.get('raw_data', {})

            # 테이블 데이터 추출
            table_data = raw_data.get('table_data', [])

            if not table_data:
                state["formatted_response"] = "표시할 테이블 데이터가 없습니다."
                return state

            # LLM에게 테이블 형식으로 포맷팅 요청
            prompt = f"""다음 데이터를 읽기 쉬운 테이블 형식으로 포맷팅하세요.
Markdown 테이블 형식을 사용하세요.

데이터:
{json.dumps(table_data, ensure_ascii=False, indent=2)}

테이블:"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",
                category="table_formatting",
                temperature=0.2
            )

            state["formatted_response"] = response['content']
            logger.info("Table response generated")

        except Exception as e:
            logger.error(f"Table response generation failed: {e}")
            state["formatted_response"] = "테이블 생성 중 오류가 발생했습니다."

        return state

    async def generate_chart_response(self, state: ResponseState) -> ResponseState:
        """차트 응답 생성 - 차트 설정 및 설명 생성"""
        try:
            raw_data = state.get('raw_data', {})
            chart_data = raw_data.get('chart_data', {})

            # 차트 설정 생성
            chart_config = {
                "type": chart_data.get('type', 'bar'),
                "data": chart_data.get('data', []),
                "options": {
                    "title": chart_data.get('title', '데이터 분석 결과'),
                    "responsive": True
                }
            }

            # LLM으로 차트 설명 생성
            prompt = f"""다음 차트 데이터에 대한 간단한 설명을 작성하세요:

차트 유형: {chart_config['type']}
데이터: {json.dumps(chart_config['data'][:5], ensure_ascii=False)}

주요 인사이트를 2-3문장으로 설명하세요:"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",
                category="chart_description",
                temperature=0.5
            )

            # 차트 설정과 설명을 함께 반환
            formatted_response = {
                "chart_config": chart_config,
                "description": response['content']
            }

            state["formatted_response"] = json.dumps(formatted_response, ensure_ascii=False, indent=2)
            logger.info("Chart response generated")

        except Exception as e:
            logger.error(f"Chart response generation failed: {e}")
            state["formatted_response"] = "차트 생성 중 오류가 발생했습니다."

        return state

    async def generate_document_response(self, state: ResponseState) -> ResponseState:
        """문서 응답 생성 - 구조화된 보고서 생성"""
        try:
            raw_data = state.get('raw_data', {})

            # 문서 생성용 데이터 준비
            doc_data = {
                "title": raw_data.get('title', '분석 보고서'),
                "summary": raw_data.get('summary', ''),
                "details": raw_data.get('details', {}),
                "recommendations": raw_data.get('recommendations', [])
            }

            # LLM으로 구조화된 문서 생성
            prompt = f"""다음 데이터를 바탕으로 전문적인 보고서를 작성하세요:

제목: {doc_data['title']}
데이터: {json.dumps(doc_data, ensure_ascii=False, indent=2)}

다음 구조로 작성하세요:
1. 요약
2. 주요 발견사항
3. 상세 분석
4. 권고사항

보고서:"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_doc",
                category="document_generation",
                temperature=0.5
            )

            state["formatted_response"] = response['content']
            logger.info(f"Document response generated: {len(response['content'])} chars")

        except Exception as e:
            logger.error(f"Document response generation failed: {e}")
            state["formatted_response"] = "문서 생성 중 오류가 발생했습니다."

        return state

    async def add_references(self, state: ResponseState) -> ResponseState:
        """참조/인용 추가 - 데이터 출처 명시"""
        raw_data = state.get('raw_data', {})
        citations = []

        # 데이터 출처 추출
        if raw_data.get('sources'):
            for source in raw_data['sources']:
                citations.append(f"- {source}")

        # 사용된 데이터베이스 추가
        if raw_data.get('databases_used'):
            for db in raw_data['databases_used']:
                citations.append(f"- 데이터베이스: {db}")

        # 타임스탬프 추가
        if raw_data.get('timestamp'):
            citations.append(f"- 조회 시간: {raw_data['timestamp']}")

        state["citations"] = citations

        # 응답에 출처 추가
        if citations and state.get('formatted_response'):
            citations_text = "\n\n📌 데이터 출처:\n" + "\n".join(citations)
            state["formatted_response"] += citations_text

        logger.info(f"Added {len(citations)} citations")
        return state

    async def final_quality_check(self, state: ResponseState) -> ResponseState:
        """최종 품질 확인 - LLM 기반 품질 평가"""
        try:
            response = state.get('formatted_response', '')

            if not response:
                state["confidence_score"] = 0.0
                return state

            # 품질 평가 프롬프트
            prompt = f"""다음 응답의 품질을 평가하세요:

응답:
{response[:1000]}...

평가 기준:
1. 완전성 (필요한 정보가 모두 포함되었는가)
2. 정확성 (정보가 정확한가)
3. 명확성 (이해하기 쉬운가)
4. 관련성 (질문에 적절한 답변인가)

0.0에서 1.0 사이의 점수만 반환하세요:"""

            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",
                category="quality_check",
                temperature=0.1
            )

            try:
                score = float(llm_response['content'].strip())
                state["confidence_score"] = min(max(score, 0.0), 1.0)
            except:
                state["confidence_score"] = 0.7  # 기본값

            logger.info(f"Quality check completed: {state['confidence_score']}")

        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            state["confidence_score"] = 0.5

        return state

    def route_by_format(self, state: ResponseState) -> str:
        """포맷별 라우팅"""
        format_type = state.get("response_format", "text")
        if format_type in ["text", "table", "chart", "document"]:
            return format_type
        return "text"