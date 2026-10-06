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
from uuid import UUID

import pytest
from sqlalchemy import select

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.engines.assessment import AnswerOption, Question
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import SPORT_SPECS, Sport
from app.modules.matchmaking.domain.searches import LAST_FIVE
from app.modules.player_profile.domain.intro import Intro
from app.seeds import catalog
from app.seeds.catalog import (
    PROTAGONISTS,
    REFERENCE_CENTRE,
    SEED_CENTRE_VARIABLE,
    Centre,
    seed_centre,
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
    EVERY_PLAYED_GAME,
    INTROS,
    PLAYED_GAMES,
    RINGS,
    WHAT_PLAYERS_SAID,
    Cohort,
    _distance_between,
    _distance_of,
    _ring_in,
    as_document,
    generate,
    latitude_of,
)
from app.modules.matchmaking.domain.geography import Point, distance_km
from app.seeds.booked_history import write_her_history
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.games import write_the_played_history
from app.seeds.payments import write_the_payment_methods
from app.seeds.pairs import write_the_relationships
from app.seeds.photos import DeclaredVerdict
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
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

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


def test_the_played_history_records_no_answer_the_platform_gave():
    """**Who played whom and who won**, and nothing the platform makes of it.

    The same rule the members are held to, one section along: a Player Score, a
    counted-game count or a run of form written here would be a committed copy of
    a fold over the events this file's own rows produce — and the copy is what
    would get believed, because it is the one a reader can see.
    """

    document = as_document(generate())
    played = document["played_games"]
    assert played, "the artifact records no played game at all"
    assert "protagonist_games" not in document, "her evenings are booked games now"

    for game in played:
        assert set(game) == {
            "sport",
            "played_days_ago",
            "side_a",
            "side_b",
            "won_by",
            "entered",
            "answered",
        }, game


def test_no_declared_pair_plays_twice():
    """**One open challenge per pair, and nothing ends one every seat accepted.**

    So a pair that has played can never be sent a second court — the platform
    refuses the send, half way through a run that has already written games. The
    generator's own refusal catches it at import; this is the claim stated where
    somebody adding a row will read it.
    """

    pairs = [pair for game in PLAYED_GAMES for pair in game.pairs]

    assert len(pairs) == len(set(pairs)), "a pair shares two courts"


def test_the_protagonist_plays_in_none_of_the_cohorts_own():
    """**Two lists, and the split is the claim.** `PLAYED_GAMES` exists so the
    cards *in* her pool reach every state a card can be in, and a row of it that
    seated her would be answering a second question in the same table.

    Her own evenings are past booked games, declared and checked in
    `app/seeds/booked_history.py`."""

    played = {handle for game in PLAYED_GAMES for handle in game.players}

    assert all(handle.startswith("cohort-") for handle in played), played


def test_nobody_is_rated_by_somebody_they_never_played():
    """A card is drawn for an evening, and a **ghost** is not one: there is
    nobody to rate for a game the platform says did not happen."""

    together: dict[str, set[str]] = {}
    for game in EVERY_PLAYED_GAME:
        if game.was_a_ghost:
            continue
        for pair in game.pairs:
            one, other = sorted(pair)
            together.setdefault(one, set()).add(other)
            together.setdefault(other, set()).add(one)

    assert WHAT_PLAYERS_SAID, "nobody says anything about anybody"
    for subject, said in WHAT_PLAYERS_SAID.items():
        for rater in said:
            assert rater in together.get(subject, set()), (rater, subject)


def test_somebody_is_rated_by_nobody():
    """**The absence is the state most players are in**, and the record omits
    the zone rather than publishing a nought. A fixture where everybody has been
    rated cannot draw it."""

    rated = set(WHAT_PLAYERS_SAID)
    played_by_somebody = {
        handle
        for game in EVERY_PLAYED_GAME
        if not game.was_a_ghost
        for handle in game.players
    }

    assert played_by_somebody - rated, "everybody who played has been rated"


def test_a_court_seats_what_its_sport_seats():
    """A line-up completes only when **every** seat is accepted, so a padel court
    one short of four opens no game at all."""

    for game in PLAYED_GAMES:
        per_side = SPORT_SPECS[Sport(game.sport)].players // 2
        assert len(game.side_a) == per_side, game
        assert len(game.side_b) == per_side, game


