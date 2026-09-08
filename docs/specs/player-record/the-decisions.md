# The player record — the decisions

**Forty-two questions put to the product owner between 2026-09-07 and 2026-09-08, and the
answers.** This file is the input to everything else in this set: the ADRs record *why*,
[`the-player-record.md`](the-player-record.md) records *what to build*, and both read from
here. Where this file and that one disagree, **this one is newer** — §2.3 and §2.4 of the
implementation document argue against two rows that have since been reinstated by decision,
and §2.6, §5 and §10 are stale until rewritten.

- **Status:** settled. Nothing here is built.
- **Method:** the frontier was walked in five rounds; a round was asked only once its
  prerequisites were answered. The frontier is empty.

---

## 0. What ships, in one place

A tap on a face inside the balance-forecast card opens **the player record** — a description
of a *person*. It carries, in order:

1. **The header** — poster, level, sport, the on-court shield, the whole handle, `In your
   area · 1,2 km`, one pill per rated sport, and the reliability pill.
2. **The skill card** — level, confidence, counted games, the band bar, the likely-range
   bracket, and a per-sport *Last 5*.
3. **The record**, headed *counted by the system, not written by people* — three metered
   rows (*shows up*, *answers challenges*, *answers about results*) and *opponent variety*.
4. **What opponents said** — its own block, its own heading, a sportsmanship average out
   of 5 over the players who rated them.
5. **Social tags**, tinted where they are shared.

And one row that opens the existing Fit breakdown, present only where a pairing is behind
the entry point.

---

## 1. The sheet, and the gesture that opens it

**A face opens the person, and the pairing gets a row.** Tapping a photograph and receiving a
weights-and-contributions table was always slightly wrong; tapping it and getting *them* is
right. The Fit breakdown is not deleted — the number in the `FitPill` has no other explanation
anywhere in the app, and deleting its only account leaves a figure on screen that nothing
answers for. It moves behind a row that says what it is.

**The row exists only where a pairing does.** Opened from the forecast card there is a Fit and
a row; opened later from Now, chat or the games list there is neither. This is the same
discipline the social-tag overlap already takes, applied to the other pairwise fact on the
sheet: *a pairing fact appears only when a pairing is in hand.*

**The forecast card's four faces, and nothing else this time.** The deck and pool cards keep
their own *Why 78?* button and are untouched. Every photograph in the app opening a record is
the right end state and it is three screens, not one — and the deck card already carries a
prominent control, so a second door on it needs a design pass of its own.

**Your own face becomes a control**, for the first time on this platform. The sheet's title
changes to *How others see you*, the distance is omitted, and you see what everybody else
sees. The argument is not symmetry, it is legibility: the reliability number has been deciding
who you are shown to since you signed up, and a penalty nobody can look up is a penalty nobody
can fix. The cost is admitted — a player sitting at 55 finds out they are at 55, and some of
them leave.

**A tall bottom sheet with an internal scroll and a pinned header.** Not a full screen:
leaving the four you are building is a heavier action than tapping a face should feel like.
The header stays put so the name and the number remain visible while the reader works down.

---

## 2. Who may read a record

> **The record is read *through* a prior disclosure, never *about* a person.**

Admitted when **any** of these holds, and never otherwise:

1. `reader == subject` — the only case needing no prior disclosure.
2. The subject was returned by a search of the reader's. **No expiry.** A search record is
   kept for ever, so an expiry shorter than that can only misfire: it would refuse a face the
   app is *currently showing*.
3. The pair share an open challenge or a game.

**The four fail-closed gates are re-run live on every open** — a block in either direction, an
account hold, an account state that may not be shown, and the mutual gender preference. They
are evaluated **in the partition of the disclosure, never of the reader's arrival sport**: the
search that returned them has a sport, the challenge has a sport, and the self case has no
gates. The `?sport=` parameter only ever selects which sport the sheet is *about*; it never
decides who may be seen. Without this rule a subject rated in squash but opened from a padel
context has no index row, the gender gate cannot be evaluated, *a gate that cannot be
evaluated excludes*, and the route refuses somebody the reader demonstrably just saw.

**One refusal, and it names nothing.** *Never disclosed to you*, *blocked*, *held* and *no
such player* return the same thing, byte-identical. On screen it is one line — **"This record
isn't available."** The indistinguishability is the feature: a payload naming the gate
discloses a block to the one person the block was meant to be invisible to.

**The face stays tappable.** Making it non-tappable requires asking the server about every
face before anybody taps — four extra requests on every four built, for a sheet most people
never open — and a face that silently is not a button is its own small lie.

---

## 3. The header and the skill card

**Sport pills and the most-played fallback are built now**, not deferred to the second entry
point. The pills answer *what else do they play*, which is useful to a reader inside a padel
four today; the fallback rule is small and means the next door is a screen with no backend
change behind it. Ties in the fallback are broken by the sport registry's own order, never by
dictionary order.

