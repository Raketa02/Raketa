# Gap answers — payments pass, market-00 (PLATFORM and FILL)

The market gaps the payments pass left open on PLATFORM and FILL (fourteen lines in the run's gap list), read
2026-10-20. Several researchers ran at once, so where a sibling file written the same day already answers a line, it is
cited, not repeated. One `###` per gap, named by its rule IDs.

**Sources tried this round (new unless marked):**

- Playtomic for Android **6.94.0** (APKPure XAPK, versionCode 37947), decompiled with jadx 1.5.1. The earlier rounds
  read only its strings.
- Playmore's web app as served on 2026-10-20: 1 489 JavaScript files, including the lazily loaded ones and the partner
  terms.
- Mastercard's *Transaction Processing Rules* (10 June 2025), read through the Wayback Machine. The live PDF answered
  403, as it did on 2026-10-11.
- Visa's Core Rules (18 April 2026).
- ING's, PKO BP's and Erste's (ex-Santander) card terms and FAQ.
- Stripe support, W3C's *Understanding SC 2.2.1*, and React Native's and Android's docs.
- German appellate reports from 2026, and three UOKiK decisions from 2026.
- MATCHi's player and venue help APIs, Ravelin's *Global Payments Report 2026*, and WhatsApp for Android's dex files.

The code reads are quoted in
[`../shots/gaps-payments-00-playtomic-6.94.0-playmore-2026-10-20.txt`](../shots/gaps-payments-00-playtomic-6.94.0-playmore-2026-10-20.txt).
Code reads are labelled `[POLICY] (code)`, as in the earlier rounds. Neither app was used signed in, so nothing here is
`[MEASURED]` on a rival.

**Kinds:**

- `[POLICY]` is a company's own rule, term, help or code.
- `[DOCS]` is a provider's, network's, standard's or platform's document.
- `[LAW]` is a statute or ruling.
- `[DATA]` is a vendor's published figure.
- `[COMPLAINT]` is one person's account.
- `[ABSENT]` means looked for and not found, with where.

Lines marked *Reading* are not sources.

| Gap | Rules | Status |
|---|---|---|
| WhatsApp's clock after closing or a restart | R-PLATFORM-48 | not found (device-gated) |
| Playtomic's home and match screen before a read, between reads, offline | R-PLATFORM-50, -51 | answered (code) |
| Polish refusals without the player; MATCHi's failed day-7 take | R-PLATFORM-64 | not found (nearest facts added) |
| How soon a Polish bank drops a released hold; the name beside it | R-PLATFORM-7, -65 | part-answered: the network rule found; banks unpublished |
| Hold ceilings at PKO BP, ING and Santander | R-PLATFORM-7 | answered (sibling file plus Erste's FAQ) |
| A second ask after a missed after-game push | R-PLATFORM-72 | part-answered: both keep the ask in the app; a second push is not found |
| Pushes after signing out | R-PLATFORM-31 | Playtomic answered (code); Playmore's server not found |
| Payout timing: P24, PayU, Reservise | R-PLATFORM-24 | Reservise answered (monthly); PayU one user's account; a club's P24 setting not found |
| P24 and Tpay fees on a refund | R-PLATFORM-19 | answered earlier (cited) |
| Keys on a join or payment retry | R-PLATFORM-2, -6, -14 | answered (Playmore sibling file; Playtomic code) |
| Which screen shows each line, signed in | R-PLATFORM-9, -13 | not found (needs an account) |
| A ruling on a swipe or "I'm in · 40 zł" as the order control | R-FILL-1, -7, -26, -58 | not found; new 2026 German split added |
| How players read "Booking in 10 s"; WCAG 2.2.1 | R-FILL-1 to -3 | accessibility half answered; reading half not found |
| The countdown when the app is left, on two phones | R-FILL-6 | not found (device-gated) |

---

### R-PLATFORM-48 — WhatsApp's clock after the app is closed or the phone restarts: still not found

- Carried:
  - WhatsApp for Android starts messaging work at boot
    (`gaps-S-02.md#whatsapps-android-app-starts-work-when-the-phone-restarts-a-messaging-task-among-it`).
  - An iPhone app the user swiped away is not woken until it is opened again
    (`gaps-S-01.md#an-iphone-app-the-user-swiped-away-is-not-woken-until-it-is-opened-again`).
  - No statement or test was found (`gaps-S-02.md#whether-a-clock-marked-message-leaves-before-whatsapp-is-reopened-still-not-found`).
- **[ABSENT]** New this round: the code behind WhatsApp's `MessagingBootCompleteObserver`.
  - The name occurs once, in `classes7.dex`'s string pool, in the APKPure "latest" build (80 MB, 13 dex files).
  - Neither jadx 1.5.1 (even with source names used as class names) nor dexdump 36.0.0 finds a class built from that
    file, and no decompiled class contains it.
  - So what the observer sends at boot can't be read. Extract §C — read 2026-10-20.
- What would answer it is unchanged: a dated device test. Put the phone in airplane mode, send a message so it shows
  the clock, then swipe WhatsApp away or restart the phone. Reconnect, and note whether the message leaves before
  WhatsApp is opened again.

### R-PLATFORM-50, R-PLATFORM-51 — Playtomic's home and match screen: a spinner first, a re-read on every return, and offline the game vanishes from Home

**Answered from the code of Playtomic for Android 6.94.0** (extract §A2 and §A3). The Android code is all that was read.

- **[POLICY] (code)** **When Home re-reads.**
  - Home re-reads the player's upcoming games and pending actions every time it comes back to the front: on the
    screen's `ON_RESUME`.
  - It loads the tab on `ON_START`.
  - No timer re-reads it. The presenter's only delay (1 s) is for the onboarding paywall and the notification prompt.
  - `HomeTabFragmentKt`, `com.playtomicui.utils.LifecycleEffectsKt`, `HomeTabPresenter`, `HomeTabInteractor`.
- **[POLICY] (code)** **Before the first read lands.**
  - The "Your next activity" carousel starts in a loading state: `HomeActivitiesViewState(isLoading = true)`, passed to
    the carousel.
  - Once the read lands, it shows the games, or hides the whole section when there are none. The section shows only
    while loading or non-empty.
- **[POLICY] (code)** **When a read fails, as it does offline.**
  - Every part of Home's read falls back to an empty list on failure (`GetUserPendingActions`, each request
    `.c(emptyList)`; `Promise.c` resolves a failure with the given value).
  - The interactor also publishes an empty read on a total failure (`nd0` case 20).
  - So a read made with no signal "succeeds" empty. The player's next game and pending actions ("Upload score",
    "Confirm result", "Pending payment") disappear from Home, with no error and no "last updated" line.
