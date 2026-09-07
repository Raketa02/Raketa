"""The released rulesets, and which one is live.

**A ruleset ships embedded with the code**, so a release is a deploy and this
package is the whole store (``docs/adr/0093``, ``docs/adr/0119``). The runtime
store is deferred until there is enough traffic for an experiment to mean
anything; its arrival changes only where a ruleset is read from, never what the
stamp guarantees — and it replaces this package rather than growing beside it.

**The engine owns the shape; this owns the data.** ``Ruleset`` and
``validate_ruleset`` are ``app/engines/matchfit/ruleset.py``'s, because what makes
a ruleset believable is arithmetic. The numbers are here, because a ruleset names
Social tag ids and an engine may not import the module that owns them.

**Validation runs here, at import.** Every registered ruleset is validated, not
only the live one, so a dataset added in a pull request cannot sit malformed
behind a version string nobody has selected yet. A malformed ruleset raises and
the process does not start: the deploy fails, and the previous ruleset keeps
serving because the old pods are still up. **There is no fallback to defaults** —
a matcher that silently falls back is one that quietly A/B tests against itself.

**Neither version stamp is selected by the environment.** Nothing in this package
reads ``APP_ENV``, or settings at all. `local`, `development`, `staging` and
`production` run the same numbers — a weight is not a setting, it is the product's
opinion about who a player should meet, which is behaviour a domain test can
observe (``docs/adr/0028``).

A released dataset is **never edited**. A second release on one day is a new
letter; a change of numbers is a new name and a new row below.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from app.engines.matchfit.ruleset import Ruleset, validate_ruleset
from app.modules.matchmaking.infrastructure.rulesets import r2026_08_26_a

#: Every ruleset this build carries, by version. Keyed by the stamp that rides on
#: a result, so an old search's ``ruleset_version`` names a row that is still here.
RULESETS: Mapping[str, Ruleset] = MappingProxyType(
    {
        r2026_08_26_a.VERSION: validate_ruleset(r2026_08_26_a.RULESET),
    }
)

#: The ruleset every search runs under. Changing this line is a ruleset release:
#: an offline diff, a deploy, and one line per changed constant in the pull
#: request saying what the hypothesis is and what would falsify it.
LIVE_RULESET_VERSION = r2026_08_26_a.VERSION

#: Resolved once, at import, from a constant — **never from the environment, a
#: setting, a header or a hash of the searcher.** The A/B split that would select
#: a ruleset per search is deferred with a written reason: its success metric is
#: acceptance, which needs the outcome half of the telemetry chain.
LIVE_RULESET: Ruleset = RULESETS[LIVE_RULESET_VERSION]
