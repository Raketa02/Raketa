# Gaps round: POSTGRID

Answers to the facts the POSTGRID grades needed (`$W/areas/POSTGRID/gaps.md`), read 2026-10-08. Each `###` heading
answers one gap and names its rule. The provisional grades come first (R-POSTGRID-3, -10, -19, -43).

Sources:
- Playmore's web app as shipped on 2026-10-08. That is its string bundles and the code that uses them: 1,368 script
  files reachable from `https://playmore.pl/` through `index-C8d-0CWt.js`. It also includes the public venue API the app
  reads (`https://zephyr.playmore.pl/api:4Tf8JTHd/venue/{id}`). Bundle names are content hashes, so they change when
  Playmore deploys.
- Playtomic's two help centres: 94 player and 157 club articles in en-gb, plus 99 and 152 in es, pulled through the
  Zendesk API on 2026-10-08.
- MATCHi's two help centres, pulled the same way.
- Padel Mates' web strings.
- tenis4U's web app (`app.tenis4u.pl`, version 3.6.1) and the club API it reads.
- kluby.org's club pages.
- Two App Store listings.
- The Polish Language Act as consolidated in Dz.U. 2024 poz. 1556 and Dz.U. 2026 poz. 81.

A line marked *reading* is this researcher's inference from the facts above it, not a source.

Kinds: `[POLICY]` a rule, wording or behaviour the operator publishes or ships; `[LAW]`; `[MEASURED]` seen by using the
product (here, by requesting its pages); `[COMPLAINT]`; `[ABSENT]` looked for and not found, with where.

## 1. A half-made game when its maker leaves the screen (R-POSTGRID-3)

### Playmore's open-game creator starts from scratch each time it opens

