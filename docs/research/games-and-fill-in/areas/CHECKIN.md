# CHECKIN — check-in on the game's day: market digest

Rules R-CHECKIN-1 to R-CHECKIN-33: the QR and short code on the phone, the desk's Check in page, what a
check-in proves against a no-show or a bank dispute, and money. R-CHECKIN-33 (the games test console)
is internal tooling that no market fact touches. Digest written 2026-10-08 from the topic files (read
2026-10-06 to 2026-10-08). Paths are relative to this research folder; `market.md` means
`../games-and-fill-in-market.md`. Kinds as in the topics; *reading* is comparison, not a source.

**Read this first.** [ABSENT] Playtomic has no check-in: no built-in QR, and with door hardware players "go straight to the court … no need to stop at reception" — `topics/competitor-club.md#no-check-in-feature-door-codes-instead`. The nearest check-in found is Playmore's booking QR at a self-checkout station — `topics/platforms.md#playmore--check-in-qr-and-door-opening`.

## 1. The code: one per seat, and who can copy it (R-CHECKIN-1, R-CHECKIN-2, R-CHECKIN-24)

- **Competitor.** [POLICY] With hardware (QT System, Micro Solution, Smart Padel) "Access codes are created automatically for each reservation and refresh 10 minutes before the match starts": one per booking, not per player — `topics/competitor-club.md#no-check-in-feature-door-codes-instead`.
- **Competitor.** [POLICY] "Some clubs use an entry PIN so you can access the courts without going to reception", shown in the booking and its email; [ABSENT] a check-in step for open-match players — `topics/competitor-joiner.md#the-court-pin-is-in-the-booking-and-its-email`.
- **Platforms.** [POLICY] Playmore: "Kod QR rezerwacji — Zeskanuj ten kod przy stanowisku self-checkout w obiekcie", beside "Skopiuj link dla znajomego" (copy a link for a friend) — `topics/platforms.md#playmore--check-in-qr-and-door-opening`.
- **Platforms (R-CHECKIN-24).** [POLICY] MATCHi's access codes are per court and time window, "reusable, not tied to one booking"; [ABSENT] a QR check-in for court bookings — `topics/platforms.md#matchi--access-codes-in-the-confirmation`.
- **Platforms.** [PRICE] kluby.org opens the door by PIN, switched on "na x minut przed rezerwacją" — `topics/platforms.md#klubyorg--sms-receipts-and-remote-control`.
- **Status quo (R-CHECKIN-24).** [POLICY] A benefit card is personal: MultiSport's app QR or plastic card is shown with ID at reception — `topics/local-market.md#how-the-operators-say-a-card-is-used`.
- *Reading:* every code found is per booking or per court; none is per player, and none is said to resist a shared screen (`topics/competitor-club.md#no-check-in-feature-door-codes-instead`, `topics/platforms.md#matchi--access-codes-in-the-confirmation`).

## 2. When the code shows, and with no signal (R-CHECKIN-3 to R-CHECKIN-7)

- **Competitor (R-CHECKIN-3, R-CHECKIN-7).** [POLICY] Playtomic's PIN is in the confirmation email as well as the app; hardware codes refresh 10 minutes before — `topics/competitor-joiner.md#the-court-pin-is-in-the-booking-and-its-email`, `topics/competitor-club.md#no-check-in-feature-door-codes-instead`.
- **Platforms (R-CHECKIN-7).** [POLICY] MATCHi puts the codes "automatically" in the booking confirmation — `topics/platforms.md#matchi--access-codes-in-the-confirmation`.
- **Platforms (R-CHECKIN-4).** [POLICY] Playmore lets nobody through the door before paying: "Aby uzyskać dostęp do obiektu, należy najpierw opłacić rezerwację" — `topics/platforms.md#playmore--check-in-qr-and-door-opening`.
- **Status quo (R-CHECKIN-3).** [POLICY] Medicover Sport registers an entry "nie wcześniej niż 15 … minut przed jej rozpoczęciem" — `topics/local-market.md#how-the-operators-say-a-card-is-used`.
- **Situation (R-CHECKIN-7).** [ABSENT] No club or platform rule for no phone, a flat battery or no signal in the hall; *opinion* AGH still keeps a paper key book — `situations.md` SIT-88; APNs keeps one notice per app while offline — SIT-97.
- **Situation (R-CHECKIN-6).** [COMPLAINT] Paid courts whose door code did not open, with no refund (Playtomic NL, MATCHi SE) — `situations.md` SIT-37.

