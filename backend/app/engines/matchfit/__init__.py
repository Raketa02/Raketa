"""The Match Fit engine — the pure half of what the new games read about a court.

``docs/adr/0093`` split the matcher across the fence this layer already draws:
the stateful half is a module at ``app/modules/matchmaking/``, and everything
that is *arithmetic* is here, under ADR-0015's rules unchanged — no clock, no
randomness, no hidden state, no module, no framework, no I/O library.

**The "who fits whom" ranking is gone** (#580, PRD #569). Scoring, its eight
terms and their evidence, the modifiers, Liveness, the quality floor, the fit
ranking, the line-up enumeration and the group objective were what the searches,
the deck and the radar called, and those went in #579. What is left is what the
Games deck, the fill, rescues, posting and the booked game call:

``core``
    The vocabulary: the kind of game (``SearchMode``), the six reliability
    strands a Player Score is read in, and the one assumption a provisional
    forecast makes.

``ruleset``
    What a ruleset *is* and what makes one malformed — now the balance rules and
    each kind of game's level tolerance. **The type is here; the dataset is
    not**: the released one lives at
    ``app/modules/matchmaking/infrastructure/rulesets/``.

``scorable`` and ``grouping``
    What crosses in — a Level, an hour of the week — and what comes back: a
    forecast and the two side strengths it was read from.

``v1``
    The arithmetic: the forecast between two sides and the hours a court shares.

**Neither the ruleset nor anything here is ever selected by the environment** —
`local`, `development`, `staging` and `production` run the same numbers
(``docs/adr/0028``). Who may share a court is behaviour a domain test can
observe.
"""
