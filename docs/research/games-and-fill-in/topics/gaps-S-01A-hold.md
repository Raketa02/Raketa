# Gaps round: the hold until the cut-off (S-01A refresh at 38f0e89a)

Answers the ten facts in `prd-530/stories/S-01A/rules-gaps.md`, each section naming the rules it grades. Everything
was read on 2026-10-11 unless a line says otherwise. Kinds: **[POLICY]** a company's own help, terms or served code;
**[DOCS]** a payment provider's, card network's or regulator's document; **[PRICE]**; **[LAW]**; **[MEASURED]** read by
this researcher (extract: [`../shots/gaps-S-01A-hold-2026-10-11.txt`](../shots/gaps-S-01A-hold-2026-10-11.txt));
**[COMPLAINT]**; **[ABSENT]** looked for and not found, with where.

Sources tried for each gap: the help centres (MATCHi's player and venue help through the Zendesk API, Playtomic's,
Booking.com's partner docs, Stripe's docs and support), the card networks' own merchant documents (Visa; Mastercard's
rulebook refused every automated read), the Polish banks' help pages and terms, Polish legal commentary and UOKiK,
NBP, the served web apps (tenis4U's visitor endpoints, Playmore's entry bundles, ten Kraków club home pages), payment
plug-ins and hotels that hold cards, and web search in English and Polish for forum and Reddit accounts.

