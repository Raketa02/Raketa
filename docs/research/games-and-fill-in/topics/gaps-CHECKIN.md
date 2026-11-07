# Gaps round: CHECKIN

Answers to the facts the CHECKIN grades needed (`$W/areas/CHECKIN/gaps.md`), read 2026-10-08. Each `###` heading
answers part of one gap and names its rule. Sources: tenis4U's club panel and player web app as shipped (their
JavaScript bundles, decoded and searched on 2026-10-08), Playmore's web app bundles and its page for clubs, kluby.org's
changelog for 2016–2026, MultiSport's app FAQ (the answers ship inside the page), MultiSport Slovakia's FAQ, Medicover
Sport's user rules and a Medicover Sport user guide, Benefit Systems' conditions for partner facilities, Stripe's dispute
docs, PayU's and Tpay's merchant documents, CourtReserve's help, Padel Mates' web strings and store listing, and the
Kraków clubs' own terms (Miazga, Squash4You, Atras, Garden Padel, Fame Sport, KSOS). No screenshot was taken: nothing is
`[MEASURED]`. A line marked *reading* is this researcher's inference from the facts above it, not a source.

Kinds: `[POLICY]` a rule, term, help text or interface text the operator publishes or ships; `[PRICE]`; `[LAW]`;
`[DOCS]` a provider's or regulator's documents; `[COMPLAINT]`; `[ABSENT]` looked for and not found, with where.

## 1. How a Kraków desk marks who of a booked group has arrived (R-CHECKIN-31)

### tenis4U's desk marks each player's payment, never an arrival

- **[POLICY]** The club panel lists every player who joined a booking and asks the desk to settle each one: "Dołączeni
  gracze bez wpłaty — rozlicz ich przyciskiem „Oznacz płatność”"; "Czy chcesz oznaczyć, że opłacono w klubie?";
  "Recepcja oznaczy płatność przy kasie"; on success "Płatność oznaczona". A per-player pay window counts benefit
  cards ("Karty pokrywają całość — użyj „Oznacz płatność”", "Gotówka do pobrania:", "Obciąż karnet"). The desk's badge
  counts open cash shares and "karty Medicover czekają na weryfikację"; a note field suggests "np. zapłacili przy
  wejściu". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[ABSENT]** Any arrival, attendance or check-in mark in the same panel: searched the decoded bundle for "obecn",
  "nieobecn", "stawi", "przyby", "przyszed", "check-in", "zameld" — the only "obecn" hits are "Obecny miesiąc" and "Korty już
  obecne w bazie". — read 2026-10-08
- *reading:* at a tenis4U desk all four players of a shared booking have a row, but the row records money (paid online,
  paid in the club, cards counted), not whether the person came.

### kluby.org settles a booking when it is paid; no arrival mark in its changelog

- **[POLICY]** Changelog entries for the desk's schedule: "Informacje o rezerwacji na grafiku" and "Rozliczenie rezerwacji
  automatycznie przy płatności" (2020); "Szybka edycja, usuwanie, drukowanie płatności" (2021); "Podsumowanie płatności
  w zestawieniu dziennym", "Podgląd z kamer na grafiku rezerwacji" (2022). [Co nowego 2020](https://oferta.kluby.org/changelog?rok=2020),
  [2021](https://oferta.kluby.org/changelog?rok=2021), [2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[ABSENT]** An attendance, arrival, check-in, QR or scanner entry in the changelogs 2016–2023 (2014, 2015 and
  2024–2026 pages list nothing): searched "obecn", "przyby", "stawien", "check", "QR", "skaner", "czytnik". — read 2026-10-08

### Playmore ticks attendance only at coached classes

