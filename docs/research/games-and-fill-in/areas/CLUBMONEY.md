# CLUBMONEY — the club as seller: fees, Stripe, Money, payouts, refunds, disputes, receipts: market digest

Rules R-CLUBMONEY-1 to R-CLUBMONEY-29. Written 2026-10-08 from the topic files (read 2026-10-06 to
2026-10-08), `situations.md` and, where a topic points back to it, `market.md` (`../games-and-fill-in-market.md`).
Kinds as in the topics; *reading* is comparison, not a source.

**Read this first.** Playtomic's New Billing Model also makes the club the seller on its own Stripe account, but takes a contract commission and pays weekly by payment date, before the game — `topics/competitor-club.md#nbm-the-club-sells-and-is-paid-weekly-by-payment-date-before-the-game`. MATCHi pays monthly by the game's date — `topics/platforms.md#matchi--the-club-is-paid-monthly-by-the-games-date`. Kraków clubs sell through Przelewy24 or Tpay as the seller — `topics/local-market.md#the-club-is-the-seller-the-platform-is-not-a-party`.

## 1. Who sells, and who pays the card fee (R-CLUBMONEY-1 to -3)

- **Provider (R-CLUBMONEY-1).** [DOCS] "Direct charges: The merchant of record is the connected account"; the seller "is also liable for any disputes or refunds" — `topics/local-market.md#direct-charges-make-the-club-the-seller`.
- **Provider (R-CLUBMONEY-1, -2).** [DOCS] With `fees_collector=stripe` Stripe takes payment, dispute and 3-D Secure fees from the club and no Connect fee — `topics/local-market.md#who-pays-stripes-fees`; with `losses_collector=stripe` Stripe carries a negative balance — `market.md#accounts-v2-the-clubs-connected-account`.
- **Provider (R-CLUBMONEY-2).** [PRICE] EEA standard cards 1,5 % + 1 zł, premium 1,9 %, UK 2,5 %, international 3,25 % (+1 zł each), conversion +2 % — `topics/local-market.md#what-polish-operators-charge-against-stripe`, `situations.md` SIT-58; [DOCS] fees "aren't returned" on a refund — `topics/local-market.md#who-pays-stripes-fees`.
- **Competitor (R-CLUBMONEY-1, -3).** [POLICY] Unpublished plan prices and a commission "defined in your club's contract", deducted "before the money reaches you" (example 3,5 %), with no separate card fee — `topics/competitor-club.md#a-commission-on-every-online-payment-per-contract`; the player pays a service fee the club may take on — `topics/competitor-club.md#the-players-service-fee-which-the-club-may-take-on`.
- **Platforms (R-CLUBMONEY-1).** [PRICE] Playmore 299 zł/month + 1,79 % online; tenis4U 49–149 zł/month; kluby.org 2 % online; PADO 2 %; MATCHi 4 % — `topics/platforms.md#playmore--what-a-club-pays`, `topics/platforms.md#12-summary`.
- **Status quo (R-CLUBMONEY-2).** [PRICE] On a 40 zł share Stripe takes 1,60 zł; Przelewy24, Tpay and PayU 0,74–1,03 zł — `topics/local-market.md#what-polish-operators-charge-against-stripe`. Players know a flat 2 % kept on an online refund — `topics/local-market.md#the-refund-deduction-players-already-know-a-flat-2-`.
- **Complaints, club (R-CLUBMONEY-1).** [COMPLAINT] "Ett monopol som ruinerar klubbar" — `topics/complaints.md#a-platforms-fees-turn-players-against-the-club`.

## 2. Connecting payments, and staying connected (R-CLUBMONEY-4 to -8, -25)

- **Competitor (R-CLUBMONEY-4).** [POLICY] "It's mandatory for your club to create a Stripe account"; "Stripe may request extra verification" — `topics/competitor-club.md#stripe-onboarding-through-playtomic`; clubs keep their details in a Stripe Express dashboard — `market.md#story-stage-gaps-club-terms-the-clubs-first-screen-payment-account-warnings-chargebacks`.
- **Competitor (R-CLUBMONEY-5, -8).** [ABSENT] What Manager shows when a live club's Stripe account is restricted — `topics/competitor-club.md#stripe-onboarding-through-playtomic`.
- **Provider (R-CLUBMONEY-4).** [DOCS] A Polish club is `individual` (18 fields), `company` (45) or `non_profit` (36); verification takes "a few minutes to a few business days" — `topics/local-market.md#what-a-polish-club-must-supply-to-stripe`.
- **Provider (R-CLUBMONEY-5, -6).** [DOCS] `currently_due`, `past_due`, `pending_verification`; each v2 requirement waits on `stripe` ("Integrator should do nothing.") or on the `user` — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Provider (R-CLUBMONEY-8).** [DOCS] A missed deadline "typically disables payouts", then perhaps charges; Stripe emails the club itself (the platform may brand it), with no fixed notice — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Provider (R-CLUBMONEY-6).** [DOCS] Webhooks may arrive twice or out of order, retried up to three days — `situations.md` SIT-99.
- **Provider (R-CLUBMONEY-25).** [DOCS] A full-Dashboard club is a Stripe user and gets dispute notices itself — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Situations (R-CLUBMONEY-8).** [DOCS] A payout that "keeps getting pushed out … is most likely due to an account verification requirement" — `situations.md` SIT-100.

