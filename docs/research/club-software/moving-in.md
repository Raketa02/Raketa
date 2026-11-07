# Moving a club in — what it can take out, how rivals bring it across, and the law

Research for area 16 (moving in) and the market side of area 18 (moving today's Raketa clubs to the full calendar) of
the planning map *Raketa becomes the club's booking software* (decided 2026-10-12: one calendar for desk, phone,
walk-ins, season bookings, online bookings and the Games deck, replacing tenis4U, Playmore and kluby.org).

**Extends** [`integration.md`](integration.md),
[`season-bookings-and-blocks.md`](season-bookings-and-blocks.md) and, in `../games-and-fill-in/`,
[`topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) (§2 Onboarding, §11 Leaving, §12 What
clubs say), [`topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`areas/CLUBSETUP.md`](../games-and-fill-in/areas/CLUBSETUP.md),
[`topics/gaps-CLUBSETUP.md`](../games-and-fill-in/topics/gaps-CLUBSETUP.md),
[`topics/gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md) and
[`../games-and-fill-in-market.md`](../games-and-fill-in-market.md) (S02-G9). Facts carried from there keep their
dates; everything else was read **2026-10-12**.

**This file decides nothing.** Each block below is for the club-software grilling to mark *Build at launch · Build
later · Leave out · Ask a real club*. Nothing here estimates Raketa's build cost.

**Sources.** tenis4U's club-side text comes from the JavaScript its public demo panel serves to every visitor
([test-panel.tenis4u.pl](https://test-panel.tenis4u.pl/), bundle `main.2b865c996e568707.js`; every string quoted
below is also in the production panel's login bundle), its player side from
[app.tenis4u.pl](https://app.tenis4u.pl/) (`main.cf446af5e9523413.js`). Playmore's player-app text is from
[playmore.pl/assets/BIIU90LQ.js](https://playmore.pl/assets/BIIU90LQ.js); its club terms from the page data of
[playmore.pl/legal/partner-terms](https://playmore.pl/legal/partner-terms)
([`Cw-tKkmq.js`](https://playmore.pl/assets/Cw-tKkmq.js), last updated 15.08.2025). Twój Tenis's text is from
[twojtenis.pl](https://twojtenis.pl/)'s bundle (`index-Bf6nIpMv.js`). Playtomic and MATCHi help was read through their
public Zendesk APIs; Playtomic's API reference at [third-party.playtomic.io](https://third-party.playtomic.io/). The
GDPR was read on EUR-Lex's Publications Office copy, Polish law on api.sejm.gov.pl. Nobody signed in, booked or paid,
and no endpoint that writes was called.

**Kinds:** `[POLICY]` the company's or club's own rule, term, help or interface text · `[PRICE]` a published price ·
`[DOCS]` a provider's or regulator's document · `[LAW]` a statute · `[COMPLAINT]` one party's account · `[ABSENT]`
looked for and not found, with where. Lines marked *reading* are inferences, not sources.

**A word on tenis4U's words** (from [`season-bookings-and-blocks.md`](season-bookings-and-blocks.md)): in its code a
*court* ("kort") is the **club** and a *station* is the court. "Users of the court" below are the club's customers.

## Read this first

- **A tenis4U club can take out one list: name, email and phone.** The users card's only download, "Pobierz jako
  CSV", writes `users.csv` with three columns. Bookings come out only as a report for at most 60 days, with both
  dates capped at today; fixed bookings ("Rezerwacje stałe") and passes ("Karnety") have no download. *Reading:* a
  tenis4U club's future and season bookings must be re-typed or copied by someone.
- **In every Polish system the player's login belongs to the platform, the booking data to the club.** tenis4U,
  Playmore and kluby.org each say the club becomes the controller of what a player books there, while the account
  stays theirs. The login cannot move; the club's record of the person can.
- **Playmore moves a club with people, free, in one to two weeks:** "Najpierw sprawdzamy eksport i mapujemy
  klientów, cenniki oraz rezerwacje cykliczne" (first we check the export and map customers, price lists and
  recurring bookings). For its own Reservise clubs it moves "Rezerwacje, bazę klientów, cennik i całą historię".
- **Nobody moves saved cards.** Eversports: "Credit card details cannot be transferred." Stripe imports card numbers
  only from another processor, on a request, in "a few days or several weeks" plus about 10 business days. Nothing
  was found on Przelewy24 or Tpay releasing card references.
- **Prepaid value moves as a typed-in final balance.** Playtomic imports wallet balances from a CSV that "will
  overwrite the customer's existing wallet balance"; Eversports re-assigns passes by hand and warns about "deducting
  units twice". No rival moves the transaction history behind a balance.
- **The switch is a date, not a sync.** Twój Tenis is moving Kraków clubs one by one, each with "najwcześniejszy
  dzień, na który można robić rezerwacje" (the earliest day bookable in the new system); a UK club froze its old
  site for one day and carried over everything booked before; a sports centre stopped the old system taking bookings
  past the switch date. Running both systems is advised only where the second one is capped.
- **Players are brought across by a key they already have.** Polish vendors use the phone: Playmore merges an old
  account after an SMS code ("Masz konto w klubie na ten numer?"), Twój Tenis asks for "numeru telefonu używanego w
  starej wersji". MATCHi and Playtomic use the email. tenis4U activates every account with an SMS code to a 9-digit
  number.
- **The law lets consents survive a change of processor, not a lack of proof.** Processors "do not need to be named
  as part of the consent requirements" (EDPB), but the club must "demonstrate that the data subject has consented"
  (GDPR art. 7(1)), and marketing by email or SMS needs prior consent (PKE art. 398). tenis4U's export carries no
  consent flag; Playtomic's does.
- **Leaving is a month's notice in Poland.** Playmore: monthly plans, renew unless cancelled 14 days before the end,
  and ending the contract deletes the club's account, so data must be asked for first. kluby.org: a month. tenis4U
  publishes no club contract.
- **No complaint of double bookings during a switch was found**, in English or Polish.
- *Reading* for area 18: vendors that moved their own clubs to a new product ran both products side by side, club
  by club, and kept money already paid under the old rules (Playtomic: a booking "can still belong to the old model
  if the payment was made before migration").

## Corrections to earlier files

- [`integration.md`](integration.md) §1 says Padel Mates took **Rocket Padel** and Racket Club from Playtomic and
  MATCHi, citing padelalto. **[POLICY]** That article names only **Racket Club** (seven Danish venues): "In February
  2025, we will switch our booking platform from Matchi to Padel Mates"
  ([padelalto, 2024-11-21](https://padelalto.com/2024/11/21/danish-padel-operator-switches-from-matchi-to-swedish-platform)).
  The Padel Mates move from Playtomic is **Padium** (UK), "this summer", in July 2025
  ([The Bandeja, 2025-05-22](https://thebandeja.com/padium-drops-playtomic-for-padel-mates/)). **[ABSENT]** where
  Rocket Padel went: the Padel Paper says only that it "veered away" from Playtomic
  ([2025-12-11](https://thepadelpaper.com/playtomic-soul-padel-data/)).
- [`gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md) lists Tpay and Przelewy24 statements among tenis4U's
  club exports. *Reading:* that form uploads a statement file and sits among tenis4U's own admin tabs (`isCallCenter`,
  `notProd`), so it may not be the club's.

