# Stripe payouts and balances — the way Rakieta uses them

What Stripe says about a club's **balance** and its **payouts**, for **this** product, read 2026-10-19 for the
payments pass on PRD #530 at `9ab0ea5b`. Every share is a **direct charge** on the club's own connected account
(Accounts v2, full Dashboard, `fees_collector` and `losses_collector` both `stripe`, Poland, złoty —
`backend/app/modules/payments/infrastructure/stripe_payments.py:317-347`), so the money lands on the **club's**
balance, never Rakieta's. Rakieta then decides one **club payout** per club per club day, at the day's close
(23:00 Kraków), of what the club's games over by then left it — shares taken, less what was given back, less the
real card fee — and makes it from the outbox with `payouts.create` on the club's account under the key
`rakieta-payout-{id}` (`backend/app/modules/payments/domain/club_payout.py:1-30`,
`backend/app/modules/payments/application/payouts.py:74-115`,
`backend/app/modules/payments/application/handlers/send_club_payouts.py:30-85`,
`stripe_payments.py:411-462`). The Money page lists the account's payouts as Stripe returns them
(`stripe_payments.py:393-409`). No `payout.*` notice is read. The spec says the club is paid **after the game is
played**, and leaves *how* to Stripe as open item O2 (`docs/specs/games-and-fill-in/the-mechanics.md:802-806`,
`:1354-1356`, `:1687-1690`).

`[DOCS]` is docs.stripe.com (Markdown, `?locale=en-US`), quoted where the words are a requirement or a
recommendation; `[MEASURED]` is read-only through `stripe` (platform `acct_1US89K5y1DB8chHb`) or `stripe-club`
(test club `acct_1US95f5y1DMwE3zY`); `[ABSENT]` was looked for and not found; *Reading* is this researcher's inference.

