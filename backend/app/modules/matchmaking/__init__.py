"""The Matchmaking context — what is left of the stateful half of the matcher.

``docs/adr/0093`` split the matcher in two. The arithmetic is an engine at
``app/engines/matchfit/``; the half that touches the world is this module.

**The searches, the deck and the radar are gone** (#579, PRD #569): the
shortlist and its read-back, the line-ups and their forecast, *Let's play*, the
deal and *Show them again*, the pass, the prompts and the reading, with their
ledgers, their tables and their jobs. A game is made one way now — a group's
Games deck books it — and nothing here searches for anybody.

**What the new games kept is pure and small**:

- ``domain/balance.py`` — how even a game between two sides is forecast to be,
  read once for the Games card and the booked game's screen;
- ``domain/level_window.py`` — the level window and the newcomer window that
  tightens it, asked of every pair the proposer, the fill and a rescue would
  seat;
- ``domain/geography.py`` and ``domain/areas.py`` — distances to clubs and the
  areas a record is drawn with;
- the three outward ports in ``domain/ports.py`` — two account gates the player
  record asks, and the at-stake read a booked game's pairing prints;
- the released ruleset (``infrastructure/rulesets/``) those readings run on.

**The ranking and the candidate index went too** (#580): nothing scores one
player against another, and nothing keeps a picture of the city to search.
"""
