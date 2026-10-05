"""The mounted route tree for the single backend deployable.

One deployable, **one router per surface** (``docs/adr/0187`` §5): the player
app's, the club website's and the public site's. Each is *emitted* as its own
document by ``app/api/contract.py`` — ``openapi.player.json``,
``openapi.club.json`` and ``openapi.public.json`` — and no document carries
another's paths.

**And the webhooks, which are no surface**: the payment provider calls them and
no client does, so they are in no document (``app/api/v1/webhooks.py``,
``docs/adr/0190``).
"""

from fastapi import APIRouter

from app.api.v1.club import club_api_router
from app.api.v1.player import player_api_router
from app.api.v1.public import public_api_router
from app.api.v1.webhooks import webhooks_api_router

api_router = APIRouter()
api_router.include_router(player_api_router)
api_router.include_router(club_api_router)
api_router.include_router(public_api_router)
api_router.include_router(webhooks_api_router)
