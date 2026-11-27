# Gaps round — payments pass, market 01: FILL and LEAVE

Answers to the fourteen market gaps the payments pass on PRD #530 left open on FILL and LEAVE, read **2026-10-20**.
Gaps already answered in `topics/` are cited by anchor, not repeated. One `##` section per gap, every fact under a `###`
heading that names its rules. The sections are numbered across three files, each kept under the folder's size:

- **this file:** the terms, the banks' holds, refusals and notices (§1–3, §8, §10, §11);
- [`gaps-payments-01-law.md`](gaps-payments-01-law.md): art. 37a UUP and VAT on a refunded share (§12–13);
- [`gaps-payments-01-krakow.md`](gaps-payments-01-krakow.md): Kraków's courts and desks, and the rivals' screens (§4–7, §9, §14–15).

- **What was read.**
  - Help centres, terms and price lists.
  - The banks' own card terms and help pages.
  - Polish statutes from the Sejm's consolidated texts, and the Ministry of Finance's tax rulings (Eureka).
  - Visa's Core Rules of 18 April 2026.
  - Two field studies of phone notifications.
  - tenis4U's public endpoints and the code tenis4U and Playmore serve.
  - Playtomic's help centres, through the Zendesk API.
  - The run's code copy at `9ab0ea5b`, for what the player is shown.
- **What was measured.** Nothing on a device and no screenshot. The two tenis4U reads and Playmore's served strings are
  saved as text extracts under `shots/`:
  - [`gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt`](../shots/gaps-payments-01-tenis4u-krakow-padel-2026-10-20.txt);
  - [`gaps-payments-01-playmore-served-2026-10-20.txt`](../shots/gaps-payments-01-playmore-served-2026-10-20.txt).
- **Tags** are as everywhere in this folder. A *Reading:* line is not a source. Playmore's own figures come from notes in
  its shipped code: the company's own numbers, Playmore-wide, all sports, not audited.
- **Not reachable:** EUR-Lex and Curia served a bot check, so CJEU judgments are cited through rulings and secondary
  sources. YouTube refused kluby.org's help videos to scripted reads. Revolut's help answered 403, so it is quoted from
  a search extract.

## Where each gap stands

| § | Rules | Gap | Now |
|---|---|---|---|
| 1 | R-FILL-11, R-FILL-60 | What the terms say; is "when a game you said yes to fills" enough of a frequency? | **Answered:** the terms at `9ab0ea5b` name all four moments, and for unscheduled charges Visa asks for the event, not a frequency. Visa's checklist items the terms step lacks are listed |
| 2 | R-FILL-13, -15, -42, -44, -49, -54, -56, -59 | How soon five banks drop a cancelled hold | Partly: PKO 7 days and ING 8 (or 30) days in their own card terms, neither naming a seller's cancellation. The timing is `[ABSENT]` |
| 3 | the same | The name beside a pending hold | `[ABSENT]` for a card hold; one PKO BLIK hold row is quoted |
| 4 [krakow](gaps-payments-01-krakow.md) | R-FILL-19 | Bajada's and Fame Sport's outdoor courts; the desk and an outside booking | Partly: both sell outdoor courts into November (measured). Winter and the desk's practice are `[ABSENT]` |
| 5 [krakow](gaps-payments-01-krakow.md) | R-FILL-20 | Kraków players and partners | Partly: 91 % of Playmore bookings name no co-player. The expectation is `[ABSENT]` |
| 6 [krakow](gaps-payments-01-krakow.md) | R-FILL-21 | What a tenis4U or kluby.org booker receives on a move | Partly: tenis4U's Move has no notice flag, and kluby.org leaves notices to the club. What arrives is `[ABSENT]` |
| 7 [krakow](gaps-payments-01-krakow.md) | R-FILL-27 | Playtomic's screen for the fourth joiner | Partly: the match locks. The screen is `[ABSENT]`. Playmore shows "Komplet!" |
| 8 | R-FILL-36, R-FILL-61 | How often banks refuse or ask without the player | `[ABSENT]`. New from Visa: written notice and 7 days after such a refusal |
| 9 [krakow](gaps-payments-01-krakow.md) | R-FILL-53 | How fast a last weekday-evening court sells | Partly: 1 of 104 sold within 16 minutes (measured). The minutes are `[ABSENT]` |
| 10 | R-FILL-33, R-FILL-61 | How fast people open a payment-problem notice | Partly: most notices are seen within minutes, but only about 15–25 % of notices other than messages are opened |
| 11 | R-LEAVE-44 | A let-go hold or check, and the bank's alert | Partly: mBank keeps a card-registration hold 14 days, Visa wants zero-amount checks, and PKO alerts "od razu". The timing is `[ABSENT]` |
| 12 [law](gaps-payments-01-law.md) | R-LEAVE-6 | Art. 37a ust. 3 UUP and a fee kept back from a refund | `[ABSENT]`. The nearest ruling, BGH *Flixbus*, points against keeping it |
| 13 [law](gaps-payments-01-law.md) | R-LEAVE-6, R-LEAVE-41 | VAT and invoices on a share taken, then refunded | **Answered** from the law and KIS rulings. Whether VAT is due on the part kept is for a tax adviser |
| 14 [krakow](gaps-payments-01-krakow.md) | R-LEAVE-21 | A late fourth, and resale of an hour handed back | `[ABSENT]`. Playmore says 88 % of its open games don't take place, and 24 % of its bookings are for the next day |
| 15 [krakow](gaps-payments-01-krakow.md) | R-LEAVE-51 | Does Playtomic or Playmore tell of a failed refund? | **Answered:** Playmore on the share's page ("Błąd zwrotu"), with no notice; Playtomic has nothing |

