"""The player card — assembled **outside** the engine, from a closed list.

``docs/adr/0107``. A ``ScorableCandidate`` has no name, no photo, no gender, no
birthdate and no precise location, so the response can name a player and say
nothing whatever about who they are. The card is the second author on a returned
row — the same seam ``at_stake`` rides — attached by the backend after
``matchfit`` returns, over the twenty rows that survived rather than over the
pool.

**The list is closed, and two of its absences are permanent refusals rather than
gaps.**

*No bio, and no free-text field of any kind.* It would be the platform's first
player-authored text shown to strangers, which is a moderation surface, and the
full moderation story is out of scope beyond the block.

*No activity recency, at any granularity* — not a timestamp, not *active today*,
not a green dot. That is row three of the Liveness table, and Liveness reaches a
screen the one way it is sanctioned to: as a reason **code**. *"Last seen 2 hours
ago"* is a presence indicator, and this product does not have one.

**A photo id in the record, and a URL on the response.** Photos are served
through short-lived presigned links and a search record is kept forever, so a URL
written into one is a dead link within the hour. The record stores the id; the
response carries ``photo_url`` beside it, minted per response by
:class:`CardPhotoLinks` and written down nowhere.

**And the on-court verdict beside the id, recorded rather than minted**
(``docs/adr/0138``). It goes the other way from the URL and for the mirror
reason: a link is dead within the hour so it cannot be stored, and a verdict is
one store round trip per row so it must not be re-read on every read-back. Both
are facts about the *photograph* rather than about the player, and neither may be
derived by a client — a shield says *checked and passed*, and only a decision the
stored note proves earns one.

**And what the platform watched them do — the record block, from two more
providers, neither of them the index.** The counted-game count and the run of the
last five are ``games``' facts and arrive through :class:`PlayerRecordSource`
(``docs/adr/0137``); the Player Score is ``player_score``'s and arrives through
``PlayerScoreQuery``, **read again at assembly time** (``docs/adr/0140`` §6) —
the engine's own reading of the same port is a separate read for a separate
purpose, bounded by the box where this one is bounded by the shortlist. Three
fields, three providers, and none of them folded into the identity:
``docs/adr/0098`` splits by *who supplies the fact*.

**Every one of the three is omitted rather than printed as a nought** where the
player has none, which is most people. A card is the surface where *nought games*
and *no record* would be one absence in two spellings, and absence here has one.

**A nickname, and nothing may shorten it.** ``users`` holds no real name and no
given name. Every sentence naming somebody uses the whole handle or names
nobody — the prototype's ``split(' ')[0]`` has nothing behind it here, and
inventing a first name is the product addressing a person by a name they never
gave it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import invariant
from app.modules.matchmaking.domain.searches import (
    LAST_FIVE,
    GameResult,
    SearchCandidateRecord,
)
from app.modules.player_profile.domain.photos import PhotoReviewDecision


@final
@dataclass(frozen=True, slots=True)
class CardIdentity:
    """The three card fields the candidate index deliberately does not hold.

    Everything else on a card — the area, the tags, the Level and its band — is
    already on the index row, because those are facts a player changes about
    themselves. These three are absent for two reasons, both deliberate: a
    nickname belongs to ``users``, which the index does not tail at all, and
    **no photo fact reaches the index** by ``docs/adr/0107``'s rule that the card
    is assembled outside the engine — which covers the id and the verdict alike.
    """

    nickname: str
    #: The **first** photo, which is the one a card shows: order is meaning in a
    #: player's photo list. ``None`` when they have none, and the client draws
    #: the generated court poster rather than a placeholder for a missing image.
    photo_id: UUID | None
    #: What the on-court check concluded about **that** photograph, or ``None``
    #: for *nobody looked* (``docs/adr/0138``).
    #:
    #: **The third state is the point of the field.** A shield drawn on ``None``
    #: would claim a check happened on every photo the platform holds from
    #: before ADR-0129, and on every one that arrived while the sidecar was
    #: down. Only a decision the stored note proves crosses; the note itself
    #: never does, on any route, in any shape.
    #:
    #: It travels with `photo_id` and is meaningless without it: this is a fact
    #: about *that* photograph, not about the player.
    review: PhotoReviewDecision | None


@runtime_checkable
class PlayerCardSource(Protocol):
    """Where the three non-index card fields come from.

    **One call for the whole shortlist, never one call per row** — the shape
    every set read in this module has. What that call costs *behind* the port is
    the adapter's business and is not promised here: the one this repository has
    pays a set read for the nicknames, a profile per surviving row and, for a row
    with a photograph, an object-store ``HEAD`` for its verdict
    (``docs/adr/0138``). It is read *after* the floor, so all of that is bounded
    by twenty players even when the pool is five hundred — which is what makes a
    per-row price affordable rather than merely tolerated.
    """

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        """Each of these players' nickname, first photo and that photo's verdict.

        A player absent from the answer is one ``users`` has never heard of. A
        row whose card cannot be assembled is **dropped from the response**
        rather than shown with a blank name: a card with no nickname is not a
        card, and the search is still a `200` with one fewer row.

        **A missing verdict is never a missing card.** It is the ordinary state
        of every photograph nothing has looked at, and of every player who has no
        photograph at all — the row is answered, and the shield is what goes
        absent (``docs/adr/0138``).
        """
        ...


@runtime_checkable
class CardPhotoLinks(Protocol):
    """Where a card's photograph gets an address. **Per response, never stored.**

    The record keeps the id and this mints the link over it — the one difference
    the round trip allows itself, on the ``POST`` and again on every ``GET``
    (``docs/adr/0107``, ``docs/adr/0109``).

    **The client cannot mint one itself, and that is why this exists.**
    ``GET /photos/{id}`` signs only the asking player's own photos and refuses a
    stranger's id deliberately — the alternative is an endpoint that confirms
    whether a stranger's id is real. A card's photo is by definition another
    player's, so the server that disclosed the person hands over their
    photograph with them rather than leaving the client an id it can do nothing
    with.
    """

    async def links_for(
        self, rows: Collection[SearchCandidateRecord]
    ) -> Mapping[UUID, str]:
        """A short-lived URL for each of these rows that recorded a photo.

        **Keyed by player**, because a row is what the renderer holds and a
        photo id is what the record holds. A row whose card has no photo is
        **absent from the answer** rather than present as ``None``: the field is
        omitted on the wire and the client draws the generated court poster.

        One call for the whole list, never one per row — the shape every set
        read in this module has.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class CardRecord:
    """What the platform watched this person do on court. **The card's record block.**

    The second half of a card, beside :class:`CardIdentity`, and it comes from a
    second provider — ``games`` rather than ``users`` — which is why it is a
    second port rather than three more fields on the first. The split is
    ``docs/adr/0098``'s: by *who supplies the fact*, never by how fresh it has to
    be.

    **A player with nothing to show is absent from the answer**, so this type is
    never the empty one. ``games`` measures a zero for ``counted_games_for`` — the
    games were counted and none of them was theirs — and the card does not print
    it: *nought games* and *no record* would be two spellings of one absence on a
    surface whose whole discipline is that absence has one.

    ``last_five`` may still be empty inside a record that exists, and that is not
    the same absence. Somebody with three counted games and no agreed score has a
    count to print and no run of form: an unscored game is an evening, not
    evidence (``docs/adr/0137``).
    """

    #: How many counted games they have played, **friendlies excluded**. One or
    #: more, because a record of nought is an absence and is spelled by not
    #: being in the answer.
    counted_games: int
    #: The last five counted results, **oldest to newest**. Fewer than five is a
    #: real answer and is **never padded** — the card draws the gap.
    last_five: tuple[GameResult, ...]

    def __post_init__(self) -> None:
        invariant(
            self.counted_games >= 1,
            "a record of no games is an absence, and an absence is spelled by "
            f"not being in the answer at all: counted games {self.counted_games}",
        )
        invariant(
            len(self.last_five) <= LAST_FIVE,
            f"{len(self.last_five)} results in a run of {LAST_FIVE}",
        )
        invariant(
            len(self.last_five) <= self.counted_games,
            f"{len(self.last_five)} results out of {self.counted_games} counted "
            "games — a result nobody played",
        )