## 3. A club that stops taking payments (R-CLUBMONEY-9)

- **Competitor.** [POLICY] A club unpaid for 5 days goes inactive and "will not be able to receive bookings"; [ABSENT] bookings already made, and a restricted Stripe account — `market.md#story-stage-gaps-closing-hours-changing-prices-switching-courts-off-an-inactive-club`.
- **Provider.** [DOCS] Under `losses_collector=stripe` "You can't pause payments or payouts for your connected accounts"; [ABSENT] refunds once charges are disabled — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Platforms.** [POLICY] A club leaving Playmore takes no new bookings, and those made before are settled — `topics/platforms.md#playmore--a-club-leaving-or-unable-to-host`.

## 4. The Money page (R-CLUBMONEY-10 to -13, -24)

- **Competitor (R-CLUBMONEY-10, -11).** [POLICY] Payments filtered by payment or **service** date, with CSV; Payment Collection by service date, per player; reports update hourly — `topics/competitor-club.md#what-the-club-sees-of-its-money`.
- **Competitor (R-CLUBMONEY-24).** [POLICY] A Payout Summary Report "every 7 days" lists transactions, fees, VAT and "the final amount transferred after deductions" — `topics/competitor-club.md#what-the-club-sees-of-its-money`; missing payout codes "might be … chargebacks or refunds" — `topics/competitor-club.md#chargebacks-what-the-club-is-told`.
- **Platforms (R-CLUBMONEY-10).** [POLICY] MATCHi statements go by "the activity's start time for bookings", not the capture date — `topics/platforms.md#matchi--the-club-is-paid-monthly-by-the-games-date`; Playmore's monthly report shows "kwotę do wypłaty" — `topics/platforms.md#playmore--the-clubs-money-passes-through-reservise`.
- **Provider (R-CLUBMONEY-13).** [PRICE] The real fee depends on the card, 1,5 % to 3,25 % + 1 zł — `topics/local-market.md#what-polish-operators-charge-against-stripe`; *reading:* the 1,5 % + 1 zł estimate is the lowest.

## 5. When the club is paid (R-CLUBMONEY-14 to -19, -27, -28)

- **Competitor (R-CLUBMONEY-14).** [POLICY] NBM pays "based on the payment date rather than the match date", every Monday, "even if the match itself takes place later"; refunds come off the next payout, which can go negative and be "withdrawn from your bank account" — `topics/competitor-club.md#nbm-the-club-sells-and-is-paid-weekly-by-payment-date-before-the-game`.
- **Competitor (R-CLUBMONEY-14, -16).** [POLICY] Distribution Model: twice a month, matches "after the match has been played" — `topics/competitor-club.md#distribution-model-and-obm-paid-twice-a-month`.
- **Platforms (R-CLUBMONEY-15, -17).** [POLICY] MATCHi pays ~15th "if there's a positive balance", else invoices the venue — `topics/platforms.md#matchi--the-club-is-paid-monthly-by-the-games-date`; Playmore pays per settlement period, [ABSENT] its length — `topics/platforms.md#playmore--the-clubs-money-passes-through-reservise`.
- **Provider (R-CLUBMONEY-14, -19).** [DOCS] Poland: first payout after 7 days (7–14 by risk), then 3 business days, minimum 5 PLN; delaying payouts needs loss liability or platform controls; "Stripe doesn't provide escrow services" — `topics/local-market.md#payouts-in-poland`. Whether payouts after the game work under `losses_collector=stripe` is left open — `market.md#payouts-poland-and-holding-the-clubs-money-until-after-the-game`.
- **Provider (R-CLUBMONEY-19).** [DOCS] Idempotency keys may be pruned after 24 hours: "We generate a new request if a key is reused after the original is pruned"; payouts create at 15 a second — `market.md#robustness-idempotency-webhooks-rate-limits-card-testing`.
- **Provider (R-CLUBMONEY-17).** [DOCS] A negative balance is offset against future payments, with no payouts while negative — `market.md#refunds`.
- **Situations (R-CLUBMONEY-15, -28).** [DOCS] A weekend or holiday payout arrives the next business day; a late one may sit with the bank — `situations.md` SIT-29; a refund after the club is paid — SIT-101.
- **Competitor (R-CLUBMONEY-27).** [POLICY] Each admin opts into an email per booking; [ABSENT] a daily digest — `topics/competitor-club.md#staff-logins-roles-and-who-gets-booking-emails`.
- **Complaints, joiner (R-CLUBMONEY-14).** [COMPLAINT] Nobody on site, refund refused because "Playtomic da Geld schon ausgezahlt hat" — `topics/complaints.md#payouts-and-refunds-after-the-club-has-been-paid`.
- **Complaints, club (R-CLUBMONEY-14 to -20).** [ABSENT] A club's own complaint about payouts — `topics/complaints.md#payouts-and-refunds-after-the-club-has-been-paid`.

