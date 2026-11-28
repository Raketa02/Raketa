# The desk calendar — what rivals and Kraków desks do

Research for area 1 of the planning map *Rakieta becomes the club's booking software*: the one calendar a
club's desk works in all day — the grid, adding a booking, lengths, desk payments, moves, cancels, the log
and the day's other acts. It follows the founder's decision of 2026-10-12 on
[#609](https://github.com/Rakieta02/Rakieta/issues/609#issuecomment-6120454776).

**This file decides nothing.** Each feature is decided Build at launch · Build later · Leave out · Ask a real
club in the club-software grilling. Build cost is estimated elsewhere.

**Extends** [`integration.md`](integration.md),
[`../games-and-fill-in/areas/CLUBBOOK.md`](../games-and-fill-in/areas/CLUBBOOK.md),
[`../games-and-fill-in/topics/gaps-CLUBBOOK.md`](../games-and-fill-in/topics/gaps-CLUBBOOK.md),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) (§5),
[`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md) and
[`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md). Facts carried
from there keep their dates and say *carried*; everything else was read **2026-10-12**.

**Sources.** Playtomic and MATCHi help through their public Zendesk API (the HTML answers 403); Playtomic
Manager's English string catalogs; the Polish string chunks and code that Playmore Manager
(`manager.playmore.pl`) serves to every visitor; the tenis4U club panel's bundle as served by the public
demo `test-panel.tenis4u.pl` (build of 2026-10-11) and by `panel.tenis4u.pl` (same strings); tenis4U's
player web app bundle; Playmore's public club pages (their embedded page data); kluby.org's offer, help
index and changelog; Kraków clubs' own price lists and rules; Stripe's docs and Polish price page.
Nobody signed in, booked or paid, no API endpoint was called, and tenis4U's API was not read (its terms
§7 forbid automated reading). Nothing is `[MEASURED]`: no screen was seen in use.

**integration.md §5, re-checked against today's tenis4U bundles:**
- Still present, word for word: "Gość", "Recepcja oznaczy płatność przy kasie", "Recepcja potwierdziła
  gotówkę", the 60-minute payment-link text, "Dodaj rezerwację stałą", "Tworzenie kilku rezerwacji
  stałych", "Dodaj blokadę", "Blokada wzajemna", "Ustawić status zalany?", both online-off refusals, "Ilość
  dni w przód możliwych do rezerwacji", "Limit aktywnych rezerwacji na użytkownika", "Minimalny czas
  rezerwacji (30 lub 60 minut)", "Ile godzin przed startem anulować nieopłacone rezerwacje", the roles
  `RECEPTION` and `COURT_MAINTENANCE`, moderator endpoints, the club's own Przelewy24 "Client ID" and "CRC
  Key", "Pobierz jako CSV", and the 10-second re-read with "Nowa rezerwacja." / "Usunięto rezerwację.".
  The player app still carries "Dla kart multisporta minimalny czas rezerwacji wynosi 60 minut", "Podaj
  numery telefonów przypisane do kart Medicover", "Otwarte sparingi", "Rezerwacje współdzielone" and
  "Zaloguj się, aby dołączyć do sparingu".
- Sharper than §5 said:
  - "Pobierz jako CSV" exports the club's **users** (`users.csv`, "Imię i nazwisko,Email,Telefon"), not
    bookings. The day goes out as "Drukuj do PDF".
  - "Recepcja potwierdziła gotówkę" is a **log line**. It is written when the desk confirms cash that a
    player promised in the app ("Wybrano płatność w klubie" — chose to pay at the club). A desk booking's
    own switch reads "Recepcja oznaczy płatność przy kasie" (the desk will mark payment at the till) or
    "Gracz otrzyma 60 min na opłacenie online" (the player gets 60 min to pay online).
  - In the new booking form a "Gość" is a name plus an optional phone. There is no email field.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price ·
`[DOCS]` a provider's developer document · `[LAW]` a statute · `[COMPLAINT]` one party's account ·
`[ABSENT]` looked for and not found, saying where. Lines marked *reading* are inferences, not sources.

## Read this first

- **Every desk tool is a grid with one column per court.** Day view is universal. A **week view** exists
  only at tenis4U ("Dzień", "Tydzień") and kluby.org ("Nowy grafik tygodniowy rezerwacji", 2023).
  Playtomic's Schedule is "a daily snapshot", and MATCHi's is one date at a time.
- **Colours mean different things at each rival.** At Playtomic and MATCHi they show the booking type.
  Playmore's legend also shows the channel (Recepcja, Internetowa, Mobilna — desk, web, mobile) and
  whether it is paid. At tenis4U the club writes what each of 20 colours means.
- **Kraków sells courts by the hour; Spain sells padel by 90 minutes.**
  - *Squash:* 60 minutes "liczone od pełnej godziny zegarowej" (counted from the full clock hour) at Atras,
    Paolo and Squash4You. Their Playmore setup offers only 60 and 120.
  - *Padel:* Garden Padel's minimum is 60, then "Przedłużenie następuje co 30 minut" (extended in steps of
    30). Fame Sport prices by the hour, and PADO lists every other Kraków padel club at "1 hour of court
    time".
  - *Tennis:* priced per hour everywhere read.
  - *Playtomic:* "padel reservations are set to 90 minutes by default"; "Open matches usually last 90
    minutes".
- **Every desk can book someone who has no account, but Playmore asks the most.** tenis4U takes a name and
  an optional phone, Playtomic a "Guest user", and MATCHi a first and last name with an optional email.
  Playmore requires a phone, a first name and a last name.
- **A payment link that deletes an unpaid booking is Polish.**
  - tenis4U: a fixed 60 minutes.
  - Playmore: the club sets the minutes, and the link goes by SMS, so a phone is required.
  - MATCHi: links stay valid 240 days and never cancel anything.
  - Playtomic: none found.
- **Cash and card at the desk are marked by hand everywhere.** Stripe's card readers (WisePOS E, S700,
  S710, T600, WisePad 3) and Tap to Pay on iPhone and Android are generally available in Poland. Tap to Pay
  needs a native app (Terminal iOS, Android or React Native SDK) or Stripe's own Dashboard app. Only
  Playtomic sells an integrated terminal, and only in the US.
- **How fast the desk sees an app booking** (re-verified today): tenis4U within 10 s, with a "Nowa
  rezerwacja." banner; Playtomic within 30 s; Playmore within 5 min, plus an SMS to a chosen employee for
  every new court booking. MATCHi emails new customer bookings to one address.
- **Drag and drop to another court or time is everywhere.** Only Playmore adds an **undo** after the drag,
  a before/after price summary and a "tell the client" switch, and lets a club switch dragging off.
- **Every rival keeps a history of a booking, at different depth.**
  - Playmore: changes field by field, who made them, and an archive older than 90 days.
  - Playtomic: "by {requestUserName} ({role})".
  - tenis4U: a log for each booking plus a club-wide "Historia".
  - MATCHi: logs moves, but not who marked a booking paid.
- **A waiting list for a full hour is rare.**
  - CourtReserve: a court waitlist with a column on the admin grid.
  - Playmore: a player can watch a taken hour and is emailed when it frees.
  - kluby.org: "Lista oczekujących" (2017).
  - tenis4U, Playtomic and MATCHi: waiting lists only for classes and matches.
- **Polish fiscal receipts sit beside the desk.** Playmore prints *paragony fiskalne* through
  Fakturownia.pl or wFirma, and kluby.org integrated a *kasa fiskalna* in 2020. Neither tenis4U's panel nor
  Playtomic shows one.

---

## 1. The day and week view per court

**What it covers.** The desk's main screen: courts side by side as columns, time down the side, several
sports in one calendar, and how a booking's kind and state are coloured.

**Who has it**
- **Playtomic Manager [POLICY]**
  - "The Schedule provides a daily snapshot of club activities, starting with today's date… You can also
    filter activities by sport or court type." A tile shows a "Red chip (for unpaid or partially paid)"
    and a "Dot (private or public note)".
  - "Apply custom colors for each type of event", but "schedule colors are set by event type… not by
    individual coach, player, or category" ([Schedule basics][pt-basics], updated 2026-03-09). The types
    are Regular, Recurring, Open match, League, Private class, Course class, Holiday and Blocking
    ([Schedule Settings][pt-settings]).
  - The catalog has "Online booking", "Onsite booking", "Blocked by shared court", "All sports",
    "Surfaces", "Display courts:" and "Occupancy" ([schedule strings][pt-schedule]).
  - **[ABSENT]** A week view. The schedule catalog has none, and "Current week" appears only in date-range
    filters ([common strings][pt-common]).
- **Playmore Manager [POLICY]**
  - Navigation by day: "Poprzedni dzień" (previous day), "Następny dzień" (next day), "Dzisiaj" (today).
    Court groups are tags ("Wszystkie" = all). A switch "Widok kalendarza: Siatka / Lista" (calendar view:
    grid or list) opens a "Lista dnia" (list of the day).
  - Legend: "Recepcja, Internetowa, Mobilna, Cykliczna, Niedostępna, Anulowana, Opłacona, Nieopłacona,
    Opłacona – karta rabatowa niezeskanowana, Pierwsza wizyta, Mecz ligowy" — desk, web, mobile,
    recurring, unavailable, cancelled, paid, unpaid, paid but the discount card is not scanned, first
    visit, league match.
  - Filters: "Oznaczaj dłużników" (mark debtors), "Wyróżnij puste zajęcia" (highlight empty classes),
    "Pokaż adnotacje po najechaniu kursorem" (show notes on hover). Side panels: "Obłożenie obiektów"
    (occupancy), "Pogoda" (weather), "Lista zadań" (to-do list) ([calendar strings][pm-cal]).
  - Each tag has a colour and a "Krótka nazwa (recepcja)" (short name for the desk): "Gracz nadal widzi
    pełną nazwę" — the player still sees the full name ([venue settings][pm-venue]).
  - **[ABSENT]** A week-view label in the strings. The code ships FullCalendar's resource views, so whether
    a week view is offered is unknown.
