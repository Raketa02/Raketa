# ADR-0138 — The verdict crosses on a card, and *never checked* is its own answer

- **Status:** Accepted
- **Date:** 2026-09-04
- **Amends [ADR-0133](0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)**
  on two clauses: *the read does not carry it* becomes **the card does**, and *fail-open
  records `ALLOWED`* becomes **fail-open records nothing**. Everything else in that record —
  above all *the note never crosses, in any shape, on any route* — stands untouched.
- Settles [#307](https://github.com/Raketa02/Raketa/issues/307) on
  [#302](https://github.com/Raketa02/Raketa/issues/302)'s spec.

## Context

Part 1 of the redrawn competitive card puts a **✓ ON COURT** shield on the photo panel:
*"confirmation the photo passed the rule that photos must be taken on a court. It appears on
every approved photo, and its absence would mean the photo hasn't been checked."*

That is one sentence of design and two decisions of ours, and both are in ADR-0133.

**The verdict does not cross on a read, on purpose.** ADR-0133 returns `PhotoReviewDecision`
on the upload response and states in writing why the read does not: *"a warning belongs to
the moment a player chose a photograph"*, and a restored tile is a photograph the player
already kept. That argument is about **the uploader's own tile** and it is still right. A
shield on somebody else's card is a different act — a **new disclosure about a third party**,
on a different route, to a reader who is not the subject — so it is not covered by that
clause and cannot be smuggled under it. It is a decision, and this is the record of it.

**The verdict fails open, so a tick would be a lie.** `verdict_when_unreviewable` returns
`ALLOWED` with a note saying nothing was really looked at. ADR-0133 kept that deliberately —
*"an unreachable reviewer means the player is **not** warned rather than wrongly warned"* —
and that is right for a warning and wrong for a badge. Under the design's own semantics a
photo nobody could check would wear a tick claiming it passed, and the tick would be shown
to twenty people who are not its owner.

Two more forces shape the answer, and neither is a matter of taste.

- **The corpus is not uniform, and it will not be for hours at a time.** As the tree stands,
  three populations carry `review: allowed` about images nothing looked at: the pass-through
  era, which wrote the word by construction; every upload that arrived during a past sidecar
  outage; and every *future* outage, on for ever, because that is what fail-open writes.
  [ADR-0132](0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)'s
  job drains the first two, through a listing that costs one `HEAD` per object and a budget
  deliberately kept small. The third is not a backfill's problem at all — it is the write
  path's. So *the backfill has been round* is not a precondition anything can wait on, and
  the growing population has to stop being written rather than be cleaned up after.
- **A verdict costs a store round trip, per photograph, whenever it is read.** It is user
  metadata: no listing carries it, no presign reads it. ADR-0133 named this as the reason the
  read stayed the poorer route, and said *"the day something wants a verdict on a restored
  tile, it pays a metadata read per photo, and this record is where the argument for that has
  to be re-opened."* This is that day, for a different route than the one it predicted.

One thing is **not** re-opened. The threshold is still `ON_COURT_CONFIDENCE_THRESHOLD = 0.5`,
still documented as provisional, and it is now load-bearing in a way it was not: a genuine
on-court photo scoring 0.49 leaves its owner silently unbadged on twenty other people's
screens. Every verdict records the similarities it was computed from, so the number is
re-derivable over stored objects **without re-running inference** — filed as
[#316](https://github.com/Raketa02/Raketa/issues/316) and deliberately not blocking here. It
is the same trade ADR-0129 made and ADR-0133 restated, taken one notch further, and it is
recorded rather than resolved.

## Decision

We will **publish the on-court decision on the player card, and make *never checked* a third
answer rather than a shade of `allowed`.**

- **Three answers, and only the first draws a shield.** *Checked and passed*, *checked and
  flagged*, *not checked*. The third is spelled as an **absence** — `None` on a verdict, no
  key on the object, an omitted field on the wire — and never as a fourth value on
  `PhotoReviewDecision`. That enum says what the reviewer **concluded**; *nobody looked* is
  not a conclusion about an image. ADR-0133 already spelled the uploader's third state `null`
  *"rather than folded into `allowed` at the boundary that knows least"*, and the stored
  verdict is the boundary that was folded.
- **`verdict_when_unreviewable` records no decision.** Fail-open survives whole and is
  restated honestly: an outage costs **silence in both directions** — no warning to the
  uploader, no shield to a stranger. Nothing is refused, nothing is flagged, and the note
  goes on saying which outage it was so ADR-0132's job can find it.
- **A stored decision is believed only where the note proves a score was taken** —
  `decision_on_record`, beside the encoder that writes it. All four fields (model, prompt
  set, confidence, raw vector) or nothing. This is what makes the shield safe on the first
  commit rather than on the last object of the last backfill run: the three legacy
  populations read as *not checked* immediately, and ADR-0132's job then makes the metadata
  honest at its own pace instead of being the thing a badge waits on. **The backfill is the
  cleanup, not the gate.**
- **The card records the verdict; it does not mint one.** `PlayerCardSource` reads it beside
  the nickname and the first photo, and `RecordedCard` stores it — so the `POST` pays at most
  one `HEAD` per row that has a photograph, over the twenty rows that survived the floor
  rather than over the pool, and the read-back pays nothing. This is the opposite of
  `photo_url` and the reason is the mirror of it: a link is dead within the hour so it cannot
  be stored, and a verdict is a round trip so it must not be re-read on every response.
  ADR-0109's rule decides the rest — a read-back reproduces **the card that was shown**, so a
  photo re-reviewed since does not rewrite the shield on a search somebody ran last week.
- **The field is additive and optional, on `player_card` and nowhere else.**
  `GET /photos/{id}` is unchanged and still carries nothing: that route serves the owner
  their own tile, and ADR-0133's argument about re-litigating a decision the player already
  made is untouched by anything here. Old builds stay installed on real phones for months and
  are entitled to a card with no shield on it.
- **The note never crosses, in any shape, on any route.** No confidence, no similarity
  vector, no model name, no fingerprint — ADR-0133's clause, restated because this record
  opens a second route and a rule that is not restated at a new boundary is a rule that
  leaks. *"We are 38% sure this is a court"* is still a number a player can do nothing with,
  and it is now a number about **somebody else**, which is worse.

**No moderation queue, no appeal, and still no `REJECTED`.** A flagged photo keeps its
position, keeps the lead if it had it, is in `photo_ids`, and commits like any other. What
changes is a shield that is not drawn.

## Consequences

**Easier**

- ***Has this photo been checked* is finally answerable from the wire.** It was decidable
  from stored metadata after ADR-0132 and readable by nobody; the distinction the note has
  carried since ADR-0129 now reaches the one place it was collected for.
- **Fail-open stopped being a word that meant two things.** `ALLOWED` was carrying *the
  model said yes* and *nobody asked* in one string, which was survivable while one person
  read it and is not once twenty do. Every reader downstream of `decision_on_record` gets the
  distinction for free, including readers that do not exist yet.
- **The threshold gains its third falsifier, and it is the one with teeth.** ADR-0133 added
  photos swapped after a warning; this adds photos whose owners never see a shield and never
  find out why. That is not a signal we can read — which is exactly why
  [#316](https://github.com/Raketa02/Raketa/issues/316) exists and why the note is stored.

**Harder**

- **We are drawing a conclusion about somebody's photograph on twenty strangers' screens, at
  a threshold nobody has calibrated.** ADR-0133 called the same number *the correct pressure*
  when the cost of being wrong was one sentence shown to the person it was about. The cost is
  now a shield **withheld** from a real player, in front of everybody, silently, with no
  copy to soften it and nothing they can do. It is the sharpest version of the trade ADR-0129
  opened, and it is being taken knowingly.
- **A card assembly now touches the object store, and that is a new dependency for a
  search.** One `HEAD` per row with a photograph, on the `POST` only. It is the same bounded
  shape `PlayerCardSource`'s profile read and `CardPhotoLinks`' signing already have — after
  the floor, twenty rows, never the pool — and it is the first time the shortlist's
  **latency** depends on the store answering rather than only on it signing. They are issued
  **together rather than one after another**, which the neighbouring reads cannot be: a
  profile is folded through the request's own session and an `AsyncSession` is not safe to
  use concurrently, while a verdict shares nothing but the adapter, which builds a client per
  call. So the cost is one store latency and twenty client constructions rather than twenty
  latencies end to end. If it ever stops being affordable the fix is the one its neighbours
  name: a batched method on the provider's port, not a table beside the blobs.
- **The record now stores a fact that can go stale, and states it as history.** A photo the
  backfill re-reviews tomorrow keeps yesterday's absence on yesterday's search. That is
  ADR-0109 working — a read-back is not a cache and reproduces the answer that was given —
  and it is still a shield that is *wrong today* on a screen somebody can open today.
- **`decision_on_record` is a second reader of the note, and the two must not drift.** It
  asks the same string `review_standing` asks, for the opposite purpose: one decides *who
  still owes a look*, the other *what may be drawn*. They are in one module beside the
  encoder for the reason ADR-0132 put them there, and a third reader of that string belongs
  in the same file or nowhere.
- **`null` versus `allowed` is now a distinction two clients could collapse, not one.**
  ADR-0133 documented the hazard on the upload; the card doubles it, and a shield is the
  easier of the two to draw by accident — `review && <Shield/>` is wrong in a way that looks
  right. The field's description says so, and mechanically nothing stops it.

**Neutral**

- **The `unavailable=` population is unchanged in size and shape.** It was already closed,
  counted and re-reviewed; what changes is that new members of it no longer carry a word that
  says they passed. Objects stamped before today keep theirs until the job reaches them, and
  `decision_on_record` is why that costs nothing but storage.
