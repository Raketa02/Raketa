# Gaps round — payments pass, market 01: Kraków's courts and desks, and the rivals' screens (§4–7, §9, §14–15)

Part of the payments pass's market gaps round 01 on FILL and LEAVE (PRD #530), read **2026-10-20**. The index, the
sources and where each gap stands are in [`gaps-payments-01.md`](gaps-payments-01.md).

- **The extracts:** the two tenis4U reads and Playmore's served strings are saved as
  [`../shots/gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt`](../shots/gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt)
  and [`../shots/gaps-payments-01-playmore-served-2026-10-20.txt`](../shots/gaps-payments-01-playmore-served-2026-10-20.txt).
- **Playmore's own figures** come from notes in its shipped code. They are the company's numbers, Playmore-wide, for
  all sports, and not audited.
- **Not reachable:** YouTube refused kluby.org's help videos to scripted reads.

---

## 4. R-FILL-19: Bajada's and Fame Sport's outdoor courts out of season, and an hour booked through an outside platform

Carried, not repeated: Bajada has 3 indoor and 2 seasonal outdoor padel courts, Fame Sport 1 and 1
(`gaps-COURTS.md#two-of-eleven-kraków-area-padel-clubs-have-indoor-and-outdoor-courts`, read 2026-10-08); Fame Sport's
winter 2026/27 price list prices only hall padel (same file, `#bajadas-indoor-price-not-published`); no club system
takes a booking from outside (`gaps-FILL.md#8-blocking-hours-from-outside`); tenis4U desks type bookings made elsewhere
into their grid as named blocks (`gaps-S-01B.md#tenis4u-desks-already-type-bookings-made-elsewhere-into-their-grid-as-named-blocks`).

### R-FILL-19 · Bajada still sells both outdoor courts online, through tenis4U, until at least 9 November

