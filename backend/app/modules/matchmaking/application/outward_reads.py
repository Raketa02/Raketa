"""Performing an outward read under the posture its port declared.

The **rule** lives with the ports — ``FAIL_POSTURE`` is a claim about each demand
and belongs beside the demand. The **execution** is here, because awaiting
somebody's callable and turning a provider's failure into a refusal is
orchestration rather than a port.

One function reading the table, rather than a `try` at every call site: a caller
cannot quietly soften a gate by handing it a default, and cannot forget to soften
a term, because the same function refuses the mismatch in both directions.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar

from uuid import UUID

from app.kernel import invariant
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.domain.errors import GateDataUnavailable
from app.modules.matchmaking.domain.ports import FAIL_POSTURE, FailPosture

_T = TypeVar("_T")


class _Missing:
    """No stood-down answer was offered. Distinct from ``None``, which is one."""


_MISSING: Any = _Missing()


async def read_demand(
    port: type,
    read: Callable[[], Awaitable[_T]],
    *,
    stood_down: _T = _MISSING,
) -> _T:
    """Perform one outward read under the posture its port declared.

    Takes a callable rather than an awaitable so the refusal happens before the
    provider is touched at all.

    **The soft branch catches broadly, and that is deliberate.** A provider that
    raises and a provider that answers something malformed are the same event to
    a term — it could not be evaluated — and standing down is the right answer to
    both. What keeps that from being silent is the per-term ``NoEvidence`` rate in
    the telemetry, which is load-bearing rather than garnish: a degraded search
    otherwise looks exactly like a duller one.
    """

    posture = FAIL_POSTURE.get(port)
    invariant(
        posture is not None,
        f"{port.__name__} has not said how it fails",
    )
    offered = not isinstance(stood_down, _Missing)
    if posture is FailPosture.CLOSED:
        invariant(
            not offered,
            f"{port.__name__} fails closed and has no degraded answer to fall "
            "through to",
        )
        try:
            return await read()
        except GateDataUnavailable:
            raise
        except Exception as failure:
            raise GateDataUnavailable(
                f"{port.__name__} could not be evaluated"
            ) from failure
    invariant(
        offered,
        f"{port.__name__} fails soft, so the caller says what it stands down to",
    )
    try:
        return await read()
    except Exception:
        return stood_down


async def live_block_set(blocks: BlockQuery, player_id: UUID) -> frozenset[UUID]:
    """This player's live block set, in either direction. **Fails closed.**

    ``BlockQuery`` is not in ``FAIL_POSTURE`` and must not be: it is not one of
    the matcher's outward demands, and its posture is asserted where the port
    lives (``docs/adr/0095``) rather than re-declared in a table here. What is
    left for this module is the same translation :func:`read_demand` performs —
    somebody else's outage becoming the matcher's own refusal, a 503 about the
    platform rather than a 403 about *you*.

    It is a function rather than a line in two use cases because **both** the
    search and its read-back evaluate this gate, and a safety gate that is
    translated in one place and swallowed in the other is the failure the whole
    fail-closed rule exists to prevent.
    """

    try:
        return await blocks.exclusions_for(player_id)
    except BlockStateUnavailable as unavailable:
        raise GateDataUnavailable(
            "the block set could not be evaluated"
        ) from unavailable
