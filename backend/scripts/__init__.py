"""Developer tooling that runs against the backend but ships with nothing.

Nothing under ``app/`` may import from here. These are the offline machines —
the cohort generator, the shard split and its arithmetic, the taskdef proof —
and they are a package rather than loose files so a test and a ``make`` target
can both name the same machine. A machine the check runs and the tests do not
is two machines, and the second one drifts.
"""
