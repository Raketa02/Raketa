# Gaps round: LEAVE

Answers to the facts the LEAVE grades needed (`$W/areas/LEAVE/gaps.md`), read 2026-10-08. Each `###` heading answers one
gap and names its rule. Sources: Playtomic's two help centres (all 157 club and 94 player en-gb articles, pulled through
the Zendesk API on 2026-10-08), MATCHi's two help centres (243 venue and 76 player articles, same way), Playmore's web
app as shipped (its string bundles and the code that uses them, read 2026-10-08), Padel Mates' web strings, and the
Kraków clubs' own terms (re-read 2026-10-08). A line marked *reading* is this researcher's inference from the facts
above it, not a source.

Kinds: `[POLICY]` a rule or wording the operator publishes or ships; `[PRICE]`; `[LAW]`; `[DOCS]` a provider's or a
regulator's documents and data; `[COMPLAINT]`; `[ABSENT]` looked for and not found, with where.

## R-LEAVE-8: is a late leaver told whether the seat was taken

### Playmore tells a late leaver the outcome is settled after the game, in the wallet

- **[POLICY]** When a player cancels after the free window and the club's rules may still give the money back, the
  reservation shows "Rozliczymy to po terminie gry" — "O tym, czy środki wrócą po odwołaniu po terminie, decyduje
  regulamin klubu. Rozliczenie idzie w nocy po terminie rezerwacji — wtedy zobaczysz wynik w portfelu." Other outcome
  cards: "Odwołanie po terminie — opłata zostaje w klubie" ("Zgodnie z regulaminem obiektu rezerwacja odwołana po
  terminie nie podlega zwrotowi"), "Zwróciliśmy {amount} na Twój portfel Playmore", "Zwrot {amount} realizuje klub"
  and "Zleciliśmy zwrot {amount} na Twoją kartę lub konto". [Playmore web strings](https://playmore.pl/assets/CG9yQPLY.js)
  (`cancellationRefund`) — read 2026-10-08
- **[POLICY]** A late leaver of an open game is told at the press: "Termin bezpłatnego wypisania minął, więc wpisowe na
  razie przepada. Jeśli gra nie zbierze składu albo odwoła ją klub, wpisowe wróci do Ciebie. Opłata serwisowa nie
  podlega zwrotowi." [same](https://playmore.pl/assets/CG9yQPLY.js) (`cancellation.openGame.lateLeaveRefund`) — read
  2026-10-08
- *reading:* Playmore names the moment (the night after the game) and the place (the wallet) where a late leaver learns
  whether money came back, and keeps an outcome card on the cancelled reservation. It does not say "your seat was
  taken"; no string announcing a taken or untaken seat to the leaver was found. **[ABSENT]** searched both string
  bundles for "zajął", "zajmie", "Twoje miejsce", "warunkow" — read 2026-10-08

### Padel Mates keeps the late leaver in the game until a replacement joins

- **[POLICY]** Past the window the leaver gets two choices: "The cancellation window has passed. You have two options:"
  "Cancel without a refund", or "Find a replacement for your spot — To find a replacement, copy the link below and share
  it. If someone joins using this link, you will be automatically removed from the activity and receive a refund within
  3–10 business days." [Padel Mates web strings](https://padelmates.se/locales/en/translation.json)
  (`cancellationWindowPassed`, `findReplacementSpotDescription`, `businessDays`) — read 2026-10-08
- *reading:* the leaver who chooses a replacement stays on the roster until someone takes the spot, so the game in his
  own list is the signal: still there means not taken; gone means taken and refunded. **[ABSENT]** no string telling
  the leaver his spot was taken, or that nobody took it before the start (searched "replac", "refund", "removed",
  "notif") — read 2026-10-08

### Kraków clubs waive a late fee if the court is resold, and tell the player only of a debt

- **[POLICY]** Atras: a late cancellation is charged "chyba że kort zostanie wynajęty przez innego klienta. W takiej
  sytuacji klubowicz, który odwołał rezerwację po terminie, będzie zwolniony z opłaty"; for a no-show, "O fakcie
  niestawienia się na korcie i powstałej zaległości pracownik recepcji klubu poinformuje klubowicza w danym dniu lub
  następnym." [Atras regulamin §6](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Miazga: "Klubowicz zostanie zwolniony z opłaty za nieterminową anulację jeżeli kort zostanie
  zarezerwowany i opłacony przez innego gracza"; the cancellation itself is confirmed by SMS, or by the status
  "Anulowana" in the app. [Miazga regulamin §4](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Squash4You: inside 24 h a cancellation is "w trybie warunkowym", the desk "będzie starał się w pierwszej
  kolejności sprzedać" the hour, which shows as free online; the fee is "zryczałtowane odszkodowanie" owed by bank
  transfer within 7 days. [Squash4You regulamin §5 c–e](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[ABSENT]** None of the three says it tells the leaver that the court was, or was not, resold; the leaver learns it
  from whether a fee is asked for (Atras's desk calls about a debt; Squash4You expects a transfer). Searched the three
  regulamins for "poinform", "zawiadom", "sprzeda" — read 2026-10-08

## R-LEAVE-36: the club cancels after an earlier leave

### Playmore gives a late leaver the entry back when the club cancels; a timely leaver already had it

- **[POLICY]** Late leaver: "Jeśli gra nie zbierze składu albo odwoła ją klub, wpisowe wróci do Ciebie. Opłata
  serwisowa nie podlega zwrotowi." [Playmore web strings](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[POLICY]** Timely leaver: "Rezygnujesz w terminie bezpłatnego odwołania"; every refund goes to the Playmore wallet
  and "Opłata serwisowa nie podlega zwrotowi". [Playmore open-game strings](https://playmore.pl/assets/93jAIRDY.js) —
  read 2026-10-08
- *reading:* at Playmore both leavers end level when the club cancels: each has the entry back and each has lost only
  the service fee, which no Playmore refund returns. The one who left early is never worse off than the one who left
  late.

### Playtomic: a timely leaver is already whole, and a late leaver cannot leave

- **[POLICY]** Leaving an open match in time refunds "a full automatic refund (including the Playtomic service fee)";
  inside 24 h of a full match "players cannot cancel through the app… the club will decide". A club cancellation
  refunds in full, fee included. [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601)
  (updated 2026-10-08), [Cancel a reservation (club)](https://helpmanager.playtomic.com/hc/en-gb/articles/20535256445969)
  — read 2026-10-08
- *reading:* no Playtomic player can be in Ivan's place, a timely leaver left short, because a timely leave returns
  everything. The question of who gets what at a later club cancellation never arises.
- **[ABSENT]** What a Kraków club gives a player who left a group earlier: club terms deal only with the booker (see
  `local-market.md#the-booker-owes-the-whole-court`); none mentions the group's other members. Searched Atras, Miazga,
  Squash4You, Garden Padel — read 2026-10-08

## R-LEAVE-14: rejoining after leaving, and an undo

### Playtomic's own help tells a player to leave and join the same match again

- **[POLICY]** "If you joined a match before having a level, you may need to leave the match, complete the initial
  level questionnaire to get your level, and then join again (if the match is still available)." [How the Playtomic
  level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works)
  (updated 2026-10-07) — read 2026-10-08
- *reading:* a player who left a Playtomic open match may join it again while a spot is open, and since a timely leave
  refunds everything, the round trip costs nothing.

### Playmore has no rule against a former player rejoining an open game

- **[ABSENT]** Playmore's open-game error codes (63 of them, `OPEN_GAME_ALREADY_STARTED` … `OPEN_GAME_VENUE_DISABLED`)
  hold none for a player who left; the only rejoin cooldown is for leagues (`REJOIN_COOLDOWN_ACTIVE`,
  "rejoinCooldownDays"). [Playmore web code](https://playmore.pl/assets/5Yh7m0Pp.js) — read 2026-10-08
- *reading:* a Playmore leaver may join again as anyone else, paying the entry and a new service fee.

### No platform offers an undo on leaving

- **[ABSENT]** No undo after leaving at Playtomic (all 251 help articles; "undo" appears only for payments, benefits
  and account deletion), Playmore (its only "Cofnij" withdraws a running-late status or an invitation), Padel Mates
  (web strings) or MATCHi (all 319 help articles) — read 2026-10-08
- **[POLICY]** Playmore's leave dialog for an organiser offers "Wróć" and states the cost before the press; its
  full-game warning offers "Zostaję w grze" against "Wypisz się mimo to". [Playmore open-game strings](https://playmore.pl/assets/93jAIRDY.js)
  — read 2026-10-08

## R-LEAVE-3: a quote that holds at the press

### Playmore works out the free window on the phone when the screen loads, and the server decides at the press

- **[POLICY]** The free-window test is `now <= free_cancellation_until` with `now = Date.now()`
  ([helper](https://playmore.pl/assets/Do_BUeqR.js)); the reservation page wraps it in a cached computed value that
  recomputes only when the reservation itself changes, then confirms with `deleteUserReservation(id, venue)` and no
  expected cost ([reservation cancel flow](https://playmore.pl/assets/CSB8J-_f.js)); the modal is titled
  "Anulowanie rezerwacji" or "Anulowanie rezerwacji nie na czas" from that value ([cancel modal](https://playmore.pl/assets/DtTD39JH.js))
  — read 2026-10-08
- **[POLICY]** For an organiser cancelling a game the sheet quotes the forfeit from `Date.now()` too, and the toast
  after the press follows the server's answer: `refund === "organizer_forfeit"` gives "Gra odwołana. Twoje wpisowe
  przepadło (anulacja nie na czas)…", otherwise "Gra odwołana - wpisowe wróciło do wszystkich graczy."
  [organiser exit and cancel](https://playmore.pl/assets/Dvmne_lJ.js) — read 2026-10-08
- *reading:* Playmore's dialog quotes what was true when the page loaded and does not check again at the press; a
  player who keeps the page open past the line, without it reloading the reservation, is told "free" and then charged.
  The toast is a neutral "Rezerwacja została anulowana." What it adds is an outcome card after
  the press, drawn from the server ("Odwołanie po terminie — opłata zostaje w klubie"), so the result is never hidden.
- **[ABSENT]** Whether the server refuses a press whose quote has gone stale: the request carries no quoted cost, so
  nothing could compare. Read from the shipped code only; not tried by hand — 2026-10-08

## R-LEAVE-20: free beside a fee kept

### Garden Padel says "bezpłatnie" while tenis4U, its booking system, keeps 2 % of an online refund

- **[POLICY]** "Rezerwację można odwołać bezpłatnie do 24 godzin przed terminem gry"; bookings go through "aplikację
  tenis4U" and are paid online by Przelewy24. [Garden Padel regulamin 4–5](https://gardenpadel.pl/regulamin) — read
  2026-10-08
- **[POLICY]** "Usunięcie rezerwacji opłaconej za pomocą płatności internetowych generuje zwrot środków pomniejszonych o
  opłatę transakcyjną w wysokości 2%". [tenis4U regulamin pkt 11](https://tenis4u.pl/regulamin/) — read 2026-10-08
- *reading:* a Garden Padel player who books online and cancels in time reads "bezpłatnie" in the club's terms and gets
  98 % back under the platform's terms. The two documents are never shown side by side.

### Playmore says "bezpłatne" and "bez dodatkowych opłat" and keeps its service fee

- **[POLICY]** The checkout line: "Bezpłatne odwołanie do {h} h przed" / "Bezpłatne odwołanie do {date}", then "Środki
  wrócą na Twój portfel Playmore". [Playmore open-game strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[POLICY]** The reservation page: "Bezpłatne anulowanie do {date}"; "Możesz anulować tę rezerwację bez dodatkowych
  opłat zgodnie z regulaminem obiektu"; the leave dialog: "Rezygnujesz w terminie bezpłatnego odwołania."; the open-game
  modal adds "Opłata serwisowa nie podlega zwrotowi." [Playmore web strings](https://playmore.pl/assets/CG9yQPLY.js),
  [open-game strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[PRICE]** The service fee kept: 1,48 zł at Atras. `platforms.md#playmore--player-fees` — read 2026-10-06
- *reading:* both Kraków systems call a timely cancellation free while something is kept: tenis4U 2 % of the payment,
  Playmore its service fee. Playmore states the kept fee on the open-game modal; tenis4U states it only in its terms.

## R-LEAVE-21b: the empty share of a short game

### No platform splits an empty share among the players still in; the owner or booker pays it

- **[POLICY]** Playtomic, a private booking turned public that does not fill: "The match is not automatically
  cancelled… Payment: The owner will be charged for empty spots. Players who joined after the conversion will receive a
  refund 2 hours after the scheduled match time." [How to convert a Private Booking to a Public Match](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match)
  (updated 2026-10-01) — read 2026-10-08
- **[POLICY]** Playtomic, an open match the club forces a court onto: "it won't be automatically cancelled"; who pays
  the empty spots is still not stated. [How to manually book a court for a Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535050634769-How-to-manually-book-a-court-for-a-Open-Match)
  (updated 2026-09-09) — read 2026-10-08
- **[POLICY]** MATCHi public match: the holder "remains financially responsible for it"; split payment: unpaid parts
  fall on the booker 2 h after. `platforms.md#matchi--public-matches-the-holder-stays-liable` — read 2026-10-06/08
- **[ABSENT]** A rule that lets the players still in keep a short game by sharing the missing player's part: not at
  Playtomic, MATCHi, Playmore ("gra bez kompletu odwoła się automatycznie"), Padel Mates or kluby.org (booker's card).
  Searched the help centres above for "remaining players", "split the remaining", "empty spots" — read 2026-10-08

## R-LEAVE-22: fees on an automatic call-off's refund

### Playtomic returns its own fee and its commission; the card fee is not stated

- **[POLICY]** An automatic cancellation refunds "a full automatic refund (including the Playtomic service fee)".
  [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) — read 2026-10-08
- **[POLICY]** On the club's side: a refund of a booking already paid out is deducted from the next weekly payout; "you
  shouldn't end up paying commission on money that was fully refunded to a player. If commission was already charged…
  Playtomic corrects it with a credit note". [Why did I receive a negative payout?](https://helpmanager.playtomic.com/hc/en-gb/articles/50457368851729-Why-did-I-receive-a-negative-payout)
  (updated 2026-09-29) — read 2026-10-08
- **[ABSENT]** Who bears the card processing fee on that refund: none of the 157 club articles says (searched "Stripe
  fee", "processing fee", "card fee", "transaction fee"); "Card on File transactions are treated the same as other online
  payments in terms of processing fees" is the only mention — read 2026-10-08

### MATCHi refunds the platform fee on an auto-cancel and bills the venue a fee per online payment

- **[POLICY]** Venue matches: "System auto-cancels (match not full) — At the cancellation deadline — Spot price including
  platform fee — to everyone"; a player who leaves in time gets the spot "excluding platform fee". [Venue created matches (venue)](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333-Venue-created-matches)
  (updated 2026-06-16) — read 2026-10-08
- **[POLICY]** The venue's monthly statement carries "Fee online payment" lines, a fixed or percentage "transaction fee"
  per online payment; "If a payment is refunded later, the refund appears as its own negative line item on the statement
  for the month the refund was processed". [Explanation of the different lines in a statement](https://matchi.zendesk.com/hc/en-gb/articles/15268887132317-Explanation-of-the-different-lines-in-a-statement)
  — read 2026-10-08
- **[ABSENT]** Whether MATCHi reverses its per-payment transaction fee when the payment is refunded: not stated in the
  statement, refund or service-fee articles — read 2026-10-08
- *reading:* both platforms give the players everything back and take back their own fee or commission; neither says
  the club recovers the card cost. At MATCHi the venue's fee line stands unless stated otherwise, the same shape as
  Rakieta's club absorbing the card fee.

## R-LEAVE-25: telling the club of an automatic call-off

### Playtomic: no club notice of an automatic cancellation is documented

- **[POLICY]** A club admin's email choices are "Bookings created or cancelled by players, course enrollment
  cancellations". [How to add/edit an admin role](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049-How-to-add-edit-an-admin-role)
  (updated 2026-07-17) — read 2026-10-08
- **[POLICY]** An open match without a court never sat in the club's calendar: the court is booked only at 4 players,
  at 3 with more than 4 h left, at 2 with more than 12 h. [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601)
  — read 2026-10-08
- **[ABSENT]** An email, push or Manager notice to the club when Anemone cancels a match: not in any of the 157 club
  articles (searched "Anemone", "automatically cancel", "notif", "email") — read 2026-10-08

### MATCHi emails the venue for any cancelled booking, the system's included

- **[POLICY]** "An email is sent to the Cancellation notification email address when any of the following are
  cancelled: Regular bookings (customer-initiated, admin-initiated, or cancelled automatically by the system)…"; activity
  cancellations instead go to the activity leader and show in "Cancelled activities" with the reason "Automatic (too few
  participants)". [Cancellation notifications](https://matchi.zendesk.com/hc/en-gb/articles/24752705156637-Cancellation-notifications)
  (updated 2026-09-15), [Cancelled Activities](https://matchi.zendesk.com/hc/en-gb/articles/28528118381469-Cancelled-Activities)
  — read 2026-10-08

## R-LEAVE-38: a lone player whose partners dropped out or didn't come

### Playtomic refunds the player who came, and charges the absent the court

- **[POLICY]** "The absent player is charged the court fee. A debt is created in their account… If an attending player
  paid their share online, we refund it once the report has been reviewed — this can take up to 10 days from review,
  plus 2–15 business days"; the report must come from an attending player through support chat, before the result is
  confirmed and within 7 days. [No-Show Policy for Open Matches: what clubs need to know](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513-No-Show-Policy-for-Open-Matches-what-clubs-need-to-know)
  (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** A converted public match left short: joiners after the conversion are refunded 2 h after the hour, the
  owner pays the empty spots. [How to convert a Private Booking to a Public Match](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match)
  — read 2026-10-08

### Kraków clubs bill the booker; the one who came is not singled out

- **[POLICY]** Late cancellation or no-show: the full court fee falls on "osoba na którą widnieje rezerwacja"
  (Squash4You §5 d), the booker at Atras, Miazga ("Niepojawienie się… zobowiązuje Klubowicza do uregulowania pełnej
  opłaty"), Garden Padel ("Niewykorzystanie rezerwacji nie zwalnia z obowiązku zapłaty"). [Squash4You](https://www.squash4you.pl/regulamin),
  [Atras](https://www.atrassquash.pl/regulamin/), [Miazga §6](https://www.miazgasquash.pl/regulamin/),
  [Garden Padel 5](https://gardenpadel.pl/regulamin) — read 2026-10-08
- **[ABSENT]** A refund, a resale or any rule for the one player who came when her partners did not: none of the four
  regulamins has one; the court is the booker's whether one or four play — read 2026-10-08

### Playmore calls a game off for everyone when a seat is still empty at its cut-off

- **[POLICY]** "Gracie, jeśli do potwierdzenia nikt się nie wypisze. Gdy ktoś się wypisze i nikt nie zajmie jego
  miejsca, odwołamy grę, a wpisowe wróci na portfel Playmore. Opłata serwisowa nie podlega zwrotowi."; leaving a full
  game: "Jeśli do {cutoff} nikt nie zajmie Twojego miejsca, gra zostanie odwołana dla całego składu. Pozostali dostaną
  wtedy zwrot wpisowego". [Playmore open-game strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[POLICY]** After the confirmation hour a leaver is told "Termin bezpłatnego odwołania minął — za Twoje miejsce nic
  nie wróci"; the late-leave refund line shows only while the game is not full (`lateLeaveRefund` and fewer players than
  places). [Playmore web code](https://playmore.pl/assets/DgI-SwaW.js), [strings](https://playmore.pl/assets/93jAIRDY.js)
  — read 2026-10-08
- *reading:* at Playmore a player whose partners drop out before the confirmation hour (2 h before by default) gets her
  entry back with the call-off; a player left alone after it is not described. **[ABSENT]** what happens to a confirmed
  game that loses players after confirmation — read 2026-10-08

## R-LEAVE-6: premium and foreign cards in Poland

### At Stripe "premium" means business cards; a consumer gold or platinum card is standard

- **[DOCS]** "Standard domestic cards include consumer cards issued by Visa, Mastercard, and other major providers";
  "premium domestic cards are commercial, corporate, or business cards issued by Visa and Mastercard"; Amex, Maestro,
  Diners, Discover and UnionPay are all standard. Poland is listed among the EEA countries where the two prices apply.
  [Stripe: What's the difference between standard and premium cards?](https://support.stripe.com/questions/what-s-the-difference-between-standard-and-premium-cards)
  (no date on the page) — read 2026-10-08
- **[PRICE]** Poland: standard EEA 1.5 % + 1 zł, premium EEA 1.9 % + 1 zł, UK 2.5 % + 1 zł, international 3.25 % +
  1 zł. `local-market.md#what-polish-operators-charge-against-stripe` — read 2026-10-06
- *reading:* a player paying a 40 zł share with a personal card, however "premium" its name, is charged the standard
  1,60 zł; 1,76 zł applies only to a company card, and 2,30 zł to a card from outside the EEA (a UK card: 2,00 zł).

### No published share of business or foreign cards among card payments in Poland

- **[ABSENT]** The share of commercial cards, or of non-EEA cards, among card payments in Poland: NBP's quarterly
  card report (2025 Q3, the latest found) splits cards by debit, credit, charge and prepaid, not by consumer and
  business, in the coverage read; the report itself refused an automated read; Statista and Euromonitor tables are
  paywalled; Stripe publishes no mix. Searched in Polish and English — read 2026-10-08
- **[DOCS]** For scale: about 46,8 m cards at the end of September 2025, 40,5 m of them debit, 5,1 m credit (10,8 %),
  1,1 m prepaid. [NBP: Informacja o kartach płatniczych 2025 Q3](https://nbp.pl/wp-content/uploads/2026/01/Informacja-o-kartach-platniczych_2025-Q3.pdf)
  (dated December 2025), read through two search engines' extracts of it, which agree; the PDF refused a direct read —
  2026-10-08

## R-LEAVE-4: what a joiner owes in a Kraków game arranged by chat

### The one written Kraków rule covers a no-show only

- **[POLICY]** Padel Krakow League, arranged in a WhatsApp community: "Court costs, balls, and rackets are covered by
  players"; "A no-show = full court fee responsibility, unless both teams agree otherwise"; a match not played is a
  walkover; nothing on cancelling an agreed match in time. [Padel Krakow League: regulamin](https://kluby.org/liga/padel-krakow-league/regulamin)
  — re-read 2026-10-08
- **[POLICY]** A Kraków meetup splits the court among whoever comes, with no drop-out rule.
  `local-market.md#a-meetup-splits-the-court-among-whoever-comes` — read 2026-10-08
- **[ABSENT]** A Kraków group's own rule or post on what a joiner who drops out owes the organiser, in time or late:
  Facebook groups need a login, WhatsApp groups are closed, and Polish web searches ("szukam czwartego", "partner
  odwołał kto płaci za kort", "zastępstwo") found only club regulamins outside Kraków — read 2026-10-08
- *reading:* the club bills the booker (`local-market.md#the-booker-owes-the-whole-court`), so whatever a joiner owes is
  a private matter between him and the organiser; the only Kraków text that settles it, the league's, makes a no-show
  owe the whole court.

## R-LEAVE-21a: how often a fourth is found late, or an hour resold

### No platform or club publishes a late-fill or resale rate

- **[ABSENT]** The share of open games completed in their last 24 hours, or of court hours handed back 24 h ahead and
  sold again: not in Playtomic's help centres, its Global Padel Report page (2026 edition; the full report sits behind a
  download form), Playmore's pages, or the Kraków club regulamins; searched in English and Polish — read 2026-10-08
- **[POLICY]** What the operators' own rules imply: Playtomic holds a court for 2 players only with more than 12 h to
  go and for 3 with more than 4 h, and calls a match off about 1 h before; "Our system predicts match completion based
  on time, club popularity, and player patterns". [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601),
  [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465-Cancellation-Policy-for-Open-Matches-Padel-Tennis)
  — read 2026-10-08
- **[POLICY]** Playmore claims games set up 3+ days ahead fill "mniej więcej 3 razy częściej"; its default call-off is
  2 h before. `platforms.md#playmore--the-clubs-open-game-settings` — read 2026-10-07
- **[POLICY]** Squash4You puts a late-cancelled hour back on the online grid at once and the desk tries to sell it
  first. [Squash4You regulamin §5 c](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[COMPLAINT]** A Playtomic player blocked from releasing a seat inside 24 h: "we could easily find another player
  within a few hours". `competitor-joiner.md#a-late-leaver-blocks-the-seat-in-a-full-match` — read 2026-10-08
- *reading:* every platform that calls games off waits until 1–2 h before, which says the operators expect late fills;
  none gives a number.

## R-LEAVE-32: an automatic call-off after the hour has begun

### No platform calls a game off once it has started; refunds after the hour do exist

- **[POLICY]** Playmore refuses to cancel a game that has begun: "Gra już się rozpoczęła - nie można jej odwołać"
  (`OPEN_GAME_ALREADY_STARTED`). [Playmore open-game strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[POLICY]** Playtomic calls an open match off "about 1 hour before the scheduled start time"; for a converted public
  match that never filled, joiners are refunded "2 hours after the scheduled match time" and the owner pays the empty
  spots. [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601),
  [Convert a Private Booking to a Public Match](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match)
  — read 2026-10-08
- **[POLICY]** Playmore settles a late cancellation "w nocy po terminie rezerwacji"; MATCHi lets a venue refund a card
  booking whose play time is in the current calendar month, past hours included. [Playmore web strings](https://playmore.pl/assets/CG9yQPLY.js),
  [MATCHi: Cancel and/or refund booking](https://matchi.zendesk.com/hc/en-gb/articles/11673921738013-Cancel-and-or-refund-booking)
  — read 2026-10-08
- **[POLICY]** Status quo: rain inside the first 30 minutes refunds the whole hour (MOSiR Sosnowiec). `situations.md`
  SIT-02 — read 2026-10-08
- **[ABSENT]** What a club expects, or any platform does, when its own automatic call-off runs late and reaches a game
  already under way: not in Playtomic's 251 or MATCHi's 319 help articles, Playmore's web strings, or the Kraków
  regulamins (searched "already started", "after the start", "rozpoczęła") — read 2026-10-08
