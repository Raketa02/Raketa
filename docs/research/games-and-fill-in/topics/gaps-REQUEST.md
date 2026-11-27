# Gaps round: REQUEST

Answers to the facts the REQUEST grades needed (`$W/areas/REQUEST/gaps.md`), read 2026-10-08. Each `###` heading
answers part of one gap and names its rules. The two provisional grades (R-REQUEST-10, R-REQUEST-44) come first.

**Sources.** Playtomic Manager's help centre (its public Zendesk API) and the web app it serves at
manager.playtomic.io; tenis4U's club panel as shipped on its demo (`test-panel.tenis4u.pl`, linked from tenis4u.pl's
"ZOBACZ DEMO") and its site; kluby.org's changelogs, feature list and help videos (auto-captions, downloaded from its
YouTube channel); Playmore's web app bundles (1,343 chunks) and its page for clubs; Airbnb's, Booksy's, TableCheck's
and Booking.com's help and developer pages; Stripe's and Google's documents; two German judgments. No screenshot was
taken: nothing is `[MEASURED]`. Interface text read from served code is tagged `[POLICY]`, as in `platforms.md`.

**Kinds:** `[POLICY]` a rule, help text or interface text the operator publishes or ships · `[DOCS]` a provider's
document · `[LAW]` · `[COMPLAINT]` · `[ABSENT]` looked for and not found, with where. A line marked *reading* is this
researcher's inference from the facts above it, not a source.

## 1. How a desk learns of a new online booking (R-REQUEST-10, R-REQUEST-6)

### Playtomic Manager is a browser app with opt-in emails and a schedule that refreshes itself quietly

