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

**Every card is answered at the run's own now**, and the window is deliberately
not consulted: ``AnswerTheCard`` refuses on *whose evening it was* and *has this
been answered*, neither of which is a clock, because a player who opened a card
at six days and twenty-three hours deserves an answer rather than a refusal. The
declared evenings are two to seven days old, so every card here is inside its own
week anyway — the ghost is the only court nobody may rate, and it is not one of
these because a ghost is not settled-and-played at all.

**Re-running writes nothing twice.** The ledger is asked which of a rater's games
are already closed before anything is sent, for the reason every probe in this
seed exists: a second answer raises, half way through, on a run whose whole job
is to be repeatable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_published_sportsmanship,
    build_settled_courts,
    build_sportsmanship_ledger,
    build_unit_of_work,
)
from app.kernel import Instant
from app.modules.sportsmanship.application.answer_the_card import AnswerTheCard
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import SettledCourt, StarsGiven
from app.seeds.clock import FixedClock
from app.seeds.cohort import COHORT, WHAT_PLAYERS_SAID, Cohort
from app.seeds.paths import player_ids
from app.seeds.pool_history import WHAT_THE_POOL_SAID, address_of, handle_of


class OpinionRefused(RuntimeError):
    """A card the run could not answer, with the reason the platform gave.

    Raised rather than warned, for ``GameRefused``'s reason one file over: an
    opinion that silently failed to exist is a record block developed against a
    state nobody produced, and the symptom is an absent zone that looks exactly
    like the absence the card is *supposed* to be able to draw.
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


async def write_what_players_said(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: Instant,
    cohort: Cohort = COHORT,
) -> SeededOpinions:
    """Answer every declared card, and read back what the platform publishes.

    One session for the whole layer: each card commits through its own unit of
    work, and the probe that skips an already-closed card reads what the previous
    commit wrote.
    """

    async with session_factory() as session:
        people = await player_ids(session, cohort)
        courts = build_settled_courts(session)
        ledger = build_sportsmanship_ledger(session)
        answer = AnswerTheCard(
            clock=FixedClock(at=now),
            courts=courts,
            ledger=ledger,
            unit_of_work=build_unit_of_work(session),
        )

        written: list[str] = []
        for rater, stars_by_subject in sorted(_by_rater().items()):
            rater_id = people[_address(cohort, rater)]
            settled = await courts.courts_of(rater_id, now=now)
            for game_id, given in _cards_of(
                rater, stars_by_subject, settled, cohort=cohort, people=people
            ).items():
                if await ledger.answered_among(rater_id=rater_id, game_ids=(game_id,)):
                    written.append(f"{rater} · {game_id} · already answered")
                    continue
                await answer.execute(
                    AnswerTheCardCommand(
                        game_id=game_id, rater_id=rater_id, given=given
                    )
                )
                written.append(
                    f"{rater} · {game_id} · "
                    + ", ".join(
                        f"{subject} {stars_by_subject[subject]}★"
                        for subject in sorted(_subjects_on(given, people, cohort))
                    )
                )

        published = build_published_sportsmanship(session)
        figures: list[str] = []
        for subject in sorted(everything_said()):
            standing = await published.published_for(people[_address(cohort, subject)])
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


def everything_said() -> Mapping[str, Mapping[str, int]]:
    """**Both declarations, as one table.**

    They are declared apart because each lives where its own population is visible — the
    cohort's in ``cohort.py``, the pool's in ``pool_history.py``, each beside a refusal
    that can see the courts it is asked about — and they are read together because a
    card is one rater's answer about everybody on one court, whichever list put them
    there.

    A subject named in both keeps every rater from each, so the split is a filing
    decision rather than a partition somebody has to maintain.
    """

    merged: dict[str, dict[str, int]] = {}
    for table in (WHAT_PLAYERS_SAID, WHAT_THE_POOL_SAID):
        for subject, said in table.items():
            merged.setdefault(subject, {}).update(said)
    return merged


def _by_rater() -> Mapping[str, Mapping[str, int]]:
    """The declarations, turned inside out. **Subject-first is how they read and
    rater-first is how they are written**, because a card is one rater's answer
    about everybody they played and the store's key is the pair."""

    inverted: dict[str, dict[str, int]] = {}
    for subject, said in everything_said().items():
        for rater, stars in said.items():
            inverted.setdefault(rater, {})[subject] = stars
    return inverted


def _cards_of(
    rater: str,
    stars_by_subject: Mapping[str, int],
    settled: Sequence[SettledCourt],
    *,
    cohort: Cohort,
    people: Mapping[str, UUID],
) -> Mapping[UUID, tuple[StarsGiven, ...]]:
    """Which court carries which stars — **the latest one the two of them shared.**

    A rater with two subjects whose latest courts differ answers two cards, and
    each card carries only the subjects it is the latest court for. That is what
    makes the standing answer the one the fixture declared: the store keeps one
    row per ``(rater, subject)`` and the last write is what stands, so putting a
    rating anywhere but the most recent shared court would be a row a later card
    could overwrite with a blank.
    """

    cards: dict[UUID, list[StarsGiven]] = {}
    for subject, stars in stars_by_subject.items():
        subject_id = people[_address(cohort, subject)]
        shared = [court for court in settled if subject_id in court.others]
        if not shared:
            raise OpinionRefused(
                f"'{rater}' is declared to have rated '{subject}' and the "
                f"platform holds no court of theirs that is played, over and "
                f"has '{subject}' on it. A card is drawn for an evening: the "
                f"declaration in `WHAT_PLAYERS_SAID` names a pair the played "
                f"history never put on the same court, or put there only on the "
                f"arrangement nobody claimed."
            )
        latest = max(shared, key=lambda court: court.played_at)
        cards.setdefault(latest.game_id, []).append(
            StarsGiven(subject_id=subject_id, stars=stars)
        )
    return {game_id: tuple(given) for game_id, given in cards.items()}


def _subjects_on(
    given: Sequence[StarsGiven], people: Mapping[str, UUID], cohort: Cohort
) -> tuple[str, ...]:
    """Who a card is about, for the report — as the fixture's own ids, which
    are what a developer reads: the platform holds a uuid, the report prints
    the slug or the ring position it was seeded under."""

    by_id = {player_id: address for address, player_id in people.items()}
    return tuple(_handle(cohort, by_id[one.subject_id]) for one in given)


def _address(cohort: Cohort, handle: str) -> str:
    """The address behind a handle — ``pool_history``'s walk, which is the one that can
    see all three populations."""

    return address_of(handle, cohort)


def _handle(cohort: Cohort, address: str) -> str:
    """The handle behind an address — :func:`_address` read the other way."""

    return handle_of(address, cohort)


__all__ = [
    "OpinionRefused",
    "SeededOpinions",
    "everything_said",
    "write_what_players_said",
]
