# Payments gaps 02 — LEAVE and PAY (market)

Answers to the market gaps the payments-pass Moderator left on **R-LEAVE-3, -4, -8, -14, -25, -32, -34, -35, -36,
-38, -54** and **R-PAY-4, -18, -24, -42, -53**. Written 2026-10-20. Each gap is a `###` heading naming its rule ID.
Earlier answers in this folder are cited by anchor, not repeated; this file adds only what is new.

**Sources this round.**

- **Playmore's player web app**, read as shipped: 1,709 script files crawled from `https://playmore.pl/`. It ships
  Playmore's own feature-flag registry, with its team's notes in Polish (`BlUiZcxz.js`).
- **Playmore's club panel**, read as shipped: 482 script files crawled from the sign-in page of
  `https://manager.playmore.pl/`. Every visitor is served them, so no sign-in was needed.
- **Playtomic**: both help centres (160 club and 94 player en-gb articles, through the Zendesk API) and the Android
  package 6.94.0 (`com.playtomic`, XAPK from APKPure).
- **Padel Mates**: its web strings.
- **Other platforms**: CourtReserve, Pike13, Zenamu and bsport help pages, and the DiR padel clubs' terms.
- **Kraków clubs' terms** (Squash4You, Atras, Miazga, Garden Padel), **kluby.org**'s terms, scripts and App Store
  page.
- **NBP**'s *Zwyczaje płatnicze w Polsce w 2023 r.*, and Gemius figures as quoted by Przelewy24.
- **Stripe**'s Express Dashboard page.

Every quoted string and code line from the three apps is saved in
[`../shots/gaps-payments-02-playmore-playtomic-padelmates-2026-10-20.txt`](../shots/gaps-payments-02-playmore-playtomic-padelmates-2026-10-20.txt).

Kinds: `[POLICY]` a company's rule, help page or the text its own app or panel ships · `[DOCS]` a provider's,
regulator's or survey's document · `[MEASURED]` read from the product as served (code or package, extract saved) ·
`[COMPLAINT]` · `[ABSENT]` looked for and not found, with where. Lines marked *reading* are inference, not sources.

| Rule | Status |
|---|---|
| R-LEAVE-34, R-LEAVE-35 | **Answered**: a racquet-club platform books a waiting player and charges them with no tap; Playmore and Playtomic never do |
| R-LEAVE-54 | **Answered for the market**: rivals give clubs their own Stripe Dashboard and some send refunds there; whether a Kraków desk acts in it is still a question for a club |
| R-LEAVE-32 | *Not found*: no club's expectation published; nearest facts listed |
| R-LEAVE-8 | **Answered for Playmore**; Padel Mates' silence when nobody takes the spot confirmed *not found* again |
| R-LEAVE-38 | **Answered for Playmore** (a confirmed game goes ahead short; the one left is not refunded) and a written venue rule (DiR); a Kraków desk's practice *not found* |
| R-LEAVE-36 | *Not found* |
| R-LEAVE-25 | **Answered**: Playmore sends the desk nothing; the calendar marks it, and a webhook exists |
| R-LEAVE-3 | **Partly**: Playmore's leave press carries no cost, so nothing can be compared. Its server does re-check the line at the press for cancel-for-all, which a late full game refuses, and for a reschedule, refused when the fee changed. A stale plain leave is still untried |
| R-LEAVE-14 | *Not found* |
| R-LEAVE-4 | *Not found* for Kraków; one written venue rule abroad |
| R-PAY-4 | **Narrowed**: at most 13,3 % of Poles 15+ hold no card at all (NBP 2023); the exact share is still unmeasured |
| R-PAY-18 | **Answered as absent**: no rival ships or publishes a message for a cap on adding cards |
| R-PAY-53 | **Answered**: neither Playmore's panel nor Playtomic Manager shows a club a pending or failed refund; tenis4U *not found* |
| R-PAY-42 | *Not found* (one more pointer, not a statement) |
| R-PAY-24 | *Not found* for kluby.org |

---

### R-LEAVE-34, R-LEAVE-35 — A racquet-club platform books the waiting player and charges them; Playmore and Playtomic only tell

**A platform that books a waiting player by itself, money included.**