## 3. The club's choice, and the desk's page (R-CHECKIN-9 to R-CHECKIN-14, R-CHECKIN-20)

- **Competitor (R-CHECKIN-9).** [ABSENT] "Check-in" appears once in a list of phone admin actions, explained nowhere in 157 club articles — `topics/competitor-club.md#no-check-in-feature-door-codes-instead`.
- **Platforms (R-CHECKIN-9, R-CHECKIN-10).** [POLICY] Playmore's door is the club's choice: "Ten obiekt nie obsługuje otwierania z aplikacji" where not fitted; Loxone lets players in by phone; Multisport and FitProfit cards are scanned at the entrance — `topics/platforms.md#playmore--check-in-qr-and-door-opening`.
- **Status quo (R-CHECKIN-11 to R-CHECKIN-14).** [PRICE] Kraków desks already check a card on site, about 15 zł off per benefit card; [MEASURED] tenis4U has a `medicover-verify` step — `topics/local-market.md#how-kraków-clubs-take-the-cards-about-15-zł-off-per-card-on-site`.
- **Situation (R-CHECKIN-20).** [DATA] Booking systems go down; kluby.org users report a week without login after an update — `situations.md` SIT-38.
- **Complaints (R-CHECKIN-20).** [COMPLAINT] Playmore: "Dostaję komunikat, że zarezerwowane, a wcale nie jest… o czym dowiedziałem się na miejscu"; a cancellation the club "nie widzi u siebie" — `topics/complaints.md#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`.

## 4. What the desk reads, and what it refuses (R-CHECKIN-15 to R-CHECKIN-19, R-CHECKIN-21, R-CHECKIN-22)

- **Competitor (R-CHECKIN-15).** [POLICY] A Playtomic club learns a player's details only "through an online payment or by the player accepting your club's Terms & Conditions" — `topics/competitor-club.md#talking-to-players-and-what-the-club-sees-of-them`.
- **Competitor (R-CHECKIN-21).** [POLICY] Arriving 10 minutes late or more "may" count as a no-show — `topics/competitor-joiner.md#the-terms-no-show-covers-late-arrival-early-leaving-and-a-replaced-player`.
- **Status quo (R-CHECKIN-21).** [POLICY] Lateness eats the hour ("do czasu gry wliczany jest również czas spóźnienia"); Sosnowiec may let the court go after 15 minutes; the game before may overrun into yours — `situations.md` SIT-16, SIT-17, SIT-18.
- **Status quo (R-CHECKIN-21).** [POLICY] Medicover's entry window runs from 15 minutes before to the start — `topics/local-market.md#how-the-operators-say-a-card-is-used`.
- **Not found (R-CHECKIN-16 to R-CHECKIN-19, R-CHECKIN-22).** [ABSENT] What any desk system answers to a wrong-day, other-club or second scan — `topics/competitor-club.md#no-check-in-feature-door-codes-instead`, `topics/platforms.md#matchi--access-codes-in-the-confirmation`.

## 5. A wrong check-in, a stand-in, a player with no phone (R-CHECKIN-23 to R-CHECKIN-25)

- **Platforms (R-CHECKIN-23).** [POLICY] Playmore's only attendance marking is for coaches' classes, editable up to 6 h after — `topics/platforms.md#playmore--results-are-reported-confirmed-or-disputed`.
- **Competitor (R-CHECKIN-24).** [POLICY] Playtomic's no-show "may be applied" when a user "is replaced", the debt going "to the replaced User" — `topics/competitor-joiner.md#the-terms-no-show-covers-late-arrival-early-leaving-and-a-replaced-player`.
- **Situation (R-CHECKIN-24).** [POLICY] A friend turns up in place of the booked player; Playtomic lets no player hand a seat on, and the club swaps players if about 2 h are left — `situations.md` SIT-87.
- **Platforms (R-CHECKIN-24).** [POLICY] Playmore puts "Skopiuj link dla znajomego" beside the booking QR — `topics/platforms.md#playmore--check-in-qr-and-door-opening`.
- **Situation (R-CHECKIN-25).** [ABSENT] Any rule for checking in without a phone — `situations.md` SIT-88.
- **Status quo (R-CHECKIN-25).** [POLICY] MultiSport takes the plastic card as well as the app QR — `topics/local-market.md#how-the-operators-say-a-card-is-used`.

