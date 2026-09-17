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
    can record — the commit *is* the end of onboarding's second part. ``PROFILE``
    is the You tab's ``PUT /players/me/proposals-opt-in`` (``docs/adr/0179`` §8),
    where the same question is answered again and every press records: the
    surface is the **route's** and never the body's, because a client that could
    assert where a consent was gathered could assert one it never gathered.
    """

    ONBOARDING = "ONBOARDING"
    PROFILE = "PROFILE"


def answerable_copy_version(value: str) -> str:
    """The copy version a consent answer may be *recorded against*, or a raise.

    **On the write path only.** A consent answer already on a stream is folded
    back without passing through here, for the reason the tag bounds and the
    radius bounds are not re-checked on replay: ``MAX_COPY_VERSION_LENGTH`` is a
    policy number somebody may lower, and a fold that could refuse a recorded
    fact would un-rehydrate the profiles that hold longer ones.

    Raises through ``invariant`` rather than returning a refusal because the
    boundary schema already constrains both ends — reaching this with an empty
    string means a caller inside the application built one, which is a bug.
    """

    invariant(bool(value.strip()), "proposals opt-in with no copy version")
    invariant(
        len(value) <= MAX_COPY_VERSION_LENGTH,
        f"copy version length: {len(value)}",
    )
    return value


@dataclass(frozen=True, slots=True)
class ProposalsOptIn:
    """One answer to the proposals question, with what makes it evidence.

    Note what is *not* here: a default, an "unknown" member, and any way to
    construct one without saying which words were shown. An unanswered opt-in is
    represented by there being no ``ProposalsOptIn`` at all.

    This is the **replayed** shape — what a fold over the stream produces — so it
    asserts only what is true of every answer ever recorded. The rule about which
    copy versions may be *written* lives in ``answerable_copy_version`` above,
    where the write path can reach it and the fold cannot.
    """

    accepted: bool
    copy_version: str
    surface: ConsentSurface
    answered_at: Instant

    def __post_init__(self) -> None:
        # A type-level truth rather than a policy: `accepted` is the answer, and
        # a non-bool here means something has put a third state into a question
        # that has two. Never edited by a product decision, so never a hazard on
        # replay.
        invariant(
            isinstance(self.accepted, bool),
            f"proposals opt-in answer: {self.accepted!r}",
        )
