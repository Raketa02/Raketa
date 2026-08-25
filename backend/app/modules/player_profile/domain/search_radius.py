"""The Search radius bounds: how far out a player may ask to look.

The radius is *"a filter when the player searches, and a weight when the engine
proposes"* (``../../../../CONTEXT.md``) — the same number answering two
questions, because who you asked to see and who the platform offers you are
different acts. Nothing consumes it yet; this module owns the range a player is
allowed to choose from and the value the step opens at.

**Whole kilometres.** The step is a kilometre, so nobody lands on a fractional
distance the matcher could not use anyway, and the served numbers are integers
for the same reason. The unit is in every field name: a bare ``minimum`` is one
refactor away from being read as metres.

Served read-only over the player API for the reason the tag vocabulary is
(``docs/adr/0089``) — a client that hardcodes the range is a client whose slider
disagrees with what the commit will accept.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.kernel import invariant
from app.modules.player_profile.domain.errors import SearchRadiusOutOfBounds


@dataclass(frozen=True)
class SearchRadiusBounds:
    """The range a Search radius may take, and where the control opens."""

    minimum_km: int
    maximum_km: int
    step_km: int
    default_km: int

    def __post_init__(self) -> None:
        invariant(self.step_km >= 1, f"search radius step: {self.step_km}")
        invariant(
            self.minimum_km < self.maximum_km,
            f"search radius range: {self.minimum_km}–{self.maximum_km}",
        )
        invariant(
            self.contains(self.default_km),
            f"search radius default outside its own bounds: {self.default_km}",
        )

    def contains(self, radius_km: int) -> bool:
        """Is this a radius a player is allowed to hold?

        Inside the range *and* on a step boundary. It lives here rather than at
        the call site so that the endpoint serving the bounds and the commit
        re-validating against them cannot answer differently.
        """

        if not self.minimum_km <= radius_km <= self.maximum_km:
            return False
        return (radius_km - self.minimum_km) % self.step_km == 0


#: The served bounds. A change here changes what every client's slider offers and
#: what the profile commit accepts, in one release and without an app-store one.
#:
#: These four numbers were unspecified too, and product confirmed them as they
#: stand on 2026-08-25. Unlike a tag id they are not on a clock: nothing persists
#: a bound, so a later opinion is an edit here rather than a retirement.
SEARCH_RADIUS_BOUNDS = SearchRadiusBounds(
    minimum_km=1,
    maximum_km=50,
    step_km=1,
    default_km=10,
)


@dataclass(frozen=True, slots=True)
class SearchRadius:
    """One player's chosen distance, checked against the served bounds.

    A type rather than a bare ``int`` for the reason every field name here spells
    its unit: a radius that has been validated and a number that happens to be
    inside the range are different things, and only one of them can be stored.

    **The check is re-done here even though the slider cannot offer an invalid
    value.** The bounds are served so a client can build a control that only
    produces legal numbers, and a control is not a validation (``docs/adr/0089``)
    — it is absent from a replayed request and from every build that is not this
    one.
    """

    kilometres: int

    def __post_init__(self) -> None:
        if not SEARCH_RADIUS_BOUNDS.contains(self.kilometres):
            raise SearchRadiusOutOfBounds()

    @classmethod
    def default(cls) -> "SearchRadius":
        """What the control opens at, for a caller that needs a radius to show."""

        return cls(kilometres=SEARCH_RADIUS_BOUNDS.default_km)
