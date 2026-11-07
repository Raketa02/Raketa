# Stripe webhooks — signatures, delivery, scopes and the events this product needs

What Stripe documents about webhooks for the way Raketa uses it: **direct charges** on each club's **Accounts v2**
connected account (full Dashboard, Stripe collects fees and covers losses), a card saved on the **platform** and
cloned onto the club's account per share, shares **held** off-session with manual capture, then **taken** or
**released**, exact refunds, payouts on demand, złoty, Poland. Read 2026-10-19 from docs.stripe.com (fetched as
Markdown) and Stripe's documentation search; sandbox objects read through `stripe` (platform) and `stripe-club`
(test club `acct_1US95f5y1DMwE3zY`) the same day. No write tool was used.

**Not redone here** — see [`stripe-sandbox.md`](stripe-sandbox.md): no endpoint or event destination exists in either
scope (`#no-webhook-endpoint-and-no-event-destination`, D1); the SDK pins `2026-08-26.dahlia` while events render
`2026-09-30.endive` (`#api-versions-the-sdk-pins-dahlia-the-account-renders-endive`, D2); the dropped refund notices
(D6); the notices the code reads (`#the-notices-the-code-reads-and-the-endpoint-each-comes-through`).

*Code:* lines read the code at `9ab0ea5b` with `path:line`; they are not facts about Stripe.

---

## 1. Signatures

### Every notice is signed with its endpoint's secret, over the timestamp and the raw body

- **[DOCS]** "Stripe signs every webhook event by including a signature in the `Stripe-Signature` header"; HMAC
  SHA-256, "ignore all schemes that aren't `v1`". "Without verification, an attacker could send fake webhook events
  to your endpoint to trigger actions like … modifying records. Always verify". Requirement: "Stripe requires the raw
  body of the request to perform signature verification. … Any manipulation to the raw body of the request causes the
  verification to fail." [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19

### Each endpoint and each mode has its own secret; the CLI's is not the Dashboard's

- **[DOCS]** "Stripe generates a unique secret key for each endpoint. If you use the same endpoint for both test and live
  API keys, the secret is different for each one." [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19
