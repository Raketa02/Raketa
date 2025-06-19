import asyncio
import ssl
import os
import nest_asyncio
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String

nest_asyncio.apply()

#  ------------------- DB setup
DATABASE_URL = "postgresql+asyncpg://basebackend_user@db:5432/postgres"


# SQLAlchemy async setup
Base = declarative_base()
AsyncSessionLocal = None
engine = None

# DB model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


def get_ssl_context():
    ssl_context = ssl.create_default_context(cafile="/certs/rootCA.crt")
    ssl_context.load_cert_chain(
        certfile="/certs/client.crt", 
        keyfile="/certs/client.key"
    )

    return ssl_context

def init_db_engine():
    connect_args = {}

    if "sslmode" in DATABASE_URL:
        connect_args = {"ssl": get_ssl_context()}

    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args=connect_args
    )
    AsyncSessionLocal = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )


# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


#  ------------------- Fast Api Demo
async def create_app() -> FastAPI:
    init_db_engine()

    app = FastAPI(
        title="Dummy App",
        description="This is a dummy FastAPI app for container startup testing",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Ensure tables exist
    @app.on_event("startup")
    async def on_startup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @app.get("/")
    async def read_root():
        return {"message": "Dummy ver is!"}
    
    @app.post("/test-db")
    async def test_db(name: str, db: AsyncSession = Depends(get_db)):
        user = User(name=name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {
            "message": f"User '{user.name}' inserted successfully", 
            "user_id": user.id
        }

    return app

# Uvicorn expects this to be a global variable
app = asyncio.run(create_app())