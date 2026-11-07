# Stripe reliability — idempotency, unknown outcomes, versions, rate limits

What Stripe says about asking twice, asking and not hearing back, which API version a request
speaks, upgrading the SDK, and how fast it may be asked — for the way Raketa uses Stripe at
`9ab0ea5b`: direct charges on each club's connected account (`Stripe-Account`), holds with manual
capture made without the player, refunds and manual payouts on the club's account, v1 Customers
and SetupIntents on the platform, v2 Accounts and Account Links for clubs, in złoty, through
**stripe-python 15.6.1** `StripeClient` over aiohttp.

Stripe pages read **2026-10-19** with `?locale=en-GB` (without it some pages came in Spanish).
`[MEASURED]` lines read the installed SDK's source (the lock's Poetry environment) or the code
copy; nothing was written to Stripe. Facts the sandbox file measured are cited, not redone
([`stripe-sandbox.md#differences`](stripe-sandbox.md#differences); D2 is the API-version split).

---

## 1. Idempotency keys

### A v1 key saves the first answer after the endpoint starts, and a retry gets it back

[DOCS] https://docs.stripe.com/api/idempotent_requests (2026-10-19): "For API v1, Stripe saves the
status code and body of the first request made with a given idempotency key after endpoint
execution begins. Retries with the same key return the saved response, **including `500` errors**."
A replay carries `Idempotent-Replayed: true` (https://docs.stripe.com/error-low-level#idempotency).

### Errors are saved too — except those raised before execution begins

[DOCS] https://docs.stripe.com/error-low-level#content-errors (2026-10-19): "Retrying a cached `400`
response with the same key returns the same error. Errors that occur before execution begins, such
as invalid parameters, an invalid API key or rate limiting, don't cache a result." The reference adds
that a request that "conflicts with another request that's executing concurrently" saves nothing
and "You can retry these requests."

### A v1 key lasts at least 24 hours; after that the same key can run a new request

[DOCS] https://docs.stripe.com/error-low-level#post-requests (2026-10-19): "Stripe retains keys for at
least 24 hours and can remove them after that. Reusing a key after it's removed can execute a new
request." The window is a floor; nothing says when after 24 hours a key goes.

### The same key with other parameters is refused

[DOCS] https://docs.stripe.com/api/idempotent_requests (2026-10-19): "The idempotency layer compares
incoming parameters to those of the original request and errors if they're not the same".
https://docs.stripe.com/error-handling?lang=python: `stripe.IdempotencyError` — "After you use an
idempotency key, **only reuse it for identical API calls**." [ABSENT] Whether a key reused on another
object's path is refused: the docs speak only of parameters (looked in the reference, the advanced
error page and the error-code table).

### A 409 means the same key is still running: wait and resend it; a new key comes only after the first outcome is known

[DOCS] https://docs.stripe.com/error-low-level#content-errors (2026-10-19): "If a `409` indicates that
another request with the same key is still executing, wait and retry with that key and the same
parameters. **A new key can start a second operation.** If you need to change the request
parameters, first establish that the original operation didn't succeed and isn't still executing."
Code `idempotency_key_in_use`: "This occurs if your integration is making duplicate requests
simultaneously" (https://docs.stripe.com/error-codes).

### A key names one operation, is at most 255 characters, and carries no personal data

[DOCS] https://docs.stripe.com/error-low-level#sending-idempotency-keys (2026-10-19): keys must
"unambiguously identify a single operation within your account over the last 24 hours, at a
minimum"; either UUID v4 or "Derive the key from a user-attached object … to protect against double
submissions". "If your application retries across separate SDK calls or process restarts,
**generate and persist a key for the operation and supply it to every attempt**."
https://docs.stripe.com/api/idempotent_requests: "up to 255 characters long. **Avoid using sensitive
data (for example, email addresses or personal identifiers) as idempotency keys.**"

### v2 keys last 30 days and re-run failed work instead of replaying the error

[DOCS] https://docs.stripe.com/api-v2-overview#idempotency (2026-10-19): "If the first request failed
(or partially failed), the API re-executes the failed requests and returns the new response." A
replay is the same key "for the same API", "in the scope of the same account or sandbox", "within
30 days". "If no key is provided, Stripe automatically generates a UUID". "API v1 always returns the
previously-saved response … even if it was an error." Here, v2 is `v2.core.accounts.create` and
`v2.core.account_links.create` (`backend/app/modules/payments/infrastructure/stripe_payments.py:317-369`).

### The keys this product sends

[MEASURED] code copy, 2026-10-19. "A key is the act and the hour it is asked in"
(`docs/adr/0190-*.md:111-115`); the onboarding link takes none. Paths under
`backend/app/modules/payments/`.

| Call (account) | Key | Hour? | Where |
|---|---|---|---|
| `customers.create` (platform) | `raketa-customer-{player}-{YYYYMMDDHH}` | yes | `application/setup.py:75-76` |
| `setup_intents.create` (platform) | `raketa-setup-{player}-{ordinal}-{hour}` | yes | `setup.py:79-80` |
| `setup_intents.cancel` (platform) | `raketa-cancel-{setup}` | no | `application/handlers/release_methods.py:29-30` |
| `payment_methods.detach` (platform) | `raketa-release-{method}` | no | `release_methods.py:25-26` |
| `v2.core.accounts.create` (platform) | `raketa-club-account-{club}-{hour}` | yes | `setup.py:83-87`, `infrastructure/club_accounts.py:43-53` |
| `v2.core.account_links.create` | none; the SDK adds a random one per call | — | `stripe_payments.py:349-369` |
| `payment_methods.create`, the clone (club) | `{hold key}-clone` | yes | `application/seat_charges.py:433-438` |
| hold, fill or rescue (club) | `raketa-{seat\|rescue}-{game}-{player}-{attempt}-{hour}`, attempt = proposal/game version | yes | `seat_charges.py:161-169`; `proposals/application/fill.py:216` |
| hold, the holding job (club) | `raketa-holding-{charge}-{charge version}-{hour}` | yes | `seat_charges.py:502-507` |
| capture / release / check let go (club) | `raketa-capture-{charge}` / `raketa-cancel-seat-{charge}` / `raketa-cancel-check-{charge}` | no | `application/handlers/settle_seat_charges.py:53-64` |
| `refunds.create` (club) | `raketa-refund-{charge}` | no | `settle_seat_charges.py:67-70` |
| `payouts.create` (club) | `raketa-payout-{payout}` | no | `application/handlers/send_club_payouts.py:30-33` |

A hold's parameters include the club's name in `description` (`seat_charges.py:265`, `:597`) and
`metadata` `game_id`, `player_id` (`stripe_payments.py:508-509`). The longest key is about 110
characters. Keys embed the player's internal id, which Stripe already gets as metadata
(`stripe_payments.py:197`, `:214`).

### Why the hour is in some keys, and what the decision weighed

[MEASURED] `application/setup.py:22-31`: "Stripe replays the first answer to a key for a day, errors
included, so a key that never changed would keep one passing outage between a player and their card
for a day … What an hour boundary can cost is an orphan — a customer or a setup opened twice". Holds
use the same rule; `seat_charges.py:36-44`: "A hold made and then orphaned by a transaction that never
committed is not cancelled by anybody: the next attempt in the hour is answered it again, and
otherwise the provider lets it lapse untaken". ADR-0190 §4 weighs only "an orphaned customer or setup
… which nothing can charge". The mechanics spec: "Idempotency keys may be forgotten after 24 h:
Raketa's own records must prevent duplicates" (`docs/specs/games-and-fill-in/the-mechanics.md:1899`).

### stripe-python adds a random key to every keyless POST and keeps it across its own retries

[MEASURED] stripe-python 15.6.1 `stripe/_api_requestor.py:568-574`: a caller's key becomes the
`Idempotency-Key` header, else `headers.setdefault("Idempotency-Key", _generate_idempotency_key())`
for every POST (and v2 DELETE). It is built once per call, so the SDK's retries share it; another call
gets a new one. [DOCS] README (https://github.com/stripe/stripe-python): keys "are automatically
generated and added to requests, when not given, to guarantee that retries are safe."

---

## 2. Retries and timeouts with an unknown outcome

### A network error or timeout leaves the outcome unknown

[DOCS] https://docs.stripe.com/error-handling?lang=python, *Connection errors* (2026-10-19): "Treat
the result of the API call as indeterminate. That is, don't assume that it succeeded or that it
failed." "This error can mask others." https://docs.stripe.com/error-low-level#network-errors:
"Restoring connectivity doesn't tell you whether the original request succeeded."

### Retry the same key within 24 hours, then stop and reconcile

[DOCS] https://docs.stripe.com/error-low-level#network-errors (2026-10-19): "Retry with the same
idempotency key and parameters within the first 24 hours after the original request. If you still
haven't received a result when that window ends, stop retrying and reconcile". #post-requests: "If
the outcome is still unknown after that window, **don't retry with either the old key or a new
one**. Retrieve the relevant object, inspect the request in the Dashboard and use webhook events …
contact Stripe support before repeating the operation."

### A 500 is indeterminate, and a new key waits until the first outcome is known

[DOCS] https://docs.stripe.com/error-low-level#server-errors (2026-10-19): "Treat the outcome of a
request that returns `500` as indeterminate … **Don't retry with a new idempotency key until you've
resolved the original outcome.**" "For API v1, Stripe caches `500` responses from `POST` requests that
use an idempotency key. Retrying with the same key returns the cached response while Stripe retains
it." `APIError`: "Rely on webhooks for information about the outcome."

### Objects can arrive by webhook that no API answer returned — tag them with your own id

[DOCS] https://docs.stripe.com/error-low-level#server-errors (2026-10-19): "During incident recovery,
Stripe attempts to reconcile failed operations and send webhook events for any objects created …
**Prepare your webhook handlers to process objects your integration hasn't received in an API
response.** … include a local identifier in its metadata so you can match an object received through
a webhook to your local records". [MEASURED] Holds carry `game_id`, `player_id`
(`stripe_payments.py:508-509`); the notice reader reads "A payment no charge here holds" and "changes
nothing" (`application/notices.py:13-18`).

### Stripe's next step by what is known

[DOCS] https://docs.stripe.com/error-handling?lang=python (2026-10-19): invalid parameters or failed
authentication → "Correct the request or API key before trying again"; declined → ask the customer;
"A connection fails or a request is still executing → Retry safely with the same idempotency key and
parameters"; "A server error … leaves the outcome unknown → Reconcile the request before starting
another operation". `AuthenticationError`: "Make sure you aren't using a key that you 'rotated' or
revoked." `RateLimitError`: "retry … after a delay, and increase the delay exponentially".

### Some refusals never clear on a retry

[DOCS] https://docs.stripe.com/error-codes (2026-10-19): `account_invalid` — the `Stripe-Account`
value is invalid; `platform_api_key_expired` — "occurs if your platform has either generated a new
key or **the connected account has been disconnected from the platform**"; `api_key_expired`;
`livemode_mismatch`; `payment_intent_unexpected_state`; `charge_expired_for_capture` — "the
authorisation has expired". [MEASURED] The adapter maps `AuthenticationError` and `PermissionError`
to `PaymentsUnavailable` — "a key it refuses, which is a configuration fault a retry will not fix"
(`stripe_payments.py:69-79`) — a 503 whose remedy is "the same request, retried"
(`domain/errors.py:15-31`); `InvalidRequestError` and `IdempotencyError` are raised as they came
(`stripe_payments.py:18-22`, `:641-654`).

### StripeClient retries nothing unless told; this product sets two retries and 20 seconds

[MEASURED] stripe-python 15.6.1: the module default `stripe.max_network_retries = 2`
(`stripe/__init__.py:39`) does not reach a `StripeClient`, whose `None` is read as 0
(`_stripe_client.py:158`, `:194`; `_http_client.py:117-129`). The product builds
`StripeClient(…, http_client=AIOHTTPClient(timeout=20.0), max_network_retries=2)`
(`stripe_payments.py:67`, `:174-179`; `backend/app/core/config.py:408`). [DOCS]
https://docs.stripe.com/error-low-level#network-retries: "Retry defaults depend on the SDK, version
and how you construct the client."

### What the SDK retries, and how long it waits

[MEASURED] `stripe/_http_client.py:117-181` (15.6.1): it retries a connection error or timeout
(aiohttp marks every request error retryable, `:1413-1423`); obeys `Stripe-Should-Retry`; retries every
`409` and every status ≥ 500; **not a `429` rate limit** unless Stripe sends `Stripe-Should-Retry:
true`. Delay `min(0.5 × 2^(n−1), 5)` s, jittered, never under 0.5 s: 0.5 s, then 0.5–1 s. [DOCS]
#should-retry: "Stripe SDKs respect this header automatically."

### How the SDK classes Stripe's statuses

[MEASURED] `stripe/_api_requestor.py:418-462` (15.6.1): `429` → `RateLimitError`; `400`/`404`
`idempotency_error` → `IdempotencyError`, else `InvalidRequestError`; `401` →
`AuthenticationError`; `402` → `CardError`; `403` → `PermissionError`; anything else, **`409`
included**, → `APIError` — which the product maps to `PaymentsUnavailable`.

### One call can take about 61,5 seconds; Stripe recommends no timeout

[MEASURED] `AIOHTTPClient` defaults to 80 s (`_http_client.py:1320-1340`); a float becomes aiohttp
`ClientTimeout(total=…)` (aiohttp 3.13.5 `client.py:589-593`), covering connect, send and read.
3 × 20 s + 1,5 s ≈ 61,5 s worst case. [ABSENT] A recommended server timeout: searched the docs, the
rate-limits page (only "watching for timeouts to identify unexpectedly slow ones") and the README.

### The fill asks Stripe inline, seat by seat, inside the yes that filled the game

[MEASURED] `seat_charges.py:26-33`, `:205-235`: "The holds are asked inline, because their answer is
the response" — a clone and a PaymentIntent per seat (`:433-450`). A padel fill is up to 8 calls,
worst case ≈ 8 × 61,5 s ≈ 8 min 12 s in one `POST …/yes`. On `PaymentsUnavailable` the yes answers
`payments_unavailable`: "Nothing was recorded; retry."
(`backend/app/modules/proposals/presentation/routes.py:129-134`).

### A hold never captured lapses on its own; cancelling releases it now

[DOCS] https://docs.stripe.com/payments/place-a-hold-on-a-payment-method (2026-10-19): "If the
authorisation expires before you capture the funds, the funds are released and the payment status
changes to `canceled`." "If you need to cancel an authorisation, you can cancel the PaymentIntent."
Visa: 4 days 18 hours merchant-initiated, 7 days customer-initiated, classified "based on signals of
cardholder participation, not solely on … `off_session`"; the sandbox measured 7 days
([`stripe-sandbox.md#every-visa-hold-lasted-exactly-7-days`](stripe-sandbox.md#every-visa-hold-lasted-exactly-7-days)).
Cancelling costs nothing ([`gaps-S-01A-leave-fee.md#letting-a-hold-go-before-it-is-taken-costs-nothing`](gaps-S-01A-leave-fee.md#letting-a-hold-go-before-it-is-taken-costs-nothing)).

### Search cannot settle an outcome right after a write

[DOCS] https://docs.stripe.com/search (2026-10-19): "**Don't use search for read-after-write flows**
… data is searchable in under 1 minute. Propagation … could be delayed during an outage." Search
"filters using a cached version of the PaymentIntent `status`". PaymentIntents are searchable by
`metadata`; 20 reads a second; list APIs "aren't subject to the availability delays".

### Stripe asks for the request ID with every error

[DOCS] https://docs.stripe.com/error-handling?lang=python (2026-10-19): "Keep the request ID so you can
find the request in your logs or share it with Stripe support." [MEASURED] The adapter logs it for
outages (`stripe_payments.py:645-653`) and a payout not yet available (`:448-451`) only.

---

## 3. API versions and pinning

### Each request speaks one version: the header, else the SDK's pin, else the account default

[DOCS] https://docs.stripe.com/api-versions (2026-10-19): Stripe takes "The `Stripe-Version` header …
The API version pinned by your server-side SDK … Your account's default API version". "When you
retrieve an event through the API, the structure of the event … is defined by the account's default
API version at the time the event occurred." "Webhook endpoints can also pin their own API version."
Current: **2026-09-30.endive**.

### Stripe wants the version written in code

[DOCS] https://docs.stripe.com/upgrades (2026-10-19): "specify the API version that you're integrating
against in your code instead of relying on your account's default API version." [MEASURED] Requests
speak the SDK's `2026-08-26.dahlia`; the account default is `2026-09-30.endive`
([`stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive`](stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive)).

### v2 requests must carry a version, which the SDK sends

[DOCS] https://docs.stripe.com/api-v2-overview (2026-10-19): "All API requests to the API `/v2`
namespace must include the `Stripe-Version` header". "After you update your SDK or CLI version,
Stripe simultaneously updates the API version of your requests and responses."

### Monthly versions never break; two majors a year can

[DOCS] https://docs.stripe.com/api-versions (2026-10-19): "new API versions monthly with no breaking
changes. Twice a year, we issue a new major release … that starts with an API version containing
breaking changes." "new minor versions of the SDKs with each monthly API version and new major
versions of the SDKs with each of the twice-a-year major releases."

### What Stripe calls compatible, and what the code must tolerate

[DOCS] https://docs.stripe.com/api-versions (2026-10-19): compatible = new resources, new optional
parameters, new response properties, property order, "the length or format of opaque strings, such
as object IDs" (up to 255 characters), new event types. "**Design your integration to ignore
unfamiliar fields and event types.**" [MEASURED] Statuses are read through exact dictionaries
(`stripe_payments.py:406`, `:461`, `:615`) covering every status documented today; refunds fall back
to *pending* (`:607`).

### Endive removes `payment_method_types` from PaymentIntents and SetupIntents

[DOCS] https://docs.stripe.com/changelog/endive/2026-09-30/removes-the-payment-method-types-parameter-from-payment-intents-and-setup-intents
(2026-10-19): "**Passing `payment_method_types` on this API version returns a 400 error with the code
`payment_method_types_no_longer_supported`.**" Use dynamic payment methods,
`excluded_payment_method_types`, or `allowed_payment_method_types` ("Incompatible types are silently
filtered"). [MEASURED] Sent on `setup_intents.create` (`stripe_payments.py:213`) and the hold
(`:504`).

### Endive removes `configurations` from v2 Account Links

[DOCS] https://docs.stripe.com/changelog/endive/2026-09-30/removes-configurations-parameter-from-v2-core-account-links-api
(2026-10-19): requests that include `configurations` "**fail on API version `2026-09-30.endive` or
later**"; "Stripe now automatically determines which configurations require onboarding".
[MEASURED] Sent as `configurations: ["merchant"]` (`stripe_payments.py:358-364`).

### Endive's other breaking changes miss what this product sends and reads

[DOCS] https://docs.stripe.com/changelog/endive (2026-10-19), released 30 September 2026: the other
breaking API changes sit in Billing, Financial Connections, Checkout, Radar, Tax, Treasury, India
mandates, PayTo, BLIK decline codes, 3D Secure *Data Share Only*, and Connect requirements (rejected
v2 capabilities, address and rejection-reason errors, eventually-due errors, SEPA settings). None
touches a parameter `stripe_payments.py` sends or a field it or `stripe_notices.py` reads
([`stripe-sandbox.md#the-notices-the-code-reads-and-the-endpoint-each-comes-through`](stripe-sandbox.md#the-notices-the-code-reads-and-the-endpoint-each-comes-through)).

### An upgrade: SDK, then webhook endpoints on two URLs, then the account, 72 hours to roll back

[DOCS] endive changelog *Upgrade* (Python) and https://docs.stripe.com/upgrades (2026-10-19): "Upgrade
your Python SDK … Upgrade the API version used for webhook endpoints. Test your integration … If you
use Connect, test your Connect integration. In Workbench, perform the upgrade. You can roll back the
version for 72 hours." A new endpoint with the target `api_version` runs beside the old; an event
destination's `snapshot_api_version` is set "only when you create" it, and with both active "your
event handler must be idempotent".

---

## 4. SDK upgrades

### stripe-python follows semantic versioning, each version pinning the API version of its day

[DOCS] https://docs.stripe.com/sdks/versioning (2026-10-19): major = "breaking changes", minor = new
compatible features, patch = compatible fixes; "Each SDK version uses the API version that is current
at the time of its release". https://docs.stripe.com/sdks/set-version: stripe-python can override
`stripe_version` globally or per request, and responses then come "in that version".

### Only the newest major line gets fixes

[DOCS] https://docs.stripe.com/sdks/versioning (2026-10-19): "New features and bug fixes are released
on the latest major version of the SDK. … **Older major versions … won't receive any additional
updates.**"

### stripe-python 16.0.0 pins endive

[DOCS] CHANGELOG (https://github.com/stripe/stripe-python/blob/master/CHANGELOG.md, 2026-10-19):
**16.0.0 — 2026-09-30**, "changes the pinned API version to `2026-09-30.endive`", breaking SDK changes
including "Path parameters must now be passed positionally to service methods"; nothing on
idempotency, retries, timeouts or aiohttp. **15.6.1 — 2026-09-01**: "Harden API requestor code against
malicious URLs". [MEASURED] The adapter already passes path parameters positionally
(`stripe_payments.py:226`, `:281`, `:546`, `:558`, `:573`).

### The caret in the lock keeps the product on 15.x

[MEASURED] `backend/pyproject.toml:39` `stripe = "^15.6.1"` (≥15.6.1, <16.0.0);
`backend/poetry.lock:3727-3728` locks 15.6.1, `CURRENT = "2026-08-26.dahlia"`. `poetry update` cannot
reach 16.x; moving is an edit of the pin.

### Python 3.11 is supported until March 2029

[DOCS] https://docs.stripe.com/sdks/versioning (2026-10-19): "We support Python 3.9+"; 3.11 end of life
October 2027, support dropped March 2029. The backend runs 3.11 (`state.json` `test_env`).

---

## 5. Rate limits

### 100 a second live, 25 in a sandbox, 25 per endpoint, per Stripe account

[DOCS] https://docs.stripe.com/rate-limits (2026-10-19): "rate limits are measured in API requests per
second, per Stripe account." Global "Live mode: 100 requests per second; Sandbox: 25"; "Individual API
endpoints (unless otherwise noted): 25 requests per second"; "each named API operation a separate
endpoint".

### Limits on the endpoints this product uses

[DOCS] same page: Payment Intents "1000 update requests per PaymentIntent object, per hour"; Payouts
"15 create requests per second; 30 concurrent requests per business"; Connect accounts (v1 and v2)
"Live mode: Create 30 accounts per second; Sandbox: Create 5"; Search "20 read requests per second".

### At most 50 requests in flight in live mode

[DOCS] https://docs.stripe.com/rate-limits#concurrency-limits (2026-10-19): "The default global
concurrency limit … in live mode is 50 in-progress requests"; lists and expansions "take longer to
run". [MEASURED] Captures and payment reads expand `latest_charge.balance_transaction`
(`stripe_payments.py:112`, `:548`, `:560`); the hold expands `latest_charge` (`:511`).

### A 429 names its reason; one without the header is a lock timeout

[DOCS] https://docs.stripe.com/rate-limits#rate-limited-responses (2026-10-19):
`Stripe-Rate-Limited-Reason` is `global-rate`, `endpoint-rate`, `global-concurrency`,
`endpoint-concurrency` or `resource-specific`; "If a request returns a `429` status code without these
headers, it wasn't the result of a rate limit. It might be a lock timeout."

### Concurrent writes on one object fail with `lock_timeout`; the SDKs retry those

[DOCS] https://docs.stripe.com/rate-limits#object-lock-timeouts (2026-10-19): "The Stripe API locks
objects on some operations … Stripe doesn't process these failed requests". "the automatic retry
mechanisms built into the Stripe SDKs retry `429`s caused by lock timeouts". "make sure that
**mutations on the same object are queued up and run sequentially**." "we recommend that all
integrations are able to retry requests."

### Handle a 429 with exponential backoff and jitter, or a client-side token bucket

[DOCS] https://docs.stripe.com/rate-limits#handling-limiting-gracefully (2026-10-19): "Follow an
exponential backoff schedule … and add randomness to the backoff schedule to avoid a thundering herd
effect." "control traffic to Stripe at a global level … a client-side token bucket rate-limiting
algorithm."

### Load tests do not belong on a sandbox

[DOCS] https://docs.stripe.com/rate-limits#load-testing (2026-10-19): "We generally discourage this
practice because API limits are lower in a sandbox"; a sandbox charge is mocked, "resulting in
significantly different latency profiles". Instead, mock Stripe and "simulate latency by sleeping for
a time … sampling the durations of real live mode Stripe API calls".

### Reads are allotted per transaction; a platform's reads for its accounts have their own allotment

[DOCS] https://docs.stripe.com/rate-limits#api-read-request-allocations (2026-10-19): "an average of
500 per transaction"; "Connect platforms use a separate allocation to make read requests on behalf of
their connected accounts"; minimum "10,000 read requests per month"; "Write API requests have no
allocation limit."

### Whose per-second limit a `Stripe-Account` request counts against is not published

[ABSENT] https://docs.stripe.com/rate-limits, https://docs.stripe.com/connect/authentication and
`search_stripe_documentation` (2026-10-19) split only read allocations; the per-second limits say "per
Stripe account". A question for Stripe support.

### Whether a replayed answer counts against the limit is not published

[ABSENT] Same pages, 2026-10-19: nothing on whether a request answered from a saved key counts.

### This product's outbox asks again every second, with no end

[MEASURED] code copy: polls every `1.0` s, 100 at a time (`backend/app/core/config.py:432-433`),
unpublished events oldest first (`backend/app/infrastructure/events/sqlalchemy_event_delivery_queue.py:35-48`);
a failure records its attempt count and error (`:72-87`) and is fetched again next poll — no delay,
jitter or last attempt (`backend/app/application/events/deliver_event_batch.py:54-93`). Captures,
cancellations, refunds and payouts are deliveries (`settle_seat_charges.py:1-9`,
`send_club_payouts.py:1-13`). A payout the balance cannot cover gets `balance_insufficient`, saved "for
a day, so the next real attempt is the day after" (`stripe_payments.py:441-454`). Several gunicorn
workers run (`backend/docker/api/startup.prod.sh:41-42`) and deliveries are claimed `SKIP LOCKED`
(`sqlalchemy_event_delivery_queue.py:45-59`); whether each worker delivers is unverified.

---

## Pitfalls

What integrations get wrong here, with the Stripe source saying what goes wrong, and where this
product meets it. Seeds for the Breakers.

1. **A key that changes on the hour turns one unknown hold into two.** Stripe: "Don't retry with a
   new idempotency key until you've resolved the original outcome"; "A new key can start a second
   operation" ([server-errors](https://docs.stripe.com/error-low-level#server-errors),
   [content-errors](https://docs.stripe.com/error-low-level#content-errors)). Fill, rescue and
   holding keys carry the hour (`seat_charges.py:161-169`, `:502-507`): a hold that timed out or
   answered `500` at 18:59 and is asked again at 19:00 makes a second PaymentIntent; if the first
   authorised, the player holds 2 × 40,00 zł at Bonarka Arena on a weekday until the first lapses (7
   days on the sandbox). ADR-0190's reason for the hour weighed customers and setups, "which nothing
   can charge"; a hold is money the player can't spend.

2. **Holds from a fill that rolled back stay on cards, and nothing lets them go.** Stripe: "Prepare
   your webhook handlers to process objects your integration hasn't received in an API response";
   "you can cancel the PaymentIntent" ([server-errors](https://docs.stripe.com/error-low-level#server-errors),
   [place-a-hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method)). Seats are held
   one by one inside the yes's transaction; an outage on the third seat rolls it back with the first
   two holds standing at Stripe and no charge recording them (`seat_charges.py:36-44`). Their notices
   carry `game_id` and `player_id` and are "read and changes nothing" (`notices.py:13-18`). Unless the
   last player taps yes again within the same clock hour, each orphan keeps 40,00 zł unusable until it
   lapses. The holding job can meet the same partway through a game (`seat_charges.py:585-605`; how it
   commits unverified).

3. **A saved 500 blocks an unchanging key for at least a day — longer than a hold may have left.**
   Stripe caches v1 `500`s and replays them "while Stripe retains it", keys living "at least 24 hours"
   ([server-errors](https://docs.stripe.com/error-low-level#server-errors),
   [post-requests](https://docs.stripe.com/error-low-level#post-requests)). Capture, release, refund
   and payout keys never change (`settle_seat_charges.py:53-70`, `send_club_payouts.py:30-33`); the
   outbox gets the same `500` every second. A cut-off capture whose first try truly failed can wait
   until the hold expires (`charge_expired_for_capture`) and the club is never paid the share.
   Stripe's way out: read the PaymentIntent — still `requires_capture` means it wasn't captured, and a
   new key is then safe.

4. **Retrying in a tight loop.** Stripe: "Follow an exponential backoff schedule … and add randomness"
   ([rate-limits](https://docs.stripe.com/rate-limits#handling-limiting-gracefully)). The outbox
   re-sends every failed write each second with no end (`config.py:432-433`), and the SDK does not
   retry a real `429` (`_http_client.py:117-162`). One payout waiting for its money asks about 86 400
   times a day; against 25 a second in the sandbox and 100 live, a few dozen such events eat the budget
   the fill's inline holds need, and players read *payments unavailable*. Failing events are fetched
   first, 100 at a time (`sqlalchemy_event_delivery_queue.py:40-45`): a hundred that never succeed
   starve every newer one.

5. **A permanent refusal treated as a passing outage.** Stripe: fix the key "before trying again";
   `platform_api_key_expired` comes when "the connected account has been disconnected from the
   platform" ([error-handling](https://docs.stripe.com/error-handling?lang=python),
   [error-codes](https://docs.stripe.com/error-codes)). The adapter calls `AuthenticationError` and
   `PermissionError` an outage whose remedy is retrying (`stripe_payments.py:73-79`,
   `errors.py:15-31`): a rotated key, or a club whose account no longer answers the platform, tells
   players *try again* for ever and loops every delivery for that club. An `InvalidRequestError` in a
   delivery — a capture on a lapsed hold, `payment_intent_unexpected_state` — loops the same way,
   since a saved `400` "returns the same error".

6. **One key, different parameters, raised as a crash.** Stripe: "only reuse it for identical API
   calls" ([error-handling](https://docs.stripe.com/error-handling?lang=python)). The hold's
   `description` carries the club's name (`seat_charges.py:265`, `:597`); a club renamed between a
   timed-out hold and its retry in the hour gets `idempotency_error`, which the adapter neither maps
   nor logs (`stripe_payments.py:73-79`): the yes answers 500.

7. **The next SDK major breaks three calls.** Stripe: on endive `payment_method_types` "returns a 400
   error" and Account Links with `configurations` "fail"
   ([changelog](https://docs.stripe.com/changelog/endive/2026-09-30/removes-the-payment-method-types-parameter-from-payment-intents-and-setup-intents),
   [changelog](https://docs.stripe.com/changelog/endive/2026-09-30/removes-configurations-parameter-from-v2-core-account-links-api)).
   stripe-python 16 speaks endive; the product sends both (`stripe_payments.py:213`, `:504`, `:361`).
   Upgraded as is, no player could save a card, no share be held, no club start onboarding. Staying
   put: "Older major versions … won't receive any additional updates"
   ([sdks/versioning](https://docs.stripe.com/sdks/versioning)).

8. **Events shaped by the account default.** Stripe: version "in your code instead of relying on your
   account's default"; an event follows "the account's default API version at the time the event
   occurred" unless its endpoint pins one ([upgrades](https://docs.stripe.com/upgrades),
   [api-versions](https://docs.stripe.com/api-versions)). Requests speak dahlia, the account endive
   (D2), and no endpoint exists yet (D1): one created without `api_version` takes the default of that
   day, and a Dashboard upgrade reshapes notices with no code change.

9. **Two writes on one PaymentIntent at once.** Stripe: "mutations on the same object are queued up
   and run sequentially" ([object-lock-timeouts](https://docs.stripe.com/rate-limits#object-lock-timeouts)).
   A share taken and refunded seconds apart are two deliveries (`settle_seat_charges.py:19-24`); two
   workers can act on one PaymentIntent together (suspected). After two SDK retries a lock timeout or
   `409` becomes an outage.

10. **Tapping again while Stripe is still answering is told it failed.** Stripe: on a `409` "wait and
    retry with that key" ([content-errors](https://docs.stripe.com/error-low-level#content-errors)).
    The fill can wait minutes (8 calls × up to 61,5 s); a second tap sends the same keys, gets
    `idempotency_key_in_use`, the SDK retries within about 1,5 s, and the player reads *payments
    unavailable* while the first request may still book the game.

11. **Reconciling by search right after a failure.** Stripe: "Don't use search for read-after-write
    flows … could be delayed during an outage" ([search](https://docs.stripe.com/search)). A fix for
    pitfall 2 that searches `metadata["game_id"]` just after the outage misses the orphans when it
    matters; the notice carrying the metadata, or a list of the club's PaymentIntents, sees them.

12. **v2 keys don't behave like v1 keys.** Stripe: a v2 retry "re-executes the failed requests", for 30
    days ([api-v2-overview](https://docs.stripe.com/api-v2-overview#idempotency)). The club account's
    key changes on the hour to escape a saved error v2 never saves (`club_accounts.py:43-53`); an
    unknown outcome straddling the hour opens a second connected account. The sandbox holds four
    never-onboarded club accounts ([`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account)),
    cause unknown.

13. **Bursts and load on the sandbox.** Stripe: sandbox limits are lower (25 a second, 5 account
    creations a second) and latency differs ([load-testing](https://docs.stripe.com/rate-limits#load-testing)).
    The console's *Run it now* fires every due capture or hold at once; a walk can meet `429`s live
    would not, and proves nothing about live latency.

## Checks

The questions a grader asks of a product rule here. The Stripe lens uses them.

1. Is each write's key derived from Raketa's own record of the act, the same on every attempt of it —
   across SDK calls, redeliveries and restarts — and different for a different act?
2. Can an attempt of an unresolved v1 write come more than 24 hours after the first? If so, what reads
   the object at Stripe before asking again?
3. Does a key change between attempts of one act while the first outcome is unknown (an hour, a
   version)? What settles the first outcome before the new key is used?
4. After a timeout or `500` on a hold, can a player hold twice for one seat? Who lets the orphan go,
   and how long is the money unusable?
5. When a notice names a PaymentIntent no charge records but whose metadata names a Raketa game and
   player, is it cancelled, linked, or dropped?
6. Does each answer go to the right next step — same key again (connection error, `409`, lock timeout,
   `5xx`); a new key only once the first outcome is known (`400`); a person, not a retry (`401`,
   `403`, `idempotency_error`, `account_invalid`, `platform_api_key_expired`); the player (`402`)?
7. Can a saved `500` or `400` under an unchanging key keep a capture, refund or payout from happening
   before its deadline (`capture_before`)? What margin is there against "at least 24 hours"?
8. Do retries back off exponentially with jitter, and does something stop and tell a person? Can one
   failing delivery delay others or spend the rate limit the fill needs?
9. Are all parameters under one key fixed for the act — amount, currency, description, metadata? Could
   a club's name, a price or a computed refund change between attempts?
10. Are two writes to one PaymentIntent ever sent at once (capture and refund, release and a notice's
    re-read, two workers)?
11. Is an inline chain's worst case — calls × (timeout × 3 + backoff) — shorter than the phone and load
    balancer wait? Are database row locks held while Stripe is waited on?
12. Which version does each request, endpoint and event read speak, and is it written in code? Is every
    webhook endpoint created with an `api_version`?
13. Before an SDK major: does the code send a parameter it removes (`payment_method_types`, Account
    Links `configurations`)? Is it tried on the new version first, webhooks on two endpoints, 72 hours
    to roll back?
14. Is the SDK on a major line that still receives fixes?
15. Does an unknown status or event type crash a reading, or is it ignored as Stripe asks?
16. Is the request ID logged for every Stripe error, not only outages?
17. At the busiest moment — the cut-off taking a Saturday morning's shares, the holding job, a payouts
    run — how many calls a second go out, against 100 live, 25 sandbox, 25 per endpoint, 50 in flight?
    Is there a client-side limit?
18. Do the v2 calls follow v2 idempotency (30 days, failed work re-run), and does their key policy
    assume it?
19. Do keys carry personal identifiers Stripe asks not to see there, beyond what metadata already
    sends?
