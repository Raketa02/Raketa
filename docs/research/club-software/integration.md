# How rivals get a club's courts — and what that means for Rakieta

Research for the grilling of story S-01E ([#609](https://github.com/Raketa02/Raketa/issues/609)), whose
decisions of 2026-10-12 ([comment](https://github.com/Raketa02/Raketa/issues/609#issuecomment-6120454776))
removed *On request* and *Instant* and set Rakieta on the path to becoming the club's booking software.
It is the starting point for the club-software grilling that follows.

**Extends** [`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) and
[`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md). Facts
carried from there keep their dates; everything else was read **2026-10-12**.

**This file decides nothing.** The decisions are in the #609 comment above and in the club-software
grilling.

**Sources.** Playtomic and MATCHi help pages were read through their public Zendesk API, because the
HTML answers 403; ClassPass partner pages through a reader proxy, for the same reason. tenis4U's and
Playmore's interface text comes from the JavaScript and page data their web apps serve to every visitor.
Nobody signed in, booked or paid, and no endpoint was called.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price
· `[DOCS]` a provider's developer document · `[ABSENT]` looked for and not found, with where. Lines marked
*reading* are not sources.

## Read this first

- **Nobody makes a club confirm a court booking.** Every racket platform read confirms a booking at
  once; the one exception is CourtReserve's opt-in approval, which a club uses to vet members and
  guests. The travel trade calls *on request* the stock no allotment covers.
- **Every rival that is effortless for the club has one calendar.** Either the platform *is* the club's
  booking software (Playtomic, MATCHi, Padel Mates, Eversports, CourtReserve, ClubSpark, and in Poland
  tenis4U, Playmore, kluby.org), or a marketplace writes into the club's software through the vendor's
  API and that software refuses a taken hour (Anybuddy, MATCHi←Matchable, ClassPass, Urban Sports Club,
  Reserve with Google).
- **Nobody relies on a desk closing hours by hand**, which is what Rakieta's *Instant* asked.
- **Kraków runs on tenis4U (padel, tennis) and Playmore (squash).** Neither, nor kluby.org, has a
  public API, feed or calendar export; nobody writes bookings into them; tenis4U's terms forbid
  automated reading; and tenis4U is building open sparring, shared bookings and split payments itself.
- *Reading:* a link to a Kraków club's own system needs a vendor with every reason to refuse; becoming
  the club's calendar is the only path Rakieta controls.

## 1. How rivals get court inventory

### The platform is the club's booking software
- **[POLICY] Playtomic Manager** handles "incoming reservations seamlessly, both online and offline"
  ([intro](https://helpmanager.playtomic.com/hc/en-gb/articles/20535516949009)); desk and app share one
  calendar to "avoid double bookings" ([Playtomic Manager](https://playtomic.com/playtomic-manager)).
- **[DOCS] Playtomic's Club API is read-only:** "Can I create or modify bookings through the API? No,
  the current API is read-only." Champion and Master plans only, "typically 1 call per minute"
  ([API guide, updated 2026-08-17](https://helpmanager.playtomic.com/hc/en-gb/articles/38836515997073)).
- **[POLICY] Playtomic is shutting out outside tools:** it "is tightening access controls for external
  tools and automations that connect to club accounts without official authorization" and sends vendors
  to its certification programme, Playtomic Connect
  ([article, updated 2026-10-02](https://helpmanager.playtomic.com/hc/en-gb/articles/47390286355089);
  [Connect](https://playtomic.com/connect)). The Connect page names no way to write bookings.
- **[POLICY] A court not on Playtomic gets a "Community Match"**, which does "not include court bookings
  or payments": "Contact the sports facility directly to book the court"
  ([player help](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481)).
- **[POLICY] Playtomic grew by buying club software, not by linking to it:** Playven in 2020
  ([eu-startups](https://www.eu-startups.com/2020/01/madrid-based-playtomic-sports-venue-booking-app-acquires-playven-and-exceeds-1-million-users/)),
  Kourts in 2021, "reservas y soluciones de gestión de clubes"
  ([interempresas](https://www.interempresas.net/Material-deportivo/523693-Playtomic-adquiere-Kourts-para-acelerar-la-entrada-en-Estados-Unidos.html)),
  GotCourts in 2022, a "sports venue management and court booking platform" with 600+ clubs
  ([tech.eu](https://tech.eu/2022/02/01/madrid-based-playtomic-courts-swiss-tennis-startup-to-strengthen-its-play-in-europe/)),
  and AirCourts in 2023
  ([eu-startups](https://www.eu-startups.com/2023/05/madrid-based-playtomic-hits-the-ace-by-acquiring-portuguese-competitor-aircourts/)).
- **[POLICY] Playtomic books an open match's court in stages:** "1 player: The court is never reserved…
  4 players: Court always reserved", and cancels if "The court becomes unavailable at the club"
  ([player help](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465)); "the system
  automatically assigns courts as the match time approaches"
  ([manager help](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353)).
- **[POLICY] Padel Mates** is the booking software for operators that move to it, such as Rocket Padel
  and Racket Club, from Playtomic and MATCHi
  ([padelalto](https://padelalto.com/2024/11/21/danish-padel-operator-switches-from-matchi-to-swedish-platform)).
- **[POLICY] Eversports** lets clubs "showcase your offers on the Eversports website and app"
  ([padel](https://www.eversportsmanager.com/padel-software)). **ClubSpark** is given to LTA-registered
  venues "free of charge"
  ([LTA, 2021-04-20](https://prod.lta.org.uk/news/2021/april/lta-launches-partnership-with-clubspark-to-provide-enhanced-online-booking-system/)).
- **[ABSENT]** Whether Playtomic owns Syltek: its help says "Club support is handled via Playtomic
  Manager or Syltek" ([player help](https://playerhelp.playtomic.com/hc/en-gb/articles/47092448477457));
  no primary source for the corporate link.

### A marketplace writes into the club's own software
- **[POLICY] MATCHi ← Matchable:** "When a lesson booking is confirmed in Matchable, it automatically
  tells MATCHi to reserve the matching court… the court is immediately unavailable for any other
  booking in MATCHi"; "MATCHi checks for conflicts when the reservation request comes in, a slot that's
  already taken will be rejected"
  ([setup guide, updated 2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/27989311536029)).
- **[POLICY] Anybuddy (France, Belgium, Spain, Switzerland) ↔ Gestion Sports:** "le dirigeant pourra
  choisir les créneaux qu'il souhaite mettre à disposition chez Anybuddy et verra son planning se mettre
  à jour automatiquement à chaque réservation" — the manager chooses the slots he makes available and
  sees his planning update itself with every booking
  ([Padel Magazine, 2022](https://padelmagazine.fr/gestion-sports-et-anybuddy-un-partenariat-unique/)).
- **[POLICY] Anybuddy ↔ OpenResa:** "Rented time slots appear in your calendars just like ordinary
  bookings"; "the choice of calendars, the time ranges and the prices are yours"; "time slots booked by
  your members are never offered"
  ([OpenResa help, updated 2026-09-11](https://openresa.com/en/help/manager/billing/anybuddy)).
  Anybuddy's pitch: "Connexion à votre logiciel de réservation existant", "Aucune modification de votre
  organisation" ([anybuddyapp.com/fr/pro](https://www.anybuddyapp.com/fr/pro)).
- **[POLICY] PlaySkan (UK)** only searches: "availability from clubs' own booking platforms", players
  "click through to the underlying booking system", "we don't take bookings or payments"
  ([PlaySkan, 2026-01-17](https://www.playskan.com/blog/best-padel-booking-systems-in-the-uk)).

## 2. Does anyone make the club confirm a booking?

- **[POLICY] CourtReserve, as an option:** "Reservation Approval requires admin approval before a court
  reservation is confirmed", used "to oversee busy court times, control guest bookings, or review
  certain membership types"
  ([help, 2026-02-16](https://help.courtreserve.com/en/articles/4299937-optional-approval-processes-in-courtreserve));
  the booking reads "Pending Approval", and a declined one "is deleted… refund as account credit"
  ([help, 2026-04-24](https://help.courtreserve.com/en/articles/7994346-managing-approval-requests)).
  Approval per reservation type is still a feature request
  ([forum, 2026-04-17](https://feedback.courtreserve.com/communities/1/topics/197-ability-to-require-approvals-on-specific-reservation-types)).
- **[POLICY] Playtomic and MATCHi approve only between players.** Playtomic's "Request your place" needs
  "approval from everyone in the match"
  ([help](https://helpmanager.playtomic.com/hc/en-gb/articles/20535718052241)); a MATCHi public match
  starts from "a confirmed court booking" and its holder reviews joiners
  ([help](https://matchi.zendesk.com/hc/en-gb/articles/21816050971933)).
- **[POLICY] The travel trade:** stock not contracted in advance is "handled as 'on-request'"
  ([Wikipedia: Allotment](https://en.wikipedia.org/wiki/Allotment_(travel_industry))).
- **[ABSENT]** Any court platform in Spain or Poland where the club confirms a booking ("pendiente de
  confirmación", "rezerwacja na zapytanie", "potwierdzenie rezerwacji przez klub"). Bookero has a
  generic "Moduł zapytań o rezerwację" ([plugin](https://wordpress.org/plugins/bookeropl/)), not a court
  product.

## 3. Aggregators that don't own the venue's software

- **[DOCS] ClassPass** "integrates with 100+… booking systems"
  ([integrations](https://classpass.com/partners/classpass-booking-integrations)); the vendor implements
  the "ClassPass Inventory API… for transactions against those schedules, such as capacity, reservations
  and attendance" ([developers](https://developers.classpass.com/specInfo)). SmartSpot predicts "how many
  spots we should make available", and "ClassPass doesn't 'own' these spots. All spots… are still fully
  bookable by your direct clients" ([FAQ](https://classpass.com/partners/faqs)). Through Pike13 it
  "refreshes schedules every four hours"
  ([Pike13](https://help.pike13.com/hc/en-us/articles/360029552092-ClassPass)).
- **[POLICY] Urban Sports Club via Eversports:** schedules about every 30 minutes, "Bookings and
  cancellations are transferred in real-time", and studios can "limit the number of spots available for
  bookings from aggregators"
  ([Eversports](https://helpcenter.eversportsmanager.com/activate-the-urban-sports-club-api);
  [USC](https://partners.urbansportsclub.com/en/integrations)).
- **[POLICY] Hotels:** a channel manager "updates your availability in real time" and "reduces the risk
  of overbooking" over "350… 2-way PMS… connections"
  ([SiteMinder](https://www.siteminder.com/channel-manager/)); an allotment returns unsold rooms at a
  release date, while "Free sale connects your portal directly to the hotel's live inventory"
  ([dmcquote](https://dmcquote.com/blog/post/b2b-hotel-portal-inventory-allotment-vs-free-sale)).
- **[POLICY] Airbnb's calendar import** "automatically updates every 3 hours", and "nights that you
  block on another calendar may or may not be blocked on Airbnb"
  ([help 99](https://www.airbnb.com/help/article/99)). A request to book gives the host "24 hours to
  respond before it expires" ([help 28](https://www.airbnb.com/help/article/28)).
- **[DOCS] Reserve with Google:** "the Booking Server acts as Google's entrypoint to confirm the
  availability", and partners "need to have a direct contractual relationship with all the merchants"
  ([overview](https://developers.google.com/actions-center/verticals/reservations/e2e/integration-steps/overview);
  [eligibility](https://developers.google.com/actions-center/verticals/reservations/e2e/overview)).
- **[POLICY] Treatwell and Booksy** are the salon's own software; "the availability on the marketplace
  is based on your availability in Connect"
  ([GetApp review](https://www.getapp.com/retail-consumer-services-software/a/treatwell-connect/reviews/)).

## 4. Poland and Kraków

### Who runs what, and what it costs
- **[PRICE] tenis4U** (Kraków, Rynek Główny 28): "372 klubów… 1478 kortów", 49–149 zł a month
  ([tenis4u.pl](https://tenis4u.pl/)).
- **[PRICE] Playmore**, formerly Reservise: "160+ clubs" ([join.playmore.pl](https://join.playmore.pl/en/));
  "Abonament od 299 zł i 1,79% od płatności online", 299/399/499+ zł by number of courts, "Wdrożenie
  trwa 1–2 tygodnie", no commission on payments taken at the desk
  ([cennik](https://join.playmore.pl/cennik/)). "Reservise żegna się po 10 latach. Przenosimy Cię na
  Playmore… Rezerwacje, bazę klientów, cennik i całą historię przenosimy"
  ([join.playmore.pl/reservise](https://join.playmore.pl/reservise/)).
- **[PRICE] kluby.org:** PRO from 79 zł a month per venue, BASIC 50 zł, "Prowizja 2%" on online
  payments ([cennik](https://oferta.kluby.org/cennik)).
- **[POLICY] Which Kraków club runs on which system**, from the provider records on Playmore's Kraków
  pages ([padel](https://playmore.pl/padel/krakow/), [tenis](https://playmore.pl/tenis/krakow/),
  [squash](https://playmore.pl/squash/krakow/)) — Playmore's view, not the clubs':

| System | Clubs |
| --- | --- |
| tenis4U, padel | Garden Padel, Bajada, Padel House, Morelowa 34, Fame Sport, Libertów, SAO Sports Hub |
| tenis4U, tennis | about 15 more, among them Park Jordana, Białoprądnicka, Sport Factory Park, UJ Ruczaj, Tenis Kliny, KSU Grzegórzecki |
| Playmore | Atras Squash Club, Paolo Squash Club, Squash4You |
| Old Reservise | AGH Squash, Miazga |
| kluby.org | Racquet Squash Club, Orzeł Piaski Wielkie |
| Twój Tenis | Czyżyny, Błonia Sport, Korty Dąbskie |

  - SAO's own website now books in its own app, app.saolife.com.pl, though Playmore still lists it on
    tenis4U.
- **[POLICY] Playtomic in Poland:** clubs in Warsaw ([Warsaw Padel Club](https://playtomic.com/clubs/warsaw-padel-club))
  and Katowice ([Padel Up](https://playtomic.com/clubs/padel-up-kato)). **[ABSENT]** A Kraków club on
  Playtomic, or any Polish club on MATCHi or Padel Mates.

### Playmore's open games book the court at once
- **[POLICY]** The player "wybiera wolny kort i godzinę… publikuje grę. Wpisowe płaci z góry jako
  pierwszy"; "Komplet graczy - gra potwierdzona, kort opłacony w całości. Brak kompletu przed startem -
  rezerwacja cofnięta i pełny zwrot"; the club sets "ile godzin przed startem gra się anuluje (1–48 h)"
  ([gry otwarte](https://join.playmore.pl/gry-otwarte/)).
  - *Reading:* the court is booked in the club's own calendar when the game is posted; nobody at the club
    confirms anything.

### Benefit cards
- **[POLICY]** MultiSport only says "Make sure that the facility accepts your card… Take your MultiSport
  card and your ID" ([kartamultisport.pl](https://kartamultisport.pl/en/squash)); Kraków clubs take
  about 15 zł off a card ([Sportano, 2025-01-28](https://sportano.pl/blog/squash-krakow-sprawdz-gdzie-znajdziesz-korty-do-squasha-w-krakowie)).
- **[POLICY]** Desks check cards in their own software or on paper: "Multisport i FitProfit na zeszyt:
  recepcja spisuje numery kart" against Playmore's "Karty zniżkowe weryfikowane automatycznie przy
  rezerwacji" ([Playmore squash](https://join.playmore.pl/dla-klubow-squasha/)).
- **[DOCS]** Medicover Sport runs an API for venues, keyed on the phone number; to connect, eFitness
  needs an "X-AUTH-TOKEN (tzw. facility token)", a Merchant ID and "Oficjalna zgoda na integrację"
  ([eFitness](https://efitness.pl/baza-wiedzy/integracja-z-medicover-sport-kompletny-przewodnik/)).
- **[ABSENT]** A booking integration between Benefit Systems (MultiSport) and club software
  ([partners](https://corp.benefitsystems.pl/en/for-partners/)).

## 5. tenis4U, close up

### It is the club's calendar, not a link to it
- **[POLICY]** "Kalendarz rezerwacji z widokiem dziennym lub tygodniowym każdego kortu w klubie.
  Błyskawiczne dodawanie i usuwanie rezerwacji z poziomu kalendarza."; "Dodawanie stałych terminów, wraz
  z monitorowaniem godzin wykorzystanych i odrobionych."; "Zarządzanie trenerami klubowi i ich
  zajęciami." ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] The club panel** (the public demo at [test-panel.tenis4u.pl](https://test-panel.tenis4u.pl/),
  linked as "Demo" from tenis4u.pl) has:
  - desk bookings: "Gość", "Recepcja oznaczy płatność przy kasie", "Recepcja potwierdziła gotówkę", and a
    payment link — "Użytkownik otrzyma link do płatności. Rezerwacja zostanie usunięta jeśli płatność
    nie zostanie wykonana w ciągu 60 minut.";
  - fixed bookings: "Dodaj rezerwację stałą", "Tworzenie kilku rezerwacji stałych";
  - blocks: "Dodaj blokadę", weekly recurring blocks, "Blokada wzajemna", closed dates, "Ustawić status
    zalany?";
  - per-court online switch: "Nie można dodać rezerwacji gdyż kort ma wyłączoną możliwość dokonania
    rezerwacji online, aktywuj rezerwacje online"; "Kort ma wyłączoną możliwość rezerwacji w godzinach
    16:30 - 22:00 oraz w weekendy";
  - limits: "Ilość dni w przód możliwych do rezerwacji", "Limit aktywnych rezerwacji na użytkownika",
    "Minimalny czas rezerwacji (30 lub 60 minut)", "Ile godzin przed startem anulować nieopłacone
    rezerwacje";
  - roles RECEPTION and COURT_MAINTENANCE, and extra staff ("moderator") accounts linked to a court;
  - each club's own Przelewy24 merchant keys (Client ID, CRC Key), and "Pobierz jako CSV".
- **[POLICY] Players' online bookings** land in the same calendar: the player app and the panel use
  one backend, `api.tenis4u.pl`. "Płatność realizowana jest przez system płatności Przelewy24.pl praz
  Tpay.com" ([regulamin §11](https://tenis4u.pl/regulamin/)).
- **[POLICY] Club websites link out; no embedded widget was found.** Garden Padel's "Rezerwacje" goes to
  `app.tenis4u.pl/#/court/483` ([gardenpadel.pl](https://gardenpadel.pl/)), Fame Sport's to
  `/#/court/104` ([famesport.pl](https://famesport.pl/)). A municipal example: "wszystkie rezerwacje
  kortu tenisowego … odbywają się za pośrednictwem tego narzędzia"
  ([Tarnów Opolski, 2026-06-16](https://www.tygodnikziemiopolskiej.info/artykul/5345)).
- **[POLICY]** The desk's calendar re-reads every 10 seconds and flags "Nowa rezerwacja." and
  "Usunięto rezerwację." (carried from `../games-and-fill-in/areas/CLUBBOOK.md`, R-CLUBBOOK-31).
- *Reading:* availability is always fresh because every door — app, website link, phone, desk — writes
  into one calendar; nothing syncs.

### What it connects to
- **[POLICY] Medicover Sport, very likely through Medicover's API** (an inference; tenis4U never says
  so): the player app sends phone numbers — "Podaj numery telefonów przypisane do kart Medicover" — and
  the panel shows "karta Medicover czeka na weryfikację".
- **[POLICY] MultiSport** only as a count of cards brought: "Dla kart multisporta minimalny czas
  rezerwacji wynosi 60 minut".
- **[POLICY] Hardware it drives itself:** "Sterownik komunikuje się z aplikacją tenis4U za pomocą karty
  SIM lub modemu", 2 500 zł net ([automatyzacja](https://tenis4u.pl/automatyzacja/)); the panel drives
  Shelly relays and TTLock door locks.
- **[POLICY]** "Aplikacja rekomendowana przez Polski Związek Tenisowy." ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] Processors named in its privacy policy:** Servizza, ComVision (SMSAPI), Cloudflare,
  PayPro (Przelewy24), Tpay ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[ABSENT]** Any API, integration or partner page, developer documentation, Google Calendar sync, or
  press about tenis4U partnering with another app, a city or Playmore (sitemap
  [wp-sitemap.xml](https://tenis4u.pl/wp-sitemap.xml): 15 marketing pages, no help pages).

### Its terms
- **[POLICY] §7 bans automated access:** "Wykorzystywał oprogramowania do automatycznego lub ręcznego
  pobierania fragmentów lub całości strony"; "Pozyskiwał dane … w szczególności do celów tzw. 'data
  miningu', 'parsowania', czy systematycznego pobrania i indeksowania strony"
  ([regulamin](https://tenis4u.pl/regulamin/)).
- **[POLICY] The club manages its data:** "Nie ponosimy odpowiedzialności za dane … przekazane przez
  Obiekt Sportowy … dotyczy to w szczególności dostępności rezerwacji … Dane te zarządzane są przez
  usługodawcę"; "tenis4U nie jest stroną umów" ([regulamin](https://tenis4u.pl/regulamin/)); booking
  data "przekazywane są klubowi i staje się on administratorem" ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[ABSENT]** The clubs' own contract with tenis4U, or any clause letting a club authorise a third
  party.

### It is building what Rakieta builds
- **[POLICY]** Its player app contains "Otwarte sparingi", "Rezerwacje współdzielone", "Zaloguj się, aby
  dołączyć do sparingu", join links, payments split per player, and an ELO ranking switched off in the
  code.

### Others read it; nobody writes to it
- **[POLICY] Playmore** shows tenis4U clubs with "Terminy wyszukuje Playmore · rezerwacja u operatora
  klubu"; its page data carries `"_isTenis4you":true,"_isExternal":true`, the club's tenis4U id and
  `"bookingUrl":"https://app.tenis4u.pl/#/court/480"` ([Padel House](https://playmore.pl/klub/padel-house/)).
  **[ABSENT]** Where Playmore gets those times, or whether tenis4U agreed.
- **[POLICY] PADO** links "Online Booking" to `app.tenis4u.pl/#/court/483` and shows no live slots
  ([Garden Padel](https://pado.app/poland/krakow/clubs/garden-padel-krakow)).
- **[POLICY] kluby.org** feeds only its own portal: "Wszystkie odwołane rezerwacje i wolne godziny w
  grafiku automatycznie trafiają na nasz portal do wyszukiwarki wolnych godzin."
  ([oferta](https://oferta.kluby.org)); its integrations are remote control, payments, SMS and invoices
  ([integracje](https://oferta.kluby.org/integracje)).
- **[ABSENT]** Any outside app, league or card provider writing bookings into tenis4U, Playmore or
  kluby.org, or any of them advertising an outside marketplace; any API, webhook or partner offer from
  Playmore ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] Public contact:** kontakt@tenis4u.pl, 889 555 966, Rynek Główny 28, 31-010 Kraków
  ([tenis4u.pl](https://tenis4u.pl/)). No partnerships address.

## 6. The ways to get courts, side by side

*Reading* — ranked by the club's work, least first, with the double-booking risk of each.

| Way | The club's work | Double-booking risk | Who does it |
| --- | --- | --- | --- |
| Rakieta writes into the club's software | none per booking | about none: the software refuses a taken hour | Anybuddy, MATCHi←Matchable, ClassPass — needs the vendor's yes; none in Poland |
| Rakieta is the club's software | a move in, then none | none: one calendar | Playtomic, Playmore, tenis4U, kluby.org |
| A block of hours handed to Rakieta (*Only Rakieta*) | set once, and block the same hours in its own system | low, if the club blocks them | hotel allotments; Anybuddy's chosen slots |
| The club confirms each game (*On request*, removed) | every booking, on a clock | none | CourtReserve's opt-in vetting only |
| Both sell, the desk closes hours by hand (*Instant*, removed) | every sale, both ways, for ever | highest: no sync at all | nobody |

## 7. Gaps

- Playmore's source for tenis4U and kluby.org free hours, and whether tenis4U agreed.
- tenis4U's contract with its clubs; whether a club may authorise an outside app.
- Playtomic's commission, MATCHi's club pricing, Padel Mates' integrations, MATCHi's API documents.
- The Syltek–Playtomic link; TPC Matchpoint; PadelHUB.
- Booking.com's calendar-sync interval (its page answered 403); whether Booksy has manual approval.
- Benefit Systems' booking integration with club software.
- Playtomic's own club search for Kraków (its API was unreachable; the absence rests on web search and
  Playmore's data).
