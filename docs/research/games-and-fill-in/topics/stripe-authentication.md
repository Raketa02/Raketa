# Stripe — authentication (SCA and 3-D Secure)

Strong customer authentication and 3-D Secure **as this product uses Stripe**, read 2026-10-19 from
docs.stripe.com and the sandbox, against the code at `9ab0ea5b`.

**How the product uses Stripe.** A player is a v1 Customer on a Polish platform; the card is saved
once in an off-session SetupIntent the phone confirms. For each share it is cloned onto the club's
Polish Accounts v2 account and held there: `capture_method: manual`, `off_session: true`,
`confirm: true`, złoty (`backend/app/modules/payments/infrastructure/stripe_payments.py:203-222`,
`:466-542`). When the bank wants the player, they confirm that same payment on the phone with
`@stripe/stripe-react-native` 0.38.6 (`frontend_player/package.json:34`), started with the club's
account id (`frontend_player/src/shared/lib/platform/payments.tsx:388-414`).

**Sources.** Pages served in Spanish are quoted *(translated)*. The sandbox was read through `stripe`
(`acct_1US89K5y1DB8chHb`, test mode) and `stripe-club` (`acct_1US95f5y1DMwE3zY`); what
`stripe-sandbox.md` measured is cited, not redone. No write tool was used.

## 1. Where SCA applies to this product

### SCA applies to direct charges on an EEA club's account

[DOCS] https://docs.stripe.com/strong-customer-authentication/connect-platforms (read 2026-10-19):

- **Who must update.** "You need to update your platform if you create any of the following
  charges: Direct charges on a connected account based in the European Economic Area (EEA)."
- **When banks may decline.** "Transactions that don't follow the new authentication guidelines
  might be declined by a customer's bank".
- **Which payments.** SCA applies to "businesses based in the EEA that accept online payments from
  customers located in the EEA".

**Fit:** the platform and the club are both `country: PL` (`stripe-sandbox.md#the-platform-account`,
`#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`). So every
Polish-issued card a player saves is in scope.

### Saving the card is where SCA is met; later payments may still need the player

[DOCS] https://docs.stripe.com/strong-customer-authentication/connect-platforms (read 2026-10-19):

- **At saving.** "Under SCA, authentication is required when saving a card to collect customer
  permission and qualify for off-session exemptions for subsequent off-session payments."
- **Later.** "SCA requires off-session payments to be authenticated when customers enter payment
  details, and subsequent off-session payments might require notifying the customer to return to
  the application to re-authenticate."

[DOCS] https://docs.stripe.com/strong-customer-authentication (read 2026-10-19): "While some
low-risk transactions … don't require authentication, banks can still request that the customer
complete authentication … update your integration so your customers can complete authentication
when requested by the bank."

### Merchant-initiated payments: outside SCA, but only after an authenticated save and an agreement

[DOCS] https://docs.stripe.com/payments/3d-secure/strong-customer-authentication-exemptions (read
2026-10-19).

- **Merchant-initiated payments.** "Payments made with saved cards when the customer isn't present
  in the checkout flow (sometimes called 'off-session') might qualify as merchant-initiated
  transactions (MITs). These payments technically fall outside the scope of SCA. In practice,
  marking a payment as MIT is similar to requesting an exemption; neither a customer challenge nor a
  liability shift occurs. To use merchant-initiated transactions, you authenticate the card when
  it's being saved. You must also secure agreement from the customer (through a mandate) to charge
  their card at a later point."
- **Low value.** Applies to "amounts less than 30 EUR". "SCA might still be required by the issuer"
  once the cardholder's payments since their last authentication exceed "100 EUR", or after "five
  transactions".
- **Transaction risk analysis.** "EEA merchants have access to TRA exemptions for qualifying low
  risk transactions up to 250 EUR."
- **Liability.** "When the customer's bank approves an exemption request, liability shift for
  fraudulent transactions doesn't apply."

