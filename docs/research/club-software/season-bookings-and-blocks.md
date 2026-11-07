# Season bookings, blocks and closures — how rivals and Kraków clubs run them

Research for areas 4 (season and fixed bookings) and 5 (blocks and closures) of the planning map *Raketa becomes
the club's booking software* (decided 2026-10-12: one calendar for desk, phone, walk-ins, season bookings, online
bookings and the Games deck; a game the club cancels is moved by Raketa to another free court at the same club,
same day, hour and price).

**Extends** [`integration.md`](integration.md) (§5 tenis4U close up),
[`../games-and-fill-in/topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`../games-and-fill-in/topics/local-market.md`](../games-and-fill-in/topics/local-market.md),
[`../games-and-fill-in/topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md),
[`../games-and-fill-in/areas/COURTS.md`](../games-and-fill-in/areas/COURTS.md) and
[`../games-and-fill-in/areas/CLUBSETUP.md`](../games-and-fill-in/areas/CLUBSETUP.md). Facts carried from there keep
their dates; everything else was read **2026-10-12**.

**This file decides nothing.** Each feature below is for the club-software grilling to mark *Build at launch ·
Build later · Leave out · Ask a real club*. Nothing here estimates Raketa's build cost.

**Sources.** tenis4U's interface text comes from the JavaScript its public demo panel
([test-panel.tenis4u.pl](https://test-panel.tenis4u.pl/), bundle `main.2b865c996e568707.js`) and its player web app
([app.tenis4u.pl](https://app.tenis4u.pl/), bundle `main.cf446af5e9523413.js`) serve to every visitor; Playmore's
from its player app bundle ([playmore.pl/assets/BIIU90LQ.js](https://playmore.pl/assets/BIIU90LQ.js)) and club pages;
Playtomic Manager's from its public locale files (`manager.playtomic.io/locales/en/*.json`). Playtomic and MATCHi help
was read through their public Zendesk API. Kraków clubs' rules and price lists are their own PDFs and pages. Nobody
signed in, booked or paid, and no endpoint was called; Polish law was read in the consolidated texts on
api.sejm.gov.pl.

**Kinds:** `[POLICY]` the company's or club's own rule, term, help or interface text · `[PRICE]` a published price ·
`[DOCS]` a provider's developer document · `[LAW]` a statute · `[COMPLAINT]` a user's complaint · `[ABSENT]` looked
for and not found, with where. Lines marked *reading* are inferences, not sources.

**A word on tenis4U's words.** In tenis4U's code and API a *court* (`court`, "kort") is the **club**, and a
*station* (`station`, "stanowisko") is the **court**: `app.tenis4u.pl/#/court/483` is Garden Padel, and the panel
reports "Przeniesiono ${n} kortów" for clubs migrated. Read "kort" in tenis4U strings with that in mind.

## Corrections to earlier files

- **tenis4U's "per-court online switch"** ([`integration.md`](integration.md) §5) is a **club-wide** switch: the
  error `COURT_DISABLED` reads "Nie można dodać rezerwacji gdyż kort ma wyłączoną możliwość dokonania rezerwacji
  online, aktywuj rezerwacje online" (a booking cannot be added because the club has online booking switched off),
  and the club list filters on `reservation_enabled`. The text "Kort ma wyłączoną możliwość rezerwacji w godzinach
  16:30 - 22:00 oraz w weekendy" is a **fixed string** returned for the error `OUT_OF_RESERVATION_MAKING_HOURS` in
  both bundles. Per court, the panel has only an *Active* toggle ("Aktywować?" / "Dezaktywować?").
  *Reading:* the hours in that string look like one club's rule baked into the text, not a setting.
- **tenis4U's block form does not warn about bookings in range.** The warning "Zaznaczony zakres pokrywa się z
  zajętymi terminami. Wyświetl zajęte terminy (n)" (attributed to the block form in
  [`gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md), read 2026-10-08) sits in the component
  `app-rep-reservation-hours`, the **standing-booking** hours picker. Both block forms
  (`app-modal-set-blocked-period`, `app-modal-set-blocked-cyclic-period`) disable *Ustaw* only while the name is empty.
- **tenis4U does have closed dates and holiday pricing**, under other words than "święto": club settings carry a tab
  "Wyłączone daty" (disabled dates, `/panel/disableDate/byCourt/{club}`) and the price list a tab "Dni weekendowe"
  ("Dodaj dzień weekendowy" — add a date that is treated as a weekend day). The earlier "no holiday anywhere in the
  club panel" ([`gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md)) searched for the word "święt" only.
- **Playtomic answers whether a changed cancellation policy reaches bookings made:** Manager shows "Your updated
  cancellation policy will only apply to new bookings and private classes" and "The cancellation policy applies to
  bookings, recurring bookings, public and private classes"
  ([venue strings](https://manager.playtomic.io/locales/en/venue.json)). This was `[ABSENT]` in
  [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md) (read 2026-10-07).

## Read this first

- **Every rival models a fixed weekly booking as a series only the desk can create.** Playtomic: "Can players
  create recurring reservations from the app? No"; MATCHi: "Subscriptions are set up by the venue, not by you";
  CourtReserve: "Members cannot set up recurring reservations". tenis4U's and Playmore's player apps show a
  "Rezerwacje stałe" list and let the player pay or cancel a session, nothing more.
- **Every rival checks the series against the calendar when it is created**, and they differ only in what happens
  to a clash: tenis4U splits the series into periods around taken dates or skips them; MATCHi lets the desk
  **overwrite (cancel) the clashing bookings** or leave those dates out; Playtomic offers "Book only free time".
- **Kraków sells standing hours by the winter season (1 October – 30 April), by 12 weeks or by the month, paid up
  front, 5–10 % off** (Fame Sport, KS Grzegórzecki, Sport Factory Park). One session can be cancelled 48 hours
  ahead (Fame Sport, KS Grzegórzecki) or 14 hours ahead (Sport Factory Park); at KS Grzegórzecki the cancelled hour
  is used another time — the *odrabianie* tenis4U tracks.
- **tenis4U's odrabianie is a real ledger:** the series is priced for its whole period, each session costs 0 zł, a
  session cancelled in time becomes "Do odrobienia {n} min" until the desk books the make-up ("Odrobiona"), and a
  series with hours still owed cannot be deleted. kluby.org sells "Abonamenty z funkcją odrabiania". Nobody abroad
  does this; MATCHi credits a value card or punch card instead.
- **Paying a series:** tenis4U can make the player pay each session online at least 3 days ahead or lose it, with a
  reminder 4 days ahead; Playmore shows the series' unpaid sessions with "Opłać zaznaczone"; MATCHi invoices the
  whole subscription or sends a payment link; Sport Factory Park takes the month in advance by the 5th.
- **A price change mid-season reaches a series only when the desk says so** (MATCHi "Update prices", Playtomic
  "Do not update the players' price"); Kraków rules say a change "nie narusza praw nabytych ani warunków usług już
  opłaconych", and the Civil Code presumes abusive a price raised after the contract without a right to withdraw.
- **Nobody moves bookings out of a new block by themselves.** MATCHi refuses a block over a booking; CourtReserve
  makes the club choose between keeping, cancelling, or rescheduling and refunding; tenis4U's and Playtomic's block
  forms say nothing. Two Kraków clubs' 2026 rules say moving a booking to another comparable court at the same club
  "nie stanowi odwołania rezerwacji" — and at KS Grzegórzecki "nie wymaga zgody" of the booker.
- **"Blokada wzajemna" is linked courts:** "Wybrane stanowiska będą blokowane w obie strony ←→" — a booking on
  one court blocks its linked courts both ways. Playtomic (*Shared courts*, with the example "Tennis 1 and
  Badminton 1 & 2"), MATCHi (*Shared resource*, set up only by MATCHi support) and CourtReserve (*Combo courts*) have
  it. No Kraków club was found that sells one hall two ways.
- **Weather:** tenis4U alone has a *flooded* status ("Ustawić status zalany?") that warns a booker and lets him
  cancel until the start; Kraków clubs refund a weather closure (Garden Padel minus 2 %; Fame Sport at no cost);
  Playmore refunds to its wallet. Nobody issues an automatic rain check.

---

## Area 4 — Season and fixed bookings

### S1. A standing weekly booking (the series)

**What it covers.** One customer, one court, one weekday and hour, repeating between two dates: creating it,
what happens when a date is taken, moving it, ending it.

**Who has it.**
- **[POLICY] tenis4U** — panel buttons "Dodaj rezerwację stałą" and, on a clash, "Tworzenie kilku rezerwacji
  stałych"; the form asks "Data rozpoczęcia", "Data zakończenia", "Stanowisko", "Dzień tygodnia", "Wariant
  cennika", "Płatność", "Telefon", "Imię i nazwisko", "Uwagi", "Wiadomość", a coach and lighting. A clash shows
  "Wybrany termin pokrywa się z istniejącymi rezerwacjami. Rezerwacja stała zostanie podzielona na następujące
  okresy:" (the series will be split into these periods), or "Możesz zaznaczyć wybraną godzinę. Jeżeli to zrobisz,
  rezerwacje stałe zostaną utworzone z pominięciem kolidujących terminów" (tick the hour and the taken dates are
  skipped). Moving a series: "Zmiany zostaną wprowadzone począwszy od pierwszego terminu w następnym tygodniu (brak
  zmian w bieżącym tygodniu)" (changes apply from next week). Ending old series in bulk: "Wybierz datę, przed którą
  rezerwacje mają zostać zakończone". Calls `/panel/reservation/repeatable/{court}`, `…/move/{id}`,
  `…/finish`, `…/cancel/{id}` ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). Listed in
  every FULL plan, 49–149 zł a month ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] Playmore** — the desk "nadal przyjmuje gotówkę, kartę i przelew oraz wpisuje rezerwacje stałe" (still
  takes cash, card and transfer and enters standing bookings) ([join.playmore.pl](https://join.playmore.pl/));
  "Grafik bez konfliktów - system pilnuje kalendarza i rezerwacji cyklicznych"
  ([squash](https://join.playmore.pl/dla-klubow-squasha/)). The player sees "Szczegóły rezerwacji stałej" with
  "Data zakończenia" or "Stały termin, do odwołania" (open-ended, until cancelled)
  ([player strings](https://playmore.pl/assets/BIIU90LQ.js)). **[ABSENT]** the club panel itself (not public).
- **[POLICY] kluby.org** — "Rezerwacje cykliczne" ([funkcje](https://oferta.kluby.org/funkcje)); changelog: "Podczas
  dodawania stałych rezerwacji komunikat o zajętych już terminach" (2017), "Automatyczne zapamiętywanie daty do
  kiedy przy stałych rezerwacjach" (2020), "Odwoływanie rezerwacji masowo z listy rezerwacji stałej rezerwacji"
  (2021), "Sortowanie abonamentów po dniu tygodnia i godzinie" (2022)
  ([2017](https://oferta.kluby.org/changelog?rok=2017), [2020](https://oferta.kluby.org/changelog?rok=2020),
  [2021](https://oferta.kluby.org/changelog?rok=2021), [2022](https://oferta.kluby.org/changelog?rok=2022)); a help
  video "2.13. Stałe rezerwacje" ([pomoc](https://oferta.kluby.org/pomoc)).
- **[POLICY] Playtomic Manager** — "Recurring Series": title, court, payment type "for the entire series", owner,
  other players, recurrence, start and end date; edits ask "This event" or "This and following events"; "If there
  is a conflict … You can choose Book only free time"
  ([series, 2026-06-22](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513),
  [edit, 2026-06-22](https://helpmanager.playtomic.com/hc/en-gb/articles/20534255539473)). Split and single payment
  cannot be swapped: "the series would need to be cancelled and recreated".
- **[POLICY] MATCHi** — a *subscription* is "the same court, same weekday, and same start time, repeating at a set
  interval for a defined date range", every 1 to 7 weeks; at the confirm step "you can either overwrite the
  conflicting bookings or go back … Overwriting cancels the conflicting bookings"; editing regenerates bookings and
  removes those outside the new range "regardless of whether they are in the past or future"; an Excel import takes
  many at once ([Subscriptions, 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/11467454905373),
  [Add subscription](https://matchi.zendesk.com/hc/en-gb/articles/11467423088285)). A lighter "Recurring" booking
  makes independent bookings with "no shared series record"
  ([2026-09-09](https://matchi.zendesk.com/hc/en-gb/articles/11467157346589)).
- **[POLICY] Eversports** — "a recurring booking (every x-days at the same hour)": end time, interval, number of
  bookings, and whether "charged separately each time or collectively (in one single invoice). This last setting
  cannot be adapted afterwards"
  ([guide](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] CourtReserve** (US, for contrast) — daily, weekly, monthly or custom recurrence with "Exception Dates";
  "Members cannot set up recurring reservations on the member portal"
  ([2026-02-20](https://help.courtreserve.com/en/articles/4852028-recurring-reservations-and-lessons)).

**The desk's day with it.** In tenis4U the desk picks a court, weekday, two dates and a price variant, and the
panel shows the dates that clash before saving; the series then lives in a list with comment, colour, payments and
a move action that starts next week. In MATCHi the desk can bulk-import a season's subscriptions from Excel and
decide per clash whether to cancel the other booking. *Reading:* the season's first week (late September) is when
a Kraków desk enters the bulk of its series.

**What a Kraków desk does today.** **[POLICY]** Fame Sport: "Klub może umożliwiać dokonywanie stałych rezerwacji
kortów na okres 12 tygodni, sezon letni, sezon zimowy lub inny okres" (III.1)
([regulamin, from 2026-08-30](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf));
KS Grzegórzecki: "na określony okres, dzień tygodnia i godzinę" (III.1)
([regulamin, from 2026-08-30](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf));
Garden Padel: "Rezerwacje stałych terminów można uzgodnić indywidualnie z administratorem"
([regulamin 4](https://gardenpadel.pl/regulamin)); Sport Factory Park: a standing booking is "rezerwację danego
terminu (abonament) na miesiąc lub dłużej na wszystkie wyznaczone terminy", booked "osobiście w recepcji klubu lub
telefonicznie" ([regulamin](https://sportfactorypark.pl/wp-content/uploads/2021/09/Regulamin-obiektu-Sport-Factory-Park.pdf)).
All four sell on tenis4U (carried from [`integration.md`](integration.md), 2026-10-12).

**What it means for the player app.** Rivals show a series to its holder as a list of dated sessions with a status
each (tenis4U and Playmore "Rezerwacje stałe", MATCHi a subscription card on the profile). *Reading:* every hour a
series holds is an hour the Games deck cannot offer, and a series is created at the desk, never from the app.

**Market signal.** Table stakes — every rival read has it.

### S2. Selling and paying for a season

**What it covers.** How the series is paid (upfront, monthly, per session, invoice, deposit), at what discount, and
who the customer is (a person, a company, a group of four).

**Who has it.**
- **[POLICY] tenis4U** — payment per series "W klubie" (`COURT_MANAGED`) or "Online" (`TENIS4U_ONLINE`): "Aktywując
  opcję płatności online stałej rezerwacji, każdy pojedynczy termin będzie musiał być opłacony online przez gracza
  min 3 dni wcześniej. W przypadku braku opłacenia terminu jest on odwoływany. Gracz otrzymuje 4 dni wcześniej
  powiadomienie przypominające o konieczności opłacenia najbliższego terminu" (each session paid online at least 3
  days ahead or cancelled; reminder 4 days ahead); a series shows "Do zapłaty", "Zapłacono", "Cena pojedynczej
  rezerwacji"; "Stała rezerwacja nie może zostać usunięta ponieważ nie została opłacona w całości"
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). The player pays at
  `/reservation/repeatable/{uuid}/pay` ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)). Pitch:
  "Możliwość pobierania opłat online … zarówno jednorazowych jak i stałych" ([tenis4u.pl](https://tenis4u.pl/)).
  **[ABSENT]** any invoice ("faktur", "NIP") in the panel strings.
- **[POLICY] Playmore** — the player's series view: "Pozostało do zapłaty", "Łączna kwota", per-session "Opłacona",
  "Nieopłacona", "Płatność w toku", "Zaznacz wszystkie nieopłacone" → "Opłać zaznaczone"; or "Tej serii nie
  opłacisz online — rozlicz się na recepcji klubu" ([player strings](https://playmore.pl/assets/BIIU90LQ.js));
  invoices through Fakturownia, "przygotowane na KSeF" ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] kluby.org** — "Automatyczne rozliczanie abonamentów podczas dodawania" (2017), "Możliwość wysłania
  szczegółów abonamentu/karnetu poprzez SMS/E-MAIL" (2018), "Tworzenie grup do istniejących stałych rezerwacji"
  (2021), "Możliwość zapisania domyślnych cen abonamentu", "Dodawanie więcej niż jednej płatności w abonamentach i
  karnetach", "Przypisywanie do grupy stałej rezerwacji" (2022)
  ([2018](https://oferta.kluby.org/changelog?rok=2018), [2021](https://oferta.kluby.org/changelog?rok=2021),
  [2022](https://oferta.kluby.org/changelog?rok=2022)); "Płatności jednorazowe i cykliczne"
  ([funkcje](https://oferta.kluby.org/funkcje)).
- **[POLICY] Playtomic** — pay at the club ("Mark as paid") or in the app, where players "need to accept the booking
  and move to check out"; "there is no pre-authorization … not automatically enforced on players. The club will need
  to follow up"; "each booking must be paid individually"
  ([series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513)). A *Recurring Wallet Benefit* gives
  members "a fixed monthly credit" that resets or accumulates
  ([2026-07-31](https://helpmanager.playtomic.com/hc/en-gb/articles/37631478400401)).
- **[POLICY] MATCHi** — a separate *subscription price list* ("applies to subscriptions"), with no fallback: "Missing
  price list for subscription"; at creation "Send payment link" or "Mark as paid"; invoicing a subscription makes one
  row "covering the full subscription period", with VAT and an optional discount
  ([price list](https://matchi.zendesk.com/hc/en-gb/articles/33350973736733),
  [invoice](https://matchi.zendesk.com/hc/en-gb/articles/11677083525917)). The player pays from the subscription
  card ([player help](https://matchiplayers.zendesk.com/hc/en-gb/articles/15950374522525)).
- **[POLICY] Eversports** — a *Subscription* product "for a whole season Sept. to June on Monday evenings", sold
  "only when you make a recurring registration"; billing per session or "in one single invoice"
  ([guide](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] CourtReserve** — "a separate fee for each individual occurrence … separate unpaid charges"
  ([recurring](https://help.courtreserve.com/en/articles/4852028-recurring-reservations-and-lessons)).

**The desk's day with it.** At tenis4U the desk either records cash per series ("Zapłacono kwotę") or switches the
series to online and lets the reminder and the 3-day lapse collect it. At MATCHi it invoices a season in one batch.
*Reading:* only MATCHi and kluby.org treat a season as an invoiceable contract; tenis4U treats it as a run of
sessions with a balance.

**What a Kraków desk does today.**
- **[PRICE]** Fame Sport: "Abonament na 1h w tygodniu na cały sezon zimowy/letni" 10 % off; "… na okres 12 tygodni"
  5 % ([cennik](https://famesport.pl/cennik/)); KS Grzegórzecki the same 10 % / 5 %
  ([cennik](https://grzegorzecki.pl/cennik/)).
- **[POLICY]** Fame Sport: "Warunkiem aktywacji stałej rezerwacji jest wniesienie wymaganej opłaty" (III.2); "Wpłacona
  kwota za abonament może zostać wykorzystana w okresie 12 miesięcy … niewykorzystane środki wygasają" (III.5);
  "Stała rezerwacja może być wykorzystywana przez osobę, która jej dokonała, albo przez wskazane przez nią osoby
  trzecie" (III.7 — the holder may pass it on)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY]** Sport Factory Park: "Stała rezerwacja jest możliwa tylko po opłaceniu z góry co najmniej czterech
  gier w miesiącu", paid "z góry za cały miesiąc najpóźniej do 5 dnia bieżącego miesiąca"
  ([regulamin](https://sportfactorypark.pl/wp-content/uploads/2021/09/Regulamin-obiektu-Sport-Factory-Park.pdf)).
- **[ABSENT]** A deposit (zaliczka, kaucja) on a season, a company or invoice customer, or a price for a group of
  four, in the rules and price lists of Fame Sport, KS Grzegórzecki, Sport Factory Park, Garden Padel, Atras,
  Squash4You and Paolo.

**What it means for the player app.** Playmore and MATCHi let the holder pay the series from the app; tenis4U sends
a reminder and cancels an unpaid session. *Reading:* if the holder is one person and three others play, the series
holder is the one a split or a reminder reaches — no Kraków rule names the other three.

**Market signal.** Recording payment at the desk: table stakes. Online pay per session with auto-lapse (tenis4U)
and one invoice for the season (MATCHi, Eversports, kluby.org): differentiators.

### S3. Price changes mid-season

**What it covers.** A new price list starting during a season, and whether it reaches series already sold.

**Who has it.**
- **[POLICY] MATCHi** — "The price shown is the price captured when the subscription was created. It only gets
  recalculated … if an admin explicitly updates the price"; "Update prices … MATCHi superadmins only"; updating "does
  not change any invoice that's already been created"; a copy to the next season is repriced from that season's
  list ([Add subscription](https://matchi.zendesk.com/hc/en-gb/articles/11467423088285),
  [price list](https://matchi.zendesk.com/hc/en-gb/articles/33350973736733)). Its invoicing article also says prices
  are recalculated "automatically when a slot is removed from the subscription"
  ([invoice subscriptions](https://matchi.zendesk.com/hc/en-gb/articles/11697392090269)) — the two articles differ.
- **[POLICY] Playtomic** — on a series edit, "Do not update the players' price"; a series made at the default price
  follows the price configuration, one with a custom price does not
  ([series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513)).
- **[POLICY] tenis4U** — price lists carry dates; "Data trwania stałej rezerwacji wykracza poza zakres danego
  cennika ({date})" (the series runs past the end of its price list)
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[ABSENT]** Playmore, kluby.org, Eversports: nothing on repricing a series.

**The desk's day with it.** *Reading:* tenis4U stops a series that outruns its price list at creation, so a desk
selling October–April needs a price list that covers April; MATCHi keeps the old price until someone presses
*Update prices*.

**What a Kraków desk does today.**
- **[PRICE]** Sport Factory Park, hall, autumn–winter 2026-27 from 1 Oct: Mon–Fri 120 / 100 / 130 zł (7–11 / 11–14 /
  14–23), weekends and holidays 130 / 120 zł, with "*ceny w trakcie sezonu zimowego mogą ulec zmianie" (prices may
  change during the winter season) ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)).
- **[POLICY]** Fame Sport and KS Grzegórzecki: a rule change "nie narusza praw nabytych ani warunków usług już
  opłaconych" (VII.5 / VII.4)
  ([Fame Sport](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf),
  [KSG](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf)).
- **[LAW]** Presumed abusive in a consumer contract: clauses that "przewidują uprawnienie kontrahenta konsumenta do
  określenia lub podwyższenia ceny lub wynagrodzenia po zawarciu umowy bez przyznania konsumentowi prawa odstąpienia
  od umowy" (art. 385³ pkt 20 k.c.), and "do jednostronnej zmiany umowy bez ważnej przyczyny wskazanej w tej umowie"
  (pkt 10) ([Kodeks cywilny, Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf)).
  Carried: UOKiK — new prices reach a later automatic charge "only with the prior consent of the consumer"
  ([`local-market.md`](../games-and-fill-in/topics/local-market.md), 2026-10-06).

**What it means for the player app.** *Reading:* a holder who paid upfront has a price fixed in money; a holder who
pays per session (tenis4U online, Sport Factory monthly) meets the new price at the next charge, which is where the
law above bites.

**Market signal.** Rare as a feature (MATCHi only); every rival otherwise leaves sold series at their old price.

### S4. Cancelling one week, and making the hour up (odrabianie)

**What it covers.** The holder skips a week; whether the money is lost, credited, or the hour is played later; how
used and owed hours are tracked.

**Who has it.**
- **[POLICY] tenis4U** — "Aktywując opcję odrabiania rezerwacji stałej ustalasz jej cenę za cały okres jej trwania
  (od daty rozpoczęcia do zakończenia). Koszt pojedynczego terminu wynosi wtedy 0 zł. Po odwoływaniu rezerwacji
  pojedynczej gracz ma możliwość odrobienia niewykorzystanego terminu" (the series is priced for its whole period,
  each session costs 0 zł, and a cancelled session can be made up). Session statuses: "Wykorzystana" (used), "Do
  wykorzystania" (to come), "Do odrobienia {n}min" (owed), "Odrobiona" (made up), "Odwołana" (cancelled); the desk
  types the minutes made up; "Nie można usunąć rezerwacji stałej, która posiada godziny do odrobienia. Najpierw
  należy odrobić zaległe godziny, a następnie usunąć rezerwację stałą"
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)); separate cut-offs, "{n} godzin przed
  rozpoczęciem można odwołać rezerwację stałą" or "możliwość odwołania rezerwacji stałej w dowolnym momencie"
  ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js); carried from
  [`platforms.md`](../games-and-fill-in/topics/platforms.md), 2026-10-08). Pitch: "Dodawanie stałych terminów, wraz z
  monitorowaniem godzin wykorzystanych i odrobionych" ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] kluby.org** — "Abonamenty z funkcją odrabiania" ([funkcje](https://oferta.kluby.org/funkcje)); for
  classes, "informacje o odwołanych i odrobionych zajęciach" (2018,
  [changelog](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] Playmore** — a series lists "Anuluj termin" per session and collapses "terminy anulowane bez kosztów co
  najmniej {days} dni przed grą" ([player strings](https://playmore.pl/assets/BIIU90LQ.js)). Its odrabianie
  ("Do odrobienia", "Odrabianie") is an attendance status for **classes**, not courts.
- **[POLICY] MATCHi** — a player can "always cancel a subscription booking online", the deadline deciding only the
  refund; the venue chooses refund "when resource is made available" or "at new reservation" (only once another
  customer books and pays), as credit note, value card, or "exactly one punch back per cancelled slot"
  ([venue](https://matchi.zendesk.com/hc/en-gb/articles/11676666349981),
  [player](https://matchiplayers.zendesk.com/hc/en-gb/articles/13948427012509)).
- **[POLICY] Playtomic** — cancel one occurrence, "not the entire series"; "Participants can leave a recurring
  booking match at any time. The club's cancellation policy only applies to the booking owner"
  ([cancel](https://helpmanager.playtomic.com/hc/en-gb/articles/29028284447121),
  [series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513)).

**The desk's day with it.** At tenis4U the desk opens the series, sees owed minutes per date, books the make-up hour
and types the minutes received. At MATCHi nothing is typed: the credit lands on a value or punch card.

**What a Kraków desk does today.**
- **[POLICY]** KS Grzegórzecki: "Odwołanie pojedynczego terminu w ramach stałej rezerwacji jest możliwe najpóźniej
  48 godzin przed jego rozpoczęciem. W przypadku zachowania tego terminu Klub umożliwi wykorzystanie opłaconego
  wstępu w innym dostępnym terminie" (cancel 48 h ahead and the paid hour is used another time); later, "termin
  uznaje się za wykorzystany" (III.5–6)
  ([regulamin](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf)).
- **[POLICY]** Fame Sport: "Pojedynczy termin … można bezkosztowo odwołać najpóźniej 48 godzin przed jego
  rozpoczęciem"; later "Klub pobiera pełną opłatę" (III.8–9)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY]** Sport Factory Park: "Istnieje możliwość zmiany daty stałej rezerwacji lub jej odwołania najpóźniej na
  14 godziny przed zaplanowaną grą"; a known absence lets the holder "wcześniej przenieść ten termin na inny dzień,
  nie ma możliwości pomniejszenia opłaty za abonament" (move it, no reduction)
  ([regulamin](https://sportfactorypark.pl/wp-content/uploads/2021/09/Regulamin-obiektu-Sport-Factory-Park.pdf)).
- **[POLICY]** Squash4You moves money paid online for a booking cancelled in time "na kolejną, najbliższą rezerwację
  ale nie podlega zwrotowi" ([regulamin §5h](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** *Reading:* in Kraków a standing hour cancelled in time is a debt of court time
the club owes the holder, not money returned; an app that lists his sessions would show hours owed and made up.

**Market signal.** Table stakes in Polish tennis software (tenis4U, kluby.org); rare abroad, where a credit replaces
the make-up hour.

### S5. Holidays inside a season

**What it covers.** 1 and 11 November, 24–26 December, 1 and 6 January, Easter, 1 and 3 May, Corpus Christi
falling inside a weekly series; whether the session is skipped, charged, or moved.

**Who has it.**
- **[POLICY] MATCHi** — "If you need to cancel just one occurrence (e.g. a holiday), you can remove individual
  bookings from the subscription … the subscription's price and VAT are automatically recalculated"
  ([2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/14564545295645)).
- **[POLICY] CourtReserve** — "Exception Dates … when the court/lesson won't take place"
  ([recurring](https://help.courtreserve.com/en/articles/4852028-recurring-reservations-and-lessons)).
- **[POLICY] tenis4U** — "Wyłączone daty" (whole-day club closures) and "Dni weekendowe" (a date priced as a
  weekend) ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). **[ABSENT]** what either does to
  a standing series' sessions on that date.
- **[ABSENT]** Playtomic, Playmore, kluby.org, Eversports: a rule for a series that meets a holiday (Playtomic
  Holidays and kluby.org's 2018 "dni świątecznych, wykluczonych oraz wolnych od pracy" exist, effect on series
  unstated).

**The desk's day with it.** *Reading:* with no rule in the software, a desk deletes the holiday sessions one by one,
or leaves them and lets the holder not come.

**What a Kraków desk does today.**
- **[POLICY]** Sport Factory Park's academy publishes its own days off for 2026/27 — 01.11, 11.11, 24–26.12, 31.12,
  01.01, 06.01, 15–28.02 (ferie), 27–29.03, 01–03.05, 27.05 — and its monthly fee "nie podlega zmniejszeniu z tytułu
  świąt" (classes, not court series) ([umowa §3, §11](https://sportfactorypark.pl/wp-content/uploads/2026/08/regulamin-umowa-WERSJA-2026_2027-1-1.pdf)).
- **[POLICY]** Atras: "może być nieczynny w dni ustawowo wolne od pracy, a także w dni znajdujące się pomiędzy dniami
  ustawowo wolnymi" (may close on public holidays and bridge days) ([regulamin §1](https://www.atrassquash.pl/regulamin/)).
- **[PRICE]** Sport Factory Park prices "Sobota, niedziela oraz święta" together
  ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)).
- Carried: 1 Nov falls on a Sunday in 2026 and 24 Dec is a day off since 2025; POSiR Poznań: "a standing booking on a
  holiday simply does not happen" ([`situations.md`](../games-and-fill-in/situations.md) SIT-26, 2026-10-06).
- **[ABSENT]** A Kraków rule on whether a season price already counts the holidays out.

**What it means for the player app.** *Reading:* a holder whose Wednesday falls on 11 November either sees it as
skipped, owed, or still booked; nobody's rule says which.

**Market signal.** Rare — only MATCHi and CourtReserve document it.

### S6. The club cancels or moves a season session

**What it covers.** A tournament, repair or weather takes the court on a series date; refund, credit, replacement
hour, or a different court.

**Who has it.**
- **[POLICY] MATCHi** — the admin picks "Cancel and give a full refund", "(customer pays cancellation fee)" or
  "Cancel without giving a refund", with an optional message (carried from
  [`platforms.md`](../games-and-fill-in/topics/platforms.md), 2026-10-07); a cancelled subscription booking "doesn't
  affect the subscription itself" and triggers the venue's refund setting
  ([refund settings](https://matchi.zendesk.com/hc/en-gb/articles/11676666349981)).
- **[POLICY] tenis4U** — "Automatyczny zwrot opłaty następuje przy usunięciu rezerwacji przed jej rozpoczęciem"
  (deleting an online-paid booking before it starts refunds it automatically)
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)); with odrabianie on, the session becomes
  owed minutes instead (S4).
- **[POLICY] Playtomic** — a club cancellation refunds in full (carried,
  [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md), 2026-10-08); a move stays on "another court
  of the same size" (carried, same file).

**The desk's day with it.** *Reading:* with tenis4U, cancelling a prepaid-season session either refunds online money
or leaves an owed hour, depending on how the series was set up — the desk has no third choice.

**What a Kraków desk does today.**
- **[POLICY]** Fame Sport: a session the club cancels "opłata za ten termin nie przepada … Klub w takim przypadku
  zaproponuje inny termin, a jeżeli nie będzie to możliwe - odpowiednia część środków zostanie przywrócona do
  wykorzystania albo zwrócona"; "Klub może zaproponować zmianę kortu lub godziny stałej rezerwacji … Jeżeli zmiana w
  istotny sposób zmienia warunki rezerwacji i klient jej nie zaakceptuje, niewykorzystana część wniesionej opłaty
  podlega zwrotowi" (III.10–12)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf));
  KS Grzegórzecki the same (III.7–8)
  ([regulamin](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf)).
- **[POLICY]** Both: "Zmiana numeru kortu w ramach obiektu na kort o porównywalnych warunkach do gry nie stanowi
  odwołania rezerwacji" (moving to a comparable court at the same club is not a cancellation; Fame Sport II.20); KSG
  adds "i nie wymaga zgody osoby dokonującej rezerwacji" (II.13).
- **[POLICY]** Squash4You: a pass is refunded only if "Klub zawiesił usługi na okres przekraczający 7 dni – wówczas
  klientowi przysługuje proporcjonalny zwrot lub przedłużenie karnetu" ([regulamin §9](https://www.squash4you.pl/regulamin)).

**What it means for the player app.** *Reading:* the Kraków rule of 2026 matches the founder's decision of
2026-10-12 for one-off games — another comparable court at the same club is not a cancellation — and extends the
same idea to standing bookings.

**Market signal.** Cancel-and-refund: table stakes. Offering another hour first, then credit or refund: Kraków
practice, which only tenis4U's owed-minutes ledger supports.

### S7. Renewing into the next season

**What it covers.** Copying this season's series into the next, and the holder's first right to keep his hour.

**Who has it.**
- **[POLICY] MATCHi** — "Copy to a new season": customer, court, weekday, time and interval are copied, pricing is
  recalculated; a slot not open in the new season is skipped; a clash copies the series "just without the
  occurrences that overlap"; a scheduled "update subscription price for next season" job exists
  ([extend, 2026-09-14](https://matchi.zendesk.com/hc/en-gb/articles/11467505708829),
  [invoice](https://matchi.zendesk.com/hc/en-gb/articles/11697392090269)).
- **[POLICY] tenis4U** — only a bulk end ("Lista rezerwacji do usunięcia przed terminem {date}")
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). **[ABSENT]** a copy or renewal.
- **[ABSENT]** Playtomic, Playmore, kluby.org, Eversports: a renewal or copy of a series.

**The desk's day with it.** *Reading:* without a copy, the desk re-enters every holder in late September and must
hold their hours against online sale until they do.

**What a Kraków desk does today.** **[POLICY]** Fame Sport: "Osoba posiadająca stałą rezerwację może mieć
pierwszeństwo w przedłużeniu dotychczasowego terminu na kolejny okres, pod warunkiem dokonania przedłużenia w terminie
określonym przez Klub" (III.6)
([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)); Sport
Factory Park: "Aby przedłużyć stałą rezerwację należy, najpóźniej do 5 dnia kolejnego miesiąca opłacić kolejne
cztery lub więcej gier" ([regulamin](https://sportfactorypark.pl/wp-content/uploads/2021/09/Regulamin-obiektu-Sport-Factory-Park.pdf)).
**[ABSENT]** the renewal deadline any Kraków club sets.

**What it means for the player app.** *Reading:* a holder's renewal is a date he can miss; nothing read reminds him.

**Market signal.** Differentiator — MATCHi alone.

### S8. The season as a calendar (winter domes, October–April prices)

**What it covers.** Two seasons a year with their own opening hours and prices; the winter dome over outdoor courts.

**Who has it.**
- **[POLICY] MATCHi** — "the most common approach is two seasons per year"; a season sets opening hours per court
  per weekday, cannot overlap, and is shortened only after its bookings are handled; "Price lists are independent";
  an outdoor season is "a dedicated season for the outdoor period"
  ([Seasons, 2026-09-09](https://matchi.zendesk.com/hc/en-gb/articles/11719070245533),
  [outdoor courts](https://matchi.zendesk.com/hc/en-gb/articles/18666276461597)).
- **[POLICY] tenis4U** — dated price lists ("tariff" `starts_at` / `ends_at`, carried from
  [`gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md), 2026-10-08). Playtomic *Timed Prices*, Eversports
  "time ranges" (carried, [`areas/COURTS.md`](../games-and-fill-in/areas/COURTS.md)).

**The desk's day with it.** *Reading:* at a dome club the courts change roof on the day the dome goes up, not on a
date fixed in advance.

**What a Kraków desk does today.**
- **[PRICE]** Fame Sport "KORTY TENIS HALA - ZIMA 01.10.2026 - 30.04.2027" ([cennik](https://famesport.pl/cennik/));
  Sport Factory Park "SEZON JESIEŃ-ZIMA 2026-2027 … od 01.10.2026"
  ([cennik](https://sportfactorypark.pl/cennik-tenis-2/)); KS Grzegórzecki "KORTY BALON (SEZON ZIMOWY) OD
  URUCHOMIENIA BALONU DO 30.04.2026" — from whenever the dome is up (page still shows last season on 2026-10-12)
  ([cennik](https://grzegorzecki.pl/cennik/)).
- **[COMPLAINT]** At Korty Białoprądnicka (tenis4U): "Regularne hałasy i przekleństwa z kortów słyszane bardzo dobrze
  także spod balona po ciszy nocnej" (Google review quoted on Playmore's page)
  ([Playmore](https://playmore.pl/klub/korty-bialopradnicka-krakow/)).

**What it means for the player app.** *Reading:* a court's roof and price change with the season, and in a dome
club the change date is not known ahead.

**Market signal.** Table stakes (dated prices everywhere; full seasons in MATCHi).

---

## Area 5 — Blocks and closures

### B1. A one-off block (maintenance, an event, a tournament)

**What it covers.** Taking one or more courts out for a stretch of time, named, without a customer.

**Who has it.**
- **[POLICY] tenis4U** — "Dodaj blokadę stanowiska": "Nazwa", "Początek", "Zakończenie", courts ("Dodaj blokadę do
  stanowisk"); listed under "Blokady stanowiska" / "Pokaż blokady"; deleted one at a time ("Usunąć blokadę?"), not
  edited; the calendar filter has "tylko blokady"
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js); add/delete only carried from
  [`gaps-COURTS.md`](../games-and-fill-in/topics/gaps-COURTS.md), 2026-10-08).
- **[POLICY] Playtomic** — a *Blocking* ("Block a court — Mark courts as unavailable") for "Maintenance Management"
  and "Weather Closures", left out of occupancy ([Schedule basics, 2026-03-09](https://helpmanager.playtomic.com/hc/en-gb/articles/20560058451985));
  editable ("Edit availability blocking") ([schedule strings](https://manager.playtomic.io/locales/en/schedule.json)).
- **[POLICY] MATCHi** — internal booking types "Not available, Training, or Competition", which "won't accept online
  bookings" ([2026-09-16](https://matchi.zendesk.com/hc/en-gb/articles/14578562110365)).
- **[POLICY] kluby.org** — "blokowania wszystkich wolnych połówek danego dnia w wybranym przedziale czasowym" (2017,
  carried from [`platforms.md`](../games-and-fill-in/topics/platforms.md)).
- **[POLICY] Eversports** — "Profile > Court Blockings"
  ([guide](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] CourtReserve** — *Closures* with a type ("Weather, Maintenance, etc."), start and end, courts, and a
  "Display Message for the Schedulers" ([2026-06-03](https://help.courtreserve.com/en/articles/4444359-how-to-close-courts)).

**The desk's day with it.** Every rival puts a block on the calendar as its own coloured item. *Reading:* the
difference is only what happens to bookings already there (B7).

**What a Kraków desk does today.** **[POLICY]** Fame Sport and KSG reserve "określone korty lub godziny na potrzeby
zajęć szkoleniowych, trenerów, zawodów, turniejów lub innych wydarzeń" (Fame Sport I.11)
([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)); Atras
keeps "imprez zamkniętych" outside its rules ([regulamin §1](https://www.atrassquash.pl/regulamin/)).

**What it means for the player app.** **[ABSENT]** A label naming a block in tenis4U's player app (it shows only
"nieczynne" on a club card) ([app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)). *Reading:* players see
a blocked hour as simply not free.

**Market signal.** Table stakes.

### B2. A weekly recurring block

**What it covers.** The same block every week — a Wednesday school group, a league night, a weekly cleaning slot.

**Who has it.**
- **[POLICY] tenis4U** — the form "Wybierz dzień tygodnia dla którego ustawiona zostanie blokada we wskazanym
  przedziale czasowym" builds **one separate block per date** for the chosen weekday and courts, previewed as
  "Ustawiasz blokadę w terminach:" ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
  *Reading:* there is no series to edit or delete; ending it means deleting each date.
- **[POLICY] MATCHi** — a deviation has a date range and "Days … at least one day" and "Close" removes unbooked slots
  ([deviations, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11719720215453)); "For a fully recurring
  weekly block, consider setting it up as a repeating internal booking"
  ([block courts](https://matchi.zendesk.com/hc/en-gb/articles/14578562110365)).
- **[POLICY] CourtReserve** — "Recurrence: Daily, Weekly, Monthly, or Custom"; "editing the parent row will apply
  changes to the series" ([close courts](https://help.courtreserve.com/en/articles/4444359-how-to-close-courts)).
- **[POLICY] Playtomic** — its Blocking feedback form asks whether clubs want "Ability to create recurring blockings"
  ([schedule strings](https://manager.playtomic.io/locales/en/schedule.json)); a *Recurring series* ("Multiple courts
  allowed") is the nearest tool.

**The desk's day with it.** *Reading:* a desk that blocks a school's Wednesdays for a season at tenis4U creates ~30
blocks in one go and removes them one by one.

**What a Kraków desk does today.** **[ABSENT]** A published Kraków rule or notice about weekly internal blocks.

**What it means for the player app.** Same as B1.

**Market signal.** Table stakes in desk software (tenis4U, MATCHi, CourtReserve); missing in Playtomic.

### B3. Closed dates and holiday hours

**What it covers.** Whole days the club is shut (Christmas Eve), and holiday days that keep different hours or prices.

**Who has it.**
- **[POLICY] tenis4U** — "Wyłączone daty" (a date list per club, "Błąd podczas pobierania listy wyłączonych dat") and
  "Dni weekendowe" ("Dodaj dzień weekendowy") ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
- **[POLICY] Playtomic** — a *Holiday* with start and end date and time, "a specific court or the whole club", to
  "block your schedule from online reservations" ([2026-03-31](https://helpmanager.playtomic.com/hc/en-gb/articles/20535276328849));
  "Add holidays to block bookings on your club calendar" ([holidays strings](https://manager.playtomic.io/locales/en/holidays.json)).
- **[POLICY] Eversports** — "Profile > Holidays … what price you will be charging on that day (i.e. if you are open on
  Christmas day and it is on Monday … the price of a Sunday)"
  ([guide](https://helpcenter.eversportsmanager.com/en/start-with-eversports-ballsport-manager-1)).
- **[POLICY] kluby.org** — "Wprowadzenie dni świątecznych, wykluczonych oraz wolnych od pracy" (2018)
  ([changelog](https://oferta.kluby.org/changelog?rok=2018)).
- **[POLICY] MATCHi** — deviations "for holidays" ([deviations](https://matchi.zendesk.com/hc/en-gb/articles/11719720215453)).
- **[POLICY] Playmore** — players see "Klub tymczasowo nieczynny do {date}" ([player strings](https://playmore.pl/assets/BIIU90LQ.js)).

**The desk's day with it.** *Reading:* tenis4U, Eversports and kluby.org price a holiday as another day type;
Playtomic and MATCHi date a price or a deviation.

**What a Kraków desk does today.** **[POLICY]** Atras may close on public holidays and bridge days
([regulamin](https://www.atrassquash.pl/regulamin/)); Sport Factory Park prices holidays with weekends
([cennik](https://sportfactorypark.pl/cennik-tenis-2/)); Garden Padel "ma prawo zamknąć obiekt w przypadku złych
warunków atmosferycznych, technicznych lub epidemiologicznych" ([regulamin 3](https://gardenpadel.pl/regulamin)).

**What it means for the player app.** *Reading:* a closed date has to reach a player who booked weeks earlier; no
rival documents a message tied to a closed date.

**Market signal.** Table stakes.

### B4. A court off for online booking only, and time-ranged release

**What it covers.** A court the desk sells by phone only; hours online players cannot take; hours held for members
until shortly before.

**Who has it.**
- **[POLICY] Playtomic** — per court "Active Court" and "Bookable online" ([courts strings](https://manager.playtomic.io/locales/en/courts.json);
  carried from [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md), 2026-10-06).
- **[POLICY] MATCHi** — "Offline only: The court is visible in the schedule but can only be booked by administrators";
  *Booking restrictions* keep slots for a requirement profile until an expiry "relative to the slot's start — for
  example, '72 hours before'", then open them to all, and can cover a date range and weekdays
  ([court status, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/14582141635101),
  [booking restrictions, 2026-09-08](https://matchi.zendesk.com/hc/en-gb/articles/34085754893469)).
- **[POLICY] kluby.org** — "Możliwość pokazania i korzystania z obiektów wyłączonych dla klientów" (2017); a
  club-wide online switch with a reason (2022) ([2017](https://oferta.kluby.org/changelog?rok=2017),
  [2022](https://oferta.kluby.org/changelog?rok=2022)).
- **[POLICY] tenis4U** — a club-wide online switch (`COURT_DISABLED`) and a per-court Active toggle; the
  `OUT_OF_RESERVATION_MAKING_HOURS` refusal reads "Kort ma wyłączoną możliwość rezerwacji w godzinach 16:30 - 22:00
  oraz w weekendy" (see *Corrections*); a club note seen in the player app: "rezerwacja kortu na godzinę 7 oraz 8
  dostępna tylko i wyłącznie dla graczy posiadających opłacony karnet"
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js),
  [app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)).

**The desk's day with it.** *Reading:* *Offline only* is how a desk keeps prime hours for its phone regulars without
blocking them; MATCHi's restriction does the same and releases them on its own.

**What a Kraków desk does today.** Carried: Garden Padel once showed kluby.org's "Tymczasowo rezerwacje ONLINE
zostały wyłączone" ([`platforms.md`](../games-and-fill-in/topics/platforms.md), 2026-10-07); Atras sells online 10 %
cheaper "a z karnetem 15%" ([cennik](https://www.atrassquash.pl/cennik/)). **[ABSENT]** A Kraków club that publishes
which hours are desk-only.

**What it means for the player app.** *Reading:* a desk-only court is a court the Games deck cannot book either,
unless the club says otherwise.

**Market signal.** Per-court offline: table stakes. Timed release to all: differentiator (MATCHi only).

### B5. Weather and flooded courts

**What it covers.** Rain, frost or wind on outdoor courts; flagging a court unplayable; refunds, credits, replays.

**Who has it.**
- **[POLICY] tenis4U** — per court "Ustawić status zalany?" / "Usunąć status zalany?"; the booker is asked "Korty są
  obecnie zalane, czy na pewno chcesz zarezerwować kort?"; "Kort oznaczony jako zalany — możesz anulować rezerwację do
  momentu jej rozpoczęcia"; a club setting "{n} godzin przed rozpoczęciem można odwołać rezerwację jeśli korty są
  zalane - oznaczone są żółtym kolorem"; the map shows a flooded marker (`marker_zalane.png`)
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js),
  [app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js)); pitch: "po opadach deszczu możliwość informowania
  graczy o chwilowym zalaniu" ([tenis4u.pl](https://tenis4u.pl/)).
- **[POLICY] Playmore** — "Odwołujesz rezerwację w panelu, a cena rezerwacji opłaconej online wraca do gracza na
  portfel w aplikacji Playmore … Zajęcia szkółki odwołujesz z powodem „warunki pogodowe” i uczestnicy dostają
  powiadomienie z tym powodem" ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] Playtomic** — Blockings for "Weather Closures"; refunds after the deadline are the club's, "commonly
  given in cases like: Bad weather" (carried, [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md),
  2026-10-08).
- **[POLICY] CourtReserve** — closure type "Weather"; the impact table shows "Used Time - The percentage of the
  reservation used by the member prior to the court being closed"; "full or partial refund"
  ([close courts](https://help.courtreserve.com/en/articles/4444359-how-to-close-courts),
  [refunds, 2026-07-31](https://help.courtreserve.com/en/articles/8258556-issue-refunds-for-closures)).
- **[ABSENT]** MATCHi: any weather article (Zendesk search "weather", "rain").

**The desk's day with it.** *Reading:* at tenis4U a wet morning is one toggle that tells bookers and frees them to
cancel; refunding is still the desk deleting each booking.

**What a Kraków desk does today.**
- **[POLICY]** Fame Sport: "W przypadku kortów zewnętrznych ocena, czy warunki atmosferyczne pozwalają na bezpieczne
  korzystanie z kortu, należy do Klubu. W przypadku zamknięcia kortu z tego powodu klient nie ponosi kosztu" (II.21)
  ([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).
- **[POLICY]** Garden Padel: "W razie niedostępności kortu z powodu złych warunków atmosferycznych opłata zostanie
  zwrócona, z potrąceniem opłaty serwisowej operatora płatności (2%)" ([regulamin 5](https://gardenpadel.pl/regulamin)).
- Carried: KSOS replays rain mid-game within 7 days, no refund; POSiR Poznań lets players move indoors paying the
  difference ([`local-market.md`](../games-and-fill-in/topics/local-market.md),
  [`situations.md`](../games-and-fill-in/situations.md) SIT-01, 2026-10-06).
- **[COMPLAINT]** Korty Białoprądnicka: "będą już pod obiektem o 10.27 dostałem wiadomość informującą, że w tym dniu
  korty będą jednak nieczynne" (Google review quoted on Playmore's page, tagged "Odwoływanie rezerwacji w ostatniej
  chwili — 3 wzmianek") ([Playmore](https://playmore.pl/klub/korty-bialopradnicka-krakow/)).

**What it means for the player app.** *Reading:* tenis4U's flag is a warning, not a closure: the booking stands and
the player decides. The founder's outdoor→indoor move of 2026-10-12 has a Kraków precedent only at POSiR Poznań, at
the player's cost.

**Market signal.** Differentiator — tenis4U's flood flag is unique; refund-on-weather is local practice.

### B6. Linked courts ("Blokada wzajemna")

**What it covers.** One physical space sold two or more ways — a hall as one tennis court or three badminton
courts; a padel court as singles or doubles — so a booking on one blocks the other.

**Who has it.**
- **[POLICY] tenis4U** — "Blokowanie wzajemne": "Wybrane stanowiska będą blokowane w obie strony ←→" (chosen courts
  are blocked both ways), "Aktualnie połączone:", "Po zapisie:", "Wybierz stanowiska do blokowania", "Zapisz
  powiązania"; a court card reads "Blokuje: {n} stanowisk" or "Niezależne". In the calendar a linked court's hour is
  drawn blocked ("+ Blokada wzajemna: {court}", cursor `not-allowed`) whenever a booking on a linked court covers it;
  calls `/panel/station/{id}/mutual-blocks` ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)).
  **[ABSENT]** the word in the player app bundle.
- **[POLICY] Playtomic** — *Shared courts*: "When one of the linked courts is booked, the same time slot is
  automatically blocked on the other linked courts"; for "one physical court … singles and doubles" or "heated vs.
  non-heated"; set by the club in Settings → Courts ([2026-03-31](https://helpmanager.playtomic.com/hc/en-gb/articles/45292498463633));
  tooltip: "if your facility shares Tennis 1 and Badminton 1 & 2 so only one of the sports can be played at once";
  calendar label "Blocked by shared court" ([courts strings](https://manager.playtomic.io/locales/en/courts.json),
  [schedule strings](https://manager.playtomic.io/locales/en/schedule.json)).
- **[POLICY] MATCHi** — *Shared resource* ("also called linked courts"), parent–child, blocking both ways at the
  moment of booking, released on cancellation unless another linked booking still overlaps; "configured by the MATCHi
  team — there's no setting in MATCHi Admin" ([2026-09-10](https://matchi.zendesk.com/hc/en-gb/articles/28362922871837)).
- **[POLICY] CourtReserve** — *Combo courts*: "two pickleball courts that combine into one tennis court … all linked
  courts are automatically blocked" ([2026-02-02](https://help.courtreserve.com/en/articles/4360421-combo-courts)).
- **[ABSENT]** Playmore (public pages), kluby.org (changelog 2015–2026), Eversports (help center).

**The desk's day with it.** Set once per court; afterwards the calendar shows the sister courts as taken.

**What a Kraków desk does today.** **[ABSENT]** A Kraków club that sells one space two ways: Fame Sport's five
badminton courts are a "profesjonalną halę dedykowaną badmintonistom" ([famesport.pl](https://famesport.pl/badminton-krakow/)),
not laid over its tennis courts; no other club page read describes shared lines.

**What it means for the player app.** *Reading:* the deck must treat a linked court as taken when its sister is
booked; at a padel club the singles/doubles case is the likely one.

**Market signal.** Table stakes in multi-sport desk software (four of seven rivals); rare in Kraków.

### B7. Bookings already inside a new block

**What it covers.** The desk blocks a time that already holds bookings (or a closed date, or a court switched off):
refused, cancelled and refunded, moved, or left, and how the player hears.

**Who has it.**
- **[POLICY] MATCHi — refused.** "Blocking a slot that already has a booking is not possible"; a "Close" deviation
  removes unbooked slots and lists booked ones "so you can see which bookings you need to cancel first"; "Booked slots
  are always protected"; a court with future bookings cannot be archived
  ([block courts](https://matchi.zendesk.com/hc/en-gb/articles/14578562110365),
  [deviations](https://matchi.zendesk.com/hc/en-gb/articles/11719720215453),
  [court status](https://matchi.zendesk.com/hc/en-gb/articles/14582141635101)).
- **[POLICY] CourtReserve — the club chooses.** Required "Cancellation Policy Options": "No Cancellations" (existing
  reservations "will remain on the schedule"), "Cancel All Reservations & Events", "Cancel Court Reservations Only",
  "Cancel Events Only"; an impact table and a "Confirm Closure" warning; per booking, "Reschedule" or "Cancel the
  booking and issue a refund"; members see "a gray bar" beside an affected booking until it is handled
  ([close courts](https://help.courtreserve.com/en/articles/4444359-how-to-close-courts)).
- **[POLICY] tenis4U — not checked in the forms.** Neither block form looks at bookings (see *Corrections*); an
  online-paid booking deleted before it starts is refunded automatically
  ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). **[ABSENT]** what the server does with
  bookings under a new block or closed date.
- **[POLICY] Playtomic — unstated.** Holidays and Blockings say nothing about bookings in them (carried `[ABSENT]`,
  [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md), 2026-10-07; re-read 2026-10-12, unchanged);
  closing clubs are told to cancel "promptly to enable player refunds" (carried, same file); a cancelled paid booking
  is refunded automatically if paid online, "if it was paid at the club you must refund it"
  ([schedule strings](https://manager.playtomic.io/locales/en/schedule.json)).
- **[POLICY] kluby.org — free hours only.** It blocks "wolnych połówek" (carried); "Masowe odwoływanie rezerwacji"
  (2016) ([changelog](https://oferta.kluby.org/changelog?rok=2016)).
- **[ABSENT]** Any rival that moves an affected booking to a free court by itself.

**The desk's day with it.** *Reading:* in every rival the desk resolves affected bookings by hand, one at a time —
MATCHi before it may block, CourtReserve after, tenis4U and Playtomic whenever the desk notices.

**What a Kraków desk does today.** **[POLICY]** Fame Sport and KS Grzegórzecki: the club "poinformuje klienta
możliwie jak najwcześniej", "zaproponuje w miarę dostępności inny kort lub termin", else the fee is "według wyboru
klienta" credited or refunded; a comparable court at the same club "nie stanowi odwołania rezerwacji"
(II.16–20 / II.10–13) ([Fame Sport](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf),
[KSG](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf)). Carried: Playmore's
terms put the duty to tell booked players on the club (§8)
([`platforms.md`](../games-and-fill-in/topics/platforms.md), 2026-10-07). **[LAW]** Presumed abusive: clauses
giving "wyłącznie dla kontrahenta konsumenta jednostronne uprawnienie do zmiany, bez ważnych przyczyn, istotnych cech
świadczenia" (art. 385³ pkt 19 k.c.) ([Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf)).
*Reading:* whether a court number is an "istotna cecha" is untested here; the two Kraków rules name a reason
(comparable conditions) for the change.

**What it means for the player app.** *Reading:* Raketa's auto-move of 2026-10-12 would be the only automatic one
found; the nearest models are CourtReserve's per-booking reschedule and the Kraków rules' "inny kort lub termin".

**Market signal.** Differentiator — no rival moves bookings out of a block; refusing (MATCHi) and choosing
(CourtReserve) are the two documented patterns.

### B8. What the club can say to players

**What it covers.** The words that reach a player about a block, closure, weather, a cancelled or moved booking, or
a standing booking.

**Who has it.**
- **[POLICY] tenis4U** — every booking (standing ones too) has "Wiadomość": "Treść widoczna dla użytkownika, podgląd w
  panelu administracyjnym oraz w aplikacji użytkownika", beside "Uwagi" visible only in the panel; the flood notice
  (B5) ([panel bundle](https://test-panel.tenis4u.pl/main.2b865c996e568707.js)). **[ABSENT]** a message attached to
  a block or closed date.
- **[POLICY] Playtomic** — the club writes a booking-confirmation message and a match registration message (carried,
  [`competitor-club.md`](../games-and-fill-in/topics/competitor-club.md), 2026-10-08); "Users always receive emails
  and in-app notifications about any changes" (carried, same file). **[ABSENT]** a reason field on a club
  cancellation (carried; locale strings re-read 2026-10-12).
- **[POLICY] MATCHi** — an optional message to the customer on cancelling (carried); "Venues send you important
  updates directly through in-app messages", pushed to players "addressed to you or to all players at that venue"
  ([player help, 2026-09-09](https://matchiplayers.zendesk.com/hc/en-gb/articles/33106117125533)); a subscription
  comment "visible to other administrators … whether this comment should be visible to the customer"
  ([Add subscription](https://matchi.zendesk.com/hc/en-gb/articles/11467423088285)).
- **[POLICY] CourtReserve** — "Enter a reason for the cancellation (optional but recommended) … CourtReserve adds the
  reason to the email notification" ([refunds](https://help.courtreserve.com/en/articles/8258556-issue-refunds-for-closures));
  "Display Message for the Schedulers" on a closure ([close courts](https://help.courtreserve.com/en/articles/4444359-how-to-close-courts)).
- **[POLICY] Playmore** — class cancellations carry a reason ("warunki pogodowe") in the notification
  ([join.playmore.pl](https://join.playmore.pl/)).
- **[POLICY] kluby.org** — "Podgląd wysłanych powiadomień w historii klienta o rezerwacjach" (2022)
  ([changelog](https://oferta.kluby.org/changelog?rok=2022)).

**The desk's day with it.** *Reading:* outside CourtReserve, the reason a player's booking was cancelled reaches him
only if the desk types it somewhere the platform sends.

**What a Kraków desk does today.** **[POLICY]** Fame Sport and KSG inform "wykorzystując posiadane dane kontaktowe"
(phone or email they hold) ([Fame Sport II.17](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf));
Squash4You gives "co najmniej 14-dniowym wyprzedzeniem" notice of rule changes ([§18](https://www.squash4you.pl/regulamin));
Fame Sport tells holders of long contracts of material changes "z odpowiednim wyprzedzeniem" (VII.6)
([regulamin](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)).

**What it means for the player app.** *Reading:* a reason and a replacement, sent with the change, is what the
[COMPLAINT] in B5 lacked.

**Market signal.** Free-text note on a booking: table stakes. A reason carried into the cancellation message:
differentiator (CourtReserve, MATCHi).

---

## Rivals × features

Yes = documented · Part = partly or by workaround · No = documented as absent, or ruled out by documented behaviour ·
— = not found where looked (the `[ABSENT]` lines above say where).

| Feature | tenis4U | Playmore | kluby.org | Playtomic | MATCHi | Eversports | CourtReserve |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 Standing weekly series | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| S1 Clash handling at creation | Split or skip | — | Warn | Free time only | Overwrite or skip | — | Report |
| S2 Player pays the series online | Yes, per session, lapses | Yes, selected sessions | — | Yes, per booking | Yes, link or app | — | — |
| S2 One invoice for the season | — | Part (Fakturownia) | Part | No (each booking) | Yes | Yes | No (per occurrence) |
| S3 Reprice a sold series only on request | Part (price list must cover) | — | — | Yes | Yes | — | — |
| S4 Make-up ledger (odrabianie) | Yes | Classes only | Yes | — | Credit instead | — | — |
| S5 Holiday inside a series | — | — | — | — | Remove one | — | Exception dates |
| S6 Club cancels a session: refund | Yes (online) | Yes (wallet) | — | Yes | Yes (3 choices) | — | Yes |
| S7 Copy series to next season | — (bulk end only) | — | — | — | Yes | — | — |
| S8 Seasons / dated prices | Part | — | — | Part | Yes | Part | — |
| B1 One-off block | Yes | — | Yes (free hours) | Yes | Yes | Yes | Yes |
| B2 Weekly block | Part (one per date) | — | — | No (asked) | Yes | — | Yes |
| B3 Closed dates / holiday pricing | Yes / Yes | Club-wide "nieczynny" | Yes | Yes / Part | Yes | Yes / Yes | Yes |
| B4 Court offline-only | Club-wide only | — | Yes | Yes | Yes | — | — |
| B4 Timed release to all | — | — | — | — (workaround) | Yes | — | — |
| B5 Flooded / weather status | Yes | — | — | Part (block) | — | — | Part (type) |
| B6 Linked courts | Yes | — | — | Yes | Yes (by support) | — | Yes |
| B7 Bookings under a new block | Not checked in the form | — | Blocks free hours only | Unstated | Refused | Unstated | Club chooses |
| B7 Auto-move to a free court | — | — | — | — | No (refuses) | — | No (by hand) |
| B8 Reason sent to the player | Booking note | Classes | Notifications | — | Message | — | Yes |

## Gaps

- **tenis4U's server behaviour** — what happens to bookings under a new block, a closed date or a deactivated court;
  whether a booking on a mutually blocked court is refused or only drawn as blocked; what a closed date does to a
  standing series. Only the front-end was readable.
- **Playmore's club panel** is not public: how a desk creates a standing booking, blocks, holidays, repricing.
- **kluby.org's help is video only** ("2.10. Abonamenty", "2.13. Stałe rezerwacje"); the changelog stops in 2023.
- **Eversports**: what Court Blockings do to bookings; whether it links courts.
- **Kraków practice not published**: renewal deadlines; deposits; company or invoice customers; how many prime hours
  standing bookings hold; how desks treat 1 and 11 November inside a season; any rule at Park Jordana (ZZM), Tenis
  Kliny, Bajada or Padel House (no own rules page found; they book through tenis4U).
- **Playtomic**: a recurring series meeting a Holiday; a Holiday's effect on bookings in it.
- **MATCHi**: its two articles disagree on whether removing a slot reprices a subscription.
- **Law**: whether "a comparable court at the same club is not a cancellation and needs no consent" (KS
  Grzegórzecki II.13) would hold under art. 385³ pkt 19 k.c.; no ruling read. Art. 38 pkt 12 of the consumer rights
  act removes the 14-day withdrawal right from distance contracts for sport services "jeżeli w umowie oznaczono dzień
  lub okres świadczenia usługi" ([Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)) —
  how it applies to a season sold online with odrabianie was not researched.
- **No Kraków club found that sells one space two ways** — a club with a multi-sport hall would answer whether B6
  matters locally.
