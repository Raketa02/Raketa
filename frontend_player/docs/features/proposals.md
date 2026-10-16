# proposals — a group's Games deck, and a game's details

The client side of the backend's **Proposals** context (#538, #539): the games a group deals a
player, answered with a silent yes, and one game still filling seen in detail. Built by
[#553](https://github.com/Raketa02/Raketa/issues/553) from the Games & Fill in screens (A2, A4.2),
the mechanics (§6–§8) and
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md). The group page
(`groups`) draws `GamesDeck` as its Games tab and reads its badge; the dependency points one way —
`groups` reads `proposals`, never the reverse.

**The deck is one read, and a game's details are another.** `GET /pools/{id}/deck?sport&kind` — the
pool filed under the group's id — is the deck: the segments, the badge, the capped weeks and the
cards in the order dealt, each the reader's own version with its sides, forecast, overlap and court.
A game's details (`GameDetailsScreen`, `/play/group/[groupId]/game/[proposalId]?sport&kind`) are
**`GET /proposals/{id}`** since #557 (#542 serves it): who is In, the sides, the club and its
distance, the status and **what the reader may do now** — see the #557 section below. Until #557 the
details found their card by id in the deck's read and kept it once a yes made the deck stop dealing
it; that memory, and `withYourYes`, went with the move.

