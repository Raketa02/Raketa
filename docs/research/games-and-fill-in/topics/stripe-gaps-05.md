# Stripe gaps 05 — CLUBMONEY and RESCUE (payments pass, prd-530)

Answers to sixteen `stripe:` gaps: two CLUBMONEY, fourteen RESCUE. Each `### ` heading names the rule it serves.

- **Read on:** 2026-10-20, against the code at `9ab0ea5b`.
- **Docs:** docs.stripe.com (en-US unless marked; Spanish-served pages quoted *(translated)*), support.stripe.com and
  Stripe's changelog, fetched directly. The Stripe MCP servers were disconnected.
- **The sandbox:** read only, through stripe-python 15.6.1 in the copy with its test key, 2026-10-20 08:26–08:40 UTC:
  the platform and its 8 connected accounts, including the test club `acct_1US95f5y1DMwE3zY` (Robert Club). Cited as
  **[MEASURED]** "read via the SDK in the copy".
- **Already answered elsewhere:** cited by anchor, not repeated.

---

### R-CLUBMONEY-23 · A Polish club can be paid out in euros, and each payout then reads in its own currency

**Answer.** Yes. A club on the full Stripe Dashboard adds a settlement currency itself, without Raketa. A payout in
that currency is listed with its own `currency`, which the adapter ignores.

- **[DOCS]** "Connected accounts with access to the full Stripe Dashboard have automatic access to multi-currency
  settlement, and can manage their own settlement currencies independently. Your platform setting doesn't affect
  them." Available in the EU; "If your platform is in the EEA, the connected account can be in any EEA country." The
  account adds it "during onboarding", in its "Dashboard Payout settings", or with "**Add settlement currency** on the
  Balances page". [Multi-currency settlement (Connect)](https://docs.stripe.com/connect/multi-currency-settlement?locale=en-US) — 2026-10-20
- **[DOCS]** "If you use multiple bank accounts, you must select a default settlement currency, which you can change at
  any time." "Charges that are presented in any enabled settlement currency settle without currency conversion."
  "Payments presented in a currency that you haven't configured an additional bank account for automatically convert
  to your default currency." [Payouts](https://docs.stripe.com/payouts?locale=en-US) — 2026-10-20
