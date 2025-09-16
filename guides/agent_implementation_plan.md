# LangGraph 0.6.7 Agent 구현 계획

## 🎯 전체 아키텍처 개요

### 3계층 메타 에이전트 구조
```
┌─────────────────────────────────────┐
│      Level 1: 메타 관리 에이전트      │
│  • QueryAnalyzer                    │
│  • PlanningAgent                    │
│  • ExecutionManager                 │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│      Level 2: 실행 에이전트          │
│  • DataAnalysisAgent               │
│  • InformationRetrievalAgent       │
│  • DocumentGenerationAgent         │
│  • ComplianceValidationAgent       │
│  • StorageDecisionAgent            │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│      Level 3: 도구 및 API           │
│  • SQL Tools                       │
│  • Vector Search                   │
│  • External APIs                   │
│  • Template Engines                │
└─────────────────────────────────────┘
```

---

## 🔴 Level 1: 메타 관리 에이전트 구현

### 1.1 QueryAnalyzer Agent

```python
from langgraph.runtime import Runtime
from typing import Dict, Any, List
import asyncio

class QueryAnalyzerAgent:
    """사용자 질의를 분석하고 실행 전략을 수립하는 메타 에이전트"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.complexity_calculator = ComplexityCalculator()
        self.capability_mapper = CapabilityMapper()
    
    async def analyze_query_node(
        self,
        state: QueryAnalyzerState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """질의 분석 메인 노드"""
        
        query = state["raw_query"]
        
        # Step 1: 다차원 분석 (병렬 실행)
        analysis_tasks = [
            self._analyze_intent(query, runtime),
            self._extract_entities(query, runtime),
            self._calculate_complexity(query),
            self._check_feasibility(query, runtime)
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        
        # Step 2: 종합 분석
        intents, entities, complexity, feasibility = results
        
        # Step 3: 에이전트 매핑
        suggested_agents = self._map_to_agents(intents, entities, complexity)
        
        # Step 4: 컨텍스트 요구사항 도출
        context_requirements = self._derive_context_requirements(
            intents, entities, runtime
        )
        
        return {
            "parsed_intents": intents,
            "extracted_entities": entities,
            "complexity_score": complexity,
            "suggested_agents": suggested_agents,
            "context_requirements": context_requirements,
            "feasibility_check": feasibility
        }
    
    async def _analyze_intent(
        self,
        query: str,
        runtime: Runtime[AdvancedContext]
    ) -> List[Dict[str, Any]]:
        """의도 분석 - Multi-label classification"""
        
        prompt = f"""
        사용자 질의: {query}
        
        다음 의도들을 분석하고 각각의 신뢰도를 평가하세요:
        1. data_analysis: 데이터 분석, 통계, 실적 조회
        2. information_retrieval: 정보 검색, 자료 찾기
        3. document_generation: 문서 작성, 보고서 생성
        4. compliance_check: 규정 검토, 위반 확인
        5. data_storage: 데이터 저장, 기록
        
        각 의도별로 0.0~1.0의 신뢰도를 부여하고,
        주요 의도와 보조 의도를 구분하세요.
        """
        
        llm = self._get_llm(runtime)
        result = await llm.ainvoke(prompt)
        
        return self._parse_intent_result(result)
    
    def _map_to_agents(
        self,
        intents: List[Dict],
        entities: List[Dict],
        complexity: float
    ) -> List[str]:
        """의도와 엔티티를 기반으로 필요 에이전트 결정"""
        
        agent_mapping = {
            "data_analysis": "DataAnalysisAgent",
            "information_retrieval": "InformationRetrievalAgent",
            "document_generation": "DocumentGenerationAgent",
            "compliance_check": "ComplianceValidationAgent",
            "data_storage": "StorageDecisionAgent"
        }
        
        required_agents = []
        
        # 의도 기반 매핑
        for intent in intents:
            if intent["confidence"] > 0.5:
                agent = agent_mapping.get(intent["intent"])
                if agent and agent not in required_agents:
                    required_agents.append(agent)
        
        # 복잡도 기반 추가
        if complexity > 0.7 and "DataAnalysisAgent" not in required_agents:
            required_agents.append("DataAnalysisAgent")
        
        return required_agents
```

### 1.2 PlanningAgent

