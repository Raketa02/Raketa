# Stripe gaps, round 06 — REQUEST and CLUBBOOK

Sixteen Stripe gaps from the REQUEST and CLUBBOOK rounds (R-REQUEST-57 to -61; R-CLUBBOOK-14, -20, -27,
-35, -44), answered on 2026-10-20 against the code at `9ab0ea5b`.

- **Sources.** The Stripe MCP servers were disconnected. Stripe's own pages were read with a web fetch on
  docs.stripe.com (English, `?locale=en-US`, unless a quote is marked *(Spanish rendering)*),
  support.stripe.com and stripe.com.
- **The sandbox** was read through the Stripe SDK in the copy (stripe-python 15.6.1), with list and
  retrieve calls only. Nothing was created, updated or deleted. The accounts read were the platform
  `acct_1US89K5y1DB8chHb` and the test club `acct_1US95f5y1DMwE3zY`.
- **Facts already in the folder** are cited by anchor, not repeated.

| # | Rule | Gap | Result |
|---|---|---|---|
| 1 | R-REQUEST-61 (+ R-CLUBBOOK-20, R-CLUBMONEY-2) | Does a reversal give the fee back? | **[ABSENT]**: Stripe's two sentences disagree |
| 2 | R-REQUEST-61 | Refund minutes after capture, nothing available | Answered by Stripe's words (`pending`); the sandbox nets it |
| 3 | R-REQUEST-59 | Stop a club pressing Capture or Cancel | Answered: no published control. Support's confirmation is [ABSENT] |
| 4 | R-REQUEST-58, -59 | Does Stripe email the club about uncaptured, cancelled or failed payments? | Not in any published list. The full list is [ABSENT] |
| 5 | R-REQUEST-57 | What a club's Radar block returns | Answered: `blocked` / `not_sent_to_network` / `generic_decline` |
| 6 | R-REQUEST-57 | A club whose card payments are inactive or paused | Partly: new charges are blocked. Clone, cancel and refund are [ABSENT] |
| 7 | R-REQUEST-60 | A full-share check let go at once | **[ABSENT]**: Visa's global notice asks for a zero-amount check |
| 8 | R-REQUEST-60 | A live clone's Visa window | **[ABSENT]**. Polish test cards also measured at 7 days |
| 9 | R-CLUBBOOK-14 | Cancel or refund once charges or payouts are disabled | **[ABSENT]** |
| 10 | R-CLUBBOOK-20 | A reversal and its fee | **[ABSENT]**, as in 1 |
| 11 | R-CLUBBOOK-20 | Fee on a Polish card | Answered: 1,60 zł measured |
| 12 | R-CLUBBOOK-44 | Refund before the money is available | Answered by Stripe's words, as in 2 |
| 13 | R-CLUBBOOK-44 | How long a pending refund waits before it fails | Answered: 45 days |
| 14 | R-CLUBBOOK-27 | Does a Dashboard press reach Rakieta, and can Rakieta tell it apart? | Answered: it reaches Rakieta, and only the `rakieta-` key tells it apart. The press itself is [ABSENT] |
| 15 | R-CLUBBOOK-20 | `cancellation_reason` on a lapsed hold | **[ABSENT]** until 26 Oct. Stripe's own cancel reads null |
| 16 | R-CLUBBOOK-35 | A weather-stopped game refused a refund, then disputed | Answered: the evidence. The bank decides |

---

### 1 · R-REQUEST-61 (also R-CLUBBOOK-20, R-CLUBMONEY-2) · Whether a reversal gives back the fee taken at capture

**The question.** Bonarka Arena cancels a game soon after Rakieta took four shares of 40,00 zł. Each share
cost the club 1,60 zł in Stripe's fee. Does a refund processed as a *reversal* give those 1,60 zł back?

