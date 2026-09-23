"""``python -m app.modules.users.infrastructure.tester_cli <player> on|off`` — the mark.

What ``make tester`` runs, and **the only way to set or clear the tester mark**
(``docs/adr/0180`` §9). A Tester is a real player who may be given a feature
before anyone else; the mark is the backend's and never the player's, and there
is deliberately no route for it — no management UI either, which the PRD puts
out of scope — so the command is the whole of the surface.

``<player>`` is an account id or an email, as typed. The mark is **named every
time** — ``on`` or ``off``, never a default — because a command that marked
somebody when the operator forgot the second word would be the easiest way to
put a feature in front of the wrong person.

Thin on purpose, like ``rebuild_cli``: it runs ``SetTesterMark`` wired out of
the composition root, so the command and ``tests/api/test_testers.py`` drive
exactly the same code, and it **never writes the store itself** — the mark is an
event on the player's stream, projected in the same transaction, and delivered
through the outbox by the API's worker like any request's. It lives under
``app/`` for that command's reason too: the container image copies ``app/`` and
not ``scripts/``, and the database is reachable from the container.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Sequence

from app.bootstrap.composition import (
    build_background_session_factory,
    build_set_tester_mark,
)
from app.core.config import get_settings
from app.infrastructure.database.engine import dispose_engine, get_engine, init_engine
from app.modules.users.application.commands import SetTesterMarkCommand
from app.modules.users.application.set_tester_mark import TesterMark
from app.modules.users.domain.errors import UnknownPlayer

_MARKS = {"on": True, "off": False}


async def set_mark(player: str, tester: bool) -> TesterMark:
    settings = get_settings()
    init_engine(settings)
    try:
        session_factory = build_background_session_factory(get_engine())
        async with session_factory() as session:
            return await build_set_tester_mark(session).execute(
                SetTesterMarkCommand(player=player, tester=tester)
            )
    finally:
        await dispose_engine()


def main(argv: Sequence[str] | None = None) -> int:
    player, tester = _parse(argv)
    try:
        mark = asyncio.run(set_mark(player, tester))
    except UnknownPlayer as refused:
        # **Non-zero, and said in a sentence.** A refusal is the operator's typo,
        # and a traceback would bury the one line that says which.
        print(refused.message, file=sys.stderr)
        return 1
    for line in _report(mark):
        print(line)
    return 0


def _parse(argv: Sequence[str] | None) -> tuple[str, bool]:
    parser = argparse.ArgumentParser(
        prog="tester_cli",
        description=(
            "Mark a player as a Tester, or clear the mark. A Tester may be "
            "given a feature before anyone else (docs/adr/0180)."
        ),
    )
    parser.add_argument("player", help="the player's account id or email")
    parser.add_argument(
        "mark",
        type=str.lower,
        choices=sorted(_MARKS),
        help="`on` to mark the player as a Tester, `off` to clear the mark",
    )
    parsed = parser.parse_args(argv)
    return parsed.player, _MARKS[parsed.mark]


def _report(mark: TesterMark) -> list[str]:
    """What the operator reads: who, and whether this run moved anything."""

    if mark.is_tester:
        said = "is now a Tester" if mark.changed else "was already a Tester"
    else:
        said = "is no longer a Tester" if mark.changed else "was not a Tester"
    lines = [f"{mark.email} ({mark.player_id}) {said}."]
    if mark.changed:
        lines.append(
            "  The player app reads it at its next launch or return to the "
            "foreground, and a gated screen at its next mount."
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
