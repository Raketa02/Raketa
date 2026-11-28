# Why a Kraków club would switch — and what Rakieta could charge

Research for the root grilling of the club-software map ("Rakieta becomes the club's booking
software", decided 2026-10-12 on [#609](https://github.com/Rakieta02/Rakieta/issues/609)): what a
Kraków club pays and gets today, why clubs change systems, what an empty hour is worth, and the
mechanics and law of each way Rakieta could charge.

**Extends** [`integration.md`](integration.md),
[`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md)
(§8, §9, §12) and [`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md).
Facts carried from there say *carried* and keep their read date; everything else was read
**2026-10-12**. Build cost is out of scope (another file).

**This file decides nothing.**

**Sources.** Playtomic and MATCHi help pages were read through their public Zendesk API (the HTML
answers 403). Playmore's player terms and interface text come from the JavaScript its web app serves
to every visitor; tenis4U's and Twój Tenis's from one read of their public web-app bundle each (no
crawling — tenis4U's §7 forbids systematic downloading). App Store reviews come from Apple's public
review feed and store pages (quotes from store pages are excerpts); a store date shown without a year
is this year's (2026). Google Play
ratings come from the store page's own structured data. Reservise's old price list was read from the
Wayback Machine because reservise.com now redirects to Playmore. EU acts were read from EUR-Lex
(Cellar), Polish acts from the Sejm's ELI API (the same text as isap.sejm.gov.pl). Nobody signed in,
booked or paid, and no endpoint that writes was called. Prices are as published: zł where a rival
publishes zł, otherwise its own currency, not converted.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published
price · `[DOCS]` a provider's developer document · `[LAW]` a statute, regulation or regulator's
decision · `[COMPLAINT]` a user's own words · `[ABSENT]` looked for and not found, with where. Lines
marked *reading* are inferences, not sources.

## Read this first

- **Kraków's incumbent is cheap and publishes no cut.** tenis4U, which runs most Kraków padel and much of
  its tennis, costs **49 / 89 / 149 zł net a month** by courts, and each club takes online payments on
  its own Przelewy24/Tpay contract; no tenis4U commission is published. Playmore costs **299 / 399 /
  499+ zł plus 1,79 %** of online payments (its own example: 1 373 zł a month on 60 000 zł online), and
  adds a service fee to the player. kluby.org: **50–599 zł plus 2 %**. (§1)
- **No published Polish plan locks a club in.** Playmore and kluby.org are monthly with a monthly notice
  (tenis4U and Twój Tenis publish no terms); trials are 14 days without a card (Playmore) or 60 days
  (kluby.org); setup and data migration are free
  (Playmore 0 zł, "1–2 tygodnie"). The cost of switching is the players, not the contract: Playmore's
  forced Reservise migration in March 2025 drew a wave of one-star reviews. (§1, §3)
- **Players already pay fees, and say so.** Playtomic in Poland takes **20 % of an open-match seat,
  1,24–3,99 zł**, nothing on private bookings, and 4,32 zł to cancel one; Playmore adds **1,48 zł** to
  each online booking at Kraków's Atras and Squash4You while its Kraków FAQ says "Nie pobieramy prowizji
  od użytkowników" (we take no commission from users); tenis4U keeps **2 %** of a refund. A 2026
  Playmore review names "przerzucanie opłat transakcyjnych na klienta zamiast na klub" (shifting
  transaction fees onto the player instead of the club). (§2)
- **Why clubs switch, in the vendors' own case studies:** unpaid bookings and no-shows (Vera Sport
  "~200+ → 0" unpaid a month), the desk's chasing work (Okęcie "~20h/tyg. → 0h", one post fewer),
  weekend staff (KS Zakręt runs unmanned), and, abroad, data and control (UK operators leaving
  Playtomic). Playmore itself tells clubs: if your system "nie zostawia mierzalnego problemu, nie
  zmieniaj go dla samej zmiany" (leaves no measurable problem, don't change it for its own sake). (§3)
- **The empty-hours pitch has no published numbers behind it.** Playmore's "Wieczory wyprzedane, ale
  rano i wczesnym popołudniem korty stoją puste" (evenings sold out, courts empty in the morning and
  early afternoon) stands alone; its analytics page shows sample figures (mornings 42 %, prime time 89 %). No Polish occupancy data, and no off-peak figure in Playtomic's
  Global Padel Report 2024 or 2025, was found. (§4)
- **Kraków prices say what an empty hour is worth.** A weekday-daytime padel hour mostly sells for
  **80–140 zł** (75–91 % of the evening price; Garden Padel's 8–9 slot is 50 zł); a squash hour for
  **40–65 zł online**, a third to a half of the evening's 103,50–120 zł. (§4)
- **Each way of charging has a clean Stripe mechanism.** A per-booking fee is `application_fee_amount`
  on the club's direct charge, with no Stripe fee on the fee itself but refunded only if Rakieta says
  so; a subscription is Stripe Billing at 0,7 % of billing volume, invoiced with 23 % VAT and, for a
  Polish business, through KSeF. (§5)
- **A player fee must be inside the price the player first sees.** The consumer act requires the total
  price before the order and voids fees not disclosed (art. 12 ust. 1 pkt 5, art. 23); UOKiK made
  eBilet put its service fee into every "od" price in 2023. Any shown discount on an empty hour must
  also show the lowest price of the last 30 days, services included. (§5)
- **Selling clubs' courts to players makes Rakieta a regulated intermediary.** The P2B Regulation
  (terms, 15-day notice of changes, ranking parameters, data access, 30-day reasons before cutting a
  club off) applies; complaint handling and mediation do not, while Rakieta is a small enterprise.
  Under Poland's DAC7 text the activity is "udostępnienie nieruchomości, ich części" (making real
  property or a part of it available) — court hire very likely in scope — with an annual report to KAS
  by the end of January. (§5)
- **The threats are moving now.** tenis4U shipped invites and split payment (April 2026), ranking
  matches (June 2026) and has an ELO ranking built but switched off; Playmore's open games went live
  27 June 2026, free in every plan; Twój Tenis is moving Kraków's tennis clubs to a new platform this
  year. Nothing public says Playtomic is coming to Kraków. (§6)

## 1. What each rival charges the club

