"""
System Configuration
Static settings that don't change during runtime
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    System-wide static configuration
    These values are read at startup and don't change during execution
    """
    
    # ============ System Paths ============
    BASE_DIR = Path(__file__).parent.parent.parent.parent  # Project root
    DB_DIR = BASE_DIR / "database" / "storage"
    CHECKPOINT_DIR = BASE_DIR / "checkpoints"
    MODEL_DIR = BASE_DIR / "models"
    LOG_DIR = BASE_DIR / "logs"
    
    # Create directories if they don't exist
    for directory in [CHECKPOINT_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ============ Database Paths ============
    DATABASES = {
        "hr_info": DB_DIR / "hr_information" / "hr_data.db",
        "hr_rules": DB_DIR / "hr_rules" / "chromadb",
        "sales_performance": DB_DIR / "sales_performance" / "sales_performance_db.db",
        "sales_targets": DB_DIR / "sales_performance" / "sales_target_db.db",
        "clients": DB_DIR / "sales_performance" / "clients_db.db",
        "compliance": DB_DIR / "rules_compliance" / "compliance.db"
    }
    
    # ============ Model Settings (Defaults) ============
    DEFAULT_MODELS = {
        "intent": "gpt-4o-mini",      # Fast for intent analysis
        "planning": "gpt-4o",          # Accurate for planning
        "execution": "gpt-4o-mini",    # Fast for execution
        "response": "gpt-4o-mini",     # Fast for response generation
        "analysis": "gpt-4o"           # Accurate for analysis
    }
    
    DEFAULT_MODEL_PARAMS = {
        "intent": {"temperature": 0.3, "max_tokens": 500},
        "planning": {"temperature": 0.3, "max_tokens": 2000},
        "execution": {"temperature": 0.3, "max_tokens": 1000},
        "response": {"temperature": 0.7, "max_tokens": 1500},
        "analysis": {"temperature": 0.5, "max_tokens": 2000}
    }
    
    # ============ System Limits ============
    TIMEOUTS = {
        "agent": 30,           # Individual agent timeout (seconds)
        "subgraph": 15,        # Subgraph timeout
        "tool": 10,            # Tool execution timeout
        "llm": 20,             # LLM call timeout
        "database": 5,         # Database query timeout
        "total": 60            # Total orchestrator timeout
    }
    
    LIMITS = {
        "max_recursion": 25,
        "max_retries": 3,
        "max_parallel_agents": 3,
        "max_parallel_tools": 5,
        "max_message_length": 10000,
        "max_sql_results": 1000,
        "max_memory_items": 100
    }
    
    # ============ Execution Settings ============
    EXECUTION = {
        "enable_parallel": True,
        "enable_caching": True,
        "enable_checkpointing": True,
        "checkpoint_interval": 5,  # Steps between checkpoints
        "cache_ttl": 300,          # Cache TTL in seconds
        "stream_mode": "updates"    # updates, values, or debug
    }
    
    # ============ Logging Settings ============
    LOGGING = {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "file_rotation": "daily",
        "max_log_size": "100MB",
        "backup_count": 7
    }
    
    # ============ Feature Flags (System Level) ============
    FEATURES = {
        "enable_llm_planning": True,
        "enable_semantic_search": True,
        "enable_reranking": False,
        "enable_memory_store": True,
        "enable_tool_validation": True,
        "enable_error_recovery": True
    }
    
    # ============ Helper Methods ============
    
    @classmethod
    def get_database_path(cls, db_name: str) -> Path:
        """Get database path by name"""
        return cls.DATABASES.get(db_name, cls.DB_DIR / f"{db_name}.db")
    
    @classmethod
    def get_checkpoint_path(cls, agent_name: str, session_id: str) -> Path:
        """Get checkpoint database path for an agent session"""
        checkpoint_dir = cls.CHECKPOINT_DIR / agent_name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        return checkpoint_dir / f"{session_id}.db"
    
    @classmethod
    def get_model_config(cls, model_type: str) -> Dict[str, Any]:
        """Get model configuration by type"""
        return {
            "model": cls.DEFAULT_MODELS.get(model_type, "gpt-4o-mini"),
            **cls.DEFAULT_MODEL_PARAMS.get(model_type, {})
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        issues = []
        
        # Check database paths exist
        for name, path in cls.DATABASES.items():
            if not path.parent.exists():
                issues.append(f"Database directory missing: {path.parent}")
        
        # Check required directories
        for directory in [cls.CHECKPOINT_DIR, cls.LOG_DIR]:
            if not directory.exists():
                issues.append(f"Required directory missing: {directory}")
        
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        return True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            "databases": {k: str(v) for k, v in cls.DATABASES.items()},
            "models": cls.DEFAULT_MODELS,
            "timeouts": cls.TIMEOUTS,
            "limits": cls.LIMITS,
            "features": cls.FEATURES
        }
