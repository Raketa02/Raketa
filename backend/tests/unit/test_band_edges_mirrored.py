"""The effective band edges, pinned because a client derives them again.

``band_for`` assigns a Level to the *higher* Band from halfway across the gap
between printed bands, so the boundaries a player is really banded at are
1,55 · 2,65 · 3,85 and not the printed 1,6 · 2,7 · 3,9. The player app's level
bar needs contiguous drawing boundaries — the bar must have no gaps, which is a
rendering requirement with no meaning in the model — and its own arithmetic
arrives at the same three numbers. Neither side copied the other and neither has
a reason to look at the other.

That is the whole risk: retuning ``BAND_EDGE_TOLERANCE`` moves the Band the
response *names* without moving the segment the coral mark is *drawn* in, so for
Levels inside a gap the picture and the word would disagree — quietly, and only
for the players who land there. The two apps cannot import each other, so a pair
of mirrored assertions is the only mechanism available: this file is the half
that fires here, and the player app carries the other.

The numbers stay client-owned, deliberately. The wire carries what the engine
concluded — a Band and its printed boundaries — and never how to draw it; the
two clients do not share a shape, so drawing geometry served from here is a
decision one of them would have to undo.
"""

from app.engines.racketskill.core import (
    BAND_EDGE_TOLERANCE,
    SCALE_MAX,
    SCALE_MIN,
    Band,
    band_for,
)

#: Where the failure has to be repaired. Named in every assertion below, because
#: a pin whose message does not say what else moves is a pin the next person
#: re-baselines in isolation — which is exactly the drift it exists to prevent.
MIRRORED_IN_THE_PLAYER_APP = (
    "These three numbers are also written in frontend_player/src/shared/ui/"
    "theme.ts, as the `band` map's lo/hi level-bar drawing boundaries, where they "
    "are derived independently and where a mirrored assertion of this one lives. "
    "A retune of BAND_EDGE_TOLERANCE has to move both sides in the same change, "
    "or the coral mark starts landing in a segment the response does not name."
)

#: The edges a Level is really banded at: each printed band's lower bound, less
#: the tolerance ``band_for`` applies, rounded the way ``band_for`` rounds it.
#: Derived from the Band definition and the tolerance rather than typed in, so
#: this is the *definition* of an effective edge and the assertion below is the
#: pin a retune has to walk past.
EFFECTIVE_BAND_EDGES = tuple(
    round(band.lower - BAND_EDGE_TOLERANCE, 2)
    for band in (Band.DEVELOPING, Band.ESTABLISHED, Band.ADVANCED)
)


def test_the_effective_band_edges_are_what_the_level_bar_draws() -> None:
    assert EFFECTIVE_BAND_EDGES == (1.55, 2.65, 3.85), MIRRORED_IN_THE_PLAYER_APP


def test_a_level_on_an_effective_edge_is_banded_above_it() -> None:
    """The derivation is only worth pinning if it is what ``band_for`` does.

    Asserted on either side of each edge rather than by reading the constant
    back, so what is pinned is the *boundary* and not the spelling of the
    arithmetic that produced it.
    """

    lower_bands = (Band.NEW, Band.DEVELOPING, Band.ESTABLISHED)
    higher_bands = (Band.DEVELOPING, Band.ESTABLISHED, Band.ADVANCED)

    for edge, lower, higher in zip(
        EFFECTIVE_BAND_EDGES, lower_bands, higher_bands, strict=True
    ):
        assert band_for(edge) is higher, MIRRORED_IN_THE_PLAYER_APP
        # A Level is carried to two decimals, so one hundredth below an edge is
        # the last Level that exists on the other side of it.
        assert band_for(round(edge - 0.01, 2)) is lower, MIRRORED_IN_THE_PLAYER_APP


def test_the_effective_edges_partition_the_whole_scale() -> None:
    """No gaps and no overlaps — the property the bar is drawn from.

    The printed bands leave gaps (1,5 → 1,6) and a bar drawn from *those* would
    have three of them. These edges are what close them, so a client can cut the
    scale at exactly these three points and cover it once.
    """

    edges = EFFECTIVE_BAND_EDGES
    assert SCALE_MIN < edges[0], MIRRORED_IN_THE_PLAYER_APP
    assert edges[-1] < SCALE_MAX, MIRRORED_IN_THE_PLAYER_APP
    assert list(edges) == sorted(set(edges)), MIRRORED_IN_THE_PLAYER_APP

    # Every hundredth of the scale falls in exactly one segment, and the segment
    # it falls in is the Band the response would name for it.
    boundaries = (SCALE_MIN, *edges, SCALE_MAX)
    for index, band in enumerate(Band):
        low, high = boundaries[index], boundaries[index + 1]
        hundredths = range(int(round(low * 100)), int(round(high * 100)))
        for value in hundredths:
            level = round(value / 100.0, 2)
            assert band_for(level) is band, (
                f"{level} draws in {band.label} but bands as "
                f"{band_for(level).label}. {MIRRORED_IN_THE_PLAYER_APP}"
            )
