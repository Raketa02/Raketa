"""Where a line-up can complete, and therefore where a game can be opened.

**Two places, and the second one is easy to miss.** The obvious trigger is the
acceptance that fills the last seat, and ``AcceptSeat`` carries it. The other is a
challenge born of two *Let's play* yeses that met: both seats are accepted from
birth, so in a **singles** sport the court is complete the instant it is minted
and **no accept ever happens on it**. A game opened only from the accept path
would silently never record a tennis game arranged that way — and the failure
would look like *this pair has never played*, which is a sentence the matcher
believes.

This file is the guard on that asymmetry. It drives the mint directly, with
hand-written stubs, because what is under test is *which act opens a game* rather
than anything about a database.

**And what kind of game** (``docs/adr/0169`` §8). A mutual's game is counted
unless either of the pair declared *for fun* for the sport, and the mint is the
one place that rule is decided — so the second half of this file is that rule
from the mint's side, over a stubbed ``FriendlyChoiceQuery``. The translation
from three declarations and an absence into *chose a friendly* is the adapter's,
and is asserted against the real repository in ``test_who_chose_a_friendly.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
)
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)
from app.modules.challenges.domain.challenge import Challenge
from app.shared.ids import new_uuid

MINTED_AT = instant(datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc))


class _AClock:
    def now(self) -> Instant:
        return MINTED_AT


class _NoOpenChallenges:
    """Nothing between anybody, on either of the port's two questions."""

    async def open_pairs_among(self, player_ids, *, now):
        return frozenset()

    async def mutual_born_challenges_that_became_games(
        self, one_player, other_player, *, sport, now
    ):
        # A **tuple**, because the port answers newest-first since
        # ``docs/adr/0154`` §4 — a double that kept the old set would still
        # satisfy every caller here and quietly stop standing for the contract.
        return ()


class _NothingToSettle:
    """A ``SettledGameQuery`` nothing is ever asked of.

    Nobody in this file has minted anything before, so the mint has no id to ask
    about and never makes the call. **It does not raise to prove that**, because
    the mint catches broadly on purpose — a stub that objected here would be
    caught and turned into a silent refusal, which is a guard that has stopped
    guarding. That property is asserted where it can be seen instead:
    ``test_a_mutual_mints_again.py``'s
    ``test_a_first_mint_never_asks_the_settled_read``.
    """

    async def settled_among(self, challenge_ids, *, now):
        return frozenset(challenge_ids)


class _ASafeCourt:
    async def admits(self, player_ids) -> bool:
        return True


class _ChoseAFriendly:
    """A ``FriendlyChoiceQuery`` answering a fixed set, and remembering the ask."""

    def __init__(self, *who: UUID) -> None:
        self._who = frozenset(who)
        self.asked: list[tuple[frozenset[UUID], Sport]] = []

    async def chose_a_friendly_among(self, player_ids, *, sport):
        self.asked.append((frozenset(player_ids), sport))
        return self._who & frozenset(player_ids)


class _Remembering:
    """A challenge repository that keeps what it was given."""

    def __init__(self) -> None:
        self.saved: list[Challenge] = []

    async def load(self, challenge_id: UUID) -> Challenge | None:
        return None

    async def save(self, challenge: Challenge) -> None:
        self.saved.append(challenge)


class _RecordingGames:
    """A ``PlannedGameHandover`` that records what it was asked to open."""

    def __init__(self) -> None:
        self.opened: list[dict] = []

    async def open_planned_game(
        self,
        *,
        challenge_id: UUID,
        sport: Sport,
        counted: bool,
        window: str | None,
        line_up: Sequence[tuple[str, UUID]],
        occurred_at: Instant,
    ) -> UUID | None:
        self.opened.append(
            {
                "challenge_id": challenge_id,
                "sport": sport,
                "counted": counted,
                "window": window,
                "line_up": tuple(line_up),
                "occurred_at": occurred_at,
            }
        )
        return new_uuid()


def _mint(
    games: _RecordingGames,
    *,
    challenges: _Remembering | None = None,
    friendly: _ChoseAFriendly | None = None,
) -> OpenChallengeFromMutualInterest:
    return OpenChallengeFromMutualInterest(
        challenges=challenges or _Remembering(),
        open_challenges=_NoOpenChallenges(),
        settled_games=_NothingToSettle(),
        safety=_ASafeCourt(),
        clock=_AClock(),
        planned_games=games,
        friendly_choices=friendly or _ChoseAFriendly(),
    )


