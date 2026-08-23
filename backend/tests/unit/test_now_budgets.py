"""Now's two budgets: the payload ceiling **fails the build**, latency reports.

ADR-0069 puts two numbers on this screen and ADR-0085 restates the condition both
are measured under. They are deliberately not the same kind of thing:

- **Payload — 150 KB uncompressed for the whole composed envelope — is a gate.**
  It is here rather than in a log line because a ceiling that only advises is one
  that can be reasoned past a defensible field at a time, which is exactly how a
  payload budget is lost. This file is the *only* thing that makes the number
  real.
- **Latency — p99 ≤ 150 ms warm, 250 ms cold — is reported and not enforced.**
  What a p99 measured in a unit suite says about a p99 measured in production is
  *nothing*, and a gate whose number depends on which machine ran it is a gate
  that teaches people to re-run the build. It becomes a gate when there is
  something profileable to measure — ADR-0069's own table is modelled and has
  never been measured against anything.

**Naming the conditions is the load-bearing half**, on ADR-0069's terms: *"a p99
measured against a cold cache is measuring the cache, not the funnel"*, and a
150 KB ceiling at 23 cards and one at 29 cards are different gates wearing one
number. So the conditions are asserted where they can be — the screen really is
23 cards across four lanes, and the report really does name the cache state, the
match count and the card count — rather than being described in a docstring
nothing checks.

**Two regions are outside the measured screen, and it is stated rather than
left to be found.** ADR-0085's *"23 cards across four lanes"* counts the lanes,
which are the only things on Now with a cap; the enrolled strip and the offers
region have none, and a strip card is the heaviest card in the contract — it can
carry a score line with both sides' players named, a refund, an owner's two
figures and a departure. So the ceiling is measured on what the *shelves* can
produce, which is the condition the ADR states, and a player with fifteen matches
of her own is unmeasured. Filed as `Raketa02/Raketa#112` rather than widened
here, because widening the screen a stated number is measured against is exactly
the substitution ADR-0085 spends a section refusing.

**What is measured here is everything above the ports.** The city answers
assembled contexts, which is what a *warm* context cache means: ADR-0069's table
puts context build at 65 ms cold and **0 ms warm**, and the cold half is the
adapter's — a reservation query per club-hour and a rating replay per seated
player. There is no database in this suite, so the cold ceiling cannot be
measured from here at all, and it is reported as unmeasured rather than
approximated.
"""

from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from coverage import Coverage

from app.engines.matchfit.v1 import MatchFitEngineV1
from app.engines.pairing.v1 import PairingEngineV1
from app.kernel import Sport
from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_now import ComposeNow
from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.scoring import MatchScorer
from app.modules.now.domain.arrivals import NEW_CLUBS_CAP, NEW_PLAYERS_CAP
from app.modules.now.domain.funnel import (
    BEST_FIT_CAP,
    CANDIDATE_LIMIT,
    FULL_CAP,
    MatchScoringContext,
)
from app.modules.now.domain.screen import ClubCard, Level, NowScreen, PersonCard, Shelf
from app.modules.now.domain.vocabulary import ShelfCode
from app.modules.now.presentation.schemas import NowResponse
from tests.unit.shelf_doubles import (
    STAMP,
    FakeCityMatches,
    FakeCommitments,
    FakeRatings,
    FakeStandbyPlaces,
    a_club,
    a_context,
    a_match,
    rated,
)
from tests.unit.test_compose_now import (
    FakeParkedRuns,
    FakeRatedSports,
    RecordingEnrolled,
    RecordingNewArrivals,
    SteppingClock,
)

AT = datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc)

#: **150 KB uncompressed for the whole composed envelope** (ADR-0069), held at
#: 23 cards by ADR-0085 rather than re-derived downward — the per-card figure was
#: a derivation and never the rule. Pinned to its literal, on the precedent the
#: funnel's own bounds set: every other number here is read *from* the product,
#: so a constant compared only against itself is one that can move without a
#: single test noticing.
PAYLOAD_CEILING_BYTES = 150 * 1024

