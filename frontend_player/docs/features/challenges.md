# challenges — the send, the answers, the fill and the withdraw

> The design record for `src/features/challenges/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**⚡ becomes a challenge on the court once full, and that is `features/challenges/`.** The seam
is drawn at _the one action in this tab that reaches another person_: the pinned CTA is the
court's own slot **calling** a challenges use-case, and `SH.propose`, the send, the two
re-reads and every sentence any of them writes are that feature's. The pre-send sheet states
the **irreversibility and no duration** — each invited seat carries its own `answer_by` and a
mutual-born challenge has none, so `{window}` was one constant standing in for three sentences
and the pre-send one is discharged by **deletion**; the real deadline is per seat and arrives
the moment after the act. Its closer is two sentences, because _nothing opens until they
accept_ is false for doubles: the first acceptance opens the chat.

**The send is pending, never optimistic, and that dissolves the question rather than answering
it.** Success **replaces the whole stack** with `[Now]` and ends the Play session, so a
rolled-back send would have nowhere to return to — nothing is rolled forward, so nothing needs
rolling back. The control is busy, the stack moves on success only, and the confirmation is the
**toast**, which is the entire report that the one irreversible act in the feature succeeded
because the destination it lands on is a placeholder. That is why it is the single
**interrupting** announcement in the app. **No `Idempotency-Key`:** one open challenge per pair
across sports is a rule that does not expire and a key does, so a duplicate press is made,
read, and refused by the same check that would refuse a stranger's — the rule is the mechanism
and a key beside it would be the weaker of two.

**A refused send is followed by a re-read, never by a payload.** The refusal states the class
of problem and names nobody, because `AppError.details` is untyped, invisible to the backend's
own response fence and ungeneratable against ADR-0006 — so `line_up_no_longer_sendable`
re-reads the **origin search**, whose withheld rows the court already turns into marked seats,
and the open-challenge refusal re-reads the player's **own** challenges for the name. **Neither
re-runs the search:** a re-run mints an id the whole line-up must adopt and can drop a seat
nobody touched, which is H-18's harm arriving through the remedy. The branch is the **code and
never the status** — three refusals share `409` and one of them is about nobody's state.
And when the re-read marks nobody, the court **says so at court level** rather than leaving
somebody refused in front of four seats that all look fine; the pair rule gets the same
treatment when the game in the way is between two invitees, on a list this player cannot read.

**The send is the one act in the app that fails rather than pausing, and the screen says
_wait_.** `networkMode: 'always'` is the mechanism — a challenge's answer window is derived at
send, so a tap deferred to the next reconnect carries a deadline nobody chose — and the closed
button beside `offlineMessage('does-not-resume')` is the courtesy over it, which is Part 11's
own split. `useIsOnline` is what the court reads for that, and it is the one caller.

**The challenge screen is the second state-keyed surface, and it is keyed on a `Standing` rather
than a `GameStanding`** ([#361](https://github.com/Raketa02/Raketa/issues/361),
[ADR-0143](../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
A challenge with no acceptance has no game to key a screen on, so there are two of these and not
one. `domain/challengeDetail.ts`'s `challengeArm` folds six standings and two sides into five arms,
and **the sentence, the card block and the controls are three readings of that one fold** — which
is what discharges §2.4's _an affordance is never removed without the space saying what took it_
**by construction** rather than by a rule a component remembers: there is no state in which the
buttons are gone and the standing sentence has not changed. **`ON` has an arm, and the inbox row is
what reaches it** — a completed line-up keeps its row while it is news and every row is a door. The
row draws §13's `ON` sentence too; **no system line** does, because §3.4 refused the one #324 had
given it, so the row is what makes the arm reachable. #324 took the **card** away, not the row
([#390](https://github.com/Raketa02/Raketa/issues/390)).

**The two answers are gated on the seat and never on the side alone.** §2.1's table reads
`AWAITING_ANSWERS · invitee → I'm in · Not this time`, and a padel four where one invitee has
already accepted is **still** `AWAITING_ANSWERS` — that reader is an invitee in the standing that
offers the buttons with an act already spent, which `POST /accept` answers `seat_already_answered`.
So the predicate is _the reader holds a seat and nobody has answered for it_, and **neither button
names a state the act cannot produce**. §13's sentence for that reader is still the one that
assumes they have not answered, which is #339's amendment owed one row up and is filed as
[#389](https://github.com/Raketa02/Raketa/issues/389) rather than invented in a build session.
**`I'm in` replaces the design's _Accept — game on_**: accepting arranges nothing and draws
_Planning_, so the phrase is false the moment it is tapped, and the label is the standing sentence
in the first person.

**`I'm in` goes to the room, and the door is drawn wherever the join answers.** Accepting is the
one act whose whole point is a room to talk in — the singles room with the person who challenged
you, the doubles room the people already in are already talking in, its history included, because
membership is derived and never cut at the moment you joined. The reply is still the redraw, and
then the screen pushes the room. The door is ADR-0149 §3's join over `GET /conversations`, and the
room is written by the teller off the outbox **after** the accept has answered, so the one re-read
the reply invalidates can land before it exists: `useAwaitedChatDoor` re-reads the list on a
cadence a little under the outbox's own second and stops on the row or at a bound
(`conversations/domain/roomOpening`), which is not Play's rule bending — a list of rooms, on the
player's own press, stopping on the answer. **What is waited for is the reply's to say.** `ON`
means this yes completed the court and a game exists — opened inline with the accept — while the
room is told which off the outbox a moment later and nothing nudges when it is; a push that
waited for the room alone landed in one drawing no plan card, so the wait is for the row to carry
its game, and `game_id` is mapped on the row for that one reader (`RoomExpectation`). Any other
reply waits for the room alone, because there is no game to know. Past the bound the screen simply stays, and it now
draws _Open the chat_ on **every arm whose reader the room would hold** rather than on the
half-built court's alone — an accepted seat waiting on the others, a court that is on, the
organiser once the first yes has landed — because _no door rather than a dead one_ cuts both ways.
Whether the reader is in the room is the fold's own answer, `readerIsInTheRoom`, asked **beside**
the join and not instead of it: the join says a room exists, and a decline or a withdraw
invalidates the list rather than patching it, so for a beat it still holds a room the reader has
just left; the `answer` arm's reader has said yes to none. _Not this time_ goes nowhere, because a
no leaves the reader outside whatever room the others keep.

**Pending, never optimistic — and the reply is the redraw.** Both answer routes return
`ChallengeSchema`, which _is_ the server's derived standing, so `redrawnFrom` folds it onto the
detail the screen holds instead of refetching. **It keeps the card block**, which ADR-0143 §8
settles in as many words — _nothing about accepting changes who those people are_ — and the arm
drops it when the standing leaves the two that draw one, **by that rule and not by a round trip**.
The merge joins seats by position and checks the occupant anyway: a card is a statement about a
**person**, and one carried onto a seat somebody else now holds is the single mistake here nothing
downstream could detect. **The neighbours are invalidated rather than patched** — an accept that
fills the last seat opens a game and a conversation in caches the reply says nothing about — and it
is `challengeKeys.list()` rather than `.all`, because `all` is a prefix that matches the detail
entry too and would send the request the redraw exists to make unnecessary.

**A stale tap is a re-read, not a toast, and there is no new copy for it.** `actRefusal` — named
for the **acts** rather than for the answers, because there are four of them and they refuse the
same three ways — re-reads on every code that means _this challenge is not what the screen thought
it was_: the closed window, the already-answered seat, a withdraw on a court that has some other
end, a withdraw offered to a side the reader is not on, a fill by somebody who has left, and a
challenge that ended under the builder. Every sentence they land on — _Your day ran out_, _You said
no_, _You withdrew this_ — is §13's and already tested; `challenge_not_found` **leaves the screen**,
one code for two cases on purpose; anything else says what it says through this feature's own
table. **Nothing in `challenges` is sent for you later** stays one line at one site:
`CHALLENGE_MUTATION_OPTIONS` covers the send, the two answers, the fill's send and the withdraw, on
the restated test _is this act's meaning fixed by the moment it is tapped?_ Offline draws the
shipped builder pattern exactly — **the controls grey out under one amber note**, not one per
button, with no third value beside `does-not-resume`. And **the offer may expire under the finger,
and it is let to**: the read sits at `staleTime: 0` with the app's focus refetch, because a pinned
pool _is_ the record where a challenge's standing goes false against a clock while you look at it.

**A half-built court is grown by any live member and ended by the organiser alone**
([#362](https://github.com/Raketa02/Raketa/issues/362),
[ADR-0150](../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
`LINE_UP_INCOMPLETE` _is not a waiting room_, so its arm is **grow · talk · end** — and the two
permissions differ because the acts do: the commonest half-built court is born of two mutual yeses,
whose "organiser" is only whoever said yes second, and making that tiebreak the only person who can
finish a padel four would leave the other looking at a court they can neither complete nor leave.
_Open the chat_ is the conversation's door and arrives with the ticket that has a room to open.
**⚡ runs the fill and pushes a builder holding a full court and a fresh search**, which is _Find a
game_'s own shape and is what dissolves the _which search_ question: the builder needs neither a
stale `search_id` nor a reconstructed line-up, and _Pick players myself_ works on the first screen
instead of after a mandatory ⚡. **Nothing outbound happens on the press** — the send is a separate
press, on that screen, and it **pops back here**. The ⚡ is **not drawn**, and that is 10.2's own
rule rather than an omission: _the ⚡ is `zap` and never the character_, `Button` has no slot for a
glyph, and §24.3's _decorative and hidden_ is discharged by there being nothing to hide.

**The reader who has left such a court is not a live member, and the screen gives them §13.1's
sentence about their own seat** — _You said no. They are still filling the court._ / _Your day ran
out…_ — and nothing to press, because the fold reads the seat rather than the side alone.
`GET /challenges` is _every challenge you hold a seat in_ and a departed seat is still a seat, so
the record keeps them and the screen resolves for them by its route. **Whether the row is drawn is
the inbox's question, and a no of your own leaves it with the tap** (`belongsOnTheInbox`): the
shelf life keeps a row a day to tell the reader something they did not do — a seat reopened, a day
run out, a court withdrawn — and a decline is the reader's own act, so _You said no_ is not news to
them, on a singles court their no ended and on a doubles court that carries on without them alike.
The organiser's row for the same no keeps its day, because to them it is news; a lapse nobody chose
keeps its row to be read. **Not because the pair rule holds them — it released them the moment they
left** (#393); what keeps them out of _this_ court is `already_asked_at`, per aggregate.

**The builder is `features/play`'s existing screen at a second route, and nothing about it is
forked.** `/chats/challenge/[challengeId]/fill` lights the Chats column for free and makes _back_
correct by construction, which is ADR-0149 §9's shape reused — **no `from` parameter**, because the
challenge is stamped on `PlayOrigin` by the fill that minted the record, and the screen reads it
there. It **borrows `playSession`**: one store, one definition of a line-up, no fork of
`domain/lineup.ts`. Its **working week is undefined**, already the legal value meaning _fill against
the profile's grid_, since there was no _Find a game_ on which to improvise one — and `PlayOrigin.week`
became optional for it, with `sameOrigin` refusing to collapse _nobody composed a week_ into _somebody
cleared theirs_. One sentence in that store moved and the important half did not: a session **begins**
when the shell lays the Play stack down **or when a challenge is re-entered from Chats**, and it
still **ends in exactly one place**. Nothing in the flow calls `resetShellStack` — `landOnNow`'s
_there is nothing left to be behind_ is false where the thing behind is the challenge you were
completing, and it is the surface that draws the result.

**The fill names the challenge and says nothing else about the court**, which is a second shape of
one request rather than a second route: `sport`, `mode` and `locked_seats` are read off the
challenge and **refused** beside it, so `LineupAsk` is a union and all three are unspellable rather
than optional. The record it mints is stamped with the mode **the engine resolved**, read off the
envelope, because a mutual-born challenge has none of its own — and a line-up answer carrying no
mode is refused rather than bound to one this client invented. It carries **no prompts**: the four
are about the searcher's own _Find a game_ values, this journey composes none of them, and a
dismissal spends the offer for thirty days on the one surface that cannot honour it. The pool it
opens draws **no ladder** for the same class of reason — taking a rung mints a search that does not
complete the challenge, so the gate would exclude the very people sitting on the court.

**An accepted seat is not a control, and `BuildSeat.accepted` finally has a producer.** No clear
badge, no press, no pool — swapping is the only thing that works on it, which **draws** _an
acceptance is to the game, not to the side_ rather than writing it. The truth table gained a
`NOTHING` arm and `courtPresentation` **lost a sentence**: _{Name} already accepted — they keep
their place_ was copy for a state nothing could reach, and the ticket that made it reachable decided
the other way, on #324's _no copy, no pill, no disabled control_. **_Start over_ is absent** on such
a court — not disabled, and not redefined to mean _empty it to these two_, which would be a second
meaning for one label. The send is `POST /challenges/{id}/seats`, the send's shape minus the mint,
and the pre-send sheet lists **only the people being asked**: somebody who accepted is not an
invitee and may not be removed. Its cache effect is an **invalidation rather than a redraw**, which
is the one place it differs from the two answers — the reply carries no `read_at`, and the fresh
deadlines it creates would otherwise be stated against the instant the screen was opened.

**The withdraw is the second irreversible act in this app that reaches other people, and it takes
the first one's shape.** `WithdrawSheet` is `SH.propose`'s: a real modal with hidden siblings and
Android back, a title naming the **moment** rather than the act, a dismissal named by what it does,
and **focus landing on the title rather than on the first action** — that action is the destructive
one, and landing focus there would make the worst outcome the cheapest to trigger. Its second body
line is what earns it: the conversation is **destroyed, not delisted**, so the Chats list is
**invalidated rather than patched** and what people wrote is gone. It is pending never optimistic,
it fails offline like every other act here, and the visible control says `Withdraw` while its
accessible name says `Withdraw this challenge` — 6.9's _names which photo it removes_, one surface
over.

**The card block is a fourth card over the same parts kit, and `challenges` spells its own
schema.** Narrower than a `PlayerCard` by ADR-0143 §5 — no social tags, no run of form, no counted
games, no photo verdict, no liveness, no inclusion reason — so `ChallengeCard` is a fourth
composition rather than a `surface` prop on one of the three. It is drawn in `AWAITING_ANSWERS` and
`LINE_UP_INCOMPLETE` and **per seat as well as per challenge**: somebody who declined or lapsed
inside a court that is still open gets none, because _that person is a stranger to you once more
the moment they leave_. **Four things the design draws that it does not** — no bio, which is a
refusal ADR-0143 holds is **stronger** here than where it was written because an invitee was put in
front of somebody without asking; **no _Why?_ affordance**, so the card is one accessibility element
with no action of its own; **no countdown**, the deadline being stated from the response's own
`read_at`; and the **Player Score as a segment that disappears** rather than a row reading
`Score 0`. Its drawn set is `LEVEL_FIT · DISTANCE · RELIABILITY`, and **`PREDICTED_BALANCE` is
deliberately not in it**: the court's forecast is the _screen's_ line drawn once, because the same
figure rides on every card, so a balance row here would print it once per seat.

**An invitation a swipe produced says so, in one line under the organiser's card**
([ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §8).
_You said yes to {name} on Players_ is drawn exactly when the organiser's id is in the reader's
own `GET /interest` outgoing list for the challenge's sport, and nowhere else: under the
organiser's card and no other seat's, so a doubles court with a card per person carries it once.
It is **client-side and the reader's own act** — no code crosses for it, and ADR-0143's refusal
to tell an invitee _why the engine picked them_ is untouched, because Ania saying yes to Karol on
Players is a fact she already holds. The read is Play's, reached through its surface
(`useOutgoingInterest`, the deck's own query, and `saidYesTo` beside it) rather than a second
query over the same route: one cache entry, shared with the deck and the pool, which a deck tap
moves on its own reply. The line is never waited for — the card is drawn without it until the
list lands and gains it without moving — and the handle in it is whole (`seatName`, ADR-0107).
The organiser reads no such line about themselves, because nobody is in their own outgoing list.

**The evidence is mapped a second time, and that is the decision rather than the debt.** The wire
carries `Court…` schemas beside Play's because the backend spelled a second, narrower contract, so
a client mapping them through `candidateMappers` would be reading a shape it was not sent — and the
two are free to diverge, which is the point. What is **not** duplicated is the vocabulary or the
words: `challengeDetailMappers` narrows against Play's own lists and produces Play's own domain
objects, so a term or an evidence variant added to the contract reaches both features at once and
the only thing spelled twice is the field renaming, which is what a mapper is.

**A player can leave a game, and the act is this feature's even though the screen is not**
([#418](https://github.com/Raketa02/Raketa/issues/418),
[ADR-0162](../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
`POST /challenges/{id}/departure` writes a fourth `SeatAnswer`, **`LEFT`**, over an accepted seat:
the seat that reopens is the challenge's, so the fill, the pool, the pair rule and the room's line
all keep the record they already have, and the game is told in the same transaction. `SEAT_ANSWERS`
gains the value and **every table over the union gains a row** — `playersStillIn` now reads a
`Record` rather than an `||` chain, because a fourth answer missing from a disjunction would have
silently kept somebody in a game they had walked out of; `challengeDetail`'s `LEFT` table treats
it as the other two, so the card block leaves with the person and the arm draws them as having
left; and the reader's own seat reads **_You left. They are still filling the court._** on §13.1's
shape, and _You left. They are still waiting on answers._ one row up, because a court somebody
left can be asking its newcomer. **The control is `LeaveGame`, composed onto the game screen by
`features/plans` through `types.ts`** — the shape `useChatDoors` already takes — because the
departure is a challenge act reached from a game, and the words stay with the control: a deck of
their own, `leaveGamePresentation.ts`, beside the surface that says them rather than rows in the
challenge screen's. **Quiet, destructive, last, behind a sheet**: a `secondary` button reading
`Leave this game` at the bottom of the plan lead, `Leaving…` while in flight, greyed under the
amber note offline, and `LeaveSheet` in front of it on `WithdrawSheet`'s exact shape — _Before
you leave_; _The others keep the game and can fill your seat._ / _You can't be asked back into
this one._ / _This cannot be undone._; `Leave the game`; `Stay in` — reworded because a departure
destroys nothing where a withdraw destroys the room, so the first line says what survives and the
second the one cost that is the leaver's alone. **Pending, never optimistic, and
`CHALLENGE_MUTATION_OPTIONS` spread whole**: a departure is dated exactly and guarded against the
agreed moment, so one queued for a reconnect could land as a refusal nobody was there to read.
`useLeaveGame` redraws the challenge detail from the reply as the withdraw does and **invalidates
the games, the plans and the conversations** — lists the reply says nothing about, and the
leaver's rail, plans and inbox all drop the game — so the card is gone from the rail because the
server no longer lists it, not because the client removed it; `planKeys` is read from
`features/plans` for that one line, because a hook that declares its cache effect declares all of
it. Then the control goes `back`, whichever door the screen was opened by. **`actRefusal` gains
the departure's three codes** — `not_a_game_yet`, `game_is_history`, `game_moment_has_passed` —
all _re-read and say nothing_, and the re-read is the composer's games list rather than a detail
this feature holds; `challenge_not_found` leaves the screen as before, and `account_held` is said
in the sentence every write here says it with. **Whether the control is drawn is the composer's
rule**: only while the agreed moment is ahead, mirroring `game_moment_has_passed` off the same
instant rather than offering a control the act would refuse. The room's `SEAT_LEFT` line gains
its third value — _{name} left — that seat is open again_ — one context over.

**The fill and the withdraw both reach a reopened court, and both are pressed on the game screen**
([#419](https://github.com/Raketa02/Raketa/issues/419),
[ADR-0163](../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). **`FillTheSeat` is
the challenge screen's ⚡ pressed on a game**: the same `useFillChallengeSeats`, the same push to
`fillRoute` — moved beside the route's own schema, since three surfaces push it now — and the
same builder, whose send pops back to wherever it was pushed from. One input differs: who has
already said yes is read off the **game's** seats by whoever composes it, because the game's court
is the court as it stands now and the challenge's is the arrangement as it was sent; this feature
never learns what a game is. It is one component for two surfaces — the Now card's wide door and
the game screen's primary act — because they are one press; the card hands in its accent and the
door's width, the screen hands in nothing. Drawn only while the agreed moment is ahead (the
composer's rule, mirroring `game_moment_has_passed`), it goes busy under its own label as the
challenge screen's ⚡ does, and a refusal costs it what `actRefusal` says: a stale tap re-reads the
composer's games list, `challenge_not_found` leaves, the rest is said. The word is
`theActsWords.ts`' `FILL_THE_SEAT` — singular, one per surface beside `⚡ Fill the seats` — because
two features say it and the control is composed into the card. **`CallOff` is the withdraw grown
to a reopened court**: the act is `useWithdrawChallenge` unchanged in what it sends, the sheet is
`WithdrawSheet` **handed different words** — it takes a `words` prop now, defaulting to its own
deck, rather than a fourth copy of its shape — and the deck is `callOffPresentation.ts`: _Before
you call it off_; _Everybody loses this game._ / _The conversation goes with it, and what people
wrote is deleted._ / _This cannot be undone._; `Call it off`; `Keep it`; `Calling it off…` in
flight. One label on the control and on the sheet's act, on `Send the challenge`'s precedent, with
what is under the sheet hidden by `behindOverlay` while it is up. **Who may is answered here and
not by the composer**: `holdsTheExit` on the cheap `Challenge` row — the reader's seat is accepted,
and they are the organiser or the organiser's seat has been given up, read and never assumed, so a
court the organiser holds no seat on fails soft — and `useHoldsTheExit` joins it off the challenge
list the tab bar already holds, keyed by the game's `challengeId` — one more observer on a query
the app keeps, rather than a detail read for one boolean; the composer hands in only what is its
own to say, that a seat is open. Not gated by the moment, so on
a short court past it this is the one act left. **`useWithdrawChallenge` now invalidates the games
and the plans as well as the challenges and the rooms**, because a withdraw can call a game off in
the act and a hook that declares its cache effect declares all of it; on a court that was never a
game the two re-reads find nothing changed. Success **stays** — the screen is about a game that
still exists, with an ending now — and re-folds into the called-off arm off the games list.
`actRefusal` needed no new code: `withdraw_is_the_organisers`, `not_a_half_built_line_up` and
`challenge_is_over` were already re-reads. **Not done here**: the challenge screen's own withdraw on
a court that has been a game still said `Withdraw` with the court's words and still drew it for
the organiser alone (`mayEnd`); [#428](https://github.com/Raketa02/Raketa/issues/428) took that
control off the filling arm altogether and gave _Call it off_ to any player on the court — the
paragraph below.

**_Leave the game_ from the Chats list and from the challenge screen, before the court is whole**
([#427](https://github.com/Raketa02/Raketa/issues/427),
[ADR-0165](../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§1, §6). A yes can be taken back: the departure route is admitted on a court that has never been a
game (#424), and the client meets it in two new places on one component. `DepartureDoor` — named
for the shape rather than the word, because a `LeaveTheGame` an article away from `LeaveGame` would
be one name — is the **door**: a render prop that hands the surface the act's word, a way to open
the sheet, the accessibility action a row offers in place of a swipe and the ref the sheet returns
focus to, and draws the sheet itself as a sibling of whatever the surface drew, with what the
surface drew hidden while the sheet is up (`CallOff`'s line: one label on the door and on the
sheet's act), so the act's whole shape is one file's whether it is met on a row or on a screen. The
conversation row takes it **composed by the shell** rather than imported — `features/challenges`
imports `features/conversations`, and the cycle is Part 1's named defect — so `ChatsScreen` hands
`DepartureDoor` to `ConversationsSection` as its `act`, satisfying the `RowActDoor` shape that row
declares without either feature naming the other; the challenge screen draws it as a `secondary`
button on **both live arms** — an accepted invitee waiting on the others, and any member of a
filling court, the organiser included, because the organiser is a player in that rule — **last**,
after the withdraw, on the game screen's own order (the act that ends it for everybody above the act
that takes one person out). Whether it is drawn is the fold's `mayLeave`: the reader is on a court
that is not whole **with somebody**, and the one case it withholds is a court of one — the organiser
nobody has joined has nothing to leave, and their exit there is #428's _Remove the challenge_. It
says nothing about whether the court has been a game; on one that has, it is the same route the game
screen's _Leave this game_ posts, and the moment guard is answered in words rather than by a control
this read cannot see the moment for. **The sheet is `LeaveSheet` grown, not a fourth sheet**: on the
game screen it dismisses on confirm and draws no refusal and no pending state, on `WithdrawSheet`'s
line; from the list there is no control left to carry either — the revealed button closed with the
row — so the sheet takes `body`, `busy`, `said` and `offline`, stays up while the act is in flight,
and **says a refusal in words** where the game screen re-reads and says nothing, because a list row
has no fold for a re-read to land on. The words are `leaveGamePresentation.ts`': one body line for
the list's sheet, `LEAVE_FROM_THE_LIST_BODY`, and `LEAVE_REFUSED` — a sentence for each of the four
codes the route documents, over `challengeErrorMessage`'s fallback — with the lists re-read for
every code that means _this court is not what the row thought it was_, **once the sheet is
dismissed**: the sheet is drawn inside the row it is about, and a re-read landing _over_ mid-sentence
would take the row and the words away together, so the re-read is owed and paid on _Stay in_, and a
court that has genuinely ended goes when the server says so. Which lists is `useReReadCourtLists`',
in `hooks/`, because a cache effect is the hook layer's to declare and the door decides only when. **The inbox drops an own `LEFT` at once**, as it
drops an own no: `OWN_ACT_LEAVES_AT_ONCE` is a second `Record` over `SeatAnswer` and deliberately
not `GIVES_UP_THE_SEAT`, because the two differ in exactly one cell — a lapse opens the seat and
nobody chose it. **`useLeaveGame` writes the reply into the challenge list** (`rowRedrawnFrom`, the
standing and the seats with the list's own `readAt` kept) **and drops the room from the conversations
list** (that feature's `dropRoomOfChallenge`), so both of the leaver's rows are gone on the reply
and not a round trip later — _gone without a refetch_ — and then re-reads the four lists as before,
because the reply is one court and the lists are every court. The game screen's `LeaveGame` is
unchanged.

**_Remove the challenge_ from the Chats list and the challenge screen while nobody has joined, and
_Call it off_ for anyone on the court**
([#428](https://github.com/Raketa02/Raketa/issues/428),
[ADR-0165](../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§4–§6). The withdrawal route carries two acts now, told apart by whether the court has been a game,
and the client meets each where its reader stands. **_Remove the challenge_ is the withdraw while
nobody has joined**: the organiser's, exactly while nobody besides them holds an accepted seat —
before anybody has answered, and again once everybody who joined has left, whatever seats are
still deciding — and nobody's the moment somebody is in. That rule is `mayRemove` on the cheap
`Challenge`, beside `holdsTheExit`, and it is read twice from one function: the organiser's
**challenge row** asks it to decide whether it swipes at all, and the fold's `arranging` arm
carries it as `mayRemove` beside `mayLeave`, which for the organiser is the same question asked
from the other side — a court of one is removed, a court with somebody is left, and the arm never
offers both (`challengeDetail.test.ts` pins it). `mayEnd` leaves the `filling` arm with the
withdraw: a court somebody has joined is nobody's to end for the others, so that arm is grow · talk ·
leave and the organiser sees what everybody sees. **The row is 6.15's `SwipeRow`, this feature's
own**, so nothing is composed in from the shell as the conversation row's act has to be: the act
behind the revealed button is `RemovalDoor`, a second door on `DepartureDoor`'s shape — a render
prop handing the surface an `ActDoor` and drawing the withdrawal's sheet beside it — and the
challenge screen draws the same door as a `secondary` button on the arranging arm, between _Open
the chat_ and where _Leave the game_ would be. What the two doors have in common — when the sheet is
up, where focus returns, and that a refusal's re-read is **owed and paid on dismissal** so the words
are read before the row they are about can go — moved out of `DepartureDoor` into
`hooks/useActDoor.ts`, because a rule written twice drifts; each door is now its act, its sheet and
its words. **The sheet is `WithdrawSheet` handed a new deck, and the withdraw's own deck is
retired**: `words` is required, `CallOff` hands in the game's and `RemovalDoor` the removal's —
_Before you remove it_; one line, _If you remove this challenge, it will also disappear for everyone
you invited._ — reworded on the QA walk ([#429](https://github.com/Raketa02/Raketa/issues/429) E1)
from _It disappears for the people you asked, too._ so the consequence hangs off the act — which
is the one consequence ADR-0165 §6 asks the sheet to name and the one the organiser cannot see from
their own list; `Remove the challenge` on the door and on the act, on `Leave the game`'s precedent; `Keep it
open`; `Removing…` on the sheet's act — and the sheet grew `busy`, `refusal` and `offline` as
`LeaveSheet` did, because from a row the sheet is the surface. `WITHDRAW`, `WITHDRAWING`, the
withdraw's title, three body lines, act and dismissal, and `WITHDRAW_CHALLENGE_NAME` are gone;
nothing drew them. **A refusal is said in words on the sheet** — `REMOVE_REFUSED`: _Somebody's in
now, so it's no longer yours to remove._ for `somebody_has_joined`, the one refusal a stale row
invites, and the departure's own `THIS_ONE_IS_OVER` for `challenge_is_over`, named once in
`leaveGamePresentation.ts` because two sheets say it — over `challengeErrorMessage`'s fallback; the
route's other three codes cannot reach a row `mayRemove` drew and earn no words. `actRefusal` gains
`somebody_has_joined` as a re-read, so on the challenge screen the arm re-folds into the one that
offers _Leave the game_ once the sheet is dismissed. **The row goes on the reply**:
`useWithdrawChallenge` writes the reply into the challenge list as `useLeaveGame` does, and the
inbox drops an own removal at once — `removedByTheReader` in `challengeInbox.ts`, a `WITHDRAWN`
challenge the reader organised on which nobody besides them had joined (`nobodyHasJoined`, the half
of `mayRemove` that survives the ending), which is the organiser's own act by construction, the
third sentence after _You said no_ and _You left_ that tells the reader nothing. A game **called
off** reads `WITHDRAWN` too and is deliberately not this: others had joined, and since anybody may
call it off the standing alone cannot say it was the reader's act, so that row keeps its day. The
room a court the organiser was alone in again still had is invalidated rather than patched, on the
withdraw's own line. **_Call it off_ is any player's on the court**: `holdsTheExit` is now _the
reader holds an accepted seat_, ADR-0163 §1's organiser-first rule and its fallback gone, and
`CallOff` on the game screen is otherwise unchanged — the composer still hands in only _a seat is
open_, and the _Called off_ ending draws as it did. **Not drawn on the challenge screen**: the arms
table names _Call it off_ on a reopened court's filling arm, but the challenge read carries no fact
for whether a court has been a game (the-loop-screens §2.5's own note on the leave), so that arm has
no end act at all and the game's own screen, reached from Now, is where the game is called off.
**The invitee's row for a removed challenge is §13's sixth sentence unchanged**, kept its day as news.
One design-system consequence, in 6.15: _Remove the challenge_ is longer than the reveal was sized
for, so the revealed control's label centres and wraps to a second line, which the row's full height
holds; the width does not grow per caller. Not seen on a device.

**A row still being filled names the people still on it, and a court that ended on somebody
leaving it leaves the inbox with its room**
([#429](https://github.com/Raketa02/Raketa/issues/429)). `othersOn` drew every occupied seat: B in,
C and D having said no, the row drew three faces and _+2_ over _2 in, 2 seats open_ — a four that
was a two. A seat given up keeps its occupant on the wire because the record says who was asked,
but a row is _who you would play with_, so on `AWAITING_ANSWERS` and `LINE_UP_INCOMPLETE` the
seats `GIVES_UP_THE_SEAT` names are dropped and a seat still deciding stays; an ended row names
everybody it asked, because it is history rather than a line-up and _{name} said no_ under a row
that no longer drew them would name nobody on a singles court. And `belongsOnTheInbox` has a
fourth row that goes at once: `DECLINED` with the reader's seat accepted and some seat `LEFT` — the
court B joined and then walked out of, leaving the reader alone with nobody deciding (ADR-0165 §3:
_a departure is a no_). The room the yes opened is where that was told, and what is left is a court
with nobody committed to it but the reader — nothing to fill, nobody to ask again about, and no
news on the row the room's going does not already say. A court everybody merely **declined** is not
this and keeps #388's day: nobody was ever in it with the reader, and _that seat is open again_ is
the news. Stated so it can be argued with: the ended row for such a court would have read
_{name} said no_ naming the **first** decline rather than the one who left, and was the one place
the organiser away from the room would have learned of the departure; the row goes because the
user walking #429 found it wrong, and the sentence it would need does not exist in §13.

**An exit confirmed on the challenge screen leaves the screen**
([#429](https://github.com/Raketa02/Raketa/issues/429)). _Leave the game_ and _Remove the
challenge_ redrew the screen from their reply into §13.1's sentence about the reader's own seat —
_You left. They are still waiting on answers._, _You withdrew this_ — with nothing to press, on a
court the reader had just stopped being part of and whose row the same reply had already taken from
the inbox: a stop on the way out. `useActDoor` gains `onDone`, what the surface does once the reply
has landed and the sheet has closed; the list passes nothing, because its row goes on the reply and
the list is what is left, and the challenge screen passes `router.back`, landing on Chats whose
return re-read shows no row in either section. The screen still resolves for a stale route and
says the sentence then — a departed seat is still a seat — so what went is the stop, not the
words. **_Not this time_ is deliberately not this**: a no stays on its sentence (`challengeScreen.test.tsx`
pins it), because it is not behind a sheet and #429 did not ask; the same argument applies to it,
and it is one `router.back` in `send` if it should.

**A yes lands on the yes screen, and the room is opened by a tap**
([#433](https://github.com/Raketa02/Raketa/issues/433),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)).
_`I'm in` goes to the room_ is retired: the reply is still the redraw, and then the challenge screen
**pushes the yes screen** — `/chats/challenge/{id}/yes?which=challenge`, this feature's own, keyed by
the challenge and by one Zod-checked _which yes_ — a challenge's here; a mutual's, _Matched!_, is
the deck's door and the last paragraph of this record
([#434](https://github.com/Raketa02/Raketa/issues/434)). The screen is the app's one
dark ground: the reader's tile, `vs`, the other side's — on a padel four the partner's tile or an
outlined empty seat beside the reader's — the one lime word **Challenge!** whatever standing the
reply came back with, and two pills. It **reads everything it draws from the challenge the cache
holds** (`useHeldChallenge`, `staleTime: Infinity` over the detail entry the reply was just written
into, so no second read and no re-fold mid-entrance): `domain/yesScreen.ts` folds the seats in wire
order into the reader's side first and the reader first within it, and **a seat is a person only
when its occupant has accepted** — deciding, declined, lapsed, left and nobody are one empty seat,
which is the room's own membership rule, so the picture and the row he lands on next agree. A bad
or foreign parameter draws the ground alone and leaves for the Chats list. **A tile is the face the
app already draws** — `PlayerPhoto`'s `face` box at the two sizes the mocks measure — with two
additions for this screen: `handleInitials` over a **poster** (never over a photograph; ADR-0167 §3's
one drawing exempt from ADR-0107 §4, on a four-sided fence the presentation deck holds — never
spoken, never in copy), and the outlined empty seat. The other players' photographs come off the
seat cards; **the reader's own comes off their own record** through `player_record`'s `useOwnFace`
— a new feature edge the boundary script holds open — read once **per open** rather than cached for
the session, because the signed link lives five minutes and a cached one would be drawn as a blank
tile on the second yes of an evening; the entrance waits for that read, so no tile swaps mid-slide,
and the poster stands in if it does not answer — it waits for the **link**, not the bytes:
`PlayerPhoto` draws a photograph as a bare `Image` with nothing beneath it while it loads, so a
photo tile on a slow connection can still fill in mid-slide, which is that primitive's and not this
screen's. **The awaited door moved here and runs from the moment the screen opens**: `useAwaitedChatDoor` unchanged in what it waits for — the room, or the
room and its game when the reply was `ON` — and now answering `expired` as well, with its
six-second bound **run from the first answer after the wait began** rather than from the wait's own
beginning (the reasons, the harness's included, are on `roomOpening.ts`). _Open the chat_ is `busy` until the room is known and never
disabled: it lands as **[Chats list, the room]** — `dismissTo` the list, then the push, so back from
the room is the list and never the celebration — and past the bound it lands on the list, where the
row will appear. _Later_ and Android back (`useHardwareBack`) `dismissTo` the list, the challenge
screen popped with it; the iOS swipe-back is off on the route (`TabShell`), because a swipe that
popped to the challenge screen would land somewhere _Later_ never does. **It moves once**, on
`motion.yesEntrance` — the sides slide in and meet, the word rises, the doors fade in last, one
success haptic as the word lands through the app's first haptics port — and under reduced motion it
is simply there and silent; under a screen reader it is simply there and buzzes once, because a
buzz is not a picture. The listener gets the picture as one header sentence built from whole
handles — _Challenge! You and Ola.N against Kuba.W and Zofia.B_, _an empty seat_ where one is —
announced as the faces land; the doors sit outside it. **What did not move**: `Not this time` goes
nowhere, and the challenge screen's own _Open the chat_ on later visits is `useChatDoor` read once,
on every arm whose reader the room would hold, exactly as before. The four walks that pinned
_accept pushes the room_ are rewritten to the new exits in `yesScreen.test.tsx`; the theme's
values — two ground colours, `yesWord`, `size.yesTile`, the button's `shape`, the entrance — and
their Part 16 rows travelled in the same commit. The measurements are the mocks' and not the
record's prose: the word is 32 rather than _about 30_, the ground's two bytes are what the mocks
render rather than the stage colours the spec expected, and the pills are drawn at the existing 40
where the mock measures 38. **`expo-haptics` is a native module, so a development build has to be
rebuilt** (`pnpm ios` / `pnpm android`) before the screen buzzes; `npx expo install --check` and
`pnpm doctor` both agree with the SDK. **Not seen on a device** — the author checks the screen
against the three mocks.

**The yes screen's second face — a mutual's, _Matched!_**
([#434](https://github.com/Raketa02/Raketa/issues/434),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§1, §4). `which=mutual` is the second member of the route's _which yes_, and **the two faces are
keyed once**: the word (`YES_WORD`), the sentence (`YES_SENTENCE`) and, on the screen, the fold,
the `vs` and the two moves out (`FACE`) are each a `Record` over the union, so a third yes fails
to compile in three places rather than falling into an `else` arm. The deck pushes it from its
mutation's own success handler (the play record says why), and **the challenge is fetched on
open**: `useHeldChallenge`'s `staleTime: Infinity` reads what is held and fetches only where
nothing is, which after a challenge's yes is never and after a mutual's is always, since the deck
never held it — and the entrance waits for it as it waits for the faces. **The picture is
`pairForReader`**: you first, then everybody else who has said yes, and **no empty seat in every
sport** — a padel mutual is a four-seat court with a side still to fill, and the fold draws two
faces off it, sized as two (`tilesIn` counts the picture, not the court). It is _everybody who has
said yes_ and not _the one this tap was about_, deliberately: the reply names _the challenge these
two have_ — the one it minted, or the one an earlier mutual opened that is not finished with
(ADR-0154 §1) — and the screen holds the challenge and not the card, so a court an earlier mutual
opened that has since filled draws everybody who is in, under _Matched!_ and with no `vs`. On the
mutual that minted it that is exactly two, which is every walk the suites take; the grown court is
a decision the ticket did not make and this record does, on the line that a picture of who is in
is the honest picture and picking two of four would be picking. The listener hears _Matched! You
and Marek.P_ — `matchedAnnouncement`, whole handles, joined with _and_ and never _against_. **The
exits by face.** After a mutual's yes, _Later_ and the device's back are a plain pop, and the
Chats list where there is nothing to pop to — a cold link to the route, which
`yesScreen.test.tsx` walks; _Open the chat_ lands as `[Chats list, the room]` through the shell's
`openTab`, the second caller that surface has, and past the bound on the list alone — the deck's
suite walks both. The challenge's face is untouched: `dismissTo` down to the list under the
challenge screen for both moves, as before. `LATER`, `MATCHED_WORD` and `matchedAnnouncement`
cross the feature's surface for the deck's suite and nothing else.

**The court ends with the game, the ending says who, and the row and the screen say it**
([#454](https://github.com/Raketa02/Raketa/issues/454), [ADR-0172](../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§2–§4, §7, §9). `CALLED_OFF` is the seventh standing — `STANDINGS`, `ENDED`,
`STILL_BEING_ARRANGED` and the vocabulary assertion each gained the row the compiler demanded —
and every ending carries `ended_by` and, on a court that has been a game, `game_id`, both mapped
off the list and off every act's reply and carried onto the row by `rowRedrawnFrom`, so the
presser's row reads _You called the game off_ on the reply. **The ended rows are keyed by
`ended_by`'s own seat and never by side**: `StandingFacts`' four endings share one `EndingFacts`
payload — who, as a `NamedPlayer` with `you` for the reader; `byADeparture`, read off that seat's
`LEFT`; and the reader's own seat — and `endingLine` writes §13's second table from it, reading the
reader's own seat first on the two folded endings (an invitee who lapsed while somebody else's no
closed the court reads _Your day ran out_, as the column always said) and the act alone on the two
announced ones. **The face is who the sentence names**: `othersOn` draws `ended_by`'s seat on an
ended row, and where the sentence is about the reader's own act — _Your day ran out_, _You called
the game off_ — the people still on the court, which on an ended court is never nobody; a doubles
_said no_ row goes from three faces to one. `endingIsTheReadersOwn` is the one predicate the words
and the faces share. **The departure-drop rule is retired** — `endedOnADepartureLeavingTheReader`
existed because the only sentence was _? said no_ — and `removedByTheReader` shrank to the
organiser seat, since `WITHDRAWN` is _Remove the challenge_'s alone. **The `Called off` tag**, the
kit's `bad` variant, sits at the trailing edge of a `CALLED_OFF` row and no other, spoken last in
the row's name because the sentence does not say the word; the stripe's rule is untouched. **The
ended court** is a sixth arm, `ended`, for `CALLED_OFF` and a departure-ended `DECLINED`: the
sentence, `EndedCourt` — every occupied seat with a `SeatWord` read off its answer, and
_called it off_ off `ended_by` because the presser's seat reads `ACCEPTED` like the reader's — and
no arm at all. **The detail read carries neither `ended_by` nor `game_id`** (the spec's §0.1 says
both reads grow them; #453 put them on `ChallengeSchema` alone), so the screen reads both off the
row the list holds — `useChallengeRow`, at `staleTime: Infinity` so a second observer does not
refetch the tab bar's list on every mount — and `asTheRowSays` merges them before the fold; if the
detail read grows the two fields, the mapper changes and nothing else does. **The leaver's sheet
says what the leaving does**: `leavingWouldEnd` is the ending rule read a move ahead — the reader
holds an accepted seat, exactly one other is accepted, nobody is deciding — and `game_id` picks
_calls the game off — for {name} too_ over _closes this court for {name}_; both doors and the
game screen's `LeaveGame` read it off the same row, so three sheets cannot disagree about one
court. On the game screen's three-line sheet the ending line **replaces** the first line rather
than preceding it, as the record has it: _The others keep the game and can fill your seat_ is false
of a leaving that calls it off, and a sheet saying both would contradict itself. Nothing on the
wire says _cancel_, and nothing here does. The mock's hint under the ended court (_Nothing to
press…_) is not drawn: the record does not ask for it, and the sentence above already says what
took the controls. **Not seen on a device** — the tag, the ended court and the sheet lines are
asked for a look.
