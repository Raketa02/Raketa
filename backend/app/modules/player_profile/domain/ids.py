"""Identity in the Player profile context — one stream that needs no id, and
one that does.

**A profile's stream id is the player id itself.** There is no derivation and no
namespace here for it, because there is nothing to derive *from*: the aggregate
is keyed on the player and only the player (``docs/adr/0089``), so the store's
own uniqueness on ``(aggregate_type, aggregate_id, version)`` is what makes *at
most one profile per player* something the database enforces. That is stated
here rather than left implicit because this is the file somebody looking for a
``player_profile_id`` function will open.

**A Play intent declaration's is derived, because its key is a pair.** One
stream per ``(player, sport)`` (``docs/adr/0094``), collapsed by ``uuid5`` in
exactly the shape ``skill_rating_id`` established
(``docs/adr/0019``, ``app/modules/rating/domain/ids.py``). *Levels never
transfer between sports, and intent does not either* stops being a rule to
remember and becomes structural: **no object in the system holds two sports'
intent at once, so there is nothing to transfer.**

Its own namespace, and never the rating's: two aggregates keyed on the same pair
would otherwise compute the same uuid, and the aggregate-type column is all that
would keep their streams apart. That is one column too few to hang a data
corruption on.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from app.kernel import Sport

_PLAY_INTENT_NAMESPACE = uuid5(NAMESPACE_URL, "rakieta/play-intent-declaration")


def play_intent_declaration_id(player_id: UUID, sport: Sport) -> UUID:
    """The deterministic event-stream id for one player's intent in one sport.

    **A concurrency control as much as a naming convenience**, the way the
    assessment's is (#35): two declarations for the same pair that both read an
    empty stream compute the same id, collide on version 1 of one stream, and
    the store rejects the loser. With a random id per call each would have minted
    its own stream and both would have succeeded, leaving one pair holding two
    intents with no rule for which answers.

    Guessable by anyone who knows a player id, and that leaks nothing: reading a
    declaration requires saying whose it is.
    """

    return uuid5(_PLAY_INTENT_NAMESPACE, f"{player_id}:{sport.value}")
