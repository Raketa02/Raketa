from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.config import Settings
from app.infrastructure.database.engine import dispose_engine, init_engine


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        init_engine(settings)
        try:
            yield
        finally:
            await dispose_engine()

    return lifespan
