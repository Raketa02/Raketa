# ADR-0050 — Below the strip, Now is shelves, and every shelf makes one claim

- **Status:** Accepted
- **Date:** 2026-08-20

## Context

Below the enrolled strip, `1-now_screen_production_spec.md` gives Now a fixed vertical
section list: **Part 5** *Best fit for you* — three stacked cards, fit-descending, no minimum
score — and **Part 6** *Full, but worth waiting for* — exactly one card, fit ≥ 80, the section
absent when nothing qualifies. `4-match_recommendation_engine_architecture.md` §3.5 caps the
whole surface at **six cards**, because *"a recommendation surface that grows without bound
stops being a recommendation."*

That shape was designed against a screen with one job: *of everything open, here are the best
three*. Three facts have since made it the wrong shape.

- **The picker that fills it does not exist.** `matchmaking.py` is a snapshot vocabulary with
  no sort, no filter and no cut; [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md)
  assigns lanes, floors, diversity and the cut to a policy object *"in the calling module's
  application layer"* and no such module is written. Nothing is being rewritten here, because
  nothing was built.
- **A full match outranks the joinable version of itself** — the same four players score **91**
  with one seat open and **94** with none, because being full is the strongest available
  evidence the match will be played ([ADR-0037](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)).
  So the two sections can never be merged into one ordered list. The boundary between them is
  load-bearing, and a screen whose two halves are already governed by different rules is
  already most of the way to being a set of independently-ruled sections.
- **The empty state lies on a thin week.** With a floor on the open section, a player in a city
  holding two poor-but-real matches gets *"Nothing open in padel right now — we do not invent
  players."* Without a floor, they get a card whose badge prints 20 for a true score of 12,
  because the badge clamps at display time. Neither is acceptable, and inside a two-section
  vertical list there is no third option.

The alternatives considered:

- **Keep the vertical list and pick one horn of the empty-state dilemma.** Cheapest, and it
  spends either the honesty of the empty card or the honesty of the badge.
- **Keep the vertical list and add sections to it.** Every added section costs vertical scroll
  against a six-card ceiling that exists for a real reason, so the sections compete for the
  same scarce space and the screen gets longer without getting more useful.
- **Shelves — a vertical list of horizontal rows**, each row one titled, side-scrolling claim.

The kit already holds the component. `rakieta-now-section-ui-spec.md` §D5 defines `.sqrow` — a
horizontally-scrolling row whose children are `flex: 0 0 auto` — and `.mrail`, a `.sqrow` of
268px cards, marked *"not used by Now"*. `.sqrow` has a property Now's current strip lacks:
**its horizontal offset survives a re-render**, where `.hstrip`'s does not, so any re-render
today snaps the strip back to card 1 (§G, `[SRC: 4277, 4281]`). Shelves are built from parts
that exist and behave better than the part they sit beside.

## Decision

**We will replace Now's fixed two-section lower half with shelves: a vertical list of titled,
horizontally-scrolling rows, each of which makes exactly one claim.**

This supersedes Parts 5 and 6 of `1-now_screen_production_spec.md` as *sections*. It changes
nothing about the match card itself, the badge, the header, the sport bar or the enrolled
strip, all of which remain final in the two UI documents.

**The shelves, in fixed order.** Order is a list the server owns and can reorder without a
client release; it is identical for every player.

| # | Shelf | Contents | Floor | Cap |
|---|---|---|---|---|
| 1 | *Best fit for you* | open matches the viewer could join | **70** | 10 |
| 2 | *Full, but worth waiting for* | full future matches, standby | **80** | **3** |
| 3 | *Recently viewed* | matches tapped in the last **48 h**, still joinable | none | 10 |
| 4 | *New on Raketa* | players who joined in the last **30 days** | — | **20** |
| 5 | *New clubs* | clubs that joined in the last **60 days** | — | 10 |

- **Five shelves is a ceiling**, and every shelf ends in a tail card opening Find, pre-filtered
  to that shelf's question. §3.5's six-card cap is superseded by a **shelf** cap for the same
  reason it was written: Now is where a player decides and Find is where they browse, and a Now
  that can be browsed has eaten Find. The ceiling now bounds the number of *questions* asked
  rather than the number of *cards*, which is the quantity that was actually scarce.
