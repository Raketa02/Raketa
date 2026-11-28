# Gaps round: the leaver's card fee (S-01A, F-LEAVE-6.1)

Answers to the facts the S-01A grilling of F-LEAVE-6.1 needed (story #605, 2026-10-10): what Stripe does with its fee
on a refund and on a released hold, how long a hold lasts, when the real fee is known and whether a card's price can
be known before charging, what a Connect platform can and cannot change about who pays, and what Polish and EU law
says about keeping a payment fee back from a consumer who leaves. Read 2026-10-10 from Stripe's own pages only
(docs.stripe.com, stripe.com, support.stripe.com) and from primary legal sources (the Sejm's consolidated statutes,
EUR-Lex, UOKiK). The two Stripe pages the product owner sent first are in §4. A line marked *reading* is this
researcher's inference from the facts above it, not a source. Nothing here is legal advice; §5's open points are for
the lawyer reviewing the terms.

Kinds: `[DOCS]` a provider's or a regulator's documents; `[PRICE]`; `[LAW]`; `[POLICY]`; `[ABSENT]` looked for and
not found, with where.

The decision these facts settled is the `story-decisions S-01A` comment of 2026-10-10 on
[#605](https://github.com/Rakieta02/Rakieta/issues/605#issuecomment-6097600856).

## 1. Stripe's fee on a refund and on a released hold

### The original processing fee is never returned on a refund

- **[DOCS]** "Stripe's processing fees from the original transaction aren't returned."
  [Stripe: Refund and cancel payments](https://docs.stripe.com/refunds) — read 2026-10-10
- **[DOCS]** "For all refunds, payment processing, Connect, and currency conversion fees from the original charge are
  not returned." [Stripe support: fees for refunded payments](https://support.stripe.com/questions/understanding-fees-for-refunded-payments)
  — read 2026-10-10
- **[PRICE]** Poland, standard pricing: "The payment processing, Connect and currency conversion fees from the original
  transaction are not returned"; issuing a card refund costs nothing: "For all other payment methods, there are no fees
  for issuing refunds." [Stripe pricing, Poland](https://stripe.com/en-pl/pricing), [support article above] — read
  2026-10-10
- **[DOCS]** On IC+ pricing, from 1 March 2023 the variable fee is no longer returned and a fixed fee is charged for
  every refund. [Stripe support: refund fee changes on IC+](https://support.stripe.com/questions/refund-fee-changes-for-businesses-on-ic-pricing)
  — read 2026-10-10

### Letting a hold go before it is taken costs nothing

- **[DOCS]** "You can cancel a payment before it's completed at no cost." [Stripe: Refund and cancel payments](https://docs.stripe.com/refunds)
  — read 2026-10-10
- **[PRICE]** Fees are assessed per successful payment; no page lists a fee for an authorisation that is never
  captured. [Stripe: local payment methods pricing](https://stripe.com/en-pl/pricing/local-payment-methods) — read
  2026-10-10
- **[DOCS]** Stripe's own advice for refunds close to the payment: "Manual authorization and capture lets you better
  control costs by canceling payments before they're captured, or by reducing your captured amount rather than
  processing a refund." [Stripe: Refunds, cost optimization](https://docs.stripe.com/refunds#cost-optimization) — read
  2026-10-10

### A refund made soon after the charge can be a reversal, and what that does to the fee is unclear

- **[DOCS]** "Some refunds—those issued shortly after the original charge—appear in the form of a reversal … (A
  reversal is the cancellation of a transaction. Stripe doesn't withhold any fees for payment reversals)". "IC+ users
  might see a difference in cost between reversals and refunds because reversals usually incur lower network fees."
  A reversal is told by `destination_details[card][type] = 'reversal'` on the refund.
  [Stripe: Refund and reversal](https://docs.stripe.com/refunds#refund-and-reversal) — read 2026-10-10
- **[DOCS]** "A partial refund made soon after the original charge can be processed as a partial reversal."
  [Stripe support: where is my customer's refund](https://support.stripe.com/questions/where-is-my-customers-refund)
  — read 2026-10-10
- *reading:* "doesn't withhold any fees" most plausibly means no extra fee for the reversal; no page says the original
  fee comes back, and the "For all refunds" sentence covers reversals. How soon "shortly" is, is not stated.

## 2. Holds: how long, what they guarantee, and what is not documented

### An off-session Visa hold lasts 4 days 18 hours; Mastercard 7 days

- **[DOCS]** Online card authorisation windows, merchant-initiated against customer-initiated: Visa "5 days\*" against
  "7 days"; Mastercard, Amex and Discover 7 against 7. "\* The exact authorization window is 4 days and 18 hours".
  [Stripe: place a hold on a payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) —
  read 2026-10-10
- **[DOCS]** "the `payment_method_details.card.capture_before` attribute on the charge is the most reliable and
  accurate way to determine your charge's authorization window." [Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits)
  — read 2026-10-10
- **[DOCS]** "Authorizing a payment guarantees the amount by holding it on the customer's payment method." On expiry,
  "the funds are released and the payment status changes to `canceled`". Stripe's own delayed-capture preview
  (`automatic_delayed`) captures "about 6 hours before the expiration time". [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method)
  — read 2026-10-10

### Extended holds do not fit off-session charges at a sports club

- **[DOCS]** Extended authorisation (up to about 30 days) is offered to "users on IC+ … If you're on blended Stripe
  pricing … contact us". Visa, all other merchant categories: "Stripe charges an additional 0.08% fee per transaction.
  The extended window only applies to Customer-Initiated Transactions"; Mastercard, all merchant categories, 30 days;
  Amex and Discover only for lodging and travel. [Stripe: extended authorization](https://docs.stripe.com/payments/extended-authorization)
  — read 2026-10-10
- **[DOCS]** Overcapture excludes Visa businesses in the EEA; incremental authorisations "don't extend the validity
  period". [overcapture](https://docs.stripe.com/payments/overcapture), [incremental authorization](https://docs.stripe.com/payments/incremental-authorization)
  — read 2026-10-10

### Renewing a hold is not documented

- **[ABSENT]** Neither the hold page nor the CIT/MIT page mentions re-authorising after a hold expires, or a
  "reauthorization" category of merchant-initiated payment. [CITs and MITs](https://docs.stripe.com/payments/cits-and-mits),
  [place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-10
- *reading:* a second, separate hold placed later on a saved card (the first one cancelled) uses only documented
  steps: an off-session manual-capture payment, a cancellation, and a capture before `capture_before`.

### BLIK cannot be held

- **[DOCS]** BLIK: "Manual capture support: No"; "Refunds / Partial refunds: Yes / Yes", processed "immediately or
  within a couple of hours"; "Reusable BLIK is supported for off-session usage." No BLIK refund fee is listed.
  [Stripe: BLIK](https://docs.stripe.com/payments/blik) — read 2026-10-10 (spec Appendix A records the saved-BLIK
  claim as contradicted elsewhere, open item O1)

## 3. When the real fee is known, and whether a card's price can be known before charging

### The fee exists only after capture, and reads late or zero for a club on its own pricing

- **[DOCS]** "A PaymentIntent must be captured and have a status of `succeeded` for the Stripe fees to be available";
  readiness is signalled by `charge.updated`. "IC+ users can't retrieve payment fee information from the balance
  transaction. Use the Payment fees report instead." [Stripe: expand use cases](https://docs.stripe.com/expand/use-cases)
  — read 2026-10-10
- **[DOCS]** Under `automatic_async`, `balance_transaction` "might be `null` immediately after confirmation"; the
  `charge.updated` service level is "1 hour". [asynchronous capture](https://docs.stripe.com/payments/payment-intents/asynchronous-capture)
  — read 2026-10-10
- **[DOCS]** Under standalone fees the charge's balance transaction has "fees set to zero", and the fee arrives later,
  "typically within 36 hours", as aggregate fees; this "can occur for reasons such as custom pricing … or Stripe fee
  credit awards". In the fees report, "Fee data becomes available within 96 hours." [standalone fees](https://docs.stripe.com/standalone-fees),
  [all fees report](https://docs.stripe.com/reports/all-fees) — read 2026-10-10
- **[DOCS]** Direct charges are read "using the connected account ID in the Stripe-Account header"; "The resulting
  charge's BalanceTransaction includes a detailed fee breakdown". [direct charges](https://docs.stripe.com/connect/direct-charges)
  — read 2026-10-10
- **[ABSENT]** Whether a manual capture's response already carries `latest_charge.balance_transaction`: no page says.

### A card's price tier cannot be known before the charge

- **[DOCS]** "Stripe determines a card's classification based on information from card networks at the point of
  capture." Premium means "Commercial, corporate, or business cards issued by Visa, Mastercard, and Cartes Bancaires";
  all other cards (Amex, Maestro…) are standard. [Stripe support: standard and premium cards](https://support.stripe.com/questions/what-s-the-difference-between-standard-and-premium-cards)
  — read 2026-10-10
- **[DOCS]** A saved card carries `country` ("You could use this attribute to get a sense of the international
  breakdown"), `funding` (`credit`, `debit`, `prepaid` or `unknown`) and `regulated_status`; no field says
  commercial or consumer. `brand_product` exists only for in-person (`card_present`) payments.
  [PaymentMethod object](https://docs.stripe.com/api/payment_methods/object), [Charge object](https://docs.stripe.com/api/charges/object)
  — read 2026-10-10
- **[PRICE]** Poland: "1.5% + 1.00zł for standard European Economic Area cards", "1.9% + 1.00zł for premium",
  "2.5% + 1.00zł for UK cards", "3.25% + 1.00zł for international cards", each "+ 2% if currency conversion is
  required"; BLIK 1.6% + 1.00zł; Przelewy24 1.9% + 1.00zł. On a 40 zł share: 1,60 / 1,76 / 2,00 / 2,30 zł; BLIK
  1,64 zł. [Stripe pricing, Poland](https://stripe.com/en-pl/pricing) — read 2026-10-10
- *reading:* the country predicts EEA, UK or international before charging; whether a Visa or Mastercard is a business
  card is learned only at capture.

## 4. Connect: who pays the fee, and what the platform can change

### The two pages the product owner sent

- **[DOCS]** The marketplace application-fees page is written for destination charges and separate charges and
  transfers ("As a marketplace, you're responsible for paying Stripe fees… you collect application fees"); it does not
  describe direct charges with no platform fee. [Stripe: collect application fees](https://docs.stripe.com/connect/marketplace/tasks/app-fees)
  — read 2026-10-10
- **[DOCS]** Fee credits offset an account's own future Stripe fees: "Stripe applies fee credits to Stripe fees as
  they're billed", "You can only apply credits to future fees." Under Connect where connected accounts pay the fees,
  credits apply "for directly processed volume on your platform only", "not for volume facilitated through your
  connected accounts". [Stripe fee credits](https://docs.stripe.com/stripe-fee-credits),
  [Stripe Startups FAQ](https://support.stripe.com/questions/stripe-startups-program-faq) — read 2026-10-10
- *reading:* neither page lets the platform cover or recover a leaver's fee on a club's direct charge.

### With fees collected by Stripe, the club pays the fee and funds every refund

- **[DOCS]** `fees_collector: stripe`: "Stripe collects payment fees directly from the connected account"; the setting
  can't be updated later. [Accounts v2 configuration](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration)
  — read 2026-10-10
- **[DOCS]** "We don't charge any Connect fees to it or to your platform"; payment processing and Interchange Plus fees
  are paid by the connected account. [direct charges: fee payer behavior](https://docs.stripe.com/connect/direct-charges-fee-payer-behavior)
  — read 2026-10-10
- **[DOCS]** "Stripe debits the refund amount from the connected account's balance directly… If the connected account's
  balance is insufficient, we set the refund status to `pending`"; "Refunds use your available Stripe balance (not
  including pending amounts)." [Connect charges](https://docs.stripe.com/connect/charges), [refunds](https://docs.stripe.com/refunds)
  — read 2026-10-10

### Pricing tools, cost passthrough and application fees cannot move the fee

- **[DOCS]** Platform pricing tools work only when "Stripe charges fees on the payment to your platform rather than the
  connected account"; "Configured pricing doesn't apply to direct charges on Standard accounts." Cost passthrough:
  "Any fees that Stripe bills to your connected account directly are ineligible for passthrough."
  [platform pricing tools](https://docs.stripe.com/connect/platform-pricing-tools), [cost passthrough](https://docs.stripe.com/connect/cost-passthrough)
  — read 2026-10-10
- **[DOCS]** An application fee is the platform's revenue; it is not refunded unless the platform passes
  `refund_application_fee`, which on a partial refund returns "a proportional amount". [direct charges](https://docs.stripe.com/connect/direct-charges)
  — read 2026-10-10

### Stripe's terms forbid card surcharges unless the law permits them

- **[POLICY]** "Except to the extent the Card Network Rules or Law permits, User must not charge surcharges, other fees,
  or Taxes for accepting payment cards" (§3.4(e)); the user must "accurately communicate and not misrepresent the
  nature, amount and currency of each Transaction" (§3.7) and keep "a fair and neutral refund and exchange policy"
  that explains how customers get a refund (§3.8). [Stripe Services Agreement](https://stripe.com/legal/ssa-service-terms)
  — read 2026-10-10
- **[DOCS]** Under PSD2, merchants "are no longer allowed to charge consumers additional fees for paying by debit or
  credit card"; "the surcharge ban does not impact the platform or application fee you charge", "provided that these
  fees are not differentiated by payment method". Stripe's surcharging feature is offered only in the United States,
  Canada and New Zealand. [Stripe support: scope of the PSD2 surcharge ban](https://support.stripe.com/questions/scope-of-the-surcharge-ban-under-psd2-for-b2c-and-b2b-payments),
  [Stripe: surcharging](https://docs.stripe.com/payments/cards/surcharge) — read 2026-10-10
- **[ABSENT]** No Stripe page addresses keeping a fee back from a refund. The old support article on passing the fee to
  customers (`passing-the-stripe-fee-on-to-customers`) now redirects to docs.stripe.com/payments.

## 5. Polish and EU law on keeping a payment fee back from a leaver

Statutes from the current consolidated texts: Kodeks cywilny
([Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf)), ustawa o prawach konsumenta
([Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)), ustawa o usługach płatniczych
([Dz.U. 2026 poz. 623](https://api.sejm.gov.pl/eli/acts/DU/2026/623/text.pdf)) — read 2026-10-10.

### A fee for using a personal EU card is banned outright; other cards are capped at cost

- **[LAW]** Art. 37a ust. 3 UUP (Poland's PSD2 art. 62(4)): "Odbiorca nie pobiera opłat za korzystanie z instrumentów
  płatniczych, w przypadku których opłaty interchange są regulowane w przepisach rozdziału II rozporządzenia (UE)
  2015/751" — the payee charges nothing for using cards whose interchange the EU caps. Ust. 2: any other such fee
  "nie mogą przekraczać kosztów bezpośrednich" — may not exceed direct costs. [UUP](https://api.sejm.gov.pl/eli/acts/DU/2026/623/text.pdf),
  [PSD2](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32015L2366) — read 2026-10-10
- **[LAW]** The capped cards are those of the Interchange Fee Regulation: transactions where both providers are in the
  Union (art. 1(1)); Chapter II excludes "commercial cards" and three-party schemes (art. 1(3)).
  [Regulation 2015/751](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32015R0751) — read 2026-10-10
- **[LAW]** Art. 383¹ KC (from the 2014 act implementing CRD art. 19): "Przedsiębiorca nie może żądać od konsumenta
  opłaty za skorzystanie z określonego sposobu zapłaty przewyższającej poniesione przez przedsiębiorcę koszty w
  związku z tym sposobem zapłaty." UOKiK: "Dodatkowa opłata – np. za płatność kartą – nie może być wyższa od prowizji".
  [KC](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf), [CRD](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32011L0083),
  [UOKiK: koszt formy płatności](https://prawakonsumenta.uokik.gov.pl/prawa-ogolne/koszt-formy-platnosci/) — read
  2026-10-10
- **[DOCS]** The Commission reads the payment-fee rule as covering "all kind of fees which are linked to a means of
  payment, regardless of how they are presented to consumers" (CRD Guidance §8.2), and says it now matters only for
  non-capped cards (§8.1). [Commission guidance 2021/C 525/01](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52021XC1229(04))
  — read 2026-10-10
- **[ABSENT]** No judgment, decision or commentary found on whether an amount kept back from a refund is a "charge for
  use". C-484/20 *Vodafone Kabel Deutschland* rules only on art. 62(4)'s reach in time
  ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62020CJ0484)); no surcharging case was found
  under C-616/18, and *VKI v Deutsche Bahn* (C-28/18) concerns SEPA direct debit.
- *reading:* "the 1,60 zł card fee isn't returned" ties the amount kept to the card, so on a personal EU card it is
  exposed to art. 37a ust. 3; on a business or non-EU card, keeping up to the real fee is allowed.

### A cancelling consumer may be charged only the costs actually incurred

- **[POLICY]** UOKiK, 4 July 2014, on leisure services (dance schools, fitness clubs, pools, ski slopes, concerts), when
  a customer resigns: "przedsiębiorca może zatrzymać jedynie kwotę odpowiadającą faktycznie poniesionym kosztom";
  "zgodnie z prawem należy mu się zwrot pieniędzy za część niezrealizowaną". 2018: "potrącenie powinno być adekwatne
  do poniesionych … wydatków". No payment, bank or card costs are mentioned.
  [UOKiK 2014](https://archiwum.uokik.gov.pl/aktualnosci.php?news_id=11103), [UOKiK 2018](https://archiwum.uokik.gov.pl/aktualnosci.php?news_id=15059)
  — read 2026-10-10
- **[LAW]** Art. 385³ KC presumes abusive terms that "wyłączają obowiązek zwrotu … zapłaty za świadczenie niespełnione
  … jeżeli konsument zrezygnuje" (pkt 12), that put "wyłącznie na konsumenta obowiązek zapłaty ustalonej sumy na
  wypadek rezygnacji" (pkt 16), or a "rażąco wygórowanej kary umownej lub odstępnego" (pkt 17). Art. 395 §2: "To, co
  strony już świadczyły, ulega zwrotowi"; art. 396 allows withdrawal "za zapłatą oznaczonej sumy (odstępne)".
  [KC](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf) — read 2026-10-10
- **[LAW]** The register of abusive clauses holds XVII AmC 3015/12 (20.02.2013): a refund "automatycznie pomniejszona o
  faktycznie poniesione … koszty bankowe, związane z przelewem zwrotnym" was abusive — in the statutory right of
  withdrawal, where the law demands a full refund; and XVII AmC 29064/13: "uboczne koszty transakcji nie podlegają
  zwrotowi". Under art. 9 of the 2015 amending act the register's effect lasted "nie dłużej … niż przez 10 lat" from
  17.04.2016, so the entries are now persuasive only. [rejestr klauzul](https://rejestr.uokik.gov.pl),
  [Dz.U. 2015 poz. 1634](https://api.sejm.gov.pl/eli/acts/DU/2015/1634/text.pdf) — read 2026-10-10

### A dated sports booking has no statutory withdrawal right; the leave right is contractual

- **[LAW]** Art. 38 ust. 1 pkt 12 UPK: no withdrawal right for "usług związanych z wypoczynkiem, wydarzeniami
  rozrywkowymi, sportowymi lub kulturalnymi, jeżeli w umowie oznaczono dzień lub okres świadczenia usługi"; the
  consumer must be told so (art. 12 ust. 1 pkt 12). C-96/21 *CTS Eventim* explains the exception as protection against
  "the setting aside of some capacity". [UPK](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf),
  [C-96/21](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62021CJ0096) — read 2026-10-10

### Fees must be disclosed before the order, and a platform must say who owes what

- **[LAW]** Art. 12 ust. 1 UPK: the total price "wraz z podatkami … oraz innych kosztach" (pkt 5) and the payment
  method (pkt 7); art. 17 ust. 1: "bezpośrednio przed złożeniem … zamówienia"; art. 23: costs not disclosed are not
  owed — "konsument nie ponosi tych opłat i kosztów"; art. 10 ust. 1: express consent to every extra payment;
  art. 12a pkt 4: an online marketplace states the "podziale obowiązków" between the trader and itself.
  [UPK](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf) — read 2026-10-10
- **[LAW]** The club is the trader and owes the refund, so the clause belongs in the club–consumer terms. *Wathelet*
  (C-149/15) treats an intermediary that "has not duly informed the consumer" as the seller (a goods case; its reach to
  services is not verified); art. 23a of the competition and consumer act bans the "stosowanie" of abusive clauses.
  [C-149/15](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62015CJ0149),
  [Dz.U. 2025 poz. 1714](https://api.sejm.gov.pl/eli/acts/DU/2025/1714/text.pdf) — read 2026-10-10

### The options ranked by legal risk

- *reading:* lowest first — (1) keep nothing back; (2) hold the card until the cut-off and let the hold go on a leave,
  so nothing is ever taken (the residual duties are disclosing the hold and handling one that cannot reach the
  cut-off); (3) keep exactly the real fee (inside art. 383¹ and UOKiK's actual-cost line, but card-dependent and so
  exposed to art. 37a ust. 3 on personal EU cards); (4) keep one worst-case fee from everyone (all of (3)'s exposure,
  and above cost for most leavers, against art. 383¹ and art. 37a ust. 2).
- *reading:* after the cut-off the leaver has no right to money back, so returning a replacement's payment less what
  Stripe kept on his own is more than he is owed, and stays within UOKiK's actual-cost line; whether it is still a
  "charge for use" on a personal EU card is the open point.

## Still open

- Whether a refund deduction that equals the card's real fee is a "charge for use" under art. 37a ust. 3 UUP, after the
  cut-off in particular — for the lawyer reviewing the terms (spec O3).
- Whether a flat, payment-neutral withdrawal sum under art. 396 KC escapes the surcharge rules.
- Whether a reversal returns the original fee to the merchant, and how soon "shortly" is.
- Whether a manual capture's response carries the balance transaction at once; whether partial-capture fees are on the
  captured amount only (implied by Stripe's 2025-03-31 changelog, not stated).
- Whether BLIK, a non-card instrument, is outside art. 37a ust. 3 (not verified), and whether saved BLIK ships (O1).
- Whether Stripe objects to a second hold placed days after a first one was let go (undocumented either way).
