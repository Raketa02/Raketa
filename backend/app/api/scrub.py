"""Where the clock is, and how a developer moves it (ADR-0092).

**Not on either API surface, and that is structural rather than a decision this
module makes.** `app/api/contract.py` emits the two documents from the two
surface routers, and this router is neither of them — it is mounted on the
application beside `/health`, by `create_app`, and only when `CLOCK_SCRUBBABLE`
is on. So no client generates a type for it, no client can call it by accident,
and `make gen-api` has nothing to say about it. `tests/api/test_scrub.py` holds
that claim as an assertion, because a router moved one line up in `create_app`
would put it in both documents and nothing else would look different.

The path is `/_clock` rather than `/api/v1/clock`. The prefix rule in
`backend/CLAUDE.md` is about the product's routes and this is not one: it exists
for the person developing against the seeded week, it ships turned off, and it
is refused outside `local` by the settings object.

**Three verbs, and the third is the one that matters.** Reading says where the
clock is; moving it says where to go; releasing gives the host's clock back —
and it is spelled as its own verb rather than as *scrub to now* so that a script
finishing up has something unambiguous to call. Every one of them answers the
same body, so a caller never has to ask a second question to find out what it
did.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

from app.kernel import Instant, Seconds, instant


@runtime_checkable
class MovableClock(Protocol):
    """What this router needs of a clock, declared where it is needed.

    Not `app.infrastructure.clock.ScrubbableClock`, and the difference is a rule
    rather than a preference: `tests/unit/test_system_clock.py` walks the tree
    and refuses any module outside `app/bootstrap/` that imports the clock
    adapter, because a layer that can reach a live clock is one refactor away
    from calling it. A route is not wiring. So the shape is declared here, the
    composition root passes something that satisfies it, and this module never
    learns which clock is real.

    It is a superset of the kernel's `Clock` on purpose: a scrub is not part of
    what the domain knows a clock to be, and `app.kernel` is not where a
    developer's convenience goes.
    """

    def now(self) -> Instant: ...

    def base_now(self) -> Instant: ...

    @property
    def displaced_by(self) -> Seconds: ...

    def scrub_to(self, moment: Instant) -> Seconds: ...

    def release(self) -> Seconds: ...


class ScrubRequest(BaseModel):
    """Where to put the clock."""

    at: datetime = Field(
        description=(
            "The instant the clock should read, with a UTC offset. The seeded "
            "week runs from Monday 7 September 2026."
        ),
        examples=["2026-09-08T21:30:00Z"],
    )

    @field_validator("at")
    @classmethod
    def _carries_an_offset(cls, value: datetime) -> datetime:
        # The kernel refuses a naive instant and would raise from inside the
        # adapter, which is a 500 for what is plainly a bad request. Refused
        # here instead, so it arrives as a 422 naming the field.
        if value.tzinfo is None:
            raise ValueError(
                "carries no UTC offset — write it as 2026-09-08T21:30:00Z"
            )
        return value


class ClockResponse(BaseModel):
    """What the clock says, what the host says, and how far apart they are."""

    now: datetime = Field(description="What every request in this process reads.")
    wall_clock: datetime = Field(description="What the host's own clock reads.")
    displaced_by_seconds: int = Field(
        description=(
            "How far `now` runs from the wall, in whole seconds. Negative runs "
            "behind it. Time still passes at either displacement: this is an "
            "offset, not a freeze."
        )
    )
    scrubbed: bool = Field(
        description="Whether the clock has been moved off the host's at all."
    )

    @classmethod
    def of(cls, clock: MovableClock) -> "ClockResponse":
        return cls(
            now=clock.now(),
            wall_clock=clock.base_now(),
            displaced_by_seconds=clock.displaced_by,
            scrubbed=clock.displaced_by != 0,
        )


def build_scrub_router(clock: MovableClock) -> APIRouter:
    """The three routes, closed over the process's one movable clock.

    A factory rather than a module-level router with a dependency, because the
    thing being moved is *the process's* and not the request's. A `Depends` here
    would say the opposite — that each request gets a clock — which is exactly
    the misreading that would let somebody build a fresh one and lose every
    scrub at the end of the response.
    """

    router = APIRouter(tags=["clock"])

    @router.get(
        "/_clock",
        response_model=ClockResponse,
        status_code=status.HTTP_200_OK,
        summary="Where this process's clock is standing",
    )
    async def read_clock() -> ClockResponse:
        return ClockResponse.of(clock)

    @router.post(
        "/_clock",
        response_model=ClockResponse,
        status_code=status.HTTP_200_OK,
        summary="Stand the clock at an instant, and let it run on from there",
    )
    async def scrub_clock(body: ScrubRequest) -> ClockResponse:
        """Move the whole deployment, not this request.

        Everything reading time reads the same displaced clock afterwards — the
        next request, the delivery worker's tick, the cascade. That is the point:
        a week walked by one screen while the timekeeper stayed on the wall
        would be a week in which no deadline ever arrived.
        """

        clock.scrub_to(instant(body.at))
        return ClockResponse.of(clock)

    @router.delete(
        "/_clock",
        response_model=ClockResponse,
        status_code=status.HTTP_200_OK,
        summary="Give the host's clock back",
    )
    async def release_clock() -> ClockResponse:
        clock.release()
        return ClockResponse.of(clock)

    return router
