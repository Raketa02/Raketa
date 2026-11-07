# Gaps round — POST (the post itself)

Answers to the facts the POST area's grades needed and the topic files lacked (`$W/areas/POST/gaps.md`),
one part per rule, read **2026-10-08**. Facts already in the other topic files are not repeated; they are
linked where an answer leans on them.

**Sources.** Playmore's interface text and logic come from the JavaScript its web app serves to every
visitor (`playmore.pl/assets/*.js`). The file names are content hashes and change with each release, so a
link may stop working after the next deploy; the strings were read on 2026-10-08. One of those files
(`D_jVwDzs.js`) is Playmore's feature-flag registry: each flag carries a Polish summary and the team's
reasons, which is how its plans, figures and ramps are known here. Playtomic's help centres were read
whole through their public Zendesk API (94 player articles, 157 club articles). No product was used as a
logged-in visitor, so nothing here is `[MEASURED]`.

**Kinds:** `[POLICY]` the company's own rule, term, help or interface text · `[PRICE]` a published price ·
`[LAW]` a statute or a court · `[DOCS]` a provider's document · `[COMPLAINT]` one person's account ·
`[ABSENT]` looked for and not found, with where. Lines marked *reading* are not sources.

## 1. R-POST-39 — a game made minutes before its own fill deadline