**Nothing the server decides is re-derived.** The order, the sides, the forecast's figure, the grade
and every cell's shade are the read's. What the client decides is how a dealt card is drawn:
`rowsOf` puts **the side with more people In on top, yours on a tie**, and within a row the people In,
then you, then the rest — the one rule every mock (2–8, 10) agrees with; `ribbonOf`, `courtTagOf`,
`chargesAtOnce` (the stamp's price: _Book it now_ — always, since #676 — or a rescue),
`countdownOf` (under 24 h, floored), `standingCards` (a card past its deadline leaves silently), `weekCapOf` (the fortnight's capped weeks) and `refusalOutcome`.

**The kind is the switch's, corrected by the intent.** The group page's Competitive · For fun switch
(`groups`' game-intent store, which Friends shares) hands in the kind chosen; the read says which
segments the player's intent shows, and a choice it does not show is read again as the segment it
does (`resolveKind`, `useGroupDeck`'s second query) — so a For-fun player never lands on an empty
Competitive deck. No segments at all is no intent declared: `DeclarationInterstitial` replaces
the deck, reporting `DECK` — the contract's word for a deck, since `PlayIntentSurface` has no value
for a group's tab — with its own line about who reads the answer, and the answer re-reads the deck.
A refused answer is said in the words the deck hands it (`refusalMessage`, since #574): the app's
recovery sentence, because `PUT /play-intents/{sport}` answers only a lost race and a malformed
request. Find a game hands it Play's own table instead; for this route's codes the two say the
same thing.

**The stage was built for the Players deck, and lives here.** `DeckStage`, `DeckAnswers` and the
interstitial moved from `play` with their words in #574, since this is the deck that stays, with
the two things that differ handed in: the stamps' words (_I'm in_ / _Not this time_, the share after
_I'm in_ when the yes charges at once) and the three buttons' names (_I'm in_, _Not this time_, _Game
details_). The stage's cards behind now fade as well as shrink (Q90), for both decks.

**An answer flies on the press and the server settles it.** The card in flight is held by `GamesDeck`
(component state), so a re-read landing mid-flight cannot pull it off the stage; when it has flown it
is dropped from the cached read (`withoutCard`, its segment's count and the badge following), and the
answer settling re-reads every deck of the group. **A refusal is a toast**, handled on the mutation
rather than on the call — TanStack drops a `mutate` call's own callbacks when a later call is made,
and a player answers the next card before the last reply lands — and `refusalOutcome` decides the
card: a reason the player can mend (no saved way to pay, a read that failed) puts it
back, and a game over, full, already answered or no longer theirs lets it go. Offline, the answer is
held and the card stays gone, with the amber _resumes_ note.

**The bar's fold is read off the tiles' Levels.** 7.11's bar takes an advantage, and a deck card's
forecast carries only `pct` and `provisional` — so `foldOf` is your side's mean published Level minus
theirs, a short side read as its present member (the engine's own provisional). The figure printed is
the server's. **Owed to the backend**: serving the signed gap on `DeckForecastSchema`, which would
make the fold the engine's too.

**The card is not one element.** Its tiles are buttons — each opens `PlayerRecordSheet`, a press
where the Players deck asks for a long one — so the card's parts speak for themselves (the ribbon a
header, each tile, the forecast, the grid as one sentence, the court block) and the details are
reached by the **i**, the accessible path the drag never is.

**Money prints whole złoty without grosze** (`formatZloty`: _32 zł_, _27,50 zł_ when there are some)
— the mocks' form, decided here because `docs/value-formatting.md` left the rendering to the first
client to draw a price. **Owed, from a root session**: that document's paragraph, and the agent rules'
`38,00 zł` example, which now disagrees.

**Calls made here, open for the product owner** (design-system Part 16 has the drawing's): the row
order above; the IN tag drawn as a green fill (the mocks' pixels) where A2.3's words say _outline_;
the rescue ribbon in `coralInk`; the cap's two lines the mock does not draw (_next week_, _this week
and next_); `DECK` as the intent's surface. **Not built, and whose**:
a tile flipping to In while the card is on screen (the read is re-asked on
focus and after answers, never polled — a live channel is not specified). **Nothing here has been
seen on a device.**

**The countdown runs from the read.** The deck's read carries no `read_at`, so the countdown starts
from the moment it was received (`dataUpdatedAt`) and, while a card on the deck counts down, the
deck's clock ticks every thirty seconds (`useDeckClock`) — so _45 min_ moves, and a card at its
deadline leaves silently rather than lingering until the next read to be refused as over. A drawing
and never a decision: the server stays the authority on whether a game is over. **The details'
answers are the read's `actions`** (#557), not a flag of the screen's, and their DAY carries the
date — _Saturday_ over _3 Oct_, _· next week_ from seven days out (A4.1). **The weekly cap's line sits
under the switch**, above the deck (A1, A2.1). _Book it now_'s court block has a solid **green**
border — the tag's own — and _Booked_ keeps `voltStroke`. The game card's three corals are recorded
in the design system's §1.2 as meanings it already had (a stroke is _where_, a `coralInk` fill is
attention). **Owed to the backend**: a distance for the details' WHERE (A4.1 draws _3,1 km_; a deck
card carries none).

**Games & money and the live yeses are this feature's** ([#554](https://github.com/Raketa02/Raketa/issues/554);
the screens A7.1, A7.3; mocks 37–39, 48). Both are the backend's Proposals context — Games & money is
its second aggregate (#539), and a live yes is a yes on a game still filling — and the deck is what
both bound: games per week decides which weeks a deck deals into, and the ceiling which cards it
deals at all. So the feature holds the two reads (`useGamesAndMoney`, `useLiveYeses`) beside the
deck's, one key factory (`proposalKeys`, renamed from `deckKeys` as it stopped being the deck's
alone), and the one write. The shell composes `GamesAndMoneyRow` first in the You tab's ACCOUNT
group, above _Payments_; its screen is `/you/games-and-money`.

**Every tap is a save, and the saves go one at a time.** No _Save_ button (A7.1): a tap writes the
pair into the read at once and `PUT`s both limits. Optimistic, against `architecture.md` Part 7's
list: nothing is charged or held — the ceiling is a preference about money, not a payment — the
answer is this player's pair alone, a refusal is rare and its rollback deterministic (the saved pair
read again), and nothing reaches another person. A read begun after a tap and answering late with
the old pair cannot undo the last save: the last answer cancels the reads before writing itself in. The saves share a TanStack `scope`, so they run
in the order tapped; only the last one in flight writes its answer into the read, a refusal with
nothing behind it re-reads the saved pair (and says why under the bound, where a note appearing does
not move the control under the finger), and once the last one settles **every group's decks are
marked stale** (`proposalKeys.decks()`). A tap steps from **the pair the last tap left**, held in a
ref until the saves settle, because the value a tap writes is drawn a tick later and two taps inside
that tick would both step from the same number; a tap that lands on that pair sends nothing. The
stepper's range and the ceilings beside _Off_ are the read's, never the client's: a key at an end
of the range is shut, and the server can offer more without a release.

**The bound is the games times the ceiling.** The row's line — _At most 4 games a week_, with _· up to
180 zł_ once a ceiling is set — and the bound under the cards — _Your bound: at most **4 games** · up
to **180 zł** a week._ — are one rule (`weeklyBoundGrosze`), and the games line turns singular at one.
The copy lives in `gamesAndMoneyCopy.ts`, import-light, because the shell composes the row at module
load and `deckPresentation`'s imports reach back into features that reach the shell.

**LIVE YESES is this feature's section, placed on Payments by its route file.** The yeses are the
deck's answers and their details are the deck's screen, and the deck will open the payment setup as
a sheet (A2.4) — so `payments` importing this feature would point the edge the wrong way.
`PaymentsScreen` takes a `liveYeses` slot and draws it in state B only (a yes needs a saved method,
and a method is not removed while a yes needs it), so state A never asks for the list. The head
counts every yes across sports, with no cap under it — the live-yes cap was removed on 2026-10-05
(the mechanics Q97); mock 48 drew _1 OF 10_ before that. A row is _Padel ·
Saturday 15:00_ in the court block's day words, the club under it, the share in grey mono; it opens
the game's details for the group, sport and kind the yes was said in. **Hidden when empty and while
the first read is on its way**; a read that failed says so under the section's name with the retry,
because a missing list would read as _nothing live_. A yes and a withdraw, wherever said, mark the
list stale (`useAnswerCard`, `useWithdrawYes`); a no never touched a yes.

**A live yes opens the game's own details.** Until #557 a live yes's row opened a view drawn from
the yes alone — the deck never deals a game the reader is In on, and there was no read of one
proposal — the club as the title and no tiles. Since #557 the details are `GET /proposals/{id}`, so
the row opens the full game: everybody In, the open seats empty, _Withdraw_. **Calls open for the
product owner**, each a Part 16 row: the live yeses' head, and the bound's limits in sans 700 (a
sentence's figures, where 1.4 sets display figures in mono). **Nothing here has been seen on a
device.**

**The moment a yes fills a game is this feature's, held above the tabs**
([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4; the mechanics §6.1, §6.5,
§11, §12.2). `FillProvider` is mounted by the shell around the stack and the bar for the session,
because what a yes sets going outlives the screen it was said on: the player swipes _Book it now_
and walks to Home inside the ten seconds, and the yes is still theirs. The deck and the details reach
it through `useFill`. It holds four things, each as component state — a card is only ever _held_,
never copied into a store:

- **The Undo window** (§6.5). A yes `waitsForUndo` — _Book it now_, and **every** rescue join (Q74) —
  flies like any other, then counts ten
  seconds under _Booking in 10 s · Undo_ (shared/ui's `UndoToast`, placed where 9.2 places a toast,
  above the bar). Its card **stays in the deck's read, hidden** while it counts, so _Undo_ deals it
  back exactly where it was; at zero the card leaves the read and the yes is sent **now or not at
  all** (`networkMode: 'always'` — a booking that landed on a reconnect the player never saw is worse
  than a sentence). **One counts at a time**: a second yes that would move money springs back with
  _One booking at a time_, so no two windows overlap — every other answer goes on. A yes said again
  after a setup the server asked for counts its ten seconds again (`yesAgain`): money moves only
  after ten seconds of _Undo_. The details' _I'm in_ is busy _Booking…_ while its own yes counts.
- **The setup before a first yes** (§6.1, §12.5). With nothing saved a yes opens payments'
  `PaymentSetupSheet` instead — the card springs back — and lands once the method is saved, through
  its ten seconds if it is a yes that waits; closing drops it. `payment_method_required` from the
  server, when the method had not been read, opens the same sheet.
- **Every yes's answer** — the deck's, the details', the delayed send's and the confirmation's — is
  read by `fillOutcome`: **booked** re-reads every deck, the live yeses, Home's games and the
  receipts, sends a details screen still on screen back to the deck, and raises **It's a game!**; a
  game **waiting for one payment** raises it too, with its line (#630, below); a **refused share** (the bank's check, a decline) says _Your payment didn't go through — confirm it
  to keep your seat_ and opens the confirmation on it; no method at the fill is the setup and the yes
  again; a new card brand names You › Payments; anything else is a vote. A yes the card called free
  can still be the last — the others got there first — so the deck's plain yes is read too.
- **It's a game!** is the yes screen's third face (ADR-0167): its ground, entrance, tiles, `vs`, word
  role and pills, its own since #574 (`YesGround`, `YesEntrance`, `YesTile`) — the faces are **the card the yes was said on**, its
  rows the sides the booking drew, photographs and all, so nothing is read. An overlay on
  `ModalStage`'s top layer over the whole phone, not a route: it answers wherever the player is ten
  seconds after the swipe, and a route could not carry a card. _Open game_ lays Home down
  (`landOnHome`) and pushes the game, so back is Home; _Later_ and Android's back leave the player
  where they were.
- **The confirmation** (`ConfirmPaymentSheet`, §12.2): the share and the seller, the game, one line —
  the bank's check over the card on file, or another card in the provider's fields for a decline —
  and one button. Payments' `useConfirmOnPhone` confirms on the club's account; then `POST
/seat-charges/{id}/confirmation` is the yes again, and its answer goes through `fillOutcome` like
  any other: booked is _It's a game!_, held with another seat still open closes the sheet with
  _you're In again_, refused at the bank once more keeps it. Every refusal — the bank's or the
  server's (not confirmed yet, the seat taken, the game over) — is said **in the sheet**. A plain yes
  refused `payment_to_confirm` opens it on the payment the refusal names, and so does a row of
  _TO CONFIRM_.
- **TO CONFIRM** (`PaymentsToConfirm`, `GET /players/me/payments-to-confirm`): the way back for a
  player whose share was refused **while they were elsewhere** — somebody else's yes filled the game.
  Placed above _LIVE YESES_ on Payments' state B by the route file, as _LIVE YESES_ is; a row is the
  game as a live yes draws it, with **Confirm**. No card is held there, so a confirmation that books
  the game draws _It's a game!_'s faces off the booking (#630, below), and says _It's a game! You'll
  find it in Home._ in a toast only when that read fails. A booking, a confirmation and every yes that
  answers _confirm_ re-read it.

**The rules are the domain's** (`domain/fill.ts`): `waitsForUndo`, `fillOutcome` over a yes's
answer, `fillRefusal` over a refused yes (`payment_method_required` → the setup,
`payment_to_confirm` → the confirmation), `itsAGamePicture`. The provider reads one outcome in one
place (`act`). The fill's contract is `hooks/useFill.ts`, and `useFillYes` binds it to a screen, so
the deck and the details say yes the same way and keep only what differs — the deck's card flies,
the details mark the yes in place and leave once it books. **The shell hands in `openGame`**: this
feature never imports the shell that mounts it.

**Calls made here, open for the product owner** (Part 16 has the drawings'): _It's a game!_ as an
overlay rather than ADR-0167's route; **a yes on a card the deck called a free vote, that turns out
to be the last, charges with no Undo** — the phone cannot know it fills until the server says so,
and holding every yes ten seconds would delay every vote (the backend could refuse such a yes and
ask for the Undo; a ruling either way); one booking window at a time; a booking said on the details
leaving them for the deck; the delayed yes and the confirmation sent now-or-not-at-all where the
deck's answers wait for a connection; no method at the fill opening the setup (the terms needing
acceptance only a toast); the confirmation's _you're In again_ toast; a declined share paid with a
card typed for it alone, the saved method unchanged; _TO CONFIRM_ on Payments (no spec draws it — the
way back until Home and the notices, #556 and #559); and a confirmation from it saying _It's a game!_
in a toast (since #630 the screen, drawn off the booking).
**Owed**: the backend's laptop provider never confirms a payment (payments.md). **Nothing here has
been seen on a device.**

**Home's booked games and a booked game's details are this feature's**
([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, A4.4, A8; the mechanics
§11.4, §14). Two reads, both #542's and both the backend's Proposals context: `GET /home` (the
reader's booked games, soonest first, the ended ones too, and Home's badge) and `GET /bookings/{id}`
(one booked game in detail). `useHome`, `useBooking`, keys
`proposalKeys.home()` and `booking(id)` (under `bookings()`); rules in `domain/home.ts`, words in
`homeCopy.ts` and `homePresentation.ts`.

**Home is one rail, and the rail is `plans`'.** A8 says _today's Now rail of game cards, renamed_, so
a booked game is a card on that rail rather than a second list: the shell fills the rail's `booked`
slot with `useBookedCards` — the cards at the rail's width, how many, a failed read, and **the Games
they stand for**. A booked game's Game is in `GET /games` too, so the rail leaves every one of them
out of its own cards and `useGamesNeedingYou` leaves them out of the Classic half of the badge; the
bar's Home count is the two halves added (`useHomeBadge`: the server's `needing_you`, which counts
the cards that need you and every payment to confirm). Booked cards come first, in their read's
order. **_TO CONFIRM_ is on Home too**, above the rail: the badge counts a payment to confirm, and a
count with nothing on the tab to answer it would be a dead end.

**A card is the Now card's shell with a booking's content** (`HomeGameCard`): the status as a grey
tag with the status's dot, _New_ until opened, the sport word; WHERE (club + court), DAY and TIME on
the status's accent line beside the others' faces; the money line (`moneyLineOf` + `moneyWords`, the
mechanics §14.1's table); _Open game_, which pushes the details over Home. **Every fold runs on the
read's clock** (`useReadClock`: `read_at` moved on by how long the phone has held the read, ticking
while a cut-off is ahead), so the cut-off's clause — _free to leave until Fri 16:00_ then, _27,18 zł
back if you leave by Fri 16:00_ since #618, and _free to leave until_ again since #642 (both below) —
leaves the line at that instant by itself. **An ended card stays a day after its hour** (`onHome`) — the wire dates no ending of a
booking, and the hour's end is the one instant every ending has.

**_New until opened_ is kept by the phone** (`useOpenedGames`, the fourth value of
`shared/lib/preferences`, per account and forgotten at sign-out): the booked games whose details
this account has opened, pruned to Home's own read. A game is new while it is waiting, booked or a
seat is open and has never been opened here; nothing is new until the phone has said, so the tag
never flashes. Opening the details — from a card, or _It's a game!_'s _Open game_, which now opens
them rather than the Classic game screen — is what marks it.

**The details are one read and nothing re-derived** (`BookedGameScreen`, `/booking/[bookingId]`): the
top bar (the others' faces, their names whole, _Padel · booked_, **Chat**); the game card — status,
tiles with _2,71 · paid_ (`GameTiles` draws _paid_ where a filling game says IN), the vs line, WHERE
with the court and the distance, DAY, TIME to the read's `ends_at`, and the money row
(`moneyRow`); once the hour has come, today's **We played** / **Confirm the result**, which opens
today's game screen at the Game the booking opened (`BookedGameResult`, `/booking/[id]/result`:
`GameScreen` with the score leading and its three Classic slots empty); and the Game's own
forecast (`games`' `GameForecast`) while the booking says to draw it. The filling details and the booked ones share `GameFacts` and
`OthersFaces`.

**The chat is reached from the details** (A4.4, §14.3) — and, since #619, from the Home card's
bubble too (Q100, below). _Chat_ is drawn while the
join keyed by the booking finds the room (`conversations`' `useBookingRoom`, by the booking the room
is filed under since [#577](https://github.com/Raketa02/Raketa/issues/577)) and the status can have
one (`chatIsOpen`: not before it is booked, not once called off). **The room's own life decides
the rest**: it closes as today — 48 hours after _we played_, when the result window closes — so a
counted game keeps its door for as long as its room does, rather than leaving a room open with no
way in. It pushes `/booking/[id]/chat` (`BookedGameChat`), which mounts `ConversationScreen` in its
booked form — no plan card, no plan chips, no _Details_ door, the header's second line the booking's
word — over the details, so the back chevron returns to them; the bar stands down there as in every
room. Before there is a game or a room to draw, the details, the room and the result say the same
four things (`BookingAbsent`): offline it resumes, the spinner, a refusal with the retry, or the one
terminal sentence.

**Calls made here, open for the product owner** (Part 16 has the drawings'):

- **The Home card's bubble is a mark, not a door.** The ticket asks for _the chat bubble_; A8 and
  §14.3 say a Home card has no chat door. It says the game's chat is open, silent, its words in the
  card's spoken name. **Ruled otherwise by Q100** (2026-10-09): the bubble is a door — #619, below.
- **_Chat · n_ has no number, and is always volt.** No read carries an unread count; the number and
  the lit-when-unread state are owed to the backend.
- **_New until opened_ is the phone's memory** — a fourth value in `shared/lib/preferences`, which
  **ADR-0188 §5 says is a new record, not an edit to its table**, and the value is a record of what
  was opened rather than a choice. Decide: a new ADR admitting it (a root session writes it), or
  _new_ held for the session only, or a server-side _seen_. A reinstall, a second phone or a
  sign-out shows every live game as new once.
- **_Chat_ follows the room's life, not the result** (§14.3 _closes as today_), where A4.1 says
  _while the game isn't over_ — the details were then the only way in, so a door that went at the
  result would leave a room nobody can reach. Home's bubble (#619) follows the same life.
- **The title names the others whole** (_Piotr Sowa, Inés Díaz, Bartek Lis_), where details 7 draws
  first names: ADR-0171 — a name is said whole, never a first name derived from it — as the filling
  details already do.
- **Booked cards first on the rail**, Classic cards after; one heading counts both.
- **An ended booking stays a day after its hour**, so a result settled later than that is not drawn
  (the Classic rail's own cost for a score counted by silence).
- **_Seat open_ and _Called off_ said their lines from what #556 had** — the seats counted off the
  sides, no reason; since #557 both are the read's (`open_seats`, `called_off_reason`,
  `refunded_grosze`), below.
- **The result is today's screen**, opened from the details by _We played_ / _Confirm the result_ —
  no mock draws where the act sits on a booked game.
- **_TO CONFIRM_ above Home's rail**, because the badge counts it.
- **The status colours**: amber for waiting, a seat open and the two result acts; mint for booked
  and counted; `gameRed` for called off.

**Owed**: the record for the fourth phone value (root, above); the unread count for _Chat · n_
(backend); with Classic play on, the Chats tab
lists a booked game's room and opens it in the Classic form, plan card and _Details_ included
(#542's call 8 — the shell could leave booked rooms out of Chats, or open them in their booked
form); `CLAUDE.md`'s _three per-account choices_ now reads four (agent config, left for the
user). **Nothing here has
been seen on a device.**

**Fill in, rescues and leaving are this feature's**
([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3, A4.2, A4.3, A8; mocks 2,
11–14, details 10; the mechanics §10, §11, §13, §14; the backend's #544, #545). Four reads,
each the server's whole answer: `GET /pools/{id}/fill-in?sport` (_Seats to fill_ and the tab's
badge), `GET /proposals/{id}` (a game still filling, in detail), `GET /bookings/{id}` (a booked game —
now also seen from outside) and the live yeses; and three writes, `POST /bookings/{id}/seats` (take a
rescue's seat), `POST /bookings/{id}/no` (a no to a _Seat open_ card) and `POST
/bookings/{id}/departure` (_Leave the game_). `pnpm gen:api` brought every field the backend added
since #556.

**The Fill in tab is `FillInBoard`**, drawn by the group page (A3). _Seats to fill_ is the board read:
only rescues — booked games that lost a player, the reader fits and is free for — soonest first, each
leaving at its deadline on the read's clock (`standingSeats`). A row (`SeatToFillRow`, framed `coral`):
_Padel · Saturday 16:00_ (_· friendly_ for For fun), the club and, bold, _fills by Fri 16:00_ before
the cut-off or _offered until the start_ after it — the read says which; the players' posters (a hold
opens the record), a dashed **?** per open seat, and a volt **I'm in · 27 zł**. _You're In_ is the
reader's live yeses in this group and sport (`yesesIn`); a row (`YoureInRow`, framed `mint`) is the
yes's game, club and _book by Sat 13:00_ with **its squares read off the game's own details**
(`useProposal`: everybody In, then the open seats dashed) and _Withdraw_ **only once those details
say the reader may** (`mayWithdraw`) — so it is hidden while the full game waits for one payment,
when the `actions` hold _Leave_ instead, and before the read lands: a withdrawal then is a departure,
with no sheet in front of it. One read a row, because the live yes does not carry who is In.
Each row's upper block opens its game. Sections only when they have rows; with neither, the group's
starting card. The tab's badge is the read's `badge`, filed under the group's root
(`proposalKeys.fillIn`), so every answer in the group and every changed limit re-reads it.

**A rescue is a card the deck already drew, now answered at its booking.** A _Seat open_ card's id is
its booking's (#545): the yes is `POST /bookings/{id}/seats` and the no `POST /bookings/{id}/no`
(`answerCard`'s `rescue`, read off the card by `isRescue`). The card draws the players _paid_, **the
reader in the seat that opened as a dashed volt tile** — _You complete it_ over _27 zł · court booked_
on the last seat, _You?_ over _27 zł_ while more are open (`GameTiles`' `rescue`) — and the court's
number on the court block (`courtName`). Every rescue join counts its ten seconds (Q74), pays, raises
_It's a game!_ and lands in Home; **a lost race is `seat_just_taken`: _Someone just took it._**, and
the card or row goes (`refusalOutcome` lets every rescue refusal go: taken, off, started, not offered).
**The fill holds what a yes is said on, not a dealt card** (`YesOn`: the id, the type, the court, the
sides when the surface has them) — a _Seats to fill_ row holds no sides, since it lists the players
and not which side the open seat is on, so _It's a game!_ then observes the booking's own read (the
overlay's `useBooking`, for as long as it waits), the seat taken, and draws its sides once it lands;
a read that fails says it in a toast. Each of the tab's reads is its own section's: one held offline
says it resumes and one refused says why with the retry, in its section's place, never hiding the
other's rows; the starting card only once both have said there is nothing.

**A rescue seen from outside is the booked details' third reader** (A4.3). The card's **i** and a
row's upper block push `/play/group/[groupId]/rescue/[bookingId]` — under Play, so _back_ is the
group — which mounts `BookedGameScreen` with `offer`: the read carries `rescue`, and the screen draws
the players _paid_, the reader's dashed seat, WHERE with the court, the share with how long the seat
is offered, and a volt **I'm in · 27 zł** (`TakeTheSeat`, the row's door too; spoken by what the share
does since [#645](https://github.com/Raketa02/Raketa/issues/645), below) — no Chat, no Leave, no
_new_ marked. A seat gone before the read says _This seat isn't offered to you any more._

**_Leave the game_ is at the foot of a booked game's details** (A4.1, details 10; §13), with the line
saying what leaving costs **now** — the read's `leaving`, folded by the server — and today's _Before
you leave_ sheet (`LeaveSheet`, this feature's since #574) with the §13 words: _You'll be refunded 27,18 zł now (the
0,82 zł card fee isn't returned)…_ before the cut-off, _…when someone takes it; if nobody does, you
won't be…_ after it, _Nobody has paid yet. Leaving withdraws your yes._ while one payment is awaited (since
#642, _Nothing is taken…_ before the cut-off and no figure after it, below). The
door is `LeaveTheGame`, the group exit's shape: the sheet is the surface while the act is in flight
and says a refusal in words; success is a toast — with when the refund landed (_BLIK within hours,
cards up to two weeks_, §12.3) until #642 made it _Nothing was taken._ — and the leaver goes back to
Home, which no longer holds the game. No
button where the read gives none (the hour has come, the game is over). **The same door stands on a
full game while it waits for one payment** (#625), sent as the withdrawal (`useLeaveWhileWaiting`,
`DELETE /proposals/{id}/yes`), and the game fills again.

**The filling details are `GET /proposals/{id}`** (A4.2; owed by #556). The status tag — _Filling · 2
of 4 in_, _Waiting for one payment_ amber, _Booked_, or how it ended unfilled — WHERE with the distance
and no court, the share with _if it fills · book by_ or _Waiting for one payment · until 14:40 · Nobody
pays until it's in_, the forecast, the grid, the paragraph while it fills, and **the actions the read names, in its order**:
_I'm in_ / _Not this time_, _Withdraw_, _Leave the game_, _Confirm your payment_ (the fill's
confirmation, on the payment the read names). Nothing about the game is held by the screen: every
answer re-reads the details (`reread` takes `proposalKeys.proposals()`), each button busy until the
read lands. **The one fold**: whether a yes from the details books, which a card carries and the read
does not — the deck's own rule read off the seats and the In count (`courtOfDetails`: the last seat is
_Book it now_).

**Home's and the details' lines are the read's now** (§14.1): _2 seats open · fills by Fri 16:00 or
the game is off and everyone is refunded_ (`open_seats`; _…and nothing is taken_ since #642), _1 seat
open · offered to others · the game goes ahead_ after the cut-off; _Called off_ with why — _A seat was
still empty at the cut-off_ — and what came back (_Refunded 28 zł_, `refunded_grosze`) or _Nobody paid_ (or _Nothing was
taken_, since #642); _Uncounted_ with _A seat was empty · no Level moved_ — on Home's
card, and under the share on the details' money row (`moneyRow`). A booking
waiting for one payment has no Game yet (`gameId` absent): no room (and `chatIsOpen` keeps its door
shut, since #577 finds a room by the booking), no forecast, no result, and it is not
in the Classic half of the badge.

**Calls made here, open for the product owner** (Part 16 has the drawings'):

- **A row's faces are read after the seat is taken.** _It's a game!_ from a _Seats to fill_ row reads
  the booking first — the row cannot say which side the open seat is on — so it lands a read later
  than from a card, and a failed read says _It's a game!_ in a toast.
- **_You complete it_ on a rescue's details too**, where A4.3 words the tile _You?_ — the card's own
  rule (A2.3: the last seat completes it), so one seat says one thing on both surfaces.
- **_Leave the game_ and _Withdraw_ are 6.1's `secondary`**, where details 10 and mock 13 draw dark
  red text: the group exit's call (red is _ended badly_, 1.3), and the sheet is what makes it
  deliberate.
- **The rescue row's coral frame** is the rescue ribbon's meaning (§1.2).
- **Short day names on the rows** (_book by Sat 13:00_, _fills by Fri 16:00_) where mock 13 spells
  _Saturday_ — the money line's and the details' own form.
- **The leaving toast** says when a refund lands, as §12.3 asks of the moment a refund is issued.
- **The details' ended statuses' words** (_Didn't fill in time_, _Taken back_, _No court left at that
  hour_) — no mock draws them.
- **A game the details read as `FILLED`** says _Booked_ and offers nothing: the details have no
  route to Home's screen; Home holds the game.
- **_Confirm your payment_ on the filling details** — A4.2 lists _I'm in_, _Not this time_,
  _Withdraw_ and _Leave_; the read's `actions` add `CONFIRM_PAYMENT` while a refused share waits, and
  an action the server offers with no door would strand it. It opens the fill's confirmation.
- **A booked game that started short** has its own end on the game screen (`games`' `started-short`,
  _A seat was empty._): the contract added `STARTED_SHORT`, and a standing with no arm fails the build.

**Owed**: the chat lines _Kuba left — the seat is open_ / _Ola took the seat_ (conversations, with the
backend's #545 note); the push and in-app notices of a seat opening (#549, #559); _+ Post a game_
enabled (#558, below). **Owed to the backend**: ~~a `called_off_reason` for the club's own cancel and
for a full game a player left~~ — both came: the club's cancel is `CANCELLED_BY_THE_CLUB` (#547), and a
full game a player left is no longer called off but stays on the others' Home as _Seat open_ (#624,
#629, below); and who is In on the live yes, which would save _You're In_ its read a row. **Nothing here has been seen on a
device.**

**Posting a game is this feature's** ([#558](https://github.com/Raketa02/Raketa/issues/558); the
screens A5; mocks 14–35; the mechanics §9; the backend's #546). Three routes, all the backend's
Proposals context: `GET /pools/{id}/posting-grid` (one week of WHEN for what the controls ask),
`GET /pools/{id}/posting-grid/slot` (a cell's sheet) and `POST /pools/{id}/posts` (_Post — you're
In_, the poster's yes). `pnpm gen:api` brought them; `Who` is spelled in `domain/vocabulary.ts` and
held to the wire in `mappers/wireVocabulary.ts`. Rules in `domain/posting.ts`, words in
`postingCopy.ts` and `postingPresentation.ts`, reads and the write in `hooks/usePosting.ts`, keys
under the group's root (`proposalKeys.posting`), so every answer, join and post in the group — and
a changed Games & money — re-reads the grid and its sheet with the decks.

**The screen is `PostAGameScreen`, mounted by `groups`** (`PostAGamePage`, `/play/group/[groupId]/post`)
because only the group knows what it hands in: the sports the reader may post in here (the page's own
filter — rated in, among an official group's declared ones), each with how many members are rated in
it (_Padel 10_, the roster's count), the sport the page is on and the kind its switch stands on. The
edge still points one way. **The draft is a feature store** (`store/postDraft.store.ts`): the four
controls, the week shown and the pick, kept while the player stays in the group and forgotten when
the group's page goes (`forgetPostDraft`, called by the page) and after a post. The sport and the
kind are absent from the draft until chosen, so the page's sport and **the player's intent** — the
switch's kind as the deck corrects it (`useGroupDeck`'s, a read the page has made already) — stand in
without being frozen before the read lands.

**The controls** (A5.1): SPORT a row of chips with the sport's dot and its count; KIND Competitive /
_For fun · friendly_; WHO Anyone / Men / Women / Mixed pairs, **Mixed pairs only in doubles** (read
off the court's seats, `courtSeatCount`) and taken back to Anyone in a sport played one a side;
LEVEL two steppers (Games & money's `Stepper`, moved out of its screen into the feature's
components for both). A sport chosen puts the level range back to the engine's and clears the pick
(`withSport`; pressing the sport already chosen does nothing); **a kind chosen re-seeds the range
too** (`withKind`) — the engine's window is the kind's, and a bound narrowed inside one may lie
outside the other. **The draft holds the narrowed bounds in whole hundredths** (`Narrowing`, each
absent while it stands at the engine's), so nothing drifts, a bound left at the engine's is sent as
nothing, and **the ask never needs the engine's window** — only the steppers read it, off a grid that
is always this sport's and kind's. Inward narrows; outward comes back to the engine's bound and
**bounces** past it — the stepper's box nudges and _You can narrow it, not widen it_ is said and
announced — and a key that would turn the range inside out is shut. A refused range
(`level_range_too_wide`, `_inverted`: the window moved under the draft) goes back to the engine's by
itself. The sport the draft falls back on, and _Mixed pairs_ read as _Anyone_ one a side, are the
domain's (`draftSport`, `draftWho`).

**The grid is the server's** (A5.2): every count, colour and flag is the read's, and `cellFill`
only names which of the five fills it draws — dead, few, enough, thin, hot — with outside your hours,
past, the pick and happening drawn over it (`PostingCell`; the look is the design system's 7.28).
_5+_ past five. The last answer stays drawn while the next is read, **within a sport, a kind and a
week** (the query's `meta`), so a stepper's taps do not blank the grid, a padel cell never sits under
a finger reading as tennis, and the steppers never step against the other kind's window. Week one starts today; the pager is shut at each end of the fortnight.
**The ⓘ is 7.6's popover**, widened for _How to read the map_'s six rows, the happening line as A5.2
rewrote it. A read refused for who it is for (`who_leaves_you_out`) says so in the grid's place; any
other refusal the shared retry; offline, the amber _resumes_.

**A cell's sheet** (`SlotSheet`, A5.3) opens on every cell but one earlier today — a dead cell's says
_Nobody who fits is free then_, a courtless one _No court is free then — every game needs a court._
— and is read for the controls the grid was read with: the headline (_5 of your best fits free
then_, _only 2 fit · may not fill_ where a court is free and fewer than a full game are, each with
_· outside your hours_), the fits (7.16's card panels, the name whole, _2,75 · 93_), the free courts
home club first with their own _4 free_, and **Already happening here**: rescues (_I'm in · 30 zł_)
then posts still filling (no court number, _I'm in_). **A court tapped is the pick**, replacing the
last, and the sheet closes so the ringed cell and the open button are what follows; on the picked
cell the row says so and _Remove this pick_ sits at the foot. **A court nobody who fits is free at is
shut** (`courtPickable`, §9.1 step 5's _nobody who fits free: cannot be picked_): the slot lists every
free court hour of the range whatever the fits, so a dead cell's courts and a _0 free_ row are drawn
and cannot be picked. **The pick holds only the choice** — the day, the range, the club's id and the
hour — and the club's name and the share under the button are read off the pick's slot again
(`usePostingSlot` for the pick's cell, the sheet's own cache entry), so nothing the server said is
copied into the store. **A fit opens their record in the
sheet's place** — two sheets are never up at once, BuilderScreen's rule — and closing it brings the
sheet back.

**Joining from the sheet is the fill's** (`useFill`, `useFillYes`): the sheet closes first, so the
payment setup never opens over it; a rescue counts its ten seconds behind _Undo_ and pays, raising
_It's a game!_ off the booking's read (a sheet's rescue holds no sides, as a row's does not); a
post's _I'm in_ is `POST /proposals/{id}/yes` — a free vote, or **on its last seat a _Book it now_
behind the ten seconds**, as on a card (`yesOnPost`, read off the seats as the details' rule is) — and
a refusal is the deck's toast (`post_not_open_to_you`
has words now). Then the player goes back to the group's page, the toast following them there.

**Post — you're In** (A5.4) is shut until a court is picked, with _Pick an hour with a court on the
map first._ under it; once picked, the line says the post (_Saturday 17:00 · Ogrody 33 · 27 zł each
if it fills_). With nothing saved the setup opens (the fill's) and the post goes once a card is; a
guard the server answers with is said in the helper's place, announced, **for the pick it was said
about** — a new pick, a removed one or a new sport clears it: `payment_method_required` (and the
setup), `live_posts_exhausted`, `games_per_week_booked`
(the week), `you_play_then`, `nobody_fits_then`, `court_hour_not_for_sale`. Posted, the draft is
forgotten, _Posted — 5 of your best fits have it._ is toasted, and the player is back on the page on
**Fill in › You're In** — the page turned to Fill in under the screen when it opened
(`groups`' `groupTab.store`), so every way back lands there. A post settling after the player has
left does not pop the page as well. Not retried: a second post is a second game. **No
`Idempotency-Key`**: the button is busy while the post is in flight, and the server refuses a second
post at an hour the poster already plays (`you_play_then`) — so a duplicate is refused, never booked. **Challenge cards**
(_Kuba Wiśniewski challenged you_, _The group challenged you_) are #553's and unchanged; the suite
`groupGames.test.tsx` holds them, and the post's own walk is `postAGame.test.tsx`.

**Calls made here, open for the product owner** (Part 16 has the drawings'):

- **The figures on the grid's greens are each green's ink, not white**, and the hot cell is
  `mintInk` with white rather than `mint` — white is 1,51 and 2,15 on the two middle greens and Rule
  C refuses it on `mint`. Two inks were added beside the two greens; no soft or line.
- **The happening dot is `coralInk`** (coral's meaning: a game you could join), ringed in white.
- **A kind re-seeds the level range**; A5.1 says only that a sport does.
- **The pick stays when the kind, who or level changes** — the court is still free; the grid says
  whether anybody fits it now, and the server's `nobody_fits_then` says it at the post.
- **The line under the button says the pick** once there is one, where mock 15 draws only the helper.
- **An outward press moves a narrowed bound back toward the engine's**, where A5.1 says _move a bound
  0,05 inward only_ — otherwise a mis-tap could not be taken back; past the engine's bound it bounces.
- **Joining from the sheet leaves for Fill in** at once (a post's free yes, a rescue's ten seconds
  running over the page); with the setup in front, only once a method is saved.
- **_Posted — 5 of your best fits have it._** — no spec words the moment after posting.
- **The legend's _Got it_ is the popover's close**, and its first line says _a club has a court_
  where the mock says _the pool_.
- **Short day names on the sheet's courts** (_book by Sat 15:00_) where mock 34 spells _Saturday_ —
  the Fill in rows' call, kept.
- **_any level ✓ · you are free ✓_ on every happening row**, as A5.3 words it: the read lists only
  games the poster fits and is free for.
- **The draft is forgotten after a post**, and when the group's page goes (back to Play, or the
  tab bar laying the stack down).

**Owed**: CONTEXT.md's Post into Part 1 and the ADR-0189 §5 amendment (root, #546's); _Your post
didn't fill_ (#549). **Nothing here has been seen on a device** — the cells' looks, the bounce, the
legend's width and two sheets swapping in one tick on iOS least of all.

**Somebody didn't come — the booking hands the Game what it knows, and Home says it**
([#560](https://github.com/Raketa02/Raketa/issues/560); the backend's #547; the mechanics §15.3).
`BookedGameResult` composes `games`' result screen with `booked`: `useRereadBooking` — Home and
this booking read again once a score, an agreement, a mark or a dispute lands, so the status, the
bar's badge and the door under the screen follow at once. The result entry then offers _Kuba Nowak
didn't come_ for every other player (`games.md` has the screen). **The player marked finds it on Home**: an uncounted card with
`uncounted_reason` `NO_SHOW` says _You were marked as not coming · say so if you were there_ while the
read says it needs them, and _Somebody didn't come · no Level moved_ to everybody else (`MoneyLine`'s
`noShow`, the details' money row too); `resultActOf` takes the game now and opens **Say you were
there** on the details for that player alone, onto the result screen where _I was there_ is
pinned. **gen:api** also brought #547's club cancel: `CANCELLED_BY_THE_CLUB` with
`club_cancel_reason`, said _Bonarka Arena cancelled it because of the weather · Refunded 30 zł_
(`OTHER` names no reason) — no player ticket held those words, and the `Exact` assertion demanded
them. The walk is `noShows.test.tsx`.

**Calls made here, open for the product owner**:

- **A sheet stands in front of the mark** — the mechanics say players _can tap_ _Kuba didn't come_;
  a mark that can become the strongest on a record is never one tap away here.
- **Marking goes on while a report's day runs**, for whoever nobody marked — two players can fail
  to come to a doubles game. The backend takes a mark until the entry window closes, and that window
  is off the wire once a report is made, so a mark past it is refused and said so (_too late to mark
  anybody else_) rather than withheld.
- **The dispute is two doors deep**: Home → the details' _Say you were there_ → the result screen's
  _I was there_, where the clock of the day is. The Home card is not a door (A8).
- **Home cannot tell the player marked once their day has passed** — the read's _needs you_ is the
  only sign — so the card then says _Somebody didn't come_ to them too.
- **Nobody else gets a door back to the report** from the details once it is made: the reporter
  reads it on the result screen they marked from, and Home's line after that.
- **A game every report was disputed on reads as today's unscored evening** (_No result_), the
  backend's `UNSCORED` — nothing says a report was made and fell.
- **The club's three reasons are said as clauses** — _because of the weather_, _for a court repair_,
  _after a double booking_ — where §16.9 lists the club's words for the dialog.

**Owed**: the push and in-app notice for a report and for the club's cancel (#549/#559). **Nothing
here has been seen on a device.**

**A notice opens the deck at its card** ([#559](https://github.com/Raketa02/Raketa/issues/559); the
screens A9). `GamesDeck` takes `onTop` — the card's id, handed down by the group page from its route —
and draws it first while it is dealt, the rest in the order dealt (`withOnTop`, pure and tested); once
it is answered, filled or gone the deck is the server's order again, with nothing said about it. Two
exports cross for the notices: `gameRoute`, so a notice about a game still filling opens the details
the deck's **i** opens, and `proposalKeys`, so a tap re-reads the read behind the screen it opens and a
push arriving re-reads Home's — `paymentKeys`' reason. The record is
[`notifications.md`](notifications.md).

**Home is this feature's rail now, and the old loop's exports went** ([#576](https://github.com/Raketa02/Raketa/issues/576)).
`HomeRail` is Home's whole rail — the heading's count (`gamesHeading`, `YOUR GAMES · n`), the pager
and its dots, the empty sentences the shell hands down and the error note — over `GET /home` alone:
the old loop's rail that took the booked cards as a slot, and `useBookedCards` with its `gameIds`
for leaving booked Games out of it, are gone, and `useHomeBadge` answers the count to draw (or
nothing at nought). #556's owed item about a booked room in the Chats tab closed with that tab.
**What #574 crossed only for the old loop is no longer exported**: the deck's stage and answers,
the ball, the declaration interstitial and its words, the yes screen's three parts and the leave
sheet are this feature's internals again. **The interstitial has one caller**, so Find a game's
`SEARCH_SWITCH`, its line (`DECLARATION_BODY`) and the two props that let two callers differ
(`declaredOn`, `refusalMessage`) went: it reports `DECK` and says a refusal in the app's recovery
sentence. **The deck's stage still takes its stamp words and labels from its caller**, a seam cut
for two decks with one left; folding them in is left for a ticket of its own. `theFill.test.tsx`
asserts the fill marks the games list stale rather than counting a re-read, since nothing holds
that list on the group page any more.

**What Home is sent, and every money row's words under the figure**
([#615](https://github.com/Raketa02/Raketa/issues/615); the backend's #613; the mechanics §14.1, the
screens A4.2 and A8). Either details' money row draws the card's line word for word, on a line of its
own under the share: the booked details opened from the card, and the filling details opened from a
_You're In_ row (`GameFacts`' `below`). It first ran on after the figure, so the card and its details
said one thing two ways; the user ruled it under the figure, as Home draws it (2026-10-09). **Every
booked money row has drawn its words under the figure since** — _PAID 40 zł_ over _Paid · 38,40 zł back if
you leave by Wed 19:00_, the seat open, why a game is off, the rescue's _fills by_ — the user's
ruling of 2026-10-10, so the row reads the same way whatever the game's state. A booked game's line
there is the Home card's without the figure the row already draws: _Paid_, then what comes back
while the cut-off is ahead, so _Paid_ alone after it; _your share · to the club_ went the same day.
The spoken row is label, figure, then the words. **No screen shows a deadline that has passed**: the
phone drops one at `now`, as `cutOffAhead` drops the cut-off, and the read's clock ticks while one is
there (`lineCanRunOut`), on the 30-second tick the cut-off's clause already runs on, so a passed
deadline can stand for up to that long. **The time is Warsaw's** (`deadlineWords`): the hour alone on
the read's day, else the weekday with it (_Sun 00:15_), the form of the cut-off's _Sun 17:00_. **Home
is sent only what it draws** since #613 — live games,
games that ended less than a day after their hour, and any game that needs the reader — so `onHome`
no longer shelves every booking ever; it catches a card that crosses the line while Home is on
screen.

**Open for the product owner**: `onHome` stays as it was, so it still drops one card the server
sends. A report of not coming made late in the entry's day leaves its player a day to dispute it,
up to two days past the hour (#560). The server keeps sending that card while it needs them and
counts it on Home's badge, while the phone shelves it a day after the hour. Through that second day
the badge can say 1 over a rail without the card. The backend's `on_home` names this as story S-33's
(not written yet). The fix is one clause, `|| game.needsYou` — the server's own rule — and is not
taken here.

**Nothing here has been seen on a device.**

**What a leaver gets back** ([#618](https://github.com/Raketa02/Raketa/issues/618); the backend's
#617; the mechanics Q99; story S-01A's F-LEAVE-20.1). While the cut-off is ahead, a booked card's
line reads _Paid · 40 zł · 38,40 zł back if you leave by Wed 19:00_ and the details' money row
_PAID 40 zł_ over _Paid · 38,40 zł back if you leave by Wed 19:00_. **Why**: _free
to leave until_ was not true. Leaving before the cut-off is refunded less the card fee, which is
never returned (Q47 stands), so Q99 has both screens say the sum rather than a word that promised
the whole share. The wire's `money.back_if_you_leave_grosze` becomes `backIfYouLeaveGrosze`, absent
for a `null` and for an older server that sends none. `backIfYouLeaveAhead` folds it with the cut-off
on the read's clock, so the clause leaves both screens at the cut-off by itself, as _free to leave
until_ did, and is spoken as part of the line. **The figure is the server's and never the phone's**:
the card fee is the payments' estimate, and the line under _Leave the game_, the leave sheet and the
booking email give the same figure. With no figure the clause is left out — never worked out here,
and never _free_ in its place. The day and hour are written as before (`shortMoment`, Warsaw's).
The wire's `free_to_leave_until` kept its name (#617 is additive), and so did the domain's
`freeToLeaveUntil`, which is the cut-off and still drives _fills by_; nothing a player reads on
Home or the details says _free_ any more. The payment terms (`payments`' `PAYMENT_TERMS`, versioned)
still say _Free to leave until the club's cut-off — refunded minus the card fee_; they keep their
words until the lawyer's review (the spec's O3). The Games deck's _no free cancellation_, the line under _Leave the game_ and the
leave sheet are unchanged. **Reversed by Q113 and #642** (below): leaving before the cut-off is free
again, so the line says so, and the figure and `backIfYouLeaveAhead` are gone.

**The bubble opens the chat** ([#619](https://github.com/Raketa02/Raketa/issues/619); the mechanics
Q100; story S-01A's F-HOME-15.1). Marta, on the tram, taps the bubble on her Thursday card, writes
_10 min late_, presses Back and is on Home again. **Why**: the chat was two taps deep — _Open game_,
then _Chat_ — for the one thing a player does with a game on its day, and the bubble already sat on
the card looking like a door. The bubble is `ChatDoor`, the design system's 6.14 icon door: 44 pt
wide and the wide door's height, `on-dark`'s fill with its pressed shade, spoken _Open the chat_
(`OPEN_THE_CHAT`, the details' _Chat_'s name) with the glyph hidden. It pushes `/booking/[id]/chat`
straight over Home with no details under it, so **Back returns to whichever screen opened the
chat**: Home from the bubble, the details from _Chat_. The route and the screen are the same, so the
bar stands down and the Home column stays lit as before (`shellTabs`). It is drawn exactly where
the card drew the mark — the join finds the room and `chatIsOpen` allows one — so never on _Waiting
for the club_ or _Called off_. **Opening the chat from the bubble clears _New_**: the rail marks the
game opened (`useOpenedGames`' `open`) as it pushes, as drawing the details does. The card's spoken
name no longer says _Chat open_ — the door says its own name. **No count and no lit state yet**:
both come with the unread count owed to the details' _Chat · n_ (F-HOME-21.1), and the bubble then
shows the same number. **From the bubble the booking is not yet cached**, so the room waits behind
`BookedGameChat`'s spinner for `GET /bookings/{id}` — the header's second line is the booking's
word — where from the details it opens at once. **Not seen on a device**: the door's pressed shade
and its row with _Open game_ want a look.

**It's a game! marks the four matched, with what is still missing under the word**
([#628](https://github.com/Raketa02/Raketa/issues/628); the backend's #622; the mechanics Q103, the
screens A2.4). **Why**: the product owner ruled that _It's a game!_ marks the four being matched, not
only a booking that is paid. With every share held nothing is missing, and there is no line; the one
thing that can be missing is a payment (#630, below). The line is drawn in `tiny` `onDarkTiny`, the
details' role for the same words, centred under the word and rising with it, and said after the
picture in the header's sentence (design-system Part 16, 2026-10-10). It shows only to the player
whose yes filled the game; the other three are told by a notice (`notifications.md`).

**A full game that falls back stays on Home as _Seat open_**
([#629](https://github.com/Raketa02/Raketa/issues/629); the backend's #624; the mechanics Q106, the
screens A8; story S-01B's F-HOME-10.1, F-REQUEST-31.1, F-REQUEST-31.2). On Thursday at 20:40 Oscar
leaves Friday's 19:00 at Kazimierz Padel while one payment is awaited. Marta reads _Oscar Bertran left
your game — it's filling again_, and the game stays on her Home: _Seat open_ in amber, _1 seat open ·
books when it's full · nobody paid_. **Why**: the game used to leave everybody's Home while Play still
had it filling, so the notice pointed at a game Home no longer held. The wire's `filling_again`
becomes `fillingAgain`, absent on every booked game and from an older server that sends none. `moneyLineOf` reads it as a line of its own
(`fillingAgain`), never _fills by …_: nobody paid, so no cut-off applies. It is a stage of its own
in the status table (`FILLING_AGAIN`): live, with no room and no court, and never _New_. The read
says how it ends: _Booked_ once it is full again, or _Called off_ with
`BOOK_BY_PASSED` (_A seat was open past its last moment to book · Nobody paid_) or `COURT_HOUR_LOST`
(_Its court went to another game before it filled again · Nobody paid_). The wire keeps
`filling_again` on the called-off game, so the stage is _Seat open_ and the mark together
(`isFillingAgain`), never the mark alone. Home's badge is the server's `needing_you`, which never
counts it, and the card has no bubble, as on _Waiting for one payment_: the chat opens when the game
is booked.

**Its way out is a game still filling's** (#629). The details draw _Seat open_ with no court and no
Chat, and the share over the card's line. At the foot, **_Withdraw_** stands where _Leave the game_
does, since the read gives no `leaving`. It is free and never on the record, as on a _You're In_
row, with no sheet and no toast: `DELETE /proposals/{id}/yes` with the booking's id, which is the
game's (`useWithdrawFillingAgain`), then back to Home, which no longer holds the game. It is gone
once the game is called off. A refused withdrawal (the game ended, or filled again meanwhile) is
a toast, and the booking is read again so the details draw what it is now. **Every withdrawal reads
Home again** (`rereadAfterWithdrawing`), so _Withdraw_ on the game's _You're In_ row takes the card
off Home too.

**Calls made here, open for the product owner**:

- **Not _New_ while filling again**: _New_ marks a game that filled, and this one is not full any
  more. **Full again, it is _New_ only if it was never opened**: the phone keeps the booking's id as
  opened, and the wire says nothing of a second fill. Marking a refill _New_ wants the server's
  instant it filled, so the phone can keep `id@filledAt` as the bell keeps `id@givenAt` — owed to
  the backend.
- **The words for the two new endings.** The wire gives one reason, `BOOK_BY_PASSED`, both for a game
  that didn't fill again in time and for a seat that opened after the book-by. _A seat was open past
  its last moment to book_ is true of both. The notice says the first as _It didn't fill again before
  its last moment to book_. The lost court uses the notice's own words.
- **No toast after _Withdraw_**, as on a _You're In_ row: the details close onto a Home without the
  card.

**Owed by the root**: the root `CONTEXT.md`'s **Seat open** still says _decided and not yet built
(#624)_, and doesn't name the lost court. **Nothing here has been seen on a device**: _Withdraw_ at the
foot of the details, and the longer called-off lines on a narrow card, want a look.

**Time to pay, on the phone**
([#630](https://github.com/Raketa02/Raketa/issues/630); the backend's #625 and #626; the mechanics
Q109–Q112, the screens A2.4, A7.3, A8; story S-01B's F-PAY-39.1, F-EMAIL-5.2, F-FILL-35.1,
F-REQUEST-15.1). At 14:10 on Tuesday Ivan's yes fills the 19:00 at Bonarka Arena (40 zł a share), but
Paula's bank wants to check her payment. She has until 14:40, the other three holds wait, and her
seat is hers alone. **Why**: the product owner ruled that a failed card gets thirty minutes, never past
the book-by, where it used to reopen the seat at once (Q109); the market's pay windows say until when.

- **Ivan, the last yes, sees _It's a game!_** with _Waiting for one payment · until 14:40 · Nobody pays
  until it's in_ under the word. The answer to his yes carries `payment_awaited_until`, which
  `fillOutcome` reads as `paymentAwaited`; the line is #628's role (`aPaymentAwaited`,
  `itsAGameLine`), spoken _Waiting for one payment until 14:40. Nobody pays until it's in_. The time is
  the answer's, so nothing is read for it. **A refusal of his own comes first**: no screen, only his
  sheet, naming his time (`confirm` carries the `Confirmation`). **Why** (Q110): the four are matched, and
  _It's a game!_ marks that.
- **Home** draws `WAITING_FOR_A_PAYMENT` as a stage of the status table: live, _New_ until opened (it
  filled), and no room and no court, since nobody paid. Its line is
  `paymentAwaited` — _until 14:40_ only while the time is ahead, so it leaves at the deadline on the
  read's clock (`lineCanRunOut`). **The payer reads their own time first** (`yourPayment`, off
  `your_payment_due_by`): _Confirm your payment by 14:40_, on that game and on one gone back to filling
  meanwhile, whose tag still says _Seat open_. A game called off `PAYMENT_NOT_IN_TIME` reads _A payment
  didn't go through in time · Nobody paid_.
- **The payer's other places name the time too.** The details' money row says the card's line under
  the share, both on the booked details Home opens and on the game's details a notice opens. A _TO
  CONFIRM_ row says it in amber (`toConfirmRowLine`), and drops it at the deadline on the phone's clock,
  ticking while a time is there (the read names no instant of its own). The sheet says _Confirm your
  payment by 14:40 to keep your seat_, the time handed in by whoever opens it (`confirmationOf`;
  `payments.md`), and named only while it is still ahead. The booked details add **_Confirm your
  payment_** under the game card while _TO CONFIRM_ holds a payment for that game
  (`paymentToConfirmOn`), so the screen that names the time offers the act. Which times the details'
  money row names, and whether their clock ticks, are `domain/details.ts`' (`paymentDueOf`,
  `detailsCanRunOut`).
- **Paying in time shows the payer _It's a game!_** (Q110; §12.2: _you see It's a game!_). The others
  are told by the server: _booked · you paid 40 zł_ (_40 zł held_ since Q113, #637). The payer's own copy is born seen,
  because the backend records the payer as the one whose act filled it. A confirmation's booked answer
  is the fill's `booked`, drawn from the card the sheet was opened on, or off the booking for a _TO
  CONFIRM_ row, which holds no card. This replaces the toast that confirming from _TO CONFIRM_ showed,
  now said only when that read fails.
- **After 14:40** the server tells the payer their time ran out and the others that the game is filling
  again. The phone re-reads Home's two reads on that notice (`rereadHome`, `notifications.md`), so the
  others' game turns _Seat open_ (#629) and the payer's _TO CONFIRM_ row stays without a time while the
  seat is free to take back. The notice opens the game's details, where _Confirm your payment_ names
  no time.

**Calls made here, open for the product owner**:

- **_Confirm your payment_ on the booked details.** A4.1 draws no such button, but without it the
  details would name a time with no way to act on it from that screen.
- **_TO CONFIRM_'s line moved into each row**, and the header stands alone (design-system Part 16).
- **On a game gone back to filling, the payer reads _Confirm your payment by 14:40_** where the others
  read _1 seat open · books when it's full · nobody paid_. The tag still says _Seat open_.
- **The phone's clock, where no read names an instant.** _It's a game!_ writes _until 14:40_ against
  the phone's clock when the answer lands. A _TO CONFIRM_ row drops its time on the phone's clock,
  ticking every thirty seconds, and the sheet names a time only while it is ahead of its read. Home and
  the details run on their reads' own clocks.
- **An answer carrying `payment_awaited_until` without a refusal of the reader's own** raises _It's a
  game!_ with the waiting line, whatever the act was. Examples are a payer's confirmation while a
  second refused payment is still awaited, or a newcomer's yes that refills the game during the wait.
  The wire documents the field as _this yes filled the game_.

**Open**: a share refused for **terms to accept again or no method** gets its time to pay as well. Its
player's Home card reads _Confirm your payment by 14:40_, but _TO CONFIRM_ lists only the bank's check
and a decline, so there is no row beside it. Their own fill opens the terms toast or the setup, which
name no time. The way through is the game's details (their _I'm in_ once mended), reached from the
notice. Which words and which surface this wants is a ruling.

**Owed**: the Stripe test-mode check that a refused payment's copy on the club's account can be
confirmed again (#533, the backend's handover), and the laptop provider that never confirms a payment
(`payments.md`). **Nothing here has been seen on a device**: the amber line on a _TO CONFIRM_ row, the
sheet's note, the line under the word and the details' _Confirm your payment_ all want a look.

**Decided, and built since #642, #643, #644 and #645 (below): the share is held until
the club's cut-off, and leaving before it is free** (the mechanics Q113, [ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-10-10 amendment; story S-01A's F-LEAVE-6.1; root
[#635](https://github.com/Raketa02/Raketa/issues/635)). **Why**: a refund always cost somebody Stripe's fee, the 1,60 zł this feature prints was
an estimate of a fee that depends on the card, and keeping it is exposed under Polish payment law.
Letting a hold go costs nothing. So the fill holds the shares and the cut-off takes them. What it
reverses here, for the tickets that build it:

- **The money line** goes back to _40 zł · free to leave until Wed 19:00_, and _Paid · 40 zł_ once
  taken; the details' row says when the share is held and when it is taken.
  `back_if_you_leave_grosze` leaves the wire ([#637](https://github.com/Raketa02/Raketa/issues/637); the phone's words [#642](https://github.com/Raketa02/Raketa/issues/642)).
- **Leaving before the cut-off** takes nothing: the line under _Leave the game_, the sheet and the
  toast say so ([#642](https://github.com/Raketa02/Raketa/issues/642)). After it, they give the exact refund the server sends, or no figure
  ([#641](https://github.com/Raketa02/Raketa/issues/641), [#644](https://github.com/Raketa02/Raketa/issues/644)).
- **A refused card before the cut-off** is the root glossary's **Time to fix the card**: _Fix your
  card by 14:40_ where this feature says _Confirm your payment_ ([#643](https://github.com/Raketa02/Raketa/issues/643)); a rescue's button says
  _held until the cut-off_ or _paid now_ ([#645](https://github.com/Raketa02/Raketa/issues/645)).

**Held until the cut-off, on the phone** ([#642](https://github.com/Raketa02/Raketa/issues/642); the
backend's #637 and #639; the mechanics Q113, §12.2, §13, §14.1; the screens A4.1, A4.2, A8; story
S-01A's F-LEAVE-6.1). Ivan's Thursday 19:00 at Bonarka Arena fills a week ahead. His Visa is only
checked that day, Oscar's Mastercard holds, and both read _40 zł · free to leave until Wed 19:00_ on
Home. Ivan's details say _40 zł_ over _Held from Sat 19:00 · taken Wed 19:00_, Oscar's _Held on your
card · taken Wed 19:00 · free to leave until then_. On Wednesday at 19:00 both lines turn to _Paid ·
40 zł_ by themselves. **Why**: the product owner ruled that the fill holds the shares and the cut-off
takes them, so a leave before it costs nobody a fee and _free_ is true again (Q113, amending Q99).

- **The wire**: `money.back_if_you_leave_grosze` is gone. `share_state` (`HELD`, `CHECKED`, `TAKEN`),
  `held_from` and `taken_at` come in, each absent for a `null` and from an older server.
  `ShareState` is spelled in `domain/vocabulary.ts` and held equal to the wire's.
- **The share on the read's clock** (`shareAt`, `domain/home.ts`): a checked share is held from
  `heldFrom`, and every share is taken at `takenAt`, the cut-off, where the server's own `paid` turns
  too. `lineCanRunOut` ticks while `heldFrom` is there as well as the cut-off. **Home's line**
  (`moneyLineOf`) is the share with _free to leave until_ the cut-off while it is ahead, held or only
  checked alike, then _Paid · 40 zł_. **The details' row** (`moneyRow`) is _YOUR SHARE 40 zł_ over the
  held or checked words (`heldWords`), then _PAID 40 zł_ over _Paid_. The label is _Your share_ until
  the share is taken, on a _Seat open_ game too.
- **A game off with nothing given back** says why, then by the reason (`NOTHING_BACK`): _Nothing was
  taken_ where the shares were held and let go (short at the cut-off, or the club's cancel before
  it), _Nobody paid_ where nothing was ever held. _Refunded 28 zł_ stays for a club's cancel after
  the cut-off. _1 seat open · fills by Fri 16:00 or the game is off and nothing is taken._
- **Leaving before the cut-off**: the line under _Leave the game_ reads _Free to leave now — nothing
  is taken_. The sheet's first line is _Nothing is taken: the hold on your card is let go._ while the
  share is held, and _Nothing is taken._ while it is only checked (`leavingAt` folds which on the
  read's clock). The rest of the sheet is as before. The toast says _You left the game. Nothing was
  taken._ **At the cut-off the line turns by itself**, as the money row turns to _Paid_: `leavingAt`
  reads a share taken at `now` as after the cut-off, which the server says once read again.
- **Leaving after the cut-off** kept today's shape with no figure and no estimate — _Refunded only if
  someone takes your seat_ under the button, the terms' own words for the refund on the sheet — until
  #644 gave the read's exact figure (below).
- **A game still filling** says _…When the last yes lands, everyone's share is held and the court is
  booked; it's taken at the club's cut-off._ (A4.2).

**Calls made without a ruling**: the line under _Leave the game_ before the cut-off (§13 only says it
_says the same_ as the sheet), and the sheet's refund clause after it without a figure, where §13
gives none while the fee isn't known (gone since #644, below); _Nothing was taken_ after the club's cancel before the cut-off, as §14.1's
table puts it, where Home said _Nobody paid_; the folds at `heldFrom` and `takenAt` on the phone's
read clock, which the backend's own reads do at the same instants. **Owed**: the rescue's join
(#645), time to fix (#643) — both built since (below). **Nothing here has been seen on a device.**

**The late leave's exact refund** ([#644](https://github.com/Raketa02/Raketa/issues/644); the
backend's #641; the mechanics Q113, §13, [ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-10-10 amendment; the screens A4.1, details 10). Ivan leaves Thursday's game on
Wednesday at 21:00, after the cut-off, with his business Visa. The line under _Leave the game_ reads
_If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)_, and
the sheet _Your seat is offered to others. / If someone takes it, you get 38,24 zł back (40 zł less the
1,76 zł kept on your payment); if nobody does, you won't. / On your record if nobody takes it._
**Why**: the product owner ruled that a leaver after the cut-off gets the share back less exactly what
Stripe kept on their payment, shown to the grosz before leaving, and that no estimate is printed
anywhere (Q113).

- **The quote is the read's** (`leaving.refund_grosze`, `leaving.card_fee_grosze`): `Leaving` carries
  it as `lateRefund` (`backGrosze`, `keptGrosze`) after the cut-off only. The noughts the read sends
  while one payment is awaited are no quote — nobody has paid. The _40 zł_ is the two together,
  which is the payment: the server's refund is the payment less the fee.
- **While the read quotes none** — the fee is not yet known, which is the case for a club on its own
  negotiated pricing until Stripe reports it, and for the moment `leavingAt` turns a share taken at
  the cut-off on the phone's clock — **there is no figure and no clause**: the line reads _Your seat
  is offered to others_, and the sheet drops the refund clause, _Your seat is offered to others. / On
  your record if nobody takes it._, as the backend's no-figure email does. The toast is unchanged.
  The line and the sheet share one copy key for the seat offered, the sheet adding the full stop.

**Calls made without a ruling**: the line's words without a figure, where §13 and A4.1 say only _no
figure and no clause_ — #642's _Refunded only if someone takes your seat_ is gone with the clause it
stood for. **Owed to the lawyer** (O3): the clause's wording, the terms'. **Nothing here has been seen
on a device**: the line under the button is now a sentence long and wants a look.

**Time to fix the card, and a rescue's share, on the phone**
([#643](https://github.com/Raketa02/Raketa/issues/643), [#645](https://github.com/Raketa02/Raketa/issues/645);
the backend's #638, #639 and #640; the mechanics Q113, §10.1, §12.2, §14.1; the screens A2.4, A3.1,
A4.1, A4.3, A5.3, A7.3, A8; story S-01A's F-LEAVE-6.1). Paula's card is refused at 14:10 when Ivan's
yes fills Thursday's game, a week before the cut-off. Nothing is being taken, so she is told _Your
card didn't go through — fix it to keep your seat. Nothing is paid now._, and her card, her _TO
CONFIRM_ row and her sheet read _Fix your card by 14:40_. On Monday Diego goes for the seat Kuba freed on
Thursday's 19:00: his _I'm in · 27 zł_ is said _held until the cut-off_, and once in he reads _27 zł ·
free to leave until Wed 19:00_, like everyone in the game. **Why**: the product
owner ruled that before the cut-off nothing is taken, only held, so a refused card is fixed, never
paid (Q113); after it, money is taken at once, and the words stay #630's.

- **The window is the server's** (`time_to`, the vocabulary's `TimeTo`, held equal to the wire's):
  on Home and the booked details beside `your_payment_due_by` (`HomeGame.timeTo`), on a refused
  share's `your_payment` (`YourPayment.timeTo`, so `Confirmation` carries it to the sheet), and on a
  _TO CONFIRM_ row. **One fold reads it at an instant** (`paymentWindowAt`, `domain/home.ts`): the
  read's window while the time is ahead, else `UNNAMED` — the time ran out (the read then names
  none), none was given, or an older server. Every surface asks it, so a row, its spoken name, its
  sheet and the details' button agree at the deadline. **Unnamed, the words say _confirm_, never
  _pay_**: a seat taken back before the cut-off is held, not paid (§12.2: _you are not asked to
  pay_), so a decline reads _Use another card for this share_ over **Use this card** where the time
  to pay's says _Pay this share with another card_. **Only the refused player's own words change by
  it**: the others read _Waiting for one payment ·
  until 14:40 · Nobody pays until it's in_ in both windows, and _It's a game!_'s line is always about
  another player's card, so it keeps its words (the mechanics §12.2, written in while recording Q113).
- **The words**, a `Record` over the window (`PROPOSALS_COPY.game.yourTimeBy`, `FILL_COPY`'s
  `refused`, `confirm` and `toConfirm`): Home's card and the details' row _Fix your card by 14:40_
  (`yourPaymentWords`, off a `YourTime` — the deadline and its window); the toast at the fill
  (`refusedToast`, the screens A2.4's words); the sheet _Fix your card_, its note _Fix your card by
  14:40 to keep your seat_ and a line _Nothing is paid now — fixing your card only places the hold
  again._, the mechanics' own _the hold is only placed again_, true of a card check run again too
  (`payments.md`); a _TO CONFIRM_ row _Fix your card by 14:40_ over _Nothing is paid now_ (A7.3), its
  button **Fix**, spoken _Fix your card for Padel · Saturday 15:00 at Bonarka Arena, 28 zł_.
- **A card refused at the holding time leaves the game booked** (#639; A8, A4.1). `moneyLineOf` now
  gives the payer their own line whatever the status — the read names the time to its payer alone —
  so the card stays _Booked_ and reads _Fix your card by 14:40_; the others' cards don't change. The
  details' row says what is at stake there, _Fix your card by 14:40 to keep your seat_
  (`stakeOnTheDetails`: a game booked already, where the tag says nothing of it — the seat at stake
  is a `SeatAtStake`, _yours_ or _aRescue_, the notice's two endings; `seatKeptBy` words it), and
  **Fix your card** under the game card opens the confirmation, as _Confirm your payment_ did on a
  game waiting for one payment.
- **A rescue's _I'm in · 27 zł_ says what the share does** (`seatButtonSpoken`): _I'm in, 27 zł held
  until the cut-off_ while it is ahead, _I'm in, 27 zł paid now_ after it — on a _Seats to fill_ row,
  a rescue's details and the slot sheet (each offer's `fillsByTheCutOff`, the row leaving at its
  deadline), and the deck's _I'm in_ under a _Seat open_ card (`answerLabels`, off the card's
  `noFreeCancellation`). The drawn words stay _I'm in · 27 zł_ (A3.1: _its spoken name says which_).
  Once in, Home and the details read the game as any player's (#642's held, checked or taken).
- **A refused rescuer keeps the seat for 30 minutes** (#640). The toast says _Your card didn't go
  through — fix it to take the seat. Nothing is paid now._ (after the cut-off _Your payment didn't go
  through — confirm it to take the seat_), and the sheet's note _Fix your card by 14:40 to take the
  seat — it's kept for you until then_ — the notice's and the email's _to take the seat_, since the seat
  is not yet theirs (`seatAtStake`, off the card the yes was said on). The rescue's details seen from
  outside read the kept seat's time under the share,
  _Fix your card by 14:40 to take the seat_, and while their _TO CONFIRM_ row holds the payment
  **Fix your card** stands where _I'm in_ stood, opening the same sheet: the join again is that
  confirmation, and _I'm in_ there would only be refused `payment_to_confirm`. A refusal for terms
  or a missing method has no row, so _I'm in_ stays, the server's _joined again here_.

**Calls made without a ruling**: the sheet's title _Fix your card_, its check line _Your bank wants
you to confirm the hold on your card yourself._, its decline line _Your bank declined the hold on the
card on file. Fix it with another card._ and button _Use this card_, where the spec words only the
note; the row's button **Fix**; the rescue toast's words, the fill's with _to take the seat_; the
rescue sheet's _— it's kept for you until then_, for the ticket's _that the seat is his until then_;
the booked details' **Fix your card**, which A4.1 calls _the confirmation one tap away_; the deck's
_I'm in_ spoken by the share on a _Seat open_ card, the one door the ticket's _Seat open card_ can
mean; the words with no window named, which say _confirm_ where the time to pay's say _pay_.
**Known gaps, both the read's to close**: a _TO CONFIRM_ row names no rescue, so its sheet says _to
keep your seat_ to a rescuer too; and once a time ran out the read names no window, so a seat taken
back can't be told _fix_ before the cut-off or _pay_ after it — the phone says _confirm_ to both. **Owed by the root**: the root `CONTEXT.md`'s **Time
to fix the card** and **Rescue** still say _not yet built_. **Nothing here has been seen on a
device**: the row's fourth line and its **Fix**, and the sheet's extra line, want a look.

**Nothing is shown at the desk: players walk straight to the court**
([#653](https://github.com/Raketa02/Raketa/issues/653); ADR-0195, Q116; the backend's #651). The
booked details no longer carry a _Show at the desk_ card on the game's day, and Home's card never
had a desk line. `CheckInCard`, its QR drawing (`qrPath.ts`, the `qrcode` core declared in
`qrcode-core.d.ts`), the `qrcode` and `@types/qrcode` dependencies, the four desk words in
`homeCopy.ts`, `shortCodeSpoken` and the theme's `size.checkIn` are deleted. `BookedGame.checkIn`,
`DeckPerson.checkedIn` and `checkedInOn` went with the wire's `check_in` and `checked_in`. So
`BookedGameResult` hands `games`' result screen only the re-read now, and every other player on the
court has a _didn't come_ row (`games.md`). **The phone was broken against the backend until this
landed**: #651 stopped sending `check_in`, and the mapper read `wire.check_in.short_code` whenever
the field was not `null`, so every booked game's details threw.

**_Played · no score_, and a For fun game reads _Played_**
([#656](https://github.com/Raketa02/Raketa/issues/656); ADR-0195 §2, §5, Q114, Q119; the backend's
#654 and #655). `HomeStatus` swaps `NEVER_PLAYED` for `PLAYED_NO_SCORE`: Home's card, the details'
tag and second line say _Played · no score_ — `onDarkHair` as _Never played_ was, an ending with the
room as before — and offer nothing. **A For fun game after its hour reads _Played_**, not _Needs
result_ and not _Counted_: it asks nobody for a result, and a score on it stands at once and counts
nothing. That is `shownStatus` in `domain/home.ts` — the wire's status with one more, `PLAYED`, for
a For fun game the wire calls `NEEDS_RESULT` or `COUNTED` — and every table the tag is drawn from
(`STATUS_INK`, `OPEN_GAME_VARIANT`, `status`, `statusInLine`) is keyed by it, so the card, the
details, the room's line and the card's spoken name say one word. `PLAYED` is `mint`, settled, and
its _Open game_ `onDark`. The details' door on it is **_Add the score_** (`resultActOf`'s
`add-score`), not _We played_, onto `games`' result screen, which asks nobody. **Nor is it on
Home's count**: the backend's `845decf0` made a For fun game whose hour has come `needs_you` false,
so the tab counts it no more — the phone draws the count it is sent and holds no second one.

**Who's here — the details' door at the court, and Home's line for a game somebody didn't come to**
([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3; the backend's #657).
`BookedGameResult` hands `games`' result screen the booking's hour and club beside the re-read
(`BookedFacts`' `startsAt` and `club`): the first half hour is measured from the one, and _You can
say so only from Bonarka Arena_ names the other. **In the first half hour the details' door is _Who's
here_** (`resultActOf`'s `whos-here`, through `games`' `tapsAreOpen` at the read's clock) — for a
Competitive game and a For fun one alike — onto the screen where a player at the club taps who
isn't here yet and an awaited player says _I'm here_; the read's clock ticks through the half hour
so the door turns back to _We played_ or _Add the score_ at its end. A game with a score already on
the table keeps _Confirm the result_: the screen it opens says who's here too. `UncountedReason`
swaps `NO_SHOW` for `DIDNT_COME`: Home's card and the details' money row say _Somebody didn't come
· say who was there_ while the read's _needs you_ says a late _I was there_ waits on the reader —
theirs to say, or somebody else's to confirm — and _Somebody didn't come · no Level moved_
otherwise (`MoneyLine`'s `didntCome`), and the details' door is **_Say who was there_**
(`who-was-there`) on the same condition. `onHome` drops no card that needs the reader any more: the
late claim's day ends half an hour before Home's day after the hour does. The walk is
`attendance.test.tsx`, with the fake location port placing the phone at the club or away and the
fake server judging it by distance, as the backend does. **Not seen on a device.**

**Calls made here, open for the product owner**:

- **One door for the late claim's two readers.** Home's read says only that it needs the reader, not
  whether they didn't come or somebody else's claim waits on them, so the door is _Say who was
  there_ for both and the screen says which.
- **Home's line says _Somebody didn't come_ to the player who didn't**, for the same reason.
- **_Who's here_ replaces _We played_ for the whole first half hour**, though the grid is on the
  screen it opens: at 16:10 the court, not the score, is what a player is there for.

**No club confirms a game: a full game is simply booked**
([#676](https://github.com/Raketa02/Raketa/issues/676); the backend's #669;
[ADR-0196](../../../docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
§1, the mechanics Q121; story S-01E's F-REQUEST-3.1, F-REQUEST-23.1). Paula's yes completes Marta's
Thursday game at Kazimierz Padel: _It's a game!_ with nothing under the word, and Home and the details
read it _Booked_, each player's 25 zł held until the cut-off. **Why**: no court platform makes a club
confirm a booking, and a desk that is shut until 16:00 called off every game that filled in the
morning, so every club now books the moment the last yes lands. **What went**, with the wire's
`waiting_for_the_club`, `club_confirms`, `answer_by` (the score's own `answer_by` stays), `HomeStatus`'
and `ProposalStatus`' `WAITING_FOR_THE_CLUB`, `TURNED_DOWN`, and `CalledOffReason`'s `REFUSED` and
`NO_ANSWER`: the _Waiting for the club_ tag and its amber _waiting for the club_ on a _You're In_ row;
_answers by_ on Home, the details, the rail's clock and _It's a game!_ (`answerByAhead`,
`answersByWords`, `waitingWords`, `itsAGameWaiting`, `ItsAGameAtTheClub` and its since-mount read,
`useBookingSinceMount`); the fill's `waiting` outcome; _said no_ and _didn't answer in time_
(`clubsAnswer`, and the filling details' second read of the booking); and _is asked again when it's
full_ — a full game gone back to filling only _books when it's full_, so `fillingAgain` is a plain
mark. **The stamp always shows the price** on _Book it now_ (`chargesAtOnce`), and a yes holds no club
any more (`YesOn`). The leaving kind is kept under a name that says so, `WHILE_WAITING_FOR_A_PAYMENT`:
_Leave the game_ while one payment is awaited still withdraws the yes, nobody having paid.
