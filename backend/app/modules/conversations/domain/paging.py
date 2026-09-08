"""How much of a stream comes back at once. **Two numbers, and neither is a
setting.**

``docs/adr/0148`` §3. The cap is enforced at the route as ``Query(le=...)`` so an
over-large request is a **422 by construction** — *not* a silent clamp: a route
that quietly returns something other than what was asked for cannot be told apart
from a route that ran out, and that is a habit worth not starting.

They live in the domain rather than in configuration for the reason every number
in this repository does: an environment that could pick a page size is an
environment where a client's paging works on a laptop and stalls in production.

**And there is no ``has_more`` beside them.** The sequence is gapless, so ``seq``
1 *is* the beginning of the conversation and a flag saying so would be the same
fact twice.
"""

from __future__ import annotations

#: What a page holds when the client does not say.
PAGE_LIMIT_DEFAULT = 50

#: The most a client may ask for in one page. Refused, never trimmed.
PAGE_LIMIT_CAP = 100