---

## 1. R-FILL-11, R-FILL-60: what the payment terms say at `9ab0ea5b`, and whether "when a game you said yes to fills" names the frequency

### R-FILL-11, R-FILL-60 · The terms in force since 2026-10-10 say held at the fill, checked when a hold wouldn't last, held four days before the cut-off, taken at the cut-off

- **[DOCS]** The words the player accepts on step 3, *Accept the terms*, version `2026-10-10`
  (`frontend_player/src/features/payments/components/paymentsCopy.ts:54`, `:62-75`; the backend holds the same
  version, `backend/app/modules/payments/domain/terms.py:20-25`): "When a game you said yes to fills, **the club it is
  played at** holds your share on your card — the court's price divided by the players. If that hold would not last
  until the club's cut-off, your card is checked when the game fills (your share held for a moment and let go), and
  your share is held four days before the cut-off. Your share is taken at the club's cut-off. Leave before the cut-off
  and nothing is taken. After the cut-off your seat is offered to others; if someone takes it, you get your share back
  less what was kept on your payment, and you see the exact sum before you leave. If a game is still missing a player
  at the cut-off, it is called off and nothing is taken." Read in the run's copy at `9ab0ea5b` — read 2026-10-20
- **[DOCS]** Around them: the bank step says "One-time 3-D Secure check — it lets the club hold and take your share
  later without you present." (`paymentsCopy.ts:152-153`); the sheet over the deck says "Save how you pay. Nothing is
  held until a game you said yes to fills, and nothing is taken before the club's cut-off." (`paymentsCopy.ts:196-200`).
  The words shown before 2026-10-10 ("charges your share at once") are kept as retired text, never shown again
  (`paymentsCopy.ts:82-94`) — read 2026-10-20
- **[DOCS]** A player who accepted older words is asked again before the next hold: a card whose terms are not in
  force is refused without asking Stripe (`terms.py:22-24`; `backend/app/modules/payments/application/seat_charges.py:422-432`) — read 2026-10-20
- *Reading:* this replaces `gaps-FILL.md#rakietas-terms-accepted-once-in-the-payment-setup-name-all-four` (2026-10-08),
  which quoted the retired words. All four moments of the mechanics are in the player's own terms: the hold at the
  fill, the check when a hold wouldn't last, the hold four days before the cut-off, and the take at the cut-off.

### R-FILL-11, R-FILL-60 · Stripe gives "unscheduled" as an example of the timing and frequency the terms must name

- **[DOCS]** "To charge customers when they're offline, include the following in your terms: … The anticipated timing
  and frequency of payments; for example, whether the charges are for scheduled installments, subscription payments,
  or unscheduled top-ups; How you determine the payment amount; Your cancellation policy for any subscription
  services." "Keep a record of each customer's agreement to your terms."
  [Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits) — read 2026-10-20
  - *Reading:* the example now on the page names a kind of timing (scheduled, subscription, unscheduled), not a count.
    The quote carried in `stripe-saving-cards.md#what-the-terms-must-say` (2026-10-19) stops before the example.

### R-FILL-11, R-FILL-60 · Visa: for unscheduled charges the terms name the event that prompts them, not a frequency

