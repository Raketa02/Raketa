# Stripe security — keys, secrets, notices and what a client may send

What Stripe documents about keeping a Stripe integration secure, read on **2026-10-19** for the way
Raketa uses Stripe at `9ab0ea5b`, with the product's own anchors beside each fact. Written for the
payments pass on PRD #530 (topic `security`). The sandbox itself is measured in
[`stripe-sandbox.md`](stripe-sandbox.md); its *Differences* D1 (no registered endpoint), D2 (API
version) and D6 (refund notices dropped) are not repeated here, only cited.

**Sources.** Stripe's own: the Stripe MCP tools (`search_stripe_documentation`,
`stripe_api_search`, `list_available_accounts_or_orgs`, `get_stripe_account_info`) and
docs.stripe.com pages fetched directly. No write tool was used, and no key or secret value was
read or copied. **A note on language:** several docs.stripe.com pages were served to the fetcher
in Spanish. A quote taken from one of those is Stripe's Spanish text translated here and marked
*(translated)*; every other quote is Stripe's English as the documentation search returned it.

**How Raketa uses Stripe, for this topic.** A club is a connected account opened with **Accounts
v2**, `dashboard: full`, the `merchant` configuration, `fees_collector` and `losses_collector`
both `stripe` (`backend/app/modules/payments/infrastructure/stripe_payments.py:317-347`). A player
is a v1 Customer on the platform; a card is saved there with a SetupIntent (`usage: off_session`,
`:203-222`), cloned onto the club's account per charge and held with a PaymentIntent created on the
club's account (`capture_method: manual`, `off_session: true`, `:466-542`) — a **direct charge**.
The phone uses `@stripe/stripe-react-native` 0.38.6 (`frontend_player/package.json:34`): Stripe's
`CardField`, `confirmSetupIntent` on the platform, and `confirmPayment` with `stripeAccountId` set to
the club's account (`frontend_player/src/shared/lib/platform/payments.tsx:220-229`, `:345-415`).
Two webhook endpoints, each with its own secret: `POST /api/v1/webhooks/stripe` and
`/stripe-connect` (`backend/app/modules/payments/presentation/webhook_routes.py:39-64`,
`backend/app/bootstrap/composition.py:980-987`). Currency złoty, country Poland.

---

## 1. API keys

### Only the publishable key may leave the server

[DOCS] https://docs.stripe.com/keys (read 2026-10-19) *(translated)*: the key-types table marks the
**publishable key** `pk_…` "safe to expose: yes" — "an API key for Stripe.js, Elements and the
mobile SDKs. It can identify your account and create tokens or PaymentMethods from payment details,
but it can't perform sensitive operations, such as creating charges or reading account data. You
can include it in front-end code or in apps you distribute." The **restricted key** `rk_…`, the
**secret key** `sk_…` and the **organization key** `sk_org_…` are each "safe to expose: no".
"Only publishable keys are safe to expose outside your application's back end."

[DOCS] https://docs.stripe.com/keys-best-practices (read 2026-10-19): "Secret API keys are a form of
account credentials, like a username and password. Unlike publishable keys, which are safe to
include in webpages and apps, secret keys must stay in your server environment. If an unauthorized
party obtains your secret API key, they can make unauthorized charges, access customer data, or
disrupt your integration." — "**Never embed secret API keys in applications** … For client-side
use cases such as client tools, SDKs, and mobile apps, embed publishable keys instead."

**In Raketa:** the secret key is a server setting only (`backend/app/core/config.py:402`); the
publishable key reaches the phone in two answers — opening a setup
(`backend/app/modules/payments/application/setup.py:126-130`) and a refused share waiting for its
player (`backend/app/modules/payments/application/seat_charges.py:854-859`).

### Stripe prefers restricted keys to secret keys

[DOCS] https://docs.stripe.com/keys/restricted-api-keys (read 2026-10-19): "Stripe recommends always
using RAKs instead of unrestricted secret keys"; the comparison table's last row: secret key "Use
sparingly and protect aggressively", restricted key "**Preferred**: Use restricted keys wherever
possible". "All Stripe APIs support restricted API keys." "In your server environment, restricted
API keys are drop-in replacements for secret API keys." "Create a restricted API key in a sandbox
before creating a live-mode key." https://docs.stripe.com/keys *(translated)*: secret keys — "we
don't recommend using secret keys for new use cases and, for existing integrations, we recommend
migrating secret-key usage to RAKs." These are recommendations, not requirements.

**In Raketa:** the settings accept `sk_` and `rk_` keys alike (`config.py:99-102`); which kind the
user placed in `backend/.env` was not read (it holds secrets).

### A restricted key that lacks a permission fails as an invalid request

