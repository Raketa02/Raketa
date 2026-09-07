"""Developer tooling that runs against the backend but ships with nothing.

Nothing under ``app/`` may import from here. These are the offline machines —
the ones that read a document, run the engine over it, and write the answer back
into the document — and they are a package rather than loose files so a test and
a ``make`` target can both name the same harness. A harness the check runs and
the tests do not is two harnesses, and the second one drifts.
"""
