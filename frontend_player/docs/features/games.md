# games — the result argument and the game screen

> The design record for `src/features/games/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**The result argument is one screen and eight states, and the state is derived**
([#314](https://github.com/Raketa02/Raketa/issues/314),
[ADR-0137](../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). **A result is the
record that a game happened** — no booking, no calendar, no date field anywhere — so the entry
_is_ the fact, and everything after it is an argument bounded to two rounds —
`domain/resultArgument.ts` is named for it, because the glossary word _conversation_ belongs to
the room the first acceptance opens, and two of them in one codebase is how somebody eventually
subscribes the wrong one. It folds the standing, the scores on the table and **which seat is
yours** into what to draw, and nothing outside that file reads a `GameStanding`: a
**correction** and a **counter** are the same `POST` and completely different news, and #314's
own worry is that _"a player will spend an attempt fixing a typo."_ Three of the eight are worth
knowing. **Silence confirming is drawn before
it happens**: the standing line says it **on the row as well as on the screen**, so a deadline is
never something a player reaches by tapping, and the screen adds
`prototype/result-confirmation`'s clock block over it — a figure at arm's length above one
sentence. **`both-stand` draws both scores and offers the agreement that ends it** — ADR-0137
§4's only exit short of the game going unscored, and the one the screen could not offer while
`standing_proposal` was _"when exactly one is"_ and the wire returned **neither** score
([#317](https://github.com/Raketa02/Raketa/issues/317),
[#318](https://github.com/Raketa02/Raketa/issues/318)) — the **eighth** state is the agreement
itself, below. The reader's own score is drawn quiet
above the other side's, the one control is named for the score it agrees with, and the copy names
the way out instead of stating an ending as though it were the only one. There is never a counter
there: that side has had its one turn. **Which of the three `AWAITING_ANSWER` screens it is comes
off the count** — `proposals` carries nought, one or two — rather than off an absence that used to
mean _nothing entered_ and _both sides have spoken_ alike. And **an agreement is a state of its own rather than a flag on the three it can happen in**: for
the length of the grace the standing still reads `AWAITING_ANSWER`, but the proposing side has
stopped waiting on silence, so the headline and the clock say the score was agreed and when it
settles, the correction goes (`state_result` refuses it with `the_other_side_has_answered`, whose
sentence can now say _while this screen was open_, because the control's own absence is what
proves the timing), a second agreement from the same side goes with it, and **the disagreement
stays** — inside the grace a counter still beats an agreement, which is the whole reason the
grace exists. It is an arm rather than an optional field because carried as a field it was a
state every renderer had to remember to pre-empt its own `switch` with, and the one that forgot
said something false. It **keeps both proposals**, because what is left to do is read off them:
the side that may counter is the side that has not spoken, and two scores standing means neither
can — the aggregate's one-per-side cap rather than a rule this client invented.

**The instrument is the prototype's, and so is most of the copy.** #314 says the score-entry
interaction is solved work, and it is: a **pad** over a grid of the sport's own legs, both sides
named above the columns they own, because _"`6-4 3-6 6-2` is not a score until you know whose 6 it
is"_ and a stepper is six taps to reach 6. The **`+` key** beside it is what keeps the range
honest — a padel third set is often a ten-point tie-break and a badminton game goes to thirty — so
_we know the shape, not the rulebook_ is built into the instrument and not only into the
validator. Variant C's layout comes with it: the score being answered stays on screen **beside**
the one being typed, and an unscored evening ends on a fact list rather than an apology. Two
things are rewritten because the model moved. **There is no absolute time anywhere** — the
prototype quoted one beside every duration, and this platform has no calendar to print one
against — so every span is measured from `read_at`, the instant the standing beside it was folded.
And **a person is named where a person acted, and a side where a side did**
([ADR-0141](../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A seat carries
a handle and nothing else about the person in it — no Level, no band, no run of form, because a
card is what a _searcher_ reads to decide about a game that might happen and this is the record of
one that did. So the eyebrow says **who you played**, which is what tells two padel games in a week
apart, and _tomek.p put a score up_ and _tomek.p agreed with your score_ name the person a result is
being settled with. The score's two columns stay _You / Them_ and _Your side / Their side_: a score
is a **side's** claim, capped one per side and answerable by either of the two who played it, so a
column headed with a handle would charge a doubles score to one of them. Every handle is drawn
**whole**, which is
[ADR-0107](../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4, and a seat
`users` can no longer answer for draws the unknown player's `?` rather than being dropped. The
prototype's `✓` went the way the on-court mark's did — **Archivo ships no U+2713** — and the
winner's row carries the word instead.

**One screen shows a game whatever state it is in, and the plan arrives on it as a child**
([#368](https://github.com/Raketa02/Raketa/issues/368),
[ADR-0149](../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §2).
**Grown, not replaced**: `GameScreen` was already a state-keyed detail surface with ten arms, and a
hand-off in the middle of one standing's life would give a player two different screens for the
same game depending which day they tapped it. What it grew is **one `ReactNode`** and **one word**,
and **`features/games` still never learns a plan exists**: no `Plan`, no ladder, no rung, and
`eslint.config.mjs` refuses the import. `GameScreenWithPlan` is the one place that holds both
halves — it does the join, folds the arm and fills the slot — and **both routes mount it
unchanged**, so a composition spelled at two call sites cannot drift at one of them.

**`AWAITING_ENTRY` is one standing over two landings, and that is the arm.** §5.2 lands _Planning_
and _Game on_ on **the plan** and _Today_ and _Needs result_ on **the score grid**, so the grid is
the screen on the two arms the moment has reached and **one press away** on the two it has not —
the press being `We played`, one word in `shared/vocabulary/theActsWords.ts` that the Now card's
door reads too — shared rather than either feature's, because the two reach each other at load time
and a word read across that seam mid-evaluation reads a half-built module. The word that crosses back into that feature is `EntryLead`, in its own
vocabulary rather than a rung in somebody else's, and it is **derived from the card's own door**
(`entryLeadOf`) so the two tables cannot disagree about where a button goes — _the verb names what
you arrive at_. **_We played_ is available on every entry arm**, not only the two that lead with it,
because `standing_of` gates entry on `entry_closes_at` alone: four people can arrange a game at six
and play it at eight without filling a slot. The cancel follows from the same fact — a grid that
_is_ the screen has nothing behind it to go back to.

**The child is the plan read rather than edited** — `Tag`s and never `Chip`s, one accessibility
element, with §22.2's **inverted** panel over it: it stops explaining an absence and names one,
because a player seeing _Zabłocie Sport · Saturday · 18:00_ inside an app may reasonably assume the
app did something about it. **The checklist is three lines, capped, in one order**, and its third is
**cited, not written** — `worthLine`, the whole of what survives ADR-0143 §8's refusal — so the
screen defers its own copy of that sentence on the entry arm rather than printing it twice. What the
arm changes is **the screen around the child and nothing inside it**: §22.6 settles that _the rungs
differ by the clock and not by the arrangement_, so the checklist is one rule on all four and no arm
reaches the child at all. **A plan arm asks for nothing, so nothing on it wears the one accent** —
the chat door is 6.1 `secondary` on every arm, because an accent in the scroller beside a quieter
control in the pinned slot inverts what pinning is for, and the coral comes back where
`Send this score` is pinned. **_Open the chat_ is always drawn, whichever door you came in by** — arriving
from Now it is the point and arriving from _Details_ it is the way back, so drawing it conditionally
on the route would make the surface depend on its door; it fails soft on the room being gone and on
nothing else. **One component, two routes** — `/games/[gameId]` and
`/chats/conversation/[conversationId]/details` — so each lights its own column and _back_ is correct
by construction, with **no `from` parameter** and `tabForPathname` still pure. Eight corrections to
the details design are **absences** rather than sentences and each is a record read out in
`GamePlan`'s own note — _part of day_ is not a slot, the lock button and its coral outline are
deleted, the slots are tags, _Sun 9_ is a date this app does not have, _60 min_ is a duration nothing
holds, and _COMPETITIVE_ is a search's mode rather than a game's kind — as is **press and hold for
the full record**, and as were the **pairing forecast and the player rows** — upheld then with an
argument of their own (a forecast helps you decide whether to play somebody, and on this screen
you already have), filed as [#346](https://github.com/Raketa02/Raketa/issues/346), and **reversed
since** by ADR-0161 for the plan lead, below.

**The plan lead is redrawn — an eyebrow and no title, three slots over two doors, nothing
pinned** ([#414](https://github.com/Raketa02/Raketa/issues/414), #410's design). `GameScreen`'s one
slot became three — `card`, `court`, `plan`, all opaque, drawn in that order on the plan lead and
nowhere else — and the screen still holds no plan, no ladder and no rung. **The eyebrow is
`formatEyebrow`'s**: the format read off the seats (the rule the Now card's retired eyebrow used,
living here now) and the kind off the game — `Doubles · Counted`, `Singles · Friendly`, stored as
words and drawn uppercase, **`Counted` and never `Competitive`** (§5.4 #8 stands), the kind clause
dropped where the build cannot read one. There is **no title under it**, the first screen in this
app without one (10.3 as amended, Part 16): the card names the people and the plan names the day,
so `gameEyebrow`'s handles and _arranged n ago_ — kept on every other arm — would be the same facts
twice. **The standing line, the shape line and the checklist go on this lead**: the card's bars say
what is agreed, the counter says how much, and the court is drawn rather than described; the
sentence about what a score records is drawn only once the grid is open, with the grid it is about.
**The two doors are in the scroll**: `Open the chat` is the app's first `dark` button, `lg` and full
width — _a filled action with no meaning attached_, which is what a wide door needs to be on a
screen that asks for nothing and so wears no accent — through the same soft-failing `useChatDoor`
join ADR-0149 §3 settles, drawn by the screen itself — which widens the seam the ADR named by one
importer, `games` reaching `conversations` for the word, the route and the join, and says so — in
a child of its own so the join is read where the door is drawn, over the one list the composition
already reads for the card's faces; and `We played` is `secondary` beneath it, opening the grid over the plan as before.
**Nothing is pinned while the grid is closed** — the design pins nothing — and the moment `We
played` opens it the footer is back with the send and `Leave it as it is`; the footer's own `We
played` went with that, because no entry arm reaches the footer with the grid closed any more (on
the score lead the grid is the screen). The score lead and the result arms keep today's screen
whole, and `result.test.tsx` asserts the entry window's sentence where it is still said.

**The plan lead draws its court's pairing — the forecast block and the players card, read beside
the game and never on it** ([#415](https://github.com/Raketa02/Raketa/issues/415),
[ADR-0161](../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md), #410's design). #346
had closed the reversal _wontfix_ on the argument that a forecast helps you decide and here you
have decided; the ADR settles it the other way on the argument #346 itself named — **a Planning
game has not happened, which is exactly why the challenge screen is allowed a forecast** — and pays
what the refusal priced: one route, `GET /games/{game_id}/pairing`, answering only while the game
is `AWAITING_ENTRY`, and **nothing on `GET /games`**. So this feature owns the read end to end —
`pairingApi`, `pairingMappers` (the wire boundary), `domain/pairing`, `usePairing` under
`gameKeys.pairing(gameId)` — and fills the `court` slot #414 declared with its own `CourtPairing`,
composed by `GameScreenWithPlan` because the players' faces come off the room join that composition
already holds and this screen may not read that list. **The read is enabled on `AWAITING_ENTRY`
and made on the plan lead alone**: the slot is drawn on the two plan-lead rungs and nowhere else,
the route refuses by name after the game has happened, and `forecastBlock.test.tsx` asserts a
result arm never asks. The route's three refusals — `game_not_found`, `pairing_is_history`,
`account_held` — are folded to _no pairing_ **by code** in the use case, an answer rather than an
outage, so a refused game is neither retried on every focus nor reported as the platform being
down. **No arithmetic on the client**: the gap is printed with the sign it was served with, the bar
takes it as its `advantage` on 7.11's one fixed scale exactly as the builder's forecast card feeds
it, and the range, the band and the percentage are the engine's. The words and the bar are
**cited, never re-spelled** — `balanceWord`, `balanceTone`, `balanceLabel` from
`shared/vocabulary/balancePresentation.ts`, below every feature that draws the bar, and `levelRow`,
this feature's own (`components/levelRow.ts`); all four were Play's until #574 — because three
copies of §B9's breaks is where one becomes `>`. **The forecast block is absent entirely when the pairing carries no
forecast, and nothing says why** (ADR-0161 §4, #410's decision): somebody unrated, a refusal, the
read in flight or failed all draw the same nothing, the stake tiles go with the block, and a
provisional figure — never served on a game today — is folded to the same absence in the mapper
rather than drawn without its caveat. Under the figure the sentence says what a confirmed score
**does**: _A counted game — a confirmed score moves everybody's level._ / _A friendly — nothing
moves._ — `worthLine`'s fact in the forecast's register rather than that sentence again four cards
apart — and the tiles are `If you win` / `If you lose`, **two or none**, the win tile tinted mint
on the design's word (7.14 as amended, Part 16), drawn by a placer of its own (`StakeTiles`, in
`shared/ui` since #839) over the shared `StatBox` because Play's `StakeBoxes` names a mode a game
has already answered and refuses a doubles court a game has already filled. **The players card is
always drawn** — its rows are the
court's seats and the Level under each is what the pairing adds — **your side first, you first**
(`courtForReader`, the one re-ordering this feature makes), the whole handle with `(you)` after
yours, the level row as §6.4 spells it plus `{n}% sure`, nothing under an unrated seat, **no chip
on anybody**, the face off the room join at the Chats row's 38 (7.19, the first people list in the
system). **Tap, not hold**: the whole row is a `button` named for the record it opens, dimmed on
press, opening `PlayerRecordSheet` for that player with the sport and nothing else — no search
stands behind this screen — and the footer says _tap_ because #285's argument against the hold is
honoured rather than reversed: the route the hold never offered is the one that exists.
`gamePlan.test.tsx`'s refusal is inverted: the plan lead draws both blocks, and the score lead
still draws neither and never asks.

**A seat can be open, and the game survives it** ([#418](https://github.com/Raketa02/Raketa/issues/418),
[ADR-0162](../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
`GameSeat.playerId` is optional — absent on a seat somebody left and nobody has filled — and
`openSeats` in `domain/game.ts` is the one definition of _open_ that the card, the screen's acts
and the spoken label read. **_We played_ is withheld while a seat is open**, and it is the
domain's answer rather than the screen's: the `awaiting-entry` arm folds `seatOpen` off the court,
and `actsOffered` returns no `enter` while it is true, because the server refuses a result on a
short court and a game with a gap in it is not one anybody could have played. Nothing else on the
arm changes — the score lead cannot be reached with an open seat, since the rung outranks the
clock. **The players card draws the seat as an `Open seat` row** — an empty face (`SeatFace`'s
`empty` occupant under Play's dashed ring, the same drawing the Now card's court uses), the words
where the handle would be, no level row (the pairing names whoever holds a rating, and nobody
holds this seat), and **not a button**, because there is no record to open for nobody; it is one
plain element named by its own words, in the reader's order like the rest. **The forecast block
is absent because the pairing omits it** — #416 serves no forecast, split or stakes while a seat
is open, and the block is drawn off the pairing alone; nothing special-cases the seat, and
`gameScreenPlanLead.test.tsx` walks the whole composition to say so. `othersOn` skips an open
seat — a sentence _with X and Y_ names the people on the court, never a `?` for the gap — and
`RatedSeat` admits the absence structurally, though no card is ever open on such a court. **The
screen gains a fourth slot, `courtActs`**, drawn last on the plan lead under _We played_ and stood
down with the doors while the grid is open: the acts on the court itself — _Leave this game_,
and #419's fill and call-off — every one a **challenge** act reached from a game, so the control
and its words are that feature's and the composer hands them in, exactly as the plan is handed
in. Whether one is drawn at all is the composer's rule, read off the plan this screen may not
know. **`CALLED_OFF` joins `GameStanding`** as the fourth end
([ADR-0163](../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)) — the `Exact`
assertion demands it — with a `called-off` arm that offers nothing, titled _It was called off_
over the gloss _Called off_ — the two words #419 §3 and ADR-0163 fix — and no body, because
nothing is invented beside them. Its `called_off_at`, its shelf life and its screen are #419's.

**The fourth end is dated, and drawn as the ghost is**
([#419](https://github.com/Raketa02/Raketa/issues/419),
[ADR-0163](../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). `Game` gains
`calledOffAt` and the mapper reads `called_off_at` — the act's own instant, present exactly on
`CALLED_OFF`, and what the card is shelved from one feature over. The `called-off` arm gains the
ghost's own body — _Nobody is marked for that. Not you, not any of the others._ — because it is the
same fact about the same people: neither an evening nor a game that never happened, so nothing
anybody is measured on moves, and a screen that said only the title would leave the reader to
wonder whether calling it off cost them. Everything else falls out of the arm being an ending:
no plan, no doors, no act on the court, the pairing not asked for (`usePairing` is enabled on
`AWAITING_ENTRY` alone, and the composition mounts `CourtPairing` on the plan lead alone), and the
star section as for any ending. Nobody is named — `called_off_by` is on no wire. **`seatedOthers`
joins `openSeats` on `types.ts`**: everybody in a seat but the reader, by id and in the court's
order — what the fill is told about the court it completes, and why it is read off the game rather
than the challenge is `challenges.md`'s to say.

**The score grid is the landing for _Needs result_ alone**
(ADR-0166). The _Today_ rung
is gone — the decision and its reasons were recorded in the old loop's `plans` record, whose ladder
it was and which left with it in #576 — so `entryLeadOf` lands a game on its own day on **the plan**, with _We played_ the quiet door
beneath _Open the chat_, and on the grid only once the agreed point has passed. Nothing in this
feature changed but the sentence: `EntryLead` is still derived from the card's door, _We played_
is still offered on every entry arm, and the two-arm docstrings now name one score-led rung.

**Who called it off, the ending block, and the card's dismissal**
([#454](https://github.com/Raketa02/Raketa/issues/454), [ADR-0172](../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§4–§5, §8). `called_off_by` is mapped onto `Game.calledOffBy` — the id and the whole name, because
the leaver's seat is vacated and the court cannot supply it — and the `called-off` arm of
`ResultArgument` gains `ending`: who (`you` for the reader's own press), **how** — a departure is
told from a press by whether that player still holds a seat, and no second field says which — and
the court's format. `resultTitle` and `resultBody` write §8's table from it: _The game was called
off for lack of players_ over _{name} left, so the singles game is called off…_ or _{name} was
the last to leave, so the doubles game is called off…_; _{name} called the game off_ (_You called
the game off_) over the ghost's own body. `IT_WAS_CALLED_OFF` stands for a reply that names nobody,
which the wire promises not to send. The standing line and the card's gloss stay the one word,
_Called off_. **The dismissal** is this feature's act — `POST /games/{id}/dismissal`, a `204`,
`dismissGame`, `useDismissGame` — and the one write here whose reply is written into the list:
`GET /games` omits a game its reader has dismissed, so a list without it is the next read's
answer one round trip early, then the list is re-read; a refusal re-reads and says nothing, because
the fold the re-read lands on is the answer. `RemoveCard` is the control — Feather `trash-2`,
spoken _Remove this card_, on `ChatDoor`'s shape — exported for `features/plans`' card and drawn
nowhere else. **Not seen on a device.**

**The dismissal clears the row too, and the hour's ending names nobody** (ADR-0173, [ADR-0175](../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)).
`useDismissGame`'s cache effect touches two lists since ADR-0173 — the card through
`dropCardOfGame`, the row through `challenges`' `dropCourtOfGame` — and `dropCardOfGame` is
exported as the one write the games list lets another feature make, for the row's own door.
**The press is gone** (ADR-0175 §1): `CalledOffEnding` is a departure, named, or `the-hour`,
which names nobody — `called_off_by` null is the platform's act and no longer a broken promise,
so `IT_WAS_CALLED_OFF` and `calledTheGameOff` are retired and the ending's heading is
`CALLED_OFF_FOR_LACK_OF_PLAYERS` alone, over a body that names the leaver or says _Nobody
filled the seat in time_. A record naming somebody still seated folds as a departure. **The
screen draws one act**: `GameScreen`'s `courtActs` slot became `fill`, drawn directly under the
card on the plan lead and stood down with the doors while the grid is open; `OpenTheChat` is
gone from the screen, and with it this feature's reach into `features/conversations` — the
seam ADR-0149 §3 named is back to its one importer.

**`awaitsYourAgreement` — a score waiting on you**
([#550](https://github.com/Raketa02/Raketa/issues/550)). Home's badge counts _a result to confirm_,
and `features/plans`, which counts the cards, cannot tell from _Confirm the result_ whether the arm
waits on the reader. So this feature answers it, beside `resultArgument`: a score waits on your
agreement exactly when agreeing is an act the screen would offer you — the other side's score up and
unanswered, or two scores standing with nobody agreed. Your own score waiting on them does not, and
neither does an agreement running out its grace. Read off `actsOffered`, so the badge and the screen
cannot disagree about a state; what crosses is the boolean, never the argument.

**`GameForecast` — the forecast block alone** ([#556](https://github.com/Raketa02/Raketa/issues/556)).
A booked game's details draw their own people, with _paid_ on each, so they take this feature's
forecast without the players card: the same `usePairing` read of the Game the booking opened and the
same `ForecastBlock`, absent on the same ground. **The block and its stake tiles are `shared/ui`'s
since [#839](https://github.com/Raketa02/Raketa/issues/839)** — a competitive game's details open on
them too, and ADR-0207 §6 moved them below both features — and so are their words (`BALANCE_FORECAST`,
`GAP_WORD`, the
counted sentence, `WIN_TILE` / `LOSE_TILE`, and the three spoken names), in
`shared/vocabulary/forecastPresentation.ts`. This feature draws them unchanged: `gamePresentation`
cites the words, kept the friendly's sentence (`forecastSentence`) until #841 retired it with the
block on For fun (below), and hands the block its own read. And a booked game's result is told on `GameScreen`
itself, composed by `proposals` with the score leading and the `card`, `court`, `plan` and `fill`
slots empty — a booking is its own plan, and a seat open on one is a rescue (#557).

**`GamePairingCard` — the pairing's card, the kind's own**
([#841](https://github.com/Raketa02/Raketa/issues/841); ADR-0207 §5, §6, §12; the backend's #835).
`GameForecast` was renamed for what it now draws: **a For-fun game's Social vibe card where _A
friendly — nothing moves._ stood**, and a competitive game's forecast and stakes as before, so a
For-fun game reads the same before and after it is booked. The pairing carries **`vibe`** on a
`FRIENDLY` game — the court's number, and a row for each of the reader's tags naming who on the
court carries it, in the reader's direction — and **the forecast too, for the apps already on
phones**. Both cross the mapper; **the kind decides the card** (`pairingCardOf`, `domain/pairing.ts`),
never which blocks arrived: `FRIENDLY` draws the vibe or nothing, the forecast ignored; any other kind
draws the forecast or nothing, a vibe ignored; a kind this build cannot read keeps the forecast it
drew before. A tag code this build can't name is left off its rows (ADR-0207 §7), as the details'
mapper does. **The columns are handed in** (`columns`): `proposals` gives the people as its tiles
stand, you first, with the faces the booking carries — this feature's seats hold neither that order
nor a photograph — and the dots and the shared bands are this feature's, off the carriers. The card
is `shared/ui`'s `SocialVibeCard`, the one a game still filling opens on (#840). **The friendly's
sentence is retired** with the block it stood under: `forecastSentence` says the counted sentence or
nothing. **Live**: `gameKeys.pairings()` roots every game's pairing, and a tag save marks it stale
(`player_profile`'s `useChangeSocialTags`, beside the deck and the details), never re-read under the
edit. **_The game at the court_ is the booked details at the game's hour**: the result screen
_Who's here_ opens leaves its `court` slot empty, as it has since #576, so the card is drawn where
the forecast was and no wider (ADR-0207 §5). Walked in `proposals`' `bookedForFunGame.test.tsx`;
`forecastBlock.test.tsx` asserts a friendly draws no forecast, sentence or tile.

**`STARTED_SHORT` — a booked game whose hour came with a seat open**
([#557](https://github.com/Raketa02/Raketa/issues/557); the backend's #544; the Games & Fill in
mechanics §14.1). Somebody left after the club's cut-off and nobody took the seat: the game takes no
result, no Level moves and nobody who stayed is marked for it. It joins `GameStanding` as its own
end — `resultArgument`'s `started-short`, titled _No result_, its standing line _A seat was empty._,
offering nothing — and the Classic card names it _uncounted_. A booked game is Home's card, so the
arm is reached only by a link straight to the Game; Home itself says _Uncounted · a seat was empty_.

**A booked game's result can say somebody didn't come, and the player marked can say they came**
([#560](https://github.com/Raketa02/Raketa/issues/560); the backend's #547; the Games & Fill in
mechanics §15.3). `NO_SHOW_REPORTED` and `NO_SHOW` join `GameStanding`, and `Game.noShows` carries
each report — who, whole name, `reportedAt`, `disputeBy`, `disputedAt` — but never who made it: the
report is the game's. **Two arms**: `no-show-reported` holds the reader's own mark (`yours`) and
everybody else's (`others`), each a `NoShowMark` — the glossary's verb, _the players who came marking
one who didn't_ — whose `state` the domain folds: `open` while it is undisputed and `readAt` is still
before its `disputeBy` (two of the server's instants, never this phone's clock: the backend's
`may_dispute` asked of the moment the list was folded), `disputed`, or `stood`. So no sentence
compares instants. `no-show`'s `didNotCome` is the reports nobody disputed. `ResultAct` gains
`dispute`, _I was there_, offered on an `open` mark of your own and pinned as the `primary` over the
clock of your day; it is never an editing act. **Marking is not a `ResultAct`**: it is an act per
person, offered beside the entry rather than instead of it, so `domain/noShows.ts`' `noShowRows`
folds the rows of the _Didn't come?_ block — every other player on the court in its order, on the
entry arm with the court whole and on `no-show-reported` for a reader nobody marked, so the second
player who did not come to a doubles game can be marked after the first. **Which game is booked is
the booking's**, so `GameScreen` takes an optional `booked` (`BookedFacts`: a `reread` of the
booking's own reads that this feature cannot name); a Classic game has no block because nobody hands
one in. **A row presses and a sheet decides** (`NoShowSheet`, the
leave sheet's shape: _Before you say so_, three lines, _Don't mark anybody_) — the mark, if it
stands, is the strongest thing on a record — and focus goes back to the row pressed. Confirming puts
the sheet away and the mark happens on the row, busy there, a refusal said in the pinned footer with
the screen's other acts: `gameErrorMessage` gains the two routes' codes, and a mark's own refusals
(`markErrorMessage`) say a mark came too late where the score's sentence would say the evening went
unrecorded — the rows outlive the entry window, which is off the wire once a report is made. **A new
act clears the last one's refusal**, so the footer's one sentence is about the act just taken. The
writes are `useReportNoShow` / `useDisputeNoShow`: invalidate, never optimistic, pause offline, the
answer dropped for `stateResult`'s reason. On a booked game the entry's body no longer says _no
booking, no calendar_ — it says a score records how it went, or to say below that somebody didn't
come. **Every write on a booked game's result re-reads Home and the booking** — the score and the
agreement too, which before #560 left Home's status and badge stale until the next refetch: the four
hooks take an `AfterAWrite` and run its `reread` from the mutation, so a write that waited out a lost
connection still re-reads after the screen has gone. A game whose every report was disputed is the
backend's `UNSCORED` and reads as today's evening. **Not seen on a device.**

**The old loop's game screen, its card and its dismissal left** ([#576](https://github.com/Raketa02/Raketa/issues/576)).
The `/games/[id]` route and `GAME_ROUTE`, the players card and `CourtPairing` (with `levelRow`, the
row's words and `courtForReader`), the dismissal (`dismissGame`, `useDismissGame`, `RemoveCard`,
`dropCardOfGame`), `awaitsYourAgreement` and `seatedOthers` went with the old loop's rail, cards and
challenge screen they served, and so did this feature's edge into `player_record`. **`GameScreen`
stays** — a booked game's result screen mounts it, on the score lead with its other slots empty —
and so do `GameForecast` (`GamePairingCard` since #841) and the result writes. `result.test.tsx` and `forecastBlock.test.tsx` walk
the booked routes now (`/booking/[id]/result` and the details), with the same assertions. **The
plan lead, the `card`, `court`, `plan` and `fill` slots and `entryLead` are still on the screen**
and nothing fills them: simplifying the screen to the one lead it now has is left for a ticket of
its own rather than folded into a removal.

**`Game` no longer carries `challengeId`** ([#577](https://github.com/Raketa02/Raketa/issues/577)).
It had no reader, and on a booked game it was the booking's id under the old loop's name; the wire's
`GameSchema` still spells it `challenge_id` until the backend's removal reaches it. The record is
[`conversations.md`](conversations.md), whose join to a booked game's room moved onto the booking in
the same ticket.

**Every other player on the court can be marked** ([#653](https://github.com/Raketa02/Raketa/issues/653);
ADR-0195). Nobody at the club checks anybody in now, so `noShowRows` takes no check-ins. A row no
longer reads _Inés Díaz · checked in at the club_ with nothing to press (`checkedInLine` is
deleted), and `BookedFacts` carries only the `reread`. `gameErrorMessage` loses
`checked_in_at_the_club`, which the backend no longer raises. The record is
[`proposals.md`](proposals.md), where the booking stopped carrying the desk's word.

**The result screen tells the truth: silence costs nothing, _That's right_ settles at once, For
fun asks nothing** ([#656](https://github.com/Raketa02/Raketa/issues/656); ADR-0195 §2, §5, Q114,
Q119; the backend's #654 and #655). Four things moved, each because the rule under it did.
**_Is that right?_ names the moment and says silence is free.** The standing line says when silence
makes the score the result, on the club's clock — _tomek.p put a score up. If neither of you answers,
it becomes the result at 20:30 on Wednesday._, _if you don't answer_ in singles (`theirs-stands`
carries `withPartner`), _at 20:30 today_ on the read's own day, and no clause at all for an instant
it cannot read — and the clock under it says _Saying nothing costs nothing._ The screen said _there
is no penalty_ over a silence that cost a miss on _Answers about results_; ADR-0195 made silence
free, and nothing on these screens talks about penalties now. The rule this record kept since #314 —
_there is no absolute time anywhere_ — is reversed for the moment a score settles: a booked game has
a calendar, the story names the moment, and the platform zone's clock (`shared/date/platformZone`)
is the one every booked hour in the app is drawn on. Two scores say when they settle too, at the
later one's `answer_by`, and what each ending is. **The agreement is not a state any more.** #654
retired the six-hour grace, so the wire carries no `acceptance` and no `settles_at`: the `agreed`
arm, `StandingAgreement`, its _Agreed — settling_ title and clock, and the refusals
`the_other_side_has_answered` and `the_result_is_already_accepted` are deleted, and _That's right_
reads back as the game `CONFIRMED` — _The result_ over _Counted._, since an agreement, silence and
the closer of two scores naming one winner all end there and the wire does not say which, so
nothing calls the score _agreed_ (`SCORE_LEAD.result`, `worthLine`'s _its result_). **Two new ends,
and one corrected.** `PLAYED_NO_SCORE` replaces `NEVER_PLAYED` — _Played · no score_, a full court
nobody recorded, played for everybody, with nothing said about marks: _Never played_ said _Nobody
is marked for that_ over a record that marked all four, and the window's refusal said it too — and `DISPUTED` joins — _Disputed_, _The two
scores named different winners._, and why: Rakieta doesn't decide who won. Both end on the fact list
`UNSCORED_FACTS` became, `EVENING_FACTS` (`endsAsAnEvening`), with `unscored`, whose body said _nobody wrote a score
down_ — false of the two-score games it used to cover — and now says what reaches it since #654: the
game everybody marked as not coming said they came to. The worth line is said only where a score is
up or stands (`saysWhatItIsWorth`), never over an ending that took none — which also takes it off
the called-off, started-short and no-show endings, where _its result becomes part of your record_
was never true. The screen's classifications of the argument are the deck's exhaustive switches
(`saysWhatItIsWorth`, `endsAsAnEvening`, `settledScore`), not ad-hoc tests in `GameScreen`. **For fun asks nothing.** A
`FRIENDLY` game is one arm, `for-fun`, before its score and after: _Played_, no _How did it go?_, no
_Is that right?_, no clock; the grid is the screen until a score is up, under _You can add the score
if you like, up to a day after the game. It stands as you put it — nobody is asked to agree, and no
Level moves._ — reached only by the details' _Add the score_, so the grid is what was asked for —
and the score reads _The score_ once it stands. Across an open seat the body offers nothing. The _Didn't come?_ rows are offered wherever a first score may go
in (`actsOffered`), on it as on the entry, until attendance replaces them (#658). **The entry asks _How did it go?_** (§15.2), and its standing line
counts down to putting a score up rather than to a game that never happened; the entry draws no
clock, and `clockLine` is the one place that says which arms count down. **Refusals in plain sentences**: a score
before the hour (`the_game_has_not_started`, its own sentence for a score; a mark keeps _The game
hasn't started yet._), a correction after the entry window (`corrections_have_closed`), and the
one-score-per-side race, which a partner's counter can cause as well as the other side's score.
**Not seen on a device.**

**Who's here, caught at the court — attendance replaces the no-show report**
([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3; the backend's #657). `gen:api`
brought #657's wire: `GameSchema.no_shows` became `attendance` — one row per player somebody tapped,
`AttendanceState` (`WAITING`, `ON_TIME`, `CAME_LATE`, `DIDNT_COME`, `CLAIMED`, `CONFIRMED`, held
equal in `wireVocabulary.ts`) with `notedAt`, `arriveBy`, `arrivedAt`, `claimBy`, `claimedAt` and
`confirmedAt`, and never who tapped. `GameStanding` gains `NOT_HERE_YET` and `DIDNT_COME` and loses
`NO_SHOW_REPORTED`, `NO_SHOW` and `UNSCORED`; a state this build cannot read keeps its row and says
nothing of it. **Two arms replace three**: `not-here-yet` (who is awaited, who the game waits
with, whether the reader is one of them, and `arriveBy`) — _Are you here?_ over _Ivan Petrov is
waiting for you._ to the player awaited, _Not here yet_ over _Waiting for Oscar Nowak._ to everybody
else, each with the half hour on the clock — and `didnt-come` (who didn't come, and the reader's own
as `may-claim`, `claimed` or `final` off `claimBy` against `readAt`) — _Were you there?_ with its day
on the clock while _I was there_ may be said, _Didn't come_ otherwise. Neither offers a score act,
neither is an evening (`endsAsAnEvening`), and `ResultAct` is about scores alone again: `dispute`
left it. **The taps are `domain/attendance.ts`'s** — `attendanceBlock(game, reader, hour)`, the
rows of the _Who's here_ block (`WhosHere`) in the court's order: _Oscar Nowak isn't here yet_ for
everybody nobody has tapped and _Oscar Nowak is here_ for anybody awaited, while the first half
hour runs and the standing takes a tap (`AWAITING_ENTRY`, `AWAITING_ANSWER`, `NOT_HERE_YET` — a
waiting score stops no tap) and the reader is not away themselves; afterwards _Oscar Nowak says
they were there_ with _Yes, Oscar Nowak was here_ while the claim's day runs; and _came late_ beside
anybody who did, the reader too. On time vanishes, and a Didn't come is the standing line's. **The
reader's own act is pinned**, the `primary` where the score's send is: _I'm here_ while they are
awaited, _I was there_ while they didn't come and their day runs. **One press, and no sheet**: the
tap costs its maker nothing and an arrival lifts it, so #560's _Before you say so_ sheet,
`NoShowBlock`, `noShowRows`, `markErrorMessage` and the no-show writes are deleted. **The block sits
above the grid**, under the body: in the first half hour it is what a player at the court opens the
screen for, and the grid is the screen from the hour's start. **The position is read at the tap
and kept by nobody** — `useAttendance.ts`: the two writes made at the club ask for the permission
where asking achieves something (`ensurePermission`), read one precise fix through the location
port's new `readPreciseFix` (`Accuracy.High`; the area's `readFix` stays `Balanced`), and hand it
straight to the request **inside the mutation**, so it is never a mutation's variables and the
cache never holds it. A refused permission, one blocked for good (with _Open Settings_ beside the
sentence) and a phone that produced no fix are `LocationAtTheTap`, said in the footer like a refusal;
the backend's `not_at_the_club` reads _You can say so only from Bonarka Arena._ with the booking's
club — **unless the fix was rougher than the check allows for** (`isRoughFix`, wider than the
backend's 200 m), which is the likeliest reason a player standing there hears it (iOS with Precise
Location off, Android's approximate location; expo-location reports the granted accuracy on
Android only), so that one says the phone could tell only roughly where it is, with _Open
Settings_. The backend still decides; the phone only picks the sentence. The precise read is
bounded (`PRECISE_FIX_WITHIN_MS`, 15 s): an arrival is dated when it lands, so a GPS that never
settles indoors answers no fix rather than holding the tap. `BookedFacts` gains `startsAt` and `club` for these. **Those two are made online or not at
all** (`networkMode: 'always'`): when an arrival lands decides what it was, so a tap is never
queued to the next reconnect, and with no connection it says _This can't be sent until you're
back._ The claim and its confirmation carry no position and pause like every other write. Every
refusal the four routes make has a sentence (`attendanceErrorMessage`, keyed by the act where one
code means two things), and the score's own refusals gain `somebody_is_not_here_yet` and
`somebody_did_not_come`. **The permission text changed with it** (`app.config.ts`'s
`locationWhenInUsePermission`): _Rakieta uses your location to set the area you play in and, when
you say who's at a game, to check you're at the club._ It is native configuration — the iOS
prompt's Info.plist string — so **it needs a new build** to reach a phone; a development build made
before this change still shows the old sentence. **Not seen on a device.**

**Calls made here, open for the product owner**:

- **The first half hour is measured on the phone before anybody is tapped.** `GameSchema` carries
  no hour and no window, so `tapsAreOpen` reads the booking's `startsAt` plus 30 minutes against
  `readAt` — a copy of the backend's `TAP_WINDOW`. A list read in the window and still on screen
  after it offers a tap the backend refuses as `the_tap_window_has_closed`, which is said.
- **The awaited player reads everybody the game waits with** (_Piotr Sowa, Inés Díaz and Bartek Lis
  are waiting for you_), because who tapped is on no wire; in singles that is the one person who
  could have. The push (#663/#664) names the tapper.
- **A platform that states no accuracy sends `accuracy_m: 0`** — no allowance claimed, the fix
  measured as it stands — rather than inventing a radius.
- **A row's tap and its line are both drawn for a late claim** (_Oscar Nowak says they were there_
  over _Yes, Oscar Nowak was here_); an awaited player reads others awaited as a line, with nothing
  to press.

**Every seat, line and tap names the nickname** ([#728](https://github.com/Raketa02/Raketa/issues/728), [ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). A game's seats, its attendance
rows and who called it off read the wire's `nickname`, so the court's eyebrow, the bar, the result
screen's sentences, _oscar.n isn't here yet_ and the late claim's line say the whole nickname,
never with an @. The stems on the bar cut at the first dot.

**PLAYED WITH has a slot on the result screen** ([#754](https://github.com/Raketa02/Raketa/issues/754);
the friends screens §3). `GameScreen` takes `playedWith`, a `ReactNode` it draws on every arm just
above _How were they?_ — under everything about the score, and over the question about how they were.
It is filled by `proposals`' `BookedGameResult` with `friends`' card, and this feature knows nothing
about it but where it stands. The record is [`friends.md`](friends.md).
