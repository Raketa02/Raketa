"""The player record keeps no record. **Asserted structurally, not remembered.**

``docs/adr/0155`` §1: this context has no aggregate, no table and no migration. It
composes five other contexts' published facts and enforces admission, and every
figure that lands on the sheet later arrives from whoever owns it.

**The day it grows a table is the day it stopped being an assembler**, and that
should fail a build rather than pass a review. The failure mode this guards is
not somebody deciding to store a record — it is one convenient cache: *the
identity read costs a profile fold, so let us keep a row*. That row is a second
place for *what is this person called* to be true, and it is the copy that gets
believed.

A structural walk rather than a claim in a docstring, for the reason
``test_composition_root`` gives about its own: the regression is one import in a
diff where nothing looks wrong.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CONTEXT = Path(__file__).resolve().parents[2] / "app" / "modules" / "player_record"

#: What a context that stored something would have to reach for. The ORM and the
#: declarative base are the two spellings of *a table*; the migration directory is
#: checked separately, because a table can also arrive from that side first.
FORBIDDEN_IMPORTS = ("sqlalchemy", "alembic", "app.infrastructure.database")


def modules() -> list[Path]:
    found = sorted(CONTEXT.rglob("*.py"))
    assert found, "the walk found no modules, so it would pass for ever"
    return found


def imported_names(module: Path) -> set[str]:
    tree = ast.parse(module.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("module", modules(), ids=lambda one: one.name)
def test_no_module_in_this_context_reaches_for_persistence(module: Path):
    """**Every layer, infrastructure included.** The adapters here translate
    somebody else's published port; one that opened a session of its own would be
    this context reading another context's schema, which is the second failure
    this walk catches with the same line."""

    offending = sorted(
        name
        for name in imported_names(module)
        for forbidden in FORBIDDEN_IMPORTS
        if name == forbidden or name.startswith(f"{forbidden}.")
    )

    assert offending == [], f"{module.name} reaches for storage: {offending}"


def test_this_context_ships_no_migration():
    """A table can arrive from the migration side first, and a walk over the
    source would not see it."""

    versions = Path(__file__).resolve().parents[2] / "migrations" / "versions"
    written = sorted(versions.rglob("*.py"))
    assert written, "the walk found no migrations, so it would pass for ever"

    naming = [one.name for one in written if "player_record" in one.read_text()]

    assert naming == []