Not redone, and cited where they matter: `gaps-S-01A-leave-fee.md` (Stripe's hold windows, fees, Polish law),
`gaps-S-01B.md` §1–§3 (Polish banks' hold terms, push opening times, bank checks), `gaps-FILL.md` §6, `gaps-POST.md` §2,
`gaps-LEAVE.md`, `gaps-S-01.md`, `gaps-S-02.md`.

---

## 1. R-LEAVE-44 (also R-PLATFORM-64, R-HOME-9, R-HOME-26, R-LEAVE-2): how soon a hold the shop let go leaves a Polish bank's app

### Visa: a reversal that matches tells the bank to lift the hold; one that doesn't leaves it 1 to 8 days
- **[DOCS]** "Authorization reversals notify the issuer that all, or part, of a sale has been cancelled and that the
  authorization hold should be released." "With missing or non-matching data elements, the issuer will not be able to
  match the authorization reversal to the original authorization. This means that the funds will remain outstanding
  for anywhere from 1 to 8 days, depending on the card and transaction type." "While some issuers will release an
  authorization hold with only a matching transaction identifer, others require the correct information in all four
  of the required data authorization felds" (STAN, RRN, authorisation code, transaction identifier). No time is given
  for a matched reversal beyond "as quickly as possible". [Visa: Authorization Reversals — the importance of providing
  the correct information (13 December 2019)](https://usa.visa.com/content/dam/VCOM/download/merchants/authorization-reversals.pdf)
  — read 2026-10-11
- *Reading:* cancelling the payment at Stripe sends the reversal; whether it reaches a Polish bank complete is Stripe's
  and the acquirer's work, not Rakieta's, and nothing published says it ever arrives incomplete.

### Stripe: some banks update the balance at once, others later
- **[DOCS]** "If a business releases a hold without capturing the payment, the available balance or credit updates when
  the issuer processes the change"; "some banks update available balances instantly, while others take a bit longer";
  the "delay reflects bank processing cycles, not business decisions"; "A hold can only be released by an issuer or the
  charging business, not the customer." [Stripe: Authorisation holds explained (last updated 27 February 2026)](https://stripe.com/gb/resources/more/authorization-holds-explained)
  — read 2026-10-11

### MATCHi tells players a cancelled booking's reserved amount is released within 24 hours, by their bank
- **[POLICY]** "The reserved amount is released. Your bank removes the hold on your card. This is not a transaction
  you'll see charged — it just disappears from your pending amounts." "The release is available within 24 hours of
  cancellation. MATCHi cannot speed this up — it's entirely on your bank's side. If you're waiting for the reserved
  amount to disappear and it's been more than 24 hours since cancellation, check with your bank first". MATCHi's cards
  go through Adyen; its markets are mostly Nordic, with none in Poland. [MATCHi: Why haven't I received my refund?
  (updated 2026-09-30)](https://matchiplayers.zendesk.com/hc/en-gb/articles/11452630118173-Why-haven-t-I-received-my-refund),
  [How we handle your card details](https://matchiplayers.zendesk.com/hc/en-gb/articles/11451033977117-How-we-handle-your-card-details)
  — read 2026-10-11

### Mastercard's issuer rule on a reversal could not be read
- **[ABSENT]** Mastercard's Transaction Processing Rules (the issuer's duties on a full reversal): the copies on
  mastercard.us and mastercard.com answered with a bot page, Moneris's mirror with an HTML page, the 2016 Australian copy
  with 403. Search found only issuers' and processors' descriptions of their own same-day handling — read 2026-10-11

### How soon each Polish bank's app drops a cancelled hold: still unpublished
- **[POLICY]** mBank: unsettled card payments "są od razu prezentowane w historii z kategoryzacją ze specjalnym
  oznaczeniem w kolumnie Typ", and "pełna lista blokad i zawieszeń dla poszczególnych rachunków jest widoczna w
  zakładce" Finanse › Historia › Blokady i zawieszenia; nothing on when a cancelled one leaves. [mBank: historia w
  serwisie transakcyjnym](https://www.mbank.pl/indywidualny/aplikacja-i-serwis/pytania-i-odpowiedzi-serwis/historia-w-serwisie-transakcyjnym/)
  — read 2026-10-11
- **[ABSENT]** PKO BP (its history page re-read: it says nothing on a hold settling or being cancelled), ING, Pekao,
  Erste and Millennium: searched again in Polish ("anulowanie transakcji przez sklep", "zwolnienie blokady", "blokada
  zniknie") across the banks' help pages, ING's community, Allegro's community and the web; no forum or Reddit account
  of a cancelled hold's timing at a named Polish bank was found. Carried: mBank lifts a hold when the cancellation
  arrives (`gaps-FILL.md#mbank-lifts-a-hold-when-the-merchants-cancellation-arrives-at-most-14-days-online`); the five
  banks' hold terms (`gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished`).
  What would answer it: on a real card from each bank, a small live hold placed and cancelled at once, with the bank
  app watched and the minutes written down — read 2026-10-11
- *Reading:* the only published timings are MATCHi's "within 24 hours", on its own banks, and Visa's 1 to 8 days for a
  reversal the bank cannot match. Neither says anything about how long a Polish bank keeps showing a hold.

---

## 2. R-LEAVE-44 (also R-HOME-45): which name a Polish bank app shows on a still-pending hold

### Visa requires the same merchant name on the hold as on the payment
- **[DOCS]** "Merchant data must be the same as, or consistent with, comparable data throughout a transaction's life
  cycle and on the transaction receipt." "Visa authorization and clearing systems provide 25 spaces in which to
  describe the Merchant name". A payment facilitator's transaction "may populate the Merchant name field with either
  the sponsored Merchant name (alone), or a combination of both … (e.g., Payment facilitator name*Sponsored Merchant
  name). It should choose the name that is the more recognizable to the cardholder." [Visa Merchant Data Standards
  Manual (April 2026), §1](https://usa.visa.com/dam/VCOM/download/merchants/visa-merchant-data-standards-manual.pdf)
  — read 2026-10-11
- Carried: on a direct charge Stripe sends the connected account's (the club's) descriptor
  (`gaps-POST.md#for-a-direct-charge-the-clubs-descriptor-goes-to-the-card-network`).
- *Reading:* on a Visa card the hold carries the club's name, as the payment later does. Mastercard's equivalent rule
  was not read.

### MATCHi tells players to tie a bank line to a booking by its number, not its name
- **[POLICY]** "Your bank transaction history shows a transaction number. Compare this to the receipt number for your
  booking in MATCHi to match the charge to the right booking." [MATCHi: How does payment work when booking? (updated
  2026-10-01)](https://matchiplayers.zendesk.com/hc/en-gb/articles/15599128235549-How-does-payment-work-when-booking)
  — read 2026-10-11

### What a Polish bank app prints beside a pending hold: still not found
- **[ABSENT]** PKO BP shows "ikonę kłódki i oznaczenie Blokada" and does not say whether the shop's name stands beside
  it ([PKO BP: zmiany w historii konta](https://www.pkobp.pl/aktualnosci/bankowosc-elektroniczna/zmiany-w-historii-konta-aplikacja-serwis),
  re-read); mBank marks unsettled card payments in the Typ column and does not say what text they carry (above).
  Searched: "blokada" with "nazwa sprzedawcy", "nazwa akceptanta", "STRIPE", "transakcje oczekujące", across PKO,
  mBank, ING and the web; Stripe's support page only covers a statement that reads "STRIPE"
  ([Stripe: FAQ for customers of businesses using Stripe](https://support.stripe.com/questions/faq-for-customers-of-businesses-using-stripe)).
  What would answer it: the same live hold as in §1, with a screenshot of each bank app's row — read 2026-10-11

---

## 3. R-LEAVE-44 (also R-PLATFORM-64): a second hold days after the first, a later debit that fails, and whether the provider objects

### MATCHi never places a second hold: past 7 days it takes the money and refunds the difference
- **[POLICY]** Player help: "We debit the amount either 12 hours after your playing time starts, or 7 days after the
  booking was created — whichever comes first." For a split booking made more than 7 days ahead: "We capture the full
  amount from the main booker after 7 days. We then refund the other players' share back to the main booker … This
  happens because many payment methods don't allow us to hold a reservation for longer than 7 days". [MATCHi: How does
  payment work when booking? (updated 2026-10-01)](https://matchiplayers.zendesk.com/hc/en-gb/articles/15599128235549-How-does-payment-work-when-booking)
  — read 2026-10-11
- **[POLICY]** Venue help: "A reservation is placed when the booking is created; the actual charge (capture) happens
  when the booking is played, or 7 days after the booking was created — whichever comes first. For a booking made well
  in advance where co-player shares aren't all settled by that point, the main booker is charged the outstanding
  amount, and any overpayment is corrected once co-players pay." [MATCHi venue help: How split payment pricing works
  for bookings (updated 2026-09-15)](https://matchi.zendesk.com/hc/en-gb/articles/14585367081757-How-split-payment-pricing-works-for-bookings)
  — read 2026-10-11

### MATCHi on a payment that fails: shown as failed, tried again on the same attempt
- **[POLICY]** "If your payment doesn't go through, the booking payment shows as failed and you'll need to try again —
  this reuses the same payment attempt rather than creating a new one." Same article — read 2026-10-11
- **[ABSENT]** What MATCHi does with the booking when the day-7 capture itself fails: neither help centre says.
  Searched through the Zendesk API, player side ("receipt", "debit", "payment failed", "declined", "charged", "card
  expired", "reserved amount") and venue side ("failed payment", "capture", "unpaid", "debit", "notification
  payment"); the venue articles *The payment process — Standard payments* and *Payments and orders* say a payment
  still waiting to be captured rolls into the next month's statement, and nothing about a capture that fails — read 2026-10-11
- *Reading:* a capture inside the hold's window takes money the bank has already set aside, so a failed day-7 debit is
  rare by design. MATCHi never meets the case of a second hold at all.

### Hotels and a Stripe plug-in do place a second hold
- **[POLICY]** "We will pre-authorise your card 48 hours prior to your arrival. We may then pre-authorise it again when
  you check-in, depending on the length of your stay". [King Charles Hotel: pre-authorisation](https://www.kingcharleshotel.co.uk/pre-authorisation/)
  — read 2026-10-11
- **[DOCS]** Amenitiz, a hotel system: the automatic hold is placed "on the day of arrival at 2 am" and "remains valid for
  30 days unless released or captured manually"; if the bank lets it go early, "you can also create a new
  pre-authorisation from the same place". [Amenitiz: automate AmenitizPay pre-authorisations (27 May 2026)](https://support.amenitiz.com/en/articles/332585-how-to-automate-amenitizpay-pre-authorisations)
  — read 2026-10-11
- **[DOCS]** OroCommerce's Stripe integration re-authorises uncaptured payments "that are about to expire": by default
  those "at least 6 days 20 hours old, but not older than 7 days". It creates a new Payment Intent on the stored
  payment method, then cancels the old one, and emails the shop if that fails. [OroCommerce 7.0: Re-Authorization of
  Uncaptured Payments](https://doc.oroinc.com/bundles/extensions/StripePaymentBundle/reauthorization) — read 2026-10-11
- *Reading:* a second hold on a saved card is ordinary in lodging and is built on Stripe by at least one commerce
  platform. None of them leaves days between letting the first hold go and placing the second, as Rakieta does between
  the fill's check and the holding time.

### Stripe documents reauthorisation only for in-person payments, and no objection to a new hold
- **[DOCS]** Stripe Terminal: `request_reauthorization` "Allows reauthorizing an expired PaymentIntent to obtain a new
  authorization", with the value `IF_AVAILABLE` ("reauthorization will be requested if the card and payment method
  support it"). This is a card-present setting. [Stripe Terminal SDK reference](https://stripe.dev/stripe-terminal-java/external/com.stripe.stripeterminal.external.models/-card-present-parameters/request-reauthorization.html)
  — read 2026-10-11
- **[ABSENT]** For online payments, no Stripe page forbids, limits or prices a new off-session hold on a saved card
  after an earlier one was cancelled. Carried: `gaps-S-01A-leave-fee.md#renewing-a-hold-is-not-documented`. Searched
  this round: Stripe's hold, refunds, Smart Retries and decline-code pages — read 2026-10-11

### The card networks' limits apply to retried declines and to checking a card with an amount
- **[DOCS]** Visa (7 November 2019): acquirers must "Ensure that their merchants use account verification instead of
  authorizations for erroneous amounts when validating cardholder accounts. This includes the addition of an account
  number to the customer profile (credential-on-file) and periodic revalidation of stored credentials." [Visa:
  Proper Account Verification Message Processing Reminders, AI09481](https://bz.review.visa.com/content/dam/VCOM/global/support-legal/documents/account-verification-vbn.pdf)
  — read 2026-10-11
- **[DOCS]** Stripe: "Card networks may also restrict 1 USD authorizations you don't intend to capture."
  [Stripe: Place a hold on a payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-11
- **[DOCS]** A processor's summary of Visa's rule: no more than 15 reattempts of a declined transaction (decline
  categories 2 and 3) in 30 days, none after a category 1 decline; "As of April 2022, Visa assess fees on decline
  reattempts". [Payway: Visa Excessive Reattempts Rule & Fees](https://www.payway.com/visa-excessive-reattempts-rule-fees)
  — read 2026-10-11
- *Reading:* a second hold for the real share at the holding time is an ordinary authorisation, and no network rule
  read limits it. The fill's check is the act these rules touch: a full-share hold let go within seconds. Visa asks for
  a zero-amount verification when the purpose is to validate an account, but a zero amount cannot test whether the
  money is there. Whether Visa would treat a full-share check as an authorisation for an "erroneous amount" is not
  stated anywhere read.

---

## 4. R-LEAVE-43: what MATCHi tells a player when it takes the money later

### The receipt appears in the app once the money is taken; no notice or email at that moment is described
- **[POLICY]** "When you pay by card for a booking, MATCHi reserves the amount on your account right away, but the
  money isn't actually taken until later." [How does payment work when booking?](https://matchiplayers.zendesk.com/hc/en-gb/articles/15599128235549-How-does-payment-work-when-booking)
  — read 2026-10-11
- **[POLICY]** "You'll find all your receipts under your profile, both in the app and on the web" (Profile › … ›
  Payments); "Receipts appear only once your payment has gone through — a payment that's still processing won't show a
  receipt yet. If a refund is issued later, it shows up on the same receipt as a line item". [MATCHi: Receipts (updated
  2026-09-16)](https://matchiplayers.zendesk.com/hc/en-gb/articles/14720788897693-Receipts) — read 2026-10-11
- **[POLICY]** The email MATCHi documents is the booking's: "players will receive just one booking confirmation email
  and one cancellation fee". [MATCHi: New Checkout and Payment methods (updated 2026-09-24)](https://matchiplayers.zendesk.com/hc/en-gb/articles/14384467304989-New-Checkout-and-Payment-methods)
  — read 2026-10-11
- **[ABSENT]** A push, in-app notice or email when MATCHi takes the money on day 7 or 12 hours after play. None of the
  player articles searched in §3, nor the venue articles on the payment process, orders and split payments, mentions
  one. What would answer it: a real MATCHi booking made more than 7 days ahead, with the inbox and the app watched on
  day 7 — read 2026-10-11
- *Reading:* MATCHi documents a debit that is silent apart from a receipt appearing in the app. Rakieta's quiet row and
  emailed receipt are at least level with it, and the emailed receipt is more than MATCHi describes.

---

## 5. R-LEAVE-45 (also R-HOME-46): how fast a player answers a payment-problem notice, and how often a Polish bank refuses or asks on a charge made without her

### Booking.com gives a guest 24 hours to replace an invalid card
- **[DOCS]** After a property reports an invalid card: "If the guest didn't update the card details within 24 hours", the
  property receives a `CREDIT_CARD_STATUS_UPDATE` notice, and if the card is still `INVALID_CARD` it can "use Extranet
  to cancel the reservation". [Booking.com connectivity: Understanding the Credit Card Status API ("Last updated 1
  month ago")](https://developers.booking.com/connectivity/docs/credit-card-status-api/understanding-the-credit-card-status-api)
  — read 2026-10-11
- **[ABSENT]** Shorter windows close to check-in: a channel manager's help page said to list them answered 403, and
  Booking.com's own page names only the 24 hours — read 2026-10-11
- Carried: Airbnb also gives 24 hours (`gaps-RESCUE.md#airbnb-blocks-the-dates-for-24-hours-while-the-guest-fixes-a-failed-payment`);
  Playmore counts 30 minutes from the booking's creation
  (`gaps-S-01B.md#playmore-counts-the-30-minutes-from-the-bookings-creation-never-against-its-start`).

### No newer figure on how fast people open a notice
- **[ABSENT]** Airship's 2026 benchmarks (data January–December 2025; apps with at least 1,000 active users) give opt-in
  and direct-open rates by vertical and no time to open ([Airship: push notification benchmarks for 2026](https://www.airship.com/mobile-app-push-notification-benchmarks-for-2026/));
  MoEngage's 2025 report on transactional messages gives only an "Average Push Notification delivery time" of 1.3 s
  ([MoEngage: The State of Transactional Messaging 2025](https://www.moengage.com/industry-reports/state-of-transactional-messaging-inform-benchmarks/)).
  Nothing found for Poland, or for payment notices as against marketing ones. Carried: medians of 7 minutes on an
  iPhone and 48 on Android (2016; `gaps-S-01B.md#people-open-a-push-in-about-7-minutes-on-an-iphone-and-48-on-android-2016-vendor-figure`)
  — read 2026-10-11

### How often a Polish bank refuses or asks on a charge made without the player: still not found
- **[ABSENT]** Searched "soft decline" with Poland, "MIT exemption" with Polish banks, UOKiK's and KNF's 2024
  recommendations on fraud and the reporting on them: they cover monitoring and limits, never a rate for charges made
  without the cardholder. Carried: such charges were 22 % of EEA remote card payments taken without the bank's check
  in 2024, and 87 % of Polish bank checks succeed
  (`gaps-S-01B.md#eea-2024-charges-made-without-the-payer-were-22-per-cent-of-remote-card-payments-taken-without-the-banks-check`,
  `gaps-S-01B.md#when-a-polish-cards-bank-does-ask-about-87-per-cent-of-checks-succeed`). What would answer it: the
  decline codes and notice-open times on Rakieta's own account once live — read 2026-10-11

---

## 6. R-PLATFORM-66 (also R-LEAVE-6): a Kraków club on its own negotiated pricing, and whether its fee ever reaches the payment

### No Kraków club was found taking card payments through Stripe today
- **[POLICY]** Carried: tenis4U takes online payments through Przelewy24 and Tpay, and kluby.org through Przelewy24 and
  PayU; Atras and Squash4You, on Playmore/Reservise, name Przelewy24
  (`gaps-PLATFORM.md#which-gateways-kraków-clubs-use-today`, `local-market.md#the-club-is-the-seller-the-platform-is-not-a-party`).
  Playmore's own booking page shows Autopay (`../games-and-fill-in-market.md`, *Playmore (formerly Reservise …)*).
  Playtomic, whose clubs hold Stripe accounts, has no club in Kraków
  (`competitor-organiser.md#playtomic-has-no-club-in-krakow`).
- **[MEASURED]** The home pages of Fame Sport, Garden Padel, Squash4You, Atras, Miazga, SAO, Bajada, Padel Lounge and
  Playmore name no payment provider at all; kluby.org's names Przelewy24 and PayU. Extract §D — read 2026-10-11
- *Reading:* a club joins Rakieta by opening a fresh Stripe account on standard pricing. A club on negotiated pricing
  would have to bring an existing high-volume Stripe account, and none of Kraków's clubs is known to have one.

### Negotiated pricing, IC+ among it, is arranged through sales for large volumes
- **[PRICE]** Stripe Poland: custom packages are "available for businesses with large payments volume or unique
  business models"; "Eligibility varies by market"; IC+ is listed among the "Flexible structures". No threshold is
  published. [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-11

### On standalone fees a payment's own fee stays at zero, and the fee for it appears in the Fees report within days
- **[DOCS]** Accounts "might transition to standalone fees … for reasons such as custom pricing (for example, tiered
  pricing) or Stripe fee credit awards". Then "We create a single balance transaction for each transaction that only
  includes the total charge amount, with fees set to zero. Within 36 hours of the charge, we create a second
  fee-specific balance transaction with the aggregate fees of all transactions"; "The aggregated amounts are accurate,
  but they aren't tied to the individual transactions." In the Dashboard each payment's fee "might take up to 2 hours";
  "You can view per-transaction fees in the Fees report". [Stripe: Standalone fees](https://docs.stripe.com/standalone-fees)
  — read 2026-10-11
- **[DOCS]** "Fee data becomes available within 96 hours after a fee affects your balance." Each itemised row carries
  `incurred_by` (for example a charge ID); the report runs through the Reporting API as `all_fees.incurred_at.itemized.2`,
  and "You can also query transaction-level fee data in the Sigma itemized_fees table." [Stripe: Fees report](https://docs.stripe.com/reports/all-fees)
  — read 2026-10-11
- Carried: "IC+ users can't retrieve payment fee information from the balance transaction. Use the Payment fees report
  instead." (`gaps-S-01A-leave-fee.md#the-fee-exists-only-after-capture-and-reads-late-or-zero-for-a-club-on-its-own-pricing`)
- **[ABSENT]** Whether a platform can run a connected account's Fees report: report runs accept a connected-account
  parameter, but Stripe's pages do not say which report types honour it. [Stripe: How the Reports API works](https://docs.stripe.com/reports/api)
  — read 2026-10-11
- *Reading:* for a club on such pricing, a refund that waits for the fee on the payment itself waits for ever. One that
  reads the Fees report waits up to about four days (36 hours for the fee to be applied, then up to 96 hours for the
  report).

---

## 7. R-LEAVE-6 (also R-HOME-26): is keeping the provider's fee back from a personal EU card's refund after the cut-off a banned charge for using the card? (for the lawyer, spec O3)

### No authority was found ruling on a fee kept back from a refund
- **[ABSENT]** EBA's Single Rulebook Q&A: no answer on art. 62(4) PSD2 and refunds, and questions sent before 2020 were
  rejected unanswered. Polish commentary on art. 37a UUP (bank.pl, lexlege, arslege) only restates the text. UOKiK's
  2025 PayPal decisions concern changing fees, not refunds. No court ruling was found on a refund "pomniejszony o
  prowizję" or "opłatę transakcyjną". Carried: the Commission reads the fee rule as covering any fee "linked to a means
  of payment, regardless of how they are presented", and no judgment was found
  (`gaps-S-01A-leave-fee.md#a-fee-for-using-a-personal-eu-card-is-banned-outright-other-cards-are-capped-at-cost`)
  — read 2026-10-11
- **[POLICY]** Carried, the Kraków status quo: tenis4U refunds a cancelled online booking "pomniejszonych o opłatę
  transakcyjną w wysokości 2%", and Garden Padel refunds "z potrąceniem opłaty serwisowej operatora płatności (2%)",
  whatever the method used (`local-market.md#the-refund-deduction-players-already-know-a-flat-2-`). No UOKiK action
  against either was found — read 2026-10-11
- *Reading:* the question stays with the lawyer. What the market shows is that Kraków's own systems already keep a
  payment operator's fee from refunds, a flat 2 % on every method, unchallenged as far as could be found.

---

## 8. R-LEAVE-46: how many cards hold for less than about 4 days 6 hours when the hold is placed without the player

### Stripe's published windows: Visa's 4 days 18 hours is the shortest
- **[DOCS]** Card-not-present holds, merchant-initiated against customer-initiated: Visa "5 days\*" against "7 days";
  Mastercard, American Express and Discover 7 against 7; "\* The exact authorization window is 4 days and 18 hours".
  "Stripe and the card network classify transactions as MIT or CIT based on signals of cardholder participation, not
  solely on API parameters like off_session. For example, a payment with off_session: true might still be classified
  as a CIT if a CVC is present, resulting in the CIT authorization window instead." The charge's
  `payment_method_details.card.capture_before` "indicates when the authorization expires". [Stripe: Place a hold on a
  payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-11 (re-read; the
  same table as `gaps-S-01A-leave-fee.md#an-off-session-visa-hold-lasts-4-days-18-hours-mastercard-7-days`)

### Cards issued in Poland are almost all Visa or Mastercard
- **[DOCS]** NBP, end of Q3 2022: Visa 53,3 % of cards issued in Poland, Mastercard 46,5 %. This was read through the
  search engine's extract, because nbp.pl and the Internet Archive's copies refuse an automated read, and the Q3 2025
  report's split by network could not be opened. [NBP: Informacja o kartach płatniczych, III kwartał 2022](https://nbp.pl/wp-content/uploads/2023/02/q_03_2022.pdf)
  — read 2026-10-11
- *Reading:* by the published windows, no card a Kraków player is likely to hold lets a hold placed without her lapse
  before 4 days 18 hours, which is 12 hours more than the 4 days 6 hours the holding time needs. The fallback fires
  only where a particular charge's `capture_before` comes earlier than the table says.
- **[ABSENT]** How often a live charge's `capture_before` comes earlier than the table: no source publishes a spread.
  What would answer it: the `capture_before` of Rakieta's own live holds, logged per card brand and bank — read 2026-10-11

---

## 9. R-HOME-11 (also R-HOME-39, R-HOME-45, R-LEAVE-20): how far ahead Kraków groups book

### On weekday evenings most court-hours are taken more than a week ahead
- **[MEASURED]** In the five Kraków padel grids read on 9 October, weekday evenings (17:00–22:00, Monday to Thursday)
  10 to 13 days ahead were already 57 % taken (179,5 of 317 court-hours), against 74 % for evenings 3 to 6 days ahead
  (235,5 of 319). Without Padel House, which is full at every distance, the figures are 42 % against 65 %. By club, at
  10–13 days and then 3–6 days: Garden Padel 26 % → 67 %, Fame Sport 71 % → 88 %, Bajada 40 % → 55 %, Padel Lounge
  59 % → 63 %. Computed from the carried read
  (`gaps-S-01.md#five-kraków-padel-clubs-how-much-of-the-next-two-weeks-weekday-hours-is-already-taken`); extract §B
  — computed 2026-10-11 from the read of 2026-10-09
- *Reading:* about three quarters of what is taken on a weekday evening 3 to 6 days out was already taken 10 to 13 days
  out (57 of 74). That makes a booking a week or more ahead the usual case for a club's evening hours. The figure counts
  standing weekly slots and classes too, and two different weeks are compared at one moment, so it is a cross-section
  rather than one evening followed over time.

### MATCHi: most venues open bookings 14 to 28 days ahead
- **[POLICY]** "Most venues and clubs allow booking somewhere between 14 and 28 days in advance, but the exact limit is
  entirely up to the venue." [MATCHi: How far in advance can I book? (updated 2026-09-16)](https://matchiplayers.zendesk.com/hc/en-gb/articles/11451466309021-How-far-in-advance-can-I-book)
  — read 2026-10-11
- Carried: Kraków padel clubs on tenis4U take bookings 14 days ahead, Fame Sport 30 and Padel SPOT 7
  (`gaps-POSTGRID.md#tenis4u-most-kraków-padel-clubs-take-bookings-14-days-ahead-two-take-30-one-7`).

### This round's read of the same grids served no free hours
- **[MEASURED]** At 12:48 on 11 October, tenis4U's visitor endpoint returned no free hour on any of the 600 court-days
  (every sport) it served for the five clubs, as on the evening of 10 October, so no fresh booking curve could be taken. Extract §A — read 2026-10-11

### How far ahead a group settles its own game: still not found
- **[ABSENT]** Kraków WhatsApp and Facebook groups need a login (`platforms.md#kraków-groups-could-not-be-read`). No
  platform publishes booking lead times: a search for padel lead-time statistics found only clubs' booking windows and
  unsourced blog figures. Playmore's "3 razy częściej" for games set up 3 or more days ahead remains its own claim
  (`gaps-LEAVE.md#no-platform-or-club-publishes-a-late-fill-or-resale-rate`) — read 2026-10-11

---

## 10. R-LEAVE-21: how often a fourth is found in a game's last 24 hours

### Still published nowhere
- **[ABSENT]** Not found in Playtomic's player help or Manager help (configuring, managing and, new in 2026, creating
  open matches from Manager), in a search for open-match completion figures (2025–2026), or in Playmore's served web
  app: its entry bundles hold no call that lists a club's or a city's open games for a visitor (extract §C; the
  lazy-loaded chunks were not read). tenis4U's grids now serve no free hours (§9). Carried: no platform or club
  publishes a late-fill or resale rate (`gaps-LEAVE.md#no-platform-or-club-publishes-a-late-fill-or-resale-rate`);
  about one free weekend hour in ten sold over the last day
  (`gaps-S-02.md#over-the-last-day-about-one-free-weekend-hour-in-ten-was-sold`). What would answer it: reads of Kraków
  clubs' Playmore open games at 48, 24 and 2 hours before each start (this needs the list call from Playmore's lazy
  chunks, or a signed-in session), or Rakieta's own fills once live — read 2026-10-11

---

## Still open

- How soon each Polish bank's app drops a hold that was let go, and what name it prints beside one still pending
  (§1, §2). A small live hold per bank answers both.
- What MATCHi does when a day-7 capture fails, and whether it tells the player when it takes the money (§3, §4). A real
  booking made more than 7 days ahead answers both.
- Whether Stripe objects to a second hold placed days after a first was let go, and whether Visa would treat a
  full-share check as an authorisation for an "erroneous amount" (§3).
- How fast a Polish player answers a payment notice, and how often a Polish bank refuses or asks on a charge made
  without her (§5). Rakieta's own data once live answers both.
- Whether a platform can run a connected club's Fees report through the API (§6).
- The lawyer's reading of art. 37a ust. 3 UUP on a fee kept back after the cut-off (§7).
- How often a live hold's `capture_before` comes earlier than the published window (§8).
- How far ahead Kraków groups settle a game, and how often a fourth is found in the last 24 hours (§9, §10).
