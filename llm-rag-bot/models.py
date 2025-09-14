from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from sqlalchemy.engine import Engine
import os

engine: Engine = create_engine("sqlite:///db.sqlite", echo=True)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str
    hashed_password: str

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    content: str
    is_user: bool  # True if from user, False if from bot

SQLModel.metadata.create_all(engine)