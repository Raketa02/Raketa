# Stripe gaps 07 — keys, secrets, card testing and links (SECURITY, CLUBBOOK)

Answers to the `stripe:` gaps the Stripe lens left on **R-CLUBBOOK-2** and **R-SECURITY-1, -2, -4, -5, -6, -10,
-11, -13, -15 and -27**, for the payments pass on PRD #530. Read on **2026-10-20** against the code at `9ab0ea5b`.

**Sources.**
- **Stripe's documentation.** The Stripe MCP servers were disconnected, so docs.stripe.com pages were fetched
  directly. Most were fetched in English (`<page>.md?locale=en-US`). A quote from a page served in Spanish is marked
  *(translated)*.
- **The sandbox.** It was read through stripe-python 15.6.1 in the code copy, using the sandbox's test keys from
  `backend/.env` (never printed). A read-only probe script ran and was then deleted. Nothing was created, updated or
  deleted. These facts are cited as [MEASURED] "read via the SDK in the copy", with each object's ID.
- **The SDKs' own source.** stripe-python 15.6.1 in the backend's Poetry environment, and `@stripe/stripe-react-native`
  0.38.6 in `frontend_player/node_modules`.

Earlier research is cited by anchor, not repeated: `stripe-security.md` (SEC), `stripe-sandbox.md` (SB),
`stripe-connect.md`, `stripe-authentication.md` (AU).

---

### R-CLUBBOOK-2 — No Stripe page says it in words; the key settings Stripe offers never name an account

[ABSENT] An explicit sentence that a platform key "can't be limited to particular connected accounts". Looked in:
- https://docs.stripe.com/keys
- https://docs.stripe.com/keys/restricted-api-keys
- https://docs.stripe.com/keys/permissions-reference
- https://docs.stripe.com/connect/authentication
- https://docs.stripe.com/context
- https://docs.stripe.com/keys/organization-api-keys
- a web search of docs.stripe.com

