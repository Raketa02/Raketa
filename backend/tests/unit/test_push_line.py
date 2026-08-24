"""The one line: which seat it names, what it says, how loud, and when at all.

ADR-0062, ADR-0065 and ADR-0067. Everything here is a pure function over a live
set and a device, which is the whole reason the ranking and the sentence live in
``domain/push.py`` rather than in the send: *which seat she learns about* is the
most consequential decision this channel makes, and it is decided without a
database.

**The sentences are pinned to their literals.** A copy test comparing a composed
string against the same expression that composed it is the *constant compared
against itself* family, and it passes on a line that says the wrong thing in
every case. So each rendering is written out here in full, and the vocabulary
this line must never use has its own negative control.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import (
    Cover,
    Instant,
    MatchRecord,
    Minutes,
    OfferKind,
    Sport,
    deadlines,
    grosze,
    hours,
    instant,
    iso_weekday,
    minutes,
    shifted,
)
from app.modules.now.domain.cascade import Rung, seat_expires_at
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.push import (
    ANDROID_CHANNEL,
    ANDROID_IMPORTANCE,
    ASKED_FOR,
    COLLAPSE_SCOPE,
    IOS_COUNT_REFRESH,
    SPORT_WORDS,
    WEEKDAY_WORDS,
    InterruptionLevel,
    NamedSeat,
    Platform,
    PushDevice,
    TimeSensitiveSetting,
    collapse_id_for,
    interruption_level_for,
    message_due,
    message_for,
    named_seat,
    push_body,
)
from app.modules.now.domain.screen import Money, Place

from tests.unit.match_records import START, a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
LONDON = ZoneInfo("Europe/London")

#: A Tuesday at 19:00 on the wall in Warsaw, which is ADR-0062's own exemplar.
#: Written as the UTC instant it really is — 17:00 — so that a composer reading
#: the moment in its own zone renders `Tue 17:00` and this file goes red.
TUESDAY_19 = instant(datetime(2026, 8, 25, 17, 0, tzinfo=timezone.utc))


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Kraków",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def offered(
    *,
    rung: Rung = Rung.IN_THE_BAND,
    cut: Minutes = minutes(30),
    match_id: UUID | None = None,
    record: MatchRecord | None = None,
    **kwargs,
) -> OfferedSeat:
    """One seat she has been offered, at a club that closes joining at ``cut``."""

    base = record if record is not None else a_match(paid=3)
    return OfferedSeat(
        **{
            "match_id": match_id or uuid4(),
            "vacancy_id": uuid4(),
            "record": replace(base, policy=replace(base.policy, join_cut=cut)),
            "where": a_place(),
            "kind": OfferKind.OPEN,
            "rung": rung,
            "share": Money(amount=grosze(3800)),
            "court_total": Money(amount=grosze(15200)),
            "offered_at": at(-600),
            **kwargs,
        }
    )


def a_device(
    platform: Platform = Platform.IOS,
    *,
    player_id: UUID | None = None,
    token: str = "ExponentPushToken[aaaaaaaaaaaaaaaaaaaaaa]",
) -> PushDevice:
    return PushDevice(
        player_id=player_id or uuid4(),
        token=token,
        platform=platform,
        time_sensitive=TimeSensitiveSetting.ENABLED,
        registered_at=at(-1000),
    )


def a_named(
    *,
    rung: Rung = Rung.IN_THE_BAND,
    sport: Sport = Sport.PADEL,
    start: Instant = TUESDAY_19,
    zone: ZoneInfo = WARSAW,
) -> NamedSeat:
    return NamedSeat(
        match_id=uuid4(),
        sport=sport,
        start=start,
        zone=zone,
        expires_at=shifted(start, minutes(-30)),
        rung=rung,
    )


# ---------------------------------------------------------------------------
# 1. Which seat the line names
# ---------------------------------------------------------------------------


def test_a_seat_she_asked_for_outranks_one_we_chose_for_her() -> None:
    """ADR-0062's ranking, and the case that tells it from soonest-to-expire.

    The chosen seat dies **first**, so a ranking that led on urgency would name
    it — which is the offers region's rule and deliberately not this one: the
    region shows every offer and only decides how far somebody scrolls, and this
    shows one and hides the rest.
    """

    asked = offered(rung=Rung.STANDBY, cut=minutes(30))
    chosen = offered(rung=Rung.CLUB_REGULAR, cut=hours(4))
    assert seat_expires_at(chosen.record) < seat_expires_at(asked.record)

    for order in ((asked, chosen), (chosen, asked)):
        assert named_seat(order) is not None
        assert named_seat(order).match_id == asked.match_id


def test_soonest_to_expire_decides_inside_a_group() -> None:
    dying = offered(rung=Rung.IN_THE_BAND, cut=hours(4))
    later = offered(rung=Rung.IN_THE_BAND, cut=minutes(30))
    assert named_seat((later, dying)).match_id == dying.match_id


def test_soonest_to_expire_decides_inside_the_asked_for_group_too() -> None:
    """Two standby seats, so the first comparator cannot be what separates them."""

    dying = offered(rung=Rung.STANDBY, cut=hours(4))
    later = offered(rung=Rung.STANDBY, cut=minutes(30))
    assert named_seat((later, dying)).match_id == dying.match_id


def test_the_match_breaks_a_tie_and_the_order_is_total() -> None:
    """Two seats at one club share a cutoff to the second.

    Without a total final key the winner is whatever order the rows arrived in,
    which is the query plan — and two ticks over one unchanged set could then
    name different seats and send a message for it.
    """

    first, second = sorted((uuid4(), uuid4()), key=str)
    rows = (
        offered(rung=Rung.IN_THE_BAND, match_id=second),
        offered(rung=Rung.IN_THE_BAND, match_id=first),
    )
    assert named_seat(rows).match_id == first
    assert named_seat(tuple(reversed(rows))).match_id == first


def test_nothing_live_names_nothing() -> None:
    assert named_seat(()) is None


def test_the_named_seat_carries_no_club_and_no_price() -> None:
    """The venue stops here, which is what makes *never the venue* a type.

    ADR-0062 is explicit that a glance at a lock screen must not publish where
    somebody will be, and the sentence is composed from this value: a field that
    is not on it is a field the copy cannot reach for.
    """

    row = offered(rung=Rung.STANDBY)
    named = named_seat((row,))
    carried = set(vars(named))
    assert carried == {"match_id", "sport", "start", "zone", "expires_at", "rung"}
    assert row.where.club_name not in str(named)


def test_the_named_seat_expires_at_the_join_cutoff() -> None:
    row = offered(rung=Rung.STANDBY, cut=hours(4))
    assert named_seat((row,)).expires_at == deadlines(row.record).join_cut


def test_asked_for_is_rung_one_and_nothing_else() -> None:
    assert ASKED_FOR == {Rung.STANDBY}
    assert named_seat((offered(rung=Rung.STANDBY),)).asked_for is True
    for rung in set(Rung) - ASKED_FOR:
        assert named_seat((offered(rung=rung),)).asked_for is False, rung


# ---------------------------------------------------------------------------
# 2. The sentence
# ---------------------------------------------------------------------------


def a_body(**kwargs) -> str:
    return push_body(
        **{
            "sport": Sport.PADEL,
            "start": TUESDAY_19,
            "zone": WARSAW,
            "asked_for": False,
            "travel": None,
            "others": 0,
            **kwargs,
        }
    )


def test_a_seat_we_chose_reads_as_the_adr_writes_it() -> None:
    assert a_body() == "A padel seat just opened — Tue 19:00. First to take it."


def test_a_seat_she_asked_about_says_so() -> None:
    """ADR-0062's *opening clause*, folded into the subject rather than prefixed.

    Of that record's three openings this is the only one a v1 build can say: *a
    match you looked at* belongs to rung 4, which ships dark, and *a seat near
    you* is a claim the platform cannot make — no player has an anchor, and rung
    6 is *everyone in the band anywhere*.
    """

    assert a_body(asked_for=True) == (
        "The padel seat you asked about just opened — Tue 19:00. First to take it."
    )


def test_travel_time_is_a_clause_and_not_a_second_sentence() -> None:
    assert a_body(travel=minutes(20)) == (
        "A padel seat just opened — Tue 19:00, 20 min away. First to take it."
    )


def test_the_rest_are_a_count() -> None:
    assert a_body(others=2) == (
        "A padel seat just opened — Tue 19:00. First to take it. +2 more"
    )
    assert a_body(others=1).endswith("+1 more")


def test_one_live_seat_prints_no_count() -> None:
    """A count of zero is *"+0 more"*, which reads as a bug on a lock screen."""

    assert "more" not in a_body(others=0)
    assert "more" not in a_body(others=-1)


def test_the_clock_face_is_the_clubs_and_never_the_readers() -> None:
    """A line formatted in the reader's zone is right at home and wrong abroad.

    The same instant, the same club, two zones: one of these is the club's wall
    clock and the other is a phone's. Only the first may ever be printed.
    """

    assert "Tue 19:00" in a_body(zone=WARSAW)
    assert "Tue 18:00" in a_body(zone=LONDON)


def test_every_sport_can_name_itself() -> None:
    assert set(SPORT_WORDS) == set(Sport)
    for sport in Sport:
        assert a_body(sport=sport).startswith(f"A {SPORT_WORDS[sport]} seat")


def test_every_day_of_the_week_can_name_itself() -> None:
    assert [WEEKDAY_WORDS[iso_weekday(day)] for day in range(1, 8)] == [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ]


def test_the_line_is_past_tense_and_claims_nothing() -> None:
    """The negative control on the vocabulary, which is the retraction design.

    *A padel seat just opened* was true at 16:42, is true at midnight, and is
    still true after somebody else takes the seat — so there is nothing to
    withdraw. A present-tense claim, a hold, a countdown or a promise that the
    seat is still there would each be a sentence that goes stale on a surface
    the server cannot reach.
    """

    for body in (a_body(), a_body(asked_for=True, travel=minutes(20), others=3)):
        assert "just opened" in body
        for forbidden in (
            "is available",
            "is free",
            "is waiting",
            "still",
            "held for you",
            "nobody else",
            "expires",
            "hurry",
        ):
            assert forbidden not in body.lower(), forbidden


def test_the_line_never_names_the_venue() -> None:
    """Sport, time and travel time — *never the venue* (ADR-0062).

    The signature is the real guarantee; this is the assertion that would notice
    a club name arriving through some other argument.
    """

    body = a_body(asked_for=True, travel=minutes(20), others=2)
    for word in ("Club", "Kraków", "court", "Court"):
        assert word not in body, word


# ---------------------------------------------------------------------------
# 3. How loud
# ---------------------------------------------------------------------------


def test_only_a_seat_she_asked_for_pierces_a_focus() -> None:
    assert (
        interruption_level_for(a_named(rung=Rung.STANDBY))
        is InterruptionLevel.TIME_SENSITIVE
    )


@pytest.mark.parametrize("rung", sorted(set(Rung) - ASKED_FOR, key=lambda r: r.value))
def test_a_seat_we_chose_updates_the_line_silently(rung: Rung) -> None:
    assert interruption_level_for(a_named(rung=rung)) is InterruptionLevel.PASSIVE


def test_an_ios_message_carries_a_level_and_no_channel() -> None:
    message = message_for(
        a_device(Platform.IOS), named=a_named(rung=Rung.STANDBY), others=0, travel=None
    )
    assert message.interruption_level is InterruptionLevel.TIME_SENSITIVE
    assert message.channel_id is None


def test_an_android_message_carries_one_channel_and_no_level() -> None:
    """`interruptionLevel` is iOS-only and a channel is Android's only lever.

    One channel and not two: *seats you asked for* and *seats we found you* as
    separate channels is a mute switch on rungs 3–7, with no server-side signal
    that it happened.
    """

    for rung in (Rung.STANDBY, Rung.IN_THE_BAND):
        message = message_for(
            a_device(Platform.ANDROID), named=a_named(rung=rung), others=0, travel=None
        )
        assert message.channel_id == ANDROID_CHANNEL
        assert message.interruption_level is None
    assert ANDROID_IMPORTANCE == "high"


def test_both_platforms_read_the_same_sentence() -> None:
    """The wording is what carries the retraction, so it cannot diverge.

    ADR-0065 narrows ADR-0062's parity line to **retraction** and diverges the
    platforms on loudness alone; a body that differed would be a second copy
    table nobody named.
    """

    named = a_named(rung=Rung.STANDBY)
    bodies = {
        message_for(
            a_device(platform), named=named, others=1, travel=None
        ).body
        for platform in Platform
    }
    assert len(bodies) == 1


def test_the_collapse_id_is_the_players_and_is_scoped_to_offers() -> None:
    """*One live message per player* — and the next kind of message stacks.

    Keyed on the player alone it would read literally, and the first message of
    any other kind we ever send would silently evict a live seat from a lock
    screen (ADR-0065).
    """

    her, him = uuid4(), uuid4()
    assert collapse_id_for(her) == collapse_id_for(her)
    assert collapse_id_for(her) != collapse_id_for(him)
    assert collapse_id_for(her).startswith(f"{COLLAPSE_SCOPE}:")
    assert str(her) in collapse_id_for(her)


def test_two_phones_share_one_collapse_id() -> None:
    """A player with two phones is one line, twice — not two lines."""

    her = uuid4()
    messages = [
        message_for(
            a_device(platform, player_id=her, token=f"token-{platform.value}"),
            named=a_named(),
            others=0,
            travel=None,
        )
        for platform in Platform
    ]
    assert {message.collapse_id for message in messages} == {collapse_id_for(her)}
    assert {message.token for message in messages} == {"token-ios", "token-android"}


def test_a_message_carries_no_data_payload() -> None:
    """The notification carries no truth; a tap re-reads live state (ADR-0062).

    An id in the payload is a truth a phone could render instead of asking,
    which is the surface this design exists to refuse.
    """

    message = message_for(
        a_device(), named=a_named(rung=Rung.STANDBY), others=2, travel=None
    )
    assert set(vars(message)) == {
        "token",
        "platform",
        "collapse_id",
        "body",
        "interruption_level",
        "channel_id",
    }


# ---------------------------------------------------------------------------
# 4. When anything is sent at all
# ---------------------------------------------------------------------------


def test_a_changed_named_seat_is_sent_on_both_platforms() -> None:
    named = a_named()
    for platform in Platform:
        assert message_due(named=named, holding=uuid4(), platform=platform)


def test_a_first_message_is_a_change() -> None:
    for platform in Platform:
        assert message_due(named=a_named(), holding=None, platform=platform)


def test_a_count_only_change_is_sent_on_neither_platform() -> None:
    """ADR-0067's flag, off, and the reason it is a flag rather than a deletion.

    Believing that a `passive` collapse-replacement is silent and shipping the
    message it buys are two acts. If the APNs hop diverges, shipping it on
    buzzes a player about the seat she already knows about; shipping it off
    costs a stale count on a line whose whole job is to make her open Now.
    """

    assert IOS_COUNT_REFRESH is False
    named = a_named()
    for platform in Platform:
        assert not message_due(
            named=named, holding=named.match_id, platform=platform
        )


def test_the_count_refresh_when_it_lands_is_ios_only(monkeypatch) -> None:
    """`Raketa02/Raketa#37` flips one flag, and Android is unmoved by it.

    Android has no way to send a count-only update quietly at all, so the branch
    behind the flag must never reach it — which is what makes a failed
    measurement collapse both platforms onto one rule rather than produce a
    second design.
    """

    monkeypatch.setattr(
        "app.modules.now.domain.push.IOS_COUNT_REFRESH", True, raising=True
    )
    named = a_named()
    assert message_due(named=named, holding=named.match_id, platform=Platform.IOS)
    assert not message_due(
        named=named, holding=named.match_id, platform=Platform.ANDROID
    )


def test_the_three_reported_settings_are_three_and_not_two() -> None:
    """`notSupported` is a fourth state and not a synonym for a refusal.

    A player on an iPad was never going to get a Focus-piercing alert and has
    refused nothing — and nothing in this module reads the value at all, which
    is `test_push_never_retracts.py`'s walk.
    """

    assert {setting.value for setting in TimeSensitiveSetting} == {
        "enabled",
        "disabled",
        "notSupported",
    }


def test_the_start_the_offers_region_orders_by_is_the_one_this_ranks_by() -> None:
    """One answer to *when does this seat die*, read from both ends.

    The region orders by `cascade.seat_expires_at` and so does this; a channel
    with its own reading would eventually name a seat the region has dropped.
    """

    row = offered(rung=Rung.STANDBY, cut=hours(4), record=a_match(paid=3))
    assert named_seat((row,)).expires_at == seat_expires_at(row.record)
    assert row.record.start == START
