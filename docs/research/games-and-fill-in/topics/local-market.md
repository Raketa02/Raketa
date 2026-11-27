# Local market — Poland and Kraków

Topic `local-market` for PRD #530 (Games & Fill in). Launch market: Kraków, Poland; money in zł.

Most facts are carried over from [`../../games-and-fill-in-market.md`](../../games-and-fill-in-market.md) with their read
dates (2026-10-06/07); new ones carry **2026-10-08**.

Kinds: [POLICY] a company's rule, listing or terms · [PRICE] · [LAW] · [DOCS] a provider's, bank's, regulator's or
tax authority's document, or a published survey · [MEASURED] seen on a site (no screenshot) · [COMPLAINT] · [ABSENT].

---

## Payment methods

### BLIK volume and channel

- **[DOCS]** H1 2026: 1.6 bn BLIK transactions worth PLN 244.8 bn; 21.6 m active users. Online payments were 766.7 m (48.5 % of all BLIK transactions); phone-to-phone (P2P) transfers 393.6 m. [BLIK press release, 20 Aug 2026](https://www.blik.com/en/blik-delivers-a-strong-first-half-of-2026-1-6-billion-transactions-and-over-2-million-more-active-users-year-on-year) — read 2026-10-06

### How Poles pay online — cards are a minority

- **[DOCS]** NBP payment diary 2023 (remote payments, small sample): BLIK 49.7 % of count, all cards 25.0 %, of which a card on a phone or a digital wallet 6.1 %; transfers incl. pay-by-link 23.5 %. 86.7 % of respondents hold a card. [NBP: Zwyczaje płatnicze w Polsce w 2023 r.](https://static.nbp.pl/systemy/platniczy/Zwyczaje-platnicze-w-Polsce-2023.pdf) — read 2026-10-07
- **[DOCS]** Autopay survey, March 2025 (1,729 online shoppers, several answers allowed): BLIK 64 %, fast transfer 45 %, card 37 %, Google Pay 14 %, Apple Pay 10 %. [Autopay: Finanse Polek i Polaków 2025, p. 9](https://autopay.pl/storage/finanse-polek-i-polakow-2025---raport-z-badania.pdf) — read 2026-10-07
- **[DOCS]** Gemius 2025 via Przelewy24: BLIK 72 %, fast transfer 64 %, card 43 %. [Przelewy24 summary](https://www.przelewy24.pl/en/news/ecommerce-2025-online-shopping-trends-polish-consumers) — read 2026-10-06
- **[ABSENT]** Share of online shoppers with no card they would use online: not in NBP 2023, Autopay 2025, Tpay 2024/25 or Gemius 2025 summaries — read 2026-10-07

### Recurring BLIK at the banks

- **[DOCS]** Recurring BLIK ("płatności powtarzalne"): the payer approves once in the bank app; later payments are taken "automatycznie lub po Twoim potwierdzeniu"; every authorisation can be cancelled in the bank app. mBank became the 9th issuer on 6 Oct 2026. Named merchants: OpenAI, CANAL+, Onet Premium, Canva, Autopay. [BLIK, 6 Oct 2026](https://www.blik.com/platnosci-powtarzalne-blik-dostepne-dla-klientow-mbanku), [BLIK FAQ](https://www.blik.com/faq) — read 2026-10-06
- **[DOCS]** H1 2026: 3.6 m recurring BLIK payments (20× a year earlier), against 766.7 m one-off online ones. [BLIK, 20 Aug 2026](https://www.blik.com/en/blik-delivers-a-strong-first-half-of-2026-1-6-billion-transactions-and-over-2-million-more-active-users-year-on-year) — read 2026-10-06
- **[ABSENT]** A Polish court-booking platform with saved or recurring BLIK: none found (PADO lists BLIK but not when a share is charged). [PADO for clubs](https://pado.app/for-club) — read 2026-10-07

### BLIK at Stripe

- **[DOCS]** BLIK: PLN only, customer-initiated, Connect yes, **manual capture no**, refunds yes; code valid 2 minutes. Refunds "immediately or within a couple of hours" depending on the bank. Disputes go through BLIK's own claims process (evidence within 12 days). [Stripe: BLIK payments](https://docs.stripe.com/payments/blik) — read 2026-10-06
- **[DOCS]** Reusable BLIK is documented with no preview label; recurring charges are off-session only, at most **2,000 PLN** each, and only for customers of nine banks (others fail with `recurring_not_supported_by_bank`). The result arrives by webhook. [Stripe: BLIK recurring payments](https://docs.stripe.com/payments/blik/recurring-payments) — read 2026-10-06
- **[DOCS]** A saved payment method can be cloned to a connected account only if it is a `card` or `us_bank_account`, so a saved BLIK cannot follow the player to each club's account. [Stripe: direct charges across multiple accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-06
- **[DOCS]** In the React Native PaymentSheet, setup mode saves only cards and PayPal. [Stripe: Accept in-app payments (RN, setup)](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup) — read 2026-10-06

### Przelewy24 at Stripe

- **[DOCS]** Single-use only: no recurring, no SetupIntents, no manual capture. Refunds within 180 days, up to 3 business days, never a reversal; no chargebacks. MCC 7941 "Sports Clubs/Fields" is *restricted* (extra information at account creation). [Stripe: Przelewy24](https://docs.stripe.com/payments/p24) — read 2026-10-06

### Apple Pay and Google Pay for a later charge

- **[DOCS]** A default Apple Pay token is device-bound and "can cause failures for future merchant-initiated transactions"; merchant tokens cover subscriptions, automatic reloads and deferred payments. The RN SDK offers `Recurring`, `AutomaticReload`, `MultiMerchant` — no deferred type. [Stripe: Apple Pay merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens), [stripe-react-native PaymentRequestType](https://stripe.dev/stripe-react-native/api-reference/enums/PlatformPay.PaymentRequestType.html) — read 2026-10-06
- **[ABSENT]** A Stripe page on saving Apple Pay once for a one-off, unscheduled later charge — read 2026-10-06

### What Polish operators charge, against Stripe

- **[PRICE]** Stripe Poland: standard EEA cards 1.5 % + 1 zł; premium EEA 1.9 % + 1 zł; UK 2.5 % + 1 zł; international 3.25 % + 1 zł; BLIK 1.6 % + 1 zł; Przelewy24 1.9 % + 1 zł. [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-06
- **[PRICE]** Przelewy24 1.29 % + 30 gr for cards, wallets, BLIK and transfers. [Przelewy24 cennik](https://www.przelewy24.pl/rozpoczecie-wspolpracy) — read 2026-10-07. Tpay STARTER 1.59 % + 0.39 zł (BLIK + 0.41 zł), recurring BLIK at the same rate. [Tpay oferta](https://tpay.com/oferta) — read 2026-10-07. PayU 1.1 % + 0.30 zł. [PayU oferta](https://poland.payu.com/oferta-handlowa/) — read 2026-10-07
- **[PRICE]** On a 40 zł share: Stripe 1.60 zł; Przelewy24 ≈ 0.82 zł; Tpay ≈ 1.03 zł; PayU ≈ 0.74 zł; a flat 2 % (below) 0.80 zł. On 20 zł Stripe takes 1.30 zł (6.5 %). Arithmetic on the pages cited.

### The refund deduction players already know: a flat 2 %

- **[POLICY]** tenis4U, the booking system of most Kraków padel clubs, refunds a cancelled online booking "pomniejszonych o opłatę transakcyjną w wysokości 2%". [tenis4U regulamin pkt 11](https://tenis4u.pl/regulamin/) — read 2026-10-06
- **[POLICY]** Garden Padel refunds a weather cancellation "z potrąceniem opłaty serwisowej operatora płatności (2%)". [Garden Padel regulamin 5.3](https://gardenpadel.pl/regulamin) — read 2026-10-06

### How fast a refund arrives, by method

- **[DOCS]** Card: credit "approximately 5-10 business days later"; a refund soon after the charge may be a reversal (the charge drops off the statement). BLIK: immediately or within hours. Przelewy24: up to 3 business days. [Stripe: Refunds](https://docs.stripe.com/refunds), [Stripe: BLIK](https://docs.stripe.com/payments/blik), [Stripe: P24](https://docs.stripe.com/payments/p24) — read 2026-10-06
- **[ABSENT]** A Polish regulator or issuer page giving a card-refund time — searched BLIK, NBP, KNF — read 2026-10-06

### Paying a friend back: BLIK to a phone number and a payment request

- **[DOCS]** PKO BP: "Przelewy BLIK są darmowe", money arrives at once, 24/7, to anyone with a bank app and a phone number registered in BLIK. "Prośba o przelew BLIK" asks contacts at any BLIK bank for 1–500 zł; **one request can go to several people, for the same or different amounts**; the recipient has **72 hours** to accept or reject. [PKO BP: Przelew na numer telefonu](https://www.pkobp.pl/klient-indywidualny/aplikacja-iko-ipko/przelew-na-numer-telefonu) — read 2026-10-08
- **[ABSENT]** A public post showing Kraków players splitting a court by BLIK to the organiser: Facebook groups need a login; no readable post found. Searched "szukam … do padla Kraków BLIK", Facebook and WhatsApp group names — read 2026-10-06 and 2026-10-08

---

## Stripe Connect in Poland

### Direct charges make the club the seller

- **[DOCS]** "Direct charges: The merchant of record is the connected account." The payment flow, terms and receipt must make clear who the seller is; the club's descriptor shows on the player's statement; the seller "is also liable for any disputes or refunds". [Stripe: Merchant of record](https://docs.stripe.com/connect/merchant-of-record) — read 2026-10-06
- **[DOCS]** BLIK by direct charge shows the connected account's name in the banking app. [Stripe: BLIK § Connect](https://docs.stripe.com/payments/blik) — read 2026-10-06

### One saved card, charged on each club's account

- **[DOCS]** Save the card on the platform, then for each charge clone it to the club's account and confirm off-session there. A clone is consumed by one charge; customer permission travels with it. [Stripe: direct charges across multiple accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts), [Stripe: SCA for Connect platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms) — read 2026-10-06
- **[ABSENT]** Whether a clone consumed by a failed off-session attempt can be re-confirmed on the same PaymentIntent — read 2026-10-06

### What a Polish club must supply to Stripe

- **[DOCS]** Entity types for Poland: `individual` (sole trader, 18 fields), `company` (45 fields incl. owners and directors; REGON), `non_profit` (association, 36). All need an MCC, a business URL, a support phone and an IBAN. **No government type**, so a municipal centre (MOSiR/OSiR) has no documented path. [Stripe: Required verification information](https://docs.stripe.com/connect/required-verification-information) — read 2026-10-07
- **[DOCS]** Verification takes "anywhere from a few minutes to a few business days" per document; a missed deadline usually disables payouts first, then charges. [Stripe: Handle verification with the API](https://docs.stripe.com/connect/handling-api-verification) — read 2026-10-07
- **[DOCS]** PL accounts can hold `blik_payments`, `blik_recurring_payments` and `p24_payments`. [Stripe: Required verification information](https://docs.stripe.com/connect/required-verification-information) — read 2026-10-06

### Who pays Stripe's fees

- **[DOCS]** With `fees_collector=stripe`, Stripe sets and collects payment fees from the club and charges no Connect fee; dispute, Radar and 3-D Secure fees on the club's account are billed to the club. [Stripe: Fee behavior on connected accounts](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior), [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-06
- **[DOCS]** "Stripe's processing fees from the original transaction aren't returned" on a refund. [Stripe: Refunds](https://docs.stripe.com/refunds) — read 2026-10-06

### Disputes cost 90 zł and land on the club

- **[PRICE]** 90 zł per dispute received, never returned; another 90 zł to contest one, returned if won. [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-06
- **[DOCS]** On a direct charge the amount and fee come from the club's balance; Stripe's loss liability covers only a negative balance. For a future service "the dispute window starts on the event date" (120 days); a dispute takes 2–3 months. [Stripe: How disputes work](https://docs.stripe.com/disputes/how-disputes-work), [Stripe: Fee behavior](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior) — read 2026-10-06

### Refunds come out of the club's balance

- **[DOCS]** A refund on a direct charge is debited from the club's available balance. If it is short, a **card** refund waits as pending and fails after an expiry window; a refund of **any other method (BLIK, P24) fails** at once. [Stripe: Refunds](https://docs.stripe.com/refunds), [Stripe: How charges work in Connect](https://docs.stripe.com/connect/charges#refunds) — read 2026-10-06

### Payouts in Poland

- **[DOCS]** First payout 7 calendar days (7–14 by risk), then 3 business days; minimum 5 PLN; no fee. [Stripe: Payouts](https://docs.stripe.com/payouts) — read 2026-10-06
- **[DOCS]** Delaying a club's payouts needs loss liability or platform controls, which `losses_collector=stripe` does not give; "Stripe doesn't provide escrow services". [Stripe: Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule), [Stripe: Manual payouts](https://docs.stripe.com/connect/manual-payouts) — read 2026-10-06

### How long a hold lasts

- **[DOCS]** Card-not-present authorisation: Visa merchant-initiated 4 days 18 hours, Visa customer-initiated 7 days, Mastercard 7 days; after that the hold is released and the payment cancelled. Cancelling an uncaptured payment costs nothing. BLIK and P24 cannot be held. [Stripe: Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method), [Stripe: Refunds](https://docs.stripe.com/refunds) — read 2026-10-06

### Receipts on a direct charge come from the club's Stripe settings

- **[DOCS]** "Direct charges: Receipts use the connected account's **Customer emails**, **Branding**, and **Public details** settings." A platform can send one for a connected account by passing `receipt_email` on the charge. Automatic receipts go only for successful payments and refunds, and only if switched on. [Stripe: Receipts — Stripe Connect customizations](https://docs.stripe.com/receipts) — read 2026-10-08
- **[DOCS]** Every receipt must show the legal business name, a support address and email, and a privacy-policy URL. [Stripe: Receipts](https://docs.stripe.com/receipts) — read 2026-10-08

### Charging a saved card without the player there

- **[DOCS]** A merchant-initiated charge is outside SCA but needs a recorded agreement naming the transactions, timing, how the amount is set and the cancellation policy. [Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-06
- **[DOCS]** EBA: a payment counts as payee-initiated only if "not dependent on a specific action of the payer to trigger the initiation". [EBA Q&A 2018_4131](https://www.eba.europa.eu/single-rule-book-qa/qna/view/publicId/2018_4131) — read 2026-10-07
- **[ABSENT]** UOKiK or KNF guidance on charging a saved card later for a one-off service — searched both sites — read 2026-10-07

---

## Receipts, invoices and fiscal rules

### No cash register for sales paid fully online

- **[LAW]** Dz.U. 2024 poz. 1902 (to 31 Dec 2027), annex poz. 42: no cash register for services to consumers paid **in full** through a bank or payment institution to the seller's account, where the records show which sale each payment was for. Sports services are not excluded (§4). Part-paid at the desk = on the register. [Dz.U. 2024 poz. 1902](https://eli.gov.pl/api/acts/DU/2024/1902/text/O/D20241902.pdf) — read 2026-10-06
- **[DOCS]** KIS accepted poz. 42 for an app where a payment operator collects and pays out to the seller's bank account, each payment carrying booking identifiers; an emailed electronic payment confirmation suffices as proof. [KIS 0113-KDIPT1-3.4012.602.2026.2.JM, 17 Sep 2026](https://eureka.mf.gov.pl/informacje/podglad/710095) — read 2026-10-06
- **[DOCS]** Closest precedent: online prepayment for room reservations through an operator, reconciled to "konkretnej rezerwacji" from the operator's reports — exemption applies. [KIS 0114-KDIP1-3.4012.883.2024.1.KP, 4 Feb 2025](https://eureka.mf.gov.pl/informacje/podglad/624727) — read 2026-10-06
- **[ABSENT]** A ruling on a court-booking platform paid by Stripe Connect — searched Eureka — read 2026-10-06

### Invoices: on request for consumers, always for businesses

- **[LAW]** A consumer gets an invoice only if asked within 3 months from the end of the month of the service or payment (art. 106b ust. 3 VAT Act); a business always (ust. 1). A sale rung through a register may be invoiced to a business only if the receipt carried its NIP (ust. 5–6). [KIS 710095 quoting art. 106b](https://eureka.mf.gov.pl/informacje/podglad/710095), [VAT Act, Dz.U. 2025 poz. 775](https://api.sejm.gov.pl/eli/acts/DU/2025/775/text.pdf) — read 2026-10-06

### KSeF

- **[DOCS]** Mandatory from 1 Feb 2026 (sales > PLN 200 m), 1 Apr 2026 (everyone else), 1 Jan 2027 (invoices ≤ PLN 10,000 a month); penalties from 1 Jan 2027. Invoices to consumers need not go through KSeF. So a club's invoice to a company NIP goes through KSeF; a fiscal receipt does not. [KSeF: Zasady obowiązywania](https://ksef.podatki.gov.pl/ksef-news/zasady-obowiazywania-ksef-i-przepisy-prawne/), [Etapy wdrożenia](https://ksef.podatki.gov.pl/etapy-wdrozenia-ksef/) — read 2026-10-06

### VAT on court time is 8 %

- **[DOCS]** Padel court rental to individuals: PKWiU 93.11.10.0, 8 % (WIS of 13 Apr 2026); tennis and squash likewise. A company booking for its staff was once classed 23 % (Nov 2023) and set back to 8 % on appeal (Jun 2024). Lessons are a different service (85.51.10.0). [WIS 687645](https://eureka.mf.gov.pl/informacje/podglad/687645), [appeal 590581](https://eureka.mf.gov.pl/informacje/podglad/590581), [WIS 698583](https://eureka.mf.gov.pl/informacje/podglad/698583) — read 2026-10-06

### Playtomic offers nothing for Polish fiscal rules

- **[ABSENT]** No Polish fiscal export, receipt, KSeF or JPK in Playtomic's 157 club help articles; tax pages exist only for Portugal and Mexico. [Playtomic Manager help](https://helpmanager.playtomic.com/hc/en-gb/articles/40674001404433-Tax-Information-for-Portuguese-Clubs) — read 2026-10-06

---

## Consumer law on cancelling and refunds

### No 14-day withdrawal for a dated court booking

- **[LAW]** Art. 38 ust. 1 pkt 12: no withdrawal right for "usług związanych z wypoczynkiem, wydarzeniami rozrywkowymi, sportowymi lub kulturalnymi, jeżeli w umowie oznaczono dzień lub okres świadczenia usługi". [Ustawa o prawach konsumenta, Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf) — read 2026-10-06
- **[DOCS]** The Commission reads it narrowly: it applies where the booking sets aside capacity the trader "may find difficult to fill". [Commission Notice 2021/C 525/01 §5.11.6](http://publications.europa.eu/resource/celex/52021XC1229%2804%29) — read 2026-10-07
- **[POLICY]** PADO and Playmore state the exemption in their terms; Playtomic's Legal Conditions are silent. [PADO Terms §8](https://pado.app/terms), [Playtomic Legal Conditions](https://playtomic.com/legal-conditions) — read 2026-10-07

### What the player must see before being bound

- **[LAW]** Art. 12: the service, the **seller's identity and address** (the club's, when Rakieta concludes for it — ust. 2), the total price, how and when payment is taken, and that there is no withdrawal right — "najpóźniej w chwili wyrażenia przez konsumenta woli związania się umową". Art. 21: a confirmation on a durable medium before the service. Art. 22: that information is part of the contract. [Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf) — read 2026-10-06
- **[LAW]** Art. 12a (online marketplace): the main ranking parameters, whether the seller is a trader, and how duties are split between the seller and the platform. [Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf) — read 2026-10-06

### The order button and a yes that charges later

- **[LAW]** Art. 17 ust. 3: an order control must read "zamówienie z obowiązkiem zapłaty" or an equivalent; otherwise "umowa nie zostaje zawarta" (ust. 4). [Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf) — read 2026-10-07
- **[LAW]** CJEU C-400/22 *Conny*: the rule applies even when payment is due "only after a subsequent condition has been satisfied". C-249/21 *Fuhrmann-2*: only the words on the button count. [C-400/22](http://publications.europa.eu/resource/celex/62022CJ0400), [C-249/21](http://publications.europa.eu/resource/celex/62021CJ0249) — read 2026-10-07
- **[DOCS]** UOKiK: "kup teraz", "zapłać teraz", "potwierdź zakup" pass; "zarejestruj", "potwierdź", "zamów teraz" do not; on 4 Feb 2026 it rejected "Zamawiam". [UOKiK Q&A](https://prawakonsumenta.uokik.gov.pl/pytania-i-odpowiedzi/prawo-do-informacji/), [UOKiK](https://uokik.gov.pl/Download/1757) — read 2026-10-07
- **[ABSENT]** Any authority on a swipe, on "Dołączam"/"I'm in", or on a price printed on the button — read 2026-10-07

### Which terms bind when a yes becomes a booking later

- **[LAW]** Civil Code: an acceptance with changes is a new offer (art. 68); standard terms bind only if delivered before the contract (art. 384). [Kodeks cywilny, Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf) — read 2026-10-07
- **[DOCS]** UOKiK (Amazon, Dec 2023): new prices or terms may reach a later automatic charge "only with the prior consent of the consumer". [UOKiK](https://uokik.gov.pl/en/change-in-subscription-terms-only-with-your-permission) — read 2026-10-06

### Cancellation fees and abusive clauses

- **[LAW]** Art. 385³ KC presumes abusive a clause that keeps payment for a service not performed when the consumer withdraws (pkt 12), a fixed sum for cancelling (pkt 16), or a grossly excessive penalty (pkt 17). [Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf) — read 2026-10-06
- **[DOCS]** UOKiK: on giving up a pre-paid leisure service the trader may keep only "faktycznie poniesionym kosztom"; it made a dance studio drop "bez możliwości zwrotu" for hall reservations. [UOKiK archive, 2014](https://archiwum.uokik.gov.pl/aktualnosci.php?news_id=11103) — read 2026-10-06
- **[ABSENT]** A court or UOKiK decision on padel or tennis late-cancellation fees — read 2026-10-06

### The payer's 8-week refund right on a charge they didn't trigger

- **[LAW]** For a payee-initiated payment whose exact amount was not set at authorisation and is higher than the payer could expect, the payer may claim a refund from their bank within 8 weeks (art. 47–48). [Ustawa o usługach płatniczych, Dz.U. 2025 poz. 611](https://api.sejm.gov.pl/eli/acts/DU/2025/611/text.pdf) — read 2026-10-07

### A complaint must be answered within 14 days

- **[LAW]** Art. 7a: unless another act says otherwise, the trader must answer a consumer's complaint within 14 days of receiving it, on paper or another durable medium; with no answer in time "uważa się, że uznał reklamację". [Art. 7a, text on LexLege (state of 24 Jun 2026)](https://lexlege.pl/ustawa-o-prawach-konsumenta/art-7a/) — read 2026-10-08 (the Sejm PDF could not be parsed here)

---

## Benefit sports cards

### How many cards

- **[DOCS]** End of Q3 2026: **1,902.7 thousand active Benefit Systems (MultiSport) cards in Poland** (2,747.2 thousand in all markets). [Benefit Systems RB 45/2026, 1 Oct 2026](https://corp.benefitsystems.pl/en/for-investors/article/rb-452026-quarterly-information-on-active-sport-cards-number/) — read 2026-10-08 (end of Q2 2026 was 1,876.3 thousand: [RB 38/2026](https://corp.benefitsystems.pl/en/for-investors/article/rb-382026-quarterly-information-on-active-sport-cards-number/), read 2026-10-06)
- **[DOCS]** MultiSport covers "more than 100 padel courts" nationally; cardholders' padel visits rose nearly threefold. [Benefit Systems, 7 Feb 2026](https://biuroprasowe.benefitsystems.pl/the-rocket-takes-centre-stage-will-the-tennis-boom-move-from-the-screen-to-the-courts) — read 2026-10-06
- **[ABSENT]** Holder counts for Medicover Sport, PZU Sport, FitProfit (fitprofit.pl returned 403) — read 2026-10-06

### How the operators say a card is used

- **[POLICY]** MultiSport: show the app QR or plastic card plus ID at reception; surcharges and conditions are each facility's. [MultiSport help](https://pomoc.emultisport.pl/pl/articles/392787-wejscie-do-obiektu-sportowego) — read 2026-10-06
- **[POLICY]** Medicover Sport: the entry is registered at the facility "nie wcześniej niż 15 … minut przed jej rozpoczęciem"; personal only; booking rules and no-show consequences are the partner's. [Medicover Sport rules from 1 Jun 2025](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-06

### How Kraków clubs take the cards: about 15 zł off per card, on site

- **[POLICY]** Squash4You: a partner card "nie zastępuje rezerwacji kortu"; after a no-show or late cancellation it cannot be used and the full court is owed. [Squash4You regulamin §11](https://www.squash4you.pl/regulamin) — read 2026-10-06
- **[PRICE]** 15 zł off the court per card (30 zł for two) at Fame Sport, Padel House, Squash4You; KSOS takes 15 zł off via a code. Fame Sport: the discount comes off the regular price and does not combine. [Fame Sport cennik](https://famesport.pl/cennik/), [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow), [KSOS](https://obiekty.ksos.pl/korty-tenisowe/) — read 2026-10-06/07
- **[MEASURED]** tenis4U's web app calls a per-booking payment calculation with `benefit_cards` and a `medicover-verify` step (seen in its code, no screenshot). [app.tenis4u.pl](https://app.tenis4u.pl/) — read 2026-10-06
- **[COMPLAINT]** A Polish Playtomic user asks it to "Add Medicover cards". [App Store PL: Playtomic](https://apps.apple.com/pl/app/playtomic-padel-tennis/id1242321076?see-all=reviews) — read 2026-10-06

---

## Status quo — clubs

### Which booking systems Kraków clubs run

- **[POLICY]** tenis4U (Kraków-based; 372 clubs, 1,478 courts; 49–149 zł a month) runs Garden Padel, Padel House, Fame Sport, Morelowa 34; Playmore (Reservise) runs Atras, Squash4You, Miazga; SAO Sports Hub has its own app; KSOS its own system. Phone and desk booking remain at every club read. [tenis4U](https://tenis4u.pl/), [Atras](https://www.atrassquash.pl/rezerwacje/), [Miazga](https://www.miazgasquash.pl/rezerwacje/), [SAO](https://saosports.pl/) — read 2026-10-06
- **[POLICY]** tenis4U 4.3.x (Apr 2025) added inviting players to a booking and sharing payment; 4.9.1 (Oct 2026) added time passes. Rated 4.7 from 98 ratings; no partner search in the description. [App Store PL: tenis4U](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113) — read 2026-10-08

### The club is the seller; the platform is not a party

- **[POLICY]** tenis4U "nie jest stroną umów", payments via Przelewy24 and Tpay; kluby.org likewise, via Przelewy24 and PayU; cancellation rules are the club's. [tenis4U regulamin](https://tenis4u.pl/regulamin/), [kluby.org regulamin](https://kluby.org/regulamin) — read 2026-10-06

### Paying ahead, and online is cheaper than the desk

- **[POLICY]** Garden Padel: "Rezerwacja jest ważna po dokonaniu płatności online (Przelewy24) lub w recepcji". SAO: paid in the app at booking. [Garden Padel 4.1](https://gardenpadel.pl/regulamin), [SAO](https://saosports.pl/) — read 2026-10-06
- **[PRICE]** Atras: online 10 % cheaper; squash 40 zł online vs 49 zł at the desk; Squash4You and Racquet +5 zł at the desk. [Atras](https://www.atrassquash.pl/rezerwacje/), [Sportano](https://sportano.pl/blog/squash-krakow-sprawdz-gdzie-znajdziesz-korty-do-squasha-w-krakowie) — read 2026-10-06
- **[POLICY]** Playmore's case study: a club went from ~20 % to 100 % online payment and to 0 unpaid bookings a month. [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-06

### The cut-off is 24 hours; late means the full price unless the court is resold

- **[POLICY]** Garden Padel, Fame Sport, Atras, Squash4You, Miazga, KSOS: free until 24 h; SAO 12 h; Fame Sport's fixed weekly slots 48 h. After it the money is kept. Atras, Miazga and Squash4You waive it only if someone else books the court; Squash4You's reception "będzie starał się w pierwszej kolejności sprzedać" the slot. [Garden Padel 5.2](https://gardenpadel.pl/regulamin), [Atras](https://www.atrassquash.pl/regulamin/), [Squash4You §5](https://www.squash4you.pl/regulamin), [Miazga §4](https://www.miazgasquash.pl/regulamin/), [Fame Sport II.5–19](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-06
- **[POLICY]** Squash4You moves a prepaid booking cancelled in time to the next booking rather than refunding. [Squash4You §5](https://www.squash4you.pl/regulamin) — read 2026-10-06

### The booker owes the whole court

- **[POLICY]** Fame Sport: on a late cancellation or no-show "osoba dokonująca rezerwacji zobowiązana jest do uiszczenia pełnej opłaty"; AGH Kraków charges "osoba na którą widnieje rezerwacja". [Fame Sport II](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf), [AGH III.6](https://swfis.agh.edu.pl/home/swfis/dokumenty/REGULAMIN_KORZYSTANIA_Z_KORTU_DO_SQUASHA.pdf) — read 2026-10-06
- **[POLICY]** POSiR Poznań: one person pays the whole booking; "Nie ma możliwości dzielenia płatności". [POSiR §3.10](https://www.posir.poznan.pl/images/obiekty/Rataje/Korty%20tenisowe/regulamin-korty.pdf) — read 2026-10-06
- **[POLICY]** kluby.org split payment: if invited players haven't paid within 2 hours after the game, the **booker's saved card** is charged for their shares, else a debt is recorded. [kluby.org Załącznik 3 §4](https://kluby.org/regulamin/karty-platnicze) — read 2026-10-06

### No-shows: blocked until paid

- **[POLICY]** Miazga: a no-show without notice may cancel all later bookings and block booking until the debt is paid; Atras tells the player of the debt the same or next day; kluby.org shares club blocks and blocks an account blocked by 2 clubs. [Miazga §4](https://www.miazgasquash.pl/regulamin/), [Atras](https://www.atrassquash.pl/regulamin/), [kluby.org §IV–V](https://kluby.org/regulamin) — read 2026-10-06

### Weather on outdoor courts

- **[POLICY]** Court closed for weather: Garden Padel refunds minus 2 %; Fame Sport and SAO in full; KSOS, rain mid-game: no refund, replay within 7 days. [Garden Padel 5.3](https://gardenpadel.pl/regulamin), [Fame Sport II.21](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf), [KSOS](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/) — read 2026-10-06

### Fixed weekly slots take the prime hours

- **[POLICY]** Fame Sport sells 12-week and season slots paid up front (5–10 % off); the holder may let others use the slot. [Fame Sport III](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-06

### Court prices in Kraków

- **[PRICE]** Fame Sport indoor padel, winter 2026/27: 135 zł (weekday 7–14), 150 zł (weekday 14–23), 140 zł (weekend). [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-06
- **[PRICE]** Padel House 120 / 160 zł; Garden Padel 100–130 zł; Bajada 80–100 zł; Libertów 100–110 zł (third-party listings). [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow), [PADO: Bajada](https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow) — read 2026-10-06; [PADO: Libertów](https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club) — read 2026-10-08
- Range: 80–160 zł a court-hour, so **20–40 zł a player** for four.

### Clubs' own open games: Playmore *Gry otwarte*

- **[POLICY]** A player picks a free hour, publishes the game and pays his share; each joiner pays at once; "Brak kompletu przed startem – rezerwacja cofnięta i pełny zwrot dla wszystkich." The club sets the cut-off for a short game (1–48 h) and the free-cancel window (0–72 h). Free in every package. App version of 10 Jul 2026. [Playmore: Gry otwarte](https://join.playmore.pl/gry-otwarte/), [App Store PL](https://apps.apple.com/pl/app/reservise-playmore/id928403015) — read 2026-10-06
- **[PRICE]** Playmore adds 1.48 zł to each online booking at Atras. [Playmore: Atras](https://playmore.pl/klub/atras-squash-club/) — read 2026-10-06
- **[POLICY]** PADO's club CRM and Playmore offer waiting lists for freed court slots, not for a seat in a paid game. [PADO for clubs](https://pado.app/for-club), [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-07

### What a club says it lacks today

- **[POLICY]** Playmore's pitch to clubs: "Wieczory wyprzedane, ale rano i wczesnym popołudniem korty stoją puste"; "Bez partnera gracz nie zarezerwuje kortu - po prostu nie przyjdzie"; "Nie ma narzędzia, żeby zestawić ze sobą dwóch chętnych na tę samą godzinę"; "Każda taka próba to telefony i wiadomości". Its comparison against "Telefon i WhatsApp" lists: payment from everyone up front, equal split, automatic refund if short, status notices, no desk work. [Playmore: Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-08

---

## Status quo — organisers

### The organiser books, and carries the court

- See *The booker owes the whole court* above (club rules and kluby.org's 2-hour charge to the booker).
- **[COMPLAINT]** On Playtomic, "the organizer takes the hit" when partners don't pay (research file §5). [games-and-fill-in-market.md §5](../../games-and-fill-in-market.md) — read 2026-10-06

### Collecting the shares

- See *Paying a friend back* above: a free, instant BLIK transfer, or one request to several friends.
- **[POLICY]** tenis4U lets the booker invite players and share the payment (since Apr 2025). [App Store PL: tenis4U](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113) — read 2026-10-08

### Arranging by WhatsApp: a Kraków padel league

- **[POLICY]** Padel Krakow League (on kluby.org; levels B1–B3, 1 Jun–30 Sep 2026): 280 zł a pair by bank transfer; "Matches are played at any Kraków facility, as agreed by players. Court costs, balls, and rackets are covered by players." Pairs "contact other pairs … via the whatsapp community dedicated to the League". "A no-show = full court fee responsibility, unless both teams agree otherwise." A team that keeps not answering loses 6–0 6–0 by walkover. Levels for unranked players by self-evaluation over WhatsApp. [Padel Krakow League: regulamin](https://kluby.org/liga/padel-krakow-league/regulamin) — read 2026-10-08
- **[MEASURED]** 119 league matches recorded by 8 Oct 2026. [Padel Krakow League](https://kluby.org/liga/padel-krakow-league) — read 2026-10-08

### A meetup splits the court among whoever comes

- **[POLICY]** Padel Meetup at Morelowa (Palmar, Dec 2024, all levels): "The cost of the court is 150zł/h, but don't worry, we'll split it among all the players"; sign-up by a Register button; no drop-out rule. [Luma: Padel Meetup – Morelowa](https://luma.com/ts731n9z) — read 2026-10-08

---

## Status quo — joiners

### Where a joiner finds a game

- **[POLICY]** Aggregators list Kraków clubs and send the player to the club's own booking: Playmore lists 9 padel venues ("rezerwacja u operatora klubu"), Planeta Padla 7, PADO several. [Playmore: Kraków](https://playmore.pl/padel/krakow/), [Planeta Padla: Kraków](https://planetapadla.pl/cities/krakow) — read 2026-10-06
- **[ABSENT]** Open games or "szukam gry" posts for Kraków on Planeta Padla's city page: none shown. [Planeta Padla: Kraków](https://planetapadla.pl/cities/krakow) — read 2026-10-08
- **[ABSENT]** Kluby.org's "Sparingi" listings load by JavaScript and could not be read. [kluby.org: padel sparingi](https://kluby.org/padel/sparingi) — read 2026-10-08

### What a joiner owes today

- In the league a no-show owes the full court unless both sides agree; at a club the booker owes it (sections above).
- **[COMPLAINT]** Playmore: "Contacted the app support for refund—they bounced me off to the club. Contacted the club—the club bounced me off to the app" (25 Mar 2025). [App Store PL: Reservise Playmore](https://apps.apple.com/pl/app/reservise-playmore/id928403015) — read 2026-10-06

---

## Status quo — newcomers

### A beginners' americano: sign up alone, pay per head

- **[PRICE]** Padel House Kraków, "Americano B3/C – DLA POCZĄTKUJĄCYCH", 28 Nov 2025, 19:00–21:00: 90 zł, 18 players, sign up individually; the system pairs you with a new partner each of ~10 short matches. Payment and refund rules not stated. [LigaPadla.pl](https://rozgrywki.ligapadla.pl/padel-house-krakow/turnieje/americano-c-oficjalne-otwarcie-padel-house-115/2025-11-28) — read 2026-10-08
- **[PRICE]** Libertów "Americano Español", 15 Nov 2025: 100 zł a person, 8 players on 2 courts, B2/B1, food included (search-result summary of the kluby.org event, page not opened). [kluby.org turniej 10700](https://kluby.org/turnieje/10700) — read 2026-10-08

### A league pairs players who come alone

- **[POLICY]** Padel Krakow League: "Players may register as pairs or as individuals, who will be matched into pairs after the registration period ends". [regulamin](https://kluby.org/liga/padel-krakow-league/regulamin) — read 2026-10-08

### Clubs' own community channels

- **[POLICY]** Garden Padel's Instagram bio reads "Rezerwuj: Tenis4u WhatsApp group👇🏽Matchmaking🔥" (seen only in a search-engine snippet; Instagram would not load). [Instagram: gardenpadel_krakow](https://www.instagram.com/gardenpadel_krakow/) — read 2026-10-08

---

## Playtomic in Poland and Kraków

### No Kraków club on Playtomic

- **[ABSENT]** No Kraków club on playtomic.com: the nearest-club lists on the Katowice, Tychy, Pszczyna and Bielsko-Biała pages reach Opole and Wrocław without one; guessed Kraków slugs return 404; web search found none (again 2026-10-08). [Playtomic: One Padel Center](https://playtomic.com/clubs/one-padel-center) — read 2026-10-06
- **[POLICY]** Planeta Padla claims "Większość polskich klubów padlowych obsługuje rezerwacje przez Playtomic lub kluby.org" (an aggregator's claim). [Planeta Padla FAQ](https://planetapadla.pl/faq) — read 2026-10-06

### Where Playtomic is in Poland

- **[MEASURED]** 33 Polish clubs found by following "clubs near" links from Polish club pages, all priced in PLN, almost all padel: Warszawa 6, Poznań area 8, Silesia 8, Toruń area 4, Wrocław area 3, one each in Bydgoszcz, Gdynia, Olsztyn, Opole. A lower bound, no screenshot. [Playtomic sitemap](https://playtomic.com/sitemap.xml) — read 2026-10-06
- **[ABSENT]** An official Polish club count or city page — read 2026-10-06

### Playtomic speaks no Polish outside the app

- **[POLICY]** App Store PL: 4.8 from ~1,475 ratings, Polish among 13 languages, Premium 47.99 zł a month. [App Store PL](https://apps.apple.com/pl/app/playtomic-play-padel/id1242321076) — read 2026-10-06
- **[ABSENT]** A Polish website (`/pl` is 404), help-centre locale or support language. [Playtomic: Customer Support](https://playerhelp.playtomic.com/hc/en-gb/articles/19831718711569-Playtomic-Customer-Support) — read 2026-10-06

### No BLIK, no Przelewy24, no Polish sport cards

- **[ABSENT]** BLIK or Przelewy24 anywhere in Playtomic's 94 player and 157 club articles or Legal Conditions; Poland is on none of its country lists (card on file, pre-authorisation, local methods). [Playtomic: Payment Methods](https://playerhelp.playtomic.com/hc/en-gb/articles/19831969439761-Payment-Methods-in-Playtomic), [Manager: Payment methods](https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281-Payment-methods-available-in-Playtomic) — read 2026-10-06
- **[POLICY]** Third-party sport cards work only through a club partnership; the providers named are none of the Polish ones. [Playtomic: Third-Party Membership Benefits](https://playerhelp.playtomic.com/hc/en-gb/articles/44586083037201-How-Third-Party-Membership-Benefits-Work-on-Playtomic) — read 2026-10-06

---

## Not found in this round

### Gaps left open

- **[ABSENT]** Readable Kraków Facebook/WhatsApp posts showing how a fourth player is found and paid back — Facebook needs a login, Instagram would not load — read 2026-10-08
- **[ABSENT]** Payment and refund rules for a club americano entry (Padel House's event page states neither) — read 2026-10-08
- **[ABSENT]** Benefit Systems' own racket-sport rules (cardholders per court, surcharge) — read 2026-10-06