**Carried over, not redone** (all under three months old): returned payouts, the reconciliation report,
`balance_insufficient`, platform controls — [`gaps-CLUBMONEY.md` §1, §4, §5](gaps-CLUBMONEY.md#1-a-payout-the-bank-sends-back-r-clubmoney-20)
(2026-10-08); Stripe's email on a returned payout — [`gaps-EMAIL.md`](gaps-EMAIL.md#stripe-emails-the-account-holder-when-a-payout-comes-back-up-to-5-business-days-later);
daily payouts on a new account, losses and Stripe's recovery — [`stripe-connect.md` §1–§3](stripe-connect.md#a-club-account-rakieta-opens-starts-on-stripes-automatic-daily-payouts);
the payout key and the outbox — [`stripe-reliability.md`](stripe-reliability.md#this-products-outbox-asks-again-every-second-with-no-end);
payout events — [`stripe-webhooks.md`](stripe-webhooks.md#a-clubs-account-its-disconnection-and-its-payouts);
refunds off the pending balance — [`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once);
the test club's manual schedule — [`stripe-sandbox.md` D3](stripe-sandbox.md#differences).

---

## 1. When a club's money becomes available, and when it leaves

### A Polish account's first money is available 7 calendar days after capture, later money 3 business days after

- **[DOCS]** Settlement timing by country: "Poland | 7 calendar days | 3 business days" (initial, default); "The
  initial settlement timing applies to your first payout, and the default settlement timing applies to subsequent
  payouts." "In some cases, risk criteria might prevent your account from changing to the default settlement
  timing." Stripe counts from "T … the time of the original payment confirmation or capture". "If … you use a
  manual payout schedule, your Stripe balance is available for payout within 3 business days of capturing a
  payment." [Receive payouts — Settlement timing](https://docs.stripe.com/payouts#settlement-timing) — 2026-10-19
- **[DOCS]** The same page's *Delay behavior per account country* puts "supported EU countries" among those whose
  `delay_days` count in **calendar** days, while the table above writes Poland's default as **business** days.
  [same page](https://docs.stripe.com/payouts#delay-behavior-per-account-country) — 2026-10-19
  - *Reading:* the two lines disagree for Poland; which one governs a shift from the 7-day start is unverified.
- **[MEASURED]** `stripe-club` · `GET /v1/balance_transactions` · 2026-10-19: all 20 transactions — 14 shares
  captured 2026-10-19 between 06:32 and 11:04 UTC and their 6 refunds — read `status: pending`,
  `available_on: 1792972800` = **2026-10-26 00:00 UTC**: seven calendar days on, rounded to midnight UTC.
- **[MEASURED]** v1 retrieve of both club accounts · `stripe` · 2026-10-19: `settings.payouts.schedule.delay_days: 7`
  on the test club (onboarded, manual) and on `acct_1USELi5y1DCSZFum` (never onboarded, daily).
- **[DOCS]** "Manual payouts always use the minimum `delay_days` value." [Changelog 2015-06-15](https://docs.stripe.com/changelog/2015-06-15/accounts-manual-payout-schedules-throw-error) — 2026-10-19

### Stripe counts days in UTC

- **[DOCS]** "All payments and payouts are processed according to UTC time, except for Asia-Pacific (APAC)
  markets. As a result, the processed date might not be the same as your local time zone."
  [Receive payouts — Payout schedule](https://docs.stripe.com/payouts#payout-schedule) — 2026-10-19
  - *Reading:* a share becomes payable at 01:00 (winter) or 02:00 (summer) Warsaw time; Rakieta's club day closes at
    23:00 Kraków (`backend/app/modules/clubs/domain/court_hours.py:95-112`).

### The schedule decides only when available money leaves

- **[DOCS]** Manual — "You choose when to send payouts and how much to transfer"; Daily — "Stripe automatically
  transfers your available funds every business day"; Weekly or monthly — chosen days; "Payouts scheduled on
  weekends or holidays arrive on the next business day." "Choosing a payout schedule doesn't change how long it
  takes for your pending balance to become available. It only controls when payouts are sent." "If … daily payouts
  with a 3-business-day settlement timing, Stripe pays out funds daily from transactions that were captured 3
  business days earlier." [Receive payouts](https://docs.stripe.com/payouts#payout-schedule) — 2026-10-19
- **[DOCS]** "By default, any charge you make on behalf of a connected account accumulates in the connected
  account's balance and is paid out on a daily rolling basis."
  [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — 2026-10-19

### A club account Rakieta opens is on daily payouts; the test club is on manual

- **[MEASURED]** v1 retrieve · `stripe` · 2026-10-19: `acct_1USELi5y1DCSZFum` (opened by the code, never
  onboarded) `settings.payouts = {debit_negative_balances: true, schedule: {interval: daily, delay_days: 7}}`;
  the test club `acct_1US95f5y1DMwE3zY` `{debit_negative_balances: true, schedule: {interval: manual, delay_days: 7}}`.
  Who set the test club to manual is not visible through the API. Confirms
  [`stripe-connect.md`](stripe-connect.md#a-club-account-rakieta-opens-starts-on-stripes-automatic-daily-payouts).
- **[MEASURED]** `GET /v1/accounts` (the list) · `stripe` · 2026-10-19: the same two accounts come back **without**
  `settings.payouts`; only a retrieve by id carries it.
- Code: the account is opened with no payout setting (`stripe_payments.py:317-347`), and the code says so: "Until O2
  is settled with Stripe, accounts are opened on Stripe's own schedule" (`:420-425`).

### On Accounts v2 a club's payout settings live in Balance Settings

- **[DOCS]** "Use Balance Settings to manage payout settings for Accounts v2. The Balance Settings object follows
  similar structure and behavior to the Accounts v1 `settings.payouts` hash. If you're currently using
  `settings.payouts` on Accounts v1, you can continue to do so."
  [Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) — 2026-10-19
- **[DOCS]** `GET`/`POST /v1/balance_settings` with the `Stripe-Account` header: `payments.payouts.schedule`
  (`interval`, `weekly_payout_days`, `monthly_payout_days`), `payments.payouts.minimum_balance_by_currency`,
  `payments.payouts.statement_descriptor`, `payments.payouts.status`, `payments.settlement_timing.delay_days` and
  `delay_days_override` ("a number up to 31"), `payments.debit_negative_balances`; event `balance_settings.updated`.
  [Balance Settings](https://docs.stripe.com/api/balance-settings), [object](https://docs.stripe.com/api/balance-settings/object),
  [update](https://docs.stripe.com/api/balance-settings/update) — 2026-10-19
- **[ABSENT]** A Balance Settings read through either MCP server: `GetBalanceSettings` is "not available" and an API
  search for balance settings finds nothing · 2026-10-19. The schedule above was read through v1 instead.

### Who may change a club's interval and delay

- **[DOCS]** "Platforms that manage fraud and dispute liability, or have platform controls, can adjust the payout
  interval." `delay_days`: "You can edit this property on accounts where you own fraud and dispute liability … For
  accounts where Stripe manages fraud and dispute liability (for example, Standard accounts), the default is the
  lowest permitted value for the account." `daily`: "The `delay_days` value can't be less than your own payout
  schedule or less than the default payout schedule for the account."
  [Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) — 2026-10-19
- **[DOCS]** "Connected accounts can still make manual payouts after you, as the platform, choose to restrict connected
  accounts from updating their own payout schedule." "If you need full control … contact us."
  [Platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts#control-payout-timing) — 2026-10-19
  - *Reading:* Rakieta (Stripe liable, platform controls) may set a club to manual but can't lengthen its delay; a
    longer wait is only available as manual payouts.

### A minimum balance keeps money back from automatic payouts

- **[DOCS]** "Automatic payouts only pay out funds exceeding this minimum balance." "Only use minimum balances to cover
  anticipated refunds, disputes, and fees." "You can also programmatically configure minimum balances **per connected
  account** with the Balance Settings API … We recommend you reach out to your customers before setting a minimum
  balance." [Minimum balances](https://docs.stripe.com/payouts/minimum-balances-for-automatic-payouts) — 2026-10-19
  - *Reading:* the one documented way to keep a buffer for refunds while the club stays on Stripe's schedule; whether
    a Stripe-liable account accepts it from the platform is not stated.

---

## 2. Who may pay a club out, and how

### A standard manual payout needs the account on the manual schedule

- **[DOCS]** "To use standard manual payouts, the connected account needs to have their payout schedule set to
  `manual`." [Payouts embedded component](https://docs.stripe.com/connect/supported-embedded-components/payouts?platform=web) — 2026-10-19
- **[DOCS]** `manual`: "This setting prevents automatic payouts. You'll have to manually pay out the account's balance
  using the Payouts API (acting as the connected account)."
  [Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) — 2026-10-19
- **[ABSENT]** The error `payouts.create` returns on an account whose interval is `daily`: not in the Payouts API
  pages, `payouts`, `connect/manual-payouts`, `connect/manage-payout-schedule`, the error-codes list, the payout
  schedules FAQ (support.stripe.com, read through WebFetch) — 2026-10-19. Nothing was created to find out (no write
  tool).
  - *Reading:* on a club account Rakieta opens today (daily), Stripe pays the club itself, and Rakieta's own payout is
    either refused or finds the balance already paid out; the code catches only `balance_insufficient` and lets any
    other refusal fail the delivery (`stripe_payments.py:441-454`).

### A full-Dashboard club needs platform controls, and can still pay itself out — instantly too

- **[DOCS]** "To schedule automatic payouts or perform manual payouts for an account that has access to the full
  Stripe Dashboard, the platform must configure Platform controls for the account."
  [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — 2026-10-19
- Carried: new accounts have platform controls; the club "can still make manual payouts" —
  [`gaps-CLUBMONEY.md#a-platform-may-pay-out-a-full-dashboard-account-only-through-platform-controls-which-new-accounts-have`](gaps-CLUBMONEY.md#a-platform-may-pay-out-a-full-dashboard-account-only-through-platform-controls-which-new-accounts-have).
- **[DOCS]** Instant payouts need the `manual` interval ("You also set an account to `manual` to use Instant
  Payouts"); in Poland only to a **debit card**, 2,00 zł to 9 999 zł; "If Stripe is liable for a connected account's
  negative balances, Stripe controls eligibility." [Instant payouts for Connect](https://docs.stripe.com/connect/instant-payouts) — 2026-10-19
  - *Reading:* a club on manual payouts can empty its own available balance at any moment from its Dashboard, before
    Rakieta's payout of the same money.

### Rakieta can't pause a v2 or Stripe-liable club's payouts

- **[DOCS]** "Accounts v2 not supported — This workflow isn't available when using Accounts v2." "Platforms can pause
  payments or payouts on accounts where they're liable for negative balances." "We don't enforce payment or payout
  pauses in a sandbox." [Pause payments and payouts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts) — 2026-10-19

### A payout moves at most the available balance, from one source type, and at least 5 zł

- **[DOCS]** "With a standard payout, you can move an amount up to the user's available balance. To find that amount,
  perform a retrieve balance call on their behalf." "While individual balance components can go negative (such as
  through refunds or chargebacks), you can't create payouts for greater than the aggregate available balance."
  [Using manual payouts](https://docs.stripe.com/connect/manual-payouts) — 2026-10-19
- **[DOCS]** "If you create a manual payout on a Stripe account that uses multiple payment source types, you need to
  specify the source type balance that the payout draws from"; `source_type` one of `bank_account`, `card`, `fpx`.
  [Create a payout](https://docs.stripe.com/api/payouts/create) — 2026-10-19
- **[DOCS]** Minimum payout amounts: "PL | 5 PLN". "If your available account balance is less than the minimum payout
  amount, it remains in your Stripe account until your balance increases." [Receive payouts](https://docs.stripe.com/payouts#minimum-payout-amounts) — 2026-10-19;
  `amount_too_small`: "The specified amount is less than the minimum amount allowed." [Error codes](https://docs.stripe.com/error-codes) — 2026-10-19
- **[ABSENT]** The exact error `payouts.create` returns below 5 zł — 2026-10-19 (same pages as above).
- Code: any positive amount is paid out (`club_payout.py:66-89`, `if not games or amount <= 0: return None`); no
  `source_type` is sent (`stripe_payments.py:427-440`).

### Money held on manual payouts must leave within 90 days

- **[DOCS]** "If you set the value of `payments.payouts.schedule.interval` to `manual`, we hold funds in the account
  holder's balance until you specify otherwise. **You must pay out the funds** within the time period … All other
  countries | 90 days." "Stripe doesn't provide escrow services … you can control payout timing through manual
  payouts." "Use delayed payouts when a delivery is delayed or when you think you have a possibility of a refund."
  [Using manual payouts](https://docs.stripe.com/connect/manual-payouts) — 2026-10-19
- **[DOCS]** "We recommend that platforms hold funds only when there's a clear purpose and a commitment to … pay them
  out when an event occurs." [Holding funds](https://docs.stripe.com/connect/account-balances#holding-funds) — 2026-10-19
- **[ABSENT]** What Stripe does with money still on a manual account after 90 days: same pages and a documentation
  search — 2026-10-19.

### Arrival, cancelling and reversing

- **[DOCS]** "Manual payouts typically take 1–4 business days to arrive"; same-day only in USD, GBP and EUR; no fee for
  normal payouts. [Receive payouts](https://docs.stripe.com/payouts#manual-payouts) — 2026-10-19. `arrival_date` "factors
  in delays to account for weekends or bank holidays." [Payout object](https://docs.stripe.com/api/payouts/object) — 2026-10-19
- **[DOCS]** Cancel only while `pending`, never an automatic payout; reverse only to US and Canadian banks.
  [Cancel](https://docs.stripe.com/api/payouts/cancel), [reverse](https://docs.stripe.com/api/payouts/reverse) — 2026-10-19

### What a payout carries: description, metadata, statement descriptor, `automatic`

- **[DOCS]** `description`, `metadata`, `statement_descriptor` (≤ 22 characters, "Some banks might not display it at
  all"); `automatic` is "`true` if the payout is created by an automated payout schedule".
  [Create a payout](https://docs.stripe.com/api/payouts/create), [object](https://docs.stripe.com/api/payouts/object) — 2026-10-19
- Code: sends a description and `metadata.rakieta_payout` (`send_club_payouts.py:61-67`); reads back only id, amount,
  arrival date and status (`stripe_payments.py:393-409`, `backend/app/modules/payments/domain/provider.py:219-225`).

---

## 3. A payout's statuses, its failure, and its notices

### Five statuses; `paid` is an expectation, and can turn `failed` within 5 business days

- **[DOCS]** "`pending`: … waiting to be submitted to the bank. Funds haven't left Stripe yet"; "`in_transit`"; "`paid`:
  … For standard payouts, this typically occurs 1-2 business days after submission"; "`failed`"; "`canceled`".
  [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts#payout-status) — 2026-10-19
- **[DOCS]** "The status changes to `paid` if the transaction succeeds, or to `failed` or `canceled` (within 5 business
  days). Some payouts that fail might initially show as `paid`, then change to `failed`." [Payout object](https://docs.stripe.com/api/payouts/object);
  `payout.paid` "Occurs whenever a payout is *expected* to be available … If the payout fails, a `payout.failed`
  notification is also sent, at a later time." [Event types](https://docs.stripe.com/api/events/types) — 2026-10-19

### A failed payout returns the money and switches off the club's bank account

- **[DOCS]** "If your bank account can't receive a payout for any reason, your bank returns the funds to us … It can
  take up to 5 additional business days." [Receive payouts — Payout failures](https://docs.stripe.com/payouts#payout-failures) — 2026-10-19
- **[DOCS]** `failure_balance_transaction` "returns the funds from the failed payout back in your balance" (type
  `payout_failure`); 18 `failure_code`s, among them `account_closed`, `no_account`, `could_not_process`, `declined`
  ("Please contact the bank before retrying"), `debit_not_authorized`, `invalid_currency`.
  [Payout object](https://docs.stripe.com/api/payouts/object), [balance transaction types](https://docs.stripe.com/reports/balance-transaction-types) — 2026-10-19
- **[DOCS]** "When a payout fails, the external account involved is disabled and can't receive payouts until the
  platform updates the connected account's external account details"; "For connected accounts with access to the full
  Stripe Dashboard … the account holder manages their external payout accounts."
  [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — 2026-10-19
- Carried: re-sent at the next scheduled interval on automatic schedules, nothing said for manual ones —
  [`gaps-CLUBMONEY.md#on-manual-payouts-nothing-says-stripe-sends-it-again`](gaps-CLUBMONEY.md#on-manual-payouts-nothing-says-stripe-sends-it-again).

### Payout notices are v1 events, from the club's account

- **[DOCS]** "You can track all payout activity on connected accounts by creating an event destination and listening for
  these events: `payout.created` … `payout.updated` … `payout.paid` … `payout.failed` … Stripe also sends an
  `account.external_account.updated` event because the failed external account is disabled." "Regardless of the
  Accounts API version that you use, payouts trigger only the v1 events described here. They don't have equivalent v2
  events." [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts#track-payouts-with-webhooks) — 2026-10-19
- **[DOCS]** Also `payout.canceled`; `payout.reconciliation_completed` (**automatic** payouts only); `balance.available` —
  "when a charge is available to be paid out … not fired for negative transactions"; `balance_settings.updated`.
  [Event types](https://docs.stripe.com/api/events/types) — 2026-10-19
- Code: none is read ([`stripe-webhooks.md`](stripe-webhooks.md#a-clubs-account-its-disconnection-and-its-payouts)).

### Failing a payout on the sandbox: Stripe's Polish test IBANs

- **[DOCS]** "Use the following test bank and debit card numbers to trigger certain events when testing payouts" —
  Poland: `PL61109010140000071219812874` succeeds; `PL62370400440532013001` fails `no_account`;
  `PL89370400440532013002` `account_closed`; `…3003` `insufficient_funds`; `…3004` `debit_not_authorized`; `…3005`
  `invalid_currency`. Debit cards: `4000056160000000` succeeds, `4000056160000018` fails `could_not_process`,
  `4000056160000026` not eligible for Instant Payouts. "Test accounts with Stripe Dashboard access always have payouts
  enabled, as long as valid external bank information and other relevant conditions are met."
  [Receive payouts — Test payouts](https://docs.stripe.com/payouts#test-payouts) — 2026-10-19
- **[MEASURED]** The test club pays out to `ba_1US9LA5y1DMwE3zYHPe7QQUm`, last four 2874 (the succeeding IBAN), PLN,
  `status: new` · `stripe` · 2026-10-19. `GET /v1/payouts` on `stripe-club` is still empty · 2026-10-19.

---

## 4. The club's balance and its transactions

### A balance is available or pending, per currency and source type

- **[DOCS]** `available` — "Available funds that you can transfer or pay out automatically by Stripe or explicitly through
  the Transfers API or Payouts API", by `source_types`; `pending` — "Funds that aren't available in the balance yet";
  `refund_and_dispute_prefunding` — "Funds to cover future refunds, disputes, or a negative balance." Read as the
  connected account. [Balance object](https://docs.stripe.com/api/balance/balance_object) — 2026-10-19

### The test club's balance: 0,00 zł available, 266,16 zł pending, all from shares

- **[MEASURED]** `stripe-club` · `GET /v1/balance` · 2026-10-19: available 0,00 zł (`card` 0); pending 266,16 zł (`card`
  26616); `refund_and_dispute_prefunding` 0,00 zł both ways. It was 133,08 zł pending earlier the same day
  ([`stripe-sandbox.md`](stripe-sandbox.md#no-payouts-the-clubs-money-is-pending-until-26-october)): a second contract run
  added the same set again.
- **[MEASURED]** Its 20 balance transactions add up to that pending sum exactly: 12 shares of 40 zł (`fee` 230, `net` 3770
  — 37,70 zł each), 2 of 27 zł (`fee` 188, `net` 2512), 4 whole refunds of 40 zł and 2 of 38,24 zł; 452,40 + 50,24 −
  160,00 − 76,48 = 266,16 zł. Each refund's transaction has `fee 0`, `type refund`, `reporting_category refund`, and the
  **same** `available_on` as its charge (e.g. `txn_3USEMi5y1DMwE3zY1DAfTNxp` for `re_3USEMi5y1DMwE3zY11GGOqFA`,
  `succeeded`, `destination_details.card.type: refund`). Each charge's `fee_details` is one `stripe_fee`, "Stripe
  processing fees".
  - *Reading:* on a share refunded 38,24 zł whose fee was 2,30 zł, the club's balance keeps 37,70 − 38,24 = −0,54 zł.

### A balance transaction's fields

- **[DOCS]** `amount`, `fee`, `fee_details`, `net` ("`amount` - `fee`"), `available_on`, `status` (`available` or
  `pending`), `type`, `reporting_category`, `source`. [Balance transaction object](https://docs.stripe.com/api/balance_transactions/object);
  "Balance transactions are our recommended starting point for reporting"; "use the `reporting_category` field instead
  of the `type` field" for accounting. [Balance transaction types](https://docs.stripe.com/reports/balance-transaction-types) — 2026-10-19

### The types a club's balance will carry

- **[DOCS]** `charge`; `refund` (and, on a partial capture, one "for the uncaptured portion"); `refund_failure` ("Stripe
  returns the funds to your balance"); `adjustment` — "When a customer disputes a charge, Stripe deducts the disputed
  amount from your balance", and dispute reversals; `payout`, `payout_cancel`, `payout_failure`,
  `payout_minimum_balance_hold` / `_release`; `stripe_fee` ("Fees for Stripe software and services").
  [Balance transaction types](https://docs.stripe.com/reports/balance-transaction-types) — 2026-10-19

### Stripe lists a payout's transactions only for automatic payouts

- **[DOCS]** List balance transactions, `payout`: "For automatic Stripe payouts only, only returns transactions that were
  paid out on the specified payout ID." `reconciliation_status: not_applicable` — "We only support this for standard
  automatic payouts." [List balance transactions](https://docs.stripe.com/api/balance_transactions/list),
  [Payout object](https://docs.stripe.com/api/payouts/object) — 2026-10-19
- **[DOCS]** "You control the timing and amount of manual payouts, so Stripe can't identify which transactions are
  included in each payout. **You're responsible for reconciling payouts you create** against your transaction history."
  [Payout reconciliation](https://docs.stripe.com/payouts/reconciliation) — 2026-10-19
- **[DOCS]** For manual payouts Stripe points to the Balance report, which "doesn't associate payouts with payment
  transactions"; its `effective_at` "For manual payouts … is the date the payout was initiated."
  [Balance report](https://docs.stripe.com/reports/balance) — 2026-10-19

---

## 5. Negative balances

### Refunds and disputes can take the club's balance below nought, and then no payout leaves

- **[DOCS]** "Some actions, such as refunds and chargebacks, create negative transactions … If at all possible, Stripe
  automatically offsets negative transactions against future payments … when charging on a connected account, a refund
  or chargeback comes from the connected account." "**While an account's balance is negative, you can't send payouts**
  to the account's bank or debit card on their behalf. Stripe resumes sending payouts to the connected account when the
  account's Stripe balance becomes positive." [Account balances](https://docs.stripe.com/connect/account-balances#accounting-for-negative-balances) — 2026-10-19
- **[DOCS]** "If you don't receive further payments to balance out the negative amount, Stripe creates a payout that
  *debits* your bank account." [Negative payouts](https://docs.stripe.com/payouts#negative-payouts) — 2026-10-19
- **[DOCS]** A card refund the available balance can't cover waits `pending`, and fails `insufficient_funds` once it "has
  crossed the pending refund expiration window." [Refunds](https://docs.stripe.com/refunds) — 2026-10-19 (the sandbox
  took refunds off the pending balance at once: carried above).

### A złoty bank account isn't listed for automatic debits

- **[DOCS]** "Banks in the following countries support auto debit for negative balances: Australia, Canada, Europe (SEPA
  countries, which includes the UK), New Zealand, United States." "Enabling `debit_negative_balances` triggers debits as
  needed, even when the connected account is on manual payouts." "Stripe can't correct a negative Stripe account balance
  using a debit card." [Account balances](https://docs.stripe.com/connect/account-balances#automatically-debit-connected-accounts) — 2026-10-19
- **[DOCS]** "For SEPA countries, we only support auto debits from EUR bank accounts." "Standard Stripe accounts will only
  be debited if their negative balance is greater than 10 units of their local currency." "We will make multiple
  subsequent attempts to debit your bank account in the event that a debit fails." [Auto debit FAQ](https://support.stripe.com/questions/auto-debit-faq)
  — 2026-10-19 (read through WebFetch: the page needs JavaScript; Poland and PLN are not named)
- **[MEASURED]** `debit_negative_balances: true` on both club accounts; the test club's bank account is `country PL`,
  `currency pln` · `stripe` · 2026-10-19.
  - *Reading:* on a club's złoty account the debit setting is unlikely to act; a negative balance waits for the next
    shares, and Stripe, as the losses collector, bears what is never recovered.

### Rakieta carries no reserve for a club's negative balance

- **[DOCS]** Platform reserves (`reserve_transaction`, after 180 days `connect_collection_transfer`) cover "negative
  connected account `available` balances that your platform is responsible for"; responsibility is v2
  `defaults.responsibilities.losses_collector`. [Account balances](https://docs.stripe.com/connect/account-balances#understanding-connected-reserve-balances) — 2026-10-19
- **[MEASURED]** `controller.losses.payments: stripe`, `controller.fees.payer: account` on every club account ·
  `stripe` · 2026-10-19.

---

## 6. Rakieta's ledger against Stripe's

### Rakieta sizes a payout from its own ledger, never from the club's Stripe balance

- Code: a game is paid once it is over and every share is settled; what it left is each share's amount, less what was
  given back, less its card fee read from the charge's balance transaction (`backend/app/modules/payments/domain/seat_charge.py:462-473`,
  `club_payout.py:66-89`). A day netting nought or less waits and is netted against the next
  (`club_payout.py:13-20`). The decision is made at the day's close, every five minutes
  (`backend/app/core/config.py:521-522`), and made at Stripe from the outbox; a `balance_insufficient` refusal becomes
  *payments unavailable* and is tried again (`stripe_payments.py:441-454`); any other refusal raises.
- Code: a booking reads *paid out* once a payout the provider took carried it (`backend/app/modules/payments/domain/ports.py:208-211`;
  `backend/app/modules/proposals/presentation/club_routes.py:592-598`: "A payout carried its money to your bank").
  Nothing re-reads the payout afterwards.
- Code: the fake pays every positive payout at once, `in_transit`, arriving two days later, and never refuses one for
  balance, schedule, minimum or bank (`backend/app/modules/payments/infrastructure/fake_payments.py:585-620`, `:104`).

### What the club's Stripe balance holds that Rakieta's ledger does not

- The club's own sales and refunds in its full Dashboard, BLIK and Klarna among them
  ([`stripe-connect.md`](stripe-connect.md#the-club-switches-its-own-payment-methods-on));
- disputes and their 90 zł fee, debited at once
  ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#a-disputed-40-zł-share-costs-the-club-130-zł-at-once-and-90-zł-more-to-fight-it));
- refunds that fail up to 30 days later and come back as `refund_failure`
  ([`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#a-refund-can-fail-up-to-30-days-later-for-seven-reasons-and-the-seller-must-pay-another-way));
- failed payouts' money back as `payout_failure` (§3); Stripe's service fees as `stripe_fee` (§4);
- Stripe's own automatic payouts, and any the club makes itself (§1, §2).
  - *Reading:* the two sums agree only while nothing but Rakieta's shares touches the account and nobody else pays it
    out.

### Stripe's tools for tying a payout to its games

- **[DOCS]** For automatic payouts: list balance transactions by `payout` with `expand[]=data.source` to reach each
  charge's `metadata` ([reconciliation](https://docs.stripe.com/payouts/reconciliation)); the report's Itemized CSV can
  carry "custom metadata" ([report](https://docs.stripe.com/reports/payout-reconciliation)) — 2026-10-19.
- Code: Rakieta keeps each payout's games (`club_payout.py:92-110`) and tags it `rakieta_payout`
  (`send_club_payouts.py:65`); the Money page lists every payout on the account without that tag (`stripe_payments.py:393-409`).

---

## Pitfalls

### P1 · Building on manual payouts while the club account is on Stripe's daily schedule
Rakieta opens every club on Stripe's default — daily, measured — and sets no schedule (`stripe_payments.py:420-425`).
Stripe then pays the club itself, 7 calendar days after each capture at first and 3 business days after later
([payouts](https://docs.stripe.com/payouts#settlement-timing)), and a standard manual payout needs `manual`
([embedded payouts](https://docs.stripe.com/connect/supported-embedded-components/payouts?platform=web)). Rakieta's own
payout is then refused or finds nothing left, the delivery retries every second, *A payout was sent* never goes, and the
club is paid on Stripe's clock instead of "after the game".

### P2 · Assuming *manual* means Rakieta alone pays the club
"Connected accounts can still make manual payouts" after the platform restricts the schedule, and full control means
contacting Stripe ([platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts#control-payout-timing));
a manual account can also take instant payouts to a Polish debit card ([instant payouts](https://docs.stripe.com/connect/instant-payouts)).
A club that pays itself first leaves Rakieta's payout `balance_insufficient`, and Rakieta's ledger still owes it.

### P3 · Treating `paid` as final, and not hearing `payout.failed`
A payout can read `paid` and turn `failed` within 5 business days; the money returns as `payout_failure` and the bank
account is switched off ([payout object](https://docs.stripe.com/api/payouts/object),
[connected payouts](https://docs.stripe.com/connect/payouts-connected-accounts)). Rakieta marks the games *paid out* when
Stripe takes the payout and never re-reads it, so the bookings keep saying paid while the money sits on the club's
balance, and on a manual schedule nothing pays it again ([gaps-CLUBMONEY](gaps-CLUBMONEY.md#on-manual-payouts-nothing-says-stripe-sends-it-again)).

### P4 · Sizing a payout from the platform's ledger instead of the account's available balance
"You can't create payouts for greater than the aggregate available balance"; "you're responsible for reconciling
payouts you create" ([manual payouts](https://docs.stripe.com/connect/manual-payouts),
[reconciliation](https://docs.stripe.com/payouts/reconciliation)). After a dispute or a failed or outside refund the same
payout is refused day after day; money the ledger doesn't know is never paid out by Rakieta.

### P5 · Paying out below 5 zł
The Polish minimum is 5 PLN ([payouts](https://docs.stripe.com/payouts#minimum-payout-amounts)); Rakieta pays any
positive day (`club_payout.py:86-88`). A day that nets, say, 3 zł is asked of Stripe and refused (error unverified), and
under a fixed key it is refused again for ever.

### P6 · Retrying a refused payout under the same key, every second
A saved `400` is replayed for 24 hours, and the outbox asks again each second with no end
([`stripe-reliability.md`](stripe-reliability.md#this-products-outbox-asks-again-every-second-with-no-end)). Stripe offers
`balance.available` for "when a charge is available to be paid out" ([event types](https://docs.stripe.com/api/events/types)).

### P7 · Expecting Stripe to say which games a manual payout carried
`reconciliation_status` is `not_applicable` for manual payouts, the `payout` filter works "for automatic Stripe payouts
only", and the reconciliation report needs automatic payouts ([payout object](https://docs.stripe.com/api/payouts/object),
[list](https://docs.stripe.com/api/balance_transactions/list), [report](https://docs.stripe.com/reports/payout-reconciliation)).
Only Rakieta's own record ties a payout to its games; the Money page's list doesn't show which payouts are Rakieta's.

### P8 · Counting availability in Warsaw time and business days
Stripe processes in UTC; the sandbox's shares became available at 00:00 UTC seven calendar days on (measured); Stripe's
own pages call Poland's later delay both business and calendar days ([payouts](https://docs.stripe.com/payouts#delay-behavior-per-account-country)).
A rule or email that promises a day computed another way is off by one.

### P9 · Counting on the debit of a negative balance from a złoty account
Automatic debits in SEPA countries are "only … from EUR bank accounts" ([auto debit FAQ](https://support.stripe.com/questions/auto-debit-faq));
the setting reads `true` on every club account (measured). While the balance is negative "you can't send payouts"
([account balances](https://docs.stripe.com/connect/account-balances#accounting-for-negative-balances)).

### P10 · Holding money past 90 days, or with no clear release
"You must pay out the funds within … 90 days"; hold "only when there's a clear purpose"
([manual payouts](https://docs.stripe.com/connect/manual-payouts), [holding funds](https://docs.stripe.com/connect/account-balances#holding-funds)).
A game never *over*, weeks of negative days, or a club leaving Rakieta leave money nobody pays out.

### P11 · Planning to pause a club's payouts, or to set its delay
Pausing is "not supported" for Accounts v2 and Stripe-liable accounts; the delay is editable only "where you own fraud
and dispute liability" ([pause](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts),
[schedule](https://docs.stripe.com/connect/manage-payout-schedule)); removal resets payout timing
([`stripe-connect.md`](stripe-connect.md#removing-a-club-ends-every-api-call-rakieta-can-make-for-it)).

### P12 · Reading payout settings from the account list
The list omits `settings.payouts` (measured); for v2, Stripe keeps them in Balance Settings
([schedule](https://docs.stripe.com/connect/manage-payout-schedule)).

### P13 · A walk that never shows a failed payout
The walk's IBAN always succeeds and the fake never fails a payout (`fake_payments.py:585-620`); Stripe's failing Polish
IBANs do ([test payouts](https://docs.stripe.com/payouts#test-payouts)).

---

## Checks

1. Which payout schedule does each club account Rakieta opens actually carry, who sets it, and when? If it is Stripe's
   daily schedule, does any rule still promise the club is paid by Rakieta, after the game?
2. Before Rakieta asks for a payout, does it compare its figure with the club's **available** balance — and when they
   differ, who is told, and does the money still reach the club?
3. When Stripe refuses a payout for anything but money not yet available (automatic schedule, payouts disabled, a
   negative balance, below 5 zł), does the retry stop, and does the club or Rakieta learn why?
4. When a payout comes back from the bank (`payout.failed`, up to 5 business days after *paid*), do the club's bookings
   stop reading *paid out*, is the desk told, and is the money paid again once the bank details are fixed?
5. Does anything hear `payout.*`, `account.external_account.updated` or `balance.available` on the Connect endpoint, or
   does the product only read the list when the Money page opens?
6. Can the club pay itself out (in its Dashboard, or instantly to a debit card) before Rakieta does, and what does
   Rakieta's ledger do with a game whose money the club already took?
7. Is every payout at least 5 zł, and is a smaller remainder carried to the next day rather than asked of Stripe?
8. Is money on a manual account paid out within 90 days in every case — a game never *over*, a long run of negative
   days, a club pausing or leaving Rakieta — and is everything paid out before the account is removed?
9. When a dispute, a failed refund or the club's own refund lowers the balance, does the next payout account for it,
   and does a negative balance stop payout attempts until it is positive?
10. Are *available* and *arrives* dates computed as Stripe does — UTC, 7 calendar days for the first payout, then the
    default — and does the payout email use Stripe's `arrival_date`?
11. Does the Money page tell Rakieta's payouts (`automatic: false`, `metadata.rakieta_payout`) from Stripe's automatic ones
    and the club's own, and show a failed one with its reason?
12. Can a club's accountant trace each payout to its games and to each share's charge, refund and fee on the club's
    balance?
13. Does a walk or a contract test show a payout that fails, using Stripe's failing Polish IBANs?
