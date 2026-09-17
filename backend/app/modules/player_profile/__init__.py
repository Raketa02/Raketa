"""The Player profile context — everything a matchmaker needs that a
questionnaire cannot infer (``docs/adr/0089``).

The aggregate is **event-sourced and keyed on the player alone** — the first in
the racket-sport domain that is not per sport, because tags, photos, a week, a
location and a consent are facts about a person. The deciding force was the
**Proposals opt-in**: it is a consent record rather than a preference, and a
boolean column cannot evidence one.

What is here today:

- the two facts the platform *serves* about profiles — the Social tag vocabulary
  and the Search radius bounds — so no client holds a second copy of either;
- the photo path, whose bytes live behind a port (``docs/adr/0091``);
- the aggregate, its events, and **the one idempotent commit that creates a
  profile** at ``POST /api/v1/players/me/profile`` — which also carries the one
  line a player may write about themselves, the **intro**, fenced at the write
  and stored as its own event (``docs/adr/0170``);
- the profile surface's unkeyed ``PUT``s — the week, the radius, and **the
  location, which moves on a cold start** (``docs/adr/0174`` §6): the client
  puts the phone's position silently on every launch, the fix is rounded to the
  cell exactly as the commit rounds it, and a fix in the cell already stored
  records nothing. It is the first caller ``change_location`` ever had in
  ``app/``, and everything that reads a location — every deck pool, every
  radar, every *In your area* — follows the candidate projection, which has
  applied ``LocationChanged`` since it was built (``docs/adr/0110``);
- **the owner's own read, grown for the You tab** (``docs/adr/0179`` §4 and
  §8). ``GET /players/me/profile`` was scoped to what the Play screens edit and
  promised the rest would land on it rather than on a sibling; it now carries
  the tags in the vocabulary's order, the photos in the player's order **each
  with the verdict its uploader is owed** — the three-valued reading, passed,
  flagged, *nobody looked*, read off the store at one ``HEAD`` per photograph —
  the intro, the standing opt-in answer, and the two values no other shape may
  carry: the owner's gender and preference. That is ADR-0096 §6's fence
  **moved, not lowered** — *no response shape carries a gender value out*
  became *no shape a stranger reads* — and the contract walk asserts it from
  both sides, refused everywhere else and present on that one shape. The
  location area stays off the wire, and no ``has_location`` stands in for it:
  a profile cannot be committed without one.

What is deliberately **not** here: the ``player_profiles`` read model. It exists
for the many-player reads matchmaking will do, and matchmaking does not exist.
Nothing this context serves reads a projection — *does a profile exist* is
answered from the stream, because the entry gate asks it immediately after the
commit (``docs/adr/0090``).
"""