```python
class PlanningAgent:
    """실행 계획을 수립하는 메타 에이전트"""
    
    def __init__(self):
        self.dependency_resolver = DependencyResolver()
        self.resource_estimator = ResourceEstimator()
        self.plan_optimizer = PlanOptimizer()
    
    async def create_plan_node(
        self,
        state: PlanningState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """실행 계획 수립 메인 노드"""
        
        analyzed_query = state["analyzed_query"]
        suggested_agents = analyzed_query["suggested_agents"]
        
        # Step 1: 의존성 그래프 구축
        dependency_graph = self._build_dependency_graph(suggested_agents)
        
        # Step 2: 실행 순서 결정 (토폴로지 정렬)
        execution_order = self._topological_sort(dependency_graph)
        
        # Step 3: 병렬 실행 기회 식별
        parallel_groups = self._identify_parallel_opportunities(
            execution_order,
            dependency_graph
        )
        
        # Step 4: 리소스 할당 계획
        resource_plan = await self._plan_resources(
            parallel_groups,
            runtime
        )
        
        # Step 5: 실행 계획 생성
        execution_plan = self._create_execution_plan(
            parallel_groups,
            resource_plan,
            runtime
        )
        
        # Step 6: 대체 계획 수립
        fallback_plans = self._create_fallback_plans(
            execution_plan,
            analyzed_query
        )
        
        return {
            "execution_plan": execution_plan,
            "task_dependencies": dependency_graph,
            "resource_requirements": resource_plan,
            "parallel_opportunities": parallel_groups,
            "fallback_plans": fallback_plans
        }
    
    def _build_dependency_graph(
        self,
        agents: List[str]
    ) -> Dict[str, List[str]]:
        """에이전트 간 의존성 그래프 구축"""
        
        # 기본 의존성 규칙
        base_dependencies = {
            "DataAnalysisAgent": [],  # 독립적
            "InformationRetrievalAgent": [],  # 독립적
            "DocumentGenerationAgent": [
                "DataAnalysisAgent",
                "InformationRetrievalAgent"
            ],
            "ComplianceValidationAgent": [
                "DocumentGenerationAgent"
            ],
            "StorageDecisionAgent": [
                "DataAnalysisAgent",
                "DocumentGenerationAgent"
            ]
        }
        
        # 실제 필요한 에이전트만 필터링
        graph = {}
        for agent in agents:
            deps = base_dependencies.get(agent, [])
            # 실제 존재하는 의존성만 포함
            graph[agent] = [d for d in deps if d in agents]
        
        return graph
    
    def _create_execution_plan(
        self,
        parallel_groups: List[List[str]],
        resource_plan: Dict,
        runtime: Runtime[AdvancedContext]
    ) -> List[Dict[str, Any]]:
        """상세 실행 계획 생성"""
        
        plan = []
        
        for idx, group in enumerate(parallel_groups):
            step = {
                "step_id": f"step_{idx}",
                "agents": group,
                "parallel": len(group) > 1,
                "timeout": self._calculate_timeout(group, runtime),
                "retry_count": 3,
                "checkpoint": True,  # 체크포인트 저장
                "resources": resource_plan.get(f"step_{idx}", {}),
                "interrupt_before": self._needs_approval(group, runtime),
                "dependencies": self._get_step_dependencies(idx, parallel_groups)
            }
            plan.append(step)
        
        return plan
```

### 1.3 ExecutionManager