- **tenis4U club panel [POLICY]**
  - Buttons "Dzień", "Tydzień", "Trenerzy", "Historia", "Kalendarz", "Stała", "Blokada", "Grupa" — day,
    week, coaches, history, calendar, fixed, block, group ([panel bundle][t4u-panel]).
  - Twenty club colours, "Opis koloru nr 1…20", each subtitled "rezerwacje specjalne" (special bookings),
    and "Zmień kolor" (change colour) on a booking.
  - A payment legend "100% opłacone · 50% częściowo · 0% nieopłacone" (paid, partly paid, unpaid) and the
    labels "STAŁE" (fixed) and "ZAJĘCIA GRUPOWE" (group class).
  - Station types include "Mączka" (clay), "Piłka nożna" (football) and "Tenis stołowy" (table tennis).
- **kluby.org [POLICY]:** "Nowy grafik tygodniowy rezerwacji" (new weekly schedule, 1 Jan 2023),
  "Informacja na grafiku o nowych klientach" (new customers flagged on the schedule, 1 Jul 2017),
  "Możliwość wyświetlenia grafiku na klubowym telewizorze" (the schedule on the club's TV, 1 Jun 2019)
  ([changelog 2023][kl-2023], [2017][kl-2017], [2019][kl-2019]).
- **MATCHi [POLICY]**
  - "a time-grid layout, colour-coded by booking type… A colour-code legend is shown below the schedule";
    "an unpaid booking is just as visible as a paid one". Ctrl/Cmd plus an arrow moves a day ([Schedule,
    updated 2026-09-14][mx-schedule]).
  - The booking type sets the colour, whether the booking counts in statistics, and whether payment is
    expected ([Booking types][mx-types]).

**The desk's day with it.** *Reading:* the desk lives on today's grid and scans it for gaps, unpaid tiles
and arrivals. A week view serves planning and fixed bookings rather than the hour in front of the desk.

**What a Kraków desk does today.**
- **[PRICE]** Several sports share one calendar. Fame Sport prices tennis, badminton and padel courts on
  one page ([Fame Sport cennik][fame-cennik]).
- **[POLICY]** Squash4You's Playmore venue carries a "Nad strugą - Squash" tag and a "Nad strugą - Tenis
  stołowy" tag. Atras has "Squash" and a non-bookable "Siłownia" (gym) ([Squash4You page data][pm-s4y],
  [Atras page data][pm-atras]).

**What it means for the player app.** *Reading:* the player never sees the grid. A rival's legend does
name the channel a booking came from, so a Games-deck booking would sit beside desk and phone bookings as
one more colour.

**Market signal.** Day view and colour by type: table stakes. Week view: a differentiator. Colours whose
meaning the club writes (tenis4U) and a channel legend (Playmore): rare.

## 2. A phone or tablet view for the desk

**What it covers.** Running the desk, or checking it from the court or at home, on a phone or tablet.

**Who has it**
- **Playtomic [POLICY]**
  - "Playtomic Manager works in your phone's browser, not as a downloadable app."
  - "Press and hold the time slot for a few seconds until the booking configuration screen opens."
  - "Zooming with two fingers is disabled by design"; "Some features are limited on mobile".
  - On a phone, admins handle "Schedule management… Daily operations: check-ins, payments, chat with
    players" ([Manager on mobile, updated 2026-09-17][pt-mobile]).
- **tenis4U [POLICY]:** a mobile edit mode with "Przenieś" (move) and "Wydłuż/Skróć" (extend/shorten)
  buttons in place of dragging, and a warning "Najlepsze wrażenia z aplikacji osiągniesz używając
  przeglądarki Chrome" — best used in Chrome ([panel bundle][t4u-panel]).
- **Playmore [POLICY]**
  - Bookings move "przeciągając kafelek myszką albo palcem" — dragging the tile with a mouse or a finger
    ([venue settings][pm-venue]). The day also opens as "Lista dnia" ([calendar strings][pm-cal]).
  - "Dostęp dla ochrony": accounts limited to "widok tylko kalendarza z oznaczaniem obecności i odbijaniem
    kart partnerskich" (the calendar only, with marking arrivals and scanning partner cards), switched on
    by email or by the device's User-Agent.
  - A TV screen set up in kiosk mode ([venue settings][pm-venue]).
- **kluby.org [POLICY]:** "Wprowadzenie grafików rezerwacji responsywnych" (responsive schedules, 1 May
  2020) and "Dostosowywanie grafiku do rozmiaru monitora" (fit to the monitor, 2020) ([changelog
  2020][kl-2020]).
- **MATCHi [ABSENT]:** any admin use on a phone (venue help searched "phone app admin", "tablet").

**The desk's day with it.** *Reading:* the desk itself is a PC. The phone serves the owner or coach away
from it, and the court-side staff who mark arrivals.

**What a Kraków desk does today.** **[ABSENT]** What device Kraków desks use. No club rule or photo says.

**What it means for the player app.** *Reading:* none directly. Rakieta's player app is native React
Native, while the club website is web — and Tap to Pay (§9) needs native.

**Market signal.** A responsive web grid: table stakes. A restricted desk or guard role: rare (Playmore).

## 3. How fast a new online booking appears, and whether the desk is alerted

**What it covers.** A booking made in the app or on the web showing up on the desk's open screen, and any
banner, sound, email or SMS that tells the desk.

**Who has it**
- **tenis4U [POLICY]**
  - The calendar re-reads the dates on screen every 10 s. It slows to 60 s while the server takes more than
    1.5 s and returns to 10 s under 0.5 s (`currentIntervalTime=1e4`, `initInterval(6e4)`).
  - It compares booking ids and shows "Nowa rezerwacja." / "Nowe rezerwacje." / "Usunięto rezerwację.",
    one line each: "{name} ({court}) - {date} {from}-{to} ({weekday})" ([panel bundle][t4u-panel],
    re-verified today).
  - **[ABSENT]** A sound or a browser notification: the bundle uses neither `Audio` nor the Notification
    API.
  - Carried (2026-10-08): booking notices by SMS to the club's phone, "dodatkowo płatna 30 gr za każdy
    sms" (30 gr extra per SMS) ([gaps-CLUBBOOK](../games-and-fill-in/topics/gaps-CLUBBOOK.md)).
- **Playtomic [POLICY], carried 2026-10-08:** the Schedule re-reads every 30 s, and each admin can opt
  into email for "Bookings created or cancelled by players"
  ([gaps-CLUBBOOK](../games-and-fill-in/topics/gaps-CLUBBOOK.md),
  [competitor-club](../games-and-fill-in/topics/competitor-club.md)).
- **Playmore [POLICY]**
  - The calendar re-reads every 300 s and skips while the browser tab is hidden, catching up on return
    (`300*1e3`, `document.hidden`, re-verified in [calendar code][pm-code]).
  - "Wysyłanie SMS potwierdzenia rezerwacji kortów dla pracownika — Wybierz pracownika, który będzie
    otrzymywał SMS-y o nowych rezerwacjach kortów" — an SMS to a chosen employee for each new court
    booking. "Dane recepcji do notyfikacji" — the desk's phone and email for system notices ([venue
    settings][pm-venue]).
  - A write against a stale view is refused: "Ten termin na korcie jest już zajęty. Odświeżyliśmy grafik —
    zamknij okno i wybierz inny termin" — taken; we refreshed the schedule ([calendar strings][pm-cal]).
- **MATCHi [POLICY]:** "Booking notification email… each time a customer makes a new regular booking…
  bookings made by administrators are excluded"; a separate cancellation email; "Each notification field
  accepts a single email address only" ([Cancellation notifications, 2026-09-15][mx-notify]).
  **[ABSENT]** How often the schedule refreshes.
- **kluby.org [POLICY]:** "Powiadomienie dla pracownika o odwołanej rezerwacji" — staff told of a
  cancelled booking (1 Jul 2020) ([changelog 2020][kl-2020]).

**The desk's day with it.** *Reading:* while the desk is on the phone, the app is selling the same hour.
A 10-second banner is what lets the desk say "it has just gone" before typing.

**What a Kraków desk does today.** *Reading:* Kraków's padel desks run tenis4U, so they get the
10-second banner; squash desks run Playmore, so they get 5 minutes plus SMS (system map in
[integration.md §4](integration.md)).

**What it means for the player app.** *Reading:* a game booked by the last yes must appear on the desk's
open grid within seconds, or the desk can sell the hour twice by phone. Every rival ends that race with a
server-side refusal of a taken slot.

**Market signal.** Auto-refresh: table stakes. An on-screen "new booking" banner: a differentiator
(tenis4U). Staff SMS per booking: rare (Playmore).

## 4. Adding a booking from the calendar

**What it covers.** The desk clicks a free slot and books a registered player, a guest with no account
("Gość"), a phone caller or a walk-in. Which fields are required, and searching the customer list from
the dialog.

**Who has it**
- **Playtomic [POLICY]**
  - Click a slot, then enter the activity type, start and end, court, "Split or Single Payment", a price
    that "the platform automatically retrieves", and "Owner and Participants… searching for a registered
    user, or… 'Guest user'". "+ New Customer" creates a profile; notes are optional ([How to add a
    reservation, 2026-06-22][pt-add]).
  - "Split Payment is not available for guest bookings"; warnings "Owner is not filled", "Price of the
    booking is not set" ([schedule strings][pt-schedule]). Customer search: "Search by name, email, or
    phone" ([customers strings][pt-customers]).
  - For a guest booking "There is no booking history to review for cancelled matches" ([Booking History,
    2026-09-03][pt-history-art]).
