# Stripe Connect — the way Rakieta uses it

What Stripe says about Connect for **this** product, read 2026-10-19 for the payments pass on PRD #530 at
`9ab0ea5b`. Rakieta is a Polish Connect platform. Each club is a connected account opened with **Accounts v2**:
the `merchant` configuration with `card_payments`, the **full Dashboard**, `fees_collector` and `losses_collector`
both `stripe`, country `pl`, entity type `company`, złoty (`backend/app/modules/payments/infrastructure/stripe_payments.py:317-347`).
Every share is a **direct charge** on the club's account with a single-use clone of the player's platform card,
held with manual capture, off-session (`:466-542`). The club onboards on Stripe-hosted pages through a v2 Account
Link (`:349-369`); *ready* means the v1 read says charges **and** payouts enabled (`:371-391`); Rakieta hears about the
account only through v1 `account.updated` on its Connected-accounts endpoint (`stripe_notices.py:130-133`).

`[DOCS]` is Stripe's documentation, quoted where the words make it a requirement ("must") or a recommendation
("we recommend"); `[MEASURED]` is the sandbox read through `stripe` (platform `acct_1US89K5y1DB8chHb`) or
`stripe-club` (test club `acct_1US95f5y1DMwE3zY`), read-only; `[ABSENT]` was looked for and not found.

