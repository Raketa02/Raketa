# ADR-0162 — A game's line-up is frozen until somebody leaves it

- **Status:** Accepted — **three sentences superseded 2026-09-13 by ADR-0165**: §1's *a court that
  has been a game — `ON`, or reopened since and not yet re-seated* (a yes can be taken back
  before the court is whole), §1's
  *a challenge folds `game_opened` off `SeatLeft`* (it folds it off the line-up completing), and
  §1's and §9's *the last person may leave too … and it lapses into Never played* (the departure
  that leaves one on a game calls it off). §2–§8 stand — **§2's title narrowed 2026-09-15 by
  [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §1**
  to *by its seats alone*: a court that has been a game still reaches no ending from its seats,
  and it **ends with its game**, by either act that calls the game off, recorded on the challenge
  as `CALLED_OFF` in the transaction that tells the game.
- **Date:** 2026-09-12
- **Supersedes, by named sentence:**
  [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) §2's
  *"`ON` has become a game, and ending the challenge would not touch it"* — the **departure**
  half: a player may now leave a game that has not happened, and the leaving lands on the
  challenge and reaches the game. The **withdraw** half is
  [#417](https://github.com/Raketa02/Raketa/issues/417)'s and is refused here until then.
  [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §7's *"the game's
  frozen line-up after"*: membership after the line-up completes is the game's **current**
  line-up. [ADR-0141](0141-a-game-names-its-court-and-the-court-is-the-gate.md) §2's *"a seat
  cannot be dropped without publishing a three-person doubles game"*: a seat can be **open**,
  and it is still never dropped — the record is honoured by drawing the seat empty.
  ADR-0150 §1's
  *"a court they can neither complete nor leave"*: leaving is an act.
- **Amends** [ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
  §4: `SEAT_LEFT` carries a **third** `departure`, `LEFT`, and *the day a seat can be released,
  the contract does not move* is that day — `people` already names the actor and nothing on the
  wire moves. **Amends** [ADR-0143](0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
  §8 in one sentence: the pair rule releases the moment a seat leaves, and a *left* seat is a
  seat that left — consistent, said so here.
- **Cites** ADR-0142 §3 for the durable names below, and
  ADR-0145 §4 for why no
  arrow moves.
- Settles [#416](https://github.com/Raketa02/Raketa/issues/416), the first child of
  [#411](https://github.com/Raketa02/Raketa/issues/411); the author's decision, grilled 2026-09-11.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** `challenges`, the Plan and their ports are gone, so the departure on the challenge (§1), the fold (§2), the moment guard (§4), the `SEAT_LEFT` line (§5), the fill and pool (§6), `late_change_threshold` (§8) and §9 describe nothing. §3 survives on a booked game: a seat can be open, and it is drawn, never dropped. `Game.vacate` writes `SeatVacated` when a player leaves through `bookings`, and a rescue taking the seat writes `LineUpReseated` through `Game.take_seat`. A result is refused while a seat is open, every reader — the room's membership included — reads the current line-up, neither event reaches the room, and `planned_at` never moves.

## Context

**A game exists only once the last seat accepts, and nobody can leave it afterwards.** That
sentence is true four times over in the code: an accepted seat cannot decline
(`_answerable_seat` raises `TheSeatIsAlreadyAnswered`), a challenge that reached `ON` cannot be
withdrawn (ADR-0142 §2), the game has no leave event of any kind (six events, every one an act
on a result), and `lineup.py` says it in words — *the line-up is settled at the plan and never
afterwards*. Two records name the consequence as a failure rather than a property: ADR-0142's
Context — *the acceptor cannot leave … and the organiser has no act at all* — and ADR-0150 §1,
which calls a court a member *can neither complete nor leave* the stated failure.

The author decided that people do drop out of games they agreed to, and that the product should
let them — with the others keeping what they agreed rather than starting over
(#411, the nine rules). This record is the backend half of the first three of those rules: who
may leave and until when; that the game survives; that the same court is filled the way a
half-built one is filled today, and the **same** game is re-seated.

### What already exists, and why the act lands where it does

Everything a half-built line-up has, a reopened court gets for free, **provided the seat that
reopens is the challenge's.** The fill is `POST /challenges/{id}/seats` by any live member; its
pool is `POST /lineups` with `completing_challenge_id`, through `HalfBuiltCourtQuery`; the
newcomer's *I'm in* is `POST /challenges/{id}/accept`; the line-up completing hands over to
`games` inline through `PlannedGameOpening`; `already_asked_at` keeps the departed out of this
court's pool; `SEAT_LEFT` is the room's line and `people` already resolves an actor who is no
longer a member; the pair rule already holds while a challenge is `ARRANGING` and releases the
moment a seat leaves. Every one of those is keyed on the **challenge's seats**. A leave modelled
on the game — a `Game.leave` with the challenge told afterwards — would put the fill, the pool,
the pair rule and the room's line on the wrong record, and every one of them would need a second
author.

So the act lands on the challenge, and the game is **told**, in the transaction — the shape the
opening already takes (`docs/adr/0137`, `planned_game.py`: *inline, and never through the
outbox*, because the player who taps is told by a screen that cannot yet show it otherwise).
The arrows stay exactly as `.importlinter` holds them: `challenges → games`, `plans → games`,
and `games` imports neither the Plan nor the matcher.

### The three things the obvious shape gets wrong

**The fold ends a court the organiser is alone on.** `standing_of`'s second rung — *is anybody
but the organiser still in it?* — folds the organiser alone among open seats to `LAPSED`,
because *the organiser alone on an empty court is indistinguishable from never having sent*.
On a reopened singles court that is exactly wrong: the opponent left, the organiser is alone,
and what stands is a **game** with a plan, a room and a record — #411 rule 9, *a two does not
end itself*. And the fact cannot be read off the seats: a re-seat gives the departed's position
to the newcomer, so a court whose newcomer then declines has no seat left that says *this was
once a game*. The fold needs one more fact than the seats hold.

**A seating with nobody in it has no code, and the line-up refuses it.** `Seating` requires
both fields; `LineUp.__post_init__` refuses a side with nobody on it; `GamePlanned.seatings` is
the only seat fact on a game. ADR-0141 §2 argued from the same shape: *a seat cannot be dropped
without publishing a three-person doubles game.* The argument was right and the conclusion was
too narrow. A seat that is **open** is not dropped — it is drawn, empty, in its place, so the
court still says which side is short and a four with one seat open is still a four.

**The moment is the plan's, and `games` cannot read a plan.** #411 rule 1: once the agreed
moment has passed, the game is *Needs result* and leaving means nothing — refused, so a no-show
cannot vacate a seat to block the result. Rule 3: no fill and no acceptance once the moment has
passed either, because a newcomer accepting into *Sunday* on Monday joins a game whose moment is
gone. The moment is `agreed_point` (ADR-0145 §3 — both slots the agreed instant, the day alone
the start of the following local day, no day nothing at all) and it is computed in `plans`
and nowhere else. ADR-0145 §4 fences `games` from the Plan and says why in a sentence this record
must not break: *if `games` ever imports the Plan, this clause has been broken.*

## Decision

### 1. `POST /challenges/{id}/departure` — the act, on the challenge, in ADR-0142 §4's noun shape

> **Three sentences below are superseded 2026-09-13 by ADR-0165.** *A court that has been a game — `ON`, or
> reopened since and not yet re-seated* — the departure is admitted on a half-built court too, because *leaving a
> half-built court is a decline, and it is already given* is true before you answer and false
> after (§1 there). *A challenge folds `game_opened` off it* — it folds it off the acceptance that
> completes the line-up, since a `SeatLeft` no longer implies a court that was `ON` (§2 there).
> *The last person may leave too … and it lapses into Never played* — the departure that leaves
> at most one player on a game, with nobody still deciding, calls it off in the same transaction
> (§3 there). The event, its shape, the seat it writes, the pool and the pair rule stand.

No body; answers `ChallengeSchema` as the court now stands. **Whose act, asked first**: the
caller holds an **accepted** seat, and otherwise the refusal is `404 challenge_not_found` —
`challenge_of_yours`' one code for two cases, extended to a third. Somebody whose seat is
awaiting, declined, lapsed or already left is told what a stranger is told, because a
departure is the one act here whose refusal must not confirm to a person that they *were* on
this court a moment ago. Then the caller's own hold, `403 account_held`, on ADR-0148 §9's rule
that a hold stops you writing anywhere another player sees it — a departure writes a line into a
room. Then the standing: **a court that has been a game** — `ON`, or reopened since and not
yet re-seated, because two people may leave and the court the second one leaves is already
half built. `409 not_a_game_yet` for a court that never was one — leaving a half-built court is
a *decline*, and it is already given — and `409 challenge_is_over` for the three endings. Then
the moment guard (§4).

**The record is a fourth `SeatAnswer`, `LEFT`, written by a new event, `SeatLeft(challenge_id,
player_id, occurred_at)`, on an accepted seat.** The occupant stays on the seat with the answer
that emptied it, as a decliner and a lapser do: *who said no, who said nothing* and now *who
left* are three facts a strand may one day price apart (§8), and a seat that forgot which one
happened could not tell them. `Seat.is_open_at` reads `LEFT` as open; `already_asked_at`
includes the departed, so the fill's pool leaves them out and `NobodyIsAskedTwice` stays a
backstop; `players_in_it_at` excludes them, so the pair rule releases them on the instant.
**Two departures leave two seats open.** The last person may leave too — a court everybody has
left is a game nobody is in, and it lapses into *Never played* when its window closes (§9).

`SeatLeft` passes ADR-0142 §3's test **without needing the exemption**: it is about a seat and
carries a player, like an acceptance, and the fold reads it as it reads a decline. What the
event *does* carry that no seat fact could is the one bit the Context named: a `SeatLeft` can
only have been written on a court that was `ON`, so **a challenge folds `game_opened` off it** —
the one fact about a challenge, beside `withdrawn_at`, that is not in its seats. Nothing
announces `ON`; nothing here does either. The event says somebody left, and what the fold
learns from that is what it was already entitled to know.

`challenges.seat_left` joins the durable name list at version 1.

### 2. The fold: a court that has been a game does not end by its seats

`standing_of` takes `game_opened` beside `withdrawn`, stated by every caller and never
defaulted, and its second rung is skipped when it is set. A reopened court re-derives
`LINE_UP_INCOMPLETE` **with no change to the rungs that follow** — not awaiting, not all
accepted — which is the state the builder is re-entered from and the state the pair rule holds.
A fill takes it to `AWAITING_ANSWERS`; the newcomer's acceptance takes it back to `ON`; the same
game is re-seated (§3). There is no new standing, because there is no new question: *is this
court still being arranged* has the same three answers it had.

**The organiser is no longer a fixed point of the court.** `refuse_a_bad_court` demanded the
organiser hold a seat because *they are the one proposing*; once they have left, the court is
proposed by nobody and filled by whoever is still on it. On a fill, the organiser must hold a
seat exactly when they are still live — which is what *everybody live keeps their seat* already
says — so the organiser rule is asked only while they are in. ADR-0150 §1's *only the organiser
may withdraw* is untouched here and is the subject of #417's fallback.

**`has_become_a_game_at` answers `game_opened` or `ON`**, so the mutual mint's idempotence key
(ADR-0152 §4) keeps naming the game a reopened mutual-born court has rather than reading it as
never having minted one.

**Withdraw refuses a court that has been a game**, with the code it already has. ADR-0142 §2
holds withdraw to *the exit exists exactly where nothing else ends it*; a reopened court has an
exit this record does not build — calling the game off, which reaches the game's record and is
the whole of #417. Letting the organiser withdraw here would end the challenge and destroy the
room while the game went on standing, `AWAITING_ENTRY`, with an open seat and nobody to be told.
So `LINE_UP_INCOMPLETE` is the standing that gets the act, and a court that has been a game is
the one `LINE_UP_INCOMPLETE` that does not — until the act that touches the game exists.

> **That act exists, same day: [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md).**
> The withdraw reaches a reopened court and calls the game off in the same transaction; the
> organiser's fallback is decided there too. The paragraph above is kept as the reason the
> refusal was interim rather than as a rule.

> **And the court has an ending of its own, since 2026-09-15:
> [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §1.**
> This section's title holds for the seats: a court that has been a game still folds to no
> ending from them. It ends **with its game** — the departure that deserts it and *Call it off*
> each record `ChallengeCalledOff` in the transaction that tells the game — and reads
> `CALLED_OFF`, the seventh standing, rather than staying `LINE_UP_INCOMPLETE` after its game
> is over.

### 3. The game's line-up stops being frozen, and the same game is re-seated

**`Seating` admits an open seat** — `player_id: None` on a side, coded `A|` — and
`LineUp`'s invariant becomes *every seat present, occupied or open; nobody twice*. `players`,
`players_on`, `side_of` and `counterparts_of` answer about the occupied seats; `is_complete`
says whether any seat is open. **`SeatingSchema.player_id` becomes nullable** (`nickname`
already was): an open seat is drawn, never dropped, and the client folds *Needs a player* from
it. Nothing on the wire names the rung (ADR-0148 §6, ADR-0157: never announced).

**Two events, and each is an act nothing on the record implies.** `SeatVacated(game_id,
player_id, occurred_at)` is written by `Game.vacate`, called from a new `games` use case in the
departure's own transaction through the port `challenges` already holds. `LineUpReseated(game_id,
seatings, occurred_at)` is written by `Game.reseat` when a completed line-up arrives for a game
that exists **with an open seat**: the port that used to *fire exactly once per challenge* now
opens a game, re-seats one, or answers `None` for a court that stands whole — and the whole
arrangement travels, as `SeatsInvited` carries its whole court, because a re-seat may move an
accepted player across the net as well as fill the seat. Both pass ADR-0142 §3's test the way
`ChallengeWithdrawn` does: a departure is a decision no arrangement of the record could reach, and
so is the arrangement that replaces it. `games.seat_vacated` and `games.line_up_reseated` join
the durable name list at version 1. **`planned_at` does not move** — it keeps meaning *when it
became a game*, and ADR-0153's *the end never moves later* is what a re-seat that re-dated the
plan would break: the room's end and the entry window are both measured from it.

The port is renamed: `PlannedGameOpening` becomes **`PlannedGameHandover`**, because it now
hands over two things and *opening* named one of them. Its idempotence is kept — a second
completion for a game standing whole is `None`, and a departure for a seat already open is a
`games` refusal that rolls the departure back.

**A result is refused on a court with an open seat**, `409 the_court_has_an_open_seat`. #411
rule 5 withholds *We played* on the client while a seat is open, and the refusal is what makes
that a rule rather than a promise: a score on a three-person doubles game is a score with a side
the engine cannot price and a seat with no outcome to give anyone. The seat stays open until it
is filled, the game is called off (#417), or the entry window closes on it.

**Every downstream fold reads the current line-up.** `PlayedCourt.line_ups_of` — the room's
membership — drops the leaver and admits the newcomer, which is ADR-0146 §7 rewritten from
*frozen* to *current* and nothing else. `GameDirectory.playing` and every `GameHistoryQuery`
read answer about the people **on** the court: the leaver's `GET /games` no longer lists the
game, they are nobody's counterpart, nobody's attendee, and `outcome_for` an open seat is
`None`. `PlanningCourt.plannable_for` is unchanged in rule — an open seat does not freeze the
plan, and the newcomer may set a slot — and narrowed in one respect: the leaver is not on the
court, so the plan is not theirs to write. The pairing read (ADR-0161) **omits the forecast, the
split and the stakes while any seat is open**, and still names the Levels of the seats that are
filled: a forecast is a claim about a court, and this court is not yet the one that will play —
which is the absence ADR-0161 §4 reserved for the day a seat could be open, rather than a
provisional figure. `late_change_threshold` stays `None`, and its reason changes (§8).

### 4. The moment guard: `games` publishes it, `plans` answers half of it, `challenges` reads it

Three ports, one arrow each, and none of them moves an arrow.

- **`AgreedMoment`** is declared in `games`' own vocabulary — *when has this game been agreed
  for?* — and answered by an adapter in `plans/infrastructure/` over the Plan's own read. It is
  `games`' **demand**, contracted on `game_demands.py` beside `CourtPairing`; `games` imports
  nothing to ask it. This is `PlanningCourt`'s pattern run the other way: there `games`
  publishes and `plans`' use case reads; here `games` demands and `plans`' adapter signs.
  ADR-0145 §4's clause holds — `games` still imports nothing from the Plan and stores no moment —
  and ADR-0137's *no date field anywhere* is still exactly true of `games`' record: the moment is
  read at the guard and written nowhere.
- **`SeatableCourt`** is what `games` **publishes**, contracted on `games_demands.py`, and it is
  named for both halves: *may a seat on this challenge's court still be left or taken?* It
  answers about a challenge id, because that is the currency `challenges` holds, and it answers
  three ways: **admitted** — the game is `AWAITING_ENTRY` and its moment is ahead, or no moment
  is agreed; **`MOMENT_PASSED`**; and **`GAME_IS_HISTORY`** — the game has happened, or its
  window closed on silence. `None` for a challenge that opened no game. The standing is the
  repository's and the moment is `AgreedMoment`'s, and the guard is written once, here.
- **`SeatableGameQuery`** is the `challenges` demand, declared beside `SettledGameQuery` in
  `challenges`' own words and signed by an adapter in `challenges/infrastructure/` that reads
  `SeatableCourt`. The two spellings meet at the adapter, by name, the way the two `Side`s do.

**The departure, the fill and the acceptance all read it, and only on a court that has been a
game.** `409 game_moment_has_passed` and `409 game_is_history` are the two refusals, on all three
routes; `challenge_is_over` is kept for the challenge's own endings and is deliberately not
reused for a game that has happened, because the challenge is still `ON` and the client is
looking at a game screen. The guard is the aggregate's own refusal one layer up — `Game.vacate`
and `Game.reseat` refuse a game that is not `AWAITING_ENTRY` regardless — and the moment is
the one half of it the aggregate cannot hold.

**Folding `AgreedMoment` into `SeatableCourt` was considered and refused.** One port answering
both would be `plans`' adapter deciding what a game's standing is, or `games`' adapter reading
the Plan; the first is a second author of a standing and the second is the import ADR-0145 §4
fences. Two ports cost a second Protocol and buy the arrow.

### 5. The room: a third departure, and two tellings that write nothing

`SeatLeft` → `SEAT_LEFT` with `departure: LEFT`, `reaches_the_room`, and a nudge, like every
line. `SystemLineCode` is unchanged; `the-words.md` §23 gains the sentence *{name} left — that
seat is open again*. `people` resolves the actor as it resolves a decliner — the shape ADR-0148
§4 made general for exactly this day. Membership reads the game's current line-up (§3), so the
leaver is out of the room and a newcomer is in it the moment the re-seat commits.

`SeatVacated` and `LineUpReseated` reach the room **not at all**, and the table says why:
the challenge's own `SeatLeft` draws the line, the acceptance that completed the court draws
its own, and the roster is read off the game live rather than told. A room told twice would
write a second line for one departure.

`lifetime._concluded_at` is untouched: a room with a game ends on `planned_at`'s anchor, and a
reopened court moves nothing later.

### 6. The fill and the pool, on a court that may hold only the filler

`HalfBuiltCourtQuery.half_built_court` answers for a reopened court — it is `LINE_UP_INCOMPLETE`
and derives it — and excludes the departed through `already_asked_at` as it excludes a decliner.
What moves is one invariant: `HalfBuiltLineUp` and `HalfBuiltCourt` refused *a half-built court
with nobody on it but the filler*, which was true while `LINE_UP_INCOMPLETE` required a second
person and is false the moment the singles opponent leaves. A fill with no locked seat is still a
fill — it names the challenge, exempts its pair and excludes the departed — so `search.surface`
records `FILL_SEATS` on the challenge being named rather than on the locked seats being
non-empty. `optimised_for` still follows the locked seats, because it is about them.

### 7. Records and copies

`CONTEXT.md`: **Seat** gains *open*; **Line-up** (Games) loses *never afterwards*; **Game** gains
the re-seat; **Standing** (Challenges) notes `LINE_UP_INCOMPLETE` after `ON`; the challenge
invariant *a challenge stands as long as somebody other than the organiser is still in it* gains
its exception. `the-loop-screens.md` §2.1 gains the reopened court's arm and §6 an obligation;
`the-words.md` §23 the third sentence and §23.1 the two tellings. The superseded sentences carry
blockquotes; the index carries this line.

### 8. What is recorded and not scored — the open question a later record owns

**Leaving costs nothing, yet** (#411 rule 7). `SeatLeft` is written and the history walk does not
read it: `answered_counterparts` and `answering_for` count acceptances and declines, and a
departure is neither. `late_change_threshold` stays `None`, and its docstring now says why —
*recorded, not yet scored*: the game has a moment now, so *late* has a referent for the first
time, and what a departure an hour before it should cost is a product judgement this record
declines to make. Recording the act with its instant is what lets a later ADR weigh it without
rewriting history. Which strand, which window and which threshold are that record's questions.

### 9. What is out of scope, and why the fold allows what it allows

Calling the game off, the organiser's fallback and `CALLED_OFF` are #417's — decided in
[ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md), which also answers the question the
Consequences below leave open: a called-off game is **not** a ghost. Removing somebody
else stays refused — `AnAcceptedPlayerMayNotBeRemoved` — because the people who agreed did
nothing wrong. There is no way back for the one who left and no unlock. And the fold lets the
**last** person leave rather than refusing it, because the alternative is a rule about a count
that #417 replaces with an act: a court everybody has left is a game nobody is in, its room has
no members and answers `conversation_not_found` to everybody, and its window closes on silence.

## Consequences

- **A game is no longer a fact about four people for ever.** Every reader of `line_up` that
  assumed occupancy — the pairing adapter, the sportsmanship court, the rating settle — now
  reads through `players` or handles `None`, and the two that are only ever asked about a played
  game are protected by the result refusal rather than by the type. The type says `UUID | None`
  so the next reader meets it.
- **A ghost is charged to the people who stayed.** A court left open until its window closes is
  `NEVER_PLAYED`, and `attendance_for` files that against the three who did not leave exactly as
  it files any ghost. Rule 7 leaves the leaver unpriced; nothing here re-prices the stayers.
  #417's call-off is the honest way out of that, and whether a called-off game is a ghost is that
  record's question.
- **A reopened court holds its pair until it is re-seated or called off.** `LINE_UP_INCOMPLETE`
  holds the pair (ADR-0142 §1) and this court can sit in it until its game's window closes —
  which releases nothing on the challenge. A half-built court that was never a game has the same
  property today, with withdraw as its exit; this one's exit is #417's. Until then, two people on
  a reopened court that nobody fills are held apart for as long as it stands, and the seed's
  pair fixtures should not build one.
- **Two ports for one guard**, and a third Protocol on the `challenges` side, because no arrow
  may move. The cost is three files where one boolean would do; what it buys is that
  `make lint-imports` still proves `games` reads no plan, which is the sentence ADR-0145 §4 told
  us to protect.
- **Withdraw on a reopened court is refused with a code whose docstring said the opposite.**
  `not_a_half_built_line_up` now covers a court that *is* half built, for a stated interim
  reason. A client drawing *Withdraw* on `LINE_UP_INCOMPLETE` draws a button that refuses on a
  reopened court until #417 lands; the client tickets (#418, #419) know it.
  *Lifted the same day by [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md); the code
  is one code for five standings again.*
- **The contract grows, and one widening is not additive for an installed build.**
  `SeatingSchema.player_id` goes from required to required-and-nullable: a regenerated client
  absorbs it as `string | null`, but a build installed before this record types it `string` and
  meets `null` the first time somebody leaves a game it is looking at. That is the cost of
  ADR-0141's *never dropped* — the alternative, a seat missing from the list, is the
  three-person doubles game that record refused. `SeatAnswer` and `SeatDeparture` each gain a
  value a client switch has to learn to fall through; one route and five refusal codes are new.
  The client's own hand-narrowed types (`ChallengeSeat.answer`, `GameSeat.playerId`) go red on
  the regenerated contract until #418 widens them, which is that ticket's first line of work.
- **`late_change_threshold`'s reason moved from *there is nothing to move* to *nothing prices
  it yet*.** The port's `None` reads the same and means something weaker. ADR-0098's demand on
  the context that owns plans is now genuinely deferred rather than vacuous, and the next record
  to answer it amends that ADR.
