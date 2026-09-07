"""The synthetic ruleset diff: the population, the run, and the report.

``docs/adr/0119`` collapses ``matchmaking-engine.md`` §22's rollout ladder into
one gate and one deploy: **shipping a ruleset is an offline diff then a deploy**,
with shadow and canary priced and deferred. This package is the mechanical half
of that gate — the half a machine can hold — and it is the repository's own
generate-commit-diff idiom for the third time, after ``make gen-api`` and
``make gen-judged-pairings``.

**Four modules, split by what they change for.**

- ``population`` — the fixture ADR-0121 argues for. Changes when the corpus's
  construction does.
- ``corpus`` — the searches that population runs. Changes when a surface does.
- ``answers`` — the run and the committed record. Changes when the pipeline's
  outputs change shape.
- ``report`` — the classification and the printed diff. Changes when the release
  argument wants a different number in front of it.

``__main__`` is the command. This is ``app/engines/matchfit/v1/``'s shape two
directories over, for the same reason.

**The other half of the gate is a signature and it is said out loud.** The
recorded-corpus diff cannot run in CI — there is no database, and ADR-0118 §7
restricts it to a restore — so what CI asserts about it is that the pull request
carries a report block naming its corpus window and its coverage: **presence,
not truth.** Pretending otherwise would be the decoration this map exists to
refuse.
"""