#: The fullest realistic screen: **23 cards across four lanes**, 6 · 3 · 8 · 6.
#: Every one of the four is read from the product — two out of ``funnel.py`` and
#: two out of ``arrivals.py``, which is where the shelves that do not run through
#: the ranked funnel keep theirs — and the sum is pinned to its literal below. A
#: fixture holding its own copy of a cap is a screen that stays 23 cards on paper
#: while the product's has become 21.
FULLEST_SCREEN_CARDS = BEST_FIT_CAP + FULL_CAP + NEW_PLAYERS_CAP + NEW_CLUBS_CAP

#: The load both budgets are stated against (ADR-0069, ADR-0085). Retrieval's own
#: safety valve means the funnel sees the soonest ``CANDIDATE_LIMIT`` of them, so
#: the fixture builds the city and then applies the valve exactly as
#: ``CityMatchesFromMatches`` does — measuring 500 through the funnel would be
#: measuring a screen the product cannot produce.
LIVE_CITY_MATCHES = 500

#: The stated gate, reported against rather than asserted on.
LATENCY_P99_MS = 150
COLD_CEILING_MS = 250

#: How many composes the p99 is taken over. A p99 over fewer than a hundred
#: samples is the maximum wearing a percentile's name, so the count is reported
#: beside the figure and this is the number that keeps it honest.
LATENCY_SAMPLES = 100


def _city(how_many: int) -> tuple[MatchScoringContext, ...]:
    """A city of live matches, half of them joinable and half of them full.

    Both lanes have to fill or the screen is not the fullest one: shelf 2 is
    *only* full matches, and a city with none in it composes three cards fewer
    than the budget is measured against.

    Every match is at its own club and its own hour, so nothing here is shaped by
    the diversity pass — what is under test is a full screen, not a varied one.
    """

    built = []
    for n in range(how_many):
        built.append(
            a_context(
                record=a_match(paid=4 if n % 2 else 1 + n % 3, starts=n * 30),
                club=a_club(),
            )
        )
    return tuple(built)


def _retrieved(city: Sequence[MatchScoringContext]) -> tuple[MatchScoringContext, ...]:
    """The safety valve, as ``CityMatchesFromMatches`` applies it: soonest 300."""

    if len(city) <= CANDIDATE_LIMIT:
        return tuple(city)
    soonest = sorted(city, key=lambda one: (one.record.start, str(one.match_id)))
    return tuple(soonest[:CANDIDATE_LIMIT])


def _arrivals() -> RecordingNewArrivals:
    """Shelves 4 and 5 at their caps, with names a real club and player have.

    They are handed in rather than composed because their ports need a database
    and the budget does not care which side of a port a card was built on — what
    it weighs is the card. Their *caps* are the thing the fixture has to respect,
    and those are asserted below rather than trusted.
    """

    return RecordingNewArrivals(
        Shelf(
            code=ShelfCode.NEW_PLAYERS,
            cards=tuple(
                PersonCard(
                    player_id=uuid4(),
                    stamp=STAMP,
                    nickname=f"katarzyna_{n}",
                    level=Level(value=2.7 + n / 10, provisional=n % 2 == 0),
                )
                for n in range(NEW_PLAYERS_CAP)
            ),
        ),
        Shelf(
            code=ShelfCode.NEW_CLUBS,
            cards=tuple(
                ClubCard(
                    club_id=uuid4(),
                    stamp=STAMP,
                    name=f"Zabłocie Sport Club Kraków {n}",
                )
                for n in range(NEW_CLUBS_CAP)
            ),
        ),
    )


def _composer(
    city: Sequence[MatchScoringContext],
) -> tuple[ComposeNow, ComposeNowQuery]:
    """The real composer over a real funnel and the two shipped engines.

    Nothing is stubbed above the ports: the badge is the engine's, the order is
    ``FEED_ORDER``'s and the passes are composition's own, because a budget
    measured against a stand-in measures the stand-in.
    """

    player = uuid4()
    return (
        ComposeNow(
            rated_sports=FakeRatedSports(**{str(player): frozenset({Sport.PADEL})}),
            parked_runs=FakeParkedRuns(),
            new_arrivals=_arrivals(),
            shelves=ComposeShelves(
                city=FakeCityMatches(*city),
                commitments=FakeCommitments(),
                standby=FakeStandbyPlaces(),
                ratings=FakeRatings(PADEL=rated(240)),
                scorer=MatchScorer(
                    pairing=PairingEngineV1(), matchfit=MatchFitEngineV1()
                ),
            ),
            enrolled=ComposeEnrolled(enrolled=RecordingEnrolled()),
            clock=SteppingClock(AT),
        ),
        ComposeNowQuery(player_id=player, sport=SportFilter.PADEL),
    )