def test_one_declared_game_is_left_with_no_agreed_score():
    """*An evening, not evidence.* It counts toward how much these people have
    played and produces an outcome for nobody, which is the one card state a
    fixture of tidy games could not reach."""

    unscored = [game for game in PLAYED_GAMES if not game.was_scored]

    assert len(unscored) == 1, [game.won_by for game in PLAYED_GAMES]


def test_the_declared_winners_are_not_all_one_side():
    """*Last 5* is win or loss, and five identical squares is a row nobody can
    read a mistake off."""

    won = {game.won_by for game in PLAYED_GAMES if game.was_scored}

    assert won == {"A", "B"}, won


def test_somebody_plays_enough_games_to_fill_the_run_of_form():
    """**Five distinct opponents**, because that is what five counted games costs
    when a pair can only ever share one court."""

    counted: dict[str, int] = {}
    for game in PLAYED_GAMES:
        for handle in game.players:
            counted[handle] = counted.get(handle, 0) + 1

    assert max(counted.values()) >= LAST_FIVE, counted
    assert any(1 <= played < LAST_FIVE for played in counted.values()), counted
    assert len(counted) < len(COHORT.members), "every member has played"


def test_everybody_who_played_a_sport_holds_a_rating_in_it():
    """The questionnaire is the only door to a Level, so the declaration has to
    reach the draw — otherwise the game would be written against a member the
    level gate removes from their own opponent's search."""

    for game in PLAYED_GAMES:
        for handle in game.players:
            member = COHORT.by_handle(handle)
            assert Sport(game.sport) in member.sports, (handle, game.sport)


def test_an_organiser_sees_no_further_than_the_people_they_play():
    """A search hands back at most `shortlist_max` rows, so an organiser
    searching wide fills that list with people this fixture never declared — and
    the declared opponent falls off the end of it."""

    organisers = {game.organiser for game in PLAYED_GAMES}

    for member in COHORT.members:
        if member.handle not in organisers:
            continue
        rings = {
            _ring_in(handle)
            for game in PLAYED_GAMES
            if game.organiser == member.handle
            for handle in game.players[1:]
        }
        furthest = max(
            _distance_between(_ring_in(member.handle), ring) for ring in rings
        )
        assert member.radius_km >= furthest, member.handle
        assert member.radius_km - 1 < furthest or furthest == 0, (
            f"'{member.handle}' searches {member.radius_km} km to reach "
            f"{furthest:.2f} km — wider than the opponents it was given"
        )


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
# 1b. The centre: the artifact's is fixed, the run's may move
# ---------------------------------------------------------------------------


def test_the_artifact_is_drawn_around_the_reference_whatever_the_shell_says():
    """`generate()` defaults to London. **The shell cannot move the artifact.**

    A developer who has exported `SEED_CENTRE` for `make seed-host` then runs
    `make gen-cohort` or this suite, and neither may notice: the committed
    population measures from the reference, and only the drawn `COHORT` — the
    run's — is translated. Two centres, one of them fixed, or the artifact test
    above would be a function of whoever last ran it.
    """

    assert REFERENCE_CENTRE == Centre(latitude=51.51, longitude=-0.13)
    assert generate().centre == REFERENCE_CENTRE
    assert as_document(generate())["centre"] == {
        "latitude": 51.51,
        "longitude": -0.13,
    }


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, REFERENCE_CENTRE),
        ("", REFERENCE_CENTRE),
        ("   ", REFERENCE_CENTRE),
        ("50.06,19.94", Centre(latitude=50.06, longitude=19.94)),
        # Whitespace, and a phone's full-precision fix rounds to the cell — the
        # same rounding the profile commit does on the way in.
        (" 50.0614 , 19.9372 ", Centre(latitude=50.06, longitude=19.94)),
        ("-33.87,151.21", Centre(latitude=-33.87, longitude=151.21)),
        ("51.51,-0.13", REFERENCE_CENTRE),
    ],
)
def test_the_centre_is_parsed_from_the_environment(raw, expected):
    """A pure function of the record, exhaustively (`docs/environments.md`)."""

    environ = {} if raw is None else {SEED_CENTRE_VARIABLE: raw}

    assert seed_centre(environ) == expected


