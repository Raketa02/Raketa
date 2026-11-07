# Stripe — gaps answered (03)

Answers to sixteen Stripe gaps the PAY and CLUBMONEY lenses left open in the payments pass at `9ab0ea5b`.
Everything was read on **2026-10-20**.

- **Stripe's docs** were fetched from docs.stripe.com, support.stripe.com and stripe.com. Pages served in Spanish
  are quoted *(translated)*. Where only the fetch tool's summary was available, the line says so.
- **The sandbox** was read only through stripe-python 15.6.1 in the copy, with the sandbox's test key. Only list
  and retrieve calls were made; nothing was created, updated or deleted. The platform is `acct_1US89K5y1DB8chHb`
  and the test club is `acct_1US95f5y1DMwE3zY`.
- **A gap another file already answers** is answered by citing that file, and only the new facts are added here.

---

### R-PAY-35 — whether Polish issuers send "authentication required" under a plain decline

**What Stripe says.**

- **[DOCS]** [Error codes](https://docs.stripe.com/error-codes) — 2026-10-20 *(translated)*. On the error
  `authentication_required`: "The payment requires authentication to proceed. If your customer is off session,
  notify them to return to your application and complete the payment." On `card_declined`: "When a card is
  declined, the error returned also includes the `decline_code` attribute with the reason the card was declined."
- **[DOCS]** [Card declines](https://docs.stripe.com/declines/card) — 2026-10-20.
  - **Off-session payments:** "payment attempts might also require authentication and fail with an
    `authentication_required` **decline code**."
  - **How to read a decline:** "Retrieve the `decline_code` property of `last_payment_error` from the
    PaymentIntent object to see why the card issuer declined the payment attempt."
- **[DOCS]** [Network decline codes](https://docs.stripe.com/declines/network-codes) — 2026-10-20 *(translated)*.
  - **Visa `1A`:** "Additional customer authentication required."
  - **Mastercard `65`:** "Exceeds withdrawal limit (or soft decline for EMV 3DS authentication identity check)."
  - **What the page leaves out:** it lists the raw codes but not the Stripe decline code each one becomes. So it
    doesn't say how Mastercard's ambiguous `65` reaches an integration.
- Carried: the decline code's meaning, and issuers that send it even after a passed check —
  [`stripe-authentication.md#authentication_required-is-also-an-issuers-decline-code`](stripe-authentication.md#authentication_required-is-also-an-issuers-decline-code).

**What the sandbox holds.**

- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: every `payment_intent.payment_failed` event on the test
  club (33 events), tallied by `last_payment_error`:

  | Card | Count | `code` | `decline_code` |
  |---|---|---|---|
  | 4000 0027 6000 3184 | 6 | `authentication_required` | `authentication_required` |
  | 4000 0082 6000 3178 | 2 | `authentication_required` | `authentication_required` |
  | 4000 0000 0000 0341 | 13 | `card_declined` | `generic_decline` |
  | 4000 0000 0000 0002 | 10 | `card_declined` | `generic_decline` |
  | 4000 0000 0000 9995 | 1 | `card_declined` | `insufficient_funds` |
  | 4000 0000 0000 0069 | 1 | `expired_card` | `expired_card` |

  No refusal on the sandbox has ever been `card_declined` with decline code `authentication_required`. A sibling file
  measured the same table independently, with event IDs:
  [`stripe-gaps-05.md#r-rescue-25--stripes-test-cards-send-the-banks-s…`](stripe-gaps-05.md#r-rescue-25--stripes-test-cards-send-the-banks-soft-decline-with-authentication_required-in-both-fields-no-card-sends-it-under-card_declined).

**What the code does.** It treats a refusal as the bank's check only when the error's `code` is
`authentication_required` (`backend/app/modules/payments/infrastructure/stripe_payments.py:523`). A `card_declined`
whose decline code is `authentication_required` would be recorded as a decline with that code (`:535-540`), and the
phone would ask the player to type another card.

**[ABSENT] Not found anywhere.**

- **The questions:**
  - whether PKO BP, Pekao, mBank, ING or Santander send the soft decline in a way that reaches Raketa as
    `card_declined` with decline code `authentication_required`;
  - which decline code Stripe gives a Mastercard `65`.
- **Where we looked:**
  - Stripe's pages: decline codes, card declines, network decline codes, error codes;
  - Stripe's support article on authenticated payments declined with this code (carried);
  - every refusal event on the sandbox.
- **On the sandbox:** no test card produces this shape
  ([`stripe-testing.md#the-decline-cards-by-reason`](stripe-testing.md#the-decline-cards-by-reason)).
- **Question for Stripe support:** "For an EEA merchant-initiated payment the issuer refuses for SCA (Visa `1A`,
  Mastercard `65`), is the error's `code` always `authentication_required`, or can it be `card_declined` with
  `decline_code: authentication_required`?"
- *Reading:* Stripe's own guidance reads `decline_code`. A check that takes the bank's check when either `code` or
  `decline_code` is `authentication_required` would meet both shapes.

### R-PAY-19 — Radar on saved cards: whether it's on, and what screening a save costs

**What Stripe says.**

- **[DOCS]** [Risk factors recommendations](https://docs.stripe.com/radar/integration) — 2026-10-20: "By default,
  Radar doesn't scan if you set up a Payment Method for future use *without* a charge. If you want to scan
  SetupIntents, go to your Radar settings and enable **Use Radar on payment methods saved for future use**."
- **[DOCS]** [Radar for Setup Intents](https://support.stripe.com/questions/radar-for-setup-intents) — 2026-10-20,
  from the fetch tool's summary:
  - **Plans:** Radar Standard, Radar Plus and Radar Pro can all be turned on for SetupIntents.
  - **Billing:** Stripe charges "per SetupIntent confirmation attempt".
  - **Rules:** Request 3DS, Allow and Block rules are evaluated against setups. Review rules are "not supported".
  - **Default rules:** "Block if CVC verification fails" and "Block if postal code verification fails" apply to
    setups only when the setting is on.
  - **Connect:** the page says nothing about Connect.
- **[PRICE]** [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — 2026-10-20, from the fetch tool's summary.
  Radar costs either "Starting at 0.23zł per screened transaction" (pay per use) or a monthly plan "Starting at
  46.00zł". The [Radar pricing page for Poland](https://stripe.com/en-pl/radar/pricing) lists platform plans from
  80 zł a month and gives no separate rate for setups.
- **Who pays:** the setup runs on the platform account, so the screening is billed to Raketa. Stripe says "Any activity
  occurring at the platform account level is billed to your platform"
  ([`stripe-saving-cards.md#card-updates-on-the-platform-are-billed-to-the-platform`](stripe-saving-cards.md#card-updates-on-the-platform-are-billed-to-the-platform)).
- *Reading:* the bill is per attempt. On pay per use, Paula saving her card at the first try costs Raketa about
  0,23 zł, and a refused try followed by a second costs about 0,46 zł.

**[ABSENT] Whether the setting is on for the sandbox platform.**

- **Not readable:** the switch lives in the Dashboard's Radar settings. No field of the setups read carries a Radar
  outcome.
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: the platform holds 145 setups.
  - **Succeeded:** 94 with 4242, 13 with 0341, 4 each with 0259, 5126 and 7726, 2 with 0005, 1 with 0077.
  - **Waiting for the bank's check:** 9 with 3184 and 4 with 3155, all `requires_action`.
  - **The rest:** 6 `requires_payment_method` and 4 `canceled`.
  - **Radar:** none has a `last_setup_error`, and none was confirmed with Radar's block card. So the sandbox can't show
    whether Radar screens setups.
- **What would answer it:** either of these.
  - An Administrator opens Dashboard → Settings → Radar on the sandbox.
  - A walker saves 4100 0000 0000 0019 ("Radar always blocks it",
    [`stripe-testing.md#radars-test-cards`](stripe-testing.md#radars-test-cards)) on the phone. A refused save means
    the setting is on; a saved card means it is off.

### R-PAY-29 / R-PAY-26 — the event kinds each deployed endpoint must enable

**What Stripe says.**

- **[DOCS]** [Create a webhook endpoint](https://docs.stripe.com/api/webhook_endpoints/create) — 2026-10-20.
  - **Two kinds of endpoint:** "A webhook endpoint must have a `url` and a list of `enabled_events`. You may optionally
    specify the Boolean `connect` parameter. If set to true, then a Connect webhook endpoint that notifies the
    specified `url` about events from all connected accounts is created; otherwise an account webhook endpoint that
    notifies the specified `url` only about events from your account is created."
  - **`api_version`:** "Events sent to this endpoint will be generated with this Stripe Version instead of your
    account's default Stripe Version."
- Carried:
  - subscribe only to what the integration needs:
    [`stripe-webhooks.md#only-subscribe-to-what-the-integration-needs`](stripe-webhooks.md#only-subscribe-to-what-the-integration-needs);
  - every Connect platform must have a Connected-accounts endpoint:
    [`stripe-connect.md#every-connect-platform-needs-a-connected-account…`](stripe-connect.md#every-connect-platform-needs-a-connected-accounts-endpoint-a-sandbox-needs-its-own);
  - a v2 club's own events go to the platform's scope:
    [`stripe-connect.md#a-v2-club-account-sends-v1-events-to-connected-a…`](stripe-connect.md#a-v2-club-account-sends-v1-events-to-connected-accounts-and-v2-events-to-your-account).
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: `GET /v1/webhook_endpoints` → `[]` and
  `GET /v2/core/event_destinations` → `[]`. There is still no endpoint in either scope
  ([`stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination`](stripe-sandbox.md#no-webhook-endpoint-and-no-event-destination)).

**The list the code needs.** These nine kinds are what the readers act on (`stripe_notices.py:57-69`, `:102-133`).
The same count is in
[`stripe-gaps-01.md#r-fill-46--no-endpoint-exists-yet-the-code-needs-seven-kinds-on-connected-accounts-and-two-on-the-platform`](stripe-gaps-01.md#r-fill-46--no-endpoint-exists-yet-the-code-needs-seven-kinds-on-connected-accounts-and-two-on-the-platform).

| Endpoint | `connect` | Kind | What it does for the product |
|---|---|---|---|
| `POST /api/v1/webhooks/stripe` | `false` | `setup_intent.succeeded` | Saves the card when the phone never reports back (R-PAY-29) |
| same | `false` | `payment_method.automatically_updated` | Records a card the network updated, including a new brand (R-PAY-26) |
| `POST /api/v1/webhooks/stripe-connect` | `true` | `payment_intent.amount_capturable_updated`, `.succeeded`, `.canceled`, `.payment_failed`, `.requires_action` | A share held, taken, let go or lapsed, refused, or waiting for the bank |
| same | `true` | `charge.updated` | "The fee is ready" — a kind Stripe documents only for asynchronous capture (see R-PAY-41 below) |
| same | `true` | `account.updated` | A club's readiness |

**What Stripe recommends for these moments that the code drops today.** Enabling these now would only get them
acknowledged and ignored.

- **Refunds:**
  - `refund.created` is Stripe's stated minimum;
  - `refund.failed`.
  - Source: [`stripe-webhooks.md#refunds`](stripe-webhooks.md#refunds).
- **Disputes:** `charge.dispute.created`
  ([`stripe-webhooks.md#disputes-on-a-direct-charge`](stripe-webhooks.md#disputes-on-a-direct-charge)).
- **Payouts and the club's account:**
  - `payout.failed`;
  - `account.external_account.updated`;
  - `account.application.deauthorized`;
  - `capability.updated`.
  - Source: [`stripe-webhooks.md#a-clubs-account-its-disconnection-and-its-payouts`](stripe-webhooks.md#a-clubs-account-its-disconnection-and-its-payouts).
- **A lapsed hold:** `charge.expired` (see R-PAY-54 below).
- **A failed save:** `setup_intent.setup_failed`, which the spec lists
  (`docs/specs/games-and-fill-in/the-mechanics.md:1901`).
- **Accounts v2:** Stripe recommends a v2 event destination in the *Your account* scope for
  `v2.core.account[requirements].updated` and `v2.core.account[configuration.merchant].capability_status_updated`.
  The code reads neither.

*Reading:* each endpoint is pinned to no API version, so it would render at the account's default, endive
([`stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive`](stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive)).

### R-PAY-54 — the events and the reason a lapsed card hold carries at this account's API version

**Answered from Stripe's changelog.** This replaces the *undocumented* line in
[`stripe-holds-and-capture.md#which-reason-and-which-events-an-expired-hold-ca…`](stripe-holds-and-capture.md#which-reason-and-which-events-an-expired-hold-carries-undocumented-readable-on-the-sandbox-after-26-october).

- **[DOCS]** [Partially capturing or cancelling payments no longer creates a Refund](https://docs.stripe.com/changelog/basil/2025-03-31/remove-refund-from-partial-capture-and-payment-cancellation-flow?locale=en-GB),
  API version `2025-03-31.basil` — 2026-10-20.
  - **No Refund object:** "Payment cancellation (both manual and automated)" no longer creates one.
  - **The reason:** "A new `cancellation_reason` value called `expired` will be introduced. This new value represents
    payments cancelled because of authorisation expiry. It replaces the formerly used value of `automatic`."
  - **The charge:** "`amount_captured` will be 0"; "`amount_refunded` will no longer be updated by these actions";
    "`refunded` will no longer be `true` for payment cancellation flows".
  - **The events:** "We'll no longer send `charge.refunded` and `charge.refund.updated` events. We'll still send
    `charge.expired`, `charge.captured`, and `payment_intent.canceled` events for their respective flows."
- **[DOCS]** [The PaymentIntent object](https://docs.stripe.com/api/payment_intents/object) — 2026-10-20:
  `cancellation_reason` is "either user-provided (`duplicate`, `fraudulent`, `requested_by_customer`, or `abandoned`)
  or generated by Stripe internally (`failed_invoice`, `void_invoice`, `automatic`, or `expired`)".
- **Fit.**
  - The SDK sends `2026-08-26.dahlia`, and the account renders events at `2026-09-30.endive`
    ([`stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive`](stripe-sandbox.md#api-versions-the-sdk-pins-dahlia-the-account-renders-endive)).
    Both are later than basil.
  - So by Stripe's word, a share whose hold lapses reads `status: canceled` and `cancellation_reason: expired`.
  - It arrives as `charge.expired` and `payment_intent.canceled`, with no Refund object and no `charge.refunded`.
  - Its charge keeps `refunded: false` and `amount_refunded: 0`.
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20.
  - **The two holds that lapse first:**
    - `pi_3USELx5y1DMwE3zY14aUf4wv`, 40,00 zł: `requires_capture`, `cancellation_reason: null`, charge
      `capture_before` 2026-10-26 11:03:41 UTC (created 2026-10-19 11:03:41 UTC).
    - `pi_3USA7i5y1DMwE3zY0Nemxwtn`, 40,00 zł: `requires_capture`, `capture_before` 2026-10-26 06:32:43 UTC.
  - **No lapse yet:** the test club has no `charge.expired` event.
  - **Every cancel so far reads `null`:** all 48 cancelled payments on the club read `cancellation_reason: null`.
    That includes `pi_3USPKC5y1DMwE3zY00HIKsMU`, which Stripe itself cancelled after ten refused tries. So `null`
    doesn't by itself mean Raketa let the share go; only `expired` marks a lapse.
- Same answer in a sibling file:
  [`stripe-gaps-05.md#r-rescue-28--a-lapsed-hold-reads-cancellation_re…`](stripe-gaps-05.md#r-rescue-28--a-lapsed-hold-reads-cancellation_reason-expired-and-sends-chargeexpired-and-payment_intentcanceled-the-sandbox-reading-waits-until-26-october).
- **Still to measure after 2026-10-26 11:03:41 UTC.** On both payments, read `status`, `cancellation_reason` and
  `canceled_at`. On their charges, read `refunded`, `amount_refunded` and the refunds. Then list the test club's
  `charge.expired`, `payment_intent.canceled` and `charge.refunded` events.
- **Code:** nothing under `backend/app` reads `cancellation_reason` (grep, 2026-10-20). A lapsed hold is heard only
  through `payment_intent.canceled` and a re-read
  ([`stripe-webhooks.md#a-share-held-taken-released-or-refused-clubs-account`](stripe-webhooks.md#a-share-held-taken-released-or-refused-clubs-account)).

### R-PAY-53 — a live card refund made before the share's money is available

**What Stripe says.**

- **[DOCS]** [Refund and cancel payments](https://docs.stripe.com/refunds) — 2026-10-20 *(translated)*.
  - **Which balance pays:** "Refunds use your available Stripe balance (not including pending amounts). If your
    available balance doesn't cover the refund amount, Stripe holds the refund as pending for card transactions
    (refunds of other payment methods fail) until your Stripe balance is sufficient."
  - **Whose balance:** "Stripe charges refunds of direct charge payments directly to the connected account."
- **[DOCS]** [Adds a field explaining why refunds are pending](https://docs.stripe.com/changelog/basil/2025-04-30/refund-pending-reason)
  — 2026-10-20.
  - `insufficient_funds`: "The balance of the Stripe account is insufficient to cover the refund."
  - `charge_pending`: "The payment being refunded hasn't settled yet."
  - `processing`: "The refund is processing."
- **[DOCS]** [Fix your pending refund](https://support.stripe.com/questions/fix-your-pending-refund) — 2026-10-20, from
  the fetch tool's summary.
  - "Stripe automatically fails a pending refund after 45 days."
  - A pending refund is released only when "the balance of the refund settlement currency is sufficient", and the
    overall balance is too.
  - "Whether a refund is put into `pending` depends on the type of Connect set-up."

**What the sandbox holds.**

- **[MEASURED]** Read via the SDK in the copy, 2026-10-20, the test club's 34 refunds.
  - **Statuses:** 30 `succeeded`, and 4 `failed` with `expired_or_canceled_card` (the Breakers' failing card).
    None is `pending`.
  - **Balance transactions:** every refund's reads `status: pending` and `fee: 0`.
  - **The club's balance:** 0,00 zł available, 407,16 zł pending.
  - So every refund made before its money was available went through at once against the pending balance. This
    confirms
    [`stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-san…`](stripe-refunds-and-disputes.md#the-money-comes-off-the-clubs-balance-on-the-sandbox-off-its-pending-balance-at-once).

**Answer from the docs, which disagree with each other.**

- **The refunds page:** say Paula leaves late and is owed 38,24 zł. If the club's available balance is 0,00 zł, her
  card refund waits as `pending` until the club's available balance covers it. That is the opposite of what the
  sandbox does.
- **A support article:** another Stripe page says a refund waits when it "results in a negative account balance".
  That fits the sandbox's netting. A sibling file found this split first:
  [`stripe-gaps-05.md#r-rescue-47--a-refund-made-before-the-clubs-mone…`](stripe-gaps-05.md#r-rescue-47--a-refund-made-before-the-clubs-money-is-available-stripes-refunds-page-says-it-waits-a-support-page-says-only-a-negative-balance-makes-it-wait-and-the-sandbox-nets-it).
- **After 45 days** it fails with `failure_reason: insufficient_funds`. The refunds page describes that reason as
  "The refund is pending due to insufficient funds and has passed the pending refund expiry window" *(translated)*.

**[ABSENT] Still open.**

- **The questions:**
  - whether a live refund is ever netted against pending funds, as the sandbox does;
  - which `pending_reason` a refund of a taken but not yet available card share carries: `insufficient_funds`, or
    `charge_pending`.
- **Where we looked:** the refunds page, the Refund object, the basil `pending_reason` changelog, and the support page
  on pending refunds.
- A question for Stripe support.

### R-PAY-39 / R-PAY-35 — how many confirmations make Stripe cancel a payment

- **The earlier reading said *not found*:**
  [`stripe-authentication.md#a-payment-confirmed-too-many-times-is-cancelled-by-stripe`](stripe-authentication.md#a-payment-confirmed-too-many-times-is-cancelled-by-stripe).
  The lifecycle page says only: "PaymentIntents might also automatically transition to canceled if they're confirmed
  too many times." The confirm reference, quoted below, answers it.
- **Where we looked again, 2026-10-20:**
  - [The PaymentIntent object](https://docs.stripe.com/api/payment_intents/object): no limit.
  - [Error codes](https://docs.stripe.com/error-codes): no code for it.
  - A docs search for confirmation limits: only the lifecycle sentence.
- **[MEASURED] On the sandbox the ceiling is ten declined attempts.** Answered by a sibling file:
  [`stripe-gaps-07.md#r-security-13--ten-declined-tries-end-a-payment…`](stripe-gaps-07.md#r-security-13--ten-declined-tries-end-a-payment-on-the-sandbox-the-clubs-radar-counts-every-try-the-platforms-rules-cant-reach-a-full-dashboard-club).
  - **The payment:** `pi_3USPKC5y1DMwE3zY00HIKsMU`, 40,00 zł on the test club, held 10 `failed` charges: the server's
    hold, then nine confirmations from the phone.
  - **Stripe's cancel:** Stripe cancelled it one second after the tenth, with `cancellation_reason: null`, not
    `automatic`.
  - Also in
    [`stripe-gaps-05.md#r-rescue-26--no-expiry-for-a-waiting-payment-the…`](stripe-gaps-05.md#r-rescue-26--no-expiry-for-a-waiting-payment-the-sandbox-cancelled-one-when-it-was-confirmed-after-ten-failed-attempts).
- **[DOCS]** [Card declines](https://docs.stripe.com/declines/card) — 2026-10-20: "Be aware that card networks limit the
  number of times you can reattempt a single charge. Stripe recommends a maximum of eight retries for charges that
  permit retries. Card issuers might see creating additional retries as potential fraud, which can result in increased
  declines for legitimate charges."
  - *Reading:* this is the likely source of the spec's "At most 8 retries". It is about retrying a declined charge,
    not about confirming one PaymentIntent again.
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: none of the 48 cancelled payments on the test club reads
  `cancellation_reason: automatic`; all read `null`, the ten-try one included.
- **[DOCS] Stripe calls the number variable.** Carried from
  [`stripe-gaps-01.md#r-fill-45--stripe-calls-the-confirmation-limit-variable-the-sandbox-cancelled-on-the-11th-call-after-10-refused-attempts`](stripe-gaps-01.md#r-fill-45--stripe-calls-the-confirmation-limit-variable-the-sandbox-cancelled-on-the-11th-call-after-10-refused-attempts),
  which quotes [Confirm a PaymentIntent](https://docs.stripe.com/api/payment_intents/confirm?locale=en-GB) (read
  2026-10-20): "There is a variable upper limit on how many times a PaymentIntent can be confirmed. After this limit is
  reached, any further calls to this endpoint will transition the PaymentIntent to the `canceled` state."
- **Answer:** there is no fixed number to build on. Stripe says the limit varies, and the sandbox allowed ten refused
  attempts. Whether live mode allows the same ten is unpublished.
- *Reading:* the code puts no cap on the phone's presses. On the sandbox, Paula's tenth refused try for one share is
  her last, and the payment is gone.

### R-PAY-49 — the React Native SDK 0.38.6's default 3-D Secure timeout

Read from Stripe's own SDK source, 2026-10-20. Stripe's iOS and Android code was read through the GitHub API at the tags
the app's version resolves to.

A sibling file reached the same answer from the same source:
[`stripe-gaps-02.md#r-fill-33-r-fill-61--the-phone-gives-the-banks-check-10-minutes-on-an-iphone-and-5-on-android`](stripe-gaps-02.md#r-fill-33-r-fill-61--the-phone-gives-the-banks-check-10-minutes-on-an-iphone-and-5-on-android).

**What the app passes.** `initStripe` gets no `threeDSecureParams`
(`frontend_player/src/shared/lib/platform/payments.tsx:223-228`).

**iPhone: 10 minutes, and the app can't change it.**

- **The React Native layer:** stripe-react-native 0.38.6's `configure3dSecure` sets only `uiCustomization`. It never
  sets the timeout, even when one is passed
  (`frontend_player/node_modules/@stripe/stripe-react-native/ios/StripeSdk.swift:479-484`).
- **The iOS SDK it uses:** its pod pins `Stripe ~> 23.28.0` (`stripe-react-native.podspec:5`).
- **[DOCS]** In stripe-ios
  [23.28.0](https://github.com/stripe/stripe-ios/blob/23.28.0/StripePayments/StripePayments/Source/PaymentHandler/STPThreeDSCustomizationSettings.swift)
  and 23.28.3, `authenticationTimeout` "is the total time allowed for a user to complete a 3DS2 authentication
  interaction, in minutes. This value *must* be at least 5 minutes. Defaults to 10 minutes." The value is
  `authenticationTimeout = 10`, and the handler waits `authenticationTimeout * 60` seconds (`STPPaymentHandler.swift:1177`).

**Android: 5 minutes.**

- **The React Native layer:** it sets a timeout only when `threeDSecureParams` is passed and holds a `timeout`
  (`frontend_player/node_modules/@stripe/stripe-react-native/android/src/main/java/com/reactnativestripesdk/StripeSdkModule.kt:109-111`, `:142-144`).
- **The Android SDK it uses:** `StripeSdk_stripeVersion=20.48.+` (the same package's `android/gradle.properties:3`).
- **[DOCS]** In stripe-android
  [v20.48.0](https://github.com/stripe/stripe-android/blob/v20.48.0/payments-core/src/main/java/com/stripe/android/PaymentAuthConfig.kt)
  and v20.48.6:
  - **The default:** `DEFAULT_TIMEOUT = 5`, allowed range 5–99 minutes.
  - **At the end:** "If the timeout is reached, the challenge screen will close, control will return to the launching
    Activity/Fragment, payment authentication will not succeed, and the outcome will be represented as
    `StripeIntentResult.Outcome.TIMEDOUT`."

**Answer.**

- **The times:** a bank's check in the app may run 10 minutes on an iPhone and 5 minutes on Android.
- **Stripe's floor:** both meet Stripe's "must be at least 5 minutes"
  ([`stripe-authentication.md#the-banks-check-may-run-for-at-least-five-minutes`](stripe-authentication.md#the-banks-check-may-run-for-at-least-five-minutes)).
- *Reading:* these bound the in-app 3DS2 challenge. A check that opens as a web page (the sandbox's `redirect_to_url`,
  PAY Breaker S7) is not under them (unverified).

### R-PAY-34 — whether a club's copy of the card inherits the platform setup's 3-D Secure

- **[DOCS]** Carried from [`stripe-authentication.md#the-platforms-setup-carries-to-every-clone-on-a…`](stripe-authentication.md#the-platforms-setup-carries-to-every-clone-on-a-clubs-account),
  read 2026-10-19:
  - **The clone inherits the setup:** "the cloned PaymentMethod inherits the setup performed on your platform account,
    so you don't need to set it up again on the connected account."
  - **Permission is shared too:** sharing a payment method "automatically shares customer permission as well".
  - **Fit:** the platform and every club are Polish, so `on_behalf_of` isn't needed.
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20.
  - **The 3155 setups:** the platform holds five setups for 4000 0025 0000 3155. Four are `requires_action`:
    `seti_1USA5o5y1DB8chHbdXmubZQ8`, `seti_1USA7H5y1DB8chHbDmxpCp8r`, `seti_1USA925y1DB8chHbOYP7vBod` and
    `seti_1USELX5y1DB8chHbexYSC652`. One is `canceled`: `seti_1USPFy5y1DB8chHbBQdPAgly`.
  - **No payment:** none of these setups succeeded, and none of the 112 payments on the test club used a 3155 card.
  - So the inheritance has never been tried on the sandbox.
- **Answer:** Stripe's documented word is yes. It is unmeasured; the same holds in
  [`stripe-gaps-01.md#r-fill-11--a-copy-inherits-the-setups-bank-check-by-stripes-word-still-unproven-on-the-sandbox`](stripe-gaps-01.md#r-fill-11--a-copy-inherits-the-setups-bank-check-by-stripes-word-still-unproven-on-the-sandbox).
- **What would prove it.** On a phone, save 4000 0025 0000 3155 and pass the bank's check. Then let a fill hold a
  share without the player. Stripe's docs predict `requires_capture`; an `authentication_required` refusal would
  contradict them.

### R-PAY-5 — whether Google Pay production access has been asked for

- **[DOCS]** Stripe's steps, carried from
  [`stripe-saving-cards.md#google-pay-googles-terms-production-access-a-real-device`](stripe-saving-cards.md#google-pay-googles-terms-production-access-a-real-device):
  production access, integration type **Gateway**, screenshots, `testEnv: false`, and a signed release build.
- **[DOCS]** [Google: Request production access](https://developers.google.com/pay/api/android/guides/test-and-deploy/request-prod-access)
  — 2026-10-20, from the fetch tool's summary.
  - **Where:** in the Google Pay & Wallet Console, "Google Pay API > Integrations > Integrate with your Android app".
  - **What to send:** "Upload the application screenshots that show your test Google Pay API integration", "Select
    Integration type: Gateway", then **Submit for approval**.
  - **Then:** "The information is sent to our onboarding team, and you need to wait for their response."
  - **Release builds:** "The debug key doesn't work in the production environment."
  - **Review time:** not stated.
- **Code:**
  - Google Pay is switched on in the app's config (`frontend_player/app.config.ts:115`).
  - `testEnv` follows the key's prefix (`frontend_player/src/shared/lib/platform/payments.tsx:354`).
- **[ABSENT]** Whether it has been asked for.
  - **In the repo:** not recorded. Grep for "production access", "Wallet Console" and "Gateway" in `docs/` and
    `frontend_player/` found nothing (2026-10-20).
  - **At Stripe:** neither Stripe's API nor the sandbox can show it; it lives in the app owner's Google Pay & Wallet
    Console.
  - **Who can answer:** a question for the product owner, not Stripe.

### R-PAY-6 — whether an Apple Pay card saved by a setup holds without the player at Polish issuers

- **Carried:**
  - **The phone's own token:** it can fail later charges made without the player. Apple Pay off-session is "slightly
    higher risk", with no liability shift and "lower authorization rates", and its terms forbid reusing a saved card
    on-session. Sources:
    [`stripe-saving-cards.md#a-device-token-can-fail-later-merchant-initiated-payments`](stripe-saving-cards.md#a-device-token-can-fail-later-merchant-initiated-payments)
    and
    [`stripe-saving-cards.md#the-setup-consumes-the-wallets-cryptogram-a-save…`](stripe-saving-cards.md#the-setup-consumes-the-wallets-cryptogram-a-saved-apple-pay-card-may-not-be-used-on-session).
  - **Merchant tokens:** they "cannot be used for unscheduled card on file"
    ([`gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unschedule…`](gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unscheduled-card-on-file)).
- **[ABSENT]** How Polish issuers treat either token for an unscheduled, deferred charge.
  - **Where we looked:** Stripe's merchant-tokens and Apple Pay recurring pages, and Apple's partner page. None names an
    issuer or a country for approval rates or for merchant-token support.
  - **The sandbox can't try it:** Apple Pay is dormant while `APPLE_PAY_MERCHANT` is null, and needs a real card even
    in test mode.
  - A question for Stripe support.

### R-PAY-26 / R-PAY-27 — whether automatic card updates reach Polish issuers

- **Carried [ABSENT]:**
  - [`gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers`](gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers);
  - [`stripe-saving-cards.md#automatic-card-updates-what-they-need-and-the-two-events`](stripe-saving-cards.md#automatic-card-updates-what-they-need-and-the-two-events):
    "International support varies from country to country. It isn't possible to identify cards that support
    automatic updates."
- **Searched again, 2026-10-20: whether Mastercard requires issuers in Europe or Poland to take part in its Automatic
  Billing Updater.**
  - **What turned up:** a Swiss issuer (PostFinance) saying it is obliged to provide the service, a US bank, and
    Mastercard's privacy notices for EEA countries.
  - **What failed:** Mastercard's Polish and Czech notices answered 403.
  - **What's missing:** no statement from a Polish issuer.
- **[PRICE]** [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — 2026-10-20, from the fetch tool's summary.
  The card updater falls under Authorisation Boost: "Included at no additional charge for businesses on standard
  payments pricing", and "0.2% per successful online card transaction" on custom pricing.
- **On the sandbox:** nothing can make an update
  ([`stripe-testing.md#no-test-card-or-trigger-for-an-automatic-card-update`](stripe-testing.md#no-test-card-or-trigger-for-an-automatic-card-update)).
- **[ABSENT]** Whether PKO BP, Pekao, mBank, ING or Santander send updates. A question for Stripe support, which can say
  whether updates reach Polish-issued cards at all.

### R-PAY-41 — `charge.updated` after a manual capture, and whether a partial refund can be a fee-returning reversal

**Part 1: `charge.updated`.**

- **[DOCS]** [Event types](https://docs.stripe.com/api/webhook_endpoints/create) — 2026-10-20: `charge.updated` "Occurs
  whenever a charge description or metadata is updated, or upon an asynchronous capture."
- **[DOCS]** [Asynchronous capture](https://docs.stripe.com/payments/payment-intents/asynchronous-capture) — 2026-10-20.
  - **How it is chosen:** "use `automatic_async` as the capture method"; "Stripe enables its functionality by default
    in the latest version of the API".
  - **What it promises:** "You can listen for the `charge.updated` event to know when the balance transaction becomes
    available"; "Our SLA for the charge.updated webhook is 1 hour after the successful PaymentIntent confirmation."
  - **What it leaves out:** the page covers only capture at confirmation, never `capture_method: manual`.
- **[DOCS]** [The PaymentIntent object](https://docs.stripe.com/api/payment_intents/object) — 2026-10-20.
  - `automatic_async` is "(Default)".
  - `manual`: "Place a hold on the funds when the customer authorizes the payment, but don't capture the funds until
    later."
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: every event on the test club. There are 56
  `charge.captured`, 56 `payment_intent.succeeded` and 0 `charge.updated`. The fee came with the capture's answer
  ([`stripe-webhooks.md#the-fee-kept-on-a-taken-share`](stripe-webhooks.md#the-fee-kept-on-a-taken-share)).
- **Answer:**
  - Stripe documents `charge.updated` carrying the fee only for asynchronous capture, which is `automatic_async`.
  - For a manual capture nothing says Stripe sends it, and the sandbox never has.
  - The code's "the fee is ready" path (`stripe_notices.py:57`, `:120-129`) waits on an event Stripe doesn't describe
    for this flow. The capture's own answer carries the fee.
- **[ABSENT]** Whether live mode ever sends it after a manual capture. Not on the asynchronous-capture, event-type or
  hold pages. A question for Stripe support.

**Part 2: a partial refund as a reversal.**

- **[DOCS]** [Refund and cancel payments](https://docs.stripe.com/refunds) — 2026-10-20 *(translated)*.
  - **Ordinary refunds:** "Stripe's processing fees from the original transaction aren't returned."
  - **Reversals:** "Some refunds (those issued shortly after the original charge) appear as a reversal instead of a
    refund." The page's glossary note says "Stripe doesn't withhold any fees for payment reversals".
  - **IC+ pricing:** "IC+ users might notice a difference in cost between reversals and refunds because reversals
    generally have lower network fees."
- Carried:
  - a reversal usually comes within about 2 hours of the capture:
    [`stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-i…`](stripe-refunds-and-disputes.md#a-refund-within-about-two-hours-of-the-capture-is-usually-a-reversal-with-no-credit-line);
  - partial reversals exist:
    [`gaps-CLUBMONEY.md#a-partial-refund-can-be-a-partial-reversal`](gaps-CLUBMONEY.md#a-partial-refund-can-be-a-partial-reversal);
  - the refunds page says both that fees aren't returned and that none is withheld on a reversal:
    [`stripe-gaps-05.md#r-rescue-20--a-refund-made-as-a-reversal-stripes…`](stripe-gaps-05.md#r-rescue-20--a-refund-made-as-a-reversal-stripes-refunds-page-says-both-that-fees-arent-returned-and-that-none-is-withheld).
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20: the test club's 34 refunds, 17 of them partial.
  - **Kind:** every one reads `destination_details.card.type: refund`; none is a reversal.
  - **Fee:** every refund's balance transaction carries `fee: 0`, so no fee came back.
- **[ABSENT]** Not found anywhere.
  - Whether a partial reversal gives back all of Stripe's fee, part of it, or none.
  - The sandbox still can't make a reversal
    ([`gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a…`](gaps-CLUBMONEY.md#no-published-window-and-nothing-on-the-fee-of-a-partial-reversal)).
  - A question for Stripe support.

### R-PAY-1 — whether a live platform whose charges are off can save cards live

- **Carried [ABSENT]:**
  [`stripe-saving-cards.md#whether-the-platform-must-be-activated-to-save-cards-live`](stripe-saving-cards.md#whether-the-platform-must-be-activated-to-save-cards-live).
  The sandbox platform reads `charges_enabled: false`
  ([`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account)).
- **[DOCS]** [Error codes](https://docs.stripe.com/error-codes) — 2026-10-20 *(translated)*: `testmode_charges_only`:
  "You can only make test charges. Set up your account in the Dashboard to start processing payments in live mode." It speaks
  of charges and says nothing about SetupIntents.
- **Where we looked again:** a docs search on activating a Connect platform for live mode found the platform-profile
  prerequisites and live-mode URL rules, and nothing about setups.
- **[ABSENT]** A question for Stripe support.

### R-PAY-34 / R-PAY-53 — taking a held share, or refunding, while Stripe has paused a club's charges

- **Carried [ABSENT]:**
  - [`stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refun…`](stripe-connect.md#not-found-whether-a-hold-can-be-taken-or-a-refund-made-after-charges-are-disabled);
  - [`gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-no…`](gaps-CLUBSETUP.md#whether-a-charges-disabled-account-can-refund-not-documented-not-tried);
  - the same gap for a rescue:
    [`stripe-gaps-05.md#r-rescue-21--taking-a-hold-after-the-clubs-charg…`](stripe-gaps-05.md#r-rescue-21--taking-a-hold-after-the-clubs-charges-are-disabled-undocumented).
- **[DOCS]** [Pause payments and payouts on connected accounts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts)
  — 2026-10-20.
  - **What a pause stops:** "Pausing payments blocks creation of any charges. It also makes the transfer, card_payments
    and other payment methods capabilities `inactive`."
  - **How it shows:** the account then reads `charges_enabled: false` with `disabled_reason: platform_paused`.
  - **The sandbox:** "we don't enforce payment or payout pauses in a sandbox".
  - **Accounts v2:** "This workflow isn't available when using Accounts v2."
  - **What it leaves out:** the page covers new charges only. It says nothing about taking a hold that already exists
    or refunding a taken share.
- *Reading:* taking a hold creates no new charge, because the charge has existed since the hold. So the page's words
  don't forbid it, but they don't allow it either. They also describe a platform's pause, not Stripe's own
  (unverified).
- **The sandbox can't settle it:**
  - pauses aren't enforced there;
  - the block cards
    ([`stripe-testing.md#cards-that-block-a-clubs-charges-or-payouts`](stripe-testing.md#cards-that-block-a-clubs-charges-or-payouts))
    need a write.
- **[ABSENT]** A question for Stripe support.

### R-CLUBMONEY-34 — what `payouts.create` answers on a club still on Stripe's `daily` schedule

- **Carried [ABSENT]:**
  - [`stripe-payouts-and-balances.md#a-standard-manual-payout-needs-the-account-on-th…`](stripe-payouts-and-balances.md#a-standard-manual-payout-needs-the-account-on-the-manual-schedule);
  - [`gaps-CLUBMONEY.md#not-found-a-platform-payout-while-the-account-st…`](gaps-CLUBMONEY.md#not-found-a-platform-payout-while-the-account-stays-on-an-automatic-schedule);
  - the same two questions for the platform, with all seven accounts' Balance Settings:
    [`stripe-gaps-00.md#r-platform-24--the-error-payoutscreate-returns-o…`](stripe-gaps-00.md#r-platform-24--the-error-payoutscreate-returns-on-a-daily-schedule-account-and-whether-raketa-may-set-manual-through-balance-settings).
- **[DOCS]** [Create a payout](https://docs.stripe.com/api/payouts/create) — 2026-10-20.
  - "To send funds to your own bank account, create a new payout object. Your Stripe balance must cover the payout
    amount. If it doesn't, you receive an 'Insufficient Funds' error."
  - The page says nothing about the account's schedule.
- **[DOCS]** [Payouts](https://docs.stripe.com/payouts) — 2026-10-20 *(translated)*.
  - "If you turn off automatic payouts, you must send funds to your bank account manually."
  - "Daily payouts: Stripe automatically transfers your available funds every business day."
  - "Each payout reflects your account's available balance at the time it was created."
  - No sentence covers a manual payout while automatic payouts are on.
- **[DOCS]** [Error codes](https://docs.stripe.com/error-codes) — 2026-10-20. No code names a payout schedule. The
  nearest are `balance_insufficient` and `payouts_not_allowed` ("Payouts have been disabled on the connected
  account").
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20, with `GET /v1/balance_settings` made as each account.
  - **The test club:** `payments.payouts.schedule.interval: manual`, `payouts.status: enabled`,
    `settlement_timing.delay_days: 7`, the day starting 00:00 `Etc/UTC`.
  - **A club Raketa opened:** `acct_1USELi5y1DCSZFum` reads `interval: daily` and `payouts.status: disabled`; it was
    never onboarded.
  - **The one payout so far:** `po_1USPGD5y1DMwE3zY2VJcHrmh`, 37,70 zł, `automatic: false`, standard, `paid`. It was
    made on the manual club.
  - **Correction:** Balance Settings are readable through the SDK. The *not available through either MCP server* line
    in
    [`stripe-payouts-and-balances.md#on-accounts-v2-a-clubs-payout-settings-live-in-b…`](stripe-payouts-and-balances.md#on-accounts-v2-a-clubs-payout-settings-live-in-balance-settings)
    was a limit of the tool, not of Stripe.
- **[ABSENT]** The answer itself.
  - Nobody has asked Stripe for a payout from a `daily` club that has money available. Only a write would show the
    answer, and that is outside this research.
  - A question for Stripe support, or a Breaker proof.

### R-CLUBMONEY-34 — whether Raketa may set `manual` through Balance Settings on its clubs, and whether the club can still pay itself out

- **[DOCS]** Carried from three sections of `stripe-payouts-and-balances.md`:
  - [`#who-may-change-a-clubs-interval-and-delay`](stripe-payouts-and-balances.md#who-may-change-a-clubs-interval-and-delay):
    platforms with platform controls "can adjust the payout interval"; "If you need full control … contact us";
  - [`#on-accounts-v2-a-clubs-payout-settings-live-in-balance-settings`](stripe-payouts-and-balances.md#on-accounts-v2-a-clubs-payout-settings-live-in-balance-settings):
    "Use Balance Settings to manage payout settings for Accounts v2";
  - [`#a-full-dashboard-club-needs-platform-controls-and-can-still-pay-itself-out--instantly-too`](stripe-payouts-and-balances.md#a-full-dashboard-club-needs-platform-controls-and-can-still-pay-itself-out--instantly-too):
    "Connected accounts can still make manual payouts after you … restrict connected accounts from updating their own
    payout schedule".
- **[DOCS]** [Update balance settings](https://docs.stripe.com/api/balance-settings/update?query=payments) — 2026-10-20.
  - **The call:** "Updates balance settings for a given connected account."
  - **The interval:** `payments.payouts.schedule.interval`: "How frequently available funds are paid out. One of:
    `daily`, `manual`, `weekly`, or `monthly`. Default is `daily`." The value `manual`: "You manually send funds to
    your bank account."
  - **Conditions:** the reference sets none by liability or Dashboard type.
- **[MEASURED]** Read via the SDK in the copy, 2026-10-20, from the test club's events.
  - **The change:** `evt_1US9LE5y1DMwE3zYRrckuQyW`, an `account.updated` at 2026-10-19 05:42:35 UTC, made by request
    `req_olqI3OLV4bqyRF`. Its `previous_attributes.settings.payouts.schedule.interval` is `daily`.
  - **What that shows:** the club (Accounts v2, full Dashboard, Stripe liable —
    [`stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pa…`](stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses))
    was moved from `daily` to `manual`, and Stripe accepted it.
  - **No Balance Settings event:** there is no `balance_settings.updated` on the club or the platform.
  - **Who did it:** the API doesn't show whose key made the request, Raketa's platform key or the club's own Dashboard.
- **Answer:**
  - Stripe's docs say Raketa may set `manual`, through platform controls and Balance Settings.
  - The sandbox shows a club of exactly this kind can sit on `manual`.
  - Nothing stops the club paying itself out, instantly too. Stripe documents that.
- **[ABSENT] Still open.**
  - Stripe's confirmation that Raketa's own key, not only the club, may set `manual` on a Stripe-liable,
    full-Dashboard v2 club.
  - What Stripe's "full control" arrangement would add.
  - A question for Stripe support. One write would settle the first part: `POST /v1/balance_settings` with
    `Stripe-Account` set to a club Raketa opened, then read the answer.
