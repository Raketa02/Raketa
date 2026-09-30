# payments — You › Account › Payments

The client side of the backend's **Payment method** (#536): a player saves the way the clubs charge
them, and sees what is saved. Built by [#552](https://github.com/Raketa02/Raketa/issues/552) from the
Games & Fill in screens (A7, A7.3; mocks 40–47), the mechanics (§12.4, §12.5), Q82 and Q83, and
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) /
[ADR-0190](../../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md). The
shell composes `PaymentsRow` into the You tab's **ACCOUNT** group; the screen is
`/you/payments`. State B's _Live yeses_ and _Receipts_ (mocks 48, 49) are #554's and #555's.

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
standing in, with Stripe's native half between the writes, should say _couldn't reach Raketa_ now
rather than resume a setup minutes later.

**The terms are evidence.** `PAYMENT_TERMS` (version `2026-09-29`, the backend's) is §12.5 compressed
from the mock's own sentences (45), plus the one promise the mock dropped — a game still short at the
cut-off is called off with everything back. The backend records the version, never the words, so a
changed word is a new version with the backend's, the old words kept (`optInPresentation`'s rule). A
setup that answers another version shuts _Accept_ and says the app needs updating. Reviewed by a
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
alternative, `CardForm`, draws a country and postcode Raketa does not need. Part 16.

**Owed, not built:** the deck's _swipe right with no saved method_ opens this setup as a sheet
(A2.4) — the checklist is a component taking its setup, ready to be hosted there. **Not seen on a
device**: the Stripe SDK needs a development build rebuilt with it (`pnpm ios` / `pnpm android`), and
no Stripe test key exists yet (O7, #533) — against a laptop's fake provider the card path is walkable
and saves the fake's Visa 4242 whatever is typed.