@pytest.mark.parametrize(
    "raw, complaint",
    [
        ("50.06", "latitude,longitude"),
        ("50.06,19.94,7", "latitude,longitude"),
        ("Kraków", "latitude,longitude"),
        ("50.06;19.94", "latitude,longitude"),
        ("91,19.94", "off the globe"),
        ("50.06,181", "off the globe"),
    ],
)
def test_a_centre_that_is_not_a_place_is_refused_by_name(raw, complaint):
    with pytest.raises(ValueError, match=complaint):
        seed_centre({SEED_CENTRE_VARIABLE: raw})


def test_a_moved_cohort_is_the_same_figure_somewhere_else():
    """**Translation, not regeneration.** Every member keeps their handle, ring
    and draws, sits on the new centre's meridian, and is exactly as far from the
    new centre as they were from the old one — because a degree of latitude is
    the same length everywhere, which is the fact the rings are built on. This
    is what lets a developer in Kraków seed around their own phone without a
    single distance in the ring table, the walkthroughs or the assertions
    changing underneath them.
    """

    krakow = Centre(latitude=50.06, longitude=19.94)
    reference, moved = generate(), generate(centre=krakow)

    assert moved.centre == krakow
    assert len(moved.members) == len(reference.members)
    for there, here in zip(moved.members, reference.members, strict=True):
        assert (there.handle, there.ring, there.archetype) == (
            here.handle,
            here.ring,
            here.archetype,
        )
        assert there.longitude == krakow.longitude
        assert there.latitude == round(
            here.latitude + (krakow.latitude - REFERENCE_CENTRE.latitude), 2
        )
        # Everything but the position is the same draw.
        assert replace(there, latitude=0.0, longitude=0.0) == replace(
            here, latitude=0.0, longitude=0.0
        )
        was = distance_km(
            Point(
                latitude=REFERENCE_CENTRE.latitude,
                longitude=REFERENCE_CENTRE.longitude,
            ),
            Point(latitude=here.latitude, longitude=here.longitude),
        )
        now = distance_km(
            Point(latitude=krakow.latitude, longitude=krakow.longitude),
            Point(latitude=there.latitude, longitude=there.longitude),
        )
        assert now == pytest.approx(was, abs=0.01), there.handle


def test_every_ring_lands_on_a_cell_wherever_the_centre_is():
    """`LocationArea` rounds to two decimal places on the way in. A ring that
    rounds to a different cell than the one it was placed on is a ring that
    moved between the seed and the database, so the offsets and the centre are
    both two-decimal and their sum is put back on the grid."""

    for centre in (REFERENCE_CENTRE, Centre(latitude=50.06, longitude=19.94)):
        for ring in RINGS:
            latitude = latitude_of(ring, centre)
            assert latitude == round(latitude, 2), (ring.code, centre)
            assert _distance_of(ring) == pytest.approx(
                distance_km(
                    Point(latitude=centre.latitude, longitude=centre.longitude),
                    Point(latitude=latitude, longitude=centre.longitude),
                ),
                abs=0.01,
            )


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


def test_three_members_carry_a_photograph_and_it_is_one_of_each_verdict():
    """**Three carriers and three answers**, and the third is an absence.

    A shield says *checked and passed*; its absence has two causes — the check
    flagged the photograph, and nothing ever looked at it — and they are
    indistinguishable on the wire (`docs/adr/0138`). So a fixture holding one of
    them proves nothing about the other, and a rate that happened to draw two of
    three would say nothing about which two.
    """

    carried = {
        member.handle: member.declared_verdict
        for member in COHORT.members
        if member.photograph is not None
    }

    assert len(carried) == len(DeclaredVerdict), carried
    assert set(carried.values()) == set(DeclaredVerdict), carried


