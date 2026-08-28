"""Same input, same snapshot, same ruleset ⇒ **byte-identical output**.

**Across two subprocesses with different hash seeds**, because that is the only
place the failure lives. A set of ids reorders *between* processes and never
*within* one (``docs/adr/0105``), so a same-process assertion is green on a
matcher that hands two workers two different answers to one question.

**The seed is never pinned.** ``PYTHONHASHSEED=0`` would make this pass on code
that iterated a set in every stage, which is the opposite of what it is for — so
the two seeds are drawn per run, and the test is allowed to be the thing that
finds it.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

#: `backend/`, so the probe is importable as `tests.unit....` exactly as it is
#: under pytest.
ROOT = Path(__file__).resolve().parents[2]

PROBE = "tests.unit.shortlist_determinism_probe"


def _run_under(seed: int) -> str:
    finished = subprocess.run(
        [sys.executable, "-m", PROBE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONHASHSEED": str(seed),
            "PYTHONPATH": str(ROOT),
            # The probe touches no database and no clock, but importing the app
            # package still reads the four-environment configuration, and `local`
            # is what a laptop and a CI runner both are.
            "APP_ENV": "local",
            "JWT_SECRET_KEY": "probe-secret-do-not-use-in-prod",
            "WRITER_DB_URL": "sqlite+aiosqlite:///:memory:",
            "DB_SSL_MODE": "disable",
        },
    )
    assert finished.returncode == 0, finished.stderr
    return finished.stdout


@pytest.mark.parametrize("attempt", range(3))
def test_two_processes_with_different_hash_seeds_agree_byte_for_byte(attempt: int):
    """The property, driven at two seeds nobody chose in advance.

    Repeated a few times because a single pair of seeds can agree by luck on a
    small set — the failure this guards is probabilistic in exactly that way.
    """

    first_seed, second_seed = random.sample(range(1, 4294967295), 2)

    first = _run_under(first_seed)
    second = _run_under(second_seed)

    assert first == second, (
        f"two processes disagreed at seeds {first_seed} and {second_seed}"
    )


def test_the_probe_actually_produced_an_ordered_answer():
    """The guard on the guard. Two empty answers are byte-identical too, and a
    probe that scored nobody would prove the property over nothing."""

    answer = json.loads(_run_under(1))

    assert len(answer["returned"]) >= 5
    assert answer["counts"]["n_scored"] >= len(answer["returned"])
    assert all(row["terms"] for row in answer["returned"])


def test_the_probe_holds_ties_for_the_seed_to_move():
    """A population of clearly distinguishable people would make the property
    pass by accident, so the fixture is asserted to contain the ambiguity the
    tie-break exists to resolve."""

    answer = json.loads(_run_under(1))
    fits = [row["fit"] for row in answer["returned"]]

    assert len(set(fits)) < len(fits), "no two candidates scored the same"
