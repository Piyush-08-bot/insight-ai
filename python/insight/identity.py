"""
User Identity System for INsight.

Provides automatic, zero-config user identification using a machine fingerprint.
Each unique (machine + OS user) combination gets a stable, deterministic ID.

No login/registration required — ideal for CLI tools distributed via npm.
"""

import hashlib
import json
import os
import platform
import getpass
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─── Identity File ──────────────────────────────────────────────

INSIGHT_DIR = Path.home() / ".insight"
IDENTITY_FILE = INSIGHT_DIR / "identity.json"


def _generate_machine_fingerprint() -> str:
    """
    Generate a deterministic fingerprint from the current machine + OS user.

    Components:
    - platform.node() → machine hostname
    - getpass.getuser() → OS-level username
    - Path.home() → home directory path (disambiguates same-name users)

    This fingerprint is stable across sessions on the same machine/user.
    """
    raw = f"{platform.node()}::{getpass.getuser()}::{str(Path.home())}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_local_identity() -> Optional[Dict[str, Any]]:
    """Load identity from the local ~/.insight/identity.json file."""
    if IDENTITY_FILE.exists():
        try:
            with open(IDENTITY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def _save_local_identity(identity: Dict[str, Any]):
    """Persist identity to ~/.insight/identity.json."""
    INSIGHT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(INSIGHT_DIR), 0o700)
    except Exception:
        pass

    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=2, default=str)

    try:
        os.chmod(str(IDENTITY_FILE), 0o600)
    except Exception:
        pass


def get_or_create_user() -> Dict[str, Any]:
    """
    Get the current user's identity, creating it if necessary.

    Flow:
    1. Generate machine fingerprint.
    2. Check local identity file — if it matches, use it.
    3. Try to register/fetch in Supabase (if DATABASE_URL configured).
    4. Save locally for offline use.

    Returns a dict with: user_id, machine_id, username, created_at
    """
    machine_id = _generate_machine_fingerprint()
    os_username = getpass.getuser()

    # ─── Check local cache first ────────────────────────────────
    local = _load_local_identity()
    if local and local.get("machine_id") == machine_id:
        # Update last_active
        local["last_active"] = datetime.now(timezone.utc).isoformat()
        _save_local_identity(local)

        # Also update Supabase last_active (non-blocking)
        _sync_to_supabase(local)
        return local

    # ─── Create new identity ────────────────────────────────────
    identity = {
        "user_id": f"user_{machine_id}",
        "machine_id": machine_id,
        "username": os_username,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat(),
    }

    # Try to register in Supabase
    db_user = _register_in_supabase(identity)
    if db_user:
        identity["db_id"] = db_user.get("db_id")

    _save_local_identity(identity)
    logger.info(f"Created new user identity: {identity['user_id']}")
    return identity


def get_current_user_id() -> str:
    """
    Quick accessor — returns the current user's stable ID.
    Used everywhere for scoping ChromaDB collections and Supabase queries.
    """
    identity = get_or_create_user()
    return identity["user_id"]


def get_project_hash(project_path: str) -> str:
    """
    Generate a stable hash for a project path.
    Used to scope ChromaDB collections per user + project.
    """
    abs_path = str(Path(project_path).resolve())
    return hashlib.sha256(abs_path.encode()).hexdigest()[:12]


def get_scoped_collection_name(project_path: str, user_id: Optional[str] = None) -> str:
    """
    Generate a user-scoped ChromaDB collection name.

    Format: {user_id_short}_{project_hash}
    Example: user_a1b2c3d4_e5f6a7b8c9d0
    """
    if not user_id:
        user_id = get_current_user_id()

    project_hash = get_project_hash(project_path)

    # ChromaDB collection names must be 3-63 chars, start/end with alphanumeric
    # and can only contain alphanumerics, hyphens, underscores, periods
    short_user = user_id[:20]  # Truncate to keep under 63 chars
    return f"{short_user}_{project_hash}"


# ─── Supabase Sync (Non-Blocking) ──────────────────────────────

def _register_in_supabase(identity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Register the user in Supabase. Non-blocking — if DB is unavailable, returns None.
    """
    try:
        from insight.database.manager import db_manager
        from insight.database.models import User

        if not db_manager.SessionLocal:
            return None

        session = db_manager.SessionLocal()
        try:
            # Check if user already exists
            existing = session.query(User).filter_by(
                machine_id=identity["machine_id"]
            ).first()

            if existing:
                existing.last_active = datetime.now(timezone.utc)
                session.commit()
                return {"db_id": existing.id}

            # Create new user
            user = User(
                username=identity["username"],
                machine_id=identity["machine_id"],
                last_active=datetime.now(timezone.utc),
            )
            session.add(user)
            session.commit()
            logger.info(f"Registered user in Supabase: {identity['user_id']}")
            return {"db_id": user.id}
        except Exception as e:
            session.rollback()
            logger.debug(f"Supabase registration failed (non-critical): {e}")
            return None
        finally:
            session.close()
    except Exception as e:
        logger.debug(f"Supabase unavailable (non-critical): {e}")
        return None


def _sync_to_supabase(identity: Dict[str, Any]):
    """Update last_active in Supabase (best-effort, non-blocking)."""
    try:
        from insight.database.manager import db_manager
        from insight.database.models import User

        if not db_manager.SessionLocal:
            return

        session = db_manager.SessionLocal()
        try:
            user = session.query(User).filter_by(
                machine_id=identity["machine_id"]
            ).first()
            if user:
                user.last_active = datetime.now(timezone.utc)
                session.commit()
            else:
                # Re-register if missing from DB
                _register_in_supabase(identity)
        except Exception:
            session.rollback()
        finally:
            session.close()
    except Exception:
        pass


def _format_date(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable format like 'Apr 1, 2026'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "unknown"


def _format_relative_time(iso_str: str) -> str:
    """Convert ISO timestamp to relative time like '2 minutes ago'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        # Make both timezone-aware or both naive for comparison
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return _format_date(iso_str)
    except Exception:
        return "unknown"


def _get_cloud_status() -> str:
    """Check if Supabase cloud sync is connected."""
    try:
        from insight.database.manager import db_manager
        if db_manager.is_available:
            return "Connected ✓"
        return "Offline"
    except Exception:
        return "Not configured"


def _get_project_count() -> int:
    """Count how many projects this user has indexed."""
    try:
        from insight.database.manager import db_manager
        identity = _load_local_identity()
        if identity and db_manager.is_available:
            workspaces = db_manager.list_user_workspaces(identity["machine_id"])
            return len(workspaces)
        return 0
    except Exception:
        return 0


def show_identity() -> str:
    """Format the current user identity for display — user-friendly output."""
    identity = get_or_create_user()

    short_id = identity["user_id"][-8:]  # Last 8 chars of hash
    username = identity["username"]
    created = _format_date(identity.get("created_at", ""))
    last_active = _format_relative_time(identity.get("last_active", ""))
    cloud = _get_cloud_status()
    projects = _get_project_count()

    lines = [
        f"  👤 User:         {username}",
        f"  🔑 ID:           {short_id}",
        f"  📅 Member Since: {created}",
        f"  ⏱️  Last Active:  {last_active}",
        f"  ☁️  Cloud Sync:   {cloud}",
        f"  📦 Projects:     {projects} indexed",
    ]
    return "\n".join(lines)
