"""
Chat API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from models.chat import ChatRequest, ChatResponse
from ai.agent import shopping_agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for the shopping agent
    
    Accepts user message and returns AI response with optional product data
    """
    try:
        response = await shopping_agent.process_message(request)
        return response
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session
    """
    if session_id in shopping_agent.sessions:
        session = shopping_agent.sessions[session_id]
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in session.messages
            ],
            "last_mentioned_phones": session.last_mentioned_phones
        }
    
    raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a session
    """
    if session_id in shopping_agent.sessions:
        del shopping_agent.sessions[session_id]
        return {"message": "Session cleared"}
    
    raise HTTPException(status_code=404, detail="Session not found")
