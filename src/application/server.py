import asyncio
import nest_asyncio
from fastapi import FastAPI

nest_asyncio.apply()

async def create_app() -> FastAPI:
    app = FastAPI(
        title="Dummy App",
        description="This is a dummy FastAPI app for container startup testing",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    @app.get("/")
    async def read_root():
        return {"message": "Dummy server is running!"}

    return app

# Uvicorn expects this to be a global variable
app = asyncio.run(create_app())