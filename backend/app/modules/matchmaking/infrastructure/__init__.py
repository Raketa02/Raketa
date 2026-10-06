"""Where the Matchmaking context meets the outside.

Today that is two things. The first is **the ruleset store**. It is embedded —
a Python package rather than a table or a file — because ``docs/adr/0093`` ships
a ruleset with the code and defers the runtime store until there is enough
traffic for an experiment to mean anything. *Its arrival changes only where the
file is read from, never what the stamp guarantees*, and this package is the
*where*.

It sits here rather than in the engine for a reason the fence makes concrete: a
ruleset names Social tag ids, and **an engine may not import a module**. Written
in the engine, the nineteen ids would have to be retyped — a second copy of a
closed vocabulary, free to drift, which
``tests/unit/test_social_tag_vocabulary.py`` refuses outright. Written here they
are read from the one place that owns them.

So the split is: the **engine** owns what a ruleset *is* and what makes one
malformed; the **module** owns the dataset and hands it over. That is the same
split the deferred runtime store will need, arriving early rather than late.

The second is **the far side of the three outward ports** — the one honest
null object in ``absent_providers.py`` (``NoHoldsExist``), and the real adapters
in ``users_account_status.py`` and ``rating_at_stake.py``. A null object says
something true about this platform today and stops being true on the day its
provider lands.

The third is the **composing adapter** a provider signs on the matcher's side of
the arrow: ``games_court_pairing.py``, the booked game's pairing (#575). And the
fourth is the **candidate index** — its model, its tail, its snapshot source and
its rebuild — which nothing reads since the searches went (#579) and which goes
with the ranking (#580).
"""
