"""``python -m app.reconciliation`` — what a nightly schedule runs.

Thin on purpose: everything it prints comes from ``runner.report``, so the
command and a test drive exactly the same code. A breach exits **1**, which is
what a scheduler alerts on.
"""

from __future__ import annotations

import asyncio

from app.reconciliation.runner import report, run


def main() -> int:
    reconciliation = asyncio.run(run())
    for line in report(reconciliation):
        print(line)
    return 0 if reconciliation.is_sound else 1


if __name__ == "__main__":
    raise SystemExit(main())
