# Gaps round: COURTS

Answers to the facts the COURTS grades needed (`$W/areas/COURTS/gaps.md`), read 2026-10-08. Each `###` heading
answers part of one gap and names its rule. Sources: tenis4U's club panel and player web app as shipped (their
JavaScript bundles, decoded and searched on 2026-10-08), kluby.org's changelog for 2014–2026, Playtomic Manager's help
centre (read through its Zendesk API) and the English text files its web app ships (`manager.playtomic.io/locales/en/*.json`),
MATCHi's venue help centre (Zendesk API), Playmore's club and price pages and its web-app strings, PADO's Kraków
listings, and the Kraków clubs' own price lists (Fame Sport, KSOS, Atras, Miazga, Squash4You, Garden Padel). No
screenshot was taken: nothing is `[MEASURED]`. A line marked *reading* is this researcher's inference from the facts
above it, not a source.

Kinds: `[POLICY]` a rule, term, help text or interface text the operator publishes or ships; `[PRICE]`; `[DOCS]`;
`[COMPLAINT]`; `[ABSENT]` looked for and not found, with where.

## 1. Public holidays (R-COURTS-20)

### kluby.org lets a club put a holiday day into its price list

- **[POLICY]** The release of 1 June 2018 lists, under Rezerwacje, "Dodanie dnia świątecznego do cennika" (a public
  holiday added to the price list as a day of its own). [kluby.org: Co nowego 2018](https://oferta.kluby.org/changelog?rok=2018) — read 2026-10-08
- *reading:* a kluby.org club can price 11 November apart from an ordinary Wednesday; nothing says which clubs do, or at
  what price.

### Playtomic: opening hours have a holidays row, and a dated price covers a holiday

- **[POLICY]** Venue settings label the opening-hours rows "Weekdays", "Weekends" and "Holidays", with an "Open" switch
  for holidays. [Playtomic Manager strings: venue](https://manager.playtomic.io/locales/en/venue.json)
  (`venue:label.opening_hours.holidays`, `venue:opening_hours.label.holidays`) — read 2026-10-08
- **[POLICY]** A price rule's "Days" are weekdays only ("At least one day must be selected"); a holiday is priced with a
  **Timed Price**, which has a start and end date: "if … you set a timed price for a holiday from 8:30 a.m. to 6:30 p.m.,
  the app will still show normal prices" for the other slots. [Playtomic Manager strings: pricing](https://manager.playtomic.io/locales/en/pricing.json),
  [Timed Prices](https://helpmanager.playtomic.com/hc/en-gb/articles/20535348126353-Timed-Prices) (updated 2026-04-14) — read 2026-10-08

### tenis4U: opening hours are weekday and weekend only; no holiday anywhere in the club panel

- **[POLICY]** The club's settings object carries `opening`, `closing`, `opening_weekend` and `closing_weekend` (defaults
  8 and 22) and nothing for holidays; price lists (`tariff`) carry `starts_at`/`ends_at` dates. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[ABSENT]** Any holiday word in the decoded panel: "święt" matches only the province name "Świętokrzyskie";
  "holiday" nothing. Same bundle — read 2026-10-08
- *reading:* a tenis4U club that wants a holiday price would have to add a one-day dated price list; nothing shows that
  any Kraków club does.

### MATCHi's price conditions name no holiday

- **[POLICY]** A price category's conditions are "time of day, weekday, court, lead time before booking, etc."; only one
  price list is active per sport at a time. [MATCHi: Create a price list](https://matchi.zendesk.com/hc/en-gb/articles/11470485625629-Create-a-price-list) (updated 2026-09-15) — read 2026-10-08

### What Kraków clubs charge on a holiday: not published

- **[ABSENT]** A holiday price, a holiday opening rule or a "weekend and holidays" band in the price lists of Fame Sport
  (tennis, badminton, padel; split only "Pn–Pt" / "Sb–Nd"), KSOS ("Pn–Pt" / "Sb–Nd"), Atras ("Poniedziałek – Piątek" /
  "Sobota – Niedziela"), Miazga (Mon–Thu, Fri, Sat, Sun), Squash4You, Garden Padel, and the PADO and Playmore pages of
  Bajada, Padel House, Morelowa 34, SAO, Błonia Sport, Libertów and Ahoj. Searched each for "święt", "Wigili",
  "listopad". [Fame Sport cennik](https://famesport.pl/cennik/), [KSOS korty](https://obiekty.ksos.pl/korty-tenisowe/),
  [Atras cennik](https://www.atrassquash.pl/cennik/), [Miazga cennik](https://www.miazgasquash.pl/cennik/),
  [PADO Kraków](https://pado.app/poland/krakow) — read 2026-10-08
- *reading:* every Kraków list found is written in weekdays and weekends, as Rakieta's bands are; whether a desk charges
  the weekend price on 11 November is not written anywhere a player can read.

## 2. A court renamed after it is booked (R-COURTS-8)

### MATCHi: existing bookings show the new name at once

- **[POLICY]** "Every court in MATCHi Admin has a name that appears in the booking schedule, on the venue's public
  booking page, and on all bookings … The new name appears immediately in the booking schedule, on the venue's public
  page, and on any future bookings. Existing bookings also show the updated name — the change applies straight away";
  "Renaming a court doesn't affect its bookings, price list, availability". [MATCHi: How to name or rename a court](https://matchi.zendesk.com/hc/en-gb/articles/14582529054493-How-to-name-or-rename-a-court) (updated 2026-09-15) — read 2026-10-08

### tenis4U and Playtomic: not written

- **[POLICY]** tenis4U's player app prints each booking's court from the `station_name` the server sends with the
  booking; the panel renames a court ("stanowisko") by saving the whole court object. [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js),
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) (`updateStation`) — read 2026-10-08
- **[ABSENT]** Whether tenis4U's server sends the old or the new name for a booking made before a rename (the client
  cannot show it); Playtomic's "How to add/edit/delete a court" says only "Click on the court's name … update the
  details"; kluby.org's changelog has no entry on it. [Playtomic: add/edit/delete a court](https://helpmanager.playtomic.com/hc/en-gb/articles/20535305323665-How-to-add-edit-delete-a-court) (updated 2026-08-25) — read 2026-10-08

## 3. Two staff saving the same page (R-COURTS-28)

### No platform says what happens; tenis4U saves whole objects

- **[POLICY]** tenis4U's panel saves a court by sending the whole object back (`PUT /panel/station/{id}` with the object
  it holds; switching a court off, marking it flooded or turning its light on all do this), and saves the club's
  settings the same way; no version or "changed meanwhile" field is sent. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** Playtomic checks one price rule against another ("Price rule overlapping … Please solve conflicts before
  continuing"), which is about overlapping hours, not two people. [Playtomic Manager strings: pricing](https://manager.playtomic.io/locales/en/pricing.json),
  [How to add and edit prices](https://helpmanager.playtomic.com/hc/en-gb/articles/20535589805585-How-to-add-and-edit-prices) (updated 2026-10-05) — read 2026-10-08
- **[ABSENT]** A message for an edit made by someone else meanwhile, in tenis4U's panel (searched "międzyczasie", "ktoś
  inny", "inny użytkownik", "409", "If-Match"), Playtomic Manager's English strings (searched "another admin",
  "modified", "someone", "outdated", "refresh"), and kluby.org's changelog. — read 2026-10-08
- *reading:* at tenis4U the later save wins, as at Rakieta; nobody is told.

## 4. Open matches with no court, and the desk (R-COURTS-12)

### Playtomic: a match below the hold rule leaves the calendar but stays in the Matches list

- **[POLICY]** "If these time conditions are not met, the court booking will be removed, and the match will no longer
  occupy a slot in the club's calendar. However, the match will still remain visible in the list of available open
  matches"; courts stay available for "Potential private bookings from other users". [Understanding When Open Matches Occupy Club Calendar Slots](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929-Understanding-When-Open-Matches-Occupy-Club-Calendar-Slots) (updated 2026-10-01) — read 2026-10-08
- **[POLICY]** The desk sees every match in Manager's "Matches" section, filtered "by venue, match type, status, or court
  type", and can "+Add Court" to one, which "will reserve the court in your schedule, even if no players have enrolled
  yet". [How to manage Open Matches in Playtomic Manager](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353-How-to-manage-Open-Matches-in-Playtomic-Manager) (updated 2026-09-09) — read 2026-10-08
- **[POLICY]** On the Schedule a match's temporary hold is drawn as "Pending booking" (`schedule:calendar_event.match_temporal`).
  [Playtomic Manager strings: schedule](https://manager.playtomic.io/locales/en/schedule.json) — read 2026-10-08
- **[ABSENT]** A warning to the desk when it books a private reservation at an hour where a court-less open match is
  gathering. Searched the four articles above and the schedule strings ("open match", "conflict", "overlap"). — read 2026-10-08
- *reading:* a Playtomic desk can see those games, but only on a second page; the schedule it books from does not show
  them. Showing a Rakieta desk the cards a closing ends would be ahead of that.

### MATCHi: a public match is a booking, so it is on the schedule

- **[POLICY]** "A player icon appears on the booking tile in the schedule view" for a public match; "venue admins have no
  control to toggle visibility". [MATCHi: Open Matches Are Visible in the Schedule View](https://matchi.zendesk.com/hc/en-gb/articles/23495851688861-Open-Matches-Are-Visible-in-the-Schedule-View) (updated 2026-09-14) — read 2026-10-08

## 5. Blocking an hour, phone bookings and exports (R-COURTS-27)

### tenis4U: a block is a form of five fields per court, with a warning for bookings already there

- **[POLICY]** The desk opens "Dodaj blokadę" on a court and fills "Nazwa", "Początek" (date and hour), "Zakończenie"
  (date and hour), "Dzień tygodnia" ("Wybierz dzień tygodnia dla którego ustawiona zostanie blokada we wskazanym
  przedziale czasowym") and the courts to block ("Dodaj blokadę do stanowisk"); the summary reads "Ustawiasz blokadę w
  terminie: …". When the chosen hours hold bookings the form says "Zaznaczony zakres pokrywa się z zajętymi terminami.
  Wyświetl zajęte terminy (n)". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- *reading:* blocking one hour is about six inputs and a save, not one click; nothing measured how long it takes.
- **[ABSENT]** How long a Kraków desk takes to block an hour or to type in a phone booking: no video, guide or club
  account was found; tenis4U's own pages describe the panel only by its forms. — read 2026-10-08

### Playtomic: a "Blocking" is one court on one date, still in beta

- **[POLICY]** "Block a court — Mark courts as unavailable": Title, Court, Date, Start time, End time, Private notes;
  "BETA feature"; the feedback form asks whether clubs want "Option to select multiple courts" and "Ability to create
  recurring blockings". [Playtomic Manager strings: schedule](https://manager.playtomic.io/locales/en/schedule.json) — read 2026-10-08

### Exports: spreadsheets and PDF, never a calendar feed

- **[POLICY]** tenis4U's panel downloads a report as `raport … .csv` for a period of at most 60 days ("Długość okresu nie
  może przekroczyć 60 dni"), the day's calendar as a PDF (`Tenis4u-DD-MM-YYYY.pdf`), the player list as `users.csv`, and
  Tpay and Przelewy24 statements as CSV. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** kluby.org added "Eksport historii rezerwacji do Excela" (2021), "Pobranie zestawienia dziennego do
  Excela" and "Pobranie do Excela podsumowania grafiku" (2022). [kluby.org: Co nowego 2021](https://oferta.kluby.org/changelog?rok=2021),
  [2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[ABSENT]** An iCal or other calendar feed, or a bookings API, in tenis4U's panel (searched "ical", "text/calendar",
  "webcal", "eksport") or kluby.org's changelog (searched "ical", "kalendarz Google", "API"). — read 2026-10-08
- *reading:* Rakieta could read a tenis4U or kluby.org desk's bookings only from a file someone downloads by hand.

## 6. Editing a block (R-COURTS-16)

### tenis4U: a block can be added and deleted, not edited

- **[POLICY]** The panel's block calls are `POST /panel/blockade/{court}`, `GET …/byCourt/…` and `DELETE /panel/blockade/{id}`;
  there is no update call, and the court list offers "Dodaj blokadę" and "Pokaż blokady" only. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

### Playtomic: a Holiday and a Blocking can both be edited

- **[POLICY]** "How to Edit a Holiday … Click on the holiday you want to edit from the Holidays list. The window titled
  'Manage Holiday' will open. Make the necessary changes and click 'Save'"; deleting asks to "Confirm that you want to
  delete the holiday permanently". [How to add/edit/delete Holidays](https://helpmanager.playtomic.com/hc/en-gb/articles/20535276328849-How-to-add-edit-delete-Holidays) (updated 2026-03-31) — read 2026-10-08
- **[POLICY]** Strings: "Holiday successfully updated"; "When you delete holiday, you lose the holiday with all data.
  This can not be undone"; a Blocking has "Edit availability blocking", "Blocking updated" and "Delete blocking?".
  [holidays strings](https://manager.playtomic.io/locales/en/holidays.json), [schedule strings](https://manager.playtomic.io/locales/en/schedule.json) — read 2026-10-08
- **[ABSENT]** What editing a Holiday does to bookings or open matches inside it. Same sources. — read 2026-10-08

### MATCHi: a deviation cannot be edited, and deleting it undoes nothing

- **[POLICY]** "Deviations cannot be edited once they've been applied … you need to create a new, corrective
  deviation"; "deleting the incorrect deviation record afterwards does not reverse the slots it created or removed";
  "Booked slots are always protected". [MATCHi: Fix an incorrect deviation](https://matchi.zendesk.com/hc/en-gb/articles/11720008772509-Fix-an-incorrect-deviation) (updated 2026-09-15) — read 2026-10-08

### kluby.org: not written

- **[ABSENT]** Editing a block in kluby.org: the changelog has "Możliwość blokowania wszystkich wolnych połówek danego
  dnia w wybranym przedziale czasowym" (2017) and nothing on changing one. [kluby.org: Co nowego 2017](https://oferta.kluby.org/changelog?rok=2017) — read 2026-10-08

## 7. Both roofs, Bajada's indoor price, members' prices, gross or net (R-COURTS-17, R-COURTS-26)

### Two of eleven Kraków-area padel clubs have indoor and outdoor courts

- **[POLICY]** PADO's Kraków page lists Ahoj Padel (6 outdoor), Bajada (3 indoor, 2 outdoor), Garden Padel (4 outdoor),
  Padel House (4 indoor), Błonia Sport (4 indoor), Padel Arena Limanowa (3 outdoor), Fame Sport (1 indoor, 1 outdoor),
  Libertów (2 indoor), Morelowa 34 (1 indoor), Padel SPOT (2 indoor) and SAO (2 outdoor). [PADO: Padel in Krakow](https://pado.app/poland/krakow),
  [PADO: Fame Sport](https://pado.app/poland/krakow/clubs/fame-sport-club-krakow) — read 2026-10-08
- **[POLICY]** Bajada: "Trzy z nich to korty całoroczne, kryte … W cieplejszych miesiącach dochodzą dwa sezonowe korty
  deblowe na zewnątrz". [Playmore: Bajada Sports Club](https://playmore.pl/klub/bajada-sports-club/) — read 2026-10-08

### Bajada's indoor price: not published

- **[PRICE]** PADO lists only Bajada's "Double court Outdoor" at 80 / 100 / 100 PLN (weekday day, weekday evening,
  weekend). [PADO: Bajada](https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow) — read 2026-10-08
- **[ABSENT]** An indoor price: Playmore's Bajada price page carries a description and no prices; bajada.pl is a
  restaurant's site. [Playmore: Bajada cennik](https://playmore.pl/klub/bajada-sports-club/cennik/), [bajada.pl](https://bajada.pl) — read 2026-10-08
- **[PRICE]** Fame Sport, the other club with both: outdoor padel 100 zł at all hours (summer 2026); hall padel 110 / 120 zł
  (summer) and 135 / 150 / 140 zł (winter 2026/27). [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-08

### Members' prices: every platform has one, and two Kraków clubs publish one

- **[PRICE]** Fame Sport tennis has a second row, "Wstęp na kort dla zawodników" (e.g. winter weekday 14–23: 120 zł
  against 140 zł), for "zawodników KS Grzegórzecki z aktualną licencją PZT lub wykupionym karnetem na dany miesiąc".
  [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-08
- **[PRICE]** Atras (squash) prices each hour twice, "ONLINE" and "W KLUBIE" (17:00–22:00: 103,50 zł against 115 zł):
  "Rezerwując online płacisz mniej — zawsze 10% taniej, a z karnetem 15%". [Atras cennik](https://www.atrassquash.pl/cennik/) — read 2026-10-08
- **[POLICY]** tenis4U: a price variant can be tied to named players ("Kiedy żaden gracz nie jest przypisany do wariantu
  cennika, to jest on widoczny dla wszystkich użytkowników"). kluby.org: a price list can be "przypisany do klienta,
  obiektu czy klubu" (2017). MATCHi: "Standard and a default Member category" exist at every venue. Playtomic: "Set a new
  price that members of this benefit will get". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js),
  [kluby.org 2017](https://oferta.kluby.org/changelog?rok=2017), [MATCHi: Special pricing for groups or members](https://matchi.zendesk.com/hc/en-gb/articles/31150669075485-Step-by-step-Special-pricing-for-groups-or-members),
  [Playtomic pricing strings](https://manager.playtomic.io/locales/en/pricing.json) — read 2026-10-08

### Gross or net in the desk's price form: not found for tenis4U or kluby.org

- **[ABSENT]** "brutto", "netto" or a VAT field in tenis4U's club panel or in kluby.org's changelog. Every Kraków price
  list read states one amount in zł with no VAT note. — read 2026-10-08
- **[POLICY]** Playtomic's form has a "Price (before sales tax)" column with the tooltip "We'll calculate and add the
  correct tax for the player at checkout"; which countries see it is not stated. [Playtomic pricing strings](https://manager.playtomic.io/locales/en/pricing.json) — read 2026-10-08

## 8. Court time after 23:00 (R-COURTS-9)

### Two Kraków padel clubs sell until midnight, one around the clock

- **[POLICY]** Padel House: "Klub jest czynny w godzinach: Pn–Sob 07:00–24:00, Nd 09:00–24:00". [Playmore: Padel House](https://playmore.pl/klub/padel-house/) — read 2026-10-08
- **[POLICY]** As listed by PADO: Padel House 07:00–23:59 every day; SAO Sports Hub "open daily from 6 a.m. to midnight";
  Libertów 00:00–23:59 with a weekday band "00:00–16:00". Garden Padel, Bajada, Morelowa 34, Fame Sport and Błonia close
  at 23:00. [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow), [PADO: SAO](https://pado.app/poland/krakow/clubs/sao-sports-hub-krakow),
  [PADO: Libertów](https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club) — read 2026-10-08
- **[PRICE]** Squash sells the last hour too: Atras "23:00 – 24:00 najtaniej 45 zł" (Mon–Fri); Miazga "22 – 24" (Mon–Fri).
  KSOS sells tennis from 06:00 on weekdays ("60 zł Pn-Pt 6:00-14:00"). [Atras cennik](https://www.atrassquash.pl/cennik/),
  [Miazga cennik](https://www.miazgasquash.pl/cennik/), [KSOS korty](https://obiekty.ksos.pl/korty-tenisowe/) — read 2026-10-08
- *reading:* a grid that stops at 23:00 cannot carry Padel House's or SAO's last hour, or KSOS's first.

## 9. A price that does not split by the seats (R-COURTS-19)

### Nobody refuses one; Playmore splits equally

- **[POLICY]** Playmore's open game shows "Kort {price} → w {count} os. {fee}/os." and "Gra otwarta — dzielicie koszt
  kortu po równo"; its rounding is not shown. [Playmore strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[PRICE]** One Kraków price that is not whole złoty: Atras online 103,50 zł, which halves to 51,75 zł for squash's two
  players. [Atras cennik](https://www.atrassquash.pl/cennik/) — read 2026-10-08
- **[ABSENT]** A refusal of a price that does not divide by the players, in Playmore's strings, tenis4U's panel,
  Playtomic's pricing strings and MATCHi's price-list help ("Zero is a valid price"). — read 2026-10-08