def test_a_few_members_wrote_a_line_and_most_did_not():
    """**Both cards are drawn** (`docs/adr/0170`): the mocks put a line on every
    card and most players will have none, so the deck has to show a card that
    quotes one beside a card that closes up. Every carrier is in the nearest
    ring, where the protagonist's pool is, so the line reaches a card."""

    carriers = {
        member.handle: member.intro
        for member in COHORT.members
        if member.intro is not None
    }

    assert carriers == dict(INTROS)
    assert 0 < len(carriers) < len(COHORT.members) // 2, carriers
    assert all(_ring_in(handle) == RINGS[0].code for handle in carriers), carriers
    assert any(
        COHORT.by_handle(handle).photograph is not None for handle in carriers
    ), "no card carries a photograph and a line together"


def test_every_seeded_line_is_one_the_platform_admits():
    """The fence the commit runs, run at import: a seeded line carrying contact
    or over the cap would fail `make seed` at the first profile, and this says
    so before a database is touched. The protagonist's line goes through the
    same check."""

    lines = list(INTROS.values()) + [
        account.profile.intro
        for account in PROTAGONISTS
        if account.profile is not None and account.profile.intro is not None
    ]

    assert lines, "nothing to check would be a check that passes for nothing"
    for line in lines:
        admitted = Intro.written(line)
        assert admitted is not None and admitted.text == line, line


def test_no_named_account_carries_a_photograph():
    """The catalog's own answer is unchanged, and it is still a declaration.

    A card renders the generated court poster without a photograph, which is the
    state most cards are in and the one worth developing against — so the
    photographs are the cohort's, where a card can be compared against the ones
    beside it, and never a protagonist's.
    """

    for account in PROTAGONISTS:
        assert account.profile is not None and account.profile.photo_ids == ()


def test_a_member_with_no_photograph_commits_none():
    """`photo_ids` is what the **upload** minted, and most members have no upload.

    The id cannot be a field on the member's row — it is minted by the write path
    — so the profile the run commits carries whatever this run uploaded, which
    for the great majority is nothing at all.
    """

    from app.seeds.runner import _profile_of

    for member in COHORT.members:
        assert _profile_of(member).photo_ids == ()
    assert _profile_of(COHORT.members[0], (UUID(int=1),)).photo_ids == (UUID(int=1),)


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
    # **One store for the whole world**, because the commit re-validates every
    # photo id through the same port the upload wrote it to — two stores would be
    # two answers to *does this player really have this photograph*. In memory,
    # so **no test in this suite needs MinIO running**, which is the acceptance
    # criterion `tests/conftest.py` states for the whole HTTP suite and not a
    # convenience.
    photos = InMemoryPhotoStorage()
    async with session_factory() as session:
        accounts = await seed(
            session, clock=FixedClock(at=now), settings=settings, photos=photos
        )
        members = await seed_the_cohort(
            session, clock=FixedClock(at=now), settings=settings, photos=photos
        )
    # **The played history is part of the world too**, and it comes before the
    # relationships for the reason `runner.run` puts it there: a game spends a
    # pair for good, and the inbox layer plans around the ones already gone.
    played = await write_the_played_history(
        session_factory, settings=settings, now=now, photos=photos
    )
    # **Her own evenings beside it**, as past booked games (#573) — so the cards,
    # the clubs and their courts they are booked through come first.
    await write_the_payment_methods(
        session_factory,
        now=now,
        cohort=[(member.member.handle, member.player_id) for member in members],
    )
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )
    await write_her_history(session_factory, settings=settings, now=now)
    # **The relationships are part of the world and not a layer above it.** Five
    # of the ten `LivenessSignal` codes are facts about a pair, so a world seeded
    # without them is one where the assertions below would be reading a fixture
    # nobody could have produced.
    pairs = await write_the_relationships(
        session_factory, settings=settings, now=now, photos=photos
    )
    return {
        "accounts": accounts,
        "members": members,
        "now": now,
        "pairs": pairs,
        "played": played,
        "photos": photos,
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
        photos=a_seeded_world["photos"],
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
        "radar ·",
        "record block ·",
        "run of form ·",
        "player score ·",
        "unscored ·",
        "familiarity ·",
        "photo verdict ·",
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
            photos=InMemoryPhotoStorage(),
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
            photos=InMemoryPhotoStorage(),
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
