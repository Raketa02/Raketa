"""Write what other players said: real cards, answered through the real use case.

**A seeded opinion is not a row and cannot be one** (``docs/adr/0029``). It is a
card drawn for a court somebody was really on, answered by a player who was
really seated there, through ``AnswerTheCard`` — which is what refuses a subject
who was not on the court, a rater who was not either, and a second answer to a
card that is already closed. A fixture that inserted into ``sportsmanship_rating``
would prove that a rating can be inserted.

**This layer writes nothing the record reads.** The average and the count are a
**fold over these rows taken when somebody opens a record** — there is no
projection, no summary column and nothing to keep up to date. That is worth
saying here because it is the whole shape of the question this fixture answers:
the record card is empty on a fresh database because *nothing has happened
yet*, not because a table has not been filled in.

**The declaration says what was thought and never where it was said.**
``WHAT_PLAYERS_SAID`` is keyed by subject and then by rater; which of their courts
carries the stars is read back out of the database here, off the rater's own
settled courts. So the fixture cannot name a game that does not exist, a game
moving a day does not have to be chased through the table, and the rule the
platform actually enforces — *only a rater's most recent answer about somebody
counts* — is honoured by putting each rating on the **latest** court the two of
them shared rather than by hoping the order works out.

**Every card is answered the day after its evening** (``RATED_AFTER``), on a
backdated clock: the day it opens, and past the day a silence takes to confirm a
score, so the court is settled and the card is inside the week it is open for
whatever day the run falls on. ``AnswerTheCard`` refuses on *whose evening it
was* and *has this been answered*, neither of which is a clock — the ghost is
the only court nobody may rate, and it is not one of these because a ghost is
not settled-and-played at all.

**The declarations are handed in**, with the resolver that turns a handle into
an address, so this layer imports no other layer's fixtures: the cohort's own
table is the default, and the runner adds whatever else a run declares.

**Re-running writes nothing twice.** The ledger is asked which of a rater's games
are already closed before anything is sent, for the reason every probe in this
seed exists: a second answer raises, half way through, on a run whose whole job
is to be repeatable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_published_sportsmanship,
    build_settled_courts,
    build_sportsmanship_ledger,
    build_unit_of_work,
    build_user_repository,
)
from app.kernel import Instant, instant
from app.modules.sportsmanship.application.answer_the_card import AnswerTheCard
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import SettledCourt, StarsGiven
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT, WHAT_PLAYERS_SAID

#: When a card is answered: the day after its evening, when it opens, and an
#: hour past the day a silence takes to confirm a score — so the court it is
#: drawn for is settled.
RATED_AFTER: Final = timedelta(days=1, hours=1)

#: Who said what about whom — subject, then rater, then stars.
Said = Mapping[str, Mapping[str, int]]


class OpinionRefused(RuntimeError):
    """A card the run could not answer, with the reason the platform gave.

    Raised rather than warned: an opinion that silently failed to exist is a
    record block developed against a state nobody produced, and the symptom is an
    absent zone that looks exactly like the absence the card is *supposed* to be
    able to draw.
    """


@final
@dataclass(frozen=True, slots=True)
class SeededOpinions:
    """Every card this layer wrote, and what the platform now says off them."""

    #: One line per card answered, or per card a previous run already closed.
    cards: tuple[str, ...]
    #: One line per subject, **read back through the published fold** rather than
    #: computed here — the same discipline every assertion in ``screens.py``
    #: takes, and the only way this report can be wrong about the record.
    published: tuple[str, ...]


def everything_said(*tables: Said) -> Said:
    """**Several declarations, as one table.** A subject named in two keeps
    every rater from each, so the split between them is a filing decision rather
    than a partition somebody has to maintain."""

    merged: dict[str, dict[str, int]] = {}
    for table in tables:
        for subject, said in table.items():
            merged.setdefault(subject, {}).update(said)
    return merged


def _cohort_address(handle: str) -> str:
    return COHORT.by_handle(handle).email


async def write_what_players_said(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    said: Said = WHAT_PLAYERS_SAID,
    address_of: Callable[[str], str] = _cohort_address,
) -> SeededOpinions:
    """Answer every declared card, and read back what the platform publishes.

    One session for the whole layer: each card commits through its own unit of
    work, and the probe that skips an already-closed card reads what the previous
    commit wrote.
    """

    async with session_factory() as session:
        people = await _player_ids(
            session,
            {
                address_of(handle)
                for subject, raters in said.items()
                for handle in (subject, *raters)
            },
        )
        handles = {
            address_of(handle): handle
            for subject, raters in said.items()
            for handle in (subject, *raters)
        }
        courts = build_settled_courts(session)
        ledger = build_sportsmanship_ledger(session)

        written: list[str] = []
        for rater, stars_by_subject in sorted(_by_rater(said).items()):
            rater_id = people[address_of(rater)]
            settled = await courts.courts_of(rater_id, now=now)
            for court, given in _cards_of(
                rater, stars_by_subject, settled, people=people, address_of=address_of
            ):
                if await ledger.answered_among(
                    rater_id=rater_id, game_ids=(court.game_id,)
                ):
                    written.append(f"{rater} · {court.game_id} · already answered")
                    continue
                await AnswerTheCard(
                    clock=FixedClock(at=instant(court.played_at + RATED_AFTER)),
                    courts=courts,
                    ledger=ledger,
                    unit_of_work=build_unit_of_work(session),
                ).execute(
                    AnswerTheCardCommand(
                        game_id=court.game_id, rater_id=rater_id, given=given
                    )
                )
                by_id = {player_id: address for address, player_id in people.items()}
                written.append(
                    f"{rater} · {court.game_id} · "
                    + ", ".join(
                        f"{subject} {stars_by_subject[subject]}★"
                        for subject in sorted(
                            handles[by_id[one.subject_id]] for one in given
                        )
                    )
                )

        published = build_published_sportsmanship(session)
        figures: list[str] = []
        for subject in sorted(said):
            standing = await published.published_for(people[address_of(subject)])
            if standing is None:
                raise OpinionRefused(
                    f"'{subject}' is declared to have been rated and the "
                    f"published fold says nobody has said anything. Every card "
                    f"this layer sent was accepted, so the rows are there and "
                    f"the read disagrees — which is a defect in the fold rather "
                    f"than in the fixture."
                )
            figures.append(
                f"{subject} · {standing.average:.1f} / 5 over "
                f"{standing.raters} rater(s)"
            )

    return SeededOpinions(cards=tuple(written), published=tuple(figures))


async def _player_ids(session: AsyncSession, addresses: set[str]) -> Mapping[str, UUID]:
    users = build_user_repository(session)
    found: dict[str, UUID] = {}
    for address in sorted(addresses):
        user = await users.get_by_email(address)
        if user is None:
            raise OpinionRefused(f"{address} is declared and is not registered")
        found[address] = user.id
    return found


def _by_rater(said: Said) -> Mapping[str, Mapping[str, int]]:
    """The declarations, turned inside out. **Subject-first is how they read and
    rater-first is how they are written**, because a card is one rater's answer
    about everybody they played and the store's key is the pair."""

    inverted: dict[str, dict[str, int]] = {}
    for subject, raters in said.items():
        for rater, stars in raters.items():
            inverted.setdefault(rater, {})[subject] = stars
    return inverted


