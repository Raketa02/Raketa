"""The wall clock, and the separation that having an interface is *for*.

`SystemClock` is the one adapter in the system that reads ambient time, and until
this module's subject moved it shared a file with the `Clock` Protocol — so every
one of the twelve modules that only wanted to know *what a clock is* had a live
one in scope. Nothing enforced the distinction, and nothing would have noticed it
being crossed.

Three of the four claims below erase at runtime and so are walked rather than
exercised: that the interface resolves from the kernel everywhere, that the
adapter is imported only by a composition root, and that an instant is built
through its validating constructor rather than its brand. Each walk counts what
it read, because a walk over a path that has moved passes by finding nothing.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.infrastructure.clock import SystemClock
from app.kernel import Clock

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = "app.infrastructure.clock"
RETIRED = "app.shared.clock"

#: The only two modules that may reach for a live clock: the FastAPI dependency
#: wiring and the event-runtime bootstrap. Everything else is handed one.
COMPOSITION_ROOTS = ["app/api/dependencies.py", "app/bootstrap/events.py"]


# --- What the adapter returns ---------------------------------------------------


def test_the_wall_clock_reads_an_aware_utc_instant() -> None:
    """Aware, and in UTC — the two halves the kernel's `instant()` checks.

    A naive `datetime.now()` here does not return a wrong-looking value; it
    returns one that reads as a time and behaves as one until it is compared with
    a stored `timestamptz`. That is why the constructor raises rather than
    normalising, and why this is the adapter's first test.
    """

    now = SystemClock().now()

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_it_reads_the_host_clock_rather_than_a_constant() -> None:
    """The adapter's whole job, and the one thing a stub cannot fake for it."""

    before = datetime.now(timezone.utc)
    reading = SystemClock().now()
    after = datetime.now(timezone.utc)

    assert before <= reading <= after


def test_it_satisfies_the_kernel_protocol() -> None:
    """Structural, so nothing declares this — which is why it is asserted."""

    assert isinstance(SystemClock(), Clock)


# --- What only a walk can see ---------------------------------------------------


def _modules_of(tree: Path) -> list[Path]:
    return sorted(tree.rglob("*.py"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _module_the_name_comes_from(path: Path, name: str) -> str | None:
    """Which module `path` imports `name` from, if it imports it at all."""

    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.ImportFrom) and not node.level:
            if any(alias.name == name for alias in node.names):
                return node.module or ""
    return None


def _imports_module(path: Path, dotted: str) -> bool:
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [] if node.level else [node.module or ""]
        else:
            continue
        if any(name == dotted or name.startswith(f"{dotted}.") for name in names):
            return True
    return False


def test_every_module_that_names_the_clock_resolves_it_from_the_kernel() -> None:
    """One `Clock`, one import path — the acceptance criterion, as a gate.

    `app.kernel` re-exports its whole surface, so a second spelling would not
    even be a second *type*; it would be the same type reached through a module
    that is free to define its own tomorrow. This is what keeps that from
    starting again after the file it started in is gone.
    """

    # Outside the kernel package: `app/kernel/__init__.py` imports the name from
    # `app.kernel.time` because it *is* the re-export, which is the one import of
    # a submodule there will ever be — and `test_kernel_surface.py` is what keeps
    # it that way.
    walked = [
        path
        for path in _modules_of(ROOT / "app") + _modules_of(ROOT / "tests")
        if "kernel" not in path.parts
    ]
    sources = {
        str(path.relative_to(ROOT)): _module_the_name_comes_from(path, "Clock")
        for path in walked
    }
    importers = {path: source for path, source in sources.items() if source}

    assert set(importers.values()) == {"app.kernel"}, importers
    assert len(importers) >= 12, "the walk has lost the call sites it claims about"
    for area in ("auth", "rating", "users", "bootstrap", "api"):
        assert any(f"/{area}/" in path for path in importers), area


def test_only_a_composition_root_imports_the_wall_clock() -> None:
    """The design smell this ticket closed, stated as the rule it became.

    A use case that can reach `SystemClock` is one refactor away from calling it,
    and the failure is silent: the tests still pass, because they inject a clock,
    and only production reads the host's. Wiring is the layer allowed to know
    which clock is real.
    """

    walked = _modules_of(ROOT / "app")
    importers = sorted(
        str(path.relative_to(ROOT)) for path in walked if _imports_module(path, ADAPTER)
    )

    assert importers == COMPOSITION_ROOTS
    assert len(walked) >= 100, "the walk has lost the tree it is claiming about"


def test_the_retired_module_is_gone_and_nothing_reaches_for_it() -> None:
    """Deleted, not merely unused — an unimported module is an available one."""

    assert not (ROOT / "app" / "shared" / "clock.py").exists()

    walked = _modules_of(ROOT / "app") + _modules_of(ROOT / "tests")
    offenders = sorted(
        str(path.relative_to(ROOT)) for path in walked if _imports_module(path, RETIRED)
    )

    assert not offenders, offenders
    assert len(walked) >= 150, "the walk has lost the tree it is claiming about"


def test_the_adapter_builds_its_instant_through_the_validating_constructor() -> None:
    """`instant(...)`, never `Instant(...)` — and no test can tell them apart.

    The brand erases, so both spellings return the same object for a value that
    is already aware and already UTC. They part company only for the value the
    type exists to refuse, which this adapter is not currently capable of
    producing — so the guard is against the day it is, and it has to be read off
    the source rather than off a return value.
    """

    parsed = _parse(ROOT / "app" / "infrastructure" / "clock.py")
    called = {
        node.func.id
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "instant" in called
    assert "Instant" not in called, "the brand is not a constructor; it checks nothing"
