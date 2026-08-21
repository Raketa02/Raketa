# ADR-0084 — The sport bar is five fixed chips, and a sport you have no level at is a door

- **Status:** Accepted
- **Date:** 2026-08-22

## Context

The sport bar is fully drawn and not at all specified. Both UI authorities fix its
anatomy — five `.chip.sm` buttons in the order **All · Padel · Tennis · Squash ·
Badminton**, a 5 px rounded swatch on the four sports and none on `All`, selection in
`--ink` because *"a filter is not an action"*, `role="radiogroup"`, one of only two
focusable element groups on the whole screen, and *"filters the whole screen; persists to
Find and Create"* (`1` §3.3, §7.1; `UI` §345, §1007, §1032, §1079). What no document
states is **what data backs the chips**, and every question under that heading was open:
which sports a player sees, what `All` means, what is selected on open, where the choice
persists, and what happens on a sport the platform cannot rank the player at.

**Four facts decided most of it, and none of them was written down anywhere.**

- **The sports picker throws its answer away.** `SportsPickerScreen`'s own docblock:
  *"The selection is never persisted — not to the server, not to the device. It exists
  only to order the next few assessments."* So there is **no stored list of the sports a
  player plays**. The only durable per-sport fact about a player is that a **Skill rating
  exists** for `(player, sport)`, which is exactly what `CONTEXT.md` already fixes: *"a
  per-player onboarding flag would be a second, coarser truth about the same fact."*
- **A player standing on Now always holds at least one rating.** `entryDestination` sends
  `ratings.length === 0` to `welcome`. The "player who declared nothing" case cannot
  occur on this screen, and no design needs to carry it.
- **Tapping an unrated sport produces a sentence that is false.** The fit engine scores a
  match against the player's level; with no level every candidate in that sport scores
  `null` and drops out, and the screen prints *"Nothing open in Squash right now — we do
  not invent players to make a city look busy."* Kraków may be full of squash. The
  specification set caught this and left it open as **[GAP-D1]**, proposing *"a distinct
  empty state keyed on `rating_missing`"*.
- **There is no way to take up a new sport at all.** The questionnaire is reachable only
  from `welcome`, which only a player with zero ratings ever sees. Nothing on You,
  nothing on Now, nothing anywhere lets a padel player acquire a squash level. The v37
  prototype does not model the gap either — its fixture player simply arrives holding all
  four.

**A fifth fact arrived late and inverted an argument this ADR had already made.** An
undeclared limit is not a penalty — `matchfit.core.constraint_term` scores it
`FULL_MARKS`, deliberately and with the guarantee written into the return type, because
*"a missing price ceiling means eligible at any price"*. So a player's **blank** sport
outscores her **declared** one: every squash match is a perfect match against nothing,
while a real padel match at 42 zł against a declared 35 zł ceiling scores less than full.
The week a player adds a second sport, a purely score-ordered `All` fills with it.

Two shelves survive an unrated sport and one design turned on noticing it: *New on
Raketa* and *New clubs* are **index queries with no scorer**
([ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md)), so
they still find squash players and squash clubs. The unrated screen is therefore
**matches missing, everything else present** — not a blank page.

## Decision

**We will ship five fixed chips for every player, resolve `All` to the sports the player
holds a rating at, reset the filter to `All` on every visit, and answer an unrated sport
with a door into the questionnaire rather than with an empty shelf.**

### The bar

- **Five fixed chips, identical for every player**, in the authorities' order. A chip for
  a sport the player has never been rated at is kept **deliberately, at a named cost**:
  hiding it hides the business, and the moment a padel player decides to try squash is
  the moment we are most valuable to her. The dishonest empty message that a fixed chip
  creates is a **copy problem with a fix** (the door, below); a hidden chip is a **dead
  end with none**. Adding a fifth sport is already a code change and a release
  (`CONTEXT.md`, *Sport is a closed enum*), so a fixed row introduces no new coupling.
