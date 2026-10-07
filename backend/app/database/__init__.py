"""Database package for e-SewaSathi."""

from app.database.collections import APPLICATIONS, AUDIT_LOGS, DOCUMENTS, USERS
from app.database.mongodb import close_db, connect_db, get_client, get_database

__all__ = [
    "APPLICATIONS",
    "AUDIT_LOGS",
    "DOCUMENTS",
    "USERS",
    "close_db",
    "connect_db",
    "get_client",
    "get_database",
]
