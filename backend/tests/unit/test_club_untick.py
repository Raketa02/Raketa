"""A sport an official group declares cannot be unticked (#509,
``docs/adr/0182`` §5) — the rule itself, and when the club's details edit asks
the groups at all.

The HTTP suite (``tests/api/test_official_groups.py``) walks the desk's refusal
as the club website meets it; this is the rule's order and the question's cost.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Sport
from app.modules.clubs.application.club_details import ChangeClubDetails
from app.modules.clubs.application.commands import (
    ChangeClubDetailsCommand,
    ClubDetailsInput,
)
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.errors import ClubSportDeclaredByGroup
from app.modules.clubs.domain.ports import DeclaringGroup
from app.modules.clubs.domain.untick import refuse_an_untick, unticked
from app.modules.clubs.domain.value_objects import (
    City,
    ClubDetails,
    ClubName,
    District,
    MapPoint,
    OfferedSports,
)
from tests.unit.fake_clock import MovableClock

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
PADEL_AND_TENNIS = frozenset({Sport.PADEL, Sport.TENNIS})


# --------------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------------- #


def test_unticked_is_what_the_club_offers_and_the_save_drops():
    assert unticked({Sport.PADEL, Sport.TENNIS}, {Sport.TENNIS}) == {Sport.PADEL}
    assert unticked({Sport.PADEL}, {Sport.PADEL, Sport.SQUASH}) == frozenset()


def test_a_sport_nobody_declares_may_go():
    refuse_an_untick(
        {Sport.TENNIS},
        [DeclaringGroup(name="Ogrody 33 Club", sports=frozenset({Sport.PADEL}))],
    )


def test_the_refusal_names_the_first_sport_in_the_registry_s_order():
    """Padel before tennis, whichever order the groups were read in."""

    declaring = [
        DeclaringGroup(name="Tennis nights", sports=frozenset({Sport.TENNIS})),
        DeclaringGroup(name="Ogrody 33 Club", sports=frozenset({Sport.PADEL})),
    ]

    with pytest.raises(ClubSportDeclaredByGroup) as refused:
        refuse_an_untick(PADEL_AND_TENNIS, declaring)

    assert refused.value.details == {
        "field": "sports",
        "sport": "PADEL",
        "group": "Ogrody 33 Club",
    }


@pytest.mark.parametrize("order", [1, -1], ids=["as-read", "reversed"])
def test_and_the_first_group_playing_it_by_name_ignoring_case(order):
    declaring = [
        DeclaringGroup(name="ogrody open play", sports=frozenset({Sport.PADEL})),
        DeclaringGroup(name="Ogrody 33 Club", sports=PADEL_AND_TENNIS),
        DeclaringGroup(name="Padel mornings", sports=frozenset({Sport.PADEL})),
    ][::order]

    with pytest.raises(ClubSportDeclaredByGroup) as refused:
        refuse_an_untick({Sport.PADEL}, declaring)

    assert refused.value.details["group"] == "Ogrody 33 Club"
    assert "Ogrody 33 Club" in refused.value.message


# --------------------------------------------------------------------------- #
# When the details edit asks
# --------------------------------------------------------------------------- #


class _Clubs:
    def __init__(self, club: Club) -> None:
        self.club = club
        self.saved: list[Club] = []

    async def load(self, club_id: UUID) -> Club | None:
        return self.club if club_id == self.club.id else None

    async def save(self, club: Club) -> None:
        self.saved.append(club)


class _Groups:
    def __init__(self, *declaring: DeclaringGroup) -> None:
        self._declaring = declaring
        self.asked = 0

    async def declared_at(self, club_id: UUID) -> Sequence[DeclaringGroup]:
        self.asked += 1
        return self._declaring


class _UnitOfWork:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def ogrody(sports: frozenset[Sport] = PADEL_AND_TENNIS) -> Club:
    club = Club.register(
        club_id=uuid4(),
        details=ClubDetails(
            name=ClubName("Ogrody 33"),
            district=District("Grzegórzki"),
            city=City("Kraków"),
            sports=OfferedSports.of(sports),
            point=MapPoint(latitude=50.06, longitude=19.95),
        ),
        occurred_at=NOW,
    )
    club.pull_events()
    return club


def saving(club: Club, *sports: Sport) -> ChangeClubDetailsCommand:
    return ChangeClubDetailsCommand(
        club_id=club.id,
        details=ClubDetailsInput(
            name="Ogrody 33",
            district="Grzegórzki",
            city="Kraków",
            sports=sports,
            latitude=50.06,
            longitude=19.95,
        ),
    )


def change(clubs: _Clubs, groups: _Groups) -> ChangeClubDetails:
    return ChangeClubDetails(
        clubs=clubs, groups=groups, uow=_UnitOfWork(), clock=MovableClock(NOW)
    )


async def test_the_groups_are_not_asked_when_no_sport_is_unticked():
    club = ogrody()
    groups = _Groups(DeclaringGroup(name="Ogrody 33 Club", sports=PADEL_AND_TENNIS))

    await change(_Clubs(club), groups).execute(
        saving(club, Sport.PADEL, Sport.TENNIS, Sport.SQUASH)
    )

    assert groups.asked == 0


async def test_an_untick_nobody_declares_is_saved():
    club = ogrody()
    clubs = _Clubs(club)
    groups = _Groups(
        DeclaringGroup(name="Ogrody 33 Club", sports=frozenset({Sport.PADEL}))
    )

    saved = await change(clubs, groups).execute(saving(club, Sport.PADEL))

    assert groups.asked == 1
    assert saved.details.sports == OfferedSports.of([Sport.PADEL])
    assert clubs.saved == [club]


async def test_an_untick_a_group_declares_is_refused_and_nothing_is_saved():
    club = ogrody()
    clubs = _Clubs(club)

    with pytest.raises(ClubSportDeclaredByGroup):
        await change(
            clubs,
            _Groups(
                DeclaringGroup(name="Ogrody 33 Club", sports=frozenset({Sport.PADEL}))
            ),
        ).execute(saving(club, Sport.TENNIS))

    assert clubs.saved == []
    assert club.pull_events() == []
