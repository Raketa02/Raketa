"""The one line on a lock screen: which seat it names, what it says, how loud.

ADR-0062, ADR-0065 and ADR-0067. Everything here can be written down without a
repository, a transport or a clock of its own: which of her live seats the line
names, the sentence the server composes for it, whether that sentence alerts,
and when a message is sent at all.

**A notification is a prompt to look, and Now is the only surface that states
what is true** (ADR-0062). Nothing here claims anything: the sentence is past
tense — *a padel seat just opened* — which was true at 16:42, is true at
midnight, and is still true after somebody else takes the seat. That is the
whole of the retraction design, because no platform offers server-side removal
of a delivered alert as a guarantee, and there is therefore nothing in this
module that withdraws, cancels or dismisses anything.

**One live message per player, and the collapse id is the frequency control.**
With no cap in v1, a new seat's message *takes the previous one's place* rather
than stacking beside it. The id is keyed on the player **and scoped to offers**
(ADR-0065): the next kind of message we ever send gets its own id rather than
silently evicting a live seat from a lock screen.

**The server composes this sentence and only this one.** ADR-0022 says the
backend never formats and ADR-0041 says the sentence is the client's; ADR-0075
states the one exception *by class rather than by count* — **copy the server
composes is copy the player reads outside the app** — and this is the class's
only member, because the OS draws it on a locked phone where no client of ours
is running. It ships in English, on that same record.

**The venue is not here and cannot be.** A glance at a lock screen must not
publish where somebody will be, so ``NamedSeat`` carries a zone and never a
club: the sentence is composed from a value that has no venue in it at all,
which makes *never the venue* a property of the type rather than a rule somebody
has to keep.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, final
from uuid import UUID

from app.kernel import (
    Instant,
    IsoWeekday,
    Minutes,
    Sport,
    Zone,
    invariant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
)

from app.modules.now.domain.cascade import Rung, seat_expires_at
from app.modules.now.domain.offers import OfferedSeat


class Platform(str, Enum):
    """Which store the app came from, which is which fields a message carries.

    Two, and the divergence between them is loudness and nothing else
    (ADR-0065). Retraction behaves identically on both — ADR-0062's parity line,
    narrowed to retraction — because past-tense wording survives a flat battery,
    a force-quit and an offline queue, which is where every removal design
    fails.
    """

    IOS = "ios"
    ANDROID = "android"


class TimeSensitiveSetting(str, Enum):
    """What ``UNNotificationSettings.timeSensitiveSetting`` said, as reported.

    **Nothing branches on it, and that is the decision rather than an
    omission** (ADR-0065). The cascade does not demote a player who has revoked:
    she keeps her standby priority, still gets the seat, and still sees the line
    when she next looks. Demoting her would quietly cost her seats as a
    punishment for a settings choice.

    It is **observability**: if a large fraction of players revoke, ADR-0065's
    central judgement was wrong, and reporting the setting is the only way we
    would ever learn it.
    """

    ENABLED = "enabled"
    DISABLED = "disabled"
    #: **A fourth value and not a synonym for ``disabled``** (ADR-0065). A
    #: player on an iPad was never going to get a Focus-piercing alert and has
    #: refused nothing.
    NOT_SUPPORTED = "notSupported"


class InterruptionLevel(str, Enum):
    """How loud one iOS message is. **iOS only** — Android has no such lever.

    ``interruptionLevel`` is a plain field on Expo's push API and on bare APNs
    alike, and [#25] established that Time Sensitive is self-serve and needs no
    Apple approval.
    """

    #: A seat she asked for. Pierces a Focus, justified on **the seat's** clock
    #: and never the match's (ADR-0065): ADR-0061's open call means what expires
    #: inside Apple's hour is the player's chance, not the fixture. The rejected
    #: alternative is a window keyed to the match, which would silence exactly
    #: the Monday-morning case the channel exists for.
    TIME_SENSITIVE = "time-sensitive"
    #: A seat we chose for her. Takes the line without lighting the phone up.
    PASSIVE = "passive"


#: The one Android channel, at ``IMPORTANCE_HIGH``. **Not two** (ADR-0065):
#: *seats you asked for* and *seats we found you* as separate channels reads as
#: a kindness and is a mute switch on rungs 3–7 — the players likeliest to throw
#: it, and the ones the open call depends on — with no server-side signal that
#: it happened.
#:
#: Do Not Disturb still silences it, and **we decline Notification Policy
#: Access**: a second permission prompt, on a platform where two denials are
#: permanent, costs more of the pool than the seats it wins. Nothing in this
#: module asks for it and nothing may.
ANDROID_CHANNEL = "offers"

#: What that channel is registered at, carried here so the server and the app
#: cannot disagree about it. The client creates the channel (`#26`); this is the
#: name and the importance it must be created with.
ANDROID_IMPORTANCE = "high"

#: What the one live message is *about*. The collapse id is keyed on the player
#: **and scoped to this**, so ADR-0062's *"one live message per player, ever"*
#: reads as what it was earned as — a frequency control on **offers** — rather
#: than as a claim on her lock screen forever. Any future message kind gets its
#: own scope and stacks beside this line.
COLLAPSE_SCOPE = "offers"

#: Whether iOS re-states the named seat when **only the count** changed.
#: **Off** (ADR-0067): the rule that a ``passive`` collapse-replacement is
#: genuinely silent is believed on `#36`'s identifier-path measurement, and the
#: APNs hop itself is unmeasured. Shipping it on would buzz a player about the
#: seat she already knows about; shipping it off costs a stale count on a line
#: whose whole job is to make her open Now. `#37` flips it.
#:
#: Annotated rather than inferred so that the branch it gates stays a branch: a
#: ``Literal[False]`` would make the expression below unreachable code.
IOS_COUNT_REFRESH: bool = False

#: The rungs that bought the interruption. **Rung 1 alone** — asking is what
#: buys it (ADR-0062), and it is the second thing joining a standby queue
#: actually buys after the ten-minute head start.
#:
#: Rung 2 is not here although a standing rule is a kind of asking: ADR-0061
#: records that when that feature ships it *auto-joins standby*, so it will feed
#: rung 1 rather than stand beside it.
ASKED_FOR: frozenset[Rung] = frozenset({Rung.STANDBY})

invariant(ASKED_FOR <= set(Rung), "a rung that buys an interruption and does not exist")

#: The sport, as the one sentence says it. A display word rather than the wire
#: code, and it lives here because this module is the only place in the backend
#: that writes English (ADR-0075).
SPORT_WORDS: dict[Sport, str] = {
    Sport.PADEL: "padel",
    Sport.TENNIS: "tennis",
    Sport.SQUASH: "squash",
    Sport.BADMINTON: "badminton",
}

invariant(set(SPORT_WORDS) == set(Sport), "a sport the one sentence cannot name")

#: The weekday, abbreviated, as ADR-0062's own exemplar spells it — *"Tue
#: 19:00"*. It is **not** ``docs/value-formatting.md``'s ``Sat 8``: that table is
#: what two *clients* implement so a value renders identically in both, and this
#: line is composed once by the server and never re-rendered by anybody.
WEEKDAY_WORDS: dict[IsoWeekday, str] = {
    iso_weekday(1): "Mon",
    iso_weekday(2): "Tue",
    iso_weekday(3): "Wed",
    iso_weekday(4): "Thu",
    iso_weekday(5): "Fri",
    iso_weekday(6): "Sat",
    iso_weekday(7): "Sun",
}

invariant(
    set(WEEKDAY_WORDS) == {iso_weekday(day) for day in range(1, 8)},
    "a day of the week the one sentence cannot name",
)


@final
@dataclass(frozen=True)
class PushDevice:
    """One phone that has told us where to reach it.

    Keyed ``(player, token)`` rather than by player alone, because a player may
    hold two phones and both get the line — with **one** collapse id, so each
    phone still shows one message.
    """

    player_id: UUID
    token: str
    platform: Platform
    #: Reported and never acted on. See ``TimeSensitiveSetting``.
    time_sensitive: TimeSensitiveSetting
    registered_at: Instant


@final
@dataclass(frozen=True)
class LiveLine:
    """The one line we occupy on a player's lock screen, and what it owes.

    **One row per player is ADR-0062's rule expressed as a key.** The pending
    half and the live half are two facts about one thing — *a send is owed* and
    *this is what her screen currently says* — so they are one row rather than a
    queue table joined to a state table on the same column.

    ``named_match_id`` is ``None`` for a player whose lock screen holds nothing
    of ours: a phone that has never been sent one, or one we could not reach.
    """

    player_id: UUID
    #: Which match the live message names. **A match and not a seat**, on
    #: ADR-0062's own rule: *"Marek's seat and Zofia's seat are not
    #: distinguishable to somebody who was told 'a padel seat just opened'"* —
    #: what she was told about is the match having room.
    named_match_id: UUID | None = None
    #: When a send is owed, or ``None`` when none is. The whole of the queue.
    due_at: Instant | None = None


@final
@dataclass(frozen=True)
class NamedSeat:
    """The seat the line names, and the whole of what may be said about it.

    **There is no club here, and its absence is the rule rather than an
    omission.** ADR-0062 fixes the line as *sport, time and travel time, never
    the venue* — a glance at somebody's lock screen must not publish where they
    will be — and a value that never carries a venue is a sentence that cannot
    print one. The zone is a **clock face** and not a place: it is what makes
    *19:00* the time on the wall at the club rather than on the reader's phone.

    ``rung`` decides two things and they are the same distinction twice: which
    subject the sentence takes, and whether the message alerts.
    """

    match_id: UUID
    sport: Sport
    start: Instant
    zone: Zone
    #: When the seat stops being takeable — the join cutoff, which is the one
    #: instant ``Match.open_claim`` enforces. It orders the live set and is
    #: never printed: a lock-screen line that counted down would be a claim.
    expires_at: Instant
    rung: Rung

    @property
    def asked_for(self) -> bool:
        """Whether she asked about this match, which is what buys the buzz."""

        return self.rung in ASKED_FOR


@final
@dataclass(frozen=True)
class PushMessage:
    """One message to one device, ready for whatever transport carries it.

    **It carries no data payload at all.** ADR-0062: *"the notification carries
    no truth"* — a tap re-reads live state, and Now is the only surface that
    states it. An id in the payload is a truth a phone could render instead of
    asking, which is exactly the surface this design refuses to create.

    ``interruption_level`` is set exactly when the platform is iOS and
    ``channel_id`` exactly when it is Android, because each is the other
    platform's dead field.
    """

    token: str
    platform: Platform
    #: Keyed to the player and scoped to offers. On Expo this drives both
    #: ``collapseId`` and ``tag``: the first coalesces in transit and only the
    #: second replaces what is already displayed on Android (`#26`).
    collapse_id: str
    body: str
    interruption_level: InterruptionLevel | None = None
    channel_id: str | None = None


def collapse_id_for(player_id: UUID) -> str:
    """The id that makes her next message replace her last one."""

    return f"{COLLAPSE_SCOPE}:{player_id}"


def named_seat(seats: Sequence[OfferedSeat]) -> NamedSeat | None:
    """Which of her live seats the line names, or nothing if she has none.

    **A seat she asked for outranks one we chose for her; soonest-to-expire
    decides inside each group** (ADR-0062). This deliberately differs from the
    offers region on Now, which is ordered soonest-to-expire and nothing else:
    the region shows **every** offer, so its order only decides how far somebody
    scrolls, while this shows **one** and hides the rest behind a count, so its
    order decides which seat she learns about at all. Ranking purely by urgency
    is right when nothing is hidden and wrong when everything else is.

    **The ranking is over the whole live set** and never within one dispatch
    (ADR-0065), which is why this takes her seats rather than a dispatch's: a
    chosen seat arriving while a standby seat holds the line must not take the
    line.

    The third comparator is load-bearing rather than decorative, exactly as
    ``FEED_ORDER``'s fourth is: without a guaranteed-total final key the winner
    is whatever order the rows arrived in, which is the query plan, and two
    ticks over one unchanged set could name different seats.
    """

    if not seats:
        return None
    return _named(min(seats, key=_rank))


def push_body(
    *,
    sport: Sport,
    start: Instant,
    zone: Zone,
    asked_for: bool,
    travel: Minutes | None,
    others: int,
) -> str:
    """The sentence the OS draws on a locked phone.

    **Past tense, always.** *A padel seat just opened* was true at 16:42, is
    true at midnight, and is still true after somebody else takes the seat —
    which is the whole of how a retraction we cannot perform is carried by the
    wording instead (ADR-0062). Nothing here is in the present tense and nothing
    counts down.

    ``asked_for`` chooses the subject, which is ADR-0062's *opening clause*
    folded into the sentence rather than prefixed to it: *the seat you asked
    about* is the one of that record's three openings a v1 build can say. *A
    match you looked at* belongs to rung 4, which ships dark; *a seat near you*
    is a claim the platform cannot make at all — no player has an anchor
    (ADR-0063, `#102`) and rung 6 is *everyone in the band **anywhere*** by
    ADR-0061's own words. One clause folded in beats two clauses that are
    unreachable and false.

    ``travel`` is *"20 min away"*, and **nothing can supply it in v1** — the
    anchor a distance is measured from is optional and no screen asks for it
    (`#129`). It is a parameter rather than a missing sentence for the reason
    ``OfferKind`` keeps a name it never writes: the copy exists the day the fact
    does, rather than a release later.

    ``others`` is the rest of her live set, printed as *"+2 more"*. It
    **undercounts on both platforms** in v1 (ADR-0067) and prints anyway:
    dropping it would make the line's *shape* depend on a measurement, so `#37`
    would return as a copy change and a layout change rather than a flag flip.
    The failure is in the right direction — a hidden seat sends her to Now.
    """

    word = SPORT_WORDS[sport]
    subject = f"The {word} seat you asked about" if asked_for else f"A {word} seat"
    when = _clock_face(start, zone)
    moment = when if travel is None else f"{when}, {travel} min away"
    line = f"{subject} just opened — {moment}. First to take it."
    return line if others <= 0 else f"{line} +{others} more"


def interruption_level_for(named: NamedSeat) -> InterruptionLevel:
    """How loud this seat is on iOS. **Only a seat she asked for buzzes.**

    Rungs 3–7 update the line silently: the count changes and the phone does not
    light up. An interruption whose cause is hidden behind *"+2 more"* is a
    broken interruption, which is why the seat that buzzes is always the seat
    the line names.
    """

    return (
        InterruptionLevel.TIME_SENSITIVE
        if named.asked_for
        else InterruptionLevel.PASSIVE
    )


def message_due(
    *, named: NamedSeat, holding: UUID | None, platform: Platform
) -> bool:
    """Whether this device is sent anything at all.

    **We send only when the named seat changes** (ADR-0065). A chosen seat
    arriving while a standby seat holds the line never takes the line, so the
    only thing that moved is the count — and a count-only update is a message in
    its own right that Android has no way to send quietly. So Android sends
    nothing, and iOS sends a ``passive`` re-statement only when
    ``IOS_COUNT_REFRESH`` is on, which it is not (ADR-0067).

    A player whose lock screen holds nothing of ours has ``holding is None``,
    which is a change by this rule and is meant to be: the first message is the
    one the whole channel exists for.
    """

    if holding != named.match_id:
        return True
    return platform is Platform.IOS and IOS_COUNT_REFRESH


def message_for(
    device: PushDevice, *, named: NamedSeat, others: int, travel: Minutes | None
) -> PushMessage:
    """One composed message for one device. The only place one is built."""

    ios = device.platform is Platform.IOS
    return PushMessage(
        token=device.token,
        platform=device.platform,
        collapse_id=collapse_id_for(device.player_id),
        body=push_body(
            sport=named.sport,
            start=named.start,
            zone=named.zone,
            asked_for=named.asked_for,
            travel=travel,
            others=others,
        ),
        interruption_level=interruption_level_for(named) if ios else None,
        channel_id=None if ios else ANDROID_CHANNEL,
    )


def _rank(seat: OfferedSeat) -> tuple[int, Instant, str]:
    """Asked for, then soonest-to-expire, then the match. Lowest wins."""

    return (
        0 if seat.rung in ASKED_FOR else 1,
        seat_expires_at(seat.record),
        str(seat.match_id),
    )


def _named(seat: OfferedSeat) -> NamedSeat:
    """The winner, narrowed to what may be said about it.

    The narrowing is the point rather than a convenience: everything the
    sentence must not contain — the club, the court, the price, the counting —
    stops here.
    """

    return NamedSeat(
        match_id=seat.match_id,
        sport=seat.record.sport,
        start=seat.record.start,
        zone=seat.where.zone,
        expires_at=seat_expires_at(seat.record),
        rung=seat.rung,
    )


def _clock_face(start: Instant, zone: Zone) -> str:
    """*"Tue 19:00"* — the day and the time on the wall **at the club**.

    An ``Instant`` is UTC and never a clock face, and the zone is a fact about
    the club: a line formatted in the reader's own zone is correct for every
    player at home and wrong for every player travelling, which is the worst
    available bug — invisible in testing, and aimed at exactly the person
    ADR-0063 builds for.
    """

    minute = local_minute_of_day(start, zone)
    day = WEEKDAY_WORDS[local_iso_weekday(start, zone)]
    return f"{day} {minute // 60:02d}:{minute % 60:02d}"
