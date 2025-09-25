"""
Configuration for the agent system
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Config:
    """System configuration"""

    # === API Keys ===
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # === Model Settings ===
    LLM_MODELS = {
        "intent": "gpt-4o-mini",      # Fast for intent analysis
        "planning": "gpt-4o",          # Accurate for planning and reasoning
        "execution": "gpt-4o-mini",    # Fast for execution
        "response": "gpt-4o-mini",     # Fast for response generation
    }

    # === Database Paths ===
    BASE_DIR = Path(__file__).parent.parent.parent.parent  # Project root
    DB_DIR = BASE_DIR / "database" / "storage"

    DATABASES = {
        "hr_info": DB_DIR / "hr_information" / "hr_data.db",
        "hr_rules": DB_DIR / "hr_rules" / "chromadb",
        "sales": DB_DIR / "sales_performance",
        "compliance": DB_DIR / "rules_compliance"
    }

    # === Checkpoint Settings ===
    CHECKPOINT_DIR = BASE_DIR / "checkpoints"
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # === Model Paths (Local) ===
    MODEL_DIR = BASE_DIR / "models"
    EMBEDDING_MODEL_PATH = MODEL_DIR / "kure_v1"  # For future use
    RERANKER_MODEL_PATH = MODEL_DIR / "bge-reranker-v2-m3-ko"  # For future use

    # === Timeout Settings ===
    TIMEOUTS = {
        "agent": 10,           # Individual agent timeout
        "orchestrator": 30,    # Total orchestrator timeout
        "intent": 5,          # Intent analysis timeout
        "planning": 10,       # Planning timeout
        "execution": 15,      # Execution timeout
        "response": 5         # Response generation timeout
    }

    # === Execution Settings ===
    MAX_RECURSION_LIMIT = 25
    MAX_RETRY_COUNT = 3
    ENABLE_PARALLEL_EXECUTION = True
    MAX_PARALLEL_AGENTS = 3

    # === Logging Settings ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def get_llm_config(cls, model_type: str = "intent") -> Dict[str, Any]:
        """
        Get LLM configuration for a specific model type

        Args:
            model_type: Type of model (intent, planning, execution, response)

        Returns:
            LLM configuration dictionary
        """
        model_name = cls.LLM_MODELS.get(model_type, "gpt-4o-mini")

        return {
            "model": model_name,
            "temperature": 0.7 if model_type == "response" else 0.3,
            "max_tokens": 2000 if model_type == "planning" else 1000,
            "api_key": cls.OPENAI_API_KEY
        }

    @classmethod
    def get_database_path(cls, db_name: str) -> Path:
        """
        Get database path

        Args:
            db_name: Name of the database

        Returns:
            Path to the database
        """
        return cls.DATABASES.get(db_name, cls.DB_DIR / db_name)

    @classmethod
    def get_checkpoint_path(cls, agent_name: str) -> Path:
        """
        Get checkpoint path for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Path to the checkpoint database
        """
        checkpoint_path = cls.CHECKPOINT_DIR / agent_name
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        return checkpoint_path / f"{agent_name}.db"

    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid
        """
        # Check API key
        if not cls.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set")
            return False

        # Check database paths
        for name, path in cls.DATABASES.items():
            if not path.parent.exists():
                print(f"Warning: Database directory not found for {name}: {path.parent}")

        return True