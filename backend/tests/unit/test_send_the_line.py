"""One owed send: what it reads, what it sends, and what it writes back.

ADR-0062, ADR-0065 and ADR-0067. The domain module decides *which* seat is named
and *what* the line says (`tests/unit/test_push_line.py`); this is about the
reach — that the ranking is over her whole live set rather than over one
dispatch, that a message goes out only when the named seat changes, and that
nothing this job does can take a line off a lock screen.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence
from uuid import UUID, uuid4

import pytest

from app.kernel import (
    Cover,
    Instant,
    MatchRecord,
    Minutes,
    OfferKind,
    grosze,
    hours,
    minutes,
    shifted,
)
from app.modules.now.application.push import (
    PushBatch,
    RegisterDevice,
    RegisterDeviceCommand,
    SendOutcome,
    SendTheLine,
)
from app.modules.now.domain.cascade import Rung
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.push import (
    ANDROID_CHANNEL,
    InterruptionLevel,
    LiveLine,
    Platform,
    PushDevice,
    PushMessage,
    TimeSensitiveSetting,
    collapse_id_for,
)
from app.modules.now.domain.screen import Money, Place

from tests.unit.cascade_doubles import FakePushLines, FixedClock, SpyUnitOfWork
from tests.unit.match_records import a_match, at
from tests.unit.test_push_line import WARSAW

NOW = at(-600)
HER = uuid4()


class StubOffered:
    """`OfferedSeats`, hand-written, recording what it was asked and when."""

    def __init__(self, *rows: OfferedSeat) -> None:
        self._rows = rows
        self.asked: list[tuple[UUID, Instant]] = []

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[OfferedSeat, ...]:
        self.asked.append((player_id, now))
        return self._rows

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> OfferedSeat | None:  # pragma: no cover - never a send's
        raise AssertionError("a send reads her whole live set, never one match")


class StubDevices:
    """`PushDevices`, answering whatever a case registered."""

    def __init__(self, *devices: PushDevice) -> None:
        self._devices = devices
        self.asked: list[UUID] = []

    async def register(self, device: PushDevice) -> None:
        self._devices = self._devices + (device,)

    async def for_player(self, player_id: UUID) -> tuple[PushDevice, ...]:
        self.asked.append(player_id)
        return tuple(
            device for device in self._devices if device.player_id == player_id
        )


class SpySender:
    """The transport, with every batch visible and an optional failure."""

    def __init__(self, *, fails: bool = False, log: list[str] | None = None) -> None:
        self.batches: list[tuple[PushMessage, ...]] = []
        self._fails = fails
        self._log = log

    @property
    def sent(self) -> list[PushMessage]:
        return [message for batch in self.batches for message in batch]

    async def send(self, messages: Sequence[PushMessage]) -> None:
        if self._log is not None:
            self._log.append("sent")
        if self._fails:
            raise RuntimeError("the transport is down")
        self.batches.append(tuple(messages))


class RecordingUnitOfWork(SpyUnitOfWork):
    """The unit of work, with its commit in the same order log as the writes."""

    def __init__(self, log: list[str]) -> None:
        super().__init__()
        self._log = log

    async def commit(self) -> None:
        self._log.append("committed")
        await super().commit()


class RecordingLines(FakePushLines):
    """The queue double, with the order of its writes against the send's."""

    def __init__(self, log: list[str], *lines: LiveLine) -> None:
        super().__init__(*lines)
        self._log = log

    async def replaced(
        self, line: LiveLine, *, named_match_id: UUID, at: Instant
    ) -> None:
        self._log.append("replaced")
        await super().replaced(line, named_match_id=named_match_id, at=at)


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
            "offered_at": at(-700),
            **kwargs,
        }
    )


def a_device(
    platform: Platform = Platform.IOS,
    *,
    player_id: UUID = HER,
    token: str = "ExponentPushToken[aaaaaaaaaaaaaaaaaaaaaa]",
    setting: TimeSensitiveSetting = TimeSensitiveSetting.ENABLED,
) -> PushDevice:
    return PushDevice(
        player_id=player_id,
        token=token,
        platform=platform,
        time_sensitive=setting,
        registered_at=at(-1000),
    )


