"""The ranking's crowd: forty-eight padel players above her, so General runs
past its first page with her below it (#770; ``docs/adr/0203`` §10).

**Why a crowd of its own, and not the cohort grown.** The cohort is the
population the Games deck, Fill in and posting deal from, and its band
histogram is a claim about all of it; forty-eight more members would move both.
These players are **outside the cohort** — the histogram, the aging refusal and
every screen layer never see them — and they reach the product through the
same doors a member does: registered and named, **rated by sitting the
questionnaire** (``seed_the_cohort`` over :data:`RANKING_CROWD`), a profile
committed, a card saved, and every result **a past booked game** in the played
history (``booked_history.py``), so the rooms layer's drain folds each row.

**Their week is cleared after the commit** (``clear_the_week``): nobody is free
at any hour, so the proposer deals none of them into anybody's deck, her *Padel
na Ogrodach* — which every played padel game joins them to — included. A yes
asks for no weekly hour, so their games book as anybody's do.

**Upper Established, a little above one another.** Three answer sets with no
spread — 3,66, 3,74 and 3,83 off today's questionnaire — so every Level here is
within the competitive window of every other from the first game, and a padel
result moves a Level a few hundredths, so five of them leave everybody well
above her 3,2-something and inside that window still. That is what puts her
below the first page: 48 above her, beside the cohort's own.

**Five rounds of twelve games**, one game a day from 75 days ago to 16: each
round seats everybody once, four to a court by a different stride through the
forty-eight, so each plays five results — listed, and none of them *New*. The
fill draws the sides, so ``won_by`` only says which declared player's side won.

**Nicknames from a pool of their own** (``CROWD_SURNAMES``), disjoint from the
catalog's and the cohort's, so no handle can collide with one already taken.
"""

from __future__ import annotations

from typing import Final

from app.kernel import Sport
from app.modules.player_profile.domain.social_tags import SocialTag
from app.seeds.catalog import CENTRE, dealt_nickname
from app.seeds.cohort import (
    CLUB_PLAYER,
    COHORT,
    COHORT_SEED,
    Cohort,
    CohortMember,
    PlayedGame,
)

#: How many: enough that the cohort's seven above her and these leave her
#: past place 50, and General longer than one page.
CROWD_SIZE: Final = 48

#: The crowd's second halves — disjoint from ``catalog.CATALOG_SURNAMES`` and
#: ``catalog.COHORT_SURNAMES``, so a crowd handle is never one already dealt.
CROWD_SURNAMES: Final[tuple[str, ...]] = (
    "Navarro",
    "Ortega",
    "Pujol",
    "Quintana",
    "Rius",
    "Serra",
)

#: The answer sets, in turn: (claims, demonstrations), no spread on either.
_ANSWERS: Final = ((3, 3), (4, 3), (3, 4))

#: Committed long before the first game, and long out of the newcomer window.
_COMMITTED_DAYS_AGO: Final = 80

#: Three tags off the served vocabulary, spelled there and nowhere else.
_TAGS: Final = tuple(
    tag.value
    for tag in (
        SocialTag.PLAYS_TO_WIN,
        SocialTag.HERE_TO_IMPROVE,
        SocialTag.TALKS_THROUGH_THE_MATCH,
    )
)

#: A week to commit with — a commit refuses an empty one — cleared after it.
_COMMITTED_WEEK: Final = ("2:19", "6:10")

#: The strides each round walks the crowd by, each coprime to 48, so every
#: round seats everybody exactly once.
_STRIDES: Final = (1, 5, 7, 11, 13)

#: The first round's first game, in days before the run; one game a day after.
_FIRST_GAME_DAYS_AGO: Final = 75


def _member(index: int) -> CohortMember:
    claims, demonstrations = _ANSWERS[index % len(_ANSWERS)]
    return CohortMember(
        handle=f"crowd-{index:02d}",
        ring="crowd",
        archetype=CLUB_PLAYER.name,
        latitude=CENTRE.latitude,
        longitude=CENTRE.longitude,
        slots=_COMMITTED_WEEK,
        tags=_TAGS,
        intents=((Sport.PADEL.value, "COMPETITIVE"),),
        gender="WOMAN" if index % 2 else "MAN",
        gender_preference="ANY",
        committed_days_ago=_COMMITTED_DAYS_AGO,
        claims=claims,
        demonstrations=demonstrations,
        claim_spread=0,
        demonstration_spread=0,
        photograph=None,
        nickname=dealt_nickname(index, CROWD_SURNAMES),
        intro=None,
    )


#: The crowd, in the shape ``seed_the_cohort`` writes — **not the cohort**, and
#: drawn from no seed: every row above is declared, and ``seed`` is the
#: cohort's own, which nothing here reads.
RANKING_CROWD: Final = Cohort(
    seed=COHORT_SEED,
    members=tuple(_member(index) for index in range(CROWD_SIZE)),
    centre=COHORT.centre,
)


def _games() -> tuple[PlayedGame, ...]:
    games: list[PlayedGame] = []
    for round_, stride in enumerate(_STRIDES):
        by_seat = sorted(
            range(CROWD_SIZE), key=lambda index: (stride * index + round_) % CROWD_SIZE
        )
        for court in range(CROWD_SIZE // 4):
            four = [
                RANKING_CROWD.members[i].handle
                for i in by_seat[4 * court : 4 * court + 4]
            ]
            games.append(
                PlayedGame(
                    sport=Sport.PADEL.value,
                    played_days_ago=_FIRST_GAME_DAYS_AGO - len(games),
                    side_a=(four[0], four[1]),
                    side_b=(four[2], four[3]),
                    won_by="A" if (court + round_) % 2 else "B",
                )
            )
    return tuple(games)


#: **The crowd's games, oldest first** — sixty, one a day.
RANKING_CROWD_GAMES: Final[tuple[PlayedGame, ...]] = _games()


def _refuse_a_crowd_that_collides() -> None:
    """On import: no crowd nickname or handle is anybody else's."""

    taken = {member.nickname for member in COHORT.members}
    for member in RANKING_CROWD.members:
        if member.nickname in taken:
            raise RuntimeError(f"'{member.nickname}' is a cohort member's nickname")
    if len({member.nickname for member in RANKING_CROWD.members}) != CROWD_SIZE:
        raise RuntimeError("two of the crowd share a nickname")


_refuse_a_crowd_that_collides()