## 6. Check-in against a no-show report (R-CHECKIN-26 to R-CHECKIN-28)

- **Competitor.** [POLICY] "Only the affected players can report the no-show, and only through Playtomic"; "Your club cannot submit this report on the player's behalf" — `topics/competitor-club.md#no-shows-open-matches-only-reported-to-playtomic-by-players`.
- **Competitor.** [POLICY] A report within 7 days and before the result is confirmed; the absentee owes the court fee as a debt that blocks the app; the result is voided — `topics/competitor-joiner.md#a-no-show-is-reported-to-support-and-charged-as-a-debt`.
- **Competitor (R-CHECKIN-27).** [POLICY] Facing a late player the group may "Wait and Play" or "Declare No-Show"; "If a match result is added, the no-show will not be applied" — `topics/competitor-organiser.md#no-shows-and-late-arrivals`.
- **Competitor.** [ABSENT] No attendance score, strike count or ban threshold — `topics/competitor-joiner.md#no-attendance-score`.
- **Platforms.** [ABSENT] Playmore has no player no-show report — `topics/platforms.md#playmore--results-are-reported-confirmed-or-disputed`.
- **Status quo.** [POLICY] Miazga blocks booking after a no-show until paid; kluby.org blocks an account blocked by 2 clubs — `topics/local-market.md#no-shows-blocked-until-paid`; Fame Sport charges the booker the full court — `topics/local-market.md#the-booker-owes-the-whole-court`; a Kraków league: "A no-show = full court fee responsibility" — `topics/local-market.md#arranging-by-whatsapp-a-kraków-padel-league`.
- **Complaints (joiner, R-CHECKIN-26).** [COMPLAINT] "Despite being physically present… I was marked as a 'no-show' and charged… they relied solely on their 'system logs'"; tenis4U lets a club warn "bez poinformowania użytkownika", blocking booking at every club — `topics/complaints.md#marked-a-no-show-warned-or-blocked-without-a-fair-hearing`.
- **Complaints (organiser).** [COMPLAINT] "the window for reporting a no-show is closed even though the slot for our game finished two minutes ago"; "2 no shows, and 1 super later comer" — `topics/competitor-organiser.md#no-shows-the-organiser-cant-report`, `topics/complaints.md#players-who-dont-show-walk-off-or-come-late-go-unpunished`.
- **Complaints (club).** [DATA] PADELHUB capped active bookings "to stop the court-hoggers" — `topics/complaints.md#players-who-hold-courts-and-dont-come`.

## 7. Money, leaving after check-in, and Bookings (R-CHECKIN-29 to R-CHECKIN-31)

- **Competitor (R-CHECKIN-30).** [POLICY] Open matches are paid online; "payment at the club is not supported", and a desk payment "will create a debt" — `topics/competitor-club.md#pay-to-join-when-the-court-is-held`.
- **Competitor (R-CHECKIN-30).** [POLICY] In a split booking, a share paid at the desk but not marked within 2 h of the end is charged to the owner — `market.md#how-the-club-handles-the-hard-cases`.
- **Competitor (R-CHECKIN-29).** [POLICY] Inside 24 hours of a full match a player leaves only if the club agrees — `topics/competitor-club.md#leaving-inside-24-hours-goes-through-the-club`.
- **Competitor (R-CHECKIN-31).** [POLICY] Playtomic's booking list filters and exports bookings; [ABSENT] any arrival mark — `topics/competitor-club.md#the-booking-list`, `topics/competitor-club.md#no-check-in-feature-door-codes-instead`.
- **Status quo (R-CHECKIN-30).** [PRICE] Kraków desks take benefit cards as about 15 zł off on site; a share already paid in the app has no place for it — `situations.md` SIT-56, `topics/local-market.md#how-kraków-clubs-take-the-cards-about-15-zł-off-per-card-on-site`.
- **Status quo (R-CHECKIN-30).** [POLICY] Refused entry for wrong shoes "nie zwalnia Użytkownika z obowiązku uiszczenia opłaty" (AGH); a drunk player is turned away — `situations.md` SIT-78, SIT-89.
- **Complaints (R-CHECKIN-30).** [COMPLAINT] Shares paid at the centre were "not marked" and billed again; "charged me twice, once through the app and once on site" — `topics/complaints.md#a-share-paid-at-the-desk-is-not-recorded-and-the-organiser-is-billed-again`.