- **[POLICY]** Visa Core Rules, 18 April 2026, Table 5-20 (ID# 0029267, last updated Oct 2025): before storing a card
  for a future transaction the merchant "must obtain the Cardholder's express informed consent to an agreement that
  contains all of the following", among them "Timing and frequency of Transactions (does not apply if the Stored
  Credential will be used for Unscheduled Credential-on-File Transactions)" and "If the Stored Credential will be used
  for Unscheduled Credential-on-File Transactions, the event that will prompt the Transaction (for example: if the
  Cardholder's balance falls below a certain amount)". The same list asks for: a description of the goods or services;
  the total purchase price; "Cancellation and refund policies"; "The location of the Merchant Outlet"; "Address, email
  address, and phone number to use to contact the Merchant"; "The Account Number that will be used to make payment
  (last four digits only)"; "How the Cardholder will be notified of any changes to the agreement"; "Transaction amount
  or a description of how the Transaction amount will be determined"; "The Transaction Currency"; "How the Stored
  Credential will be used"; "The expiration date of the agreement, if applicable". And: "all requirements related to
  specific Transaction types must be clearly displayed at the time that the Cardholder gives their consent and must
  be displayed separately from the general purchase terms and conditions."
  [Visa Core Rules and Visa Product and Service Rules, 18 April 2026, pp. 458–459](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf) — read 2026-10-20
- **[POLICY]** Visa's definition: an Unscheduled Credential-on-File Transaction is "A Transaction using a Stored
  Credential for a fixed or variable amount that does not occur on a scheduled or regularly occurring Transaction
  Date, where the Cardholder has provided consent for the Merchant to initiate one or more future Transactions."
  (Glossary, ID# 0029548). Same source — read 2026-10-20
- **[POLICY]** Visa Europe, same table: "For Unscheduled Credential-on-File Transactions, the Merchant must provide
  notification to the Cardholder of any change in the Transaction amount or any other terms of the agreement at least
  2 working days before the change." The 2017 guide also asked for a notice two business days before an unscheduled
  charge when "More than six months have elapsed since the previous transaction"; in the April 2026 rules that
  six-month notice stands only for recurring transactions (Table 5-21).
  Same source, p. 460, p. 462; [Visa: Improving Authorization Management for Transactions with Stored Credentials (VBS 10.MAY.17), p. 15](https://www.commerce.uwo.ca/pdf/stored-credential-transaction-framework-vbs-10-may-17.pdf) (a university's copy of Visa's guide) — read 2026-10-20
- *Reading:* Rakieta's holds are unscheduled: each one follows an event (the fill, four days before the cut-off, the
  cut-off), and the terms name those events. Under Visa's rule, naming the event is what is asked, so "when a game you
  said yes to fills" meets the frequency item. The terms are shown on their own step (`paymentsCopy.ts:119-124`).
  Asking again for changed words before the next hold (`seat_charges.py:422-432`) is stricter than Visa's two working
  days' notice. Against Visa's checklist, the terms step does not show:
  - the card's last four digits: the step comes after the card, and nothing beside it names the card
    (`frontend_player/src/features/payments/components/SetupChecklist.tsx:70-89`, `:196-211`);
  - the currency;
  - the seller's location and contact details: the seller is "the club it is played at", unknown at saving;
  - how a change to the terms will be told.

### R-FILL-11 · From 18 April 2026 a Polish Visa card's bank must let the player stop unscheduled payments in its app

- **[POLICY]** Visa Core Rules §4.1.19.3, *Subscription Management Controls – AP and Europe Regions*: "effective 18
  April 2026 Europe Region (Belgium, Croatia, Czech Republic, France, Hungary, Italy, Luxembourg, Poland, …): An Issuer
  must provide a Cardholder, via an Issuer website and/or application (excluding telephone), with functionality to
  identify and, as applicable, deactivate or reactivate future payments for any of the following: Installment
  Transactions; Recurring Transactions; Unscheduled Credential-on-File Transactions". When declining for such a stop,
  the issuer uses "R1 (Stop all future payments)" or "R3 (Stop all merchants)", and must "Clearly inform … that the
  Cardholder may still be required to cancel a contractual relationship". Card portfolios up to 250,000 active cards
  are exempt (ID# 0031077–0031078, updated Apr 2026).
  [Visa Core Rules, 18 April 2026, pp. 248–249](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf) — read 2026-10-20
  - *Reading:* a player can now stop the clubs' holds from her bank's app. Rakieta then meets a decline at the hold, not
    a missing card. It looks like any other refusal at the fill or at the holding time.

---

## 2. R-FILL-13, R-FILL-15, R-FILL-42, R-FILL-44, R-FILL-49, R-FILL-54, R-FILL-56, R-FILL-59: how soon PKO BP, ING, Pekao, Erste and Millennium drop a hold the seller cancelled

Already answered, carried with their dates:

- mBank lifts a hold when the seller's cancellation arrives, otherwise after at most 14 days for online purchases
  (`gaps-FILL.md#mbank-lifts-a-hold-when-the-merchants-cancellation-arrives-at-most-14-days-online`, 2026-10-08).
- The five banks' hold terms: PKO BP 7 days (prepaid sheets), ING 8 days and its staff's "szybciej" on a seller's
  notice, Millennium 30 days, Erste 30 days "bez względu na to czy transakcja doszła do skutku", Pekao none found
  (`gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished`, 2026-10-10).
- Visa: a matched reversal tells the bank to lift the hold; an unmatched one leaves it 1 to 8 days. Stripe: "some
  banks update available balances instantly, while others take a bit longer". MATCHi: released "within 24 hours"
  (`gaps-S-01A-hold.md#visa-a-reversal-that-matches-tells-the-bank-to-lift-the-hold-one-that-doesnt-leaves-it-1-to-8-days`,
  `#stripe-some-banks-update-the-balance-at-once-others-later`, `#matchi-tells-players-a-cancelled-bookings-reserved-amount-is-released-within-24-hours-by-their-bank`, 2026-10-11).

### R-FILL-13, … · PKO BP's personal account and debit-card terms drop a hold on settlement or after 7 days, and name no seller's cancellation

- **[POLICY]** "§ 52. 1. PKO Bank Polski SA może ustanowić blokadę środków pieniężnych z tytułu nierozliczonych
  operacji dokonanych przy użyciu karty. 2. Blokada, o której mowa w ust. 1, jest anulowana w momencie obciążenia
  rachunku […] kwotą rozliczonej operacji lub po upływie 7 dni od dnia dokonania operacji, jeżeli PKO Bank Polski SA
  nie otrzyma potwierdzenia rozliczenia operacji. W przypadku nieotrzymania potwierdzenia rozliczenia operacji w
  terminie 7 dni, PKO Bank Polski SA może obciążyć Posiadacza rachunku kwotą operacji […] w terminie późniejszym".
  (The hold is cancelled when the account is debited with the settled amount, or after 7 days without a settlement;
  a later settlement can still debit the account.) *Regulamin rachunków bankowych i kart debetowych dla klientów
  indywidualnych w PKO Banku Polskim SA*, Dział IV rozdz. 5:
  - an undated 13-page version, p. 10: [pkobp.pl/api/public/c0dcae9e…](https://www.pkobp.pl/api/public/c0dcae9e-8d53-4e6d-9a7d-8f5877a7b76e.pdf);
  - a 17-page version whose annex reads "Obowiązuje od 9 stycznia 2017 r.", p. 12: [pkobp.pl/api/public/8dcfdbdf…](https://www.pkobp.pl/api/public/8dcfdbdf-5c05-4501-b9c2-6366735b8b01.pdf)
  — read 2026-10-20
- **[ABSENT]** A 2025 or 2026 version of these terms: the search found only these two and the 2015 booklet.
  Searched pkobp.pl through the search engine ("Regulamin rachunków bankowych i kart debetowych dla klientów
  indywidualnych" 2025/2026, "regulamin kart debetowych PKO BP 2026 blokada") — read 2026-10-20
- *Reading:* the earlier round had the 7 days only from PKO's prepaid-card sheets; the personal debit-card terms say
  the same, and they too name only settlement and the 7 days, never a seller's cancellation.

### R-FILL-13, … · ING's card terms in force from 24 August 2025: at most 8 calendar days, 30 where the networks say so, lifted on the debit or when no settlement comes

- **[POLICY]** "17. Blokady na Rachunku karty […] 2. W przypadku Transakcji, które powodują założenie blokady, blokada
  jest znoszona w momencie obciążenia Rachunku karty kwotą Transakcji […]. 3. Termin utrzymywania na rachunku blokady
  z tytułu dokonanej Transakcji jest obliczony w oparciu o czas, wynikający z przeciętnego terminu oczekiwania przez
  Bank na informację o Transakcjach do rozliczenia i wynosi maksymalnie 8 dni kalendarzowych od daty Transakcji […].
  W niektórych przypadkach, określonych przez organizacje płatnicze, maksymalny termin […] utrzymywania na rachunku
  blokady wynosi 30 dni kalendarzowych. Jeżeli Bank nie otrzyma z organizacji płatniczej informacji o Transakcjach
  rozliczenia, blokada zostaje zniesiona." (The length is set from the bank's average wait for the settlement; at most
  8 calendar days, 30 in cases the networks define; lifted when no settlement arrives.) *Komunikat ING Banku Śląskiego
  S.A. dla Użytkowników kart kredytowych — Informacja dodatkowa*, "Obowiązuje od 24.08.2025", p. 5.
  [ing.pl/_fileserver/item/1123353/v25](https://www.ing.pl/_fileserver/item/1123353/v25) — read 2026-10-20
- **[ABSENT]** ING's matching sheet for personal debit cards in force in 2025–2026, and any ING sentence on a seller's
  cancellation. Searched ing.pl's file server through the search engine ("Informacja dodatkowa" "kart debetowych"
  "Blokady na Rachunku"; "jak rozliczamy"), and ING's older account and payment-services terms (2014, 2016) — read 2026-10-20
- *Reading:* the card terms say "maksymalnie 8 dni" (was: prepaid business cards, 2021); like PKO's, they name no
  seller's cancellation. Only ING's staff on its forum (carried above) say a seller's notice can lift the hold sooner.

### R-FILL-13, … · Revolut: a payment the seller cancelled "may remain pending for some days", and the app shows the latest date it resolves

- **[POLICY]** "If a merchant informed you they cancelled a transaction, it may remain pending for some days, once fully
  processed, your money will be released to you. To check the maximum time for the transaction to resolve
  (complete/revert) tap on it in your transaction list. It can automatically resolve before the mentioned date."
  Read through the search engine's extract of [Revolut help: cancel or revert a pending payment](https://help.revolut.com/help/card-payments-withdrawals/cancel-or-revert-a-pending-payment/);
  a direct read answered 403 (WebFetch and curl) — read 2026-10-20
- **[POLICY]** Polish help: "Zwrot jest traktowany jako nowa transakcja, natomiast cofnięcie płatności skutkuje zmianą
  statusu transakcji pierwotnej." (A refund is a new transaction; a reversal changes the status of the original one.)
  Search-engine extract of [Revolut help (pl-PL): refund isn't showing on my statement](https://help.revolut.com/pl-PL/business/help/card-payments/refunds/refund-isn-t-showing-on-my-statement/) — read 2026-10-20
- *Reading:* not one of the five banks the gap names. It is the only card issuer found that states a time for a seller's
  cancellation, and its word is "some days", with a date shown per payment.

### R-FILL-13, … · Erste lists card holds and refused payments in the app's history since July 2021

- **[POLICY]** "Poza zaksięgowanymi transakcjami, na liście zobaczysz także blokady kartowe i płatności odrzucone."
  Transactions are sorted "po dacie wykonania, a nie – jak do tej pory – po dacie księgowania", with a new "filtr
  Status". [Erste (then Santander Bank Polska): nowa historia w Santander mobile, 12 lipca 2021](https://www.erste.pl/aktualnosci/aktualnosci-lista/nowa-historia-w-santander-mobile) — read 2026-10-20
- **[POLICY]** On a seller's cancellation Erste says only that the payer should get a paper: "przy anulowaniu
  autoryzacji w punkcie usługowo-handlowym powinieneś otrzymać stosowny dokument"; and "Usługodawca powinien przesłać
  transakcję do rozliczenia maksymalnie w ciągu 30 dni". [Erste: pytania i odpowiedzi — karty](https://www.erste.pl/klient-indywidualny/kontakt/pytania-i-odpowiedzi-karty?sr=1) — read 2026-10-20

### R-FILL-13, … · Pekao and Millennium: nothing new

- **[ABSENT]** Pekao: its personal-account terms (the copy on pzu.pl, 37 pp.) carry no card-hold length, as found
  before; its personal card terms and a help page on holds were not found. Searched "Banku Pekao" regulamin kart
  debetowych "blokada" "dni", pekao.com.pl pomoc "blokada środków" — read 2026-10-20.
  [Regulamin rachunków bankowych Banku Pekao S.A. dla osób fizycznych (pzu.pl copy)](https://www.pzu.pl/_fileserver/item/1524128)
- **[ABSENT]** Millennium: no FAQ or terms sentence on a cancelled hold beyond the carried 30 days. Searched
  bankmillennium.pl ("blokada" "zwrot" anulowana; regulamin kart debetowych 2026 "30 dni" anulowanie) — read 2026-10-20

### R-FILL-13, … · How soon each of the five banks drops a cancelled hold: still not published

- **[ABSENT]** None of PKO BP, ING, Pekao, Erste or Millennium states minutes, hours or days for a hold the seller
  cancelled; their terms name only settlement and a ceiling (7, 8, 30 and 30 days; Pekao none). No first-hand account
  at a named bank was found either: Allegro community threads ("anulowana płatność", 2020, ING named with no timing;
  "blokada w PKO", 16-09-2024, no timing; "Blokada BLIK", 02-12-2025, below), and searches of Reddit, wykop and
  forum.bankier.pl through the search engine ("blokada nie zniknęła po anulowaniu", "od razu zniknęła", "następnego
  dnia"). What would answer it is unchanged: on a real card from each bank, a small live hold placed and cancelled at
  once, with the bank app watched and the times written down — read 2026-10-20

---

## 3. R-FILL-13, R-FILL-15, R-FILL-42, R-FILL-44, R-FILL-49, R-FILL-54, R-FILL-56, R-FILL-59: what name each bank prints beside a pending hold

Already answered, carried: PKO BP marks a pending card payment "ikonę kłódki i oznaczenie Blokada"
(`gaps-POST.md#pko-lists-a-hold-as-blokada-in-the-account-history`, 2026-10-08); Visa wants the same merchant name on
the hold as on the payment, and a direct charge carries the club's descriptor
(`gaps-S-01A-hold.md#visa-requires-the-same-merchant-name-on-the-hold-as-on-the-payment`, 2026-10-11).

### R-FILL-13, … · At PKO BP a BLIK hold read "BLIK INTERNET: ALLEGRO.PL" with "Blokada Banku" (one buyer's account)

- **[COMPLAINT]** A buyer who paid 2 224,74 zł by BLIK on 28 November 2025 and returned part the same day saw a hold
  of "-1 949,00 PLN" with the lines "BLIK INTERNET: ALLEGRO.PL" and "Blokada Banku"; he writes "Dzwonilem do PKO BP,
  powiedzieli ze oni nie mają z tym nic wspólnego", and later "W banku powiedzieli ze ta forsa zostanie odblokowana
  w ciągu 7 dni kalendarzowych." [Allegro community: Blokada BLIK, posts of 02-12-2025](https://spolecznosc.allegro.pl/t5/dyskusje-kupuj%C4%85cych/blokada-blik/m-p/1122858) — read 2026-10-20
- *Reading:* a BLIK hold, not a card hold, and one person's screen. It shows a PKO hold row carrying the payee's name
  next to the word "Blokada"; whether a card hold's row does the same is not shown.

### R-FILL-13, … · The name beside a pending card hold: still not found for any of the five banks

- **[ABSENT]** No bank page, app-store text or screenshot read says what a pending card hold's row prints (the
  seller's name, the processor's, or none). Erste says only that holds are listed (§2); mBank's "Blokady i
  zawieszenia" and Moje ING's "transakcje oczekujące i blokady" are named without their rows described. Searched:
  "szczegóły blokady" "nazwa akceptanta"; "Moje ING" "blokady"; mBank "Blokady i zawieszenia" opis; IKO "Blokada"
  YouTube; "STRIPE" w historii konta; ING's 38-page app guide *#zdalnidopomocy* ([ing.pl/_fileserver/item/3jmgwqx](https://www.ing.pl/_fileserver/item/3jmgwqx)),
  whose *Historia* pages show no hold. What would answer it: the live hold in §2, with a screenshot of each bank app's
  row — read 2026-10-20

---

## 8. R-FILL-36, R-FILL-61: how often a Polish or EEA bank refuses, or asks for its check, on a payment made without the player

### R-FILL-36, R-FILL-61 · Still no published rate; the European Commission's PSD2 study has none either

- **[ABSENT]** The European Commission's PSD2 evaluation study, *A study on the application and impact of Directive
  (EU) 2015/2366 on Payment Services (PSD2)*, FISMA/2021/OP/0002 (2023), was read through for merchant-initiated
  payments and declines. It says only that SCA "has led to a decline in the authorisation of payments" (p. 90). It
  reports stakeholders calling the MIT exemption "unnecessary" (p. 131). It gives no rate of refusals or bank checks
  on payments made without the payer.
  [EC / ECRI copy](https://www.ecri.eu/sites/default/files/a-study-on-the-application-and-impact-of-directive-ev0423061enn.pdf) — read 2026-10-20
- **[ABSENT]** Also searched this round:
  - Visa's April 2026 rules: they set what happens after a decline, not how often one happens.
  - Recurly's published decline figures: global and US-led, card-on-file subscriptions, 14.4–15.9 % of payments by
    value declined in 2015 ([Digital Transactions, 11 July 2016](https://www.digitaltransactions.net/a-report-shows-how-credit-card-declines-eat-in-to-recurring-payments-revenue/)).
    No split by country or for the bank's check.
  - Vendor SCA guides (Saferpay, 2Checkout, Chargebee, Mastercard Gateway): each says the bank may ask, and none
    says how often.

  Read 2026-10-20.
- Carried:
  - EEA 2024: merchant-initiated payments were 22 % of remote card payments made without the bank's check
    (`gaps-S-01B.md#eea-2024-charges-made-without-the-payer-were-22-per-cent-of-remote-card-payments-taken-without-the-banks-check`, 2026-10-10).
  - Poland: about 87 % of the bank's checks succeed
    (`gaps-S-01B.md#when-a-polish-cards-bank-does-ask-about-87-per-cent-of-checks-succeed`, 2026-10-10).
  - France 2021: 4,35 % of payments soft-declined with the payer present (`gaps-PAY.md#how-often-issuers-ask-and-how-fast-people-answer`).
- What would answer it: the decline codes on Rakieta's own Stripe account once live, split by bank and by "asked for
  its check" against "refused".

### R-FILL-33, R-FILL-61 · Visa: after a refused payment made without the cardholder, she gets written notice and at least 7 days

- **[POLICY]** Visa Core Rules, Table 5-22 *Processing Requirements for Transactions Using Stored Credentials*, row
  *Authorization Request Declines*: "If an Authorization Request for a Merchant-initiated Transaction with a Stored
  Credential is declined, the Merchant must notify the Cardholder in writing and allow the Cardholder at least 7
  calendar days to pay by other means." (ID# 0029267, last updated Oct 2025; no region is named on the row.)
  [Visa Core Rules, 18 April 2026, p. 464](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf) — read 2026-10-20
- **[ABSENT]** Neither a Visa page nor any other source was found applying this row to a seat that is let go rather
  than a debt still owed. A web search for its wording found no processor or Visa guidance quoting it — read 2026-10-20
  - *Reading:* Rakieta writes to the player ("Fix your card by 19:30 to keep your seat", by email and notice,
    `backend/app/modules/notifications/application/telling.py:23`). It gives her 30 minutes, never past the cut-off,
    and then lets the seat go. Read literally, Visa's row asks for 7 days to pay another way. Whether letting the seat
    go, with nothing owed, meets the row is for Stripe's support or the acquirer.

---

## 10. R-FILL-33, R-FILL-61: how fast people open a payment-problem notice

### R-FILL-33, R-FILL-61 · Field studies: half of all notices seen within minutes, but other apps' notices rarely opened

- **[DOCS]** Pielot, Church and de Oliveira, *An In-Situ Study of Mobile Phone Notifications*, MobileHCI '14 (15
  Android users, one week): "The median time ranges from 3.5 min for messengers on weekends to 27.7 min for email on
  weekends." "half of the notifications were viewed within a few minutes, and that the majority were attended to
  within hour (email on weekends being the exception)". "When notifications arrived, the screen had been off in 69.2%
  of the cases." Notices were seen significantly faster with the phone on vibrate than on silent or ring.
  [Paper (author copy)](https://ic.unicamp.br/~oliveira/doc/MHCI2014_An-in-situ-study-of-mobile-phone-notifications.pdf) — read 2026-10-20
- **[DOCS]** Pielot, Vradi and Park, *Dismissed! A Detailed Exploration of How Mobile Phone Users Handle Push
  Notifications*, MobileHCI '18 (794,525 notices from 278 users): notices other than messages "rarely lead to a
  conversion (rates between ca. 15 and 25%)", where a conversion is opening the app from the notice. "NonSocial
  notifications tend to be dismissed quickly." Citing earlier work: a tapped notice was tapped "within a median time
  interval of 30 seconds" (Sahami et al.), and 20 participants "clicked on 60% of the notifications within 10 minutes"
  (Mehrotra et al.).
  [Paper](https://www.interruptions.net/literature/Pielot-MobileHCI18.pdf) — read 2026-10-20
- **[ABSENT]** A newer time-to-open figure from push vendors. Airship's 2026 benchmarks (data January–December 2025)
  give opt-in and direct-open rates and monthly sends, and no time to open.
  [Airship: Mobile App Push Notification Benchmarks for 2026](https://www.airship.com/mobile-app-push-notification-benchmarks-for-2026/) — read 2026-10-20
- Carried: Leanplum 2016, median time to open a marketing push of 7 minutes on iPhone and 48 on Android
  (`gaps-S-01B.md#people-open-a-push-in-about-7-minutes-on-an-iphone-and-48-on-android-2016-vendor-figure`). The phone
  gives the bank's check 10 minutes on an iPhone and 5 on Android (`stripe-gaps-02.md#r-fill-33-r-fill-61--the-phone-gives-the-banks-check-10-minutes-on-an-iphone-and-5-on-android`).
- *Reading:* a "Fix your card" notice is not a message from a person. The studies put most notices in front of the
  player within minutes. Notices from apps other than messengers lead to opening the app in only about one case in
  five, and those are dismissed fastest. So 30 minutes is about the time it takes people to see a notice; whether they
  act on it in that time is not shown.

---

## 11. R-LEAVE-44: how soon each bank's app drops a let-go hold or a card check, and whether a check alerts as a card payment

In this product a *check* is the player's full share (40,00 zł) held and let go at once
(`stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card`, 2026-10-19).
How soon a let-go hold leaves each bank's app is §2 above; nothing there differs for a check.

### R-LEAVE-44 · mBank: a small hold placed when a card is registered with a service expires after 14 days

- **[POLICY]** Under "Preautoryzacja - weryfikacja ważności konta oraz dostępnych środków w niektórych serwisach
  internetowych": "przy rejestrowaniu swojej karty płatniczej, serwisy przeprowadzają weryfikację ważności konta […]
  po pozytywnej autoryzacji zostaje założona blokada na niewielką kwotę […] która po upływie 14 dni wygasa" (the page
  names iTunes, Amazon and PayPal and an amount of one currency unit). A completed 3-D Secure payment is seen under
  "Produkty -> Karty -> Blokady". [mBank: płatności kartą na odległość](https://www.mbank.pl/indywidualny/karty/pytania-i-odpowiedzi/platnosci-karta-na-odleglosc/) — read 2026-10-20
- *Reading:* mBank shows a card check as a hold and, if nothing cancels it, keeps it 14 days, the same as any online
  hold (carried, §2). A check that is let go is a cancellation, which mBank says lifts the hold.

### R-LEAVE-44 · Visa wants a zero-amount account verification, not a small amount, to check a card being stored

- **[DOCS]** "Account verification messages are authorizations with a zero amount used by merchants to check the
  validity of a primary account number with issuers." "In a number of instances, however, merchants and acquirers are
  incorrectly using authorizations with low values instead of zero-amount account verifications." Acquirers must
  "Ensure that their merchants use account verification instead of authorizations for erroneous amounts when
  validating cardholder accounts. This includes the addition of an account number to the customer profile
  (credential-on-file) and periodic revalidation of stored credentials." Issuers "should return response code 85 (no
  reason to decline)". Global. [Visa Business News AI09481, *Proper Account Verification Message Processing
  Reminders*, 7 November 2019](https://bz.review.visa.com/content/dam/VCOM/global/support-legal/documents/account-verification-vbn.pdf) — read 2026-10-20
- Carried: Stripe, "Card networks may also restrict 1 USD authorizations you don't intend to capture"
  (`stripe-holds-and-capture.md#a-full-share-hold-let-go-at-once-the-networks-word-on-checking-a-card`, 2026-10-19).
- *Reading:* Visa's word is about checking a card when it is stored. It does not name a full-amount hold let go at
  once to check the money, which stays *not found* (`stripe-gaps-02.md#r-leave-44--a-full-share-hold-let-go-at-once-to-check-the-money`).

### R-LEAVE-44 · Stripe tells customers that saving a card may show a pending charge of about $1 that will disappear

- **[DOCS]** "Stripe may send a request to the issuing bank for either a $0, $1, or similar authorization" when
  storing a card; customers "may occasionally see an approximately $1 pending charge on their bank statement. This is a
  temporary authorization charge and it will disappear from their statement." No time is given.
  [Stripe support: unexpected $1 charge on customer's bank statement](https://support.stripe.com/questions/unexpected-1-charge-on-customers-bank-statement) — read 2026-10-20
- **[DOCS]** "The card information is verified when the card is saved, but it only verifies that the information is
  valid"; "it cannot check credit limits or account balances". [Stripe support: check if a card is valid without a
  charge](https://support.stripe.com/questions/check-if-a-card-is-valid-without-a-charge) — read 2026-10-20
- *Reading:* the player's payment setup can leave its own small pending line, apart from any full-share check.

### R-LEAVE-44 · PKO BP sends its card-payment alert "od razu po zdarzeniu", with no alert for a payment let go; mBank's SMS goes "W chwili wykonywania operacji"

- **[POLICY]** PKO BP: "Płatność kartą — SMS: tak (powyżej wskazanej kwoty), e-mail: tak, aplikacja mobilna: tak";
  the app and e-mail alerts go "od razu po zdarzeniu", SMS "od razu po zdarzeniu lub od 8:00 do 22:00"; the card rows
  have nothing for a cancelled payment or a refund (the account rows carry "Niezrealizowana transakcja"). Whether the
  card alert fires at the authorisation or at the booking is not said. [PKO BP: powiadomienia SMS, e-mail, push](https://www.pkobp.pl/klient-indywidualny/aplikacja-iko-ipko/powiadomienia-bank-sms-email-push) — read 2026-10-20
- **[POLICY]** mBank: "W chwili wykonywania operacji otrzymasz powiadomienie na numer telefonu zarejestrowany w
  mBanku", containing "jego typie, dacie i dokładnym czasie"; the app's push toggles include "operacje kartowe" and
  "niezrealizowane operacje". Nothing on holds, cancellations or refunds.
  [mBank: powiadomienia SMS](https://www.mbank.pl/indywidualny/uslugi/uslugi/powiadomienia-sms/),
  [mBank: powiadomienia push](https://www.mbank.pl/indywidualny/aplikacja-i-serwis/dodatkowe-uslugi/powiadomienia/) — read 2026-10-20
- **[POLICY]** Pekao: "Bank może powiadamiać o transakcjach kartą i operacjach z przewalutowaniem" (a news report
  citing pekao.com.pl). [gsmmaniak.pl, 10 lipca 2026](https://www.gsmmaniak.pl/1670117/pekao-klienci-ustawienia-powiadomienia/amp/) — read 2026-10-20

### R-LEAVE-44 · Whether a full-share check alerts as a card payment, and how soon it leaves: still not found

- **[ABSENT]** No bank says whether its card-payment alert fires on an authorisation that is let go at once, or on a
  zero-amount check; ING, Millennium and Erste publish no alert timing that was found. No first-hand account of a
  check's alert or its time to leave the app was found. Searched: "weryfikacja karty 0 zł blokada powiadomienie",
  "0,00 PLN" powiadomienie, "1,00 PLN" blokada dodanie karty, "1 zł" weryfikacja karty Uber Bolt, the five banks'
  notification pages, Allegro's community. What would answer it: the live check from §2 on a card from each bank with
  alerts on, noting whether an alert arrives, its words, and when the row leaves — read 2026-10-20
