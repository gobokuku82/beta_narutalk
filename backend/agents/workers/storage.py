"""
Storage Decision Agent
저장 전략 결정 및 실행 에이전트
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import hashlib

logger = logging.getLogger(__name__)


class StorageDecisionAgent:
    """데이터 저장 전략 결정 및 실행을 담당하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize storage decision agent"""
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.name = "StorageDecisionAgent"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        start_time = datetime.now()

        try:
            # Extract task parameters
            data_to_store = task.get("data_to_store", {})
            data_type = task.get("data_type", "general")
            storage_requirements = task.get("storage_requirements", {})
            retention_period = task.get("retention_period", 365)
            encryption_required = task.get("encryption_required", False)
            backup_strategy = task.get("backup_strategy", "daily")

            # Determine storage strategy
            storage_strategy = await self._determine_storage_strategy(
                data_to_store, data_type, storage_requirements
            )

            # Apply storage optimizations
            optimized_data = await self._optimize_for_storage(
                data_to_store, storage_strategy
            )

            # Execute storage
            storage_result = await self._execute_storage(
                optimized_data, storage_strategy, encryption_required
            )

            # Setup backup if needed
            if backup_strategy != "none":
                backup_config = await self._configure_backup(
                    storage_result["storage_id"], backup_strategy
                )
                storage_result["backup_config"] = backup_config

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "confidence_score": 0.95,
                "execution_time": execution_time,
                "storage_location": storage_result["location"],
                "storage_method": storage_strategy["method"],
                "storage_id": storage_result["storage_id"],
                "metadata_stored": storage_result["metadata"],
                "compression_used": storage_strategy.get("compression", False),
                "encryption_applied": encryption_required,
                "retention_period": retention_period,
                "backup_strategy": backup_strategy
            }

        except Exception as e:
            logger.error(f"Storage decision failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "confidence_score": 0.0,
                "execution_time": execution_time,
                "error": str(e)
            }

    async def _determine_storage_strategy(
        self, data: Dict, data_type: str, requirements: Dict
    ) -> Dict[str, Any]:
        """최적의 저장 전략 결정"""

        # Analyze data characteristics
        data_size = self._estimate_data_size(data)
        access_pattern = requirements.get("access_pattern", "regular")
        performance_needs = requirements.get("performance", "standard")

        strategy = {
            "method": "database",  # default
            "compression": False,
            "indexing": [],
            "partitioning": None,
            "cache_strategy": None
        }

        # Determine storage method based on data type and size
        if data_type == "document":
            strategy["method"] = "document_store"
            if data_size > 1000000:  # > 1MB
                strategy["compression"] = True
        elif data_type == "structured":
            strategy["method"] = "relational_db"
            strategy["indexing"] = await self._determine_indexes(data)
        elif data_type == "time_series":
            strategy["method"] = "time_series_db"
            strategy["partitioning"] = "monthly"
        elif data_type == "blob" or data_size > 10000000:  # > 10MB
            strategy["method"] = "object_storage"
            strategy["compression"] = True
        elif data_type == "cache":
            strategy["method"] = "redis"
            strategy["cache_strategy"] = "LRU"

        # Adjust based on access pattern
        if access_pattern == "frequent":
            strategy["cache_strategy"] = "aggressive"
        elif access_pattern == "rare":
            strategy["compression"] = True

        # Performance optimizations
        if performance_needs == "high":
            strategy["indexing"].append("performance_index")
            strategy["cache_strategy"] = "preload"

        logger.info(f"Storage strategy determined: {strategy}")
        return strategy

    async def _optimize_for_storage(
        self, data: Dict, strategy: Dict
    ) -> Dict[str, Any]:
        """저장을 위한 데이터 최적화"""

        optimized = data.copy()

        # Apply compression if needed
        if strategy.get("compression"):
            optimized = self._compress_data(optimized)

        # Remove redundant fields
        optimized = self._remove_redundancy(optimized)

        # Normalize data structure
        if strategy["method"] == "relational_db":
            optimized = self._normalize_for_rdb(optimized)
        elif strategy["method"] == "document_store":
            optimized = self._flatten_for_document(optimized)

        return optimized

    async def _execute_storage(
        self, data: Dict, strategy: Dict, encrypt: bool
    ) -> Dict[str, Any]:
        """실제 저장 실행 (시뮬레이션)"""

        # Generate storage ID
        storage_id = self._generate_storage_id(data)

        # Simulate encryption
        if encrypt:
            data = self._simulate_encryption(data)

        # Determine storage location based on strategy
        location_map = {
            "database": f"postgresql://main_db/table/{storage_id}",
            "relational_db": f"postgresql://main_db/table/{storage_id}",
            "document_store": f"mongodb://doc_store/collection/{storage_id}",
            "time_series_db": f"influxdb://tsdb/measurement/{storage_id}",
            "object_storage": f"s3://bucket/objects/{storage_id}",
            "redis": f"redis://cache/key/{storage_id}"
        }

        location = location_map.get(strategy["method"], f"storage://{storage_id}")

        # Create metadata
        metadata = {
            "storage_id": storage_id,
            "stored_at": datetime.now().isoformat(),
            "data_type": type(data).__name__,
            "size_bytes": self._estimate_data_size(data),
            "strategy": strategy,
            "encrypted": encrypt,
            "checksum": self._calculate_checksum(data)
        }

        # Simulate storage delay
        await asyncio.sleep(0.5)

        logger.info(f"Data stored at: {location}")

        return {
            "storage_id": storage_id,
            "location": location,
            "metadata": metadata,
            "success": True
        }

    async def _configure_backup(
        self, storage_id: str, backup_strategy: str
    ) -> Dict[str, Any]:
        """백업 구성 설정"""

        backup_config = {
            "enabled": True,
            "strategy": backup_strategy,
            "storage_id": storage_id
        }

        if backup_strategy == "realtime":
            backup_config.update({
                "type": "continuous_replication",
                "target": f"backup://realtime/{storage_id}",
                "lag_ms": 100
            })
        elif backup_strategy == "daily":
            backup_config.update({
                "type": "scheduled_snapshot",
                "schedule": "0 2 * * *",  # 2 AM daily
                "target": f"backup://daily/{storage_id}",
                "retention_days": 30
            })
        elif backup_strategy == "weekly":
            backup_config.update({
                "type": "scheduled_snapshot",
                "schedule": "0 2 * * 0",  # Sunday 2 AM
                "target": f"backup://weekly/{storage_id}",
                "retention_days": 90
            })

        logger.info(f"Backup configured: {backup_config}")
        return backup_config

    def _estimate_data_size(self, data: Any) -> int:
        """데이터 크기 추정 (bytes)"""
        try:
            return len(json.dumps(data, default=str).encode('utf-8'))
        except:
            return 0

    async def _determine_indexes(self, data: Dict) -> List[str]:
        """인덱스 필드 결정"""
        indexes = []

        # Common index candidates
        for key in data.keys():
            if any(pattern in key.lower() for pattern in ['id', 'name', 'date', 'time']):
                indexes.append(key)

        return indexes[:5]  # Limit to 5 indexes

    def _compress_data(self, data: Dict) -> Dict:
        """데이터 압축 시뮬레이션"""
        return {
            "compressed": True,
            "algorithm": "gzip",
            "original_size": self._estimate_data_size(data),
            "data": str(data)[:100] + "..."  # Simplified representation
        }

    def _remove_redundancy(self, data: Dict) -> Dict:
        """중복 제거"""
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != "" and value != []:
                cleaned[key] = value
        return cleaned

    def _normalize_for_rdb(self, data: Dict) -> Dict:
        """관계형 DB를 위한 정규화"""
        # Simple normalization simulation
        normalized = {
            "main_table": {},
            "related_tables": []
        }

        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                normalized["main_table"][key] = value
            elif isinstance(value, (list, dict)):
                normalized["related_tables"].append({
                    "table_name": f"{key}_table",
                    "data": value
                })

        return normalized

    def _flatten_for_document(self, data: Dict) -> Dict:
        """문서 저장소를 위한 평탄화"""
        # Keep nested structure but ensure it's JSON-serializable
        return json.loads(json.dumps(data, default=str))

    def _generate_storage_id(self, data: Dict) -> str:
        """고유 저장 ID 생성"""
        timestamp = datetime.now().isoformat()
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_input = f"{timestamp}_{data_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _simulate_encryption(self, data: Dict) -> Dict:
        """암호화 시뮬레이션"""
        return {
            "encrypted": True,
            "algorithm": "AES-256",
            "data": f"encrypted_{self._generate_storage_id(data)}"
        }

    def _calculate_checksum(self, data: Dict) -> str:
        """체크섬 계산"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드 실행 메서드"""

        # Extract task from state
        execution_state = state.get("execution_manager_state", {})
        pending_tasks = execution_state.get("pending_tasks", [])

        if not pending_tasks:
            logger.warning("No pending tasks for storage decision")
            return state

        # Get first task for this agent
        task = None
        for t in pending_tasks:
            if t.get("agent") == "StorageDecisionAgent":
                task = t
                break

        if not task:
            logger.warning("No storage decision task found")
            return state

        # Execute task
        result = await self.execute(task)

        # Update state
        completed_tasks = execution_state.get("completed_tasks", [])
        completed_tasks.append({
            "task_id": task.get("task_id"),
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Remove from pending
        pending_tasks.remove(task)

        state["execution_manager_state"]["pending_tasks"] = pending_tasks
        state["execution_manager_state"]["completed_tasks"] = completed_tasks

        # Store agent-specific result
        if "agent_results" not in state:
            state["agent_results"] = {}
        state["agent_results"][self.name] = result

        logger.info(f"Storage decision completed for task {task.get('task_id')}")
        return state