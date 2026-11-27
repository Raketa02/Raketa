# payments — You › Account › Payments

The client side of the backend's **Payment method** (#536): a player saves the way the clubs charge
them, and sees what is saved. Built by [#552](https://github.com/Raketa02/Raketa/issues/552) from the
Games & Fill in screens (A7, A7.3; mocks 40–47), the mechanics (§12.4, §12.5), Q82 and Q83, and
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) /
[ADR-0190](../../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md). The
shell composes `PaymentsRow` into the You tab's **ACCOUNT** group; the screen is
`/you/payments`. State B's _Live yeses_ (mock 48) are handed in by the route file (#554, below);
_Receipts_ (mock 49) are #555's.

**One read decides the screen.** `GET …/payment-methods/current` behind the row and the screen alike:
nothing saved is **state A**, the numbered checklist; a saved method is **state B**, the dark method
card. A save writes the confirmation's answer into that read (`setQueryData`), so the screen turns
from A to B the moment the bank's answer is read back, and the row says the new card when the
player goes back. The row's line is _Card •••• 4312_ for a typed card, the wallet's name for one
saved through it, _Not set up_ for none (the screens A7).

**The order is Q82's, and it is the contract's.** Choose how you pay → Card details → **Accept the
terms** → Confirm with your bank. The mocks drew the terms last; Q82 moved them up, and #536 made it
unbreakable: `POST …/setup` never returns the setup's secret, `POST …/terms` does — so nothing can be
confirmed, let alone saved, before the terms. The machine is `domain/setupSteps` (`advance`,
`setupSteps`), pure and tested as events: every event outside its step answers the progress
unchanged, the same object, so a late answer arriving after the player moved on moves nothing.

