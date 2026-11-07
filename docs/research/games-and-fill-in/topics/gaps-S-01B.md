# Gaps round after the S-01B refresh

Answers to the ten facts the S-01B refresh found missing (`prd-530/stories/S-01B/rules-gaps.md`: R-EMAIL-7, R-PAY-39,
R-FILL-56, R-REQUEST-55, R-PAY-50, R-PAY-49, R-FILL-53, R-EMAIL-41, R-NOTIFY-36, R-NOTIFY-42, with the rules each one
also touches). None of them held a grade provisional; each sharpens a side or a grilling. Read **2026-10-10**; web search
worked throughout. Each `###` heading answers part of one gap and names what it found, so it can be cited as
`topics/gaps-S-01B.md#<heading>`.

Sources: Polish banks' own pages and card terms (PKO BP, ING Bank Śląski, Bank Millennium, Erste Bank Polska — formerly
Santander Bank Polska —, Pekao), ING's community forum through a search engine's extract; Stripe's docs and support
pages; Visa Business News AI13522; the EBA-ECB report on payment fraud (December 2025); Ravelin's 3-D Secure country
rankings (2025, 2026); Leanplum's push timing as reported by MarTech; Baymard's checkout survey; an Autopay figure quoted
by Shoper; Playmore's web app as served on 2026-10-10 (1,432 bundles reachable from playmore.pl, entry
`index-CFpbCOgi.js`; the phone apps are Capacitor shells that load the same site) and the source maps inside Playmore
Android 6.118.0 (unpacked by the NOTIFY round on 2026-10-08), every quote of the second checked against the first;
Playtomic Android 6.93.2's decompile and string table (the package the NOTIFY round read on 2026-10-08) and its player
help (Zendesk API); tenis4U's public booking grid for five Kraków padel clubs, read twice on 2026-10-10 evening.

Kinds: `[POLICY]` a rule, help text, term or shipped string an operator or bank publishes · `[LAW]` · `[DOCS]` a
provider's, network's, regulator's or vendor's document · `[MEASURED]` read from the product itself (shipped code or the
public data its web app shows a visitor; the extract is saved under `../shots/`) · `[COMPLAINT]` one person's account ·
`[ABSENT]` looked for and not found, with where. *Reading* lines are this researcher's inference, not a source.

Extracts: [`../shots/gaps-S-01B-playmore-unread-unpaid-2026-10-10.txt`](../shots/gaps-S-01B-playmore-unread-unpaid-2026-10-10.txt),
[`../shots/gaps-S-01B-playtomic-6.93.2-folded-notices.txt`](../shots/gaps-S-01B-playtomic-6.93.2-folded-notices.txt),
[`../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt`](../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt).

---

## 1. R-EMAIL-7 (also R-FILL-42, R-PAY-52, R-FILL-56): how long a Polish bank's app shows a hold that was let go, and whether a 30-minute hold shows at all

