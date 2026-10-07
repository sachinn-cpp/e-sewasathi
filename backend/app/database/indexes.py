"""Index creation for e-SewaSathi collections."""

from __future__ import annotations

import logging

from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import APPLICATIONS, AUDIT_LOGS, DOCUMENTS, USERS

logger = logging.getLogger(__name__)


async def ensure_indexes(db: AsyncDatabase) -> None:
    """Create the indexes required by Phase 1 queries."""
    await db[USERS].create_index("email", unique=True, name="uniq_users_email")
    await db[APPLICATIONS].create_index("user_id", name="apps_user_id")
    await db[APPLICATIONS].create_index("status", name="apps_status")
    await db[DOCUMENTS].create_index("application_id", name="docs_application_id")
    await db[AUDIT_LOGS].create_index(
        [("application_id", 1), ("created_at", -1)],
        name="audit_app_created_at",
    )
    logger.info("MongoDB indexes ensured for database '%s'", db.name)