- **Playmore [POLICY]**
  - Two steps: "Wybierz termin i kort. Klienta i cenę podasz w następnym kroku" — pick time and court,
    then client and price.
  - The client step requires "Numer telefonu klienta", "Imię klienta" and "Nazwisko klienta" (phone,
    first and last name), checked in code. A price list, and a time and length on the club's step, are
    also required.
  - The client badges read "Zaległość / blokada" (debt or block), "Klient znaleziony po adnotacji, nie po
    nazwisku" (found by a note, not the name), and "Nowy klient — gwiazdka zniknie… 3 godziny po jego
    pierwszej grze" (a new-client star until 3 h after the first game).
  - Co-players: "Szukaj klienta (telefon lub imię)..." ([calendar strings][pm-cal]).
- **tenis4U [POLICY]**
  - "Wyszukaj zarejestrowanego użytkownika lub wpisz imię gościa" — search a registered user or type a
    guest's name. A guest is `guest_name` plus `guest_phone` under "Telefon (opcjonalnie)", with no email.
    The organiser may be left empty ("brak gracza" — no player).
  - The same form takes a declared player count, MultiSport and Medicover card counts, a custom price,
    a colour, a coach, lighting, panel-only "Uwagi" (remarks) and a message to the player.
  - An older form takes name, phone and email ([panel bundle][t4u-panel]).
  - The desk can create an account ("Tworzenie użytkownika": Imię i nazwisko, E-mail, Telefon) and confirm
    the phone with a "Kod sms".
- **MATCHi [POLICY]**
  - "New customer… Enter the customer's email, first name, and last name"; "Email is optional, but not
    checked for duplicates" ([Book court for a new customer][mx-newcust]).
  - The admin booking is "the fastest way to… register a walk-in customer"; "Admin bookings skip normal
    restrictions" ([random admin booking][mx-admin]).
  - A "default booking customer" exists for internal bookings ([default customer][mx-default]).
- **kluby.org [POLICY]:** "Wymagany numer telefonu podczas dodawania rezerwacji przez obsługę klubu" —
  phone required when staff add a booking (1 Jul 2017) ([changelog 2017][kl-2017]).

**The desk's day with it.** *Reading:* a call is name, time, court and phone in about a minute. A walk-in
is a name and cash. A regular is found by phone number. Polish tools key the customer on the phone
because the desk calls and texts.

**What a Kraków desk does today**
- **[POLICY] Phone, desk and online at every club read except SAO:**
  - Garden Padel: "online… telefonicznie w godzinach pracy recepcji, osobiście w recepcji" ([regulamin
    4][garden-reg]).
  - Fame Sport: "telefonicznie, osobiście w recepcji Klubu lub za pośrednictwem… systemu rezerwacyjnego"
    ([regulamin II.2][fame-reg]).
  - Paolo: "online, przez aplikację mobilną, telefonicznie lub w recepcji" ([regulamin][paolo-reg]).
  - Squash4You: the same ([regulamin 5a][s4y-reg]).
- **[POLICY]** SAO books only in its app: "bez telefonów i czekania" — no phone calls, no waiting
  ([saosports.pl][sao]).
- **[POLICY]** KSOS books online and takes payment "w kasie Administratora" — at the administrator's till
  ([KSOS rules][ksos-reg]).

**What it means for the player app.** *Reading:* a desk booking for someone with a Rakieta account appears
in their app as theirs, as at MATCHi ("show up in the customer's own booking history") and Playtomic. A
guest's booking has no app to land in, only the phone the desk typed.

**Market signal.** Booking from the grid for a member or guest: table stakes. A required phone: the Polish
norm (Playmore, kluby.org). A desk-created account with SMS confirmation: rare (tenis4U).

## 5. Booking lengths and the grid, and which lengths Kraków sells

**What it covers.** 30, 60, 90 and 120-minute bookings; start times on the hour or half hour; a minimum
length; buffers between bookings; and the lengths Kraków clubs actually sell, against Spain.

**Who has it**
- **tenis4U [POLICY], per court** ([panel bundle][t4u-panel]):
  - "Rezerwacje półgodzinne" (half-hour bookings) and "Minimalny czas rezerwacji 60 minut" (a switch; off
    means 30).
  - "Łączenie rezerwacji (30 minut) — Pozwala na rezerwacje 30-minutowe gdy użytkownik ma sąsiednią
    rezerwację na tym samym stanowisku. Nie obowiązuje wtedy ustalona minimalna ilość minut do
    rezerwacji." — a 30-minute add-on next to the user's own booking, ignoring the minimum.
  - "Zezwalaj na przerwy 30 minutowe pomiędzy rezerwacjami" — allow 30-minute gaps between bookings.
  - "Limitowane wejścia — Jedna rezerwacja dziennie na jednego użytkownika" — one booking a day per user.
  - The player app: "Dla kart multisporta minimalny czas rezerwacji wynosi 60 minut"
    ([app bundle][t4u-app]).
- **Playmore [POLICY]**
  - "Krok rezerwacji w kalendarzu recepcji — Co ile minut można zaznaczać, przesuwać i rozciągać
    rezerwacje… Przy 30 albo 60 minutach formularz przyjmie tylko czas trwania, który jest wielokrotnością
    kroku, więc nie powstaną rezerwacje na 15 czy 45 minut… Dotyczy tylko recepcji" — the desk's step is
    15, 30 or 60 minutes and only lengths in that step are accepted; desk only.
  - Per court group: "Interwał rezerwacji" (every 15 min, 30 min, 1 h, 1.5 h or 2 h), "Przesunięcie
    siatki slotów" (+15/30/45, e.g. "+30 min dla 8:30 zamiast 8:00"), and "Dostępne długości rezerwacji
    (minuty)" from 30 min to 4 h ([venue settings][pm-venue]).
  - Form refusal: "Rezerwacja może zaczynać się tylko o pełnej godzinie albo o :30" — only on the hour or
    at :30 ([calendar strings][pm-cal]).
- **Playtomic [POLICY]**
  - "Booking duration… The most common are 60, 90 and 120 minutes". Rules are "Fixed – Avoid Unbookable
    Time", "Flexible – Avoid Unbookable Time" and "Flexible – Allow Unbookable Time" ("Slots open every 30
    minutes"); "Unbookable time: is a gap… too short for any booking to fit" ([Availability,
    2026-09-28][pt-avail]).
  - "intervals ranging from 15 minutes to 180 minutes" in 15-minute blocks ([Flexible Booking Duration,
    2026-04-01][pt-flex]).
  - In the Schedule, "padel reservations are set to 90 minutes by default" ([Schedule basics][pt-basics]).
    Players are told "Open matches usually last 90 minutes" ([player help][pt-player-dur]).
- **MATCHi [POLICY]**
  - "Minimum booking duration", "Maximum booking duration" and "Avoid gaps" per sport. These "only apply
    to customer-facing bookings" ([Schedule][mx-schedule]).
  - A season sets "Booking duration… 5-minute increments" and "**Time between bookings** – optional gap
    between slots (e.g. 0:10 for a 10-minute break)" ([Create a new season, 2026-09-15][mx-season]).
  - Adjacent slots merge into one booking ([merge][mx-merge]). Punch cards cover "30, 60, 90, or 120
    minutes. The default is 90 minutes" ([schedule improvements][mx-improve]).
- **kluby.org [POLICY]:** "Zmiana czasu rezerwacji przyciskami + i -" — lengthen or shorten with + and −
  (1 Jul 2017) ([changelog 2017][kl-2017]). Carried: it blocks "wszystkich wolnych połówek" — all free
  half-hours ([platforms](../games-and-fill-in/topics/platforms.md)).
- **Buffers:**
  - MATCHi is the only rival with an explicit gap.
  - **[ABSENT]** at Playtomic: club help searched "buffer", "cleaning time" and "time between bookings";
    the hits are pricing articles.
  - **[ABSENT]** at Playmore: strings searched "bufor", "przerwa".
  - tenis4U's 30-minute setting concerns gaps that players leave, not a buffer.

**What a Kraków desk does today — the lengths sold**

