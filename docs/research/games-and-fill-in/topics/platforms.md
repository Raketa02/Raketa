# Other platforms in the market

The platforms around Rakieta other than Playtomic, the main competitor: the booking systems Kraków clubs
already run (tenis4U, Playmore/Reservise, kluby.org), the Polish aggregators and matchmakers (PADO,
Planeta Padla), the European ones (MATCHi, Padel Mates, Eversports), small apps that deal decks, and
WhatsApp/Facebook groups as a platform.

**Extends** [`../../games-and-fill-in-market.md`](../../games-and-fill-in-market.md) §2, §7.1–§7.9 and
the gap answers (read 2026-10-06/07). Those facts are carried over with their original dates, shortened.
Nothing a grade leans on is older than three months, so none was re-verified.

**New on 2026-10-08:** Kraków padel runs on tenis4U; Playmore's results, check-in QR, payment
deadline and club price; tenis4U's cut-offs; kluby.org's fees; MATCHi's payouts, access codes and
Communities; Padel Mates' replacement link; WhatsApp events.

**Sources.** Playmore and tenis4U interface text comes from the JavaScript their web apps serve to every
visitor; MATCHi help from its public Zendesk API. No screenshot was taken: nothing is `[MEASURED]`.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published
price · `[DOCS]` a provider's document · `[COMPLAINT]` one person's account · `[ABSENT]` looked for and
not found, with where. Lines marked *reading* are not sources.

## 1. Which systems Kraków clubs run

### Kraków padel clubs sit on tenis4U
- **[POLICY]** Playmore's Kraków padel page lists 8 clubs. For 6 of them (Bajada, Fame Sport, Garden Padel, Morelowa 34 Padel Lounge, Padel House, SAO Sports Hub) the club images come from Playmore's folder `external-venue-images/tenis4you`; Libertów's from another external source; Padel SPOT has none. [Playmore: Korty padlowe w Krakowie (page source)](https://playmore.pl/padel/krakow/) — read 2026-10-08
  - *Reading:* the folder shows where Playmore imported each club's data from, not proof of where it books; SAO sells in its own app (below).
- **[POLICY]** Fame Sport's booking link goes to tenis4U; PADO says Padel House "Bookings run through Tenis4U"; Garden Padel books by tenis4U, phone or desk. [Fame Sport](https://famesport.pl/cennik/), [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow), [Garden Padel regulamin §4](https://gardenpadel.pl/regulamin/) — read 2026-10-06/07
- **[POLICY]** kluby.org's booking pages say Padel House "ma wyłączone rezerwacje ONLINE" and Fame Sport "nie korzysta z systemu rezerwacji ONLINE", though both have kluby.org club pages. [kluby.org: Padel House](https://kluby.org/padel-house-krakow/rezerwacje), [Fame Sport](https://kluby.org/fame-sport-club/rezerwacje) — read 2026-10-07
- **[POLICY]** Planeta Padla's FAQ claims "Większość polskich klubów padlowych obsługuje rezerwacje przez Playtomic lub kluby.org" — not true of Kraków on the evidence above. [Planeta Padla FAQ](https://planetapadla.pl/faq) — read 2026-10-06

