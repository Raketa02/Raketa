# Stripe gaps for S-16

The `stripe:` gaps of story S-16 (the new player's last yes fills a game; the today path, the *Undo* round, B1–B3
and branch C), answered on 2026-10-20 against the code at `9ab0ea5b`.

**Sources.**

- docs.stripe.com pages, fetched directly.
- The Stripe CLI's own source at tag `v1.54.0`, the version installed on the laptop.
- The sandbox, read through the Stripe SDK in the code copy, read only:
  - the platform key, `acct_1US89K5y1DB8chHb`, test mode;
  - the test club's objects read as `acct_1US95f5y1DMwE3zY` (Robert Club).

The Stripe MCP servers were disconnected. No object was made.

| # | Rule | The question, short | Answer |
|---|---|---|---|
| 1 | R-FILL-11 | A queued offline yes held `off_session` | Stripe's definitions make it the player's own payment; how networks treat the label is **[ABSENT]** |
| 2 | R-FILL-59 | A full-share check let go at once | **[ABSENT]**, carried. New: an uncaptured hold can't be disputed, and S-16's two checks were let go within 1–3 s with no fee booked |
| 3 | R-FILL-59 | Visa window of a live off-session hold on a clone | **[ABSENT]** live; Stripe's signal points to 4 days 18 hours; the sandbox gives 7 days again today |
| 4 | R-DECK-33 | Terms accepted at the save as the cancellation-policy disclosure | Stripe's guidance ties the disclosure to the purchase, and these terms don't describe the take; the issuer's verdict is **[ABSENT]** |
| 5 | R-FILL-10 | The platform's Inspector on a club's `pi_` | **[ABSENT]** as asked; the View Dashboard As path is documented end to end |
| 6 | R-FILL-10 | Does `stripe listen` mark a Connect notice | **Yes**: `--> connect <type>`, and the answer line names `/webhooks/stripe-connect` |
| 7 | R-FILL-11 | Off-session hold while the same player confirms another payment (C2) | **[ABSENT]** for the networks; the sandbox treats both alike |
| 8 | R-FILL-11 | `statement_descriptor_suffix` on a direct charge, v2 full-Dashboard club | **Yes**, documented with the `Stripe-Account` header; Robert Club's prefix leaves 10 characters |
| 9 | R-FILL-10 | Two identical 40,00 zł holds seconds apart (C1) | Radar has no default rule for it; the sandbox approved 12 on one card in 28 s; issuers **[ABSENT]** |
| 10 | R-FILL-37 | Window of a refused share confirmed with a typed card, live Visa | 7 days by Stripe's table, counted from the charge that held; measured twice; live **[ABSENT]** |
| 11 | R-FILL-2 | Club notices after hosted onboarding | **Yes** on the sandbox: nine Connect lines over 6½ minutes after the form was sent, then quiet |

---

### 1 · R-FILL-11 · A queued yes sent at reconnect, with no press at that moment

**The code.** Every share is held `off_session: True`, `confirm: True`, the filler's own included
(`backend/app/modules/payments/infrastructure/stripe_payments.py:506-507`). A yes queued offline arrives as the same
request as a yes pressed now, so the server can't tell them apart.

**What Stripe says.**

- **[DOCS]** [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits), re-read 2026-10-20:
  - MIT: "An MIT is a transaction that you initiate without direct participation of your customer, based on a prior
    agreement with that customer authorizing you to store and use their credentials."
  - CIT: "CITs normally include all other transaction types, including any transaction where the cardholder is
    available to participate in the payment flow."
  - These are definitions, not requirements.
  - The page says nothing about a customer who is in the app but outside a checkout flow, or about the consequence
    of a payment labelled one way and classed the other.
