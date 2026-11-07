# Gaps — NOTIFY (notices, pushes, the bell)

Answers to the NOTIFY area's open gaps for PRD #530 (`$W/areas/NOTIFY/gaps.md`), read **2026-10-08**. One section per
rule; every fact sits under a `###` heading so it can be cited as `topics/gaps-NOTIFY.md#<heading>`. Facts already in
`competitor-*.md`, `platforms.md`, `complaints.md` or `local-market.md` are cited there, not repeated.

Kinds: [POLICY] a company's rule, help page, changelog or store listing · [DOCS] a platform's or provider's own
document, or a published measurement · [MEASURED] read from the product itself (app package text or code; the extract
is saved under `../shots/`, no screen image) · [COMPLAINT] · [ABSENT] looked for and not found, with where.
*Reading* lines are comparison, not sources.

Packages read on 2026-10-08:
- **Playtomic Android 6.93.2** (`com.playtomic`, from APKPure): its English strings, and a jadx 1.5.1 decompile of
  its code. Extract: [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt).
- **Playmore Android 6.118.0** (`com.reservise.reserviseapp`, from APKPure): a Capacitor shell that loads
  `https://playmore.pl` and ships its web app's source in source maps. Extract:
  [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt).
- **tenis4U** web app and club panel bundles, and the tenis4U and Kluby.org store listings. Extract:
  [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt).

**Limits.** Code shows what an app *can* do, not what a phone showed on a given day. Push wording, sending limits,
message priority and expiry live on the companies' servers and are in no package. No iPhone package (IPA) was read.
The session's web-search budget ran out part-way, so MATCHi, Eversports and Padel Mates help pages were not searched for
alert caps (noted where it matters).

---

## R-NOTIFY-5 — when Playtomic asks for push

