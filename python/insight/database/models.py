"""
SQLAlchemy Models for INsight Hosted Architecture.
"""

import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Stores user profiles and global API configurations."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    # JSON field to store multiple API keys securely
    # Example: {"openai": "sk-...", "groq": "gsk-..."}
    api_keys: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relationships
    workspaces: Mapped[List["Workspace"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"


class Workspace(Base):
    """Stores metadata about indexed codebases."""
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    path_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Metadata about the codebase (e.g., tech stack, file counts)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    owner: Mapped["User"] = relationship(back_populates="workspaces")

    def __repr__(self) -> str:
        return f"Workspace(id={self.id!r}, name={self.name!r})"


class Conversation(Base):
    """Stores persistent chat history between users and their code."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspaces.id"))
    
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # The actual message pair
    # Example: {"question": "...", "answer": "...", "sources": [...]}
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")

    def __repr__(self) -> str:
        return f"Conversation(id={self.id!r}, session_id={self.session_id!r})"
