# Stripe sandbox — what it actually holds

What the Rakieta sandbox holds on 2026-10-19, read through the two Stripe servers after running the
provider contract tests against it, compared with what the code at `9ab0ea5b` expects. Every
`[MEASURED]` line names the object, the server it was read through (`stripe` = the platform,
`stripe-club` = the test club's connected account) and the date. Amounts are in złoty; Stripe
stores grosze. The test club account is shared by every agent and walk: judge each object by its
own ID, never by a balance.

Sources: the four Stripe tools only (`get_stripe_account_info` / `list_available_accounts_or_orgs`,
`stripe_api_search`, `stripe_api_details`, `stripe_api_read`, `search_stripe_documentation`); no
write tool was used.

## 1. Mode

### The platform server is the Rakieta sandbox, in test mode

[MEASURED] `stripe` · `list_available_accounts_or_orgs` → one account, `acct_1US89K5y1DB8chHb`,
"Rakieta sandbox", `livemode: false` · 2026-10-19.

### The seller server is the test club's account, in test mode

[MEASURED] `stripe-club` · `get_stripe_account_info` → `acct_1US95f5y1DMwE3zY`, "Robert Club";
`GET /v1/balance` on the same server answers `livemode: false` · 2026-10-19. No server is on a live
account.

## 2. The provider contract run

### The contract run: 51 passed, 5 skipped

[MEASURED] `state.json` `stripe.contract`, run in the copy with `backend/.env` linked in (the test
keys and `STRIPE_TEST_CLUB_ACCOUNT` set, since the club demands ran and charged
`acct_1US95f5y1DMwE3zY`), 2026-10-19 11:02–11:04 UTC:

```
.............s...........................s...s.s.......s                 [100%]
SKIPPED [4] tests/demands/test_payments_demands.py:123: a bank's 3-D Secure check needs a browser in Stripe test mode
SKIPPED [1] tests/demands/test_payments_demands.py:820: paying a club out needs its test account on manual payouts with money available to pay — open item O2 (#548)
51 passed, 5 skipped, 1 warning in 84.20s (0:01:24)
```

The one warning is not printed by `-q -rs`. The fake's half and Stripe's half both ran; only the
five below were not asked of Stripe.

### Four demands skipped: the bank's check needs a browser

[MEASURED] The four demands whose card asks for the bank's check skip in the suite's Stripe phone
(`backend/tests/demands/test_payments_demands.py:122-123`, called from `_saved` at `:176-189`):
`test_a_card_the_bank_checks_waits_for_the_check`, `test_a_bank_that_wants_the_player_present_says_so`,
`test_a_payment_waiting_for_its_player_is_read_with_its_secret`,
`test_a_payment_its_player_confirmed_is_held_to_be_taken`. Each left its setup on the platform at
`requires_action` with a 3-D Secure redirect: `seti_1USEMP5y1DB8chHbsGbYDRCX`,
`seti_1USEMO5y1DB8chHbm8ytDD7X`, `seti_1USEMI5y1DB8chHbHZ4jqaul`, `seti_1USELX5y1DB8chHbexYSC652`
(`stripe`, 2026-10-19). So no payment on the club account was ever made with
`pm_card_authenticationRequired`: the "confirm your payment" path is unproven on the sandbox.

### The payout demand is skipped for Stripe, whatever the account

[MEASURED] `test_a_club_is_paid_out_what_it_is_asked_once_per_key`
(`backend/tests/demands/test_payments_demands.py:812-838`) skips whenever the provider is not the
fake (`:817-821`), so the skip does not test its own stated condition. See *Differences* D3.

## 3. What the run made

### Customers: one per player, carrying nothing but the player's id

[MEASURED] `stripe` · `GET /v1/customers?created[gte]=1792407700` → 26 customers made by the run,
`cus_VTAgWG7DcHmZqh` … `cus_VTAi7A6VcGRw6Q`; each has `email: null`, `name: null`, `phone: null`,
`test_clock: null`, and `metadata.rakieta_player_id` only · 2026-10-19. Matches
`backend/app/modules/payments/infrastructure/stripe_payments.py:192-201` ("Nothing about the person
but their id").

### Setup intents: off-session, cards only

[MEASURED] `stripe` · `GET /v1/setup_intents?created[gte]=1792407700` → 22 setups, every one
`usage: off_session`, `payment_method_types: ["card"]`,
`payment_method_options.card.request_three_d_secure: automatic` · 2026-10-19. By status:

- `succeeded`, card saved (e.g. `seti_1USEM75y1DB8chHbIWnqTBhZ` → `pm_1USEM75y1DB8chHbfBXqHM9F`,
  Visa •••• 4242, `card.country: US`, `cvc_check: pass`);
- `requires_action`, waiting for the bank's check (the four in §2);
- `canceled`, abandoned (`seti_1USELb5y1DB8chHbjRE7giNQ`, no method);
- `requires_payment_method`, nobody confirmed it (`seti_1USELQ5y1DB8chHbxB4WHTAC`, no attempt).

The platform also emits `payment_method.attached` and `setup_intent.created` alongside
`setup_intent.succeeded` (events `evt_1USEM85y1DB8chHbH4o02bUZ`, `evt_1USEM75y1DB8chHbzqEhqYRX`).

### Payments on the test club: manual capture, off-session, on a single-use copy of the card

[MEASURED] `stripe-club` · `GET /v1/payment_intents?created[gte]=1792407700&expand[]=data.latest_charge`
→ 12 payments, every one `capture_method: manual`, `currency: pln`, `payment_method_types: ["card"]`,
`customer: null` (the clone belongs to nobody on the club's account),
`application: ca_VT4JuiojqLY0o3NiUC7dcMvrueSONfGf` (the platform), `application_fee_amount: null`,
description "Padel · Bonarka Arena", statement descriptor `ROBER CLUB` · 2026-10-19. As the
Dashboard would label them:

| Payment | Amount | Status | Dashboard label |
|---|---|---|---|
| `pi_3USELx5y1DMwE3zY14aUf4wv` | 40,00 zł | `requires_capture` | Uncaptured |
| `pi_3USELs5y1DMwE3zY1ZISteUh`, `pi_3USEM05y1DMwE3zY1kxRwJrI`, `pi_3USEML5y1DMwE3zY0NDKI5az` | 40,00 zł each | `succeeded` | Succeeded |
| `pi_3USEMT5y1DMwE3zY0KRL9Il4` | 27,00 zł | `succeeded` | Succeeded |
| `pi_3USEMX5y1DMwE3zY1YRksIue` | 40,00 zł | `succeeded`, 38,24 zł refunded | Partially refunded |
| `pi_3USEMc5y1DMwE3zY0JHlKSUG`, `pi_3USEMi5y1DMwE3zY1J5JiqYr` | 40,00 zł each | `succeeded`, fully refunded | Refunded |
| `pi_3USEM45y1DMwE3zY1jHeYGQR`, `pi_3USEM85y1DMwE3zY0N8xawbM`, `pi_3USEMD5y1DMwE3zY1H4zdf9h` | 40,00 zł each | `canceled` | Canceled |
| `pi_3USEMG5y1DMwE3zY0P5qCp1v` | 40,00 zł | `requires_payment_method` | Incomplete |

Every authorised charge reads `extended_authorization.status: disabled`,
`incremental_authorization.status: unavailable`, `multicapture.status: unavailable`,
`overcapture.status: unavailable`, `three_d_secure: null`.

### Every Visa hold lasted exactly 7 days

[MEASURED] `stripe-club` · every authorised charge above has
`payment_method_details.card.capture_before = created + 604 800 s` — 7 days to the second. Example:
`pi_3USELx5y1DMwE3zY14aUf4wv` created 2026-10-19 11:03:41 UTC, `capture_before` 2026-10-26
11:03:41 UTC; its charge `ch_3USELx5y1DMwE3zY11neAJGZ`, Visa •••• 4242, made off-session on a clone
with `cvc_check: pass` · 2026-10-19.

[DOCS] https://docs.stripe.com/payments/place-a-hold-on-a-payment-method (read 2026-10-19): Visa
card-not-present, merchant-initiated "5 days*" ("The exact authorization window is 4 days and 18
hours"), customer-initiated "7 days"; and "Stripe and the card network classify transactions as MIT
or CIT based on signals of cardholder participation, not solely on API parameters like
`off_session`. For example, a payment with `off_session: true` might still be classified as a CIT
if a CVC is present, resulting in the CIT authorization window instead." The same page: "You need
to capture the funds before the authorization expires" (a requirement), and `capture_before` "on
the charge indicates when the authorization expires".

### A card refused off-session: decline code and advice

[MEASURED] `stripe-club` · `pi_3USEMG5y1DMwE3zY0P5qCp1v`, 40,00 zł, card •••• 0341
(`pm_card_chargeCustomerFail`, cloned as `pm_1USEMG5y1DMwE3zYNIEUACzA`): status
`requires_payment_method`, `payment_method: null`, `last_payment_error.code: card_declined`,
`decline_code: generic_decline`, `advice_code: try_again_later`, `network_decline_code: "01"`;
charge `ch_3USEMG5y1DMwE3zY0vKtkfxM` `status: failed`, `outcome.type: issuer_declined` · 2026-10-19.
The adapter reads exactly this as a decline with `generic_decline`
(`stripe_payments.py:519-541`); `advice_code` is not read.

### Stripe's fee on a share: 2,30 zł on 40 zł with Stripe's US test card

[MEASURED] `stripe-club` · balance transactions of two captured shares, both
`fee_details: [stripe_fee "Stripe processing fees"]`, `status: pending`,
`available_on` 2026-10-26 00:00 UTC · 2026-10-19:

| Balance transaction | Charge | Amount | Fee | Net |
|---|---|---|---|---|
| `txn_3USEMX5y1DMwE3zY1B9S1C47` | `ch_3USEMX5y1DMwE3zY1lrc899G` | 40,00 zł | 2,30 zł | 37,70 zł |
| `txn_3USEMT5y1DMwE3zY05DNMjmZ` | `ch_3USEMT5y1DMwE3zY0Xq1PAHI` | 27,00 zł | 1,88 zł | 25,12 zł |

Both are 3,25 % + 1 zł, the fake's price for a card from outside Europe
(`backend/app/modules/payments/infrastructure/fake_payments.py:109-114`, `fee_on` at `:128-133`
gives 230 and 188 grosze exactly), because 4242 is US-issued (`card.country: US`). The fee is on
the club's account; no application fee is taken.

### Refunds: exactly the amounts asked, succeeded at once

[MEASURED] `stripe-club` · `GET /v1/refunds?created[gte]=1792407700` → 3 refunds, all
`status: succeeded`, `reason: null`, `destination_details.card.type: refund` (not a reversal),
each with its acquirer reference available · 2026-10-19:

| Refund | Payment | Amount |
|---|---|---|
| `re_3USEMX5y1DMwE3zY1Boz4mHQ` | `pi_3USEMX5y1DMwE3zY1YRksIue` | 38,24 zł of 40,00 zł |
| `re_3USEMc5y1DMwE3zY0JLlLobG` | `pi_3USEMc5y1DMwE3zY0JHlKSUG` | 40,00 zł |
| `re_3USEMi5y1DMwE3zY11GGOqFA` | `pi_3USEMi5y1DMwE3zY1J5JiqYr` | 40,00 zł (asked twice with one key, made once) |

For each, the club account emitted `charge.refunded`, `refund.updated` and `charge.refund.updated`
(e.g. `evt_3USEMi5y1DMwE3zY1Bw2cqr2`, `evt_3USEMi5y1DMwE3zY1zTt3jBa`,
`evt_3USEMi5y1DMwE3zY18OMQzvN`), each `pending_webhooks: 0`.

[DOCS] https://docs.stripe.com/refunds (read 2026-10-19): "A refund can fail if the customer's bank
or card issuer can't process it … This process can take up to 30 days from the post date." "In the
rare instance that a refund fails, Stripe notifies you using the `refund.failed` event … If this
occurs, you need to arrange an alternative way to provide your customer with a refund."

### No payouts; the club's money is pending until 26 October

[MEASURED] `stripe-club` · `GET /v1/payouts` → empty; `GET /v1/balance` → available 0,00 zł,
pending 133,08 zł (card) · 2026-10-19. The run's charges become available on 2026-10-26 00:00 UTC
(`available_on` above), 7 days after capture.

### What the run left behind on the shared account

[MEASURED] The run leaves, every time: an uncaptured 40,00 zł hold on the club account
(`pi_3USELx5y1DMwE3zY14aUf4wv`, lapses 2026-10-26 11:03 UTC, from
`test_an_authorisation_reports_its_last_moment`, `test_payments_demands.py:498`); four setups at
`requires_action`; and a new, never-onboarded connected account from
`test_a_new_club_account_is_not_ready_and_has_an_onboarding_link` (`:378`) — this run's is
`acct_1USELi5y1DCSZFum`, "Bonarka Arena", `disabled_reason: requirements.past_due`, read as
*not started* by `read_club_account` (`stripe_payments.py:371-391`) · `stripe`, 2026-10-19.

## 4. Configuration

### No webhook endpoint and no event destination

[MEASURED] `stripe` · `GET /v1/webhook_endpoints` → empty; `GET /v2/core/event_destinations` →
empty · 2026-10-19. The newest platform event (`evt_1USEM85y1DB8chHb4Tf7DeRH`,
`setup_intent.succeeded`) read `pending_webhooks: 2` at 11:04 UTC and `0` minutes later, so two
receivers that are not registered endpoints took it — most likely `stripe listen` sessions
(unverified). Every club-account event read shows `pending_webhooks: 0`.

[DOCS] https://docs.stripe.com/webhooks, *Create an event destination for Connect* (read
2026-10-19): "Register an event destination for **Connected accounts** to receive events for
resources that belong to your connected accounts. Examples include direct charges, … payout
failures, and legacy snapshot connected-account lifecycle updates, such as onboarding,
verification, external-account changes, and account disconnections."
https://docs.stripe.com/connect/accounts-v2/migrate-integration (read 2026-10-19): for a v2
account, "v1 `account.updated` events" are in the **Connected accounts** scope and v2 events in
**Your account**; "We recommend setting up new endpoints to listen to v2 events."

### API versions: the SDK pins dahlia, the account renders endive

[MEASURED] The lock pins stripe-python 15.6.1 (`backend/pyproject.toml:39`,
`backend/poetry.lock:3727-3735`), whose `stripe/_api_version.py` says
`CURRENT = "2026-08-26.dahlia"`; the code sets no API version of its own (grep for `api_version`,
`stripe_version` or `Stripe-Version` under `backend/app` finds nothing). Every event read on both
servers carries `api_version: "2026-09-30.endive"` · 2026-10-19.

[DOCS] https://docs.stripe.com/api-versions (read 2026-10-19): "The current version of the API is
**2026-09-30.endive**"; "When you retrieve an event through the API, the structure of the event
that Stripe returns is defined by the account's default API version at the time the event
occurred"; "Webhook endpoints can also pin their own API version"; majors twice a year start "with
an API version containing breaking changes". https://docs.stripe.com/sdks/set-version: recent
stripe-python "use the API version that was latest at the time your version of stripe-python was
released". https://docs.stripe.com/webhooks/versioning: "Each webhook endpoint has a specific API
version. Stripe uses that version to structure the event payloads it sends to the endpoint."

### The test club account: full Dashboard, the club pays the fees, Stripe covers losses

[MEASURED] `stripe` · `GET /v1/accounts/acct_1US95f5y1DMwE3zY` · 2026-10-19: `type: standard`,
`country: PL`, `default_currency: pln`, `business_type: company`, name "Rober Club" (Dashboard
display name "Robert Club"), `charges_enabled: true`, `payouts_enabled: true`,
`details_submitted: true`, requirements and future requirements empty, `controller.fees.payer:
account`, `controller.losses.payments: stripe`, `controller.requirement_collection: stripe`,
`controller.stripe_dashboard.type: full`, `metadata.rakieta_club_id:
9b98e746-368a-4a9f-b3ee-3efc83f1900a` (opened by the product's `open_club_account`, then
onboarded by hand). `GET /v2/core/accounts/acct_1US95f5y1DMwE3zY?include=defaults,requirements`:
`applied_configurations: ["merchant"]`, `dashboard: full`, `defaults.currency: pln`,
`locales: ["pl-PL"]`, `responsibilities: {fees_collector: stripe, losses_collector: stripe,
requirements_collector: stripe}`. Reading `configuration.merchant` through the platform server is
refused ("Permission denied … mconf_test_…"). This agrees with what the code asks for
(`stripe_payments.py:317-347`) and with `read_club_account`'s *ready*.

### The test club's capabilities: card payments and nine more

[MEASURED] same read: `capabilities` = `card_payments`, `blik_payments`, `bancontact_payments`,
`eps_payments`, `ideal_payments`, `klarna_payments`, `link_payments`, `pay_by_bank_payments`,
`revolut_pay_payments`, `transfers`, all `active` · 2026-10-19.

### The test club's payouts are manual, with a 7-day delay

[MEASURED] same read: `settings.payouts.schedule = {interval: manual, delay_days: 7}`,
`debit_negative_balances: true` · 2026-10-19. The never-onboarded accounts carry no payout settings.

### The test club's bank account: Polish, in złoty

[MEASURED] same read: `external_accounts` → `ba_1US9LA5y1DMwE3zYHPe7QQUm`, STRIPE TEST BANK,
`country: PL`, `currency: pln`, last four 2874 (the walk's IBAN), `default_for_currency: true`,
`status: new`, `available_payout_methods: ["standard"]` · 2026-10-19.

### The platform account

[MEASURED] `stripe` · `GET /v1/accounts/acct_1US89K5y1DB8chHb` · 2026-10-19: `country: PL`,
`default_currency: pln`, `charges_enabled: false`, `details_submitted: false`, own payouts
`daily`, `delay_days: 7`. Its connected accounts (`GET /v1/accounts`): seven — the onboarded test
club; four never-onboarded club accounts the product opened (`acct_1US8x15y1DVGcQql`,
`acct_1USA5z5y1DA5YwZc`, `acct_1USA7S5y1DjBnxJM`, `acct_1USELi5y1DCSZFum`); and Stripe's two sample
"Test connected account"s (`acct_1US8XX5y1Dlh7WsG` full Dashboard; `acct_1US8XX5y1DflbnVu`
Express, where the platform pays fees and bears losses).

## 5. What the code expects

### The calls the adapter makes, and on which account

From `backend/app/modules/payments/infrastructure/stripe_payments.py` at `9ab0ea5b`:

| Call | Account | Money-deciding parameters | Lines |
|---|---|---|---|
| `customers.create` | platform | metadata only | 192-201 |
| `setup_intents.create` | platform | `usage: off_session`, `payment_method_types: [card]` | 203-222 |
| `payment_methods.detach` | platform | — | 298-313 |
| `v2.core.accounts.create` | platform | `dashboard: full`, `fees_collector`/`losses_collector: stripe`, `card_payments` requested | 317-347 |
| `v2.core.account_links.create` | platform | `account_onboarding`, `merchant` | 349-369 |
| `accounts.retrieve` (v1) | platform | ready = charges and payouts enabled | 371-391 |
| `payment_methods.create` (clone) | club | `customer`, `payment_method` | 466-483 |
| `payment_intents.create` | club | `capture_method: manual`, `off_session: true`, `confirm: true`, `pln`, expand `latest_charge` | 485-542 |
| `payment_intents.retrieve` / `capture` | club | expand `latest_charge.balance_transaction` (the fee) | 544-567 |
| `payment_intents.cancel` | club | — | 569-581 |
| `refunds.create` | club | exact `amount`, no `reason` | 583-609 |
| `payouts.list` / `payouts.create` | club | `amount`, `pln`; `balance_insufficient` → not available yet | 393-462 |

Every write carries the caller's idempotency key; the SDK retries twice on the network
(`:67`, `:175-179`).

### The notices the code reads, and the endpoint each comes through

`backend/app/modules/payments/infrastructure/stripe_notices.py` (five-minute signature tolerance,
`:52`), mounted at `POST /api/v1/webhooks/stripe` and `/stripe-connect`
(`backend/app/modules/payments/presentation/webhook_routes.py:39-64`), each over its own secret,
both required only when deployed (`backend/app/core/config.py:895-912`):

- platform: `setup_intent.succeeded` (`:102-105`), `payment_method.automatically_updated`
  (`:106-113`);
- connected accounts, naming the account at the top level:
  `payment_intent.amount_capturable_updated`, `.succeeded`, `.canceled`, `.payment_failed`,
  `.requires_action` (`:61-69`, `:114-119`), `charge.updated` as *the fee is ready* (`:120-129`),
  `account.updated` (`:130-133`);
- every other kind is acknowledged and dropped (`:134`; `application/notices.py:105-106`).

## Differences

**D1 · No endpoint receives any notice the code reads.** The code reads two Stripe endpoints and
nine event types (§5), and a deployed environment refuses to start without both secrets
(`config.py:895-912`). The sandbox has no webhook endpoint and no event destination in either
scope (§4); the platform's events reached two unregistered receivers, and the club account's
events show no receiver at all. On the sandbox the product hears from Stripe only while a person
keeps `stripe listen --forward-to … --forward-connect-to …` running, as `stripe.walk` step 2 says;
without the Connect half, a club's onboarding never reads *ready* and a held, taken or refused
share is never re-read from its notice.

**D2 · The API version is chosen by the SDK, and the account renders a newer major.** The code
pins no version; stripe-python 15.6.1 sends `2026-08-26.dahlia` on every call, while the account's
default — the shape of every event read, and of any endpoint created without `api_version` — is
`2026-09-30.endive`, the start of a new major line that "can require changes". The notice reader
uses only `id`, `type`, `account`, `data.object.id`, `customer` and `payment_intent`, so nothing
broke in this run; the endive changelog was not checked against those fields (unverified).

**D3 · The test club is on manual payouts, but paying a club out is still unproven.** The code sets
no payout schedule and says accounts are opened "on Stripe's own schedule" until open item O2
(`stripe_payments.py:420-425`); the onboarded test club reads `interval: manual`,
`delay_days: 7` — who set it is not visible through the API. The payout demand skips for Stripe
unconditionally (`test_payments_demands.py:817-821`), though half its stated condition (manual
payouts) holds; the other half (money available) is false today — 0,00 zł available, 133,08 zł
pending — and the run's shares become available on 2026-10-26. No payout exists on the account,
so `pay_out`, `payouts` and a failed payout have never been seen on the sandbox; the code
subscribes to no `payout.*` notice and reads the list on demand
(`backend/app/modules/payments/application/payouts.py:131`).

**D4 · On the sandbox a Visa hold always lasts 7 days, never 4 days 18 hours.** The fake models a
Visa hold made without its player as 4 days 18 hours (`fake_payments.py:118-121`), and the
holding lead (4 days) and reach margin (6 hours) are sized for that window
(`backend/app/modules/payments/domain/seat_charge.py:87-100`). Every off-session Visa hold on the
sandbox came back with `capture_before` exactly 7 days out — Stripe classifies by signals, and a
clone with a CVC check reads as customer-initiated. The product reads `capture_before`
(`stripe_payments.py:130-142`), so it follows Stripe; but a walk on the sandbox cannot produce the
short Visa window, and every *the hold won't reach the cut-off* scene the fake builds on it is
reachable only on the fake.

**D5 · The sandbox's everyday card costs the outside-Europe fee.** Stripe's 4242 card is
US-issued, so Stripe keeps 3,25 % + 1 zł: 2,30 zł on a 40 zł share, 1,88 zł on 27 zł. The fake
gives a card the EU personal price (1,5 % + 1 zł = 1,60 zł on 40 zł) unless told otherwise
(`fake_payments.py:20-23`, `:109-114`). So a late leaver whose seat is taken gets back 37,70 zł on
the sandbox with 4242, where the same scene on the fake returns 38,40 zł; a walk's boxes must take
the fee from the payment's own balance transaction. The demand's 38,24 zł refund
(`test_payments_demands.py:760-783`) is not 40 zł less the 2,30 zł actually kept on that payment
(`ch_3USEMX5y1DMwE3zY1lrc899G`); a Polish-issued test card, which would carry the EU price, was not
found in Stripe's docs this session (unverified).

**D6 · Stripe reports each refund's progress; the code hears none of it.** For each refund the
club account emitted `charge.refunded`, `refund.updated` and `charge.refund.updated`; the code
drops all three, and records a refund as given whatever status Stripe answered
(`backend/app/modules/payments/application/handlers/settle_seat_charges.py:142-161`;
`seat_charge.py:733-754` keeps no status). Stripe documents that a refund can fail up to 30 days
later and is announced by `refund.failed`, after which the seller must pay the player another way.
All three sandbox refunds were `succeeded` at once, so the sandbox cannot show a failed refund
either way.

**D7 · The test club can take BLIK and eight more methods the code says it doesn't use.** The code
requests only `card_payments` (`stripe_payments.py:337-341`), creates every payment and setup with
`payment_method_types: ["card"]`, and says BLIK "waits on Stripe (open item O1)" (`:211-212`). The
onboarded club holds ten active capabilities, `blik_payments` among them. The capability does not
answer O1 (saving BLIK for a later off-session hold), but the club's own full Dashboard can already
take BLIK, Klarna and others outside Rakieta.