- **[DOCS]** On the same page, two sentences point opposite ways:
  - the glossary tooltip on "reversal": "A reversal is the cancellation of a transaction. **Stripe doesn't
    withhold any fees for payment reversals**";
  - the page's opening: "Stripe's processing fees from the original transaction **aren't returned**."

  The page also says: "IC+ users might see a difference in cost between reversals and refunds because
  reversals usually incur lower network fees." A reversal is read as `destination_details[card][type] =
  'reversal'`.
  [Refund and cancel payments](https://docs.stripe.com/refunds?locale=en-US) — 2026-10-20
- **[DOCS]** Support says "For all refunds, payment processing, Connect, and currency conversion fees from the
  original charge are not returned" and "Stripe doesn't return our fees when a payment is refunded". It does
  not mention reversals.
  [Understanding fees for refunded payments](https://support.stripe.com/questions/understanding-fees-for-refunded-payments)
  — 2026-10-20 (undated page)
- **[DOCS]** Support's statuses page gives this about a reversal, and nothing on fees:
  - "Reversed: The refund has been initiated as a reversal."
  - "The original payment will not show up on your customer's bank statement."
  - "The status is usually accompanied by a System Trace Audit Number (STAN) on the Dashboard payment page."

  [Understanding refund statuses](https://support.stripe.com/questions/understanding-refund-statuses) — 2026-10-20
- **[DOCS]** The balance-transaction types have no type for a reversal or for a fee given back:
  - a card refund is `refund`: "Created when a credit card charge refund is initiated";
  - `payment_reversal` is "Created when a debit/failure related to a payment is detected from a banking
    partner", which is not a refund;
  - "In the past, Connect platform fee refunds were represented as adjustments."

  [Balance transaction types](https://docs.stripe.com/reports/balance-transaction-types?locale=en-US) — 2026-10-20
- **[MEASURED]** The sandbox makes no reversals. All 34 refunds on the test club read
  `destination_details.card.type: refund`: 30 `succeeded` and 4 `failed`. Read via the SDK in the copy, test
  club, 2026-10-20. Carried from earlier rounds:
  - the refund's balance transaction carries `fee 0`
    ([`stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once));
  - no test card produces a reversal
    ([`stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line)).
- **[ABSENT]** On a direct charge, does "doesn't withhold any fees for payment reversals" return the 1,60 zł
  already on the capture's balance transaction? If it does, it is unknown whether that shows as a negative
  fee on the refund's balance transaction, as a separate credit, or not at all. It may instead mean only that
  no refund fee is added.
  - Searched on 2026-10-20: the refunds page (English and Spanish), its glossary tooltip, the three support
    pages above, the balance-transaction types, and a web search for Stripe's reversal fee.
  - Earlier searches: [`gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a-partial-reversal`](gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a-partial-reversal)
    (2026-10-08).
  - This is a question for Stripe support.
- *Reading:* the club is on Stripe's standard (blended) price, so the IC+ difference in network fees doesn't
  reach it (see §11). Only the balance transaction of a live reversal would show the truth.

### 2 · R-REQUEST-61 · A full card refund minutes after capture, with nothing available: Stripe says it waits, the sandbox nets it

- **[DOCS]** "Refunds use your available Stripe balance (not including pending amounts). If your available
  balance doesn't cover the amount of the refund, **Stripe holds the refund as pending for card transactions**
  (refunds for other payment method types fail) until your Stripe balance becomes sufficient."
  [Refund and cancel payments](https://docs.stripe.com/refunds?locale=en-US) — 2026-10-20. The same rule for
  direct charges is carried in
  [`stripe-connect.md#refunds-and-disputed-money-come-out-of-the-clubs-balance-a-short-refund-waits`](stripe-connect.md#refunds-and-disputed-money-come-out-of-the-clubs-balance-a-short-refund-waits).
- **[DOCS]** Support's reasons for a pending refund:
  - "Our financial partner needs to finish processing the refund."
  - "The refunding payment has not been settled."
  - "Your Stripe account has a negative balance that you need to fix".

  It adds: "Normally, your pending refunds are automatically released when future payments are processed and
  offset your negative balance."
  [Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund) — 2026-10-20
  (undated). The statuses page: "Some refunds are pending because the refunding payment is still processing
  and has not been settled."
  [Understanding refund statuses](https://support.stripe.com/questions/understanding-refund-statuses) — 2026-10-20
- **[DOCS]** Pending and available money:
  - "Funds in the pending state represent incoming transactions that haven't settled into your balance. For
    example, when a customer makes a card payment, the charge amount (minus Stripe's fee) appears in your
    pending balance until settlement."
  - Available funds: "You can use these funds for payouts to bank accounts, refunds, transfers, or any other
    debit transaction."
  - Poland: "7 calendar days" for the first payout, then "3 business days".

  [Balances and settlement time](https://docs.stripe.com/payments/balances?locale=en-US) — 2026-10-20
- **[MEASURED]** The test club's balance reads available 0,00 zł and pending 407,16 zł.
  - None of its 34 refunds is `pending`, and none carries a `pending_reason`.
  - 30 are `succeeded` and 4 are `failed` with `expired_or_canceled_card` (for example
    `re_3USPJm5y1DMwE3zY1S3GJVRF`).
  - So every sandbox refund was netted against pending money at once.

  Read via the SDK in the copy, test club, 2026-10-20.
- **[ABSENT]** Live confirmation is missing on two points:
  - whether a Polish club's card refund made with 0,00 zł available waits as `pending`, as Stripe writes, or
    is netted as on the sandbox;
  - whether a refund processed as a reversal (within about two hours of the capture) needs any available
    money at all.

  Searched: refunds, balances, connect/account-balances, and the three support pages above — 2026-10-20.
  This is a question for Stripe support.
- *Reading:* Stripe's documented word outranks the sandbox.
  - Live, a refund in a new club's first week, before any money is available, should wait as `pending` until
    money arrives, unless it goes through as a reversal.
  - Support's "has not been settled" is not defined for card payments. It may be the `charge_pending` reason
    ([`stripe-refunds-and-disputes.md#five-statuses-and-why-a-refund-is-pending`](stripe-refunds-and-disputes.md#five-statuses-and-why-a-refund-is-pending)).

### 3 · R-REQUEST-59 · Stripe publishes no way for a platform to stop a full-Dashboard club pressing Capture or Cancel

- **[DOCS]** The platform controls over a full-Dashboard account are:
  - third-party extensions;
  - payout timing;
  - consolidated reporting;
  - co-branding;
  - Terminal hardware;
  - "Remove account".

  None touches a payment.
  [Platform controls in the Stripe Dashboard](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts)
  — 2026-10-20
- **[DOCS]** Support lists what a platform can do: "creating payouts, updating payout schedules, and adding
  platform branding". For the account holder: "There are no changes to your Stripe login or access."
  [Platform controls for connected accounts](https://support.stripe.com/questions/platform-controls-for-connected-accounts)
  — 2026-10-20 (undated)
- **[DOCS]** The club's own Approvals can require or block only these actions:
  - "Bank account is added, updated or deleted";
  - "Admin is invited to account";
  - "Payment intent is created";
  - "Refund is created";
  - "Subscription is created or canceled";
  - "Credit note is created";
  - "Customer balance transaction is created".

  Capturing or cancelling a payment is not among them. "By default, only team members with the Administrator
  role can create or edit approval rules", so these are the club's settings, not Rakieta's.
  [Set up two-party approvals](https://docs.stripe.com/account/approvals?locale=en-US) — 2026-10-20
- Carried: the full Dashboard gives "unrestricted access to Stripe's full feature set", and the Dashboard type
  is permanent. The **Capture** and **Cancel** buttons are carried in
  [`stripe-holds-and-capture.md#a-club-on-the-full-dashboard-can-capture-or-cancel-a-held-share-itself`](stripe-holds-and-capture.md#a-club-on-the-full-dashboard-can-capture-or-cancel-a-held-share-itself).
- **[ABSENT]** A statement from Stripe that no such control exists, or a control granted on request.
  Searched: the pages above — 2026-10-20. This is a question for Stripe support.
- **Answer:** no published control. Rakieta can only hear the press (§14) and react to it.

### 4 · R-REQUEST-58, R-REQUEST-59 · Stripe's published emails to a club leave out uncaptured, cancelled and failed payments

- **[DOCS]** "Stripe sends email notifications to you when any of the following events occur":
  - "A successful payment is received."
  - "An application fee is collected from a connected account."
  - "A payment is disputed by a customer."
  - "A payment is marked as elevated risk by Stripe or a custom Stripe Radar rule."
  - "You're mentioned in a note."
  - "A customer sends an incorrect amount to pay their invoice."
  - "A webhook delivery fails."

  The page continues: "**For a full list of notification events, go to your Communication preferences under
  Profile.**" Settings are per user: "If your team members also want to receive notifications, they must
  customize their own settings."
  [Start a team — Receive email notifications](https://docs.stripe.com/get-started/account/teams?locale=en-US)
  — 2026-10-20. This is the same list as on 2026-10-08
  ([`gaps-CLUBMONEY.md#each-dashboard-user-picks-their-own-notices-and-payouts-are-not-in-the-published-list`](gaps-CLUBMONEY.md#each-dashboard-user-picks-their-own-notices-and-payouts-are-not-in-the-published-list)).
- **[DOCS]** Support's list is a successful payment, a dispute, elevated risk, an application fee,
  connected-account risk requirements and a mention. Failed, cancelled and uncaptured payments, refunds and
  payouts are not on it.
  [Set up account email notifications](https://support.stripe.com/questions/set-up-account-email-notifications)
  — 2026-10-20 (undated)
- **[DOCS]** Stripe Workflows can do it instead:
  - "Use Stripe Workflows to automate sending emails to your team."
  - Workflows "Start workflows automatically when Stripe events occur, such as a payment succeeding".
  - "Workflows support Connect platforms, trigger workflows on connected account events and run actions on
    connected account resources."

  [Teams](https://docs.stripe.com/get-started/account/teams?locale=en-US),
  [Workflows](https://docs.stripe.com/workflows?locale=en-US) — 2026-10-20
- Carried: "By default, Stripe doesn't email customers in sandboxes"
  ([`stripe-testing.md#stripe-emails-nobody-in-a-sandbox`](stripe-testing.md#stripe-emails-nobody-in-a-sandbox)).
- **[ABSENT]** Two things are unknown:
  - whether the full list under **Communication preferences** has an email for an uncaptured payment about to
    lapse, a cancelled payment or a failed payment;
  - whether any of these reaches a club user by default.

  The list is visible only when signed in as a user of the club's account, and no session here holds one.
  Searched: the teams page, support's notifications page, and a web search for Stripe's email about expiring
  uncaptured payments — 2026-10-20.
- **Answer:** no published Stripe email covers these moments, so the desk can't count on Stripe to tell it.
  A club could build its own email with Workflows, and Rakieta could too, on the club's events.

### 5 · R-REQUEST-57 · A club's own Radar rule blocking the fill's hold: `blocked`, never sent to the bank, read as `generic_decline`

- **[DOCS]** A payment fails in one of three ways: an issuer decline, a blocked payment, or an invalid API
  call.
  - "When Stripe blocks a payment, it doesn't obtain authorization from the card issuer" *(Spanish rendering,
    translated)*.
  - A block's published outcome is `"network_status": "not_sent_to_network"`, `"reason":
    "highest_risk_level"`, `"advice_code": "do_not_try_again"`, `"seller_message": "Stripe blocked this charge
    as too risky."` and `"type": "blocked"`.
  - An issuer's decline reads `"network_status": "declined_by_network"` and `"type": "issuer_declined"`.

  [Declines](https://docs.stripe.com/declines) — 2026-10-20
- **[DOCS]** The charge's outcome fields:
  - `outcome.reason`: "Charges blocked by Radar's default block rule have the value `highest_risk_level` …
    **Charges authorized, blocked, or placed in review by custom rules have the value `rule`**."
  - `outcome.rule`: "The ID of the Radar rule that matched the payment, if applicable."
  - `outcome.type`: "`authorized`, `manual_review`, `issuer_declined`, `blocked`, and `invalid`".
  - `network_status` also has `reversed_after_approval`: "the payment was blocked by Stripe after bank
    authorization".

  [Charge object — outcome](https://docs.stripe.com/api/charges/object?query=outcome) — 2026-10-20
- **[DOCS]** The decline codes involved:
  - `generic_decline`: "The card was declined for an unknown reason **or Stripe Radar or Adaptive Acceptance
    blocked the payment**."
  - `fraudulent`: "declined because Stripe suspects that it's fraudulent … present it in the same manner as
    `generic_decline`."
  - `merchant_blacklist`: "matches a value on the Stripe user's block list".

  [Decline codes](https://docs.stripe.com/declines/codes?locale=en-US) — 2026-10-20
- Carried: on a direct charge only the club's Radar runs
  ([`stripe-security.md#on-a-direct-charge-only-the-clubs-radar-runs`](stripe-security.md#on-a-direct-charge-only-the-clubs-radar-runs)).
  Radar's block test card is carried in
  [`stripe-testing.md#radars-test-cards`](stripe-testing.md#radars-test-cards), with Stripe's note that "The
  response is the same as what you get when a charge fails".
- **[MEASURED]** The sandbox holds no blocked charge. The test club's 123 charges read `authorized` 96,
  `issuer_declined` 27 and `blocked` 0. Twenty-two of the issuer declines read `generic_decline`, with
  `network_decline_code: 01` and `network_status: declined_by_network` (for example
  `ch_3USSg75y1DMwE3zY0QNbuJra`). Read via the SDK in the copy, test club, 2026-10-20. So the bank's plain
  refusal and a Radar block share a decline code.
- *Code:* from a refusal the adapter keeps only `decline_code or code`, and it never reads `outcome`
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:519-540`, `:618-635`).
- **[DOCS]** A related control: a club's Approval rule on "Payment intent is created", set to **Block**,
  rejects the action "outright". Its error is `action_blocked`: "An approval rule on this account blocks this
  action. To allow it, modify or remove the rule in the Dashboard."
  [Approvals](https://docs.stripe.com/account/approvals?locale=en-US),
  [Error codes](https://docs.stripe.com/error-codes?locale=en-US) — 2026-10-20
- **[ABSENT]** Whether a club's Approval rule applies to the platform's requests on the club's account.
- **Answer:** a Radar block reads, on the charge, `outcome.type: blocked`,
  `network_status: not_sent_to_network`, and `outcome.reason: rule` with `outcome.rule` set to the club's rule
  ID. The decline code is `generic_decline`; `fraudulent` names Stripe's own suspicion. Only the charge's
  outcome tells a block from the bank's refusal. This was not measured: it needs 4100 0000 0000 0019 or a
  rule on the club.

### 6 · R-REQUEST-57 · A club whose card payments Stripe made inactive or paused

- **[DOCS]** "Pausing payments blocks creation of any charges. It also makes the transfer, card_payments and
  other payment methods capabilities `inactive`."
  - "**we don't enforce payment or payout pauses in a sandbox.** Pausing payments in a sandbox deactivates
    the corresponding capabilities on the account, but doesn't block the creation of charges."
  - The page applies to platforms "liable for negative balances", and "This workflow isn't available when
    using Accounts v2".
  - The page says nothing on capturing, cancelling or refunding.

  [Pause payments and payouts on connected accounts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts?locale=en-US)
  — 2026-10-20
- **[DOCS]** `capability_not_active`: "Your account is missing the active capabilities required to access this
  endpoint. Check the capabilities array in the error response for details".
  [Error codes](https://docs.stripe.com/error-codes?locale=en-US) — 2026-10-20
- **[POLICY]** A third party, not Stripe: a billing platform quotes Stripe's refusal as "This Connect account
  cannot currently make live charges." and "The `requirements.disabled_reason` property on the account will
  provide information". It gives no error code.
  [Chargebee](https://www.chargebee.com/docs/payments/2.0/kb/billing/stripe-error-this-connect-account-cannot-currently-make-live-charges)
  — 2026-10-20 (undated)
- Carried:
  - either capability going inactive disables both
    ([`stripe-connect.md#card-payments-need-transfers-too-either-inactive-stops-both`](stripe-connect.md#card-payments-need-transfers-too-either-inactive-stops-both));
  - Stripe may pause a club it is liable for
    ([`stripe-connect.md#stripe-may-pause-a-clubs-charges-or-payouts-hold-a-reserve-or-close-it`](stripe-connect.md#stripe-may-pause-a-clubs-charges-or-payouts-hold-a-reserve-or-close-it)).
- **[MEASURED]** No payment exists on a club whose card payments are inactive. `acct_1USELi5y1DCSZFum`
  (`card_payments` and `transfers` inactive, carried) holds no PaymentIntent. Read via the SDK in the copy,
  2026-10-20.
- **[ABSENT]** Three questions stay open:
  1. what cloning the player's card onto such a club answers;
  2. which error and code the off-session hold gets, whether `capability_not_active`, the "cannot currently
     make live charges" refusal or another;
  3. whether a payment wait's kept holds can still be cancelled, and taken shares refunded.

  Searched: the pausing page, error codes, refunds, and a web search; earlier, account capabilities and
  handling-api-verification
  ([`stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled))
  — 2026-10-20. This can't be tried on a sandbox, which doesn't enforce pauses. It is a question for Stripe
  support.
- *Code:* the adapter treats `stripe.PermissionError` as an outage and retries it (`stripe_payments.py:71-80`).
  Which error class Stripe raises here is not documented.

### 7 · R-REQUEST-60 · A full-share authorisation let go at once, only to check the card

- **[DOCS]** Visa, Article AI09481, 7 November 2019, scope "**Global** | Acquirers, Issuers, Processors":
  - "Account verification messages are authorizations with a zero amount used by merchants to check the
    validity of a primary account number with issuers."
  - "merchants and acquirers are incorrectly using authorizations with low values instead of zero-amount
    account verifications."
  - Acquirers must "Ensure that their merchants use account verification instead of authorizations for
    erroneous amounts when validating cardholder accounts."

  [Visa: Proper Account Verification Message Processing Reminders](https://bz.review.visa.com/content/dam/VCOM/global/support-legal/documents/account-verification-vbn.pdf)
  — 2026-10-20, text taken from the PDF. The wording is carried from 2026-10-11; this round adds the scope,
  which is Global, so the notice covers Poland.
- Carried: Stripe says "Card networks may also restrict 1 USD authorizations you don't intend to capture"
  ([`stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card`](stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card)).
- **[ABSENT]** Whether a full-share authorisation that is let go at once counts, for Visa or Mastercard in
  Europe, as an "authorization for an erroneous amount when validating cardholder accounts", and whether
  either network charges the acquirer for it.
  - The notices found target low-value or nominal authorisations, not the real price.
  - A Mastercard Europe rule on checking cards was not found. The web search turned up only processor notices
    for Canada and Asia-Pacific about a fee on reversed authorisations of one currency unit or less.
  - Searched: Stripe's hold page, Visa AI09481, and web searches on Visa account verification and Mastercard's
    Account Status Inquiry — 2026-10-20.
  - This is a question for Stripe support, as the acquirer.
- *Reading:* the share is the real price, not an "erroneous amount", but it is authorised with no intent to
  capture. Visa's notice doesn't decide that case.

### 8 · R-REQUEST-60 · The Visa window a live off-session hold on a clone gets

- Carried: Stripe classes a payment as CIT or MIT by "signals of cardholder participation, not solely on API
  parameters like `off_session` … might still be classified as a CIT if a CVC is present". `capture_before` is
  "the most reliable and accurate way" to read the window
  ([`stripe-holds-and-capture.md#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session`](stripe-holds-and-capture.md#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session)).
- **[DOCS]** The CIT and MIT page names no field that says how a payment was classed, only `capture_before`.
  [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-US) — 2026-10-20
- **[MEASURED]** Holds on clones of Polish test Visa cards also get exactly 7 days:
  - `ch_3USPFA5y1DMwE3zY0VSNB1u9` (40,00 zł, Visa PL credit •••• 0005, `cvc_check: pass`), created
    2026-10-19 22:41:24 UTC, `capture_before` 2026-10-26 22:41:24 UTC;
  - `ch_3USPCF5y1DMwE3zY1HE29XAk`, created 22:38:23 UTC, `capture_before` 26 October 22:38:23 UTC.

  This matches every 4242 hold. Read via the SDK in the copy, test club, 2026-10-20.
- **[ABSENT]** Live, does the clone of a card saved weeks earlier carry a CVC signal, and so get 7 days rather
  than 4 days 18 hours? Not documented. On the sandbox every clone passes the CVC check, so the 4 days
  18 hours window can't be produced there. This is a question for Stripe support; live, the answer is the
  charge's `capture_before`.

### 9 · R-CLUBBOOK-14 · Cancelling a hold or refunding after Stripe disables a club's charges or payouts

- As in §6, nothing Stripe publishes covers capturing, cancelling or refunding on an account whose charges
  are disabled or paused. Pausing "blocks creation of any charges", and the sandbox does not enforce pauses.
- **[DOCS]** The nearest statement is about a *negative* balance, not disabled charges: "Your business won't
  be able to send refunds to customers until the issue is resolved."
  [Support: Fix the negative balance on your account](https://support.stripe.com/questions/pending-refunds-due-to-insufficient-stripe-balance)
  — 2026-10-20 (undated)
- Carried: payouts stop first, then charges
  ([`stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled),
  [`gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried`](gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried)).
- **[ABSENT]** An Accounts v2 club, Stripe-liable with the full Dashboard, has charges or payouts disabled
  for past-due requirements. Can it still cancel a held PaymentIntent, and refund a captured one?
  Searched on 2026-10-20: pausing, error codes, refunds, the support pages above, and a web search. Searched
  earlier on 2026-10-08 and 2026-10-19. The shared test club can't be pushed into that state. This is a
  question for Stripe support.

### 10 · R-CLUBBOOK-20 · A full refund minutes to two hours after a Polish club's capture: reversal, and its fee

- See §1: no published answer on whether the fee comes back, and **[ABSENT]** there.
- The timing, carried: "usually happens within 2 hours of the payment capture"
  ([`stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line)).
- The same unknown decides R-CLUBBOOK-41's live cost. It also decides whether R-CLUBBOOK-43's "the card fees
  are not returned" can be untrue for a reversal.

### 11 · R-CLUBBOOK-20 · The fee on a Polish card: 1,60 zł on a 40,00 zł share, measured

- **[MEASURED]** Two shares paid with the Polish test Visa 4000 0061 6000 0005 (credit, issued in PL):
  - `ch_3USPFA5y1DMwE3zY0VSNB1u9`: balance transaction `txn_3USPFA5y1DMwE3zY0nTUGB4z`, amount 40,00 zł,
    `fee` 1,60 zł (`stripe_fee`, "Stripe processing fees"), `net` 38,40 zł, `pending`, available on
    2026-10-26 00:00 UTC;
  - `ch_3USPCF5y1DMwE3zY1HE29XAk`: balance transaction `txn_3USPCF5y1DMwE3zY1pslz86F`, the same figures.
  - Each share was later refunded 38,40 zł.

  Read via the SDK in the copy, test club, 2026-10-20.
- **[PRICE]** Stripe's prices in Poland: "Standard EEA cards: 1.5% + 1.00zł"; "Premium EEA cards: 1.9% +
  1.00zł"; "UK cards: 2.5% + 1.00zł"; "International cards: 3.25% + 1.00zł", plus "2% if currency conversion
  is required". [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — 2026-10-20
- **Answer, in złoty:**
  - A 40,00 zł share costs 1,60 zł on a standard Polish card (measured) and 1,76 zł on a premium one.
  - Stripe's US test card 4242 costs 2,30 zł, as measured earlier.
  - Four standard Polish shares cost the club 6,40 zł, and four premium ones 7,04 zł.
  - The rule's "about 6,40 zł" holds for standard consumer cards and now rests on Stripe's figure.

### 12 · R-CLUBBOOK-44 · A refund on the day its share was taken, while the money is still pending

- See §2. Stripe's words: with no available money, a card refund waits as `pending`. The sandbox nets it
  against pending money at once. Live confirmation is **[ABSENT]**.
- **[DOCS]** In Poland a club's first money is available after "7 calendar days" and later money after
  "3 business days" ([Balances and settlement time](https://docs.stripe.com/payments/balances?locale=en-US),
  2026-10-20). Measured on the test club: all 407,16 zł is pending, available from 26 October.
- *Reading:* by Stripe's words, a pending refund is the everyday case in a club's first week. After that, it
  happens whenever the club's available balance is smaller than the refund.

### 13 · R-CLUBBOOK-44 · A refund pending for want of funds fails after 45 days

- **[DOCS]** "**Stripe automatically fails a pending refund after 45 days.**"
  [Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund) — 2026-10-20
  (undated support page). The failure reason is `insufficient_funds`: "Refund is pending due to insufficient
  funds and has crossed the pending refund expiration window."
  [Refund and cancel payments](https://docs.stripe.com/refunds?locale=en-US) — 2026-10-20
- **[DOCS]** "Normally, your pending refunds are automatically released when future payments are processed
  and offset your negative balance." Same support page, 2026-10-20.
- Carried:
  - a dispute filed while the refund is pending makes it fail with `charge_for_pending_refund_disputed`
    ([`stripe-refunds-and-disputes.md#while-a-dispute-is-open-the-share-cant-be-refunded-and-a-refund-still-pending-fails`](stripe-refunds-and-disputes.md#while-a-dispute-is-open-the-share-cant-be-refunded-and-a-refund-still-pending-fails));
  - the code drops every refund event (D6 in [`stripe-sandbox.md#differences`](stripe-sandbox.md#differences)).
- *Reading:* a club whose available balance stays short for 45 days has the refund fail. `refund.failed`
  reaches the Connect endpoint and is dropped, so the player gets nothing back and nobody is told.

### 14 · R-CLUBBOOK-27 · A Capture or Cancel pressed in the club's own Dashboard reaches Rakieta, and only the key tells it apart

- **[DOCS]** The Connect scope covers "Events triggered by resources that exist in connected accounts … Direct
  charges for customers of your connected accounts"; "Each event for a connected account contains a
  top-level `account` property". `payment_intent.succeeded` is "Available for all payments, including
  destination and direct charges." The page makes no exception for who acted.
  [Connect webhooks](https://docs.stripe.com/connect/webhooks?locale=en-US) — 2026-10-20
- **[DOCS]** The event's `request` is "Information on the API request that triggers the event."
  - `request.id`: "ID of the API request that caused the event. **If null, the event was automatic** (e.g.,
    Stripe's automatic subscription handling). Request logs are available in the dashboard, but currently not
    in the API."
  - `request.idempotency_key`: "The idempotency key transmitted during the request, if any."
  - No field names the Dashboard as the source.

  [Event object](https://docs.stripe.com/api/events/object?query=request) — 2026-10-20
- *Code:* every key Rakieta's server sends begins with `rakieta-`:
  - the take, `rakieta-capture-{charge_id}`;
  - the let-go, `rakieta-cancel-seat-{charge_id}`;
  - the card check, `rakieta-cancel-check-{charge_id}`;
  - the refund, `rakieta-refund-{charge_id}`
    (`backend/app/modules/payments/application/handlers/settle_seat_charges.py:54-70`);
  - the hold, `rakieta-{kind}-…` (`backend/app/modules/payments/application/seat_charges.py:169`).
- **[MEASURED]** The test club holds 228 events of the six money kinds (`payment_intent.canceled` and
  `.succeeded`, `charge.captured`, `charge.refunded`, `refund.created`, `charge.expired`). All 228 carry a
  request ID, and all but one carry a `rakieta-…` key.
  - The exception is `evt_3USPKC5y1DMwE3zY0xQEMKTV` (`payment_intent.canceled`, payment
    `pi_3USPKC5y1DMwE3zY00HIKsMU`). It carries `req_ZW2hNCf2S7SLgf` with the key
    `ff2e7700-48da-b31a-018a-fcc6250d53b6`.
  - Stripe itself cancelled that payment at the tenth confirmation in a FILL Breaker test, and the event names
    that confirmation's request.

  Read via the SDK in the copy, test club, 2026-10-20.
- **[ABSENT]** The request ID and key a **Dashboard** press carries. The press was never made on the sandbox,
  and Stripe documents no Dashboard marker. Searched: the Event object, Connect webhooks, and the refunds
  page's "Cancel a payment" — 2026-10-20. *What would answer it:* press Capture or Cancel on an uncaptured
  share in the test club's Dashboard, then read that event's `request`. Three holds remain to press (§15).
- **Answer:** the press reaches Rakieta's Connect endpoint as `payment_intent.succeeded` or `.canceled`, as
  documented. Rakieta can tell its own server's act from everyone else's by the `rakieta-` key. Nothing
  documented tells the club's press from the player's phone confirming, or from Stripe's own automatic
  cancel.

### 15 · R-CLUBBOOK-20 · The `cancellation_reason` on a lapsed hold is still unread, and null is not only Rakieta's

- **[DOCS]** `cancellation_reason`: "Reason for cancellation of this PaymentIntent, either user-provided
  (`duplicate`, `fraudulent`, `requested_by_customer`, or `abandoned`) or **generated by Stripe internally
  (`failed_invoice`, `void_invoice`, `automatic`, or `expired`)**." No value is described further.
  [PaymentIntent object](https://docs.stripe.com/api/payment_intents/object) — 2026-10-20
- **[DOCS]** "PaymentIntents might also automatically transition to `canceled` if they're confirmed too many
  times." [How Payment Intents and Setup Intents work](https://docs.stripe.com/payments/paymentintents/lifecycle?locale=en-US)
  — 2026-10-20
- **[MEASURED]** Stripe's own automatic cancel left no reason. `pi_3USPKC5y1DMwE3zY00HIKsMU` (40,00 zł) was
  cancelled by Stripe at 2026-10-19 22:46:49 UTC, at the tenth confirmation. It reads
  `cancellation_reason: null`, and its charge `ch_3USPKC5y1DMwE3zY0F5mM0Z5` reads `failed`. All 48 cancelled
  payments on the test club read null. Read via the SDK in the copy, test club, 2026-10-20.
- **[MEASURED]** Three holds wait to lapse, all `requires_capture` today:
  - `pi_3USA7i5y1DMwE3zY0Nemxwtn`, `capture_before` 2026-10-26 06:32:43 UTC;
  - `pi_3USELx5y1DMwE3zY14aUf4wv`, 11:03:41 UTC;
  - `pi_3USHgd5y1DMwE3zY0vozapC7`, 14:37:15 UTC.

  Each is 40,00 zł on 4242. Read via the SDK in the copy, test club, 2026-10-20.
- **[ABSENT]** Whether a lapsed card hold reads `automatic`, `expired` or null. It becomes readable after
  2026-10-26 06:32:43 UTC on `pi_3USA7i5y1DMwE3zY0Nemxwtn`. Searched: the API reference, the hold page, the
  lifecycle page, and a web search — 2026-10-20. Earlier:
  [`stripe-holds-and-capture.md#which-reason-and-which-events-an-expired-hold-carries-undocumented-readable-on-the-sandbox-after-26-october`](stripe-holds-and-capture.md#which-reason-and-which-events-an-expired-hold-carries-undocumented-readable-on-the-sandbox-after-26-october).
- *Reading:* the carried reading that null marks Rakieta's own let-go is weaker now. Stripe's automatic cancel
  after too many confirmations also reads null. A share the club cancels after Stripe refused its take is
  safer told apart by the event's key (§14) than by the reason.

### 16 · R-CLUBBOOK-35 · A game stopped by the weather minutes after it began, refused a refund, then disputed

- **[DOCS]** The *Credit not processed* category: "The customer claims they're entitled to a full or partial
  refund because they returned the purchased product or **didn't fully use it, or the transaction was
  otherwise canceled or not fully fulfilled**, but you haven't yet provided a refund or credit."
  - To overturn it, show one of: "You already issued the refund your customer is entitled to", "The customer
    isn't entitled to a refund", or that the customer withdrew the dispute.
  - The evidence Stripe lists for an offline service:
    - the cancellation or refund policy "as provided to the customer";
    - "how and where you provided the applicable policy to your customer prior to purchase";
    - "Your explanation for why the customer isn't entitled to a refund";
    - "Whether or not the customer attempted to resolve the issue with you prior to filing a dispute";
    - "If they partially used the service, or whether the dispute amount exceeds the value of the unused
      portion".
  - To prevent it: "Have a clear return or cancellation policy that's easy to find or explicitly disclosed to
    the customer prior to purchase."

  [Dispute categories](https://docs.stripe.com/disputes/categories?locale=en-US) — 2026-10-20. This extends
  [`stripe-refunds-and-disputes.md#the-evidence-a-booked-game-would-need-the-cancellation-policy-as-shown-and-that-it-was-played`](stripe-refunds-and-disputes.md#the-evidence-a-booked-game-would-need-the-cancellation-policy-as-shown-and-that-it-was-played).
- **[DOCS]** The reason codes:
  - Visa 13.7, "Canceled Merchandise or Services": "Cancellation policy: Provide a copy of your refund or
    cancellation terms and proof that the customer agreed to them at checkout or signup"; "Usage logs (for
    services or subscriptions)"; "The customer is obligated to proactively communicate the issue before filing
    a dispute."
  - Visa 13.1, services not received: "Proof of service completion: Provide appointment records, work logs, or
    check-in confirmations."
  - Mastercard 4860 covers "canceled services or orders where the cardholder expected a credit", with "Return
    or cancellation policy: Provide evidence that the cardholder didn't comply with return or cancellation
    requirements."
  - "**The cardholder's bank, not Stripe, decides the outcome of each dispute.**"

  [Dispute reason codes](https://docs.stripe.com/disputes/reason-codes-defense-requirements?locale=en-US) — 2026-10-20
- **[ABSENT]** A Stripe statement on a service stopped by the weather or by force majeure, or on whether such
  a dispute can be won. Searched: the categories page, the reason codes page, and (carried) responding and best
  practices — 2026-10-20. This is a question for Stripe's disputes team.
- *Reading:* to win, the club needs four things:
  - the policy text the player accepted before paying, and where it was shown;
  - proof that the game began, and for how many minutes;
  - that the player didn't write to the club first;
  - the amount against what was used.

  The share's payment carries none of these
  ([`stripe-refunds-and-disputes.md#what-a-share-carries-into-a-dispute-no-customer-no-3-d-secure-the-clubs-name`](stripe-refunds-and-disputes.md#what-a-share-carries-into-a-dispute-no-customer-no-3-d-secure-the-clubs-name)).
  If the bank files the stop as a service not received (Visa 13.1), the evidence asked for is the service
  completed, which a stopped game cannot show.
