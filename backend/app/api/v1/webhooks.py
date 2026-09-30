"""The routes nobody's client calls: the payment provider's webhooks.

**Mounted beside the three surfaces and on none of them** (``docs/adr/0190``).
A surface is what one client generates its wire types from (``docs/adr/0187``
§5), and the caller here is Stripe, whose event shapes are Stripe's contract —
so these routes are left out of every OpenAPI document, including the running
application's own, and ``app/api/contract.py`` never sees them. They take no
session: a notice is signed, and the signature is the whole of the permission.

**Under ``/api/v1/webhooks``**, so a path still says it is this backend's API and
never begins with a surface's prefix.
"""

from fastapi import APIRouter

from app.modules.payments.presentation.webhook_routes import (
    router as payment_webhooks_router,
)

webhooks_api_router = APIRouter(prefix="/api/v1", include_in_schema=False)
webhooks_api_router.include_router(payment_webhooks_router)