- **`All` means the sports the player holds a rating at**, never every sport on the
  platform. The empty line the authorities already fix — *"Nothing open in **your
  sports** right now"* (`UI` §742, `spec` AC-61) — is true only under this reading, and
  it is the only reading under which *Best fit for you* is a claim about the player
  rather than about our inventory. The cost scales with sports played, and the majority
  play one, for whom `All` and their sport are the same screen.
- **`All` is selected on every visit.** The filter hides the enrolled strip as well as
  the shelves (`V.home`: `ms.filter(m => S.sport === 'all' || m.sport === S.sport)`), so
  a remembered filter can hide a match the player has **paid for and is playing
  tomorrow**. That is a different class of mistake from showing too much, and it decides
  the default outright.
- **The filter lasts a visit, and a visit ends after 30 minutes away.** A cold start is
  not the boundary: phones do not close apps, so "reset on launch" would almost never
  fire and the protection above would be decorative. Stepping out to answer a text keeps
  the filter; returning the next morning does not.
- **The selection is never a server-side fact about the player.** It rides on the request
  and nothing else — which is
  [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md)'s *"the request
  carries the selected sport and nothing else"*, with the `all` value now defined. A tap
  on a filter chip is not a statement about who somebody is, and storing it would let a
  stray tap follow them to a new phone.

### The door

- **On a sport the player holds no rating at, the position the ranked shelves would
  occupy carries a door**: the honest sentence, and a route into that sport's
  questionnaire. *New on Raketa* and *New clubs* **still render beneath it**. The clubs
  are the argument for spending the two minutes, so they belong under the ask — and the
  screen answers the player's actual question, *is there squash here*, while asking.
  This closes **[GAP-D1]** with a destination rather than with a better sentence.
- **The door is a block on the wire, in the list, in order** — not a flag the phone
  reasons from, and not an inference the phone draws from absent shelves.
  [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) leaves the phone no
  rules to hold, and an inference would fire wrongly on any day the city genuinely has no
  matches in a sport the player *is* rated at. The block also carries **which sentence**
  it shows, so *"take the squash questions"* and *"pick up where you left off"* are one
  block type and the client never learns the difference. Wording, destination and the
  block's very existence then change without an app release.
- **Finishing lands the player back on Now, filtered to the new sport**, having passed
  the result screen and the **skippable preferences editor** for that sport — and
  **never** the city screen or the Proposals opt-in, which are answered once per player
  and asking again is the app forgetting them. This narrows the onboarding tail
  [ADR-0066](0066-a-declaration-is-per-sport-and-the-ask-is-never-furniture-on-now.md)
  fixes (`result → city → editor → opt-in → done`) to `result → editor → back` for a
  sport added later. Two minutes in is the cheapest moment we will ever get to ask how
  somebody wants to play a sport they have just taken up.
- **An unfinished run no longer outranks an existing rating.** `entryDestination`'s
  current order — *"a player rated at padel with a tennis run half-answered should land
  back in the tennis questionnaire"* — is **right for the player it was written for and
  wrong for the one the door creates**: four squash questions answered on a tram must
  never stand between a player and the padel match she has paid for. A run in progress
  takes over the screen **only for a player holding no rating at all**; otherwise it
  parks, and the door becomes the way back into it. The existing one-session deferral
  survives for the first-run case it was built for.
- **A parked run continues where it stopped**, however old. The questionnaire already
  carries its own control for walking back and changing answers
  ([ADR-0020](0020-revisable-assessment-answers.md)), so nothing is stranded and
  no second door is offered beside the first.

### Ordering, and the line that explains it

- **`All` merges the player's sports on pure fit score.** A shelf called *Best fit for
  you* that reserves a slot for a match it does not think is one of the best six is a
  shelf lying politely. The remedy for a sport crowded out is one tap on its own chip,
  which is a filter working.
