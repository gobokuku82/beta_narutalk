"""
Base Tool Classes
LangChain Tool 기본 클래스 정의
"""

from typing import Any, Dict, Optional, List, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool as LangChainBaseTool, Tool
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
import logging
logger = logging.getLogger(__name__)
from datetime import datetime
import traceback


class ToolResult(BaseModel):
    """도구 실행 결과"""
    success: bool = Field(description="실행 성공 여부")
    data: Any = Field(description="실행 결과 데이터")
    error: Optional[str] = Field(None, description="에러 메시지")
    execution_time: float = Field(description="실행 시간 (초)")
    tool_name: str = Field(description="도구 이름")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class BaseTool(LangChainBaseTool):
    """확장된 Base Tool 클래스"""
    
    name: str = "base_tool"
    description: str = "Base tool implementation"
    return_direct: bool = False
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> ToolResult:
        """동기 실행 (Override 필요)"""
        raise NotImplementedError("Subclass must implement _run method")
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """비동기 실행 (Override 필요)"""
        raise NotImplementedError("Subclass must implement _arun method")
    
    def handle_error(self, error: Exception) -> ToolResult:
        """에러 처리"""
        logger.error(f"Tool {self.name} error: {str(error)}")
        logger.error(traceback.format_exc())
        
        return ToolResult(
            success=False,
            data=None,
            error=str(error),
            execution_time=0,
            tool_name=self.name
        )
    
    def validate_input(self, input_data: Any) -> bool:
        """입력 검증 (Override 가능)"""
        return True
    
    def format_output(self, raw_output: Any) -> Any:
        """출력 포맷팅 (Override 가능)"""
        return raw_output


class StructuredTool(BaseTool):
    """구조화된 입력을 받는 Tool"""
    
    args_schema: Type[BaseModel] = None
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> ToolResult:
        """구조화된 입력으로 실행"""
        raise NotImplementedError("Subclass must implement _run method")
    
    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> ToolResult:
        """구조화된 입력으로 비동기 실행"""
        raise NotImplementedError("Subclass must implement _arun method")


class MultiStepTool(BaseTool):
    """여러 단계를 거치는 Tool"""
    
    steps: List[str] = []
    
    async def execute_steps(self, input_data: Any) -> ToolResult:
        """단계별 실행"""
        results = {}
        
        for step in self.steps:
            step_method = getattr(self, f"step_{step}", None)
            if step_method:
                try:
                    result = await step_method(input_data, results)
                    results[step] = result
                except Exception as e:
                    logger.error(f"Step {step} failed: {e}")
                    return self.handle_error(e)
        
        return ToolResult(
            success=True,
            data=results,
            error=None,
            execution_time=0,
            tool_name=self.name
        )


class CachedTool(BaseTool):
    """캐싱 기능이 있는 Tool"""
    
    cache: Dict[str, ToolResult] = {}
    cache_ttl: int = 300  # 5분
    
    def get_cache_key(self, input_data: Any) -> str:
        """캐시 키 생성"""
        return str(hash(str(input_data)))
    
    def is_cache_valid(self, cached_result: ToolResult) -> bool:
        """캐시 유효성 검사"""
        if not cached_result:
            return False
        
        cached_time = datetime.fromisoformat(cached_result.timestamp)
        age = (datetime.now() - cached_time).total_seconds()
        
        return age < self.cache_ttl
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """캐싱을 사용한 실행"""
        cache_key = self.get_cache_key(query)
        
        # 캐시 확인
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if self.is_cache_valid(cached):
                logger.info(f"Using cached result for {self.name}")
                return cached
        
        # 실제 실행
        result = await self._execute(query, run_manager)
        
        # 캐시 저장
        if result.success:
            self.cache[cache_key] = result
        
        return result
    
    async def _execute(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """실제 실행 로직 (Override 필요)"""
        raise NotImplementedError("Subclass must implement _execute method")


class ToolRegistry:
    """Tool 레지스트리"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register(self, tool: BaseTool, category: str = "general"):
        """Tool 등록"""
        self.tools[tool.name] = tool
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)
        
        logger.info(f"Registered tool: {tool.name} in category: {category}")
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Tool 가져오기"""
        return self.tools.get(tool_name)
    
    def get_by_category(self, category: str) -> List[BaseTool]:
        """카테고리별 Tool 목록"""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def list_tools(self) -> List[str]:
        """모든 Tool 이름 목록"""
        return list(self.tools.keys())
    
    def list_categories(self) -> List[str]:
        """모든 카테고리 목록"""
        return list(self.categories.keys())


# Global registry instance
tool_registry = ToolRegistry()