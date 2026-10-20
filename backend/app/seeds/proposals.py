"""The games still filling: **the proposer deals them**, and four of the
protagonist's picks are answered to nought, one, two and three of the other
three In (#538, #540; the screens Part D).

**The seed runs the proposer for its pools** — every group the layers above
wrote, through ``ProposeGames``, the engine's own use case, over the run's own
clock — so what a developer's decks hold is what the engine deals: the most even
four at every hour a club sells and its members are free for, dealt at their
best hour. Nothing here chooses who is on a card. Each yes is then said by
``SayYes``, the use case the phone's swipe runs, so a seeded yes needed a saved
card exactly as a real one does. Nothing here opens a
table.

**Its own group, because none of the others can seat a four.** Every Play
group above is drawn from the named accounts (``groups.py``), and the
protagonist's own padel group holds two accounts with no Player profile — who
fit nobody, since a gate that cannot be evaluated excludes. So this layer
gathers a crowd the way a group does: she creates *Padel po pracy* at Bonarka
Arena, which sells padel on her evenings and her Saturday, and **the cohort
members who want competitive padel, as she does, and fit her and each other**
join it — chosen by the real pair rule (``PlayerFit``), in the cohort's own
order, so the group is a clique the proposer can seat.

**Her four answered picks** are the first pick she is on each day from two days
out, so a card outlives a day of developing against it; the other three named on
each say yes, nought to three of them.

**Written at the run's own now**, since a proposal is about an hour ahead; and
**re-running makes no pick twice** — the proposer deals nothing a court hour
already holds, and a pick's id is its game, so a pick already filling is found
and left as the developer left it. A later run on a later day deals later hours,
and the earlier picks expire at their own book-by.

**The run fails by name** when the proposer deals her fewer answered picks than
this layer promises, rather than seeding a deck that cannot show *Book it now*.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_domain_event_store,
    build_event_publisher,
    build_group_code_minter,
    build_home_clubs,
    build_player_fit,
    build_propose_games,
    build_proposal_directory,
    build_proposal_repository,
    build_say_yes,
    build_unit_of_work,
    build_user_repository,
    build_wanted_kinds,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE, local_day
from app.modules.groups.application.commands import CreatePlayerGroupCommand
from app.modules.groups.application.create_player_group import CreatePlayerGroup
from app.modules.groups.domain.value_objects import GroupName, JoinPolicy
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.proposals.application.propose_games import Proposed
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.users.domain.value_objects import Email
from app.seeds.catalog import THE_POPULATED_PLAYER
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS, desk_email
from app.seeds.groups import group_repository, group_run_by, join_group
from app.seeds.money import THE_FAKE, SeedMoney

#: The group the games are dealt in, and where it plays.
GAMES_GROUP: Final = "Padel po pracy"
GAMES_CLUB: Final = next(club for club in SEED_CLUBS if club.name == "Bonarka Arena")
GAMES_SPORT: Final = Sport.PADEL
#: Her padel intent, so her deck's segment is the one these are dealt in.
GAMES_KIND: Final = SearchMode.COMPETITIVE

#: How many of the cohort the group gathers besides her: three disjoint fours
#: at an hour Bonarka's courts can hold.
CROWD: Final = 12
#: Her answered picks, by how many of the other three are In. The last is
#: *Book it now*.
IN_ON_EACH: Final = (0, 1, 2, 3)
#: How far ahead the first answered pick is, so a card outlives a day of
#: developing.
LEAD: Final = timedelta(days=2)

# Refused on import, through the domain's own value object, as ``groups.py``'s
# names are: a name the New group form would refuse fails here rather than half
# way through a run.
GroupName(GAMES_GROUP)


@final
@dataclass(frozen=True, slots=True)
class SeededPick:
    proposal_id: UUID
    start: Instant
    #: The three named beside her, in the order they were named.
    named: tuple[UUID, ...]
    #: How many of them said yes.
    in_count: int
    #: Whether this run made it, or found it already filling.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededProposals:
    group_id: UUID
    created_group: bool
    #: How many of the cohort fit her and each other and are in the group.
    crowd: int
    #: Her answered picks.
    picks: tuple[SeededPick, ...]
    #: What the proposer did over every pool this run.
    proposed: Proposed


class NotEnoughToDeal(RuntimeError):
    """The crowd cannot seat the picks this layer promises."""


async def write_the_proposals(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    cohort: Sequence[tuple[str, UUID]],
    money: SeedMoney = THE_FAKE,
) -> SeededProposals:
    """Gather the group, run the proposer over every pool, then answer four of
    her picks.

    **After the accounts, the cohort, their cards, the clubs' courts and every
    group**, which it reads and never writes, and after every layer that writes a
    block — the fit is read live, so a block written later could leave a four
    that no longer fits."""

    clock = FixedClock(at=now)
    async with session_factory() as session:
        her = await _protagonist(session)
        club_id = await games_club_id(session)
        crowd = await _the_crowd(session, her, [player for _, player in cohort], now)
        group_id, created = await _the_group(
            session, settings, her, club_id, crowd, now
        )
        before = set(
            await build_proposal_directory(session).filling_in(group_id, now=now)
        )
        proposer = build_propose_games(session, clock=clock)
        proposed = Proposed()
        for pool_id in await proposer.every_pool():
            proposed += await proposer.execute(pool_id)
        mine = await _her_picks(session, her, group_id, now)
        if len(mine) < len(IN_ON_EACH):
            raise NotEnoughToDeal(
                f"{GAMES_GROUP} cannot answer {len(IN_ON_EACH)} picks: {len(crowd)} of "
                f"the cohort want competitive padel and fit her and each other, and "
                f"the proposer dealt her a pick on only {len(mine)} days of the "
                f"fortnight from {LEAD.days} days out at {GAMES_CLUB.name}"
            )
        picks: list[SeededPick] = []
        for (proposal, named), in_count in zip(mine, IN_ON_EACH, strict=True):
            for player in named[:in_count]:
                if player not in proposal.yeses:
                    await _says_yes(
                        session,
                        clock,
                        settings,
                        money.provider(),
                        proposal.proposal_id,
                        player,
                    )
            picks.append(
                SeededPick(
                    proposal.proposal_id,
                    proposal.start,
                    named,
                    in_count,
                    made=proposal.proposal_id not in before,
                )
            )
    return SeededProposals(
        group_id=group_id,
        created_group=created,
        crowd=len(crowd),
        picks=tuple(picks),
        proposed=proposed,
    )


async def _protagonist(session: AsyncSession) -> UUID:
    user = await build_user_repository(session).get_by_email(THE_POPULATED_PLAYER.email)
    if user is None:
        raise RuntimeError("the protagonist is not registered — the accounts run first")
    return user.id


async def games_club_id(session: AsyncSession) -> UUID:
    """The club the games are dealt at — its id, off its desk's account."""

    account = await build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).get_by_email(Email(desk_email(GAMES_CLUB)))
    if account is None:
        raise RuntimeError(f"{GAMES_CLUB.name} has not signed up — the clubs run first")
    return account.club_id


