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
