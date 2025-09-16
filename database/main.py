"""
Database API Server
FastAPI server for database operations and data management
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from .database import get_db, init_db
from .schemas import (
    ConversationCreate, ConversationResponse,
    MessageCreate, MessageResponse,
    AgentStateCreate, AgentStateResponse,
    AnalysisResultCreate, AnalysisResultResponse
)
from . import crud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Pharma Chatbot Database API",
    description="Database management API for LangGraph multi-agent chatbot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    logger.info("Database initialized successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pharma Chatbot Database API",
        "version": "1.0.0",
        "status": "running"
    }


# Conversation endpoints
@app.post("/conversations/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    try:
        return await crud.create_conversation(db, conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation by ID"""
    conversation = await crud.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.get("/conversations/", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List conversations with optional filtering"""
    return await crud.list_conversations(db, user_id, skip, limit)


# Message endpoints
@app.post("/messages/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new message"""
    try:
        return await crud.create_message(db, message)
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get message by ID"""
    message = await crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a conversation"""
    return await crud.get_conversation_messages(db, conversation_id, skip, limit)


# Agent State endpoints
@app.post("/agent-states/", response_model=AgentStateResponse)
async def create_agent_state(
    state: AgentStateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create or update agent state"""
    try:
        return await crud.create_or_update_agent_state(db, state)
    except Exception as e:
        logger.error(f"Error creating agent state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent-states/{state_id}", response_model=AgentStateResponse)
async def get_agent_state(
    state_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent state by ID"""
    state = await crud.get_agent_state(db, state_id)
    if not state:
        raise HTTPException(status_code=404, detail="Agent state not found")
    return state


@app.get("/conversations/{conversation_id}/agent-states", response_model=List[AgentStateResponse])
async def get_conversation_agent_states(
    conversation_id: str,
    agent_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all agent states for a conversation"""
    return await crud.get_conversation_agent_states(db, conversation_id, agent_name)


# Analysis Result endpoints
@app.post("/analysis-results/", response_model=AnalysisResultResponse)
async def create_analysis_result(
    result: AnalysisResultCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create analysis result"""
    try:
        return await crud.create_analysis_result(db, result)
    except Exception as e:
        logger.error(f"Error creating analysis result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis-results/{result_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis result by ID"""
    result = await crud.get_analysis_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result


@app.get("/conversations/{conversation_id}/analysis-results", response_model=List[AnalysisResultResponse])
async def get_conversation_analysis_results(
    conversation_id: str,
    result_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all analysis results for a conversation"""
    return await crud.get_conversation_analysis_results(db, conversation_id, result_type)


# Health check endpoint
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Statistics endpoint
@app.get("/stats")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get database statistics"""
    try:
        stats = await crud.get_database_statistics(db)
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )