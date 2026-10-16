"""``GET /api/v1/players/{id}/record`` and ``/players/me/record``.

A player taps a face and is told who that person is. The rule the route runs on
(``docs/adr/0159``): **a record is read through a prior disclosure, never about a
person** — the pair played together, share a group, or the reader runs a group
the subject is in (#575) — and the gates about accounts are re-evaluated live on
every open, so a disclosure entitles a reader to ask and never to be answered.

**The refusal is the thing most worth testing here**, and it is tested as a
*sameness* rather than as three statuses: never disclosed, held and no such
player produce the same bytes, because a response separating *never disclosed*
from *no such player* would answer *is this id real* about a stranger.

**A block is no gate any more, in either direction** (``docs/adr/0193`` §2). The
blocker opens the record and reads ``blocked_by_you``; the blocked person reads
the blocker's record **byte for byte** as they would have unblocked.

Every assertion lands on HTTP, through the async client fixture: ASGI transport
over in-memory SQLite, **no MinIO, no Redis and no sidecar**.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_sportsmanship_ledger,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.presentation.dependencies import get_block_query
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.rating.domain.events import RatingInitialised
from app.modules.sportsmanship.domain.card import (
    SettledCourt,
    SportsmanshipCard,
    StarsGiven,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)
from app.shared.ids import new_uuid
from tests.unit.event_log import append
from tests.api import players_world as players
from tests.api.test_groups import a_club, a_group
from tests.api.test_groups import join as join_group


@pytest.fixture
async def searcher(client):
    return await players.a_rated_player(client, "searcher")


async def their_group(client, searcher) -> tuple[dict, dict]:
    """The reader's own *Anyone* group at a club, and the reader as its owner."""

    owner = {"id": searcher["id"], "headers": players.auth(searcher["token"])}
    return await a_group(client, owner, await a_club(client)), owner


async def a_member_of_their_group(client, session_factory, searcher) -> UUID:
    """Somebody filed on the log who joined the reader's group — the disclosure
    a group's Members makes, made the way the platform makes one: a real group
    and a real *Join*, so what entitles the read is membership the platform
    holds rather than a fixture's say-so."""

    group, _ = await their_group(client, searcher)
    subject, token = await players.a_player_on_the_log(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    joined = await join_group(
        client, {"id": subject, "headers": players.auth(token)}, group
    )
    assert joined.status_code == 200, joined.text
    return subject


async def record_of(client, token: str, player_id: UUID, *, sport: Sport | None = None):
    return await client.get(
        f"/api/v1/players/{player_id}/record",
        params={} if sport is None else {"sport": sport.value},
        headers=players.auth(token),
    )


async def own_record(client, token: str, *, sport: Sport | None = None):
    return await client.get(
        "/api/v1/players/me/record",
        params={} if sport is None else {"sport": sport.value},
        headers=players.auth(token),
    )


async def also_rated_in(session_factory, player_id: UUID, *, sport: Sport, mu: float):
    """One more Level for somebody already rated, filed where a rating lives.

    Through the log at the stream id the rating context derives, because that is
    the address the read port asks — a rating filed anywhere else is one the
    sheet can never find (``docs/adr/0105``).
    """

    at = datetime.now(timezone.utc) - timedelta(days=3)
    await append(
        session_factory,
        RatingInitialised(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport.value,
            mu=mu,
            sigma=0.20,
            confidence=83,
            range_low=mu - 0.2,
            range_high=mu + 0.2,
            band_name="Established",
            band_lower=2.7,
            band_upper=3.8,
            status="INITIAL_ESTIMATE",
            engine_version="v3",
            source_assessment_id=new_uuid(),
            occurred_at=at,
        ),
        aggregate_type=RATING_AGGREGATE,
        aggregate_id=skill_rating_id(player_id, sport),
    )


async def a_game_not_come_to(
    session_factory, absent: UUID, reporter: UUID, *, sport: Sport
):
    """A booked game ``reporter`` came to and tapped ``absent`` *isn't here
    yet* at the club; ``absent`` never arrived and never claimed — **Didn't
    come**, for good a day after the tap window (#657).

    The miss half of *shows up*, charged to **the player reported** and to
    nobody else on that court. Since #655 it is the only one: a full court
    nobody recorded is played, and nothing is charged for the silence.
    """

    starts = instant(datetime.now(timezone.utc) - timedelta(days=6))
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=absent),
                Seating(side=GameSide.B, player_id=reporter),
            )
        ),
        occurred_at=instant(starts - timedelta(days=2)),
        starts_at=starts,
    )
    # *Isn't here yet* ten minutes in, at the club, and no arrival: Didn't
    # come at half past, for good a day later (#657).
    game.note_absent(
        by=reporter,
        absent=absent,
        where=ClubVerdict(at_the_club=True, club_name=None),
        occurred_at=instant(starts + timedelta(minutes=10)),
    )
    async with session_factory() as session:
        await build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(game)
        await session.commit()


async def a_kept_booked_game(session_factory, player: UUID):
    """A padel game the player stayed in until its hour — the good half of
    *keeps plans* (#544). Booked five days before its hour, four days ago,
    through the aggregate."""

    starts = instant(datetime.now(timezone.utc) - timedelta(days=4))
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=starts,
        share_grosze=30_00,
        first_side=(player, new_uuid()),
        second_side=(new_uuid(), new_uuid()),
        cut_off=instant(starts - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(starts - timedelta(days=5)),
    )
    async with session_factory() as session:
        await build_booking_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(booking)
        await session.commit()


#: A record nothing has happened to: everyone starts at a hundred.
A_HUNDRED_AND_NEW = {
    "player_score": 100,
    "band": "VERY_HIGH",
    "is_new": True,
    "turned_up": 0,
    "turned_up_of": 0,
    "late": 0,
    "kept": 0,
    "kept_of": 0,
    "left_in_dispute": 0,
}


def every_key(payload) -> list[str]:
    """Every property name anywhere in a response, however deeply nested.

    Keys rather than the raw text, deliberately: a tag id or a handle that
    happened to contain the word would make a text search fail for a reason that
    has nothing to do with the rule being kept.
    """

    if isinstance(payload, dict):
        return [
            name
            for key, value in payload.items()
            for name in (key, *every_key(value))
        ]
    if isinstance(payload, list):
        return [name for one in payload for name in every_key(one)]
    return []


def without_the_trace(response) -> str:
    """One refusal's body, minus the one field that is per-request.

    ``trace_id`` ties a client failure to a server log and is different on every
    response by design. Everything else has to be identical, and comparing the
    **text** rather than a parsed dictionary is deliberate: key order and
    spelling are part of what a client sees.
    """

    body = json.loads(response.text)
    assert body.pop("trace_id"), "a refusal with no trace is a refusal nobody can chase"
    return json.dumps(body, sort_keys=False)


# ---------------------------------------------------------------------------
# What opens
# ---------------------------------------------------------------------------


async def test_a_group_you_share_opens_their_record(
    client, session_factory, searcher
):
    """The ordinary case, and the whole identity zone with it."""

    subject = await a_member_of_their_group(client, session_factory, searcher)

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "is_self": False,
        "blocked_by_you": False,
        # The one read about another player that carries both halves of the
        # naming (``docs/adr/0171`` §4): two people may share a name, and the
        # record is where a friend tells them apart.
        "name": "subject",
        "nickname": "subject",
        "area_code": "A+05151-000013",
        "social_tags": list(players.COMPETITIVE_TAGS),
        "sports": [
            {
                "sport": "PADEL",
                "level": pytest.approx(searcher["mu"]),
                "band": "Improver",
            }
        ],
        "skill": {
            "sport": "PADEL",
            "level": pytest.approx(searcher["mu"]),
            "band": "Improver",
            "confidence": 62,
            # A Level out of the questionnaire that no game has tested yet. **A
            # measured nought and not an absence** — the confidence beside it is
            # what makes that readable.
            "counted_games": 0,
            "likely_range": {
                "low": pytest.approx(searcher["mu"] - 0.3),
                "high": pytest.approx(searcher["mu"] + 0.3),
            },
            "last_five": [],
        },
        # Everyone starts at a hundred: nothing has happened to them yet (#659).
        "reliability": A_HUNDRED_AND_NEW,
    }
    # The photograph's three fields are **omitted together** for a player with
    # none, and never sent as nulls: the client draws the generated poster.
    assert "photo_id" not in body and "photo_url" not in body
    assert "review" not in body
    # And nobody has watched them play, so there is no habit to describe: the
    # row is **absent** rather than drawn at nought over nought.
    assert "variety" not in body


