"""The Player profile context — everything a matchmaker needs that a
questionnaire cannot infer (``docs/adr/0089``).

The aggregate is **event-sourced and keyed on the player alone** — the first in
the racket-sport domain that is not per sport, because tags, photos, a week and a
location are facts about a person. The deciding force was the **Proposals
opt-in**, a consent record a boolean column could not evidence; it went with the
search radius in #581, because only the "who fits whom" ranking read either.

What is here today:

- the facts the platform *serves* about profiles — the Social tag vocabulary and
  how many of them a player picks — so no client holds a second copy of either;
- the photo path, whose bytes live behind a port (``docs/adr/0091``);
- the aggregate, its events, and **the one idempotent commit that creates a
  profile** at ``POST /api/v1/players/me/profile`` — which also carries the one
  line a player may write about themselves, the **intro**, fenced at the write
  and stored as its own event (``docs/adr/0170``);
- the profile surface's unkeyed ``PUT``s — the week, and **the location, which
  moves on a cold start** (``docs/adr/0174`` §6): the client puts the phone's
  position silently on every launch, the fix is rounded to the cell exactly as
  the commit rounds it, and a fix in the cell already stored records nothing.
  Everything that reads a location — a group's area, a club's distance, the
  record — loads the profile, so it reads the new cell on its next read;
- **the five writes the You tab needed, on the same surface** (``docs/adr/0179``
  §6, §8) — the tags, the photos, the intro, the gender and the preference. The
  aggregate's heading *Later changes, from the profile screen* is now **true**:
  every transition under it has the route it was written for, one unkeyed
  ``PUT`` per fact. Three of them
  ADR-0170 §5 held back until they could ship together — the intro, the tags
  and the photos — and the intro's is the one that needed a new event,
  ``IntroChanged``, whose ``None`` is the withdrawal (``IntroWritten`` stays the
  commit's, and the fold keeps the latest of either). Each re-validates as the
  commit re-validates, under the commit's codes; the photos are checked against
  the same port the upload used; the two gender writes and the intro's answer
  ``204`` so that *served on one route and no other* (ADR-0179 §4) and *the
  card, the record and its author* (ADR-0170 §3) stay sentences about response
  shapes. Whatever reads one of these facts reads the aggregate, so it follows
  on the next read;
- **the owner's own read, grown for the You tab** (``docs/adr/0179`` §4 and
  §8). ``GET /players/me/profile`` was scoped to what the Play screens edit and
  promised the rest would land on it rather than on a sibling; it now carries
  the tags in the vocabulary's order, the photos in the player's order **each
  with the verdict its uploader is owed** — the three-valued reading, passed,
  flagged, *nobody looked*, read off the store at one ``HEAD`` per photograph —
  the intro, and the two values no other shape may carry: the owner's gender
  and preference. That is ADR-0096 §6's fence **moved, not lowered** — *no
  response shape carries a gender value out* became *no shape a stranger
  reads* — and the contract walk asserts it from both sides, refused everywhere
  else and present on that one shape. The
  location area stays off the wire, and no ``has_location`` stands in for it:
  a profile cannot be committed without one.

What is deliberately **not** here: the ``player_profiles`` read model. It exists
for the many-player reads matchmaking will do, and matchmaking does not exist.
Nothing this context serves reads a projection — *does a profile exist* is
answered from the stream, because the entry gate asks it immediately after the
commit (``docs/adr/0090``).
"""
