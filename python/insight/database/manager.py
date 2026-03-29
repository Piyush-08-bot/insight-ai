"""
Database Connection Manager for INsight.
Handles connections to the remote PostgreSQL database (Supabase).
"""

import os
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from insight.database.models import Base


class DatabaseManager:
    """Manages the connection and lifecycle of the relational database."""

    def __init__(self, database_url: Optional[str] = None):
        # Default to environment variable if not provided
        self.database_url = database_url or os.getenv("DATABASE_URL")
        
        if not self.database_url:
            # Silent fallback if no database is configured
            self.engine = None
            self.SessionLocal = None
            return

        # Transaction pooler connection usually requires specific parameters for stability
        # We increase the pool_pre_ping to ensure connection health
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """Create all tables in the database if they don't exist."""
        if self.engine:
            Base.metadata.create_all(bind=self.engine)

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


# Singleton instance for the project
db_manager = DatabaseManager()