- **[POLICY]** "Playtomic Manager works in your phone's browser, not as a downloadable app … It is not a native app
  from the App Store or Google Play"; staff add it to the home screen. So no staff phone push exists.
  [Playtomic Manager help: How to use Playtomic Manager on mobile](https://helpmanager.playtomic.com/hc/en-gb/articles/46212092028561-How-to-use-Playtomic-Manager-on-mobile) (updated 2026-09-17) — read 2026-10-08
- **[POLICY]** Each admin's only booking alert is email, chosen per admin: "Set the email notifications: Bookings
  created or cancelled by players, course enrollment cancellations." The "Communication and notifications" article
  covers only messages sent to players. [How to add/edit an admin role](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049-How-to-add-edit-an-admin-role), [Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145-Communication-and-notifications) — read 2026-10-08
- **[POLICY]** The served schedule re-reads its bookings every 30 seconds (`pollingInterval: 3e4` on the occupancy and
  event queries). A new booking simply appears on the grid.
  [manager.playtomic.io: schedule chunk](https://manager.playtomic.io/assets/schedule-D2qv8-fn.js), [Calendar chunk](https://manager.playtomic.io/assets/Calendar-DrLnPhQX.js) — read 2026-10-08
- **[ABSENT]** A sound, a browser notice, an SMS or a tab-title change for a new booking. Help centre searched for
  notification, sound, alert, push, mobile app, new booking, email notifications, real time, refresh. Across the 794
  chunks the web app serves there is no audio file or `Audio` element and no `document.title` change, and the only
  browser-notification code is inside the Braze marketing SDK — read 2026-10-08.

### tenis4U's club panel re-reads the calendar every 10 seconds and puts up a Nowa rezerwacja box

- **[POLICY]** tenis4U's notifications page: "6. Obsługa kortu może otrzymywać każdorazowo powiadomienie, jeśli
  pojawi się rezerwacja online na ich kortach." Its club section lists "Powiadomienia o rezrwacjach".
  [tenis4U: Powiadomienia](https://tenis4u.pl/powiadomienia/), [tenis4U](https://tenis4u.pl/) — read 2026-10-08
- **[POLICY]** A court's settings in the club panel hold "Lista osób powiadamianych o rezerwacji w korcie" (with
  "Dodaj"), "Numer telefonu do powiadomień SMS" and "opcja powiadomień sms jest dodatkowo płatna 30 gr za każdy sms".
  [tenis4U club panel (demo), main bundle](https://test-panel.tenis4u.pl/main.abcc0a0a9785a191.js) — read 2026-10-08
- **[POLICY]** The panel's calendar re-reads bookings every 10 seconds, or every 60 seconds when the server takes over
  1.5 seconds to answer. When a booking is new since the last read, it shows an alert box above the calendar,
  "Nowa rezerwacja." / "Nowe rezerwacje.", listing "{name} ({court}) - {date} {from}-{to} ({weekday})", closed with
  ×. A booking that disappeared shows "Usunięto rezerwację." The navbar's notifications bell re-reads every 60
  seconds. [same bundle](https://test-panel.tenis4u.pl/main.abcc0a0a9785a191.js) — read 2026-10-08
- **[ABSENT]** In the same code: no sound (no `Audio`, no audio file), no browser notification (`Notification` is never
  requested) and no tab-title change (`document.title` is set only on PDF windows) — read 2026-10-08.
  - *Reading:* tenis4U's desk sees a new booking within about 10 seconds, but only if the panel is open on the
    calendar. Away from it, the channels are the per-court email list and paid SMS.

### kluby.org emails and texts the staff on each new online booking, and lists the latest bookings

- **[POLICY]** Help video "Rozdział 2.5. Powiadomienia" (auto-captions; machine transcript, quoted words approximate):
  in the settings the club enters an email address and a phone number "na które będą przychodziły [powiadomienia]
  do nas jako osób zarządzających kortami", and ticks whether to get word "o nowych rezerwacjach internetowych",
  "odwołaniu internetowym" and "o nowych ogłoszeniach". SMS sent from the club's own SIM need kluby.org's control
  computer. [kluby.org: Pomoc, 2.5](https://oferta.kluby.org/pomoc), [video](https://www.youtube.com/watch?v=1ibSZxbDhrE) — read 2026-10-08
- **[POLICY]** Video "Rozdział 2.8. Najnowsze i odwołane rezerwacje": a list of bookings "posortowana od tych które
  zostały dodane przed chwilą", showing how many minutes ago and by which staff member or user; the same for cancelled
  ones. [video](https://www.youtube.com/watch?v=zp41Kxx5H0Y) — read 2026-10-08
- **[POLICY]** Changelog: "Możliwość ustawienia powiadomień na więcej niż jeden adres e-mail" (1 Mar 2018);
  "Powiadomienie dla pracownika o odwołanej rezerwacji" (1 Jul 2020). Feature list: "Powiadomienia SMS/MAIL".
  [Co nowego 2018](https://oferta.kluby.org/changelog?rok=2018), [2020](https://oferta.kluby.org/changelog?rok=2020), [Funkcje](https://oferta.kluby.org/funkcje) — read 2026-10-08
- **[ABSENT]** A sound, browser notice or tab title for a new booking: changelogs 2016–2023 (2012–2015 and 2024–2026
  show no entries) and the feature list searched for dźwięk, push, alert, powiadom — read 2026-10-08.

### Playmore and Reservise publish no desk alert

- **[ABSENT]** How a Playmore/Reservise desk learns of a new online booking. Its page for clubs sells "Mniej pracy na
  recepcji" and payments seen "w grafiku" (green bar = paid), nothing on alerts; the player web app's 1,343 chunks
  hold no new-booking alert ("nowa rezerwacja", "newReservation"); the club panel is not public; the App Store has no
  Reservise staff app. [Playmore dla klubów](https://join.playmore.pl/), [App Store search "reservise"](https://itunes.apple.com/search?term=reservise&country=pl&entity=software) — read 2026-10-08

### Outside racket sport, a restaurant system rings for same-day bookings

- **[POLICY]** TableCheck (restaurants): "You can receive alert notifications by email / SMS when you have a new
  reservation, a reservation is modified or cancelled … for same-day reservations, it is now possible to configure a
  alert sound on TableCheck Manager … the alert sound will be heard only for same-day reservations."
  [TableCheck: Alerts for Reservations](https://support-restaurants.tablecheck.com/hc/en-us/articles/4404958835993-New-Feature-Alerts-for-Reservations) (released 13 Aug 2021) — read 2026-10-08
  - *Reading:* the only desk system found that makes a sound does it for bookings that need acting on today; none of
    the three Kraków systems makes one.

---

## 2. Whether a game screen changes by itself when an answer arrives (R-REQUEST-44)

### Playmore's booking screen re-reads itself only while its own payment is settling

- **[POLICY]** The booking details page (`ReservationDetailsPage`) loads the booking once when opened and offers
  pull-to-refresh. It re-reads by itself only (a) right after an online payment, for bookings made in the last three
  minutes, up to 18 times until "paid" — the page says "Płatność przyjęta — status zaktualizuje się sam. Nie płać
  ponownie." — and (b) every 30 seconds while one of its split shares is pending and the page is visible, at most 40
  times. Nothing re-reads the booking or its open game on any other event.
  [Playmore web app: reservation details chunk](https://playmore.pl/assets/D-b_RkfX.js), [Polish strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** A push received while the app is open shows a toast with the push text, unless the player is already on
  the page the push points to (then nothing shows); it also refreshes the bell's unread count and the bookings badge
  from the local cache. It does not re-read the booking. In the browser, a push in the foreground becomes a system
  notification only. [native push chunk](https://playmore.pl/assets/DI8sPgBJ.js), [web push chunk](https://playmore.pl/assets/B3ivJW8g.js) — read 2026-10-08
  - *Reading:* a Playmore player looking at a game when its confirmation lands keeps seeing the old state, with no
    toast, until they pull to refresh or reopen the page.

### Playmore's lists re-read when the app comes back, at most every 30 seconds

- **[POLICY]** A shared "RefetchOnFocus" hook re-reads when the app returns to the foreground or the tab becomes
  visible, at most once per 30 seconds by default. The bookings list uses it, plus a re-read when the network comes
  back (at most every 10 s) and when the page is returned to (at most every 5 s). The open-game card's countdown
  ("Zostało {minutes} min") ticks every 30 seconds without re-reading data. [shared hooks chunk](https://playmore.pl/assets/Cng0yjU9.js), [bookings list chunk](https://playmore.pl/assets/Du2k_EAD.js), [open-games chunk](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08
- **[ABSENT]** Any live connection (WebSocket, server-sent events, realtime channel) used by Playmore's screens: the
  Supabase client is bundled, but no app code subscribes to a channel — read 2026-10-08.

### Playtomic: not found

- **[ABSENT]** Whether Playtomic's match screen updates itself when a request is accepted or a match is confirmed. The
  player help says an accepted requester "will receive a notification", and of a paid match missing from the list,
  "your booking is confirmed and should appear shortly". The app is native and its code was not readable; help
  searched for refresh, not updated, real time, notification, pull down.
  [Playtomic help: How to request a spot in a open match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832027031569-How-to-request-a-spot-in-a-open-match) — read 2026-10-08

---

## 3. Request-to-book outside racket sport (R-REQUEST-1, R-REQUEST-3, R-REQUEST-25)

### Airbnb gives the host 24 hours, then the request expires and the money goes back

- **[POLICY]** "The status for your reservation will be 'Pending' until the host responds"; the host "has 24 hours to
  accept or decline the request"; if declined or unanswered, "the booking status will be updated as 'Declined' or
  'Expired,'" and "your payment will be refunded to your original payment method". The guest pays at the request.
  [Airbnb help 2810](https://www.airbnb.com/help/article/2810) — read 2026-10-08
- **[POLICY]** On a declined or expired request "no reservation is made"; an expired one is where the host "took longer
  than 24 hours"; the authorisation on the payment method "will be removed". [Airbnb help 315](https://www.airbnb.com/help/article/315) — read 2026-10-08
- **[POLICY]** Host side: "You have 24 hours to respond before it expires"; after expiry "The dates will remain blocked
  on your calendar until you manually unblock them"; a missed request is recovered only by the guest sending a new one.
  No pause for night or closed days is mentioned. [Airbnb help 28](https://www.airbnb.com/help/article/28) — read 2026-10-08

### Booksy lets a business switch off automatic confirmation, with no deadline published

- **[POLICY]** "If you haven't changed any of your Booking Settings, bookings made by clients are automatically
  confirmed … If you'd like to … confirm bookings yourself: … Turn off the Automatically confirm bookings switch."
  [Booksy help: Do I have to confirm bookings made by my clients?](https://support.booksy.com/hc/en-us/articles/16463923827986-Do-I-have-to-confirm-bookings-made-by-my-clients) (updated 2024-08-09) — read 2026-10-08
- **[ABSENT]** How long a Booksy business has to confirm, what happens if it doesn't, and when a deposit is taken.
  Help centre searched for manual, confirm appointment, request, pending, decline, accept, approve, automatic — read 2026-10-08.

### TableCheck restaurants may hold a booking as Pending until staff confirm

- **[POLICY]** "certain merchants may first place your reservation into 'Pending' status which will require their staff
  to manually confirm your booking"; the diner sees "an amber message"; on confirmation an email and/or SMS, and the
  page shows a green "Accepted"; "If your reservation is 'Pending' and you did not receive an email or SMS … please
  contact the restaurant directly". No deadline is given.
  [TableCheck: Pending Reservations](https://support-diners.tablecheck.com/hc/en-us/articles/900000622486-Pending-Reservations) — read 2026-10-08

### Booking.com request to book: an expired request is frozen

- **[DOCS]** Its partner API refuses a late answer: "The Rtb request is expired, so status cannot be updated"
  (`RTB_STATUS_CAN_NOT_CHANGE`). The answer window is not stated on the page.
  [Booking.com Connectivity: Modifying booking requests](https://developers.booking.com/connectivity/docs/request-to-book/modifying-booking-requests) — read 2026-10-08
  - *Reading:* Booking.com, like Rakieta, refuses an answer after the deadline; Airbnb lets the guest send the request
    again.

### Fresha, TheFork and OpenTable: not found

- **[ABSENT]** A published request-to-book window, expiry or charge moment for Fresha, TheFork or OpenTable. Searched
  their help centres through web search ("booking request", "approval", "pending", "demande de réservation") and
  found only third-party pages — read 2026-10-08.
- **[ABSENT]** Any request-to-book whose window counts only the host's open hours: Airbnb's 24 hours run on the clock,
  and no other source read states a rule — read 2026-10-08.

---

## 4. The deadline on the waiting guest's screen (R-REQUEST-43, R-REQUEST-40)

### Airbnb tells the guest the window in its help, with no countdown found

- **[POLICY]** The help page says the host "has 24 hours to accept or decline", and the trip reads "Pending" meanwhile.
  [Airbnb help 2810](https://www.airbnb.com/help/article/2810) — read 2026-10-08
- **[ABSENT]** An expiry time or countdown on Airbnb's pending trip screen: help articles 28, 315 and 2810 and the
  community forum searched ("request will expire", "expires in") — read 2026-10-08.

### TableCheck shows Pending without a deadline

- **[POLICY]** The diner's page shows the amber "Pending" message until the restaurant confirms; no time is given
  (`#tablecheck-restaurants-may-hold-a-booking-as-pending-until-staff-confirm`).
- *Reading:* among the request-to-book products read, only Playmore counts a wait down on the player's screen, and
  only for waits the player controls (`platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`).

---

## 5. A refusal's reason, and refusal against timeout (R-REQUEST-20, R-REQUEST-23)

### Airbnb names Declined and Expired apart, and hosts often give a reason

- **[POLICY]** A trip ends as "Declined" or "Expired" — two statuses ([Airbnb help 2810](https://www.airbnb.com/help/article/2810)).
  Hosts "often" tell the guest why they declined but "may not always provide that info"; an expired request has no
  host answer to pass on. [Airbnb help 315](https://www.airbnb.com/help/article/315) — read 2026-10-08

### Booking.com keeps the refusal reason from the guest

- **[DOCS]** The property's rejection reason (`rejectionReasonText`): "This information is private and is not shared
  with the guest"; it "is kept private and is only used to improve the overall experience."
  [Booking.com Connectivity: Modifying booking requests](https://developers.booking.com/connectivity/docs/request-to-book/modifying-booking-requests) — read 2026-10-08
  - *Reading:* both models exist: Booking.com keeps the reason private, as Rakieta does, but the host's own message can
    still reach an Airbnb guest; both platforms tell a refusal from a timeout.

---

## 6. How fast Kraków desks answer, and nights (R-REQUEST-1, R-REQUEST-3, R-REQUEST-6)

### Kraków desks are staffed about 07:00 to 23:00 and book on the spot

- **[POLICY]** Garden Padel 7:00–23:00, phone bookings "w godzinach pracy recepcji"; Atras 7.00–24.00 on weekdays,
  8.00–22.00 at weekends — carried from `gaps-FILL.md#desks-take-phone-bookings-during-opening-hours-online-bookings-confirm-at-once` (read 2026-10-08).

### Some clubs run whole days with nobody at the desk

- **[POLICY]** Playmore's page for clubs quotes a club owner under "Weekendy bez recepcji" (KS Zakręt; booking,
  payment, door and light linked): "Nie muszę nikogo zatrudniać na sobotę i niedzielę."
  [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08
- **[POLICY]** tenis4U sells a controller that "umożliwia bezobsługową pracę obiektu przez całą dobę, siedem dni w
  tygodniu" (2,500 zł net): door, lights and heating follow the booking. [tenis4U: Automatyzacja](https://tenis4u.pl/automatyzacja/) — read 2026-10-08
  - *Reading:* at an unstaffed hour, or a whole unstaffed weekend, a request waits for nobody; the online booking
    systems these clubs use need no one to answer.

### No published response time for a sports desk

- **[ABSENT]** A Kraków club's stated time to answer an online message or request, or whether anyone reads them while
  the club is closed; and any published norm for a sports desk. Searched the clubs' sites and rules (Garden Padel,
  Fame Sport, Atras, Squash4You, Miazga), pado.app's Kraków club pages and web search ("odpowiadamy", "w godzinach
  pracy recepcji"); Facebook pages were not read — read 2026-10-08.

---

## 7. Blocking an hour by hand for an outside request (R-REQUEST-2, R-REQUEST-7, R-REQUEST-37)

### tenis4U's desk adds a one-off or recurring block on a court

- **[POLICY]** Panel strings: "Dodaj blokadę stanowiska", "Blokady jednorazowe", "Blokady cykliczne", "Ustawiasz
  blokadę w terminie:", "Usunąć blokadę?", and a calendar filter "tylko blokady".
  [tenis4U club panel (demo), main bundle](https://test-panel.tenis4u.pl/main.abcc0a0a9785a191.js) — read 2026-10-08

### kluby.org blocks free half-hours in a range

- **[POLICY]** "Możliwość blokowania wszystkich wolnych połówek danego dnia w wybranym przedziale czasowym" (2017).
  [Co nowego 2017](https://oferta.kluby.org/changelog?rok=2017) — read 2026-10-08

### Playtomic Manager has blocking reservations

- **[POLICY]** "Create dedicated blocking reservations for courts when they are not available for use" (maintenance,
  weather); blocks do not count in occupancy statistics.
  [Playtomic Manager help: Schedule basics](https://helpmanager.playtomic.com/hc/en-gb/articles/20560058451985-Schedule-basics) — read 2026-10-08

### Whether a desk would block the hour: not found

- **[ABSENT]** A Kraków desk's account of blocking an hour for an outside platform's pending request, or of selling it
  by phone meanwhile; none of the three systems imports bookings or offers an API
  (`gaps-ENGINE.md#one-club-three-ways-in-online-phone-and-desk`, `gaps-FILL.md#klubyorgs-integrations-list-has-no-calendar-feed-import-or-api`) — read 2026-10-08.
  - *Reading:* blocking is a manual entry in every system read; a request that is taken back leaves that block
    behind unless someone removes it.

---

## 8. A club whose payments account is asked for more (R-REQUEST-9)

### Stripe keeps an account active until the deadline for what is currently due

- **[DOCS]** `currently_due`: "the requirements that you must resolve by the `current_deadline` for the account to
  remain `active`"; `past_due`: "the requirements that have disabled capabilities because they weren't resolved before
  the `current_deadline`". [Stripe: Handle verification with the API](https://docs.stripe.com/connect/handling-api-verification) — read 2026-10-08
- **[DOCS]** "Stripe typically disables payouts on the account if we don't receive the information by the
  `current_deadline` … if payouts are already disabled and the account is unresponsive to our inquiries, Stripe might
  also disable the ability to process charges." [same page](https://docs.stripe.com/connect/handling-api-verification) — read 2026-10-08
  - *Reading:* a direct charge on an account with requirements currently due but not past due should still succeed,
    and payouts stop before charges. Not tested on a live account.

### What a live Playtomic club sees: not found

- **[ABSENT]** What Playtomic Manager shows a live club whose Stripe account is restricted or has information due. Help
  centre searched for stripe, verification, restricted, payouts paused, update your details, account suspended, KYC;
  the Stripe articles cover setup, personal details and rejected payouts only
  ([Online payments with Stripe](https://helpmanager.playtomic.com/hc/en-gb/articles/20535417606161-Online-payments-with-Stripe), [Payout Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/51376628311441-Payout-Issues-how-to-fix-rejected-or-returned-payouts)) — read 2026-10-08.

---

## 9. Apple Pay and Google Pay for one later, unscheduled charge (R-REQUEST-12, R-REQUEST-14)

### Apple's merchant tokens do not cover an unscheduled card on file

- **[DOCS]** "Outside of these supported use cases, MPAN cannot be used for unscheduled card on file (UCOF)"; one-time
  payments use a device token (DPAN) — carried from `gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unscheduled-card-on-file` (read 2026-10-08).

### Google Pay can be saved through Stripe; Google's own categories have no unscheduled one

- **[DOCS]** Stripe's Google Pay page: "Recurring payments: Yes"; "fully compatible with Stripe's products and features
  (for example, recurring payments)"; the React Native SDK confirms a SetupIntent with `confirmPlatformPaySetupIntent`.
  A card added on the phone is a device token (DPAN), one from Chrome or Play a card number (FPAN), and one picked on a
  merchant site an "e-commerce token". [Stripe: Google Pay (React Native)](https://docs.stripe.com/google-pay?platform=react-native) — read 2026-10-08
- **[DOCS]** Google (15 Apr 2026) added three merchant-initiated types to the Google Pay API: recurring, deferred ("the
  payment is authorized upfront but charged at a single point in the future") and automatic reload; the earlier
  specification "was primarily designed for immediate customer initiated transactions". No unscheduled type.
  [Google Developers Blog](https://developers.googleblog.com/new-enhancements-for-merchant-initiated-transactions-with-the-google-pay-api/) — read 2026-10-08
- **[DOCS]** Stripe's own example of saving now and charging only if something happens later: "A crowdfunding website
  that collects card details to be charged later, only if the campaign reaches a certain amount"; a properly saved card
  makes later off-session payments merchant-initiated, under an agreement covering "the anticipated frequency of
  payments (that is, one-time or recurring)". [Stripe: Setup Intents API](https://docs.stripe.com/payments/setup-intents) — read 2026-10-08
  - *Reading:* a card saved by Google Pay can be charged later through Stripe; whether a DPAN keeps working for an
    unscheduled charge after a phone change was not found. On iPhone the Apple limit above stands.

---

## 10. The order control when payment waits for the club (R-REQUEST-1, R-REQUEST-39)

### No authority on a swipe or "I'm in"; the statute covers "a similar function"

- **[ABSENT]** / **[LAW]** Carried from `gaps-FILL.md#no-authority-on-a-swipe-or-a-priced-im-in-as-the-order-control`
  (art. 17 ust. 3 "przycisku lub podobnej funkcji") and `local-market.md#the-order-button-and-a-yes-that-charges-later`
  (CJEU *Conny*: the rule applies when payment is due only after a later condition) — read 2026-10-07/08.

### German courts: no binding order, no contract, and a later confirmation does not repair it

- **[LAW]** AG München, 27.02.2023, 191 C 1446/22: a "Jetzt kaufen" button beside a cart symbol was no offer; the
  provider's emailed booking confirmation was itself the offer ("Ein Angebot der Beklagten … liegt allerdings in der per
  E-Mail übersandten Buchungsbestätigung"), the customer's silence was "ein rechtliches Nullum", and no contract formed
  because the page "genügt … nicht den Anforderungen des § 312 j III BGB"; the 95 % cancellation fee was repaid.
  [gesetze-bayern.de](https://www.gesetze-bayern.de/Content/Document/Y-300-Z-BECKRS-B-2023-N-56288) — read 2026-10-08
- **[LAW]** BGH, 9 Oct 2025, I ZR 159/24 (as reported): a plain "Senden" button left an online brokerage contract
  "endgültig unwirksam"; a later viewing request did not cure it — only an express declaration to pay would.
  Secondary source: [Forvis Mazars newsletter](https://www.forvismazars.com/de/en/who-we-are/news/press-media/newsletters/newsletter-immobilienrecht/newsletter-update-immobilienrecht-1-2026/bgh-online-maklervertrag-ohne-hinweis-unwirksam) — read 2026-10-08
  - *Reading:* if the control that sends a game to the club does not meet the rule, the club's later yes cannot bind
    the player, and charging at that yes takes money under no contract.

---

## 11. Playmore's soft lapse and its open games (R-REQUEST-25)

### The soft lapse is written for a court booking's payment page

- **[POLICY]** The payment page counts down a booking's `payment_auto_cancel_at` ("Opłać do {time}", "Zostało
  {minutes} min — po tym czasie rezerwacja zostanie anulowana."). After it: "Czas na opłacenie minął … Jeśli obiekt go
  nie zwolnił, płatność wciąż utrzyma rezerwację", and the page re-checks the booking 0 s, 15 s, 30 s, then every 1–3
  minutes. [payment page chunk](https://playmore.pl/assets/BNVUkjYD.js), [Polish strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### League half-court seats lapse hard

- **[POLICY]** In the league "kort po połowie" flow a seat is held while someone pays ("Ktoś właśnie opłaca to
  miejsce. Sprawdź za chwilę."), and a late payer is turned away: "Czas na płatność minął. Otwórz mecz jeszcze raz."
  The creator is told "Nieopłacony kort po godzinie wraca do klubu."
  [league strings](https://playmore.pl/assets/CPLsdYdo.js), [booking strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08

### Open games carry no payment window

- **[ABSENT]** A payment window, seat hold or late-payment rule for joining a *gra otwarta*: the open-game strings have
  only the join price, the auto-cancel cut-off and the free-cancel window; the payment page's open-game block only
  sends a visitor to the join page. Searched all Polish string chunks for minut, opłać, wygas, pending, hold — read 2026-10-08.
  - *Reading:* the soft lapse is documented for ordinary court bookings only. Playmore's two flows that hold a place
    for someone part-way through do the opposite: the league seat lapses hard.
