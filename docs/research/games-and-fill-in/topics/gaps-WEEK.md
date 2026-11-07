# Gaps round — WEEK (your week in hours, games per week, Most I'll pay)

Answers to the facts the WEEK Moderator found missing (`$W/areas/WEEK/gaps.md`), one `##` section per
gap and one `###` per fact. Read 2026-10-08. Kinds as in the other topic files; *reading* is
arithmetic or comparison, not a source. Two app builds were read as shipped, with their excerpts
saved beside this file:

- **Playmore's web app** (entry `index-C8d-0CWt.js`, linked from playmore.pl on 2026-10-08; 3,014
  bundles crawled): the code and strings behind its availability grid and open-game limits —
  [`../shots/gaps-WEEK-playmore-availability-code.txt`](../shots/gaps-WEEK-playmore-availability-code.txt).
- **Playtomic Android 6.93.2** (`com.playtomic`, XAPK from APKPure, 2026-10-08): string keys and
  values from its resources —
  [`../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt`](../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt).

Nothing was measured on a device; reading shipped code is `[POLICY]` (what the product does), never
a screenshot.

---

## R-WEEK-7 — hours changed and not saved

### Playmore saves its weekly grid by itself, 600 ms after the last tap, and says so

- **[POLICY]** Playmore's grid has no save button. Every tap, drag, preset or "Wyczyść wszystko"
  marks the week *dirty* and schedules a save of the whole week 600 ms later
  (`e.state.saveState="dirty"… e.timer=setTimeout(()=>p(e,t,r),600)`); the status beside the grid
  reads "Zapisuję…", then "Zapisano", or "Nie udało się zapisać - zaznaczenie zachowane" with a
  retry button. [Playmore store code](https://playmore.pl/assets/0fXvRGhI.js),
  [strings](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** Leaving never drops hours: the availability page saves at once when it is left
  (`onUnmounted → flush()`), when the tab is hidden (`visibilitychange`) and when the page is
  closed (`pagehide`); on the next visit a week still dirty or failed is saved again
  (`resume()`). No question is asked, because nothing is waiting to be lost.
  [Playmore AvailabilityPage](https://playmore.pl/assets/DdhlT6ee.js) — read 2026-10-08
- **[POLICY]** A tap made while a save is out is kept: the save that lands compares its revision,
  leaves the week *dirty* instead of *saved* (`e.rev===r?"saved":"dirty"`) and the next save,
  chained after it, sends the newer week. [Playmore store code](https://playmore.pl/assets/0fXvRGhI.js)
  — read 2026-10-08
- **[POLICY]** The one question Playmore's availability page asks is before clearing everything (the wizard step clears without asking): "Wyczyścić cały
  tydzień? — Usuniemy wszystkie zaznaczone godziny. Rywale przestaną widzieć, kiedy zwykle grasz."
  [Playmore strings](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** The *Szukam grania* wizard's "Kiedy zwykle możesz grać?" step uses the same store,
  so hours ticked there are saved as they are ticked, before the wizard's own "Zapisz".
  [Playmore open-games code (`SeekStepWhen`)](https://playmore.pl/assets/DM7ksFDa.js) — read 2026-10-08

### Playtomic asks "Discard changes?" when a profile edit is left, and saves time preferences with a button

- **[POLICY]** Playtomic's *Edit profile* asks before throwing edits away: "Discard changes? — You
  will lose any changes you have made" [Discard changes]; editing a community match asks "Discard
  and leave — If you discard your changes, your data will not be saved…" [Discard] / [Don't
  discard]. Android 6.93.2, keys `profile_menu_edit_discard_dialog_*`,
  `community_match_discard_dialog_*`, extract in
  [`../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt`](../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[POLICY]** Its "Your preferred time to play" is no longer one drop-down: a player adds days
  ("Add new day", "Set by days" / "Set by time frame", "You can select a fixed time frame or
  specify by the hour") and presses **"Save preferences"**, answered by "Data correctly saved".
  Same extract — read 2026-10-08
- **[ABSENT]** Whether the time-preferences screen reuses the "Discard changes?" question when it
  is left unsaved: no key of its own (`profile_add_day_to_play_*` has none); not measurable without
  a signed-in device.

### Apple's guidelines: confirm before a sheet with unsaved changes is swiped away

- **[DOCS]** "If people have unsaved changes in the sheet when they begin swiping to dismiss it,
  use an action sheet to let them confirm their action." "The Cancel (or Close) button dismisses a
  sheet without saving any changes." [Apple HIG: Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets)
  — read 2026-10-08
  - *Reading:* the two answers the market gives are "save as you tick" (Playmore) and "ask before
    discarding" (Playtomic's profile edit, Apple's guideline). Dropping ticked hours with no word,
    and dropping a tap made during a save, matches neither.

---

## R-WEEK-4 — a drag that turns back or leaves the grid

### Playmore paints each cell once per drag, paints nothing off the grid, and makes a touch wait 250 ms

- **[POLICY]** A drag paints toward the opposite of the first cell's state
  (`y=!t(e.day,e.hour)`) and paints each cell once (`d.has(e.key)` skips it): turning back
  un-ticks nothing — the same as Raketa. [Playmore grid code](https://playmore.pl/assets/DQ5ScoLS.js)
  — read 2026-10-08
- **[POLICY]** The cell under the finger is found with `document.elementFromPoint(…)
  .closest("[data-avail-cell]")`; off the cells it returns nothing and nothing is painted, and the
  drag paints again if the finger comes back. It does **not** keep ticking the edge row or column,
  as Raketa does. Same source — read 2026-10-08
- **[POLICY]** On a touch screen the paint starts only after a 250 ms hold; a move of more than
  10 px before then cancels it and the page scrolls (`setTimeout(…,250)`,
  `Math.hypot(…)>10`). Hour labels are not cells, so a drag there scrolls. Each part of the day
  ("Rano" 06–12, "W ciągu dnia" 12–17, "Wieczorem" 17–23) has a heading that ticks or unticks it whole
  ("zaznacz całość" / "odznacz całość"). Same source and
  [strings](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08

---

## R-WEEK-1 — padel before 07:00 or any court from 23:00 in Kraków

### SAO Sports Hub sells its courts, padel included, from 06:00 to midnight every day

- **[POLICY]** "Jesteśmy otwarci codziennie, od poniedziałku do niedzieli, w godzinach
  6:00-24:00. Ostatnie rezerwacje przyjmujemy tak, aby zakończyć grę przed zamknięciem obiektu."
  The hub (ul. Piastowska 26) has outdoor panoramic padel courts, two clay tennis courts and
  pickleball, booked in its own app. [SAO Sports](https://saosports.pl/) — read 2026-10-08
- **[PRICE]** A listing's rate card for SAO's padel: Mon–Fri 06:00–16:00 137 zł, 16:00–23:59
  175 zł; weekend 06:00–23:59 175 zł an hour. [PADO: SAO Sports Hub](https://pado.app/poland/krakow/clubs/sao-sports-hub-krakow)
  — read 2026-10-08 (third-party listing)

### Padel House sells padel until midnight; Atras sells squash until midnight on weekdays

- **[PRICE]** Padel House Kraków's rate card runs Mon–Fri 07:00–16:00 (120 zł) and 16:00–23:59
  (160 zł), weekend 07:00–23:59 (160 zł); "open from 7 a.m. to midnight, and from 9 a.m. on
  Sundays", booked through tenis4U. [PADO: Padel House](https://pado.app/poland/krakow/clubs/padel-house-krakow)
  — read 2026-10-08 (third-party listing; the club's own hours page was not found)
- **[POLICY]** Atras Squash (ul. Zawiła 61): "Godziny otwarcia Pon – Pt: 7:00 – 24:00, Sob – Nd:
  8:00 – 22:00". [Atras Squash](https://www.atrassquash.pl/) — read 2026-10-08
- **[PRICE]** Libertów Padel & Tennis Club (Przylesie 41, Libertów, just outside Kraków) is listed
  with hours 00:00–23:59 every day and a rate card from 00:00. [PADO: Libertów](https://pado.app/poland/krakow/clubs/libertow-padel-tennis-club)
  — read 2026-10-08 (third-party listing; no own site found, so unconfirmed)

### Most Kraków padel clubs sell 07:00–23:00

- **[POLICY]** Garden Padel: "Korty dostępne są codziennie w godzinach 7:00–23:00".
  [Garden Padel regulamin](https://gardenpadel.pl/regulamin/) — read 2026-10-08
- **[PRICE]** Bajada (ul. Tyniecka 215), Morelowa 34, Błonia Sport and Fame Sport are listed
  07:00–23:00 every day; Ahoj Padel (Staniątki, Niepołomice) 14:00–22:00 on weekdays and
  08:00–23:00 at weekends. [PADO: Bajada](https://pado.app/poland/krakow/clubs/bajada-padel-club-krakow),
  [Morelowa 34](https://pado.app/poland/krakow/clubs/morelowa-34-padel-krakow),
  [Błonia Sport](https://pado.app/poland/krakow/clubs/blonia-sport),
  [Fame Sport](https://pado.app/poland/krakow/clubs/fame-sport-club-krakow),
  [Ahoj Padel](https://pado.app/poland/krakow/clubs/ahoj-padel) — read 2026-10-08
  - *Reading:* Raketa's grid (07:00–23:00) leaves out SAO's 06:00 padel hour and the 23:00 hour
    at SAO, Padel House and Atras. Playmore's grid runs 06:00–23:00
    ([code](https://playmore.pl/assets/_5DcUrM8.js)), so it holds the 06:00 hour but not the 23:00
    one either; Playtomic's preferences take any hour ("specify by the hour").

---

## R-WEEK-16 — a weekly spend bound stated to the player

### Google Play states a monthly budget and the amount spent so far, but never blocks

- **[DOCS]** "Set a budget for your Google Play expenses": "At the top, you can find how much you
  spent so far this month." Budgets "don't prohibit transactions when you exceed your budget"; "If
  you're close to or over your budget, you get a message every time that you buy an item from your
  account." [Google Play Help](https://support.google.com/googleplay/answer/9281767?hl=en-GB) —
  read 2026-10-08

### UK gambling rules make a 7-day money limit standard, and the tighter of two limits wins

- **[LAW]** The UK Gambling Commission's technical standard RTS 12 requires deposit limits the
  customer sets in a free-text box, offered over "24 hours and 7 days and 1 month"; "Customers must
  be prompted to set a limit as part of the registration process or at the point at which the
  customer makes the first deposit"; and when daily and weekly limits are both set "the most
  restrictive limit must always apply… if a daily deposit limit of £10 and a weekly limit of £100
  are both set, then the maximum the system must allow to be deposited is £10 per day and £70 per
  week." [UKGC: RTS 12 – Financial limits](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-12-financial-limits)
  (last updated 30 Sep 2026) — read 2026-10-08
  - *Reading:* the nearest regulated precedent for "at most 2 games · up to 70 zł a week" is a
    gambling deposit limit; it states the bound in money and enforces it at the moment of payment.

### A Polish sports pass states its bound in visits, by the calendar week

- **[POLICY]** PZU Sport (149 zł a month): "8 wejść w miesiącu", "2 wejścia w tygodniu
  kalendarzowym", "maksymalnie 1 wejście do tego samego obiektu w danym dniu"; "niewykorzystane
  wejścia w danym tygodniu kalendarzowym nie przechodzą na kolejny tydzień". Rules in force from
  3 Nov 2023. [PZU Sport rules, Oferta](https://sport.pzu.pl/_fileserver/item/1513932) — read
  2026-10-08
- **[ABSENT]** A racket, booking or class app that states a player's weekly spend in money ("up to
  X zł a week"). Looked in: Playtomic Android 6.93.2 strings (memberships state "Up to %1$s active
  bookings", "Up to %1$s bookings per day", "Wallet top-up: %1$s/%2$s" — a top-up per week, month
  or year, not a ceiling), Playmore's 3,014 web bundles (every money limit is the bank's: "Kwota
  przekracza limit płatności na Twojej karcie"), Padel Mates' web strings. Gym and class software
  could not be searched further: the session's web-search budget ran out (2026-10-08).

---

## R-WEEK-20, R-WEEK-25 — telling a person when her own limit pauses or hides things

### Android dims an app when its own timer runs out; the timer resets at midnight

- **[DOCS]** Digital Wellbeing app timers, set by the user: "When you run out of time, the app
  closes and its icon dims." "App timers reset at midnight." [Android Help: Digital Wellbeing](https://support.google.com/android/answer/9346420?hl=en)
  — read 2026-10-08

### Google Play warns at the purchase; UK gambling rules require saying when a limit starts

- **[DOCS]** Google Play's budget: "If you're close to or over your budget, you get a message every
  time that you buy an item" (above). [Google Play Help](https://support.google.com/googleplay/answer/9281767?hl=en-GB)
  — read 2026-10-08
- **[LAW]** RTS 12A: "The customer must be informed when the limit will come into force." RTS 12B:
  the system "must prevent a customer from further depositing funds once a deposit limit is
  reached, until the defined period of the limit restarts". RTS 12C: limit settings must be one
  link from the home page and from every deposit screen. [UKGC: RTS 12](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-12-financial-limits)
  — read 2026-10-08

### Racket apps name the filter when a list is empty, and refuse a club cap in words

- **[POLICY]** Playtomic's open-match list, empty: "There are no matches with your filters. Try
  adjusting them or create your own match."; flexible matches: "There aren't any flexible matches
  available with your filters; try later ⏰"; activities: "No activities match your filters. Try
  adjusting them to see more options." Android 6.93.2 (`match_wizard_marketplace_empty_matches_description`,
  `match_wizard_flexible_matches_empty`, `activity_list_search_no_results_message`), extract in
  [`../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt`](../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt)
  — read 2026-10-08. These filters are chosen per search, not standing settings.
- **[POLICY]** Playmore names the missing setting and links to it: "Nie ustawiono - rywale nie
  wiedzą, kiedy proponować grę", "Ustaw swoją dostępność, żeby zobaczyć wasze wspólne okna",
  "Ustaw siatkę dostępności". [Playmore strings](https://playmore.pl/assets/CPLsdYdo.js) — read
  2026-10-08
- **[POLICY]** A club cap is refused at the press, in words, with the number: "Masz już {max}
  aktywne gry w godzinach szczytu w tym klubie… poczekaj, aż któraś gra się zakończy" (Playmore);
  "You've reached the maximum number of activities you can join for this club. Contact the club
  for further support." (Padel Mates). [Playmore strings](https://playmore.pl/assets/Ct1XsxUt.js),
  [Padel Mates strings](https://padelmates.se/locales/en/translation.json) — read 2026-10-08
- **[ABSENT]** A racket app with a limit the player sets herself, so none that says when such a
  limit starts pausing her games. Looked in: Playtomic Android 6.93.2 strings, Playmore's web
  bundles, Padel Mates' web strings (2026-10-08).
  - *Reading:* outside sport, a self-set limit announces itself at the moment it bites (a dimmed
    icon, a message at the purchase, a refusal at the deposit). Inside sport, only club caps
    exist, and they too speak at the moment of the refusal.

---

## R-WEEK-22 — what raising a cap does to joins already refused

### At Playmore and Padel Mates a refusal holds nothing; the player tries again

- **[POLICY]** Playmore's cap is checked when the open game is created: the server answers
  `OPEN_GAME_TOO_MANY_ACTIVE` and the creator shows "Nie udało się utworzyć gry"-family errors
  ("Masz już maksymalną liczbę aktywnych gier otwartych w tym klubie.", "…poczekaj, aż któraś gra
  się zakończy"). Nothing is queued: the player creates the game again later.
  [Playmore error mapping](https://playmore.pl/assets/5Yh7m0Pp.js), [strings](https://playmore.pl/assets/Ct1XsxUt.js)
  — read 2026-10-08
- **[POLICY]** Padel Mates refuses at the join and points to the club ("Contact the club for
  further support"); the club's setting is "Activity limit restrictions". Its waiting list
  ("Join waiting list") is for a full activity, not for a refused join.
  [Padel Mates strings](https://padelmates.se/locales/en/translation.json) — read 2026-10-08
- **[ABSENT]** Any platform that brings back, or tells the player about, a join refused under a
  cap once the cap is raised. Looked in: the same code and strings, Playtomic Android 6.93.2.
  - *Reading:* because the refusal elsewhere happens at the press and holds nothing, raising a cap
    there needs no rule for old refusals: the next press passes. Raketa's pause is different, a
    held yes that stays held.

### UK rules: a player-set limit goes up only after 24 hours, down at once

- **[LAW]** RTS 12D: "Customer-led limits must only be increased at the customer's request, only
  after a cooling-off period of at least 24 hours has elapsed and only once the customer has taken
  positive action at the end of the cooling off period to confirm their request. … customer-led
  reductions to limits must be implemented immediately." [UKGC: RTS 12](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-12-financial-limits)
  — read 2026-10-08

---

## R-WEEK-18 — the counting week of a per-week limit

### PZU Sport counts by the calendar week and nothing carries over

- **[POLICY]** "2 wejścia w tygodniu kalendarzowym"; "niewykorzystane wejścia w danym tygodniu
  kalendarzowym nie przechodzą na kolejny tydzień". The rules define working days as Monday to
  Friday but never state when a calendar week starts or at what hour. [PZU Sport rules](https://sport.pzu.pl/_fileserver/item/1513932)
  — read 2026-10-08

### Other limits count by the day, the month or a rolling period — or not by time at all

- **[DOCS]** Android app timers "reset at midnight"; Google Play's budget counts "this month".
  [Android Help](https://support.google.com/android/answer/9346420?hl=en),
  [Google Play Help](https://support.google.com/googleplay/answer/9281767?hl=en-GB) — read 2026-10-08
- **[LAW]** UK deposit limits run over "24 hours and 7 days and 1 month", until "the defined
  period of the limit restarts". [UKGC: RTS 12](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-12-financial-limits)
  — read 2026-10-08
- **[POLICY]** Playtomic's club memberships count "Up to %1$s bookings per day" and "Up to %1$s
  active bookings"; Playmore's cap counts "aktywne gry naraz", with a separate count for off-peak
  slots; neither counts by the week. [Playtomic extract](../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt),
  [Playmore strings](https://playmore.pl/assets/Ct1XsxUt.js) — read 2026-10-08
- **[ABSENT]** Any platform or club that states the hour its week starts (Monday 00:00, 07:00 or
  otherwise) for a per-week limit. Looked in: the sources above and the Kraków club rules already
  read (Atras, Miazga, Squash4You, Garden Padel, SAO, KSOS).

---

## R-WEEK-13, R-WEEK-30 — how many games a week regular players play in Poland

### GUS 2025: nine in ten Poles who play tennis, badminton or squash every week play once or twice

- **[DATA]** GUS, *Uczestnictwo w sporcie i rekreacji ruchowej w 2025 r.* (published 27 Jul 2026),
  table 26, "Gra w tenisa ziemnego, badmintona lub squasha", share of participants by frequency:
  okazjonalna 61.7 %, sporadyczna 19.7 %, systematyczna 1–2 razy w tygodniu 17.2 %, 3–5 razy
  1.4 %, ponad 5 razy —. In towns: 66.1 / 17.0 / 15.2 / 1.7 / —; men 52.9 / 26.1 / 20.5 / 0.5;
  women 70.5 / 13.2 / 13.9 / 2.4. Padel is not a separate line. "Systematyczne uczestnictwo
  oznacza uczestnictwo w zajęciach … co najmniej 1 raz w tygodniu." [GUS: release](https://stat.gov.pl/obszary-tematyczne/kultura-turystyka-sport/sport/uczestnictwo-w-sporcie-i-rekreacji-ruchowej-w-2025-r-,4,5.html),
  [tables (XLSX)](https://stat.gov.pl/download/gfx/portalinformacyjny/pl/defaultaktualnosci/5495/4/5/1/uczestnictwo_w_sporcie_i_rekreacji_ruchowej_w_2025_r._tablice.xlsx),
  [publication (PDF), "Podstawowe pojęcia"](https://stat.gov.pl/download/gfx/portalinformacyjny/pl/defaultaktualnosci/5495/4/5/1/uczestnictwo_w_sporcie_i_rekreacji_ruchowej_w_2025_r..pdf)
  — read 2026-10-08
  - *Reading:* of those who play these sports every week, 17.2 / 18.6 = 92 % play once or twice
    and 8 % three to five times. Across all sports, GUS counts 70.3 % of weekly participants at
    1–2 times, 24.5 % at 3–5 and 5.2 % above 5 (same publication). A default of 2 sits at the top
    of the band where most weekly racket players are.

### Playmore asks "how often" with three weekly bands, and its sample profile says 1–2 a week

- **[POLICY]** The Playmore Score quiz for padel: "Jak często lądujesz na korcie? — Okazjonalnie
  (jak się zbierze czwórka) / Mniej więcej raz w tygodniu / 2–3 razy w tygodniu / 4+ razy w
  tygodniu (kort to mój drugi dom)"; the same bands for badminton and pickleball. The profile's
  example bio: "Gram 2 lata, poziom średni, na korcie 1-2 razy w tygodniu." [Playmore padel quiz](https://playmore.pl/assets/CzIUSdk1.js),
  [strings](https://playmore.pl/assets/CPLsdYdo.js) — read 2026-10-08
- **[POLICY]** PZU Sport's monthly pass allows "2 wejścia w tygodniu kalendarzowym" (above).
- **[ABSENT]** A Polish padel-specific count of games per week per player (Playtomic, Playmore,
  the Polish padel association): not found; the web-search budget ran out before the Playtomic
  *Global Padel Report* could be read.

---

## R-WEEK-28 — a join refused because of the player's own stated hours

### Playmore uses usual hours to suggest and to mark, never to refuse

- **[POLICY]** Playmore marks a proposed slot "Pasuje do Twojej dostępności" and says "To wstępna
  dostępność - termin i tak potwierdzicie razem"; *Szukam grania* only suggests ("podpowiemy gry
  w Twoich terminach"). Before a first Challenger challenge or acceptance it asks for usual hours
  if none are set ("Zaznacz jednym tapnięciem i od razu przejdziesz do wyzwania"), or to confirm
  hours read from past matches ("Ustawiliśmy je z Twoich meczów w tym klubie… Tak, zgadzają się /
  Zmień godziny"). The only hour-based refusal is the system's own window: "Któryś z terminów
  wypada poza godzinami 6:00–22:30." [Playmore strings](https://playmore.pl/assets/CPLsdYdo.js),
  [hours gate code](https://playmore.pl/assets/D_EAS1DE.js) — read 2026-10-08
- **[POLICY]** Playtomic's "Preferred time to play" is a profile preference with no refusal string
  of its own; its join refusals are about level and gender ("You cannot join the activity - check
  your level and gender information.", "This player does not fit the gender option of the match")
  and timing ("You must join at least %1$s before it starts").
  [Playtomic extract](../shots/gaps-WEEK-playtomic-android-6.93.2-strings.txt) — read 2026-10-08
- **[ABSENT]** Any app that refuses a join or a seat because it falls outside the player's own
  stated hours. Looked in: Playmore's 3,014 web bundles, Playtomic Android 6.93.2 strings, Padel
  Mates' web strings (2026-10-08).