A share (40,00 zł in the walk's padel game) is well under 30 EUR. This matters only for the player's
own confirmation in the app; the club's holds are merchant-initiated.

### Who classifies a payment as merchant-initiated

[DOCS] https://docs.stripe.com/payments/cits-and-mits (read 2026-10-19): "An MIT is a transaction
that you initiate without direct participation of your customer, based on a prior agreement with
that customer authorizing you to store and use their credentials." Stripe and the networks classify
by signals, not by `off_session` alone; on the sandbox every off-session Visa hold got the
customer-initiated window (`stripe-sandbox.md#every-visa-hold-lasted-exactly-7-days`).

### Stripe can't be told to skip 3-D Secure

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (read 2026-10-19):

- **No switch to turn it off.** "You can't use Stripe APIs to manually turn off 3DS." and "Stripe's
  mandatory authentication rules run automatically, regardless of whether or not you manually
  request 3DS."
- **When Stripe triggers it.** "Stripe triggers 3DS automatically if mandated by regulations such as
  Strong Customer Authentication in Europe, … if requested by an issuer with a soft decline code,
  or if certain Stripe optimizations apply."
- **Payments that can't take it.** "not all transactions support 3DS, for example wallets or
  off-session payments."
- **What `request_three_d_secure` does.** `any` requests 3DS "with a preference for a
  `frictionless` flow", and `challenge` "with a preference for a `challenge` flow". "Stripe can't
  guarantee your preference because the issuer determines the ultimate authentication flow."

The code never sets the parameter. The sandbox shows `request_three_d_secure: automatic` on every
setup and payment (`stripe-sandbox.md#setup-intents-off-session-cards-only`; on
`pi_3USEMG5y1DMwE3zY0P5qCp1v` below).

### Whose Radar rules decide 3-D Secure: the platform's at saving, the club's at paying

[DOCS] https://docs.stripe.com/strong-customer-authentication/connect-platforms (read 2026-10-19):
"With Connect, the rules you create only apply to payments created on the platform account.
Payments created directly on the connected account are subject to the connected account's rules."

**Fit:**
- The SetupIntent lives on the platform, so Rakieta's Radar rules apply when a card is saved.
- Every share's PaymentIntent lives on the club's account. The club has the full Dashboard
  (`stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`),
  so its own rules apply there.

### Liability after 3-D Secure is expected, never guaranteed

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (read 2026-10-19): "Successful
3DS authentication doesn't guarantee liability shift. You can expect liability shift for
successfully authenticated payments that later receive eligible fraud disputes, but it isn't
guaranteed for any specific payment or dispute." And: "If you receive an inquiry for a
3D-Secure-authenticated charge, you *must* respond", or a "no-reply" chargeback "could invalidate
the liability shift".

**Fit:** holds made without the player are merchant-initiated, so no shift (§1). A payment the player
confirmed in the app is authenticated: a shift is expected, not guaranteed. The dispute lands on the
club's account (see `refunds-and-disputes`).

## 2. Saving the card: 3-D Secure at setup

### A SetupIntent authenticates the card and records the permission

- **[DOCS]** https://docs.stripe.com/payments/paymentintents/lifecycle (read 2026-10-19): "Setup
  Intents use 3DS to authenticate a payment method without making any charge and then create a
  mandate or agreement for future charges." *(translated)*
- **[DOCS]** https://docs.stripe.com/api/setup_intents/create (read 2026-10-19), `usage`:
  "`off_session` — Use `off_session` if your customer may or may not be in your checkout flow. …
  If not provided, this value defaults to `off_session`."
- **[DOCS]** https://docs.stripe.com/billing/subscriptions/deferred-payment (read 2026-10-19):
  "Authentication failures occur when Stripe is unable to authenticate your customer with their
  card issuer. When this happens, the `status` of the SetupIntent is set to `requires_action`."

**Code:** `usage: off_session` and `payment_method_types: ["card"]`, with no
`request_three_d_secure` (`stripe_payments.py:203-222`).

### The platform's setup carries to every clone on a club's account

[DOCS] https://docs.stripe.com/connect/direct-charges-multiple-accounts (read 2026-10-19):

- **Confirm on the client.** "Confirming on the client allows the customer to go through any flows
  required to set up their payment details for future use, such as authentication with 3D Secure."
- **The clone inherits the setup.** "The cloned PaymentMethod is an independent object with a unique
  ID. It isn't linked to, or kept in sync with, the PaymentMethod on your platform. However, the
  cloned PaymentMethod inherits the setup performed on your platform account, so you don't need to
  set it up again on the connected account."
- **When the countries differ.** "If your platform is in a different country than your connected
  accounts, the setup performed on your platform might not be sufficient … you might need to use
  `on_behalf_of`".

[DOCS] https://docs.stripe.com/strong-customer-authentication/connect-platforms (read 2026-10-19): "If
you clone saved payment methods to reuse across multiple connected accounts, sharing a payment
method with a connected account automatically shares customer permission as well. This allows the
platform to make off-session payments on any of their connected accounts without requiring the
customer to authenticate their payment method again."

**Fit:** the platform and every club are in Poland, so `on_behalf_of` isn't needed; the code sends
none. That the clone inherits the setup is **not proven on the sandbox**. The demand that would show
it, card `4000 0025 0000 3155`, skips (`stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser`).

### A setup waiting for the bank's check, as the sandbox holds it

[MEASURED] `stripe` · `GET /v1/setup_intents/seti_1USEMO5y1DB8chHbm8ytDD7X?expand[]=latest_attempt`
· 2026-10-19:

- `status: requires_action`, `usage: off_session`;
- `payment_method_options.card.request_three_d_secure: automatic`;
- `next_action.type: redirect_to_url`, with the `return_url` the demand passed
  (`https://rakieta.example/return`), because the demand confirmed on the server;
- its attempt `setatt_1USEMO5y1DB8chHbKmngZSIS` at `requires_action`, with
  `payment_method_details.card.three_d_secure: null`, since nobody answered the check;
- `mandate: null`.

The setup's client secret is in the reading; it is not copied here.

**What the code does with it:**
- **On the phone.** The SDK draws the bank's check itself. `confirmSetupIntent` runs with the card
  taken from Stripe's fields (`payments.tsx:345-386`).
- **On the server.** A setup at `requires_action` reads as `AUTHENTICATING`
  (`stripe_payments.py:260-272`). The confirmation answers 409 `payment_setup_not_finished` with
  that status (`backend/app/modules/payments/application/setup.py:207-225`;
  `backend/app/modules/payments/presentation/routes.py:139-166`).

### The setup's notice saves the card if the phone never reports back

**[DOCS]** https://docs.stripe.com/connect/direct-charges?platform=react-native (read 2026-10-19):
"Listen for these events rather than waiting for a callback from the client. On the client side,
the customer could close the browser window or quit the app before the callback executes."
*(translated)*

**Code:**
- **Read.** `setup_intent.succeeded` on the platform endpoint is read as *SetupSucceeded*
  (`backend/app/modules/payments/infrastructure/stripe_notices.py:102-105`).
- **Acted on.** It saves the card the same way the phone's confirmation does
  (`backend/app/modules/payments/application/notices.py:110`).
- **The bank's check at saving.** It is covered both ways, on the phone and by the notice.

### A changed card brand stops off-session payments until the player agrees again

[DOCS] https://docs.stripe.com/payments/cits-and-mits (read 2026-10-19):
- "When a card's brand changes, you must prompt the cardholder to update their payment method."
- "When a card's brand changes, you can't charge it for any MITs until you get a new cardholder
  agreement."
- "Identify card brand changes by listening for the `payment_method.automatically_updated` event
  and comparing the `brand` in `previous_attributes` with the `brand` in the associated `card`
  object."

**Code:** reads `payment_method.automatically_updated` (`stripe_notices.py:106-113`;
`notices.py:129`). It asks for the terms again (the PRD's story 128, the refusal `TERMS_NEEDED`).

## 3. Holding a share without the player

### An off-session payment that needs the player fails at once, with a 402

- **[DOCS]** https://docs.stripe.com/api/payment_intents/create (read 2026-10-19), `off_session`: "Set
  to `true` to indicate that the customer isn't in your checkout flow during this payment attempt
  and can't authenticate. … This parameter can only be used with `confirm=true`."
- **[DOCS]** https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native (read
  2026-10-19): "Set `off_session` to `true` … This causes the PaymentIntent to throw an error if
  authentication is required."
- **[DOCS]** https://docs.stripe.com/payments/save-and-reuse?payment-ui=embedded-components (read
  2026-10-19):
  - "If, during your checkout flow, a partner requests authentication, Stripe requests exemptions
    using customer information from a previous on-session transaction. If the conditions for
    exemption aren't met, the PaymentIntent might result in an error."
  - "If a payment attempt fails, the request also fails with a 402 HTTP status code, and the
    PaymentIntent status is `requires_payment_method`."
- **[DOCS]** https://docs.stripe.com/error-codes (read 2026-10-19), `authentication_required`: "The
  payment requires authentication to proceed. If your customer is off session, notify them to
  return to your application and complete the payment. If you specified the
  `error_on_requires_action` parameter, the customer should try another card that doesn't require
  authentication." *(translated)*

### A refused payment waits in `requires_payment_method`, its card on its last error

**Expected behaviour.** Stripe leaves a payment refused without its player in
`requires_payment_method`, not `requires_action` (the 402 fact above).

[MEASURED] `stripe-club` · `GET /v1/payment_intents/pi_3USEMG5y1DMwE3zY0P5qCp1v` · 2026-10-19. This
is the off-session refusal the demand made with `pm_card_chargeCustomerFail`, 40,00 zł:

- **The payment.** `status: requires_payment_method`, `payment_method: null`, `next_action: null`,
  `customer: null`, `setup_future_usage: null`.
- **Its last error.** `last_payment_error.type: card_error`, `code: card_declined`,
  `decline_code: generic_decline`, `advice_code: try_again_later`.
- **The card it tried.** `last_payment_error.payment_method` is the clone
  `pm_1USEMG5y1DMwE3zYNIEUACzA`: `customer: null`, `card.three_d_secure_usage.supported: true`,
  `checks.cvc_check: pass`, Visa •••• 0341, `country: US`.

So the clone the payment tried is readable only from `last_payment_error.payment_method`. The
payment's own `payment_method` is empty. **No payment refused for `authentication_required` exists
on the sandbox**, because every demand that would make one skips
(`stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser`).

### How the code reads a refusal, and what a later reading says

- **At the hold.** A `stripe.CardError` whose `code` is `authentication_required` is
  `AUTHENTICATION_REQUIRED`. Any other is `DECLINED`, with
  `error.decline_code or error.code` (`stripe_payments.py:519-541`).
- **When it is decided.** The reason is fixed at that moment, from the error (`seat_charges.py:173-178`,
  `:449`). The phone chooses its way through from it: `DECLINED` → another card, typed; anything
  else → the card on file with the bank's check
  (`frontend_player/src/features/payments/domain/seatCharge.ts:60-62`).
- **A later reading.** Reading the same payment again maps `requires_payment_method` to `DECLINED`
  (`stripe_payments.py:88`, `:614-635`). So a payment refused for the bank's check reads back as
  *declined*, with `decline_code` taken from the last error.
- **Notices.** The notices `payment_intent.payment_failed` and `.requires_action` are prompts only.
  A reading after them records nothing unless the payment is held, taken or cancelled
  (`backend/app/modules/payments/domain/seat_charge.py:812-829`).

### `authentication_required` is also an issuer's decline code

[DOCS] https://docs.stripe.com/declines/codes (read 2026-10-19) *(translated)*:

- **`authentication_required`.** "The card was declined because the transaction requires
  authentication, such as 3D Secure." Next steps: "When using Stripe's front ends, in most cases an
  issuer's soft decline triggers an authentication flow, letting the customer retry and
  authenticate their card. In some cases, such as off-session payments, you might have to ask the
  customer to retry. If the card issuer sends this decline code even though the transaction was
  successfully authenticated, the customer must contact their card issuer for more information."
- **`authentication_not_handled`.** "Related to `authentication_required`. The customer tried to
  continue without performing the required authentication, so the issuer declined the payment
  again." Next steps: "Run EMV 3D Secure (3DS) or strong customer authentication (SCA). For
  off-session payments, charge and set up authentication on-session first, and then return to
  on-session authentication if needed."

[DOCS] https://docs.stripe.com/payments/analytics/authentication (read 2026-10-19): "Bank request —
Payments where the customer's bank requests 3DS with the soft decline code
`authentication_required`."

[DOCS] https://support.stripe.com/questions/authenticated-payment-declined-with-an-authentication-required-decline-code
(read 2026-10-19, summarised by the fetch tool):
- **Why.** Issuers sometimes return the code on a payment that already passed 3-D Secure, "mostly …
  Mastercard-branded cards".
- **What to do.** The customer contacts the issuer or uses a different payment method.

### Each clone is used up by the payment it makes

[DOCS] https://docs.stripe.com/connect/direct-charges-multiple-accounts (read 2026-10-19): "Creating a
charge with the cloned PaymentMethod consumes it, because it's not attached to a customer. However,
consuming the clone doesn't affect the original PaymentMethod saved on your platform. You can't
reuse the consumed clone, but you can clone the platform PaymentMethod again and use the new clone
for another charge."

### Whether a clone used up by a failed attempt can confirm the same payment on-session

**[ABSENT] Not documented.**
- **Where we looked.** `direct-charges-multiple-accounts`; `save-and-reuse-cards-only?platform=react-native`;
  `error-codes` (`payment_method_unexpected_state`: "The state of the provided payment method isn't
  compatible with the operation you're trying to perform" *(translated)*); and a documentation
  search for a used-up payment method.
- **What Stripe's example does.** Its recovery confirms with `lastPaymentError.paymentMethod.id`,
  but it is written for a payment method attached to a Customer, never for a clone.
- **What this product does.** Its recovery for the bank's check is exactly that call on a clone
  (§4, *What the phone does*).
- **The open question.** Whether Stripe accepts it is untested.

### Wallet payments don't run 3-D Secure

[DOCS] https://docs.stripe.com/payments/analytics/authentication (read 2026-10-19): digital wallets
"use device-based authentication methods (such as biometrics) instead of 3DS". Off-session payments
can't run it either (§1, *Stripe can't be told to skip 3-D Secure*).

## 4. Bringing the player back

### Stripe's recovery: tell the player, then confirm the same payment with the same card

[DOCS] https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native (read
2026-10-19):

- **Tell the player.** "If the PaymentIntent has any other status, the payment did not succeed and
  the request fails. Notify the customer to return to your application (for example, by email, text
  message or push notification) to complete the payment. We recommend building a recovery flow in
  your app that shows why the payment initially failed and lets the customer retry."
  *(translated)*
- **Confirm the same payment.** "*confirm* the original, failed PaymentIntent by reusing its client
  secret instead of creating a new one."
- **With the same card.** "If the payment failed because authentication is required, retry with the
  existing PaymentMethod instead of creating a new one." *(translated)* The example code:
  `if (paymentIntent.lastPaymentError?.code === 'authentication_required') { … confirmPayment(paymentIntent.clientSecret, { paymentMethodType: 'Card', paymentMethodData: { paymentMethodId: paymentIntent.lastPaymentError?.paymentMethod.id } }) } else { // Collect a new PaymentMethod }`.

**Fit:** the product tells the player by push, email and in-app notice, as *Confirm your payment by
14:40 to keep your seat* or *Fix your card …*
(`backend/app/modules/payments/application/seat_charge_emails.py:166-200`). The player then confirms
the same payment (`payments.tsx:388-414`).

### What the phone does

`devicePayments.confirmPayment` (`payments.tsx:388-414`):

- **Start.** It starts the SDK with the platform's publishable key and the club's account id
  (`:220-230`).
- **With the card on file.** It reads the payment by its secret, takes
  `lastPaymentError.paymentMethod.id ?? paymentMethodId`, and confirms with that id.
- **With another card.** It confirms with whatever Stripe's card fields hold. That card pays this
  share only and isn't saved (`ConfirmPaymentSheet.tsx:24-29`).
- **What it answers.** One of `confirmed`, `cancelled`, `declined` or `failed`
  (`bankAnswerOf`, `:195-212`).
- **Where the secret comes from.** It is asked of the server for each press, never kept: the payment
  is read from Stripe while the charge `awaits_its_player`
  (`backend/app/modules/payments/application/seat_charges.py:808-866`).

### A direct charge is confirmed on the phone under the club's account id

[DOCS] https://docs.stripe.com/connect/direct-charges?platform=react-native (read 2026-10-19):

- **The setup it shows.** `<StripeProvider publishableKey='<<YOUR_PUBLISHABLE_KEY>>'
  stripeAccountId='{{CONNECTED_ACCOUNT_ID}}' urlScheme='your-url-scheme' // required for 3D Secure
  and bank redirects`.
- **Where the payment lives.** "Transaction objects such as `PaymentIntents` and `Charges` exist on
  the connected account, not on the platform."

**Code:** it starts once for each key-and-account pair, and the setup always starts again without
the account (`payments.tsx:214-230`). So a payment is never confirmed against the platform, nor a
setup against a club.

### The way back from the bank's own app

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (read 2026-10-19), React
Native: "To automatically dismiss the webview when authentication completes, configure a custom URL
scheme or universal link and set your scheme in the `urlScheme` parameter."

[DOCS] https://docs.stripe.com/connect/direct-charges?platform=react-native (read 2026-10-19), *Set up
a return URL (iOS only)*: "The customer may leave your app to authenticate (for example, in Safari
or their banking app). To let them return to your app automatically after authenticating, configure
a custom URL scheme and set up the app delegate to send the URL to the SDK. Stripe doesn't support
universal links." *(translated)* The two pages disagree about universal links; the product uses a
custom scheme.