- **[POLICY] (code)** **Between reads.** The last read stays in memory and on screen until the next return to Home.
- **[POLICY] (code)** **A match's own screen.**
  - It opens with the match the card handed it, shown at once, and reads the match again by id.
  - It reads again each time the screen is shown (`MatchDetailObserverMiddleware`, on `subscribe`).
  - A failed read leaves the shown match in place. The screen shows an error state only when no match was loaded at all
    (`MatchDetailInteractor`; failure handler `vt0` case 5).
  - No timer re-reads it: no `Timer`, `postDelayed` or `scheduleAtFixedRate` in the match module, apart from a wizard
    cell.
- Carried for the strings:
  - Playtomic's connection errors: "Connection Error", "Could not connect to the server…"
    (`gaps-PLATFORM.md#playtomics-words-while-a-payment-is-pending`, `gaps-PLATFORM.md` §1).
  - Playmore's grey "Dane mogą być nieaktualne" banner over a saved copy, and its 30 s re-read on focus
    (`gaps-PLATFORM.md#playmores-open-game-list-is-not-refreshed-while-it-is-on-screen`).
- *Reading:*
  - Playtomic tells a player nothing when Home is stale or offline. Offline, Home shows the player as having no game,
    which is worse than showing the last known game.
  - The match screen keeps the last known match quietly.
  - Playmore marks a saved copy with its time.
  - The iPhone build was not read.

### R-PLATFORM-64 — How often a Polish bank refuses a charge made without the player, and what MATCHi does when its day-7 take fails: still not found

- Carried: no published rate (`gaps-S-01A-hold.md#how-often-a-polish-bank-refuses-or-asks-on-a-charge-made-without-the-player-still-not-found`,
  `gaps-FILL.md` §15).
