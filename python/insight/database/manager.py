"""
Database Connection Manager for INsight.

Handles connections to the remote PostgreSQL database (Supabase).
Includes URL-encoding fix for special characters in passwords,
and convenience methods for user/workspace/conversation CRUD.
"""

import os
import logging
from typing import Optional, Generator, Dict, Any, List
from urllib.parse import quote_plus, urlparse, urlunparse
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from insight.database.models import Base, User, Workspace, Conversation

logger = logging.getLogger(__name__)


def _fix_database_url(url: str) -> str:
    """
    Fix DATABASE_URL for SQLAlchemy compatibility.

    Problem: Supabase connection strings often contain special characters
    in passwords (like $, @, #) that break SQLAlchemy's URL parser.

    Solution: Parse the URL, URL-encode the password, and reconstruct.
    """
    try:
        parsed = urlparse(url)
        if parsed.password:
            # URL-encode the password to handle special chars like $
            encoded_password = quote_plus(parsed.password)
            # Reconstruct the netloc with encoded password
            if parsed.port:
                netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}:{parsed.port}"
            else:
                netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            # Reconstruct the full URL
            fixed = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return fixed
        return url
    except Exception:
        return url


class DatabaseManager:
    """Manages the connection and lifecycle of the relational database."""

    def __init__(self, database_url: Optional[str] = None):
        raw_url = database_url or os.getenv("DATABASE_URL")

        if not raw_url:
            # Silent fallback if no database is configured
            self.database_url = None
            self.engine = None
            self.SessionLocal = None
            self._connected = False
            return

        # Fix URL-encoding issues (e.g., $ in Supabase passwords)
        self.database_url = _fix_database_url(raw_url)

        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_timeout=10,
                connect_args={"connect_timeout": 5}
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            self._connected = True
            logger.debug("Database engine created successfully")
        except Exception as e:
            logger.warning(f"Database connection setup failed: {e}")
            self.engine = None
            self.SessionLocal = None
            self._connected = False

    @property
    def is_available(self) -> bool:
        """Check if database is configured and reachable."""
        if not self._connected or not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return True
        except Exception:
            return False

    def init_db(self):
        """Create all tables in the database if they don't exist."""
        if not self.engine:
            return

        try:
            Base.metadata.create_all(bind=self.engine)
            logger.debug("Database tables initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize database tables: {e}")

    def get_session(self) -> Generator[Session, None, None]:
        """Provides a database session for operations."""
        if not self.SessionLocal:
            yield None
            return

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ─── User CRUD ──────────────────────────────────────────────

    def get_user_by_machine_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Find a user by their machine fingerprint."""
        if not self.SessionLocal:
            return None

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if user:
                return {
                    "db_id": user.id,
                    "username": user.username,
                    "machine_id": user.machine_id,
                    "api_keys": user.api_keys or {},
                    "created_at": str(user.created_at),
                    "last_active": str(user.last_active) if user.last_active else None,
                }
            return None
        except Exception as e:
            logger.debug(f"Failed to fetch user: {e}")
            return None
        finally:
            session.close()

    def create_user(self, username: str, machine_id: str) -> Optional[int]:
        """Create a new user record. Returns the database ID."""
        if not self.SessionLocal:
            return None

        session = self.SessionLocal()
        try:
            user = User(
                username=username,
                machine_id=machine_id,
                last_active=datetime.now(timezone.utc),
            )
            session.add(user)
            session.commit()
            logger.info(f"Created user in Supabase: {username} ({machine_id})")
            return user.id
        except Exception as e:
            session.rollback()
            logger.debug(f"Failed to create user: {e}")
            return None
        finally:
            session.close()

    def update_user_last_active(self, machine_id: str):
        """Update a user's last_active timestamp."""
        if not self.SessionLocal:
            return

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if user:
                user.last_active = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def save_user_api_key(self, machine_id: str, provider: str, api_key: str):
        """Save an API key for a user, identified by machine_id."""
        if not self.SessionLocal:
            return

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if user:
                keys = user.api_keys or {}
                keys[provider.lower()] = api_key
                user.api_keys = keys
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_user_api_key(self, machine_id: str, provider: str) -> Optional[str]:
        """Get a specific API key for a user."""
        if not self.SessionLocal:
            return None

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if user and user.api_keys:
                return user.api_keys.get(provider.lower())
            return None
        except Exception:
            return None
        finally:
            session.close()

    # ─── Workspace CRUD ─────────────────────────────────────────

    def register_workspace(
        self,
        owner_machine_id: str,
        name: str,
        path_hash: str,
        collection_name: str,
        metadata: Optional[Dict] = None,
    ) -> Optional[int]:
        """Register a workspace (indexed project) for a user."""
        if not self.SessionLocal:
            return None

        session = self.SessionLocal()
        try:
            # Find the user
            user = session.query(User).filter_by(machine_id=owner_machine_id).first()
            if not user:
                logger.debug(f"Cannot register workspace: user {owner_machine_id} not found")
                return None

            # Check if workspace already exists for this user
            existing = (
                session.query(Workspace)
                .filter_by(owner_id=user.id, path_hash=path_hash)
                .first()
            )

            if existing:
                # Update metadata
                existing.metadata_json = metadata or existing.metadata_json
                existing.collection_name = collection_name
                existing.updated_at = datetime.now(timezone.utc)
                session.commit()
                return existing.id

            # Create new workspace
            ws = Workspace(
                name=name,
                path_hash=path_hash,
                collection_name=collection_name,
                owner_id=user.id,
                metadata_json=metadata or {},
            )
            session.add(ws)
            session.commit()
            logger.info(f"Registered workspace: {name} for user {owner_machine_id}")
            return ws.id
        except Exception as e:
            session.rollback()
            logger.debug(f"Failed to register workspace: {e}")
            return None
        finally:
            session.close()

    def list_user_workspaces(self, machine_id: str) -> List[Dict[str, Any]]:
        """List all workspaces for a user."""
        if not self.SessionLocal:
            return []

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if not user:
                return []

            workspaces = session.query(Workspace).filter_by(owner_id=user.id).all()
            return [
                {
                    "id": ws.id,
                    "name": ws.name,
                    "path_hash": ws.path_hash,
                    "collection_name": ws.collection_name,
                    "metadata": ws.metadata_json,
                    "created_at": str(ws.created_at),
                }
                for ws in workspaces
            ]
        except Exception:
            return []
        finally:
            session.close()

    # ─── Conversation CRUD ──────────────────────────────────────

    def save_conversation(
        self,
        machine_id: str,
        session_id: str,
        question: str,
        answer: str,
        sources: Optional[List[str]] = None,
    ):
        """Persist a conversation exchange to the database."""
        if not self.SessionLocal:
            return

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if not user:
                return

            conv = Conversation(
                user_id=user.id,
                session_id=session_id,
                content={
                    "question": question,
                    "answer": answer,
                    "sources": sources or [],
                },
            )
            session.add(conv)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.debug(f"Failed to save conversation: {e}")
        finally:
            session.close()

    def load_conversation_history(
        self, machine_id: str, session_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Load conversation history for a session."""
        if not self.SessionLocal:
            return []

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(machine_id=machine_id).first()
            if not user:
                return []

            convs = (
                session.query(Conversation)
                .filter_by(user_id=user.id, session_id=session_id)
                .order_by(Conversation.created_at.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "question": c.content.get("question", ""),
                    "answer": c.content.get("answer", ""),
                    "sources": c.content.get("sources", []),
                    "created_at": str(c.created_at),
                }
                for c in convs
            ]
        except Exception:
            return []
        finally:
            session.close()


# Singleton instance for the project
db_manager = DatabaseManager()