**Code:**
- **The scheme.** `urlScheme: APP_SCHEME` (`'rakieta'`, `frontend_player/src/shared/config/appLinks.ts:25`).
- **Who passes the return to Stripe.** A `Linking` listener hands it to `handleURLCallback`, only
  while a confirmation runs (`payments.tsx:232-242`).
- **Any other time.** The router ignores an address it doesn't know.

### The bank's check may run for at least five minutes

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (read 2026-10-19):
- **The setting.** "You can use `timeout` to specify how much time the 3DS authentication process can
  elapse before timing out. This duration includes both network round trips and awaiting customer
  input, and must be at least 5 minutes."
- **On Android.** "A value less than 5 minutes results in an error."

**Code:** the app passes no `threeDSecureParams` (`payments.tsx:220-230`), so the SDK's default
applies (its value was not read: unverified). Time to pay is 30 minutes
(`backend/app/modules/proposals/application/time_to_pay.py:4-6`).

### What a confirmation does to the payment, step by step

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow (read 2026-10-19):

- **Waiting for the bank.** "When 3DS flow information is received from the issuer … The
  PaymentIntent transitions to a status of `requires_action`".
- **Authenticated.** "Stripe attempts the charge and the PaymentIntent transitions to a status of
  `processing`".
- **Failure.** "The PaymentIntent transitions to a status of `requires_payment_method`, indicating
  that you need to try a different payment method, or you can retry 3DS by reconfirming."
