"""One import path, and an export list that says what the kernel has become.

``app.kernel`` re-exports its whole public API, and nothing outside the package
— tests included — imports a submodule. That is already how the ``Sport``
registry is consumed, and it is what lets the kernel be reorganised internally
without breaking a caller: moving ``invariant`` beside the money types is then a
file move, not a sweep across the tree.

The export list earns its keep by being read. A reviewer watching ``__all__``
grow is watching the innermost ring of the system grow, which is the one place
where *"does this belong here?"* has to be asked every time — ADR-0022 settles
it with two questions: does it answer a question about the domain? then it is
not the kernel. Would a second implementation of it be a defect? then it is.
"""

import ast
from pathlib import Path

import pytest

import app.kernel

ROOT = Path(__file__).resolve().parents[2]
KERNEL = ROOT / "app" / "kernel"

#: The whole public surface, written out rather than derived, so that growing it
#: is a diff on this line as well as on `__init__.py`. **No deep-freeze helper**
#: is among them and none is coming: immutability here is frozen dataclasses and
#: tuples, with no development-versus-production split.
THE_SURFACE = (
    "SPORT_SPECS",
    "Sport",
    "SportSpec",
    "InvariantViolated",
    "exhaustive",
    "invariant",
    "Err",
    "Ok",
    "Reason",
    "Result",
    "Unavailable",
)


def kernel_submodules() -> list[Path]:
    return sorted(p for p in KERNEL.rglob("*.py") if p.name != "__init__.py")


def public_definitions(path: Path) -> set[str]:
    """Module-level names `path` defines and does not hide behind an underscore.

    Definitions only — a name this module *imported* is somebody else's export,
    and `TypeVar`s are private by convention and by their leading underscore.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            found.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.add(node.target.id)
        elif isinstance(node, ast.Assign):
            found.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return {name for name in found if not name.startswith("_")}


def kernel_submodule_imports(path: Path) -> list[str]:
    """Imports in `path` that reach past `app.kernel` into one of its files."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [] if node.level else [node.module or ""]
        else:
            continue
        for name in names:
            if name.startswith("app.kernel."):
                found.append(f"{path.relative_to(ROOT)}:{node.lineno}: {name}")
    return found


def test_the_export_list_is_the_whole_surface() -> None:
    assert sorted(app.kernel.__all__) == sorted(THE_SURFACE)


@pytest.mark.parametrize("name", THE_SURFACE)
def test_every_exported_name_resolves(name: str) -> None:
    assert getattr(app.kernel, name, None) is not None


def test_nothing_public_is_reachable_only_through_a_submodule() -> None:
    """The re-export is *whole*, so no caller ever has a reason to go deeper."""

    unexported = {
        f"{path.relative_to(ROOT)}: {name}"
        for path in kernel_submodules()
        for name in public_definitions(path)
        if name not in app.kernel.__all__
    }
    assert not unexported, (
        "defined in a kernel submodule and not re-exported, so the only way to "
        "reach it is the import this package forbids:\n" + "\n".join(sorted(unexported))
    )


def test_no_module_and_no_test_imports_a_kernel_submodule() -> None:
    """Inside `app/kernel/` the submodules import each other, necessarily —
    that is what a package re-exporting itself looks like. Everywhere else the
    one import path is `app.kernel`.
    """

    subjects = [
        path
        for tree in (ROOT / "app", ROOT / "tests")
        for path in tree.rglob("*.py")
        if KERNEL not in path.parents
    ]
    offenders = [line for path in subjects for line in kernel_submodule_imports(path)]
    assert not offenders, (
        "the kernel is consumed through `from app.kernel import ...`, never a "
        "submodule — otherwise moving a definition between kernel files becomes "
        "a change to every caller:\n" + "\n".join(offenders)
    )


def test_the_walk_reaches_the_tree_it_is_claiming_about() -> None:
    """A walk over a path that has moved passes by finding nothing."""

    subjects = [
        path
        for tree in (ROOT / "app", ROOT / "tests")
        for path in tree.rglob("*.py")
        if KERNEL not in path.parents
    ]
    walked = {str(path.relative_to(ROOT)) for path in subjects}
    assert "app/engines/assessment.py" in walked
    assert "app/modules/rating/domain/assessment.py" in walked
    assert "tests/unit/test_sport_registry.py" in walked
    assert "app/kernel/sports.py" not in walked
    assert len(walked) >= 100
    assert len(kernel_submodules()) >= 3
