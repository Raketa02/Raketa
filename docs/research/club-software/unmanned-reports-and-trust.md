# Unmanned hours, reports and trust — what rivals give a club, and what a club can rely on

Research for areas 12, 15 and 17 of the planning map *Raketa becomes the club's booking software*: how a
court runs with nobody at the desk, what an owner and a desk read from their software, and what a club
needs before it trusts a vendor with all its bookings and money.

**Extends** [`integration.md`](integration.md) (§5 *What it connects to*, *Its terms*) and, in
[`../games-and-fill-in/`](../games-and-fill-in/), `topics/competitor-club.md` (§6 Check-in, §11 Leaving and
pausing, §12 What clubs say), `topics/platforms.md` and `areas/CHECKIN.md`. Facts carried from there keep
their dates and say where they came from; everything else was read **2026-10-12**.

**This file decides nothing.** Each feature is to be decided Build at launch · Build later · Leave out ·
Ask a real club in the club-software grilling.

**Sources.** Playtomic's and MATCHi's help pages were read through their public Zendesk API, because the
HTML answers 403. tenis4U's panel and player-app text, and Playmore's partner terms, come from the
JavaScript their web apps serve to every visitor. MATCHi's incident history comes from its public
Statuspage API, Playmore's uptime from its public UptimeRobot page. EUR-Lex answered every request with
a 202 challenge page, so the three EU regulations were read from the EU Publications Office's own copy
of the Official Journal text (`publications.europa.eu/resource/celex/…`). The links below still point
to EUR-Lex. Polish statutes were read through the Sejm's ELI API (`api.sejm.gov.pl`), which serves the
ISAP texts, and the links point to ISAP. TTLock's documentation was read from the HTML pages its open
platform loads. tenis4U's public club list was read once, to name the clubs its automation page links
to. Nobody signed in, booked or paid, and nothing that writes was called.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price ·
`[DOCS]` a device maker's or provider's developer document · `[LAW]` a statute or regulation ·
`[COMPLAINT]` one party's account of a problem · `[ABSENT]` looked for and not found, saying where.
Lines marked *reading* are inferences, not sources.

## Read this first

- **Every rival sells hours with nobody at the desk, but none builds the hardware.** They plug in
  other people's devices. Playtomic works with QT System, Micro Solution and Smart Padel. MATCHi works
  with QT, Telkey, CONLAN and MPC. Playmore uses Loxone, after a site audit. tenis4U sells its own
  controller (2,500 zł net, connected by SIM card or modem) and drives TTLock locks and Shelly relays.
  kluby.org sends clubs to an installer, sterowanie.org: a PIN pad with a door strike costs 1,900 zł,
  plus 12 zł a month per switch.
- **Kraków already has unmanned hours, on tenis4U.** SAO Sports Hub (tennis, padel, pickleball) is
  "w pełni zautomatyzowany — brak stałej recepcji" (fully automated, no permanent desk). Its gate code
  goes live 15 minutes before play and the lights 10 minutes before. Smartpong runs table tennis 24/7
  behind a PIN pad and moved from kluby.org to tenis4U. No Kraków padel or squash club advertises
  24-hour play.
- **Losing the internet is handled at the lock, not the cloud.** TTLock's random passcodes are checked
  by an algorithm inside the lock, with no gateway. When a lock goes silent, tenis4U's panel tells the
  owner: "Kody wgrane wcześniej działają — zamek otwiera je lokalnie, bez internetu" (codes already
  loaded still work; the lock opens them locally, without internet). If the door fails twice,
  Playmore's app shows an emergency code.
- **Hardware does fail.** Between Friday 20:50 and Saturday 10:00 on 25–26 April 2025, some MATCHi
  bookings got no working access code and no lights, because the QT hardware never received them.
- **Codes come per player, per booking or per court.** tenis4U gives each player a permanent personal
  code, and QT gives a code to each player per booking. Playtomic gives one code per match. MATCHi's
  venue codes are shared by everyone booking that court in that time window. tenis4U holds back the
  door until a cash-at-club payment is confirmed. *Reading:* Raketa charges every seat, so a code per
  player fits it.
- **Every rival reports occupancy, revenue and customers; Playmore goes furthest.** It has 20+ reports.
  Among them are no-show patterns, repeat no-showers, a daily PDF for the owner and a monthly Excel file
  for the accountant, and each report is labelled with who reads it. Playtomic's reports refresh
  hourly. MATCHi's are computed live but count only money that went through MATCHi.
- **Nobody publishes an uptime guarantee.** MATCHi provides its service "'as is' and 'as available'".
  kluby.org says its services "nie są w 100% niezawodne" (are not 100% reliable). Playmore excludes
  short outages for repairs or maintenance. Status pages exist for Playtomic, MATCHi (with incidents
  back to 2020, light and passage among them) and Playmore (desk panel at 99.982% over 90 days). tenis4U
  and kluby.org have none.
- **Only the Polish vendors support clubs in Polish.** Playmore advertises 24/7 chat and phone support
  in the price. kluby.org sells reply times of 8, 5 or 3 hours for 99, 199 or 299 zł a month.
  MATCHi's emergency line is open 08:00–21:00 every day for light and door failures. Playtomic replies
  within 48, 8 or 4 hours depending on plan, and in none of its nine languages is Polish.
- **The club owns its players' booking data at every rival checked except Playtomic** (Padel Mates not
  found). tenis4U, kluby.org and
  Playmore make the club the controller of its players' booking data, and Playmore and MATCHi publish a
  processing agreement (DPA). Playtomic is itself the controller of player data. The club gets a
  player's details only through an online payment or when the player accepts the club's terms.
- **Leaving looks different at each rival, and none publishes an exit export.**
  - Playtomic: 30 days' notice and a person to take the club offline; the club's configuration is kept.
  - MATCHi: 3 months' notice and fixed periods of 12–36 months; the club's data is deleted or
    anonymised at the end.
  - Playmore: monthly plans; ending the contract deletes the club's account; the club chooses whether
    its data is returned or deleted.
  - kluby.org: one month's notice.
  - tenis4U: publishes nothing on leaving.
- **The law sets a floor that Raketa's terms must meet.**
  - **EU Data Act**, from 12 September 2025: it covers software as a service. Notice to start a switch
    can be at most 2 months, the move gets 30 days, the club has at least 30 days to take its data, and
    switching charges are banned from 12 January 2027.
  - **EU P2B Regulation**, if Raketa connects clubs with players: it sets what the terms must contain,
    15 days' notice of changes, and 30 days' notice with reasons before ending a club.
  - **Polish e-services act, art. 8**: Raketa must publish its terms (a regulamin) and give them free
    before the contract.
  - Playmore's partner terms are the only rival terms found that cite P2B.

---

## Area 12 — Unmanned hours

### 12.1 Running hours with nobody at the desk

- **What it covers.** The operating model: courts that sell, open, light and close themselves, for a
  whole day, a weekend or the quiet hours.