### PKO BP lists a card hold at once, with a padlock and the word Blokada
- **[POLICY]** "Informacje o transakcjach zrealizowanych i niektórych blokadach znajdziesz teraz na jednej liście." "Na
  liście operacji sprawdzisz blokady płatności kartą oraz płatności mobilnych, np. BLIK." "Jeśli Twoja płatność czeka na
  rozliczenie, zobaczysz przy niej ikonę kłódki i oznaczenie Blokada." In IKO from version 3.179, and in iPKO's
  *Ostatnie* tab. [PKO BP: zmiany w historii konta (23.03.2026)](https://www.pkobp.pl/aktualnosci/bankowosc-elektroniczna/zmiany-w-historii-konta-aplikacja-serwis) — read 2026-10-10
- **[ABSENT]** The page does not say when a hold leaves the list, or what a hold the shop cancelled looks like. Same page — read 2026-10-10

### PKO BP alerts a card payment by SMS, e-mail and app, and has no alert for a hold let go
- **[POLICY]** Under *Powiadomienia o kartach*: "Płatność kartą — SMS: tak (powyżej wskazanej kwoty), e-mail: tak,
  aplikacja mobilna: tak". The card rows are only that and a PIN change; no row covers a cancelled transaction, a
  released hold or a refund. (The account rows above them include *Blokada kwoty pod transakcję BLIK* and
  *Niezrealizowana transakcja*.) [PKO BP: powiadomienia SMS, e-mail, push](https://www.pkobp.pl/klient-indywidualny/aplikacja-iko-ipko/powiadomienia-bank-sms-email-push) — read 2026-10-10
- *Reading:* a PKO player who has card alerts on is told of a 30-minute hold when it is placed, and told nothing when it
  is let go.

### PKO BP's card rules drop a hold on settlement or after 7 days, and do not name a shop's cancellation
- **[POLICY]** "Blokady … podlegają anulowaniu w momencie otrzymania przez Bank rozliczenia transakcji lub po upływie 7 dni
  od dnia ich ustanowienia, jeżeli PKO Bank Polski SA nie otrzyma potwierdzenia rozliczenia transakcji." The same
  sentence stands in three of PKO's prepaid-card rule sheets. [PKO: zasady używania kart przedpłaconych personalizowanych](https://www.pkobp.pl/media_files/a56f1f19-9e86-4193-a4f0-9c7847e72bee.pdf),
  [another version](https://www.pkobp.pl/media_files/b701508c-04d1-46c3-a8fc-139975af8a4a.pdf),
  [kart debetowych typu przedpłaconego](https://www.pkobp.pl/media_files/5ec1e767-f3d5-454e-b7d8-ba363f215afe.pdf) — read 2026-10-10
- **[ABSENT]** The current terms for PKO's personal debit cards (the ones most players hold): the search found only
  2015–2016 versions and business-card terms. Searched pkobp.pl through the search engine and PKO's help pages — read 2026-10-10

### ING keeps a card hold at most 8 calendar days, and its staff say a shop's notice can lift it sooner
- **[POLICY]** "Blokada środków na rachunku związana z dokonaną transakcją kartową utrzymywana jest maksymalnie przez 8
  dni kalendarzowych od daty transakcji, w zależności od daty faktycznego obciążenia rachunku." ING's prepaid cards for
  business, in force from 14 November 2021. [ING: komunikat dla posiadaczy kart przedpłaconych](https://www.ing.pl/_fileserver/item/e5dykb1) — read 2026-10-10
- **[POLICY]** ING staff on ING's own community forum: "Blokady na płatności kartą w przypadku nie rozliczenia ich przez
  usługodawcę zdejmujemy po 11 dniach kalendarzowych. Może to się zdarzyć szybciej, jeżeli dostaniemy od niego
  informację np. o odrzuceniu transakcji." In another reply: "Gdy nie dostaniemy potwierdzenia po 8 dniach roboczych
  licząc od dnia następnego po nałożeniu blokady, to ściągamy blokadę automatycznie." Read through the search engine's
  extract of spolecznosc.ing.pl; the threads answer a direct read with a Cloudflare check, so which thread holds which
  sentence, and their dates, were not confirmed. [BLOKADA NA RACHUNKU](https://spolecznosc.ing.pl/-/P%C5%82atno%C5%9Bci/BLOKADA-NA-RACHUNKU/td-p/2493),
  [Blokada przy płatności kartą](https://spolecznosc.ing.pl/-/P%C5%82atno%C5%9Bci/Blokada-przy-p%C5%82atno%C5%9Bci-kart%C4%85/td-p/12266) — read 2026-10-10

### Millennium shows the hold at once and keeps it at most 30 days
- **[POLICY]** "Jeżeli zapłacisz w tym trybie [online], to od razu zobaczysz na swoim rachunku blokadę na kwotę
  autoryzowanej transakcji. Pieniądze możemy zablokować na maksymalnie 30 dni. Jeżeli do tego czasu nie otrzymamy
  rozliczenia tej transakcji, zwolnimy blokadę." Nothing about a shop's cancellation. [Bank Millennium: Regulamin ogólny świadczenia usług bankowych dla osób fizycznych, last updated 1.04.2025, p. 41](https://www.bankmillennium.pl/delegate/managedfiles/27/latest) — read 2026-10-10

### Erste, formerly Santander Bank Polska, may keep a hold 30 days whether or not the payment went through
- **[POLICY]** "Na jak długo blokowane są środki gdy dokonam transakcji kartą?" — "Każda autoryzacja transakcji kartą
  powoduje blokadę środków na kwotę udzielonej autoryzacji." "Blokada (bez względu na to czy transakcja doszła do
  skutku) może być utrzymana maksymalnie przez 30 dni". (santander.pl's FAQ now redirects here.) [Erste Bank Polska: pytania i odpowiedzi — karty](https://www.erste.pl/klient-indywidualny/kontakt/pytania-i-odpowiedzi-karty?sr=1) — read 2026-10-10
- **[POLICY]** "Transakcja przetwarzana online może zmniejszyć dostępne środki o autoryzowaną kwotę: a. dla transakcji
  gotówkowych w bankomacie – do 10 dni kalendarzowych; b. dla pozostałych transakcji – do 30 dni kalendarzowych."
  [Regulamin debetowych kart płatniczych dla klientów indywidualnych, in force from 25 April 2026, p. 12–13](https://www.santander.pl/regulation_file_server/time20230720100030/download?id=150050&lang=pl_PL) — read 2026-10-10

### Pekao publishes no hold length that was found
- **[ABSENT]** Pekao's personal-account terms (in force from 1.09.2021) carry no card-hold length; its card terms were not
  found. Searched pekao.com.pl through the search engine ("blokada", "dni", "rozliczenie"), and the terms' text. [Pekao: Regulamin rachunków bankowych dla osób fizycznych](https://www.pekao.com.pl/dam/jcr:99a17c03-a7bb-47b3-8c76-e168b94956ac/Regulamin%20rachunk%C3%B3w%20bankowych%20Banku%20Pekao%20S.A.%20dla%20os%C3%B3b%20fizycznych.pdf) — read 2026-10-10
- Carried: mBank lifts a hold when the shop's cancellation arrives, else after 14 days online
  (`gaps-EMAIL.md#mbank-drops-a-hold-when-the-shops-cancellation-arrives-else-after-14-days-online`, read 2026-10-08).

### A cancelled hold drops off the statement; how soon each bank's app shows that is still unpublished
- **[DOCS]** Stripe, for a refund made soon after the charge: "In the case of a reversal, the original charge drops off
  the customer's statement, and a separate credit isn't issued." [Stripe: refund and cancel payments](https://docs.stripe.com/refunds) — read 2026-10-10
- **[DOCS]** Stripe, writing as a card issuer: "Authorizations that have been reversed by the merchant will have the
  status set to reversed"; otherwise the hold lapses after "usually up to 7 days for most merchant categories". No delay
  is stated for a reversal. [Stripe support: Issuing — common questions about reversals](https://support.stripe.com/questions/issuing-common-questions-about-reversals) — read 2026-10-10
- **[ABSENT]** How many minutes or hours after a shop's cancellation the hold leaves the app, at PKO BP, ING, Pekao,
  Erste or Millennium. None of their terms, FAQs or help pages read above names it; only mBank says the cancellation
  lifts the hold (no delay given). What would answer it: on a real card from each bank, a small live-mode hold placed
  and cancelled at once, with the bank app watched and the times written down — read 2026-10-10
- *Reading:* a 30-minute hold does show: PKO and Millennium list a hold the moment the card is authorised, and PKO's
  card alert fires on it. Whether it leaves within minutes depends on the bank acting on the cancellation: mBank says it
  does, ING's staff say it may, Erste's FAQ warns a hold may stay 30 days whether or not the payment happened.

---

## 2. R-PAY-39 (also R-PAY-49, R-EMAIL-5): how often Polish banks ask for their check on a charge made without the player, and how long a player takes to answer

### EEA 2024: charges made without the payer were 22 per cent of remote card payments taken without the bank's check
- **[DOCS]** "In 2024, around 29% of remote card payments without SCA were exempted under TRA. The next most prevalent
  reason for not applying SCA to remote card transactions relates to merchant-initiated transactions (MIT) … which
  amounted to 22% in 2024." The report counts payments and fraud; it does not count how often a bank refused such a
  charge and asked for its check. [EBA-ECB: 2025 report on payment fraud, p. 29–31](https://www.ecb.europa.eu/press/intro/publications/pdf/ecb.ebaecb202512.en.pdf) — read 2026-10-10

### When a Polish card's bank does ask, about 87 per cent of checks succeed
- **[DOCS]** Ravelin's 2026 country table: Poland's "Average 3DS success rate" is 87 % (tied 10th). Ravelin's own wording
  of the rate is ambiguous ("successful 3DS challenges as a proportion of all 3DS secure challenges"); the data are its
  merchants' checkouts, where the payer is present, and the period is not stated. [Ravelin: 3D Secure rates 2026 (19 March 2026)](https://www.ravelin.com/blog/3d-secure-rates-2026) — read 2026-10-10
- **[DOCS]** The 2025 edition ranks Poland 16th of 37 for 3-D Secure success, 28th for frictionless rate and 11th for
  challenge success, with no figures in the text. [Ravelin: global 3D Secure rates (10 April 2025)](https://www.ravelin.com/blog/global-3d-secure-rates-country-data-comparison) — read 2026-10-10

### People open a push in about 7 minutes on an iPhone and 48 on Android (2016 vendor figure)
- **[DOCS]** "the median (middle) time to open for Android users is 48 minutes … For iOS users, the median time is seven
  minutes." Leanplum's data on marketing pushes, reported 27 May 2016. [MarTech: Android users open 2x more notifications](https://martech.org/android-users-open-2x-notifications-ios-users-much-faster-open-report/) — read 2026-10-10
- *Reading:* the nearest public figure for how long a player away from the app takes to come back; a bank's check
  needs her to open the app and then pass the check, so the real time is longer.

### How often Polish banks ask on a charge made without the player: still not found
- **[ABSENT]** No Polish or EEA rate of `authentication_required` (or any soft decline) on merchant-initiated charges.
  Searched this round: the EBA-ECB 2025 report (above), NBP's quarterly notes on fraudulent transactions (found by
  search; they split by channel, not by SCA or initiator), Ravelin (above), Checkout.com's and Mastercard's SCA guides.
  Carried: France 2021, 4.35 % of e-commerce payments soft-declined with the payer present
  (`gaps-PAY.md#how-often-issuers-ask-and-how-fast-people-answer`). What would answer it: the decline codes on Raketa's
  own Stripe account once live, or an acquirer's published split — read 2026-10-10

---

## 3. R-FILL-56 (also R-FILL-54, R-FILL-42): how long a hold lasts when the player completes the payment in the app with her bank's check

### Stripe holds a payment the customer takes part in for 7 days on every card brand
- **[DOCS]** Card-not-present windows, merchant-initiated against customer-initiated: Visa "5 days\*" against "7 days"
  (\* "4 days and 18 hours"), Mastercard, Amex and Discover 7 against 7. "Stripe and the card network classify
  transactions as MIT or CIT based on signals of cardholder participation, not solely on API parameters like
  off_session. For example, a payment with `off_session: true` might still be classified as a CIT if a CVC is present".
  [Stripe: place a hold on a payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-10
- **[DOCS]** "the `payment_method_details.card.capture_before` attribute on the charge is the most reliable and accurate
  way to determine your charge's authorization window." [Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-10

### Visa's own rule since 13 April 2024: 10 days for a payment the cardholder makes online, 5 for one the merchant makes
- **[DOCS]** "New Authorization-to-Clearing Time Frames: CNP (cardholder-initiated) transactions — 10 calendar days … All
  merchant-initiated transactions — Five calendar days", "Time frames begin on the date of a valid authorization."
  Effective 13 April 2024; the notice is addressed to U.S. acquirers. [Visa Business News AI13522 (19 October 2023)](https://corporate.review.visa.com/content/dam/VCOM/regional/na/us/support-legal/documents/authorization-framework-will-be-updated-to-simplify-authorization-processing-time-frames.pdf) — read 2026-10-10
- **[ABSENT]** Visa's notice for Europe was not found; a secondary page says some regions keep earlier limits. Searched
  visa.com and the web — read 2026-10-10
- *Reading:* a payment the player finishes in the app with her bank's check carries her participation, so Stripe should
  class it customer-initiated and hold it 7 days on Visa, inside Visa's 10. Carried:
  `gaps-FILL.md#the-hold-window-follows-how-the-card-network-classifies-the-attempt-that-succeeded`.

### The real capture_before of such a payment: still not read
- **[ABSENT]** No page gives the window Stripe stamps on a payment first refused off-session, then confirmed by the
  customer with 3-D Secure. What would answer it: on a Stripe test account, an off-session manual-capture payment with a
  card that demands authentication, confirmed with the test 3-D Secure page, then `capture_before` read on its charge
  (test mode shows what Stripe stamps, not what a Polish issuer does) — read 2026-10-10

---

## 4. R-REQUEST-55 (also R-REQUEST-14, R-REQUEST-52): whether a Kraków desk blocks the hour in its own system when it accepts a Raketa request

### tenis4U desks already type bookings made elsewhere into their grid as named blocks
- **[MEASURED]** tenis4U's grid carries, per court and day, the hours a desk has blocked under a name. In the 14 days
  ahead: PADEL LOUNGE blocks "Ania - lekcja z Marcinem" (Mon 19 Oct 20:00–21:00), "Holiwear poniedzialki 19-20" and
  "Kids 18-19 poniedziałki" (a standing group and children's class, Mondays); Fame Sport Club blocks "PADEL LIGA /
  ROTATION", "BLOKADA EVENT", "RTL FINALS"; Padel House and Garden Padel close hours as "nieczynne" and "zamkniete".
  Extract [`../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt`](../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt),
  from [tenis4U's public occupancy endpoint](https://app.tenis4u.pl/) — read 2026-10-10 17:21
- *Reading:* the tool a desk would use to keep a Raketa hour from being sold twice exists, and desks use it for lessons
  and standing groups. With no import or API at tenis4U, kluby.org or Playmore, a Raketa booking reaches that grid only
  by someone typing it (carried: `gaps-FILL.md#tenis4us-club-calendar-has-no-published-import-or-api`).

### Whether a desk will do it for a Raketa booking: not found
- **[ABSENT]** No club's terms or page says how it records bookings from another platform. Only a real desk answers
  this. What would answer it: asking the five clubs, or, after the first accepted request, reading the tenis4U grid for
  that hour — read 2026-10-10

---

## 5. R-PAY-50: what share of refused shares are for the terms or a missing card, against declines and bank checks

### Shoppers who quit at checkout: one in ten because the card was declined
- **[DOCS]** Reasons given for abandoning a checkout (US, "just browsing" excluded): "Extra costs too high" 40 %, "Delivery
  was too slow" 20 %, "I didn't trust the site with my credit card information" 19 %, "The site wanted me to create an
  account" 18 %, "Too long / complicated checkout process" 17 %, "The credit card was declined" 10 %, "There weren't
  enough payment methods" 9 %. [Baymard: cart abandonment rate (updated 22 September 2025)](https://baymard.com/lists/cart-abandonment-rate) — read 2026-10-10

### In Poland, a missing preferred payment method loses most buyers
- **[DOCS]** "aż 61% klientów rezygnuje z zakupu, gdy nie znajduje preferowanej metody płatności", attributed to an
  Autopay study; sample and date not given. [Shoper: bez gotówki ze smartfonem (updated 3 September 2026)](https://www.shoper.pl/2017/04/27/bez-gotowki-ze-smartfonem-nowy-raport-o-platnosciach-online/) — read 2026-10-10
- Carried: soft declines are "80% to 90% of all declines" (Checkout.com, all transaction types;
  `gaps-FILL.md#no-figure-for-how-often-polish-or-eea-issuers-soft-decline-a-charge-without-the-player`).

### The split for one share of a group's court: not found
- **[ABSENT]** No platform found publishes why its players' shares fail (terms not accepted, no card saved, a decline,
  the bank's check). Playmore names a decline's reason to the player (carried:
  `platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`) but no one gives shares. Searched this round:
  Baymard, the Gemius and Autopay coverage (search and Shoper), soft-decline studies. What would answer it: Raketa's own
  refusals, counted by reason, once live — read 2026-10-10

---

## 6. R-PAY-49: how Playmore treats an unpaid booking whose start is nearer than its 30 minutes

### Playmore counts the 30 minutes from the booking's creation, never against its start
- **[MEASURED]** The countdown on the booking's card is `created_at + 30 min − now`, stopped only by payment or
  cancellation; nothing in it reads the start time (`PAYMENT_COUNTDOWN_MS = 30 * 60 * 1000`). The Reservise booking flow
  polls the gateway for the same 30 minutes: "Reservise auto-cancels an unpaid dotpay reservation after 30 minutes."
  Served [BW9d7bZN.js](https://playmore.pl/assets/BW9d7bZN.js) and [D5nZmz0m.js](https://playmore.pl/assets/D5nZmz0m.js);
  6.118.0 sources `usePaymentCountdown.js`, `useReservisePaymentStatus.js`; extract
  [`../shots/gaps-S-01B-playmore-unread-unpaid-2026-10-10.txt`](../shots/gaps-S-01B-playmore-unread-unpaid-2026-10-10.txt) §B — read 2026-10-10
- *Reading:* a booking made ten minutes before its start shows a countdown that runs twenty minutes past the start.

### At the deadline Playmore checks whether the hour is still held, and a late payment can still keep it
- **[MEASURED]** When the time runs out: "Czas na opłacenie minął — Sprawdzamy, czy termin jest jeszcze zajęty — może to
  zająć kilka minut. Jeśli obiekt go nie zwolnił, płatność wciąż utrzyma rezerwację." For a desk-made booking that the
  player pays online, a comment says "endpointy płatności nie mają bramki na deadline, więc zapłata przed przejściem
  sweepu wciąż ratuje rezerwację", and "The sweep only runs every 5 minutes". Same extract §B — read 2026-10-10
- Carried: the 30-minute rule's own words (`platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`).

### What Playmore's server does when the start comes before the 30 minutes end: not found
- **[ABSENT]** The cut is made on Playmore's server, which the client does not show; its help, terms and FAQ say nothing
  of a booking close to its start. What would answer it: a booking made 20 minutes before its start at a Playmore club,
  left unpaid, and watched — read 2026-10-10

---

## 7. R-FILL-53: how fast a free weekday-evening padel court sells in Kraków once only one is left

### The third read, meant to time the last courts, could not be taken
- **[MEASURED]** At 17:11 and 17:21 CEST on Saturday 10 October, and in spot checks to 17:31, tenis4U's public grid
  served no free hour for any court of the five Kraków padel clubs on any day, nor for three other tenis4U venues; the
  same call served free hours at 05:02 that day, and the web app still builds its grid from that field. So every hour
  read as taken, and the reads were stopped. Extract
  [`../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt`](../shots/gaps-S-01B-tenis4u-krakow-padel-2026-10-10-evening.txt) — read 2026-10-10
- Carried: at Padel House, Monday 12 October 17:00–20:00 was handed back between 9 October 08:20 and 10 October 05:02
  and was then the only free court at those hours, still unsold at 05:02; Tuesday to Friday 17:00–22:00 were fully
  taken at both reads, so no last court existed to watch
  (`gaps-S-02.md#hours-handed-back-at-the-busiest-club-were-still-unsold-the-next-morning`); over 21 hours about one free
  weekend hour in ten sold (`gaps-S-02.md#over-the-last-day-about-one-free-weekend-hour-in-ten-was-sold`).

### How fast a last court sells: not found
- **[ABSENT]** No club, platform or report publishes how long a last free court lasts. What would answer it: the grid
  read every 10 to 15 minutes through a weekday afternoon and evening once tenis4U serves free hours again, with each
  last court's minutes to sale written down; or a club's own sales log — read 2026-10-10

---

## 8. R-EMAIL-41: whether Playmore tells a lapsed booking's payer by email or push

### Playmore has its own notice for a booking cancelled for want of payment
- **[MEASURED]** The notice list knows the backend template `reservation_cancellation_due_to_payment_failed`, filed
  under payments with the headline "Rezerwacja anulowana — brak płatności" ("Booking cancelled — not paid"); tapping
  it opens the bookings list, "says the booking is already gone". Its siblings: `reservation_payment_window` ("Opłać
  rezerwację"), `payment_reminder`, `reservation_payment_last_call` ("Ostatnie wezwanie do zapłaty"). Served
  [85oPQRfV.js](https://playmore.pl/assets/85oPQRfV.js), [AEIQ8K1Z.js](https://playmore.pl/assets/AEIQ8K1Z.js); 6.118.0
  `notificationEventMap.js`, `notificationTarget.js`; extract §C — read 2026-10-10

### Booking notices go by push to app users and by SMS to the rest, with a copy in the bell
- **[MEASURED]** Account settings: "SMS-y o rezerwacjach — Potwierdzenia, przypomnienia i odwołania wysyłamy SMS-em.
  Jeśli masz aplikację, te same informacje dostajesz jako powiadomienie — wtedy SMS-a już nie wysyłamy." The bell lists
  each "mirrored Xano message" sent by "Push - send with template". Served [CIr6Arwx.js](https://playmore.pl/assets/CIr6Arwx.js);
  extract §C — read 2026-10-10

### Playmore emails booking confirmations; whether it emails this lapse is not in the client
- **[MEASURED]** A banner warns "Nie możemy dostarczyć wiadomości na Twój adres e-mail — możesz przegapić potwierdzenia
  rezerwacji." Same bundle — read 2026-10-10
- **[POLICY]** The club pays Playmore "opłaty za wysyłkę powiadomień push, e-mail, SMS do Użytkownika związanych z
  Rezerwacjami". Partner terms in [Cw-tKkmq.js](https://playmore.pl/assets/Cw-tKkmq.js) — read 2026-10-10
- **[ABSENT]** Which channels carry `reservation_cancellation_due_to_payment_failed` besides push or SMS: the template
  lives on Playmore's server. What would answer it: one unpaid Playmore booking left to lapse, with the inbox watched —
  read 2026-10-10
- **[POLICY]** For comparison, Playtomic: "Playtomic emails you in the following scenarios: … Cancellation of a booking,
  match or activity … E-mail notifications cannot be disabled." [Playtomic: how to manage the notifications (updated 2026-09-29)](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337) — read 2026-10-10

---

## 9. R-NOTIFY-36: whether Playmore's unread count clears on a player's second phone once read on the first

### Playmore keeps what is read on its server, and opening the list marks everything read there
- **[MEASURED]** The count comes from `GET …/unread-count`; marking read is `POST …/mark-read` with ids or `{all: true}`.
  Opening the notice list remembers which rows were unread (to show them bold), then marks all read on the server
  ("Marks the whole inbox read — fired when the centre opens"). Served [BQRNRCzY.js](https://playmore.pl/assets/BQRNRCzY.js),
  [D-kdY-r0.js](https://playmore.pl/assets/D-kdY-r0.js), [DvFO-X_-.js](https://playmore.pl/assets/DvFO-X_-.js); 6.118.0
  `useUnreadNotifications.js`; extract §A — read 2026-10-10

### A second phone's bell catches up when its app comes to the front; its icon number waits
- **[MEASURED]** The bell asks the server when it appears, and again whenever the app returns to the foreground, at most
  once per 30 seconds ("Re-runs `refetch` when the tab/app regains focus or becomes visible again, throttled to once per
  `ttlMs`"; native apps listen to `appStateChange`). The app-icon number is written by the app while it runs and, while
  it is closed, by the count the server puts in each push ("the PUSH payload carries the count while the app is dead").
  Served [DvfNGzcV.js](https://playmore.pl/assets/DvfNGzcV.js), [DSQ7hmTs.js](https://playmore.pl/assets/DSQ7hmTs.js);
  6.118.0 `useRefetchOnFocus.js`, `appIconBadge.js`; extract §A — read 2026-10-10
- *Reading:* read on phone A, the count clears on phone B the next time Playmore is opened there; B's icon keeps the old
  number until then or until the next push.
- Corrects `gaps-S-02.md#playmore-reads-a-tab-badge-and-the-bell-with-their-full-number-and-what-it-counts`: the bell
  does not re-read its count every 30 s; it re-reads on appearing and on each return to the foreground, no oftener than
  once per 30 s.

### Whether Playmore's server pushes a silent update to clear the other phone's icon: not found
- **[ABSENT]** Not in the client; the server (Xano) sets each push's badge count. What would answer it: two phones on one
  account, a notice read on one, the other's icon watched with the app closed — read 2026-10-10

---

## 10. R-NOTIFY-42: whether a row Playtomic folds into another ("and 2 more") counts as new again

### Playtomic's folded row is one notice from its server, with one status
- **[MEASURED]** A social notice is one record with one id, one status (UNSEEN, SEEN or READ) and a list of people; the
  app writes "<b>%1$s and %2$s more</b> liked your post" from the first name and the list's length. The fold is made by
  the server, not by the app. Playtomic Android 6.93.2, `SocialNotificationsPresenter`, `SocialNotificationStatus`;
  extract [`../shots/gaps-S-01B-playtomic-6.93.2-folded-notices.txt`](../shots/gaps-S-01B-playtomic-6.93.2-folded-notices.txt) — read 2026-10-10

### The app marks rows seen by id when the list closes, and never marks one new again itself
- **[MEASURED]** On leaving the list, every row still UNSEEN is sent to `POST /v2/notifications/mark` with status SEEN;
  the same call can send READ (where the app sends that was not traced). The read and seen flags shown come only from
  each row's status as the server returns it, plus the rows read in this visit. Same extract — read 2026-10-10
- **[POLICY]** "Likes notifications: These are push notifications sent when your posts receive new likes". Nothing on
  folding or re-marking. [Playtomic: how to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337) — read 2026-10-10

### Whether Playtomic's server turns a seen folded row back to unseen when another person joins it: not found
- **[ABSENT]** Decided on Playtomic's server. Its player help, searched for "notifications" (13 articles, read for
  like, unread, unseen, badge, bell, inbox), says nothing of it. What would answer it: a post liked twice, the list
  opened, a third like added, and the bell's dot watched — read 2026-10-10
- Carried: the fold's strings (`gaps-NOTIFY.md#lists-fold-social-notices-no-pushed-digest-was-found`).
