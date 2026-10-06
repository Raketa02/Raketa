"""The released ruleset, and which one is live.

**A ruleset ships embedded with the code**, so a release is a deploy and this
package is the whole store (``docs/adr/0093``, ``docs/adr/0119``).

**The engine owns the shape; this owns the data.** ``Ruleset`` and
``validate_ruleset`` are ``app/engines/matchfit/ruleset.py``'s, because what makes
a ruleset believable is arithmetic.

**Validation runs here, at import.** A malformed ruleset raises and the process
does not start: the deploy fails, and the previous ruleset keeps serving because
the old pods are still up. **There is no fallback to defaults.**

**The version stamp is not selected by the environment.** Nothing in this package
reads ``APP_ENV``, or settings at all. `local`, `development`, `staging` and
`production` run the same numbers — who may share a court is behaviour a domain
test can observe (``docs/adr/0028``).

**One release is carried** (#580). The older two were kept so that a recorded
search could name the numbers it ran under; the searches went in #579 and
nothing else records a ruleset version. That cut took sections out of the live
dataset and moved no number in it; past it, a released dataset is **never
edited** — a change of numbers is a new name and a new module here.
"""

from __future__ import annotations

from app.engines.matchfit.ruleset import Ruleset, validate_ruleset
from app.modules.matchmaking.infrastructure.rulesets import r2026_09_15_a

#: The ruleset every reader runs under. Changing this line is a ruleset release:
#: a deploy, and one line per changed constant in the pull request saying what
#: the hypothesis is and what would falsify it.
LIVE_RULESET_VERSION = r2026_09_15_a.VERSION

#: Resolved once, at import, from a constant — **never from the environment, a
#: setting or a header.**
LIVE_RULESET: Ruleset = validate_ruleset(r2026_09_15_a.RULESET)