- **[POLICY] CourtReserve** (US racquet-club software) has an *Auto Registration* waitlist for events:
  - "When an event spot becomes available, CourtReserve automatically registers the first name on the waitlist."
  - "The registered person is sent a notification but does not have to respond to be registered/confirmed."
  - It "posts the event fee to their account", and "Any remaining amount is charged to the player's saved payment
    methods, tried one at a time until one succeeds."
  - If payment can't be collected, "the player stays registered and the fee remains on their account as an unpaid
    balance. The registration is not canceled, and the spot doesn't pass to the next player on the waitlist."
  - "CourtReserve doesn't automatically notify players or system users when an auto-registration payment isn't
    collected."
  - Auto-registration runs only "up to the cutoff point set by Prevent Auto Registrations X Hours Before Event"; the
    example: "no players will be automatically moved from the waitlist within 8 hours of the event start time".
  - It works for single-date events only; recurring events fall back to notifying everyone.

  [CourtReserve: Event registration waitlists](https://help.courtreserve.com/en/articles/6601471-event-registration-waitlists)
  (page shows "Updated today") — read 2026-10-20
- **[POLICY] Pike13** (studios and clubs): "If a spot opens, the client is automatically enrolled and their card on
  file is automatically charged the course fee"; clients "must have a payment method on file" to join the waitlist;
  staff set "how many hours before the event the auto-fill stops". [Pike13: Course Waitlists](https://help.pike13.com/hc/en-us/articles/21119527966605-Course-Waitlists)
  — read 2026-10-20
- **[POLICY] Zenamu** (studio booking): the client at the top of the queue is "booked into the class, notified via
  email", using credits held when they joined. Card and PayPal waitlisters are charged at once ("Paid" with a
  "waitlist" tag) and refunded automatically once the class has started if no spot opened. Automatic filling stops at
  the cancellation deadline, except for card and PayPal bookings.
  [Zenamu: Waitlist for fully booked classes](https://help.zenamu.com/articles/11628592) — read 2026-10-20
- **[POLICY] bsport** (studios), *First in line* mode: "when a spot opens, the next client in line is booked
  automatically"; "Credits are deducted from the pass expiring soonest". Automatic booking stops a set number of
  minutes before the session; after that "they'll get a notification instead so they can confirm manually".
  [bsport: Waitlist management](https://intercom.help/bsport-helpcenter/en/articles/16096632-waitlist-management)
  (dated 2026-07-27) — read 2026-10-20

**The padel platforms in or near Kraków never book by themselves.**

- **[MEASURED] Playmore**, open games. A waitlist on a full game went live in four clubs on 2026-09-27 and in every
  club with games on 2026-10-10. Its rule, as Playmore's own notes give it: "Gdy zwolni się miejsce, powiadomimy
  wszystkich z listy naraz — kto pierwszy, ten gra." (no queue position).
  - Its reason: "3 z 10 kompletów, które się nie odbyły, padły po wypisaniu bez dosadzenia" — 3 of 10 full games that
    did not happen fell apart after a drop-out that nobody refilled.
  - A game confirmed at its cut-off has no *Join*, so it has no waitlist either: "potwierdzona po cut-offie nie ma
    „Dołącz”, więc nie ma też listy".

  Flag `open-game-waitlist` in `BlUiZcxz.js`, extract §A — read 2026-10-20. This confirms
  [`../areas/LEAVE.md`](../areas/LEAVE.md) §11 [p-waitlist].
- **[MEASURED] Playmore**, classes and tournaments, "Lista rezerwowa 2.0" (flag added 2026-10-14 at 0 %, switched on
  club by club). A club in *queue* mode "proponuje zwolnione miejsce po kolei: pierwsza osoba dostaje je na
  wyłączność na określony czas … a reszta czeka". The player answers "Miejsce czeka na Ciebie do 14:30" with
  "Biorę" or "Nie tym razem". It is an exclusive offer, never a booking. Flag `class-waitlist-queue`, extract §A —
  read 2026-10-20
- **[POLICY] Playtomic, MATCHi, Eversports**: no waitlist that enrols anyone.
  - Playtomic and MATCHi: [`../areas/LEAVE.md`](../areas/LEAVE.md) §11.
  - Eversports: a waitlisted customer "must complete the booking themselves", and staff cannot move them in
    ([Eversports Manager: How to use the waiting list](https://helpcenter.eversportsmanager.com/how-to-use-the-waiting-list),
    through a search engine's extract) — read 2026-10-20.

*Reading:*

- Booking a waiting player and charging their saved card, with no tap from them, is an established pattern:
  - CourtReserve does it for racquet-club events;
  - Pike13, Zenamu and bsport do it for classes.
- Every one of them stops doing it a set time before the start: CourtReserve's example is 8 h.
- CourtReserve keeps the booking when the charge fails and leaves the player owing.
- In padel itself, and in Kraków, nobody does it: Playmore tells everyone at once, or offers the seat to one person
  for a while.

The player and club sides of R-LEAVE-35 can now be graded against these facts, not left at "untested".

---

### R-LEAVE-54 — Rivals give clubs their own Stripe Dashboard, and some send refunds there; whether a Kraków desk acts in it is still a club question

**A Kraków rival puts the club's own Stripe account behind every payment.**

- **[MEASURED] Playmore**, the system Kraków's squash clubs run on
  (`platforms.md#kraków-squash-clubs-sit-on-playmorereservise`), connects each club's **own** Stripe account. The club signs in with Stripe and authorises Playmore:
  - "Kliknij „Połącz ze Stripe” — przeniesiemy Cię na bezpieczną stronę logowania Stripe."
  - "Zaloguj się swoim kontem Stripe i autoryzuj dostęp dla Playmore."
  - "Wypłaty idą prosto na Twoje konto Stripe."
  - "Po zmianie konta wcześniejsze płatności i ich zwroty zostają na poprzednim koncie."
  - When Stripe won't let the account take payments yet: "Sprawdź w panelu Stripe, czego brakuje, i połącz konto
    ponownie."

  `venue-settings-OPJNS5u4.js`, `growth-CeB9gCIc.js`, extract §B — read 2026-10-20.

  *Reading:* a club that signs in with its own Stripe account keeps its own full Stripe Dashboard. Playmore's desk
  can therefore see, take or refund any of its payments there.
- **[MEASURED]** Playmore tells the desk, on each refund Playmore makes, that nothing is left to do: "Pieniądze zejdą
  z salda klubu w Stripe. Z tą kwotą recepcja nie musi nic robić." No string in the panel warns the desk off acting in
  Stripe itself.
  - Searched every Stripe mention in the panel's 482 files.
  - `calendar-DawkByxO.js`, extract §B — read 2026-10-20.
- **[MEASURED]** When an online payment went straight to the club's own account (not through Playmore), the **desk
  refunds by hand**: "zwrot robi klub — przelewem albo na miejscu. Playmore go nie zleca. Klient widzi w aplikacji, że
  o zwrot ma się zgłosić do recepcji." The player is told "Zwrot {amount} realizuje klub … W sprawie zwrotu skontaktuj
  się z recepcją".
  - `calendar-DawkByxO.js`, `reports-Ct22FugR.js`, `CuTXkj_H.js`, extract §A/§B — read 2026-10-20.

  *Reading:* Polish desks already move money by hand outside the booking system, by bank transfer or at the desk.

**The other platforms.**

- **[POLICY] Playtomic**: clubs hold Stripe connected accounts and log in to Stripe Express.
  - "all online transactions, including payments and refunds, can be viewed directly in your Stripe Connected account"
    ([New Billing Model](https://helpmanager.playtomic.com/hc/en-gb/articles/26436916409361-Introducing-Playtomic-s-New-Billing-Model),
    updated 2026-10-19).
  - Clubs "log in to your Stripe account … Stripe Express dashboard"
    ([Update your personal details in Stripe](https://helpmanager.playtomic.com/hc/en-gb/articles/20534135185937-How-to-update-your-personal-details-in-Stripe),
    updated 2026-10-19).
  - Some refunds are the club's to make by hand, outside Manager:
    - "online payments cannot be refunded through the system. The club must issue refunds manually"
      ([Monthly online payments for courses](https://helpmanager.playtomic.com/hc/en-gb/articles/20534196278929-Monthly-online-payments-for-courses),
      updated 2026-10-14);
    - a share wrongly charged to the owner "it is the club's responsibility, not Playtomic's, to refund"
      ([Split payment statuses](https://helpmanager.playtomic.com/hc/en-gb/articles/50423411876881-Split-payment-bookings-statuses-and-charges-in-Playtomic-Manager),
      updated 2026-10-19).
  - All read 2026-10-20.
- **[DOCS] Stripe**: in the Express Dashboard, "When Stripe is responsible for negative balances on your connected
  accounts, we require some features, such as **View payments**, **Issue refunds**, **Manage disputes** … and don't
  permit disabling them." [Stripe: Express Dashboard](https://docs.stripe.com/connect/express-dashboard) — read
  2026-10-20 (page served in Spanish chrome, English text).

  *Reading:* even a Playtomic club on Express can refund from its own Dashboard. No Express feature to capture a held
  payment is listed.
- **[POLICY] Padel Mates**, release of 2026-04-02: "Clubs can now handle payouts and refunds directly through Stripe —
  faster and more secure." [Padel Mates web strings](https://padelmates.se/locales/en/translation.json) (`rel.4`) —
  read 2026-10-20
- **[POLICY] Booking platforms in other trades** both send venues to the Dashboard and forbid it:
  - **ResDiary**: refunds can't be made in the diary, so "you'll need to action them within your Stripe dashboard",
    and the refund doesn't show in ResDiary
    ([ResDiary: Issue a refund from your Stripe dashboard](https://help-resdiary.theaccessgroup.com/en/articles/12044039-issue-a-refund-from-your-stripe-dashboard)).
  - **Now Book It**: "All refunds … must be processed through Stripe, not Now Book It"
    ([Now Book It](https://help.nowbookit.com/stripe-how-to-issue-a-refund)).
  - **Qondor** forbids it: refunds must be done in Qondor, "Not from the payment service provider"
    ([Qondor](https://help.qondor.com/en/articles/3532308)).
  - All through a search engine's extracts, read 2026-10-20.

**Still not found.**

- **[ABSENT]** Whether a Kraków desk opens its Stripe Dashboard and takes or refunds a payment there by hand.
  - The clubs' terms (Squash4You, Atras, Miazga, Garden Padel, read 2026-10-20) say nothing about how a desk handles
    an online payment.
  - Playmore's panel never mentions it.
  - This stays a question for a club (`questions.md`).

---

### R-LEAVE-32 — What a club expects when a call-off reaches a game already under way: not found

- **[ABSENT]** No club, platform or Kraków club's terms say what should happen when an automatic call-off runs after
  the hour has begun. Searched:
  - Playmore's player app and club panel (2,191 script files);
  - Playtomic's 254 help articles;
  - the four Kraków club terms;
  - CourtReserve, KUYY and Playbypoint help pages.

  All read 2026-10-20.
- **[MEASURED] Playmore** settings:
  - The club sets the automatic call-off in hours before the start: "Jeśli na tyle godzin przed startem nie zbierze
    się komplet, gra zostanie automatycznie anulowana, a wpisowe zwrócone. Zakres 1–48."
  - The free leave must last at least as long as that window.
  - A started game cannot be cancelled at all (`OPEN_GAME_ALREADY_STARTED`,
    `gaps-LEAVE.md#no-platform-calls-a-game-off-once-it-has-started-refunds-after-the-hour-do-exist`).
  - `venue-settings-OPJNS5u4.js`, extract §B — read 2026-10-20.
- **[MEASURED]** Playmore's only cancellation that runs **after** the court hour is for league matches, and it moves
  no money: "Po upływie tego czasu od końca zarezerwowanego terminu kortu, mecz bez wprowadzonego wyniku zostaje
  automatycznie anulowany." Panel bundle `leagues-DD2GnELF.js` — read 2026-10-20
- **[POLICY] KUYY** (activity platform): the minimum-players check "dimulai saat batas waktu tiba dan diulang
  kira-kira tiap 5 menit sampai acara dibatalkan". Whether it stops at the start is not stated.
  [KUYY FAQ](https://kuyy.id/faq/reschedule-pembatalan) — read 2026-10-20

*Reading:* every system found decides before the start. The clubs' terms make a booked hour owed once it begins
(`gaps-LEAVE.md#kraków-clubs-bill-the-booker-the-one-who-came-is-not-singled-out`). Nothing published says a club
would accept a refund for an hour already being played.

---

### R-LEAVE-8 — Playmore tells a late leaver what comes back if the game falls through, never whether the seat was taken

- **[MEASURED] At the press**, a leaver of a game that is not full, after the free window, is told the entry is lost
  for now and comes back only if the game falls through:
  - "Termin bezpłatnego wypisania minął, więc wpisowe na razie przepada. Jeśli gra nie zbierze składu albo odwoła ją
    klub, całe wpisowe wróci do Ciebie." (`CuTXkj_H.js`)
  - On the organiser's sheet: "wpisowe za Twoje miejsce wróci tylko wtedy, gdy gra się nie odbędzie."
  - That line shows only while the game is short: `lateLeaveRefund` and `count < limit` (`BXfZGVTf.js`, `P(e)`).
  - Leaving a full game late shows instead: "Termin bezpłatnego odwołania minął — za Twoje miejsce nic nie wróci."
    (`C9ye8j_u.js`, `CvcDIatB.js`)
  - Extract §A — read 2026-10-20
- **[MEASURED] After the press** the card is the same one every cancelled paid booking gets.
  - It is drawn from the server's `cancellation_refund.destination`: `wallet`, `club_refund`, `carnet`,
    `carnet_entry`, `pending`, `none` or `venue` (`DNDBLHel.js`).
  - It is shown only to the booking's owner (`BcrPl5q_.js`).
  - The card that fits an open game's late leaver is `pending`: "Rozliczymy to po terminie gry … Rozliczenie idzie w
    nocy po terminie rezerwacji — wtedy zobaczysz wynik w portfelu."
  - Otherwise it is `none`: "Odwołanie po terminie — opłata zostaje w klubie".
  - Which one the server sends for an open-game seat is not visible from the client.
  - Extract §A — read 2026-10-20
- **[ABSENT]** No player string announces that the leaver's seat was taken, or was not.
  - Searched the player bundles for "zajął", "zajmie", "Twoje miejsce", "dosadz", "zastęp", "odsprzed" — read
    2026-10-20.
  - At Playmore the leaver's money depends on whether the game takes place, not on whether someone takes the seat.
  - After the cut-off the line-up is closed ("Skład tej gry jest już zamknięty."), so no one can take it.
- **[MEASURED]** Playmore's server does record a taken seat, and only the club sees it. Among the reasons a booking
  can be cancelled automatically is `og_seat_resold`. The desk reads it in the booking's history as "miejsce w grze
  otwartej zostało odsprzedane".
  - Club panel `calendar-views-D40b467p.js` and `calendar-DawkByxO.js`, extract §B — read 2026-10-20.
  - *Reading:* the seat being resold is an event in Playmore's records. It is shown to the club, and the player's app
    holds no words for it.
- **[ABSENT] Padel Mates**: still no string telling a leaver that nobody took the spot before the start.
  - Re-read its web strings on 2026-10-20 for "replac", "no one", "nobody", "taken", "removed".
  - Only the offer at the press stands: "If someone joins using this link, you will be automatically removed from the
    activity and receive a refund within …" (extract §D).
  - The earlier reading stands: `gaps-LEAVE.md#padel-mates-keeps-the-late-leaver-in-the-game-until-a-replacement-joins`.

---

### R-LEAVE-38 — Playmore lets a confirmed game go ahead short and refunds nobody; one venue makes the leaver pay for all

- **[MEASURED] Playmore**, a game confirmed at its cut-off:
  - The players read "Gra się odbędzie. Do zobaczenia na korcie!" and "{count}/{limit} · skład potwierdzony".
  - The line-up is closed ("Skład tej gry jest już zamknięty.").
  - It has no *Join* and no waitlist ("potwierdzona po cut-offie nie ma „Dołącz”, więc nie ma też listy").
  - The call-off rule covers only the time before confirmation: "Gracie, jeśli do potwierdzenia nikt się nie wypisze.
    Gdy ktoś się wypisze i nikt nie zajmie jego miejsca, odwołamy grę".
  - `C9ye8j_u.js`, `BlUiZcxz.js`, extract §A — read 2026-10-20
- **[MEASURED]** The club panel says why the free leave must last at least as long as the call-off window: "Dzięki
  temu nikt nie wypisze się bezpłatnie z gry, którą Playmore już potwierdził, a klub nie dopłaca za zwolnione
  miejsce." `venue-settings-OPJNS5u4.js`, extract §B — read 2026-10-20
- **[ABSENT]** No Playmore string calls off a confirmed game, or refunds the players left in it.
  - It offers the organiser only "Gra ma komplet, a termin bezpłatnego odwołania minął — nie odwołasz jej już
    wszystkim, bo reszta składu na nią liczy. Możesz się wypisać."
- *Reading:* at Playmore a confirmed game that loses players goes ahead with whoever is left. The leaver's entry stays
  with the club. Nobody left in the game gets anything back, even if only one remains. This closes the earlier
  `[ABSENT]` in `gaps-LEAVE.md#playmore-calls-a-game-off-for-everyone-when-a-seat-is-still-empty-at-its-cut-off`.
- **[POLICY] DiR padel clubs** (Barcelona), the one written venue rule found:
  - "When there is a last-minute cancellation in a game of four (4) players, the responsibility for finding a
    replacement will fall on the user who caused the cancellation" (a "switch" link is provided).
  - "If a replacement cannot be found and three (3) players are left unable to play", the leaver must justify it
    within 48 h. If they don't, "the player must pay the total amount of the game … and the amounts will be refunded
    to the rest of the group members".
  - Incomplete games are cancelled automatically 60 minutes before the start.
  - [DiR: Terms of use, padel](https://www.dir.cat/themes/custom/dir/AvisLegal/Padel/NORMATIVA_US_PADEL_EN.pdf),
    §3 and §7.1 — read 2026-10-20
- **[ABSENT]** What a Kraków desk does in practice for the one player who came.
  - The terms bill the booker, as before
    (`gaps-LEAVE.md#kraków-clubs-bill-the-booker-the-one-who-came-is-not-singled-out`).
  - Squash4You, Atras, Miazga and Garden Padel were re-read 2026-10-20, with no change.

---

### R-LEAVE-36 — What a Kraków club gives a group member who left before the club cancels: not found

- **[ABSENT]** None of the Kraków club terms speaks of a group member who is not the booker.
  - Re-read 2026-10-20: Squash4You, Atras, Miazga, Garden Padel.
  - kluby.org's split-payment terms send every refund question to the club: "rozliczenia transakcji, w tym zakresu
    świadczonej usługi, jej ceny, zwrotów, anulacji … należy kierować do podmiotu sprzedającego usługę (klubu)".
    [kluby.org: karty płatnicze §6](https://kluby.org/regulamin/karty-platnicze) — read 2026-10-20
- The platform answers stand: Playmore gives a late leaver the entry back when the club cancels, and a timely leaver
  already had it (`gaps-LEAVE.md#playmore-gives-a-late-leaver-the-entry-back-when-the-club-cancels-a-timely-leaver-already-had-it`).
  The current text confirms it: "Jeśli gra nie zbierze składu albo odwoła ją klub, całe wpisowe wróci do Ciebie"
  (extract §A, read 2026-10-20).

---

### R-LEAVE-25 — Playmore sends the desk nothing when a short open game is called off; its calendar marks it

- **[MEASURED]** Playmore tells clubs the desk takes no part in open games:
  - "Gry otwarte tworzą wyłącznie gracze w aplikacji — recepcja niczego nie obsługuje."
  - "Brak kompletu przed startem = automatyczna anulacja, pełne zwroty i wolny kort."
  - The desk only "przegląda i w razie potrzeby anuluje z grafiku".
  - `open-games-CtT_Xj4X.js`, `venue-settings-OPJNS5u4.js`, extract §B — read 2026-10-20
- **[MEASURED]** The panel lists every message it sends. The ones that "Nie trafiają do klienta — idą na numer lub
  adres recepcji" cover:
  - a trainer booking cancelled (SMS to the trainer and the desk);
  - a group class left with no participant (SMS to the desk);
  - course sign-ups ending, and course resignations (email to the desk).

  **None covers an open game called off.**
- **[MEASURED]** What the club does get:
  - the cancelled booking in its calendar, marked "Anulowane automatycznie przez system";
  - the hour back on its grid;
  - a webhook it can subscribe to, `open_game.cancelled` ("Gra otwarta odwołana"), for "Zapier, n8n lub własnym
    serwerem".
  - `calendar-DawkByxO.js`, `venue-settings-OPJNS5u4.js`, extract §B — read 2026-10-20
- Unchanged from the earlier round:
  - MATCHi emails the venue for system cancellations;
  - Playtomic documents no club notice (`gaps-LEAVE.md#r-leave-25-telling-the-club-of-an-automatic-call-off`).
  - Playtomic's 160 club articles were re-read 2026-10-20 ("automatically cancel", "Anemone", "notif"), with no change.

---

### R-LEAVE-3 — Playmore's leave press carries no cost to check; its reschedule press does, and is refused when the fee moved

- **[MEASURED] Leave.**
  - The request is `DELETE /reservation/{id}`, with one optional parameter, `split_liable` (`DKpNMi8e.js`,
    `BcrPl5q_.js`).
  - No quoted cost or "late" flag goes with it, so the server has nothing to compare the press against.
  - Extract §A — read 2026-10-20
- **[MEASURED] Cancel for everyone.** The organiser's request sends `confirmedPlayers`, the number the dialog showed
  ("Tak, odwołaj grę {n} graczom"). Playmore's notes say only that the count "jedzie do ligi", and they measure
  cancels sent without it. No refusal for a changed count appears among the client's error codes. `DKpNMi8e.js`,
  `BlUiZcxz.js` — read 2026-10-20
- **[MEASURED] Cancel for everyone, after the line.** The server decides at the press. When a game has become full
  and late while the organiser's sheet still offered "Odwołaj grę wszystkim", it refuses with
  `OPEN_GAME_LATE_FULL_LEAVE_ONLY`. The phone then shows "Pełnej gry po terminie bezpłatnego odwołania nie odwołasz już
  wszystkim. Możesz się z niej wypisać — odwołaj swoją rezerwację, a organizację przejmie kolejna osoba ze składu."
  (`CWQZrcVT.js` error map, `C9ye8j_u.js`) — read 2026-10-20
- **[MEASURED] Reschedule.** The press does carry the quoted fee, and the server refuses a stale one:
  `OPEN_GAME_RESCHEDULE_FEE_CHANGED` → "feeChanged" (`CvcDIatB.js`) — read 2026-10-20
- **[ABSENT]** Whether the server refuses a leave whose dialog went stale is still untried by hand: no account or
  booking was used. *Reading:* nothing the leave request carries would let it.
  - Playmore's server checks the line again at the press where the *choice* changes: cancel-for-all becomes
    leave-only.
  - It returns no quoted cost for a plain leave. The outcome card after the press follows the server
    (`gaps-LEAVE.md#playmore-works-out-the-free-window-on-the-phone-when-the-screen-loads-and-the-server-decides-at-the-press`).

---

### R-LEAVE-14 — Whether a Kraków club lets a late canceller book the same hour back: not found

- **[ABSENT]** Re-read 2026-10-20 for "przywr", "ponown", "cofn", "ten sam termin", and found nothing on a late
  canceller booking their own hour back:
  - Squash4You, Atras, Miazga and Garden Padel terms;
  - kluby.org's terms.

  The waivers all name *another* client or player:
  - "przez innego klienta" (Atras);
  - "przez innego gracza" (Miazga);
  - Squash4You sells it "w trybie warunkowym".
- **[MEASURED]** Playmore's club panel has one related option, under "Blokowanie użytkowników z zaległościami":
  "Gracz nie zarezerwuje w aplikacji, jeśli ma nieopłaconą, późno odwołaną rezerwację." Where a club switches it on,
  a late canceller with the fee still unpaid cannot book anything in the app until it is paid.
  `venue-settings-OPJNS5u4.js` — read 2026-10-20

---

### R-LEAVE-4 — What a joiner of a Kraków chat-arranged game owes: not found; one venue's written rule abroad

- **[ABSENT]** Re-searched 2026-10-20 in Polish and English ("zasady wypisania z gry", "kto płaci za kort", Reddit
  padel etiquette). No Kraków group's own rule was found; Facebook groups and WhatsApp communities are closed.
- **[POLICY]** The nearest written rule is a venue's, not a group's. DiR (Barcelona) puts the replacement on the
  leaver, and makes an unjustified leaver pay the whole court while the others are refunded (see R-LEAVE-38 above).
- The Kraków league rule stands: a no-show owes the full court fee
  (`gaps-LEAVE.md#the-one-written-kraków-rule-covers-a-no-show-only`).

---

### R-PAY-4 — Poles with no card they would use online: at most 13,3 % hold no card at all; the exact share is still unmeasured

- **[DOCS] NBP 2023** (the central bank's survey, people aged 15+):
  - "Posiadanie karty płatniczej zadeklarowało 86,7% badanych." So 13,3 % hold no card at all.
  - The most common reason is having no bank account (49 %). Fear of losing control of spending follows (33,2 %),
    then fear of card misuse (27,5 %).
  - In the survey's diary of remote payments (285 transactions, mostly e-commerce), BLIK took 49,7 % by number and
    cards 25 %.

  [NBP: Zwyczaje płatnicze w Polsce w 2023 r.](https://static.nbp.pl/systemy/platniczy/Zwyczaje-platnicze-w-Polsce-2023.pdf),
  synthesis p. 6 and §2.2.1 — read 2026-10-20
- **[DOCS] Gemius, E-commerce in Poland 2025**, as Przelewy24 quotes it: "BLIK – 72%", "Fast transfer (Przelewy24,
  PayU, etc.) – 64%", "Card – 43%" of online shoppers.
  [Przelewy24: Gemius E-commerce 2025](https://www.przelewy24.pl/en/news/ecommerce-2025-zakupy-online-trendy-polscy-konsumenci)
  (2025-09-26) — read 2026-10-20. The 2024 edition: card 43 %, as quoted by
  [weblo.pl](https://weblo.pl/?p=1807) — read 2026-10-20.
- **[ABSENT]** The share of online shoppers who hold no card they would use online is still not measured.
  - The NBP 2024 consumer survey (in *Ocena funkcjonowania systemu płatniczego*, I półrocze 2025, p. 91) refused an
    automated read.
- *Reading:* the bound tightens from Findex's "about 19 % used no debit card"
  (`gaps-PAY.md#how-many-poles-use-a-card-at-all-and-pay-online`) to **at most 13,3 % with no card at all** (NBP 2023).
  Online shoppers are likelier to hold one, so the share of Raketa's newcomers who cannot save any card is below that.
  The share who own a card but would rather not use it online is not bounded: 57 % of online shoppers did not pay by
  card in the year.

---

### R-PAY-18 — What a player sees at a rival's cap on adding cards: no rival ships or publishes one

- **[MEASURED] Playtomic Android 6.94.0** (2026-10-20) holds no message for a limit on adding cards.
  - Its only "limit", "maximum" or "too many" strings are about groups, members, search distance and follows.
  - A refused card add can show only the generic messages: "There was an error processing your card -- try again in a
    few seconds", "Invalid card number", and Stripe's own `stripe_card_declined`.
  - Extract §C — read 2026-10-20
- **[MEASURED] Playmore** saves no card, so it has nothing to cap
  (`gaps-PAY.md#playmore-saves-no-card-so-there-is-nothing-to-remove`).
- **[ABSENT]** kluby.org's terms (§4–5) and app listing say nothing of a limit. The account pages need a login, and the
  app is iOS-only (version 3.56.0). [kluby.org: karty płatnicze](https://kluby.org/regulamin/karty-platnicze),
  [App Store](https://apps.apple.com/pl/app/kluby-org/id1658178253) — read 2026-10-20
- Unchanged: no gateway or competitor publishes a per-card or per-account try cap
  (`gaps-payments-06.md#r-security-13--no-gateway-publishes-a-per-payment-card-try-cap-and-no-kraków-club-card-testing-case-was-found`,
  same round).
- *Reading:* the players side has nothing to compare against. If any rival caps card setups on its server, its
  players meet it as a generic "try again" error.

---

### R-PAY-53 — Neither Playmore's panel nor Playtomic Manager shows a club a refund pending or failed

- **[MEASURED] Playmore club panel.** For an on-time cancellation the booking shows "Automatyczny zwrot przez Stripe:
  {amount}" and: "Playmore zlecił zwrot tą samą drogą, którą klient zapłacił … Pieniądze zejdą z salda klubu w
  Stripe. Z tą kwotą recepcja nie musi nic robić."
  - No string for a refund that is waiting for the club's balance, or has failed. Searched the 482 files for refund
    together with pending, failed, insufficient, "oczekuj", "nieudan", "nie powiódł", "w toku".
  - Where Playmore's server records a refund that failed, the club is not told so. The automatic-cancellation reason
    `court_deleted_refund_failed` is shown to the desk only as "kort został usunięty" (`calendar-views-D40b467p.js`,
    extract §B).
  - The payer, by contrast, is told: "zwrot Twojej wpłaty się nie powiódł. Napisz do nas przez pomoc w aplikacji."
    (`gaps-payments-04.md#r-rescue-47--what-a-player-is-told-when-a-refund-shown-as-made-then-fails-playmore-has-a-state-for-it-matchi-sends-the-player-to-the-club-playtomic-says-nothing`).
  - The player's card shows the refund as ordered ("Zleciliśmy zwrot … Bank księguje go zwykle w ciągu kilku dni
    roboczych") only once it is confirmed. Before that it reads "zwrot przez klub" in muted grey (`DNDBLHel.js`,
    `confirmed`).
  - Extract §A/§B — read 2026-10-20
- **[POLICY] Playtomic Manager.** Payments are split into:
  - *Processed*: "all completed payments, minus any refunds";
  - *Pending*: "transactions still in progress";
  - *Voided*.

  A refunded payment links back to the original
  ([The Payments Section](https://helpmanager.playtomic.com/hc/en-gb/articles/20534669386641-The-Payments-Section),
  updated 2026-10-19).

  A refund never waits for the club's balance. The money is taken back from the next weekly payout, or "withdrawn
  from your bank account", shown as a negative payout and as "Withdrawn" in Stripe
  ([Why did I receive a negative payout?](https://helpmanager.playtomic.com/hc/en-gb/articles/50457368851729-Why-did-I-receive-a-negative-payout),
  updated 2026-10-19).

  Players read that "Playtomic processes the refund immediately"
  ([Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593-Refunds-and-when-you-will-receive-your-money),
  updated 2026-09-10). All read 2026-10-20.
- **[ABSENT]** A failed or stuck refund in Playtomic Manager: no article describes one. Searched all 160 club articles
  for refund near "pending", "fail", "insufficient", "negative balance" — read 2026-10-20.
- **[ABSENT] tenis4U**: its club panel needs a login and no help pages on refunds were found (searched 2026-10-20).
  The status quo the club side is graded on stands: a Przelewy24 refund on a short balance fails at once, with no
  pending state (`local-market.md#refunds-come-out-of-the-clubs-balance`).

*Reading:* both rivals show a club only that a refund was made, never that one is waiting or failed.

- Playtomic can say so because it recovers the money itself.
- Playmore does not say what happens when the club's Stripe balance is short.

---

### R-PAY-42 — Whether Playtomic's transactions stay after the paying card is removed: still not found

- **[MEASURED] Playtomic 6.94.0** still keeps the history as its own list, beside the methods:
  - "Payment methods, transactions, club memberships..."
  - "Transactions", "All transactions", "Payment history"
  - "All transactions you make will be displayed here."

  Removing a method shows "Remove card?" and "Are you sure you want to remove this card?", and for subscriptions
  "This payment method will be removed but will remain available for %s subscriptions." No string says what removal
  does to past transactions. Extract §C — read 2026-10-20
- **[POLICY]** The one further pointer, in Playtomic's US/Canada Card on File article: "You can find a receipt for the
  charge in the app at any time", next to "Remove a card or revoke a club's permission to charge it at any time".
  [Card on File (US and Canada)](https://playerhelp.playtomic.com/hc/en-gb/articles/41522182623505-Card-on-File-Letting-your-Club-charge-your-saved-card-directly-US-and-Canada-only)
  (updated 2026-08-19) — read 2026-10-20. *Reading:* receipts are promised "at any time", not "while the card is
  saved". It is a pointer, not a statement about removal.
- **[ABSENT] kluby.org**: payment history needs a login; the app is iOS-only and its listing says nothing (above) —
  read 2026-10-20.

---

### R-PAY-24 — Whether kluby.org asks before a saved card is removed: still not found

- **[ABSENT]** Nothing public shows the step.
  - The terms say only "Użytkownik może w dowolnym momencie: usunąć zapisaną kartę … Usunięcie karty powoduje
    natychmiastową utratę możliwości obciążenia jej w przyszłości"
    ([kluby.org: karty płatnicze §5](https://kluby.org/regulamin/karty-platnicze)).
  - The public scripts (`/js/script.js`, `/unit/js/slots.js`, `/unit/js/slots.def.js`) hold no card-management code.
  - The account and card pages (`/konto` and the like) redirect signed-out visitors home.
  - The app is iOS-only, version 3.56.0. No Android package exists to read, and the App Store page says nothing about
    cards ([App Store](https://apps.apple.com/pl/app/kluby-org/id1658178253)).
  - All read 2026-10-20.
- Unchanged: Playtomic asks before it removes a card; Playmore saves none
  (`gaps-PAY.md#playtomic-asks-before-it-removes-a-card`). Re-confirmed in Playtomic 6.94.0, extract §C.