[DOCS] https://docs.stripe.com/keys/restricted-api-keys (read 2026-10-19): "If a restricted API key
doesn't have the correct permissions to complete an API request, Stripe returns an invalid request
error." The same page's migration steps: "If you find any error messages such as `403 ERR`, edit
the restricted key's permissions to add the actions that failed", and "If the restricted key sent
with a request doesn't have the correct permissions, the response body includes an error message
explaining which permissions to add." https://docs.stripe.com/keys/permissions-reference: permissions
are named per endpoint, for example `POST /v1/account_links` → `account_link_write`,
`GET /v1/accounts/{id}` → `connected_account_read`, both marked "(Direct)".

[ABSENT] The permission names for the **v2** `core/accounts` and `core/account_links` endpoints the
product calls were not in the part of the permissions reference read (only v1 rows were returned).

### Secret keys live in a vault — never in source, logs or error pages

[DOCS] https://docs.stripe.com/keys-best-practices (read 2026-10-19): "**Never put secret API keys in
source code**: Bad actors continuously scan public repositories for Stripe API keys. Even private
repositories can be exposed through development environments." "Use your platform's secrets
management tools (such as a secrets vault) … If your platform doesn't provide a secrets vault, use
environment variables instead." It lists **AWS Secrets Manager** first. "If you put Stripe API keys in environment variables, be careful not to expose these variables to
your users. For example, don't show environment variables on error pages, and don't make
diagnostic modes available to a broad audience." "Share secret API keys through your platform's
secret-management tools—not in emails, chat messages, or customer support messages. **Stripe never
asks you for your secret API key.**"

**In Raketa:** the production task definition reads all four Stripe values from AWS Secrets
Manager (`backend/deploy/ecs/taskdef.json:51-54`); a laptop reads them from `backend/.env` and
`backend/.env.docker`, both ignored by git ([MEASURED] `git check-ignore -v` → `.gitignore:7` and
`:8`, 2026-10-19); the template holds placeholders only (`backend/.env.example:179-184`); the
settings' refusals never print a key (`config.py:397-401`).

### Rotate on any exposure; old and new keys overlap for up to 7 days

[DOCS] https://docs.stripe.com/keys-best-practices (read 2026-10-19): "**Rotate secret API keys
periodically**"; "If a [key] is exposed or compromised, rotate it immediately even if you aren't
sure anyone saw it. Treat any exposure as a potential compromise. *Exposure* means the key became
visible somewhere it shouldn't have been, such as a public repository, a log file, or an email."
"If Stripe detects an exposed [key], we notify you and request that you rotate the key. In some
cases, Stripe deactivates the key proactively … Stripe doesn't guarantee detection of all exposed
or compromised keys." https://docs.stripe.com/keys *(translated)*: "when you roll a key in the
Dashboard, both the old and the new key keep working for up to 7 days"; roll "if a team member
with access to the key leaves your organization or changes role".

### Access policies limit where a key works

[DOCS] https://docs.stripe.com/keys, *Access policies* (read 2026-10-19) *(translated)*: "Stripe
recommends configuring access policies on all live mode keys. That way you are notified of any
unauthorized access and can roll the keys accordingly." Two kinds: **IP addresses** (IPv4 or CIDR)
and **Advanced** (allowed ASNs, allowed countries, blocked sources: anonymous VPNs, public proxies,
residential proxies, Tor exit nodes), combined with AND. "You can separate test environments from
production by assigning different policies to their keys." Access policies replace the older
"IP restrictions".

### A key that has not paid out for 180 days loses payout rights

[DOCS] https://docs.stripe.com/keys, *Restore access to an API key* (read 2026-10-19)
*(translated)*: "Access to an API key may be limited if it hasn't been used to create transfers,
payouts or update payout destinations for more than 180 days. You can't use a key with limited
access to create payouts and transfers or to create payout destinations." It can be restored in
the Dashboard.

**In Raketa:** the club payouts job creates payouts with the platform key on each club's account
(`stripe_payments.py:393-462`).

### Dashboard sign-in: multi-factor, roles, sandbox access levels

[DOCS] https://docs.stripe.com/security (read 2026-10-19): "We recommend passkeys or hardware
security keys because they're resistant to phishing. SMS-based MFA is vulnerable to SIM-swapping
and interception, so use it only as a last resort." "From the Dashboard, you can assign different
detailed roles to enable least-privilege access for your employees". https://docs.stripe.com/sandboxes/dashboard/manage-access:
"New sandboxes use the **Private** access level by default"; a **Sandbox User** role gives sandbox
access "without granting access to any details of your live account".

---

## 2. Keeping test and live apart

### Each mode has its own keys, and objects never cross