- **[DATA]** Nearest new figure. It is about the bank's check, not about charges made without the player.
  - Ravelin's own data puts Poland in the top four for 3-D Secure success at **91 %**, with China; India is at 90 % and
    the UK at 89 %.
  - The report covers 37 countries, Poland among them, from Ravelin's internal data.
  - [Ravelin: Global Payments Report 2026, p. 8](https://pages.ravelin.com/hubfs/PR26%20Global%20Payments%20Report%202026/Global%20Payments%20Report%202026%20by%20Ravelin.pdf) — read 2026-10-20
- **[ABSENT]** A rate of refusals for charges made without the cardholder (merchant-initiated), for Poland or the EEA.
  - Searched Forter's PSD2 pages (UK, Germany, France, Spain and Italy only), Ravelin 2026 (3-D Secure only), and
    vendor blogs (Solidgate, Checkout.com).
  - What would answer it is unchanged: Rakieta's own decline codes once live — read 2026-10-20.
- **[POLICY]** MATCHi, nearest facts (the day-7 take itself is not covered):
  - Player help: "If one of your co-players does not pay for their part of the booking, you as the booker will be
    charged for your co-player's part of the booking according to the regular price."
    [Split Payment Q&A (updated 2026-09-11)](https://matchiplayers.zendesk.com/hc/en-gb/articles/14685446085661-Split-Payment-Q-A)
  - Venue help, the schedule: "an unpaid booking still takes up its slot and appears on the grid just like a paid one."
    [Schedule settings (updated 2026-09-15)](https://matchi.zendesk.com/hc/en-gb/articles/34133368415005)
  - Venue help, statements: "Payments still marked as pending are left off the statement entirely — once captured, they'll
    appear…" [Explanation of the different lines in a statement (2026-09-14)](https://matchi.zendesk.com/hc/en-gb/articles/15268887132317)
  - Venue help, payment links: an unpaid order can be paid from the customer's "unpaid orders" through a payment link,
    and "failed payment attempts remain payable".
    [Working with payment links (2026-09-15)](https://matchi.zendesk.com/hc/en-gb/articles/14858820219165)
  - Venue help, memberships only: "If a renewal payment fails, it's retried automatically — after the maximum number of
    attempts, the renewal order is cancelled and the customer is notified."
    [Add a new membership type (2026-09-15)](https://matchi.zendesk.com/hc/en-gb/articles/11467713631389)
  - All read 2026-10-20.
- **[ABSENT]** A MATCHi article on a booking whose day-7 capture fails.
  - Searched through both Zendesk APIs: "capture", "capture failed", "payment failed", "card declined", "unpaid",
    "unpaid booking", "declined", "debt", "outstanding" and "insufficient" — read 2026-10-20.
- *Reading:* MATCHi's documented failure paths keep the slot booked and leave an unpaid order to chase. Nothing says a
  booking is released when its take fails.

### R-PLATFORM-7, R-PLATFORM-65 — How soon a released hold leaves a Polish bank app, and the name beside it: the network rule is found, the banks' practice is not

- **[DOCS]** **Mastercard's issuer rule.** It could not be read on 2026-10-11
  (`gaps-S-01A-hold.md#mastercards-issuer-rule-on-a-reversal-could-not-be-read`).
  - §2.11.2 *Full and Partial Reversals – Issuer Requirements*: "An Issuer receiving a Reversal Request/0400 message or
    an Acquirer Reversal Advice/0420 message must release any hold placed on funds in the Mastercard or Maestro Account
    in the amount specified within 60 minutes of matching the reversal message to the original authorization request
    message."
  - For the Europe Region, the only change to §2.11.2 concerns prepaid ranges in Italy (p. 77), so the 60 minutes bind
    Polish issuers.
  - [Mastercard: Transaction Processing Rules, 10 June 2025, p. 54 (Wayback copy of 2025-12-16)](https://web.archive.org/web/20251216034228/https://www.mastercard.us/content/dam/public/mastercardcom/na/global-site/documents/transaction-processing-rules.pdf) — read 2026-10-20
- **[DOCS]** **Visa's issuer rule.** §1.7.4.3: "An Issuer must reverse an authorized Transaction from its Cardholder's
  account upon receipt of a Reversal." (ID# 0004383, last updated Oct 2022). No time is stated.
  [Visa Core Rules and Visa Product and Service Rules, 18 April 2026, p. 125](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf) — read 2026-10-20
- Carried, Visa: a reversal that doesn't match leaves the hold 1 to 8 days
  (`gaps-S-01A-hold.md#visa-a-reversal-that-matches-tells-the-bank-to-lift-the-hold-one-that-doesnt-leaves-it-1-to-8-days`).
- Carried, the banks: none of PKO BP, ING, Pekao, Erste or Millennium states a time for a hold the seller cancelled
  (`gaps-payments-01.md#r-fill-13---how-soon-each-of-the-five-banks-drops-a-cancelled-hold-still-not-published`,
  `gaps-payments-06.md#r-clubbook-24--how-soon-a-polish-banks-app-drops-a-hold-rakieta-let-go-unpublished-and-the-email-can-only-say-so`).
- **[POLICY]** Erste Bank Polska, the former Santander Bank Polska (santander.pl now answers 308 to erste.pl):
  - Its card FAQ says a hold "może być utrzymana maksymalnie przez 30 dni (w zależności od rodzaju karty i transakcji)".
  - At a cancellation in a shop, "powinieneś otrzymać stosowny dokument". No time is given for a cancelled hold.
  - [Erste: pytania i odpowiedzi — karty](https://www.erste.pl/klient-indywidualny/kontakt/pytania-i-odpowiedzi-karty) — read 2026-10-20
- **The name.**
  - Carried: Visa requires the same merchant name on the hold as on the payment, and a direct charge carries the club's
    descriptor (`gaps-S-01A-hold.md#visa-requires-the-same-merchant-name-on-the-hold-as-on-the-payment`).
  - Carried: no Polish bank's row for a pending card hold is described
    (`gaps-payments-01.md#r-fill-13---the-name-beside-a-pending-card-hold-still-not-found-for-any-of-the-five-banks`).
  - **[DOCS]** New: the bank, not Stripe, picks the name a banking app shows.
    - Customers "may sometimes see a charge description on their banking app or statement which does not match", because
      banks show "a friendly, human-readable merchant name (sometimes called a 'soft descriptor')".
    - "Stripe has no control over the mapping systems banks and card issuers use". Once the data Stripe sends is right,
      "the card issuer must fix the incorrect merchant name/image mapping on their end."
    - [Stripe support: Why do customers see statement descriptors that don't match what I've set in Stripe?](https://support.stripe.com/questions/why-do-customers-see-statement-descriptors-that-don-t-match-what-i-ve-set-in-stripe) — read 2026-10-20
- *Reading:*
  - Once Stripe's cancellation reaches a Polish bank as a matching reversal, a Mastercard hold must leave within the
    hour. Visa sets no clock.
  - When the hold actually leaves the app, and what name it shows meanwhile, is still each bank's own practice. Only a
    live hold, cancelled and watched on each bank's app, would show it.

### R-PLATFORM-7 — Hold ceilings at PKO BP, ING and Santander (not grade-moving): answered

- Carried from the sibling file written today:
  - PKO BP's personal debit-card terms: a hold is cancelled on settlement or after **7 days**
    (`gaps-payments-01.md#r-fill-13---pko-bps-personal-account-and-debit-card-terms-drop-a-hold-on-settlement-or-after-7-days-and-name-no-sellers-cancellation`).
    This round read the same §52 in PKO's 2018 general terms (§49, 4 August 2018) and in the 2017 terms.
  - ING: at most **8 calendar days**, and **30** where the networks say so. The card terms are in force from 24 August
    2025; the 2021 prepaid business cards say the same 8 days
    (`gaps-payments-01.md#r-fill-13---ings-card-terms-in-force-from-24-august-2025-at-most-8-calendar-days-30-where-the-networks-say-so-lifted-on-the-debit-or-when-no-settlement-comes`).
  - Santander, now Erste: at most **30 days**, by card and transaction type (FAQ above;
    `gaps-payments-01.md#r-fill-13---erste-lists-card-holds-and-refused-payments-in-the-apps-history-since-july-2021`).
  - mBank: 30 days, 14 online (carried, `gaps-PLATFORM.md` §8).
- **[ABSENT]** A 2025 or 2026 version of PKO's personal debit-card terms (also searched this round), and ING's
  personal debit-card sheet — read 2026-10-20.

### R-PLATFORM-72 — A second ask when the first after-game push is missed: both rivals keep the ask in the app; a second push is not found

- Carried:
  - Playtomic documents one push after the match ("After your match ends, you'll receive a notification…"), and keeps
    "Upload score" and "Confirm result" on Home for up to a week
    (`gaps-RESULT.md#playtomic-documents-one-push-after-the-match-ends-and-keeps-the-rest-inside-the-app`).
  - Playmore sends a push after the game that opens the result sheet
    (`gaps-RESULT.md#playmore-sends-a-push-after-the-game-and-shows-the-clock-on-the-reservation`).
- **[POLICY] (code)** Playtomic 6.94.0 schedules no local reminder.
  - Its local notifications have three categories (general, chat, social), and nothing about results.
  - The Home pending actions are re-read each time Home comes back to the front (previous gap). So the ask is shown
    again on every visit until the week ends, but never pushed again by the phone. Extract §A2 and §A4.
- **[POLICY] (code)** Playmore, as served 2026-10-20 (extract §B1):
  - **Open games.** The reservation's "Po meczu" tile ("Wynik, znajomi z gry i kolejny mecz w jednym miejscu", with
    "Wpisz wynik" / "Potwierdź wynik") shows from the game's start for **72 hours**: `now ≥ start && now < start + 2592e5`
    in [`-UbPNqVj.js`](https://playmore.pl/assets/-UbPNqVj.js), used by `OpenGamePostGameEntry`.
  - **Court bookings with added players.** The "report" and "confirm" prompts last until **7 days** after the booking's
    end (`B = 6048e5`).
  - **Ladders (Challenger).** Playmore says outright that it reminds: "Jeśli przez {duration} po zaplanowanym starcie
    meczu żaden z Was nie wpisze wyniku, system wyśle Wam przypomnienie. Bez kary — wpiszcie wynik kiedy zdążycie."
  - **Leagues.** It says the same: "Po tym czasie przypomnimy Wam automatycznie"; "Jeśli zapomnicie, przypomnimy Wam
    {duration} po końcu kolejki." [`CtEmagZ3.js`](https://playmore.pl/assets/CtEmagZ3.js)
  - Read 2026-10-20.
- **[ABSENT]** A second push for an open game's or a court booking's result, at either rival.
  - Searched Playmore's 1 489 files for "przypomn", "remind" and "reminder" near result, score and game; only the
    league and ladder lines above were found.
  - Searched Playtomic's local notifications and strings. Server-sent pushes can't be seen from either app.
  - Read 2026-10-20.
- *Reading:* where Playmore promises a reminder (leagues, ladders), it says so in the rules. For casual games, both
  rivals rely on a prompt that stays in the app: 72 hours on Playmore's open-game tile, a week on Playtomic's Home.

### R-PLATFORM-31 — Pushes after signing out: Playtomic's phone stays registered; whether its server or Playmore's still pushes is not seen

- **[POLICY] (code)** Playtomic 6.94.0 (extract §A1):
  - Signing out asks for confirmation, then only clears the session on the phone: the access and refresh tokens, two
    user stores, the web cookies, and the signed-in flag (`AuthenticationService.logout()`).
  - It makes no call to the server and does not delete the Firebase token. No `deleteToken` exists in Playtomic's own
    code.
  - The phone's push token is registered by `POST /v1/notifications/tokens` with the token, platform, device id, app and
    language. The app has no call that removes a token.
  - The app registers the token again whenever the signed-in user differs from the one it last registered for
    (`NotificationManagerDelegate.a`).
- Carried: Playmore's sign-out also leaves the push token registered. It is removed only when the player turns pushes
  off (`gaps-PLATFORM.md#playmores-sign-out-does-not-unregister-the-phone`).
- **[ABSENT]** Whether either server stops pushing a signed-out phone, or moves the token to the next account. Server
  behaviour can't be read from the apps, and no help page or complaint covers it — read 2026-10-20.
- *Reading:*
  - At both rivals, a signed-out phone stays registered for pushes. Whether pushes still arrive depends on the server.
  - Playtomic re-registers the same token for the next account that signs in. That suggests its server then treats the
    phone as that account's. It is not proven.

### R-PLATFORM-24 — Payout timing: Reservise pays clubs monthly; PayU's timing is only in one user's account; a club's own Przelewy24 setting is not public

- **[POLICY]** Reservise, Playmore's company, pays clubs **monthly**. This answers the earlier `[ABSENT]` in
  `platforms.md#playmore--the-clubs-money-passes-through-reservise`.
  - Its partner terms (last updated 15.08.2025) say online payments go "chwilowo na nasz rachunek".
  - Its fees "będą dokonywane w okresie rozliczeniowym obejmującym jeden miesiąc kalendarzowy".
  - "Po rozliczeniu przekazujemy na Twój rachunek bankowy łączną kwotę wpłaconą przez Użytkowników … w danym okresie
    rozliczeniowym", with the fees "potrącane z wypłaty".
  - [Playmore: Regulamin dla Partnerów](https://playmore.pl/legal/partner-terms) (text served in
    [`Cw-tKkmq.js`](https://playmore.pl/assets/Cw-tKkmq.js)) — read 2026-10-20
  - No number of days after the month's end is stated.
- **[COMPLAINT]** PayU, one community member's account:
  - "Środki są przelewane do końca następnego dnia roboczego od zlecenia wypłaty". A payout ordered on a non-working day
    counts from the next working day.
  - It concerns PayU payouts for Allegro sellers, on 29-12-2020.
  - [Allegro community: Wypłata z PayU](https://spolecznosc.allegro.pl/t5/pocz%C4%85tkuj%C4%85cy-sprzedawcy/wyp%C5%82ata-z-payu/m-p/138351) — read 2026-10-20
- **[ABSENT]** PayU's own statement of how long a payout takes.
  - Searched PayU Poland's documents through the search engine: *Regulamin Systemu* annex no. 4 (2022 and 2025 versions,
    tokenisation only) and the complaints rules.
  - Carried: `gaps-PLATFORM.md#payu-manual-or-every-n-days-timing-not-published` — read 2026-10-20.
- **[ABSENT]** The payout schedule a small Kraków club on Przelewy24 actually sets.
  - It is a setting in the club's own panel. Nothing public names a club's choice.
  - Carried: the 1 000 zł default, the daily option, and money available by the end of the next business day
    (`gaps-PLATFORM.md#przelewy24-available-by-the-end-of-the-next-business-day-paid-out-on-request-or-by-a-schedule`).
  - What would answer it: asking two or three clubs.
- *Reading:* a Kraków club on Playmore waits up to a month plus a settlement for its online money. On its own
  Przelewy24 account it waits days, or less on a daily schedule.

### R-PLATFORM-19 — Whether Przelewy24 or Tpay keep their fee on a refund: answered in an earlier round

- Carried:
  - **Przelewy24** keeps the commission, and the refund itself is free: "Prowizja za zrealizowaną płatność jest
    bezzwrotna" (`gaps-CLUBBOOK.md#przelewy24-the-refund-is-free-the-commission-is-kept`).
  - Its terms say the same: "Zwrot Płatności … nie stanowi podstawy do zwrotu przez Przelewy24 opłat, prowizji" (§10
    ust. 13), in `gaps-CLUBMONEY.md`.
  - **Tpay** keeps the commission, and charges a card refund like a card payment (1 zł per refund on Starter for
    non-card payments)
    (`gaps-CLUBBOOK.md#tpay-the-commission-is-kept-and-a-card-refund-is-charged-like-a-card-payment`).
  - The worked 160 zł example is in the same file.
- *Reading:*
  - Charge-then-refund through either gateway costs a club the full commission on every share it hands back.
  - Playmore's own called-off open games refund to Playmore's wallet (`platforms.md`, the rivals table). Whether that
    wallet refund reaches the gateway at all is not documented.

### R-PLATFORM-2, R-PLATFORM-6, R-PLATFORM-14 — Keys on a retried join or payment (not grade-moving): Playmore keys every payment; Playtomic sends no key

- Carried and confirmed: Playmore sends an `idempotency_key` with every booking and share payment, the open-game join
  included. A new key is made per press, and the same key is used on its own retries
  (`gaps-payments-05.md#r-rescue-19--playmore-sends-an-idempotency-key-with-every-booking-and-payment-the-open-game-join-included-a-new-one-per-press-the-same-one-on-its-own-retries`).
  - **[POLICY] (code)** This round's read agrees. `/payment/create`, `/payment/create_auth` and `/split/{id}/pay` go
    through one helper ([`Deodb_08.js`](https://playmore.pl/assets/Deodb_08.js)). It adds a random UUID unless the
    caller passes one, and `createOnlinePayment` never does.
  - The helper re-posts the same body and key while the server answers `REQUEST_IN_PROGRESS` (every 3 s, up to 45
    times), or on a 429 multi-click (up to twice, 1,2 s apart). Extract §B2 — read 2026-10-20.
- **[POLICY] (code)** Playtomic 6.94.0 sends no idempotency key (extract §A4).
  - Its requests carry `X-Requested-With`, `User-Agent` and `X-Playtomic-Device-Id`, and no key or request id.
  - Its HTTP clients have no automatic retry.
  - A payment starts with `POST /v1/payment_intents` carrying `allowed_payment_method_types`, `user_id` and
    `cart.requested_item`.
  - Read 2026-10-20.
- *Reading:* at Playtomic, a second press creates a second payment intent on its server. Any de-duplication happens
  there, out of sight.

### R-PLATFORM-9, R-PLATFORM-13 — Which screen shows each rival's line, measured signed in (not grade-moving): not found

- **[ABSENT]** Not measured: it needs signed-in accounts at Playtomic and Playmore, and no account was made.
- What the code says is carried:
  - Playmore's lines name their place: the game preview, the pay page, an invitation, and booking details while a
    payment is checked (`gaps-PLATFORM.md#playmore-says-who-was-faster-and-that-nothing-was-taken`,
    `gaps-PLATFORM.md#playmore-tells-the-player-not-to-pay-twice-while-it-checks`).
  - Playtomic's strings carry no screen names (`gaps-PLATFORM.md#playtomics-words-for-a-full-match-or-a-gone-slot`).
- This round read the namespaces of Playmore's lines:
  - "Skład tej gry jest już pełny" is `openGameJoin.leadFull`.
  - "Komplet — Wszystkie miejsca zajęte" is `preview.fullHint`.
  - "Sprawdzamy status płatności" and "Przetwarzamy Twoją płatność" are `details.status.payment.initialCheck` and
    `processing`.
- What would answer it: a signed-in walk of each app at a full game and a slow payment, with screenshots.

### R-FILL-1, R-FILL-7, R-FILL-26, R-FILL-58 — A ruling or a lawyer's opinion on a swipe, or on "I'm in · 40 zł", as the order control: still none; German appeal courts split in 2026 on what a bad button costs

- Carried: no authority on a swipe or a priced "I'm in"; Polish lawyer still needed
  (`gaps-FILL.md#no-authority-on-a-swipe-or-a-priced-im-in-as-the-order-control`,
  `gaps-payments-04.md#r-rescue-14--whether-im-in--40-zł-meets-the-order-button-rule-no-new-authority`).
  The carried rulings are:
  - *Fuhrmann-2*: only the words on the button count
    (`gaps-POST.md#c-24921-only-the-buttons-own-words-count-not-the-text-around-it`).
  - *Conny*: the duty applies when payment depends on a later condition
    (`local-market.md#the-order-button-and-a-yes-that-charges-later`).
  - BGH I ZR 159/24: "Senden" is not enough.
- **[LAW]** New, as reported: German appeal courts disagree on whether a button that fails § 312j(3) BGB still leaves a
  contract when the price was plain.
  - **OLG Braunschweig, 18 Dec 2025, 9 U 69/25.** A Tesla bought through a button reading "Bestellen". The button breaks
    § 312j(3), but the contract stands. The court narrowed § 312j(4) because the buyer "could not have overlooked" that
    the car cost money: the financing lines stood directly above the button.
    [jura-online (29 Jul 2026)](https://jura-online.de/blog/2026/07/29/rechtsfolge-der-buttonloesung-kaufvertrag-trotz-mangelhaften-bestellbuttons-wirksam/),
    [beck-aktuell (18 Feb 2026)](https://www.beck-aktuell.de/heute-im-recht/rechtsprechung/olg-braunschweig-9u6925-bestellbutton-tesla-kauf-internet-teleologische-reduktion-2026-02-18)
  - **OLG Frankfurt, 15 Sep 2026, 9 U 76/25.** The same result for a car bought through "Bestellen".
  - **Kammergericht Berlin, 17 Sep 2026, 1 U 25/25.**
    - "Bestellen" fails, and "sei schon gar kein Vertrag zustande gekommen".
    - The court refused the narrowing: "Eine teleologische Reduktion der Norm komme demnach gerade nicht in Betracht".
    - Only the moment of the buyer's declaration counts, "ungeachtet vorheriger Hinweise".
    - It departs expressly from OLG München 13 U 3232/24, OLG Hamm 34 U 6/25, OLG Braunschweig 9 U 69/25 and its own
      26th senate (26 U 17/25). It allowed an appeal to the BGH "zur Sicherung einer einheitlichen Rechtsprechung".
    - [LTO, 25 Sep 2026](https://www.lto.de/recht/nachrichten/n/kg-1u2525-auto-online-bestell-knopf-button-zahlungspflichtig-bestellen)
  - All read 2026-10-20, from reports, not the judgments.
- **[ABSENT]** A Polish 2026 decision on the order button.
  - The three UOKiK decisions of 2026 found by the search say nothing of "przycisk" or "obowiązkiem zapłaty":
    [RKR-2/2026 (Beliani, 20 Apr 2026)](https://uokik.gov.pl/Download/1910), [DOZIK-1/2026](https://uokik.gov.pl/Download/1743)
    and [DOZIK-2/2026](https://uokik.gov.pl/Download/1754).
  - The Glovo charges of May 2023 still show no decision.
  - No ruling, German or other, on a gesture or a price printed on the control.
  - Read 2026-10-20.
- *Reading:*
  - None of these courts looked at a swipe or a price on the control. Under the Kammergericht's strict reading, which
    matches *Fuhrmann-2*, a control that names joining and not paying forms no contract. A price shown on the control or
    next to it would not save it.
  - The lenient courts weigh how plain the price was, and a price on the control would help there.
  - The BGH appeal will decide which line holds in Germany. Poland has no case yet, so the lawyer's opinion is still
    needed.

### R-FILL-1 to R-FILL-3 — How players read "Booking in 10 s", and whether a ten-second Undo is a time limit WCAG 2.2.1 wants adjustable: the standard's own definition says it is; the reading still needs players

- Carried, Android's half:
  - Android's "Time to take action (Accessibility timeout)" setting lets a person choose 10 s, 30 s, 1 min or 2 min.
  - `getRecommendedTimeoutMillis` ("Controls should remain on the screen for at least this long…").
  - Material's Snackbar honours the setting, and with a screen reader on older phones it never times out
    (`gaps-payments-04.md#r-rescue-15--a-ten-second-undo-before-money-moves-what-android-does-for-people-who-need-longer-new-how-players-read-it-still-needs-players`).
- **[DOCS]** New, W3C's own definition of a time limit:
  - "Any process that happens without user initiation after a set time or on a periodic basis is a time limit."
  - The exception: "Content that operates on a timer does not need to be time adjustable if there is an alternative
    that does not rely on a timer". The example given is a mail client's toast that disappears after a few seconds while
    the inbox still holds the mail.
  - [W3C: Understanding SC 2.2.1 Timing Adjustable (WCAG 2.2)](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html) — read 2026-10-20
- **[DOCS]** React Native exposes the Android setting to apps:
  - `AccessibilityInfo.getRecommendedTimeoutMillis(originalTimeout)` (Android) "Gets the timeout in millisecond that the
    user needs. This value is set in 'Time to take action (Accessibility timeout)' of 'Accessibility' settings."
  - [React Native docs: AccessibilityInfo](https://reactnative.dev/docs/accessibilityinfo) (source
    [docs/accessibilityinfo.md](https://raw.githubusercontent.com/facebook/react-native-website/main/docs/accessibilityinfo.md)) — read 2026-10-20
- *Code, for comparison (the copy at `9ab0ea5b`):*
  - Rakieta's window is a fixed `UNDO_WINDOW_MS = 10_000` (`frontend_player/src/features/proposals/domain/fill.ts:42`).
  - No file under `frontend_player/src` calls `getRecommendedTimeoutMillis`.
- **[ABSENT]** How players read "Booking in 10 s": as money being held, or not. No study or test was found. Only testing
  with players can say (carried, `gaps-RESCUE.md#needs-players-not-research`).
- *Reading:*
  - By W3C's definition, a count that sends the yes and the hold when it ends, unless the player presses Undo, is a time
    limit on the Undo.
  - It is exempt only if an equal way to undo exists without the timer. Leaving the game free of charge afterwards could
    serve, if that is free and as easy. Otherwise 2.2.1 wants the ten seconds to be turned off, extended, or stretched to
    at least 100 seconds.
  - On Android, the platform's way is to honour the user's chosen time, which React Native can read.

### R-FILL-6 — The countdown when the app is left within two seconds, on the Galaxy A55 and the iPhone: still not found

- Carried: what React Native 0.76.9 and Apple document.
  - On Android, timers stop while the app is in the background.
  - On iOS, timers run for a few seconds, then the app is suspended.
  - `gaps-FILL.md#on-android-react-native-stops-firing-timers-while-the-app-is-in-the-background`,
    `gaps-FILL.md#on-ios-timers-keep-running-briefly-then-the-app-is-suspended`.
- **[ABSENT]** A device run. It is a measurement of Rakieta on the walker's phones and seeded store, which a researcher
  does not touch. It stays for the walk.
  - Say Book it now, press Home within two seconds, wait a minute, then read the booking's time and the console's Sent
    pane, on each phone.
  - Read 2026-10-20.