- **[POLICY]** The creator is a three-step sheet on the club's open-games page: "Krok {step}/{total}", with the steps
  "Termin i kort", "Partnerzy i poziom" and "Ogłoszenie". [Playmore pl strings](https://playmore.pl/assets/Ct1XsxUt.js)
  (`reservations.openGames.creator.stepLabel`, `.steps`). Read 2026-10-08.
- **[POLICY]** Opening the sheet resets it. The code sets the step to 1. It clears the description, tags, the chosen
  template and the level, and clears any error. Then it re-initialises the slot picker, which clears the chosen date,
  hour, court and price and reloads the first page of free slots. It fills anything in only when the opening carries a
  `prefill`. Closing the sheet without submitting is logged as `abandoned`, and the creator code saves none of the
  sheet's content (it touches no browser storage). The sport chosen in the club's picker may stay selected on the page.
  [Playmore creator code](https://playmore.pl/assets/DM7ksFDa.js) (the creator shell's `openShell`, `resetStepContent`
  and `close`; the picker's `init` → `reload` → `clearSelection`). Read 2026-10-08.
- **[POLICY]** Two things carry over, and both come from games already created, not from a sheet left half-done:
  - "Twoje ostatnie opisy". These are descriptions saved to the account after a game is created; the code calls
    `rememberDescription` only after a successful create. [strings](https://playmore.pl/assets/Ct1XsxUt.js)
    (`creator.description.ideas.recentLabel`), [code](https://playmore.pl/assets/DM7ksFDa.js). Read 2026-10-08.
  - The chip "Załóż jak ostatnio". It loads "Ustawienia z ostatniej gry wczytane — wybierz termin." Its flag note says it
    fills in "sport, czas gry, liczba partnerów, opis, tagi, poziom — bez terminu" from "ostatnią grą gracza w klubie".
    A rematch opens the creator "z terminem i ustawieniami oryginału". [strings](https://playmore.pl/assets/Ct1XsxUt.js),
    [Playmore flag registry](https://playmore.pl/assets/p_SkNwim.js) (`open-game-recreate`, added 2026-09-26;
    `open-game-rematch`, added 2026-09-28). Read 2026-10-08.
- *reading:* Playmore keeps no draft. Leaving part-way loses the sport, slot, partners, level and text. The nearest
  thing to a draft is a one-tap copy of the last game the player actually created.

### Playtomic: no draft of a half-made match is described

- **[ABSENT]** No help article mentions a draft, a saved half-made match or resuming creation. Searched all 94 player
  and 157 club en-gb articles (and the es sets) for "draft", "saved … match/booking", "resume", "continue". Read
  2026-10-08. The creation flow is described only as a sequence of choices. [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match-Padel-Tennis)
  (updated 2026-10-03).

## 2. A player's own "whom I play with", and a player with no gender (R-POSTGRID-10)

### Playtomic sets gender on the match, never as the joiner's own preference

- **[POLICY]** "There are four options available for an open match: All Players … Only Women … Only Men … Mixed". "The
  gender of a match is determined by the first player who registers for an open match". "if a user attempts to join a
  match with a gender restriction that does not align with their own gender, they will be unable to participate."
  [Gender of the match in Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831467158801-Gender-of-the-match-in-Open-Matches)
  (updated 2026-03-05). Read 2026-10-08.
- **[POLICY]** Gender is optional on the profile: "You don't need to fill everything out—just add what you're
  comfortable sharing … Gender". [How to create your account in Playtomic](https://playerhelp.playtomic.com/hc/en-gb/articles/19831938095633-How-to-create-your-account-in-Playtomic)
  (updated 2026-10-02). Read 2026-10-08.
- **[POLICY]** The only player-side gender setting is a search filter for tournaments and leagues. It is "Gender
  Preference: Select Male, Female, or Open", with "Tournaments I Can Play … to see only tournaments that match your
  gender and level". [How to join a Tournament](https://playerhelp.playtomic.com/hc/en-gb/articles/19831745721617-How-to-join-a-Tournament)
  (updated 2026-10-07). Read 2026-10-08.
- **[ABSENT]** What Playtomic does when a player with no gender joins or opens an Only Women, Only Men or Mixed match.
  Searched all player and club help articles (en-gb, es) for "gender", "prefer not", "not specified", "your gender".
  Read 2026-10-08.

### Padel Mates keeps a player who is neither male nor female out of single-gender matches

- **[POLICY]** "You cannot add this player to the open match because it is restricted to male participants only." The
  same string exists for female, and both appear beside the male/female pairs ("You cannot add a female player…").
  The same rule applies to tournaments and coaching. [Padel Mates web strings](https://padelmates.se/locales/en/translation.json)
  (`maleCannotAddOther`, `femaleCannotAddOther`). Read 2026-10-08.

### Playmore has no gender on open games or seekers

- **[ABSENT]** Playmore asks for gender only when a child is added to a course ("Płeć", "Chłopiec", "Dziewczynka").
  Open games, "Szukam grania" and its creator have no gender field. Searched every current bundle for
  `gender`/"płeć"/"kobiet"/"mężczy"/"mikst". [course child strings](https://playmore.pl/assets/DdhO7KuR.js). Read
  2026-10-08.

### Small padel apps offer gender as a filter on games, not as a two-way preference

- **[POLICY]** AUN we play: "Browse matches near you, filter by level, side, gender", and "Filter by gender — open
  matches or strict criteria, you pick". [App Store](https://apps.apple.com/us/app/aun-we-play/id6768347960). Read
  2026-10-08.
- **[POLICY]** Padeligo: "Use advanced filters such as location, level, dominant hand, gender, or play style."
  [App Store](https://apps.apple.com/us/app/padeligo-padel-community/id6475889008). Read 2026-10-08.
- **[ABSENT]** No app was found where a player's own preference ("I play only with women", "not in mixed") also keeps
  her out of the games others count or deal. Every rule found is either set on the game by its creator (Playtomic,
  Padel Mates, MATCHi) or a search filter (Playtomic tournaments, AUN, Padeligo). Searched the help centres above, the
  Playmore and Padel Mates string bundles, and App Store listings. Read 2026-10-08.

## 3. Grading an hour by fitting players free together, and whether they fit each other (R-POSTGRID-19, R-POSTGRID-17)

### Playmore's creator counts matching seekers for the one slot picked, and says they will be told

- **[POLICY]** Once a court and hour are picked, the creator asks the server how many "Szukam grania" seekers match. It
  sends the start, end, court, level tier and band, and player count (`GET /open-games/seek-pool` → `matching`). It
  shows the count on the description step: "nikt jeszcze nie czeka na taką grę | {count} pasująca osoba dostanie
  powiadomienie o Twojej grze | {count} pasujące osoby dostaną powiadomienie o Twojej grze". The count is recomputed
  when the level or the number of partners changes. [API client](https://playmore.pl/assets/DYS4n-xJ.js)
  (`openGames.seekPool`), [creator code](https://playmore.pl/assets/DM7ksFDa.js) (`seekBoost`),
  [Szukam grania strings](https://playmore.pl/assets/5BE1o4M2.js) (`boost.matching`). Read 2026-10-08.
- **[POLICY]** Seekers declare their usual hours, a format ("Singiel / Debel / Bez znaczenia") and openness to new
  partners. They are matched "poziomem i godzinami"; "Dopasowujemy osoby o poziomie zbliżonym do Twojego."
  [Szukam grania strings](https://playmore.pl/assets/5BE1o4M2.js) (`card.subtitle`, `wizard.who`). Read 2026-10-08.
- *reading:* the count belongs to one slot after it is chosen, not to every hour of the grid. Each seeker is matched to
  the game's level band and hour. Nothing in the strings or the request checks whether the seekers suit each other.

### Playmore's singles ladder shows, hour by hour, who in your range can play, with the court checked

- **[POLICY]** "Kiedy zagrać": "Godziny osób z Twojego zasięgu i tych, które Cię wyzwały — z od razu sprawdzonym kortem."
  It shows seven days with "Kto może grać: {day}" and, per hour, "{time} — mogą grać: {names}", with "Wolny kort" or
  "Brak wolnego kortu". When nobody fits, it says "W tym tygodniu nikt nie pasuje". A card reads "W tym tygodniu mogą
  z Tobą zagrać — {n} osoby z Twojego zasięgu mają wolne godziny". [Challenger strings](https://playmore.pl/assets/CPLsdYdo.js)
  (`rangeCalendar`, `challengeTimes.entryCard`). [Flag registry](https://playmore.pl/assets/p_SkNwim.js)
  (`league-range-calendar`, added 2026-10-01: "członek singla widzi tydzień z awatarami osób ze swojego zasięgu …
  godziny, w których mogą grać, ze stanem kortu"). Read 2026-10-08.
- **[POLICY]** A challenge can propose 1–3 hours "które pasują wam obu", taken from the next 7 days with the court's
  state. [strings](https://playmore.pl/assets/CPLsdYdo.js) (`challengeTimes.picker.hint`);
  [flag registry](https://playmore.pl/assets/p_SkNwim.js) (`league-challenge-times`, added 2026-10-03). Read 2026-10-08.
- *reading:* in a one-against-one ladder, "free together with you" and "fits you" are the whole question. For a game
  of four, no app was found that grades an hour by players free together who also fit each other.
- **[ABSENT]** Any app that checks whether the free players suit one another, not only the organiser, before calling
  an hour a full game. Searched Playmore's open-game, seeker and league strings and code; Playtomic's and MATCHi's help
  centres; Padel Mates' strings. Read 2026-10-08. Playtomic shows nobody's free hours; see `../../games-and-fill-in-market.md#s05-g-8--published-weekly-availability-a-groups-shared-free-hours`.

## 4. The free-slot list after a clash (R-POSTGRID-43)

### Playmore sends the creator back to step 1 and re-reads the free slots

- **[POLICY]** A create refused with any of these codes shows the refusal, returns the creator to step 1 and reloads
  the picker: `OPEN_GAME_SLOT_TAKEN` ("Ktoś właśnie zajął ten termin. Wybierz inny slot."),
  `OPEN_GAME_PRICE_UNAVAILABLE`, `OPEN_GAME_TOO_SOON`, `OPEN_GAME_TOO_FAR_AHEAD` or `OPEN_GAME_OFF_PEAK_ONLY`. The
  reload clears the chosen date, hour, court and price and fetches availability again with `force`. Other refusals
  stay on the current step with their message. [creator helpers](https://playmore.pl/assets/RktoVfyX.js) (the list
  `["OPEN_GAME_SLOT_TAKEN","OPEN_GAME_PRICE_UNAVAILABLE","OPEN_GAME_TOO_SOON","OPEN_GAME_TOO_FAR_AHEAD","OPEN_GAME_OFF_PEAK_ONLY"]`),
  [creator code](https://playmore.pl/assets/DM7ksFDa.js) (`handleSubmitError`: on those codes `step=1` and
  `picker.reload()`), [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`creator.errors.slotTaken`). Read 2026-10-08.
- **[POLICY]** Moving an open game to another slot does the same: a `OPEN_GAME_SLOT_TAKEN` refusal refreshes the
  picker. [reschedule code](https://playmore.pl/assets/DnlhJjRi.js). Read 2026-10-08.

### Playtomic: no clash message or refresh is described

- **[ABSENT]** No help article describes what a player sees when the slot she picked was taken a moment before, or
  whether the list reloads. Searched player and club articles for "taken", "already booked", "not available",
  "someone else". Read 2026-10-08.

## 5. A price that changes between the preview and the button (R-POSTGRID-41)

### Playmore's create request carries no price; the organiser then pays on a checkout that refuses a stale total

- **[POLICY]** The button reads "Utwórz i zapłać wpisowe ({fee} {currency})". The fee comes from the court price
  shown when the court was picked ("Cena kortu: {price} {currency}"), read from the court's availability price list.
  The create request sends only the court, start, end, description, tags and level, with no price.
  [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`creator.submit`, `creator.slot.price`),
  [creator helpers](https://playmore.pl/assets/RktoVfyX.js) (the request builder and `loadPrice`),
  [API client](https://playmore.pl/assets/DYS4n-xJ.js) (`openGames.create` → `POST /open-games`). Read 2026-10-08.
- **[POLICY]** Creating opens a checkout for the new game. It shows "Twoja część", "{date}, {time} · {court}" and "Po
  opłaceniu gra pojawi się w klubie i powiadomimy szukających grania." The payment carries the total the checkout
  shows (`total_price`). The server's "amount shown" or "price not matched" refusal becomes "Cena tego terminu się
  zmieniła. Odśwież i sprawdź nową cenę." [creator code](https://playmore.pl/assets/DM7ksFDa.js) (after create,
  the class checkout opens with `source: "creator"`), [checkout code](https://playmore.pl/assets/DPJjiND7.js)
  (`ClassesOpenGameSummary`, `total_price`), [error map](https://playmore.pl/assets/Cng0yjU9.js)
  (`"amount shown"`/`"price not matched"` → `reservations.common.errors.priceChanged`),
  [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`creator.pay`, `common.errors.priceChanged`). Read 2026-10-08.
- *reading:* nothing compares the button's fee with the price at creation. But nobody is charged at the creator's
  button. The organiser pays on the next screen, and a total that no longer matches is refused there with a message,
  before any money moves.

## 6. A free-cancel window that has already closed when the game is made (R-POSTGRID-45)

### Playmore's creator states the leaving rule in general terms, whatever the time to the start

- **[POLICY]** The creator's rules box always lists these lines, whatever the time to the start: "Gra dochodzi do
  skutku tylko w komplecie ({count} graczy).", "Brak kompletu na {hours} h 10 min przed startem → automatycznie
  odwołujemy grę i kort…" and "Do {hours} h przed startem wypiszesz się ze zwrotem wpisowego; później wpisowe przepada
  (anulacja nie na czas)." The hours come from the club's open-game settings, by default 2 and 12. Nothing in the box
  compares them with the chosen start. [checkout/rules code](https://playmore.pl/assets/DPJjiND7.js)
  (`OpenGameRulesBox`), [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`creator.rules`). Read 2026-10-08.
- **[POLICY]** A slot less than 24 h away gets "Mało czasu" and "Do gry zostało mniej niż 24 h. Tak blisko skład
  zbiera się rzadko — zaproś znajomych od razu po opłaceniu albo wybierz późniejszy termin." That line is about
  filling the game, not about leaving it. A slot too close to fill is refused: "Wybrany termin jest zbyt blisko startu
  - gra nie zdążyłaby się skompletować." [strings](https://playmore.pl/assets/Ct1XsxUt.js)
  (`creator.slot.shortLeadHint`, `creator.errors.tooSoon`). Read 2026-10-08.
- **[POLICY]** Elsewhere Playmore does say that the window has closed:
  - At the court checkout: "Termin bezpłatnego odwołania minął — start za {h} h lub mniej" and "Rezerwacja bez
    bezpłatnego odwołania — termin już minął". [court checkout code](https://playmore.pl/assets/TULASMQx.js),
    [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`reservations.checkout.clean.policy`).
  - When a player leaves an open game: "Termin bezpłatnego odwołania minął — wpisowe za Twoje miejsce wróci tylko
    wtedy, gdy gra się nie odbędzie." [strings](https://playmore.pl/assets/Ct1XsxUt.js).

  Read 2026-10-08.
- **[ABSENT]** The shortest lead at which Playmore accepts a new open game. The "too soon" refusal names no hours, and
  no minimum was found in the creator code or the flag registry. Read 2026-10-08.
- *reading:* Playmore warns a court booker that her window has already closed, but its open-game creator does not.
  "Mało czasu" shows that slots under 24 hours can be picked. If one inside the leaving window is accepted (12 hours
  by default), the creator still shows the same general sentence. The organiser then learns the window has passed
  only when she tries to leave.

## 7. How far ahead a game can be made in Kraków (R-POSTGRID-15)

### tenis4U: most Kraków padel clubs take bookings 14 days ahead; two take 30, one 7

- **[POLICY]** tenis4U shows each club's horizon on its information panel as "{n} dni w przód możliwych do
  rezerwacji", or "dowolna ilość dni możliwa do rezerwacji w przód" when it is 0. The number is the club's
  `reservation_days_ahead`. [tenis4U web app](https://app.tenis4u.pl/main.cf446af5e9523413.js). Read 2026-10-08.
- **[POLICY]** Values for the Kraków clubs listed with padel, read from the API the app uses (`https://api.tenis4u.pl/court/{id}`):

  | Club | Days ahead | Free cancel (h) |
  |---|---|---|
  | Padel House | 14 | 24 |
  | Garden Padel | 14 | 24 |
  | Bajada Padel Club | 14 | 24 |
  | PADEL LOUNGE | 14 | 24 |
  | SAO Sports Hub Piastowska | 14 | 24 |
  | Libertów Padel Club | 14 | 24 |
  | Tennis Zakrzów Center | 14 | 24 |
  | Fame Sport Club | 30 | 24 |
  | Squash&Padel (Skawina) | 30 | 24 |
  | Padel SPOT (Modlniczka) | 7 | 24 |

  [tenis4U club list](https://api.tenis4u.pl/court/all), [e.g. Padel House](https://app.tenis4u.pl/court/480). Read
  2026-10-08.

### kluby.org: Padel House Kraków's public schedule stops 7 days ahead

- **[MEASURED]** Asking Padel House Kraków's kluby.org schedule for 16 Oct, 22 Oct, 8 Nov or 8 Dec 2026 serves
  Thursday 15 Oct. That is today plus 7, asked on 2026-10-08. 14 and 15 Oct are served as asked.
  [kluby.org schedule](https://kluby.org/padel-house-krakow/grafik?data_grafiku=2026-10-22&dyscyplina=1&strona=0).
  Read 2026-10-08. No screenshot was saved: a headless browser got kluby.org's error page, so this was read from the
  served HTML.
- **[POLICY]** Fame Sport Club's kluby.org page now says "Ten klub nie korzysta z systemu rezerwacji ONLINE." Its
  bookings run on tenis4U (above). [kluby.org](https://kluby.org/fame-sport-club/grafik). Read 2026-10-08.

### Playmore: open games follow the club's own booking window, and the grid opens three days out

- **[POLICY]** Playmore's three Kraków clubs are squash clubs: Atras Squash Club, Paolo Squash Club and Squash4You.
  All three take bookings 14 days ahead (`max_advance_booking: 14`) and allow free cancellation 24 h before
  (`time_to_free_cancellation: 24`). [Playmore venue API](https://zephyr.playmore.pl/api:4Tf8JTHd/venue/22) (also
  `/venue/127`, `/venue/182`), [Playmore Kraków padel page](https://playmore.pl/padel/krakow/). The padel clubs on that
  page are listings only and are not bookable on Playmore. Read 2026-10-08.
- **[POLICY]** The open-game creator stops at that window. It shows "Brak terminów - gry można tworzyć tylko z
  ograniczonym wyprzedzeniem. Wróć do bliższych dni." and refuses a later slot with "Ten termin jest zbyt odległy -
  wybierz bliższą datę." The grid starts three days out: "Pokazujemy terminy od {date} — gry zakładane 3+ dni
  wcześniej zbierają komplet mniej więcej 3 razy częściej. Wcześniejsze dni są pod strzałką."
  [strings](https://playmore.pl/assets/Ct1XsxUt.js) (`creator.slot.maxAdvance`, `.leadIntro`, `creator.errors.tooFarAhead`),
  [flag registry](https://playmore.pl/assets/p_SkNwim.js) (`open-game-creator-liquidity-hints`, added 2026-09-24:
  "siatka startuje od T+3"). Read 2026-10-08.

## 8. Showing a member's free hours without her opting in (R-POSTGRID-28)

### Playmore's ladder sets a player's hours from her past matches and shows them to rivals before she confirms

- **[POLICY]** The ladder asks "Te godziny się zgadzają?" and explains: "Ustawiliśmy je z Twoich meczów w tym klubie.
  Rywale widzą je przy Twoim nazwisku." The answers are "Tak, zgadzają się" and "Zmień godziny". The flag note says
  the question "nie blokuje", and that hours are "ustawione z historii gier (PLA-5899)".
  [Challenger strings](https://playmore.pl/assets/CPLsdYdo.js) (`availability.hoursGate.history`),
  [flag registry](https://playmore.pl/assets/p_SkNwim.js) (`league-availability-required`, added 2026-10-08). Read
  2026-10-08.
- **[POLICY]** Beside a rival who has no hours, the ladder offers "Poproś o godziny" ("przy rywalu bez godzin jest
  „Poproś o godziny”"). A player with an empty grid is asked "Kiedy zwykle grasz?" with "Rywal zobaczy wspólne
  terminy." before she challenges or accepts. [strings](https://playmore.pl/assets/CPLsdYdo.js)
  (`availability.askForHours`, `hoursGate.empty`). Read 2026-10-08.
- **[POLICY]** Contrast this with Playmore's seeker list. There, only visible seekers see others' full cards: "pełne
  karty widzą tylko osoby, które same są widoczne". A player can choose quiet mode: "Dostajesz powiadomienia, ale nie
  widać Cię na liście". [Szukam grania strings](https://playmore.pl/assets/5BE1o4M2.js) (`seekers.lockedBody`,
  `lockedQuietBody`). Read 2026-10-08.
- *reading:* inside a ladder league the player joined, Playmore shows rivals her hours, as inferred from her history,
  before she has said they are right. On the open seeker list the opt-in is two-way.

## 9. Gender rules that would leave the creator out, and Mixed for two players (R-POSTGRID-9, R-POSTGRID-11)

### Playtomic: only women can create an Only Women match, and only men an Only Men one

- **[POLICY]** "Only Women: This option allows only women to create and join the match. Only women can create and join
  this type of match." "Only Men: … Only men can create and join this type of match." [Gender of the match in Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831467158801-Gender-of-the-match-in-Open-Matches)
  (updated 2026-03-05). Read 2026-10-08.
- *reading:* a Playtomic creator cannot open a single-gender match that she herself could not join.

### Playtomic defines Mixed as teams of a man and a woman, and courts of 2 or 4

- **[POLICY]** "Mixed: … Each team consists of a man and a woman." [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/19831467158801-Gender-of-the-match-in-Open-Matches).
  In leagues: "Mixed: Requires one man and one woman (for pair leagues)." [FAQs | Leagues](https://helpmanager.playtomic.com/hc/en-gb/articles/20535773758097-FAQs-Leagues)
  (updated 2026-04-01). Read 2026-10-08.
- **[POLICY]** "Both private bookings and open matches support either 2 or 4 players — this depends on the court size.
  Single courts are designed for 2 players, while double courts are for 4." [Private Bookings vs Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831958258193-Private-Bookings-vs-Open-Matches)
  (updated 2026-10-07). Read 2026-10-08.
- **[ABSENT]** Whether Playtomic offers or refuses Mixed on a single court (a two-player match). Searched the player
  and club help centres (en-gb, es) for "mixed"/"mixto" with "single", "2 players", "singles". Read 2026-10-08.
- *reading:* the league FAQ limits Mixed to pairs, and a team of one cannot hold a man and a woman. Mixed for two
  players is not defined anywhere found.

## 10. The paying words in Polish, and a court on "I'm in" (R-POSTGRID-34, R-POSTGRID-36)

### Polish law requires Polish for a Kraków consumer's offer, terms and consumer information

- **[LAW]** Art. 7 ust. 1: "Na terytorium Rzeczypospolitej Polskiej w obrocie z udziałem konsumentów … używa się języka
  polskiego, jeżeli: 1) konsument … ma miejsce zamieszkania na terytorium Rzeczypospolitej Polskiej w chwili zawarcia
  umowy oraz 2) umowa ma być wykonana lub wykonywana na terytorium Rzeczypospolitej Polskiej."
  [Ustawa o języku polskim, Dz.U. 2024 poz. 1556](https://api.sejm.gov.pl/eli/acts/DU/2024/1556/text.html). Read
  2026-10-08.
- **[LAW]** Art. 7a ust. 1–2: the duty covers "nazewnictwa towarów i usług, ofert, warunków gwarancji, faktur, rachunków
  i pokwitowań, jak również ostrzeżeń i informacji dla konsumentów wymaganych na podstawie innych przepisów, instrukcji
  obsługi oraz informacji o właściwościach towarów i usług". Foreign-language offers and consumer information "muszą
  być jednocześnie sporządzone w polskiej wersji językowej". [same](https://api.sejm.gov.pl/eli/acts/DU/2024/1556/text.html).
  Read 2026-10-08.
- **[LAW]** Art. 8 ust. 1, 1a and 1b:
  - Consumer contracts "sporządza się w języku polskim". Foreign versions may sit beside the Polish one, which governs
    interpretation for Polish citizens.
  - A foreign-language-only contract is allowed only at the request of a consumer who is not a Polish citizen, knows
    the language and has first been told of the right to Polish.
  - Under art. 15, using only a foreign language in these documents and information is punishable by a fine.

  [same](https://api.sejm.gov.pl/eli/acts/DU/2024/1556/text.html). Read 2026-10-08.
- **[LAW]** Arts. 7–8 are unchanged in the current consolidated text. Neither amendment touches them: Dz.U. 2025
  poz. 1564 changes art. 11, and Dz.U. 2026 poz. 676 changes arts. 1 and 11a.
  [Dz.U. 2026 poz. 81](https://api.sejm.gov.pl/eli/acts/DU/2026/81/text.pdf),
  [2025 poz. 1564](https://api.sejm.gov.pl/eli/acts/DU/2025/1564/text.pdf),
  [2026 poz. 676](https://api.sejm.gov.pl/eli/acts/DU/2026/676/text.pdf). Read 2026-10-08.
- *reading:* the price, the paying control and the cancellation terms that a Kraków resident sees before being bound
  are an offer and consumer information required by other law, so they must exist in Polish. An English version may
  sit beside the Polish one but may not replace it.

### Courts have held "Jetzt anmelden" too weak as the paying control; none has ruled on "I'm in"

- **[LAW]** German courts applied the same EU rule (Art. 8(2) Directive 2011/83, § 312j BGB) and held these sign-up
  labels insufficient as the button that binds a consumer to pay:
  - "Jetzt anmelden": AG Bonn, 25.4.2013, 115 C 26/13; AG Mönchengladbach, 16.7.2013, 4 C 476/12.
  - "Jetzt verbindlich anmelden (zahlungspflichtiger Reisevertrag)": LG Berlin, 17.7.2013, 97 O 5/13.
  - "Jetzt anmelden" with "zahlungspflichtig bestellen" in small print: LG Leipzig, 26.7.2013, 08 O 3495/12.

  This is cited from a law publisher's commentary; the judgments themselves were not read.
  [Hilgert, Otto Schmidt IT-Recht-Blog, 30.09.2014](https://www.otto-schmidt.de/blog/it-recht-blog/die-rechtsprechung-zur-buttonlosung-schiesst-uber-das-ziel-hinaus-ITBLOG0002139.html).
  Read 2026-10-08.
- **[ABSENT]** Any ruling or authority decision on "I'm in", "Join", "Dołącz", "Teilnehmen" or a "post — you're in"
  control where joining or posting later becomes a paid booking. Searched UOKiK decisions and Polish commentary,
  German Button-Lösung case lists and the commentary above. Read 2026-10-08. The CJEU's rule that the control must
  say so even when payment falls due only after a later condition is already in
  `local-market.md#the-order-button-and-a-yes-that-charges-later`.
