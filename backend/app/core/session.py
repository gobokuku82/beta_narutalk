"""
Simple session management
"""
from typing import Dict, Optional
import uuid
from datetime import datetime

# In-memory session storage
sessions: Dict[str, Dict] = {}

def create_session() -> str:
    """Create a new session and return session ID"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": datetime.now(),
        "messages": []
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID"""
    return sessions.get(session_id)

def update_session(session_id: str, data: Dict) -> bool:
    """Update session data"""
    if session_id in sessions:
        sessions[session_id].update(data)
        return True
    return False