### tenis4U (Kraków; most Kraków padel, much of its tennis)
- **[PRICE]** Four cards, all "netto miesięcznie": **FULL 49 zł** (1 kort), **FULL 89 zł** (2–3 korty),
  **FULL 149 zł** ("powyżej 3 kortów"), **BASIC 10 zł** ("BAZA + ROZGRYWKI"). The three FULL cards list
  the same features: "Rezerwacje online, Stałe rezerwacje, Trenerzy klubowi, System turniejowy, ligowy i
  challenge, Powiadomienia turniejowe, Dodanie klubu na mapie, Wizytówka klubu" (online bookings, fixed
  bookings, club coaches, tournaments/leagues/challenge, tournament notices, a map pin, a club card). BASIC strikes out the
  first three — no online bookings, no fixed bookings, no coaches
  ([tenis4u.pl, cennik](https://tenis4u.pl/#cennik)).
  - *Reading:* the FULL price changes only with the number of courts; there is no feature tier.
- **[PRICE]** Automation is extra: a court controller "2 500 zł net" (carried from `integration.md`,
  [automatyzacja](https://tenis4u.pl/automatyzacja/), read 2026-10-12).
- **[POLICY]** Online payments run on the club's own merchant account: the panel stores "each club's
  own Przelewy24 merchant keys (Client ID, CRC Key)" (carried, `integration.md`, read 2026-10-12);
  "Operatorem płatności online jest firma Tpay oraz P24" ([tenis4u.pl](https://tenis4u.pl/)).
  - *Reading:* the club pays Przelewy24/Tpay at its own rate — Przelewy24 lists 1,29 % + 30 gr (carried,
    `local-market.md`, read 2026-10-07).
- **[POLICY]** Partnership: "20% zniżki przy płatności Kartą tenisową Visa" with BNP Paribas
  ([tenis4u.pl](https://tenis4u.pl/)).
- **[ABSENT]** Contract length, notice period, trial, setup fee, migration offer or any commission on
  online payments: not on the home page, the sign-up form ("Wybierz wariant FULL / BASIC",
  [dodaj](https://tenis4u.pl/dodaj/)) or the player regulamin ([regulamin](https://tenis4u.pl/regulamin/)).

### Playmore (Reservise sp. z o.o., Warsaw; Kraków squash)
- **[PRICE]** "Abonament od 299 zł i 1,79% od płatności online." The subscription "Zależy od liczby
  kortów: 1–4 korty to 299 zł, 5–8 kortów 399 zł, a 9 i więcej od 499 zł. Kwoty netto miesięcznie."
  The 1,79 % is "Liczona od płatności, które gracze robią w aplikacji i na stronie. Rezerwacja opłacona
  na recepcji gotówką, kartą albo przelewem jest bez prowizji" (on payments players make in the app and on
  the web; a booking paid at the desk carries none). Worked example: 60 000 zł online →
  1 074 zł commission + 299 zł = "1373 zł czyli ok. 2,3% płatności online"
  ([cennik](https://join.playmore.pl/cennik/)).
- **[POLICY]** Included: onboarding with a "Opiekun" and staff training, "Przeniesienie danych z obecnego
  systemu", "Wsparcie 24/7 przez czat i telefon", the player app, "Gry otwarte w każdym pakiecie", the
  coach app and the school module. Extra: "Liga Challenger: pierwszy miesiąc za darmo, potem 249 zł
  netto miesięcznie"; door and light automation "po audycie technicznym"; SMS and other "Koszty
  zmienne … wpisujemy do oferty" ([cennik](https://join.playmore.pl/cennik/)).
- **[POLICY]** Contract: "14 dni okresu próbnego bez karty. Bez opłaty wdrożeniowej, wszystkie plany są
  miesięczne"; "bez umowy długoterminowej. Wypowiedzenie jest miesięczne. Możesz zapłacić za rok z góry
  z 20% rabatem, ale nigdy tego nie wymagamy"; "Wdrożenie trwa 1–2 tygodnie"
  ([cennik](https://join.playmore.pl/cennik/)).
  - The partner terms say plans renew unless cancelled 14 days before the period ends (§5) (carried,
    `platforms.md`, [partner terms](https://playmore.pl/legal/partner-terms), read 2026-10-07).
- **[POLICY]** Payouts: "Codziennie. Pieniądze za rezerwację opłaconą online trafiają na konto klubu w
  codziennej wypłacie, po rozegraniu gry" (daily, after the game is played) ([cennik](https://join.playmore.pl/cennik/)); the money passes
  "chwilowo na nasz rachunek" (carried, `platforms.md`, partner terms §9, read 2026-10-07).
  - *Reading:* Reservise collects the money, so the 1,79 % likely includes card processing; no separate
    processing fee is published.
- **[POLICY]** Its own comparison page, "Stan na 8 października 2026", tells a club that wants only a
  calendar: "Jeśli potrzebujesz tylko kalendarza, tańszy system może wystarczyć" (if you only need a calendar, a
  cheaper system may do)
  ([porównanie](https://join.playmore.pl/porownanie/)). It compares itself with kluby.org, Playtomic,
  Twój Tenis and ActiveNow — not tenis4U.
- **[POLICY]** Scale claims: "160+ klubów w Europie" for its club software
  ([cennik](https://join.playmore.pl/cennik/)); "1425 klubów w 201 miastach", "ponad 130 tys. aktywnych
  graczy", "ponad 19 tys. rezerwacji w tydzień" for its player portal ([playmore.pl](https://playmore.pl/)).
  - *Reading:* the 1 425 include clubs Playmore only lists, such as tenis4U's (see `integration.md` §5).

### Reservise (legacy, being retired into Playmore)
- **[PRICE]** The last Polish price list, archived 10 July 2026: "Rozliczamy się za efekty!", every plan
  with all features, priced by online and mobile bookings a month: **299 zł** (do 100), **399 zł**
  (101–200), **599 zł** (201–500), **1099 zł** (500+) "miesięcznie", per location; "Darmowe wdrożenie",
  "Migracje z innych systemów", start-up "do 48h roboczych, łącznie z importem danych"
  ([Wayback: reservise.com/pl/pricing](https://web.archive.org/web/20260710103417/https://reservise.com/pl/pricing/)).
  The English page priced the same tiers at €80/120/180/300
  ([Wayback, 13 Jun 2026](https://web.archive.org/web/20260613113454/https://reservise.com/en/pricing/)).
- **[POLICY]** Migration offer: "Reservise żegna się po 10 latach. Przenosimy Cię na Playmore"; "Nic nie
  tracisz, Twój abonament zostaje bez zmian"; "Zamrażasz swoją cenę"; "Rezerwacje, bazę klientów,
  cennik i całą historię przenosimy"; a 45-minute call; "Do kiedy muszę przejść? Termin ustalamy
  indywidualnie" ([join.playmore.pl/reservise](https://join.playmore.pl/reservise/)).
- **[ABSENT]** Whether a migrated Reservise club also pays the 1,79 %
  ([reservise page](https://join.playmore.pl/reservise/), [cennik](https://join.playmore.pl/cennik/)).

### kluby.org (IT Sports Solutions, Warsaw)
- **[PRICE]** "KLUB BASIC — do 30 rezerwacji miesięcznie — 50 PLN / mies."; "* Po jednorazowym
  przekroczeniu 30 rezerwacji przejście na plan PRO". **KLUB PRO "od 79 PLN"** by "liczba obiektów
  udostępnionych do rezerwacji (korty, boiska, salki, etc.)": 1 → 79, 2 → 139, 3 → 179, 4 → 209, 5 → 249,
  then +30 zł each to 10 → 399, … 15 → 549, 16+ → 599 zł. "Wszystkie podane ceny są kwotami netto." Each
  plan: "2 miesiące gratis" ([cennik](https://oferta.kluby.org/cennik)).
  - The table earlier showed two price columns (carried, `platforms.md`, read 2026-10-08); today it shows one.
- **[PRICE]** Support: included "wg kolejności", 9–17; BUSINESS 99 zł (8 h), VIP 199 zł (5 h), MAX 299 zł
  (3 h); training, audit, consultation 200 zł/h; "Ceny za miesiąc korzystania z usługi (miesieczny okres
  wypowiedzenia)" ([cennik](https://oferta.kluby.org/cennik)). Add-on modules ROZGRYWKI 50, ZAJĘCIA 99,
  TRENER 50, WYDARZENIA 50 zł a month.
- **[PRICE]** Online payments: "opłaty za rezerwacje: dobrowolne lub wymagane 25%/50%/100%" — "Ile to
  kosztuje?: Prowizja 2%"; SMS 0,07–0,16 zł each; door/light control priced per install
  ([integracje](https://oferta.kluby.org/integracje)).
- **[POLICY]** "Wypróbuj przez 60 dni za darmo bez konsekwencji!"; "Jeżeli nie będziesz zadowolony -
  możesz w każdej chwili zrezygnować!" (60 days free; quit at any time if unhappy) ([oferta](https://oferta.kluby.org)).
- **[ABSENT]** A migration offer from another system ([oferta](https://oferta.kluby.org),
  [cennik](https://oferta.kluby.org/cennik)).

### Twój Tenis (Kraków tennis, old and new platform)
- **[POLICY]** "Wdrażamy nową wersję najstarszego polskiego serwisu do rezerwacji kortów"; "W najbliższych
  tygodniach będziemy migrować kolejne kluby na nową platformę"; players need "założenie nowego konta …
  oraz podanie numeru telefonu używanego w starej wersji" (a new account, and the phone number used on the
  old version). Clubs listed on the new platform with start
  dates include Błonia Sport (23.04.2026), WKS Wawel, Centrum Sportowe Czyżyny, Korty ziemne (Centrum
  tenisowe PK), KKT Olsza, Sport Klub Kryspinów, KS Nadwiślan, Akademia Topsportu, Klub Tenisowy Błonia,
  Korty Dąbskie, TENIS24 and Forehand (to 21.07.2026), plus clubs outside Kraków
  ([twojtenis.pl, bundle](https://www.twojtenis.pl/assets/index-Bf6nIpMv.js)).
- **[POLICY]** The old site: "34 liczba naszych klubów", "227 liczba kortów", "4 416 898 dokonanych
  rezerwacji", "73 680 liczba użytkowników", "16 lat"; club accounts need "weryfikacja działalności"
  ([old.twojtenis.pl](https://old.twojtenis.pl/)).
- **[ABSENT]** Any club price, on either site; Playmore's comparison found none either
  ([porównanie](https://join.playmore.pl/porownanie/)).

### PADO (Wrocław; lists Kraków clubs)
- **[PRICE]** "Only 2% of the booking cost per court", which the club may pass to the player (carried,
  `platforms.md`, [for clubs](https://pado.app/for-club), read 2026-10-08).

### Playtomic Manager (Spain; no Kraków club)
- **[POLICY]** Plans Standard, Professional, Champion, Master; "Monthly / Yearly"; no amounts
  ([pricing](https://playtomic.com/pricing)). Checkout is by card through Stripe: "Enjoy the first two weeks
  free"; a failed renewal leaves 5 days before "your club will be automatically set to inactive"
  ([help, updated 2026-10-10](https://helpmanager.playtomic.com/hc/en-gb/articles/20535458071313)).
- **[POLICY]** Monthly ↔ annual needs cancel and resubscribe
  ([help](https://helpmanager.playtomic.com/hc/en-gb/articles/46121277584017)); cancelling "does not
  automatically take your club offline … you'll also need to contact our team"; "Cancel your
  subscription at least 30 days before you want your club to go offline"; seasonal clubs are told to use
  monthly renewal ([help, updated 2026-10-09](https://helpmanager.playtomic.com/hc/en-gb/articles/50864435573009)).
- **[POLICY]** Commission: "Every time a player pays for a booking online … our service fee is
  automatically deducted from that payment before the money reaches you", invoiced monthly; refunds
  corrected "with a credit note" ([help, updated 2026-10-09](https://helpmanager.playtomic.com/hc/en-gb/articles/50654517291537)).
  The rate is per contract; the only figure Playtomic prints is an example, "3.5% (example of your
  center's commission)", which includes processing (carried, `competitor-club.md` §8,
  [help](https://helpmanager.playtomic.com/hc/en-gb/articles/26470554139025), read 2026-10-08).
- **[COMPLAINT]** A rival vendor's claim, unsourced: "4% fee on every booking … €59–€279/mo" (carried,
  `competitor-club.md` §8, [Book & Go DE](https://www.bookandgo.app/de/playtomic-alternative), read 2026-10-06).
- **[ABSENT]** Any first-party Playtomic plan price or commission rate: pricing page, and a search of the
  club help centre for "commission", "subscription price", "plan price", "contract", "minimum term",
  "onboarding fee" ([pricing](https://playtomic.com/pricing)).

### MATCHi (Sweden; merging with Eversports)
- **[POLICY]** A venue's monthly statement carries "Monthly platform fees — always included if your venue
  has an active subscription, even if you had no revenue that month", SMS fees, and per-payment fees in
  four contract shapes: "Fixed transaction fee for … bookings of 60 minutes or less", per booking length,
  "Variable transaction fee with percentage fee specified", or "fixed fee + x %"; cash and manual
  payments generate no line ([help, updated 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/15268887132317)).
- **[ABSENT]** Any amount — platform fee or transaction fee — on matchi.se, its "get MATCHi" page or the
  venue help centre (searched "subscription", "transaction fee", "license", "commission").

### Padel Mates (Sweden)
- **[PRICE]** "No subscription for players. Clubs only pay when they earn."; club card "From 0 SEK /month"
  with "Booking system, Payments & payouts, In-app marketing, Support 7 days a week"; "We migrate your
  courts, members and schedule. Launch-ready in days, not months"
  ([web-app strings](https://padelmates.se/locales/en/translation.json)).
- **[ABSENT]** The rate a club pays when it earns ([same file](https://padelmates.se/locales/en/translation.json)).

### Eversports Manager (Austria)
- **[PRICE]** Sports-centre packages, "Courts can be – Padel, Tennis, Badminton or Squash courts":
  **Starter** up to 8 courts **€99/month** billed annually (€113 monthly); **Accelerate** up to 16 courts
  **€149** (€166); **Professional** unlimited courts **€199** (€221); "plus setup € 199 one-time"; light
  control and door access €38 a month each plus a one-time €729–1 378
  ([pricing, page data](https://www.eversportsmanager.com/pricing)).
- **[POLICY]** "The transaction fees are outlined in your Eversports contract"; "A small surcharge is added
  for central management" ([help](https://helpcenter.eversportsmanager.com/1-setup-online-payments));
  "transaction fees from payment service providers may apply" ([pricing](https://www.eversportsmanager.com/pricing)).

### CourtReserve (US)
- **[PRICE]** **Launch** "Includes 8 Courts" **$199/month** ($159 billed annually); **Advance** 16 courts
  **$369** ($329); **Momentum** 32 courts **$549** ($499); branded app "One-time $499 setup fee & 1-year
  contract"; integrations $25 a month each ([pricing](https://courtreserve.com/pricing/)).
- **[POLICY]** "Unless otherwise agreed, CourtReserve plans are subscription based"
  ([pricing FAQ](https://courtreserve.com/pricing/)).

### ClubSpark (UK)
- **[POLICY]** Free "to all LTA registered venues" (carried, `integration.md`,
  [LTA, 2021-04-20](https://prod.lta.org.uk/news/2021/april/lta-launches-partnership-with-clubspark-to-provide-enhanced-online-booking-system/)).
- **[ABSENT]** Any first-party price or transaction fee ([clubspark.com](https://clubspark.com/); /pricing is 404).
  A rival's comparison claims "1.4% + 5p" per transaction plus Stripe (via web search, Book & Go — not used).

### Rakieta today
- **[POLICY]** No platform fee; the club is the seller on its own Stripe account and pays Stripe's fee,
  1,5 % + 1 zł for a standard EEA card (carried, `local-market.md`,
  [Stripe pricing PL](https://stripe.com/en-pl/pricing), read 2026-10-06).

## 2. What each rival charges the player

- **[PRICE] Playtomic, Poland** — the country table: "Open Matches PLN 20.0 % · min 1.24 · max 3.99";
  "Player Bookings NO FEE"; Classes 4,0 % (1,24–8,49); Courses 2,0 % (1,24–12,99); Leagues and
  Tournaments 4,0 % (1,24–8,49) ([Service Fee, updated 2026-10-02](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337),
  [Poland table](https://playerhelp.playtomic.com/hc/article_attachments/39560464619025)). It "will not be
  refunded if you cancel a reservation" and "will be refunded, If you delete yourself from an open match
  or if the match is canceled".
  - **[PRICE]** Cancellation fee on player-made private bookings: "Poland PLN 4.32", 1-hour grace, taken
    from the refund while "also keep[ing] the Playtomic fee"
    ([help, updated 2026-07-20](https://playerhelp.playtomic.com/hc/en-gb/articles/19831791848721)).
  - *Reading:* on a 100 zł court split four ways, 20 % of a 25 zł seat is 5 zł, capped to 3,99 zł — about
    16 zł on top of the court for the four players.
- **[PRICE] MATCHi** — "The service fee is 4% of the transaction amount, with a minimum and maximum amount
  that varies per market", in Belgium, Denmark, Finland, Netherlands, Norway, Romania, Sweden, Thailand
  (e.g. Sweden 3–15 SEK, Netherlands 0,30–1,80 €); "generally non-refundable"; "As a venue admin, you can't
  turn it on, turn it off, or change its rate"
  ([venue help, updated 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/21623335434269),
  [player help](https://matchiplayers.zendesk.com/hc/en-gb/articles/21632070063517)). Not Poland.
- **[PRICE] Playmore** — Atras: "Do rezerwacji opłaconych online doliczamy opłatę serwisową 1,48 zł"
  (carried, read 2026-10-06); Squash4You, today: "Do rezerwacji opłaconych online doliczamy opłatę
  serwisową 1,48 zł" ([Squash4You cennik](https://playmore.pl/klub/squash4you/cennik/)). The club price page:
  "Opłata serwisowa: przy płatności online dopłaca ją gracz, nie klub. Jej wysokość podajemy w ofercie"
  ([cennik](https://join.playmore.pl/cennik/)).
  - **[POLICY]** Terms §8.8–8.11: "Reservise pobiera od Użytkownika prowizję"; "Wysokość opłaty ustalana
    jest dynamicznie i zależy od: metody płatności, rodzaju Partnera, wartości Rezerwacji oraz innych
    parametrów"; shown "przed finalizacją Rezerwacji"; "Opłata nie podlega zwrotowi w przypadku anulowania"
    ([terms](https://playmore.pl/legal/terms-of-service), [text chunk](https://playmore.pl/assets/CjQyHVHG.js)).
  - **[POLICY]** Yet the Kraków squash FAQ: "Rezerwacja kortu przez Playmore jest darmowa — płacisz tylko za
    sam wynajem kortu w klubie. Nie pobieramy prowizji od użytkowników"
    ([playmore.pl/squash/krakow](https://playmore.pl/squash/krakow/)).
  - **[POLICY] Wallet:** "W klubach z portfelem Playmore pieniądze nie wracają na kartę płatniczą — czekają
    tutaj na Ciebie"; withdrawal "„Zleć wypłatę" → numer konta → kod SMS", with a minimum and maximum
    amount; balance capped at "PLN 10 000"
    ([strings](https://playmore.pl/assets/CG9yQPLY.js), [terms §9.2](https://playmore.pl/assets/CjQyHVHG.js)).
    **[ABSENT]** A fee on withdrawing from the wallet (same files).
- **[POLICY] tenis4U** — "Nie pobieramy żadnych opłat za korzystanie z aplikacji" unless stated; "Usunięcie
  rezerwacji opłaconej za pomocą płatności internetowych generuje zwrot środków pomniejszonych o opłatę
  transakcyjną w wysokości 2%" (an online-paid booking cancelled is refunded minus a 2 % transaction fee) ([regulamin](https://tenis4u.pl/regulamin/)).
- **[POLICY] kluby.org** — services free unless stated; a paid "Konto Premium" exists (carried,
  `games-and-fill-in-market.md`, [regulamin](https://kluby.org/regulamin), read 2026-10-06). **[ABSENT]** A
  per-booking player fee or the Premium price ([regulamin](https://kluby.org/regulamin)).
- **[POLICY] Twój Tenis** — "Korzystanie z Portalu jest darmowe"; a payment arriving after the 15-minute
  window is refunded "pomniejszona o prowizję … Krajowy Integrator Płatności w wysokości do 2,5%"
  ([regulamin](https://old.twojtenis.pl/pl/regulamin.html)).
- **[POLICY] Padel Mates** — "No subscription for players" ([strings](https://padelmates.se/locales/en/translation.json)),
  though its US store listing sells a player PRO plan, $6 a month (carried, `games-and-fill-in-market.md`, read 2026-10-06).
- **[POLICY] CourtReserve** — the club may add "A convenience fee … for the ease of paying online", which
  "cannot exceed 4% of the transaction total", with "at least 30 days' advance notice" recommended
  ([help](https://help.courtreserve.com/en/articles/7172928-convenience-fees)).
- **[ABSENT]** A player-facing fee at Eversports or ClubSpark
  ([Eversports help](https://helpcenter.eversportsmanager.com/1-setup-online-payments), [clubspark.com](https://clubspark.com/)).

## 3. Why clubs switch

### Vendors' case studies (Poland)
- **[POLICY] Okęcie Tennis Club, Warsaw** — "obiekt z pełnym obłożeniem w godzinach szczytu"; before:
  "kilkadziesiąt nieopłaconych rezerwacji miesięcznie", the desk as "dział windykacji", "„Przecież mnie nie
  było, za co mam płacić?"", "„Rezerwacje-duchy" zabierały miejsca płacącym klientom". After: online
  payments "~20% → 100%", unpaid "kilkadziesiąt → 0", chasing "~20h/tyg. → 0h", "minus 1 etat". Owner:
  "odstraszył nieuczciwych klientów, którzy zajmowali korty i się nie pojawiali"
  ([case study](https://join.playmore.pl/case-studies/okecie-tenis-club/)).
- **[POLICY] Vera Sport, Łódź** — "ponad 200 nieopłaconymi rezerwacjami miesięcznie i stratami rzędu
  kilku tysięcy PLN miesięcznie"; after: "~200+ → 0", phone bookings get "SMS z 30-minutowym limitem na
  opłacenie". Owner: "Największą obawą było to, że klienci odejdą. Nie odeszli. Wręcz przeciwnie - mamy
  lepsze obłożenie" (the biggest fear was customers leaving; they didn't — occupancy is better)
  ([case study](https://join.playmore.pl/case-studies/vera-sport/)).
- **[POLICY] KS Zakręt, Warsaw** — weekend reception "1–2 osoby … niezależnie od obłożenia", "Kilka tys.
  zł miesięcznie"; after: "0 osób", doors and lights from the app with Loxone. Owner: "W weekendy nasz klub
  działa sam" ([case study](https://join.playmore.pl/case-studies/kszakret/)).
- **[POLICY]** Playmore's own advice: "Jeżeli obecny system nie zostawia mierzalnego problemu, nie zmieniaj
  go dla samej zmiany. Playmore ma sens wtedy, gdy przedpłaty, no-show, rozliczenia szkółki albo ręczna
  praca recepcji kosztują więcej niż zmiana systemu" (if your system leaves no measurable problem, don't
  change it for its own sake) ([dla klubów tenisa](https://join.playmore.pl/dla-klubow-tenisa/)).
- **[POLICY]** kluby.org's claims: leagues moved online "średnio już w 1 sezonie podwajają liczbę
  zarezerwowanych godzin"; "Aż do 70% mniej telefonów w przeciągu pierwszego roku"; 4,1 m bookings worth
  102,7 m zł ([oferta](https://oferta.kluby.org)).
  - *Reading:* 102,7 m zł over 4,1 m bookings is about 25 zł a booking.

### Clubs leaving Playtomic and MATCHi (abroad)
- **[COMPLAINT]** Rocket Padel and Padium (UK) left Playtomic "citing a lack of accessibility to their
  customers"; Padel Shed built its own software to "control our customer journey" (carried,
  `competitor-club.md` §12, [Padel Paper, 11 Dec 2025](https://thepadelpaper.com/playtomic-soul-padel-data/), read 2026-10-06).
- **[POLICY]** Racket Club (seven venues, Denmark) moved from MATCHi to Padel Mates from February 2025 "to
  ensure that you, as members, get the best experience when booking"
  ([padelalto, 21 Nov 2024](https://padelalto.com/2024/11/21/danish-padel-operator-switches-from-matchi-to-swedish-platform)).
- **[POLICY]** Padel Mates' testimonials: "Since switching to Padel Mates, we've seen a steady increase in
  occupancy through open matches and matchmaking" (Luleå Padel); "From migrating two existing clubs to opening
  two new ones" (PadelX); Rocket Padel UK "Since switching" ([strings](https://padelmates.se/locales/en/translation.json)).
- **[COMPLAINT]** "Ett monopol som ruinerar klubbar" — MATCHi charging clubs and players for more features
  (carried, `games-and-fill-in-market.md` §5, [App Store SE](https://apps.apple.com/se/app/matchi/id720782039?see-all=reviews), 26 Dec 2024).

### Forced migrations: what switching does to players
- **[COMPLAINT]** Reservise → Playmore, March 2025, App Store PL (one star unless stated):
  - "Nie było idealnie, za to jest gorzej. … Reservise była lepsza, bo działała" (MacKopyt, 2025-03-07);
  - "Nie widziałem jeszcze tak fatalnie przeprowadzonej zmiany świetnie działającej aplikacji na fatalną,
    która uniemożliwia pracę klubom tenisowym i zawodnikom" (Makos5768, 2025-03-08);
  - "Prosimy Przywróćcie poprzednią aplikację tenisiści korty Muchowiec" (KrisBrzydal, 2025-03-06)
  ([review feed](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortBy=mostRecent/json)).
  - *Reading:* 22 of the 50 most recent reviews fall between 6 and 26 March 2025.
- **[COMPLAINT]** The rebuilt app (v6, from 27 June 2026): "Odkąd aplikacja Reservise przeobraziła się …
  zwykła rezerwacja w obiekcie sportowym stała się uciążliwa" (2★, 2026-10-10); "Już naprawdę wolałem ta
  poprzednia wersje reservire … która może wyglądała jak z 2010 roku ale przynajmniej działała" (3★,
  2026-09-17); "Niestety muszę z niej korzystać, taki wymóg mojego obiektu sportowego" (1★, 2026-05-01)
  ([review feed](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortBy=mostRecent/json)).
- **[POLICY]** Twój Tenis asks every player to create a new account on its new platform (§1).

### Store ratings and the top complaints
| App | App Store PL | Google Play | Downloads (Play) |
| --- | --- | --- | --- |
| tenis4U | 4,7 from 103 ([store](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113)) | 4,2 from 162 ([Play](https://play.google.com/store/apps/details?id=pl.tenis4u.android.free&hl=pl&gl=PL)) | 50 tys.+ |
| Playmore | 4,2 from 492 ([store](https://apps.apple.com/pl/app/reservise-playmore/id928403015)) | 3,8 from 2 742 ([Play](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp&hl=pl&gl=PL)) | 50 tys.+ |
| kluby.org | 2,2 from 5 ([store](https://apps.apple.com/pl/app/kluby-org/id1658178253)) | 3,0 from 13 ([Play](https://play.google.com/store/apps/details?id=com.multiplatform.kluby&hl=pl&gl=PL)) | 5 tys.+ |

- **[COMPLAINT] tenis4U** — search and finding courts: "Nie ma wyszukiwania kortów w danym obszarze wg
  godzin, trzeba klikać po wszystkich kortach" (6 Sept 2026); cross-club blocks: "aplikacja umożliwia
  arbitralne zgłaszanie ostrzeżeń przez klub bez poinformowania użytkownika … skutkuje zablokowaniem
  możliwości rezerwacji we wszystkich klubach" (Bart W, 4 Jan 2026, Play); reach: "Aż dziwne, że w
  Warszawie nie ma ani jednego klubu korzystającego z aplikacji" (23 May 2025)
  ([App Store reviews](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113?see-all=reviews),
  [Play](https://play.google.com/store/apps/details?id=pl.tenis4u.android.free&hl=pl&gl=PL)).
- **[COMPLAINT] Playmore** — refunds and support: "On Sep 16 I emailed about refund for a reservation I
  cancelled on Sep 11 … still no reply" (2026-09-28); fees: "przerzucanie opłat transakcyjnych na klienta
  zamiast na klub" (2★, 2026-07-20) and "za Blika AutoPay pobiera 1,5 zł prowizji" (2★, 2025-07-25); held
  money: "Aplikacja od miesiąca blokuje środki i nie podaje w jaki sposób je można odebrać" (2025-10-21)
  ([review feed](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortBy=mostRecent/json));
  on Play: "Czy ta wspaniała aplikacja może w końcu pamiętać moje wybory cennika, rodzaju płatności …?"
  (2 Oct 2026) ([Play](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp&hl=pl&gl=PL)).
- **[COMPLAINT] kluby.org** — login: "Już tydzień nie mogę zalogować się" (07/06/2025); updates: "Nie polecam
  aktualizacji" (17 Mar 2026); payments: "płatność online do bani. ciężko się połapać ogólnie" (26 Jan 2026,
  Play) ([App Store reviews](https://apps.apple.com/pl/app/kluby-org/id1658178253?see-all=reviews),
  [Play](https://play.google.com/store/apps/details?id=com.multiplatform.kluby&hl=pl&gl=PL)).

### What clubs are told they lack
- **[POLICY]** Playmore's pitch for open games: "Puste korty rano to nie brak popytu. To brak kojarzenia
  graczy"; "Bez partnera gracz nie zarezerwuje kortu - po prostu nie przyjdzie"; "Recepcja nie skojarzy
  graczy … Każda taka próba to telefony i wiadomości" ([gry otwarte](https://join.playmore.pl/gry-otwarte/)).
- **[POLICY]** For squash: "Rezerwacja bez przedpłaty na 19:00 to ryzyko pustego kortu w najdroższej godzinie
  dnia"; a report shows "gdzie podnieść cenę, a gdzie martwe poranki potrzebują promocji"
  ([dla klubów squasha](https://join.playmore.pl/dla-klubow-squasha/)).
- **[ABSENT]** A Kraków club saying, in its own words, why it would change systems: no club statement found
  beyond Atras's "Przeszliśmy na system Playmore" (carried, `games-and-fill-in-market.md`,
  [Atras](https://www.atrassquash.pl/rezerwacje/), read 2026-10-06).

## 4. The empty-hours problem

### Where the pitch comes from
- **[POLICY]** "Martwe godziny zjadają marżę — Wieczory wyprzedane, ale rano i wczesnym popołudniem korty
  stoją puste. Czynsz, prąd i etaty lecą niezależnie od tego, czy ktoś gra" (dead hours eat the margin;
  evenings sold out, mornings and early afternoons empty; rent, power and staff are paid regardless). No
  figure, survey or source accompanies it ([gry otwarte](https://join.playmore.pl/gry-otwarte/)).
- **[POLICY]** Playmore's analytics page shows a sample dashboard: "Rano · 7:00–12:00 42%",
  "Popołudnie · 12:00–16:00 58%", "Prime time · 16:00–22:00 89%", with the advice "Rano 42% - pomysł na
  promocję lub karnet poranny" ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - *Reading:* these are illustrative product figures, not a measurement of any club.

### Published occupancy data
- **[DOCS]** Playtomic and PwC Strategy&'s Global Padel Report 2025: average ticket per booking (player and
  club bookings) Spain 24 €, France 29 €, Germany 43 €, UK 52 €; it names off-peak products only as a
  tactic — clubs "are forced to create engaging products during off-peak hours: open matches, rankings,
  Americanas" (Mexico) ([GPR 2025, pp. 17, 27](https://8258038.fs1.hubspotusercontent-na1.net/hubfs/8258038/Global%20Padel%20Report/PLAYTOMIC_GLOBAL%20_PADEL_REPORT_2025.pdf)).
  The 2024 edition ranks UK counties by occupancy without percentages
  ([GPR 2024](https://8258038.fs1.hubspotusercontent-na1.net/hubfs/8258038/Global%20Padel%20Report/Playtomic%20and%20Strategy%26%20-%20Global%20Padel%20Report.pdf)).
- **[ABSENT]** Off-peak or hour-by-hour occupancy, and any Poland figure, in the 2024 and 2025 reports; the
  2026 edition ("Club Economics") sits behind a form and was not read
  ([report page](https://playtomic.com/global-padel-report)). MATCHi's "Padel Report" (2022) is also
  form-gated ([page](https://playmore.matchi.com/the-padel-report-by-matchi)). No Polish federation,
  city or club occupancy data was found (web search, Polish and English).
- **[POLICY]** Vendor claims only: Padel Mates' Luleå testimonial (occupancy up "through open matches"),
  Vera Sport's "lepsze obłożenie" (§3).

### How Kraków clubs price the day, read 2026-10-12
| Club | Sport | Weekday off-peak | Weekday peak | Off-peak ÷ peak | Source |
| --- | --- | --- | --- | --- | --- |
| Garden Padel | padel, outdoor | 8–9 **50 zł**; 9–15 **100 zł** | 15–23 130 zł (weekend 130) | 0,77 | [PRICE] Playmore's club FAQ ([page](https://playmore.pl/klub/garden-padel/)) |
| Fame Sport | padel, hall, winter 2026/27 | 7–14 **135 zł** | 14–23 150 zł (weekend 140) | 0,90 | [PRICE] [cennik](https://famesport.pl/cennik/) |
| Fame Sport | tennis, hall, winter | 11–14 **100 zł** (7–11 120) | 14–23 140 zł | 0,71 | [PRICE] [cennik](https://famesport.pl/cennik/) |
| Padel House | padel, hall | 7–16 **120 zł** | 16–24 160 zł (weekend 160) | 0,75 | [PRICE] PADO listing ([page](https://pado.app/poland/krakow/clubs/padel-house-krakow)) |
| Morelowa 34 | padel | 7–17 **140 zł** | 17–23 160 zł | 0,88 | [PRICE] PADO ([page](https://pado.app/poland/krakow/clubs/morelowa-34-padel-krakow)) |
| Bajada | padel | 7–16 **80 zł** | 16–23 100 zł | 0,80 | [PRICE] PADO ([page](https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow)) |
| Libertów | padel | to 16 **100 zł** | 16–24 110 zł | 0,91 | [PRICE] PADO ([page](https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club)) |
| Atras | squash, online | 10–16 **45 zł** (7–10 54) | 17–22 103,50 zł | 0,43 | [PRICE] [cennik, from 1.09.2026](https://www.atrassquash.pl/cennik/) |
| Paolo | squash, online | 10–16 **40 zł** (8–10 70) | 17–22 110 zł | 0,36 | [PRICE] Playmore's club FAQ ([page](https://playmore.pl/klub/paolo-squash-club/)) |
| Squash4You | squash, online, Mon–Thu | 11–16 **65 zł** (7–11 75) | 17–22 120 zł | 0,54 | [PRICE] [Playmore cennik](https://playmore.pl/klub/squash4you/cennik/) |
| KSOS | tennis, outdoor | 6–14 **60 zł** | 14–22 75 zł | 0,80 | carried, [KSOS](https://obiekty.ksos.pl/korty-tenisowe/), read 2026-10-07 |

- **[PRICE]** Off-peak tools already in use: Atras "Zniżka studencka 25% / 50% … W tygodniu poza godzinami
  17:00 – 22:00", and online "zawsze 10% taniej" ([Atras](https://www.atrassquash.pl/cennik/)); Squash4You
  "Happy Hours … migrujące terminy w niższych cenach — za godzinę gry zapłacisz 50–65 zł"
  ([Playmore page](https://playmore.pl/klub/squash4you/)); Paolo "Kiedy gra się najtaniej? … To mniej niż
  połowa ceny wieczornej godziny" ([Playmore page](https://playmore.pl/klub/paolo-squash-club/)).
- **[LAW]** Court time to individuals is VAT 8 % (carried, `local-market.md`,
  [WIS 687645](https://eureka.mf.gov.pl/informacje/podglad/687645), read 2026-10-06).

### What one empty hour is worth
- *Reading:* a weekday-daytime **padel** hour that sells is **80–140 zł** gross, **74–130 zł** net of 8 % VAT;
  a **squash** hour **40–65 zł** online, **37–60 zł** net. One extra sold hour per court each weekday (~21
  a month) is 1 680–2 940 zł gross per padel court a month, 840–1 365 zł per squash court.
- *Reading:* the marginal cost of a filled hour (light, heat, cleaning) was not found; KSOS's "10 zł" light
  surcharge (carried) is the only public proxy.

## 5. What Rakieta could charge — mechanics and law

### Ways to charge, side by side (*reading*, on a 100 zł court split four ways)
| Way | Who pays Rakieta | What it costs whom on that booking | Precedent |
| --- | --- | --- | --- |
| Free (today) | nobody | the club pays Stripe 4 × (1,5 % × 25 + 1 zł) = **5,50 zł** for four seat charges | Rakieta |
| Monthly subscription | the club | a fixed zł a month; Stripe Billing 0,7 % of it | tenis4U, kluby.org, Eversports, CourtReserve |
| Per-booking fee from the club's charge | the club | X % on top of the 5,50 zł | Playmore 1,79 %, kluby.org 2 %, PADO 2 %, Playtomic (example 3,5 %) |
| Player service fee | the player | e.g. 1,48 zł a booking, or 20 % capped at 3,99 zł a seat | Playmore, Playtomic, MATCHi |

- *Reading:* the 1 zł fixed part of Stripe's fee is charged per seat, so splitting a court into four charges
  costs more than one charge — a single Przelewy24 charge on the club's own contract is 1,59 zł (carried
  P24 price), and Playmore's commission on the same 100 zł is 1,79 zł.

### A subscription to the club
- **[PRICE]** Stripe Billing, Poland: "Pay as you go … 0.7% of Billing volume", or annual tiers from
  2 500 zł a month ([Billing pricing](https://stripe.com/en-pl/billing/pricing)); Stripe Invoicing "0.4% per
  paid invoice" (Starter) ([Invoicing pricing](https://stripe.com/en-pl/invoicing/pricing)).
- **[PRICE]** Stripe Connect "Pay with Stripe balance (Preview)" lets a platform "Collect subscription fees
  directly from your customers' Stripe balance" at "1% of transaction volume"
  ([Connect pricing](https://stripe.com/en-pl/connect/pricing)).
- **[LAW]** VAT: art. 41 ust. 1 sets 22 %, but art. 146ef ust. 1 pkt 1 makes it **23 %** "w okresie od dnia
  1 stycznia 2024 r. do końca roku, w którym" defence spending exceeds 3 % of GDP
  ([ustawa o VAT, Dz.U. 2026 poz. 1263](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf)).
- **[DOCS]** KSeF is mandatory from 1 Feb 2026 for sellers over 200 m zł and from 1 Apr 2026 for everyone
  else, with a seller invoicing ≤ 10 000 zł a month exempt until 1 Jan 2027 (carried, `local-market.md`, [KSeF](https://ksef.podatki.gov.pl/etapy-wdrozenia-ksef/), read
  2026-10-06). **[POLICY]** Fakturownia: "Integracja ze Stripe jest w pełni kompatybilna z Krajowym Systemem
  e-Faktur (KSeF)"; "Aby uniknąć podwójnego fakturowania, zalecamy jej wyłączenie w ustawieniach Stripe"
  ([Fakturownia + Stripe](https://fakturownia.pl/apps/stripe-app)). **[ABSENT]** Any Stripe page on KSeF
  (web search of stripe.com and docs.stripe.com).

### A per-booking fee taken from the club's charge
- **[DOCS]** "`payment_intent_data[application_fee_amount]`: This attribute specifies the amount your platform
  deducts from the transaction … After the payment is processed on the connected account, the
  application_fee_amount is transferred to the platform." Limits: "must be positive and less than the amount
  of the charge … capped at the captured amount"; "There are no additional Stripe fees on the application fee
  itself" ([direct charges](https://docs.stripe.com/connect/direct-charges)).
- **[DOCS]** "Application fees aren't automatically refunded when issuing a refund. Your platform must
  explicitly refund the application fee or the connected account … loses that amount" — `refund_application_fee=true`,
  proportional on a partial refund ([direct charges](https://docs.stripe.com/connect/direct-charges)).
- **[DOCS]** With the fee collector set to Stripe, "Stripe deducts its processing fee and your application fee
  from the payment … Set the application fee amount to include only your fee"
  ([fee behaviour](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior)); such platforms "do not
  incur additional account, payout volume, tax reporting, or per-payout fees", and "Collect additional fees
  on each transaction" is "Included" ([Connect pricing](https://stripe.com/en-pl/connect/pricing)). The no-code
  Platform Pricing Tool "is currently only available for platforms responsible for paying Stripe fees"
  ([direct charges](https://docs.stripe.com/connect/direct-charges)).
- **[POLICY]** Precedent for invoicing it: Playtomic deducts its fee before the money reaches the club and
  sends "a single invoice for the total" monthly ([help](https://helpmanager.playtomic.com/hc/en-gb/articles/50654517291537)).
  - *Reading:* Rakieta's fee to a Polish club is its own B2B sale — 23 % VAT and a KSeF invoice.

### A service fee on top, paid by the player
- **[LAW]** Before the consumer is bound the trader states "łącznej cenie lub wynagrodzeniu za świadczenie wraz
  z podatkami … a także opłatach … oraz innych kosztach" (art. 12 ust. 1 pkt 5); "przedsiębiorca ma obowiązek
  uzyskać wyraźną zgodę konsumenta na każdą dodatkową płatność" and a pre-ticked one is refundable (art. 10);
  "Jeżeli przedsiębiorca nie spełnił obowiązków informacyjnych dotyczących opłat dodatkowych … konsument nie
  ponosi tych opłat" (art. 23) ([ustawa o prawach konsumenta, Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)).
- **[LAW]** A marketplace operator ("dostawca internetowej platformy handlowej") must also tell the consumer the
  main ranking parameters, "czy osoba trzecia oferująca … usługi … jest przedsiębiorcą", and the "podziale
  obowiązków" between the seller and the platform (art. 12a) ([same act](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)).
- **[LAW]** UOKiK, eBilet, 16 Nov 2023: "This price will have to include a service fee or other mandatory fees,
  if any"; "the initially promised price of PLN 135, went up to PLN 141.75"; "eBilet was obliged to refund the
  service fee to those consumers who had filed complaints" ([UOKiK](https://uokik.gov.pl/en/a-commitment-and-a-fine-two-decisions-by-president-of-uokik-in-the-ebilet-case)).
- **[LAW]** Omnibus pricing covers services in Poland: "cena" includes VAT (art. 3 ust. 2); "W każdym przypadku
  informowania o obniżeniu ceny towaru lub usługi … uwidacznia się również informację o najniższej cenie …
  w okresie 30 dni przed wprowadzeniem obniżki" (art. 4 ust. 2)
  ([ustawa o informowaniu o cenach, Dz.U. 2023 poz. 168](https://api.sejm.gov.pl/eli/acts/DU/2023/168/text.pdf)).
  Playmore's terms repeat it: "W przypadku obniżki ceny poinformujemy Cię również o najniższej cenie Usługi
  Partnera z ostatnich 30 dni" (§8.6) ([terms chunk](https://playmore.pl/assets/CjQyHVHG.js)).
  - *Reading:* a "−30 % this morning" label on an empty hour triggers the 30-day lowest-price line.
- **[POLICY]** How rivals do it: MATCHi's fee "is presented to the player as its own line item at checkout"
  and is "collected by MATCHi" ([help](https://matchi.zendesk.com/hc/en-gb/articles/21623335434269));
  Playtomic invoices its B2C fee to the player itself (carried, `games-and-fill-in-market.md` §1.2, read 2026-10-06).
  - *Reading:* on a direct charge the whole amount is the club's sale (merchant of record, carried), so a
    Rakieta fee to the player is either a second charge on Rakieta's own account, with its own 23 % VAT
    receipt, or part of the club's price.

### Free
- *Reading:* staying free costs Rakieta nothing at Stripe while Stripe collects its fees from the clubs — no
  per-account or payout fee ([Connect pricing](https://stripe.com/en-pl/connect/pricing)); the 9 zł a month
  per active account and 0,25 % + 1,35 zł per payout apply only if Rakieta takes over fee collection (same page).
  The club still pays card fees, as tenis4U's clubs pay Przelewy24/Tpay today.

### What a platform owes clubs: the P2B Regulation
- **[LAW]** Scope: services that "allow business users to offer goods or services to consumers, with a view to
  facilitating the initiating of direct transactions … irrespective of where those transactions are ultimately
  concluded", on a contract with the business user (art. 2(2)); it applies whatever the provider's size
  ([Regulation (EU) 2019/1150](https://eur-lex.europa.eu/eli/reg/2019/1150/oj)).
- **[LAW]** Duties: terms in "plain and intelligible language", available pre-contract, with the grounds to
  suspend or terminate (art. 3(1)); changes notified on a durable medium at least **15 days** ahead, the club
  free to terminate (art. 3(2)); a statement of reasons **30 days** before ending the whole service (art.
  4(2)); "the main parameters determining ranking" and any paid influence on it (art. 5(1), (3)); no
  retroactive changes, exit conditions, and what data survives the contract (art. 8); what data each side can
  access (art. 9) ([same](https://eur-lex.europa.eu/eli/reg/2019/1150/oj)).
- **[LAW]** The internal complaint-handling system (art. 11(5)) and naming mediators (art. 12(7)) "shall not
  apply to providers … that are small enterprises" — "fewer than 50 persons" and turnover or balance sheet "not
  exceed[ing] EUR 10 million" ([Recommendation 2003/361/EC, Annex art. 2](https://eur-lex.europa.eu/eli/reco/2003/361/oj)).
- *Reading:* the club website alone is the club's own tool; the Games deck, which shows clubs' courts and
  games to Rakieta's players, is what makes Rakieta an "online intermediation service".

### The DSA, briefly
- **[LAW]** The trader-traceability section for "online platforms allowing consumers to conclude distance
  contracts with traders" (art. 30–32: name, ID, payment account, register number, self-certification) "shall
  not apply to providers … that qualify as micro or small enterprises" (art. 29); art. 19 exempts them from
  the general online-platform section the same way, "with the exception of Article 24(3)"
  ([Regulation (EU) 2022/2065](https://eur-lex.europa.eu/eli/reg/2022/2065/oj)).

### DAC7: reporting the clubs' income
- **[LAW]** The directive: a "Platform" is software "allowing Sellers to be connected to other users for the
  purpose of carrying out a Relevant Activity", including "any arrangement for the collection and payment of a
  Consideration"; it excludes software that "exclusively allows" payment processing, listing or redirecting.
  Relevant activities: "the rental of immovable property, including both residential and commercial property,
  as well as any other immovable property and parking spaces", a "Personal Service" (time- or task-based work
  by individuals — coaching), goods, transport. Excluded sellers: governmental entities, listed companies, an
  Entity with "more than 2 000 Relevant Activities by means of the rental of immovable property in respect of a
  Property Listing" (all units "at the same street address … same owner … same Seller"). Report by 31 January
  ([Directive (EU) 2021/514, Annex V](https://eur-lex.europa.eu/eli/dir/2021/514/oj)).
- **[LAW]** Poland's wording is wider: "stosownej czynności — … a) udostępnienie nieruchomości, ich części, w
  tym pomieszczeń przynależnych, lub udziału w nieruchomościach" (making real property or a part of it
  available); the operator reports to the Szef KAS "do końca miesiąca następującego po zakończeniu okresu
  sprawozdawczego"; a seller who does not supply its data within 60 days has its payouts held ("wstrzymać
  wypłatę wynagrodzenia") or bookings blocked; due diligence done by 31 December; penalties up to
  1 000 000 zł (art. 75a ust. 1 pkt 20, 24; art. 75b ust. 1; art. 75o ust. 5–6; art. 75p; art. 90b with
  art. 91 ust. 1) ([Dz.U. 2024 poz. 879](https://api.sejm.gov.pl/eli/acts/DU/2024/879/text.pdf),
  [ISAP](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240000879)); in force 1 July 2024.
- **[POLICY]** MATCHi reads its own scope narrowly: "Currently, only personal services are in scope —
  coaching sessions … Standard court bookings made directly by players are not included"
  ([help, updated 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/16302209202205)). Booksy, a Polish
  booking platform, reports "rezerwacji dokonanych i opłaconych przez klientów za pomocą Booksy"
  ([Booksy, 14 Oct 2024](https://biz.booksy.com/pl-pl/blog/unijna-dyrektywa-dac7-co-powinni-wiedziec-o-niej-wlasciciele-biznesow)).
  - *Reading:* under the Polish text an hour of court hire paid through Rakieta is very likely "udostępnienie
    części nieruchomości", so Rakieta would report each club; a municipal centre (MOSiR/OSiR) is an excluded
    governmental seller; a club passing 2 000 Rakieta bookings a year at one address drops out as a seller.

## 6. Threats

- **[POLICY] tenis4U is shipping the social layer.** Its iOS release notes: 4.3.0 (20 Apr 2026) "dodano
  możliwość zapraszania innych graczy do rezerwacji oraz współdzielenia płatności"; 4.6.0 (2 Jun 2026)
  "umożliwiono tworzenie meczy rankingowych"; 4.7.0 (15 Jun) doubles tournaments; 4.8.5 (22 Sept) "kod do
  zamka"; 4.9.1–4.9.2 (Oct) "karnetów czasowych"
  ([App Store](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113)).
  - This dates invites and shared payment to **April 2026** — 4.2.2 (13 Apr) added "wsparcie dla systemu iOS
    26" — correcting `local-market.md`'s "Apr 2025".
- **[POLICY] Its ELO ranking is built and hidden.** In the web app: "Flaga: wizualna prezentacja systemu
  rankingowego ELO (ratingi, mecze, H2H). // false = ukrywa komponenty rankingowe w UI. Pobieranie danych z
  API pozostaje aktywne. const RANKING_FEATURE_ENABLED = false", for "RANKED_SPORTS = ['TENNIS', 'PADEL',
  'PICKLEBALL']"; a court's "Otwarte sparingi" tab ("Brak otwartych sparingów na tym korcie", "Zaloguj się,
  aby dołączyć do sparingu") ([app.tenis4u.pl bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[ABSENT]** A public tenis4U roadmap, blog, changelog or press item ([tenis4u.pl](https://tenis4u.pl/),
  [sitemap](https://tenis4u.pl/wp-sitemap.xml)).
- **[POLICY] Playmore's open games are live and free.** Release 6.1.29 (27 Jun 2026): "Gry otwarte — znajdź
  partnera, podziel koszt"; then weekly releases ([App Store](https://apps.apple.com/pl/app/reservise-playmore/id928403015));
  "Gry otwarte - bezpłatne w każdym pakiecie. Martwe godziny zapełniają się same"
  ([gry otwarte](https://join.playmore.pl/gry-otwarte/)); games made 3+ days ahead fill "mniej więcej 3 razy
  częściej" (carried, `platforms.md`, read 2026-10-07).
- **[ABSENT]** Any count of Playmore open games created or filled, in its pages, case studies or store notes.
- **[POLICY] Twój Tenis is re-platforming Kraków tennis** (§1) — a window in which its clubs' players must
  re-register anyway.
- **[POLICY] Playtomic in Poland:** 33 Polish clubs, none in Kraków; no Polish website, help or payment method
  (carried, `local-market.md`, read 2026-10-06/08). **[ABSENT]** Any announcement, job posting or press about
  Playtomic entering Kraków or Poland further (web search; playtomic.com/work-with-us is 404).
- **[POLICY] PadelCity** lists Kraków "– soon –", booked only in its own app (carried, `platforms.md`,
  [padelcity.pl](https://www.padelcity.pl/), read 2026-10-06).

## 7. Side by side

| Rival | Club price (net, a month) | Player fee | Commission · who pays card fees | Contract · trial | Migration |
| --- | --- | --- | --- | --- | --- |
| tenis4U | 49 / 89 / 149 zł by courts; BASIC 10 zł | none to use; 2 % kept on refunds | none published · club, on its own P24/Tpay contract | not published | not published |
| Playmore | 299 / 399 / 499+ zł by courts; Challenger +249 zł | service fee, 1,48 zł at Atras/Squash4You; dynamic; non-refundable | 1,79 % of online, 0 at the desk · included (*reading*) | monthly, monthly notice, −20 % yearly · 14 days, no card | 0 zł, 1–2 weeks, data moved |
| Reservise (legacy) | 299 / 399 / 599 / 1 099 zł by online bookings; price frozen on move | not published | not published | not published | free, ≤ 48 h |
| kluby.org | BASIC 50 zł (≤ 30 bookings); PRO 79–599 zł by courts | none per booking | 2 % of online · club | monthly notice · 60 days | not published |
| Twój Tenis | not published | free; ≤ 2,5 % kept on late-payment refunds | not published · Tpay | not published | moving clubs to a new platform |
| PADO | — | none | 2 % per booking, club may pass it on | not published | not published |
| Playtomic Manager | 4 plans, no prices | PL: 20 % of an open-match seat (1,24–3,99 zł), 0 on private bookings, 4,32 zł to cancel | per contract (example 3,5 %), includes processing | monthly or yearly, cancel ≥ 30 days before · 2 weeks | not published |
| MATCHi | monthly platform fee, amount not published | 4 % in 8 markets, not Poland | fixed or % per contract | not published | not published |
| Padel Mates | "From 0 SEK" | "No subscription for players" | "Clubs only pay when they earn", rate not published | not published | "We migrate … in days" |
| Eversports Manager | €99 / 149 / 199 by courts (yearly); €113 / 166 / 221 monthly | none found | per contract + surcharge | yearly saves ≤ 17 % · setup €199 | not published |
| CourtReserve | $199 / 369 / 549 by courts ($159 / 329 / 499 yearly) | club may add ≤ 4 % | processor's rate · club or player | subscription; branded app 1 year + $499 | not published |
| ClubSpark | free to LTA venues; else not published | none found | not published | — | — |
| Rakieta today | 0 | 0 | 0 · club pays Stripe 1,5 % + 1 zł per charge | — | — |

## 8. Gaps

- **What tenis4U clubs actually sign:** contract length, notice, any commission or minimum term — the only
  question that decides how hard it is to take a tenis4U club. Ask a real club.
- **Real occupancy by hour** at any Kraków or Polish club; the marginal cost of a filled hour (light, heat).
  Ask a real club; the Global Padel Report 2026 ("Club Economics") was not read because it is form-gated.
- **Playtomic's, MATCHi's and Padel Mates' actual rates** — unpublished; only rival vendors' claims exist.
- **Twój Tenis's club price** and the terms of its new platform.
- **Whether migrated Reservise clubs pay Playmore's 1,79 %**, and how many Kraków clubs are still on Reservise.
- **Playmore open-game volumes**: no count of games made or filled.
- **Playmore's player service fee schedule** beyond 1,48 zł at two Kraków clubs ("dynamicznie").
- **DAC7 for court hire:** no KAS interpretation found on whether "udostępnienie części nieruchomości" covers
  hourly court bookings, or whether white-label booking software used by one club is a "platforma";
  MATCHi reads it the other way. Needs a tax adviser or an interpretacja indywidualna.
- **Stripe and KSeF:** no Stripe document; a third-party app (Fakturownia) is the only path found.
- **Playtomic's plans for Poland**: nothing public.
