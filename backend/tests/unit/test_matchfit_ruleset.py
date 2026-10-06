"""The ruleset: what it refuses to load, and the facts the live one pins.

Two kinds of test, and the split is deliberate.

**Refusals** drive a deliberately broken ruleset through the validator and assert
it goes red — the idiom this repository already holds three times over
(``make test-drift``, ``make test-poetry-pin``, ``make test-hooks``), on the
stated reason that *a guardrail that silently stops matching is worse than none,
because you stop watching for it.*

**Pinned facts** assert what the two sections that are left (#580) were argued
from: a tolerance for each kind of game, the newcomer narrowing being the
competitive one, and the claim the stronger partner's share makes.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path
from types import MappingProxyType

import pytest

from app.core.config import Environment
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import ModeRules, Ruleset, validate_ruleset
from app.kernel import InvariantViolated
from app.modules.matchmaking.infrastructure import rulesets as ruleset_registry
from app.modules.matchmaking.infrastructure.rulesets import (
    LIVE_RULESET,
    LIVE_RULESET_VERSION,
)
from app.modules.matchmaking.infrastructure.rulesets import (
    r2026_09_15_a as dataset_module,
)

#: ``backend/app``, derived from a module inside it rather than from this file's
#: own depth, so moving the tests does not silently point the walk at nothing.
APP_ROOT = Path(dataset_module.__file__).parents[4]

# ---------------------------------------------------------------------------
# The stamp


def test_the_live_ruleset_is_named_and_dated() -> None:
    assert LIVE_RULESET.version == LIVE_RULESET_VERSION
    assert LIVE_RULESET.released_on == "2026-09-15"


def test_a_released_ruleset_cannot_be_edited() -> None:
    """*Immutable once released* — a change is a new name, never an edit.

    Held by frozen dataclasses and read-only mappings rather than by discipline.
    """

    with pytest.raises(dataclasses.FrozenInstanceError):
        LIVE_RULESET.version = "2026.09.16-a"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        LIVE_RULESET.balance.pct_min = 40  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        LIVE_RULESET.modes[SearchMode.COMPETITIVE].level_tolerance = 1.0  # type: ignore[misc]
    with pytest.raises(TypeError):
        LIVE_RULESET.modes[SearchMode.COMPETITIVE] = ModeRules(level_tolerance=1.0)  # type: ignore[index]


def test_a_ruleset_whose_date_disagrees_with_its_name_refuses_to_load() -> None:
    """Two spellings of one fact, so the pair is checked rather than trusted."""

    with pytest.raises(InvariantViolated, match="disagrees with its name"):
        validate_ruleset(dataclasses.replace(LIVE_RULESET, released_on="2026-09-16"))


@pytest.mark.parametrize("version", ["2026.09.15", "2026-09-15-a", "2026.9.15-a", "a"])
def test_a_ruleset_version_is_a_date_and_a_letter(version: str) -> None:
    """The letter is what makes a second release on one day a new dataset."""

    with pytest.raises(InvariantViolated):
        validate_ruleset(dataclasses.replace(LIVE_RULESET, version=version))


def test_the_four_environments_resolve_the_same_ruleset(monkeypatch) -> None:
    """`local`, `development`, `staging` and `production` run the same numbers.

    **The modules are genuinely re-executed under each name**, because
    ``LIVE_RULESET`` is resolved at import: a plain re-``import`` would hit
    ``sys.modules`` and hand back the same object four times, which is a
    tautology a ruleset that *did* read ``APP_ENV`` would sail through.
    """

    assert set(Environment) == {
        Environment.LOCAL,
        Environment.DEVELOPMENT,
        Environment.STAGING,
        Environment.PRODUCTION,
    }

    resolved = set()
    for environment in Environment:
        monkeypatch.setenv("APP_ENV", environment.value)
        importlib.reload(dataset_module)
        registry = importlib.reload(ruleset_registry)
        resolved.add(
            (
                registry.LIVE_RULESET.version,
                registry.LIVE_RULESET.balance,
                tuple(
                    rules.level_tolerance
                    for rules in registry.LIVE_RULESET.modes.values()
                ),
            )
        )

    assert len(resolved) == 1

    # And left as it was found: the reloaded modules are the ones every other
    # test holds references into.
    monkeypatch.setenv("APP_ENV", Environment.LOCAL.value)
    importlib.reload(dataset_module)
    importlib.reload(ruleset_registry)


@pytest.mark.parametrize(
    "package",
    [
        APP_ROOT / "engines" / "matchfit",
        APP_ROOT / "modules" / "matchmaking" / "infrastructure" / "rulesets",
    ],
    ids=["engine", "ruleset store"],
)
def test_nothing_that_resolves_a_ruleset_can_read_configuration(package: Path) -> None:
    """The reload above catches an import-time read; this catches every other one.

    ``import-linter`` fences the engines layer off ``app.core.config`` already,
    but the ruleset **store** is a module's infrastructure and is on the outside
    of that contract — so the claim is asserted over the source of both halves
    rather than half of it.
    """

    sources = sorted(package.rglob("*.py"))
    assert sources, package
    # Imports and names rather than raw text: the modules *discuss* `APP_ENV` in
    # their docstrings, on purpose, and a walk that could not tell a sentence
    # about a rule from a breach of it would be deleted the first time somebody
    # documented the rule properly.
    forbidden_imports = {"os", "app.core.config", "pydantic_settings"}
    forbidden_names = {"get_settings", "Settings", "Environment", "environ", "getenv"}
    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert (
                        alias.name.split(".")[0] not in forbidden_imports
                        and alias.name not in forbidden_imports
                    ), f"{source.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert (
                    module.split(".")[0] not in forbidden_imports
                    and module not in forbidden_imports
                ), f"{source.name} imports from {module}"
                for alias in node.names:
                    assert alias.name not in forbidden_names, (
                        f"{source.name} imports {alias.name}"
                    )
            elif isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names, (
                    f"{source.name} reaches for {node.attr}"
                )


# ---------------------------------------------------------------------------
# The level tolerance


def test_every_kind_of_game_has_a_tolerance() -> None:
    assert set(LIVE_RULESET.modes) == set(SearchMode)


def test_a_friendly_tolerates_a_wider_gap_than_a_competitive_game() -> None:
    """The newcomer window narrows a friendly *to the competitive number*
    (``docs/adr/0113``), which only narrows anything while this holds."""

    assert (
        LIVE_RULESET.modes[SearchMode.FOR_FUN].level_tolerance
        > LIVE_RULESET.modes[SearchMode.COMPETITIVE].level_tolerance
    )


def test_a_kind_of_game_with_no_tolerance_refuses_to_load() -> None:
    with pytest.raises(InvariantViolated, match="every kind of game"):
        validate_ruleset(
            dataclasses.replace(
                LIVE_RULESET,
                modes=MappingProxyType(
                    {SearchMode.COMPETITIVE: ModeRules(level_tolerance=0.55)}
                ),
            )
        )


@pytest.mark.parametrize("tolerance", [0.0, -0.1])
def test_a_tolerance_that_admits_nobody_refuses_to_load(tolerance: float) -> None:
    modes = dict(LIVE_RULESET.modes)
    modes[SearchMode.FOR_FUN] = ModeRules(level_tolerance=tolerance)
    with pytest.raises(InvariantViolated, match="level tolerance"):
        validate_ruleset(
            dataclasses.replace(LIVE_RULESET, modes=MappingProxyType(modes))
        )


# ---------------------------------------------------------------------------
# The balance rules


def _with_balance(**changes: object) -> Ruleset:
    return dataclasses.replace(
        LIVE_RULESET, balance=dataclasses.replace(LIVE_RULESET.balance, **changes)
    )


def test_a_clamp_whose_floor_is_not_below_its_ceiling_refuses_to_load() -> None:
    with pytest.raises(InvariantViolated, match="balance clamp"):
        validate_ruleset(_with_balance(pct_min=96, pct_max=96))


@pytest.mark.parametrize(
    "changes",
    [{"mu_coefficient": 0.0}, {"sigma_coefficient": -1.0}],
)
def test_a_coefficient_that_does_not_cost_anything_refuses_to_load(
    changes: dict[str, float],
) -> None:
    with pytest.raises(InvariantViolated, match="balance coefficients"):
        validate_ruleset(_with_balance(**changes))


@pytest.mark.parametrize("share", [0.0, 0.5, 0.55])
def test_the_stronger_partner_sets_less_than_half_a_side(share: float) -> None:
    """*The weaker partner sets more of a side* is the claim; a half or more is
    the claim not being made."""

    with pytest.raises(InvariantViolated, match="less than half a side"):
        validate_ruleset(_with_balance(stronger_partner_share=share))