- **Carried:**
  - "Stripe and the card network classify transactions as MIT or CIT based on signals of cardholder participation,
    not solely on API parameters like `off_session`"
    ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session)).
  - `off_session`: "the customer isn't in your checkout flow during this payment attempt and can't authenticate"
    ([`stripe-gaps-01.md`](stripe-gaps-01.md#r-fill-11--a-share-held-while-its-player-is-in-the-app-started-by-his-own-yes-is-customer-initiated-by-stripes-definitions)).

**What the sandbox holds.**

- **[MEASURED]** Read via the SDK in the copy on 2026-10-20: the two holds of B3's shape (C-3 in the story's
  breaker), made by a last yes at a club Stripe knows:
  - `pi_3USbi65y1DMwE3zY1ppdt5tH` → `ch_3USbi65y1DMwE3zY1i8UhO3n`;
  - `pi_3USbi85y1DMwE3zY01oPtlhU` → `ch_3USbi85y1DMwE3zY0y9SBhZX`;
  - each 40,00 zł on Visa •••• 4242, `cvc_check: pass`, `three_d_secure: null`, `risk_level: normal`;
  - each `capture_before` exactly 168,0 hours after its charge.
- No field on the payment or the charge says how it was classed
  ([`stripe-gaps-06.md`](stripe-gaps-06.md#8--r-request-60--the-visa-window-a-live-off-session-hold-on-a-clone-gets)).

**[ABSENT]** Whether a card network treats a payment flagged "can't authenticate" as merchant-initiated when the
cardholder's own queued yes started it while he holds the phone, and with what consequence.

- **Looked, 2026-10-20:** CITs and MITs (re-read), place-a-hold, the PaymentIntent create and confirm references,
  and SCA exemptions (all three carried).
- A question for Stripe support.

**Reading.**

- The queue changes nothing that Stripe documents. The yes was the player's own act, pressed earlier and delivered
  now. By Stripe's definitions that is participation, the customer-initiated side, while the flag says the
  opposite.
- This is the same labelling question as the pressed yes in `stripe-gaps-01.md`.
- Live, the only readable sign is the hold's `capture_before` on a Visa card:
  - 7 days means it was treated as customer-initiated;
  - 4 days 18 hours means merchant-initiated.

### 2 · R-FILL-59 · A full-share authorisation let go at once, only to check the money

**Answer: still [ABSENT]. Nothing new from Stripe on the networks' side.**

- Carried, read 2026-10-20 by three earlier passes:
  - "Card networks may also restrict 1 USD authorizations you don't intend to capture";
  - nothing is said of a full-amount authorisation cancelled at once;
  - cancelling costs nothing on blended pricing, and on IC+ each authorisation and void carries a network fee.
  - Sources: [`stripe-gaps-01.md`](stripe-gaps-01.md#r-fill-59--a-full-share-check-let-go-at-once-stripe-names-only-1-usd-checks-on-blended-pricing-it-costs-the-club-nothing),
    [`stripe-gaps-00.md`](stripe-gaps-00.md#r-platform-65--whether-the-networks-restrict-a-full-share-hold-let-go-at-once-and-whether-it-counts-toward-reattempt-limits),
    [`stripe-gaps-05.md`](stripe-gaps-05.md#r-rescue-14--a-full-share-hold-cancelled-at-once-the-networks-may-restrict-it-and-no-source-says-whether-this-counts).
- **[DOCS]** New, from [Best practices for preventing fraud](https://docs.stripe.com/disputes/prevention/best-practices),
  read 2026-10-20: "Cardholders can't dispute uncaptured authorizations, only fully captured payments."
  - A check that is let go can't come back to the club as a dispute.
- **[MEASURED]** The story's breaker made two checks (row C-5, a game filling 8 days ahead). Read via the SDK in the
  copy on 2026-10-20, on the test club:
  - `pi_3USbiI5y1DMwE3zY1nBdvTSz` → `ch_3USbiI5y1DMwE3zY1pHyFMm9`: 40,00 zł held at 12:00:18 UTC, let go at 12:00:21;
  - `pi_3USbiJ5y1DMwE3zY0dqHRYMy` → `ch_3USbiJ5y1DMwE3zY0pEua5zO`: held at 12:00:19, let go at 12:00:20;
  - both charges read `approved_by_network`, `captured: false` and `balance_transaction: null`, so no fee is booked.

  A sandbox applies no network rule, so it can't show a restriction.
- **[ABSENT]** Whether Visa or Mastercard accept a full-share authorisation cancelled the same second as a card
  check, or count it toward their reattempt limits.
  - **Looked:** place-a-hold, cits-and-mits, the support article on checking a card (all carried), the fraud best
    practices page (2026-10-20).
  - A question for Stripe support, or for the networks' own rules.

### 3 · R-FILL-59 · Which window a live off-session Visa hold on a cloned card gets

**Answer: [ABSENT] live, carried.** Stripe's own signal points to 4 days 18 hours.

- Carried **[DOCS]**:
  - Visa's merchant-initiated window is "5 days\*", exactly 4 days 18 hours; its customer-initiated window is 7 days;
  - "a payment with `off_session: true` might still be classified as a CIT if a CVC is present";
  - a saved card's later payment carries no CVC;
  - the charge's `capture_before` is "the most reliable and accurate way" to read the window.
  - Sources: [`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#online-card-holds-visa-4-days-18-hours-without-the-payer-7-days-with-mastercard-amex-discover-7),
    [`stripe-gaps-01.md`](stripe-gaps-01.md#r-fill-59-r-fill-60--a-live-off-session-hold-on-a-copy-carries-no-cvc-and-that-signal-points-to-visas-4-days-18-hours-unmeasured),
    [`stripe-gaps-02.md`](stripe-gaps-02.md#r-leave-44-r-leave-46--which-window-a-live-off-session-visa-hold-on-a-card-copy-gets).
- **[MEASURED]** Nine S-16 holds made off-session were read in full. Each reads `cvc_check: pass` and a
  `capture_before` exactly 168,0 hours after its charge. They were read via the SDK in the copy on 2026-10-20, and
  were created between 12:00:06 and 12:00:34 UTC:
  - `ch_3USbi65y1DMwE3zY1i8UhO3n`, `ch_3USbi85y1DMwE3zY0y9SBhZX`;
  - `ch_3USbiB5y1DMwE3zY0O8xPGcd`, `ch_3USbiC5y1DMwE3zY1GnHkJuH`, `ch_3USbiE5y1DMwE3zY1x5fqzyW`,
    `ch_3USbiF5y1DMwE3zY1dS7xwsU`;
  - `ch_3USbiP5y1DMwE3zY1jqTG59C`;
  - `ch_3USbiX5y1DMwE3zY19JCYmYB`, `ch_3USbiY5y1DMwE3zY0z7pMlok`.

  The sandbox's test card answers the CVC check on every clone, so it can't produce the shorter window.
- **[ABSENT]** The live window.
  - A question for Stripe support.
  - Live, the first hold's `capture_before` settles it. The code reads that field on every hold
    (`stripe_payments.py:510-511`).

### 4 · R-DECK-33 · Terms accepted once, at the save, as the cancellation-policy disclosure for a share taken at the fill

**The terms.** These are the terms the player accepted when saving the card, version `2026-10-10`
(`frontend_player/src/features/payments/components/paymentsCopy.ts:62-75`). They say: "Your share is taken at the
club's cut-off. Leave before the cut-off and nothing is taken."

They don't name a share taken as soon as a game fills after its cut-off. They also don't say that such a game has no
free cancellation.

**What Stripe says.**

- **[DOCS]** [Best practices for preventing fraud](https://docs.stripe.com/disputes/prevention/best-practices), read
  2026-10-20. This is a best-practice page; its "must" is a condition for evidence, not a rule on the payment:
  - "Include a clear description of your refund and cancellation policies in your terms of service. You can require
    your users to agree to your terms of service to increase the likelihood that card issuers respect your policies
    in the event of a dispute."
  - "Card issuers can be very specific about how you present your policies. If you have a checkbox your customer
    must accept that only contains a link, the issuer might reject it as unsatisfactory evidence that your customer
    was aware of your policies. There must be reasonable evidence that you presented your customer with a full copy
    of your policies prior to their purchase."
- **[DOCS]** [Dispute categories](https://docs.stripe.com/disputes/categories), read 2026-10-20. Under *Credit not
  processed* (Visa 13.6, 13.7 "Canceled Merchandise/Services"):
  - "Have a clear return or cancellation policy that's easy to find or explicitly disclosed to the customer prior to
    purchase."
  - "Offline services include purchases that are made in advance, such as event tickets and reservations, where
    evidence of a cancellation policy can be material."
  - The evidence asked for: "An explanation of how and where you provided the applicable policy to your customer
    prior to purchase" (`cancellation_policy_disclosure`).
  - Carried: [`stripe-refunds-and-disputes.md`](stripe-refunds-and-disputes.md#the-evidence-a-booked-game-would-need-the-cancellation-policy-as-shown-and-that-it-was-played).
- **[DOCS]** [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits), read 2026-10-20. Phrased as an
  instruction:
  - "To charge customers when they're offline, include the following in your terms: … The anticipated timing and
    frequency of payments".
  - "When you save a payment method, you can only use it for the specific purposes included in your terms."
  - Carried: [`stripe-saving-cards.md`](stripe-saving-cards.md#what-the-terms-must-say).

**[ABSENT]** Whether an issuer accepts terms accepted once, at the save, as the disclosure for a later booking whose
policy they don't state. Issuers decide disputes. No Stripe page addresses a policy agreed before an earlier,
different purchase.

- **Looked, 2026-10-20:** the fraud best practices page, dispute categories, CITs and MITs, and the carried dispute
  pages in `stripe-refunds-and-disputes.md`.

**Reading.**

- Stripe ties the disclosure to the purchase, which here is the yes. It warns that issuers can reject even a
  checkbox with a link.
- The saved terms describe a take at the cut-off, so they don't describe what happened:
  - a take at the fill;
  - no free cancellation.
- A club defending a *credit not processed* dispute on such a share would have only those terms to show. Stripe's
  guidance makes that weak evidence.
- What meets Stripe's guidance is the policy shown in full on the card before the yes, with a record of what was
  shown and when. The club can then cite that record as its `cancellation_policy_disclosure`.

### 5 · R-FILL-10 · Does the platform's Workbench Inspector find a club's `pi_` outside View Dashboard As

**What Stripe says.**

- **[DOCS]** [How Workbench works](https://docs.stripe.com/workbench/overview), read 2026-10-20:
  - "Use the Inspector to explore a JSON view of API objects on your Stripe account."
  - "To inspect an object, you can: Enter an object ID from the **Inspector** tab. Visit a Dashboard page for any
    object (for example, a `Payment`, `Customer`, or `Subscription`) and click the **Inspector** icon".
  - Connected accounts are named only in the Logs filters: "Account that the request applied to, which might be the
    connected account of a Connect platform". The Shell's API Explorer can set "the Stripe-Account header which
    allows making API requests to a connected account".
- **[DOCS]** [Manage individual accounts](https://docs.stripe.com/connect/dashboard/managing-individual-accounts),
  read 2026-10-20. View Dashboard As "works by passing the connected account ID as the `stripe-account-header` on
  requests made from the Stripe Dashboard, similar to making API calls on behalf of connected accounts."
- **[DOCS]** [Workbench use cases](https://docs.stripe.com/workbench/guides), read 2026-10-20: no word on connected
  accounts.
- **[DOCS]** Stripe's own CLI builds the Dashboard link of a Connect notice under the club's account ID in the path:
  `https://dashboard.stripe.com/<connected account>/test/events/<evt_…>`.
  - Source: [`pkg/proxy/stripeevent.go` `BaseDashboardURL`, v1.54.0](https://github.com/stripe/stripe-cli/blob/v1.54.0/pkg/proxy/stripeevent.go),
    read 2026-10-20.
  - The Dashboard addresses a club's objects in the club's own context.
- Carried: [`stripe-testing.md`](stripe-testing.md#a-clubs-own-pages-the-connected-account-and-view-dashboard-as).

**[ABSENT]** Whether the platform's own Inspector tab, outside View Dashboard As, finds a `pi_` that lives on a
club's account by its ID.

- **Looked, 2026-10-20:** the Workbench overview and use cases, Manage individual accounts, and a web search.
- It can't be tried here: it is the Dashboard's interface, and the MCP servers were disconnected.

**Reading.** One path is documented at every step: Connected accounts → the club → ⋯ → **View Dashboard As** →
Payments → the payment → the **Inspector** icon.

- View Dashboard As sends the club's account ID.
- The Inspector works from any object's page.
- In the listener, clicking a club notice's `evt_` ID also opens the club's own Dashboard context (§6).

### 6 · R-FILL-10 · Does `stripe listen` mark a Connect notice in its terminal lines

**Answer: yes.** It marks the notice, and the answer line names the endpoint.

- **[DOCS]** The Stripe CLI's source at `v1.54.0`, read 2026-10-20,
  [`pkg/cmd/listen.go`](https://github.com/stripe/stripe-cli/blob/v1.54.0/pkg/cmd/listen.go):
  - **The notice line** (`:368-387`):
    - for each snapshot event, `maybeConnect = "connect "` when `data.IsConnect()`;
    - the line is printed as `"%s   --> %s%s [%s]"`, giving for example
      `2026-10-20 12:00:07   --> connect payment_intent.amount_capturable_updated [evt_…]`;
    - v2 thin events get the same mark (`:346-366`).
  - **What makes a notice Connect:** `IsConnect()` is `e.Account != ""`, the event's top-level `account`
    ([`pkg/proxy/stripeevent.go:28-31`](https://github.com/stripe/stripe-cli/blob/v1.54.0/pkg/proxy/stripeevent.go)).
  - **The answer line** (`:402-407`): `"%s  <--  [%d] %s %s [%s]"`, giving for example
    `<--  [200] POST http://localhost:8000/api/v1/webhooks/stripe-connect [evt_…]`. A club's notice shows
    `/webhooks/stripe-connect`, the platform's shows `/webhooks/stripe`.
  - **Only in text output:** with `--format JSON` or `--print-json` the raw event is printed instead
    (`:347-350`, `:369-370`).
- **[MEASURED]** On 2026-10-20:
  - `stripe version` on the laptop prints `1.54.0`;
  - the latest release is `v1.54.1`, published 2026-10-19 22:54 UTC (GitHub releases API);
  - `stripe listen --help` lists a newer flag the docs page didn't show on 2026-10-19: `--events-from` with
    `@self`, `@accounts` or `all`.
- Carried: [`stripe-testing.md`](stripe-testing.md#stripe-listen).

### 7 · R-FILL-11 · An off-session hold while the same player confirms another payment on-session (C2)

**What the sandbox holds.** **[MEASURED]**, read via the SDK in the copy on 2026-10-20, all on the test club, all
Visa:

| Time (UTC, 2026-10-20) | Object | What happened |
|---|---|---|
| 12:00:26 | `pi_3USbiQ5y1DMwE3zY1mgot0SP` → `ch_3USbiQ5y1DMwE3zY1tDAn31N` | Her share is refused off-session on Visa •••• 0341: `issuer_declined`, `generic_decline`, advice `try_again_later` |
| 12:00:31 | the same payment → `ch_3USbiQ5y1DMwE3zY1qvJxArB` | She confirms it on-session with a typed Visa •••• 4242: held, `cvc_check: pass`, `three_d_secure: null`, `capture_before` +168,0 h |
| 12:00:33 | `pi_3USbiX5y1DMwE3zY1xSOvAT0` → `ch_3USbiX5y1DMwE3zY19JCYmYB` | The other game's shares, hers among them, held off-session on fresh clones (`pm_1USbiW5y1DMwE3zYJSICrmkD`), 2 s after her confirmation: `cvc_check: pass`, `risk_level: normal`, +168,0 h |
| 12:00:34 | `pi_3USbiY5y1DMwE3zY0huXXqsL` → `ch_3USbiY5y1DMwE3zY0z7pMlok` | The same, on clone `pm_1USbiX5y1DMwE3zYkFJjZYEf`, +168,0 h |

The holds made seconds after her on-session confirmation look exactly like every other off-session hold on the
sandbox.

**What Stripe says.**

- Carried **[DOCS]**: Stripe classes a payment "based on signals of cardholder participation, not solely on API
  parameters like `off_session`"
  ([`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#stripe-decides-with-or-without-the-payer-from-signals-not-from-off_session)).
- No page says that one payment's on-session confirmation changes how another payment on the same account and card
  is classed.

**[ABSENT]** Whether such a hold is classed customer- or merchant-initiated.

- **Looked, 2026-10-20:** CITs and MITs (re-read), place-a-hold and SCA exemptions (both carried).
- The sandbox gives 7 days to everything, so it can't show a difference.
- A question for Stripe support. Live, each hold's own `capture_before` answers it for that hold.

### 8 · R-FILL-11 · `statement_descriptor_suffix` on a direct charge on an Accounts v2 club with its own full Dashboard

**Answer: yes, by Stripe's docs.** No page limits the suffix by Dashboard type or by Accounts v2.

**What Stripe says.**

- **[DOCS]** [Set statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors),
  read 2026-10-20 (the page the gap said was unread):
  - "The customer's statement uses the connected account's static component for the following charge types:
    Direct charges …"
  - Under *Set a dynamic suffix for connected account charges*: "Dynamic suffixes are supported only for card
    charges by using the PaymentIntents `statement_descriptor_suffix` parameter." The example creates the
    PaymentIntent with `-H "Stripe-Account: {{CONNECTEDACCOUNT_ID}}"` and `statement_descriptor_suffix=Custom suffix`.
    That is a direct charge, as Raketa makes them.
  - A recommendation: "If you use a dynamic suffix on a charge that uses the connected account's static descriptor,
    we recommend setting a prefix to on the connected account so the complete statement descriptor appears as
    intended." The typo is Stripe's.
  - Who controls the prefix:
    - "Connected accounts with access to a Stripe-hosted dashboard … can update their own statement descriptor
      settings."
    - The platform may update the descriptor and prefix only "After onboarding an account that doesn't have access
      to the full Stripe Dashboard".
    - So a full-Dashboard club owns its prefix, and Raketa only adds the suffix.
  - "Only the first 22 characters of the full statement descriptor are sent for card payments."
  - "For card payments, you can't specify the `statement_descriptor`. You can only specify the
    `statement_descriptor_suffix`."
- **[DOCS]** [Statement descriptors](https://docs.stripe.com/get-started/account/statement-descriptors?locale=en-GB),
  read 2026-10-20. These are requirements, "must meet":
  - "Contains only Latin characters."
  - "Contains between 5 and 22 characters, inclusive."
  - "Contains at least one letter (if using a prefix and a suffix, both require at least one letter)."
  - "Doesn't contain any of the following special characters: `<`, `>`, `\`, `'` `"` `*`."
  - "A static prefix … must contain between 2 and 10 characters".
  - On length: "Make sure that the total length of the concatenated descriptor is no more than 22 characters,
    including the `*` symbol and the space." Example: `RUNCLUB* 9-22-19 10K`.
  - "Most banks display this information consistently, but some might display it incorrectly or not at all."
- **[DOCS]** [Capture a PaymentIntent](https://docs.stripe.com/api/payment_intents/capture), read 2026-10-20: the
  capture also takes `statement_descriptor_suffix`, which "Provides information about a card charge. Concatenated to
  the account's statement descriptor prefix to form the complete statement descriptor that appears on the customer's
  statement."

**What the sandbox holds.**

- **[MEASURED]** The test club `acct_1US95f5y1DMwE3zY`, read via the SDK on 2026-10-20:
  - full Dashboard (`controller.stripe_dashboard.type: full`), shown as `type: standard` by the v1 read;
  - `settings.payments.statement_descriptor: "ROBER CLUB"`;
  - `settings.card_payments.statement_descriptor_prefix: "ROBER CLUB"`, 10 characters.
- **[MEASURED]** Every S-16 payment reads `statement_descriptor_suffix: null`, and every charge reads
  `calculated_statement_descriptor: "ROBER CLUB"`.
- The code sends no descriptor at all: `grep statement_descriptor backend/app` finds nothing at `9ab0ea5b`.
- **[MEASURED]** The connected accounts that never finished onboarding read null for both settings.

**Reading.**

- With Robert Club's prefix, `ROBER CLUB* ` takes 12 characters and leaves 10 for the suffix. For example,
  `CZW 19:00` (9) gives `ROBER CLUB* CZW 19:00` (21).
- Stripe says "Latin characters" without saying whether Polish letters such as Ś or Ż count. Unaccented day names
  (`SR`, `CZW`, `PT`, `SOB`) stay within the stated rule.
- The club can change its prefix at any time, which changes the room left. So the suffix's length has to be fitted
  to the club's current prefix, read from its account.
- **[ABSENT]** Whether a Latin suffix sent with the hold shows on the player's pending line, or only once the share
  is taken. Stripe documents send timing only for Japanese descriptors, which are "sent to issuers at time of
  payment capture".

### 9 · R-FILL-10 · Two identical 40,00 zł holds from one club on one card within seconds (C1)

**What the sandbox holds.**

- **[MEASURED]** Every payment the test club received from 11:59:00 to 12:01:00 UTC was listed via the SDK in the copy
  on 2026-10-20. All were 40,00 zł shares from the story's breaker run:
  - on one card fingerprint, `gjVniwT1NxRTIMol` (Visa •••• 4242), **12 authorisations were approved in the 28 seconds
    from 12:00:06 to 12:00:34**, and 21 in the 90 seconds from 11:59:04;
  - every 4242 card in the sandbox shares that fingerprint;
  - the 28 seconds include C1's four: `pi_3USbiB5y1DMwE3zY02bjmNUO`, `pi_3USbiC5y1DMwE3zY1Cc4hsef`,
    `pi_3USbiE5y1DMwE3zY1IIW7CHB` and `pi_3USbiF5y1DMwE3zY1LGsndo9`, from 12:00:11 to 12:00:15;
  - the only refusals were two on Visa •••• 0341, a different card: `ch_3USbhO5y1DMwE3zY0qmOjnGG` and
    `ch_3USbiQ5y1DMwE3zY1tDAn31N`.
- **[MEASURED]** Every one of the 21 approvals reads:
  - `network_status: approved_by_network`;
  - `risk_level: normal`, with risk scores from 6 to 61.

  The nine read in full (§3) also read `type: authorized` and no Radar rule.
- **[MEASURED]** Those nine carry the same `description` ("Tennis · Kort Testowy") and the same statement descriptor
  ("ROBER CLUB"). Nothing on the payment tells one game from the other.

**What Stripe says.**

- **[DOCS]** [Fraud prevention rules](https://docs.stripe.com/radar/rules), read 2026-10-20:
  - "All transactions are screened using Radar's default rules."
  - The default AI rules block `:risk_level: = 'highest'` ("This rule is enabled by default") and send `elevated` to
    review. There are account-level twins as well.
  - No default rule counts repeats.
  - Custom rules apply only "If your Radar plan supports this feature".
  - On a direct charge the club's rules run, not Raketa's
    ([`stripe-connect.md`](stripe-connect.md#the-club-writes-its-own-radar-rules-raketas-rules-dont-reach-its-payments)).
- **[DOCS]** The same page says how Radar groups retries for a rule's traffic allocation: "For card payments, Radar
  groups retry attempts using the following signals, in order of priority: 1. The same invoice. 2. The same customer
  and amount, if no invoice is present. 3. The same card and amount, if no customer is present."
  - A share's clone carries no customer, so two 40,00 zł shares on one card at one club match signal 3.
  - Stripe says this only for traffic allocation, and nowhere that it blocks the second.
- **[DOCS]** [Supported attributes](https://docs.stripe.com/radar/rules/supported-attributes), read 2026-10-20,
  translated from the page as served:
  - `authorized_charges_per_card_number_hourly`: the number of charges from this card authorised in the last hour
    on your account;
  - `total_charges_per_card_number_hourly` is its counterpart for all charges;
  - hourly is the shortest window.
  - A club whose plan allows custom rules could write one on these. None exists by default.
- **[DOCS]** [Dispute categories](https://docs.stripe.com/disputes/categories), read 2026-10-20, *Duplicate* (Visa
  12.6.1):
  - to overturn: "Each payment was for a separate product or service";
  - evidence: `duplicate_charge_id`, `duplicate_charge_explanation`, `duplicate_charge_documentation`;
  - prevention: "ensure it can handle errors without double-charging".
- **[DOCS]** "Cardholders can't dispute uncaptured authorizations, only fully captured payments."
  [Best practices](https://docs.stripe.com/disputes/prevention/best-practices), 2026-10-20. Two identical lines can
  be disputed only once both are taken.

**[ABSENT]** Whether an issuer declines or flags the second of two identical 40,00 zł authorisations from one
merchant seconds apart, and whether Radar's live model scores the second higher.

- **Looked, 2026-10-20:** the Radar rules, supported attributes, fraud best practices and dispute categories pages.
- The sandbox's issuer is simulated and approved all 21. Radar's outcomes in a sandbox come from its test cards
  ([`stripe-testing.md`](stripe-testing.md#radars-test-cards)).
- A question for Stripe support.

### 10 · R-FILL-37 · The window of a share refused off-session, then confirmed on-session with a typed card, on a live Visa

**Answer: 7 days by Stripe's table, counted from the charge that held. The sandbox shows it twice; live is
[ABSENT].**

- Carried **[DOCS]**:
  - the customer-initiated window is "7 days" for Visa, Mastercard, American Express and Discover;
  - "a payment with `off_session: true` might still be classified as a CIT if a CVC is present";
  - "The validity window won't change after the PaymentIntent is confirmed."
  - Sources: [`stripe-gaps-01.md`](stripe-gaps-01.md#r-fill-37-r-fill-61--after-the-player-confirms-stripes-table-gives-7-days-for-every-network-the-banks-check-case-is-still-unread),
    [`stripe-holds-and-capture.md`](stripe-holds-and-capture.md#capture_before-on-the-charge-is-the-window-to-trust-and-it-does-not-move-once-confirmed).
- **[MEASURED]** Two payments on the sandbox, both read via the SDK in the copy on 2026-10-20:
  - `pi_3USPIk5y1DMwE3zY03JvGogQ`, carried: 168,0 hours from the charge that held;
  - `pi_3USbiQ5y1DMwE3zY1mgot0SP`, new:
    - created 12:00:26 UTC on 2026-10-20, refused on Visa •••• 0341 the same second;
    - confirmed with a typed Visa •••• 4242 at 12:00:31 (`ch_3USbiQ5y1DMwE3zY1qvJxArB`);
    - `capture_before` 2026-10-27 12:00:31 UTC, exactly 168,0 hours after the charge that held, not after the
      payment's creation;
    - `cvc_check: pass`, `three_d_secure: null`.
- **[ABSENT]** The live window. A question for Stripe support. Live, the charge's `capture_before` settles it, and the
  code reads it (`stripe_payments.py:510-511`).

**Reading.** A typed card brings both signals Stripe names: the CVC is present, and the cardholder is there at that
moment. So Stripe's table gives the customer-initiated window, 7 days, on Visa too.

### 11 · R-FILL-2 · Does `stripe listen --forward-connect-to` keep printing club notices minutes after hosted onboarding ends

**Answer: yes, on this sandbox.** After the club submitted Stripe's form, the account's notices kept coming for
about 6½ minutes, then stopped.

**What the sandbox holds.** **[MEASURED]**, read via the SDK in the copy on 2026-10-20 as each account. These are
the v1 snapshot events, the kind the walk's `stripe listen` prints.

- **The test club `acct_1US95f5y1DMwE3zY`**, created 2026-10-19 05:26:32 UTC. It is the only sandbox account that
  finished hosted onboarding:

  | Time (UTC, 2026-10-19) | After the form was sent | Notices |
  |---|---|---|
  | 05:48:59 | 0 | `account.updated` (`details_submitted`, `tos_acceptance` changed: the form was sent), `evt_1US9RP5y1DMwE3zYfHBJoWJJ`, and two `capability.updated` (still `inactive`) |
  | 05:54:29 | +5 min 30 s | `capability.updated` transfers → `pending` and card_payments → `pending`; `account.updated` (`capabilities`), `evt_1US9Wj5y1DMwE3zYGLocyYBZ` |
  | 05:55:24–26 | +6 min 25–27 s | `account.updated` (`charges_enabled`, `payouts_enabled`), `evt_1US9Xc5y1DMwE3zYmCAPbbET`; `capability.updated` card_payments → `active` (`evt_1US9Xd5y1DMwE3zYvhmkNLVM`) and transfers → `active` (`evt_1US9Xe5y1DMwE3zY7iuDZhUY`) |
  | 09:01:10–09:02:13 | +3 h 12 min | 20 notices as eight more payment methods were requested and turned on (Bancontact, EPS, iDEAL, Klarna, Link, Pay by Bank, BLIK, Revolut Pay). `requested` is among their changed keys, so they come from a request made then, not from the onboarding |

  So nine Connect lines arrived in the 6½ minutes after the form, and the last of them is the one that turns card
  payments on.
- **Its v2 thin events** on the platform end with `v2.core.account[requirements].updated` at 05:55:39. The walk's
  `stripe listen` passes no thin flag, so it doesn't print them (`state.json` `stripe.walk`).
- **The seven other accounts the platform reaches** never finished onboarding. Each goes quiet within about a minute
  of its creation: notices at creation, a few more between 50 and 63 s later, then nothing. For example
  `acct_1USPFh5y1DXbCdOQ`: 22:42:00, 22:42:50–51 and 22:43:02 on 2026-10-19.

**What Stripe says.**

- Carried: the return from hosted onboarding "doesn't mean that all information has been collected"
  ([`stripe-connect.md`](stripe-connect.md#p2--calling-the-club-ready-from-the-return-url-or-a-stale-read)).
- **[DOCS]** [Testing Connect](https://docs.stripe.com/connect/testing), read 2026-10-20:
  - "Document tokens simulate the review process in production, so fields might appear in
    `pending_verification` before the result is applied."
  - The test bank account numbers complete their check "after a short delay".
  - No page gives a time.
- These notices print as `--> connect account.updated` and `--> connect capability.updated` (§6).

**[ABSENT]** A documented bound on how long a sandbox account's notices keep coming after onboarding. This sample
is one account; another onboarding may take longer.

**Reading.**

- A box that says "the listener prints nothing", walked within minutes of the club's onboarding, can meet these
  account lines.
- Until the club reads **Enabled**, the lines are `account.updated` and `capability.updated` only, never
  `payment_intent` or `charge`.
- On this sample, the club read **Enabled** with the last of them.
