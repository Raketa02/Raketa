# Gaps round after S-01

Answers to the facts story S-01 (published as S-01A to S-01D) still lacked (`$W/stories/S-01/gaps.md`: R-REQUEST-3,
R-NOTIFY-35, R-RESULT-44, R-DECK-11, R-PAY-1, R-HOME-9), and to the four rules whose market grade was still
`? (provisional)` after the area rounds (R-CHECKIN-35, R-NOTIFY-32, R-PLATFORM-48, R-CLUBSETUP-38; what was tried before
is in each area's `gaps-left.md`). Read **2026-10-09**; web search worked throughout. Each `###` heading answers part of
one gap and names its rule, so it can be cited as `topics/gaps-S-01.md#<heading>`.

Sources: Tagvenue's, Airbnb's and a university sports centre's help pages; tenis4U's public web app and the endpoints it
calls for a visitor (five Kraków padel clubs' booking grids, read once each); Playmore's shipped notice-centre source
(Android 6.118.0); Playtomic's Android 6.93.2 string table and push receiver; App Store review feeds (GB, ES, IT);
Playtomic's player help; PerfectGym's and eFitness' help centres, eFitness' App Store listing and Zebra's DS2208
reference guide; Firebase's and Braze's documentation; WhatsApp's help centre and press reports of its 2017 update; an
Apple engineer's forum answer; Stripe's Connect docs, risk policy and support pages; a Shopify community thread.

Kinds: `[POLICY]` a rule, help text, store listing or text an operator ships · `[PRICE]` · `[LAW]` · `[DOCS]` a provider's
or regulator's document, or a published report · `[MEASURED]` read from the product itself (shipped code, string table
or the public data its web app shows a visitor; the extract is saved under `../shots/`) · `[COMPLAINT]` one person's
account · `[ABSENT]` looked for and not found, with where. *Reading* lines are this researcher's inference, not a source.

---

## 1. R-REQUEST-3: how fast a desk answers a request, and whether anyone reads it before opening

### Tagvenue expects venues to answer in 24 to 48 hours and measures an average near 12
- **[POLICY]** "For standard booking inquiries, venues are expected to respond within 24-48 hours, with inquiries expiring
  after 72 hours if unanswered. Formal requests involving payments allow up to two business days for acceptance or
  decline before automatic expiration." It measures replies: "top venues reply in under three hours while the average is
  around 12 hours". [Tagvenue: How does Tagvenue manage venue response times](https://support.tagvenue.com/hc/en-gb/articles/360019425457-How-does-Tagvenue-manage-venue-response-times-and-communication)
  (updated 2026-01-27; read through the help centre's public API, the page itself answers 403) — read 2026-10-09
- *Reading:* the one platform found that publishes measured answer times for venues taking requests by hand gets a
  12-hour average; a 60-minute ceiling is far below what venues answering by hand achieve on it.

### A university sports centre promises two business days, and sells its courts online instead
- **[POLICY]** "Expected response times are within 2 (two) business days after submitting the request." This covers the
  gymnasium, pool and performance centre; "Squash Courts and Studio 1" are reserved through the online booking portal.
  [Toronto Metropolitan University: Facility rentals](https://www.torontomu.ca/recreation/services/facility-rentals.html) — read 2026-10-09
- *Reading:* where a sports operator does answer requests by hand, it counts business days; the hourly courts are sold
  without anyone answering.

### Whether a Kraków desk reads a request before it opens: not found
- **[ABSENT]** A Kraków club's reply time, or whether its desk reads messages before opening. Searched the web in Polish
  ("potwierdzimy … w ciągu", "odpowiada", Messenger, reception hours) and English; Facebook pages, the one place a reply
  time ("Typically replies within…") is shown, refuse a signed-out visitor (Garden Padel's and Fame Sport's answered
  HTTP 400). The earlier rounds' search is in `gaps-REQUEST.md#no-published-response-time-for-a-sports-desk`. Only asking
  a desk answers it — read 2026-10-09

---

## 2. R-NOTIFY-35: how Playmore, tenis4U and WhatsApp date a row in their lists

### Playmore files notices under Today, Yesterday or a date, and gives each row its clock time
- **[MEASURED]** The notice centre groups rows by calendar day in the phone's local time, under "Dzisiaj", "Wczoraj" or the
  date written out ("12 lipca", with the year only when it is not this year; English "Today", "Yesterday"); a row with a
  broken date goes under "Wcześniej". Each row shows its own time as hours and minutes (`toLocaleTimeString`, two-digit
  hour and minute), taken from the notice's `createdAt`. A code comment: "23:59 yesterday is 'Wczoraj' even when it is
  two minutes old." Extract: [`../shots/gaps-S-01-notice-row-dates-playmore-tenis4u.txt`](../shots/gaps-S-01-notice-row-dates-playmore-tenis4u.txt)
  ([Playmore web app](https://playmore.pl/), its source as shipped in Android 6.118.0 from APKPure, as in `gaps-NOTIFY.md`) — read 2026-10-09
- **[POLICY]** Carried: whether the notice centre is switched on for every player is a server switch
  (`gaps-NOTIFY.md#playmore-numbers-the-bell-and-the-app-icon`).
- *Reading:* Playmore carries the same information as Rakieta's row (the time today, Yesterday and the time, a date
  further back) in a day header plus a clock time; it has no weekday tier, and dates a notice when its server wrote it.

### tenis4U's web list puts no time on a row
- **[MEASURED]** A row of the player web app's notice list is the server's title and text and nothing else; an unread
  title gets a green dot. No date or time of the notice is bound anywhere in the component, so a row is dated only if
  the server writes a date into its text. Extract: same file, from [tenis4U web app main.js](https://app.tenis4u.pl/) (3.6.1) — read 2026-10-09
- **[ABSENT]** tenis4U's phone apps' list: not read.

### WhatsApp shows a day or date beside each chat; its own help does not describe the tiers
- **[DOCS]** A press report on a 2018 beta bug: WhatsApp "shows the 'sent day or date' next to each user in the chat list, as
  well as within the conversation", with the labels "Today" and "Yesterday" (the bug printed them as "84ODAY" and
  "89ESTERDAY"). [Beebom, 2018-04-12](https://beebom.com/whatsapp-beta-android-today-yesterday-bug/) — read 2026-10-09
- **[ABSENT]** WhatsApp's own description of the chat list's time format (clock time today, a weekday within the week, a
  date further back): searched faq.whatsapp.com through web search; not found — read 2026-10-09
- *Reading:* the `=` no longer rests on Playtomic alone: Playmore dates every row with the day and the clock time, as
  Rakieta does; tenis4U dates none.

---

## 3. R-RESULT-44: whether players choose partners by a line beside a reliability figure

### Two more players, in Spain and Britain, ask to keep players under a reliability line out of their match
- **[COMPLAINT]** "falta poner una opción para poder marcar con favoritos algunos partidos y poner una fiabilidad mínima para
  entrar" (jjjjjjjjjjjjjjjjjiiiiiiiiii, 4★, ES, 2025-03-28). [App Store ES feed, page 5](https://itunes.apple.com/es/rss/customerreviews/page=5/id=1242321076/sortby=mostrecent/xml) — read 2026-10-09
- **[COMPLAINT]** "many people over estimate their ability. The reliablity indicator is good, so why can't we create public
  games but have an option to limit participation to those with a certain reliabilty rating?" (Mikedefieslife, 2★, GB,
  2022-04-07). [App Store GB feed, page 4](https://itunes.apple.com/gb/rss/customerreviews/page=4/id=1242321076/sortby=mostrecent/xml) — read 2026-10-09
- **[COMPLAINT]** Carried, re-read the same day: "I've learnt to only book competitive matches with people whose
  reliability of their play level is more than 50%" (Markeknows, 4★, GB, 2025-09-25), `competitor-newcomer.md#complaints-about-placement`.
  [App Store GB feed, page 2](https://itunes.apple.com/gb/rss/customerreviews/page=2/id=1242321076/sortby=mostrecent/xml) — read 2026-10-09
- **[COMPLAINT]** Players also read a levelling session as resetting the figure: "empiezo al 50 otra vez" (Pushfinal, 1★, ES,
  2025-07-14); "il livellamento non ti dà diritto ad essere 'affidabile' da subito" (Alejeep, 4★, IT, 2026-09-12).
  [ES feed, page 5](https://itunes.apple.com/es/rss/customerreviews/page=5/id=1242321076/sortby=mostrecent/xml), [IT feed, page 1](https://itunes.apple.com/it/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/xml) — read 2026-10-09

### Playtomic itself acts on reliability: some matches and challenges require a level of it
- **[MEASURED]** Playtomic's string table: "The match requires a player reliability level of %1$s, your reliability level is
  %2$s."; "Need more reliability" / "Reliability ok!"; "A reliability of %1$s and a Level in the range of %2$s is required.
  Request a place to join."; "Only players with %1$s reliability or higher are eligible for the challenge"; and the way up:
  "you can call the club to do a test, improve your ranking and play in all matches." Who sets a match's requirement is
  not in the strings. Extract: [`../shots/gaps-S-01-playtomic-6.93.2-reliability-strings.txt`](../shots/gaps-S-01-playtomic-6.93.2-reliability-strings.txt) — read 2026-10-09
- **[POLICY]** The 50 % players quote is Playtomic's own mark: after a levelling session at a certified club "your
  reliability is automatically set to medium (50%), since the level assigned during that session is considered trustworthy
  by the system" (the app prints LOW, MEDIUM or HIGH beside the percentage, same strings extract). [Playtomic: How the level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works)
  (updated 2026-10-07; read through the help centre's public API) — read 2026-10-09
- *Reading:* three independent players (GB 2022, ES 2025, GB 2025) treat the figure as a line to choose partners by,
  which meets the two-complaint threshold. On Playtomic the line is also enforced in places (a match or a challenge can
  require a reliability); Rakieta's words name a bar nothing enforces.

---

## 4. R-DECK-11: two games at two clubs back to back

### How often players hold back-to-back games, and the gap they leave: not found
- **[ABSENT]** Any count or account of players holding games at two clubs on the same evening, or the time they leave
  between them. Searched the web (English, Polish), Playtomic's help, and the App Store review feeds of Playtomic (GB,
  ES, IT, PT, NL, DE, FR, BE) and Playmore (PL) for "two matches", "back to back", "same time", "double booking", "dos
  partidos", "a la misma hora", "w tym samym czasie" — the two hits are about paying together and a court sold twice —
  read 2026-10-09
- **[MEASURED]** None of the five Kraków padel clubs read on tenis4U turns on its one-booking-at-a-time setting
  (`one_reservation_policy: false` at Garden Padel, Padel House, Fame Sport, Bajada and PADEL LOUNGE); Bajada caps a
  player at 5 active bookings, the others at none (`active_reservations_limit_per_user`). [tenis4U court data, e.g.
  `GET https://api.tenis4u.pl/court/483`](https://app.tenis4u.pl/) — read 2026-10-09
- *Reading:* nothing at a Kraków desk system stops one player holding two courts at once, so back-to-back or even
  overlapping bookings are possible there; how often they happen is unmeasured.

---

## 5. R-PAY-1: how many weekday hours a club would have sold anyway

### Five Kraków padel clubs: how much of the next two weeks' weekday hours is already taken
- **[MEASURED]** On 2026-10-09 at 08:20 the public booking grids of five Kraków padel clubs on tenis4U showed, for the
  eight weekdays Mon–Thu 12–15 and 19–22 October (3 to 13 days ahead), this share of sellable padel court-hours no longer
  free:

  | Club | Courts | 17:00–22:00 | Whole day |
  |---|---|---|---|
  | Padel House | 4 | 100 % (160 of 160 h) | 84 % |
  | Fame Sport Club | 2 | 79 % (64 of 80 h) | 44 % |
  | PADEL LOUNGE | 1 | 61 % (22 of 36 h) | 22 % |
  | Bajada Padel Club | 5 | 48 % (96 of 200 h) | 20 % |
  | Garden Padel | 4 | 46 % (74 of 160 h) | 39 % (online from 15:00 on weekdays) |

  "Not free" counts every booking the grid holds (online, desk, phone, standing weekly slots, classes) and any hour kept
  off sale without a named closure; Garden Padel closes weekday mornings to online booking ("zamkniete" 09:00–15:00).
  It is a snapshot of what is taken days ahead, not final occupancy. Per-day table and method:
  [`../shots/gaps-S-01-tenis4u-krakow-padel-occupancy-2026-10-09.txt`](../shots/gaps-S-01-tenis4u-krakow-padel-occupancy-2026-10-09.txt),
  from the endpoints [tenis4U's web app](https://app.tenis4u.pl/) calls for a visitor (`/court/{id}`, `/occupancy/{id}`) — read 2026-10-09
- *Reading:* at Padel House every weekday evening hour two weeks out is already taken (by standing bookings, since its
  grid opens only 14 days ahead), so a Rakieta game there is an hour the club sells anyway, or none at all. At the
  other four, about half the evening hours and most daytime hours are still unsold three to thirteen days ahead: there a
  game Rakieta fills is mostly a sale the club would not otherwise have made, and its card fee buys that sale.

### Published occupancy: British peak hours near 85 per cent, nothing for Poland
- **[DOCS]** Citing Playtomic and Strategy&'s 2026 Global Padel Report: "In major British clubs, the occupancy rate reaches
  approximately 85% during peak hours"; "nearly one in two players report having difficulty finding an available time
  slot". [Padel Magazine UK](https://padel-magazine.co.uk/Could-the-United-Kingdom-become-the-next-major-world-power-in-padel/) (2026-05) — read 2026-10-09
- **[ABSENT]** An occupancy figure for Poland or Kraków, or for weekday daytime anywhere, in a published report: The Padel
  Paper's coverage of the 2024 and 2025 reports has none; the 2026 report is behind a download form; Polish web search
  ("obłożenie kortów padel") found only a court maker's brochure. [The Padel Paper 2025](https://thepadelpaper.com/playtomic-global-padel-report-2025/),
  [2024](https://thepadelpaper.com/playtomic-global-padel-report-2024/), [Playtomic: Global Padel Report](https://playtomic.com/global-padel-report) — read 2026-10-09

---

## 6. R-HOME-9: how a seller takes its name on a request it never answered

### Airbnb counts an unanswered request against the host, in search and in a figure guests see
- **[POLICY]** "Letting a reservation request expire without responding counts as a non-response and will lower your response
  rate"; the response rate "impacts your Superhost status and search placement". [Airbnb help 430](https://www.airbnb.com/help/article/430)
  — read 2026-10-09
- **[POLICY]** "Your response rate can impact your listing's position in search results." [Airbnb help 2414](https://www.airbnb.com/help/article/2414) — read 2026-10-09
- **[MEASURED]** A listing page shows guests, under *Meet your host* → *Host details*, "Response rate: 100%" and "Responds
  within an hour". [Airbnb listing 1730732010822759543](https://www.airbnb.com/rooms/1730732010822759543) — read 2026-10-09
- **[POLICY]** Carried: the guest's request reads *Expired* when "the host took longer than 24 hours" (`gaps-REQUEST.md#airbnb-gives-the-host-24-hours-then-the-request-expires-and-the-money-goes-back`).

### Tagvenue ranks, badges and can remove a venue that answers slowly
- **[POLICY]** "Venues failing to meet these standards face consequences like reduced visibility, suspension, or removal";
  the *Supervenue* badge needs "a 90%+ response rate, an average time of 12 hours or less, and at least 20 inquiries".
  [Tagvenue help](https://support.tagvenue.com/hc/en-gb/articles/360019425457-How-does-Tagvenue-manage-venue-response-times-and-communication) — read 2026-10-09
- *Reading:* outside racket sport, a seller that lets a request lapse carries it in a public figure and in its ranking,
  and the guest is told the host took too long. No racket platform has a request to lapse; the nearest market practice
  puts the lapse on the seller's record, where Rakieta names the club on the card and keeps no record.

---

## 7. R-CHECKIN-35: what a desk's QR reader does with what it reads

### Polish club desk systems take handheld scanners that type what they read as keystrokes
- **[POLICY]** PerfectGym's reception app (POSweb; the Polish club system that carries the Medicover Sport integration below): a scanner works either on a COM
  port, or "w trybie klawiatury, to w panelu sterowania widoczny jest jako zwykła klawiatura. Wysyła numer karty jako
  tekst"; such a scanner needs a prefix before and a suffix after the scan, otherwise it "nie będzie działał w pełni
  automatycznie". [PerfectGym: Konfiguracja urządzeń w POSweb](https://help.perfectgym.com/hc/en-001/articles/39315699629713-Konfiguracja-urz%C4%85dze%C5%84-w-POSweb)
  (updated 2025-10-10; read through the help centre's public API, the page answers 403) — read 2026-10-09
- **[POLICY]** Medicover Sport's QR "can be recognized by a POSweb reader or a stand-alone Access Control reader"; at the
  desk "a pop-up will appear informing that the Medicover Sport member entrance was allowed", and "The receptionist is
  allowed to cancel the visit after a short period". [PerfectGym: Medicover Sport – Access Control Integration](https://help.perfectgym.com/hc/en-001/articles/39319047252881-Medicover-Sport-Access-Control-Integration)
  (updated 2025-10-10, same route) — read 2026-10-09
- **[POLICY]** eFitness, a Polish club system: supported readers are a barcode reader, two proximity-card readers and "QR
  codes reader Zebra DS2208 and Symbol DS7708" ([2020-08-06](https://help.efitness.com/2020/08/06/step-6-how-to-configure-fiscal-printer-and-club-cards-reader-how-to-enable-qr-codes/));
  members' app QR codes need "a dedicated scanner, which is integrated with our system", set up remotely
  ([2022-01-21](https://help.efitness.com/baza-wiedzy/how-to-enable-qr-codes-in-your-club/)); and eFitness Scanner is a phone app,
  "mobilny multi-czytnik kodów QR … bez dodatkowego sprzętu" ([App Store](https://apps.apple.com/us/app/-/id1624676851)) — read 2026-10-09
- **[DOCS]** Zebra's DS2208, the handheld QR reader eFitness names, "automatically detects the USB host interface type and
  uses the default setting (USB Keyboard HID)"; its default data format is "Data As Is", so no Enter follows a scan unless
  a suffix is set. [Zebra: DS2208 Product Reference Guide, MN-002874-14EN, Oct 2025](https://www.zebra.com/content/dam/support-dam/en/documentation/unrestricted/guide/product/ds2208-prg-en.pdf) — read 2026-10-09

### Which reader a Kraków padel desk owns: still not found
- **[ABSENT]** The make or kind of reader at any named Kraków padel desk, and anything from Playmore/Reservise on desk
  scanners. Searched the web ("Reservise czytnik", "Playmore self-checkout", Fame Sport's reader), on top of the earlier
  rounds' search of tenis4U's and Playmore's desk code (`gaps-CHECKIN.md#the-device-itself-was-not-found`) — read 2026-10-09
- *Reading:* a USB reader that types into whatever box has focus is the ordinary desk set-up in Polish club software, and
  the commonest model ships that way; a club that owns one would meet the six-character box on its first scan. That
  Kraków padel desks own one is not shown.

---

## 8. R-NOTIFY-32: priority, expiry and time-sensitive level of rivals' pushes

### What the rivals' push services do when the sender sets nothing
- **[DOCS]** Firebase: normal priority "is the default priority for data and notification messages"; "When the device is in
  Doze mode, delivery may be delayed to conserve battery until the device exits doze"; high-priority messages that show
  nothing may be "deprioritized to normal priority". [Firebase: Android message priority](https://firebase.google.com/docs/cloud-messaging/android/message-priority)
  (updated 2026-10-07) — read 2026-10-09
- **[DOCS]** Firebase: a message without a lifespan lasts "for a maximum period of four weeks"; the ceiling is 2,419,200 s;
  "a `ttl` value of 0 means messages that can't be delivered immediately are discarded". [Firebase: Setting message lifespan](https://firebase.google.com/docs/cloud-messaging/customize-messages/setting-message-lifespan) — read 2026-10-09
- **[MEASURED]** Playtomic's push receiver passes each message to Zendesk's, Braze's or its own local-notification
  handler (`com.playtomic.general.manager.notification.NotificationsListenerService`, jadx decompile of Android 6.93.2), so
  its pushes arrive through Firebase, some of them sent by Braze. Playmore's arrive through Firebase too
  (`gaps-NOTIFY.md#playmore-uses-one-default-channel-plus-a-lock-screen-countdown`) — read 2026-10-09
- **[DOCS]** Braze: "By default, Braze sets the Push TTL to the maximum for each push messaging service" (28 days on
  Firebase); the Android priority is a workspace default the customer picks, "Normal" or "High"; the iPhone interruption
  level defaults to "Active", and "Time Sensitive" needs the app's Time Sensitive Notifications capability.
  [Braze: Push settings](https://www.braze.com/docs/user_guide/administer/global/workspace_settings/push_settings),
  [Braze: iOS notification options](https://braze.com/docs/user_guide/channels/push/platform_specific_resources/ios/notification_options) — read 2026-10-09
- *Reading:* unless their servers say otherwise, the rivals' pushes travel as Rakieta's do: normal on Android, kept up to
  four weeks, never time-sensitive on an iPhone. What their servers actually set is still unread: **only a dated test on
  a phone with a real booking or alert settles it.**

---

## 9. R-PLATFORM-48: whether a WhatsApp message waiting to send survives closing the app

### WhatsApp: a clock means not yet sent, and the message waits and goes on reconnect
- **[POLICY]** "Seeing a clock means the message is not yet sent or delivered. This could be due to connectivity issues."
  [WhatsApp Help: How to check read receipts](https://faq.whatsapp.com/665923838265756) — read 2026-10-09
- **[POLICY]** As the search engine returned the page (its body would not load directly): "A clock icon next to your message
  means your phone isn't connected to the internet"; "Turn airplane mode on and off to reset your connection. Restart
  your phone and try sending the message again." [WhatsApp Help: Can't send or receive messages](https://faq.whatsapp.com/5155925751185676) — read 2026-10-09
- **[DOCS]** WhatsApp for iPhone 2.17.1 (January 2017) "allows you to tap send on your messages even when you don't have
  an internet connection. Messages will be queued up and sent automatically when your phone connects".
  [iPhone in Canada](https://www.iphoneincanada.ca/2017/01/24/whatsapp-iphone-offline-messaging/); Android had it from June 2016
  ([Purebreak](https://www.purebreak.com/news/whatsapp-sur-iphone-on-peut-enfin-envoyer-des-messages-sans-connexion/119730)) — read 2026-10-09

### An iPhone app the user swiped away is not woken until it is opened again
- **[DOCS]** Apple's engineer: on removing an app from the multitasking screen "The system will not give the app background
  fetch time until after the user manually launches the app again" (Quinn "The Eskimo!", Apple DTS, Nov 2020).
  [Apple Developer Forums 666149](https://developer.apple.com/forums/thread/666149) — read 2026-10-09

### Whether the waiting message survives closing WhatsApp or restarting the phone: not found
- **[ABSENT]** A statement, test or complaint on a clock-marked message after WhatsApp is closed or the phone restarts.
  Searched WhatsApp's help centre, the 2017 press coverage, troubleshooting explainers, forensic write-ups of WhatsApp's
  message database, Reddit and phone forums — read 2026-10-09
- *Reading:* WhatsApp's own help tells a stuck sender to restart and "try sending the message again", and an iPhone
  would not send anything from a swiped-away app before it is reopened. **Only a dated device test settles it** (send in
  airplane mode, swipe WhatsApp away or restart, reconnect, see whether it leaves before or after WhatsApp is reopened).

---

## 10. R-CLUBSETUP-38: a refund from a club account whose payments Stripe has stopped

### Stripe: pausing payments blocks new charges; refunds are not mentioned, and pauses are not enforced in a sandbox
- **[DOCS]** "Pausing payments blocks creation of any charges. It also makes the transfer, card_payments and other payment
  methods capabilities `inactive`"; the account then shows `charges_enabled: false` with `disabled_reason: platform_paused`.
  "We don't enforce payment or payout pauses in a sandbox", and "This workflow isn't available when using Accounts v2."
  [Stripe: Pause payments and payouts on connected accounts](https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts) — read 2026-10-09

### Stripe keeps a stopped account's money to cover refunds; a closed account cannot refund
- **[POLICY]** Under Stripe's risk policy, payouts are typically paused for 120 days "while covering potential refunds,
  disputes or chargebacks on the account". [Stripe: Unacceptable Risk Policy](https://stripe.com/legal/unacceptable-risk-policy) — read 2026-10-09
- **[POLICY]** Once an account is closed "you'll no longer be able to process any refunds, issue any payments, or respond to
  any customer disputes"; Stripe recommends "keeping your account open until those have been resolved".
  [Stripe support: Close a Stripe account](https://support.stripe.com/questions/how-can-i-close-my-stripe-account) — read 2026-10-09

### The refusal message seen again, tied to a short balance
- **[COMPLAINT]** A merchant's Klarna refunds failed for days with "This account is not currently able to refund charges.
  Please contact us via support.stripe.com/contact for further information" (2022-11-14); a community moderator: it
  usually appears when the payout balance does not cover the refund (2022-11-15). [Shopify Community (DE)](https://community.shopify.com/t/ruckzahlung-bei-zahlung-per-klara-nicht-mehr-moglich/167543) — read 2026-10-09
- **[ABSENT]** A Stripe statement on refunds from an account whose `charges_enabled` is false because requirements went past
  due: searched Stripe's Connect refunds-and-disputes guide, the account-rejection changelog (2026-07-29), the pause guide,
  the risk policy and support pages — read 2026-10-09
- *Reading:* everything written points to the balance, not the account's state, as what stops a refund. **Only a Stripe
  test-mode run settles it**, and it must stop the account by letting requirements go past due: a platform pause is not
  enforced in a sandbox and is not offered for Accounts v2, which Rakieta's clubs use.