```python
from langgraph.types import Send, Command, interrupt

class ExecutionManagerAgent:
    """실행을 관리하고 조율하는 메타 에이전트"""
    
    def __init__(self):
        self.task_dispatcher = TaskDispatcher()
        self.result_aggregator = ResultAggregator()
        self.quality_checker = QualityChecker()
        self.replan_evaluator = ReplanEvaluator()
    
    async def manage_execution_node(
        self,
        state: ExecutionManagerState,
        runtime: Runtime[AdvancedContext]
    ) -> Union[List[Send], Dict[str, Any], str]:
        """실행 관리 메인 노드"""
        
        current_plan = state["current_plan"]
        current_step = self._get_current_step(state)
        
        # Step 1: 실행 상태 확인
        if state["execution_status"] == "initializing":
            return await self._initialize_execution(state, runtime)
        
        # Step 2: 현재 단계 에이전트 실행
        if current_step and current_step["agents"]:
            return await self._dispatch_agents(current_step, state, runtime)
        
        # Step 3: 완료된 태스크 확인
        if self._all_tasks_completed(state):
            return await self._finalize_execution(state, runtime)
        
        # Step 4: 재계획 필요 여부 확인
        if state["need_replan"]:
            return "replan"  # PlanningAgent로 전환
        
        # Step 5: 다음 단계로 진행
        return await self._proceed_to_next_step(state, runtime)
    
    async def _dispatch_agents(
        self,
        step: Dict,
        state: ExecutionManagerState,
        runtime: Runtime[AdvancedContext]
    ) -> List[Send]:
        """에이전트 디스패치"""
        
        sends = []
        
        for agent_name in step["agents"]:
            # 에이전트별 태스크 준비
            task = self._prepare_agent_task(agent_name, state, runtime)
            
            # 인터럽트 체크
            if step.get("interrupt_before"):
                approval = await self._request_approval(task, runtime)
                if not approval:
                    continue
            
            # Send 객체 생성
            sends.append(
                Send(
                    agent_name.lower(),  # 노드 이름
                    {
                        "task": task,
                        "step_id": step["step_id"],
                        "timeout": step["timeout"],
                        "retry_count": step["retry_count"]
                    }
                )
            )
        
        return sends
    
    async def _aggregate_results(
        self,
        state: ExecutionManagerState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """결과 집계"""
        
        completed_tasks = state["completed_tasks"]
        
        # 에이전트별 결과 그룹화
        results_by_agent = {}
        for task in completed_tasks:
            agent = task["agent"]
            if agent not in results_by_agent:
                results_by_agent[agent] = []
            results_by_agent[agent].append(task["result"])
        
        # 통합 전략 선택
        strategy = self._select_aggregation_strategy(results_by_agent)
        
        # 결과 통합
        if strategy == "sequential":
            final_result = self._sequential_aggregation(results_by_agent)
        elif strategy == "merge":
            final_result = self._merge_aggregation(results_by_agent)
        elif strategy == "prioritized":
            final_result = self._prioritized_aggregation(results_by_agent)
        else:
            final_result = results_by_agent
        
        return {
            "final_results": final_result,
            "aggregation_method": strategy,
            "quality_scores": self._calculate_quality_scores(final_result)
        }
```

---

## 🔵 Level 2: 실행 에이전트 구현

### 2.1 DataAnalysisAgent

```python
class DataAnalysisAgent:
    """데이터 분석 실행 에이전트"""
    
    def __init__(self):
        self.sql_generator = SQLGenerator()
        self.data_processor = DataProcessor()
        self.visualizer = DataVisualizer()
        self.cache_manager = CacheManager()
    
    async def execute_node(
        self,
        state: DataAnalysisAgentState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """데이터 분석 실행"""
        
        task = state["assigned_task"]
        
        # Step 1: 캐시 확인
        cache_key = self._generate_cache_key(task)
        if cached := await self.cache_manager.get(cache_key):
            return {"result": cached, "cache_hit": True}
        
        # Step 2: SQL 쿼리 생성
        queries = await self._generate_sql_queries(task, runtime)
        
        # Step 3: 쿼리 실행
        raw_data = await self._execute_queries(queries, runtime)
        
        # Step 4: 데이터 처리 및 분석
        processed_data = await self._process_data(raw_data, task)
        
        # Step 5: 시각화 생성
        visualizations = await self._create_visualizations(
            processed_data,
            task
        )
        
        # Step 6: 결과 캐싱
        result = {
            "raw_data": raw_data,
            "processed_data": processed_data,
            "statistics": self._calculate_statistics(processed_data),
            "visualizations": visualizations
        }
        
        await self.cache_manager.set(cache_key, result)
        
        return {
            "result": result,
            "confidence_score": self._calculate_confidence(result),
            "execution_time": self._get_execution_time()
        }
    
    async def _generate_sql_queries(
        self,
        task: Dict,
        runtime: Runtime[AdvancedContext]
    ) -> List[str]:
        """Text2SQL 쿼리 생성"""
        
        prompt = f"""
        다음 요청을 SQL 쿼리로 변환하세요.
        
        요청: {task['description']}
        엔티티: {task.get('entities', [])}
        
        사용 가능한 테이블:
        - Employee_Performance: 직원 실적
        - Customer_Trend: 거래처 트렌드
        - HR_Info: 인사 정보
        
        주의사항:
        - 보안을 위해 파라미터화된 쿼리 사용
        - 성능을 위해 인덱스 활용
        - 필요시 여러 쿼리로 분할
        """
        
        llm = self._get_llm(runtime)
        sql_result = await llm.ainvoke(prompt)
        
        # SQL 검증
        queries = self._parse_and_validate_sql(sql_result)
        
        return queries
```

