"""``make tester`` — the admin command that sets and clears the tester mark.

The use case is asserted end to end in ``tests/api/test_testers.py``; this file
holds the command line to what it promises the operator: it takes a player and
an explicit ``on`` or ``off``, it says whether anything moved, and a player
nobody answers to is a non-zero exit rather than a traceback
(``docs/adr/0180`` §9).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

import app.modules.users.infrastructure.tester_cli as cli
from app.modules.users.application.set_tester_mark import TesterMark
from app.modules.users.domain.errors import UnknownPlayer

PLAYER_ID = UUID("5b7e1f0c-2d5a-4c1e-9d0e-6a7b8c9d0e1f")


def _mark(*, is_tester: bool, changed: bool) -> TesterMark:
    return TesterMark(
        player_id=PLAYER_ID,
        email="alice@example.com",
        is_tester=is_tester,
        changed=changed,
    )


def test_the_mark_is_named_on_or_off_and_never_assumed() -> None:
    assert cli._parse(["alice@example.com", "on"]) == ("alice@example.com", True)
    assert cli._parse([str(PLAYER_ID), "OFF"]) == (str(PLAYER_ID), False)

    # A run that forgot the mark must not quietly mark somebody.
    for argv in (["alice@example.com"], ["alice@example.com", "yes"], []):
        with pytest.raises(SystemExit):
            cli._parse(argv)


@pytest.mark.parametrize(
    ("mark", "said"),
    [
        (_mark(is_tester=True, changed=True), "is now a Tester"),
        (_mark(is_tester=True, changed=False), "was already a Tester"),
        (_mark(is_tester=False, changed=True), "is no longer a Tester"),
        (_mark(is_tester=False, changed=False), "was not a Tester"),
    ],
)
def test_the_report_says_whether_anything_moved(
    mark: TesterMark, said: str, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    async def set_mark(player: str, tester: bool) -> TesterMark:
        return mark

    monkeypatch.setattr(cli, "set_mark", set_mark)

    assert cli.main(["alice@example.com", "on" if mark.is_tester else "off"]) == 0
    printed = capsys.readouterr().out
    assert said in printed
    assert "alice@example.com" in printed and str(PLAYER_ID) in printed


def test_a_player_nobody_answers_to_exits_non_zero(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    async def set_mark(player: str, tester: bool) -> TesterMark:
        raise UnknownPlayer(player)

    monkeypatch.setattr(cli, "set_mark", set_mark)

    assert cli.main(["nobody@example.com", "on"]) == 1
    assert "nobody@example.com" in capsys.readouterr().err


def test_the_makefile_runs_this_module() -> None:
    # The command and the target are two spellings of one path, and a rename
    # that moved only the module would leave a target that fails at import.
    makefile = (Path(__file__).resolve().parents[2] / "Makefile").read_text(
        encoding="utf-8"
    )

    assert "\ntester:" in makefile
    assert "app.modules.users.infrastructure.tester_cli" in makefile
