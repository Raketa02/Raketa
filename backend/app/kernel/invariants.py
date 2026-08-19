"""Broken preconditions, and closed sets that stay closed.

Two mechanisms live here, and the distinction between them is the point
(``docs/adr/0022``).

``invariant`` is for **programmer errors only**. It raises, and it raising in
production means a bug shipped: nothing catches it, and there is nothing for a
caller to do about it. A legitimate domain state where no answer exists is the
*other* mechanism entirely — a ``Result`` returned for the caller to branch on,
in ``app/kernel/results.py``. Confusing the two forces ``try`` into pure code,
or forces every call site to handle a case that cannot happen.

``exhaustive`` is the tail of a ``match`` over a closed union. Adding a member
to such a union then becomes a typechecking failure at every place that does not
handle it, which is exactly the behaviour wanted as the domain's closed sets
grow — the ``Sport`` registry today, the unavailability reasons next.
"""

from __future__ import annotations

from typing import Never, TypeVar, assert_never

_T = TypeVar("_T")


class InvariantViolated(Exception):
    """A precondition of kernel or engine code does not hold — i.e. a bug.

    Kernel-specific deliberately. ``ValueError`` would be caught by the handlers
    modules already wrap around parsing and validation, and a bug that lands in
    a client as a tidy 400 is a bug nobody goes looking for.
    """


def invariant(subject: _T | None, message: str) -> _T:
    """Return ``subject``, or raise because this code was called wrongly.

    ``subject`` is either the value being checked or the condition being
    asserted, and the invariant is broken when it is ``None`` (absent) or
    ``False`` (untrue) — those two singletons and nothing else. ``0``, ``""``
    and ``()`` pass, because each is an ordinary value a caller may well have
    meant, and a guard that rejects a zero price is a guard that gets deleted.

    The return is what makes this worth writing over a bare ``if``: the compiler
    drops the ``None``, so a caller carries the narrowed value forward instead
    of testing it a second time to prove something the raise already
    guarantees::

        spec = invariant(SPORT_SPECS.get(sport), f"no spec for sport: {sport!r}")
        spec.players  # SportSpec, not SportSpec | None

    In the condition form the return is simply ignored::

        invariant(0 <= minute < MINUTES_PER_DAY, f"minute of day: {minute}")

    ``message`` must **name the offending value**. A bare "invalid argument"
    costs an hour of reading call sites to find out which one; "minute of day:
    1500" costs none. It is an f-string at every call site for that reason.

    This is not ``assert``: ``python -O`` strips assert statements, so an
    invariant written as one is a guarantee that evaporates in exactly the
    environment where it mattered.
    """

    if subject is None or subject is False:
        raise InvariantViolated(message)
    return subject


def exhaustive(value: Never) -> Never:
    """Close a ``match`` over a closed union: every member has been handled.

    Put it in the final ``case _`` of a match and the compiler will check the
    claim — a member added to the union later narrows to something that is not
    ``Never``, and every match that does not handle it fails typechecking::

        match sport:
            case Sport.PADEL: ...
            case Sport.TENNIS: ...
            case _: exhaustive(sport)  # a type error while SQUASH is unhandled

    It delegates to ``typing.assert_never``, which is where the runtime raise
    and the value in its message come from. The helper exists so that the tail
    of a match reads from the same import as the union it matches over: the
    kernel is one import path (``app.kernel``) and reaching into ``typing`` for
    half of an idiom is how a second way to spell it starts.
    """

    assert_never(value)
