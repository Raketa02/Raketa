# Gaps for DECK: the Games deck

Answers to the facts the DECK grades asked for and the research lacked (`areas/DECK/gaps.md` of
PRD #530). Read 2026-10-08. One `##` section per gap, every fact under a `###` heading. The two gaps
holding a provisional grade (R-DECK-38, R-DECK-22) come first.

**Sources.**
- **Playmore:** interface text and screen logic come from the JavaScript its web app serves to every
  visitor (`playmore.pl/assets/*.js`, 1,367 chunks crawled from the 8 Oct 2026 build and read by grep).
  File names are content hashes and change with each release, so each fact quotes enough text to
  find it again. The open-games page is now `DM7ksFDa.js`, which replaces `DGQrxHKX.js` cited by
  earlier files; the old file is still served.
- **Playtomic:** help articles come from its public Zendesk API (94 player articles in English, 99 in
  Spanish, 157 club articles). Interface strings come from the Android app 6.93.2 (XAPK from APKPure,
  default-locale `resources.arsc`). The lines used are saved in
  `shots/gaps-DECK-playtomic-android-6.93.2-strings.txt`, and the help images in `shots/gaps-DECK-*.png`.
- **Law:** EUR-Lex and the Sejm's ELI API.

No screenshot was taken of a live app, so nothing here is `[MEASURED]`.

**Kinds.** `[POLICY]` is the company's own rule, term, help or interface text. `[PRICE]` is a published
price. `[LAW]` is a statute or a court ruling. `[DOCS]` is a regulator's or provider's document.
`[COMPLAINT]` is one person's account. `[ABSENT]` means looked for and not found, with where. Lines
marked *reading* are comparisons, not sources.

---

## R-DECK-38 — how a list of games is kept current

### Playmore reads its open-games list when the page opens and after the player's own actions
- **[POLICY]** *(code)* The club's open-games page (`ReservationOpenGames`) reads the list once when it
  mounts: `Ye(async()=>{… await Qs(i,()=>Promise.all([w(),Da()])) …})`, which is guarded by "Open games
  page initialization failed". It hands the same loader to the create, cancel and leave helpers as
  `reload` ("Open games refresh after a create failed"). The loader has no timer: it reads
  `leaguePublic.openGames(venue, from, until)` and logs "Failed to fetch open games:".
  [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js), [BfBfjPsN.js](https://playmore.pl/assets/BfBfjPsN.js) — read 2026-10-08
- **[POLICY]** *(code)* The only interval on the page is the status strip's clock,
  `setInterval(()=>{s.value=Date.now()},3e4)` in `OpenGameStatusStrip`. It recounts "Zostało {h} godz.
  {m} min" every 30 seconds and re-reads no data.
  [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08

### Playmore's open-games page does not re-read on return and has no pull-to-refresh
- **[POLICY]** *(code)* Playmore has a helper that re-reads a screen when the app comes back to the
  front, at most every 30 s (`[RefetchOnFocus]`, listening to `appStateChange` and
  `visibilitychange`). Each screen opts in by importing it. Home, *My reservations*, payments, passes
  and calendar screens import it. The open-games chunk does not: it imports only another export
  (`K`) of that module. [Cng0yjU9.js](https://playmore.pl/assets/Cng0yjU9.js),
  [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08
- **[POLICY]** *(code)* Pull-to-refresh is a `PullToRefreshContainer`, and the iOS native control
  attaches only while such a container is on screen. Thirteen chunks mount it, among them
  `MarketplaceHomeLayout`, `NotificationsLayout`, `WalletLayout`, passes, `MultiCalendarBoard` and
  standing-slot requests. The open-games chunk is not among them.
  [BB4a-K4G.js](https://playmore.pl/assets/BB4a-K4G.js), [lkex2N-2.js](https://playmore.pl/assets/lkex2N-2.js) — read 2026-10-08
- *Reading:* this narrows `topics/gaps-SWIPE.md#neither-playmore-nor-playtomic-redraws-a-roster-live`,
  which reads the app-wide refresh-on-return and pull-to-refresh as covering open games. They cover
  other screens. On Playmore a player sees new open games only by opening the page again, or after
  their own create, leave or cancel. This agrees with
  `topics/gaps-RESCUE.md#playmore-reads-its-open-games-list-when-the-page-opens-and-after-the-players-own-actions`.

### Playtomic does not document how its match list refreshes; one player says it needs a restart
- **[ABSENT]** How *Find a match* or a match page updates: not in 94 English and 99 Spanish player
  articles (searched "refresh", "real time", "actualiz", "desliza") and not in the Legal Conditions.
  There is no refresh string among the Android strings (searched "refresh", "pull", "reload").
  [Playtomic player help API](https://playerhelp.playtomic.com/api/v2/help_center/en-gb/articles.json) — read 2026-10-08
- **[COMPLAINT]** "Sometimes does not refresh well and needs killing" (NicknameLoading…, App Store GB,
  2024-11-10). On the other side: "La aplicación te informa en todo momento de cualquier actualización
  sobre el partido; nuevos jugadores que se apuntan, si se cierra i se cancela" (Alf748, App Store
  ES, 2023-05-05).
  [App Store GB feed](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortBy=mostRecent/json),
  [App Store ES feed](https://itunes.apple.com/es/rss/customerreviews/page=1/id=1242321076/sortBy=mostRecent/json) — read 2026-10-08
- *Reading:* neither rival changes a list on screen. Rakieta reads the deck again on return to the
  front and after 30 s away, which Playmore's open-games page does not. No rival offers a
  pull-to-refresh that Rakieta lacks on this list.

---

## R-DECK-22 — the order of games in a list, and what a platform must tell clubs about it

### Playmore orders open games by day and hour; nothing puts nearly full games first
- **[POLICY]** *(code)* The feed keeps listable future games sorted by start time:
  `.filter(n=>p(n,r)).sort((n,e)=>a(n.startTime)-a(e.startTime))`. It then groups them by day. Within
  a day, players' games come before trainer games and trainer games before classes (`Or`: game 0,
  trainer 1, class 2), each by start time: `m.items.sort((d,g)=>Or(d)-Or(g)||d.startMs-g.startMs)`.
  No key counts seats left. [Dv8V2l3V.js](https://playmore.pl/assets/Dv8V2l3V.js), [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08
- **[POLICY]** A player can narrow the feed by sport, level and daypart ("feedFilters"), but cannot
  re-sort it. [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08

### Playtomic lets a player sort matches by number of players; the default is Relevance
- **[POLICY]** *Find a match* → *More filters* → "Sort by": "Relevance", "Nearest", "Number of players",
  "More recent". Its sections are "For your level — These matches fit your search and your level
  perfectly"; "Request your place"; "Are you flexible? — These matches are available and are similar
  to your search"; "Playtomic suggestions — Here are some matches that may interest you"; "Be the
  first player!" and "Availability from Playtomic clubs".
  [Android 6.93.2 strings](../shots/gaps-DECK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** What "Relevance" weighs, and whether "Number of players" puts fuller or emptier matches
  first: not in any player or club help article, nor in the Legal Conditions (searched "ranking",
  "relevance", "sort", "order", "parameters"). [Playtomic Legal Conditions](https://playtomic.com/legal-conditions) — read 2026-10-08

### Playtomic's own help image lists a fuller, gold-bordered match before an earlier one
- **[POLICY]** The help article's results image, with the filter "Today", shows under "For your level":
  first "Monday 09 February | 17:00", a gold-bordered card with three seats taken; then "14:30", one
  seat taken; then a "Friendly" card. The later, fuller, gold card comes first, so the list is not in
  time order. [How to sign up for an Open Match, image](https://playerhelp.playtomic.com/hc/article_attachments/43661039908753) ([saved](../shots/gaps-DECK-playtomic-for-your-level-order.png)) — read 2026-10-08
- **[POLICY]** The gold border is a Golden Match. The Terms say a Golden Match "promotes the
  distinguished and promoted match in the available matches". The app says "Golden Matches will give
  your matches more visibility so they get filled sooner", and the Premium help says "Matches you
  create or join are promoted as Golden Matches". The Premium help's image shows two gold cards,
  14:30 then 17:00. [Legal Conditions](https://playtomic.com/legal-conditions), [Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited) ([image](../shots/gaps-DECK-playtomic-golden-matches-list.png)) — read 2026-10-08
- *Reading:* one image cannot tell whether the gold promotion or the fuller line-up lifted the 17:00
  card. Paid promotion is a ranking factor, the case P2B Art. 5(3) names (below). Rakieta's
  fewest-seats-first order is close to Playtomic's "Number of players" sort, made the default and
  free of payment.

### The EU platform-to-business rule: clubs must be told the main ranking parameters in the terms
- **[LAW]** Regulation (EU) 2019/1150 applies to online intermediation services offered to business
  users established in the EU that offer services to consumers in the EU (Art. 1(2)). Such a service
  lets business users "offer goods or services to consumers, with a view to facilitating the
  initiating of direct transactions", on a contract with them (Art. 2(2)). "Ranking" is "the relative
  prominence given to the goods or services offered through online intermediation services …
  irrespective of the technological means used" (Art. 2(8)).
  [Regulation (EU) 2019/1150](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R1150) — read 2026-10-08
- **[LAW]** Art. 5(1): "Providers of online intermediation services shall set out in their terms and
  conditions the main parameters determining ranking and the reasons for the relative importance of
  those main parameters as opposed to other parameters." Art. 5(3): where payment can influence
  ranking, the terms must describe those possibilities and their effects. Art. 5(5): enough for an
  "adequate understanding" of how the services' characteristics and their relevance to consumers
  count. Art. 5(6): no duty to disclose algorithms. Art. 3(1): terms must be plain and intelligible and
  available "at all stages … including in the pre-contractual stage". [same](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R1150) — read 2026-10-08
- **[LAW]** The small-enterprise exemption covers only the complaint-handling system (Art. 11(5)) and
  mediation (Art. 12(7)): they "shall not apply to providers … that are small enterprises". Art. 5 has
  no exemption. [same](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019R1150) — read 2026-10-08
- **[DOCS]** The Commission's ranking guidelines put feeds in scope: "algorithmic sequencing of results
  in response to a search query is just one example". Covered presentation includes "'default'
  ordering of goods and services that consumers may navigate without using search queries … visual
  exposure … highlighting" (§36), and different headings or markings for parts of a list (§37).
  [Guidelines on ranking transparency, 2020/C 424/01](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52020XC1208(01)) — read 2026-10-08
- **[ABSENT]** A published statement of ranking parameters for clubs by Playtomic or Playmore. Playtomic's
  player Legal Conditions contain none; its club contract is not public. Playmore's partner terms were
  read for money only (`topics/platforms.md#playmore--the-clubs-money-passes-through-reservise`). — read 2026-10-08
- *Reading:* Rakieta contracts with clubs, and players book those clubs' hours through it, so a club is a
  "business user". The deck's order (seats open after your yes, card type, deadline, forecast) decides
  the relative prominence of the club's hours. The P2B rule therefore wants those parameters, and why
  they weigh as they do, in the club terms. This holds even though the deck is a feed and Rakieta is
  small. The consumer-side duty (`areas/DECK.md` §4) is separate.

---

## R-DECK-18 — taking back a pass in a deck

### Tinder lets a subscriber take back the last swipe
- See `topics/gaps-SWIPE.md#tinder-lets-a-subscriber-take-back-the-last-swipe-a-no-included`: Rewind
  takes back "your last Like or Nope", for subscribers only (help updated 2026-10-01).

### Bumble's Backtrack undoes a no swipe, on a paid plan, and never a yes
- **[POLICY]** "If you accidentally swipe left on someone, or change your mind, you can use Backtrack to
  undo it. Simply tap the 'undo' arrow in the top-right corner (you'll need a Bumble Boost, Premium or
  Premium+ subscription for this). Please note that it is not possible to Backtrack or undo a right
  swipe." SuperSwipes "can't be undone". Boost lists "Unlimited Backtrack: undo a no swipe on someone
  you liked". [Bumble: Using the 'People' tab](https://support.bumble.com/hc/en-us/articles/28423154479645-Using-the-People-tab) (updated 2026-10-08),
  [Bumble: paid features](https://support.bumble.com/hc/en-us/articles/32668790872733-Understanding-Bumble-s-paid-features-and-subscription-plans) (updated 2026-10-07) — read 2026-10-08

### No racket deck offers an undo
- **[ABSENT]** Undo, rewind or a passed card coming back: Hitch (2.2.79), RallyRally (1.0.1), CourtSync
  (1.1.3, "Swipe through match proposals") and Matchup Sport (1.1.1). Their store descriptions and
  release notes were searched for "undo", "rewind", "go back", "take back", "zurück", "rückgängig".
  Noavo, Padelbuddy and Quadra are covered in
  `topics/gaps-SWIPE.md#the-racket-swipe-decks-say-nothing-about-taking-a-pass-back`.
  [Hitch](https://apps.apple.com/gb/app/find-doubles-partners-hitch/id6670320911), [RallyRally](https://apps.apple.com/gb/app/rallyrally/id6758130721),
  [CourtSync](https://apps.apple.com/gb/app/courtsync-padel-matches/id6764694179), [Matchup Sport](https://apps.apple.com/de/app/matchup-sport/id6782085896) — read 2026-10-08
- *Reading:* in dating apps an undo is a paid extra that covers the last no only, never a yes. A free
  Undo after a no would be ahead of every deck found; with no undo, Rakieta is level with the racket
  decks.

---

## R-DECK-15 — what a club-wide pause does to bookings already made

### kluby.org's switch is still documented only as stopping online booking
- **[POLICY]** Garden Padel's booking page still shows its courts, hours and grid under "Tymczasowo
  rezerwacje ONLINE zostały wyłączone. Skontaktuj się z klubem aby wyjaśnić tę kwestię." Padel House
  shows "Ten klub ma wyłączone rezerwacje ONLINE." and no courts. The feature dates from the
  December 2022 release: "Możliwość dodania powodu wyłączenia rezerwacji online".
  [kluby.org: Garden Padel](https://kluby.org/garden-padel/rezerwacje), [Padel House](https://kluby.org/padel-house-krakow/rezerwacje),
  [Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[ABSENT]** What the switch does to bookings already made or being paid. Searched: the changelog for
  2017–2026 ("wyłącz", "wstrzym", "zawiesz", "ONLINE"); the club help's chapter list, which is videos
  only and has no chapter on the switch; the user terms; and both live pages.
  [kluby.org: Pomoc](https://oferta.kluby.org/pomoc), [Regulamin](https://kluby.org/regulamin) — read 2026-10-08

### Playmore: ending or pausing a game series keeps the games already made
- **[POLICY]** Ending a recurring open-game series: "Nie założymy kolejnych gier. Gry już założone zostają
  — odwołujesz je jak zwykle." A club can pause a series: "Klub wstrzymał tę serię. Wznowić ją może
  tylko klub." An organiser's pause skips the next date: "Następny termin pominięty."
  [Playmore strings: reservations (Ct1XsxUt.js)](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** A club that turns open games off appears only as a refusal on creating: "Gry otwarte są w
  tym klubie wyłączone." (`OPEN_GAME_VENUE_DISABLED`, mapped to the creator's errors).
  [5Yh7m0Pp.js](https://playmore.pl/assets/5Yh7m0Pp.js), [Ct1XsxUt.js](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[ABSENT]** What happens to open games already published when a club turns open games off. No
  string or error covers it. — read 2026-10-08
- *Reading:* the one platform that says anything keeps games already made and stops new ones. That is
  Rakieta's rule for a paused club, whose filling cards stay until their book-by.

---

## R-DECK-11 and R-DECK-14 — two games at the same hour

### Playmore does not stop a player joining two open games at the same hour
- **[ABSENT]** A same-hour refusal on joining. None of Playmore's mapped open-game errors covers it.
  Those errors include slot taken, too many active, too soon, too far ahead, already started, not
  found, prepay required and the series errors. The Polish strings were searched for "tym samym
  czasie", "tej samej godzinie", "koliz", "nakłada", "pokrywa się", "inną grę", "innej gry".
  [5Yh7m0Pp.js](https://playmore.pl/assets/5Yh7m0Pp.js), [Ct1XsxUt.js](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** The only per-player limit is a club's cap on active games, checked when creating a game:
  "Masz już maksymalną liczbę aktywnych gier otwartych w tym klubie." (`OPEN_GAME_TOO_MANY_ACTIVE` →
  `creator.errors.tooManyActive`). [same](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** *(code)* The court-booking grid marks hours where the player already has something, at any
  club: "Masz już termin: {details}. Pokaż szczegóły"; sheet "Twoje terminy"; "Inny klub: {venue}";
  pills "Twoja gra", "Twój trening". This is a marker on the court grid (`OwnBookingMarker`), not a
  refusal, and not on the open-games list. [CMQ6w4-L.js](https://playmore.pl/assets/CMQ6w4-L.js), [Ct1XsxUt.js](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08

### Playtomic's app has no same-hour warning either
- **[ABSENT]** No string about a match or booking at the same time ("same time", "already have a match",
  "overlap", "at that time") among the Android 6.93.2 strings. This agrees with the earlier
  `market.md` §7.7. [Android 6.93.2 strings](../shots/gaps-DECK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- *Reading:* for R-DECK-11, never dealing a card at an hour the player has taken is ahead of both. For
  R-DECK-14, letting two filling games at one hour both take a yes matches Playmore. Playmore then
  charges both joins at once, where Rakieta books the first to fill and withdraws the other yes.

---

## R-DECK-34 — a swipe, an "I'm in" control, or a price on the control

### No Polish ruling or UOKiK statement on a swipe, "Dołączam", or a price on the button
- **[ABSENT]** Searched UOKiK's site and consumer Q&A, Polish case-law and news search for "art. 17 ust.
  3" with "aplikacja", "przycisk", "przesunięcie" and "Dołącz". Only the charges and guidance below were
  found. — read 2026-10-08

### What authorities have said about order buttons, beyond the research so far
- **[DOCS]** UOKiK, charges against Temu's seller Whaleco (16 Oct 2024): "the button 'Place your order'
  may be insufficient"; "it should contain the words as follows: 'with obligation to pay'". The same
  release says "some content available there is presented in Chinese".
  [UOKiK: Who is the seller on the Temu platform?](https://uokik.gov.pl/en/who-is-the-seller-on-the-temu-platform) — read 2026-10-08
- **[DOCS]** The Commission's guidance on the order button: "The respective indication (label) must be on
  the button itself or immediately next to it". "'buy now', 'pay now' or 'confirm purchase'" pass;
  "'register', 'confirm' or 'order now'" and "unnecessarily long phrases" are "less likely to meet this
  requirement". [Commission Notice 2021/C 525/01 §4.2.2](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52021XC1229(04)) — read 2026-10-08
- **[LAW]** Dutch Supreme Court (Hoge Raad), Friday 4 Oct 2024, on bol.com and a second case: buttons
  reading "bestellen", "bestelling plaatsen" or "bestelling afronden" do not say clearly enough that
  the consumer must pay. "The text on the button must be unambiguous and necessarily create a
  connection with the creation of a payment obligation." Bol had already changed its button to
  "order and pay" in 2022. This is a news report of the ruling.
  [NL Times, 6 Oct 2024](https://nltimes.nl/2024/10/06/supreme-court-rules-online-order-button-clear-enough) — read 2026-10-08
- The "Zamawiam" charge (4 Feb 2026), C-400/22 *Conny* and C-249/21 *Fuhrmann-2* are in
  `topics/local-market.md#the-order-button-and-a-yes-that-charges-later`.
- *Reading:* each authority judges the words on the control, or the words right next to it. A swipe is
  a "similar function" with no words of its own. "I'm in" or "Dołączam" says joining, not paying, so
  it sits with "bestellen" and "Zamawiam". A price printed on the control ("40 zł") is a fact, not a
  statement that the tap or swipe creates a duty to pay; no authority has said a price alone is
  enough (*opinion*).

---

## R-DECK-32, R-DECK-33, R-DECK-34 — must the binding information be in Polish?

### Polish law requires offers and required consumer information in Polish; other languages may stand beside
- **[LAW]** Polish Language Act, Art. 7(1): in dealings with consumers in Poland, Polish is used where
  the consumer lives in Poland when the contract is made and it is performed in Poland. Art. 7(3): the
  Act covers documents and information required by other laws. Art. 7a(1): the duty covers "nazewnictwa
  towarów i usług, ofert, … faktur, rachunków i pokwitowań, jak również ostrzeżeń i informacji dla
  konsumentów wymaganych na podstawie innych przepisów … oraz informacji o właściwościach towarów i
  usług". Art. 7a(2): foreign-language offers and consumer information "muszą być jednocześnie
  sporządzone w polskiej wersji językowej".
  [Ustawa o języku polskim, Dz.U. 2026 poz. 81](https://api.sejm.gov.pl/eli/acts/DU/2026/81/text.pdf) — read 2026-10-08
- **[LAW]** Art. 8(1): consumer contracts and documents are drawn up in Polish. Art. 8(1a): foreign
  versions may run alongside, and the Polish one governs for Polish citizens. Art. 8(1b): a contract
  may be in a foreign language only at the request of a consumer who is not Polish, speaks that
  language and was first told of the right to Polish. Art. 15(1): using only foreign-language offers or
  required consumer information is punished by a fine. Art. 7b: UOKiK, the Trade Inspection and
  consumer ombudsmen enforce it. The May 2026 amendment
  (Dz.U. 2026 poz. 676) changes certification and does not touch Art. 7–8 or 15.
  [Dz.U. 2026 poz. 81](https://api.sejm.gov.pl/eli/acts/DU/2026/81/text.pdf), [Dz.U. 2026 poz. 676](https://api.sejm.gov.pl/eli/acts/DU/2026/676/text.pdf) — read 2026-10-08
- **[DOCS]** Poland notified Art. 7 and 7a of this Act to the Commission as its language requirement
  under Art. 6(7) of the Consumer Rights Directive ("so as to ensure that such information is easily
  understood by the consumer").
  [Commission: Poland's regulatory choices under the CRD](https://commission.europa.eu/system/files/2019-05/pl_regulatory_choices_en_version.pdf) — read 2026-10-08
- **[DOCS]** UOKiK's Temu charges named content "presented in Chinese" (above).
- *Reading:* for a Kraków player at a Kraków club, the price, when payment is taken and the absence of a
  free cancellation are information Art. 12 of the Consumer Rights Act requires
  (`topics/local-market.md#what-the-player-must-see-before-being-bound`). So they must be in Polish.
  English may sit beside them, but English only risks a fine and a UOKiK case. The order words on a
  control would be judged in Polish too.

---

## R-DECK-33 — a Polish complaint about a late charge under a rule the player didn't see

### Not found; the nearest Polish complaints are about refunds after cancelling
- **[ABSENT]** A first-hand Polish complaint that a late-cancellation charge was kept under a rule the
  player had not been shown. Searched: the Polish App Store review feeds, 10 pages each (152 reviews),
  of Playtomic, Playmore, kluby.org, tenis4U, PADO, MATCHi and Padel Mates; Playmore's Polish Google
  Play page; and Polish web searches ("odwołałem rezerwację … pobrali", "opłata za późne odwołanie
  kortu"). — read 2026-10-08
- **[COMPLAINT]** "OSTRZEGAM! Nie zwracają środków za anulowaną rezerwację. Nie odpisują na maile. Brak
  kontaktu." (Katarzyna R., 1★, Google Play PL, Playmore, 2026-08-26).
  [Google Play PL: Playmore](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp&hl=pl&gl=PL) — read 2026-10-08
- **[COMPLAINT]** A refund request for a booking cancelled "more than 24h before booking time, so fully
  refundable" unanswered after two weeks (Lycroois, 1★, App Store PL, Playmore, 2026-09-28, in English).
  [App Store PL feed](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=928403015/sortBy=mostRecent/json) — read 2026-10-08
- **[COMPLAINT]** A tenis4U user asks to "odblokować" a slot after the cancellation deadline has passed,
  without a refund, so someone else can use it (luki1645, 5★, App Store PL, 2020-06-20).
  [App Store PL feed](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=1222721113/sortBy=mostRecent/json) — read 2026-10-08

---

## R-DECK-9 — where Playmore's "Mało czasu" badge shows

### In the creator's slot picker, never on the joiner's card
- **[POLICY]** *(code)* The key is `reservations.openGames.creator.slot.shortLeadBadge`, and only the
  creator's slot grid uses it: `isShortLeadCell(d,i)?{label:a("reservations.openGames.creator.slot.shortLeadBadge")}`.
  Its hint, under the same `creator.slot` namespace, reads: "Do gry zostało mniej niż 24 h. Tak blisko
  skład zbiera się rzadko — zaproś znajomych od razu po opłaceniu albo wybierz późniejszy termin."
  [RktoVfyX.js](https://playmore.pl/assets/RktoVfyX.js), [Ct1XsxUt.js](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** *(code)* The joiner's card keys (`card.*`, `status.*`) carry no short-time badge. The card
  shows urgency only through the status strip "Komplet do {time}" and its countdown "Zostało {h} godz.
  {m} min", which runs whatever the time left (`status.open`, `status.countdownHm`).
  [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08
- *Reading:* this corrects the lenses' reading. Playmore puts a countdown on every open card and a
  "less than 24 h" badge only in front of the person creating a game.

---

## R-DECK-39 — where a notice about a game lands

### Playtomic's alerts cover courts and the last place in a match; a court alert opens the club's slot
- **[POLICY]** The alert wizard asks "What alerts do you want to receive?": "Last minute cancellations",
  "Few courts available", "Last place in an Open Match". Inbox lines read "**Last minute cancellation**
  for **{alert name}**" and "**Last available spot** for **{alert name}**". An alert can expire ("Keep
  alert active"). [Android 6.93.2 strings](../shots/gaps-DECK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[POLICY]** A court alert opens the club's page (`tenant_detail_push_*`) and says why when the hour has
  gone: "The time slot is no longer available."; "The date for that availability has already passed."
  A link to a match that has filled says "The match is full, and there are no available spots".
  [same](../shots/gaps-DECK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[POLICY]** The help image shows alerts on a club's *Book* tab ("Priority alerts — Configure your alert
  in one click with your predefined filters — Manage Alerts"). The Inbox shows "Priority alerts — Create
  or manage your alerts" and an Activity line "Last minute cancellation for Last minute cancellation 10
  minutes ago". [Premium Plan: Unlimited, image](https://playerhelp.playtomic.com/hc/article_attachments/44737079789969) ([saved](../shots/gaps-DECK-playtomic-priority-alerts-inbox.png)) — read 2026-10-08
- **[POLICY]** *Club Updates* (bell → "Club" tab) counts a favourite club's open matches for 7 days:
  "Click on any activity type to go directly to that section of the club". It lands on a list, not a
  match. [How to follow your favorite club activities](https://playerhelp.playtomic.com/hc/en-gb/articles/44465662231185-How-to-follow-your-favorite-club-activities) (updated 2026-09-29) — read 2026-10-08
- **[ABSENT]** What a "Last place in an Open Match" push opens: no string or help text names its screen.
  Reviews on six App Store feeds (GB, ES, PL, SE, IT, NL) were also searched. Alert complaints are in
  `topics/gaps-RESCUE.md#players-say-the-alerts-dont-fire`. — read 2026-10-08

### Playmore opens the club's open-games list with the game scrolled to the centre
- **[POLICY]** *(code)* An open-game link or alert opens `/reservation/{venue}/open-games?gameId=…`, with
  `seekAlert=1` for an alert. The page drops the alert flags, keeps `gameId` and finds the game. It
  widens the date window if needed, marks the game focused and scrolls it to the middle of the screen:
  `scrollIntoView({behavior:"smooth",block:"center"})`. If the game is gone, it says why: "Ta gra już się
  zapełniła" / "Ta gra została odwołana" / "Ta gra już się odbyła" / "Nie udało się sprawdzić tej
  gry". It then offers "Zobacz inne gry w {venue} w najbliższych dniach." and "Inne gry w {venue}".
  [DM7ksFDa.js](https://playmore.pl/assets/DM7ksFDa.js), [D8YZN20W.js](https://playmore.pl/assets/D8YZN20W.js), [Ct1XsxUt.js](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- *Reading:* Rakieta's "card on top while it is still dealt" is level with Playmore's focus. Both rivals
  say why a game or hour is gone; a notice that lands with no word on a card no longer dealt would be
  behind them.

---

## R-DECK-32 — a benefit-card holder who has paid a share online

### Playmore: declare the card, pay a refundable card deposit, get it back when reception scans the card
- **[POLICY]** "Zniżkę za kartę sportową potwierdza dopiero jej odbicie w recepcji przy wizycie — tak
  działają programy kart sportowych (np. MultiSport, Medicover Sport), a klub rozlicza się z operatorem
  karty tylko za odbite wejścia. Rezerwację opłacasz przed wizytą, więc do ceny z kartami doliczamy
  kaucję za karty. Kaucja wraca na Twój portfel zaraz po odbiciu karty w recepcji … Wcześniej część
  klubów dawała zniżkę od razu — gdy karty potem nie odbito, klub tracił tę kwotę. Dlatego od sierpnia
  2026 wszystkie kluby w Playmore rozliczają karty tak samo."
  [Playmore strings (Ct1XsxUt.js)](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** At some clubs online payment forfeits the discount: "W tym klubie zniżka za karty partnerskie
  działa tylko przy płatności na miejscu … Przy płatności online płacisz pełną cenę i różnica nie
  wraca"; "Rezerwacja opłacona online zostaje w pełnej cenie — także po odbiciu kart."
  [same](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** In a shared or open game: "Kto ma kartę partnerską? … Zaznacz, kto ma kartę. Zwrot za nią
  trafi do tej osoby, gdy zapłaci swoją część przed odbiciem karty"; "W grze otwartej płacisz z góry —
  online, portfelem albo karnetem. Płacisz kartą partnerską? Zaznacz ją w formularzu." The open-game card
  shows "Karty partnerskie w grze: {count}". [same](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** Atras Squash Club (Kraków) honours "MultiSport (wszystkie warianty), Medicover Sport,
  FitProfit i PZU Sport — maksymalnie 2 karty jednego partnera na kort".
  [Playmore: Atras Squash Club](https://playmore.pl/klub/atras-squash-club/) — read 2026-10-08
- **[COMPLAINT]** "Nieintuicyjne rezerwacje, płatność całej kwoty nawet jeśli używa się kart Multisport,
  dodatkowe opłaty dla playmore za rezerwację" (Adam Ł, 1★, Google Play PL, Playmore, 2026-08-29).
  [Google Play PL: Playmore](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp&hl=pl&gl=PL) — read 2026-10-08
- **[ABSENT]** A Kraków club's own written rule for a card holder who paid online through another
  platform. The rules found say only that a card "nie zastępuje rezerwacji kortu" and takes about 15 zł
  off at the desk (`topics/local-market.md#how-kraków-clubs-take-the-cards-about-15-zł-off-per-card-on-site`). — read 2026-10-08
- *Reading:* the market's answer is to ask about the card before paying and to return the card's share
  when reception scans it. Without that, a player who paid a 40 zł share online pays full price and
  loses the about 15 zł the desk would have taken off. That is the complaint Playmore's players make.
