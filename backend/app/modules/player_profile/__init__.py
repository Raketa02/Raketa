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
- the aggregate, its seven events, and **the one idempotent commit that creates a
  profile** at ``POST /api/v1/players/me/profile``.

What is deliberately **not** here: the ``player_profiles`` read model. It exists
for the many-player reads matchmaking will do, and matchmaking does not exist.
Nothing this context serves reads a projection — *does a profile exist* is
answered from the stream, because the entry gate asks it immediately after the
commit (``docs/adr/0090``).
"""