### Playtomic asks on the Home tab, from the second visit on
- **[MEASURED]** When the phone hasn't granted notifications, the Home tab shows Playtomic's own sheet before the
  phone's dialog: "Notifications — Enable notifications to receive alerts, last minute deals and discounts. Do you want
  to activate them now?". The code skips the first Home load (a stored counter has to reach 1 first) and skips anyone
  flagged as already asked at the end of onboarding (`onboarding_finish_notification_permission`; where that flag is
  written was not found in the decompile). On Android below 13 there is nothing to ask. Code path:
  `HomeTabPresenter` → `NotifPermissionPromptDisplayControl` (threshold 1) → `PermissionBridgeNotificationManager`.
  [Playtomic on Google Play](https://play.google.com/store/apps/details?id=com.playtomic) (package 6.93.2), extract in
  [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[MEASURED]** The notification settings screen carries a banner "Turn on Notifications — Click here to get instant
  alerts, direct messages, and match updates!" and an action that asks the phone. Same extract — read 2026-10-08
- **[MEASURED]** The marketing SDK in the package (Braze) can also raise the ask from an in-app message (a "push
  primer", `RequestPushPermissionStep`); whether and when Playtomic sends one is decided on its server. Same extract —
  read 2026-10-08
- **[ABSENT]** An ask tied to the first booking or to joining a match: none in the decompiled code. The help centre only
  says "push notifications also depend on your phone settings, so don't forget to turn Playtomic notifications on".
  [Playtomic help: How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337) (updated 2026-09-29) — read 2026-10-08
- **[ABSENT]** When the iPhone app asks: no iPhone package read; needs a dated test on an iPhone.

### Playmore asks in onboarding, then after a successful booking
- **[MEASURED]** Onboarding has a push step ("Włącz powiadomienia" / "Może później"), tested in two wordings, one of
  them "Przypomnimy Ci o grze — „Za 40 minut gra: Kort 2, z Markiem” — włącz powiadomienia, a nic Ci nie umknie".
  Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[MEASURED]** The main ask is "NO LONGER auto-shown on app entry — it fires only at a moment of delivered value (a
  successful booking)", or after joining a league; it is "the LOWEST-priority booking-success prompt" and waits until a
  rating or survey prompt has had its turn. "Skipping push in onboarding must leave the user eligible for the
  post-booking ask, where consent converts best." A player who already gets push on another device is not asked on the
  web. In the phone app the ask sits behind a staged switch (`push_native_prompt`). After a booking the sheet reads
  "Gotowe! Przypomnimy Ci o tej grze — Włącz powiadomienia — damy znać o zmianach w rezerwacji i przypomnimy o grze".
  Same extract — read 2026-10-08
- **[MEASURED]** The "Szukam grania" sign-up asks once more, for its own reason: "Nie przegap zaproszeń — Na
  powiadomieniach stoi cała ta funkcja: pasujące gry i wiadomość, gdy ktoś chce z Tobą zagrać" / "Później". Same
  extract — read 2026-10-08

---

## R-NOTIFY-6 — offering push again after a refusal

### Playtomic shows a "Turn on Notifications" dialog that opens the phone's settings
- **[MEASURED]** Once the phone has refused, the same Home-tab check shows "Turn on Notifications — Get important match
  updates, personal messages and last-minute reminders when you turn on notifications" with "Yes" and "Not now"; "Yes"
  opens the phone's settings. The check runs on each Home load (after the first) while notifications are off. The code
  keeps no refusal count and no date; a flag inside the running app gates the dialog (whether that limits it to once per
  launch could not be traced). Extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[MEASURED]** The notification settings screen keeps a "Turn on Notifications" banner while push is off. Same extract — read 2026-10-08
- **[MEASURED]** A separate location sheet for friends' activity ("Want to know when your friends are playing nearby?")
  offers "Not now" and a "Don't ask me again" box. Same extract — read 2026-10-08
- **[ABSENT]** How often a refusing player actually sees the dialog: needs a dated test on a phone.

### Playmore snoozes the ask for 3, 7, 14, 30, 60, then 90 days, then stops
- **[MEASURED]** "Maybe later" on Playmore's sheet snoozes the ask: `SNOOZE_DAYS = [3, 7, 14, 30, 60, 90]`; "only once
  the whole ladder is exhausted (the 6th dismissal, ~7 months in) do we stop asking for good — a couple of quick
  dismissals must never opt the user out". The count is stored on the player's account, so it holds across phones and
  the web. The same count drives a card in the account hub ("Włącz powiadomienia, aby nie przegapić potwierdzeń i
  przypomnień o grze." / "Włącz push" / "Zamknij"); closing either quiets both. Extract in
  [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[MEASURED]** Playmore re-asks only while the phone's answer is still undecided. After the phone refuses, the
  settings page says "Powiadomienia zablokowane — Powiadomienia są zablokowane w ustawieniach przeglądarki lub systemu.
  Odblokuj je tam, aby z nich korzystać." and "Dopóki są wyłączone, nie damy Ci znać o wolnym miejscu na zajęciach, na
  które czekasz.", with an "Otwórz ustawienia" button on iPhone only. Same extract — read 2026-10-08
- **[MEASURED]** Another Playmore prompt (the favourite-sport question) is capped at "max 2 pokazania, min 30 dni
  odstępu, jeden prompt na sesję". Same extract — read 2026-10-08

### What the phone allows after a refusal
- **[DOCS]** Android: "if the user taps Deny for a specific permission more than once during your app's lifetime of
  installation on a device, the user will no longer see the system permissions dialog if your app requests that
  permission again … considered a permanent denial." [Android Developers: Request runtime permissions](https://developer.android.com/training/permissions/requesting) — read 2026-10-08
- **[DOCS]** iPhone: "The first time your app makes this authorization request, the system prompts the person to grant or
  deny the request and records that response. Subsequent authorization requests don't prompt the person." A trial is
  possible: "The system delivers provisional notifications quietly — they don't interrupt the person with a sound or
  banner, or appear on the lock screen." [Apple: Asking permission to use notifications](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications) — read 2026-10-08

---

## R-NOTIFY-8 — iPhones, and what tenis4U and kluby.org push

### iPhones are about a third of Polish mobile web traffic
- **[DOCS]** StatCounter, Poland, mobile operating systems, Oct 2025 – Sep 2026: iOS **32.03%**, Android 67.72%; month by
  month iOS ran from 29.8% (Feb 2026) to 36.27% (Sep 2026). StatCounter counts web page views, not phone owners.
  [StatCounter: Mobile OS market share Poland](https://gs.statcounter.com/os-market-share/mobile/poland), data in
  [`../shots/gaps-NOTIFY-statcounter-pl-mobile-os-2025-10_2026-09.csv`](../shots/gaps-NOTIFY-statcounter-pl-mobile-os-2025-10_2026-09.csv) — read 2026-10-08
- **[MEASURED]** Store counts as a weak proxy for racket-app players: Playmore has 475 App Store ratings in Poland against
  2,73 tys. Google Play reviews (iPhone ≈ 15% of the two together); tenis4U 100 against 161 (≈ 38%); Kluby.org 4 against
  13. [App Store PL: Playmore](https://apps.apple.com/pl/app/id928403015), [Google Play: Playmore](https://play.google.com/store/apps/details?id=com.reservise.reserviseapp),
  [App Store PL: tenis4U](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113), [Google Play: tenis4U](https://play.google.com/store/apps/details?id=pl.tenis4u.android.free),
  [App Store PL: Kluby.org](https://apps.apple.com/pl/app/kluby-org/id1658178253), [Google Play: Kluby.org](https://play.google.com/store/apps/details?id=com.multiplatform.kluby);
  counts in [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt) — read 2026-10-08
- *Reading:* the two stores ask for ratings differently, so these ratios say little; StatCounter's third is the better
  anchor.
- **[ABSENT]** A Kraków-only share, or one for padel and tennis players: StatCounter has no city level, and no survey of
  Polish racket players' phones was found (search budget ran out after the first queries).

### tenis4U pushes booking notices and tournament news; clubs get an SMS line
- **[MEASURED]** tenis4U's web app keeps a "Powiadomienia" list of the last 50 notices; tapping one opens "my
  reservations" (`tenis4u://myReservations`), a tournament, or a match. [tenis4U web app](https://app.tenis4u.pl/),
  extract in [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt) — read 2026-10-08
- **[COMPLAINT]** Google Play, PL, 2025-09-04: "nie d[a] się zarządzać powiadomieniami, tak żeby wyłączyć informacje o
  turniejach tenisowych, a pozostawić powiadomienia o rezerwacjach"; the developer answered "dobry pomysł - wprowad[zimy
  go w życie]". So tenis4U pushes booking notices and tournament news, with no per-type switch in 2025.
  [Google Play: tenis4U](https://play.google.com/store/apps/details?id=pl.tenis4u.android.free) — read 2026-10-08
- **[MEASURED]** In tenis4U's club panel each court has "SMS / Push" settings, a "Lista osób powiadamianych o rezerwacji
  w korcie" and a "Numer telefonu do powiadomień SMS" ("opcja powiadomień sms jest dodatkowo płatna 30 gr za każdy
  sms"); the panel can also "Powiadom o rozpoczęciu turnieju". Same extract — read 2026-10-08
- **[ABSENT]** Which booking events reach the booker as a push (a move, a cancellation by the club, a freed court): the
  wording lives on tenis4U's server; the App Store text (4.9.2, 8 Oct 2026) names no notifications. The freed-court alert
  is reported unreliable — `complaints.md#no-waiting-list-or-queue-for-a-full-game`.

### kluby.org tells by SMS and e-mail; its app states no push
- **[POLICY]** kluby.org's changelog lists only SMS and e-mail notices: "Powiadomienia SMS o zaległościach" (2018),
  "Powiadomienie dla pracownika o odwołanej rezerwacji" (2020), "Wysyłanie smsów do pojedynczego klienta" and "Wysyłanie
  smsów masowo do wszystkich" (2021), "Powiadomienia o odwołaniu uczestnika z zajęć", "… całych zajęć", "… trenera z
  zajęć" and "Podgląd wysłanych powiadomień w historii klienta o rezerwacjach" (2022). [kluby.org: Co nowego](https://oferta.kluby.org/changelog) — read 2026-10-08
- **[POLICY]** The Kluby.org app (iPhone 3.56.0, 31 Aug 2026; Android, 5 tys.+ downloads) is described as search,
  booking and competitions. [App Store PL: Kluby.org](https://apps.apple.com/pl/app/kluby-org/id1658178253), [Google Play: Kluby.org](https://play.google.com/store/apps/details?id=com.multiplatform.kluby) — read 2026-10-08
- **[ABSENT]** Any push from the kluby.org app: not in its listings or its changelog (the 2024–2026 pages list no
  entries).

---

## R-NOTIFY-16 — marking what arrived while the app was closed

### Playtomic marks its bell with dots, no number found
- **[POLICY]** "Tap the bell icon in the top right corner of the app, then go to the "Club" tab to see your favorite
  clubs' upcoming activities". [Playtomic help: How to follow your favorite club activities](https://playerhelp.playtomic.com/hc/en-gb/articles/44465662231185) (updated 2026-09-29) — read 2026-10-08
- **[MEASURED]** Behind the bell, "Inbox" has three chips, "Notifications", "Chats" and "Clubs", each with a yes/no
  badge; the Chats badge lights when its unread count is above zero. The account API carries an `unseen_notifications`
  number that no screen reads. The Android manifest asks for no launcher-badge permission. Extract in
  [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[ABSENT]** A number on the iPhone app icon, or a banner at launch: not readable from the Android package; needs a
  dated test on a phone.

### Playmore numbers the bell and the app icon
- **[MEASURED]** Playmore's notification centre ("Powiadomienia", "Nieprzeczytane", "Oznacz wszystkie") holds what came
  by push. The bell shows the unread count, capped at "99+". The app icon carries the same number: "the PUSH payload
  carries the count while the app is dead … and this module writes it while the app is alive"; on Android it is
  best-effort ("stock Pixel shows a dot, no number"), "iOS is where the count is a promise". The centre sits behind two
  switches (an app flag and a server flag), so whether every player has it today was not verifiable. Extract in
  [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[MEASURED]** A muted push category still lands in the bell: "Wyciszone i tak znajdziesz w dzwonku w aplikacji."
  Same extract — read 2026-10-08

### tenis4U marks unread notices with a dot
- **[MEASURED]** tenis4U's web list puts a green dot on each unread notice and offers "oznacz wszystkie jako
  przeczytane". [tenis4U web app](https://app.tenis4u.pl/), extract in [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt) — read 2026-10-08
- **[ABSENT]** An app-icon number in tenis4U's phone apps: their packages were not read.

---

## R-NOTIFY-17 — an unread count on the list of notices

### Playtomic shows dots; Playmore shows a number
- **[MEASURED]** Playtomic: a dot per Inbox chip, no count (see the R-NOTIFY-16 heading above); the list's strings
  include a "New" and an "Activity" heading, and it says "No new notifications — All quiet for now. Check back later for updates." when empty.
  Extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[MEASURED]** Playmore: the count on the bell (up to "99+"); unread rows are shown bold when the centre opens, then
  marked read; "Oznacz wszystkie" clears them. Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[MEASURED]** tenis4U: a dot per unread row; the count only switches "mark all read" on or off. Extract in
  [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt) — read 2026-10-08

---

## R-NOTIFY-20 — the language of a notice, and the club's own words

### Playtomic's app follows the phone, and the club picks its e-mails' language
- **[POLICY]** "On Android, Playtomic follows your device language … On iOS, you can change the Playtomic app language
  without changing your device language." [Playtomic help: How to change the language](https://playerhelp.playtomic.com/hc/en-gb/articles/46119983392529) (updated 2026-09-29) — read 2026-10-08
- **[POLICY]** For clubs: "Communication Language — Customize the language of the messages your players receive! The email
  they get will include automatically completed details like: Player name, Date and time of the match, Location, Payment
  information", set under Settings > Venue > Communication. So a booking e-mail comes in the club's chosen language,
  not the player's. [Playtomic Manager help: Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145) (updated 2026-07-21) — read 2026-10-08
- **[MEASURED]** The player's account holds a `communications_language` value that the app can send when it updates the
  profile; how it is first set, and whether pushes use it, is decided on the server. Extract in
  [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[ABSENT]** The language of a Playtomic push on a phone set to Polish: not documented; needs a dated test with a real
  booking (Playtomic has no club in Kraków — `competitor-organiser.md#playtomic-has-no-club-in-krakow`).

### Playmore lets clubs post announcements; booking notices are named after the club
- **[MEASURED]** Playmore's push categories include "Komunikaty klubu — np. zmiana godzin otwarcia, wiadomość od
  recepcji", which a player may mute. A booking notice's server title is the club's name, the body built from a
  template (example in the code: "Okęcie Tennis Club: Mateusz, rezerwacja…"). Extract in
  [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[ABSENT]** Whether a Playmore club can change the wording of the booking or cancellation template: not in the app
  code (the templates live on Playmore's server).

### tenis4U lets the club write text that the player sees with the booking
- **[MEASURED]** The club panel has "Wiadomość widoczna dla użytkowników" (up to 512 characters) on a booking, and per
  court "Treść widoczna dla gracza w szczegółach rezerwacji" and "Treść wyświetlana użytkownikowi po dokonaniu rezerwacji
  i na liście rezerwacji". Extract in [`../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt`](../shots/gaps-NOTIFY-tenis4u-kluby-notices.txt) — read 2026-10-08
- **[ABSENT]** Whether that text travels in a push: not readable.

---

## R-NOTIFY-22 — where a refund notice lands

### Playtomic tells refunds by e-mail and lists them under Your payments
- **[POLICY]** "the money is returned to the original payment method … You can see all payment and refund transactions in
  your profile. Simply click on the three bars in the top right corner and go to Your payments menu." [Playtomic help:
  Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593) (updated 2026-09-10) — read 2026-10-08.
  E-mails on a cancellation and a receipt: `competitor-joiner.md#on-joining-a-confirmation-email-and-the-clubs-message`.
- **[MEASURED]** Rows under Transactions carry a "Refund" label, and a cancelled booking offers "Get cancellation receipt
  by email". Extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt);
  `gaps-PAY.md` strings extract — read 2026-10-08
- **[ABSENT]** A refund push, and where its tap lands: no refund push text in the package (push wording is on the
  server).

### Playmore files a refund notice under Wallet
- **[MEASURED]** Playmore's notice "Zwrot na portfel" (code `wallet_first_partner_card_refund`) sits in the Wallet
  category. A tap opens the in-app address the server put in the notice (the code's example is
  `https://playmore.pl/wallet`); with no usable address the row expands in place. A refund notice never gets a pay
  button. Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[ABSENT]** Where a card refund (not to the wallet) lands at Playmore: no such notice code in the app.

---

## R-NOTIFY-24 — a cap on a player's alerts per day

### No platform read publishes a daily cap on alerts a player receives
- **[ABSENT]** Playtomic: no per-day cap in its help or app text. The free plan limits the *number* of priority alerts
  to one ("Upgrade to Premium to create unlimited alerts"); each alert is bounded by days ("Choose your days (max.
  %1$s)"), hours ("Max. %1$s hours") and an optional end ("The alert will not expire if no option is selected"). Alert
  types: "Last minute cancellations", "Few courts available", "Last place in an Open Match".
  [Playtomic help: How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337) (updated 2026-09-29),
  extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[MEASURED]** Playmore caps the sender, not the receiver: inviting players to your game has a daily limit
  ("Dzienny limit zaproszeń wyczerpany - wróć jutro.") and a per-person pause ("Tę osobę zaprosiłeś niedawno - daj jej
  chwilę."); an invite is "jedno powiadomienie z terminem". A "Szukam grania" sign-up lasts 4 weeks and then asks
  "Nadal szukasz grania?". The feature runs only in pilot clubs (Okęcie Tennis Club in Warsaw, Padel Point Białystok).
  Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[ABSENT]** A receiver-side cap at MATCHi, Eversports or Padel Mates: not searched (search budget ran out); Padel
  Mates' site markets "Smart alerts" and "Push notifications for open matches" with no limit stated
  (`platforms.md#padel-mates--what-it-is-and-how-players-pay`).

---

## R-NOTIFY-25 — bundling alerts past a limit into a digest

### Lists fold social notices; no pushed digest was found
- **[MEASURED]** Playtomic's list folds social notices into one line: "<b> %1$s and %2$s more </b>liked your post",
  "<b> %1$s and other %2$s contacts </b>have joined a match". Whether pushes fold the same way is decided on the server.
  Extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[MEASURED]** Playmore: a muted category is not pushed but still lands in the bell; no digest push in the code.
  Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[POLICY]** kluby.org added "Dedykowany adres e-mail do codziennych wiadomości z systemu ligowego" (2023), a sender
  for the league system's daily e-mails; what they contain is not stated. [kluby.org: Co nowego](https://oferta.kluby.org/changelog) — read 2026-10-08
- **[ABSENT]** A daily or weekly digest *push* at Playtomic, Playmore, tenis4U or kluby.org: none in their code, help or
  changelogs read.

---

## R-NOTIFY-28 — how a Kraków desk tells players of a late cancellation

### Kraków club rules reserve the right to cancel and say nothing on how players are told
- **[POLICY]** KSOS (al. Powstania Warszawskiego 6, Kraków): "Administrator zastrzega sobie prawo do odwołania
  rezerwacji w każdym czasie, jeśli konieczność taka uzasadniona jest stanem technicznym obiektu, awarią, przerwami w
  dostawie mediów…", and for tournaments and maintenance; the rules don't say how the booker is told. A player cancels by
  e-mail to korty@ksos.pl. [KSOS: Regulamin rezerwacji kortów](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/) — read 2026-10-08
- **[POLICY]** Miazga Squash (Kraków): a booking or a cancellation is confirmed by "wiadomość SMS wysłana z systemu";
  the club may cancel bookings made more than 14 days ahead or with doubtful details; no clause on how a club
  cancellation is told. [Miazga Squash: Regulamin](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Garden Padel (Kraków): complaints "na e-mail … lub telefonicznie"; nothing on club cancellations.
  [Garden Padel: Regulamin](https://gardenpadel.pl/regulamin/) — read 2026-10-08
- **[POLICY]** The desks' tools: kluby.org sends SMS "do pojedynczego klienta" or "masowo do wszystkich" (see the
  kluby.org heading above); tenis4U gives a court an SMS line at 30 gr per SMS.
- **[ABSENT]** Whether Kraków desks phone, text or WhatsApp players when they cancel late, and how often a player turns
  up anyway: not in any club rule read (KSOS, Miazga, Garden Padel, Atras, Fame Sport) or review found; needs asking a
  desk.

---

## R-NOTIFY-30 — whether Playmore's open-game alerts say how many seats are open

### The alert wording is on Playmore's server; the app counts seats elsewhere
- **[MEASURED]** Open-game and reserve-list push wording is not in the app package. The app shows counts around it: the
  creator sees "Powiadomimy {count} osób szukających grania"; the invite sheet lists your games with "{count} wolne
  miejsca"; the tab reads "Ktoś szuka partnera do gry - {count} otwarte gry". Reserve-list ("lista rezerwowa") pushes are
  always sent and cannot be muted. Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[ABSENT]** Whether the open-game or reserve-list push itself says how many seats are open: needs a dated test on a
  phone in a pilot club.

---

## R-NOTIFY-32 — priority, expiry and time-sensitive level

### Playtomic puts every Android channel at high importance
- **[MEASURED]** Playtomic's three Android channels, "General", "Chat" and "Community", are all created at importance 4
  (high: sound and a pop-up banner). Priority alerts carry an end date ("Expires on %1$s"), which ends the alert, not a
  message. Extract in [`../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt`](../shots/gaps-NOTIFY-playtomic-android-6.93.2-push.txt) — read 2026-10-08
- **[ABSENT]** Message priority, expiry (time to live) and the iPhone's time-sensitive level: set per message on the
  server; needs a dated test on a phone.

### Playmore uses one default channel, plus a lock-screen countdown
- **[MEASURED]** Playmore creates no Android channel and names no default, so its pushes land in Firebase's fallback
  channel ("Miscellaneous"). On an iPhone with the app open, a push shows only "badge" and "sound". From 60 minutes before
  a game until its end, an iPhone shows a lock-screen card "Nadchodząca gra — Karta z odliczaniem do najbliższej gry".
  Extract in [`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`](../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt) — read 2026-10-08
- **[DOCS]** Firebase creates that fallback channel at `IMPORTANCE_DEFAULT`, commented "shows everywhere, makes noise,
  but does not visually intrude". [firebase-android-sdk: CommonNotificationBuilder.java](https://github.com/firebase/firebase-android-sdk/blob/main/firebase-messaging/src/main/java/com/google/firebase/messaging/CommonNotificationBuilder.java) — read 2026-10-08
- **[ABSENT]** Playmore's message priority and the iPhone time-sensitive level: set on the server; needs a dated test.
- *Reading:* an iPhone in a Focus holds anything not time-sensitive (`situations.md` SIT-96), so neither rival's level
  can be graded from outside.