| Club (system) | Sport | What is sold, in the club's words | Source |
| --- | --- | --- | --- |
| Garden Padel (tenis4U) | padel | "Minimalny czas rezerwacji to 60 minut. Przedłużenie następuje co 30 minut." The rented time "obejmuje przygotowanie kortu, grę, sprzątanie… i zejście z kortu" (includes setup, play, tidying and leaving) | [regulamin 4][garden-reg] [POLICY] |
| Fame Sport (tenis4U) | padel, tennis, badminton | prices per "Godzina" (hour); "Przedłużenie gry możliwe jest wyłącznie za zgodą recepcji" (extension only with the desk's consent); "Spóźnienie nie powoduje przedłużenia" (lateness does not extend) | [cennik][fame-cennik] [PRICE], [regulamin II.12–14][fame-reg] [POLICY] |
| Bajada, Padel House, Morelowa 34, Libertów (tenis4U) | padel | "All prices are for 1 hour of court time" — a third party; the clubs publish only Facebook or Instagram | PADO: [Bajada][pado-bajada], [Padel House][pado-ph], [Morelowa][pado-mor], [Libertów][pado-lib] [PRICE] |
| SAO Sports Hub (own app) | padel, tennis, pickleball | **[ABSENT]** a length; "Wszystko odbywa się online" (all online) | [saosports.pl][sao] |
| Atras (Playmore) | squash | "Podstawowym okresem wynajęcia kortu jest czas 1 godziny, liczonej zgodnie z godzinami zegarowymi"; the desk "w indywidualnych sytuacjach" may rent off the clock hour. Playmore setup: lengths [60,120], interval 60 | [regulamin §5][atras-reg], [cennik "cena za kort / 60 min"][atras-cennik], [page data][pm-atras] [POLICY] |
| Paolo (Playmore) | squash | "wynajmowane są na godzinę… 60 minut, liczone od pełnej godziny zegarowej"; "przedłużenie gry maksymalnie do 10 minut… w przypadku wolnego kortu" (up to 10 min over if the court is free). Setup [60,120], interval 60 | [regulamin][paolo-reg], [page data][pm-paolo] [POLICY] |
| Squash4You (Playmore) | squash, table tennis | the same wording, a 10-minute grace. Setup [60,120], interval 60 | [regulamin][s4y-reg], [page data][pm-s4y] [POLICY] |
| KS Grzegórzecki, Sport Factory Park, Białoprądnicka, KSOS (tenis4U, KSOS's own) | tennis | per hour: "Godzina", "zł/h", "ceny w PLN za 1 h"; classes "55 lub 85 minut" (KSG and Fame Sport, V.4) | [KSG cennik][ksg-cennik], [KSG regulamin][ksg-reg], [Sport Factory][sf-cennik], [Białoprądnicka][bp-cennik], [KSOS][ksos-courts] [PRICE] |
| Playtomic clubs (Spain and others) | padel | "padel reservations are set to 90 minutes by default"; "Most clubs offer sessions of 60, 90, or 120 minutes" | [Schedule basics][pt-basics], [player help][pt-player-dur] [POLICY] |

- **[ABSENT]** A Kraków club selling squash in 30 or 45 minutes, or padel only in 90-minute blocks, in the
  rules and price lists above.
- *Reading:*
  - Kraków's unit is the clock hour. Padel's 90 minutes exists only as 60 plus a 30-minute extension
    (Garden Padel).
  - The 5-minute changeover sits inside the hour (classes of 55 or 85 minutes; Garden Padel's rental
    includes leaving the court), not as a gap in the grid.
  - Playmore's own setup for Kraków squash offers 120 as a second length.

**What it means for the player app.** *Reading:* the Games deck's fixed one-hour game matches Kraków's
unit. A 90-minute padel game would be a second length, and a game ending at :30 leaves a half-hour the desk
must sell. That gap is the "unbookable time" Playtomic's rules exist to avoid.

**Market signal.** Several lengths and a half-hour grid: table stakes. Rules against stranded gaps:
a differentiator (Playtomic, tenis4U, MATCHi). A buffer between bookings: rare (MATCHi only).

## 6. Paying at the desk: cash and card marked by hand

**What it covers.** The desk records that someone paid in cash or by card at the till. Not an integrated
terminal (§9).

**Who has it**
- **tenis4U [POLICY]**
  - At creation, "Forma płatności": "Recepcja oznaczy płatność przy kasie" (the desk will mark payment at
    the till).
  - On the booking: "Oznacz płatność" (mark payment), "Czy chcesz oznaczyć, że opłacono w klubie?",
    "Obciąż karnet" (charge a pass), "Gotówka do pobrania" (cash to collect), "Potwierdź płatność" and
    "płatności gotówkowych do potwierdzenia" (cash payments to confirm). Statuses: "Opłacone, Płatność w
    klubie, Nieopłacone, Zwrócone". Methods: "Przelewy24, Karnet, Gotówka, Karta benefit.", plus "Ręczna"
    (manual).
  - A player who picked pay-at-club shows "Wybrano płatność w klubie". The desk's confirmation logs
    "Recepcja potwierdziła gotówkę" with who confirmed it ([panel bundle][t4u-panel]).
- **Playmore [POLICY]**
  - "Dodaj płatność" with "Karnet, Gotówka, Przelew, Karty płatnicze, Inne" (pass, cash, transfer, card,
    other); "Zapłaci później" (will pay later).
  - "Dokument sprzedaży: Faktura / Rachunek / Paragon" (sales document: invoice, bill, receipt)
    ([calendar strings][pm-cal]).
  - "Kasa fiskalna — Sprzedawaj produkty… i drukuj paragony fiskalne bezpośrednio z systemu", through
    Fakturownia.pl or wFirma ("Fiskalizuj paragon" — fiscalise the receipt) ([fiscal strings][pm-fisc]).
- **Playtomic [POLICY]**
  - "Click Mark as paid… Choose the right method (e.g., Card, Cash, Transfer, Wallet…)".
  - For an online split booking, a share paid at the club must be marked "within 2 hours of the match
    ending — otherwise the system will automatically charge the remaining balance to the booking owner"
    ([Mark as paid, 2026-10-05][pt-paid]).
  - Clubs "create their own custom methods" ([Payment methods, 2026-10-05][pt-methods]).
  - A Cash Register shows "Expected Cash… Actual Cash… Difference" ([Cash Register,
    2026-10-05][pt-cash]).
  - Carried: nothing for Polish fiscal rules ([local-market](../games-and-fill-in/topics/local-market.md)).
- **MATCHi [POLICY]:** "Marking a booking as paid does not trigger any charge — it's purely a
  record-keeping flag"; "no separate log entry is created showing who made the change"
  ([Mark as paid][mx-paid]). At creation it "records a captured cash payment" ([random admin
  booking][mx-admin]).
- **kluby.org [POLICY]**
  - "Możliwość dodania przy rezerwacji kilku płatności na jednego klienta" — several payments per client
    (2017).
  - "Integracja z kasą fiskalną" and "Drukowanie paragonów" — fiscal-register integration and receipt
    printing (2020).
  - "Paragon łączący rezerwację z zakupami w sklepie" — one receipt for the booking and shop items (2022)
    ([changelog 2017][kl-2017], [2020][kl-2020], [2022][kl-2022]).
- **Eversports [POLICY]:** "OPEN means that the client will pay at a later date"; "Credit card (on
  site)… on-site credit card device", with no integration described ([on-site methods][ev-onsite]).

**What a Kraków desk does today**
- **[POLICY]** Payment methods in the clubs' rules:
  - Garden Padel: "płatności online (Przelewy24) lub w recepcji (karta/gotówka)" ([regulamin
    4][garden-reg]).
  - Paolo: "online (DotPay), przelewem, gotówką lub kartą w recepcji" ([regulamin][paolo-reg]).
  - Squash4You: "przelewem oraz bezpośrednio w recepcji klubu gotówką lub kartą" ([regulamin][s4y-reg]).
- **[PRICE]** Online costs less: Atras charges 45–103,50 zł online against 50–115 zł in the club
  ([cennik][atras-cennik]).
- **[LAW] carried:** a sale part-paid at the desk goes through the cash register; only a sale paid fully
  online is exempt ([local-market](../games-and-fill-in/topics/local-market.md)).

**What it means for the player app.** *Reading:* a share paid in cash must show as paid in the app. At
tenis4U a player can even choose "pay at the club" in the app and the desk confirms it.

**Market signal.** Marking cash and card: table stakes. Polish fiscal receipts from the desk: a
differentiator in Poland (Playmore, kluby.org).

## 7. A payment link with a deadline

**What it covers.** The desk books a phone caller and the system sends a link; unpaid by the deadline,
the booking is deleted and the hour freed.

**Who has it**
- **tenis4U [POLICY]**
  - "Gracz otrzyma 60 min na opłacenie online"; the tooltip: "Użytkownik otrzyma link do płatności.
    Rezerwacja zostanie usunięta jeśli płatność nie zostanie wykonana w ciągu 60 minut." — the user gets a
    link, and the booking is deleted if unpaid within 60 minutes.
  - The booking shows a countdown ("{h} godz {m} min", "Czas minął") and the statuses "Oczekuje na
    płatność" and "Wygasła" (awaiting payment, expired).
  - Per court: "Ile godzin przed startem anulować nieopłacone rezerwacje (puste = wyłączone)" — cancel
    unpaid bookings N hours before the start ([panel bundle][t4u-panel]).
- **Playmore [POLICY]**
  - "Klient płaci online — Klient dostanie SMS z linkiem do płatności. Jeśli nie zapłaci w ciągu {minutes}
    min, rezerwacja zostanie automatycznie anulowana, a termin zwolniony." — the client gets an SMS link;
    unpaid in N minutes, the booking is cancelled and the slot freed.
  - "Termin płatności ogłaszamy w tym SMS-ie, więc przy płatności online jest on wymagany" — the deadline
    is announced in the SMS, so a phone is required.
  - Refused for a zero price, a missing phone, or a number that cannot take SMS.
  - Delivery is tracked: "SMS z linkiem do płatności wysłany o {time}", or "nie wyszedł… Skopiuj link i
    wyślij go klientowi inaczej" (copy the link and send it another way). "Wyłącz auto-anulowanie" turns
    the auto-cancel off ([calendar strings][pm-cal]).
  - Club setting: "Płatność online przy rezerwacjach recepcyjnych — Domyślnie wymagaj płatności online —
    Czas na opłacenie … min" — require online payment by default, minutes to pay ([venue
    settings][pm-venue]).
  - The log reason: "brak płatności w terminie" (not paid in time). Carried: a player's own online booking
    lapses after 30 minutes ([platforms](../games-and-fill-in/topics/platforms.md), read 2026-10-08).
- **MATCHi [POLICY]:** "select payment link as the payment method when creating or editing a booking";
  the customer must be logged in; "Payment links remain valid for up to 240 days"; "the payment link does
  not expire when the booked time has passed" ([payment links][mx-links]).
- **Playtomic [ABSENT]:** a payment link for a desk booking (club help searched "payment link"). Players
  of a club-made recurring series pay in the app, with payments "not automatically enforced"
  ([Recurring][pt-recurring]).
- **kluby.org [POLICY]:** "Wymaganie płatności ONLINE" (2019) and "Wysyłanie płatności klienta
  (sms/e-mail)" — sending the client's payment by SMS or email (2021) ([changelog 2019][kl-2019],
  [2021][kl-2021]).

**What a Kraków desk does today.**
- **[POLICY]** Garden Padel: "Rezerwacja jest ważna po dokonaniu płatności online (Przelewy24) lub w
  recepcji" — valid once paid online or at the desk ([regulamin 4][garden-reg]).
- **[POLICY]** Fame Sport's fixed bookings: "Nieopłacona rezerwacja może zostać anulowana po upływie
  terminu wskazanego przez Klub" — an unpaid booking may be cancelled after a deadline the club sets
  ([regulamin III.3][fame-reg]).

