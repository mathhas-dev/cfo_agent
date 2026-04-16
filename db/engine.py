from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def build_engine(connection_string: str) -> Engine:
    """Factory for SQLAlchemy Engine. Callers own the lifecycle.

    Fails loudly if connection_string is empty — this is a boundary validation
    (clean-code.md: fail loudly at boundaries).
    """
    if not connection_string:
        raise ValueError(
            "DB_CONNECTION_STRING is required. "
            "Set it in your .env file (see .env.example)."
        )
    return create_engine(
        connection_string,
        pool_pre_ping=True,  # verify connections before use to catch stale pool entries
        pool_size=5,
        max_overflow=10,
    )
