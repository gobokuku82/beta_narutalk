# Registry System - 약한 결합 에이전트/툴 관리

에이전트와 툴을 레지스트리에 등록하여 약한 결합(Loose Coupling)으로 관리하는 시스템입니다.

## 목차
- [개요](#개요)
- [구조](#구조)
- [주요 기능](#주요-기능)
- [사용 방법](#사용-방법)
- [예제](#예제)
- [API Reference](#api-reference)

## 개요

레지스트리 패턴을 사용하여 에이전트와 툴을 동적으로 등록하고 관리합니다. 이를 통해:

- **약한 결합**: 컴포넌트 간 직접 의존성 제거
- **동적 로딩**: 런타임에 컴포넌트 등록 및 로드
- **확장성**: 새로운 툴/에이전트 추가 용이
- **의존성 관리**: 자동 의존성 해결 및 검증

## 구조

```
registry/
├── __init__.py              # 모듈 초기화
├── base_registry.py         # 기본 레지스트리 클래스
├── tool_registry.py         # 툴 레지스트리
├── agent_registry.py        # 에이전트 레지스트리
├── registry_manager.py      # 통합 관리자
├── auto_register.py         # 자동 등록
├── examples.py              # 사용 예제
└── README.md                # 문서
```

## 주요 기능

### 1. Tool Registry
툴 클래스와 함수를 등록하고 관리합니다.

```python
from backend.service.registry import tool_registry, register_tool

# 데코레이터로 등록
@register_tool(name="calculator", category="math")
class Calculator:
    def add(self, a, b):
        return a + b

# 사용
calc = tool_registry.create_tool("calculator")
result = calc.add(10, 20)
```

### 2. Agent Registry
에이전트와 서브그래프를 등록하고 관리합니다.

```python
from backend.service.registry import agent_registry, register_agent, AgentType

# 데코레이터로 등록
@register_agent(
    name="worker",
    agent_type=AgentType.WORKER,
    dependencies=["calculator"]
)
class WorkerAgent:
    def process(self, data):
        return f"Processed: {data}"

# 사용
worker = agent_registry.create_agent("worker")
```

### 3. Registry Manager
모든 레지스트리를 통합 관리합니다.

```python
from backend.service.registry import get_registry_manager

manager = get_registry_manager()

# 통계 확인
stats = manager.get_statistics()
print(f"Tools: {stats['tools']['total']}")
print(f"Agents: {stats['agents']['total']}")

# 검색
results = manager.search("calculator")
```

### 4. 자동 등록
기존 컴포넌트를 자동으로 레지스트리에 등록합니다.

```python
from backend.service.registry.auto_register import initialize_registries

# 모든 기존 툴/에이전트 자동 등록
initialize_registries()
```

## 사용 방법

### 기본 사용

#### 1. 툴 등록

**데코레이터 방식:**
```python
from backend.service.registry import register_tool

@register_tool(
    name="sql_executor",
    category="database",
    description="Execute SQL queries",
    version="1.0.0"
)
class SQLExecutor:
    def execute(self, query):
        # Implementation
        pass
```

**수동 등록:**
```python
from backend.service.registry import tool_registry

tool_registry.register_tool(
    name="sql_executor",
    tool_class=SQLExecutor,
    category="database",
    description="Execute SQL queries"
)
```

#### 2. 에이전트 등록

**서브그래프 등록:**
```python
from backend.service.registry import register_subgraph

@register_subgraph(
    name="data_collection",
    description="Collect data from databases",
    dependencies=["sql_executor", "sql_generator"]
)
class DataCollectionSubgraph:
    def build_graph(self):
        # Implementation
        pass
```

**일반 에이전트 등록:**
```python
from backend.service.registry import register_agent, AgentType

@register_agent(
    name="supervisor",
    agent_type=AgentType.SUPERVISOR,
    capabilities=["reasoning", "planning"]
)
class SupervisorAgent:
    pass
```

#### 3. 레지스트리에서 사용

```python
from backend.service.registry import tool_registry, agent_registry

# 툴 생성 및 사용
tool = tool_registry.create_tool("sql_executor")
result = tool.execute("SELECT * FROM table")

# 에이전트 생성 및 사용
agent = agent_registry.create_agent("supervisor")
```

### 의존성 관리

#### 의존성 검증
```python
from backend.service.registry import agent_registry

# 의존성 확인
deps = agent_registry.get_dependencies("data_collection")
print(f"Dependencies: {deps}")

# 의존성 검증
is_valid, missing = agent_registry.validate_dependencies("data_collection")
if not is_valid:
    print(f"Missing dependencies: {missing}")
```

#### 자동 의존성 해결
```python
from backend.service.registry import get_registry_manager

manager = get_registry_manager()

# 모든 의존성 자동 해결 및 생성
resolved = manager.resolve_dependencies("data_collection")
# resolved = {"sql_executor": <instance>, "sql_generator": <instance>}
```

### 검색 및 필터링

```python
from backend.service.registry import tool_registry, agent_registry, AgentType

# 카테고리로 툴 검색
calc_tools = tool_registry.list_by_category("calculation")

# 타입으로 에이전트 검색
workers = agent_registry.list_by_type(AgentType.WORKER)
subgraphs = agent_registry.list_subgraphs()

# 능력으로 에이전트 검색
data_agents = agent_registry.find_by_capability("data_processing")

# 전체 검색
from backend.service.registry import get_registry_manager
manager = get_registry_manager()
results = manager.search("sql")  # {"tools": [...], "agents": [...]}
```

### 오케스트레이터와 통합

레지스트리를 사용하는 오케스트레이터:

```python
from backend.service.orchestrator.registry_based_orchestrator import (
    RegistryBasedOrchestrator
)
from backend.service.registry.auto_register import initialize_registries

# 1. 레지스트리 초기화
initialize_registries()

# 2. 레지스트리 기반 오케스트레이터 생성
orchestrator = RegistryBasedOrchestrator(use_registry=True)

# 3. 워크플로우 빌드 (레지스트리에서 컴포넌트 로드)
graph = orchestrator.build_graph()

# 4. 레지스트리 정보 확인
info = orchestrator.get_registry_info()
print(f"Using registry: {info['using_registry']}")
```

## 예제

### Example 1: 커스텀 툴 등록

```python
from backend.service.registry import register_tool, tool_registry

@register_tool(name="text_processor", category="nlp")
class TextProcessor:
    """Process text data"""

    def clean(self, text: str) -> str:
        return text.strip().lower()

    def tokenize(self, text: str) -> list:
        return text.split()

# 사용
processor = tool_registry.create_tool("text_processor")
cleaned = processor.clean("  Hello World  ")
tokens = processor.tokenize("hello world")
```

### Example 2: 함수를 툴로 등록

```python
from backend.service.registry import tool_function

@tool_function(name="add_numbers", category="math")
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

# 사용
from backend.service.registry import tool_registry
adder = tool_registry.create_tool("add_numbers")
result = adder.execute(10, 20)
```

### Example 3: 의존성이 있는 에이전트

```python
from backend.service.registry import register_agent, AgentType, get_registry_manager

@register_agent(
    name="data_processor",
    agent_type=AgentType.WORKER,
    dependencies=["sql_executor", "text_processor"],
    capabilities=["data_processing"]
)
class DataProcessor:
    def __init__(self):
        # 의존성은 레지스트리 매니저로 해결
        manager = get_registry_manager()
        self.deps = manager.resolve_dependencies("data_processor")
        self.sql = self.deps["sql_executor"]
        self.text = self.deps["text_processor"]

    def process(self, query: str):
        data = self.sql.execute(query)
        # Process data...
        return data

# 사용 (의존성 자동 해결)
from backend.service.registry import agent_registry
processor = agent_registry.create_agent("data_processor")
```

### Example 4: 레지스트리 상태 관리

```python
from backend.service.registry import get_registry_manager
from pathlib import Path

manager = get_registry_manager()

# 통계 확인
stats = manager.get_statistics()
print(f"Total tools: {stats['tools']['total']}")
print(f"Total agents: {stats['agents']['total']}")

# 상태 내보내기
state = manager.export_all()

# 파일로 저장
manager.save_to_file(Path("registry_state.json"))

# 요약 출력
manager.print_summary()
```

### Example 5: 자동 등록 및 검증

```python
from backend.service.registry.auto_register import initialize_registries
from backend.service.registry import get_registry_manager

# 모든 기존 컴포넌트 자동 등록
counts = initialize_registries()
print(f"Auto-registered: {counts['tools']} tools, {counts['agents']} agents")

# 전체 검증
manager = get_registry_manager()
validation = manager.validate_all()

if not validation["valid"]:
    print("Issues found:")
    for issue in validation["issues"]:
        print(f"  - {issue['type']}: {issue['agent']} missing {issue['missing']}")
```

## API Reference

### BaseRegistry

기본 레지스트리 클래스.

```python
class BaseRegistry:
    def register(name, item, metadata, tags, version, override)
    def unregister(name)
    def get(name, default)
    def has(name)
    def list_all()
    def list_by_tag(tag)
    def search(query)
    def count()
    def clear()
```

### ToolRegistry

툴 레지스트리.

```python
class ToolRegistry(BaseRegistry):
    def register_tool(name, tool_class, category, description, ...)
    def get_tool(name)
    def create_tool(name, *args, **kwargs)
    def list_by_category(category)
    def list_categories()
    def get_tool_info(name)
```

**데코레이터:**
```python
@register_tool(name, category, description, version, ...)
@tool_function(name, category, description, ...)
```

### AgentRegistry

에이전트 레지스트리.

```python
class AgentRegistry(BaseRegistry):
    def register_agent(name, agent_class, agent_type, dependencies, ...)
    def register_subgraph(name, subgraph_class, input_state, output_state, ...)
    def get_agent(name)
    def create_agent(name, *args, **kwargs)
    def list_by_type(agent_type)
    def list_supervisors()
    def list_subgraphs()
    def get_dependencies(name)
    def validate_dependencies(name)
    def find_by_capability(capability)
```

**데코레이터:**
```python
@register_agent(name, agent_type, dependencies, capabilities, ...)
@register_subgraph(name, input_state, output_state, dependencies, ...)
```

**AgentType Enum:**
```python
class AgentType(Enum):
    SUPERVISOR = "supervisor"
    SUBGRAPH = "subgraph"
    WORKER = "worker"
    TOOL = "tool"
    CUSTOM = "custom"
```

### RegistryManager

통합 레지스트리 관리자.

```python
class RegistryManager:
    # Tool management
    def register_tool(name, tool_class, **kwargs)
    def get_tool(name)
    def create_tool(name, *args, **kwargs)
    def list_tools(category)

    # Agent management
    def register_agent(name, agent_class, **kwargs)
    def register_subgraph(name, subgraph_class, **kwargs)
    def get_agent(name)
    def create_agent(name, *args, **kwargs)
    def list_agents(agent_type)

    # Dependency management
    def validate_agent_dependencies(agent_name)
    def resolve_dependencies(agent_name)

    # Search and discovery
    def search(query)
    def find_by_capability(capability)
    def get_tool_categories()
    def get_agent_types()

    # Statistics and info
    def get_statistics()
    def get_info(name)

    # Export/Import
    def export_all()
    def save_to_file(file_path)
    def validate_all()

    # Display
    def print_summary()
```

**Global Instance:**
```python
from backend.service.registry import get_registry_manager
manager = get_registry_manager()
```

### Auto Registration

자동 등록 함수들.

```python
def auto_register_tools() -> int
def auto_register_agents() -> int
def auto_register_all() -> dict[str, int]
def initialize_registries() -> None
```

## 베스트 프랙티스

### 1. 애플리케이션 시작 시 초기화

```python
# main.py 또는 __init__.py
from backend.service.registry.auto_register import initialize_registries

# 앱 시작 시 한 번 실행
initialize_registries()
```

### 2. 데코레이터 사용

```python
# 명시적이고 선언적인 방식 선호
@register_tool(name="my_tool", category="custom")
class MyTool:
    pass
```

### 3. 의존성 명시

```python
# 의존성을 명확히 선언
@register_agent(
    name="my_agent",
    dependencies=["tool1", "tool2"],
    capabilities=["feature1"]
)
class MyAgent:
    pass
```

### 4. 버전 관리

```python
# 버전 정보 포함
@register_tool(
    name="my_tool",
    version="2.0.0",  # Semantic versioning
    category="custom"
)
class MyTool:
    pass
```

### 5. 메타데이터 활용

```python
# 유용한 메타데이터 추가
@register_tool(
    name="my_tool",
    category="custom",
    author="Your Name",
    license="MIT",
    documentation_url="https://..."
)
class MyTool:
    pass
```

## 트러블슈팅

### Q: 컴포넌트가 등록되지 않아요
A: `initialize_registries()`를 호출했는지 확인하거나, 데코레이터가 올바르게 적용되었는지 확인하세요.

### Q: 의존성 에러가 발생해요
A: `manager.validate_all()`로 누락된 의존성을 확인하세요.

```python
manager = get_registry_manager()
validation = manager.validate_all()
print(validation["issues"])
```

### Q: 레지스트리에서 컴포넌트를 찾을 수 없어요
A: 레지스트리 내용을 확인하세요.

```python
manager = get_registry_manager()
manager.print_summary()
print(manager.list_tools())
print(manager.list_agents())
```

## 예제 실행

```bash
# 모든 예제 실행
python -m backend.service.registry.examples

# 특정 예제만
python -c "
from backend.service.registry.examples import example_using_tools
example_using_tools()
"
```

## 확장하기

### 새로운 레지스트리 타입 추가

```python
from backend.service.registry.base_registry import BaseRegistry

class MyCustomRegistry(BaseRegistry):
    def __init__(self):
        super().__init__(name="MyCustomRegistry")

    def register_custom(self, name, item, **kwargs):
        self.register(name=name, item=item, **kwargs)
```

### 커스텀 검증 로직

```python
class CustomAgentRegistry(AgentRegistry):
    def validate_dependencies(self, name):
        # Custom validation logic
        is_valid, missing = super().validate_dependencies(name)
        # Additional checks...
        return is_valid, missing
```

## 라이선스

MIT License