[DOCS] https://docs.stripe.com/keys, *Sandbox versus live mode* (read 2026-10-19) *(translated)*:
"Each mode has its own set of API keys, and objects from one mode aren't accessible from the
other." Sandbox keys start `pk_test_`, `rk_test_`, `sk_test_`; live keys `pk_live_`, `rk_live_`,
`sk_live_`. https://docs.stripe.com/keys-best-practices: "Make sure your developers aren't using live
keys when a Sandbox key is appropriate."

**In Raketa:** a live secret key outside production and a test secret key in production both stop
the process at start (`config.py:915-934`); only `STRIPE_SECRET_KEY` is checked — the publishable
key is checked for presence only (`config.py:902`), and the phone decides by its prefix
(`payments.tsx:180-182`; Google Pay's test switch follows it, `:354`).

### General sandboxes isolate settings; the test mode sandbox shares some with live

[DOCS] https://docs.stripe.com/testing-use-cases (read 2026-10-19): "For new integrations, use a
general sandbox instead of the test mode sandbox. General sandboxes isolate settings and data from
live mode"; in the test mode sandbox, "you might also change them in live mode."
https://docs.stripe.com/stripe-apps/build-backend: "`livemode=false` … doesn't distinguish a
general sandbox from the test mode sandbox."

### Production Connect endpoints also receive test events — check `livemode`

[DOCS] https://docs.stripe.com/connect/webhooks (read 2026-10-19): "For Connect webhooks, your
development webhook URLs receive only test webhooks, but your production webhook URLs receive both
live and test webhooks. This is because you can perform both live and test transactions under a
production application. **We recommend that you check the `livemode` value when receiving an event
webhook** to determine whether users need to take action." (A recommendation.)

[ABSENT] Whether a connected account keeps the same `acct_` id in test and live mode, and which
secret signs a test event delivered to a live Connect endpoint, are not stated on the pages read
(connect/webhooks, webhooks, keys, testing-use-cases).

### A sandbox needs its own webhook endpoints

[DOCS] https://docs.stripe.com/connect/webhooks (read 2026-10-19): "You must define separate webhook
endpoints for your sandbox accounts to receive events for those accounts." (A requirement.) The
sandbox has none registered today: [`stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination`](stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination) (D1).

### Both servers are on the sandbox, in test mode

[MEASURED] `stripe` · `list_available_accounts_or_orgs` → one account, `acct_1US89K5y1DB8chHb`
"Raketa sandbox", `livemode: false`; `stripe-club` · `get_stripe_account_info` →
`acct_1US95f5y1DMwE3zY` "Robert Club" · 2026-10-19. Agrees with
[`stripe-sandbox.md#1-mode`](stripe-sandbox.md#1-mode).

---

## 3. Client secrets

### A client secret can complete the payment, so only its customer may hold it

[DOCS] https://docs.stripe.com/api/payment_intents/object, `client_secret` (read 2026-10-19): "The
client secret of this PaymentIntent. Used for client-side retrieval using a publishable key. The
client secret can be used to complete a payment from your frontend. **It should not be stored,
logged, or exposed to anyone other than the customer.** Make sure that you have TLS enabled on any
page that includes the client secret." The guides' glossary: it "lets the client access important
fields from the PaymentIntent (status, amount, currency) while hiding sensitive ones (metadata,
customer)"; and (https://docs.stripe.com/billing/subscriptions/acss-debit) "it can complete the
charge. Don't log it, embed it in URLs, or expose it to anyone but the customer." For a SetupIntent (https://docs.stripe.com/payments/payto/set-up-payment):
"Handle the client secret carefully, because it allows access to the SetupIntent. Don't log it,
embed it in URLs, or expose it to anyone but the customer."

### A publishable key with the client secret can confirm the PaymentIntent

[DOCS] https://docs.stripe.com/api/payment_intents/object, `confirmation_method` (read 2026-10-19):
"`automatic` (Default) PaymentIntent can be confirmed using a publishable key. After `next_action`s
are handled, no additional confirmation is required"; "`manual` All payment attempts must be made
using a secret key."

**In Raketa:** the product never sets `confirmation_method` (`stripe_payments.py:485-542`), so a
refused share's PaymentIntent is confirmable from the phone — with the card on file or with a newly
typed card (`payments.tsx:388-415`).

### Stripe documents no lifetime for a client secret

[ABSENT] Looked for an expiry of a PaymentIntent's or SetupIntent's `client_secret` in the
PaymentIntent object reference and the guides quoted above (2026-10-19): none is given. What a
secret can do follows its intent's status (`confirmation_method`, above). The only "expires after 1
hour" found is Stripe Identity's ephemeral key secret (https://docs.stripe.com/identity/verify-identity-documents),
which this product does not use.

**In Raketa:** the setup's secret is answered only to accepting the terms for the caller's own open
setup (`backend/app/modules/payments/presentation/routes.py:110-136`, `setup.py:151-169`); a
payment's secret only while it waits for its player (`stripe_payments.py:627-629`), only on its own
player's `GET /seat-charges/{id}` (`seat_charges.py:841-859`), with the club's account id and the
publishable key; neither is written to the event store
(`backend/app/modules/payments/domain/events.py:7`, `:122`). The phone keeps no persisted query
cache and logs nothing in payments ([MEASURED] grep of `frontend_player/src` and `app` for a
persister and `console.*`, 2026-10-19: none).

---

## 4. The phone: the connected account and PCI scope

### A direct charge is confirmed on the phone with the platform's publishable key and the club's id

[DOCS] https://docs.stripe.com/connect/authentication (read 2026-10-19): "**Server-side**: Include
the connected account ID in the `Stripe-Account` header on each request. **Client-side**: Pass the
connected account ID as an argument to the client library." React Native: `<StripeProvider
publishableKey="<<YOUR_PUBLISHABLE_KEY>>" stripeAccountId="{{CONNECTED_ACCOUNT_ID}}">`.
https://docs.stripe.com/connect/direct-charges?platform=react-native: "Transaction objects such as
`PaymentIntents` and `Charges` exist on the connected account, not on the platform."

### Stripe's own mobile card components keep the app at the lightest PCI form

[DOCS] https://stripe.com/guides/pci-compliance (read 2026-10-19) *(translated)*: **SAQ A** "when you
only use user-interface components from our official iOS or Android SDKs" — card numbers go from
the customer straight to Stripe; with custom code that handles card data "you may be responsible
for additional PCI DSS requirements (6.3 to 6.5)"; sending raw card data to the API is **SAQ D**;
"if you collect card data exclusively through a Connect platform", SAQ A, with the platform
providing the PCI documentation. React Native is not named in the guide.
https://docs.stripe.com/sdks/react-native lists the SDK's "**Card Element (Legacy)**: Use the basic
card field in your own payment UI" beside the recommended Payment Sheet.

**In Raketa:** the number is typed into Stripe's `CardField` and never reaches the app's own code
(`payments.tsx:6-20`, `:270-299`).

### Stripe tells each account which PCI form to file

[DOCS] https://docs.stripe.com/security (read 2026-10-19): "We analyze the user's integration method
and dynamically inform them of which PCI validation form to use. If a user integrates with Stripe
Elements, Checkout, Terminal SDKs, or our mobile libraries, we provide assistance in completing
their PCI validation form (Self-Assessment Questionnaire) in the Dashboard."
https://docs.stripe.com/security/guide: "As a business accepting payments, you must do so in a
PCI-compliant manner, and annually attest to this compliance."

### Brand, last four and expiry are out of PCI scope

[DOCS] https://docs.stripe.com/security/guide (read 2026-10-19): "Stripe returns non-sensitive card
information in the response to a charge request. This includes the card type, the last four digits
of the card, and the expiration date. This information isn't subject to PCI compliance, so you can
store any of these properties in your database. Additionally, you can store anything returned by
our API."

**In Raketa:** a saved card is kept as its method id, brand, last four and wallet
(`stripe_payments.py:146-158`).

---

## 5. Card testing

### Card testers prefer saving cards, and use the publishable key

[DOCS] https://docs.stripe.com/disputes/prevention/card-testing (read 2026-10-19) *(translated)*:
"**Card setup**: the preferred method of fraudsters, since validation and authorizations during card
setup usually don't appear on the cardholder's bank statement." "Card testers can take your
publishable key and use it to retry a large number of payments on your website." Card testing
raises decline rates, so all of a business's transactions look riskier to issuers.

### Stripe's prevention list: sign-in, rate limits, limits per account, CAPTCHA, Radar

[DOCS] same page (read 2026-10-19) *(translated)*: card testers target endpoints that "save the card"
or "make a payment". "You can reduce your exposure … by asking them to sign in or validate the
session before they can pay." Rate limits — "for example, if they use your integration to validate
cards by attaching them to new customers, an effective deterrent could be to limit the number of
new customers that can be created from a single IP address in 1 day." Detect unusual behaviour —
"Limit the number of cards that can be added to an account", "Limit the number of customers that
can be created from the same IP address". CAPTCHA — "Make sure the CAPTCHA requires validation on
all requests that enable card checks or payments with Stripe". Radar velocity rules "if your plan
supports it". Stripe's automatic controls come with the Payment Element or Checkout; otherwise
"include as much data as possible or implement your own controls".

**In Raketa:** five setups per player per day, refused before Stripe is asked
(`backend/app/modules/payments/domain/terms.py:31`, `payment_method.py:173-179`,
`errors.py:113-120`); every payment route needs a signed-in player.

### On a direct charge only the club's Radar runs

[DOCS] https://docs.stripe.com/connect/radar (read 2026-10-19): "**Direct charges**: Paid directly to
a connected account; Stripe applies only the collecting account's Radar configuration and rules."
For a connected account with the Stripe Dashboard, Radar is configured in the connected account's
Dashboard, not the platform's. https://docs.stripe.com/radar/risk-settings: a platform can apply its
own rules to direct charges, but "These settings apply only to connected accounts controlled solely
by your platform."

---

## 6. Webhook security

### Verify every signature over the raw body, with each endpoint's own secret

[DOCS] https://docs.stripe.com/webhooks (read 2026-10-19): "Without verification, an attacker could
send fake webhook events to your endpoint to trigger actions like fulfilling orders, granting
account access, or modifying records. Always verify that webhook events originate from Stripe
before acting on them." "Stripe requires the raw body of the request to perform signature
verification". "Stripe generates a unique
secret key for each endpoint. If you use the same endpoint for both test and live API keys, the
secret is different for each one. Additionally, if you use multiple endpoints, you must obtain a
secret for each one you want to verify signatures on." Manual verification: "To prevent downgrade
attacks, ignore all schemes that aren't `v1`" and "use a constant-time-string comparison".
https://docs.stripe.com/events/manage-webhook-endpoints: "The secret for a CLI-forwarded endpoint is
different from the secret for a Dashboard-managed endpoint—don't mix them up."

**In Raketa:** the raw body is passed unparsed (`webhook_routes.py:45-49`) to stripe-python's
`WebhookSignature.verify_header` (`backend/app/modules/payments/infrastructure/stripe_notices.py:84-100`);
unsigned, mis-signed or stale notices are a 400 and nothing is read; each endpoint has its own
secret (`composition.py:980-987`); without one an endpoint answers 503 (`stripe_notices.py:80-81`).

### Replays: a five-minute tolerance, never zero; each retry is signed afresh

[DOCS] https://docs.stripe.com/webhooks, *Preventing replay attacks* (read 2026-10-19): "Our
libraries have a default tolerance of 5 minutes between the timestamp and the current time …
Use Network Time Protocol (NTP) to make sure that your server's clock is accurate". "**Don't use a
tolerance value of `0`. Using a tolerance value of `0` disables the recency check entirely.**" "If
Stripe retries an event … then we generate a new signature and timestamp for the new delivery
attempt." Duplicates: "guard against duplicated event receipts by logging the event IDs you've
processed".

**In Raketa:** `TOLERANCE_SECONDS = 300` passed explicitly (`stripe_notices.py:50-52`, `:86-88`); a
notice id already in the inbox is acknowledged and does nothing (ADR-0190 §3).

### Allowlist Stripe's webhook IPs too, and use HTTPS with TLS 1.2 or 1.3

[DOCS] https://docs.stripe.com/security/guide (read 2026-10-19): "If you're using webhooks, use TLS
for the endpoint to avoid traffic being intercepted and having notifications altered … **You must
also verify webhook signatures and allowlist Stripe's IP addresses** to ensure that every Stripe
webhook you receive is sent exclusively by Stripe." https://docs.stripe.com/webhooks: "Use both of
these protections: **IP allowlisting** … Configure your server or firewall to only accept webhook
requests from these addresses. **Signature verification**"; "If you use an HTTPS URL for your
webhook endpoint (required in live mode) … Stripe webhooks support only TLS versions v1.2 and
v1.3." https://docs.stripe.com/ips: the webhook list is published at
`https://stripe.com/files/ips/ips_webhooks.json` (and `.txt`); "We provide seven days' notice
through that mailing list before making changes." `stripe listen` forwards from the laptop itself,
so an allowlist applies to deployed endpoints only.

### Events carry no sensitive data; re-read the object, as the connected account

[DOCS] https://docs.stripe.com/security/guide (read 2026-10-19): "(sensitive information is never
included in a webhook event)". https://docs.stripe.com/webhooks *(translated)*: in a snapshot handler
"you can also retrieve the API resource from Stripe to access the most recent, up-to-date object
definition"; https://docs.stripe.com/connect/webhooks: "Each event for a connected account contains
a top-level `account` property that identifies the connected account. Because the connected account
owns the object that triggered the event, you must make API requests for that object as the
connected account."

**In Raketa:** a notice is a prompt and never a reading — the object it names is read from Stripe
as it stands (ADR-0190 §3), on the account the signed event names (`stripe_notices.py:114-133`).

### Roll a signing secret with up to 24 hours of overlap

[DOCS] https://docs.stripe.com/webhooks, *Roll endpoint signing secrets periodically* (read
2026-10-19): "we recommend that you roll (change) secrets periodically, or when you suspect a
compromised secret." "You can choose to immediately expire the current secret or delay its
expiration for up to 24 hours … During this time, multiple secrets are active for the endpoint.
Stripe generates one signature per secret until expiration."