async def _the_crowd(
    session: AsyncSession, her: UUID, cohort: Sequence[UUID], now: Instant
) -> tuple[UUID, ...]:
    """The cohort members who want the kind she plays and fit her and each
    other, in the cohort's order — greedily, so each one taken fits everybody
    taken before. The proposer deals nobody a kind they do not want."""

    unfit = await build_player_fit(session).unfit_pairs(
        [her, *cohort], sport=GAMES_SPORT, kind=GAMES_KIND, at=now
    )
    wanted = build_wanted_kinds(session)
    taken = [her]
    for member in cohort:
        if len(taken) > CROWD:
            break
        kinds = await wanted.of(member, sport=GAMES_SPORT)
        if (
            kinds is not None
            and GAMES_KIND in kinds
            and all(frozenset((member, other)) not in unfit for other in taken)
        ):
            taken.append(member)
    return tuple(taken[1:])


async def _the_group(
    session: AsyncSession,
    settings: Settings,
    her: UUID,
    club_id: UUID,
    crowd: Sequence[UUID],
    now: Instant,
) -> tuple[UUID, bool]:
    """Her group at the club, created once; everybody in the crowd joins it —
    joining again records nothing."""

    group_id = await _games_group_of(session, her, club_id)
    created = group_id is None
    if group_id is None:
        group_id = await CreatePlayerGroup(
            groups=group_repository(session),
            clubs=build_home_clubs(session),
            codes=build_group_code_minter(session),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=now),
        ).execute(
            CreatePlayerGroupCommand(
                creator_id=her,
                name=GAMES_GROUP,
                home_club_id=club_id,
                join_policy=JoinPolicy.ANYONE,
            )
        )
    for member in crowd:
        await join_group(session, settings, group_id, member, FixedClock(at=now))
    return group_id, created


