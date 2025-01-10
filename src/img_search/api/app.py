"""FastAPI app definition."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI

from img_search.api.routers.images import router as images_router
from img_search.settings import api_settings
from img_search.types import DDL


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan function to set up DDL on app launch."""
    async with aiosqlite.connect(api_settings.img_sqlite_path) as conn:
        for ddl_stmt in DDL:
            await conn.execute(ddl_stmt)
        await conn.commit()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(images_router)
