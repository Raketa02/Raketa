# ADR-0073 — A card counts money, and counts down to what happens anyway

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) drew the envelope and left the
**situation half** to [`Raketa02/Raketa#42`](https://github.com/Raketa02/Raketa/issues/42);
[ADR-0072](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md) fixed the
enumeration the half hangs off. This ADR is what the half **carries**, walked across all 36.

Four constraints arrived settled and are honoured rather than re-decided: the moment a card is
about is an **absolute instant** and the phone only subtracts
([ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md)); the **fit sub-object** lives in
the spine ([ADR-0037](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)); a **score crosses
per side, never as a display string**
([ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md)); and a club's
**distance is optional**, printed as `~{n} km` or not at all
([ADR-0064](0064-a-radius-orders-now-and-bounds-only-a-search.md)).

The walk turned up five things the specification set had never had to answer, because no card had
ever been drawn from real facts.

- **A card's lifetime is defined off the wrong moment.** `keepUntil` is `matchEnd + 24 h`
  ([ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)), which is
  exactly right for a match that was played and absurd for one **cancelled** in advance: a match
  killed on Thursday for a Saturday game sits on the player's home screen until Sunday.
- **`completed` was to print a level movement and nothing produces one.** `backend/app/engines/`
  holds assessment, fit, forecast, matchfit, matchmaking, pairing and racketskill, and **no engine
  updates a rating from a result**; a rating today only knows how to be initialised from
  onboarding. The Player Score line is withdrawn and the card has a hole where it was.
- **`{f} of {n}` counts four different things** across the 36 — seats **paid**, seats **held** by a
  name with no money behind them, players who **turned up**, and **shares** paid on a private
  court — with one card counting two at once (*"{f} of {n} paid · 1 seat held"*).
- **The court's category is on six cards and none of the shelves.** Indoor-or-outdoor is stated on
  six situations and absent from every card on which a player is actually **choosing**.
- **`hold.note` is a sentence written by the server**, printed verbatim on `heldSoft` — the one
  place in the whole contract where the server would hold Polish, against ADR-0041's rule.

## Decision

**We will make every card count in money, count down to the next thing that happens without the
player, and say where the money went.**

### One clock rule, not thirty-six judgements

ADR-0070 gives a card **exactly one clock slot**. Which moment fills it is decided by a rule, not
per situation:

> **The clock is the next moment at which something happens to the viewer whether they act or
> not.**

A forming match counts to the court locking in; a full one to settlement; a match about to start to
the start; a match wanting a score to the 24 hours; an offer to its expiry. **A card that is over
or cancelled counts to nothing and the slot is empty.**

- **Always the start time** was refused: on a match three weeks out it ticks down five hundred
  hours to a game nobody is worried about, while the thing that actually expires — the hold, the
  offer, the result window — passes in silence.
- **The next moment the player can still change the outcome** was refused for the opposite reason:
  it blanks the card at the worst moments. A seat being rescued is precisely when a player can do
  nothing and precisely when they most need to see the deadline. **The clock is the app's warning,
  not its to-do list.**

The moment may **also** appear as an ordinary fact where a card prints it as words (`full`'s
*"settles to the club at 18:00"*) — ADR-0070 already permits this, and printing a moment and
counting to it are different jobs.

### A card lives 24 hours from the moment it closed

Not from when the match would have ended. Cancelled Thursday 09:00, gone Friday 09:00; played
Tuesday 20:30, gone Wednesday 20:30.

This **narrows `keepUntil`** from ADR-0048's `matchEnd + 24 h`, which stays correct for every
played ending because for those two moments coincide. It gives all ten post-match situations one
rule instead of one clock for played matches and another for cancelled ones, and it removes the
outcome nobody would defend: the further ahead a match was booked, the longer its corpse stays on
screen.

**The rule it replaces was sharper and still wrong.** *A card stays until it has nothing left to
ask* is right about the two situations that want a score and wrong about everything else, because
a card can have nothing to **ask** and something to **tell** — and telling has its own clock.
ADR-0030's leaver card already assumed a 24-hour tail on a card that asks nothing; this makes that
general.

### Counting is by money

**Every card counts seats that are paid**, and where a hold exists it is **its own number** beside
that count, never folded into it.

A seat is real when it is paid for; a held seat is a name with no money and can lapse. Counting
people would tell a player a match is full when a hold is about to expire and the seat was theirs;
suppressing holds entirely produces the same lie in reverse — *3 of 4*, and a seat somebody has
been sitting on unpaid for a day.

**Every number the sentence prints is sent as that number.** The seven sentences reading *one less
than the seats* send **three and four**, never *four, now take one off*. It is only ever minus one
until a doubles match loses two people, at which point the phone would confidently print *3 of 4*
and the player would believe three people played.

The cost, stated: *3 of 4* no longer means one thing across the screen, so the copy must say what
it counts — **seats paid**, **shares paid**, **played** — on every card.

### What a card says about money

**Four rules, and between them they cover every money line on the screen.**

- **A cancellation names the amount and where it went, and the destination fixes the tense.**
  *"30 zł on its way back to your card"* against *"30 zł credit at Sport Club Kraków"*. A card
  refund is **never** claimed to have landed: a card lives 24 hours and a refund rarely arrives
  inside one, so the *it has landed* branch would be built, shipped on every cancellation card, and
  never rendered. The club credit is definite because it genuinely is instant —
  [ADR-0058](0058-one-balance-and-it-never-goes-above-zero.md) makes it a club card entry, not a
  payment.
- **A private owner's card carries two figures that disagree on purpose:** what she has
  **recovered**, and the **whole court** she still guarantees until the sold format is met. Today's
  copy — *"every public share reduces what you guarantee"* — **is false**:
  [ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md) refunds every marketplace payer in
  full when the format is unmet and leaves the owner carrying the court, so her exposure does not
  move at all until it fills. The gap between the two figures **is** the product fact, and it is
  the most surprising thing in the private-court model: she watches money come back while owing
  exactly what she owed at the start. Showing the guarantee alone looks broken — 30 zł just landed
  and the card acts as though nothing happened.
- **`{price} settled to the club` is the court's total, for every audience.** The subject of that
  sentence is the **court**, and what it tells the viewer is *this game is happening*. The viewer's
  own share answers a question they did not ask and answers it worse — their money left days ago,
  so *your 30 zł has gone* is stale news dressed as an update. This is the one money line on the
  screen that needs **no audience at all**.
- **Otherwise money on a card is written for whoever is looking** — the viewer's own share inside
  the match, what they *would* pay when browsing. The server sends the number that applies to this
  viewer; the client holds one sentence per audience where they differ, and the phone never derives
  which it is. Shipping both numbers with a flag was refused: it ships a number that does not apply
  on every card forever and invites the bug where the wrong one prints.

### A finished card prints the score

`completed` prints **no level movement in v1**, and the engine that would produce one is
rating-context work ruled out of this map. In its place the card prints **the score** — both sides
named, the viewer's first — which is the thing that actually happened and the only thing available.

**The card that awaits an answer prints it too.** Otherwise it asks the player to agree and gives
them nothing to agree with, so every player taps through to read three numbers. The four remaining
post-match situations carry no score, because none exists.

A bare *6-4, 3-6, 6-2* was refused. It feels safe — a player does remember Tuesday — but with four
cards from four evenings on one screen it prints a number that is true of **somebody**, which is
the same class of defect as deriving *n − 1*. The cost is that a card now carries a **person**,
which is the first time one does.

### The court's category becomes part of *where*

Indoor-or-outdoor rides the **spine**, on every card, alongside the club, its timezone and its
optional distance. ADR-0070 fixed the spine as a list of **concepts** — *which thing, the moment,
where, how much, the badge, the emphasis flag, the stamp* — and never enumerated what *where*
contains; this reads the category as part of it.

It behaves like place, not like state, and leaving it on six situations fails the player at the
exact moment they are choosing: in November in Kraków it is the most important fact about a padel
court, and it is absent from every shelf. **The specific court name stays with `ready`**, where it
is drawn fifteen minutes before the start — it is usually unassigned until then, and a spine field
that is empty almost always is one somebody eventually fills with something else.

**This is the one place #42 reaches into the spine**, and it is an interpretation of *where* rather
than a new concept.

### `hold.note` becomes a reason and its facts

The five reasons a court is held — **committed by the club**, **far off and part-paid**, **close
and nearly full**, **the hold has gone stale**, **extended beyond what the ladder guarantees** —
cross as a named reason plus the numbers it needs. The client writes all five sentences.

Dropping the reason entirely was the serious alternative and is the better of the two losing
options: *why* a court is held is the difference between relaxing and chasing friends for the last
seat, and it is the only line on that card doing work. **Free text was refused**, and would have
been the single precedent for a server-held sentence anywhere in the contract.

### The cause enumeration is complete

[ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md) left the list knowingly short and
named this walk as the place to finish it. The five: **`inventoryLost`**, **`clubCancelled`**,
**`formCancelled`**, **`checkpointCancelled`**, **`settlementReopened`**.

**Four names, three identical money rules.** The three refunds return money to the method it came
from; the checkpoint ending issues club credit (ADR-0058). Four names because they are four
different sentences to the player, not four different arithmetics — and *refunded* alone answers
nothing a year later, which is the whole reason causes exist.

**`settlementReopened` never appears on a card**, because by the time a settled departure is
reopened no card exists. It is a ledger cause only.

**What a club owes when it sells our court out from under a forming match is ruled out of scope** —
a contract question between Raketa and the club, with its own legal shape, on a surface this effort
already excludes.

## Consequences

**Easier**

- The clock, the lifetime and the counting are each **one rule** rather than a table of 36
  judgements nobody can maintain — which was the explicit failure mode
  [#50](https://github.com/Raketa02/Raketa/issues/50) names for `cta`.
- A player choosing on a shelf can finally see whether a court is indoors.
- *"Settled to the club"* needs no audience, which removes one of the two per-viewer rewrites the
  resolver was carrying.
- [#44](https://github.com/Raketa02/Raketa/issues/44) inherits a specified corpus: five hold
  sentences, two money tenses, a per-card counting noun, and a scoreline naming two sides.

**Harder**

- **A card carries a person's name**, on two situations. Nothing else on Now names anybody, and
  the shape has to exist for two cards.
- **A private owner's card carries two money figures on two short lines.** If that proves
  unrenderable it is a copy and layout problem, not a contract one — the facts have to be there
  either way.
- **`keepUntil` is narrowed**, so anything already written against `matchEnd + 24 h` is wrong for
  cancellations, and ADR-0048 must be read with this beside it.
- **The category on the spine is paid on every card of every screen**, including the shelves where
  it is most useful and the strip where the player already knows.
- **Every counting sentence must name its noun**, which is 36 rows of copy that cannot be
  templated from one string.

**Neutral**

- **Naming a friend already in a match is deliberately excluded, not overlooked.** *Kuba is in this
  one* would beat every other fact on the card and the played-with graph exists
  ([ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md)), but it redraws a card whose
  anatomy belongs to two UI documents this effort treats as final. Recorded so a later session
  finds an idea rather than an oversight.
- **Person and club cards are untouched.** They have no situation half (ADR-0070), so they are
  outside this walk entirely; ADR-0051 fixes the inert face on the new-players shelf.
- Nothing here is built. No route, schema or generated type carries any of it.
