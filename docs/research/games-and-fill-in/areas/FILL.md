# FILL — the moment a game fills: market digest

Rules R-FILL-1 to R-FILL-48: Undo, all-or-nothing charging, It's a game!, a refused share and its
recovery. Written 2026-10-08 from the topic files (read 2026-10-06 to 2026-10-08).
Paths are relative to this research folder; `market.md` means `../games-and-fill-in-market.md`.
Kinds as in the topics; *reading* is arithmetic or comparison, not a source.

## 1. A yes that moves money, Undo and the countdown (R-FILL-1 to R-FILL-9)

- **Competitor.** [POLICY] Playtomic charges an open-match spot at join: "the user will be charged immediately, regardless of the country or model" — `topics/competitor-joiner.md#she-pays-her-own-spot-online-at-join-charged-at-once`.
- **Competitor.** [POLICY] The join runs through a checkout, with a *Booking Cancellation Policy* row before "Continue to payment" — `topics/competitor-joiner.md#adding-a-card-at-checkout-takes-four-screens`, `topics/competitor-joiner.md#the-checkout-shows-the-cancellation-block-never-a-passed-deadline`.
- **Competitor (R-FILL-2).** [POLICY] Its nearest thing to Undo: a match not yet full can be left any time before the start, refunded in full, fee included — `topics/competitor-joiner.md#a-match-not-yet-full-can-be-left-any-time-before-it-starts`, `topics/competitor-joiner.md#leaving-refunds-in-full-the-service-fee-included`.
- **Platforms.** [POLICY] No racket app found charges on a swipe or one tap; each joins through a payment step (Playmore "Dołącz za {price}", MATCHi "Tap Join. Pay your spot price") — `topics/platforms.md#swipe-decks-deal-people-not-games`, `market.md#s05-g-11--swipeable-card-decks-a-swipe-or-one-tap-that-pays-padel-mates-suggestions`.
- **Platforms (R-FILL-3).** [POLICY] The only payment timer found: Playmore gives an unpaid booking 30 minutes ("Opłać do {time} · Zostało {minutes} min"), then cancels it — `topics/platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`.
- **Platforms (R-FILL-9, R-FILL-14).** [POLICY] Playmore answers a slot taken a moment earlier with "Ktoś właśnie zajął ten termin. Wybierz inny slot." — `topics/platforms.md#playmore--the-court-is-held-from-publication`; Playtomic cancels a short match when another fills the last court — `topics/competitor-organiser.md#the-court-is-held-in-stages`.
- **Law (R-FILL-1, R-FILL-7).** [LAW] The control that binds a consumer to pay must say so ("zamówienie z obowiązkiem zapłaty"), even when payment falls due only after a later condition (CJEU *Conny*); [ABSENT] no authority on a swipe or "I'm in" — `topics/local-market.md#the-order-button-and-a-yes-that-charges-later`.
- **Provider (R-FILL-9, R-FILL-17).** [DOCS] Stripe keeps a result per idempotency key for 24 h or more; concurrent changes to one payment fail — `market.md#robustness-idempotency-webhooks-rate-limits-card-testing`.
- **Complaints (R-FILL-17).** [COMPLAINT] "It took the money but then said there was an issue and didn't book me on… it took the money twice" (GB, 2026-08-12); Playmore "zacięła się przy płatności… straciłem 100 zł za duplikat rezerwacji" — `topics/complaints.md#charged-twice-or-charged-when-the-booking-failed`.

## 2. Everyone pays together or nobody pays (R-FILL-10 to R-FILL-17)