**Carried over, not redone** (all under three months old): merchant of record, cloning, what a Polish club
supplies, fees, the 90 zł dispute fee, refunds out of the club's balance, payouts and receipts in Poland —
[`local-market.md#stripe-connect-in-poland`](local-market.md#stripe-connect-in-poland) (2026-10-06/08); Stripe's
emails to a full-Dashboard club, signing in, platform controls for payouts —
[`gaps-CLUBMONEY.md` §2, §3, §5](gaps-CLUBMONEY.md#5-a-payout-rakieta-asks-of-stripe-r-clubmoney-19) (2026-10-08);
who pays the fee —
[`gaps-S-01A-leave-fee.md#with-fees-collected-by-stripe-the-club-pays-the-fee-and-funds-every-refund`](gaps-S-01A-leave-fee.md#with-fees-collected-by-stripe-the-club-pays-the-fee-and-funds-every-refund)
(2026-10-10); the sandbox's configuration and the code's calls —
[`stripe-sandbox.md#differences`](stripe-sandbox.md#differences) (2026-10-19).

---

## 1. The account type and its configuration

### Accounts v2 with the merchant configuration is what Stripe recommends for new platforms

- **[DOCS]** "v2 Accounts are the most flexible option, and **we recommend** them for new integrations"; legacy
  Standard/Express/Custom are "(deprecated)". [Integration recommendations](https://docs.stripe.com/connect/integration-recommendations) — 2026-10-19
- **[DOCS]** "The `merchant` configuration allows an `Account` to accept payments … It includes the `card_payments`
  and `stripe_balance.payouts` … capabilities." [Accounts v2](https://docs.stripe.com/connect/accounts-v2) — 2026-10-19;
  "You must minimally request `card_payments`." [Create a connected account](https://docs.stripe.com/connect/saas/tasks/create) — 2026-10-19

### The responsibilities are set once and can never change

- **[DOCS]** "You must define `defaults.responsibilities` properties when you add the Merchant configuration …
  **You can't update their values later.**" `fees_collector: stripe`: "Stripe collects payment fees directly from the
  connected account." `losses_collector: stripe`: "Stripe is liable for the connected account's negative balances.
  Your platform is still liable for negative balances on your platform account."
  [Connected account configuration](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration) — 2026-10-19

### The Dashboard type is permanent

- **[DOCS]** "**Dashboard type is immutable.** … To change a connected account's dashboard, you must create a new
  `Account` object." [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19

### With Stripe liable and a full Dashboard, Stripe collects the requirements

- **[DOCS]** "Your platform is responsible only when you set `losses_collector` to `application` and `dashboard` to
  `none`." [Connected account configuration](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration) — 2026-10-19
- **[MEASURED]** `stripe` · `GET /v2/core/accounts/acct_1USELi5y1DCSZFum` (opened by the product for "Bonarka Arena",
  never onboarded) · 2026-10-19: `requirements_collector: stripe`, `dashboard: full`, `identity: {country: PL,
  entity_type: company}`.

### Stripe recommends exactly this pairing for direct charges

- **[DOCS]** "For integrations using direct charges, **we recommend** assigning responsibility for connected account
  negative balances to Stripe." [Integration recommendations](https://docs.stripe.com/connect/integration-recommendations) — 2026-10-19
- **[DOCS]** "**We recommend** using direct charges for connected accounts that have access to the full Stripe
  Dashboard." [Direct charges (React Native)](https://docs.stripe.com/connect/direct-charges?platform=react-native) — 2026-10-19

### Accounts v2 must be enabled for the platform; a v2 account still answers on v1

- **[DOCS]** A v2 Account Link fails with `400 accounts_v2_access_blocked`: "Accounts v2 is not enabled for your
  merchant." [v2 account links](https://docs.stripe.com/api/v2/core/account-links/create) — 2026-10-19; "You can enable
  Accounts v2 for your Connect platform from your Dashboard." [Billing + Connect](https://docs.stripe.com/connect/integrate-billing-connect) — 2026-10-19
- **[DOCS]** "You can still pass the ID of a v2 `Account` to an Accounts v1 API endpoint … the response is structured
  as a v1 `Account`." v1 is required for OAuth, recipient agreements, deprecated payment methods and "certain payment
  methods in public or private preview". v2 calls "return … null for other properties" unless asked with `include`.
  [Accounts v2](https://docs.stripe.com/connect/accounts-v2) — 2026-10-19

### Through v1, a club's v2 account reads as a Standard account Rakieta controls

- **[MEASURED]** `stripe` · `GET /v1/accounts/acct_1USELi5y1DCSZFum` · 2026-10-19: `type: standard`,
  `controller: {type: application, is_controller: true, fees.payer: account, losses.payments: stripe,
  requirement_collection: stripe, stripe_dashboard.type: full}`, `charges_enabled`/`payouts_enabled`/`details_submitted`
  false, `disabled_reason: requirements.past_due`.
- **[MEASURED]** Same read of the test club `acct_1US95f5y1DMwE3zY`: same controller, `mcc: "7299"`,
  `statement_descriptor: "ROBER CLUB"`, `dashboard.timezone: "Etc/UTC"`.

### A club account Rakieta opens starts on Stripe's automatic daily payouts

- **[MEASURED]** v1 read of `acct_1USELi5y1DCSZFum` · 2026-10-19: `payouts.schedule = {interval: daily, delay_days: 7}`,
  `debit_negative_balances: true`. The code sets no schedule (`stripe_payments.py:420-425`); the test club reads
  `manual` ([`stripe-sandbox.md#the-test-clubs-payouts-are-manual-with-a-7-day-delay`](stripe-sandbox.md#the-test-clubs-payouts-are-manual-with-a-7-day-delay)),
  whose "carry no payout settings" holds for the v2 read only.
- **[DOCS]** "By default, Stripe pays out funds that have settled in your connected accounts' balances on a daily
  rolling basis." [Design an integration (v1)](https://docs.stripe.com/connect/design-an-integration) — 2026-10-19

---

## 2. What a full-Dashboard club can do on its own

### The club handles its own payments, refunds and disputes

- **[DOCS]** Connected accounts can "View payments, balances, customers … Handle disputes, refunds, and chargebacks";
  "If you need more control over Dashboard features …, **we recommend** using the Express Dashboard."
  [Stripe Dashboard for connected accounts](https://docs.stripe.com/connect/stripe-dashboard) — 2026-10-19
- Signing in, no login links: [`gaps-CLUBMONEY.md#a-full-dashboard-club-signs-in-at-dashboardstripecom-login-links-exist-only-for-express`](gaps-CLUBMONEY.md#a-full-dashboard-club-signs-in-at-dashboardstripecom-login-links-exist-only-for-express) (2026-10-08).

### The club switches its own payment methods on

- **[DOCS]** "For connected accounts with access to the full Stripe Dashboard … **most payment method capabilities are
  enabled by default. Those accounts can manage their own payment method capabilities.**" BLIK "must be activated on
  the Dashboard settings page." [Account capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2) — 2026-10-19
- **[MEASURED]** The test club holds ten active capabilities, BLIK among them —
  [`stripe-sandbox.md#the-test-clubs-capabilities-card-payments-and-nine-more`](stripe-sandbox.md#the-test-clubs-capabilities-card-payments-and-nine-more).

### The club writes its own Radar rules; Rakieta's rules don't reach its payments

- **[DOCS]** "**Your platform Radar rules don't apply to direct charges made on your connected accounts.**"
  [Integration recommendations](https://docs.stripe.com/connect/integration-recommendations) — 2026-10-19

### A club Rakieta opened can't disconnect itself; only Rakieta can remove it

- **[DOCS]** Under platform controls: "You cannot disconnect the platform that administers your account." The account
  asks the platform. [Support: Platform controls](https://support.stripe.com/questions/platform-controls-for-connected-accounts) — 2026-10-19 (undated page)
- **[MEASURED]** Both club accounts read `controller.is_controller: true` (§1).

### Removing a club ends every API call Rakieta can make for it

- **[DOCS]** "A removed account … **you can't process payments or make API calls for it.** You also permanently lose any
  platform-controlled settings … even if the account reconnects later." [Manage individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts) — 2026-10-19;
  removal "revokes access in the same way as the OAuth de-authorize endpoint … resets all platform controls … such as
  payout timing." [Platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts) — 2026-10-19

---

## 3. Who pays the fees, and who bears the losses

### The club pays Stripe's fees, disputes included; Rakieta pays no Connect fee

- Carried: [`local-market.md#who-pays-stripes-fees`](local-market.md#who-pays-stripes-fees) (2026-10-06),
  [`gaps-S-01A-leave-fee.md#pricing-tools-cost-passthrough-and-application-fees-cannot-move-the-fee`](gaps-S-01A-leave-fee.md#pricing-tools-cost-passthrough-and-application-fees-cannot-move-the-fee) (2026-10-10).
- **[DOCS]** Dispute-fee payer for a v2 account with `fees_collector` = `stripe`: "Connected account."
  [Refunds and disputes (SaaS)](https://docs.stripe.com/connect/saas/tasks/refunds-disputes) — 2026-10-19

### Refunds and disputed money come out of the club's balance; a short refund waits

- **[DOCS]** Direct charges: "If the connected account's balance is insufficient, we set the refund status to
  `pending` … Stripe automatically processes pending refunds in the order they were created." "Stripe debits the
  disputed amount from the connected account's balance." [How charges work](https://docs.stripe.com/connect/charges) — 2026-10-19
- Carried, earlier reading: a short card refund "fails after an expiry window"; BLIK or P24 "fails at once" —
  [`local-market.md#refunds-come-out-of-the-clubs-balance`](local-market.md#refunds-come-out-of-the-clubs-balance).

### Stripe covers only what it can't recover, and first takes it from the club's bank

- **[DOCS]** "Stripe first attempts to offset the negative amount by collecting funds from the account's external
  account." [Risk management](https://docs.stripe.com/connect/risk-management) — 2026-10-19; "While an account's balance
  is negative, you can't send payouts"; `debit_negative_balances` "triggers debits as needed, even when the connected
  account is on manual payouts." [Account balances](https://docs.stripe.com/connect/account-balances) — 2026-10-19
- **[MEASURED]** `debit_negative_balances: true` on both club accounts (§1).

### With Stripe liable, Rakieta can't pause a club's payments or payouts

- **[DOCS]** "**You can't pause payments or payouts for your connected accounts.**" "You can't directly debit connected
  account balances." Stripe "directly contacts your connected accounts … and in some cases can take action against
  them." [Risk management](https://docs.stripe.com/connect/risk-management) — 2026-10-19

### Stripe may pause a club's charges or payouts, hold a reserve, or close it

- **[DOCS]** "Stripe might slow or pause payouts, or pause a connected account's ability to process charges"; "might
  hold a reserve"; "might deactivate the connected account." Managed Risk requires Radar on connected-account payments,
  direct charges, hosted or embedded onboarding, and the full service agreement; it costs nothing extra on Standard-like
  accounts. [Managed Risk](https://docs.stripe.com/connect/risk-management/managed-risk) — 2026-10-19

---

## 4. Direct charges, and on whose account each object lives

### The payment, charge, fee, refunds and disputes live on the club's account

- **[DOCS]** "Transaction objects such as `PaymentIntents` and `Charges` exist on the connected account … **you must**
  query the Stripe API using the connected account ID in the Stripe-Account header."
  [Direct charges (React Native)](https://docs.stripe.com/connect/direct-charges?platform=react-native) — 2026-10-19
- **[DOCS]** "Because the connected account owns the object that triggered the event, **you must** make API requests
  for that object as the connected account." [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-19

### The player's card lives on the platform; each charge uses a single-use clone

- **[DOCS]** "Cloning supports PaymentMethods that have `type` set to either `card` or `us_bank_account`." The clone
  "inherits the setup performed on your platform account"; "Creating a charge with the cloned PaymentMethod consumes
  it … You can't reuse the consumed clone." A platform in another country "might need to use `on_behalf_of`".
  [Multiple accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — 2026-10-19. Platform and
  clubs are all Polish ([`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account)).
- Code: clone with the platform Customer (`stripe_payments.py:466-483`); the payment names no customer (`:501-502`).

### The phone confirms a refused share on the club's account

- **[DOCS]** `<StripeProvider publishableKey=… stripeAccountId='{{CONNECTED_ACCOUNT_ID}}'>`.
  [Direct charges (React Native)](https://docs.stripe.com/connect/direct-charges?platform=react-native) — 2026-10-19
- Code: `stripeAccountId: accountId` from `connected_account_id` (`frontend_player/src/shared/lib/platform/payments.tsx:226`,
  `frontend_player/src/features/payments/mappers/seatChargeMappers.ts:41`).

### The player's statement shows the name the club picked

- **[DOCS]** With `card_payments`, "customers' bank statements display the connected account's statement descriptor,
  not the platform's." [Account capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2) — 2026-10-19;
  it "must be similar to the business name, legal entity name, or business URL."
  [Verification with the API](https://docs.stripe.com/connect/handling-api-verification) — 2026-10-19
- **[MEASURED]** Test club: `ROBER CLUB`, MCC 7299 (§1).

### Card payments need transfers too; either inactive stops both

- **[DOCS]** "You must request both `card_payments` and `transfers`." "If … the `status` of either one is `inactive`,
  then both capabilities are disabled." [Account capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2) — 2026-10-19
- **[MEASURED]** The code asks only for `card_payments`; v1 read of `acct_1USELi5y1DCSZFum` shows
  `{card_payments: inactive, transfers: inactive}` — Stripe added `transfers`.

---

## 5. Onboarding links, requirements and capabilities

### An Account Link is single use, lasts minutes, and goes only to the signed-in holder

- **[DOCS]** "You can only use each temporary Account Link URL once … **Authenticate the account in your application
  before redirecting them.**" "**Don't email, text, or otherwise send account link URLs outside of your platform
  application.**" [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19; the v2 example
  expires ten minutes after creation. [v2 account links](https://docs.stripe.com/api/v2/core/account-links/create) — 2026-10-19
- Code: minted only for the signed-in desk (`backend/app/modules/payments/presentation/club_routes.py:79-85`); the
  email links to `/payments/continue`, which mints a fresh one (`frontend_club/src/app/payments/continue/route.ts:10-12`,
  `backend/app/modules/clubs/application/payments_account.py:146-157`).

### A stale, used or previewed link sends the club to the refresh URL

- **[DOCS]** Refresh when "The link expired (a few minutes …)", "was already visited", or "was shared in … a messaging
  client that attempts to … preview it"; "**live mode only accepts HTTPS**."
  [Onboard (SaaS)](https://docs.stripe.com/connect/saas/tasks/onboard) — 2026-10-19

### Coming back to the return URL doesn't mean the club is done

- **[DOCS]** The return URL is hit on completion or "**Save for later** … **It doesn't mean that all information has
  been collected** … This URL passes no state." [Onboard (SaaS)](https://docs.stripe.com/connect/saas/tasks/onboard) — 2026-10-19
- Code reads the account after every link (`payments_account.py:90-98`) and every `account.updated` (`:130-144`).

### A full-Dashboard club can't get an update link, only the onboarding link again

- **[DOCS]** `account_update` links: "**You can't create them for accounts that have access to a Stripe-hosted
  Dashboard.**" [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19. Code: one
  `account_onboarding` link for both (`stripe_payments.py:349-369`).

### Prefill before the first link; the club can edit it, but not the country

- **[DOCS]** "If you specify the account's country or request any capabilities …, the account owner can't change its
  country." "The account holder can edit any pre-filled information before they accept the service agreement."
  "Prefill … before generating the Account Link because **you can't read or write information for the connected account
  afterward**." [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19
- Code prefills `country: pl`, `entity_type: company`, the desk's email and the club's name (`stripe_payments.py:321-331`).
  Whether "any pre-filled information" includes the v2 `entity_type` is not stated (unverified).

### Rakieta collects only what is due now; later requirements arrive while games are booked

- **[DOCS]** "If you don't specify `collection_options`, the default value is `currently_due`."
  [Changelog](https://docs.stripe.com/changelog/basil/2025-07-30/enable-v2-account-links-api-for-connect) — 2026-10-19;
  up-front collection "**Avoids the possibility of payout and processing issues due to missed deadlines**."
  [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19. Code passes none (`:355-366`).

### A new Polish company club owes Stripe 35 items, all due at once

- **[MEASURED]** v2 read of `acct_1USELi5y1DCSZFum` · 2026-10-19: 35 `requirements.entries`, all
  `awaiting_action_from: user`, `past_due`, restricting `card_payments` and payouts: MCC, support phone, business URL
  and product description, bank account, owners attestation, terms (date, IP), company address, phone, registered name
  and REGON (`id_numbers.pl_regon`), each owner's address, birth date, email and name, and the representative's
  address, birth date, email, name, nationality, phone and title.
- **[DOCS]** A working `business_profile.url` is required "when requesting the `card_payments` capability", else a
  product description. [Verification with the API](https://docs.stripe.com/connect/handling-api-verification) — 2026-10-19
- Carried: Polish entity types, no government type — [`local-market.md#what-a-polish-club-must-supply-to-stripe`](local-market.md#what-a-polish-club-must-supply-to-stripe).

### Hosted onboarding needs Rakieta's Connect branding, and a real browser

- **[DOCS]** Brand name, colour and icon: "**Stripe-hosted onboarding requires this information.**" "You can't use it
  in embedded web views." [Hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding) — 2026-10-19

### A v2 capability is active, pending, restricted or unsupported

- **[DOCS]** `pending`: "Stripe might be in the process of verifying"; `restricted`: "possibly because of outstanding
  requirements"; exiting onboarding "doesn't confirm that they've provided all outstanding requirements. **You must
  still check the statuses.**" [Track onboarding (v2)](https://docs.stripe.com/connect/track-account-onboarding?dashboard-or-api=api&accounts-namespace=v2) — 2026-10-19

### At a missed deadline, payouts usually stop first

- **[DOCS]** "Stripe typically disables payouts … by the `current_deadline` … if payouts are already disabled and the
  account is unresponsive …, Stripe might also disable the ability to process charges." `disabled_reason` includes
  `requirements.past_due`, `under_review`, `listed`, `rejected.*`. Risk reviews add requirements "which you can't
  provide using the API." [Verification with the API](https://docs.stripe.com/connect/handling-api-verification) — 2026-10-19
- Code: *ready* = charges **and** payouts enabled (`stripe_payments.py:376-381`).

### The sandbox may allow what a capability doesn't

- **[DOCS]** "**Sandboxes might not enforce some capabilities.**" [Account capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2) — 2026-10-19

---

## 6. The events a platform must handle for its clubs

### Every Connect platform needs a Connected-accounts endpoint; a sandbox needs its own

- **[DOCS]** "Todas las integraciones Connect **deben** establecer un punto de conexión del webhook para escuchar los
  eventos de Connect" (served in Spanish: every Connect integration *must*); "You must define separate webhook endpoints
  for your sandbox accounts." [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-19
- **[MEASURED]** None on the sandbox — [`stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination`](stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination).

### A v2 club account sends v1 events to Connected accounts and v2 events to Your account

- **[DOCS]** "**v2 `Events` use the Your account scope, while v1 `Events` use the Connected accounts scope**, even when
  triggered by the same v2 `Account`." "**We recommend** setting up new endpoints to listen to v2 events."
  [Migrate to Accounts v2](https://docs.stripe.com/connect/accounts-v2/migrate-integration) — 2026-10-19
- **[DOCS]** For v2 accounts: "listen for v2.core.account[requirements].updated events. **Don't listen for the
  `account.updated` v1 event.**" [Billing + Connect](https://docs.stripe.com/connect/integrate-billing-connect) — 2026-10-19
  (the Connect webhooks page still lists `account.updated` "for all connected accounts").
- **[MEASURED]** `stripe` · `GET /v2/core/events?object_id=acct_1US95f5y1DMwE3zY` · 2026-10-19: 20 events in the
  platform's context — `…[configuration.merchant].capability_status_updated`, `…[requirements].updated`,
  `…[identity].updated`. `stripe-club` · `GET /v1/events?type=account.updated`: `evt_1USCSP5y1DMwE3zYWSetoQfO` and
  more, `api_version: 2026-09-30.endive`.

### Capability changes arrive as their own v2 event

- **[DOCS]** Listen for `v2.core.account[configuration.merchant].capability_status_updated`; "`data.updated_capability`
  identifies the capability." [Track onboarding (v2)](https://docs.stripe.com/connect/track-account-onboarding?dashboard-or-api=api&accounts-namespace=v2) — 2026-10-19

### The Connect events Stripe calls important

- **[DOCS]** `account.application.deauthorized` "Occurs when a connected account disconnects from your platform. You
  can use it to trigger cleanup"; `account.external_account.updated` "can impact payouts"; `account.updated`;
  `payout.failed` — "the external account involved is disabled, and no automatic or manual payouts can be processed";
  `person.updated`; `payment_intent.succeeded`. [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-19;
  disputes: "listen for the `charge.dispute.created` event on a connected account."
  [Embedded integration](https://docs.stripe.com/connect/build-full-embedded-integration) — 2026-10-19
- Code reads five `payment_intent.*` kinds, `charge.updated`, `account.updated`, and drops the rest
  (`stripe_notices.py:114-134`).

### A Connect event names the club at its top level

- **[DOCS]** "Each event for a connected account contains a top-level `account` property." [Connect webhooks](https://docs.stripe.com/connect/webhooks);
  "Connect events include both the `context` and `account` fields." [Changelog](https://docs.stripe.com/changelog/basil/2025-04-30/additional-context-organization-events) — 2026-10-19

### A live Connect endpoint also receives test events

- **[DOCS]** "**Your production webhook URLs receive both live and test webhooks** … **We recommend** that you check the
  `livemode` value." [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-19. Code: no `livemode` under
  `backend/app` (grep, 2026-10-19).

### Testing Connect notices on a laptop

- **[DOCS]** `stripe listen --forward-connect-to …`; `stripe trigger --stripe-account {{ID}} {{EVENT}}`.
  [Connect webhooks](https://docs.stripe.com/connect/webhooks) — 2026-10-19

---

## 7. Disconnection, and a club Rakieta can no longer reach

### A disconnected club makes Rakieta's key fail for it

- **[DOCS]** `platform_api_key_expired`: "This occurs if your platform has generated a new key **or the connected
  account has been disconnected from the platform.**" `account_invalid`: the `Stripe-Account` ID "isn't valid";
  `capability_not_active`; `payouts_not_allowed`. [Error codes](https://docs.stripe.com/error-codes) — 2026-10-19
- Code: an authentication or permission error is "transient … the same request, retried, is the remedy"
  (`stripe_payments.py:71-77`, `:641-654`; `backend/app/modules/payments/domain/errors.py:15-25`);
  `account.application.deauthorized` is dropped (`stripe_notices.py:134`).

### Not found: what becomes of a hold or refund on a club Rakieta can't reach

- **[ABSENT]** Whether an uncaptured PaymentIntent on a removed account can still be captured or cancelled, or just
  lapses; whether a refund can still be made. Looked in managing-individual-accounts, platform-controls, connect/webhooks,
  error-codes, connect/charges, support *Platform controls* — 2026-10-19.

### Not found: whether a hold can be taken, or a refund made, after charges are disabled

- **[ABSENT]** Capture of a `requires_capture` payment after `charges_enabled` turns false. Looked in
  handling-api-verification, account-capabilities, managed-risk, connect/charges, error-codes — 2026-10-19. Refunds:
  [`gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried`](gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried) (2026-10-08).

---

## Pitfalls

Seeds for the Breakers, each with the Stripe source that says what goes wrong.

### P1 · Treating a removed or blocked club as Stripe being down

A removed club allows no API calls ([individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts));
the key fails with `platform_api_key_expired` ([error codes](https://docs.stripe.com/error-codes)). The code retries
such errors as an outage, drops `account.application.deauthorized`, and keeps the club *ready* (§7). Its holds, takes,
refunds and payouts are asked again indefinitely (unverified how often the outbox retries); holds lapse at
`capture_before`. Stripe's event exists "to trigger cleanup" ([Connect webhooks](https://docs.stripe.com/connect/webhooks)).

### P2 · Calling the club ready from the return URL or a stale read

"It doesn't mean that all information has been collected" ([onboard](https://docs.stripe.com/connect/saas/tasks/onboard)).
Rakieta reads after every link and notice; a lost notice is caught only when the desk next asks for a link
(`payments_account.py:84-98`).

### P3 · Collecting only what is due now, then losing payouts mid-season

The default is `currently_due`; up-front "avoids … issues due to missed deadlines"
([hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding)); payouts stop first at a deadline
([verification](https://docs.stripe.com/connect/handling-api-verification)). *Ready* needs both, so the club leaves the
decks while its holds still stand on its account.

### P4 · Listening for the club's account in the wrong scope

v2 account events go to **Your account** ([migrate](https://docs.stripe.com/connect/accounts-v2/migrate-integration));
a v2 subscription under Connected accounts receives nothing. Rakieta relies on v1 `account.updated` alone, which one
Stripe guide says not to use for v2 accounts ([billing + Connect](https://docs.stripe.com/connect/integrate-billing-connect)).

### P5 · Forgetting the club has a full Dashboard of its own

The club can refund, cancel or capture a hold, answer disputes, enable payment methods and add Radar rules on
Rakieta's payments ([Dashboard](https://docs.stripe.com/connect/stripe-dashboard),
[capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2),
[recommendations](https://docs.stripe.com/connect/integration-recommendations)); the code drops refund and dispute
events ([`stripe-sandbox.md` D6](stripe-sandbox.md#differences)).

### P6 · Planning to hold a club's payouts on a Stripe-liable account

"You can't pause payments or payouts" ([risk](https://docs.stripe.com/connect/risk-management)); the club can still pay
itself out ([`gaps-CLUBMONEY.md` §5](gaps-CLUBMONEY.md#5-a-payout-rakieta-asks-of-stripe-r-clubmoney-19)); a new
account pays out **daily** (§1). The club is paid before the game unless something changes it.

### P7 · Choosing the configuration after the first live club

Responsibilities and the Dashboard type can't change ([configuration](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration),
[hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding)): any later change means a new account per club.

### P8 · Handing out, or letting something preview, an onboarding link

Single use, never by email or text; a preview spends it ([hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding)).
Rakieta emails its own `/payments/continue` — keep it that way.

### P9 · Trusting a sandbox proof about a capability

"Sandboxes might not enforce some capabilities" ([capabilities](https://docs.stripe.com/connect/account-capabilities?accounts-namespace=v2)).

### P10 · Mixing live and test notices on the live endpoint

Production Connect endpoints get test events too; check `livemode` ([Connect webhooks](https://docs.stripe.com/connect/webhooks)).
Rakieta never reads it; what each handler does with a test account's notice under live keys is unverified.

### P11 · Going live without the platform's Connect switches

Branding is required, live URLs must be HTTPS ([hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding)),
and v2 links fail with `accounts_v2_access_blocked` where v2 isn't enabled ([v2 links](https://docs.stripe.com/api/v2/core/account-links/create)).
The sandbox platform reads `charges_enabled: false` ([`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account)).

### P12 · Prefilling the wrong kind of business

Rakieta prefills `company` (`stripe_payments.py:326`), so REGON, owners and a representative follow (§5). Many venues
are sole traders, associations or city units ([`local-market.md#what-a-polish-club-must-supply-to-stripe`](local-market.md#what-a-polish-club-must-supply-to-stripe));
after the first link Rakieta can't rewrite it ([hosted onboarding](https://docs.stripe.com/connect/hosted-onboarding)).

---

## Checks

- **K1** Does the rule assume a fees, losses or Dashboard setting other than the code's? None can change later.
- **K2** Is *ready* read from Stripe after every return and every notice, never from the return URL?
- **K3** When a ready club stops being ready, what happens to its held shares, and who is told? Are *payouts stopped*
  and *charges stopped* treated apart?
- **K4** When Rakieta removes a club or Stripe rejects it, does the club leave the decks, do its calls stop being retried
  as an outage, and is it said what becomes of holds and refunds owed?
- **K5** Is every read and write of a share made on the club's account, and does the phone confirm with `stripeAccountId`?
- **K6** Does the rule survive the club acting in its own Dashboard: a refund, a cancelled or taken hold, a dispute
  answer, BLIK switched on, a Radar rule?
- **K7** When a refund or dispute exceeds the club's balance, does the rule say the club pays, as Stripe does, and what
  the player sees meanwhile?
- **K8** Does any rule promise to hold or time the club's payouts? Rakieta can't pause them, and new accounts pay daily.
- **K9** Is the onboarding link minted only for the signed-in desk, never sent, and replaced through the refresh URL?
- **K10** Are requirements collected up front, and does the rule plan for a deadline that lands while games are booked?
- **K11** Does the Connected-accounts endpoint subscribe to every event the rule needs — `account.updated`,
  `account.application.deauthorized`, `payout.failed`, `charge.dispute.created`, `refund.failed` — and is there a
  Your-account destination for any v2 account event used?
- **K12** In live mode, are test notices recognised by `livemode` and kept from moving anything?
- **K13** Before the first live club: v2 enabled on the live platform, branding set, HTTPS URLs, platform activated?
- **K14** Does any sandbox proof depend on a capability that isn't active yet?
- **K15** Can a club that isn't a company finish onboarding, given that Rakieta prefills *company*?
