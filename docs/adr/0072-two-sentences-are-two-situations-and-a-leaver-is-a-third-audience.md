# ADR-0072 — Two sentences are two situations, and a leaver is a third audience

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) split a card into a **spine**
every phone can draw and a **situation half** only a current one can, and handed
[`Raketa02/Raketa#42`](https://github.com/Raketa02/Raketa/issues/42) one job: *fill the situation
half for 33 situations, never touch the spine, and stop.*

Walking the 33 field by field found four places where the **enumeration itself** is wrong — not
the facts hanging off it. Each is the same mistake in a different costume: a single name covering
two different sentences, or a name covering none.

- **The offers region has no situation at all.** ADR-0070 gave an offered seat its own region
  above everything else; [ADR-0052](0052-a-vacancy-is-offered-not-announced.md) and
  [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md) give it two wordings —
  *a seat is being offered to you* above 24 h, where the seat genuinely is held for one player,
  and *a seat just opened — first to take it* inside 24 h, where it is a race. **Neither is one
  of the 33.** All 33 describe what a **match** is doing; the match under an offer is in
  `replacement` or `rescue`, which is a fact about the person who left and not about the person
  being offered the seat.
- **`formingLate` is two sentences under one name.** Its two `ctx` variants key on
  `m.created >= d.commit`, and its court line reads either `Protected · {cat}` or *"Not
  protected — no court is held yet"* — opposite answers to *is there a court*, three hours before
  a match, which is the only question that matters at that point.
- **`privateFull` cannot happen.** Rung 7 has three outcomes and four keys; the state-table
  research produced it **zero** times across 280 224 records
  ([`research/state-table.md`](../specs/now/research/state-table.md) §3), and `SPEC` §E2 flags it
  while `UI` §B6.3, `DOM` §E.2 and `3.1` list it without comment.
- **The alert strip gets quieter as the deadline approaches.** Only `replacement` and `rescue`
  set `alert` (`UI` §B6.4, verified in the prototype). `rescueLate` — the same situation, two
  hours out instead of four — does not.

Underneath all four sits a question ADR-0070 did not have to answer and this walk cannot avoid:
**how many audiences does one card have?** ADR-0070's handoff assumed two, through the non-member
money rewrite — a player in the match, and a player looking in.
[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) already established a third and did not
name it as one: *"the leaver's card is the match's card rendered for somebody who used to hold a
seat."*

## Decision

**We will let two sentences mean two situations, and the enumeration reaches 36.**

### The rule

**A situation is a sentence.** Where one name would make the client choose between two sentences
from a fact on the wire, it is two names instead.

This is not a stylistic preference; it is the only reading under which
[ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md) and
[ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) both survive. A boolean whose
sole job is to pick which sentence the phone writes **is** a rule on the phone, wearing a
different hat. And it degrades in the wrong direction: under ADR-0070's unknown-situation rule an
old phone meeting an unknown name loses one sentence, where a phone mis-reading one boolean
prints a **confident wrong fact** — *a court is held* when none is.

### The three additions

| Added | Replaces | Why it is its own sentence |
|---|---|---|
| `seatOffered` | — | *A seat is being offered to you.* Exclusive: nobody else can take it, for one hour. |
| `seatOpened` | — | *A seat just opened — first to take it.* No reservation; a race in waves. |
| `formingLateHeld` | half of `formingLate` | A court **is** held on a match created after the commit deadline. |

`formingLate` keeps its name and its other half: past the commit deadline, no court held.

`seatOffered` and `seatOpened` are the situations the **offers region** draws. They are ordinary
members of the enumeration, carried on ordinary match cards with the ordinary spine — an offer has
a price, a moment, a club and a fit score, all of which the spine already holds. **They were not
made a fourth card type**: ADR-0070's three types exist because a person and a club have no
situation, no clock, no price and no emphasis, and an offer has all four.

**The alternative refused for the offers, and the reason it matters:** rendering the match's own
situation (`replacement`, `rescue`) for an *offered* audience. It would have kept the count at 33
and put two competing sentences on the phone — *the seat stays funded* and *a seat is being
offered to you* — with a rule for choosing. That rule is the thing this ADR exists to refuse.

### `privateFull` keeps its place and gains a rung

It is not a spare key; it is the sentence that fires the moment a private owner **stops carrying
the court**. [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md) fixes
that an owner's card prints what she has recovered **and** the whole court she still guarantees
until the sold format is met. When the last share is paid that guarantee is discharged — and under
today's ladder that moment resolves to `privatePartial`, whose card would go on saying *you cover
120 zł unless it fills* about a court that has just filled.

So the fix is the ladder, not the enumeration. **Leaving it unreachable was refused outright**: a
name nothing produces is a name somebody eventually builds against, and no test can fail.

### The alert is a row in the client's table, not a field on the wire

**Anything still short a player inside the rescue window carries the alert, and it stops only when
a seat is actually being taken** — so `replacement`, `rescue` and `rescueLate` alert, and
`replacementTransfer` does not, because a transfer in progress is good news.

Stated that way the alert is a **total function of the situation**: nothing else feeds it, not the
clock, not the viewer, not the money. So it belongs where `tone` and the tag already went under
ADR-0041 — the client's own 36-row table — and **crosses no wire**.

- A flag would ship a lookup on every card of every screen that the phone can already do.
- Worse, it would let the server and the phone disagree about whether a card is urgent, which is
  precisely the two-derivations failure [ADR-0040](0040-one-ladder-resolves-a-situation.md) exists
  to make unreachable.
- If the rule ever stops being a function of the name alone, that is the moment to put it on the
  wire, and it will be obvious.

**The screen now has two kinds of loud, deliberately.** ADR-0051's single emphatic card is a
*suggestion* shouting **take this seat**; an alert is the player's **own match** shouting *you are
about to lose your game*. They are different claims about different things, and ADR-0052 already
silences emphasis whenever an offer is on screen — the screen's loudness is budgeted, just not by
silencing this.

### Three audiences, and a leaver's departure is its own payload

**A card is rendered for one of three audiences: a player in the match, a player looking in, and a
player who used to hold a seat.** The first two were already implicit in the non-member money
rewrite; the third is ADR-0030's leaver, named.

**The leaver's departure rides beside the situation as its own payload, in two forms** — *paid,
recoverable if the seat refills* and *nothing was taken* — rather than as one payload holding an
amount that is sometimes absent. ADR-0030 fixes that before commitment the seat is cleared **and**
unpaid, *"so there is nothing left to derive from and the card can name no amount at all"*; an
optional amount would be a field whose absence the phone has to interpret, and the phone
interprets nothing.

**The leaver keeps the match's own facts.** Whether she gets her money back depends **entirely** on
her seat being refilled, so a card that hid the match's progress would hide the only thing that
determines her outcome.

**A cause is the same cause for all three audiences.** A cause names the rule that fired, never
who was watching ([ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md)).

## Consequences

**Easier**

- The offers region draws with the same machinery as everything else, and the exclusive claim is
  made **only** where the seat is exclusive — which was ADR-0052's whole discipline and now has a
  structure enforcing it rather than a convention.
- Three of the four defects the walk found are now unreachable rather than documented: a name
  cannot cover two sentences, a name cannot cover none, and the alert cannot disagree with itself.
- A player short a seat is told so more loudly as it gets worse rather than less.
- The leaver stops being a special case applied by hand at render time and becomes a named
  audience with a payload of its own.

**Harder**

- **The enumeration is 36, and every client owes 36 rows** — copy, tag, tone and now the alert —
  in an exhaustive switch. ADR-0041's accepted duplication grows by three, and
  [#44](https://github.com/Raketa02/Raketa/issues/44) inherits the larger corpus.
- **`privateFull` needs a rung that does not exist**, which is a change to the resolver rather
  than to a table. It is the only place this walk reaches into the ladder, and it is `backend/`
  work not performed here.
- **`formingLate` splitting means the state-table research's 35-context table is now wrong in a
  second place**, after ADR-0031–0033 removed two. Anything reading that table for a count needs
  the deltas beside it.
- **Two kinds of loud on one screen** is a real risk and this ADR takes it deliberately. If alerts
  become common the emphatic card stops reading as special, and the evidence for that will arrive
  as real matches rather than as an argument.

**Neutral**

- The count is 36 only until the next situation; ADR-0070 already made additions cheap, and this
  ADR is the first exercise of that. An old phone meeting `seatOffered` draws the price, the time,
  the club and the countdown, and loses one sentence.
- Nothing here is built. No resolver, schema or generated union carries these names.
