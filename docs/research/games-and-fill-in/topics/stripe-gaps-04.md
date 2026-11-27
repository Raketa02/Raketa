# Stripe gaps, batch 04 — CLUBMONEY

Answers to sixteen `stripe:` gaps from the CLUBMONEY area of the payments pass on PRD #530, at the code's commit
`9ab0ea5b`. Every share is a direct charge on the club's own Accounts v2 account (merchant configuration, full
Dashboard, fees and losses on Stripe, Poland, złoty).

**Sources.**
- `[DOCS]` is docs.stripe.com (Markdown, `?locale=en-US` where given) or support.stripe.com, read 2026-10-20.
  Words that make something a requirement or a recommendation are quoted.
- `[MEASURED]` is "read via the SDK in the copy": a read-only probe through stripe-python 15.6.1 with the
  sandbox's platform key (`acct_1US89K5y1DB8chHb`, test mode). It sends a `Stripe-Account` header for the test
  club `acct_1US95f5y1DMwE3zY`. All reads were made on 2026-10-20 and nothing was created, updated or deleted.
  Measurements already in a breaker file are carried by name.
- `[ABSENT]` means looked for and not found, with where.
- *Reading* is this researcher's inference.

Checked first, so as not to answer twice: `stripe-payouts-and-balances.md`, `stripe-connect.md`,
`stripe-refunds-and-disputes.md`, `stripe-reliability.md`, `stripe-security.md`, `gaps-CLUBMONEY.md` and the
`breaker.md` of CLUBMONEY, PLATFORM and SECURITY. Each gap below adds only what those files lack, and carries the
rest by anchor.

---

### R-CLUBMONEY-14 · After the first payout: 3 business days or calendar-day `delay_days`, and risk keeping a new club at 7

**Answer, in part:**
- A Polish club's first money waits **7 calendar days**. This is measured, and it contradicts the support page's
  "7 business days".
- Stripe says later money waits 3 business days, from "all new payments after your first payout".
- On the sandbox the switch had **not** happened the day after the test club's first payout.
- Two things stay open: whether Poland's 3 days count as business or calendar days, and what risk keeps a club
  at 7.

