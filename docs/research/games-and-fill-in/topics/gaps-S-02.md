# Gaps round after story S-02

Answers to the facts story S-02 still lacked (`$W/stories/S-02/gaps.md`: R-DECK-41, R-DECK-23, R-RESCUE-41 twice,
R-RESCUE-2, R-RESCUE-1, R-DECK-21, R-RESCUE-9), and to the two rules whose market grade is still `? (provisional)`:
R-PLATFORM-48 and R-NOTIFY-32. For those two, only sources not tried in `gaps-PLATFORM.md`, `gaps-NOTIFY.md` and
`gaps-S-01.md` were tried. Read **2026-10-10**; web search worked throughout. Each `###` heading answers part of one gap
and names what it found, so it can be cited as `topics/gaps-S-02.md#<heading>`.

Sources: Playmore's web app as served on 2026-10-10 (1,419 bundles reachable from playmore.pl, entry
`index-l-ePYLJ-.js`, its feature-flag register `C86-QTBp.js` included); Playtomic's Android 6.93.2 decompile and string
table (the package of 2026-10-08 that the NOTIFY round read; the App Store still lists 6.93.2 on 2026-10-10) and its 94
English player help articles (Zendesk API); WhatsApp for Android 2.26.39.79, read with the Android SDK's own `aapt2`
and `dexdump`; tenis4U's public booking grids for five Kraków padel clubs, read again 20 h 42 min after the S-01 round's
read; Directive (EU) 2019/882 (legislation.gov.uk's copy, EUR-Lex refused an automated read) and Poland's act of 26 April
2024 (Dziennik Ustaw PDF); gov.pl's page on e-commerce under that act; W3C's WCAG notes; Google Search Central; Android
Developers; WhatsApp's help centre; Bruce's help centre; 1,666 recent App Store reviews of Playtomic and Playmore
(eight countries, ten pages each); a padel operator's job ad and a university padel group's code of conduct.

Kinds: `[POLICY]` a rule, help text, review-feed or flag note an operator ships · `[LAW]` · `[DOCS]` a provider's,
platform's or standards body's document · `[MEASURED]` read from the product itself (shipped code, a package, or the
public data its web app shows a visitor; the extract is saved under `../shots/`) · `[COMPLAINT]` one person's account ·
`[ABSENT]` looked for and not found, with where. *Reading* lines are this researcher's inference, not a source.

---

## 1. R-DECK-41, R-DECK-23: an app that shows the same people once, or hides one game because of another

### No racket or game app found that shows the same people once, or hides a game because another holds them
- **[ABSENT]** Playtomic: none of its 94 English player help articles has a rule that hides a match, or shows the same
  players only once; the one "only once" rule is for kudos ("only once per match"). Searched the article bodies for only
  once, same players or people, won't see, not shown, hidden, already in, overlap and at the same time.
  [Playtomic player help](https://playerhelp.playtomic.com/hc/en-gb) (Zendesk API) — read 2026-10-10
- **[ABSENT]** Playmore: the web app served today still lists every open game at a club by day and hour (carried:
  `gaps-DECK.md#playmore-orders-open-games-by-day-and-hour-nothing-puts-nearly-full-games-first`), and no entry in its
  feature-flag register drops a game because its players are in another. Searched the register and all bundles for
  duplikat, dedup, "ten sam skład", "tych samych graczy", and ukryw / chowa / pomija next to gry, karta or skład.
  [C86-QTBp.js](https://playmore.pl/assets/C86-QTBp.js) — read 2026-10-10
- **[ABSENT]** WhatsApp groups, the status quo, show every post to every member (carried:
  `platforms.md#whatsapp-groups-polls-events-and-1024-members`).

### Playmore steers a repeat of the same four to the game already made, and never hides it
- **[POLICY]** Playmore's rematch, "Rewanż za tydzień" (flag `open-game-rematch`, added 2026-09-28): if a rematch of the
  game already exists, the button opens the club's game list at that game ("Rewanż już jest: … Dołącz") instead of making
  a second; otherwise the creator opens with the first game's settings and, once the new game is paid, the previous
  line-up is invited ("{Imię} zaprasza na rewanż", a push without SMS). The team's reason, in its note: a joiner becomes
  a creator in 11 % of cases (4 of 38), and only 2 pairs have played two or more confirmed games together.
  [C86-QTBp.js](https://playmore.pl/assets/C86-QTBp.js) — read 2026-10-10
- *Reading:* the nearest market move to a once-only rule keeps one game per line-up by sending its creator to the game
  that exists; that game stays listed for everybody.

### Search engines thin out repeats from one source, and say so
- **[DOCS]** Google: "Our site diversity system works so that we generally won't show more than two web page listings
  from the same site" in its top results; among near-identical pages, "our systems show only the most relevant results
  to avoid unhelpful duplication". [Google Search Central: A guide to Google Search ranking systems](https://developers.google.com/search/docs/appearance/ranking-systems-guide)
  (updated 2025-12-10) — read 2026-10-10
- *Reading:* the only documented rule found that shows one source once or twice and drops the rest of its items is
  outside sport, in a results list the reader scrolls. None found drops an item that names the reader, or one that other
  people have already said yes to.

---

## 2. R-RESCUE-41: how rivals' seat counts and badges are read out by VoiceOver and TalkBack

### Playmore reads its seat meter as players of the limit and players missing
- **[MEASURED]** The open-game card's seat meter is an image whose spoken label is "{count} z {limit} graczy, brakuje
  {missing}" ("2 z 4 graczy, brakuje 2"), or "{count} z {limit} graczy, komplet" when full; English "2 of 4 players, 2
  missing". The visible line "2/4 · brakuje 2 graczy" is hidden from screen readers (`aria-hidden`), so the count is
  heard once. The "Ostatnie miejsce" chip is not hidden. Component `OpenGameSeatsMeter`
  [mFrbX9po.js](https://playmore.pl/assets/mFrbX9po.js), strings [E4x38PLO.js](https://playmore.pl/assets/E4x38PLO.js);
  extract [`../shots/gaps-S-02-playmore-playtomic-spoken-labels.txt`](../shots/gaps-S-02-playmore-playtomic-spoken-labels.txt) — read 2026-10-10
- *Reading:* Playmore speaks a count per game, in players, the same unit the card shows.

### Playmore reads a tab badge and the bell with their full number and what it counts
- **[MEASURED]** A bottom tab with a badge is read as "{tab}, nieopłacone rezerwacje: {count}" (unpaid bookings); the
  visible badge, which stops at "9+", is hidden from screen readers. The bell is read as "Skrzynka powiadomień,
  nieprzeczytane: {count}" and re-reads its count every 30 s. `BottomTabItem` in
  [index-l-ePYLJ-.js](https://playmore.pl/assets/index-l-ePYLJ-.js), the bell in [CZeoPNe3.js](https://playmore.pl/assets/CZeoPNe3.js),
  strings [ntkaKkR_.js](https://playmore.pl/assets/ntkaKkR_.js); same extract — read 2026-10-10

### Playtomic's tab badge is a bare number that the tab's spoken label leaves out
- **[MEASURED]** Playtomic's Android app draws a tab's badge as its own small text view inside the tab and gives it no
  spoken label; the tab's spoken label is its title. The Material library it ships adds a count to a tab's label only for
  Material's own badge type, which Playtomic does not use. Its string table holds three spoken labels of its own (back,
  close, an illustration), none for a count. Classes `TabBarNavigationManager`, `Badge` and Material's
  `NavigationBarItemView` in the 6.93.2 decompile; same extract — read 2026-10-10
- *Reading:* TalkBack most likely says the tab's name without its number; not checked on a phone, and Playtomic's iPhone
  app was not read.
- **[MEASURED]** The match card's seat line is plain text, heard as written: "Hurry up! Only %1$s place/s available",
  "%1$s places left to confirm the match". Playtomic Android 6.93.2 string table — read 2026-10-10

### No screen-reader complaint and no accessibility statement found for either app
- **[ABSENT]** 1,666 recent App Store review entries of Playtomic and Playmore (Poland, Spain, Britain, Italy, France, Sweden,
  the Netherlands and Germany, ten pages each, newest first) name no screen reader (VoiceOver, TalkBack, niewidomy, ciego,
  blind). A search of playtomic.com and playmore.pl found no accessibility statement. Apple's review feeds:
  [Playtomic](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json),
  [Playmore](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortby=mostrecent/json) — read 2026-10-10

---

## 3. R-RESCUE-41: whether the European Accessibility Act and Poland's act reach a booking app's spoken labels

### The EU act covers e-commerce services, their websites and mobile apps included, since 28 June 2025
- **[LAW]** Directive (EU) 2019/882 applies "to the following services provided to consumers after 28 June 2025", among
  them "(f) e-commerce services" (Art. 2(2)). These are "services provided at a distance, through websites and mobile
  device-based services by electronic means and at the individual request of a consumer with a view to concluding a
  consumer contract" (Art. 3(30)). Every covered service must make "websites, including the related online
  applications, and mobile device-based services, including mobile applications, accessible in a consistent and adequate
  way by making them perceivable, operable, understandable and robust" (Annex I, Section III(c)); e-commerce adds
  accessible identification, security and payment functions (Section IV(g)).
  [Directive (EU) 2019/882, legislation.gov.uk's copy: Art. 2](https://www.legislation.gov.uk/eudr/2019/882/article/2),
  [Art. 3](https://www.legislation.gov.uk/eudr/2019/882/article/3), [Annex I](https://www.legislation.gov.uk/eudr/2019/882/annex/I) — read 2026-10-10

### Microenterprises that provide services are exempt, in the EU act and in Poland's
- **[LAW]** "Microenterprises providing services shall be exempt from complying with the accessibility requirements"
  (Art. 4(5)); a microenterprise "employs fewer than 10 persons and … has an annual turnover not exceeding EUR 2 million or
  an annual balance sheet total not exceeding EUR 2 million" (Art. 3(23)).
  [Art. 4](https://www.legislation.gov.uk/eudr/2019/882/article/4), [Art. 3](https://www.legislation.gov.uk/eudr/2019/882/article/3) — read 2026-10-10
- **[LAW]** Poland: "Przepisów ustawy nie stosuje się do: 1) usług oferowanych lub świadczonych przez
  mikroprzedsiębiorców" (art. 4). [Ustawa z dnia 26 kwietnia 2024 r. o zapewnianiu spełniania wymagań dostępności niektórych produktów i usług przez podmioty gospodarcze, Dz.U. 2024 poz. 731](https://dziennikustaw.gov.pl/D2024000073101.pdf) — read 2026-10-10

### Poland's act covers e-commerce in the same words and asks for compatibility with assistive tools
- **[LAW]** The act applies to services offered to consumers, among them "6) handlu elektronicznego" (art. 3 ust. 2):
  "usługi oferowane lub świadczone na odległość przez strony internetowe i urządzenia mobilne, drogą elektroniczną i na
  indywidualne żądanie konsumenta w celu zawarcia umowy" (art. 5 pkt 32). A service must ensure "jednolitość stron
  internetowych i aplikacji mobilnych przez zapewnienie ich postrzegalności, funkcjonalności, zrozumiałości i
  kompatybilności" (art. 12 ust. 2 pkt 3), compatibility meaning undisturbed working with other systems, "w tym z
  narzędziami wspomagającymi" (art. 5 pkt 12). In force from 28 June 2025. Meeting a harmonised standard is presumed to
  meet the requirements it covers (art. 20). [Dz.U. 2024 poz. 731](https://dziennikustaw.gov.pl/D2024000073101.pdf) — read 2026-10-10
- **[LAW]** A service provider that does not meet the requirements of art. 12–19 can be fined up to ten times the average
  monthly wage, capped at 10 % of the previous year's turnover (art. 73). Same act — read 2026-10-10
- **[POLICY]** The government's page: e-commerce is "wszelkie formy oferowania i świadczenia usług przez Internet, także
  niewymienionych bezpośrednio w ustawie"; "Minister Cyfryzacji (MC) swoim nadzorem obejmuje usługi handlu
  elektronicznego"; a microenterprise's services are outside the act.
  [gov.pl: Polski Akt o Dostępności — usługi handlu elektronicznego](https://www.gov.pl/web/dostepnosc-cyfrowa/polski-akt-o-dostepnosci--uslugi-handlu-elektronicznego)
  (modified 2025-08-14) — read 2026-10-10

### Neither act sets wording; the usual yardstick asks a spoken name to contain the visible label
- **[ABSENT]** Neither the directive nor the Polish act says how a count, a badge or any spoken label must be worded;
  both set principles (perceivable, understandable, robust, compatible with assistive tools). — read 2026-10-10
- **[DOCS]** WCAG's "Label in Name" (level A): "the name contains the text that is presented visually"; screen-reader
  users "will also have a better experience if the text they hear matches the text they see on the screen".
  [W3C: Understanding SC 2.5.3 Label in Name](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html) — read 2026-10-10
- *Reading:* a player app that takes a consumer's payment for a seat is an e-commerce service in both texts, so its spoken
  labels fall under their principles. While the operator is a microenterprise (fewer than 10 people, at most EUR 2
  million a year) the act does not apply and the spoken count is a matter of wording; once the operator outgrows that, a
  spoken count naming a different quantity from the one on screen becomes a compliance question, though no text names it
  a breach. The club website serves clubs, not consumers, and is outside both.

---

## 4. R-RESCUE-2: how often a Kraków club resells an hour handed back a day ahead, a weekend morning in particular

### A day before a weekend morning, most clubs' indoor doubles courts are already taken
- **[MEASURED]** At 05:02 on Saturday 10 October 2026, tenis4U's public grids for five Kraków padel clubs showed 30.5 of
  66 sellable court-hours of Sunday morning (opening to 12:00) taken, 46 %, and 34.5 of 72 of Saturday morning, 48 %.
  Sunday morning by club: Padel House 13 of 14, Fame Sport Club 5 of 10, Bajada 9 of 25, PADEL LOUNGE 2 of 5, Garden
  Padel 1.5 of 12. The free Sunday-morning hours sit mostly on outdoor courts (Bajada's two, Fame's one), on Bajada's
  singles court and in Padel Lounge's early hours; at Padel House, Bajada and Fame the indoor doubles courts are taken
  from 08:00 to 12:00, and only Garden Padel has its courts mostly free. A week out, Saturday 17 and Sunday 18 October,
  24 % and 37 % of morning hours were taken. Extract with each court's free hours:
  [`../shots/gaps-S-02-tenis4u-krakow-padel-weekend-2026-10-10.txt`](../shots/gaps-S-02-tenis4u-krakow-padel-weekend-2026-10-10.txt),
  from the endpoints [tenis4U's web app](https://app.tenis4u.pl/) calls for a visitor — read 2026-10-10

### Over the last day, about one free weekend hour in ten was sold
- **[MEASURED]** The same grids read 20 h 42 min apart (9 October 08:20, 10 October 05:02), net of hours handed back:
  Saturday 10 October, from one day ahead to the morning of play, +13.5 court-hours of 142.5 free (9.5 %); Sunday 11,
  from two days to one day ahead, +7 of 135 (5.2 %: +9 at four clubs, −2 at Padel House); a week out, Saturday 17 +1 of 169 and
  Sunday 18 +6 of 155. Same extract, and the first read in
  [`gaps-S-01.md`](gaps-S-01.md#five-kraków-padel-clubs-how-much-of-the-next-two-weeks-weekday-hours-is-already-taken) — read 2026-10-10
- *Reading:* whole days only, since the first read did not split hours by time of day; a morning's own rate is not
  separated.

### Hours handed back at the busiest club were still unsold the next morning
- **[MEASURED]** At Padel House, where every weekday evening hour two weeks out was taken on 9 October, court 3 had
  17:00–20:00 on Monday 12 October free on 10 October: three evening court-hours handed back between the reads, two and a
  half days before play, and not sold again by 05:02. An evening hour on Saturday 10 and one on Sunday 11 were handed
  back too and were still free. Same extract — read 2026-10-10
- *Reading:* even where evenings sell out, hours handed back two or three days ahead had not sold within 21 hours. A
  weekend morning hour handed back a day ahead lands, at four of these five clubs, among free morning hours (mostly
  outdoor or off-peak), and at Padel House in a morning that is almost full.

### A resale rate itself: still not published
- **[ABSENT]** No club, booking system or report gives how often an hour handed back 24 hours ahead is sold again, for
  any time of day. Tried this time: the two reads above, Playmore's flag notes and Playtomic's player help; carried:
  `gaps-RESCUE.md#kraków-desks-resell-a-late-cancelled-hour-nobody-publishes-how-often`,
  `gaps-LEAVE.md#no-platform-or-club-publishes-a-late-fill-or-resale-rate`. A true rate needs reads of each handed-back
  hour from the moment it is handed back until play, or the clubs' own records. — read 2026-10-10

---

## 5. R-RESCUE-1, R-RESCUE-2: how a group says a seat has opened, or that a game is about to be called off

### WhatsApp's own events tell the people going when the creator edits or cancels
- **[POLICY]** As the search engine returned the page (its body would not load directly): "Only event creators can edit
  and cancel events"; members who answered Going, Going with guest or Maybe are notified when the creator edits or
  cancels the event, and a notice of the change is also sent to the chat.
  [WhatsApp Help: How to create and edit events in groups](https://faq.whatsapp.com/3313983622238973/) — read 2026-10-10
- **[ABSENT]** Whether anyone is told when a member changes an answer to Not going, the moment a seat opens: not in
  WhatsApp's help on creating or answering events. [WhatsApp Help: How to respond to events](https://faq.whatsapp.com/3855462068110340/)
  (body would not load) — read 2026-10-10

### A player says freed places reach her through the canceller's own post in a WhatsApp group
- **[COMPLAINT]** Playtomic App Store review (Britain, 4 stars, 14 August 2026, app 6.85.0): "You either have to keep
  checking if something has come up or be notified by the person cancelling via a WhatsApp group which in my case is a
  She serves group which means men don't get notified. Waiting lists are much fairer way of dealing with cancellations."
  [Apple's review feed, Playtomic, Britain](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-10

### Kraków group posts: still unreadable
- **[ABSENT]** No Kraków group post could be read. Tried this time: Polish web searches ("grupa whatsapp" padel Kraków,
  "zwolniło się miejsce", szukamy czwartego), a padel operator's community-host job ad (PadelCity, Warsaw, Kraków and
  Kielce: no word on groups), and a university padel WhatsApp community's code of conduct (Cambridge: conduct and phone
  numbers only, no rule on dropping out). [PadelCity job ad](https://pracasport.pl/praca/student-community-host-padelcity-713488),
  [Cambridge University Sport: padel WhatsApp communities](https://www.sport.cam.ac.uk/padel/padel-whatsapp-communities) — read 2026-10-10

---

## 6. R-DECK-21, R-RESCUE-9: whether a few offers per seat refill a court faster than telling everyone at once

### Bruce alerts its waitlist in 20-second waves, in no order, to fill short-notice places fast
- **[POLICY]** Bruce, a class-booking app: when a place opens, notifications go out "at 20-second intervals", "in no
  particular order"; "The first person to book the spot gets it"; "This approach is designed to quickly fill spots that
  often become available on short notice." [Bruce help: Waitlist](https://help.bruce.app/en/articles/10166414-waitlist)
  (dated 2024-12-13) — read 2026-10-10
- *Reading:* a staggered alert chosen for speed, as Raketa's three cards come before the open board, but with no figure
  behind the choice.

### Playmore tells its whole waitlist at once and will judge it by the share refilled, not against another order
- **[POLICY]** Playmore's line to players: "Gdy zwolni się miejsce, powiadomimy wszystkich z listy naraz — kto pierwszy,
  ten gra." (no place in a queue). Live at three clubs and a test club since 27 September 2026, and at every club with
  open games from 10 October; it stays if "dosadzenia zwolnionych miejsc ≥ 50% (n ≥ 6)" at the review of 22 December, with a first read
  due 23 October. [C86-QTBp.js](https://playmore.pl/assets/C86-QTBp.js) (flag `open-game-waitlist`) — read 2026-10-10

### A measured comparison of the two orders: not found
- **[ABSENT]** No platform, club or study found reports how fast, or how often, a freed place refills when a few chosen
  people are offered it first, against telling everyone at once. Searched: Bruce's help, Playmore's flag notes, web search
  for studies of in-turn against all-at-once waitlist offers; carried: HelloClub, FitDegree and CourtReserve
  (`gaps-RESCUE.md#nobody-ranks-who-hears-of-a-seat-by-how-even-the-game-would-be`). — read 2026-10-10

---

## 7. R-PLATFORM-48: whether an answer held offline survives the app being closed (sources not tried before)

Tried before: WhatsApp's help centre, its 2017 press coverage, troubleshooting explainers, forensic write-ups, Reddit and
phone forums and an Apple engineer's forum answer (`gaps-S-01.md` §9); Playmore's code and Playtomic's strings
(`gaps-PLATFORM.md` §1). New this time: WhatsApp's Android package and Android's own documentation.

### WhatsApp's Android app starts work when the phone restarts, a messaging task among it
- **[MEASURED]** WhatsApp for Android 2.26.39.79 asks for `RECEIVE_BOOT_COMPLETED` and registers its own `BootReceiver`
  for the phone's restart. On it, the receiver logs "BootManager; boot completed." and calls a set of start-up observers;
  the package's names include `MessagingBootCompleteObserver`, `NotificationBootCompleteObserver` and
  `EventStartAlarmBootCompletedObserver` ("message store is ready, setting event start alarms"). The observers' own code
  was not read. Extract [`../shots/gaps-S-02-whatsapp-android-2.26.39.79-boot.txt`](../shots/gaps-S-02-whatsapp-android-2.26.39.79-boot.txt)
  (APKPure copy of 2026-10-09) — read 2026-10-10

### Android keeps an app's scheduled work through the app closing and the phone restarting
- **[DOCS]** "WorkManager features a robust scheduling mechanism that lets tasks persist across app restarts and device
  reboots"; it is meant for work that must "run reliably even if the user navigates off a screen, the app exits, or the
  device restarts". [Android Developers: WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager)
  (updated 2026-02-26) — read 2026-10-10

### Whether a clock-marked message leaves before WhatsApp is reopened: still not found
- **[ABSENT]** No statement or test says whether a message waiting behind WhatsApp's clock is sent after the app is
  closed or the phone restarts, before WhatsApp is opened again. — read 2026-10-10
- *Reading:* on Android, WhatsApp has the means to resume its messaging work at restart, which makes "it still goes" the
  likelier answer there; on an iPhone a swiped-away app is not woken until reopened (carried,
  `gaps-S-01.md#an-iphone-app-the-user-swiped-away-is-not-woken-until-it-is-opened-again`). **Only a dated device test
  settles it.**

---

## 8. R-NOTIFY-32: priority, expiry and time-sensitive level of rivals' pushes (sources not tried before)

Tried before: Playtomic's Android channels and push receiver, Playmore's Android source maps, Firebase's and Braze's
documentation (`gaps-NOTIFY.md`, `gaps-S-01.md` §8). New this time: Playmore's web app and flag notes as served today,
and App Store reviews.

### Playmore's shipped code and flag notes say nothing of push priority, expiry or time-sensitive delivery
- **[ABSENT]** Searched today's 1,419 bundles for time-sensitive, interruption level, apns priority and Android channel
  ids, and the flag register for those and for TTL, time to live and priority next to push; the only lifetime found
  belongs to a join from a shared link kept pending (30 or 120 minutes). [C86-QTBp.js](https://playmore.pl/assets/C86-QTBp.js) — read 2026-10-10

### Reviews tell of alerts that never come, not of alerts that come late
- **[COMPLAINT]** Playmore (Poland, 2 stars, 20 July 2026, app 6.10.13): "Powiadomienie o zwolnieniu kortu - niby jest
  włączone, a nigdy nie przychodzi"; another (Poland, 2 stars, 20 May 2025) says the freed-court alert stopped arriving
  months earlier. Playtomic (Spain, 3 stars, 10 September 2025): "No me llegan notificaciones cuando mis contactos se unen
  a partidas"; (Italy, 3 stars, 30 June 2025): "Non arriva più notifica di iscrizione ad una partita". Apple's review
  feeds, [Playmore, Poland](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortby=mostrecent/json),
  [Playtomic, Spain](https://itunes.apple.com/es/rss/customerreviews/page=5/id=1242321076/sortby=mostrecent/json) — read 2026-10-10
- **[ABSENT]** None of the 1,666 reviews read describes a push that arrived hours late, which is how a normal-priority
  push held back by a sleeping phone would show; nothing separates a low priority from an alert never sent. — read 2026-10-10
- *Reading:* still not found. **Only a dated test on a phone, with a real booking or alert, settles it.**
