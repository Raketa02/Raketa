"""Framework-level security primitives.

The HTTPBearer scheme is a FastAPI concept, not a domain port — concrete
hashing / token-issuing adapters live under each module's `infrastructure/`.
"""
from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False, description="Bearer access token")
