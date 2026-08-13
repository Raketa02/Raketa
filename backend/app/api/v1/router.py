"""The mounted route tree for the single backend deployable.

One deployable serves both API surfaces (``docs/adr/0016``); the contract is then
*emitted* as two documents, one per client — see ``app/api/contract.py``.
"""

from fastapi import APIRouter

from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router

api_router = APIRouter()
api_router.include_router(player_api_router)
api_router.include_router(club_api_router)