**What it means for the player app.** *Reading:* the link lands where the player has an account, which is
an app notice at tenis4U and Playmore (push, else SMS). A guest needs SMS. The countdown is the player's to
see.

**Market signal.** A differentiator, and Polish: both Kraków systems have it. The others either keep the
link open (MATCHi) or have none (Playtomic).

## 8. Partial payment, deposits and debts

**What it covers.** Part paid now and the rest later; a deposit; a running debt that blocks a customer.

**Who has it**
- **Playmore [POLICY]**
  - Part payments: "Płatność została dodana - pozostało {x}" (payment added, X left), "Suma wpłat",
    "Pozostało do zapłaty", "Rezerwacja nadpłacona" (overpaid). "Mimo anulowania można dodać płatność (np.
    kara za anulowanie lub opłata manipulacyjna)" — a payment can be added after a cancel, e.g. a fee
    ([calendar strings][pm-cal]).
  - Debts: "Klient ma zaległości: {amount}" and the filter "Oznaczaj dłużników". Setting: "Blokowanie
    użytkowników z zaległościami — Nieopłacone rezerwacje" ([venue settings][pm-venue]). Reports
    "Nieopłacone rezerwacje" and "Dłużnicy" ([report strings][pm-reports]).
- **tenis4U [POLICY]:** "Zapłacono kwotę" (amount paid) on fixed bookings and "50% częściowo" (partly
  paid). Desk warnings: "Ostrzeżono ({n}/3 ostrzeżeń)", "Ostrzeżono. Użytkownik został zbanowany" — warned;
  three warnings ban the user ([panel bundle][t4u-panel]).
- **Playtomic [POLICY]:** "Partially paid", "Paid with debt" ([bookings strings][pt-bookings],
  [schedule strings][pt-schedule]); "This player has unpaid debts and is blocked from being added to
  Matches". Carried: card-on-file debts ([competitor-club](../games-and-fill-in/topics/competitor-club.md)).
- **kluby.org [POLICY]:** online prepayment "dobrowolne lub wymagane 25%/50%/100%" (optional, or 25, 50 or
  100 % required; carried). "Lista zaległości" (arrears list) ([funkcje][kl-funkcje]). "Powiadomienia SMS
  o zaległościach" (SMS about arrears, 2018). Carried: blocks on indebted clients
  ([platforms](../games-and-fill-in/topics/platforms.md)).
- **Eversports [POLICY]:** an "OPEN" sale makes "an open unpaid invoice" ([on-site methods][ev-onsite]).
  "How to Process Partial Payments" exists (title only, [Financials][ev-fin]).
- **MATCHi [ABSENT]:** a deposit or part payment at booking (help searched "unpaid", "cash").

**What a Kraków desk does today**
- **[POLICY]** Fame Sport: "Prawo do dokonywania kolejnych rezerwacji może zostać ograniczone wobec osób
  posiadających wymagalne zaległości" — booking can be restricted for people in arrears — and statutory
  interest ([regulamin II.7–8][fame-reg]).
- **[POLICY]** Paolo: "Płatność za nieterminową anulację lub nieobecność należy uiścić do 7 dni przelewem
  lub w recepcji" — a late cancel or no-show is owed within 7 days, by transfer or at the desk
  ([regulamin][paolo-reg]). Squash4You says the same ([regulamin 5e–f][s4y-reg]).
- Carried: Atras's desk tells the debtor the same or the next day
  ([local-market](../games-and-fill-in/topics/local-market.md)).

**What it means for the player app.** *Reading:* a debt the desk records needs to reach the player and
gate the next yes, as Playmore's block and Playtomic's debts do.

**Market signal.** Debts and blocks: table stakes in Poland. Part payments at the desk: common. A required
deposit: rare (kluby.org).

## 9. A card terminal, or Tap to Pay, in Poland

**What it covers.** Taking a card at the desk through Stripe, so the payment lands on the booking — Stripe
Terminal readers or a phone used as a reader.

**Who has it**
- **Stripe [DOCS], availability in Poland**
  - Readers: "BBPOS WisePOS E, Stripe Reader T600, Stripe Reader S710, Stripe Reader S700, BBPOS WisePad
    3, Tap to Pay on Android, Tap to Pay on iPhone" ([set up your reader][st-readers]).
  - Tap to Pay on iPhone lists Poland among generally available countries. "Stripe includes Tap to Pay on
    iPhone in the Terminal iOS SDK and the Terminal React Native SDK, and enables payments directly in
    your iOS mobile app" ([Tap to Pay, iOS][st-ttp-ios]). The same holds for Android ([Android][st-ttp-and]).
  - No code: "Tap to Pay with Stripe Dashboard lets you process in-person, contactless payments using only
    your phone… available on iOS and Android in all countries where Tap to Pay is supported"
    ([no-code in-person][st-nocode]).
- **Stripe [DOCS], with Connect:** "If you use direct charges, you submit Terminal API requests to
  configure readers and accept payments using your platform's API key and the Stripe-Account header";
  "Terminal connected accounts must have the card_payments capability"; in Standalone mode "you (not the
  connected account) must register the reader" ([Terminal with Connect][st-connect]).
- **[ABSENT]** Terminal or Tap to Pay fees for Poland: [stripe.com/en-pl/pricing][st-pricing] lists only
  online rates (1.5 % + 1 zł for standard EEA cards, BLIK 1.6 % + 1 zł).
- **Playtomic [POLICY]:** "Playtomic Terminal (United States only) lets clubs accept card payments onsite
  through a physical card reader, processed through Stripe" ([Payment methods][pt-methods]).
- **Playmore, tenis4U, kluby.org, MATCHi [ABSENT]:** an integrated card reader. Playmore's "Karty
  płatnicze" is a manual method; tenis4U has none; MATCHi help searched "terminal"; kluby.org's
  integrations list remote control, payments, SMS and invoices.
- **Eversports [POLICY]:** a card device on site, recorded by hand ([on-site methods][ev-onsite]).

**What a Kraków desk does today.** The desks take cards (Garden Padel, Paolo, Squash4You above).
*Reading:* that is on a bank's POS terminal separate from the booking system, since none of their
systems integrates one.

**What it means for the player app.** *Reading:* the same club account receives the app's shares and a
desk card payment only if the desk charges through Stripe. Tap to Pay would have to live in a native app
(Rakieta's is React Native), not in the club website.

**Market signal.** Rare: one rival, in the US only.

## 10. Moving a booking

**What it covers.** Drag and drop, another court, another time or day, resizing; what happens to the price,
and who is told.

**Who has it**
- **Playtomic [POLICY]**
  - "To move a reservation within the same day, simply drag and drop… also… to a different court." For
    another day, Reschedule: "Select the new time by drawing on a date and time you want".
  - "Past reservations can also be rescheduled"; "All customers in the reservation will get an email
    notification" ([Reschedule][pt-resched], [schedule strings][pt-schedule]).
  - Refusals: "Moving an event to a court with a different size is not allowed", "…with a different sport
    is not allowed". On a paid booking: "This booking has been paid and the price can't be updated…
    Move anyway" ([schedule strings][pt-schedule]).
- **tenis4U [POLICY]**
  - "Upuść rezerwację na wolny termin" (drop on a free slot), "Nie można przenosić rezerwacji w
    przeszłość" (not into the past), "Nie można edytować rezerwacji z przeszłości", "Wskazano termin poza
    godzinami otwarcia kortu" (outside opening hours).
  - The dialog "Przenieś rezerwację" → "Przenieś do: Stanowisko: Data:", and "Wydłuż/Skróć" (extend or
    shorten) ([panel bundle][t4u-panel]).
  - Carried: no switch to tell the players ([gaps-CLUBBOOK](../games-and-fill-in/topics/gaps-CLUBBOOK.md)).
- **Playmore [POLICY]**
  - Drag, resize and a "Przenieś na nowy termin" form that checks "czy termin jest wolny" (whether the
    slot is free).
  - A summary "Cena przed / Cena po / do dopłaty / do zwrotu" (price before and after, to collect, to
    refund).
  - "Powiadom klienta o zmianie (SMS, push, e-mail)" — tell the client of the change.
  - Series moves: "Całą serię można przesunąć najwyżej o 6 dni" — a whole series moves at most 6 days.
  - "Klub wyłączył przesuwanie rezerwacji przeciąganiem" — the club has switched dragging off
    ([calendar strings][pm-cal]).
  - Why a club would: "cena zależy od godziny i przeciągnięcie łatwo zostawia niedopłatę albo nadpłatę"
    — the price depends on the hour, and a drag easily leaves an under- or overpayment ([venue
    settings][pm-venue]).
- **MATCHi [POLICY]:** "Click Move"; "The price does not change when you move a booking"; "Moving onto
  an occupied slot swaps the bookings"; "Every move is logged" ([Move a booking][mx-move]).
- **kluby.org [POLICY]:** "Możliwość zamiany miejscami rezerwacji na grafiku" — swap two bookings on the
  schedule (1 Aug 2016) ([changelog 2016][kl-2016]).

**What a Kraków desk does today**
- **[POLICY]** Fame Sport: "Zmiana numeru kortu w ramach obiektu na kort o porównywalnych warunkach do gry
  nie stanowi odwołania rezerwacji" — another comparable court is not a cancellation; and "Klub
  poinformuje klienta możliwie jak najwcześniej" — the club tells the client as early as possible
  ([regulamin II.17, II.20][fame-reg]).
- **[POLICY]** KS Grzegórzecki adds "nie wymaga zgody osoby dokonującej rezerwacji" — it needs no consent
  from the booker ([regulamin II.13][ksg-reg]).

**What it means for the player app.** *Reading:* a moved game must reach every seat-holder — email and
app at Playtomic, SMS, push and email at Playmore. Kraków's written rules let the desk change the court
without asking.

**Market signal.** Drag and drop: table stakes. A price prompt and a notify switch: a differentiator.
A club switch to forbid dragging: rare.

## 11. Cancelling, refunds from the desk, and telling the player

**What it covers.** The desk calls a booking off, with or without money back, with a reason, telling
the player; and refunds started from the desk.

**Who has it**
- **Playtomic [POLICY]**
  - "When you cancel a paid booking… If the payment was made online it will be refunded automatically and
    if it was paid at the club you must refund it to the client" ([schedule strings][pt-schedule]).
  - A single share is refunded by "Remove participant" ([Mark as paid][pt-paid]).
  - Carried: a club cancel refunds in full, and there is no reason field
    ([competitor-club](../games-and-fill-in/topics/competitor-club.md)).
- **Playmore [POLICY]**
  - "Anuluj na czas" / "Anuluj nie na czas" (on time / late), suggested from the club's free window
    ("Minął próg {h} h przed grą — sugerowane „Anuluj nie na czas”"). "Wyślij SMS" (send an SMS).
    "Zmień na anulowaną na czas… Ta operacja jest nieodwracalna" — change to on time; irreversible.
  - Who refunds:
    - "Klient zapłacił online, a pieniądze trafiły prosto na konto klubu… zwrot robi klub — przelewem albo
      na miejscu" — paid online straight to the club, so the club refunds, by transfer or on the spot.
    - "Playmore zlecił zwrot tą samą drogą… Pieniądze zejdą z salda klubu w Stripe" — Playmore refunds by
      the same route, out of the club's Stripe balance.
    - "Wpłatę przyjętą w recepcji usuniesz koszem w historii płatności" — a desk-taken payment is deleted
      from the payment history.
  - The log names "Anulowane przez pracownika / klienta / automatycznie przez system" — by an employee,
    the client, or the system ([calendar strings][pm-cal]).
- **tenis4U [POLICY]**
  - "Anulować rezerwację ze zwrotem?" / "Anulować rezerwację BEZ zwrotu?" (with or without refund), with a
    warning from the server. "Rezerwacja zostanie trwale usunięta!" — permanently deleted.
  - The log line "Anulowano rezerwację" shows a reason. The club-wide history types are `USER_CANCEL`,
    `ADMIN_CANCEL` and `AUTO_UNPAID` ([panel bundle][t4u-panel]).
  - Carried: no desk refund once the booking has started
    ([gaps-CLUBBOOK](../games-and-fill-in/topics/gaps-CLUBBOOK.md)).
- **MATCHi [POLICY]:** full refund, refund minus a fee, or none, with an optional message (carried). "A
  record of the cancellation is kept… who cancelled what and when" ([extra info on a booking][mx-info]).
- **kluby.org [POLICY]:** "Masowe odwoływanie rezerwacji" (mass cancelling, 2016); "Wyłączenie lub
  ograniczenie możliwości odwolywania rezerwacji dla pracownika" (staff may be barred from cancelling,
  2018) ([changelog 2016][kl-2016], [2018][kl-2018]).