## 6. A payout that fails or comes back (R-CLUBMONEY-20, -23)

- **Competitor.** [POLICY] A failed payout is made "manually"; a bounced one "is returned to us. It is not lost", and the club asks Customer Care to resend — `topics/competitor-club.md#a-payout-that-fails`.
- **Provider.** [DOCS] Payout events on connected accounts are v1 only: `payout.created`, `updated`, `paid`, `failed` — `market.md#payouts-poland-and-holding-the-clubs-money-until-after-the-game`.

## 7. Refunds and disputes (R-CLUBMONEY-21, -22)

- **Provider (R-CLUBMONEY-21).** [DOCS] A refund comes from the club's available balance; if short, a card refund waits as pending, then fails; a BLIK or P24 refund fails at once — `topics/local-market.md#refunds-come-out-of-the-clubs-balance`; a refund to a closed card can come back 30 days later — `situations.md` SIT-65.
- **Competitor (R-CLUBMONEY-21).** [POLICY] An in-app payment is refunded automatically; one paid at the club "you are responsible for issuing the refund" — `topics/competitor-club.md#adding-or-removing-a-player`.
- **Platforms (R-CLUBMONEY-21).** [POLICY] Playmore refunds to its wallet and keeps the service fee — `topics/platforms.md#playmore--refunds-go-to-the-wallet-and-the-fee-is-kept`.
- **Provider (R-CLUBMONEY-22).** [PRICE] 90 zł per dispute, never returned, and 90 zł more to contest; [DOCS] amount and fee come from the club's balance; the window "starts on the event date" — `topics/local-market.md#disputes-cost-90-zł-and-land-on-the-club`, `market.md#disputes`.
- **Provider (R-CLUBMONEY-22).** [DOCS] For a reservation "evidence of a cancellation policy can be material" — `situations.md` SIT-60; unrecognised charges — SIT-61; a chargeback weeks later — SIT-59.
- **Competitor (R-CLUBMONEY-22).** [POLICY] A chargeback "may be recorded as an outstanding debt"; [ABSENT] who bears the loss — `topics/competitor-club.md#chargebacks-what-the-club-is-told`.
- **Complaints, joiner (R-CLUBMONEY-21).** [COMPLAINT] "Another 14 days holding my money"; "Nie zwracają środków za anulowaną rezerwację" — `topics/complaints.md#refunds-are-slow-partial-or-never-arrive`.

## 8. Receipts and invoices (R-CLUBMONEY-26, -24)

- **Law.** [LAW] No cash register for a consumer service paid in full online to the seller's account where records tie each payment to its sale; KIS accepted per-booking identifiers — `topics/local-market.md#no-cash-register-for-sales-paid-fully-online`.
- **Law.** [LAW] A consumer gets an invoice only if asked within 3 months, a business always; KSeF for invoices to a NIP; court time at 8 % VAT — `topics/local-market.md#invoices-on-request-for-consumers-always-for-businesses`, `topics/local-market.md#ksef`, `topics/local-market.md#vat-on-court-time-is-8-`.
- **Provider.** [DOCS] Direct-charge receipts use the club's own Stripe settings; a platform may pass `receipt_email` — `topics/local-market.md#receipts-on-a-direct-charge-come-from-the-clubs-stripe-settings`.
- **Competitor.** [POLICY] The club invoices the player when asked; [ABSENT] anything for Poland — `topics/competitor-club.md#who-invoices-whom`, `topics/competitor-club.md#nothing-for-poland`.
- **Platforms.** [POLICY] Playmore: invoices "wystawia bezpośrednio Partner" — `topics/platforms.md#playmore--operator-scale-and-seller`; kluby.org sells e-paragony, 0–60 zł a month — `topics/platforms.md#klubyorg--sms-receipts-and-remote-control`.
- **Complaints, joiner.** [COMPLAINT] "you can't get receipts from the club"; "App does not produce VAT receipt" — `topics/complaints.md#no-receipt-or-vat-invoice`.

## Rules no market fact touches

R-CLUBMONEY-29, the laptop's stand-in for Stripe; R-CLUBMONEY-12 only as a contrast with Playtomic's
per-player view (`topics/competitor-club.md#what-the-club-sees-of-its-money`).

