# Stripe gaps, round 02: FILL, LEAVE and PAY

Answers to sixteen open Stripe gaps from the payments pass on PRD #530, read **2026-10-20**.

- **How Stripe was read.** The Stripe MCP servers were disconnected, so Stripe's own pages were fetched from
  docs.stripe.com and support.stripe.com. Some pages came back in Spanish and are quoted *(translated)*.
- **How the sandbox was read.** Through the Stripe SDK in the run's code copy at `9ab0ea5b` (stripe-python 15.6.1,
  API `2026-08-26.dahlia`, test key). It was read only: nothing was created, updated or deleted. The test club is
  `acct_1US95f5y1DMwE3zY`. It is shared, so each object is judged by its own ID.
- **What each tag means.** `[DOCS]` is Stripe's own word, including its SDK source as installed. `[MEASURED]` is what
  the sandbox holds. `[ABSENT]` was looked for and not found, with where. A *reading* line is not a source.

Gaps already answered elsewhere are cited by anchor rather than repeated.

## Where each gap stands

| Rules | Gap | Now |
|---|---|---|
| R-FILL-33, R-FILL-61 | The phone's default timeout for the bank's check | **Answered:** 10 min on iPhone, 5 on Android |
| R-LEAVE-6 | Keeping the fee back as a "surcharge" under §3.4(e) | `[ABSENT]`: for Stripe support and the lawyer |
| R-LEAVE-6 | Does a reversal return the club's fee? | Partly: a *reading* says no; `[ABSENT]` outright |
| R-LEAVE-6, R-LEAVE-39 | IC+ or standalone club: zero fee or none? | **Standalone: zero.** IC+ `[ABSENT]` |
| R-LEAVE-7, -36, -41, -51 | Is an early refund pending or netted, and the expiry window? | **Window: 45 days.** Live netting `[ABSENT]` |
| R-LEAVE-44 | A full-share check let go at once: allowed, and any fees? | **Fees answered.** Network view `[ABSENT]` |
| R-LEAVE-44, R-LEAVE-46 | A live Visa hold on a card copy: 4 d 18 h or 7 d? | `[ABSENT]`: only a live `capture_before` says |
| R-LEAVE-45 | Can a fresh copy confirm the refused payment? | **Answered** (measured): yes, the check opens |
| R-LEAVE-45 | `capture_before` after the bank's check | `[ABSENT]`: no such payment anywhere; nearest case measured |
| R-LEAVE-45 | How many confirmations cancel a payment? | **Measured:** cancelled after ten failed tries |
| R-LEAVE-32, R-LEAVE-52 | A lapsed hold's reason, events and errors | **Errors answered.** Reason and events `[ABSENT]` until 26 Oct |
| R-LEAVE-54 | What tells a Dashboard capture from Rakieta's? | **Answered:** the notice's request and its key |
| R-LEAVE-36, R-LEAVE-41 | Refunds on a stopped or removed club | Partly: removed is answered; charges disabled `[ABSENT]` |
| R-LEAVE-7, R-LEAVE-38 | How issuers rule a kept share | Evidence documented; outcomes `[ABSENT]` |
| R-LEAVE-51 | Is a full-Dashboard club emailed when a refund fails? | **Answered:** not on Stripe's list of emails |
| R-PAY-35 | Fresh copy then bank's check: completes? and its window | Partly: the check opens; completion `[ABSENT]` |

---

### R-FILL-33, R-FILL-61 · The phone gives the bank's check 10 minutes on an iPhone and 5 on Android

**What Stripe requires**

