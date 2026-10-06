"""Request-scoped declarations for the matchmaking context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.

**Two gates are declared here, and nothing else since #579.** The searches, the
deck and the radar went, and with them every ledger and workbench this file
used to declare; what is left is the pair of account gates the player record
asks before it shows one player to another. They stay declared in the matcher's
own words, exactly as `get_block_query` is declared once in `blocks`: a surface
deciding for itself where a gate comes from is how one of them ends up wired to
a different answer.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import DbSession
from app.bootstrap.composition import (
    build_account_hold_query,
    build_account_status_query,
)
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery


def get_account_hold_query(db: DbSession) -> AccountHoldQuery:
    """Whether an account is under a live hold. **Declared, like every gate.**

    A line here rather than a call inside a use case's factory, for the reason
    ``get_block_query`` is: a gate the test suite cannot reach is a gate whose
    fail-closed posture is asserted only in prose.
    """

    return build_account_hold_query(db)


AccountHoldQueryDep = Annotated[AccountHoldQuery, Depends(get_account_hold_query)]


def get_account_status_query(db: DbSession) -> AccountStatusQuery:
    """The set of accounts that may not be shown. Fails closed."""

    return build_account_status_query(db)


AccountStatusQueryDep = Annotated[AccountStatusQuery, Depends(get_account_status_query)]
