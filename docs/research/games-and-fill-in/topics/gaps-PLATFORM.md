# Gap answers — PLATFORM

Answers to the PLATFORM gaps of PRD #530 (`areas/PLATFORM/gaps.md` in the story work dir), read
2026-10-08. Each `##` names the rule IDs it answers; every fact sits under a `###` heading so it
can be cited as `topics/gaps-PLATFORM.md#<heading>`.

**Sources.** Playmore's interface text and behaviour come from the JavaScript its web app serves to
every visitor (playmore.pl, the same code its phone app wraps: it carries Capacitor push, badge and
app-state hooks); asset names are hashed and change with each release, so each line names the file
as read on 2026-10-08. Playtomic's interface text comes from the string table of its Android app,
version 6.93.2 (package `com.playtomic`, APKPure copy last modified 2026-10-08); the strings carry no
screen names, and the table also holds Stripe Link and Zendesk chat strings. Neither app was used
signed in, so nothing here is `[MEASURED]`.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published
price · `[DOCS]` a provider's or bank's document · `[COMPLAINT]` one person's account · `[ABSENT]`
looked for and not found, with where. Lines marked *reading* are not sources.

## 1. Pressing with no signal, and whether anything waits to be sent (R-PLATFORM-46, R-PLATFORM-48)