- **A shelf that has nothing to show is absent.** No header, no empty card — Part 6's existing
  rule, generalised: *"a section that appears every time saying 'no full matches worth waiting
  for' is a section players learn to scroll past."* This is what dissolves the empty-state
  dilemma: on a thin week the best-fit shelf is simply not there and the others carry the
  screen, so the 70 floor costs nothing and no empty card claims the city is empty.
- **Best fit never goes silent.** When nothing clears 70 it does not disappear; its **title
  changes to *Same level*** and it shows the matches closest to the viewer's own level, with no
  floor. One place on the screen always answers *what should I play*.
- **The 80 floor and the 3 cap on the waitlist shelf are kept deliberately**, though the
  geometry that forced *one* card is gone. Asking somebody to **wait** is a bigger ask than
  asking them to **join**; a shelf of ten things to wait for makes waiting feel cheap, and every
  entry costs the match a standby player who may not answer when called.
- **A match may appear on more than one shelf.** Each shelf answers a different question, and a
  shelf that hides its own best answer to avoid a repeat stops answering its question. The one
  guard: **a shelf is dropped entirely when it would be nothing but repeats of a shelf above
  it**, which is what keeps a six-match city from rendering the same six matches five times.
  This reverses `4` §3.5's *"dedupe across lanes, first lane wins"*, which was correct for lanes
  competing to fill one list and is wrong for shelves answering different questions.
- **The sport filter applies to every shelf, including people and clubs.** A filter part of the
  screen ignores is a filter nobody can trust — a thin shelf would be indistinguishable from an
  unapplied one. There is no such thing as a player without a sport here: a Level is a level *at
  a sport*, so on the tennis screen a player either has a tennis level or is not shown.
- **The first run is three shelves and that is a finished screen.** A player who has just
  onboarded is in no matches, has viewed nothing and holds no standby entries, so shelves 1, 4
  and 5 render and 2 and 3 do not. Nothing is added to fill the gap: no first-run shelf (it
  would need the reliability record the platform does not yet collect) and no dismissible
  banner, because everything on Now is either a thing the player is in or a thing they could
  join, and a banner is neither.
- **Two shelves are not matches.** *New on Raketa* shows people — photo, name, level — and *New
  clubs* shows clubs. Their contents and their taps are ruled in
  [ADR-0051](0051-now-is-ordered-not-drawn.md) §*The shelves that are not matches*.

## Consequences

**Easier**

- The empty-state contradiction is gone rather than traded: no card claims the city is empty
  while matches exist, and no badge prints a number that is not the match's.
- A new claim is a new shelf, not a renegotiation of scarce vertical space. *Play somewhere
  new*, *your usual club*, *friends' matches* all become a row in a list the server owns.
- Reordering the screen, or retiring a shelf that nobody swipes, is a server change. Neither
  client ships a release for it.
- Horizontal position survives a re-render, which the current strip does not — so a live update
  no longer throws away where the player had scrolled to.

**Harder**

- **This is the largest departure from the two UI documents in this effort.** They are final on
  the screen and they describe a vertical list; a delta now governs their Parts 5 and 6. The
  reason it is a supersede rather than an overrule is that the section shapes were sized against
  a six-card vertical budget that shelves abolish, and neither document was deciding against
  shelves — the component they would have used is defined in one of them and marked unused.
- **Fifty cards is a much larger surface than six**, and everything about it — retrieval cost,
  scoring cost, the payload, the scroll performance — is roughly an order of magnitude bigger
  than what `4` Part 6 budgeted for.
- **A repeat is now possible by design**, and the thin-week guard is a heuristic. A city with
  eight matches will sometimes show one of them three times, and that will look like a bug to
  somebody.
- **Two shelves make claims about people and clubs**, which Now had never done. That drags
  profile visibility, consent and eventually a profile screen into a screen that was purely
  about matches.
- **Five shelves × ten cards is a lot of scrolling to reach the fifth claim.** The bottom shelf
  will be seen by far fewer players than the top one, and the fixed order means we have decided
  that ordering for everybody rather than learning it.

**Neutral**

- No engine changes. Floors, caps, shelf membership and order are all ranking-layer policy,
  which [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md) already placed
  outside the engines.
- The match card, the fit badge and its two-band rule are untouched and remain final in
  `rakieta-now-section-ui-spec.md` §B9.
