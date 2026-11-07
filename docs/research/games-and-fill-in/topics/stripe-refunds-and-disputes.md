# Stripe — refunds and disputes

What Stripe says about refunds and disputes for the way Raketa uses it: every share is a **direct charge**
on the club's **Accounts v2** connected account (full Dashboard, `fees_collector` and `losses_collector`
both `stripe`), a single-use clone of the player's platform card, held with manual capture and taken at the
club's cut-off; złoty; Poland. Read 2026-10-19 from docs.stripe.com (fetched as Markdown,
`?locale=en-US`) and Stripe's documentation search; sandbox objects read through `stripe-club` (test club
`acct_1US95f5y1DMwE3zY`) the same day. No write tool was used.

*Code:* readings of the code at `9ab0ea5b`, with `path:line`; they are not facts about Stripe. Today a
**taken** share is refunded for four reasons (`backend/app/modules/payments/domain/seat_charge.py:152-173`):
a leaver after the cut-off whose seat is taken gets the share less exactly the fee kept on that payment
(`SEAT_TAKEN`); a game called off at the cut-off, a club's cancel, and a club's cancel after the player left
give the whole share. A **held** share is let go, never refunded. The refund is one call,
`refunds.create(payment_intent, amount)` on the club's account with no `reason` and no `metadata`, under
the key `raketa-refund-{charge}` — "One refund per charge, ever"
(`backend/app/modules/payments/infrastructure/stripe_payments.py:583-609`;
`backend/app/modules/payments/application/handlers/settle_seat_charges.py:67-70`, `:142-161`), sent from
the outbox after the commit. Nothing under `backend/app` reads a dispute.

