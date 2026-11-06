"""The public API surface.

Every endpoint the public site (``frontend_public/``) may depend on, and
nothing any other client reads (``docs/adr/0187`` §5). ``app/api/contract.py``
emits it as ``openapi.public.json``, which the site generates its wire types
from.

**No route here takes a session**: the site has no sign-in, no session and no
cookies (§4), and serves strangers — somebody who tapped a group link without
the app, and somebody who opened an invitation or a reset email on a laptop.
So **it discloses the least a page needs** (§5): a group's name, tile, club,
district, sports and size, and never who is in it; a friend link's owner's
nickname and face, and nothing else about them; an invitation's name, club
and state, and its code while it still works; a reset's state. The two
password pages set a password by exactly the rules the app follows, and **sign
nobody in** — there is nothing on the site to hold a session in.

**Its own prefix, ``/api/v1/public``**, so no path is ever in two documents
(``tests/unit/test_public_surface.py``). A token travels in a body, never a
path, so it is in no access log; a group's code is in the path, because it is
the link a WhatsApp group was sent and no secret — and a friend link's, for the
same reason.
"""

from fastapi import APIRouter

from app.modules.administrators.presentation.public_routes import (
    router as invitations_router,
)
from app.modules.auth.presentation.public_routes import (
    router as password_resets_router,
)
from app.modules.friends.presentation.public_routes import (
    router as friend_links_router,
)
from app.modules.groups.presentation.public_routes import router as groups_router

public_api_router = APIRouter(prefix="/api/v1/public")
public_api_router.include_router(groups_router)
public_api_router.include_router(invitations_router)
public_api_router.include_router(password_resets_router)
public_api_router.include_router(friend_links_router)