- **`All` may carry the declaration caption in exactly one case: a sport the player holds
  a rating at and has declared *nothing* for.** This narrows
  [ADR-0066](0066-a-declaration-is-per-sport-and-the-ask-is-never-furniture-on-now.md)'s
  *"it reads the currently filtered sport's declaration"*, which had no `All` case.
  Silence was the default and remains it — a line about one sport cannot speak for a
  screen about two — but the full-marks finding makes this the case where the screen
  genuinely **is** mostly that one sport, which is what the line exists to explain. One
  tap then fixes it permanently.
- **We will not change how the engine treats a blank limit.** `FULL_MARKS` is deliberate,
  is relied on well beyond this screen, and its guarantee is written into a return type
  precisely so that nothing can quietly move a declared limit onto the evidence side.
  Reopening it to tidy one shelf's ordering would be paying in the model for a
  presentation problem.

### Ruled out, and one defect recorded

- **The prototype's gallery override does not ship.** `S.gallery` forces every state card
  on screen and ignores the filter (`UI` §897), but it touches only the enrolled strip's
  `shown` list, never the feed, and it exists to demonstrate the state table. Nothing on
  the real screen reads it.
- **Whether a player may *create* a match in a sport she holds no rating at is Create's
  question**, on a surface this map already excludes (*the level toggle on open-match
  creation*, ruled out on [#1](https://github.com/Raketa02/Raketa/issues/1)). The chip
  row carries to Create by the authorities' own rule; what Create does with an unrated
  sport is decided by whoever builds it.
- **ADR-0066's *"one card per declared sport, in sport-picker order"* cannot be
  implemented as written**, because the sports picker's selection is never persisted.
  The only durable order is **the order the ratings came to exist**. Recorded here rather
  than ticketed: nothing on Now reads it, and the answer is forced — there is exactly one
  order available.

## Consequences

- **Three of five chips lie to a one-sport player until she taps one.** That is the
  accepted cost of a fixed row, and it is bounded: the lie survives exactly one tap,
  after which the door tells the truth and offers a way out of it. Before the door is
  built, the lie is unbounded — so **the door is not a follow-up to the fixed row, it is
  the condition on it.**
- **The app gains its first growth path for an existing player.** Until now, the set of
  sports a player could ever be rated at was fixed at onboarding, permanently, with no
  surface anywhere to change it. This is a larger change than a filter ticket looks like
  it should produce, and it is worth naming as such.
- **A shipped, tested rule changes.** `entryDestination` is a pure function with its own
  test file describing the current order as deliberate; this reverses it for players who
  already hold a rating. The test file must change with it, and its docblock — which
  argues the current behaviour is correct — must be rewritten rather than deleted, since
  it is right about the case it was written for.
- **`All` costs what the player plays.** Resolving `All` to the player's rated sports
  means the funnel runs once per sport and merges, so a two-sport player costs twice a
  one-sport player against
  [ADR-0069](0069-the-budget-is-two-budgets-and-both-fail-the-build.md)'s p99 — on a
  budget that is **modelled and never measured**, and was sized for one sport. The
  majority play one, but nothing enforces that and nothing yet measures the tail.
- **A newly added sport still crowds `All`**, and we have chosen to explain it rather
  than to prevent it. A player who reads past the line, or who declines to fill the
  editor in, sees a merged screen dominated by her newest sport for as long as she leaves
  it blank. The line is the only mitigation and it is a sentence, not a mechanism.
- **The door's block is new wire.** ADR-0070 enumerated three regions and shelves
  carrying codes; this adds a block that is neither, and every client that draws Now must
  handle it or drop it. Under
  [ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md) adding it
  strands nobody, but an old build that ignores it renders an unrated sport as a blank
  screen — the exact failure the door exists to fix.
- **Half an hour is a judgement with no evidence behind it.** It is the conventional
  session boundary and nothing here measures whether it is right; a player who habitually
  puts the phone down for twenty minutes keeps a filter we would rather have cleared.
- **Nothing here is built.** The chips, the door, the block, the tail after a second
  sport, and the entry-gate change are all specified and unwritten.
