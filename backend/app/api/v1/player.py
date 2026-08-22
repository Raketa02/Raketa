"""The player API surface.

Every endpoint a player client (``frontend_player/``) may depend on. The club
console generates its wire types from a *separate* document (see ``club.py``), so
neither client can take a dependency on the other's contract
(``docs/adr/0016-modular-monolith-two-api-surfaces.md``).
"""

from fastapi import APIRouter

from app.api.v1.sports import router as sports_router
from app.modules.auth.presentation.routes import router as auth_router
from app.modules.now.presentation.routes import router as now_router
from app.modules.rating.presentation.routes import ratings_router
from app.modules.rating.presentation.routes import router as assessments_router
from app.modules.users.presentation.routes import router as users_router

player_api_router = APIRouter(prefix="/api/v1")
player_api_router.include_router(users_router)
player_api_router.include_router(auth_router)
player_api_router.include_router(sports_router)
player_api_router.include_router(assessments_router)
player_api_router.include_router(ratings_router)
player_api_router.include_router(now_router)