### A v2 account's events split across the two scopes

[DOCS] https://docs.stripe.com/connect/webhooks (read 2026-10-19): "v2 `Account` objects trigger both
v1 and v2 `Events`, which can have different scopes. For events triggered by connected accounts,
v2 `Events` use the **Your account** scope, while v1 `Events` use the **Connected accounts** scope,
even when triggered by the same v2 `Account`." Direct charges' events are in the **Connected
accounts** scope.

**In Raketa:** the Connect endpoint reads v1 `account.updated` and the `payment_intent.*` and
`charge.updated` kinds; an `account.updated` without a top-level `account` is read as nothing
(`stripe_notices.py:59-69`, `:114-134`).

---

## 7. Connect: who can act on a club's payments

### The platform acts for a club with its own key and the club's account id — Stripe does not limit which

[DOCS] https://docs.stripe.com/connect/authentication (read 2026-10-19): "To make server-side API
calls for connected accounts, use the `Stripe-Account` header with the Account ID … using your
platform's API secret key and the connected account's Account ID." Stripe's documentation search
answered (knowledge entry, 2026-10-19): restricting a key to specific connected accounts "is not
directly possible within Stripe. Implement validation checks in your own code".

**In Raketa:** the account id on every charge call comes from the platform's own record of the
charge (`seat_charges.py:851-853`), and no route takes an amount, a fee or an account id from a
player (state `area_sources.SECURITY`).