class Fixture:
    """One player, her live seats, her phones and what her line holds."""

    def __init__(
        self,
        *seats: OfferedSeat,
        devices: Sequence[PushDevice] = (),
        holding: UUID | None = None,
        fails: bool = False,
        now: Instant = NOW,
    ) -> None:
        self.log: list[str] = []
        self.lines = RecordingLines(self.log)
        self.offered = StubOffered(*seats)
        self.devices = StubDevices(*devices)
        self.sender = SpySender(fails=fails, log=self.log)
        self.uow = RecordingUnitOfWork(self.log)
        self.now = now
        self.line = LiveLine(player_id=HER, named_match_id=holding, due_at=now)

    def build(self) -> SendTheLine:
        return SendTheLine(
            lines=self.lines,
            offered=self.offered,
            devices=self.devices,
            sender=self.sender,
            uow=self.uow,
            clock=FixedClock(self.now),
        )

    async def run(self) -> SendOutcome:
        return await self.build().execute(self.line)


# ---------------------------------------------------------------------------
# 1. The first message
# ---------------------------------------------------------------------------


async def test_a_first_seat_reaches_her_phone_and_the_line_records_it() -> None:
    seat = offered(rung=Rung.STANDBY)
    fixture = Fixture(seat, devices=[a_device()])

    assert await fixture.run() is SendOutcome.SENT
    assert len(fixture.sender.sent) == 1
    assert fixture.lines.named == [(HER, seat.match_id, NOW)]
    assert fixture.uow.commits == 1


async def test_the_line_is_written_after_the_send_and_committed_after_that() -> None:
    """A transport that raised must leave the row due, not the line moved.

    The direction this fails in is a message sent twice — which the collapse id
    turns into one line replaced by an identical one — rather than a seat nobody
    hears about.

    The commit is asserted **last** for the other half of the same argument: a
    write that is not committed is a line the next tick sends again, and a
    commit before the write would leave the debt due with the message already
    gone.
    """

    fixture = Fixture(offered(rung=Rung.STANDBY), devices=[a_device()])
    await fixture.run()
    assert fixture.log == ["sent", "replaced", "committed"]


async def test_a_failing_transport_leaves_the_line_untouched() -> None:
    fixture = Fixture(offered(rung=Rung.STANDBY), devices=[a_device()], fails=True)

    with pytest.raises(RuntimeError):
        await fixture.run()
    assert fixture.lines.named == []
    assert fixture.lines.cleared == []
    assert fixture.uow.commits == 0


async def test_she_is_asked_about_at_the_sends_own_instant() -> None:
    """Nothing here is told what changed; the live set is re-read now.

    A send that runs late tells the truth late rather than telling a stale
    truth, which is `RunCascade`'s *"a dispatch is a look, not an instruction"*
    applied to the job downstream of it.
    """

    fixture = Fixture(offered(rung=Rung.STANDBY), devices=[a_device()])
    await fixture.run()
    assert fixture.offered.asked == [(HER, NOW)]


# ---------------------------------------------------------------------------
# 2. The ranking is over the whole live set
# ---------------------------------------------------------------------------


async def test_a_chosen_seat_never_takes_the_line_from_a_standby_seat() -> None:
    """ADR-0065's rule, and the case the whole queue shape exists for.

    A dispatch on rung 6 owes her a send; her lock screen already names the
    standby seat she asked about. Ranking within that dispatch would name the
    chosen seat and buzz her about it; ranking over the live set re-picks the
    standby seat, finds it unchanged, and sends nothing.
    """

    asked = offered(rung=Rung.STANDBY, cut=minutes(30))
    chosen = offered(rung=Rung.CLUB_REGULAR, cut=hours(4))
    fixture = Fixture(
        chosen, asked, devices=[a_device()], holding=asked.match_id
    )

    assert await fixture.run() is SendOutcome.UNCHANGED
    assert fixture.sender.sent == []


async def test_a_count_only_change_leaves_her_line_exactly_as_it_was() -> None:
    """Settled, not replaced: her phone still shows what it showed."""

    asked = offered(rung=Rung.STANDBY)
    fixture = Fixture(
        asked, offered(rung=Rung.IN_THE_BAND, cut=hours(4)),
        devices=[a_device()],
        holding=asked.match_id,
    )

    await fixture.run()
    assert fixture.lines.cleared == [HER]
    assert fixture.lines.named == []
    assert fixture.uow.commits == 1


async def test_the_named_seat_changing_sends_even_when_it_is_a_chosen_one() -> None:
    """Rungs 3–7 *update the line*; what they do not do is alert.

    A silent replacement is still a message: without it the line would go on
    naming a seat that is gone while the count never moved, which is the
    undercount ADR-0067 accepts turned into a line that never changes at all.
    """

    chosen = offered(rung=Rung.CLUB_REGULAR)
    fixture = Fixture(chosen, devices=[a_device()], holding=uuid4())

    assert await fixture.run() is SendOutcome.SENT
    assert fixture.sender.sent[0].interruption_level is InterruptionLevel.PASSIVE


