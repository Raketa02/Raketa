"""The player API surface.

Every endpoint the player client (``frontend_player/``) may depend on, and
``app/api/contract.py`` emits it as ``openapi.player.json`` — the one document
that client generates its wire types from
(``docs/adr/0006-backend-owns-api-contract.md``). The club website has a surface
of its own (``app/api/v1/club.py``), and no path is in both.
"""

from fastapi import APIRouter

from app.api.v1.sports import router as sports_router
from app.modules.administrators.presentation.routes import (
    administrator_router,
    invitations_router,
)
from app.modules.auth.presentation.routes import router as auth_router
from app.modules.blocks.presentation.routes import router as blocks_router
from app.modules.conversations.presentation.routes import (
    router as conversations_router,
)
from app.modules.discovery.presentation.routes import (
    new_in_raketa_router,
    on_screen_router,
    same_level_router,
    same_vibe_router,
)
from app.modules.friends.presentation.link_routes import (
    router as friend_link_router,
)
from app.modules.friends.presentation.routes import router as friends_router
from app.modules.games.presentation.routes import router as games_router
from app.modules.groups.presentation.administrator_routes import (
    handovers_router,
)
from app.modules.groups.presentation.administrator_routes import (
    router as administrator_groups_router,
)
from app.modules.groups.presentation.routes import (
    home_clubs_router,
    hottest_groups_router,
    join_search_router,
    router as groups_router,
)
from app.modules.notifications.presentation.routes import (
    router as notifications_router,
)
from app.modules.payments.presentation.routes import router as payments_router
from app.modules.payments.presentation.seat_charge_routes import (
    receipts_router,
    seat_charges_router,
)
from app.modules.player_profile.presentation.photo_routes import (
    router as photos_router,
)
from app.modules.player_profile.presentation.play_intent_routes import (
    router as play_intents_router,
)
from app.modules.player_profile.presentation.profile_routes import (
    router as profile_commit_router,
)
from app.modules.player_profile.presentation.profile_surface_routes import (
    router as profile_surface_router,
)
from app.modules.player_profile.presentation.routes import (
    router as player_profile_router,
)
from app.modules.player_record.presentation.routes import (
    router as player_record_router,
)
from app.modules.proposals.presentation.routes import (
    bookings_router,
    home_router,
    players_router as proposal_players_router,
    pools_router,
)
from app.modules.proposals.presentation.routes import (
    seat_charges_router as seat_charge_confirmation_router,
)
from app.modules.proposals.presentation.routes import router as proposals_router
from app.modules.rankings.presentation.routes import router as rankings_router
from app.modules.rating.presentation.routes import ratings_router
from app.modules.rating.presentation.routes import router as assessments_router
from app.modules.sportsmanship.presentation.routes import (
    router as sportsmanship_router,
)
from app.modules.users.presentation.routes import router as users_router

player_api_router = APIRouter(prefix="/api/v1")
player_api_router.include_router(users_router)
player_api_router.include_router(auth_router)
player_api_router.include_router(sports_router)
player_api_router.include_router(assessments_router)
player_api_router.include_router(ratings_router)
player_api_router.include_router(player_profile_router)
player_api_router.include_router(profile_commit_router)
player_api_router.include_router(profile_surface_router)
player_api_router.include_router(play_intents_router)
player_api_router.include_router(photos_router)
player_api_router.include_router(blocks_router)
player_api_router.include_router(friend_link_router)
player_api_router.include_router(friends_router)
player_api_router.include_router(conversations_router)
player_api_router.include_router(games_router)
player_api_router.include_router(sportsmanship_router)
player_api_router.include_router(player_record_router)
player_api_router.include_router(rankings_router)
player_api_router.include_router(groups_router)
player_api_router.include_router(home_clubs_router)
player_api_router.include_router(join_search_router)
player_api_router.include_router(hottest_groups_router)
player_api_router.include_router(new_in_raketa_router)
player_api_router.include_router(same_level_router)
player_api_router.include_router(same_vibe_router)
player_api_router.include_router(on_screen_router)
player_api_router.include_router(invitations_router)
player_api_router.include_router(administrator_router)
player_api_router.include_router(administrator_groups_router)
player_api_router.include_router(payments_router)
player_api_router.include_router(notifications_router)
player_api_router.include_router(proposals_router)
player_api_router.include_router(proposal_players_router)
player_api_router.include_router(pools_router)
player_api_router.include_router(seat_charges_router)
player_api_router.include_router(seat_charge_confirmation_router)
player_api_router.include_router(receipts_router)
player_api_router.include_router(home_router)
player_api_router.include_router(bookings_router)
player_api_router.include_router(handovers_router)
