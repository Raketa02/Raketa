# Prices, passes and benefit cards — what rivals and Kraków clubs do, and what the law allows

Research for areas 6 (prices) and 10 (benefit sports cards) of the planning map *Raketa becomes the club's
booking software* (decided 2026-10-12): how a club prices a court-hour, sells passes and prepaid value, and takes
MultiSport, Medicover Sport, FitProfit and PZU Sport, in rival software, at Kraków desks, and under Polish and EU law.

**Extends** [`integration.md`](integration.md) (§4 *Benefit cards*, §5 *tenis4U*),
[`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md) (*Benefit sports cards*,
*Court prices in Kraków*, *Paying ahead, and online is cheaper than the desk*),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) (*Prices*),
[`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md) (Playmore's wallet) and
[`../games-and-fill-in/areas/COURTS.md`](../games-and-fill-in/areas/COURTS.md). Facts carried from there keep their
dates; everything else was read **2026-10-12**.

**This file decides nothing.** Each feature below is to be decided *Build at launch · Build later · Leave out · Ask a
real club* in the club-software grilling. Nothing here estimates what Raketa would cost to build.

**Sources.** Playtomic and MATCHi help pages were read through their public Zendesk API (the HTML answers 403).
Playmore's and tenis4U's interface text comes from the JavaScript their web apps serve to every visitor
(`playmore.pl/assets/…`, `app.tenis4u.pl`, the public demo panel `test-panel.tenis4u.pl`). Polish acts were read in
the *Dziennik Ustaw* PDFs on eli.gov.pl (ISAP's pages need JavaScript; the ISAP links are given for reference); EU
acts in the Publications Office's copies of the EUR-Lex documents (EUR-Lex itself answered 202 with a bot check).
Kraków prices come from the clubs' own sites, Playmore's club price pages — which Playmore labels *"Stawki
orientacyjne"* (indicative rates) and, for clubs on tenis4U, writes itself — and PADO's listings. MultiSport's own
facility search API answered 403 and was not used. Nobody signed in, booked or paid, and no endpoint that writes was
called.

**Kinds:** `[POLICY]` a company's own rule, term, help or interface text · `[PRICE]` a published price · `[DOCS]` a
provider's developer or partner document · `[LAW]` an act, directive or regulator's text · `[COMPLAINT]` one
person's account · `[ABSENT]` looked for and not found, with where. Lines marked *reading* are inferences, not
sources.

## Read this first

- **Every rival keeps one price table keyed by court × day × time band × booking length, with dated changes,** and
  adds a member or category price on top (Playtomic, MATCHi, tenis4U, kluby.org). **No main rival sells
  demand-based "dynamic" pricing**; MATCHi's price condition *"lead time before booking"* is the closest. Raketa's
  bands (standard + weekday/weekend) are the common core.
- **Three of the four Kraków squash clubs read run two price lists, online cheaper:** Atras 10 % (15 % with a pass),
  Squash4You 15 zł, Paolo 5 zł; Miazga charges the same. Playmore then adds a 1,48–1,99 zł service fee to online
  payments. **No Kraków padel club publishes an online/desk difference.**
- **Prepaid value is normal in Kraków squash:** *"Karnet wartościowy 600 zł"* sold for 495 zł at Squash4You, *"płacisz
  500 zł, do wykorzystania masz 550 zł. Ważny 90 dni"* at Paolo. Every platform sells count passes and value passes
  with an expiry the club sets.
- **Expiry and non-refund are the club's to set, within limits.** Poland has no statute on gift-card validity (ECC
  Poland on uokik.gov.pl); Atras and Squash4You write *"opłacony karnet nie podlega zwrotowi"* (a paid pass is not
  refunded), the kind of clause the Civil Code's grey list (art. 385³ pkt 12) treats, in case of doubt, as abusive when
  it denies a refund for a service not performed.
- **A wallet usable at one club is outside payment law; a credit spendable at many clubs may not be.** The Polish
  act excludes instruments usable *"wyłącznie w placówkach wydawców"* or in a *"ograniczonej sieci"* (art. 6 pkt 11);
  above €1 m a year the issuer must notify KNF, which may refuse; PSD2's recital 14 says a network of listed merchants
  that keeps growing does not qualify. E-money, by contrast, must be redeemable at par on demand and needs a licence
  (art. 59l); Playmore's wallet already pays out on demand.
- **Stripe lists stored value "issued by anyone other than the seller" as a Restricted Business** (approval needed);
  seller-kept credit *"may be subject to limits"*. Its *customer balance* applies only to invoices. *Reading:* a
  per-club wallet on a direct-charge account fits Stripe's model; a Raketa-wide credit does not without approval.
- **Playmore settles sport cards with a deposit since August 2026:** the player pays the card discount up front and
  gets it back in the Playmore wallet when the desk stamps the card, because *"Klub dostaje pieniądze od operatora
  karty tylko za odbite wejście"* (the club is paid by the card operator only for a stamped entry). Its "automatic
  verification" is a declared count plus the desk's stamp, not a check with Benefit Systems.
- **Playmore's wallet already crosses clubs and can be cashed out** (*"Zleć wypłatę"*, limit 10 000 zł), while its
  terms say it *"nie stanowi świadczenia usług płatniczych"* (is not a payment service).
- **Card operators pay the club per registered visit, monthly.** Medicover Sport: *"Raz w miesiącu, opłacimy każde
  zrealizowane wejście"*; Benefit Systems co-finances a tennis court *"po 15 PLN za każdego użytkownika karty
  MultiSport (maksymalnie dwóch …)"* (Sport Factory Park). FitProfit belongs to the Benefit Systems group.
- **Entry-check integrations exist, per facility and by consent, never public:** MultiSport (a *ClientId* from
  Benefit Systems), Medicover Sport (a *facility token* and *"Oficjalna zgoda na integrację"*), FitProfit and PZU
  Sport are wired into gym gate systems (eFitness, GYMMANAGER). None verifies a card at booking time; the MultiSport
  app takes no bookings. tenis4U checks Medicover by phone number only from 15 min before to 15 min after the start.
- **The Kraków rule is 15 zł off per card per hour, usually two cards per court at most;** Medicover at Sport
  Factory Park has no per-court cap as long as the total stays under the court price; tenis4U needs 60 minutes for
  MultiSport; a no-show forfeits the card and pays in full (Squash4You).
- **The first published Kraków holiday price:** Sport Factory Park prices *"Sobota, niedziela oraz święta"* (weekends
  and public holidays) as one band.

## The law on prepaid value, and Stripe's rules

### Poland — payment services and e-money
- **[LAW] The limited-use exclusion.** The act does not apply to *"usług opartych na instrumentach płatniczych, które
  można wykorzystywać jedynie w ograniczony sposób"* (services on instruments usable only in a limited way) that
  either *"pozwalają posiadaczowi nabywać towary lub usługi wyłącznie w placówkach wydawców tych instrumentów lub w
  ramach ograniczonej sieci podmiotów związanych umową handlową bezpośrednio z zawodowym wydawcą"* (buy only at the
  issuer's premises or within a limited network under direct commercial agreement with a professional issuer), lit. a,
  or *"służą wyłącznie do nabywania bardzo ograniczonego zakresu towarów lub usług"* (a very limited range), lit. b
  (art. 6 pkt 11) ([Dz.U. 2026 poz. 623, consolidated text as of 13 Apr 2026](https://eli.gov.pl/api/acts/DU/2026/623/text/O/D20260623.pdf);
  [ISAP](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260000623)).
- **[LAW] The €1 m notification.** When payment transactions under lit. a or b exceed €1 000 000 in 12 months the
  issuer notifies KNF within 14 days; KNF enters it in the register or *"wydaje decyzję o odmowie wpisu"* (refuses),
  after which the issuer has 3 months to shrink below the threshold or apply for a payment-institution licence
  (art. 6c ust. 1–5) ([same text](https://eli.gov.pl/api/acts/DU/2026/623/text/O/D20260623.pdf)).
- **[LAW] E-money** is *"wartość pieniężną przechowywaną elektronicznie … wydawaną, z obowiązkiem jej wykupu, w celu
  dokonywania transakcji płatniczych, akceptowaną przez podmioty inne niż wyłącznie wydawca pieniądza elektronicznego"* (stored value issued
  with a duty to redeem, accepted by others than the issuer) (art. 2 pkt 21a); the issuer must *"umożliwić … wykup
  pieniądza elektronicznego w każdym czasie, według wartości nominalnej"* (redeem at any time at par) (art. 59l);
  a redemption fee only in narrow cases and at cost (art. 59m); the claim lapses 5 years after the contract ends
  (art. 59o) ([same text](https://eli.gov.pl/api/acts/DU/2026/623/text/O/D20260623.pdf)).
- **[LAW] KNF applies the EBA guidelines.** Since 1 June 2022 KNF assesses the limited network under EBA/GL/2022/02:
  a contract between the issuer and each acceptor, a *"maksymalnej liczby dostawców"* (maximum number of
  acceptors), *"wspólnej marki"* (a common brand), the geographic area, the maximum load per instrument;
  *"Pojedynczy instrument płatniczy … nie może być wykorzystywany w ramach różnych ograniczonych sieci"* (one
  instrument, one network); and an excluded issuer must tell users the service *"nie podlegają regulacji przepisów
  u.u.p. i nie są objęte nadzorem KNF"* (is not regulated or supervised by KNF)
  ([KNF communication, updated 1 Jun 2022](https://www.knf.gov.pl/knf/pl/komponenty/img/Komunikat_ws_stosowania_wylaczenia_z_art_6_pkt_11_ustawy_o_uslugach_platniczych.pdf)).
  The register is at [e-rup.knf.gov.pl](https://e-rup.knf.gov.pl/).

### EU — PSD2, EMD2 and the coming Regulation
- **[LAW] PSD2 art. 3(k)** excludes *"instruments allowing the holder to acquire goods or services only in the
  premises of the issuer or within a limited network of service providers under direct commercial agreement with a
  professional issuer"* and instruments for *"a very limited range of goods or services"*. Recital 14 names
  *"store cards, fuel cards, membership cards … vouchers for specific services"* and adds: *"Instruments which can be
  used for purchases in stores of listed merchants should not be excluded … as such instruments are typically
  designed for a network of service providers which is continuously growing"*
  ([Directive (EU) 2015/2366, EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015L2366)).
- **[LAW] EMD2** *"does not apply to monetary value stored on instruments exempted as specified in Article 3(k)"*
  (art. 1(4)); otherwise e-money must be redeemed *"at any moment and at par value"* (art. 11(2))
  ([Directive 2009/110/EC, EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0110)).
- **[LAW] The Payment Services Regulation keeps the exclusion, narrowed.** The provisional agreement of 30 April
  2026 excludes instruments usable *"only in the premises, including physical premises or online stores, of the
  issuer or within a single limited network of service providers"*, and *"it should not be possible to use the same
  specific-purpose instrument … within more than one limited network"*; the Regulation would apply 21 months after
  entry into force ([Council doc. ST 9304/26, 18 May 2026](https://data.consilium.europa.eu/doc/document/ST-9304-2026-INIT/en/pdf)).
  **[ABSENT]** Publication in the Official Journal (not found by search on 2026-10-12).

### Poland — vouchers, passes, refunds, VAT
- **[LAW] No statutory expiry rule.** ECC Poland: *"W Polsce … nie ma przepisów regulujących w tym zakresie, datę
  ważności określa sprzedawca"* (no rules; the seller sets the validity) and *"sprzedawca nie ma obowiązku
  przedłużania ważności karty lub wypłacenia pieniędzy, gdy wygaśnie termin jej ważności"* (no duty to extend or pay
  out after expiry) ([ECC press release, 16 Dec 2019, on uokik.gov.pl](https://uokik.gov.pl/download/24056)).
- **[LAW] Abusive clauses.** Terms not individually agreed *"nie wiążą"* a consumer if they breach good practice and
  grossly harm his interests (art. 385¹ § 1); in case of doubt abusive are clauses that *"wyłączają obowiązek zwrotu
  konsumentowi uiszczonej zapłaty za świadczenie niespełnione w całości lub części, jeżeli konsument zrezygnuje …"*
  (exclude refunding payment for a service not performed when the consumer withdraws) (art. 385³ pkt 12)
  ([Kodeks cywilny, Dz.U. 2026 poz. 795](https://eli.gov.pl/api/acts/DU/2026/795/text/T/D20260795L.pdf);
  [ISAP](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260000795)).
- **[LAW] Limitation.** Six years, or three for claims tied to a business (art. 118); *"Terminy przedawnienia nie
  mogą być skracane ani przedłużane przez czynność prawną"* (a contract cannot shorten them) (art. 119); a benefit
  gained without legal basis must be returned (art. 405) ([same](https://eli.gov.pl/api/acts/DU/2026/795/text/T/D20260795L.pdf)).
  - *Reading:* an expiry date on a pass is a term of the contract, not a limitation period; whether a lapse that
    keeps the money is abusive is the court's call. A search of court portals found no Polish judgment on a sports
    pass or gift-card expiry that could be read at the source.
- **[LAW] VAT on vouchers.** A *"bon jednego przeznaczenia"* (single-purpose voucher: place of supply and VAT known at
  issue) is taxed when sold (art. 8a ust. 1); a *"bon różnego przeznaczenia"* (multi-purpose) only when redeemed
  (art. 8b ust. 1) (VAT Act art. 2 pkt 41–45 and art. 8a–8b, added by
  [Dz.U. 2018 poz. 2433](https://eli.gov.pl/eli/DU/2018/2433/ogl/pol/pdf)). Court time carries 8 % VAT (carried from
  `local-market.md`, *VAT on court time is 8 %*, read 2026-10-06).
  - *Reading:* a court-only pass at one club is single-purpose (VAT at sale); a wallet that also pays for drinks or
    rackets at 23 % is multi-purpose (VAT at use). MATCHi's two products follow exactly this split (below).

### Stripe
- **[POLICY]** Under *Restricted Businesses* (*"require additional due diligence"*): *"Sale of stored value or credits
  maintained, accepted and issued by anyone other than the seller. Seller-maintained stored value or credits may be
  subject to limits."* and *"Pre-loaded payment cards, gift cards, virtual credits or other products and services in
  which a monetary value is stored within the item"* ([Prohibited and Restricted Businesses, updated 2026-09-22](https://stripe.com/en-pl/legal/restricted-businesses)).
- **[DOCS]** Stripe's *customer invoice balance* is *"a balance on the customer that you can apply to future
  invoices"*; it does not apply to invoices from Checkout Sessions with `invoice_creation`
  ([Customer invoice balance](https://docs.stripe.com/billing/customer/balance)).
  - *Reading:* nothing in Stripe holds a player's wallet for card-present or PaymentIntent bookings; a wallet is a
    ledger Raketa keeps, with the money already on the seller's Stripe balance.

## Area 6 — prices

### A. The court-hour price table: bands, length, dated changes, holidays, VAT
**What it covers.** One price per court, sport, day and time band, by booking length; future-dated price lists;
public-holiday prices; gross prices with VAT included.

**Who has it.**
- **[POLICY] Playtomic:** rules per court, day, time range and length (*"Choose your time range (e.g., 60, 90, or 120
  minutes) and enter the prices for each"*), overlapping rules refused ([How to add and edit prices, updated
  2026-10-05](https://helpmanager.playtomic.com/hc/en-gb/articles/20535589805585)); a *Timed Price* has start and end
  dates, used *"during specific times, like summer or holiday periods"* ([Timed Prices](https://helpmanager.playtomic.com/hc/en-gb/articles/20535348126353));
  singles and doubles prices on one tennis court ([article, 2026-08-17](https://helpmanager.playtomic.com/hc/en-gb/articles/45291089794449));
  prices include VAT (carried, `competitor-club.md`, read 2026-10-06).
- **[POLICY] MATCHi:** a price list per sport with a *Start date*, hour-based or slot-based; *"Only one price list is
  active at a time per sport"*; price categories by *"time of day, weekday, court, lead time before booking"*; editing
  *"does not change the price of bookings already confirmed"* ([Create a price list, updated 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11470485625629)).
- **[POLICY] Eversports:** *"Under Profile > Holidays you can set the holidays and select what price you will be
  charging on that day (i.e. … the price of a Sunday)"* ([Start with Eversports Ballsport Manager](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] tenis4U:** price lists (*taryfy*) carry `starts_at`/`ends_at`; a booking that runs past one is refused:
  *"Data trwania stałej rezerwacji wykracza poza zakres danego cennika"* (the standing booking runs past this price
  list's range) ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)); no holiday field (carried,
  `gaps-COURTS.md`, read 2026-10-08).
- **[POLICY] kluby.org:** *"Dodanie dnia świątecznego do cennika"* (a public holiday as a price-list day, 2018) and
  *"Cenniki cykliczne"* (recurring-booking price lists) ([changelog 2018](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] Playmore:** shows each club's price per hour, *"Mogą się różnić w zależności od dnia"*, and a range when
  *"ta sama godzina kosztuje różnie — zależnie od kortu albo cennika (np. ulgowego)"* (the same hour costs differently
  by court or price list, e.g. a reduced one) ([web-app strings](https://playmore.pl/assets/BIIU90LQ.js)).

**The desk's day with it.** Prices are set once a season; Kraków lists change on 1 October and 1 May (Fame Sport,
Sport Factory Park, below). Playtomic and MATCHi leave confirmed bookings at their old price; tenis4U refuses a
standing booking that outruns its price list.

**What a Kraków desk does today.**
- **[PRICE]** Seasonal lists with dates printed: Fame Sport *"KORT HALA PADEL – ZIMA 01.10.2026 – 30.04.2027"*
  ([cennik](https://famesport.pl/cennik/)); Sport Factory Park *"ceny obowiązują od 01.10.2026r."* with *"ceny w trakcie
  sezonu zimowego mogą ulec zmianie"* (prices may change during the winter season) ([cennik](https://sportfactorypark.pl/cennik-tenis-2/));
  Atras *"Obowiązuje od 1.09.2026"* ([cennik](https://www.atrassquash.pl/cennik/)).
- **[PRICE]** One holiday rule found: Sport Factory Park's band *"Sobota, niedziela oraz święta"*
  ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)). Every other Kraków list is weekdays and weekends only
  (carried, `gaps-COURTS.md`, read 2026-10-08).
- **[PRICE]** Squash prices the 60-minute court with three to six bands a day; Squash4You and Miazga split Friday and
  Sunday from the rest ([Squash4You](https://playmore.pl/klub/squash4you/cennik/), [Miazga](https://playmore.pl/klub/miazga-squash/cennik/)).
  See the price table below.

**What it means for the player app.** A seat's share comes from the band the hour falls in; a dated list means a game
proposed for next month may carry next season's price. Atras's online 103,50 zł halves to 51,75 zł (carried,
`gaps-COURTS.md`).

**Market signal.** Table stakes (bands, length, dated lists, VAT-inclusive); holiday pricing is rare in Kraków.

### B. Online price vs desk price
**What it covers.** A lower price for a booking paid online than for one paid at reception.

**Who has it.**
- **[PRICE] Playmore clubs:** two columns *"Online"* and *"Na miejscu"* on every squash club's page
  ([Atras](https://playmore.pl/klub/atras-squash-club/cennik/), [Paolo](https://playmore.pl/klub/paolo-squash-club/cennik/)):
  *"Klub prowadzi dwa cenniki: internetowy i klubowy"* (the club keeps two price lists, online and club) (Paolo).
- **[ABSENT]** An online/desk price split in Playtomic's and MATCHi's help, tenis4U's panel strings, or kluby.org's
  changelog (searched "online", "desk", "recepcj", "na miejscu").
- **[COMPLAINT]** MATCHi: a court cost 90 kr on the website but 180 kr in the app (DK, 5 Jun 2026; carried,
  `games-and-fill-in-market.md`, read 2026-10-06).

**The desk's day with it.** The desk charges the club column; the online column is what the app takes.

**What a Kraków desk does today.**
- **[PRICE]** Atras: *"Rezerwując online płacisz mniej — zawsze 10% taniej, a z karnetem 15%"* (online always 10 %
  cheaper, 15 % with a pass); peak 103,50 zł online vs 115 zł at the desk ([cennik](https://www.atrassquash.pl/cennik/)).
- **[PRICE]** Squash4You: *"Rezerwacja online przez Playmore jest 15 zł tańsza niż płatność w klubie"*; peak 120 zł
  online vs 135 zł ([Playmore page](https://playmore.pl/klub/squash4you/cennik/)). In January 2025 the gap was 5 zł
  (carried, `local-market.md`, via Sportano).
- **[PRICE]** Paolo: *"Rezerwacja online jest o 5 zł tańsza niż opłata w recepcji"*; Miazga: the same price both ways
  ([Paolo](https://playmore.pl/klub/paolo-squash-club/cennik/), [Miazga](https://playmore.pl/klub/miazga-squash/cennik/)).
- **[PRICE]** Playmore adds *"opłatę serwisową 1,48 zł"* to online bookings at Atras and Squash4You and *"1,99 zł"* at
  Paolo (same pages).
- **[ABSENT]** An online/desk difference at any Kraków padel or tennis club (Fame Sport, Sport Factory Park, and the
  PADO and Playmore pages of Garden Padel, Bajada, Padel House, Morelowa 34, Libertów). Garden Padel's Playmore page
  shows desk prices only (*"Online —"*) ([page](https://playmore.pl/klub/garden-padel/cennik/)).

**What it means for the player app.** Every Raketa seat is paid online; *reading:* a squash club with two lists would
expect its online column to apply, and the app's share would differ from what the same player pays at the desk.

**Market signal.** Differentiator in Kraków squash, absent in padel and in the platforms' own feature sets.

### C. Members' prices, categories and memberships
**What it covers.** A cheaper price for a member, a club's players or a category of customer; memberships sold for a
fee, with booking privileges.

**Who has it.**
- **[POLICY] Playtomic:** a membership has a cost and frequency (*"One-off, Weekly, Monthly, Quarterly, or Yearly"*),
  grace days, privileges (*"Booking ahead days … Cancellation policy (in hours)"*) and pricing (*"Amount discount,
  Percentage discount, Price per hour, Price for all bookings"*); *"Players can pay the full booking with their
  benefit: We recommend keeping this disabled … When disabled, only split payments are allowed"*; *"the benefit …
  only applies to private bookings and open matches"* ([Club Membership Feature, 2026-09-13](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745));
  *"A player can only have one benefit at a time"* ([troubleshooting, 2026-09-22](https://helpmanager.playtomic.com/hc/en-gb/articles/46682341803409)).
- **[POLICY] MATCHi:** customer categories priced per price category; **Multiple Player Price** *"splits a court
  booking's cost among its players, so individual benefits like membership discounts apply to each player's own
  share"* — a 400 SEK padel court with a free-play member booking costs 300 SEK; missing spots are *"padded at the full
  price"*; only MATCHi staff can switch it on ([MPP, 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/16860340422429)).
- **[POLICY] tenis4U:** a *"Wariant cennika"* (price variant) can be tied to named players: *"Kiedy żaden gracz nie
  jest przypisany do wariantu cennika, to jest on widoczny dla wszystkich użytkowników"* ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] kluby.org:** a price list *"przypisany do klienta, obiektu czy klubu"* (2017; carried, `gaps-COURTS.md`).
- **[POLICY] Eversports:** *"Memberships can be used only for studio classes and not for court bookings"*
  ([help](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).

**The desk's day with it.** The desk enrols a member (Playtomic: *"clubs can also add or remove members manually"*)
and the price follows the player's account.

**What a Kraków desk does today.**
- **[PRICE]** Fame Sport tennis has a second row, *"Wstęp na kort dla zawodników"*, e.g. winter weekday 14–23 120 zł
  against 140 zł, for *"zawodników KS Grzegórzecki z aktualną licencją PZT lub wykupionym karnetem na dany miesiąc"*
  (club players with a federation licence or a monthly pass) ([cennik](https://famesport.pl/cennik/)).
- **[ABSENT]** A members' court price at any other club read, padel included.
- **[POLICY]** PADO says Garden Padel has *"three tiers — Casual Pass, Club Member, and Elite Player"*
  ([PADO](https://pado.app/poland/krakow/clubs/garden-padel-krakow)), but those tiers are a website template's
  placeholder: gardenpadel.pl lists them priced *"IDR 75K /session"* under *"the Padelo community"*
  ([gardenpadel.pl](https://gardenpadel.pl/)). *Reading:* not a real offer.

**What it means for the player app.** A member and a non-member in one Raketa game would pay different shares; MATCHi's
MPP is the only rival model for that, and it charges the booker, not each seat.

**Market signal.** Table stakes in the platforms; rare at Kraków padel and squash desks.

### D. Student, junior, senior and off-peak discounts; promo codes
**What it covers.** Reduced prices by status or hour, and codes that take money off.

**Who has it.**
- **[POLICY] Playtomic:** promo codes give *"a fixed amount off"* (*"Currently, only Amount discount is available"*),
  with usage limits and *"Promo usage hours … to keep discounts away from peak hours"*; *"Promos can't be edited after
  they're created"* ([Promo Codes, 2026-10-02](https://helpmanager.playtomic.com/hc/en-gb/articles/43779352948753)).
- **[POLICY] MATCHi:** a code is *"either a fixed amount or a percentage discount"*, with dates and per-customer limits
  ([Create Promo Code](https://matchi.zendesk.com/hc/en-gb/articles/14947335787677)).
- **[POLICY] Playmore:** *"Kody rabatowe mogą być procentowe albo kwotowe, jednorazowe albo z limitem użyć i datą
  końca"* (percentage or amount, single-use or capped, with an end date) ([join.playmore.pl FAQ](https://join.playmore.pl/)).

**The desk's day with it.** In Kraków the status discounts are given at reception against a document.

**What a Kraków desk does today.**
- **[PRICE]** Atras: *"Zniżka studencka 25% / 50%"* (one or two student cards), *"W tygodniu poza godzinami 17:00 –
  22:00 … Płatność tylko w recepcji"* (off-peak, desk only); *"Trening z trenerem taniej −10 zł"*; *"Promocje nie łączą
  się ze sobą"* ([cennik](https://www.atrassquash.pl/cennik/)).
- **[PRICE]** Squash4You: *"Studenci i uczniowie płacą mniej poza szczytem"*; *"Druga godzina −50%"* (Mon–Fri 16–23,
  ask at reception); *"Migrujące Happy Hours … Terminy ogłaszane na bieżąco"* (happy hours announced as they come)
  ([page](https://playmore.pl/klub/squash4you/cennik/)).
- **[PRICE]** Paolo: free equipment for students; Atras's *"Studenckie Integracje"* Fridays 30 zł (15 zł with a benefit
  card) ([Paolo](https://playmore.pl/klub/paolo-squash-club/cennik/), [Atras](https://playmore.pl/klub/atras-squash-club/cennik/)).
- **[PRICE]** Seniors: only through the card, *"Multisport Senior (do 16:00) −15 zł"* at Atras ([cennik](https://www.atrassquash.pl/cennik/)).
- **[ABSENT]** A student, junior or senior court price at any Kraków padel or tennis club read.

**What it means for the player app.** A student discount per head would make shares unequal, and Atras gives it only at
the desk.

**Market signal.** Differentiator (squash desks); promo codes are table stakes in the platforms.

### E. Dynamic pricing
**What it covers.** Prices that move with demand or occupancy, not set bands.

**Who has it.**
- **[ABSENT]** Playtomic: its help returns nothing for "surge" or "yield"; "demand" finds only Timed Prices, which are
  manual date ranges ([search API](https://helpmanager.playtomic.com/api/v2/help_center/articles/search.json?query=demand&locale=en-gb));
  its pricing strings have no such option ([pricing.json](https://manager.playtomic.io/locales/en/pricing.json)).
- **[POLICY] MATCHi:** a price category may depend on *"lead time before booking"*, and value and punch cards on
  *"Hours in advance"* ([price list](https://matchi.zendesk.com/hc/en-gb/articles/11470485625629),
  [value card](https://matchi.zendesk.com/hc/en-gb/articles/11673568781725)) — set rules, not demand.
- **[ABSENT]** Dynamic pricing at Playmore, tenis4U, kluby.org or Eversports (their strings, changelog and help).
  Smaller vendors (wakesys, On Spot, Bookaball) advertise it in marketing only.
- **[POLICY]** Playmore's terms: *"Ceny w Systemie nie są indywidualnie dostosowywane na podstawie zautomatyzowanego
  podejmowania decyzji — obowiązują wszystkich Użytkowników"* (prices are not individually set by automated
  decision-making; they apply to all users) (§8.7, [terms chunk](https://playmore.pl/assets/CjQyHVHG.js)).

**The desk's day with it.** Nothing to run: no rival offers it.

**What a Kraków desk does today.** Fixed bands plus ad hoc happy hours (Squash4You, above).

**What it means for the player app.** Nothing a club asks for today.

**Market signal.** Rare.

### F. Season and fixed-slot discounts (price side)
**What it covers.** A discount for paying a weekly hour for a season or a block of weeks up front.

**Who has it.**
- **[POLICY] Eversports:** *"Subscriptions … a subscription booking for a whole season Sept. to June on Monday
  evenings"*, sold only from the calendar ([help](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] MATCHi:** separate price lists for subscription bookings (*"Check this box if the price list should apply
  to subscription bookings"*) ([price list](https://matchi.zendesk.com/hc/en-gb/articles/11470485625629)).
- **[POLICY] tenis4U:** *"Dodawanie stałych terminów"* (carried, `integration.md` §5); kluby.org: *"Cenniki cykliczne"*
  ([2018](https://oferta.kluby.org/changelog?rok=2018)).

**The desk's day with it.** The desk sells the season once, from the calendar (Eversports), at the subscription price
list's rate (MATCHi), and the hours stay blocked all season.

**What a Kraków desk does today.**
- **[PRICE]** Fame Sport: *"Abonament na 1h w tygodniu na cały sezon zimowy/letni"* (one hour a week for the whole
  winter or summer season) 10 % off; *"Abonament na 1h w tygodniu na okres 12 tygodni"* 5 % off
  ([cennik](https://famesport.pl/cennik/)).
- **[PRICE]** Sport Factory Park: *"RABAT 10% na opłatę za kort PRZY PŁATNOŚCI Z GÓRY ZA TRENINGI ZA 6 MIESIĘCY"*,
  15 % for 12 months ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)).

**What it means for the player app.** Season hours are the desk's; they block the hours the deck could sell.

**Market signal.** Table stakes for tennis.

### G. Count passes (karnet ilościowy, punch card, block card)
**What it covers.** A pass for N hours or N entries, paid ahead, with an expiry.

**Who has it.**
- **[POLICY] MATCHi:** punch cards with a *"max duration setting (30, 60, 90, or 120 minutes)"* per punch, limits per
  day/week/month, conditions by date, weekday, time, court and hours in advance ([Punch card](https://matchi.zendesk.com/hc/en-gb/articles/11673307250205));
  a *"Summer card"* is a punch card with an end date or *"number of days valid (pre-filled with 365)"*
  ([Summer card](https://matchi.zendesk.com/hc/en-gb/articles/18666713630365)); its VAT is fixed at purchase
  ([VAT for punch cards](https://matchi.zendesk.com/hc/en-gb/articles/11720289322781)).
- **[POLICY] Eversports:** a block card *"allows the customer to book for a given number of credits, each credit
  corresponding to one slot"* ([help](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] Playmore:** *"Tworzysz karnety ilościowe, na przykład na 10 godzin, i kwotowe, każdy z terminem
  ważności. Gracz może kupić karnet w aplikacji i płacić nim za rezerwacje"* (count and amount passes, each with an
  expiry, bought and spent in the app) ([FAQ](https://join.playmore.pl/)); types *"Kwotowy / Czasowy / Ilościowy"*
  ([strings](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] tenis4U:** *"np. Karnet 10 wejść"*, *"Karnet wygasa po określonej liczbie dni od zakupu"* or *"Karnet
  nie wygasa po określonym czasie"*, *"Historia użycia karnetu"*, and withdrawal of a pass type ([panel](https://test-panel.tenis4u.pl/main.2b865c996e568707.js));
  players see *"Kup karnet i oszczędzaj na rezerwacjach"*, *"Saldo karnetów na ten termin"*, *"Brak środków na
  karnetach obejmujących ten termin"* (no balance on passes that cover this slot) ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js));
  the App Store's 4.9.1 (Oct 2026) added time passes (carried, `local-market.md`, read 2026-10-08).
- **[POLICY] kluby.org:** *"Brak możliwości rezerwacji na karnet jeśli nie ma się wystarczającej liczby godzin"*
  (2020), *"Wykupienie karnetu ONLINE"* (2021) ([2020](https://oferta.kluby.org/changelog?rok=2020),
  [2021](https://oferta.kluby.org/changelog?rok=2021)).
- **[COMPLAINT]** kluby.org: *"nie działa mój karnet"* (my pass doesn't work) (App Store PL, carried,
  `games-and-fill-in-market.md`, read 2026-10-06).

**The desk's day with it.** The desk creates pass types, sells them at reception or lets players buy them online, and
books against the balance (kluby.org: *"Szybkie dodawanie karnetu podczas rozliczania rezerwacji"*, 2021,
[changelog](https://oferta.kluby.org/changelog?rok=2021)); expiries and extensions are handled by hand (Squash4You,
below).

**What a Kraków desk does today.**
- **[POLICY]** Atras: passes *"Ograniczone są 2-, 4- lub 6-miesięcznym terminem ważności … a opłacony karnet nie
  podlega zwrotowi lub zamianie"* (2-, 4- or 6-month validity; a paid pass is not refunded or exchanged)
  ([regulamin](https://www.atrassquash.pl/regulamin/)).
- **[POLICY]** Squash4You: passes are personal, time-limited and not refunded except *"gdy Klub zawiesił usługi na
  okres przekraczający 7 dni"* (club closed over 7 days: pro-rata refund or extension) or documented illness;
  extension costs *"19,00 zł brutto"* for 30 days, *"29,00 zł"* for 60 ([regulamin §9–11](https://www.squash4you.pl/regulamin)).
- **[ABSENT]** A court count pass at any Kraków padel club; Garden Padel *"Karnet / pakiet godzin — do ustalenia"*
  (to be agreed) ([page](https://playmore.pl/klub/garden-padel/cennik/)).

**What it means for the player app.** A pass pays one booker's whole court; Raketa's game splits a court in seats.
*Reading:* a pass would need to pay one seat, or the desk keeps passes for its own bookings.

**Market signal.** Table stakes in squash and tennis software; rare in Kraków padel.

### H. Value passes and the club wallet (karnet wartościowy, value card, Club Wallet)
**What it covers.** Money paid in ahead, often with a bonus, spent on bookings at that club, with or without expiry.

**Who has it.**
- **[POLICY] Playtomic Club Wallet:** *"Recharge packs … The recharge amount is the balance added … the price is what
  the player pays (e.g. price €50, amount €60)"*; wallets restricted by *"specific courts, sports, time"*
  ([setup, 2026-09-25](https://helpmanager.playtomic.com/hc/en-gb/articles/20535667026961)); optional expiry per top-up
  since August 2026, *"the credit closest to expiring is always used first"*, a refund to an expired top-up *"is lost
  right away"* ([top-up expiration, 2026-08-24](https://helpmanager.playtomic.com/hc/en-gb/articles/49347788251153));
  *"The wallet must cover the full payment amount"*, *"Wallets can only be used at the club where the balance is
  held"*, and no fees on spending it ([how players use wallets, 2026-10-05](https://helpmanager.playtomic.com/hc/en-gb/articles/46724768519953)).
  The player help still says *"No expiration: Your credit never expires"* and *"Each club decides whether to approve or
  deny refund requests, as Club Wallets are managed by the club, not by Playtomic"*
  ([What is the Club Wallet?, 2026-08-19](https://playerhelp.playtomic.com/hc/en-gb/articles/19831817632273)).
  A monthly *Recurring Wallet Benefit* *"Resets"* or *"Accumulates"* ([article](https://helpmanager.playtomic.com/hc/en-gb/articles/37631478400401)).
- **[POLICY] MATCHi value card:** *"1 credit = 1 unit of your venue's currency"*, validity *"a fixed number of days
  from purchase, or a specific end date"*, purchase price per customer category, *"Use it to sell gift cards,
  corporate health-benefit credits, or promotional credit bundles"* ([Create value card, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11673669415453));
  *"No VAT is charged when a customer purchases a value card. VAT is applied when the card is used"*
  ([VAT for value cards](https://matchi.zendesk.com/hc/en-gb/articles/11720261581085)); it can pay a player's share of a
  split booking ([split payment, 2026-09-09](https://matchi.zendesk.com/hc/en-gb/articles/19335714618653)).
- **[POLICY] Eversports:** value vouchers, *"You can create vouchers with 0% VAT, as taxes will be applied when the
  voucher is redeemed"* ([help](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] tenis4U:** vouchers with `value` and `balance` on the player's account, and refunds *"Środki zostaną
  zwrócone na karnet, którym opłacono rezerwację"* (returned to the pass that paid) ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)).
- **[COMPLAINT]** Playtomic PL: wallet credit cannot be combined with another payment and the minimum top-up is 200 zł
  (App Store PL, 2026-07-16; carried, `games-and-fill-in-market.md`).

**The desk's day with it.** The desk sells a top-up, marks it paid, edits balances (Playtomic: *"Balance edits are not
recorded in the Payments list"*) and refunds into the wallet ([managing balances](https://helpmanager.playtomic.com/hc/en-gb/articles/46724086196881)).

**What a Kraków desk does today.**
- **[PRICE]** Squash4You: *"Karnet wartościowy 600 zł"* for 495 zł, *"Doładowanie taniej — na koncie 600 zł do wykorzystania na grę"*; also 700
  for 585, 850 for 720, 1200 for 1035 ([page](https://playmore.pl/klub/squash4you/cennik/)).
- **[PRICE]** Paolo: *"Doładowanie konta w klubie: płacisz 500 zł, do wykorzystania masz 550 zł. Ważny 90 dni"*; 750
  for 850 (90 days); 1000 for 1150, *"dłuższa ważność — 120 dni"*, usable on courts and classes ([page](https://playmore.pl/klub/paolo-squash-club/cennik/)).
- **[ABSENT]** A value pass at any Kraków padel or tennis club read.

**What it means for the player app.** A wallet would be a payment method for a seat. *Reading:* Playtomic's rule that
the wallet must cover the whole amount would make a 37,50 zł seat payable only with ≥ 37,50 zł left.

**Market signal.** Table stakes in the platforms; a differentiator in Kraków squash.

### I. A wallet or credit that crosses clubs
**What it covers.** One balance spendable at several clubs, held by the platform or a chain.

**Who has it.**
- **[POLICY] Playmore:** *"Środkami z portfela opłacisz rezerwację w dowolnym klubie na Playmore"* (pay at any
  Playmore club); funds come from card deposits and refunds — *"W klubach z portfelem Playmore pieniądze nie wracają na
  kartę płatniczą"*; *"„Zleć wypłatę" → numer konta → kod SMS. To Twoje pieniądze, możesz je wyprowadzić w każdej
  chwili"* (withdraw to a bank account at any time) ([strings](https://playmore.pl/assets/BIIU90LQ.js)). Terms §9:
  *"Rozliczenia Playmore to wewnętrzny system płatności … funkcjonalność ta nie stanowi świadczenia usług płatniczych
  ani bankowych"*; *"Saldo Playmore nie może przekraczać limitu PLN 10 000"*; a *"Kaucja … Zbiorcza (jednocześnie na
  rzecz wielu Partnerów)"* for up to 12 months; transfers to the recipient *"nie dłużej niż 30 dni od zlecenia"*
  ([terms chunk of playmore.pl/legal/terms-of-service](https://playmore.pl/assets/CjQyHVHG.js)). Refunds land there
  and *"Opłata serwisowa nie podlega zwrotowi"* (carried, `platforms.md`, read 2026-10-07).
- **[POLICY] Playtomic Chain Wallet:** *"top up once and spend their balance at any club in your chain"*; with several
  legal entities *"the chain may need to reconcile between companies"* ([Chain Wallets, 2026-07-31](https://helpmanager.playtomic.com/hc/en-gb/articles/46485752572817)).
  The platform's own wallet is closed: *"It is no longer possible to top up the Playtomic Wallet"* (carried,
  `games-and-fill-in-market.md`, read 2026-10-06).
- **[POLICY] MATCHi:** value cards work *"at the venue that issued it, and at venues in the same master/local chain
  group"* ([split payment](https://matchi.zendesk.com/hc/en-gb/articles/19335714618653)); gift cards bought through its
  wellness partners (Benifex, Epassi, Edenred, Benefits) *"can be used at any participating MATCHi venue"*
  ([wellness benefits](https://matchi.zendesk.com/hc/en-gb/articles/13991290310557)).
- **[ABSENT]** A KNF register entry for Reservise (Playmore) or a statement of the legal basis of its wallet beyond §9;
  the register's search ([e-rup.knf.gov.pl](https://e-rup.knf.gov.pl/)) runs by form POST and was not used.

**The desk's day with it.** A chain reconciles balances between its companies from a CSV (Playtomic); a Playmore club
does nothing — the balance is Playmore's.

**What a Kraków desk does today.** Nothing of its own; Playmore clubs' refunds already flow into Playmore's balance.

**What it means for the player app.** *Reading:* a Raketa credit spent at many clubs is Raketa's liability under the
limited-network test and Stripe's restricted list (see *The law*); a per-club wallet is the club's.

**Market signal.** Rare (Playmore in Poland; chains only elsewhere).

### J. Gift vouchers (bony podarunkowe)
**What it covers.** A voucher bought for someone else.

**Who has it.**
- **[POLICY] MATCHi:** value cards *"to sell gift cards"* ([Create value card](https://matchi.zendesk.com/hc/en-gb/articles/11673669415453));
  Eversports: vouchers (above); Playmore's terms list *"vouchery"* among what the balance pays
  ([terms chunk](https://playmore.pl/assets/CjQyHVHG.js)); Playtomic: no gift cards — *"a club can add credit to a
  player's Club Wallet instead"* (carried, `games-and-fill-in-market.md`).

**The desk's day with it.** A gift card is a value card the desk issues by hand or sells online (MATCHi).

**What a Kraków desk does today.**
- **[ABSENT]** A gift voucher on the price pages of Fame Sport, Atras, Squash4You, Paolo, Miazga, Sport Factory Park,
  Garden Padel, Bajada, or the PADO pages of Padel House, Morelowa 34, Libertów (searched "podarunk", "voucher",
  "bon").

**What it means for the player app.** None today.

**Market signal.** Rare in Kraków.

### K. Refunds into the wallet instead of the card
**What it covers.** A cancelled booking's money returning as credit, not to the card.

**Who has it.**
- **[POLICY] Playtomic:** a club on Professional or higher may refund to the player's Club Wallet instead of the card,
  which causes no negative payout (carried, `games-and-fill-in-market.md`, read 2026-10-06).
- **[POLICY] Playmore:** weather cancellations: *"cena rezerwacji opłaconej online wraca do gracza na portfel"*
  ([FAQ](https://join.playmore.pl/)); terms §5.4: when the club is at fault the player chooses *"zwrot … na swój
  rachunek bankowy"* or the balance ([terms chunk](https://playmore.pl/assets/CjQyHVHG.js)).
- **[POLICY] tenis4U:** a cancelled online payment comes back *"pomniejszonych o opłatę transakcyjną w wysokości 2%"*
  (carried, `platforms.md`); a pass-paid booking returns to the pass ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)).

**The desk's day with it.** The desk picks the refund route when it cancels (Playtomic) or the system sends it to the
wallet by default (Playmore); no bank refund to chase.

**What a Kraków desk does today.**
- **[POLICY]** Squash4You moves a prepaid booking cancelled in time to the next booking rather than refunding it
  (carried, `local-market.md`, read 2026-10-06).

**What it means for the player app.** Raketa refunds to the card in full today; *reading:* a wallet would let a club
keep the money, which is what clubs on Playtomic and Playmore choose.

**Market signal.** Differentiator.

## Area 10 — benefit sports cards

### L. Taking a card at the desk: registering the visit and being paid
**What it covers.** How a facility checks a card, registers the visit and is paid for it.

**Who has it (the operators).**
- **[POLICY] MultiSport:** *"Przy recepcji należy okazać kod QR z aplikacji mobilnej MultiSport lub plastikową kartę
  MultiSport, a także dokument potwierdzający tożsamość"*; *"Jeśli na terminalu pojawi się komunikat „Wizyta
  zarejestrowana x minut temu""*; Classic one entry a day, Plus *"kilka razy dziennie"*
  ([Wejście do obiektu](https://pomoc.emultisport.pl/pl/articles/392787-wejscie-do-obiektu-sportowego)); dopłaty
  (surcharges) are per facility and *"nie ma możliwości zapisów przez aplikację MultiSport"* (no sign-ups through the
  MultiSport app) ([Zasady korzystania](https://pomoc.emultisport.pl/pl/articles/392855-zasady-korzystania-z-obiektow)).
- **[DOCS] Benefit Systems' partner terms** require at reception *"Możliwość montażu terminala do kart MultiSport"*
  (room to install a MultiSport card terminal); squash and tennis are on the list of services
  ([Warunki współpracy dla Partnerów](https://corp.benefitsystems.pl/fileadmin/benefitsystems/dokumenty/Warunki-wspolpracy-dla-Partnerow.pdf)).
  The partner portal has a *"Virtual Visit Form for registering MultiSport card holders' visits"*, a *"Billing module
  for settling MultiSport card holders' visits"* and a *"Counter of registered visits"* (the PDF's two-column layout pairs each tool with its purpose)
  ([Partner Zone](https://corp.benefitsystems.pl/fileadmin/benefitsystems/Dla_Partnera/2022/Strefa_Partnera_EN.pdf)).
- **[POLICY] Medicover Sport** (formerly OK System: *"OK System zmienił się w Medicover Sport"*,
  [history](https://medicoversport.pl/historia-rebrandingu)): *"Rejestracja wejścia … odbywa się poprzez kod QR
  generowany w aplikacji mobilnej Użytkownika lub wysłanie sms … Potwierdzenie … pojawia się jednocześnie – w aplikacji
  lub telefonie Partnera i Użytkownika"*; *"Raz w miesiącu, opłacimy każde zrealizowane wejście na podstawie wystawionej
  przez Ciebie faktury"* (once a month we pay every visit against your invoice); joining is free; a partner app
  *"MEDICOVER SPORT PARTNERZY"* registers and cancels entries ([Dla partnera](https://medicoversport.pl/partner)). Its
  user rules: entry registered *"nie wcześniej niż 15 … minut przed jej rozpoczęciem"* (carried, `local-market.md`,
  read 2026-10-06).
- **[POLICY] PZU Sport:** partners contract with *PZU Pomoc*; an *"Interfejs"* is *"dedykowane Klientom i Partnerom
  narzędzie umożliwiające m.in. … rejestrację Wstępów"*; an entry may be cancelled within 10 minutes; without a stated
  length *"czas trwania usługi wynosi nie mniej niż 60 minut"* ([Zasady, from 20 Sep 2023](https://sport.pzu.pl/_fileserver/item/1513976)).
- **[POLICY] FitProfit / FitSport** are VanityStyle's cards (fitprofit.pl redirects to it); *"VanityStyle jest częścią
  grupy kapitałowej Benefit Systems"* ([vanitystyle.pl](https://www.vanitystyle.pl/programy/programy-sportowe)).
- **[DOCS]** Card volume: 1 902,7 thousand active MultiSport cards in Poland at end of Q3 2026 (carried,
  `local-market.md`, read 2026-10-08).

**The desk's day with it.** The player shows the card or app QR with ID; the desk registers a visit on the operator's
terminal, partner app or online form; the operator pays monthly for registered visits.

**What a Kraków desk does today.**
- **[PRICE]** Sport Factory Park, in the operators' own wording: *"Benefit system współfinansuje wynajem kortu do
  tenisa ziemnego dopłaca po 15 PLN za każdego użytkownika karty MultiSport (maksymalnie dwóch użytkowników karty na
  jeden kort)"*, *"raz dziennie"*; *"Medicover SPORT współfinansuje wynajem kortu … dopłatą po 15 PLN za każdego
  użytkownika karty Medicover SPORT ( nie ma limitu użytkowników karty na jeden kort, suma dopłat nie może tylko
  przekroczyć całości kwoty za wynajem kortu)"*, *"jeden raz na 60 minut"* ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)).
- **[POLICY]** Playmore's own explanation: *"Klub dostaje pieniądze od operatora karty tylko za odbite wejście"*
  ([strings](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY]** Playmore's pitch against the status quo: *"Multisport i FitProfit na zeszyt: recepcja spisuje numery
  kart, a na koniec miesiąca ktoś skleja raport"* (carried, `integration.md` §4).
- **[ABSENT]** The rate Benefit Systems pays per fitness visit, or any partner contract (Partner Zone needs a login;
  no Kraków municipal contract found).

**What it means for the player app.** The discount is real money from the operator, earned only by a registered visit
on the day, at the club.

**Market signal.** Table stakes at every Kraków club read.

### M. Declaring cards in an online booking
**What it covers.** The player says, when booking, how many card holders will play, and pays the reduced price.

**Who has it.**
- **[POLICY] tenis4U:** the booking summary has *"Karty Multisport"* and *"Karty Medicover"* selectors from 0 to a
  maximum (*"maxMultisportCards = 2; // wartość domyślna"*, Medicover 2, FitProfit 0, *"Nowe API - dynamiczne limity
  kart benefitowych"*); *"Dla kart multisporta minimalny czas rezerwacji wynosi 60 minut"*; courts flag
  *"Obsługa kart multisport"* / *"Obsługa kart medicover"* ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js));
  the panel shows *"Karta benefit."* and the discount per card ([panel](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] Playmore:** *"Gracz podaje przy rezerwacji, ile osób wchodzi z kartą Multisport albo FitProfit. Kartę
  odbija się przy wejściu, a zestawienia generują się w panelu raportów"* (the player gives the number of card
  holders; the card is stamped on entry; reports build themselves) ([FAQ](https://join.playmore.pl/)) — what its squash
  page calls *"Karty zniżkowe weryfikowane automatycznie przy rezerwacji"* ([dla klubów squasha](https://join.playmore.pl/dla-klubow-squasha/)).
  Its club pages carry *"Limit kart … max {maxCards} karty"* and *"-{discount} zł za każdą odbijaną kartę"*
  ([strings](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] Playmore's card deposit, since August 2026:** *"przy rezerwacji widzisz cenę z kartami i płacisz do niej
  kaucję za karty. Kaucja wraca tutaj, na portfel, zaraz po odbiciu karty w recepcji"* (you see the price with cards
  and pay a deposit for them, returned to the wallet once the desk stamps the card); *"bez odbicia kart kaucja nie
  wraca"*; *"Kaucja wraca na Twój karnet dzień po odbiciu karty"*; *"Od sierpnia 2026 wszystkie kluby rozliczają karty
  tak samo"* — earlier *"część klubów dawała zniżkę od razu i traciła pieniądze, gdy karty potem nie odbito"*
  ([strings](https://playmore.pl/assets/BIIU90LQ.js)).
- **[POLICY] Playtomic:** cards only through the club's own provider deal and a user category; the providers named are
  none of the Polish ones ([Third-Party Membership Benefits](https://playerhelp.playtomic.com/hc/en-gb/articles/44586083037201)).
  **[COMPLAINT]** *"Brak integracji multisport"*; *"Add Medicover cards"* (Playtomic PL reviews, carried,
  `games-and-fill-in-market.md`).
- **[POLICY] kluby.org:** only flags a club that takes Multisport (*"Oznaczanie możliwości korzystania z kart … Multisport
  w klubie"*, 2022) ([changelog 2022](https://oferta.kluby.org/changelog?rok=2022)).

**The desk's day with it.** The desk still stamps each card before play; Playmore turns the stamp into the refund of
the deposit.

**What a Kraków desk does today.**
- **[PRICE]** Paolo: *"Rezerwując online, płacisz pełną cenę, a równowartość zniżki wraca na Twój portfel Playmore po
  weryfikacji karty w recepcji"*; *"Kort wieczorem z dwiema kartami 80 zł zamiast 110 zł"* ([page](https://playmore.pl/klub/paolo-squash-club/cennik/)).
- **[POLICY]** Atras: *"Kartę okazujesz w recepcji przed grą"* ([cennik](https://www.atrassquash.pl/cennik/)); Fame
  Sport: card users meet the operator's conditions *"przed rozpoczęciem gry"* (carried, `local-market.md`).
- **[POLICY]** Squash4You: *"Karta partnerska nie zastępuje rezerwacji kortu"* and *"W razie niestawiennictwa lub
  nieterminowej anulacji Klient nie może posłużyć się kartą partnerską i podlega pełnym opłatom"* (no-show or late
  cancel: no card, full price) ([regulamin §11](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** A seat could carry a declared card. *Reading:* Raketa holds each share until the
cut-off and charges it; Playmore's deposit is the same shape — charge the full share, return the card's 15 zł after
the desk stamps it.

**Market signal.** Differentiator (tenis4U and Playmore have it; Playtomic does not).

### N. Medicover Sport verified by phone number
**What it covers.** Checking a Medicover holder against Medicover's system rather than by eye.

**Who has it.**
- **[POLICY] tenis4U:** *"Podaj numery telefonów przypisane do kart Medicover"*; *"Aktywacja karty Medicover jest możliwa
  w 30-minutowym oknie czasowym tj. 15 min przed rozpoczęciem rezerwacji do 15 min od rozpoczęcia rezerwacji"*;
  *"Medicover zweryfikowany"*, *"Nie udało się zweryfikować kart Medicover"*, *"Ten kort nie obsługuje weryfikacji
  Medicover"* ([app](https://app.tenis4u.pl/main.cf446af5e9523413.js)); the panel shows *"✅ Wszystkie karty Medicover
  zaakceptowane"* or *"karta Medicover czeka na weryfikację"* ([panel](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[DOCS] eFitness's guide (10 Jun 2026):** data *"otrzymasz bezpośrednio od Medicover Sport: Oficjalna zgoda na
  integrację. X-AUTH-TOKEN (tzw. facility token)"*; *"Numer telefonu jest unikalnym identyfikatorem w systemie
  Medicover"*; a visit left within 15 minutes is cancelled automatically
  ([Integracja z Medicover Sport](https://efitness.pl/baza-wiedzy/integracja-z-medicover-sport-kompletny-przewodnik/)).
  The *"Merchant ID"* carried in `integration.md` §4 is not in the current text.

**The desk's day with it.** The player activates the card in the app around the start; the desk sees the result on the
booking instead of typing numbers.

**What a Kraków desk does today.** Desks on tenis4U see the verification status per booking; other desks register the
visit in Medicover's partner app ([Dla partnera](https://medicoversport.pl/partner)).

**What it means for the player app.** Verification can only happen around the start of play, not when a game fills days
ahead.

**Market signal.** Differentiator (tenis4U only among court platforms).

### O. Entry-check integrations with the card operators
**What it covers.** Software that asks MultiSport, Medicover Sport, FitProfit or PZU Sport whether a holder may enter.

**Who has it.**
- **[DOCS] eFitness ↔ MultiSport (4 Sep 2026):** *"Poproś MultiSport o wygenerowanie tzw. ClientId (indywidualny
  identyfikator Twojego klubu)"* after *"kontakt z Twoim opiekunem w Benefit Systems … w celu uzyskania zgody na
  integrację"*; the gate opens *"Jeśli wizyta zostanie pozytywnie zweryfikowana przez system MultiSport PL"*; the phone
  number is the identifier ([Integracja z MultiSport](https://efitness.pl/baza-wiedzy/integracja-z-multisport-kompletny-przewodnik/)).
- **[DOCS] eFitness ↔ FitProfit:** *"Integracja z FitProfit jest dostępna dla klubów, które korzystają już z integracji z
  MultiSport"* ([guide](https://efitness.pl/baza-wiedzy/integracja-z-fitprofit-kompletny-przewodnik/)).
- **[POLICY] GYMMANAGER:** *"integrates with leading partners such as Benefit Systems, Medicover, and PZU Sport"*, plus
  BeActive, for *"Automatic entry verification"* ([integrations](https://gymmanager.io/system-integrations-in-sports-facilities/)).
- **[ABSENT]** Public developer documentation or a vendor programme from Benefit Systems, Medicover Sport, VanityStyle
  or PZU Sport ([Benefit Systems partners](https://corp.benefitsystems.pl/en/for-partners/), [Medicover Sport partner](https://medicoversport.pl/partner)).
- **[ABSENT]** A court platform that verifies MultiSport with Benefit Systems at booking time (tenis4U and Playmore take a
  declared count).

**The desk's day with it.** At a gym the gate opens on the operator's yes and nobody at reception touches the card.

**What a Kraków desk does today.** Registers visits on the operator's terminal or app (section L); no Kraków court club
was found with a gate integration.

**What it means for the player app.** *Reading:* the route is per club: each club asks its operator's account manager for
consent and a key, and the software uses it. This revises `integration.md` §4's *"[ABSENT] A booking integration
between Benefit Systems (MultiSport) and club software"*: entry-check integrations exist; booking-time ones were not
found.

**Market signal.** Table stakes in gym software; rare in court software.

### P. Cards in a shared booking: limits and who gets the discount
**What it covers.** How many cards a court takes, and how a card discount sits with per-player payment.

**Who has it.**
- **[POLICY] tenis4U:** shared bookings say *"Każdy uczestnik płaci swoją część"* and *"Po opłaceniu przez organizatora
  będziesz mógł zapłacić swoją część"*, and show *"Rabat karta"* and *"2x Multisport"*
  ([reservation module](https://app.tenis4u.pl/src_app_routes_reservation-v3_reservation-v3_module_ts.b8c3629f5a4e1beb.js)).
  **[ABSENT]** Whose part the card discount reduces.
- **[POLICY] MATCHi:** with MPP, *"individual benefits like membership discounts only apply to that player's portion"*
  ([MPP](https://matchi.zendesk.com/hc/en-gb/articles/16860340422429)); wellness cards are converted into value cards,
  which can pay a share ([wellness](https://matchi.zendesk.com/hc/en-gb/articles/13991290310557)).
- **[POLICY] Playmore:** the deposit returns to the wallet of the player who declared the cards ([strings](https://playmore.pl/assets/BIIU90LQ.js)).

**The desk's day with it.** The desk counts cards against the court's limit and stamps each holder; the rest of the
price is the booker's or is split.

**What a Kraków desk does today.**
- **[PRICE]** Two cards a court at most: Atras *"na jeden kort możesz użyć maksymalnie dwóch kart"* ([own page](https://www.atrassquash.pl/cennik/)),
  though its Playmore page says *"Maksymalnie 2 karty jednego partnera na kort"* (two per operator) ([Playmore](https://playmore.pl/klub/atras-squash-club/cennik/));
  Miazga *"maks. 2 karty na kort"*; Squash4You *"Przy zajęciach grupowych maksymalnie 2 osoby z kartą na kort"*;
  Sport Factory Park MultiSport two, Medicover unlimited up to the court price (pages above).
- **[PRICE]** Padel: Padel House *"all variants of the MultiSport card are accepted with a 15 PLN discount"*, no limit
  stated ([PADO](https://pado.app/poland/krakow/clubs/padel-house-krakow)); Garden Padel *"honoruje karty Multisport i
  Medicover. Zasady i dostępność potwierdza recepcja"* ([Playmore](https://playmore.pl/klub/garden-padel/cennik/)).
- **[POLICY]** Fame Sport: *"Rabat z kart partnerskich (Multisport Plus, Medicover Sport, MyBenefit) naliczany jest od
  ceny regularnej i nie łączy się z innymi rabatami"* ([cennik](https://famesport.pl/cennik/)); Paolo: *"Ceny promocyjne
  za płatność online nie łączą się z innymi zniżkami"* yet refunds the card's 15 zł on online bookings ([page](https://playmore.pl/klub/paolo-squash-club/cennik/)).
- *Reading:* four padel players, two with MultiSport, at Padel House's 160 zł peak: the court costs 130 zł; split
  equally that is 32,50 zł each, while the card holders expect their own 15 zł — 25 zł for them, 40 zł for the others.

**What it means for the player app.** Equal shares and per-seat card discounts conflict; the share would have to depend
on the seat.

**Market signal.** Table stakes at the desk; unsolved in every platform read.

## Kraków price table

Court-hour prices in zł, gross, read 2026-10-12. "Own" = the club's site; "PM" = Playmore's page (*"Stawki
orientacyjne"*; for tenis4U clubs written by Playmore); "PADO" = PADO's listing.

| Club | Sport | Weekday | Weekend | Peak / off-peak | Member | Online vs desk | Card rule | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fame Sport | padel, hall, winter 1.10.2026–30.04.2027 | 135 (7–14), 150 (14–23) | 140 | 150 / 135 | — | none published | Multisport Plus, Medicover Sport, MyBenefit off the regular price, no stacking; 15 zł per PADO | [own](https://famesport.pl/cennik/), [PADO](https://pado.app/poland/krakow/clubs/fame-sport-club-krakow) |
| Fame Sport | padel, outdoor, summer 2026 | 100 | 100 | — | — | — | as above | [own](https://famesport.pl/cennik/) |
| Fame Sport | tennis, hall, winter | 120 (7–11), 100 (11–14), 140 (14–23) | 125, 125, 110 (16–23) | 140 / 100 | 100 / 85 / 120; weekend 105 / 105 / 100 | — | as above | [own](https://famesport.pl/cennik/) |
| Fame Sport | badminton, winter | 70 (7–10), 60 (10–16), 90 (16–23) | 90 | 90 / 60 | — | — | as above | [own](https://famesport.pl/cennik/) |
| Sport Factory Park | tennis, hall, from 1.10.2026 | 120 (7–11), 100 (11–14), 130 (14–23) | 130 (7–15), 120 (15–23), also holidays | 130 / 100 | — | — | MultiSport 15 zł per user, max 2 per court, once a day; Medicover 15 zł per user, no cap up to the court price, once per 60 min | [own](https://sportfactorypark.pl/cennik-tenis-2/) |
| Garden Padel | padel, outdoor, from 1 May | 50 (8–9), 100 (9–15), 130 (15–23) | 130 | 130 / 100 | — | desk only shown | Multisport, Medicover "honoured", amount not stated | [PM](https://playmore.pl/klub/garden-padel/cennik/), [PADO](https://pado.app/poland/krakow/clubs/garden-padel-krakow) |
| Bajada | padel, outdoor | 80 (day), 100 (evening) | 100 | 100 / 80 | — | — | MultiSport "wg zasad programu" | [PADO](https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow), [PM](https://playmore.pl/klub/bajada-sports-club/cennik/); indoor **[ABSENT]** |
| Padel House | padel, indoor | 120 (7–16), 160 (16–24) | 160 | 160 / 120 | — | — | all MultiSport variants −15 zł | [PADO](https://pado.app/poland/krakow/clubs/padel-house-krakow) |
| Morelowa 34 | padel, indoor | 140 (7–17), 160 (17–23) | 160 | 160 / 140 | — | — | MultiSport accepted | [PADO](https://pado.app/poland/krakow/clubs/morelowa-34-padel-krakow) |
| Libertów | padel, indoor | 100 (0–16), 110 (16–24) | 100 | 110 / 100 | — | — | none stated | [PADO](https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club) |
| Atras | squash, from 1.09.2026 | online/desk 54/60 (7–10), 45/50 (10–16), 63/70 (16–17), 103,50/115 (17–22), 63/70 (22–23), 45/50 (23–24) | 72/80 (8–22) | 103,50 / 45 online | pass: 15 % off online | 10 % online, 15 % with a pass; +1,48 zł online fee | Multisport Plus/Classic/Student/Light, MultiActive, Senior (to 16:00), Medicover, FitProfit, PZU −15 zł each, max 2 per court | [own](https://www.atrassquash.pl/cennik/), [PM](https://playmore.pl/klub/atras-squash-club/cennik/) |
| Squash4You | squash | Mon–Thu online/desk 75/90 (7–11), 65/80 (11–16), 100/115 (16–17), 120/135 (17–22), 85/100 (22–23), 60/75 (23–24); Fri peak 17–20 | Sat 70/85, 85/100, 60/75; Sun the same from 8:00 | 120 / 60 online | value passes 495→600 … 1035→1200 | 15 zł online; +1,48 zł fee | Multisport, Medicover, FitProfit, PZU −15 zł | [PM](https://playmore.pl/klub/squash4you/cennik/) |
| Paolo | squash | online/desk 70/75 (8–10), 40/45 (10–16), 70/75 (16–17), 110/115 (17–22), 70/75 (22–23), 40/45 (23–24) | 70/75 (8–10), 55/60 after | 110 / 40 online | value passes 500→550, 750→850 (90 days), 1000→1150 (120 days) | 5 zł online; +1,99 zł fee | MultiSport or Medicover −15 zł each hour with ID; online: full price, 15 zł back to the wallet after the desk checks | [PM](https://playmore.pl/klub/paolo-squash-club/cennik/) |
| Miazga | squash | 45 (7–16), 65 (16–17), 95 (17–22), 65 (22–24); Fri 75 (17–20) | Sat 50/60/50; Sun 50/65/50/65 | 95 / 45 | — | none | Multisport, FitProfit, Medicover −15 zł, max 2 | [PM](https://playmore.pl/klub/miazga-squash/cennik/) |
| Park Jordana | tennis | **[ABSENT]** | | | | | | [PM](https://playmore.pl/klub/kort-w-parku-jordana/) (no prices); ZZM's site none |
| Racquet | squash | **[ABSENT]** on its own site (404) | | | | +5 zł at the desk (Sportano, Jan 2025; carried) | | carried, `local-market.md` |

*Reading:* padel runs 100–160 zł a court-hour (25–40 zł a seat for four); squash 40–135 zł for two; a card takes 15 zł off a
seat's share, which is up to 60 % of an off-peak squash seat (25 zł with a card instead of 40 zł at Paolo).

## Rivals × features

| Feature | Playtomic | MATCHi | Eversports | Playmore | tenis4U | kluby.org |
| --- | --- | --- | --- | --- | --- | --- |
| A. Bands, length, dated lists | yes; Timed Prices | yes; start-dated lists | yes; holiday = chosen day | shows club lists | yes; dated tariffs | yes; holiday day (2018) |
| B. Online vs desk price | no | no | no | yes, per club | not found | not found |
| C. Member / category price | yes (benefits, memberships) | yes; MPP per seat | classes only | "cennik ulgowy" | price variant per player | per client (2017) |
| D. Promo codes | amount only, hours | amount or % | voucher codes | % or amount | voucher discount | not found |
| E. Dynamic pricing | no | lead-time condition | no | no | no | no |
| F. Season discount | recurring bookings (price not read) | subscription price lists | subscriptions | via club | standing bookings | recurring price lists |
| G. Count pass | not as such (wallet) | punch cards | block cards | yes, with expiry | yes, days or none | hours (2020) |
| H. Value pass / club wallet | Club Wallet, bonus packs, expiry optional | value cards, expiry | vouchers | karnet kwotowy | vouchers, karnet balance | wallet (app 3.56.0) |
| I. Multi-club credit | chain only | chain + wellness gift cards | not found | yes, cash-out | not found | not found |
| J. Gift vouchers | no | via value cards | yes | listed in terms | not found | not found |
| K. Refund to wallet | club's choice | venue handles refunds; value-card part back to the card | not read | default | to the pass | not found |
| M. Declare cards online | no (club category) | wellness → value card | not found | yes + deposit | yes, count + limits | flag only |
| N. Medicover verification | no | — | — | not found | yes, ±15 min | no |
| O. Operator check | no | wellness providers convert to gift cards; no gate check | not read | no (desk stamp) | Medicover, by phone (API inferred) | no |
| P. Card discount per seat | — | MPP | — | to the declarer | not stated | — |

## Gaps

- The rate Benefit Systems, VanityStyle, Medicover Sport and PZU Pomoc pay a facility per fitness visit, and whether
  the 15 zł co-financing on courts is the operator's standard or each club's deal.
- Benefit Systems' and Medicover Sport's terms for a software vendor (rather than a club) to integrate; whether a
  booking-time check is possible at all.
- Whose share a card discount reduces in tenis4U's shared bookings; what tenis4U does when a declared card is not
  stamped.
- Padel House's, Morelowa 34's, Libertów's and Bajada's prices from the clubs themselves (no own price pages; PADO only),
  Bajada's indoor price, Park Jordana's price.
- Whether any Kraków padel club sells passes, value passes, gift vouchers or members' prices.
- Reservise's (Playmore's) standing with KNF for its cross-club, withdrawable wallet; MATCHi's licence basis for gift
  cards valid at every venue.
- The final text and date of application of the EU Payment Services Regulation (provisional agreement of 30 April 2026
  read; Official Journal not found).
- A Polish judgment or UOKiK decision on expiry or non-refund of a sports pass or wallet, readable at the source.
