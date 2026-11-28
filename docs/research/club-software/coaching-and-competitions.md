# Coaches, classes and competitions — what rivals run, and what Kraków does

Research for the club-software grilling that follows story S-01E
([#609](https://github.com/Rakieta02/Rakieta/issues/609)), whose decisions of 2026-10-12 set Rakieta on the path
to becoming the club's whole booking software. This file covers the map's **area 8** (coaches, lessons,
classes, academies) and **area 9** (leagues, tournaments, ladders).

**Extends** [`integration.md`](integration.md), [`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md) and
[`../games-and-fill-in-market.md`](../games-and-fill-in-market.md). Facts carried from there keep their dates and
say so; everything else was read **2026-10-12**.

**This file decides nothing.** Each feature will be decided Build at launch · Build later · Leave out · Ask a
real club in the club-software grilling. Nothing here estimates what building it would cost.

**Sources.** Playtomic and MATCHi help pages were read through their public Zendesk API, because the HTML
answers 403. tenis4U's interface text comes from the scripts its player web app
([app.tenis4u.pl](https://app.tenis4u.pl/)) and its public club-panel demo
([test-panel.tenis4u.pl](https://test-panel.tenis4u.pl/)) serve to every visitor; Playmore's from the scripts
its web app serves ([playmore.pl](https://playmore.pl/), asset names as served on 2026-10-12). League rules and
club rules published as PDFs were read in full. Nobody signed in, booked, entered or paid, and no endpoint
was called.

**Kinds:** `[POLICY]` the company's or club's own rule, help, offer page or interface text · `[PRICE]` a
published price · `[DOCS]` a developer document or a tax ruling · `[LAW]` a statute, or the government's
statement of one · `[COMPLAINT]` a user's public complaint · `[ABSENT]` looked for and not found, saying where.
Lines marked *reading* are not sources.

## Read this first

- **In Poland, coaches, classes and competitions come inside the club's subscription.** tenis4U lists
  "Trenerzy klubowi" and "System turniejowy, ligowy i challenge" in every plan, the 10 zł BASIC included
  ([tenis4u.pl](https://tenis4u.pl/)); kluby.org's two plans both list Zajęcia, Rozgrywki, Turnieje
  ([cennik](https://oferta.kluby.org/cennik)). Playmore prices by module ("płacisz za to, czego używasz") yet
  says "Moduł szkółki jest w cenie abonamentu, bez dopłaty" ([szkoły](https://join.playmore.pl/dla-szkolek-sportowych/),
  [szkółki](https://join.playmore.pl/szkolki/)); its challenge ladder costs 249 zł net a month extra
  ([Challenger](https://join.playmore.pl/challenger/)). Playtomic gates coaches, courses, leagues and private
  classes behind its Champion plan (carried, [pricing](https://playtomic.com/pricing), read 2026-10-06).
- **Kraków's competitions mostly do not run in the club's booking system.** Squash leagues run on bo5.pl
  ([Paolo](https://bo5.pl/paolo), [Squash4You](https://bo5.pl/squash4you)), tennis and padel leagues at Fame
  Sport on openleague.pl ([OpenLeague](https://www.openleague.pl/)), padel leagues and series on kluby.org
  and WhatsApp ([Kraków padel leagues](https://kluby.org/padel/rozgrywki/krakow)), padel americanos on
  LigaPadla.pl, and a coaching school on ActiveNow — while the courts sit in tenis4U, Playmore or Padel Mates.
  In the tennis and padel leagues read, the players book the court themselves and pay for it; the squash
  leagues play fixed rounds at the club for a fee per round.
- **Every rival that is the club's software puts lessons and competitions on the one calendar — except
  MATCHi.** Playtomic books a tournament's courts "automatically … no manual court blocking needed"; MATCHi's
  training planner "does not automatically block that court time in your Schedule"
  ([Playtomic](https://helpmanager.playtomic.com/hc/en-gb/articles/20563451171985),
  [MATCHi](https://matchi.zendesk.com/hc/en-gb/articles/11677891942045)).
- **A Kraków coach is often not the club's employee.** A coaching school teaches at five Kraków venues for
  130 zł an hour "+ opłata za kort" ([teniskrakow.pl](https://teniskrakow.pl/cennik/)); Fame Sport sells "Gra
  z trenerem" at 120 zł "+ cena kortu" and runs its academy with a separate association
  ([cennik](https://famesport.pl/cennik/), [tenis](https://famesport.pl/tenis/)); Miazga Squash bars outside
  personal training without its consent ([regulamin](https://www.miazgasquash.pl/regulamin/)).
- **What the Polish rivals sell academies is attendance, make-ups, parents and coach pay** — Playmore,
  kluby.org and ActiveNow all do it; Playtomic's help has no attendance marking at all.
- **A class cancelled for too few people, with an automatic refund, is standard** at Playtomic (public
  classes), MATCHi, Eversports and tenis4U. Playtomic's own private classes are the exception: "this is not
  done automatically".
- **Americano and mexicano tooling is now everywhere** — Playtomic added it ([2026-09-15](https://helpmanager.playtomic.com/hc/en-gb/articles/44129657203985)),
  Playmore, MATCHi (Padelboard), PADO, kluby.org — and LigaPadla gives it to clubs for 0 zł while charging
  players 29,99 zł a month or 199,99 zł a year ([regulamin](https://ligapadla.pl/regulamin)).
- **Polish players and organisers talk in letter levels** — C, B3, B2, B1, A (A2 at the padel federation) —
  and the ranked systems decide who may enter: LigaPadla's "Współczynnik Formy" bars a player from more than
  one level below his form ([regulamin rozgrywek](https://ligapadla.pl/regulamin-rozgrywek)). Playtomic says
  "Tournaments don't affect player levels"
  ([help](https://helpmanager.playtomic.com/hc/en-gb/articles/48343795791505)).
- **Kids' classes carry a legal duty:** organisers of sports activity for minors must have child-protection
  standards since 15 August 2024 ([gov.pl](https://www.gov.pl/web/sprawiedliwosc/ustawa-kamilka--standardy-ochrony-maloletnich));
  Squash4You and Fame Sport publish theirs.
- **A club near Kraków books on Padel Mates:** Ahoj Padel (Niepołomice) sends league players to the Padel
  Mates app ([liga regulamin](https://kluby.org/liga/ahoj-padel/regulamin)) — the first Polish Padel Mates
  club seen; `integration.md` recorded none.

## Area 8 — coaches, lessons, classes, academies

### 1. Coach profiles and coach logins

**What it covers.** A coach exists in the club's system — name, photo, sports, a public profile — and can
sign in to see his own day, without seeing the club's money.

**Who has it.**
- **[POLICY] Playtomic:** a coach profile has "three tabs: Profile, Pricing, and Calendar"; adding a coach
  sends "an email confirming their admin role for the club. This doesn't create a new Playtomic account, just
  a new user role" ([Coach Profile, updated 2026-08-01](https://helpmanager.playtomic.com/hc/en-gb/articles/20534816309649)).
  The coach's own view is a paid add-on: "The club pays for the Playtomic Coach web app and chooses how many
  coaches to include"; "this is not a mobile app"; "Coaches must have admin permissions"; freelancers are
  "the club's responsibility" ([Coach web app, updated 2026-09-10](https://helpmanager.playtomic.com/hc/en-gb/articles/45335085102481)).
- **[POLICY] MATCHi:** "A coach doesn't need a linked MATCHi account to be added and assigned"; "A coach
  belongs to a single venue and can't be shared across venues"; online visibility is a separate switch
  ([Coaches, updated 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11678599910813)).
- **[POLICY] Eversports:** a trainer is made from a customer profile ("Select Create Trainer"), and login
  rights are "handled separately" ([trainer profile](https://helpcenter.eversportsmanager.com/1-create-a-teacher-profile)).
- **[POLICY] CourtReserve:** an instructor is a user with the "Is Instructor?" box checked
  ([instructor availability](https://help.courtreserve.com/en/articles/7971811-manage-instructor-availability)).
- **[POLICY] tenis4U:** the club panel has a "Trenerzy" list with columns "Stawka" (rate) and "Wynagrodzenie"
  (pay), and "Przypisz trenera do kortu" (assign a coach to the club); the player app marks a booking "Jesteś
  trenerem" (you are the coach) ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js),
  [player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] Playmore:** a free native coach app — "Za system płaci klub, nie trener. Aplikacja Playmore dla
  Ciebie jest za darmo … profil aktywuje recepcja Twojego klubu" (the club pays; the app is free to the
  coach; the desk activates the profile); "Wiele klubów, jeden login"; a public page
  "playmore.pl/trener/twoje-imie"; sync to Google, Apple and Outlook calendars
  ([trenerzy](https://join.playmore.pl/trenerzy/)). The coach cannot add classes himself: "Grafik zajęć układa
  recepcja klubu i w aplikacji nie dodasz ich samodzielnie" ([web app script](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] kluby.org:** "Panel trenera/opiekuna" ([funkcje](https://oferta.kluby.org/funkcje)); 2021
  "Możliwość ograniczenia podglądu zajęć w panelu trenera na określoną liczbę dni"; 2022 "Dopisywanie
  uczestnika przez panel trenera" ([changelog 2021](https://oferta.kluby.org/changelog?rok=2021),
  [2022](https://oferta.kluby.org/changelog?rok=2022)). Its public portal lists coaches under "Nauka —
  Trenerzy" ([kluby.org](https://kluby.org/osrodek/leagues-in-krakow)).
- **[POLICY] PADO:** "For Coaches — Manage your schedule and players"; club CRM: "Manage your coaching team
  with full control over schedules, workload, and performance" ([pado.app](https://pado.app),
  [for clubs](https://pado.app/for-club)).

**The desk's day with it.** *Reading:* the desk creates the coach once and decides what he sees; at Playmore
it is literally the desk that switches the coach's profile on. Without a coach view, the desk answers "what's
my day?" calls.

**What a Kraków desk does today.**
- **[POLICY]** Clubs list their coaches on their own sites: Squash4You's "Polecani trenerzy klubowi"
  ([trenerzy](https://www.squash4you.pl/trenerzy)), Paolo's "główny trener klubu" and team
  ([paolosquashclub.pl](https://paolosquashclub.pl/)), Fame Sport's "Kadra" ([famesport.pl](https://famesport.pl/tenis/)).
- **[POLICY]** Playmore describes the coach's status quo as "Grafik w pięciu miejscach — SMS od recepcji,
  grupa na WhatsAppie, kartka w torbie" (a schedule in five places: a text from the desk, a WhatsApp group, a
  note in the bag) ([trenerzy](https://join.playmore.pl/trenerzy/)). *Reading:* a vendor's pitch, not a survey.

**What it means for the player app.** *Reading:* a coach is a new kind of person on the club's side — not a
player, not the Administrator. If coaches sign in, they need a view of their day that is not the player app's
Games deck; Playmore made it a separate mobile surface, Playtomic a separate web app.

**Market signal.** Table stakes — every club-software rival read has coach profiles. A coach's own app is a
differentiator (Playmore free and native; Playtomic paid, web only).

### 2. A coach's sessions on the club's calendar

**What it covers.** Lessons, classes and courses hold courts in the same calendar as bookings, so the desk,
the website and the Games deck cannot sell an hour a coach has.

**Who has it.**
- **[POLICY] Playtomic:** a private class is made from the Schedule and "will appear in both the schedule and
  the coach's calendar"; "The system will notify you if the coach is unavailable"
  ([private classes, updated 2026-07-16](https://helpmanager.playtomic.com/hc/en-gb/articles/20534804347409)).
  A recurring class series is made only where "resources are available", with an email listing the sessions
  that could not be created ([class series, updated 2026-09-16](https://helpmanager.playtomic.com/hc/en-gb/articles/48824527477009)).
  Manager shows "private and course classes" on the one Schedule (carried,
  [Schedule basics](https://helpmanager.playtomic.com/hc/en-gb/articles/20560058451985), read 2026-10-06).
- **[POLICY] MATCHi, the exception:** "Setting up a course session in the Training Planner does not
  automatically block that court time in your Schedule. You must separately create a Training-type booking …
  updating one does not update the other" ([training planner, updated 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/11677891942045)).
  Lessons sold in Matchable do block the court; such a reservation is "still subject to schedule and conflict
  checks", but "per-slot booking restrictions (such as opening-hours restrictions) … are not enforced"
  ([Matchable private trainings, updated 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/27989884702749)).
- **[POLICY] tenis4U:** the panel's "Dodaj rezerwację grupową" takes a class name, "Maks. liczba uczestników",
  a coach and a date range, and reports "Utworzono ${n} zajęć grupowych" ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] kluby.org:** the academy has "Pełna integracja z systemem rezerwacji"
  ([funkcje](https://oferta.kluby.org/funkcje)); 2019 "Informacje z grafiku zajęć na grafiku rezerwacji";
  2021 "Przypisywanie rezerwacji do zajęć", "Tworzenie grup do istniejących stałych rezerwacji"; 2022
  "Przenoszenie zajęć razem z rezerwacjami" ([2019](https://oferta.kluby.org/changelog?rok=2019),
  [2021](https://oferta.kluby.org/changelog?rok=2021), [2022](https://oferta.kluby.org/changelog?rok=2022)).
- **[POLICY] Playmore:** "Utwórz kurs z kalendarza … siatka dat generuje się sama" (create a course from the
  calendar; the dates generate themselves) ([szkółki](https://join.playmore.pl/szkolki/)).

**The desk's day with it.** *Reading:* the desk blocks a coach's hours once a term; any clash shows at
creation. With MATCHi's split the desk keeps two schedules in step by hand.

**What a Kraków desk does today.**
- **[POLICY] Fame Sport** reserves the right to give courts to coaching: "Klub może przeznaczyć określone korty
  lub godziny na potrzeby zajęć szkoleniowych, trenerów, zawodów, turniejów" (rules I.11, in force 30.08.2026)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY] teniskrakow.pl** teaches at five venues — Hala Politechniki, Hala AWF, KSOS, Białoprądnicka,
  Fame — enrols pupils in ActiveNow, and sends court bookings at Białoprądnicka to tenis4U
  (`app.tenis4u.pl/#/court/217`) ([cennik](https://teniskrakow.pl/cennik/),
  [Białoprądnicka](https://teniskrakow.pl/korty-bialopradnicka-krakow/),
  [zapisy](https://teniskrakow.pl/treningi-indywidualne-zapisy/)).
  - *Reading:* the school's timetable and the courts' calendar are two systems; the school holds courts in
    the club's calendar as an ordinary booker.

**What it means for the player app.** *Reading:* the Games deck already proposes only hours the club sells;
once lessons and classes live in the same calendar, an hour a coach holds simply drops out of the deck.

**Market signal.** Table stakes inside club software; MATCHi's two-calendar design is the cautionary case.

### 3. Private lessons booked online by the player

**What it covers.** A player picks a coach, a length and a free time, pays, and the court is held — tenis4U's
"Zarządzanie trenerami klubowi i ich zajęciami" seen from the player's side.

**Who has it.**
- **[POLICY] Playtomic:** in the coach's Pricing tab, "Select 'Allow players to book this coach from the
  Playtomic app'"; prices are per player "for up to 4 players", and online booking needs "pricing set for a
  60‑minute class first" ([Coach Profile](https://helpmanager.playtomic.com/hc/en-gb/articles/20534816309649));
  players cancel "within the club's cancellation policy (the same policy that applies to private bookings)"
  ([private classes](https://helpmanager.playtomic.com/hc/en-gb/articles/20534804347409)); they find classes
  under the app's "Learn" tab ([player help, updated 2026-07-01](https://playerhelp.playtomic.com/hc/en-gb/articles/19831733963409)).
- **[POLICY] MATCHi:** "If your venue has the Book a Trainer feature enabled and a coach is marked as bookable,
  players can book that coach directly, based on the availability slots you set"
  ([Coaches](https://matchi.zendesk.com/hc/en-gb/articles/11678599910813)); for structured private training it
  points venues to Matchable, which "owns trainer availability, session setup, pricing, and the player-facing
  booking flow" ([Matchable](https://matchi.zendesk.com/hc/en-gb/articles/27989884702749)).
- **[POLICY] Eversports:** private sessions (BETA) let customers "either book appointments directly or submit
  booking requests"; teachers may be "allowed to manage their own appointments"
  ([online booking](https://helpcenter.eversportsmanager.com/make-your-private-session-offer-available-for-online-booking),
  [private sessions](https://helpcenter.eversportsmanager.com/create-and-manage-private-sessions)).
- **[POLICY] CourtReserve:** "Book a Pro … allows members to book their own lessons without admin
  involvement"; a lesson type can require approval ("Pending Approval"), and one declined after payment gives
  "an account credit" ([Book a Pro](https://help.courtreserve.com/en/articles/5520963-book-a-pro-setup)).
  Rates are set per instructor, lesson type and membership type, hourly or fixed
  ([pricing](https://help.courtreserve.com/en/articles/4726752-set-instructor-and-lesson-pricing)).
- **[POLICY] Playmore:** "Trener {name} - sprawdź dostępność, specjalizacje i umów się na trening personalny";
  "Poznaj trenerów i umów lekcję" ([web app script](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] PADO:** "Choose a padel coach by level, language and city. Book a private or group lesson right in
  the app" ([pado.app](https://pado.app)).
- **[ABSENT] tenis4U:** no player-side flow to book a coach in its web app (searched "trener", "lekcj"); a
  coach appears only on a booking or a class ([player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[COMPLAINT]** "Playtomic cancelled my lesson due glitch. Drove 35 minutes only to find it cancelled" (UK,
  29 Apr 2026) (carried, [Trustpilot](https://www.trustpilot.com/review/playtomic.io), read 2026-10-06).

**The desk's day with it.** *Reading:* without it the desk brokers every lesson by phone between the player,
the coach's diary and a free court; with it the desk only sees lessons arrive.

**What a Kraków desk does today.**
- **[POLICY] Fame Sport:** "Termin treningu indywidualnego ustalany jest z Klubem i zależy od dostępności
  trenera oraz kortu" (the time is agreed with the club, subject to coach and court); free cancellation up to
  24 h, after that "pełnej opłacie" (rules IV.2, IV.4) ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY] teniskrakow.pl:** a self-service form for "pojedynczy trening indywidualny" (one individual
  lesson), run by ActiveNow ([zapisy](https://teniskrakow.pl/treningi-indywidualne-zapisy/)).
- **[PRICE] Squash4You:** "Nowy w klubie? Czeka na Ciebie lekcja -50%!" ([trenerzy](https://www.squash4you.pl/trenerzy)).

**What it means for the player app.** *Reading:* a lesson is a booking with a coach on it — a different object
from a Rakieta game (one player or a few, no Level matching, the coach's price on top of the court's). It
could sit beside games on Home without touching the deck.

**Market signal.** Differentiator turning table stakes: all four large rivals and two Polish ones have it;
Kraków's main system, tenis4U, does not.

### 4. Coach availability

**What it covers.** When each coach works, where, and his exceptions — the input to online lessons and to
assigning classes.

**Who has it.**
- **[POLICY] Playtomic:** availability is drawn in the Pricing tab by days, times and courts
  ([Coach Profile](https://helpmanager.playtomic.com/hc/en-gb/articles/20534816309649)).
- **[POLICY] CourtReserve:** "five ways" — every day, a weekly block, several blocks a day, a one-time block,
  and "a block of unavailable time" ([availability](https://help.courtreserve.com/en/articles/7971811-manage-instructor-availability)).
- **[POLICY] Eversports:** "Booking- and date-specific availabilities needed for the online booking"
  ([private sessions](https://helpcenter.eversportsmanager.com/create-and-manage-private-sessions)).
- **[POLICY] MATCHi:** Book a Trainer slots; Matchable's availability is "separate from Matchable's and aren't
  synced" with MATCHi's own ([Matchable intro](https://matchi.zendesk.com/hc/en-gb/articles/27894762272285)).
- **[POLICY] Playmore:** "Uczysz w kilku miejscach? Jeden grafik łączy wszystkie obiekty, a Ty sam ustawiasz
  dostępne godziny w każdym z nich" (one schedule across venues; the coach sets his hours at each)
  ([trenerzy](https://join.playmore.pl/trenerzy/)).
- **[POLICY] kluby.org:** 2021 "Odznaczanie dostępności trenerów podczas dodawania do grupy"
  ([changelog 2021](https://oferta.kluby.org/changelog?rok=2021)).

**The desk's day with it.** *Reading:* the desk stops keeping a coach's hours in its head; a sick coach is a
change in one place.

**What a Kraków desk does today.**
- **[ABSENT]** A public coach-availability calendar at any Kraków club read (Fame, Squash4You, Paolo, Garden
  Padel). teniskrakow.pl matches by hand: "Dobierzemy trenera, kort i porę dnia"
  ([teniskrakow.pl](https://teniskrakow.pl/)).

**What it means for the player app.** *Reading:* only matters if players book lessons themselves (block 3).

**Market signal.** Table stakes wherever online lessons exist.

### 5. Coach money: rent, employment, rates and payroll

**What it covers.** Who sells the lesson and who is paid what: the club employing the coach, the coach renting
the court and selling his own lessons, or a split; and the software that works out a coach's month.

**Who has it.**
- **[POLICY] Eversports, "Smart Payroll":** per-teacher rates, "Base salary" or "Base salary + bonus" (per
  participant, from X participants, or by participant spans); "The payroll is not automatically paid … The
  transaction happens outside of Eversports" ([Smart Payroll](https://helpcenter.eversportsmanager.com/you-want-to-use-the-automated-payroll)).
- **[POLICY] CourtReserve:** two reports to calculate pay by "revenue splits, flat rates, and hourly
  compensation" ([instructor pay](https://help.courtreserve.com/en/articles/13492513-calculating-instructor-pay-using-reports)).
- **[POLICY] Playmore:** "Wynagrodzenia trenerów policzone ze stawek i zastępstw" (coach pay computed from
  rates and substitutions), "Raport wynagrodzeń trenerów" ([szkółki](https://join.playmore.pl/szkolki/));
  to the coach: hours counted are "konkretny argument, gdy rozmawiasz z klubem o stawce"
  ([trenerzy](https://join.playmore.pl/trenerzy/)).
- **[POLICY] tenis4U:** per-coach "Stawka" and "Wynagrodzenie" in the panel ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] kluby.org:** "Rozliczanie klientów i trenerów" ([funkcje](https://oferta.kluby.org/funkcje)).
- **[POLICY] ActiveNow** (school software): "Automatic instructor payroll … calculates monthly salaries based on
  your specific rates" ([activenow.io](https://activenow.io/en)).
- **[POLICY] Playtomic:** reports only — "Classes per Coach", "Hours per Coach", "Coach Revenue", "Paid Coach
  Revenue" ([Academy](https://helpmanager.playtomic.com/hc/en-gb/articles/20559686617361)). A club can run its
  academy as a separate legal entity with its own Stripe account (carried,
  [legal entities](https://helpmanager.playtomic.com/hc/en-gb/articles/43703990729105), read 2026-10-06).
  **[ABSENT]** coach pay or payout to a coach in the manager help (searched "coach commission", "coach payment").
- **[POLICY] PADO** lets a coach be the seller: cancellation rules are "determined by the respective service
  provider (club, coach, or tournament organizer)" (carried, [terms](https://pado.app/terms), read 2026-10-06).
- **[DOCS]** Lessons are a different VAT service from court time: coaching is PKWiU 85.51.10.0, outside the
  8 % court service 93.11.10.0 (carried, [WIS 698583](https://eureka.mf.gov.pl/informacje/podglad/698583),
  read 2026-10-06).

**The desk's day with it.** *Reading:* at month end someone counts each coach's hours, substitutions and
no-shows; with rates in the system that is a report, without it a spreadsheet.

**What a Kraków desk does today.**
- **[PRICE] teniskrakow.pl** (an independent school, ul. Bandurskiego 24), from 1.10.2026, per hour: alone
  130 zł "+ opłata za kort"; two players 70 zł each "+ opłata za kort"; three 95 zł each and four 75 zł each,
  "kort wliczony" (court included); "Rabat 5 PLN/h przy płatności z góry za cały semestr". It lists the courts
  it rents, e.g. Białoprądnicka 110–130 zł, Fame 100–140 zł ([cennik](https://teniskrakow.pl/cennik/)).
- **[PRICE] Fame Sport:** "Gra z trenerem 1 os - 120zł/h + cena kortu / 2 os - 125zł/h … / 3 os - 140zł/h …
  /każda kolejna osoba +10zł"; 12-lesson pass −10 %
  ([cennik](https://famesport.pl/cennik/)). Its rules: "Koszt treningu indywidualnego obejmuje opłatę za
  trenera oraz opłatę za wstęp na kort" ([regulamin IV.3](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
  The academy is run "we współpracy z Akademią Tenisa KS Grzegórzecki" ([tenis](https://famesport.pl/tenis/)).
- **[PRICE] Squash4You**, two pages disagree: "cena wynajmu kortu plus 40-60 zł"
  ([cennik](https://www.squash4you.pl/cennik)) against "około 100-120zł … Do ceny należy doliczyć koszt
  wynajęcia kortu" ([trenerzy](https://www.squash4you.pl/trenerzy)).
- **[POLICY] Squash4You** keeps coaches off cheap court passes: "Do zakupu karnetów nie są uprawnieni
  instruktorzy posiadający certyfikat trenera … oraz kadra trenerska współpracująca ze Squash4You"
  ([regulamin](https://www.squash4you.pl/regulamin)).
- **[POLICY] Miazga Squash** forbids "prowadzenia działalności przez podmioty niezwiązane z Klubem Miazga
  Squash bez zgody Miazga Squash, w szczególności treningów personalnych"
  ([regulamin](https://www.miazgasquash.pl/regulamin/)).
- **[POLICY]** Elsewhere in Poland a coach teaches "na własny rachunek oraz na własną odpowiedzialność" (POSiR
  Poznań §3.5), or needs the director's consent (MOSiR Sosnowiec §14–15) (carried, SIT-76,
  [Poznań](https://www.posir.poznan.pl/images/obiekty/Rataje/Korty%20tenisowe/regulamin-korty.pdf),
  [Sosnowiec](https://mosir.sosnowiec.pl/gfx/files/regulamin-kortow-tenisowych-ob2.pdf), read 2026-10-06).
- **[ABSENT]** Published lesson prices at Kraków padel clubs (Garden Padel, Padel House, Bajada, Libertów,
  Morelowa 34; their sites and PADO pages read); Garden Padel only says "certyfikowanych trenerów"
  ([gardenpadel.pl](https://gardenpadel.pl/)).

**The desk's day with it.** *Reading (Kraków):* three models live side by side — the club sells the lesson
plus the court (Fame), the coach's school sells the lesson and books the court like any customer
(teniskrakow.pl), and the club tolerates only its own coaches (Miazga, Squash4You's passes rule).

**What it means for the player app.** *Reading:* if a coach sells his own lessons, the seller on the receipt
is not the club — the opposite of Rakieta's "the club is the seller" (ADR-0189). Lesson VAT differs from court
VAT.

**Market signal.** Coach-pay tooling is a differentiator abroad and table stakes among the Polish rivals
(tenis4U, Playmore, kluby.org). The coach as an independent seller is rare (PADO, Matchable).

### 6. Group classes with capacity and a waiting list

**What it covers.** A class with a coach, a court, a price and a cap; players sign up; when full they queue.

**Who has it.**
- **[POLICY] Playtomic:** public classes repeat weekly, biweekly or custom, up to "365 days"; players "book
  single sessions, not entire series"; filters by level and gender; a "registration deadline"
  ([class series, updated 2026-07-16](https://helpmanager.playtomic.com/hc/en-gb/articles/43089011499537)).
  **[ABSENT]** a waiting list for classes in the manager help (searched "waitlist": 0 results; "waiting
  list": no class article among the top results, and the leagues FAQ answers "Can managers open a waiting
  list for the league? No").
- **[POLICY] MATCHi:** capacity "is enforced as a hard limit"; "everyone on the waiting list is notified
  automatically" ([Activities, updated 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11673332213789)).
  Courses differ: players apply, land "on the waiting list with the status Waiting", and the venue accepts or
  declines; "No notification email is sent" on decline ([Courses](https://matchi.zendesk.com/hc/en-gb/articles/11677925933981),
  [applications](https://matchi.zendesk.com/hc/en-gb/articles/11678022474013)).
- **[POLICY] CourtReserve:** a waitlist either notifies all ("first-come, first-served") or "automatically
  registers the first name", with "Prevent Auto Registration X Hours Before Event" and "Auto Charge if Package
  or Payment Profile Exists" ([event waitlists](https://help.courtreserve.com/en/articles/6601471-event-waitlists)).
- **[POLICY] Eversports:** maximum participants per date ([classes](https://helpcenter.eversportsmanager.com/create-classes-and-trainings-eversports-help-center));
  waiting list: "you will not be automatically signed in" (carried,
  [waiting list](https://helpcenter.eversportsmanager.com/how-to-use-the-waiting-list), read 2026-10-07).
- **[POLICY] tenis4U:** "Zajęcia grupowe", "Cena zajęć", "Pozostało miejsc:", "Zapisz się", "(możesz
  zrezygnować do" (you can withdraw until), "Lista rezerwowa" ([player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] Playmore:** "Pełna grupa? Lista oczekujących pilnuje kolejki" ([szkółki](https://join.playmore.pl/szkolki/));
  seats shown as "Brak wolnych miejsc | Ostatnie wolne miejsce | {count} wolnych miejsc"
  ([web app script](https://playmore.pl/assets/BIIU90LQ.js)); the class waiting list is free to join (carried,
  `platforms.md`, read 2026-10-07).
- **[POLICY] kluby.org:** "Lista oczekujących" ([funkcje](https://oferta.kluby.org/funkcje)); 2018
  "Wprowadzenie informacji o zajętości grup na grafiku zajęć" ([2018](https://oferta.kluby.org/changelog?rok=2018)).
- **[PRICE] Playtomic in Poland** adds a player service fee: Classes 4 % (1,24–8,49 PLN) (carried,
  [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337), read 2026-10-06).

**The desk's day with it.** *Reading:* the desk stops keeping a paper list per class and calling the next name
when someone drops out.

**What a Kraków desk does today.**
- **[PRICE] Squash4You** group classes: "Opłata: 50zł/h + sprzęt gratis" or 55 zł/h by coach; "Maksymalna
  liczba użytkowników z kartą Multisport/FitProfit korzystających z zajęć to 2 osoby na 1 kort"; sign up "w
  recepcji klubu przez stronę www lub aplikację mobilną, najlepiej 48h przed"; late cancellation or no-show
  pays in full ([zajęcia grupowe](https://www.squash4you.pl/zajcia-grupowe)).
- **[POLICY] teniskrakow.pl** groups are "do 4 osób" ([teniskrakow.pl](https://teniskrakow.pl/)).

**What it means for the player app.** *Reading:* a class is a seat sold one by one with a cap — close to the
Games deck's seats, but chosen by the player from a list, with no Level matching beyond a level band.

**Market signal.** Table stakes.

### 7. A class cancelled for too few people

**What it covers.** A minimum number of participants and a deadline; short of it, the class is cancelled,
everyone is told and refunded.

**Who has it.**
- **[POLICY] Playtomic:** public classes "are automatically canceled if they do not reach the minimum number of
  players before the registration deadline … players are automatically refunded"
  ([cancel classes, updated 2026-07-16](https://helpmanager.playtomic.com/hc/en-gb/articles/48825792808721));
  private classes: "Cancel classes if the minimum number of participants isn't met — this is not done
  automatically" ([private classes](https://helpmanager.playtomic.com/hc/en-gb/articles/20534804347409)).
- **[POLICY] MATCHi:** "Automatic cancellations only happen when both a minimum number of participants and a
  cancellation deadline have been set"; reasons logged as "Automatic (too few participants)"
  ([Cancelled Activities, updated 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/28528118381469)).
- **[POLICY] Eversports:** "enable automatic cancellation if the minimum number of participants isn't reached"
  ([courses](https://helpcenter.eversportsmanager.com/create-courses-workshops-events-and-more)).
- **[POLICY] tenis4U:** "Wymagane min. {n} uczestników"; "— zajęcia zostaną odwołane jeśli do {time} nie
  zbierze się wymagana liczba osób"; on the player's dashboard "Zebranie min. osób do:" (minimum to be reached
  by) ([player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] Playmore:** "anulujesz zajęcia z powiadomieniem uczestników" ([szkółki](https://join.playmore.pl/szkolki/));
  **[ABSENT]** an automatic minimum rule in what was read.
- **[POLICY] kluby.org:** 2022 "Powiadomienia o odwołaniu całych zajęć", "Uwalnianie środków podczas odwoływania
  zajęć" ([2022](https://oferta.kluby.org/changelog?rok=2022)).

**The desk's day with it.** *Reading:* without the rule the desk decides at the last minute and phones everyone.

**What a Kraków desk does today.**
- **[POLICY] Squash4You:** "w przypadku braku minimalnej liczby chętnych zajęcia nie odbywają się"
  ([zajęcia grupowe](https://www.squash4you.pl/zajcia-grupowe)).
- **[POLICY] Fame Sport** dissolves a term group instead: "Jeżeli liczba Uczestników w grupie spadnie poniżej
  minimalnej liczby … Klub może rozwiązać grupę" (rules V.13) ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).

**What it means for the player app.** *Reading:* the same shape as a Rakieta game short of players at its
cut-off — the "class short of people" and the game that falls back are one pattern, and the player needs the
same telling.

**Market signal.** Table stakes.

### 8. Courses, terms and class passes (an academy's billing)

**What it covers.** A course over months; paying the whole term, monthly or in instalments; and passes
("karnety") of N classes.

**Who has it.**
- **[POLICY] Playtomic:** a course is sold whole or by single class; "Fees are not prorated"; "a course can have
  a maximum of 20 participants" ([FAQ, updated 2026-10-08](https://helpmanager.playtomic.com/hc/en-gb/articles/20534603772305),
  [create a course](https://helpmanager.playtomic.com/hc/en-gb/articles/20534444311185)). Monthly: "charged
  automatically on the first day of each month at 8:00 AM"; "online payments cannot be refunded through the
  system" ([monthly payments](https://helpmanager.playtomic.com/hc/en-gb/articles/20534196278929)). Custom
  instalments, e.g. "Sep–Dec: 140€ · Jan–Mar: 120€ · Apr–Jun: 120€"
  ([payment plans](https://helpmanager.playtomic.com/hc/en-gb/articles/45955147883537)). Players cancel "only
  before the course starts". Courses carry a 2 % player fee in Poland (1,24–12,99 PLN) (carried,
  [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337), read 2026-10-06).
- **[POLICY] MATCHi:** courses are billed by "invoice rows" from the training planner
  ([invoice courses](https://matchi.zendesk.com/hc/en-gb/articles/11697415993885)).
- **[POLICY] Eversports:** courses sold by tickets or by existing products ("memberships, block cards")
  ([courses](https://helpcenter.eversportsmanager.com/create-courses-workshops-events-and-more)).
- **[POLICY] Playmore:** "Grupy, semestry, obecności i rozliczenia"; each item "nieopłacone, częściowo,
  opłacone"; payments recorded as "gotówka, karta, przelew, karnet"; "Sprzedajesz też pakiety i karnety - np.
  10 zajęć z terminem ważności" ([szkółki](https://join.playmore.pl/szkolki/)).
- **[POLICY] kluby.org:** "Płatności jednorazowe i cykliczne", "Abonamenty z funkcją odrabiania", "Karnety"
  ([funkcje](https://oferta.kluby.org/funkcje)); 2021 "Możliwość dodania roku szkolnego do zajęć"
  ([2021](https://oferta.kluby.org/changelog?rok=2021)).
- **[POLICY] ActiveNow:** the amount due is calculated "based on your rates, attendance, and custom class
  schedules"; "automatically issues invoices"; reminders for arrears; deposits at registration
  ([activenow.io](https://activenow.io/en)).

**The desk's day with it.** *Reading:* the hard part of an academy is not the timetable but who has paid for
which month; Playmore's "Zaległości" (arrears) screen is the selling point.

**What a Kraków desk does today.**
- **[PRICE] Fame Sport** kids' section, monthly by hours a week: 1 h 280 zł · 1,5 h 380 zł · 2 h 450 zł · 3 h
  545 zł; adults 1,5 h 500 zł · 3 h 800 zł; "Rodzeństwa … 20% rabatem" ([cennik](https://famesport.pl/cennik/)).
  "Miesięczna opłata jest niezależna od liczby zajęć przypadających w danym miesiącu oraz indywidualnej
  obecności" (the monthly fee does not depend on sessions in the month or attendance) (rules V.7)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[PRICE] teniskrakow.pl:** "Płatności naliczane są miesięcznie"; the monthly sum "zależy od liczby godzin
  przypadających na dany miesiąc – szczegóły widać w naszej aplikacji ActiveNow" ([cennik](https://teniskrakow.pl/cennik/)).
- **[PRICE] Squash4You** class passes: "karnet 180zł, ważność 60dni", "karnet 300zł, ważność 90dni"; partner
  cards refund to the pass at once ([zajęcia grupowe](https://www.squash4you.pl/zajcia-grupowe)); a junior
  school runs September–June for ages 7–16 ([squash4you.pl](https://www.squash4you.pl/)).

**What it means for the player app.** *Reading:* a term fee is a recurring charge to a saved card — a payment
shape Rakieta's money port does not have today (it charges seats per game).

**Market signal.** Table stakes for any club with an academy; recurring card billing is a differentiator
(Playtomic); passes are table stakes in Poland.

### 9. Attendance lists and make-up sessions

**What it covers.** The coach marks who came; absences can be made up ("odrabianie") in another group.

**Who has it.**
- **[POLICY] Playmore:** "✓ Obecny / ✗ Nieobecny", "Zaznacz wszystkich obecnych", "Masz 6 godzin po zajęciach
  na poprawki" ([trenerzy](https://join.playmore.pl/trenerzy/)); "Usprawiedliwioną nieobecność uczestnik
  odrabia w innej grupie - Ty ustalasz limit odrabiań i to, do kiedy trzeba je wykorzystać"
  ([szkółki](https://join.playmore.pl/szkolki/)).
- **[POLICY] kluby.org:** "Lista obecności", "Trenerzy mogą bezpośrednio w trakcie zajęć sprawdzić listę
  obecności" ([funkcje](https://oferta.kluby.org/funkcje)); 2018 "informacje o odwołanych i odrobionych
  zajęciach" ([2018](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] MATCHi:** attendance is kept in a downloaded spreadsheet "until the new complete attendance
  function … is launched" — a stop-gap for reporting to the Swedish federation
  ([report attendance, updated 2026-09-17](https://matchi.zendesk.com/hc/en-gb/articles/33629175961245)).
- **[ABSENT] Playtomic:** class attendance in the manager help (searched "attendance": the five results are
  open-match no-shows, levelling, league scoring, open-match settings and the Academy overview, which has no
  register).

**The desk's day with it.** *Reading:* attendance drives make-ups, complaints ("my child missed three
sessions") and, at ActiveNow-style schools, the bill.

**What a Kraków desk does today.**
- **[POLICY] Fame Sport** refuses make-ups: "Nieobecność Uczestnika na zajęciach nie uprawnia do odrabiania
  zajęć w innej grupie, obniżenia miesięcznej opłaty ani zwrotu jej części" (rules V.8)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY]** Playmore says coaches today mark "w zeszycie albo Excelu" (in a notebook or Excel)
  ([szkółki](https://join.playmore.pl/szkolki/)). *Reading:* the vendor's claim.

**What it means for the player app.** *Reading:* Rakieta already catches attendance at the court for games
(#657); a class register is the coach's version of the same fact.

**Market signal.** Table stakes for Polish academy software; absent at Playtomic.

### 10. Children and parents

**What it covers.** A child is enrolled by a parent, who pays, consents and is told.

**Who has it.**
- **[POLICY] Playtomic:** "Children do not have their own profiles. Instead, they will be linked to a parent";
  family members are made and enrolled "only … through Playtomic Manager", only in whole courses; one-time
  payments "cannot be made through the app" ([Kid's Academy, updated 2026-07-16](https://helpmanager.playtomic.com/hc/en-gb/articles/21102948164113)).
- **[POLICY] MATCHi:** a child's account needs "a unique email address"; under 13 it is private and cannot
  join public matches ([player help, updated 2026-09-16](https://matchiplayers.zendesk.com/hc/en-gb/articles/13948766738205)).
- **[POLICY] CourtReserve:** "Allow Family Members to Be Individually Registered" for events
  ([event waitlists](https://help.courtreserve.com/en/articles/6601471-event-waitlists)).
- **[POLICY] Playmore:** "Profil rodzica — Zarządzaj profilami dzieci dla rezerwacji i kursów"; "Gotowe!
  {child} ma zapis na kurs" ([web app script](https://playmore.pl/assets/BIIU90LQ.js)); consents "RODO i
  regulamin w PDF - które rodzic akceptuje przy zapisie" ([szkoły](https://join.playmore.pl/dla-szkolek-sportowych/)).
- **[POLICY] kluby.org:** "Płatności przypisane do opiekuna", "Podgląd obecności i płatności dla opiekuna"
  ([funkcje](https://oferta.kluby.org/funkcje)).
- **[LAW]** Organisers of sports activity for minors must adopt "standardy ochrony małoletnich" (child-protection
  standards), with a transition "do 15 sierpnia 2024 r." ([gov.pl](https://www.gov.pl/web/sprawiedliwosc/ustawa-kamilka--standardy-ochrony-maloletnich)).

**The desk's day with it.** *Reading:* parents write to the coach's private phone — Playmore's pitch: "Rodzice
piszą na prywatny numer trenera" ([szkoły](https://join.playmore.pl/dla-szkolek-sportowych/)).

**What a Kraków desk does today.**
- **[POLICY] Squash4You:** minors in group classes need "pisemnej zgody rodzica lub opiekuna prawnego"; it
  publishes "Standardy Ochrony Małoletnich Squash4You" ([regulamin](https://www.squash4you.pl/regulamin)).
- **[POLICY] Fame Sport:** training is sold "na podstawie umów zawieranych z rodzicami"; parents stay off court;
  the club supervises "od momentu przejęcia Uczestnika przez trenera" (rules V.1, V.19, V.21)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY]** AGH Kraków: under-18s need written parental consent, under-13s only with a parent (carried,
  [AGH](https://swfis.agh.edu.pl/home/swfis/dokumenty/REGULAMIN_KORZYSTANIA_Z_KORTU_DO_SQUASHA.pdf), read 2026-10-06).

**What it means for the player app.** *Reading:* a child in Rakieta would be a profile without its own sign-in,
owned by an adult who pays — an account shape the player app has not got.

**Market signal.** Table stakes for academies; parent-facing apps are a differentiator (Playmore, kluby.org).

## Area 9 — leagues, tournaments, ladders

### 11. One-evening social formats: americano, mexicano, king of the court

**What it covers.** Sign up alone or as a pair, the system pairs each round, scores add up, a live table.

**Who has it.**
- **[POLICY] Playtomic:** "King of the Court", "Americano", "Mexicano", "so you can stop using spreadsheets and
  external apps"; resting players get "compensation points"; but "players don't yet see live matchups or
  leaderboards directly in the Playtomic app" — they get them in the tournament chat
  ([new tools, updated 2026-09-15](https://helpmanager.playtomic.com/hc/en-gb/articles/44129657203985)).
  Recurring tournaments: weekly is "95% of recurring tournaments" ([create](https://helpmanager.playtomic.com/hc/en-gb/articles/20563451171985)).
- **[POLICY] MATCHi:** Padelboard, its own add-on, runs "Americano, Mexicano, or Beat the Box"; "Players use
  Padelboard for free. The subscription cost … is billed to your venue"
  ([Padelboard](https://matchi.zendesk.com/hc/en-gb/articles/14502314451101)).
- **[POLICY] Playmore:** "Americano, Mexicano i Piekło/Niebo" (heaven/hell court ladder), squash, tennis, padel
  and badminton; "Recepcja wpisuje tylko wyniki"; a live table "na telewizorze w klubie"; an Instagram graphic
  "jednym kliknięciem" ([turnieje](https://join.playmore.pl/turnieje/)).
- **[PRICE] LigaPadla:** six formats (Americano, Americano w parach, Mexicano, Mexicano w parach, Klasiko,
  Polako); "system LigaPadla.pl jest całkowicie darmowy dla klubów"; a PIN lock on "ZAKOŃCZ TURNIEJ"; results
  "w chmurze w czasie rzeczywistym" ([dla klubów](https://ligapadla.pl/darmowy-system-do-organizacji-rozgrywek-padla/)).
- **[POLICY] kluby.org:** 2018 "Dodano system turniejowy 'Americano'" ([2018](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] PADO:** "Americano, Mexicano, Winner Court, Groups, and Playoff" ([for clubs](https://pado.app/for-club)).
- **[ABSENT] tenis4U:** "americano", "mexicano" in both the panel and player-app scripts.

**The desk's day with it.** *Reading:* Playmore's picture of the old way — "Lista zapisów na kartce … Recepcja
przez cały wieczór liczy słupki" (a paper list; the desk counts columns all evening)
([turnieje](https://join.playmore.pl/turnieje/)).

**What a Kraków desk does today.**
- **[PRICE]** Padel House, "Americano B3/C – DLA POCZĄTKUJĄCYCH", 90 zł, 18 players, on LigaPadla (carried,
  `local-market.md`, read 2026-10-08).
- **[PRICE]** Libertów, "Americano Español": "2 hours play for 8 people, 2 courts … (100 PLN per person)", run by
  the organiser "Leagues in Krakow" on kluby.org ([organiser page](https://kluby.org/osrodek/leagues-in-krakow)).
- **[POLICY]** Playmore's Kraków club pages show "Turnieje LigaPadla — Zapisy prowadzi LigaPadla.pl" and
  "Otwiera się w nowej karcie" ([web app script](https://playmore.pl/assets/BIIU90LQ.js)).

**What it means for the player app.** *Reading:* an americano is the newcomer's way in ("sign up alone, pay per
head" — `local-market.md`), close to what the Games deck offers a player who comes alone.

**Market signal.** Table stakes for padel in 2026.

### 12. Bracket tournaments: entries, draw, seeding, groups and play-off

**What it covers.** Categories, entries, seeding by ranking, a draw, groups and knock-out, consolation,
schedule, scores, a TV or web board.

**Who has it.**
- **[POLICY] tenis4U:** "System grupowy z awansem do fazy playoff", "System pucharowy z drabinką pocieszenia",
  "System pucharowy" ([tenis4u.pl](https://tenis4u.pl/)); the panel: "Rozlosuj uczestników do drabinki",
  "Faza grupowa", "Grupowy + pucharowy" ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] kluby.org:** "Wiele systemów rozgrywek, Planowanie meczów, Rozstawienie, Losowanie, Wtyczka na TV,
  Wtyczka na WWW, Drukowanie drabinek, Dostęp do ogólnopolskiej bazy graczy" ([funkcje](https://oferta.kluby.org/funkcje));
  "Drabinka o miejsca", "Drabinka do dwóch przegranych" (2018), "grupy + drabinki o miejsca" (2022).
- **[POLICY] bo5.pl (Best of Five):** "Drabinki, harmonogramy, zapisy, sędziowanie i rankingi … Od 2013 roku";
  "2 350+ rozegranych turniejów · 25 000+ graczy · 355 000+ zapisanych meczów"; tablet refereeing
  ([system](https://bo5.pl/system)).
- **[POLICY] LigaPadla:** Klasiko "Faza grupowa + faza pucharowa"; Polako "Pary losowane w fazie grupowej +
  stałe w pucharowej" ([dla klubów](https://ligapadla.pl/darmowy-system-do-organizacji-rozgrywek-padla/)).
- **[POLICY] Playtomic:** single or couples entries, min/max players, level and gender limits, an organiser
  ([create](https://helpmanager.playtomic.com/hc/en-gb/articles/20563451171985)). **[ABSENT]** a draw, seeding
  or knock-out bracket tool in what was read.
- **[COMPLAINT]** MATCHi charged a player twice for a tournament entry and ignored refund requests (DK, 9 Dec
  2024) (carried, [Trustpilot](https://www.trustpilot.com/review/matchi.se), read 2026-10-06).

**The desk's day with it.** *Reading:* draws and schedules are an evening's work by hand; every tool sells
"one click" for the draw.

**What a Kraków desk does today.**
- **[PRICE] Paolo Squash Club**, "Head Squash Open vol. 6 B++" (16–17.10.2026): "OPEN - 120zł/os, DAMSKI -
  100zł/os"; entries "do godziny 12:00 dwa dni przed turniejem"; draw "w aplikacji BO5"; "W przypadku wycofania
  się z turnieju, po dokonaniu losowania, zawodnik jest zobowiązany do uregulowania opłaty wpisowej"; a PZSq
  licence required ([bo5.pl](https://bo5.pl/t7813/Head+Squash+Open+vol.+6+B%2B%2B.html)).

**What it means for the player app.** *Reading:* a bracket is a fixed set of matches between named entrants
— nothing the deck proposes; it would appear to a player as "your next match".

**Market signal.** Table stakes for tennis and squash in Poland (tenis4U, kluby.org, bo5.pl); for padel it
lives in LigaPadla and federation cycles.

### 13. Leagues over weeks

**What it covers.** Groups or divisions, rounds, a points table, promotion and relegation; either fixed
match days at the club, or players arranging their own matches within a window.

**Who has it.**
- **[POLICY] Playtomic:** teams, groups, rounds, "Number of Teams Up / Down"
  ([concepts](https://helpmanager.playtomic.com/hc/en-gb/articles/20535742113681)); "leagues can only be
  launched and played in one club"; padel and tennis only; "Matches are automatically arranged based on the
  league settings, match days calendar, and court availability"; "Can managers manually create league
  bookings? No"; no league waiting list; no monthly charging ([FAQs, updated 2026-10-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20535773758097)).
  An absent team "loses 1 point" ([scoring](https://helpmanager.playtomic.com/hc/en-gb/articles/20535702278289));
  "Players can also enter their own match results"
  ([scores](https://helpmanager.playtomic.com/hc/en-gb/articles/29511711697937)).
- **[POLICY] MATCHi:** leagues run in Backhandsmash, "MATCHi's league management platform … works alongside
  your regular MATCHi bookings so league courts and open bookings never clash"
  ([Backhandsmash](https://matchi.zendesk.com/hc/en-gb/articles/14787431465117)); types "Singles", "Doubles with
  fixed pairs", "Doubles (Americano format)", "Ladder" ([new league](https://matchi.zendesk.com/hc/en-gb/articles/30726051071389)).
- **[PRICE] CourtReserve:** leagues are "only available for pickleball doubles flex leagues"; $99 a month on
  Launch, or legacy "$1.00 per player per active session" ([leagues](https://help.courtreserve.com/en/articles/8051423-manage-leagues)).
- **[POLICY] tenis4U:** "Generujesz rozgrywki, przyjmujesz zapisy i wpisowe online. Klikasz 'Start' a resztą
  zajmują się gracze … rezerwują termin na mecz i podają wynik online. System sam podsumowuje punkty";
  announcements to players within a chosen radius ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] kluby.org:** "System oparty o zasadę każdy z każdym · Podział na tabele ligowe · Możliwe
  awanse/spadki po każdej rundzie" ([funkcje](https://oferta.kluby.org/funkcje)).
- **[POLICY] Playmore:** league tables "Wyniki grup, awanse i spadki"; club pages list "Ligi rozgrywane w tym
  klubie — Organizator: {name}" with a "Zobacz w LigaPadla" link ([web app script](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] OpenLeague.pl** (run by KS Grzegórzecki, Kraków): "zaawansowany serwis ligowy" — season stats,
  "Head2Head", "Pełna kariera zawodnika" ([openleague.pl](https://www.openleague.pl/)).

**The desk's day with it.** *Reading:* the work is chasing unplayed matches and walkovers; every Polish tool
sells automatic deadlines and walkovers.

**What a Kraków desk does today** (all leagues are in the Kraków table below).
- **[POLICY] Fixed match days at the club:** Squash4You's league plays "8 kolejek", "Mecze rozgrywane od godz.
  14:00", groups set "w piątek o godz. 12:00", "2 najlepszych … awansuje … 2 najsłabszych spada", "Nieobecny
  Zawodnik przegrywa walkowerem i automatycznie spada" ([regulamin](https://bo5.pl/squash4you/Dunlop+Krakowska+Liga+Squash4You,rules,1270,2666.html)).
- **[POLICY] Players arrange matches:** Relaksmisja Tennis League — "Zawodnicy zobowiązani są do
  indywidualnego umawiania się na rozegranie meczu … rezerwując wolny termin w recepcji klubu lub poprzez
  aplikację https://tenis4u.pl"; an organiser-set date if a rival does not answer three times
  ([regulamin RTL Zima 2026/2027](https://www.openleague.pl/clubs-media/regulations/relaksmisja-tennis-league-rtl-lato-2026-2027-regulamin-fazy-grupowej.pdf?v=1791797927)).
  The Padel Krakow League pairs teams through "the whatsapp community dedicated to the League" (carried,
  [regulamin](https://kluby.org/liga/padel-krakow-league/regulamin), read 2026-10-08).
- **[POLICY]** Business Tennis League, a team league of 2–4 players in its 37th edition (search-engine summary
  of a [Radio Kraków article](https://radiokrakow.pl/aktualnosci/sport/business-tennis-league-powraca-w-krakowie-w-wielkim-stylu);
  the page did not load; date, organiser and fee unknown).

**What it means for the player app.** *Reading:* a league is a group that must play each other by a date —
the opposite of the deck, which finds who is free. A league match still needs a court booked by someone.

**Market signal.** Table stakes in Polish tennis and squash; Playtomic and MATCHi have it; CourtReserve
only for pickleball.

### 14. Challenge ladders

**What it covers.** A standing ranking where a lower player challenges a higher one; a win swaps places.

**Who has it.**
- **[PRICE] Playmore Challenger:** "Gracz niżej wyzywa gracza wyżej - w dozwolonym zasięgu, np. do 7 pozycji";
  "Wynik bez sprzeciwu zatwierdza się sam po 48 godzinach"; an automatic walkover after the deadline; enforced
  rotation of opponents; "Bezczynność i niestawienie się kosztują: ostrzeżenie, potem spadek pozycji"; holidays
  of at least 7 days; presets "Luźny, Klasyczny (rekomendowany), Intensywny"; "Pierwszy miesiąc za darmo · Potem
  249 zł netto/mc" ([Challenger](https://join.playmore.pl/challenger/)).
- **[POLICY] tenis4U:** "System challenge"; the panel asks "W jakich widełkach rankingowych można wyzwać
  gracza" (default range 100) and sets free rejections (default 2); the player sees "Otrzymałeś wyzwanie !"
  ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js),
  [player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] kluby.org:** "Klasyczny challenge lub piramida" ([funkcje](https://oferta.kluby.org/funkcje));
  2017 "Możliwość rezerwacji kortu z systemu challenge", "Spersonalizowany sposób karania za walkowery"; 2018
  "Karanie za brak aktywności", "Blokada wyzywania przy braku opłaty wpisowego" ([2017](https://oferta.kluby.org/changelog?rok=2017),
  [2018](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] MATCHi:** a "Ladder" type in Backhandsmash ([new league](https://matchi.zendesk.com/hc/en-gb/articles/30726051071389)).
- **[ABSENT] Playtomic:** a ladder (manager help "ladder" returns only the king-of-the-court article).

**The desk's day with it.** *Reading:* Playmore's diagnosis — "Każda liga na tablicy korkowej umiera tak samo
… Po trzech tygodniach drabinka wisi martwa" ([Challenger](https://join.playmore.pl/challenger/)).

**What a Kraków desk does today.** **[ABSENT]** A running challenge ladder at a Kraków club in what was read
(bo5.pl pages of Paolo and Squash4You, kluby.org Kraków listings, OpenLeague).

**What it means for the player app.** *Reading:* a ladder needs no club work per match but does need courts —
each challenge is a booking the two players make.

**Market signal.** Rare abroad; table stakes among the Polish club systems (tenis4U, kluby.org, Playmore).

### 15. How a competition holds courts in the club's calendar

**What it covers.** Courts reserved for a tournament evening or a league round; league matches booked as
ordinary bookings; released when cancelled.

**Who has it.**
- **[POLICY] Playtomic:** tournament courts "are automatically booked in your Schedule — no manual court
  blocking needed"; a recurring series is made only where courts are free
  ([create](https://helpmanager.playtomic.com/hc/en-gb/articles/20563451171985)); a league's courts and
  "timeframes when match bookings … can be automatically arranged"
  ([launch](https://helpmanager.playtomic.com/hc/en-gb/articles/20535741575057)); slots can be held only "using
  the recurring reservations feature" ([FAQs](https://helpmanager.playtomic.com/hc/en-gb/articles/20535773758097)).
- **[POLICY] MATCHi:** "Cancelling an occasion releases the court time immediately"
  ([Activities](https://matchi.zendesk.com/hc/en-gb/articles/11673332213789)); Backhandsmash: "released league
  times become available for regular bookings", and only bookings of approved customers can be cancelled from
  it ([Backhandsmash](https://matchi.zendesk.com/hc/en-gb/articles/14787431465117)).
- **[POLICY] Playmore:** "Klikasz wolny termin, wybierasz format … korty"; "anulowany turniej sam zwalnia korty
  w kalendarzu" ([turnieje](https://join.playmore.pl/turnieje/)).
- **[POLICY] kluby.org:** 2017 "Możliwość rezerwacji kortu z systemu ligowego"; 2023 "Możliwość wyłączenia
  wprowadzania przez graczy terminów spotkań bez rezerwacji" (an option to forbid match dates without a
  booking) ([2017](https://oferta.kluby.org/changelog?rok=2017), [2023](https://oferta.kluby.org/changelog?rok=2023)).
- **[POLICY] tenis4U:** "Pełna kontrola nad rezerwacjami ligowymi i turniejowymi" ([tenis4u.pl](https://tenis4u.pl/));
  a booking can carry its tournament's details (`reservationContext.tournament_details`)
  ([player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[ABSENT] LigaPadla, bo5.pl, OpenLeague:** any court booking; LigaPadla books nothing (carried,
  `platforms.md`, read 2026-10-08).

**The desk's day with it.** *Reading:* with an outside league tool the desk sees only ordinary bookings and
cannot tell a league match from any other, nor give its league price without being told.

**What a Kraków desk does today.**
- **[POLICY] Fame Sport** may move bookings for "organizacji zawodów, turniejów lub wydarzeń klubowych" (rules
  II.16) ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY] RTL** discounts league courts only if the match is planned in OpenLeague first: "warunkiem
  otrzymania zniżki jest zaplanowanie meczu w portalu www.openleague.pl przed jego rozpoczęciem"; matches count
  only at four venues (KS Grzegórzecki Wysłouchów 34, Fame Dekerta 21, Sport Factory Park Brzezie, Sport Klub
  Kryspinów) ([regulamin](https://www.openleague.pl/clubs-media/regulations/relaksmisja-tennis-league-rtl-lato-2026-2027-regulamin-fazy-grupowej.pdf?v=1791797927)).
- **[POLICY] Padel Open League:** "Uczestnicy rozgrywają mecze w kolejkach weekendowych"; "zniżka 20 zł na
  każdą godzinę gry … warunkiem … jest zaplanowanie meczu w systemie openleague.pl"
  ([regulamin](https://www.openleague.pl/clubs-media/regulations/padel-open-league-padel-open-league-2026-regulamin-fazy-grupowej.pdf?v=1791797928)).
- **[POLICY] Liga Ahoj Padel:** "Zawodnicy/pary umawiają się na mecz ligowy na wcześniej zarezerwowaną godzinę
  (kort) … Rezerwacja kortu możliwa poprzez aplikacje Padel Mates"; "Koszt wynajęcia kortu pokrywają zawodnicy.
  Cena jednej godzin meczu ligowego zazwyczaj 90 zł" ([regulamin](https://kluby.org/liga/ahoj-padel/regulamin)).
- **[POLICY]** Outside Kraków, a municipal tennis league on tenis4U: "rezerwacje kortów oraz umawianie swoich
  meczy dokonują sami uczestnicy"; "koszty najmu całego kortu ponosi zawodnik, który nie stawił się"
  ([Liga GOS Tenis 2025, Pawłowice](https://gos.pawlowice.pl/fileadmin/repozytorium/GOS/Regulamin_Ligi_GOS_Tenis_2025.pdf)).

**What it means for the player app.** *Reading:* the most common Kraków pattern — two players book an ordinary
court for a league match and split it — is a Rakieta booking with a league label. A no-show "pays 100% of the
court" in every league read, the same rule as Rakieta's.

**Market signal.** Table stakes inside club software; the Kraków gap is that league tools and booking tools
are different products.

### 16. Entry fees and how they are paid

**What it covers.** Who pays (each player, the pair, the team captain), when, how online, and refunds.

**Who has it.**
- **[POLICY] Playtomic leagues:** "One up-front fee", "Captain payment", "No match fees"; refunds only before the
  enrolment end date; teams added by the club "don't pay in Playtomic"
  ([league payments, updated 2026-10-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20535655330193)).
  Tournaments: per-player price; a player added by the club gets "a push notification and an email asking
  them to pay"; "You can collect payments before you publish the draw"
  ([add participants](https://helpmanager.playtomic.com/hc/en-gb/articles/48343795791505)); minimum not reached
  → cancelled and refunded ([cancel](https://helpmanager.playtomic.com/hc/en-gb/articles/48343157338897)).
  In Poland: Leagues 4 % and Tournaments 4 % (1,24–8,49 PLN) on top (carried,
  [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337), read 2026-10-06).
- **[PRICE] LigaPadla:** players need a licence, "Subskrypcja Miesięczna (29,99 zł / miesiąc)" or "Licencja
  Roczna (199,99 zł / rok)"; entry fees go through Przelewy24, which "pobiera środki jako pośrednik, a następnie
  rozlicza się z Organizatorami (Klubami)"; refund of the entry if leaving more than 48 h ahead, the Przelewy24
  commission never ([regulamin usługi](https://ligapadla.pl/regulamin)). Its competition rules say instead
  "zwrot wpisowego pomniejszony o 5 zł opłaty manipulacyjnej" ([regulamin rozgrywek](https://ligapadla.pl/regulamin-rozgrywek)).
  It cites the law: no 14-day withdrawal for sports events "oznaczonych co do dnia" (art. 38 pkt 12).
- **[POLICY] tenis4U:** "wpisowe online" or "bez wpisowego"; "Pobieranie wpisowego online wymaga aktywacji
  konta u operatora płatności"; "Usunięcie gracza spowoduje pełny zwrot wpisowego"
  ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] kluby.org:** 2020 "Płatność za turniej online", "Automatyczne potwierdzanie uczestnika turnieju po
  płatności"; 2019 lists "do zbierania wpisowego na poszczególny dzień" ([2020](https://oferta.kluby.org/changelog?rok=2020),
  [2019](https://oferta.kluby.org/changelog?rok=2019)). A Warsaw-area event charges "170 zł/os. (przy płatności
  on-line przez kluby.org …) lub 200 zł/os. (płatność w recepcji)" ([turniej 12301](https://kluby.org/turnieje/12301)).
- **[POLICY] Playmore:** "Wpisowe i limit graczy ustawiasz przy tworzeniu turnieju" ([turnieje](https://join.playmore.pl/turnieje/)).

**The desk's day with it.** *Reading:* cash on the night is still common, so the desk keeps a "who has paid"
list; unpaid entrants are the no-shows.

**What a Kraków desk does today.**
- **[PRICE] Squash4You league:** "opłata wpisowa … wynosi 120zł" (−20 zł for returning players) plus "Opłata za
  każdą kolejkę wynosi 95zł … przelewem lub w dniu rozgrywek w recepcji"; less than 24 h' notice → "pełną
  opłatę za tę kolejkę" ([regulamin](https://bo5.pl/squash4you/Dunlop+Krakowska+Liga+Squash4You,rules,1270,2666.html)).
- **[PRICE] Paolo, Amatorska Liga Squasha:** "Wpisowe za cały sezon wynosi 100 zł, lub 160zł pakiet z koszulką
  ligową … płatne gotówką"; "opłata za kolejkę ligową wynosi 80 zł, można użyć kart Benefit/Medicover"
  ([regulamin](https://bo5.pl/paolo/Amatorska+Liga+Squasha+,rules,1216,2678.html)).
- **[PRICE] RTL:** "180 zł (rozgrywki singlowe) oraz 270 zł od pary deblowej", by Przelewy24 at sign-up, cash or
  card at the KS Grzegórzecki desk, or bank transfer ([regulamin](https://www.openleague.pl/clubs-media/regulations/relaksmisja-tennis-league-rtl-lato-2026-2027-regulamin-fazy-grupowej.pdf?v=1791797927)).
- **[PRICE] Padel Open League:** "270 zł" per pair, the same three ways ([regulamin](https://www.openleague.pl/clubs-media/regulations/padel-open-league-padel-open-league-2026-regulamin-fazy-grupowej.pdf?v=1791797928)).
- **[PRICE] Liga Ahoj Padel:** "200 zł od osoby … należy wpłacić na recepcji klubu" ([regulamin](https://kluby.org/liga/ahoj-padel/regulamin)).
- **[PRICE] Padel Krakow League:** 280 zł a pair by bank transfer (carried, `local-market.md`, read 2026-10-08).

**What it means for the player app.** *Reading:* an entry fee is paid once for a season or an evening, by one
player for a pair or each for himself — shapes Rakieta's per-seat charge already half covers.

**Market signal.** Table stakes; Kraków still mixes cash, transfer and Przelewy24.

### 17. Results feeding a ranking or a level

**What it covers.** Scores entered (by players or the desk), standings, a ranking across events, and a rating
that changes with results and decides who may enter what.

**Who has it.**
- **[POLICY] Playtomic:** league standings from scores players can enter; levels move "After every competitive
  match", tournaments do not ([levels](https://helpmanager.playtomic.com/hc/en-gb/articles/20563641264145),
  [FAQ](https://helpmanager.playtomic.com/hc/en-gb/articles/48343795791505)). Certified clubs run paid
  "Playtomic leveling" sessions; afterwards the player's "reliability … will be set to 50%"
  ([leveling clubs](https://playerhelp.playtomic.com/hc/en-gb/articles/19832024478097)).
  **[COMPLAINT]** "Rubbish experience using coach level assessment, £28" (UK, 6 Mar 2026) (carried,
  [App Store GB](https://apps.apple.com/gb/app/playtomic-padel-tennis/id1242321076?see-all=reviews), read 2026-10-06).
- **[POLICY] LigaPadla:** the ranking counts "24 najlepiej punktowane turnieje … w ostatnich 365 dniach", plus
  all-time and club rankings; americano points by place; level multipliers "C x1.0 … B3 x1.5 … B2 x2.0 … B1
  x2.5 … A x3.0"; after 20 matches a "Współczynnik Formy" over up to 100 matches decides entry: own level,
  any higher, "maksymalnie o 1 poziom niżej" ([regulamin rozgrywek](https://ligapadla.pl/regulamin-rozgrywek)).
- **[POLICY] tenis4U:** a general ranking adding tournament bonus points; a "Mecz rankingowy" switch that
  "cofnie graczom naliczone punkty rankingowe" when turned off ([panel demo script](https://test-panel.tenis4u.pl/main.2b865c996e568707.js));
  the player app has ELO screens ("Brak meczów rankingowych", rating history) ([player app script](https://app.tenis4u.pl/main.cf446af5e9523413.js)),
  which `integration.md` read as switched off.
- **[POLICY] PADO:** "Profiles with match history and ELO rating"; "For Federations … Connect rankings players
  already use. Coming soon" ([pado.app](https://pado.app)).
- **[POLICY] kluby.org:** hosts the Polish padel association's cycle — "Polski Związek Padla": Ranking,
  Licencje, "Punkty za miejsce" by tier (CLUB A … Club Series Tour) ([cykl PZP](https://kluby.org/cykl/pzp),
  [punktacja](https://kluby.org/cykl/pzp/punktacja)) — and a "Rating padlowy" list of 11 466 entries
  ([ratingi](https://kluby.org/padel/ratingi)).
- **[POLICY] MATCHi:** Padelboard's "Beat the Box" keeps "a persistent venue ranking, marketed as MATCHi
  Playlist" ([Padelboard](https://matchi.zendesk.com/hc/en-gb/articles/14502314451101)).
- **[PRICE] CourtReserve:** DUPR ratings sync "in real time", usable "as registration restrictions"; "$25/month
  add-on for Launch plans" ([DUPR](https://help.courtreserve.com/en/articles/8265424-courtreserve-dupr-integration)).
- **[POLICY] Padel levels in Poland:** the Polish Padel Federation's scale A, A2, B1, B2, B3, C, e.g. "B3 –
  zawodnicy początkujący … C – zawodnicy rozpoczynający grę" (quoted as annex 1 of a municipal tournament rule,
  [POSiR Poznań, 2026-07-24](https://www.posir.poznan.pl/images/cykle/posir_open/2026/2026.07.24_Zarz%C4%85dzenie_Regulamin_turniej%C3%B3w_padlowych.pdf)).

**The desk's day with it.** *Reading:* the desk's job is seeding and policing sandbaggers; the organisers'
rules all reserve the right to move a player up.

**What a Kraków desk does today.**
- **[POLICY] Squash4You** seeds round 1 by "rankingu Polskiego Związku Squasha"; ranking points = points won +
  group value ("grupa A - 100 pkt., grupa B - 80 pkt."); "Do rankingu końcowego liczy się 7 najlepszych kolejek"
  ([regulamin](https://bo5.pl/squash4you/Dunlop+Krakowska+Liga+Squash4You,rules,1270,2666.html)).
- **[POLICY] Paolo** seeds by "rankingu PZSQ, maksymalnego rankingu PZSQ oraz indywidualnej ocenie poziomu"
  ([regulamin](https://bo5.pl/paolo/Amatorska+Liga+Squasha+,rules,1216,2678.html)).
- **[POLICY] RTL** tests newcomers: "W dniach 20.11.2026 - 27.11.2026 nastąpi sprawdzenie umiejętności nowo
  zapisanych uczestników"; coaches and former players are not "amatorzy" except in Top Pro and Pro without a
  PZT licence ([regulamin](https://www.openleague.pl/clubs-media/regulations/relaksmisja-tennis-league-rtl-lato-2026-2027-regulamin-fazy-grupowej.pdf?v=1791797927)).
- **[POLICY] "Leagues in Krakow"** series: "PZP ranked, CST B2"; "The players accumulate points at every
  tournament under the PZP ranking B2" ([turniej 12339](https://kluby.org/turnieje/12339)).
- **[POLICY]** The Padel Krakow League levels unranked players "by self-evaluation over WhatsApp" (carried,
  `local-market.md`, read 2026-10-08).

**What it means for the player app.** *Reading:* Rakieta's questionnaire gives a Level per sport; Kraków's
organisers speak letters (C to A) and squash leagues seed by the PZSq ranking. A Level that league results
move, and that maps to the letters, is the bridge the deck and the leagues would share.

**Market signal.** Standings and rankings are table stakes; a rating that gates entry is rare (LigaPadla's
form coefficient, CourtReserve's DUPR restriction).

### 18. Outside competition tools, federations and licences

**What it covers.** The specialised tools and federation systems Polish clubs and players already use — what a
club would have to keep, link to, or replace.

**Who has it.**
- **[PRICE] LigaPadla.pl** (LigaPadla.pl sp. z o.o., Warsaw): free to clubs, paid by players (block 16); "ponad
  200 turniejów miesięcznie"; it calls itself not the organiser but "Federacją inicjującą, rozwijającą i
  administrującą rozgrywki" ([jak gramy](https://ligapadla.pl/jak-gramy/),
  [regulamin rozgrywek](https://ligapadla.pl/regulamin-rozgrywek)).
- **[POLICY] bo5.pl:** squash tournaments and leagues since 2013 (block 12); it also runs the PZSq licence and
  ranking pages linked from the federation ([PZSq licences](https://polskisquash.pl/rozgrywki/licencje)).
- **[PRICE] PZSq licence:** "Obowiązuje jeden rodzaj licencji zawodniczej"; seniors 30 zł a month or 110 zł for
  12 months; "obowiązkowa we wszystkich rozgrywkach PZSQ" ([licencje](https://polskisquash.pl/rozgrywki/licencje)).
- **[PRICE] PZT "Tenis Open Polska" (TOP)** for amateurs: entries "za pośrednictwem TPO"; a year's licence 65 zł
  for adults aged 26–60 in a PZT club (75 zł outside one; 50 or 60 zł under 26 and over 60), one-off 20 or 10 zł; "jedynej oficjalnej liście rankingowej TOP w Polsce" (programme rules
  in force from 1 Jan 2021, as published by
  [OSiR Suwałki](https://osir.suwalki.pl/wp-content/uploads/2025/07/regulamin-RECMAN-CUP.pdf)).
- **[POLICY] kluby.org:** the Polish padel association's cycle and licence list ([cykl PZP](https://kluby.org/cykl/pzp/licencje)),
  and a home for independent organisers such as "Leagues in Krakow" ([organiser](https://kluby.org/osrodek/leagues-in-krakow)).
- **[POLICY] OpenLeague.pl:** organiser "Klub Sportowy Grzegórzecki, Aleja Pokoju 16, 31-564 Kraków"; leagues
  "Relaksmisja Tennis League", "Padel Open League", "Lekarski Tenis", "UBS SUMMER LEAGUE"
  ([openleague.pl](https://www.openleague.pl/)).
- **[POLICY] ActiveNow** (Activenow sp. z o.o.): sign-ups, payments, attendance and instructor payroll for
  schools ([activenow.io](https://activenow.io/en)); used by teniskrakow.pl.
- **[POLICY] MATCHi's satellites:** Padelboard (own), Backhandsmash (league platform), Matchable (external
  academy software) (blocks 2, 11, 13).
- **[ABSENT]** Rankedin or Tournament Software at a Kraków club or a Polish federation (web searches
  "rankedin.com Polska padel turniej Kraków", "PZT system turniejowy … tournamentsoftware": nothing).

**The desk's day with it.** *Reading:* a Kraków squash desk already lives in two systems — courts in
Playmore or its own, competitions in bo5.pl — and keys the same players into both.

**What a Kraków desk does today.** See the table below: of the 12 Kraków competitions whose tool is known,
none runs in the booking software of the club whose courts it uses.

**What it means for the player app.** *Reading:* federation licences and rankings are external facts a
player carries; LigaPadla and bo5.pl are where Kraków's competitive players already have profiles.

**Market signal.** Polish competition is a separate ecosystem from booking; replacing it is a choice, linking
to it the cheaper default the rivals took (Playmore links to LigaPadla).

## Kraków on 2026-10-12

### Competitions

| Competition | Sport | Organiser | Tool | Fee | Courts |
| --- | --- | --- | --- | --- | --- |
| Padel Krakow League | padel | "Leagues in Krakow", an organiser account on kluby.org | kluby.org + WhatsApp community | 280 zł a pair (carried) | any Kraków facility; players pay the court (carried); 56 players listed ([kluby.org](https://kluby.org/padel/rozgrywki/krakow)) |
| "Series – Win a Babolat Viper", 4th round, 23.10.2026 | padel | Leagues in Krakow; cycle "Polski Związek Padla" | kluby.org | 130 PLN per player | Libertów Padel, 8 pairs on 2 courts, 20:00–midnight ([turniej 12339](https://kluby.org/turnieje/12339)) |
| Americano Español | padel | Leagues in Krakow | kluby.org | 100 PLN per person | Libertów, 8 players, 2 courts ([organiser](https://kluby.org/osrodek/leagues-in-krakow)) |
| Americano B3/C, 28.11.2025 | padel | Padel House | LigaPadla | 90 zł (carried) | Padel House |
| Padel Open League 2026 | padel | Stowarzyszenie KS Grzegórzecki | openleague.pl | 270 zł a pair | Fame Sport, Dekerta 21; weekend rounds; max 10 pairs per category ([regulamin](https://www.openleague.pl/clubs-media/regulations/padel-open-league-padel-open-league-2026-regulamin-fazy-grupowej.pdf?v=1791797928)) |
| Relaksmisja Tennis League, Zima 2026/27 | tennis | KS Grzegórzecki | openleague.pl; courts via desk or tenis4U | 180 zł singles, 270 zł a doubles pair | 4 venues; players book and pay at league prices; prizes "o wartości 95 000 zł" ([regulamin](https://www.openleague.pl/clubs-media/regulations/relaksmisja-tennis-league-rtl-lato-2026-2027-regulamin-fazy-grupowej.pdf?v=1791797927)) |
| Liga Ahoj Padel 2026 | padel | Ahoj Padel (Niepołomice) | kluby.org; courts on Padel Mates | 200 zł a person at the desk | Ahoj Padel only, ~90 zł an hour paid by players; 60 players ([regulamin](https://kluby.org/liga/ahoj-padel/regulamin)) |
| Dunlop Krakowska Liga Squash4You 2026/27 | squash | Squash4You s.c. | bo5.pl | 120 zł + 95 zł a round | Squash4You, 8 Saturday rounds from 14:00 ([regulamin](https://bo5.pl/squash4you/Dunlop+Krakowska+Liga+Squash4You,rules,1270,2666.html)) |
| Klubowa Liga Squasha | squash | Squash4You | bo5.pl | not stated | monthly rounds ([bo5.pl](https://bo5.pl/squash4you)) |
| Amatorska Liga Squasha, season 3 | squash | Paolo Squash Club | bo5.pl | 100 zł season (160 zł with shirt), cash, + 80 zł a round | Paolo, 12 rounds 11.10.2026–14.03.2027 ([bo5.pl](https://bo5.pl/paolo)) |
| Profesjonalna Liga Squasha | squash | Paolo Squash Club | bo5.pl | not read | monthly, Oct 2026–Jun 2027 ([bo5.pl](https://bo5.pl/paolo)) |
| Head Squash Open vol. 6 B++ | squash | Paolo Squash Club | bo5.pl | 120 zł (open), 100 zł (women) | Paolo; PZSq licence required ([event](https://bo5.pl/t7813/Head+Squash+Open+vol.+6+B%2B%2B.html)) |
| Business Tennis League | tennis | not identified | not identified | not identified | team of 2–4; 37th edition (search summary only) |

### Coaching prices

| Who | Lesson | Groups / academy | Courts |
| --- | --- | --- | --- |
| teniskrakow.pl, independent school ([cennik](https://teniskrakow.pl/cennik/)) | 130 zł + court; 2 players 70 zł each + court | 3 players 95 zł each, 4 players 75 zł each, court included; billed monthly | court fees it lists at 5 venues, 100–140 zł an hour |
| Fame Sport ([cennik](https://famesport.pl/cennik/)) | 120 / 125 / 140 zł an hour for 1 / 2 / 3 players + court | kids 280–545 zł a month; adults 500 / 800 zł a month | tennis hall winter 100–140 zł; padel hall winter 135–150 zł |
| Squash4You ([cennik](https://www.squash4you.pl/cennik), [trenerzy](https://www.squash4you.pl/trenerzy)) | court + 40–60 zł, or "około 100-120zł" + court | group classes 50–55 zł an hour; passes 180 zł / 60 days, 300 zł / 90 days | — |
| Paolo, Garden Padel, Padel House, Bajada, Libertów, Morelowa 34 | **[ABSENT]** no published lesson price | — | — |

## Rivals × features

Y has it (read) · P part of it · – looked for, not found · ? not checked.

| Feature | Playtomic | MATCHi | Eversports | CourtReserve | tenis4U | Playmore | kluby.org | PADO | LigaPadla | bo5.pl | OpenLeague | ActiveNow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Coach profiles and logins | Y (paid web app) | Y | Y | Y | Y | Y (free app) | Y | Y | – | – | – | P |
| 2 Lessons and classes on the court calendar | Y | P (planner does not block) | P | ? | Y | Y | Y | ? | – | – | – | – |
| 3 Player books a private lesson | Y | Y | Y (beta) | Y | – | Y | ? | Y | – | – | – | P |
| 4 Coach availability | Y | Y | Y | Y | ? | Y | Y | Y | – | – | – | ? |
| 5 Coach pay and rates | P (reports) | – | Y | P (reports) | Y | Y | Y | P | – | – | – | Y |
| 6 Classes with a cap and a waiting list | P (no waiting list) | Y | Y | Y | Y | Y | Y | ? | – | – | – | ? |
| 7 Auto-cancel for too few | Y (public) | Y | Y | ? | Y | P | P | ? | – | – | – | ? |
| 8 Courses, terms, passes | Y | P (invoices) | Y | ? | ? | Y | Y | ? | – | – | – | Y |
| 9 Attendance and make-ups | – | P | ? | ? | ? | Y | Y | ? | – | – | – | Y |
| 10 Children and parents | P | P | ? | Y | ? | Y | Y | ? | – | – | – | ? |
| 11 Americano / mexicano | Y | Y (add-on) | ? | ? | – | Y | Y | Y | Y | ? | – | – |
| 12 Brackets, draw, seeding | – | ? | ? | ? | Y | P | Y | Y | Y | Y | P (play-off) | – |
| 13 Leagues | Y | Y (Backhandsmash) | ? | P (pickleball) | Y | P | Y | P | Y | Y | Y | – |
| 14 Challenge ladders | – | Y | ? | ? | Y | Y (249 zł) | Y | ? | – | ? | – | – |
| 15 Competition courts in the calendar | Y | Y | ? | ? | Y | Y | Y | ? | – | – | – | – |
| 16 Online entry fees | Y | Y | ? | ? | Y | Y | Y | Y | Y | ? | Y | Y |
| 17 Results → ranking or rating | Y | P | ? | P (DUPR) | Y | Y | Y | Y | Y | Y | Y | – |

## Gaps

- **Kraków padel coaching:** no Kraków padel club publishes lesson prices or says whether its coaches are
  employed, rent courts, or pay the club a share. Ask a real club.
- **The coach's contract with a Kraków club** — rent per hour, a percentage, or employment — is published
  nowhere read; only the outcomes (lesson + court prices, Miazga's ban, Squash4You's pass rule) are.
- **Business Tennis League** (Kraków, 37th edition): the article would not load; organiser, tool and fee
  unknown. Kraków tennis leagues on tenis4U itself were not found (tenis4U's terms forbid automated reading,
  so its tournament map was not queried).
- **Garden Padel, Padel House and Morelowa 34 competitions:** whether they run their own leagues or ladders,
  beyond LigaPadla americanos and WhatsApp matchmaking (Instagram and Facebook need a login).
- **Playmore:** whether Challenger and the school module are used by any Kraków squash club (Atras' site
  answered 403), and the price of its school module outside the subscription.
- **Playtomic:** price of the Coach web app ("Consult your CSM"); whether classes have a waiting list in the
  player app (none in the manager help).
- **Eversports and CourtReserve:** their tournament, ladder and attendance features were not read.
- **The Polish padel body's name and rules:** kluby.org shows "Polski Związek Padla"; a municipal rule quotes
  "Polskiej Federacji Padla"; whether these are one body, and its licence price, were not established.
- **LigaPadla's refund rule** says two different things (refund minus 5 zł, or refund minus the Przelewy24
  commission); which applies was not established.
- **Squash4You's lesson price** (court + 40–60 zł, or 100–120 zł + court): the two pages disagree.
- **Kraków ladders:** none found; whether any club runs one on paper or in Playmore is unknown.
- **VAT on lessons sold by a club through a platform** beyond the PKWiU line carried from earlier research.