- **The end.** "The PaymentIntent transitions to one of the following statuses …: `succeeded`,
  `requires_capture`, or `requires_payment_method`."
- **What Stripe records.** "`three_d_secure.result` indicates the authentication outcome", on the
  charge's `payment_method_details.card`.
- **The sandbox's stand-in for the bank.** "When you build an integration with your test API keys,
  the authentication process displays a mock authentication page. On that page, you can either
  authorize or cancel the payment. … Clicking the **Failure** button simulates an unsuccessful
  attempt at authentication."

**Code:**
- **Asked of Stripe, not the phone.** The server takes the confirmation only from Stripe's reading:
  `requires_capture` → `AUTHORISED`, anything else → 409 `payment_not_confirmed` with the status
  (`seat_charges.py:768-805`).
- **What the player reads.** The phone says *Your bank hasn't confirmed it yet. Try again in a
  moment.* (`frontend_player/src/features/proposals/components/fillCopy.ts:126`).
- **The Dashboard.** It shows the waiting payment as *Incomplete* (`state.json` `stripe.dashboard`).

### A payment confirmed too many times is cancelled by Stripe

[DOCS] https://docs.stripe.com/payments/paymentintents/lifecycle (read 2026-10-19): "PaymentIntents
could also transition automatically to `canceled` if they're confirmed too many times."
*(translated)* The number is **[ABSENT]**: it is not on that page, the API reference or the
documentation search.