### 2.2 InformationRetrievalAgent

```python
class InformationRetrievalAgent:
    """정보 검색 실행 에이전트"""
    
    def __init__(self):
        self.internal_searcher = InternalSearcher()
        self.vector_searcher = VectorSearcher()
        self.web_searcher = WebSearcher()
        self.relevance_ranker = RelevanceRanker()
    
    async def execute_node(
        self,
        state: InformationRetrievalAgentState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """정보 검색 실행"""
        
        task = state["assigned_task"]
        query = task["query"]
        
        # Step 1: 검색 소스 결정
        search_sources = self._determine_search_sources(task, runtime)
        
        # Step 2: 병렬 검색 실행
        search_tasks = []
        
        if "internal_db" in search_sources:
            search_tasks.append(
                self.internal_searcher.search(query, runtime)
            )
        
        if "vector_db" in search_sources:
            search_tasks.append(
                self.vector_searcher.search(query, runtime)
            )
        
        if "web" in search_sources:
            search_tasks.append(
                self.web_searcher.search(query, runtime)
            )
        
        search_results = await asyncio.gather(*search_tasks)
        
        # Step 3: 결과 통합 및 중복 제거
        merged_results = self._merge_and_deduplicate(search_results)
        
        # Step 4: 관련성 평가 및 순위 지정
        ranked_results = await self.relevance_ranker.rank(
            merged_results,
            query
        )
        
        # Step 5: 상위 결과 필터링
        filtered_results = self._filter_top_results(
            ranked_results,
            task.get("max_results", 10)
        )
        
        # Step 6: 출처 추적
        sources = self._extract_sources(filtered_results)
        
        return {
            "result": {
                "search_results": filtered_results,
                "sources": sources,
                "total_found": len(merged_results)
            },
            "confidence_score": self._calculate_search_confidence(
                filtered_results
            ),
            "execution_time": self._get_execution_time()
        }
```

### 2.3 DocumentGenerationAgent

```python
class DocumentGenerationAgent:
    """문서 생성 실행 에이전트"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.content_generator = ContentGenerator()
        self.formatter = DocumentFormatter()
        self.storage_handler = StorageHandler()
    
    async def execute_node(
        self,
        state: DocumentGenerationAgentState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """문서 생성 실행"""
        
        task = state["assigned_task"]
        doc_type = task["document_type"]
        
        # Step 1: 템플릿 로드
        template = self.template_manager.get_template(doc_type)
        
        # Step 2: 데이터 수집 및 준비
        prepared_data = await self._prepare_document_data(
            task,
            state,
            runtime
        )
        
        # Step 3: 콘텐츠 생성
        content = await self.content_generator.generate(
            template,
            prepared_data,
            runtime
        )
        
        # Step 4: 문서 포맷팅
        formatted_doc = await self.formatter.format(
            content,
            doc_type,
            task.get("format", "pdf")
        )
        
        # Step 5: 문서 저장
        document_id = await self.storage_handler.save(
            formatted_doc,
            doc_type,
            runtime
        )
        
        # Step 6: 메타데이터 생성
        metadata = {
            "document_id": document_id,
            "document_type": doc_type,
            "created_at": datetime.now().isoformat(),
            "created_by": runtime.context.user_id,
            "file_size": len(formatted_doc),
            "storage_location": f"/documents/{document_id}"
        }
        
        return {
            "result": {
                "document_id": document_id,
                "content": content,
                "metadata": metadata,
                "document_url": f"/api/documents/{document_id}"
            },
            "confidence_score": 0.95,
            "execution_time": self._get_execution_time()
        }
```

### 2.4 ComplianceValidationAgent

