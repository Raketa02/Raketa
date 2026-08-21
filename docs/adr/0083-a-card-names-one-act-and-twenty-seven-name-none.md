# ADR-0083 — A card names one act, from six, and twenty-seven cards name none

- **Status:** Accepted
- **Date:** 2026-08-22
- **Resolves:** [`Raketa02/Raketa#50`](https://github.com/Raketa02/Raketa/issues/50)
- **Completes:** [ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md), which gave `cta` its first two writers and left the other thirty-one open
- **Ratifies and narrows:** `UI` §G Open Decision 8 — one of its four groups accepted, one refused, two already settled
- **Departs from:** `UI` §B6.3's action row, whose primary button this removes from twenty-seven of thirty-six cards

## Context

[ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md) put the result
conversation on a route and made `needsResult` and `confirmResult` the first situations ever to set
`cta`. Before that, nobody had written the field and the `Open match` fallback answered all
thirty-three uniformly, so no situation carried a question. Afterwards **every remaining situation
carried one**: does this one name its own act, or fall back? `UI` §B6.3's `[GAP]` — *"`cta` and
`left` are read by `stateCard` but no state in the table ever sets them"* — was half discharged and
half inverted.

`UI` §G **Open Decision 8** had a recommendation waiting: four groups, `ready` → *"Getting in"*,
`needsResult` → *"Enter the score"*, `confirmResult` → *"Confirm 6-4, 3-6, 6-2"*, `cancelled*` →
*"See alternatives"*, everything else keeping the fallback.
[#24](https://github.com/Raketa02/Raketa/issues/24) took the two result groups, refused the score in
a button label, and declined the other two **for want of evidence**.
[ADR-0072](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md) then took the
enumeration to thirty-six, and the three new members all arrived with the question open — including
`seatOffered` and `seatOpened`, the two strongest candidates on the screen, which §G never
considered because the offers region did not exist when it was written.

Walking the thirty-four found the same thing §G could not have seen: **the fallback's destination
does not exist.** `UI` §D9 sends every card's press to the match screen; this map ruled the
match-detail screen out of scope, and [ADR-0074](0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md)
refused a general `GET /matches/{id}` specifically so a later effort could draw that screen
properly. So `Open match` in v1 is a button naming an act that goes nowhere, and the ticket's
question loses its second half: not *does this situation name its own act, or fall back*, but **does
this situation name an act at all**.

Three further findings shaped the answer.

- **The act is not a function of the situation.** `tag`, `tone` and `alert` are, which is why
  ADR-0072 could put all three in the client's thirty-six-row table and cross no wire. The act is
  not: one `forming` match offers *join* to somebody looking in and nothing at all to somebody
  already in it, and [ADR-0081](0081-a-seat-is-never-taken-until-it-is-paid.md)'s live seat claim
  changes it a third time for a third viewer of the same card.
- **`ready`'s act already has a button.** `⌘` on the same action row opens the Getting-in sheet —
  door code and QR, cached offline (`UI` §B16). §G was proposing to promote an act that was already
  reachable one control to the right.
- **The act that removes you was drawn on the screen that is gone.** *Cancel my position ·
  45,00 zł back* and the waitlist toggle are both match-screen controls in the prototype
  (`[SRC: 2053, 2267]`), and [ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)
  grants the right they exercise: *"a marketplace player may withdraw freely before the lock"*.

## Decision

**We will let a card name at most one act, drawn from a closed set of six, composed by the server
and carried as a code in the spine — and we will let a card with no act carry no button.**

### The rule

> **A card names an act when the viewer can take it now and a v1 surface can receive it.**

Both halves are load-bearing. The first is why a member's `rescue` card is silent — she can do
nothing, and [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md) already
settled that argument for the clock: *"a seat being rescued is precisely when a player can do
nothing and precisely when they most need to see the deadline — the clock is the app's warning, not
its to-do list."* The second is why a private owner's card is silent — inviting somebody is a real
act with no screen in v1.

**There is no fallback.** `Open match` dies with its destination. A card with no act has **no
primary button**, and its body is **not a tap target** either — ADR-0060 fixed that the card and its
button resolve to the same place, and that survives here as *both resolve to nothing*.

### The six acts

| Code | Receiving surface | Who gets it |
|---|---|---|
| `takeSeat` | a seat claim (ADR-0081) | `seatOffered`, `seatOpened`, and every shelf card whose seat is takeable |
| `finishPaying` | the running claim's payment | any card, whenever the viewer holds a live claim on it |
| `enterResult` | the result route (ADR-0074) | `needsResult` |
| `answerResult` | the result route | `confirmResult` |
| `seeAlternatives` | Find, pre-filtered | `cancelledIncomplete`, `cancelledCheckpoint`, `cancelledClub`, `inventoryLost` — and the **leaver**, on any situation |
| `gettingIn` | the Getting-in sheet (`UI` §B16) | `ready` |

**The enumeration is closed**, as [ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md)
closed causes. A seventh act arrives **with the surface that receives it**, never ahead of it —
which is precisely how the removal act will come back. The point of this ticket was that a
per-situation judgement made thirty-six times is a table nobody can maintain; a closed set of six
against an open set of thirty-six is a rule that can be checked.

### The act rides in the spine, as a code alone

**In the spine, not the situation half.** The act is the composition's judgement about *this
viewer* — which is exactly what the spine already holds (the fit badge, the emphasis flag, the card
stamp, the seat claim). It also means a phone that cannot name a new situation can still take the
seat, where putting the act in the situation half would silently disarm the offers region on an old
client.

**A code, and no `target` beside it.** `UI` §B6.3 sketches `cta?: { label, target }`; each of the
six codes determines its destination, and the card already identifies the thing it is about. A
`target` beside a code that determines it is a second answer to one question — the shape this map
has refused for *where* and for *which situation*. ADR-0070 already decided this exact case for the
tail card: *"the client appends the card and routes on the shelf code and the sport it already
holds… it decides where a tap goes, which it already does for every button."* The day an act needs a
parameter, it arrives as an added field with a reader ([ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md)).

**The label stays the client's.** [ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
is unchanged: the wire carries the code, the client's table maps code → sentence. That table is
**six rows, not thirty-six**, and it is total — which is the tell that the act belongs where it has
been put.

**A live claim wins.** `finishPaying` overrides whatever the situation named, the same override
ADR-0081 already applies to the card's one clock slot. Five minutes is the only thing on that card
that matters, and a card counting *1:30 to pay* under a button offering anything else is two
instructions.

### What §G proposed, settled

- **`ready` → Getting in: accepted**, and the primary button opens the sheet. `⌘` is **dropped for
  that one situation**, the same structural move the action row already makes when `post` is set.
  Two controls doing one thing on one card is worse than either alone, and `ready` is the moment
  the door code is the only thing anybody wants.
- **`cancelled*` → See alternatives: accepted, all four.** The evidence #24 lacked has arrived:
  ADR-0073 gives a terminal card a **bounded twenty-four hours** on screen with an **empty clock**,
  so it is the one card where the player certainly wants something and Now would otherwise offer
  nothing. It is also the only group in the walk where the act is *to leave this match behind*.
- **The score in a button label: refused**, as #24 refused it, and for the reason ADR-0060 gives —
  a score with its sides cut off is exactly what that ADR stopped shipping.

### The removal act is not a `cta`

Leaving a match, leaving the standby list and cancelling a private court are real acts a player is
entitled to, and **none of them may take the primary slot**. *Cancel my position* as the loudest
thing on every match a player is looking forward to inverts a screen whose job is reassurance.

Where the removal act **does** live is a surface question, filed as
[The act that removes you](https://github.com/Raketa02/Raketa/issues/59) rather than answered here,
because it needs the money line the prototype's `leaveOutcome` prints — *free to leave until Thu
18:00 · 45,00 zł back* — and a card demonstrably cannot give it that room.

**This is the sharpest cost in the ADR and it is not hidden:** until that ticket lands, **nothing a
player does can trigger the cascade**, so `replacement`, `replacementTransfer`, `rescue`,
`rescueLate`, `cancelledCheckpoint` and the entire leaver audience are reachable only from seeded
data.

### Departing from a UI authority, and how that is to be read

`UI` §B6 draws a primary button on every state card. This ADR removes it from twenty-seven of
thirty-six, and drops `⌘` from `ready` as well.

**This is a forced consequence of an out-of-scope ruling, not an override of a UI authority.** The
two UI documents describe a prototype in which the match screen exists; they are final on what a
card looks like and silent on what a control does when its destination is not built. The button is
not overruled — **its target is gone**.

Recording it the other way, as a genuine override, would make every later scope ruling look like a
licence to redraw the UI, which is the one thing this map's resolution rule exists to prevent.

### The twenty-seven that name nothing

`forming`, `formingHeld`, `formingLate`, `formingLateHeld`, `formingBack`, `heldSoft`,
`heldReleased`, `heldStale`, `heldExtended`, `clubHeld`, `protectedBack`, `full`, `confirmed`,
`confirmedOnFill`, `replacement`, `replacementTransfer`, `rescue`, `rescueLate`, `waitlisted`,
`completed`, `playedShort`, `playedNoShow`, `playedNoScore`, `privateReserved`, `privatePartial`,
`privateFull`, `privateOpen`.

Nine name an act: `seatOffered`, `seatOpened`, `needsResult`, `confirmResult`, `ready` and the four
cancellations. Twenty-seven do not. (`protectedCourt` and `protectedLate` are absent from both
counts — ADR-0031–0033 removed them, and `deltas/state-vocabulary.md` records it.)

Of the six `post` situations, two name an act and four do not; those four keep only `✉`, since
`⌘` is already dropped when `post` is set.

The four private ones are the **second named casualty of the invite flow being out of scope**, after
the two owner messages with nowhere to arrive. They can only arrive from seeded data in v1 anyway,
since there is no private-booking flow.

## Consequences

**Easier**

- One rule replaces thirty-six judgements, and it is checkable: a closed set of six acts, each with
  a named surface, against an open set of situations.
- The act cannot disagree with itself across audiences, because one place composes it. The leaver
  is the first real test and it passes without a second mechanism: one situation, two audiences,
  two acts.
- The offers region and the shelves become actionable from Now, which is what a shelf was for —
  [ADR-0050](0050-now-below-the-strip-is-shelves.md) puts a card on a shelf
  precisely because it is *a thing they could join*.
- Adding a situation no longer asks a button question. Adding an **act** does, and that question
  arrives attached to a screen somebody is building.

**Harder**

- **Now ships with twenty-seven cards a player cannot press.** On a member's own forming or
  confirmed match the action row holds `✉` and `⌘` and nothing else. This is the honest shape of a
  v1 without a match screen, and it should not be patched with a button that opens something
  irrelevant.
- **Nothing player-driven triggers the cascade until [#59](https://github.com/Raketa02/Raketa/issues/59)
  lands.** Half of this map's most carefully modelled machinery is demo-only until then.
- **The spine grows a third screen-fact slot**, after the debt line and the seat claim. ADR-0070's
  warning stands: the slot is not an invitation, and the next thing proposed for it must make its
  own argument.
- **`UI` §B6.3's `cta?: { label, target }` is now wrong in both halves** — no label crosses, and no
  target. Anyone reading the UI spec for the wire shape will find a sketch this ADR replaced.
- **A shelf card's `⌘` is now visibly wrong.** The Getting-in sheet on a match you have not joined
  is a prototype artifact nobody has ruled on; it was found here and is left where it was found,
  because it is a card-anatomy question and this ADR only fills a slot.
- **`ready` losing `⌘` is a second structural variant of the action row**, where `UI` §B6.3 records
  exactly one. A client that treats the variant as a boolean on `post` needs a second condition.