**Fit:**
- The spec writes "At most 8 retries" (`docs/specs/games-and-fill-in/the-mechanics.md`, *The fill*),
  without a source.
- The code puts no cap on the phone's presses.
- A cancellation that arrives as a notice closes a refused charge
  (`seat_charge.py:793-810`).

### Nothing documents how long a payment can wait for its player

**[ABSENT]** No expiry is documented for a PaymentIntent waiting in `requires_payment_method` or
`requires_action`.
- **Where we looked.** The lifecycle page lists cancellation by the integration and *confirmed too
  many times*, and nothing else. Nothing else turned up in the API reference for `create`, the 3-D
  Secure guide or the save-and-reuse guide.
- **What the code does.** It leaves a refused payment open on the club's account while the charge
  `awaits_its_player` (`seat_charge.py:496-499`). After the player's time runs out the payment
  stays *theirs to confirm while the seat is free*
  (`backend/app/modules/proposals/application/time_to_pay.py:14-23`, `:53-88`).

## 5. Testing authentication

### The 3-D Secure and authentication test cards

[DOCS] https://docs.stripe.com/testing, *Authentication and setup* (read 2026-10-19) *(translated)*:

| Card | PaymentMethod | What it does |
|---|---|---|
| 4000 0025 0000 3155 | `pm_card_authenticationRequiredOnSetup` | "requires authentication for off-session payments unless you set it up for future payments. After you set it up, off-session payments no longer require authentication. However, on-session payments with this card always require authentication." |
| 4000 0027 6000 3184 | `pm_card_authenticationRequired` | "requires authentication on every transaction, regardless of how it was set up." |
| 4000 0038 0000 0446 | `pm_card_authenticationRequiredSetupForOffSession` | "already set up for off-session use. It requires authentication for one-time and other on-session payments. However, all off-session payments succeed as if the card had been set up previously." |
| 4000 0082 6000 3178 | `pm_card_authenticationRequiredChargeDeclinedInsufficientFunds` | "requires authentication for one-time payments. All payments are declined with an `insufficient_funds` failure code even after being successfully authenticated or set up previously." |

