# Gaps, payments pass — round 03 (PAY and CLUBMONEY market gaps)

Answers to the fourteen market gaps handed to this round (ten PAY lines and four CLUBMONEY lines), read 2026-10-20.
Every gap had been tried before; earlier answers are cited by anchor, not repeated. New sources this round: Playtomic's
two help centres read whole (Zendesk API, 254 articles) and its Legal Conditions; Visa Business News and Visa
Acceptance; Apple's and Stripe's Apple Pay pages; Przelewy24's and Tpay's terms read whole; Eureka's own search API
(29 new phrases); Kraków's city sports board's contract lists; the Rzecznik Finansowy, UOKiK, a German Federal Court
ruling and a UK Ombudsman decision; press for NBP figures nbp.pl will not serve to a bot. Nothing here is `[MEASURED]`.

| Gap | Rule | Now |
|---|---|---|
| A Kraków club's desk cost; IC+ for a small account | R-PAY-1 | *not found*. Only a city board's PayU contract ceilings exist; Stripe still names no threshold |
| Apple Pay device token failing a later charge | R-PAY-6 | **answered in part**: how and why it fails, and Visa's planned decline, are documented; no rate |
| What an internet address proves in a Polish dispute | R-PAY-11 | **answered in part**: in Polish law, a record of use alone does not prove consent; no source names the address |
| The decline code for a card blocked online | R-PAY-17 | *not found* for Polish banks; Visa's rule on code 57 is found |
| How many Polish cards change network | R-PAY-26, -27 | **answered in part**: a net swing of about 3 million cards to Visa in 3¼ years (press, citing NBP) |
| Statement name at mBank, ING, Pekao, Erste | R-PAY-34 | *not found*; the networks' name-and-logo schemes are found |
| How soon a bank app drops a released hold | R-PAY-2, -34, -52 | *not found* |
| How often banks ask on a charge without the player, and how fast she answers | R-PAY-39, -49 | *not found* |
| A tax ruling on one court-hour paid by several people | R-PAY-40 | **answered in part**: the two closest rulings are found; neither has several consumers sharing one service |
| Keeping Stripe's fee from a personal EU card's refund | R-PAY-13, -41 | *not found*: no authority has ruled; one foreign court's test is found |
| A returned payout at Przelewy24 and Tpay | R-CLUBMONEY-20 | **answered in part**: neither re-sends one by itself, by its terms |
| Playtomic's open matches when a club's Stripe is restricted | R-CLUBMONEY-9 | *not found* |
| Playtomic when a refund fails after it showed | R-CLUBMONEY-33 | **answered in part**: a closed card or account is the player's problem, by its terms |
| How many Kraków clubs have Przelewy24 pay out daily | R-CLUBMONEY-14, -15 | *not found* |

---

### R-PAY-1 · What a named Kraków club pays at its desk, and whether a small club can get Stripe's IC+ or volume pricing

**Answer:** still *not found* on both counts. The one named Kraków sports body whose payment contracts are public
uses PayU for online race entries, and its lists show yearly ceilings, never a rate. Stripe still publishes no
threshold. Third-party figures contradict each other.

- Carried: PKO BP 0,55 % a card payment, PolCard 0,59 % + 4 gr after a free year, SumUp 1,49 %, and the EU cap on
  interchange (`gaps-PAY.md#what-a-desk-terminal-costs-a-polish-club-per-card-payment`). Custom pricing is arranged
  through sales, "available for businesses with large payments volume", and no Kraków club was found on Stripe
  (`gaps-S-01A-hold.md#no-kraków-club-was-found-taking-card-payments-through-stripe-today`,
  `gaps-S-01A-hold.md#negotiated-pricing-ic-among-it-is-arranged-through-sales-for-large-volumes`).