All were read on 2026-10-20. The only explicit statement is still the documentation-search knowledge entry quoted in
[SEC §7](stripe-security.md#the-platform-acts-for-a-club-with-its-own-key-and-the-clubs-account-id--stripe-does-not-limit-which),
and it has no page.

[DOCS] What Stripe offers instead, read on 2026-10-20. None of these controls names an account:
- **Restricted keys.** https://docs.stripe.com/keys/restricted-api-keys: "For each resource you want the new key to
  access, select the appropriate permission: **None**, **Read**, or **Write**. If you use Connect, you can also select
  the permission to allow for this key when accessing connected accounts." That is one setting for all connected
  accounts at once.
- **The permissions reference.** https://docs.stripe.com/keys/permissions-reference: "Permissions labeled with
  (Direct) can’t authorize Connect call patterns." The only Connect distinction is whether a permission works on a
  connected account at all.
- **Access policies.** https://docs.stripe.com/keys#access-policies: a policy restricts by "IP addresses", by
  "ASNs to allow", by "Countries" and by "Sources". These say where a request comes from, never which account it
  acts on.
- **Connected-account calls.** https://docs.stripe.com/connect/authentication: "To make server-side API calls for
  connected accounts, use the `Stripe-Account` header with the Account ID … using your platform’s API secret key and
  the connected account’s `Account` ID." Each request names its own account.

**For the rule:** cite the restricted-keys page together with the access-policies section. Between them, they show
that the only per-club guard is Rakieta's own check of the desk's club.

### R-SECURITY-1 — Nothing is deployed yet, and the deployment runbook admits every address

[DOCS] Stripe's word, read on 2026-10-20:
- https://docs.stripe.com/webhooks: "Use both of these protections: **IP allowlisting**: Stripe sends webhook events
  from a set list of IP addresses. Configure your server or firewall to only accept webhook requests from these
  addresses. **Signature verification** …".
- https://docs.stripe.com/error-handling?lang=python *(translated)*: "If you restrict inbound traffic by IP address,
  allow Stripe's public webhook IP addresses."
- The list itself, and the security guide's "must", are carried in
  [SEC §6](stripe-security.md#allowlist-stripes-webhook-ips-too-and-use-https-with-tls-12-or-13).

[MEASURED] The code copy at `9ab0ea5b`, 2026-10-20:
- **No deployed load balancer exists to ask about.** Only `local` runs (`CLAUDE.md:88`, `:114`; `docs/environments.md`).
- **The runbook allows every address.** The runbook that would provision the balancer is
  `backend/docs/deployment/aws-ecs.md:101-120` (§1 step 6: "ALB listener on `:443` with an ACM certificate", a health
  check, a deregistration delay and optional mTLS). It has no step that restricts source addresses, names Stripe's IP
  list, or adds a web firewall.
- **Nothing else in the repository restricts addresses.** A grep of the copy for `ips_webhooks`, security groups,
  load-balancer resources and WAF finds only that document. `backend/deploy/ecs/taskdef.json` is the only deployment
  file.

**Answer:** no deployed endpoint exists today. A deployment built as the runbook says would admit every address, which
grades the rule **✗ Stripe**, unless someone adds the allowlist by hand. The two webhook paths, `/api/v1/webhooks/stripe`
and `/stripe-connect` (`webhook_routes.py:39-64`), share their listener with the phone's API, which must stay open to
everyone. An allowlist therefore has to be scoped to those two paths, not to the whole listener *(opinion: how to
build it on AWS was not read)*.

### R-SECURITY-2 — Test and live: objects never cross; which secret signs a test event at a live Connect endpoint is not stated

[DOCS] read on 2026-10-20:
- https://docs.stripe.com/keys: "Each mode has its own set of API keys, and objects in one mode aren’t accessible to
  the other."
- https://docs.stripe.com/testing-use-cases: a general sandbox has its own credentials ("Copy the test API keys for
  the sandbox. Copy the sandbox account ID.") and settings ("Isolate settings completely for each sandbox").
- https://docs.stripe.com/sandboxes: "You can’t create connections between a Connect platform’s sandbox and
  connected account sandboxes."
- https://docs.stripe.com/connect/webhooks: "You must define separate webhook endpoints for your sandbox accounts to
  receive events for those accounts."
- **Every club account Rakieta opens lives in the mode of the key that opened it.** Rakieta opens every club account
  itself, with `POST /v2/core/accounts` (`stripe_payments.py:317-347`), and never connects one through OAuth. The
  sandbox is `acct_1US89K5y1DB8chHb` ([SB](stripe-sandbox.md)).

[ABSENT] Whether a live connected account can carry the same `acct_` id as a test one. This is the OAuth case, where
an existing account is connected in both modes. No page read states it. Rakieta never connects accounts through OAuth,
so for Rakieta the case does not arise.

[DOCS] https://docs.stripe.com/webhooks (read 2026-10-20) says three things about signing secrets:
- "Stripe generates a unique secret key for each endpoint. If you use the same endpoint for both test and live API
  keys, the secret is different for each one."
- "To aid with testing, Stripe sends an additional signature with a fake `v0` scheme, for test events."
- https://docs.stripe.com/connect/webhooks: "your production webhook URLs receive both live and test webhooks … We
  recommend that you check the `livemode` value".

[ABSENT] Which secret signs a **test** event delivered to a **live** Connect endpoint: that endpoint's own secret, or
a test-mode one. It is not on webhooks, connect/webhooks, keys, sandboxes or testing-use-cases (2026-10-20). A
question for Stripe support.

**What each case means for Rakieta.** The Connect route checks against one secret only,
`STRIPE_CONNECT_WEBHOOK_SECRET` (`webhook_routes.py:53-64`).
- If test events come signed with a different secret, they fail verification with a 400 and change nothing.
- If they come signed with the live endpoint's secret, they pass, and only `livemode` would tell them apart. Rakieta
  never reads it.

### R-SECURITY-4 — A padded key: Stripe never promises to trim it; HTTP's own rules explain three of the four cases

[ABSENT] Any mention of whitespace in a key, of trimming, or of tolerance. Looked in https://docs.stripe.com/keys,
https://docs.stripe.com/api/authentication, https://docs.stripe.com/keys-best-practices and
https://docs.stripe.com/error-handling (2026-10-20).

[DOCS] https://docs.stripe.com/api/authentication (2026-10-20): "The Stripe API authenticates requests using HTTP
Basic Auth … If you need to authenticate using bearer auth … use `-H "Authorization: Bearer …"`".
stripe-python 15.6.1 sends the key exactly as given, without stripping it: `"Authorization": "Bearer %s" %
(options.get("api_key"),)` (`stripe/_api_requestor.py:557`, read in the backend's environment on 2026-10-20).

[DOCS] RFC 9110, *HTTP Semantics* (https://www.rfc-editor.org/rfc/rfc9110.html, read 2026-10-20):
- §5.5: "A field value does not include leading or trailing whitespace." A parser "MUST exclude such whitespace prior
  to evaluating the field value".
- §11.4: `credentials = auth-scheme [ 1*SP ( token68 / #auth-param ) ]`. One *or more* spaces may separate `Bearer`
  from the key.

So a trailing space, a trailing tab and a leading space all fall within HTTP's own grammar. A leading tab
(`Bearer` SP HTAB key) does not: Stripe accepting it is Stripe's own leniency.

[MEASURED] read via the SDK in the copy on 2026-10-20 at 08:27 UTC, with the default synchronous client. The
platform's test secret key padded four ways (a trailing space, a trailing tab, a leading space, a leading tab) each
answered `GET /v1/accounts/acct_1US95f5y1DMwE3zY`. Together with BR S2 (the aiohttp client, a leading space and a
tab), Stripe accepted every padding tried.

**Answer:** Stripe promises nothing. Three of the cases rest on HTTP itself; the leading tab rests on leniency that no
page promises. Rakieta's key refusals remain the only guard of its own.

### R-SECURITY-4 — An organisation key needs `Stripe-Context` on every account call; the adapter never sends it

[DOCS] https://docs.stripe.com/keys/organization-api-keys (read 2026-10-20, *(translated)*):
- "All organization API keys use the `sk_org` prefix, regardless of permission level. (There is no `rk_org`
  prefix.)"
- "All API requests made with an organization API key that target a specific account must include the
  `Stripe-Context` header to identify the affected account."
- "All API requests made with an organization API key must include the `Stripe-Version` header."
- For a connected account, the context is "a path that identifies both the platform and the connected account" in the
  form `acct_platform/acct_connected`.
- "Organizations have no publishable API keys … you must use existing account-specific publishable keys for
  client-side operations."

[DOCS] https://docs.stripe.com/context (en-US, 2026-10-20):
- "The `Stripe-Context` header supersedes the `Stripe-Account` header".
- "When you make an API request targeting an account other than that of the API key, you must identify the intended
  account by including the `Stripe-Context` header."

**The code.**
- **The adapter never sends `Stripe-Context`.** A grep of `backend/app` finds no `stripe_context`. Club calls carry
  only `stripe_account` (`stripe_payments.py:396-600`), and platform calls carry no account at all (customers,
  setups, v2 accounts, `:196-374`). stripe-python adds the header only when `stripe_context` is passed
  (`_api_requestor.py:564-566`).
- **The key checks don't name `sk_org_`** (`config.py:99-102`; [SEC Pitfalls](stripe-security.md#pitfalls)).

**Answer:** an `sk_org_` key cannot drive the adapter's calls, by Stripe's own "must":
- every platform call targets an account (the platform's) without a context;
- every club call names the club in the superseded header, and without the platform in the path.

[ABSENT] The error Stripe answers when `Stripe-Context` is missing. It is not on organization-api-keys, context, keys
or error-handling (2026-10-20). It can't be measured either: the sandbox has no organisation key, and making one is a
write. A question for Stripe support.

### R-SECURITY-5 — v2 permissions are `v2_account_storer_*`; an unknown key is a 401 on v2 as on v1

[DOCS] https://docs.stripe.com/keys/permissions-reference (read 2026-10-20; none of these rows is marked "(Direct)"):

| Method | Endpoint | Permission |
|---|---|---|
| POST | `/v2/core/accounts` | `v2_account_storer_write` |
| GET | `/v2/core/accounts/{id}` | `v2_account_storer_read` |
| POST | `/v2/core/accounts/{id}` | `v2_account_storer_write` |
| POST | `/v2/core/account_links` | `v2_account_storer_write` |

So one permission, `v2_account_storer_write`, covers both v2 calls the adapter makes (`stripe_payments.py:321`,
`:355`).

[DOCS] What a refused key gets, read on 2026-10-20:
- https://docs.stripe.com/keys: "If a request doesn’t include a valid key, Stripe returns an invalid request error. If
  a request includes an expired key, Stripe returns an authentication error."
- https://docs.stripe.com/keys/restricted-api-keys: a key without a permission gets "an invalid request error", seen
  as "`403 ERR`" in its request log, and "the response body includes an error message explaining which permissions to
  add".
- https://docs.stripe.com/error-handling?lang=python *(translated)*: `stripe.AuthenticationError` means "Stripe can't
  authenticate you with the information provided — … make sure you're not using a key that you've rolled or revoked".
  `stripe.PermissionError` means "The API key used for this request doesn't have the necessary permissions."
- No page read says anything specific to v2.

[MEASURED] read via the SDK in the copy, 2026-10-20 08:27 UTC:
- **Unknown keys.** An unknown `sk_test_…` key and an unknown `rk_test_…` key on
  `GET /v2/core/accounts/acct_1US95f5y1DMwE3zY` each got `stripe.AuthenticationError`, HTTP **401**, error type
  `invalid_request_error`, message "Invalid API Key provided: sk_test_*…0000". The answer was identical on
  `GET /v1/accounts/{id}`.
- **A key without access.** The platform's publishable key on the same v2 read got `stripe.PermissionError`, HTTP
  **403**, "Permission denied. API Key does not have permission to access account …".

**Answer:** v2 behaves as v1. Stripe types an unknown key `invalid_request_error`, as the keys page says, but sends a
401, which stripe-python raises as `AuthenticationError`. A key without access is a 403 `PermissionError`. The adapter
lists both classes among its outages (`stripe_payments.py:72-78`), which is what F-SECURITY-5.1 is about.

[ABSENT] The answer for an **expired** (rolled or revoked) key was not measured, because making one needs the
Dashboard (a write). The keys page says "authentication error": the same class as the measured unknown key.

### R-SECURITY-6 — stripe-python documents its debug level, not what it writes; no redaction exists, only the logger's level

[ABSENT] A docs.stripe.com page on stripe-python's logging (web search, 2026-10-20).

[DOCS] stripe-python's README, as shipped in the installed 15.6.1 (`stripe-15.6.1.dist-info/METADATA`, *Logging*; the
same text is on https://pypi.org/project/stripe/), read on 2026-10-20: "The library can be configured to emit logging
that will give you better insight into what it's doing. The `info` logging level is usually most appropriate for
production use, but `debug` is also available for more verbosity."
- It names three switches: `STRIPE_LOG=debug|info`, `stripe.log = 'debug'`, and Python's logging module,
  `logging.getLogger('stripe').setLevel(logging.DEBUG)`.
- It never says what `debug` writes.

[MEASURED] the library's source in the backend's environment, read on 2026-10-20:
- **The request.** `_api_requestor.py:765-768` logs "Post details" with the encoded request parameters at DEBUG.
- **The answer.** `:797-798` logs "API response body" with the whole body at DEBUG.
- **Where it goes.** Both lines go to the `stripe` logger (`_util.py:36`, `:54-58`). They also go to stderr when
  `stripe.log` or `STRIPE_LOG` is `debug` (`_util.py:45-58`).
- **No redaction.** Neither function has a filter, a mask or a list of fields.

[ABSENT] A supported way to redact `client_secret`. There is none in the README, the source or the docs.

The supported control is the level. Setting `logging.getLogger('stripe').setLevel(logging.INFO)`, the README's third
switch, keeps both DEBUG lines out. The INFO lines carry only the method, URL, path and status (`:765`, `:797`).

**In Rakieta:**
- The root logger's level comes from `LOG_LEVEL`: DEBUG in `local` and `development`, INFO in `staging` and
  `production` (`config.py:134-143`, `logging.py:50`).
- Nothing sets the `stripe` logger's own level: a grep finds no `getLogger("stripe")`.

### R-SECURITY-10 — Reads for a club use the platform's Connect allocation; whose per-second bucket, and what an overrun does, are unpublished

[DOCS] https://docs.stripe.com/rate-limits (en-US, read 2026-10-20):
- "In general, rate limits are measured in API requests per second, per Stripe account."
- "Requests to `GET /v1/payment_intents/{id}` for different PaymentIntent IDs count toward the same endpoint limit."
- On read allocations: "Connect platforms use a separate allocation to make read requests on behalf of their
  connected accounts using either their secret API key or OAuth access tokens. This allocation is also 500 requests
  per transaction based on the aggregate transaction count across its connected accounts."
- "Your account’s read API requests must not exceed an average of 500 per transaction"; "Every account, regardless of
  transaction count, has a minimum allocation of 10,000 read requests per month."

So a platform's `GET` with `Stripe-Account` counts against the **platform's** Connect read allocation.

[DOCS] https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api (read 2026-10-20) is the only page
found that ties `Stripe-Account` to a rate limit: "If you’re a Connect platform making requests on behalf of a
connected account using the `Stripe-Account` header, you’re subject to regular Stripe rate limits, which is 100
operations per second." It does not say whose bucket.

[ABSENT] Whether that per-second limit is counted on the platform or on the club. Looked in rate-limits,
connect/authentication, recording-usage-api and a web search (2026-10-20). A Stripe community thread
(insiders.stripe.dev) was reported as saying each connected account has its own limit, but it could not be fetched,
so it is not cited. A question for Stripe support.

[ABSENT] What Stripe does when the platform's read allocation is exceeded. The page gives "must not exceed" and
"Request a limit increase … through Stripe Support", but no error, status or enforcement. Its 429 reasons
(`Stripe-Rate-Limited-Reason`: `global-rate`, `endpoint-rate`, `global-concurrency`, `endpoint-concurrency`,
`resource-specific`) name no allocation. A question for Stripe support.

### R-SECURITY-11 — Still no documented lifetime; on the sandbox a secret works a day later and after its payment has finished

[ABSENT] (re-checked 2026-10-20) A lifetime for a PaymentIntent's or SetupIntent's `client_secret`. Looked in the
PaymentIntent object and confirm references and the keys pages, as well as the pages in
[SEC §3](stripe-security.md#stripe-documents-no-lifetime-for-a-client-secret).

[DOCS] What does end a secret's power over money is its status. https://docs.stripe.com/payments/paymentintents/lifecycle
(en-US, 2026-10-20): "Cancellation invalidates the PaymentIntent for future payment attempts, releases any held funds,
and can’t be undone." BR H7 measured the same thing: after the let-go, the secret can't hold money.

[MEASURED] read via the SDK in the copy, 2026-10-20 08:27 UTC:
- **The oldest setup on the platform.** `seti_1USA5i5y1DB8chHblZDHrQYr` was created 2026-10-19 06:30:38 UTC and
  stands at `requires_payment_method`. Read with the publishable key and its client secret 25,9 hours later, it
  answered.
- **The oldest payment on the test club.** `pi_3USA7e5y1DMwE3zY0Dy5rOZd` was created 2026-10-19 06:32:38 UTC, is
  `succeeded`, and is for 40,00 zł. Read with the publishable key, the club's account and its client secret 25,9 hours
  later, it answered.
- **A wrong secret, for contrast.** On the same payment it got `InvalidRequestError` 400
  `payment_intent_invalid_parameter`: "The client_secret provided does not match the client_secret associated with the
  PaymentIntent."
- **Nothing older exists to test.** The sandbox holds no older objects (145 setups and 112 club payments were
  scanned).

**Answer:** there is no expiry to rely on. A secret still reads its object at least a day later, and after the payment
has finished. Its power to move money ends only with its intent's status.

### R-SECURITY-13 — Ten declined tries end a payment on the sandbox; the club's Radar counts every try; the platform's rules can't reach a full-Dashboard club

**How many confirmations.**

[DOCS] https://docs.stripe.com/payments/paymentintents/lifecycle (en-US, 2026-10-20): "PaymentIntents might also
automatically transition to `canceled` if they’re confirmed too many times." No number is given there, in the confirm
reference, or in the PaymentIntent object. The object's `cancellation_reason` lists the reasons "generated by Stripe
internally (`failed_invoice`, `void_invoice`, `automatic`, or `expired`)"
(https://docs.stripe.com/api/payment_intents/object, 2026-10-20).

[MEASURED] read via the SDK in the copy on 2026-10-20: `pi_3USPKC5y1DMwE3zY00HIKsMU`, a 40,00 zł share on the test
club made by FILL BR S5.
- It holds **10 charges**, all `failed` with `generic_decline`: the server's hold without the player at 22:46:37 UTC,
  then nine confirmations from the phone at 22:46:38–48.
- It was `canceled` at 22:46:49 UTC, one second after the tenth, with `cancellation_reason: null` (not `automatic`).
- The next confirmation answered `payment_intent_unexpected_state` (FILL breaker S5).

So on the sandbox, Stripe's ceiling is **ten declined attempts on one PaymentIntent**.

[ABSENT] Whether live mode uses the same number. A question for Stripe support.

**Does the club's Radar count tries made with the platform's publishable key?**

[DOCS] read on 2026-10-20:
- https://docs.stripe.com/connect/radar: "Direct charges: Paid directly to a connected account; Stripe applies only the
  collecting account’s Radar configuration and rules". For "Direct for connected accounts with access to the Stripe
  Dashboard", the rules used are the "Connected account" ones.
- https://docs.stripe.com/radar/rules/reference: "`total_charges_per_customer_hourly` represents the number of
  previous charge attempts from a given customer in the preceding hour". Its bounded counters count charges "on your
  account". Velocity attributes have "a common use case … to reduce card testing".

[MEASURED] read via the SDK in the copy on 2026-10-20: `pi_3USPFY5y1DMwE3zY0346e1bw` (BR S1) holds **five charges on
the club**:
- the server's hold at 22:41:48 UTC, declined;
- three declines by a script holding only the publishable key and the secret (22:41:51–54);
- one authorisation at 22:41:55.

Each charge carries a Radar outcome (`risk_level: normal`; risk scores 5, 47, 63, 59, 53) and no rule. So each try
from the phone is a charge attempt on the club's own account, which is exactly what the club's Radar evaluates and
what its velocity attributes count. Whether the club can write velocity rules depends on its Radar plan ("if your plan
supports it", https://docs.stripe.com/disputes/prevention/card-testing, *(translated)*).

**Can the platform apply its own rules?**

[DOCS] read on 2026-10-20:
- https://docs.stripe.com/radar/risk-settings, *Apply Radar rules to direct charges*: the options are "Only connected
  accounts", "Only my platform" and "Both my platform and connected accounts", followed by "These settings apply only
  to connected accounts controlled solely by your platform."
- https://docs.stripe.com/connect/radar's configuration table: for "Connected accounts with access to the Stripe
  Dashboard", the "Connected account Dashboard" is "✓ Supported" and the "Platform account Dashboard Connect page" is
  "❌ Unsupported".

Rakieta's clubs have `dashboard: full` (`stripe_payments.py:325`). **Answer: no.** A full-Dashboard club's Radar is
configured only by the club.

### R-SECURITY-13 — After a burst: the club is emailed; Stripe may pause or hold a reserve; the platform sees it in its Dashboard only

[DOCS] read on 2026-10-20:
- **Stripe's automatic blocks.** https://docs.stripe.com/disputes/prevention/card-testing *(translated)*: "If you use
  the latest version of the Stripe Payment Element or Checkout … When we detect that you're experiencing a card
  testing attack, we dynamically choose interventions … You'll see these payments marked as `Blocked by Stripe`."
  Rakieta uses `CardField` and `confirmPayment` ([SEC §4](stripe-security.md#4-the-phone-the-connected-account-and-pci-scope)),
  not the Payment Element, so the page does not promise these to it.
- **The club is told.** https://docs.stripe.com/radar/analytics/fraud-alerts (en-US): "When Stripe detects a potential
  fraud attack on your account, we notify you with: **Email notification** … **Dashboard notification**". A direct
  charge's account is the club's.
- **Automatic tightening.** https://docs.stripe.com/radar/risk-settings: "The dynamic risk thresholds control
  automatically blocks additional elevated and high-risk payments when your account is under fraud pressure". This
  applies where the club's Radar plan supports risk settings.
- **Managed Risk.** https://docs.stripe.com/connect/risk-management/managed-risk (en-US). Stripe "might slow or pause
  payouts, or pause the connected account’s ability to process charges", "might hold a reserve", or "might deactivate
  the connected account". These answer signals "such as elevated losses, spikes in chargeback rates, or refunds".
  - Who is told: "Stripe notifies your connected accounts of any risk interventions through email and a notification
    in their Stripe Dashboard".
  - What the platform sees: "You can view Stripe’s risk assessments, interventions, and connected account actions in
    your platform Dashboard."
  - Carried in [stripe-connect.md](stripe-connect.md#stripe-may-pause-a-clubs-charges-or-payouts-hold-a-reserve-or-close-it).

[ABSENT] Whether a card-testing burst on a club's direct charges by itself leads to a reserve or a pause, and whether
the platform is told by an event or an email rather than only its Dashboard. Not on card-testing, fraud-alerts,
risk-settings, managed-risk, connect/radar, or https://support.stripe.com/questions/i-suspect-my-account-is-experiencing-a-card-testing-attack-what-do-i-do
(2026-10-20). A question for Stripe support.

### R-SECURITY-15 — Stripe documents that its return adds the payment's id and client secret; the React Native SDK can only use a custom scheme

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (en-US, 2026-10-20):
- On the web redirect: "When the customer finishes the authentication process, the redirect sends them back to the
  `return_url` you specified … The redirect also adds `payment_intent` and `payment_intent_client_secret` URL query
  parameters that your application can use to identify the PaymentIntent associated with the purchase."
- On iOS: "After webview-based authentication finishes, Stripe redirects the user back to your app or web page with
  the `return_url` you provided."
- https://docs.stripe.com/api/payment_intents/confirm, `return_url`: "If you’d prefer to redirect to a mobile
  application, you can alternatively supply an application URI scheme."

**The code.** `@stripe/stripe-react-native` 0.38.6 sets the confirm's `return_url` to `<urlScheme>://safepay`, both
on iOS (`ios/Mappers.swift:769-771`, used at `ios/StripeSdk.swift:294` for setups and `:883` for payments) and on
Android (`android/src/main/java/com/reactnativestripesdk/utils/Mappers.kt:62-67`). Rakieta's scheme is `rakieta`
([AU §4](stripe-authentication.md#the-way-back-from-the-banks-own-app)).

**What the return would carry.** Stripe documents that its redirect appends the payment's id and its client secret,
and does not say the mobile return differs. The way back would then read
`rakieta://safepay?payment_intent=pi_…&payment_intent_client_secret=…` *(unverified: inferred from the web wording,
not measured, because the bank's page needs a browser, SB §2)*.

What another app that claims `rakieta` could do with it, adding the publishable key and the club's account id:
- read the payment's status, amount and currency (the secret "lets the client access … status, amount, currency",
  [SEC §3](stripe-security.md#a-client-secret-can-complete-the-payment-so-only-its-customer-may-hold-it));
- confirm it with another card while it waits for a card, since `confirmation_method` is automatic (same anchor).

After a successful check the share stands at `requires_capture`. From there a script holding the secret could
neither change its amount nor capture it (BR S6).

**Universal links.** The pages disagree, and for this app the React Native page governs.
- https://docs.stripe.com/payments/accept-a-payment?payment-ui=mobile&platform=react-native (en-US, 2026-10-20): "1.
  Register a custom URL. Universal links aren’t supported."
- The 3-D Secure page allows "a custom URL scheme or universal link", for the native iOS SDK and for React Native's
  `urlScheme`.
- 0.38.6 builds the way back as `scheme + "://safepay"`, so a universal (https) link can't be expressed through
  `urlScheme`. The React Native page's "aren’t supported" matches what the SDK in the copy can do.

[ABSENT] Whether the mobile SDK's way back, as opposed to the web redirect, carries the query parameters. It is not on
the pages read, and can be measured only on a device with a challenge card.

### R-SECURITY-27 — The Accounts v2 guide for Rakieta's case allows HTTP while testing; only the marketplace guide says creation fails

[DOCS] Accounts v2 pages that create links with `POST /v2/core/account_links`, read on 2026-10-20:
- **SaaS** (https://docs.stripe.com/connect/saas/tasks/onboard): a platform whose clubs are merchants taking direct
  charges, which is Rakieta's case. "You can use HTTP for your `refresh_url` and `return_url` while you’re in a testing
  environment (for example, to test locally), but live mode only accepts HTTPS. You must update any testing URLs to
  HTTPS URLs before you go live."
- **Marketplace** (https://docs.stripe.com/connect/marketplace/tasks/onboard): a recipient configuration. "You must use
  HTTPS for your `return_url` and `refresh_url`, both in production and in testing environments (for example, to test
  with localhost). The Account Link creation process fails if you use HTTP."
- **The v2 API reference** (https://docs.stripe.com/api/v2/core/account-links/create): `return_url` is "The URL that
  the user will be redirected to upon completing the linked flow". Neither URL's description names a scheme. The
  listed errors are `accounts_v2_access_blocked`, `configs_must_match_to_use_account_links`, `not_found` and
  `account_rate_limit_exceeded`, with no error for an http URL.
- **The older guide** (https://docs.stripe.com/connect/hosted-onboarding): it shows only `/v1/account_links`, even with
  `accounts-namespace=v2`, and carries the same "HTTP … while you’re in a testing environment" sentence.

**The code.** Rakieta's link asks for `configurations: ["merchant"]` (`stripe_payments.py:349-369`), on an account
opened with the merchant configuration (`:337-341`). That is the SaaS guide's case.

**Answer:** the page that governs Rakieta's case allows HTTP in a testing environment. That matches BR S4 and S5,
measured on 2026-10-20: links were made with `http://localhost` ways back for `acct_1US95f5y1DMwE3zY` and for the new
v2 account `acct_1USPFh5y1DXbCdOQ`. The marketplace guide's "fails" is the outlier, written for a configuration Rakieta
doesn't use. Deployed environments already require `https://` (`config.py:857`).

[ABSENT] A promise that the sandbox will keep accepting HTTP. The SaaS guide's sentence is the only statement, and no
deprecation is listed on the v2 account-links reference. A question for Stripe support.