### A full-Dashboard club can see, refund and dispute its payments itself

[DOCS] https://docs.stripe.com/connect/stripe-dashboard (read 2026-10-19): "Connected accounts can use
the Dashboard to: … View payments, balances, customers, billing, and other products … Handle
disputes, refunds, and chargebacks". https://docs.stripe.com/connect/saas/tasks/dashboard: "Set
`dashboard` to `full` to give connected accounts unrestricted access to the Stripe Dashboard using
their own login credentials" — best when they "need to manage their own API keys, webhooks, or
developer integrations". https://docs.stripe.com/refunds: a refund can be issued "by using the
Refunds API or the Dashboard"; "Stripe debits the connected account directly for refunds to direct
charge payments."

[MEASURED] The test club is `dashboard: full` —
[`stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`](stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses).

### A club can disconnect from the platform

[DOCS] https://docs.stripe.com/connect/webhooks (read 2026-10-19): "`account.application.deauthorized`
… Occurs when a connected account disconnects from your platform. You can use it to trigger cleanup
on your server. Available for connected accounts with access to the Stripe Dashboard".
https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts: the platform's
*Remove account* "disconnects the account from your platform and revokes access in the same way as
the OAuth de-authorize endpoint."

### Onboarding links: single use, minutes, only to the signed-in account holder, over HTTPS

