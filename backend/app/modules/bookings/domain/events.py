"""The Booking stream: one per filled proposal, filed under the proposal's id.

**Born booked** (#541): ``BookingConfirmed`` is the fill's whole record — the
court and its number, the seats and their sides, the club's cut-off as it stood
then, and the Game it opened — written in the transaction that took every seat's
money.

**Never born waiting for a club** (#669; ``docs/adr/0196`` §1): On request's
seven events — the request, the club's yes, no and silence, the request taken
back, and the payment its yes waited on, come or not — are removed with it,
unregistered and undecodable, since the local store is reset with the removal
and only ``local`` has ever run.

**Then the booked game is lived** (#544): ``SeatLeft`` is a player leaving it —
their seat open, the game still the others' — and ``CalledOffAtCutOff`` is a
seat that opened before the club's cut-off still open at it: the game is off,
and everybody still in is named, to be refunded in full. **A player whose
holding was refused** (#639) has their time to fix the card: ``CardToFix``,
then ``CardFixed`` — or, run out, ``SeatLeft`` marked ``card_not_fixed``.

**And an open seat is a rescue** (#545): ``SeatRescued`` is somebody taking it
— the leaver's seat and side, their share held or taken — and
``NoSaidToTheSeat`` is a member the seat was dealt to as a *Seat open* card
saying no to it. **A rescuer whose share was refused keeps a seat** (#640):
``SeatKept``, then ``SeatRescued`` once they pay in time — or, run out,
``KeptSeatRanOut``.

**The club runs it** (#547): ``CourtMoved`` puts the game on another court of
its sport at the same hour — of the same kind, or indoor for an outdoor game
(#671, Q122) — and ``CancelledByClub`` calls it off with the club's reason —
everybody still in named, to be refunded in full. **A club's cancel that a free
court absorbs is a ``CourtMoved``** naming the cancel's reason and the court it
left (#672): the game is never called off, so nothing a cancel does follows.
Both fields are defaulted, version 2 unchanged, so a move recorded before reads
as the club's own.

**The court's kind travels with the court** (#671): ``BookingConfirmed`` and
``CourtMoved`` each carry ``indoor`` beside the court's name, since a booked
game always shows *Court 3 · indoor* and the kind follows a move. Both are at
**version 2** for it, version 1 of each left without a decoder, the local store
reset with the change. ``PlayerCheckedIn``,
the desk's scan of a player's code on the day, is **retired** with desk
check-in (#651): nothing writes it, and it stays registered so a stored row
still decodes.

**A friends game is the stream's second birth** (#751; ``docs/adr/0202``
§5): ``BookedByAFriend`` books the court the moment its sender sends it, the
sender In and every other seat **invited** — held for its friend until a
moment — then ``InvitedSeatAccepted``, ``InvitedSeatDeclined`` or
``InvitedSeatRanOut`` answers each, and ``CalledOffBySender`` is the sender
calling it off before the cut-off. **Its empty seats** (#752): ``SeatInvited``
is a friend invited into one — ended ``InvitedSeatTaken`` when somebody else
took it first — ``SeatOpened`` puts one to the group as a rescue, by its
sender or at the cut-off, and ``CoverWarned`` is the warning its sender gets
a day before the cut-off. Leaving one is the ordinary ``SeatLeft``: what
becomes of the seat — empty, or a rescue — is the fold's to say.

Every event carries ``booking_id``, the stream's own key. Sport and kind travel
as their codes, as a proposal's do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


def _uuids(values: tuple[UUID, ...]) -> tuple[UUID, ...]:
    # JSON hands a list of strings back; the codec coerces a bare ``UUID`` hint
    # and nothing inside a tuple (``proposals``' ``VersionDealt`` does the same).
    return tuple(UUID(str(value)) for value in values)


@dataclass(frozen=True)
class BookingConfirmed:
    """The game is booked: a court is held, every seat paid, a Game opened.

    ``first_side`` and ``second_side`` are the sides **drawn for the most even
    game** (the mechanics §11.7) — one player each in singles, two in doubles.
    ``cut_off`` is the club's free cancellation deadline for this game,
    measured with the club's setting at the moment it filled; a game that filled
    after it was never free to leave.
    """

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court_id: UUID
    #: What the court is called at the club — *Court 2* — given at booking.
    court_name: str
    #: The court's kind, indoor or outdoor (#671, Q122).
    indoor: bool
    sport: str
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    kind: str
    start: datetime
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    cut_off: datetime
    #: The ordinary Game this booking opened.
    game_id: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_side", _uuids(self.first_side))
        object.__setattr__(self, "second_side", _uuids(self.second_side))


@dataclass(frozen=True)
class SeatLeft:
    """A player left the booked game before it started — *Leave the game*
    (#544; the mechanics §13). **Their seat is open**, and the game is still
    the others'. Whether they left before the club's cut-off is read off this
    instant against the booking's ``cut_off``; what it costs them is the
    money's, recorded on their Seat charge."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime
    #: Not the player's own act: their holding was refused and their time to
    #: fix the card ran out (#639). On the record it is a leave before the
    #: cut-off all the same. ``False`` on every leave recorded before.
    card_not_fixed: bool = False


@dataclass(frozen=True)
class CardToFix:
    """**A player's holding was refused** (#639; the mechanics Q113): their
    share, checked at the fill, could not be held at its Holding time. The game
    stays booked, their seat theirs alone **until ``until``** — their time to
    fix the card, never past the cut-off — and nothing is paid meanwhile.
    ``seat_charge_id`` is the payment to confirm, and ``reason`` why it was
    refused (``AUTHENTICATION_REQUIRED``, ``DECLINED``, ``TERMS_NEEDED`` or
    ``NO_METHOD``)."""

    booking_id: UUID
    player_id: UUID
    until: datetime
    seat_charge_id: UUID
    reason: str
    occurred_at: datetime


@dataclass(frozen=True)
class CardFixed:
    """The player fixed their card in time (#639): their share is held until
    the cut-off, and their seat is simply theirs again."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CalledOffAtCutOff:
    """**A game plays full or not at all** (#544; the mechanics §12.3): a seat
    that opened before the club's cut-off was still open at it, so the game is
    off, the court is the club's again, and everybody still in — ``player_ids``
    — is refunded in full. Recorded by the cut-off job, at or after the
    cut-off."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class SeatRescued:
    """Somebody took a seat a leaver left open — a **rescue** (#545; the
    mechanics §10.1). ``player_id`` sits where ``replacing`` sat, on ``side``
    (``A``, the first, or ``B``), and has paid their share; the seat that
    opened first is the one taken. Whether the leaver is refunded now — they
    left after the cut-off — is the money's, recorded on their Seat charge."""

    booking_id: UUID
    player_id: UUID
    side: str
    #: The leaver whose seat this was.
    replacing: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatKept:
    """**A rescuer's share was refused** (#640; the mechanics §10.1, Q113):
    a seat is kept for ``player_id`` alone **until ``until``** — their time to
    fix the card before the cut-off (``to_fix_the_card``), or to pay after it,
    never past the game's start — and offered to nobody else meanwhile. They
    take it as any rescue does, once paid: ``SeatRescued``. ``seat_charge_id``
    is the payment to confirm, and ``reason`` why it was refused
    (``AUTHENTICATION_REQUIRED``, ``DECLINED``, ``TERMS_NEEDED`` or
    ``NO_METHOD``). Recorded again, with the time they had, when the same
    rescuer is refused again within it."""

    booking_id: UUID
    player_id: UUID
    until: datetime
    seat_charge_id: UUID
    reason: str
    to_fix_the_card: bool
    occurred_at: datetime


@dataclass(frozen=True)
class KeptSeatRanOut:
    """The rescuer's time ran out before they paid (#640): the seat kept for
    them is offered again, as before — still theirs to take while it is free,
    and never kept for them again on this game. ``to_fix_the_card`` when their
    time was to fix the card, before the cut-off, rather than to pay."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime
    to_fix_the_card: bool


@dataclass(frozen=True)
class NoSaidToTheSeat:
    """A member the open seat was dealt to as a *Seat open* card swiped it
    away — *not this time* (#545; the mechanics §6.2). Silent and never on
    their record: the card does not come back to their deck."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CourtMoved:
    """The club moved the booked game to another court of its sport at the same
    hour — a broken court, a desk's own reshuffle (#547; the mechanics §16.16).
    The players read the new number and its kind; nothing else about the game
    moves (#671, Q122)."""

    booking_id: UUID
    court_id: UUID
    #: What the new court is called at the club.
    court_name: str
    #: The new court's kind, indoor or outdoor.
    indoor: bool
    occurred_at: datetime
    #: The club's cancel this move took the place of — a **move by cancel**
    #: (#672; the mechanics §16.9, Q122): ``WEATHER``, ``REPAIR``,
    #: ``DOUBLE_BOOKING`` or ``OTHER``, told to the players as why the court it
    #: left can't be played. ``None`` for the club's own Move, and on the rows
    #: recorded before.
    reason: str | None = None
    #: What the club calls the court the game left. ``None`` on the rows
    #: recorded before it was asked.
    moved_from: str | None = None


@dataclass(frozen=True)
class CancelledByClub:
    """The club cancelled the booked game before it started (#547; the
    mechanics §16.9): everybody still in — ``player_ids`` — is refunded in full,
    it is on nobody's record, and the court hour is the club's again.

    ``reason`` is the club's: ``WEATHER``, ``REPAIR``, ``DOUBLE_BOOKING`` or
    ``OTHER`` — told to the players with the refund."""

    booking_id: UUID
    reason: str
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))


@dataclass(frozen=True)
class PlayerCheckedIn:
    """**Retired** (#651; ``docs/adr/0195`` §4, §9): the club's desk scanned a
    player's code, or typed it, on the day of the game (#547).

    Nothing writes it any more. It stays because stored history outlives the
    code that wrote it, and every read of a booking walks its whole stream — so
    a stored row still decodes, and the fold reads it and changes nothing.
    """

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class BookedByAFriend:
    """**A friends game, booked the moment its sender sent it** (#751;
    ``docs/adr/0202`` §5–§6): the Booking's second birth, under an id of its
    own — no proposal precedes it. The court is held, the sender's share and a
    **cover** for every other seat are held or taken on the sender's card, and
    the Game is open with only the sender on it.

    ``first_side`` and ``second_side`` are the sides **as the card drew them**,
    the sender among them: every other player on them holds an **invited
    seat**, theirs alone **until ``invited_until``** — 24 hours from the send,
    never past the cut-off (made before it) or the start (made after it).
    ``pay_mode`` is ``SPLIT_THE_COST`` — each friend pays their own share on
    accepting — or ``WHOLE_COURT``, the sender paying every seat."""

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court_id: UUID
    court_name: str
    indoor: bool
    sport: str
    #: ``COMPETITIVE`` or ``FOR_FUN`` — the sender's choice for this game.
    kind: str
    start: datetime
    share_grosze: int
    sender_id: UUID
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    pay_mode: str
    invited_until: datetime
    cut_off: datetime
    game_id: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_side", _uuids(self.first_side))
        object.__setattr__(self, "second_side", _uuids(self.second_side))


@dataclass(frozen=True)
class InvitedSeatAccepted:
    """An invited friend said yes in time (#751): they are In, on ``side`` —
    the side the card drew them on — and, with *Split the cost*, their own
    share is held or taken on their card, recorded on their Seat charge."""

    booking_id: UUID
    player_id: UUID
    side: str
    occurred_at: datetime
    #: This accept took the last seat: every seat is held now — *It's a
    #: game!*, to all four.
    last_seat: bool = False


@dataclass(frozen=True)
class InvitedSeatDeclined:
    """An invited friend said *Not this time* (#751): their seat is empty, and
    the sender is told they can't make it. What becomes of the seat is #752's
    to say."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class InvitedSeatRanOut:
    """An invited friend's 24 hours ended without an answer (#751): silence is
    *Not this time*, and the sender is told they didn't answer. Recorded by the
    invitations job, at or after the invitation's end."""

    booking_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CalledOffBySender:
    """**The sender called the friends game off before the cut-off** (#751;
    ``docs/adr/0202`` §6): every hold and cover is let go, nobody pays, the
    court is the club's again, and everybody is told — ``player_ids``
    everybody In, the sender among them, ``invited`` every invitee still
    waiting."""

    booking_id: UUID
    player_ids: tuple[UUID, ...]
    invited: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "player_ids", _uuids(self.player_ids))
        object.__setattr__(self, "invited", _uuids(self.invited))


