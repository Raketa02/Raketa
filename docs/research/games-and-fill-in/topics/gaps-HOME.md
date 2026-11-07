# Gap answers — HOME (Home, a game's details, the game's chat)

Answers to the missing facts listed for the HOME rules (R-HOME-3, 4, 6, 14, 18, 19, 21, 22, 23, 25,
36, 37, 41). All read **2026-10-08**. Facts already in the other topic files are cited, not repeated.

**Sources and how they were read.**
- **Playtomic:** its two Zendesk help centres read whole through their public API (94 player and 157
  club articles, each with its own "updated" date); the interface text of the Android app 6.93.2
  (package `com.playtomic`, XAPK from APKPure, 2026-10-08), read as key and text from its
  `resources.arsc`, with the lines used saved in
  [`../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt`](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt);
  the App Store listing (6.93.2, released 2026-10-07) and its screenshots; App Store reviews from ten
  countries (1,737 reviews, RSS feeds).
- **Playmore (Reservise):** the interface text and code its web app serves to every visitor
  (`playmore.pl/assets/*.js`), which is the same code its iOS and Android apps wrap. Chunk names are
  content hashes and change when Playmore deploys, so the excerpts used are saved in
  [`../shots/gaps-HOME-playmore-tenis4u-web-strings.txt`](../shots/gaps-HOME-playmore-tenis4u-web-strings.txt).
  Part of that code is Playmore's own feature-flag register, with dated notes on what each feature does.
- **tenis4U:** the code of its web app, `app.tenis4u.pl` (same evidence file).
- **WhatsApp:** its help centre and blog. The help pages draw their text with a script, so their wording
  was read through the search engine's copy of the page; the links are the pages themselves.
- **Kraków clubs:** Playmore's public club pages and the clubs' own rules.

**Not used.** No account was opened on Playtomic or Playmore, so nothing here is `[MEASURED]`: watching
a list while another player joins, or opening it in airplane mode, needs an account with a paid seat,
and Playtomic has no Kraków club. No video walkthrough of either app's own-games screens was found.

**Kinds:** `[POLICY]` the company's own rule, help or interface text · `[DOCS]` a provider's document ·
`[COMPLAINT]` one person's account · `[ABSENT]` looked for and not found, with where. Lines marked
*reading* are not sources.

## 1. What a player's own list marks as waiting on her (R-HOME-3)

