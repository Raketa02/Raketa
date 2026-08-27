"""The Match Fit engine — the pure half of the matcher.

``docs/adr/0093`` splits the matcher across the fence this layer already draws:
the stateful half (the candidate index, the ledgers, the telemetry) is a module
at ``app/modules/matchmaking/``, and everything that is *arithmetic* is here,
under ADR-0015's rules unchanged — no clock, no randomness, no hidden state, no
module, no framework, no I/O library.

**The name is taken back.** An engine called Match Fit was removed in the
2026-08-25 reset; inventing a synonym to avoid a ghost would have cost the
correct domain term permanently (``docs/adr/0093``).

Three things live here, and the split between them is the point:

``core``
    The vocabulary that outlives both version stamps — the two search modes, the
    eight terms, the evidence kinds they emit, the six reliability strands, the
    tag-relationship shape. A ruleset names these; a version computes with them;
    neither may redefine one.

``ruleset``
    What a ruleset *is*, and what makes one malformed. A ruleset is a named,
    dated, frozen dataset of every number the engine uses, validated on load.
    **The type is here; the datasets are not.** A ruleset names Social tag ids
    and an engine may not import the module that owns them, so the released
    datasets live at ``app/modules/matchmaking/infrastructure/rulesets/`` — which
    is also where the deferred runtime store will land, since *its arrival
    changes only where the file is read from*.

``v1`` and its successors
    A version is a directory that is never deleted, because the maths a result
    was computed with must stay readable forever. It holds the scorer: what
    crosses the privacy fence, the evidence a term explains itself in, the eight
    terms, and the renormalisation that turns them into one printed number.

**Two version stamps ride on every result and they mean different things**
(``docs/adr/0093``, ``docs/adr/0106``): the **engine version** says how the maths
works, the **ruleset version** says what the numbers were. **Neither is ever
selected by the environment** — `local`, `development`, `staging` and
`production` run the same numbers (``docs/adr/0028``). A weight is not a setting:
it is the product's opinion about who a player should meet, which is behaviour a
domain test can observe.

**Where the line falls between them is ``docs/adr/0106``:** a number is ruleset,
a *shape* is the API contract. Moving a weight is a ruleset release and free.
Adding or reshaping an evidence variant is an API release, because the client
generates an exhaustive renderer per variant and must never be handed a shape it
cannot draw.
"""