### Kraków squash clubs sit on Playmore/Reservise
- **[POLICY]** Atras Squash Club runs on Playmore (online 10 % cheaper than at the desk); Squash4You's system and app are by reservise.com (Przelewy24); Miazga embeds `reservise.com/online/miazgasquash`. Each club's regulamin and payment are its own. [Atras](https://www.atrassquash.pl/rezerwacje/), [Squash4You pt 3, 22](https://www.squash4you.pl/regulamin), [Miazga](https://www.miazgasquash.pl/rezerwacje/) — read 2026-10-06
- **[POLICY]** Their rules: free cancellation to 24 h; later the full price, waived only if the court is resold. [Atras regulamin](https://www.atrassquash.pl/regulamin/), [Miazga §4](https://www.miazgasquash.pl/regulamin/) — read 2026-10-06

### Own apps and newcomers
- **[POLICY]** SAO Sports Hub books in its own app "SAO Life": pay at booking, free cancel or move to 12 h, full refund or new slot when the club calls off. [saosports.pl](https://saosports.pl/) — read 2026-10-06
- **[POLICY]** PadelCity (Germany's largest padel operator) opened in Warsaw and lists Kraków "– soon –", booked only in its own app. [PadelCity Polska](https://www.padelcity.pl/) — read 2026-10-06
- **[ABSENT]** No Kraków club on Playtomic (web search "playtomic Kraków padel klub rezerwacja"). — read 2026-10-06

### No system writes bookings into another
- **[ABSENT]** No page of PADO, Playmore or Planeta Padla says it creates bookings in a club's tenis4U or kluby.org calendar; no public tenis4U or kluby.org booking API was found. Aggregators show free hours and send the player to the club's operator ("Terminy wyszukuje Playmore · rezerwacja u operatora klubu"). [Playmore: Garden Padel](https://playmore.pl/klub/garden-padel/), [Planeta Padla FAQ](https://planetapadla.pl/faq) — read 2026-10-07

## 2. Playmore (Reservise)

### Playmore — operator, scale and seller
- **[POLICY]** Reservise Sp. z o.o. (Warsaw); six racket sports; own claim "200+ klubów w Europie". [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-06
- **[POLICY]** "dokonując rezerwacji zawierasz umowę bezpośrednio z Partnerem, nie z nami"; Playmore is "dostawcą internetowej platformy handlowej"; receipts and invoices "wystawia bezpośrednio Partner" (§8.4); no withdrawal right for a dated booking (§14.4). [Playmore Regulamin](https://playmore.pl/legal/terms-of-service) — read 2026-10-07
- **[POLICY]** Club data on its pages carry only a trade name (Atras: `"company_name":"Atras Squash"`), no NIP or legal form. [Playmore: Atras (page source)](https://playmore.pl/klub/atras-squash-club/) — read 2026-10-07

### Playmore — the contract waits for the club, but no confirm step exists
- **[POLICY]** "Umowa Rezerwacyjna zawierana jest … w momencie potwierdzenia przez niego [Partnera] Rezerwacji" (§4.6). [Playmore Regulamin §4.6](https://playmore.pl/legal/terms-of-service) — read 2026-10-07
- **[ABSENT]** No booking state waiting for the club was found in the web app's Polish strings (searched "czeka na potwierdzenie", "oczekuje na potwierdzenie", "akceptacj"): the only "waiting" states are payment ("Oczekuje na płatność") and a result awaiting the other side. [Playmore strings: main](https://playmore.pl/assets/CG9yQPLY.js), [reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore — an unpaid booking lapses after 30 minutes
- **[POLICY]** "Aby potwierdzić rezerwację, dokonaj płatności w ciągu 30 minut. Po tym czasie rezerwacja zostanie automatycznie anulowana"; the pay screen counts down "Opłać do {time} · Zostało {minutes} min"; on expiry "Sprawdzamy, czy termin jest jeszcze zajęty … Jeśli obiekt go nie zwolnił, płatność wciąż utrzyma rezerwację". [Playmore strings: main](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[POLICY]** Declines are named by reason: "Bank odrzucił płatność — brak środków / limit karty / karta nieważna". [same file](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08

### Playmore — open games: each player pays at join
- **[POLICY]** *Gry otwarte* (in the app since v6.10.13, 10 Jul 2026): the organiser picks a free court and hour, sets the player limit, publishes and **pays his share first**; each joiner pays at once (wallet or online, BLIK named); the court cost is split equally ("17,50 zł / os."). [Playmore: Gry otwarte](https://join.playmore.pl/gry-otwarte/), [strings: reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-06/07
- **[POLICY]** All or nothing: "Komplet graczy – gra potwierdzona, kort opłacony w całości. Brak kompletu przed startem – rezerwacja cofnięta i pełny zwrot dla wszystkich." [Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-06
- *Reading:* the outcome matches Rakieta's; the money moves earlier — Rakieta charges nobody until the last yes.

### Playmore — the court is held from publication
- **[POLICY]** "Rezerwujesz kort, piszesz kogo szukasz"; button "Utwórz i zapłać wpisowe ({fee})"; a clash: "Ktoś właśnie zajął ten termin. Wybierz inny slot." The court is freed only when the game is called off ("odwołujemy grę i kort", "kort się zwolni"). A full game is confirmed only at the cut-off: "Skład pełny · potwierdzimy o {time}". [strings: reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-07

### Playmore — the club's open-game settings
- **[POLICY]** "Ilu graczy może szukać jednocześnie (1–10), ile godzin przed startem gra się anuluje (1–48 h) i do kiedy można anulować bezpłatnie (0–72 h)"; free in every package; otherwise "masz tylko podgląd gier - żadnej z nich nie obsługujesz". Code defaults when unset: cut-off 2 h, free cancel 12 h. [Gry otwarte](https://join.playmore.pl/gry-otwarte/), [open-games code](https://playmore.pl/assets/DGQrxHKX.js) — read 2026-10-07
- **[ABSENT]** Whether a changed setting reaches games already published; a warning when free-cancel is longer than the cut-off. [Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-07
- **[POLICY]** Club caps on the creator: "maks. {max} aktywne gry naraz" (separate peak cap). Playmore's own claim: games made 3+ days ahead fill "mniej więcej 3 razy częściej". [strings: reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-07

### Playmore — the open-game card and preview
- **[POLICY]** Card: sport, time, court, avatars, "Organizuje {name}", seat meter "2/4 · brakuje 2 graczy" / "Ostatnie miejsce" / "Komplet", level chip with a Playmore Score range, tags ("Na luzie", "Na punkty", "Nowi mile widziani"…), note, "{fee} zł za osobę", and a strip "Komplet do {time} · Zostało {h} godz. {m} min" (refreshed every 30 s). A game never shows 0/N because its creator pays first. [open-games code](https://playmore.pl/assets/DGQrxHKX.js), [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-07
- **[POLICY]** Preview before "Dołącz za {price}": roster, note, and three rules — only if full; auto-cancel "{hours} h 10 min przed startem"; "Do {hours} h przed startem wypiszesz się ze zwrotem wpisowego". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-07

### Playmore — leaving an open game
- **[POLICY]** "Wypisz się — gra zostaje"; the organiser's role passes on ("organizację przejmie {name}"). After the free window "za Twoje miejsce nic nie wróci", or "…wróci tylko wtedy, gdy gra się nie odbędzie". Leaving a full game warns "Jeśli do {cutoff} nikt nie zajmie Twojego miejsca, gra zostanie odwołana dla całego składu." [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-07
- **[POLICY]** The organiser cancelling late: "Twoje wpisowe przepada. Pozostali gracze dostaną zwrot wpisowego"; to call a game off "Po prostu się wypisz - gra bez kompletu odwoła się automatycznie". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore — refunds go to the wallet and the fee is kept
- **[POLICY]** Every refund string reads "wpisowe wraca na portfel Playmore. Opłata serwisowa nie podlega zwrotowi"; ordinary bookings: "Środki nie wrócą do portfela ani na karnet" after the free deadline. [strings](https://playmore.pl/assets/93jAIRDY.js), [locale](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-07
- **[POLICY]** Default rule unless the club sets another: cancel or move up to 24 h before; later, no refund (§5.1–5.2). [Playmore Regulamin](https://playmore.pl/legal/terms-of-service) — read 2026-10-07

### Playmore — player fees
- **[PRICE]** Atras: "Do rezerwacji opłaconych online doliczamy opłatę serwisową 1,48 zł". [Playmore: Atras](https://playmore.pl/klub/atras-squash-club/) — read 2026-10-06
- **[POLICY]** Yet its Kraków FAQ says "Rezerwacja kortu przez Playmore jest darmowa … Nie pobieramy prowizji od użytkowników"; the club price page says the player's service fee is set "w ofercie" for each club. [Playmore Kraków](https://playmore.pl/padel/krakow/), [Playmore cennik](https://join.playmore.pl/cennik/) — read 2026-10-08

### Playmore — what a club pays
- **[PRICE]** "od 299 zł netto / mies." by modules and size, plus **1,79 % of online payments** (in app and on the web; nothing on desk payments). Example: 60 000 zł online a month → 1 074 zł fee, "od 1373 zł" in all. Setup and data transfer 0 zł; monthly, no long contract; Challenger league 249 zł/month; SMS priced in the offer. [Playmore cennik](https://join.playmore.pl/cennik/) — read 2026-10-08

### Playmore — the club's money passes through Reservise
- **[POLICY]** A player's online payment goes "chwilowo na nasz rachunek"; after each settlement period Reservise pays the club the total minus its fees (§9). The monthly report shows "kwotę do wypłaty". [Playmore Regulamin dla Partnerów §9](https://playmore.pl/legal/partner-terms) — read 2026-10-07; [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08
- **[ABSENT]** The length of the settlement period. [Playmore cennik](https://join.playmore.pl/cennik/) — read 2026-10-08

### Playmore — results are reported, confirmed or disputed
- **[POLICY]** After a confirmed game one side enters "Kto grał z kim?" (Drużyna A/B), the winner and optional sets; "Wynik czeka na potwierdzenie drugiej strony"; it "Potwierdzi się automatycznie {date}". The other side confirms or "Zgłoś zastrzeżenie": "Zastrzeżenie zamraża wynik do wyjaśnienia przez klub"; "skontaktuje się z Wami recepcja klubu". Refusals: "Minął termin na wpisanie wyniku", "Nie możesz potwierdzić wyniku, który sam zgłosiłeś", "Wpisywanie wyników jest w tym klubie wyłączone". Then "Zagrajcie znowu — Ten sam kort … za tydzień". [strings: reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** A way for players to report a no-show (searched "nie stawi", "nieobecn", "no-show"); attendance marking exists only for coaches' classes, editable up to 6 h after. [strings](https://playmore.pl/assets/93jAIRDY.js), [main](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08

### Playmore — check-in QR and door opening
- **[POLICY]** A booking's "Kod QR rezerwacji — Zeskanuj ten kod przy stanowisku self-checkout w obiekcie", with "Skopiuj link dla znajomego". Door: "Aby uzyskać dostęp do obiektu, należy najpierw opłacić rezerwację", "Otwórz drzwi do obiektu", or scan "naklejkę QR przy drzwiach"; "Ten obiekt nie obsługuje otwierania z aplikacji" where not fitted. [strings: reservations](https://playmore.pl/assets/93jAIRDY.js), [main](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08
- **[POLICY]** Club side: Loxone integration — players enter by phone, lights on at the booking's start and off at its end; Multisport and FitProfit cards scanned at the entrance. [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08

### Playmore — waiting lists and alerts
- **[POLICY]** Full open game: "Zapisz się na rezerwę"; "Gdy zwolni się miejsce, powiadomimy wszystkich z listy naraz — kto pierwszy, ten gra"; no payment to join the list. Classes: "Zapis nic nie kosztuje"; told "mailem, a jeśli masz aplikację — także powiadomieniem". Courts: a bell on a taken hour sends "natychmiastowe powiadomienie email" when it frees; booking stays her own act. [strings](https://playmore.pl/assets/93jAIRDY.js), [main](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-07
- **[POLICY]** Open-game alerts by sport, level and daypart, no price field. Notices: "Ktoś dołączył, gra potwierdzona, gra anulowana - gracze wiedzą wszystko bez udziału recepcji". [strings](https://playmore.pl/assets/93jAIRDY.js), [Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-07

### Playmore — weekly availability grids
- **[POLICY]** *Szukam grania*: "Kiedy zwykle możesz grać? — To nie rezerwacja"; seekers see "Wspólne terminy: …"; reciprocal visibility, quiet mode, 4-week expiry. *Challenger* shows rivals a weekly grid. None at sign-up. [strings: lookingForGame](https://playmore.pl/assets/5BE1o4M2.js), [challenger](https://playmore.pl/assets/Dy2aBMG-.js) — read 2026-10-07

### Playmore — invites by WhatsApp and a club's community links
- **[POLICY]** A game short of players offers "Wyślij zaproszenie na WhatsAppie", "Zaproś Buddies", "Skopiuj link" ("zapiszą się do gry sami"). A club page can list its community channels: WhatsApp, Facebook, Instagram, Telegram, Discord ("Dołącz do naszej społeczności!"). [strings: reservations](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore — a club leaving or unable to host
- **[POLICY]** Monthly or yearly terms renewing unless cancelled 14 days before the end (§5); a club leaving over a terms change cannot take new bookings, and Playmore "rozliczymy te Rezerwacje, które zostały dokonane przed" (§16); a club that cannot host must post a notice or tell the booked player directly (§8). [Regulamin dla Partnerów](https://playmore.pl/legal/partner-terms) — read 2026-10-07
- **[ABSENT]** A pause switch, a court-blocking help, a dated price list (sitemap and web searched). — read 2026-10-07

### Playmore — complaints
- **[COMPLAINT]** "Contacted the app support for refund—they bounced me off to the club. Contacted the club—the club bounced me off to the app" (25 Mar 2025). [App Store PL reviews](https://apps.apple.com/pl/app/reservise-playmore/id928403015) — read 2026-10-06

## 3. tenis4U

### tenis4U — operator, scale and seller
- **[POLICY]** Run from Kraków (tennis4U Sp. z o.o., Rynek Główny 28); "the largest software provider for tennis, padel and pickleball courts in PL", 1478 courts, recommended by PZT; leagues, tournaments, a challenge ladder, no partner matchmaking. "tenis4U nie jest stroną umów". [tenis4U](https://tenis4u.pl/), [Regulamin](https://tenis4u.pl/regulamin/) — read 2026-10-06

### tenis4U — payment and the 2 % refund deduction
- **[POLICY]** Online payment where the club enables it, via Przelewy24 and Tpay; "Zasady anulowania określa regulamin Usługodawcy"; a cancelled online payment returns "pomniejszonych o opłatę transakcyjną w wysokości 2%". No app fee for players. [tenis4U Regulamin §11](https://tenis4u.pl/regulamin/) — read 2026-10-06
- **[PRICE]** Club subscription: FULL 49 zł/month net (1 court), 89 zł (2–3), 149 zł (more); BASIC 10 zł. [tenis4U cennik](https://tenis4u.pl/#cennik) — read 2026-10-06

### tenis4U — separate cut-offs for one-off and standing bookings
- **[POLICY]** A court's page shows "{n} godzin przed rozpoczęciem można odwołać rezerwację jednorazową" and, separately, "…rezerwację stałą", or "możliwość odwołania … w dowolnym momencie"; a club rule can cap use ("1 osoba może zarezerwować 1 godzinę dziennie"). [tenis4U web app](https://app.tenis4u.pl/) — read 2026-10-08

### tenis4U — flooded courts and classes short of people
- **[POLICY]** A club flags courts "zalane" after rain; booking then asks "Korty są obecnie zalane, czy na pewno chcesz zarezerwować kort?", and "Kort oznaczony jako zalany — możesz anulować rezerwację do momentu jej rozpoczęcia". [tenis4U web app](https://app.tenis4u.pl/), [Rezerwacje](https://tenis4u.pl/rezerwacje/) — read 2026-10-07/08
- **[POLICY]** Group classes: "zajęcia zostaną odwołane jeśli do {time} nie zbierze się wymagana liczba osób", with a "Lista rezerwowa". [tenis4U web app](https://app.tenis4u.pl/) — read 2026-10-08

### tenis4U — no club-confirm state, no published club contract
- **[ABSENT]** No booking awaiting the club's acceptance in the web app's code (searched "akceptac", "oczekuj", "confirm"). No club contract, pause switch or court-block help published. [tenis4U web app](https://app.tenis4u.pl/), [sitemap](https://tenis4u.pl/wp-sitemap-posts-page-1.xml) — read 2026-10-07/08

## 4. kluby.org

### kluby.org — operator, scale and seller
- **[POLICY]** IT Sports Solutions Michał Buze (Warsaw); club software plus a public portal; "not a party" to the booking, which is with the club under its regulamin; own claims 150+ clubs, 4.1 m bookings, 102.7 m zł. [Regulamin §IV](https://kluby.org/regulamin), [oferta](https://oferta.kluby.org) — read 2026-10-06

### kluby.org — payments, partial prepayment and its fee
- **[POLICY]** The user pays the club directly; online payment is optional, via Przelewy24 and PayU. Clubs set booking payments "dobrowolne lub wymagane 25%/50%/100%". [Regulamin §IV](https://kluby.org/regulamin), [Integracje](https://oferta.kluby.org/integracje) — read 2026-10-06/08
- **[PRICE]** Online payments: "Prowizja 2%". [Integracje](https://oferta.kluby.org/integracje) — read 2026-10-08
- **[POLICY]** Split payment: if invited players have not paid "within 2 hours after the game ends", the booker's saved card (PayU) is charged their shares; if that fails, a debt is recorded at that club. [Załącznik nr 3 §4](https://kluby.org/regulamin/karty-platnicze) — read 2026-10-06

### kluby.org — cancellation on the club's terms
- **[POLICY]** Cancel "tylko na warunkach określonych przez Klub przy danej Usłudze"; refunds and complaints go to the club. January 2023: "Wprowadzenie opcjonalnego limitu odwołania dla danej rezerwacji" (a per-booking cancel limit). [Regulamin §IV](https://kluby.org/regulamin), [Co nowego 2023](https://oferta.kluby.org/changelog?rok=2023) — read 2026-10-06/08

### kluby.org — blocks and debts
- **[POLICY]** Clubs can block a user; the count is shared with every club the user books; two clubs' blocks can lock the account. Changelog: "Blokada klientów zadłużonych" (2019), "Powiadomienia SMS o zaległościach" (2018). [Regulamin §IV pt 5f, §V](https://kluby.org/regulamin), [Co nowego 2018](https://oferta.kluby.org/changelog?rok=2018), [2019](https://oferta.kluby.org/changelog?rok=2019) — read 2026-10-06/08

### kluby.org — pausing online booking and blocking hours
- **[POLICY]** A club-wide switch with a reason (Dec 2022); live: "Tymczasowo rezerwacje ONLINE zostały wyłączone" (Garden Padel). Blocking covers "wszystkich wolnych połówek" in a range (2017) — free half-hours only. [Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022), [Garden Padel](https://kluby.org/garden-padel/rezerwacje) — read 2026-10-07
- **[POLICY]** Cancelled bookings and free hours "automatycznie trafiają na nasz portal". [oferta](https://oferta.kluby.org) — read 2026-10-06

### kluby.org — results, waiting lists, partner search
- **[POLICY]** Players enter league results (2017, switchable off); "Dodanie listy oczekujących" (2017); game proposals in the *Sparingi* partner base (2022), by city, radius 30 km. [Co nowego 2017](https://oferta.kluby.org/changelog?rok=2017), [2022](https://oferta.kluby.org/changelog?rok=2022), [Padel sparingi](https://kluby.org/padel/sparingi) — read 2026-10-07/08

### kluby.org — SMS, receipts and remote control
- **[PRICE]** SMS from the club's name 0,07–0,16 zł each; online invoices, receipts and e-paragony 0–60 zł/month; remote control of lights, heating, gate and **door by PIN**, switched "na x minut przed rezerwacją" (priced per install). [Integracje](https://oferta.kluby.org/integracje) — read 2026-10-08

### kluby.org — what a club pays
- **[PRICE]** KLUB BASIC 50 zł/month net (≤30 bookings); KLUB PRO from 79 zł by courts (two tables are shown: 2 courts 139 or 119 zł, 4 courts 209 or 179 zł); 60 days free; "miesięczny okres wypowiedzenia". [Cennik](https://oferta.kluby.org/cennik) — read 2026-10-08

## 5. PADO (Wrocław)

### PADO — seller and payments
- **[POLICY]** 7DESIGN Sp. z o.o.; "a technology platform … not a party to the transaction … does not act as a merchant of record"; payments via Stripe; club CRM lists "Stripe, Apple Pay, Google Pay, Blik, and card payments", "New bookings appear instantly". [PADO Terms §2, §4](https://pado.app/terms) — read 2026-10-06; [PADO for clubs](https://pado.app/for-club) — read 2026-10-08
- **[ABSENT]** When a share is charged, how clubs are paid out, any no-show rule, any check-in, any club approval step. [PADO Terms](https://pado.app/terms), [for clubs](https://pado.app/for-club) — read 2026-10-08

### PADO — matchmaking, auto-fill and ELO
- **[POLICY]** "browse players and open matches in your city, and send or accept an invite"; CRM "Auto-Fill Matches", split payment "between 2 or 4 match participants", "Waitlist: Queue for cancelled court slots"; players see an ELO and its change. [pado.app](https://pado.app), [for clubs](https://pado.app/for-club) — read 2026-10-07/08

### PADO — fees, cancellation and disputes
- **[PRICE]** Players: "free … You only pay for the court". Clubs: "Only 2% of the booking cost per court", passed to the player or kept by the club. [pado.app](https://pado.app), [for clubs](https://pado.app/for-club) — read 2026-10-08
- **[POLICY]** Cancellation set by the provider, who "must display" it before payment; disputes to the provider, then PADO after 7 days; no withdrawal right for dated bookings (§8). [PADO Terms §4A, §8](https://pado.app/terms) — read 2026-10-08

## 6. Planeta Padla

### Planeta Padla — aggregator with open matches and a slot exchange
- **[POLICY]** PM INVEST sp. z o.o.; availability and prices from "95+ klubów w 33 miastach" (7 in Kraków), sends the player to the club's booking; free for players; "Szukam gry i otwarte mecze", "Matchmaking według poziomu", and "Giełda terminów: oddaj albo przejmij rezerwację" (how money moves on it: not stated). Card sample: "Brakuje 1 osoby · dziś 20:00 · 3.0–3.5 · 3/4 graczy · Dołącz". [Planeta Padla](https://planetapadla.pl/), [Kraków](https://planetapadla.pl/cities/krakow) — read 2026-10-06/07
- **[POLICY]** "Dostępni znajomi" shows whether past Playtomic partners are free today, from their Playtomic bookings. [Polityka prywatności §3](https://planetapadla.pl/polityka-prywatnosci) — read 2026-10-07

## 7. MATCHi (Sweden; merging with Eversports)

### MATCHi — scale, owner and seller
- **[POLICY]** 1718 venues; merging with Eversports in 2026; a venue "is an independent business"; Adyen, Swish, Vipps, wallets; no Polish method. [MATCHi](https://www.matchi.se/), [payment methods](https://matchiplayers.zendesk.com/hc/en-gb/articles/11452041548445-Which-payment-methods-we-accept) — read 2026-10-06

### MATCHi — the card is held at booking and captured later
- **[POLICY]** "We debit the amount either 12 hours after your playing time starts, or 7 days after the booking was created — whichever comes first", because "many payment methods don't allow us to hold a reservation for longer than 7 days". [How does payment work](https://matchiplayers.zendesk.com/hc/en-gb/articles/15599128235549-How-does-payment-work-when-booking) — read 2026-10-06

### MATCHi — venue matches: pay at join, optional auto-cancel
- **[POLICY]** The venue pre-books court, time, skill range and spots; each player pays his spot ("slot price per customer category ÷ number of spots"); outsiders blocked ("This match requires skill level X–Y"); leaving before the venue's cut-off refunds the spot minus the platform fee, after it nothing; optional auto-cancel refunds everyone in full "with a notification". [Venue created matches (player)](https://matchiplayers.zendesk.com/hc/en-gb/articles/36168240420253-Venue-created-matches), [(venue)](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333-Venue-created-matches) — read 2026-10-06/07
- **[POLICY]** "Match Settings only affect new matches — existing matches keep their values" (cancellation rule, e.g. 12 h; auto-cancel, e.g. 2 h). [Venue created matches (venue)](https://matchi.zendesk.com/hc/en-gb/articles/36168172962333-Venue-created-matches) — read 2026-10-07

### MATCHi — public matches: the holder stays liable
- **[POLICY]** A holder makes a confirmed single-court booking public, sets a level range and accepts or declines each request; "keeps full ownership of the booking and remains financially responsible for it"; on acceptance "the system automatically handles splitting the payment"; turning it private leaves accepted players in. "If the match doesn't fill up … it's still your responsibility as the booker to cancel it." [Public Matches (venue)](https://matchi.zendesk.com/hc/en-gb/articles/21816050971933-Introducing-MATCHi-s-New-Feature-Public-Matches) — read 2026-10-08; [(player)](https://matchiplayers.zendesk.com/hc/en-gb/articles/23495400766621-Information-about-Public-Matches) — read 2026-10-06
- **[POLICY]** Split payment: if co-players don't pay "within 2 hours after the booking ends, you'll cover their parts"; only the booker can cancel. [Split Payment Q&A](https://matchiplayers.zendesk.com/hc/en-gb/articles/14685446085661-Split-Payment-Q-A), [App Store screenshot 07](https://apps.apple.com/gb/app/matchi/id720782039) — read 2026-10-06/07

### MATCHi — fees on cancellation
- **[PRICE]** 4 % service fee in SE, NO, DK, FI, NL, BE, RO, TH (min/max per market), "generally non-refundable" unless the venue picks a full refund; 12.50 SEK fee on card cancellations. [Service fee (venue)](https://matchi.zendesk.com/hc/en-gb/articles/21623335434269-Service-fee) — read 2026-10-08; [How do I cancel](https://matchiplayers.zendesk.com/hc/en-gb/articles/11451781340061-How-do-I-cancel-a-booking) — read 2026-10-06

### MATCHi — the club cancels or blocks
- **[POLICY]** The admin chooses "Cancel and give a full refund", "…(customer pays cancellation fee)" or "Cancel without giving a refund"; the customer gets a cancellation email. Blocking a booked slot "is not possible"; a venue "Close" removes only unbooked slots and lists the booked ones to cancel first; a court with future bookings cannot be archived. [Cancel and/or refund](https://matchi.zendesk.com/hc/en-gb/articles/11673921738013-Cancel-and-or-refund-booking), [Create deviations](https://matchi.zendesk.com/hc/en-gb/articles/11719720215453-Create-deviations), [Court status](https://matchi.zendesk.com/hc/en-gb/articles/14582141635101-How-to-change-court-status-on-off) — read 2026-10-07

### MATCHi — the club is paid monthly, by the game's date
- **[POLICY]** MATCHi collects through Adyen "on your venue's behalf"; a statement ~10th covers the previous month, payout ~15th "if there's a positive balance", else the venue is invoiced. Statements go by "the delivery date of the order — the activity's start time for bookings", not the capture date; payments not yet captured roll to the next month; refunds are simply excluded. [The payment process](https://matchi.zendesk.com/hc/en-gb/articles/17393855711517-The-payment-process-Standard-payments), [What is a statement](https://matchi.zendesk.com/hc/en-gb/articles/14804896435869-What-is-a-statement) — read 2026-10-08

### MATCHi — access codes in the confirmation
- **[POLICY]** Codes per court and time window are "automatically included in their booking confirmation"; reusable, not tied to one booking. [Access codes](https://matchi.zendesk.com/hc/en-gb/articles/34085754817949-Access-codes) — read 2026-10-08
- **[ABSENT]** A QR check-in for court bookings (venue help searched "check in"). — read 2026-10-08

### MATCHi — Communities are a venue's groups
- **[POLICY]** "A community is a private social space attached to a customer group at your venue", created and moderated by the venue; invites in-app, push and email; join by link or QR; posts link matches and bookings; joining makes the player the venue's customer. [Communities](https://matchi.zendesk.com/hc/en-gb/articles/36758141080093-Communities) — read 2026-10-08

### MATCHi — waiting lists and auto-cancelled activities
- **[POLICY]** Activities: everyone on the list is notified at once when a place opens; nobody is enrolled or charged. An occasion is cancelled automatically "because the minimum number of participants wasn't reached by the cancellation deadline", refunded automatically, only if both a minimum and a deadline are set. [Waiting list (player)](https://matchiplayers.zendesk.com/hc/en-gb/articles/13948726057117-Can-I-get-in-line-for-an-activity-that-is-fully-booked) — read 2026-10-07; [Cancelled Activities](https://matchi.zendesk.com/hc/en-gb/articles/28528118381469-Cancelled-Activities) — read 2026-10-08
- **[ABSENT]** A player-facing no-show rule (players' help searched "no show"). — read 2026-10-06

## 8. Padel Mates (Sweden)

### Padel Mates — what it is and how players pay
- **[POLICY]** Padel Mates International AB: find players, matches, clubs, book and "split the cost"; Apple Pay, Google Pay, card, Swish, MobilePay; "Smart Match Suggestions … based on your skill level and preferred center" shown as lists ("In focus", "Activities close to you"); 4.4/5 from 5.2 k ratings (SE). [App Store SE](https://apps.apple.com/se/app/padel-mates/id1531797995), [App Store PL](https://apps.apple.com/pl/app/padel-mates/id1531797995) — read 2026-10-06/07
- **[POLICY]** Web FAQ: "As a player, Padel Mates is completely free"; "up to 24 hours before play you get a full refund. Policies may vary by club"; "Offline check-in at the court"; release 2 Apr 2026 "Clubs can now handle payouts and refunds directly through Stripe"; 15 Mar 2026 push "when an open match appears that matches your level and location". [Padel Mates strings](https://padelmates.se/locales/en/translation.json) — read 2026-10-08

### Padel Mates — find a replacement for your spot
- **[POLICY]** "Find a replacement for your spot — To find a replacement, copy the link below and share it. If someone joins using this link, you will be automatically removed from the activity and receive a refund"; leaving an online-paid booking quotes the club's cancellation fee; "Cancel with refund" / "Cancel without a refund". [Padel Mates strings](https://padelmates.se/locales/en/translation.json) — read 2026-10-08
- **[POLICY]** Club cap at join: "You've reached the maximum number of activities you can join for this club"; "Join waiting list" (what a freed spot does: not stated). [same](https://padelmates.se/locales/en/translation.json) — read 2026-10-07
- **[COMPLAINT]** After the 2023 update one can "no longer see who has Swished" — players paid the organiser by Swish. [App Store SE](https://apps.apple.com/se/app/padel-mates/id1531797995) — read 2026-10-06

## 9. Small apps: decks and balance figures

### Swipe decks deal people, not games
- **[POLICY]** Padelbuddy, Hitch, Quadra and the Polish Noavo ("Przesuń. Dopasuj. Graj.") deal people with a mutual yes; Matchup Sport and CourtSync deal open slots. [Noavo](https://apps.apple.com/pl/app/noavo/id6764517766), [Matchup Sport](https://apps.apple.com/de/app/matchup-sport/id6782085896) — read 2026-10-07
- **[ABSENT]** Any app where a swipe or one tap pays for a spot; every one found joins through a separate payment step. — read 2026-10-07

### A balance figure or suggested sides
- **[POLICY]** Only small apps: Padel Pals shows each pair's "Win probability 59% / 41%" with a "Swap"; PickleCrew "Make Fair Teams … never shown as a rating". Playmore assigns sides only at result entry; PADO shows ELO only. [Padel Pals](https://apps.apple.com/gb/app/padel-pals/id6742356382), [PickleCrew](https://apps.apple.com/gb/app/picklecrew-pickleball-scores/id6815026461) — read 2026-10-07

## 10. Other platforms checked

### Eversports
- **[POLICY]** Waiting list: a free spot triggers a push; "you will not be automatically signed in"; first come, first served. [How to use the waiting list](https://helpcenter.eversportsmanager.com/how-to-use-the-waiting-list) — read 2026-10-07

### LigaPadla, Anolla and dead ends
- **[POLICY]** LigaPadla.pl sp. z o.o. (Warsaw): padel tournaments, leagues and rankings at listed clubs, a free system for organising competitions; no booking. [LigaPadla](https://rozgrywki.ligapadla.pl/kluby/garden-padel-krakow-50) — read 2026-10-08
- **[ABSENT]** No Kraków club on Anolla; tennispartner.pl, tie-break.pl, squasher.pl do not resolve; Booksy has no Kraków court category. [Anolla](https://anolla.com/pl/oprogramowanie-do-padla) — read 2026-10-06

### No club-confirms booking mode anywhere
- **[ABSENT]** No platform read has courts booked on the club's confirmation (Playmore, tenis4U, kluby.org, PADO, MATCHi; for Playtomic see its topic). The confirm-or-deny pattern exists only for joining someone's booking (MATCHi public matches), course applications (MATCHi) and tournament entries (kluby.org "Zatwierdzanie zgłoszeń", 2019). [MATCHi Public Matches](https://matchi.zendesk.com/hc/en-gb/articles/21816050971933-Introducing-MATCHi-s-New-Feature-Public-Matches), [kluby.org Co nowego 2019](https://oferta.kluby.org/changelog?rok=2019) — read 2026-10-08

### No platform shows a club the player groups that play at it
- **[ABSENT]** Playmore's "Grupy" are coaching groups; Planeta Padla's groups need a login; MATCHi Communities are the venue's own customer groups, not player-made ones. [Playmore dla klubów](https://join.playmore.pl/), [MATCHi Communities](https://matchi.zendesk.com/hc/en-gb/articles/36758141080093-Communities) — read 2026-10-07/08
- **[ABSENT]** A club passing its full-court demand to a partner club; MATCHi: bookings "can never be moved to a different venue". [The venue settings](https://matchi.zendesk.com/hc/en-gb/articles/11468129157405-The-venue-settings) — read 2026-10-07

## 11. WhatsApp and Facebook groups

### WhatsApp groups: polls, events and 1024 members
- **[POLICY]** Since Nov 2022: in-chat polls, "groups with up to 1024 users", Communities linking groups. [WhatsApp blog: Communities now available](https://blog.whatsapp.com/communities-now-available) — read 2026-10-08
- **[POLICY]** Events (May 2024): "Anyone can create an event", "others can respond so the whole group knows who is coming", "those going will get an automatic notification when it's getting close", listed on the group's info page; first in Community groups, then all groups. [WhatsApp blog: events](https://blog.whatsapp.com/new-to-communities-events-and-replies-in-announcement-groups) — read 2026-10-08
- *Reading:* nothing in either post books a court or moves money; the organiser still books and collects.

### Operators and booking systems lean on WhatsApp
- **[POLICY]** PadelCity links one WhatsApp group per location (30) for finding opponents. [PadelCity.de](https://padelcity.de/) — read 2026-10-06
- **[POLICY]** Playmore pitches *Gry otwarte* against "Telefon i WhatsApp", yet ships a WhatsApp invite button and lets clubs list WhatsApp and Facebook groups (§2 above). [Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-06; [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Kraków groups could not be read
- **[ABSENT]** No public Kraków padel, tennis or squash group post ("szukam 1 osoby na 19:00", BLIK to the organiser) could be read: Facebook needs a login; searches found pages (Stowarzyszenie Padel Kraków, Vamos Padel Kraków), not groups; no Kraków club site links a WhatsApp or Facebook group (Garden Padel, Padel Lounge, SAO, Fame Sport, Atras checked). [Stowarzyszenie Padel Kraków](https://www.facebook.com/padelkrakowassociation/), [Vamos Padel Kraków](https://www.facebook.com/padelkrakow/) — read 2026-10-06/08
- **[ABSENT]** Polish evidence of paying the organiser by BLIK (Sweden has Swish, §8). — read 2026-10-06

## 12. Summary

| Platform | When a player pays | Short game | Late leaver | Who is paid, when | Fee |
| --- | --- | --- | --- | --- | --- |
| Playmore *Gry otwarte* | At join; court held from publishing | Called off 1–48 h before, refund to wallet | Nothing after 0–72 h unless called off | Via Reservise, per settlement period | Player fee (1,48 zł at Atras); club 1,79 % + 299 zł/month |
| tenis4U | At booking, if the club enables it | — | Club's rules; online refunds minus 2 % | The club, via P24/Tpay | Club 49–149 zł/month |
| kluby.org | Club sets 0/25/50/100 % online; split shares charged to the booker 2 h after | — | Club's rules; per-booking limit | The club, via P24/PayU | 2 % online; club 50–79+ zł/month |
| PADO | In app (Stripe); timing not stated | — | Club's rules | Not stated | 2 % per booking |
| MATCHi venue match | At join | Optional auto-cancel, full refund | Spot minus fee before cut-off, nothing after | MATCHi collects; club paid ~15th of next month by game date | 4 % in 8 countries |
| MATCHi public match | Holder pays all; split on acceptance | Holder's problem | Holder liable | as above | as above |
| Padel Mates | In app | — | Full refund to 24 h; or a replacement via link | Club's Stripe | Free for players |
| WhatsApp groups | Organiser collects | Organiser's problem | None | Organiser | None |
| Rakieta (spec) | Nobody until the last yes | Called off at cut-off, full refund | Minus card fee before cut-off; after, only if the seat is taken | The club, after the game | None |
