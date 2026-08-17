"""`invariant` and `exhaustive`: the raising half of the kernel's two mechanisms.

What is asserted here is runtime behaviour. The half that matters most —
``invariant`` narrowing its subject for the compiler, and ``exhaustive`` refusing
a union member nobody handled — has no runtime existence at all and is asserted
in ``test_kernel_typing.py``, which runs mypy over deliberately-wrong call sites.
"""

import pytest

from app.kernel import InvariantViolated, Sport, exhaustive, invariant


def test_a_present_subject_comes_back_unchanged() -> None:
    spec = object()
    assert invariant(spec, "unreachable") is spec


def test_an_absent_subject_raises() -> None:
    with pytest.raises(InvariantViolated):
        invariant(None, "no spec for sport: Sport.PADEL")


def test_an_untrue_condition_raises() -> None:
    with pytest.raises(InvariantViolated):
        invariant(1 > 2, "minute of day: 1500")


def test_a_true_condition_passes() -> None:
    assert invariant(2 > 1, "unreachable") is True


@pytest.mark.parametrize("subject", [0, 0.0, "", (), [], {}, frozenset()])
def test_a_falsy_value_is_still_a_value(subject: object) -> None:
    """Only `None` and `False` break an invariant, and this is why.

    A zero price, an empty option list and an empty transcript are all ordinary
    values somebody meant. A guard that rejected them would be wrong in the
    expensive direction — it raises on the case the caller handled correctly —
    and it is the guard that gets deleted rather than fixed.
    """

    assert invariant(subject, "unreachable") is subject


def test_the_message_reaches_the_reader_verbatim() -> None:
    """It has to name the offending value; nothing here may reword it."""

    with pytest.raises(InvariantViolated) as raised:
        invariant(None, "no spec for sport: 'CHESS'")
    assert str(raised.value) == "no spec for sport: 'CHESS'"


def test_it_is_not_a_value_error() -> None:
    """`ValueError` is what the modules' own parsing and validation raise, and
    what their handlers turn into a tidy 400. A bug that reaches a client
    looking like bad input is a bug nobody goes looking for.
    """

    with pytest.raises(InvariantViolated):
        try:
            invariant(None, "no spec")
        except (ValueError, TypeError, KeyError):  # pragma: no cover - the point
            pytest.fail("InvariantViolated was caught as an ordinary domain error")


def test_it_survives_python_dash_o() -> None:
    """The reason this is a function and not `assert`.

    `python -O` strips assert statements, so an invariant written as one is a
    guarantee that evaporates in exactly the environment where it mattered.
    This is a raise, so there is nothing to strip.
    """

    import subprocess
    import sys

    completed = subprocess.run(
        [
            sys.executable,
            "-O",
            "-c",
            "from app.kernel import InvariantViolated, invariant\n"
            "try:\n"
            "    invariant(None, 'still raises')\n"
            "except InvariantViolated as raised:\n"
            "    print(raised)\n",
        ],
        capture_output=True,
        text=True,
        cwd=__import__("pathlib").Path(__file__).resolve().parents[2],
    )
    assert completed.stdout.strip() == "still raises", completed.stderr


def test_reaching_exhaustive_at_runtime_raises_and_names_the_value() -> None:
    """Typechecking is the point; this is what happens when it was bypassed —
    a value from outside the closed set, off the wire or out of a database
    column written by an older release.
    """

    with pytest.raises(AssertionError) as raised:
        exhaustive(Sport.PADEL)  # type: ignore[arg-type]
    assert "Sport.PADEL" in str(raised.value)
