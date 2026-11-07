# The club's customers, its staff, and what players are told

Research for the club-software planning map ("Raketa becomes the club's booking software", decided
2026-10-12): areas 7 (the club's customers), 13 (staff) and 14 (telling players), feature by feature,
with the Polish law that bounds each.

**Extends** [`integration.md`](integration.md) and, in `../games-and-fill-in/`,
[`topics/competitor-club.md`](../games-and-fill-in/topics/competitor-club.md),
[`topics/platforms.md`](../games-and-fill-in/topics/platforms.md),
[`topics/local-market.md`](../games-and-fill-in/topics/local-market.md),
[`areas/EMAIL.md`](../games-and-fill-in/areas/EMAIL.md),
[`areas/NOTIFY.md`](../games-and-fill-in/areas/NOTIFY.md),
[`topics/gaps-EMAIL.md`](../games-and-fill-in/topics/gaps-EMAIL.md) and
[`topics/gaps-NOTIFY.md`](../games-and-fill-in/topics/gaps-NOTIFY.md). Facts carried from there keep
their dates; everything else was read **2026-10-12**.

**This file decides nothing.** Each feature is to be decided Build at launch · Build later · Leave out ·
Ask a real club in the club-software grilling. Build cost is estimated elsewhere.

**Sources.** Playtomic and MATCHi help pages were read through their public Zendesk API, because the
HTML answers 403. Interface text for tenis4U comes from the JavaScript its panel demo
([test-panel.tenis4u.pl](https://test-panel.tenis4u.pl/), `main.2b865c996e568707.js`) and its player
web app ([app.tenis4u.pl](https://app.tenis4u.pl/), `main.cf446af5e9523413.js`) serve to every
visitor; for Playmore, from the JavaScript its player site ([playmore.pl](https://playmore.pl/)) and its
staff panel ([manager.playmore.pl](https://manager.playmore.pl/), the "Logowanie dla recepcji" link in
Playmore's footer) serve to every visitor. Nobody signed in, booked, paid or called an endpoint; API
paths named below are strings in that code, not calls. Polish statutes were read from the ELI service
behind [isap.sejm.gov.pl](https://isap.sejm.gov.pl/); the GDPR from the EU Publications Office copy of
the Official Journal text, because EUR-Lex's HTML answered with a bot challenge.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price
· `[DOCS]` a provider's developer document · `[LAW]` a statute, regulation or a regulator's decision ·
`[COMPLAINT]` one person's account · `[ABSENT]` looked for and not found, with where. Lines marked
*reading* are not sources.

## Read this first

- **Every rival keeps customers who have no app account, and links them later in different ways.**
  MATCHi links a desk-made profile to an account by matching email and name, or by an emailed invite;
  Playmore links by the phone number, confirmed with an SMS code; tenis4U makes the desk create a full
  account (name, email, phone, unique across the platform) or type a guest's name and phone into one
  booking; Playtomic never merges: "the two are managed independently".
- **Who controls the customer data is written down at Playmore and nowhere else as fully.** Its partner
  terms carry a GDPR art. 28 processing agreement: the club is controller, Reservise the processor
  (breaches reported within 36 hours, sub-processors on 7 working days' notice, audits on 7 days'
  notice). tenis4U and kluby.org say only that booking data passes to the club, which "staje się …
  administratorem". Playtomic's public policy names only Playtomic as controller. Art. 28(3) requires a
  written contract with fixed contents; UODO fined a culture centre 2 500 zł in 2022 for entrusting
  data without one.
- **Bans diverge sharply.** Playmore lets a club block one customer from booking, with listed reasons;
  tenis4U counts a club's warnings against the person's whole account (three warnings block booking
  everywhere: "3 ostrzeżenia skutkują blokadą konta"); kluby.org shows every club how many clubs have
  blocked someone and locks the account after two. Playtomic and MATCHi have no club ban at all.
- **Sharing a debt between unrelated businesses has its own statute.** A consumer's debt may go to a
  credit-information bureau only if it is at least 200 zł, 30 days overdue, and a registered-letter
  warning went out a month earlier (art. 14 of the act on economic information). *Reading:* a shared
  "blocked at another club" flag sits outside that route.
- **Every rival gives each staff member their own login; Raketa's one shared desk login has no
  counterpart.** Roles: Playmore five (its published matrix lets reception see financial reports and
  add employees), tenis4U four (the panel hides cancel, price change and payment registration from
  reception and court staff), MATCHi six additive roles per venue, Playtomic view or edit per menu
  under one Tenant Owner.
- **Who-did-what is logged per booking at tenis4U and Playtomic, and per employee at Playmore.** No
  rival documents two-factor sign-in for club staff.
- **Playmore texts players who have no app.** Confirmations, reminders and cancellations go by SMS;
  with the app they go by push instead; door and login codes always go by SMS; a push reminder comes
  2 hours before the game. Clubs edit the templates and pick email, SMS or push for each event.
  Playtomic sends no SMS, no reminders and no bulk messages ("use … Mailchimp").
- **An SMS in Poland costs 0,10–0,17 zł net.** A sender name may have at most 11 characters, each one
  is checked by the gateway's staff, and nobody can reply to it. WhatsApp Business costs €0.0303 per
  marketing message and €0.0101 per utility message to Poland, from 1 October 2026.
- **Since 10 November 2024 one rule covers SMS, email, push and WhatsApp marketing: prior consent**
  (art. 398 Prawo komunikacji elektronicznej). The President of UKE can fine up to 3 % of revenue or
  1 000 000 zł, whichever is higher. A booking confirmation is not "informacja handlowa" (commercial
  information). UOKiK has counted asking for consent, and surveys, as direct marketing (2019, under the
  old law). Playtomic and Playmore keep a marketing-consent flag on each customer, and kluby.org sells
  "Zbieranie zgód marketingowych".
- **Kraków clubs already call themselves the controller** in their own rules (Miazga, Atras, Garden
  Padel), confirm by system SMS (Miazga), and tell a no-show of the debt the same or next day (Atras).

---

## Area 7 — the club's customers

### 7.1 A customer without an app account

**What it covers.** The desk records a person who books by phone or at the counter — a name and a
phone, sometimes an email — so the booking has someone attached, without that person installing
anything.

**Who has it.**
- **[POLICY] Playtomic:** "New Customer" with Full Name, Email, Phone, Gender, Country, Private Notes;
  "Club-only customers: added manually by your club, with a basic profile. These have no linked
  Playtomic account." A player shows as "Visitor" in a booking until they pay online or a manager adds
  them; "Marking a payment as paid … no longer creates a customer profile automatically." Minors can be
  created without an account
  ([Customers, 2026-09-18](https://helpmanager.playtomic.com/hc/en-gb/articles/20535413988113);
  [common issues, 2026-09-26](https://helpmanager.playtomic.com/hc/en-gb/articles/46345235970833)).
- **[POLICY] MATCHi:** "A customer profile is your venue's record of a person or organisation —
  separate from their MATCHi account … normal for walk-ins, bulk-imported customers"; fields run to
  address, company, VAT, up to two guardians and a national ID number; "there's no uniqueness check on
  email" ([Add customer, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11697146259613)).
- **[POLICY] tenis4U panel:** two ways. A one-booking guest: "Wyszukaj lub wpisz imię gościa" (search
  or type a guest's name) with a guest phone; the booking then shows "(gość)". Or "Tworzenie
  użytkownika" (creating a user): name, e-mail and phone all required, checked against every account on
  the platform — "E-mail już istnieje w systemie.", "Numer już istnieje w systemie." — then
  "Potwierdzenie telefonu użytkownika · Kod sms" unless the court is set to create users without
  confirmation ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] Playmore Manager:** "Nowy klient" — first name, last name, email, phone, "Adnotacja" (a
  note) and a tick box "Klient wyraził zgodę marketingową" (the client gave marketing consent)
  ([manager.playmore.pl](https://manager.playmore.pl/), `clients-CGUmLEHn.js`). Playmore sells "Jedna
  baza klientów dla wszystkich dyscyplin" (one customer base for every sport)
  ([kompleksy sportowe](https://join.playmore.pl/dla-kompleksow-sportowych/)).
- **[POLICY] kluby.org:** "Baza klientów" ([funkcje](https://oferta.kluby.org/funkcje)); "Informacja na
  grafiku o nowych klientach" (new customers flagged on the schedule, 2017); "Informacja o terminie
  stworzenia klienta" (2022) ([changelog 2017](https://oferta.kluby.org/changelog?rok=2017),
  [2022](https://oferta.kluby.org/changelog?rok=2022)).

**The desk's day with it.** *Reading:* a phone booking at 18:00 needs, at most, a name and a number
typed in under a minute. tenis4U's full-account route makes the desk wait for an SMS code read back by
the caller, unless the club switches that off.

**What a Kraków desk does today.** **[POLICY]** Miazga takes bookings "telefonicznej, internetowej lub
przez recepcję" and confirms each "wiadomość SMS wysłana z systemu"
([Miazga regulamin](https://www.miazgasquash.pl/regulamin/)). Miazga may verify a booker's details
and cancel a booking with doubtful ones (carried, `gaps-EMAIL.md` §3, 2026-10-08).

**What it means for the player app.** *Reading:* a booked game may now hold people Raketa has never
met. The player app's game, its roster and its notices have to cope with a seat held by a name and a
phone, and Raketa's identity (one account, several profiles) needs a place for a person who is only
the club's customer.

**Market signal.** Table stakes.

### 7.2 Joining a desk-made customer to an app account, and duplicates

**What it covers.** The same person later installs the app, or has two accounts, or two club records.

**Who has it.**
- **[POLICY] MATCHi:** automatic linking "if there is an existing MATCHi user with a matching email and
  name"; otherwise "Invite" emails an activation link; a person with records at several venues of a
  chain "will be linked automatically … once it's linked anywhere"
  ([Invite customer](https://matchi.zendesk.com/hc/en-gb/articles/11697240164125)). Duplicates are
  merged by the desk: the primary keeps its fields, blanks fill from the secondaries, and secondaries
  are archived; "Bookings, invoices, value cards, punch cards, and course history stay on the archived
  secondary profiles"; "There's no way to undo a merge"
  ([Merge Customer Profiles, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/28363745638685)).
- **[POLICY] Playmore (player side):** "Masz konto w klubie na ten numer? Potwierdź numer kodem SMS, a
  połączymy Twoją historię i karnety." (Have an account at the club on this number? Confirm it with an
  SMS code and we will join your history and passes.); "Rezerwujesz w klubie przez recepcję? Połącz
  konto klubu" (Booking through reception? Link the club account)
  ([playmore.pl](https://playmore.pl/), `BIIU90LQ.js`).
- **[POLICY] Playmore (staff side):** an email already on another account cannot be saved — "Najczęściej
  oznacza to, że ta sama osoba ma u nas drugie konto … zgłoś sprawę do wsparcia Playmore: konta można
  połączyć razem z rezerwacjami i karnetami" (usually the same person has a second account; report it
  to support: accounts can be joined with their bookings and passes); "Ten numer telefonu ma już inny
  klient" ([manager](https://manager.playmore.pl/), `clients-CGUmLEHn.js`).
- **[POLICY] Playtomic:** no merge. "If this person later turns out to have a Playtomic account, your
  entry won't need to match theirs — the two are managed independently"; the player's own profile
  appears beside the club's entry "only once the player accepts your club's Terms & Conditions
  (typically by completing an online payment)". Duplicates come from login methods; the fix is to
  "Delete the duplicate entry that was not manually created"
  ([common issues](https://helpmanager.playtomic.com/hc/en-gb/articles/46345235970833)).
- **[POLICY] kluby.org:** "Wyświetlenie klientów oczekujących na synchronizację" (customers awaiting
  sync, 2018); "Automatyczne powiadomienie administratora o chęci połączenia gracza z kontem na portalu"
  (the admin is told when a player asks to be joined to their portal account, 2019)
  ([2018](https://oferta.kluby.org/changelog?rok=2018), [2019](https://oferta.kluby.org/changelog?rok=2019)).
- **[POLICY] tenis4U:** no merge step; the desk-made customer is a platform account from the start
  (7.1).

**The desk's day with it.** *Reading:* the merge is either invisible (Playmore's phone code, MATCHi's
email match) or a desk chore with no undo (MATCHi merge, Playmore support ticket).

**What a Kraków desk does today.** **[ABSENT]** How a desk reconciles a paper or phone-book customer
with an app user; not in any Kraków club rule read.

**What it means for the player app.** *Reading:* the phone number becomes a joining key, so sign-up
needs a verified phone. A first booking at a club where the person was already a desk customer is the
moment to offer "this is you?", as Playmore does at checkout.

**Market signal.** Table stakes (some way to join); the phone-code join is a differentiator.

### 7.3 Notes on a customer

**What it covers.** Free text only staff see: preferences, "pays cash", "bring racket for him".

**Who has it.**
- **[POLICY] Playtomic:** "Private Notes: a free-text field visible only to your club — never to the
  player" ([Customers](https://helpmanager.playtomic.com/hc/en-gb/articles/20535413988113)).
- **[POLICY] MATCHi:** "Notes – internal notes for venue staff only; these never appear in booking
  confirmations"; and a warning: "don't put anything in there you wouldn't want a colleague at another
  venue to see either, since notes stay on the profile through archiving"
  ([Add customer](https://matchi.zendesk.com/hc/en-gb/articles/11697146259613)).
- **[POLICY] Playmore:** "Adnotacja do profilu" ([manager](https://manager.playmore.pl/)).
- **[POLICY] tenis4U:** per booking, "Wiadomość · widoczna dla użytkowników" (message, visible to users)
  apart from "Uwagi · tylko panel" (remarks, panel only) ([panel demo](https://test-panel.tenis4u.pl/));
  its privacy policy speaks of an "adnotacja do klienta" that is not passed to other clubs
  ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[ABSENT] kluby.org:** a customer note (changelog 2016–2026 and functions page).

**The desk's day with it.** *Reading:* notes are what replace the receptionist's memory between shifts.

**What a Kraków desk does today.** **[ABSENT]** Not documented anywhere public.

**What it means for the player app.** *Reading:* nothing shows; but a player's access request (7.13)
returns their notes, so a note must be writable in front of the person.

**Market signal.** Table stakes.

### 7.4 Tags, groups and per-customer rules

**What it covers.** Labels (VIP, seniors, members, league) that drive price, how far ahead someone
may book, or who may book a slot.

**Who has it.**
- **[POLICY] tenis4U:** "Indywidualne ustawienia" — named templates ("np. VIP, Karta mieszkańca,
  Seniorzy") that override, per customer, "Dni rezerwacji w przód", "Limit aktywnych rezerwacji",
  "Godziny na anulowanie", 30-minute bookings and 30-minute gaps
  ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] Playmore:** "Tagi klienta" set up under "Ustawienia → Tagi klientów"; a standing discount
  per customer, two rates (court bookings; classes, courses, league), and "Każda zmiana jest zapisywana
  w historii: kto, kiedy i z jakiej wartości na jaką" (every change is logged: who, when, from what to
  what) ([manager](https://manager.playmore.pl/)).
- **[POLICY] MATCHi:** customer groups and categories give "Special pricing", an "Extended booking
  window" and a forced category price
  ([categories](https://matchi.zendesk.com/hc/en-gb/articles/11720390524573)); requirement profiles and
  booking restrictions keep prime slots for members until, e.g., 72 hours before
  ([booking restrictions](https://matchi.zendesk.com/hc/en-gb/articles/34085754893469)).
- **[POLICY] Playtomic:** "categories" (benefits) assigned to customers, exported with expiry
  ([export](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)).
- **[POLICY] kluby.org:** "Masowe dodawanie klientów do grupy" (2020), "Zaznaczanie grup klientów w
  szybkiej aktualizacji klienta" (2022), "Skonfigurowanie wymaganych płatności pod konkretnego klienta"
  (2020) ([2020](https://oferta.kluby.org/changelog?rok=2020), [2022](https://oferta.kluby.org/changelog?rok=2022)).

**The desk's day with it.** *Reading:* the desk tags once; the price and booking window then follow the
person without anyone remembering.

**What a Kraków desk does today.** Benefit cards (MultiSport, Medicover) are the common "tag" — 15 zł off
on site (carried, `integration.md` §4, 2026-10-12).

**What it means for the player app.** *Reading:* a tag can change what a player pays and when they may
book, so a game card's price may differ per seat holder at one club.

**Market signal.** Table stakes.

### 7.5 Warnings, bans and blocks ("blokada klienta")

**What it covers.** Stopping one person from booking at the club, with or without a reason, for a
while or for good.

**Who has it.**
- **[POLICY] Playmore:** "Blokada rezerwacji … uniemożliwi użytkownikowi tworzenie nowych rezerwacji",
  to be used when "Użytkownik ma nieopłacone rezerwacje", "Naruszył regulamin korzystania z usług" or
  "Wymaga czasowego ograniczenia dostępu"; separately, an exception that lets one customer book despite
  the club's unpaid-bookings limit ([manager](https://manager.playmore.pl/)).
- **[POLICY] tenis4U:** the desk presses "Ostrzeż" on a participant of a booking (only an app account,
  not a guest); the panel answers "Ostrzeżono ({n}/3 ostrzeżeń)." or "Ostrzeżono. Użytkownik został
  zbanowany ({n} ostrzeżeń)." A list "Ostrzeżeni użytkownicy" shows the warned
  ([panel demo](https://test-panel.tenis4u.pl/)). The player sees "Ostrzeżenia użytkownika", each with
  the club's name and booking time and no reason, "3 ostrzeżenia skutkują blokadą konta." and at three
  "Konto zablokowane, ureguluj zaległości" (account blocked, settle your arrears)
  ([app.tenis4u.pl](https://app.tenis4u.pl/)).
- **[COMPLAINT] tenis4U, Google Play, 2026-01-04:** "umożliwia arbitralne zgłaszanie ostrzeżeń przez
  klub bez poinformowania użytkownika… co skutkuje zablokowaniem możliwości rezerwacji we wszystkich
  klubach" (carried, `complaints.md`, 2026-10-08).
- **[POLICY] kluby.org:** "Blokada klientów zadłużonych" (2019); the club sees "informacja o ilości
  blokad na Usługi Klubów"; kluby.org may block the account when the user "otrzyma blokadę na Usługi
  Klubów od co najmniej 2 Klubów" ([regulamin §IV Rezerwacje pt 5, §V Zablokowanie konta pt 2g](https://kluby.org/regulamin)).
- **[ABSENT] Playtomic:** a club ban. Its only block is player against player: "if someone in an Open
  Match has blocked a player, that blocked player will not be able to join"
  ([block a user (App only)](https://helpmanager.playtomic.com/hc/en-gb/articles/20535339424529)).
- **[ABSENT] MATCHi:** a per-customer ban (searched "blacklist", "prevent customer from booking",
  "no-show"); requirement profiles restrict by group or membership only
  ([requirement profiles](https://matchi.zendesk.com/hc/en-gb/articles/19511826305565)).

**The desk's day with it.** *Reading:* a ban is pressed after a no-show or an unpaid court; tenis4U makes
it one tap inside the booking, Playmore a tick box on the customer card.

**What a Kraków desk does today.** **[POLICY]** Miazga: a no-show without notice "może się wiązać z
odwołaniem wszystkich kolejnych rezerwacji i blokadą możliwości robienia rezerwacji do czasu
uregulowania należności" ([Miazga regulamin](https://www.miazgasquash.pl/regulamin/)).

**What it means for the player app.** *Reading:* a banned person may still be in a Raketa group whose
deck deals that club's games. Whether the ban reaches the deck, the yes and the booking — and whether
the player is told why — is a decision the player app cannot dodge. tenis4U's unexplained,
platform-wide ban is the complaint to avoid.

**Market signal.** Table stakes in Poland (tenis4U, Playmore, kluby.org); absent at Playtomic and
MATCHi.

### 7.6 Debts, and "blocked until paid"

**What it covers.** What a customer owes (a no-show, an unpaid court, a split share), shown to the
desk, told to the player, and used to stop new bookings.

**Who has it.**
- **[POLICY] Playmore:** a "Debtors" report (name, phone, reservations, debt; export to a spreadsheet)
  ([manager](https://manager.playmore.pl/), `reports-CsJiUhyb.js`); the player's "Rozliczenia —
  Przeglądaj i opłacaj zaległe rozliczenia" (settlements: view and pay what you owe)
  ([playmore.pl](https://playmore.pl/)); "Przypomnienie o płatności" and "Link do płatności" templates
  ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Lista zaległości"; "Powiadomienia SMS o zaległościach" (2018); a bell icon
  showing "czy dany klient został już powiadomiony o zaległości" (2018); "Sortowanie listy zaległości po
  kwocie" (2019); "Masowe wysyłanie powiadomień o zaległościach" (2022)
  ([funkcje](https://oferta.kluby.org/funkcje), [2018](https://oferta.kluby.org/changelog?rok=2018),
  [2019](https://oferta.kluby.org/changelog?rok=2019), [2022](https://oferta.kluby.org/changelog?rok=2022)).
  Split shares unpaid two hours after the game are charged to the booker's card, else "a debt is
  recorded at that club" (carried, `platforms.md`, 2026-10-06).
- **[POLICY] tenis4U:** three warnings end in "Konto zablokowane, ureguluj zaległości" (7.5).
- **[POLICY] Playtomic:** debts are Playtomic's, not the club's: a no-show in an open match is "charged
  … as a debt" the player must pay "in-app with a card in order to continue using the app" (carried,
  `NOTIFY.md` §6, 2026-10-08).
- **[ABSENT] MATCHi:** a debt or debtor list (searched "unpaid bookings").

**The desk's day with it.** *Reading:* chase by list, by SMS, and at the counter when the person next
turns up.

**What a Kraków desk does today.** **[POLICY]** Atras: "O fakcie niestawienia się na korcie i powstałej
zaległości pracownik recepcji klubu poinformuje klubowicza w danym dniu lub następnym" (reception tells
the member of the no-show and the debt that day or the next)
([Atras regulamin](https://www.atrassquash.pl/regulamin/)).

**What it means for the player app.** *Reading:* Raketa charges every seat at the yes, so its own debts
come from failed charges and late-leave fees. A club-side debt for a desk booking is new; the player app
would need somewhere to see and pay it.

**Market signal.** Table stakes in Poland.

**The law.** **[LAW]** A creditor may pass a consumer's debt to a credit-information bureau only if
"łączna kwota wymagalnych zobowiązań … wynosi co najmniej 200 złotych oraz są one wymagalne od co
najmniej 30 dni", after "co najmniej miesiąc od wysłania … listem poleconym … wezwania do zapłaty,
zawierającego ostrzeżenie o zamiarze przekazania danych do biura", and within 6 years
([ustawa o udostępnianiu informacji gospodarczych, t.j. Dz.U. 2025 poz. 85, art. 14 ust. 1](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20250000085)).
*Reading:* a club keeping its own debtor list is ordinary; telling other clubs is the bureau route's
territory.

### 7.7 No-show counts and repeat offenders

**What it covers.** A tally per customer of no-shows and late cancellations.

**Who has it.**
- **[POLICY] Playmore:** reports "No-show impact", "Repeat offenders" (per client: no-shows and late
  cancellations, a minimum-incidents filter), "No-show patterns" and "No-show benchmarking"; the
  customer's bookings show "Odwołane po czasie" (cancelled late)
  ([manager](https://manager.playmore.pl/), `reports-CsJiUhyb.js`, `clients-CGUmLEHn.js`).
- **[POLICY] tenis4U:** the warning count (7.5) is the only tally.
- **[POLICY] Playtomic:** no-shows only in open matches, reported by players to Playtomic, "Your club
  cannot submit this report" (carried, `competitor-club.md` §7, 2026-10-08).
- **[ABSENT] MATCHi, kluby.org:** a per-customer no-show count.

**The desk's day with it.** *Reading:* a count lets the desk decide a ban on a pattern, not on one bad
evening.

**What a Kraków desk does today.** **[ABSENT]** A kept count; the rules read punish each no-show
singly (7.5, 7.6).

**What it means for the player app.** *Reading:* Raketa already records attendance at the court
(#657), which a club report could count; the player's own record of it is the other side of the same
fact.

**Market signal.** Differentiator (Playmore only).

### 7.8 Booking history per customer

**What it covers.** Every booking of one person at this club, past, future and cancelled.

**Who has it.**
- **[POLICY] Playtomic:** a Booking History tab per customer with "all past, future, and canceled
  bookings" ([Booking History](https://helpmanager.playtomic.com/hc/en-gb/articles/20535184436881)).
- **[POLICY] MATCHi:** the profile shows bookings, orders, subscriptions, memberships, invoices
  ([Customers](https://matchi.zendesk.com/hc/en-gb/articles/11678704771613)).
- **[POLICY] tenis4U:** a user's reservations filtered to the court (club) in the panel
  ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] Playmore:** "Historia rezerwacji każdego gracza"
  ([squash](https://join.playmore.pl/dla-klubow-squasha/)); client card tabs: Rezerwacje, Rezerwacje
  stałe, Karnety, Portfel, Rozliczenia, Wiadomości, Dokumenty, Zgody
  ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Historia rezerwacji"; "Eksport historii rezerwacji do Excela" (2021)
  ([funkcje](https://oferta.kluby.org/funkcje), [2021](https://oferta.kluby.org/changelog?rok=2021)).

**The desk's day with it.** *Reading:* the first thing opened when a caller says "I always play
Tuesdays".

**What a Kraków desk does today.** **[ABSENT]** Not documented.

**What it means for the player app.** *Reading:* the club's history of a person includes Raketa games;
a group game booked by one yes appears in each seat holder's history at that club.

**Market signal.** Table stakes.

### 7.9 Exporting the customer list

**What it covers.** Downloading customers for a spreadsheet, an accountant, a mailing tool, or leaving.

**Who has it.**
- **[POLICY] Playtomic:** "Export List of Customers in CSV" after the admin reads and accepts terms;
  the file carries name, email, ID, "Whether the player accepted commercial communications", category,
  birthday, phone, gender and wallet balances
  ([export](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)); import requires the
  admin to "Confirm you have permission to import the customer data"
  ([import](https://helpmanager.playtomic.com/hc/en-gb/articles/20535597078417)).
- **[POLICY] MATCHi:** "export your customer list to Excel"
  ([Customers](https://matchi.zendesk.com/hc/en-gb/articles/11678704771613)).
- **[POLICY] tenis4U:** "Pobierz jako CSV" on the users list ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] Playmore:** a clients report under user reports; data moved in on arrival: "Najpierw
  sprawdzamy eksport i mapujemy klientów, cenniki oraz rezerwacje cykliczne"
  ([join.playmore.pl](https://join.playmore.pl/)); importers for Reservise and GymManager exist in the
  panel ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Backup danych" ([funkcje](https://oferta.kluby.org/funkcje)); export of
  bookings and payments to Excel ([2021](https://oferta.kluby.org/changelog?rok=2021)).

**The desk's day with it.** *Reading:* rare for the desk; decisive when a club switches software, and
Raketa is the one asking clubs to switch.

**What a Kraków desk does today.** Kraków clubs moving from Reservise had "Rezerwacje, bazę klientów,
cennik i całą historię" carried over (carried, `integration.md` §4, 2026-10-12).

**What it means for the player app.** *Reading:* an import makes thousands of desk customers at once;
the join (7.2) decides how many of them meet their Raketa account.

**Market signal.** Table stakes.

### 7.10 Consents kept on the customer

**What it covers.** Whether this person agreed to marketing, and to which club terms, with dates.

**Who has it.**
- **[POLICY] Playmore:** the desk ticks "Klient wyraził zgodę marketingową"; a "Zgody" tab lists each
  consent with version, date, required/optional and accepted/rejected; venue consents typed global,
  course, carnet or league ([manager](https://manager.playmore.pl/)). The player manages "zgody
  marketingowe dla obiektów sportowych" (marketing consents per sports venue)
  ([playmore.pl](https://playmore.pl/), `BIIU90LQ.js`).
- **[POLICY] Playtomic:** an Agreements tab with each signed waiver or T&C and its timestamp
  ([Legal Documents](https://helpmanager.playtomic.com/hc/en-gb/articles/45838498871697)); the export's
  commercial-communications flag (7.9).
- **[POLICY] kluby.org:** "Zbieranie zgód marketingowych" ([funkcje](https://oferta.kluby.org/funkcje)).
- **[POLICY] MATCHi:** customers who "opted out of club messages" are skipped by newsletters
  ([newsletter](https://matchi.zendesk.com/hc/en-gb/articles/14582472515741)).
- **[ABSENT] tenis4U:** a marketing-consent field in the panel or player app.

**The desk's day with it.** *Reading:* the desk's tick box is the only proof a phone customer agreed;
it is also the easiest thing to tick without asking.

**What a Kraków desk does today.** **[POLICY]** Garden Padel: "wysyłki informacji handlowych drogą
elektroniczną – wyłącznie w przypadku wyrażenia zgody przez Użytkownika"
([polityka prywatności](https://gardenpadel.pl/polityka-prywatnosci/)).

**What it means for the player app.** *Reading:* consent is per club; one Raketa player may say yes to
one club's newsletter and no to another's, so a single "marketing" switch is not enough.

**Market signal.** Table stakes (see 14.13 for the law).

### 7.11 Who controls the customer data, and the processing agreement

**What it covers.** Whether the club or the software decides what is done with a customer's data, and
the contract between them (umowa powierzenia przetwarzania danych).

**Who has it.**
- **[POLICY] Playmore:** its partner terms (in force 01.01.2025, last updated 15.08.2025) end with
  "Załącznik nr 1 — Powierzenie przetwarzania danych osobowych": "Administratorem, w rozumieniu RODO,
  danych osobowych Użytkowników, którzy dokonali Rezerwacji … jesteś Ty, jako Partner"; "W zakresie w
  jakim Ty nie administrujesz danymi Użytkowników, administratorem danych osobowych jest Reservise."
  Entrusted: "imię, nazwisko, numer telefonu, adres e-mail"; general consent to sub-processors with "co
  najmniej 7 (siedem) dni roboczych" notice and a right to object; delete or return at the end; audits
  on 7 days' notice; answers within 3 working days; breaches reported "nie dłużej jednak niż w terminie
  36 (trzydziestu sześciu) godzin"; "nie odpowiadamy za legalność pozyskiwanych przez Ciebie danych
  osobowych" ([Regulamin dla Partnerów](https://playmore.pl/legal/partner-terms)). Its privacy policy
  (updated 03.10.2026): sharing with a Partner makes the Partner controller, "stajemy się podmiotem
  przetwarzającym działającym w imieniu Partnera" ([polityka prywatności](https://playmore.pl/legal/privacy-policy)).
- **[POLICY] tenis4U:** "Administratorem Twoich danych osobowych … jest PC Company Sp. z o.o."; on
  booking, name, phone, payment information and email "przekazywane są klubowi i staje się on
  administratorem Twoich danych osobowych"; "Obiekty, z którymi współpracujemy przetwarzają dane według
  własnych określonych zasad"; "O dostępie pracowników w danym obiekcie decyduje manager lub jego
  właściciel"; processors named: Servizza (storage, Germany), ComVision (SMS), Cloudflare, PayPro
  ([privacy](https://tenis4u.pl/privacypolicy/)). (The panel's own arrears notice names "tennis4U Sp.
  z o. o." with its bank account — [panel demo](https://test-panel.tenis4u.pl/).)
- **[POLICY] kluby.org:** "Podczas dokonania Rezerwacji wyrażana jest na rzecz Klubu … zgoda na
  przetwarzanie Danych Osobowych … Klub staje się wówczas administratorem danych osobowych Użytkownika"
  ([regulamin §IV Rezerwacje pt 4](https://kluby.org/regulamin)).
- **[POLICY] Playtomic:** "Playtomic S.L. … will act in quality of 'Data Controller'"; data are shared
  with "the club managers related to your booking"
  ([privacy policy](https://playtomic.com/privacy-policy)). **[ABSENT]** a published club-side
  processing agreement (help centre and legal pages searched).
- **[POLICY] MATCHi:** "A customer profile is your venue's record of a person … separate from their
  MATCHi account" ([Add customer](https://matchi.zendesk.com/hc/en-gb/articles/11697146259613)).
  **[ABSENT]** a published processing agreement.
- **[POLICY] Kraków clubs name themselves controller:** Miazga for data "gromadzonych za pośrednictwem
  strony internetowej …, aplikacji Reservise (w części dotyczącej klubu Miazga Squash), rezerwacji
  telefonicznej i rezerwacji bezpośredniej w recepcji" ([Miazga](https://www.miazgasquash.pl/regulamin/));
  Atras ([regulamin](https://www.atrassquash.pl/regulamin/)); Garden Padel
  ([polityka prywatności](https://gardenpadel.pl/polityka-prywatnosci/)).

**The law.**
- **[LAW]** Controller: the body which "samodzielnie lub wspólnie z innymi ustala cele i sposoby
  przetwarzania"; processor: one which "przetwarza dane osobowe w imieniu administratora" (art. 4 pkt 7,
  8). The controller uses only processors with "wystarczające gwarancje" (art. 28 ust. 1); processing
  rests on a contract fixing subject, duration, nature, purpose, data types and categories of people,
  with the processor acting "wyłącznie na udokumentowane polecenie administratora", keeping staff
  confidential, securing data (art. 32), using sub-processors only with consent (ust. 2, 4), helping
  with data subjects' requests and art. 32–36, deleting or returning data at the end, and allowing
  audits (art. 28 ust. 3 lit. a–h); the contract must be in writing, electronic form included
  (ust. 9); a processor that sets purposes and means itself "uznaje się go za administratora" (ust. 10);
  a processor reports a breach to the controller "bez zbędnej zwłoki" (art. 33 ust. 2)
  ([RODO, EUR-Lex 32016R0679](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)).
- **[LAW] UODO, 21.09.2022:** a 2 500 zł fine on Sułkowicki Ośrodek Kultury for "powierzenie
  przetwarzania danych osobowych bez zawartej na piśmie umowy powierzenia oraz bez przeprowadzenia
  weryfikacji, czy podmiot przetwarzający zapewnia wystarczające gwarancje"
  ([UODO](https://uodo.gov.pl/pl/138/2485)).
- **[LAW]** Two or more bodies that "wspólnie ustalają cele i sposoby przetwarzania" are joint
  controllers and must set their responsibilities out (art. 26 ust. 1, [RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)).
- *Reading:* the market's pattern — club controls its customers, the software is its processor and
  separately controls its own app accounts — is Playmore's written split. Raketa's Games deck uses
  player data for Raketa's own purposes (dealing games), which art. 28 ust. 10 would make a controller's
  act, not a processor's.

**The desk's day with it.** *Reading:* invisible day to day; it surfaces when a person asks "what do you
hold on me" (7.13) or the club switches software.

**What it means for the player app.** *Reading:* the player app is Raketa's own product (Raketa
controls), while the club website's customer list is the club's (Raketa processes). One person can be
both, and the line between the two records is where the processing agreement bites.

**Market signal.** Table stakes (legally required); only Playmore publishes it.

### 7.12 What a club may record, and for how long

**What it covers.** Which fields, notes and bans a club may keep, and when they must go.

**Who has it.**
- **[POLICY] kluby.org:** data kept "do dnia upływu okresu przedawnienia roszczeń" for the service, and
  "w celach księgowych, podatkowych, rachunkowych – nie dłużej niż przez 6 lat"; marketing "nie dłużej
  niż do czasu cofnięcia … zgody" ([polityka prywatności §6](https://kluby.org/regulamin/polityka-prywatnosci)).
- **[POLICY] Playmore:** per purpose, e.g. bookings and account "Do upływu terminu przedawnienia roszczeń
  związanych z Kontem" ([polityka prywatności](https://playmore.pl/legal/privacy-policy)).
- **[POLICY] tenis4U:** only criteria: "tak długo, jak masz konto u nas lub korzystasz z naszych usług",
  legal obligations, "Czy zachowanie jest wskazane w świetle naszej sytuacji prawnej"
  ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[POLICY] Playtomic:** "10 years from the last access" for bookings and profile (carried,
  `gaps-EMAIL.md` §4, 2026-10-08).
- **[POLICY] MATCHi:** deleting keeps "the anonymised record in the database for audit purposes
  (booking history and invoice references are preserved)"
  ([Delete customer](https://matchi.zendesk.com/hc/en-gb/articles/11697234507933)).

**The law.**
- **[LAW]** Data must be "adekwatne, stosowne oraz ograniczone do tego, co niezbędne" and kept "przez
  okres nie dłuższy, niż jest to niezbędne do celów" (art. 5 ust. 1 lit. c, e,
  [RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)).
- **[LAW]** Claims lapse after six years, "a dla … roszczeń związanych z prowadzeniem działalności
  gospodarczej – trzy lata", ending "na ostatni dzień roku kalendarzowego"
  ([Kodeks cywilny, t.j. Dz.U. 2026 poz. 795, art. 118](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260000795)).
  Tax records: five years after the year (carried, `gaps-EMAIL.md` §4, 2026-10-08).
- **[ABSENT]** UODO guidance on how long a sports club may keep notes, warnings or a ban, or on
  customer blacklists in general (uodo.gov.pl searched for "czarna lista", "lista dłużników").
  *Reading:* a ban is kept as long as its purpose lasts (an unpaid debt until paid or time-barred);
  a free-text note has no such end.

**What a Kraków desk does today.** **[POLICY]** Garden Padel keeps invoices and complaint records
"przez czas … w którym przepisy prawa nakazują przechowywanie dokumentów"
([polityka prywatności](https://gardenpadel.pl/polityka-prywatnosci/)).

**What it means for the player app.** *Reading:* a ban or debt that expires has to stop affecting what
the player is dealt on the day it expires.

**Market signal.** Table stakes (legal).

### 7.13 A person's rights: access and erasure

**What it covers.** "Show me what you hold" and "delete me", asked of the club or of the software.

**Who has it.**
- **[POLICY] Playmore:** staff can tick "Usuń konto użytkownika (anonimizacja danych zgodnie z RODO)",
  "Na wyraźne żądanie użytkownika" or "W celu realizacji prawa do usunięcia danych (RODO Art. 17)";
  "Tej operacji nie można cofnąć!" ([manager](https://manager.playmore.pl/)); the player has "Eksport
  danych" in the account menu ([playmore.pl](https://playmore.pl/)).
- **[POLICY] MATCHi:** "Delete permanently removes personal details … Bookings and invoices already on
  record stay intact"; a customer with upcoming bookings cannot be deleted
  ([Delete customer](https://matchi.zendesk.com/hc/en-gb/articles/11697234507933)).
- **[POLICY] Playtomic:** deleting a customer "only removes them from your club database … Only the
  player can delete their Playtomic profile"
  ([Customers](https://helpmanager.playtomic.com/hc/en-gb/articles/20535413988113)).
- **[POLICY] tenis4U:** requests go to kontakt@tenis4u.pl; "Możemy odmówić Ci usunięcia danych
  osobowych zawartych w złożonej przez Ciebie rezerwacji do czasu jej zakończenia"
  ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[POLICY] kluby.org:** "Usuwanie konta użytkownika" (2022) ([changelog](https://oferta.kluby.org/changelog?rok=2022)).

**The law.** **[LAW]** Answer "bez zbędnej zwłoki – a w każdym razie w terminie miesiąca", extendable by
two months with notice (art. 12 ust. 3); a copy of the data (art. 15 ust. 3); erasure yields where
processing is needed "do wywiązania się z prawnego obowiązku" or "do ustalenia, dochodzenia lub obrony
roszczeń" (art. 17 ust. 3 lit. b, e); the processor helps the controller answer (art. 28 ust. 3 lit. e)
([RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)).

**The desk's day with it.** *Reading:* rare; when it comes, it has a one-month clock, and the request
may arrive at the club about data only Raketa holds, or the reverse.

**What a Kraków desk does today.** Garden Padel names a contact for the controller "pisemnie … mailem …
telefonicznie" ([polityka prywatności](https://gardenpadel.pl/polityka-prywatnosci/)).

**What it means for the player app.** *Reading:* deleting a Raketa account does not delete the clubs'
customer records (Playtomic's and MATCHi's split), and anonymising a club customer must not erase the
booking and invoice it still has to keep.

**Market signal.** Table stakes (legal); one-click anonymisation is common (Playmore, MATCHi).

### 7.14 One person, several clubs on one platform

**What it covers.** Whether club A sees what club B knows about the same person.

**Who has it.**
- **[POLICY] tenis4U:** "W każdym obiekcie posiadasz osobny profil … Nie przekazujemy informacji takich
  jak adnotacja do klienta czy historii rezerwacji w innych Klubach Tenisowych"
  ([privacy](https://tenis4u.pl/privacypolicy/)) — yet warnings count across the account and block
  every club (7.5).
- **[POLICY] kluby.org:** every club booked gets "informacja o ilości blokad na Usługi Klubów"; "Klubom,
  którym choć raz zostały udostępnione Dane Osobowe … domyślnie udostępniane są aktualne dane z Konta"
  ([regulamin §IV Rezerwacje pt 5–6](https://kluby.org/regulamin)).
- **[POLICY] Playmore:** "Ten klient nie należy do tego klubu"; "Ten pracownik pracuje też w innym
  klubie — jego adres e-mail może zmienić tylko support Playmore"; a client's email shared with another
  account cannot be changed by the desk ([manager](https://manager.playmore.pl/)).
- **[POLICY] MATCHi:** "A customer profile belongs to exactly one venue"; within a chain, local copies
  sync from a master profile ([Add customer](https://matchi.zendesk.com/hc/en-gb/articles/11697146259613)).
- **[POLICY] Playtomic:** the player's Playtomic details reach a club only after accepting its T&C
  through an online payment ([common issues](https://helpmanager.playtomic.com/hc/en-gb/articles/46345235970833));
  chains can import "organization-level customers" ([import](https://helpmanager.playtomic.com/hc/en-gb/articles/20535597078417)).

**The law.** *Reading:* each club is its own controller (7.11); passing one club's ban or debt to
another is a disclosure needing its own legal basis and notice, and debts have the bureau route (7.6).

**What it means for the player app.** *Reading:* a Raketa group plays at several clubs. A ban at club A
must not leak to club B through the deck, the roster or a shared "reliability" figure unless that
sharing is designed and told.

**Market signal.** Separation is table stakes; kluby.org's and tenis4U's cross-club penalties are rare
and drew the complaint in 7.5.

---

## Area 13 — staff

### 13.1 A login for each person

**What it covers.** Each receptionist, manager and coach signs in as themselves.

**Who has it.**
- **[POLICY] Playtomic:** "Each admin has their own login credentials" (carried, `gaps-EMAIL.md` §2,
  2026-10-08); admins are added under Settings > Club Admins with name, email, optional role and phone
  ([admin role, 2026-07-17](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049)).
- **[POLICY] MATCHi:** an administrator is "a MATCHi user account that has been granted access"; the
  email "must match an existing, verified MATCHi account"
  ([Administrators, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/11677195707677)).
- **[POLICY] Playmore:** "Dodaj nowego pracownika"; the employee gets "e-mail z linkiem do ustawienia
  hasła, ważnym 24 godziny"; the list shows "Data zatrudnienia" and "Ostatnie logowanie"
  ([manager](https://manager.playmore.pl/), `employees-DO82xKLr.js`).
- **[POLICY] tenis4U:** staff are platform users given a role ("Dodaj rolę użytkownikowi", chosen from a
  list or by user ID) ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] kluby.org:** "Możliwość zarządzania pracownikami: dodawanie, usuwanie, przydzielanie
  uprawnień" (2017) ([changelog](https://oferta.kluby.org/changelog?rok=2017)).
- **Raketa today:** one shared login per club (ticket context).

**The desk's day with it.** *Reading:* with personal logins, a leaver is removed without changing the
password for everyone, and every action has a name (13.6).

**What a Kraków desk does today.** **[ABSENT]** Whether desks share one panel login; not in any club
rule read.

**What it means for the player app.** *Reading:* Raketa already has per-person Administrators (one per
club and email) for groups, so a person may be both a player and a club's staff on one account.

**Market signal.** Table stakes.

### 13.2 Roles, and what each may do

**What it covers.** Reception versus manager versus owner: who can cancel, refund, change prices, see
money.

**Who has it.**
- **[POLICY] Playmore:** roles Administrator, Manager, Supervisor, Recepcja, "Tylko do odczytu". The
  panel's own legend (code `employees-Bwe-7zKB.js`): every role but read-only may create, edit and
  cancel bookings, view clients, edit prices, seasons, passes, tags and automations; **reception may see
  financial reports** but not activity, user or system reports; reception may add and delete employees
  but not edit them or see the employee list; only Administrator and Manager open the venue settings
  panel; read-only sees the calendar only ([manager](https://manager.playmore.pl/)).
- **[POLICY] tenis4U:** roles "Recepcja" ("Dostęp do automatyzacji, stanowisk, użytkowników kortu i
  kalendarza rezerwacji"), "Manager" ("Dostęp do automatyzacji, użytkowników kortu i kalendarza
  rezerwacji"), "Kortowi" (court maintenance: "Dostęp do listy stanowisk i kalendarza rezerwacji"),
  "Organizator Turniejów". The panel's code hides cancelling, editing a price, adding participants,
  registering a payment and charging a pass from Recepcja and Kortowi
  ([panel demo](https://test-panel.tenis4u.pl/)). Separate "Moderatorzy" are players linked to a court.
- **[POLICY] MATCHi:** additive roles: Facility admin (all, manages admins), Schedule, Customer, Invoice,
  Training planner, Attendance keeper (read-only plus attendance)
  ([Edit administrators rights](https://matchi.zendesk.com/hc/en-gb/articles/11677212906269)).
- **[POLICY] Playtomic:** per-menu "view-only or view and edit" for Schedule, Reports, Customers, Export
  Customers List, Club Payments, Billing, Settings and more; "Only the main admin user can create new
  admins" ([permissions, 2026-10-06](https://helpmanager.playtomic.com/hc/en-gb/articles/20534222446353));
  "The Tenant Owner is the only person who can access Club Admins"
  ([admin role](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049)).
- **[POLICY] kluby.org:** "Dostosowywanie i nadawanie szczegółowych uprawnień pracownikom" (2021);
  per-employee: "Wyłączenie lub ograniczenie możliwości odwoływania rezerwacji dla pracownika",
  "Spersonalizowanie liczby dni do przodu dla pracownika", "Wyłączenie dostępności do stałych rezerwacji
  dla pracowników" (2018) ([2018](https://oferta.kluby.org/changelog?rok=2018),
  [2021](https://oferta.kluby.org/changelog?rok=2021)).
- **[POLICY] Przelewy24:** a bookkeeper role with refunds, payouts and invoices (carried,
  `gaps-EMAIL.md` §2, 2026-10-08).

**The desk's day with it.** *Reading:* the split that matters is money: tenis4U keeps refunds and price
changes away from reception; Playmore does not keep financial reports away from it.

**What a Kraków desk does today.** **[ABSENT]** Not documented.

**What it means for the player app.** *Reading:* a staff member's role decides who may cancel a Raketa
game for the club and trigger its refunds; the player app shows the result, so the club-side role
should be named in what the player is told.

**Market signal.** Table stakes.

### 13.3 Who gets booking notices

**What it covers.** Which staff are emailed or texted when a booking is made or cancelled.

**Who has it.**
- **[POLICY] Playtomic:** each admin opts into emails for "Bookings created or cancelled by players,
  course enrollment cancellations" (carried, `competitor-club.md` §2, 2026-10-08).
- **[POLICY] MATCHi:** one "Cancellation notification email" and one "Booking notification email" per
  venue, "a single email address only"; admins' own bookings do not trigger it
  ([Cancellation notifications, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/24752705156637)).
- **[POLICY] tenis4U:** "Lista osób powiadamianych o rezerwacji w korcie" and an SMS number at 30 gr
  per SMS (carried, `gaps-EMAIL.md` §2, 2026-10-08).
- **[POLICY] Playmore:** "Reception e-mail notification", a reception SMS number, "Send court booking
  confirmation SMS" to a chosen employee ([manager](https://manager.playmore.pl/), `settings-LroEKw3A.js`).
- **[POLICY] kluby.org:** notices to more than one address (2018); "Powiadomienie dla pracownika o
  odwołanej rezerwacji" (2020) (carried, `gaps-EMAIL.md` §2, §9, 2026-10-08).

**The desk's day with it.** *Reading:* the desk wants cancellations at once (to resell) and new
bookings quietly.

**What a Kraków desk does today.** **[ABSENT]** Not documented (carried, `gaps-EMAIL.md` §9).

**What it means for the player app.** *Reading:* a Raketa game booked by the last yes, or a seat left,
reaches whoever the club names, not "the club".

**Market signal.** Table stakes.

### 13.4 A coach's login

**What it covers.** A coach sees their own lessons and players, without the desk's powers.

**Who has it.**
- **[POLICY] Playtomic:** "Playtomic Coach web app … separate from Playtomic Manager"; a paid add-on
  priced "on the number of coaches"; "Coaches must have admin permissions in your club"; activation
  3–5 business days ([Coach web app, 2026-09-10](https://helpmanager.playtomic.com/hc/en-gb/articles/45335085102481)).
- **[POLICY] Playmore:** a free coach app: "Za system płaci klub, nie trener"; "Wiele klubów, jeden
  login" (many clubs, one login) ([trenerzy](https://join.playmore.pl/trenerzy/)).
- **[POLICY] MATCHi:** the "Training planner" role (13.2).
- **[POLICY] kluby.org:** "Panel trenera/opiekuna"; "Trenerzy mogą bezpośrednio w trakcie zajęć
  sprawdzić listę obecności" ([funkcje](https://oferta.kluby.org/funkcje)).
- **[ABSENT] tenis4U:** a coach login; coaches are assigned to bookings ("Przypisz trenera do kortu")
  ([panel demo](https://test-panel.tenis4u.pl/)).

**What a Kraków desk does today.** **[ABSENT]** Not documented.

**What it means for the player app.** *Reading:* none until Raketa sells lessons.

**Market signal.** Differentiator.

### 13.5 An owner over several venues

**What it covers.** One person runs two clubs or a chain.

**Who has it.**
- **[POLICY] Playtomic:** switch clubs from the club name if added "to all clubs using the same email
  address" ([admin role](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049)); a
  Multi-Club dashboard by country, city and club
  ([dashboards](https://helpmanager.playtomic.com/hc/en-gb/articles/20535028898449)).
- **[POLICY] MATCHi:** "a matrix shows all venues in the group with checkboxes for each role"; "Switch
  facility" ([Administrators](https://matchi.zendesk.com/hc/en-gb/articles/11677195707677)).
- **[POLICY] Playmore:** "Dostęp do wszystkich obiektów" permission; "Wybierz swój ośrodek" at login
  ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Dodatkowe uprawnienia zarządcy" (2023) ([changelog](https://oferta.kluby.org/changelog?rok=2023)).
- **[ABSENT] tenis4U:** an owner view across courts (not in the panel text).

**What it means for the player app.** *Reading:* none directly; Raketa's Administrator is already one
per club and email, so the owner model needs one account, many clubs.

**Market signal.** Table stakes for chains; rare need in Kraków (single-site clubs).

### 13.6 An audit trail: who did what

**What it covers.** For each booking, payment or setting: who changed it, when, from what.

**Who has it.**
- **[POLICY] tenis4U:** a booking's "Zdarzenia" (events): "Utworzono rezerwację", "Przeniesiono
  rezerwację", "Anulowano rezerwację" (with its reason), "Zmiana rezerwacji", "Recepcja potwierdziła
  gotówkę", each with the actor's name and source "Aplikacja", "Panel" or "System"; role grants list
  "Utworzono" and "Utworzył" ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] Playtomic:** "The system automatically logs every action taken by the customer or club",
  showing "Who created or cancelled the reservation: the player or a club admin"; for a guest booking
  "you will not be able to … check who cancelled it"
  ([Booking History](https://helpmanager.playtomic.com/hc/en-gb/articles/20535184436881)).
- **[POLICY] Playmore:** a reception log of booking changes filtered by employee; "privileged" reports
  behind a feature switch — cancellations listed by employee and client with refunded totals, late
  changes, a pass audit; discount changes logged
  "kto, kiedy i z jakiej wartości na jaką" ([manager](https://manager.playmore.pl/), `reports-CsJiUhyb.js`).
- **[POLICY] kluby.org:** "Zapisywanie informacji o zmianach w rezerwacji" (2017)
  ([changelog](https://oferta.kluby.org/changelog?rok=2017)).
- **[ABSENT] MATCHi:** an admin action log (searched "audit log", "history of changes"); merges keep
  archived secondaries "so there's an audit trail" ([merge](https://matchi.zendesk.com/hc/en-gb/articles/28363745638685)).

**The law.** **[LAW]** Controller and processor must ensure "każda osoba fizyczna działająca z
upoważnienia … przetwarzała je wyłącznie na polecenie administratora" (art. 32 ust. 4,
[RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)). *Reading:* a shared
login makes that unprovable.

**The desk's day with it.** *Reading:* used after the fact — a disputed refund, cash short at closing.

**What it means for the player app.** *Reading:* when the club cancels a Raketa game, the player's
notice can say who at the club did it only if staff sign in as themselves.

**Market signal.** Table stakes (per booking); per-employee reports are a differentiator.

### 13.7 Acting as a customer

**What it covers.** Staff open the player's own app view to help them.

**Who has it.**
- **[POLICY] Playmore:** "Zaloguj jako klient … Otworzysz aplikację Playmore jako {name} w nowej karcie i
  będziesz działać w imieniu tego klienta"; the player site shows "Podglądasz jako {name}" with "Zakończ
  podgląd" ([manager](https://manager.playmore.pl/); [playmore.pl](https://playmore.pl/)).
- **[ABSENT]** Playtomic, MATCHi, tenis4U, kluby.org.

**Market signal.** Rare.

### 13.8 Two-factor sign-in

**What it covers.** A second factor (code, app) for staff sign-in.

**Who has it.**
- **[ABSENT] Playmore Manager:** its login offers email, password, "Zapamiętaj mnie", a reset link and a
  magic link, no second factor ([manager](https://manager.playmore.pl/), `login-BkRmUEE6.js`).
- **[ABSENT] Playtomic Manager:** no 2FA in the help centre (searched "2FA", "two-factor",
  "authenticator"); password reset links expire after an hour
  ([login issues, 2026-10-06](https://helpmanager.playtomic.com/hc/en-gb/articles/39795404368913)).
- **[POLICY] MATCHi:** its security page lists "Strong authentication – strong password policies and
  multi-factor authentication (MFA)", without saying whether venue admins use it
  ([IT Security](https://matchi.zendesk.com/hc/en-gb/articles/27511819595421)).
- **[ABSENT] tenis4U, kluby.org:** no second factor in the panel text or the changelog.

**The law.** **[LAW]** "odpowiednie środki techniczne i organizacyjne" proportionate to risk (art. 32
ust. 1, [RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)); no rule names
2FA.

**Market signal.** Rare (no rival documents it for staff).

### 13.9 A staff rota

**What it covers.** Who works which shift at the desk.

**Who has it.** **[POLICY] Playmore:** "Grafik pracy" — shifts in 15-minute steps, drafts published
with "każda osoba dostaje e-mail wyłącznie ze swoimi zmianami", leave requests approved in the panel;
"Playmore nie rejestruje wejść ani wyjść pracowników" ([grafik pracy](https://join.playmore.pl/grafik-pracy/)).
**[ABSENT]** the others.

**Market signal.** Rare.

---

## Area 14 — telling players

### 14.1 The booking confirmation

**What it covers.** The message that says "you have a court".

**Who has it.**
- **[POLICY] Playtomic:** emails a confirmation, receipt and cancellation; "E-mail notifications cannot
  be disabled" (carried, `NOTIFY.md` §1, 2026-10-08); the club writes a "Booking confirmation email
  message" per court, the email fills player, date, time, place and payment
  ([Communication, 2026-07-21](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145)).
- **[POLICY] Playmore:** "Potwierdzenia, przypomnienia i odwołania wysyłamy SMS-em. Jeśli masz
  aplikację, te same informacje dostajesz jako powiadomienie — wtedy SMS-a już nie wysyłamy."; "Otrzymuj
  potwierdzenia i przypomnienia na swój adres email" ([playmore.pl](https://playmore.pl/), `BIIU90LQ.js`).
- **[POLICY] MATCHi:** a confirmation email whose sending depends on a "notify customer" box per booking;
  access codes ride in it ([venue settings](https://matchi.zendesk.com/hc/en-gb/articles/11468129157405);
  [access codes](https://matchi.zendesk.com/hc/en-gb/articles/34085754817949)).
- **[POLICY] tenis4U:** push notices for bookings (carried, `gaps-NOTIFY.md`, 2026-10-08).
- **[POLICY] kluby.org:** "Powiadomienia SMS/MAIL" ([funkcje](https://oferta.kluby.org/funkcje)).

**What a Kraków desk does today.** **[POLICY]** Miazga: "Potwierdzeniem zrobienia rezerwacji
telefonicznej, internetowej lub przez recepcję jest wiadomość SMS wysłana z systemu"
([Miazga](https://www.miazgasquash.pl/regulamin/)).

**What it means for the player app.** *Reading:* Raketa players get the push and email it already sends;
a desk customer without the app needs SMS or email, and Raketa's "Notice" model has no non-app reader.

**Market signal.** Table stakes.

### 14.2 A reminder before the game

**What it covers.** "You play at 19:00" sent some hours ahead.

**Who has it.**
- **[POLICY] Playmore:** "Włącz powiadomienia, a 2 godziny przed grą dostaniesz przypomnienie z adresem
  klubu. Damy też znać, gdy klub zmieni coś w rezerwacji."; sample push "Za 2h grasz w {venue} o {time}."
  ([playmore.pl](https://playmore.pl/)); SMS reminders to non-app users (14.1).
- **[POLICY] tenis4U:** for a standing booking paid online, "Gracz otrzymuje 4 dni wcześniej
  powiadomienie przypominające o konieczności opłacenia najbliższego terminu"
  ([panel demo](https://test-panel.tenis4u.pl/)).
- **[POLICY] MATCHi:** a reminder email set in hours before the match, in its league tool Backhandsmash
  only ([Time settings](https://matchi.zendesk.com/hc/en-gb/articles/15579287532957)).
- **[COMPLAINT] Playtomic:** "does not send reminders for upcoming matches" (carried, `NOTIFY.md` §1).

**Market signal.** Differentiator in Poland (Playmore); absent at Playtomic.

### 14.3 A cancellation or a change

**What it covers.** The club cancels, moves or edits a booking; the player must know.

**Who has it.**
- **[POLICY] Playtomic:** "Users always receive emails and in-app notifications about any changes"
  (carried, `NOTIFY.md` §1).
- **[POLICY] MATCHi:** "The player also gets their own cancellation confirmation email"
  ([Cancellation notifications](https://matchi.zendesk.com/hc/en-gb/articles/24752705156637)).
- **[POLICY] Playmore:** "Anulowanie rezerwacji" template; "Damy też znać, gdy klub zmieni coś w
  rezerwacji"; with SMS and push both off, "o zmianach w rezerwacjach dowiesz się tylko z aplikacji albo
  maila" ([manager](https://manager.playmore.pl/); [playmore.pl](https://playmore.pl/)).
- **[POLICY] kluby.org:** class cancellations, participant and coach changes notified (2022)
  ([changelog](https://oferta.kluby.org/changelog?rok=2022)).

**What a Kraków desk does today.** Kraków rules reserve the right to cancel and say nothing on how
players are told (carried, `gaps-NOTIFY.md` R-NOTIFY-28, 2026-10-08); Miazga confirms cancellations by
system SMS ([Miazga](https://www.miazgasquash.pl/regulamin/)).

**Market signal.** Table stakes.

### 14.4 Payment link, payment reminder, debt notice

**What it covers.** "Pay for your booking here", "you still owe 60 zł".

**Who has it.**
- **[POLICY] tenis4U:** "Użytkownik otrzyma link do płatności. Rezerwacja zostanie usunięta jeśli
  płatność nie zostanie wykonana w ciągu 60 minut." (carried, `integration.md` §5, 2026-10-12).
- **[POLICY] Playmore:** templates "Link do płatności", "Przypomnienie o płatności"; a "Send link SMS"
  dialog ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Wysyłanie płatności klienta (sms/e-mail)" (2021); "Wysyłanie powiadomień o
  wystawionych fakturach oraz przypomnienia o płatnościach" (2022); debt SMS (7.6)
  ([2021](https://oferta.kluby.org/changelog?rok=2021), [2022](https://oferta.kluby.org/changelog?rok=2022)).
- **[POLICY] MATCHi:** payment links ([Working with payment links](https://matchi.zendesk.com/hc/en-gb/articles/14858820219165)).

**What it means for the player app.** *Reading:* Raketa's seat charge needs no link; a desk booking
paid later does, and that is a message to a person who may have no app.

**Market signal.** Table stakes in Poland.

### 14.5 The door or access code

**What it covers.** The code or app button that opens the court.

**Who has it.**
- **[POLICY] Playmore:** "Kody do drzwi i kody logowania przychodzą SMS-em zawsze, niezależnie od tego
  ustawienia" ([playmore.pl](https://playmore.pl/)); "Send SMS with door access instructions"
  ([manager](https://manager.playmore.pl/)).
- **[POLICY] MATCHi:** "the code is automatically included in their booking confirmation email" and in
  the app's booking view ([access codes](https://matchi.zendesk.com/hc/en-gb/articles/34085754817949)).
- **[POLICY] kluby.org:** "otwieranie drzwi na PIN"; tenis4U opens the door from the app; Playtomic's
  codes refresh 10 minutes before (carried, `gaps-EMAIL.md` §10 and `competitor-club.md` §6).

**Market signal.** Table stakes where hardware is fitted.

### 14.6 What the club may write itself

**What it covers.** The club's own text in confirmations and notices.

**Who has it.**
- **[POLICY] Playmore:** notification templates editable per message with variables and an SMS cost
  readout; a rules table turning email, SMS and push on per event
  ([manager](https://manager.playmore.pl/), `settings-LroEKw3A.js`); "Komunikaty klubu" pushes (carried,
  `gaps-NOTIFY.md` R-NOTIFY-20).
- **[POLICY] Playtomic:** confirmation message per court and an open-match message, in a language the
  club picks ([Communication](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145)).
- **[POLICY] tenis4U:** "Wiadomość widoczna dla użytkowników" per booking (up to 512 characters) and per
  court text shown after booking (carried, `gaps-NOTIFY.md` R-NOTIFY-20).

**Market signal.** Table stakes.

### 14.7 SMS as a channel

**What it covers.** Who sends SMS, for what, at what price, under what sender name.

**Who has it.**
- **[POLICY] Playmore:** SMS by default to players without the app; per-client SMS from the desk ("Maksymalnie
  można wysłać 3 SMS-y na raz", with "Koszt za część: … zł"); history of the last 30 days with statuses
  such as "Odrzucona przez operatora" and "Nie wysłano — to nie numer komórkowy"; numbers that cannot
  take an SMS flagged ("To nie wygląda na polską komórkę") ([manager](https://manager.playmore.pl/)).
  **[PRICE]** "Koszty zmienne, na przykład SMS-y do graczy, wpisujemy do oferty przed podpisaniem umowy"
  ([cennik](https://join.playmore.pl/cennik/)); its partner terms bill "opłaty za wysyłkę powiadomień
  push, e-mail, SMS" ([Regulamin dla Partnerów](https://playmore.pl/legal/partner-terms)).
- **[PRICE] kluby.org:** "wysyłka z nazwą klubu w polu nadawcy … Stawka 0,07-0,16 PLN/SMS"; or "wysyłka
  SMS z powiadomieniami z własnej karty SIM" ([integracje](https://oferta.kluby.org/integracje)); "Blokada
  wysyłania smsów na telefony stacjonarne i premium" (2021) ([changelog](https://oferta.kluby.org/changelog?rok=2021)).
- **[PRICE] tenis4U:** 30 gr per SMS to the desk (carried, `gaps-EMAIL.md` §2); its SMS processor is
  ComVision, i.e. SMSAPI ([privacy](https://tenis4u.pl/privacypolicy/)).
- **[POLICY] MATCHi:** "Send SMS" to selected customers where enabled; "you need a sender name or number
  configured before the SMS feature can be turned on"
  ([Choose action](https://matchi.zendesk.com/hc/en-gb/articles/11696109139613);
  [venue settings](https://matchi.zendesk.com/hc/en-gb/articles/11468129157405)).
- **[ABSENT] Playtomic:** SMS (help centre search "SMS": 0 results).

**Gateway prices and sender names.**
- **[PRICE] SMSAPI:** prepaid 0,17 zł (top-up 49–499,99 zł) down to 0,11 zł (over 10 000 zł) per SMS;
  postpaid shows two figures per tier, 0,16 and 0,14 zł for up to 1 000 a month, down to 0,10 and
  0,08 zł above 50 000, plus "49 PLN netto" a month; all net ([cennik](https://www.smsapi.pl/cennik)).
- **[PRICE] SMSPLANET:** "SMS PRO — SMS z polem nadawcy" 0,10 zł postpaid (1–4 999 a month, minimum 50
  zł a month), 0,12 zł prepaid; net ([cennik](https://www.smsplanet.pl/cennik)).
- **[DOCS] SMSAPI sender names:** "Ograniczenia standardu GSM pozwalają na użycie maksymalnie 11 znaków";
  adding one requires a checkbox "które potwierdza prawo nadawcy do jego wykorzystania … każde z nich
  weryfikowane jest przez konsultanta" ([zrób to sam](https://www.smsapi.pl/blog/podstawy/zrob-to-sam-konfiguracja-konta/));
  "bez polskich liter"; "nie można odpowiedzieć na wiadomość PRO" ([FAQ](https://www.smsapi.pl/blog/podstawy/bok-faq/)).
- **[LAW]** Telecoms may block SMS "zawierające treść wyczerpującą znamiona smishingu"; CSIRT NASK keeps
  a list of sender names reserved for public bodies and their look-alikes
  ([ustawa o zwalczaniu nadużyć w komunikacji elektronicznej, Dz.U. 2023 poz. 1703, art. 9–10](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20230001703)).
  *Reading:* a municipal court operator may already hold a reserved name; a private club registers its
  name only with its gateway.

**What a Kraków desk does today.** Miazga's system SMS (14.1); tenis4U clubs buy the 30 gr desk SMS.

**What it means for the player app.** *Reading:* SMS is how a club reaches the half of its customers
without an app; Raketa's player notices have no SMS today. Playmore's rule — SMS only when there is no
push — is the cost control.

**Market signal.** Table stakes in Poland (Playmore, kluby.org, tenis4U, Kraków desks); absent at
Playtomic.

### 14.8 Push and in-app messages from the club

**What it covers.** The club writing to app users, one or many.

**Who has it.**
- **[POLICY] MATCHi:** "In-app messages … appear in the player's notification center, and the player
  also receives a push"; only to customers with a linked account and a relationship with the venue;
  players can "Unsubscribe from in-app messages from a specific venue"; "In-app messages are one-way"
  ([In-app messages](https://matchi.zendesk.com/hc/en-gb/articles/33106023684381)).
- **[POLICY] Playtomic:** booking chat; "managers can send messages to all players" of a booking (carried,
  `competitor-club.md` §5); to reach a player, "the best way is the chat inside the reservation itself"
  ([How players contact your club](https://helpmanager.playtomic.com/hc/en-gb/articles/48993331219985)).
- **[POLICY] Playmore:** push from the client card ("Pushe trafiają tylko do klientów z kontem w
  aplikacji"), statuses down to "Tylko w dzwonku w apce" ([manager](https://manager.playmore.pl/)).
- **[POLICY] tenis4U:** tournament pushes, "Powiadom o rozpoczęciu turnieju" ([panel demo](https://test-panel.tenis4u.pl/)).

**What it means for the player app.** *Reading:* a club message lands in the same bell as Raketa's game
notices; per-club mute (MATCHi) keeps the bell the player's.

**Market signal.** Differentiator (MATCHi, Playmore).

### 14.9 Newsletters and announcements to all customers

**What it covers.** One message to the whole customer list or a group.

**Who has it.**
- **[POLICY] MATCHi:** email newsletter to a filtered selection; "Customers who have opted out of club
  messages will not receive the email"; sent "under your venue's identity"; no scheduling, no delivery
  report ([newsletter, 2026-09-15](https://matchi.zendesk.com/hc/en-gb/articles/14582472515741)).
- **[POLICY] kluby.org:** "Wysyłanie smsów masowo do wszystkich" (2021); "wysyłka do wszystkich klientów,
  grup klientów, uczestników turniejów" ([integracje](https://oferta.kluby.org/integracje)).
- **[POLICY] Playmore:** "Automatyzacja marketingu" permission in the role legend
  ([manager](https://manager.playmore.pl/)); club announcements by push (14.6).
- **[POLICY] Playtomic:** "Sending a single message to all members at once isn't possible … use an
  external tool like Mailchimp" ([Communication](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145)).
- **[ABSENT] tenis4U:** a mass message to customers (panel "Wiadomości" exists; its audience is not
  stated).

**What a Kraków desk does today.** **[POLICY]** Atras names its channels: website, a Facebook page and
the club phone ([Atras §3](https://www.atrassquash.pl/regulamin/)); Garden Padel runs a WhatsApp group
(carried, `local-market.md`, 2026-10-08).

**Market signal.** Differentiator (absent at Playtomic).

### 14.10 WhatsApp

**What it covers.** Messages through WhatsApp, by the club or the software.

**Who has it.**
- **[POLICY] Playmore:** a "Wyślij zaproszenie na WhatsAppie" button and club community links (carried,
  `platforms.md` §2, 2026-10-08).
- **[POLICY] Playtomic:** without commercial consent the club "shouldn't contact them directly about
  WhatsApp groups, coaching, promotions" ([export](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)).
- **[ABSENT]** Any rival sending booking notices through the WhatsApp Business Platform.

**Prices and rules.**
- **[PRICE] WhatsApp Business Platform, Poland, EUR, effective 1 October 2026:** marketing €0.0303,
  utility €0.0101, authentication €0.0101 per delivered message (EUR list rates linked from
  [pricing](https://developers.facebook.com/docs/whatsapp/pricing)); Poland got "market-specific rates"
  from 1 July 2026; "Utility templates delivered within an open customer service window are free".
- **[DOCS]** Opt-in: "Businesses must clearly state that a person is opting in to receive communication
  from the business" and "the business's name"; collectable by SMS, website, phone or paper
  ([getting opt-in](https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in)).

**What it means for the player app.** *Reading:* Raketa's groups already live in WhatsApp; a utility
message costs about 4 gr, against 10–17 gr for an SMS.

**Market signal.** Rare (as a channel for booking notices).

### 14.11 What was sent, kept per customer

**What it covers.** The desk can see which messages a customer got.

**Who has it.**
- **[POLICY] Playmore:** "Historia wiadomości (ostatnie 30 dni)" with type, recipient, content, status
  ([manager](https://manager.playmore.pl/)).
- **[POLICY] kluby.org:** "Podgląd wysłanych powiadomień w historii klienta o rezerwacjach" (2022);
  "Statystyki wysłanych wiadomości GSM" ([changelog](https://oferta.kluby.org/changelog?rok=2022)).
- **[POLICY] MATCHi:** "There's no per-send delivery report available"
  ([newsletter](https://matchi.zendesk.com/hc/en-gb/articles/14582472515741)).

**What it means for the player app.** *Reading:* "I was never told" is the commonest complaint; a sent
log is the desk's answer (carried, `NOTIFY.md` §1).

**Market signal.** Differentiator.

### 14.12 The law: marketing needs consent, service messages do not

**What it covers.** Which messages need prior consent in Poland, and who enforces it.

- **[LAW] Prawo komunikacji elektronicznej, art. 398 (in force 10.11.2024):** "Zakazane jest używanie:
  1) automatycznych systemów wywołujących, 2) telekomunikacyjnych urządzeń końcowych, w szczególności w
  ramach korzystania z usług komunikacji interpersonalnej — do celów przesyłania informacji handlowej …,
  w tym marketingu bezpośredniego, do abonenta lub użytkownika końcowego, chyba że uprzednio wyraził on
  na to zgodę" (ust. 1); consent may be given by providing an electronic address "w celu przesyłania
  informacji handlowej" (ust. 2); not at the recipient's cost (ust. 3); a breach is an act of unfair
  competition (ust. 4)
  ([Dz.U. 2024 poz. 1221](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240001221)).
  *Reading:* SMS, email, push and WhatsApp all reach a terminal device, so one rule covers them.
- **[LAW] Fine:** for failing to obtain the consent "o której mowa w art. 398", the President of UKE
  imposes "karę pieniężną w wysokości do 3% przychodu … lub do 1 000 000 zł, przy czym zastosowanie ma
  kwota wyższa" (art. 446 ust. 5,
  [PKE](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240001221)).
- **[LAW] The old e-mail rule is gone:** art. 10 of the act on electronic services is "(uchylony)" by
  art. 26 pkt 3 of the PKE introductory act
  ([UŚUDE, t.j. Dz.U. 2024 poz. 1513](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240001513)).
  The 2026 amendment of that act (Dz.U. 2026 poz. 1296, in force 06.11.2026) implements the Digital
  Services Act and touches PKE only to add a DSA task (art. 419)
  ([Dz.U. 2026 poz. 1296](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260001296)).
- **[LAW] What is commercial information:** "każdą informację przeznaczoną bezpośrednio lub pośrednio
  do promowania towarów, usług lub wizerunku przedsiębiorcy … z wyłączeniem informacji umożliwiającej
  porozumiewanie się za pomocą środków komunikacji elektronicznej z określoną osobą oraz informacji o
  towarach i usługach niesłużącej osiągnięciu efektu handlowego" (UŚUDE art. 2 pkt 2,
  [Dz.U. 2024 poz. 1513](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240001513)).
  *Reading:* a confirmation, reminder, cancellation, payment link or door code serves the booking, not a
  sale, and rests on the contract (GDPR art. 6 ust. 1 lit. b); "free courts tonight, 20 % off" is
  commercial information.
- **[LAW] UOKiK, decision RWR 5/2019 of 26.07.2019** (under the predecessor, art. 172 Prawa
  telekomunikacyjnego): direct marketing includes contact made "w celu uzyskania zgody na marketing
  bezpośredni", to study "jego potrzeb lub oczekiwań", "informowanie o akcjach promocyjnych" and "zapowiedzi
  oferty" ([decision](https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/0/E754C1CD05AAC77CC12584FC002224F5/$file/ZIK%20CMSE%20wersja%20bip.pdf)).
- **[LAW] UOKiK's other tool:** "uciążliwe i niewywołane działaniem albo zaniechaniem konsumenta
  nakłanianie do nabycia produktów przez telefon, faks, pocztę elektroniczną lub inne środki
  porozumiewania się na odległość" is an aggressive practice "w każdych okolicznościach"
  ([ustawa o przeciwdziałaniu nieuczciwym praktykom rynkowym, t.j. Dz.U. 2023 poz. 845, art. 9 pkt 3](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20230000845)).
- **[LAW] GDPR:** a person may object to direct marketing "w dowolnym momencie", after which the data
  "nie wolno już przetwarzać do takich celów" (art. 21 ust. 2–3); direct marketing may be a legitimate
  interest (recital 47) — for the data, not for the channel, which PKE governs
  ([RODO](https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32016R0679)).
- **How rivals draw the line.** **[POLICY]** Playtomic: "Contact is only allowed for essential service
  matters related to an existing booking or activity … For promotional or marketing communication,
  player consent is required first" ([export](https://helpmanager.playtomic.com/hc/en-gb/articles/20535213209489)).
  Playmore puts satisfaction surveys under "kontakt zgodnie z art. 398 Prawa komunikacji elektronicznej"
  ([polityka prywatności](https://playmore.pl/legal/privacy-policy)). kluby.org's terms take, at
  booking, consent to contact "w celach niezbędnych do realizacji Usługi Klubu"
  ([regulamin §IV Rezerwacje pt 9](https://kluby.org/regulamin)). Partners must "nie rozpowszechniać
  niezamówionej informacji handlowej" ([Playmore partner terms](https://playmore.pl/legal/partner-terms)).

**What a Kraków desk does today.** Garden Padel sends commercial information "wyłącznie w przypadku
wyrażenia zgody" ([polityka prywatności](https://gardenpadel.pl/polityka-prywatnosci/)); Miazga cites
"marketing usług własnych" as a legitimate interest ([Miazga](https://www.miazgasquash.pl/regulamin/)).

**What it means for the player app.** *Reading:* Raketa's game notices (a game booked, a seat left, a
payment to confirm) are service messages; "Fill in alerts" and "Challenges for you" that invite a
player to a new purchase sit near the line UOKiK drew, and a club's "come play" blast to Raketa players
needs that club's consent per player.

**Market signal.** Table stakes (legal).

---

## Rivals × features

`yes` documented · `no` documented as absent or impossible · `—` not found · Kraków desk = the status
quo in club rules read.

| Feature | Playtomic | MATCHi | tenis4U | Playmore | kluby.org | Kraków desk |
| --- | --- | --- | --- | --- | --- | --- |
| 7.1 Customer without app account | yes | yes | yes (guest, or desk-made account) | yes | yes | phone and desk bookings |
| 7.2 Join to app account | no (kept apart) | yes (email+name, invite, merge) | n/a (account from start) | yes (phone + SMS code; support merges) | yes (sync request) | — |
| 7.3 Private notes | yes | yes | yes (per booking) | yes | — | — |
| 7.4 Tags / per-customer rules | yes (categories) | yes (groups, profiles) | yes (setting templates) | yes (tags, discounts) | yes (groups) | benefit cards |
| 7.5 Club ban | no | no | yes (3 warnings, account-wide) | yes (per club, with reasons) | yes (block count shared) | yes (until paid) |
| 7.6 Debts list | no (Playtomic's own debts) | — | yes (blocks until paid) | yes (Debtors report) | yes (arrears list, SMS) | yes |
| 7.7 No-show counts | open matches only | — | warnings only | yes (repeat offenders) | — | — |
| 7.8 History per customer | yes | yes | yes | yes | yes | — |
| 7.9 Export list | yes (CSV) | yes (Excel) | yes (CSV) | yes (reports) | yes (Excel, backup) | — |
| 7.10 Consents on the customer | yes | opt-out flag | — | yes (versions, per club) | yes | consent clause |
| 7.11 Published processing agreement | — | — | — | yes (art. 28 annex) | — | controller named |
| 7.13 Erasure tool | club record only | yes (anonymise) | by email | yes (anonymise, RODO art. 17) | yes | — |
| 13.1 Login per person | yes | yes | yes | yes | yes | — |
| 13.2 Roles | per-menu view/edit | 6 additive | 4 | 5 + matrix | per-permission | — |
| 13.3 Staff booking notices | per admin | one address | list + SMS | email + SMS | several addresses | — |
| 13.4 Coach login | yes (paid add-on) | yes (role) | — | yes (free app) | yes (panel) | — |
| 13.5 Multi-venue owner | yes | yes | — | yes | yes | — |
| 13.6 Audit trail | per booking | — | per booking, with actor | per employee | booking changes | — |
| 13.8 Staff 2FA | — | "MFA" (scope unclear) | — | no | — | — |
| 14.1 Confirmation | email | email | push | SMS or push, email | SMS / email | system SMS |
| 14.2 Reminder | no | leagues only | payment reminder | yes (2 h push) | — | — |
| 14.4 Payment link / reminder | — | yes | yes | yes | yes | — |
| 14.6 Club's own words | yes | — | yes | yes (templates) | — | — |
| 14.7 SMS | no | yes (sender name) | desk only, 30 gr | yes | yes, 0,07–0,16 zł | yes |
| 14.8 Push / in-app from club | chat | yes (per-venue opt-out) | tournaments | yes | — | — |
| 14.9 Bulk to all customers | no ("Mailchimp") | email newsletter | — | push announcements | mass SMS | Facebook, WhatsApp |
| 14.11 Sent log per customer | — | no | — | yes (30 days) | yes | — |

## Gaps

- **Club contracts.** Playtomic's, MATCHi's, tenis4U's and kluby.org's processing agreements with clubs
  are not public; only Playmore's is.
- **UODO on bans and notes.** No UODO decision or guide on customer blacklists, shared bans or how long
  a sports club may keep notes and warnings (uodo.gov.pl searched); the GDPR principles are the only
  rule found.
- **tenis4U's warnings.** Whether a club can see warnings given by other clubs, what "cancel" of a
  warning does, and how a ban is lifted; the code lists the endpoints, the help text does not exist.
- **Playmore's Polish settings text.** The panel's notification-rules event list, guard mode, SMS price
  per part and marketing-automation screens load their Polish text from somewhere not in the bundles
  read; only English identifiers were seen. Playmore's SMS price to clubs is "wpisujemy do oferty".
- **MATCHi** SMS prices and sender rules, and whether venue admins use MFA.
- **Kraków desks.** How a desk keeps its customer list today (paper, Excel, the system), whether it
  writes notes or bans, whether staff share one login, and whether it texts or WhatsApps players itself
  — none of it in club rules or reviews read; needs asking a desk.
- **The anti-abuse act** was read in its 2023 text (Dz.U. 2023 poz. 1703); its consolidated text (Dz.U.
  2024 poz. 1803) was not compared.
- **UKE guidance** on art. 398 (what counts as a service message) was not found on uke.gov.pl; the
  UOKiK decision cited is under the predecessor provision.
- **WhatsApp** service-message pricing for Poland: the rate card lists a "Service" column at the utility
  rate while the pricing page says service conversations are free; not reconciled.
