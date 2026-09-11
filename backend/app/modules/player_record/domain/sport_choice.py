"""Which sport the sheet is about. **The one rule this context owns.**

Every other figure on a record arrives from the context that owns it, already
decided; this is a question about the *reader* rather than about the subject, so
nobody else could answer it. It decides what the sheet is **about** and never who
may be seen — the four fail-closed gates run in the partition of the disclosure,
which is a fact the platform holds, and the sport asked for is a fact the client
sends (``docs/adr/0159``).

**Registry order is structural here, not remembered.** Both functions walk
``Sport`` and look the mapping up, rather than iterating the mapping and sorting
afterwards. That is the difference between an order somebody has to keep applying
and one there is no way to get wrong: an unordered ``max`` over a mapping is
exactly the set-iteration non-determinism ``docs/adr/0105`` exists about, and a
header printing padel on one read and squash on the next would be its most
visible possible instance.
"""

from __future__ import annotations

from typing import Mapping

from app.kernel import Sport
from app.modules.player_record.domain.record import SportPill, SubjectRating


def sport_to_print(
    arrived_from: Sport | None, rated: Mapping[Sport, SubjectRating]
) -> Sport | None:
    """The sport whose Level the header prints and whose panel is drawn.

    Three answers:

    **The sport asked for**, where they hold a rating in it — the overwhelming
    case, and the whole reason the parameter exists.

    **Otherwise their most counted.** *Most counted games*, and deliberately not
    two other things it could have been: a fallback on the highest **Level**
    would make the header a boast about a sport nobody asked about, and a
    fallback on the most **recent** would be activity recency wearing a sport's
    name — which this product refuses in every shape.

    The number it compares is the one the panel prints, which is
    ``SubjectRating.counted_games`` — *results that have moved this Level* rather
    than *games they have played*. One number, one meaning, and the sheet cannot
    fall back on a count it does not then show. It follows that a newcomer rated
    in two sports and tested by no game is **entirely** decided by the tie-break
    below, which is the case that makes the tie-break ordinary rather than exotic.

    **``None``** where they are rated in nothing. An ordinary state during
    onboarding rather than an error: the header draws the poster with no Level on
    it and the skill card is simply absent.
    """

    if arrived_from is not None and arrived_from in rated:
        return arrived_from
    most_counted: SubjectRating | None = None
    for sport in Sport:
        rating = rated.get(sport)
        if rating is None:
            continue
        # **Strictly greater**, so the first sport in the registry's order wins a
        # tie. The tie is the ordinary case rather than the exotic one: two
        # sports and nothing counted in either is what every newcomer holds.
        if most_counted is None or rating.counted_games > most_counted.counted_games:
            most_counted = rating
    return None if most_counted is None else most_counted.sport


def pills_of(rated: Mapping[Sport, SubjectRating]) -> tuple[SportPill, ...]:
    """One pill per rated sport, in the registry's own order.

    **Narrower than what it is drawn from**: a pill answers *what else do they
    play*, and the certainty and the counted-games count belong to the one sport
    the sheet is about rather than to all four.
    """

    return tuple(
        SportPill(sport=sport, level=rating.level, band=rating.band)
        for sport in Sport
        if (rating := rated.get(sport)) is not None
    )


__all__ = ["pills_of", "sport_to_print"]
