"""The cohort: what it declares, what it promises about the screens, and when it fails.

Four claims, and each fails differently.

1. **The declarations are a committed artifact, and it holds inputs only.** A
   generator edit arrives as a readable population diff rather than as a fixture
   that silently became a different fixture — and no level, uncertainty or band
   is in the file, because those are the engine's answers and a committed copy of
   an answer is a second number nothing keeps honest.
2. **The draws are keyed off the handle**, so adding or removing one member
   changes that row and nobody else's, and two developers get one database.
3. **The assertions run the real read paths as the protagonist.** This is the
   expensive test and the one the whole layer exists for: a pool, a deck, a
   court, a ladder and four named states, read through the use cases a request
   runs, against a database the seed has just written.
4. **Three different clocks fail the run** — an engine retune moves the band
   histogram, a calendar walks the cohort out of ADR-0113's window, and either
   stops `make seed` by name rather than warning.

The suite drives its own SQLite fixture, exactly as `test_seed_runner.py` does.
The `make seed` gate proper needs a real database and does not run in CI, which
is the same half-a-gate the ruleset diff ships with and is stated here rather
than discovered.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.engines.assessment import AnswerOption, Question
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Sport
from app.seeds import catalog
from app.seeds.catalog import (
    PROTAGONISTS,
    THE_BLANK_WEEK_PLAYER,
    THE_POPULATED_PLAYER,
    AnswerPolicy,
    answer_key,
)
from app.seeds.clock import NEWCOMER_WINDOW_DAYS, FixedClock, days_before
from app.seeds.cohort import (
    ARCHETYPES,
    ARTIFACT,
    BAND_HISTOGRAM,
    COHORT,
    RINGS,
    Cohort,
    as_document,
    generate,
)
from app.seeds.pairs import write_the_relationships
from app.seeds.runner import (
    COHORT_DISCLAIMER,
    SeedFailed,
    refuse_a_cohort_that_has_aged_out,
    refuse_a_histogram_that_has_moved,
    report,
    seed,
    seed_the_cohort,
)
from app.seeds.screens import CANNOT_BE_DRAWN, assert_the_screens

ROOT = Path(__file__).resolve().parents[2]


def a_question(*, tier: str | None, options: int, id: str = "probe") -> Question:
    return Question(
        id=id,
        category="Probe",
        situation="A situation.",
        text="A question?",
        qualifier="Choose one.",
        tier=tier,
        options=tuple(
            AnswerOption(id=f"o{index}", text=f"option {index}")
            for index in range(options)
        ),
    )


# ---------------------------------------------------------------------------
# 1. The artifact: committed, and inputs only
# ---------------------------------------------------------------------------


def test_the_committed_population_is_what_the_generator_draws():
    """`make gen-cohort`, and the file beside it. **Byte-identical or a diff.**

    The repository's generate-commit-diff idiom, fourth instance: an edit to the
    generator has to arrive as a visible population diff, or the fixture every
    Play screen is developed against changes underneath the person reading the
    pull request.
    """

    committed = json.loads(ARTIFACT.read_text())

    assert committed == as_document(generate()), (
        "app/seeds/cohort.json is not what the generator draws — run "
        "`make gen-cohort` and commit the diff."
    )


def test_the_population_records_no_answer_the_engine_gave():
    """**Inputs only**, checked over the whole document rather than per field.

    A level, an uncertainty or a band in this file would be a second copy of a
    number the engine owns — and the day the two disagreed, the file would be the
    one people believed, because it is the one they can read.
    """

    text = json.dumps(as_document(generate()))

    for forbidden in ("\"mu\"", "\"sigma\"", "\"level\"", "\"confidence\""):
        assert forbidden not in text, f"the population records {forbidden}"
    for member in json.loads(text)["members"]:
        assert "band" not in member, f"{member['handle']} carries a band"
    # The band names that *are* in the file are declarations — which band an
    # archetype aims at, and the histogram the run checks the engine against —
    # and the artifact's own header says so.
    assert "aims_at_band" in text, "an archetype no longer says which band it is for"
    assert "newcomer" in json.loads(text)["members"][0], "the newcomer flag is gone"


def test_every_committed_member_is_a_function_of_their_handle():
    """The keying that makes the file worth committing at all.

    Under one global stream, inserting a member rewrites every row after it, the
    diff is noise, and committing buys nothing. Keyed off the handle, a member's
    row is a function of their name — so a member removed from the middle leaves
    every other row byte-identical.
    """

    whole = {member.handle: member for member in generate().members}
    kept = {
        member.handle: member
        for member in generate().members
        if member.handle != "cohort-a-07"
    }

    assert set(whole) - set(kept) == {"cohort-a-07"}
    for handle, member in kept.items():
        assert member == whole[handle], f"removing a member moved {handle}"


def test_the_cohort_is_the_same_under_two_hash_seeds():
    """`docs/adr/0105`'s question, answered rather than assumed.

    Every draw is seeded from a *string*, which `random.Random` hashes with
    SHA-512 before seeding — so nothing here rides on `PYTHONHASHSEED`. Asserted
    across two processes because that is the only place the interpreter's hash
    seed is a variable at all.
    """

    drawn = [_draw_in_a_subprocess(seed) for seed in ("0", "1")]

    assert drawn[0] == drawn[1]


def _draw_in_a_subprocess(hash_seed: str) -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json;from app.seeds.cohort import as_document, generate;"
            "print(json.dumps(as_document(generate()), sort_keys=True))",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


# ---------------------------------------------------------------------------
# 2. The declarations themselves
# ---------------------------------------------------------------------------


def test_the_rings_are_cut_by_the_ladders_own_multipliers():
    """Each rung reaches a ring the one below it did not, **by construction**.

    Written out here rather than read from `Ring.bounds_km`, because a test that
    checks a constant against itself agrees with every value that constant could
    take: this is the ladder's own ×1.5 and ×2.0 against the protagonist's own
    radius, spelled from the two facts the product owns.
    """

    radius = catalog.PROTAGONIST_RADIUS_KM
    edges = [ring.bounds_km for ring in RINGS]

    assert edges[0] == (0.0, float(radius))
    assert edges[1] == (float(radius), radius * 1.5)
    assert edges[2] == (radius * 1.5, radius * 2.0)
    assert edges[3][0] == radius * 2.0
    # The last ring is past the slider's ceiling, so no radius a player can set
    # and no rung the ladder can offer reaches it.
    assert edges[4][0] == 50.0
    # And somebody lives past it, or `radius_clamp` has nobody it provably
    # cannot reach and the ceiling is a rule with no witness.
    assert any(member.ring == RINGS[4].code for member in COHORT.members)


def test_one_archetype_per_band_and_a_histogram_that_names_them_all():
    bands = [archetype.band for archetype in ARCHETYPES]

    assert len(bands) == len(set(bands))
    assert set(bands) == set(BAND_HISTOGRAM)


def test_no_cohort_member_carries_a_photo():
    """A seeded photo would need bytes in this repository and a store to put them
    in, and the card renders the generated court poster without one — which is
    the state most cards are in and the one worth developing against."""

    from app.seeds.runner import _profile_of

    for member in COHORT.members:
        assert _profile_of(member).photo_ids == ()
    for account in PROTAGONISTS:
        assert account.profile is not None and account.profile.photo_ids == ()


def test_the_protagonists_straddle_the_newcomer_window_with_both_edges_clear():
    """Three settled and one inside, and neither on the edge.

    A protagonist accidentally inside the window would tighten the level gate on
    every search a developer ran, and nothing on the screen would say why.
    """

    ages = {
        account.slug: account.profile.committed_days_ago
        for account in PROTAGONISTS
        if account.profile is not None
    }

    assert len(ages) == len(PROTAGONISTS), "a protagonist has no profile"
    assert ages["the-newcomer"] < NEWCOMER_WINDOW_DAYS - 1
    for slug, days in ages.items():
        if slug != "the-newcomer":
            assert days > NEWCOMER_WINDOW_DAYS + 1, slug


def test_the_cohort_declares_both_sides_of_the_window():
    inside = [member for member in COHORT.members if member.is_a_newcomer]
    outside = [member for member in COHORT.members if not member.is_a_newcomer]

    assert inside and outside
    assert all(
        member.committed_days_ago < NEWCOMER_WINDOW_DAYS - 1 for member in inside
    )
    assert all(
        member.committed_days_ago > NEWCOMER_WINDOW_DAYS + 1 for member in outside
    )


# ---------------------------------------------------------------------------
# 3. The widened answer policy
# ---------------------------------------------------------------------------


def test_a_named_policy_answers_the_same_thing_for_everybody():
    """The six catalog policies are zero-spread draws, unchanged by the widening.

    A named account's claim is one band and one position inside it, so its
    answers may not depend on who is answering — which is also why a spread
    policy in the catalog is refused at import.
    """

    policy = AnswerPolicy(claims=1, demonstrations=3)
    question = a_question(tier="standard", options=5)

    assert policy.option_id_for(question, drawn_for="alice|PADEL") == "o3"
    assert policy.option_id_for(question, drawn_for="bob|TENNIS") == "o3"


def test_a_spread_policy_draws_per_handle_sport_and_question():
    """The three parts of the key, each shown to move the answer.

    Keyed this way and never by consumption order: an engine that inserted one
    question would otherwise reshuffle every later answer for every member, and
    the band histogram would move for a reason having nothing to do with skill.
    """

    policy = AnswerPolicy(claims=2, demonstrations=2, demonstration_spread=2)
    first = a_question(tier="standard", options=5, id="q1")
    second = a_question(tier="standard", options=5, id="q2")

    for member in ("cohort-a-05", "cohort-a-06", "cohort-a-07"):
        key = answer_key(member, Sport.PADEL)
        assert policy.option_id_for(first, drawn_for=key) == policy.option_id_for(
            first, drawn_for=key
        )

    keyed = {
        policy.option_id_for(first, drawn_for=answer_key(handle, Sport.PADEL))
        for handle in ("cohort-a-05", "cohort-a-06", "cohort-a-07", "cohort-a-08")
    }
    assert len(keyed) > 1, "every member answered identically"

    one = answer_key("cohort-a-05", Sport.PADEL)
    other = answer_key("cohort-a-05", Sport.TENNIS)
    per_sport = {
        policy.option_id_for(first, drawn_for=one),
        policy.option_id_for(first, drawn_for=other),
    }
    per_question = {
        policy.option_id_for(first, drawn_for=one),
        policy.option_id_for(second, drawn_for=one),
    }
    assert len(per_sport) > 1 or len(per_question) > 1


def test_every_archetype_declares_zero_width_on_the_claims():
    """The opening question is a claim, and its weakest option ends the run.

    A drawn claim would not spread a member around their band — it would put them
    on the engine's one-question beginner path and into a different archetype's.
    So the width is **declared** per axis and every archetype declares zero on
    the claims; asserted over the archetypes rather than over the mechanism,
    because the mechanism draws every question and the exception is a number.
    """

    assert all(
        archetype.answers.claim_spread == 0 for archetype in ARCHETYPES
    ), "an archetype jitters its claims, and the opening claim ends the run"

    policy = AnswerPolicy(claims=2, demonstrations=2, demonstration_spread=2)
    claim = a_question(tier=None, options=5)

    answers = {
        policy.option_id_for(claim, drawn_for=answer_key(handle, Sport.PADEL))
        for handle in (member.handle for member in COHORT.members)
    }
    assert answers == {"o2"}


def test_a_named_account_may_not_carry_a_spread(monkeypatch):
    monkeypatch.setattr(
        catalog,
        "ACCOUNTS",
        (
            catalog.SeedAccount(
                slug="drawn",
                description="a claim nobody can check",
                scenarios=(
                    catalog.RatedRun(
                        sport=Sport.PADEL,
                        answers=AnswerPolicy(
                            claims=2, demonstrations=2, demonstration_spread=1
                        ),
                        claim=catalog.RatingClaim(band=catalog.BAND_ESTABLISHED),
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(RuntimeError, match="spread belongs to the cohort"):
        catalog._refuse_an_impossible_catalog()


# ---------------------------------------------------------------------------
# 4. The run: the screens, and the clocks that fail it
# ---------------------------------------------------------------------------


@pytest.fixture
async def a_seeded_world(session_factory):
    """The whole seed — both layers, on one now.

    Expensive on purpose. It is per test rather than per module because the
    database fixture under it is: each of the assertions below is about a *run*,
    and a run that had already been asserted over is a run whose search records
    and interest rows are not the ones the next assertion is about.
    """

    settings = get_settings()
    now = build_clock().now()
    async with session_factory() as session:
        accounts = await seed(session, clock=FixedClock(at=now), settings=settings)
        members = await seed_the_cohort(
            session, clock=FixedClock(at=now), settings=settings
        )
    # **The relationships are part of the world and not a layer above it.** Five
    # of the ten `LivenessSignal` codes are facts about a pair, so a world seeded
    # without them is one where the assertions below would be reading a fixture
    # nobody could have produced.
    pairs = await write_the_relationships(
        session_factory, settings=settings, now=now
    )
    return {
        "accounts": accounts,
        "members": members,
        "now": now,
        "pairs": pairs,
    }


async def test_the_cohort_reaches_every_screen_it_promises(
    session_factory, a_seeded_world
):
    """The assertions, run as the protagonist. **This is the acceptance test.**

    Every line here is an outcome of a real read path — the pool search, the
    deal, the line-up, the ladder and the three named states — and not one of
    them is a number the generator chose. What is asserted about the *lines* is
    only that each surface reported: the surfaces themselves refuse by raising,
    which is the whole design of `screens.py`.
    """

    lines = await assert_the_screens(
        session_factory,
        settings=get_settings(),
        now=a_seeded_world["now"],
        pairs=a_seeded_world["pairs"],
    )
    text = "\n".join(lines)

    for surface in (
        "pool ·",
        "gender gate ·",
        "newcomer window ·",
        "reason lines ·",
        "deck ·",
        "court ·",
        "ladder ·",
        "proposals opt-out ·",
        "interest ·",
        "mutual ·",
        "outstanding ·",
        "decline ·",
        "absences ·",
        "block ·",
        "pass ·",
        "newcomer gate ·",
        "one sport ·",
        "blank week ·",
    ):
        assert surface in text, f"nothing was read for {surface}"


async def test_the_band_histogram_is_met_by_the_engine_that_ships(
    session_factory, a_seeded_world
):
    """The archetypes choose answers and the engine chooses bands.

    That is what keeps the claim a real check rather than the generator grading
    its own work — so this is the assertion that goes red on an engine retune.
    """

    async with session_factory() as session:
        await refuse_a_histogram_that_has_moved(session, a_seeded_world["members"])


async def test_a_band_that_has_emptied_fails_the_seed_by_name(
    session_factory, a_seeded_world, monkeypatch
):
    """Simulated from the other side — the claim is moved rather than the engine.

    The two are the same disagreement and only one of them can be written in a
    test, which is exactly how `_refuse_a_name_that_lies` is driven one layer up.
    """

    monkeypatch.setattr(
        "app.seeds.runner.BAND_HISTOGRAM", {**BAND_HISTOGRAM, "Advanced": (400, 500)}
    )

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="Advanced: .*promises 400–500"):
            await refuse_a_histogram_that_has_moved(session, a_seeded_world["members"])


async def test_an_aged_out_cohort_fails_by_name_with_its_age_in_days(session_factory):
    """**The calendar.** A fortnight on, every seeded newcomer ages out at once.

    Driven by writing the cohort on a clock a fortnight in the past, which is
    what a database seeded a fortnight ago *is* — rather than by moving the
    window, which would be testing the assertion against itself.

    One member, because the refusal is about the calendar and not about the
    population: paying for forty questionnaires to watch a date go stale would be
    buying nothing this does not already show.
    """

    now = build_clock().now()
    stale = generate().members[0]
    cohort = Cohort(
        seed=0, members=(replace(stale, committed_days_ago=1, handle="cohort-x-00"),)
    )

    async with session_factory() as session:
        members = await seed_the_cohort(
            session,
            cohort=cohort,
            clock=days_before(now, NEWCOMER_WINDOW_DAYS + 6),
            settings=get_settings(),
        )
        with pytest.raises(SeedFailed) as refused:
            await refuse_a_cohort_that_has_aged_out(session, members, now=now)

    complaint = str(refused.value)
    assert "cohort-x-00" in complaint, "the refusal does not name the member"
    assert f"{NEWCOMER_WINDOW_DAYS + 7} days" in complaint, complaint
    assert "make seed" in complaint, "the refusal does not say how to fix it"


async def test_a_cohort_with_no_newcomer_declared_is_refused(session_factory):
    """A gate with one side present cannot be seen at all."""

    now = build_clock().now()
    settled = replace(
        generate().members[0], committed_days_ago=60, handle="cohort-x-01"
    )

    async with session_factory() as session:
        members = await seed_the_cohort(
            session,
            cohort=Cohort(seed=0, members=(settled,)),
            clock=FixedClock(at=now),
            settings=get_settings(),
        )
        with pytest.raises(SeedFailed, match="declares no newcomer"):
            await refuse_a_cohort_that_has_aged_out(session, members, now=now)


async def test_backdated_events_are_not_monotonic_with_the_log(
    session_factory, a_seeded_world
):
    """The one demand the injected clock creates, stated where it can fail.

    A settled member and a newcomer are the same code on two clocks, so the log
    is appended in run order while the instants inside it walk backwards and
    forwards. Nothing downstream may order on `occurred_at` and expect the log's
    order — and this is what says so, rather than a comment nobody runs.
    """

    async with session_factory() as session:
        rows = await session.execute(
            select(EventStoreORM.occurred_at).order_by(EventStoreORM.sequence_no)
        )
        instants = [row[0] for row in rows.all()]

    assert instants, "the run appended nothing"
    assert instants != sorted(instants), (
        "every backdated event landed in calendar order, which means the run is "
        "no longer writing the cohort on its own clocks"
    )


def test_the_report_says_the_cohort_stands_for_nothing(a_seeded_world):
    """Said on the report and not only in a docstring.

    The ruleset-diff corpus prints its own disclaimer for the same reason: a
    fixture that stands for nothing outside itself has to say so where somebody
    reading its output will see it, or the numbers get quoted.
    """
    from app.seeds.runner import SeedReport

    text = "\n".join(
        report(
            SeedReport(
                accounts=a_seeded_world["accounts"],
                members=a_seeded_world["members"],
                now=a_seeded_world["now"],
                screens=("pool · read",),
            )
        )
    )

    assert COHORT_DISCLAIMER in text
    assert "ruleset-diff" in text
    assert THE_POPULATED_PLAYER.email in text
    assert THE_BLANK_WEEK_PLAYER.email in text
    assert "ring a:" in text
    assert "pool · read" in text


def test_every_unreachable_reason_line_carries_its_reason():
    """A list of measured absences and not a list of exceptions.

    Each entry says *why* it cannot be drawn, and the assertion in `screens.py`
    checks the same code really is absent from the run — so the day a provider
    lands, the run goes red and demands the code move to the promised side.
    """

    assert CANNOT_BE_DRAWN
    for code, because in CANNOT_BE_DRAWN.items():
        assert len(because) > 20, f"{code} is excluded without a reason"
