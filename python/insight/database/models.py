"""
SQLAlchemy Models for INsight Hosted Architecture.

Tracks users (via machine fingerprint), their indexed workspaces,
and persistent conversation history.
"""

import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Stores user profiles identified by machine fingerprint."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    # Machine fingerprint — the primary way we identify users
    # Generated from (hostname + OS username + home dir) hash
    machine_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # JSON field to store multiple API keys securely
    # Example: {"openai": "sk-...", "groq": "gsk-..."}
    api_keys: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    last_active: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relationships
    workspaces: Mapped[List["Workspace"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, machine_id={self.machine_id!r})"


class Workspace(Base):
    """Stores metadata about indexed codebases, scoped per user."""
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Hash of the absolute project path — unique per user
    path_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # The ChromaDB collection name used for this workspace
    collection_name: Mapped[str] = mapped_column(String(100), nullable=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Metadata about the codebase (e.g., tech stack, file counts, project path)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="workspaces")

    def __repr__(self) -> str:
        return f"Workspace(id={self.id!r}, name={self.name!r}, collection={self.collection_name!r})"


class Conversation(Base):
    """Stores persistent chat history between users and their code."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    workspace_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workspaces.id"), nullable=True)

    session_id: Mapped[str] = mapped_column(String(100), index=True)

    # The actual message pair
    # Format: {"question": "...", "answer": "...", "sources": [...]}
    content: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")

    def __repr__(self) -> str:
        return f"Conversation(id={self.id!r}, session_id={self.session_id!r})"
