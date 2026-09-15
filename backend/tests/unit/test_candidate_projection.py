"""The fold from one stored event to what it moves in the index.

**Pure, and a function of the event alone.** Every contract the index consumes
carries its whole new value rather than a delta — a tag list, a grid, an area, a
Level — so nothing here needs the row it is about to move, and that is what makes
``rebuild == tail`` a property of the shape rather than a thing to hope for. A
projection that had to read the row it was updating would be one whose answer
depended on the order two readers happened to run in.

The list of what is consumed is asserted as a whole, in both directions: a
contract the index reads that nothing here projects is a column that silently
stops moving, and an event this projects that the spec's table does not name is a
fact in the index nobody agreed to hold.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)
from app.modules.matchmaking.domain.candidate_projection import (
    CandidateRowMoved,
    PlayerFactsMoved,
    PROJECTED_CONTRACTS,
    project,
)
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    GenderChanged,
    GenderPreferenceChanged,
    IntroWritten,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.rating.domain.events import (
    AssessmentCompleted,
    RatingInitialised,
)

WHEN = datetime(2026, 8, 27, 9, 30, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 27, 11, 0, tzinfo=timezone.utc)
PLAYER = UUID("11111111-1111-1111-1111-111111111111")


def _created(**overrides: object) -> PlayerProfileCreated:
    fields: dict[str, object] = {
        "player_id": PLAYER,
        "social_tags": ("competitive_edge",),
        "photo_ids": ("a-photo",),
        "availability": ("1:MORNING",),
        "latitude": 52.23,
        "longitude": 21.01,
        "search_radius_km": 12,
        "idempotency_key": "key",
        "occurred_at": WHEN,
        "gender": "FEMALE",
        "gender_preference": "ANY",
    }
    fields.update(overrides)
    return PlayerProfileCreated(**fields)  # type: ignore[arg-type]


def _rating(**overrides: object) -> RatingInitialised:
    fields: dict[str, object] = {
        "rating_id": uuid4(),
        "player_id": PLAYER,
        "sport": "PADEL",
        "mu": 2.71,
        "sigma": 0.34,
        "confidence": 62,
        "range_low": 2.4,
        "range_high": 3.0,
        "band_name": "Improver",
        "band_lower": 2.5,
        "band_upper": 3.0,
        "status": "INITIAL_ESTIMATE",
        "engine_version": "v3",
        "source_assessment_id": uuid4(),
        "occurred_at": WHEN,
        "calibration_priority": "STANDARD",
    }
    fields.update(overrides)
    return RatingInitialised(**fields)  # type: ignore[arg-type]


def _only(event: object) -> PlayerFactsMoved | CandidateRowMoved:
    moved = project(event)  # type: ignore[arg-type]
    assert len(moved) == 1, f"{type(event).__name__} moved {len(moved)} things"
    return moved[0]


# ---------------------------------------------------------------------------
# The creating commit
# ---------------------------------------------------------------------------


def test_the_creating_commit_moves_every_fact_it_carries() -> None:
    moved = _only(_created())
    assert moved == PlayerFactsMoved(
        player_id=PLAYER,
        changes={
            "profile_created_at": WHEN,
            "social_tags": ("competitive_edge",),
            "tags_updated_at": WHEN,
            "availability": ("1:MORNING",),
            "grid_updated_at": WHEN,
            "area_latitude": 52.23,
            "area_longitude": 21.01,
            "search_radius_km": 12,
            "gender": "FEMALE",
            "gender_preference": "ANY",
        },
    )


def test_the_creating_commit_carries_no_photo_into_the_index() -> None:
    """``docs/adr/0107``: the player card is assembled outside the engine.

    The event carries a photo list and the index refuses it — the one place the
    two disagree, and the reason this is asserted rather than left to the fence
    on the row.
    """

    assert "photo_ids" not in _only(_created()).changes


def test_a_profile_committed_before_the_gender_question_moves_a_stated_absence() -> (
    None
):
    """``None`` is *nobody was asked*, and it is not ``PREFER_NOT_TO_SAY``.

    It reaches the index as itself, because the alternative — leaving the column
    unmoved — would make a replayed row disagree with the stream it came from.
    """

    assert _only(_created(gender=None)).changes["gender"] is None


# ---------------------------------------------------------------------------
# The preference changes
# ---------------------------------------------------------------------------


def test_a_tag_change_moves_the_tags_and_says_when() -> None:
    moved = _only(SocialTagsChanged(PLAYER, ("social_first",), LATER))
    assert moved == PlayerFactsMoved(
        player_id=PLAYER,
        changes={"social_tags": ("social_first",), "tags_updated_at": LATER},
    )


def test_an_availability_change_moves_the_grid_and_says_when() -> None:
    moved = _only(AvailabilityChanged(PLAYER, ("3:EVENING",), LATER))
    assert moved == PlayerFactsMoved(
        player_id=PLAYER,
        changes={"availability": ("3:EVENING",), "grid_updated_at": LATER},
    )


def test_a_location_change_moves_the_coarse_area_and_nothing_finer() -> None:
    moved = _only(LocationChanged(PLAYER, 52.2297, 21.0122, LATER))
    assert moved == PlayerFactsMoved(
        player_id=PLAYER,
        changes={"area_latitude": 52.23, "area_longitude": 21.01},
    )


def test_a_radius_change_moves_the_radius() -> None:
    moved = _only(SearchRadiusChanged(PLAYER, 25, LATER))
    assert moved.changes == {"search_radius_km": 25}


def test_a_gender_change_moves_the_gender() -> None:
    assert _only(GenderChanged(PLAYER, "NON_BINARY", LATER)).changes == {
        "gender": "NON_BINARY"
    }


def test_a_gender_preference_change_moves_the_preference() -> None:
    assert _only(
        GenderPreferenceChanged(PLAYER, "SAME_GENDER_ONLY", LATER)
    ).changes == {"gender_preference": "SAME_GENDER_ONLY"}


def test_an_opt_in_answer_moves_the_opt_in() -> None:
    moved = _only(ProposalsOptInAnswered(PLAYER, True, "v1", "ONBOARDING", LATER))
    assert moved.changes == {"proposals_opt_in": True}


def test_a_written_intro_moves_the_line_and_nothing_else() -> None:
    """The one text fact in the index, projected like the tags — a fact a
    player changes about themselves (``docs/adr/0170`` §3) — and **without a
    moment beside it**: nothing reads when a line was written, and a stamp
    would be activity recency by another door."""

    moved = _only(IntroWritten(PLAYER, "Moved from Wrocław in May.", LATER))
    assert moved == PlayerFactsMoved(
        player_id=PLAYER, changes={"intro": "Moved from Wrocław in May."}
    )


# ---------------------------------------------------------------------------
# The per-sport facts
# ---------------------------------------------------------------------------


def test_a_rating_moves_the_row_for_that_sport_and_no_other() -> None:
    moved = _only(_rating())
    assert moved == CandidateRowMoved(
        player_id=PLAYER,
        sport="PADEL",
        changes={
            "mu": 2.71,
            "sigma": 0.34,
            "confidence": 62,
            "range_low": 2.4,
            "range_high": 3.0,
            "band": "Improver",
            "band_lower": 2.5,
            "band_upper": 3.0,
            "rating_status": "INITIAL_ESTIMATE",
            "calibration_priority": "STANDARD",
        },
    )


def test_a_declared_intent_moves_the_row_for_the_sport_it_names() -> None:
    moved = _only(
        PlayIntentDeclared(PLAYER, "TENNIS", "COMPETITIVE", "ONBOARDING", LATER)
    )
    assert moved == CandidateRowMoved(
        player_id=PLAYER, sport="TENNIS", changes={"declared_intent": "COMPETITIVE"}
    )


# ---------------------------------------------------------------------------
# Activity — the one fact read from another context's stream
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event",
    [
        RefreshTokenIssued(uuid4(), PLAYER, "jti", LATER, WHEN),
        RefreshTokenRotated(PLAYER, uuid4(), "old", uuid4(), "new", WHEN),
    ],
    ids=["issued", "rotated"],
)
def test_a_session_refresh_is_the_whole_of_the_activity_signal(
    event: object,
) -> None:
    """``docs/adr/0111``: ``last_active_at`` **means last session refresh.**

    Nothing in this repository records when a player opened the app, so the
    signal resolves days rather than hours — and it resolves days *because* these
    two events are the only ones that move it.
    """

    assert _only(event) == PlayerFactsMoved(
        player_id=PLAYER, changes={"last_active_at": WHEN}
    )


def test_a_revoked_token_is_not_activity() -> None:
    """Signing out is not a session refresh, and the two must not read alike."""

    assert project(RefreshTokenRevoked(uuid4(), PLAYER, "jti", "logout", WHEN)) == ()


# ---------------------------------------------------------------------------
# What is deliberately not consumed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event",
    [
        PhotosChanged(PLAYER, ("a", "b"), LATER),
        AssessmentCompleted(
            assessment_id=uuid4(),
            mu=2.7,
            sigma=0.3,
            confidence=60,
            range_low=2.4,
            range_high=3.0,
            band_name="Improver",
            band_lower=2.5,
            band_upper=3.0,
            status="INITIAL_ESTIMATE",
            questions_asked=9,
            engine_version="v3",
            occurred_at=WHEN,
        ),
    ],
    ids=["photos", "assessment-completed"],
)
def test_an_event_the_index_does_not_read_moves_nothing(event: object) -> None:
    """Silence rather than a shrug: an unknown contract is simply not projected.

    ``PhotosChanged`` is the deliberate one — ``docs/adr/0107`` assembles the
    player card outside the engine, so no photo fact reaches the index at all.
    """

    assert project(event) == ()  # type: ignore[arg-type]


def test_the_projected_contracts_are_exactly_what_projects_something() -> None:
    """The register and the dispatch check each other, in both directions.

    Two lists rather than one derived from the other, for the reason
    ``MATCHER_DEMANDS`` is not derived from ``FAIL_POSTURE``: forgetting to
    register a contract would otherwise be invisible instead of red.
    """

    declared = set(PROJECTED_CONTRACTS)
    assert declared == {
        PlayerProfileCreated,
        SocialTagsChanged,
        AvailabilityChanged,
        LocationChanged,
        SearchRadiusChanged,
        GenderChanged,
        GenderPreferenceChanged,
        IntroWritten,
        ProposalsOptInAnswered,
        PlayIntentDeclared,
        RatingInitialised,
        RefreshTokenIssued,
        RefreshTokenRotated,
    }


def test_the_activity_signal_resolves_days_because_the_token_lifetime_does() -> None:
    """The coupling ``docs/adr/0111`` named and had nothing to make loud.

    ``last_active_at`` means *last session refresh*, so its resolution **is**
    ``REFRESH_TOKEN_EXPIRE_SECONDS``. At a day, Liveness's activity dock reads
    *this week* … *dormant*; shorten the lifetime and the same column starts
    resolving hours, quietly changing what a ranking input measures — and there
    is nothing in ``auth`` that would know to say so. This is that missing
    sentence, as a red test.

    Read from the **declared default** rather than from the running settings:
    the suite deliberately shortens the lifetime, and what this asserts is the
    number the platform ships with.
    """

    from app.core.config import Settings

    lifetime = Settings.model_fields["REFRESH_TOKEN_EXPIRE_SECONDS"].default
    assert lifetime >= 86_400, (
        "the refresh-token lifetime has dropped below a day, so `last_active_at` "
        "no longer resolves days — Liveness's activity reading and the spec's "
        "*this week … dormant* wording both change with it"
    )