- **Competitor.** [POLICY] Playtomic books the court in stages (never at one player; at two only >12 h ahead; at three >4 h; at four at once) and cancels a match still short about 1 h before, refunding all, fee included — `topics/competitor-organiser.md#the-court-is-held-in-stages`, `topics/competitor-organiser.md#automatic-cancellation-and-refunds`.
- **Competitor.** [POLICY] In a split private booking only the owner pays at booking; shares unpaid 2 h after the game fall on the owner, and Poland is on neither guarantee list, so likely a debt — `topics/competitor-club.md#split-payment-an-unpaid-share-is-charged-after-the-game`, `topics/competitor-organiser.md#who-covers-unpaid-shares-three-guarantees-by-country`.
- **Platforms.** [POLICY] Playmore *Gry otwarte* has Raketa's outcome ("Komplet graczy – gra potwierdzona… Brak kompletu… pełny zwrot dla wszystkich") but every player pays at join, organiser first — `topics/platforms.md#playmore--open-games-each-player-pays-at-join`.
- **Platforms.** [POLICY] MATCHi holds the card at booking and captures 12 h after the start or 7 days after booking, whichever comes first — `topics/platforms.md#matchi--the-card-is-held-at-booking-and-captured-later`.
- **Provider (R-FILL-10, R-FILL-15).** [DOCS] A card hold lasts 4 days 18 h (Visa, merchant-initiated) to 7 days; cancelling an uncaptured payment costs nothing; BLIK and P24 cannot be held — `topics/local-market.md#how-long-a-hold-lasts`.
- **Provider (R-FILL-11).** [DOCS] Charging a saved card without the player there needs a recorded agreement naming the transactions, timing, how the amount is set and the cancellation policy — `topics/local-market.md#charging-a-saved-card-without-the-player-there`.
- **Price fixed at the deal (R-FILL-12).** [POLICY] Playtomic's spot price can differ between joiners by the court free when each joins; its terms keep price changes off confirmed orders — `topics/competitor-joiner.md#the-price-per-spot-can-differ-between-joiners`, `topics/competitor-club.md#a-changed-setting-and-bookings-already-made`. [DOCS] UOKiK: new prices reach a later automatic charge only with prior consent — `topics/local-market.md#which-terms-bind-when-a-yes-becomes-a-booking-later`.
- **Status quo.** [POLICY] Today the booker owes the whole court; kluby.org charges the booker's saved card for unpaid shares 2 h after the game; friends pay back by a free BLIK transfer or request — `topics/local-market.md#the-booker-owes-the-whole-court`, `topics/local-market.md#paying-a-friend-back-blik-to-a-phone-number-and-a-payment-request`.
- **Processor down (R-FILL-16).** [DATA] PKO BP's app and BLIK were down one July 2025 night; plastic cards worked — `situations.md` SIT-30.
- **Complaints.** [COMPLAINT] The organiser's card carries everyone: "charges you the full 60 and refunds you within 2 weeks"; a hold "for up to a week" — `topics/complaints.md#the-organisers-card-carries-everyones-share-until-the-others-pay`.
- **Complaints (R-FILL-15).** [COMPLAINT] Playmore, PL 2026-07-17: "Pieniądze na koncie zablokowane, ale płatność nieudana" — `topics/complaints.md#charged-twice-or-charged-when-the-booking-failed`.
- *reading:* a joiner of a 40 zł Playtomic spot pays 43,99 zł at join; at Raketa nothing moves until the last yes — `topics/competitor-joiner.md#reading-on-money-at-the-moment-of-joining`.

## 3. The booked game: court, sides, chat and the player's other yeses (R-FILL-18 to R-FILL-26)

- **Court (R-FILL-19).** [POLICY] Playtomic assigns the court by "Autoselect" and keeps its type; the page then reads "✓ Court booked" — `topics/competitor-organiser.md#creating-an-open-match-the-doors-and-what-the-creator-sets`, `topics/competitor-joiner.md#the-match-page-shows-whether-the-court-is-booked`.
- **Sides (R-FILL-20).** [POLICY] Playtomic joiners pick side A or B; Playmore assigns sides only at the result; only small apps print a balance (Padel Pals "Win probability 59% / 41%") — `topics/platforms.md#a-balance-figure-or-suggested-sides`, `market.md#s05-g-7--balance-or-match-quality-percentage-suggested-sides-pados-elo`.
- **Chat (R-FILL-21).** [POLICY] Playtomic's match chat is open to anyone, booked or not — `topics/competitor-joiner.md#the-match-chat-is-public`.
- **Blocks at the fill (R-FILL-18).** [POLICY] A blocked player cannot join a Playtomic match; [ABSENT] blocking someone already in — `topics/competitor-joiner.md#a-blocked-player-cannot-join`.
- **One game per hour (R-FILL-23, R-FILL-24).** [ABSENT] No club or platform rule on one player in two games at the same hour — `situations.md` SIT-85; Playtomic has no overlap check — `market.md#77-rejoining-overlapping-games-per-player-limits-and-closures-over-a-held-court-s06-g5-s06-g8-s07-s08-g10`. [COMPLAINT] "you cannot be added to more than one game a day" — `topics/competitor-newcomer.md#how-many-games-at-once`.
- **A paused yes that books by itself (R-FILL-25, R-FILL-26).** [POLICY] Every racket waiting list found sends an offer and charges nobody until she books; the one auto-enrolment that moves money (Zenamu) takes it when she joins the list — `market.md#s08-g9--waitlists-automatic-enrolment-and-charge-or-an-offer-to-accept`.
- **Weekly cap.** [ABSENT] No racket app lets a player cap her own games per week; club caps are checked at join — `market.md#s08-g1--a-players-own-price-ceiling-or-weekly-cap-is-it-checked-at-join`.

