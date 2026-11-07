# Gaps round — payments pass, market 01: the law (§12–13)

Part of the payments pass's market gaps round 01 on FILL and LEAVE (PRD #530), read **2026-10-20**. The index, the
sources and where each gap stands are in [`gaps-payments-01.md`](gaps-payments-01.md).

- **Statutes** are read from the Sejm's consolidated texts, and **tax rulings** from the Ministry of Finance's Eureka.
- **CJEU judgments:** EUR-Lex and Curia served a bot check, so they are cited through the rulings and secondary
  sources that quote them.
- **Advice still needed:** a tax adviser's or the lawyer's reading, wherever a line says so.

---

## 12. R-LEAVE-6: does art. 37a ust. 3 UUP reach a fee kept back from a refund after the cut-off?

Already answered: [`gaps-S-01A-leave-fee.md#a-fee-for-using-a-personal-eu-card-is-banned-outright-other-cards-are-capped-at-cost`](gaps-S-01A-leave-fee.md#a-fee-for-using-a-personal-eu-card-is-banned-outright-other-cards-are-capped-at-cost),
[`#a-cancelling-consumer-may-be-charged-only-the-costs-actually-incurred`](gaps-S-01A-leave-fee.md#a-cancelling-consumer-may-be-charged-only-the-costs-actually-incurred)
and [`#a-dated-sports-booking-has-no-statutory-withdrawal-right-the-leave-right-is-contractual`](gaps-S-01A-leave-fee.md#a-dated-sports-booking-has-no-statutory-withdrawal-right-the-leave-right-is-contractual)
(all 2026-10-10), [`gaps-S-01A-hold.md#no-authority-was-found-ruling-on-a-fee-kept-back-from-a-refund`](gaps-S-01A-hold.md#no-authority-was-found-ruling-on-a-fee-kept-back-from-a-refund)
(2026-10-11), and, for Stripe's terms, [`stripe-gaps-02.md#r-leave-6--keeping-stripes-fee-back-from-a-consumers-refund-under-the-surcharge-clause`](stripe-gaps-02.md#r-leave-6--keeping-stripes-fee-back-from-a-consumers-refund-under-the-surcharge-clause)
(2026-10-20). They are less than three months old and are carried, not repeated. This round tried sources not tried before.

### R-LEAVE-6 · The text in force bans a payee's charges "for using" capped cards, and says nothing about refunds

- **[LAW]** Art. 37a ust. 2 UUP: the provider does not stop the payee "żądania od płatnika opłaty, oferowania mu zniżki
  lub kierunkowania jego wyboru w inny sposób, tak aby skorzystał z określonego instrumentu płatniczego. Ewentualne
  opłaty pobierane z tego tytułu nie mogą przekraczać kosztów bezpośrednich ponoszonych przez odbiorcę z tytułu
  korzystania z określonego instrumentu płatniczego." In English: a payee may steer the payer by a fee or a discount, but
  any such fee may not exceed the payee's direct costs of that instrument.
- **[LAW]** Ust. 3: "Odbiorca nie pobiera opłat za korzystanie z instrumentów płatniczych, w przypadku których opłaty
  interchange są regulowane w przepisach rozdziału II rozporządzenia (UE) 2015/751". In English: the payee charges
  nothing for using a card whose interchange the EU caps.
  - The article names no refund, deduction or cancellation.
  - The consolidated text marks changes to art. 37a from **9 January 2027**, made by the act of 23 January 2026
    (Dz.U. 2026 poz. 340). Its footnotes tie that act to Regulation (EU) 2024/886 on instant payments. The amended
    wording was not read.
  - Source: [UUP, Dz.U. 2026 poz. 623, art. 37a](https://api.sejm.gov.pl/eli/acts/DU/2026/623/text.pdf), read 2026-10-20.
- *Reading:* R-LEAVE-6 keeps a different amount by card kind (1,60 zł on a personal EU card, 1,76 zł on a business
  card, 2,30 zł on a card from outside Europe). That links the deduction to the instrument used. A lawyer could read it
  as a charge "for using" the card, even though it is taken from a refund and not added at payment.

### R-LEAVE-6 · Germany's highest civil court separates a fee for an intermediary's service from a fee for using the instrument

- **[LAW]** BGH, I ZR 203/19 (*Flixbus*), 24 March 2021, Leitsatz 2: "Eine Vereinbarung, die den Schuldner bei Wahl der
  Zahlungsmittel "Sofortüberweisung" oder "PayPal" zur Zahlung eines Entgelts verpflichtet, verstößt nicht gegen § 270a
  BGB, wenn das Entgelt allein für die Nutzung dieser Zahlungsmittel und nicht für eine damit im Zusammenhang stehende
  Nutzung einer Lastschrift, Überweisung oder Zahlungskarte im Sinne von § 270a BGB vereinbart wird."
  - In English: a fee for choosing Sofort or PayPal does not breach Germany's surcharge ban (§ 270a BGB, its PSD2
    art. 62(4) rule) when the fee is only for using that service. It must not be for the underlying transfer, debit or
    card.
  - Source: [gesetze.co: BGH I ZR 203/19](https://gesetze.co/urteile/I_ZR_203-19), a decision database, read 2026-10-20.
- **[LAW]** The court's reason, as reported: the fee paid for "die Einschaltung eines Dienstleisters, der noch
  zusätzliche Leistungen übernehme, beispielsweise die Prüfung der Bonität" (bringing in a provider that does extra work,
  such as a credit check).
  - This is secondary reporting; the judgment's full text was not read.
  - Source: [beck-aktuell, 25 March 2021](https://www.beck-aktuell.de/heute-im-recht/rechtsprechung/bgh-gebuehr-fuer-zahlung-per-sofortueberweisung-oder-paypal-zulaessig-2021-03-25), read 2026-10-20.
- *Reading:* this is the nearest court ruling found, and it is German, about a fee charged at payment, not about a
  refund. Its test goes against R-LEAVE-6. The amount Raketa keeps is the card's own processing fee, which differs by
  card kind, not a separate service. Under the Flixbus test it would sit on the banned side.

### R-LEAVE-6 · Still nothing rules on a fee kept back from a refund rather than charged at payment

- **[ABSENT]** No court ruling, UOKiK decision, regulator's guidance or commentary found addresses a payment fee kept back
  from a **refund**. Where we looked this round (2026-10-20):
  - **Polish courts:** searches for judgments on "art. 37a" of the UUP found none in any court.
  - **Commentary:** the Polish payments-law blog *Usługi płatnicze – aspekty prawne* reads ust. 3 as "odbiorca nie może
    nakładać żadnych opłat na tego płatnika" (the payee may impose no fee at all on that payer) for debit, credit and
    prepaid cards, and ust. 2 as capped at direct costs. It says nothing about refunds or deductions
    ([21 October 2018](https://prawoplatnicze.wordpress.com/2018/10/21/czy-sprzedawcy-moga-pobierac-dodatkowe-oplaty-surcharge-z-tytulu-platnosci-kartami-platniczymi/)).
  - **UOKiK:** its eBilet decision RWR 9/2023 (15 November 2023) is about showing a ticket's compulsory service fee in
    the "cena od…" price and before the basket, not about keeping a fee from a refund
    ([decision](https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/530d151df5ad4a6ec1258a69003b85da/$FILE/14304903.pdf/e-Bilet_wersja%20jawna%20decyzja%20zobowi%C4%85zaniowa%20RWR%209_2023.pdf)).
  - **EU:** the European Court of Auditors' special report 01/2025 questions the evidence for the surcharge ban and
    names gaps in enforcement. As reported, it says nothing about refunds ([heise, 9 January 2025](https://heise.de/-10234876);
    the report itself was not read).
  - **PSR/PSD3:** the provisional agreement of 27 November 2025 has no final article text that could be found. Law-firm
    notes disagree on how far its surcharge ban reaches ([Hogan Lovells](https://www.hoganlovells.com/en/publications/final-texts-for-psd3-and-psr-awaited-as-european-parliament-and-council-of-eu-announce-provisional),
    [Taylor Wessing](https://www.taylorwessing.com/en/insights-and-events/insights/2025/11/eu-lawmakers-strike-a-deal-on-payments-reforms)).
  - **Rzecznik Finansowy:** nothing found on payees' fees.
  - **CJEU:** EUR-Lex and Curia answered with a bot check, so the judgments were not re-read this round. The finding on
    C-484/20 is carried.
- *Reading:* the question is still for the lawyer reviewing the terms. Nothing new weakens the earlier reading that, on a
  personal EU card, keeping the card's fee back is exposed to ust. 3. The one new analogy, Flixbus, points the same way.

---

## 13. R-LEAVE-6, R-LEAVE-41: what a Polish club records for VAT and invoices when a share is taken and then refunded

The club is the seller. Already answered and carried, with their dates:

- Court hire is 8 % VAT ([`local-market.md#vat-on-court-time-is-8-`](local-market.md#vat-on-court-time-is-8-), 2026-10-06).
- No cash register is needed for a sale paid in full through a bank or operator, under annex poz. 42
  ([`local-market.md#no-cash-register-for-sales-paid-fully-online`](local-market.md#no-cash-register-for-sales-paid-fully-online)).
- An invoice goes to a consumer only on request, and to a business always
  ([`#invoices-on-request-for-consumers-always-for-businesses`](local-market.md#invoices-on-request-for-consumers-always-for-businesses)).
- KSeF dates, and that invoices to consumers stay outside KSeF ([`#ksef`](local-market.md#ksef)).
- Refunds of register sales go in a separate register, and an invoiced refund needs a corrective invoice
  ([`../club-software/money-desk-invoices-and-fiscal.md#6-refunds-who-gives-back-what-and-how`](../../club-software/money-desk-invoices-and-fiscal.md#6-refunds-who-gives-back-what-and-how),
  [`#8-invoices-and-ksef`](../../club-software/money-desk-invoices-and-fiscal.md#8-invoices-and-ksef)).

This section adds what happens **at the moment of the refund**. A tax adviser's reading is still needed wherever a line
below says so.

Statutes are read from the current consolidated texts:

- the VAT Act, [Dz.U. 2026 poz. 1263](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf) (state of 26 August 2026);
- the cash-register regulation, [Dz.U. 2025 poz. 845](https://api.sejm.gov.pl/eli/acts/DU/2025/845/text.pdf).

Both were read 2026-10-20.

### R-LEAVE-6, R-LEAVE-41 · A share taken before the game is an advance: VAT is due when the money arrives

- **[LAW]** Art. 19a ust. 8: "Jeżeli przed dokonaniem dostawy towaru lub wykonaniem usługi otrzymano całość lub część
  zapłaty, w szczególności przedpłatę, zaliczkę, zadatek, … obowiązek podatkowy powstaje z chwilą jej otrzymania w
  odniesieniu do otrzymanej kwoty". In English: money received before the service is taxed when it is received, on the
  amount received.
- **[DOCS]** A hotel that only places a pre-authorisation on the guest's card "pobiera odpowiednią kwotę za nocleg
  dopiero po pojawieniu się klienta w Hotelu i dopiero na ten moment rozpoznaje obowiązek podatkowy". In English: it
  takes the money, and counts the tax, only when the guest arrives.
  - This is the applicant's own description of its practice in a ruling, not the authority's finding.
  - Source: [KIS 0113-KDIPT1-3.4012.1199.2025.1.JM, 13 February 2026](https://eureka.mf.gov.pl/informacje/podglad/679758),
    read 2026-10-20.
- *Reading:* a held share is not money received. VAT arises when the share is taken at the cut-off, as 2,96 zł of every
  40 zł at 8 %, and never for a hold that is let go.

### R-LEAVE-6, R-LEAVE-41 · Giving back a share for a game the player doesn't get lowers the club's VAT

- **[LAW]** Art. 29a ust. 10: "Podstawę opodatkowania obniża się o: … 3) zwróconą nabywcy całość lub część zapłaty
  otrzymaną przed dokonaniem sprzedaży, jeżeli do niej nie doszło". In English: the taxable amount is lowered by an
  advance returned, in whole or in part, when the sale did not happen.
- **[LAW]** Ust. 13: where the tax was shown on an invoice, the lowering is made "za okres rozliczeniowy, w którym
  podatnik wystawił fakturę korygującą w postaci faktury ustrukturyzowanej". In English: in the period of the KSeF
  corrective invoice.
  - Ust. 13a: for any other corrective invoice, in the period the buyer's receipt of it is confirmed.
  - Ust. 15 pkt 6: there is a way out when receipt can't be confirmed.
  - Ust. 13 to 13c apply only "w stosunku do podstawy określonej na wystawionej fakturze z wykazanym podatkiem", so
    they set no period for a sale with no invoice.
- *Reading:*
  - **R-LEAVE-41** (the club cancels, 40 zł back): the plain case of pkt 3. The club's VAT falls by 2,96 zł.
  - **R-LEAVE-6** (the seat is taken): the leaver's own sale never happens, so the 38,24 zł given back lowers VAT by
    2,83 zł. The joiner's 40 zł is a new advance, taxed when received.

### R-LEAVE-6 · The part kept back: KIS treats money kept when the service never happens as compensation outside VAT, but taxes it when the service is partly given

- **[DOCS]** A hotel deposit kept after a late cancellation or no-show:
  - "zatrzymana kwota zadatku, nie stanowi wynagrodzenia za wykonanie usługi, lecz pełni funkcję odszkodowawczą" (the
    deposit kept is not pay for a service but compensation);
  - "Spółka ma prawo do skorygowania podstawy opodatkowania i podatku należnego z tytułu wpłaconego na rzecz Spółki
    zadatku nawet, jeśli zadatek nie podlega zwrotowi" (the seller may correct the VAT on the deposit even though it
    keeps it).
  - The ruling relies on C-277/05 *Société thermale*.
  - Source: [KIS 0112-KDIL1-1.4012.155.2024.3.HW, 28 May 2024](https://eureka.mf.gov.pl/informacje/podglad/587951), read 2026-10-20.
- **[DOCS]** On a cancelled booking: "należy skorygować podatek należny od zadatku, zaliczki, opłaty rezerwacyjnej nie
  ma bowiem przedmiotu podatku" (the VAT on the deposit, advance or booking fee must be corrected, because nothing taxable
  remains).
  - Source: [KIS 0112-KDIL3.4012.421.2024.2.MC, 19 September 2024](https://eureka.mf.gov.pl/informacje/podglad/605340), read 2026-10-20.
- **[DOCS]** The newest hotel ruling splits the cases:
  - fees kept "w sytuacji gdy usługi nie są zrealizowane, nie stanowią wynagrodzenia … i nie podlegają opodatkowaniu"
    (when the service is not given, they are not pay and not taxed);
  - fees kept "w sytuacji częściowego zrealizowania usług stanowią wynagrodzenie (zaliczkę) za świadczenie usług i
    podlega opodatkowaniu" (when the service is partly given, they are pay, and taxed).
  - It weighs C-277/05, C-90/20 *Apcoa* and C-295/17 *MEO*.
  - Source: [KIS 0113-KDIPT1-3.4012.1199.2025.1.JM, 13 February 2026](https://eureka.mf.gov.pl/informacje/podglad/679758), read 2026-10-20.
- **[DOCS]** The other line of EU case law:
  - **C-250/14 *Air France-KLM* (23 December 2015):** the price of an unused, non-refundable ticket stays taxable,
    because the passenger had the right to the service ([Pinsent Masons](https://www.pinsentmasons.com/out-law/news/cjeu-vat-is-chargeable-on-non-refundable-unused-air-tickets),
    secondary).
  - **C-295/17 *MEO*:** HMRC reads it as: "the fact that the customer is no longer making use of that supply is not
    relevant if the supplier has made the service available" ([HMRC VATSC05920, updated 7 March 2025](https://www.gov.uk/hmrc-internal-manuals/vat-supply-and-consideration/vatsc05920)).
    This is a UK authority and does not bind Poland.
  - The judgments themselves could not be opened, because EUR-Lex and Curia served a bot check. Read 2026-10-20.
- *Reading, for a tax adviser:* the 1,76 zł kept from a leaver whose seat was taken (R-LEAVE-6) fits KIS's "not given"
  line, because he gets no game: compensation outside VAT, with the 0,13 zł of VAT in it corrected. But the court hour is
  still played, which looks like the "partly given" case KIS taxes. *Air France* and *MEO* would also tax a sum kept for
  a service that stayed available. The same question arises for a share kept whole when nobody takes the seat after the
  cut-off. No ruling on a shared court or a seat was found.

### R-LEAVE-6, R-LEAVE-41 · With no invoice, the online sale goes in the VAT records on an internal document; a refund's lowering goes in a separate record of corrections

- **[DOCS]** A venue renting tennis courts online, paid through an operator and exempt from the register under poz. 42,
  enters those sales in JPK_V7M "dowodem wewnętrznym z oznaczeniem WEW" (on an internal document marked WEW).
  - The entry is built from "ewidencji sprzedaży bezrachunkowej": page number, date, gross amount, VAT rate and which
    service.
  - An invoice a consumer asks for changes none of that. It carries no FP mark and is not listed separately in JPK. KIS
    found the position correct.
  - Source: [KIS 0111-KDIB3-2.4012.631.2025.1.SR, 30 September 2025](https://eureka.mf.gov.pl/informacje/podglad/659768), read 2026-10-20.
- **[LAW]** On the register, refunds are never rung up: "W ewidencji nie ujmuje się zwrotów towarów i uznanych reklamacji
  towarów i usług" (§ 3 ust. 2). Returns and accepted complaints go in "odrębnej ewidencji zwrotów i uznanych reklamacji"
  with the details set out in § 3 ust. 3.
  - An advance paid by transfer gets its receipt "niezwłocznie po uznaniu tej należności na rachunku bankowym …, nie
    później niż z końcem miesiąca" (as soon as it is credited, at the latest by the month's end; Annex 1, part A pkt 5).
  - Source: [Dz.U. 2025 poz. 845](https://api.sejm.gov.pl/eli/acts/DU/2025/845/text.pdf), read 2026-10-20.
- **[DOCS]** A cancellation is neither a return nor a complaint. For a deposit rung on the register and then kept, KIS
  allows the lowering through "ewidencji korekt odrębnej od wyżej wskazanych ewidencji, o których mowa w § 3 ust. 3-4
  rozporządzenia". In English: a corrections record separate from the § 3 registers.
  - Its form "nie jest uwarunkowany" by § 3 ust. 3–5. The seller must be able to name each customer and the reason.
  - The lowering is made "w okresie, w którym dochodzi do przekształcenia zadatku w odszkodowanie" (in the period the
    deposit turns into compensation).
  - Source: [KIS 587951](https://eureka.mf.gov.pl/informacje/podglad/587951), question 4, read 2026-10-20.
- **[ABSENT]** No ruling on refunding a register-exempt online sale recorded on a WEW document.
  - Searched Eureka's own search (its public API) on 2026-10-20 with nine phrasings: refunds, WEW, poz. 42,
    court bookings, online bookings, cancelled tickets.
- *Reading, for a tax adviser:* the club lowers the base under art. 29a ust. 10 pkt 3. It records the refund as a minus
  entry on an internal document against the share's own WEW entry, citing the Stripe refund. By question 4's logic it
  does so in the period of the leave or the refund. Raketa's per-share record (payer, game, amounts, refund) is what lets
  the club "jednoznacznie" link each payment and each refund to a service, which both poz. 42 and question 4 require.

### R-LEAVE-6, R-LEAVE-41 · With an invoice: a business always, a consumer on request; a refund needs a corrective invoice, through KSeF for a business

- **[LAW]** Art. 106b ust. 1: an invoice must document a sale to another taxpayer (pkt 1), and the "otrzymanie przez niego
  całości lub części zapłaty przed dokonaniem czynności, o których mowa w pkt 1 i 2" (an advance; pkt 4).
  - Ust. 1a: no advance invoice is needed "jeżeli całość lub część zapłaty … otrzymał w tym samym miesiącu, w którym
    dokonał czynności" (when the advance and the service fall in the same month).
  - Ust. 3 pkt 1a: a consumer may ask for an advance invoice within 3 months of the end of the month of the service or
    the payment.
- **[LAW]** Art. 106j ust. 1: a corrective invoice is issued when "dokonano zwrotu nabywcy całości lub części zapłaty, o
  której mowa w art. 106b ust. 1 pkt 4" (pkt 4) or the taxable amount changes (pkt 1). Ust. 2 pkt 2a: it carries the
  KSeF number of the invoice it corrects.
- **[LAW]** For a KSeF corrective invoice, art. 29a ust. 13 (above) puts the lowering in the period it is issued.
  - Source: [VAT Act, Dz.U. 2026 poz. 1263](https://api.sejm.gov.pl/eli/acts/DU/2026/1263/text.pdf), read 2026-10-20.
- *Reading:* a share taken at a cut-off a day before a game in the same month needs no separate advance invoice for a
  business player. One taken on 31 October for a 1 November game does. A refunded share that was invoiced (always, for a
  business; on request, for a consumer) needs a corrective invoice, and for a business it goes through KSeF. With
  per-seat shares, one game can mean up to four invoices and four corrections at a club. Playmore wires Fakturownia to
  "faktura VAT z każdej płatności" (a VAT invoice from every payment; carried, `money-desk-invoices-and-fiscal.md#8-invoices-and-ksef`).

### R-LEAVE-6, R-LEAVE-41 · Still open, for a tax adviser and the lawyer

- Whether the card fee kept from a leaver whose seat was taken, or a share kept whole after the cut-off, is compensation
  outside VAT (KIS's "service not given" line) or taxable pay (the "partly given" line, *Air France*, *MEO*).
- The settlement period for a refund of a register-exempt online share recorded on a WEW document. No ruling was found.
- Whether a fee kept back from a refund on a personal EU card is a charge "for using" the card under art. 37a ust. 3 UUP.
  Nothing rules on it; the one analogy found (BGH *Flixbus*) points against keeping it.
