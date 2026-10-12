"""The reliability filter's one clause — the part of #661 that is arithmetic
(``docs/adr/0195`` §6).

*Play only with players of at least High reliability* (or *at least Medium*):
somebody passes a minimum when their band is at or above it — read off the
engine's own floors, so the filter and the sheet cannot disagree about where
High starts — and **New passes every minimum**. The pair rule asks it both
ways; that is ``MatcherPlayerFit``'s, proven over HTTP.
"""

from __future__ import annotations

import pytest

from app.engines.matchfit.core import (
    RELIABILITY_MINIMUMS,
    ReliabilityBand,
    passes_reliability_minimum,
)

HIGH, MEDIUM = ReliabilityBand.HIGH, ReliabilityBand.MEDIUM


def test_a_filter_asks_for_at_least_medium_or_at_least_high_and_nothing_else():
    assert RELIABILITY_MINIMUMS == (MEDIUM, HIGH)


@pytest.mark.parametrize("band", list(ReliabilityBand))
def test_no_filter_lets_everybody_through(band):
    assert passes_reliability_minimum(None, band=band, is_new=False)


@pytest.mark.parametrize(
    ("minimum", "band", "passes"),
    [
        (HIGH, ReliabilityBand.VERY_HIGH, True),
        (HIGH, HIGH, True),
        # Sergio at 70: Medium, so Marta's *at least High* keeps him off.
        (HIGH, MEDIUM, False),
        (HIGH, ReliabilityBand.LOW, False),
        (MEDIUM, ReliabilityBand.VERY_HIGH, True),
        (MEDIUM, HIGH, True),
        (MEDIUM, MEDIUM, True),
        (MEDIUM, ReliabilityBand.LOW, False),
    ],
)
def test_a_band_passes_a_minimum_at_or_below_it(minimum, band, passes):
    assert passes_reliability_minimum(minimum, band=band, is_new=False) is passes


@pytest.mark.parametrize("minimum", RELIABILITY_MINIMUMS)
def test_new_passes_every_minimum_whatever_the_figure(minimum):
    """Nerea, New after two evenings she never came to — 50, Medium — is let
    through *at least High*: nobody is shut out before they've had a chance."""

    assert passes_reliability_minimum(minimum, band=ReliabilityBand.LOW, is_new=True)