async def test_a_standby_seat_taking_the_line_pierces_a_focus() -> None:
    fixture = Fixture(
        offered(rung=Rung.STANDBY), devices=[a_device()], holding=uuid4()
    )

    await fixture.run()
    assert (
        fixture.sender.sent[0].interruption_level
        is InterruptionLevel.TIME_SENSITIVE
    )


async def test_the_count_is_the_rest_of_her_live_set() -> None:
    named = offered(rung=Rung.STANDBY, cut=minutes(30))
    fixture = Fixture(
        named,
        offered(rung=Rung.IN_THE_BAND, cut=hours(4)),
        offered(rung=Rung.IN_THE_BAND, cut=hours(5)),
        devices=[a_device()],
    )

    await fixture.run()
    assert fixture.sender.sent[0].body.endswith("+2 more")


# ---------------------------------------------------------------------------
# 3. What is live, and what is not
# ---------------------------------------------------------------------------


async def test_a_seat_somebody_else_took_is_not_named() -> None:
    """Liveness is the region's own expression, asked at the send's instant.

    A line naming a filled match is not a *lie* — the wording is past tense —
    but it spends the one line she gets on the seat least worth racing for.
    """

    gone = offered(rung=Rung.STANDBY, record=a_match(paid=4))
    live = offered(rung=Rung.IN_THE_BAND)
    fixture = Fixture(gone, live, devices=[a_device()])

    await fixture.run()
    assert fixture.lines.named == [(HER, live.match_id, NOW)]
    assert "+1 more" not in fixture.sender.sent[0].body


async def test_nothing_live_sends_nothing_and_withdraws_nothing() -> None:
    """Her lock screen keeps the line it holds. There is no way to take it back.

    Nothing is ever removed from a lock screen (ADR-0062), and the line the
    server remembers must match what her phone shows or the next dispatch sends
    the same message to her again.
    """

    held = uuid4()
    fixture = Fixture(
        offered(rung=Rung.STANDBY, record=a_match(paid=4)),
        devices=[a_device()],
        holding=held,
    )

    assert await fixture.run() is SendOutcome.NOTHING_LIVE
    assert fixture.sender.sent == []
    assert fixture.lines.named == []
    assert fixture.lines.cleared == [HER]


async def test_a_player_with_no_phone_keeps_an_empty_line() -> None:
    """Unreachable is not *unchanged*, and the difference is her first message.

    A line marked as naming this match would make her next dispatch a count-only
    change, so registering a token a minute later would leave her never told
    about a seat she is queued for.
    """

    fixture = Fixture(offered(rung=Rung.STANDBY))

    assert await fixture.run() is SendOutcome.UNREACHABLE
    assert fixture.lines.named == []
    assert fixture.lines.cleared == [HER]


async def test_both_her_phones_are_written_to_under_one_collapse_id() -> None:
    fixture = Fixture(
        offered(rung=Rung.STANDBY),
        devices=[
            a_device(Platform.IOS, token="ios-token"),
            a_device(Platform.ANDROID, token="android-token"),
        ],
    )

    await fixture.run()
    assert len(fixture.sender.batches) == 1
    assert {message.token for message in fixture.sender.sent} == {
        "ios-token",
        "android-token",
    }
    assert {message.collapse_id for message in fixture.sender.sent} == {
        collapse_id_for(HER)
    }
    assert {message.channel_id for message in fixture.sender.sent} == {
        None,
        ANDROID_CHANNEL,
    }


async def test_nobody_elses_phone_is_written_to() -> None:
    fixture = Fixture(
        offered(rung=Rung.STANDBY),
        devices=[a_device(token="hers"), a_device(player_id=uuid4(), token="his")],
    )

    await fixture.run()
    assert [message.token for message in fixture.sender.sent] == ["hers"]


async def test_the_message_never_names_the_club_the_row_carries() -> None:
    """The seam where *never the venue* is either kept or lost.

    The row the send reads carries a club name — the offers region prints one —
    and the composed body must not, which is what the narrowing into
    `NamedSeat` buys.
    """

    seat = offered(rung=Rung.STANDBY)
    fixture = Fixture(seat, devices=[a_device()])

    await fixture.run()
    assert seat.where.club_name not in fixture.sender.sent[0].body


