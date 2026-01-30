from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession
from databases.session_database import SessionManager, get_session_db, init_session_db
from schemas import (
    CreateSessionRequest,
    SessionResponse,
    SessionSchema,
    ChatRequest,
    ChatResponse,
)
from databases.notes_database import init_notes_db

from agents.main_agent import call_main_agent

app = FastAPI(title="Agent API", version="1.0.0")

# Allow browser apps to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def startup_event():
    init_session_db()
    init_notes_db()


@app.post("/sessions/create", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest | None = None,
    db: DBSession = Depends(get_session_db)
):
    """Create a new conversation session"""
    manager = SessionManager(db)
    session = manager.create_session(session_name=request.session_name if request else None)
    return SessionResponse(
        session_id=session.id,
        session_name=session.session_name,
        message="Session created successfully"
    )


@app.get("/sessions/{session_id}", response_model=SessionSchema)
async def get_session(session_id: str, db: DBSession = Depends(get_session_db)):
    """Get session details including chat history"""
    manager = SessionManager(db)
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions", response_model=list[SessionSchema])
async def list_sessions(db: DBSession = Depends(get_session_db)):
    """List all sessions"""
    manager = SessionManager(db)
    return manager.list_sessions()


@app.delete("/sessions/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str, db: DBSession = Depends(get_session_db)):
    """Delete a session"""
    manager = SessionManager(db)
    success = manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session_id,
        message="Session deleted successfully"
    )


@app.post("/query/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: DBSession = Depends(get_session_db)
):
    """Send a message to the agent and get a response"""
    manager = SessionManager(db)
    session = manager.get_session(request.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    chat_history = ([] if not request.enable_history else manager.get_chat_history(request.session_id))
    response_text = call_main_agent(request.query, chat_history[-10:])
    manager.save_message(request.session_id, "human", request.query)
    manager.save_message(request.session_id, "ai", response_text)
    
    return ChatResponse(response=response_text)
       

        


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Caja Agent API",
        "version": "1.0.0",
        "endpoints": {
            "create_session": "POST /sessions/create",
            "get_session": "GET /sessions/{session_id}",
            "list_sessions": "GET /sessions",
            "delete_session": "DELETE /sessions/{session_id}",
            "chat": "POST /query/chat"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