**BLIK is offered and cannot continue** (§12.4 — Stripe's recurring BLIK is a preview, open item O1).
Its chip shows the notice and _Continue_ stays shut; no setup is opened for it.

**The phone's wallet skips the card details** — Google Pay on Android when Google says the phone can
pay with it; **Apple Pay on an iPhone only once a merchant identifier exists**
(`shared/config/applePay.ts`, null today), which needs the Apple
Developer membership (O4, O6), so an iPhone offers a card and BLIK until then. The wallet's chip is
drawn only when the port says the phone has one. Step 2 is then drawn **not done but not needed** — a
dash, and _In Google Pay_ on its right — because the wallet holds the card.

**Step 4 asks the bank by itself.** _Ticks itself when the bank asks nothing_ is only possible if
nobody presses anything, so arriving at step 4 — from the terms, or from a second card after a
decline — confirms at once: a bank with no check answers straight away and the screen is state B; one
with a check draws it over the screen (Stripe's SDK does). **The button on the step is for asking
again** — after the player closed the check, after a failure, or while the server says the check is
not done. _Once the bank said saved_, asking again only re-reads the server, never confirms twice.

**One setup per visit.** The server allows five a day (the card-testing guard) and a second replaces
the first at the provider, so the setup the first _Continue_ opens is kept for as long as the screen
is: a changed mind on step 1 (a finished step 1 is pressable), a refused card and a closed check all
reuse it, and **the terms are accepted for the setup, not for a card** — after a decline the card
details open again and the next card goes straight to the bank. Only the server saying the setup is
gone (`payment_setup_not_started`) starts everything over. What each refusal does — the server's
and the bank's alike, one type — is `domain/setupRefusal`, on the code and never the status; what
step 1 offers (`waysToPay`) and whether _Accept_ agrees to the terms in force (`wordsInForce`) are
`domain/setupSteps`'. The secret lives in a ref for as long as the
screen does, never in state a render could print.

**The three setup writes are made online or not at all** (`networkMode: 'always'`), the one place the
app's paused-and-resumed mutations are not wanted besides challenges': a press in a flow the player is
standing in, with Stripe's native half between the writes, should say _couldn't reach Rakieta_ now
rather than resume a setup minutes later.

**The terms are evidence.** `PAYMENT_TERMS` (version `2026-09-29`, the backend's, until #642 put
Q113's `2026-10-10` in force, below) is §12.5 compressed from the mock's own sentences (45), plus the
one promise the mock dropped — a game still short at the cut-off is called off with everything back. The backend records the version, never the words, so a
changed word is a new version with the backend's, the old words kept, so every recorded acceptance
still points at the words it was shown. A setup that answers another version shuts _Accept_ and
says the app needs updating. Reviewed by a
lawyer before launch (O3).

**Change keeps the old method working; Remove is the server's to refuse** (Q83). _Change_ opens the
checklist under _Card •••• 4312 keeps working until the new one is saved_, with _Keep this one_ to
close it; nothing is removed first. _Remove this method_ is sent, and a `payment_method_in_use`
refusal is said under the link with its counts (`schemas/methodInUse` parses `details` — an untyped
dictionary — so a refusal whose counts do not parse still says why in words).

**A card the bank moved to another brand asks for the terms again** (§12.5): the read's
`terms_needed` puts an amber note, the terms and _Accept the terms_ on state B, and the row adds
_accept the terms again_. One `POST …/terms` with no setup open; it answers no secret, and the read is
re-read. This was not in #552's criteria and is here because without it the card is uncharged with no
way to mend it on the phone.

**Stripe is a platform port.** `shared/lib/platform/payments.tsx` is the only importer of
`@stripe/stripe-react-native` (lint, `pnpm test:boundaries`), and the one port that carries a
**component** — `CardFields`, Stripe's `CardField` styled to mock 43 — beside its three verbs
(`phoneWallet`, `takeCard`, `confirmSetup`). See [`_shared.md`](_shared.md). Screens reach it through
`usePayments()`; suites through `fakePayments()`, which behaves as Stripe's test cards do (4242 saves,
3155 is checked once, 0002 is declined) with one text input for the fields, and the router harness
always provides one (`stubPayments` to drive it). **A key that is not Stripe's is the laptop's
provider** — the backend's in-process fake, whose setups confirm themselves as they are read — so the
port takes the card and answers _saved_ without calling anybody, and a laptop run walks on a device.
It is the key that decides, never the environment's name.

**Stripe's fields are one row, where the mock draws three boxes.** `CardField` is Stripe's
single-line field (number, then expiry and CVC as it scrolls), and the SDK draws no separate boxes;
it is styled with the text field's surface, border and radius and the number in the mono face. The
alternative, `CardForm`, draws a country and postcode Rakieta does not need. Part 16.

**The deck hosts the setup as a sheet** ([#555](https://github.com/Raketa02/Raketa/issues/555)):
`PaymentSetupSheet` is the same checklist over a line, titled _Before your first yes_, opened by the
fill when a yes meets nothing saved (`usePaymentSetupNeeded`, the read's `method === null`) or the
server refuses one `payment_method_required`. `onSaved` lands the yes; closing drops it, and the close
control says so. Mounted only while open, so each opening is a fresh visit — one setup each. **Not
seen on a device**: the Stripe SDK needs a development build rebuilt with it (`pnpm ios` / `pnpm android`), and
no Stripe test key exists yet (O7, #533) — against a laptop's fake provider the card path is walkable
and saves the fake's Visa 4242 whatever is typed.

**State B places the live yeses; it does not read them** ([#554](https://github.com/Raketa02/Raketa/issues/554)).
_LIVE YESES_ is the proposals feature's section — the deck's answers, whose details are the deck's
screen — and the deck will open this feature's setup as a sheet (A2.4), so the edge points from
there to here. `PaymentsScreen` takes a `liveYeses` slot, drawn under the method in state B only,
and the route file `you/payments.tsx` composes it. See [`proposals.md`](proposals.md).

**RECEIPTS close state B** ([#555](https://github.com/Raketa02/Raketa/issues/555); A7.3; mock 49).
`GET /players/me/receipts` is this feature's own read (`useReceipts`, `paymentKeys.receipts()`):
every share paid, newest first as served, **the club as the row's title** — the seller (§12.1) — and
_Padel · Today · 16:00_ under it, the amount signed with a true minus (_−28 zł_). Refunds (↩ on
`mintSoft`, _+26,58 zł_ in `mintInk`) are served since #544, and the kinds are `Exact` with the
wire's (#557). **A refunded share is two rows under one payment** — the charge and its refund share
a `seat_charge_id` — so a row is keyed by the payment and its kind.
Empty, the section says what will land there; the refund-timing footer is drawn under rows only. A
receipt is a record, not a door — the game is reached from Home. State B alone, as the screens draw
it. A booking anywhere re-reads the list (the fill, through `paymentKeys` on `types.ts`).

**A refused share is read here and confirmed on the phone here; the yes again is proposals'** —
and so is _TO CONFIRM_, the list of them, placed on state B by the route file above _LIVE YESES_
(`toConfirm` slot). How a share is confirmed is `confirmsWith` (a decline with another card typed
for it, anything else the bank's check over the card on file).
([#555](https://github.com/Raketa02/Raketa/issues/555); #541). `useSeatCharge` reads `GET
/seat-charges/{id}` for what the confirmation draws — the share, the seller, the game, why it was
refused — **mapped without its secret**; `useConfirmOnPhone` reads it again for the press, hands the
secret straight to the port and never caches it (the setup's rule). The port's fourth verb,
`confirmPayment`, confirms **on the club's account** (a direct charge; Stripe started with the
club's `stripeAccountId`): with the card on file it re-confirms the payment with the card its last
error names — Stripe's recovery for an off-session payment that wanted its customer — and with
another card it pays from the fields on screen. It answers `confirmed · cancelled · declined ·
failed`, never an error; the fake answers the bank's check as `bank` says and a typed card as its
number does, and records every confirmation in `payments`. **Owed to the backend**: a laptop run's
in-process provider confirms setups as they are read but never a payment, so the confirmation is
refused `payment_not_confirmed` on a laptop — only a test key (O7) walks it end to end. **Not seen on
a device**, and `retrievePaymentIntent` / `confirmPayment` on a connected account have met only the
type checker.

**The confirmation names the time to pay** ([#630](https://github.com/Raketa02/Raketa/issues/630);
the backend's #625 and #626; the mechanics Q109). A refused share now holds its player's seat for
thirty minutes, never past the book-by, and the sheet says until when in an amber note: _Confirm your
payment by 14:40 to keep your seat_, the notice's and the email's words, the time written as Home
writes it. **The seat charge's read does not carry the time**: `GET /seat-charges/{id}` is the
Payments context's, and the time to pay is the game's, held by Proposals. So whoever opens the sheet
hands it in (`ConfirmAsk.confirmBy`): the yes's answer (`your_payment.confirm_by`), a _TO CONFIRM_
row (`confirm_by`), a game's details. Once the time ran out there is nothing to name, and no note —
nor for a time already past when the sheet reads the payment, which a row read earlier can hand in.
Each _TO CONFIRM_ row now says its own state — _Confirm your payment by 14:40_ in amber while the time
runs, _Your seat stays open until you confirm — or someone else takes it._ once it ran out — where the
section used to say the second for every row. **Why**: the old sentence was false for a held seat,
which nobody else can take until the time ends, and one list can hold both. The rows, the yes again
and what a booked confirmation shows are `proposals.md`'s.

**The confirmation reads by the window the server names**
([#643](https://github.com/Raketa02/Raketa/issues/643), [#645](https://github.com/Raketa02/Raketa/issues/645);
the backend's #638 and #640; the mechanics Q113, §12.2). Before the club's cut-off nothing is being
taken, so a refused card is fixed, never paid: the sheet is _Fix your card_, its note _Fix your card
by 14:40 to keep your seat_, a line _Nothing is paid now — fixing your card only places the hold
again._, the bank's check _Your bank wants you to confirm the hold on your card yourself._ and
a decline _Your bank declined the hold on the card on file. Fix it with another card._ over **Use this
card**. After it, the words above. **Whoever opens the sheet hands the window in with the time**
(`ConfirmAsk.timeTo`, from `time_to`), since the seat charge's read carries neither, and the sheet
reads both as of its opening (`paymentWindowAt`). With no window named — a time run out, an older
server — the words say _confirm_, never _pay_: a decline reads _Your bank declined the card on file.
Use another card for this share._ over **Use this card**, since a seat taken back before the cut-off
is held, not paid. **On a rescue** the seat is kept for the player to take (#640), so the note
reads _Fix your card by 14:40 to take the seat — it's kept for you until then_; the fill knows a rescue
by the card the yes was said on, and a _TO CONFIRM_ row holds none. The words are `proposals.md`'s
record; `FILL_COPY.confirm` keys each by the window.

**Decided, and built since #642 and #644 (below): new terms, and receipts that explain every
movement** (the mechanics
Q113 and §12.5, the screens A7.3; [ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-10-10 amendment; root [#635](https://github.com/Raketa02/Raketa/issues/635)). **Why**: a share is
now held when its game fills and taken at the club's cut-off, so the terms, the method card's
_Charged by the club when a game fills_ and the receipts must say what really happens. `PAYMENT_TERMS`
gets a new version with §12.5's words, under the version the backend puts in force, and a player who
accepted the old one accepts again before their next game holds money ([#637](https://github.com/Raketa02/Raketa/issues/637), [#642](https://github.com/Raketa02/Raketa/issues/642)).
Receipts read _−40 zł · paid_ for a share taken, _+38,24 zł · refunded_ over _1,76 zł kept on your
payment_ for a refund, and _40 zł held · released_ for a hold let go; the card check never appears,
and the footer loses its BLIK line ([#641](https://github.com/Raketa02/Raketa/issues/641), [#644](https://github.com/Raketa02/Raketa/issues/644)).

**The terms in force are Q113's** ([#642](https://github.com/Raketa02/Raketa/issues/642); the
backend's #637; the mechanics §12.5, the screens A7.3). `PAYMENT_TERMS_VERSION` is `2026-10-10`, the
version #637 put in force, and `PAYMENT_TERMS` is §12.5's text without its first sentence (_Your card
is saved_ is not yet true on step 3): the share held when a game fills, or the card checked and the
share held four days before the cut-off; taken at the club's cut-off; nothing taken for a leave
before it; after it the share back less what was kept on the payment if the seat is taken; a game
short at the cut-off called off with nothing taken. The retired words stay in `RETIRED_PAYMENT_TERMS`,
keyed by their version. **A player who accepted the earlier words** meets state B's amber note, the
terms and _Accept the terms_, as for a changed brand. The read's `terms_needed` does not say which of
the two it is, so the note names both: _Clubs can't hold your share on this card until you accept the
terms in force — they changed, or your bank moved the card to another network._ **Why**: the earlier
words promised a refund less the card fee for a leave before the cut-off, which no longer happens.

The method card reads _Held when a game fills · taken by the club at its cut-off_, step 4 _…it lets
the club hold and take your share later without you present_, and the receipts' footer _Refunds can
take up to two weeks to reach your card._, with no BLIK line. **A hold let go** (`RELEASED`, #641) was
left out of the receipts by the mapper until #644 drew it (below). **Calls made without a ruling**: the setup sheet's
_Before your first yes_ line, which the spec leaves open for the product owner, now reads _Save how you
pay. Nothing is held until a game you said yes to fills, and nothing is taken before the club's
cut-off._; and the terms-again note's words. **Owed to the lawyer** (O3): the clause after the
cut-off. **Nothing here has been seen on a device.**

**Receipts explain every movement of the money** ([#644](https://github.com/Raketa02/Raketa/issues/644);
the backend's #641; the mechanics Q113, §12.1, [ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-10-10 amendment; the screens A7.3). Ivan left Thursday's game after the
cut-off and Diego took his seat, so his receipts read _−40 zł · paid_ and _+38,24 zł · refunded_ over
_1,76 zł kept on your payment_. A player who left before the cut-off reads _40 zł held · released_
over _Released 28 Sep_. **Why**: the share is held at the fill and taken at the cut-off (Q113), so a
bank app shows holds that never became payments; a receipt that says the hold was let go, and when,
explains it, and a refund says to the grosz what was kept.

- **Three kinds, `Exact` with the wire's** (`ReceiptKind`): `CHARGE` (✓ on `paper2`, ink), `REFUND`
  (↩ on `mintSoft`, `mintInk`), `RELEASED` (Feather `unlock` on `paper2`, all `muted`, unsigned —
  nothing moved). The `Exclude` stopgap in `mappers/wireVocabulary.ts` is gone.
- **What the movement leaves to explain is a third line** (`receiptNote`): exactly what was kept on a
  refund's payment (`card_fee_grosze`, carried as `keptGrosze` on a refund alone), nothing for a
  refund in full, where nought was kept; and on a hold let go, the day it was let go (`paid_at`, now
  carried as `movedAt`), a date as a bank app dates the hold. The spoken label carries both.
- **The amount shares the club's line** in the row, where it was centred beside the club and the game
  under it: _+38,24 zł · refunded_ in the number role is half the row's width, and beside a two-line
  block of words it would squeeze the game's line onto two. The game's line and the note now run the
  row's whole width.
- **The footer** keeps no BLIK line (#642), asserted by the screen test.

**Calls made without a ruling**: the released row's date is the day the hold was let go, as the
backend dates it (`paid_at`, _dated when it was let go_ in its tests), drawn _Released 28 Sep_ — the
screens say only _with its date_; the open lock as its glyph; and a refund in full drawing no _0 zł
kept_ line. **Nothing here has been seen on a device**: the amount on the club's line and the three
rows want a look.