```python
class ComplianceValidationAgent:
    """규정 검증 실행 에이전트"""
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.validator = ComplianceValidator()
        self.risk_assessor = RiskAssessor()
    
    async def execute_node(
        self,
        state: ComplianceValidationAgentState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """규정 검증 실행"""
        
        task = state["assigned_task"]
        target = task["validation_target"]
        
        # Step 1: 적용 규정 결정
        applicable_rules = self._determine_applicable_rules(
            target,
            runtime
        )
        
        # Step 2: 규정별 검증 실행
        validation_results = []
        
        for rule in applicable_rules:
            result = await self.validator.validate(
                target,
                rule,
                runtime
            )
            validation_results.append(result)
        
        # Step 3: 위반 사항 식별
        violations = self._identify_violations(validation_results)
        
        # Step 4: 리스크 평가
        risk_level = await self.risk_assessor.assess(
            violations,
            target
        )
        
        # Step 5: 권고사항 생성
        recommendations = await self._generate_recommendations(
            violations,
            risk_level,
            runtime
        )
        
        return {
            "result": {
                "validation_results": validation_results,
                "violations": violations,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "compliant": len(violations) == 0
            },
            "confidence_score": self._calculate_validation_confidence(
                validation_results
            ),
            "execution_time": self._get_execution_time()
        }
```

### 2.5 StorageDecisionAgent

```python
class StorageDecisionAgent:
    """저장 결정 실행 에이전트"""
    
    def __init__(self):
        self.data_analyzer = DataAnalyzer()
        self.schema_mapper = SchemaMapper()
        self.storage_executor = StorageExecutor()
    
    async def execute_node(
        self,
        state: StorageDecisionAgentState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """저장 결정 및 실행"""
        
        task = state["assigned_task"]
        data = task["data_to_store"]
        
        # Step 1: 데이터 분석
        data_analysis = await self.data_analyzer.analyze(data)
        
        # Step 2: 저장소 결정
        storage_decision = self._decide_storage(
            data_analysis,
            runtime
        )
        
        # Step 3: 스키마 매핑
        if storage_decision == "structured_db":
            schema_mapping = await self.schema_mapper.map_to_schema(
                data,
                data_analysis
            )
        else:
            schema_mapping = None
        
        # Step 4: 저장 실행
        storage_result = await self.storage_executor.store(
            data,
            storage_decision,
            schema_mapping,
            runtime
        )
        
        return {
            "result": {
                "storage_decision": storage_decision,
                "storage_location": storage_result["location"],
                "storage_metadata": storage_result["metadata"],
                "success": storage_result["success"]
            },
            "confidence_score": 0.9,
            "execution_time": self._get_execution_time()
        }
    
    def _decide_storage(
        self,
        analysis: Dict,
        runtime: Runtime[AdvancedContext]
    ) -> str:
        """저장소 결정 로직"""
        
        # 구조화 가능 여부
        if analysis["structured_ratio"] > 0.8:
            return "structured_db"
        
        # 텍스트 중심 데이터
        elif analysis["text_ratio"] > 0.7:
            return "vector_db"
        
        # 비정형 데이터
        elif analysis["binary_content"]:
            return "unstructured_db"
        
        # 하이브리드
        else:
            return "hybrid"
```

---

## 🔧 그래프 구성 및 연결

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