**Last 5 becomes per sport.** Today's run is built across every sport and drawn beside a
single sport's Level, which is a defect the new design makes visible by putting the run
*inside* the per-sport skill card. The read gains a sport; the record sheet passes one. **The
search result cards are not changed here** — those rows are frozen at search time and kept for
ever, so changing what their squares mean makes the same person's card read differently before
and after. That is a change worth making deliberately, in its own ticket, not as a side effect
of this one.

**`In your area · 1,2 km`, and no neighbourhood name.** Nothing in this repository can turn a
coordinate into the word *Kazimierz*, and deriving one would be inventing a naming scheme
nobody has calibrated and printing it as fact beside a real person's face. What is licensed
is a comparison between two coarse codes, which the client already makes. The gazetteer is a
small well-bounded slice of its own that lights up every card in the app; it is **priced
separately**.

**No activity recency, at any granularity** — not a timestamp, not *active today*, not a green
dot, not *active this week*. This product has no presence indicator and that is a standing
refusal, not a gap. It is dropped from the design entirely.

**No languages.** There is no vocabulary, no onboarding step and no field. Languages could
legitimately be *shown* — the standing refusal is about *scoring* them — but the field must
exist first, and building it is a signup step plus a backfill for every existing player. Out
of this scope.

**Opponent variety returns**, as this route's own demand, over the **whole record** rather
than a window, printed as **`70% · 14 of 20`**. The raw pair is not decoration: this card
argues two rows above that a perfect record over 9 games and one over 40 are different claims
and a bar alone hides that, and a bare `70%` would break the rule the card had just made about
itself.

---

## 4. Answers about results

The design asked for *Confirms results*. Investigation found the row cannot mean what it says.

**Silence is a yes.** When one score stands unanswered for a day, it is confirmed. A player
who ignores a result entirely gets the same outcome as one who agrees. The only games that
end unconfirmed are the ones where **two people put different scores up and neither gave
way** — so a row reading *"results confirmed, of results awaiting them"* would measure exactly
one thing: how often you have disagreed with somebody, docking both sides of every honest
disagreement including whoever turned out to be right.

**So the row measures answering, not confirming.**

| | |
| --- | --- |
| **Denominator** | scores put in front of them |
| **Good** | they responded inside the window — **accepting counts, countering counts** |
| **Miss** | silence until the window closed |
| **Name on screen** | **Answers about results** |

The rename is load-bearing. Keeping the word *confirms* over a number that counts *answers*
means a player who counters a score they believe is wrong watches their *"Confirms results"*
go **up** — and they are exactly the person who will notice.

**It enters the reliability number and the matcher**, like the two rows beside it, with a
**minimum of 5** results put to that player before it counts — so somebody with two behind them
cannot be sunk by one bad week. Its share is **15**, the number it held before it was struck,
restored rather than retuned: nothing has been learned since that would justify moving it.
The weights are **35 / 20 / 15**.

**A twelve-month window**, matching the horizon the rest of the score already uses, so a bad
month does not follow somebody indefinitely.

**On the day this ships, everyone's number is re-mixed** and some players' matcher penalty
appears or lifts through nothing they did. That is a one-off and it is worth saying out loud
to players if there is a channel for it.

---

## 5. Sportsmanship

A whole new bounded context, and **the first thing in this piece of work that stores
anything** — every other part derives.

### The rating

**One to five whole stars.** No zero: a rating that reads as *worthless* is a weapon out of
proportion to a tap, and one star already dents an average about as hard. No half-stars — five
taps, one number.

**You rate everybody else on the court.** In doubles that is three people: both opponents
**and your partner**. In singles it is the one opponent.

**One card, three people, and each may be left blank.** Two cards per doubles game would turn
a busy month into a chore list; forcing an answer about all three is how you collect
default-five noise.

**It appears in the games list**, once the score has settled and **not until the day after the
game** — an answer given in the ten minutes after losing 6-2 6-1 is not the answer wanted. It
stays for **7 days**, then expires.

**One-time and final, per card.** Submitting closes it. **A blank stays blank for ever**, and
submitting with all three blank closes the card too — an explicit *I am not rating anyone* is
an answer, and leaving it to expire would park a dead card in the list for a week.

**Not rating costs nothing.** There is no strand for it, no obligation, and no penalty. Making
a voluntary opinion compulsory harvests exactly the low-quality answers this design is built
to avoid.

**A low rating feeds the average and nothing else.** It does not pass, hide or block. The card
says so in one line — *"This helps other players. It won't stop you being matched with Karol."*
Pass and Block already exist and both mean something specific; a control that silently does
two things is one nobody can reason about.

### What is published

**One rating per person, and the most recent counts.** Two friends who partner every week
would otherwise farm each other: ten games with the same partner and two opponents would give
twelve ratings, ten of them one person's opinion, and the average would drift toward what your
regular partner thinks — the opposite of what the row claims to measure. Collapsed, that same
history gives **three** ratings, and the count on the sheet then means *how many different
people have an opinion*, which is the number a reader actually wants.