---

## A. Taking the club's data out of the old system

**What it covers.** What a club can download itself before it switches: customers, past and future bookings, fixed
bookings, prices, prepaid balances and consents.

**Who has it**
- **[POLICY] tenis4U**
  ([demo panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)):
  - The "Użytkownicy" card has one button, "Pobierz jako CSV". It writes `users.csv` with the header "Imię i
    nazwisko,Email,Telefon" (full name, email, phone), taken from the rows on screen after any search. Fields are
    joined with commas and not quoted.
  - "Generuj raport" between "Początek okresu" and "Koniec okresu" (start and end of period) downloads
    `raport <timestamp>.csv` from `/panel/report/reservations/{club}/{from}/{to}`. It is refused over 60 days ("Długość
    okresu nie może przekroczyć 60 dni"), and both date fields have `max` set to today.
  - The day's calendar saves as `Tenis4u-DD-MM-YYYY.pdf`, drawn with html2canvas as a JPEG picture.
  - "Rezerwacje stałe" (fixed bookings) and "Karnety" (passes, with "Historia użycia karnetu") have no download.
  - *Reading:* future and fixed bookings have no way out in the panel, the report's columns are made on the server and
    were not seen, and the PDF is a picture, not data.
- **[POLICY] Playmore / Reservise.** The club panel is not public. The club page sells "Raport zintegrowany zbiera
  wszystkie płatności miesiąca w jednym pliku Excel" (one Excel file per month of payments)
  ([join.playmore.pl](https://join.playmore.pl/)). A player can export their own data from Account → "Eksport danych"
  (route `/account/data-export`) ([bundle](https://playmore.pl/assets/BIIU90LQ.js)). **[ABSENT]** What a club can
  download itself, or what Playmore hands over when a club leaves.
- **[POLICY] kluby.org changelog:**
  - "Eksport do excela grup, uczestników" (groups and participants, 1 January 2020)
    ([2020](https://oferta.kluby.org/changelog?rok=2020)).
  - "Eksport historii rezerwacji do Excela" (booking history, 1 April 2021) and "Pobieranie płatności klienta do
    Excela" (a customer's payments, 1 July 2021) ([2021](https://oferta.kluby.org/changelog?rok=2021)).
  - Daily summary, accounting report, payouts report and "podsumowania grafiku" (schedule summary) to Excel (2022)
    ([2022](https://oferta.kluby.org/changelog?rok=2022)).
  - "Nowy mechanizm backupu danych" (new backup, 1 January 2023) ([2023](https://oferta.kluby.org/changelog?rok=2023));
    "Backup danych" on [funkcje](https://oferta.kluby.org/funkcje); help "9.10. Kopia zapasowa" is a video only
    ([pomoc](https://oferta.kluby.org/pomoc)).
  - **[ABSENT]** An export of the customer list: no such entry in the 2016–2026 changelogs (searched "eksport",
    "excel", "klient", "import").
- **[POLICY] Twój Tenis** (old platform): club accounts offer "zapis do plików xls" (saving to xls files)
  ([old.twojtenis.pl](https://old.twojtenis.pl/)). **[ABSENT]** Exports on its new platform.
- **[POLICY] Playtomic Manager:**
  - Customers → "Export List of Customers in CSV", after "Accept and Export". It holds name, email, Playtomic ID,
    "Whether the player accepted commercial communications", category and its expiry, birthday, phone, gender, and
    "the balance of each wallet and the total balance"
    ([export a user list, updated 2026-08-18](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)).
  - The booking list, recurring bookings included, filters by creation or **service** date and exports JSONL or CSV
    ([Booking List, 2026-09-12](https://helpmanager.playtomic.com/hc/en-gb/articles/20534162168337)); payments export as
    CSV (carried, 2026-10-07).
- **[DOCS] Playtomic Club API**, read-only, Champion and Master plans:
  - Range: "the past 90 days plus all future bookings", at most 365 days a request, "typically 1 call per minute"
    ([guide, 2026-08-17](https://helpmanager.playtomic.com/hc/en-gb/articles/38836515997073)).
  - Bookings carry court, start and end, `origin` (app, manager, recurring configuration…), price, `payment_status`,
    and `booking_type` including `RECURRING_BOOKING`
    ([bookings](https://third-party.playtomic.io/endpoints/bookings/)).
  - Players carry name, email, phone, birth date, `accepts_commercial_communications` ("explicitly accepted to receive
    marketing communications from the venue"), sports levels, benefits and wallets
    ([players](https://third-party.playtomic.io/endpoints/players/)).
  - Playtomic may "discontinue the API entirely with prior notice of one month"
    ([home](https://third-party.playtomic.io/)).
- **[POLICY] MATCHi:**
  - Customers → Choose action → Export "to an Excel file (Complete, IdrottOnline, or NIF format)", made in the
    background ([Choose action, 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/11696109139613)).
  - Schedule → More → "export your reservations"
    ([Schedule, 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/11467301471901)).
  - Statistics exports booking data as `.xls` and revenue data
    ([Statistics, 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)).

**The desk/owner's day with it.** At Playtomic and MATCHi a few clicks give customers, bookings by service date and
money. At tenis4U one click gives the customer list; bookings come only in past 60-day slices, and the season's fixed
bookings have to be read off the screen.

**What a Kraków desk does today.** Padel and tennis desks keep customers, fixed bookings and passes in tenis4U; squash
desks in Playmore or old Reservise ([`integration.md`](integration.md) §4). *Reading:* the only complete list a tenis4U
club can carry out is who its customers are and how to reach them.

**What it means for the player app.** *Reading:* a player's past games at a tenis4U club will not arrive with them, so
their history at that club in Raketa starts on the switch day.

**Market signal.** Playtomic and MATCHi give a club the most to take away, tenis4U the least. Playmore keeps its club
panel private and does migrations with its own staff.

## B. Importing the club's customers

**What it covers.** Loading the club's list of people into the new system before any of them signs up.

**Who has it**
- **[POLICY] Playtomic:**
  - Customers → Imports → "Import new customers", from a CSV with "name\*", "email\*", "phone_number" (with the
    club's country prefix), gender, birthdate and optional benefit columns. The club must "Confirm you have
    permission to import the customer data", and rows with errors can be downloaded. A chain imports once for all its
    clubs ([import users, 2026-05-13](https://helpmanager.playtomic.com/hc/en-gb/articles/20535597078417)).
  - An imported or hand-added person is a club record: "The details you enter here belong to your club's own customer
    record. If this person later turns out to have a Playtomic account, your entry won't need to match theirs"
    ([Customers, 2026-09-18](https://helpmanager.playtomic.com/hc/en-gb/articles/20535413988113)).
- **[POLICY] MATCHi:** customers come "in bulk from an Excel (XLSX) file", one venue at a time; "After import, the
  system automatically checks each imported customer to see if they match an existing MATCHi account, and links them
  if so"; "there's no uniqueness check on email"
  ([Customers, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11678704771613)).
- **[POLICY] Eversports:** the club fills in a template and "we'll take care of the import within 2–3 business days".
  A "Newsletter" column takes 1 or 0 so "only customers who have provided consent receive communications", and "Your
  customers will not receive any notifications during the import process"
  ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
- **[POLICY] CourtReserve:** "the CourtReserve Onboarding team manages the import process for new clubs" from an Excel
  template, after a 3–5 row sample. "We're unable to import members until your CourtReserve subscription is active",
  and "each organization is allowed a single member import"
  ([member list import](https://help.courtreserve.com/en/articles/4051118-member-list-import)).
- **[POLICY] Playmore:** "mapujemy klientów" (we map the customers), by its own staff
  ([join.playmore.pl](https://join.playmore.pl/)).
- **[ABSENT]** A customer import in tenis4U's panel (no "import" string in the demo bundle) or in kluby.org's
  changelogs 2016–2026.

**The desk/owner's day with it.** The owner fills in or hands over one spreadsheet. Where the vendor runs the import,
the owner waits two or three days and checks a sample first.

**What a Kraków desk does today.** *Reading:* a tenis4U club's `users.csv` already fits Playtomic's two required
columns and the phone column. It has no birth date, gender or consent, and the whole name sits in one column.

**What it means for the player app.** An imported customer is the club's record, not a player account. It turns into
a linked player only through block I.

**Market signal.** Every rival imports customers from a file. Eversports, CourtReserve and Playmore do it for the
club; Playtomic and MATCHi let the club upload it. Consent travels as a column at Eversports and Playtomic.

## C. Importing future bookings and season (fixed) bookings

**What it covers.** Bringing across bookings already sold for dates after the switch: one-offs and a season's weekly
series.

**Who has it**
- **[POLICY] Playmore:** for Reservise clubs, "Rezerwacje, bazę klientów, cennik i całą historię przenosimy do
  Playmore — robi to nasz zespół, za Ciebie" (we move bookings, customer base, price list and all history; our team
  does it for you) ([join.playmore.pl/reservise](https://join.playmore.pl/reservise/)). From other systems it maps
  "rezerwacje cykliczne" (recurring bookings) ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] Eversports**, from another vendor:
  - "Bookings are not transferred automatically as part of the migration process." The club recreates them, or asks
    customers "to book their classes or appointments again through Eversports from a specified date onwards"
    ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
  - From its own acquired product USC, a tool moves them: "Future bookings of your USC customers will also be
    transferred"; "The migration can only be done once"
    ([USC migration](https://helpcenter.eversportsmanager.com/how-can-i-migrate-my-data-from-the-usc-to-eversports)).
- **[POLICY] MATCHi:** a season's subscriptions can be imported from Excel, with a conflict check that can "overwrite
  the conflicting bookings" (carried from [`season-bookings-and-blocks.md`](season-bookings-and-blocks.md) §4,
  [Subscriptions](https://matchi.zendesk.com/hc/en-gb/articles/11467454905373)).
- **[POLICY] Playtomic:**
  - Recurring series are typed into the Schedule by hand. Players see them "as long as the email matches their profile
    in the Playtomic app" ([Recurring series, 2026-06-22](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513)).
  - **[ABSENT]** An import of bookings (club help searched for "import bookings", "import reservations", "recurring
    booking", "previous software").
- **[POLICY] A club's own switch:** Magdalen Park LTC told members "We'll be migrating any court bookings (from the
  current site to ClubSpark) made between now and 5pm Saturday 31st August"
  ([notice](https://clubspark.lta.org.uk/mpltc/News/f675209a-8451-49f4-8092-592fc38bb5bb); the page is dated 10 May
  2020 and the year of the switch is not given).
- **[POLICY] Twój Tenis:** bookings follow a player to the new platform by phone number (block I).

**The desk/owner's day with it.** *Reading* (carried from
[`season-bookings-and-blocks.md`](season-bookings-and-blocks.md) §4): a Kraków desk enters most of its season series in
the season's first week, late September. A club switching in October would re-enter them a second time, or have the
vendor do it.

**What a Kraków desk does today.** **[POLICY]** tenis4U keeps fixed bookings in "Rezerwacje stałe", with a cut-off of
their own ("Na ile godzin przed rozpoczęciem można anulować rezerwację stałą"), and offers no download of them
([demo panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). Fame Sport sells "stałe rezerwacje
kortów na okres 12 tygodni, sezon letni, sezon zimowy" paid up front (carried, 2026-10-06).

**What it means for the player app.** *Reading:* a player whose Tuesday 19:00 slot is missing in Raketa on day one
will think it was sold. The slot has to land under the account they will claim (block I).

**Market signal.** Vendors that own both ends (Playmore from Reservise, Eversports from USC, Twój Tenis old to new)
move future bookings. From a rival's system they either ask players to rebook from a date (Eversports) or have their
own staff type them in (Playmore).

## D. Importing prices, courts and rules

**What it covers.** The courts, opening hours, price list and booking rules the new system must hold before it sells.

**Who has it**
- **[POLICY] Playmore:** "Opiekun ustawia system pod zasady i grafik Twojego klubu i przenosi dane z obecnego
  systemu" (a named adviser sets the system to the club's rules and schedule and moves the data)
  ([cennik](https://join.playmore.pl/cennik/)); "Mapujemy dane, ustawiamy zasady klubu i przechodzimy prawdziwą
  płatność, zwrot oraz wyjątki" (we map the data, set the rules and walk through a real payment, a refund and the
  exceptions) ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] Playtomic:** the club enters "Courts and Prices" and the other go-live items; an onboarding coordinator
  then "will make your club visible" (carried, [Go live, 2026-09-17](https://helpmanager.playtomic.com/hc/en-gb/articles/20535378377745)).
- **[POLICY] MATCHi:** the club watches "10 short video guides" before an onboarding call, which covers "your venue's
  specific setup"; "MATCHi provisions your MATCHi Admin and Backhandsmash admin credentials"
  ([Onboarding, 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/32609893008413)).
- **[ABSENT]** A price-list import file at any rival (Playtomic, MATCHi, Eversports, CourtReserve help searched).

**The desk/owner's day with it.** The price grid, courts and rules are entered once, by the owner or the vendor's
person, and checked with a real payment.

**What a Kraków desk does today.** Its prices and rules sit in the tenis4U panel per court and time
([`integration.md`](integration.md) §5).

**What it means for the player app.** Nothing new.

**Market signal.** Configuration is set up by hand everywhere, usually with the vendor's person on a call.

## E. Carrying prepaid value: passes, wallets, vouchers

**What it covers.** Money players have already paid the club and not yet used: passes ("karnety"), wallet credit,
vouchers, memberships.

**Who has it**
- **[POLICY] Playtomic:** "Import balance" takes a CSV of email, wallet name, `wallet_balance` and an optional
  expiry, after the club confirms "you have the customer's permission to import financial data". "The value in
  wallet_balance will overwrite the customer's existing wallet balance", and "negative balances can't be imported"
  ([import Club Wallets, 2026-09-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20535575911825)).
- **[POLICY] Eversports:**
  - Block and time cards "need to be assigned manually", with remaining units adjusted "to avoid deducting units
    twice".
  - Vouchers already sold are re-sold at 0 €.
  - Memberships assigned by hand "cannot be cancelled online by customers"
    ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
- **[POLICY] Playmore:** when a player's old account is merged, the summary lists "Karnety", "Płatności" and "Saldo
  portfela zostało przeniesione" (the wallet balance was moved) ([bundle](https://playmore.pl/assets/BIIU90LQ.js)).
- **[ABSENT]** An export of pass balances in tenis4U's panel ("Karnety", "Obciąż karnet", "Historia użycia
  karnetu", no download) or in kluby.org's changelogs (passes and subscriptions exist since 2018).

**The desk/owner's day with it.** The owner lists who holds how much and types it in as an opening balance.

**What a Kraków desk does today.** **[POLICY]** tenis4U sells passes at the desk and online; online needs the club's
payment operator: "Dodanie karnetu wymaga aktywacji konta u operatora płatności"
([demo panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). Squash4You keeps an online payment
cancelled in time as credit for the next booking (carried in
[`booking-directly-and-games-in-one-calendar.md`](booking-directly-and-games-in-one-calendar.md)).

**What it means for the player app.** *Reading:* a player holding a 10-entry pass expects the remaining entries to be
there after the switch, and the club owes them either way.

**Market signal.** Balances move as one number per person per wallet, never with their history. Eversports names the
risk of charging the same entry twice.

## F. Saved cards and other payment methods

**What it covers.** Whether a player's saved card, or a token for it, can move from the old processor to Stripe.

**Who has it**
- **[POLICY] Eversports:** "Credit card details cannot be transferred." SEPA mandates move only if the old software
  can export the bank details
  ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
- **[DOCS] Stripe, importing card data from another processor**
  ([PAN import](https://docs.stripe.com/get-started/data-migrations/pan-import)):
  - The merchant must "complete a Data migration request", and "Many processors require the account owner to request
    a data transfer".
  - "Your previous processor might take a few days or several weeks to transfer the final data to Stripe"; then
    "Stripe typically imports data within 10 business days".
  - Meanwhile the merchant can "continue charging your existing customers with your current processor until the
    migration is complete".
  - Stripe helps "only if your request includes both customer records and the associated payment data"
    ([overview](https://docs.stripe.com/get-started/data-migrations)), and answers a request "within the next three
    business days" ([support](https://support.stripe.com/questions/request-a-data-migration)).
- **[DOCS] Stripe, exporting:** only "to another PCI DSS Level 1-compliant payment processor" with an Attestation of
  Compliance; "You can't transfer the payment credentials saved with Link"
  ([PAN export](https://docs.stripe.com/get-started/data-migrations/pan-export)).
- **[ABSENT]** Anything in Stripe's migration pages about importing into a Connect connected account.
- **[DOCS] Przelewy24:** saved cards are charged by a reference (`refId`/`methodRefId`). Sending card numbers directly
  means "The Merchant must hold PCI DSS certification"
  ([API reference](https://developers.przelewy24.pl/), `en_documentation_1.0.yaml`).
- **[ABSENT]** A card-reference export or migration at Przelewy24 (API reference searched for "export", "migrat")
  or at Tpay ([tokenization](https://docs-api.tpay.com/en/tokenization/)).

**The desk/owner's day with it.** Nothing to do. The player adds a card or pays by BLIK at their first booking.

**What a Kraków desk does today.** **[POLICY]** tenis4U clubs take payments on their own Przelewy24 keys, and players
pay by Przelewy24 or Tpay (carried, [`integration.md`](integration.md) §5). The "karta" strings in tenis4U's player app
are Medicover cards ("Karty Medicover zostały zarejestrowane"); no saved payment card was seen
([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)).

**What it means for the player app.** *Reading:* every migrated player meets Raketa's card or BLIK step at their first
payment, as a new player does.

**Market signal.** Card portability exists only between big processors under PCI. No court-booking rival offers it.

## G. A person who does the move

**What it covers.** Whether the vendor's staff carry out the switch, what it costs and how long it takes.

**Who has it**
- **[PRICE]** **[POLICY] Playmore:** "Wdrożenie i przeniesienie danych: 0 zł"; "Wdrożenie trwa 1–2 tygodnie";
  "Nie dostajesz loginu i instrukcji. Przechodzimy zmianę razem" (you don't get a login and a manual; we make the
  change together) ([join.playmore.pl](https://join.playmore.pl/), [cennik](https://join.playmore.pl/cennik/)). For
  Reservise clubs: a 45-minute call, "Migrację poprowadzi Klaudiusz z naszego zespołu", in three steps: a meeting, "Przenosimy
  Twoje dane", "Sprawdzamy i działasz dalej" ([reservise](https://join.playmore.pl/reservise/)).
- **[POLICY] Playtomic:** a form, a demo, a single-use code, the checklist, then a coordinator makes the club visible
  and provides "materials to help communicate with players" (carried,
  [Go live](https://helpmanager.playtomic.com/hc/en-gb/articles/20535378377745)).
- **[POLICY] MATCHi:** videos, then an onboarding call (block D).
- **[POLICY] CourtReserve:** its onboarding team runs the member import (block B).
- **[POLICY] Eversports:** its staff import customers within 2–3 business days (block B).
- **[POLICY]** Outside sport, Zenamu (studios): "We'll move your client data over for free"
  ([migration](https://zenamu.com/booking-system-migration)).
- **[ABSENT]** How tenis4U onboards a club beyond the "Dodaj korty" form ([tenis4u.pl/dodaj](https://tenis4u.pl/dodaj/)).

**The desk/owner's day with it.** One call, one to two weeks, a test payment, staff training.

**What a Kraków desk does today.** It came on to tenis4U or Playmore the same way: a form or a demo, then the vendor's
setup (carried, [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) §2).

**What it means for the player app.** Nothing new.

**Market signal.** A free, staffed migration is standard, and Playmore sells it as a reason to switch.

## H. The switch: a freeze, a date, or both systems running

**What it covers.** How a club stops selling in one system and starts in the other without selling an hour twice.

**Who has it**
- **[POLICY] Twój Tenis** (Kraków), moving its own clubs from the old platform to a new one:
  - "W najbliższych tygodniach będziemy migrować kolejne kluby na nową platformę" (in the coming weeks we will
    move more clubs to the new platform), and "Daty przy klubach wskazują na najwcześniejszy dzień, na który można
    robić rezerwacje" (the dates by the clubs are the earliest day bookable).
  - Kraków dates include Błonia Sport 23.04.2026, WKS Wawel 27.04.2026, Centrum Sportowe Czyżyny 01.05.2026, Korty
    Dąbskie 06.07.2026 and Soldi (Niepołomice) 01.10.2026 ([twojtenis.pl](https://twojtenis.pl/)).
- **[POLICY] Aberdeen Sports Village:** from 23 June "it will not be possible to book any further ahead than 1 July
  2022", the switch day; members "will have to re-register/verify themselves via a new online system"
  ([notice, 2022-06-24](https://abdn.ac.uk/staffnet/news/16130)).
- **[POLICY] Magdalen Park LTC:** bookings made up to 5pm Saturday 31 August are migrated; "we ask that you do not
  make any bookings on the current website on Sunday 1 September"; the new site opens Monday 2 September
  ([notice](https://clubspark.lta.org.uk/mpltc/News/f675209a-8451-49f4-8092-592fc38bb5bb)).
- **[POLICY] Laguna Woods Village:** "European-based Playtomic … acquired Kourts" and "the new platform will no
  longer work with our online reservation system"; Kourts ends 30 June, Court Reserve from 1 July; "Residents will
  be entered into the Court Reserve system" ([notice, 2022-06-24](https://lagunawoodsvillage.com/?p=15154)).
- **[POLICY] Eversports:**
  - "We recommend switching at the beginning of the week rather than on weekends."
  - Once passes are moved, "bookings should no longer be accepted through your previous platform".
  - Running both is offered only for aggregator traffic: "Allow aggregator bookings through Eversports while
    continuing to use your previous software", limiting "the number of places available to aggregators"
    ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
- **[POLICY] Zenamu:** "For 1–2 weeks, keep both systems running"
  ([migration](https://zenamu.com/booking-system-migration)).
- **[POLICY] Playmore:** "klub działa normalnie przez cały czas" (the club works normally throughout); "Twoi klienci
  nie odczują przerwy w działaniu" ([reservise](https://join.playmore.pl/reservise/)).
- **[ABSENT]** A first-hand complaint of a double booking during a club's switch. Searched in English and Polish
  ("new booking system" "double bookings", "nowy system rezerwacji" "stary system"), and the Playmore App Store PL
  reviews, none of which mentions the Reservise change
  ([App Store](https://apps.apple.com/pl/app/reservise-playmore/id928403015)).

**The desk/owner's day with it.** *Reading:* the safest pattern seen is to stop the old system taking bookings past
the switch date, carry over what it already holds, and freeze for a day. Running two calendars for one to two weeks
means the desk closes every sale in both.

**What a Kraków desk does today.** *Reading:* desk, phone and app write into one tenis4U calendar
([`integration.md`](integration.md) §5), so all three doors have to move on the same day.

**What it means for the player app.** *Reading:* there is a date from which the club's hours are bookable in Raketa;
before it the player books in the old app. Twój Tenis shows that date beside each club.

**Market signal.** A hard date, with the old system's booking horizon cut at that date, is the common pattern. Nobody
advises two open calendars for the same courts.

## I. Bringing the club's players into the new app

**What it covers.** How a player who books at the club through the old app gets an account in the new one with
their bookings and passes already there.

**Who has it**
- **[POLICY] Playmore**, phone first ([bundle](https://playmore.pl/assets/BIIU90LQ.js)):
  - At checkout: "Masz konto w klubie na ten numer? Potwierdź numer kodem SMS, a połączymy Twoją historię i
    karnety" (have an account at the club on this number? Confirm it by SMS and we will join your history and
    passes).
  - In the lists: "Nie widzisz swoich rezerwacji? … Potwierdź numer telefonu, który podajesz w klubie. Jeśli masz
    już u nas konto, połączymy je i zobaczysz swoje rezerwacje, karnety i zajęcia".
  - After a merge: "Twoje konta zostały połączone", listing "Profile w obiektach", "Rezerwacje", "Karnety",
    "Płatności", "Poziomy sportowe" and "Saldo portfela zostało przeniesione".
  - Conflicts: "Ten numer jest przypisany do innego konta"; "Znaleźliśmy Twoje starsze konto … Możesz połączyć je z
    obecnym logowaniem albo przenieść tu sam numer".
  - Login is by phone, with the code sent to the account's email or by SMS.
- **[POLICY] Twój Tenis:** "Wymagane założenie nowego konta (login i hasło) oraz podanie numeru telefonu używanego w
  starej wersji w celu poprawnej migracji rezerwacji" (a new account is needed, with the phone number used in the
  old version, so the bookings migrate correctly) ([twojtenis.pl](https://twojtenis.pl/)).
- **[POLICY] MATCHi:**
  - Invite one customer or many; the email subject is "Invited to {facility}'s online booking". "Customers without
    an email address are silently skipped"
    ([Invite customer, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11697240164125)).
  - A new customer record links itself when "there is an existing MATCHi user with a matching email and name"
    ([Add customer](https://matchi.zendesk.com/hc/en-gb/articles/11697146259613)). Once linked anywhere, other venues'
    records are "matched by email, first name, and last name".
- **[POLICY] Playtomic:**
  - Matches by email. "Playtomic treats each login method as a separate account", so one person can appear twice
    ([Customers: common issues, 2026-09-26](https://helpmanager.playtomic.com/hc/en-gb/articles/46345235970833)).
  - The player's own details show to the club "only once the player accepts your club's Terms & Conditions".
- **[POLICY] Eversports:** "you will need to invite them to create or connect their Eversports accounts",
  "individually, per customer groups or all together"
  ([switching guide](https://helpcenter.eversportsmanager.com/switching-to-eversports-your-step-by-step-migration-guide)).
- **[POLICY] CourtReserve:** "the Welcome Email is not sent automatically during the import process"; staff send it
  ([member import](https://help.courtreserve.com/en/articles/4051118-member-list-import)).
- **[POLICY] kluby.org:** "Możliwość zaproszenia klienta do rezerwacji ONLINE" (invite a customer to book online, 1
  December 2018) ([2018](https://oferta.kluby.org/changelog?rok=2018)); "Możliwość wysyłania wiadomości SMS z
  zaproszeniem do rezerwacji ONLINE przez pracownika" (staff send the invitation by SMS, 1 May 2019)
  ([2019](https://oferta.kluby.org/changelog?rok=2019)).
- **[POLICY] tenis4U**, the player's side: an account needs "Numer telefonu (9 cyfr)" and "Kod SMS jest wymagany do
  aktywowania konta" ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)). **[ABSENT]** An invite to
  players in the club panel (demo bundle searched "zapro", "invite").

**The desk/owner's day with it.** The owner sends one invitation (email or SMS) to the whole list. The desk answers
"where is my booking?" by asking for the phone number.

**What a Kraków desk does today.** *Reading:* desks know players by phone, and every tenis4U app user has a phone
number verified by SMS, so the phone is the key a Kraków club's list already holds.

**What it means for the player app.** *Reading:* a player claims the club's record of them by confirming the same
phone number with an SMS code, with email as a second key. Bookings and passes then appear without retyping; a
conflict ("this number belongs to another account") needs its own screen.

**Market signal.** Polish vendors key on the phone (Playmore, Twój Tenis, tenis4U's SMS check); MATCHi, Playtomic and
Eversports key on the email. Nobody moves a login or a password.

## J. The law on moving the club's customer data

**What it covers.** Who owns the list, what contract the switch needs, whether marketing consents survive it, and
what customers must be told.

**Who has it**
- **[POLICY] The club is the controller of booking data; the platform keeps its own users.**
  - Playmore's club terms (Załącznik nr 1): "Administratorem … danych osobowych Użytkowników, którzy dokonali
    Rezerwacji … – jesteś Ty, jako Partner"; "W zakresie w jakim Ty nie administrujesz danymi Użytkowników,
    administratorem danych osobowych jest Reservise". The data entrusted are "imię, nazwisko, numer telefonu, adres
    e-mail" ([partner terms](https://playmore.pl/legal/partner-terms)).
  - tenis4U: at a booking, name, phone, payment data and email "przekazywane są klubowi i staje się on
    administratorem", while PC Company Sp. z o.o. is controller of the account. "W każdym obiekcie posiadasz osobny
    profil" (a separate profile at each club) ([privacy](https://tenis4u.pl/privacypolicy/)).
  - kluby.org: "Klub staje się wówczas administratorem danych osobowych Użytkownika" (regulamin in force from 14 March
    2025) ([regulamin](https://kluby.org/regulamin)).
- **[LAW] GDPR art. 28** ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)):
  - The controller "shall use only processors providing sufficient guarantees" (28(1)).
  - Processing "shall be governed by a contract", which must make the processor, "at the choice of the controller,
    deletes or returns all the personal data to the controller after the end of the provision of services" (28(3)(g)).
  - "if a processor infringes this Regulation by determining the purposes and means of processing, the processor
    shall be considered to be a controller in respect of that processing" (28(10)).
- **[DOCS] UODO** fined the Sułkowice culture centre 2,5 tys. zł for "powierzenie przetwarzania danych osobowych bez
  zawartej na piśmie umowy powierzenia" (entrusting data without a written contract)
  ([uodo.gov.pl, 2022-09-21](https://uodo.gov.pl/pl/138/2485)).
- **[POLICY] Playmore's contract in practice:** it tells the club of a new sub-processor "na co najmniej 7 (siedem)
  dni roboczych przed" (at least 7 working days before), and silence counts as consent
  ([partner terms](https://playmore.pl/legal/partner-terms)).
- **[LAW]** **[DOCS] Consents:**
  - "the controller shall be able to demonstrate that the data subject has consented" (GDPR art. 7(1)).
  - EDPB: "Processors do not need to be named as part of the consent requirements, although to comply with Articles
    13 and 14 of the GDPR, controllers will need to provide a full list of recipients or categories of recipients
    including processors" ([Guidelines 05/2020, §65](https://www.edpb.europa.eu/system/files/documents/files/file1/edpb_guidelines_202005_consent_en.pdf)).
  - "If the processing operations change or evolve considerably then the original consent is no longer valid" (§110).
- **[LAW] Marketing by email or SMS:** "Zakazane jest używanie … telekomunikacyjnych urządzeń końcowych … do celów
  przesyłania informacji handlowej …, w tym marketingu bezpośredniego, … chyba że uprzednio wyraził on na to zgodę"
  (using terminal equipment to send commercial information, direct marketing included, is forbidden without prior
  consent) (Prawo komunikacji elektronicznej, art. 398(1), in force 10 November 2024)
  ([Dz.U. 2024 poz. 1221](https://api.sejm.gov.pl/eli/acts/DU/2024/1221/text.html)).
- **[POLICY]** Playtomic's export warns the club: "If a player hasn't opted in to receive commercial
  communications, the club shouldn't contact them directly about WhatsApp groups, coaching, promotions, or similar
  activities" ([export a user list](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)).
- **[LAW]** **[DOCS] Telling customers:**
  - The notice names "the recipients or categories of recipients" (GDPR art. 13(1)(e)).
  - Where data were not obtained from the person, the notice is due "at the latest at the time of the first
    communication" (art. 14(3)(b)).
  - Article 29 WP: a change that is "indicative of a fundamental change to the nature of the processing (e.g.
    enlargement of the categories of recipients …)" should be told "well in advance of the change actually taking
    effect", by "an appropriate modality … specifically devoted to those changes (e.g. not together with direct
    marketing content)" ([WP260 rev.01, §29–30](https://ec.europa.eu/newsroom/article29/redirection/document/51025)).
- **[LAW] Portability is the player's right, not the club's:** a person may receive data "which he or she has
  provided to a controller" and "have the personal data transmitted directly from one controller to another, where
  technically feasible" (GDPR art. 20). tenis4U lists "Exportować Twoje dane osobowe" as a request to
  kontakt@tenis4u.pl ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[ABSENT]** UODO guidance on a controller changing processors or migrating a customer list (uodo.gov.pl's search
  answered 500; web search of the site found only the general guidance above).

**The desk/owner's day with it.** *Reading:*
- The owner signs a processing contract (umowa powierzenia) with Raketa and asks the old vendor to return or delete
  the data.
- The privacy notice needs Raketa among its recipients, unless a category such as a booking-system provider already
  covers it.
- Customers get one dedicated message about the change, not mixed with promotion.

**What a Kraków desk does today.** *Reading:* a tenis4U club holds no record of marketing consent: the panel has no
consent field (demo bundle searched "zgod", "marketing", "newsletter"), and `users.csv` carries none. It cannot prove
consent under art. 7(1), so the imported list serves bookings and service messages but not promotion until people opt
in again. A Playtomic club's export carries the flag.

**What it means for the player app.** *Reading:*
- If Raketa used a club's imported list to create Raketa accounts or to market for itself, art. 28(10) would make it a
  controller of that processing.
- Records that stay the club's until the player claims them keep the club as controller.
- Whether an "install the new app" invitation is commercial information under PKE art. 398 is unanswered (see Gaps).

**Market signal.** All three Polish systems already split controller and processor the way Raketa would. Playmore's
contract is the one published model (return or delete, notice before a new sub-processor).

## K. Getting out of the old contract

**What it covers.** Notice periods, minimum terms, what happens to bookings already sold, and to the club's data when
it leaves.

**Who has it**
- **[ABSENT] tenis4U:** no club contract is published (sitemap and "Dodaj korty" page checked again today; carried
  [S02-G9, 2026-10-07](../games-and-fill-in-market.md)). Prices are per month, "netto miesięcznie"
  ([tenis4u.pl](https://tenis4u.pl/)). **[POLICY]** Two companies appear: the privacy policy names PC Company Sp. z
  o.o. (KRS 0000519490) as controller ([privacy](https://tenis4u.pl/privacypolicy/)), the club sign-up form tennis4U
  Sp. z o.o. (KRS 0001010643) ([dodaj](https://tenis4u.pl/dodaj/)).
- **[POLICY] Playmore** ([partner terms](https://playmore.pl/legal/partner-terms), last updated 15.08.2025):
  - **Term:** monthly or yearly; it renews unless either side gives notice "w terminie 14 dni przed upływem Okresu
    Subskrypcji" (§5), and a running period "stanowi zobowiązanie Stron" (binds both sides).
  - **Data at exit:** "Rozwiązanie Umowy jest równoznaczne z usunięciem Twojego Konta z Systemu" (ending the contract
    deletes the club's account) (§5). "zależnie od Twojej decyzji, usuwamy lub zwracamy Ci wszelkie dane osobowe"
    (at the club's choice, we delete or return all personal data) (Załącznik nr 1).
  - **Bookings and money:** carried — leaving over a terms change stops new bookings and "rozliczymy te Rezerwacje,
    które zostały dokonane przed" (§16); money is settled after each period (§9).
  - **Its sales pages:** "Wszystkie plany są miesięczne, bez umowy długoterminowej. Wypowiedzenie jest miesięczne"
    (all plans monthly, no long contract, a month's notice); a year paid up front is 20 % off, "ale nigdy tego nie
    wymagamy" ([cennik](https://join.playmore.pl/cennik/)).
- **[POLICY] kluby.org:** "miesięczny okres wypowiedzenia" (a month's notice) (carried,
  [cennik](https://oferta.kluby.org/cennik), checked again today); no club contract published (carried).
- **[ABSENT] Twój Tenis:** no club terms. Its regulamin covers players and says "Korzystanie z Portalu jest darmowe"
  ([regulamin](https://old.twojtenis.pl/pl/regulamin.html)).
- **[POLICY] Playtomic:** cancel at least 30 days ahead and ask the team to take the club offline; configuration kept
  (carried, [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) §11).

**The desk/owner's day with it.** *Reading:* at Playmore the owner gives notice 14 days before the period ends,
downloads or asks for the data first (the account is deleted at the end), and lets bookings already sold be served
or moved.

**What a Kraków desk does today.** It pays 49–149 zł a month to tenis4U, 299+ zł and 1,79 % to Playmore, or 50–79+ zł
to kluby.org (carried, [`integration.md`](integration.md) §4).

**What it means for the player app.** *Reading:* bookings sold in the old app for dates after the switch belong to the
club. They must be served in the old system, moved (block C), or cancelled and refunded.

**Market signal.** Polish club software is monthly with about a month's notice, so lock-in is the data, not the
contract.

## L. Area 18, market side: a vendor moving its own clubs to its new product

**What it covers.** How vendors moved clubs already on their older product onto a new one. This is the parallel for
moving today's *Only Raketa* clubs to the full calendar.

**Who has it**
- **[POLICY] Playmore, Reservise to Playmore:**
  - "Reservise żegna się po 10 latach"; "zostajesz przy obecnym abonamencie" (you keep your current price).
  - "Termin ustalamy indywidualnie z każdym klubem, pod jego kalendarz. Nikogo nie zostawiamy bez systemu" (the date
    is set with each club around its calendar; nobody is left without a system)
    ([reservise](https://join.playmore.pl/reservise/)).
  - The player app serves both systems at once. It has routes `/reservation/reservise/…` and the note "Karnety z
    obiektów działających na starszej wersji systemu (Reservise) zobaczysz podczas rezerwacji terminu" (passes from
    clubs still on the older system appear when you book) ([bundle](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] Twój Tenis:** old and new platforms run side by side, each club with its own start date and a link to
  each ("Przejdź do Nowego TwójTenis", "Przejdź do Starego TwójTenis") ([twojtenis.pl](https://twojtenis.pl/)).
- **[POLICY] Playtomic, the billing-model change:** "you may receive a hybrid payout"; "even if a booking takes place
  after migration, it can still belong to the old model if the payment was made before migration"
  ([NBM migration, 2026-10-09](https://helpmanager.playtomic.com/hc/en-gb/articles/45366964593041)).
- **[POLICY] Playmore's player terms:** "Rezerwacje dokonane przed wejściem w życie zmian realizowane są na
  dotychczasowych zasadach" (bookings made before a change are served on the old rules) (carried, §17.3,
  [terms](https://playmore.pl/legal/terms-of-service), 2026-10-07).
- **[POLICY] Eversports**, from its acquired USC product: a one-shot tool moves past and future appointments
  (block C).
- **[ABSENT]** What MATCHi and Eversports will do with their clubs after merging in 2026: no migration plan in MATCHi's
  venue help (searched "Eversports", "migration").

**The desk/owner's day with it.** *Reading:* one switch date per club, agreed around its calendar. Whatever was booked
and paid before that date runs to the end on the rules it was sold under.

**What a Kraków desk does today.** Not applicable: no real club runs on Raketa
([`what-raketa-has-and-build-cost.md`](what-raketa-has-and-build-cost.md) §18).

**What it means for the player app.** *Reading:* for a while a player may see clubs on both ways of working. Playmore
labels which system a pass or booking comes from.

**Market signal.** Moving one's own clubs is done club by club, with the old product left running until the last one
moves.

---

## What each old system lets a club export

| System | Customers | Past bookings | Future bookings | Fixed / season | Prices | Passes, wallets | Consent flag | API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **tenis4U** | `users.csv`: name, email, phone | report CSV, ≤ 60 days, up to today; day as a PDF picture | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** |
| **Playmore / Reservise** | panel not public; Playmore staff move "bazę klientów" | "całą historię" by staff; monthly payments Excel | moved by staff for Reservise clubs | "rezerwacje cykliczne" mapped by staff | "cennik" moved by staff | merged on a player's account | **[ABSENT]** | **[ABSENT]** |
| **kluby.org** | **[ABSENT]** a list export; "Backup danych" | booking history to Excel (2021) | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** |
| **Twój Tenis** | "zapis do plików xls" (old platform; what it covers is not stated) | not stated | moved to the new platform by the player's phone | not stated | not stated | not stated | **[ABSENT]** | **[ABSENT]** |
| **Playtomic Manager** | CSV: name, email, ID, consent, category, birthday, phone, gender, wallet balances | CSV/JSONL by service date; API 90 days | CSV/JSONL by service date; API, all | in the booking list and API (`RECURRING_BOOKING`) | **[ABSENT]** | in the customer CSV and API | yes | read-only, Champion/Master |
| **MATCHi** | Excel (Complete, IdrottOnline, NIF) | reservations export; statistics `.xls` | reservations export | subscriptions list (export not stated) | **[ABSENT]** | **[ABSENT]** | **[ABSENT]** | not read |

Cards: no system lets a club take saved cards away; Stripe's import needs the old processor's cooperation (block F).

## Gaps

- **tenis4U:** the columns of its reservation report (made on the server, never seen), and whether tenis4U will
  export future and fixed bookings or pass balances if a club asks. Its club contract (notice, data return) is
  unpublished. Only a real club's export or a question to tenis4U answers these.
- **Playmore:** what its club panel exports, and what it does when a club leaves *to* a rival.
- **kluby.org:** whether a club can export its customer list, and what its backup contains (the help is video only).
- **Twój Tenis:** exports and club terms of its new platform.
- **Cards:** whether Przelewy24 or Tpay ever release card references to another processor, and whether Stripe imports
  into a Connect connected account. Neither seems to matter for Kraków, where saved cards were not seen.
- **Law:** whether an email or SMS inviting a club's customers to install a new app is "informacja handlowa" under
  PKE art. 398; whether creating player accounts from a club's list makes Raketa a controller; what a privacy notice
  must say when the processor changes. These are questions for a lawyer. No UODO guidance on changing processors was
  found.
- **Market:** no first-hand complaint of double bookings during a switch, no published migration plan for the
  MATCHi–Eversports merger, and no source for where Rocket Padel went.
