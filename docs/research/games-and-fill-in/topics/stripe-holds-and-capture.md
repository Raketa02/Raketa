# Stripe — holds and capture

What Stripe says about holding a card and taking the money later, for the way Raketa uses it at
`9ab0ea5b`: a **direct charge on the club's connected account** (Accounts v2, full Dashboard, Stripe
collects the fees), in **złoty**, made **off-session** with **manual capture** on a single-use copy
of the player's saved card. A share is held at the fill and **kept until the club's cut-off**, then
taken; it is let go (cancelled) by a leave, a game short at its cut-off or the club's cancel. When a
hold would not last until six hours after the cut-off, it is **checked** (held and let go at once)
and **held again at its Holding time**, four days before the cut-off; a holding that still falls
short is taken at its last moment less six hours (`backend/app/modules/payments/domain/seat_charge.py:84-119`,
`backend/app/modules/payments/infrastructure/stripe_payments.py:485-581`).

Read 2026-10-19 from docs.stripe.com (English pages, `?locale=en-US`; the default locale served
Spanish, and one table differs — see *Extended authorisation*), the Stripe documentation search, and
the test club's account through the `stripe-club` server (read only). Facts carried from earlier
rounds keep their dates. Not repeated here, only pointed to: what the sandbox measured
([`stripe-sandbox.md`](stripe-sandbox.md)), retries and idempotency on a capture
([`stripe-reliability.md`](stripe-reliability.md)), the events ([`stripe-webhooks.md`](stripe-webhooks.md)),
the fee and the law on a leaver's refund ([`gaps-S-01A-leave-fee.md`](gaps-S-01A-leave-fee.md)),
and what Polish banks show ([`gaps-S-01A-hold.md`](gaps-S-01A-hold.md), [`gaps-S-01B.md`](gaps-S-01B.md)).
Amounts are złoty; Stripe stores grosze.

## 1. Placing a hold

### Manual capture holds the amount now and takes it later

- **[DOCS]** "Authorizing a payment guarantees the amount by holding it on the customer's payment
  method." "To indicate that you want separate authorization and capture, specify `capture_method`
  as `manual` when creating the PaymentIntent. This parameter instructs Stripe to authorize the
  amount but not capture it." "After the payment method is authorized, the PaymentIntent status
  transitions to `requires_capture`." The Dashboard lists such a payment as **Uncaptured**.
  [Place a hold on a payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US)
  — read 2026-10-19