@runtime_checkable
class PlayerRecordSource(Protocol):
    """Where the card's record block comes from. **One read for the shortlist.**

    Beside :class:`PlayerCardSource` rather than in ``ports.py`` for the reason
    that file gives about itself: it holds what the **scorer** demands, and a
    record block is read after ``matchfit`` returns, over the twenty rows that
    survived. It is the card's second author, on the seam ``at_stake`` and the
    identity already ride (``docs/adr/0107``).

    **The Player Score is deliberately not here**, and it is not because the card
    goes without one. It has its own provider — ``player_score`` rather than
    ``games`` — so it arrives on its own port, ``PlayerScoreQuery``, read a
    second time at assembly (``docs/adr/0140`` §6). Folding somebody else's fact
    into this answer would be the one thing ``docs/adr/0098``'s split exists to
    prevent: a provider signing half of two contracts has signed all of neither.
    """

    async def records_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardRecord]:
        """Each of these players' counted-game count and run of form.

        **A player with no counted game is absent from the answer**, never a
        ``0`` and never an empty run. That is the opposite of what ``games``
        answers its own callers — there a zero is measured, because the games
        were counted and none of them was theirs — and the translation happens at
        the adapter, on the way to a surface where a printed nought would read as
        *this person turns up and loses*.

        **A failure here is not a soft one, and that is why nothing catches it.**
        The absence on this card means *they have none*; an outage answered as an
        empty mapping would publish that about everybody on the shortlist. A
        refusal is the honest answer, exactly as it is when a nickname cannot be
        read.
        """
        ...