def _cards_of(
    rater: str,
    stars_by_subject: Mapping[str, int],
    settled: Sequence[SettledCourt],
    *,
    people: Mapping[str, UUID],
    address_of: Callable[[str], str],
) -> list[tuple[SettledCourt, tuple[StarsGiven, ...]]]:
    """Which court carries which stars — **the latest one the two of them shared.**

    A rater with two subjects whose latest courts differ answers two cards, and
    each card carries only the subjects it is the latest court for. That is what
    makes the standing answer the one the fixture declared: the store keeps one
    row per ``(rater, subject)`` and the last write is what stands, so putting a
    rating anywhere but the most recent shared court would be a row a later card
    could overwrite with a blank.
    """

    cards: dict[UUID, tuple[SettledCourt, list[StarsGiven]]] = {}
    for subject, stars in stars_by_subject.items():
        subject_id = people[address_of(subject)]
        shared = [court for court in settled if subject_id in court.others]
        if not shared:
            raise OpinionRefused(
                f"'{rater}' is declared to have rated '{subject}' and the "
                f"platform holds no court of theirs that is played, over and "
                f"has '{subject}' on it. A card is drawn for an evening: the "
                f"declaration names a pair the played history never put on the "
                f"same court, or put there only on the game nobody claimed."
            )
        latest = max(shared, key=lambda court: court.played_at)
        cards.setdefault(latest.game_id, (latest, []))[1].append(
            StarsGiven(subject_id=subject_id, stars=stars)
        )
    return [(court, tuple(given)) for court, given in cards.values()]


__all__ = [
    "OpinionRefused",
    "RATED_AFTER",
    "SeededOpinions",
    "everything_said",
    "write_what_players_said",
]
