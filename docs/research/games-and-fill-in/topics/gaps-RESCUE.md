# Gaps — RESCUE (seats to fill, taking a seat)

Answers to the RESCUE area's missing facts (`areas/RESCUE/gaps.md` in the story work dir), read
2026-10-08. One `##` section per gap, named by its rule. Every fact sits under a `###` heading.

**A new source in this file: Playmore's own web-app code.** Playmore's player app is one web app
(its native apps load it remotely: "Apka natywna ładuje web zdalnie (server.url)", see
[p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js)). Its script files on `playmore.pl/assets/`
carry every Polish string the player sees, the screen logic, and a **feature-flag register in which
Playmore's team writes down, in Polish, why each flag exists and what its numbers say**. Facts read
from it are tagged `[POLICY]` like the earlier strings reads, and say *(code)* when they come from
screen logic rather than words. File names are content hashes: they change on Playmore's next
release, so each fact quotes enough text to find it again.

## R-RESCUE-5 — can a player who left take the same seat back?

### Playmore refuses nobody for having left an open game
- **[ABSENT]** Playmore's open-game join has no refusal for a player who left the same game: its
  waitlist errors are "Ta gra nie jest już dostępna", "Jesteś już w tej grze", "Nie możesz zapisać
  się na grę w tym klubie" ([93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js)), and its open-game
  error codes (`OPEN_GAME_SLOT_TAKEN`, `OPEN_GAME_NOT_PARTICIPANT`, …) hold none about a leaver
  ([DGQrxHKX.js](https://playmore.pl/assets/DGQrxHKX.js)). The only "you left, wait before rejoining"
  rule anywhere in the app is the league's: "ponownie dołączysz dopiero za {duration}" (leaving a
  league ladder). Searched: "ponownie", "Wypisałeś", "nie możesz dołączyć", "już się wypisa". — read 2026-10-08
- *Reading:* at Playmore a leaver whose seat is still open can join again like anyone else, paying again.

### Playtomic's help still does not say
- **[ABSENT]** Playtomic's player help search returns nothing for "rejoin"; "join again" returns 50
  articles, none about rejoining a match left. Its sign-up FAQ covers only paying, partners, level
  requests and accounts. [Help search API, "rejoin"](https://playerhelp.playtomic.com/api/v2/help_center/articles/search.json?query=rejoin&locale=en-gb), [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match-Padel-Tennis) (updated 2026-10-03) — read 2026-10-08
- **[ABSENT]** 1 636 App Store reviews (GB, US, ES, PL, SE, NL, IT, DE, FR, 10 pages each) hold no
  complaint about being unable to rejoin, or about someone rejoining. [App Store feed, GB](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

### A Kraków club forgives a late canceller only through another player
- **[POLICY]** Atras: a late cancellation is charged "chyba że kort zostanie wynajęty przez innego
  klienta"; a no-show is charged "chyba że w zastępstwie wskaże inną osobę, która wynajmie kort".
  Miazga: forgiven "jeżeli kort zostanie zarezerwowany i opłacony przez innego gracza". Squash4You: a
  late cancellation is "warunkowa" — the hour shows as free "w grafiku on-line dla wszystkich
  Klientów" and the desk "będzie starał się w pierwszej kolejności sprzedać" it. [Atras regulamin](https://www.atrassquash.pl/regulamin/), [Miazga regulamin §4–5](https://www.miazgasquash.pl/regulamin/), [Squash4You regulamin](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[ABSENT]** None of the three says whether the canceller may book the same hour back; every
  waiver names "another" client or player. — read 2026-10-08

## R-RESCUE-8 — how open-game lists refresh

### Playmore reads its open-games list when the page opens and after the player's own actions
- **[POLICY]** *(code)* The club's open-games page loads its list once when it opens ("Open games page
  initialization failed" guards that first read, together with the player's own games) and hands the
  same loader to the cancel, leave and join helpers as `reload`; the loader itself has no timer
  ("Failed to fetch open games:"). [DGQrxHKX.js](https://playmore.pl/assets/DGQrxHKX.js), [BfBfjPsN.js](https://playmore.pl/assets/BfBfjPsN.js) — read 2026-10-08
- **[POLICY]** *(code)* The strip "Komplet do {time} · Zostało {h} godz. {m} min" ticks every 30
  seconds (`setInterval(…, 3e4)`) on the clock alone: it recounts the time left, it does not re-read
  the games. [DGQrxHKX.js](https://playmore.pl/assets/DGQrxHKX.js) (`OpenGameStatusStrip`) — read 2026-10-08

### Playmore's pull to refresh
- **[POLICY]** Flag `native-pull-refresh` (added 25 Sep 2026): a native iOS "pociągnij, żeby
  odświeżyć" replaces the JavaScript gesture, which "wisi na 10 ekranach"; "Kontrolka wisi tylko nad
  ekranami z odświeżaniem". Android and old builds keep the JavaScript gesture. [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08
- *Reading:* which ten screens is not listed; the open-games page is not named.

### Playmore tells a player who lost a race to refresh
- **[POLICY]** In its league "Kort po połowie" (a 1-v-1 seat paid half each, a pilot not before
  10 Nov 2026), a player who opens a seat someone is paying for sees "Ktoś właśnie dołącza — Jeśli
  nie zapłaci do {time}, miejsce wróci. Sprawdź za chwilę." with a button "Odśwież"; the author sees
  "Ktoś właśnie opłaca drugie miejsce." [CPLsdYdo.js](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08

### Playtomic's refresh is not documented
- **[ABSENT]** No Playtomic help article describes how *Find a match* or a match page updates (help
  search "refresh": one article, about the Club Wallet). The only review touching it says players
  "have to keep checking if something has come up" (Kevin the Labradorable, GB, 2026-08-14). [Help search API, "refresh"](https://playerhelp.playtomic.com/api/v2/help_center/articles/search.json?query=refresh&locale=en-gb), [App Store GB feed](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortBy=mostRecent/json) — read 2026-10-08

## R-RESCUE-19 — can the pay button be pressed again while a payment is on its way?

### Playmore hides "pay" while a payment is processing and says "do not pay again"
- **[POLICY]** A booking's details have a *processing* state whose notice reads "Przetwarzamy Twoją
  płatność — Płatność przyjęta — status zaktualizuje się sam. Nie płać ponownie."; *(code)* the pay
  button shows only in the unpaid, overdue and pay-window states, never in *processing* or *initial
  check* ("Sprawdzamy status płatności… Proszę czekać"). [CG9yQPLY.js](https://playmore.pl/assets/CG9yQPLY.js), [D-b_RkfX.js](https://playmore.pl/assets/D-b_RkfX.js) — read 2026-10-08
- **[POLICY]** *(code)* On the payment page the main button is disabled while the order is being
  submitted (`disabled: !canPurchase || isSubmitting`) and reads "Trwa opłacanie..." during a wallet
  payment. [BNVUkjYD.js](https://playmore.pl/assets/BNVUkjYD.js), [CG9yQPLY.js](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[POLICY]** Apple Pay or Google Pay not yet confirmed: "może to potrwać do 15 minut. Nie płać
  ponownie: odśwież tę stronę za kilka minut, a status wpisowego sam się zaktualizuje" (league entry
  fee). The league seat: "Płatność jest już w toku — poczekaj na jej wynik." An open-game seat already
  paid, reached again from a reminder: "Twoje miejsce w tej grze jest już opłacone." [CPLsdYdo.js](https://playmore.pl/assets/CPLsdYdo.js), [93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore's own team guards against duplicates after the bank
- **[POLICY]** Flag notes: rematch invites go out "dopiero po opłaceniu gry … bez duplikatów po
  powrocie z banku"; court bookings that fail after payment are recovered ("court_reservation_replay_recovered").
  [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08
- **[COMPLAINT]** Carried: a Playmore payment that hung cost "100 zł za duplikat rezerwacji"
  (Google Play, 2025-09-01) ([complaints](complaints.md#charged-twice-or-charged-when-the-booking-failed)).

### Playtomic: no rule found; players report double charges
- **[ABSENT]** No Playtomic help article covers pressing pay twice or a payment in progress (help
  search "pay twice", "charged twice", "duplicate": no such article). [Help search API, "charged twice"](https://playerhelp.playtomic.com/api/v2/help_center/articles/search.json?query=charged%20twice&locale=en-gb) — read 2026-10-08
- **[COMPLAINT]** "Te cobran dos veces por una sola reserva que hiciste y no te reembolsan" (Dados
  triples, ES, 2026-05-25); "It took the money but then said there was an issue and didn't book me
  on. I booked on again and it worked but it took the money twice" (Tonyhean, GB, 2026-08-12). [App Store ES feed](https://itunes.apple.com/es/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json), [App Store GB feed](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

## R-RESCUE-24 and R-RESCUE-26 — a seat while a join payment is pending, and where it shows

### Playmore holds a league seat 10 minutes for whoever pays first
- **[POLICY]** League "Kort po połowie": "Gram · zapłać {amount}" — "Gra ten, kto pierwszy opłaci
  miejsce. Na płatność masz 10 minut."; while paying: "Dokończ płatność — Trzymamy dla Ciebie miejsce
  do {time}", with "Rezygnuję z miejsca"; others see "Ktoś właśnie dołącza"; afterwards "Ten mecz ma
  już komplet — Ktoś był szybszy." The author's own unpaid half: "Nieopłacony kort po godzinie wraca
  do klubu." [CPLsdYdo.js](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** That feature is off: flag `league-open-match` "na 0%", pilot at one club "nie
  wcześniej niż 10.11". [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08

### Playmore's open games: no held seat for a pending join was found
- **[ABSENT]** For *Gry otwarte* no string or state holds a seat for a joiner whose payment is still
  pending: the preview's "Dołącz za {price}" leads to the shared checkout, and the joiner is told
  "Jesteś w grze!" after it ([93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js)); the only
  join-side parking is a client-side note of the intent (`pendingClassEnrollment`, 30 min, 120 min
  for link joins) that resumes the sign-up, not a seat ([p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js), flag `open-game-link-fast-lane`). Searched: "Trzymamy", "Miejsce czeka", "Oczekuje na płatność", "Opłać do". — read 2026-10-08

### Playmore's pay-by countdown belongs to a booking awaiting payment
- **[POLICY]** A booking awaiting payment shows, on its details, "Opłać do {time} — Rezerwacja czeka
  na płatność online — nieopłacona do {time} zostanie automatycznie anulowana. [Zapłać teraz]", and
  a countdown "Masz jeszcze {time} na opłacenie rezerwacji"; *Moje rezerwacje* has a filter "Tylko
  nieopłacone", a status "Płatność w toku", and a tab badge "nieopłacone rezerwacje: {count}". [CG9yQPLY.js](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[ABSENT]** Whether a pending open-game join appears as such a booking (it is booked as a class
  seat, `single_class`) was not established from the code. — read 2026-10-08

### Playtomic now lets some players into a public match with payment pending
- **[COMPLAINT]** "Basura absoluta lo de que alguien pueda entrar un partido público con el pago
  pendiente, diga tres horas antes que no viene, no se salga porque no puede … y encima pague yo su
  parte de la pista" (Damihu97, ES, 2026-05-25). [App Store ES feed](https://itunes.apple.com/es/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08
- *Reading:* the help still says a spot "is only confirmed after payment"
  ([competitor-joiner](competitor-joiner.md#she-pays-her-own-spot-online-at-join-charged-at-once)); the review likely describes a private booking turned public, whose owner carries unpaid shares.

## R-RESCUE-9 — who is offered a freed seat, and how many are told

### HelloClub offers a freed court one person at a time, 10 minutes each
- **[POLICY]** "The first person to get on the waiting list, will be notified first when a court becomes
  available"; if they do not book, "a notification will be sent to the next person on the list after
  10 minutes"; it "does not guarantee a booking" and "anyone can make a booking for that slot". [Hello Club: Using the waiting list](https://help.helloclub.com/en/articles/1899045-using-the-waiting-list) (dated 2025-05-12) — read 2026-10-08

### FitDegree offers a freed class spot in turn, with a window that shrinks toward the start
- **[POLICY]** "Once a client's time ends, the next client on the list will be given a chance": 12 hours
  to respond 48 h before class, 4 hours at 47–13 h, "5 mins" under 13 h; when everyone's time runs out
  "the class is opened up to the public". [FitDegree: How does the waitlist work?](https://guide.fitdegree.com/support/solutions/articles/151000097566-how-does-the-waitlist-work-) (modified 2023-08-08) — read 2026-10-08

### CourtReserve tells the whole waitlist at once
- **[POLICY]** "Currently, CourtReserve sends an email to everyone on the waitlist at the same time";
  "Open spots are not reserved"; "It's first come, first serve"; up to 25 names per list. [CourtReserve: Court Waitlisting](https://help.courtreserve.com/en/articles/7235129-court-waitlisting) (updated 2026-04-30) — read 2026-10-08

### Playmore's league tells the players within the author's ladder range
- **[POLICY]** "Po rezerwacji powiadomimy graczy z Twojego zasięgu w rankingu — kto pierwszy się
  zgłosi, ten gra"; the author sees "Powiadomiliśmy {n} graczy z Twojego zasięgu" and may invite named
  players from a small quota ("Zostało Ci {n} zaproszeń"); a player out of range is refused "Ten mecz
  jest poza Twoim zasięgiem w drabince". [CPLsdYdo.js](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** A freed open-game seat goes to the whole waitlist at once (carried,
  [platforms](platforms.md#playmore--waiting-lists-and-alerts)) "push + e-mail, SMS gdy push nie doszedł",
  and "fala do subskrybentów komórki (liga #262) dochodzi osobno" — a second wave to players subscribed
  to that sport, level and daypart. [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) (flag `open-game-waitlist`) — read 2026-10-08

### Nobody ranks who hears of a seat by how even the game would be
- **[ABSENT]** Every queue found orders by time joined (HelloClub, FitDegree) or tells everyone at
  once (CourtReserve, MATCHi, Eversports, Playmore); Playmore narrows by ladder range, not by the game's
  balance. PADO's "Auto-Fill Matches" still says nothing of how it picks. — read 2026-10-08

## R-RESCUE-35 — does Playtomic's priority alert fire for a seat in an existing match?

### Playtomic's alert is for "available matches"
- **[POLICY]** "With a standard Playtomic account, you can set up one priority alert to get push
  notifications for available matches"; Settings › Notifications › Priority alerts › "+ New alert".
  [How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App) (updated 2026-09-29; read through the help centre's API, the page refuses robots) — read 2026-10-08
- **[POLICY]** Premium: "Create unlimited custom alerts to receive push notifications when matches
  become available. Customize alerts based on your preferences." [Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited) (updated 2026-09-30) — read 2026-10-08
- **[POLICY]** App Store: "select which notifications you want to receive … so that you stay up to
  date on matches, courts, and last-minute opportunities". [App Store GB](https://apps.apple.com/gb/app/playtomic-padel-pickleball/id1242321076) — read 2026-10-08
- **[ABSENT]** Whether "available matches" includes a seat freed in a match already full: not said in
  the help, the Terms, the listing or 1 636 reviews. — read 2026-10-08

### Players say the alerts don't fire
- **[COMPLAINT]** "Nunca funcionan las alertas" (Eemm27, ES, 2025-04-10); "Je ne recois aucune alertes
  prioritaires" (Women 55, FR, 2024-01-30); "Notifications never trigger and alerts are not intuitive
  to setup. Odd restrictions on times." (mytr77, GB, 2025-04-08); a Premium user's "alert per i campi
  liberi non funziona da mesi" (Lorilol93, IT, 2023-06-27); expired alerts listed first (caterinaa_, GB, 2025-06-07). [App Store feeds](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

## R-RESCUE-23 — are the others told the seat was taken?

### Playmore tells the organiser who joined, and the roster when it fills
- **[POLICY]** The organiser gets "Ktoś dołączył do Twojej gry — Przywitaj się" with ready greetings;
  the roster gets a push "Komplet w Waszej grze" or "Mecz potwierdzony" opening a sheet with contacts
  and calendar (flag `open-game-filled-moment`, on for all clubs since 26 Sep 2026); the roster's
  contacts sheet says "Ktoś się wypisał — w składzie zwolniło się miejsce." [93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js), [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08

## R-RESCUE-2 — is a seat left at the cut-off kept or given back, and is the hour resold?

### Playmore's own numbers on full games that don't happen
- **[POLICY]** Playmore's flag notes, written by its team: full game → game played "57% → ≥ 75%" (the
  target of its "Komplet" push); "3 z 10 kompletów, które się nie odbyły, padły po wypisaniu bez
  dosadzenia" (3 of 10 full games that didn't happen fell after a leave nobody refilled); the
  waitlist stays if "dosadzenia zwolnionych miejsc ≥ 50% (n ≥ 6)"; full games called off by their
  organiser in one click, before a confirmation step was added, "2 w 4 tygodnie"; open-game join starts "~70 … miesięcznie". [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) (flags `open-game-filled-moment`, `open-game-waitlist`, `open-game-organizer-leave`, `session-replay-open-game-join`) — read 2026-10-08

### Playmore counts a game called off at its cut-off as an empty court
- **[POLICY]** On games started from the court checkout: "gry z checkoutu, które nie skompletują się do
  cutoffu, zostawiają kort pusty zamiast normalnej rezerwacji" — named "główne ryzyko biznesowe",
  checked weekly, with the flag as its kill switch. [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) (flag `checkout-open-game-hint`) — read 2026-10-08
- *Reading:* Playmore's default call-off is 2 h before the start, so a court it gives back is rarely resold; at 24 h ahead nobody publishes a resale rate.
- **[POLICY]** Demand signal at one Warsaw club (Okęcie, 27 Sep 2026): "~2/3 otwarć arkusza to gry
  pełne" — two in three game previews opened were of full games. [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) (flag `open-game-waitlist`) — read 2026-10-08

### Playtomic keeps a court longer the fuller the match
- **[POLICY]** "1 player: The court is never reserved. 2 players: Court reserved if more than 12 hours
  until match time. 3 players: Court reserved if more than 4 hours until match time. 4 players: Court
  always reserved"; "Our system predicts match completion based on time, club popularity, and player
  patterns"; "Cancelled matches can't be restored." [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465-Cancellation-Policy-for-Open-Matches-Padel-Tennis) (updated 2026-09-30) — read 2026-10-08
- *Reading:* a match one player short keeps its court until 4 h before the start at Playtomic — not 24 h.

### Kraków desks resell a late-cancelled hour; nobody publishes how often
- **[POLICY]** Squash4You puts a late-cancelled hour back on its online grid for everyone and tries to
  sell it first (see R-RESCUE-5 above).
- **[ABSENT]** How often a Kraków booker short one player keeps the court, or how often a club resells an
  hour given back 24 h ahead, by daypart: no club, booking system or report publishes it (searched
  web coverage of Playtomic's Global Padel Report, Kraków and Polish club pages and price lists,
  Playtomic's help on cancellations; none gives a cancellation, resale or daypart occupancy rate). — read 2026-10-08
- *Reading:* the evening premium in Kraków prices ([local-market](local-market.md#court-prices-in-kraków)) says evenings sell out first; a measured rate needs the clubs' own booking data.

## R-RESCUE-29 — card fees when everyone is refunded

### tenis4U's 2 % is taken on any deleted online booking
- **[POLICY]** "Usunięcie rezerwacji opłaconej za pomocą płatności internetowych generuje zwrot środków
  pomniejszonych o opłatę transakcyjną w wysokości 2%" — the rule names the deleted booking, not who
  deletes it. [tenis4U Regulamin pkt 11](https://tenis4u.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Carried: Garden Padel keeps the payment operator's 2 % on a weather cancellation, which is
  the club's call ([local-market](local-market.md#the-refund-deduction-players-already-know-a-flat-2-)).

### Playmore refunds to its wallet and keeps the service fee; the commission on a refund is unstated
- **[POLICY]** Every open-game refund: "wpisowe wraca na portfel Playmore. Opłata serwisowa nie podlega
  zwrotowi"; a late leaver's fee comes back "Jeśli gra nie zbierze składu albo odwoła ją klub"; where
  the online payment "trafiła prosto do klubu … to klub oddaje pieniądze na Twoją kartę lub konto". [CG9yQPLY.js](https://playmore.pl/assets/CG9yQPLY.js), [93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** Whether the club's 1,79 % commission is credited back on a refund: the price page says
  only "Liczona od płatności, które gracze robią w aplikacji i na stronie" and nothing on refunds. [Playmore cennik](https://join.playmore.pl/cennik/) — read 2026-10-08

## R-RESCUE-14 — does "I'm in · 40 zł" satisfy the order-button rule?

### Still no authority on "I'm in", "join", or a price printed on the button
- **[ABSENT]** No UOKiK decision, Polish court ruling or CJEU judgment found on "Dołącz", "Zapisz się",
  "I'm in", or a label carrying the amount ("Zapłać 40 zł", "… · 40 zł"); searched UOKiK's pages,
  Polish legal press on art. 17 and German case law on § 312j BGB. — read 2026-10-08

### The nearest rulings: membership and payment-method labels failed
- **[LAW]** LG München I, 19 Jun 2023, 4 HK O 9117/22: "Jetzt Mitglied werden" fails the button rule
  for a paid membership after a free month; the price stood at the top of the page, not on the button;
  the court pointed to "kostenpflichtig abonnieren" as a clear alternative. [IT-Recht Kanzlei report](https://www.it-recht-kanzlei.de/lg-muenchen-i-jetzt-mitglied-werden-bestellbutton.html) — read 2026-10-08
- **[LAW]** LG Hildesheim, 7 Mar 2023, 6 O 156/22: "Mit PayPal bezahlen", "Mit Kreditkarte bezahlen"
  fail when they sit under a payment-method step: the customer may read them as confirming "zunächst
  lediglich das Zahlungsmittel", not as ordering. [IT-Recht Kanzlei report](https://www.it-recht-kanzlei.de/beschriftung-bestellbutton-mit-zahlungsart-unzulaessig.html) — read 2026-10-08
- *Reading:* both rulings turn on a verb that does not say "pay"; neither tests a pay verb with the
  amount. Carried: UOKiK accepts "zapłać teraz" and rejected "Zamawiam" ([local-market](local-market.md#the-order-button-and-a-yes-that-charges-later)).

### What Playmore prints on its buttons
- **[POLICY]** Playmore's buttons pair a pay verb with the amount: "Zapłać {amount}", "Zapłać teraz",
  "Gram · zapłać {amount}" (league seat), "Dołącz i zapłać {amount}" (joining from an invite),
  "Utwórz i zapłać wpisowe ({fee})" (creating a game); its open-game preview says "Dołącz za {price}"
  and leads to the checkout; its guest booking button reads "Zarezerwuj za {price} {currency}".
  [93jAIRDY.js](https://playmore.pl/assets/93jAIRDY.js), [CPLsdYdo.js](https://playmore.pl/assets/CPLsdYdo.js), [CbBkX2Te.js](https://playmore.pl/assets/CbBkX2Te.js) — read 2026-10-08

## R-RESCUE-15 — do players read a ten-second "Booking" toast as a payment?

### Needs players, not research
- **[ABSENT]** No study or review found on how people read a timed toast that ends in a charge; no app
  found where one tap pays for a seat behind an Undo (carried: [platforms](platforms.md#swipe-decks-deal-people-not-games)). Only testing with players can answer it. — read 2026-10-08

### Where a timed Undo is familiar
- **[DOCS]** Gmail: after sending, "you'll see 'Message sent' and the option to 'Undo'"; the "Send
  cancellation period" is "5, 10, 20, or 30 seconds", chosen in Settings. [Gmail Help: Send or unsend](https://support.google.com/mail/answer/2819488?hl=en) — read 2026-10-08

### The accessibility rule on time limits
- **[DOCS]** WCAG 2.2 SC 2.2.1 (Level A): for each time limit set by the content, the user can turn it
  off, adjust it to at least ten times the default, or extend it with at least 20 seconds' warning —
  unless it is part of a real-time event, essential, or over 20 hours. [W3C: Understanding SC 2.2.1](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html) — read 2026-10-08
- *Reading:* whether a ten-second Undo before a charge is a "time limit" in this sense is untested; Gmail lets the user choose the length.

## R-RESCUE-21 — how often a capture fails after the hold succeeded

### Providers describe an authorisation as a guarantee and publish no failure rate
- **[DOCS]** Stripe: "Authorizing a payment guarantees the amount by holding it on the customer's
  payment method"; the funds must be captured before the authorisation expires. [Stripe: Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-08
- **[DOCS]** Adyen: a CAPTURE_FAILED means "the capture or refund was rejected by the card scheme";
  six causes — technical issue (Adyen re-captures itself), shopper cancelled a recurring payment,
  incorrect request, account configuration error, capture expired, cannot be re-captured. [Adyen: CAPTURE_FAILED and REFUND_FAILED reasons](https://docs.adyen.com/online-payments/capture/failure-reasons) — read 2026-10-08
- **[ABSENT]** A rate of captures failing after a successful hold: not published by Stripe or Adyen,
  nor found elsewhere; only the provider's own data, or a test account, could give it. — read 2026-10-08

## R-RESCUE-24 — more on a seat held while a payment is put right

### Airbnb blocks the dates for 24 hours while the guest fixes a failed payment
- **[POLICY]** "What does awaiting payment mean?": the guest "will have 24 hours to successfully update
  their payment info"; "dates will be blocked on the host's calendar for up to 24 hours"; otherwise "the
  request to book will be withdrawn with no consequences to the host or guest". [Airbnb Help 2411](https://www.airbnb.com/help/article/2411) — read 2026-10-08

## R-RESCUE-37 — how long an On request club takes to answer

### Playmore's club-approved requests promise an answer within two days
- **[POLICY]** Playmore's standing-slot request ("Stały termin"), at clubs that approve them: status
  "Czeka na klub"; "Klub odpowie w ciągu 2 dni."; "Dostaniesz powiadomienie."; at most "3 wnioski
  czekające na odpowiedź"; a club's counter-proposal "wygasła po 7 dniach". The feature is off (flag
  `standing-slots` "na 0%", 5 Oct 2026). [DyQUCw1g.js](https://playmore.pl/assets/DyQUCw1g.js), [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08
- **[ABSENT]** How long Kraków desks actually take to answer, and how players read an amber "waiting for
  the club" with no time: no published figure; only the desks' own logs and players can say. — read 2026-10-08

## R-RESCUE-1 and R-RESCUE-23 — how Kraków groups refill a seat and say it is filled

### Still unreadable
- **[ABSENT]** No readable Kraków group post was found again: web search for "szukam czwartego",
  "brakuje jednej osoby" with padel, squash, tenis and Kraków, and for Reddit or WhatsApp group links,
  returned club listings only; Facebook groups need a login (carried: [platforms](platforms.md#kraków-groups-could-not-be-read)). — read 2026-10-08

### Playmore builds on the group chat rather than replacing it
- **[POLICY]** Playmore's flag notes: the WhatsApp share opens WhatsApp with no recipient, because
  "WhatsApp sam pokazuje wybór kontaktu i GRUPY, czyli tego, czego potrzebuje ekipa kortowa";
  "WhatsApp jest główną akcją" of its game-filling lever; a court booking's WhatsApp message carries a
  second line linking the club's open games. [p_SkNwim.js](https://playmore.pl/assets/p_SkNwim.js) (flags `whatsapp-quick-messages`, `open-game-court-bridge`) — read 2026-10-08

## R-RESCUE-11 — the club's address on the rescue's details

### A code question, with the market beside it
- *Routed:* whether the rescue's details show the club's address is for the Rule agent to read in the code.
- **[LAW]** Carried: the seller's identity and address must be shown before the player is bound (art.
  12, the club's when Rakieta concludes for it) ([local-market](local-market.md#what-the-player-must-see-before-being-bound)).
- **[POLICY]** Playmore's open-game join card on a booking page lists "Termin", "Kort", "Wolne miejsca",
  "Cena za osobę"; its payment page names "Obiekt sportowy" with court, date and price; its club data
  carry a trade name only (carried: [platforms](platforms.md#playmore--operator-scale-and-seller)). [CG9yQPLY.js](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