[DOCS] https://docs.stripe.com/payments/3d-secure/authentication-flow, *Test the 3DS flow* (read
2026-10-19):

- **`4000000000003220`** (`pm_card_threeDSecure2Required`): "The payment must always complete 3DS2
  authentication to be successful."
- **`4000008400001629`** (`pm_card_threeDSecureRequiredChargeDeclined`): "3DS authentication is
  required, but payments will be declined with a `card_declined` failure code after authentication."
- **`4000000000003055`**: "3DS authentication can still be performed, but isn't required."
- **`4242424242424242`**: "This card supports 3DS, but it isn't enrolled in 3DS. This means that if
  your Radar rules request 3DS, the customer won't go through additional authentication."
- **React Native challenge screens** *(translated)*: `4000582600000094` out of band;
  `4000582600000045` one-time passcode; `4000582600000102` single select; `4000582600000110`
  multi-select. Each "3D Secure 2 authentication must be completed on all transactions."
- **Other test cards.** "All other Visa and Mastercard test cards don't require authentication from
  the card issuer."

No test card was found that answers `card_declined` with decline code `authentication_required`
(**[ABSENT]**, searched on the testing page). The page also notes *(translated)*: "3D Secure won't
redirect payments created directly in the Stripe Dashboard."

**Fit:** `state.json` `stripe.cards` matches these rows. The everyday 4242 never shows the bank's
check and is US-issued (`stripe-sandbox.md#setup-intents-off-session-cards-only`).