async def test_a_record_quotes_the_line_they_wrote_and_omits_it_otherwise(
    client, session_factory, searcher
):
    """**The record sheet draws the intro under the name** (``docs/adr/0170``
    §4), verbatim and off the profile — and a player who skipped has no key at
    all, never an empty string."""

    group, _ = await their_group(client, searcher)
    shown = {}
    for name, intro in (
        ("karol", "Moved from Wrocław in May. Needs opponents."),
        ("ola", None),
    ):
        member_id, token = await players.a_player_on_the_log(
            client, session_factory, name, mu=searcher["mu"], intro=intro
        )
        joined = await join_group(
            client, {"id": member_id, "headers": players.auth(token)}, group
        )
        assert joined.status_code == 200, joined.text
        shown[name] = member_id

    wrote = await record_of(client, searcher["token"], shown["karol"])
    skipped = await record_of(client, searcher["token"], shown["ola"])

    assert wrote.status_code == 200, wrote.text
    assert wrote.json()["intro"] == "Moved from Wrocław in May. Needs opponents."
    assert skipped.status_code == 200, skipped.text
    assert "intro" not in skipped.json()


async def test_your_own_record_opens_with_nothing_behind_it(client, searcher):
    """*How others see you* — the one record needing no prior disclosure, and the
    one the client must not have to compare identifiers to recognise."""

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text
    assert response.json()["is_self"] is True
    assert response.json()["name"] == "searcher"
    assert response.json()["nickname"] == "searcher"
    # Nobody can block themselves, so their own sheet never says they did.
    assert response.json()["blocked_by_you"] is False


async def test_asking_about_yourself_by_id_is_still_your_own_record(
    client, searcher
):
    response = await record_of(client, searcher["token"], searcher["id"])

    assert response.status_code == 200, response.text
    assert response.json()["is_self"] is True