async def test_two_yeses_in_a_singles_sport_open_a_game_with_no_accept_in_sight():
    """The court is complete the moment it exists, so the game is too.

    Nobody will ever tap accept on this challenge — both seats were accepted from
    birth — so this is the only place the arrangement can be handed over.
    """

    games = _RecordingGames()

    await _mint(games).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.TENNIS,
            player_id=new_uuid(),
            other_player_id=new_uuid(),
        )
    )

    assert len(games.opened) == 1
    opened = games.opened[0]
    assert opened["occurred_at"] == MINTED_AT, (
        "the game is dated by the act that caused it"
    )
    assert {side for side, _ in opened["line_up"]} == {"A", "B"}
    assert opened["window"] is None, "no grid was proposed from"


async def test_a_mutual_born_game_is_counted_because_nobody_chose_a_friendly():
    """A friendly is a thing people *choose*, and neither of these two did.

    The alternative — no mode means for fun — would make every game arranged this
    way evidence about nobody, and would hand a player the exact evening they
    never said they wanted.
    """

    games = _RecordingGames()

    await _mint(games).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.SQUASH,
            player_id=new_uuid(),
            other_player_id=new_uuid(),
        )
    )

    assert games.opened[0]["counted"] is True


async def test_two_yeses_in_a_doubles_sport_open_no_game_yet():
    """*A one-to-one padel challenge is half a game*, with a side still to fill.

    The accept path takes it from here, and opening a game now would record an
    arrangement two of the four people are not in.
    """

    games = _RecordingGames()

    await _mint(games).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.PADEL,
            player_id=new_uuid(),
            other_player_id=new_uuid(),
        )
    )

    assert games.opened == []


# ---------------------------------------------------------------------------
# What kind of game — counted unless either declared for fun (ADR-0169 §8)
# ---------------------------------------------------------------------------


async def test_a_mutual_is_a_friendly_when_either_of_the_pair_chose_one():
    """*The deck ignores intent for discovery; the game honours an explicit
    wish.* One of the two said *for fun* for this sport, so the challenge is
    minted ``FOR_FUN`` and the singles game it opens in the same act is a
    friendly — the existing derivation, *counted = mode is not FOR_FUN*, read
    off a mode that is now there to be read."""

    ania, marek = new_uuid(), new_uuid()
    games = _RecordingGames()
    challenges = _Remembering()

    await _mint(games, challenges=challenges, friendly=_ChoseAFriendly(marek)).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.TENNIS, player_id=ania, other_player_id=marek
        )
    )

    (minted,) = challenges.saved
    assert minted.mode is SearchMode.FOR_FUN
    assert games.opened[0]["counted"] is False


async def test_a_mutual_where_nobody_chose_a_friendly_carries_no_mode():
    """Competitive, no preference and undeclared all leave the mode absent —
    the port answers *who chose a friendly* and nobody did, so the aggregate
    is minted exactly as it was before the rule: counted by the absence."""

    ania, marek = new_uuid(), new_uuid()
    challenges = _Remembering()

    await _mint(_RecordingGames(), challenges=challenges).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.TENNIS, player_id=ania, other_player_id=marek
        )
    )

    (minted,) = challenges.saved
    assert minted.mode is None


async def test_a_doubles_mutual_carries_the_friendly_for_the_fill_to_finish():
    """In a doubles sport the mint opens no game — the court is half built —
    so the friendly has to travel on the challenge to the acceptance that
    completes it, which reads ``mode`` off the same aggregate."""

    ania, marek = new_uuid(), new_uuid()
    games = _RecordingGames()
    challenges = _Remembering()

    await _mint(games, challenges=challenges, friendly=_ChoseAFriendly(ania)).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.PADEL, player_id=ania, other_player_id=marek
        )
    )

    (minted,) = challenges.saved
    assert minted.mode is SearchMode.FOR_FUN
    assert games.opened == []


async def test_the_declarations_read_are_the_pairs_in_the_sport_of_the_yes():
    """One read, about exactly these two, in the sport the mutual is in — a
    padel *for fun* says nothing about a tennis game between the same pair."""

    ania, marek = new_uuid(), new_uuid()
    friendly = _ChoseAFriendly()

    await _mint(_RecordingGames(), friendly=friendly).execute(
        OpenFromMutualInterestCommand(
            sport=Sport.SQUASH, player_id=ania, other_player_id=marek
        )
    )

    assert friendly.asked == [(frozenset({ania, marek}), Sport.SQUASH)]