### Playmore: the bookings tab's badge counts unpaid bookings only
- **[POLICY]** The bottom bar's *Rezerwacje* tab carries a number read out as "nieopłacone rezerwacje:
  {count}"; the bell has its own "nieprzeczytane: {count}". The bar's tabs are *Mój klub*, *Szukaj*,
  *Twoje obiekty*, *Rezerwacje*, *Konto*. [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js),
  [App Store PL screenshot](https://apps.apple.com/pl/app/reservise-playmore/id928403015)
  ([saved](../shots/gaps-HOME-playmore-appstore-qr-checkin.png)) — read 2026-10-08
- **[ABSENT]** A badge or count for a result to enter, a result to confirm or an open seat (searched the
  strings for tab and badge keys). [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### Playmore: each booking tile carries its own pills
- **[POLICY]** On *Moje rezerwacje* a tile shows a payment pill ("Opłacone" / "Nieopłacone", or pay at
  the club), a cancellation pill ("Anulowane", "Anulowane nie na czas"), a won or lost mark, the kind
  ("Gra otwarta", "Turniej"), "Organizator" when she organised it, and one action pill: "Po meczu", or
  "Wpisz wynik" / "Potwierdź wynik" when a result waits on her. A filter offers "Tylko nieopłacone".
  [list code](https://playmore.pl/assets/Du2k_EAD.js), [strings](https://playmore.pl/assets/CccZ1mLc.js),
  [open-game strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08

### Playmore: the club home lists the results waiting on her
- **[POLICY]** *Mój klub* shows "Najbliższa rezerwacja" with "Zapłać", and a section "Wyniki meczów do
  uzupełnienia" with rows "Rozegrany mecz", "Wynik do potwierdzenia" and "{opponent} wpisał wynik —
  sprawdź i potwierdź." The app's home has "Twój plan" rows with "Zapłać", "Nawiguj", "Kalendarz" and an
  "Odwołane" badge. [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### Playmore: an open seat shows only inside the booking
- **[POLICY]** The booking's ticket reads "Skład {current}/{limit}", "wolne: {count}" and "Zaproś
  graczy, wolne: {count}"; a sheet says "Brakuje {count} do Waszej gry". Nothing on the tile or the tab
  counts an open seat. [strings](https://playmore.pl/assets/CccZ1mLc.js),
  [open-game strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08

### Playtomic: Home's "Don't forget" section lists what waits on her
- **[POLICY]** Home has a section titled "Don't forget" whose items include "Upload score", "Confirm
  result", "Pending payment", "Pending payments" (a partner has not paid), "Place request pending",
  "Place request accepted!", "Approve place requests", "Request league match reschedule", "Confirm
  payment now", "Payment failed" and "Edit your player preferences". No item is about a free seat in her
  match. [Playtomic Android 6.93.2 strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt)
  ([Google Play](https://play.google.com/store/apps/details?id=com.playtomic)) — read 2026-10-08
- **[POLICY]** "Open the app and go to Home. In the Don't forget section, tap Pending payment." "The
  payment shows in Don't forget for 15 days after the tournament ends." [Playtomic: How to join a
  Tournament](https://playerhelp.playtomic.com/hc/en-gb/articles/19831745721617) (updated 2026-10-07) —
  read 2026-10-08
- **[POLICY]** Club side: "a Pending payment message appears on the app's Home screen"; for a booking
  the club creates, "the player/s will have a notification in the home screen. They need to accept the
  booking". [How to add participants to a
  Tournament](https://helpmanager.playtomic.com/hc/en-gb/articles/48343795791505) (2026-10-07),
  [Recurring booking series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513)
  (2026-06-22) — read 2026-10-08

### Playtomic: Home's "Your next activity" carousel and the counts it shows
- **[POLICY]** "At the top of the Home screen in the Your next activity carousel" sit her coming
  activities; a carousel card can read "Pending payment". The App Store's Home screenshot shows a "32"
  badge on the *Find a match* button and a booked card marked "✓ Booked". [Courses: recurring
  payments](https://playerhelp.playtomic.com/hc/en-gb/articles/19831372854545) (2026-07-01),
  [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt),
  [App Store GB](https://apps.apple.com/gb/app/playtomic/id1242321076)
  ([saved](../shots/gaps-HOME-playtomic-appstore-home.png)) — read 2026-10-08
  - *Reading:* the screenshot does not say what the 32 counts; it sits on the button that finds matches,
    so it is most likely matches on offer, not things waiting on her.
- **[COMPLAINT]** "my next matches selection, horizontal scrolling is an inefficient pattern for mobile"
  (NicknameLoading…, GB, 2024-11-10); "the list of upcoming games … it's fairly small above with a
  horizontal scrolling" (Bongstr, DE, 2025-04-29); "removed upcoming game tabs from the home page"
  (Metallifknca, US, 2024-06-13), later "reinserita ✅" (Davide.pato96, IT, 2024-07-03).
  [App Store reviews feed](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

## 2. A game still filling on her own list (R-HOME-4)

### Playmore: an open game is on Moje rezerwacje from the moment she joins or creates it
- **[POLICY]** A tile is badged "Gra otwarta", plus "Organizator" for its organiser; its ticket reads
  "Gra otwarta", "Skład {current}/{limit}", and a lone organiser's roster reads "Na razie tylko Ty".
  Leaving is done from the booking: "To gra otwarta: zwalniasz miejsce, a gra bez kompletu odwoła się
  automatycznie…"; the organiser gets "Wypisz się z gry" and "Odwołaj grę".
  [strings](https://playmore.pl/assets/CccZ1mLc.js), [list code](https://playmore.pl/assets/Du2k_EAD.js) —
  read 2026-10-08
  - *Reading:* joining is paying at once ([platforms.md](platforms.md#playmore--open-games-each-player-pays-at-join)),
    so the seat is a booking of hers from the first press.

### Playtomic: her matches sit under "Your matches", marked enrolled and paid or pending
- **[POLICY]** The match list has a tab "Your matches" and a "Show canceled matches" switch; a cell reads
  "You are enrolled in this match", "%1$s places left to confirm the match", "Hurry up! Only %1$s
  place/s available" or "This match is full", and each seat "paid" or "pending".
  [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[POLICY]** An organiser finds her own match under "Your Activity, and select Matches". [Community
  Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481) (2026-06-19) — read 2026-10-08
  - *Reading:* the "places left" and "enrolled" lines show a match not yet full is listed to the
    player who holds a seat in it.

## 3. A "new" mark on a game (R-HOME-14)

### Playmore: "Nowa" for 24 hours after a game is created, shown only to people not in it
- **[POLICY]** An open-game card's corner badge is "Twoja gra" for its organiser, nothing for a player
  in it, and "Nowa" for anyone else while the game is less than 24 hours old (864e5 ms from
  `createdAt`). The mark comes from the game's creation time, so it is the same on every phone and every
  account, and it never appears on her own games. [card code](https://playmore.pl/assets/DM7ksFDa.js),
  [open-game strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08

### Playtomic: a "NEW MATCH" tag on the list of matches to join
- **[POLICY]** The App Store screenshot of *Matches — For your level* shows a card tagged "NEW MATCH".
  [App Store GB](https://apps.apple.com/gb/app/playtomic/id1242321076)
  ([saved](../shots/gaps-HOME-playtomic-appstore-new-match.png)) — read 2026-10-08
- **[ABSENT]** What makes a match "new", and any new mark on her own booked games (help centres; Android
  strings for "new", "badge", "unseen"). — read 2026-10-08

### Neither marks her own newly booked game as unopened
- **[ABSENT]** A mark on her own list for a game she has not opened yet, kept per phone or per account, on
  either app (Playmore list code and strings; Playtomic help and Android strings). — read 2026-10-08

## 4. Whether the list and the game's page refresh (R-HOME-18)

### Playmore: Moje rezerwacje is pulled down to refresh
- **[POLICY]** The bookings page sits inside a pull-to-refresh container ("Pociągnij, aby odświeżyć",
  "Puść, aby odświeżyć", "Odświeżanie..."). Since 2026-09-25 iOS uses the system's own pull control,
  which the flag note says sits "tylko nad ekranami z odświeżaniem" (ten screens).
  [list code](https://playmore.pl/assets/Du2k_EAD.js), [strings](https://playmore.pl/assets/CccZ1mLc.js),
  [flag register](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08
- **[POLICY]** A booking being paid updates itself: "Płatność przyjęta — status zaktualizuje się sam. Nie
  płać ponownie." [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[ABSENT]** A timed re-read of the bookings list while it stays open (no interval or return-to-app hook
  in the list's code). The 30-second strip already recorded is a countdown on the open-game card
  ([platforms.md](platforms.md#playmore--the-open-game-card-and-preview)). — read 2026-10-08

### Playtomic: no refresh rule published; players report stale screens
- **[ABSENT]** Pull to refresh or automatic refresh of the match list or match page (251 help articles;
  Android strings: "refresh", "pull", "reload" appear only in the Zendesk support chat). — read 2026-10-08
- **[COMPLAINT]** "Sometimes does not refresh well and needs killing" (NicknameLoading…, GB,
  2024-11-10); a chat push arrives but the message "si aggiorna con 30/40 min di ritardo" (Ciok83, IT,
  2024-09-08). [App Store reviews feed](https://itunes.apple.com/it/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

## 5. Loading and offline (R-HOME-19)

### Playmore: without a connection it shows the last saved list and says how old it is
- **[POLICY]** A banner "Brak połączenia z internetem"; when the server cannot be reached the bookings
  list and Home's "Twój plan" show "Dane mogą być nieaktualne — Nie udało się połączyć z serwerem.
  Pokazujemy ostatnią zapisaną wersję (sprzed {n} min)" with "Spróbuj ponownie"; an action offline gets
  "Brak połączenia z internetem. Spróbuj ponownie, gdy wróci zasięg." While loading: "Ładowanie
  rezerwacji..."; on failure: "Nie udało się pobrać rezerwacji. Spróbuj ponownie."
  [strings](https://playmore.pl/assets/CccZ1mLc.js), [cached-data notice](https://playmore.pl/assets/BtkUyy7P.js),
  [list code](https://playmore.pl/assets/Du2k_EAD.js) — read 2026-10-08
- **[POLICY]** The ticket tells the player to keep a copy: "Zrób screenshot i wyślij znajomym — bilet ma
  wszystko, czego potrzebują"; "Kody do drzwi i kody logowania przychodzą SMS-em zawsze".
  [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### Playtomic: a connection error, and the booking also in an email
- **[POLICY]** Errors read "Could not connect to the server. Check your connection and try again" and, at
  start, "We were unable to connect. Please check your wifi/data connection and try again." Help: "Make
  sure you have a stable internet connection; connect to Wi-Fi if possible."
  [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt), [How to fix app
  issues](https://playerhelp.playtomic.com/hc/en-gb/articles/48990072840721) (2026-07-21) — read 2026-10-08
- **[ABSENT]** What the own-matches list shows offline (no cached-list text in the strings, no help
  article). The court PIN also travels in the booking email
  ([competitor-joiner.md](competitor-joiner.md#the-court-pin-is-in-the-booking-and-its-email)). — read 2026-10-08
- **[COMPLAINT]** "keeps saying no internet connection try again even tought internet is on" (PT,
  2026-07-14); "Dice que no se pudo conectar al servidor y que se compruebe la conexión de Internet"
  (danivibar, ES, 2024-04-02). [App Store reviews feed](https://itunes.apple.com/es/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

### Kraków halls: Wi-Fi at some, a gate that needs the app at one, signal unknown
- **[POLICY]** Fame Sport Club: "Bezpłatna sieć Wi-Fi dostępna na terenie całego obiektu". Bajada
  Sports Club: "recepcja, szatnie z prysznicami i szafkami, WiFi". Garden Padel lists
  "recepcja, szatnie oraz strefa relaksu", no Wi-Fi; Padel House lists no facilities.
  [Playmore: Fame Sport](https://playmore.pl/klub/fame-sport-club-krakow/),
  [Bajada](https://playmore.pl/klub/bajada-sports-club/), [Garden Padel](https://playmore.pl/klub/garden-padel/),
  [Padel House](https://playmore.pl/klub/padel-house/) — read 2026-10-08
- **[POLICY]** SAO Sports Hub (Piastowska): "brama i oświetlenie uruchamiają się przez aplikację
  Tenis4U, brak stałej recepcji". [Playmore: SAO Sports Hub](https://playmore.pl/klub/sao-sports-hub-piastowska-krakow/) — read 2026-10-08
  - *Reading:* at SAO a player without data cannot open the gate herself.
- **[ABSENT]** Mobile signal at any Kraków hall (club pages, rules, PADO listings, web search), and any
  padel venue called "Bonarka Arena" (Playmore's Kraków list has eight clubs, none of that name).
  [Playmore: Kraków padel](https://playmore.pl/padel/krakow/), [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow) — read 2026-10-08

## 6. Unread messages (R-HOME-21)

### WhatsApp: an unread count beside each chat, a badge on the icon, an Unread filter
- **[POLICY]** "In-app notifications include the banner that appears when a message arrives in another
  chat, the unread count next to a chat, and the badge on the WhatsApp icon." [WhatsApp Help: Can't see
  or hear notifications](https://faq.whatsapp.com/655426345948308/) — read 2026-10-08
- **[POLICY]** Chat filters: "Unread: Chats with messages that you mark as unread or haven't opened
  yet." [WhatsApp Help: About chat filters](https://faq.whatsapp.com/1470216183498937/) — read 2026-10-08

### Playtomic: a chat inbox with unread badges; the match page's Chat button has no documented count
- **[POLICY]** The inbox has three parts, *Chats*, *Notifications* and *Clubs*; "Chats from your matches
  and bookings will appear here". The match page has a "Chat" button.
  [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[COMPLAINT]** "I have a badge with four unread messages which doesn't go away" (Cypher21, NL,
  2025-01-30); "Thank you for fixing this annoying iOS bug that didn't remove notification badge inside
  the app once the chat has been seen!" (martin_padel, DE, 2026-05-16); the chat was moved under
  notifications (Dav612, IT, 2024-06-19). [App Store reviews feed](https://itunes.apple.com/de/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08
- **[ABSENT]** A count on the match page's Chat button (help; Android strings: the only unread-count
  strings belong to the Zendesk support chat). — read 2026-10-08

### Playmore: no chat; players are sent to WhatsApp
- **[POLICY]** No in-app chat. A court booking's "Kontakt do graczy — Napisz do osób, z którymi grasz"
  shows the others' numbers on "Pokaż numery", each with a button opening WhatsApp to that person
  (live for all players since a production deploy after 2026-09-03); "Wyślij na WhatsAppie" opens
  WhatsApp with a ready text and no recipient, so the player picks a person or group.
  [open-game strings](https://playmore.pl/assets/Ct1XsxUt.js), [flag register](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08

## 7. When a match chat closes (R-HOME-36)

### Playtomic: no closing time published; the chat is used after the match
- **[ABSENT]** When a match chat stops taking messages (251 help articles; Android strings; web and
  Reddit search). — read 2026-10-08
- **[POLICY]** After a no-show, "We recommend that the attending players write the name of the no-show
  player in the Open Match chat." [No-Show Policy for Open
  Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513) (2026-09-15) — read 2026-10-08
- **[POLICY]** Changing an accepted result needs "A screenshot of the conversation where the other team
  agrees to the change"; "You have up to one week after playing to add a result." [How to edit
  incorrect match results](https://playerhelp.playtomic.com/hc/en-gb/articles/19831850222609) (2026-05-27) — read 2026-10-08
- **[POLICY]** "Once the match is completed, players cannot cancel the spot. If they need to cancel they
  need to contact the club through match chat or telephone." [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
  - *Reading:* the chat still works after the match ends, for days if a no-show or result is argued.

## 8. Whether a message notifies the others (R-HOME-37)

### Playtomic: every match-chat message pushes the other players
- **[POLICY]** "Whenever players get a message—either from the manager or another player—they will get a
  push notification on their phone." [Chat option](https://helpmanager.playtomic.com/hc/en-gb/articles/20535129899921)
  (updated 2026-10-07) — read 2026-10-08
- **[POLICY]** Chat pushes have their own Android notification channel, "Chat"; a chat can be muted
  ("Mute chat") from its options. [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[COMPLAINT]** "The app does not send notifications when someone messages you" (GB, 2024-09-16), already in
  [complaints.md](complaints.md#notifications-missing-duplicated-or-impossible-to-tune).

### WhatsApp: a group rings for every message unless muted or set to Highlights
- **[POLICY]** Muting a group: "You'll still receive messages sent to the group, but your phone won't
  vibrate or make noise when they're received." "Group notifications have their own settings, separate
  from individual chats." [WhatsApp Help: How to mute or unmute group
  notifications](https://faq.whatsapp.com/487825425189091/) — read 2026-10-08
- **[POLICY]** "Use the new 'Notify for' setting and select 'Highlights' to limit notifications for
  @mentions, replies, and messages from saved contacts or 'All' to receive all notifications." [WhatsApp
  Blog, 2025-04-09](https://blog.whatsapp.com/new-feature-roundup-updates-to-group-chats-events-calls-channels-and-more) — read 2026-10-08
- **[ABSENT]** A help page stating the default of "Notify for". — read 2026-10-08

### Playmore: a running-late notice pushes the roster; ready-made messages are still in test
- **[POLICY]** A court booking with co-players has "Spóźnię się" on its page, with a push to the rest
  of the roster; on for every player since 2026-09-07. [flag register](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08
- **[POLICY]** Built for open games but, by the flag note of 2026-09-28, switched on only in Playmore's
  test club, with clubs to follow from about 2026-11-17: "Wiadomość do składu — Gotowe teksty, bez
  pisania. Skład dostanie powiadomienie." Four texts ("Do zobaczenia!", "Wezmę piłki", "Gram tu pierwszy
  raz", "Będę 15 min wcześniej na rozgrzewkę"), each once, up to three per game; refused before the game
  is full or once it starts. Beside it, "Będziesz na grze?" — "Będę" / "Spóźnię się" (5, 10, 15, 15+ min)
  / "Nie dam rady" (which opens leaving); "Twój status zobaczy cały skład tej gry", with a push to the
  roster. No free-text message exists. [open-game strings](https://playmore.pl/assets/Ct1XsxUt.js),
  [flag register](https://playmore.pl/assets/p_SkNwim.js) — read 2026-10-08

## 9. A block when the two already share a match (R-HOME-41)

### Playtomic: a block stops joining and future contact; nothing says it removes anyone
- **[POLICY]** "Block - Choose this if you want to prevent any future interactions with this player."
  "if someone in an Open Match has blocked a player, that blocked player will not be able to join the
  match. This also applies to: Open Matches, Private Bookings, Community Matches". Report sits beside
  Block on the profile. [How to block and/or report a
  Player](https://playerhelp.playtomic.com/hc/en-gb/articles/19831797811729) (2026-04-23) — read 2026-10-08
- **[POLICY]** In a chat: "Remember that you can mute or block the chat if you have any problem." Once
  blocked: "This chat has been blocked", "You have blocked messages from this user"; the other side
  reads "You can't send messages to this user — This chat is currently blocked". A safety filter hides
  flagged messages: "Our safety filter flagged this message. Make sure you trust the sender before acting
  on it." [How you can chat with players in
  Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19832063135249) (2026-02-16),
  [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** Whether a blocked player already in the same match is removed from it, or loses the match
  chat (both help centres; the "Block chat" strings sit in chat options, so they may cover only
  one-to-one chats). — read 2026-10-08

## 10. A club moving a booking (R-HOME-23)

### Playmore: promises to tell players of changes; no move notice found
- **[POLICY]** After booking: "Włącz powiadomienia — damy znać o zmianach w rezerwacji i przypomnimy o
  grze". SMS settings: "Potwierdzenia, przypomnienia i odwołania wysyłamy SMS-em"; with both off, "o
  zmianach w rezerwacjach dowiesz się tylko z aplikacji albo maila". Calendar sync: "Zmiany i odwołania
  nanoszą się same". [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[ABSENT]** The text of a notice for a booking moved to another court or hour (player strings:
  "przenies", "zmiana kortu", "nowy termin"; Playmore's club pages; no public Reservise club help). — read 2026-10-08

### tenis4U: an in-app notification list; no move notice in the player app
- **[POLICY]** The header counts unread notifications. [tenis4U web app](https://app.tenis4u.pl/) — read 2026-10-08
- **[ABSENT]** Any text about a club moving a booking (web-app code; tenis4U and App Store pages; web
  search). — read 2026-10-08

## 11. What the booked game shows about the club (R-HOME-22)

### Playmore: the club's name, logo, street and city, and a map link; no phone
- **[POLICY]** The booking's ticket header shows the club's name and logo, "address, city" and a link to
  OpenStreetMap at the club; the list row has "Nawiguj" and "Kalendarz"; the ticket also has "Kod QR
  rezerwacji" and "Kto gra". No telephone link is on the ticket; *Mój klub* has "Zadzwoń do klubu".
  [ticket code](https://playmore.pl/assets/D-b_RkfX.js), [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### Playtomic: directions and the club's rules on the booking; phone and address on the club's page
- **[POLICY]** Booking details show the club's cancellation policy ("Scroll down to the bottom of the
  screen"); phone, website, address and opening hours are on the club profile's Home tab. A club writes
  a "Public match registration message" (parking, lockers, rental) sent when a player joins.
  [How to modify a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832144958225)
  (2026-05-20), [Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145)
  (2026-07-21) — read 2026-10-08
- **[POLICY]** The app ships a directions icon for matches and a "Directions" button on the club page.
  [Android strings and resources](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** A screenshot of the match page itself showing address, map or phone. — read 2026-10-08

## 12. Whether Kraków desks check players in (R-HOME-25)

### tenis4U: a door code per player, shown just before and during the game
- **[POLICY]** Where the club has a coded lock, the booking shows the player's own code: "Twój stały
  kod, ten sam we wszystkich klubach. Działa tuż przed grą i w jej trakcie"; when live, "Wpisz na
  klawiaturze przy drzwiach. Gdyby nie zadziałał, użyj przycisku „Otwórz drzwi”." Players can also
  switch lights and doors from the booking. [tenis4U web app code](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08
- **[POLICY]** SAO Sports Hub runs with no permanent desk (section 5). Garden Padel's rules take payment
  "online … lub w recepcji" and say nothing of checking in. [Garden Padel regulamin §4](https://gardenpadel.pl/regulamin/) — read 2026-10-08

### Playmore: a self-checkout QR and clubs run without a desk
- **[POLICY]** The App Store screenshot shows a club card with "Otwórz drzwi" and "QR Checkin"; the
  booking's QR is for "stanowisko self-checkout"
  ([platforms.md](platforms.md#playmore--check-in-qr-and-door-opening)). Its padel page: "Wejścia
  bezobsługowe na kod QR … W weekend klub działa bez recepcji"; the desk's grid shows "co jest opłacone,
  zanim gracz wejdzie na kort". [App Store PL](https://apps.apple.com/pl/app/reservise-playmore/id928403015)
  ([saved](../shots/gaps-HOME-playmore-appstore-qr-checkin.png)), [Playmore dla klubów
  padla](https://join.playmore.pl/dla-klubow-padla/), [Zobacz system](https://join.playmore.pl/zobacz-system/) — read 2026-10-08
- **[ABSENT]** A Kraków desk on tenis4U or Playmore checking players in by name or QR (club rules,
  Playmore club pages, tenis4U code). Fame Sport's app QR is a loyalty card read at purchases. [Fame
  Sport regulamin](https://famesport.pl/regulamin/) — read 2026-10-08

## 13. How long a played game stays on the list (R-HOME-6)

### Playmore: "Nadchodzące" and "Historia"; history opens on the last 30 days
- **[POLICY]** *Moje rezerwacje* has two segments, "Nadchodzące" and "Historia"; history first shows 30
  days ("Brak rezerwacji z ostatnich {days} dni", days = 30) and "Pobierz więcej" reaches further. The
  result pill stays on the tile until the result window closes ("Minął termin na wpisanie wyniku").
  [list code](https://playmore.pl/assets/Du2k_EAD.js), [strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[ABSENT]** The moment a game moves from "Nadchodzące" to "Historia" (decided by the server). — read 2026-10-08

### Playtomic: a played match stays in her history for good
- **[POLICY]** "Matches: Here you can see all the results of your matches, both private bookings and
  public matches." "It is not possible to delete a match from your profile or reset your match statistics
  under any circumstances." The profile shows "Match history in the last 6 months".
  [Player profile sections](https://playerhelp.playtomic.com/hc/en-gb/articles/19831576375313)
  (2026-09-29), [How to edit incorrect match results](https://playerhelp.playtomic.com/hc/en-gb/articles/19831850222609)
  (2026-05-27), [Android strings](../shots/gaps-HOME-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** How long a played match stays in Home's "Your next activity" (help; strings). — read 2026-10-08
