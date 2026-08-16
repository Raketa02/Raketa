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

from app.kernel.invariants import InvariantViolated, exhaustive, invariant
from app.kernel.results import Err, Ok, Reason, Result
from app.kernel.sports import SPORT_SPECS, Sport, SportSpec
from app.kernel.time import (
    MINUTES_PER_DAY,
    Clock,
    DayOffset,
    Instant,
    MinuteOfDay,
    Minutes,
    NonexistentLocalTime,
    day_offset,
    elapsed_minutes,
    hours,
    instant,
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
    # time — instants, the integer coordinates, and the one conversion
    "MINUTES_PER_DAY",
    "Clock",
    "DayOffset",
    "Instant",
    "MinuteOfDay",
    "Minutes",
    "NonexistentLocalTime",
    "day_offset",
    "elapsed_minutes",
    "hours",
    "instant",
    "local_minute_of_day",
    "minute_of_day",
    "minutes",
    "shifted",
    "slot_start",
]