@dataclass(frozen=True)
class SeatInvited:
    """**A friend invited into an empty seat** (#752; the friends mechanics
    §10.1, §10.3): anybody In may invite one of their own friends into a seat
    nobody holds — empty, or open to the group — before or after the cut-off.
    ``seat_of`` names the seat by whose it was: the friend who said *Not this
    time*, didn't answer or left it, or the sender. ``side`` is the seat's.
    Theirs until ``until`` — 24 hours on, never past the cut-off (made before
    it) or the start (made after it) — unless somebody else takes the seat
    first."""

    booking_id: UUID
    player_id: UUID
    invited_by: UUID
    seat_of: UUID
    side: str
    until: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class InvitedSeatTaken:
    """**Somebody else took the seat first** (#752): this friend's invitation
    into it ended — *seat taken* — because ``taken_by`` accepted an invitation
    into the same seat, or took it as a rescue, a moment earlier."""

    booking_id: UUID
    player_id: UUID
    taken_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatOpened:
    """**An empty seat opened to the group** (#752; the friends mechanics
    §10.1, §10.3): from now on it is a **rescue** — a *Seat open* card in the
    decks of members who fit, a row in Fill in, an alert — named by whose it
    was (``seat_of``). Opened by its sender before the cut-off, or, on a game
    its sender's card covers, **by the cut-off** (``at_the_cut_off``) for every
    seat still empty then."""

    booking_id: UUID
    seat_of: UUID
    occurred_at: datetime
    at_the_cut_off: bool = False


@dataclass(frozen=True)
class CoverWarned:
    """**The cover warning** (#752; the friends mechanics §10.2): 24 hours
    before the cut-off of a *Split the cost* game its sender still covers,
    ``seats`` — each named by whose it is — still lacked their own payment, so
    the sender was warned what the cut-off would take from him. **Once per
    game.**"""

    booking_id: UUID
    sender_id: UUID
    seats: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "seats", _uuids(self.seats))


@dataclass(frozen=True)
class NewBookingsSummarised:
    """The club's desk was sent the day's new bookings (#548; the mechanics
    §16.12, the screens B9 — *a new booking: a daily summary*): every game
    booked at the club in the day up to the close of ``day`` (``YYYY-MM-DD``)
    — ``booking_ids`` — once. **Its own stream, one per club per day**, so a
    second process summing up the same day collides on it."""

    summary_id: UUID
    club_id: UUID
    day: str
    booking_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "booking_ids", _uuids(self.booking_ids))