**What a Kraków desk does today**
- **[POLICY]** Fame Sport and KS Grzegórzecki offer "inny kort lub termin" (another court or time), else a
  credit or a refund, "według wyboru klienta" — at the client's choice ([Fame II.18–19][fame-reg],
  [KSG II.12][ksg-reg]).
- **[POLICY]** Squash4You's desk cancels late "w trybie warunkowym" (conditionally) and tries to resell
  the slot ([regulamin 5c][s4y-reg]).
- **[POLICY]** Atras: free cancellation until "23 godzin przed… telefonicznie oraz w recepcji" against "24
  godzin… przy użyciu aplikacji" — an hour more by phone or at the desk than in the app
  ([regulamin §6][atras-reg]).

**What it means for the player app.** *Reading:* a desk cancel has to reach every seat-holder and say
where the money goes. Playmore's split — the club refunds money it took, Stripe refunds online — is the
one Rakieta's direct charges would face.

**Market signal.** Cancel with or without refund: table stakes. A suggested on-time or late status, and a
reason in the log: a differentiator.

## 12. Undo

**What it covers.** Reversing the desk's last act — a drag, a payment marked by mistake.

**Who has it**
- **Playmore [POLICY]:** after a drag, "Cofnij" → "Przesunięcie cofnięte" (move undone). It fails safe:
  "Nie można cofnąć — stary termin jest już zajęty. Termin zostaje w nowym miejscu" — the old slot is
  taken, so the booking stays. Undo also covers a marked arrival and a card scan ("Cofnij odbicie")
  ([calendar strings][pm-cal]).
- **Playtomic [POLICY]:** no undo. "Undo a payment or change the payment method… by removing the
  participant", then add them back and mark again ([Mark as paid][pt-paid]). In the till: "The payment
  method of a recorded sale can't be edited" ([Cash Register][pt-cash]).
- **MATCHi [POLICY]:** "There's no confirmed way to reverse this back to unpaid" ([Mark as
  paid][mx-paid]).
- **tenis4U [ABSENT]:** "Cofnij" or any undo in the panel bundle.
- **kluby.org [ABSENT]:** in the changelog.

**The desk's day with it.** *Reading:* a mis-drag at the desk is the common slip. The rivals without undo
fall back on a fresh move or a remove-and-re-add.

**What a Kraków desk does today.** **[ABSENT]** No source.

**What it means for the player app.** *Reading:* an undone move must not leave the player with two notices
— Playmore sends notices only when told to.

**Market signal.** Rare (Playmore).

## 13. The audit log: who changed what

**What it covers.** A booking's history and the club-wide record of the desk's acts.

**Who has it**
- **Playtomic [POLICY]**
  - "Booking History tab… all changes made to the reservation, including payments. The system
    automatically logs every action taken by the customer or club" ([Booking History][pt-history-art]).
  - Lines read "Start time updated from {oldTime} to {newTime} by {requestUserName} ({role})", "Price
    updated…", "Court updated…", "Payment Removed… by…", "Match canceled… automatically by Playtomic"
    ([history strings][pt-history]).
- **Playmore [POLICY]**
  - A "Historia" tab with "Utworzono / Zaktualizowano / Usunięto / Przekwalifikowano" (created, updated,
    deleted, reclassified) and "Wykonane przez {name}" (done by).
  - Field names include "Cena", "Czas rozpoczęcia", "Kort", "Status płatności", "Status anulowania",
    "Stworzona przez" and "Źródło rezerwacji" (price, start, court, payment status, cancel status, created
    by, source).
  - "Starsze zmiany (sprzed 90 dni)" — older changes, beyond 90 days ([calendar strings][pm-cal]).
  - Carried: owner reports on privileged cancellations and last-minute changes
    ([gaps-CLUBBOOK](../games-and-fill-in/topics/gaps-CLUBBOOK.md)).
- **tenis4U [POLICY]**
  - Each booking has events: "Utworzono rezerwację", "Przeniesiono rezerwację", "Anulowano rezerwację"
    (with a reason), "Zmiana rezerwacji", payments, refunds and "Recepcja potwierdziła gotówkę". Each line
    names the actor and the source: "Aplikacja", "Panel", "System".
  - A club-wide "Historia" lists "USUNIĘCIE / ANULOWANIE / EDYCJA" (deleted, cancelled, edited) by
    "użytkownik" or "panel", time-stamped to the second ([panel bundle][t4u-panel]).
- **MATCHi [POLICY]:** "Every move is logged"; marking paid creates "no separate log entry… showing who
  made the change" ([Move][mx-move], [Mark as paid][mx-paid]).
- **kluby.org [POLICY]:** "Zapisywanie informacji o zmianach w rezerwacji" (changes to a booking saved,
  1 Sep 2017); "Skracanie rezerwacji widoczne w historii odwołanych i przeniesionych rezerwacji" (shortened
  bookings in the history of cancelled and moved ones, 2020) ([changelog 2017][kl-2017],
  [2020][kl-2020]).
- **CourtReserve [POLICY]:** waitlist activity appears "on the audit log" ([Court Waitlisting][cr-wait]).

**The desk's day with it.** *Reading:* with one shared login per club (Rakieta today), every line says
"the club". The rivals name the employee: Playtomic's admins are separate (carried) and Playmore's
reports watch staff.

**What a Kraków desk does today.** **[ABSENT]** No source. Kraków's desks run the logs above.

**What it means for the player app.** *Reading:* the same log answers a player who disputes "I didn't
cancel that". tenis4U's source label (app, panel or system) is exactly that answer.

**Market signal.** A per-booking history: table stakes. Field-level history with the employee: a
differentiator.

## 14. Printing or exporting the day

**What it covers.** The day's sheet for the desk or the owner — a print, a PDF, a CSV.

**Who has it**
- **tenis4U [POLICY]:** "Drukuj do PDF" saves the calendar view as `Tenis4u-DD-MM-YYYY.pdf` (A4 portrait).
  "Pobierz jako CSV" is the users list ([panel bundle][t4u-panel]).
- **Playtomic [POLICY]:** the Booking List filters by "Creation Date or Service Date" and exports "JSONL or
  CSV" ([Booking List][pt-list]). **[ABSENT]** A printed day (club help searched "print": invoicing and FAQ
  only).
- **Playmore [POLICY]:** "Raport dzienny — Kompleksowe podsumowanie dnia z porównaniami" (daily report,
  with a PDF); "XLSX do dalszej pracy albo PDF gotowy do druku (A4 w poziomie)" — XLSX, or a printable A4
  landscape PDF ([report strings][pm-reports]); a client's bookings as CSV or XLSX ([client
  strings][pm-clients]). It also draws "Wolne terminy na Instagram" — free slots as an image ([calendar
  strings][pm-cal]).
- **MATCHi [POLICY]:** "Click More to send a message or text to a customer, or to export your
  reservations" ([Schedule][mx-schedule]).
