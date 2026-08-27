"""Where the Matchmaking context meets the outside.

Today that is one thing: **the ruleset store**. It is embedded — a Python package
rather than a table or a file — because ``docs/adr/0093`` ships a ruleset with the
code and defers the runtime store until there is enough traffic for an experiment
to mean anything. *Its arrival changes only where the file is read from, never
what the stamp guarantees*, and this package is the *where*.

It sits here rather than in the engine for a reason the fence makes concrete: a
ruleset names Social tag ids, and **an engine may not import a module**. Written
in the engine, the nineteen ids would have to be retyped — a second copy of a
closed vocabulary, free to drift, which
``tests/unit/test_social_tag_vocabulary.py`` refuses outright. Written here they
are read from the one place that owns them.

So the split is: the **engine** owns what a ruleset *is* and what makes one
malformed; the **module** owns the dataset and hands it over. That is the same
split the deferred runtime store will need, arriving early rather than late.
"""
