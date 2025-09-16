"""
SQLAlchemy database models
"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a new UUID"""
    return str(uuid.uuid4())


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    company_id = Column(String, nullable=True)
    status = Column(String, default="initializing")
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    agent_states = relationship("AgentState", back_populates="conversation", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class AgentState(Base):
    """Agent state model"""
    __tablename__ = "agent_states"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    agent_name = Column(String, nullable=False, index=True)
    task_id = Column(String, nullable=True)
    state_data = Column(JSON, nullable=False)
    execution_status = Column(String, default="initializing")
    execution_time = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="agent_states")


class AnalysisResult(Base):
    """Analysis result model"""
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    agent_name = Column(String, nullable=False, index=True)
    result_type = Column(String, nullable=False, index=True)
    query = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="analysis_results")


class Document(Base):
    """Document model"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    document_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    metadata = Column(JSON, default={})
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComplianceCheck(Base):
    """Compliance check model"""
    __tablename__ = "compliance_checks"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    target_id = Column(String, nullable=False)  # Document or data ID being checked
    target_type = Column(String, nullable=False)  # document, action, data
    applied_rules = Column(JSON, default=[])
    validation_results = Column(JSON, default=[])
    violations = Column(JSON, default=[])
    risk_level = Column(String, nullable=True)  # low, medium, high, critical
    recommendations = Column(JSON, default=[])
    passed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class VectorEmbedding(Base):
    """Vector embedding model for semantic search"""
    __tablename__ = "vector_embeddings"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, nullable=False, index=True)  # Reference to original document/data
    source_type = Column(String, nullable=False)  # document, message, knowledge
    content_chunk = Column(Text, nullable=False)
    embedding_model = Column(String, nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Note: Actual embedding vector would be stored in a vector database like ChromaDB or Pinecone
    # This table stores metadata and references


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)