## 4. It's a game! and what everyone is told (R-FILL-27 to R-FILL-30)

- **Competitor.** [POLICY] Playtomic emails "Confirmation of new booking, match or activity joined" and "Receipt of a transaction" (cannot be switched off), plus the club's registration message — `topics/competitor-joiner.md#on-joining-a-confirmation-email-and-the-clubs-message`.
- **Competitor.** [ABSENT] No push when a match fills or someone joins — `topics/competitor-joiner.md#players-are-not-told-when-someone-joins-or-leaves-an-open-match`.
- **Platforms.** [POLICY] Playmore: "Ktoś dołączył, gra potwierdzona, gra anulowana - gracze wiedzą wszystko bez udziału recepcji"; a full game reads "Skład pełny · potwierdzimy o {time}" and is confirmed only at its cut-off — `topics/platforms.md#playmore--waiting-lists-and-alerts`, `topics/platforms.md#playmore--the-court-is-held-from-publication`.
- **Receipt (R-FILL-30).** [DOCS] On a direct charge the receipt uses the club's Stripe settings and must carry its legal name — `topics/local-market.md#receipts-on-a-direct-charge-come-from-the-clubs-stripe-settings`; [LAW] a confirmation on a durable medium is due before the service — `topics/local-market.md#what-the-player-must-see-before-being-bound`.
- **Receipt.** [POLICY] Playtomic's receipt is the full share or only its fee, by the club's set-up — `topics/competitor-joiner.md#the-receipt-is-the-full-share-or-only-the-fee`; [DOCS] a club's name may not be recognised on a bank statement — `situations.md` SIT-61.
- **Phones (R-FILL-27).** [DOCS] Samsung's battery saver delays pushes; an iPhone Focus holds all but Time Sensitive ones — `situations.md` SIT-95, SIT-96.
- **Complaints.** [COMPLAINT] "Es kommt immer dieselbe Push-Benachrichtigung nochmal gleichzeitig als Mail" — `topics/complaints.md#notifications-missing-duplicated-or-impossible-to-tune`.

## 5. On request: the last yes asks the club (R-FILL-31, R-FILL-32)

- **Competitor.** [ABSENT] Every Playtomic online booking is confirmed at once — `topics/competitor-club.md#no-booking-that-waits-for-the-club-to-confirm`.
- **Platforms.** [ABSENT] No platform read books a court on the club's confirmation — `topics/platforms.md#no-club-confirms-booking-mode-anywhere`; Playmore's terms form the contract at the club's confirmation yet ship no confirm step — `topics/platforms.md#playmore--the-contract-waits-for-the-club-but-no-confirm-step-exists`.
- **Provider.** [DOCS] A hold placed while the club decides runs out after 4 days 18 h to 7 days — `situations.md` SIT-63.

## 6. A refused share and its recovery (R-FILL-33 to R-FILL-48)

- **Competitor.** [POLICY] Playtomic names insufficient funds, a wrong CVC and an expired card ("delete the card and enter it again"); [ABSENT] no retry screen, no held seat, no 3-D Secure — `topics/competitor-joiner.md#3-d-secure-and-failed-payments`, `topics/competitor-newcomer.md#when-the-first-payment-fails`.
- **Competitor (R-FILL-41).** [POLICY] An unpaid share becomes a debt shown in the app that blocks booking until paid — `topics/competitor-joiner.md#a-joiner-the-club-adds-pays-in-the-app-or-owes-a-debt`, `situations.md` SIT-66.
- **Platforms (R-FILL-34, R-FILL-47).** [POLICY] Playmore names the decline: "Bank odrzucił płatność — brak środków / limit karty / karta nieważna" — `topics/platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`.
- **Provider (R-FILL-37, R-FILL-38).** [DOCS] An off-session charge can fail with `authentication_required`; recovery confirms the same PaymentIntent, with the saved card for authentication and a new one otherwise; Stripe advises at most eight retries — `market.md#off-session-charges-declines-and-recovery`, `situations.md` SIT-62.
- **Provider (R-FILL-45).** [ABSENT] Whether a cloned card used up by a failed attempt can be confirmed again — `topics/local-market.md#one-saved-card-charged-on-each-clubs-account`.
- **Provider (R-FILL-42 to R-FILL-44).** [DOCS] A hold ends when cancelled or at expiry, releasing the money — `topics/local-market.md#how-long-a-hold-lasts`.
- **Provider (R-FILL-46).** [DOCS] The provider's notice may come twice, late or out of order — `situations.md` SIT-99.
- **Cards that fail later.** [DOCS]/[POLICY] Expiry or replacement (SIT-64), Revolut single-use cards (SIT-68), Apple Pay tokens tied to one phone (SIT-69), a card's own internet limit (SIT-70), BLIK as most Poles' way to pay (SIT-71) — `situations.md`.
- **First card (R-FILL-48).** [POLICY] Playtomic saves the card during the first payment ("Save the payment method…" pre-ticked) or under Profile › My Payments — `topics/competitor-newcomer.md#adding-the-first-card`.
- **Status quo (R-FILL-33).** [POLICY] Today the booker pays a missing share; Playtomic charges the holder 2 h after the match — `topics/local-market.md#the-booker-owes-the-whole-court`, `situations.md` SIT-54.
- **Complaints.** [COMPLAINT] "Saved payment method is not offered"; "'Card Declined- Generic Decline'… just a bot" — `topics/complaints.md#the-saved-card-is-not-offered-or-is-declined-with-no-reason`.
- **Complaints.** [COMPLAINT] "lack of possibility in payment with BLIK is disappointing" — `topics/complaints.md#no-blik-no-google-pay-no-paypal`.
- **Complaints (R-FILL-33).** [COMPLAINT] The organiser pays for a drop-out: "encima pague yo su parte" — `topics/complaints.md#the-organiser-takes-the-hit-when-a-player-drops-out-late-or-doesnt-show`.

