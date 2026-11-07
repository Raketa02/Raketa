# Gaps round — FILL (the moment a game fills)

Answers to the facts the FILL Moderator found missing (`$W/areas/FILL/gaps.md`), one `###` per fact.
Read 2026-10-08. Kinds as in the other topic files; *reading* is arithmetic or comparison, not a
source. A claim about Raketa's own code carries `path:line` in the repo (read in the story copy at
commit `3e65f213`). Nothing here was measured on a device: the phones and the local stack hold the
walker's seeded store and were left alone.

---

## 1. The order control

Rules: R-FILL-1, R-FILL-7, R-FILL-11, R-FILL-26.

### No authority on a swipe or a priced "I'm in" as the order control

- **[ABSENT]** No UOKiK decision or statement, Polish court ruling, CJEU ruling or German ruling on
  a swipe (gesture, slider) or on a button reading "I'm in · 40 zł" as the control that binds a
  consumer to pay. Searched: UOKiK's Q&A and press archive, prawo.pl, legeartis.org,
  poradnikprzedsiebiorcy.pl; German § 312j BGB commentary (it-recht-kanzlei.de, haendlerbund.de,
  otto-schmidt.de, cms.law) with "Wischgeste", "Swipe", "Slider" — read 2026-10-08.
- **[LAW]** The statute itself covers more than a button: "Jeżeli w celu złożenia zamówienia wymagane
  jest aktywowanie przycisku **lub podobnej funkcji**, przycisk lub podobna funkcja muszą być
  oznaczone w łatwo czytelny sposób słowami «zamówienie z obowiązkiem zapłaty» lub innym
  równoważnym jednoznacznym sformułowaniem" (art. 17 ust. 3); otherwise "umowa nie zostaje
  zawarta" (ust. 4). [Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf),
  [arslege.pl art. 17](https://arslege.pl/ustawa-o-prawach-konsumenta/k1270/a79296/) — read 2026-10-08
  - *Reading:* "or a similar function" means a gesture that places the order is inside the rule;
    what is open is only whether a price on the control ("40 zł") is an "equivalent unambiguous
    wording". UOKiK's accepted examples all name payment ("kup teraz", "zapłać teraz") —
    `local-market.md#the-order-button-and-a-yes-that-charges-later`.
- **[LAW]** UOKiK charged Glovo (16 May 2023) partly because its final button read "Potwierdź
  zamówienie" without "zamówienie z obowiązkiem zapłaty", and said the order button "nie powinien
  być aktywny, zanim konsumentowi nie zostaną przedstawione wszystkie koszty". These are charges,
  not a decision; no outcome found. [UOKiK: Glovo z zarzutami](https://archiwum.uokik.gov.pl/aktualnosci.php?news_id=19572),
  [bankier.pl](https://www.bankier.pl/wiadomosc/Glovo-z-zarzutami-UOKiK-za-wprowadzanie-konsumentow-w-blad-8541044.html) — read 2026-10-08
- **[ABSENT]** A lawyer's opinion on this exact control — none public; still needs one.

---

## 2. Undo before money moves

Rules: R-FILL-1 to R-FILL-4.

### Gmail holds a sent message for 5 to 30 seconds behind Undo

- **[DOCS]** "If you decide you don't want to send an email, you have a short time after to cancel
  it… select a Send cancellation period of 5, 10, 20, or 30 seconds." The message leaves only when
  the period ends — the same delayed-send pattern as Raketa's ten seconds, but no money is involved.
  [Google: Unsend Gmail messages](https://support.google.com/mail/answer/2819488?hl=en) — read 2026-10-08

### Uber lets a rider cancel free for two minutes after a driver accepts

- **[POLICY]** UberX and Share are charged a cancellation fee only when the rider cancels "more than
  2 minutes" after a driver accepts; Black and Black SUV after 5 minutes; the fee varies by city.
  The nearest money app to a grace window: the request binds at once, and backing out costs nothing
  for a short time. [Uber help: Review cancellation fee](https://help.uber.com/h/6bec690f-ee35-40ba-96ee-c38a8ae796e0),
  [Uber help: Am I charged for canceling?](https://help.uber.com/h/24e75a3b-cf44-44e4-abae-8c2dce3b07a3) — read 2026-10-08

### No payment app found that waits behind an Undo before charging

- **[ABSENT]** No app, sport or not, that counts down and charges only when the count ends. Food
  delivery (Wolt, Glovo, DoorDash) lets an order be cancelled until the venue accepts it, but its
  help pages could not be read (403) and the only claim of a "ten-second cancel button" at Wolt is
  an unofficial site ([infocontact.ro](https://www.infocontact.ro/anulare-comanda-wolt/)); Amazon's
  "30 minutes for 1-Click" appears only on third-party sites. Searched: Google, Uber, Wolt, DoorDash,
  Amazon help — read 2026-10-08.
  - *Reading:* the market's grace windows run **after** the binding act (Playtomic's free hour,
    Uber's two minutes); Raketa's runs **before** it. That is what makes Undo leave nothing to
    refund (R-FILL-2).

---

## 3. Kept offline, sent later

Rules: R-FILL-5, R-FILL-6, R-FILL-8.

### Stripe Terminal stores card payments offline and forwards them later, at the seller's risk

- **[DOCS]** "When operating offline, payment information is collected at the time of sale, and
  authorization is only attempted after connectivity is restored and the payment is forwarded. You,
  as the user, assume all decline and tamper-related risks… If… the issuer declines the transaction,
  there's no way to recover the funds." Stored payments survive a reboot; clearing the app's storage
  loses them; a payment confirmed offline "can't [be] cancel[led] or refund[ed]… until it's
  forwarded". It is a seller's in-person till with the card present, never a consumer's phone.
  [Stripe: Collect card payments while offline](https://docs.stripe.com/terminal/features/operate-offline/collect-card-payments.md?terminal-card-present-integration=terminal&reader-type=bluetooth&terminal-sdk-platform=react-native),
  [overview](https://docs.stripe.com/terminal/features/operate-offline/overview) — read 2026-10-08
  - *Reading:* the one store-and-forward payment design found puts the risk on the party that chose
    it and lets it cap the amount (`REQUIRE_ONLINE` above a sum). Raketa's offline free vote (R-FILL-8)
    is the reverse: the person who typed it carries the charge, and so do three others.

### WhatsApp queues a message typed offline and sends it on reconnect

- **[DOCS]** A clock on a WhatsApp message means it is still on the phone and has not left; it goes
  when the connection returns. This is how an "I'm in" typed underground reaches the group today —
  but it costs nobody anything until the organiser asks for a BLIK. Official FAQ not readable (only
  its title loaded); third-party explainers: [gulfnews.com](https://gulfnews.com/lifestyle/whatsapp-messages-not-sending-but-your-internet-works-heres-what-to-check-1.500683472),
  [itgeared.com](https://www.itgeared.com/what-does-a-square-clock-mean-on-whatsapp) — read 2026-10-08

### No consumer booking or payment app keeps a join made offline

- **[ABSENT]** No player or consumer app found that stores a join or a payment made offline and sends
  it later; Playtomic, Playmore and MATCHi pay in a checkout in front of the player
  (`areas/FILL.md` §1). Searched: Stripe, Square, WhatsApp, the racket apps' help — read 2026-10-08.

---

## 4. The countdown in the background

Rules: R-FILL-6.

### Raketa's countdown is a JavaScript timer in the phone's memory

- **[DOCS]** The count is a `setTimeout` chain that sends the yes when `endsAt - Date.now()` reaches
  zero (`frontend_player/src/features/proposals/components/FillProvider.tsx:223-239`); nothing
  persists it and nothing asks the OS for background time (no `beginBackgroundTask`, no background
  task library in `frontend_player/package.json`; background location off,
  `frontend_player/app.config.ts:97-98`). React Native 0.76.9 with the new architecture
  (`frontend_player/package.json:52`, `app.config.ts:70`) — read 2026-10-08

### On Android, React Native stops firing timers while the app is in the background

- **[DOCS]** React Native 0.76.9's `JavaTimerManager`: `onHostPause()` sets `isPaused` and removes
  the timers' frame callback; the callback returns at once `if (isPaused.get() && !isRunningTasks.get())`;
  `onHostResume()` re-posts it. Timers run in the background only while a headless JS task runs.
  [JavaTimerManager.kt @ v0.76.9, lines 71-86, 135-142, 276-278](https://github.com/facebook/react-native/blob/v0.76.9/packages/react-native/ReactAndroid/src/main/java/com/facebook/react/modules/core/JavaTimerManager.kt) — read 2026-10-08
  - *Reading:* on the Galaxy A55, a yes whose ten seconds run out after the player switches app is
    sent the moment Raketa comes back to the front — possibly minutes later — or never, if the
    system kills it first (Samsung's sleeping apps, `situations.md` SIT-95).

### On iOS, timers keep running briefly, then the app is suspended

- **[DOCS]** React Native 0.76.9's `RCTTiming.mm`: on `UIApplicationDidEnterBackgroundNotification`
  it stops the display link and schedules an `NSTimer` for the next timer
  (`appDidMoveToBackground`, `scheduleSleepTimer`), so timers fire while the process still runs.
  [RCTTiming.mm @ v0.76.9, lines 180-189, 300-339](https://github.com/facebook/react-native/blob/v0.76.9/packages/react-native/React/CoreModules/RCTTiming.mm) — read 2026-10-08
- **[DOCS]** Apple: when an app moves to the background its delegate method "has five seconds to
  perform any tasks and return. Shortly after that method returns, the system puts your app into
  the suspended state", unless it asks for more time with `beginBackgroundTask`.
  [Apple: Extending your app's background execution time](https://developer.apple.com/documentation/uikit/extending-your-app-s-background-execution-time) — read 2026-10-08
  - *Reading:* on the iPhone, a count with more than about five seconds left when the player leaves
    is sent when Raketa next comes to the front; a count with less may still go out in the background.
- **[ABSENT]** Not seen on either device: the phones belong to the walk. A walker can check it by
  saying Book it now, pressing Home within two seconds, waiting a minute, and watching the console's
  Sent pane and the booking time.

---

## 5. The saved-card agreement

Rules: R-FILL-11.

### What Stripe says the saved-card terms must name

- **[DOCS]** "To charge customers when they're offline, include the following in your terms: the
  customer's agreement to your initiating a payment or a series of payments on their behalf for
  specified transactions; the anticipated timing and frequency of payments…; how you determine the
  payment amount; your cancellation policy…" and "Keep a record of each customer's agreement to
  your terms." [Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-08

### Raketa's terms, accepted once in the payment setup, name all four

- **[DOCS]** The terms the player accepts with *Accept and continue* (version `2026-09-29`, recorded
  by version): "When a game you said yes to fills, **the club it is played at** charges your share at
  once — the court's price divided by the players. Free to leave until the club's cut-off — refunded
  minus the card fee; after it, refunded when someone takes your seat. A game still missing a player
  at the cut-off is called off, and everyone gets everything back."
  (`frontend_player/src/features/payments/components/paymentsCopy.ts:52-70`). The card step adds
  "One-time 3-D Secure check — it lets the club charge your share later without you present."
  (`paymentsCopy.ts:129-130`); the sheet over the deck reads "Save how you pay. The club charges
  your share only when a game you said yes to fills." (`paymentsCopy.ts:167-171`) — read 2026-10-08
  - *Reading:* transactions (a share of a game you said yes to), timing (at once, when it fills),
    amount (the court's price divided by the players) and the cancellation policy (the cut-off and
    its refunds) are all there. What it does not name is the frequency: nothing says how many games
    a week may be charged — the player's games-per-week setting is elsewhere.

### Playtomic asks a separate consent before it may charge a saved card later

- **[POLICY]** Card on File for split private bookings: before the first split booking the owner must
  "Review the information about registering your card; Accept the consent for automatic charges;
  Complete your payment". It may then be charged only if a share is still unpaid 2 h after the match.
  [Playtomic help: Card on File (CoF) in split payments](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457-Card-on-File-CoF-in-split-payments-what-it-is-and-how-it-works) (updated 2026-09-15) — read 2026-10-08

---

## 6. Released holds on Polish cards

Rules: R-FILL-15, R-FILL-36, R-FILL-44, R-FILL-49.

### mBank lifts a hold when the merchant's cancellation arrives, at most 14 days online

- **[POLICY]** mBank, cards FAQ: "Kiedy dostaniemy potwierdzenie, że sprzedawca anulował płatność,
  zdejmiemy blokadę"; "Jeśli sprzedawca nie prześle anulowania lub rozliczenia zakupu w tym czasie,
  blokada wygaśnie po 14 dniach" (internet purchases; 7 days with the card present). Elsewhere:
  "Blokadę autoryzacyjną utrzymujemy maksymalnie do 30 dni" for any unsettled transaction.
  [mBank: Karty debetowe — pytania i odpowiedzi](https://www.mbank.pl/indywidualny/karty/pytania-i-odpowiedzi/karty-debetowe/) — read 2026-10-08
  - *Reading:* a hold Raketa cancels (an authorisation reversal sent at once) should leave an mBank
    customer's app when the reversal arrives; a hold left to lapse can show for up to 14 days at
    mBank — longer than the 4 days 18 hours to 7 days after which the network itself releases it.

### Stripe: cancelling releases the hold; a quick refund becomes a reversal

- **[DOCS]** "If you need to cancel an authorization, you can cancel the PaymentIntent"; if a hold
  expires uncaptured "the funds are released and the payment status changes to canceled". Refunds
  "issued shortly after the original charge" go as a reversal: "the original charge drops off the
  customer's statement". No issuer timing is promised.
  [Stripe: Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method),
  [Stripe: Refunds — refund and reversal](https://docs.stripe.com/refunds) — read 2026-10-08

### Playtomic tells players a hold may show as a pending charge, by bank

- **[POLICY]** "depending on your bank, you will see this pre-authorization reflected as a pending
  charge"; a booking cancelled in time is refunded "instantaneously to your original payment method".
  [Playtomic help: What does a "temporary hold" on my payment method mean?](https://playerhelp.playtomic.com/hc/en-gb/articles/19831499991441) (updated 2026-09-04) — read 2026-10-08

### Not found for the other Polish banks

- **[ABSENT]** PKO BP (only the prepaid card's 7 days), ING, Pekao, Santander and Millennium publish
  no time for a cancelled authorisation to leave their app. An ING community reply of "11 calendar
  days" could not be opened (403). Searched: bank help pages and regulations, bankier.pl,
  kontomaniak.pl — read 2026-10-08.

---

## 7. A club that lost card payments

Rules: R-FILL-16.

### Stripe refuses the charge request itself, not each card

- **[DOCS]** "The `charges_enabled` and `payouts_enabled` attributes on an Account object indicate
  whether it can create charges"; if `card_payments` or `transfers` is inactive, "both capabilities
  are disabled". [Stripe: Handle verification](https://docs.stripe.com/connect/handling-api-verification),
  [Stripe: Account capabilities](https://docs.stripe.com/connect/account-capabilities) — read 2026-10-08
- **[DOCS]** Platforms whose seller account cannot charge report Stripe's answer at checkout as an
  error on the request, "This account cannot make live charges", appearing "for one of two
  reasons… test mode… [or] under review due to risk factors or business verification" — not a card
  decline. Third-party help, not Stripe's own: [Recharge help](https://support.getrecharge.com/hc/en-us/articles/11716506299799-Stripe-Error-This-account-cannot-make-live-charges) (updated 2026-07-13) — read 2026-10-08
- **[ABSENT]** Stripe's own documentation of the error type and code for a PaymentIntent created on
  an account without active card payments — searched the error-codes page (`account_invalid`,
  `capability_not_active` are listed, neither for this case) — read 2026-10-08.
  - *Reading:* if it comes back as an invalid request, Raketa's adapter treats it as its own bug and
    raises it, rather than calling it an outage or a decline
    (`backend/app/modules/payments/infrastructure/stripe_payments.py:18-22, 73-79`). A test-mode check
    on a restricted test account would settle it.

---

## 8. Blocking hours from outside

Rules: R-FILL-19.

### kluby.org's integrations list has no calendar feed, import or API

- **[POLICY]** kluby.org integrates with: remote control (lights, heating, gate, door PIN), online
  payments (2 %), mass SMS in the club's name, online invoices and e-receipts; the request form also
  names "Systemy zarządzania, System rezerwacji, Challenge / Liga / Turnieje". No API, iCal feed or
  import of blocks is offered. [kluby.org: Integracje](https://oferta.kluby.org/integracje) — read 2026-10-08

### Reservise is being retired into Playmore

- **[POLICY]** "Reservise is bowing out after 10 years… We're moving you to Playmore… We move your
  bookings, customer base, pricing and full history"; no date given; no API or calendar import
  mentioned. [Playmore: Reservise](https://join.playmore.pl/en/reservise) — read 2026-10-08

### tenis4U's club calendar has no published import or API

- **[ABSENT]** tenis4U's site describes a day/week calendar per court with "Błyskawiczne dodawanie i
  usuwanie rezerwacji", standing slots and league bookings, and nothing on API, iCal or import; its
  App Store listing (4.9.2) neither. [tenis4U](https://tenis4u.pl/), [App Store](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113) — read 2026-10-08
  - *Reading:* in all three, a Raketa booking reaches the club's own calendar only by a person typing
    it, as a phone booking does today.

---

## 9. The drawn sides

Rules: R-FILL-20.

### Raketa: the sides drawn at the fill are the sides the result is entered for

- **[DOCS]** "The line-up is frozen until somebody leaves it": the fill draws the sides, and only a
  departure or a rescue moves a seat (`backend/app/modules/games/domain/lineup.py:1-25`,
  `backend/app/modules/games/domain/game.py:15-21`). A result is one score, A against B, entered
  by a player whose side is looked up from that line-up (`game.py:334-360`, `_side_of` at `:854`);
  there is no act to swap two players. So the drawn sides bind for the result and the rating.

### Playtomic lets players swap positions after the match, before the result

- **[POLICY]** "If the players in your open match are in the wrong order, you can switch their
  positions after the match has been played, but only before entering the results… Any player can
  change positions after the match ends… This allows you to accurately reflect how the teams
  actually played, even if it differs from the original match setup."
  [Playtomic help: How to Change Player Positions in an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/43819065293457-How-to-Change-Player-Positions-in-an-Open-Match) (updated 2026-07-13) — read 2026-10-08
- **[POLICY]** "Do I need to have a team to sign up for an open match? No… You join the match alone
  and are matched with opponents of similar levels." [Playtomic help: How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match) (updated 2026-10-03) — read 2026-10-08
  - *Reading:* the market leader expects players to rearrange sides on court and lets the result
    follow what was played; Playmore assigns sides only at result entry
    (`platforms.md#a-balance-figure-or-suggested-sides`). Raketa's drawn sides are stricter than both.

### Social formats rotate partners

- **[POLICY]** Americano: players sign up alone and get "a different partner and different opponents"
  each round, pairs drawn by the system or organiser.
  [Decathlon PL: Padel americano i mexicano](https://www.decathlon.pl/c/disc/padel-americano-i-mexicano-czym-sie-roznia_6b16ce06-97a6-418b-a1be-b200fe51799e) — read 2026-10-08

### Not found: whether Kraków players expect to pick their partner

- **[ABSENT]** No Kraków forum, group post or survey on who picks partners in a casual four — Facebook
  groups need a login (`local-market.md#gaps-left-open`); searched Polish phrases "zmiana par",
  "rotacja par", Reddit r/padel — read 2026-10-08.

---

## 10. A club messaging its players

Rules: R-FILL-21.

### tenis4U pushes tournament and league news by distance, nothing about a booking

- **[POLICY]** "O każdym turnieju czy lidze powiadomisz graczy za pomocą powiadomień, wybierasz
  odległość w promieniu której tenisiści mają dowiedzieć się o planowanych rozgrywkach."
  [tenis4U](https://tenis4u.pl/) — read 2026-10-08
- **[ABSENT]** A way for a tenis4U club to write to the players of one booking (moved court, broken
  light): not on the site or in the App Store text (which lists "Messaging and Chat" only as an
  age-rating item). A September review: "O powiadomieniach gdy kort się zwolni też można zapomnieć."
  [App Store](https://apps.apple.com/pl/app/tenis4u-korty-i-turnieje/id1222721113) — read 2026-10-08
- **[POLICY]** For comparison, a Miazga Squash (Reservise) booking or cancellation is confirmed by
  "wiadomość SMS wysłana z systemu". [Miazga regulamin §3c, §4c](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08

---

## 11. The fourth joiner

Rules: R-FILL-27.

### Not found: a distinct "match complete" screen or push at Playtomic

- **[ABSENT]** Playtomic's player help has no article on what the fourth joiner sees; its notification
  list has only "Confirmation of new booking, match or activity joined" and the receipt, the same for
  every joiner (`competitor-joiner.md#on-joining-a-confirmation-email-and-the-clubs-message`).
  Searched the help centre for "match complete", "match full", "court booked match", its App Store text, Reddit and YouTube — read 2026-10-08.
- **[POLICY]** What a full match changes for her: "Match is full? You can cancel up to 24 hours before
  the start time", and with four players the "Court [is] always reserved".
  [Playtomic help: Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465) (updated 2026-09-30) — read 2026-10-08

---

## 12. The club's own receipt

Rules: R-FILL-30.

### Stripe sends a direct charge's receipt only with the club's setting on and an address

- **[DOCS]** "Direct charges: Receipts use the connected account's Customer emails, Branding, and
  Public details settings"; automatic receipts need **Successful payments** switched on, "only sent
  if the payment succeeds"; a platform may send one by passing `receipt_email`. Accounts with the
  Stripe Dashboard set this themselves. [Stripe: Receipts](https://docs.stripe.com/receipts) — read 2026-10-08

### Raketa gives the club's Stripe no address to send to

- **[DOCS]** The club's account is opened with its own full Stripe Dashboard (`"dashboard": "full"`,
  `backend/app/modules/payments/infrastructure/stripe_payments.py:301-331`); the player's Stripe
  customer carries no name or email ("Stripe needs no name or email… Raketa sends none",
  `:176-184`); the charge passes no `receipt_email` (`:512-544`) — read 2026-10-08
  - *Reading:* even if the club switches Successful payments on in its own Dashboard, Stripe has no
    address, so the player gets only Raketa's email; the club can still send one by hand from its
    Dashboard by typing an address, in Stripe's words and with the club's branding.

---

## 13. Desk hours

Rules: R-FILL-31.

### Desks take phone bookings during opening hours; online bookings confirm at once

- **[POLICY]** Garden Padel: open "Poniedziałek – Niedziela 7:00 – 23:00"; bookings online
  (tenis4U), "telefonicznie w godzinach pracy recepcji" or at the desk; "Rezerwacja jest ważna po
  dokonaniu płatności"; complaints "rozpatrywane w terminie 14 dni".
  [Garden Padel](https://gardenpadel.pl/), [regulamin §4, §8](https://gardenpadel.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Atras Squash Club: "czynny od poniedziałku do piątku w godz. od 7.00 do 24.00 oraz w
  soboty, niedziele i święta od 8.00 do 22.00"; complaints by email, 14 days.
  [Atras regulamin](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Miazga Squash: every booking by phone, internet or desk is confirmed by an SMS "wysłana
  z systemu". [Miazga regulamin §3c](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** Any Kraków club's stated time to answer a booking request: none publishes one, because
  none takes requests to confirm later — a slot is booked on the spot. Searched the sites and
  regulations of Garden Padel, Fame Sport, Atras, Squash4You, Miazga — read 2026-10-08.
  - *Reading:* a desk is staffed roughly 07:00–23:00/24:00; an On request booking made at night
    waits at least until the desk opens.

---

## 14. When another share fails

Rules: R-FILL-35.

### Playtomic shows every player's payment as pending or paid

- **[POLICY]** Split private booking: "In the 'View' section of the match, you can check the status of
  all players payments (pending or paid)." A share still unpaid 2 h after the match falls on the
  owner — by hold, saved card or a debt. [Playtomic help: How to split the payment of a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation) (updated 2026-07-20) — read 2026-10-08
- **[POLICY]** When the owner's saved card fails ("expired card, insufficient funds, or declined
  authentication") Playtomic tries his other saved cards, then makes a debt that blocks new bookings.
  [Playtomic help: Card on File](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457-Card-on-File-CoF-in-split-payments-what-it-is-and-how-it-works) (updated 2026-09-15) — read 2026-10-08

### Uber: the requester pays when a co-rider's split fails

- **[POLICY]** "If a rider chooses not to accept Split Fare or doesn't have a valid payment method,
  the person who requested the trip will be charged the full amount."
  [Uber: Split Fare](https://www.uber.com/gb/en/ride/how-it-works/split-fare) — read 2026-10-08
  - *Reading:* both name an outcome for the others (a status, a charge to the requester); neither has
    a fill that silently fails for everyone.

---

## 15. Off-session declines

Rules: R-FILL-36, R-FILL-37, R-FILL-42, R-FILL-45.

### No figure for how often Polish or EEA issuers soft-decline a charge without the player

- **[ABSENT]** No published rate of `authentication_required` or other soft declines on
  merchant-initiated charges, for Poland or the EEA. Searched: EBA SCA readiness report, EBA/ECB fraud
  report, Stripe, Checkout.com, Cybersource, The Paypers — read 2026-10-08. Nearest: Checkout.com puts
  soft declines at "80% to 90% of all declines" (vendor, all transaction types)
  [Checkout.com](https://www.checkout.com/blog/post/when-should-merchants-prepare-for-soft-declines);
  The Paypers reports UK issuers declining about 3 % of non-3-D-Secure payments in Nov 2021
  [The Paypers](https://thepaypers.com/payments/interviews/strong-customer-authentication-where-are-we-now-3) — read 2026-10-08

### A clone is consumed by the charge it makes

- **[DOCS]** "Creating a charge with the cloned PaymentMethod consumes it, because it's not attached to
  a customer… You can't reuse the consumed clone, but you can clone the platform PaymentMethod again."
  [Stripe: Direct charges on multiple accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts) — read 2026-10-08
- **[ABSENT]** Whether a clone whose off-session attempt was declined or asked for 3-D Secure counts
  as "consumed" when the player confirms the **same** PaymentIntent in the app — no Stripe page, issue
  or answer found; a Stripe test-mode check is still needed (Raketa's own demand suite skips it:
  `backend/tests/demands/test_payments_demands.py:121-124`) — read 2026-10-08.
  - *Reading:* Raketa confirms the same payment with the same clone
    (`stripe_payments.py:545-566` returns the refused payment's `client_secret`); if Stripe treats the
    clone as used, that confirmation fails and only a new payment with a fresh clone works.

### The hold window follows how the card network classifies the attempt that succeeded

- **[DOCS]** Visa: merchant-initiated 4 days 18 hours, customer-initiated 7 days; Mastercard 7 and 7.
  "Stripe and the card network classify transactions as MIT or CIT based on signals of cardholder
  participation, not solely on API parameters like `off_session`"; the charge's
  `payment_method_details.card.capture_before` "indicates when the authorization expires".
  [Stripe: Place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-08
  - *Reading:* an off-session attempt that fails holds nothing; the authorisation that holds is the
    one the player completes in the app with the bank's check, which carries cardholder
    participation, so on a Visa it should get the 7-day window. Only `capture_before` on a test
    payment proves it — not read (no test keys, `state.json` waiting #533).
