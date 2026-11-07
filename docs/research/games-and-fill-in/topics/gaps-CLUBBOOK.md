# Gaps round — CLUBBOOK (the club's Bookings page)

Answers to the facts the CLUBBOOK grades needed, read 2026-10-08. The three provisional grades come
first (R-CLUBBOOK-31, -33, -34), then the rest in the order of the gaps list.

**Sources and how they were read.** Help centres through their own Zendesk search (Playtomic club
and player help, MATCHi venue help, GetYourGuide supplier help); the club web apps a desk uses,
read from their published code and translation catalogs (Playtomic Manager at
`manager.playtomic.io`, Playmore Manager at `manager.playmore.pl`, tenis4U's club panel at
`panel.tenis4u.pl`) and tenis4U's player web app; Kraków clubs' own rules; the payment operators'
pages; Airbnb's host help. A line read from a web app's code or catalog is tagged **[POLICY]**, as
in the other gaps files: it shows what the product's screens say and do, not a session of using it.
A general web search could not be run for most of this round (the session's search budget was
spent), so every source here was opened directly.

Kinds: **[POLICY]** a rule or a screen's text · **[PRICE]** · **[DOCS]** a provider's document ·
**[DATA]** a figure or a computation · **[ABSENT]** looked for and not found, with where. *Reading*
lines compare; they are not sources.

---

## 1. R-CLUBBOOK-31 — does the desk's day view follow changes by itself?

### Playtomic's Schedule re-reads the day every 30 seconds

