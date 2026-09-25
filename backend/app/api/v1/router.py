"""The mounted route tree for the single backend deployable.

One deployable, **one router per surface** (``docs/adr/0187`` §5): the player
app's and the club website's. Each is *emitted* as its own document by
``app/api/contract.py`` — ``openapi.player.json`` and ``openapi.club.json`` —
and neither document carries the other's paths.
"""

from fastapi import APIRouter

from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router

api_router = APIRouter()
api_router.include_router(player_api_router)
api_router.include_router(club_api_router)