- **[DOCS]** "The most common cause is using the wrong endpoint secret. The secret for a CLI-forwarded endpoint is
  different from the secret for a Dashboard-managed endpoint—don't mix them up." [manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints)
  — read 2026-10-19. An API-created destination returns its secret once: "Public API clients cannot retrieve it later."
  [create an event destination](https://docs.stripe.com/api/v2/core/event-destinations/create) — read 2026-10-19

### The libraries' tolerance is five minutes, and zero turns the check off

- **[DOCS]** "Our libraries have a default tolerance of 5 minutes between the timestamp and the current time. … Use
  Network Time Protocol (NTP) to make sure that your server's clock is accurate". "Don't use a tolerance value of `0`.
  Using a tolerance value of `0` disables the recency check entirely." [webhooks](https://docs.stripe.com/webhooks)
  (*Preventing replay attacks*) — read 2026-10-19
- *Code:* stripe-python 15.6.1's `verify_header` defaults `tolerance=None` and checks only the past:
  `if tolerance and timestamp < time.time() - tolerance` (SDK `stripe/_webhook.py:132-195`); Raketa passes 300
  (`backend/app/modules/payments/infrastructure/stripe_notices.py:52`, `:86-88`).

### A retry is signed afresh

- **[DOCS]** "If Stripe retries an event …, then we generate a new signature and timestamp for the new delivery
  attempt." [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19. A five-minute tolerance never refuses a retry.

### Rolling a secret leaves two signatures for up to 24 hours

- **[DOCS]** Recommendation: "roll (change) secrets periodically, or when you suspect a compromised secret"; the old one
  can stay "for up to 24 hours … Stripe generates one signature per secret until expiration." [webhooks](https://docs.stripe.com/webhooks)
  — read 2026-10-19. *Code:* the SDK accepts any matching `v1` signature (`stripe/_webhook.py:178-186`).

### Stripe asks for IP allowlisting beside the signature

- **[DOCS]** "Use both of these protections: **IP allowlisting** … Configure your server or firewall to only accept webhook
  requests from these addresses. **Signature verification** …" [webhooks](https://docs.stripe.com/webhooks); list at
  https://stripe.com/files/ips/ips_webhooks.txt ([IP addresses](https://docs.stripe.com/ips)) — read 2026-10-19

---

## 2. Delivery

### Answer 2xx quickly, before the work

- **[DOCS]** "Your endpoint must quickly return a successful status code (`2xx`) before any complex logic that could
  cause a timeout." Recommendation: "process incoming events with an asynchronous queue. You might encounter
  scalability issues if you choose to process events synchronously." [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19

### Every non-2xx, redirect, TLS error or timeout is a failure

- **[DOCS]** "We consider redirect responses to webhook requests as failures"; `4xx` "when the server detects an error
  (`400`)"; `5xx`; "Stripe requires TLS version `v1.2` or higher"; "(Timed out) … defer complex logic and return a
  successful response immediately". [webhooks](https://docs.stripe.com/webhooks) (*Fix HTTP status codes*) — read 2026-10-19

### How long Stripe waits for an answer is not documented

- **[ABSENT]** No number of seconds on [webhooks](https://docs.stripe.com/webhooks),
  [manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints),
  [how events work](https://docs.stripe.com/events/how-events-work) or in the documentation search — looked 2026-10-19.

### Retries: three days in live mode, three tries over a few hours in a sandbox

- **[DOCS]** "Stripe attempts to deliver events to your destination for up to three days with an exponential back off in
  live mode. … We retry event deliveries created in a sandbox three times over the course of a few hours. If your
  destination has been disabled or deleted when we attempt a retry, we prevent future retries of that event."
  [webhooks](https://docs.stripe.com/webhooks) (*Automatic retries*) — read 2026-10-19
- **[ABSENT]** Whether Stripe disables a failing endpoint itself is not on those pages. The search's own answer: Stripe
  emails owners, admins and developers "when webhooks have several failures"; "it may take several days" (a search
  answer, not a page) — looked 2026-10-19.

### Resending by hand does not stop the retries

- **[DOCS]** Dashboard **Resend** for "up to 15 days", `stripe events resend` for "up to 30 days"; "Manually resending …
  doesn't cancel Stripe's automatic retry behavior". "When your endpoint receives an event you've already processed,
  skip it and return a `200` response to stop further retries." [webhooks](https://docs.stripe.com/webhooks);
  [manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints) — read 2026-10-19

### After an outage: list what failed, within 30 days

- **[DOCS]** List Events with `ending_before` (the last event delivered before the outage), `types`, and
  `delivery_success=false`; "Stripe only returns events created in the last 30 days." [manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints)
  (*Process undelivered events*) — read 2026-10-19
- **[DOCS]** Adding an event type later "affects future delivery only"; a connected account's events are listed with its
  `Stripe-Account` header, "each affected account context separately". [how events work](https://docs.stripe.com/events/how-events-work)
  (*Recover from missing event types*, *Event retention*) — read 2026-10-19

### An event can fail to exist at all

- **[DOCS]** Public preview: "In rare cases, Stripe can fail to generate an `Event` object. … the event is
  irrecoverable"; Stripe sends `v2.core.health.event_generation_failure.resolved` (its example: a lost
  `payment_intent.requires_action`) and says to "poll the relevant API to get the current state". [manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints)
  — read 2026-10-19

### HTTPS in live mode, at most 16 destinations, sandboxes apart

- **[DOCS]** HTTPS is "required in live mode"; "sandbox mode also supports HTTP". "A maximum of 16 event destinations per
  livemode or sandbox account". "You must define separate webhook endpoints for your sandbox accounts". [webhooks](https://docs.stripe.com/webhooks);
  [create an event destination](https://docs.stripe.com/api/v2/core/event-destinations/create); [how events work](https://docs.stripe.com/events/how-events-work);
  [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19

---

## 3. Duplicates and order

### The same event can arrive more than once

- **[DOCS]** "Webhook endpoints might occasionally receive the same event more than once. You can guard against duplicated
  event receipts by logging the event IDs you've processed". [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19

### Sometimes two different events say the same thing

- **[DOCS]** "In some cases, two separate Event objects are generated and sent. To identify these duplicates, use the ID of
  the object in `data.object` along with the `event.type`." — same page. An event-id inbox does not catch these.

### No order is guaranteed, and `created` cannot order them

- **[DOCS]** "Stripe doesn't guarantee the delivery of events in the order that they're generated. … Snapshot events record
  `created` in seconds, so distinct events can share a timestamp. Don't use `created` to determine event order or whether
  you've already processed an event." [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19
- **[MEASURED]** One hold on the test club produced `payment_intent.created`, `charge.succeeded` and
  `payment_intent.amount_capturable_updated` in the same second (`evt_3USEMi5y1DMwE3zY19K0g7T1`, `…1OyFgVzI`,
  `…1Wx4DESj`, all `created` 1792407868) · `stripe-club` · `GET /v1/events` · 2026-10-19

### A snapshot can be stale by the time it is read

- **[DOCS]** "Because this snapshot can be stale by the time your application processes it, fetch the latest version of the
  resource from the API before acting on the data." [how events work](https://docs.stripe.com/events/how-events-work) — read 2026-10-19

---

## 4. The platform's endpoint and the Connected accounts endpoint

### Direct charges' events exist only in the Connected accounts scope

- **[DOCS]** **Your account**: "`v2.core.account.*` events for v2 `Accounts` in your account", "Events for `Customers` in your
  account"; **Connected accounts**: "v1 `account.updated` events for both v1 and v2 `Accounts`", "Direct charges … for
  customers of your connected accounts". [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19
- **[DOCS]** The Connected accounts scope receives "direct charges, Customers and payment methods of connected accounts,
  payout failures, and legacy snapshot connected-account lifecycle updates, such as onboarding, verification,
  external-account changes, and account disconnections. For Accounts v2, this scope only receives snapshot events for
  Account objects". [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19. A webhook endpoint's `connect`
  "Defaults to `false`" (Your account). [create a webhook endpoint](https://docs.stripe.com/api/webhook_endpoints/create)

### A connected account's event names it at the top level, and its object is read as that account

- **[DOCS]** "Each event for a connected account contains a top-level `account` property that identifies the connected
  account. Because the connected account owns the object that triggered the event, you must make API requests for that
  object as the connected account." [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19.
  The Event also has `context`, "Authentication context needed to fetch the event or related object". [Event object](https://docs.stripe.com/api/events/object)
- **[MEASURED]** Events read through the test club's own key carry `context: acct_1US95f5y1DMwE3zY` and no `account`
  (e.g. `evt_3USEMi5y1DMwE3zY1RXEORYv`) · `stripe-club` · 2026-10-19. A Connect-delivered copy could not be seen (D1).

### Accounts v2: the v1 `account.updated` comes to Connected accounts, the v2 events to Your account

- **[DOCS]** "For events triggered by connected accounts, v2 `Events` use the **Your account** scope, while v1 `Events` use
  the **Connected accounts** scope, even when triggered by the same v2 `Account`." Updating the `merchant` configuration
  "emits v1 `account.updated` events". "We recommend setting up new endpoints to listen to v2 events." The v2 events for
  requirements: `v2.core.account[requirements].updated`, `v2.core.account[configuration.<type>].capability_status_updated`.
  [Connect webhooks](https://docs.stripe.com/connect/webhooks?accounts-namespace=v2); [migrate to Accounts v2](https://docs.stripe.com/connect/accounts-v2/migrate-integration);
  [integrate-billing-connect](https://docs.stripe.com/connect/integrate-billing-connect) — read 2026-10-19

### Stripe's pages disagree on where the v2 account events go; the sandbox shows them on the platform

- **[DOCS]** The SaaS-fees page says, for those v2 events, "select **Connected accounts**" with **Thin** payload
  ([integrate-billing-connect](https://docs.stripe.com/connect/integrate-billing-connect)); the Connect and migration pages
  say **Your account**; the search's own answer: "sent to the 'your account' webhook endpoint" — read 2026-10-19.
- **[MEASURED]** `GET /v2/core/events` on the platform holds `v2.core.account[requirements].updated`
  (`evt_test_65VbcKOJskN4zOy8F2H16VbW6g93NJvd1kpceXWgE1gX8a`) and two `…[configuration.merchant].capability_status_updated`
  for `acct_1USELi5y1DCSZFum` (opened by the contract run, 11:04 UTC), each with `context: acct_1US89K5y1DB8chHb` (the
  platform). The platform's 100 newest v1 events hold no `account.updated` · `stripe` · 2026-10-19.

### A production Connect endpoint receives test events too

- **[DOCS]** Recommendation: "your production webhook URLs receive both live and test webhooks. … We recommend that you check
  the `livemode` value when receiving an event webhook to determine whether users need to take action." [Connect webhooks](https://docs.stripe.com/connect/webhooks)
  — read 2026-10-19
- **[ABSENT]** Which secret signs a test event sent to a live Connect endpoint — not on the pages above (looked 2026-10-19).

### On a laptop: `stripe listen`, one secret for both, kept across restarts

- **[DOCS]** `--forward-connect-to`: "The URL that Connect webhook events will be forwarded to. By default, the same URL will
  be used for all snapshot webhook events." "By default, `listen` accepts all snapshot webhook events"; `-e` filters; thin
  events need `--thin-events`. "The webhook signing secret provided will not change between restarts". Events use "your
  account's default API version" unless `--latest`. [CLI listen](https://docs.stripe.com/cli/listen) — read 2026-10-19
- **[DOCS]** `stripe trigger --stripe-account {{CONNECTED_ACCOUNT_ID}} {{EVENT_NAME}}` raises a Connect event.
  [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19

---

## 5. Snapshot and thin events, and the API version

### Thin events are Stripe's recommendation for new integrations

- **[DOCS]** "For new integrations, use thin events. Thin events are unversioned, fully typed in the Stripe SDKs, and let your
  integration fetch the latest resource state"; "If you use Accounts v2, you might listen to both snapshot and thin events";
  a thin destination needs its own endpoint. [how events work](https://docs.stripe.com/events/how-events-work);
  [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19
- **[MEASURED]** v1 events also appear as thin twins, e.g. `v1.setup_intent.succeeded`
  (`evt_test_65VbcK36kYYbo4l3f6R16VbW6g93NJvd1kpceXWgE1gEjw`, `snapshot_event: evt_1USEMh5y1DB8chHbYVShRg0p`) · `stripe` · 2026-10-19

### A snapshot event is shaped by a version fixed when the event is made

- **[DOCS]** "The API version in your account settings when the event occurs dictates the API version, and therefore the
  structure of an Event"; "You can't change Event objects after creation"; test destinations may use the default or the
  latest version. [webhooks](https://docs.stripe.com/webhooks). An endpoint's `api_version`: "Events sent to this endpoint
  will be generated with this Stripe Version instead of your account's default". [create a webhook endpoint](https://docs.stripe.com/api/webhook_endpoints/create).
  Twice a year a release "begins with a breaking-change version". [how events work](https://docs.stripe.com/events/how-events-work) — read 2026-10-19

### Stripe's upgrade path for a snapshot endpoint runs two endpoints on one URL

- **[DOCS]** "Create a new disabled webhook endpoint" with "the same URL … but add a query parameter"; then "every event is sent
  twice: once with the old API version and once with the new one"; old-version copies get "a 400 status to let Stripe
  automatically retry". "To avoid webhook versioning, use thin events." [webhook versioning](https://docs.stripe.com/webhooks/versioning) — read 2026-10-19

### Only subscribe to what the integration needs

- **[DOCS]** Recommendation: "Configure your webhook endpoints to receive only the types of events required by your
  integration. Listening for extra events (or all events) puts undue strain on your server and we don't recommend it."
  [webhooks](https://docs.stripe.com/webhooks) — read 2026-10-19

---

## 6. The events this product's moments produce

### Saving a card (platform)

- **[DOCS]** `setup_intent.succeeded`, `.setup_failed` ("has failed the attempt to setup a payment method"),
  `.requires_action`, `.canceled`; `payment_method.attached`, `.detached`, `.automatically_updated` ("details are
  automatically updated by the network"). [event types](https://docs.stripe.com/api/events/types) — read 2026-10-19
- **[MEASURED]** Platform, 100 newest v1 events (06:34–11:04 UTC): 29 `customer.created`, 26 `setup_intent.created`, 17
  `setup_intent.succeeded`, 17 `payment_method.attached`, 8 `setup_intent.requires_action`, 1 `setup_intent.setup_failed`,
  1 `setup_intent.canceled`, 1 `payment_method.detached`; all `livemode: false`, `pending_webhooks: 0` · `stripe` · 2026-10-19
- *Code:* reads `setup_intent.succeeded` and `payment_method.automatically_updated` (`stripe_notices.py:102-113`); the rest
  are `Unheeded` (`:134`). The spec lists `setup_intent.succeeded/setup_failed` (`docs/specs/games-and-fill-in/the-mechanics.md:1901`).

### A share held, taken, released or refused (club's account)

- **[DOCS]** A manual-capture payment completed "triggers the `payment_intent.amount_capturable_updated` event". "If the
  authorization expires before you capture the funds, the funds are released and the payment status changes to
  `canceled`." [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method). Catalogue: `charge.expired`
  "Occurs whenever an uncaptured charge expires"; `charge.captured`; `payment_intent.canceled`, `.payment_failed`,
  `.requires_action`. [event types](https://docs.stripe.com/api/events/types) — read 2026-10-19
- **[DOCS]** Polling "is much less reliable and might trigger rate limits"; on `payment_failed`, "prompt them to provide another
  payment method". [payment status updates](https://docs.stripe.com/payments/payment-intents/verifying-status) — read 2026-10-19
- **[MEASURED]** Test club, 100 newest events (09:01–11:04 UTC): 13 `payment_intent.created`; 12 `charge.succeeded` + 12
  `payment_intent.amount_capturable_updated` (holds); 9 `charge.captured` + 9 `payment_intent.succeeded` (takes); 3
  `payment_intent.canceled` (releases, each carrying the call's idempotency key, e.g. `evt_3USEMD5y1DMwE3zY1w7Y7kwB`); 1
  `payment_intent.payment_failed` + 1 `charge.failed`; 5 each of `refund.created`, `charge.refunded`, `refund.updated`,
  `charge.refund.updated` (the last two with `request.id: null`); 10 each of `account.updated` and `capability.updated`
  (onboarding). Over 30 days, `charge.expired`, `payment_intent.requires_action`, `refund.failed`, `payout.paid`,
  `payout.failed`, `charge.dispute.created`, `account.application.deauthorized` → none · `stripe-club` · 2026-10-19
- *Code:* the five `payment_intent.*` kinds prompt a re-read on the club's account (`stripe_notices.py:61-69`, `:114-119`;
  `backend/app/modules/payments/application/notices.py:143-157`); only *held*, *taken* or *released* readings move a share
  (`backend/app/modules/payments/domain/seat_charge.py:821-829`). `charge.captured`, `charge.expired` are `Unheeded`; a
  lapsed hold is heard through `payment_intent.canceled`.

### The fee kept on a taken share

- **[DOCS]** Under asynchronous capture "The `balance_transaction` … might be `null` immediately after confirmation … listen for
  the `charge.updated` event"; "Our SLA for the charge.updated webhook is 1 hour". [asynchronous capture](https://docs.stripe.com/payments/payment-intents/asynchronous-capture)
  — read 2026-10-19; also `gaps-CLUBMONEY.md#the-fee-is-on-the-charges-balance-transaction-which-may-arrive-after-the-capture`
- **[MEASURED]** `GET /v1/events?type=charge.updated` on the test club → empty for 30 days, after nine manual captures; the fee
  came with the capture (`stripe-sandbox.md#stripes-fee-on-a-share-230-zł-on-40-zł-with-stripes-us-test-card`) · `stripe-club` ·
  2026-10-19. The code's `charge.updated` path (`stripe_notices.py:120-129`) is not reachable on the sandbox.

### Refunds

- **[DOCS]** "At a minimum, Stripe recommends that you listen for the `refund.created` event." "In the rare instance that a
  refund fails, Stripe notifies you using the `refund.failed` event … you need to arrange an alternative way to provide your
  customer with a refund"; the money returns within "up to 30 days". Reasons include `charge_for_pending_refund_disputed`,
  `insufficient_funds` (pending past the expiration window), `lost_or_stolen_card`. `charge.refund.updated` is
  **Deprecated** — "Listen to `refund.updated`". If the available balance is short, a card refund stays pending "until your
  Stripe balance becomes sufficient" — on a direct charge, the club's. [refunds](https://docs.stripe.com/refunds) — read 2026-10-19
- *Code:* every refund kind is `Unheeded`; a refund is recorded from the create call's answer (D6).

### Disputes on a direct charge

- **[DOCS]** `charge.dispute.created`, `.updated`, `.closed` ("`lost`, `warning_closed`, or `won`"), `.funds_withdrawn`,
  `.funds_reinstated` ([event types](https://docs.stripe.com/api/events/types)). "For connected accounts that use direct
  charges, Stripe always attempts to debit disputed amounts from the connected account's balance"; "We recommend setting up a
  webhook to listen to dispute created events." [Connect disputes](https://docs.stripe.com/connect/disputes) — read 2026-10-19
- *Code:* no dispute kind is read and no seat-charge event for one exists under `backend/app/modules/payments`, though the
  PRD has the seat charge "… disputed; folded idempotently from Stripe webhooks" (`prd-530.md:249`) and the spec lists
  `charge.dispute.created` (`the-mechanics.md:1904`).

### A club's account, its disconnection, and its payouts

- **[DOCS]** `account.updated` "Allows you to monitor changes to connected account requirements and status changes";
  `account.application.deauthorized` "Occurs when a connected account disconnects from your platform … Available for
  connected accounts with access to the Stripe Dashboard" (Raketa's clubs have the full Dashboard). [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19
- **[DOCS]** Payouts: `payout.created`, `.updated`, `.paid` ("*expected* to be available … If the payout fails, a
  `payout.failed` notification is also sent, at a later time"), `.failed` — "Stripe also sends an
  `account.external_account.updated` event because the failed external account is disabled", and "no automatic or manual
  payouts can be processed until the external account is updated". "Regardless of the Accounts API version …, payouts
  trigger only the v1 events". [payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts);
  [event types](https://docs.stripe.com/api/events/types); [Connect webhooks](https://docs.stripe.com/connect/webhooks) — read 2026-10-19
- *Code:* `account.updated` naming an account is read (`stripe_notices.py:130-133`); `capability.updated`,
  `account.external_account.*`, `account.application.deauthorized`, `payout.*` and v2 thin events are not. Ticket #548:
  "Payout webhooks (`payout.paid/failed`) are not listened to; the list reads the provider live."

---

## 7. What the code does at these moments (readings)

- *Code:* `POST /api/v1/webhooks/stripe` and `/stripe-connect` verify the raw body with their own secrets
  (`backend/app/modules/payments/presentation/webhook_routes.py:39-64`; `backend/app/bootstrap/composition.py:976-987`):
  refused → **400**, no secret → **503** (`backend/app/modules/payments/domain/errors.py:124-143`), read → **204**. A deployed
  server refuses to start without both secrets (`backend/app/core/config.py:895-912`).
- *Code:* both readers accept every kind; nothing ties a kind to its endpoint (`stripe_notices.py:79-134`); no `livemode`
  check under `backend/app` (grep, 2026-10-19).
- *Code:* the event id enters `payment_notices` in the transaction that acts on it (`application/notices.py:88-107`); two
  racing deliveries meet the primary key, one fails and is retried (`.../infrastructure/sqlalchemy_notice_inbox.py:1-31`).
  `Unheeded` kinds get a row too (`notices.py:59-60`); nothing prunes the table.
- *Code:* the object is read from Stripe **inside the request**, before the 2xx (`notices.py:98`, `:125`, `:139`, `:153-155`);
  each read waits up to 20 s and is retried twice (`config.py:408`; `stripe_payments.py:67`, `:169-179`); an outage →
  **503** and nothing commits (`stripe_payments.py:641-654`; `errors.py:15-24`).
- *Code:* a payment notice moves only a charge on the same account (`notices.py:146-152`).
- *Code:* no recovery sweep (no `events.list` or `delivery_success` under `backend/app`); no list of event types to enable in
  the repo (grep `enabled_events`); the app keeps FastAPI's default slash redirect (`backend/app/main.py:19-30`), so a
  trailing-slash URL would answer a redirect (unverified for this app).

---

## Pitfalls

1. **Work before the 2xx.** Stripe wants 2xx "before any complex logic" ([webhooks](https://docs.stripe.com/webhooks)); a
   Stripe read inside the request (up to 20 s × 3) can time the delivery out. Nothing is lost while retries last, but a
   sandbox retries only three times in a few hours.
2. **Under-subscribing the real endpoint.** `stripe listen` forwards every kind ([CLI listen](https://docs.stripe.com/cli/listen)),
   so walks never show a missing subscription; adding one later "affects future delivery only"
   ([how events work](https://docs.stripe.com/events/how-events-work)). Without `account.updated` on Connected accounts a
   club never reads *ready*; without `payment_intent.*`, a hold a player confirmed on their bank's page is not recorded from
   the notice.
3. **Wrong scope.** Direct-charge events only reach **Connected accounts**; v2 account events only **Your account**
   ([Connect webhooks](https://docs.stripe.com/connect/webhooks)); one Stripe page says otherwise (§4).
4. **Mixed-up secrets.** CLI vs Dashboard, test vs live, one per endpoint ([manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints));
   a wrong one turns every notice into a 400 until Stripe gives up.
5. **Tolerance 0, or a fast clock.** Zero disables the age check; a server clock ahead refuses every notice
   ([webhooks](https://docs.stripe.com/webhooks)).
6. **A body parsed before verification** no longer verifies ([webhooks](https://docs.stripe.com/webhooks)).
7. **Redirects** are failures ([webhooks](https://docs.stripe.com/webhooks)): trailing slash, HTTP→HTTPS, host redirects.
8. **Dedup by event id only.** Two Event objects can describe one change ([webhooks](https://docs.stripe.com/webhooks)); only
   effects idempotent on the object's own state are safe.
9. **Trusting order or `created`** ([webhooks](https://docs.stripe.com/webhooks)); the sandbox stamped one hold's three events
   the same second.
10. **Acting on a stale snapshot** ([how events work](https://docs.stripe.com/events/how-events-work)).
11. **Ignoring `livemode` on a live Connect endpoint**, which also receives test events ([Connect webhooks](https://docs.stripe.com/connect/webhooks));
    a full-Dashboard club can make test objects under the same `acct_…`.
12. **No recovery after a long outage.** Retries end after three days, events list for 30, a failed generation never arrives
    ([manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints)).
13. **A refund that fails later.** Only `refund.failed` says so, up to 30 days on ([refunds](https://docs.stripe.com/refunds)):
    a late leaver told she got 38,40 zł back never receives it.
14. **A refund pending on the club's thin balance** ([refunds](https://docs.stripe.com/refunds)).
15. **A dispute nobody hears.** Stripe debits the club's balance and recommends `charge.dispute.created`
    ([Connect disputes](https://docs.stripe.com/connect/disputes)).
16. **A failed payout** disables the club's bank account for later payouts; `payout.paid` is only an expectation
    ([payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts)).
17. **A disconnection** (`account.application.deauthorized`) unheard: the club keeps selling games it can't be charged for
    ([Connect webhooks](https://docs.stripe.com/connect/webhooks)).
18. **`charge.updated` never fires on the sandbox's manual captures** (§6): the late-fee path is proven on the fake only
    ([asynchronous capture](https://docs.stripe.com/payments/payment-intents/asynchronous-capture)).
19. **One secret per path vs Stripe's upgrade recipe**, which runs two endpoints (two secrets) on one URL and sends each
    event twice ([webhook versioning](https://docs.stripe.com/webhooks/versioning)).
20. **A rolled secret not placed within 24 hours**: every notice refused after ([webhooks](https://docs.stripe.com/webhooks)).

## Checks

1. Is every notice verified over the raw body with its endpoint's secret and a tolerance above zero, before a field is
   read, and refused whole otherwise? (R-PLATFORM-26)
2. Does the endpoint answer 2xx without waiting on Stripe — or is its inline read (20 s × 3) inside Stripe's wait, and what
   does a player see while Stripe retries?
3. Is a notice read once, in the transaction of its effect, and is a second Event about the same change harmless because
   the effect re-reads the object and only moves forward? (R-PLATFORM-27, R-PLATFORM-2)
4. Does anything depend on notice order or `created`?
5. Is each needed kind enabled in the right scope — `setup_intent.succeeded`, `payment_method.automatically_updated` on
   **Your account**; `account.updated`, the five `payment_intent.*`, `charge.updated` on **Connected accounts** — and is that
   list written down where a deployed endpoint can be checked against it?
6. Are the kinds the PRD and spec promise read: `setup_intent.setup_failed`, `charge.dispute.*`, `refund.*`, `refund.failed`?
   For each dropped one, who finds out, and how? (R-PLATFORM-28, R-PAY-29)
7. When a refund recorded as given fails, does the player learn it, and does the club's Money stop counting it?
8. When a share is disputed, does the seat charge, the club or the player see it, and whose balance pays?
9. When a payout fails or the bank account is disabled, does the club website say so before the next payout?
10. When a club disconnects, does Raketa stop proposing games there?
11. Can a test-mode notice on a live Connect endpoint move anything for a real club's `acct_…`?
12. After an outage longer than Stripe's retries, does a job re-read what only a notice moves (a hold confirmed on the
    bank's page, an account becoming ready)?
13. Does a deployed server refuse to start without both secrets, and a laptop without one answer 503? (R-PLATFORM-33)
14. Can a notice naming a payment on one club's account move a share on another's?
15. Is the endpoint URL registered exactly as routed (no trailing slash, no redirect), on HTTPS with TLS 1.2+?
16. Are the fields the reader uses (`id`, `type`, `account`, `data.object.id`, `customer`, `payment_intent`) stable across
    the endpoint's version and the next major, and can two secrets be held while endpoints overlap?
17. On a walk, is `stripe listen` run with both `--forward-to` and `--forward-connect-to`, and its one secret placed in both
    settings before the store is made?
</content>
</invoke>
