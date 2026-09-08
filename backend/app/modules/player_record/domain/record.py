"""What a record says about a person, in this context's own words.

**The header identity, and today that is the whole of it.** The skill card, the
metered rows, what opponents said and the sport pills all arrive on this type
later (#379–#387); what ships first is the zone every one of them hangs under,
because the route and its admission rule are what the rest of the sheet is
blocked on.

**Every one of these fields is spelled here rather than imported**, and the
duplication is the decision (``docs/adr/0155``). ``matchmaking`` already holds a
``CardIdentity`` with three of them on it, and a record that reused it would
inherit a *card's* closed list — the list ``docs/adr/0107`` keeps short because it
is attached over the twenty rows of a search and frozen into a record kept for
ever. A record is one person, live, and read at most a handful of times a day.
Two surfaces with two lists, and the day one of them grows a field is the day the
other one is asked whether it wants one.

**A photograph's three facts travel together and are meaningless apart.** The id
is what the platform stores, the link is minted for this response and written
down nowhere (``docs/adr/0107``), and the verdict is what the on-court check
concluded about *that* photograph rather than about the player
(``docs/adr/0138``). A player with no photograph has none of the three, and the
client draws the generated court poster rather than a placeholder.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID


class OnCourtVerdict(StrEnum):
    """What the on-court check concluded about a photograph. **Two values.**

    The third state — *nobody looked* — is the **absence** of one of these and
    never a third value, which is ``docs/adr/0138``'s rule: a shield saying
    *checked and passed* cannot be drawn on a photograph nothing examined, and a
    value meaning *unknown* is a value somebody eventually draws a tick for.

    **The words are the ones a card already carries, and they are checked
    against it.** This is a second spelling of ``player_profile``'s
    ``PhotoReviewDecision`` on purpose — this context imports no other context's
    domain types — and a second spelling that drifts is worse than an import: a
    client reading a search card and a record would get two words for one fact.
    ``tests/unit/test_player_record_identity.py`` fails the build if the two
    vocabularies stop agreeing.
    """

    ALLOWED = "allowed"
    FLAGGED = "flagged"


@final
@dataclass(frozen=True, slots=True)
class SubjectIdentity:
    """Who this person is, as the platform can describe them to a stranger.

    **The whole handle and nothing that shortens it.** ``users`` holds a nickname
    and no real name; every sentence naming somebody uses the handle they gave or
    names nobody.

    **The area is a code and never a sentence.** Nothing in this repository can
    turn a coordinate into the name of a neighbourhood, and a code is what
    licenses the one comparison a client may make — *are we in the same square*
    (``docs/adr/0021``).
    """

    nickname: str
    #: The **first** photo, because order is meaning in a player's photo list.
    #: ``None`` when they have none.
    photo_id: UUID | None
    #: What the check concluded about ``photo_id``, or ``None`` for *nobody
    #: looked*. Meaningless without a photo id, and never present without one.
    review: OnCourtVerdict | None
    #: Their coarse area, as a machine code.
    area_code: str
    #: The Social tag ids they hold, in the vocabulary's own order.
    social_tags: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class PlayerRecord:
    """One player's record, as of the moment somebody opened it.

    **``is_self`` is the server's answer and not the client's.** A sheet titled
    *How others see you* draws a different screen from one about a stranger — no
    distance, a coarse band where a figure would be — and a client deciding that
    by comparing the id it asked about against the one in its session is a client
    that gets it wrong exactly once, on the screen where being wrong is most
    visible. So the subject's id is deliberately **not** on this type: there is
    nothing here to compare.
    """

    is_self: bool
    identity: SubjectIdentity
    #: A short-lived signed URL for ``identity.photo_id``, minted for this
    #: response and stored nowhere. **Present exactly when the photo id is**:
    #: signing is a signature over a request that is never sent, so there is no
    #: outage that produces an id without an address for it.
    photo_url: str | None


__all__ = [
    "OnCourtVerdict",
    "PlayerRecord",
    "SubjectIdentity",
]