- **[DOCS]** "To accrue a balance in a given currency, you must first accept payments in that currency."
  [Multi-currency settlement](https://docs.stripe.com/payouts/multi-currency-settlement?locale=en-US) — 2026-10-20
- **[DOCS]** "You can't delete the default external account for a currency if … The external account's `currency`
  code is the same as the `account.default_currency`." [Bank accounts (Connect)](https://docs.stripe.com/connect/payouts-bank-accounts) — 2026-10-20
- **[DOCS]** A payout's `amount` is "in the smallest currency unit", beside its own `currency`; a bank refusing the
  currency fails it with `invalid_currency`. [Payout object](https://docs.stripe.com/api/payouts/object?locale=en-US) — 2026-10-20
- **[MEASURED]** The test club has one bank account, `ba_1US9LA5y1DMwE3zYHPe7QQUm` (PL, `pln`,
  `default_for_currency: true`), and `default_currency: pln`. All 8 connected accounts are PL / `pln`.
- **[ABSENT]** Stripe's settlement-currency table for an EU account (it renders only as "See table on original page",
  in HTML and `.md`), and whether a Polish account may make euros its *default*, so złoty shares convert. Looked in
  both multi-currency pages, Payouts, settlement-payouts and Balance Settings — 2026-10-20.

**For the Payouts card.** Shares are charged in złoty (`backend/app/modules/payments/infrastructure/stripe_payments.py:500`).

- **Euro account added, złoty kept:** shares still settle and pay out in złoty. Nothing changes.
- **Euros made the default, if Poland allows it:** every share converts; payouts list as `currency: "eur"` in cents.
  `payouts()` reads `payout.amount` into `amount_grosze` and never reads `payout.currency`
  (`stripe_payments.py:393-410`), so 100,00 € shows as 100,00 zł. The fee is in euros too, so `_fee_of` reads it as
  *not yet known* for ever (`stripe_payments.py:115-127`, the check at `:125`).

---

### R-CLUBMONEY-22 · A dispute on a partly refunded share takes the disputed amount and the fee; a lost one returns only the refunded part

**Answer.** Stripe takes the disputed amount from the club's balance at once, usually the whole 40,00 zł even after a
38,40 zł refund, plus the dispute fee
([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#a-disputed-40-zł-share-costs-the-club-130-zł-at-once-and-90-zł-more-to-fight-it)).
Fully won, the 40,00 zł comes back; otherwise only the refunded 38,40 zł comes back, and the dispute reads `lost`.

- **[DOCS]** "A customer can dispute a payment for the full amount even if they've already received a partial refund
  … Always respond." "In most cases, the card issuer cancels the original dispute and then creates a separate one for
  the corrected amount. On Stripe, we use the existing dispute to track the overall outcome. If the dispute is fully
  resolved in your favor, you receive the entire amount back. If it's not, you only receive the partially refunded
  amount. In this case, the dispute's `status` is set to `lost`." The response is a "credit issued" one: "the amount
  and date of the refund, and even a screenshot" (`refund_refusal_explanation`).
  [Dispute evidence best practices](https://docs.stripe.com/disputes/best-practices#partial-refund-bp) — 2026-10-20
- **[DOCS]** *(translated)* Stripe "debits your Stripe account the disputed amount plus a dispute fee"; no refund
  "outside the dispute process while it is open". Listed among amounts that differ: "a business partially refunded a
  payment, but the account holder disputes the full payment". [How disputes work](https://docs.stripe.com/disputes/how-disputes-work#disputed-amount) — 2026-10-20
- **[DOCS]** Dispute `balance_transactions`: "zero, one, or two balance transactions that show funds withdrawn and
  reinstated"; `is_charge_refundable`: "After the payment has been fully refunded, no further funds are withdrawn".
  [Dispute object](https://docs.stripe.com/api/disputes/object?locale=en-US); `charge.dispute.funds_reinstated` is
  sent "including partially refunded payments" ([Refunds — events](https://docs.stripe.com/refunds?locale=en-US#refund-events)) — 2026-10-20
- **[ABSENT]** The balance entries when the bank disputes 40,00 zł and later corrects it to 1,60 zł: whether 38,40 zł
  comes back early or at the close, and how the two transactions split. No page shows them, and a test dispute fires
  only at the capture, so none can follow a refund ([`stripe-testing.md`](stripe-testing.md#the-dispute-cards-and-how-to-win-or-lose-one)).
  A question for Stripe support — 2026-10-20.

---

### R-RESCUE-20 · Keeping back exactly the card's fee from a refund: Stripe's terms and its PSD2 note, and no ruling

**Answer.** No Stripe page rules on it.

- Carried **[POLICY]** Services Agreement §3.4(e): "Except to the extent the Card Network Rules or Law permits, User
  must not charge surcharges, other fees, or Taxes for accepting payment cards". Carried **[DOCS]** PSD2 note: "the
  surcharge ban does not impact the platform or application fee you charge", "provided that these fees are not
  differentiated by payment method". Both in [`gaps-S-01A-leave-fee.md`](gaps-S-01A-leave-fee.md#stripes-terms-forbid-card-surcharges-unless-the-law-permits-them)
  (2026-10-10; Polish law in its §5). Same question for a leaver: [`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-6--keeping-stripes-fee-back-from-a-consumers-refund-under-the-surcharge-clause).
- **[DOCS]** "Stripe's processing fees from the original transaction aren't returned." [Refunds](https://docs.stripe.com/refunds?locale=en-GB);
  "For all refunds, payment processing, Connect, and currency conversion fees from the original charge are not
  returned." [Fees for refunded payments](https://support.stripe.com/questions/understanding-fees-for-refunded-payments) — 2026-10-20
- **[MEASURED]** The amount kept differs by card: 1,60 zł on the Polish Visa, 2,30 zł on Stripe's US card, for the same
  40,00 zł share (section below; [`stripe-sandbox.md`](stripe-sandbox.md#differences) D5). *Reading:* by Stripe's own
  PSD2 test, what is kept differs by payment method.
- **[ABSENT]** Whether keeping exactly the processing fee back from a consumer's refund is a "surcharge … or other
  fee" under §3.4(e). Looked in refunds, the refunded-fees article, surcharging, a support search — 2026-10-20. For
  Stripe support and the club's lawyer.

---

### R-RESCUE-20 · A refund made as a reversal: Stripe's refunds page says both that fees aren't returned and that none is withheld

**Answer.** Still open; Stripe's page supports two readings.

- **One way:** "doesn't withhold any fees for payment reversals" gives the club its 1,60 zł back, and Bonarka Arena
  holds 1,60 zł kept from Ivan that it never paid.
- **The other way:** only IC+ users are named as seeing a cost difference, so on standard pricing (Raketa's clubs) the
  fee stays with Stripe and the sentence means no extra fee for the reversal. Sibling files take this reading,
  unverified: [`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-6--whether-a-reversal-gives-the-club-its-original-fee-back),
  [`stripe-gaps-04.md`](stripe-gaps-04.md#r-clubmoney-2--the-fee-on-a-partial-reversal-how-soon-shortly-is-and-a-reversal-on-the-sandbox).

- **[DOCS]** Glossary, en-US and en-GB alike: "A reversal is the cancellation of a transaction. Stripe doesn't withhold
  any fees for payment reversals." "IC+ users might see a difference in cost between reversals and refunds because
  reversals usually incur lower network fees." [Refunds — refund and reversal](https://docs.stripe.com/refunds?locale=en-GB#refund-and-reversal) — 2026-10-20.
  The page's and the support article's "not returned" sentences (previous section) don't mention reversals.
- Carried **[DOCS]** "usually … within 2 hours of the payment capture"; reads `destination_details.card.type =
  "reversal"` ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line)).
- **[MEASURED]** All 34 latest refunds on the test club read `type: refund`, none `reversal`, many seconds after capture.
- **[ABSENT]** Whether a standard-pricing club gets the fee back on a reversal, how that shows on its balance, and how
  long after capture a refund is a reversal. Test mode can't make one; for Stripe support or a live account.

---

### R-RESCUE-20 · The Polish test Visa costs 1,60 zł on a 40 zł share (measured)

**Answer.** Measured: two shares taken on the test club with `4000 0061 6000 0005`. Stripe kept **1,60 zł** each, the
EU personal-card price, and the leaver got back **38,40 zł**.

- **[MEASURED]** On `acct_1US95f5y1DMwE3zY`:

| Charge | PaymentIntent | Made (UTC) | Card | Amount | Fee kept | Refunded |
|---|---|---|---|---|---|---|
| `ch_3USPFA5y1DMwE3zY0VSNB1u9` | `pi_3USPFA5y1DMwE3zY0LyICoBw` | 2026-10-19 22:41:24 | Visa •••• 0005, PL, credit | 40,00 zł | 1,60 zł | 38,40 zł |
| `ch_3USPCF5y1DMwE3zY1HE29XAk` | `pi_3USPCF5y1DMwE3zY1ZZ8B4cn` | 2026-10-19 22:38:23 | Visa •••• 0005, PL, credit | 40,00 zł | 1,60 zł | 38,40 zł |

  Both captured; fee from each charge's balance transaction (`fee 160`, `pln`); `capture_before` 7 days out.
- Carried **[DOCS]** Poland: 1,5 % + 1 zł for a standard EEA card ([`gaps-S-01A-leave-fee.md`](gaps-S-01A-leave-fee.md), 2026-10-10).
- **[MEASURED]** The test club's latest 100 charges: 96 US, 2 GB (3178), 2 PL. The sandbox prices by card country:
  2,30 zł on 4242, 1,60 zł on 0005.
- **For a walk:** `4000 0061 6000 0005` gives the product's own 38,40 zł back, not 4242's 37,70 zł. Settles the note in
  [`stripe-testing.md`](stripe-testing.md#a-polish-visa-exists-4000-0061-6000-0005).

---

### R-RESCUE-14 · Pressing I'm in is "on session" by Stripe's own definition; what mis-flagging costs is unpublished

**Answer.** A payment made ten seconds after the player pressed I'm in is, in Stripe's words, on session, so
customer-initiated. `off_session: true` lets Stripe claim an exemption and may mark it recurring with the network.
When the customer is present Stripe expects confirmation on their device, any bank step handled there. What networks
do to a mis-flagged payment is not published.

- **[DOCS]** "When a payment is made 'on session', the customer is present on your website or mobile application."
  "By default, payments in our API are 'on session'." Off session: "the customer is not present … to confirm the
  payment" (renewals, late fees, MOTO). "By indicating that the payment … is 'off session', you allow Stripe to either
  skip some of those steps or claim an exemption with the partner." "Setting `off_session: true` might cause us to mark
  the transaction as recurring with the card network." "If any action is needed … you would need to get the customer
  back 'on session'." [On vs off session](https://support.stripe.com/questions/what-is-the-difference-between-on-session-and-off-session-and-why-is-it-important) — 2026-10-20
- **[DOCS]** `off_session`: "the customer isn't in your checkout flow during this payment attempt and can't
  authenticate." [Create a PaymentIntent](https://docs.stripe.com/api/payment_intents/create?locale=en-US&query=off_session);
  CITs include "any transaction where the cardholder is available to participate in the payment flow"
  ([CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-US)) — 2026-10-20
- **[DOCS]** Stripe and the networks classify "based on signals of cardholder participation, not solely on … `off_session`"
  ([Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US), 2026-10-20); on the
  sandbox every off-session hold got the customer-initiated window
  ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#on-the-sandbox-an-off-session-visa-hold-lasts-exactly-7-days-and-offers-nothing-beyond-a-plain-hold)).
- *Code:* every hold, the rescue's included, is `off_session: True, confirm: True` on the club's account
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:505-507`).
- **[ABSENT]** The network rules on a customer-initiated payment flagged merchant-initiated, and what Stripe does when
  flag and signals disagree beyond the window. Looked in CITs/MITs, SCA exemptions, the session article, place-a-hold,
  declines — 2026-10-20. For Stripe support.

---

### R-RESCUE-14 · A full-share hold cancelled at once: the networks "may restrict" it, and no source says whether this counts

**Answer.** Still not found. Stripe speaks only of 1 USD authorizations. Cancelling costs nothing on standard pricing;
on IC+ each void is a fee-bearing request.

- **[DOCS]** "Card networks may also restrict 1 USD authorizations you don't intend to capture." [Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US);
  carried with Visa's account-verification wording ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card)).
- **[DOCS]** "You can cancel a payment before it's completed at no cost." [Refunds](https://docs.stripe.com/refunds?locale=en-GB);
  on IC+, per-auth fees apply to "authorization (successful and declined), void, charge, reversal, or to validate a
  card" ([IC+ fees](https://support.stripe.com/questions/understanding-ic-fees)); *(translated)* a void can be up to 24
  times cheaper than a refund, and an authorisation can "generally" stay open "up to two days before paying additional
  fees" ([Network costs guide](https://stripe.com/guides/guide-to-managing-network-costs)) — 2026-10-20
- **[ABSENT]** Whether Visa or Mastercard treat a full-share authorisation cancelled the same second, as a card check,
  as one "you don't intend to capture". No Stripe page covers misuse-of-authorisation or zero-amount checks — 2026-10-20.
  For Stripe support.

---

### R-RESCUE-14 · The window of a rescue hold the player authenticated: 7 days by Stripe's table, still unread on the sandbox

**Answer.** The window runs 7 days from the successful authorisation, for Visa and Mastercard alike, since a payment
the cardholder completes in the app is customer-initiated. No such payment exists on the sandbox to confirm it.

- **[DOCS]** Customer-initiated: 7 days on Visa, Mastercard, Amex, Discover; Visa merchant-initiated "4 days and 18
  hours". "`capture_before` … indicates when the authorization expires." [Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-US);
  a failed attempt "returns to `requires_payment_method`" ([Payment status updates](https://docs.stripe.com/payments/payment-intents/verifying-status?locale=en-US)) — 2026-10-20
- **[MEASURED]** No charge on any of the 8 accounts carries `three_d_secure` (test club's latest 100, all of the other
  seven's). The bank-check refusals `pi_3USPJ05y1DMwE3zY0QhCXhff`, `pi_3USPGb5y1DMwE3zY0lldplS1`,
  `pi_3USSck5y1DMwE3zY1AR9oPkr` were cancelled unconfirmed. Carried note stands:
  [`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#a-payment-the-player-confirms-in-the-app-its-window-is-still-unread).
- **[MEASURED]** Nearest case: `pi_3USPIk5y1DMwE3zY03JvGogQ`, refused off-session then confirmed with a typed card
  (no 3-D Secure); `capture_before` is exactly 168 h after the successful charge
  ([`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-45--the-window-stamped-on-a-payment-confirmed-after-the-banks-check)).
- **[ABSENT]** The stamp itself. *To answer:* on a phone, a rescue refused with `4000 0027 6000 3184`, then
  authenticated in the app; read its charge's `capture_before`.

---

### R-RESCUE-21 · Taking a hold after the club's charges are disabled: undocumented

**Answer.** Still not found. Stripe documents that disabling blocks *creating* charges, not capturing one already
authorised; the sandbox doesn't enforce capabilities.

- Carried **[ABSENT]**: [`stripe-connect.md`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled),
  [`stripe-gaps-04.md`](stripe-gaps-04.md#r-clubmoney-9--capturing-a-held-share-or-refunding-once-charges_enabled-is-false-or-the-account-is-removed).
- **[DOCS]** "A capability must be active for a connected account to perform actions associated with that
  capability." "Sandboxes might not enforce some capabilities." [Account capabilities](https://docs.stripe.com/connect/account-capabilities?locale=en-US);
  "Pausing payments blocks creation of any charges"; "we don't enforce … pauses in a sandbox"; not available on
  Accounts v2 ([Pausing](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts?locale=en-US)) — 2026-10-20
- **[DOCS]** A refusal might read `capability_not_active` ("missing the active capabilities required to access this
  endpoint"). [Error codes](https://docs.stripe.com/error-codes?locale=en-US) — 2026-10-20
- **[MEASURED]** 7 of 8 connected accounts read `charges_enabled: false` and hold no payment; no case to read.
- **[ABSENT]** Whether a `requires_capture` payment can be captured after `card_payments` went inactive. It decides
  whether a refund decided on an authorisation is ever matched by a take. For Stripe support or a live account.

---

### R-RESCUE-24 · Recovering a refused clone: the spent clone is refused, a fresh clone is accepted on the same payment, and neither is Stripe's stated recovery

**Answer.** Stripe's recovery confirms the same PaymentIntent with the card on its last error; on a clone that card
is spent, and Stripe refuses it. Documented ways to charge again: a **fresh clone** of the platform card, or the clone
**attached to a Customer** on the club's account. The sandbox accepts a fresh clone on the original refused payment,
at least as far as opening the bank's check. No page names either as the recovery.

- **[DOCS]** "Creating a charge with the cloned PaymentMethod consumes it … You can't reuse the consumed clone, but you
  can clone the platform PaymentMethod again and use the new clone for another charge." Recurring charges need "a
  Customer object on the connected account" with the clone attached. [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts?locale=en-US) — 2026-10-20
- **[MEASURED]** The spent clone, refused twice: FILL `pi_3USPJ05y1DMwE3zY0QhCXhff` (`req_8rsitla8xVevKv`) and RESCUE
  R6 `pi_3USSck5y1DMwE3zY1AR9oPkr` (`req_p0SEYswKwenFJu`). Stripe's message, per the FILL log: "The provided
  PaymentMethod was previously used with a PaymentIntent without Customer attachment…". This closes
  [`stripe-authentication.md`](stripe-authentication.md#whether-a-clone-used-up-by-a-failed-attempt-can-confirm-the-same-payment-on-session): no.
- **[MEASURED]** A fresh clone on `pi_3USPGP5y1DMwE3zY0vlzqtWy` (3184, test club) moved it to `requires_action`
  (`req_lqtcr6tCX8Zq8A`): [`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-45--a-fresh-copy-of-the-saved-card-is-accepted-on-the-original-refused-payment).
- **[ABSENT]** Which Stripe sanctions — a fresh clone on the same PaymentIntent, or a per-club Customer — and neither
  shown end to end with authentication. Looked in the cloning page, the RN save-and-reuse guide, PaymentMethod and
  confirm references, error codes — 2026-10-20. For Stripe support.

---

### R-RESCUE-24 · The bank's check at I'm in, on a phone: never walked, and nothing on the sandbox carries a 3-D Secure result

**Answer.** Unmeasured; only a walk can answer it.

- **[MEASURED]** No charge on the 8 accounts carries a 3-D Secure result. The test club's six 3184 refusals all came
  off-session and were cancelled unconfirmed (e.g. `evt_3USSck5y1DMwE3zY1aRy4YDy` on `pi_3USSck5y1DMwE3zY1AR9oPkr`).
- What the phone must do is documented: confirm under the club's account id
  ([`stripe-authentication.md`](stripe-authentication.md#a-direct-charge-is-confirmed-on-the-phone-under-the-clubs-account-id)),
  return from the bank's app ([`stripe-authentication.md`](stripe-authentication.md#the-way-back-from-the-banks-own-app)),
  show the challenge for 3184 ([`stripe-testing.md`](stripe-testing.md#the-phones-challenge-screens)).
- **[ABSENT]** A phone walk: `4000 0027 6000 3184` typed into the app, then I'm in on a rescue seat. It needs a usable
  card on the club's account (section above).

---

### R-RESCUE-25 · Stripe's test cards send the bank's soft decline with `authentication_required` in both fields; no card sends it under `card_declined`

**Answer.** On the sandbox every bank-check refusal reads `code` and `decline_code` both `authentication_required`,
which the adapter reads as the bank wanting the player. No test card gives `card_declined` with decline code
`authentication_required` or `authentication_not_handled`. Stripe lists `authentication_required` as a decline code,
and `card_declined` errors carry decline codes, so a live soft decline under `card_declined` stays possible and unproven.

- **[MEASURED]** The test club's `payment_intent.payment_failed` events:

| Card | Events | `code` | `decline_code` | Example |
|---|---|---|---|---|
| •••• 3184 | 6 | `authentication_required` | `authentication_required` | `evt_3USSck5y1DMwE3zY1aRy4YDy` |
| •••• 3178 | 2 | `authentication_required` | `authentication_required` | `evt_3USPGb5y1DMwE3zY00RzyN84` |
| •••• 0002 | 10 | `card_declined` | `generic_decline` | `evt_3USPKC5y1DMwE3zY0YesMNt9` |
| •••• 0341 | 13 | `card_declined` | `generic_decline` | `evt_3USSg75y1DMwE3zY0wKIz8jN` |
| •••• 9995 | 1 | `card_declined` | `insufficient_funds` | `evt_3USPFY5y1DMwE3zY0Zptxtd8` |
| •••• 0069 | 1 | `expired_card` | `expired_card` | `evt_3USPFY5y1DMwE3zY0Oa9cO8B` |

  All `type: card_error`. A cancelled PaymentIntent reads `last_payment_error: null`; the codes survive only in events.
- **[DOCS]** The testing page's declines (0002, 9995, 9987, 9979, 0069, 0127, 0119, …4241, 6975) never use
  `authentication_required` nor name `authentication_not_handled` ([Testing](https://docs.stripe.com/testing?locale=en-GB)).
  "Payment attempts might also require authentication and fail with an `authentication_required` decline code"
  ([Card declines](https://docs.stripe.com/declines/card?locale=en-US#off-session-declines)). `card_declined`: "the error
  returned also includes the `decline_code`" ([Error codes](https://docs.stripe.com/error-codes?locale=en-US)) — 2026-10-20.
  Carried: [`stripe-authentication.md`](stripe-authentication.md#authentication_required-is-also-an-issuers-decline-code).
- *Code:* the adapter tests only `refusal.code == "authentication_required"` (`stripe_payments.py:519-541`, `:523`). A
  `card_declined` + `authentication_required` refusal becomes `DECLINED` with that decline code, and the rescuer reads
  "declined, use another card". Reading `decline_code` too would close it either way.
- **[ABSENT]** Which `code` a live issuer's soft decline carries off-session. For Stripe support.

---

### R-RESCUE-26 · No expiry for a waiting payment; the sandbox cancelled one when it was confirmed after ten failed attempts

**Answer.** No published wait limit; Stripe treats an open payment as one an integration may keep. "Too many"
confirmations is unpublished too. On the sandbox a PaymentIntent took ten failed attempts, and the next confirmation
was answered `payment_intent_unexpected_state` with the PaymentIntent `canceled`, no reason. Stripe recommends at most
eight retries.

- **[DOCS]** "You can keep a PaymentIntent in an incomplete status, like `requires_confirmation` or
  `requires_payment_method`." [Refunds — cancel a payment](https://docs.stripe.com/refunds?locale=en-GB#cancel-payment);
  carried "confirmed too many times", no number ([`stripe-authentication.md`](stripe-authentication.md#a-payment-confirmed-too-many-times-is-cancelled-by-stripe)) — 2026-10-20
- **[DOCS]** "Card networks limit the number of times you can reattempt a single charge. Stripe recommends a maximum of
  eight retries." [Card declines](https://docs.stripe.com/declines/card?locale=en-US#declined-card-retries) — likely the
  spec's "At most 8 retries". `card_decline_rate_limit_exceeded`: "declined too many times … again after 24 hours"
  ([Error codes](https://docs.stripe.com/error-codes?locale=en-US)) — 2026-10-20
- **[MEASURED]** `pi_3USPKC5y1DMwE3zY00HIKsMU` (40,00 zł), created 22:46:36 UTC 2026-10-19: ten failed charges (the
  off-session hold on 0341, then nine typed 0002, all `generic_decline`), each with `charge.failed` and
  `payment_intent.payment_failed`; then `canceled`, `cancellation_reason: null`, at 22:46:49. Its
  `payment_intent.canceled` (`evt_3USPKC5y1DMwE3zY0xQEMKTV`) carries `req_ZW2hNCf2S7SLgf`, none of the charges'
  requests; by the FILL breaker's S5 log it is the tenth typed confirmation. Same payment in
  [`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-45--stripe-cancelled-a-payment-after-ten-failed-tries).
- **[ABSENT]** Whether ten is the live number, and any time limit on `requires_payment_method` or `requires_action`.
  For Stripe support.

---

### R-RESCUE-28 · A lapsed hold reads `cancellation_reason: expired` and sends `charge.expired` and `payment_intent.canceled`; the sandbox reading waits until 26 October

**Answer.** Stripe's changelog answers it from `2025-03-31.basil`, earlier than both versions the product speaks: a
lapsed hold is cancelled with `cancellation_reason: expired` (replacing `automatic`), `charge.expired` and
`payment_intent.canceled` are still sent, and no Refund is made. Raketa's own cancels read `null`, as did Stripe's
too-many-confirmations cancel above.

- **[DOCS]** "A new `cancellation_reason` value called `expired` … represents payments canceled because of
  authorization expiration. It replaces the formerly used value of `automatic`." "We'll still send `charge.expired`,
  `charge.captured`, and `payment_intent.canceled` events." Cancellation, "both manual and automated", creates no
  `Refund`; "`amount_captured` will be 0"; "`refunded` will no longer be `true`".
  [Changelog 2025-03-31.basil](https://docs.stripe.com/changelog/basil/2025-03-31/remove-refund-from-partial-capture-and-payment-cancellation-flow) — 2026-10-20
- Versions: SDK pins `2026-08-26.dahlia`, account renders `2026-09-30.endive`
  ([`stripe-reliability.md`](stripe-reliability.md#each-request-speaks-one-version-the-header-else-the-sdks-pin-else-the-account-default)).
  Corrects [`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#which-reason-and-which-events-an-expired-hold-carries-undocumented-readable-on-the-sandbox-after-26-october).
- **[MEASURED]** 08:26 UTC: no `charge.expired` on any account. Still `requires_capture` on the test club:
  `pi_3USA7i5y1DMwE3zY0Nemxwtn` (`capture_before` 2026-10-26 06:32:43), `pi_3USELx5y1DMwE3zY14aUf4wv` (11:03:41),
  `pi_3USHgd5y1DMwE3zY0vozapC7` (14:37:15).
- **To confirm:** after 2026-10-26 06:32:43 UTC, read `pi_3USA7i5y1DMwE3zY0Nemxwtn` and the test club's
  `charge.expired` and `payment_intent.canceled` events.

---

### R-RESCUE-47 · A refund made before the club's money is available: Stripe's refunds page says it waits, a support page says only a negative balance makes it wait, and the sandbox nets it

**Answer.** Still open live. The refunds page: refunds use the *available* balance, "not including pending amounts",
so a short refund waits `pending`. A support article: a refund waits when it "results in a negative account balance",
which fits the sandbox netting it against pending money. If it waits, it fails after 45 days with
`insufficient_funds`, and the product hears neither. Siblings reach the same split:
[`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-7-r-leave-36-r-leave-41-r-leave-51--a-refund-pending-for-want-of-money-fails-after-45-days-whether-a-live-refund-of-a-fresh-capture-waits-is-still-unstated),
[`stripe-gaps-04.md`](stripe-gaps-04.md#r-clubmoney-33--how-long-a-card-refund-may-stay-pending-for-insufficient_funds-and-a-live-refund-made-before-its-charge-is-available).

- **[DOCS]** "Refunds use your available Stripe balance (not including pending amounts). If your available balance
  doesn't cover the amount of the refund, Stripe holds the refund as pending for card transactions … until your Stripe
  balance becomes sufficient." [Refunds](https://docs.stripe.com/refunds?locale=en-GB) — 2026-10-20
- **[DOCS]** `pending_reason`: `processing`, `insufficient_funds` or `charge_pending` ([Refund object](https://docs.stripe.com/api/refunds/object?locale=en-US&query=pending_reason)).
  Causes: "The refunding payment has not been settled", "an insufficient balance"; "Stripe automatically fails a
  pending refund after 45 days"; "Whether a refund is put into `pending` depends on the type of Connect set-up"
  ([Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund),
  [Refund statuses](https://support.stripe.com/questions/understanding-refund-statuses)) — 2026-10-20
- Carried **[DOCS]** "a refund … that results in a negative account balance … will show as `pending`"
  ([support](https://support.stripe.com/express/questions/pending-refunds-due-to-insufficient-funds-or-negative-balance));
  direct charges: "If the connected account's balance is insufficient, we set the refund status to `pending`"
  ([`stripe-connect.md`](stripe-connect.md#refunds-and-disputed-money-come-out-of-the-clubs-balance-a-short-refund-waits)).
- **[MEASURED]** Carried: a 38,24 zł refund before its charge was available read `succeeded`, its balance transaction
  `pending`, with 0,00 zł available ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once)).
  Now: none of 34 refunds is `pending`; four are `failed` (`expired_or_canceled_card`): `re_3USPJm5y1DMwE3zY1S3GJVRF`,
  `re_3USPIG5y1DMwE3zY1laOFgA7`, `re_3USPCn5y1DMwE3zY1f6MP6cg`, `re_3USOki5y1DMwE3zY1vMVdEMD` — unheard by the product.
- *Reading:* a club Raketa opens pays out daily ([`stripe-payouts-and-balances.md`](stripe-payouts-and-balances.md#a-club-account-raketa-opens-is-on-daily-payouts-the-test-club-is-on-manual)),
  and a share taken at the cut-off is available 3 business days later, 7 calendar days on a new account
  ([`stripe-payouts-and-balances.md`](stripe-payouts-and-balances.md#a-polish-accounts-first-money-is-available-7-calendar-days-after-capture-later-money-3-business-days-after)).
  On the refunds page's rule a seat-taken refund will often wait.
- **[ABSENT]** Which rule holds live, and which `pending_reason` such a refund carries. For Stripe support.

---

### R-RESCUE-40 · What a "credit not processed" dispute needs: the policy shown before the purchase and agreed at checkout; shown on one way in of three falls short

**Answer.** For a reservation disputed as *credit not processed*, Stripe asks for the policy as the customer saw it,
how and where it was shown *before the purchase*, and for Visa 13.7 "proof that the customer agreed to them at
checkout or signup". A rescuer who joined through a Seats to fill row or the rescue's details never saw it at that
purchase; the club could cite only sign-up terms, if they carry the rule. The issuer decides.

- **[DOCS]** Offline services, "such as event tickets and reservations, where evidence of a cancellation policy can be
  material": the policy "as provided to the customer" (`cancellation_policy`, `refund_policy`); "how and where you
  provided the applicable policy to your customer prior to purchase" (`cancellation_policy_disclosure`,
  `refund_policy_disclosure`); why no refund is due (`cancellation_rebuttal`, `refund_refusal_explanation`). Prevent
  it with a policy "explicitly disclosed to the customer prior to purchase".
  [Dispute categories](https://docs.stripe.com/disputes/categories?locale=en-US) — 2026-10-20
- **[DOCS]** Visa 13.7: "Provide a copy of your refund or cancellation terms and proof that the customer agreed to them
  at checkout or signup." [Reason codes](https://docs.stripe.com/disputes/reason-codes-defense-requirements?locale=en-US);
  "provide proof that your customer agreed to and understood your terms of service at checkout … a clean screenshot"
  ([Best practices](https://docs.stripe.com/disputes/best-practices)); "a checkbox … that only contains a link, the
  issuer might reject … There must be reasonable evidence that you presented your customer with a full copy of your
  policies prior to their purchase" ([Preventing fraud](https://docs.stripe.com/disputes/prevention/best-practices?locale=en-US)) — 2026-10-20
- Carried: the club answers its own disputes, and a share reaches it with no customer and no 3-D Secure
  ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#on-a-direct-charge-the-dispute-is-the-clubs-its-balance-its-fee-its-answer),
  [`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#what-a-share-carries-into-a-dispute-no-customer-no-3-d-secure-the-clubs-name)).
- **[ABSENT]** Whether a policy shown on one way in of three, agreed only through sign-up terms, satisfies
  `cancellation_policy_disclosure`. "The cardholder's bank, not Stripe, decides." Nothing of the policy goes to Stripe
  with the payment (the gap's premise), so the club builds the evidence itself. For Stripe's disputes team.