def _cards(screen: NowScreen) -> int:
    return sum(
        len(block.cards)
        for block in screen.shelves.shelves
        if isinstance(block, Shelf)
    )


def _envelope(screen: NowScreen) -> bytes:
    """The document the route renders, in the bytes it renders it in.

    ``NowResponse`` *is* the route's ``response_model`` and this is the model's
    own serialiser, so what is weighed here is the body — compact separators, no
    ASCII escaping, and every ``None`` field present as ``null``, because neither
    the route nor the app excludes them.
    """

    return NowResponse.from_domain(screen).model_dump_json().encode("utf-8")


def _instrumentation() -> str:
    """Whether coverage is tracing, because it roughly halves the figure.

    ``make check`` runs pytest under ``--cov`` and a bare ``pytest --no-cov``
    does not, so the same build reports two numbers that differ by more than the
    gate's own headroom. A condition that changes the measurement by a factor of
    two is a condition that has to be in the line.
    """

    return "under coverage" if Coverage.current() is not None else "no coverage"


def _p99(samples: Sequence[float]) -> float:
    """The 99th percentile: the nearest-rank order statistic, sorted first.

    A function rather than three lines inside the measurement, because a
    percentile read off an unsorted list is a random sample wearing a
    percentile's name — and the reported figure is the one thing in that test
    nothing else can check. Here it is checkable against a list whose answer is
    known.
    """

    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, round(0.99 * len(ordered)) - 1)]


def _report(pytestconfig, line: str) -> None:
    """Write one line to the terminal, past pytest's capture.

    A ``print`` in a passing test is swallowed unless somebody remembers ``-s``,
    and a figure nobody sees is not a figure the build reports.
    """

    reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:  # pragma: no cover - only in an embedding without one
        print(line)
        return
    reporter.write_line(line)


# --- the screen both budgets are measured on --------------------------------


async def test_the_measured_screen_is_23_cards_across_four_lanes() -> None:
    """The condition itself, asserted (ADR-0085).

    A budget is only as real as the screen it is measured on, and the cheapest
    way to lose a gate is to keep the number and quietly measure it against a
    thinner screen. Both lanes of the ranked pair have to be *there*, or the
    payload figure below is a figure for a screen no player gets.
    """

    composer, query = _composer(_retrieved(_city(LIVE_CITY_MATCHES)))

    screen = await composer.execute(query)
    lanes = [
        (block.code, len(block.cards))
        for block in screen.shelves.shelves
        if isinstance(block, Shelf)
    ]

    assert lanes == [
        (ShelfCode.BEST_FIT, BEST_FIT_CAP),
        (ShelfCode.FULL_WORTH_WAITING, FULL_CAP),
        (ShelfCode.NEW_PLAYERS, NEW_PLAYERS_CAP),
        (ShelfCode.NEW_CLUBS, NEW_CLUBS_CAP),
    ]
    assert _cards(screen) == FULLEST_SCREEN_CARDS == 23


# --- 1 · the payload ceiling, which fails the build -------------------------


