"""The register of kept-order stores, and the questions every one of them
answers (#770; ``docs/adr/0203`` §10).

**A kind of its own, as ``payments_demands.py`` and ``push_demands.py`` are**:
the two adapters of one port onto the outside world — the ephemeral store's,
which every API process reads, and **the in-memory equivalent** every test and
a seed run stand on — so
``tests/demands/test_general_order_demands.py`` asks both the same questions,
and an in-memory store that drifts from Redis's goes red rather than green.

**Redis's is built over whatever client the test hands it** — the suite's
in-process fake server (``tests/unit/fake_redis.py``), so no test needs Redis
running — and **as the composition root builds it**, wrapped, so the wrapper is
held to the same answers. What that leaves unproven is that a real server
orders and counts its members as the fake does; ``make up`` is where that is
answered, and #770's measurement was taken against it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from redis.asyncio import Redis

from app.bootstrap.composition import (
    build_general_orders,
    build_general_orders_kept_here,
)
from app.modules.rankings.domain.ports import GeneralOrders


@dataclass(frozen=True)
class RegisteredOrderStore:
    """One adapter of the kept orders, and how to build it over a client."""

    name: str
    build: Callable[[Redis], GeneralOrders]


GENERAL_ORDER_IMPLEMENTATIONS: tuple[RegisteredOrderStore, ...] = (
    RegisteredOrderStore(
        name="InMemoryGeneralOrders",
        build=lambda client: build_general_orders_kept_here(),
    ),
    RegisteredOrderStore(name="RedisGeneralOrders", build=build_general_orders),
)


__all__ = ["GENERAL_ORDER_IMPLEMENTATIONS", "RegisteredOrderStore"]