- **[DOCS]** Zarząd Infrastruktury Sportowej w Krakowie (ZIS) is the City of Kraków's sports-infrastructure board. Its
  contract lists for 2020 to Q1 2026 name one payment provider, PayU S.A., "Udostępnienie systemu płatności online na
  potrzeby obsługi i wpłat na imprezy biegowe organizowane przez Zarząd Infrastruktury Sportowej".
  - Yearly ceilings: 30 000 zł (2020–21), 18 000 zł raised to 28 000 zł (2021–22), 50 000 zł raised to 55 000 zł
    (2022–23), 53 000 zł (2023–24).
  - No card terminal, acquirer (eService, PolCard/Fiserv, Elavon, Worldline) or court-booking system appears in any of
    the nine lists read; the Q1 2026 list holds no payment contract.
  - Sources: [BIP Kraków, ZIS wykaz umów 2020](https://bip.krakow.pl/zalaczniki/dokumenty/n/294750/karta),
    [2021](https://bip.krakow.pl/zalaczniki/dokumenty/n/322815/karta),
    [2022](https://bip.krakow.pl/zalaczniki/dokumenty/n/371195/karta),
    [2023](https://bip.krakow.pl/zalaczniki/dokumenty/n/445125/karta),
    [Q1 2026](https://bip.krakow.pl/zalaczniki/dokumenty/n/665152/karta) — read 2026-10-20.
- **[ABSENT]** A rate any named Kraków club or city venue pays at its desk. Looked in the ZIS lists above and in a
  search for KSOS's contracts (none published in the results). Carried: no club, tenis4U or kluby.org page states one.
  — read 2026-10-20
- **[ABSENT]** A Stripe page naming a volume above which IC+ or volume pricing is offered, or saying that a small
  connected account can get it. Looked again: the Poland pricing page (carried), the pricing policy, and a search of
  support.stripe.com. — read 2026-10-20
- *opinion:* third-party sites put Stripe's negotiating point at "$100K+/mo"
  ([toolradar](https://toolradar.com/tools/stripe/pricing)) or "around $1M a month"
  ([eightx](https://eightx.co/blog/what-is-interchange-fee-ecommerce)). They disagree, and neither is Stripe's word.
- *Reading:* Bonarka Arena's whole weekday padel offer is 4 courts from 17:00 to 22:00, or 100 court-hours a week at
  160 zł. Sold out, that is about 69 000 zł a month, well below either opinion. A Raketa club stays on 1,5 % + 1 zł a
  share unless Stripe says otherwise.
- What would answer it: a club's own terminal contract, which is private, or Stripe sales' answer for one named club.

---

### R-PAY-6 · How often an Apple Pay device token fails a later charge after the player changes phones

**Answer:** answered in part.
- How and why it fails is documented, and Stripe says it "can cause failures" for later charges made without the player.
- Visa has announced that it will decline such charges on device tokens. Its date is now "delayed until further notice".
- Apple says its merchant token cannot be used for an unscheduled card on file, which is Raketa's case.
- No source publishes how often it happens. Stripe's own data can measure it once Raketa is live.

- Carried: Stripe's sentence on device tokens failing later charges, and Apple's limits on merchant tokens
  (`stripe-saving-cards.md`, section 4 and Pitfall 5;
  `gaps-PAY.md#apples-merchant-tokens-are-not-for-an-unscheduled-card-on-file`).
- **[DOCS]** Stripe: "By default, Apple Pay creates a Device Primary Account Number (DPAN), which is tied to a specific
  device. If a customer replaces their device or removes the card from it, the DPAN might no longer work. This doesn't
  affect one-time customer-initiated transactions (CIT), but it can cause failures for future merchant-initiated
  transactions (MIT)." For Sigma users, "the `charges` table contains a `card_token_type` enum field to indicate the
  charge is using an `mpan` or `dpan` card". [Stripe: Apple Pay merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens)
  — read 2026-10-20
- **[DOCS]** Apple: DPANs "are specific and unique to the Apple device they reside on". MPANs are "not dependent on the
  continued use of a single device", and "MPANs are unaffected if the underlying card is reissued". No date of change
  is printed. Network support is stated "As of January 2026". [Apple Pay for partners: Merchant tokens](https://applepaypartners.apple.com/merchants/features/merchant-tokens-mpans)
  — read 2026-10-20
- **[DOCS]** Apple's security overview says the Device Account Number "is stored in the Secure Element", and "is never
  stored on Apple servers, and is never backed up to iCloud". Erasing a phone remotely "also removes the ability to pay
  with the cards", and they "will be suspended from Apple Pay by your bank", even if the phone is offline.
  [Apple: Apple Pay security and privacy overview](https://support.apple.com/en-us/101554) — read 2026-10-20
- **[DOCS]** Visa Business News AI12301 (22 September 2022, "Global | Acquirers, Issuers, Processors"):
  - "Standing instruction MITs on device tokens provisioned after 28 February 2024 will be declined."
  - "Visa expects that such device token usage for standing instruction MITs will reduce over time by natural attrition
    as device tokens are deactivated or expire."
  - "Visa reserves the right to block all standing instruction MITs on device tokens at a future date."
  - [Visa: Restrictions on Standing Instruction MITs](https://usa.visa.com/content/dam/VCOM/regional/na/us/support-legal/documents/restrictions-on-standing-instruction-mits.pdf) — read 2026-10-20
- **[DOCS]** Visa Acceptance knowledge article KA-04318, "Delay of Changes to Merchant Initiated Transactions (MIT) on
  Apple Pay Tokens" (version 1.4, last modified 10/07/2026):
  - Standing-instruction use cases are "recurring, installments, or unscheduled credential on file token usages".
  - The restriction, last set for 30 July 2025, "has been delayed until further notice" (Visa Business News AI15042,
    20 February 2025).
  - Visa "may announce a new comply-by date in the future".
  - Apple's recurring (merchant) token is recommended for these uses.
  - [Visa Acceptance: KA-04318](https://support.visaacceptance.com/knowledgebase/knowledgearticle/?code=KA-04318) — read 2026-10-20
- **[POLICY]** Playtomic charges a saved card automatically at a membership's renewal, but "If you paid with another
  method (such as Apple Pay, Google Pay …), renewals will need to be completed manually"
  ([player help](https://playerhelp.playtomic.com/hc/en-gb/articles/19831425477649)). For split payments, though, "Apple
  Pay and Google Pay are supported and count as a CoF guarantee". If that later charge fails it "will try charging any
  other card the booking owner has saved", then records a debt that blocks new bookings
  ([club help](https://helpmanager.playtomic.com/hc/en-gb/articles/46647891110673),
  [player help](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457)). — read 2026-10-20
- **[ABSENT]** How often a device token fails a later charge after a phone change, in Poland or anywhere. Looked in
  Apple's and Stripe's pages above, Visa's two notices, WWDC material found by search, the token-lifecycle pages of
  gateways (J.P. Morgan, Gr4vy), and processor blogs (ACI, Spreedly, Hyperswitch). None gives a rate. — read 2026-10-20
- *Reading:* a share charged on the card Nerea saved through Apple Pay is, in Visa's words, an unscheduled
  credential-on-file charge on a device token, the use Visa has said it will decline (on hold). Apple's merchant token,
  which Visa points to, is not offered for that use. So it can fail when Nerea changes phones, and every Visa card saved
  through Apple Pay could fail if Visa sets a new date. Playtomic charges wallet tokens later only with a fallback.
- What would answer it: on Raketa's live account, Sigma's `card_token_type = 'dpan'` against each charge's outcome, per
  month, by brand.

---

### R-PAY-11 · What an internet address proves in a card dispute, by Polish guidance

**Answer:** answered in part.
- Polish law, its Supreme Court, the Financial Ombudsman and UOKiK all say a recorded, authenticated use of a card does
  not by itself prove that the payer agreed to the payment. An internet address is one such record.
- None of them names the address. All of them deal with a payer and her own bank, not with a shop's chargeback, which
  runs on the card schemes' rules (carried).

- Carried: chargebacks follow the schemes, not Polish statute; Stripe weighs the address only under Visa's Compelling
  Evidence 3.0 (`gaps-PAY.md#card-disputes-in-poland-run-on-the-card-schemes-rules`,
  `gaps-PAY.md#where-an-internet-address-counts-in-a-dispute-and-where-it-does-not`).
- **[LAW]** Art. 45 ust. 1–2 UUP, as quoted by the Financial Ombudsman's office:
  - the provider bears "ciężar udowodnienia, że transakcja płatnicza była autoryzowana przez użytkownika";
  - "wykazanie przez dostawcę zarejestrowanego użycia instrumentu płatniczego nie jest wystarczające do udowodnienia,
    że transakcja płatnicza została przez użytkownika autoryzowana".
  - It cites Sąd Najwyższy, 18.01.2018, V CSK 141/17: a payment made with the payer's instrument "ale bez jego zgody" is
    not authorised.
  - Slides 29–31 headline "AUTORYZACJA TO NIE UWIERZYTELNIENIE".
  - [Rzecznik Finansowy: Nieautoryzowane transakcje – co zrobić, by odzyskać utracone pieniądze? (webinar, 7.12.2023)](https://rf.gov.pl/wp-content/uploads/2024/04/Transakcje-nieautoryzowane-7_12-2023.pdf) — read 2026-10-20
- **[POLICY]** UOKiK, 10.09.2026: commitment decisions against Alior Bank, mBank, BNP Paribas and Bank Millennium.
  "Authorisation and authentication are not the same": "the mere fact that a card was used correctly, a code was entered
  or a transaction was approved in an app … does not in itself establish that the consumer knowingly consented to the
  transaction". Ten more proceedings are open. Logs, devices and internet addresses are not mentioned.
  [UOKiK: Four banks change their practices](https://uokik.gov.pl/en/unauthorised-payment-transactions-four-banks-change-their-practices-following-decisions-by-the-president-of-uokik)
  — read 2026-10-20
- **[ABSENT]** Any Polish court, ombudsman, KNF, UOKiK or bank text saying what an internet address proves in a card
  dispute. Searched in Polish, using "adres IP" with "transakcja nieautoryzowana", "dowód" and "zarejestrowanego użycia
  instrumentu płatniczego", across UOKiK's two sites, rf.gov.pl, SAOS and Lege Artis case notes. — read 2026-10-20
- *Reading:* a Polish player who says "I never agreed to this share" is on the side Polish law favours. Raketa's
  record of her address, by itself, is the kind of technical record that law calls not enough. What carries weight is
  the agreement itself: the terms she accepted, when, and on which screen. With the card network, CE 3.0 helps only if
  the same card paid the same club twice before, 120–364 days earlier.

---

### R-PAY-17 · Which decline reason a Polish bank returns for a card whose internet limit is 0 zł, or that is blocked online

**Answer:** *not found* for any Polish bank. What Visa's rules say about the likeliest code, 57, is now found: it
belongs to the codes an issuer "will never approve", so a retry is pointless.

- Carried: Stripe's codes, and the raw codes 57, 61, 62 and 65
  (`gaps-PAY.md#what-a-declined-setup-hands-back`).
- **[DOCS]** The UK Financial Ombudsman, deciding a complaint against PaySend PLC (DRN-6268987, 14 April 2026), quotes
  Visa's Core Rules §7.3.6.3, "Use of Authorization Response Codes": under "Decline Response Codes Use" there is "a
  list of codes relating to transaction types which the card issuer will never approve. Code 57 appears in this list as:
  '57 (Transaction not permitted to cardholder)'". So "the decline would have happened automatically, without Bank A
  needing to manually review or record it". [Financial Ombudsman: DRN-6268987](https://www.financial-ombudsman.org.uk/decision/DRN-6268987.pdf)
  — read 2026-10-20
- **[DOCS]** Adyen maps "57: Transaction not permitted to issuer/cardholder" and "57: Transaction not allowed for this
  merchant" to refusal 23, *Transaction Not Permitted*, and "62: Restricted Card" to 25. Its refusal *Not supported*
  reads "The shopper's bank does not support or does not allow this type of transaction". No entry names a card that
  is blocked online. [Adyen: Refusal reasons](https://docs.adyen.com/development-resources/refusal-reasons) — read 2026-10-20
- **[ABSENT]** Which code PKO BP, mBank, ING, Pekao, Erste, Millennium or any Polish acquirer returns for an internet
  limit of 0 zł or a card blocked online. Looked in Citi Handlowy's declined-transaction guide for business cards
  (reasons without codes, none about online use:
  [Citi Handlowy](https://www.citibank.pl/poland/citidirect/polish/pdf/Odrzucona-transakcja-sposoby-postepowania-dla-posiadaczy-kart-PL.pdf)),
  in Polish searches for "transakcje internetowe" with "kod odmowy" and "57", and in the eService, PayU, Przelewy24 and
  Paynow documentation found by search. — read 2026-10-20
- *Reading:* if a Polish bank answers 57 for a card that is blocked online, Visa's rules class it as never approvable.
  Asking again cannot succeed until the player changes the setting in her bank's app. If it answers 05 or 61, the
  shop cannot tell a limit from any other refusal. A message that names the bank-app setting as one likely cause is
  the most it can say.

---

### R-PAY-26 / R-PAY-27 · How many Polish cards change network in a year

**Answer:** answered in part, as a floor. Over 3¼ years, about 3 million Polish cards moved net from Mastercard to
Visa. NBP's figures come through the press, because nbp.pl refuses an automated read. That is roughly 0,9 million a
year, or 2 % of all cards. It is a net swing, not a count of cards that changed network. PKO BP's switch is still
known only from the press.

- Carried: end of Q3 2022, Visa 53,3 % and Mastercard 46,5 % of cards issued in Poland (NBP, via a search extract);
  PKO BP's renewals moving from Mastercard to Visa (press); Maestro ending by 2027
  (`gaps-S-01A-hold.md#cards-issued-in-poland-are-almost-all-visa-or-mastercard`,
  `gaps-PAY.md#polish-cards-do-move-between-networks`).
- **[DOCS]** Telepolis (9 May 2026), on NBP's Q4 2025 card statistics: 46,7 million active payment cards at the end of
  December 2025, Visa "59,8 proc.", Mastercard "40,1 proc.". [Telepolis: Polacy rezygnują nie tylko z gotówki](https://www.telepolis.pl/fintech/cashless/polska-platnosci-karty-platnicze)
  — read 2026-10-20 (press, citing NBP; [NBP's Q3 2025 report](https://nbp.pl/wp-content/uploads/2026/01/Informacja-o-kartach-platniczych_2025-Q3.pdf)
  answered with a bot check, both through curl and through the fetch tool)
- *Reading (arithmetic):*
  - Visa's share rose 6,5 points between the end of Q3 2022 and the end of 2025: 46,7 million × 6,5 % ≈ 3,0 million
    cards, over 3¼ years.
  - The swing also includes cards opened and closed, so it is not a count of changes. Some cards may have moved the
    other way too, which makes the real number of changes higher, not lower.
  - Each card that changes network at renewal gets a new number. For a card on file at Raketa, that is a card Stripe's
    updater may not follow (`gaps-PAY.md#automatic-card-updates-are-not-documented-for-polish-issuers`).
- **[ABSENT]** A published count of Polish cards that changed network in a year, and PKO BP's own confirmation of the
  switch. Searched pkobp.pl (its terms and fee tables surface; none mentions the change of network) and NBP. — read 2026-10-20

---

### R-PAY-34 · What mBank, ING, Pekao and Erste (formerly Santander) show in place of the club's statement name

**Answer:** *not found* for those four banks. Both card networks run schemes through which a bank may show a
merchant's brand name and logo in place of the raw statement name. PKO BP uses Visa's. A club that never enrols in
either is shown by its statement name.

- Carried: on a direct charge the player's statement shows the club's own descriptor, at most 22 characters. PKO BP
  shows a merchant's name and sometimes its logo
  (`gaps-PAY.md#the-statement-shows-the-clubs-descriptor`, `gaps-PAY.md#how-polish-banks-rename-the-line`).
- **[DOCS]** PKO BP's IKO and iPKO add "logotyp sklepu czy punktu usługowego i jego nazwę marketingową" to a card
  payment, "Na początek … dla wybranych sprzedawców". It is "wprowadzone wraz z firmą Visa". Holds are not mentioned.
  [Telepolis, 21 October 2024](https://www.telepolis.pl/tech/aplikacje/pko-bp-nowosc-aplikacja-iko-serwis-ipko)
  — read 2026-10-20 (press)
- **[DOCS]** Mastercard offers banks the merchant's name, logo and place of purchase through its company Ethoca.
  Merchants send logos "bez żadnych dodatkowych opłat, po wypełnieniu odpowiedniego formularza" at logo.ethoca.com. The
  stated problem: the merchant's name "może być niezrozumiała lub zamiast niej wyświetla się nazwa pośrednika
  przetwarzającego płatność". In Kantar's survey for Mastercard, "84% respondentów czasami nie jest w stanie
  zidentyfikować niektórych zakupów". No Polish bank is named as adopting it.
  [aleBank.pl, 1 February 2021](https://bank.pl/?p=357949), [Super Biznes, 4 February 2021](https://superbiz.se.pl/technologie/dziwne-opisy-transakcji-karta-w-bankowych-aplikacjach-klienci-domagaja-sie-wyjasnien-aa-zsuB-gdR6-KxmT.html)
  — read 2026-10-20 (press)
- **[ABSENT]** Whether mBank, ING, Pekao (PeoPay) or Erste uses Visa's or Mastercard's name-and-logo data, and what
  each shows for a merchant not enrolled. Searched each bank's help and news pages and the press. — read 2026-10-20
- *Reading:* a Kraków club that never enrols is shown by the descriptor Stripe sends. That makes the descriptor the
  one name Raketa controls, through the club's onboarding, and it should read as the club's own name, not Stripe's.

---

### R-PAY-2 / R-PAY-34 / R-PAY-52 · How soon each Polish bank's app drops a hold the club let go

**Answer:** still *not found*. No new bank page, forum thread or Reddit account gives a time.

- Carried, in full: mBank lifts a hold when the cancellation arrives and gives no time; ING keeps one at most
  8 days; Erste and Millennium may keep one 30 days; Visa's reversal rule; MATCHi's "within 24 hours"
  (`gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished`,
  `gaps-S-01A-hold.md#how-soon-each-polish-banks-app-drops-a-cancelled-hold-still-unpublished`).
- **[ABSENT]** This round searched again, in Polish, for a merchant's cancellation and the hold leaving, with mBank, ING,
  Pekao and Santander/Erste by name, Reddit and the banks' help pages. The only new page is ING's card terms, which
  repeat the 8 days ([ING](https://www.ing.pl/_fileserver/item/1123353/v8)). — read 2026-10-20
- What would answer it, unchanged: on a real card from each bank, a small live hold placed and cancelled at once, with
  the bank app watched and the minutes written down.

---

### R-PAY-39 / R-PAY-49 · How often Polish banks ask for their check on a charge made without the player, and how long players take to answer

**Answer:** still *not found*. Nothing newer than the figures already carried.

- Carried: France 2021, 4,35 % of e-commerce payments soft-declined with the payer present; EEA 2024, charges made
  without the payer were 22 % of remote card payments taken without the check; 87 % of Polish bank checks succeed;
  people open a push in a median 7 minutes on iPhone and 48 on Android (2016)
  (`gaps-PAY.md#how-often-issuers-ask-and-how-fast-people-answer`,
  `gaps-S-01B.md#how-often-polish-banks-ask-on-a-charge-made-without-the-player-still-not-found`).
- **[DOCS]** Checkout.com lists the likely causes when banks refuse a charge made without the cardholder and ask for
  their check (its code 20154): "The initial CIT to set up the MIT agreement was not authenticated with SCA
  (challenge)", or "The subsequent MITs were not flagged correctly". "Only customer-initiated transactions (CITs) are
  eligible for SCA retries". No rate is given. [Checkout.com: Manage SCA retries](https://www.checkout.com/docs/risk-management/3d-secure/automated-sca-soft-decline-retry)
  — read 2026-10-20
- **[ABSENT]** A Polish or EEA rate of `authentication_required` on charges made without the payer. Looked in a search
  for 2024–2026 studies, Checkout.com, Worldpay and Lloyds Cardnet bulletins. A newer time-to-open figure: Airship's
  2025 and 2026 push benchmarks report opt-in and open rates, not time to open
  ([Airship 2026](https://www.airship.com/mobile-app-push-notification-benchmarks-for-2026/)). — read 2026-10-20
- *Reading:* Checkout's causes put the weight on the moment the card is saved. A card whose saving went through the
  bank's check, and whose later charges are marked as made without the player, is the case banks are least likely to
  stop. What would answer the rate is unchanged: the decline codes and notice-open times on Raketa's own live account.

---

### R-PAY-40 · A tax ruling on one court-hour paid in several parts by several people, under the online-payment cash-register exemption

**Answer:** answered in part.
- No ruling covers several consumers each paying a part of one service.
- The two closest rulings, both found through Eureka's own search API, point the same way: what counts is that every
  part reaches the seller through a bank or payment operator, and that the records tie each part to its sale.
  1. A single service paid in several bank payments by several payers fitted the exemption.
  2. A payment operator collecting and paying out in bulk fitted it too.

- Carried: KIS, 30 September 2025, tennis courts sold online through an operator, inside the exemption
  (`gaps-PAY.md#the-closest-ruling-tennis-courts-booked-online-through-an-operator`); "Stripe Connect" has 0 rulings
  (`gaps-CLUBMONEY.md#not-found-a-tax-ruling-on-the-cash-register-exemption-for-sales-taken-by-stripe-connect`).
- **[DOCS]** IPTPP2/443-89/11-5/AW (10 August 2011), a care home run by a county:
  - The facts: "Zapłata za świadczoną usługę – pobyt w DPS składa się z kilku wpłat dokonywanych przez: ZUS (70%
    emerytury), ośrodek pomocy społecznej, mieszkańca", all "za pośrednictwem banku".
  - KIS: services to individuals must go through a cash register "za wyjątkiem usług, za które zapłata w całości
    następuje za pośrednictwem poczty lub banku na rachunek bankowy oraz z ewidencji i dowodów dokumentujących te
    transakcje jednoznacznie wynika, jakiej konkretnie transakcji zapłata dotyczy".
  - KIS: the cash register does not apply to a service "w części, w jakiej te czynności są opłacane przez inne podmioty
    niż osoby fizyczne nieprowadzące działalności gospodarczej".
  - [Eureka: informacja 121620](https://eureka.mf.gov.pl/informacje/podglad/121620) — read 2026-10-20
- **[DOCS]** 0114-KDIP1-3.4012.458.2026.2.AMA (24 August 2026), digital products paid through a payment operator, by
  card "w tym płatność odroczona/w ratach":
  - The facts: "środki w całości wpływają najpierw na konto operatora płatności (…), a następnie są wypłacane zbiorczo na
    rachunek bankowy Wnioskodawcy".
  - The applicant argued that collecting first and paying out in bulk "nie wpływa na spełnienie tego warunku, ponieważ
    każda transakcja pozostawia ślad i jest jednoznacznie identyfikowalna", given a transaction ID, the buyer's email,
    the amount, the date and the product.
  - KIS: "stanowisko prawidłowe".
  - [Eureka: informacja 706073](https://eureka.mf.gov.pl/informacje/podglad/706073) — read 2026-10-20
- **[ABSENT]** A ruling where several consumers each pay a part of one service. Eureka's API, full phrase in content,
  filtered to theses naming the cash register: "przez osobę trzecią", "w ratach", "w częściach", "płatności częściowe",
  "wynajmu kortów", "kortów tenisowych", "padel", "squash", "zrzutka", "wpłat od uczestników", "kilku przelewów",
  "kilku wpłat", "dwóch płatności", "Przelewy24", "Tpay", "bramki płatniczej", "każdy z uczestników",
  "współnabywców", "kilku nabywców", "kilka osób", "część ceny", "rezerwacji online", "obiektu sportowego" and six
  more. — read 2026-10-20
- *Reading:* Bonarka Arena's 160 zł court-hour, paid as four 40 zł shares, each by card through Stripe to the club's own
  account, matches the 2011 case: one service, several bank payments, each tied to the booking. It also matches the 2026
  case: an operator collects and pays out in bulk, and each payment stays traceable. The difference that no ruling
  covers is that every payer is a consumer. The wording asks only that the whole price comes through the bank and that
  the records tie each part to its sale. A lawyer or the club's own ruling settles it.

---

### R-PAY-13 / R-PAY-41 · Whether keeping Stripe's fee from a personal EU card's refund is a banned charge for using the card

**Answer:** still *not found*: no authority has ruled on an amount kept back from a refund. This round found the
nearest court test of what a "fee for using" a payment method is. It looks at what the fee objectively pays for.

- Carried: art. 37a ust. 3 UUP, art. 383¹ KC, the Commission's guidance, the options ranked by legal risk, and Kraków's
  2 % refund deduction (`gaps-S-01A-leave-fee.md#a-fee-for-using-a-personal-eu-card-is-banned-outright-other-cards-are-capped-at-cost`,
  `gaps-S-01A-leave-fee.md#the-options-ranked-by-legal-risk`,
  `gaps-S-01A-hold.md#no-authority-was-found-ruling-on-a-fee-kept-back-from-a-refund`).
- **[LAW]** Bundesgerichtshof, I ZR 203/19 (24 March 2021, *Flixbus*), on § 270a BGB, Germany's version of PSD2
  art. 62(4):
  - Headnote 2: an agreement making the payer pay when choosing "Sofortüberweisung" or "PayPal" does not breach § 270a
    "wenn das Entgelt allein für die Nutzung dieser Zahlungsmittel und nicht für eine damit zusammenhängende Nutzung
    einer Lastschrift, Überweisung oder Zahlungskarte vereinbart wird".
  - Rn. 32: the fee is paid "nicht für die Nutzung der Überweisung, sondern für die Einschaltung eines Dritten".
  - Rn. 51: "gerade nicht für die Nutzung einer Lastschrift oder einer Zahlungskarte".
  - Rn. 16: for cards the ban holds only "bei Zahlungsvorgängen mit Verbrauchern".
  - [BGH I ZR 203/19 (text)](https://gesetze.co/urteile/I_ZR_203-19), [LTO report](https://www.lto.de/recht/nachrichten/n/bgh-i-zr203-19-zusatz-gebuehren-entgelt-zahlung-paypal-sofortueberweisung) — read 2026-10-20
- **[ABSENT]** The EBA's only surcharging question in its Q&A tool (2019_4576, on currency-conversion margins) was
  rejected on 11/02/2022 without an answer. No Q&A on art. 62(4) and refunds was found.
  [EBA Q&A 2019_4576](https://www.eba.europa.eu/single-rule-book-qa/qna/view/publicId/2019_4576) — read 2026-10-20
- *Reading:* under the German court's test, a fee is a charge for using the card when what it objectively pays for is
  the card payment itself. The 1,60 zł Stripe kept on Ivan's 40 zł is Stripe's price for processing that card payment,
  and it varies with the card. That ties it to the card more closely than Flixbus's fee was tied to the bank transfer.
  This reading leans toward the ban on personal EU cards. It remains a foreign court on a different fact, and the
  question stays with the lawyer (spec O3).

---

### R-CLUBMONEY-20 · What Przelewy24 or Tpay do with a payout the bank sends back

**Answer:** answered in part. Neither Przelewy24 nor Tpay promises in its terms to send a returned payout again by
itself, or to tell the club.
- Przelewy24's terms book a returned payout back to the merchant's balance, and the merchant orders it again. This is
  written out for payouts in a foreign currency.
- Przelewy24 promises to contact the merchant only when the money comes back after the contract has ended.
- Tpay proves the bank account before the first payout, so a payout seldom bounces, and it makes the merchant prove
  any new account the same way.
- For both, a payout that fails because the merchant's details were wrong is the merchant's problem.

- Carried, the Stripe side: a returned automatic payout is retried at the next scheduled payout; nothing re-sends a
  manual one (`gaps-CLUBMONEY.md#stripe-sends-a-returned-automatic-payout-again-at-the-next-scheduled-payout-once-the-details-are-fixed`,
  `stripe-gaps-04.md`, *R-CLUBMONEY-20*). Playtomic: a bounced payout "is returned to us"; the club corrects its details
  and asks Customer Care to resend it (`competitor-club.md#a-payout-that-fails`).
- **[DOCS]** Przelewy24 OWU v2.0 (from 15 May 2026), § 8 ust. 10: no liability "za niedojście lub opóźnienie w realizacji
  przelewu środków na Rachunek Rozliczeniowy" once its bank has the order, nor "za skutki podania przez Akceptanta
  nieprawidłowych lub niekompletnych danych uniemożliwiających wykonanie przelewu bankowego".
  [Przelewy24 OWU v2.0](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf) — read 2026-10-20
- **[DOCS]** Same terms, § 15 ust. 8, after the contract ends: "Jeżeli środki zostaną zwrócone przez bank prowadzący
  Rachunek Rozliczeniowy, Przelewy24 będzie podejmować próby kontaktu z Akceptantem w celu poczynienia ustaleń co do
  wypłaty tych środków". (OWU's text reads "przed bank".) — read 2026-10-20
- **[DOCS]** Same terms, Annex 8 (currency conversion, run by PayPro), § 4 ust. 5–6:
  - A payout the merchant's bank refuses is recorded as "taki zwrot", and "Akceptant może ją ponownie próbować wypłacić".
  - "PayPro zwraca Akceptantowi jedynie taką kwotę jaką zwróci dostawca prowadzący Rachunek Rozliczeniowy", so any bank
    charges come off it.
  - The panel "ewidencjonuje kwoty zwrotów wypłat".
  - — read 2026-10-20
- **[DOCS]** Tpay OWU, § 3 ust. 6 and 9: the payout account is set by an "opłata aktywacyjna" paid from it, and its
  details "muszą być zgodne z danymi podanymi podczas rejestracji". Changing the account means "ponowne wykonanie
  procesu weryfikacji, co wiąże się z ponownym poniesieniem opłaty aktywacyjnej". § 10 ust. 3: Tpay is not liable for
  "niezrealizowane lub opóźnione transakcje płatnicze będące następstwem podania przez Akceptanta nieprawidłowych lub
  niekompletnych danych". Nothing in § 7 (payouts) covers a returned payout.
  [Tpay OWU](https://tpay.com/user/assets/files_for_download/owu.pdf) — read 2026-10-20
- **[ABSENT]** A Przelewy24 or Tpay help page on a returned payout, and whether either emails the merchant. Searched
  both help centres by search engine, the Allegro sellers' community and Shoper's guides. — read 2026-10-20
- *Reading:* in Kraków today, a club whose payout bounces finds the money back in its Przelewy24 balance and orders the
  payout again. It may never be told, beyond the payout's status in its panel. On Tpay the bank account was proven by
  a transfer from it, so a bounce is rare. Stripe behaves much the same for a manual payout. On an automatic schedule
  Stripe is better, because it retries by itself once the details are fixed.

---

### R-CLUBMONEY-9 · What Playtomic does with an open match still filling, and with bookings already made, when its club's Stripe account is restricted

**Answer:** still *not found*. Playtomic's help and terms say nothing about open matches or bookings once a club's
Stripe account is restricted. This round confirmed where the money sits: on Playtomic's newer model each player's
payment lands on the club's own Stripe account, so a restricted club account would stop those payments.

- Carried: Manager warns "Your payments are about to be interrupted" before Stripe stops the account; what follows is
  not written (`gaps-CLUBSETUP.md#a-warning-bar-and-a-pop-up-your-payments-are-about-to-be-interrupted`,
  `gaps-CLUBSETUP.md#playtomic-and-matchi-not-written`).
- **[POLICY]** On Playtomic's New Billing Model, "When a player books online, funds are immediately reflected in your
  Stripe Connected account", and "payments are now processed directly between the player and your club". Split
  payments use a temporary hold or a saved card, and "payments/refunds are visible in your Stripe Connected account".
  [Introducing Playtomic's New Billing Model](https://helpmanager.playtomic.com/hc/en-gb/articles/26436916409361)
  (updated 2026-10-19) — read 2026-10-20
- **[POLICY]** On the older Distribution Model, Playtomic pays the club twice a month; if "There's an issue with
  automatic payments … Playtomic's finance team will process your payment manually".
  [Payout Cycle for Clubs Using the Distribution Model](https://helpmanager.playtomic.com/hc/en-gb/articles/37355604106129)
  (updated 2026-10-19) — read 2026-10-20
- **[POLICY]** The Legal Conditions name the clubs as the providers of the services (§ 5) and say nothing about a
  club's payment account being restricted or suspended. [Playtomic Legal Conditions](https://playtomic.com/legal-conditions)
  — read 2026-10-20
- **[ABSENT]** What Playtomic does to an open match still filling, or to bookings already paid, when the club's Stripe
  account is restricted. Looked in all 160 club and 94 player help articles (titles and bodies searched for
  "restricted", "suspend", "interrupt", "KYC", "Stripe account") and in the Legal Conditions. — read 2026-10-20
- *Reading:* on the Distribution Model a restricted club account only stops the club's payout, which Playtomic then
  pays by hand, and players keep booking. On the New Billing Model, which is Raketa's shape, a restricted club account
  would stop players' payments and Manager warns in advance. What happens to matches already gathering is unwritten.

---

### R-CLUBMONEY-33 · What Playtomic does when a player's refund fails after it showed as issued

**Answer:** answered in part. Playtomic's terms put a refund that cannot reach a closed card or account on the player:
she must recover it through her own bank, and Playtomic is "not responsible". Nothing tells the player what happens
when a refund fails for any other reason after the app showed it, and no fallback to the wallet or a bank transfer is
offered.

- Carried: refunds go "only to the same payment method originally used" and Playtomic "cannot redirect refunds"
  (`competitor-newcomer.md#how-long-a-refund-takes`). Players complain the app shows a refund that never arrives
  (`complaints.md#refunds-are-slow-partial-or-never-arrive`). On the New Billing Model a refund comes off the club's next
  payout, which can go negative and be "withdrawn from your bank account"
  (`competitor-club.md#nbm-the-club-sells-and-is-paid-weekly-by-payment-date-before-the-game`).
- **[POLICY]** Legal Conditions, § 7 ("Refunds to original payment method. Bank account closure."):
  - when the original method is no longer available, "it is the User's responsibility to liaise with their bank or
    payment provider to recover the funds";
  - "Playtomic cannot redirect refunds to a different bank account or payment method";
  - "Playtomic shall not be responsible for any inability to complete a refund caused by the closure".
  - § 8: "Failed payments due to technical issues, expired cards, or insufficient funds do not automatically create a
    debt" and "may be handled directly by the corresponding club".
  - [Playtomic Legal Conditions](https://playtomic.com/legal-conditions) (no date printed) — read 2026-10-20
- **[POLICY]** Player help: "Playtomic processes the refund immediately, however, consider that it can take 2-15 business
  days to receive in your bank. This is determined by your own banks processes". Nothing on a refund that fails.
  [Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593)
  (updated 2026-09-10) — read 2026-10-20
- **[ABSENT]** What Playtomic does, or tells the player, when a card refund fails after showing as issued, for a reason
  other than a closed account. Looked in all 254 help articles (searched for "refund failed", "could not", "bounced",
  "haven't received") and in the Legal Conditions. — read 2026-10-20
- *Reading:* Playtomic tells the player nothing and sends her to her bank. Stripe documents that a card refund to a
  closed or expired card fails, and that the money returns to the seller's balance
  (`stripe-gaps-04.md`, *R-CLUBMONEY-33*, which measured four `expired_or_canceled_card` failures). Raketa can do better
  than the market only by noticing the failure and offering another way to repay.

---

### R-CLUBMONEY-14 / R-CLUBMONEY-15 · How many Kraków clubs set Przelewy24 to pay out daily rather than once 1000 zł has built up

**Answer:** still *not found*. The setting lives in each club's own panel and is published nowhere.

- Carried: Przelewy24 pays out on demand, on a schedule, or by default once 1000 zł has built up; Tpay pays out every
  day (`gaps-CLUBMONEY.md#przelewy24-available-by-the-end-of-the-next-business-day-paid-out-on-demand-on-a-schedule-or-at-1000-zł`,
  `gaps-CLUBMONEY.md#tpay-available-by-the-end-of-the-next-business-day-paid-out-automatically-every-day-arrives-within-3-business-days`).
- **[DOCS]** The OWU v2.0 text read whole this round confirms § 10 ust. 7–8 unchanged; Tpay's § 7 ust. 2–3 allows a
  daily payout above a minimum Tpay sets, or a schedule or threshold the merchant sets.
  [Przelewy24 OWU v2.0](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf),
  [Tpay OWU](https://tpay.com/user/assets/files_for_download/owu.pdf) — read 2026-10-20
- **[ABSENT]** Any count or survey of Kraków clubs' payout settings, or a statement from Przelewy24 or Tpay on what
  share of merchants keep the default. Searched Przelewy24's and Tpay's help by search engine, the Allegro sellers'
  community, Shoper's guides ("the shortest interval between two payouts is 1 day"), and the tenis4U and kluby.org
  pages already read. — read 2026-10-20
- *Reading:* 1000 zł is about six of Bonarka Arena's 160 zł court-hours. If it sold only a fifth of its 100 weekday
  padel court-hours, about 3 200 zł a week, it would cross 1000 zł every two or three days. Even on Przelewy24's
  default, a busy Kraków club is paid every few days. That makes "paid daily,
  after the game" slower than the status quo by the days between booking and game, not by the threshold.
  What would answer it: asking five Kraków clubs which setting they use (`questions.md`).
