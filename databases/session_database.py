from requests import session
from sqlalchemy.orm import Session as DBSession
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, noload
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from agents.summarization_agent import call_summarization_agent
import os

SESSION_DATABASE_URL = os.getenv("SESSION_DATABASE_URL", "sqlite:///./agent_sessions.db")

engine = create_engine(
    SESSION_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_session_db():
    Base.metadata.create_all(bind=engine)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)  # "human" or "ai"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="messages")



class SessionManager:
    def __init__(self, db: DBSession):
        self.db = db

    def create_session(self, session_name: Optional[str] = None) -> Session:
        session = Session(id=str(uuid.uuid4()), session_name=session_name)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.db.query(Session).filter(Session.id == session_id).first()

    def save_message(self, session_id: str, role: str, content: str) -> Message:
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _map_messages(self, messages: List[Message]) -> List[BaseMessage]:
        mapped = []
        for msg in messages:
            if msg.role == "human":
                mapped.append(HumanMessage(content=msg.content))
            elif msg.role == "ai":
                mapped.append(AIMessage(content=msg.content))
            elif msg.role == "summary":
                mapped.append(AIMessage(content=f"[Summary of earlier conversation]: {msg.content}"))
        return mapped

    def get_chat_history(self, session_id: str) -> List[BaseMessage]:
        session = self.get_session(session_id)
        if not session:
            return []
        
        chat_history = []
        # only get the last 10 messages
        MSG_THRESHOLD = 10
        msg_count = len(session.messages)
        if msg_count > MSG_THRESHOLD:
            latest_messages = session.messages[-MSG_THRESHOLD:]
            msg_roles = [m.role for m in latest_messages]
            has_summary = (False if "summary" not in msg_roles else True)
            if has_summary:
                summary_index = msg_roles.index("summary")
                new_messages = latest_messages[summary_index:]
                chat_history = self._map_messages(new_messages)
                
            else:
                last_sum_index = None
                for i, val in enumerate(session.messages):
                    if val.role == "summary":
                        last_sum_index = i
                if last_sum_index:
                    latest_messages = session.messages[last_sum_index:]
                summary = call_summarization_agent(latest_messages)
                chat_history.append(AIMessage(content=f"[Summary of earlier conversation]: {summary}"))
                self.save_message(session_id, "summary", summary)

        elif msg_count == MSG_THRESHOLD:
            try:
                summary = call_summarization_agent(session.messages)
                chat_history.append(AIMessage(content=f"[Summary of earlier conversation]: {summary}"))
                self.save_message(session_id, "summary", summary)
            except Exception as e:
                chat_history = self._map_messages(session.messages)
        else:
            chat_history = self._map_messages(session.messages)
            
        return chat_history
    
    def list_sessions(self) -> List[Session]:
        # return sessions without chat history
        return self.db.query(Session).options(noload(Session.messages)).all()

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
