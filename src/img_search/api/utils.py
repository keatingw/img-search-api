"""Utilities for API routes."""

from collections.abc import AsyncGenerator

import aiosqlite
from img_search.settings import api_settings


async def get_db_conn() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependency function to give a sqlite connection."""
    async with aiosqlite.connect(api_settings.img_sqlite_path) as conn:
        yield conn