[DOCS] https://docs.stripe.com/connect/marketplace/tasks/onboard (Accounts v2, read 2026-10-19):
"Each Account Link URL can only be used once, because it grants access to the account holder's
personal information." "**Don't email, text, or otherwise send account link URLs outside of your
platform application. Instead, provide them to the authenticated account holder within your
application.**" The refresh URL is used when "The link expired (a few minutes elapsed after the
link was created)", was already visited, "was shared in a third-party application such as a
messaging client that attempts to access the URL to preview it", or the platform lost access. "**You must use
HTTPS for your `return_url` and `refresh_url`, both in production and in testing environments (for
example, to test with localhost). The Account Link creation process fails if you use HTTP.**" (The
older v1 pages, such as https://docs.stripe.com/connect/custom/hosted-onboarding, still allow HTTP
"while you're in testing".) v1 pages add: "Authenticate the user in your application before
redirecting them to this URL." https://docs.stripe.com/api/v2/core/account-links/create: "a
single-use URL"; its example response expires 10 minutes after it was created.

**In Raketa:** a link is made only by `POST /club/payments/onboarding-link` behind the club's cookie
session (`backend/app/modules/payments/presentation/club_routes.py:45-84`); the desk's *Stripe needs
something from you* email carries the website's own continue page, not a Stripe link
(`backend/app/modules/clubs/application/payments_account.py:153`,
`backend/app/modules/clubs/domain/payments_account.py:58-59`); deployed environments refuse a
club website address that is not `https://` (`config.py:857`), a laptop defaults to
`http://localhost:3000` (`config.py:178`).

