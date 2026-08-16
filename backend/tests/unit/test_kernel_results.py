"""`Result`: the returned half of the kernel's two mechanisms.

A legitimate domain state where no answer exists is a value the caller branches
on, never an exception — which is what keeps `try` out of pure code and out of
the engines. What is asserted here is the shape of that value and what mapping
and chaining do to it; that a *sentence* cannot be a reason, and that no third
inhabitant can be declared, are compiler facts and live in `test_kernel_typing.py`.
"""

from dataclasses import FrozenInstanceError, dataclass, fields
from typing import Literal, Never, Union, get_args, get_origin

import pytest

from app.kernel import Err, Ok, Result, Unavailable


@dataclass(frozen=True)
class Closed:
    """A stand-in reason, shaped the way every real one will be."""

    day_offset: int
    kind: Literal["closed"] = "closed"


def test_a_success_carries_its_value() -> None:
    assert Ok(3).value == 3


def test_a_failure_carries_its_reason() -> None:
    reason = Closed(day_offset=2)
    assert Err(reason).reason is reason


def test_neither_carries_the_other() -> None:
    """The whole reason this is two classes and not one pair with two nullable
    fields: *both* and *neither* are states such a pair has, and every caller of
    one ends up writing a defensive branch for them.
    """

    assert [field.name for field in fields(Ok)] == ["value"]
    assert [field.name for field in fields(Err)] == ["reason"]


def test_the_union_has_exactly_two_members() -> None:
    assert get_origin(Result) is Union
    assert tuple(get_origin(member) for member in get_args(Result)) == (Ok, Err)


def test_neither_member_can_be_extended() -> None:
    """`@final`, so the closed set stays two. The compiler enforces it; this
    records that the marker is present, since deleting it changes nothing a
    runtime test could otherwise see.
    """

    assert Ok.__final__ is True
    assert Err.__final__ is True


@pytest.mark.parametrize(
    ("result", "attribute", "value"),
    [(Ok(1), "value", 2), (Err(Closed(day_offset=1)), "reason", Closed(day_offset=2))],
)
def test_both_are_frozen(result: object, attribute: str, value: object) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(result, attribute, value)


def test_a_result_is_consumed_by_pattern_match() -> None:
    def read(result: Result[int, Closed]) -> str:
        match result:
            case Ok(value):
                return f"ok:{value}"
            case Err(reason):
                return f"err:{reason.kind}"

    assert read(Ok(7)) == "ok:7"
    assert read(Err(Closed(day_offset=0))) == "err:closed"


def test_a_reason_is_a_machine_code_and_its_payload() -> None:
    reason = Closed(day_offset=3)
    assert reason.kind == "closed"
    assert reason.day_offset == 3


# --- mapping and chaining ------------------------------------------------------


def test_mapping_a_success_transforms_the_value() -> None:
    assert Ok(3).map(str) == Ok("3")


def test_mapping_a_failure_keeps_the_reason_unchanged() -> None:
    """Unchanged means *the same object*. A reason rebuilt on the way out would
    lose whatever payload its producer put in it, silently, several frames from
    where the failure was decided.
    """

    reason = Closed(day_offset=4)
    mapped = Err(reason).map(str)
    assert mapped.reason is reason


def test_mapping_a_failure_never_runs_the_transform() -> None:
    calls = []

    def transform(value: int) -> int:
        calls.append(value)
        return value

    Err(Closed(day_offset=0)).map(transform)
    assert calls == []


def test_chaining_a_success_runs_the_next_step() -> None:
    assert Ok(3).and_then(lambda value: Ok(value * 2)) == Ok(6)


def test_a_step_that_has_no_answer_ends_the_chain() -> None:
    reason = Closed(day_offset=5)
    assert Ok(3).and_then(lambda value: Err(reason)) == Err(reason)


def test_chaining_a_failure_keeps_the_reason_unchanged() -> None:
    reason = Closed(day_offset=6)
    chained = Err(reason).and_then(lambda value: Ok(value))
    assert chained.reason is reason


def test_chaining_a_failure_never_runs_the_next_step() -> None:
    calls = []

    def step(value: int) -> Result[int, Closed]:
        calls.append(value)
        return Ok(value)

    Err(Closed(day_offset=0)).and_then(step)
    assert calls == []


def test_a_reason_survives_a_whole_chain_untouched() -> None:
    """Where the identity guarantee actually gets used: the failure is decided
    once, deep in a computation, and every step after it is a pass-through.
    """

    reason = Closed(day_offset=7)
    end = Err(reason).map(str).and_then(lambda value: Ok(len(value))).map(bool)
    assert end.reason is reason


# --- the reason union, empty ---------------------------------------------------


def test_the_reason_union_ships_empty() -> None:
    """`Never` is how an empty union is spelled, and the emptiness is the claim.

    Every kind the source specification documents name is produced by an engine
    that does not exist, so inventing one now would be answering a domain
    question this repo has deliberately left open. The first real member arrives
    with the time module's nonexistent-local-time case, and this line changes
    with it.
    """

    assert Unavailable is Never
    assert get_args(Result[int, Unavailable])[1] == Err[Never]
