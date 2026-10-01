# proposals — a group's Games deck, and a game's details

The client side of the backend's **Proposals** context (#538, #539): the games a group deals a
player, answered with a silent yes, and one game still filling seen in detail. Built by
[#553](https://github.com/Raketa02/Raketa/issues/553) from the Games & Fill in screens (A2, A4.2),
the mechanics (§6–§8) and
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md). The group page
(`groups`) draws `GamesDeck` as its Games tab and reads its badge; the dependency points one way —
`groups` reads `proposals`, never the reverse.

**One read, and the details are a card of it.** `GET /pools/{id}/deck?sport&kind` — the pool filed
under the group's id — is the whole of what the feature reads: the segments, the badge, the capped
weeks and the cards in the order dealt, each the reader's own version with its sides, forecast,
overlap and court. There is no read of one proposal, so a game's details (`GameDetailsScreen`,
`/play/group/[groupId]/game/[proposalId]?sport&kind`) find their card by id in the same read. Once a
yes is said there the deck stops dealing the card (a card you are In on is _You're In_'s), so the
screen keeps the card it last found for as long as it is open — React's own set-during-render shape,
in the screen's state and nowhere a later screen could find it — with your tile In, the game one yes
further on (`withYourYes`) and _Withdraw_ in place of the two answers. A card the screen never found
says so in one sentence.

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
rescue tiles (_paid_, the dashed _You?_ seat, the court number — #545/#557, not on the wire yet); the
Fill in badge (#545/#557); a tile flipping to In while the card is on screen (the read is re-asked on
focus and after answers, never polled — a live channel is not specified). **Nothing here has been
seen on a device.**

**The countdown runs from the read.** The deck's read carries no `read_at`, so the countdown starts
from the moment it was received (`dataUpdatedAt`) and, while a card on the deck counts down, the
deck's clock ticks every thirty seconds (`useDeckClock`) — so _45 min_ moves, and a card at its
deadline leaves silently rather than lingering until the next read to be refused as over. A drawing
and never a decision: the server stays the authority on whether a game is over. **The details'
Withdraw follows your tile's IN** (`youAreIn`), not a flag of the screen's, and their DAY carries the
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

**A game you are already In on is drawn from your yes.** The deck never deals a game the reader is
In on, and there is no read of one proposal until #542 — so a live yes's row would have opened on
_This game isn't dealt to you any more_. When the deck has answered without the card, the details
read the live yeses and, finding the game there, draw what the yes knows: the club as the title,
_Filling_, WHERE · DAY · TIME · YOUR SHARE and _Withdraw_ — no tiles, forecast or grid, since who else
is In is not on the yes. A withdraw puts the answers back, and the deck, read again, deals the game
with everything on it. The yes found is kept while the screen is open, as the card is. **Owed**: when
#542 serves a proposal's details, this view gives way to the full card. **Calls open for the product
owner**, each a Part 16 row: the live yeses' head, the yes's details, and the bound's limits in sans
700 (a sentence's figures, where 1.4 sets display figures in mono). **Nothing here has been seen on a
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