**Not redone here, cited at the facts that lean on them:** the fee kept on a refund
(`gaps-S-01A-leave-fee.md`, 2026-10-10); reversals (`gaps-CLUBMONEY.md`, 2026-10-08); a refund short of the
club's balance (`stripe-connect.md` §3); the refund and dispute events and their scope (`stripe-webhooks.md`
§4, §6); the sandbox's refunds, the 2,30 zł fee on 4242 and the dropped refund notices (`stripe-sandbox.md`
§3, D5, D6); refunding a hold (`stripe-holds-and-capture.md` pitfall 9); fraud disputes without 3-D Secure
(`gaps-SWIPE.md`); Visa CE 3.0 (`gaps-PAY.md`); the 120-day window (`gaps-EMAIL.md`); a closed account can't
refund ([`gaps-S-01.md#stripe-keeps-a-stopped-accounts-money-to-cover-refunds-a-closed-account-cannot-refund`](gaps-S-01.md#stripe-keeps-a-stopped-accounts-money-to-cover-refunds-a-closed-account-cannot-refund)).

---

## 1. A refund's life

### A refund is made from the PaymentIntent, in parts if wanted, never beyond what is left

- **[DOCS]** "You can optionally refund only part of a charge. You can do so multiple times, until the entire
  charge has been refunded. Once entirely refunded, a charge can't be refunded again. This method **will
  raise an error** when called on an already-refunded charge, or when trying to refund more money than is
  left on a charge." `amount`: "Can refund only up to the remaining, unrefunded amount of the charge."
  [Create a refund](https://docs.stripe.com/api/refunds/create) — 2026-10-19
- **[DOCS]** "To refund a payment after the PaymentIntent succeeds, create a refund using the PaymentIntent,
  which is the same as refunding the underlying charge." A `requires_capture` PaymentIntent "can't be
  refunded directly. **You must** cancel the PaymentIntent." "Refunds can only be sent back to the original
  payment method used in a charge." [Refund and cancel payments](https://docs.stripe.com/refunds) — 2026-10-19
- **[DOCS]** Error codes: `charge_already_refunded` — "has already been refunded. Inspect its existing refunds
  to confirm whether the intended refund is complete"; `charge_disputed` — "has been charged back";
  `refund_disputed_payment` — "You can't refund a disputed payment." [Error codes](https://docs.stripe.com/error-codes) — 2026-10-19
- **[MEASURED]** `ch_3USEMX5y1DMwE3zY1lrc899G` (40,00 zł), after a 38,24 zł refund: `amount_refunded: 3824`,
  `refunded: false` (true only once refunded in full) · `stripe-club` · 2026-10-19.
- *Code:* a refusal of this kind is an `InvalidRequestError`, raised as it came
  ([`stripe-reliability.md#some-refusals-never-clear-on-a-retry`](stripe-reliability.md#some-refusals-never-clear-on-a-retry)),
  inside an outbox delivery that is asked again every second with no last attempt
  ([`stripe-reliability.md#this-products-outbox-asks-again-every-second-with-no-end`](stripe-reliability.md#this-products-outbox-asks-again-every-second-with-no-end)).
  The fake refuses an over-refund the same way (`backend/app/modules/payments/infrastructure/fake_payments.py:737-744`).

### Five statuses, and why a refund is pending

- **[DOCS]** Refund `status`: "`pending`, `requires_action`, `succeeded`, `failed`, or `canceled`".
  `pending_reason`: "`processing`, `insufficient_funds`, or `charge_pending`". `requires_action` is only
  for "payment methods that require customer action" (Konbini, PromptPay, bank transfers) — never a card.
  [Refund object](https://docs.stripe.com/api/refunds/object), [Cancel a refund](https://docs.stripe.com/api/refunds/cancel) — 2026-10-19
- **[DOCS]** `pending_reason` was added in `2025-04-30.basil`; `charge_pending`: "The payment being refunded
  hasn't settled yet." [Changelog](https://docs.stripe.com/changelog/basil/2025-04-30/refund-pending-reason) —
  2026-10-19. The SDK sends `2026-08-26.dahlia`, so the field is present
  ([`stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive`](stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive)).
- **[DOCS]** "In live mode, refunds are asynchronous: a refund can appear to succeed and later fail, or can
  appear as `pending` at first and later succeed." [Testing](https://docs.stripe.com/testing#refunds) — 2026-10-19
- *Code:* `pending` and `requires_action` map to `PENDING`, `failed` and `canceled` to `FAILED`
  (`stripe_payments.py:93-99`), but **nothing reads the mapped status**: the charge records the amount as
  given whatever it says (`seat_charge.py:733-754`, `settle_seat_charges.py:154-160`; grep `RefundStatus.`
  finds only the map and the fake's `SUCCEEDED`, `fake_payments.py:749`).

### A refund can fail up to 30 days later, for seven reasons, and the seller must pay another way

- **[DOCS]** "A refund can fail if the customer's bank or card issuer can't process it … the bank returns the
  refunded amount to Stripe, and Stripe adds it back to your Stripe account balance. This process can take
  up to 30 days from the post date." The refund turns `failed` with `failure_balance_transaction` and
  `failure_reason`: `charge_for_pending_refund_disputed`, `declined`, `expired_or_canceled_card`,
  `insufficient_funds` ("pending due to insufficient funds and has crossed the pending refund expiration
  window"), `lost_or_stolen_card`, `merchant_request`, `unknown`. "In the rare instance that a refund fails,
  Stripe notifies you using the `refund.failed` event … **you need to arrange an alternative way** to provide
  your customer with a refund." [Refunds — failed refunds](https://docs.stripe.com/refunds#failed-refunds) — 2026-10-19
- **[DOCS]** "Refunds to expired or canceled cards are handled by the customer's card issuer and, in most
  cases, credited to the customer's replacement card … In rare cases, a refund back to a card might fail."
  [Refunds — destinations](https://docs.stripe.com/refunds#refund-destinations) — 2026-10-19
- *Reading:* on a direct charge the failed amount returns to the **club's** balance (the refund was debited
  there); only destination charges send it to the platform ("If your platform uses Connect with
  destination charges, funds from a failed refund deposit to your platform account's Stripe balance").

### Stripe recommends hearing `refund.created` at least, and telling the people concerned

- **[DOCS]** "Stripe triggers events every time a refund is created or changed … **You must also build
  internal logic for notifying customers or your team** about the state of the refund process. At a
  minimum, **Stripe recommends** that you listen for the `refund.created` event." Events: `refund.created`,
  `refund.updated` (ARN and metadata), `refund.failed`, `charge.refunded` ("including partial refunds.
  Listen to `refund.created` for information about the refund"), `charge.dispute.funds_reinstated`
  ("including partially refunded payments"), `review.closed` (reason `refunded` or `refunded_as_fraud`);
  `charge.refund.updated` is **Deprecated**. [Refunds — events](https://docs.stripe.com/refunds#refund-events);
  [Event types](https://docs.stripe.com/api/events/types) — 2026-10-19
- **[DOCS]** For direct charges: "Listen to events on connected accounts to receive notifications about
  refunds and disputes." [Handle refunds and disputes (SaaS)](https://docs.stripe.com/connect/saas/tasks/refunds-disputes) — 2026-10-19
- *Code:* every refund kind is dropped (D6, [`stripe-sandbox.md#differences`](stripe-sandbox.md#differences)).

### A card refund can be cancelled only in the Dashboard, for a short while — and the club has one

- **[DOCS]** "Some card refunds support cancellation for a short period of time. The refund must not have
  been processed as a charge reversal. **Only Dashboard cancellations are currently supported for card
  refunds.**" "Canceled refunds transition to a `canceled` status. As cancellations are a type of refund
  failure, the attributes `failure_reason` and `failure_balance_transaction` are included." The API cancels
  only a `requires_action` refund. [Refunds — cancel a refund](https://docs.stripe.com/refunds#cancel-refund) — 2026-10-19
- **[DOCS]** "In live mode, you can cancel a card refund within a short but nonspecific period of time.
  Testing environments simulate that period by allowing you to cancel a card refund within 30 minutes."
  [Testing](https://docs.stripe.com/testing#refunds) — 2026-10-19
- **[DOCS]** The club's full Dashboard handles "disputes, refunds, and chargebacks"
  ([`stripe-security.md#a-full-dashboard-club-can-see-refund-and-dispute-its-payments-itself`](stripe-security.md#a-full-dashboard-club-can-see-refund-and-dispute-its-payments-itself));
  a Dashboard refund asks for a reason ("If you select **Other**, you must add a note").
  [Refunds — issue refunds](https://docs.stripe.com/refunds#issue-refunds) — 2026-10-19
- *Reading:* a club can cancel the refund Raketa made, or refund a share itself; Raketa hears neither.

### A refund within about two hours of the capture is usually a reversal, with no credit line

- **[DOCS]** "The only time a refund can prevent a fraud report is when it's processed as a reversal, which
  **usually happens within 2 hours of the payment capture**." [How disputes work — early fraud warnings](https://docs.stripe.com/disputes/how-disputes-work#early-fraud-warnings) — 2026-10-19.
  This is the first hour figure found for "shortly after"; the earlier search found none
  ([`gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a-partial-reversal`](gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a-partial-reversal)).
- **[DOCS]** "In the case of a reversal, the original charge drops off the customer's statement, and a
  separate credit isn't issued." "An ARN isn't available in the case of a reversal." A reversal reads
  `destination_details[card][type] = 'reversal'`. [Refunds — refund and reversal](https://docs.stripe.com/refunds#refund-and-reversal) — 2026-10-19
- **[MEASURED]** Refunds made two seconds after the hold and its capture (`re_3USEMX5y1DMwE3zY1Boz4mHQ`
  created 1792407859, charge created 1792407857; likewise `re_3USEMc…`, `re_3USEMi…`) all read
  `destination_details.card.type: refund`, with an ARN · `stripe-club` · 2026-10-19.
- **[ABSENT]** A test card or setting that produces a reversal in test mode: not on the testing page
  ("With all other test cards, refunds succeed immediately") — 2026-10-19.
- *Reading:* in Raketa a share is taken at the club's cut-off (24 h before at Bonarka Arena); a late
  leaver's seat taken within about two hours of that is the only refund likely to be a reversal.

### The player sees a card refund in about 5–10 business days; the reference comes within 7

- **[DOCS]** "Your customer sees the refund as a credit approximately 5-10 business days later, depending
  upon the bank." "It takes up to 7 business days after initiating the refund to receive the ARN"; it is
  read from `destination_details.card.reference` on `refund.updated` or a retrieve. [Refunds — trace a refund](https://docs.stripe.com/refunds#tracing-refunds) — 2026-10-19
- **[MEASURED]** Every sandbox refund carries `reference_status: available`,
  `reference_type: acquirer_reference_number` at once (e.g. `re_3USEMi5y1DMwE3zY11GGOqFA`) · `stripe-club` · 2026-10-19.
- *Code:* the PRD promises Receipts with "the refund timing (BLIK within hours, cards up to two weeks)"
  (`prd-530.md:179`); no ARN is read.

### Stripe emails the player about a refund only when the charge is on a Customer — a share's is not

- **[DOCS]** Stripe emails the customer about a refund only if "The original charge was created on a
  customer in your Stripe account", "The customer has a stored email address" and "Email customers for
  refunds" is on. [Refunds — refund requests](https://docs.stripe.com/refunds#refund-requests) — 2026-10-19
- **[MEASURED]** `ch_3USEMX5y1DMwE3zY1lrc899G` and all six refunds on the test club: `customer: null` ·
  `stripe-club` · 2026-10-19. *Code:* "The clone, which belongs to no customer on the club's account"
  (`stripe_payments.py:500-502`).

### The money comes off the club's balance; on the sandbox, off its pending balance, at once

- Carried: on a direct charge the refund is debited from the club; short of funds a card refund is
  `pending` and is processed when funds arrive
  ([`stripe-connect.md#refunds-and-disputed-money-come-out-of-the-clubs-balance-a-short-refund-waits`](stripe-connect.md#refunds-and-disputed-money-come-out-of-the-clubs-balance-a-short-refund-waits)).
- **[DOCS]** "Refunds use your available Stripe balance (not including pending amounts)."
  [Refunds](https://docs.stripe.com/refunds) — 2026-10-19
- **[MEASURED]** The 38,24 zł refund's balance transaction `txn_3USEMX5y1DMwE3zY1VA3EatO`: `amount −3824`,
  `fee 0`, `type refund`, `status pending`, `available_on` 1792972800 (2026-10-26 00:00 UTC, the same day as
  its charge); the refund itself `succeeded`. The club's balance: available 0,00 zł, pending 266,16 zł,
  `refund_and_dispute_prefunding` 0,00 zł · `stripe-club` · 2026-10-19. So on the sandbox a share refunded
  before its money is available is netted against the pending balance and does not wait.
- **[ABSENT]** Whether a live card refund made before its charge is available goes through the same way or
  waits as `pending` (`charge_pending` or `insufficient_funds`): the refunds, Connect charges and balance
  pages say only "available balance" — 2026-10-19.
- **[DOCS]** `refund_and_dispute_prefunding`: "Funds to cover future refunds, disputes, or a negative
  balance." [Balance object](https://docs.stripe.com/api/balance/balance_object) — 2026-10-19

### Card refunds have no time limit; the reason and the metadata are the caller's

- **[DOCS]** Stripe's documentation search, as a short answer with no page: "Card payments through Stripe do
  not have a time restriction for refunds." (SEPA Direct Debit, unused here, has 180 days.)
  [SEPA Direct Debit](https://docs.stripe.com/payments/sepa-debit) — 2026-10-19
- **[DOCS]** `reason`: `duplicate`, `fraudulent`, `requested_by_customer`; "specifying `fraudulent` … will
  add the associated card and email to your block lists" (on a direct charge, the club's).
  `refund_application_fee` and `reverse_transfer` apply only to application fees and destination charges,
  which Raketa does not use. [Create a refund](https://docs.stripe.com/api/refunds/create) — 2026-10-19
- *Code:* no reason ("a game called off is none of them", `stripe_payments.py:596-598`) and no metadata;
  the club's Dashboard ties the refund to the game only through the payment's description, such as
  "Padel · Bonarka Arena", and its `game_id`/`player_id` metadata
  (`backend/app/modules/payments/application/seat_charges.py:439-445`).

---

## 2. Disputes on a share

### On a direct charge the dispute is the club's: its balance, its fee, its answer

- **[DOCS]** For direct charges: respond through the API as "Connected account. Use its ID in the
  `Stripe-Account` header"; "Balance debited for the disputed amount: Connected account's balance";
  dispute-fee payer for a v2 account with `fees_collector` = `stripe`: "Connected account". "Stripe always
  attempts to debit disputed amounts from the connected account's balance. However, if Stripe can't debit
  the amount, ultimate responsibility depends on whether Stripe or the platform is responsible for negative
  balances." [Disputes on Connect platforms](https://docs.stripe.com/connect/disputes) — 2026-10-19
- **[MEASURED]** `fees_collector: stripe`, `losses_collector: stripe` on the test club
  ([`stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`](stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses));
  Stripe collects from the club's bank before it covers anything
  ([`stripe-connect.md#stripe-covers-only-what-it-cant-recover-and-first-takes-it-from-the-clubs-bank`](stripe-connect.md#stripe-covers-only-what-it-cant-recover-and-first-takes-it-from-the-clubs-bank)).
- **[DOCS]** "When you use Managed Risk, you and your connected accounts still need to manage disputes,
  including accepting disputes or submitting evidence before the deadline." "Clearly define
  responsibilities for disputes and refunds in your agreements with connected accounts."
  [Handle refunds and disputes (SaaS)](https://docs.stripe.com/connect/saas/tasks/refunds-disputes) — 2026-10-19

### The club is told by email and in its Dashboard; Raketa only by its Connect endpoint

- **[DOCS]** "We notify you of a dispute through … Your email address, The Stripe Dashboard, A
  `charge.dispute.created` event (if your integration is set up to receive events …), A push notification".
  [Respond to disputes](https://docs.stripe.com/disputes/responding) — 2026-10-19
- **[DOCS]** "You can view all disputes filed against your platform and connected accounts in your
  Dashboard." "We recommend setting up a webhook to listen to dispute created events."
  [Disputes on Connect platforms](https://docs.stripe.com/connect/disputes) — 2026-10-19
- *Code:* no `charge.dispute.*` kind is read, and no seat-charge event for one exists, though the PRD has
  the seat charge "… disputed; folded idempotently from Stripe webhooks" (`prd-530.md:249`)
  ([`stripe-webhooks.md#disputes-on-a-direct-charge`](stripe-webhooks.md#disputes-on-a-direct-charge)).
- **[MEASURED]** `GET /v1/disputes` on the test club → none · `stripe-club` · 2026-10-19.

### A disputed 40 zł share costs the club 130 zł at once, and 90 zł more to fight it

- **[PRICE]** Poland: "The dispute received fee is 90 PLN, and the dispute countered fee is 90 PLN"; the
  countered fee "will be returned if you win"; the received fee is not; the counter fee applies "when you
  counter disputes initiated after June 17, 2025", and for Dashboard connected accounts where Stripe manages
  risk "These changes will apply to the Stripe fees for your connected accounts."
  [Stripe support: June 2025 pricing updates for disputes](https://support.stripe.com/questions/june-2025-pricing-updates-for-disputes)
  — 2026-10-19 (re-confirms [`local-market.md#disputes-cost-90-zł-and-land-on-the-club`](local-market.md#disputes-cost-90-zł-and-land-on-the-club), 2026-10-06)
- **[DOCS]** Stripe "Debits the disputed amount, plus a dispute fee, from your Stripe account." "For
  businesses outside Mexico, the fee for receiving a dispute is non-refundable." Won: "The issuer returns
  the debited chargeback amount to Stripe. Stripe passes this amount back to you." Lost: "No money moves
  from your perspective." [How disputes work](https://docs.stripe.com/disputes/how-disputes-work) — 2026-10-19
- *Reading, in złoty:* on a 40 zł share the club's balance drops by 40 zł + 90 zł = 130 zł when the dispute
  opens; countering takes 90 zł more; a win returns 40 zł + 90 zł; a loss keeps all of it. Stripe's card
  fee on the share (1,60 zł EU, 2,30 zł on 4242) stays kept either way.

### While a dispute is open the share can't be refunded, and a refund still pending fails

- **[DOCS]** "You can't issue a refund outside the dispute process while the dispute is open."
  [How disputes work — receive a dispute](https://docs.stripe.com/disputes/how-disputes-work#receive-dispute);
  "You can't issue a refund on a disputed charge until your customer's card issuer decides in your favor."
  [Dispute withdrawals](https://docs.stripe.com/disputes/withdrawing) — 2026-10-19
- **[DOCS]** `failure_reason: charge_for_pending_refund_disputed` — "A customer disputed the charge while the
  refund is pending. In this case, **Stripe recommends** accepting or challenging the dispute instead of
  refunding to avoid duplicate reimbursements to the customer." [Refunds](https://docs.stripe.com/refunds#failed-refunds) — 2026-10-19
- **[DOCS]** Dispute `is_charge_refundable`: "If true, it's still possible to refund the disputed payment.
  After the payment has been fully refunded, no further funds are withdrawn." An inquiry can be resolved
  "without incurring a dispute fee by … Issuing a full refund." [Dispute object](https://docs.stripe.com/api/disputes/object);
  [How disputes work — inquiries](https://docs.stripe.com/disputes/how-disputes-work#inquiries) — 2026-10-19

### A partly refunded share can still be disputed in full

- **[DOCS]** "A customer can dispute a payment for the full amount even if they've already received a partial
  refund … **Always respond** in such cases because card issuers are very willing to rectify this
  situation." "Provide evidence of the partial refund … the amount and date of the refund, and even a
  screenshot … (this is known as a 'credit issued' response)." "If it's not [fully resolved in your
  favor], you only receive the partially refunded amount. In this case, the dispute's `status` is set to
  `lost`." [Dispute evidence best practices](https://docs.stripe.com/disputes/best-practices#partial-refund-bp) — 2026-10-19
- **[DOCS]** "Inquiries on partially refunded charges can still escalate to a chargeback."
  [How disputes work](https://docs.stripe.com/disputes/how-disputes-work#inquiries) — 2026-10-19
- *Reading:* a late leaver refunded 38,40 zł of 40 zł who disputes the 40 zł is this case.

### 7–21 days to answer, one answer only, 2–3 months in all

- **[DOCS]** "You have a limited window to respond (usually 7 to 21 days …). If you don't respond before the
  deadline, you automatically lose the dispute." "You've only one opportunity to submit your response …
  You can't edit the response or submit additional files." Accepting an inquiry "doesn't resolve" it.
  [Respond to disputes](https://docs.stripe.com/disputes/responding) — 2026-10-19
- **[DOCS]** The issuer decides "usually 60-75 days" after evidence; the whole dispute "can take 2-3 months";
  "Stripe doesn't support the arbitration phase"; rarely a `lost` dispute becomes a "late win".
  [How disputes work](https://docs.stripe.com/disputes/how-disputes-work#dispute-timing) — 2026-10-19
- **[DOCS]** The deadline is `evidence_details.due_by`; the API answers by updating the dispute's `evidence`.
  [Use the API to respond to disputes](https://docs.stripe.com/disputes/api) — 2026-10-19
- Carried: the 120-day window starts on the event date for a service paid ahead
  ([`gaps-EMAIL.md#card-disputes-120-days-longer-for-a-service-paid-ahead`](gaps-EMAIL.md#card-disputes-120-days-longer-for-a-service-paid-ahead)).

### Statuses, reasons and inquiries

- **[DOCS]** `status`: `warning_needs_response`, `warning_under_review`, `warning_closed`, `needs_response`,
  `under_review`, `won`, `lost`, `prevented` ("prevented from becoming a formal chargeback"). `reason`:
  `bank_cannot_process`, `check_returned`, `credit_not_processed`, `customer_initiated`,
  `debit_not_authorized`, `duplicate`, `fraudulent`, `general`, `incorrect_account_details`,
  `insufficient_funds`, `noncompliant`, `product_not_received`, `product_unacceptable`,
  `subscription_canceled`, `unrecognized`. "In extremely rare cases, you might receive more than one dispute
  per payment." [Dispute object](https://docs.stripe.com/api/disputes/object);
  [How disputes work](https://docs.stripe.com/disputes/how-disputes-work#multiple-disputes) — 2026-10-19
- **[DOCS]** Inquiries: "American Express and Discover are the networks that most often use this phase, while
  **Mastercard and Visa no longer use it**"; an unanswered inquiry can escalate "to a formal, and *likely
  unwinnable*, chargeback"; open 120 days without escalation → `warning_closed`.
  [How disputes work — inquiries](https://docs.stripe.com/disputes/how-disputes-work#inquiries) — 2026-10-19.
  Polish cards are almost all Visa or Mastercard
  ([`stripe-holds-and-capture.md#cards-issued-in-poland-are-almost-all-visa-or-mastercard`](stripe-holds-and-capture.md#cards-issued-in-poland-are-almost-all-visa-or-mastercard)).
- **[DOCS]** Events: `charge.dispute.created`, `.updated`, `.closed`, `.funds_withdrawn`,
  `.funds_reinstated`. [Event types](https://docs.stripe.com/api/events/types) — 2026-10-19

### The evidence a booked game would need: the cancellation policy as shown, and that it was played

- **[DOCS]** "Offline services include purchases that are made in advance, such as event tickets and
  reservations, where evidence of a cancellation policy can be material." [Dispute categories](https://docs.stripe.com/disputes/categories) — 2026-10-19
- **[DOCS]** *Credit not processed* (Visa 13.6, 13.7 "Canceled Merchandise/Services"): "The customer claims
  they're entitled to a full or partial refund because they … didn't fully use it, or the transaction was
  otherwise canceled". To overturn: "You already issued the refund your customer is entitled to" or "The
  customer isn't entitled to a refund". Offline-service evidence: the policy "as provided to the customer"
  (`cancellation_policy`, `refund_policy`); "how and where you provided the applicable policy to your
  customer prior to purchase" (`cancellation_policy_disclosure`); "why the customer isn't entitled to a
  refund" (`cancellation_rebuttal`, `refund_refusal_explanation`); the customer's messages
  (`customer_communication`). [Dispute categories — credit not processed](https://docs.stripe.com/disputes/categories) — 2026-10-19
- **[DOCS]** *Product not received* (Visa 13.1): offline-service evidence "showing that the service was
  provided to the cardholder, including the date" (`service_date`, `service_documentation`), or "that the
  agreed-upon service date hasn't arrived yet". *Duplicate*: "Each payment was for a separate product or
  service"; "ensure it can handle errors without double-charging". *Unrecognized*: "effectively
  indistinguishable from the Fraudulent reason"; prevent with a recognisable statement descriptor and
  receipts. [Dispute categories](https://docs.stripe.com/disputes/categories) — 2026-10-19
- **[DOCS]** "The more information your integration collects and passes to Stripe when your customer makes a
  payment, the better your ability to prevent disputes and fraud … and challenge them effectively."
  [Respond to disputes](https://docs.stripe.com/disputes/responding) — 2026-10-19

### What a share carries into a dispute: no customer, no 3-D Secure, the club's name

- **[MEASURED]** `ch_3USEMX5y1DMwE3zY1lrc899G`: `customer: null`, `payment_method_details.card.three_d_secure:
  null`, `electronic_commerce_indicator: "07"`, `calculated_statement_descriptor: "ROBER CLUB"`,
  `description: "Padel · Bonarka Arena"`, `outcome.risk_level: normal`, `disputed: false` · `stripe-club` · 2026-10-19.
- Carried: off-session payments don't support 3DS and the liability shift "typically applies to payments
  successfully authenticated using 3DS"
  ([`gaps-SWIPE.md#stripe-fraud-disputes-are-hard-to-win-and-an-off-session-charge-has-no-3-d-secure-shift`](gaps-SWIPE.md#stripe-fraud-disputes-are-hard-to-win-and-an-off-session-charge-has-no-3-d-secure-shift));
  Visa CE 3.0 needs earlier undisputed payments matching IP, device, email or customer account ID
  ([`gaps-PAY.md#where-an-internet-address-counts-in-a-dispute-and-where-it-does-not`](gaps-PAY.md#where-an-internet-address-counts-in-a-dispute-and-where-it-does-not)).
- *Reading:* the share's payment holds none of the player's name, email, the terms accepted or whether they
  came; Raketa holds them, and nothing hands them to the club.

### Withdrawn disputes still need evidence, and still count

- **[DOCS]** "A withdrawn dispute … isn't *necessarily* a won dispute, because the dispute might still resolve
  as a loss if you haven't submitted evidence"; "It still counts against your dispute rate". "In cases where
  you agree that the customer should keep the disputed funds, accept the dispute rather than ask the
  cardholder to withdraw the dispute for a regular refund." [Dispute withdrawals](https://docs.stripe.com/disputes/withdrawing);
  [Best practices](https://docs.stripe.com/disputes/best-practices) — 2026-10-19

### Early fraud warnings: refund one only below about the 90 zł dispute fee

- **[DOCS]** "If you don't refund the charge, about 40% of Visa and Mastercard EFWs become fraud disputes."
  "The optimal point for issuing a refund on early fraud warnings is on charges that are roughly less than
  or equal to your dispute fee. It's likely not worthwhile to refund EFWs on charges more than 35 percent
  higher than your dispute fee." "Automatically refunding all EFWs … isn't a good strategy."
  [How disputes work — early fraud warnings](https://docs.stripe.com/disputes/how-disputes-work#early-fraud-warnings) — 2026-10-19
- **[DOCS]** `actionable`: "An EFW is actionable if it has not received a dispute and has not been fully
  refunded." Events `radar.early_fraud_warning.created`, `.updated`.
  [Early Fraud Warning object](https://docs.stripe.com/api/radar/early_fraud_warnings/object);
  [Event types](https://docs.stripe.com/api/events/types) — 2026-10-19
- *Reading:* every share (25–40 zł) is below 90 zł; on a direct charge the warning lands on the club's
  account, where only the club's Radar runs
  ([`stripe-connect.md#the-club-writes-its-own-radar-rules-raketas-rules-dont-reach-its-payments`](stripe-connect.md#the-club-writes-its-own-radar-rules-raketas-rules-dont-reach-its-payments)).

### Tools a platform can give its clubs: Smart Disputes and embedded components

- **[DOCS]** "If you use Smart Disputes, you can enable Smart Disputes auto-responses for your connected
  accounts." Disputes list and disputes-for-a-payment embedded components let accounts "manage disputes
  from within your site". [Disputes on Connect platforms](https://docs.stripe.com/connect/disputes) — 2026-10-19
- **[DOCS]** Smart Disputes "automatically submits the pre-filled evidence packet just before the dispute
  times out"; "we only bill you a Smart Disputes fee if you win". [Smart Disputes](https://docs.stripe.com/disputes/smart-disputes) — 2026-10-19

---

## 3. Producing these on the sandbox

### Test cards for a refund that waits or fails, and for each kind of dispute

- **[DOCS]** "With all other test cards, refunds succeed immediately and don't change status after that."
  Refund that starts `pending`, then `succeeded` with `refund.updated`: **4000 0000 0000 7726**
  (`pm_card_pendingRefund`). Refund that starts `succeeded`, then `failed` with `refund.failed`:
  **4000 0000 0000 5126** (`pm_card_refundFail`). [Testing — refunds](https://docs.stripe.com/testing#refunds) — 2026-10-19
- **[DOCS]** Disputes ("charge succeeds, only to be disputed"): fraudulent **4000 0000 0000 0259**
  (`pm_card_createDispute`); product not received **4000 0000 0000 2685**; inquiry **4000 0000 0000 1976**;
  early fraud warning **4000 0000 0000 5423**; multiple disputes **4000 0004 0400 0079**; Smart Disputes
  **4000 0000 0100 0043**. Evidence text `winning_evidence`, `losing_evidence`,
  `escalate_inquiry_evidence` (in `uncategorized_text`, or the Dashboard's *Additional information*).
  [Testing — disputes](https://docs.stripe.com/testing#disputes) — 2026-10-19
- **[ABSENT]** Whether these behaviours survive saving the card on the platform and cloning it onto the club,
  and whether a dispute card fires on a manually captured payment at its capture: not stated on the testing,
  disputes or Connect pages — 2026-10-19. A walk would show it.

---

## Pitfalls

1. **Recording a refund as given from the create call.** "A refund can appear to succeed and later fail, or
   can appear as `pending` at first" ([testing](https://docs.stripe.com/testing#refunds)); a failure comes up
   to 30 days later ([refunds](https://docs.stripe.com/refunds#failed-refunds)). The product records the
   amount whatever the status (`seat_charge.py:733-754`), so a receipt says *refunded* for money the player
   never gets.
2. **Hearing nothing after the refund.** Stripe recommends `refund.created` at a minimum and says the seller
   "must also build internal logic for notifying customers" and must "arrange an alternative way" when
   `refund.failed` arrives ([refunds](https://docs.stripe.com/refunds#refund-events)). All refund kinds are
   dropped (D6).
3. **Retrying a refusal that never clears.** `charge_disputed`, `refund_disputed_payment`,
   `charge_already_refunded` and an amount beyond what is left are final answers
   ([error codes](https://docs.stripe.com/error-codes); [create a refund](https://docs.stripe.com/api/refunds/create));
   the key replays the saved error for 24 hours
   ([`stripe-reliability.md#errors-are-saved-too--except-those-raised-before-execution-begins`](stripe-reliability.md#errors-are-saved-too--except-those-raised-before-execution-begins))
   and the outbox asks every second without end.
4. **Refunding a disputed share.** "You can't issue a refund outside the dispute process while the dispute
   is open"; a pending refund fails with `charge_for_pending_refund_disputed`, and Stripe recommends
   "accepting or challenging the dispute instead of refunding to avoid duplicate reimbursements"
   ([how disputes work](https://docs.stripe.com/disputes/how-disputes-work#receive-dispute);
   [refunds](https://docs.stripe.com/refunds#failed-refunds)). A club cancel or a seat taken after a
   dispute opens meets this.
5. **Assuming a partial refund caps the dispute.** A player can dispute the full amount after a partial
   refund; "Always respond", with the refund's amount and date
   ([best practices](https://docs.stripe.com/disputes/best-practices#partial-refund-bp)).
6. **Forgetting the club's own Dashboard.** It can refund a share, refund it in part, or cancel a card
   refund for a short while ([refunds](https://docs.stripe.com/refunds#cancel-refund)); Raketa's later
   refund then fails as an over-refund, or Raketa's refund silently turns `canceled`.
7. **Taking the sandbox's instant success for the live behaviour.** Only 7726 and 5126 make a refund wait or
   fail ([testing](https://docs.stripe.com/testing#refunds)); every sandbox refund so far was `succeeded`
   at once ([`stripe-sandbox.md#refunds-exactly-the-amounts-asked-succeeded-at-once`](stripe-sandbox.md#refunds-exactly-the-amounts-asked-succeeded-at-once)),
   and a pre-settlement refund was netted against pending funds where the docs speak of the available
   balance ([above](#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once)).
8. **Promising Stripe's refund email.** Stripe emails only for a charge made on a Customer
   ([refunds](https://docs.stripe.com/refunds#refund-requests)); a share's payment has none, so Raketa's
   own message is the only one the player gets.
9. **Telling the player to look for a credit after a reversal.** A refund within about two hours of the
   capture "drops off the customer's statement, and a separate credit isn't issued", with no ARN
   ([refunds](https://docs.stripe.com/refunds#refund-and-reversal);
   [how disputes work](https://docs.stripe.com/disputes/how-disputes-work#early-fraud-warnings)).
10. **Leaving the seller without evidence.** For a reservation the decisive evidence is the cancellation
    policy "as provided to the customer", "how and where" it was shown, and proof the service was provided
    and when ([categories](https://docs.stripe.com/disputes/categories)); "the more information your
    integration … passes to Stripe", the better ([responding](https://docs.stripe.com/disputes/responding)).
    A share's payment carries no customer, no email and no policy.
11. **A dispute nobody hears.** The club gets Stripe's email; the platform gets only
    `charge.dispute.created` on its Connected-accounts endpoint, which Stripe recommends listening to
    ([Connect disputes](https://docs.stripe.com/connect/disputes)). The product reads none, so its receipts,
    the club's Money and its payouts carry on as if the share were paid.
12. **Counting a club's money without its disputes.** A dispute takes the share plus 90 zł from the club's
    balance at once ([how disputes work](https://docs.stripe.com/disputes/how-disputes-work);
    [June 2025 pricing](https://support.stripe.com/questions/june-2025-pricing-updates-for-disputes)); a
    payout sized from Raketa's own ledger then asks for money the balance no longer holds, and a negative
    balance blocks payouts ([`stripe-connect.md#stripe-covers-only-what-it-cant-recover-and-first-takes-it-from-the-clubs-bank`](stripe-connect.md#stripe-covers-only-what-it-cant-recover-and-first-takes-it-from-the-clubs-bank)).
13. **Missing the deadline.** 7–21 days, one submission, and no answer is a loss
    ([responding](https://docs.stripe.com/disputes/responding)); a club that doesn't read Stripe's email
    loses 130 zł per disputed 40 zł share by default.
14. **Refunding every early fraud warning, or none.** Stripe's threshold is a charge at or below the dispute
    fee ([how disputes work](https://docs.stripe.com/disputes/how-disputes-work#early-fraud-warnings)); each
    share is below 90 zł.

## Checks

1. Does the rule say what the player and the club see while a refund is **pending**, and when it **fails**
   up to 30 days later — and who pays the player another way? Stripe puts that on the seller, the club.
2. Is a refund shown as given only when Stripe says `succeeded`, or does the receipt say it is on its way?
3. Does the product hear `refund.created`, `refund.updated` and `refund.failed` on its Connected-accounts
   endpoint, and re-read the refund as the club?
4. Is every refund at most what is left on the charge, given the club may have refunded part of it in its
   own Dashboard?
5. Does a refusal that never clears (`charge_disputed`, `refund_disputed_payment`,
   `charge_already_refunded`, too large) stop being retried and reach a person?
6. When a share is disputed, does the rule stop every refund of it, and say who is told — the club, the
   player, Raketa?
7. Does the rule say the club pays a dispute — the share and 90 zł at once, 90 zł more to counter, the 90 zł
   received fee never back — and does the club's Money show it?
8. Can the club, in its own Dashboard, show what each likely reason needs: the cancellation policy as the
   player saw it and when they accepted it, the leave sheet's words, the game's date and whether they came?
9. For a share refunded in part (a late leaver's 38,40 zł of 40 zł), does the rule expect a dispute of the
   whole 40 zł and tell the club to answer with the refund?
10. Does any refund time the product promises match Stripe's: about 5–10 business days to a card, nothing
    visible after a reversal, an ARN within 7 business days?
11. Does any text promise the player an email from Stripe about a refund? None is sent.
12. Is a refund made before the share's money is available expected to wait (`charge_pending`,
    `insufficient_funds`) or go through? The sandbox nets it against pending funds, and live is unread.
13. Does a payout sized from Raketa's ledger survive a dispute, or a refund the club made itself?
14. Was a refund rule proven only on the fake or on a card whose refunds always succeed, rather than on
    4000 0000 0000 7726 and 5126?
15. When a club account is closed, removed or disabled, are the refunds it still owes, and its open disputes,
    accounted for?
16. Does an early fraud warning on a share lead anywhere, given that only the club's Radar sees it and the
    product reads no `radar.early_fraud_warning.*`?
