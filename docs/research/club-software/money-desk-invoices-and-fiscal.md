# Money at the club: online, at the desk, invoices and the cash register

Research for area 11 (money) of the planning map *Rakieta becomes the club's booking software*. It
covers what a Kraków club needs from one system to take, record, refund and pay out every złoty, and
what Polish tax law asks of each sale.

**Extends** [`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md)
(*Payment methods*, *Stripe Connect in Poland*, *Receipts, invoices and fiscal rules*),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) (§9, §10),
[`../games-and-fill-in/areas/CLUBMONEY.md`](../games-and-fill-in/areas/CLUBMONEY.md),
[`../games-and-fill-in/areas/PAY.md`](../games-and-fill-in/areas/PAY.md),
[`../games-and-fill-in/topics/gaps-CLUBMONEY.md`](../games-and-fill-in/topics/gaps-CLUBMONEY.md),
[`../games-and-fill-in/topics/gaps-PAY.md`](../games-and-fill-in/topics/gaps-PAY.md) and
[`integration.md`](integration.md). Facts carried from those files keep their dates. Everything else
was read on **2026-10-12**.

**This file decides nothing.** Each feature will be decided in the club-software grilling as *Build at
launch*, *Build later*, *Leave out* or *Ask a real club*.

**Sources.**
- **Stripe.** The docs were read as the Markdown that docs.stripe.com serves. Prices come from
  stripe.com/en-pl/pricing.
- **Polish law.** Laws and regulations were read in the Sejm ELI texts (api.sejm.gov.pl), using the
  consolidated VAT Act of 28 September 2026 (Dz.U. 2026 poz. 1263).
- **Tax rulings.** Rulings were read through the Ministry of Finance's Eureka public API. Each one links
  to its eureka.mf.gov.pl page.
- **Playtomic and MATCHi.** Their help centres were read through the public Zendesk API.
- **Playmore, kluby.org and fiscal-printer vendors.** Their public pages were read.
- **tenis4U.** Text comes from the JavaScript its public club-panel demo (test-panel.tenis4u.pl) serves
  to every visitor. It was fetched once and searched for words; tenis4U's terms (§7) forbid automated
  reading of its site, which this single read for research stays close to.

Nobody signed in, booked or paid, and no endpoint that writes was called.

**Kinds:**
- `[POLICY]` a company's own rule, help page or interface text.
- `[PRICE]` a published price.
- `[DOCS]` a provider's developer or merchant document.
- `[LAW]` an act, a regulation, or a tax ruling (interpretacja indywidualna, WIS) at its source.
- `[COMPLAINT]` one person's account.
- `[ABSENT]` looked for and not found, saying where.

Lines marked *reading* are inferences, not sources. Polish is quoted in Polish with an English gloss.

## Read this first

- **Online, BLIK and Przelewy24 cannot be held.** On Stripe, BLIK and P24 do not support manual
  capture, so only a card or a wallet card can be authorised now and taken later. A player paying a
  whole court by BLIK is charged at once, and any refund later comes out of the club's balance.
  ([BLIK](https://docs.stripe.com/payments/blik), [P24](https://docs.stripe.com/payments/p24))
- **A desk payment link can expire; a Stripe Payment Link cannot.** A Checkout Session takes
  `expires_at` "anywhere from 30 minutes to 24 hours", and both BLIK and P24 work in Checkout.
  - tenis4U deletes an unpaid booking after 60 minutes.
  - MATCHi keeps a payment link valid for 240 days and never releases the hour.
- **Stripe Terminal is in Preview in Poland; Tap to Pay is generally available.** Poland is under
  "Available in (Preview)" for card readers. It is in the plain availability list for Tap to Pay on
  iPhone and on Android. In-person pricing in PL is 1,4 % for EEA cards, plus 0,40 zł per Tap to Pay
  authorisation. Terminal takes no BLIK.
- **No rival found integrates a card terminal.** Every one found records "paid by card at the desk"
  by hand: Playtomic's "Credit Card" method, tenis4U's `CARD_TERMINAL`, and Playmore's "karta".
  Polish bank terminals cost 0,55 % (PKO) to 1,49 % (SumUp) a card with no fixed fee
  (carried, 2026-10-08).
- **The law no longer asks for a terminal-to-register link.** It was abolished from 1 April 2025. The
  card acquirer now reports every terminal transaction to the tax authority (KAS) instead.
- **A Kraków club needs a cash register for every consumer sale it does not take fully online.**
  - The online exemption (annex poz. 42) needs the whole price paid through a bank or payment
    institution, with records tying each payment to its sale. A deposit online plus the rest at the
    desk puts the sale on the register.
  - The 20 000 zł threshold counts online sales too, so almost no padel club falls under it.
  - Court hire is not excluded from the exemptions. A café or bar, and alcohol above 1,2 %, are
    excluded: they need a register from the first złoty.
- **Court hire may not use a software (virtual) register; the bar may.** Software registers are
  allowed for gastronomy (PKWiU 56), accommodation, transport and, from 1 April 2026, unattended
  devices. Sports-facility services are not on the list.
- **KSeF is in force, but club invoices to consumers stay outside it.**
  - Structured invoices have been mandatory since 1 February 2026 (big firms) and 1 April 2026
    (everyone else).
  - A taxpayer invoicing at most 10 000 zł gross a month may stay outside KSeF until 31 December 2026.
  - Penalties start on 1 January 2027: up to 100 % of the VAT, or 18,7 % of the gross amount.
  - Invoices to consumers need not go through KSeF. Stripe Invoicing "doesn't generate or transmit
    legally compliant e-invoice files".
- **Court hire is 8 % VAT. Lessons are 8 % or 23 % depending on who sells them and how.**
  - Rulings put court hire, passes (karnety), and a racket hired with the court at 8 % (PKWiU
    93.11.10.0, annex 3 poz. 55).
  - Group lessons went 8 % when a hall operator sold court plus coach as one service. They went
    23 % (PKWiU 85.5) when a coach sold the teaching.
  - A non-profit sports club's classes can be VAT-exempt, but its court rental cannot.
- **Rivals split along money lines.**
  - Playmore has a POS with bar and stock, invoices through Fakturownia ("gotowość na KSeF"), and
    daily payouts after the game.
  - kluby.org drives a fiscal printer and sends e-receipts.
  - tenis4U records cash and card at the desk but issues no receipt or invoice.
  - Playtomic has a POS and an invoicing tool but "no integration with POS printers" and nothing
    Polish.
- *Reading:* nobody found offers what the law makes hardest: fiscal receipts for desk sales, plus a
  KSeF invoice on demand, plus an online exemption that holds up in an audit. Playmore comes closest on
  invoices and kluby.org on receipts.

---

## 1. A player pays the whole court online

**What it covers.** A player (or a desk-made booking) pays the full court price online. This covers
the methods Poles use, their fees on a Polish connected account, whether each can be held, refund
speed by method, and disputes. All of it runs on Stripe Connect direct charges, where the club is the
seller.

**Who has it**
- **Playtomic Manager.** Card, prepaid card, Apple Pay, Google Pay and Club Wallet are processed
  through Stripe. Local methods exist only in SE, FI, BE/NL, DE and PT, and Poland is in no list
  (**[POLICY]** [Payment methods, updated 2026-10-05](https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281)).
  It has no Kraków club (carried, `local-market.md`, 2026-10-06).
- **Playmore.** "Przedpłaty i kaucje — Karta lub BLIK przy rezerwacji. Brak płatności = brak
  rezerwacji" — prepayments and deposits, card or BLIK at booking; no payment, no booking
  (**[POLICY]** [dla klubów padla](https://join.playmore.pl/dla-klubow-padla/)). It charges 1,79 % on
  online payments (**[PRICE]** [cennik](https://join.playmore.pl/cennik/)). The money passes through
  Reservise's account (carried, `platforms.md`, 2026-10-07).
- **tenis4U.** "Płatność realizowana jest przez system płatności Przelewy24.pl oraz Tpay.com", through
  each club's own P24 merchant keys (carried, `integration.md`, 2026-10-12). Its panel's payment
  methods include `Przelewy24` (**[POLICY]** [club-panel demo bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **kluby.org.** Online payments go through Przelewy24 and PayU, "opłaty za rezerwacje: dobrowolne lub
  wymagane 25%/50%/100%" — booking fees optional or required at 25/50/100 %, at "Prowizja 2%"
  (**[POLICY]**/**[PRICE]** [integracje](https://oferta.kluby.org/integracje)).
- **MATCHi.** Payments run through Adyen and include no Polish method (carried, `platforms.md`,
  2026-10-06).

**The desk's day with it.** The desk does nothing for a prepaid booking: it lands in the calendar paid.
Playmore's case study says a club moved "z około 20% do 100% płatności online" — from about 20 % to
100 % online — and in its FAQ, "recepcja nadal przyjmuje gotówkę, kartę i przelew" — the desk still
takes cash, card and transfer (**[POLICY]** [join.playmore.pl](https://join.playmore.pl/)).

**What a Kraków desk does today**
- **[POLICY]** Garden Padel: "Rezerwacja jest ważna po dokonaniu płatności online (Przelewy24) lub w
  recepcji (karta/gotówka)" — a booking stands once paid online through P24 or at reception, card or
  cash ([regulamin](https://gardenpadel.pl/regulamin)).
- **[POLICY]** Squash4You: "Opłaty za rezerwację dokonać można on-line (Przelewy24) lub przelewem oraz
  bezpośrednio w recepcji klubu gotówką lub kartą" — online through P24, by transfer, or at reception
  in cash or by card ([regulamin](https://www.squash4you.pl/regulamin)).
- Online is cheaper than the desk at Atras (40 zł against 49 zł) (carried, `local-market.md`,
  2026-10-06).

**What it means for the player app**
- **[DOCS]** BLIK works in Checkout, Payment Links and the Payment Element, and with Connect. "Express
  Checkout Element doesn't support BLIK." A BLIK code "is valid for 2 minutes; customers have 60
  seconds to authorize" ([Stripe: BLIK](https://docs.stripe.com/payments/blik)).
- **[DOCS]** P24 works in Checkout, Payment Links, the Payment Element and in-app, and with Connect,
  but not with `setup_future_usage` or SetupIntents ([Stripe: P24](https://docs.stripe.com/payments/p24)).
- **[DOCS]** With direct charges the platform must register every web domain that shows Apple Pay,
  Google Pay or Link, separately for each club: "If the platform creates direct charges, use your
  platform's secret key … and set the Stripe-Account header to your connected account's Stripe ID"
  ([Stripe: register domains](https://docs.stripe.com/payments/payment-methods/pmd-registration?dashboard-or-api=api)).
- *Reading:* a whole court paid by BLIK is a charge, not a hold. Only cards and wallet cards can be
  authorised now and taken at a cut-off.

**Market signal**
- **[DOCS]** In remote payments BLIK is about half of all transactions and cards a quarter (NBP 2023).
  Of online shoppers, 64 % use BLIK and 37 % a card (Autopay 2025) (carried, `local-market.md`,
  2026-10-07).
- **[COMPLAINT]** "lack of possibility in payment with BLIK is disappointing" — said of Playtomic
  (carried, `areas/PAY.md`, 2026-10-08).

**What the law requires**
- **[LAW]** Before the player is bound: the seller's identity and address, the total price, how
  payment is taken, and that a dated sports booking has no withdrawal right. The order button must say
  it obliges payment. (Ustawa o prawach konsumenta art. 12, 17, 38 pkt 12; carried, `local-market.md`,
  2026-10-06/07.)

**Stripe facts by method** (read 2026-10-12 unless dated)

| | Cards, Apple Pay, Google Pay | BLIK | Przelewy24 |
| --- | --- | --- | --- |
| Fee on a PL account ([pricing](https://stripe.com/en-pl/pricing)) | 1,5 % + 1,00 zł standard EEA; 1,9 % + 1,00 zł premium EEA; 2,5 % + 1 zł UK; 3,25 % + 1 zł international (+2 % with conversion) | 1,6 % + 1,00 zł | 1,9 % + 1,00 zł |
| Connect | yes | yes, `blik_payments` capability ([BLIK](https://docs.stripe.com/payments/blik)) | yes ([P24](https://docs.stripe.com/payments/p24)) |
| Hold, then capture | yes; 4 d 18 h to 7 days (carried, 2026-10-06) | "Manual capture support: No" | "✗ Manual capture" |
| Refund speed | "approximately 5-10 business days"; an early refund is a reversal ([refunds](https://docs.stripe.com/refunds)) | "immediately or within a couple of hours", depending on the bank | "up to 3 business days", within 180 days; "never issued as a reversal" |
| Disputes | 90 zł received, 90 zł to counter; Smart Disputes 30 % of a won amount ([pricing](https://stripe.com/en-pl/pricing)) | BLIK's own claims process; evidence "within 12 calendar days"; Stripe "holds back the disputed amount" | "you won't have disputes that turn into chargebacks" |
| Club as seller | descriptor of the connected account (carried) | "Direct — Connected Account" descriptor in the banking app | — |

- **[DOCS]** P24 asks more of the club's website. It "must display the tax identification number …
  the business registration number … the return and refund policy … a privacy policy … terms of
  service". MCC 7941 *Sports Clubs/Fields* is "Restricted", meaning it needs more information at
  account creation ([Stripe: P24](https://docs.stripe.com/payments/p24)).
- **[DOCS]** "Refunds can only be sent back to the original payment method used in a charge. You
  can't send a refund to a different destination" ([Stripe: Refunds](https://docs.stripe.com/refunds)).

---

## 2. A payment link for a booking made at the desk or by phone

**What it covers.** The desk books an hour for someone who will pay remotely. It sends a link, and
releases the hour if nobody pays in time.

**Who has it**
- **tenis4U.** "Użytkownik otrzyma link do płatności. Rezerwacja zostanie usunięta jeśli płatność nie
  zostanie wykonana w ciągu 60 minut." — the user gets a payment link, and the booking is deleted if
  not paid within 60 minutes (**[POLICY]** carried, `integration.md`, 2026-10-12). It also offers
  "Ile godzin przed startem anulować nieopłacone rezerwacje" — how many hours before the start to
  cancel unpaid bookings.
- **MATCHi.** A booking's payment method can be "payment link". The customer "Receives an email with
  payment instructions" and must log in. "Payment links remain valid for up to 240 days … For
  bookings, the payment link does not expire when the booked time has passed" (**[POLICY]**
  [Working with payment links, updated 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/14858820219165)).
  An order can sit as "Unpaid payment link" (**[POLICY]** [Payments and orders](https://matchi.zendesk.com/hc/en-gb/articles/26122506946845)).
- **Playmore.**
  - **[POLICY]** An online booking lapses unpaid after 30 minutes, counted from creation (carried,
    `platforms.md` and `areas/PAY.md`, 2026-10-08/10).
  - **[POLICY]** The player's account has "Rozliczenia — Przeglądaj i opłacaj zaległe rozliczenia za
    rezerwacje" — browse and pay outstanding settlements for bookings (carried, `gaps-CLUBMONEY.md`,
    2026-10-08).
  - **[ABSENT]** A link the desk sends: nothing on join.playmore.pl.
- **Playtomic Manager.** **[ABSENT]** No payment-link article: a help search for "payment link"
  returned only payments and billing pages
  ([search](https://helpmanager.playtomic.com/api/v2/help_center/articles/search.json?query=payment%20link&locale=en-gb)).
- **kluby.org.** **[ABSENT]** Nothing on the integrations, features or changelog pages.

**The desk's day with it.** In tenis4U the desk picks "Gość" (guest) or a user and chooses the link.
The hour holds for an hour, then frees itself. MATCHi's desk activates the link and chases unpaid
orders by hand.

**What a Kraków desk does today.** Phone bookings at tenis4U clubs either use this link or are marked
"Recepcja oznaczy płatność przy kasie" — the desk will mark it paid at the till (**[POLICY]**
[panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).

**What it means for the player app.** The link would open the club's checkout on the web, or the app
if installed. MATCHi requires a logged-in, matching customer; tenis4U sends it to the user.

**Market signal.** *Reading:* tenis4U's 60 minutes and Playmore's 30 are the local expectation. MATCHi's
240 days suits invoiced, not walk-up, customers.

**What the law requires**
- **[LAW]** A link paid in full through a bank or payment institution can fall under the online
  cash-register exemption (§ 9 below). A link paid partly, with cash on arrival, puts the whole sale
  on the register.

**Stripe facts**
- **[DOCS]** Checkout Session `expires_at` "can be anywhere from 30 minutes to 24 hours after Checkout
  Session creation. By default, this value is 24 hours". A session can also be expired at once
  through `/v1/checkout/sessions/{id}/expire`. Stripe sends `checkout.session.expired`, "to return to
  inventory any items reserved in the expired session"
  ([API: create session](https://docs.stripe.com/api/checkout/sessions/create);
  [Manage limited inventory](https://docs.stripe.com/payments/checkout/managing-limited-inventory?payment-ui=stripe-hosted)).
- **[DOCS]** Payment Links can be limited — "When the payment link reaches the limit, it automatically
  deactivates" — or switched off with `active=false`
  ([customize](https://docs.stripe.com/payment-links/customize);
  [API: update](https://docs.stripe.com/api/payment-link/update)).
- **[ABSENT]** Any expiry time on a Payment Link: the create and update references have no expiry
  parameter.
- *Reading:* a 60-minute desk link maps to a Checkout Session with `expires_at` = now + 60 min,
  created on the club's connected account. A Payment Link would need Rakieta to switch it off itself.

---

## 3. Cash and card recorded at the desk

**What it covers.** The desk marks a booking paid in cash, by card on its own terminal, or by transfer,
in the same calendar as online payments. It also covers a till session that counts the cash.

**Who has it**
- **Playtomic Manager.**
  - **[POLICY]** "Onsite payments are the ones your club configures and registers manually in
    Playtomic Manager when a player pays at the venue … default methods like cash or card at the club,
    or … custom methods" ([Payment methods, 2026-10-05](https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281)).
    The defaults are "Credit Card" and "Cash", and a club can add others such as "Bizum, bank
    transfer" ([Onsite Payment Methods, 2026-06-19](https://helpmanager.playtomic.com/hc/en-gb/articles/20534904432401)).
  - **[POLICY]** The Cash Register runs "opening the session, cash deposits, withdrawals, audits, and
    closing the session". "Any cash refund must also be recorded". A payment's method "can't be
    edited"; the fix is to refund and record it again ([Store: Cash Register, updated 2026-10-05](https://helpmanager.playtomic.com/hc/en-gb/articles/22684483827857)).
    It is "an informative tool" (carried, `competitor-club.md`, 2026-10-08).
- **Playmore.**
  - **[POLICY]** The payments report lists "Wszystkie płatności z okresu do 7 dni: gotówka, karta,
    przelew, online … codzienna kontrola kasy" — all payments of up to 7 days, cash, card, transfer,
    online, for a daily cash check. Its sample shows "Online 43% · Karta 31% · Gotówka 18% · Przelew
    8%" ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - **[PRICE]** "Rezerwacja opłacona na recepcji gotówką, kartą albo przelewem jest bez prowizji" —
    no commission on desk payments ([cennik](https://join.playmore.pl/cennik/)).
- **tenis4U.** **[POLICY]** The panel's payment methods are `CASH`, `CARD_TERMINAL`, `BENEFIT_CARD`,
  `CASH_AND_ONLINE` and `PENDING_CASH`, with `cash_confirmed_by` and `cash_confirmed_at`. A
  `cashPercentage` is shown, along with "Recepcja oznaczy płatność przy kasie" and "Recepcja
  potwierdziła gotówkę" ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js);
  `integration.md`).
- **kluby.org.** **[POLICY]** Features include "Rozliczanie klientów i trenerów", "Zestawienia
  finansowe" and "Lista zaległości" — settling clients and coaches, financial statements, a debtors'
  list ([funkcje](https://oferta.kluby.org/funkcje)). The changelog adds "Pobranie zestawienia
  dziennego do Excela" (daily statement to Excel, 2022) and "Drukowanie 1 paragonu do płatności
  zbiorczej" (one receipt for a combined payment, May 2021) ([changelog 2022](https://oferta.kluby.org/changelog?rok=2022),
  [2021](https://oferta.kluby.org/changelog?rok=2021)).
- **MATCHi.** **[POLICY]** "If a customer has paid outside of MATCHi (for example, in person), you can
  mark it as paid yourself" ([Payments and orders](https://matchi.zendesk.com/hc/en-gb/articles/26122506946845)).
  **[ABSENT]** A cash-drawer feature: a help search for "cash register" and "POS" found none.

**The desk's day with it.** It takes cash or the bank terminal and marks the booking paid with that
method. At close, it counts the drawer (Playtomic) or pulls the day's report (Playmore, kluby.org).
Playmore names the problem: "Wyciąg z banku, zeszyt recepcji, raport z terminala. Co miesiąc ktoś
siedzi wieczorem i skleja arkusz dla księgowej" — the bank statement, the reception notebook, the
terminal report: each month someone sits in the evening gluing a spreadsheet for the accountant
(**[POLICY]** [analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).

**What a Kraków desk does today.** Card or cash at reception is the norm (Garden Padel and Squash4You
above). Benefit cards come off at the desk: "Każda karta daje rabat wysokości 15zł, maksymalnie 2
karty na kort" — each card gives 15 zł off, at most 2 cards a court (**[PRICE]**
[Miazga cennik](https://www.miazgasquash.pl/cennik/)).

**What it means for the player app.** A booking paid at the desk should show as paid, with how. A
player who "owes" at the desk sees nothing to pay online. Playtomic: "Payment at the club … can be
changed" (**[POLICY]** [Payment methods](https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281)).

**Market signal.** Every rival read records the desk's method by hand. *Reading:* this is table stakes
for replacing tenis4U.

**What the law requires**
- **[LAW]** Every desk sale to a consumer is rung on a cash register (§ 9). The receipt is issued "nie
  później niż z chwilą przyjęcia należności, bez względu na formę płatności" — no later than the
  moment payment is taken, whatever the form (Rozporządzenie MF w sprawie kas rejestrujących,
  [Dz.U. 2025 poz. 845 § 6 ust. 1 pkt 1](https://api.sejm.gov.pl/eli/acts/DU/2025/845/text.pdf),
  in force from 1 July 2025).
- **[LAW]** A cash prepayment gets a receipt "z chwilą jej otrzymania" — when received (§ 6 ust. 1
  pkt 2 lit. a, same act).

---

## 4. Taking the card inside the system: Stripe Terminal and Tap to Pay

**What it covers.** Card-present payments run through the same Stripe account as online ones. They
use a reader or a phone (Tap to Pay), are tied to the booking, and refund through the same API. The
alternative is a bank terminal the software only records.

**Who has it**
- **Playtomic Manager.** **[ABSENT]** A card reader integration: help searches for "terminal", "point
  of sale" and "POS" return the Store and payment-method pages, which mark card payments manually.
  The Shop's "Card on File" charge (US first) charges a saved card, not a reader (**[POLICY]**
  [Charging your players credit card in the Shop](https://helpmanager.playtomic.com/hc/en-gb/articles/40648454493841)).
- **Playmore, tenis4U, kluby.org, MATCHi.** **[ABSENT]** Any integrated terminal on their public
  pages and help. tenis4U only labels a payment `CARD_TERMINAL`.

**The desk's day with it.**
- **[DOCS]** With direct charges "all API resources belong to the connected account … The connected
  account is responsible for the cost of Stripe fees, refunds, and chargebacks"
  ([Terminal with Connect: direct charges](https://docs.stripe.com/terminal/features/connect?connect-charge-type=direct)).
- **[DOCS]** "Online refunds are available on all card networks except for Interac. In-person refunds
  are only available on Interac" ([Refund transactions](https://docs.stripe.com/terminal/features/refunds?terminal-sdk-platform=server-driven)).
- *Reading:* the desk refunds from the booking screen, not on the reader.

**What a Kraków desk does today.** A bank or fintech terminal, priced as below, recorded as "karta".

**Stripe Terminal in Poland**
- **[DOCS]** Readers: "Available in (Preview)" lists PL beside BG, CY, EE, HR, HU and others
  ([Terminal global availability](https://docs.stripe.com/terminal/payments/collect-card-payment/supported-card-brands)).
  Preview means "Not feature-complete … Some breaking changes expected"; some previews "might require
  users to request access" ([release phases](https://docs.stripe.com/release-phases)).
- **[DOCS]** For PL: "Stripe supports Visa, Mastercard, American Express, and Discover payments in
  Poland. All transactions must be made in Polish złoty (PLN). … either your platform account or
  connected account must be in Poland" ([Regional considerations: PL](https://docs.stripe.com/terminal/payments/regional?integration-country=PL)).
  The readers listed for PL:
  - Smart readers: BBPOS WisePOS E, Stripe Reader T600, S710 and S700.
  - Mobile reader: BBPOS WisePad 3.
  - Tap to Pay on Android and on iPhone.
- **[DOCS]** Tap to Pay on iPhone lists PL under "Availability", not preview, and so does Tap to Pay
  on Android ([iPhone](https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay?platform=ios),
  [Android](https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay?platform=android)). Both
  are in the Terminal React Native SDK. "For platforms, use of Tap to Pay on iPhone is subject to the
  Apple Acceptance Platform User Terms".
- **[DOCS]** Non-card methods on Terminal are WeChat Pay, Affirm and PayNow by QR, with no BLIK
  ([Additional payment methods](https://docs.stripe.com/terminal/payments/additional-payment-methods?terminal-sdk-platform=server-driven)).
- **[PRICE]** In-person in PL: "1.4% per successful charge for EEA cards", "2.9% … for non-EEA cards",
  "+ 0.40zł per authorisation for Tap to Pay", "+ 0.20zł per authorisation for optional
  point-to-point-encryption". Readers excl. VAT: WisePad 3 249 zł, WisePOS E 899 zł, S700 1 079 zł,
  S710 1 079 zł. Cellular costs 36 zł per reader per month ([Stripe pricing, Poland](https://stripe.com/en-pl/pricing)).

**Polish alternatives a club uses** (the software only records them)

| Provider | Card fee | Monthly | Source |
| --- | --- | --- | --- |
| PKO BP / eService | 0,55 % Visa and MC, 0,39 % BLIK, no fixed fee; 0 % for 12 months under *Polska Bezgotówkowa* | 39,99 zł (29,90 SmartPOS) | carried, `gaps-PAY.md`, 2026-10-08 |
| eService (own site) | — | "Twój pierwszy rok z terminalem za 0 zł, kolejne 18 miesięcy za 1 zł miesięcznie" — first year free, then 1 zł a month for 18 months (*Polska Bezgotówkowa*). It also sells a phone terminal app, "eService tom" (iPhone, Android), "PIN pady do systemów kasowych" (PIN pads for till systems) and has a "Sekcja dla integratora" | **[PRICE]**/**[POLICY]** [eservice.com.pl](https://www.eservice.com.pl/), 2026-10-12 |
| mBank / PolCard (Fiserv) | 0 % to 100 000 zł, then 0,59 % + 4 gr; BLIK 0,39 % + 10 gr | 33 zł after 24 months | carried, `gaps-PAY.md`; PolCard: "Terminal za 0 zł przez rok" ([polcard.pl](https://polcard.pl/blog/ile-wynosi-prowizja-za-platnosc-karta)) |
| SumUp | 1,49 %; or 0,79 % on *Płatności Plus* | 0 zł, or 89 zł | carried, `gaps-PAY.md` |
| myPOS | "1.45% + 0,20 zł" domestic/EEA consumer and domestic business cards; Amex 2,45 % + 0,20 zł; other cards 2,85 % + 0,20 zł (under 50 000 zł a month) | 0 zł; device 239–299 zł | **[PRICE]** [myPOS cennik](https://www.mypos.com/pl-pl/pricing-and-fees), 2026-10-12 |
| Revolut Reader | **[ABSENT]** revolut.com answered 403 to every pricing page | | |
| Elavon | not checked | | |

- **[LAW]** Interchange is capped at 0,2 % (consumer debit) and 0,3 % (consumer credit) (carried,
  `gaps-PAY.md`).
- *Reading:* eService's PIN pads for till systems and its integrator section suggest a third route: a
  bank terminal driven by the club software. Its integration terms were not read.
- *Reading:* on a 160 zł court paid by one card, PKO costs 0,88 zł, Stripe Terminal 2,24 zł (1,4 %),
  and Tap to Pay 2,64 zł. Four 40 zł cards on Tap to Pay cost 3,84 zł.

**What it means for the player app.** Nothing changes for the player, except that the booking shows
"paid by card" once captured.

**Market signal.** No racket rival found integrates a terminal. *Reading:* the only gain over a bank
terminal is reconciliation (one Stripe payout, refunds from the booking). The cost is a higher rate,
no BLIK at the desk, and preview status for readers.

**What the law requires**
- **[LAW]** "Zniesiony został obowiązek integracji terminali płatniczych z kasami on-line … Został on
  zastąpiony wprowadzonym na stałe obowiązkiem raportowania struktur ITP" — the duty to integrate
  terminals with online registers was abolished and replaced by permanent ITP reporting
  (**[DOCS]** [KAS: Agenci rozliczeniowi, v19.0 of 2026-07-30](https://www.gov.pl/web/kas/agenci-rozliczeniowi)).
  The basis is art. 6 of the act of 24 January 2025 ([Dz.U. 2025 poz. 222](https://api.sejm.gov.pl/eli/acts/DU/2025/222/text.pdf)),
  in force 1 April 2025.
- **[LAW]** Its art. 5 adds art. 49aaa to the KAS Act: the tax authority "wykorzystuje informacje o
  transakcjach płatniczych akceptanta wykonywanych przy użyciu terminala płatniczego, oprogramowania
  lub systemu teleinformatycznego", and "Do przekazywania … jest obowiązany agent rozliczeniowy" —
  the acquirer must send data on the merchant's terminal, software or system payments, with the
  merchant's NIP and the place of each transaction (same act).
- *Reading:* card-at-desk takings are visible to the tax authority whatever terminal is used. A club
  whose register totals fall short of its card takings shows up in that data.
- **[LAW]** A card payment at the desk is still a register sale (§ 9); the Terminal receipt is not a
  fiscal receipt.

---

## 5. Selling extras: racket hire, balls, drinks, a shop

**What it covers.** Selling things besides the court, at the desk or added to a booking, with stock,
prices, VAT rates and the same day's report.

**Who has it**
- **Playtomic Manager.**
  - **[POLICY]** "The Store or POS (Point of Sale) function … allows clubs to offer additional services
    such as balls, drinks, and other products … POS items can only be purchased at the club's
    reception." It offers quick-access items, custom items, discounts and sales history
    ([Using the Store/POS, updated 2026-07-01](https://helpmanager.playtomic.com/hc/en-gb/articles/45074894700689)),
    and stock management ([Store: Stock Management](https://helpmanager.playtomic.com/hc/en-gb/articles/45052977020177)).
  - **[POLICY]** Booking "Extras" are "Racket rental, Balls, Overgrips, Water", each with a "VAT/TAX
    field" ([Extra products, 2026-06-17](https://helpmanager.playtomic.com/hc/en-gb/articles/20974373071377)).
  - **[POLICY]** POS starts at the Professional plan (carried, `competitor-club.md`, 2026-10-06).
- **Playmore.** **[POLICY]** "POS działa obok rezerwacji. Sprzedaż barowa i sklepowa kończy się w tym
  samym systemie i raporcie co sprzedaż kortów" — POS runs beside bookings, and bar and shop sales end
  in the same system and report as court sales ([join.playmore.pl](https://join.playmore.pl/)). "Moduł
  POS obsługuje sprzedaż barową i sklepową … jeden rachunek dla klienta, magazyn i raporty sprzedaży" —
  one bill per customer, stock, sales reports ([dla kompleksów sportowych](https://join.playmore.pl/dla-kompleksow-sportowych/)).
- **kluby.org.** **[POLICY]** "Sklep z towarami" (a shop with goods) ([funkcje](https://oferta.kluby.org/funkcje)).
  The changelog shows its growth:
  - Quick shop sale while settling a booking — "Dodanie szybkiej sprzedaży ze sklepu podczas
    rozliczania rezerwacji" (June 2017).
  - Shop products tied to services — "Tworzenie produktów w sklepie powiązanych z usługami" (February
    2021).
  - Quick product sales — "Szybka sprzedaż produktów" (April 2022).
  - One receipt for a booking plus shop items — "Paragon łączący rezerwację z zakupami w sklepie"
    (July 2022).
  ([changelog 2017](https://oferta.kluby.org/changelog?rok=2017), [2021](https://oferta.kluby.org/changelog?rok=2021),
  [2022](https://oferta.kluby.org/changelog?rok=2022)).
- **tenis4U.** **[ABSENT]** A shop or POS: no "sklep" or "produkt" in the panel bundle. **[POLICY]**
  Hardware: "możliwość uruchomienia automatu do wypożyczania sprzętu tenisowego" — an
  equipment-rental machine ([tenis4u.pl](https://tenis4u.pl/)).
- **MATCHi.** **[POLICY]** Invoice rows cover "court hire, memberships, courses, merchandise"
  ([Create invoice from invoice basis](https://matchi.zendesk.com/hc/en-gb/articles/11429366519581)).
  **[ABSENT]** A POS: a help search for "POS" and "kiosk" found nothing.

**The desk's day with it.** It adds a racket and balls to the booking's bill, sells a drink, and closes
one bill. Playtomic warns: "Players cannot cancel 'Extras' separately"
([Extras](https://helpmanager.playtomic.com/hc/en-gb/articles/20974373071377)).

**What a Kraków desk does today**
- **[PRICE]** Fame Sport: "Wypożyczenie piłek tenis/padel 5 zł", "Wypożyczenie rakiety tenis/padel
  10 zł", ball machine 40 zł/h, sauna 15 zł/h, stringing 35 zł ([cennik](https://famesport.pl/cennik/)).
- **[PRICE]** Miazga: racket 10 PLN, premium 15 PLN, balls and goggles free, "Trener 1h (plus opłata za
  całość kortu) 80 PLN" — a coach, plus the court ([cennik](https://www.miazgasquash.pl/cennik/)).
- **[POLICY]** Squash4You: "Usługi nieobjęte kartą partnerską (m.in. wypożyczenie sprzętu) podlegają
  odrębnej opłacie" — services the partner card doesn't cover, such as equipment hire, are charged
  separately ([regulamin](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** Playtomic lets the player add Extras on the payment screen. An
extra added online and paid with the court counts as online paid in full; one bought at the desk does
not (§ 9).

**Market signal.** Playtomic (Professional+), Playmore and kluby.org all sell extras. *Reading:* the
local leader tenis4U does not, so a club on tenis4U runs a separate till.

**What the law requires**
- **[LAW]** Racket hire bundled with the court is 8 %:
  - A padel court with racket hire to individuals is one service under PKWiU 93.11.10.0, at 8 %
    ([WIS 0112-KDSL2-1.440.68.2026.3.BK, 13 April 2026](https://eureka.mf.gov.pl/informacje/podglad/687645)).
  - So was court entry plus racket and balls, priced separately but sold only with the court
    ([WIS 0112-KDSL2-2.440.235.2023.3.AS, 13 October 2023](https://eureka.mf.gov.pl/informacje/podglad/565146)).
- **[LAW]** Annex 3 of the VAT Act lists no equipment rental (PKWiU 77.21) and no gastronomy (PKWiU 56)
  ([Dz.U. 2026 poz. 1263, załącznik nr 3](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf)).
  *Reading:* standalone racket hire falls to the 23 % default; the bar's rates were not researched.
- **[LAW]** A café or bar is excluded from every cash-register exemption, and so is alcohol (§ 9).

---

## 6. Refunds: who gives back what, and how

**What it covers.** Who refunds what:
- the desk refunding an online payment;
- a cash refund at the desk;
- a club-wide cancellation (weather, closure);
- the records a refund needs.

**Who has it**
- **Playtomic Manager.**
  - **[POLICY]** A removed player who "paid through the app" is refunded automatically. If they paid
    "at the club, you are responsible for issuing the refund". A club cancellation gives a full refund
    "within 2–10 business days" (carried, `competitor-club.md`, 2026-10-08).
  - **[POLICY]** Cash refunds go through the Cash Register ([Store: Cash Register](https://helpmanager.playtomic.com/hc/en-gb/articles/22684483827857)).
  - **[POLICY]** The invoicing tool "automatically generate[s] credit notes for refunds"
    ([Invoicing System, updated 2026-10-08](https://helpmanager.playtomic.com/hc/en-gb/articles/24829231088657)).
- **Playmore.** **[POLICY]** On weather, "cena rezerwacji opłaconej online wraca do gracza na portfel w
  aplikacji Playmore. Nie robisz ręcznych przelewów" — the online price returns to the player's
  Playmore wallet, with no manual transfers ([join.playmore.pl](https://join.playmore.pl/)). Its
  refunds keep the service fee (carried, `platforms.md`).
- **tenis4U.** **[POLICY]** An online refund is "pomniejszonych o opłatę transakcyjną w wysokości 2%" —
  less a 2 % transaction fee (carried, `local-market.md`). The panel shows a "Historia transakcji" with
  a `refunded` flag ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **MATCHi.** **[POLICY]** "An annulled order can have a refund attached, and if it does, the payment is
  reversed with the customer at the same time" ([Payments and orders](https://matchi.zendesk.com/hc/en-gb/articles/26122506946845)).
  The admin chooses between a full refund, a refund less a fee, or no refund (carried, `platforms.md`).
- **kluby.org.** **[POLICY]** Refunds and complaints go to the club (carried, `platforms.md`). The help
  index lists "4.8. Zablokowane środki" (blocked funds) ([pomoc](https://oferta.kluby.org/pomoc)).

**The desk's day with it.** It refunds an online payment from the booking. Cash goes from the drawer,
recorded against the day's session. A payment rung up wrongly is refunded and rung again (Playtomic).

**What a Kraków desk does today.** Weather: Garden Padel refunds minus 2 %, while Fame Sport and SAO
refund in full; Squash4You moves a prepaid booking instead of refunding (carried, `local-market.md`).

**What it means for the player app.** The player sees a refund's method and expected time: card 5–10
business days, BLIK hours, P24 up to 3 business days. A cash refund shows as returned at the desk.

**Market signal.** **[COMPLAINT]** "Contacted the app support for refund—they bounced me off to the
club…" (Playmore; carried, `local-market.md`).

**What the law requires**
- **[LAW]** Refunds of register sales are not rung on the register. They go in "odrębnej ewidencji
  zwrotów i uznanych reklamacji" — a separate register of returns and accepted complaints. It holds the
  sale date, the service, the refunded gross and its VAT, the receipt's number, and "protokół przyjęcia
  zwrotu … podpisany przez sprzedawcę i nabywcę" — a protocol signed by seller and buyer
  ([Dz.U. 2025 poz. 845 § 3 ust. 2–3](https://api.sejm.gov.pl/eli/acts/DU/2025/845/text.pdf)).
- **[LAW]** An invoiced sale refunded needs a corrective invoice. For a business buyer this goes
  through KSeF from 2026, and a KSeF error is fixed "wyłącznie poprzez wystawienie faktury korygującej"
  — only by a corrective invoice (**[DOCS]** [inFakt: KSeF FAQ, 2026-05-08](https://pomoc.infakt.pl/hc/pl/articles/29215187153938)).
- **[DOCS]** On Stripe a refund comes from the club's available balance. If the balance is short, a
  card refund waits as pending and other methods fail. "Refunds can only be sent back to the original
  payment method" ([Stripe: Refunds](https://docs.stripe.com/refunds)). Fees aren't returned (carried).
- *Reading:* a desk refunding an online payment in cash breaks the trail. The online sale was exempt
  from the register, and a cash refund of it is neither an online refund nor a register sale.

---

## 7. Payouts and what the club sees of its money

**What it covers.** When online money reaches the club's bank, what each payout contains, and the
reports the club and its accountant use.

**Who has it**
- **Playtomic Manager.** **[POLICY]** NBM pays every Monday by payment date, before the game. It sends
  a weekly payout summary PDF, and its Payments list filters by payment or service date (carried,
  `competitor-club.md`, 2026-10-06/08).
- **Playmore.**
  - **[POLICY]** "Kiedy dostajemy pieniądze z płatności online? Codziennie. Pieniądze za rezerwację
    opłaconą online trafiają na konto klubu w codziennej wypłacie, po rozegraniu gry" — daily, after
    the game is played ([join.playmore.pl](https://join.playmore.pl/)).
  - **[POLICY]** "Raport zintegrowany … przychody z rezerwacji i karnetów, prowizje, kwota netto do
    wypłaty … wysyłasz księgowej" — a monthly file for the accountant. "Płatności online … kwota od
    klienta, prowizja serwisowa i kwota netto do wypłaty" — gross, fee and net per online payment
    ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
- **tenis4U.** **[POLICY]** The club uses its own P24 account. The report is "Początek okresu / Koniec
  okresu — Cały obiekt / Stanowisko / Gracz — Pobierz raport", plus CSV (carried, `gaps-CLUBMONEY.md`).
  **[DOCS]** P24 releases money "nie później niż do końca następnego Dnia Roboczego" — by the end of the
  next business day (carried).
- **kluby.org.** **[POLICY]** "Pobranie raportu księgowości do Excela", "Pobranie raportu wypłat do
  Excela" — accounting and payout reports to Excel (2022) ([changelog 2022](https://oferta.kluby.org/changelog?rok=2022)).
- **MATCHi.** **[POLICY]** A monthly statement by activity date, paid out around the 15th (carried,
  `platforms.md`). It offers downloadable receipts, too ([Payments and orders](https://matchi.zendesk.com/hc/en-gb/articles/26122506946845)).

**The desk's day with it.** It checks yesterday's online money against bookings. The manager sends one
monthly file to the accountant.

**What a Kraków desk does today.** P24 or Tpay pay the club itself, next business day; P24 lists each
payout package's transactions (carried, `gaps-CLUBMONEY.md`).

**What it means for the player app.** Nothing.

**Market signal.** *Reading:* Playmore's "daily, after the game" answers both the club's wish to be
paid fast and the risk of refunding money already paid out.

**What the law requires**
- **[LAW]** For the online cash-register exemption, records must show "jakiej konkretnie czynności
  dotyczyła" — which sale each payment was for (§ 9).

**Stripe facts**
- **[DOCS]** Poland's settlement: "Poland | 7 calendar days | 3 business days" (first payout, then
  default). Schedules can be manual, daily, weekly or monthly ([Stripe: Payouts](https://docs.stripe.com/payouts)).
- **[DOCS]** Instant Payouts lists PL ([Instant Payouts](https://docs.stripe.com/payouts/instant-payouts)),
  at "1% of Instant Payouts volume, Minimum fee of 2.00zł" ([pricing](https://stripe.com/en-pl/pricing)).
  "New Stripe users aren't immediately eligible".
- **[DOCS]** Only automatic payouts are itemised. "Stripe can't identify which transactions are
  included" in a manual payout (carried, `gaps-CLUBMONEY.md`).

---

## 8. Invoices and KSeF

**What it covers.** Issuing a VAT invoice for a court, a lesson or a membership: always to a business,
and to a consumer on request. It also covers sending it through KSeF and connecting an invoicing tool.

**Who has it**
- **Playmore.** **[POLICY]** "Faktury wystawiasz przez połączenie z Fakturownią, przygotowane na KSeF" —
  invoices through a Fakturownia connection, KSeF-ready ([join.playmore.pl](https://join.playmore.pl/)).
  "Połączenie z Fakturownią: faktura VAT z każdej płatności, gotowość na KSeF" — a VAT invoice from
  every payment ([dla miast i gmin](https://join.playmore.pl/dla-miast-i-gmin/)). Its "raport faktur"
  is a list of "klientów, którzy poprosili o fakturę" — customers who asked for an invoice, exported to
  Excel ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)). Players keep "Dane do
  faktury" on their account (carried, `gaps-CLUBMONEY.md`).
- **kluby.org.** **[PRICE]** "Faktury online internetowe — wystawianie i wysyłanie faktur — drukowanie
  tradycyjnych paragonów — wystawianie i wysyłanie e-paragonów — Abonament 0-60 PLN miesięcznie" —
  invoices, paper receipts and e-receipts for 0–60 zł a month ([integracje](https://oferta.kluby.org/integracje)).
  "Wysyłanie powiadomień o wystawionych fakturach" — invoice notices (August 2022)
  ([changelog 2022](https://oferta.kluby.org/changelog?rok=2022)). **[ABSENT]** Which invoicing
  provider it uses, and any KSeF mention, on its pages.
- **Playtomic Manager.** **[POLICY]** The Invoicing System offers "simplified invoice (receipt)" or
  "full invoice" with a tax ID, plus automatic credit notes. "At the moment, there is no integration
  with POS printers" ([updated 2026-10-08](https://helpmanager.playtomic.com/hc/en-gb/articles/24829231088657)).
  It is on the Champion plan, with nothing for Poland (carried, `competitor-club.md`).
- **MATCHi.** **[POLICY]** Built-in invoicing from "invoice rows", credit invoices, and "an accounting
  integration such as Fortnox" ([Register payments](https://matchi.zendesk.com/hc/en-gb/articles/11697353382557)).
- **tenis4U.** **[ABSENT]** "faktur", "paragon", "NIP", "invoice" and "receipt" occur 0 times in its
  club-panel bundle ([bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)), and its player
  app has none either (carried).

**Invoice tools a club software can drive**

| Tool | API | KSeF | Fiscal receipts | Price |
| --- | --- | --- | --- | --- |
| Fakturownia | REST, `api_token`; "Dzięki API można … wystawiać faktury/rachunki/paragony" ([API README, last commit 2026-09-07](https://github.com/fakturownia/API)); KSeF guide with `gov_save_and_send` and offline modes ([KSeF.md](https://github.com/fakturownia/API/blob/master/KSeF.md)) | "Integracja z KSeF 0 zł" ([cennik](https://fakturownia.pl/cennik)) | Paragony.pl module: printers "obsługujące protokół THERMAL i POSNET"; API prints a receipt or e-receipt (`mode=e-receipt`) ([cennik](https://fakturownia.pl/cennik); [e-paragony API](https://github.com/e-paragony/api)) | Base net a month on a 12-month plan: Micro 0 (3 invoices), Start 13,15 zł, Standard 29,96 zł, Pro 52,62 zł, Max 87,85 zł ([public price feed](https://appstore.fakturownia.io/billing/products/fakturownia/public_prices.json)); Paragony.pl 34,90 zł a month (12 months) or 39,90 zł (6), 20 e-receipts free, then e.g. 3 000 for 99 zł ([paragony.pl](https://paragony.pl)) |
| inFakt | REST + JSON ([API](https://pomoc.infakt.pl/hc/pl/articles/115000174410)); `send_to_ksef` flag ([2026-04-15](https://pomoc.infakt.pl/hc/pl/articles/34824149003922)) | yes; "Wysyłka faktur B2C do KSeF jest dobrowolna" — B2C to KSeF is voluntary ([FAQ](https://pomoc.infakt.pl/hc/pl/articles/29215187153938)) | not checked | **[ABSENT]** the price page renders by JavaScript |
| iFirma | API; limits "15 000 zapytań" a day and "100 zapytań" a minute; "wysyłanie faktury do KSeF", "status wysyłki do KSeF i numer KSeF" ([api.ifirma.pl](https://api.ifirma.pl/)) | yes | not checked | invoicing above three invoices needs "Faktura+ w cenie 12,50 zł/mies." (12-month payment) ([cennik](https://www.ifirma.pl/cennik)) |
| wFirma | API documented at [doc.wfirma.pl](https://doc.wfirma.pl/) (help: [API](https://pomoc.wfirma.pl/-api-interfejs-dla-programistow), [KSeF](https://pomoc.wfirma.pl/-integracja-z-ksef)) | yes | "Drukarki fiskalne" is listed on its price page ([cennik](https://wfirma.pl/cennik)) | **[ABSENT]** prices render by JavaScript |

- **[DOCS]** Stripe: "Stripe Invoicing creates invoice records … but doesn't generate or transmit
  legally compliant e-invoice files on its own". It points to Billit or a webhook integration
  ([Stripe: e-invoicing](https://docs.stripe.com/invoicing/e-invoicing)). **[ABSENT]** Any Stripe page
  naming KSeF.

**The desk's day with it.** A company asks for an invoice with its NIP. The desk issues it from the
payment, and it goes to KSeF. A consumer who asks gets a PDF.

**What a Kraków desk does today.** **[POLICY]** At AGH, the customer emails name, address and "potwierdzenie
dokonania przelewu" (proof of the transfer) to get an invoice (carried, `gaps-CLUBMONEY.md`). Other
Kraków club rules mention no invoices (carried).

**What it means for the player app.**
- A field for invoice details (company name, NIP) and an "I need an invoice" request on a payment.
- For a desk sale, the NIP must be on the receipt before an invoice can follow (below).
- *Reading:* the four sharers of a court each pay their own share. Whether one organiser can get one
  company invoice for the whole court is untested (carried as a gap).

**Market signal.**
- **[COMPLAINT]** "you can't get receipts from the club" (Playtomic, BE, 2026-07-14), and "App does
  not produce VAT receipt. The form… goes into a balck hole" (Playtomic, Google Play, 2026-09-22)
  (carried, `complaints.md`).
- Playmore puts "KSeF" in its headline module.

**What the law requires** (VAT Act, consolidated [Dz.U. 2026 poz. 1263](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf))
- **[LAW]** Invoices must be issued:
  - always for a sale to another taxpayer or a legal person (art. 106b ust. 1 pkt 1);
  - for a prepayment from one (ust. 1 pkt 4), unless paid in the month the service happens (ust. 1a);
  - for a consumer, only if asked within 3 months from the end of the month of the service or payment
    (ust. 3).
- **[LAW]** After a register sale, an invoice to a business "wystawia się wyłącznie, jeżeli paragon …
  zawiera numer" identifying the buyer — only if the receipt carries the NIP (art. 106b ust. 5).
- **[LAW]** "Podatnicy są obowiązani wystawiać faktury ustrukturyzowane przy użyciu Krajowego Systemu
  e-Faktur" (art. 106ga ust. 1). This "nie dotyczy … na rzecz nabywcy … będącego osobą fizyczną
  nieprowadzącą działalności gospodarczej" — not for a consumer (ust. 2 pkt 4) — though such invoices
  "mogą" be issued in KSeF (ust. 4).
- **[DOCS]** Start dates: 1 February 2026 for taxpayers with 2024 sales above 200 m zł, and 1 April 2026
  for the rest. Receiving through KSeF has been mandatory since 1 February 2026
  ([KSeF: zasady obowiązywania](https://ksef.podatki.gov.pl/ksef-news/zasady-obowiazywania-ksef-i-przepisy-prawne/)).
- **[LAW]** Small-taxpayer deferral: "W okresie od dnia 1 kwietnia 2026 r. do dnia 31 grudnia 2026 r."
  a taxpayer may issue paper or e-invoices if their gross value "udokumentowana tymi fakturami
  wystawionymi w danym miesiącu jest mniejsza lub równa 10 000 zł", losing it from the invoice that
  crosses it (art. 145m).
- **[LAW]** Until 31 December 2026, invoices from a cash register and receipts-with-NIP counting as
  invoices stay allowed (art. 145n). "Od 1 stycznia 2027 r. będzie można nadal wystawiać paragony
  fiskalne z NIP nabywcy, jednak nie będą one uznawane za faktury uproszczone" — receipts with a NIP
  remain, but no longer count as simplified invoices ([KSeF FAQ](https://ksef.podatki.gov.pl/ksef-news/zasady-obowiazywania-ksef-i-przepisy-prawne/)).
  From 1 January 2027, art. 111 ust. 3a pkt 1 reads "wystawić i wydać nabywcy paragon fiskalny z każdej
  sprzedaży" — a receipt from every sale.
- **[LAW]** Penalties from 1 January 2027, for not issuing in KSeF: "karę pieniężną w wysokości do 100 %
  kwoty podatku wykazanego na tej fakturze … a w przypadku faktury bez wykazanego podatku … do 18,7 %
  kwoty należności ogółem" — up to 100 % of the VAT, or 18,7 % of the gross where no VAT is shown
  (art. 106ni). "Nie będą więc nakładane kary … w okresie 1.02.2026 r. do 31.12.2026 r." — no penalties
  in that period ([KSeF FAQ](https://ksef.podatki.gov.pl/ksef-news/zasady-obowiazywania-ksef-i-przepisy-prawne/)).
- **[DOCS]** VAT-exempt taxpayers (under 240 000 zł) still issue KSeF invoices from 1 April 2026, with
  the 10 000 zł deferral open to them (same FAQ). The subjective exemption limit is 240 000 zł
  (art. 113 ust. 1).

---

## 9. The cash register (kasa fiskalna) and fiscal printers

**What it covers.** Which of a Kraków club's sales must be rung on a cash register, which are exempt,
whether a software (virtual) register is allowed, and how club software drives a fiscal printer or
e-receipt.

**Who has it**
- **kluby.org.** **[POLICY]** "Integracja z kasą fiskalną" (November 2020); "Sterowanie — Drukowanie
  paragonów" (December 2020); "Dodanie ikonki przy płatności z wydrukiem z kasy fiskalnej" (March
  2021); "NIP do paragonu" (January 2022); "Widok listy wydrukowanych paragonów" (June 2022)
  ([changelog 2020](https://oferta.kluby.org/changelog?rok=2020), [2021](https://oferta.kluby.org/changelog?rok=2021),
  [2022](https://oferta.kluby.org/changelog?rok=2022)). The integrations page lists "integracja z
  drukarką fiskalną" under its remote-control hardware ([integracje](https://oferta.kluby.org/integracje)).
  *Reading:* the printer is driven through kluby.org's on-site controller.
- **Playmore.** **[ABSENT]** "fiskal", "paragon" or "drukarka" on 14 join.playmore.pl pages, though it
  sells "POS (kasa i sprzedaż)" — till and sales. Its terms say receipts and invoices "wystawia
  bezpośrednio Partner" — the club issues them (carried, `platforms.md`).
- **tenis4U.** **[ABSENT]** "paragon" and "fiskal" occur 0 times in the panel bundle.
- **Playtomic Manager.** **[POLICY]** "there is no integration with POS printers"; **[ABSENT]** any
  Polish fiscal feature (carried, `competitor-club.md`).
- **MATCHi.** **[ABSENT]** (Swedish product; not searched for Polish fiscal rules).

**How web software reaches a fiscal printer**
- **[DOCS]** Fakturownia's Paragony.pl: "pobrać nasz moduł do fiskalizacji, a następnie zintegrować go
  ze swoją drukarką fiskalną" — download the fiscal module and connect it to your printer
  ([paragony.pl](https://paragony.pl)). Via API, "Do fiskalizacji paragonu, wymagana jest drukarka
  fiskalna połączona z Fakturownią", by `fiscal_print?…&mode=e-receipt|print`
  ([e-paragony API](https://github.com/e-paragony/api)). Supported printers use "protokół THERMAL i
  POSNET" ([cennik](https://fakturownia.pl/cennik)).
- **[DOCS]** A third-party bridge: "JavaScript cannot communicate with printer directly, so it needs
  middle layer: Posnet Server RESTful service", on localhost ports 3050/3051 (BigDotSoftware, updated
  2021-11-10) ([WordPress plugin](https://wordpress.org/plugins/posnet-printer-for-woocommerce/)).
- **[ABSENT]** A cloud API published by Posnet or Elzab themselves: web search found only local bridges.
- *Reading:* every route found needs a small program on a PC at the desk next to the printer. The
  e-receipt is still produced by that printer.

**The desk's day with it.** It rings each desk sale on the register (or prints from the software), on
paper or as an e-receipt with the customer's consent. It prints a daily report, keeps a refunds
register, and books the register's annual service.

**What a Kraków desk does today.** Desk payments by card or cash at every club read (§ 3). **[ABSENT]**
Any Kraków club page naming its register or receipts.

**What it means for the player app.** An e-receipt for a desk sale could be sent to the player's email
or app with consent. A player wanting a company invoice for a desk sale must give the NIP before the
receipt.

**Market signal.** kluby.org has driven fiscal printers since 2020. *Reading:* tenis4U, the Kraków
leader, leaves clubs to run a separate till, which shows clubs live with a second device.

**What the law requires**
- **[LAW]** Who must register: "Podatnicy dokonujący sprzedaży na rzecz osób fizycznych
  nieprowadzących działalności gospodarczej oraz rolników ryczałtowych są obowiązani prowadzić
  ewidencję sprzedaży przy zastosowaniu kas rejestrujących" — sales to consumers and flat-rate farmers
  (VAT Act art. 111 ust. 1). A sale to a company is not on the register.
- **[LAW]** Failing that costs "dodatkowe zobowiązanie podatkowe w wysokości … 30 % kwoty podatku
  naliczonego" — 30 % of input VAT (art. 111 ust. 2).
- **[LAW]** The exemptions are in the Rozporządzenie Ministra Finansów z dnia 17 grudnia 2024 r. w
  sprawie zwolnień z obowiązku prowadzenia ewidencji sprzedaży przy zastosowaniu kas rejestrujących
  ([Dz.U. 2024 poz. 1902](https://api.sejm.gov.pl/eli/acts/DU/2024/1902/text.html)). It is valid "nie
  dłużej jednak niż do dnia 31 grudnia 2027 r." (§ 2–3). It was amended only for parking and
  coin-mechanical vending ([Dz.U. 2026 poz. 420](https://api.sejm.gov.pl/eli/acts/DU/2026/420/text.pdf),
  from 31 March 2026).
- **[LAW]** The online exemption is **annex poz. 42**, in Part II, *Sprzedaż dotycząca szczególnych
  czynności*: "Świadczenie usług na rzecz osób fizycznych nieprowadzących działalności gospodarczej
  oraz rolników ryczałtowych, jeżeli świadczący usługę otrzyma w całości zapłatę za wykonaną czynność
  za pośrednictwem poczty, banku lub spółdzielczej kasy oszczędnościowo-kredytowej (odpowiednio na
  rachunek bankowy podatnika …), a z ewidencji i dowodów dokumentujących zapłatę jednoznacznie wynika,
  jakiej konkretnie czynności dotyczyła". In English: services to consumers paid **in full** through a
  bank to the seller's account, where the records show which service each payment was for.
- **[LAW]** Rulings accept a payment operator in the chain:
  - Tennis courts booked online, with the operator paying the club monthly with a list of
    transactions ([0111-KDIB3-2.4012.631.2025.1.SR, 30 September 2025](https://eureka.mf.gov.pl/informacje/podglad/659768);
    carried).
  - An app where an operator collects and pays out, with an e-mailed payment confirmation as proof
    ([0113-KDIPT1-3.4012.602.2026.2.JM, 17 September 2026](https://eureka.mf.gov.pl/informacje/podglad/710095);
    carried).
  - **[ABSENT]** A ruling naming Stripe Connect, or one service paid in several shares (carried).
- **[LAW]** The 20 000 zł threshold: exempt are "podatników, u których wartość sprzedaży dokonanej na
  rzecz osób fizycznych … w poprzednim roku podatkowym nie przekroczyła kwoty 20 000 zł" (§ 3 ust. 1
  pkt 1), pro rata for newcomers (pkt 2).
  - Only sales under annex poz. 40 (real estate) and 50 (fixed assets) are left out of the count (§ 3
    ust. 3 pkt 1). Online consumer sales count.
  - The exemption lapses "po upływie dwóch miesięcy następujących po miesiącu", in which the threshold
    was crossed (§ 5 ust. 1 pkt 1). It lapses at once on any § 4 activity (§ 5 ust. 2).
- **[LAW]** The 80 % rule covers only Part I items (§ 3 ust. 1 pkt 3), so poz. 42 sales do not lift a
  club into it. Part I poz. 34 exempts education "z wyłączeniem … usług w zakresie pozaszkolnych form
  edukacji sportowej oraz zajęć sportowych i rekreacyjnych (PKWiU 85.51.10.0)" — sports lessons are
  excluded. Poz. 36 exempts "PKWiU 94 Usługi świadczone przez organizacje członkowskie".
- **[LAW]** Court hire is not excluded from the exemptions. § 4 ust. 1 lists the sales that never get
  one, and among services it names:
  - "związanych z wyżywieniem (PKWiU ex 56.10, 56.21, ex 56.29, ex 56.30), wyłącznie: świadczonych przez
    stacjonarne placówki gastronomiczne" — a café or bar (pkt 2 lit. i);
  - entry to amusement parks and dance halls (lit. l);
  - parking (lit. n);
  - self-service devices (lit. o);
  - among goods, alcohol "o zawartości alkoholu powyżej 1,2%" (pkt 1 lit. q).
  Sports facilities appear nowhere in the list.
- **[LAW]** Online registers: a register must connect "z Centralnym Repozytorium Kas" (art. 111 ust. 6a,
  ust. 3a pkt 12). Older registers with a paper or electronic copy remain usable, except for the
  sectors in art. 145b (art. 145a ust. 1). Art. 145b names "obiektów służących poprawie kondycji
  fizycznej – wyłącznie w zakresie wstępu", meaning fitness entry.
  - **[LAW]** A 2022 ruling for a city's sports units held that entry to "korty do gry w tenisa i
    squasha" is not such a service, and so was not bound to online registers from 1 July 2021
    ([0114-KDIP1-3.4012.609.2021.1.KP, 27 January 2022](https://eureka.mf.gov.pl/informacje/podglad/479165)).
- **[LAW]** Software (virtual) registers (kasy wirtualne) are allowed only for listed activities
  ([Dz.U. 2023 poz. 2268, § 1](https://api.sejm.gov.pl/eli/acts/DU/2023/2268/text.pdf)):
  - passenger transport and taxis;
  - accommodation (PKWiU 55);
  - "usług restauracji i pozostałych placówek gastronomicznych (PKWiU 56.10)", "pozostałych usług
    gastronomicznych (PKWiU 56.29)", "usług przygotowywania i podawania napojów (PKWiU 56.30)";
  - car washes, volunteer fire brigades, rural housewives' circles;
  - from 1 April 2026, "świadczenia usług przy użyciu urządzeń, w tym wydających bilety, obsługiwanych
    przez klienta" — unattended devices ([Dz.U. 2025 poz. 1345](https://api.sejm.gov.pl/eli/acts/DU/2025/1345/text.pdf)).

  Sports-facility services (93.11) are not listed. The regulations made under art. 111b ust. 3 lapse
  on 1 January 2028 ([Dz.U. 2026 poz. 1270, art. 7 and art. 9 pkt 3](https://api.sejm.gov.pl/eli/acts/DU/2026/1270/text.pdf)).
- **[LAW]** When to ring a prepayment: one paid by bank gets a receipt "niezwłocznie po jej uznaniu na
  rachunku podatnika, nie później niż z końcem miesiąca … a jeżeli przed końcem tego miesiąca dokonano
  sprzedaży, nie później niż z chwilą jej dokonania" — promptly after it reaches the account, by
  month-end, or at the sale if earlier ([Dz.U. 2025 poz. 845 § 6 ust. 1 pkt 2 lit. b](https://api.sejm.gov.pl/eli/acts/DU/2025/845/text.pdf)).
- **[LAW]** E-receipts: the receipt is given "w postaci papierowej lub … za zgodą nabywcy, w postaci
  elektronicznej, przesyłając ten dokument w sposób z nim uzgodniony" — on paper, or electronically
  with the buyer's consent (art. 111 ust. 3a pkt 1).
- **[LAW]** Municipal units: local government (JST) units exempt on 31 December 2016 stay exempt
  (§ 3 ust. 1 pkt 5).
- *Reading — which sales of a Kraków club go on the register:*

  | Sale | On the register? |
  | --- | --- |
  | Court paid fully online by the player (card, BLIK, P24, Apple/Google Pay) to the club's account, booking-identified | No, under poz. 42, if the club's records tie each Stripe payment and payout to the booking (untested for Stripe Connect) |
  | Court paid at the desk, cash or card | Yes, at payment |
  | Deposit online, rest at the desk (kluby.org's 25/50 %) | Yes, the whole sale (poz. 42 needs payment "w całości") |
  | Court split four ways online | Probably no; no ruling on several payers (carried gap) |
  | Lesson paid at the desk | Yes; poz. 34 excludes sports lessons |
  | Bar, café, beer | Yes, from the first sale; a software register is allowed |
  | Racket hire with the court at the desk | Yes |
  | Sale to a company with NIP | No (invoice instead) |
  | A tiny club under 20 000 zł of consumer sales a year, with no bar | No register at all |

---

## 10. Receipts and confirmations for online sales

**What it covers.** What the player gets after paying online: a payment confirmation, a Stripe
receipt, an e-receipt, or an invoice on request.

**Who has it**
- **MATCHi.** **[POLICY]** "You can download a PDF receipt for any order that's been paid" ([Payments
  and orders](https://matchi.zendesk.com/hc/en-gb/articles/26122506946845)). The customer "Receives a
  receipt after successful payment" by payment link ([payment links](https://matchi.zendesk.com/hc/en-gb/articles/14858820219165)).
- **Playtomic Manager.** **[POLICY]** "Get the invoice by email" or only the fee's receipt, by club
  set-up (carried, `areas/PAY.md`).
- **kluby.org.** **[POLICY]** E-receipts, as above.
- **tenis4U.** **[ABSENT]** Any receipt; P24 emails a payment confirmation (carried).
- **Playmore.** **[POLICY]** Booking confirmation; invoice details on the account (carried).

**The desk's day with it.** Nothing for online sales.

**What a Kraków desk does today.** The payment operator emails a confirmation. The club confirms the
booking by SMS or in its app. An invoice comes only on request (carried, `gaps-CLUBMONEY.md`).

**What it means for the player app.**
- **[DOCS]** "Direct charges: Receipts use the connected account's Customer emails, Branding, and
  Public details settings". A platform may pass `receipt_email`, and every receipt shows the legal
  name, support address and privacy policy (carried, `local-market.md`, 2026-10-08).
- *Reading:* the Stripe receipt names the club as seller. It is not a fiscal receipt and is not needed
  as one when poz. 42 applies.

**Market signal.** The receipt complaints in § 8.

**What the law requires.**
- **[LAW]** No fiscal receipt for a sale exempt under poz. 42.
- **[LAW]** An e-mailed payment confirmation is acceptable proof of payment, but it is "nie są to
  dokumenty przewidziane przez przepisy o podatku od towarów i usług" — not a VAT document (carried,
  KIS 710095).

---

## 11. VAT rates on what a club sells

**What it covers.** Getting the rate right on each line: court hire, passes and memberships, lessons,
racket hire.

**Who has it.**
- **Playtomic Manager.** **[POLICY]** Prices are VAT-inclusive, and Extras carry a "VAT/TAX field"
  ([Invoicing System](https://helpmanager.playtomic.com/hc/en-gb/articles/24829231088657);
  [Extras](https://helpmanager.playtomic.com/hc/en-gb/articles/20974373071377)).
- **MATCHi.** **[POLICY]** "VAT settings in MATCHi" and "Which VAT applies?" articles
  ([help](https://matchi.zendesk.com/hc/en-gb/articles/11720153639581)).
- **Playmore, tenis4U, kluby.org.** **[ABSENT]** Per-product VAT settings on their public pages.

**The desk's day with it.** It sets each product's rate once, and the register and invoices use it.

**What a Kraków desk does today.** **[ABSENT]** A Kraków club page stating its VAT rates.

**What it means for the player app.** It shows VAT-inclusive prices; the invoice shows the rate.

**Market signal.** —

**What the law requires** (rulings bind only their applicant; a WIS binds for five years)
- **[LAW]** Court hire is 8 %. The basis is "art. 41 ust. 2 ustawy w zw. z art. 146ef ust. 1 pkt 2
  ustawy w zw. z poz. 55 załącznika nr 3 do ustawy". Annex 3 poz. 55 reads "93.11.10.0 Usługi związane
  z działalnością obiektów sportowych". Annex 3 is titled 7 %, and art. 146ef ust. 1 pkt 2 sets it at 8 %
  for a period the article ties to defence spending ([VAT Act](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf)).
  Latest rulings:
  - squash courts let to schools ([WIS 0112-KDSL2-2.440.217.2026.2.TG, 1 July 2026](https://eureka.mf.gov.pl/informacje/podglad/698583));
  - padel court plus racket ([WIS of 13 April 2026](https://eureka.mf.gov.pl/informacje/podglad/687645)).
- **[LAW]** Passes are 8 %: "odpłatne udostępnianie kortu tenisowego na zasadzie wykupienia
  karnetu/jednorazowego wstępu na halę" — a court by pass or single entry → 93.11.10.0, 8 %
  ([WIS 0112-KDSL2-1.440.359.2023.3.BK, 7 November 2023](https://eureka.mf.gov.pl/informacje/podglad/569109)).
- **[LAW]** Lessons go either way, on the facts:
  - **8 %:** group table-tennis lessons in a sports hall, hall and equipment and instructor sold as one
    package fee → "PKWiU 2015 - 93.11.10.0 Stawka podatku: 8%" ([WIS 0112-KDSL2-2.440.340.2026.2.AS,
    14 September 2026](https://eureka.mf.gov.pl/informacje/podglad/709073)). Likewise a hall tenant
    organising tennis lessons with the court ([WIS 0112-KDSL2-1.440.441.2023.2.BK, 19 December 2023](https://eureka.mf.gov.pl/informacje/podglad/573970)).
  - **23 %:** group tennis lessons by a coach on a court he leases or rents → "PKWiU 2015 – 85.5 Stawka
    podatku … 23%" ([WIS 0112-KDSL2-1.440.720.2024.4.AP, 25 February 2025](https://eureka.mf.gov.pl/informacje/podglad/628342);
    [WIS 0112-KDSL2-1.440.201.2025.3.MW, 9 July 2025](https://eureka.mf.gov.pl/informacje/podglad/648966)).
  - Classification notes put "usług indywidualnych nauczycieli, zawodowych instruktorów sportowych,
    trenerów" under 85.51.10.0, outside 93 (quoted in WIS 698583).
  - *Reading:* a club selling court plus coach as one hour leans to 8 %. A coach selling teaching, or a
    lesson priced on top of the court ("plus opłata za całość kortu", Miazga), leans to 23 %.
- **[LAW]** A non-profit sports club's own services can be exempt. Art. 43 ust. 1 pkt 32 exempts
  "usługi ściśle związane ze sportem … świadczone przez kluby sportowe … nienastawieni na osiąganie
  zysków … z wyłączeniem … usług wynajmu sprzętu sportowego i obiektów sportowych za odpłatnością" —
  it excludes paid rental of equipment and facilities. Tennis classes by sports associations were held
  exempt ([0114-KDIP4-2.4012.321.2025.2.SKJ, July 2025](https://eureka.mf.gov.pl/informacje/podglad/649551);
  [0114-KDIP4-2.4012.572.2026.2.MMA, 4 September 2026](https://eureka.mf.gov.pl/informacje/podglad/708464)).
  *Reading:* an association's court hire stays taxable at 8 %, while its classes may be exempt.
- **[LAW]** The small-taxpayer exemption (art. 113 ust. 1) covers sales not above 240 000 zł in the
  previous and the current year, which many solo coaches meet. It does not lift KSeF (§ 8).
- **[ABSENT]** Rates on bar items and membership fees of associations (składki członkowskie): not
  researched beyond the above.

---

## Rivals × money features

As read on the dates above. "—" means not found on the public pages and help read.

| Feature | Playtomic Manager | Playmore | tenis4U | kluby.org | MATCHi |
| --- | --- | --- | --- | --- | --- |
| Online methods usable in PL | card, Apple/Google Pay; no BLIK/P24 | card, BLIK | Przelewy24, Tpay (club's own merchant account) | Przelewy24, PayU | — (Adyen, no PL method) |
| Fee to club on online money | contract commission (unpublished) | 1,79 % + from 299 zł/month | 49–149 zł/month, no % | 2 % + 50–79 zł+/month | 4 % service fee (player) |
| Partial prepayment | — | deposit ("kaucja") | — | 25/50/100 % | — |
| Desk payment link with auto-release | — | 30-min lapse on online booking | link, deleted after 60 min | — | link, valid 240 days, no release |
| Desk methods recorded | Cash, Credit Card, custom | cash, card, transfer | CASH, CARD_TERMINAL, benefit cards | settling at desk, combined payments | Mark as paid |
| Integrated card terminal | — | — | — | — | — |
| Cash drawer session | Cash Register | daily cash report | cash confirmed by/at | daily statement | — |
| POS / extras / stock | Store/POS, stock, Extras (Professional+) | POS, bar, shop, stock | — (rental vending machine) | shop, quick sale | merchandise as invoice rows |
| Refunds | auto online; club does cash | to Playmore wallet, fee kept | online minus 2 % | club's terms | annul with refund |
| Payout | weekly by payment date | daily, after the game | club's own P24 (next business day) | via P24/PayU | monthly by activity date |
| Reports for accountant | payments CSV, payout PDF | integrated monthly XLSX, 20+ reports | period report, CSV | accounting and payout XLSX | statements, receipts |
| Invoices | own tool, Champion plan, not PL | Fakturownia, "gotowość na KSeF" | — | own module, 0–60 zł/month | own + Fortnox |
| KSeF | — | stated ready | — | — | — |
| Fiscal printer | "no integration with POS printers" | — | — | yes (since November 2020) | — |
| E-receipt (e-paragon) | — | — | — | yes | — |
| VAT per product | yes | — | — | — | yes |

## Gaps

- **Stripe.**
  - Whether Terminal's "Preview" in PL needs an access request.
  - Whether Instant Payouts can be offered to Polish connected accounts by a platform.
  - BLIK dispute behaviour on direct charges, as the club sees it.
- **Revolut Reader pricing in Poland.** revolut.com answered 403. Elavon was not checked.
- **Playmore.**
  - Whether its POS prints fiscal receipts or drives a fiscal printer: nothing public.
  - The length of its settlement before the "daily, after the game" payout.
- **kluby.org.** Which invoicing provider sits behind "Faktury online", and whether it sends to KSeF.
- **wFirma and inFakt.** Invoice-only prices (their price pages render by JavaScript). Whether either
  drives fiscal printers.
- **Cloud fiscal printing.** No Posnet- or Elzab-published cloud API was found; only local bridges
  (Paragony.pl's module, the Posnet Server bridge).
- **Tax rulings still missing.**
  - A ruling on poz. 42 for Stripe Connect direct charges, or for one court-hour paid by several
    people (carried).
  - Whether a Stripe payout line and its reconciliation report satisfy "z ewidencji … jednoznacznie
    wynika, jakiej konkretnie czynności dotyczyła".
- **VAT.**
  - Rates on bar items and racket hire sold alone.
  - How associations' membership fees are treated.
  - How the VAT and the register treat a MultiSport visit: the club bills Benefit Systems, the player
    pays the remainder.
- **A company invoice for a shared court.** Whether one organiser can get one company invoice for a
  court the four sharers paid separately (carried).
- **The e-receipt route through the tax authority.** The exact start date of the route in art. 111
  ust. 3a pkt 1 lit. b, and whether club software can use it.
- **Kraków clubs' own practice.** What register each club runs and what its card terminal costs.
  *Ask a real club.*
