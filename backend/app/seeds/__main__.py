"""``python -m app.seeds`` — what ``make seed`` runs.

Thin on purpose: importing this module has already run the production guard (it
imports the package), and everything it prints comes from ``runner.report``, so
the command and a test drive exactly the same code.

A refusal arrives as a traceback rather than a tidy message, because the guard
fires while the package is being imported — before this file exists to catch
anything. That is the trade the guard is worth: unmissable, and impossible to
reach around.
"""

from __future__ import annotations

import asyncio

from app.seeds.runner import report, run


def main() -> int:
    for line in report(asyncio.run(run())):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
