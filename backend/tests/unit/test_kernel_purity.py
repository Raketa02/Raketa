"""The half of the purity fence `.importlinter` cannot express.

`import-linter` works at module granularity, so it can say `datetime` is legal in
the kernel and forbidden to the engines — but not that calling `now()` on it is
forbidden to both. ADR-0015's first purity rule is *no clock*: an engine reads the
time it is given, because a rating that quietly depends on when it was computed is
not reproducible, and reproducibility is what the falsification programme rests on.

So this walks the source instead. Two claims, over `app/kernel` and `app/engines`:

1. every import resolves to the standard library or to `app` itself — the contracts
   name the libraries anyone thought to name, this one catches the one nobody did;
2. no module anywhere in either package reads an ambient clock.

Parsing rather than importing is deliberate: a module that read a clock at import
time would already have read it by the time an import-based check could look.
"""

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARDED = (ROOT / "app" / "kernel", ROOT / "app" / "engines")

# The last two segments of a dotted read. `datetime.now`, `datetime.datetime.now`
# and `dt.date.today` all land here; so does `time.time()`. Reaching an ambient
# clock by any other spelling means importing `time` or `datetime` under a new
# name, which is the contracts' half of the fence.
AMBIENT_READS = frozenset(
    {
        ("datetime", "now"),
        ("datetime", "utcnow"),
        ("date", "today"),
        ("time", "time"),
    }
)


def modules_of(package: Path) -> list[Path]:
    return sorted(package.rglob("*.py"))


def _dotted(node: ast.expr) -> str | None:
    """`datetime.datetime.now` for an attribute chain rooted in a plain name."""

    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def foreign_imports(path: Path) -> list[str]:
    """Imports in `path` resolving to neither the stdlib nor `app`, named."""

    found = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative — first-party by construction
                continue
            names = [node.module or ""]
        else:
            continue
        for name in names:
            root = name.split(".")[0]
            if root == "app" or root in sys.stdlib_module_names:
                continue
            found.append(f"{_named(path)}:{node.lineno}: {name}")
    return found


def ambient_clock_reads(path: Path) -> list[str]:
    """Reads of an ambient clock in `path`, named."""

    found = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        dotted = _dotted(node)
        if dotted is None:
            continue
        segments = dotted.split(".")
        if len(segments) >= 2 and tuple(segments[-2:]) in AMBIENT_READS:
            found.append(f"{_named(path)}:{node.lineno}: {dotted}")
    return found


def _named(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


# --- The two claims, over the real packages ------------------------------------


@pytest.mark.parametrize("package", GUARDED, ids=lambda p: p.name)
def test_every_import_resolves_to_the_stdlib_or_to_app(package):
    offenders = [line for path in modules_of(package) for line in foreign_imports(path)]
    assert not offenders, "third-party imports in a pure package:\n" + "\n".join(
        offenders
    )


@pytest.mark.parametrize("package", GUARDED, ids=lambda p: p.name)
def test_no_module_reads_an_ambient_clock(package):
    offenders = [
        line for path in modules_of(package) for line in ambient_clock_reads(path)
    ]
    assert not offenders, (
        "ambient clock read in a pure package — time is passed in, never taken:\n"
        + "\n".join(offenders)
    )


def test_the_walk_reaches_both_packages():
    """A walk over a path that has moved passes by finding nothing.

    Which is the way this whole file fails silently, so the modules it is meant to
    be reading are counted rather than assumed.
    """

    walked = {_named(path) for package in GUARDED for path in modules_of(package)}
    assert "app/kernel/sports.py" in walked
    assert "app/engines/assessment.py" in walked
    assert "app/engines/racketskill/v3/engine.py" in walked
    assert len(walked) >= 8


# --- That each walk fires, which is the only reason to trust the two above ------


def _module(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "subject.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_a_third_party_import_is_found_and_named(tmp_path):
    subject = _module(tmp_path, "import math\nfrom sqlalchemy import select\n")
    assert [line.split(": ")[-1] for line in foreign_imports(subject)] == ["sqlalchemy"]
    assert "subject.py:2" in foreign_imports(subject)[0]


def test_a_plain_third_party_import_statement_is_found(tmp_path):
    subject = _module(tmp_path, "import redis.asyncio\n")
    assert [line.split(": ")[-1] for line in foreign_imports(subject)] == [
        "redis.asyncio"
    ]


def test_stdlib_first_party_and_relative_imports_are_left_alone(tmp_path):
    subject = _module(
        tmp_path,
        "from __future__ import annotations\n"
        "import math\n"
        "from dataclasses import dataclass\n"
        "from app.kernel import Sport\n"
        "from .core import combine_sigma\n",
    )
    assert foreign_imports(subject) == []


@pytest.mark.parametrize(
    "source",
    [
        "from datetime import datetime\nx = datetime.now()\n",
        "from datetime import datetime\nx = datetime.utcnow()\n",
        "import datetime\nx = datetime.datetime.now(datetime.timezone.utc)\n",
        "from datetime import date\nx = date.today()\n",
        "import time\nx = time.time()\n",
        "import datetime as dt\nx = dt.date.today()\n",
        "def f():\n    return datetime.now()\n",  # nested, not only module level
    ],
)
def test_each_ambient_clock_read_is_found_and_named(tmp_path, source):
    subject = _module(tmp_path, source)
    found = ambient_clock_reads(subject)
    assert len(found) == 1, found
    assert found[0].startswith("subject.py:")


def test_holding_a_datetime_is_not_reading_a_clock(tmp_path):
    """The kernel's time module is `datetime`'s one legitimate home."""

    subject = _module(
        tmp_path,
        "from datetime import datetime, timezone\n"
        "def at(value: datetime) -> datetime:\n"
        "    return value.astimezone(timezone.utc)\n"
        "EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)\n",
    )
    assert ambient_clock_reads(subject) == []
