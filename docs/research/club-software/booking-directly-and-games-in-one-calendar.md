# Players booking a court directly, and the Games deck in one calendar

Research for the club-software grilling ("Raketa becomes the club's booking software"), areas 2 and 3: what
rivals let a player do when booking a court directly (in their app, on the club's website, or with no app at
all), and how rivals let open matches and private bookings share one calendar, so each feature can be
decided Build at launch · Build later · Leave out · Ask a real club.

**Extends** [`integration.md`](integration.md) and, in `../games-and-fill-in/`,
[`topics/competitor-organiser.md`](../games-and-fill-in/topics/competitor-organiser.md),
[`topics/competitor-joiner.md`](../games-and-fill-in/topics/competitor-joiner.md),
[`topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md),
[`topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`topics/local-market.md`](../games-and-fill-in/topics/local-market.md),
[`areas/COURTS.md`](../games-and-fill-in/areas/COURTS.md) and
[`topics/gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md). Facts carried from there say
"carried" and keep their read date; everything else was read **2026-10-12**.

**This file decides nothing.** It does not estimate what anything would cost Raketa to build.

**Sources.** Playtomic's and MATCHi's help centres were read through their public Zendesk API (the HTML
answers 403); the dates in brackets are each article's own "updated" date. Playmore's and tenis4U's interface
text comes from the JavaScript their web apps serve to every visitor: Playmore's string files
`CG9yQPLY.js` and `93jAIRDY.js` and its club pages' embedded data; tenis4U's player app
(`main.cf446af5e9523413.js` and its two shared-booking chunks) and its club panel
(`main.333e76605ded56e6.js`, served with Last-Modified 2026-10-04). Each tenis4U file was fetched once, not
crawled. File names with a hash change when the vendor ships, so a link may stop resolving. Nobody signed in,
booked or paid, and no endpoint was called.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price
· `[DOCS]` a provider's developer or help document about a third party · `[LAW]` a statute · `[COMPLAINT]`
one person's account · `[ABSENT]` looked for and not found, saying where. Lines marked *reading* are
inferences, not sources.

**Raketa today, for comparison.** The player app books a court only through the Games deck: a game is one
hour, up to 14 days ahead, the last yes books the court at once and holds each share on the card until the
club's cut-off (default 24 h). A club hands Raketa a weekly block ("Only Raketa") released back N days before.

## Read this first

- **Every rival that sells courts to players lets them book a whole court directly**: find the club, pick a
  day, an hour and a length, pay, done. Playtomic adds "Pay your part" at the same checkout; tenis4U and
  Playmore let the organiser book and then collect from the others (§2.1, §2.2).
- **A split never leaves the club short.** Playtomic charges unpaid shares to the booking owner 2 h after
  the game (carried); tenis4U warns "Jako organizator zostaniesz obciążony pozostałą kwotą"; Playmore makes the
  organiser pay the whole court first and only then "Poproś o spłatę" (§2.2).
- **Polish club software lets the club demand prepayment and drops unpaid bookings fast**: tenis4U "Płatność
  tylko online … usunięcie rezerwacji w ciągu 20 minut", Playmore 30 minutes, and a per-court choice of online
  only / online or at the club / at the club only (§2.5, §2.6).
- **The club's booking rules are the same five settings everywhere**: days ahead, cancellation hours,
  per-day limit, active-bookings limit, minimum length. Kraków's Playmore squash clubs all run 14 days ahead
  and 24 h cancellation (§2.4, §2.7, §2.8).
- **Members booking earlier is standard in club software**, and MATCHi has the closest analogue yet to
  Raketa's release lead: a *booking restriction* that keeps chosen hours for a group of customers "until
  72 hours before the slot starts", after which "anyone can book the slot" (§2.10, §3.11).
- **People without the app reach the club through a link or a widget.** Playtomic (iframe), MATCHi (booking
  widget), Eversports (widget) and Playmore (club-branded booking page) offer one; tenis4U and kluby.org only a
  link. Only Playmore books with a phone number and an SMS code instead of an account (§2.14–2.16).
- **No court platform is a Reserve with Google partner** (441 partners listed, none of Playtomic, MATCHi,
  Eversports, CourtReserve, Playmore, tenis4U, kluby.org); a club can still put any booking URL on its Google
  profile. Facebook's own booking integration ended on 8 June 2022, per a vendor's help page (§2.17, §2.18).
- **Two ways to put open games in one calendar.** Playtomic (and Padel Mates, copying it) books the court in
  stages and lets "private reservations always take priority over open matches that aren't full"; Playmore,
  MATCHi and tenis4U book the court the moment the game exists, so first come wins (§3.1, §3.8).
- **Only Playmore lets a club fence open play**: off-peak hours only, a separate cap on peak-hour games, a
  club-paid off-peak discount, and the 1–48 h cut-off. Playtomic's club controls are sport, format, level and
  (unexplained) a "Courts" field (§3.2–§3.6).
- **Late court assignment is Playtomic's alone** ("Pending to assign", "the system automatically assigns
  courts as the match time approaches"); a Kraków regulamin already says a change of court number "nie stanowi
  odwołania rezerwacji" (§3.9).

---

## Area 2 — Players booking a court directly

### 2.1 Find a club, see free hours, choose a length, book the whole court

**What it covers.** The plain private booking: the player picks club, day, hour, court and length and pays.

**Who has it.**
- **[POLICY] Playtomic:** "Tap 'Book a court' … Select your sport … Choose where you want to play … Select the
  date and time … Select the court and duration … Choose if you want to pay your part (split payment) or if
  you want to pay everything. In the same screen you will see the cancellation policy"
  ([help, 2026-08-17](https://playerhelp.playtomic.com/hc/en-gb/articles/19831881490449)). A club page has a
  *Book* tab and an *Open Matches* tab
  ([help, 2026-09-01](https://playerhelp.playtomic.com/hc/en-gb/articles/19831715222929)). Lengths are what the
  club's price rules allow, in 15-minute multiples from 15 to 180 minutes
  ([Flexible Booking Duration, 2026-04-01](https://helpmanager.playtomic.com/hc/en-gb/articles/20534683083793)).
- **[POLICY] MATCHi:** one checkout for "the mobile app, the web booking flow, and the booking widget"
  ([New Checkout, 2026-09-08](https://matchi.zendesk.com/hc/en-gb/articles/14135337263005)); adjacent slots
  "merge into a single booking"
  ([help, 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/18511790370461)).
- **[POLICY] Playmore:** "Gracze rezerwują o 23:00 w piątek - z aplikacji albo z Twojej własnej strony
  rezerwacji" — players book at 23:00 on a Friday, from the app or the club's own booking page
  ([dla klubów padla](https://join.playmore.pl/dla-klubow-padla/)). A cart takes several hours at once:
  "Koszyk mieści maksymalnie {max} rezerwacji" ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] tenis4U:** the court page and booking flow in the player app; one backend with the desk (carried,
  [integration.md §5](integration.md)).
- **[POLICY] kluby.org:** a booking makes a contract "pomiędzy Użytkownikiem a Klubem" under the club's
  regulamin ([regulamin §IV.7](https://kluby.org/regulamin)).

**The desk's day with it.** *Reading:* nothing; the booking lands in the same calendar the desk works from,
which is why every one of these is also the club's software ([integration.md](integration.md) "Read this
first").

**What a Kraków desk does today.** Every Kraków regulamin read lists three doors: online, phone and desk.
Garden Padel: "online przez system rezerwacji na stronie www.gardenpadel.pl lub aplikację tenis4U,
telefonicznie w godzinach pracy recepcji, osobiście w recepcji"
([regulamin §4](https://gardenpadel.pl/regulamin/)). Fame Sport: "telefonicznie, osobiście w recepcji Klubu lub
za pośrednictwem aktualnie stosowanego przez Klub systemu rezerwacyjnego"
([regulamin II.2](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
Atras: "osobiście w recepcji klubu lub za pomocą systemu rezerwacji on-line poprzez stronę internetową klubu
oraz za pomocą aplikacji" ([regulamin](https://www.atrassquash.pl/regulamin/)). Squash4You adds "telefonicznie"
([regulamin 5a](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** *Reading:* this is the one booking path every rival has and Raketa does
not; without it a Raketa club's players need a second app to book a court for four friends.

**Market signal.** Table stakes.

### 2.2 Pay the whole court, or pay your part — and who covers unpaid shares

**What it covers.** Whether one person pays the court, or each pays a share; what happens to a share nobody
pays.

**Who has it.**
- **[POLICY] Playtomic:** "Pay your part" or "Pay everything" at checkout; "Split payment is not available on
  the Playtomic website"; unpaid shares are charged to the owner 2 h after the match; in Poland most likely
  as a debt that blocks new bookings (all carried,
  [competitor-organiser §3](../games-and-fill-in/topics/competitor-organiser.md), read 2026-10-08). New detail:
  "If you do not invite any players to join you in the match, you will be charged for the total reservation
  fee, 2 hours after the match ends"; "Debts must be paid off until you can make another reservation"
  ([help, 2026-09-07](https://playerhelp.playtomic.com/hc/en-gb/articles/19831869050769)); "In some clubs,
  single payments are not allowed due to club configuration. In these cases, pre-authorization is mandatory"
  ([Payment Guidelines FAQ, 2026-09-19](https://playerhelp.playtomic.com/hc/en-gb/articles/26569889841169)).
  "Split Payment is not available for guest bookings"
  ([Manager strings](https://manager.playtomic.io/locales/en/matches.json)).
- **[POLICY] tenis4U** ("Rezerwacje współdzielone"): the organiser chooses `ORGANIZER_PAYS` or
  `PAY_MY_SHARE`; joiners read "Opłacone przez organizatora" or "Każdy uczestnik płaci swoją część"; until the
  organiser pays, "Oczekiwanie na płatność organizatora — Po opłaceniu przez organizatora będziesz mógł zapłacić
  swoją część"; the organiser is told "Odpowiadasz za pełną opłatę rezerwacji … Jako organizator zostaniesz
  obciążony pozostałą kwotą w przypadku braku pełnej płatności przez resztę uczestników" — you answer for the
  full price and are charged the rest if the others don't pay
  ([shared-booking chunk](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3_module_ts.b8c3629f5a4e1beb.js),
  [join chunk](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3-join_module_ts.a7f31903187e991f.js)).
  A club setting reads "Auto-anulowanie rezerwacji współdzielonych przed terminem" — auto-cancel shared
  bookings before the start ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
- **[POLICY] Playmore:** the organiser pays the whole court, then asks: "Rezerwacja jest opłacona przez
  Ciebie. Poproś ekipę o zwrot — po {amount} od osoby"; "Każdy płaci równą część pełnej ceny kortu. Prośba
  przyjdzie w powiadomieniu z aplikacji albo SMS-em, z linkiem do zapłaty"; a cancelled request "zostaje na
  Tobie — rezerwacja jest opłacona, więc nic nie musisz dopłacać"; "Ten klub nie obsługuje jeszcze podziału
  kosztów" ([strings](https://playmore.pl/assets/CG9yQPLY.js)).
  - *Reading:* the club is paid in full at booking; the split is between players, through Playmore's wallet.
- **[POLICY] MATCHi** and **kluby.org:** the booker covers co-players who haven't paid 2 h after the game
  (carried, [platforms §4, §7](../games-and-fill-in/topics/platforms.md), read 2026-10-06/08).

**The desk's day with it.** *Reading:* none at Playmore and tenis4U (the court is paid or the organiser owes
it); at Playtomic a desk must mark at-the-club shares paid within 2 h of the end, or the owner is charged and
"the club will need to refund the booking owner directly" (carried).

**What a Kraków desk does today.** "osoba dokonująca rezerwacji zobowiązana jest do uiszczenia pełnej opłaty"
(Fame Sport, carried); Squash4You charges "osoba na którą widnieje rezerwacja"
([regulamin 5d](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** *Reading:* Raketa's deck already splits a court four ways with each
share held until the cut-off; a direct booking could reuse the share, but rivals all name one person who
answers for the whole court, which the deck does not.

**Market signal.** Table stakes (split exists at every platform read); who carries an unpaid share differs.

### 2.3 Inviting the other players

**Who has it.**
- **[POLICY] Playtomic:** invite by name, email, phone or link (carried); after booking, "Use the share link to
  invite specific players" ([help](https://playerhelp.playtomic.com/hc/en-gb/articles/19831881490449));
  inviting needs a verified phone ([help, 2026-09-29](https://playerhelp.playtomic.com/hc/en-gb/articles/51110112972561)).
- **[POLICY] tenis4U:** "Zaproś graczy", "Ostatnio grani", "Link do zaproszenia", "zaprasza Cię do wspólnej gry",
  "Zaloguj się, aby dołączyć do rezerwacji" ([chunks](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3-join_module_ts.a7f31903187e991f.js)).
- **[POLICY] Playmore:** "Zaproś współgraczy", "Dopisz współgraczy", a payment link "na WhatsAppie"
  ([strings](https://playmore.pl/assets/CG9yQPLY.js)).

**The desk's day with it.** *Reading:* none.

**What a Kraków desk does today.** **[ABSENT]** in the regulaminy read (Garden Padel, Fame Sport, Atras,
Squash4You): none mentions inviting.

**What it means for the player app.** *Reading:* Raketa's group already is the invite list; a direct booking
would need a way to name the three others, from the group or by link.

**Market signal.** Table stakes.

### 2.4 The cancellation window

**Who has it.**
- **[POLICY] Playtomic:** the club sets "Cancellation Time (hours)"; a member category can have its own
  ([Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297),
  [Membership, 2026-09-13](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745)); checkout shows
  the deadline as a date (carried).
- **[POLICY] MATCHi:** "Free cancellations (hours in advance)" and, new to this research, "Late cancellation
  refunds (%) … if set to 50%, a customer who cancels too late gets back 50% of what they paid"
  ([Schedule settings, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005)).
- **[POLICY] tenis4U:** separate hours for one-off and standing bookings, "0 = bez limitu"
  ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)); the player sees "Rezerwację można odwołać do
  {max_hours} godzin przed rozpoczęciem gry" ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)); a refund
  comes "z potrąceniem kosztów serwisowych wynoszących 2%"
  ([chunk](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3_module_ts.b8c3629f5a4e1beb.js)).
- **[POLICY] Playmore:** per club, `"time_to_free_cancellation":24` at Atras, Paolo and Squash4You
  ([Atras page data](https://playmore.pl/klub/atras-squash-club/)).

**What a Kraków desk does today.** 24 h everywhere read: Garden Padel "do 24 godzin przed terminem gry"
([§5](https://gardenpadel.pl/regulamin/)); Atras "23 godzin … telefonicznej oraz w recepcji" or "24 godzin …
przy użyciu aplikacji mobilnej" ([regulamin](https://www.atrassquash.pl/regulamin/)); Fame Sport 24 h, standing
slots 48 h, and "Rezerwacja dokonana na mniej niż 24 godziny przed planowanym terminem gry jest wiążąca" — a
booking made inside 24 h is binding at once
([II.5–6, III.8](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
Squash4You keeps an online payment cancelled in time as credit: "zostanie przeniesiona na kolejną, najbliższą
rezerwację ale nie podlega zwrotowi" ([5h](https://www.squash4you.pl/regulamin)). Atras alone grants a 14-day
withdrawal "od umowy zawartej przez Internet", lost once the service is used
([regulamin](https://www.atrassquash.pl/regulamin/)) — more than the law requires (art. 38 pkt 12 excludes
dated sport services, carried).

**What it means for the player app.** *Reading:* Raketa's cut-off (default 24 h) already matches the city; a
direct booking would need the same number shown before paying.

**Market signal.** Table stakes; a partial late refund (MATCHi) is rare.

### 2.5 Paying at the club, or prepayment required

**Who has it.**
- **[POLICY] Playtomic:** "Cash or card at the Club (This option is only available in selected regions and
  under special conditions)" ([player help, 2026-09-01](https://playerhelp.playtomic.com/hc/en-gb/articles/19831969439761));
  "Playtomic Manager has no setting to block payment at the club" for the other shares of a split; "Website
  bookings and app bookings with Single Payment are always paid in full online"
  ([Split vs Single, 2026-10-08](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721)).
- **[POLICY] tenis4U:** per court, "Płatność tylko w klubie" / "Płatność w klubie lub online" / "Płatność tylko
  online" ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)); the panel asks "Chcesz ustawić płatności
  tylko online?" ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)); a pay-later booking reads "Twoja
  rezerwacja została potwierdzona. Płatność zostanie rozliczona na miejscu w klubie"
  ([chunk](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3_module_ts.b8c3629f5a4e1beb.js)).
- **[POLICY] Playmore:** methods "Zapłacę później — Gotówka lub karta w obiekcie", "Karnet", "Płatność online";
  "Płatność wymagana"; and the reverse: "Tę rezerwację możesz opłacić wyłącznie na miejscu lub karnetem —
  zgodnie z cennikiem wybranym przez obiekt" ([strings](https://playmore.pl/assets/CG9yQPLY.js)). Clubs are sold
  "Przedpłaty i kaucje: Karta lub BLIK przy rezerwacji. Brak płatności = brak rezerwacji, a kaucja zabezpiecza
  odwołania w ostatniej chwili" ([dla klubów padla](https://join.playmore.pl/dla-klubow-padla/)) and "Przedpłatę
  przy rezerwacji online włączasz sam, a recepcja nadal przyjmuje gotówkę, kartę i przelew"
  ([dla klubów tenisa](https://join.playmore.pl/dla-klubow-tenisa/)).
- **[POLICY] Eversports:** "you can select if you accept online payments or if it is also possible for
  customers to optionally pay cash onsite"
  ([help](https://helpcenter.eversportsmanager.com/start-with-eversports-ballsport-manager-1)).
- **[POLICY] Padel Mates:** "Pay at the club"; "in some cases, cash payments at the venue"
  ([strings](https://padelmates.se/locales/en/translation.json)).
- **[POLICY] kluby.org:** payment "dobrowolne lub wymagane 25%/50%/100%" (carried).

**What a Kraków desk does today.** Garden Padel: "Rezerwacja jest ważna po dokonaniu płatności online
(Przelewy24) lub w recepcji (karta/gotówka)" ([§4](https://gardenpadel.pl/regulamin/)); Squash4You: "Podstawą
do korzystania z kortów jest opłacenie rezerwacji przed wejściem na kort"
([3](https://www.squash4you.pl/regulamin)); Paolo prices online 5 zł lower ("Rezerwuj online — zawsze 5 zł
taniej", [page data](https://playmore.pl/klub/paolo-squash-club/)); Atras 10 % lower (carried).

**What it means for the player app.** *Reading:* Raketa takes every share online; pay-at-the-club for a
direct booking would be the first booking Raketa does not hold money for.

**Market signal.** Table stakes in Poland (every Polish system offers both, club's choice).

### 2.6 Unpaid bookings lapse

**Who has it.**
- **[POLICY] Playmore:** 30 minutes, then "rezerwacja zostanie automatycznie anulowana" (carried); also in its
  booking form for Reservise clubs: "jeśli nie zrobisz tego w ciągu 30 minut, rezerwacja zostanie
  automatycznie anulowana" ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] tenis4U:** "Płatność online jest wymagana. Brak płatności powoduje usunęcie rezerwacji w ciągu 20
  minut" ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)); a desk payment link lapses in 60 minutes and
  the club can "anulować nieopłacone rezerwacje" N hours before the start (carried,
  [integration.md §5](integration.md)).
- **[POLICY] MATCHi:** "an unpaid booking still takes up its slot"
  ([Schedule settings](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005)).
- **[POLICY] Fame Sport (standing slots):** "Nieopłacona rezerwacja może zostać anulowana po upływie terminu
  wskazanego przez Klub" ([III.3](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).

**The desk's day with it.** **[POLICY]** Playmore's pitch: unpaid bookings "znikają z grafiku" and at Vera
Sport fell "z ponad 200" a month ([dla klubów squasha](https://join.playmore.pl/dla-klubow-squasha/)).

**What it means for the player app.** *Reading:* Raketa never has an unpaid player booking (a share is held
or the game is not booked); a lapse rule matters only if pay-later or pay-at-the-club is allowed.

**Market signal.** Table stakes in Poland.

### 2.7 How far ahead a player may book

**Who has it.**
- **[POLICY] Playtomic:** "Book Ahead Limit … how many days in advance a player can make a reservation"
  ([Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297)).
- **[POLICY] MATCHi:** "Days in advance … customers can only see and book slots up to 30 days ahead", overridable
  per customer category, "Whichever value is highest wins"
  ([Schedule settings](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005)).
- **[POLICY] tenis4U:** "Ilość dni w przód możliwych do rezerwacji" (carried).
- **[POLICY] Playmore:** `"max_advance_booking":14` in each club's data ([Atras](https://playmore.pl/klub/atras-squash-club/)).
- **[ABSENT]** CourtReserve's days-ahead setting in the two articles read
  ([Restrictions](https://help.courtreserve.com/en/articles/8071325-booking-settings-restrictions),
  [Membership Type Booking Windows](https://help.courtreserve.com/en/articles/8099478-membership-type-booking-windows));
  a search engine's summary names one, not confirmed here.

**What a Kraków desk does today.** 14 days at Atras, Paolo and Squash4You (Playmore data); Squash4You's
regulamin: "Pojedynczej rezerwacji można dokonywać tylko i wyłącznie na 14 dni w przód"
([5g](https://www.squash4you.pl/regulamin)). **[ABSENT]** a days-ahead figure in the regulaminy of Garden Padel
and Fame Sport; Padel House's and Bajada's could not be found.

**What it means for the player app.** *Reading:* Raketa's 14 days equals the Kraków squash clubs' window;
a club that sells 30 days ahead to the desk would see the deck stop at 14.

**Market signal.** Table stakes.

### 2.8 Per-player limits (active bookings, per day, per week, minutes)

**Who has it.**
- **[POLICY] Playtomic:** "Maximum Bookings/Day" and "Number of Active Bookings"
  ([Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297)).
- **[POLICY] MATCHi:** "Maximum number of upcoming bookings", "… per day", "Booked minutes total", "Booked
  minutes per day", and "Allow same day bookings" exempting today from the totals; "Match spots don't count
  against a player's normal booking limit"
  ([Schedule settings](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005),
  [Venue matches](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333)).
- **[POLICY] tenis4U:** "Limit aktywnych rezerwacji na użytkownika" and a court rule "1 osoba może zarezerwować 1
  godzinę dziennie" (carried).
- **[POLICY] CourtReserve — the only per-week limit found:** "Number of RESERVATIONS a Member is Allowed to
  Reserve per Week", and a separate count for prime time
  ([by count](https://help.courtreserve.com/en/articles/8027083-reservation-rules-by-reservation-count),
  [prime time](https://help.courtreserve.com/en/articles/8099355-reservation-rules-by-prime-time-reservation-count)).
- **[ABSENT]** A per-week limit at Playtomic, MATCHi, tenis4U or Playmore (help and strings above).

**What a Kraków desk does today.** **[ABSENT]** in the four regulaminy read.

**What it means for the player app.** *Reading:* the deck has no per-player cap on yeses (Q97, live-yes cap
removed); a club that sets "2 active bookings" would have to decide whether deck games count, as MATCHi decided
that matches do not.

**Market signal.** Active and per-day limits: table stakes. Per-week and prime-time counts: rare.

### 2.9 Minimum length and length steps

**Who has it.** **[POLICY]** Playtomic: 15-minute multiples (above). MATCHi: "Minimum booking duration",
"Maximum booking duration", "Avoid gaps"
([Schedule settings](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005)). tenis4U: "Minimalny czas
rezerwacji (30 lub 60 minut)" (carried), per-court `allow_half_hour_reservations`
([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)). Playmore: `"reservation_lengths":[60,120]`
([Atras](https://playmore.pl/klub/atras-squash-club/)).

**What a Kraków desk does today.** Garden Padel: "Minimalny czas rezerwacji to 60 minut. Przedłużenie następuje
co 30 minut" ([§4](https://gardenpadel.pl/regulamin/)).

**What it means for the player app.** *Reading:* the deck's game is exactly one hour; a direct booking at
Garden Padel would need 90 minutes.

**Market signal.** Table stakes.

### 2.10 Members book earlier; member-only courts and hours

**Who has it.**
- **[POLICY] Playtomic:** a membership's privileges are "Booking ahead days, Maximum bookings per day, Number
  of active bookings, Cancellation policy (in hours)"
  ([Membership, 2026-09-13](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745)); the
  "private club" workaround sets the general window to 0, which "will disable Open Match creation for everyone"
  ([help, 2026-09-17](https://helpmanager.playtomic.com/hc/en-gb/articles/50979728127889)).
- **[POLICY] MATCHi — three tools.** *Regulations*: "premium members might book 14 days ahead while
  non-members can only book 7 days ahead"
  ([Booking regulations, 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/34085754864157)).
  *Requirement profiles* on a court: "only customers who meet the profile can book that court online"
  ([2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/19511826305565)). *Booking restrictions* on
  chosen slots, expiring before the start (§3.11)
  ([2026-09-08](https://matchi.zendesk.com/hc/en-gb/articles/34085754893469)).
- **[POLICY] tenis4U:** setting templates assigned to named players, "np. VIP, Karta mieszkańca, Seniorzy", each
  with "Ile dni w przód użytkownik może rezerwować", "Minimalny czas rezerwacji", "Ile godzin przed rezerwacją
  można ją anulować", "Maksymalna liczba aktywnych rezerwacji użytkownika"
  ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).
- **[POLICY] CourtReserve:** open and closed booking windows "by membership type", by court type, day and time
  ([Booking Windows, 2026-01-29](https://help.courtreserve.com/en/articles/8078617-booking-settings-booking-windows);
  [Membership Type Booking Windows, 2026-02-27](https://help.courtreserve.com/en/articles/8099478-membership-type-booking-windows)).

**What a Kraków desk does today.** Fame Sport gives standing-slot holders first refusal: "Osoba posiadająca
stałą rezerwację może mieć pierwszeństwo w przedłużeniu dotychczasowego terminu na kolejny okres"
([III.6](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)); members'
prices exist (carried, [gaps-COURTS §7](../games-and-fill-in/topics/gaps-COURTS.md)).

**What it means for the player app.** *Reading:* membership windows collide with open play at Playtomic, which
refuses them for open matches "because the match needs to be available for all players to join"
([player help, 2026-09-30](https://playerhelp.playtomic.com/hc/en-gb/articles/47312414385169)); a Raketa group's
game is private to the group, so that reason does not carry over.

**Market signal.** Table stakes in club software; MATCHi's expiring slot restriction is rare.

### 2.11 Courts or hours not sold online

**Who has it.** Playtomic "Bookable Online" per court; MATCHi "Offline only" and member-only courts; tenis4U
per-court online switch and blocked hour ranges (all carried). New: **[POLICY]** Playmore tells players "Ta
lokalizacja nie przyjmuje jeszcze rezerwacji przez internet … Kort zarezerwujesz w recepcji klubu"
([strings](https://playmore.pl/assets/93jAIRDY.js)); CourtReserve's closed windows (above); kluby.org's
"Blokada rezerwacji nocą" (2016, [changelog](https://oferta.kluby.org/changelog?rok=2016)).

**What a Kraków desk does today.** Garden Padel's standing slots are agreed "indywidualnie z administratorem"
([§4](https://gardenpadel.pl/regulamin/)); Fame Sport "może przeznaczyć określone korty lub godziny" for its
own classes and events ([I.11](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).

**What it means for the player app.** *Reading:* "Only Raketa" is the inverse switch: hours sold only through
the deck. One calendar needs both, per court and per hour.

**Market signal.** Table stakes.

### 2.12 Phone-number verification

**Who has it.**
- **[POLICY] Playmore:** "Zweryfikuj numer telefonu — Aby korzystać z aplikacji, podaj i zweryfikuj swój numer
  telefonu" ([strings](https://playmore.pl/assets/CG9yQPLY.js)).
- **[POLICY] tenis4U:** "Kod SMS jest wymagany do aktywowania konta" ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] kluby.org:** the phone number "stanowi unikalny identyfikator w systemie"; some services need "kodu
  SMS" ([regulamin §V.11](https://kluby.org/regulamin)); since 2017 the desk must enter one: "Wymagany numer
  telefonu podczas dodawania rezerwacji przez obsługę klubu" ([changelog](https://oferta.kluby.org/changelog?rok=2017)).
- **[POLICY] Playtomic:** a verified phone gates social features — "inviting or adding players to a match",
  chat, groups — not a solo booking; "Each phone number can only be linked to one account"
  ([help, 2026-09-29](https://playerhelp.playtomic.com/hc/en-gb/articles/51110112972561)).

**The desk's day with it.** *Reading:* the phone is how a Polish desk finds a player; a verified one lets a
phone booking and an app account be the same person.

**What it means for the player app.** *Reading:* Raketa signs up by email today; every Polish rival keys the
player on a verified phone.

**Market signal.** Table stakes in Poland.

### 2.13 Blocking debtors and repeat no-shows

**Who has it.**
- **[POLICY] Playmore:** "Masz w tym klubie nieopłacone rezerwacje. Ureguluj je w „Moje rezerwacje”" and
  "Twoje rezerwacje w tym klubie są zablokowane — skontaktuj się z klubem, żeby to wyjaśnić" — per club
  ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] tenis4U:** the desk warns a player ("Czy na pewno chcesz dać ostrzeżenie?"); at the limit "Ostrzeżono.
  Użytkownik został zbanowany ({total_warns} ostrzeżeń)" ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js));
  the player sees "Masz {n} ostrzeżeń", and at three "Konto zablokowane, ureguluj zaległości"
  ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[POLICY] kluby.org:** a club sees "informacja o ilości blokad na Usługi Klubów" with each booking; blocks from
  "co najmniej 2 Klubów" can lock the account ([regulamin §IV.5, Zablokowanie konta 2g](https://kluby.org/regulamin)).
- **[POLICY] Playtomic:** a debt blocks new bookings (above); the club itself cannot ban a player (carried).

**What a Kraków desk does today.** Fame Sport: "Prawo do dokonywania kolejnych rezerwacji może zostać
ograniczone wobec osób posiadających wymagalne zaległości wobec Klubu do czasu ich uregulowania"
([II.7](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)); Atras's desk
tells a no-show of the debt "w danym dniu lub następnym" ([regulamin](https://www.atrassquash.pl/regulamin/));
Squash4You's late fee is paid "w terminie do 7 dni, przelewem" ([5e](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** *Reading:* a deck player never owes a club (the share is held); a
direct pay-later booking creates the debt these blocks exist for.

**Market signal.** Table stakes in Poland.

### 2.14 A link from the club's own website

**Who has it.** tenis4U (Garden Padel → `app.tenis4u.pl/#/court/483`), PADO, Playmore's external listings
(carried, [integration.md §5](integration.md)). Playmore shows tenis4U clubs as "Rezerwacja realizowana przez
recepcję klubu", "Otwórz formularz online", "Pokaż numer telefonu" ([strings](https://playmore.pl/assets/CG9yQPLY.js)).

**What a Kraków desk does today.** Garden Padel's and Fame Sport's "Rezerwacje" buttons link to tenis4U (carried).

**What it means for the player app.** *Reading:* the link opens a web page, so a link-only path still needs
Raketa to book on the web, not only in the app.

**Market signal.** Table stakes.

### 2.15 An embedded widget or club-branded booking page

**Who has it.**
- **[POLICY] Playtomic:** an iframe whose `src` "must follow the white-label format: https://playtomic.io/wl/{tenant_id}",
  allowed only on the website set in the club's profile, matching "protocol … and domain"
  ([Embed, 2026-09-30](https://helpmanager.playtomic.com/hc/en-gb/articles/29889024973841)).
- **[POLICY] MATCHi:** a "booking widget" sharing the app's checkout; its general terms "regulate the API as
  well as our Widget" ([New Checkout](https://matchi.zendesk.com/hc/en-gb/articles/14135337263005),
  [terms update, 2026-05-18](https://matchi.zendesk.com/hc/en-gb/articles/36167433642269)).
- **[POLICY] Eversports:** "Settings > Court Booking Widget", link `https://www.eversports.com/widget/w/…`,
  as a button or `<iframe>`; a newer script widget "removing the iframe"
  ([what is a widget](https://helpcenter.eversportsmanager.com/what-is-a-widget),
  [new widgets](https://helpcenter.eversportsmanager.com/how-to-integrate-the-new-widgets)).
- **[POLICY] Playmore:** "Własna strona rezerwacji z logo i kolorami Twojego klubu"
  ([dla klubów padla](https://join.playmore.pl/dla-klubow-padla/)); Miazga embeds `reservise.com/online/…`
  (carried).
- **[POLICY] Padel Mates:** "Widget Creator Panel", "Create Widget" ([strings](https://padelmates.se/locales/en/translation.json)).
- **[ABSENT]** A widget or embed at tenis4U (carried) or kluby.org ([oferta](https://oferta.kluby.org),
  [integracje](https://oferta.kluby.org/integracje), changelog 2014–2026: only TV "wtyczki").

**What a Kraków desk does today.** Links out; no embedded widget was found (carried).

**What it means for the player app.** *Reading:* the people a club reaches through its website are the
ones not in the app; a widget is how most rivals sell to them.

**Market signal.** Table stakes for club software outside Poland; absent at Kraków's own systems.

### 2.16 Booking without an account

**Who has it.**
- **[POLICY] Playmore — phone and SMS, no password:** "Twój numer nie jest jeszcze w systemie Reservise. Podaj
  dane i kod SMS, aby dokończyć rezerwację"; "Tego numeru nie ma na liście klientów tego klubu … poproś
  recepcję o dopisanie numeru"; and for open games "Dołącz w minutę … Wyślemy kod SMS. Konto założy się samo",
  "Bez hasła i logowania — numer telefonu i kod SMS" ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] Playtomic:** only the club adds a "Guest user" (carried); "Split Payment is not available for guest
  bookings" ([Manager strings](https://manager.playtomic.io/locales/en/matches.json)).
- **[ABSENT]** A guest checkout without an account in Playtomic's embed article, MATCHi's player help
  (searched "without an account", "widget"), Eversports' widget pages, tenis4U ("Zaloguj się, aby dołączyć") or
  kluby.org (booking requires a Konto, [regulamin §V](https://kluby.org/regulamin)).

**What it means for the player app.** *Reading:* the nearest thing to guest checkout in Poland is a phone
number plus a code, which is also an account.

**Market signal.** Rare.

### 2.17 Reserve with Google and the Google profile's booking link

**Who has it.**
- **[DOCS] Reserve with Google partners:** 441 names on Google's list, mostly restaurants, salons and fitness
  (Booksy, MINDBODY, Fresha, Treatwell, Square Appointments, SimplyBook.me, Wix; in Poland mojstolik and
  Zjedz.my) ([partners](https://www.google.com/maps/reserve/partners)). Partners need "a direct contractual
  relationship with all the merchants" (carried, [integration.md §3](integration.md)).
- **[ABSENT]** Playtomic, MATCHi, Eversports, CourtReserve, ClubSpark, Padel Mates, Playmore, tenis4U or
  kluby.org on that list ([partners](https://www.google.com/maps/reserve/partners), read 2026-10-12).
- **[POLICY] Any business can add booking links:** "You can also add up to 10 links per category. Links can help
  customers: Book an appointment. Make a reservation"
  ([Business Profile help](https://support.google.com/business/answer/6218037)).

**What a Kraków desk does today.** **[ABSENT]** Which Kraków clubs set a booking link on Google (not visible
without Maps scraping).

**What it means for the player app.** *Reading:* a "Book" button on Google is a plain link a club adds
itself; becoming a Reserve with Google partner would put Raketa ahead of every court platform read.

**Market signal.** Booking link: table stakes and free. Reserve with Google: absent among court platforms.

### 2.18 Facebook "Book now"

**Who has it.** **[DOCS]** A booking vendor's help: "As of 8 June 2022, the Facebook Bookings integration feature
has been discontinued", and it advises a "Contact Us", "Learn More" or "Sign Up" button carrying the booking URL
([Cliniko, 2023-10-05](https://help.cliniko.com/en/articles/1023972-add-online-bookings-to-your-facebook-page)).
**[ABSENT]** A Meta help page confirming this (Meta's help pages were not readable), or any court platform
offering a Facebook booking integration.

**Market signal.** Absent.

---

## Area 3 — The Games deck inside one calendar

### 3.1 How an open game holds its court

**What it covers.** When a game players make for each other takes a court out of the calendar.

**Who has it.**
- **[POLICY] Playtomic — in stages:** "0 or 1 player: The court is never booked. 2 players … more than 12
  hours … 3 players … more than 4 hours … 4 players: The court is booked immediately"; below that "the match
  will no longer occupy a slot in the club's calendar … courts remain available for … Potential private
  bookings" ([Occupy calendar slots, 2026-10-01](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929)).
  Open matches are made "at all available times in your club schedule"
  ([Configure, 2026-09-29](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473)).
- **[POLICY] Padel Mates — the same stages, word for word:** "If you are the only player in the match, no
  booking will be created … A booking will automatically be created if there are more than 12 hours remaining
  … more than 4 hours remaining" ([strings](https://padelmates.se/locales/en/translation.json)).
- **[POLICY] Playmore — at once:** the organiser picks a free court and pays; the court is held from publishing
  (carried, [platforms §2](../games-and-fill-in/topics/platforms.md)).
- **[POLICY] MATCHi — at once:** "A match is a court booking with multiple player spots"
  ([Venue matches](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333)); a public match is "a
  confirmed court booking" made public (carried).
- **[POLICY] tenis4U — a booking made public:** "Otwarte sparingi" are loaded with `getPublicReservations`, each
  a shared booking with `open_slots` and a price per person or "Darmowe" if the organiser pays
  ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)); the organiser can add "Opis sparingu"
  ([chunk](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3_module_ts.b8c3629f5a4e1beb.js)).
- **[POLICY] kluby.org "Sparingi":** game proposals in a partner base, no court (carried).

**The desk's day with it.** Playtomic's held court shows as "Pending booking" on the schedule, and the court-less
matches only in the Matches list (carried, [gaps-COURTS §4](../games-and-fill-in/topics/gaps-COURTS.md)).
tenis4U's desk sees and toggles it on the booking: "Publiczny sparing włączony / wyłączony"
([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)); MATCHi marks it with a player icon (carried).

**What a Kraków desk does today.** **[ABSENT]** Whether any Kraków tenis4U club's players use "Otwarte
sparingi", or any Kraków Playmore club has *Gry otwarte* on (Playmore's open-games pages render only in the
browser; club page data carries no flag).

**What it means for the player app.** *Reading:* Raketa sits with Playmore and MATCHi — nothing is booked until
the last yes, and then the court is booked at once — but nothing is held before that, so in one calendar
the deck's proposals are like Playtomic's one-player matches: visible to players, invisible to the desk.

**Market signal.** Open games in the club's own calendar: table stakes for the big platforms; staged holding:
Playtomic and its copier only.

### 3.2 Switching open play on: per sport, court or hour

**Who has it.**
- **[POLICY] Playtomic:** "Activate the toggle for Padel or Tennis", "Only Double" or "Single & Double", level
  offsets for club-launched matches ([Configure](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473));
  the settings form also has a field labelled "Courts" (key `skip_individual_resources`)
  ([Manager strings](https://manager.playtomic.io/locales/en/matches.json)).
  - *Reading:* the key suggests a club can leave some courts out of open matches; no help article says so.
- **[POLICY] Playmore:** "Gry otwarte są w tym klubie wyłączone"; "W tym klubie gry otwarte zakładasz tylko
  {days} {from}–{to}" or "tylko poza godzinami szczytu" ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] MATCHi:** venue matches are created by the venue; public matches cannot be switched off: "venue
  admins have no control to toggle visibility" (carried).
- **[ABSENT]** A per-hour switch at Playtomic, MATCHi or tenis4U (help and strings above; tenis4U's panel shows
  only the per-booking public toggle and the shared-booking auto-cancel).

**What it means for the player app.** *Reading:* Raketa's "Only Raketa" block is a per-hour switch already;
Playmore is the only rival that lets the club say which hours open play may use.

**Market signal.** Per sport: table stakes. Per hour: rare (Playmore).

### 3.3 Caps on open play, and an off-peak discount

**Who has it.** **[POLICY] Playmore only:** "Limit gier: maks. {max} aktywne gry naraz. Gry startujące w dni robocze
{from}–{to} mają osobny limit {offPeakMax} i nie liczą się do podstawowego limitu" — a separate cap for off-peak
games; "Masz już {max} aktywne gry w godzinach szczytu w tym klubie"; and "Poza szczytem wpisowe {percent}%
taniej, różnicę pokrywa klub" — off-peak entry cheaper, the club covers the difference
([strings](https://playmore.pl/assets/93jAIRDY.js)).
**[ABSENT]** A maximum share of courts or hours for open play, anywhere (Playtomic, MATCHi, Playmore, tenis4U,
Padel Mates sources above).

**What a Kraków desk does today.** Playmore's pitch is "gry otwarte na martwe godziny"
([dla klubów padla](https://join.playmore.pl/dla-klubow-padla/)).

**What it means for the player app.** *Reading:* a per-player cap on deck games (removed in Q97) is the one
cap rivals use; a club-funded off-peak price is a lever Raketa's club side has no equivalent for.

**Market signal.** Rare.

### 3.4 How far ahead, and how close to the start, a game may be made

**Who has it.**
- **[POLICY] Playtomic:** "the standard booking window applies (the same for everyone)"; "early booking
  privileges do not apply to open matches"
  ([Configure](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473)).
- **[POLICY] Playmore:** "Ten termin jest zbyt odległy"; "Wybrany termin jest zbyt blisko startu - gra nie
  zdążyłaby się skompletować"; it shows dates from 3 days out first: "gry zakładane 3+ dni wcześniej zbierają
  komplet mniej więcej 3 razy częściej"; under 24 h: "Mało czasu"
  ([strings](https://playmore.pl/assets/93jAIRDY.js)).

**What it means for the player app.** *Reading:* Raketa deals 14 days ahead and has a cut-off; Playmore's
"too close to start" is the same idea applied at creation.

**Market signal.** Window: table stakes. Minimum lead at creation: rare (Playmore).

### 3.5 How many players hold a court

**Who has it.** Playtomic and Padel Mates: 2 players with >12 h, 3 with >4 h, 4 at once; in 20 countries (not
Poland) one player holds it "until 48 hours before" (§3.1, carried). Playmore, MATCHi, tenis4U: one paying
organiser holds it (§3.1).

**What it means for the player app.** *Reading:* Raketa holds nothing until four (or two) say yes; it is the
strictest of all, and the only one where no player money is at risk before the game is full.

**Market signal.** Differentiator either way; no common rule.

### 3.6 The cancel deadline for a game that doesn't fill

**Who has it.**
- **[POLICY] Playmore:** the club sets "ile godzin przed startem gra się anuluje (1–48 h)" and free cancel
  "0–72 h" (carried); the player sees "auto-cancel {hours} h 10 min przed startem" (carried).
- **[POLICY] MATCHi venue matches:** "Automatically cancelled (hours before start)" and a separate
  "Cancellation rule"; "Match Settings only affect new matches"
  ([Venue matches](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333)).
- **[POLICY] Playtomic:** fixed, about 1 h before, not club-set (carried).
- **[POLICY] tenis4U:** "Auto-anulowanie rezerwacji współdzielonych przed terminem"
  ([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)); its unit is not shown.

**What it means for the player app.** *Reading:* Raketa's club cut-off is the same lever as Playmore's.

**Market signal.** Table stakes where clubs run open play.

### 3.7 May an open game take the last free court?

**Who has it.** **[POLICY]** Playtomic: a match is cancelled when "No court is left available for that time slot.
This can happen if another open match fills up first and books the court, or if someone makes a private
reservation" ([Cancel an Open Match, 2026-10-08](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601)).
Playmore: the organiser may pick any free court the club opens to open play (above).
**[ABSENT]** A rule anywhere that keeps the last court (or a number of courts) for private bookings.

**What it means for the player app.** *Reading:* no rival protects the last court; the club's only tool is
fencing hours (Playmore) or courts (Playtomic's unexplained field).

**Market signal.** Absent.

### 3.8 Races: a direct booking and an open game want the same hour

**Who has it.**
- **[POLICY] Playtomic — the private booking wins:** "private reservations always take priority over open
  matches that aren't full or don't have a court assigned yet"; the loser is cancelled with "a full automatic
  refund (including the Playtomic service fee)", signed "Cancelled by Anemone"
  ([Cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601)).
  **[COMPLAINT]** open matches at peak are "guaranteed to get cancelled by someone booking a private match";
  "an initial booking can be taken by later bookings with four players" (carried,
  [competitor-organiser §8](../games-and-fill-in/topics/competitor-organiser.md)).
- **[POLICY] Playmore, MATCHi, tenis4U — first come:** the game already holds the court, so the other side meets a
  taken hour: Playmore "Ktoś właśnie zajął ten termin. Wybierz inny slot" (organiser) and "Ups! Ktoś cię już
  uprzedził z rezerwacją, wybierz inną godzinę" (booker) ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[POLICY] Playmore steers players to one game per hour:** "O tej porze na graczy czeka już {count} gra —
  dołącz … Jedna pełna gra jest lepsza niż dwie w połowie puste" ([strings](https://playmore.pl/assets/93jAIRDY.js)).
- **[ABSENT]** A warning to a Playtomic desk booking over a gathering match (carried).

**What it means for the player app.** *Reading:* at Raketa the race is between a proposal and anyone else
until the last yes, and the yes can fail at the last moment; Playtomic tells the loser by cancelling with a
full refund, Playmore by refusing the slot before payment.

**Market signal.** Table stakes to resolve it somehow; which side wins differs.

### 3.9 Late court assignment

**Who has it.**
- **[POLICY] Playtomic:** "courts are assigned using the 'Autoselect' option"; "the system automatically assigns
  courts as the match time approaches"; a ticket reads "Pending to assign"; "The system will only assign a court
  that matches the specific properties of the original request"; "the price per player may vary"
  ([Manually book, 2026-09-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20535050634769),
  [Manage, 2026-09-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353),
  [Configure](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473),
  [strings](https://manager.playtomic.io/locales/en/matches.json)). A court added by the club "won't be
  automatically cancelled if not enough players register".
- **[POLICY] Fame Sport (a Kraków regulamin):** "Zmiana numeru kortu w ramach obiektu na kort o porównywalnych
  warunkach do gry nie stanowi odwołania rezerwacji" — moving a booking to a comparable court is not a
  cancellation ([II.20](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[ABSENT]** Late assignment at MATCHi, Playmore or tenis4U (each game is a booking on a named court).

**The desk's day with it.** *Reading:* the desk keeps every court sellable until the game is full, and drags
the match to another court at will (Playtomic: "drag the match to a different court").

**What it means for the player app.** *Reading:* a deck card could promise "a court at Fame Sport, 19:00" and
name the court only when the game is booked.

**Market signal.** Rare (Playtomic only).

### 3.10 Making a private booking public

**Who has it.** MATCHi public matches (app only: "Public matches are only available in the MATCHi mobile app,
not on the web", [Q&A](https://matchi.zendesk.com/hc/en-gb/articles/21816310080797)); Playtomic "Convert to
Public Match", which traps the owner with the empty seats (carried); tenis4U's per-booking "Publiczny sparing"
toggle, usable by the organiser and by the desk
([panel](https://panel.tenis4u.pl/main.333e76605ded56e6.js)).

**What it means for the player app.** *Reading:* the reverse of the deck: a booked court looking for players.
Raketa's Fill in (a freed seat offered on) is the nearest thing.

**Market signal.** Table stakes among platforms with open play.

### 3.11 Analogues of the release lead (new ones only)

Hotel allotments, ClassPass SmartSpot, Urban Sports Club's aggregator cap and Anybuddy's chosen slots are in
[integration.md §1, §3](integration.md).

- **[POLICY] MATCHi booking restrictions — the closest analogue found.** "Booking restrictions let you reserve
  specific time slots for customers who match a requirement profile. Until the restriction expires, only
  qualifying customers can book those slots — after expiry, the slots open up to everyone"; the expiry is
  "relative to the slot's start — for example, '72 hours before the slot starts'"; it can repeat by weekday over
  a date range; "A restriction is automatically removed once a qualifying booking is made"; "Venue admins are
  never blocked"; "A restriction can never revert to 'restricted' once it's expired"
  ([Booking restrictions, 2026-09-08](https://matchi.zendesk.com/hc/en-gb/articles/34085754893469)).
  - *Reading:* the same shape as Only Raketa + release lead, with a customer group in place of a channel, and
    the desk still able to book inside it.
- **[POLICY] Playtomic's one-player hold** releases a match's court "until 48 hours before" in 20 countries
  (carried) — a release lead attached to one game rather than a block.
- **[POLICY] Resy (restaurants):** each table is online, in-house or "walk-in only"; "Tables set to online will
  automatically sync with your set pacing … so that guests cannot book over your set pacing limit"
  ([Resy helpdesk](https://helpdesk.resy.com/en_us/how-to-setup-flexible-seating-to-maximize-covers-BkL3bvQLO.md)).
- **[POLICY] CourtReserve:** open and closed windows per membership type, court type, day and time (§2.10).
- **[POLICY] tenis4U:** setting templates per named player group (§2.10).
- **[POLICY] Playmore:** open play allowed only in hours the club names, with a club-paid discount (§3.2–3.3).

**Market signal.** An expiring hold on chosen hours for one channel or group: rare (MATCHi).

---

## Kraków clubs, side by side

| Club | System | Doors | Days ahead | Free cancel | Payment | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Garden Padel | tenis4U | website/app, phone, desk | not stated | 24 h | valid once paid online or at the desk; 60 min min., then 30-min steps | [regulamin](https://gardenpadel.pl/regulamin/) |
| Fame Sport | tenis4U | phone, desk, booking system | not stated | 24 h; standing slots 48 h; inside 24 h binding | per booking; debts can stop new bookings | [regulamin 2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) |
| Atras | Playmore | desk, website, app | 14 | 24 h app, 23 h phone/desk | online 10 % cheaper (carried) | [regulamin](https://www.atrassquash.pl/regulamin/), [data](https://playmore.pl/klub/atras-squash-club/) |
| Paolo | Playmore | — | 14 | 24 h | online 5 zł cheaper | [data](https://playmore.pl/klub/paolo-squash-club/) |
| Squash4You | Playmore | online, app, phone, desk | 14 | 24 h; later only if resold | paid before play; refund kept as credit | [regulamin](https://www.squash4you.pl/regulamin), [data](https://playmore.pl/klub/squash4you/) |

Padel House's and Bajada's regulaminy were not found.

## Rivals × features

`yes` documented · `no` documented absent or refused · `—` not found in what was read.

| Feature | Playtomic | MATCHi | Eversports | Playmore | tenis4U | kluby.org | Padel Mates | CourtReserve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Direct booking of a whole court | yes | yes | yes | yes | yes | yes | yes | yes |
| Split payment | yes (not on web) | yes | — | organiser pays, then asks | yes | yes | yes | — |
| Pay at the club | some regions | desk marks cash | club's choice | yes | per court | yes | yes | — |
| Prepay required, club's choice | no setting | — | yes | yes | per court | 25/50/100 % | — | — |
| Unpaid booking lapses | — | no (holds slot) | — | 30 min | 20 min | — | — | — |
| Days-ahead window | yes | yes | — | yes | yes | — | — | — |
| Active / per-day limits | yes | yes | — | — | active | — | per club | yes |
| Per-week limit | no | no | — | no | no | — | — | yes |
| Members book earlier | yes | yes | — | — | templates | — | — | yes |
| Expiring hold on chosen hours | 1 player, 48 h (20 countries) | yes | — | no | no | no | — | — |
| Phone verified | for social | — | — | yes | yes | yes | — | — |
| Block debtors | debt blocks | — | — | per club | 3 warnings | yes, shared | — | — |
| Widget or branded page | iframe | widget | widget | branded page | link only | link only | widget | — |
| Book without an account | club adds guest | — | — | phone + SMS | no | no | — | — |
| Reserve with Google partner | no | no | no | no | no | no | no | no |
| Open games in the club calendar | yes | yes | — | yes | yes (public booking) | partner search only | yes | — |
| Court held | in stages | at once | — | at once | at once | — | in stages | — |
| Club limits open play by hour | — ("Courts" field) | no | — | yes | no | — | — | — |
| Cap on open games | — | — | — | per player, peak/off-peak | — | — | — | — |
| Club-set auto-cancel | no (≈1 h) | yes | — | 1–48 h | yes | — | — | — |
| Private booking beats a gathering game | yes | no | — | no | no | — | — (copies the hold rules) | — |
| Late court assignment | yes | no | — | no | no | — | — | — |

## Gaps

- **What a Kraków desk thinks of open play next to its own bookings** — no Kraków club's view was found;
  whether any Kraków club has Playmore *Gry otwarte* or tenis4U *Otwarte sparingi* switched on (Ask a real club).
- **Padel House's and Bajada's regulaminy**, and the days-ahead window at the tenis4U padel clubs (their court
  pages need tenis4U's API, which was not called).
- **Playtomic's "Courts" field** (`skip_individual_resources`) in the open-match settings: what it does.
- **Guest checkout** in Playtomic's embed, MATCHi's widget and Eversports' widget: whether any books without an
  account.
- **tenis4U's "Auto-anulowanie rezerwacji współdzielonych przed terminem"**: its unit, default and what the
  players are told.
- **Whether Playmore's organiser-pays-first split** returns the organiser's money if the club cancels.
- **Facebook**: no Meta primary source on the "Book now" button; Google: which Kraków clubs set a booking link.
- **Eversports' and Padel Mates' open-match club controls** were not read.