## Gaps round answers (read 2026-10-08)

- **R-CLUBMONEY-20.** [DOCS] A returned payout goes back to the club's balance; on an automatic schedule Stripe resends it "at the next scheduled payout interval" once the club fixes its bank details — `topics/gaps-CLUBMONEY.md#stripe-sends-a-returned-automatic-payout-again-at-the-next-scheduled-payout-once-the-details-are-fixed`; [ABSENT] a resend of a failed manual payout — `topics/gaps-CLUBMONEY.md#on-manual-payouts-nothing-says-stripe-sends-it-again`.
- **R-CLUBMONEY-8, -20.** [DOCS] Stripe writes to the club's own users, each picking their notices; Raketa cannot customise those emails, its admins get capability warnings — `topics/gaps-CLUBMONEY.md#stripe-writes-to-the-clubs-own-account-users-directly`, `topics/gaps-CLUBMONEY.md#raketa-cannot-rebrand-or-redirect-a-full-dashboard-clubs-requirement-emails`; [ABSENT] which club user receives them.
- **R-CLUBMONEY-25.** [DOCS] Link full-Dashboard accounts to dashboard.stripe.com; login links are Express-only — `topics/gaps-CLUBMONEY.md#a-full-dashboard-club-signs-in-at-dashboardstripecom-login-links-exist-only-for-express`.
- **R-CLUBMONEY-13.** [DOCS] The fee is on the charge's balance transaction, often null at capture and ready on `charge.updated` — `topics/gaps-CLUBMONEY.md#the-fee-is-on-the-charges-balance-transaction-which-may-arrive-after-the-capture`.
- **R-CLUBMONEY-24.** [DOCS] Stripe itemises only automatic payouts; a platform-made payout it "can't identify" — `topics/gaps-CLUBMONEY.md#stripe-lists-a-payouts-charges-only-for-automatic-payouts`; status quo: Przelewy24 opens each payout's transactions and refunds — `topics/gaps-CLUBMONEY.md#przelewy24-lists-each-payout-packages-transactions-and-the-refunds-taken-off-it-status-quo`.
- **R-CLUBMONEY-19.** [DOCS] Above the available balance: `balance_insufficient`; platform payouts on a full Dashboard need platform controls (on for new accounts) — `topics/gaps-CLUBMONEY.md#a-platform-may-pay-out-a-full-dashboard-account-only-through-platform-controls-which-new-accounts-have`; [ABSENT] a platform payout while on the automatic schedule.
- **R-CLUBMONEY-2.** [DOCS] A refund shortly after the charge is a reversal with no fee withheld, and a partial refund can be a partial reversal — `topics/gaps-CLUBMONEY.md#a-partial-refund-can-be-a-partial-reversal`; [ABSENT] the window and the fee on a partial reversal.
- **R-CLUBMONEY-14, -15, -17.** [DOCS] Status quo: Przelewy24 and Tpay release each payment by the end of the next business day; P24 pays on demand, on a schedule or at 1000 zł, Tpay daily — `topics/gaps-CLUBMONEY.md#przelewy24-available-by-the-end-of-the-next-business-day-paid-out-on-demand-on-a-schedule-or-at-1000-zł`, `topics/gaps-CLUBMONEY.md#tpay-available-by-the-end-of-the-next-business-day-paid-out-automatically-every-day-arrives-within-3-business-days`; all three refuse a refund above the balance — `topics/gaps-CLUBMONEY.md#a-refund-larger-than-the-balance-is-refused-by-all-three`.
- **R-CLUBMONEY-5, -8.** [DOCS] Tpay and Przelewy24 take no payments before verification and block an account with outdated documents — `topics/gaps-CLUBMONEY.md#przelewy24-the-contract-starts-only-after-verification-later-requests-come-by-email-outdated-documents-block-the-account`; [ABSENT] their and Playtomic Manager's screens meanwhile.
- **R-CLUBMONEY-26.** [DOCS]/[POLICY] Status quo: the operator emails a payment confirmation, the club an SMS or in-app booking; an invoice only on request — `topics/gaps-CLUBMONEY.md#the-payment-operator-emails-the-payer-a-confirmation`, `topics/gaps-CLUBMONEY.md#an-invoice-on-request-by-email-with-proof-of-payment`; [ABSENT] how often organisers want one company invoice, and a KIS ruling on Stripe Connect — `topics/gaps-CLUBMONEY.md#not-found-a-tax-ruling-on-the-cash-register-exemption-for-sales-taken-by-stripe-connect`.

Still open from the earlier list: R-CLUBMONEY-4, -6, -7 Stripe's onboarding links; R-CLUBMONEY-5 the `charges_enabled`/`payouts_enabled` fields.