**The window is fifty people, not fifty ratings** — each person's latest rating, taken over
the fifty most recent raters. Read the other way round, a weekly partner would eat twenty of
the fifty slots and hand the farming problem back through a side door after it had just been
closed at the front.

**Published from the very first rating.** No minimum. The count is always printed beside the
figure — `4,7 / 5 · 17 players` — and that is the card's own existing discipline doing its job:
`3,0 / 5 · 1 player` is visibly one person's opinion and reads as one.

**No outlier trimming.** Trimming is the platform deciding which opponents were wrong, which is
a larger claim than publishing the number.

**Individual ratings are never shown to anybody**, and the row is titled **"Sportsmanship, by
players"** — not *by opponents*, which stopped being true when partners started rating.

### What the subject sees

**A coarse band, and no count.** Not the number.

A published average plus a published count lets the subject subtract: an average moving from
4,80 over ten to 4,73 over eleven names the new rating as a 4, and the subject knows who they
played. Every answer would be individually identifiable by the one person who must never see
it, and the failure mode is somebody being confronted about it at the club. A three-step band
across the whole scale tells them *something is going wrong*, which is the useful half, and
never who to blame for it, which is the half that keeps people answering honestly.

This holds at a minimum of one. At one or two ratings the band is deliberately too coarse to
be informative about any individual.

### What it does not touch

**The matcher ignores it entirely — the floor and the term.** This is the one strand a person
can weaponise and there is no appeal route behind it. A reader seeing `3,1 / 5 · 12 players`
and deciding for themselves is the product working; the app halving somebody's exposure on the
same evidence, silently, with no way for them to answer it, is not.

**And therefore the reliability pill is the counted-only number.** This was put as an open
question and overtaken by the mechanism: a star average is not a ratio out of a hundred, so it
cannot be a strand in a weighted mean over ratios. The pill is *shows up · answers challenges ·
answers about results*, and it is exactly what the matcher acts on — which keeps intact the
stated reason the floor reads the published number at all: **a player who works their visible
score back up must be able to see the penalty lift.** Had the pill included opinions the
matcher ignores, the number the player can see would not be the number that demotes them, and
the penalty would become the unexplainable kind that rule exists to forbid.

**It is not on search result cards.** Those are built for twenty people at once and frozen for
ever, and this figure must be current. A search would also be showing a human opinion about
somebody to twenty strangers who never asked for it.

### The card splits

The record card is headed **"counted by the system, not written by people"** — the rule the
whole card exists to enforce, and the reason anybody trusts the rows beneath it. A number
opponents typed makes that title false.

So the card divides where the **authority** divides: the three metered rows and opponent
variety keep the title and the promise; sportsmanship gets its own block headed **"What
opponents said"**. Two headings, no lie, and a reader can see which is which.

---

## 6. Per-strand minimums

The bar a strand must clear is **one number for every strand today: three observations**.
Two of the decisions above need different bars, which that shape cannot express.

| | Minimum |
| --- | --- |
| Shows up | 3 — unchanged |
| Answers challenges | 3 — unchanged |
| Answers about results | **5** |
| Sportsmanship *(its own figure, not a strand)* | **1** |

Raising the single number to five instead would take a brand-new player who has played three
games and turned up to all three from a score of 100 to **no score at all** — which changes how
newcomers are treated across the whole app, and is a decision that deserves its own
conversation rather than arriving as a side effect of this one.

---

## 7. What this costs

Both rows reinstated by decision are larger than the rest of the sheet put together. Named
rather than discovered:

**A ruleset release, and it is a build gate.** Adding a strand to the matcher's reliability
term changes **two mode weight vectors**, and per-strand minimums change the ruleset's shape.
`make gen-ruleset-diff` and `make gen-judged-pairings` both go red until regenerated, and
**the ranking diff they print has to be argued in the pull request**. That is the repository
proving the change does what it is claimed to do, not overhead.

**A context that stores.** Sportsmanship is the first part of this work with an aggregate, a
table and a migration. Everything else derives.

**A frontend flow, not just a sheet.** The games-list rating card, three people on it, blanks,
submit, and the closed state.

**Three sessions.** The ownership hook blocks cross-app writes, so this splits into a root
session (ADRs, specs, glossary, ruleset regeneration), a `backend/` session and a
`frontend_player/` session. This is a worktree, so **the final merge is run by a human**.

---

## 8. What is deliberately not decided here

- **The neighbourhood gazetteer.** Priced separately; lights up every card in the app.
- **Languages.** A vocabulary, an onboarding step and a field, then the line draws itself.
- **The bracket-narrowing algorithm.** The bracket already draws whatever range the server
  sends, so nothing on this sheet waits on it.
- **The search cards' cross-sport *Last 5*.** Fixed machinery, deliberate change, own ticket.
- **Every photograph in the app opening a record.** The right end state, three screens, later.
