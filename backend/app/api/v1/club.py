"""The club API surface.

The club console (``frontend_club/``) generates its wire types from this document.
It carries no endpoints yet — the two-document split is set up now, while it costs
a one-line edit, rather than after real club wire types exist and moving them would
be a migration. Club endpoints mount here.
"""

from fastapi import APIRouter

club_api_router = APIRouter(prefix="/api/v1")