- **Who has it.**
  - **[POLICY] tenis4U:** "Nasz sterownik umożliwia bezobsługową pracę obiektu przez całą dobę, siedem
    dni w tygodniu" (our controller lets a venue run unattended round the clock, seven days a week). It
    offers two models.
    - Fully unmanned: "Korty są w 100% bezobsługowe, czynne całą dobę", with "OSZCZĘDNOŚCI MIESIĘCZNE
      > 15 000" (monthly savings over 15,000) and the controller paid back "w ciągu 5 dni" (within 5
      days).
    - Partly manned: one employee "w najpopularniejszych godzinach np. między 16 - 22" (in the busiest
      hours, e.g. 16–22), the rest unmanned.

    **[PRICE]** "Cena sterownika netto 2500 zł" (controller price, net)
    ([automatyzacja](https://tenis4u.pl/automatyzacja/)). The venues the page links to are Olesno,
    Olsztyn (UWM), Brzesko and Radłów: tenis4U club ids 190, 264, 314 and 329 in its public club list,
    none in Kraków.
  - **[POLICY] Playmore:** KS Zakręt, Warsaw, is "klub bez recepcji w weekendy" (a club with no desk at
    weekends). It reports "0 osób personelu w weekendy (było 1–2 na recepcji)" (0 staff at weekends,
    previously 1–2 at the desk) and "Model: Bezobsługowy" (unmanned)
    ([case study](https://join.playmore.pl/case-studies/kszakret/)). The owner is quoted: "Nie muszę
    nikogo zatrudniać na sobotę i niedzielę" (I don't have to hire anyone for Saturday and Sunday)
    ([join.playmore.pl](https://join.playmore.pl/)). **[PRICE]** "Automatyka obiektu: … Zakres i koszt
    ustalamy po audycie technicznym obiektu" (building automation: scope and cost set after a technical
    audit) ([cennik](https://join.playmore.pl/cennik/)).
  - **[POLICY] kluby.org, through sterowanie.org:** the installer promises "Bezobsługową kontrolę
    dostępu do obiektu … za pomocą kodów pin generowanych dla klientów czy pracowników … umożliwiają
    rezygnację z utrzymywania pracownika" (unattended access control with PIN codes for customers or
    staff, so a club can do without an employee) ([sterowanie.org](https://sterowanie.org)). It lists
    65 kluby.org clubs as installations, one of them in Kraków (Smartpong).
  - **[POLICY] MATCHi:** "Access and/or lighting – for example is a type of Optionals with automated
    code lock and steering of lights whereby the Player receives a code when booking the court" (General
    Terms §3.3, [terms](https://playmore.matchi.com/general-terms-and-conditions-matchi)).
  - **[POLICY] Playtomic:** "Players can go straight to the court and use the pin code to access it — no
    need to stop at reception"
    ([hardware](https://helpmanager.playtomic.com/hc/en-gb/articles/20534244219665), updated 2026-07-28).
  - **[POLICY] Padel Mates:** its player web has "Door code" (Polish: "Kod do drzwi") and "Offline
    check-in at the court" ([strings](https://padelmates.se/locales/en/translation.json)).
    **[ABSENT]** What either does; no club-side page explains them.
- **The desk/owner's day with it.** tenis4U's partly-manned model keeps one person for the evening peak
  only. At KS Zakręt nobody works the weekend, and a separate support line answers 7:00–23:00
  (§12.5). *Reading:* the job moves from letting people in to answering the phone when a door or light
  fails.
- **What a Kraków desk does today.**
  - **[POLICY] SAO Sports Hub** (Piastowska 26; 2 clay tennis courts, 2 panoramic padel courts,
    pickleball; runs on tenis4U), as Playmore's page for it puts it: "Obiekt jest w pełni
    zautomatyzowany — brak stałej recepcji. Wjazd na teren przez szlaban lub intercom przy bramie. Kod do
    bramy kortowej dostaniesz w aplikacji Tenis4U i jest aktywny 15 minut przed rezerwacją. Oświetlenie
    uruchamia się automatycznie 10 minut przed grą." In English: fully automated, no permanent desk;
    entry through a barrier or intercom at the gate; the court-gate code is in the tenis4U app, live 15
    minutes before the booking; lights come on 10 minutes before play. Also "Brak kasy na miejscu" (no
    till on site), and hours 06:00–24:00 in the page's data
    ([Playmore: SAO](https://playmore.pl/klub/sao-sports-hub-piastowska-krakow/)). This is Playmore's
    account of the club, not the club's own.
  - **[POLICY] Smartpong** (Zakopiańska 58; 4 table-tennis tables): "Tenis stołowy Kraków 24/7"; "przy
    drzwiach znajduje się panel z klawiaturą do wpisania kodu dostępu" (a keypad at the door for the
    access code). The code arrives "w wiadomości SMS lub e-mail". The site also says "Od 1 sierpnia
    przechodzimy na aplikację tenis4u!" (from 1 August we move to the tenis4U app; no year given), and
    its booking link now goes to `app.tenis4u.pl/court/564` ([smartpong.pl](https://smartpong.pl/);
    [kluby.org page](https://kluby.org/smartpong-krakow): "Poniedziałek - Niedziela cały dzień").
  - Carried: Kraków desks are staffed about 07:00–23:00 (Garden Padel 7–23, Atras 7–24 on weekdays)
    (`../games-and-fill-in/topics/gaps-REQUEST.md` §6, read 2026-10-08).
  - **[ABSENT]** A Kraków padel, tennis-only or squash club advertising 24-hour or self-service play.
    Searched: web ("korty samoobsługowe Kraków 24h", "padel Kraków otwarte 24h kod dostępu"), and
    Playmore's Kraków padel, tennis, squash and badminton lists for "bez recepcji", "24/7", "całodob",
    "samoobsług", "bezobsług".
- **What it means for the player app.** *Reading:* in an unmanned hour the player app is the only
  desk. The player needs the code or door button there, the help number, and what to do if the door
  fails. SAO's "brak kasy na miejscu" assumes everyone has paid online, which Raketa's every-seat
  payment already does.
- **Market signal.** Offered by every rival vendor as an add-on, so table stakes for the software. Rare
  among clubs: two Kraków venues found, neither padel-only nor squash.

### 12.2 The door opens for a paid booking

- **What it covers.** A code, QR or app button that lets a player in only while they hold a paid
  booking, and stops working outside it.
- **Who has it.**
  - **[POLICY] Playtomic:** "Access codes are created automatically for each reservation and refresh 10
    minutes before the match starts"; "a unique code is generated for every match on the connected
    courts"; "The pin code appears in the match details". To set up, the club pastes "your API token …
    (provided by your hardware provider)", sends "a 4-digit code" to each keypad, and sets "how long
    before and after a reservation the access codes will work"
    ([hardware](https://helpmanager.playtomic.com/hc/en-gb/articles/20534244219665)).
  - **[POLICY] MATCHi, venue codes:** codes are "linked to specific courts and valid for a defined time
    period". "Codes are reusable. A single access code isn't tied to one player or one booking". They
    are sent in the confirmation email and shown in the app to "the booking owner, a co-booker, or a
    participant". These are "a fallback" behind "personal customer codes, subscription codes, or an MPC
    lock integration"; "Automated Telkey and CONLAN code generation and import are handled by MATCHi
    directly" ([access codes](https://matchi.zendesk.com/hc/en-gb/articles/34085754817949), updated
    2026-09-15).
  - **[POLICY] MATCHi, QT hardware:** "Each player gets their own access code tied to their booking";
    "The code only works from a set number of minutes before the booking starts to a set number of
    minutes after it ends"; "If a booking is cancelled, the access code stops working"; "the integration
    itself can only be turned on by MATCHi" ([QT](https://matchi.zendesk.com/hc/en-gb/articles/17957711960221),
    updated 2026-09-16).
  - **[POLICY] Playmore:** "W obiekcie połączonym z Loxone gracz wchodzi telefonem" (with Loxone the
    player enters by phone) ([join.playmore.pl](https://join.playmore.pl/)). At KS Zakręt "Wchodzą
    wyłącznie osoby z aktywną, opłaconą rezerwacją" (only people with an active, paid booking get in)
    ([case study](https://join.playmore.pl/case-studies/kszakret/)). Carried: "Aby uzyskać dostęp do
    obiektu, należy najpierw opłacić rezerwację", "Otwórz drzwi do obiektu", a QR sticker at the door,
    and "Ten obiekt nie obsługuje otwierania z aplikacji" where nothing is fitted
    (`../games-and-fill-in/topics/platforms.md`, read 2026-10-08).
  - **[POLICY] tenis4U:** "Wejście na kort może otworzyć osoba posiadająca opłaconą rezerwację. Gracz nie
    musi wpisywać żadnych kodów, w wygodny sposób otwiera drzwi poprzez aplikację" (whoever holds a paid
    booking can open the court entrance; no code needed, the app opens the door)
    ([automatyzacja](https://tenis4u.pl/automatyzacja/)).
    - Where a keypad is fitted, the app shows "Kod na klawiaturę" (keypad code): "Twój stały kod, ten sam
      we wszystkich klubach. Działa tuż przed grą i w jej trakcie" (your permanent code, the same at every
      club; it works just before and during the game). Once the code is live: "Wpisz na klawiaturze
      przy drzwiach. Gdyby nie zadziałał, użyj przycisku „Otwórz drzwi”" (type it on the keypad; if it
      fails, use the Open door button).
    - The app's source comments hide the door actions in two cases: "Blokuj automatyzację gdy płatność
      "w klubie" nie potwierdzona" (cash-at-club payment not yet confirmed) and "Ukryj automatyzację gdy
      karty Medicover nie zostały zweryfikowane" (Medicover cards not yet verified)
      ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
    - In the panel, a code's validity window runs "Minimum minuta, maksimum 30 dni" (one minute to 30
      days). A code not issued by tenis4U "został nadany poza systemem. Może go używać ekipa serwisowa
      albo najemca obiektu" (was issued outside the system; maintenance staff or the venue's tenant may
      use it) ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
  - **[POLICY] kluby.org:** "otwieranie drzwi na PIN"; "możliwość automatycznego sterowania do
    rezerwacji (na x minut przed rezerwacja)" (PIN door opening; automatic control tied to the booking,
    x minutes before it). **[PRICE]** "Indywidualna wycena instalacji montera - jednorazowy koszt +
    abonament" (installer's quote: one-off cost plus subscription)
    ([integracje](https://oferta.kluby.org/integracje)). **[PRICE]** sterowanie.org: "pinpad +
    elektrozaczep (bez doprowadzenia prądu i zamykacza do drzwi) 1900zł" (PIN pad and door strike,
    without power cabling or door closer), "komputer sterujący 900zł" (controller), "przełącznik 900zł"
    (switch), "moduł GSM 500zł", "abonament 12zł/przełącznik" (subscription per switch)
    ([cennik](https://sterowanie.org/cennik)).
  - **[POLICY] Padel Mates:** "Door code" in the court component
    ([strings](https://padelmates.se/locales/en/translation.json)). **[ABSENT]** How it is made or which
    hardware is used.
- **The desk/owner's day with it.** *Reading:* nobody issues codes by hand. The desk, if there is one,
  handles the exceptions: a code that fails, a guest without the app, a booking cancelled late, or
  maintenance staff with a code of their own (tenis4U's "poza systemem").
- **What a Kraków desk does today.** At SAO the gate code is in the tenis4U app 15 minutes before play;
  Smartpong sends the code by SMS or email (both §12.1). Carried: Fame Sport bans screenshots of its
  app's codes (`../games-and-fill-in/areas/CHECKIN.md`, gaps answers, read 2026-10-08).
- **What it means for the player app.** *Reading:* Raketa charges each seat, and each of the four
  players arrives alone. A code per player (tenis4U, QT) lets the first player in without the
  organiser. A code per booking (Playtomic) has to be shared. tenis4U's rule — no door until the money
  is in — matches Raketa's game, which is paid before it is booked. Playmore says "Każde wejście
  zapisuje się w systemie" (every entry is logged, KS Zakręt case). A door-open event could therefore
  stand beside Raketa's *I'm here* attendance as evidence of arrival. **[ABSENT]** Any rival using door
  events for no-shows.
- **Market signal.** Table stakes for vendors, and installed club by club. A code per player is the
  better practice, offered by tenis4U and QT.

### 12.3 Lights (and heating) follow the booking

- **What it covers.** Court lights, and sometimes heating or air conditioning, switched on before a
  booking and off after it, with the club setting the margins.
- **Who has it.**
  - **[POLICY] Playtomic:** "Set light rules: Choose how long before and after a reservation you want
    the lights to be on"; "Verify lights: Test each court by clicking 'turn on'"
    ([hardware](https://helpmanager.playtomic.com/hc/en-gb/articles/20534244219665)).
  - **[POLICY] MATCHi (QT):** "Court lighting turns on automatically at the start of the access window
    and turns off at the end of it" ([QT](https://matchi.zendesk.com/hc/en-gb/articles/17957711960221)).
  - **[POLICY] Playmore:** "Światło zapala się na początku rezerwacji i gaśnie po jej zakończeniu.
    Klimatyzacja może pracować według grafiku." (lights on at the start of the booking, off at its end;
    air conditioning can follow the schedule) ([join.playmore.pl](https://join.playmore.pl/)).
  - **[POLICY] tenis4U:** "Oświetlenie automatycznie załączy się na czas rezerwacji, która tego wymaga …
    Np. oświetlenie ma się zapalić 5 minut przed rezerwacją i wyłączyć 5 minut po rezerwacji" (lights
    come on for a booking that needs them, e.g. 5 minutes before and 5 after). Heating: "ile minut przed
    rezerwacją mają działać nagrzewnice" (how many minutes before the booking the heaters run); "Sterownik
    może pełnić rolę termostatu" (the controller can act as a thermostat); "Użytkownik może zdecydować,
    czy chce korzystać z oświetlenia" (the player chooses whether to use the lights)
    ([automatyzacja](https://tenis4u.pl/automatyzacja/)). In the app: "Oświetlenie płatne dodatkowo"
    (lights cost extra) and "Włącz oświetlenie" ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
    In the panel: "Cena oświetlenia (zł/h)" and "Zakup oświetlenia", plus a thermostat mode fed by
    sensors on its "shelly-hub" ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
  - **[POLICY] kluby.org:** "możliwość zdalnego sterowania: oświetleniem, ogrzewaniem, wentylacją, bramą"
    (remote control of lights, heating, ventilation and gate), "na x minut przed rezerwacja"
    ([integracje](https://oferta.kluby.org/integracje)). sterowanie.org pitches savings: "Unikniemy np.
    zbędnej pracy ogrzewania czy oświetlenia ze względu na błąd pracownika" (no heating or lights left
    on by staff mistake) ([sterowanie.org](https://sterowanie.org)).
  - **[ABSENT] Padel Mates:** no lighting string found.
- **The desk/owner's day with it.** *Reading:* the owner sets the margins once. The saving is energy,
  and lights no longer left on after the last game.
- **What a Kraków desk does today.** At SAO the lights come on 10 minutes before play (§12.1).
- **What it means for the player app.** *Reading:* where lights cost extra (tenis4U), the price of an
  evening game depends on them, and somebody has to choose. A Raketa game would either include lights
  in the seat price or ask the four players.
- **Market signal.** Table stakes wherever automation exists. Lights as a paid extra chosen by the
  player: rare (tenis4U only).

### 12.4 The owner's remote control and device health

- **What it covers.** Opening a door or switching lights from anywhere, overriding the schedule (a
  class, a tournament, maintenance), and seeing whether locks, gateways and controllers are alive.
- **Who has it.**
  - **[POLICY] tenis4U:** "Zarządca kortów ma możliwość zdalnego zarządzania automatyzacją z dowolnego
    miejsca na świecie" (the court manager can run the automation remotely from anywhere). Each action
    has three states — "automat" (follows bookings), "włącz na stałe", "wyłącz na stałe" (on or off
    permanently). For classes or tournaments the manager can "odblokowac wejście na korty, aby przez
    określony czas były cały czas otwarte" (unlock the entrance for a set time)
    ([automatyzacja](https://tenis4u.pl/automatyzacja/)). The panel's "Zamki TTLock" page has "Otwórz
    zamek zdalnie", "Stan zamka", "Poziom baterii:", "ostatni udany kontakt z zamkiem", "Jeden zamek
    wymaga uwagi", "Kody dostępu" and a code count against the lock's capacity. The controller page has
    "Status połączenia ze sterownikiem" and "Stan pochodzi z shelly-huba"
    ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
  - **[POLICY] MATCHi (QT):** "you can manually open or lock a court and turn lighting on or off through
    the QT app … Manual actions are logged with your name and the time, and they don't affect the
    automated schedule" ([QT](https://matchi.zendesk.com/hc/en-gb/articles/17957711960221)).
  - **[POLICY] kluby.org:** "możliwość ręcznego sterowania przez system KLUBY.ORG", "monitoring obiektów",
    "czujniki temperatury, oświetlenia" (manual control through kluby.org, building monitoring, temperature
    and light sensors) ([integracje](https://oferta.kluby.org/integracje)).
  - **[POLICY] Playmore:** "Każde wejście zapisuje się w systemie, każdy kort jest monitorowany" (every
    entry is logged, every court monitored) ([case study](https://join.playmore.pl/case-studies/kszakret/)).
  - **[ABSENT] Playtomic:** a manual open or lights override after setup (searched the club help for
    "hardware", "door", "lights", "access code"). Setup has test buttons only.
- **The desk/owner's day with it.** *Reading:* the owner's phone replaces the desk for exceptions: a
  coach's class, a tournament day, a player stuck outside, a lock with a flat battery.
- **What a Kraków desk does today.** **[ABSENT]** How SAO's owner handles exceptions. *Reading:* it is
  presumably tenis4U's panel.
- **What it means for the player app.** *Reading:* tenis4U puts "Otwórz drzwi" and "Włącz oświetlenie"
  on the player's booking, alongside the owner's overrides. If both exist, the app needs to show
  whether the door is open because of an override or because of the player's booking.
- **Market signal.** Table stakes wherever automation exists. Lock health and battery in the booking
  panel: tenis4U only.

### 12.5 When the network or a device fails

- **What it covers.** What still works with no internet, a silent gateway or a power cut, and who the
  player calls.
- **Who has it.**
  - **[DOCS] TTLock** — the locks tenis4U drives:
    - Random passcodes: "An accordant passcode algorithm and passcode key data will be generated in both
      the lock and cloud server … When the passcode is inputed on the keypad of the lock, the lock will
      check if it's valid by the algorithm". They "do not rely on gateways". Their period is accurate
      only to the hour, and a timed one "must be used at least once within 24 hours from it's start
      time, or it will be suspended".
    - Custom passcodes are accurate to the minute but "rely on gateway". The passcode guide says the
      lock holds "up to 150 records" ([passcode guide](https://euopen.ttlock.com/documentPages/htmlPages/userGuide/passcodeEn.html));
      the add API says "only 250 passcodes can be added at most"
      ([add API](https://euopen.ttlock.com/documentPages/htmlPages/cloud/passcode/addEn.html)).
    - Gateway: "remote operation should be requested one by one"; "our timeout for requests of remote
      operation is 30 seconds" ([gateway guide](https://euopen.ttlock.com/documentPages/htmlPages/userGuide/gatewayEn.html)).
  - **[POLICY] tenis4U:**
    - When a lock goes silent: "Kody wgrane wcześniej działają — zamek otwiera je lokalnie, bez
      internetu. Nie da się teraz otworzyć zdalnie." (codes loaded earlier work, opened locally without
      internet; remote opening is impossible now).
    - Also: "Trwa odczyt innego zamka — poczekaj, operacje idą przez gateway pojedynczo" (operations go
      through the gateway one at a time), and "Kody wyłączone — znikną z zamków przy najbliższym
      przebiegu automatu" (disabled codes leave the locks at the automation's next run)
      ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
    - The controller "komunikuje się z aplikacją tenis4U za pomocą karty SIM lub modemu" (talks to tenis4U
      by SIM card or modem). Its working "jest stale monitorowane" (is monitored continuously), with "dedykowaną
      infolinię, dostępną pod numerem znajdującym się przy każdej rezerwacji" (a dedicated hotline whose
      number is on every booking) ([automatyzacja](https://tenis4u.pl/automatyzacja/)).
    - Carried: each court's settings hold "Numer telefonu do kontaktu w przypadku awarii automatyzacji"
      (`../games-and-fill-in/topics/gaps-EMAIL.md`, read 2026-10-08).
  - **[POLICY] Playmore:** "Awaryjny kod wejścia — Po dwukrotnej nieudanej próbie otwarcia drzwi aplikacja
    automatycznie wyświetla kod awaryjny" (after two failed attempts the app shows an emergency code).
    "Najważniejsze elementy są zdublowane, a awaryjne zasilanie podtrzymuje pracę przy krótkich przerwach
    w dostawie prądu" (key parts are duplicated; backup power covers short power cuts). "Wsparcie
    techniczne 7:00–23:00 … Gwarantowany czas reakcji: do 15 minut" (a guaranteed reaction within 15
    minutes) ([case study](https://join.playmore.pl/case-studies/kszakret/)).
  - **[POLICY] MATCHi:**
    - "Because the hardware checks in on its own schedule rather than receiving instant commands, there
      can be a short delay between a booking being cancelled and the door locking"
      ([QT](https://matchi.zendesk.com/hc/en-gb/articles/17957711960221)).
    - Incident of 25–28 April 2025: "between Friday 20:50 and Saturday 10:00 this weekend, a small number
      of bookings … did not trigger working access codes or automatic lighting as intended"
      ([incident](https://stspg.io/wgx895f82j84)).
    - 9 April 2026: "up to a 15–20 minute delay before bookings are reflected on-site". Earlier
      light-and-passage incidents: 2020-02-28, 2020-09-03, 2021-09-30, 2022-02-03
      ([status.matchi.se](https://status.matchi.se)).
    - Emergency line for "issues regarding light or passage control", Monday–Sunday 08:00–21:00
      ([Contact](https://matchi.zendesk.com/hc/en-gb/articles/14013508361373)).
  - **[PRICE] kluby.org / sterowanie.org:** "moduł GSM 500zł"; warranty "12 miesiecy — zdalna pomoc,
    dojazd i naprawa uszkodzeń niemechanicznych" (12 months: remote help, call-out and repair of
    non-mechanical faults); service subscription "Dojazd i naprawa wszelkich uszkodzeń (bez części)"
    (call-out and repair of any fault, parts excluded) ([serwis](https://sterowanie.org/serwis)).
  - **[COMPLAINT]** Carried: paid courts whose door code did not open, with no refund (Playtomic NL,
    MATCHi SE) (`../games-and-fill-in/situations.md` SIT-37, read 2026-10-06).
- **The desk/owner's day with it.** *Reading:* the owner's worst hour is a Saturday morning with codes
  that never reached the lock (MATCHi, April 2025). What helps is an emergency path: a code shown
  after failure, a phone line, backup power.
- **What a Kraków desk does today.** **[ABSENT]** SAO's or Smartpong's published rule for a code that
  does not open.
- **What it means for the player app.** *Reading:*
  - The code must be on the phone before the player reaches a hall with no signal, so it should be
    shown ahead of time and kept offline.
  - The help number belongs on the booking, as tenis4U does it.
  - A failed door is a refund or rescue case for the game. Raketa's money rules would need to say who
    pays when the club's door fails.
- **Market signal.** Offline codes at the lock: table stakes with TTLock-class hardware. An emergency
  path for the player (Playmore's code after two failures, MATCHi's emergency line): a differentiator.

### 12.6 The device makers' APIs and what they cost

- **What it covers.** The locks and relays Raketa could drive directly, how codes are pushed, and
  whether access is free.
- **Who has it.**
  - **[DOCS] TTLock:** "Develop your own platform based on our SDKs, which is free"; a new application
    is "manually reviewed by the backend within business days"; "On-premise (Fee required)"
    ([getting started](https://euopen.ttlock.com/documentPages/htmlPages/userGuide/getStartedEn.html)).
    A random passcode comes from `keyboardPwd/get` "without having a gateway"
    ([get API](https://euopen.ttlock.com/documentPages/htmlPages/cloud/passcode/getEn.html)). A custom
    one comes from `keyboardPwd/add`, using `addType=2` through a gateway.
  - **[DOCS] Shelly:** "Currently API calls are limited to one per second" on the Cloud Control API,
    with a key generated in the app ([Cloud Control API](https://shelly-api-docs.shelly.cloud/cloud-control-api/)).
    On the device itself, "There is a limit of 20 schedule instances per device"
    ([Schedule](https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Schedule)).
    **[ABSENT]** Price or licence terms on those pages. tenis4U runs its own hub: "komenda przez MQTT do
    shelly-hub" ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
  - **[DOCS] Nuki:** keypad codes are "6-digits in length", use "the numbers 1-9", "cannot start 12".
    "Older devices can store 100 authorizations, whereas newer devices can store 200". "Smartlocks and
    other devices require an internet connection to interact with the REST API … Some older Smart Locks
    will require a bridge" ([concepts](https://docs.nuki.io/guide/overview/concepts/)). **[ABSENT]**
    Nuki Web or API pricing on that page.
  - **[DOCS] Tedee** (Polish maker): "send fields 'startDate' or 'endDate', it will mark the period when
    pin will be active". This needs the lock "paired with a bridge" and "paired with a keypad". "Pins
    created with an endDate are automatically removed"
    ([PIN how-to](https://tedee-tedee-api-doc.readthedocs-hosted.com/en/latest/howtos/manage-lock-pin-list.html)).
    **[ABSENT]** PIN count limit, offline behaviour, pricing.
  - **[DOCS] Salto KS:** "you will need a Client ID and Client Secret, which you can obtain from your local
    Salto Business Unit" ([Connect API](https://developer.saltosystems.com/ks/connect-api/)).
  - **[POLICY] Loxone, through Playmore:** Playmore Manager has webhooks for devices: "Podaj adres
    https:// sterownika lub producenta (np. Loxone Cloud DNS)" (carried,
    `../games-and-fill-in/topics/gaps-CLUBBOOK.md` §12, read 2026-10-08).
  - **[POLICY] Installation:** tenis4U: "Montaż może być przeprowadzony zarówno przez naszych
    doświadczonych techników, jak i przez elektryków klienta" (installed by its technicians or the
    club's electricians) ([automatyzacja](https://tenis4u.pl/automatyzacja/)). Playmore: "Zakres
    integracji … potwierdzamy po audycie technicznym" (scope confirmed after a technical audit)
    ([join.playmore.pl](https://join.playmore.pl/)).
- **The desk/owner's day with it.** Not applicable. Hardware is a one-off installation.
- **What a Kraków desk does today.** **[ABSENT]** Which lock brand SAO or Smartpong uses. SAO goes
  through tenis4U's automation.
- **What it means for the player app.** *Reading:* TTLock's random passcodes are accurate to the hour,
  which fits Raketa's one-hour games starting on the hour. A code needed from :50 before a :00 start
  would need a custom passcode, which goes through the gateway.
- **Market signal.** TTLock and Shelly are tenis4U's consumer-grade picks; QT, Telkey, CONLAN, MPC and
  Loxone serve the others. **[ABSENT]** A rival naming Tedee, Nuki or Salto.

---

## Area 15 — Reports

### 15.1 The live dashboard and the daily report

- **What it covers.** What the desk or manager reads every day: today's money, bookings, who is in,
  what is unpaid, and alerts.
- **Who has it.**
  - **[POLICY] Playmore:**
    - "Pulpit managera — Najważniejsze liczby na żywo: przychód dnia, aktywne rezerwacje, obłożenie,
      klienci obecni i nieopłacone rezerwacje. Do tego oś czasu kortów i alerty z linkiem do problemu.
      Dla managera i recepcji" (manager dashboard: today's revenue, active bookings, occupancy,
      customers present, unpaid bookings, a court timeline and alerts linking to the problem; for the
      manager and desk).
    - "Raport dzienny — Pełne podsumowanie dnia: liczby, pogoda, przychody godzina po godzinie, kolorowa
      mapa godzin i ranking kortów, alerty. Pobierzesz jako plik Excel albo PDF gotowy do wysyłki. Dla
      właściciela - poranny briefing" (daily report: the day's figures, weather, revenue hour by hour, a
      colour map of hours, a court ranking, alerts; Excel or PDF to send; for the owner, a morning
      briefing).
    - "Raport płatności — Wszystkie płatności z okresu do 7 dni … codzienna kontrola kasy. Dla recepcji i
      managera" (payments over up to 7 days; the daily cash check; desk and manager). The demo's alerts
      read "3 nieopłacone rezerwacje na dziś" and "Zajęcia 17:00 bez uczestników"
      ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - **[POLICY] Playtomic:** "Reports update every hour — they are not real-time", and "figures for past
    dates can change if you later modify or cancel bookings"
    ([Reports](https://helpmanager.playtomic.com/hc/en-gb/articles/43127115602961), updated 2026-09-25).
    Carried: a Payout Summary Report every 7 days (`../games-and-fill-in/topics/competitor-club.md` §9,
    read 2026-10-08).
  - **[POLICY] MATCHi:** "Data is calculated fresh every time you load the page"; the date range
    "Defaults to the current week" ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277),
    updated 2026-09-16).
  - **[POLICY] tenis4U:** the day's calendar as PDF (`Tenis4u-DD-MM-YYYY.pdf`) (carried,
    `../games-and-fill-in/topics/gaps-COURTS.md` §5, read 2026-10-08). The desk's calendar re-reads
    every 10 seconds (carried, `integration.md` §5).
  - **[POLICY] kluby.org:** "Pobranie zestawienia dziennego do Excela" (daily summary to Excel, 2022)
    (carried, `gaps-COURTS.md` §5).
  - **[POLICY] Padel Mates:** "you can choose to see the clubs daily, weekly or monthly statistics"
    ([strings](https://padelmates.se/locales/en/translation.json)).
- **The desk/owner's day with it.** Playmore splits the readers explicitly: the dashboard and payment
  report for the desk, the daily PDF for the owner's morning.
- **What a Kraków desk does today.** *Reading:* Kraków's padel and tennis clubs run on tenis4U
  (`integration.md` §4). Their day is its calendar and day PDF. Atras, Paolo and Squash4You are on
  Playmore and have its dashboard.
- **What it means for the player app.** *Reading:* "klienci obecni" (customers present) needs arrival
  data. Raketa already records attendance at the court (#657: *isn't here yet*, *I'm here*), which
  could feed such a figure.
- **Market signal.** A live dashboard is a differentiator, offered by Playmore and Padel Mates. A daily
  report sent to the owner is rare: only Playmore.

### 15.2 Occupancy by court, hour and day

- **What it covers.** Booked hours out of sellable hours, cut by court, hour band, weekday and sport.
- **Who has it.**
  - **[POLICY] Playtomic:**
    - The report shows "Occupancy %", total occupied hours, "Average occupied hours per court per day"
      and a breakdown "by court, sport, and time period". It filters by hour, sport, product, court,
      court type and day of week.
    - "if you leave it covering hours when your club is closed, those closed hours are counted against
      you" ([Occupancy](https://helpmanager.playtomic.com/hc/en-gb/articles/50249496386065), updated
      2026-09-25).
    - It combines "bookings, tournaments, and blocked hours into one complete picture". *Note:* this
      contradicts the carried "blocks are excluded from occupancy stats"
      (`../games-and-fill-in-market.md`, read 2026-10-06). The article read today says blocked hours
      are included.
  - **[POLICY] MATCHi:** "Occupancy — Percentage of available time that is booked, based on the courts,
    time window, and days you've filtered to — not your venue's full operating hours", with a chart of
    available, booked and online slots per day. "Statistics don't break down by individual court — you'll
    see sport-level and indoor/outdoor groupings" ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)).
  - **[POLICY] Playmore:**
    - "Raport kortów — Obłożenie i przychód każdego kortu, kolorowa mapa dni i godzin, ranking kortów i
      średnia cena za godzinę" (occupancy and revenue per court, a heat map of days and hours, court
      ranking, average price per hour; "Dla właściciela - cennik i oferta", for the owner's pricing).
    - "Strefy obłożenia — Dzień podzielony na strefy czasowe - rano, prime time, wieczór … Strefy
      ustawiasz sam" (the day split into zones the owner defines). The demo's reading: "Prime time pełny
      w 89% - kandydat do wyższego cennika" (prime time 89% full, a candidate for higher prices)
      ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - **[POLICY] tenis4U:** "Statystyki" builds a report for "Cały obiekt", "Stanowisko", "Gracz" or
    "Trener" (whole venue, court, player, coach), between "Początek okresu" and "Koniec okresu" — "Długość
    okresu nie może przekroczyć 60 dni" (the period may not exceed 60 days), "Generuj raport". A monthly
    widget shows hours and revenue
    ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)). **[ABSENT]** An occupancy
    percentage label in the panel.
  - **[POLICY] kluby.org:** "Pobranie do Excela podsumowania grafiku" (schedule summary to Excel, 2022)
    (carried, `gaps-COURTS.md` §5); "Raporty" listed among features
    ([funkcje](https://oferta.kluby.org/funkcje)).
  - **[POLICY] Padel Mates:** "Live occupancy, revenue and engagement metrics"
    ([strings](https://padelmates.se/locales/en/translation.json)).
- **The desk/owner's day with it.** An owner's question, asked monthly: which hours to reprice or
  promote. Playmore suggests "Rano 42% - pomysł na promocję lub karnet poranny" (mornings 42%, an idea
  for a promotion or morning pass).
- **What a Kraków desk does today.** Carried, measured from tenis4U's public grid: on weekday evenings
  over the next fortnight, 46–100% of padel hours were already taken (Padel House 100%, Fame Sport 79%)
  (`../games-and-fill-in/areas/PAY.md`, R-PAY-1, read 2026-10-09). *Reading:* the owners see this in
  tenis4U's Statystyki or by eye.
- **What it means for the player app.** *Reading:* Games-deck bookings fill the same courts. For an owner
  to see what the deck added, each booking needs its channel recorded (deck, desk, online).
- **Market signal.** Table stakes. Per-court heat maps and owner-defined zones are a differentiator
  (Playmore).

### 15.3 Revenue by channel and method, and the payouts

- **What it covers.** How much came in, by cash, card, transfer or online and by desk, app or website,
  and how it reconciles with what the processor paid out.
- **Who has it.**
  - **[POLICY] Playtomic:** "Total revenue (including VAT), with a breakdown by payment method (online vs.
    onsite)", by product type, court or sport. "All metrics in this report are calculated based on the
    payment date … not when the service is actually delivered." Wallet payments are excluded from
    Revenue and included in "Amount". Data starts only "from the date your club activated the Payments
    List feature" ([Revenues](https://helpmanager.playtomic.com/hc/en-gb/articles/50249504725265), updated
    2026-09-25).
  - **[POLICY] MATCHi:**
    - Revenue is the "Sum of online payments in the selected period, net of refunded (credited) amounts
      and MATCHi service fees. Coupon/value card and offline payments are not included". "Payments taken
      outside the platform (like cash handled entirely off-system) don't appear in any statistics
      totals" ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)).
    - Monthly statements go by the date of play: "Use statements for financial reconciliation … and use
      statistics for day-to-day operational reporting"
      ([Statements vs Statistics](https://matchi.zendesk.com/hc/en-gb/articles/18510259047069)).
  - **[POLICY] Playmore:**
    - "Raport rezerwacji — … anulowania, rezerwacje last minute, karty partnerskie, źródła (recepcja,
      aplikacja, playmore.pl) i metody płatności" (cancellations, last-minute bookings, partner cards,
      sources — desk, app, playmore.pl — and payment methods; "Dla właściciela - decyzje biznesowe").
    - "Płatności online — kwota od klienta, prowizja serwisowa i kwota netto do wypłaty … Sprawdzisz, ile
      wpłynęło, gdy Cię nie było" (amount from the customer, fee and net payout; "Dla właściciela -
      kontrola wypłat", the owner's payout check).
    - "Nieopłacone rezerwacje — Lista zaległości … Dla recepcji - windykacja" (unpaid bookings; for the
      desk, collections). The demo splits methods "Online 43% · Karta 31% · Gotówka 18% · Przelew 8%"
      ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - **[POLICY] tenis4U:** a monthly report widget with price, online price, pass price, "passesSoldCount"
    and "passesSoldRevenue". "Przychód z ostatnich 12 miesięcy" (revenue over the last 12 months), with
    "Obecny miesiąc" and "Poprzedni miesiąc" (current and previous month)
    ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)). Przelewy24 and Tpay
    statements as CSV (carried, `gaps-COURTS.md` §5).
  - **[POLICY] kluby.org:** "Zestawienia finansowe", "Lista zaległości", "Rozliczanie klientów i trenerów"
    (financial statements, arrears list, settling customers and coaches)
    ([funkcje](https://oferta.kluby.org/funkcje)).
  - **[POLICY] Padel Mates:** "Through the financial tab you will see your revenue streams … you will also
    get a comparison from last period in the form of a percentage"
    ([strings](https://padelmates.se/locales/en/translation.json)).
- **The desk/owner's day with it.** The desk checks the till and chases unpaid bookings daily. The owner
  checks payouts and channels monthly. MATCHi and Playtomic date revenue differently (by date of play
  vs by payment), which an owner comparing them has to know.
- **What a Kraków desk does today.** **[POLICY]** Playmore describes the status quo it sells against:
  "Wyciąg z banku, zeszyt recepcji, raport z terminala. Co miesiąc ktoś siedzi wieczorem i skleja arkusz
  dla księgowej" (bank statement, the desk's notebook, the terminal report; every month someone spends
  an evening gluing a sheet together for the accountant)
  ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)). That is a vendor's picture, not a
  club's. Carried: "Multisport i FitProfit na zeszyt: recepcja spisuje numery kart" (benefit cards
  logged in a notebook) (`integration.md` §4).
- **What it means for the player app.** *Reading:* Raketa's player payments are Stripe direct charges on
  the club's account. A channel tag (Games deck, online booking, desk) and a method tag (card, BLIK,
  cash, benefit card) on each booking are what a revenue-by-channel report would cut by.
- **Market signal.** Revenue by method: table stakes. Revenue by channel (desk / app / portal) and a
  payout check: differentiator (Playmore). Counting only the platform's own money: MATCHi's limit.

### 15.4 Customers: new, returning, top bookers

- **What it covers.** Who plays, who is new, who comes back, who spends most, and who is drifting away.
- **Who has it.**
  - **[POLICY] Playtomic:** "The total number of unique players"; "A player counts as new the first time
    they play at your club … based on the player's full history"; a "Player Type filter … New and
    Returning"; a "Top Players chart"; and charts "Players by Product, Players by Gender, and Players by
    Level" ([Players](https://helpmanager.playtomic.com/hc/en-gb/articles/50250795406225), updated
    2026-09-25).
  - **[POLICY] MATCHi:** the Customer tab lists per customer "Number of bookings, splits (group bookings),
    activities, coupon uses … Total amount spent", sorted "by highest spending first"
    ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)).
  - **[POLICY] Playmore:** "Ranking klientów — Klienci uporządkowani po liczbie rezerwacji, łącznym
    przychodzie i średniej cenie. TOP 10 do programu VIP, a dołowi rankingu przypomnisz się, zanim
    przestaną przychodzić. Dla właściciela - program lojalnościowy" (customers ranked by bookings,
    revenue and average price; the top 10 for a VIP scheme, the bottom reminded before they stop coming;
    for the owner's loyalty scheme) ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
  - **[POLICY] tenis4U:** a report for one "Gracz" (player) ([panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js));
    the player list as `users.csv` (carried, `gaps-COURTS.md` §5).
  - **[ABSENT] kluby.org, Padel Mates:** a customer report described on their public pages.
- **The desk/owner's day with it.** Monthly, for the owner: loyalty and retention. Playmore's own label
  says so.
- **What a Kraków desk does today.** **[ABSENT]** A Kraków club's practice; ask a real club.
- **What it means for the player app.** *Reading:* Playtomic cuts players by level. Raketa holds a Skill
  per sport for each player, which a club report could use, subject to what the club may see of a player
  (§17.5).
- **Market signal.** Top customers: table stakes. New versus returning by first-ever visit: a
  differentiator (Playtomic).

### 15.5 No-shows and cancellations

- **What it covers.** Who did not come, who cancelled late, on which days, and what it cost.
- **Who has it.**
  - **[POLICY] Playmore:**
    - "Wzorce no-show — Kolorowa mapa nieprzyjść po dniach tygodnia i godzinach, najgorszy dzień i procent
      nieprzyjść. Podstawa do decyzji o przedpłatach i przypomnieniach SMS" (a heat map of no-shows by
      weekday and hour, the worst day, the rate; the basis for prepayment and SMS reminders).
    - "Powtarzający się no-show — Klienci z największą liczbą incydentów: no-show, późne anulacje,
      utracony przychód i procent no-show. Dane do decyzji o blokadzie rezerwacji lub wymogu przedpłaty"
      (repeat offenders: no-shows, late cancellations, lost revenue; for blocking or requiring
      prepayment). The demo shows "Utracony przychód 1 680 zł — no-show + późne anulacje"
      ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
    - Carried: Playmore has no player-to-player no-show report
      (`../games-and-fill-in/topics/platforms.md`, read 2026-10-08). *Reading:* the report must rest on
      marks made by the club.
  - **[POLICY] MATCHi:** "Late cancellations — Bookings cancelled after payment was captured", counted in
    the Revenue tab ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)).
  - **[ABSENT] Playtomic:** a no-show or cancellation report among its five report tabs
    ([Reports](https://helpmanager.playtomic.com/hc/en-gb/articles/43127115602961)). Carried: its
    no-shows exist only for open matches, reported by players (`competitor-club.md` §7).
  - **[ABSENT] tenis4U:** a no-show report in the panel's text; only "Rezerwacja anulowana" (booking
    cancelled).
  - **[ABSENT] kluby.org:** a no-show report on its public pages.
- **The desk/owner's day with it.** Monthly, for the manager: Playmore's "Dla managera - zasady
  przedpłat" (deciding the prepayment rules) and "problemowi klienci" (problem customers).
- **What a Kraków desk does today.** Carried: Miazga blocks booking after a no-show until it is paid;
  Fame Sport charges the booker the full court (`../games-and-fill-in/areas/CHECKIN.md` §6, read
  2026-10-08).
- **What it means for the player app.** *Reading:* Raketa already records attendance at the court
  (#657: *Came late*, *Didn't come*, checked against the club's position) — the raw data such a report
  needs. A report about players raises whether a player can see their own record.
- **Market signal.** Differentiator: only Playmore reports no-shows fully. Late cancellations as a count:
  MATCHi.

### 15.6 Exports and the accountant's month-end

- **What it covers.** Getting the numbers out — for the accountant, for the club's own spreadsheets, and
  when leaving (§17.6).
- **Who has it.**
  - **[POLICY] Playmore:**
    - "Raport zintegrowany — Comiesięczne zestawienie wszystkich płatności w jednym pliku Excel (XLSX):
      przychody z rezerwacji i karnetów, prowizje, kwota netto do wypłaty. Przygotujesz w 30 sekund i
      wysyłasz księgowej. Dla księgowej - zamknięcie miesiąca" (a monthly file of all payments: booking
      and pass revenue, fees, net payout; 30 seconds; for the accountant's month-end).
    - Also "raport faktur — lista klientów, którzy poprosili o fakturę" (customers who asked for an
      invoice) ([analiza przychodów](https://join.playmore.pl/analiza-przychodow/)).
    - Invoices "przez połączenie z Fakturownią, przygotowane na KSeF" (through Fakturownia, ready for
      KSeF). Benefit cards: "zestawienia generują się w panelu raportów" (statements generate in the
      reports panel) ([join.playmore.pl](https://join.playmore.pl/)).
  - **[POLICY] Playtomic:** "Downloads only include what's visible in your current view — for larger data
    extractions or custom reporting, use the Playtomic API instead"
    ([Reports](https://helpmanager.playtomic.com/hc/en-gb/articles/43127115602961)). The API is
    read-only, on the Champion and Master plans (carried, `integration.md` §1). The booking list
    exports JSONL or CSV and payments CSV (carried, `competitor-club.md` §5, §9). Carried: nothing for
    Polish fiscal rules — no KSeF, no JPK (`competitor-club.md` §10).
  - **[POLICY] MATCHi:** "Click Export to schedule a background export of the booking data as an Excel
    (.xls) file"; "Download receipts to get a PDF of all receipts"
    ([Statistics](https://matchi.zendesk.com/hc/en-gb/articles/34131969861277)). "You can export your
    customer list to Excel" ([Customers](https://matchi.zendesk.com/hc/en-gb/articles/11678704771613)).
  - **[POLICY] tenis4U:** a report CSV for at most 60 days, the day's PDF, `users.csv`, and Przelewy24 and
    Tpay statements (carried, `gaps-COURTS.md` §5); "Pobierz jako CSV" (carried, `integration.md` §5).
  - **[POLICY] kluby.org:** "Eksport historii rezerwacji do Excela" (2021) and daily and schedule
    summaries to Excel (2022) (carried, `gaps-COURTS.md` §5). "Faktury online … drukowanie tradycyjnych
    paragonów … e-paragonów" for "0-60 PLN miesięcznie", and "integracja z drukarką fiskalną" (fiscal
    printer) ([integracje](https://oferta.kluby.org/integracje)).
- **The desk/owner's day with it.** Once a month, for the accountant. The owner forwards a file.
- **What a Kraków desk does today.** As §15.3: by Playmore's account, a hand-glued sheet; on tenis4U,
  60-day CSVs and processor statements.
- **What it means for the player app.** *Reading:* a player who asks for an invoice (Playmore's "raport
  faktur") needs a place to give the club their company details.
- **Market signal.** CSV/Excel export: table stakes. A monthly file ready for the accountant, KSeF-ready
  invoicing: a differentiator in Poland (Playmore, kluby.org).

---

## Area 17 — Trust

### 17.1 Status page and incident history

- **What it covers.** A public page showing whether each part of the service is up, with past incidents
  and subscriptions.
- **Who has it.**
  - **[POLICY] Playtomic:** four components ("Playtomic", "Academy", "PT Manager", "Playtomic.com"), none
    for payments. No notices August–October 2026. Email, Slack, RSS and webhook subscriptions (carried,
    `../games-and-fill-in/topics/gaps-PLATFORM.md` §9, read 2026-10-08).
  - **[POLICY] MATCHi:** [status.matchi.se](https://status.matchi.se) lists 13 components, including
    "Payments", "Notifications", "Light and passage", "Sign-in/Authentication" and integrations. It read
    "All Systems Operational" on 2026-10-12, and incidents are public back to 2020 with email and text
    subscriptions. Recent ones:
    - 2025-06-04, critical: "Ongoing technical issues" (22 minutes).
    - 2024-11-07, critical: "Performance issues affecting both our Web and Mobile application" (about 6
      hours).
    - 2026-03-15, major: "Login issues for Android users" (about 1.5 hours).
    - 2025-04-21, minor: "Payment provider under DDOS attack".
  - **[POLICY] Playmore:** [status.playmore.pl](https://status.playmore.pl/) redirects to UptimeRobot with
    4 monitors: player app, "Panel Recepcji" (desk panel), "Panel Rezerwacji Internetowych" (online
    booking panel) and the website. On 2026-10-12 all were up. Over 90 days all ran at 100% except the
    desk panel at 99.982% ([data](https://stats.uptimerobot.com/api/getMonitorList/tePZAixxDw)). Carried:
    about 23 minutes down on 29 July 2026 (`gaps-PLATFORM.md` §12). Nothing for payments.
  - **[ABSENT] tenis4U, kluby.org:** a status page (carried, `gaps-PLATFORM.md` §12). kluby.org announces
    breaks inside its app (carried, same place).
  - **[ABSENT] Padel Mates:** a status page — `status.padelmates.se` answers 404, `status.padelmates.com`
    does not resolve.
- **The desk/owner's day with it.** *Reading:* a desk that cannot book checks the page before calling.
  MATCHi's component list shows what a club needs watched: payments and the door.
- **What a Kraków desk does today.** Kraków runs on tenis4U, which has no status page. Carried
  **[COMPLAINT]**: "W wyniku awarii systemu reservise straciłem wszystkie rezerwacje w klubie" (a system
  failure at Reservise lost all my club's bookings; Google Play, 2024-02-03), and kluby.org users a week
  without login (`../games-and-fill-in/topics/complaints.md`; `situations.md` SIT-38).
- **What it means for the player app.** *Reading:* Raketa's surfaces are the player app, the club
  website, payments (Stripe) and, if built, door control. A status page covering payments and the door
  would go beyond Playtomic's.
- **Market signal.** Differentiator in Poland (only Playmore). Table stakes among the international
  players (Playtomic, MATCHi).

### 17.2 What the contract promises about availability

- **What it covers.** Any uptime commitment, service credits, and the liability a club gets if the
  system is down.
- **Who has it.**
  - **[POLICY] MATCHi:**
    - "3.1 The Service is provided 'as is' and 'as available'". "9.1 … Problems caused by power cuts,
      computer breakdown, cyber-attacks or the like at MATCHi or its suppliers … shall not be considered
      to be within MATCHi's control."
    - "9.6 MATCHi's maximum total liability … shall per calendar year be limited to the total amount …
      paid by the Customer … during the 12-month period immediately preceding". "9.7 … not under any
      circumstances be liable for indirect damage, including … loss of profit or revenue"
      ([General Terms](https://playmore.matchi.com/general-terms-and-conditions-matchi)).
  - **[POLICY] Playmore:**
    - Reservise "zapewnia jej sprawne funkcjonowanie techniczne i w tym zakresie jest odpowiedzialne"
      (ensures the system works technically and is responsible to that extent). It is not liable for
      "krótkotrwałego uniemożliwienia lub utrudnienia w dostępie do Systemu, spowodowanej koniecznością
      przeprowadzenia prac naprawczych, konserwatorskich czy modernizacyjnych" (short outages for repair,
      maintenance or upgrades), nor "za utracone korzyści" (lost profits).
    - An update may need "przerwy technicznej … W takiej sytuacji nie przysługują Ci jednak w stosunku do
      nas żadne roszczenia" (a technical break; then you have no claims against us).
    - "Nie gwarantujemy świadczeń jakichkolwiek usług innych niż te do których świadczenia wprost
      zobowiązaliśmy … Wszelkie usługi dodatkowe, takie jak usługi wsparcia technicznego … będą
      świadczone wyłącznie jeśli strony ustaliły inaczej" (extra services, such as technical support,
      only if agreed) (partner terms §2, §13, §17, [playmore.pl/legal/partner-terms](https://playmore.pl/legal/partner-terms),
      in force from 01.01.2025).
    - *Reading:* the terms promise less support than the marketing (24/7, §17.3).
  - **[POLICY] kluby.org:** "Usługi dostępne w Aplikacji nie są w 100% niezawodne" (§XI,
    [regulamin](https://kluby.org/regulamin); carried and re-read).
  - **[POLICY] tenis4U:** may stop "wybranych lub wszystkich usług ze względu na prace konserwacyjne …"
    (selected or all services, for maintenance and the like) (carried, `gaps-PLATFORM.md` §12).
  - **[ABSENT] Playtomic:** its terms for clubs. Only player-facing legal conditions and the help
    centre are public; the pricing page gives reply times, not uptime (§17.3).
  - **[ABSENT]** An uptime percentage or service credits in any rival's published terms. The nearest is a
    support reaction time: KS Zakręt's "Gwarantowany czas reakcji: do 15 minut" (§12.5).
- **The desk/owner's day with it.** *Reading:* when the system is down, a club has no contractual remedy
  at any rival.
- **What a Kraków desk does today.** Same as above: tenis4U publishes no club contract.
- **What it means for the player app.** *Reading:* a player-facing outage is also a club outage, since
  one calendar serves both.
- **Market signal.** Rare: nobody publishes an availability commitment. Doing so would be a
  differentiator.

### 17.3 Support: hours, languages, channels, reply times

- **What it covers.** Who answers the club, when, in which language and how fast, plus an emergency path
  for hours with nobody at the desk.
- **Who has it.**
  - **[POLICY] Playtomic:**
    - "Our Help Center supports 9 languages" — Spanish, English, Italian, Swedish, German, Dutch,
      Finnish, French, Portuguese. Channels: "Knowledge Base", "Playtomic Campus", "Live Chat", "Email"
      ([Club Support](https://helpmanager.playtomic.com/hc/en-gb/articles/20534845748881), updated
      2026-09-24). The help centre's locale list has no `pl`
      ([locales](https://helpmanager.playtomic.com/api/v2/help_center/locales.json)).
    - Reply times by plan: "48h response time" (Standard), "8h" (Professional), "4h" (Champion),
      "Highest priority with tickets/chat" (Master) ([pricing](https://playtomic.com/pricing)).
    - Carried: player support Monday–Friday 9:30–17:30 CET (`gaps-PLATFORM.md` §9).
  - **[POLICY] MATCHi:**
    - Live chat "Monday - Friday 09:00 - 16:00 CET, closed for lunch between 12:00-13:00 … only for
      venues". Phone "Monday - Friday 9:00-11:30 CET". "Emergency Technical Support … Monday - Sunday
      08:00 - 21:00 CET … issues regarding light or passage control or other business-critical situations
      … such as not being able to make bookings", with the number "not … shared with your
      players/customers" ([Contact](https://matchi.zendesk.com/hc/en-gb/articles/14013508361373),
      updated 2026-10-06).
    - The terms say chat "currently weekdays between 09:30 – 16:00 CET" (§3.6). The help centre has 13
      locales, no Polish ([locales](https://matchi.zendesk.com/api/v2/help_center/locales.json)).
      "To create greater internal efficiencies and reduce cost our terms will only be available in
      English" ([update](https://matchi.zendesk.com/hc/en-gb/articles/36167433642269), 2026-05-18).
  - **[POLICY] Playmore:**
    - "Wsparcie 24/7 przez czat i telefon w cenie" (24/7 chat and phone support included)
      ([cennik](https://join.playmore.pl/cennik/), [porównanie](https://join.playmore.pl/porownanie/)).
      "Po starcie nadal masz wsparcie produktowe i biznesowe przez czat i telefon" (after go-live,
      product and business support by chat and phone) ([join.playmore.pl](https://join.playmore.pl/)).
    - Sales: "Oddzwaniamy od poniedziałku do piątku, 9-17", and on WhatsApp "odpisujemy zwykle w kilka
      minut (pn–pt 9–17)".
    - Complaints ("reklamacje") answered "w terminie 14 (czternastu) dni" by email to
      wsparcie@playmore.pl (partner terms §14).
    - Carried: the only reply time in its app is for a failed account merge, "odpowiemy w ciągu 12
      godzin" (`gaps-PLATFORM.md` §9).
  - **[PRICE] kluby.org:** support packages
    ([cennik](https://oferta.kluby.org/cennik)):
    - STANDARD, in the subscription: "SLA (czas odpowiedzi) — wg kolejności" (in queue order), "Godziny
      pracy supportu 9-17", email only.
    - BUSINESS, 99 PLN: 8h, phone and email, a dedicated adviser.
    - VIP, 199 PLN: 5h, plus WhatsApp, 1h a month of configuration help, 1h of staff training.
    - MAX, 299 PLN: 3h, 3h a month of configuration help, 2h of training.

    "Pakiety wsparcia obowiązują przy conajmniej 10 zainteresowanych klubach na pakiet VIP lub MAX. Do
    tego czasu indywidualna wycena." (VIP and MAX run once at least 10 clubs want them; until then,
    quoted individually.) Phone "+48 571 207 300 (pon-pt 9:00-15:00)".
  - **[POLICY] tenis4U:** phone 889 555 966 and kontakt@tenis4u.pl (carried, `integration.md` §5), plus
    the automation hotline on every booking (§12.5). **[ABSENT]** Support hours or reply times
    ([tenis4u.pl](https://tenis4u.pl/), [automatyzacja](https://tenis4u.pl/automatyzacja/)).
  - **[POLICY] Padel Mates:** "Support 7 days a week" (Polish string "Wsparcie 7 dni w tygodniu") and
    support@padelmates.se ([strings](https://padelmates.se/locales/en/translation.json)). **[ABSENT]** A
    statement that support answers in Polish, though a Polish string file exists.
- **The desk/owner's day with it.** *Reading:* Kraków desks work about 07:00–23:00 and weekends (§12.1).
  Weekday office-hours support (MATCHi chat, kluby.org's standard tier) misses the club's busiest
  hours.
- **What a Kraków desk does today.** tenis4U is a Kraków company at Rynek Główny 28 (carried,
  `integration.md` §5) and answers in Polish by phone. Carried **[COMPLAINT]**: "Contacted the app
  support for refund—they bounced me off to the club. Contacted the club—the club bounced me off to the
  app" (Reservise/Playmore App Store, 2025-03-25) (`platforms.md`).
- **What it means for the player app.** *Reading:* the player app must say who answers the player, the
  club or Raketa. tenis4U puts its automation hotline on the booking. MATCHi keeps its emergency number
  away from players.
- **Market signal.** Polish-language phone support: table stakes in Poland (Playmore, kluby.org,
  tenis4U). Evening and weekend cover: a differentiator (Playmore's 24/7 claim, MATCHi's 08–21
  emergency line).

### 17.4 Onboarding and moving data in

- **What it covers.** Who sets the club up, how long it takes, what it costs, and whether customers,
  prices and standing bookings come across from the old system.
- **Who has it.**
  - **[POLICY] Playmore:**
    - "Wdrożenie trwa 1–2 tygodnie. Opiekun ustawia system pod zasady i grafik Twojego klubu i przenosi
      dane z obecnego systemu" (set-up takes 1–2 weeks; an account manager configures the club and moves
      its data); "Wdrożenie i przeniesienie danych: 0 zł"; "14 dni okresu próbnego bez karty" (14-day
      trial, no card) ([cennik](https://join.playmore.pl/cennik/)).
    - "Najpierw sprawdzamy eksport i mapujemy klientów, cenniki oraz rezerwacje cykliczne … sprawdzamy
      pełną ścieżkę płatności i zwrotu oraz szkolimy zespół przed startem" (we check the old export, map
      customers, price lists and recurring bookings, test a real payment and refund, train the team)
      ([join.playmore.pl](https://join.playmore.pl/)).
    - Carried: Reservise customers are moved over with "Rezerwacje, bazę klientów, cennik i całą
      historię" (`integration.md` §4).
  - **[POLICY] Playtomic:** a Playtomic person makes the club visible (carried, `competitor-club.md`
    §2). "Playtomic Campus … video tutorials explaining how the Playtomic Manager works"
    ([Club Support](https://helpmanager.playtomic.com/hc/en-gb/articles/20534845748881)). "Free Trial:
    Enjoy the first two weeks free" ([plans](https://helpmanager.playtomic.com/hc/en-gb/articles/20535458071313),
    updated 2026-10-10). Its help centre has an article titled "How to import users and benefits into
    Playtomic Manager" (seen in search results; not read).
  - **[POLICY] MATCHi:** "3.5 MATCHi provides free introductory training via its Help Center … Personal
    online training … can be provided upon request, if MATCHi's schedule allows … If such personal
    training has been offered to the Customer as included in the start-up fee, it should be requested …
    within three months" ([General Terms](https://playmore.matchi.com/general-terms-and-conditions-matchi)).
    "You can import customers in bulk from an Excel (XLSX) file"
    ([Customers](https://matchi.zendesk.com/hc/en-gb/articles/11678704771613)).
  - **[PRICE] kluby.org:** "Wypróbuj przez 60 dni za darmo" (60-day free trial). "Szkolenie pracowników
    200 PLN/h", "Audyt konta 200 PLN/h", "Wizyta w klubie 200 PLN/h min. 4h + koszt dojazdu" (staff
    training, account audit, a visit to the club at least 4h plus travel)
    ([cennik](https://oferta.kluby.org/cennik)).
  - **[POLICY] tenis4U:** a club joins through the "Dodaj korty" form (carried, `../games-and-fill-in-market.md`
    S02-G9). **[ABSENT]** Any description of set-up or data migration.
  - **[POLICY] Padel Mates:** "We migrate your courts, members and schedule. Launch-ready in days, not
    months." ([strings](https://padelmates.se/locales/en/translation.json)).
- **The desk/owner's day with it.** *Reading:* the move is the riskiest week, when two calendars run at
  once. Playmore's "przechodzimy pełną ścieżkę na prawdziwych danych" (we walk the full path on real
  data) speaks to that fear.
- **What a Kraków desk does today.** *Reading:* a Kraków padel club would be leaving tenis4U. Its known
  exports are a CSV report of at most 60 days and `users.csv` (§15.6). Standing bookings ("rezerwacje
  stałe") would have to be re-entered or mapped from something else. Smartpong did move from kluby.org
  to tenis4U (§12.1), so clubs do switch.
- **What it means for the player app.** *Reading:* the imported customers have no Raketa account yet.
  Their standing weekly hours have to reach the one calendar before the Games deck sells around them.
- **Market signal.** Free set-up with data migration: table stakes among the challengers (Playmore,
  Padel Mates). Paid training: kluby.org.

### 17.5 Who controls the data: controller, DPA, sub-processors, hosting

- **What it covers.** Whether the club or the vendor is the controller of the players' data, the
  processing agreement (GDPR art. 28), the vendor's own processors, and where data is kept.
- **Who has it.**
  - **[POLICY] tenis4U:** booking data "przekazywane są klubowi i staje się on administratorem Twoich
    danych osobowych" (is passed to the club, which becomes the controller of your personal data). PC
    Company Sp. z o.o. is controller of the account. Processors: "Servizza Sp. z o.o. Sp. k. –
    Przechowywanie danych – Niemcy" (data storage, Germany), "ComVision Sp. z o.o. – Komunikacja sms –
    Polska", "Cloudflare, Inc. – Zapewnienie bezpieczeństwa i stabilności serwerów … – USA", "PayPro
    S.A. – Obsługa płatności internetowych … – Polska", Tpay ([privacy](https://tenis4u.pl/privacypolicy/)).
    **[ABSENT]** A processing agreement for clubs; no club contract is published (carried,
    `integration.md` §5).
  - **[POLICY] kluby.org:** at a booking "Klub staje się wówczas administratorem danych osobowych
    Użytkownika" (the club then becomes the controller of the user's personal data), and likewise for
    competitions; ITSS is controller of the account ([regulamin](https://kluby.org/regulamin)).
    **[ABSENT]** A club contract or processing agreement (carried: `oferta.kluby.org/terms-and-conditions`
    answers 404, `../games-and-fill-in-market.md` S02-G9).
  - **[POLICY] Playmore:**
    - Partner terms, Annex 1: "Administratorem, w rozumieniu RODO, danych osobowych Użytkowników, którzy
      dokonali Rezerwacji … – jesteś Ty, jako Partner" (you, the club, are the controller of the data of
      users who booked). Reservise processes on the club's behalf. Processors are named by category —
      "dostawcy hostingu … podmiotom zapewniającym rozwiązania chmurowe" (hosting and cloud providers)
      — under general consent.
    - "Poinformujemy Cię o wszelkich zamierzonych zmianach dotyczących dodania lub zastąpienia innych
      podmiotów przetwarzających, na co najmniej 7 (siedem) dni roboczych … umożliwiając Ci tym samym
      wyrażenie sprzeciwu" (at least 7 working days' notice of new sub-processors, with a right to
      object) ([partner terms](https://playmore.pl/legal/partner-terms)).
    - Privacy policy: "Partner któremu udostępniamy Twoje dane osobowe staje się ich administratorem"
      (§3.7), with Reservise acting as "podmiotem przetwarzającym działającym w imieniu danego Partnera"
      (§3.8). "Twoje dane osobowe są przetwarzane wyłącznie w ramach Europejskiego Obszaru
      Gospodarczego i nie będą przekazywane do państw trzecich" (processed only within the EEA, §2.4)
      ([privacy policy, from 9 January 2025](https://playmore.pl/legal/privacy-policy.pdf)).
  - **[POLICY] MATCHi:** its Data Processing Agreement (Appendix 2 of the General Terms) names "the
    Customer (hereinafter the 'Controller')", with MATCHi as Processor.
    - 5.4: "a general authorisation to replace or engage additional Processors". 5.5: the list is
      available "upon request", with email updates on request. 5.6: objections "within thirty (30)
      days".
    - 5.10: a breach is reported "without undue delay, within 48 hours if possible". 5.13: audits "once
      per calendar year". 5.16: transfers to third countries under EU standard clauses
      ([General Terms](https://playmore.matchi.com/general-terms-and-conditions-matchi)).
    - **[ABSENT]** Hosting location: MATCHi's privacy policy renders only in a browser and was not read.
  - **[POLICY] Playtomic:**
    - "Playtomic S.L. … which will act in quality of 'Data Controller'". Processors are "hosting
      providers, software providers, social networks. The list of the Data processors is at your
      disposal, under request". Data is shared with "(i) the club managers related to your booking".
      "Some Data Processors … may transfer your personal data to servers located in non-EU territory"
      ([privacy policy](https://playtomic.com/privacy-policy)).
    - Carried: the club gets a player's details "only … through an online payment or by the player
      accepting your club's Terms & Conditions" (`competitor-club.md` §5).
    - The customer export asks the club to "Accept and Export"; "If a player hasn't opted in to receive
      commercial communications, the club shouldn't contact them directly"
      ([export](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489), updated 2026-08-18).
    - **[ABSENT]** A processing agreement for clubs.
  - **[COMPLAINT]** The Padel Paper, 11 December 2025: "several UK multi-site operators have veered away
    from industry-leading platform Playtomic, notably Rocket Padel and Padium", citing "a lack of
    accessibility to their customers". Playtomic's co-founder and CCO replied: "Our philosophy at
    Playtomic is simple: clubs should have transparent access to their data"
    ([article](https://thepadelpaper.com/playtomic-soul-padel-data/)).
- **The desk/owner's day with it.** *Reading:* where the club is controller, its customer list is its own
  to export and use within the players' consents. Where the vendor is controller (Playtomic), the club
  reaches its players through the vendor.
- **What a Kraków desk does today.** tenis4U's model: the club controls its booking data, and tenis4U
  keeps it in Germany behind Cloudflare.
- **What it means for the player app.** *Reading:* a Raketa player is Raketa's account holder. When they
  book a club's court, the Polish model would make the club controller of that booking's data (name,
  phone, email), with Raketa its processor. The player app's privacy notice would have to say so, as
  Playmore's §3.7–3.8 do.
- **Market signal.** Club as controller, with a published processing agreement: table stakes among the
  serious vendors (Playmore, MATCHi). An EEA-only promise: Playmore only.

### 17.6 Leaving: notice, exports, and what happens to the data

- **What it covers.** How a club ends the contract, how long it takes, what it can take with it, and
  what the vendor does with the data afterwards.
- **Who has it.**
  - **[POLICY] Playtomic:**
    - "Cancel your subscription at least 30 days before you want your club to go offline"; cancelling
      "does not automatically take your club offline … you'll also need to contact our team"; "We'll
      connect you with your Club Success representative".
    - "Your configuration is kept, not deleted" ([cancel](https://helpmanager.playtomic.com/hc/en-gb/articles/50864435573009),
      updated 2026-10-09, unchanged in substance since the 2026-10-07 reading).
    - A failed renewal: "If the payment is not completed within 5 days, your club will be automatically
      set to inactive … You will not be able to receive bookings"
      ([plans](https://helpmanager.playtomic.com/hc/en-gb/articles/20535458071313), updated 2026-10-10).
    - **[ABSENT]** What happens to bookings already sold and to the club's Stripe account (carried,
      `competitor-club.md` §11).
  - **[POLICY] MATCHi:**
    - "10.1 … a mutual notice period of 3 months, unless otherwise agreed in the form of a Fixed Period",
      a Fixed Period being "usually between 12-36 months", renewing "unless three months notice is given".
    - "10.3 … MATCHi has the right to terminate this Agreement with immediate effect … if the Customer
      actively develops, offers or promotes services competing with the Service". "10.5 No fees paid in
      advance will be re-paid".
    - 5.4: the club must "register bookings received by telephone, on site or by other means" in MATCHi,
      and "Bookings made via the Service shall always take precedence". 5.7: third-party software may
      not automate bookings into MATCHi.
    - DPA 5.14: "The Processor may, when this DPA ceases to be valid, unless the Controller provides other
      instructions, delete or anonymise the Personal Data"
      ([General Terms](https://playmore.matchi.com/general-terms-and-conditions-matchi); the page is
      headed "last revised on the 20th of April 2024", while the help centre says updated terms apply
      from 1 June 2026 and add "measures to encourage customers to adhere to the notice period"
      ([update](https://matchi.zendesk.com/hc/en-gb/articles/36167433642269))).
  - **[POLICY] Playmore:**
    - "W przypadku niezłożenia … oświadczenia o rezygnacji … w terminie 14 dni przed upływem Okresu
      Subskrypcji, Umowa będzie automatycznie odnawiana" (renews unless cancelled 14 days before the
      subscription period ends).
    - "Rozwiązanie Umowy jest równoznaczne z usunięciem Twojego Konta z Systemu" (ending the contract
      means deleting your account).
    - Annex 1: "Po zakończeniu świadczenia usług … zależnie od Twojej decyzji, usuwamy lub zwracamy Ci
      wszelkie dane osobowe" (afterwards, at your choice, we delete or return all personal data)
      ([partner terms](https://playmore.pl/legal/partner-terms)).
    - Price page: "Wszystkie plany są miesięczne, bez umowy długoterminowej. Wypowiedzenie jest
      miesięczne." (all plans monthly, no long-term contract; one month's notice)
      ([cennik](https://join.playmore.pl/cennik/)).
    - Carried: a club leaving over changed terms keeps its bookings already made, settled by Playmore
      (§16); Playmore ending all services gives 30 days (§14) (`../games-and-fill-in-market.md` S02-G9).
  - **[POLICY] kluby.org:** "miesieczny okres wypowiedzenia" (a month's notice)
    ([cennik](https://oferta.kluby.org/cennik)); "Backup danych" ([funkcje](https://oferta.kluby.org/funkcje));
    "Nowy mechanizm backupu danych" (2023, [changelog](https://oferta.kluby.org/changelog?rok=2023)).
    **[ABSENT]** What happens to data or future bookings after the club leaves.
  - **[ABSENT] tenis4U:** notice, future bookings, data export or retention (carried,
    `../games-and-fill-in-market.md` S02-G9).
  - **[ABSENT]** Any rival publishing an export framed as the way out (carried for Playtomic; read today
    for MATCHi, Playmore, kluby.org).
  - **[ABSENT]** A Polish club's complaint about being held hostage or unable to take its data (web
    searches in Polish on changing booking systems and exporting a customer base, 2026-10-12; carried
    searches on Capterra, GetApp, G2, Trustpilot, 2026-10-08).
- **The desk/owner's day with it.** *Reading:* the owner's fear is a month of overlap with two calendars
  and players double-booked, then an account deleted before the data is out. Playmore's "usunięciem
  Twojego Konta" at termination, with no export window stated, is exactly that risk.
- **What a Kraków desk does today.** *Reading:* switches happen (Smartpong, the Reservise clubs), but
  through the new vendor importing from whatever the old one exports.
- **What it means for the player app.** *Reading:* if a club leaves Raketa, its players keep their
  Raketa accounts, but the club's future bookings and paid seats need a rule. The club's customer list
  can only leave with the consents the players gave.
- **Market signal.** Short notice: table stakes in Poland (monthly at Playmore and kluby.org). A
  published exit export and retrieval window: nobody offers one, so it would be a differentiator — and
  for SaaS the Data Act now requires it (§17.7).

### 17.7 The contractual minimum Raketa must publish

- **What it covers.** What Polish and EU law requires of the terms a club software vendor offers, and of
  a vendor that also brings players to clubs.
- **The law.**
  - **[LAW] Ustawa o świadczeniu usług drogą elektroniczną, art. 8** (consolidated text Dz.U. 2024 poz.
    1513, [ISAP](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20021441204)):
    - "1. Usługodawca: 1) określa regulamin świadczenia usług drogą elektroniczną …; 2) nieodpłatnie
      udostępnia usługobiorcy regulamin przed zawarciem umowy o świadczenie takich usług, a także - na
      jego żądanie - w taki sposób, który umożliwia pozyskanie, odtwarzanie i utrwalanie treści
      regulaminu". (The provider sets terms for its electronic services and gives them free before the
      contract and, on request, in a form that can be saved and reproduced.)
    - "2. Usługobiorca nie jest związany tymi postanowieniami regulaminu, które nie zostały mu
      udostępnione" (clauses not so provided do not bind the user).
    - "3. Regulamin określa w szczególności: 1) rodzaje i zakres usług …; 2) warunki świadczenia usług
      …, w tym: a) wymagania techniczne …, b) zakaz dostarczania przez usługobiorcę treści o charakterze
      bezprawnym; 3) warunki zawierania i rozwiązywania umów …; 4) tryb postępowania reklamacyjnego."
      (The terms must state at least: the kinds and scope of services; the conditions, including
      technical requirements and a ban on unlawful content; how contracts are made and ended; and the
      complaints procedure.)
    - The act is amended by Dz.U. 2026 poz. 1296 (implementing the Digital Services Act, in force
      2026-11-06, [ISAP](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260001296)). Whether
      that touches art. 8 was not checked, as the amendment is published as PDF only.
  - **[LAW] P2B Regulation (EU) 2019/1150** ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2019/1150/oj)),
    applying from 12 July 2020:
    - Scope (art. 1(2), art. 2(2)): services that "allow business users to offer goods or services to
      consumers, with a view to facilitating the initiating of direct transactions between those
      business users and consumers", provided on a contractual basis.
    - Terms (art. 3(1)): "drafted in plain and intelligible language"; "easily available … including in
      the pre-contractual stage"; "set out the grounds for decisions to suspend or terminate"; and
      information on extra distribution channels and on intellectual property.
    - Changes (art. 3(2)): a notice period of "at least 15 days", during which the business user may
      terminate.
    - Ending a club (art. 4(2)): "at least 30 days prior to the termination taking effect, with a
      statement of reasons". Restricting or suspending one (art. 4(1)): reasons "prior to or at the time".
    - Ranking (art. 5(1)): the terms must set out "the main parameters determining ranking".
    - Specific clauses (art. 8): no retroactive changes; "information on the conditions under which
      business users can terminate"; and "a description of the technical and contractual access, or
      absence thereof, to the information … which they maintain after the expiry of the contract".
    - Data (art. 9): describe what data the platform and the business user can access, including
      aggregated data, and what goes to third parties.
    - Complaints and mediators (art. 11 and art. 12): an internal complaint system and "two or more
      mediators". Neither applies to small enterprises (art. 11(5), art. 12(7)).
  - **[LAW] GDPR (EU) 2016/679, art. 28** ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj)):
    - Art. 28(2): no sub-processor "without prior specific or general written authorisation of the
      controller", and with general authorisation the processor must announce changes, "giving the
      controller the opportunity to object".
    - Art. 28(3): the contract must set out "subject-matter and duration … nature and purpose … type of
      personal data and categories of data subjects", and that the processor acts "only on documented
      instructions", keeps confidentiality, secures the data (art. 32), assists with data-subject
      rights, and "(g) at the choice of the controller, deletes or returns all the personal data to the
      controller after the end of the provision of services". (h) makes audits possible.
  - **[LAW] Data Act (EU) 2023/2854, Chapter VI** ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2023/2854/oj)),
    applying "from 12 September 2025" (art. 50):
    - Recital 81 names "Software as a Service (SaaS)" among data processing services.
    - Art. 25(1): switching rights "clearly set out in a written contract", available before signing.
    - Art. 25(2) requires:
      - "(a) … the mandatory maximum transitional period of 30 calendar days", during which the
        provider keeps the service running and helps.
      - "(d) a maximum notice period for initiation of the switching process, which shall not exceed two
        months".
      - "(e) an exhaustive specification of all categories of data and digital assets that can be
        ported".
      - "(g) a minimum period for data retrieval of at least 30 calendar days".
      - "(h) … full erasure of all exportable data" afterwards.
    - Art. 26: information on switching methods and formats, and an online register of data formats.
    - Art. 29: "From 12 January 2027, providers of data processing services shall not impose any switching
      charges"; until then, charges are capped at the provider's direct costs.
    - Art. 30(2): open interfaces "free of charge". Art. 30(5): export "in a structured, commonly used
      and machine-readable format".
    - Art. 31: exemptions only for custom-built services and test versions.
- **Who has it.**
  - **[POLICY] Playmore** is the only rival whose terms cite P2B. They define a "Wewnętrzny System
    Rozpatrywania Skarg … zgodnie z Rozporządzeniem … (UE) 2019/1150" (an internal complaint system
    under P2B) and give 15 days to complain. They promise to publish its effectiveness "co najmniej raz w
    roku" (at least yearly), provide mediation information, and give 14 days' email notice of changes
    to the terms: "co najmniej 14 (czternaście) dni przed dniem jego wejścia w życie"
    ([partner terms](https://playmore.pl/legal/partner-terms)). *Reading:* that is one day short of
    P2B's 15-day minimum (art. 3(2)).
  - **[ABSENT]** A P2B reference in the terms of MATCHi, kluby.org or tenis4U, or in Playtomic's
    player-facing legal conditions (searched for "2019/1150", "P2B", "platform-to-business",
    "mediat").
  - Club-facing terms are public only at Playmore and MATCHi. Playtomic, tenis4U and kluby.org publish
    player terms only (§17.2, §17.5). Playmore's partner terms carry what UŚUDE art. 8 lists: technical
    requirements (§2) and a complaints procedure answered within 14 days (§14).
- **The desk/owner's day with it.** Not applicable.
- **What a Kraków desk does today.** tenis4U publishes only its player terms and privacy policy, no club
  contract (carried, `integration.md` §5).
- **What it means for the player app.** *Reading:* Raketa's player app shows clubs' courts and games,
  and players pay the club directly. That fits P2B's "facilitating the initiating of direct
  transactions", which would make Raketa an online intermediation service towards clubs — a legal
  question to confirm. Separately, MATCHi encourages each club to show its own terms to players (§5.6),
  so the player app may need a place for each club's rules.
- **Market signal.** A published regulamin and processing agreement: table stakes. P2B-ready terms:
  rare (Playmore). Data Act switching terms: none found. *Reading:* MATCHi's 3 months' notice exceeds
  the Data Act's 2-month cap on notice to start a switch, if Chapter VI applies to it — a legal
  question.

---

## Rivals × features

| Feature | Playtomic | MATCHi | Playmore | tenis4U | kluby.org | Padel Mates |
| --- | --- | --- | --- | --- | --- | --- |
| Door opens for a paid booking | via QT System, Micro Solution, Smart Padel | QT, Telkey, CONLAN, MPC; venue codes | Loxone: phone or QR | own controller + TTLock; app button | PIN via sterowanie.org | "Door code" (unexplained) |
| Code granularity | one per match, refreshed 10 min before | per player (QT) or shared per court window | app button; emergency code | permanent personal code | PIN per client | not found |
| Lights follow booking | margins before/after | QT window | start → end; A/C schedule | e.g. ±5 min; heating; paid lights | x min before | not found |
| Owner remote control | test at setup only | QT app, logged | "pełna kontrola", entries logged | panel: open, battery, lock state, gateway | manual control, sensors | not found |
| Works without network | not stated | hardware checks in periodically; delays | backup power, duplicated parts | codes open locally without internet; SIM/modem | GSM module 500 zł | "Offline check-in" (unexplained) |
| Automation price published | no | no ("Optionals") | after site audit | 2,500 zł net controller | installer's price list | no |
| Live dashboard / daily report | hourly refresh | live; monthly statements | live dashboard + daily PDF | day PDF; monthly widget | daily summary to Excel | daily/weekly/monthly stats |
| Occupancy report | %, by court/hour/day | %, no per-court view | per court, heat map, zones | period report ≤60 days | schedule summary | "live occupancy" |
| Revenue by method/channel | online vs onsite; by payment date | platform money only | methods + sources (desk/app/web) | price/online/pass; 12 months | financial statements | financial tab |
| Customers (new/returning/top) | yes, incl. new vs returning | spend per customer | ranking, TOP 10 | per-player report | not found | not found |
| No-show / cancellation report | none (open matches only) | late cancellations | patterns + repeat no-showers | none found | none found | not found |
| Exports for the accountant | CSV/JSONL; API (Champion+) | Excel; receipts PDF | monthly XLSX; KSeF via Fakturownia | CSV ≤60 days; P24/Tpay CSV | Excel; e-paragony, fiscal printer | not found |
| Status page | yes, 4 parts, no payments | yes, 13 parts incl. Payments and door | yes, UptimeRobot, 4 monitors | none | none | none |
| Uptime promise | not public | none ("as is") | none (short outages excluded) | none | "nie są w 100% niezawodne" | not found |
| Support hours / reply time | 48h / 8h / 4h by plan | chat weekdays 9–16; emergency 08–21 daily | "24/7" chat + phone; 15-min line (case) | phone + email; hotline on booking | queue 9–17; paid 8h / 5h / 3h | "7 days a week" |
| Support in Polish | no | no (terms English only) | yes | yes | yes | Polish UI; support language not stated |
| Onboarding | coordinator; 2-week trial | free Help Center training; start-up fee | 1–2 weeks, migration free | contact form | 60-day trial; training 200 zł/h | "We migrate … in days" |
| Controller of player data | Playtomic | club (MATCHi processor) | club (Reservise processor) | club, for booking data | club, at booking | not found |
| DPA published | no | yes (Appendix 2) | yes (Annex 1) | no club contract | no club contract | not found |
| Sub-processors / hosting | categories, list on request; non-EU possible | list on request; 30 days to object | categories; 7 working days' notice; EEA only | named; storage in Germany; Cloudflare US | not found | not found |
| Notice to leave | 30 days + contact | 3 months; fixed 12–36 months | 14 days before period; "miesięczne" | not published | 1 month | not found |
| Data after leaving | configuration kept | deleted or anonymised unless instructed | account deleted; return or delete at club's choice | not published | backup feature; not stated | not found |
| P2B in terms | club terms not public | no | yes | no | no | not checked |

## Gaps

- **Hardware costs behind the international rivals.** QT, Smart Padel, Telkey and the others publish no
  price, and neither does MATCHi's "Optionals" licence for access and lighting nor Playmore's Loxone
  audit.
- **Device makers' commercial terms.** TTLock's terms beyond "SDKs … free" and a fee for on-premise;
  Shelly's cloud licensing; Nuki Web API pricing; Tedee's PIN limits and offline behaviour; Salto
  through a local business unit only.
- **Kraków unmanned hours beyond SAO and Smartpong.** Whether Fame Sport, Garden Padel or Padel House
  use tenis4U's automation for any hour; which lock brands SAO and Smartpong use; their rule when a code
  fails; what Smartpong's switch from kluby.org to tenis4U involved, and in which year.
- **What a Kraków owner actually reads monthly and the desk daily.** No club's own account was found:
  ask a real club. Playmore's picture of the status quo is a vendor's.
- **Playtomic's club contract.** Its DPA, sub-processor list, hosting location and uptime terms are not
  public. Also: which way its occupancy report treats blocked hours (the article read today and the
  2026-10-06 reading disagree).
- **MATCHi's privacy policy** renders only in a browser; its hosting location and the current dated
  version of its General Terms were not confirmed.
- **tenis4U's and kluby.org's club contracts** are unpublished, so their exit exports, retention after
  termination and notice terms are unknown.
- **Playmore's exit.** Whether Playmore Manager lets a leaving club export its customer base and
  booking history before the account is deleted.
- **Clubs' complaints about lock-in in Poland.** None found.
- **Legal questions needing advice:**
  - whether Raketa's player app makes it a P2B "online intermediation service" towards clubs;
  - whether the Data Act's Chapter VI applies to club booking SaaS (the art. 2(8) definition against
    recital 81);
  - whether Dz.U. 2026 poz. 1296 changes art. 8 of the e-services act;
  - the Civil Code's rules on standard terms (art. 384), which were not read because the consolidated
    text is not served as HTML.
