"""The Proposals opt-in: an answer, and the evidence that it was given.

This is the record ADR-0089 is *about*. Five of a profile's six answers are
ordinary mutable preferences; this one is a consent record, and a boolean column
cannot evidence one. What makes it evidence is the three facts recorded beside
the answer:

- **the moment** it was given — which the event carries as its ``occurred_at``,
  like every other event, so nobody maintains a second timestamp;
- **the copy version shown**, because consent gathered against one sentence is
  not consent to a different one, and copy changes;
- **the surface** it was answered on, because *asked during onboarding* and
  *changed later from the profile screen* are different acts and a consent log
  that cannot tell them apart cannot answer the only question anyone will ask of
  it.

**It has no default. Unanswered is neither yes nor no** — the screen is never
pre-ticked and no other act in the product may be read as answering it
(``../../../../CONTEXT.md``: *Skipping is not consent*). That is why the type
below has no default value anywhere in it, and why the commit refuses a null
rather than filling one in.

**What ``false`` switches off** is stated in the glossary rather than here:
opting out stops the engine pushing, not the player existing. Nothing consumes it
yet — there is no matchmaking engine to switch off — and writing the rule down
before the consumer exists is the point.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.kernel import Instant, invariant

#: The longest a copy version string may be. Long enough for any scheme a
#: content pipeline might use (a date, a hash, a release tag), short enough that
#: nothing prose-shaped ends up in a consent record — **the copy itself is never
#: stored**, only the identifier of it. Freezing copy in history is how a wording
#: change becomes a migration.
MAX_COPY_VERSION_LENGTH: Final = 64


class ConsentSurface(StrEnum):
    """Where a player was standing when they answered.

    Two values, and both are reachable. ``ONBOARDING`` is the only one the commit
    can record — the commit *is* the end of onboarding's second part. The profile
    screen edits the same value later (``docs/adr/0089``), which is what
    ``PROFILE`` is for; the aggregate transition it uses exists, and the endpoint
    that drives it does not yet.
    """

    ONBOARDING = "ONBOARDING"
    PROFILE = "PROFILE"


@dataclass(frozen=True, slots=True)
class ProposalsOptIn:
    """One answer to the proposals question, with what makes it evidence.

    Note what is *not* here: a default, an "unknown" member, and any way to
    construct one without saying which words were shown. An unanswered opt-in is
    represented by there being no ``ProposalsOptIn`` at all.
    """

    accepted: bool
    copy_version: str
    surface: ConsentSurface
    answered_at: Instant

    def __post_init__(self) -> None:
        invariant(
            isinstance(self.accepted, bool),
            f"proposals opt-in answer: {self.accepted!r}",
        )
        invariant(
            bool(self.copy_version.strip()),
            "proposals opt-in with no copy version",
        )
        invariant(
            len(self.copy_version) <= MAX_COPY_VERSION_LENGTH,
            f"copy version length: {len(self.copy_version)}",
        )
