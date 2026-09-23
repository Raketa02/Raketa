"""Which sport the sheet is about — **the one rule this context owns.**

Everything else on a record arrives from the context that owns it, already
decided. This is the exception, and it is here rather than in ``rating`` because
it is a question about a *reader*: which sport did they arrive from, and what do
we print when the person they tapped does not play it.

Four answers, and the third is why this is a function rather than a
``dict.get``:

- **the sport asked for**, where they are rated in it — the overwhelming case;
- **otherwise their most counted** — not their highest Level, which would make
  the header a boast, and not their most recent, which would be activity recency
  wearing a sport's name;
- **a tie broken by the registry's own order**, never by a mapping's — an
  unordered ``max`` is exactly the set-iteration non-determinism
  ``docs/adr/0105`` exists about, and a header printing padel on one read and
  squash on the next would be the most visible possible instance of it;
- **nothing at all**, for somebody rated in no sport, which is an ordinary state
  during onboarding and not an error.

The registry order is asserted **against ``Sport`` itself** rather than against a
list spelled here, so a fifth sport added in the middle of that enum moves these
answers rather than quietly leaving a second order behind.
"""

from __future__ import annotations

from app.kernel import Sport
from app.modules.player_record.domain.record import LikelyRange, SubjectRating
from app.modules.player_record.domain.sport_choice import (
    pills_of,
    sport_to_print,
)


def a_rating(sport: Sport, *, counted: int = 0, level: float = 3.0) -> SubjectRating:
    return SubjectRating(
        sport=sport,
        level=level,
        band="Established",
        confidence=77,
        counted_games=counted,
        likely_range=LikelyRange(low=level - 0.3, high=level + 0.3),
    )


def rated(*ratings: SubjectRating) -> dict[Sport, SubjectRating]:
    return {one.sport: one for one in ratings}


def test_the_sport_asked_for_wins_when_they_are_rated_in_it():
    """The overwhelming case: you opened this from a padel four."""

    held = rated(a_rating(Sport.PADEL, counted=2), a_rating(Sport.SQUASH, counted=40))

    assert sport_to_print(Sport.PADEL, held) is Sport.PADEL


def test_a_sport_they_do_not_play_falls_back_to_their_most_counted():
    """Most **counted games**, and never the highest Level — a fallback on Level
    would make the header a boast about a sport nobody asked about."""

    held = rated(
        a_rating(Sport.PADEL, counted=3, level=4.6),
        a_rating(Sport.SQUASH, counted=19, level=2.1),
    )

    assert sport_to_print(Sport.TENNIS, held) is Sport.SQUASH


def test_a_tie_on_counted_games_breaks_on_the_registrys_own_order():
    """Two sports, nothing counted in either — the ordinary newcomer — and the
    answer is the same on every process and under every ``PYTHONHASHSEED``."""

    later, earlier = sorted(
        (Sport.BADMINTON, Sport.PADEL), key=list(Sport).index, reverse=True
    )
    held = rated(a_rating(later), a_rating(earlier))

    assert sport_to_print(Sport.TENNIS, held) is earlier
    # Insertion order is not the answer either: the mapping above was built
    # later-first on purpose.
    assert list(held) != sorted(held, key=list(Sport).index)


def test_a_player_rated_in_nothing_resolves_to_nothing():
    """A real state during onboarding. The header draws the poster with no Level
    on it and the skill card is simply absent."""

    assert sport_to_print(Sport.PADEL, {}) is None
    assert sport_to_print(None, {}) is None


def test_arriving_from_nowhere_falls_back_the_same_way():
    """A record opened from a surface with no sport behind it — a chat, a games
    list — takes the same fallback rather than a third rule."""

    held = rated(
        a_rating(Sport.PADEL, counted=1), a_rating(Sport.BADMINTON, counted=9)
    )

    assert sport_to_print(None, held) is Sport.BADMINTON


def test_the_pills_are_one_per_rated_sport_in_the_registrys_order():
    held = rated(
        a_rating(Sport.BADMINTON, level=2.0),
        a_rating(Sport.PADEL, level=3.0),
        a_rating(Sport.SQUASH, level=4.0),
    )

    pills = pills_of(held)

    assert [one.sport for one in pills] == [
        sport for sport in Sport if sport in held
    ]
    assert [one.level for one in pills] == [3.0, 4.0, 2.0]


def test_a_player_rated_in_nothing_has_no_pills():
    """Empty, and never a pill with no Level on it."""

    assert pills_of({}) == ()
