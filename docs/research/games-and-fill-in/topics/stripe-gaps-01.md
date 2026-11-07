# Stripe gap answers — 01

Answers to sixteen `stripe:` gaps of the payments pass on PRD #530 (areas FILL and PLATFORM), read
**2026-10-20**. Sources are Stripe's own:

- docs.stripe.com, some pages served in Spanish and quoted *(translated)*, the rest read with
  `?locale=en-GB`;
- support.stripe.com, and stripe.com's Polish pricing and pricing policy;
- Stripe's own phone SDK source on GitHub, at the versions the app pins;
- the sandbox, read through the Stripe SDK in the code copy at `9ab0ea5b`. These reads only listed
  and retrieved objects: nothing was created, updated or deleted.

Each `###` heading names the rule IDs it answers. Money is in złoty; times are UTC.

**Kinds:**

- `[DOCS]`: Stripe's document.
- `[PRICE]`: Stripe's published price.
- `[MEASURED]`: read via the SDK in the copy, or read in the SDK's source, with the object ID or file.
- `[ABSENT]`: looked for and not found, with where.

Lines marked *reading* are not sources.

| Rule | Status |
|---|---|
| R-PLATFORM-13 | Answered: the outcome is unknown, and the request may have run. The recommended timeout is `[ABSENT]` |
| R-PLATFORM-33 | Answered for organisation keys. The same `acct_` id across modes is `[ABSENT]`, and moot for Raketa's flow |
| R-PLATFORM-46 | Answered (SDK source): no key on confirm, and only a `429` is retried |
| R-FILL-37 (fresh copy) | Partly: the reference allows it, and a measured near-twin. The exact path is `[ABSENT]` |
| R-FILL-37, R-FILL-61 (window) | Answered by Stripe's table: 7 days, measured on a typed-card twin. The 3-D Secure case is `[ABSENT]` |
| R-FILL-59 (network word) | `[ABSENT]`. The fee part is answered: none on blended pricing |
| R-FILL-59, R-FILL-60 (live window) | Partly: Stripe's own signal points to 4 days 18 hours. The live reading is `[ABSENT]` |
| R-FILL-11 (who initiates) | Answered by Stripe's definitions. A network consequence is `[ABSENT]` |
| R-FILL-11 (inherited check) | Documented. The sandbox proof is still `[ABSENT]` |
| R-FILL-45 | Answered: Stripe calls the limit variable, and the sandbox cancelled on the 11th call |
| R-FILL-50, R-FILL-63 | `[ABSENT]` until 2026-10-26 06:32:43, plus one new measured fact |
| R-FILL-13, R-FILL-63 | Removal is answered. Lost card payments is `[ABSENT]` |
| R-FILL-15, R-FILL-44, R-FILL-49, R-FILL-56 | `[ABSENT]` for Poland. Stripe documents this only for Japan |
| R-FILL-46 | Answered: no endpoint exists, and the list the code needs is derived. The deployed list isn't Stripe's to answer |
| R-FILL-31, R-FILL-34 | Answered by the docs. No blocked charge exists on the sandbox |
| R-FILL-16 | `[ABSENT]`, plus the sandbox measured not enforcing it |

---

### R-PLATFORM-13 · No published client timeout; a create the client gave up on may still have run at Stripe

