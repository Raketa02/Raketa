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
`chargesAtOnce` (the stamp's price: _Book it now_ unless the club confirms, or a rescue),
`countdownOf` (under 24 h, floored), `standingCards` (a card past its deadline leaves silently), `weekCapOf` (the fortnight's capped weeks) and `refusalOutcome`.

**The kind is the switch's, corrected by the intent.** The group page's Competitive · For fun switch
(`groups`' game-intent store, which Friends shares) hands in the kind chosen; the read says which
segments the player's intent shows, and a choice it does not show is read again as the segment it
does (`resolveKind`, `useGroupDeck`'s second query) — so a For-fun player never lands on an empty
Competitive deck. No segments at all is no intent declared: Play's `DeclarationInterstitial` replaces
the deck, reporting `DECK` — the contract's word for a deck, since `PlayIntentSurface` has no value
for a group's tab — with its own line about who reads the answer, and the answer re-reads the deck.

**The stage is the Players deck's.** `DeckStage` and `DeckAnswers` come through `play/types`, with
the two things that differ handed in: the stamps' words (_I'm in_ / _Not this time_, the share after
_I'm in_ when the yes charges at once) and the three buttons' names (_I'm in_, _Not this time_, _Game
details_). The stage's cards behind now fade as well as shrink (Q90), for both decks.

**An answer flies on the press and the server settles it.** The card in flight is held by `GamesDeck`
(component state), so a re-read landing mid-flight cannot pull it off the stage; when it has flown it
is dropped from the cached read (`withoutCard`, its segment's count and the badge following), and the
answer settling re-reads every deck of the group. **A refusal is a toast**, handled on the mutation
rather than on the call — TanStack drops a `mutate` call's own callbacks when a later call is made,
and a player answers the next card before the last reply lands — and `refusalOutcome` decides the
card: a reason the player can mend (no saved way to pay, the live-yes cap, a read that failed) puts it
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
counts every yes across sports with _up to 10 per sport_ under it — the server's `cap_per_sport` —
where mock 48 drew _1 OF 10_, a fraction of two different wholes (Part 16). A row is _Padel ·
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

- **The Undo window** (§6.5). A yes `waitsForUndo` — _Book it now_ (an On request club's too: at zero
  the game goes to the club), and **every** rescue join (Q74) — flies like any other, then counts ten
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
  **refused share** (the bank's check, a decline) says _Your payment didn't go through — confirm it
  to keep your seat_ and opens the confirmation on it; no method at the fill is the setup and the yes
  again; a new card brand names You › Payments; anything else is a vote. A yes the card called free
  can still be the last — the others got there first — so the deck's plain yes is read too.
- **It's a game!** is the yes screen's third face (ADR-0167): its ground, entrance, tiles, `vs`, word
  role and pills, crossed from `challenges/types` — the faces are **the card the yes was said on**, its
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
  the game says _It's a game! You'll find it in Home._ in a toast rather than drawing faces it has
  not got. A booking, a confirmation and every yes that answers _confirm_ re-read it.

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
in a toast.
**Owed**: the backend's laptop provider never confirms a payment (payments.md). **Nothing here has
been seen on a device.**

**Home's booked games and a booked game's details are this feature's**
([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, A4.4, A8; the mechanics
§11.4, §14, §15.1). Two reads, both #542's and both the backend's Proposals context: `GET /home` (the
reader's booked games, soonest first, the ended ones too, and Home's badge) and `GET /bookings/{id}`
(one booked game in detail, with the check-in code on its day). `useHome`, `useBooking`, keys
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
while a cut-off is ahead), so _free to leave until Fri 16:00_ leaves the line at that instant by
itself. **An ended card stays a day after its hour** (`onHome`) — the wire dates no ending of a
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
`GameScreen` with the score leading and its three Classic slots empty); the Game's own forecast
(`games`' `GameForecast`) while the booking says to draw it; and **Show at the desk** on the game's
day (`CheckInCard`: the QR drawn by `qrPath.ts` over `qrcode`'s core as one path, the short code
spoken a character at a time). The filling details and the booked ones share `GameFacts` and
`OthersFaces`.

**The chat is reached from the details and nowhere else** (A4.4, §14.3). _Chat_ is drawn while the
join keyed by the game finds the room (`conversations`' `useGameRoom`, the join `GET /bookings/{id}`
documents) and the status can have one (`chatIsOpen`: not while the club decides, not once called
off). **The room's own life decides the rest**: it closes as today — 48 hours after _we played_,
when the result window closes — so a counted game keeps its door for as long as its room does,
rather than leaving a room open with no way in. It pushes `/booking/[id]/chat` (`BookedGameChat`), which mounts `ConversationScreen` in
its booked form — no plan card, no plan chips, no _Details_ door, the header's second line the
booking's word — over the details, so the back chevron returns to them; the bar stands down there as
in every room. Before there is a game or a room to draw, the details, the room and the result say
the same four things (`BookingAbsent`): offline it resumes, the spinner, a refusal with the retry,
or the one terminal sentence.

**Calls made here, open for the product owner** (Part 16 has the drawings'):

- **The Home card's bubble is a mark, not a door.** The ticket asks for _the chat bubble_; A8 and
  §14.3 say a Home card has no chat door. It says the game's chat is open, silent, its words in the
  card's spoken name.
- **_Chat · n_ has no number, and is always volt.** No read carries an unread count; the number and
  the lit-when-unread state are owed to the backend.
- **_New until opened_ is the phone's memory** — a fourth value in `shared/lib/preferences`, which
  **ADR-0188 §5 says is a new record, not an edit to its table**, and the value is a record of what
  was opened rather than a choice. Decide: a new ADR admitting it (a root session writes it), or
  _new_ held for the session only, or a server-side _seen_. A reinstall, a second phone or a
  sign-out shows every live game as new once.
- **_Chat_ follows the room's life, not the result** (§14.3 _closes as today_), where A4.1 says
  _while the game isn't over_ — the details are the only way in, so a door that went at the result
  would leave a room nobody can reach.
- **The title names the others whole** (_Piotr Sowa, Inés Díaz, Bartek Lis_), where details 7 draws
  first names: ADR-0171 — a name is said whole, never a first name derived from it — as the filling
  details already do.
- **_Waiting for the club_ names no court** on the card and the details (A4.2), ahead of #543
  producing the status.
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
been seen on a device**, the QR least of all: it is drawn from `qrcode`'s matrix and never scanned.

**Fill in, rescues, leaving and On request are this feature's**
([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3, A4.2, A4.3, A8; mocks 2,
11–14, details 10; the mechanics §10, §11, §13, §14; the backend's #543, #544, #545). Four reads,
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
yes's game, club and _book by Sat 13:00_ — or, amber, _waiting for the club_ — with **its squares read
off the game's own details** (`useProposal`: everybody In, then the open seats dashed) and _Withdraw_
**only once those details say the reader may** (`mayWithdraw`) — so it is hidden while the club
decides, when the `actions` hold _Leave_ instead, and before the read lands: a withdrawal while the
club decides is a departure, and calls the request off with no sheet in front of it. One read a row,
because the live yes carries neither who is In nor the club's turn.
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
is offered, and a volt **I'm in · 27 zł** (`TakeTheSeat`, the row's door too) — no Chat, no Leave, no
_new_ marked. A seat gone before the read says _This seat isn't offered to you any more._

**_Leave the game_ is at the foot of a booked game's details** (A4.1, details 10; §13), with the line
saying what leaving costs **now** — the read's `leaving`, folded by the server — and today's _Before
you leave_ sheet (`challenges`' `LeaveSheet`) with the §13 words: _You'll be refunded 27,18 zł now (the
0,82 zł card fee isn't returned)…_ before the cut-off, _…when someone takes it; if nobody does, you
won't be…_ after it, _Nobody has paid yet. Leaving withdraws your yes._ while the club decides. The
door is `LeaveTheGame`, the group exit's shape: the sheet is the surface while the act is in flight
and says a refusal in words; success is a toast — with when the refund lands (_BLIK within hours,
cards up to two weeks_, §12.3) — and the leaver goes back to Home, which no longer holds the game. No
button where the read gives none (the hour has come, the game is over). **The same door stands on a
game still filling while its club decides**, sent as the withdrawal (`useLeaveWhileWaiting`, `DELETE
/proposals/{id}/yes`, which calls off the request).

**The filling details are `GET /proposals/{id}`** (A4.2; owed by #556). The status tag — _Filling · 2
of 4 in_, _Waiting for the club_ amber, _Booked_, or how it ended unfilled — WHERE with the distance
and no court, the share with _if it fills · book by_ or _nobody pays until Bonarka Arena confirms_,
the forecast, the grid, the paragraph while it fills, and **the actions the read names, in its order**:
_I'm in_ / _Not this time_, _Withdraw_, _Leave the game_, _Confirm your payment_ (the fill's
confirmation, on the payment the read names). Nothing about the game is held by the screen: every
answer re-reads the details (`reread` takes `proposalKeys.proposals()`), each button busy until the
read lands. **The one fold**: whether a yes from the details books, which a card carries and the read
does not — the deck's own rule read off the seats and the In count (`courtOfDetails`: the last seat is
_Book it now_).

**On request** (#543; A2.4, §11): a _Book it now_ yes at an On request club counts its ten seconds
like any other; the server answers `waiting_for_the_club`, and the fill reads it as its own outcome
(`fillOutcome`'s `waiting`) — Home and every deck re-read, and a toast: _Waiting for Bonarka Arena to
confirm — nobody pays until it does._ No _It's a game!_: the charge and the celebration follow the
club's yes, told by the notices (#549). Home and the booked details say _Waiting for the club_ with no
court; their _Leave the game_ withdraws the yes.

**Home's and the details' lines are the read's now** (§14.1): _2 seats open · fills by Fri 16:00 or
the game is off and everyone is refunded_ (`open_seats`), _1 seat open · offered to others · the game
goes ahead_ after the cut-off; _Called off_ with why — _A seat was still empty at the cut-off_,
_Kazimierz Padel couldn't take it_, _… didn't answer in time_ — and what came back (_Refunded 28 zł_,
`refunded_grosze`) or _Nobody paid_; _Uncounted_ with _A seat was empty · no Level moved_ — on Home's
card, and beside the share on the details' money row (`moneyRow`). A booking
waiting for its club has no Game yet (`gameId` absent): no room, no forecast, no result, and it is not
in the Classic half of the badge.

**Calls made here, open for the product owner** (Part 16 has the drawings'):

- **A row's faces are read after the seat is taken.** _It's a game!_ from a _Seats to fill_ row reads
  the booking first — the row cannot say which side the open seat is on — so it lands a read later
  than from a card, and a failed read says _It's a game!_ in a toast.
- **_You complete it_ on a rescue's details too**, where A4.3 words the tile _You?_ — the card's own
  rule (A2.3: the last seat completes it), so one seat says one thing on both surfaces.
- **The On request toast** — A2.4 says the game goes to the club at zero and nothing about what the
  player sees; silence after ten seconds of _Booking_ would read as a failure.
- **_Leave the game_ and _Withdraw_ are 6.1's `secondary`**, where details 10 and mock 13 draw dark
  red text: the group exit's call (red is _ended badly_, 1.3), and the sheet is what makes it
  deliberate.
- **The rescue row's coral frame** is the rescue ribbon's meaning (§1.2), and the waiting line's amber
  is `amber` (_watch this — not yet wrong_).
- **Short day names on the rows** (_book by Sat 13:00_, _fills by Fri 16:00_) where mock 13 spells
  _Saturday_ — the money line's and the details' own form.
- **The leaving toast** says when a refund lands, as §12.3 asks of the moment a refund is issued.
- **The details' ended statuses' words** (_Didn't fill in time_, _Taken back_, _No court left at that
  hour_, _The club couldn't take it_) — no mock draws them.
- **A game the details read as `FILLED`** says _Booked_ and offers nothing: the details have no
  route to Home's screen; Home holds the game.
- **_Confirm your payment_ on the filling details** — A4.2 lists _I'm in_, _Not this time_,
  _Withdraw_ and _Leave_; the read's `actions` add `CONFIRM_PAYMENT` while a refused share waits, and
  an action the server offers with no door would strand it. It opens the fill's confirmation.
- **A booked game that started short** has its own end on the game screen (`games`' `started-short`,
  _A seat was empty._): the contract added `STARTED_SHORT`, and a standing with no arm fails the build.

**Owed**: the chat lines _Kuba left — the seat is open_ / _Ola took the seat_ (conversations, with the
backend's #545 note); the push and in-app notices of the club's answer and of a seat opening (#549,
#559); _+ Post a game_ enabled (#558). **Owed to the backend**: a `called_off_reason` for the club's
own cancel (#547) and for a request called off when a player left it — §14.1 lists both, and the
wire names neither, so those cards say only what came back; and who is In and the club's turn on
the live yes, which would save _You're In_ its read a row. **Nothing here has been seen on a
device.**