- **[MEASURED]** tenis4U's public endpoints for Bajada Padel Club (id 421), read 2026-10-20 10:56 CEST: five padel
  courts, two of them `"type_name": "padel outdoor"`, `"roofing": "NONE"`, `"enabled": true`; booking window 21 days
  (it was 14 on 9 October); free cancellation until 24 h; online payment required. Both outdoor courts have free hours
  on every one of the 21 days to 9 November (320 and 317 free hours in all); the only block on them is a private event
  on Sunday 25 October ("Impreza", on all five courts). Extract `../shots/gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt`,
  from [tenis4U](https://app.tenis4u.pl/#/court/421) (`GET https://api.tenis4u.pl/court/421`, `/occupancy/421`) — read 2026-10-20
- **[MEASURED]** Same read, weekday evenings 17:00–22:00 to 9 November: Bajada's two indoor doubles courts are taken at
  every weekday-evening hour except Friday 23 Oct 17:00, Fri 30 Oct 17:00, Mon 2 Nov 21:00, Fri 6 Nov 17:00 and Mon
  9 Nov 17:00; every other free weekday-evening court at Bajada is an outdoor one. Same extract — read 2026-10-20
- **[POLICY]** Playmore's page for Bajada: "W ciepłe miesiące dostępne są dodatkowe korty zewnętrzne — warto sprawdzić
  dostępność na Playmore" (in warm months extra outdoor courts are available) and "Dwa korty zewnętrzne działają
  sezonowo, w cieplejszych miesiącach" (the two outdoor courts work seasonally, in the warmer months). No end date is
  given. [Playmore: Bajada Sports Club](https://playmore.pl/klub/bajada-sports-club/) — read 2026-10-20
- *Reading:* in late October the outdoor courts are on sale and are most of what is free at Bajada on a weekday
  evening, so a game that takes "the first free court of any kind" there now lands outdoors. When the outdoor season
  ends is not published; the booking window does not reach December, so whether they are sold in winter is still
  *not found*.

### R-FILL-19 · Fame Sport sells both padel courts through tenis4U to 18 November

- **[MEASURED]** Fame Sport Club (tenis4U id 104), read 2026-10-20 10:57 CEST: padel stations "padel" (1197) and
  "padel hala" (1535), both enabled; 30-day window to 18 November. "padel" has free hours on 29 of 30 days (413.5 h),
  blocked only on 1 November ("KLUB ZAMKNIĘTY - ŚWIĘTO") and the evening of 7 November ("RTL PARTY"); "padel hala" is
  blocked on weekend days 10:00–19:00 for "PADEL LIGA / ROTATION". tenis4U leaves Fame Sport's `roofing` field empty.
  Same extract — read 2026-10-20
- *Reading, unverified:* "padel" without "hala" is the outdoor court; if so, Fame Sport also sells its outdoor court
  into mid-November, although its winter 2026/27 price list names only hall padel (carried above).
- **[ABSENT]** Fame Sport's own season dates: famesport.pl now serves only a WordPress sign-in page, and its 2026 rules
  PDF (`/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf`) returns 404 — read 2026-10-20

### R-FILL-19 · Garden Padel, an outdoor club on PADO's list, also sells into November

- **[MEASURED]** Garden Padel (tenis4U id 483), read 2026-10-20 10:57 CEST: four padel courts on sale for the 14-day
  window to 2 November, free hours on every day; each court is blocked 09:00–15:00 Monday to Thursday ("zamkniete"),
  09:00–15:30 on Fridays (unnamed) and for "Turniej" 11:00–14:00 and 15:00–18:00 at weekends.
  Same extract — read 2026-10-20

### R-FILL-19 · An outside platform that lists a Kraków tenis4U club sends the booker to the club's tenis4U grid

- **[POLICY]** Playmore's directory carries Bajada as an outside venue: `"venueId":null,"isExternal":true`,
  `"bookingUrl":"https://app.tenis4u.pl/#/court/421"`, its five courts copied from tenis4U ("padel debel" ×2, "padel
  singiel", "padel outdoor" ×2). Playmore's code maps a tenis4U venue to `_isExternal: true, _isTenis4you: true,
  _hasAvailability: true`, so it shows tenis4U's free hours and hands the booking to tenis4U.
  [Playmore: Bajada](https://playmore.pl/klub/bajada-sports-club/), [`/assets/BZKsZmQ2.js`](https://playmore.pl/assets/BZKsZmQ2.js) — read 2026-10-20
- **[POLICY]** The same directory lists other sources it reads venues from: "Kluby.org — Polskie kluby sportowe (667
  obiektów)", "Tenis4U — Korty tenisowe (katalog, bez rezerwacji online)", "Zagraj w Padla — Polskie kluby padla
  (katalog)". [`/assets/CuTXkj_H.js`](https://playmore.pl/assets/CuTXkj_H.js) — read 2026-10-20
- **[MEASURED]** The names Kraków desks give their blocks on 2026-10-20: "PADEL LIGA / ROTATION", "RTL PARTY", "KLUB
  ZAMKNIĘTY - ŚWIĘTO" (Fame Sport); "Impreza", "Impreza zamknięta" (Bajada); "zamkniete" (Garden Padel). None names
  an outside platform. Same extract — read 2026-10-20
- **[ABSENT]** Whether a Kraków desk keeps an hour booked through an outside platform off its phone sales: no club's
  terms or page says so, and no booking made through another platform could be watched. Searched: the five tenis4U
  clubs' grids, Playmore's directory code, kluby.org's terms and changelog (2014–2026), tenis4U's terms — read 2026-10-20
  - *Reading:* in Kraków the "outside platforms" that list these clubs (Playmore, PADO) do not hold hours of their own:
    they show tenis4U's grid and send the booker to it, so there is one calendar per club and nothing to keep apart.
    A Raketa booking would be the first one not made in that calendar.

---

## 5. R-FILL-20: whether Kraków players expect to pick, keep or rotate their partner in a casual four

Carried: Playtomic lets players swap positions after the match and before the result; social formats rotate partners;
nothing Kraków-specific was found (`gaps-FILL.md#9-the-drawn-sides`); Playmore records who played with whom only when
the result is entered (`platforms.md#a-balance-figure-or-suggested-sides`).

### R-FILL-20 · Playmore: nine court bookings in ten never record a second player

- **[POLICY]** Playmore's own figure, written in its served web app's feature notes (19 Oct 2026): "91% rezerwacji
  kortu kończy się bez dopisanego współgracza, a liga przyjmuje wynik tylko od rezerwacji z dwiema osobami" (91 % of
  court bookings end without a co-player added). And (9 Oct 2026): "79% organizatorów nie ma w kroku „Z kim grasz?”
  kogo wybrać, więc podziału nie zakłada niecały 1% rezerwacji, przy których jest możliwy" (79 % of organisers have
  nobody to pick at "Who are you playing with?", so under 1 % of bookings set up a split). Playmore-wide, all sports;
  not audited. [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js) — read 2026-10-20
  - *Reading:* the people in a Polish court booking are arranged outside the app; who partners whom is not something
    the market leader's players record before the game.

### R-FILL-20 · Playmore's leagues: you invite your own partner, or the club pairs you, and you name your side of the court

- **[POLICY]** Doubles leagues: "Grasz w parze. Partnera zapraszasz sam, a gdy przyjmie zaproszenie, klub wstawia Waszą
  parę do grupy" or "Pary tworzy klub"; a player sets "Preferowana strona kortu" (Lewa / Prawa / Obojętnie): "To tylko
  podpowiedź przy dobieraniu par — nikogo nie ukrywa ani nie wyklucza." (a hint when pairs are made; it hides or
  excludes nobody). [`/assets/CtEmagZ3.js`](https://playmore.pl/assets/CtEmagZ3.js) — read 2026-10-20
- **[POLICY]** Club tournaments offered: "Americano, Mexicano, Piekło/Niebo i pucharowe" — Americano and Mexicano
  rotate partners. [`/assets/C9ye8j_u.js`](https://playmore.pl/assets/C9ye8j_u.js) — read 2026-10-20
- **[MEASURED]** Fame Sport blocks its hall padel court on weekend days 10:00–19:00 for "PADEL LIGA / ROTATION" through
  mid-November. tenis4U grid, extract above — read 2026-10-20

### R-FILL-20 · Kraków players' own expectation: still not found

- **[ABSENT]** No Kraków or Polish post, survey or club rule on whether a casual four keeps, picks or rotates partners.
  Searched this round: Polish web search ("zmiana partnera po secie", "pary losowane", "gry otwarte" Kraków), English
  search incl. Reddit (r/padel's search refuses scripted reads with 403), padel etiquette guides (Red Bull, Padel
  Browser, The Padel Passport: none local, none ruling), Playmore's served strings. Facebook groups need a login
  (carried) — read 2026-10-20

---

## 6. R-FILL-21: what a tenis4U or kluby.org booker receives when the desk moves the booking

Carried: both desks can move a booking and nothing said the booker is told
(`gaps-EMAIL.md#tenis4u-and-klubyorg-a-desk-can-move-a-booking-nothing-says-the-booker-is-told`); tenis4U's panel has no
tell-the-players choice on Move (`gaps-CLUBBOOK.md#tenis4us-panel-no-tell-the-players-choice-on-move-or-cancel`).

### R-FILL-21 · tenis4U's panel sends only the new time and court, and logs the move

- **[POLICY]** tenis4U's club panel as served today (`main.bf9c0f8a156c883a.js`, newer than the 2026-10-08 read): a
  move sends `{start_time, end_time, station_id}` for new-style bookings (older ones resend colour, court, comment,
  message, times, coach and lighting); no notify flag exists. On failure: "Nie udało się przenieść rezerwacji" or
  "Wskazano termin poza godzinami otwarcia kortu". The booking's history in the panel shows
  the move as "Przeniesiono rezerwację" with the new time, the court and who did it. [tenis4U panel](https://panel.tenis4u.pl/) — read 2026-10-20
- **[POLICY]** The player web app (`main.cf446af5e9523413.js`, unchanged) holds cancel lines ("Rezerwacja odwołana")
  and nothing for a moved booking; its notifications arrive from the server as a title and text, so whether a move
  produces one is decided server-side. [tenis4U app](https://app.tenis4u.pl/) — read 2026-10-20
- **[POLICY]** tenis4U's terms: "Dokonując rezerwacji wyrażasz zgodę na kontakt z Tobą bezpośrednio przez usługodawcę
  lub za pośrednictwem tenis4U, poprzez wiadomości SMS, wiadomości E-mail czy kontakt telefonicznego w celach
  niezbędnych do realizacji usługi" (by booking you agree to be contacted by the club, directly or through tenis4U, by
  SMS, e-mail or phone, as the service needs); its notices cover "o własnych rezerwacjach" (your own bookings), by SMS
  or push. [tenis4U: regulamin](https://tenis4u.pl/regulamin/) — read 2026-10-20

### R-FILL-21 · kluby.org: the club decides, and kluby.org disclaims it

- **[POLICY]** kluby.org's app terms: the app provides "powiadomienia o Rozgrywkach sportowych i dokonanych
  Rezerwacjach"; "ITTS nie ma wpływu jak również nie ponosi odpowiedzialności za częstotliwość oraz fakt przesyłania
  powiadomień przez Innych Usługodawców" (kluby.org has no say over, and no responsibility for, whether and how often
  clubs send notices); by booking the user agrees to contact "bezpośrednio przez Klub lub za pośrednictwem Aplikacji –
  poprzez wiadomości e-mail/SMS, powiadomienia PUSH czy kontakt telefoniczny". [kluby.org: regulamin](https://kluby.org/regulamin) — read 2026-10-20
- **[POLICY]** kluby.org's changelog, every year 2014–2026: "Możliwość zamiany miejscami rezerwacji na grafiku" (2016),
  "Powiadomienie dla pracownika o odwołanej rezerwacji" (2020), "Podgląd wysłanych powiadomień w historii klienta o
  rezerwacjach" (2022); no entry for telling a customer that a booking moved. [kluby.org: changelog](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-20
- **[ABSENT]** kluby.org's help videos "2.3.2. Edycja rezerwacji" (YouTube `tUmANuUF4yM`, 5 min 18 s) and "2.5.
  Powiadomienia" (`1ibSZxbDhrE`, 3 min 43 s) have Polish automatic captions, but YouTube refused both the captions and
  the video to every scripted client without a proof-of-origin token, so neither was watched.
  [kluby.org: pomoc](https://oferta.kluby.org/pomoc) — read 2026-10-20

### R-FILL-21 · For comparison, Playmore always tells: "Zmiana w rezerwacji"

- **[POLICY]** Playmore's bell maps `reservation_update` to the headline "Zmiana w rezerwacji", and its notice settings
  say changes and cancellations of bookings are always sent and cannot be muted ("wszystkie odwołania i zmiany
  rezerwacji"). Carried from `../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt` (2026-10-08); the map is
  unchanged in today's [`/assets/BDacQxpB.js`](https://playmore.pl/assets/BDacQxpB.js) — read 2026-10-20
- **[POLICY]** Since 11 October, when the booking's owner moves the court, Playmore offers a ready WhatsApp text for the
  others ("zmiana terminu (właściciel przełożył kort)"). [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js), flag `whatsapp-group-moments` — read 2026-10-20
- **[ABSENT]** What a tenis4U or kluby.org booker actually receives when the desk moves the booking: still not found;
  only a booking moved by a desk, watched from the booker's phone, answers it — read 2026-10-20

---

## 7. R-FILL-27: what Playtomic shows the joiner whose join completes a match

Carried: no distinct "match complete" screen or push at Playtomic
(`gaps-FILL.md#not-found-a-distinct-match-complete-screen-or-push-at-playtomic`).

### R-FILL-27 · Playtomic locks a public match when the fourth player joins

- **[POLICY]** "When a fourth player joins a public match, it becomes locked, and no player can leave independently.
  Players must request removal through the match chat so that your club can handle it via Playtomic Manager."
  [Playtomic Manager help: How to Handle Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097-How-to-Handle-Common-Booking-Issues-A-Quick-Guide-for-Your-Club) (updated 2026-08-03) — read 2026-10-20
- **[POLICY]** "If the match is complete with four players and it starts within 24 hours, you need to contact the Club
  directly". [Playtomic help: How can I delete myself from a Public Match?](https://playerhelp.playtomic.com/hc/en-gb/articles/19832116272785-How-can-I-delete-myself-from-a-Public-Match) (updated 2026-08-31) — read 2026-10-20
- **[ABSENT]** What the fourth joiner sees: not in any of Playtomic's 94 English and 99 Spanish player articles or 160
  and 155 club articles (Zendesk API, searched for "match is full", "complete", "fourth player", "completo", "cuarto
  jugador"); the Android package could not be fetched again (APKPure answers with a Cloudflare check, 403);
  app.playtomic.com serves only "Continue in the app"; the old help.playtomic.com no longer resolves — read 2026-10-20

### R-FILL-27 · Playmore, the Kraków rival, shows the filling joiner "Komplet!"

- **[POLICY]** After paying for a seat in someone else's open game, Playmore opens a sheet on the booking: "Jesteś w
  grze! · {count}/{limit} · brakuje {missing}" with invite buttons, or, when that join fills the game, "Komplet! ·
  {count}/{limit} · skład pełny" with "Poleć klub na WhatsAppie" and "Znasz kogoś, kto gra w {venue}? Dostanie alerty o
  grach". The flag note: "albo wariant „Komplet” (singiel, domknięty debel) z poleceniem alertów klubu
  (`surface=join_full`)"; on for every club with games since 10 October 2026.
  [`/assets/C9ye8j_u.js`](https://playmore.pl/assets/C9ye8j_u.js), [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js) (flag `open-game-join-invite`) — read 2026-10-20
- **[POLICY]** The organiser is told by push and then offered a WhatsApp text for the group: "komplet (ostatnie
  miejsce; organizator po arkuszu z pushu)"; text "Mamy komplet ✅ Gramy: {when}, {venue}. Do zobaczenia na korcie!".
  Same files, flag `whatsapp-group-moments` (added 2026-10-11) — read 2026-10-20

---

## 9. R-FILL-53: how fast a last free weekday-evening court sells in Kraków

Carried: no club or platform publishes it; tenis4U served no free hours on 10–11 October, so the earlier timing could not
be taken (`gaps-S-01B.md#the-third-read-meant-to-time-the-last-courts-could-not-be-taken`,
`gaps-S-01B.md#how-fast-a-last-court-sells-not-found`); on weekday evenings most court-hours are taken more than a week
ahead (`gaps-S-01A-hold.md#on-weekday-evenings-most-court-hours-are-taken-more-than-a-week-ahead`).

### R-FILL-53 · tenis4U serves free hours again; where a last weekday-evening court stood on 20 October

- **[MEASURED]** tenis4U's public grid serves free hours again: on Tuesday 20 October at 10:57 CEST every one of the
  five Kraków padel clubs on tenis4U showed free hours (102 free intervals at Padel House, 96 at Garden Padel, 180 at
  Bajada, 749 at Fame Sport), unlike 10–11 October, when none were served (carried above). Extract `../shots/gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt` — read 2026-10-20
- **[MEASURED]** Weekday evenings 17:00–22:00 at that read (whole hours, doubles courts): Padel House had no court free
  at any weekday-evening hour of its 14 days; Garden Padel had one court left at 6 hours (this evening 18:00 and 19:00,
  Wed 21 Oct 19:00, Fri 23 Oct 18:00, Wed 28 Oct 20:00 and 21:00); Bajada at 6 hours, every one an outdoor court (this
  evening 21:00, Fri 23 Oct 18:00 and 19:00, Wed 4 Nov 18:00–21:00); PADEL LOUNGE, a one-court club, at 13 hours; and at
  Fame Sport the hall court was taken at 79 weekday-evening hours that left only the other court. Same extract — read 2026-10-20
- **[MEASURED]** A second read 16 minutes later (11:13:38 CEST): of those 104 last-court hours, one had sold (PADEL
  LOUNGE, Thursday 22 October 20:00). None of this evening's last courts had sold (Garden Padel 18:00 and 19:00, Fame
  Sport 20:00 and 21:00, Bajada 21:00 outdoors, PADEL LOUNGE 21:00). Bajada's last free indoor court on Monday 2 November
  21:00 sold, with an outdoor court still free beside it. Same extract — read 2026-10-20
  - *Reading:* a coarse lower bound only: on a weekday morning, last evening courts in Kraków mostly outlast a quarter
    of an hour, including the same evening's. How many minutes they last is still not measured.

### R-FILL-53 · Playmore: fewer than one app booking in five is for the same day

- **[POLICY]** Playmore's own study, written in its served web app (18 Oct 2026, PostHog 28.09–18.10 and a copy of its
  database): "tylko 17% rezerwacji kortu z apki jest na dziś (po 20:00 — 0,8%), 24% na jutro, 54% w 0–2 dni; 34% to
  dokładnie ten sam dzień tygodnia i godzina co w ostatnich 5 tyg., 64% ±1 h. Mediana od otwarcia apki do potwierdzenia
  80 s" (only 17 % of app court bookings are for today, 0.8 % after 20:00; 24 % for tomorrow; 54 % within 0–2 days;
  34 % repeat the same weekday and hour as in the last five weeks, 64 % within an hour of it; median 80 s from opening
  the app to a confirmed booking). Playmore-wide, all sports; not audited.
  [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js), flag `my-club-book-chips` — read 2026-10-20
- **[ABSENT]** Minutes from a last free weekday-evening court appearing to its sale: still published nowhere, and two
  reads ~16 minutes apart time it only coarsely (above). What would answer it: the grid read every 10 to 15 minutes
  through a weekday afternoon and evening — read 2026-10-20

---

## 14. R-LEAVE-21: how often a fourth is found in a Kraków game's last 24 hours, and how often an hour handed back a day ahead sells again

Carried: published nowhere (`gaps-S-01A-hold.md#still-published-nowhere`,
`gaps-LEAVE.md#no-platform-or-club-publishes-a-late-fill-or-resale-rate`); hours handed back at Padel House were still
unsold the next morning (`gaps-S-02.md#hours-handed-back-at-the-busiest-club-were-still-unsold-the-next-morning`); about
one free weekend hour in ten sold over a day (`gaps-S-02.md#over-the-last-day-about-one-free-weekend-hour-in-ten-was-sold`).

### R-LEAVE-21 · Playmore: 88 % of its open games do not take place

- **[POLICY]** Playmore's own figures, written in its served web app's feature notes: "88% gier nie odbywa się" (88 %
  of games do not take place; flag `open-game-landing-states`, 26 Sep 2026); "23 osoby zakładają 68% gier" (23 people
  create 68 % of games; flag `open-game-recreate`); "Dane z ligi z 45 dni (60 gier, 95 miejsc)" (45 days of data: 60
  games, 95 seats; flag `open-game-score-required`, 8 Oct 2026); and the risk it watches weekly: "gry z checkoutu, które
  nie skompletują się do cutoffu, zostawiają kort pusty zamiast normalnej rezerwacji" (games started at checkout that
  do not fill by the cut-off leave the court empty instead of a normal booking). Playmore-wide, all sports; not
  audited; none splits by the hours before the start. [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js) — read 2026-10-20
  - *Reading:* the only Polish open-game platform is small (about 60 games in 45 days, all clubs) and most of its games
    never fill, so a fourth found late is rare there in absolute terms; the share found in the last 24 hours is still
    unknown.

### R-LEAVE-21 · A handed-back next-day hour meets real next-day demand

- **[POLICY]** Same Playmore study: 24 % of app court bookings are made for the next day and 17 % for the same day
  (quoted in full under R-FILL-53). [`/assets/BlUiZcxz.js`](https://playmore.pl/assets/BlUiZcxz.js) — read 2026-10-20
- **[MEASURED]** Hours that turned free between the two reads of 20 October: none. No weekday-evening half-hour at the five clubs turned free between 10:57 and 11:13, so no handed-back hour could be followed. Extract above — read 2026-10-20

### R-LEAVE-21 · The Global Padel Report has no fill or resale figure

- **[ABSENT]** Playtomic and Strategy&'s *Global Padel Report 2025* (44 pages) gives booking types by country (open
  matches, private, academy, leagues — no Poland), indoor against outdoor availability and prices, and no figure for how
  often an open match fills, when, or how fast a freed court resells. [Global Padel Report 2025 (PDF via Padel Addict)](https://www.padeladdict.com/wp-content/uploads/2025/07/PLAYTOMIC_GLOBAL-_PADEL_REPORT_2025.pdf) — read 2026-10-20
- **[ABSENT]** Kraków's own late-fill and resale rates: still not found; what would answer them is unchanged (reads of a
  club's grid and open games at 48, 24 and 2 hours before each start, or Raketa's own fills once live) — read 2026-10-20

---

## 15. R-LEAVE-51: whether Playtomic or Playmore ever tells a player that a refund failed

Answered for Playmore in an earlier round, under another area: a split share has the state "Błąd zwrotu"
(`gaps-PLATFORM.md#playmore-says-where-each-refund-went-and-names-a-failed-one`, read 2026-10-08). Playtomic's app had no
string for a failed or late refund (`gaps-PLATFORM.md#playtomic-a-fixed-promise-of-days-then-chat-in-office-hours`).

### R-LEAVE-51 · Playmore tells the payer on the share's page, and the organiser in the list, not by notice

- **[POLICY]** On the page where a co-player pays her share ("Spłata części rezerwacji"): "Rezerwacja została anulowana,
  ale zwrot Twojej wpłaty się nie powiódł. Napisz do nas przez pomoc w aplikacji." (the booking was cancelled, but
  refunding your payment failed; write to us through help in the app), on a red banner; the organiser's list shows
  that share as "Błąd zwrotu" in red. A refund that works reads "Rezerwacja została anulowana — Twoja wpłata wróciła do
  portfela" (back to the Playmore wallet). [`/assets/D9q4OuNg.js`](https://playmore.pl/assets/D9q4OuNg.js), [`/assets/Bdy1oKPq.js`](https://playmore.pl/assets/Bdy1oKPq.js) — read 2026-10-20
- **[POLICY]** Playmore's bell maps 33 kinds of notice; none is a failed refund (the only refund one is
  `wallet_first_partner_card_refund` → "Zwrot na portfel"). [`/assets/BDacQxpB.js`](https://playmore.pl/assets/BDacQxpB.js) — read 2026-10-20
  - *Reading:* the client can show a failed refund only where the player opens that share; whether the server also
    sends a text or e-mail is not visible in the client.
- **[POLICY]** The wallet's history names a failed withdrawal that came back: "Zwrot nieudanej wypłaty".
  [`/assets/CuTXkj_H.js`](https://playmore.pl/assets/CuTXkj_H.js) — read 2026-10-20

### R-LEAVE-51 · Playtomic: a promise of days, and no failure path

- **[POLICY]** "Playtomic processes the refund immediately, however, consider that it can take 2-15 business days to
  receive in your bank. This is determined by your own banks processes." Nothing on a refund that fails.
  [Playtomic help: Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593-Refunds-and-when-you-will-receive-your-money) (updated 2026-09-10) — read 2026-10-20
- **[ABSENT]** A failed-refund notice or article at Playtomic: none in the 94 English and 99 Spanish player articles or
  the 160 and 155 club articles (searched "refund" with "fail", "unsuccessful", "error", "could not", and
  "reembolso" with "fallido", "error", "rechazado"); the only hit is the US-only saved-card article's "contact the
  club first" for a charge made in error — read 2026-10-20
