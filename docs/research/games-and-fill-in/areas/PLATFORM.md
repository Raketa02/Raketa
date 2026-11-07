# PLATFORM — market digest

Digest of R-PLATFORM-1 to 58 (PRD #530), 2026-10-08, from this folder's topics and situations; kind, link and read date sit in the topic line cited; index `README.md`.
Cites: CO/CJ/CN/CC = `topics/competitor-organiser|joiner|newcomer|club.md`, PF = `topics/platforms.md`, LM = `topics/local-market.md`, CP = `topics/complaints.md`, SIT = `situations.md`; the part after # is the heading anchor.
Most PLATFORM rules are engineering guarantees; the market shows up as what goes wrong when they fail. Competitor: Playtomic `CC#manager-is-a-web-app-and-the-clubs-only-calendar`. Status quo: the club's own booking system beside phone and desk `LM#which-booking-systems-kraków-clubs-run`.

## 1. An act and what it causes, delivered once and in order (R-PLATFORM-1 to 4, 6, 14, 55 to 57)

- **Playtomic:** a match paid but missing is explained as "the bank… temporarily withholds the amount, wait a few days" `CJ#3-d-secure-and-failed-payments`
- **Playtomic (club):** payments show as Processed, Pending or "Voided"; reports update hourly and past figures "can change" `CC#what-the-club-sees-of-its-money`
- **Stripe:** a refund soon after the charge is a reversal and the charge drops off the statement; a card refund otherwise takes about 5–10 business days `LM#how-fast-a-refund-arrives-by-method`
- **Playtomic:** a card refund is "processed immediately" but "can take 2-15 business days" to show; refunds are listed under *Your payments* `CN#how-long-a-refund-takes`
- **Complaints (joiner):** "charged THREE TIMES"; "Reservation placement was failed but still it cost me 47 euros"; "It took the money but then said there was an issue and didn't book me on… it took the money twice" `CP#charged-twice-or-charged-when-the-booking-failed`
- **Complaints (joiner):** Playmore "straciłem 100 zł za duplikat rezerwacji"; a BLIK payment "ciągle oczekująca bez możliwości opłacania ponownie" `CP#charged-twice-or-charged-when-the-booking-failed`
- **Complaints (joiner):** the app shows the refund, "Tot heden niks ontvangen"; Playmore "Dostaję komunikat, że zarezerwowane, a wcale nie jest" `CP#refunds-are-slow-partial-or-never-arrive` `CP#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`
- **Complaints (organiser):** a desk payment not recorded in time, so the organiser is billed again; "charged me twice, once through the app and once on site" `CP#a-share-paid-at-the-desk-is-not-recorded-and-the-organiser-is-billed-again`

## 2. Holds let go, refused shares resolved (R-PLATFORM-5, 7, 10)

- **Stripe:** cancelling an uncaptured payment costs nothing; an uncancelled hold lapses after 4 days 18 h to 7 days `LM#how-long-a-hold-lasts`
- **Playtomic:** an owner's split-booking hold ends "two hours after the end of the match" once all have paid `CN#holds-on-a-split-private-booking`
- **Playtomic (club):** with Card on File "if it fails, the booking may remain partially unpaid… The club is responsible for following up" `CC#nbm-the-club-sells-and-is-paid-weekly-by-payment-date-before-the-game`
- **Complaints:** "that hold can stay on your account for up to a week"; Playmore "Pieniądze na koncie zablokowane, ale płatność nieudana" `CP#the-organisers-card-carries-everyones-share-until-the-others-pay` `CP#charged-twice-or-charged-when-the-booking-failed`
- **Situation:** a hold runs out before capture (SIT-63) `SIT#paying`

## 3. Two presses at once: the last yes, the court, the last seat (R-PLATFORM-8, 9, 11 to 13, 58)

- **Playtomic (club):** desk and app sell from one calendar, "so desk and app cannot double-sell"; linked shared courts block each other `CC#manager-is-a-web-app-and-the-clubs-only-calendar`
- **Playtomic:** a spot request reserves nothing, "another player could take yours before you finish booking" `CJ#requesting-a-spot-needs-every-players-yes-and-holds-no-seat`
- **Other platforms:** Playmore refuses a taken hour ("Ktoś właśnie zajął ten termin. Wybierz inny slot."); its reserve list is "kto pierwszy, ten gra" `PF#playmore--the-court-is-held-from-publication` `PF#playmore--waiting-lists-and-alerts`
- **Playtomic:** "private reservations always take priority over open matches that aren't full", so a filling match loses its court to a full booking `CO#the-court-is-held-in-stages`
- **Status quo (club):** no system writes bookings into another, so an hour sold elsewhere is not seen [ABSENT] `PF#no-system-writes-bookings-into-another`
- **Complaints (organiser):** "somebody else jumped on and booked one of the available spaces" `CP#a-held-court-is-taken-by-strangers-or-bumped-by-a-full-booking`
- **Complaints (joiner):** "another group of 4 turned up… the court was doubled booked"; a club "ha sovrapposto due prenotazioni" `CP#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`
- **Complaints (club):** "W wyniku awarii systemu reservise straciłem wszystkie rezerwacje w klubie" `CP#booking-software-that-breaks-the-desks-day`

## 4. One clock, Warsaw's (R-PLATFORM-15, 16)

- **Playtomic:** a private booking's checkout prints the deadline as a date and time ("Before Friday 13 February | 11:30") `CO#cancelling-a-private-booking`
- **Other platforms:** Playmore's card counts down "Komplet do {time} · Zostało {h} godz. {m} min", refreshed every 30 s `PF#playmore--the-open-game-card-and-preview`
- **Situations:** on Sun 25 Oct 2026, 24 h before 10:00 is 11:00 the day before (SIT-22); Poland has no clock-change dates for 2027 yet (SIT-23); Easter 2027 falls on the spring change (SIT-24) `SIT#time-and-the-calendar`

## 5. Timed jobs: book-by, time to confirm, cut-off, catching up (R-PLATFORM-17 to 23)

- **Playtomic:** a short match is cancelled about 1 h before start and refunded automatically, "Cancelled by Anemone" `CJ#a-match-still-short-about-an-hour-before-start-is-cancelled-by-anemone`
- **Playtomic:** a converted private match that never fills refunds its joiners "2 hours after the scheduled match time" `CJ#joining-a-private-booking-turned-public`
- **Other platforms:** Playmore confirms a full game only at its cut-off ("Skład pełny · potwierdzimy o {time}"); an unpaid booking is cancelled after 30 minutes `PF#playmore--the-court-is-held-from-publication` `PF#playmore--an-unpaid-booking-lapses-after-30-minutes`
- **Other platforms:** MATCHi captures 12 h after the start or 7 days after booking, whichever is first `PF#matchi--the-card-is-held-at-booking-and-captured-later`
- **Status quo:** Playmore *Gry otwarte* calls a short game off before the start with "pełny zwrot dla wszystkich"; the club sets when (1–48 h) `LM#clubs-own-open-games-playmore-gry-otwarte`
- **Complaints (joiner):** "When someone cancels a session the refunds are never issued and the chatbot crashes" `CJ#refunds-that-never-arrive`
- **Situation:** a booking system down for a week after an update (SIT-38) `SIT#the-club-cancels-closes-or-changes`

## 6. A club paid once per closed day (R-PLATFORM-22, 24)

- **Playtomic (club):** paid weekly by Stripe every Monday for everything paid in the 7 days, even for games later; refunds can make a payout negative `CC#nbm-the-club-sells-and-is-paid-weekly-by-payment-date-before-the-game`
- **Playtomic (club):** other models pay twice a month, matches "after the match has been played"; a failed payout is redone by hand `CC#distribution-model-and-obm-paid-twice-a-month` `CC#a-payout-that-fails`
- **Other platforms:** MATCHi pays monthly by the game's date; uncaptured payments roll to the next month `PF#matchi--the-club-is-paid-monthly-by-the-games-date`
- **Stripe:** first payout after 7 days, then 3 business days; minimum 5 zł; delaying a club's payouts needs loss liability or platform controls that `losses_collector=stripe` does not give; "Stripe doesn't provide escrow services" `LM#payouts-in-poland`
- **Stripe:** a refund is taken from the club's available balance; if it is short a card refund waits and can fail, a BLIK or P24 refund fails at once `LM#refunds-come-out-of-the-clubs-balance`
- **Situations:** weekend and holiday payouts land the next business day (SIT-29); a refund after the club was paid becomes a negative payout (SIT-101) `SIT#time-and-the-calendar` `SIT#the-payment-provider-and-the-platform`
- **Complaints:** a refund refused because "Playtomic da Geld schon ausgezahlt hat" `CP#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`

## 7. The provider's notices (R-PLATFORM-26 to 28)

- **Stripe:** events may arrive more than once and out of order, retried for up to three days (SIT-99); a saved BLIK's result arrives only by webhook `SIT#the-payment-provider-and-the-platform` `LM#blik-at-stripe`
- **Stripe:** a dispute takes 90 zł and the amount from the club's balance, opens up to 120 days after the event, and runs 2–3 months `LM#disputes-cost-90-zł-and-land-on-the-club`
- **Playtomic:** a chargeback "may be recorded as an outstanding debt"; the club sees it only in reconciliation `CJ#a-chargeback-becomes-a-debt` `CC#chargebacks-what-the-club-is-told`

## 8. Emails and pushes (R-PLATFORM-29 to 31)

- **Playtomic:** emails cannot be switched off; a manager's chat message pushes every player `CJ#on-joining-a-confirmation-email-and-the-clubs-message` `CC#talking-to-players-and-what-the-club-sees-of-them`
- **Situations:** APNs keeps only the last push while a phone is offline (SIT-97); Samsung's battery saver delays pushes (SIT-95); Android 13 blocks all after "don't allow" (SIT-94); Gmail rejects mail without SPF/DKIM (SIT-98) `SIT#phones-pushes-and-email`
- **Complaints:** a push repeated "gleichzeitig als Mail"; Playmore's freed-court alert "nigdy nie przychodzi" `CP#notifications-missing-duplicated-or-impossible-to-tune` `CP#no-waiting-list-or-queue-for-a-full-game`

## 9. On the phone: errors, offline, Undo, freshness, sign-in (R-PLATFORM-44 to 51, 54)

- **Other platforms:** Playmore names a decline in plain words ("Bank odrzucił płatność — brak środków / limit karty / karta nieważna") `PF#playmore--an-unpaid-booking-lapses-after-30-minutes`
- **Playtomic:** a player-made private booking has a 1-hour grace period before its cancellation fee; converting to public "cannot" be undone `CO#cancelling-a-private-booking` `CO#converting-a-private-booking-into-a-public-match`
- **Complaints (organiser):** "share it by accident. Says you're unable to cancel even when no one has joined"; booked today by mistake, the default date `CP#shared-or-booked-private-by-mistake-and-it-cannot-be-undone` `CP#a-first-booking-that-goes-wrong-costs-money`
- **Complaints (joiner):** "it's not easy to find my next match… see it right on the main screen"; an update removed finding full activities `CJ#finding-your-own-next-game`
- **Complaints:** "Card Declined- Generic Decline" with only a bot to ask `CP#the-saved-card-is-not-offered-or-is-declined-with-no-reason`
- **Complaints (newcomer):** "Once every month i can't log into the app through Facebook for 2 weeks"; kluby.org users a week without login (SIT-38) `CN#verification-gates-social-features-not-joining` `SIT#the-club-cancels-closes-or-changes`
- **Situations:** no signal in the hall (SIT-88); underground or on a flight (SIT-97) `SIT#people-on-court` `SIT#phones-pushes-and-email`

## 10. Money and names on screen (R-PLATFORM-52, 53)

- **Playtomic:** the card shows first names and the price per spot ("€12.54 / 60min"); sign-up asks "Name and last name" `CJ#what-a-match-card-shows` `CN#four-ways-in-a-phone-number-and-an-email-link`
- **Other platforms:** Playmore writes "17,50 zł / os." and "Organizuje {name}" `PF#playmore--open-games-each-player-pays-at-join` `PF#playmore--the-open-game-card-and-preview`

## Not reached by the topics

- R-PLATFORM-32 to 43 (token surfaces, start-up refusals, the stand-in provider, the console, the seed, the store reset, the local stack) govern no market moment `README.md`
- R-PLATFORM-25 (a change dealt within seconds, five minutes at worst): the only figure found is Playmore's card refreshing every 30 s `PF#playmore--the-open-game-card-and-preview`
- Candidate gaps: R-PLATFORM-2/6/14, the topics hold nothing on how rivals key retries or keep one charge per act, only the complaints above `CP#charged-twice-or-charged-when-the-booking-failed`

## 11. Gap answers, 2026-10-08 (GP = `topics/gaps-PLATFORM.md`)

- **R-PLATFORM-46:** Playmore refuses any write offline ("Spróbuj ponownie, gdy wróci zasięg") under a banner; Playtomic shows "Could not connect to the server…" `GP#playmore-blocks-every-write-while-offline-and-keeps-nothing-to-send-later` `GP#playtomic-shows-a-connection-error-and-has-no-words-for-a-press-sent-later`
- **R-PLATFORM-48:** no rival keeps a press made offline, open or closed app [ABSENT] `GP#no-rival-keeps-a-press-made-offline-once-the-app-is-closed`
- **R-PLATFORM-13:** Playmore: check "zanim zapłacisz ponownie", "Nie płać ponownie"; Playtomic only "Processing payment…", "Payment pending" `GP#playmore-tells-the-player-not-to-pay-twice-while-it-checks` `GP#playtomics-words-while-a-payment-is-pending`
- **R-PLATFORM-9:** Playtomic "This match is full"; Playmore "Ktoś właśnie zajął ostatnie wolne miejsce. Płatność nie została pobrana." `GP#playtomics-words-for-a-full-match-or-a-gone-slot` `GP#playmore-says-who-was-faster-and-that-nothing-was-taken`
- **R-PLATFORM-2, 6, 14:** Playmore never resends a write, refuses a "multi-click" server-side, keys standing-slot acts per act; Playtomic unknown `GP#playmore-never-retries-a-write-and-keys-some-acts`
- **R-PLATFORM-50:** Playmore's open-game list is not re-read while on screen; the strip's 30 s timer only re-counts the clock `GP#playmores-open-game-list-is-not-refreshed-while-it-is-on-screen`
- **R-PLATFORM-31:** Playmore's sign-out leaves the push token registered (removed only when pushes are muted); Playtomic not found `GP#playmores-sign-out-does-not-unregister-the-phone`
- **R-PLATFORM-24:** Przelewy24: available by the next business day's end, paid on request, by schedule or by default at 1000 zł; Tpay within 3 business days; PayU timing unpublished `GP#przelewy24-available-by-the-end-of-the-next-business-day-paid-out-on-request-or-by-a-schedule` `GP#tpay-on-request-or-automatically-transfer-within-three-business-days` `GP#payu-manual-or-every-n-days-timing-not-published`
- **R-PLATFORM-7:** mBank keeps an unsettled hold at most 30 days (14 before 20 Feb 2025); a direct charge carries the club's descriptor; the pending name in a Polish bank app not found `GP#mbank-keeps-an-unsettled-card-hold-at-most-30-days` `GP#on-a-direct-charge-the-clubs-descriptor-is-what-the-bank-receives`
- **R-PLATFORM-3, 20:** Playtomic: 2–10 business days, chat in office hours, no payments on its status page; Playmore names each refund's destination and a "Błąd zwrotu" `GP#playtomic-a-fixed-promise-of-days-then-chat-in-office-hours` `GP#playmore-says-where-each-refund-went-and-names-a-failed-one`
- **R-PLATFORM-28:** Stripe contacts full-Dashboard accounts directly; dispute emails are a per-user setting, default unstated `GP#stripe-speaks-directly-to-accounts-with-a-stripe-dashboard`
- **R-PLATFORM-16:** no Kraków club rule mentions the clock change; cut-offs are "24 godzin przed" [ABSENT] `GP#no-kraków-club-rule-mentions-the-clock-change`
- **R-PLATFORM-22:** Playmore publishes uptime (desk panel 98.4 % on 29 Jul 2026, else 100 %); kluby.org announces breaks in the app; tenis4U names no channel `GP#playmore-publishes-uptime-tenis4u-and-klubyorg-publish-none`

## Gaps answered 2026-10-09 (after S-01)

- **R-PLATFORM-48.** [POLICY] WhatsApp's clock means not yet sent, and since 2016–17 the message is queued and sent on reconnect; [DOCS] an iPhone app swiped away is not woken until reopened; [ABSENT] whether the queued message survives closing WhatsApp or a restart — only a dated device test settles it — `topics/gaps-S-01.md#whatsapp-a-clock-means-not-yet-sent-and-the-message-waits-and-goes-on-reconnect`, `topics/gaps-S-01.md#an-iphone-app-the-user-swiped-away-is-not-woken-until-it-is-opened-again`, `topics/gaps-S-01.md#whether-the-waiting-message-survives-closing-whatsapp-or-restarting-the-phone-not-found`.

## Gaps answered 2026-10-10 (after S-02)

- **R-PLATFORM-48.** [MEASURED] WhatsApp for Android registers for the phone's restart and names a messaging start-up observer; [DOCS] Android keeps scheduled work through the app closing and the phone restarting; [ABSENT] still whether a clock-marked message leaves before WhatsApp is reopened, which only a device test settles — `topics/gaps-S-02.md#whatsapps-android-app-starts-work-when-the-phone-restarts-a-messaging-task-among-it`, `topics/gaps-S-02.md#whether-a-clock-marked-message-leaves-before-whatsapp-is-reopened-still-not-found`.

## Gaps answered 2026-10-11 (S-01A hold round)

- **R-PLATFORM-64.** [POLICY] MATCHi never places a second hold (past 7 days it captures and refunds the difference); hotels and an OroCommerce Stripe module do re-authorise a saved card; [DOCS] no Stripe page or card-network rule limits a new approved hold (Visa's limits fall on retried declines and on checking an account with an amount); [DOCS] a matched reversal lifts a hold, an unmatched one leaves it 1 to 8 days — `topics/gaps-S-01A-hold.md#matchi-never-places-a-second-hold-past-7-days-it-takes-the-money-and-refunds-the-difference`, `topics/gaps-S-01A-hold.md#hotels-and-a-stripe-plug-in-do-place-a-second-hold`, `topics/gaps-S-01A-hold.md#stripe-documents-reauthorisation-only-for-in-person-payments-and-no-objection-to-a-new-hold`, `topics/gaps-S-01A-hold.md#the-card-networks-limits-apply-to-retried-declines-and-to-checking-a-card-with-an-amount`.
- **R-PLATFORM-66.** [POLICY]/[MEASURED] no Kraków club takes card payments through Stripe today (Przelewy24, Tpay, PayU, Autopay); [PRICE] negotiated pricing is by sales for "large payments volume"; [DOCS] on standalone fees the payment's own fee stays at zero for ever, while the Fees report itemises it by charge within 96 hours (Dashboard about 2 hours), so a refund keyed to the payment's fee would wait for ever for such a club — `topics/gaps-S-01A-hold.md#no-kraków-club-was-found-taking-card-payments-through-stripe-today`, `topics/gaps-S-01A-hold.md#negotiated-pricing-ic-among-it-is-arranged-through-sales-for-large-volumes`, `topics/gaps-S-01A-hold.md#on-standalone-fees-a-payments-own-fee-stays-at-zero-and-the-fee-for-it-appears-in-the-fees-report-within-days`.