async def test_a_game_you_are_both_on_opens_the_record_both_ways(
    client, session_factory, searcher
):
    """**Played together** (#575): a court the platform put the pair on — booked
    and still ahead of them, with no group and no search anywhere between them
    — is a disclosure each way round."""

    subject, token = await players.a_player_on_the_log(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    assert (await record_of(client, searcher["token"], subject)).status_code == 404

    await players.a_booked_game(
        session_factory, side_a=(searcher["id"],), side_b=(subject,)
    )

    theirs = await record_of(client, searcher["token"], subject)
    mine = await record_of(client, token, searcher["id"])

    assert theirs.status_code == 200, theirs.text
    assert theirs.json()["name"] == "subject"
    assert mine.status_code == 200, mine.text
    assert mine.json()["name"] == "searcher"


async def two_strangers_in_one_group(
    client, session_factory, searcher
) -> tuple[dict, dict, dict]:
    """The searcher and a player nobody has shown them, both in the searcher's
    *Anyone* group — the pair a group's Members lists to each other (#514)."""

    subject_id, subject_token = await players.a_player_on_the_log(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    group, owner = await their_group(client, searcher)
    member = {"id": subject_id, "headers": players.auth(subject_token)}
    joined = await join_group(client, member, group)
    assert joined.status_code == 200, joined.text
    return group, {**owner, "token": searcher["token"]}, {
        **member,
        "token": subject_token,
    }


async def test_a_group_you_are_both_in_opens_the_record_both_ways(
    client, session_factory, searcher
):
    """**The strand Members promises** (#529): *Press and hold anyone for the
    full record* is read by a member about people nothing else introduced —
    the group is what introduced them."""

    subject_id, subject_token = await players.a_player_on_the_log(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    assert (await record_of(client, searcher["token"], subject_id)).status_code == 404

    group, _ = await their_group(client, searcher)
    joined = await join_group(
        client, {"id": subject_id, "headers": players.auth(subject_token)}, group
    )
    assert joined.status_code == 200, joined.text

    theirs = await record_of(client, searcher["token"], subject_id)
    mine = await record_of(client, subject_token, searcher["id"])

    assert theirs.status_code == 200, theirs.text
    assert theirs.json()["name"] == "subject"
    assert mine.status_code == 200, mine.text
    assert mine.json()["name"] == "searcher"


async def test_leaving_the_group_closes_the_record_it_opened(
    client, session_factory, searcher
):
    """**Membership as it stands, not as it was** — Members lists who is in the
    group now, so the strand is the group now: unlike a game, a group left is no
    longer one the pair are in."""

    group, owner, member = await two_strangers_in_one_group(
        client, session_factory, searcher
    )
    assert (await record_of(client, owner["token"], member["id"])).status_code == 200

    left = await client.delete(
        f"/api/v1/groups/{group['id']}/membership", headers=member["headers"]
    )

    assert left.status_code == 204, left.text
    assert (await record_of(client, owner["token"], member["id"])).status_code == 404
    assert (await record_of(client, member["token"], owner["id"])).status_code == 404


async def test_a_preference_gates_no_record(client, session_factory, searcher):
    """**No preference** (#575). A gender preference says
    who a player is willing to be *matched* with; the group already put these
    two in front of each other, and its Members lists each to the other — so
    the record opens whichever way the preference points."""

    group, _ = await their_group(client, searcher)
    kuba_id, kuba = await players.a_player_on_the_log(
        client,
        session_factory,
        "kuba",
        mu=searcher["mu"],
        gender="MAN",
        gender_preference="WOMEN_ONLY",
    )
    piotr_id, piotr = await players.a_player_on_the_log(
        client, session_factory, "piotr", mu=searcher["mu"], gender="MAN"
    )
    for member_id, token in ((kuba_id, kuba), (piotr_id, piotr)):
        joined = await join_group(
            client, {"id": member_id, "headers": players.auth(token)}, group
        )
        assert joined.status_code == 200, joined.text

    assert (await record_of(client, piotr, kuba_id)).status_code == 200
    assert (await record_of(client, kuba, piotr_id)).status_code == 200


async def test_a_block_closes_no_record_and_the_blocker_reads_their_own(
    client, session_factory, searcher
):
    """**A block is not a record gate, in either direction** (``docs/adr/0193``
    §2). The blocker opens the record of the person they blocked — it is where
    they would look to undo it — and it says they blocked them (§3)."""

    _, owner, member = await two_strangers_in_one_group(
        client, session_factory, searcher
    )

    blocked = await players.block_between(client, member["token"], owner["id"])
    assert blocked.status_code == 204, blocked.text

    mine = await record_of(client, member["token"], owner["id"])
    assert mine.status_code == 200, mine.text
    assert mine.json()["blocked_by_you"] is True

    lifted = await client.delete(
        f"/api/v1/blocks/{owner['id']}", headers=players.auth(member["token"])
    )
    assert lifted.status_code == 204, lifted.text
    again = await record_of(client, member["token"], owner["id"])
    assert again.json()["blocked_by_you"] is False


async def test_the_blocked_person_reads_the_blocker_byte_for_byte_as_before(
    client, session_factory, searcher
):
    """**Nothing the blocked person reads names a block** (``docs/adr/0193``
    §3). Their read of the blocker's record is the same bytes whether or not
    they were blocked: ``blocked_by_you`` answers about the reader's own block,
    and the reader made none."""

    _, owner, member = await two_strangers_in_one_group(
        client, session_factory, searcher
    )
    before = await record_of(client, owner["token"], member["id"])

    blocked = await players.block_between(client, member["token"], owner["id"])
    assert blocked.status_code == 204, blocked.text
    after = await record_of(client, owner["token"], member["id"])

    assert before.status_code == after.status_code == 200, after.text
    assert after.text == before.text
    assert after.json()["blocked_by_you"] is False


async def test_both_having_blocked_each_record_says_only_the_readers_own(
    client, session_factory, searcher
):
    """The record is directed, so the fact is per reader: each reads their own
    block, and an unblock by one says nothing about the other's."""

    _, owner, member = await two_strangers_in_one_group(
        client, session_factory, searcher
    )
    await players.block_between(client, member["token"], owner["id"])
    await players.block_between(client, owner["token"], member["id"])
    await client.delete(
        f"/api/v1/blocks/{owner['id']}", headers=players.auth(member["token"])
    )

    assert (await record_of(client, member["token"], owner["id"])).json()[
        "blocked_by_you"
    ] is False
    assert (await record_of(client, owner["token"], member["id"])).json()[
        "blocked_by_you"
    ] is True


class UnreadableBlocks:
    """A block state nobody can read."""

    async def exclusions_for(self, player_id):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocked_between(self, first, second):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocked_pairs_among(self, player_ids):
        raise BlockStateUnavailable("the block store is unreachable")

    async def blocks_made_by(self, blocker_id):
        raise BlockStateUnavailable("the block store is unreachable")


async def test_an_unreadable_block_state_takes_no_record_down(
    client, session_factory, searcher
):
    """**A block stops only what would put two people on a court**
    (``docs/adr/0193``, Consequences): the record opens, and the one fact it
    could not read — the reader's own block — is **omitted**, so the sheet draws
    neither *Block* nor *Unblock* rather than a guess."""

    _, owner, member = await two_strangers_in_one_group(
        client, session_factory, searcher
    )
    readable = (await record_of(client, owner["token"], member["id"])).json()
    players.override(client, get_block_query, UnreadableBlocks)

    unreadable = await record_of(client, owner["token"], member["id"])

    assert unreadable.status_code == 200, unreadable.text
    assert "blocked_by_you" not in unreadable.json()
    assert unreadable.json() == {
        key: value for key, value in readable.items() if key != "blocked_by_you"
    }


# ---------------------------------------------------------------------------
# The one refusal
# ---------------------------------------------------------------------------


async def test_a_person_you_have_never_been_shown_is_refused(
    client, session_factory, searcher
):
    """Without this the route is a player-enumeration endpoint, and a UUID being
    hard to guess is not an authorization model. **A search is no disclosure any
    more** (#575): nothing a reader looked for opens a record — only a court, a
    group or a group they run."""

    stranger, _ = await players.a_player_on_the_log(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    response = await record_of(client, searcher["token"], stranger)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "record_unavailable"


async def test_the_three_refusals_are_byte_identical(
    client, session_factory, searcher
):
    """**Asserted as a sameness, not as three statuses.**

    Never disclosed, held and no such player. A payload separating *never
    disclosed* from *no such player* would answer *is this id real* about a
    stranger. A block is not among them since ``docs/adr/0193`` §2 — it refuses
    no record, either way round.
    """

    subject = await a_member_of_their_group(client, session_factory, searcher)
    stranger, _ = await players.a_player_on_the_log(
        client, session_factory, "stranger", mu=searcher["mu"]
    )

    never_disclosed = await record_of(client, searcher["token"], stranger)
    no_such_player = await record_of(client, searcher["token"], uuid4())
    # **The hold is refused about somebody the reader *was* shown**, so it comes
    # from the live gate rather than from the disclosure. Run against a
    # stranger it would take the same path `never_disclosed` just took, and the
    # sameness below would be a claim about two causes wearing three names.
    players.hold_only(client, subject)
    held = await record_of(client, searcher["token"], subject)
    players.hold_only(client)
    assert (await record_of(client, searcher["token"], subject)).status_code == 200, (
        "the hold, not the fixture, is what refused"
    )

    refusals = (never_disclosed, no_such_player, held)
    assert {one.status_code for one in refusals} == {404}
    assert len({without_the_trace(one) for one in refusals}) == 1


async def test_the_held_reader_is_refused_by_the_same_line(
    client, session_factory, searcher
):
    """A hold points **both ways** (``docs/adr/0095``), so it reaches the route
    that remembers who a player has been shown — and it reaches it as this
    route's one refusal rather than as a second thing to draw."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    players.hold_only(client, searcher["id"])

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "record_unavailable"


async def test_a_held_player_can_still_read_their_own_record(client, searcher):
    """The one screen that tells somebody how they appear is the one a penalty
    must not close: *a penalty nobody can look up is a penalty nobody can fix.*"""

    players.hold_only(client, searcher["id"])

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text


async def test_an_account_that_may_not_be_shown_is_refused(
    client, session_factory, searcher
):
    subject = await a_member_of_their_group(client, session_factory, searcher)
    players.may_not_show(client, subject)

    response = await record_of(client, searcher["token"], subject)

    assert response.status_code == 404, response.text


async def test_a_record_needs_a_signed_in_reader(client, searcher):
    assert (
        await client.get(f"/api/v1/players/{searcher['id']}/record")
    ).status_code == 401
    assert (await client.get("/api/v1/players/me/record")).status_code == 401


async def test_me_is_never_parsed_as_a_player_id(client, searcher):
    """The route ordering, asserted rather than assumed: a parameterised segment
    declared ahead of the literal one would answer the refusal to everybody
    asking for their own record, and nothing else would look wrong."""

    response = await own_record(client, searcher["token"])

    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Which sport the sheet is about
# ---------------------------------------------------------------------------


async def test_the_sport_asked_for_is_the_one_the_skill_card_draws(
    client, session_factory, searcher
):
    """The overwhelming case, and the pills beside it name every sport they hold
    **in the registry's own order** rather than the order the ratings arrived."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)

    asked = await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    body = asked.json()

    assert [one["sport"] for one in body["sports"]] == ["PADEL", "SQUASH"]
    assert body["skill"]["sport"] == "SQUASH"
    assert body["skill"]["level"] == pytest.approx(4.10)
    assert body["skill"]["band"] == "Established"
    assert body["skill"]["confidence"] == 83


async def test_a_sport_they_do_not_play_falls_back_and_never_refuses(
    client, session_factory, searcher
):
    """**The parameter chooses what is drawn and never whether it is.** Admission
    ran in the partition of the search that showed them, which is a fact the
    platform holds — so naming a sport nobody was ever shown in changes the
    header and nothing else."""

    subject = await a_member_of_their_group(client, session_factory, searcher)

    response = await record_of(client, searcher["token"], subject, sport=Sport.TENNIS)

    assert response.status_code == 200, response.text
    assert response.json()["skill"]["sport"] == "PADEL"


async def test_asking_for_no_sport_falls_back_the_same_way(
    client, session_factory, searcher
):
    """A record opened from a surface with no sport behind it — a chat, a games
    list — takes the same fallback rather than a third rule."""

    subject = await a_member_of_their_group(client, session_factory, searcher)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["skill"]["sport"] == "PADEL"


async def test_your_own_record_takes_the_sport_too(client, session_factory, searcher):
    """The same resolution on the one sheet nothing gates."""

    await also_rated_in(session_factory, searcher["id"], sport=Sport.SQUASH, mu=2.40)

    body = (await own_record(client, searcher["token"], sport=Sport.SQUASH)).json()

    assert body["is_self"] is True
    assert body["skill"]["sport"] == "SQUASH"
    assert [one["sport"] for one in body["sports"]] == ["PADEL", "SQUASH"]


# ---------------------------------------------------------------------------
# The run of five
# ---------------------------------------------------------------------------


async def test_the_run_of_five_is_the_resolved_sports_and_nobody_elses(
    client, session_factory, searcher
):
    """**The defect this ticket fixes, over the wire.** A run built across every
    sport and drawn beneath a single sport's Level was squash results under a
    padel number.

    The subject has one padel result and two squash ones; the padel sheet draws
    the padel one alone.
    """

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.SQUASH, a_won=False
    )
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.SQUASH, a_won=True
    )

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    squash = (
        await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    ).json()

    assert padel["skill"]["last_five"] == ["WIN"]
    assert sorted(squash["skill"]["last_five"]) == ["LOSS", "WIN"]
    # And the count the certainty rests on is **not** the run's length: a Level
    # moves when the rating context walks a result forward, and nothing here has.
    assert padel["skill"]["counted_games"] == 0


async def test_a_run_shorter_than_five_is_never_padded(
    client, session_factory, searcher
):
    """One result means one, and the client draws the gap rather than filling
    it. An empty list is what somebody with none gets."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=False
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["skill"]["last_five"] == ["LOSS"]


# ---------------------------------------------------------------------------
# Opponent variety
# ---------------------------------------------------------------------------


async def test_the_record_says_how_widely_they_spread_their_games(
    client, session_factory, searcher
):
    """**A pair and never a share**, over the **whole** record.

    Three counted games against two people: two different faces, three evenings.
    The percentage is the client's division, because *two of three* and *twenty
    of thirty* are the same share and different claims — the same argument the
    rows above it print their raw fractions for.
    """

    subject = await a_member_of_their_group(client, session_factory, searcher)
    somebody_else = uuid4()
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=False
    )
    await players.a_confirmed_game(
        session_factory, subject, somebody_else, sport=Sport.TENNIS, a_won=True
    )

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["variety"] == {"distinct_opponents": 2, "times_on_court": 3}


async def test_variety_counts_every_sport_and_the_sport_asked_for_moves_it_not(
    client, session_factory, searcher
):
    """**It is about no sport at all**, unlike the run of five above it.

    The same sheet asked for padel and for squash draws the same variety and two
    different runs of form: one is a habit and the other is this sport's record.
    """

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await also_rated_in(session_factory, subject, sport=Sport.SQUASH, mu=4.10)
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await players.a_confirmed_game(
        session_factory, subject, uuid4(), sport=Sport.SQUASH, a_won=True
    )

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    squash = (
        await record_of(client, searcher["token"], subject, sport=Sport.SQUASH)
    ).json()

    assert padel["variety"] == {"distinct_opponents": 2, "times_on_court": 2}
    assert squash["variety"] == padel["variety"]
    assert padel["skill"]["last_five"] == ["WIN"]
    assert squash["skill"]["last_five"] == ["WIN"]


async def test_your_own_record_carries_the_same_pair(
    client, session_factory, searcher
):
    """*How others see you* draws the number everybody else is shown, which is
    the whole reason the screen exists."""

    await players.a_confirmed_game(
        session_factory, searcher["id"], uuid4(), sport=Sport.PADEL, a_won=True
    )

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["variety"] == {"distinct_opponents": 1, "times_on_court": 1}


# ---------------------------------------------------------------------------
# Player reliability — points, the band, New and the counts (#659)
# ---------------------------------------------------------------------------

async def test_the_record_reads_points_the_band_new_and_the_counts(
    client, session_factory, searcher
):
    """A game played through a month ago (100), a booked game they Didn't come
    to six days ago (75) — kept on *Keeps plans*, since a *Didn't come* is
    priced once — and the booking of it kept: **75 · High**, still New."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await players.a_confirmed_game(
        session_factory, subject, searcher["id"], sport=Sport.PADEL, a_won=True
    )
    await a_game_not_come_to(
        session_factory, subject, searcher["id"], sport=Sport.PADEL
    )
    await a_kept_booked_game(session_factory, subject)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["reliability"] == {
        "player_score": 75,
        "band": "HIGH",
        "is_new": True,
        "turned_up": 1,
        "turned_up_of": 2,
        "late": 0,
        "kept": 1,
        "kept_of": 1,
        "left_in_dispute": 0,
    }


async def test_no_strand_ratio_or_weight_crosses_on_this_response(
    client, session_factory, searcher
):
    """The strands, their raw pairs, their figures and the weights left the
    wire with ADR-0195 §1 — *Answers about results* and the dead strands too."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await a_kept_booked_game(session_factory, subject)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert set(body["reliability"]) == set(A_HUNDRED_AND_NEW)
    assert [
        name
        for name in every_key(body)
        if any(word in name.lower() for word in ("weight", "strand", "pct"))
    ] == []


async def test_a_player_nothing_has_happened_to_reads_a_hundred_and_new(
    client, session_factory, searcher
):
    """**Everyone starts at a hundred**, so the zone is always there: a
    newcomer reads *100 · New* with every count at nought — a newcomer, never a
    failure, and never a blank."""

    subject = await a_member_of_their_group(client, session_factory, searcher)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["reliability"] == A_HUNDRED_AND_NEW
    assert body["skill"] is not None


async def test_your_own_record_carries_the_figure_others_read(
    client, session_factory, searcher
):
    """*How others see you* draws the figure everybody else is shown — a
    penalty nobody can look up is a penalty nobody can fix, and a player
    earning their points back must be able to watch them come back."""

    await a_game_not_come_to(
        session_factory, searcher["id"], uuid4(), sport=Sport.PADEL
    )

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["reliability"] == {
        **A_HUNDRED_AND_NEW,
        "player_score": 75,
        "band": "HIGH",
        "turned_up_of": 1,
        # Their own filter, off, in no group yet (#661).
        "filter": {"hides": 0, "of": 0},
    }
    # A game they Didn't come to is not a game they played: no variety at all.
    assert "variety" not in body


# ---------------------------------------------------------------------------
# What other players said
# ---------------------------------------------------------------------------


async def stars_for(session_factory, subject: UUID, *stars: int) -> None:
    """One card per rater, each giving this person that many stars.

    Written through ``sportsmanship``'s own aggregate rather than an ``INSERT``
    (``docs/adr/0029``), because the collapse *only a rater's most recent stars
    count* lives in that store's key — a row inserted beside the card would be
    this suite arranging away the very thing it wants to read.
    """

    async with session_factory() as session:
        ledger = build_sportsmanship_ledger(session)
        for given in stars:
            at = instant(datetime.now(timezone.utc) - timedelta(days=1))
            await ledger.record(
                SportsmanshipCard.answered(
                    court=SettledCourt(
                        game_id=new_uuid(),
                        rater_id=new_uuid(),
                        others=(subject,),
                        played_at=at,
                    ),
                    given=[StarsGiven(subject_id=subject, stars=given)],
                    at=at,
                )
            )
        await session.commit()


async def test_a_reader_is_told_the_figure_and_how_many_people_it_rests_on(
    client, session_factory, searcher
):
    """**Its own zone, and both numbers in it.** The card above promises
    *counted by the system, not written by people*; this is the one thing on the
    sheet people typed, so it crosses under its own name and never beside the
    reliability counts."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await stars_for(session_factory, subject, 5, 4, 5)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 4.7, "raters": 3}


async def test_it_publishes_from_a_single_rating_with_the_count_beside_it(
    client, session_factory, searcher
):
    """**No minimum**, because the count does a minimum's work honestly: over one
    player the field visibly reads as one person's opinion, which is the same
    discipline the reliability counts take by printing *12 of 13*."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await stars_for(session_factory, subject, 3)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 3.0, "raters": 1}


async def test_a_person_nobody_has_rated_has_the_zone_absent_entirely(
    client, session_factory, searcher
):
    """A **fourth absence**, and a fourth question: rating is a favour, ignoring
    a card costs nothing and nothing records the omission — so this is never a
    nought and never an empty object."""

    subject = await a_member_of_their_group(client, session_factory, searcher)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert "sportsmanship" not in body


async def test_nothing_is_trimmed_at_either_end_of_the_window(
    client, session_factory, searcher
):
    """**No outlier trimming of any kind**, because trimming is the platform
    deciding which raters were wrong — a larger claim than publishing the number,
    and one with no appeal route behind it either."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await stars_for(session_factory, subject, 1, 5, 5)

    body = (await record_of(client, searcher["token"], subject)).json()

    assert body["sportsmanship"] == {"average": 3.7, "raters": 3}


async def test_your_own_record_carries_the_figure_and_the_count(
    client, session_factory, searcher
):
    """**The subject reads what a reader reads** (``docs/adr/0179`` §5).

    The sheet titled *How others see you* draws *Sportsmanship, by players ·
    4,7 / 5 · 3 players* — the published average over the fifty most recent
    raters and how many different people it rests on — exactly as it is drawn
    for anybody else. The subtraction ``docs/adr/0158`` §6 named is real and is
    accepted by name; the band that used to stand in for the figure is gone
    from the shape, asserted as an absence of the whole field.
    """

    await stars_for(session_factory, searcher["id"], 5, 4, 5)

    body = (await own_record(client, searcher["token"])).json()

    assert body["is_self"] is True
    assert body["sportsmanship"] == {"average": 4.7, "raters": 3}
    assert "sportsmanship_band" not in body


async def test_the_subject_and_a_reader_are_served_one_figure(
    client, session_factory, searcher
):
    """**One record, one resolution, whoever is reading.** The figure on your
    own sheet is byte-for-byte the figure somebody in your group is served
    about you — no coarsening, no withheld count, no second fold."""

    group, _ = await their_group(client, searcher)
    subject, token = await players.a_player_on_the_log(
        client, session_factory, "subject", mu=searcher["mu"]
    )
    joined = await join_group(
        client, {"id": subject, "headers": players.auth(token)}, group
    )
    assert joined.status_code == 200, joined.text
    await stars_for(session_factory, subject, 5, 3, 4, 4)

    as_a_reader = (await record_of(client, searcher["token"], subject)).json()
    as_the_subject = (await own_record(client, token)).json()

    assert as_a_reader["is_self"] is False
    assert as_the_subject["is_self"] is True
    assert as_a_reader["sportsmanship"] == {"average": 4.0, "raters": 4}
    assert as_the_subject["sportsmanship"] == as_a_reader["sportsmanship"]


async def test_asking_about_yourself_by_id_is_answered_with_the_figure_too(
    client, session_factory, searcher
):
    """The parameterised route reaches the same sheet: ``is_self`` retitles it
    and moves nothing else, whichever route was called."""

    await stars_for(session_factory, searcher["id"], 1, 2)

    body = (await record_of(client, searcher["token"], searcher["id"])).json()

    assert body["is_self"] is True
    assert body["sportsmanship"] == {"average": 1.5, "raters": 2}


async def test_a_subject_nobody_has_rated_has_the_zone_absent_on_their_own_record(
    client, searcher
):
    """The same absence a stranger's sheet spells, so a newcomer's own record
    draws neither an empty zone nor a nought."""

    body = (await own_record(client, searcher["token"])).json()

    assert "sportsmanship" not in body


async def test_the_sport_asked_for_does_not_move_what_players_said(
    client, session_factory, searcher
):
    """It is about **no sport**, like Player reliability and the variety beside it:
    how somebody is to play with is not a padel fact, and `?sport=` says what the
    sheet is about rather than which record is folded."""

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await stars_for(session_factory, subject, 4, 4)

    padel = (
        await record_of(client, searcher["token"], subject, sport=Sport.PADEL)
    ).json()
    tennis = (
        await record_of(client, searcher["token"], subject, sport=Sport.TENNIS)
    ).json()

    assert (
        padel["sportsmanship"]
        == tennis["sportsmanship"]
        == {
            "average": 4.0,
            "raters": 2,
        }
    )


async def test_stars_move_no_part_of_player_reliability(
    client, session_factory, searcher
):
    """**What other players said does not enter the figure.**

    The record is read twice over the same watched history, once before anybody
    has an opinion and once after three people have given the lowest stars there
    are, and the whole reliability block is identical: no moved figure, no
    moved band, no moved count.

    It matters because Player reliability is what the reliability filter acts
    on (#661): the moment an opinion got into the number a player can see, the
    figure that keeps somebody off a court would be one they could not work
    back up by turning up.
    """

    subject = await a_member_of_their_group(client, session_factory, searcher)
    await a_game_not_come_to(
        session_factory, subject, searcher["id"], sport=Sport.PADEL
    )
    await a_kept_booked_game(session_factory, subject)

    before = (await record_of(client, searcher["token"], subject)).json()["reliability"]

    await stars_for(session_factory, subject, 1, 1, 1)

    after = (await record_of(client, searcher["token"], subject)).json()
    assert after["sportsmanship"] == {"average": 1.0, "raters": 3}
    assert after["reliability"] == before
