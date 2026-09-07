# ADR-0133 — The verdict crosses on the upload, and the warning says the check may be wrong

- **Status:** Accepted
- **Date:** 2026-08-29

> **Amended 2026-09-04 by [ADR-0138](0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)
> on two clauses, and only two.** *The upload carries it; the read does not* still holds for
> `GET /photos/{id}` — the owner's own restored tile — and **`player_card` now carries the
> decision** to a reader who is not the subject, which is a new disclosure this record did not
> weigh. And *fail-open is re-examined and kept* is kept in substance and changed in spelling:
> an unreachable reviewer records **no decision** rather than `ALLOWED`, because the word that
> meant *nothing to warn about* would mean *checked and passed* on somebody else's card. The
> third state this record spelled `null` on the wire is now spelled the same way on the stored
> verdict. **Everything else stands, above all *the note never crosses, in any shape, on any
> route*.**

## Context

[ADR-0129](0129-the-photo-check-is-a-sidecar-the-backend-asks.md) built the on-court check and
shipped it in **measure-only posture** — *"not a mode and needs no flag: it is what the tree
already is. `UploadPhoto` records the verdict as object metadata, no route returns it, and no
client copy shows a warning."*
[ADR-0132](0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md) then made
that metadata honest for the whole bucket, so every photo the platform holds now carries either a
real verdict or a note saying why it does not.

Two sentences in ADR-0129 gave this record its agenda. The posture is measure-only *by
construction*, which means ending it is a code change and not a switch. And its Consequences say,
about failing open: **"That is the correct trade while nothing reads the decision; it is a trade
that has to be re-examined on the day something does."** This is that day.

What is left is one product decision with three edges, and
[#196](https://github.com/Raketa02/Raketa/issues/196) is right that the interesting ones are on
the backend side of a ticket that reads like copy work.

- **`PhotoResponse` is three fields.** `UploadPhoto` returns the verdict to its caller and the
  route drops it; a client cannot warn about something the API does not tell it. So the first
  edge is a contract change ([ADR-0006](0006-backend-owns-api-contract.md)), and it must be
  additive: old builds stay installed on real phones for months.
- **What crosses.** `review-note` holds the model, the prompt-set fingerprint, the confidence and
  the raw similarity vector. Putting it on the wire was considered and rejected, and not only on
  [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)'s *codes, never display text*: the
  note is evidence collected **for us**, so that ADR-0129's explicitly-placeholder threshold can
  be re-derived over stored objects. A confidence on the wire invites a client that renders one,
  and *"we are 38% sure this is a court"* is a number a player can do nothing with, drawn from a
  line nobody has calibrated. The decision crosses; the evidence does not.
- **Which routes.** `PhotoResponse` serves the upload and the read from one shape, and its
  docstring names that as a feature — *a client renders a tile it has just filled and a tile it
  is restoring with one code path*. Splitting the shape costs that. Populating the field on the
  read costs a request per object: `GET /photos/{id}` proves existence and signs a URL, and user
  metadata is a separate call in every S3-compatible store.

Two things were **not** re-opened. There is no `REJECTED`, and there will not be one here: the
check soft-warns, and a false reject stops a real player on their first day. And the threshold and
the prompt set stay where ADR-0129 put them — tuning them wants the corpus, not this record.

## Decision

We will **return the verdict on the upload response, as a code, and warn the player in copy that
says the check may be wrong about them.**

- **One additive optional field, `review`,** carrying `PhotoReviewDecision` — `allowed` or
  `flagged` — on the shared `PhotoResponse`. A code and never a sentence; the client owns the
  words, in its own copy and its own language. **The backend never grows a `message` beside it.**
- **The upload carries it; the read does not, and `null` is not `allowed`.** Two reasons, and
  neither is that the read is harder. A warning belongs to the moment a player *chose* a
  photograph — a tile being restored is one they already kept, and saying it again is a screen
  re-litigating a decision the player made. And the read would pay a metadata request per tile for
  a fact no client asks it for. The shape stays one shape and the tile stays one code path; what
  differs is whether a given response has anything to say. A client that was told nothing warns
  about nothing, which is why the third state is spelled `null` rather than folded into `allowed`
  at the boundary that knows least.
- **The note never crosses, in any shape, on any route.** No confidence, no similarity vector, no
  model name, no fingerprint. It stays on the object, where the re-review backfill and a future
  threshold derivation read it.
- **Fail-open is re-examined, as ADR-0129 required, and kept.** Now that something reads the
  decision, an unreachable reviewer means the player is **not warned** rather than wrongly warned
  — which is the right way round. A sentence produced by our own outage would be a fact about our
  infrastructure delivered to a player as a fact about their photograph. The cost of an outage is
  therefore *silence*, not *noise*, and it stays queryable: the `unavailable=` population is
  closed, counted and re-reviewed by ADR-0132's job.
- **The measure-only posture ends here, and it ends the way it began — without a flag.** There is
  no mode, nothing to toggle and nothing to roll back to; what changes is what the response says.
- **The warning's copy is bound by four rules, and they are part of this decision rather than an
  implementation detail of it.** Some unknown share of the people who read it are on a court in
  the photograph they just picked, and the flag rate is a fact about a corpus nobody has measured.
  So the sentence: is written as **our failure to see** rather than the player's failure to comply
  (*we could not see a court*, never *this is not an on-court photo*); says **nobody has looked**,
  because nothing reviews a flagged photo a second time and there is no queue at the end of one;
  says **nothing is blocked**, because the photo is stored, keeps its id, is committed with the
  profile and never touches `Continue`; and names the **choice keep-first**, because the player
  the check is wrong about is the one the sentence risks insulting.
- **The step still does not announce the check up front.** Saying *we check every photo* to the
  majority whose photo is fine is small print, and it reads as a threat to the rest — the same
  argument that already took two lines off that step. The check earns a sentence at the one
  moment it has a claim to make.

## Consequences

**Easier**

- The soft-warn is finally a warning. Between ADR-0129 and today the check was a measurement with
  no effect on anything; a player whose photo shows a car now finds out at the moment they can
  cheaply do something about it, rather than never.
- The threshold gains a second falsifier and it is a behavioural one: photos swapped after a
  warning. Until now the only evidence was the stored distribution, which says what the model
  thinks and nothing about whether players agree.
- Nothing about the collection changed. A flagged photo keeps its position, keeps the lead if it
  had it, is in `photo_ids`, and the commit is untouched — so *the check never blocks* is a
  property of the shapes rather than a rule somebody has to keep obeying.

**Harder**

- **We are now telling real people something about their photographs, at a threshold ADR-0129
  itself calls a placeholder.** Every point of flag rate is a sentence shown to somebody, and an
  unknown share of those sentences are wrong. The number moved from one nobody could feel to one
  that costs copy, which is the correct pressure and is still pressure that did not exist
  yesterday.
- **`null` versus `allowed` is a distinction a careless client will collapse**, and collapsing it
  the wrong way warns everybody about everything. It is documented on the field and on both
  routes; the player app collapses it *toward silence* at its wire boundary, and a second client
  gets no help from anything mechanical.
- **The four copy rules are enforced by tests in one client and by this record everywhere else.**
  A second client would have to be told them again. That is the honest cost of the backend
  emitting codes: the words are exactly where the rules cannot follow them.
- **The read is now the poorer of the two routes**, which it was not before. The day something
  wants a verdict on a restored tile, it pays a metadata read per photo, and this record is where
  the argument for that has to be re-opened.