async def _games_group_of(
    session: AsyncSession, her: UUID, club_id: UUID
) -> UUID | None:
    return await group_run_by(session, her, club_id=club_id, name=GAMES_GROUP)


async def her_games_group(session: AsyncSession) -> tuple[UUID, UUID] | None:
    """The protagonist, and the group this layer deals her games in — ``None``
    before a run has gathered it. What the screens read her deck from."""

    her = await _protagonist(session)
    group_id = await _games_group_of(session, her, await games_club_id(session))
    return None if group_id is None else (her, group_id)


async def _her_picks(
    session: AsyncSession, her: UUID, group_id: UUID, now: Instant
) -> list[tuple[Proposal, tuple[UUID, ...]]]:
    """The first pick she was dealt on each day from ``LEAD`` out, soonest
    first, the first ``IN_ON_EACH``'s worth — each with the three named beside
    her on her version, in the order they were dealt."""

    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    days: set[date] = set()
    mine: list[tuple[Proposal, tuple[UUID, ...]]] = []
    for proposal_id in await build_proposal_directory(session).filling_in(
        group_id, now=now
    ):
        proposal = await proposals.load(proposal_id)
        if (
            proposal is None
            or proposal.origin is not Origin.PICK
            or proposal.sport is not GAMES_SPORT
            or proposal.kind is not GAMES_KIND
            or proposal.start < now + LEAD
        ):
            continue
        version = proposal.version_of(her)
        day = local_day(proposal.start)
        if version is None or day in days:
            continue
        # Dealt with the three beside her — never a version widened to her
        # later, which names only the seats that were open.
        named = tuple(player for player in version.players if player != her)
        if len(named) < len(IN_ON_EACH) - 1:
            continue
        days.add(day)
        mine.append((proposal, named[: len(IN_ON_EACH) - 1]))
        if len(mine) == len(IN_ON_EACH):
            break
    return mine


async def _says_yes(
    session: AsyncSession,
    clock: FixedClock,
    settings: Settings,
    provider: PaymentProvider,
    proposal_id: UUID,
    player: UUID,
) -> YesAnswer:
    """The swipe the phone's yes runs — and, when it is the last, the fill,
    through the run's own provider (``money.py``)."""

    return await build_say_yes(
        session, clock=clock, provider=provider, settings=settings
    ).execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=player))


def proposal_lines(seeded: SeededProposals) -> list[str]:
    """The report's section: the group, and each pick with who is In."""

    done = seeded.proposed
    lines = [
        f"Games still filling — the proposer over {done.pools} pool(s): "
        f"{done.made} picked, {done.dealt} dealt on, {done.lost} lost, "
        f"{done.refused} refused",
        f"  {GAMES_GROUP} at {GAMES_CLUB.name}, "
        f"{'created' if seeded.created_group else 'already there'}, "
        f"{seeded.crowd} of the cohort fit {THE_POPULATED_PLAYER.email}; "
        f"her answered picks:",
    ]
    for pick in seeded.picks:
        state = "made" if pick.made else "already filling"
        lines.append(
            f"  {pick.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
            f"{pick.in_count} of 3 In · {state}"
        )
    return lines
