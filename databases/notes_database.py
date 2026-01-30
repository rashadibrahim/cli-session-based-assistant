from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
load_dotenv()
import os


Base = declarative_base()
NOTES_DATABASE_URL = os.getenv("NOTES_DATABASE_URL", "sqlite:///./notes.db")

engine = create_engine(NOTES_DATABASE_URL, echo=False)
db = SQLDatabase.from_uri(NOTES_DATABASE_URL)
# Many-to-many association table (junction table)
note_tag = Table(
    "note_tag",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False, index=True)

    notes = relationship("Note", secondary=note_tag, back_populates="tags")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=True)

    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    is_archived = Column(
        Boolean,
        nullable=False,
        server_default=func.false()   # or default=False
    )

    tags = relationship("Tag", secondary=note_tag, back_populates="notes")

def init_notes_db():
    Base.metadata.create_all(engine)


    