## 8. A bank dispute, and what the club can show (R-CHECKIN-32)

- **Provider.** [PRICE]/[DOCS] 90 zł per dispute, taken from the club's balance on a direct charge; for a future service "the dispute window starts on the event date" (120 days) — `topics/local-market.md#disputes-cost-90-zł-and-land-on-the-club`, `situations.md` SIT-59.
- **Provider.** [DOCS] For reservations "evidence of a cancellation policy can be material": the policy, how and where it was shown before purchase, the customer's messages — `situations.md` SIT-60.
- **Competitor.** [POLICY] A Playtomic club sees chargebacks only in reconciliation, and a player's chargeback "may be recorded as an outstanding debt"; [ABSENT] who bears the loss — `topics/competitor-club.md#chargebacks-what-the-club-is-told`, `topics/competitor-joiner.md#a-chargeback-becomes-a-debt`.
- **Competitor.** [POLICY] "You can't change results in Playtomic Manager": the club does not hold the result — `topics/competitor-club.md#results-belong-to-the-players`.
- **Complaints.** [COMPLAINT] Nobody on site, and the refund refused because "Playtomic da Geld schon ausgezahlt hat" — `topics/complaints.md#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`.

## Gaps round answers (read 2026-10-08)

- **R-CHECKIN-31.** [POLICY] tenis4U's desk marks each player's payment; [ABSENT] an arrival mark anywhere — `topics/gaps-CHECKIN.md#tenis4us-desk-marks-each-players-payment-never-an-arrival`.
- **R-CHECKIN-32.** [DOCS] Stripe wants proof the cardholder got the reserved service, with its date — `topics/gaps-CHECKIN.md#stripe-for-a-reserved-offline-service-show-it-was-received-and-when`.
- **R-CHECKIN-35.** [POLICY] MultiSport's desk terminal takes a typed token; [ABSENT] the device — `topics/gaps-CHECKIN.md#the-device-itself-was-not-found`.
- **R-CHECKIN-8.** [POLICY] Playmore notifies at each desk card scan — `topics/gaps-CHECKIN.md#playmore-notifies-the-player-when-the-desk-scans-a-declared-card`.
- **R-CHECKIN-23.** [POLICY] MultiSport undoes a visit within 20 min, Medicover 10 min — `topics/gaps-CHECKIN.md#multisport-a-new-code-at-the-desk-within-20-minutes`.
- **R-CHECKIN-24.** [POLICY] MultiSport's photo; Fame Sport bans screenshots — `topics/gaps-CHECKIN.md#a-kraków-club-bans-screenshots-of-its-apps-codes`.
- **R-CHECKIN-25.** [ABSENT] a no-phone rule; desks settle by name — `topics/gaps-CHECKIN.md#no-kraków-rule-for-a-booked-player-without-a-phone`.
- **R-CHECKIN-7.** [ABSENT] its meaning — `topics/gaps-CHECKIN.md#padel-mates-lists-offline-check-in-as-an-app-feature-and-never-explains-it`.
- **R-CHECKIN-34.** [POLICY] "Zapłacono online (nr operacji)" — `topics/gaps-CHECKIN.md#kraków-desk-systems-show-an-online-payment-tenis4u-with-its-operation-number`.
- **R-CHECKIN-30.** [POLICY] Playmore's card discount waits for the desk scan — `topics/gaps-CHECKIN.md#the-card-is-declared-online-and-scanned-at-the-desk-and-the-discount-waits-for-the-scan`.
- **R-CHECKIN-21.** [POLICY] KSOS: court let 10 min before — `topics/gaps-CHECKIN.md#ksos-lets-the-court-go-if-nobody-is-there-10-minutes-before-others-count-lateness-in-the-hour`.

## Gaps answered 2026-10-09 (after S-01)

- **R-CHECKIN-35.** [POLICY] Polish club desk software takes USB readers that type a scan as keystrokes (PerfectGym POSweb: "Wysyła numer karty jako tekst"; eFitness supports Zebra DS2208, which [DOCS] ships as a USB keyboard) — `topics/gaps-S-01.md#polish-club-desk-systems-take-handheld-scanners-that-type-what-they-read-as-keystrokes`. [ABSENT] which reader a named Kraków padel desk owns — `topics/gaps-S-01.md#which-reader-a-kraków-padel-desk-owns-still-not-found`.