- **kluby.org [POLICY]:**
  - "Wprowadzenie raportu danego dnia lub przefiltrowanych rezerwacji" — a report of the day or of
    filtered bookings (1 May 2017).
  - "Generowanie do PDF historii przefiltrowanych rezerwacji" — a PDF of filtered booking history (1 Jul
    2017).
  - "Eksport historii rezerwacji do Excela" (2021); "Pobranie zestawienia dziennego do Excela" — the daily
    summary in Excel (2022) ([changelog 2017][kl-2017], [2021][kl-2021], [2022][kl-2022]).

**What a Kraków desk does today.** **[ABSENT]** No club rule mentions a printed day.

**What it means for the player app.** None.

**Market signal.** An export: table stakes. A printed day sheet: a differentiator (tenis4U, Playmore,
kluby.org).

## 15. Notes on a booking

**What it covers.** Text on a booking — for the desk only, or for the player too.

**Who has it**
- **Playtomic [POLICY]:** "Notes (public for customers)" and "Private notes are only visible to club
  admins"; a note shows as a dot on the tile, and the schedule searches "Description, notes, user email,
  user phone" ([schedule strings][pt-schedule]).
- **tenis4U [POLICY]**
  - "Uwagi": "Treść niewidoczna dla gracza, podgląd tylko w panelu" — hidden from the player.
  - A message: "Treść widoczna dla gracza w szczegółach rezerwacji" — shown to the player.
  - The tooltip reads "Uwagi: … Wiadomość: …". Per court, "Komunikat po rezerwacji" (a message after
    booking) ([panel bundle][t4u-panel]).
- **Playmore [POLICY]:**
  - "Adnotacja" on a booking (up to 255 characters), a client note ("Dodaj adnotację do klienta…") and a
    note for a fixed series; shown on hover.
  - "Notatka" as its own calendar entry; "Notatka o uczestniku — Widoczna tylko dla recepcji" (a note on a
    participant, desk only).
  - A "Lista zadań" (to-do list) whose done tasks "automatycznie usuwane po 72 godzinach" — auto-deleted
    after 72 h ([calendar strings][pm-cal]).
- **MATCHi [POLICY]:** "Comments… If Show comment was enabled, the comment is also visible directly on
  the schedule" ([extra info][mx-info]).
- **kluby.org [POLICY]:** "Możliwość pokazania klientowi komentarza płatności" — show the client a payment
  comment (2016) ([changelog 2016][kl-2016]).

**What a Kraków desk does today.** *Reading:* the clubs' rules say nothing. The tenis4U and Playmore
desks have private and public notes.

**What it means for the player app.** *Reading:* a public note ("bring your own balls", "court 3 tonight")
is something the player reads in the game's detail.

**Market signal.** Table stakes, including the split between private and public.

## 16. Recurring bookings ("repeat this booking")

**What it covers.** A weekly fixed slot for a season or a set number of weeks, and how its exceptions are
handled.

**Who has it**
- **Playtomic [POLICY]:** "Recurring Series" with a title, court and payment type; edits ask "This event"
  or "This and following events". Payments "are not automatically enforced… The club will need to follow
  up"; "Can players create recurring reservations from the app? No"; "Can you mark more than one booking
  as paid at the same time? No" ([Recurring][pt-recurring]).
- **Playmore [POLICY]**
  - "Powtarzaj rezerwację" until a date or "do odwołania" (until cancelled): "Terminy założymy na rok do
    przodu, a co noc dołożymy kolejny tydzień" — a year ahead, plus a week every night.
  - Conflicts: "Utwórz mimo kolizji terminów" — create despite clashes.
  - Moving a series: one notice ("Klient dostanie jedno powiadomienie — o pierwszym terminie"), at most 6
    days ([calendar strings][pm-cal]).
- **tenis4U [POLICY]:** "Dodaj rezerwację stałą", "Tworzenie kilku rezerwacji stałych" (several fixed
  bookings at once), and "Aktywuj opcję odrabiania": "ustalasz jej cenę za cały okres… Po odwoływaniu
  rezerwacji pojedynczej gracz ma możliwość odrobienia niewykorzystanego terminu" — one price for the whole
  period, and a cancelled date can be made up ([panel bundle][t4u-panel]). Carried: a separate cut-off for
  fixed bookings ([platforms](../games-and-fill-in/topics/platforms.md)).
- **MATCHi [POLICY]:** "Subscriptions" are bounded by a season; "If there are conflicts… you can either
  overwrite the conflicting bookings… Overwriting cancels the conflicting bookings". On creation there is an
  optional email "including a payment link" or "Mark it as paid immediately (cash)"
  ([Subscriptions][mx-subs]).
- **kluby.org [POLICY]:** "Rezerwacje cykliczne", "Abonamenty z funkcją odrabiania" (subscriptions with
  make-up) ([funkcje][kl-funkcje]); "Podczas dodawania stałych rezerwacji komunikat o zajętych już
  terminach" — a notice of already-taken dates while adding (2017).

**What a Kraków desk does today**
- **[POLICY]** Fame Sport: fixed bookings "na okres 12 tygodni, sezon letni, sezon zimowy" (12 weeks, a
  summer or a winter season). A single date is free to cancel until 48 h before. The holder "może mieć
  pierwszeństwo w przedłużeniu" (may have priority to renew) ([regulamin III][fame-reg]).
- **[POLICY]** KS Grzegórzecki: the same 48 h ([regulamin III][ksg-reg]); **[PRICE]** "Abonament na 1h w
  na cały sezon" — an hour a week for the season ([cennik][ksg-cennik]).
- **[POLICY]** Garden Padel: "Rezerwacje stałych terminów można uzgodnić indywidualnie z administratorem"
  — fixed slots by arrangement ([regulamin 4][garden-reg]).

**What it means for the player app.** *Reading:* fixed slots take the prime hours. The Games deck sees
them only as taken hours — unless a fixed group's game is to be played by Rakieta's players.

**Market signal.** Table stakes. Rolling "until cancelled": a differentiator (Playmore). Make-up of
cancelled dates: rare (tenis4U, kluby.org).

## 17. A waiting list for a full hour

**What it covers.** A player or the desk queues for a taken court hour and is told when it frees.

**Who has it**
- **CourtReserve [POLICY]**
  - "The Court Waitlist allows clubs to provide players with easy access to the court waitlist"; "Each
    waitlist can include up to 25 player names".
  - When a court frees, "CourtReserve sends an email to everyone on the waitlist at the same time".
  - Admins see it "on the left side of the scheduler" and can "Create a reservation for a player from the
    waitlist" ([Court Waitlisting, 2026-04-30][cr-wait]).
- **Playmore [POLICY]**
  - For a taken court hour: "E-mail do gracza, który w aplikacji obserwuje zajęty termin. Wychodzi
    natychmiast, gdy rezerwacja obejmująca ten termin zostanie anulowana" — an email to a player watching
    a taken hour, sent the moment it is cancelled ([venue settings][pm-venue]).
  - For classes: "Lista rezerwowa… wszyscy z listy dostają powiadomienie — miejsce dostaje ten, kto
    zapisze się pierwszy" — everyone on the list is told; first to sign up gets it.
  - "Na tę listę gracz zapisuje się sam w aplikacji — recepcja nikogo tu nie dopisuje" — players add
    themselves in the app, and the desk adds nobody ([calendar strings][pm-cal]).
- **kluby.org [POLICY]:** "Dodanie listy oczekujących" (1 Apr 2017) under Rezerwacje ([changelog
  2017][kl-2017]); help topic "2.4. Lista oczekujących" is a video only ([pomoc][kl-pomoc]).
- **tenis4U [ABSENT]** for courts: "Lista rezerwowa" appears only for tournaments and classes ([panel
  bundle][t4u-panel]).
- **Playtomic [ABSENT]** for courts (player and club help searched "waiting list", "notify me"). Premium
  offers "Priority Alerts… when matches become available" ([Premium][pt-premium]).
- **MATCHi [ABSENT]** for courts; activities only (carried, [platforms](../games-and-fill-in/topics/platforms.md)).

**What a Kraków desk does today.** **[POLICY]** Squash4You's desk resells a late-cancelled slot itself,
and "termin ten będzie również widoczny w grafiku on-line dla wszystkich Klientów jako dostępny" — it shows
online as free ([regulamin 5c][s4y-reg]).

**What it means for the player app.** *Reading:* a freed hour already goes back to sale everywhere. A
queue adds a push to whoever waited — the same "first to tap wins" shape as Rakieta's Fill in.

