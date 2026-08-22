"""An effective-dated series: the row in force, and the rows that were.

ADR-0077 gives history to three named facts rather than to the aggregate, and
this is the mechanism all three share. A change does **not** update in place: it
closes the current row and opens a new one, carrying a validity interval. The
fold is *the row whose interval contains now*, not a replay, which is what makes
this event sourcing's non-drift property without event sourcing's machinery —
the current value is not a copy kept beside the history, it **is** the open row.

**At most one open row, and it is the last one.** That is the invariant the
partial unique index (``(key) WHERE valid_to IS NULL``) enforces at the database
and this type enforces in memory. They are not redundant: one stops a bug from
reaching disk, the other stops it from being constructed.

**Intervals are half-open ``[valid_from, valid_to)``**, the same convention
``docs/adr/0035`` fixed for a reservation's claimed range — a row closed at
16:00 and its successor opened at 16:00 do not both contain 16:00, so *what was
the hold cap on Friday at 16:00* has exactly one answer at the instant of the
change as well as either side of it.

**A closed series is a legitimate state.** Retiring a court closes the open row
and opens nothing (ADR-0079: *retired, never deleted*), so ``current`` is
``None`` and the history still parses. That is the shape ``inventoryLost`` is
explained out of.

**Nothing in the domain reads the past.** ``as_of`` exists because a human
reconstructing an outcome is the audience ADR-0077 names, and it is deliberately
*not* what the hold ladder calls: policy is read as of now, always. See
``Club.policy_now``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

from app.kernel import Instant

from app.modules.clubs.domain.value_objects import SYSTEM, ChangedBy

T = TypeVar("T")


@dataclass(frozen=True)
class Version(Generic[T]):
    """One row of a series: a value, when it took effect, and who changed it.

    ``valid_to`` is ``None`` while the row is in force. ``changed_by`` is on
    every row from the first migration — ADR-0077's argument is that a column
    added later leaves every pre-existing row claiming an actor it never had,
    and a nullable one cannot distinguish *we did not know* from *nobody did
    it*. In v1 it reads ``system`` and says so.
    """

    value: T
    valid_from: Instant
    valid_to: Instant | None = None
    changed_by: ChangedBy = SYSTEM

    def __post_init__(self) -> None:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError(
                f"a version cannot end before it began: "
                f"{self.valid_from.isoformat()} -> {self.valid_to.isoformat()}"
            )

    @property
    def is_open(self) -> bool:
        return self.valid_to is None

    def contains(self, moment: Instant) -> bool:
        """Half-open: the closing instant belongs to the next row, not this one."""

        if moment < self.valid_from:
            return False
        return self.valid_to is None or moment < self.valid_to


@dataclass(frozen=True)
class Series(Generic[T]):
    """Every version of one fact, oldest first, with at most one still open.

    Immutable: ``opened`` and ``closed`` return a new series. A caller therefore
    cannot half-apply a change, which is the in-memory half of the hazard
    ADR-0077 flags as *"every write to a history-bearing fact is now two
    statements, and getting it wrong is silent."* The other half is the
    repository's, and the partial unique index is what makes it loud.
    """

    versions: tuple[Version[T], ...] = ()

    def __post_init__(self) -> None:
        previous: Version[T] | None = None
        for index, version in enumerate(self.versions):
            if previous is not None:
                if previous.valid_to is None:
                    raise ValueError(
                        "a series may hold only one open version, and it is the "
                        f"last: version {index - 1} of {len(self.versions)} is open"
                    )
                if version.valid_from < previous.valid_to:
                    raise ValueError(
                        "a series' versions may not overlap: version "
                        f"{index} begins at {version.valid_from.isoformat()}, "
                        f"before version {index - 1} ended at "
                        f"{previous.valid_to.isoformat()}"
                    )
            previous = version

    def __iter__(self) -> Iterator[Version[T]]:
        return iter(self.versions)

    def __len__(self) -> int:
        return len(self.versions)

    @property
    def open_version(self) -> Version[T] | None:
        """The row in force, or nothing — a retired court has no open row."""

        if self.versions and self.versions[-1].is_open:
            return self.versions[-1]
        return None

    @property
    def current(self) -> T | None:
        version = self.open_version
        return None if version is None else version.value

    def as_of(self, moment: Instant) -> T | None:
        """What this fact was at ``moment``, for a human reconstructing an outcome.

        Not for the domain. ADR-0077: *"a policy value is always read as of
        now"*, and making Clubs temporally queryable by the ladder would put a
        second aggregate's fold inside the derivation kernel.
        """

        for version in self.versions:
            if version.contains(moment):
                return version.value
        return None

    def opened(
        self, value: T, *, at: Instant, changed_by: ChangedBy = SYSTEM
    ) -> "Series[T]":
        """Close whatever is in force and open a new row from ``at``.

        One operation rather than two, so *close* and *open* cannot be written
        apart and get out of step. Re-opening at an instant before the row in
        force began is refused rather than silently reordering history.
        """

        closed = self._closed_at(at)
        return Series(
            closed.versions
            + (Version(value=value, valid_from=at, changed_by=changed_by),)
        )

    def closed(self, *, at: Instant) -> "Series[T]":
        """End the series without opening anything — a retirement.

        The closing instant is written onto the row that was in force; the actor
        that closed it is not recorded separately, because a close is always
        half of something else (a change, which records its opener's actor, or a
        retirement, whose actor is the same one).
        """

        return self._closed_at(at)

    def _closed_at(self, moment: Instant) -> "Series[T]":
        version = self.open_version
        if version is None:
            return self
        if moment < version.valid_from:
            raise ValueError(
                f"a version cannot be closed at {moment.isoformat()}, before it "
                f"opened at {version.valid_from.isoformat()}"
            )
        return Series(
            self.versions[:-1]
            + (
                Version(
                    value=version.value,
                    valid_from=version.valid_from,
                    valid_to=moment,
                    changed_by=version.changed_by,
                ),
            )
        )


def series_from(
    value: T, *, at: Instant, changed_by: ChangedBy = SYSTEM
) -> Series[T]:
    """A series that has never changed: one open row, from ``at``."""

    return Series((Version(value=value, valid_from=at, changed_by=changed_by),))
