"""``make gen-cohort`` — rewrite the seed cohort's committed population.

The repository's generate-commit-diff idiom, fourth instance: the generator is in
code, its output is committed, and a generator edit therefore arrives as a
**visible population diff** rather than as a fixture that silently became a
different fixture.

**It writes inputs only.** No level, no uncertainty and no band is in the file —
those are the engine's answers to the questionnaire each member sits, and a
committed copy of an answer is a second number nothing keeps honest. What makes
the file worth committing is the keying: every draw is a function of the member's
handle alone, so adding or removing one member changes that row and nobody else's
and the diff is readable.

It lives in ``scripts/`` and not in ``app/seeds/`` because it is a developer
command and not something a container runs: the image copies ``app/`` so that
``make seed`` works where the database is, and regenerating a committed artifact
is done on somebody's laptop against the repository.
"""

from __future__ import annotations

from app.seeds.cohort import ARTIFACT, generate, write


def main() -> int:
    path = write(generate())
    print(f"wrote {path.relative_to(ARTIFACT.parents[3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
