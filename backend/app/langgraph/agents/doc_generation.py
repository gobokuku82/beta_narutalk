"""
Document Generation Agent - 문서자동생성 에이전트
영업 제안서, 보고서 등 문서 자동 생성
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from loguru import logger
import json
from pathlib import Path
from datetime import datetime
import os

from app.langgraph.state import AgentState
from app.core.config import settings


class DocGenerationAgent:
    """문서 자동생성 전문 에이전트"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,  # gpt-4o
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 문서 템플릿 경로
        self.templates_dir = settings.DOCUMENTS_DIR / "templates"
        self.generated_dir = settings.DOCUMENTS_DIR / "generated"
        
        # 디렉토리 생성
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        
        # 도구 등록
        self.tools = {
            "create_proposal": self.create_proposal,
            "generate_report": self.generate_report,
            "create_presentation": self.create_presentation,
            "email_composer": self.compose_email
        }
        
        # 템플릿 초기화
        self._initialize_templates()
    
    def _initialize_templates(self):
        """기본 템플릿 생성"""
        templates = {
            "proposal_template.md": """# 제약 제품 제안서

## 1. 제품 개요
- **제품명**: {product_name}
- **성분명**: {generic_name}
- **적응증**: {indication}

## 2. 제품 특징
{product_features}

## 3. 임상 데이터
{clinical_data}

## 4. 경쟁 우위
{competitive_advantages}

## 5. 가격 정책
{pricing}

## 6. 공급 조건
{supply_terms}

---
작성일: {date}
담당자: {author}
""",
            "report_template.md": """# 영업 활동 보고서

## 기간: {period}

### 1. 방문 현황
- 총 방문 건수: {total_visits}
- 신규 거래처: {new_customers}
- 기존 거래처: {existing_customers}

### 2. 실적 요약
{performance_summary}

### 3. 주요 성과
{key_achievements}

### 4. 이슈 사항
{issues}

### 5. 다음 계획
{next_plans}

---
작성자: {author}
작성일: {date}
""",
            "email_template.txt": """제목: {subject}

안녕하세요, {recipient_name}님

{greeting}

{main_content}

{closing}

감사합니다.

{sender_name}
{sender_title}
{company_name}
{contact_info}
"""
        }
        
        # 템플릿 파일 생성
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                template_path.write_text(content, encoding="utf-8")
                logger.info(f"템플릿 생성: {filename}")
    
    async def create_proposal(self, params: Dict) -> Dict:
        """영업 제안서 생성"""
        try:
            # 템플릿 로드
            template_path = self.templates_dir / "proposal_template.md"
            template = template_path.read_text(encoding="utf-8")
            
            # LLM으로 내용 생성
            prompt = f"""
            다음 정보를 바탕으로 제약 제품 제안서를 작성하세요:
            
            제품: {params.get('product_name', '신약')}
            대상 병원: {params.get('hospital', '종합병원')}
            목적: {params.get('purpose', '신규 제품 소개')}
            
            전문적이고 설득력 있는 제안서를 작성하세요.
            """
            
            response = await self.llm.ainvoke(prompt)
            content = response.content
            
            # 문서 생성
            document = template.format(
                product_name=params.get('product_name', ''),
                generic_name=params.get('generic_name', ''),
                indication=params.get('indication', ''),
                product_features=content[:500],
                clinical_data="임상시험 데이터 요약",
                competitive_advantages="경쟁 제품 대비 장점",
                pricing="협의 필요",
                supply_terms="표준 공급 조건",
                date=datetime.now().strftime("%Y-%m-%d"),
                author=params.get('author', '영업팀')
            )
            
            # 파일 저장
            filename = f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = self.generated_dir / filename
            filepath.write_text(document, encoding="utf-8")
            
            return {
                "status": "success",
                "filename": filename,
                "path": str(filepath),
                "content": document[:500] + "..."
            }
            
        except Exception as e:
            logger.error(f"제안서 생성 오류: {e}")
            return {"status": "error", "message": str(e)}
    
    async def generate_report(self, params: Dict) -> Dict:
        """보고서 생성"""
        try:
            # 템플릿 로드
            template_path = self.templates_dir / "report_template.md"
            template = template_path.read_text(encoding="utf-8")
            
            # 보고서 내용 생성
            report = template.format(
                period=params.get('period', '2024년 9월'),
                total_visits=params.get('total_visits', 0),
                new_customers=params.get('new_customers', 0),
                existing_customers=params.get('existing_customers', 0),
                performance_summary=params.get('summary', ''),
                key_achievements=params.get('achievements', ''),
                issues=params.get('issues', '없음'),
                next_plans=params.get('plans', ''),
                author=params.get('author', ''),
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # 파일 저장
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = self.generated_dir / filename
            filepath.write_text(report, encoding="utf-8")
            
            return {
                "status": "success",
                "filename": filename,
                "path": str(filepath),
                "content": report
            }
            
        except Exception as e:
            logger.error(f"보고서 생성 오류: {e}")
            return {"status": "error", "message": str(e)}
    
    async def create_presentation(self, topic: str) -> Dict:
        """프레젠테이션 자료 생성"""
        # 실제 구현에서는 PPTX 라이브러리 활용
        outline = f"""
        # {topic} 프레젠테이션
        
        ## 슬라이드 1: 제목
        - {topic}
        
        ## 슬라이드 2: 목차
        1. 개요
        2. 주요 내용
        3. 데이터 분석
        4. 결론
        
        ## 슬라이드 3-10: 상세 내용
        [내용 생성 중...]
        """
        
        return {
            "status": "success",
            "outline": outline,
            "slides_count": 10
        }
    
    async def compose_email(self, params: Dict) -> Dict:
        """이메일 작성"""
        try:
            # 템플릿 로드
            template_path = self.templates_dir / "email_template.txt"
            template = template_path.read_text(encoding="utf-8")
            
            # LLM으로 본문 생성
            prompt = f"""
            다음 내용으로 전문적인 비즈니스 이메일을 작성하세요:
            수신자: {params.get('recipient', '의사')}
            목적: {params.get('purpose', '제품 소개')}
            핵심 메시지: {params.get('key_message', '')}
            """
            
            response = await self.llm.ainvoke(prompt)
            
            # 이메일 생성
            email = template.format(
                subject=params.get('subject', '제품 안내'),
                recipient_name=params.get('recipient_name', '선생님'),
                greeting="평소 저희 제품에 관심을 가져주셔서 감사합니다.",
                main_content=response.content,
                closing="추가 문의사항이 있으시면 언제든 연락 주시기 바랍니다.",
                sender_name=params.get('sender_name', '홍길동'),
                sender_title="영업 담당자",
                company_name="제약회사",
                contact_info="Tel: 02-1234-5678 | Email: info@pharma.com"
            )
            
            return {
                "status": "success",
                "email": email
            }
            
        except Exception as e:
            logger.error(f"이메일 작성 오류: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        logger.info("문서생성 에이전트 처리 시작")
        
        # 최신 메시지 확인
        last_message = state["messages"][-1]
        user_request = last_message.get("content", "")
        
        # 문서 유형 파악
        doc_type = self._identify_document_type(user_request)
        
        # 문서 생성
        result = None
        if doc_type == "proposal":
            result = await self.create_proposal({
                "product_name": "신약 A",
                "hospital": "서울대병원",
                "purpose": user_request
            })
        elif doc_type == "report":
            result = await self.generate_report({
                "period": "2024년 9월",
                "summary": user_request
            })
        elif doc_type == "email":
            result = await self.compose_email({
                "purpose": user_request
            })
        else:
            result = {
                "status": "info",
                "message": "생성 가능한 문서: 제안서, 보고서, 이메일"
            }
        
        # 응답 생성
        if result.get("status") == "success":
            response = f"문서가 성공적으로 생성되었습니다.\n파일: {result.get('filename', 'N/A')}"
            if result.get("content"):
                response += f"\n\n미리보기:\n{result['content'][:500]}"
        else:
            response = result.get("message", "문서 생성에 실패했습니다.")
        
        return {
            "messages": [{"role": "assistant", "content": response}],
            "agent_outputs": {
                "doc_generation": result
            },
            "next_agent": None
        }
    
    def _identify_document_type(self, request: str) -> str:
        """요청에서 문서 유형 식별"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["제안서", "proposal", "제안"]):
            return "proposal"
        elif any(word in request_lower for word in ["보고서", "report", "리포트"]):
            return "report"
        elif any(word in request_lower for word in ["이메일", "email", "메일"]):
            return "email"
        else:
            return "unknown"