async def test_the_composed_envelope_fits_the_payload_ceiling(pytestconfig) -> None:
    """**150 KB uncompressed at 23 cards, and going over fails the build.**

    This is the whole of the gate. If it goes red the response is ADR-0069's own:
    argue the ceiling in an ADR, or take the field back out — not raise the
    number here, which is the one edit that makes every previous card-contents
    decision retroactively unfunded.
    """

    composer, query = _composer(_retrieved(_city(LIVE_CITY_MATCHES)))
    screen = await composer.execute(query)

    envelope = _envelope(screen)

    # The screen this figure is about, asserted where it is measured. A ceiling
    # kept at its number and quietly measured against a thinner screen is the
    # failure ADR-0085 spends a section on, and it is invisible from a byte
    # count alone.
    assert _cards(screen) == FULLEST_SCREEN_CARDS
    # And weighed as the wire carries it, absent fields included. Excluding them
    # would measure a document nobody receives, in the direction that makes the
    # gate look roomier than it is; `tests/api/test_now.py` holds the other half
    # of that claim, which is that the route really does render them.
    assert b'"debt":null' in envelope

    _report(
        pytestconfig,
        f"[now · payload] {len(envelope) / 1024:.1f} KB uncompressed"
        f" · {_cards(screen)} cards across four lanes"
        f" · ceiling {PAYLOAD_CEILING_BYTES / 1024:.0f} KB (a gate)",
    )
    assert len(envelope) <= PAYLOAD_CEILING_BYTES


def test_the_budgets_and_their_conditions_are_the_decided_numbers() -> None:
    """Pinned to their **literals**, because an ADR is where any of them may move.

    Every other assertion in this file reads these from the constants, so nothing
    else in the suite can see one change — which is how a ceiling comes to be
    raised by the very change that needed it raised, and how a load the gate is
    stated against quietly becomes a load it passes under.
    """

    assert PAYLOAD_CEILING_BYTES == 153_600
    assert LIVE_CITY_MATCHES == 500
    assert (LATENCY_P99_MS, COLD_CEILING_MS) == (150, 250)
    # Not an ADR's number but this file's, and pinned for the same reason: a p99
    # over fewer than a hundred samples is a maximum wearing a percentile's name,
    # and the cheapest way to make a slow measurement fast is to take fewer.
    assert LATENCY_SAMPLES == 100


def test_the_reported_percentile_is_the_percentile() -> None:
    """Against a list whose answer is known, and against it shuffled.

    The figure the build prints is the one thing in the measurement below that
    nothing else can check — every other condition in the line is asserted, and a
    number is a number. A percentile read off the list in arrival order would
    report whichever compose happened to land 99th.
    """

    ordered = [float(n) for n in range(100)]

    assert _p99(ordered) == 98
    assert _p99(list(reversed(ordered))) == 98
    assert _p99([3.0]) == 3.0


# --- 2 · the latency figure, which is reported and does not fail ------------


async def test_the_compose_reports_a_p99_with_the_conditions_it_was_measured_under(
    pytestconfig,
) -> None:
    """Reported, never asserted — and the *conditions* are what is asserted.

    A number without its cache state is a measurement of the cache, so the thing
    this test can genuinely enforce is that the line says what it was measured
    against. The figure itself is left alone: it is a p99 taken in a unit suite,
    on whatever machine ran it, with coverage instrumentation attached.

    What the first run of it found is filed as `Raketa02/Raketa#113`: the figure
    is several times ADR-0069's modelled warm total, and the reason is that the
    table was sized for ~130 candidates where the retrieval valve lets 300
    through. That is the ADR's own *"it may find the shape wrong rather than the
    numbers"*, and it is a decision rather than a fix.
    """

    city = _retrieved(_city(LIVE_CITY_MATCHES))
    composer, query = _composer(city)
    screen = await composer.execute(query)

    assert _cards(screen) == FULLEST_SCREEN_CARDS

    samples = []
    for _ in range(LATENCY_SAMPLES):
        started = time.perf_counter()
        await composer.execute(query)
        samples.append((time.perf_counter() - started) * 1000)

    p99 = _p99(samples)
    line = (
        f"[now · latency] p99 {p99:.0f} ms · median"
        f" {statistics.median(samples):.0f} ms over {LATENCY_SAMPLES} composes"
        f" · warm context cache · {LIVE_CITY_MATCHES} live city matches"
        f" ({len(city)} retrieved) · {_cards(screen)} cards"
        f" · {_instrumentation()}"
        f" · reported, not a gate (stated p99 {LATENCY_P99_MS} ms warm,"
        f" {COLD_CEILING_MS} ms cold — the cold half is the adapter's and is"
        " not measured here)"
    )

    _report(pytestconfig, line)
    assert "warm context cache" in line
    assert str(LIVE_CITY_MATCHES) in line
    assert f"{_cards(screen)} cards" in line
    assert _instrumentation() in line
