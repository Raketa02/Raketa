# Gaps — PAY (a way to pay)

Answers to the PAY area's open gaps for PRD #530 (`$W/areas/PAY/gaps.md`), read **2026-10-08**. One section per
rule; every fact sits under a `###` heading so it can be cited as `topics/gaps-PAY.md#<heading>`. Facts already
in `local-market.md`, `competitor-*.md` or `platforms.md` are cited there, not repeated.

Kinds: [POLICY] a company's rule, help page or the text its own app shows · [PRICE] · [LAW] · [DOCS] a provider's,
network's, regulator's or tax authority's document, or a published survey · [MEASURED] read from the product itself
(app package text or web app code; the extract is saved under `../shots/`, no screen image) · [COMPLAINT] ·
[ABSENT] looked for and not found, with where.

App packages read: Playtomic Android 6.93.2 (`com.playtomic`) and Playmore/Reservise Android 6.118.0
(`com.reservise.reserviseapp`), both from APKPure on 2026-10-08; the Playtomic strings quoted below are saved in
[`../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt`](../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt).

---

## R-PAY-24 — removing a saved card

### Playtomic asks before it removes a card
- **[MEASURED]** The Android app's own text carries a confirm step: "Remove card?", "Are you sure you want to
  remove this card?", "Are you sure you want to remove this credit card?", with the action "Remove payment method";
  the payment-methods screen is "Manage, add, and delete your payment methods, including your Wallet and credit or
  debit cards." [Playtomic on Google Play](https://play.google.com/store/apps/details?id=com.playtomic) (package
  6.93.2), extract in [`../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt`](../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[POLICY]** A card that guarantees a split booking cannot be removed: "You cannot remove your card while you are
  responsible for a split payment booking that has not yet been played"; "you can remove your saved card at any
  time, as long as you do not have upcoming split payment bookings pending". The app says: "This card can't be
  deleted. It is being used as a guarantee in an ongoing split payment booking." [Playtomic help: Card on File (CoF)
  in split payments](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457) (updated 2026-09-15), same
  extract — read 2026-10-08
- **[POLICY]** Removing and re-entering the card is Playtomic's own repair for a wrong CVC or expiry ("delete the card
  and enter it again"), so players are sent to Remove on purpose. [Playtomic help: Credit/debit card issues](https://playerhelp.playtomic.com/hc/en-gb/articles/19831469004305) (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** For the US/Canada club *Card on File*: "Remove a card or revoke a club's permission to charge it at any
  time" from the club's profile; no confirm step is described. [Playtomic help: Card on File (US and Canada)](https://playerhelp.playtomic.com/hc/en-gb/articles/41522182623505) (updated 2026-08-19) — read 2026-10-08

