"""Request-scoped declarations for the matchmaking context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.

**Declared before their first caller exists**, exactly as `get_block_query` was
and for the same reason: every Play surface reads these two, none of them is
built, and the surfaces should wire to this line rather than each deciding where
a ledger comes from. It also puts the seam where the test suite can hold it —
`tests/conftest.py` overrides both with in-memory ledgers, so **no test in this
suite needs Redis running**, and that stays true on the day the first route
lands rather than becoming somebody's problem then.

The one infrastructure import here is `get_redis`, which is not an adapter but
the process's connection pool — the same allowance `get_db` has in
`app/api/dependencies.py`, on the same argument.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.bootstrap.composition import (
    build_exposure_ledger,
    build_suppression_ledger,
)
from app.infrastructure.redis_client import get_redis
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger

# The pool is the process's, not the request's — `get_redis` takes no request and
# reads no application state. It stays a `Depends` so a test can override it, and
# so that a route asking for a ledger never has to know a client exists.
EphemeralStoreDep = Annotated[Redis, Depends(get_redis)]


def get_exposure_ledger(store: EphemeralStoreDep) -> ExposureLedger:
    return build_exposure_ledger(store)


ExposureLedgerDep = Annotated[ExposureLedger, Depends(get_exposure_ledger)]


def get_suppression_ledger(store: EphemeralStoreDep) -> SuppressionLedger:
    return build_suppression_ledger(store)


SuppressionLedgerDep = Annotated[SuppressionLedger, Depends(get_suppression_ledger)]
