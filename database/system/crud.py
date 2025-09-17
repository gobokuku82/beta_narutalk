"""
CRUD operations for database
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .models import (
    Conversation, Message, AgentState,
    AnalysisResult, Document, ComplianceCheck,
    VectorEmbedding, AuditLog
)
from .schemas import (
    ConversationCreate, MessageCreate,
    AgentStateCreate, AnalysisResultCreate
)


# Conversation CRUD
async def create_conversation(
    db: AsyncSession,
    conversation: ConversationCreate
) -> Conversation:
    """Create a new conversation"""
    db_conversation = Conversation(
        user_id=conversation.user_id,
        session_id=conversation.session_id,
        company_id=conversation.company_id,
        metadata=conversation.metadata or {}
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: str
) -> Optional[Conversation]:
    """Get conversation by ID"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def list_conversations(
    db: AsyncSession,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Conversation]:
    """List conversations with optional filtering"""
    query = select(Conversation)

    if user_id:
        query = query.where(Conversation.user_id == user_id)

    query = query.order_by(desc(Conversation.created_at))
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def update_conversation_status(
    db: AsyncSession,
    conversation_id: str,
    status: str
) -> Optional[Conversation]:
    """Update conversation status"""
    conversation = await get_conversation(db, conversation_id)
    if conversation:
        conversation.status = status
        conversation.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(conversation)
    return conversation


# Message CRUD
async def create_message(
    db: AsyncSession,
    message: MessageCreate
) -> Message:
    """Create a new message"""
    # Get the next sequence number
    result = await db.execute(
        select(func.coalesce(func.max(Message.sequence_number), 0))
        .where(Message.conversation_id == message.conversation_id)
    )
    next_sequence = result.scalar() + 1

    db_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        sequence_number=next_sequence,
        metadata=message.metadata or {}
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_message(
    db: AsyncSession,
    message_id: str
) -> Optional[Message]:
    """Get message by ID"""
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    return result.scalar_one_or_none()


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Message]:
    """Get all messages for a conversation"""
    query = select(Message).where(Message.conversation_id == conversation_id)
    query = query.order_by(Message.sequence_number)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# Agent State CRUD
async def create_or_update_agent_state(
    db: AsyncSession,
    state: AgentStateCreate
) -> AgentState:
    """Create or update agent state"""
    # Check if state exists
    result = await db.execute(
        select(AgentState).where(
            and_(
                AgentState.conversation_id == state.conversation_id,
                AgentState.agent_name == state.agent_name,
                AgentState.task_id == state.task_id
            )
        )
    )
    existing_state = result.scalar_one_or_none()

    if existing_state:
        # Update existing state
        existing_state.state_data = state.state_data
        existing_state.execution_status = state.execution_status
        existing_state.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_state)
        return existing_state
    else:
        # Create new state
        db_state = AgentState(
            conversation_id=state.conversation_id,
            agent_name=state.agent_name,
            task_id=state.task_id,
            state_data=state.state_data,
            execution_status=state.execution_status
        )
        db.add(db_state)
        await db.commit()
        await db.refresh(db_state)
        return db_state


async def get_agent_state(
    db: AsyncSession,
    state_id: str
) -> Optional[AgentState]:
    """Get agent state by ID"""
    result = await db.execute(
        select(AgentState).where(AgentState.id == state_id)
    )
    return result.scalar_one_or_none()


async def get_conversation_agent_states(
    db: AsyncSession,
    conversation_id: str,
    agent_name: Optional[str] = None
) -> List[AgentState]:
    """Get all agent states for a conversation"""
    query = select(AgentState).where(AgentState.conversation_id == conversation_id)

    if agent_name:
        query = query.where(AgentState.agent_name == agent_name)

    query = query.order_by(desc(AgentState.updated_at))

    result = await db.execute(query)
    return result.scalars().all()


# Analysis Result CRUD
async def create_analysis_result(
    db: AsyncSession,
    result: AnalysisResultCreate
) -> AnalysisResult:
    """Create analysis result"""
    db_result = AnalysisResult(
        conversation_id=result.conversation_id,
        agent_name=result.agent_name,
        result_type=result.result_type,
        query=result.query,
        result_data=result.result_data,
        metadata=result.metadata or {}
    )
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)
    return db_result


async def get_analysis_result(
    db: AsyncSession,
    result_id: str
) -> Optional[AnalysisResult]:
    """Get analysis result by ID"""
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == result_id)
    )
    return result.scalar_one_or_none()


async def get_conversation_analysis_results(
    db: AsyncSession,
    conversation_id: str,
    result_type: Optional[str] = None
) -> List[AnalysisResult]:
    """Get all analysis results for a conversation"""
    query = select(AnalysisResult).where(AnalysisResult.conversation_id == conversation_id)

    if result_type:
        query = query.where(AnalysisResult.result_type == result_type)

    query = query.order_by(desc(AnalysisResult.created_at))

    result = await db.execute(query)
    return result.scalars().all()


# Statistics
async def get_database_statistics(db: AsyncSession) -> Dict[str, Any]:
    """Get database statistics"""
    # Total conversations
    total_conversations = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_conversations.scalar()

    # Total messages
    total_messages = await db.execute(select(func.count(Message.id)))
    total_messages = total_messages.scalar()

    # Total agent states
    total_agent_states = await db.execute(select(func.count(AgentState.id)))
    total_agent_states = total_agent_states.scalar()

    # Total analysis results
    total_analysis_results = await db.execute(select(func.count(AnalysisResult.id)))
    total_analysis_results = total_analysis_results.scalar()

    # Active conversations (status != 'completed')
    active_conversations = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.status != 'completed')
    )
    active_conversations = active_conversations.scalar()

    # Average messages per conversation
    avg_messages = 0
    if total_conversations > 0:
        avg_messages = total_messages / total_conversations

    # Most active agents
    agent_activity = await db.execute(
        select(
            AgentState.agent_name,
            func.count(AgentState.id).label('count')
        )
        .group_by(AgentState.agent_name)
        .order_by(desc('count'))
        .limit(5)
    )
    most_active_agents = [
        {"agent": row[0], "count": row[1]}
        for row in agent_activity
    ]

    # Recent activity (last 10 conversations)
    recent_convs = await db.execute(
        select(Conversation)
        .order_by(desc(Conversation.created_at))
        .limit(10)
    )
    recent_activity = [
        {
            "id": conv.id,
            "user_id": conv.user_id,
            "status": conv.status,
            "created_at": conv.created_at.isoformat()
        }
        for conv in recent_convs.scalars()
    ]

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_agent_states": total_agent_states,
        "total_analysis_results": total_analysis_results,
        "active_conversations": active_conversations,
        "avg_messages_per_conversation": round(avg_messages, 2),
        "most_active_agents": most_active_agents,
        "recent_activity": recent_activity
    }