async def test_a_revoked_setting_changes_nothing_about_the_message() -> None:
    """Reported and never branched on (ADR-0065).

    A player who has revoked Time Sensitive still gets the seat and still gets
    the alert level the seat's rung earns: demoting her would quietly cost her
    seats as a punishment for a settings choice.
    """

    bodies = set()
    levels = set()
    for setting in TimeSensitiveSetting:
        fixture = Fixture(
            offered(rung=Rung.STANDBY, match_id=HER),
            devices=[a_device(setting=setting)],
        )
        await fixture.run()
        bodies.add(fixture.sender.sent[0].body)
        levels.add(fixture.sender.sent[0].interruption_level)
    assert len(bodies) == 1
    assert levels == {InterruptionLevel.TIME_SENSITIVE}


# ---------------------------------------------------------------------------
# 4. The batch
# ---------------------------------------------------------------------------


class SpySend:
    """`SendTheLine` narrowed to what the batch does with it."""

    def __init__(self, *, failing: set[UUID] | None = None) -> None:
        self.ran: list[UUID] = []
        self._failing = failing or set()

    async def execute(self, line: LiveLine) -> SendOutcome:
        self.ran.append(line.player_id)
        if line.player_id in self._failing:
            raise RuntimeError("this phone is unreachable")
        return SendOutcome.SENT


def a_batch(lines: FakePushLines, send: SpySend, uow: SpyUnitOfWork) -> PushBatch:
    return PushBatch(
        lines=lines,
        send=send,  # type: ignore[arg-type]
        uow=uow,
        clock=FixedClock(NOW),
    )


async def test_the_batch_runs_every_owed_send() -> None:
    her, him = uuid4(), uuid4()
    lines = FakePushLines(
        LiveLine(player_id=her, due_at=NOW),
        LiveLine(player_id=him, due_at=shifted(NOW, minutes(-1))),
    )
    send = SpySend()

    assert await a_batch(lines, send, SpyUnitOfWork()).execute(worker_id="w") == 2
    assert sorted(send.ran, key=str) == sorted([her, him], key=str)


async def test_a_send_that_is_not_owed_yet_is_not_taken() -> None:
    lines = FakePushLines(
        LiveLine(player_id=uuid4(), due_at=shifted(NOW, minutes(1)))
    )
    send = SpySend()

    assert await a_batch(lines, send, SpyUnitOfWork()).execute(worker_id="w") == 0
    assert send.ran == []


async def test_a_line_owing_nothing_is_not_taken() -> None:
    lines = FakePushLines(LiveLine(player_id=uuid4(), named_match_id=uuid4()))
    send = SpySend()

    assert await a_batch(lines, send, SpyUnitOfWork()).execute(worker_id="w") == 0


async def test_one_failing_send_does_not_stop_the_tick() -> None:
    """Two phones have nothing to do with each other.

    The rollback is what makes *the rest are run* true rather than hopeful: a
    session left holding a failed statement fails every send after it, and the
    tick would read as one broken phone rather than as a broken tick.
    """

    her, him = sorted((uuid4(), uuid4()), key=str)
    lines = FakePushLines(
        LiveLine(player_id=her, due_at=NOW), LiveLine(player_id=him, due_at=NOW)
    )
    send = SpySend(failing={her})
    uow = SpyUnitOfWork()

    assert await a_batch(lines, send, uow).execute(worker_id="w") == 1
    assert send.ran == [her, him]
    assert uow.rollbacks == 1


# ---------------------------------------------------------------------------
# 5. Registering a phone
# ---------------------------------------------------------------------------


async def test_registering_stamps_the_moment_and_commits() -> None:
    devices = StubDevices()
    uow = SpyUnitOfWork()

    await RegisterDevice(devices=devices, uow=uow, clock=FixedClock(NOW)).execute(
        RegisterDeviceCommand(
            player_id=HER,
            token="ExponentPushToken[x]",
            platform=Platform.ANDROID,
            time_sensitive=TimeSensitiveSetting.NOT_SUPPORTED,
        )
    )

    (device,) = await devices.for_player(HER)
    assert device.registered_at == NOW
    assert device.platform is Platform.ANDROID
    assert device.time_sensitive is TimeSensitiveSetting.NOT_SUPPORTED
    assert uow.commits == 1


async def test_registering_sends_nothing() -> None:
    """The first message a phone can receive is the next one a dispatch owes.

    A send on registration would be this channel deciding to interrupt somebody
    because she opened the app, which is the opposite of *only a seat you asked
    for*.
    """

    devices = StubDevices()
    use_case = RegisterDevice(
        devices=devices, uow=SpyUnitOfWork(), clock=FixedClock(NOW)
    )
    assert not hasattr(use_case, "_sender")
    assert not hasattr(use_case, "_lines")
