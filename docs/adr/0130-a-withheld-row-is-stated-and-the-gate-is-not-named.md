# ADR-0130 — A withheld row is stated; the gate that withheld it is not named

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

[ADR-0109](0109-a-read-back-names-what-it-withholds.md) settled the read-back:
`GET /api/v1/searches/{id}` re-reads the gates that fail closed against live state, the
stored record is not rewritten, and **a withheld row is stated rather than vanished** —
because a list that quietly gets shorter is the same class of lie as a breakdown that
quietly stops adding up.

It said one more thing, in a sentence that had no code under it at the time:

> **The response says a row was withheld, and why, in the coarse gate spelling already in
> use.**

Building it, *and why* turned out to contradict an accepted record it cites two paragraphs
earlier. [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)
decides that a block is a directed record with a symmetric effect and that **neither party
is ever notified, and the other side sees no trace anywhere in any response.** A read-back
carrying `withheld: BLOCKED` is exactly that trace, delivered to the one person the block
was designed to be invisible to — and it is delivered on a shortlist *they already saw*,
where the row's position tells them which person it is about.

The other three fail-closed gates fail the same test for their own reasons. A **hold** and
an **account that may not be shown** are moderation facts about a third party, and
ADR-0095 and [ADR-0124](0124-the-matcher-gates-account-state-never-age.md) both say they
are told to nobody. A **gender preference** is a safety setting whose owner is the only
person entitled to read it ([ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)), and
*nothing on any screen reveals how many people it hid* — a per-row disclosure is a
stronger leak than the count that rule already refuses.

So the coarse gate spelling is not publishable on this route. It is also, on inspection,
not *needed*: nothing on the screen behaves differently per cause, and there is no recovery
a searcher could take from any of the four.

## Decision

**The read-back states that a row is withheld and does not say which gate withheld it.**

One shape, one field:

```jsonc
{ "withheld": true }
```

Four causes — a block in either direction, a hold, an account `users` may not show, and the
mutual gender preference — reach the wire as **one indistinguishable statement**. ADR-0109
§1's *stated, never vanished* stands unchanged and is what this route is built on; only its
*and why* is struck.

**The withheld row is a separate wire shape, not a candidate with holes.** It carries no
`player_id`, no card, no Fit and no breakdown — a union member with exactly one field, so
that *render a person the product has agreed to stop showing* is not a shape the contract
can hold and not a branch a renderer can forget. The searcher loses nothing they are owed:
they were shown this row when they ran the search, and the only new fact is that the
product will no longer show it.

**One exemption is recorded where the rule lives.** The central fence
(`tests/unit/test_no_response_carries_a_forbidden_fact.py`) refuses the word *withheld* on
any response schema, for layer 3 — *a player may ask why somebody was shown; nobody may ask
who was withheld*. That rule is about a person the searcher was **never shown**, named to
them for the first time. This field is about a person they were shown this morning, and it
names nobody. It goes in that module's `PERMITTED` list with its reason attached;
`withheld_reason` and `near_miss_count` are still refused, which is what keeps this an
exemption for one field rather than a weakened rule.

## Consequences

**A searcher can still infer that *something* changed about a specific row**, and that is
unavoidable and accepted: it is the direct cost of ADR-0109's refusal to shorten the list
silently. What is bought is that the inference stops at *this person is no longer shown to
me*, which is four different facts wearing one sentence, rather than *this person blocked
me*, which is one fact and the one ADR-0095 forbids. Splitting out the searcher's **own**
block as a distinguishable cause was considered and rejected: it tells them nothing they do
not already know, and it makes the residual statement more informative by elimination.

**Nobody is told which gate, including support.** The gate histogram
(`search.excluded_by_gate`) is per search and counts only, and it is unchanged and remains
internal; investigating *why did this row go* means reading the record beside live state,
which is a thing an operator does and not a thing a route answers.

**The client branches on a union.** `candidates` is
`(CandidateSchema | WithheldRowSchema)[]` in the generated types, so every render site has
to discriminate. That is the point — the alternative was optional `player_id` and
`player_card` on the candidate, which weakens the contract on the `POST` path, which is the
one every screen uses, in order to describe a case that only ever occurs on the other one.

**The record had to grow to make the round trip true.** A read-back reproduces *the
recorded answer*, so everything on a row has to come off the row; the card, the concerns,
the whole-kilometre distance and the at-stake block were previously assembled at response
time from sources that keep moving. They are now recorded
(`0011_search_candidate_records_the_answer`), which is ADR-0107's *the record stores a
`photo_id`; the URL is minted per response* taken literally, and it is what makes both
routes render the same type through one function.

**Three things about the *search* route changed on the way, and are named here
rather than left in a docstring.**

1. **`sorts_available` now reads whole kilometres on both routes.** *Closest* used
   to be judged on the measurement; the record stores the integer the wire
   carries, so judging on the measurement would make the two routes disagree
   about whether a control is honest. It is also the more correct of the two:
   offerability is a claim about what the **client** could do with the rows it
   holds, and the client holds an integer — two candidates 3.2 km and 3.4 km away
   are one distance to it. The visible effect is that a narrow spread that used
   to draw *Closest* no longer does, which is the rule working rather than
   loosening.
2. **`sorts_available` is a third departure from *the recorded answer*.** ADR-0109
   named two — a re-verified row and a re-minted photo link. This adds one, and
   deliberately: after a withholding the reader is holding different rows, and a
   control that would now reorder nothing must not be drawn. The round-trip test
   asserts the envelope reproduces when nothing was withheld, which is where the
   original clause bites.
3. **A held reader is refused their own old answers**, with the same
   `account_held` the search returns. A held player can still sign in, so
   refusing them a fresh search while handing back this morning's would be the
   hold ending at the one route that remembers.

**`withheld` will sometimes mean *we cannot check*, and that is the fail-closed
rule working.** The mutual gender preference is the only fail-closed gate whose
other half lives on the index row, so a candidate the partition no longer holds
has no preference to read — and *a gate that cannot be evaluated excludes*. A
reader cannot tell that case from a block, which is the same indistinguishability
this record is built on; what it costs is that a withheld row is a slightly
weaker signal about the world than *somebody blocked you* would be. The
alternative — treating *not indexed* as *still fine* — is serving a row on a gate
nobody evaluated, and that is the failure this whole route exists to prevent.

**And the read-back costs slightly more than ADR-0109 priced it at.** That record said *a
lookup plus a block-set read*; the mutual gender gate makes it a lookup, three set reads and
one snapshot binding, because gender is the one fail-closed gate whose other half lives on
the index row — and resolving twenty ids inside that container is a pass over the partition,
because `CandidateSource` deliberately answers with the container and never with questions
about rows ([ADR-0112](0112-the-snapshot-is-a-per-partition-container-bound-once.md)). The staleness ladder is deliberately **not** applied — it refuses on ranking
quality ([ADR-0111](0111-the-index-holds-only-what-a-player-changes-about-themselves.md))
and a read-back ranks nothing — but a candidate the index no longer holds has no preference
to read, so that gate cannot be evaluated, and *a gate that cannot be evaluated excludes*.
