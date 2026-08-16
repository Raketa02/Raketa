"""mypy as a test: the kernel's type constraints, asserted rather than assumed.

The kernel's guarantees are carried by the type system — ``Ok`` and ``Err`` are
``@final`` so a result has no third inhabitant, ``Err``'s reason is bound to
``Reason`` so a failure cannot carry a sentence, ``exhaustive`` takes ``Never``
so a closed union that grows fails the build. **None of that exists at runtime.**
Remove any of it and behaviour is identical, every test still passes, and the
diff reads like a simplification. Branded types, which the money module lands
next, are the same problem in a sharper form: they erase completely.

So the typechecker is the assertion. This runs it over
``tests/typecheck/kernel_misuse.py`` — a file of deliberately-wrong call sites,
each marked with the error code it must produce — and checks the two directions
that matter:

* every marked line produces exactly the marked error, so a constraint that
  stops being enforced fails here;
* no unmarked line produces any error, so the legitimate uses in that file are
  pinned too — a narrowing that stops narrowing, or a chain that stops
  composing, is as much a regression as a brand that stops binding.

It is seeded on the first constraints there are anything to say about, and it is
meant to grow: each branded module adds its own misuses to the subject file.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = ROOT / "tests" / "typecheck" / "kernel_misuse.py"

#: `path:line: error: message  [code]` — the only part of mypy's output this
#: reads, so a change to its prose does not become a change to this test.
REPORTED = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): error: .*\[(?P<code>[\w-]+)\]$")

#: The marker a wrong call site carries, at the end of its own line.
WANTED = re.compile(r"#\s*want-error:\s*(?P<code>[\w-]+)\s*$")


def wanted_errors(subject: Path) -> dict[int, str]:
    """The `{line: code}` the subject file claims for itself."""

    found = {}
    for number, text in enumerate(subject.read_text(encoding="utf-8").splitlines(), 1):
        marker = WANTED.search(text)
        if marker:
            found[number] = marker.group("code")
    return found


def reported_errors(subject: Path) -> dict[int, str]:
    """The `{line: code}` mypy actually reports for it.

    `--no-incremental` because a cached run of a file whose *dependency* changed
    is exactly the run that would report a constraint as still enforced after it
    was deleted. Run from the repo root so `pyproject.toml` — and with it the
    strict override on `app.kernel` — is the configuration in force, which is
    the configuration CI uses.
    """

    target = str(subject)
    completed = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental", target],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode in (0, 1), (
        "mypy could not run — this is a broken harness, not a passing one:\n"
        + completed.stdout
        + completed.stderr
    )

    # Scoped to the subject. mypy follows the imports, so an error inside
    # `app.kernel` itself would otherwise land in this dict under a line number
    # that means something entirely different. Resolved against the root
    # because mypy reports a path under its cwd relative to it and any other
    # path — a tmp_path subject below — as it was given.
    found = {}
    for line in completed.stdout.splitlines():
        match = REPORTED.match(line.strip())
        if match and (ROOT / match.group("path")).resolve() == subject.resolve():
            found[int(match.group("line"))] = match.group("code")
    return found


@pytest.fixture(scope="module")
def errors() -> dict[int, str]:
    return reported_errors(SUBJECT)


def test_the_subject_file_is_where_this_expects_it() -> None:
    """A harness pointed at a file that has moved passes by finding nothing.

    Which is how this whole file fails silently, so the subject is located and
    its claims are counted rather than assumed — the argument
    ``test_kernel_purity.py`` already makes for its walk.
    """

    assert SUBJECT.exists(), f"the misuse subject is missing: {SUBJECT}"
    assert len(wanted_errors(SUBJECT)) >= 10


def test_every_claimed_constraint_is_still_enforced(errors: dict[int, str]) -> None:
    """The direction that matters: a deleted constraint shows up here."""

    wanted = wanted_errors(SUBJECT)
    unenforced = {line: code for line, code in wanted.items() if line not in errors}
    assert not unenforced, (
        "the typechecker no longer refuses these — a constraint the kernel "
        "claims has stopped being enforced:\n"
        + "\n".join(
            f"  {SUBJECT.name}:{line}: expected [{code}]"
            for line, code in unenforced.items()
        )
    )


def test_each_wrong_call_site_fails_the_way_it_says_it_does(
    errors: dict[int, str],
) -> None:
    """And for the *stated* reason. A line refused on some unrelated grounds —
    a typo, a signature that drifted — would otherwise read as proof of a
    constraint nothing is checking.
    """

    wanted = wanted_errors(SUBJECT)
    mismatched = {
        line: (code, errors[line])
        for line, code in wanted.items()
        if line in errors and errors[line] != code
    }
    assert not mismatched, "refused, but not for the reason claimed:\n" + "\n".join(
        f"  {SUBJECT.name}:{line}: expected [{want}], got [{got}]"
        for line, (want, got) in mismatched.items()
    )


def test_no_legitimate_use_in_the_subject_file_is_refused(
    errors: dict[int, str],
) -> None:
    """The other direction: the correct uses beside them have to stay correct."""

    wanted = wanted_errors(SUBJECT)
    unexpected = {line: code for line, code in errors.items() if line not in wanted}
    assert not unexpected, (
        "the typechecker refuses a line the subject file does not claim is "
        "wrong — either the kernel has over-tightened, or a new misuse was "
        "added without its marker:\n"
        + "\n".join(
            f"  {SUBJECT.name}:{line}: [{code}]" for line, code in unexpected.items()
        )
    )


# --- That the harness itself fires, which is the only reason to trust it ------


def test_a_marker_with_no_error_behind_it_is_caught(tmp_path: Path) -> None:
    """The failure mode this exists to have: a constraint quietly removed.

    Driven against a subject the kernel has no quarrel with, so the marker on it
    goes unanswered — which is precisely the shape of `@final` being deleted.
    """

    subject = tmp_path / "subject.py"
    subject.write_text("x: int = 1  # want-error: assignment\n", encoding="utf-8")
    assert wanted_errors(subject) == {1: "assignment"}
    assert reported_errors(subject) == {}


def test_a_real_error_is_read_back_with_its_line_and_code(tmp_path: Path) -> None:
    subject = tmp_path / "subject.py"
    subject.write_text(
        "from app.kernel import Ok\n\n\nOk(1).value = 2  # want-error: misc\n",
        encoding="utf-8",
    )
    assert wanted_errors(subject) == {4: "misc"}
    assert reported_errors(subject) == {4: "misc"}