### Playmore refuses a game that starts too close to its cut-off
- **[POLICY]** The create press is refused with "Wybrany termin jest zbyt blisko startu - gra nie zdążyłaby się skompletować. Wybierz późniejszy slot." (server code `OPEN_GAME_TOO_SOON`). [Playmore strings: reservations](https://playmore.pl/assets/93jAIRDY.js), [error map](https://playmore.pl/assets/B-ec6oFn.js) — read 2026-10-08
- **[POLICY]** Moving a game to another hour states the margin: the new start must be at least the club's cut-off plus 30 minutes away (code: `now + cancelCutoffHours × 60 min + 30 min`, else `too_soon`); the German copy reads "Das Spiel muss frühestens in {hours} Std. 30 Min. beginnen." The club's cut-off defaults to 2 h. [reschedule code](https://playmore.pl/assets/Dvmne_lJ.js), [German strings](https://playmore.pl/assets/DtS7b0k6.js), [rules box](https://playmore.pl/assets/DPJjiND7.js) — read 2026-10-08
- *Reading:* whether the create check uses the same 30-minute margin is not in the client; the refusal text says only "too close to the start".

### Playmore steers creators away from short-lead games
- **[POLICY]** Slots less than 24 h away carry a "Mało czasu" badge and the line "Do gry zostało mniej niż 24 h. Tak blisko skład zbiera się rzadko — zaproś znajomych od razu po opłaceniu albo wybierz późniejszy termin."; the grid opens at day +3: "gry zakładane 3+ dni wcześniej zbierają komplet mniej więcej 3 razy częściej". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[POLICY]** These hints sit behind the flag `open-game-creator-liquidity-hints`, on at 100 % since 25 Sep 2026 for three "lighthouse" clubs, to be widened after a review on 24 Oct. [flag registry](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08

### Playmore alerts its seekers for every game created
- **[POLICY]** The pay step says "Po opłaceniu gra pojawi się w klubie i powiadomimy szukających grania", and the creator is told how many: "Powiadomimy {count} osób szukających grania" / "Nikt jeszcze nie czeka na taką grę". No exception for a game close to its start was found; the refusal above keeps such games from being made. [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playtomic sets no minimum lead for an open match
- **[POLICY]** Open matches exist "at all available times in your club schedule"; one still short "about 1 hour before the scheduled start time" is cancelled. [How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473), [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) (updated 2026-10-08) — read 2026-10-08
- **[ABSENT]** Any rule refusing an open match created inside its last hour, or any word on whether priority alerts fire for one. Searched all 251 help articles for "minimum notice", "in advance", "too late", "last-minute", "at least … before"; the only lead-time rules found are for courses and clubs' book-ahead windows. [Playtomic player help](https://playerhelp.playtomic.com/hc/en-gb), [club help](https://helpmanager.playtomic.com/hc/en-gb) — read 2026-10-08; see also `competitor-club.md#no-minimum-notice`

## 2. R-POST-20 — whose name a pending card hold carries

### For a direct charge the club's descriptor goes to the card network
- **[DOCS]** "The full statement descriptor is provided to the bank or card network processing the payment … The customer's statement uses the connected account's static component for … Direct charges". [Stripe: Set statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors) — read 2026-10-08
- **[DOCS]** "Most banks display this information consistently, but some might display it incorrectly or not at all." For Japanese descriptors, sent only at capture, "a temporary descriptor might be visible to cardholders: Visa, Mastercard: The English-language statement descriptor" — so the ordinary descriptor already travels with the authorisation. [Stripe: Statement descriptors](https://docs.stripe.com/get-started/account/statement-descriptors) — read 2026-10-08

### Banks may show a pending hold under another name
- **[DOCS]** A Stripe user's support page, quoting Stripe: "Some banks and card issuers use a 'soft descriptor' … when the transaction is pending … but will update to the chosen descriptor once the transaction finalizes"; "the behavior is not consistent across all customers or banking systems". Third-party page, not Stripe's own. [North Capital support](https://support.northcapital.com/knowledge/why-does-my-pending-stripe-transaction-have-a-different-descriptor-showing-on-my-banking-account) — read 2026-10-08

### PKO lists a hold as "Blokada" in the account history
- **[POLICY]** Since 23 Mar 2026 IKO and iPKO show holds in the same history as completed payments: "Jeśli Twoja płatność czeka na rozliczenie, zobaczysz przy niej ikonę kłódki i oznaczenie Blokada", for "blokady płatności kartą oraz płatności mobilnych, np. BLIK". [PKO BP: zmiany w historii konta](https://www.pkobp.pl/aktualnosci/bankowosc-elektroniczna/zmiany-w-historii-konta-aplikacja-serwis) — read 2026-10-08
- **[ABSENT]** Whether PKO, mBank or any Polish bank shows the merchant's name on such a hold, or a different name than on the settled charge. Searched PKO's and mBank's help and news pages and the web ("blokada" with "nazwa sprzedawcy", "nazwa akceptanta", "transakcje oczekujące"). — read 2026-10-08

## 3. R-POST-2 — the order button: only the words on it count

### C-249/21: only the button's own words count, not the text around it
- **[LAW]** CJEU, *Fuhrmann-2* (C-249/21, 7 Apr 2022): to decide whether a button's words correspond to "order with obligation to pay", "only the words that appear on that button or that similar function should be taken into account" (ruling, paras 28 and 34); the duty must be shown "through an unambiguous formulation and thus without any reference to an overall assessment of the circumstances" (para 29), "regardless of the overall circumstances of the booking process" (para 32). "Complete booking" ("Buchung abschließen") was sent back as doubtful. [EUR-Lex: C-249/21](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62021CJ0249) — read 2026-10-08
- *Reading:* a line under the button such as "… if it fills" is one of the circumstances the Court sets aside; what is judged is the button's text alone. The later *Conny* ruling (C-400/22), that the duty applies even when payment depends on a condition, is in `local-market.md#the-order-button-and-a-yes-that-charges-later`.

### "Jetzt verbindlich anmelden!" was held not enough in Germany
- **[LAW]** LG Berlin, 17 Jul 2013, 97 O 5/13: a coach-tour button reading "Jetzt verbindlich anmelden! (zahlungspflichtiger Reisevertrag)" used neither "zahlungspflichtig bestellen" nor "an equally unambiguous formulation". Read in a law firm's report, not the judgment itself. [IT-Recht Kanzlei: Button-Lösung](https://www.it-recht-kanzlei.de/button-loesung-abmahnung-kostenpflichtig-bestellen.html) — read 2026-10-08
- **[ABSENT]** Any ruling on a button reading "I'm in", "Join", "Dołączam" or a Polish equivalent, or on a sign-up that charges only if a condition is met later, beyond *Conny*. Searched EUR-Lex, German case reports ("Jetzt anmelden", "teilnehmen") and UOKiK's site. — read 2026-10-08

### Playmore names the payment on its create button
- **[POLICY]** Steps "Termin i kort" → "Partnerzy i poziom" → "Ogłoszenie"; on step 3 the button reads "Utwórz i zapłać wpisowe ({fee} {currency})" (a club's host game: "Gra klubowa", no payment). [open-games code](https://playmore.pl/assets/DGQrxHKX.js), [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

## 4. R-POST-37 — what a creator reads about cancelling before the press

### Playmore shows its rules box on the step with the create button
- **[POLICY]** Step 3 of the creator renders the box "Zasady" above the button "Utwórz i zapłać wpisowe": "Gra dochodzi do skutku tylko w komplecie ({count} graczy)", "Brak kompletu na {hours} h 10 min przed startem → automatycznie odwołujemy grę i kort, a wpisowe wraca na portfel Playmore. Opłata serwisowa nie podlega zwrotowi.", "Do {hours} h przed startem wypiszesz się ze zwrotem wpisowego; później wpisowe przepada (anulacja nie na czas).", "Chcesz odwołać swoją grę? Po prostu się wypisz …", "Płatność z góry: portfel Playmore lub online (BLIK).", and the club's cap. Defaults when unset: cut-off 2 h, free leave 12 h. [rules box `OpenGameRulesBox`](https://playmore.pl/assets/DPJjiND7.js), [creator code](https://playmore.pl/assets/DGQrxHKX.js), [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** A different line when the free-leave window has already passed at creation; the box prints the hours, not a date. [same files] — read 2026-10-08

### Playtomic's creator passes a cancellation-policy row at checkout
- **[POLICY]** For a new open match ("you are the first player to join"): "Go to checkout … Read the Cancellation policy and then Continue to payment"; the checkout shows the date, "Competitive", the club, the total "Playtomic service fee and Tax incl." and a "Booking Cancellation Policy" row above "Continue payment". The policy's wording is not visible in the image. [Playtomic help: Add My Partner](https://playerhelp.playtomic.com/hc/en-gb/articles/19831380139793-Add-My-Partner), [checkout image](https://playerhelp.playtomic.com/hc/article_attachments/43751051675665) — read 2026-10-08
- **[POLICY]** The player rule it would show: "Match not full yet? Cancel anytime before it starts—no restrictions. Match is full? You can cancel up to 24 hours before the start time." [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465) — read 2026-10-08

## 5. R-POST-36 — a price that changes between the preview and the press

### Playmore refuses a court booking whose price changed
- **[POLICY]** Ordinary booking: "Cena tego terminu się zmieniła. Odśwież i sprawdź nową cenę."; in the multi-booking cart: "Cena uległa zmianie — odśwież pozycję". [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore keeps a moved open game's fee, or refuses the move
- **[POLICY]** Moving an open game to an hour with another fee is refused: "Dieser Termin hat eine andere Teilnahmegebühr: {fee} {currency} statt {current} {currency}. Du kannst das Spiel nur auf einen Termin zum gleichen Preis verschieben"; when it is the same: "Teilnahmebeitrag unverändert"; "Der Teilnahmebeitrag ändert sich nicht" (server code `OPEN_GAME_RESCHEDULE_FEE_CHANGED`; Polish copy not in the files read). [German strings](https://playmore.pl/assets/DtS7b0k6.js), [reschedule code](https://playmore.pl/assets/Dvmne_lJ.js) — read 2026-10-08

### Playmore's create flow names the fee but has no price-changed refusal
- **[POLICY]** The slot step shows "Cena kortu: {price} {currency}" ("Sprawdzamy cenę kortu…"), the button carries the fee, and the create refusals are a taken slot, a price that cannot be read ("Nie udało się ustalić ceny kortu dla tego terminu"), too soon, too far, a cap. [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** A create refusal for a price changed since the preview; whether the server charges the shown fee or the current one. [strings](https://playmore.pl/assets/93jAIRDY.js), [error map](https://playmore.pl/assets/B-ec6oFn.js) — read 2026-10-08

### A Kraków club changes its court prices by season, and lists both seasons
- **[PRICE]** Fame Sport's padel hall: summer 01.05–30.09.2026 110 zł (weekday 7–14), 120 zł (weekday 14–23), 120 zł (weekend); winter 01.10.2026–30.04.2027 135 / 150 / 140 zł — a 17–25 % rise on 1 October, both seasons on one page. Tennis and badminton change on the same dates. [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-08
- **[POLICY]** Fame Sport: "Opłata za wstęp na kort ustalana jest zgodnie z aktualnym cennikiem obowiązującym dla danego rodzaju kortu, dnia i godziny" (II.4); "Zmiana Regulaminu nie narusza praw nabytych ani warunków usług już opłaconych" (VII.5); notice "z odpowiednim wyprzedzeniem" only for continuing services or long contracts (VII.6). [Regulamin Fame Sport Club, from 30.08.2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-08
- **[POLICY]** Miazga Squash promises a month's notice for changed opening hours, none for prices; Atras ties the price to "cennik obowiązujący w klubie … zawierający aktualne ceny". [Miazga regulamin](https://www.miazgasquash.pl/regulamin/), [Atras regulamin](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** How far ahead a Kraków club announces a new price list, and any price change inside a season. The Wayback Machine was offline that day, so when Fame Sport first published its winter prices could not be dated. — read 2026-10-08

## 6. R-POST-9 and R-POST-21 — the creator leaves, or everybody does

### Playtomic re-centres the range on the highest player when the creator leaves (one user's account)
- **[COMPLAINT]** "When a player creates an open competitive game and e.g. is 0.5 level, then the range level is 0.2-1.2. And if for example are already three players joined and this player leaves then the range increases to the player of the highest level … The range level increases to 0.9-1.9." (GriLs_21, 1★, NL, 2026-06-07). [App Store NL feed](https://itunes.apple.com/nl/rss/customerreviews/page=1/id=1242321076/sortby=mostrecent/json) — read 2026-10-08
- *Reading:* this fits the club help's "The match level adjusts dynamically, based on the first player to join (-0.25 / +0.75)" ([How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473)) if the earliest remaining player becomes the "first"; no Playtomic source says so.

### Playtomic: gender is fixed at the first player; leaving is otherwise not described
- **[POLICY]** "The gender of a match is determined by the first player who registers"; "Once a match is created and registered, it is not possible to edit or change the gender setting"; "the only way to change the gender is to delete (if possible) the public match and create a new one". [Gender of the match in Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831467158801) — read 2026-10-08
- **[POLICY]** Club-made matches: "Competitive — … The level range is set automatically based on the first registered player's level"; "Friendly — … You can adjust the level range during creation, but not after the match has been created." [How to create an open match from Playtomic Manager](https://helpmanager.playtomic.com/hc/en-gb/articles/48305440234129) — read 2026-10-08
- **[ABSENT]** What the gender or the range becomes when the creator leaves after others joined: not in the 251 help articles (re-searched "first player", "creator", "organizer", "leaves") — read 2026-10-08

### Playmore passes the organiser's role to the earliest joiner
- **[POLICY]** An organiser with others in the game gets "Co chcesz zrobić?": "Wypisz się — gra zostaje" ("Zwalniasz swoje miejsce, a organizację przejmie {name}. Reszta składu gra dalej.") or "Odwołaj grę wszystkim" ("Tak, odwołaj grę {n} graczom"). [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[POLICY]** "organizację przejmuje najwcześniej zapisany — liga, roster watch, ≤ 5 min"; the sheet is on for every club since 26 Sep 2026, because of "pełne gry odwołane jednym kliknięciem" (two full games in four weeks). [flag registry: `open-game-organizer-leave`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[POLICY]** A game's level shows either the organiser's declared band ("Poziom podany przez organizatora") or "Średni Playmore Score zapisanych graczy". **[ABSENT]** Whether a declared band stays after the organiser leaves. [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore: a game with one player left is called off when that player leaves
- **[POLICY]** "Jesteś w tej grze sam — bez Ciebie gra odwoła się automatycznie."; leaving a game: "zwalniasz miejsce, a gra bez kompletu odwoła się automatycznie"; "Tylko organizator może odwołać tę grę." So no Playmore game stands with nobody in it. [strings](https://playmore.pl/assets/93jAIRDY.js), [main strings](https://playmore.pl/assets/CG9yQPLY.js) — read 2026-10-08

### Playtomic: an empty hour is an open match nobody has started
- **[POLICY]** "Open Matches are automatically created by Playtomic Manager at all available times in your club schedule"; "0 or 1 player: The court is never booked"; "If a club cancels a match, it will be removed from the current schedule but will reappear in the club's list of open matches, making it available for other players to join at the same date and time"; a club can share a match link only when "at least one player must be registered for the match". [How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473), [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601), [When Open Matches Occupy Club Calendar Slots](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929), [Sharing a Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535063385873) — read 2026-10-08
- **[ABSENT]** A statement of what a match becomes once every player has left. *Reading:* the hour falls back to an empty slot that the next player starts afresh, with their own gender and range.

## 7. R-POST-12 — one game offered to a set of fitting players

### Playmore tells everyone whose alerts match, and shows the creator how many
- **[POLICY]** "Po opłaceniu gra pojawi się w klubie i powiadomimy szukających grania"; "Powiadomimy {count} osób szukających grania"; on the grid "{count} osób dostaje alerty o tej porze". Alerts are by sport, level and daypart (`platforms.md#playmore--waiting-lists-and-alerts`): one broadcast, not a ranked set. [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### Playmore's rematch invites the last line-up first, with 24 hours' priority
- **[POLICY]** "Zaprosiliśmy {count} osoby z Waszego składu. Mają 24 h pierwszeństwa." After the new game is paid, "poprzedni skład dostaje zaproszenie „{Imię} zaprasza na rewanż” (… push bez SMS)". On production only for the sandbox club as of 26 Sep 2026; lighthouse clubs "najwcześniej 17.11.2026". Reason given: "Dołączający zostaje twórcą w 11% przypadków (4/38)". [strings](https://playmore.pl/assets/93jAIRDY.js), [flag registry: `open-game-rematch`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08

### Club software promises auto-fill without saying how
- **[POLICY]** PADO's club CRM: "Auto-Fill Matches — Find players to fill open spots in games"; nothing on who is asked or in what order. [PADO for clubs](https://pado.app/for-club) — read 2026-10-08

### No app offers one game as several line-ups
- **[ABSENT]** Any app that offers one game to a ranked set of fitting players, or as several line-ups at once. Searched store listings and the web (QuadMatch, Padel Players App, Padel Pulse, PlayPad, Padel Plus, Playmate, Rally, Padel iD) — each posts a game for players to opt into, or has the organiser invite by hand ("assemble all four players", QuadMatch). [QuadMatch listing](https://mwm.ai/apps/quadmatch/6783829193) — read 2026-10-08; see also `platforms.md#swipe-decks-deal-people-not-games`

## 8. R-POST-13 — the club's view of games still filling

### Playmore: the club only watches open games
- **[POLICY]** "Reszta to podgląd — Włączasz i wyłączasz funkcję, kiedy chcesz. Poza ustawieniami masz tylko podgląd gier - żadnej z nich nie obsługujesz."; "Zero pracy recepcji - Ty masz tylko podgląd". The settings: how many may search at once (1–10), the cut-off (1–48 h), free cancellation (0–72 h). [Playmore: Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-08
- **[POLICY]** Yet a player who leaves late reads "Jeśli gra nie zbierze składu albo odwoła ją klub, wpisowe wróci do Ciebie", so a club can call a game off. A pilot lets players on a club's host list post "Gra klubowa — Twoje miejsce opłaca klub" (production schedule empty until a pilot in one club, about 10 Nov 2026). [main strings](https://playmore.pl/assets/CG9yQPLY.js), [flag registry: `open-game-host-games`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[ABSENT]** What Playmore's club back office shows of a game still filling; it needs a club login and was not opened. — 2026-10-08

### Playtomic: the club can cancel, add, remove or force a court on a filling match
- **[POLICY]** Manager → Matches, filtered by venue, type, status and court type; "Cancel" ("All players will be refunded automatically"); "Remove Participant" after the player's window; "New participant" (pays in the app or by wallet); "+Add Court … will reserve the court in your schedule, even if no players have enrolled yet"; the club can also "Create open match". [How to manage Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353), [How to add/remove players](https://helpmanager.playtomic.com/hc/en-gb/articles/20535085001361), [How to create an open match from Playtomic Manager](https://helpmanager.playtomic.com/hc/en-gb/articles/48305440234129) — read 2026-10-08
- **[COMPLAINT]** "Los clubes preparan las partidas con bots, si tú inicias una y no les gusta por nivel te la quitan sin explicaciones." (Jaclegio, 2★, ES, 2026-05-06). [App Store ES feed](https://itunes.apple.com/es/rss/customerreviews/page=3/id=1242321076/sortby=mostrecent/json) — read 2026-10-08

## 9. R-POST-29 — the words of a "your game didn't happen" notice

### Playmore: "Ta gra została odwołana", and a cancellation always reaches the phone
- **[POLICY]** A link to a called-off game: "Ta gra została odwołana" + "Zobacz inne gry w {venue} w najbliższych dniach."; the organiser's own cancel: "Gra odwołana - wpisowe wróciło do wszystkich graczy."; the club page: "Ktoś dołączył, gra potwierdzona, gra anulowana - gracze wiedzą wszystko bez udziału recepcji." [strings](https://playmore.pl/assets/93jAIRDY.js), [Gry otwarte](https://join.playmore.pl/gry-otwarte/) — read 2026-10-08
- **[POLICY]** Push settings: "Tego nie wyciszysz. O płatnościach, odwołanych rezerwacjach, kodach do drzwi i kodach logowania piszemy zawsze — inaczej przepada Ci gra albo dostęp do konta." [push categories](https://playmore.pl/assets/DFF_llKm.js) — read 2026-10-08
- **[ABSENT]** The push's own words for a game that didn't fill: they are written on Playmore's server, not in the web app's files. — 2026-10-08

### Playmore pushes the organiser of a failed game, now with a way back
- **[POLICY]** "push po nieudanej grze nie miał żadnego CTA"; the fix: "link „Załóż ponownie” z pushu ligi do organizatora gry, której zabrakło graczy"; "Wariant pushu dla organizatora ma własny harmonogram w lidze (prod pusty)". [flag registry: `open-game-recreate`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08

### Playtomic's cancellation email: the words were not found
- **[COMPLAINT]** "I've received an email on the morning of the booking saying the booking has been cancelled by the organiser. I am the organiser." (KTCLMW, 1★, GB, 2024-08-09). [App Store GB feed](https://itunes.apple.com/gb/rss/customerreviews/page=3/id=1242321076/sortby=mostrecent/json) — read 2026-10-08
- **[ABSENT]** The words of Playtomic's "match cancelled" email or push. Searched the 251 help articles, the web ("your match has been cancelled", "Cancelled by Anemone", "partido cancelado") and 1,937 App Store reviews from 17 storefronts (GB, US, IE, AU, ES, SE, NL, IT, FR, DE, PL, PT, BE, DK, NO, FI, AE). That the email exists and cannot be switched off: `../games-and-fill-in-market.md` §7.5 — read 2026-10-08

## 10. R-POST-30 — making the unfilled game again

### Playmore's "Załóż ponownie" opens the creator filled in from the failed game
- **[POLICY]** "link „Załóż ponownie” z pushu ligi do organizatora gry, której zabrakło graczy … otwiera kreator wypełniony ustawieniami tamtej gry (sport, czas gry, liczba partnerów, opis, tagi, poziom — bez terminu), a krok 1 pokazuje chip „Załóż jak ostatnio”"; the chip says "Ustawienia z ostatniej gry wczytane — wybierz termin." Reason: "23 osoby zakładają 68% gier, a każde założenie to 3 kroki od zera". On production only for the sandbox club (flag 100 % with `{"venueIds":[13]}`), review on 17 Nov 2026, kept if "≥ 30% twórców nieudanej gry zakłada ją ponownie w 7 dni". [flag registry: `open-game-recreate`](https://playmore.pl/assets/D_jVwDzs.js), [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- *Reading:* the hour is left out, so the organiser still picks a slot and pays again: a short path, not one tap.

### Playmore's next-week rematch and weekly repeat
- **[POLICY]** After a game: "Zagrajcie znowu — Ten sam kort, {day} {time} za tydzień"; a switch "Powtarzaj co tydzień" on step 3 of the creator ("także po „Załóż jak ostatnio” / „Załóż ponownie”") sends `repeatWeekly: true`. [strings](https://playmore.pl/assets/93jAIRDY.js), [flag registry: `open-game-series`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08

### Playtomic: a cancelled match can't be restored
- **[POLICY]** "Cancelled matches can't be restored. You'll need to create or join a new one." [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465) — read 2026-10-08

## 11. R-POST-4 — a cap on live games per player

### Playtomic's Premium lists no extra matches, and clubs set the caps
- **[POLICY]** Premium's benefits are Zero Commissions, Advanced Statistics, Full Level Graphs, Priority Alerts and Golden Matches; no cap on matches is lifted. "Does Premium let me book further in advance? No." [Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633) (updated 2026-09-30), [Premium: common questions](https://playerhelp.playtomic.com/hc/en-gb/articles/47307663143953) — read 2026-10-08
- **[POLICY]** A club may set "Maximum Bookings/Day" and "Number of Active Bookings — This shows how many future reservations a player can have at once", also per membership. **[ABSENT]** Whether a spot in an open match counts toward them. [Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297), [Club Membership Feature](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745) — read 2026-10-08
- **[ABSENT]** Any other review naming a cap: of 1,937 App Store reviews from 17 storefronts only the two GB ones already in `competitor-newcomer.md#how-many-games-at-once` do. *Reading:* their "2 games" is most likely a club's active-booking limit, not Playtomic's. — read 2026-10-08

### Playmore caps per club, with a separate off-peak cap
- **[POLICY]** "Limit gier: maks. {max} aktywne gry naraz. Gry startujące w dni robocze {from}–{to} mają osobny limit {offPeakMax} i nie liczą się do podstawowego limitu."; refusals "Masz już {max} aktywne gry w godzinach szczytu w tym klubie. Sloty oznaczone „nie liczy się do limitu” mają osobny limit…" and "Masz już maksymalną liczbę aktywnych gier otwartych w tym klubie." [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

## 12. R-POST-27 — what someone outside sees on a game's link

### A Playtomic match link shows a stranger only "Continue in the app"
- **[MEASURED]** Opened signed out in a browser, a match link with a made-up id (`app.playtomic.com/matches/2f0c1b9e-…`) shows "Continue in the app — Everything you need is in the Playtomic app" and the download links, as every page there does; the web says nothing about whether the match exists. [app.playtomic.com](https://app.playtomic.com/), `../shots/gaps-POST-playtomic-match-link.png` — read 2026-10-08
- **[POLICY]** A Community Match can be marked private: "only the players you share the match link with, will be able to join"; an open match's chat is public ("Any user will be able to access it"). [Community Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481), [chat](https://playerhelp.playtomic.com/hc/en-gb/articles/19832063135249) — read 2026-10-08
- **[ABSENT]** What the app shows a signed-in stranger on a private match's link, or on a cancelled one. Help centre (251 articles) searched for "link", "private", "cancelled". — read 2026-10-08

### Playmore tells anyone with a link whether the game is full, called off or over
- **[POLICY]** A link to a game no longer open lands on the club's games with "Ta gra już się zapełniła" / "Ta gra została odwołana" / "Ta gra już się odbyła" / "Nie udało się sprawdzić tej gry", up to three other games there in the next 7 days, and "Daj znać o grach". The state is read from a public endpoint (`GET /public/open-games/{id}`), on for all clubs since 26 Sep 2026, because "88% gier nie odbywa się, a odbiorca linku trafiał na obcy feed bez wyjaśnienia". [strings](https://playmore.pl/assets/93jAIRDY.js), [flag registry: `open-game-landing-states`](https://playmore.pl/assets/D_jVwDzs.js) — read 2026-10-08
- **[MEASURED]** A made-up share token (`playmore.pl/g/zz9QxYk2Lw`), signed out: "To zaproszenie już nie działa — Link wygasł albo został już wykorzystany. Możesz poszukać innej gry w okolicy." with "Zobacz gry w okolicy". `../shots/gaps-POST-playmore-dead-link.png` — read 2026-10-08
- *Reading:* Playmore's games are public by design, so telling a stranger a game was called off leaks nothing it would hide.

## 13. R-POST-8 — coaching on a court booked for a game

### Miazga Squash (Kraków) forbids outsiders' personal training without its consent
- **[POLICY]** Forbidden in the club: "prowadzenia działalności przez podmioty niezwiązane z Klubem Miazga Squash bez zgody Miazga Squash, w szczególności treningów personalnych." [Miazga regulamin](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08

### Fame Sport (Kraków) sells coaching as its own service, on top of the court
- **[POLICY]** "Klub umożliwia udział w indywidualnych treningach tenisowych prowadzonych przez trenerów lub instruktorów. Termin treningu … ustalany jest z Klubem"; "Koszt treningu … obejmuje opłatę za trenera oraz opłatę za wstęp na kort" (IV.1–3). [Regulamin Fame Sport Club, from 30.08.2026](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf) — read 2026-10-08
- **[PRICE]** "Gra z trenerem: 1 os - 120zł/h + cena kortu … /każda kolejna osoba +10zł". [Fame Sport cennik](https://famesport.pl/cennik/) — read 2026-10-08

### Squash4You (Kraków) keeps its passes from coaches
- **[POLICY]** "Do zakupu karnetów nie są uprawnieni instruktorzy posiadający certyfikat trenera (klubowego lub Europejskiej Federacji Squasha) oraz kadra trenerska współpracująca ze Squash4You." [Squash4You regulamin](https://www.squash4you.pl/regulamin) — read 2026-10-08

### Playmore lets only a club's own trainers post a training as an open game
- **[POLICY]** The creator asks "Zakładasz grę jako… Gracz - szukam partnerów / Trener - prowadzę trening"; the trainer plays free ("Ty (trener) — grasz za darmo"), sets a fee and an online deposit; refusals "Nie masz aktywnego profilu trenera w tym klubie." and "Treningi z trenerem są w tym klubie wyłączone." [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08

### No Kraków padel club's rule on coaching was found
- **[ABSENT]** A Kraków padel club's regulamin that allows, or forbids, coaching on a court booked for a game: Garden Padel's and KSOS's regulamins and tenis4U's terms say nothing about coaches; the rules found are squash and tennis clubs' (above). [Garden Padel](https://gardenpadel.pl/regulamin), [KSOS](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/), [tenis4U](https://tenis4u.pl/regulamin/) — read 2026-10-08
