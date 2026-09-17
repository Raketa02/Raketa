# ADR-0159 — A record is read through a prior disclosure, and the refusal names nothing

- **Status:** Accepted
- **Date:** 2026-09-08
- **The 2026-09-08 sportsmanship amendment's split amended by [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §5** — the
  figure and its count cross to the subject too, `SubjectSportsmanship` has one method,
  `sportsmanship_band` retires from the record and the invariant beside `is_self` with it.
  The cost is accepted and written beside the reversal there.

## Context

[#373](https://github.com/Raketa02/Raketa/issues/373) opens a surface this platform has
never had: **tapping a face and being told who that person is.** Today that gesture opens
the Fit breakdown — weights, contributions, a sub-total — which answers a question about a
*pairing* to somebody who asked a question about a *person*.
[#377](https://github.com/Raketa02/Raketa/issues/377) is the first ticket behind it, and
what it decides is not the sheet's contents. It decides **who may open one, and what
happens when they may not.**

Four forces shape that, and only the first is about product.

**A record is live and a card is recorded.** The obvious move is to widen `player_card` and
let the sheet draw from the row the client already holds. ADR-0107's rule for admitting a
field would allow most of what the sheet needs — every one of them is a fact about that
person alone — but the card's *size* rule refuses it: a card is attached over the twenty
rows that survived a search and **frozen into a record kept for ever** (ADR-0104), so the
sheet's payload would be paid twenty times per search to be read at most three times and
usually never. It also inverts ADR-0107's own economics, which chose one round trip
because *"a batch profile route would … put a second request in front of* Why 78?". That
argument is about a **list**. A sheet opened by a deliberate tap on one person is the case
where a second request is correct: it is one player rather than twenty, it has a legitimate
place to show progress, and it is not on the path to the screen.

**A route that takes a player id and answers with a person is an enumeration endpoint.**
Level, photograph, area, tags — for anybody in the city reachable by id. The fact that a
UUID is hard to guess is not an authorization model, and `POST /forecasts` already settled
the shape for a lighter payload than this one: *"unbounded, this would be a level lookup for
any player in the city reachable by id; bounded, it tells you nothing the shortlist did not
already show you."*

**The gates that decide who may be introduced are live, and they are partitioned.**
ADR-0095 reaches *every surface that shows one player to another*, and #374 has already
made the four — a block either way, an account hold, an account state that may not be
shown, and the mutual gender preference — one collaborator rather than a private step
inside the search read-back. The half of it that matters here is that the gender gate reads
the other side's preference off a **candidate index row**, and the index is keyed by sport
(ADR-0112). Which partition the question is asked in therefore decides whether it can be
answered at all.

**A refusal is a disclosure.** ADR-0095 is explicit that *neither party is ever notified and
the other side sees no trace anywhere in any response*, and ADR-0130 narrowed the search
read-back's own withholding on the same grounds. A record route has four ways to say no, and
three of them are facts about somebody else that the person asking is not entitled to.

## Decision

### 1. A new context, `player_record`, which stores nothing

`app/modules/player_record/` — **no aggregate, no table, no migration.** It is
`player_score`'s shape (ADR-0140 §1) with a second job: that context folds two records into
arithmetic, and this one folds five into a description and **enforces admission**. A player
record is derived from `users`, `player_profile`, `rating`, `games` and `player_score`, and
it is not a sixth record.

It is a new module rather than a widening of `matchmaking` because `matchmaking` owns *why
these people*, and a description of one person is not that. The sport-pill read in
particular would make the matcher a reader of every rated sport of every candidate — for a
fact no term may score.

### 2. Two routes, and the caller's is declared first

> `GET /api/v1/players/me/record` — your own.
> `GET /api/v1/players/{player_id}/record` — one player's.

The ordering is load-bearing rather than tidy: a parameterised segment declared ahead of the
literal one parses `me` as a player id and answers the refusal to everybody. It is the same
ordering `players/me/profile` already relies on.

**The response says whether the record is the caller's own**, and the client never derives
it. A sheet titled *How others see you* draws a different screen — no distance, a coarse
band where a figure would be — and a client deciding that by comparing the id it asked about
against the one in its session is a client that gets it wrong exactly once, on the screen
where being wrong is most visible. The subject's id is therefore **not on the response at
all**: there is nothing there to compare.

**Your own record is a second use case rather than a branch.** `ReadOwnRecord` names no
admission collaborator, so the `/me` route does not depend on the gate machinery — which
binds a candidate index and refuses when there is none. That is right for a sheet about a
stranger and absurd for the one screen that tells a player how they appear. It also leaves
no branch for anybody to delete: a use case that took an admission and skipped it when
`reader == subject` is one refactor away from skipping it when it should not.

**There is no `?sport=` yet.** The reader's arrival sport selects which sport the sheet is
*about* and never who may be seen; nothing on this response is per sport today, so the
parameter arrives with the skill card that needs it (#379).

### 3. A record is read through a prior disclosure, never about a person

Admitted when **any** of these holds, and never otherwise:

1. `reader == subject`.
2. A search of the reader's **returned** them.
3. The pair share a **live challenge** or a **game**.

**Nothing expires.** A search record is kept for ever (ADR-0104), so any window shorter than
that could only misfire: it would refuse a face the app is *currently showing*, from a
shortlist the reader can still open. There is no `since` on any read here and no age on any
answer.

The third strand is not a nicety. A court is sent off the **organiser's** search, so the
organiser has been shown the invitee and the invitee has been shown nothing at all — and
they are the person who most obviously needs to know who they have just been asked to give
up an evening to.

This is expressed as one port, `PriorDisclosure`, with **three implementations**. A fourth
surface that introduces one player to another satisfies the same demand with a fourth row in
the register, and this context never learns what it is.

### 4. The gates are re-run live, in the partition of the disclosure

The disclosure entitles a reader to **ask**; the four fail-closed gates decide, on every
open. A block placed since the search refuses the record.

**And they are evaluated in the partition the disclosure happened in, never in the reader's
arrival sport.** The search that returned them has a sport, the challenge has a sport, and
the self case has no gates. Without this rule, a subject rated only in squash and opened
from a padel context has no index row, the gender gate cannot be evaluated, *a gate that
cannot be evaluated excludes*, and the route refuses somebody the reader demonstrably just
saw. This is why `PriorDisclosure` answers in **sports** rather than in booleans, and why
the partitions are walked in the **sport registry's own order** — the answer does not depend
on the order, but which database reads happen does, and a walk in hash order is a different
sequence of reads on every process (ADR-0105).

**The reader's own hold is refused here too.** The four answer about *subjects*; whether the
person asking may be shown anybody at all is the surface's own entry rule, and a hold points
both ways (ADR-0095). A hold that did not reach this route would be a hold ending at the one
route that remembers what a search already showed.

### 5. One refusal, and it names nothing

Never disclosed, blocked either way, held, and no such player return **the same status and
the same body, byte for byte**: `404`, `record_unavailable`, one fixed message, no
`details`.

A payload naming the gate delivers a block to the one person the block was meant to be
invisible to. A payload separating *never disclosed* from *no such player* answers *is this
id real* about a stranger. A `403` would say *there is somebody here you may not see*, which
is already more than this refusal is allowed to say — so it is a `404`, and the client draws
one line: *This record isn't available.*

The indistinguishability is asserted **as a sameness** rather than as four statuses
(`tests/api/test_player_record.py`), because four assertions about four codes all pass on
the day somebody adds a fifth cause with a fifth message.

**And the gate runs before any provider is touched.** A read that fetched a stranger's
handle, photograph and area and *then* refused would have performed the lookup the whole rule
exists to prevent.

### 6. This context declares its own ports and its own types

Four demands — `SubjectIdentitySource`, `RecordPhotoLink`, `PriorDisclosure`, `RecordGates`
— each in this context's own vocabulary, satisfied by adapters that translate. The
alternative was to reuse `matchmaking`'s `CardIdentity`, which carries three of the five
fields this sheet's header needs, and it is refused: a record that borrowed a card's type
would inherit a **card's closed list**, and the two surfaces have opposite constraints — a
card is short because it is paid twenty times and kept for ever, and a record is long because
it is one person read live.

The cost is a second spelling of two strings — `OnCourtVerdict` beside
`PhotoReviewDecision` — and it is paid deliberately, exactly as `games` pays it for
`PlayedOutcome` beside `PairwiseOutcome`. What keeps it honest is that the agreement is
**asserted**: a value added to either enum without the other turns the build red, because a
client reading a card and a record must not be handed two words for one fact.

The rule is held by an **import contract** rather than by a test, because nothing else could
hold it: an application layer importing `CardIdentity` would look like sensible reuse in the
diff, and no test would go red.

### 7. `matchmaking` grows one read, and it is a question about a pair

`SearchStore.sports_shown_in(searcher_id, player_id)` — every sport in whose partition this
searcher was shown this person. Both ids are in the signature and neither is optional: a
method taking a searcher alone would answer *everybody you have ever been shown*, which is a
list this platform has no route for and no reason to assemble. The near-miss band is not
readable through it, for the reason it is not readable through anything on that port — a
player withheld from a search was shown to nobody and was disclosed by nothing.

## Consequences

**A record costs a second request, and that is the trade this ADR chose.** It is paid on a
deliberate tap and never on the path to a screen, and it is the reason a shortlist did not
get thirty percent heavier for a sheet most people never open.

**Admission costs three reads and up to four gate evaluations.** One indexed query over the
search record, and two directory folds; then one gate evaluation per disclosed partition
until one admits, each of which is a profile load, three set reads over a single id and one
index binding. In the overwhelming case there is one partition and the loop runs once. If
that ever stops being affordable, the fix is a narrower disclosure read on the provider's
side, not a cache of who may see whom — a cached permission is a stale block.

**A refusal is deliberately unhelpful, and support will feel it.** *This record isn't
available* is the whole of what anybody is told, including a player who typed nothing wrong
and a developer reading their own logs. The `trace_id` is what ties a report to a server log;
the response body will never say more.

**A held player can read their own record and nobody else's.** That is a deliberate
asymmetry: the sheet is the one screen that shows somebody how they appear, and *a penalty
nobody can look up is a penalty nobody can fix.*

**A pair whose challenge lapsed loses that strand.** The sender still holds the search that
made it, so this is only visible for an invitee whose seat has ended — they can no longer
open the record of the person who asked them. That is the correct reading of *share a live
challenge*, and if it turns out to matter, the remedy is a fourth strand argued on its own
terms rather than a widening of this one.

**The context will grow, and every zone that arrives is a port and not a table.** The skill
card, the metered rows, opponent variety and the sportsmanship figure are all somebody
else's facts. The day this context grows a migration is the day it stopped being an
assembler, and that should fail a build rather than pass a review, so
`tests/unit/test_player_record_stores_nothing.py` walks the context for an import of the ORM
and the migrations for a table named after it.

## Amendment — 2026-09-08: the parameter arrives, and the demands are six

Building the sport pills and the skill card
([#379](https://github.com/Raketa02/Raketa/issues/379)) cashed the two forward references
above. Both are corrected here rather than in place, because this record is immutable once
accepted.

**§2's *there is no `?sport=` yet* is now a parameter on both routes**, and it does exactly
what that sentence promised it would: it selects which sport the sheet is *about* and reaches
nothing else. `ReadPlayerRecord` hands it to the assembler and never to the admission, which
still runs in the partitions of the **disclosure** — so a caller naming a sport they were
never shown this person in changes what is drawn and nothing about whether it is drawn. That
is asserted rather than described: the admission stub in `tests/unit/test_read_player_record.py`
records what it was asked, and there is nowhere on its signature for a sport to arrive.

**§6's *four demands* are six.** `SubjectRatings` answers *every sport this person is rated
in*, and `SubjectForm` answers *how their last few counted games in one sport went*. Both are
single-player reads, which is now four of the six — a record is one person opened by a
deliberate tap, and a set-shaped port here would be a contract nobody can honour cheaply for
a caller that never batches.

**One rule moved into this context and it is the only one here.** `domain/sport_choice.py`
resolves which sport the sheet is about: the sport asked for where they are rated in it,
otherwise their **most counted**, ties broken by the sport registry's own order, and `None`
for somebody rated in nothing. It lives here because it is a question about the *reader* —
nobody else could answer it — and every other figure on the sheet still arrives from the
context that owns it, already decided. Registry order is **structural**: both functions walk
`Sport` and look the mapping up, rather than iterating a mapping and sorting afterwards, so
ADR-0105's failure mode has nowhere to happen.

**The cost of §6's second-spelling rule is paid a second time**, on the same terms.
`GameOutcome` sits beside `games`' `Outcome` carrying the same two strings, and the agreement
is asserted in both directions in `tests/unit/test_player_record_skill.py` — as
`OnCourtVerdict`'s is against `PhotoReviewDecision`.

**Two provider ports widened, and one of them deliberately did not.** `rating`'s
`RatedPlayerQuery` gains `ratings_of(player_id)` — one player and every sport, the mirror of
the existing read's twenty people in one sport — and it is on the **read** port rather than
the repository precisely because a sheet drawing a number must not hold something it could
save. `games`' `GameHistoryQuery` gains `recent_results_in(player_id, sport=, now=)` as a
**second method and not a parameter on the set read**: that one is what a search attaches to
twenty rows and freezes into a record kept for ever, and narrowing it would make the same
person's card read differently before and after. The new one filters on the sport **before**
it trims to five, which is the whole reason a consumer could not have built it out of the
other.

**One number on the skill card is not the number the player card carries under the same
word.** `counted_games` here is *how many confirmed counted results have moved this Level, in
this sport* — `SkillRating`'s own applied-games count — where the card's is *how much have
they played*, over every sport, including an evening nobody agreed a score for. The skill card
claims to say what a certainty **rests on**, and the honest answer to that is the results that
moved it: a number off the same stream as the Level beside it, which therefore moves in step
with it (ADR-0139). The cost is admitted — a confirmed result is on the card before the
catch-up job has run and before it is here — and it is the right cost, because the alternative
prints a certainty beside a count of games that certainty has never seen.

**Nothing else moves.** The four refusals are still one refusal, admission is still read
through a prior disclosure with no expiry, your own record still has no gates, and this
context still stores nothing at all.

## Amendment — 2026-09-08: opponent variety, and a seventh demand

Building opponent variety ([#380](https://github.com/Raketa02/Raketa/issues/380)) cashed one
more of the forward references above: *the metered rows, opponent variety and the
sportsmanship figure are all somebody else's facts*, and this is the first of the three to
arrive. It arrived as a port, and this context still has no table.

**§6's demands are seven.** `SubjectVariety` answers *how widely does this person spread their
games* — five of the seven are now single-player reads. On this one the single-player signature
is a **fence rather than a convenience**, and that is the whole argument for it being a
*separate port on `games`* rather than a sixth fact on `GameHistoryQuery`: the fold is
deliberately unbounded, and an unbounded fold on the port a search already holds is one
somebody eventually calls inside the walk over five hundred candidates ADR-0098 §4 bounds. The
narrow type is what makes that unreachable rather than discouraged, and both sides of the seam
assert their own signature.

**It returns as this context's demand, which is what ADR-0098's withdrawal said would happen.**
Opponent variety was contracted on `player_score`'s behalf for two consumers, both were struck,
and the amendment recorded the terms of its return: *if a later term wants variety, it returns
as that term's demand and signs for it.* This record is that consumer. It is **not a strand** —
it prices no promise and enters no weighted score — and the matcher still never reads it.

**Unbounded is the definition and not an omission.** *How widely do they spread their games* is
a claim about a habit, so there is no window, no decay and no floor. A window would be a second
horizon that must not disagree with the matcher's; a floor — a minimum number of games before
the figure is published — was in the older implementation document and is **dropped rather than
forgotten**, because the newer decision publishes the **raw pair** and a pair carries its own
sample size. *Fourteen of twenty* and *seven of ten* are the same share and different claims,
which is the argument the metered rows beside it print their raw fractions for; a percentage on
this response would be the one number that could hide which of the two a reader is looking at,
and it is a client's division rather than a platform judgement.

**Two absences on one sheet, and they are different questions.** `skill` is absent for somebody
rated in nothing; `variety` is absent for somebody no counted game was ever recorded for.
Neither implies the other — a newcomer rated in nothing may have played all week, and somebody
rated in four sports may never have had a game counted — so the assembler asks for variety
whatever the sport resolved to, and asks for a run of form only when one did.

**`?sport=` does not reach it, and that is a third thing that parameter does not do.** A person
who plays padel with the same four faces and squash with twenty has one habit, and a figure
narrowed to a sport would be a different statistic under the same word.

**The cost of §6's second-spelling rule is paid a third time.** `games` measured
`distinct_counterparts` over `counted_games` — everybody who was on a court with them, on that
context's own rule that *a pair is anybody you were on a court with*, partner included — and
this context prints `distinct_opponents` over `games_played`, which is what the row is called on
screen. The rename lives in one adapter. And on the provider's side the denominator is
`counted_games_for`'s own predicate, written once and read by both, because the sheet prints
this pair beside a count of counted games and two spellings of *counted and played* would
eventually disagree on the same screen.

**Nothing else moves.** The four refusals are still one refusal, admission is still read through
a prior disclosure with no expiry, your own record still has no gates, and this context still
stores nothing at all.

## Amendment — 2026-09-08: the two live strands, and an eighth demand

Building the metered rows ([#381](https://github.com/Raketa02/Raketa/issues/381)) cashed the
second of §6's three forward references. Nothing new is computed anywhere: the raw counts
already existed in `player_score`'s domain and were never put on a wire, so what changed is
that the caller stopped throwing them away.

**§6's demands are eight.** `SubjectReliability` answers *what has the platform watched this
person do* — the published Player Score and the rows it is the mean of. It is the **first
demand here whose provider reads a set**: `PublishedScoreQuery` answers about a whole
collection because the matcher asks it once per search over every candidate still standing, and
the narrowing to one person happens in the adapter. That is the mirror of `SubjectVariety`,
where the single-player signature is a fence against an unbounded fold; here it is the record's
own shape refusing to inherit the shape of somebody else's caller.

**The raw pair crosses, and so does the figure — and the difference from opponent variety is
the argument.** Variety publishes two counts and no percentage, because the division is a
drawing decision and the figure prices no promise. A strand's figure is different in kind: it
is the number the platform **acts** on. `StrandRatio.value` is derived in one place precisely
so that a card, a profile and the matcher's evidence cannot print three roundings of one
record, and a client dividing `good` by `opportunities` would be the fourth. So all three
cross, and the two counts are what keep a perfect record over nine and one over forty visibly
different claims.

**The weights stay off the wire.** The blend arrives already taken, and no row carries its
weight. They are a fact about how the number is made rather than about the person, and a client
holding them could both re-derive the pill — the fourth rounding again — and draw one strand as
worth more than another, which no screen here claims. It is also the boundary
[ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)
drew: these weights live in `player_score` and never in a ruleset, because a weight release must
not change what somebody's own profile says about them.

**A third absence, asking a third question.** A player with no publishable strand has the whole
zone omitted — no `player_score` to draw a red pill from and no empty `strands` to head a card
with. It is not `skill`'s absence, and it is not `variety`'s: a plan that dissolved and a seat
that ran out are opportunities here and neither is a game anybody played. Nobody has failed to
turn up who was never due to.

**§6's second-spelling rule has one exception, and it is argued rather than taken.**
`ReliabilityStrand` is imported from `app/engines/matchfit/` rather than respelled. What §6
refuses is borrowing another *context's* domain types; the engines are the pure layer every
context reads and none of them owns, exactly as the kernel is — and `player_score` already made
this argument about these same five names, in the `.importlinter` note beside its own contract.
A second spelling would also put two words for one strand in front of a client, since the codes
are already on the player contract under that enum's own name.

**Nothing else moves.** The four refusals are still one refusal, admission is still read through
a prior disclosure with no expiry, your own record still has no gates — and it now carries the
number that decides who they are offered to, which was the point of the screen — and this
context still stores nothing at all.

## Amendment — 2026-09-08: what other players said, and the zone that turns on who reads

[#382](https://github.com/Raketa02/Raketa/issues/382) added the fifth and last zone on the
sheet, and it is the first thing here that is **not the same fact retitled for the subject**.
Everything else on this record is one answer drawn two ways; this is two answers.

**A ninth demand, and the second on this list whose provider owns a store.**
`SubjectSportsmanship` is answered by an adapter over `sportsmanship`'s
`PublishedSportsmanshipQuery`. It takes **neither a sport nor an instant** — the only demand
here that takes neither — because how somebody is to play with is not a padel fact and
nothing about it decays: the window is fifty *people*, so an opinion falls out of the record
when fifty others have since had one and never when a calendar passes. A `now` would be a
second horizon nobody could keep in step with the first.

**Two methods, and the second cannot say what the first says.** The figure and the count of
distinct raters cross for a reader; a coarse band and nothing else crosses for the subject. A
published average beside a published count in front of the person it is about is a
subtraction that names each new rating exactly, and they know who they played
([ADR-0158](0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md) §2). The split is
on the *port* rather than in the assembler, because a use case that received the figure would
already be holding the thing the rule forbids whatever it then rendered — so the sheet about
*you* asks a question with no figure in its answer, and the question with one is never put.

**`is_self` decides more than a title now, and `PlayerRecord` is where that is checked.** Two
fields, at most one ever present, and an invariant on the record itself refuses a figure
beside `is_self` and a band without it. The branch is what decides; the invariant is what
makes a branch taken the wrong way loud rather than a screen quietly showing somebody the
arithmetic of their own ratings. It is still **one response type** — a second one would be
how *How others see you* and *how a stranger sees you* stop being the same screen.

**A fourth absence, asking a fourth question.** A player nobody has rated has the whole zone
omitted, on both sides of `is_self`. It is not `skill`'s, not `variety`'s and not
`reliability`'s: rating is a favour, ignoring a card costs nothing, and nothing anywhere
records that somebody did not answer — so a nought here would publish a verdict nobody gave.

**§6's second-spelling rule is paid a fourth time, and this one has a wire consequence.**
`OpinionBand` and `WhatPlayersSaid` are declared here and translated in an adapter;
`tests/unit/test_player_record_sportsmanship.py` fails the build if the two vocabularies stop
agreeing. **The band takes a different name from the provider's on purpose**, as
`OnCourtVerdict` does beside `PhotoReviewDecision` — and here that is two rules meeting,
because this enum reaches the wire *as itself*: the emitted contract is one namespace, and a
class of the same name in two modules does not shadow the other, it renames both. That is
`RecordLikelyRangeSchema`'s argument one layer down, and it renamed the schema beside it into
`RecordSportsmanshipSchema` too.

The other wire cost is different in kind: the forbidden-fact sweep refuses the property name
`stars` outright, so the figure crosses as `average` and `raters` — an honest name for a mean
rather than a second word for a tap — and a test walks the emitted contract to assert those
words reach exactly one response type, which is where *it is not on search result cards*
stopped being a promise.

**Nothing else moves.** The four refusals are still one refusal, admission is still read
through a prior disclosure with no expiry, `?sport=` still says what the sheet is about and
never who may be seen, your own record still has no gates, and this context still stores
nothing at all.