class GraphBuilder:
    """전체 그래프 구성"""
    
    async def build_graph(self) -> CompiledGraph:
        """메인 그래프 구성"""
        
        # 그래프 초기화
        builder = StateGraph(
            state_schema=GlobalSessionState,
            context_schema=AdvancedContext
        )
        
        # Level 1: 메타 에이전트 노드
        builder.add_node("query_analyzer", QueryAnalyzerAgent().analyze_query_node)
        builder.add_node("planner", PlanningAgent().create_plan_node)
        builder.add_node("executor", ExecutionManagerAgent().manage_execution_node)
        
        # Level 2: 실행 에이전트 노드
        builder.add_node("data_analysis", DataAnalysisAgent().execute_node)
        builder.add_node("info_retrieval", InformationRetrievalAgent().execute_node)
        builder.add_node("doc_generation", DocumentGenerationAgent().execute_node)
        builder.add_node("compliance", ComplianceValidationAgent().execute_node)
        builder.add_node("storage", StorageDecisionAgent().execute_node)
        
        # 엣지 연결
        self._connect_edges(builder)
        
        # 체크포인터 설정
        checkpointer = await AsyncSqliteSaver.from_conn_string(
            "checkpoints.db"
        )
        
        # 컴파일
        return builder.compile(
            checkpointer=checkpointer,
            durability="async"
        )
    
    def _connect_edges(self, builder: StateGraph):
        """엣지 연결"""
        
        # 시작 -> 질의 분석
        builder.add_edge(START, "query_analyzer")
        
        # 질의 분석 -> 계획
        builder.add_edge("query_analyzer", "planner")
        
        # 계획 -> 실행
        builder.add_edge("planner", "executor")
        
        # 실행 관리자 -> 실행 에이전트 (조건부)
        builder.add_conditional_edges(
            "executor",
            self._route_to_agent,
            {
                "data_analysis": "data_analysis",
                "info_retrieval": "info_retrieval",
                "doc_generation": "doc_generation",
                "compliance": "compliance",
                "storage": "storage",
                "replan": "planner",
                "end": END
            }
        )
        
        # 실행 에이전트 -> 실행 관리자 (피드백 루프)
        for agent in ["data_analysis", "info_retrieval", "doc_generation", "compliance", "storage"]:
            builder.add_edge(agent, "executor")
    
    def _route_to_agent(self, state: GlobalSessionState) -> str:
        """에이전트 라우팅 로직"""
        
        exec_state = state["execution_manager_state"]
        
        # 재계획 필요
        if exec_state["need_replan"]:
            return "replan"
        
        # 완료
        if exec_state["execution_status"] == "completed":
            return "end"
        
        # 다음 에이전트 결정
        current_plan = exec_state["current_plan"]
        current_step = self._get_current_step(exec_state)
        
        if current_step and current_step["agents"]:
            # 첫 번째 에이전트 반환 (Send로 병렬 처리)
            agent_map = {
                "DataAnalysisAgent": "data_analysis",
                "InformationRetrievalAgent": "info_retrieval",
                "DocumentGenerationAgent": "doc_generation",
                "ComplianceValidationAgent": "compliance",
                "StorageDecisionAgent": "storage"
            }
            return agent_map.get(current_step["agents"][0], "end")
        
        return "end"
```

---

## 🚀 구현 로드맵

### Phase 1: 기초 구축 (Week 1-2)
```python
# 1. State 정의
- GlobalSessionState
- 메타 에이전트 States
- 실행 에이전트 States

# 2. 기본 그래프 구조
- 노드 정의
- 엣지 연결
- 체크포인터 설정

# 3. QueryAnalyzer 구현
- 의도 분석
- 엔티티 추출
- 복잡도 계산
```

### Phase 2: 핵심 에이전트 (Week 3-4)
```python
# 1. PlanningAgent
- 의존성 그래프
- 실행 계획 수립

# 2. ExecutionManager
- 태스크 디스패치
- 결과 집계

# 3. DataAnalysisAgent
- SQL 생성
- 데이터 처리
```

### Phase 3: 실행 에이전트 (Week 5-6)
```python
# 1. InformationRetrievalAgent
- 멀티 소스 검색
- 관련성 평가

# 2. DocumentGenerationAgent
- 템플릿 관리
- 문서 생성

# 3. ComplianceValidationAgent
- 규정 검증
- 리스크 평가
```

### Phase 4: 고도화 (Week 7-8)
```python
# 1. Human-in-the-Loop
- 승인 프로세스
- 인터럽트 처리

# 2. 에러 복구
- 재시도 로직
- 대체 경로

# 3. 성능 최적화
- 캐싱
- 병렬 처리
```

### Phase 5: 통합 테스트 (Week 9-10)
```python
# 1. 단위 테스트
- 각 에이전트 테스트
- State 전환 테스트

# 2. 통합 테스트
- End-to-End 시나리오
- 부하 테스트

# 3. 배포 준비
- 문서화
- 모니터링 설정
```

---

## 📊 성능 메트릭

### 목표 KPI
| 메트릭 | 목표값 | 측정 방법 |
|--------|--------|-----------|
| 평균 응답 시간 | < 5초 | End-to-End |
| 에이전트 정확도 | > 90% | 검증 세트 |
| 병렬 처리율 | > 60% | 실행 로그 |
| 캐시 히트율 | > 50% | 캐시 통계 |
| 에러 복구율 | > 95% | 에러 로그 |

---

**버전**: 1.0.0  
**작성일**: 2025-01-10  
**기반**: LangGraph 0.6.7