**Market signal.** Rare for courts (CourtReserve, Playmore's watch, kluby.org). Common for classes.

---

## Rivals × features

`Y` has it · `—` looked for, not found · `?` could not be read · `n/a` not applicable.

| Feature | Playtomic | Playmore | tenis4U | kluby.org | MATCHi | Others |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Day view, courts side by side | Y | Y | Y | Y | Y | |
| 1. Week view | — | ? | Y | Y (2023) | — | |
| 1. Colour by type / channel / club meaning | type | channel + payment | 20 club colours | client colour (2018) | type | |
| 2. Phone or tablet use | Y (web) | Y (touch drag, guard mode) | Y (mobile edit mode) | Y (responsive, 2020) | — | |
| 3. Auto-refresh | 30 s | 300 s | 10 s + banner | ? | ? | |
| 3. Desk alerted of a new booking | email per admin | SMS to an employee | banner; SMS to club | staff told of cancels (2020) | email | |
| 4. Guest without account | name | phone + first and last name required | name, phone optional | phone required (2017) | first and last name | |
| 5. Several lengths / half-hour grid | Y / Y | Y / Y (15, 30, 60 step) | Y / Y | Y / Y | Y / Y (5-min) | |
| 5. Buffer between bookings | — | — | — | ? | Y | |
| 6. Mark cash or card | Y | Y | Y | Y | Y (no log) | Eversports Y |
| 6. Polish fiscal receipt | — | Y (Fakturownia, wFirma) | — | Y (2020) | n/a | Eversports DE, AT, ES |
| 7. Payment link deleting an unpaid booking | — | Y (club-set min, SMS) | Y (60 min) | ? | link, no deletion | |
| 8. Part payment / debts | Y / Y | Y / Y | Y / warnings | Y / Y | — / ? | Eversports open invoice |
| 9. Integrated card reader | US only | — | — | — | — | Stripe: PL readers + Tap to Pay |
| 10. Drag and drop / other court | Y (same day) | Y (switch-off) | Y | swap (2016) | Move button, swap | |
| 10. Price prompt / notify switch | Y / always email | Y / Y | — / — | ? | price fixed / ? | |
| 11. Cancel with or without refund | full refund | on time / late | with / without | mass cancel | 3 options | |
| 12. Undo | — | Y | — | — | — | |
| 13. Audit log with the employee | Y | Y (field level, 90 d+) | Y (+ club history) | Y (2017) | moves only | CourtReserve |
| 14. Print or export the day | CSV, JSONL | PDF, XLSX | PDF | PDF, Excel | export | |
| 15. Private and public notes | Y | Y (+ client, to-do) | Y | Y | comment | |
| 16. Recurring | Y | Y (until cancelled) | Y (make-up) | Y (make-up) | Y (season) | |
| 17. Court waiting list | — | watch a taken hour | — | Y (2017) | — | CourtReserve Y |

## Gaps

- **Playmore:** the default for "Czas na opłacenie" (the desk link's minutes; the code holds no default),
  and whether Manager offers a week view.
- **MATCHi:** how often the admin schedule refreshes, and whether admins work on a phone.
- **kluby.org:** its schedule's interface text. Its help is video only and its changelog stops at 2023, so
  its colours, guest fields, payment link and undo are unknown.
- **Kraków padel clubs' own price lists and rules:** Bajada, Padel House, Morelowa 34 and Libertów
  publish only Facebook or Instagram (Playmore's page data names those as their websites), so their
  lengths rest on PADO's "1 hour" listings. SAO states no length. Park Jordana (ZZM, on tenis4U) publishes
  none.
- **What tenis4U actually allows per club:** the panel shows the settings, not each club's values.
  Reading them would mean calling tenis4U's API, which its terms forbid. Playmore's [60,90,120] for tenis4U
  clubs is Playmore's own data.
- **Stripe's in-person rates for Poland** (not on the Polish price page), and whether a club on direct
  charges can use Tap to Pay in the Stripe Dashboard app against its own account without a platform app.
- **Playtomic:** a payment link for desk bookings, and any undo.
- **tenis4U's payment link:** which channel it uses (SMS, push or email) and what the player sees.
- **Kraków desks in practice:** the device at the desk, whether staff keep a paper day sheet, how a
  walk-in is recorded, and whether desk card payments go through a separate bank terminal. No club rule,
  review or photo answers these. They are the "Ask a real club" questions.
- **A waiting list for a full court hour in Poland:** whether kluby.org's "Lista oczekujących" covers
  courts or only classes.

[pt-basics]: https://helpmanager.playtomic.com/hc/en-gb/articles/20560058451985-Schedule-basics
[pt-settings]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535294627985-Schedule-Settings
[pt-schedule]: https://manager.playtomic.io/locales/en/schedule.json
[pt-common]: https://manager.playtomic.io/locales/en/common.json
[pt-history]: https://manager.playtomic.io/locales/en/match_history_record.json
[pt-bookings]: https://manager.playtomic.io/locales/en/bookings.json
[pt-customers]: https://manager.playtomic.io/locales/en/customers.json
[pt-mobile]: https://helpmanager.playtomic.com/hc/en-gb/articles/46212092028561-How-to-use-Playtomic-Manager-on-mobile
[pt-add]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535410170769-How-to-add-a-reservation
[pt-history-art]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535184436881-Booking-History
[pt-avail]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535323617425-Availability-Fixed-Flexible-reservations
[pt-flex]: https://helpmanager.playtomic.com/hc/en-gb/articles/20534683083793-Flexible-Booking-Duration
[pt-player-dur]: https://playerhelp.playtomic.com/hc/en-gb/articles/19831958258193-Private-Bookings-vs-Open-Matches
[pt-paid]: https://helpmanager.playtomic.com/hc/en-gb/articles/46928469100817-How-to-mark-a-booking-or-activity-as-paid-in-Playtomic-Manager
[pt-methods]: https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281-Payment-methods-available-in-Playtomic
[pt-cash]: https://helpmanager.playtomic.com/hc/en-gb/articles/22684483827857-Store-Cash-Register
[pt-resched]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535241098257-How-to-reschedule-a-reservation
[pt-list]: https://helpmanager.playtomic.com/hc/en-gb/articles/20534162168337-Booking-List-Menu
[pt-recurring]: https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513-Recurring-booking-series
[pt-premium]: https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited
[pm-cal]: https://manager.playmore.pl/assets/calendar-CVb43Ojq.js
[pm-venue]: https://manager.playmore.pl/assets/venue-settings-CvgT8INg.js
[pm-reports]: https://manager.playmore.pl/assets/reports-Bp6psLp1.js
[pm-clients]: https://manager.playmore.pl/assets/clients-CGUmLEHn.js
[pm-fisc]: https://manager.playmore.pl/assets/fiscalization-CJudxqb3.js
[pm-code]: https://manager.playmore.pl/assets/calendar-views-H3ldrvfE.js
[pm-atras]: https://playmore.pl/klub/atras-squash-club/
[pm-paolo]: https://playmore.pl/klub/paolo-squash-club/
[pm-s4y]: https://playmore.pl/klub/squash4you/
[t4u-panel]: https://test-panel.tenis4u.pl/main.2b865c996e568707.js
[t4u-app]: https://app.tenis4u.pl/main.cf446af5e9523413.js
[kl-funkcje]: https://oferta.kluby.org/funkcje
[kl-pomoc]: https://oferta.kluby.org/pomoc
[kl-2016]: https://oferta.kluby.org/changelog?rok=2016
[kl-2017]: https://oferta.kluby.org/changelog?rok=2017
[kl-2018]: https://oferta.kluby.org/changelog?rok=2018
[kl-2019]: https://oferta.kluby.org/changelog?rok=2019
[kl-2020]: https://oferta.kluby.org/changelog?rok=2020
[kl-2021]: https://oferta.kluby.org/changelog?rok=2021
[kl-2022]: https://oferta.kluby.org/changelog?rok=2022
[kl-2023]: https://oferta.kluby.org/changelog?rok=2023
[mx-schedule]: https://matchi.zendesk.com/hc/en-gb/articles/11467301471901-Schedule
[mx-types]: https://matchi.zendesk.com/hc/en-gb/articles/11452719320605-Booking-types
[mx-newcust]: https://matchi.zendesk.com/hc/en-gb/articles/11467085227677-Book-court-for-a-new-customer
[mx-admin]: https://matchi.zendesk.com/hc/en-gb/articles/14557110952861-How-to-make-a-random-admin-booking
[mx-default]: https://matchi.zendesk.com/hc/en-gb/articles/14556926072477-How-to-create-a-default-booking-customer
[mx-info]: https://matchi.zendesk.com/hc/en-gb/articles/14581009325213-How-to-find-extra-info-on-a-booking
[mx-move]: https://matchi.zendesk.com/hc/en-gb/articles/11467183900957-Move-a-booking
[mx-paid]: https://matchi.zendesk.com/hc/en-gb/articles/11467149476893-Mark-a-booking-as-paid
[mx-links]: https://matchi.zendesk.com/hc/en-gb/articles/14858820219165-Working-with-payment-links
[mx-merge]: https://matchi.zendesk.com/hc/en-gb/articles/18511790370461-Multiple-adjacent-slots-now-merge-into-a-single-booking
[mx-improve]: https://matchi.zendesk.com/hc/en-gb/articles/14372543759901-Improvements-to-our-booking-schedule
[mx-notify]: https://matchi.zendesk.com/hc/en-gb/articles/24752705156637-Cancellation-notifications
[mx-subs]: https://matchi.zendesk.com/hc/en-gb/articles/11467454905373-Subscriptions
[mx-season]: https://matchi.zendesk.com/hc/en-gb/articles/11719357664797-Create-a-new-season
[cr-wait]: https://help.courtreserve.com/en/articles/7235129-court-waitlisting
[ev-onsite]: https://helpcenter.eversportsmanager.com/open
[ev-fin]: https://helpcenter.eversportsmanager.com/financials
[st-readers]: https://docs.stripe.com/terminal/payments/setup-reader
[st-ttp-ios]: https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay?platform=ios
[st-ttp-and]: https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay?platform=android
[st-nocode]: https://docs.stripe.com/no-code/in-person
[st-connect]: https://docs.stripe.com/terminal/features/connect
[st-pricing]: https://stripe.com/en-pl/pricing
[garden-reg]: https://gardenpadel.pl/regulamin/
[fame-cennik]: https://famesport.pl/cennik/
[fame-reg]: https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf
[pado-bajada]: https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow
[pado-ph]: https://pado.app/poland/krakow/clubs/padel-house-krakow
[pado-mor]: https://pado.app/poland/krakow/clubs/morelowa-34-padel-krakow
[pado-lib]: https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club
[sao]: https://saosports.pl/
[atras-reg]: https://www.atrassquash.pl/regulamin/
[atras-cennik]: https://www.atrassquash.pl/cennik/
[paolo-reg]: https://paolosquashclub.pl/regulamin/
[s4y-reg]: https://www.squash4you.pl/regulamin
[ksg-cennik]: https://grzegorzecki.pl/cennik/
[ksg-reg]: https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf
[sf-cennik]: https://sportfactorypark.pl/cennik-tenis-2/
[bp-cennik]: https://teniskrakow.pl/cennik-2/
[ksos-reg]: https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/
[ksos-courts]: https://obiekty.ksos.pl/korty-tenisowe/
