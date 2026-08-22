"""The shared kernel.

The vocabulary and value objects that every bounded context and every engine
reads verbatim, and that neither may redefine. Nothing here may import a module
(``app.modules.*``), the engines layer, FastAPI, SQLAlchemy or any I/O library —
the kernel is the innermost, dependency-free ring. See
``docs/adr/0015-engines-as-a-pure-versioned-layer.md`` and
``docs/adr/0022-kernel-negative-space-and-constant-homes.md``.

**One import path.** Everything public is re-exported here, and nothing outside
this package — tests included — imports a submodule. That is what lets the
kernel be reorganised internally without touching a caller, and it is why no
reader ever has to work out which file a value comes from. ``__all__`` below is
the whole surface: a reviewer watching it grow is watching the kernel grow.
``tests/unit/test_kernel_surface.py`` enforces both halves.

**No deep-freeze helper, deliberately.** Immutability is frozen dataclasses and
tuples, everywhere, with no development-versus-production split — a guard that
only runs in development is a guard that has never been run where it counts.
"""

from app.kernel.holds import (
    Hold,
    HoldKind,
    HoldReason,
    court_hold,
    hold_boundaries,
    is_held,
)
from app.kernel.invariants import InvariantViolated, exhaustive, invariant
from app.kernel.matches import (
    Deadlines,
    HoldPolicy,
    MatchKind,
    MatchRecord,
    OfferKind,
    PayModel,
    Seat,
    Vacancy,
    Viewer,
    born_late,
    committed_on_fill,
    deadlines,
    door_code_at,
    filled,
    held_unpaid,
    is_full,
    is_terminal,
    match_end,
    result_window,
    seat_count,
    vacancy_expires_at,
)
from app.kernel.money import (
    GROSZE_PER_ZLOTY,
    SOLD_FORMATS,
    CardAllowance,
    CardCoversShare,
    ClubCard,
    CourtPrice,
    Grosze,
    NoCard,
    Payable,
    Ratio,
    SeatShare,
    add_grosze,
    apply_fraction,
    at_least_zero,
    card_offset,
    court_price,
    divide_among_players,
    grosze,
    negate_grosze,
    payable_from,
    percent,
    ratio,
    round_half_away_from_zero,
    subtract_grosze,
    zloty,
)
from app.kernel.results import Err, Ok, Reason, Result
from app.kernel.situations import (
    SITUATION_COUNT,
    Situation,
    next_wake_at,
    situation,
)
from app.kernel.sports import SPORT_SPECS, Sport, SportSpec
from app.kernel.time import (
    MINUTES_PER_DAY,
    Clock,
    DayOffset,
    Instant,
    IsoWeekday,
    MinuteOfDay,
    Minutes,
    NonexistentLocalTime,
    Zone,
    day_offset,
    elapsed_minutes,
    hours,
    instant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
    minute_of_day,
    minutes,
    shifted,
    slot_start,
)
from app.kernel.unavailability import Unavailable

__all__ = [
    # sports — the closed registry
    "SPORT_SPECS",
    "Sport",
    "SportSpec",
    # invariants — broken preconditions, and closed sets that stay closed
    "InvariantViolated",
    "exhaustive",
    "invariant",
    # results — unavailability as a returned value
    "Err",
    "Ok",
    "Reason",
    "Result",
    "Unavailable",
    # money — integer grosze, the rounding order, and the exact seat split
    "GROSZE_PER_ZLOTY",
    "SOLD_FORMATS",
    "CardAllowance",
    "CardCoversShare",
    "ClubCard",
    "CourtPrice",
    "Grosze",
    "NoCard",
    "Payable",
    "Ratio",
    "SeatShare",
    "add_grosze",
    "apply_fraction",
    "at_least_zero",
    "card_offset",
    "court_price",
    "divide_among_players",
    "grosze",
    "negate_grosze",
    "payable_from",
    "percent",
    "ratio",
    "round_half_away_from_zero",
    "subtract_grosze",
    "zloty",
    # time — instants, the integer coordinates, and the one conversion
    "MINUTES_PER_DAY",
    "Clock",
    "DayOffset",
    "Instant",
    "IsoWeekday",
    "MinuteOfDay",
    "Minutes",
    "NonexistentLocalTime",
    "Zone",
    "day_offset",
    "elapsed_minutes",
    "hours",
    "instant",
    "iso_weekday",
    "local_iso_weekday",
    "local_minute_of_day",
    "minute_of_day",
    "minutes",
    "shifted",
    "slot_start",
    # matches — the facts one pure function reads, and the five deadlines
    "Deadlines",
    "HoldPolicy",
    "MatchKind",
    "MatchRecord",
    "OfferKind",
    "PayModel",
    "Seat",
    "Vacancy",
    "Viewer",
    "born_late",
    "committed_on_fill",
    "deadlines",
    "door_code_at",
    "filled",
    "held_unpaid",
    "is_full",
    "is_terminal",
    "match_end",
    "result_window",
    "seat_count",
    "vacancy_expires_at",
    # holds — is a court being kept aside, on what terms, and until when
    "Hold",
    "HoldKind",
    "HoldReason",
    "court_hold",
    "hold_boundaries",
    "is_held",
    # situations — one ladder over thirty-six names, and the wake it agrees with
    "SITUATION_COUNT",
    "Situation",
    "next_wake_at",
    "situation",
]