## Gaps round answers (2026-10-08)

In `topics/gaps-FILL.md` (`g`), by section.

- **R-FILL-1/7/11/26.** [LAW] The rule covers "a button or a similar function"; [ABSENT] no ruling on a swipe or a priced "I'm in" — `g#1-the-order-control`.
- **R-FILL-1–4.** [DOCS] Gmail's 5–30 s Undo; [POLICY] Uber's free 2 min; [ABSENT] no app charging after an undo count — `g#2-undo-before-money-moves`.
- **R-FILL-5/6/8.** [DOCS] Only Stripe Terminal stores and forwards offline payments, at the seller's risk — `g#3-kept-offline-sent-later`.
- **R-FILL-6.** [DOCS] Android timers stop in the background; iOS suspends after ~5 s; not measured — `g#4-the-countdown-in-the-background`.
- **R-FILL-11.** [DOCS] Raketa's terms name what, when, how much and cancelling, not how often — `g#5-the-saved-card-agreement`.
- **R-FILL-15/36/44/49.** [POLICY] mBank drops a hold on the cancellation, else 14 days online — `g#6-released-holds-on-polish-cards`.
- **R-FILL-16.** [DOCS] The charge request is refused, not each card — `g#7-a-club-that-lost-card-payments`.
- **R-FILL-19.** [ABSENT] No feed, import or API at kluby.org or tenis4U — `g#8-blocking-hours-from-outside`.
- **R-FILL-20.** [DOCS] Raketa's sides bind the result; [POLICY] Playtomic lets players swap before it — `g#9-the-drawn-sides`.
- **R-FILL-21.** [POLICY] tenis4U pushes tournaments only — `g#10-a-club-messaging-its-players`.
- **R-FILL-27.** [ABSENT] — `g#11-the-fourth-joiner`. **R-FILL-30.** [DOCS] No club receipt: no address — `g#12-the-clubs-own-receipt`.
- **R-FILL-31.** [POLICY] Desks ~07:00–23:00, booking on the spot — `g#13-desk-hours`.
- **R-FILL-35.** [POLICY] Playtomic shows each share pending or paid — `g#14-when-another-share-fails`.
- **R-FILL-36/37/42/45.** [ABSENT] No soft-decline rate; re-confirming a used clone untested; [DOCS] the window follows the successful attempt — `g#15-off-session-declines`.

## Gaps answered 2026-10-10 (after the S-01B refresh)

- **R-FILL-53, R-FILL-56 (R-FILL-42, R-FILL-54).** [DOCS] Visa since 13 April 2024: 10 days for a payment the cardholder makes online, 5 for one the merchant makes; Stripe holds a customer-initiated payment 7 days; the real `capture_before` of a payment confirmed in the app still needs a test account [ABSENT]. [MEASURED] tenis4U served no free hours on the evening of 10 October, so how fast a last court sells is still not timed [ABSENT] — `topics/gaps-S-01B.md#visas-own-rule-since-13-april-2024-10-days-for-a-payment-the-cardholder-makes-online-5-for-one-the-merchant-makes` `topics/gaps-S-01B.md#the-real-capture_before-of-such-a-payment-still-not-read` `topics/gaps-S-01B.md#the-third-read-meant-to-time-the-last-courts-could-not-be-taken`