- **[POLICY]** For a coach: "Dotknij osoby, żeby zaznaczyć obecność. Dotknij drugi raz — zaznaczysz nieobecność.",
  "Obecność {checked}/{total}", "Cofnij obecność". [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read
  2026-10-08. The page for clubs: "Trener … odhacza obecność na zajęciach. Ty widzisz frekwencję". [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08
- **[ABSENT]** An arrival mark for a court booking in Playmore's web app (searched the 1,157 shipped bundles for
  "check-in", "zameld", "obecność" outside classes). The booking's QR is for a self-checkout stand (section 3). — read 2026-10-08

### Kraków clubs' own rules: report to the desk and pay on entry

- **[POLICY]** Miazga Squash (Playmore/Reservise): "Klubowicze proszeni są o zgłoszenie się do Recepcji Klubu
  każdorazowo po wejściu i przed opuszczeniem Klubu"; "Podstawą do przebywania w klubie i korzystania z kortów jest
  opłacenie rezerwacji po wejściu do obiektu"; card holders show "ważnej, podpisanej karty wraz z dowodem tożsamości,
  przed skorzystaniem z gry". [Miazga regulamin §2](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Squash4You: "Podstawą do korzystania z kortów jest opłacenie rezerwacji przed wejściem na kort."
  [Squash4You regulamin, rezerwacja pt 3](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[POLICY]** Atras: "O fakcie niestawienia się na korcie i powstałej zaległości pracownik recepcji klubu poinformuje
  klubowicza w danym dniu lub następnym." [Atras regulamin §6](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** A Kraków club rule for a paper list, or for checking each player of a booking rather than the booker:
  searched the terms of Garden Padel, Fame Sport, KSOS, Miazga, Squash4You, Atras and SAO. — read 2026-10-08
- *reading:* today a Kraków desk knows a booking was used when someone pays or reports at the counter; the record is per
  booking and per payer, and a player who paid online and walks to the court leaves no trace.

## 2. What a check-in and a result are worth in a card dispute (R-CHECKIN-32)

### Stripe: for a reserved offline service, show it was received, and when

- **[DOCS]** "Offline services include purchases that are made in advance, such as event tickets and reservations, where
  evidence of a cancellation policy can be material." For *Product not received*, offline service, Stripe recommends:
  "Evidence proving that the cardholder disputing the transaction received the service" (`uncategorized_text`,
  `uncategorized_file`); "Documentation showing that the service was provided to the cardholder, including the date that
  the cardholder received or began receiving the purchased service in a clear, human-readable format" (`service_date`,
  `service_documentation`); "Evidence that the service was signed for … Cardholder signature … A copy of identification
  presented by the cardholder" (`customer_signature`); the customer's messages (`customer_communication`).
  [Stripe: Dispute categories](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[DOCS]** For *Product unacceptable*, offline service: how the service was described before purchase
  (`product_description`), the refund policy and how it was shown (`refund_policy`, `refund_policy_disclosure`), and
  "If the service was only partially used, whether the dispute amount exceeds the value of the unused portion".
  [same](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[DOCS]** Activity logs with "IP addresses, corresponding timestamps" (`access_activity_log`) are listed for digital
  services and fraud, not for offline services. [same](https://docs.stripe.com/disputes/categories) — read 2026-10-08
- **[ABSENT]** A Stripe document that names a check-in, attendance or a match result as evidence, or says how much a
  bank weighs it (searched the categories page and the evidence fields of the dispute API). — read 2026-10-08
- *reading:* a check-in of the disputing player with its time, shown as a readable record, is the "received the service,
  with the date" Stripe asks for; a check-in of the other three, or a result the players typed, proves less about this
  cardholder.

### Polish acquirers ask for proof the service was carried out

- **[DOCS]** PayU's merchant guide, for "Niedostarczenie towaru lub niezrealizowanie usługi": "Potwierdzenie odbioru
  towaru przez klienta … lub potwierdzenie realizacji usługi", "Kopia informacji zawierającej opis towaru/usługi oraz
  termin…", and whether the cardholder contacted the merchant first; without documents "w wyznaczonym terminie" the
  amount goes back to the consumer. [PayU: Chargeback](https://poland.payu.com/wp-content/uploads/sites/14/2020/03/Chargeback_pl_0.pdf) — read 2026-10-08
- **[DOCS]** Tpay's card terms bind the merchant to "przekazywać kopie dokumentów potwierdzających realizację
  zobowiązania dotyczącego danej Płatności" and to keep "dokumenty potwierdzające, że spełnił świadczenie … przez co
  najmniej 3 lata". [Tpay: Załącznik nr 3 do OWU §4](https://tpay.com/user/assets/files_for_download/zalacznik-nr-3-do-owu-dodatkowe-warunki-obslugi-platnosci-kartami-platniczymi.pdf) — read 2026-10-08
- **[DOCS]** A Przelewy24 transfer has no chargeback, and BLIK disputes run through BLIK's own claims process —
  `topics/local-market.md#przelewy24-at-stripe`, `topics/local-market.md#blik-at-stripe` (read 2026-10-06).

### What a tenis4U club holds today

- **[POLICY]** The desk sees an online share as "Zapłacono online ({payment_operation_number})", others as "Zapłacono"
  or "Nie zapłacono", and a booking's "historia zdarzeń". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- *reading:* a club selling through tenis4U (Przelewy24 or Tpay) can show the bank the operation number, its terms and
  its own event log; it holds no record that a player arrived, only that a share was paid.

## 3. What Kraków counters scan codes and cards with (R-CHECKIN-35)

### MultiSport: a terminal at the desk, and a token typed on its keypad when the scanner fails

- **[POLICY]** "The device that scans QR codes generated by the MultiSport app in the sports facility is out of order.
  How do I register my entry?" — "Give the token number shown under the QR code to the person at the reception desk in
  the sports facility. They will enter the token manually using the terminal keyboard." [MultiSport: mobile app FAQ](https://www.kartamultisport.pl/en/about/support/mobile-app) — read 2026-10-08
- **[POLICY]** Benefit Systems' conditions for a partner facility: "RECEPCJA — Stała recepcja z obsługą — Możliwość
  montażu terminala do kart MultiSport". [Warunki współpracy dla Partnerów](https://corp.benefitsystems.pl/fileadmin/benefitsystems/dokumenty/Warunki-wspolpracy-dla-Partnerow.pdf) — read 2026-10-08

### Medicover Sport: staff scan, a self-service reader, or an SMS code checked on the club's phone

- **[POLICY]** The rules: an entry is registered by SMS, "systemu mobilnego (kod QR skanowany przez pracownika
  Obiektu)", or the plastic card; for SMS, Medicover sends the code "na telefon komórkowy Użytkownika oraz na telefon
  komórkowy wskazany przez Partnera", and the club "ma prawo dokonać porównania kodów". [Medicover Sport: Regulamin
  użytkowników od 1.06.2025 §9, §12](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-08
- **[POLICY]** A Medicover Sport user guide: "Pokaż na recepcji QR kod, by pracownik obiektu mógł go zeskanować lub
  zeskanuj go samodzielnie poprzez czytnik QR kodów." [Przewodnik użytkownika goFIT FITmore, p. 10](https://usz.edu.pl/wp-content/uploads/Przewodnik_Użytkownika_platforma_benefitowa_goFIT_FITmore.pdf) — read 2026-10-08

### Playmore: cards are "odbite" at the entrance, the booking QR goes to a self-checkout stand

- **[POLICY]** "Gracz podaje przy rezerwacji, ile osób wchodzi z kartą Multisport albo FitProfit. Kartę odbija się przy
  wejściu, a zestawienia generują się w panelu raportów, bez spisywania numerów na recepcji." [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08
- **[POLICY]** The booking shows "Kod QR rezerwacji" (Polish, no description); the German and Ukrainian texts add "Falls
  die Anlage Self-Checkout unterstützt, scanne diesen Code am Kiosk". [Playmore strings PL](https://playmore.pl/assets/CccZ1mLc.js),
  [DE/UA](https://playmore.pl/assets/DtrPGQHI.js) — read 2026-10-08

### Fame Sport: a QR reader at a Kraków desk, for its own app

- **[POLICY]** For loyalty points the player must "wyświetlić kod QR, który należy zbliżyć do czytnika. Po prawidłowym
  zeskanowaniu kodu QR punkty zostaną naliczone automatycznie". [Fame Sport: regulamin aplikacji §10](https://famesport.pl/regulamin/) — read 2026-10-08

### The device itself was not found

- **[ABSENT]** The make or kind of reader on any Kraków counter (a handheld scanner that types into a field, a webcam,
  a tablet's camera), and whether tenis4U's or Playmore's desk accepts a scanner's typed input: searched both desk
  bundles for "skan", "czytnik", "scanner", the clubs' terms, and Benefit Systems' partner pages; PerfectGym's
  "Medicover Sport Access Control Integration" article answered 403. — read 2026-10-08
- **[POLICY]** Outside Poland, CourtReserve's check-in "Kiosks can be accessed on tablets, desktop computers, or other
  web-enabled devices using a unique URL"; a club may let players type "their player number instead of using a barcode
  scanner" — "If not checked, all players must use the barcode scanner to check in." [CourtReserve: Self check-in kiosk](https://help.courtreserve.com/en/articles/4993563-self-check-in-kiosk) — read 2026-10-08
- *reading:* "terminal", "czytnik" and "zbliżyć do czytnika" all describe a device at the counter, separate from the
  desk computer's screen; a MultiSport token typed on the terminal's own keypad shows a fallback that is typed, not
  scanned.

## 4. Playmore's self-checkout answer, and apps that tell a player they were checked in (R-CHECKIN-8)

### Playmore notifies the player when the desk scans a declared card

- **[POLICY]** A card declared on a prepaid booking is charged as a deposit, returned "zaraz po odbiciu karty w
  recepcji"; on a pass: "Kaucja za karty odbite w recepcji wróci na karnet dzień po odbiciu karty w klubie. Przy każdym
  odbiciu wyślemy Ci powiadomienie."; the booking then reads "Odbito {count} kart partnerskich" or "Odbito {scanned} z
  {declared} kart". [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[ABSENT]** What Playmore's self-checkout stand shows when a booking QR is scanned: the stand's screens are not in the
  player web app, and the page for clubs does not describe it (searched "self-checkout", "kiosk", "stanowisk"). — read 2026-10-08

### tenis4U shows the player that their Medicover cards were registered

- **[POLICY]** "Aktywacja karty Medicover jest możliwa w 30-minutowym oknie czasowym tj. 15 min przed rozpoczęciem
  rezerwacji do 15 min od rozpoczęcia rezerwacji"; results "Karty Medicover zostały zarejestrowane", "Medicover
  zweryfikowany", "Nie udało się zweryfikować kart Medicover". [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08

### Card operators confirm a registered visit to the phone

- **[POLICY]** Medicover Sport confirms an SMS entry with a code sent back to the user's phone (and the club's).
  [Medicover Sport rules §12](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-08
- **[POLICY]** MultiSport: "You will be sent a request for rating 1.5 hours after the visit registered via the MultiSport
  application", by push. [MultiSport: mobile app FAQ](https://www.kartamultisport.pl/en/about/support/mobile-app) — read 2026-10-08
- **[POLICY]** CourtReserve (US racket-club software): "The kiosk screen displays a success message upon check-in"; with
  an upcoming reservation the player sees its details. [CourtReserve: Player self check-in](https://help.courtreserve.com/en/articles/5575693-player-self-check-in) — read 2026-10-08
- **[ABSENT]** A racket app that changes the player's own booking to "checked in" after a desk scan of the booking itself
  (searched Playmore, tenis4U, Padel Mates, CourtReserve). — read 2026-10-08

## 5. Undoing an arrival or an entry (R-CHECKIN-23)

### MultiSport: a new code at the desk within 20 minutes

- **[POLICY]** "In order to cancel a visit … you need to generate another QR code or token and provide it to the person
  at the reception desk … asking them to cancel your visit. You need to scan the QR code or token within 20 minutes after
  it is generated in the facility where your visit has been registered." [MultiSport: mobile app FAQ](https://www.kartamultisport.pl/en/about/support/mobile-app) — read 2026-10-08

### Medicover Sport: 10 minutes alone, then an hour through support

- **[POLICY]** A wrong entry must be cancelled "w ciągu 10 minut od jego rejestracji" by SMS "anuluje" or the app's QR;
  after that only through customer service, before the service ends and within 1 hour. [Medicover Sport rules §13](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-08

### Booking systems: classes can be undone, payments can be deleted, nothing marks arrival

- **[POLICY]** Playmore: "Cofnij obecność"; "Nie można edytować obecności po upływie 6 godzin od zakończenia zajęć"
  (classes only). [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** kluby.org: "Szybka edycja, usuwanie, drukowanie płatności" (2021), "Usuwanie pojedynczych płatności z
  płatności zbiorczej" (2022). [Co nowego 2021](https://oferta.kluby.org/changelog?rok=2021), [2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[ABSENT]** An undo for tenis4U's "Oznacz płatność" (searched the panel for "Cofnij", "Odznacz", "Usuń płatność",
  "unmark"); the panel offers "Anulować rezerwację ze zwrotem?" / "BEZ zwrotu?" for a whole booking. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

## 6. Whether an entry code rotates, expires, resists a screenshot or shows a photo (R-CHECKIN-24)

### MultiSport puts the holder's photo behind the code

- **[POLICY]** The holder uploads a photo; at a first visit they "Generate your special QR code or token number. Present
  the QR code for scanning together with your ID card"; after that "you will be able to register your visits without the
  need to show your ID card". The photo can change "no more than once every 30 days". [MultiSport: mobile app FAQ](https://www.kartamultisport.pl/en/about/support/mobile-app) — read 2026-10-08
- **[POLICY]** MultiSport Slovakia: "A QR code will be generated (its validity is limited to 10s)"; an "Offline code"
  under it is read out if the scan fails; the virtual card carries a photo. [MultiSport SK: virtual card FAQ](https://multi-sport.sk/en/faq/faq_category/virtual-card/) — read 2026-10-08
- **[ABSENT]** The validity of the Polish app's QR (the Polish FAQ says only "generate"). — read 2026-10-08

### Medicover Sport refuses copies of identity and checks codes on two phones

- **[POLICY]** Use is "wyłącznie osobiście"; a valid ID excludes "kopii, wydruków, skanów, zdjęć lub innych graficznych
  potwierdzeń"; with an SMS entry the club compares the code sent to both phones. [Medicover Sport rules §9, §10, §12](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-08
- **[ABSENT]** Whether Medicover's app QR expires or changes. — read 2026-10-08

### A Kraków club bans screenshots of its app's codes

- **[POLICY]** Fame Sport: "Organizator nie wyraża zgody na posługiwanie się identyfikatorami w formie papierowej
  (wydruki) lub w formie statycznych lub animowanych grafik (obrazków) wyświetlanych poza Aplikacją"; a reward's QR "jest
  jednorazowy. W razie zamknięcia okna z kodem QR na nagrodę, wygasa on". [Fame Sport: regulamin aplikacji §10](https://famesport.pl/regulamin/) — read 2026-10-08

### tenis4U's door code is personal, permanent and opens only around the game

- **[POLICY]** "Twój stały kod, ten sam we wszystkich klubach. Działa tuż przed grą i w jej trakcie."; when live: "Wpisz
  na klawiaturze przy drzwiach. Gdyby nie zadziałał, użyj przycisku „Otwórz drzwi”." The code is withheld while a
  share waits for cash or Medicover cards wait for verification (comments in the shipped code: "Blokuj automatyzację
  gdy płatność "w klubie" nie potwierdzona", "Ukryj automatyzację gdy karty Medicover nie zostały zweryfikowane"). [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08

## 7. A booked player with no phone or no signal (R-CHECKIN-25)

### Card operators keep a plastic card, and desks find a booking by name

- **[POLICY]** MultiSport's app QR works offline ("even if you don't have access to the internet"); the plastic card is
  still accepted — [MultiSport: mobile app FAQ](https://www.kartamultisport.pl/en/about/support/mobile-app) (read
  2026-10-08), `topics/local-market.md#how-the-operators-say-a-card-is-used`.
- **[POLICY]** Medicover Sport takes the plastic card as well as SMS and QR. [Medicover Sport rules §12](https://medicoversport.pl/assets/documents/terms/REGULAMIN_UZYTKOWNIKOW_DLA_UMOW_ZAWARTYCH_OD_01_06_2025.pdf) — read 2026-10-08
- **[POLICY]** At a tenis4U desk the clerk settles a joined player by name ("Oznacz płatność"), with no code. [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** Miazga: a booking is confirmed by SMS or in the app; "Brak potwierdzenia rezerwacji może oznaczać, że nie
  została ona zrobiona. W takim wypadku prosimy o kontakt z recepcją." [Miazga regulamin §3](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
### No Kraków rule for a booked player without a phone

- **[ABSENT]** A Kraków club or platform rule for a booked player who arrives with no phone or no signal (searched the
  terms of Garden Padel, Fame Sport, KSOS, Miazga, Squash4You, Atras, SAO, and tenis4U's and Playmore's desk strings). — read 2026-10-08
- *reading:* every desk read works by name and payment, so a player without a phone is served by the clerk finding the
  booking; only card operators need a code, and both keep a plastic card.

## 8. Padel Mates' "Offline check-in at the court" (R-CHECKIN-7)

### Padel Mates lists offline check-in as an app feature and never explains it

- **[POLICY]** The phrase is one bullet of the player app's list "Your court. In your pocket.": "Apple Pay & Google Pay",
  "Offline check-in at the court", "Personalised court recommendations", "Apple Watch support for bookings" (Swedish:
  "Offline-incheckning på banan"). Elsewhere: "Check in via the app and focus on the game"; for clubs "Seamless
  payments, memberships and check-in". [Padel Mates strings EN](https://padelmates.se/locales/en/translation.json),
  [SV](https://padelmates.se/locales/sv/translation.json) — read 2026-10-08
- **[ABSENT]** Any explanation of what the check-in is or how it works offline: not in the App Store listing (SE), the web
  strings, or a web search; Google Play's page did not load. — read 2026-10-08
- *reading:* placed among app features, it most likely means a check-in the app can do without signal; that is not stated.

## 9. How a desk sees a booking already paid online (R-CHECKIN-34)

### Kraków desk systems show an online payment, tenis4U with its operation number

- **[POLICY]** tenis4U's player app shows "Zapłacono online", "Opłacono karnetem", "Zapłacono", "Do zapłaty" or
  "Płatność w klubie" [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js); the desk sees
  "Zapłacono online ({payment_operation_number})" or "Nie zapłacono", and door automation "Działa tylko dla opłaconych
  rezerwacji (w tym zweryfikowane karty Medicover/Multisport)" [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** kluby.org: "Rozliczenie rezerwacji automatycznie przy płatności". [Co nowego 2020](https://oferta.kluby.org/changelog?rok=2020) — read 2026-10-08
- **[POLICY]** Playmore: "Opłacona rezerwacja otwiera drzwi i uruchamia kort" [Playmore dla klubów](https://join.playmore.pl/);
  a payer is told "Rezerwacja została już opłacona", "Ta część została już opłacona". Prepaid card discounts warn
  "bez odbicia kart recepcja policzy pełną cenę". [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
### No Kraków complaint of paying twice was found

- **[ABSENT]** A Kraków complaint of being asked at the desk to pay again for a court already paid online (web search in
  Polish; the complaints found are Playtomic's and Playmore's, in `topics/complaints.md#a-share-paid-at-the-desk-is-not-recorded-and-the-organiser-is-billed-again`
  and `#paid-but-the-court-was-not-there-double-booked-wrong-venue-nobody-on-site`). — read 2026-10-08

## 10. Benefit cards on a court prepaid online (R-CHECKIN-30)

### The card is declared online and scanned at the desk, and the discount waits for the scan

- **[POLICY]** Playmore, since August 2026: the discount for a declared card is paid as a deposit, returned to the wallet
  "zaraz po odbiciu karty w recepcji"; "Zniżka za kartę sportową (MultiSport, Medicover Sport i podobne) należy się tylko
  wtedy, gdy recepcja odbije kartę przy wizycie. Klub dostaje pieniądze od operatora karty tylko za odbite wejście";
  "Wcześniej część klubów dawała zniżkę od razu i traciła pieniądze, gdy karty potem nie odbito. Od sierpnia 2026
  wszystkie kluby rozliczają karty tak samo"; "Kartę partnerską można zadeklarować tylko przed rozpoczęciem gry"; at some
  clubs "Przy płatności online w tym klubie zniżka za karty partnerskie nie wraca — także po ich odbiciu w recepcji".
  [Playmore strings](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08
- **[POLICY]** tenis4U: the booking carries a number of MultiSport and Medicover cards; "Kartę Multisport należy pokazać
  przed rezerwacją. Jednej karty można użyć tylko raz dziennie na tenisa, a kolejne użycia będą odrzucane"; "Dla kart
  sportowych minimalny czas rezerwacji wynosi 60 minut"; Medicover cards are activated in the app 15 minutes either side
  of the start. [tenis4U web app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08
- **[PRICE]** Fame Sport: "Rabat z kart partnerskich (Multisport Plus, Medicover Sport, MyBenefit) naliczany jest od ceny
  regularnej i nie łączy się z innymi rabatami." [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-08
- **[POLICY]** KSOS: 15 zł off per card by coupon code ("karta2x" for two); "Karty partnerskie należy okazać pracownikowi
  recepcji przed rozpoczęciem gry." [KSOS: korty tenisowe](https://obiekty.ksos.pl/korty-tenisowe/) — read 2026-10-08
- **[ABSENT]** A Kraków club's rule for a card on a court booked and prepaid through another platform (Playtomic, PADO, a
  player app): searched the terms above. — read 2026-10-08

### How many Kraków padel players use a card

- **[ABSENT]** A count of MultiSport or Medicover holders playing padel in Kraków, or nationally: Benefit Systems publishes
  card totals and says padel visits nearly tripled (`topics/local-market.md#how-many-cards`), nothing per city or sport
  (searched its press office and investor news). — read 2026-10-08

## 11. Late arrival at Kraków clubs (R-CHECKIN-21)

### KSOS lets the court go if nobody is there 10 minutes before; others count lateness in the hour

- **[POLICY]** KSOS (Kraków, tennis): "Administrator obiektu uprawniony jest do wynajęcia kortów tenisowych innej osobie,
  jeśli użytkownik, który dokonał rezerwacji, nie stawił się na korcie tenisowym na 10 minut przed zarezerwowaną
  godziną oraz nie powiadomił o możliwym spóźnieniu." [KSOS: regulamin rezerwacji](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/),
  [odkryte korty §2](https://obiekty.ksos.pl/regulamin-odkrytych-kortow-tenisowych-krakowskiego-szkolnego-osrodka-sportowego/) — read 2026-10-08
- **[POLICY]** Squash4You: the hour is "60 minut, liczone od pełnej godziny zegarowej"; play may run over "max do 10 min
  tylko i wyłącznie w przypadku wolnego kortu". [Squash4You regulamin](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[POLICY]** Garden Padel: "Czas wynajmu kortu obejmuje przygotowanie kortu, grę, sprzątanie piłek". [Garden Padel regulamin §4](https://gardenpadel.pl/regulamin/) — read 2026-10-08
### Playmore's late notice goes to the other players, not the club's record

- **[POLICY]** Playmore lets a court player warn the others: "Spóźnię się" (~{minutes} min) — "Damy znać pozostałym graczom
  z tej rezerwacji, żeby nie czekali pod kortem"; "To tylko informacja: kort zostaje zarezerwowany, a płatność się nie
  zmienia." For classes the coach sees it "przy Twoim nazwisku na liście obecności". [Playmore strings](https://playmore.pl/assets/C2ReOno3.js) — read 2026-10-08
### No Kraków padel club records a late arrival

- **[ABSENT]** A Kraków padel club that records a late arrival, or gives the court away after some minutes (searched
  Garden Padel, Fame Sport, SAO; Padel House, Morelowa 34 and Bajada publish no terms found). — read 2026-10-08
