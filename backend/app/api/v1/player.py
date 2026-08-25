"""The player API surface.

Every endpoint the player client (``frontend_player/``) may depend on. It is the
only surface this backend serves, and ``app/api/contract.py`` emits it as
``openapi.player.json`` — the one document the client generates its wire types
from (``docs/adr/0006-backend-owns-api-contract.md``).
"""

from fastapi import APIRouter

from app.api.v1.sports import router as sports_router
from app.modules.auth.presentation.routes import router as auth_router
from app.modules.player_profile.presentation.photo_routes import (
    router as photos_router,
)
from app.modules.player_profile.presentation.routes import (
    router as player_profile_router,
)
from app.modules.rating.presentation.routes import ratings_router
from app.modules.rating.presentation.routes import router as assessments_router
from app.modules.users.presentation.routes import router as users_router

player_api_router = APIRouter(prefix="/api/v1")
player_api_router.include_router(users_router)
player_api_router.include_router(auth_router)
player_api_router.include_router(sports_router)
player_api_router.include_router(assessments_router)
player_api_router.include_router(ratings_router)
player_api_router.include_router(player_profile_router)
player_api_router.include_router(photos_router)