- **[DOCS]** [Advanced error handling](https://docs.stripe.com/error-low-level?locale=en-GB), read 2026-10-20:
  - "Network errors result from connectivity problems between client and server, such as socket
    errors or timeouts. A connection might close before your client receives a response.
    Restoring connectivity doesn't tell you whether the original request succeeded."
  - "When a connection fails, you might not know whether Stripe received or executed the request.
    Retry with the same idempotency key and parameters within the first 24 hours after the original
    request."
  - "For a `POST` operation using an idempotency key, Stripe caches the result after the API method
    begins execution, including errors."
  - "If a `409` indicates that another request with the same key is still executing, wait and
    retry with that key and the same parameters. A new key can start a second operation."
  - "If the outcome is still unknown after that window, don't retry with either the old key or a
    new one."
- **[ABSENT]** A recommended client or server timeout. The whole of `error-low-level` was read
  2026-10-20: HTTP errors, network errors, automatic retries, server errors, idempotency,
  `Stripe-Should-Retry` and the status codes. None gives a value. Also searched 2026-10-19:
  error-handling, rate-limits and the stripe-python README
  ([`stripe-reliability.md`](stripe-reliability.md#one-call-can-take-about-615-seconds-stripe-recommends-no-timeout)).
  This is a question for Stripe support.
- *Reading:* Stripe never treats a client's timeout as "not done". A PaymentIntent create that the
  adapter abandons at 20 s (`backend/app/core/config.py:408`) may still finish at Stripe. The SDK
  then retries it twice with the same key
  ([`stripe-reliability.md`](stripe-reliability.md#stripe-python-adds-a-random-key-to-every-keyless-post-and-keeps-it-across-its-own-retries)),
  and each retry has one of three outcomes:
  - if the first has finished, the retry replays its result;
  - if the first is still running, it meets a `409`, which the SDK retries;
  - otherwise it runs the operation once.

  After the last retry the outcome is unknown. Stripe then asks for the payment to be reconciled
  before anything new is sent.

### R-PLATFORM-33 · An organisation key names a club with `Stripe-Context`, and its `sk_org` prefix shows no mode

- **[DOCS]** [Organisation API keys](https://docs.stripe.com/keys/organization-api-keys?locale=en-GB), read 2026-10-20:
  - "Organisation API keys are prefixed `sk_org`. Like account-level restricted API keys (RAKs) or
    secret keys, you can limit their permissions, and they support sandboxes and live mode."
  - "Organisation API keys all have the same `sk_org` prefix, regardless of their permission
    levels. (There's no `rk_org` prefix.)"
  - "All API requests made with an organisation API key that target a specific account must
    include the `Stripe-Context` header to identify the affected account."
  - "All API requests made with an organisation API key must include the `Stripe-Version` header."
  - For a connected account, "use a path that identifies both the platform and the connected
    account, following the format `acct_1R3fqDP6919yCiFv/acct_1032D82eZvKYlo2C`."
  - "Organisations don't have publishable API keys because they can't accept payments. You can use
    your organisation API key to create a PaymentIntent for any account in your organisation, but
    you must use existing account-specific publishable keys for client-side operations."
  - "Don't use an organisation API key if you need to access only one account."
- **[ABSENT]** Whether an organisation key accepts `Stripe-Account` in place of `Stripe-Context`. The
  page documents only `Stripe-Context`.
- *Reading against the code:*
  - The adapter names a club only through `stripe_account`, which is the `Stripe-Account` header
    (`backend/app/modules/payments/infrastructure/stripe_payments.py:477-480`, `:512-515`).
    Nothing documents that an organisation key works this way.
  - The SDK's pinned `Stripe-Version` would meet the second requirement.
  - The page writes one prefix for both modes. The start refusals match only `sk_live_`/`rk_live_`
    and `sk_test_`/`rk_test_` (`backend/app/core/config.py:99-102`), so they can't tell an
    organisation key's mode. That is the gap the rule needs closed: a live key must not run
    outside production.
- **[DOCS]** [API keys](https://docs.stripe.com/keys) *(translated)*, read 2026-10-20: "Each mode has
  its own set of API keys, and objects from one mode aren't accessible from the other."
- **[DOCS]** [Sandboxes](https://docs.stripe.com/sandboxes?locale=en-GB), read 2026-10-20: "A sandbox is
  an isolated test environment". Under *Limitations*: "You can't create connections between a
  Connect platform's sandbox and connected account sandboxes."
- **[MEASURED]** The platform is `acct_1US89K5y1DB8chHb`, created 2026-10-19 04:26:14. Its eight
  connected accounts were all created there the same day, between 04:51 and 22:41. The product opens
  a new account at every club's *Connect with Stripe* (`stripe_payments.py:317-346`).
- **[ABSENT]** Whether one Stripe account keeps the same `acct_` id in test and live mode. Looked:
  - keys and sandboxes (2026-10-20);
  - connect/testing, first 100 000 characters (2026-10-20): "no explicit statement";
  - testing-use-cases and connect/webhooks (2026-10-19,
    [`stripe-security.md`](stripe-security.md#production-connect-endpoints-also-receive-test-events--check-livemode)).
- *Reading:* for Raketa the question does not arise. A club onboarded in the sandbox is a sandbox
  object, and a live club is a new account made by live onboarding, so no sandbox id can carry over.

### R-PLATFORM-46 · Neither phone SDK sends an idempotency key on `confirmPayment`, and each retries only a 429

- **[MEASURED]** The pins, in the copy's `node_modules`. `@stripe/stripe-react-native` 0.38.6 pins:
  - stripe-ios `~> 23.28.0` (`stripe-react-native.podspec:5`);
  - stripe-android `20.48.+` (`android/gradle.properties:3`).

  `confirmPayment` calls `STPPaymentHandler.shared().confirmPayment` on iOS (`ios/StripeSdk.swift:791-823`)
  and `paymentLauncher.confirm` on Android (`android/.../PaymentLauncherFragment.kt:153`). The app
  calls it at `frontend_player/src/shared/lib/platform/payments.tsx:388-414`.
- **[MEASURED]** stripe-ios at tag `23.28.0`, read on GitHub 2026-10-20:
  - **The request.** `STPAPIClient+Payments.swift`'s `confirmPaymentIntent` posts to
    `payment_intents/{id}/confirm` with no headers of its own.
  - **The headers.** `STPAPIClient.swift` builds `X-Stripe-User-Agent`, `Stripe-Version`,
    `Stripe-Account` and `Authorization`.
  - **No key.** A code search of the repository for `"Idempotency-Key"` in Swift finds 0 files.
  - **Retries.** `StripeCore/Source/Helpers/URLSession+Retry.swift` retries only when
    `httpResponse.statusCode == 429`, `retryCount = StripeAPI.maxRetries` (`= 3`,
    `StripeAPI.swift:43`). The delay is (1 + n)² seconds plus up to 0,5 s of jitter.
- **[MEASURED]** stripe-android at tag `v20.48.0`, read on GitHub 2026-10-20:
  - **The options.** The launcher's options come from `ApiRequest.Options`' injected constructor,
    which sets only `apiKey` and `stripeAccount` (`stripe-core/.../ApiRequest.kt:118-125`). So
    `idempotencyKey` stays `null`.
  - **The header.** `RequestHeadersFactory` adds `Idempotency-Key` only through
    `apiRequestOptions.idempotencyKey?.let { … }`.
  - **The call.** `PaymentLauncherViewModel` confirms with `options = apiRequestOptionsProvider.get()`.
  - **Retries.** `DefaultStripeNetworkClient` retries `DEFAULT_RETRY_CODES = 429..429`, with
    `DEFAULT_MAX_RETRIES = 3`.
- **[DOCS]** [Advanced error handling](https://docs.stripe.com/error-low-level?locale=en-GB), read 2026-10-20: "Errors
  that occur before execution begins, such as invalid parameters, an invalid API key or rate
  limiting, don't cache a result." A `429` the SDK retries never ran.
- *Reading:* the SDK never retries a confirmation that times out on the phone, and a second press
  sends a new confirm without a key.
  - If the first press held the money, the payment is in `requires_capture`. The second confirm
    then meets `payment_intent_unexpected_state`
    ([cancel and confirm](stripe-holds-and-capture.md#a-capture-works-only-on-requires_capture-and-answers-anything-else-with-an-error)).
  - The PAY breaker measured exactly this case: "confirm again after a timeout" holds, row C-A8
    (`areas/PAY/breaker.md` in the story work dir).
  - One PaymentIntent holds at most once, so a retried confirmation cannot hold twice.

### R-FILL-37 · A fresh copy: the reference lets a waiting payment take another method; the copy itself is untried

- **[DOCS]** [Confirm a PaymentIntent](https://docs.stripe.com/api/payment_intents/confirm?locale=en-GB), read 2026-10-20:
  - "`payment_method` … ID of the payment method … to attach to this PaymentIntent. If the payment
    method is attached to a Customer, it must match the customer that is set on this PaymentIntent."
  - "If payment fails, the PaymentIntent transitions to the `requires_payment_method` status or
    the `canceled` status if the confirmation limit is reached."
- **[DOCS]** [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts),
  carried from 2026-10-19: "You can't reuse the consumed clone, but you can clone the platform
  PaymentMethod again and use the new clone for another charge."
- **[MEASURED]** `pi_3USPIk5y1DMwE3zY03JvGogQ`, 40,00 zł on the test club `acct_1US95f5y1DMwE3zY`:
  1. The charge `ch_3USPIk5y1DMwE3zY0OwGGxFN` failed at 2026-10-19 22:45:07. It was on the copy
     `pm_1USPIk5y1DMwE3zYOrHRv3wV` (•••• 0341, `generic_decline`).
  2. The charge `ch_3USPIk5y1DMwE3zY0iAFXnJM` succeeded at 22:45:08 on a different method,
     `pm_1USPIm5y1DMwE3zYYMjYwnLg` (•••• 4242, typed with the publishable key), and left the
     payment `requires_capture`.

  So the same refused payment accepted a new, unspent card on the club's account that belongs to no
  customer. That is the FILL breaker's S1 (`areas/FILL/breaker.md`).
- **[MEASURED]** The FILL breaker's S2, `pi_3USPJ05y1DMwE3zY0QhCXhff`: the spent copy itself was
  refused ("previously used with a PaymentIntent without Customer attachment",
  `req_8rsitla8xVevKv`).
- **[ABSENT]** A fresh copy of the platform card confirming the original refused payment. Looked:
  - the cloning page, the confirm reference and the React Native save-and-reuse guide;
  - the sandbox: none of the 123 charges on the test club is a second copy of one platform card
    used on the same payment.
- *Reading:* a fresh copy has no customer and lives on the club's account, exactly like the typed
  card in S1, so it is the case the reference allows. Two things stay unproven: the phone confirming
  with a method id the server made (`paymentMethodData.paymentMethodId`), and the bank's check
  running on it.

### R-FILL-37, R-FILL-61 · After the player confirms, Stripe's table gives 7 days for every network; the bank's-check case is still unread

- **[DOCS]** [Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-GB), read 2026-10-20:
  for card-not-present payments the customer-initiated window is "7 days" for Visa, Mastercard,
  American Express and Discover. Only Visa's merchant-initiated window is shorter: "5 days\*", with
  "the exact authorisation window is 4 days and 18 hours".
- **[DOCS]** [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-GB), read 2026-10-20:
  - "CITs normally include all other transaction types, including any transaction where the
    cardholder is available to participate in the payment flow."
  - "the `payment_method_details.card.capture_before` attribute on the charge is the most reliable
    and accurate way to determine your charge's authorisation window."
- **[DOCS]** Carried: "The validity window won't change after the PaymentIntent is confirmed."
  ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#capture_before-on-the-charge-is-the-window-to-trust-and-it-does-not-move-once-confirmed))
- **[MEASURED]** `pi_3USPIk5y1DMwE3zY03JvGogQ`, refused off-session, then confirmed with a typed card.
  Its holding charge reads `capture_before` **2026-10-26 22:45:08**. That is exactly 168 hours after
  that charge was created (22:45:08), not after the payment's creation (22:45:06) or the refused
  attempt (22:45:07). The window runs from the attempt that held.
- **[MEASURED]** No charge on any of the sandbox's eight connected accounts has `three_d_secure` set.
  All were listed 2026-10-20: 123 on the test club, and one each on two of Stripe's sample accounts.
  No payment confirmed with the bank's check exists to read.
- **[ABSENT]** The `capture_before` of a payment confirmed with the bank's check. The four
  bank's-check demands skip because they need a browser
  ([`stripe-sandbox.md`](stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser)).
- *Reading:* a player confirming in the app with his bank's check is participating. By Stripe's
  table that payment gets the customer-initiated window, 7 days, on Visa too, counted from the
  attempt that held. Only the `capture_before` of a real one settles it.

### R-FILL-59 · A full-share check let go at once: Stripe names only 1 USD checks; on blended pricing it costs the club nothing

- **[DOCS]** [Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-GB), read 2026-10-20: "Card networks
  may also restrict 1 USD authorisations you don't intend to capture."
- **[DOCS]** Stripe support, [Check if a card is valid without a charge](https://support.stripe.com/questions/check-if-a-card-is-valid-without-a-charge)
  (undated), read 2026-10-20: saving a card "only verifies that the information is valid". It
  "cannot check credit limits or account balances to guarantee that a card will have sufficient
  funds".
- **[ABSENT]** Whether Visa or Mastercard accept a full-amount authorisation made only to check the
  money and reversed at once. Looked, 2026-10-20: place-a-hold, cits-and-mits, the support article
  above, and the pricing policy. Visa's own account-verification guidance is carried in
  [`gaps-S-01A-hold.md`](gaps-S-01A-hold.md#the-card-networks-limits-apply-to-retried-declines-and-to-checking-a-card-with-an-amount).
  This is a question for Stripe support.
- **[DOCS]** [Stripe Pricing Policy](https://stripe.com/en-pl/legal/pricing-policy), last modified
  12 October 2026, read 2026-10-20:
  - Blended: "Under a blended rate pricing model, you pay an agreed fee for the applicable
    Transaction (or Charge Event), regardless of the underlying differences in Network Costs (e.g.,
    interchange and scheme fees, for payment cards)."
  - IC+: "Under an IC+ pricing model, Stripe attributes underlying Network Costs to you and adds a
    Stripe fee (markup)."
- **[PRICE]** [Stripe pricing, Poland](https://stripe.com/en-pl/pricing), read 2026-10-20:
  - "1.5% + 1.00zł" for standard EEA cards;
  - "1.9% + 1.00zł" for premium EEA cards;
  - "2.5% + 1.00zł" for UK cards;
  - "3.25% + 1.00zł" for international cards.

  The page says nothing about declined, uncaptured or cancelled authorisations.
- **[MEASURED]** The test club's fees are blended:
  - Stripe's fee was 2,30 zł on 40,00 zł and 1,88 zł on 27,00 zł. Both are 3,25 % + 1,00 zł, the
    Polish blended price for an international card
    ([`stripe-sandbox.md`](stripe-sandbox.md#stripes-fee-on-a-share-230-zł-on-40-zł-with-stripes-us-test-card)).
    So the test club is on blended pricing.
  - A let-go share's charge reads `balance_transaction: null` (`ch_3USA7x5y1DMwE3zY0r61YRsL`,
    [`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#why-a-payment-was-cancelled-four-reasons-the-caller-gives-four-stripe-sets)).
    No fee is booked for it.
- **[DOCS]** [Sandboxes](https://docs.stripe.com/sandboxes?locale=en-GB): "You can't test IC+ pricing in a sandbox."
- *Reading:*
  - On blended pricing, Stripe documents no cost to the club for a check that is let go.
  - A club on IC+ would carry whatever network costs Stripe attributes, and no page names one for
    a reversed authorisation in Poland.

### R-FILL-59, R-FILL-60 · A live off-session hold on a copy carries no CVC, and that signal points to Visa's 4 days 18 hours; unmeasured

- **[DOCS]** [Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method?locale=en-GB), read 2026-10-20: "Stripe and
  the card network classify transactions as MIT or CIT based on signals of cardholder
  participation, not solely on API parameters like `off_session`. For example, a payment with
  `off_session: true` might still be classified as a CIT if a CVC is present, resulting in the CIT
  authorisation window instead."
- **[DOCS]** Stripe support, [Non-recurring charges show as "recurring" on customer bank statements](https://support.stripe.com/questions/non-recurring-charges-show-as-recurring-on-customer-bank-statements)
  (undated), read 2026-10-20. *Paraphrased, because the reader limited verbatim quotes:*
  - PCI rules don't let Stripe store a CVC on its servers, so a payment made with saved card
    details carries none.
  - Such payments are marked "recurring" to tell the card's bank why the CVC is missing.
- **[MEASURED]** On the sandbox, every off-session hold on the test club reads `cvc_check: pass`
  and 7 days. For example, `ch_3USA7i5y1DMwE3zY09j5MxD1` reads `capture_before` 2026-10-26 06:32:43
  (read again 2026-10-20). The sandbox's test card answers the CVC check.
- **[ABSENT]** The live window of such a hold. No page states it, and the sandbox can't shorten a
  hold ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#nothing-in-test-mode-shortens-a-hold-or-moves-its-clock)).
- *Reading:*
  - Live, a copy of a saved card carries no CVC, which is exactly the signal Stripe names. So a
    Visa hold made by the fill or by the holding is expected to get 4 days 18 hours.
  - The card check would then run live for every Visa seat whose cut-off lies further away than
    that.
  - The first live hold's `capture_before` settles it, and the code already reads it on every hold
    (`stripe_payments.py:510-511`).

### R-FILL-11 · A share held while its player is in the app, started by his own yes, is customer-initiated by Stripe's definitions

- **[DOCS]** [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits?locale=en-GB), read 2026-10-20:
  - "An MIT is a transaction that you initiate without direct participation of your customer,
    based on a prior agreement with that customer authorising you to store and use their
    credentials."
  - "CITs normally include all other transaction types, including any transaction where the
    cardholder is available to participate in the payment flow."
- **[DOCS]** [Create](https://docs.stripe.com/api/payment_intents/create?locale=en-GB) and
  [confirm](https://docs.stripe.com/api/payment_intents/confirm?locale=en-GB) a PaymentIntent, read
  2026-10-20: `off_session`: "Set to `true` to indicate that the customer isn't in your checkout
  flow during this payment attempt and can't authenticate."
- **[DOCS]** Carried
  ([`stripe-authentication.md`](stripe-authentication.md#merchant-initiated-payments-outside-sca-but-only-after-an-authenticated-save-and-an-agreement)):
  "Payments made with saved cards when the customer isn't present in the checkout flow … might
  qualify as merchant-initiated transactions (MITs) … marking a payment as MIT is similar to
  requesting an exemption; neither a customer challenge nor a liability shift occurs."
- *Code:* every hold is created `off_session: True`, the filler's own included
  (`stripe_payments.py:505-506`).
- **[ABSENT]** Whether a network treats that flag on a present cardholder's payment as misuse, and
  with what consequence. No Stripe page says so: cits-and-mits, SCA exemptions, the create and
  confirm references, place-a-hold. This is a question for Stripe support.
- *Reading:*
  - The filler is "available to participate": he is in the app and has just pressed yes. By
    Stripe's words his own share is customer-initiated, yet it is sent as "can't authenticate".
  - When his bank wants its check, the code already asks him in the app on the same payment, which
    is the on-session path.
  - What is open is only how the first attempt is labelled.

### R-FILL-11 · A copy inherits the setup's bank check by Stripe's word; still unproven on the sandbox

- **[DOCS]** Both carried from 2026-10-19
  ([`stripe-authentication.md`](stripe-authentication.md#the-platforms-setup-carries-to-every-clone-on-a-clubs-account)):
  - [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts):
    "the cloned PaymentMethod inherits the setup performed on your platform account, so you don't
    need to set it up again on the connected account."
  - [SCA for Connect platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms):
    "sharing a payment method with a connected account automatically shares customer permission as
    well".
- **[MEASURED]** No charge on any connected account in the sandbox uses card 3155 (all listed
  2026-10-20). Two refused off-session holds used 3178:
  - `ch_3USPGb5y1DMwE3zY0lldplS1` and `ch_3USPFG5y1DMwE3zY1tsvLRa4`, each `authentication_required`;
  - 3178 asks for the check on every payment, so it cannot show inheritance.
- **[ABSENT]** The proof on the sandbox. The demand that would show it, card 3155, still skips
  ([`stripe-sandbox.md`](stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser)).

### R-FILL-45 · Stripe calls the confirmation limit "variable"; the sandbox cancelled on the 11th call, after 10 refused attempts

- **[DOCS]** [Confirm a PaymentIntent](https://docs.stripe.com/api/payment_intents/confirm?locale=en-GB), read 2026-10-20:
  - "If payment fails, the PaymentIntent transitions to the `requires_payment_method` status or
    the `canceled` status if the confirmation limit is reached."
  - "There is a variable upper limit on how many times a PaymentIntent can be confirmed. After this
    limit is reached, any further calls to this endpoint will transition the PaymentIntent to the
    `canceled` state."
- **[MEASURED]** `pi_3USPKC5y1DMwE3zY00HIKsMU`, 40,00 zł on the test club, the FILL breaker's S5:
  1. It made 10 failed charges: the off-session copy (•••• 0341) at 22:46:37, then nine typed cards
     (•••• 0002) from 22:46:38 to 22:46:48.
  2. Each failure emitted `charge.failed` and `payment_intent.payment_failed`.
  3. The 11th confirmation, request `req_ZW2hNCf2S7SLgf` (a phone-side key), made no charge. The
     breaker recorded its answer as `payment_intent_unexpected_state` (`areas/FILL/breaker.md` S5).
  4. Stripe moved the payment to `canceled` at 22:46:49 with **`cancellation_reason: null`**. The
     event `evt_3USPKC5y1DMwE3zY0xQEMKTV` (`payment_intent.canceled`) names that confirmation's
     request.
- *Reading:*
  - The number is Stripe's to vary, so no product limit should be pinned to it. On this sandbox, 10
    refused attempts were allowed.
  - Stripe's own cancel here carried no reason, so a null reason does not mean Raketa let the
    payment go. See the next section.

### R-FILL-50, R-FILL-63 · A lapsed hold's reason and events: unreadable until 26 October

- **[MEASURED]** Read 2026-10-20:
  - `pi_3USA7i5y1DMwE3zY0Nemxwtn` is still `requires_capture`: 40,00 zł, its charge's
    `capture_before` 2026-10-26 06:32:43.
  - There is no `charge.expired` event on any of the eight connected accounts.
  - All 48 `payment_intent.canceled` events on the test club carry a request.
  - The platform was created 2026-10-19 04:26:14, so no hold anywhere in this sandbox can lapse
    before 2026-10-26.
- **[DOCS]** Carried
  ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#why-a-payment-was-cancelled-four-reasons-the-caller-gives-four-stripe-sets)):
  the reasons Stripe sets itself include `automatic` and `expired`.
- **[MEASURED]** A cancel Stripe made by itself, for too many confirmations, carried
  `cancellation_reason: null` (`pi_3USPKC5y1DMwE3zY00HIKsMU`, above).
- **[ABSENT]** Which reason, and which events, a lapsed card hold carries at this account's version.
  Looked: place-a-hold, lifecycle, cancel, capture and event types (2026-10-19). Answer it after
  2026-10-26 06:32:43 by reading, through the test club:
  - `pi_3USA7i5y1DMwE3zY0Nemxwtn`'s `status`, `cancellation_reason` and `canceled_at`;
  - the account's `charge.expired` and `payment_intent.canceled` events.
- *Reading:*
  - Raketa's own let-go carries its key in the event's `request`. A lapse, which Stripe makes on its
    own clock, should carry none.
  - The request is therefore the dependable way to tell a lapse from Raketa's own let-go. The reason
    is not: Stripe's measured self-cancel above also read null.

### R-FILL-13, R-FILL-63 · After a club is removed Raketa can't capture or cancel; after it loses card payments, nothing is documented

- **[DOCS]** Carried from 2026-10-19
  ([`stripe-connect.md`](stripe-connect.md#removing-a-club-ends-every-api-call-raketa-can-make-for-it)):
  "A removed account … you can't process payments or make API calls for it."
- **[DOCS]** [Error codes](https://docs.stripe.com/error-codes) *(translated)*, read 2026-10-20:
  `platform_api_key_expired` "occurs if your platform has generated a new key or if the connected
  account has been disconnected from the platform."
- **[DOCS]** Two more points, carried:
  - A full-Dashboard club can capture or cancel a held share itself
    ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#a-club-on-the-full-dashboard-can-capture-or-cancel-a-held-share-itself)).
  - Stripe cancels a lapsed hold and releases the money
    ([`…#stripe-cancels-a-lapsed-hold-releases-the-money-and-says-so`](stripe-holds-and-capture.md#stripe-cancels-a-lapsed-hold-releases-the-money-and-says-so)).
- **[DOCS]** [Pause payments and payouts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts?locale=en-GB),
  read 2026-10-20:
  - "Pausing payments blocks creation of any charges. It also makes the transfer, card_payments and
    other payment methods capabilities `inactive`."
  - It applies only to accounts "where they're liable for negative balances", and "This workflow
    isn't available when using Accounts v2".
  - "we don't enforce payment or payout pauses in a sandbox … doesn't block the creation of charges."
- **[ABSENT]** Whether a `requires_capture` payment can still be captured or cancelled once
  `card_payments` turns inactive or `charges_enabled` turns false. Looked:
  - 2026-10-20: pausing-payments, error-codes, and a docs and support search ("capture uncaptured
    payment after connected account disconnected OR rejected OR charges disabled"), which found only
    the unreject changelog and the pausing page;
  - carried: handling-api-verification, account-capabilities, managed-risk, connect/charges.

  This is a question for Stripe support.
- *Reading:* on a removed club, the held share lapses at its `capture_before` unless the club takes
  or lets it go in its own Dashboard. Raketa's cut-off capture fails with `platform_api_key_expired`,
  and the player reads paid while nothing is taken.

### R-FILL-15, R-FILL-44, R-FILL-49, R-FILL-56 · A fee for letting a hold lapse is documented only in Japan, where Stripe's advice is to cancel

- **[DOCS]** Stripe support, [Visa Processing Integrity Program Fee (PIPF) in Japan](https://support.stripe.com/questions/visa-processing-integrity-program-fee-(pipf)-in-japan)
  (undated; the fee starts October 2026), read 2026-10-20:
  - Visa "will charge fees for authorizations that aren't captured or cancelled within compliance
    windows".
  - It concerns Japan-based accounts, on JPY payments with internationally issued cards.
  - On blended pricing Stripe absorbs the fee, though it may pass it through in a future pricing
    update. On IC+ it is passed to the business per authorisation.
  - Stripe's advice: "Cancel the `PaymentIntent` when a customer abandons an order or booking,
    rather than letting the authorization expire."
- **[DOCS]** The Stripe Pricing Policy's blended and IC+ lines, quoted under R-FILL-59 above.
- **[ABSENT]** Any fee on a Polish account for an authorisation left to lapse. Looked, 2026-10-20:
  - place-a-hold, the cancel reference and refunds;
  - Stripe's Polish pricing page and pricing policy;
  - a docs and support search for "misuse of authorization", "processing integrity" and
    "authorization fee";
  - the earlier search named in the gap.
- *Reading:*
  - Nothing documented falls on a blended-price Polish club, and the test club is on blended
    pricing (R-FILL-59 above).
  - Where Stripe does document such a fee, its advice is to cancel rather than let the hold lapse.
    These four rules let holds lapse.

### R-FILL-46 · No endpoint exists yet; the code needs seven kinds on Connected accounts and two on the platform

- **[MEASURED]** Read 2026-10-20 on the platform `acct_1US89K5y1DB8chHb`:
  - `GET /v1/webhook_endpoints` returns 0;
  - `GET /v2/core/event_destinations` returns `{"data":[]}`.

  The same as on 2026-10-19 ([`stripe-sandbox.md`](stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination)).
- *Code, searched in the copy at `9ab0ea5b`:* nothing lists the event types.
  - No `enabled_events` exists under `docs`, `backend/app`, `backend/deploy` or `.github`.
  - The deployment artefact names only the two secrets (`backend/deploy/ecs/taskdef.json:53-54`).
  - The environments page names `STRIPE_WEBHOOK_SECRET` but never `STRIPE_CONNECT_WEBHOOK_SECRET`:
    neither in its refusals table nor in the turning-on checklist (`docs/environments.md:85`, `:418`). The settings still refuse to start without both
    (`backend/app/core/config.py:898-905`).
- *Code:* what the reader acts on.
  - **Connected accounts:**
    - `payment_intent.amount_capturable_updated`, `.succeeded`, `.canceled`, `.payment_failed`
      and `.requires_action`;
    - `charge.updated` and `account.updated`.

    (`backend/app/modules/payments/infrastructure/stripe_notices.py:57-69`, `:114-133`)
  - **Platform:** `setup_intent.succeeded` and `payment_method.automatically_updated`
    ([`stripe-webhooks.md`](stripe-webhooks.md#saving-a-card-platform)).
  - Everything else is `Unheeded`, including `charge.expired`.
- **[DOCS]** Carried ([`stripe-webhooks.md`](stripe-webhooks.md#only-subscribe-to-what-the-integration-needs)):
  "Configure your webhook endpoints to receive only the types of events required by your
  integration."
- **[ABSENT]** The list a deployed endpoint will carry. This is a deployment choice nobody has
  written down, not a question for Stripe. The minimum is the nine kinds above, on their two scopes.

### R-FILL-31, R-FILL-34 · A club's Radar block reads like a bank decline in the error; only the charge's outcome tells them apart

- **[DOCS]** [Declines](https://docs.stripe.com/declines) *(translated)*, read 2026-10-20:
  - "When Stripe blocks a payment, it doesn't obtain authorisation from the card issuer."
  - Its example of a blocked outcome: `"network_status": "not_sent_to_network"`,
    `"reason": "highest_risk_level"`, `"advice_code": "do_not_try_again"`, `"type": "blocked"`.
  - Its example of a bank decline: `"network_status": "declined_by_network"`,
    `"type": "issuer_declined"`.
- **[DOCS]** [Decline codes](https://docs.stripe.com/declines/codes?locale=en-GB), read 2026-10-20:
  - `generic_decline`: "The card was declined for an unknown reason or Stripe Radar or Adaptive
    Acceptance blocked the payment."
  - `fraudulent`: "declined because Stripe suspects that it's fraudulent".
  - `merchant_blacklist`: "matches a value on the Stripe user's block list".
- **[DOCS]** [Testing](https://docs.stripe.com/testing?locale=en-GB), read 2026-10-20: "Blocked payments
  result in card errors with an error code of fraud." Stripe's pages name different codes for a
  block, and none is unique to it.
- **[DOCS]** [The Charge object, `outcome`](https://docs.stripe.com/api/charges/object?locale=en-GB&query=outcome), read 2026-10-20:
  - `type`: "`authorized`, `manual_review`, `issuer_declined`, `blocked`, and `invalid`".
  - `network_status`: "`approved_by_network`, `declined_by_network`, `not_sent_to_network`, and
    `reversed_after_approval`".
  - `reason`: "Charges authorized, blocked, or placed in review by custom rules have the value
    `rule`".
  - `rule`: "The ID of the Radar rule that matched the payment, if applicable."
- **[DOCS]** [Fraud prevention rules](https://docs.stripe.com/radar/rules?locale=en-GB), read 2026-10-20:
  rules can test `:is_off_session:`, so a club can write a rule aimed at off-session payments.
  Carried: on a direct charge, only the club's own rules run
  ([`stripe-security.md`](stripe-security.md#on-a-direct-charge-only-the-clubs-radar-runs)).
- **[MEASURED]** The sandbox has no blocked charge. All 123 test-club charges, listed 2026-10-20,
  read `authorized` or `issuer_declined`/`declined_by_network`. For example,
  `ch_3USEMG5y1DMwE3zY0vKtkfxM` reads `generic_decline`, "The bank did not return any further details
  with this decline."
- *Code:* the hold reads only the error's `code` and `decline_code`
  (`stripe_payments.py:519-539`), never `latest_charge.outcome`. A club's block is therefore recorded
  as a decline, and the player is asked for another card, just as for the bank's generic decline.
- *Reading:*
  - What tells them apart is the charge's `outcome`: `type: blocked`, `network_status:
    not_sent_to_network`, `reason: rule` and `rule: <id>`. A bank decline reads `issuer_declined`
    and `declined_by_network`.
  - A club's own rule can't be produced on the shared test club without that club's Dashboard.
  - Card 4100 0000 0000 0019 makes Radar block a payment for highest risk, not for a rule match.

### R-FILL-16 · A restricted club: Stripe documents no answer for the copy or the hold, and the sandbox doesn't enforce it

- **[DOCS]** [Error codes](https://docs.stripe.com/error-codes) *(translated)*, read 2026-10-20:
  - `capability_not_active`: "Your account lacks the active capabilities required to access this
    endpoint. See the capabilities matrix in the error response for more information".
  - `account_invalid`, for an invalid `Stripe-Account` value.
  - `platform_api_key_expired`, for a disconnected account.

  None names creating a payment method or a payment on an account without card payments.
- **[DOCS]** Carried: "Sandboxes might not enforce some capabilities."
  ([`stripe-connect.md`](stripe-connect.md#the-sandbox-may-allow-what-a-capability-doesnt)).
  Pausing a club's payments doesn't block charges in a sandbox either (the pausing page, above).
- **[MEASURED]** Seven of the sandbox's eight connected accounts read `charges_enabled: false`,
  `card_payments: inactive`, `disabled_reason: requirements.past_due`. Examples are
  `acct_1USELi5y1DCSZFum` and `acct_1USPFh5y1DXbCdOQ`. None holds a copy or a hold made by Raketa.
- **[MEASURED]** On `acct_1US8XX5y1Dlh7WsG`, one of Stripe's sample accounts, a payment went through
  without card payments:
  - At 04:51:23 the events show `capability.updated` (`card_payments` `inactive`) and
    `account.updated` (`charges_enabled: false`).
  - One second later, `pi_3US8Xf5y1Dlh7WsG0YJHcQz5` (100,00 zł) succeeded. Its charge's description
    reads "Test payment automatically created to show how payments appear on your platform".

  The sandbox let a payment through on an account without card payments, so no sandbox test can
  show what live Stripe answers.
- Third-party help pages, not Stripe's own, quote "This Connect account cannot currently make live
  charges" for an unverified account. Read 2026-10-20:
  [Chargebee](https://support.chargebee.com/support/solutions/articles/260023-stripe-error-this-connect-account-cannot-currently-make-live-charges-),
  [Novo](https://www.novo.co/help/why-am-i-getting-this-stripe-error-this-connect-account-cannot-currently-make-live-charges).
- **[ABSENT]** The error Stripe returns, in live mode, for a payment-method copy and for a
  PaymentIntent on an account whose `card_payments` is inactive. Looked: error codes, declines,
  pausing, the account-capabilities pages (carried), and a web search (2026-10-20). This is a
  question for Stripe support.
