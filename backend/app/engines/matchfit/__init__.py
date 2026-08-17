"""The Match Fit engine: how good one match is for one player, and how much of
that was actually measured.

``core`` holds everything that must outlive a version — the two term builders that
make a term's kind a fact about how it was built, the renormalisation the score is
computed through, the decay curve a declared numeric limit shares, the contribution
ranking a reason list is ordered by, and the one crossing from exact ratios into a
whole percent. A version owns the *constants*: the weights, how far past a ceiling
the decay runs, what a mismatch is worth, and the threshold a warning fires at.

Each shipped version is a directory that is never deleted, because a score quoted
against a match is interpretable only through the code that produced it — and
because a term that was *excluded* in one version and scored in the next is a
different claim about the same match.

**This engine never runs the pairing engine.** It takes the analysis as an input
value, so the score and the card drawn beside it come from one pairing by
construction (``docs/adr/0026``). ``.importlinter`` forbids the two packages from
importing each other in either direction, and ``make test-gates`` proves that
contract fires.
"""
