# Gaps for SWIPE: a yes, a no and a withdrawn yes

Answers to the facts the SWIPE grades asked for and the research lacked
(`areas/SWIPE/gaps.md` of PRD #530). Read 2026-10-08. Each section names the rule IDs it answers.

**Sources.** Playtomic help comes from its public Zendesk API, both player help
(`playerhelp.playtomic.com`, 94 articles in English, 99 in Spanish) and club help
(`helpmanager.playtomic.com`). Playmore interface text and its shipped feature-flag notes come from
the JavaScript its web app serves to every visitor (`playmore.pl/assets/*.js`, 2,244 chunks read by
grep). The flag notes are Playmore's own descriptions of what its app does, written in Polish by its
team. No screenshot was taken, so nothing is `[MEASURED]`.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published
price · `[LAW]` a statute or a court ruling · `[DOCS]` a provider's or regulator's document ·
`[COMPLAINT]` one person's account · `[ABSENT]` looked for and not found, with where. Lines marked
*reading* are not sources.

## 1. The last seat and who is told (R-SWIPE-13, R-SWIPE-15, R-SWIPE-14)

### Playmore's last-seat lines are share texts players send by hand
- **[POLICY]** "Zostało ostatnie miejsce{game}" and "Ratujmy grę{game} — zapisy tylko do {cutoff}" are
  two of five `headline` variants of the invite message (with "{name} zaprasza do gry", "{name} jest
  w grze i szuka jeszcze graczy"), followed by lines "Brakuje {count} osób", "Zrzucamy się po {fee}
  {currency}/os.", "Zapisy do {cutoff}" and the call "Dołącz:". The same text block holds the WhatsApp
  messages ("Cześć! Gramy razem w {when} 🎾"). [Playmore strings: reservations](https://playmore.pl/assets/93jAIRDY.js),
  [same, newer chunk](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- *Reading:* the two lines are the opening of a message a player shares; they are not a push Playmore
  sends.

### Playmore pushes "brakuje 1" to the players already in the game, to make them invite
- **[POLICY]** Flag `open-game-join-invite` (active, 100 % in four clubs since 27 Sep 2026): after paying
  for a seat in someone else's game the joiner gets the sheet "Jesteś w grze! 2/4 · brakuje 2" with
  WhatsApp, Share, Buddies and Copy link; "tap w push „brakuje 1” otwiera ten arkusz (`surface=nudge`)".
  The sheet's titles are "Brakuje 1 do Waszej gry" / "Nikt jeszcze nie dołączył" and "Wyślij znajomym
  link — zapiszą się do gry sami." [Playmore flag notes](https://playmore.pl/assets/D_jVwDzs.js),
  [strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- *Reading:* the "one missing" push goes to members of the game ("Waszej gry", your game, plural) and
  asks them to recruit; it is not sent to outsiders.

### Playmore's game alerts fire when a game is created, not when its last seat is left
- **[POLICY]** "Daj znać o grach w {venue} — Jeden tap. Powiadomimy Cię, gdy ktoś założy grę w tym
  klubie." (web: "Damy znać w apce Playmore i w dzwonku na koncie, gdy ktoś założy grę"). Alerts are
  set by sport and daypart ("W dzień (pn–pt 9–16)", "Wieczorem", "W weekend"); a counter shows
  "{count} osób dostaje już alerty o grach w tym klubie". The creator's success sheet promises
  "powiadomimy N osób". [strings](https://playmore.pl/assets/Ct1XsxUt.js), [flag notes: `looking-for-game-alerts`, `open-game-creator-success`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[POLICY]** A full game's reserve list: "Gdy zwolni się miejsce, powiadomimy wszystkich z listy naraz
  — kto pierwszy, ten gra." (flag `open-game-waitlist`, ramping to four clubs on 20 Oct 2026).
  [flag notes](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[ABSENT]** Any push about a game's last seat to alert subscribers or to anyone outside the game:
  searched the strings and the 95 flag notes for "ostatnie miejsce", "lastSpot", "brakuje 1", "atRisk",
  "Ratujmy" — the hits are the share texts, the card label "Ostatnie miejsce" and the members' nudge
  above. [flag notes](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- *Reading for R-SWIPE-13:* Playmore pushes the gap to the people in the game and leaves it to them to
  forward; nobody named in advance is told "a game needs only you", because Playmore names nobody.

### Playmore greets the organiser with "Ktoś dołączył do Twojej gry" on the booking
- **[POLICY]** The organiser's booking details carry a section (component `OpenGameGreetingSection`,
  props `reservation` and `organizerGame`) titled "Ktoś dołączył do Twojej gry", "Przywitaj się - to
  pierwsza rzecz, jaką ta osoba usłyszy od Ciebie.", with one "Przywitaj" button per new joiner and
  three ready lines ("Super, że dołączasz - do zobaczenia! 👋"). [strings](https://playmore.pl/assets/Ct1XsxUt.js),
  [component](https://playmore.pl/assets/CSB8J-_f.js) — read 2026-10-08
- **[POLICY]** Members of a game are told when it fills: league pushes "Komplet w Waszej grze" and
  "Mecz potwierdzony" open a sheet for "członek składu" (flag `open-game-filled-moment`, 100 % since
  26 Sep 2026: "push „Komplet” (PLA-4822) wychodzi we wszystkich klubach od 25.09"). The roster's
  contacts section says "Ktoś się wypisał — w składzie zwolniło się miejsce." after a leave.
  [flag notes](https://playmore.pl/assets/D_jVwDzs.js), [strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[POLICY]** Push categories a player can mute: "rezerwacje, zajęcia, liga, społeczność, komunikaty
  klubu", shown as "Rezerwacje i Twoje gry" and "Społeczność i alerty o grach"; game pushes are
  "transakcyjne pushe gier → reservation". [flag notes: `push-category-prefs`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[ABSENT]** A push to every member of the game, or to alert subscribers, for each single join: the
  greeting is for the organiser, the push on a full game for the members. Searched strings and flags
  for "dołączył", "greeting", "joined". — read 2026-10-08
- *Reading for R-SWIPE-15:* "Ktoś dołączył" reaches the game's organiser (who can greet the joiner);
  the rest of the game hears when it is full.

### Neither Playmore nor Playtomic redraws a roster live
- **[POLICY]** Playmore's open-game screens run only clock timers: the countdown strip re-reads the time
  every 30 s (`setInterval(…, 3e4)` setting `Date.now()`), class openings every 60 s; data is re-read
  when the app returns to the front ("[RefetchOnFocus]" on `appStateChange` / `visibilitychange` /
  `focus`) and by pull-to-refresh (flag `native-pull-refresh`: "Natywne „pociągnij, żeby odświeżyć”").
  [open-games code](https://playmore.pl/assets/DGQrxHKX.js), [network layer](https://playmore.pl/assets/Cng0yjU9.js),
  [flag notes](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[ABSENT]** A socket, server-sent events or a polling interval on Playmore's open-game data: searched
  the chunks that call `/open-games` for `setInterval`, `refetchInterval`, `WebSocket`, `EventSource`;
  every interval found sets a clock. — read 2026-10-08
- **[ABSENT]** Playtomic: no help article says the match page updates as players join; all 94 player
  articles searched for "refresh", "real time", "live", "update". [Playtomic player help](https://playerhelp.playtomic.com/hc/en-gb) — read 2026-10-08
- The same finding, read from the list loader itself, is in
  `topics/gaps-PLATFORM.md#playmores-open-game-list-is-not-refreshed-while-it-is-on-screen` and
  `topics/gaps-RESCUE.md#playmore-reads-its-open-games-list-when-the-page-opens-and-after-the-players-own-actions`.
- *Reading for R-SWIPE-14:* the rivals refresh on open, on return and on a pull, which is where Raketa
  is today; a tile turning In as it happens would be ahead of them, and level with a WhatsApp poll.

## 2. A no, and taking an answer back (R-SWIPE-9)

### Playtomic tells a player to leave a match and join it again
- **[POLICY]** "If you joined a match before having a level, you may need to leave the match, complete
  the initial level questionnaire to get your level, and then join again (if the match is still
  available)." [Playtomic help: How the Playtomic level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works) (updated 2026-10-07) — read 2026-10-08
- **[POLICY]** No cancellation fee on open matches: "It will not be applied to open matches, leagues,
  tournaments, and classes" (Poland's fee on player bookings is 4,32 PLN). [Playtomic help: Cancellation fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831791848721-Cancellation-fee) (updated 2026-07-20) — read 2026-10-08
- *Reading:* leaving and rejoining an open match is possible while it has a seat; this replaces the
  earlier *Rejoining after leaving is not described* (`topics/competitor-joiner.md`). Playmore has no
  rule against rejoining either, and no platform offers an undo on leaving:
  `topics/gaps-LEAVE.md#playmore-has-no-rule-against-a-former-player-rejoining-an-open-game`,
  `topics/gaps-LEAVE.md#no-platform-offers-an-undo-on-leaving`.

### Tinder lets a subscriber take back the last swipe, a no included
- **[POLICY]** "The Rewind option lets you take back your last Like or Nope. If you accidentally passed
  on someone you wanted to get to know, they're no longer lost in the Tindersphere™ forever … Only
  Tinder subscribers can take back their last SWIPE of choice (Like, Nope, Super Like)."
  [Tinder help: Rewind](https://www.help.tinder.com/hc/en-us/articles/115004493323-Rewind) (updated 2026-10-01) — read 2026-10-08

### The racket swipe decks say nothing about taking a pass back
- **[ABSENT]** Undo, rewind, or a passed player coming back: Noavo (v1.0.6; Premium sells "more swipes"),
  Padelbuddy, Quadra (v1.1.1) App Store listings. [Noavo](https://apps.apple.com/pl/app/noavo/id6764517766),
  [Padelbuddy](https://apps.apple.com/gb/app/padelbuddy-padel-partner/id6759984156),
  [Quadra](https://apps.apple.com/gb/app/quadra-find-matches-nearby/id6758919221) — read 2026-10-08

## 3. A seat for a named player who has not answered (R-SWIPE-12)

### Spond: invitees hold nothing on a capped event, first come first served
- **[POLICY]** "When you select 'Max number' it's 'First come, first served'. When the number of
  participants is full, the next people who sign up will be put on a waiting list." "If someone
  withdraws before the deadline, the first person on the waiting list will receive a push notification
  … if the first person declines, the second person on the waiting list will receive the offer."
  Reminders go "to participants who haven't responded … 48 hours after the invitation is sent or 48
  hours before the event starts." [Spond help: Features in events](https://help.spond.com/app/en/articles/129730-features-in-events) (dated 2026-04-21) — read 2026-10-08

### Playtomic: a friend the owner adds to a private booking takes the seat without answering
- **[POLICY]** The owner adds friends "before completing your payment" or after, by name, email or
  phone; "If you're the only one in the booking, only two out of three empty places will appear active
  … The fourth place will activate once there are three players in the match." [Playtomic help: Add my friends to a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/43212099147025-Add-my-friends-to-a-reservation) (updated 2026-05-31) — read 2026-10-08
- **[POLICY]** In a split-payment booking the owner's card is the guarantee: "If any player does not pay
  their share within 2 hours after the end of the match, an automatic charge will be made to your Card
  on file". [Playtomic help: Card on File in split payments](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457-Card-on-File-CoF-in-split-payments-what-it-is-and-how-it-works) (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** "Add my partner" pays both seats at once; "Invitation and payment for the other player
  can only be done when you join." [Playtomic help: Add My Partner](https://playerhelp.playtomic.com/hc/en-gb/articles/19831380139793-Add-My-Partner) — read 2026-10-08
- *Reading:* where a named seat is kept, somebody pays for it (the owner's guarantee, the partner's
  fee); where nobody pays (Spond, Playtomic's spot request), the first answer takes it.

### No app keeps a named seat open on a timer
- **[ABSENT]** An invite that holds a seat for a set time and then frees it: Playtomic player help
  ("invitation", "reserved for", "hold … spot"), Spond help, Playmore strings ("zaproszenie"), and a web
  search for padel invite holds; the PlayByPoint club pages found describe "add players" with no hold.
  [RAD Padel on PlayByPoint](https://app.playbypoint.com/f/radpadel/pages/how-to-book-a-court) — read 2026-10-08

## 4. A block between two people already in one game (R-SWIPE-19)

### Playtomic's current block rule covers joining only
- **[POLICY]** "Block - Choose this if you want to prevent any future interactions with this player …
  if someone in an Open Match has blocked a player, that blocked player will not be able to join the
  match. This also applies to: Open Matches Private Bookings Community Matches." The club-help copy
  says the same. [Playtomic help: How to block and/or report a Player](https://playerhelp.playtomic.com/hc/en-gb/articles/19831797811729-How-to-block-and-or-report-a-Player) (updated 2026-04-23),
  [Playtomic Manager help: How to block a user (App only)](https://helpmanager.playtomic.com/hc/en-gb/articles/20535339424529-How-to-block-a-user-App-only) (updated 2026-07-20) — read 2026-10-08
- *Unverified:* a web search's summary of the club-help URL quoted "Keep in mind that blocking a player
  won't affect open matches. If players sign up for an open match, it will still be visible to
  everyone, including the player they blocked." The current text of that article (read through its
  API) does not contain it, so it is not used as a fact.
  [helpmanager article 20535339424529](https://helpmanager.playtomic.com/hc/en-gb/articles/20535339424529) — read 2026-10-08
- What a block does to a chat and a shared group (Playtomic, WhatsApp, Meetup) is in
  `topics/gaps-ENGINE.md#playtomic-a-block-is-to-prevent-any-future-interactions` and the sections after it.
- **[ABSENT]** What happens when the two are already in the same match: none of the 94 player articles
  or the two block articles says; Playtomic's own route to take a player out is the club's "Remove
  participant", refunded to the original payment method. [Playtomic Manager help: How to add/remove players in an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535085001361-How-to-add-remove-players-in-an-Open-Match) (updated 2026-09-09) — read 2026-10-08
- **[ABSENT]** A player-to-player block in Playmore: no "Zablokuj" or blocked-players string in the web
  app; the only refusal is the club's: "Nie możesz zapisać się na grę w tym klubie. Skontaktuj się z
  recepcją." [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- *Reading:* on Playtomic a block placed after both joined leaves both in the match, as far as anything
  written shows; a player who wants out leaves (free while the match isn't full).

## 5. When the answer meets the network (R-SWIPE-30, R-SWIPE-31)

### Playmore says the outcome is unknown and tells the player to check before paying again
- **[POLICY]** Playmore's copy for an unconfirmed outcome: "Płatność mogła się rozpocząć. Sprawdź status
  rezerwacji, zanim zapłacisz ponownie."; "Nie mamy jeszcze potwierdzenia płatności Apple Pay — może to
  potrwać do 15 minut. Zanim spróbujesz ponownie, sprawdź swoje rezerwacje."; "Wciąż nie mamy
  potwierdzenia płatności Apple Pay. Jeśli bank pokazuje obciążenie, nie płać ponownie — udział opłaci
  się sam. Jeśli nie, możesz zapłacić jeszcze raz."; at a lapsed payment "Nie udało się potwierdzić
  statusu rezerwacji. Odśwież stronę za kilka minut lub skontaktuj się z obiektem."; a slow server
  "Serwer nie odpowiada. Sprawdzamy połączenie…". [Playmore strings: main](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[ABSENT]** A Playmore or Playtomic line for an open-game join that timed out: the join errors are
  "Nie udało się zapisać na rezerwę. Spróbuj ponownie.", "Ta gra nie jest już dostępna.", "Jesteś już w
  tej grze."; Playtomic help has none. [strings](https://playmore.pl/assets/93jAIRDY.js), [Playtomic player help](https://playerhelp.playtomic.com/hc/en-gb) — read 2026-10-08
- *Reading for R-SWIPE-30:* the stated rule in the market is "we don't know yet — check before you try
  again", never "it failed".

### Playmore refuses a write while offline; it never queues one
- **[POLICY]** Playmore's web app rejects every POST, PUT, PATCH and DELETE while the phone is offline
  (error `ERR_OFFLINE_BLOCKED`, "Network offline — write blocked") and shows "Brak połączenia z
  internetem. Spróbuj ponownie, gdy wróci zasięg."; reads time out after 15 s
  (`Sn=15e3`) and fall back to "Dane mogą być nieaktualne — … Pokazujemy ostatnią zapisaną wersję
  ({time})"; an offline banner reads "Brak połączenia z internetem". [network layer](https://playmore.pl/assets/Cng0yjU9.js),
  [strings](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08

### Android's guidance: queue only what need not reach the server, store critical writes locally
- **[DOCS]** Online-only writes are for transactions "that must happen online in near real time—for
  example, a bank transfer … you can opt not to present a UI … or … notify the user that they are
  offline." Queued writes ("drain the queue with exponential backoff … persistent work … delegated to
  `WorkManager`") suit cases where "It's not essential that the data ever be written … not time
  sensitive … not essential that the user be informed if the operation fails." Lazy writes, stored
  locally first, are "the correct choice when the data is critical". [Android Developers: Build an offline-first app](https://developer.android.com/topic/architecture/data-layer/offline-first) (updated 2026-05-13) — read 2026-10-08
- **[ABSENT]** A booking or swipe app that keeps an answer given offline and sends it later: Playmore
  (above), Playtomic help ("offline", "connection"), the swipe-deck listings. The familiar case is a
  WhatsApp message waiting behind its clock, sent on reconnect (official FAQ not readable; see
  `topics/gaps-FILL.md#whatsapp-queues-a-message-typed-offline-and-sends-it-on-reconnect` and
  `topics/gaps-FILL.md#no-consumer-booking-or-payment-app-keeps-a-join-made-offline`). — read 2026-10-08
- *Reading for R-SWIPE-31:* the one rival that decided this (Playmore) refuses the tap offline and says
  so; Raketa's held answer is closer to a WhatsApp message waiting to send, and Google classes an
  answer that may charge money with bank transfers (online-only), not with queued writes.

## 6. What the club sees of a game forming at its courts (R-SWIPE-1)

### Playmore: the club watches open games and joiners, and runs none of them
- **[POLICY]** "Ty włączasz funkcję i ustawiasz zasady … Poza ustawieniami masz tylko podgląd gier -
  żadnej z nich nie obsługujesz."; "Zero pracy recepcji - Ty masz tylko podgląd."; "Recepcja nie
  kiwa palcem."; "Powiadomienia o dołączeniu, potwierdzeniu i anulacji idą automatycznie."
  [Playmore: Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-08
- **[POLICY]** A new player joining by SMS code is told "Klub zobaczy, kto dołącza do gry."; a club can
  bar a player from its games: "Nie możesz zapisać się na grę w tym klubie. Skontaktuj się z
  recepcją." The court is held as the organiser's booking from publication
  (`platforms.md#playmore--the-court-is-held-from-publication`). [strings](https://playmore.pl/assets/Ct1XsxUt.js),
  [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playtomic: the club sees every open match and can cancel it, remove a player or assign a court
- **[POLICY]** "Open matches are automatically managed by Playtomic Manager … You do not need to
  actively create open matches". Under *Matches* the club filters "by venue, match type, status, or
  court type"; it can cancel a confirmed match ("All players will be refunded automatically"), remove
  a player once the player's own window has passed ("Remove Participant"), and "+Add Court", which
  "will reserve the court in your schedule, even if no players have enrolled yet." [Playtomic Manager help: How to manage Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353-How-to-manage-Open-Matches-in-Playtomic-Manager) (updated 2026-09-09) — read 2026-10-08
- **[POLICY]** The club can also add a participant, who is pushed to pay in the app or owes a debt.
  [Playtomic Manager help: How to add/remove players in an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535085001361-How-to-add-remove-players-in-an-Open-Match) — read 2026-10-08
- *Reading:* both rivals show the desk the games forming at its courts; Playtomic lets it act on one,
  Playmore deliberately does not.

## 7. A cap on games at once (R-SWIPE-21)

### Playtomic's cap is the club's, per venue, and may be left blank
- **[POLICY]** Club booking rules: "Maximum Bookings/Day … you can set a limit on how many
  reservations a player can make in one day. You can either set a number or leave the box empty for no
  limit. Number of Active Bookings … how many future reservations a player can have at once. You can
  set a limit or leave the box empty for no restriction." Category and membership rules can override
  them ("Maximum bookings/day", "Active bookings"). [Playtomic Manager help: Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297-Reservation-rules) (updated 2026-06-22),
  [Club Membership Feature](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745-Club-Membership-Feature) (updated 2026-09-13) — read 2026-10-08
- **[POLICY]** Premium's benefits, as Playtomic lists them to players and to clubs: zero commissions,
  advanced statistics, level graphs, "unlimited custom alerts", Golden Matches. No match limit is
  named or lifted. [Playtomic help: Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited) (updated 2026-09-30),
  [Playtomic Manager help: Premium Plan for players](https://helpmanager.playtomic.com/hc/en-gb/articles/20534670300561-Playtomic-Premium-Plan-for-players) (updated 2026-06-26) — read 2026-10-08
- **[ABSENT]** A Playtomic-wide two-game cap for free accounts: 94 player and 157 club articles, the
  Premium pages, and a web and Reddit search ("2 matches", "two matches", "limit") — read 2026-10-08
- *Reading:* the reported "only 2 games … at any one time" (`competitor-newcomer.md#how-many-games-at-once`)
  matches a club's "Number of Active Bookings" set to 2, not a Playtomic rule.

## 8. One player in two games at one hour (R-SWIPE-23, R-SWIPE-24)

### Playmore marks an hour where the player already has something, at any club, and does not refuse
- **[POLICY]** On the booking grid a marker reads "Masz już termin: {details}. Pokaż szczegóły"; the
  sheet "Twoje terminy" lists the player's games, trainings and league matches, with "Inny klub:
  {venue}" for one elsewhere, and "Zobacz moje rezerwacje". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** A Playmore refusal of an overlapping booking or join: searched strings for "w tym samym
  czasie", "o tej samej godzinie", "nakłada się", "koliduje" — the only hits are a trainer's grid gap
  warning. — read 2026-10-08

### Clubs on CourtReserve ask to stop members booking two things at once
- **[COMPLAINT]** Club admins' feature request (17 votes): "prevent a member from registering for an
  event at the same time they have an active court reservation … Folks can't be two places at once …
  we don't have the staff to monitor where they are"; status "Accepted for Future Development"
  (24 Dec 2024), then "Waiting on Votes" (29 Oct 2025); a club user notes a "concurrent court
  reservation" limit exists for courts but "no such equivalent limitation exists" for events
  (8 Apr 2026). A second request: "Players can be blocked by booking a 2-hour reservations back to back
  and same with the open play" (23 Jun 2026). [CourtReserve feedback #1738](https://feedback.courtreserve.com/communities/1/topics/1738-prevent-players-from-double-booking-themselves),
  [#3309](https://feedback.courtreserve.com/communities/1/topics/3309-prevent-players-booking-a-court-reservation-and-open-play-consequently-or-vice-versa) — read 2026-10-08

### How often a Kraków player holds two clubs at one hour
- **[ABSENT]** Any count, survey or club statement for Kraków (or Poland) on one person holding two
  bookings at the same hour at two clubs, or a Kraków desk checking for it: club regulations found by
  search (Poznań POSiR, Jelenia Góra, Gdynia, Żory) limit unpaid debts and fixed slots, not overlaps;
  tenis4U and kluby.org publish no overlap rule (`platforms.md`); Playmore only marks it (above).
  Desks see one club's calendar, so a clash across two clubs cannot reach them. — read 2026-10-08

## 9. A swipe or "I'm in" as the control that binds to pay (R-SWIPE-27, R-SWIPE-32)

### Still no authority on a swipe; the Dutch Supreme Court rejects generic order labels
- **[LAW]** Art. 17 ust. 3 covers "przycisk lub podobna funkcja", so a gesture that places an order is
  inside the rule; no UOKiK, Polish, CJEU or German authority on a swipe or a priced "I'm in" — see
  `topics/gaps-FILL.md#no-authority-on-a-swipe-or-a-priced-im-in-as-the-order-control` (read
  2026-10-08), not repeated here.
- **[LAW]** Hoge Raad (Netherlands), two rulings of 4 Oct 2024: buttons reading "place order", "order"
  or "complete order" do not meet the Dutch rule taken from art. 8(2) of the Consumer Rights
  Directive; the consumer's contract may be annulled in full or in part (a one-third reduction treated
  as reasonable in principle). One case concerned a course provider's "schrijf je nu in" ("sign up
  now") button; the summary does not say how that label was judged. [CMS: Netherland's Supreme Court rulings shake up Dutch e-commerce (9 Oct 2024)](https://cms.law/en/nld/legal-updates/netherland-s-supreme-court-rulings-shake-up-dutch-e-commerce-what-you-need-to-know) — read 2026-10-08
- *Unverified:* a Bird & Bird note titled "The Netherlands: New EU Withdrawal Button Requirement and
  CJEU Referral on Order Button Compliance" reports a further Dutch referral to the CJEU on the order
  button (6 Jan 2026, per a search summary); the page returned 403 and no case number or outcome was
  found. [Bird & Bird](https://cm.twobirds.com/en/insights/2026/netherlands/the-netherlands-new-eu-withdrawal-button-requirement-and-cjeu-referral-on-order-button-compliance) — read 2026-10-08
- *Reading:* the closest rulings say a label must name payment; a sign-up word ("Dołączam", "I'm in")
  has never been accepted anywhere as that.

## 10. The payer's 8-week refund on a share charged days after a paused yes (R-SWIPE-18)

### The refund right needs an authorisation without an exact amount, and a surprise
- **[LAW]** PSD2 art. 76(1), which the Polish act transposes (`local-market.md#the-payers-8-week-refund-right-on-a-charge-they-didnt-trigger`):
  a refund of a payee-initiated payment "if both of the following conditions are met: (a) the
  authorisation did not specify the exact amount of the payment transaction when the authorisation
  was made; (b) the amount … exceeded the amount the payer could reasonably have expected taking into
  account the previous spending pattern, the conditions in the framework contract and relevant
  circumstances of the case. At the payment service provider's request, the payer shall bear the
  burden of proving such conditions are met." Art. 77: request within 8 weeks of the debit; the bank
  refunds or justifies a refusal within 10 business days. The unconditional 8-week refund is for SEPA
  direct debits only. [Directive (EU) 2015/2366, art. 76–77 (EN)](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32015L2366),
  [PL](https://eur-lex.europa.eu/legal-content/PL/TXT/HTML/?uri=CELEX:32015L2366) — read 2026-10-08
- **[DOCS]** The EU's new Payment Services Regulation was agreed on 27 Nov 2025 and its final compromise
  texts published on 23 Apr 2026; it applies only after adoption and a transition. The Commission had
  proposed an unconditional 8-week refund for every merchant-initiated payment; Parliament's text kept
  it for direct debits only; how the final text settles card-on-file charges was not found.
  [Arthur Cox via Mondaq (23 Apr 2026)](https://www.mondaq.com/ireland/financial-services/1782218/psd3-and-psr-final-compromise-texts-published),
  [AmCham EU](https://www.amchameu.eu/node/16644),
  [joint industry statement, Nov 2025](https://www.eurocommerce.eu/app/uploads/2025/11/joint-industry-statement-psr-refund-rights-final.pdf) — read 2026-10-08
- **[ABSENT]** A ruling, KNF/UOKiK statement or Rzecznik Finansowy position on whether an amount shown on
  the screen at the tap (rather than in the card authorisation) is "the exact amount", or whether a
  charge days later is beyond what the payer "could reasonably have expected" — searched EUR-Lex, the
  EBA Q&A tool (results on art. 76 are about SCA on refunds), rf.gov.pl via web search. — read 2026-10-08
- *Reading:* with 35 zł shown on the card and saved-card terms naming the charge, condition (b) is
  hard for the player to prove, so the statutory refund probably does not reach the share; the card
  dispute below is the route left.

## 11. What wins a Polish card dispute on a share charged without the player (R-SWIPE-27)

### Stripe: fraud disputes are hard to win, and an off-session charge has no 3-D Secure shift
- **[DOCS]** "Because fraud disputes are so difficult to win, prevention is key"; to overturn one, show
  the cardholder made the payment, that it was authenticated with 3-D Secure, a refund, or a
  withdrawn dispute. For an "Offline service" ("event tickets and reservations, where evidence of a
  cancellation policy can be material"): proof the cardholder used the service, "a signed contract,
  work order, or other form of written agreement", "Evidence of one or more non-disputed payments on
  the same card", and for recurring payments "a legally binding contract … and of any previous
  payments not disputed". [Stripe: Dispute categories](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[DOCS]** "not all transactions support 3DS, for example wallets or off-session payments"; the
  liability shift "typically applies to payments successfully authenticated using 3DS". [Stripe: Authenticate with 3D Secure](https://docs.stripe.com/payments/3d-secure/authentication-flow) — read 2026-10-08
- **[DOCS]** A merchant-initiated charge needs a recorded agreement naming the transactions, timing,
  how the amount is set and the cancellation policy (`local-market.md#charging-a-saved-card-without-the-player-there`;
  `topics/gaps-FILL.md#what-stripe-says-the-saved-card-terms-must-name`).

### mBank: a charge "for a service you did not order" is a chargeback ground
- **[POLICY]** Grounds include a paid service "nie zostały do Ciebie dostarczone", a settlement of a
  transaction "przez Ciebie anulowana", and a hotel or rental that "pobrały z Twojej karty pieniądze
  za usługę, której nie zamawiasz"; report "jak najszybciej"; the merchant answers through Visa or
  Mastercard with a re-presentment, and with none in time the complaint is accepted.
  [mBank: chargeback Q&A](https://www.mbank.pl/indywidualny/karty/pytania-i-odpowiedzi/chargeback/) — read 2026-10-08
- **[ABSENT]** A Polish ruling, Rzecznik Finansowy report or bank statement on a card-on-file charge
  made after a free in-app yes, or on a recorded tap with the price shown as evidence. — read 2026-10-08
- *Reading:* the evidence that counts is the player's own record: the yes with its time and price, the
  saved-card terms they accepted, the booked game, and that they came; a "not ordered" claim is the
  ground a paused yes that returns days later invites.

## 12. Players with no card they would use online (R-SWIPE-4)

### The nearest figures are national, not padel and not Kraków
- **[DOCS]** About 19 % of Polish adults used no debit card in the past year (Global Findex 2025) — see
  `topics/gaps-PAY.md#how-many-poles-use-a-card-at-all-and-pay-online`, not repeated here.
- **[DOCS]** Tpay's 2026 report: "40 proc. konsumentów rezygnuje z zakupów, jeśli w sklepie internetowym
  zabraknie ich ulubionej metody płatności." [wiadomoscihandlowe.pl, 22 Apr 2026](https://www.wiadomoscihandlowe.pl/retailtech-i-nowe-technologie/tpay-pokazuje-zwyczaje-polakow-w-temacie-platnosci-2534453) — read 2026-10-08
- **[ABSENT]** The share among Kraków padel players: no survey of racket players' payment methods was
  found; Tpay 2026's PDF could not be read as text. — read 2026-10-08

## 13. Leaving a group or a club's community, and the matches already joined (R-SWIPE-34)

### Neither Playtomic's groups nor MATCHi's communities are tied to a match
- **[POLICY]** Playtomic chat groups: the admin can "add or remove participants" and "share the link of
  the group to promote your matches"; nothing links a match to a group
  (`competitor-organiser.md#playtomic-groups-are-chat-groups-not-game-pools`). [Playtomic help: How to create a chat group](https://playerhelp.playtomic.com/hc/en-gb/articles/19831494082705-How-to-create-a-chat-group) — read 2026-10-08
- **[POLICY]** MATCHi Communities: members "leave the community whenever they like"; "A player who leaves
  voluntarily still sees the community … they can rejoin anytime"; "Removing a customer from the Group
  also removes them from the community"; nothing is said of their bookings or matches. [MATCHi: Communities](https://matchi.zendesk.com/hc/en-gb/articles/36758141080093-Communities) (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** Playmore's club "community" is a list of outside links (WhatsApp, Facebook, Instagram,
  Telegram, Discord) under "Dołącz do naszej społeczności!". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** Any rival where leaving a group takes back a seat or a pending answer: on all three a
  match is joined and paid by the player, so leaving a group touches nothing. How long Raketa's own
  passing-on of a leaving takes is a code fact, not a market one; no measurement in practice was
  found. — read 2026-10-08
