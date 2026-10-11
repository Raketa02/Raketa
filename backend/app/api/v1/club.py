"""The club API surface.

Every endpoint the club website (``frontend_club/``) may depend on, and nothing
any other client reads (``docs/adr/0187`` §5). ``app/api/contract.py`` emits it
as ``openapi.club.json``, which the website generates its wire types from.

**Its own prefix, ``/api/v1/club``**, so that no path is ever in two documents
and a request's path says which surface it was made to. Its tokens carry the
club audience and its routes refuse the player app's (``docs/adr/0185`` §6).
"""

from fastapi import APIRouter

from app.modules.administrators.presentation.club_routes import (
    router as administrators_router,
)
from app.modules.clubs.presentation.auth_routes import router as club_auth_router
from app.modules.clubs.presentation.courts_routes import router as courts_router
from app.modules.clubs.presentation.routes import router as clubs_router
from app.modules.groups.presentation.club_routes import router as groups_router
from app.modules.payments.presentation.club_routes import payouts_router
from app.modules.payments.presentation.club_routes import router as payments_router
from app.modules.proposals.presentation.club_routes import money_router
from app.modules.proposals.presentation.club_routes import router as requests_router

club_api_router = APIRouter(prefix="/api/v1/club")
club_api_router.include_router(club_auth_router)
club_api_router.include_router(clubs_router)
club_api_router.include_router(courts_router)
club_api_router.include_router(administrators_router)
club_api_router.include_router(groups_router)
club_api_router.include_router(payments_router)
club_api_router.include_router(payouts_router)
club_api_router.include_router(requests_router)
club_api_router.include_router(money_router)
