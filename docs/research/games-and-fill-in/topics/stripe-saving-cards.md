# Stripe — saving cards

What Stripe says about saving a player's card for charges made without the player, and what the
sandbox holds, read **2026-10-19** against the code at `9ab0ea5b`. Raketa's shape: a player is a
**v1 Customer on the platform** carrying only their id; the card is typed into Stripe's `CardField`
and saved by a **SetupIntent** (`off_session`, cards only) after the player accepts the terms; each
share **clones the card onto the club's account** (Accounts v2, the club pays the fees, Stripe
covers losses) and holds it there as a **direct charge** in złoty. Google Pay on Android; Apple Pay
waits on a merchant identifier.

Sources: docs.stripe.com (fetched in en-GB where the page offered it), the four Stripe tools, and
`stripe` (platform, `acct_1US89K5y1DB8chHb`) / `stripe-club` (test club, `acct_1US95f5y1DMwE3zY`)
for reads. No write tool was used. Sandbox objects come from the contract run recorded in
[`stripe-sandbox.md`](stripe-sandbox.md) §3; its *Differences* D1–D7 are not repeated here.
Idempotency keys for the setup calls are in
[`stripe-reliability.md`](stripe-reliability.md#the-keys-this-product-sends); the setup events the
code reads and drops are in [`stripe-webhooks.md`](stripe-webhooks.md) (`setup_intent.*`, lines on
the sandbox's platform events).

---

## 1. SetupIntents for later off-session use

### A SetupIntent saves a card without charging it, and attaches it to its customer on success
- **[DOCS]** "Use the Setup Intents API to set up a payment method for future payments. It's similar
  to a payment, but no charge is created … When setting up a card, for example, it may be necessary
  to authenticate the customer or check the card's validity with the customer's bank."
  [Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-19
- **[DOCS]** `customer`: "If present, the SetupIntent's payment method will be attached to the
  Customer on successful setup. Payment methods attached to other Customers cannot be used with this
  SetupIntent." [API: The SetupIntent object](https://docs.stripe.com/api/setup_intents/object) — read 2026-10-19
- *Code:* `setup_intents.create` with `customer`, `usage: off_session`, `payment_method_types:
  ["card"]` (`backend/app/modules/payments/infrastructure/stripe_payments.py:203-222`).

### `usage: off_session` is the default, and it is an optimisation, not a guarantee
- **[DOCS]** "Setting `usage` to `off_session` properly authenticates a credit or debit card for
  off-session payments so that your customer doesn't have to come back online and re-authenticate."
  And: "`Usage` is an optimisation … Either case might still require authentication later, so build
  a recovery process in your app. When an off-session card payment requires authentication, bring
  your customer back online to complete the payment." If not given, it "defaults to `off_session`".
  [Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-19

### The statuses, and where a refusal is kept
- **[DOCS]** `status` is one of `requires_payment_method`, `requires_confirmation`, `requires_action`,
  `processing`, `canceled`, `succeeded`; `last_setup_error` is "The error encountered in the previous
  SetupIntent confirmation"; `latest_attempt` is "The most recent SetupAttempt".
  [API: The SetupIntent object](https://docs.stripe.com/api/setup_intents/object) — read 2026-10-19
- *Code:* `read_setup` maps `requires_payment_method` with a `last_setup_error` to *declined*, and
  without one to *awaiting the phone* (`stripe_payments.py:224-271`). What a declined setup hands
  back (decline and network codes) is already in
  [`gaps-PAY.md#what-a-declined-setup-hands-back`](gaps-PAY.md#what-a-declined-setup-hands-back) (2026-10-08).

### A setup can be cancelled only before it succeeds
- **[DOCS]** "You can cancel a SetupIntent object when it's in one of these statuses:
  `requires_payment_method`, `requires_confirmation`, or `requires_action`. After you cancel it,
  setup is abandoned and any operations on the SetupIntent fail with an error … Returns an error if
  the SetupIntent is already canceled or isn't in a cancelable state." `cancellation_reason`:
  `abandoned`, `requested_by_customer`, `duplicate`.
  [API: Cancel a SetupIntent](https://docs.stripe.com/api/setup_intents/cancel) — read 2026-10-19
- *Code:* a setup replaced by a newer one is cancelled after the commit; if it had already
  succeeded, the card it saved is detached (`backend/app/modules/payments/application/handlers/release_methods.py:52-74`,
  `stripe_payments.py:273-290`). No `cancellation_reason` is sent.

### The client secret: never stored, logged or shown to anyone but the customer
- **[DOCS]** "The client secret can be used to complete payment setup from your frontend. It should
  not be stored, logged, or exposed to anyone other than the customer."
  [API: The SetupIntent object](https://docs.stripe.com/api/setup_intents/object) — read 2026-10-19
- **[DOCS]** "You can use the client secret to validate and authenticate card details using the
  credit card networks. The client secret is sensitive—don't log it, embed it in URLs, or expose it
  to anyone but the customer." [Set up future card payments (React Native)](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native) — read 2026-10-19
- *Code:* the secret is handed out only as the answer to accepting the terms
  (`backend/app/modules/payments/application/setup.py:133-170`); who may hold it is the `security` topic.

### What a saved card looks like on the platform
- **[MEASURED]** `stripe` · `GET /v1/setup_intents/seti_1USEM75y1DB8chHbIWnqTBhZ?expand[]=payment_method&expand[]=latest_attempt`
  · 2026-10-19: `status: succeeded`, `usage: off_session`, `on_behalf_of: null`,
  `request_three_d_secure: automatic`, `mandate: null`; attempt `setatt_1USEM75y1DB8chHblEjfWXN3`
  `three_d_secure: null`, `cvc_check: pass`. The saved `pm_1USEM75y1DB8chHbfBXqHM9F`:
  `customer: cus_VTAhPi9eS8Wact`, `allow_redisplay: unspecified`, every `billing_details` field
  null, Visa •••• 4242, `exp_month: 10`, `exp_year: 2027`, `country: US`, `funding: credit`,
  `networks.available: ["visa"]`, `wallet: null`, `regulated_status: unregulated`.

---

## 2. Consent for merchant-initiated payments

### What the terms must say
- **[DOCS]** "If you set up a payment method for future off-session payments, you need permission.
  Creating an agreement (sometimes called a mandate) up front allows you to charge the customer when
  they're not actively using your website or app." [Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-19
- **[DOCS]** What the terms must cover: "The customer's agreement to your initiating a payment or a series of
  payments on their behalf for specified transactions; The anticipated timing and frequency of
  payments; How you determine the payment amount; Your cancellation policy for any subscription
  services." And: "require customers to opt in before you save their payment information."
  [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-19
- *Code:* the terms are the client's text; the backend holds only their version, `2026-10-10`
  (`backend/app/modules/payments/domain/terms.py:20-25`); the words are the mechanics §12.5.

### Keep a record, and use the card only for the purpose agreed
- **[DOCS]** "Keep a record of each customer's agreement to your terms." "When you save a payment
  method, you can only use it for the specific purposes included in your terms."
  [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-19
- **[DOCS]** Showing a saved method again in a later checkout is a separate purpose: "you must
  explicitly collect consent from the customer for this specific use", and `allow_redisplay` tells
  the two apart. [Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-19
- *Code:* each acceptance records version, time, IP and the card brand it was given for
  (`backend/app/modules/payments/domain/payment_method.py:95-104`, `:208-234`).

### Authentication at saving is what lets later payments go as merchant-initiated
- **[DOCS]** "Under SCA, authentication is required when saving a card to collect customer
  permission and qualify for off-session exemptions for subsequent off-session payments."
  [SCA for Connect platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms) — read 2026-10-19
- **[DOCS]** "When you set up your integration to properly save a card, Stripe marks any subsequent
  off-session payment as a merchant-initiated transaction (MIT) so that your customers don't have to
  come back online and authenticate. Merchant-initiated transactions require an agreement between you
  and your customer." [Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-19
- The off-session exemptions themselves, and `authentication_required`, are the `authentication`
  topic. An EBA reading of "payee-initiated" is in
  [`local-market.md#charging-a-saved-card-without-the-player-there`](local-market.md#charging-a-saved-card-without-the-player-there) (2026-10-07).

### A card whose brand changed cannot be charged as an MIT until its holder agrees again
- **[DOCS]** "In some cases, an automatic update changes a card's brand (for example, from Visa to
  Mastercard). When a card's brand changes, you must prompt the cardholder to update their payment
  method. Identify card brand changes by listening for the `payment_method.automatically_updated`
  event and comparing the `brand` in `previous_attributes` with the `brand` in the associated `card`
  object." **"When a card's brand changes, you can't charge it for any MITs until you get a new
  cardholder agreement."** [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-19
- *Code:* the brand the consent was given for is compared with the card's brand now; a mismatch, or
  terms no longer in force, refuses the hold without asking Stripe (`payment_method.py:152-163`;
  `backend/app/modules/payments/application/seat_charges.py:426-432`). Polish cards do move between
  networks: [`gaps-PAY.md#polish-cards-do-move-between-networks`](gaps-PAY.md#polish-cards-do-move-between-networks) (2026-10-08).

### Sharing a card with a connected account shares the customer's permission
- **[DOCS]** "If you clone saved payment methods to reuse across multiple connected accounts, sharing
  a payment method with a connected account automatically shares customer permission as well. This
  allows the platform to make off-session payments on any of their connected accounts without
  requiring the customer to authenticate their payment method again."
  [SCA for Connect platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms) — read 2026-10-19
- **[DOCS]** For bank debits only, Stripe adds: "you must communicate to the customer that their
  authorization extends to connected accounts on your platform … Failure to communicate this message
  … could result in customer confusion and increase the risk of disputed payments."
  [Payment method support for Connect](https://docs.stripe.com/payments/payment-methods/payment-method-connect-support) — read 2026-10-19
- **[ABSENT]** The same wording for cards: no card page asks it; looked in the two pages above and
  [direct-charges-multiple-accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-19.
  Raketa's terms do name "the club it is played at" as the one that holds the share (mechanics §12.5).

---

## 3. The React Native SDK

### Stripe recommends the Payment Sheet; the card-only guide is for two cases
- **[DOCS]** "We recommend that you follow the Accept in-app payments guide. Only use this guide if
  you need to use manual server-side confirmation or your integration requires presenting payment
  methods separately." [Set up future card payments (React Native)](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native) — read 2026-10-19
- **[DOCS]** The Payment Sheet "doesn't support customer-configured Accounts … It only supports
  `Customer` objects", and "When used with a SetupIntent, PaymentSheet supports cards and PayPal."
  [Accept in-app payments (setup)](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup) — read 2026-10-19
- *Code:* Raketa presents its own four steps (choose, card, terms, bank) with `CardField`
  (`frontend_player/src/shared/lib/platform/payments.tsx:6-41`) — the "present payment methods
  separately" case, so the terms can sit between the card and the bank.

### The card-only flow
- **[DOCS]** "pass the customer card and billing information to `confirmSetupIntent`." "The SDK
  manages the payment confirmation and authentication flow." "When saving card details to use for
  future off-session payments, especially in Europe … get permission to save a card. Include text in
  your checkout flow to inform your customer how you intend to use the card."
  [Set up future card payments (React Native)](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native) — read 2026-10-19
- *Code:* `createPaymentMethod({paymentMethodType: 'Card'})` while the field is mounted, then
  `confirmSetupIntent(secret, {paymentMethodType: 'Card', paymentMethodData: {paymentMethodId}})`;
  `postalCodeEnabled={false}`; no billing details are sent (`payments.tsx:284`, `:331-386`).

### The return URL
- **[DOCS]** "When a customer exits your app (for example to authenticate in Safari or their banking
  app), provide a way for them to automatically return to your app … Register a custom URL. Universal
  links aren't supported … Set up your root component to forward the URL to the Stripe SDK"
  (`handleURLCallback`); `urlScheme` is "required for 3D Secure and bank redirects".
  [Accept in-app payments (setup)](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup) — read 2026-10-19
- *Code:* `initStripe({urlScheme: APP_SCHEME, …})`; the URL listener lives only while a confirmation
  runs (`payments.tsx:220-243`). Stripe's sample also reads `Linking.getInitialURL()`; the code does
  not — a cold start from the bank app would not be handed to Stripe (*unverified* on a device).

### The SDK's support policy, and the version the app ships
- **[DOCS]** "New features and bug fixes are released on the latest minor version of the SDK. If
  you're on an older minor version, we recommend upgrading … Older minor versions of the SDK continue
  to be available for use, but won't receive any additional updates." "Unless specifically noted …
  the mobile SDKs is compatible with any Stripe API version you use on your backend."
  [Mobile SDK versioning](https://docs.stripe.com/sdks/mobile-sdk-versioning) — read 2026-10-19
- **[DOCS]** Latest releases: 0.82.0 (2026-10-13), 0.81.0 (2026-10-06), 0.80.0 (2026-09-30); the
  0.78.0 notes say "React Native versions < 0.75 are deprecated".
  [stripe-react-native releases](https://github.com/stripe/stripe-react-native/releases) — read 2026-10-19
- *Code:* `"@stripe/stripe-react-native": "0.38.6"` with Expo `~52.0.0` and React Native 0.76.9
  (`frontend_player/package.json:34-51`) — 44 minor versions behind, receiving no fixes.

### Recovery confirms the same failed payment
- **[DOCS]** "Give the customer the option to update or remove their saved card and try payment
  again … confirm the original, failed PaymentIntent by reusing its client secret instead of creating
  a new one. If the payment failed because it requires authentication, try again with the existing
  PaymentMethod instead of creating a new one" (sample: `lastPaymentError?.paymentMethod.id`).
  [Set up future card payments (React Native)](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native) — read 2026-10-19
- *Code:* the same, on the club's account (`stripeAccountId`), with the bank's check for
  `authentication_required` and a typed card for a decline (`payments.tsx:388-414`). Stripe's sample
  reuses a card attached to a customer; Raketa's `lastPaymentError.paymentMethod` is the **clone**
  (§7, *A refused clone*).

---

## 4. Wallets

### Wallet cards are saved as `card` PaymentMethods
- **[DOCS]** `card.wallet.type` is "one of `amex_express_checkout`, `apple_pay`, `google_pay`,
  `masterpass`, `samsung_pay`, `visa_checkout`, or `link`"; `card.wallet.dynamic_last4` is "(For
  tokenized numbers only.) The last four digits of the device account number"; `card.fingerprint`:
  "For payment methods that tokenize card information (Apple Pay, Google Pay), the tokenized number
  might be provided instead of the underlying card number."
  [API: The PaymentMethod object](https://docs.stripe.com/api/payment_methods/object) — read 2026-10-19
- *Code:* `card_of` keeps only `apple_pay` and `google_pay` as wallets, anything else as a plain card,
  and shows `last4`, never `dynamic_last4` (`stripe_payments.py:81`, `:145-157`).

### Google Pay: Google's terms, production access, a real device
- **[DOCS]** "By integrating Google Pay, you agree to Google's terms of service." "Expo Go doesn't
  support Google Pay … you must create a development build" (Apple Pay likewise). To go live:
  "request production access for your app. Choose the integration type **Gateway** when prompted, and
  provide screenshots of your app for review … test your integration in production by using
  `testEnv: false`, and launching Google Pay from a signed, release build." "You must test Google Pay
  using a physical Android device … with a real card saved to Google Wallet." When confirming a
  SetupIntent, "use `confirmPlatformPaySetupIntent`".
  [Google Pay (React Native)](https://docs.stripe.com/google-pay?platform=react-native) — read 2026-10-19
- **[DOCS]** Three kinds of Google Pay card: a card added on the phone is "a Device Primary Account
  Number (DPAN), and it supports liability shift by default"; one added in Chrome or a Google property
  is "a Funding Primary Account Number (FPAN)"; a card picked in another merchant's Google Pay flow is
  "saved as e-commerce tokens that represent the cards on file. Neither liability shift nor 3D Secure
  are supported for e-commerce tokens at this time." Same page — read 2026-10-19
- *Code:* `confirmPlatformPaySetupIntent` with `testEnv` set from the key's prefix,
  `merchantCountryCode: 'PL'`, `currencyCode: 'PLN'` (`payments.tsx:350-372`); Google Pay is offered
  only after Stripe was started once on that visit (`payments.tsx:314-329`).

### Apple Pay: a merchant ID, a Stripe certificate, a real card even in test mode
- **[DOCS]** "enrol in the Apple Developer Program … register for an Apple Merchant ID and create a
  new Apple Pay certificate." "To test Apple Pay, you must use a real credit card number and your test
  API keys … You can't save Stripe test cards or Apple Pay test cards to Apple Pay wallets."
  [Apple Pay (React Native)](https://docs.stripe.com/apple-pay?platform=react-native) — read 2026-10-19
- **[DOCS]** "The certificate is valid for 25 months from activation."
  [Apple Pay best practices](https://docs.stripe.com/apple-pay/best-practices) — read 2026-10-19

### A device token can fail later merchant-initiated payments
- **[DOCS]** "By default, Apple Pay creates a Device Primary Account Number (DPAN), which is tied to a
  specific device. If a customer replaces their device or removes the card from it, the DPAN might no
  longer work. This doesn't affect one-time customer-initiated transactions (CIT), but it can cause
  failures for future merchant-initiated transactions (MIT)." Merchant tokens are for
  "Subscriptions … Automatic reloads … Deferred payments: Authorize payment at booking, then charge
  after you provide the service". "If Apple Pay and the card issuer support merchant tokens, Apple Pay
  returns an MPAN. Otherwise, it returns a DPAN."
  [Apple Pay merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens) — read 2026-10-19
- Carried over: Apple says an MPAN "cannot be used for unscheduled card on file (UCOF)", and the RN
  library offers no deferred request type —
  [`gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unscheduled-card-on-file`](gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unscheduled-card-on-file) (2026-10-08).

### Apple Pay in setup mode: Stripe documents a recurring summary item
- **[DOCS]** For setup with the Payment Sheet: "In accordance with Apple's guidelines for recurring
  payments, you must also set a `cardItems` that includes a `RecurringCartSummaryItem` with the amount
  you intend to charge … You can also adopt merchant tokens by setting the `request` with its `type`
  set to `PaymentRequestType.Recurring`."
  [Accept in-app payments (setup)](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup) — read 2026-10-19
- *Code:* `confirmPlatformPaySetupIntent` with one `Immediate` item of `0.00`, `isPending: true`, no
  `request` (`payments.tsx:359-370`); dormant while `APPLE_PAY_MERCHANT` is null (`:314-318`).

### The setup consumes the wallet's cryptogram; a saved Apple Pay card may not be used on-session
- **[DOCS]** "When a DPAN (or an MPAN) generates, it also comes with an expiring one-time use
  cryptogram … When the first CIT using the cryptogram fails, subsequent MITs using the same Card will
  likely also fail." "SetupIntent confirmation initiates the same CIT 0 USD validation to consume the
  cryptogram." "Apple Pay supports `usage=off_session` payments using DPANs (or MPANs) … However, they
  have a slightly higher risk because they don't get a liability shift from the network and might get
  lower authorization rates than average." **"Apple Pay terms forbid using a saved payment method for
  `usage=on_session` payments. If the customer is in the flow, you're required to have them authorize
  and generate a new cryptogram for that transaction."**
  [Manage recurring payments on Apple Pay](https://docs.stripe.com/apple-pay/apple-pay-recurring) — read 2026-10-19

---

## 5. Card updates and expiry

### Automatic card updates: what they need, and the two events
- **[DOCS]** "Stripe works with card networks and automatically attempts to update saved card details
  whenever a customer receives a new card … Automatic card updates require card issuers to
  participate … It's widely supported in the United States … International support varies from
  country to country. It isn't possible to identify cards that support automatic updates."
  "`payment_method.updated` … notifies you of updates to a card through an API call. The
  `payment_method.automatically_updated` event notifies you of automatic card updates from the
  network. These events include the card's new expiry date and last four digits … If the card update
  includes a new card number, the fingerprint changes."
  [How cards work](https://docs.stripe.com/payments/cards/overview) — read 2026-10-19
- Carried over: no Polish issuer's participation is documented —
  [`gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers`](gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers) (2026-10-08).
- *Code:* reads `payment_method.automatically_updated` on the platform endpoint, re-reads the card
  and records a change of brand or last four only (`backend/app/modules/payments/infrastructure/stripe_notices.py:106-113`;
  `backend/app/modules/payments/application/notices.py:129-142`; `payment_method.py:288-306`).

### Card updates on the platform are billed to the platform
- **[DOCS]** "Any activity occurring at the platform account level is billed to your platform
  regardless of the entity responsible for fee collection. For example, Stripe charges the platform
  directly for … card account updates for cards stored on your platform account." On a club account
  with `fees_collector = stripe`, "Card Account Updater", "Radar" and "3D Secure" are the connected
  account's. [Fee behaviour on connected accounts](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior) — read 2026-10-19
- This **corrects** the 2026-10-08 reading in
  [`gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers`](gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers)
  that any updater fee is the club's: Raketa stores the cards on the platform, so it is Raketa's.

### The expiry is on every card, and an updated card keeps working
- **[DOCS]** `card.exp_month`, `card.exp_year`: the card's expiry month and four-digit year.
  [API: The PaymentMethod object](https://docs.stripe.com/api/payment_methods/object) — read 2026-10-19
- **[DOCS]** "Updating a saved card can only change its name, billing address, expiry date, or
  metadata. To make any other changes, you must delete the card and create a new one … To let your
  customers manage their own payment methods, implement processes that allow them to manually update
  and replace their saved cards." [How cards work](https://docs.stripe.com/payments/cards/overview) — read 2026-10-19
- **[DOCS]** An expired card is declined with error code `expired_card` (test card
  4000 0000 0000 0069, `pm_card_chargeDeclinedExpiredCard`). [Testing](https://docs.stripe.com/testing) — read 2026-10-19
- *Code:* `card_of` reads brand, last four and wallet only; Raketa never reads or shows the expiry
  (`stripe_payments.py:145-157`).

---

## 6. Replacing and removing a card

### Detaching is permanent
- **[DOCS]** "Detachment is permanent and irreversible — once detached, a PaymentMethod can no longer
  be used for payments or re-attached to a Customer."
  [API: Detach a PaymentMethod](https://docs.stripe.com/api/payment_methods/detach) — read 2026-10-19
- *Code:* *Change* keeps the old card until the new one is saved, then detaches the old one after the
  commit; *Remove* is refused while there is a live yes or a booked game ahead, then detaches
  (`payment_method.py:236-286`; `backend/app/modules/payments/application/method.py:31-62`;
  `release_methods.py:33-47`; `stripe_payments.py:298-313`).

### A clone is not the platform card
- **[DOCS]** "The cloned PaymentMethod is an independent object with a unique ID. It isn't linked to,
  or kept in sync with, the PaymentMethod on your platform." "To update customer or payment method
  data, you only need to update the objects on your platform. You clone the PaymentMethod for each
  direct charge, which ensures that you always use the current platform version."
  [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-19
- So a hold already made on a club's account stands on its own clone when the player changes or
  removes the platform card; the next share is cloned from the new card.

---

## 7. Customers and payment methods across the platform and its clubs

### Save once on the platform, clone for each direct charge
- **[DOCS]** "When collecting payment details from your customer, set them up for future use and save
  them on your platform. You only need to set up each payment method once." To clone, "Specify the
  connected account ID as the Stripe account, and pass the IDs of the Customer and PaymentMethod saved
  on your platform" (`POST /v1/payment_methods` with `Stripe-Account`, `customer`, `payment_method`).
  "The cloned PaymentMethod … inherits the setup performed on your platform account, so you don't need
  to set it up again on the connected account."
  [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-19
- *Code:* one clone per share, keyed `{payment key}-clone`, then a manual-capture off-session
  PaymentIntent naming no customer (`stripe_payments.py:466-542`; `seat_charges.py:433-446`).

### What can be cloned, and where
- **[DOCS]** "Cloning supports PaymentMethods that have `type` set to either `card` or
  `us_bank_account`." "You can't clone payment methods from one connected account to another connected
  account. You can't clone payment methods from a connected account to a platform account."
  [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts),
  [Billing for a multi-entity business](https://docs.stripe.com/billing/multi-entity-business) — read 2026-10-19
- **[DOCS]** The older token-based cloning page is marked "**Deprecated** … a legacy feature. Support
  for it might end without notice." [Clone customer payment information](https://docs.stripe.com/connect/cloning-customers-across-accounts) — read 2026-10-19

### A clone attached to no customer is spent by one charge
- **[DOCS]** "Creating a charge with the cloned PaymentMethod consumes it, because it's not attached to
  a customer. However, consuming the clone doesn't affect the original PaymentMethod saved on your
  platform. You can't reuse the consumed clone, but you can clone the platform PaymentMethod again."
  Recurring charges need "a Customer object on the connected account" with the clone attached.
  [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-19
- **[ABSENT]** Whether a clone whose off-session attempt was refused still counts as unspent, so that
  the same PaymentIntent can be confirmed on-session with it: not on the cloning page, the RN
  recovery guide or the PaymentMethod reference — read 2026-10-19 (also open since
  [`local-market.md#one-saved-card-charged-on-each-clubs-account`](local-market.md#one-saved-card-charged-on-each-clubs-account), 2026-10-06).
  The demand that would prove it on the sandbox, `test_a_payment_its_player_confirmed_is_held_to_be_taken`,
  skips on Stripe ("needs a browser", `backend/tests/demands/test_payments_demands.py:125-126`, `:718-743`).

### A platform in another country may need `on_behalf_of` on the setup
- **[DOCS]** "If your platform is in a different country than your connected accounts, the setup
  performed on your platform might not be sufficient … To make sure that your setup meets the
  requirements of the connected account's country, you might need to use `on_behalf_of` to specify a
  connected account in that country." `on_behalf_of`: "The account (if any) for which the setup is
  intended." [Share payment methods across accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts),
  [API: The SetupIntent object](https://docs.stripe.com/api/setup_intents/object) — read 2026-10-19
- **[MEASURED]** The platform is `country: PL` and the test club `country: PL`
  ([`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account),
  [`…#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`](stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses)), and setups carry
  `on_behalf_of: null` (above) — same country, so the caution does not bite today.

### A direct charge follows the club's Radar rules, not Raketa's
- **[DOCS]** "With Connect, the rules you create only apply to payments created on the platform
  account. Payments created directly on the connected account are subject to the connected account's
  rules." [SCA for Connect platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms) — read 2026-10-19
- Raketa's clubs have the full Dashboard (`stripe_payments.py:317-347`), so a club can add rules that
  block or challenge Raketa's off-session holds on its own account.

### A clone on the test club
- **[MEASURED]** `stripe-club` · `GET /v1/payment_intents/pi_3USELx5y1DMwE3zY14aUf4wv?expand[]=payment_method&expand[]=latest_charge`
  · 2026-10-19: 40,00 zł, `requires_capture`, `customer: null`; its method `pm_1USELx5y1DMwE3zYfOuoVHa7`
  is `customer: null`, `allow_redisplay: unspecified`, Visa •••• 4242 `exp 10/2027`,
  `cvc_check: pass`, **`fingerprint: ZassUyymUdRzxwgI`**; the charge reads `network_transaction_id:
  909711511585121`, `network_token.used: false`, `three_d_secure: null`, `risk_level: normal`.
  On the platform the same test number reads `fingerprint: gjVniwT1NxRTIMol`
  (`pm_1USEM75y1DB8chHbfBXqHM9F`, above): a card's fingerprint differs between the platform and a club.

### A refused clone stays on the payment's last error
- **[MEASURED]** `stripe-club` · `GET /v1/payment_intents/pi_3USEMG5y1DMwE3zY0P5qCp1v` · 2026-10-19:
  40,00 zł, `requires_payment_method`, `payment_method: null`; `last_payment_error`: `card_declined`,
  `decline_code: generic_decline`, `network_decline_code: 01`, `advice_code: try_again_later`,
  `payment_method.id: pm_1USEMG5y1DMwE3zYNIEUACzA` (•••• 0341, `customer: null`). This is the id the
  app's *on file* recovery confirms with (`payments.tsx:399-409`).

---

## 8. Card testing on the save

### Card testers target the save, and a recommended integration brings Stripe's own controls
- **[DOCS]** "Card testers can use your publishable key … Endpoints targeted by card testers typically
  allow them to do one of the following: Save card. Make a payment." "If you use the latest Stripe
  Payment Element or Checkout, we have many automated and manual controls in place … rate limiters, AI
  models, CAPTCHA triggers." "If you can't use a recommended integration, include as much data as
  possible or implement your own controls": advanced fraud detection, "IP address, Customer email,
  Customer name, Billing address". Controls: require login, rate limits, "Limit the number of cards
  that can be added to an account". [Protect yourself from card testing](https://docs.stripe.com/disputes/prevention/card-testing) — read 2026-10-19
- *Code:* the setup needs a signed-in player and stops at 5 setups a day
  (`terms.py:27-32`, `payment_method.py:172-183`); the customer carries no email or name and the card
  no billing details (`stripe_payments.py:192-201`, `payments.tsx:284`).

### Whether the platform must be activated to save cards live
- **[ABSENT]** Whether a platform with `charges_enabled: false` (the sandbox platform's state,
  [`stripe-sandbox.md#the-platform-account`](stripe-sandbox.md#the-platform-account)) can confirm
  live SetupIntents for cards it never charges itself: not stated on the cloning, Connect or
  SetupIntent pages read above — read 2026-10-19. A question for Stripe support.

---

## Pitfalls

1. **Reusing a refused clone.** The recovery confirms the payment with
   `lastPaymentError.paymentMethod` — a clone on no customer, which one charge consumes; Stripe's
   sample reuses a customer-attached card. Undocumented, and the sandbox demand skips.
   ([cloning](https://docs.stripe.com/connect/direct-charges-multiple-accounts#clone-and-create-direct-charges),
   [RN recovery](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native))
2. **Charging after a brand change** — "you can't charge it for any MITs until you get a new
   cardholder agreement"; refreshing only last four misses it. ([CITs and MITs](https://docs.stripe.com/payments/cits-and-mits#card-brand-changes))
3. **Terms without timing and amount**, or a new terms version not re-asked before the next MIT.
   ([CITs and MITs](https://docs.stripe.com/payments/cits-and-mits#compliance))
4. **Cloning a detached card.** A fill that read the method before a *Change* committed and clones
   after the release asks Stripe for a detached card; the adapter raises an invalid request as a bug,
   not a refusal (*unverified*). ([detach](https://docs.stripe.com/api/payment_methods/detach))
5. **Apple Pay device tokens for later charges**: a DPAN "can cause failures for future
   merchant-initiated transactions"; setup mode wants a recurring item or merchant token; a saved Apple
   Pay card may not be reconfirmed on-session — what the *on file* recovery does.
   ([merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens), [recurring](https://docs.stripe.com/apple-pay/apple-pay-recurring))
6. **Google Pay e-commerce tokens** support "Neither liability shift nor 3D Secure" — a bank's-check
   recovery has nothing to draw. ([Google Pay](https://docs.stripe.com/google-pay?platform=react-native))
7. **Google Pay live on test settings**: production access ("Gateway"), a signed release build,
   `testEnv: false`; walks need a physical device and a real card. ([Google Pay](https://docs.stripe.com/google-pay?platform=react-native))
8. **An old SDK**: fixes ship only on the latest minor; 0.38.6 gets none. ([policy](https://docs.stripe.com/sdks/mobile-sdk-versioning))
9. **A cold start from the bank app** never handed to `handleURLCallback`.
   ([return URL](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup))
10. **Card testing on a bare integration**: Stripe's models rely on what the integration sends; no
    email, name or billing address gives them little. ([card testing](https://docs.stripe.com/disputes/prevention/card-testing))
11. **Assuming updates reach Polish cards**: coverage "varies from country to country"; an expired
    card is declined `expired_card` at the hold, days after the yes. ([cards overview](https://docs.stripe.com/payments/cards/overview))
12. **Assuming the club pays for card updates**: platform-saved cards are billed to the platform.
    ([fee behaviour](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior))
13. **The club's Radar rules** govern direct charges; a full-Dashboard club can block or challenge
    Raketa's holds. ([SCA for platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms))
14. **Cancelling a succeeded setup** is refused; its card stays attached unless detached.
    ([cancel](https://docs.stripe.com/api/setup_intents/cancel))
15. **Fingerprints differ between platform and club** (measured above): a club's Dashboard cannot be
    joined to Raketa's cards by fingerprint.

## Checks

1. Is every card saved by an `off_session` SetupIntent on the platform customer, only after the terms
   in force were accepted, with the acceptance recorded (version, time, the card it covered)?
2. Do the terms say who takes the money (the club where the game is played), when (fill, four days
   before the cut-off, cut-off), how much (court price ÷ players), and the leaving rule?
3. Before any hold without the player, is a changed brand or outdated terms version caught and the
   player asked again?
4. When an off-session hold needs the bank's check, can the player complete it on the same payment —
   proven on the sandbox with the clone, not only on the fake?
5. When a hold is declined, can the player pay it with another card, and do they know whether that
   card replaces the saved one?
6. Does *Change* keep the old card until the new one is saved, and detach it only when no share can
   still be cloned from it?
7. Is *Remove* refused while a live yes or a booked game ahead could still clone the card?
8. Is each share cloned once, from the current platform card, and never reused for a second payment?
9. Does a card the bank updated keep working untouched, and does a brand change ask for the terms?
10. Does the player learn that the saved card expires before a game's hold, or only from the decline?
11. Is a wallet offered only where it can be charged later: Google Pay after Google's review, Apple
    Pay with a merchant token or recurring item and never reconfirmed on-session?
12. Is the bank app's return handed to Stripe on a cold start as well as a warm one?
13. Is a setup's or refused payment's client secret given only to its player, when needed, never
    logged or stored?
14. Are setups limited per signed-in player per day, and does Stripe get enough about the player for
    its card-testing models?
15. Do card-update, setup 3D Secure and setup Radar costs sit with Raketa, and the club's own Radar and
    3D Secure with the club?
16. Is the React Native SDK on a minor version that still receives Stripe's fixes?