### What the sandbox has proven about authentication so far

[MEASURED] (`stripe-sandbox.md`, 2026-10-19): the four demands that need the bank's check skipped,
each leaving a setup at `requires_action` (`#four-demands-skipped-the-banks-check-needs-a-browser`);
no payment on the club's account used `pm_card_authenticationRequired`; every authorised charge
reads `three_d_secure: null`. So a hold refused for the bank's check, its reason, the player's
confirmation on a clone, its reading and the notice after it have never been seen on Stripe; each
rests on the docs above and on the fake.

### The fake guesses Stripe wrong at one point

**The fake.** A card set to *ask for the bank's check every time* leaves the payment at
`AUTHENTICATION_REQUIRED` (`backend/app/modules/payments/infrastructure/fake_payments.py:866-868`),
announced as `payment_intent.requires_action` (`:150-157`); a later reading says *the bank's check*.
**Stripe** leaves `requires_payment_method` (§3, the 402 fact), which the adapter reads back as
`DECLINED` (`stripe_payments.py:88`), and by its docs the event is `payment_intent.payment_failed`
([DOCS] https://docs.stripe.com/payments/payment-methods, read 2026-10-19: "The payment failed. —
Send an email or push notification to request another payment method."); not seen on the sandbox
(unverified). **Effect today:** none found, since the reason is fixed at the hold and later readings
record only held, taken or cancelled (§3). Code that ever derives the reason from a reading will
pass on the fake and fail on Stripe.

## Pitfalls

Seeds for the Breakers: what goes wrong, and the Stripe source that says so.

1. **Waiting for `requires_action` after an off-session refusal.** Stripe answers a 402 and leaves
   the payment in `requires_payment_method`; a prompt keyed on `requires_action` never fires
   (https://docs.stripe.com/payments/save-and-reuse?payment-ui=embedded-components). The product
   fixes the reason from the error at the hold (§3); the fake models it the other way (§5).
2. **Reading the refusal from `code` only.** An issuer can soft-decline with `card_declined` and
   decline code `authentication_required` or `authentication_not_handled`
   (https://docs.stripe.com/declines/codes). The code calls only `code == "authentication_required"`
   the bank's check (`stripe_payments.py:519-541`), so such a refusal sends the player to type
   *another card* where Stripe says to retry with authentication. No test card produces it.
3. **Confirming the same payment with a clone it already used up.** A charge consumes a clone and a
   consumed clone "can't" be reused (https://docs.stripe.com/connect/direct-charges-multiple-accounts);
   whether it may still confirm the payment it failed on is undocumented (§3). If Stripe refuses,
   every recovery from the bank's check fails with a non-card error (`failed` on the phone), and for
   that refusal the phone never offers another card (`seatCharge.ts:60-62`).
4. **Trusting the phone's callback after the bank's own app.** Stripe says to act on events, since
   the app can close first (https://docs.stripe.com/connect/direct-charges?platform=react-native).
   If the app dies in the bank's app, the return reaches no listener (`payments.tsx:232-242`) and
   `/confirmation` is never sent. The notice can still record the hold (`seat_charge.py:812-822`),
   but only that request says the yes (`backend/app/modules/proposals/presentation/routes.py:375-432`):
   money may sit held on the club's account with no seat behind it (read from the code, not run:
   suspected).
5. **Testing with 4242 only.** It "isn't enrolled in 3DS" and is US-issued
   (https://docs.stripe.com/payments/3d-secure/authentication-flow); every provider demand for the
   bank's check skips on the sandbox. A walk must type 3155 or 3184 on a phone.
6. **Promising the bank's check runs "only if my bank asks" (PRD story 124).** Under SCA
   "authentication is required when saving a card" for off-session use
   (https://docs.stripe.com/strong-customer-authentication/connect-platforms): most Polish cards go
   through 3-D Secure at setup, frictionless or challenged, as the issuer decides.
7. **Expecting no further authentication after the setup.** "subsequent off-session payments might
   require notifying the customer to return … to re-authenticate" (same page). A share whose hold
   doesn't reach the cut-off makes two off-session payments for one game — the card check at the
   fill and the holding four days before the cut-off — and either can come back wanting the player.
8. **Re-trying a refused card off-session again and again.** `card_decline_rate_limit_exceeded`:
   "This card has been declined too many times. You can try charging this card again after 24
   hours." *(translated)* (https://docs.stripe.com/error-codes). A 3184-like card fails at every
   fill, check and holding it meets.
9. **Confirming the same payment too many times.** Stripe cancels a payment "confirmed too many
   times", number unstated (https://docs.stripe.com/payments/paymentintents/lifecycle). Repeated
   presses, or a typed card declining again and again, can lose the payment; the server then has
   nothing to hand the phone.
10. **Charging off-session after a card-brand change.** "you can't charge it for any MITs until you
    get a new cardholder agreement" (https://docs.stripe.com/payments/cits-and-mits).
11. **Expecting liability shift on holds made without the player.** "neither a customer challenge
    nor a liability shift occurs" for MIT
    (https://docs.stripe.com/payments/3d-secure/strong-customer-authentication-exemptions); after
    3-D Secure a shift is "expected … but it isn't guaranteed"
    (https://docs.stripe.com/payments/3d-secure/authentication-flow).
12. **Forgetting whose Radar rules apply.** Direct charges "are subject to the connected account's
    rules" (https://docs.stripe.com/strong-customer-authentication/connect-platforms): a club with
    the full Dashboard can add rules that block or challenge Rakieta's holds; the platform's rules
    govern only the setup.
13. **A deadline shorter than the bank's check.** The 3-D Secure timeout "must be at least 5
    minutes" (https://docs.stripe.com/payments/3d-secure/authentication-flow), and a bank's own app
    can take longer. Time to pay is 30 minutes: a check started at minute 28 can finish after the
    seat reopened, arriving as a late yes
    (`backend/app/modules/proposals/application/answers.py:242-330`).

## Checks

Questions a grader asks of a product rule here.

1. Is the card saved with a SetupIntent for off-session use, confirmed by the player on the phone so
   the bank can check it, before any off-session hold?
2. Is every hold made `off_session: true`, `confirm: true`, on a clone of the setup's card, so Stripe
   can claim the merchant-initiated exemption?
3. When a hold comes back `authentication_required`, is the player told (push, email, in-app), with
   the deadline, and led to confirm **the same** payment?
4. Is the refusal's reason read from both `code` and `decline_code` (`authentication_required`,
   `authentication_not_handled`), so a soft decline gets the bank's check, not *another card*?
5. Does the phone confirm on the club's account (`stripeAccountId`) with the card the payment last
   tried (`last_payment_error.payment_method.id`)?
6. Has confirming a refused payment on a **clone** been seen to work on the sandbox (4000 0027 6000
   3184 typed on a phone)? If not, is the rule graded on Stripe's docs and the fake only, and does it
   say so?
7. Is the confirmation recorded only from Stripe's own reading (`requires_capture`), never the
   phone's word?
8. If the player passes the bank's check but the app never reports back, does the product act on
   Stripe's notice — and does the seat follow the money, or is a share held with no seat?
9. Does the iOS app hand the bank app's return to Stripe (`urlScheme`, `handleURLCallback`), also
   after a cold start?
10. Do *time to pay* and *time to fix the card* leave room for a bank's check of five minutes or
    more, and say what happens to one finished after the deadline?
11. Is a payment that waits for its player closed when its seat or game is gone — or, left
    confirmable, is a late confirmation let go at once?
12. Can repeated presses get the payment cancelled at Stripe, and is the player then told something
    true?
13. Does a changed card brand stop every off-session hold until the player agrees again?
14. Does a story about the bank's check use a card enrolled in 3-D Secure (3155, 3184, 3220,
    4000 5826 0000 0045), never 4242?
15. Who bears a fraud dispute: no liability shift on a hold made without the player, a shift
    expected but not guaranteed on one the player confirmed — and does the rule name the club as the
    one who answers?
16. Does a game held in two steps (card check, then holding) expect that either step may need the
    player, and give each its own way back?