### Playmore blocks every write while offline and keeps nothing to send later
- **[POLICY]** A request interceptor refuses any POST, PUT, PATCH or DELETE before it leaves the phone when the browser reports offline and no request has succeeded in the last 30 s ("Network offline — write blocked", code `ERR_OFFLINE_BLOCKED`); the player sees the toast "Brak połączenia z internetem. Spróbuj ponownie, gdy wróci zasięg." Reads (GET) get a 15 s timeout. No queue, outbox or retry of a refused write exists in the code. [Playmore web app: network module `assets/Cng0yjU9.js`](https://playmore.pl/assets/Cng0yjU9.js), [strings `assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** A banner across the top of every screen: amber "Brak połączenia z internetem" when offline, grey "Serwer nie odpowiada. Sprawdzamy połączenie…" when the server is slow; a screen shown from the saved copy says "Dane mogą być nieaktualne — Nie udało się połączyć z serwerem. Pokazujemy ostatnią zapisaną wersję ({time})". [`assets/index-C8d-0CWt.js`](https://playmore.pl/assets/index-C8d-0CWt.js) (NetworkStatusBar), [strings `assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** Where a flow can be resumed it says so: "Brak połączenia z internetem. Sprawdź zasięg i spróbuj ponownie — nie musisz zaczynać od nowa" (linking a phone number to an account). [strings `assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** Only the push-token registration is exempt from the offline gate (`offlineGateExempt`); a join, a leave, a payment and an answer to an invitation all go through it. [`assets/DYS4n-xJ.js`](https://playmore.pl/assets/DYS4n-xJ.js) — read 2026-10-08
- *Reading:* at Playmore a press with no signal is refused at once, with words, and nothing is sent when the signal returns; joining there is paying, so it cannot be done offline at all.

### Playtomic shows a connection error and has no words for a press sent later
- **[POLICY]** The app's own error lines: "Connection Error"; "An error occurred. Check your connection and try again."; "Could not connect to the server. Check your connection and try again"; "We were unable to connect. Please check your wifi/data connection and try again."; "We are experiencing issues connecting to our payments provider. Please check your internet connection and try again."; in chat "Offline. You won't receive messages." and "Reconnecting…". [Playtomic Android 6.93.2 string table (APKPure)](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08
- **[ABSENT]** No string about an action kept and sent once the signal returns ("when you're back online", "will be sent", "queued", "pending sync") in the 6,187 base strings or the 3,336 English ones; the only "Sending…" belongs to the chat. Same source — read 2026-10-08
- **[POLICY]** Playtomic's own fix for connection errors is to reinstall the app, use "a stable internet connection; connect to Wi-Fi if possible" and turn off a VPN. [Playtomic: How to fix app issues](https://playerhelp.playtomic.com/hc/en-gb/articles/48990072840721-How-to-fix-app-issues-and-report-a-problem-to-Playtomic) — read 2026-10-08

### No rival keeps a press made offline once the app is closed
- **[ABSENT]** Neither Playmore's code (offline writes refused, nothing stored to resend; the only state kept on the phone across a reload is a standing-slot request's idempotency key, below) nor Playtomic's strings show an answer kept and sent after the app is closed. Searched Playmore's 1,363 JavaScript files for queue, outbox, background sync and service-worker sync: the queues found hold invitations, logs and analytics, never a player's answer; Playtomic's string table as above. [Playmore web app](https://playmore.pl/), [Playtomic Android 6.93.2](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08
- **[POLICY]** Carried, same finding from other rounds: `gaps-SWIPE.md#playmore-refuses-a-write-while-offline-it-never-queues-one`, `gaps-FILL.md#no-consumer-booking-or-payment-app-keeps-a-join-made-offline`.

## 2. When the reply never comes (R-PLATFORM-13)

### Playmore tells the player not to pay twice while it checks
- **[POLICY]** "Bank jeszcze nie potwierdził płatności. Sprawdź za chwilę, czy przeszła, zanim zapłacisz ponownie." (a share's payment unconfirmed); booking details while checking: "Sprawdzamy status płatności — Trwa weryfikacja statusu płatności. Proszę czekać…", then "Przetwarzamy Twoją płatność — Płatność przyjęta — status zaktualizuje się sam. Nie płać ponownie."; a booking's status "Płatność w toku". [strings `assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** Wallet payments: "Nie udało się potwierdzić płatności Apple Pay — odśwież tę stronę i sprawdź, czy zapis jest już opłacony, zanim spróbujesz ponownie." (same for Google Pay); a changed price: "Kwota do zapłaty zmieniła się — nic nie zostało pobrane." [strings `assets/BC_1Vm5t.js`](https://playmore.pl/assets/BC_1Vm5t.js), [`assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** A request still being processed has its own words: "Wciąż zapisujemy Twój wniosek. Sprawdź za chwilę w Moich rezerwacjach." (standing slot); "Wciąż odwołujemy terminy. Sprawdź za chwilę." [strings `assets/DyQUCw1g.js`](https://playmore.pl/assets/DyQUCw1g.js) — read 2026-10-08
- **[POLICY]** At the payment deadline: "Sprawdzamy, czy termin jest jeszcze zajęty" (carried from `platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`).

### Playtomic's words while a payment is pending
- **[POLICY]** "Processing payment...", "Processing…", "Payment pending", "Pending payment"; failures: "An error occurred during the operation. Please try again.", "Sorry, an error has occurred, try again in a few minutes", "Oops! Something went wrong!". [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08
- **[ABSENT]** No string telling the player not to pay again, or to check whether a payment went through, after a lost reply. Same source — read 2026-10-08
- **[POLICY]** Help, for a match paid but not shown: the bank "temporarily withholds the amount", wait a few days (carried from `competitor-joiner.md#3-d-secure-and-failed-payments`).

## 3. The last spot gone a moment before a join (R-PLATFORM-9)

### Playtomic's words for a full match or a gone slot
- **[POLICY]** "This match is full"; "The match is full, and there are no available spots"; "The time slot is no longer available."; "You cannot change your votes because this match is already full."; a card's teaser "<b>Last available spot</b> for <b>%1$s</b>". [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08
- **[ABSENT]** No string saying another player took the spot first or that nothing was charged; the help centre has no article on a join refused because the match filled. [Playtomic help: Request a spot](https://help.playtomic.com/en/articles/4498075-request-a-spot-in-a-match), string table as above — read 2026-10-08

### Playmore says who was faster and that nothing was taken
- **[POLICY]** Classes: "Ktoś właśnie zajął ostatnie wolne miejsce. Płatność nie została pobrana." Matches waiting for a rival: "Ten mecz ma już komplet — Ktoś był szybszy. Zobacz inne korty, które czekają na rywala."; while another player pays: "Ktoś właśnie dołącza — Jeśli nie zapłaci do {time}, miejsce wróci. Sprawdź za chwilę."; the rule up front: "Gra ten, kto pierwszy opłaci miejsce. Na płatność masz 10 minut." [strings `assets/Ct1XsxUt.js`](https://playmore.pl/assets/Ct1XsxUt.js), [`assets/CPLsdYdo.js`](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** Open games: a full game's preview "Komplet — Wszystkie miejsca zajęte. Zajrzyj do innych gier albo załóż własną."; the pay page "Skład tej gry jest już pełny."; an invitation "Na korcie nie ma już wolnego miejsca." [strings `assets/Ct1XsxUt.js`](https://playmore.pl/assets/Ct1XsxUt.js), [`assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js), [`assets/CbBkX2Te.js`](https://playmore.pl/assets/CbBkX2Te.js) — read 2026-10-08

## 4. One charge per act: how rivals key retries (R-PLATFORM-2, R-PLATFORM-6, R-PLATFORM-14)

### Playmore never retries a write and keys some acts
- **[POLICY]** The app retries automatically only reads (GET, HEAD) after a timeout or a gateway error; a write is never resent by the client. [`assets/Cng0yjU9.js`](https://playmore.pl/assets/Cng0yjU9.js) — read 2026-10-08
- **[POLICY]** A server answer matching "multi-click" is recognised and not retried, so the server refuses a second press. Same file — read 2026-10-08
- **[POLICY]** Standing-slot requests, their acceptance and their cancellation carry an `idempotency_key`: one key per act, kept on the phone with a hash of the request, reused when the same request is sent again and dropped once an answer comes; while the first is still running the server answers `REQUEST_IN_PROGRESS` and the app polls every 3 s, up to 45 times. Open-game joins and booking payments were not seen to carry a key. [`assets/DA5jpXa4.js`](https://playmore.pl/assets/DA5jpXa4.js), [`assets/CmHDsq0P.js`](https://playmore.pl/assets/CmHDsq0P.js), [`assets/pir8ZsJu.js`](https://playmore.pl/assets/pir8ZsJu.js) — read 2026-10-08
- **[ABSENT]** Playtomic: nothing public on how a retry is keyed; the Android strings hold no duplicate-payment warning. [Playtomic Android 6.93.2](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08

## 5. Seats changing while a card is watched (R-PLATFORM-50)

### Playmore's open-game list is not refreshed while it is on screen
- **[POLICY]** The open-games list loads when opened and again only when the date filter widens; no timer, push channel or socket re-reads it (the code holds no WebSocket). The card's only timer is the countdown strip, which re-computes its "Komplet do… · Zostało…" text every 30 s from data already loaded. The club page's game teasers re-read when the page is shown again after at least 60 s away. [open-games list `assets/BfBfjPsN.js`](https://playmore.pl/assets/BfBfjPsN.js), [panel `assets/DM7ksFDa.js`](https://playmore.pl/assets/DM7ksFDa.js), [60-second re-read `assets/D0m80LOl.js`](https://playmore.pl/assets/D0m80LOl.js) — read 2026-10-08
- **[POLICY]** Elsewhere the app re-reads on return to the app, at most once every 30 s ("RefetchOnFocus"), and a split payment's shares are polled every 30 s while one is still pending, up to 40 times, only while visible. [`assets/Cng0yjU9.js`](https://playmore.pl/assets/Cng0yjU9.js), [`assets/D-b_RkfX.js`](https://playmore.pl/assets/D-b_RkfX.js) — read 2026-10-08
- **[ABSENT]** Playtomic: no source on whether a match card updates while watched; its card shows no spot count (carried from `competitor-joiner.md#no-spot-count-and-no-deadline-on-the-card`).

## 6. Pushes after signing out or switching account (R-PLATFORM-31)

### Playmore's sign-out does not unregister the phone
- **[POLICY]** Signing out clears the session and the wallet cache, records "user_logged_out" and sets the app-icon badge to 0; it does not call the push-token removal (`DELETE /push_token`). That call is made only when the player turns pushes off ("[PushConsent] deletePushToken failed (muted locally anyway)"). Signing in registers the token again (`POST /push_token`). [store `assets/Cv3K5GjF.js`](https://playmore.pl/assets/Cv3K5GjF.js), [`assets/B3ivJW8g.js`](https://playmore.pl/assets/B3ivJW8g.js), [`assets/DYS4n-xJ.js`](https://playmore.pl/assets/DYS4n-xJ.js), [badge `assets/DHtHdiNm.js`](https://playmore.pl/assets/DHtHdiNm.js) — read 2026-10-08
- *Reading:* whether Playmore's server stops pushing a signed-out phone, or moves the token to the next account that signs in, cannot be seen from the app.
- **[ABSENT]** Playtomic: no help article, string or complaint on pushes after signing out or with a second account; help covers only switching categories off. [Playtomic: manage notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App), Android strings ("Are you sure you want to log out?" is the only sign-out line) — read 2026-10-08

## 7. How soon a Kraków club's own online payments reach its bank (R-PLATFORM-24)

### Which gateways Kraków clubs use today
- **[POLICY]** Atras (on Playmore): "Rozliczenia transakcji kartą kredytową i e-przelewem przeprowadzane są za pośrednictwem Przelewy24.pl"; Squash4You (on Playmore): "Opłaty za rezerwację dokonać można on-line (Przelewy24)". tenis4U clubs pay through Przelewy24 and Tpay, kluby.org clubs through Przelewy24 and PayU (carried from `platforms.md#tenis4u--payment-and-the-2--refund-deduction`, `platforms.md#kluby-org--payments-partial-prepayment-and-its-fee`). [Atras regulamin](https://www.atrassquash.pl/regulamin/), [Squash4You regulamin](https://www.squash4you.pl/regulamin) — read 2026-10-08

### Przelewy24: available by the end of the next business day, paid out on request or by a schedule
- **[DOCS]** OWU Przelewy24 v2.0 (in force from 15 May 2026), §10 "Rozliczenie (wypłaty)", item 6: money from a completed payment is made available to the merchant for payout "nie później niż do końca następnego Dnia Roboczego po otrzymaniu Płatności", unless anti-money-laundering measures prevent it; the merchant may agree to a later date. A settlement report is generated in the panel every day (item 4). [OWU Przelewy24 v2.0 (PDF)](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf) — read 2026-10-08 (text reconstructed from the PDF's font maps, a few letters lost)
- **[DOCS]** Item 7: payouts are made on request in the panel or on a schedule set there (e.g. everything on a set day of the week or month, or whenever a set amount builds up); by default a payout is made on the business day the made-available, unpaid sum reaches or passes 1000 zł, which the merchant may change straight after registering. Same document — read 2026-10-08
- **[POLICY]** Carried: P24's panel manual states the same 1000 zł default and lists each payout under "Historia wypłat" (`gaps-EMAIL.md#przelewy24-pays-out-on-a-threshold-or-a-schedule-and-lists-each-payout-in-the-panel`).
- *Reading:* a small club taking a few hundred złoty a day on the default setting is paid only every few days; on a daily schedule, by the business day after the next.

### Tpay: on request or automatically, transfer within three business days
- **[POLICY]** "Środki mogą być wypłacane ręcznie lub automatycznie, co ilość środków lub co ilość dni … Przelew zostanie zrealizowany na wskazany przez Państwa rachunek bankowy w terminie maksymalnie do trzech dni roboczych." (updated 25.03.2025). [Tpay: Jak mogę wypłacić środki](https://support.tpay.com/pl/faq/jak-moge-wyplacic-srodki-zgromadzone-na-koncie-w-tpay-com) — read 2026-10-08

### PayU: manual or every N days, timing not published
- **[DOCS]** Each shop has its own balance, paid out with "Pay out funds" or by automatic payouts set as "the number of days after which payouts will be processed", with a minimum amount. [PayU: Payouts panel](https://developers.payu.com/europe/docs/payouts/payouts-panel/) — read 2026-10-08
- **[ABSENT]** How long a PayU payout takes to reach the bank: not on the payouts page, the developer docs or PayU Poland's business pages; the acceptor agreement template defines working days but its commercial terms (where timing would sit) are not public. [PayU umowa z akceptantem (template)](https://poland.payu.com/wp-content/uploads/sites/14/2020/09/umowa_z_akceptantem.pdf) — read 2026-10-08
- **[ABSENT]** How often a club on Playmore is paid by Reservise (carried from `platforms.md#playmore--the-clubs-money-passes-through-reservise`).

## 8. Holds in a Polish bank app, and whose name a pending hold carries (R-PLATFORM-7)

### mBank keeps an unsettled card hold at most 30 days
- **[DOCS]** mBank (debit cards for firms in retail banking, in force from 3 December 2024): a hold "widnieje do czasu pierwszego z następujących zdarzeń: transakcja kartowa dojdzie do skutku lub anuluje ją odbiorca, lub rozwiąże się samodzielnie bez rozliczenia"; "Blokadę autoryzacyjną utrzymujemy nie dłużej niż 14 / 30 dni" — 14 days for transactions up to 19.02.2025, 30 days from 20.02.2025; after that the bank releases it and raises the available balance. [mBank: Regulamin kart debetowych dla firm, p. 7](https://www.mbank.pl/pdf/firmy/karty/regulamin-kart-debetowych-dla-firm-od-3-12-2024.pdf) — read 2026-10-08
- **[DOCS]** mBank set the earlier 14-day ceiling in 2011. [mBank: Zmiana regulaminu (2.09.2011)](https://www.mbank.pl/komunikaty/klienci-indywidualni/1036-zmiana-regulaminu-mbanku/) — read 2026-10-08
- **[POLICY]** Carried: mBank's consumer card FAQ lifts the hold when the merchant's cancellation arrives ("Kiedy dostaniemy potwierdzenie, że sprzedawca anulował płatność, zdejmiemy blokadę"), otherwise after 14 days for an internet purchase (`gaps-FILL.md#mbank-lifts-a-hold-when-the-merchants-cancellation-arrives-at-most-14-days-online`); Playtomic warns a hold may show "as a pending charge", by bank (`gaps-FILL.md#playtomic-tells-players-a-hold-may-show-as-a-pending-charge-by-bank`).
- **[ABSENT]** How many hours or days a cancellation takes to reach the bank app, and the current ceilings at PKO BP, ING and Santander: not found in their published card terms or help pages (searched each bank's site and terms PDFs for "blokada autoryzacyjna" and "transakcje oczekujące"; also `gaps-FILL.md#not-found-for-the-other-polish-banks`). — read 2026-10-08
- **[DOCS]** Stripe: card statements "from some issuers … don't always distinguish between authorizations and captured (settled) payments, which can sometimes confuse customers"; an uncaptured authorization lasts 7 days for an online customer-initiated payment (Visa merchant-initiated 4 days 18 h); cancelling costs nothing. [Stripe: Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method), [Stripe: Refund and cancel payments](https://docs.stripe.com/refunds) — read 2026-10-08

### On a direct charge the club's descriptor is what the bank receives
- **[DOCS]** "The customer's statement uses the connected account's static component" for direct charges; only the first 22 characters reach the card network. [Stripe: Statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors) — read 2026-10-08
- **[DOCS]** "Most banks display this information consistently, but some might display it incorrectly or not at all." [Stripe: Statement descriptors](https://docs.stripe.com/get-started/account/statement-descriptors) — read 2026-10-08
- **[ABSENT]** Which name a Polish bank app shows on a still-pending hold (the descriptor, the acquirer's name, or "Stripe"): no Polish bank or Stripe page says. — read 2026-10-08

## 9. How a stalled refund or payout is shown (R-PLATFORM-3, R-PLATFORM-20)

### Playtomic: a fixed promise of days, then chat in office hours
- **[POLICY]** In the app a cancelled booking reads "Booking cancelled — Refund issued" and "We've processed your refund … It will be returned to your original payment method within 2-10 business days"; there is no string for a refund that failed or is late. [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download) — read 2026-10-08
- **[POLICY]** Support is a help centre plus live chat in the app, in nine languages (no Polish), Monday to Friday 9:30–17:30 CET in Europe; no reply time is promised. [Playtomic Customer Support](https://playerhelp.playtomic.com/hc/en-gb/articles/19831718711569-Playtomic-Customer-Support) (updated 2026-10-08) — read 2026-10-08
- **[POLICY]** Playtomic's status page lists four components ("Playtomic", "Academy", "PT Manager", "Playtomic.com"), none for payments, refunds or payouts; no notices August–October 2026; email, Slack, RSS and webhook subscriptions. [status.playtomic.com](https://status.playtomic.com/), [history](https://status.playtomic.com/history/1) — read 2026-10-08
- **[POLICY]** A club's failed payout is redone by hand after the club writes to Customer Care (carried from `competitor-club.md#a-payout-that-fails`).
- **[DOCS]** Carried: Stripe emails a full-Dashboard account holder when a payout bounces, up to 5 business days later, and retries at the next interval (`gaps-EMAIL.md#stripe-emails-the-account-holder-when-a-payout-comes-back-up-to-5-business-days-later`); P24's help for a payout that has not arrived only says to check re-verification and the account number (`gaps-EMAIL.md#przelewy24-and-tpay-a-payout-that-does-not-arrive`).

### Playmore: says where each refund went, and names a failed one
- **[POLICY]** A booking's money line reads "Zwrócone", "Zwrócone częściowo", "na portfel Playmore", "zwrot zlecony na kartę lub konto", "zwrot w recepcji", "zwrot przez klub", "rozliczenie po terminie gry", "bez zwrotu — po terminie" or "bez zwrotu — rozliczone z klubem". A split share has the state "Błąd zwrotu": "Rezerwacja została anulowana, ale zwrot Twojej wpłaty się nie powiódł. Napisz do nas przez pomoc w aplikacji." [strings `assets/CccZ1mLc.js`](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** The only reply time promised in the app is for a failed account merge: "odpowiemy w ciągu 12 godzin". Same file — read 2026-10-08
- **[POLICY]** Playmore's status page (UptimeRobot) monitors "Aplikacja Mobilna Playmore", "Panel Recepcji", "Panel Rezerwacji Internetowych" and "Strona internetowa Playmore.pl"; nothing for payments or payouts. [status.playmore.pl](https://status.playmore.pl/) — read 2026-10-08

## 10. Does Stripe itself tell a club about a dispute or a restriction (R-PLATFORM-28)

### Stripe speaks directly to accounts with a Stripe Dashboard
- **[DOCS]** Standard accounts (full Dashboard) suit a platform that prefers "that Stripe handles direct communication with the connected account for account issues (for example, to request more information for identity verification purposes)"; Custom accounts (no Dashboard): "Stripe doesn't contact them directly." Under Standard, fraud and dispute liability sit with the connected account for direct charges. [Stripe: Connected account types](https://docs.stripe.com/connect/accounts) — read 2026-10-08
- **[DOCS]** In Accounts v2, `dashboard: full` gives the club the full Stripe Dashboard; Stripe collects the identity requirements unless the platform takes losses and sets no Dashboard. [Stripe: Configure connected accounts (v2)](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration) — read 2026-10-08
- **[DOCS]** For accounts on a Stripe-built Dashboard, "Stripe will proactively reach out and collect information about your accounts whenever requirements change." [Stripe support: communicating requirement updates](https://support.stripe.com/questions/best-practices-for-connect-platforms-communicating-updates-to-verification-requirements-with-standard-or-express-connected-accounts) — read 2026-10-08
- **[DOCS]** An account's own email notifications include "A payment is disputed by a cardholder"; each team member turns them on or off in Communication preferences; operational emails (account notifications, security alerts) cannot be switched off. [Stripe support: account email notifications](https://support.stripe.com/questions/set-up-account-email-notifications), [Stripe support: opt out of emails](https://support.stripe.com/questions/how-to-opt-out-of-emails-from-stripe) — read 2026-10-08
- **[DOCS]** On a direct charge the dispute is answered from the connected account and its balance is debited; with `fees_collector = stripe` the dispute fee falls on the connected account too. [Stripe: Disputes on Connect platforms](https://docs.stripe.com/connect/disputes) — read 2026-10-08
- **[DOCS]** Carried: "We notify you of a dispute through … Your email address, The Stripe Dashboard, A `charge.dispute.created` event …, A push notification" (`gaps-EMAIL.md#stripe-tells-the-account-holder-by-email-dashboard-event-and-push`); "Stripe will still notify the individual Standard or Express connected accounts directly" about requirements, with a grace period "typically 7 to 30 days" before a capability is degraded (`gaps-EMAIL.md#stripe-writes-to-a-full-dashboard-club-itself-when-requirements-change`).
- **[ABSENT]** Whether the per-user dispute email can be off by default for a new team member: Stripe's pages do not say. — read 2026-10-08
- *Reading:* Rakieta opens each club with `dashboard: full` and both collectors `stripe` (`backend/app/modules/payments/infrastructure/stripe_payments.py:305`), the Standard-like set-up, so the club's owner has Stripe's own channel; Express and no-Dashboard accounts would not.

## 11. A 24-hour cut-off over a clock change, in Kraków clubs' rules (R-PLATFORM-16)

### No Kraków club rule mentions the clock change
- **[POLICY]** The cut-off is written in hours with no word on the clock: Garden Padel "Rezerwację można odwołać bezpłatnie do 24 godzin przed terminem gry"; KSOS "nie później niż na 24 godziny przed ustalonym terminem"; Miazga "w czasie krótszym niż pełne 24 godziny przed grą". Courts are let by clock hour ("liczonej zgodnie z godzinami zegarowymi", Atras; "pełne godziny zegarowe", Miazga). [Garden Padel](https://gardenpadel.pl/regulamin/), [KSOS](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/), [Miazga](https://www.miazgasquash.pl/regulamin/), [Atras](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** Any mention of "zmiana czasu", "czas letni/zimowy", a time zone or official time in the rules of Fame Sport, Garden Padel, KSOS, Atras, Miazga and Squash4You, or in the terms of kluby.org, tenis4U and Playmore (Padel House, SAO and Morelowa 34 publish no rules page that could be fetched). — read 2026-10-08

## 12. How often Kraków booking systems go down, and how clubs are told (R-PLATFORM-22)

### Playmore publishes uptime; tenis4U and kluby.org publish none
- **[POLICY]** Playmore's UptimeRobot data, 11 Jul–8 Oct 2026: the player app, the online booking panel and the website at 100 % every day; the desk panel ("Panel Recepcji") at 98.406 % on 29 July 2026 (about 23 minutes down), otherwise 100 %. [UptimeRobot API for status.playmore.pl](https://stats.uptimerobot.com/api/getMonitorList/tePZAixxDw) — read 2026-10-08 (no screenshot; the figures are the page's own data)
- **[POLICY]** kluby.org's terms, §XI "Przerwy serwisowe": planned and unplanned breaks are announced, with best effort, "za pośrednictwem stosownej informacji lub komunikatu w Aplikacji"; the user accepts "że Usługi dostępne w Aplikacji nie są w 100% niezawodne". [kluby.org Regulamin](https://kluby.org/regulamin) — read 2026-10-08
- **[POLICY]** tenis4U reserves the right to stop "wybranych lub wszystkich usług ze względu na prace konserwacyjne, modyfikacje serwisu lub z powodu braku dostępności usług firm trzecich", with no notice channel named. [tenis4U Regulamin](https://tenis4u.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** A status page for tenis4U, kluby.org or Reservise (status.* subdomains do not resolve; none linked from their sites), and any outage report for tenis4U or kluby.org in search results. — read 2026-10-08
- **[COMPLAINT]** Carried: "W wyniku awarii systemu reservise straciłem wszystkie rezerwacje w klubie" (`complaints.md#booking-software-that-breaks-the-desks-day`); kluby.org users a week without login (`situations.md` SIT-38).