### Playmore saves no card, so there is nothing to remove
- **[MEASURED]** Neither the web app's text nor the Android app (a web app in a Capacitor shell, 1,001 script
  files) holds a saved card, a card list or a remove-card action. Online payment goes to the operator's page:
  "Metodę płatności wybierzesz na bezpiecznej stronie płatności"; methods are BLIK, Przelew, Apple Pay, Google Pay,
  wallet and pass. Searched "usuń kartę", "usunąć kartę", "zapisan* kart", "zapamiętaj kart", "Twoje karty",
  "savedCard", "setup_future_usage". The only "Czy na pewno chcesz usunąć" is for a court alert. [Playmore web app
  scripts](https://playmore.pl/), [Playmore on Google Play](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp) (package 6.118.0) — read 2026-10-08

### kluby.org lets a card go at any time; a confirm step is not described
- **[POLICY]** "Użytkownik może w dowolnym momencie: usunąć zapisaną kartę, dodać nową kartę, wyłączyć korzystanie z
  zapisanej karty poprzez ustawienia konta w aplikacji. Usunięcie karty powoduje natychmiastową utratę możliwości
  obciążenia jej w przyszłości." The card is held by PayU; it is charged without the player only for a split
  booking's unpaid shares 2 h after the game. [kluby.org: Załącznik — karty płatnicze §4–5](https://kluby.org/regulamin/karty-platnicze) — read 2026-10-08
- **[ABSENT]** Whether kluby.org asks before removing: the account settings need a login, and neither the terms nor
  the public script (`/js/script.js`) mention it. [kluby.org](https://kluby.org/js/script.js) — read 2026-10-08

---

## R-PAY-42 — payment history once the card is removed

### Playtomic keeps transactions apart from payment methods
- **[POLICY]** "You can see all payment and refund transactions in your profile. Simply click on the three bars in the
  top right corner and go to Your payments menu." [Playtomic help: Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593) (updated 2026-09-10) — read 2026-10-08
- **[MEASURED]** In the app, *Your payments* is subtitled "Payment methods, transactions, club memberships..."; the
  history is its own list ("Payment history", "Transactions", "All transactions"; empty: "You don't have any
  transactions", "All transactions you make will be displayed here."), with receipts on request ("Get the invoice by
  email", "Get Service Fee receipt by email", "Get cancellation receipt by email"). Android 6.93.2, extract in
  [`../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt`](../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** No help article or app text says what happens to past transactions when the card that paid them is
  removed. That they stay is a reading of the layout (transactions are a list of purchases beside the methods), not a
  stated fact. Searched the player help for "remove card", "delete card", "your payments", "payment method" — read 2026-10-08

### Playmore's history sits in the wallet and the bookings
- **[MEASURED]** The web app's wallet has "Historia transakcji" and "Ostatnie transakcje" with filters by date range;
  refunds land there: "W klubach z portfelem Playmore pieniądze nie wracają na kartę płatniczą — czekają tutaj na
  Ciebie." No card is ever saved (above), so the history cannot depend on one. [Playmore web app scripts](https://playmore.pl/) — read 2026-10-08

### kluby.org's payment history is not public
- **[ABSENT]** Whether kluby.org shows past payments after a card is removed: the account pages need a login and the
  terms say only that removing stops future charges. [kluby.org: karty płatnicze §5](https://kluby.org/regulamin/karty-platnicze) — read 2026-10-08

---

## R-PAY-1 — the club's card cost at its own desk, and Stripe's custom pricing

### What a desk terminal costs a Polish club per card payment
- **[PRICE]** PKO BP (terminals run by eService), standard offer: 0.55 % Visa, 0.55 % Mastercard, 0.39 % BLIK, no
  fixed fee per payment listed; rental 39.99 zł a month (fixed or portable terminal) or 29.90 zł (SmartPOS). Under
  *Polska Bezgotówkowa*: 0 % on all three for 12 months up to 100,000 zł of turnover, rental 0 zł, then 1 zł a month
  for 18 months. [PKO BP: Terminal płatniczy](https://www.pkobp.pl/firmy/uslugi-dla-firm/terminal-platniczy) — read 2026-10-08
- **[PRICE]** mBank with PolCard (Fiserv): cards 0 % up to 100,000 zł, then 0.59 % + 4 gr; BLIK 0.39 % + 10 gr; rental
  33 zł net a month after 24 months. Only for a business that took no card payments in the past 12 months.
  [mBank: Polska Bezgotówkowa](https://www.mbank.pl/firmy/terminale/darmowe-terminale/polska-bezgotowkowa/) — read 2026-10-08
- **[PRICE]** SumUp: 1.49 % per in-person card payment, no monthly fee; *Płatności Plus* 89 zł a month for 0.79 % on
  debit and credit cards (1.49 % on premium and Amex), pitched at 16,400 zł a month and up. [SumUp: cennik](https://www.sumup.com/pl-pl/cennik/) — read 2026-10-08
- **[PRICE]** Arithmetic on these pages, one 160 zł court-hour paid at the desk with one card: PKO 0.88 zł, PolCard
  about 0.98 zł, SumUp 2.38 zł. Four 40 zł cards at PKO: 0.88 zł in all (0.22 zł each), since there is no fixed fee.
  On Stripe the same four shares cost 6.40 zł (1.5 % + 1 zł each, `local-market.md#what-polish-operators-charge-against-stripe`), plus nothing a month.
- **[LAW]** The ceiling under all of these: interchange on a consumer debit card is at most 0.2 % and on a consumer
  credit card 0.3 % of the payment. [Regulation (EU) 2015/751, Art. 3(1) and 4](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015R0751) — read 2026-10-08
- **[ABSENT]** What a named Kraków club actually pays at its desk: terminal contracts are priced per contract, and no
  club, tenis4U or kluby.org page read for this folder states one; no public rate was found for Polskie ePłatności
  (web search) — read 2026-10-08

### Stripe's custom pricing in Poland: on request, for large volume
- **[PRICE]** Stripe Poland offers, beside 1.5 % + 1 zł: "Custom — Design a custom package – available for businesses
  with large payments volume or unique business models. Contact sales · IC+ pricing · Volume discounts ·
  Multi-product discounts · Country-specific rates." [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-08
- **[DOCS]** With `fees_collector = stripe` (Raketa's club accounts), the connected account itself pays "Interchange
  Plus Payment Fees", and also Radar, 3D Secure and Card Account Updater fees, so IC+ would be the club's own deal
  with Stripe, not Raketa's. [Stripe: Fee behavior on connected accounts](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior) — read 2026-10-08
- **[DOCS]** IC+ still has a fixed part: Stripe's markup is a percentage "`volume_fee`" plus a "`per_auth_fee`", charged
  on every gateway request (authorisations, voids and card validations alike); networks may bill their costs "up to
  two months after" the payment. [Stripe support: Reviewing IC+ fees](https://support.stripe.com/questions/reviewing-ic-fees-stripe-fees-and-network-costs) — read 2026-10-08
- **[ABSENT]** A published volume threshold for IC+ or volume pricing in Poland, or any statement that a small
  connected account can get it: not on the pricing page, the fee-behaviour page or the IC+ support page. — read 2026-10-08

---

## R-PAY-4 — Poles with no card they would use online

### How many Poles use a card at all, and pay online
- **[DOCS]** Global Findex 2025 database (survey 2024, Poland, adults 15+): used their own debit card for a purchase in
  the past year 81.4 %; own a credit card 20.3 %; used a card or phone to pay 77.8 %; bought something online 49.9 %;
  paid online for an online purchase 46.8 %; cash on delivery 3.1 %. [World Bank: Global Findex Database 2025 (CSV)](https://thedocs.worldbank.org/en/doc/be6615202d1f08a25855c8ac2d615122-0050012025/related/GlobalFindexDatabase2025.csv), [glossary](https://thedocs.worldbank.org/en/doc/be6615202d1f08a25855c8ac2d615122-0050012025/related/GlobalFindex2025-glossary.xlsx) (indicators fin2.t.d, fin10, fin3, fin26b, fin27a, fin27b) — read 2026-10-08
- **[ABSENT]** The share of Polish online shoppers with no card they would use online: Findex asks about debit-card
  use and paying online, not about paying online by card; also not in NBP 2023, Autopay 2025, Tpay 2024/25 or
  Gemius 2025 (`local-market.md#how-poles-pay-online--cards-are-a-minority`). The nearest bound is that about 19 % of
  adults used no debit card at all in the past year (arithmetic on fin2.t.d). — read 2026-10-08

---

## R-PAY-6 — Apple Pay for one unscheduled later charge

### Apple's merchant tokens are not for an unscheduled card on file
- **[DOCS]** Apple: merchant tokens (MPANs) are for "subscriptions, recurring billing, automatic reload of balances,
  deferred payments, and installment loan repayments. For all other types of transactions — including one‑time
  payments — merchants will continue to use a DPAN." And: "Outside of these supported use cases, MPAN cannot be used
  for unscheduled card on file (UCOF)." A deferred payment is a "Deferred or fixed date charge, with one or more
  supplemental charges" (car hire, hotels). As of January 2026 Amex, Discover, JCB, Mastercard and Visa support
  MPANs; where an issuer does not, "a DPAN will be returned instead". [Apple Pay for partners: Merchant tokens (MPANs)](https://applepaypartners.apple.com/merchants/features/merchant-tokens-mpans) — read 2026-10-08
- **[DOCS]** Stripe lists deferred payments as "Authorize payment at booking, then charge after you provide the
  service, such as after a hotel stay"; on the web the Payment Element and Express Checkout Element take a
  `deferredPaymentRequest` with a `deferredPaymentDate`. Checkout requests merchant tokens by itself. [Stripe: Apple Pay merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens) — read 2026-10-08
- **[DOCS]** The phone library still cannot ask for a deferred token: stripe-react-native (latest release v0.81.0,
  6 Oct 2026; source on `master`) has `PaymentRequestType` = `Recurring`, `AutomaticReload`, `MultiMerchant` only;
  its `DeferredCartSummaryItem` is a line on the sheet, not a token request. [stripe-react-native: PlatformPay.ts](https://github.com/stripe/stripe-react-native/blob/master/src/types/PlatformPay.ts), [releases](https://github.com/stripe/stripe-react-native/releases) — read 2026-10-08
- *Reading:* a card saved once and charged whenever some future game fills is an unscheduled card on file. Apple
  says an MPAN cannot be used for that, so an iPhone would hand over a device token (DPAN), which can fail after a
  phone change (SIT-69). A deferred request fits one booking with a known date, and the React Native library can't
  make one today.

---

## R-PAY-11 — the player's internet address in a card dispute

### Card disputes in Poland run on the card schemes' rules
- **[DOCS]** "Obciążenie zwrotne jest standardem ustalanym przez organizacje płatnicze i nie posiada odrębnych
  regulacji prawnych" (Visa and Mastercard); a claim filed after the bank's or scheme's deadline is rejected.
  [Bankier.pl: Czym jest i jak działa chargeback](https://www.bankier.pl/smart/chargeback-w-polskich-bankach) (19 Sep 2025, press explainer) — read 2026-10-08

### Where an internet address counts in a dispute, and where it does not
- **[DOCS]** For reservations Stripe's advice is the policy, not the address: "Offline services include purchases
  that are made in advance, such as event tickets and reservations, where evidence of a cancellation policy can be
  material." Its evidence list for an offline service is a link between the person served and the cardholder,
  documentation that the service was provided and when, earlier undisputed payments on the same card, and, "For
  recurring payments, evidence of a legally binding contract". "Customer's IP address at the time of purchase"
  (`customer_purchase_ip`) is listed only for digital products. [Stripe: Dispute reason code categories](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[DOCS]** The address decides only Visa's *Compelling Evidence 3.0*, and only on fraud reason 10.4: at least two
  earlier paid, undisputed payments on the same payment method, 120–364 days before the disputed one, all matching
  two main elements (purchase IP, device fingerprint or ID) or one main and one secondary (shipping address, email,
  customer account ID). [Stripe: Visa Compelling Evidence 3.0 disputes](https://docs.stripe.com/disputes/api/visa-ce3) — read 2026-10-08
- **[DOCS]** Fraud is "the most common reason for a dispute" and "a difficult dispute type to win"; Stripe's prevention is
  a recognisable statement descriptor and a receipt for each payment. [same page](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[ABSENT]** Any Polish guidance (Rzecznik Finansowy, KNF, UOKiK, a bank's chargeback rules) on what an internet
  address proves in a card dispute — searched in Polish and English — read 2026-10-08
- *Reading:* a Raketa share is charged when the game fills, with nobody pressing anything, so there is no "address at
  purchase". The address recorded with the terms supports the agreement, and helps under CE 3.0 only if the same card
  paid the same club twice before, 120–364 days earlier, from a matching address or device.

---

## R-PAY-17 — the reasons Stripe gives for a declined card setup

### What a declined setup hands back
- **[DOCS]** A SetupIntent keeps its failure in `last_setup_error`; a card error carries `decline_code` ("the card
  issuer's reason for the decline if they provide one"), `network_decline_code` (the raw code) and
  `network_advice_code`. [Stripe API: Errors](https://docs.stripe.com/api/errors), [Stripe API: SetupIntent object](https://docs.stripe.com/api/setup_intents/object) — read 2026-10-08
- **[DOCS]** The codes and Stripe's next step: `insufficient_funds` (use another method); `card_velocity_exceeded`
  ("exceeded the balance, credit limit, or transaction amount limit available on their card", contact the bank);
  `withdrawal_count_limit_exceeded`; `card_not_supported` ("doesn't support this type of purchase"); `expired_card`;
  `restricted_card`; `authentication_required`; `transaction_not_allowed`, `do_not_honor`, `service_not_allowed` and
  `generic_decline` ("declined for an unknown reason"). `lost_card` and `stolen_card` must be shown to the customer as a
  generic decline. [Stripe: Decline codes](https://docs.stripe.com/declines/codes) — read 2026-10-08
- **[DOCS]** The raw codes that match a card's own limits: 61 "Exceeds approval amount limit", 65 "Exceeds withdrawal
  frequency limit", 57 "Transaction not permitted to cardholder", 62 "Restricted card", 05 "Do not honor"; Stripe warns
  that "The meaning of a code differs based on the card network". [Stripe: Network decline codes](https://docs.stripe.com/declines/network-codes), [Stripe: Card declines](https://docs.stripe.com/declines/card) — read 2026-10-08

### Banks and rivals name the reason
- **[POLICY]** mBank promises its own customer the reason: "przekażemy Ci informację dlaczego odrzuciliśmy płatność oraz
  jak możesz uniknąć podobnej sytuacji w przyszłości", in online banking, the app, by SMS or at the merchant.
  [mBank: Regulamin kart debetowych od 25.06.2025](https://pdf.mbank.pl/mbankpl/of/regulaminy/karty/regulamin_kart_debetowych_dla_osob_fizycznych_i_klientow_private_banking_w_ramach_bankowosci_detalicznej_mbanku_s.a._od_25.06.2025_r.pdf) — read 2026-10-08
- **[MEASURED]** Playtomic's app carries a message per reason: "Your card has insufficient funds.", "Your card has
  expired", "This card has expired. Update your card info or choose a different payment method.", "Your card was
  declined", "We are unable to authenticate your payment method. Please choose a different payment method and try
  again." Android 6.93.2, extract in [`../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt`](../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** Which code a Polish issuer returns for a card whose internet limit is 0 zł, or a card blocked for online
  use: no Polish bank, Stripe or acquirer page maps it — read 2026-10-08

---

## R-PAY-26 / R-PAY-27 — card updates and network changes in Poland

### Automatic card updates are not documented for Polish issuers
- **[DOCS]** "It's widely supported in the United States … International support varies from country to country. It
  isn't possible to identify cards that support automatic updates." Updates arrive as
  `payment_method.automatically_updated`. [Stripe: How cards work — Automatic card updates](https://docs.stripe.com/payments/cards/overview) — read 2026-10-08
- **[DOCS]** "Participation in Visa Account Updater is highest in the U.S., Canada, UK, Ireland, Italy and Greece";
  elsewhere issuers are told to ask their Visa representative. Poland is not named. [Visa Developer: Visa Account Updater](https://developer.visa.com/capabilities/vau/docs-getting-started-vau) — read 2026-10-08
- **[DOCS]** On Raketa's club accounts (`fees_collector = stripe`) any Card Account Updater fee is the club's.
  [Stripe: Fee behavior on connected accounts](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior) — read 2026-10-08
- **[ABSENT]** Whether PKO BP, Pekao, mBank, ING or Santander send updates to Visa Account Updater or Mastercard's
  Automatic Billing Updater — searched the networks' pages, Stripe's docs and the banks' card terms — read 2026-10-08

### Polish cards do move between networks
- **[POLICY]** PKO BP has been replacing most Mastercard debit cards with Visa ones at renewal; its press office
  confirmed the debit offer was unified; the old card stays valid until its printed expiry. [Superbiz](https://superbiz.se.pl/wiadomosci/rewolucja-w-banku-pko-bp-takiej-karty-juz-nie-dostaniesz-co-w-zamian-aa-pCFT-C5jq-H36d.html) (14 Jul 2023), [Telepolis](https://www.telepolis.pl/fintech/cashless/pko-bank-polski-karta-przesylka) (14 Mar 2024), press reports — read 2026-10-08; not re-verified on PKO's own site
- **[DOCS]** The same report cites NBP: Visa 52.9 %, Mastercard 46.9 % of Polish cards at the end of 2022. [Superbiz](https://superbiz.se.pl/wiadomosci/rewolucja-w-banku-pko-bp-takiej-karty-juz-nie-dostaniesz-co-w-zamian-aa-pCFT-C5jq-H36d.html) — read 2026-10-08
- **[DOCS]** Maestro has not been issued in the EU since 1 July 2023; existing Maestro cards "will still be functioning in
  the field until 2027 at the latest", so the last ones are being replaced now. [Adyen: Debit Mastercard is replacing Maestro](https://www.adyen.com/knowledge-hub/debit-mastercard-is-replacing-maestro-what-you-need-to-know) — read 2026-10-08
- **[ABSENT]** How many Polish cards change network in a year: no NBP, bank or network figure — read 2026-10-08

---

## R-PAY-34 — what the statement shows, and how long a released hold stays

### The statement shows the club's descriptor
- **[DOCS]** For direct charges "The customer's statement uses the connected account's static component"; "Only the
  first 22 characters of the full statement descriptor are sent for card payments". If Stripe-hosted onboarding finds
  no descriptor, Stripe builds one from `business_profile.name`, then `business_profile.url`, then the legal name; "For
  accounts where the platform handles onboarding, you must set their statement descriptor." The club's support phone,
  email and URL travel with it. [Stripe: Set statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors) — read 2026-10-08
- **[DOCS]** Rules: Latin characters only, 5–22 characters, at least one letter, none of `< > \ ' " *`; a per-payment
  suffix is joined as prefix + `* ` + suffix inside the 22. "Most banks display this information consistently, but some
  might display it incorrectly or not at all." [Stripe: Statement descriptors](https://docs.stripe.com/get-started/account/statement-descriptors) — read 2026-10-08
- *Reading (code):* the hold passes a `description` and metadata only, no `statement_descriptor_suffix`
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:469-534`; no `statement_descriptor` anywhere in
  `backend/app/modules/payments/`), so the player's bank shows the club's own descriptor, never "Raketa" or "Padel".

### How Polish banks rename the line
- **[DOCS]** PKO BP's IKO and iPKO show "nazwę sprzedawcy, a w przypadku wybranych sklepów nawet logo" on a card payment,
  with categories, websites and locations announced. [Spider's Web](https://spidersweb.pl/2024/10/bank-pko-aplikacja-historia-transkacji.html) (22 Oct 2024, press) — read 2026-10-08
- **[ABSENT]** What mBank, ING, Pekao or Santander show in place of the descriptor — read 2026-10-08

### How long a released hold stays in a Polish bank app
- **[POLICY]** mBank personal debit cards: the hold lowers the available balance "do czasu, gdy rozliczymy transakcję
  kartową, rozwiążemy blokadę autoryzacyjną … lub anuluje ją akceptant"; an unsettled hold is kept "nie dłużej niż 30
  dni", then dropped: "W historii swoich operacji nie będziesz tego widział." (14 days for transactions up to
  19 Feb 2025.) [mBank: Regulamin kart debetowych od 25.06.2025](https://pdf.mbank.pl/mbankpl/of/regulaminy/karty/regulamin_kart_debetowych_dla_osob_fizycznych_i_klientow_private_banking_w_ramach_bankowosci_detalicznej_mbanku_s.a._od_25.06.2025_r.pdf), [mBank: Regulamin kart debetowych dla firm od 3.12.2024](https://www.mbank.pl/pdf/firmy/karty/regulamin-kart-debetowych-dla-firm-od-3-12-2024.pdf) — read 2026-10-08
- **[POLICY]** ING prepaid cards: a hold lasts "maksymalnie przez 8 dni kalendarzowych od daty transakcji" (PKO's prepaid
  cards: 7 days). [ING: regulamin kart przedpłaconych](https://www.ing.pl/_fileserver/item/e5dykb1) — read 2026-10-08
- **[ABSENT]** How fast a Polish bank app drops a hold the merchant cancelled: the terms say the hold ends when the
  merchant cancels it, not how long that takes to show — read 2026-10-08

---

## R-PAY-39 — the bank's check on a charge made without the player

### How often issuers ask, and how fast people answer
- **[DOCS]** France, January 2021: 4.35 % of e-commerce payments were soft-declined (the bank asked for its check), and
  82.1 % of those were simply rejected, not retried; merchant-initiated payments were outside the rule. [Dalenys/Payplug: PSD2 key figures](https://www.payplug.com/wp-content/uploads/2021/04/PSD2-key-figures-on-the-end-of-migration-Dalenys.pdf) (vendor sheet, 2021) — read 2026-10-08
- **[DOCS]** For `authentication_required` on an off-session payment, "you might need to ask the customer to retry".
  [Stripe: Decline codes](https://docs.stripe.com/declines/codes) — read 2026-10-08
- **[ABSENT]** How often Polish issuers ask for their check on a merchant-initiated charge, and how long players take to
  answer one: no NBP, KNF, Stripe, Visa, Mastercard or acquirer figure — read 2026-10-08

---

## R-PAY-40 — a tax ruling for a court-hour paid in several charges

### The closest ruling: tennis courts booked online through an operator
- **[DOCS]** KIS, 30 Sep 2025: a centre selling tennis court bookings online, where the system forces payment "w całości
  zapłaty bezgotówkowo za pośrednictwem banku na konto operatora", and the operator settles monthly "wraz z zestawieniem
  (ewidencją) wszystkich transakcji (czynności) oraz danymi kupującego". Its position, that consumer sales are exempt
  from the cash register under poz. 42 of Dz.U. 2024 poz. 1902, "jest prawidłowe". The conditions restated: the whole
  price "za pośrednictwem poczty, banku lub spółdzielczej kasy" to the seller's account, and "z ewidencji i dowodów
  dokumentujących zapłatę jednoznacznie wynika, jakiej konkretnie czynności dotyczyła".
  [Eureka: 0111-KDIB3-2.4012.631.2025.1.SR](https://eureka.mf.gov.pl/informacje/podglad/659768) — read 2026-10-08
- **[ABSENT]** A ruling on one service paid in several parts by several people (a court-hour split into four charges, or
  Stripe Connect by name): searched Eureka for "podział płatności", "płatność dzielona", "kilku płatności", "od kilku
  osób", "każdy z graczy", "Stripe", "rezerwacji kortów", "rezerwacji obiektów sportowych" — read 2026-10-08
- *Reading:* the wording asks that the whole price reaches the seller's bank account through a bank or payment
  operator and that each payment is traceable to its sale. Four shares, each tied to the same booking, fit the
  wording, but no ruling says so.
