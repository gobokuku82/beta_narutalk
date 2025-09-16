"""
Agent Tools Implementation
각 Worker 에이전트를 LangChain StructuredTool로 래핑
"""

from typing import Dict, Any, List, Optional
from langchain.tools import StructuredTool
from langchain_core.tools import ToolException
import asyncio
import logging
from datetime import datetime

from .schemas import (
    DataAnalysisInput, DataAnalysisOutput,
    InfoRetrievalInput, InfoRetrievalOutput,
    DocumentGenerationInput, DocumentGenerationOutput,
    ComplianceInput, ComplianceOutput,
    StorageInput, StorageOutput
)

logger = logging.getLogger(__name__)


# ============= Tool Handler Functions =============

async def data_analysis_handler(
    task_id: str,
    task_description: str,
    query: str,
    data_source: Optional[str] = "main_db",
    analysis_type: str = "sql",
    context: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """데이터 분석 에이전트 핸들러"""
    try:
        # Import worker agent dynamically to avoid circular imports
        from ..workers.data_analysis import DataAnalysisAgent

        agent = DataAnalysisAgent()

        # Prepare input
        task_input = {
            "task_id": task_id,
            "task_description": task_description,
            "query": query,
            "data_source": data_source,
            "analysis_type": analysis_type,
            "context": context or {},
            **kwargs
        }

        # Execute analysis
        result = await agent.execute(task_input)

        # Format output
        output = DataAnalysisOutput(
            task_id=task_id,
            status="success" if result.get("success") else "failed",
            confidence_score=result.get("confidence_score", 0.8),
            execution_time=result.get("execution_time", 0),
            sql_query=result.get("sql_query"),
            results=result.get("results", []),
            row_count=result.get("row_count", 0),
            summary=result.get("summary")
        )

        return output.dict()

    except Exception as e:
        logger.error(f"Data analysis failed: {str(e)}")
        return DataAnalysisOutput(
            task_id=task_id,
            status="failed",
            confidence_score=0.0,
            execution_time=0,
            error_message=str(e)
        ).dict()


async def info_retrieval_handler(
    task_id: str,
    task_description: str,
    search_query: str,
    search_type: str = "hybrid",
    collections: Optional[List[str]] = None,
    top_k: int = 5,
    context: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """정보 검색 에이전트 핸들러"""
    try:
        from ..workers.info_retrieval import InformationRetrievalAgent

        agent = InformationRetrievalAgent()

        task_input = {
            "task_id": task_id,
            "task_description": task_description,
            "search_query": search_query,
            "search_type": search_type,
            "collections": collections or ["hr_rules", "policies"],
            "top_k": top_k,
            "context": context or {},
            **kwargs
        }

        result = await agent.execute(task_input)

        output = InfoRetrievalOutput(
            task_id=task_id,
            status="success" if result.get("success") else "failed",
            confidence_score=result.get("confidence_score", 0.85),
            execution_time=result.get("execution_time", 0),
            documents=result.get("documents", []),
            total_found=result.get("total_found", 0),
            relevance_scores=result.get("relevance_scores", []),
            sources=result.get("sources", []),
            summary=result.get("summary")
        )

        return output.dict()

    except Exception as e:
        logger.error(f"Information retrieval failed: {str(e)}")
        return InfoRetrievalOutput(
            task_id=task_id,
            status="failed",
            confidence_score=0.0,
            execution_time=0,
            error_message=str(e)
        ).dict()


async def doc_generation_handler(
    task_id: str,
    task_description: str,
    document_type: str,
    content_data: Dict[str, Any],
    format: str = "markdown",
    context: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """문서 생성 에이전트 핸들러"""
    try:
        from ..workers.doc_generation import DocumentGenerationAgent

        agent = DocumentGenerationAgent()

        task_input = {
            "task_id": task_id,
            "task_description": task_description,
            "document_type": document_type,
            "content_data": content_data,
            "format": format,
            "context": context or {},
            **kwargs
        }

        result = await agent.execute(task_input)

        output = DocumentGenerationOutput(
            task_id=task_id,
            status="success" if result.get("success") else "failed",
            confidence_score=result.get("confidence_score", 0.9),
            execution_time=result.get("execution_time", 0),
            document_content=result.get("document_content", ""),
            document_format=format,
            word_count=result.get("word_count", 0),
            sections=result.get("sections", []),
            metadata=result.get("metadata", {})
        )

        return output.dict()

    except Exception as e:
        logger.error(f"Document generation failed: {str(e)}")
        return DocumentGenerationOutput(
            task_id=task_id,
            status="failed",
            confidence_score=0.0,
            execution_time=0,
            document_content="",
            document_format=format,
            error_message=str(e)
        ).dict()


async def compliance_handler(
    task_id: str,
    task_description: str,
    validation_type: str,
    content_to_validate: str,
    strict_mode: bool = True,
    context: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """규정 검증 에이전트 핸들러"""
    try:
        from ..workers.compliance import ComplianceValidationAgent

        agent = ComplianceValidationAgent()

        task_input = {
            "task_id": task_id,
            "task_description": task_description,
            "validation_type": validation_type,
            "content_to_validate": content_to_validate,
            "strict_mode": strict_mode,
            "context": context or {},
            **kwargs
        }

        result = await agent.execute(task_input)

        output = ComplianceOutput(
            task_id=task_id,
            status="success" if result.get("success") else "failed",
            confidence_score=result.get("confidence_score", 0.95),
            execution_time=result.get("execution_time", 0),
            is_compliant=result.get("is_compliant", False),
            violations=result.get("violations", []),
            warnings=result.get("warnings", []),
            recommendations=result.get("recommendations", []),
            compliance_score=result.get("compliance_score", 0.0),
            checked_rules=result.get("checked_rules", [])
        )

        return output.dict()

    except Exception as e:
        logger.error(f"Compliance validation failed: {str(e)}")
        return ComplianceOutput(
            task_id=task_id,
            status="failed",
            confidence_score=0.0,
            execution_time=0,
            is_compliant=False,
            error_message=str(e)
        ).dict()


async def storage_handler(
    task_id: str,
    task_description: str,
    data_to_store: Dict[str, Any],
    data_type: str,
    encryption_required: bool = False,
    context: Dict[str, Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """저장 결정 에이전트 핸들러"""
    try:
        from ..workers.storage import StorageDecisionAgent

        agent = StorageDecisionAgent()

        task_input = {
            "task_id": task_id,
            "task_description": task_description,
            "data_to_store": data_to_store,
            "data_type": data_type,
            "encryption_required": encryption_required,
            "context": context or {},
            **kwargs
        }

        result = await agent.execute(task_input)

        output = StorageOutput(
            task_id=task_id,
            status="success" if result.get("success") else "failed",
            confidence_score=result.get("confidence_score", 0.95),
            execution_time=result.get("execution_time", 0),
            storage_location=result.get("storage_location", ""),
            storage_method=result.get("storage_method", ""),
            storage_id=result.get("storage_id"),
            metadata_stored=result.get("metadata_stored", {}),
            compression_used=result.get("compression_used", False),
            encryption_applied=result.get("encryption_applied", False)
        )

        return output.dict()

    except Exception as e:
        logger.error(f"Storage decision failed: {str(e)}")
        return StorageOutput(
            task_id=task_id,
            status="failed",
            confidence_score=0.0,
            execution_time=0,
            storage_location="",
            storage_method="",
            error_message=str(e)
        ).dict()


# ============= Tool Creation Functions =============

def create_data_analysis_tool() -> StructuredTool:
    """데이터 분석 도구 생성"""
    return StructuredTool(
        name="data_analysis",
        description="""SQL 쿼리 실행 및 데이터 분석 도구.
        데이터베이스에서 정보를 조회하고 분석합니다.
        통계 분석, 집계, 트렌드 분석을 수행할 수 있습니다.""",
        func=lambda **kwargs: asyncio.run(data_analysis_handler(**kwargs)),
        args_schema=DataAnalysisInput,
        return_direct=False,
        handle_tool_error=True
    )


def create_info_retrieval_tool() -> StructuredTool:
    """정보 검색 도구 생성"""
    return StructuredTool(
        name="info_retrieval",
        description="""벡터 검색 및 정보 검색 도구.
        HR 규정, 정책, 문서에서 관련 정보를 검색합니다.
        ChromaDB를 활용한 의미 기반 검색을 지원합니다.""",
        func=lambda **kwargs: asyncio.run(info_retrieval_handler(**kwargs)),
        args_schema=InfoRetrievalInput,
        return_direct=False,
        handle_tool_error=True
    )


def create_doc_generation_tool() -> StructuredTool:
    """문서 생성 도구 생성"""
    return StructuredTool(
        name="doc_generation",
        description="""문서 및 보고서 생성 도구.
        다양한 형식의 문서를 자동으로 생성합니다.
        보고서, 요약, 이메일, 프레젠테이션 등을 만들 수 있습니다.""",
        func=lambda **kwargs: asyncio.run(doc_generation_handler(**kwargs)),
        args_schema=DocumentGenerationInput,
        return_direct=False,
        handle_tool_error=True
    )


def create_compliance_tool() -> StructuredTool:
    """규정 검증 도구 생성"""
    return StructuredTool(
        name="compliance_validation",
        description="""규정 준수 및 검증 도구.
        HR 정책, 법규, 내부 규정 준수 여부를 검증합니다.
        위반 사항을 식별하고 권고사항을 제공합니다.""",
        func=lambda **kwargs: asyncio.run(compliance_handler(**kwargs)),
        args_schema=ComplianceInput,
        return_direct=False,
        handle_tool_error=True
    )


def create_storage_tool() -> StructuredTool:
    """저장 결정 도구 생성"""
    return StructuredTool(
        name="storage_decision",
        description="""데이터 저장 전략 및 실행 도구.
        최적의 저장 방법을 결정하고 데이터를 저장합니다.
        암호화, 압축, 백업 전략을 관리합니다.""",
        func=lambda **kwargs: asyncio.run(storage_handler(**kwargs)),
        args_schema=StorageInput,
        return_direct=False,
        handle_tool_error=True
    )


def get_all_agent_tools() -> List[StructuredTool]:
    """모든 에이전트 도구를 반환"""
    return [
        create_data_analysis_tool(),
        create_info_retrieval_tool(),
        create_doc_generation_tool(),
        create_compliance_tool(),
        create_storage_tool()
    ]


# ============= Tool Selection Helper =============

def select_tools_for_task(task_type: str, requirements: List[str]) -> List[StructuredTool]:
    """태스크 유형과 요구사항에 따라 필요한 도구 선택"""

    tool_mapping = {
        "data": create_data_analysis_tool(),
        "search": create_info_retrieval_tool(),
        "document": create_doc_generation_tool(),
        "compliance": create_compliance_tool(),
        "storage": create_storage_tool()
    }

    selected_tools = []

    # Task type based selection
    if "analysis" in task_type.lower() or "data" in task_type.lower():
        selected_tools.append(tool_mapping["data"])
    if "search" in task_type.lower() or "retrieval" in task_type.lower():
        selected_tools.append(tool_mapping["search"])
    if "report" in task_type.lower() or "document" in task_type.lower():
        selected_tools.append(tool_mapping["document"])
    if "compliance" in task_type.lower() or "validation" in task_type.lower():
        selected_tools.append(tool_mapping["compliance"])
    if "store" in task_type.lower() or "save" in task_type.lower():
        selected_tools.append(tool_mapping["storage"])

    # Requirements based selection
    for req in requirements:
        req_lower = req.lower()
        if "sql" in req_lower or "query" in req_lower:
            if tool_mapping["data"] not in selected_tools:
                selected_tools.append(tool_mapping["data"])
        if "search" in req_lower or "find" in req_lower:
            if tool_mapping["search"] not in selected_tools:
                selected_tools.append(tool_mapping["search"])
        if "generate" in req_lower or "create" in req_lower:
            if tool_mapping["document"] not in selected_tools:
                selected_tools.append(tool_mapping["document"])
        if "check" in req_lower or "validate" in req_lower:
            if tool_mapping["compliance"] not in selected_tools:
                selected_tools.append(tool_mapping["compliance"])

    # Return all tools if none selected
    return selected_tools if selected_tools else list(tool_mapping.values())