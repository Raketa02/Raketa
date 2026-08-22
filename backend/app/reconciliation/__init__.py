"""The nightly ledger reconciliation, as a command something can schedule.

``ReconcileLedgers`` is the use case; this is the process around it. It is a
package of its own rather than a module under ``app/modules/money/`` for the
reason ``app/seeds/`` is: a command assembles its own session and reaches the
composition root, and a context's layers may not.

**There is no scheduler in this repository**, and this does not add one —
deployment is dormant (ADR-0010). What a nightly job needs from the code is to
be invocable and to *fail loudly*, and that is what this is: one command, one
exit code, one ERROR line per breach.
"""
