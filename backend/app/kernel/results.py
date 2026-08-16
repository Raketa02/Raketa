"""Unavailability as a returned value.

The counterpart to ``invariant`` (``app/kernel/invariants.py``), and the split
between them is the one ``docs/adr/0022`` draws along the fence ``import-linter``
already enforces:

* inside the kernel and the engines, a domain condition is **returned**. There
  is no answer to give, the caller is entitled to one, and the caller branches;
* a broken precondition is **raised**, because no caller can recover from a bug;
* outside the fence, modules and adapters raise as they do today and translate
  an ``Unavailable`` into a response.

``Result`` is the returned half: a frozen ``Ok`` or a frozen ``Err``, consumed
by pattern match::

    match price_for(slot):
        case Ok(value):
            ...
        case Err(reason):
            ...

There is no third inhabitant. Two ``@final`` classes, one field each, so a
result can never carry both a value and a reason, and never neither — the state
a success/failure *pair* with two nullable fields has, and the one every caller
of such a pair ends up writing a defensive branch for.

A reason carries a **machine code and its payload, never a sentence**. The
clients own the words: an ``Unavailable`` crosses the wire as ``{kind, …payload}``
and each app renders it in its own language and its own design system, which is
also the only way *"show nothing"* stays a client decision.

**The reasons themselves live elsewhere.** This module owns the machinery and
knows about no particular reason; ``app/kernel/unavailability.py`` owns the
closed union of them, assembled from the modules that produce them. A function
declares the reasons it can actually give — ``Result[Instant,
NonexistentLocalTime]`` — and only code aggregating over all of them names
``Unavailable``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Protocol, TypeAlias, TypeVar, final

_T = TypeVar("_T")
_U = TypeVar("_U")
_R = TypeVar("_R", bound="Reason")


class Reason(Protocol):
    """Why no answer exists: a stable machine code, and payload beside it.

    ``kind`` is the code — lowercase, snake_case, stable across releases, and
    the thing a client switches on. Everything else a concrete reason declares
    is payload: the values a client needs to say what it wants to say, such as
    the date and the local time that does not exist.

    **No sentence.** A reason never carries display text, in any language. One
    string chosen here would be one rendering, and the same refusal reads
    differently in a booking grid, a confirmation sheet and a support export.

    Structural, so a reason is an ordinary frozen dataclass that declares a
    ``kind`` field and inherits nothing.
    """

    @property
    def kind(self) -> str: ...


@final
@dataclass(frozen=True)
class Ok(Generic[_T]):
    """An answer: ``value`` is it."""

    value: _T

    def map(self, transform: Callable[[_T], _U]) -> Ok[_U]:
        """Apply ``transform`` to the value."""

        return Ok(transform(self.value))

    def and_then(self, step: Callable[[_T], Result[_U, _R]]) -> Result[_U, _R]:
        """Run ``step`` on the value, which may itself have no answer."""

        return step(self.value)


@final
@dataclass(frozen=True)
class Err(Generic[_R]):
    """No answer, and ``reason`` says why in machine terms."""

    reason: _R

    def map(self, transform: Callable[[_T], _U]) -> Err[_R]:
        """Nothing to transform. The reason is passed through untouched.

        Untouched literally: the same object, not a rebuilt equal one. A reason
        that were re-wrapped on the way out would lose whatever a producer put
        in its payload, and it would lose it silently, several frames from where
        the failure was decided.
        """

        return self

    def and_then(self, step: Callable[[_T], Result[_U, _R]]) -> Err[_R]:
        """Nothing to run ``step`` on. The reason is passed through untouched."""

        return self


#: A value, or the machine-readable reason there is none.
Result: TypeAlias = Ok[_T] | Err[_R]