- **[POLICY]** The Schedule asks the server again every 30 seconds for the day's court occupancy,
  the closed dates, and the matches, leagues, tournaments and classes on it (`pollingInterval: 3e4`,
  `refetchOnMountOrArgChange: true` on each query). The re-reading is switched off only while the desk
  is in the middle of a reschedule (`isRescheduleInProgress`).
  [Playtomic Manager: schedule module](https://manager.playtomic.io/assets/schedule-D2qv8-fn.js),
  [Calendar module](https://manager.playtomic.io/assets/Calendar-DrLnPhQX.js) — read 2026-10-08
- **[ABSENT]** A timed re-read of the Booking List (its module has no polling), and any help article
  on the Schedule refreshing: club help searched for "real time" and "refresh" (hits only on reports,
  mobile, hardware, the API and leagues). [Club help search API](https://helpmanager.playtomic.com/api/v2/help_center/articles/search.json?query=refresh&locale=en-gb) — read 2026-10-08
- *Reading:* on an open Playtomic Schedule, a player leaving, a match cancelled or a seat taken shows
  within about half a minute, with nobody touching the page. Reports are a separate thing and update
  hourly (`competitor-club.md#what-the-club-sees-of-its-money`).

### tenis4U's club calendar re-reads every 10 seconds and flags bookings that appear or vanish

- **[POLICY]** The calendar carries a component (`app-refresh-calendar-interval`) that re-reads the
  club's bookings for the dates on screen every 10 seconds, slowing to every 60 seconds while the
  server takes longer than 1.5 s to answer. When a booking appears or disappears it redraws the
  calendar and shows a banner, "Nowa rezerwacja." / "Nowe rezerwacje." or "Usunięto rezerwację." /
  "Usunięto rezerwacje.", one line per booking: "{name} ({court}) - {date} {from}-{to} ({weekday})".
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- *Reading:* the check compares booking numbers only. A change inside a booking that keeps its number
  (a player leaving a shared booking, a payment marked) neither redraws the calendar nor raises the
  banner; it shows at the desk's next action or reload.

### Playmore Manager re-reads the calendar every 5 minutes while the tab is in front

- **[POLICY]** The calendar re-reads its bookings every 300 seconds; if the browser tab is hidden at
  that moment it skips the read and does it when the desk comes back to the tab. When a write meets a
  stale view, the desk is told to refresh: "Tej rezerwacji nie ma już w tym obiekcie — odśwież
  kalendarz", "Nie udało się odświeżyć kalendarza — odśwież stronę, aby zobaczyć aktualny stan", "Ten
  termin na korcie jest już zajęty. Odświeżyliśmy grafik — zamknij okno i wybierz inny termin."
  [Playmore Manager calendar module](https://manager.playmore.pl/assets/calendar-views-DgSAcW-a.js),
  [Polish calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js) — read 2026-10-08
- *Reading:* all three desks' calendars follow changes by themselves — Playtomic within 30 seconds,
  tenis4U within 10 (for whole bookings), Playmore within 5 minutes.

---

## 2. R-CLUBBOOK-33 — a renamed court on bookings already made

### No platform says what a booking shows after its court is renamed

- **[ABSENT]** Playtomic's court article says only that a court's details can be edited, and its
  Manager strings for courts (name, delete warning) say nothing about bookings on it; searched club
  help for "rename" (0 hits) and "court name". Playmore Manager's settings strings ("Nazwa
  kortu/obiektu") and tenis4U's panel say nothing either.
  [Playtomic: How to add/edit/delete a court](https://helpmanager.playtomic.com/hc/en-gb/articles/20535305323665-How-to-add-edit-delete-a-court) (updated 2026-08-25),
  [Manager courts strings](https://manager.playtomic.io/locales/en/courts.json),
  [Playmore settings strings](https://manager.playmore.pl/assets/venue-settings-YhePUFzO.js) — read 2026-10-08

### What the desks' code shows

- **[POLICY]** Playtomic: a match carries its court's name beside its court number (`resourceName`,
  `resourceId`), and the match screens print that name. The booking history records a court change as
  "Court updated from {oldResourceName} to {newResourceName} by {requestUserName} ({role})".
  [Manager booking-history strings](https://manager.playtomic.io/locales/en/match_history_record.json) — read 2026-10-08
- **[POLICY]** tenis4U: the desk calendar puts each booking in its court's column by court number, and
  the new/removed banner looks the court's name up in the club's current court list
  (`findStationName(station_id)`), so the desk reads the current name. The player's app prints the
  `station_name` sent with the booking.
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js),
  [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08
- *Reading:* the desk's grid follows the court's number at both, so a renamed court's column carries
  the new name. Whether the name a player is sent is the new one or the one at booking is not visible
  from any source read.

---

## 3. R-CLUBBOOK-34 — counting a club's own cancellations

### No racket platform publishes a measure of a club's cancellations

- **[ABSENT]** Playtomic club help searched for "cancellation rate", "ranking", "visibility",
  "penalty", "club rating", "cancellations by the club"; MATCHi venue help for "cancellation rate" and
  "quality"; Playmore Manager's report strings; tenis4U's panel. Nothing counts the club's
  cancellations or ties a consequence to them. — read 2026-10-08

### Playmore gives the club owner audit reports on its own staff's cancellations and late changes

- **[POLICY]** Reports "Uprzywilejowane anulowania — Anulowania po terminie oznaczone jako
  regulaminowe i przekwalifikowania po fakcie" (columns: employee, client, booking, court, the club's
  limit, hours past the deadline, price, refunded) and "Zmiany last-minute — Przeniesienia, skrócenia i
  zmiany ceny rezerwacji zrobione w panelu … Korekty ceny po starcie gry są liczone osobno". Each
  cancellation is labelled "Anulowane przez pracownika", "Anulowane przez klienta" or "Anulowane
  automatycznie przez system".
  [Playmore Manager report strings](https://manager.playmore.pl/assets/reports-iEpTYc3L.js),
  [calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js) — read 2026-10-08
- *Reading:* the count belongs to the club and watches its staff; the platform does not rate the club
  by it.

### GetYourGuide: a supplier's own cancellations must stay at or under 1.0 % over 90 days

- **[POLICY]** "Supplier Cancellation Rate (non-force majeure): Partners must maintain a cancellation
  rate of 1.0% or lower"; no-show rate 0.2 % or lower; "monitored on a 90-day rolling basis"; counted
  by the date of cancellation. Force majeure ("bad weather, natural disasters, war, strikes, or
  government actions") is left out; "lack of availability, vehicle issues, or you ask the traveler to
  cancel" count. "Failure to consistently meet these standards may result in the temporary removal of
  activities from the platform." The supplier sees its rate under Performance.
  [GetYourGuide: Performance Quality Standards](https://supply.getyourguide.support/hc/en-us/articles/29374073400989-GetYourGuide-Performance-Quality-Standards) (updated 2026-09-30) — read 2026-10-08
- **[POLICY]** Temporary suspension may follow "high cancellation rates associated with your
  activities"; bookings already made may go ahead, or GetYourGuide may cancel them "and offer
  customers either a full refund or alternative services".
  [GetYourGuide: temporary suspension and permanent deactivation](https://supply.getyourguide.support/hc/en-us/articles/14336225334813-Understanding-temporary-suspension-and-permanent-deactivation-of-your-activities-on-GetYourGuide) — read 2026-10-08
- **[POLICY]** Every supplier cancel carries one of three reasons — ordinary operational, force
  majeure (an isolated one needs "a justification/explanation"), or customer-requested — and "The
  selected reason will be shared with customers".
  [GetYourGuide: Understanding Cancellation Reasons](https://supply.getyourguide.support/hc/en-us/articles/30568164738589-Understanding-Cancellation-Reasons-for-Bookings) — read 2026-10-08

### Airbnb: under 1 % for Superhost, a fee for each host cancellation, the dates blocked

- **[POLICY]** Superhost requires "a less than 1% cancellation rate", with exceptions for Major
  Disruptive Events or other valid reasons, assessed every 3 months over the past 12; Airbnb "may
  suspend or withhold status for hosts with … high host-initiated cancellation rates".
  [Airbnb: What's required to be a Superhost](https://www.airbnb.com/help/article/829) — read 2026-10-08
- **[PRICE]** A host who cancels pays 50 % of the nights not stayed when 48 hours or less before
  check-in (or after it), 25 % from 48 hours to 30 days, 10 % beyond (at least 50 USD), gets no payout
  for the stay, and may have the listing's calendar blocked on those dates, lose Superhost, or have the
  listing suspended. A host found responsible, "such as by double-booking", pays whoever starts the
  cancellation. [Airbnb: Host Cancellation Policy (effective 9 Oct 2023)](https://www.airbnb.com/help/article/990) — read 2026-10-08
- *Reading:* where a marketplace counts its sellers' cancellations, the line sits at about 1 %,
  weather and force majeure are left out, the seller can see its own figure, and what follows is
  lost standing or temporary removal; only Airbnb adds a fee.

---

## 4. R-CLUBBOOK-25 — another game for the players after a club cancels

### Playtomic, MATCHi and Playmore refund; none offers another slot

- **[POLICY]** Playtomic: when the club cancels, "the money is returned to your original payment
  method"; "If you arrive and the club is closed, please contact the club directly to cancel your
  booking and request a refund or reschedule." The Manager's cancel dialog offers only refund routes
  ("Refund all participants to their original payment methods", "… to the club wallet", "Let me
  choose how to refund each participant") and says "participants will be informed by email and
  notification".
  [Player help: How to cancel a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832121593873) (updated 2026-09-30),
  [Player help: FAQ](https://playerhelp.playtomic.com/hc/en-gb/articles/19831519179281-FAQ-Players-Playtomic),
  [Manager match strings](https://manager.playtomic.io/locales/en/matches.json) — read 2026-10-08
- **[POLICY]** MATCHi: the admin picks a refund option and may "type a message to the customer";
  nothing else follows. [MATCHi: Cancel and/or refund booking](https://matchi.zendesk.com/hc/en-gb/articles/11673921738013-Cancel-and-or-refund-booking) (updated 2026-09-14) — read 2026-10-08
- **[POLICY]** Playmore Manager, cancelling an open game: "W tej grze jest {n} graczy — wszyscy dostaną
  zwrot i powiadomienie." The player app's push prompt promises "Zwolnione terminy i odwołania w Twoich
  obiektach" as a standing alert, not an offer tied to the cancel.
  [Playmore Manager calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js),
  [Playmore player strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[ABSENT]** An offer of another slot or game after a club cancel: Playtomic's club and player help,
  MATCHi's cancel article, Playmore's player and Manager strings. — read 2026-10-08

### Kraków clubs' own rules offer another court or time

- **[POLICY]** Fame Sport (tenis4U): "W przypadku odwołania rezerwacji przez Klub klientowi zostanie,
  w miarę dostępności, zaproponowany inny kort lub termin" (II.18); if that fails, the fee is
  "według wyboru klienta — zaliczona na poczet kolejnej rezerwacji albo zwrócona" (II.19). A standing
  booking's date cancelled by the club: "Klub w takim przypadku zaproponuje inny termin" (III.11).
  [Fame Sport: Regulamin obiektu 2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-08
- **[POLICY]** SAO Sports Hub: "W przypadku odwołania gry z naszej strony (np. warunki pogodowe)
  zawsze zwracamy pełną kwotę lub proponujemy nowy termin"; in rain "poinformujemy Cię o tym, a opłatę
  zwrócimy lub przełożymy na inny termin bez dodatkowych kosztów".
  [SAO Sports Hub](https://saosports.pl/) — read 2026-10-08

### GetYourGuide lets the customer pick a new date or the refund

- **[POLICY]** After a supplier's single cancel, customers are told by email and in the app and "will
  be able to reschedule the booking to a new date, or to receive the full refund"; with no choice
  within 2 days the booking is cancelled and refunded. A bulk cancel offers "the option to cancel or
  reschedule", except for bookings in the past and severe force majeure.
  [GetYourGuide: Single and Batch Cancellations](https://supply.getyourguide.support/hc/en-us/articles/13980989354141-Canceling-Bookings-Single-and-Batch-Cancellations-Explained) — read 2026-10-08
- *Reading:* the platforms stop at the refund; the Kraków clubs' written rules and GetYourGuide go one
  step further and offer the same people another time.

---

## 5. R-CLUBBOOK-17 — telling the players of a move or a closure

### Playtomic: an email and an in-app notice; their wording is not published

- **[POLICY]** "Users always receive emails and in-app notifications about any changes to their
  reservations"; "All customers in the reservation will get an email notification about the change."
  The club's booking history logs the move as "Court updated from {oldResourceName} to
  {newResourceName} …" and "from {oldTime} to {newTime} …".
  [General Rules to modify a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20534894210833-General-Rules-to-modify-a-reservation) (updated 2026-09-23),
  [How to reschedule a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535241098257-How-to-reschedule-a-reservation),
  [Manager booking-history strings](https://manager.playtomic.io/locales/en/match_history_record.json) — read 2026-10-08
- **[ABSENT]** The text of the change email or push, and whether it names the old court beside the
  new: club help searched for "booking modified", "change court", "reschedule email"; player help for
  "booking modified", "court changed"; the Manager catalogs; the Android app's strings (6.93.2, where
  a push's text is not held). — read 2026-10-08

### Playmore Manager: a switch to tell the client, by SMS, push and email

- **[POLICY]** Editing a booking: "Powiadom klienta o zmianie (SMS, push, e-mail)"; switched off,
  "Klient nie dostanie żadnego powiadomienia o tej rezerwacji (SMS, push, e-mail)."; on a past booking
  "Rezerwacja już się odbyła, więc powiadomienie klienta jest domyślnie wyłączone."; moving several
  dates of a series, "Klient dostanie jedno powiadomienie — o pierwszym terminie."
  [Playmore Manager calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js) — read 2026-10-08
- **[POLICY]** The club may switch off system messages "dotyczących potwierdzenia rezerwacji,
  przypomnień o płatnościach, anulowania rezerwacji i innych operacji systemowych", and writes its own
  SMS templates, with the cost of one SMS shown.
  [Playmore Manager settings strings](https://manager.playmore.pl/assets/venue-settings-YhePUFzO.js) — read 2026-10-08

### tenis4U's panel: no tell-the-players choice on Move or Cancel

- **[ABSENT]** A notify switch or message in the move ("Przenieś rezerwację", "Przenieś do:") or
  cancel ("Anuluj ze zwrotem", "Anuluj bez zwrotu") dialogs; the panel's SMS settings are the club's
  own phone for booking notices ("opcja powiadomień sms jest dodatkowo płatna 30 gr za każdy sms") and a
  per-court SMS/push switch. Whether tenis4U's server tells the player is not visible.
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** The player app has lines for a cancel ("Rezerwacja odwołana", "Odwołano") and none for a
  booking the club moved. [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08
  Carried: a tenis4U club cannot write to the players of one booking
  (`gaps-FILL.md#tenis4u-pushes-tournament-and-league-news-by-distance-nothing-about-a-booking`).

### Kraków clubs: "as early as possible, with the contact details we hold"

- **[POLICY]** Fame Sport: "O zmianie lub odwołaniu rezerwacji Klub poinformuje klienta możliwie jak
  najwcześniej, wykorzystując posiadane dane kontaktowe" (II.17); "Zmiana numeru kortu w ramach
  obiektu na kort o porównywalnych warunkach do gry nie stanowi odwołania rezerwacji" (II.20).
  [Fame Sport: Regulamin 2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-08
- **[ABSENT]** Garden Padel's rules say nothing on how players are told of a closure; only the club's
  email for complaints (8.1). [Garden Padel: Regulamin](https://gardenpadel.pl/regulamin/) — read 2026-10-08
- *Reading:* in Kraków a desk tells players itself, by phone or SMS from the booker's details, and
  Fame Sport's rules don't count a move to a comparable court as a change worth the player's consent.

---

## 6. R-CLUBBOOK-20 — what a refund costs a club at Przelewy24 and Tpay

### Przelewy24: the refund is free, the commission is kept

- **[POLICY]** "Brak opłaty za wykonanie zwrotu." "Prowizja za zrealizowaną płatność jest
  bezzwrotna, w związku z tym, że usługa przekazania środków za zamówienie została wykonana." "Zwrot
  można wykonać tylko do wysokości dostępnego salda w panelu Przelewy24."
  [Przelewy24: Zwroty](https://www.przelewy24.pl/zwroty), [Rozpoczęcie współpracy](https://www.przelewy24.pl/rozpoczecie-wspolpracy) ("Obsługa zwrotów — Jest zawsze darmowa") — read 2026-10-08

### Tpay: the commission is kept, and a card refund is charged like a card payment

- **[POLICY]** "Prowizja pobierana jest od każdej poprawnie zaksięgowanej transakcji i nie podlega
  zwrotowi w przypadku anulowania/ zwrotu zamówienia przez klienta."
  [Tpay FAQ](https://support.tpay.com/faq/czy-w-przypadku-zwrotu-transakcji-oddajecie-pobrana-prowizje) — read 2026-10-08
- **[PRICE]** "Zwroty": 1 zł each on Starter, 0 zł on Business and Enterprise ("Nie dotyczy transakcji
  opłaconych kartą"); "Zwroty płatności kartą": "jak za płatność kartą" on all three.
  [Tpay: Oferta](https://tpay.com/oferta) — read 2026-10-08

### Marta's 160 zł game cancelled by the club, at standard rates

- **[DATA]** Computed from the standard rates (Przelewy24 1,29 % + 0,30 zł; Tpay Starter 1,59 % +
  0,39 zł, BLIK + 0,41 zł; Stripe 1,60 zł on a 40 zł share — `local-market.md#what-polish-operators-charge-against-stripe`):

  | How the 160 zł was paid | What the club is left short |
  |---|---|
  | Raketa: four 40 zł shares on Stripe | 6,40 zł |
  | Przelewy24: four 40 zł payments | ≈ 3,26 zł (commission kept, refund free) |
  | Przelewy24: one 160 zł payment | ≈ 2,36 zł |
  | Tpay Starter: four 40 zł card payments | ≈ 8,21 zł (4 × 1,03 commission + 4 × 1,03 refund) |
  | Tpay Starter: four 40 zł BLIK payments | ≈ 8,18 zł (4 × 1,05 + 4 × 1 zł) |
  | Tpay Starter: one 160 zł card payment | ≈ 5,87 zł |

- **[POLICY]** Carried: tenis4U returns any deleted online booking "pomniejszonych o opłatę
  transakcyjną w wysokości 2%" (`gaps-RESCUE.md#tenis4us-2--is-taken-on-any-deleted-online-booking`),
  and Garden Padel keeps 2 % on a weather refund (`local-market.md#the-refund-deduction-players-already-know-a-flat-2-`):
  at those clubs the player bears it — 3,20 zł on 160 zł — not the club.
- **[ABSENT]** Which operator contract and rate a tenis4U club pays under: the panel lists "P24
  włączone" per club and Tpay as "legacy"; no rate is published.
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

---

## 7. R-CLUBBOOK-14 — Playtomic Manager when the club's Stripe account is restricted

### Manager warns that payments and payouts will stop, and lets the desk skip the warning

- **[POLICY]** "Your payments are about to be interrupted" — "Your Stripe Connect Account has missing
  information. Solve this issue immediately, otherwise online payments and payouts will be
  interrupted.", with the buttons "Add missing information" and "Skip for now".
  [Manager integrations strings](https://manager.playtomic.io/locales/en/integrations.json) — read 2026-10-08
- **[POLICY]** A move refuses only a court of another size or sport ("Moving an event to a court with a
  different size is not allowed", "… with a different sport is not allowed"); the reschedule code
  checks nothing about the club's payments account.
  [Manager schedule strings](https://manager.playtomic.io/locales/en/schedule.json),
  [Calendar module](https://manager.playtomic.io/assets/Calendar-DrLnPhQX.js) — read 2026-10-08
- **[ABSENT]** A help article on what a restricted account stops at the desk: club help searched for
  "restricted", "Stripe verification", "charges disabled", "payouts paused". — read 2026-10-08
- *Reading:* at Playtomic a move is a calendar act and goes ahead whatever Stripe says; what stops is
  money, because Stripe refuses a charge on the account itself
  (`gaps-FILL.md#stripe-refuses-the-charge-request-itself-not-each-card`).

---

## 8. R-CLUBBOOK-35 — money back for a game stopped after it began

### Playtomic lets a club cancel and refund a played booking for 30 days, or reschedule it

- **[POLICY]** "The cancellation of bookings that are over 30 days old from the date of play is not
  permitted, to ensure the club has sufficient funds for refunds." "You cannot cancel a past booking as
  it was created under the distribution model. Past bookings cancellation is only available under the
  model with pre-authorization." Partial refunds are not offered ("Additional refund options are coming
  in the following months"). [Manager match strings](https://manager.playtomic.io/locales/en/matches.json) — read 2026-10-08
- **[POLICY]** "Past reservations can also be rescheduled." For unusable courts: "cancel bookings if
  necessary to process refunds if the courts were unusable."
  [How to reschedule a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535241098257-How-to-reschedule-a-reservation),
  [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097-How-to-Handle-Common-Booking-Issues-A-Quick-Guide-for-Your-Club) — read 2026-10-08

### tenis4U refuses a desk refund once the booking has begun

- **[POLICY]** "Nie można usunąć rezerwacji opłaconej online, która się już rozpoczęła lub zakończyła.
  Automatyczny zwrot opłaty następuje przy usunięciu rezerwacji przed jej rozpoczęciem. Jeśli chcesz
  wygenerować zwrot po czasie rozpoczęcia rezerwacji, skontaktuj się z nami :)". Newer bookings offer
  "Anuluj ze zwrotem" and "Anuluj bez zwrotu" where the server allows each.
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

### Playmore lets the desk lower the price after the start, and the difference goes back

- **[POLICY]** A change after the start is labelled "Zmiana po rozpoczęciu rezerwacji — po terminie
  bezpłatnego odwołania ({window}). Cena spada o {amount}."; the form shows "Cena przed", "Cena po",
  "do zwrotu". Once the booking is settled with the club: "obniżka ceny nie zwróciłaby graczowi
  pieniędzy. Zgłoś ją do Playmore, a oddamy różnicę." The owner's report counts "Korekty po starcie
  gry" separately. [Playmore Manager calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js),
  [report strings](https://manager.playmore.pl/assets/reports-iEpTYc3L.js) — read 2026-10-08

### MATCHi refunds a played booking within its month, in part if wanted

- **[POLICY]** "You can also issue a partial refund rather than the full amount"; a card-paid booking
  can be refunded "as long as the booking's play time falls within the current calendar month".
  [MATCHi: Cancel and/or refund booking](https://matchi.zendesk.com/hc/en-gb/articles/11673921738013-Cancel-and-or-refund-booking) (updated 2026-09-14) — read 2026-10-08

### Kraków clubs write nothing for rain mid-hour, except KSOS

- **[ABSENT]** A rule for a game stopped after it began: Garden Padel covers only a court unavailable
  for weather (5.3, refund minus 2 %); Fame Sport only an outdoor court closed for weather, at no cost
  (II.21); SAO says a booking "może zostać odwołana" in rain and the player may edit it "przed jej
  rozpoczęciem". KSOS's 7-day replay is the one written case
  (`local-market.md#weather-on-outdoor-courts`).
  [Garden Padel](https://gardenpadel.pl/regulamin/), [Fame Sport 2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf),
  [SAO Sports Hub](https://saosports.pl/) — read 2026-10-08
- *Reading:* Playtomic, Playmore and MATCHi each leave the club a way to give money back after the
  start; tenis4U sends the club to its own support.

---

## 9. R-CLUBBOOK-3 — what a desk sees of the booker

### tenis4U shows the booker's phone on the booking

- **[POLICY]** Booking details show "Telefon: {phone}"; a desk booking form takes phone, name and email;
  the club can export its users as "Imię i nazwisko,Email,Telefon".
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

### Playmore needs the client's phone for a desk booking

- **[POLICY]** "Numer telefonu klienta jest wymagany"; "Szukaj klienta (telefon lub imię)..."; "Brak
  telefonu"; payment links go by SMS ("Wpisz numer telefonu klienta — link do płatności idzie SMS-em").
  [Playmore Manager calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js) — read 2026-10-08

### Playtomic: copy a player's email or phone from the booking

- **[POLICY]** A participant's menu offers "Copy email" and "Copy phone number"; the customer export
  covers "name, surname, e-mail, phone number". Carried: the details reach the club only through an
  online payment or the club's terms (`competitor-club.md#talking-to-players-and-what-the-club-sees-of-them`).
  [Manager schedule strings](https://manager.playtomic.io/locales/en/schedule.json),
  [customers strings](https://manager.playtomic.io/locales/en/customers.json) — read 2026-10-08
- *Reading:* every desk read can ring its booker; the phone is required at Playmore and shown at tenis4U.

---

## 10. R-CLUBBOOK-13 — hours kept off online sale, and moves onto them

### SAO keeps its best hours for members first

- **[POLICY]** "Członkowie klubu mają pierwszeństwo w dostępie do najlepszych terminów"; "Jako członek
  klubu masz dostęp do najlepszych terminów, zanim zwolnią się dla pozostałych graczy."
  [SAO Sports Hub](https://saosports.pl/) — read 2026-10-08

### Fame Sport may set courts or hours aside, and books by phone, desk or system

- **[POLICY]** "Klub może przeznaczyć określone korty lub godziny na potrzeby zajęć szkoleniowych,
  trenerów, zawodów, turniejów lub innych wydarzeń" (I.11); bookings "telefonicznie, osobiście w
  recepcji Klubu lub za pośrednictwem aktualnie stosowanego przez Klub systemu rezerwacyjnego" (II.2);
  a standing booking's holder "może mieć pierwszeństwo w przedłużeniu dotychczasowego terminu" (III).
  [Fame Sport: Regulamin 2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-08

### tenis4U can switch a court's online booking off, or limit the hours it takes bookings

- **[POLICY]** Panel refusals: "Nie można dodać rezerwacji gdyż kort ma wyłączoną możliwość dokonania
  rezerwacji online, aktywuj rezerwacje online" and "Kort ma wyłączoną możliwość rezerwacji w
  godzinach 16:30 - 22:00 oraz w weekendy" (`OUT_OF_RESERVATION_MAKING_HOURS`).
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
  - *Reading:* the second is a fixed text in the code; which club it serves is not shown.

### Playtomic's Schedule, and its moves, include courts not sold online

- **[POLICY]** The Schedule loads every active court whether bookable online or not
  (`isBookableOnline: [true, false]`), and a move refuses only another size or sport.
  [Manager schedule module](https://manager.playtomic.io/assets/schedule-D2qv8-fn.js),
  [schedule strings](https://manager.playtomic.io/locales/en/schedule.json) — read 2026-10-08.
  Carried: a court not bookable online "stays in the calendar for the desk"
  (`competitor-club.md#which-courts-are-sold-online`).
- **[ABSENT]** A Kraków club's written rule keeping evening hours for the desk or regulars: Garden
  Padel, Fame Sport and SAO read here; Atras, Miazga and Squash4You earlier
  (`local-market.md#which-booking-systems-kraków-clubs-run`). — read 2026-10-08

---

## 11. R-CLUBBOOK-11 — a refunded player on Playtomic's lists

### The refund shows on the booking's row and on the payment, not on the player's line

- **[POLICY]** The Booking List has one row per booking, with "Participants" and a "Payment status"
  chip: Paid, Partially paid, Pending, Refunded, Unpaid, N/A.
  [Manager bookings strings](https://manager.playtomic.io/locales/en/bookings.json) — read 2026-10-08
- **[POLICY]** A participant's line in the Schedule reads "Paid", "Unpaid", "Paid by Owner", "Cash:
  Paid", "App: Paid", "Wallet: Paid", "Paid with debt" and the like; Payments → Processed lists each
  payment with the status "Refunded", and "Related payments" groups one booking's payments.
  [Manager schedule strings](https://manager.playtomic.io/locales/en/schedule.json),
  [payments strings](https://manager.playtomic.io/locales/en/club_payments.json),
  [Split payment statuses](https://helpmanager.playtomic.com/hc/en-gb/articles/50423411876881-Split-payment-bookings-statuses-and-charges-in-Playtomic-Manager) — read 2026-10-08
- **[ABSENT]** A "refunded" status on a participant's line (the Manager's English catalogs). — read 2026-10-08

---

## 12. R-CLUBBOOK-29 — taking in bookings from another system

### Playmore takes in bookings once, from Reservise, and offers no feed

- **[POLICY]** Integrations: wFirma, Fakturownia, Stripe, Google Analytics, Pixel Meta, Automatyka and
  Webhooki, the last for devices ("Podaj adres https:// sterownika lub producenta (np. Loxone Cloud
  DNS)"). Bookings come in only by "Import rezerwacji z systemu Reservise" ("Wszystkie rezerwacje będą
  oznaczone jako „import”"; undoing it "spowoduje anulowanie wszystkich zaimportowanych rezerwacji");
  GymManager imports clients only.
  [Playmore Manager settings strings](https://manager.playmore.pl/assets/venue-settings-YhePUFzO.js) — read 2026-10-08
- **[ABSENT]** An iCal feed, a booking API or a calendar sync in Playmore Manager's strings (searched
  "ical", "google", "synchroniz", "api", "integrac"). — read 2026-10-08
- Carried: kluby.org and tenis4U publish no import, feed or API
  (`gaps-FILL.md#klubyorgs-integrations-list-has-no-calendar-feed-import-or-api`,
  `gaps-FILL.md#tenis4us-club-calendar-has-no-published-import-or-api`).

### Playtomic's club API reads, never writes

- **[POLICY]** "a secure, read-only interface that allows clubs to access their booking data", for the
  Champion or Master plans. [Playtomic API: Complete Guide](https://helpmanager.playtomic.com/hc/en-gb/articles/38836515997073-Playtomic-API-Complete-Guide) (updated 2026-08-17) — read 2026-10-08
- *Reading:* none of the systems a Kraków club runs can take a Raketa game into its calendar except
  by a person typing it.

---

## 13. R-CLUBBOOK-32 — closing a whole evening, and many cancels at once

### tenis4U and Playmore block several courts at once

- **[POLICY]** tenis4U: "Dodaj blokadę do stanowisk" (a tick per court, a start and end date and
  hour), one-off or weekly ("Blokady cykliczne", "Wybierz dzień tygodnia dla którego ustawiona
  zostanie blokada we wskazanym przedziale czasowym").
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** Playmore: "Niedostępność zostanie utworzona dla wszystkich wybranych kortów", repeating
  up to a year ("Maksymalny okres powtarzania to 1 rok") and saved one by one ("Zamknięcie lub
  odświeżenie karty przerwie zapis w połowie").
  [Playmore Manager calendar strings](https://manager.playmore.pl/assets/calendar-BtoV5Fhx.js) — read 2026-10-08
- **[ABSENT]** In either, what a block does to bookings already in those hours, and a cancel of many
  bookings in one act: Playmore's batch acts cover one series' future dates only ("Anuluj wszystkie
  przyszłe", "Przenieś zaznaczone ({count})"). Playtomic's Holidays "block bookings on your club
  calendar", and its catalogs hold no bulk cancel (`competitor-club.md#holidays-and-blocks`). — read 2026-10-08

### GetYourGuide cancels a timeframe, stops sales and tells every customer

- **[POLICY]** Bulk cancellation: pick the activity and the timeframe, review "a list of all bookings
  impacted", answer "Should we stop accepting bookings?", give a reason, and review "the automatic
  customer replies that will be sent"; at most 100 at a time when more than 120 are affected. "All
  selected bookings will be canceled, customers will be notified automatically."
  [GetYourGuide: Single and Batch Cancellations](https://supply.getyourguide.support/hc/en-us/articles/13980989354141-Canceling-Bookings-Single-and-Batch-Cancellations-Explained) — read 2026-10-08
- Carried: MATCHi's Close lists the booked slots to cancel first
  (`platforms.md#matchi--the-club-cancels-or-blocks`).

---

## Not found this round

- **R-CLUBBOOK-33:** what a player is sent after a court is renamed, at any platform.
- **R-CLUBBOOK-17:** the wording of Playtomic's change email or push.
- **R-CLUBBOOK-13:** a Kraków club's written rule holding evening hours for the desk or regulars.
- **R-CLUBBOOK-32:** what a tenis4U or Playmore block does to bookings inside it; a multi-booking cancel there.
- **R-CLUBBOOK-35:** Garden Padel's, Fame Sport's and SAO's rule for rain after play has begun.
- **R-CLUBBOOK-14:** a Playtomic help article on a restricted payments account.
- **R-CLUBBOOK-34:** any racket platform's measure of a club's cancellations.

Where each was looked for is on its `[ABSENT]` line above. Also tried for all of them: the App Store
review feeds read on 2026-10-08 (Playtomic in 11 stores, Playmore, tenis4U, kluby.org, MATCHi,
Padel Mates, PADO, Planeta Padla), scanned in English, Spanish, Italian and Polish for a moved or
renamed court, rain after the start and a desk not refreshing — no review on any of them. Reddit and
Polish forums were not tried again: earlier rounds found them unreadable
(`complaints.md#what-could-not-be-read`). Video walkthroughs could not be looked for, as a web search
could not be run. — read 2026-10-08
