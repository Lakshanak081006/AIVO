"""Database package.

Import concrete session objects from ``app.database.session`` only when a runtime
connection is needed. Keeping this package lightweight allows Alembic offline
SQL generation without loading a PostgreSQL driver.
"""

from app.database.base import Base

__all__ = ["Base"]