- **[DOCS]** "Poland | 7 calendar days | 3 business days" (initial, default). "The initial settlement timing applies
  to your first payout, and the default settlement timing applies to subsequent payouts." "In some cases, risk
  criteria might prevent your account from changing to the default settlement timing." "If your Stripe account is
  in a country with a T+3 standard settlement timing and you use a manual payout schedule, your Stripe balance is
  available for payout within 3 business days of capturing a payment."
  [Receive payouts](https://docs.stripe.com/payouts?locale=en-US) — 2026-10-20
- **[DOCS]** On the same page, *Delay behavior per account country*: "Calendar day (Sunday - Saturday)" for "BR, CA,
  GI, HK, LI, MX, NO, SG, CH, GB, and supported EU countries". The section opens "As a platform, you can set
  `delay_days` on your connected accounts" (served in Spanish on the first fetch; this is the English text).
  [Receive payouts](https://docs.stripe.com/payouts?locale=en-US#delay-behavior-per-account-country) — 2026-10-20
- **[DOCS]** Both quotes are from [Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) — 2026-10-20:
  - "Stripe calculates the delay in business days or calendar days, depending on the connected accounts' country."
  - "For accounts where Stripe manages fraud and dispute liability (for example, Standard accounts), the default is
    the lowest permitted value for the account, determined by the connected account's country."
- **[DOCS]** The following are quoted from [Default payout speeds in Europe and Canada](https://support.stripe.com/questions/default-payout-speeds-in-europe-and-canada)
  — 2026-10-20 (undated; Poland not named):
  - "Stripe has a delay of 7 business days on your first payout in many European countries and Canada."
  - "After that, you'll automatically move to the default speed of your market. This is generally 3 business days."
  - "The default payout speed will apply to all new payments after your first payout."
  - "In some cases, risk criteria might prevent your account from changing to the default payout speed."
  - "Stripe tracks and separates funds acquired on your standard T+7 timing vs. those acquired on your new T+3
    timing."
- **[DOCS]** "There is a 7-day waiting period for connected accounts from the time of first charge to the first
  payout." [Delay for first payout for connected accounts](https://support.stripe.com/questions/delay-for-first-payout-for-connected-accounts) — 2026-10-20
- **[MEASURED]** The test club has 99 balance transactions, all created on Monday 2026-10-19. 97 of them read
  `available_on` 2026-10-26 00:00 UTC: charges, refunds, refund failures and dispute adjustments. The other two are
  the payout and one share made with a card that is available at once. Monday to Monday is 7 **calendar** days;
  7 business days would have been Wednesday 28 October.
- **[MEASURED]** The first payout and what came after it:
  - The club's first payout is `po_1USPGD5y1DMwE3zY2VJcHrmh`: 37,70 zł, manual, created 2026-10-19 22:42:29 UTC,
    `paid`, arriving 2026-10-21.
  - A share captured **after** it, `txn_3USPMX5y1DMwE3zY1wWtVvAF` (charge, 22:49:02 UTC), still reads
    `available_on` 2026-10-26 00:00 UTC.
  - On 2026-10-20 the account still reads `settings.payouts.schedule.delay_days: 7` (v1).
  - `GET /v1/balance_settings` likewise reads `payments.settlement_timing.delay_days: 7`, with `start_of_day`
    00:00 `Etc/UTC`.
- **[ABSENT]** Looked in `payouts`, `connect/manage-payout-schedule`, both support pages above and a support-site
  search — 2026-10-20. Not found:
  - whether Poland's default 3 days count as business days (the settlement table) or calendar days (the delay
    table for EU countries);
  - what decides that "risk criteria" keep a club at 7;
  - whether the sandbox ever switches, whether at the payout's arrival or not at all.

  Re-reading the test club's `delay_days`, and the `available_on` of a share captured after 2026-10-21, would show
  the sandbox's answer.
- *Reading:* in the worst case a new club's first week of shares waits 7 calendar days. For the money after that,
  plan on the longer reading, 3 business days (Friday's take on Wednesday), until it is measured.

### R-CLUBMONEY-14 · A minimum balance on a Stripe-liable, full-Dashboard club, set by the platform through Balance Settings

**Answer, in part:**
- Stripe documents per-account minimum balances as something a platform does through Balance Settings. Unlike the
  interval and the delay, this field carries no liability condition.
- The platform can read the test club's Balance Settings.
- Whether Stripe accepts the write on a Stripe-liable account was not tried, because it is a write.

- **[DOCS]** Quoted from [Minimum balances for automatic payouts](https://docs.stripe.com/payouts/minimum-balances-for-automatic-payouts) — 2026-10-20:
  - "As a platform … You can also programmatically configure minimum balances **per connected account** with the
    Balance Settings API."
  - "After you set a minimum balance for your connected accounts, their payouts differ from the amounts shown on
    their balance. **We recommend** you reach out to your customers before setting a minimum balance to explain the
    purpose and effects."
  - "Minimum balances work with all automatic payout schedules."
  - "Only use minimum balances to cover anticipated refunds, disputes, and fees."
  - On an account's own Dashboard: "Minimum Balances are only available when you have access to the Stripe
    Dashboard".
- **[DOCS]** `payments.payouts.minimum_balance_by_currency` is described as "The minimum balance amount to retain per
  currency after automatic payouts. Only funds that exceed these amounts are paid out." The other fields carry a
  condition this one does not:
  - `delay_days`: "You can edit this property on accounts where you own fraud and dispute liability".
  - `interval`: "Platforms that manage fraud and dispute liability, or have platform controls, can adjust the payout
    interval."

  [Update balance settings](https://docs.stripe.com/api/balance-settings/update?query=),
  [Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) — 2026-10-20
- **[MEASURED]** `GET /v1/balance_settings` on `acct_1US95f5y1DMwE3zY` with the platform key answers without a
  permission error. It reads:
  - `payments.payouts.minimum_balance_by_currency: null`;
  - `schedule.interval: manual`, `status: enabled`;
  - `debit_negative_balances: true`;
  - `settlement_timing.delay_days: 7`, with no `delay_days_override`.
- **[ABSENT]** Looked in the minimum-balances page, the Balance Settings update and object references,
  manage-payout-schedule and platform-controls — 2026-10-20. Not found:
  - whether Stripe accepts the update on an account where Stripe holds the losses and the club has a full Dashboard;
  - whether the club can then lower or remove the minimum from its own Payout settings.
- *Reading:* a minimum balance holds money back only from Stripe's **automatic** payouts. No page says it limits a
  manual payout Rakieta makes, which may take up to the available balance.

### R-CLUBMONEY-2 · The fee on a partial reversal, how soon "shortly" is, and a reversal on the sandbox

**Answer:**
- Still not documented for a partial reversal, and Stripe's own refunds page contradicts itself on reversals in
  general.
- "Shortly" stays at about two hours (carried).
- No refund on the sandbox is a reversal, and no documented card or setting makes one.

- **[DOCS]** One page holds both sentences: the opening says "Stripe's processing fees from the original transaction
  aren't returned", while its definition of a reversal reads "A reversal is the cancellation of a transaction.
  Stripe doesn't withhold any fees for payment reversals." The page now adds: "*IC+* users might see a difference in
  cost between reversals and refunds because reversals usually incur lower network fees."
  [Refund and cancel payments](https://docs.stripe.com/refunds?locale=en-US#refund-and-reversal) — 2026-10-20
- **[DOCS]** "For all refunds, payment processing, Connect, and currency conversion fees from the original charge are
  not returned." "Stripe doesn't return our fees when a payment is refunded." Reversals are not mentioned.
  [Understanding fees for refunded payments](https://support.stripe.com/questions/understanding-fees-for-refunded-payments) — 2026-10-20
- *Reading:* the newer sentence names only IC+ users as seeing a cost difference. That suggests a club on Stripe's
  standard pricing pays the same on a reversal as on a refund, with the fee kept. Unverified.
- Carried: "usually happens within 2 hours of the payment capture"
  ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line));
  a partial refund can be a partial reversal
  ([`gaps-CLUBMONEY.md`](gaps-CLUBMONEY.md#a-partial-refund-can-be-a-partial-reversal)).
- **[MEASURED]** No refund on the test club reads `destination_details.card.type: reversal`, the four failed ones
  included. Carried from the CLUBMONEY breaker's S1:
  - the refund's balance transaction `txn_3USPFA5y1DMwE3zY0BwcFbjg` shows −38,40 zł with fee 0;
  - the 1,60 zł fee on the 40,00 zł share stays charged;
  - so on the sandbox Stripe keeps the fee on a refund.
- **[ABSENT]** Looked in refunds, the support fee page, the testing page ("With all other test cards, refunds succeed
  immediately", carried) and a docs/support search for "partial reversal" — 2026-10-20. Not found:
  - the fee on a **partial** reversal;
  - a sandbox card or setting that produces a reversal.

  A question for Stripe support.

### R-CLUBMONEY-9 · Capturing a held share, or refunding, once `charges_enabled` is false or the account is removed

**Answer:** answered for **removal** and still undocumented for **charges disabled**.
- After removal Rakieta can make no call at all for the club.
- The club, still a normal Stripe account, keeps its own Dashboard.

- **[DOCS]** "A removed account no longer appears in your connected accounts list, and **you can't process payments or
  make API calls for it**." "Removing an account only disconnects it from your platform. It still functions as a
  normal Stripe account." [Manage individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts) — 2026-10-20.
  Removal "revokes access in the same way as the OAuth de-authorize endpoint … It doesn't otherwise affect the
  account". [Platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts) — 2026-10-20
- **[DOCS]** `platform_api_key_expired`: "This occurs if your platform has either generated a new key or the connected
  account has been disconnected from the platform." [Error codes](https://docs.stripe.com/error-codes) — 2026-10-20
- Carried **[MEASURED]**, the closest stand-in: an account the key can't reach (`acct_fake_breakerclubmoney0001`)
  answers a read, a list and a payout with `403 PermissionError`: "does not have access to account … Application
  access may have been revoked" (CLUBMONEY breaker S6).
  - *Reading:* after removal, Rakieta's capture at the cut-off, its cancel and its refunds would all meet this.
  - The held shares lapse on their own after 7 days unless the club captures or cancels them in its own Dashboard.
  - A refund owed can then only be made by the club.
- **[DOCS]** The closest page for charges disabled is [Pause payments and payouts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts) — 2026-10-20. It only partly applies:
  - Pausing "blocks **creation** of any charges. It also makes the transfer, card_payments and other payment
    methods capabilities `inactive`". It says nothing of capturing or refunding.
  - The workflow "isn't available when using Accounts v2".
  - "we don't enforce payment or payout pauses in a sandbox".
- **[ABSENT]** Whether a `requires_capture` PaymentIntent can be captured, or a charge refunded, once `charges_enabled`
  is false.
  - Looked in the pausing page, managing-individual-accounts, platform-controls and error-codes (no capture or
    refund code names a disabled account), plus a search — 2026-10-20.
  - Also carried: [`stripe-connect.md`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled).
  - It can't be staged: the test club can't be restricted, and sandboxes enforce neither pauses nor some
    capabilities.

### R-CLUBMONEY-9 · The refusal Rakieta's payout meets on an account whose payouts are disabled

**Answer:**
- Stripe documents `payouts_not_allowed`.
- It also documents that a disabled bank account blocks "automatic or manual payouts".
- The refusal itself was not measured: making a payout is a write, and which check Stripe runs first is not
  documented.

- **[DOCS]** "`payouts_not_allowed` — Payouts have been disabled on the connected account. Check the connected
  account's status to see if any additional information needs to be provided, or if payouts have been disabled for
  another reason." [Error codes](https://docs.stripe.com/error-codes) — 2026-10-20
- **[DOCS]** On `payout.failed`: "When a payout fails, the external account involved is disabled, and **no automatic or
  manual payouts can be processed** until the external account is updated."
  [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-20
- **[DOCS]** "Pausing payouts blocks creation of both automatic and manual payouts", read as `payouts_enabled: false`
  with `disabled_reason: platform_paused` (v1 only).
  [Pause payments and payouts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts) — 2026-10-20
- **[MEASURED]** The sandbox holds seven never-onboarded club accounts with `payouts_enabled: false` (v1 list):
  - `acct_1USPFh5y1DXbCdOQ`, `acct_1USELi5y1DCSZFum`, `acct_1USA7S5y1DjBnxJM`, `acct_1USA5z5y1DA5YwZc`,
    `acct_1US8x15y1DVGcQql`, `acct_1US8XX5y1Dlh7WsG`, `acct_1US8XX5y1DflbnVu`;
  - all read `card_payments` and `transfers` `inactive`, with `disabled_reason: requirements.past_due`;
  - through v2, `card_payments` reads `restricted` (`requirements_past_due`).
- **[ABSENT]** The refusal as measured, which was not tried. A Breaker proof could ask the adapter for a 5,00 zł
  payout on `acct_1USELi5y1DCSZFum`:
  - it holds no balance, so no money can move;
  - Stripe may still answer `balance_insufficient` before `payouts_not_allowed`, because the order of its checks is
    not documented;
  - "Sandboxes might not enforce some capabilities" (carried,
    [`stripe-connect.md`](stripe-connect.md#the-sandbox-may-allow-what-a-capability-doesnt)).

### R-CLUBMONEY-36 · Which page governs a v2 club's status, and whether v1 `account.updated` keeps firing

**Answer:**
- Both kinds of event fire.
- Stripe's v2 pages **recommend** listening to the v2 events instead, and none says the v1 event stops.
- On the sandbox every capability change on the test club produced a v1 `account.updated`, including Stripe's own
  verification decisions. v1 fired even for in-between states that the v2 events lumped together.

- **[DOCS]** From [Use the Accounts v2 API in your existing integration](https://docs.stripe.com/connect/accounts-v2/migrate-integration) — 2026-10-20. This page governs **what fires**:
  - "v2 `Accounts` send both v1 (snapshot) Events and v2 (thin) Events. The v1 events depend on the updated
    configuration. For example, updating properties of the `merchant` configuration emits v1 `account.updated`
    events".
  - "**We recommend** setting up new endpoints to listen to v2 events."
  - "changing any property on an `Account` triggers a `v1.account.updated` event. However, the same action might
    trigger property-specific events for v2".
  - Its scopes for connected accounts: "v2 events: Your account (scope changed from API v1) · v1 events: Connected
    accounts".
- **[DOCS]** `account.updated` "Allows you to monitor changes to connected account requirements and status changes.
  Available for all connected accounts"; "v1 `account.updated` events for both v1 and v2 `Accounts`".
  [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-20
- **[DOCS]** "For Account v2, create an event destination to listen for v2.core.account[requirements].updated events
  **instead of** the `account.updated` v1 event." [Onboard (SaaS, v2)](https://docs.stripe.com/connect/saas/tasks/onboard) — 2026-10-20.
  The Billing + Connect page says "Don't listen for the `account.updated` v1 event". Its setup steps then pick
  **Events from: Connected accounts** for the v2 thin events, which contradicts the migrate page's *Your account*.
  [Billing + Connect](https://docs.stripe.com/connect/integrate-billing-connect) — 2026-10-20.
  The marketplace page adds: "Your existing connected accounts fire both v1 and v2 events, so your integration can
  manage them by listening for `v1.account.updated` v2 events instead of `account.updated` v1 events."
  [Onboard (marketplace)](https://docs.stripe.com/connect/marketplace/tasks/onboard) — 2026-10-20
- *Reading:* the migrate page says what Stripe sends. The SaaS page, whose shape is Rakieta's (merchant configuration,
  full Dashboard, direct charges), says what Stripe would have Rakieta listen to. Its wording ("instead of") is a
  recommendation, not a statement that v1 stops.
- **[MEASURED]** The test club had 32 v1 `account.updated` events (all `api_version 2026-09-30.endive`, read with
  `Stripe-Account`) and 48 v2 events (read through the platform with no `Stripe-Account`, so in the *Your account*
  context). Capability moves pair up as follows:

  | v1 `account.updated` (UTC, 2026-10-19) | What it changed | v2 `capability_status_updated` |
  |---|---|---|
  | `evt_1US9Wj5y1DMwE3zYGLocyYBZ` 05:54:29 | `card_payments`, `transfers` inactive → pending | 05:54:32 `card_payments`, `stripe_balance.payouts` |
  | `evt_1US9Xc5y1DMwE3zYmCAPbbET` 05:55:24 | both pending → active; `charges_enabled`, `payouts_enabled` → true | 05:55:39 the same two |
  | ten events 09:01:10–09:02:13 | one per step: bancontact, eps (inactive → pending → active), ideal, klarna, link, pay_by_bank (none → active, inactive → active), blik, revolut_pay | eight events, batched at 09:01:28, 09:01:53, 09:02:20 |

  Nobody pressed anything for the first two rows: they were Stripe's own verification after onboarding. Who made
  the 09:01 changes is not visible.
- **[ABSENT]** Any Stripe statement that v1 `account.updated` is or will be retired for v2 accounts. Not on the
  migrate, Connect webhooks, SaaS, marketplace or Billing + Connect pages — 2026-10-20.

### R-CLUBMONEY-36 · The event types the deployed Connected-accounts endpoint will be subscribed to

**Answer:** still none to read.

- **[MEASURED]** On the platform, `GET /v1/webhook_endpoints` returns 0 and `GET /v2/core/event_destinations` returns 0
  (2026-10-20), as on 2026-10-19
  ([`stripe-sandbox.md`](stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination)).
- **[ABSENT]** The deployed endpoint's `enabled_events`: there is nothing to read until a person makes the endpoint,
  and nothing in the repo names the list (PLATFORM breaker C-J5;
  [`stripe-webhooks.md`](stripe-webhooks.md)).
- What the endpoint's list will be read against once it exists:
  - **The reader** handles five `payment_intent.*` kinds, `charge.updated` and `account.updated`, and drops the rest
    (`backend/app/modules/payments/infrastructure/stripe_notices.py:114-134`, as cited in
    [`stripe-connect.md`](stripe-connect.md#the-connect-events-stripe-calls-important)).
  - **Stripe's list for connected accounts:** `account.application.deauthorized`, `account.external_account.updated`,
    `account.updated`, `payout.failed`, `person.updated`, `payment_intent.succeeded`
    ([Connect webhooks](https://docs.stripe.com/connect/webhooks), 2026-10-20).
  - **Refunds:** "At a minimum, Stripe recommends that you listen for the `refund.created` event"
    ([Refunds](https://docs.stripe.com/refunds?locale=en-US#refund-events), 2026-10-20).
  - **v2 account events** need their own destination (the scope is above).

### R-CLUBMONEY-6 · What Stripe's hosted onboarding page shows a desk whose account is already complete

**Answer:**
- Stripe says the page shows only what is outstanding, and the test club has nothing outstanding.
- The screen itself is still unread: opening it needs a fresh link (a write) and a browser.

- **[DOCS]** `account_onboarding` "Provides a form for inputting outstanding requirements. Send the user to the form in
  this mode to just collect the new information you need." [Create an account link (v1)](https://docs.stripe.com/api/account_links/create?query=) — 2026-10-20
- **[DOCS]** "Each time an account user accesses Stripe-hosted onboarding, it reflects up-to-date requirements."
  [Migrate to Stripe-hosted or embedded onboarding](https://docs.stripe.com/connect/migrate-from-api-onboarding) — 2026-10-20
- **[DOCS]** On coming back: the return URL "doesn't mean that all information has been collected"; `account_update`
  links: "You can't create them for accounts that have access to a Stripe-hosted Dashboard."
  [Stripe-hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-20
- Carried **[MEASURED]**:
  - Stripe makes the link for the complete test club (`https://connect.stripe.com/setup/s/acct_1US95f5y1DMwE3zY/…`,
    CLUBMONEY breaker S7).
  - The account reads `currently_due []`, `eventually_due []` (S5), so such a link opens with nothing outstanding.
- **[ABSENT]** The screen a complete account sees: a summary, a Stripe sign-in, or a straight return. Looked in
  hosted-onboarding, the SaaS and marketplace onboarding pages, the v1 and v2 Account Link references,
  migrate-from-api-onboarding and a search — 2026-10-20.

  A walk shows it: on a ready club, the desk presses Connect with Stripe again in a real browser, and the walker
  writes down the page.

### R-CLUBMONEY-4 · HTTP return and refresh pages for an Account Link: refused even in testing, or not; and live

**Answer:**
- The v2 marketplace page is the odd one out.
- The v2 SaaS page, whose shape is Rakieta's, and the v1 hosted-onboarding page both allow HTTP in testing, and the
  sandbox accepted it twice.
- All three agree that live mode accepts HTTPS only.

- **[DOCS]** "You must use HTTPS for your `return_url` and `refresh_url`, both in production and in testing environments
  (for example, to test with localhost). The Account Link creation process fails if you use HTTP."
  [Onboard (marketplace)](https://docs.stripe.com/connect/marketplace/tasks/onboard) — 2026-10-20
- **[DOCS]** "You can use HTTP for your `refresh_url` and `return_url` while you're in a testing environment (for
  example, to test locally), but **live mode only accepts HTTPS**. You must update any testing URLs to HTTPS URLs
  before you go live." [Onboard (SaaS, v2)](https://docs.stripe.com/connect/saas/tasks/onboard) — 2026-10-20; the same
  sentence is on [Stripe-hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-20
- **[DOCS]** The v2 Account Link reference gives no scheme rule for either URL. Its error codes are
  `accounts_v2_access_blocked`, `configs_must_match_to_use_account_links`, `not_found` and
  `account_rate_limit_exceeded`. [Create an account link (v2)](https://docs.stripe.com/api/v2/core/account-links/create?query=) — 2026-10-20
- Carried **[MEASURED]**: links made with `http://localhost:3000` pages on the onboarded test club (CLUBMONEY breaker
  S7) and on a new, not-started v2 account `acct_1USPFh5y1DXbCdOQ` (SECURITY breaker S4, S5).
- *Reading:* the HTTPS rule holds for live. Deployed environments already refuse a club website address that is not
  `https://` ([`stripe-security.md`](stripe-security.md#onboarding-links-single-use-minutes-only-to-the-signed-in-account-holder-over-https)).
  A sandbox can't show live behaviour.

### R-CLUBMONEY-5 · What the v1 read shows while the account's v2 capabilities are `pending`

**Answer:** measured.
- While Stripe was verifying the test club, the v1 read showed charges and payouts both off, with details
  submitted.
- On those values the product shows "Stripe needs more details" with Continue with Stripe, although nothing was
  due.

- **[MEASURED]** `evt_1US9Wj5y1DMwE3zYGLocyYBZ` is the v1 `account.updated` of 2026-10-19 05:54:29 UTC. Its object
  reads:
  - `capabilities.card_payments` and `capabilities.transfers` `pending`;
  - `charges_enabled: false`, `payouts_enabled: false`, `details_submitted: true`;
  - `requirements.disabled_reason: requirements.pending_verification` and `currently_due: []`;
  - `pending_verification`: the representative's date of birth, first and last name, and identity document.

  The v2 events at 05:54:32 are `capability_status_updated` for `card_payments` and `stripe_balance.payouts`.
  55 seconds later (05:55:24, `evt_1US9Xc5y1DMwE3zYmCAPbbET`) both capabilities were `active` and charges and
  payouts were enabled.
- Code: charges and payouts both false with details submitted reads `NEEDS_DETAILS`
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:376-385`). The code's own comment expects this:
  "Stripe still verifying included — reads as needing details".
- **[DOCS]** v2 `pending`: "Stripe might be in the process of verifying" (carried,
  [`stripe-connect.md`](stripe-connect.md#a-v2-capability-is-active-pending-restricted-or-unsupported)).
- *Reading:*
  - v1's `requirements.disabled_reason` (`requirements.pending_verification`) is what separates "Stripe is checking"
    from "details are missing", and the read doesn't take it.
  - The sandbox verified in under a minute. A live check may take longer (unverified), and for that time the desk is
    asked for details it has already given.

### R-CLUBMONEY-8 · Which of a club's Stripe users gets Stripe's requirement, payout-failure and dispute emails, and in which language

**Answer:**
- Still not documented.
- What Rakieta sets is now measured: the v2 contact email is the desk's address, and the account's preferred
  language is Polish. No Stripe page says its emails follow either.

- Carried, [`gaps-CLUBMONEY.md` §2](gaps-CLUBMONEY.md#2-which-inbox-stripes-emails-reach-r-clubmoney-8-r-clubmoney-20):
  - Stripe writes to the club's own users directly.
  - Notices are chosen per user.
  - Payouts are not in the published list.
  - The recipient was not found.
- **[DOCS]** "You can configure email notifications under **Communication preferences** … on a per-user basis. If your
  team members also want to receive notifications, they must customize their own settings."
  [Start a team](https://docs.stripe.com/get-started/account/teams) — 2026-10-20
- **[DOCS]** v2 `contact_email`: "The primary contact email address for the Account." `defaults.locales`: "The Account's
  preferred locales (languages), ordered by preference." Neither says Stripe emails that address or writes in that
  language. [v2 Account object](https://docs.stripe.com/api/v2/core/accounts/object?query=contact_email),
  [create](https://docs.stripe.com/api/v2/core/accounts/create?query=defaults.locales) — 2026-10-20
- **[DOCS]** Stripe's per-category recipients file has the columns "Email Address" and "User has claimed primary user
  email address". Exporting it "from a sandbox results in an error".
  [Connected account email configuration](https://docs.stripe.com/connect/account-emails-config) — 2026-10-20
- **[MEASURED]** On the test club:
  - the v1 `email` equals the v2 `contact_email`, which is the address Rakieta sends (`stripe_payments.py:323`);
  - v2 `defaults.locales` reads `['pl-PL']`, which Rakieta sets (`:329`);
  - `business_profile.support_email` is unset.
- **[ABSENT]** Looked in teams, user roles, account-emails-config, the v2 Account object and create references, and a
  support search — 2026-10-20. Not found:
  - which user receives these emails: the person who onboarded, every Administrator, or the contact email;
  - their language.

  The recipients list can be exported only in live mode. A question for Stripe support.

### R-CLUBMONEY-32 · A club on IC+ or negotiated pricing: a `fee` on the charge's balance transaction, and `charge.updated`

**Answer, in part:**
- Stripe says IC+ users can't take the payment's fee from the balance transaction, and network costs can arrive up
  to two months later.
- Whether `charge.updated` still fires is not stated.

- **[DOCS]** "*IC+ users* … **can't retrieve payment fee information from the balance transaction.** Use the Payment
  fees report instead." "The `charge.updated` event references the `balance_transaction` property … indicating that
  it's ready to use." [Use cases for expanding responses](https://docs.stripe.com/expand/use-cases) — 2026-10-20
- **[DOCS]** "Card networks can bill fees for a given payment up to two months after it was processed"; fees are
  attributed to the originating transaction date in the Activity and Payment Fees reports.
  [Reviewing IC+ fees](https://support.stripe.com/questions/understanding-ic-fees) — 2026-10-20
- **[DOCS]** "*IC+* users might see a difference in cost between reversals and refunds because reversals usually incur
  lower network fees." [Refunds](https://docs.stripe.com/refunds?locale=en-US#refund-and-reversal) — 2026-10-20
- Carried **[MEASURED]**: the test club is on standard pricing.
  - A Polish Visa share of 40,00 zł carries a 1,60 zł `stripe_fee` on its balance transaction, and a US Visa share
    2,30 zł (CLUBMONEY breaker S1, S3, S4).
  - There are no network-cost lines.
- *Reading:* for an IC+ club the balance transaction's `fee` is not the whole cost of the share. Because the balance
  transaction still exists, `charge.updated` (which announces it) would still come, but Rakieta would record a fee that
  is too low or nil. Unverified.
- **[ABSENT]** Looked in expand/use-cases, the support IC+ pages and a docs search — 2026-10-20. Not found:
  - what an IC+ club's charge balance transaction carries in `fee`: nothing, only Stripe's part, or the whole cost;
  - whether `charge.updated` fires for it.

  A sandbox club can't be put on IC+. A question for Stripe support.

### R-CLUBMONEY-20 · Whether Stripe sends a failed manual payout again, and what Rakieta's next payout meets while the bank account is disabled

**Answer:**
- Nothing re-sends a failed manual payout: Stripe's retry is tied to "the next scheduled payout interval".
- While the bank account is disabled, Stripe says no payout, automatic or manual, can be processed.
- The exact answer to Rakieta's next payout is still unmeasured.

- **[DOCS]** From [Receive payouts — Payout failures](https://docs.stripe.com/payouts?locale=en-US#payout-failures) — 2026-10-20:
  - "If a payout fails, make sure your bank account details are correct by re-entering them. Stripe then reattempts
    the payout **at the next scheduled payout interval**."
  - "After you resolve any issues with your bank, you can reactivate the payouts by clicking **Resume Payouts**."
- **[DOCS]** "When a payout fails, the external account involved is disabled, and **no automatic or manual payouts can be
  processed until the external account is updated**." [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-20
- *Reading:*
  - A manual account has no scheduled interval, so the returned money stays on the club's balance
    (`failure_balance_transaction`) until somebody asks for a payout again: Rakieta, or the club from its Dashboard.
  - Rakieta's next payout can't go through until the club fixes its bank account in its own Dashboard.
- **[MEASURED]** The test club has one payout, `po_1USPGD5y1DMwE3zY2VJcHrmh`, which is `paid`. Its bank account pays to
  the succeeding test IBAN, so no failure has happened on the sandbox.
- **[ABSENT]** What `payouts.create` answers while the account's only bank account is disabled: a refusal
  (`payouts_not_allowed`? `bank_account_unusable`?) or a payout made and then failed. Looked in error-codes, payouts,
  connect/payouts-connected-accounts and connect/webhooks — 2026-10-20.

  The walk that shows both: onboard a walk club with Stripe's failing Polish IBAN `PL62370400440532013001`
  (`no_account`), let one payout fail, then read the next day's payout.

### R-CLUBMONEY-33 · How long a card refund may stay `pending` for `insufficient_funds`, and a live refund made before its charge is available

**Answer:**
- The window is **45 days**, from Stripe support, though the page doesn't say when the count starts.
- Whether a live refund made before its share's money is available waits or is netted, as on the sandbox, is still
  not documented.

- **[DOCS]** "**Stripe automatically fails a pending refund after 45 days.**" The page says this twice, and doesn't say
  when the count starts or which payment methods it covers.
  [Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund) — 2026-10-20 (undated)
- **[DOCS]** `failure_reason: insufficient_funds` — "Refund is pending due to insufficient funds and has crossed the
  pending refund expiration window." *Reading:* the window is those 45 days.
  [Refunds](https://docs.stripe.com/refunds?locale=en-US#failed-refunds) — 2026-10-20
- **[DOCS]** "Refunds use your available Stripe balance (not including pending amounts). If your available balance
  doesn't cover the amount of the refund, Stripe holds the refund as pending for card transactions (refunds for other
  payment method types fail) until your Stripe balance becomes sufficient." [Refunds](https://docs.stripe.com/refunds?locale=en-US) — 2026-10-20
- **[DOCS]** "Some refunds are pending because the refunding payment is still processing and has not been settled."
  [Understanding refund statuses](https://support.stripe.com/questions/understanding-refund-statuses) — 2026-10-20.
  "In the event a charge with a `pending` refund is disputed by the cardholder's bank, the refund will fail … and a
  dispute will be created." [Pending refunds due to insufficient funds](https://support.stripe.com/embedded-connect/questions/pending-refunds-due-to-insufficient-funds-or-negative-balance) — 2026-10-20
- **[MEASURED]** The test club holds 0,00 zł available, 407,16 zł pending and 0,00 zł in
  `refund_and_dispute_prefunding`. Every refund on it either succeeded at once, netted against pending money as
  measured before, or failed. None reads `pending`.
  - Four refunds failed about two minutes after they were made, with `failure_reason: expired_or_canceled_card`.
  - `re_3USPJm5y1DMwE3zY1S3GJVRF` (37,70 zł, 22:46:33 UTC) has its `refund_failure` balance transaction
    `txn_1USPMD5y1DMwE3zYEst4rfzk` at 22:48:41.
  - `re_3USOki5y1DMwE3zY1vMVdEMD` (40,00 zł, 22:09:58) has `txn_1USOmr5y1DMwE3zYWqCEmpnH` at 22:12:09.
  - In each case the money went back onto the club's **pending** balance, available 2026-10-26.
- **[ABSENT]** Whether a live card refund made before its charge's money is available waits as `pending`
  (`charge_pending` or `insufficient_funds`), as "not including pending amounts" suggests, or nets against pending
  money as the sandbox does. Looked in refunds, the three support pages above and the `pending_reason` changelog
  ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once))
  — 2026-10-20. A question for Stripe support.

### R-CLUBMONEY-19 · How long past 24 hours Stripe keeps a v1 idempotency key that replays `balance_insufficient`

**Answer:** only the minimum is published, still 24 hours.

- **[DOCS]** "For API v1, you can remove keys from the system automatically after they're **at least 24 hours old**. We
  generate a new request if a key is reused after the original is pruned." "Retries with the same key return the
  saved response, including `500` errors." [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) — 2026-10-20.
  The "you can" reads as Stripe's own pruning; no upper bound is given.
- Carried:
  - [`stripe-reliability.md`](stripe-reliability.md#a-v1-key-lasts-at-least-24-hours-after-that-the-same-key-can-run-a-new-request).
  - PLATFORM breaker T2: the payout refused `balance_insufficient` (`req_KMmuW3vNG9ksN0`) and replayed under the same
    key (`req_tdXEJ6Br2j9RzK`, `Idempotent-Replayed: true`) within the day.
- **[ABSENT]** How long keys are actually kept. Looked in idempotent_requests and the low-level error-handling page —
  2026-10-20. It can't be measured read-only, because it needs the same `POST` again more than a day later. A
  question for Stripe support.
- *Reading:* the product can count on 24 hours only. After that the same key may run anew, so a payout refused one
  day for lack of money may go through on a later day.

### R-CLUBMONEY-30 · What Stripe does with an available balance under 5 zł on a manual account

**Answer:**
- Nothing, by itself. The money stays on the club's balance until a payout of at least 5 zł takes it.
- Today's English page states this for every schedule, not only automatic ones.
- What Stripe does if it is still there after 90 days stays unknown.

- **[DOCS]** "**If your available account balance is less than the minimum payout amount, it remains in your Stripe
  account until your balance increases.**" "Minimum payout amounts are typically one base unit of the local currency."
  "PL | 5 PLN". This sits in the general *Minimum payout amounts* section, which names neither schedule.
  [Receive payouts](https://docs.stripe.com/payouts?locale=en-US#minimum-payout-amounts) — 2026-10-20
- Carried **[MEASURED]**: a 3,00 zł payout on the test club is refused with `amount_too_small`, "Amount must be no less
  than 5.00 zł" (PLATFORM breaker T3).
- Carried **[DOCS]**: on `manual`, "we hold funds in the account holder's balance until you specify otherwise. You must
  pay out the funds within" 90 days
  ([`stripe-payouts-and-balances.md`](stripe-payouts-and-balances.md#money-held-on-manual-payouts-must-leave-within-90-days)).
- *Reading:*
  - On a manual account no payout leaves by itself, so the few złoty wait on the available balance.
  - They leave with a later payout of 5 zł or more, whether Rakieta's or the club's own from its Dashboard.
- **[ABSENT]** What Stripe does with money still on a manual account after 90 days (carried, same anchor) — 2026-10-20.