---

## Pitfalls

Seeds for the Breakers. Each names what Stripe says and where the product stands; "suspected"
means read from the code path and not run.

1. **Client secrets in the logs of `local` and `development`.** Stripe: the client secret "should
   not be stored, logged" ([client secret](#a-client-secret-can-complete-the-payment-so-only-its-customer-may-hold-it)),
   and a key seen "in a log file" counts as exposed ([rotate](#rotate-on-any-exposure-old-and-new-keys-overlap-for-up-to-7-days)).
   stripe-python 15.6.1 logs every response through the `stripe` logger at DEBUG —
   `log_debug("API response body", body=rcontent)` (`stripe/_api_requestor.py:881-882` in the
   locked package) — and the backend's root logger runs at DEBUG in `local` and `development`
   (`backend/app/core/config.py:132-138`, `backend/app/core/logging.py:50`). Every
   `setup_intents.create/retrieve` and `payment_intents.create/retrieve` body carries the
   `client_secret`; `development` is a deployed environment shipping JSON logs to an aggregator.
   Suspected.
2. **`livemode` is never read on a notice.** Stripe recommends checking it because a production
   Connect endpoint also receives test events ([livemode](#production-connect-endpoints-also-receive-test-events--check-livemode)).
   `stripe_notices.py:89-133` reads `id`, `type`, `data.object`, `account` only. Each notice is
   re-read with the process's own key, which bounds the harm; whether a test event can name a live
   club's account is undocumented ([ABSENT] above).
3. **No allowlist of Stripe's webhook IPs.** Stripe: "You must also verify webhook signatures and
   allowlist Stripe's IP addresses" ([IPs](#allowlist-stripes-webhook-ips-too-and-use-https-with-tls-12-or-13)).
   Nothing in the repository restricts the two webhook routes ([MEASURED] grep for `ips_webhooks`
   and allowlists, 2026-10-19: none); the load balancer is provisioned by hand outside the
   repository (`backend/docker/api/startup.prod.sh:26-30`) — unverified.
4. **A restricted key's missing permission is read as a bug or an outage.** Stripe answers an
   invalid-request error (its migration steps also show `403 ERR`) ([restricted key](#a-restricted-key-that-lacks-a-permission-fails-as-an-invalid-request)).
   The adapter raises `InvalidRequestError` as a bug and maps `PermissionError` to
   `PaymentsUnavailable`, "try again" (`stripe_payments.py:68-79`, `:641-654`); neither says the
   key lacks a permission.
5. **A club that disconnects the platform.** Stripe sends `account.application.deauthorized` for
   full-Dashboard accounts ([disconnect](#a-club-can-disconnect-from-the-platform)); the product
   drops it as unheeded (`stripe_notices.py:134`). Shares already held on that club can then no
   longer be taken or let go by the platform, and the refusal would surface as a permission error,
   which the adapter calls an outage (`stripe_payments.py:70-79`). Suspected.
6. **A club acts on a share outside Raketa.** With the full Dashboard a club can refund, and handle
   disputes, itself ([full Dashboard](#a-full-dashboard-club-can-see-refund-and-dispute-its-payments-itself)).
   A capture or cancel made there arrives as `payment_intent.*` and is re-read; a refund made there
   arrives as `charge.refunded` / `refund.updated`, which the product drops
   ([`stripe-sandbox.md` D6](stripe-sandbox.md#differences)) — so a player's receipt and the club's
   Money page do not show it.
7. **The publishable key is never checked against the secret key.** Objects never cross modes or
   accounts ([modes](#each-mode-has-its-own-keys-and-objects-never-cross)); the settings check
   only `STRIPE_SECRET_KEY`'s prefix (`config.py:902`, `:915-934`). A `pk_live_` beside an
   `sk_test_`, or keys of two different accounts, start cleanly and fail every phone confirmation.
8. **Key prefixes the refusals don't know.** The live/test refusals match `sk_live_`/`rk_live_` and
   `sk_test_`/`rk_test_` only (`config.py:99-102`). An organization key (`sk_org_…`, a kind Stripe
   lists, [keys](#only-the-publishable-key-may-leave-the-server)) or any other prefix passes both
   refusals, in production and outside it.
9. **Card testing through "pay with another card".** Stripe: card testers retry many payments with
   the publishable key, and a PaymentIntent with automatic confirmation can be confirmed with a
   publishable key ([card testing](#card-testers-prefer-saving-cards-and-use-the-publishable-key),
   [confirmation](#a-publishable-key-with-the-client-secret-can-confirm-the-paymentintent)). A
   refused share's secret lets the phone confirm it with any typed card (`payments.tsx:393-397`);
   the backend sees only the outcome (`seat_charges.py` `ConfirmSeatCharge`) and counts no attempts;
   the five-a-day guard covers setups only (`terms.py:31`). [ABSENT] a Stripe limit on confirmation
   attempts per PaymentIntent was not found.
10. **The card-testing guard is per player, not per address.** Stripe suggests limiting new
    customers and cards per IP address per day ([prevention](#stripes-prevention-list-sign-in-rate-limits-limits-per-account-captcha-radar)).
    Five setups a day is per player (`payment_method.py:173-179`); a Stripe Customer is opened at a
    player's first setup (`stripe_payments.py:192-201`). No per-address limit on sign-up or setup
    was found in the payments module; elsewhere not searched. Suspected.
11. **The address recorded with the terms may be the load balancer's.** Stripe asks platforms to
    "Keep a record of your customer's written agreement to your terms"
    (https://docs.stripe.com/payments/mobile/save-during-payment?platform=react-native, read
    2026-10-19). The acceptance records `request.client.host` (`routes.py:133`); production runs
    gunicorn's Uvicorn worker with no forwarded-headers setting (`startup.prod.sh:39-47`), so behind
    the load balancer the recorded address is likely the balancer's (unverified).
12. **Onboarding on a laptop over HTTP.** Stripe's Accounts v2 onboarding guide says account-link
    creation "fails if you use HTTP", even testing on localhost ([links](#onboarding-links-single-use-minutes-only-to-the-signed-in-account-holder-over-https)).
    A laptop's club website is `http://localhost:3000` (`config.py:178`), and the walk presses
    *Connect with Stripe* there; the sandbox's test club was onboarded by hand, so this path is
    unproven either way.
13. **One laptop secret used twice.** `stripe listen` prints one secret for both forwards, and the
    walk sets it as both endpoint secrets; deployed, each endpoint has its own, and Stripe warns not
    to mix CLI and Dashboard secrets ([verify](#verify-every-signature-over-the-raw-body-with-each-endpoints-own-secret)).
    Nothing checks the two deployed secrets differ (`config.py:902-912`); copying the laptop habit
    would make one endpoint refuse every notice with 400.

## Checks

The questions a grader asks of a product rule at these moments.

1. Can any process hold a live secret key outside production, or a test key in production — for
   every key prefix Stripe issues (`sk_`, `rk_`, `sk_org_`)?
2. Do the publishable and secret keys belong to the same account and mode, checked before the
   process serves anyone?
3. Is the server key a restricted key with only the permissions the adapter's calls need, and is a
   missing permission reported as such rather than as a bug or an outage?
4. In every deployed environment, are both keys and both signing secrets read from the secrets
   vault, and does nothing print them — error pages, debug mode, logs?
5. Can each key and each signing secret be rolled without downtime (keys overlap up to 7 days,
   signing secrets up to 24 hours), and is there an access policy on the live keys?
6. Will the live key still be allowed to pay clubs out after a quiet season (the 180-day rule)?
7. Is a client secret handed only to the payer it belongs to, only while its payment or setup waits
   for them, and never stored or logged — by the product or by the Stripe SDK's own logging?
8. Is the club account a payment is confirmed on taken from the platform's own record, never from
   what a phone or a request sent?
9. Is every notice verified over the raw body with its own endpoint's secret, with a tolerance
   above zero and at most five minutes, and acted on once by event id?
10. Does the Connect endpoint check `livemode` before acting, as Stripe recommends?
11. Do the webhook routes accept requests only from Stripe's webhook IP list, over HTTPS with TLS
    1.2 or 1.3?
12. Is the object a notice names re-read from Stripe on the connected account the signed event
    names, rather than trusted from the payload?
13. Are saving a card and confirming a refused share protected against card testing: sign-in,
    limits per player and per address, a limit on attempts, and the club's Radar?
14. Can a club refund, capture or cancel a share in its own Dashboard, and does Raketa notice each?
15. What happens to shares already held when a club disconnects the platform, and is
    `account.application.deauthorized` handled?
16. Is an onboarding link made on demand, only for the signed-in desk, never emailed, with HTTPS
    return and refresh addresses in every environment?
17. Does card data stay inside Stripe's own field (SAQ A), with only brand, last four, expiry and
    ids stored?
18. Is the platform's Stripe Dashboard behind phishing-resistant multi-factor sign-in and
    least-privilege roles, and the sandbox at *Private* access?
19. Does the record of a player's consent to off-session charges carry the player's real address,
    not a proxy's?
