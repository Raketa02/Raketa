# Stripe testing — cards, IBANs, Dashboard labels, the CLI and sandboxes

What Stripe documents for testing **this product's** money on a sandbox, read 2026-10-19 from docs.stripe.com
(`?locale=en-GB` where the plain URL came in Spanish) and the two servers (`stripe` = platform, `stripe-club` = the
test club `acct_1US95f5y1DMwE3zY`), against the code at `9ab0ea5b`: a card typed into Stripe's `CardField`, saved on
the platform; each share a manual-capture, off-session **direct charge** on the club's v2 account, in złoty.

Covered elsewhere, cited by anchor: what the sandbox holds
([`stripe-sandbox.md`](stripe-sandbox.md)); `stripe listen`'s one secret and the two scopes
([`stripe-webhooks.md#on-a-laptop-stripe-listen-one-secret-for-both-kept-across-restarts`](stripe-webhooks.md#on-a-laptop-stripe-listen-one-secret-for-both-kept-across-restarts));
no test card or clock shortens a hold
([`stripe-holds-and-capture.md#nothing-in-test-mode-shortens-a-hold-or-moves-its-clock`](stripe-holds-and-capture.md#nothing-in-test-mode-shortens-a-hold-or-moves-its-clock));
general vs test-mode sandbox settings
([`stripe-security.md#general-sandboxes-isolate-settings-the-test-mode-sandbox-shares-some-with-live`](stripe-security.md#general-sandboxes-isolate-settings-the-test-mode-sandbox-shares-some-with-live));
Apple Pay's merchant ID and real card
([`stripe-saving-cards.md#apple-pay-a-merchant-id-a-stripe-certificate-a-real-card-even-in-test-mode`](stripe-saving-cards.md#apple-pay-a-merchant-id-a-stripe-certificate-a-real-card-even-in-test-mode)).

---

## 1. Typing a test card on the phone

### Any future expiry, any CVC, any value elsewhere

- **[DOCS]** "When testing interactively, use a card number, such as 4242 4242 4242 4242. Enter the card number in the
  Dashboard or in any payment form. Use a valid future date, such as **12/34**. Use any three-digit CVC (four digits
  for American Express cards). Use any value you like for other form fields."
  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- **[DOCS]** "Test card numbers are only valid in sandboxes. Don't use them for real payments."
  [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19

### Never a real card in a sandbox — except inside a wallet

- **[DOCS]** Requirement: "Don't use real card details. The Stripe Services Agreement prohibits testing in live mode
  using real payment method details. Use your test API keys and the card numbers below."
  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- **[DOCS]** Wallets are the exception: "Apple Pay Wallet can't save Stripe test card information. Instead, Stripe
  recognizes when you're using your test API keys and provides a successful test card token for you to use. This
  allows you to make test payments using a live card without any charges being applied."
  [Cartes Bancaires](https://docs.stripe.com/payments/cartes-bancaires?platform=web) — 2026-10-19. Google Pay: §9.

### The phone saves through `createPaymentMethod` then `confirmSetupIntent` on the platform

- Code: the typed card becomes a PaymentMethod (`createPaymentMethod`, `frontend_player/src/shared/lib/platform/payments.tsx:337`)
  and the setup is confirmed with it (`:376-380`); a refused share is confirmed on the club's account with a typed card
  (`:393-397`) or the card on file (`lastPaymentError.paymentMethod`, `:399-409`). So a test card's *attach* behaviour
  decides the save, and its *charge* behaviour decides every later hold.

---

## 2. Cards that decline

### A card that simulates an issuer decline cannot be saved; 0341 saves and then fails

- **[DOCS]** "You can't attach cards that simulate issuer declines to a `Customer` object. To simulate a declined
  payment with an attached card, use the 'Decline after attaching' test card." 4000 0000 0000 0341: "Attaching this
  card to a Customer object succeeds, but attempts to charge the customer fail." (`pm_card_chargeCustomerFail`)
  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- **[MEASURED]** 0341's clone on the club, `pi_3USEMG5y1DMwE3zY0P5qCp1v`: `requires_payment_method`, `card_declined`,
  `generic_decline` — [`stripe-sandbox.md#a-card-refused-off-session-decline-code-and-advice`](stripe-sandbox.md#a-card-refused-off-session-decline-code-and-advice).

### The decline cards, by reason

- **[DOCS]** Each fails with `card_declined` and the decline code shown, or with the error code alone
  ([Testing](https://docs.stripe.com/testing), 2026-10-19):

| Card | PaymentMethod | Code |
|---|---|---|
| 4000 0000 0000 0002 | `pm_card_visa_chargeDeclined` | `generic_decline` |
| 4000 0000 0000 9995 | `pm_card_visa_chargeDeclinedInsufficientFunds` | `insufficient_funds` |
| 4000 0000 0000 9987 | `pm_card_visa_chargeDeclinedLostCard` | `lost_card` |
| 4000 0000 0000 9979 | `pm_card_visa_chargeDeclinedStolenCard` | `stolen_card` |
| 4000 0000 0000 0069 | `pm_card_chargeDeclinedExpiredCard` | `expired_card` (error code) |
| 4000 0000 0000 0127 | `pm_card_chargeDeclinedIncorrectCvc` | `incorrect_cvc` |
| 4000 0000 0000 0119 | `pm_card_chargeDeclinedProcessingError` | `processing_error` |
| 4242 4242 4242 4241 | — | `incorrect_number` |
| 4000 0000 0000 6975 | `pm_card_visa_chargeDeclinedVelocityLimitExceeded` | `card_velocity_exceeded` |

- On the phone all of these are refused **while saving**; the player reads one sentence whatever the reason —
  "Your bank declined this card, so nothing is saved. Try another one."
  (`frontend_player/src/features/payments/components/paymentsCopy.ts:164`). A refused share reads one of three fixed
  lines (`frontend_player/src/features/proposals/components/fillCopy.ts:85-89`). The reason is kept as `decline_code`
  (`backend/app/modules/payments/domain/provider.py:129`, `stripe_payments.py:519-541`) and shown nowhere to a person.

### Radar's test cards

- **[DOCS]** 4100 0000 0000 0019 (`pm_card_radarBlock`): "Radar always blocks it"; 4000 0000 0000 4954: highest risk,
  "Radar might block it depending on your settings"; 4000 0000 0000 9235: elevated risk, may be queued for review.
  "No matter which version of Radar you use, it might block a charge … The response is the same as what you get when a
  charge fails." [Testing](https://docs.stripe.com/testing?locale=en-GB);
  [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19
- On a direct charge the club's Radar rules run, not Raketa's —
  [`stripe-saving-cards.md#a-direct-charge-follows-the-clubs-radar-rules-not-raketas`](stripe-saving-cards.md#a-direct-charge-follows-the-clubs-radar-rules-not-raketas).

---

## 3. The bank's check (3D Secure)

### The four authentication-and-setup cards

- **[DOCS]** ([Testing](https://docs.stripe.com/testing?locale=en-GB), 2026-10-19)
  - 4000 0025 0000 3155 (`pm_card_authenticationRequiredOnSetup`): "requires authentication for off-session payments
    unless you set it up for future payments. After you set it up, off-session payments no longer require
    authentication. However, on-session payments with this card always require authentication."
  - 4000 0027 6000 3184 (`pm_card_authenticationRequired`): "requires authentication on all transactions, regardless
    of how the card is set up."
  - 4000 0038 0000 0446 (`pm_card_authenticationRequiredSetupForOffSession`): "already set up for off-session use. It
    requires authentication for one-time and other on-session payments. However, all off-session payments succeed as
    if the card has been previously set up."
  - 4000 0082 6000 3178: "requires authentication for one-time payments. All payments are declined with an
    `insufficient_funds` failure code even after being successfully authenticated or previously set up."

### Cards that require, support or refuse 3D Secure

- **[DOCS]** 4000 0000 0000 3220 (IE) and 4000 0084 0000 0027 (US): 3DS "must be completed for the payment to be
  successful"; 4000 0084 0000 1629: "required, but payments are declined with a `card_declined` failure code after
  authentication"; 4000 0084 0000 1280: the 3DS lookup fails, "Payments will be declined with a `card_declined`";
  4000 0000 0000 3055: supported, not required; 4242 4242 4242 4242: "supported … but the card is not enrolled";
  3782 822463 10005 (Amex): not supported, "proceeds without performing authentication"; 4000 0000 3220 0000:
  required on all transactions, completed "frictionless". [Testing](https://docs.stripe.com/testing) — 2026-10-19

### The phone's challenge screens

- **[DOCS]** For React Native, "pick a test card to trigger a specific challenge flow": 4000 5826 0000 0094 Out of
  Band, 4000 5826 0000 0045 One Time Passcode, 4000 5826 0000 0102 Single Select, 4000 5826 0000 0110 Multi Select —
  each "3D Secure 2 authentication must be completed on all transactions". "All other Visa and Mastercard test cards
  don't require authentication from the customer's card issuer."
  [3D Secure authentication flow](https://docs.stripe.com/payments/3d-secure/authentication-flow?locale=en-GB) — 2026-10-19
- **[DOCS]** "These cards only trigger special behaviour in mobile payments, not in browser forms or API calls."
  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19

### The mock check: authorise, or press Failure

- **[DOCS]** "With your test API keys, the authentication process displays a mock authentication page. On that page,
  you can either authorise or cancel the payment. Authorising the payment simulates successful authentication …
  Clicking the **Failure** button simulates an unsuccessful attempt at authentication."
  [3D Secure authentication flow](https://docs.stripe.com/payments/3d-secure/authentication-flow?locale=en-GB) — 2026-10-19
- **[DOCS]** A failed check leaves the PaymentIntent at `requires_payment_method`; "you can retry 3DS by
  reconfirming". The React Native `timeout` "must be at least 5 minutes". Same page — 2026-10-19
- **[ABSENT]** The exact button words drawn on an Android or iOS phone for each challenge flow — not on the testing or
  3DS pages (looked 2026-10-19). The walker writes them down on the first walk.

### A payment made in the Dashboard never asks for the check

- **[DOCS]** "3D Secure redirects won't occur for payments created directly in the Stripe Dashboard. Instead, use your
  integration's own front end or an API call." [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19

### On the sandbox the confirm-your-payment path has never run

- **[MEASURED]** The four demands that need the bank's check skip and leave their setups at `requires_action`; no
  payment on the club has ever been made with 3184 —
  [`stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser`](stripe-sandbox.md#four-demands-skipped-the-banks-check-needs-a-browser).
  Whether 3155's "set up" status survives the clone onto the club's account is therefore unmeasured.

---

## 4. Cards by country and brand — and the fee they cost

### A Polish Visa exists: 4000 0061 6000 0005

- **[DOCS]** "Poland (PL) · 4000006160000005 · Visa"; `pm_card_pl`; `tok_pl`. Other EEA Visas follow the same pattern
  (DE 4000 0027 6000 0016, FR 4000 0025 0000 0003, ES 4000 0072 4000 0007, IE 4000 0037 2000 0005); no EEA
  Mastercard is listed (GB 5555 5582 6555 4449 is the only European Mastercard row).
  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- This corrects [`stripe-sandbox.md#differences`](stripe-sandbox.md#differences) D5, which found no Polish-issued test
  card. The fee Stripe keeps on it is not yet measured; 4242 is US-issued and cost 2,30 zł on 40 zł
  ([`stripe-sandbox.md#stripes-fee-on-a-share-230-zł-on-40-zł-with-stripes-us-test-card`](stripe-sandbox.md#stripes-fee-on-a-share-230-zł-on-40-zł-with-stripes-us-test-card)).

### The brand cards

- **[DOCS]** Visa 4242 4242 4242 4242; Visa debit 4000 0566 5566 5556; Mastercard 5555 5555 5555 4444; Mastercard
  2-series 2223 0031 2200 3222; Mastercard debit 5200 8282 8282 8210; Mastercard prepaid 5105 1051 0510 5100 —
  "Any 3 digits · Any future date". [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19

---

## 5. Money that moves after the fact

### Only two cards make a refund change later

- **[DOCS]** "In live mode, refunds are asynchronous: a refund can appear to succeed and later fail, or can appear as
  `pending` at first and later succeed. To simulate refunds with those behaviours, use the test cards in this section.
  With all other test cards, refunds succeed immediately and don't change status after that."
  - 4000 0000 0000 7726 (`pm_card_pendingRefund`): "If you initiate a refund, its status begins as `pending`. Some
    time later, its status transitions to `succeeded` and sends a `refund.updated` event."
  - 4000 0000 0000 5126 (`pm_card_refundFail`): "its status begins as `succeeded`. Some time later, its status
    transitions to `failed` and sends a `refund.failed` event."

  [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- Both save normally (they only change the refund), so a player can type either on the phone. The product records a
  refund as given whatever status Stripe answered and reads no refund event
  ([`stripe-sandbox.md#differences`](stripe-sandbox.md#differences) D6).

### Why a refund fails, and what Stripe then asks of the seller

- **[DOCS]** `failure_reason`: `charge_for_pending_refund_disputed`, `declined`, `expired_or_canceled_card`,
  `insufficient_funds` ("Refund is pending due to insufficient funds and has crossed the pending refund expiration
  window"), `lost_or_stolen_card`, `merchant_request`, `unknown`. Requirement: "you need to arrange an alternative way
  to provide your customer with a refund." Some refunds made "shortly after the original charge" are reversals; the
  Dashboard shows it under the payment's Timeline → **View Details**. [Refunds](https://docs.stripe.com/refunds) — 2026-10-19

### The dispute cards, and how to win or lose one

- **[DOCS]** "With default account settings, charge succeeds, only to be disputed as …": 4000 0000 0000 0259
  fraudulent ("protected after 3D Secure authentication"); 4000 0000 0000 2685 product not received ("isn't
  protected"); 4000 0000 0000 1976 enquiry; 4000 0000 0000 5423 early fraud warning only; 4000 0004 0400 0079
  multiple disputes. [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- **[DOCS]** "If you respond in the Dashboard … enter the value from the table in the **Additional information**
  field. Then, click **Submit evidence**": `winning_evidence` "Closes the dispute as won and credits your account for
  the amount of the charge and related fees"; `losing_evidence` "Closes the dispute as lost without crediting your
  account"; `escalate_inquiry_evidence` turns an enquiry into a chargeback. [Testing](https://docs.stripe.com/testing) — 2026-10-19

### What a test dispute does to the money and the Dashboard

- **[DOCS]** Disputed: "The charge appears as **Disputed** in the Dashboard under Payments. Stripe debits the charge
  amount plus the dispute fee from the balance, creates a `Dispute` … `charge.dispute.created`", status
  `needs_response`; an enquiry `warning_needs_response`, "no funds are withdrawn unless we elevate an enquiry";
  closed as `won`, `lost` or `warning_closed` with `charge.dispute.closed`. "This is an asynchronous outcome."
  [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19
- **[DOCS]** Disputes are listed on the **Disputes** tab; the Dashboard's evidence statuses are `Needs response`,
  `Under review`, `Won`, `Lost`. [Respond to disputes](https://docs.stripe.com/disputes/responding);
  [Disputes analytics](https://docs.stripe.com/payments/analytics/disputes) — 2026-10-19
- **[ABSENT]** Whether a dispute card disputes a manual-capture payment while it is only held, or only once taken —
  not on the testing, disputes or 3DS pages (searched 2026-10-19).
- **[MEASURED]** `stripe-club` · `GET /v1/disputes` → empty · 2026-10-19: no dispute has ever been made on the test
  club, and the code subscribes to no `charge.dispute.*` event
  ([`stripe-webhooks.md#disputes-on-a-direct-charge`](stripe-webhooks.md#disputes-on-a-direct-charge)).

### Cards that put the money straight into the available balance

- **[DOCS]** "Other test cards send funds from a successful payment to your pending balance." 4000 0000 0000 0077
  (`pm_card_bypassPending`): "The US charge succeeds. Funds are added directly to your available balance, bypassing
  your pending balance." 4000 0037 2000 0278 (`pm_card_bypassPendingInternational`): "The international charge
  succeeds …" [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19
- **[DOCS]** "Test transactions settle instantly and are added to your available test balance" is written under bank
  debits (after the microdeposit table, before SEPA Direct Debit), not cards. Same page — 2026-10-19
- **[MEASURED]** Card shares on the club stay pending 7 days (`available_on` = capture + 7 days); balance now
  available 0,00 zł, pending 266,16 zł · `stripe-club` `GET /v1/balance` · 2026-10-19.
- Unmeasured: whether the bypass cards keep that behaviour on a clone charged on the club's account.

---

## 6. The club's account: onboarding values, payout IBANs, blocks

### Test values for the club's hosted onboarding

- **[DOCS]** ([Testing Connect](https://docs.stripe.com/connect/testing?locale=en-GB), 2026-10-19)
  - phone `0000000000` "Successful validation"; "Use `000-000` as the SMS code when prompted for test accounts";
  - date of birth `1901-01-01` "Successful date of birth match. Any other DOB results in a no-match"; `1900-01-01`
    "Triggers an OFAC alert";
  - address line 1 `address_full_match` (with a real city and postal code); `address_no_match` etc. fail;
  - personal ID `000000000` match, `111111111` mismatch; company tax ID `000000000` success, `000000004` inactive,
    `111111111` mismatch;
  - business URL `https://accessible.stripe.com` "successful validation"; `https://inactivity.stripe.com` pauses
    verification;
  - documents: `file_identity_document_success` / `_failure` or the success/failed images; "Test images override
    test ID numbers"; document tokens "may sit in `pending_verification`".
- **[MEASURED]** The test club was onboarded with exactly these: `support_phone +48000000000`,
  `url https://accessible.stripe.com`, address `address_full_match`, krakow 31-465, MCC 7299, `tax_id_provided`,
  requirements and `eventually_due` empty · `stripe` `GET /v1/accounts/acct_1US95f5y1DMwE3zY` · 2026-10-19.
- **[ABSENT]** A Polish REGON test value, and any "skip" or "use test data" button in hosted onboarding for a v2
  merchant account — the page offers force-skip only for the OAuth test client ("Stripe Dashboard accounts only")
  (looked 2026-10-19).

### The Polish payout IBANs: one succeeds, five fail

- **[DOCS]** ([Payouts](https://docs.stripe.com/payouts?locale=en-GB);
  [Testing Connect](https://docs.stripe.com/connect/testing), 2026-10-19)

| IBAN | Outcome |
|---|---|
| PL61109010140000071219812874 | Payout succeeds |
| PL62370400440532013001 | fails `no_account` |
| PL89370400440532013002 | fails `account_closed` |
| PL89370400440532013003 | fails `insufficient_funds` |
| PL89370400440532013004 | fails `debit_not_authorized` |
| PL89370400440532013005 | fails `invalid_currency` |

- **[DOCS]** "Test payouts simulate a live payout but aren't processed with the bank. Test accounts with Stripe
  Dashboard access always have payouts enabled, as long as valid external bank information and other relevant
  conditions are met, and never requires real identity verification." "You can't use test bank and debit card numbers
  in the Stripe Dashboard on a live mode connected account." Same pages — 2026-10-19
- **[ABSENT]** When a test payout turns `paid` or `failed`, and whether automatic test payouts are created on schedule
  — not on the payouts or Connect testing pages (looked 2026-10-19).

### Payout timing in Poland

- **[DOCS]** "First payout: After you successfully receive your first live payment, Stripe typically schedules your
  initial payout to complete within 7–14 days". Poland: initial settlement "7 calendar days", default "3 business
  days", minimum payout 5 PLN. [Payouts](https://docs.stripe.com/payouts?locale=en-GB) — 2026-10-19
- **[DOCS]** On a full-Dashboard account the platform may schedule or make payouts only after configuring Platform
  controls; payouts send v1 events only. [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — 2026-10-19

### Cards that block a club's charges or payouts

- **[DOCS]** "For the trigger actions to work, you must use these cards with a Connect charge by setting
  `on_behalf_of` or creating a direct charge on the connected account. The connected account must have an
  eventually_due requirement." 4000 0000 0000 4202 "Changes the next set of eventually due requirements to currently
  due"; 4000 0000 0000 4210 "Triggers a charge block"; 4000 0000 0000 4236 "Triggers a payout block". "These cards
  disable the connected account and move any currently due requirements to overdue. These cards have no effect until an
  account provides the initial information that's required to enable charges and payouts."
  [Testing Connect](https://docs.stripe.com/connect/testing?locale=en-GB) — 2026-10-19
- **[MEASURED]** The test club has no `eventually_due` requirement (above), so these cards would do nothing on it; a
  walk club's must be read first.

### A club cannot bring its own sandbox

- **[DOCS]** "You can't create connections between a Connect platform's sandbox and connected account sandboxes."
  [Sandboxes](https://docs.stripe.com/sandboxes) — 2026-10-19. A walk club is opened inside the platform's sandbox by
  the product's Connect with Stripe.

---

## 7. Where the walker sees each object

### The Payments page summarises; Workbench gives the exact state

- **[DOCS]** "The Payments page in the Dashboard shows a payment status … This status summarizes the payment but
  doesn't include the additional details provided by the PaymentIntent status." Mapping: `requires_payment_method` →
  **Incomplete** ("Typically occurs if there's no `latest_charge` … can also be **Partially paid**, **Waiting on
  funding**, or **Failed**"); `requires_confirmation`, `requires_action` → **Incomplete**; `processing` → **Pending**;
  `requires_capture` → **Uncaptured** ("or **Partial capture**" once any amount is received); `succeeded` →
  **Succeeded**, with later refunds and disputes reflected on the Charge; `canceled` → **Canceled**. "Edge cases such as
  expired attempts and specific decline codes can affect this mapping. Use the API or Workbench Inspector to get the
  authoritative state." [Payment status updates](https://docs.stripe.com/payments/payment-intents/verifying-status) — 2026-10-19
- **[DOCS]** "Charge fail: The charge appears as **Failed** in the Dashboard under Payments." "Charge partially
  refunded: You can see the charge as `Refunded`". [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19
- **[MEASURED]** The off-session decline `pi_3USEMG5y1DMwE3zY0P5qCp1v` has a failed `latest_charge`
  (`ch_3USEMG5y1DMwE3zY0vKtkfxM`), so the Dashboard's word for a refused share is likely **Failed**, not Incomplete;
  a share waiting for the bank's check (`requires_action`) reads **Incomplete**.

### Workbench: any object by its ID, every event and its deliveries

- **[DOCS]** Inspector: "Enter an object ID from the **Inspector** tab" — JSON, related objects, request logs and
  events. Events tab: filter by type (wildcards) and resource; "Click **Resend** on a delivery attempt to resend".
  Logs: filter by "Account that the request applied to, which might be the connected account". Only Administrator or
  Developer roles have full access. [How Workbench works](https://docs.stripe.com/workbench/overview) — 2026-10-19
- **[ABSENT]** A Dashboard list page for SetupIntents — not found; the Inspector by `seti_` ID is the documented way
  (looked 2026-10-19).

### A club's own pages: the connected account and View Dashboard As

- **[DOCS]** Connected accounts badges: **Restricted**, **Restricted soon**, **In review** ("typically last 24–48
  hours"), **Enabled**, **Rejected**; an **Actions required** list tops the account page.
  [Connect Dashboard](https://docs.stripe.com/connect/dashboard) — 2026-10-19
- **[DOCS]** "To view the Stripe Dashboard from the perspective of the connected account, click the overflow menu (⋯)
  and select **View Dashboard As** … This feature works by passing the connected account ID as the
  `stripe-account-header`". [Manage individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts) — 2026-10-19
- **[DOCS]** "Connected accounts with access to the full Stripe Dashboard show 'Unavailable' in the **Volume**
  column, unless they have platform controls enabled." The **Payment balance** column is pending plus available.
  [Review connected accounts](https://docs.stripe.com/connect/dashboard/review-actionable-accounts);
  [View all accounts](https://docs.stripe.com/connect/dashboard/viewing-all-accounts) — 2026-10-19

### Payout and refund statuses

- **[DOCS]** Payout: `pending` ("Funds haven't left Stripe yet"), `in_transit`, `paid` ("typically … 1-2 business days
  after submission"), `failed` (with `failure_code`), `canceled`.
  [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — 2026-10-19
- **[DOCS]** Refund: `pending`, `succeeded`, `failed`, `canceled` ("a type of refund failure"), `requires_action` (not
  for cards). [Refunds](https://docs.stripe.com/refunds) — 2026-10-19

### Stripe emails nobody in a sandbox

- **[DOCS]** "By default, Stripe doesn't email customers in sandboxes." [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19.
  Every email in a walk is the product's own (Mailpit).

---

## 8. Clocks: what a sandbox can't speed up

### Test clocks move Billing objects only

- **[DOCS]** "Test clocks allow you to simulate `Billing` objects, like subscriptions, through time in a sandbox."
  [Test your Billing integration](https://docs.stripe.com/billing/testing); limits on attaching existing customers and
  on list results are Billing's ([API and advanced usage](https://docs.stripe.com/billing/testing/test-clocks/api-advanced-usage)) — 2026-10-19
- **[ABSENT]** Any clock that moves a hold's `capture_before`, a balance's `available_on` or a payout schedule — carried
  from [`stripe-holds-and-capture.md#nothing-in-test-mode-shortens-a-hold-or-moves-its-clock`](stripe-holds-and-capture.md#nothing-in-test-mode-shortens-a-hold-or-moves-its-clock), re-searched 2026-10-19.

### A card's state carries from one test to the next

- **[DOCS]** "Card-level state from one test can affect later tests that use the same card. When a test depends on
  card-level state, use a different test card for each independent end-to-end scenario."
  [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19
- **[DOCS]** "The rate limiter is stricter in test environments than in live mode." [Testing](https://docs.stripe.com/testing?locale=en-GB) — 2026-10-19

---

## 9. The CLI and the sandbox

### `stripe login`: an administrator must allow the CLI first

- **[DOCS]** "For Stripe CLI versions newer than v1.50.0, an Administrator or IAM Admin must enable CLI access before you
  can authenticate … Settings → Team and security → MCP and CLI access." `stripe switch` selects "another account or
  sandbox"; `stripe login --interactive` takes an API key instead. [CLI login](https://docs.stripe.com/cli/login) — 2026-10-19

### `stripe listen`

- **[DOCS]** "You don't need to configure any webhook endpoints in your Dashboard to receive webhooks with the CLI."
  "By default, `listen` accepts all snapshot webhook events"; `-e` filters; `-c, --forward-connect-to`: "The URL that
  Connect webhook events will be forwarded to. By default, the same URL will be used for all snapshot webhook events";
  thin events only with `--thin-events` and `--forward-thin-to`; `-l, --latest` for the latest API version, else the
  account's default; `--live`: "Requests run in a sandbox by default." [CLI listen](https://docs.stripe.com/cli/listen) — 2026-10-19
- **[DOCS]** "To use the `--forward-to` argument with `stripe listen`, you must run the command with Stripe CLI in a
  terminal. This command can't be run in the Workbench Shell". [Webhooks](https://docs.stripe.com/webhooks) — 2026-10-19
- **[ABSENT]** Whether the CLI retries an event the laptop answered with an error — not on the listen page (2026-10-19).

### `stripe trigger` makes objects of its own

- **[DOCS]** "Triggering events causes side effects: all necessary API objects will be created in the process." Flags:
  `--stripe-account` ("a header identifying the connected account"), `--override`, `--add`, `--remove`, `--skip`,
  `--edit`. [CLI trigger](https://docs.stripe.com/cli/trigger) — 2026-10-19
- **[DOCS]** Of the events this product reads or should read, the list **has** `setup_intent.succeeded`,
  `.setup_failed`, `payment_intent.amount_capturable_updated`, `.succeeded`, `.canceled`, `.payment_failed`,
  `.requires_action`, `charge.captured`, `charge.refunded`, `charge.refund.updated`, `charge.dispute.created`,
  `payout.created`, `payout.updated`, `account.updated`, `account.application.deauthorized`; it **lacks**
  `charge.updated`, `refund.failed`, `refund.updated`, `payout.paid`, `payout.failed`, `charge.dispute.closed` and
  `payment_method.automatically_updated`. Same page — 2026-10-19
- Code: a notice is matched to the product's own records by the object's ID — a payment of no seat is logged
  `payments.notice.payment_of_no_seat` and dropped (`backend/app/modules/payments/application/notices.py:143-152`), an
  account of no club `payments.notice.account_of_nobody` (`:96-101`). A triggered fixture belongs to nobody.

### `stripe events resend` re-delivers a real event to the laptop

- **[DOCS]** "Resend an event to the CLI's local webhook endpoint … You can only resend events that have been created
  within the last 30 days." `--account=<account_id>`: "To resend an event that's sent to a Connect webhook endpoint on
  a platform, set this flag to the connected account ID". [CLI events resend](https://docs.stripe.com/cli/events/resend) — 2026-10-19
- Code: the inbox acts on a notice only at its first reading by ID (`notices.py:87-90`), so a resend should be
  acknowledged and do nothing; an older event resent after a newer one is the out-of-order case.

### No test card or trigger for an automatic card update

- **[ABSENT]** A test card or trigger that raises `payment_method.automatically_updated` — not in the testing page or
  the trigger list; searched "test card account updater" 2026-10-19.

### Sandboxes versus the test mode sandbox

- **[DOCS]** The test mode sandbox: "Use one sandbox"; "Share settings between live mode and the test mode sandbox";
  "Supports V1 and partially supports V2"; "Can't be deleted". General sandboxes: "up to five"; "Isolate settings
  completely"; "Supports V1 and V2"; "Can be deleted". [Testing use cases](https://docs.stripe.com/testing-use-cases?locale=en-GB) — 2026-10-19
- **[DOCS]** In a sandbox "Identity doesn't perform any verification checks. Also, Connect account objects don't
  return sensitive fields." Delete test data: "Developers > Overview … **Review test data** … **Delete test data** …
  You can't undo"; "Sandboxes are temporarily unusable while the deletion process occurs." Same page — 2026-10-19
- Which kind the Raketa sandbox is was not established: `livemode: false` "doesn't distinguish" them
  ([`stripe-security.md#general-sandboxes-isolate-settings-the-test-mode-sandbox-shares-some-with-live`](stripe-security.md#general-sandboxes-isolate-settings-the-test-mode-sandbox-shares-some-with-live));
  the product's v2 account calls succeeded on it ([`stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses`](stripe-sandbox.md#the-test-club-account-full-dashboard-the-club-pays-the-fees-stripe-covers-losses)).

### Google Pay on the Android phone

- **[DOCS]** "Google allows you to make test payments through their Test card suite. The test suite supports using
  Stripe test cards. You must test Google Pay using a physical Android device instead of a simulated device, in a
  country where Google Pay is supported. Log in to a Google account on your test device with a real card saved to
  Google Wallet." "Expo Go doesn't support Google Pay." [Google Pay](https://docs.stripe.com/google-pay?platform=react-native&locale=en-GB) — 2026-10-19
- Code: the wallet's test switch follows the key, `testEnv: publishableKey.startsWith('pk_test_')`
  (`payments.tsx:354`), and Google Pay is offered only after a setup has started Stripe (`:314-330`).
- **[ABSENT]** Which brand and last four Stripe records for a Google Pay card saved in test mode, and whether any
  decline or check can be simulated through a wallet (looked 2026-10-19).

---

## Pitfalls

1. **Typing an issuer-decline card to stage a refused hold.** 0002, 9995, 0069 and the rest can't be attached, so the
   phone refuses them at Save and no game ever reaches the bank. A refused hold needs 0341 (generic decline) or
   3178 (insufficient funds), which save first. ([Testing](https://docs.stripe.com/testing))
2. **Expecting the phone to name the reason.** Stripe returns a different code per card; the product shows one
   sentence for all and keeps the code only on the share. A walk that wants reason-specific words grades the product,
   not the card. ([Testing](https://docs.stripe.com/testing); `paymentsCopy.ts:164`)
3. **Using 3155 to stage "the bank wants you present" at the hold.** Once set up, Stripe says 3155's off-session
   payments pass; the every-payment check is 3184 (or the 4000 5826 … challenge cards). And whether 3155's setup
   carries to the club's clone has never been seen. ([Testing](https://docs.stripe.com/testing))
4. **Making a payment in the Dashboard to see the check.** "3D Secure redirects won't occur for payments created
   directly in the Stripe Dashboard." ([Testing](https://docs.stripe.com/testing))
5. **Reading 4242's fee as a Polish player's fee.** 4242 is US-issued; a Polish Visa is 4000 0061 6000 0005. Read
   each share's fee on its own payment. ([Testing](https://docs.stripe.com/testing))
6. **Waiting for a refund to fail on an ordinary card.** "With all other test cards, refunds succeed immediately and
   don't change status after that." Only 5126 fails later (with `refund.failed`) and only 7726 starts pending.
   ([Testing](https://docs.stripe.com/testing))
7. **Reaching for `stripe trigger` for a failed refund or payout.** Neither `refund.failed` nor `payout.failed`
   (nor `charge.updated`, `payout.paid`) can be triggered, and a triggered fixture belongs to no seat or club.
   Duplicates and disorder on real objects come from `stripe events resend`. ([CLI trigger](https://docs.stripe.com/cli/trigger);
   [CLI events resend](https://docs.stripe.com/cli/events/resend))
8. **Reading the badge as the state.** Partial and full refunds both read *Refunded*; a refused share reads *Failed*
   or *Incomplete* by whether a charge was attempted; "use the API or Workbench Inspector to get the authoritative
   state." ([Payment status updates](https://docs.stripe.com/payments/payment-intents/verifying-status))
9. **Looking for the club's money on the platform's own pages.** Direct charges, refunds, disputes, balance and
   payouts live on the club's account: Connected accounts → the club → ⋯ → **View Dashboard As**.
   ([Manage individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts))
10. **Expecting a club's payout in a walk.** Card money waits 7 days on the sandbox (Poland's first settlement is 7
    calendar days), and a full-Dashboard club needs Platform controls before the platform can pay it out. The
    bypass-pending cards may shorten the first part; nothing shortens the second.
    ([Payouts](https://docs.stripe.com/payouts); [Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts))
11. **Using the block cards on a fully onboarded club.** 4210 and 4236 need an `eventually_due` requirement and do
    nothing without one; the test club has none. ([Testing Connect](https://docs.stripe.com/connect/testing))
12. **Testing a wallet on an emulator or in Expo Go.** Google Pay needs a physical device with a real card in Google
    Wallet; Apple Pay a merchant ID and a real card. ([Google Pay](https://docs.stripe.com/google-pay?platform=react-native))
13. **Reusing one card across scenes.** "Card-level state from one test can affect later tests that use the same card."
    ([Testing use cases](https://docs.stripe.com/testing-use-cases))
14. **A CLI that can't log in.** From v1.50.0 an administrator must turn on CLI access first; the walk's listener then
    fails before any notice. ([CLI login](https://docs.stripe.com/cli/login))
15. **Building on Accounts v2 in the test mode sandbox.** It "partially supports V2"; general sandboxes support it
    fully. ([Testing use cases](https://docs.stripe.com/testing-use-cases))
16. **Treating a sandbox dispute as a walk of the club's experience.** The club answers in its own Dashboard with
    `winning_evidence` / `losing_evidence` in **Additional information**; the product hears nothing, since it reads no
    dispute event. ([Testing](https://docs.stripe.com/testing))

## Checks

1. Does each money scene name the card whose documented behaviour produces it **at the moment the product acts** —
   attach for a save, charge for a hold — rather than a card that fails a step earlier?
2. Is a refused-at-save scene walked with an issuer-decline card, and a refused-hold scene with 0341 or 3178?
3. Is "the bank wants the player present" walked with 3184 (or a 4000 5826 … challenge card), and is the
   saving-only check walked with 3155, each on the phone, never from the Dashboard?
4. Does a rule about the reason for a decline say what the player sees, given that every card's reason reaches the
   share but none reaches the screen?
5. Is each fee box read from that payment's balance transaction, with the card's country named (4242 US;
   4000 0061 6000 0005 PL)?
6. Is the refund-fails-later scene walked with 5126 and the refund-pending scene with 7726, and does the product
   follow `refund.failed` and `refund.updated` to the player and the club?
7. Is a card dispute walked with 0259, 2685 or 1976 after the share is taken, read on the club's Disputes tab, and
   is the rule that says the product records it (or emails the desk) checked against a code that subscribes to no
   dispute event?
8. Does every Dashboard box use Stripe's own word and page — Uncaptured, Succeeded, Canceled, Failed or Incomplete,
   Refunded (partial too), Disputed; Connected accounts → the club → View Dashboard As → Payments / Balances /
   Disputes — and the Inspector by ID for a SetupIntent?
9. Is a duplicate or out-of-order notice walked with `stripe events resend <evt> --account=<club>` on a real event,
   never with `stripe trigger`?
10. Is every scene measured in days (hold lapse, first payout, refund failing weeks later in live) marked not walkable
    rather than given a test clock?
11. Is the walk's club opened by the product inside the platform's sandbox and onboarded with Stripe's test values,
    and is its `eventually_due` read before 4202, 4210 or 4236 is used?
12. Is a failed payout staged with a failing Polish IBAN on the club's bank account, and is a club payout attempted
    only where Platform controls and available money allow it?
13. Is each independent scene given its own card, so one test's card state can't leak into the next?
14. Is a wallet scene walked on the physical Android phone with a real card in Google Wallet, and the iPhone's Apple
    Pay left waiting on the merchant ID?
15. Is it known whether the Raketa sandbox is a general sandbox or the test mode sandbox, given that the latter only
    partially supports v2 accounts?
16. Before the walk, has an administrator enabled CLI access, and is `stripe listen` forwarding both scopes?
