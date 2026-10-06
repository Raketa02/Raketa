"""The level window and the newcomer window — what the new games kept (#579).

The searches' gates and the newcomer path went with the searches; what the
proposer, the fill, a rescue and a post still ask is whether **two people** are
close enough to play, at the tolerance the forecast's curve uses, narrowed to
the competitive one while either of them is new (``docs/adr/0103``,
``docs/adr/0113``). Asserted here at the seam they call, rather than through a
gate roster that no longer exists.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit import ruleset as ruleset_module
from app.engines.matchfit.core import SearchMode
from app.modules.matchmaking.domain.level_window import (
    NEWCOMER_WINDOW,
    is_new_at,
    level_close_enough,
    level_tolerance,
)
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.presentation.schemas import (
    CommitPlayerProfileRequest,
)

NOW = datetime(2026, 10, 6, 18, 0, tzinfo=timezone.utc)
#: A profile long out of its newcomer window.
SETTLED = NOW - timedelta(days=90)
#: A profile committed two days ago — inside the window with twelve to run.
NEWLY = NOW - NEWCOMER_WINDOW + timedelta(days=2)


def _tolerance(mode: SearchMode) -> float:
    return LIVE_RULESET.modes[mode].level_tolerance


#: A gap outside the competitive window and inside the for-fun one.
BETWEEN = (_tolerance(SearchMode.COMPETITIVE) + _tolerance(SearchMode.FOR_FUN)) / 2


def _close(
    gap: float,
    *,
    mode: SearchMode,
    a_created_at: datetime = SETTLED,
    b_created_at: datetime = SETTLED,
) -> bool:
    return level_close_enough(
        mu_a=2.80,
        mu_b=2.80 + gap,
        a_created_at=a_created_at,
        b_created_at=b_created_at,
        mode=mode,
        ruleset=LIVE_RULESET,
        now=NOW,
    )


def test_the_window_reads_the_tolerance_the_curve_uses():
    """``Δμ < LEVEL_TOL_mode``, and the two numbers are the same number — so the
    window and the curve cannot drift apart."""

    tolerance = _tolerance(SearchMode.COMPETITIVE)

    assert _close(tolerance - 0.01, mode=SearchMode.COMPETITIVE)
    assert not _close(tolerance + 0.01, mode=SearchMode.COMPETITIVE)


def test_for_fun_reads_its_own_wider_tolerance():
    assert not _close(BETWEEN, mode=SearchMode.COMPETITIVE)
    assert _close(BETWEEN, mode=SearchMode.FOR_FUN)


def test_newness_tightens_the_window_on_either_side_of_the_pair():
    """**Newness changes the window, never anything else**, and it binds the
    *pairing*: either side being new is enough, so the bad first game cannot
    arrive through the veteran's half of it."""

    assert _close(BETWEEN, mode=SearchMode.FOR_FUN), "inside for fun, or vacuous"
    assert not _close(BETWEEN, mode=SearchMode.FOR_FUN, a_created_at=NEWLY)
    assert not _close(BETWEEN, mode=SearchMode.FOR_FUN, b_created_at=NEWLY)


def test_the_tightening_introduces_no_constant():
    """*A first game is judged on the stricter of the two bars the product
    already has* — the competitive tolerance, exactly, and nothing new."""

    tolerance = level_tolerance(
        mode=SearchMode.FOR_FUN, ruleset=LIVE_RULESET, now=NOW, created_at=(NEWLY,)
    )

    assert tolerance == _tolerance(SearchMode.COMPETITIVE)
    assert level_tolerance(
        mode=SearchMode.FOR_FUN, ruleset=LIVE_RULESET, now=NOW, created_at=(SETTLED,)
    ) == _tolerance(SearchMode.FOR_FUN)


def test_the_newcomer_window_is_a_date_of_fourteen_days():
    """A date, never a flag: *new* is computed where it is read, from when the
    profile was committed, and the window's edge is exclusive."""

    assert NEWCOMER_WINDOW == timedelta(days=14)
    assert is_new_at(NOW - NEWCOMER_WINDOW + timedelta(seconds=1), NOW)
    assert not is_new_at(NOW - NEWCOMER_WINDOW, NOW)


#: What a *no beginners* switch would have to be spelled with. A blocklist over
#: names rather than a positive enumeration, because the claim is about a field
#: that does not exist and there is nothing positive to enumerate.
REFUSAL_STEMS = ("newcomer", "beginner", "novice", "experienc", "counted_games")

#: The one name on that list that is allowed: it **bounds an ask** of the
#: ranking, and withholds nobody (``docs/adr/0114``).
ALLOWED = {"newcomer_absorption_cap"}


def _ruleset_field_names() -> set[str]:
    """Every field of every released-ruleset shape, walked rather than listed."""

    held = [getattr(ruleset_module, name) for name in dir(ruleset_module)]
    shapes = [one for one in held if isinstance(one, type) and is_dataclass(one)]
    return {field.name for shape in shapes for field in fields(shape)}


@pytest.mark.parametrize(
    "names",
    [
        pytest.param({field.name for field in fields(PlayerProfile)}, id="the-profile"),
        pytest.param(set(CommitPlayerProfileRequest.model_fields), id="the-commit"),
        pytest.param(_ruleset_field_names(), id="the-ruleset"),
    ],
)
def test_no_no_beginners_switch_exists(names: set[str]) -> None:
    """**There is no setting that declines newcomers** (``docs/adr/0114``). It
    cannot be mutual — a newcomer declining veterans is incoherent — so it could
    only be the one-directional preference over people ``docs/adr/0096`` refused
    by name."""

    offending = {
        name
        for name in names - ALLOWED
        if any(stem in name.lower() for stem in REFUSAL_STEMS)
    }

    assert not offending
