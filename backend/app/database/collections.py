"""MongoDB collection names for e-SewaSathi."""

USERS: str = "users"
APPLICATIONS: str = "applications"
DOCUMENTS: str = "documents"
AUDIT_LOGS: str = "audit_logs"

# Phase 2
CONSENTS: str = "consents"
WORKFLOWS: str = "workflows"
CHECKPOINTS: str = "workflow_checkpoints"
ESCALATIONS: str = "escalations"
CHAT_MESSAGES: str = "chat_messages"
STATUS_EVENTS: str = "status_events"
NOTIFICATIONS: str = "notifications"

ALL_COLLECTIONS: tuple[str, ...] = (
    USERS,
    APPLICATIONS,
    DOCUMENTS,
    AUDIT_LOGS,
    CONSENTS,
    WORKFLOWS,
    CHECKPOINTS,
    ESCALATIONS,
    CHAT_MESSAGES,
    STATUS_EVENTS,
    NOTIFICATIONS,
)