- **[DOCS]** "When a customer completes the payment process on a PaymentIntent with manual capture,
  it triggers the `payment_intent.amount_capturable_updated` event. You can inspect the
  PaymentIntent's `amount_capturable` property to see the total amount that you can capture." The
  event: "Occurs when a PaymentIntent has funds to be captured." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US),
  [event types](https://docs.stripe.com/api/events/types?locale=en-US) — read 2026-10-19

### On a direct charge the hold, and everything done to it, lives on the club's account

- **[DOCS]** Direct charges: "You create a charge on your connected account, so the payment appears in
  the connected account's balance, not in your platform's balance." "Refunds and chargebacks reduce
  the connected account's balance." [Connect charges](https://docs.stripe.com/connect/charges) — read 2026-10-19
- **[MEASURED]** Carried: every share on the test club is `capture_method: manual`, `currency: pln`,
  `customer: null`, statement descriptor `ROBER CLUB` (the club's, not Raketa's) —
  [`stripe-sandbox.md#payments-on-the-test-club-manual-capture-off-session-on-a-single-use-copy-of-the-card`](stripe-sandbox.md#payments-on-the-test-club-manual-capture-off-session-on-a-single-use-copy-of-the-card),
  read 2026-10-19

### Only cards can be held among the methods a Polish player uses; BLIK cannot

- **[DOCS]** "Only some payment methods support separate authorization and capture. Some payment
  methods that support this include cards, Affirm, Afterpay, Cash App Pay, Klarna, and PayPal." "You
  can't accept card payments and SEPA Direct Debit (which doesn't support capture after) for a single
  PaymentIntent"; per-method capture is set with `payment_method_options[<type>][capture_method]=manual`.
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- **[DOCS]** Carried: BLIK "Manual capture support: No".
  [`gaps-S-01A-leave-fee.md#blik-cannot-be-held`](gaps-S-01A-leave-fee.md#blik-cannot-be-held) — read 2026-10-10

## 2. How long a hold lasts

### Online card holds: Visa 4 days 18 hours without the payer, 7 days with; Mastercard, Amex, Discover 7

- **[DOCS]** Card-not-present, merchant-initiated against customer-initiated: **Visa "5 days\*" against
  "7 days"**; Mastercard, American Express and Discover 7 against 7. "\* The exact authorization
  window is 4 days and 18 hours, to allow time for clearing processes." In person: Visa 4 days 18
  hours, the others 2 days. "Card payments: The amount is typically on hold for 7 days for online
  payments and 2 days for in-person Terminal payments (depending on the type of transaction and the
  card network)." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US)
  — read 2026-10-19 (the same table as 2026-10-10 and 2026-10-11:
  [`gaps-S-01A-hold.md#stripes-published-windows-visas-4-days-18-hours-is-the-shortest`](gaps-S-01A-hold.md#stripes-published-windows-visas-4-days-18-hours-is-the-shortest))

### Stripe decides "with or without the payer" from signals, not from `off_session`

- **[DOCS]** "Stripe and the card network classify transactions as MIT or CIT based on signals of
  cardholder participation, not solely on API parameters like `off_session`. For example, a payment
  with `off_session: true` might still be classified as a CIT if a CVC is present, resulting in the
  CIT authorization window instead." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US)
  — read 2026-10-19
- **[DOCS]** An MIT is "a transaction that you initiate without direct participation of your
  customer, based on a prior agreement with that customer authorizing you to store and use their
  credentials". "When a card's brand changes, you can't charge it for any MITs until you get a new
  cardholder agreement." [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-US) — read 2026-10-19

### `capture_before` on the charge is the window to trust, and it does not move once confirmed

- **[DOCS]** "the `payment_method_details.card.capture_before` attribute on the charge is the most
  reliable and accurate way to determine your charge's authorization window."
  [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-US) — read 2026-10-19
- **[DOCS]** "we recommend that you rely on the `capture_before` field to confirm the validity window
  for any given payment because these rules can change without prior notice." "The validity window
  won't change after the PaymentIntent is confirmed."
  [Extended authorization](https://docs.stripe.com/payments/extended-authorization?platform=web&ui=elements) — read 2026-10-19
- **[DOCS]** API reference: `capture_before` — "When using manual capture, a future timestamp at which
  the charge will be automatically refunded if uncaptured." [Charge object](https://docs.stripe.com/api/charges/object?locale=en-US)
  — read 2026-10-19
- **[DOCS]** "The `capture_before` field is located on the Charge, so it's only present after the
  `PaymentIntent` is confirmed." [Terminal extended authorizations](https://docs.stripe.com/terminal/features/extended-authorizations)
  — read 2026-10-19 (a Terminal page; the field sits on the charge for online payments too, per the
  Charge object)
- *reading:* a PaymentIntent read without `latest_charge` expanded carries no `capture_before`. The
  adapter expands it on the hold and on every reading (`stripe_payments.py:510-511`, `:544-551`,
  `_THE_FEE` at `:112`).

### Visa's own rule since April 2024: 5 days when the merchant charges, 10 when the cardholder does

- **[DOCS]** Carried: "CNP (cardholder-initiated) transactions — 10 calendar days … All
  merchant-initiated transactions — Five calendar days", effective 13 April 2024, addressed to U.S.
  acquirers; Visa's European notice not found.
  [`gaps-S-01B.md#visas-own-rule-since-13-april-2024-10-days-for-a-payment-the-cardholder-makes-online-5-for-one-the-merchant-makes`](gaps-S-01B.md#visas-own-rule-since-13-april-2024-10-days-for-a-payment-the-cardholder-makes-online-5-for-one-the-merchant-makes)
  — read 2026-10-10

### Cards issued in Poland are almost all Visa or Mastercard

- **[DOCS]** Carried: NBP, Q3 2022 — Visa 53,3 %, Mastercard 46,5 %.
  [`gaps-S-01A-hold.md#cards-issued-in-poland-are-almost-all-visa-or-mastercard`](gaps-S-01A-hold.md#cards-issued-in-poland-are-almost-all-visa-or-mastercard)
  — read 2026-10-11

### On the sandbox an off-session Visa hold lasts exactly 7 days, and offers nothing beyond a plain hold

- **[MEASURED]** `stripe-club` · `ch_3USA7i5y1DMwE3zY09j5MxD1` (payment `pi_3USA7i5y1DMwE3zY0Nemxwtn`,
  40,00 zł, Visa •••• 4242, made off-session by the contract run): created 2026-10-19 06:32:43 UTC,
  `capture_before` 1792996363 = **2026-10-26 06:32:43 UTC**, exactly 168 hours later;
  `cvc_check: pass`, `three_d_secure: null`; `extended_authorization.status: disabled`,
  `incremental_authorization.status: unavailable`, `multicapture.status: unavailable`,
  `overcapture.status: unavailable` with `maximum_amount_capturable: 4000`; `captured: false`,
  `balance_transaction: null` · read 2026-10-19. The same shape as the twelve payments in
  [`stripe-sandbox.md#every-visa-hold-lasted-exactly-7-days`](stripe-sandbox.md#every-visa-hold-lasted-exactly-7-days).
- *reading:* the clone carries a passed CVC check, the signal Stripe names for classing a payment
  customer-initiated; whether a live clone of a card saved weeks earlier carries one is not
  documented. The live window can be either; only `capture_before` says which.

### A payment the player confirms in the app: its window is still unread

- **[ABSENT]** Carried: no page gives the window Stripe stamps on a payment first refused off-session,
  then confirmed by the customer with 3-D Secure; the sandbox's four bank-check demands skip (they need
  a browser), so no such payment exists to read.
  [`gaps-S-01B.md#the-real-capture_before-of-such-a-payment-still-not-read`](gaps-S-01B.md#the-real-capture_before-of-such-a-payment-still-not-read),
  [`stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser`](stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser)
  — read 2026-10-10 and 2026-10-19

### Nothing in test mode shortens a hold or moves its clock

- **[DOCS]** "Test clocks allow you to simulate `Billing` objects, like subscriptions, through time in a
  sandbox." [Test your Billing integration](https://docs.stripe.com/billing/testing) — read 2026-10-19
- **[ABSENT]** No test card or setting that gives the 4 days 18 hours Visa window, or that makes a hold
  lapse early, was found. Searched: Stripe's documentation search ("test card … short authorization
  window", "uncaptured PaymentIntents expire … test mode"), the hold, extended-authorisation,
  incremental, multicapture and overcapture pages (their test cards cover only availability) — read 2026-10-19

## 3. Taking the money

### A capture takes the whole hold unless told less; a partial capture lets the rest go, once

- **[DOCS]** "This captures the total authorized amount by default. To capture less or (for certain
  online card payments) more than the initial amount, pass the `amount_to_capture` option. **A partial
  capture automatically releases the remaining amount.**" "You can only perform one capture on an
  authorized payment for most payments. If you partially capture a payment, you can't perform another
  capture for the difference. (Instead, consider saving the customer's payment method details for
  later and creating future payments as needed.)"
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- **[DOCS]** `amount_to_capture`: "must be less than or equal to the original amount. Defaults to the
  full `amount_capturable`." `application_fee_amount` on capture: "capped at the total amount
  captured". [Capture a PaymentIntent](https://docs.stripe.com/api/payment_intents/capture?locale=en-US) — read 2026-10-19
- **[DOCS]** Stripe's own advice: "Manual authorization and capture lets you better control costs by
  canceling payments before they're captured, or by reducing your captured amount rather than
  processing a refund." [Refunds, cost optimization](https://docs.stripe.com/refunds?locale=en-US#cost-optimization) — read 2026-10-19
- *code:* the adapter never passes `amount_to_capture` (`stripe_payments.py:554-567`): every capture
  takes the whole share.

### A capture works only on `requires_capture`, and answers anything else with an error

- **[DOCS]** "Capture the funds of an existing uncaptured PaymentIntent when its status is
  `requires_capture`. **Uncaptured PaymentIntents are cancelled a set number of days (7 by default)
  after their creation.**" Returns "a PaymentIntent object with `status="succeeded"` if the
  PaymentIntent is capturable. Returns an error if the PaymentIntent isn't capturable or if an
  invalid amount to capture is provided." [Capture a PaymentIntent](https://docs.stripe.com/api/payment_intents/capture?locale=en-US)
  — read 2026-10-19

### The error codes for a capture that comes too late or finds the wrong state

- **[DOCS]** `charge_expired_for_capture`: "The charge can't be captured because the authorization has
  expired. Authorization and capture charges must be captured within a set number of days (7 by
  default)." `capture_charge_authorization_expired`: "The charge can't be captured as the
  authorization has expired. Refer to the payment method's documentation to learn more."
  `payment_intent_unexpected_state`: "The PaymentIntent's state was incompatible with the operation
  you were trying to perform." `charge_already_captured`: "Inspect the charge to confirm whether the
  intended capture is complete." [Error codes](https://docs.stripe.com/error-codes?locale=en-US) — read 2026-10-19
- **[ABSENT]** Which of these a PaymentIntent capture returns once its hold has lapsed is not stated.
  Searched: the capture reference, the hold page, the lifecycle page, the error-code table — read
  2026-10-19. Carried: the reliability round reads either as an `InvalidRequestError` the outbox would
  repeat ([`stripe-reliability.md`](stripe-reliability.md), pitfall 5).

### Stripe's own backstop captures about six hours before a hold lapses (private preview)

- **[DOCS]** `capture_method=automatic_delayed` (private preview): "Stripe captures your card payment
  before the authorization expires, triggering the capture about 6 hours before the expiration time.
  This serves as a backup process to make sure we capture authorized payments before expiration. You
  can still manually capture or cancel the PaymentIntent before it's automatically captured."
  `capture_by`: `auth_expiry` (default), `end_of_day`, or `target_delay` with a `capture_delay` of days
  or hours up to 30 days; "If the authorization window is shorter than the specified delay period, we
  capture the PaymentIntent before expiration, ignoring the delay period."
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- *code:* the six hours are the product's `REACH_MARGIN` (`seat_charge.py:84-87`, citing this page);
  the product captures itself, from a 30-second job and the outbox, and does not use the preview.

### A club on the full Dashboard can capture or cancel a held share itself

- **[DOCS]** "To capture the funds, go to the payment details page and click **Capture**."
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US); "You can
  cancel a payment using the Dashboard when its status is `uncaptured`" — click the payment, then
  **Cancel**, and choose a reason. [Refunds, cancel a payment](https://docs.stripe.com/refunds?locale=en-US#cancel-payment)
  — read 2026-10-19
- **[DOCS]** "The Stripe Dashboard gives connected accounts unrestricted access to Stripe's full
  feature set using their own login credentials. Connected accounts can sign into dashboard.stripe.com
  directly at any time." "The dashboard you specify when creating a connected account is permanent."
  [Design an advanced Connect integration](https://docs.stripe.com/connect/design-an-integration); the
  payments embedded component lets accounts "view payment information, capture charges, and manage
  disputes". [Direct charges](https://docs.stripe.com/connect/direct-charges?platform=web&ui=embedded-page)
  — read 2026-10-19
- *code:* clubs are opened with `dashboard: full` (`stripe_payments.py:317-347`, per
  [`stripe-sandbox.md#the-calls-the-adapter-makes-and-on-which-account`](stripe-sandbox.md#the-calls-the-adapter-makes-and-on-which-account)).

## 4. Making a hold longer, larger or split

### Extended authorisation: up to 30 days, on IC+ pricing, and for Visa outside travel only when the customer pays

- **[DOCS]** "We offer extended authorizations to users on IC+ pricing. If you're on blended Stripe
  pricing and want access to this feature, contact us." No regional restrictions; Visa, Mastercard,
  Amex and Discover only. Windows: **Visa** — hotel, lodging, vehicle rental, cruise line, and "All
  other merchant categories\*": 30 days (exactly 29 days 18 hours); **Mastercard (not including Maestro
  and Cirrus cards)** — all merchant categories, 30 days; Amex — lodging and vehicle rental; Discover —
  travel categories. "\* For other merchant categories, Stripe charges an additional 0.08% fee per
  transaction. **The extended window only applies to Customer-Initiated Transactions** and doesn't
  apply to transactions with businesses in Japan or transactions related to healthcare, bill payment,
  or debt repayment."
  [Extended authorization](https://docs.stripe.com/payments/extended-authorization?platform=web&ui=elements)
  — read 2026-10-19 (the Spanish rendering of the same page says Mastercard "Maestro y Cirrus
  incluidas"; the English page governs)
- **[DOCS]** "You're responsible for your compliance with all applicable laws, regulations, and
  network rules when using extended authorization. … For instance, **for many networks extended
  validity windows are only for cases where you don't know the final amount that you'll capture** at
  the time of authorization." "Customers see their funds held longer when you use extended
  authorizations. Use clear statement descriptors to avoid increased disputes from unrecognized
  payments." Requested per payment with `payment_method_options[card][request_extended_authorization]=if_available`;
  granted when the charge's `extended_authorization.status` reads `enabled`. Same page — read 2026-10-19
- **[MEASURED]** The test club's holds read `extended_authorization.status: disabled` (none is
  requested) — see *On the sandbox an off-session Visa hold lasts exactly 7 days* above.
- *reading:* a share held without its player, at a sports club, for a price known at the hold, meets
  none of the Visa conditions and the Mastercard compliance note; the clubs are on Stripe's standard
  pricing (Stripe collects the fees). Carried with the same conclusion:
  [`gaps-S-01A-leave-fee.md#extended-holds-do-not-fit-off-session-charges-at-a-sports-club`](gaps-S-01A-leave-fee.md#extended-holds-do-not-fit-off-session-charges-at-a-sports-club) — read 2026-10-10

### Incremental authorisation raises the amount, never the window

- **[DOCS]** IC+ only ("If you're on standard Stripe pricing … contact us"). "Whether you increase the
  authorized amount on a PaymentIntent with an incremental authorization or not, you need to capture
  the funds before the initial authorization expires–**incremental authorizations don't extend the
  validity period**." A declined increment returns `card_declined` and "the PaymentIntent object
  remains capturable for the previously authorized amount"; at most 10 attempts per PaymentIntent.
  Networks "prohibit the use of incremental authorizations for transactions where the transaction
  amount should be known at the time of authorization". Under SCA, increments after a 3DS-authenticated
  first authorisation are "considered merchant-initiated".
  [Incremental authorization](https://docs.stripe.com/payments/incremental-authorization?platform=web&ui=elements)
  — read 2026-10-19

### Multicapture takes one hold in several parts, for goods shipped separately

- **[DOCS]** IC+ only; online cards; `request_multicapture=if_available`, then `final_capture=false`
  keeps the rest held; "Stripe allows up to 50 non-final captures". The PaymentIntent stays
  `requires_capture` until a final capture "or the authorization window expires"; then "Uncaptured
  PaymentIntents transition to `canceled`, while partially captured PaymentIntents transition to
  `succeeded`." Networks "restrict multicapture usage to card-not-present transactions for the sale of
  goods that ship separately". Supports all Connect cases except separate charges and transfers with
  `source_transaction`. [Multicapture](https://docs.stripe.com/payments/multicapture?platform=web&ui=elements)
  — read 2026-10-19

### Overcapture is closed to Visa for businesses in the EEA

- **[DOCS]** IC+ only. Visa: "\* Excludes businesses in the European Economic Area (EEA)"; Mastercard:
  US restaurants, card issued in the US; Amex and Discover: named categories only (lodging, car rental,
  restaurants and the like). "Under SCA requirements, you generally need to authenticate an amount
  that's greater than or equal to the amount that you eventually capture … If you find it necessary to
  capture an amount beyond the originally authorized and authenticated amount, you must cancel the
  original payment and create a new one with the correct amount."
  [Overcapture](https://docs.stripe.com/payments/overcapture?platform=web&ui=elements) — read 2026-10-19
- *reading:* for a Polish club none of the four stretches a hold to a far cut-off or lets a held share
  grow; a share that must change after its hold is captured smaller, or let go and held again.

### Renewing an online hold before it lapses: still documented only in person

- **[DOCS]** Carried: Stripe Terminal's `request_reauthorization` "Allows reauthorizing an expired
  PaymentIntent", a card-present setting.
  [`gaps-S-01A-hold.md#stripe-documents-reauthorisation-only-for-in-person-payments-and-no-objection-to-a-new-hold`](gaps-S-01A-hold.md#stripe-documents-reauthorisation-only-for-in-person-payments-and-no-objection-to-a-new-hold)
  — read 2026-10-11
- **[ABSENT]** Searched again for an online reauthorisation or a renewal of an expiring hold: Stripe's
  documentation search ("reauthorize an expired or expiring uncaptured online card payment"), the
  CIT/MIT page (its only "re-authorization" is a new cardholder agreement after a brand change), the
  hold page — read 2026-10-19. A later hold is a new PaymentIntent on the saved card, as the hold page
  itself suggests for the uncaptured difference ("creating future payments as needed").

## 5. Letting a hold go

### Cancelling releases the held money at no cost and cannot be undone

- **[DOCS]** "You can cancel a payment before it's completed at no cost." "If you … refund a
  PaymentIntent that has a status of `requires_capture` … the charge attached to the PaymentIntent
  remains uncaptured and can't be refunded directly. **You must cancel the PaymentIntent.**" "A
  PaymentIntent can't be canceled after it has succeeded. … Any operations that your application
  attempts to perform on a canceled PaymentIntent fails with an error."
  [Refund and cancel payments](https://docs.stripe.com/refunds?locale=en-US) — read 2026-10-19
- **[DOCS]** Cancellable from `requires_payment_method`, `requires_capture`, `requires_confirmation`,
  `requires_action` or, rarely, `processing`. "After it's canceled, no additional charges are made by
  the PaymentIntent and any operations on the PaymentIntent fail with an error. For PaymentIntents with
  a `status` of `requires_capture`, the remaining `amount_capturable` is automatically refunded."
  "Returns an error if the PaymentIntent is already canceled or isn't in a cancelable state."
  [Cancel a PaymentIntent](https://docs.stripe.com/api/payment_intents/cancel?locale=en-US) — read 2026-10-19
- **[DOCS]** "Cancellation invalidates the PaymentIntent for future payment attempts, releases any held
  funds, and can't be undone." [PaymentIntent lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle?locale=en-US)
  — read 2026-10-19
- **[DOCS]** Carried: no fee is listed for an authorisation never captured.
  [`gaps-S-01A-leave-fee.md#letting-a-hold-go-before-it-is-taken-costs-nothing`](gaps-S-01A-leave-fee.md#letting-a-hold-go-before-it-is-taken-costs-nothing) — read 2026-10-10

### Why a payment was cancelled: four reasons the caller gives, four Stripe sets

- **[DOCS]** `cancellation_reason`: "either user-provided (`duplicate`, `fraudulent`,
  `requested_by_customer`, or `abandoned`) or generated by Stripe internally (`failed_invoice`,
  `void_invoice`, `automatic`, or `expired`)." [PaymentIntent object](https://docs.stripe.com/api/payment_intents/object?locale=en-US&query=cancellation_reason)
  — read 2026-10-19
- **[MEASURED]** `stripe-club` · the contract run's let-go shares `pi_3USA7x5y1DMwE3zY0T8vWvEl`,
  `pi_3USA7t5y1DMwE3zY0KmsrW0N`, `pi_3USA7q5y1DMwE3zY0j8JqnVn` (40,00 zł each): `status: canceled`,
  `cancellation_reason: null` (the adapter gives none, `stripe_payments.py:569-581`), `canceled_at` one
  second after `created`; the charge of the first, `ch_3USA7x5y1DMwE3zY0r61YRsL`, reads `captured: false`,
  `amount_refunded: 0`, `refunded: false`, `balance_transaction: null`. Each cancel emitted
  `payment_intent.canceled` with the request's idempotency key (`evt_3USA7x5y1DMwE3zY0eJ7qzbS` and
  two more) · read 2026-10-19
- *reading:* a hold Raketa let go and a hold Stripe dropped are told apart only by
  `cancellation_reason` (null against one of Stripe's own) and by the event's `request` (Raketa's
  cancel carries its key).

### What the player sees when a hold is let go is the bank's to decide

- **[DOCS]** "Card statements from some issuers and interfaces from payment methods don't always
  distinguish between authorizations and captured (settled) payments, which can sometimes confuse
  customers." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- Carried: a matching reversal tells the bank to lift the hold, one that doesn't match leaves it 1 to 8
  days; Polish banks keep an unsettled hold 7 to 30 days and publish no release time.
  [`gaps-S-01A-hold.md#visa-a-reversal-that-matches-tells-the-bank-to-lift-the-hold-one-that-doesnt-leaves-it-1-to-8-days`](gaps-S-01A-hold.md#visa-a-reversal-that-matches-tells-the-bank-to-lift-the-hold-one-that-doesnt-leaves-it-1-to-8-days),
  [`gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished`](gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished)
  — read 2026-10-10 and 2026-10-11

### A full-share hold let go at once: the networks' word on checking a card

- **[DOCS]** "Card networks may also restrict 1 USD authorizations you don't intend to capture."
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- Carried: Visa asks acquirers to use account verification "instead of authorizations for erroneous
  amounts when validating cardholder accounts"; whether a full-share check counts as one is stated
  nowhere read.
  [`gaps-S-01A-hold.md#the-card-networks-limits-apply-to-retried-declines-and-to-checking-a-card-with-an-amount`](gaps-S-01A-hold.md#the-card-networks-limits-apply-to-retried-declines-and-to-checking-a-card-with-an-amount)
  — read 2026-10-11

### A card refused too often is locked for a day

- **[DOCS]** `card_decline_rate_limit_exceeded`: "This card has been declined too many times. You can
  try to charge this card again after 24 hours. We suggest reaching out to your customer to make sure
  they've entered all of their information correctly and that there are no issues with their card."
  [Error codes](https://docs.stripe.com/error-codes?locale=en-US) — read 2026-10-19 (Visa's reattempt
  limits are carried in the same `gaps-S-01A-hold.md` section)

## 6. When a hold lapses

### Stripe cancels a lapsed hold, releases the money, and says so

- **[DOCS]** "You need to capture the funds before the authorization expires. If the authorization
  expires before you capture the funds, the funds are released and the payment status changes to
  `canceled`." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US) — read 2026-10-19
- **[DOCS]** `charge.expired`: "Occurs whenever an uncaptured charge expires."
  `payment_intent.canceled`: "Occurs when a PaymentIntent is canceled." [Event types](https://docs.stripe.com/api/events/types?locale=en-US)
  — read 2026-10-19. The code reads `payment_intent.canceled` from the Connect endpoint and drops
  `charge.expired` ([`stripe-webhooks.md`](stripe-webhooks.md), `stripe_notices.py:61-69`).
- **[DOCS]** For multicapture only: "We send a `charge.captured` event for final captures or at the end
  of the authorization window to reverse the authorization of the uncaptured amount."
  [Multicapture](https://docs.stripe.com/payments/multicapture?platform=web&ui=elements) — read 2026-10-19

### Which reason and which events an expired hold carries: undocumented, readable on the sandbox after 26 October

- **[ABSENT]** Whether Stripe sets `cancellation_reason` to `automatic` or `expired` on a lapsed card
  hold, and whether `charge.expired` and `payment_intent.canceled` both arrive, is not stated. Searched:
  the hold, lifecycle, cancel, capture and event-type pages — read 2026-10-19.
- **[MEASURED]** `stripe-club` · `pi_3USA7i5y1DMwE3zY0Nemxwtn`, 40,00 zł, `status: requires_capture`,
  left uncaptured by the contract run; its charge's `capture_before` is **2026-10-26 06:32:43 UTC**.
  No `charge.expired` event exists on the account yet; the six `payment_intent.canceled` events all
  carry a request from the run · read 2026-10-19. *What would answer it:* after that moment, read the
  PaymentIntent (`status`, `cancellation_reason`, `canceled_at`) and the account's events of both types
  through `stripe-club`.

### A lapsed hold can be neither taken nor let go

- **[DOCS]** The hold page sets the payment to `canceled` on expiry; on a canceled PaymentIntent "any
  operations … fail with an error"; capture "Returns an error if the PaymentIntent isn't capturable";
  cancel "Returns an error if the PaymentIntent is already canceled". Pages as above — read 2026-10-19
- *code:* the product's fake answers a second cancel of a cancelled payment with success and refuses
  only a capture (`backend/app/modules/payments/infrastructure/fake_payments.py:678-705`); the Stripe
  adapter catches neither error on capture or cancel, mapping only outages (`stripe_payments.py:554-581`,
  `:641-654`).

## Pitfalls

1. **Reading the window from the table, or from the brand.** Stripe: rely on `capture_before`
   "because these rules can change without prior notice", and classification follows "signals of
   cardholder participation, not solely … `off_session`"
   ([extended authorization](https://docs.stripe.com/payments/extended-authorization?platform=web&ui=elements),
   [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US)). The fake
   models a Visa as 4 days 18 hours (`fake_payments.py:118-121`), the sandbox gives 7 days
   (`stripe-sandbox.md` D4): any rule or test that assumes either is wrong somewhere.
2. **Treating "no `capture_before`" as "lasts for ever".** The field is on the charge and "only present
   after the PaymentIntent is confirmed"; a reading without `latest_charge` has none. `reaches` answers
   *reaches* when the last moment is unknown (`seat_charge.py:96-100`), so a reading that lost the field
   keeps a hold past its real lapse.
3. **Capturing too close to the lapse.** Stripe's own backstop fires "about 6 hours before the
   expiration time" ([place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US)).
   A capture job that stops, or an outbox repeating a saved error ([`stripe-reliability.md`](stripe-reliability.md)
   pitfall 3), turns a held share into nothing: Stripe releases the money and the club is never paid.
4. **Capturing or cancelling a payment Stripe already cancelled.** Both "fail with an error"
   ([cancel](https://docs.stripe.com/api/payment_intents/cancel?locale=en-US)). A lapse, a cancel from the
   club's Dashboard, or a second let-go of a checked hold meets this; the fake treats a repeated cancel
   as success (`fake_payments.py:693-705`), so tests on the fake never see the error Stripe raises.
5. **Hearing the lapse as a status, not as a decision.** A lapsed hold arrives as
   `payment_intent.canceled` (and `charge.expired`, unread). Moving a *held* share to *cancelled*
   (`seat_charge.py:793-811`, via `heard` at `:812-831`) settles the money record but not who now owes
   the seat.
6. **Expecting extended authorisation to reach a far cut-off.** IC+ only; Visa outside travel "only
   applies to Customer-Initiated Transactions"; "for many networks … only for cases where you don't
   know the final amount" ([extended authorization](https://docs.stripe.com/payments/extended-authorization?platform=web&ui=elements)).
7. **Expecting an increment, a re-confirm or a reauthorisation to renew a hold.** "Incremental
   authorizations don't extend the validity period"; cancellation "can't be undone"; online
   reauthorisation is not documented. A renewed hold is a new PaymentIntent, with its own
   `capture_before`, decline risk and idempotency key.
8. **Changing a held share's amount.** Capturing less releases the rest and forbids a second capture;
   capturing more needs overcapture, which "Excludes businesses in the European Economic Area" for Visa
   ([overcapture](https://docs.stripe.com/payments/overcapture?platform=web&ui=elements)); under SCA a larger
   amount means "cancel the original payment and create a new one".
9. **Refunding a hold.** "The charge … remains uncaptured and can't be refunded directly. You must cancel
   the PaymentIntent." A path that refunds whatever it finds breaks on a share still held.
10. **Capturing then refunding what could have been captured less.** Stripe recommends "reducing your
    captured amount rather than processing a refund"; the original fee "isn't returned" on a refund
    ([refunds](https://docs.stripe.com/refunds?locale=en-US)). Every capture takes the whole share
    (`stripe_payments.py:554-567`).
11. **Forgetting the club can act on the hold.** A full-Dashboard club can press **Capture** or
    **Cancel** on an uncaptured payment
    ([place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US),
    [refunds](https://docs.stripe.com/refunds?locale=en-US#cancel-payment)); Raketa then hears a capture or a
    cancel it did not ask for.
12. **A full-share check let go at once.** "Card networks may also restrict 1 USD authorizations you
    don't intend to capture"; Visa wants account verification for validating a card (carried). The
    player sees one hold appear and vanish, then a second days later, on a statement that "don't always
    distinguish between authorizations and captured … payments".
13. **Retrying a refused hold without a limit.** `card_decline_rate_limit_exceeded` locks the card for
    24 hours ([error codes](https://docs.stripe.com/error-codes?locale=en-US)); Visa charges for excess
    reattempts (carried).
14. **Walking the hold window on the sandbox.** Holds there last 7 days, no test card or test clock
    shortens one, and an uncaptured test hold lapses only in real time (26 October for the oldest);
    every *the hold won't reach the cut-off* scene is reachable only on the fake.

## Checks

1. Is each decision about when to take a share computed from that payment's own `capture_before`,
   read from its charge, rather than from a table, a brand or a constant?
2. Is the share taken at least about six hours before `capture_before`, with time left for a failed
   capture to be retried before the hold lapses?
3. When `capture_before` is missing, does the rule assume the shortest documented window (4 days 18
   hours) instead of assuming the hold lasts?
4. For a game whose cut-off falls after the hold's last moment, does the rule either hold again on a
   new payment before the lapse or take the share early — and is the player told which, and when?
5. When Stripe drops a hold on its own, does the product hear it, and does a person decide what happens
   to the seat and to the club's money?
6. Does a capture or a cancel that finds the payment already cancelled (lapsed, cancelled by the club,
   or cancelled twice) end in a recorded outcome, not a delivery repeated for ever?
7. Is a held share ever refunded instead of cancelled, or a taken share ever cancelled instead of
   refunded?
8. Is the amount taken ever different from the amount held? If smaller, is it captured smaller rather
   than captured whole and refunded? If larger, is a new hold made?
9. Does any rule rely on extended, incremental, multicapture or overcapture? Each needs IC+ pricing,
   and none fits an off-session share of known price at a Polish club.
10. If the club presses **Capture** or **Cancel** in its own Dashboard, does Raketa's record of the
    share follow, and is anyone told?
11. When a share is let go, do the player's words match Stripe ("releases any held funds") and leave the
    timing to the bank?
12. Is a card check (a full-share hold let go at once) made only when the hold cannot reach the
    cut-off, and does the player know a second hold follows at the Holding time?
13. After a refused holding, how many times is the card tried again, and could the attempts lock it for
    24 hours before the cut-off?
14. When the player confirms a payment in the app, is the new `capture_before` read from the charge
    after confirmation, not inherited from the refused attempt?
15. Does each story or test that crosses a hold's lapse say whether it runs on the fake (Visa 4 days 18
    hours) or the sandbox (7 days, real time)?
