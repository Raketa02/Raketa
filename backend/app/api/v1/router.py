"""The mounted route tree for the single backend deployable.

One deployable, one API surface — the player client. The contract is *emitted*
as ``openapi.player.json`` by ``app/api/contract.py``.
"""

from fastapi import APIRouter

from app.api.v1.player import player_api_router

api_router = APIRouter()
api_router.include_router(player_api_router)