- **[DOCS]** "You can use `timeout` to specify how much time the 3DS authentication process can elapse before timing
  out. This duration includes both network round trips and awaiting customer input, and must be at least 5 minutes."
  On Android, "A value less than 5 minutes results in an error."
  - Source: [3DS authentication flow](https://docs.stripe.com/payments/3d-secure/authentication-flow), carried from
    [`stripe-authentication.md#the-banks-check-may-run-for-at-least-five-minutes`](stripe-authentication.md#the-banks-check-may-run-for-at-least-five-minutes)
    (read 2026-10-19).

**What the app's SDK does when no timeout is passed** (Stripe's own source, as installed, read 2026-10-20)

- **[DOCS]** React Native SDK 0.38.6, the app's version: `threeDSecureParams.timeout` is optional.
  - With none passed, iOS skips the setting (`ios/StripeSdk.swift:95-101`: `if let params3ds = params3ds { configure3dSecure(params3ds) }`).
  - Android sets a timeout only `if (params.hasKey("timeout"))` (`android/…/StripeSdkModule.kt:109-121`).
  - So each native SDK's default applies. Read in `frontend_player/node_modules/@stripe/stripe-react-native`.
- **[DOCS]** iOS uses Stripe's `StripePayments` pod 23.28.3 (the RN SDK asks for `~> 23.28.0`).
  - It says: "`authenticationTimeout` is the total time allowed for a user to complete a 3DS2 authentication
    interaction, in minutes. This value *must* be at least 5 minutes. Defaults to 10 minutes."
  - The code: `@objc public var authenticationTimeout = 10` (`STPThreeDSCustomizationSettings.swift:40-43`).
  - It is passed as the authentication's `maxTimeout` and as the challenge's timeout, in minutes × 60 s
    (`STPPaymentHandler.swift:1150`, `:1184`).
  - Read from the installed pod (`frontend_player/ios/Pods/StripePayments`).
- **[DOCS]** Android uses Stripe's `payments-core` 20.48.6 (the RN SDK pins `StripeSdk_stripeVersion=20.48.+`).
  - `PaymentAuthConfig.Stripe3ds2Config.DEFAULT_TIMEOUT = 5`.
  - The builder starts at 5, and the default `PaymentAuthConfig` is built from that builder.
  - Any value outside 5 to 99 throws "Timeout value must be between 5 and 99, inclusive".
  - Read by disassembling the AAR in the Gradle cache.

**What the code does**

- The app starts Stripe with the publishable key, the URL scheme, the club's account and the Apple Pay merchant only.
  It passes no `threeDSecureParams` (`frontend_player/src/shared/lib/platform/payments.tsx:220-230`).
- `bankAnswerOf` reads any error that is neither `Canceled` nor a decline as `failed` (`payments.tsx:195-206`).
  Which error code a timeout returns is *unverified*.
- Carried: near the cut-off or the book-by, the time to fix the card can be minutes. A confirmation that lands after
  it lets the payment go (FILL breaker row A13, `backend/app/modules/proposals/application/answers.py:333-338`).

**Reading**

- Suppose a player opens the bank's check with less than 10 minutes left (iPhone) or less than 5 (Android). He can
  still be inside the check when his time to fix ends.
- Stripe forbids a timeout below 5 minutes, so the app cannot shrink the check to fit. Near the cut-off, Rakieta's
  deadline decides, not the SDK's.

### R-LEAVE-6 · Keeping Stripe's fee back from a consumer's refund, under the surcharge clause

**What Stripe says**

- Carried **[POLICY]** Stripe Services Agreement §3.4(e): "Except to the extent the Card Network Rules or Law permits,
  User must not charge surcharges, other fees, or Taxes for accepting payment cards".
- Carried **[DOCS]** On PSD2, Stripe says the ban "does not impact the platform or application fee you charge"
  if not differentiated by payment method.
  - Both from [`gaps-S-01A-leave-fee.md#stripes-terms-forbid-card-surcharges-unless-the-law-permits-them`](gaps-S-01A-leave-fee.md#stripes-terms-forbid-card-surcharges-unless-the-law-permits-them),
    read 2026-10-10. That is under three months old, so it was not re-read.
- **[DOCS]** "Stripe's processing fees from the original transaction aren't returned" *(translated)*. The page says
  nothing about passing that fee on to the customer.
  - Source: [Refund and cancel payments](https://docs.stripe.com/refunds), read 2026-10-20.

**Not found**

- **[ABSENT]** No Stripe page says whether keeping the card fee back from a refund is a fee "for accepting payment
  cards".
  - Where we looked: the Services Agreement, the PSD2 surcharge-ban support article, Stripe's surcharging docs (US, CA
    and NZ only; all carried), and the refunds page (2026-10-20).
  - A question for Stripe support, and for the lawyer reviewing the terms.

### R-LEAVE-6 · Whether a reversal gives the club its original fee back

**What Stripe says** (from [Refund and cancel payments](https://docs.stripe.com/refunds), read 2026-10-20, *(translated)*)

- "Some refunds (those issued shortly after the original charge) appear as a reversal instead of a refund."
- Its glossary: "A reversal is the cancellation of a transaction. Stripe doesn't withhold any fees for payment
  reversals."
- "IC+ users may see a difference in cost between reversals and refunds because reversals usually carry lower network
  fees."
- "Stripe's processing fees from the original transaction aren't returned."

**Carried**

- "Shortly" means usually within about 2 hours of the capture:
  [`stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line).
- "For all refunds, payment processing, Connect, and currency conversion fees from the original charge are not
  returned": [`gaps-S-01A-leave-fee.md#the-original-processing-fee-is-never-returned-on-a-refund`](gaps-S-01A-leave-fee.md#the-original-processing-fee-is-never-returned-on-a-refund).
- **[MEASURED]** No sandbox refund was ever a reversal, and no test card makes one (same anchor in
  `stripe-refunds-and-disputes.md`).

**Reading**

- Stripe names a cost difference between a reversal and a refund only for IC+ users.
- On standard pricing, which Rakieta's clubs use, that suggests a reversal costs the club what a refund does. The
  original fee stays with Stripe, and "doesn't withhold any fees" means no extra fee for the reversal itself.
- If so, the fee kept from a leaver is a fee the club really paid.

**Not found**

- **[ABSENT]** No page states this outright. A question for Stripe support. Test mode cannot make a reversal.

### R-LEAVE-6, R-LEAVE-39 · A club on standalone fees reads a fee of zero on its capture; for IC+ Stripe says only that the fee is not there

**What Stripe says** (read 2026-10-20)

- **[DOCS]** Under standalone fees, "We create a single balance transaction for each transaction that only includes
  the total charge amount, with fees set to zero. Within 36 hours of the charge, we create a second fee-specific
  balance transaction with the *aggregate fees* of all transactions processed within that period."
  - Accounts "might transition to standalone fees … for reasons such as custom pricing (for example, tiered pricing)
    or Stripe fee credit awards."
  - Source: [Standalone fees](https://docs.stripe.com/standalone-fees).
- **[DOCS]** A balance transaction's `fee` is an integer, never null: "Fees (in the smallest currency unit) paid for
  this transaction. Represented as a positive integer when assessed."
  - Source: [Balance Transaction object](https://docs.stripe.com/api/balance_transactions/object).
- **[DOCS]** "IC+ users can't retrieve payment fee information from the balance transaction. Use the payment fees
  report instead." *(translated)*
  - Source: [Expand use cases](https://docs.stripe.com/expand/use-cases).
- **[DOCS]** On IC+, per-auth fees apply "including for authorization (successful and declined), void, charge,
  reversal, or to validate a card". Network costs can be billed "up to two months after" the payment.
  - Source: [Understanding IC+ fees](https://support.stripe.com/questions/understanding-ic-fees).

**What the code does**

- `_fee_of` takes the expanded balance transaction's `fee` whenever it is an integer in złoty. It returns `None`,
  meaning the fee is not yet known, only when there is no balance transaction
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:112-126`).

**Reading**

- For a club on standalone fees, the capture's fee reads `0`, not "none". The code treats 0 as a known fee.
- So the sheet quotes the whole 40,00 zł back, and the refund goes at once. The leaver keeps everything, and the club
  pays the card fee itself in that day's aggregate.
- The refund never waits for ever on this path. It waits only while the balance transaction is missing.

**Not found**

- **[ABSENT]** Whether an IC+ club's capture also reads 0 (billed as standalone fees), or carries some partial fee.
  - Where we looked: Standalone fees, Expand use cases, the Fees report, the IC+ support article and the balance
    transaction object (all 2026-10-20).
  - No IC+ or standalone club exists on the sandbox.

### R-LEAVE-7, R-LEAVE-36, R-LEAVE-41, R-LEAVE-51 · A refund pending for want of money fails after 45 days; whether a live refund of a fresh capture waits is still unstated

**The expiry window**

- **[DOCS]** "Stripe automatically fails a pending refund after 45 days."
  - Source: [Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund), read 2026-10-20.
- **[DOCS]** The failure reason `insufficient_funds`: "The refund is pending due to insufficient funds and has passed
  the pending refund expiry window" *(translated)*.
  - Source: [Refund and cancel payments](https://docs.stripe.com/refunds), read 2026-10-20.

**Which balance pays the refund: Stripe's pages differ** (all read 2026-10-20)

- **[DOCS]** The refunds page: "Refunds use your available Stripe balance (not including pending amounts). If your
  available balance doesn't cover the amount of the refund, Stripe holds the refund as pending for card
  transactions" *(translated)*.
- **[DOCS]** Stripe's support article for Express accounts: "In the event you issue a refund to a customer that
  results in a negative account balance, the refund will show as `pending`."
  - Source: [Pending refunds due to insufficient funds or negative balance](https://support.stripe.com/express/questions/pending-refunds-due-to-insufficient-funds-or-negative-balance).
- **[DOCS]** Connect, direct charges: "If the connected account's balance is insufficient, we set the refund status to
  `pending`."
  - Source: [Create a charge (Connect)](https://docs.stripe.com/connect/charges).

**What the sandbox did**

- **[MEASURED]** A refund made before its money was available was netted against the pending balance, and did not
  wait. Carried from
  [`stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once).

**Reading**

- The support article's "negative account balance" fits what the sandbox did: a refund goes through while the whole
  balance stays above zero.
- The refunds page's "available balance" does not fit. On that reading, a club whose only money is this week's
  captures would see a late leaver's refund pending until its first funds become available: 7 days for a new Polish
  account. It would fail after 45 days if they never do.

**Not found**

- **[ABSENT]** Which reading holds live.
  - Where we looked: the refunds page, Connect charges, Connect SaaS refunds and disputes, and three Stripe support
    articles on pending refunds (2026-10-20).
  - A question for Stripe support.

### R-LEAVE-44 · A full-share hold let go at once to check the money

**What it costs the club** (read 2026-10-20)

- **[DOCS]** "You can cancel a payment before it's completed at no cost" *(translated)*. This is on standard
  pricing, which Rakieta's clubs use.
  - Source: [Refund and cancel payments](https://docs.stripe.com/refunds).
- **[DOCS]** On IC+, per-auth fees apply "for each instance you direct Stripe to submit a request to a payment
  method", "including for authorization (successful and declined), void, charge, reversal, or to validate a card".
  - Source: [Understanding IC+ fees](https://support.stripe.com/questions/understanding-ic-fees).
  - So a club on IC+ would pay two per-auth fees for each check: one for the hold and one for letting it go.

**What the networks say** (carried)

- **[DOCS]** "Card networks may also restrict 1 USD authorizations you don't intend to capture."
  - From [`stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card`](stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card),
    read 2026-10-19.
- Visa asks acquirers to use account verification "instead of authorizations for erroneous amounts", from the same
  anchor (2026-10-11).

**Not found**

- **[ABSENT]** Three things nobody states:
  - whether a full-amount authorisation released at once is acceptable to the networks;
  - whether Visa counts it as an erroneous-amount authorisation on the club's account;
  - whether any network fee for it reaches a Polish club on standard pricing.
- Where we looked: the hold page, the refunds page, the IC+ support article, and a web search for Stripe's word on
  verification authorisations, which found only third-party pages.
- A question for Stripe support.

### R-LEAVE-44, R-LEAVE-46 · Which window a live off-session Visa hold on a card copy gets

**What Stripe says**

- Carried **[DOCS]** Visa gives "5 days\*" when the merchant starts the payment (exactly 4 days 18 hours) and 7 days
  when the customer does. Stripe decides which from signals: "a payment with `off_session: true` might still be
  classified as a CIT if a CVC is present".
  - From [`stripe-holds-and-capture.md#online-card-holds-visa-4-days-18-hours-without-the-payer-7-days-with-mastercard-amex-discover-7`](stripe-holds-and-capture.md#online-card-holds-visa-4-days-18-hours-without-the-payer-7-days-with-mastercard-amex-discover-7)
    and [`#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session`](stripe-holds-and-capture.md#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session),
    read 2026-10-19.
- **[DOCS]** Re-read 2026-10-20, the CIT and MIT page still says nothing about how a cloned card's off-session hold is
  classed. It points only to the charge: "the `payment_method_details.card.capture_before` attribute on the charge
  is the most reliable and accurate way to determine your charge's authorization window."
  - Source: [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits).

**What the sandbox holds**

- **[MEASURED]** Every off-session Visa hold on the sandbox lasted exactly 168 hours. Carried from
  [`stripe-holds-and-capture.md#on-the-sandbox-an-off-session-visa-hold-lasts-exactly-7-days-and-offers-nothing-beyond-a-plain-hold`](stripe-holds-and-capture.md#on-the-sandbox-an-off-session-visa-hold-lasts-exactly-7-days-and-offers-nothing-beyond-a-plain-hold).
- **[MEASURED]** The copy's own CVC check reads `pass` on `ch_3USPIk5y1DMwE3zY0iAFXnJM`. This was read via the SDK in
  the copy, 2026-10-20.

**Not found**

- **[ABSENT]** The live window. Only a live hold's own `capture_before` can say, and the product already reads it on
  every payment.
- A question for Stripe support, if an answer is wanted before going live.

### R-LEAVE-45 · A fresh copy of the saved card is accepted on the original refused payment

**What Stripe says**

- Carried **[DOCS]** "You can't reuse the consumed clone, but you can clone the platform PaymentMethod again and use
  the new clone for another charge."
  - From [`stripe-authentication.md#each-clone-is-used-up-by-the-payment-it-makes`](stripe-authentication.md#each-clone-is-used-up-by-the-payment-it-makes).

**What the sandbox holds**

- **[MEASURED]** `pi_3USPGP5y1DMwE3zY0vlzqtWy`: a 40,00 zł share on the test club, made by the PAY breaker with card
  3184. Its events were read via the SDK in the copy, 2026-10-20:

  | Time (UTC, 2026-10-19) | Event | What it shows |
  |---|---|---|
  | 22:42:41 | `payment_intent.created`, `payment_intent.payment_failed` | The off-session hold, refused with `authentication_required` |
  | 22:42:44 | `payment_intent.requires_action` | The confirmation with a **fresh** copy, under `req_lqtcr6tCX8Zq8A`: the bank's check opened |
  | 22:42:45 | `payment_intent.canceled` | The breaker's tidy-up |

- The payment's `payment_method` is the fresh copy, `pm_1USPGR5y1DMwE3zYlWShf5Oq`. The refused copy was
  `pm_1USPGP5y1DMwE3zYZyowkUH3`.
- No charge exists on the payment: a charge is made only once the bank's check ends.
- The used copy had been refused before:
  - PAY breaker S7, `req_q2AGEZy3aexIb2`;
  - FILL breaker S2, `req_8rsitla8xVevKv`: "The provided PaymentMethod was previously used with a PaymentIntent
    without Customer attachment…".

**Answer**

- Yes: a fresh copy of the platform card confirms the original refused payment, at least as far as opening the bank's
  check.
- Whether it then completes is unmeasured: see
  [R-PAY-35](#r-pay-35--a-refused-payment-confirmed-with-a-fresh-card-copy-the-check-opens-whether-it-completes-and-its-window-are-unmeasured).

### R-LEAVE-45 · The window stamped on a payment confirmed after the bank's check

**What Stripe says**

- Carried **[DOCS]** "The validity window won't change after the PaymentIntent is confirmed." The field sits on the
  charge, so it exists only after a successful confirmation.
  - From [`stripe-holds-and-capture.md#capture_before-on-the-charge-is-the-window-to-trust-and-it-does-not-move-once-confirmed`](stripe-holds-and-capture.md#capture_before-on-the-charge-is-the-window-to-trust-and-it-does-not-move-once-confirmed).

**What the sandbox holds** (read via the SDK in the copy, 2026-10-20)

- **[MEASURED]** No charge with `three_d_secure` set exists on any of the eight accounts the platform reaches.
  - The test club holds 123 charges.
  - The other seven accounts hold 0, 0, 0, 0, 0, 1 and 1.
  - So no payment completed through the bank's check exists to read.
- **[MEASURED]** The nearest case is `pi_3USPIk5y1DMwE3zY03JvGogQ` (FILL breaker S1).
  - It was refused off-session with `generic_decline` (charge `ch_3USPIk5y1DMwE3zY0OwGGxFN`).
  - Two seconds later it was confirmed with a typed card: charge `ch_3USPIk5y1DMwE3zY0iAFXnJM`, created 2026-10-19
    22:45:08 UTC.
  - Its `capture_before` is 2026-10-26 22:45:08 UTC: exactly 168.0 hours from the charge that succeeded, not from
    when the payment was made. `three_d_secure` is null.

**Reading**

- The window runs from the authorisation that succeeds.
- A payment the player authenticates on the phone is customer-initiated, and the hold table gives that 7 days on
  every network.

**Not found**

- **[ABSENT]** The stamp itself. It needs a payment completed through Stripe's test bank page on a phone or in a
  browser. PAY breaker S7 stopped at `requires_action`.

### R-LEAVE-45 · Stripe cancelled a payment after ten failed tries

**What Stripe says**

- Carried **[DOCS]** "PaymentIntents could also transition automatically to `canceled` if they're confirmed too many
  times." Stripe gives no number.
  - From [`stripe-authentication.md#a-payment-confirmed-too-many-times-is-cancelled-by-stripe`](stripe-authentication.md#a-payment-confirmed-too-many-times-is-cancelled-by-stripe).

**What the sandbox holds**

- **[MEASURED]** `pi_3USPKC5y1DMwE3zY00HIKsMU`: a 40,00 zł share on the test club (FILL breaker S5). Read via the SDK
  in the copy, 2026-10-20.
  - It made ten failed charges: the off-session one at 22:46:37 UTC, then nine typed cards. All were
    `generic_decline`. Each had its own `payment_intent.payment_failed` event, and each left the payment in
    `requires_payment_method`.
  - Then came `payment_intent.canceled` at 22:46:49 UTC. Its request, `req_ZW2hNCf2S7SLgf`, is none of the ten
    failed attempts.
  - The payment reads `cancellation_reason: null` and `canceled_at` 2026-10-19 22:46:49 UTC.
  - The breaker's tenth typed card, the eleventh confirmation in all, was answered `payment_intent_unexpected_state`
    (FILL breaker S5).

**Reading**

- On the sandbox, Stripe allowed ten failed tries on one payment. The next confirmation found it cancelled.
- The cancellation carries no reason, so it cannot be told apart from Rakieta's own let-go by its reason. Only the
  request tells them apart.
- The spec's "at most 8 retries" stays within this limit.

**Not found**

- **[ABSENT]** Whether the live limit is the same, and whether bank's-check attempts count like declines. Stripe does
  not say.

### R-LEAVE-32, R-LEAVE-52 · A lapsed hold: its reason and events wait for 26 October; a cancelled payment refuses with `payment_intent_unexpected_state`

**What Stripe says** (read 2026-10-20)

- **[DOCS]** `cancellation_reason` is "either user-provided (`duplicate`, `fraudulent`, `requested_by_customer`, or
  `abandoned`) or generated by Stripe internally (`failed_invoice`, `void_invoice`, `automatic`, or `expired`)". No
  value is tied to a lapsed card hold.
  - Source: [PaymentIntent object](https://docs.stripe.com/api/payment_intents/object).
- **[DOCS]** "When a PaymentIntent is cancelled, you can no longer use it to make other charges. Any operation your
  application attempts on a cancelled PaymentIntent will error." *(translated)*
  - Source: [Refund and cancel payments](https://docs.stripe.com/refunds).

**What the sandbox holds**

- **[MEASURED]** Letting go a payment the club had already let go was refused `payment_intent_unexpected_state`,
  twice: `pi_3USPJy5y1DMwE3zY0hKDfKvT`, `req_FfuA48l6n23CgI` and `req_M3Nad90y6XTBV7` (FILL breaker S4).
- A capture of a cancelled payment has not been tried.
- A capture of an already-captured payment answers `payment_intent_unexpected_state`, "This PaymentIntent could not
  be captured because it has already been captured." (LEAVE breaker L6, `req_OTMlSE6L5UC9UB`).
- **[MEASURED]** Stripe's own cancellation after too many tries carried `cancellation_reason: null` (previous
  section). So a cancellation Stripe makes need not carry `automatic` or `expired`.

**Not found yet**

- **[ABSENT]** The reason and events a lapsed hold carries, until the lapse.
  - `pi_3USA7i5y1DMwE3zY0Nemxwtn` lapses 2026-10-26 06:32:43 UTC.
  - `pi_3USELx5y1DMwE3zY14aUf4wv` lapses at 11:03:41 UTC the same day.
- Then read:
  - each payment's `status`, `cancellation_reason` and `canceled_at`;
  - the club's `charge.expired` and `payment_intent.canceled` events for it, with their `request.id` (null means
    Stripe did it on its own).

### R-LEAVE-54 · Only a notice's request says who took a held share

**What Stripe says** (from the [Event object](https://docs.stripe.com/api/events/object?query=request), read 2026-10-20)

- **[DOCS]** `request`: "Information on the API request that triggers the event."
- `request.id`: "ID of the API request that caused the event. If null, the event was automatic (e.g., Stripe's
  automatic subscription handling). Request logs are available in the dashboard, but currently not in the API."
- `request.idempotency_key`: "The idempotency key transmitted during the request, if any."
- Nothing on the event or the PaymentIntent names a user or says "Dashboard".
- A PaymentIntent's `application` is the "ID of the Connect application that created the PaymentIntent": who made
  the payment, not who took it ([PaymentIntent object](https://docs.stripe.com/api/payment_intents/object)).

**What the sandbox holds** (read via the SDK in the copy, 2026-10-20)

- **[MEASURED]** All 56 `payment_intent.succeeded` events on the test club, from 2026-10-19 06:32 to 22:49 UTC, carry
  a request id and an idempotency key.
- The product's own captures carry `rakieta-capture-<charge id>`. Example: `evt_3USPCF5y1DMwE3zY1K4GZYiy` on
  `pi_3USPCF5y1DMwE3zY1ZZ8B4cn`, `req_vmmdVcCqRts36M`. That is the key `capture_key` builds
  (`backend/app/modules/payments/application/handlers/settle_seat_charges.py:53-54`).
- The L6 shares were taken by a stand-in for the desk, and their captures carry the stand-in's own key:

  | Share | `payment_intent.succeeded` event | Request | Key |
  |---|---|---|---|
  | `pi_3USPCt5y1DMwE3zY1F38KqZ9` | `evt_3USPCt5y1DMwE3zY1tzo1lVD` | `req_F48OWqxUZZ8n2N` | `rakieta-breaker-leave-dashboard-capture-…` |
  | `pi_3USPCw5y1DMwE3zY1cQfpDvj` | `evt_3USPCw5y1DMwE3zY1TpsYA9J` | `req_mTE1dvZrG7Nfvw` | the same stand-in key |

- Both payments read `captured: true` and `application: ca_VT4JuiojqLY0o3NiUC7dcMvrueSONfGf` (Rakieta's), exactly as
  a product capture does.
- No event on the club comes from a real press in the Dashboard.

**What the code does**

- The notice reader never reads an event's `request`: the word does not appear in
  `backend/app/modules/payments/infrastructure/stripe_notices.py`.

**Reading**

- The one field that tells the two apart is the event's `request.idempotency_key`. Rakieta's capture always sends
  `rakieta-capture-<its charge id>`.
- Anything else is not Rakieta's: another key, no key, or `request.id: null` from Stripe's own automatic capture.
- Put another way: a `payment_intent.succeeded` for a share Rakieta still holds as held is someone else's take.

**Not found**

- **[ABSENT]** What a real Dashboard capture's `request` carries, such as whether the Dashboard sends its own
  idempotency key.
  - Stripe does not document it, and the sandbox holds none.
  - A press in the club's Dashboard is a write, so it was not made here.

### R-LEAVE-36, R-LEAVE-41 · Refunds on a club Stripe stopped or Rakieta removed

**What Stripe says**

- Carried **[DOCS]** A removed account: "you can't process payments or make API calls for it".
  - From [`stripe-connect.md#removing-a-club-ends-every-api-call-rakieta-can-make-for-it`](stripe-connect.md#removing-a-club-ends-every-api-call-rakieta-can-make-for-it).
- Carried **[DOCS]** A full-Dashboard club handles its own refunds.
  - From [`stripe-connect.md#the-club-handles-its-own-payments-refunds-and-disputes`](stripe-connect.md#the-club-handles-its-own-payments-refunds-and-disputes).
- **[DOCS]** Closing an Accounts v2 account: "Closed Accounts can no longer be operated on, but limited information can
  still be retrieved through the API".
  - It refuses with `stripe_loss_liable_cannot_be_deleted` ("Account with Stripe-owned loss liability and dashboard
    cannot be deleted"), `cannot_delete_account_with_balance` and `pending_transactions_cannot_be_deleted`.
  - Source: [Close an account (v2)](https://docs.stripe.com/api/v2/core/accounts/close), read 2026-10-20.
  - So Rakieta cannot close one of its clubs, which are Stripe-liable with a full Dashboard. "Removed" can only mean
    disconnected.
- **[DOCS]** "Your connected accounts must have the card_payments capability active in order to use direct charges."
  This is about making charges, not refunding them.
  - Source: [Create a charge (Connect)](https://docs.stripe.com/connect/charges), read 2026-10-20.

**Reading**

- Once a club is removed, a late leaver's refund can be made only by the club, in its own Dashboard.
- Rakieta's refund call fails with `platform_api_key_expired` (carried, same file, §7).

**Not found**

- **[ABSENT]** Whether a refund, or a capture, is accepted on an account whose charges Stripe has disabled.
  - Looked again 2026-10-20: the refunds page, Connect charges, Connect SaaS refunds and disputes, the v2 close
    reference, and Stripe support.
  - Carried searches: [`stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled)
    and [`gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried`](gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried).
  - It cannot be tested read-only.

### R-LEAVE-7, R-LEAVE-38 · How an issuer rules a kept share: Stripe documents the evidence, not the outcome

**What Stripe says** (from [Dispute categories](https://docs.stripe.com/disputes/categories), read 2026-10-20)

- **[DOCS]** *Credit not processed*: "The customer claims they're entitled to a full or partial refund because they
  returned the purchased product or didn't fully use it, or the transaction was otherwise canceled or not fully
  fulfilled, but you haven't yet provided a refund or credit."
  - To overturn it, show that "The customer isn't entitled to a refund".
  - For "**Offline services** … such as event tickets and reservations, … evidence of a cancellation policy can be
    material."
  - The evidence it asks for:
    - "The language of the applicable cancellation or refund policy, as provided to the customer"
      (`cancellation_policy`, `refund_policy`);
    - "An explanation of how and where you provided the applicable policy to your customer prior to purchase"
      (`cancellation_policy_disclosure`, `refund_policy_disclosure`);
    - "Your explanation for why the customer isn't entitled to a cancellation or refund" (`cancellation_rebuttal`,
      `refund_refusal_explanation`).
- **[DOCS]** *Product not received*: "The customer claims they did not receive the products or services purchased."
  For offline services the evidence it asks for:
  - "Documentation showing that the service was provided to the cardholder, including the date that the cardholder
    received or began receiving the purchased service" (`service_date`, `service_documentation`);
  - "Evidence that the agreed-upon service date hasn't arrived yet";
  - "Whether you have already issued the refund the cardholder is entitled to".
- **[DOCS]** On a refund policy offered in other categories: "Depending on network and context, the issuer might or
  might not take this into consideration".
- Carried: [`stripe-refunds-and-disputes.md#the-evidence-a-booked-game-would-need-the-cancellation-policy-as-shown-and-that-it-was-played`](stripe-refunds-and-disputes.md#the-evidence-a-booked-game-would-need-the-cancellation-policy-as-shown-and-that-it-was-played).

**Not found**

- **[ABSENT]** How issuers rule these two kinds of dispute when a share was kept under a stated policy, for a game
  played short or not played by the payer.
- Stripe publishes no win rates for it. A question for Stripe support.

### R-LEAVE-51 · Stripe's account emails do not include a failed refund

**What Stripe says** (read 2026-10-20)

- **[DOCS]** "In the rare case a refund fails, Stripe notifies you using the `refund.failed` event … you'll need to
  arrange an alternative way of providing your customer with a refund." *(translated)*
  - Source: [Refund and cancel payments](https://docs.stripe.com/refunds).
- **[DOCS]** Stripe "can notify you of account activity via email, including when":
  - a payment is made;
  - a payment is disputed;
  - a payment is marked elevated risk;
  - an application fee is collected;
  - a connected account has a risk requirement;
  - a teammate mentions you in a note.
  - Source: [Set up account email notifications](https://support.stripe.com/questions/set-up-account-email-notifications).
- **[DOCS]** The team page adds two more: an incorrect invoice amount, and a failed webhook delivery. It says "For a
  complete list of notification events, go to your **Communication preferences** in **Profile**" *(translated)*.
  - Source: [Create a team](https://docs.stripe.com/get-started/account/teams).
- Neither list includes refunds or failed refunds. The pending-refund support article mentions no email either.

**Reading**

- A full-Dashboard club is not emailed when a share's refund fails. It sees the failure only if it opens the payment
  in its Dashboard.
- Rakieta hears `refund.failed` on its Connect endpoint.

**Not found**

- **[ABSENT]** The full list under Communication preferences. It is shown only in a signed-in Dashboard and was not
  read.

### R-PAY-35 · A refused payment confirmed with a fresh card copy: the check opens; whether it completes, and its window, are unmeasured

**What the sandbox holds**

- **[MEASURED]** With a fresh copy, the refused payment moved to `requires_action`, so the bank's check opened:
  `pi_3USPGP5y1DMwE3zY0vlzqtWy`, `req_lqtcr6tCX8Zq8A`. See
  [the fresh-copy section above](#r-leave-45--a-fresh-copy-of-the-saved-card-is-accepted-on-the-original-refused-payment).
- **[MEASURED]** `pi_3USPdt5y1DMwE3zY0ckeA2tw` (PAY breaker S7b), read via the SDK in the copy, 2026-10-20.
  - Events: created and `payment_failed` at 23:06:57–58 UTC, then `canceled` at 23:06:59 UTC.
  - There is no `requires_action` event: the phone's call with the publishable key, on the used copy, was refused
    (`req_TjhZFnZkNJuFTF`).

**What Stripe says happens next**

- Carried **[DOCS]** After the player authenticates, "Stripe attempts the charge and the PaymentIntent transitions to
  a status of `processing`", then to `succeeded`, `requires_capture` or `requires_payment_method`.
  - From [`stripe-authentication.md#what-a-confirmation-does-to-the-payment-step-by-step`](stripe-authentication.md#what-a-confirmation-does-to-the-payment-step-by-step).

**Not found**

- **[ABSENT]** Whether the payment then completes after the bank's check, and the `capture_before` Stripe stamps on
  it. See
  [the window section above](#r-leave-45--the-window-stamped-on-a-payment-confirmed-after-the-banks-check).
- Answering it needs someone to pass Stripe's test bank page on a phone or in a browser. A read-only researcher
  cannot.
