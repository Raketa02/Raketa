# Gaps round: RESULT

Answers to the facts the RESULT grades needed (`$W/areas/RESULT/gaps.md`), read 2026-10-08. One `##` section per gap
line, named by its rules; each `###` heading is one fact or one *not found*. A line marked *reading* is this
researcher's inference from the facts above it, not a source.

Sources, all read 2026-10-08:

- **Playtomic:** its two Zendesk help centres read whole through their public API (94 player articles in English, 99 in
  Spanish, 157 club articles; each article's own "updated" date is given where it is cited); its Terms
  (`playtomic.com/legal-conditions`); the interface text of the Android app 6.93.2 (`com.playtomic`, XAPK from APKPure),
  read as key and text from its `resources.arsc`; the English locale files of the Playtomic Manager web app
  (`manager.playtomic.io/locales/en/*.json`, public without signing in); and its App Store reviews (1,710 reviews from
  eleven storefronts, the corpus fetched for `topics/complaints.md`). The lines used are saved in
  [`../shots/gaps-RESULT-playtomic-strings.txt`](../shots/gaps-RESULT-playtomic-strings.txt).
- **Playmore:** its web app as shipped (`playmore.pl/assets/*.js`), including the team's own feature-flag register in
  `D_jVwDzs.js`, and the source maps inside its Android app 6.118.0 (`com.reservise.reserviseapp`, from APKPure), whose
  `sourcesContent` carry the developers' comments. File names are content hashes and change with each deploy, so the
  excerpts used are saved in [`../shots/gaps-RESULT-playmore-strings.txt`](../shots/gaps-RESULT-playmore-strings.txt).
  Facts from screen logic or comments say *(code)*.
- **Kraków clubs and a league:** Fame Sport Club's 2026 regulamin (PDF), Garden Padel's, Miazga's, Atras's and
  Squash4You's regulamins, Playmore's Kraków padel list and its eight club pages, PADO's Padel House listing, and the
  Padel Kraków League rules on kluby.org.
- **Stripe:** its dispute documentation.

No product was used as a signed-in visitor, so nothing here is `[MEASURED]`. The session's web-search budget was used up
before this round started, so no search engine was queried: every source was opened at a known address, or found by
following links from one. Reddit and forums could not be searched for this round; the App Store review corpus stands in
for complaints.

Kinds: `[POLICY]` a rule or wording the operator publishes or ships; `[LAW]`; `[DOCS]` a payment provider's documents;
`[COMPLAINT]` one person's account; `[ABSENT]` looked for and not found, with where.

## R-RESULT-21: how a player Playtomic marks as a no-show contests it, and how long he has

### Playtomic publishes no way to contest a no-show and no time limit for it

- **[POLICY]** The player and club articles on the no-show policy say how a report is made (by an attending player,
  through Customer Care's chat, within 7 days and before a result is confirmed), what the absent player owes ("A debt is
  created in the app, and the no-show player must pay this debt in-app with a card in order to continue using the app")
  and that "The match result will be marked as void". Neither says how the reported player can object, or by when.
  [Player help: What happens if a player doesn't show up?](https://playerhelp.playtomic.com/hc/en-gb/articles/43240624037393-What-happens-if-a-player-doesn-t-show-up)
  (updated 2026-09-15), [club help: No-Show Policy for Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513-No-Show-Policy-for-Open-Matches-what-clubs-need-to-know)
  (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** The Terms' no-show clause names only the other side's steps: "Notification: … the remaining users have the
  option to notify this absence to the club or Playtomic's Customer Care via chat or using our email address
  (hola@playtomic.io)"; "Verification: The customer care team will proceed to confirm the absence by reviewing the chat of
  the corresponding match or contacting directly with club where the match was played"; "Once the absence is confirmed,
  Playtomic shall … charge the user or the users who did not show up." [Playtomic Terms §4, "Public Matches No Show"](https://playtomic.com/legal-conditions)
  — read 2026-10-08
- **[ABSENT]** A hearing, an appeal, a form or a deadline for the reported player: searched all 94 English and 99 Spanish
  player articles and 157 club articles for "dispute", "contest", "appeal", "disagree", "wrongly", "unfair", "claim",
  "no-show", "no se presenta", "incomparecencia", and the Terms; the app's string table has no no-show screen at all (its
  only no-show text is a post-match rating reason, "A player was missing"). — read 2026-10-08

### What a marked player can fall back on: the general complaint route

- **[POLICY]** "The User can send Playtomic their complaints, claims or any other comment they wish to make through the
  Website or App, or via email (hola@playtomic.io), and will endeavor to provide you with a substantive response within the
  legal deadlines established by the applicable regulations." EU consumers may then go to a national ADR body; Spanish law
  governs, without removing the protection of the consumer's own country. [Playtomic Terms §15–16](https://playtomic.com/legal-conditions)
  — read 2026-10-08
- **[LAW]** In Poland a trader answers a consumer's complaint within 14 days, or it is taken as accepted —
  `local-market.md#a-complaint-must-be-answered-within-14-days`.
- **[POLICY]** Disputing the charge with the bank instead makes another debt: "The disputed amount may be recorded as an
  outstanding debt … Playtomic may temporarily restrict access … until the outstanding balance is resolved. … Users are
  encouraged to contact Playtomic Customer Care before initiating a dispute with their bank." [Playtomic Terms §8,
  "Disputed Payments and Card on File Charges"](https://playtomic.com/legal-conditions); the same for a disputed Card on
  File charge: "Playtomic will create a debt on your account for that amount. While you have an active debt, you will not
  be able to make new bookings." [Player help: Card on File](https://playerhelp.playtomic.com/hc/en-gb/articles/42829261821457-Card-on-File-CoF-in-split-payments-what-it-is-and-how-it-works)
  (updated 2026-09-15) — read 2026-10-08
- **[POLICY]** On debts in general: "Playtomic is not responsible for refund requests related to any debt." [Playtomic
  Terms §8](https://playtomic.com/legal-conditions) — read 2026-10-08
- *reading:* a player Playtomic marks as a no-show learns it from a debt that locks the app, pays it to play again, and
  can only then argue through the general complaint chat or email; nothing published gives him a window, and his
  argument runs after the money has moved.

### A player marked absent while on site was turned down on the system's logs

- **[COMPLAINT]** "Despite being physically present and ready to play, I was marked as a 'no-show' and charged for the
  match. … I contacted support multiple times, explained the situation in detail, and even clarified that I was present
  at the venue. However, they relied solely on their 'system logs' and completely dismissed what actually happened on
  site." (Seli1.0, German storefront, 13 Apr 2026, 1 star) [App Store DE reviews](https://apps.apple.com/de/app/playtomic/id1242321076)
  — read 2026-10-08
- **[COMPLAINT]** "Un jugador no se ha presentado al partido, vuestro sistema se ha confundido y me ha puesto la deuda a
  mí, he intentando contactar con vosotros y me atiende una IA … que se queda en bucle." (Spanish storefront, 13 May 2026,
  1 star) [App Store ES reviews](https://apps.apple.com/es/app/playtomic/id1242321076) — read 2026-10-08

## R-RESULT-41: is an acceptance tied to the score shown, and does a correction move the automatic-confirmation date

### Playmore: confirming sends nothing about the score, and a correction restarts the clock

- **[POLICY]** *(code)* The confirm call carries no body, so it names neither the score nor a version of it:
  `` confirmResult(e,t){… a.post(`/open-games/${t}/result/confirm`,null, …)} ``, documented as "POST
  /open-games/{id}/result/confirm — opposing side accepts; the result settles." The confirm sheet shows the reported winner
  and sets ("{name} zgłosił(a) wynik Waszej gry. Zgadza się?", "Zwycięzcy: {names}") before the press.
  [Playmore web code](https://playmore.pl/assets/D4AshuGr.js), Android 6.118.0 source map `src/api/modules/league.js`,
  [strings](https://playmore.pl/assets/93jAIRDY.js); excerpts in `../shots/gaps-RESULT-playmore-strings.txt` — read 2026-10-08
- **[POLICY]** *(code)* Only the reporter can correct, while the result waits ("Popraw wynik"), and a correction restarts
  the countdown: "Re-report by the original submitter overwrites and restarts the auto-confirm clock"; "Re-report is the
  submitter's privilege (restarts the confirm clock)." The date shown, "Potwierdzi się automatycznie {date}", is read
  from the server's `confirmDeadlineAt` after every action. Android 6.118.0 source maps `src/api/modules/league.js`,
  `src/modules/userReservations/components/OpenGameResultSection.vue`; [reservation page code](https://playmore.pl/assets/CSB8J-_f.js)
  — read 2026-10-08
- *reading:* at Playmore a correction made while the other side has the old score on screen would be accepted by a press
  meant for the old one; the restarted clock gives the other side a fresh period to see the new score, but nothing ties
  the press to the score that was read.

### Playtomic: each edit hands the score back, and the 24 hours run from the last edit

- **[POLICY]** "The opposing team can confirm these results or propose a different result. The initial team will respond
  similarly until both teams confirm a result or until 24 hours pass without a team editing or confirming. … If the
  opposing team tries to confirm an incorrect result, users can only reject it and send the correct one." [Playtomic
  Terms §4, "Result Modifications" and "Handling Unconfirmed Results"](https://playtomic.com/legal-conditions) — read 2026-10-08
- **[POLICY]** The app: "After you add the score, the other team can review or edit it, and you can approve or update
  their changes. If they don't respond within 24 hours, it's validated automatically"; after an edit the other side sees
  "The other team modified this match's result". [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download)
  (`match_edit_pending_result_review_message`, `match_detail_warning_edited_match`) — read 2026-10-08
- **[ABSENT]** Whether Playtomic's confirm press names the score the player saw: the app's endpoints are not documented
  and the shipped code lists none for confirming a result. — read 2026-10-08

## R-RESULT-29: do Kraków clubs act on no-shows of paid bookings, and does Playtomic Manager show results and no-show reports

### Kraków clubs bill a no-show; only Miazga names a sanction that does not depend on an unpaid fee

- **[POLICY]** Miazga: "Niepojawienie się w zarezerwowanym czasie zobowiązuje Klubowicza do uregulowania pełnej opłaty
  za wynajem kortu"; "Nieprzyjście na grę bez powiadomienia, może się wiązać z odwołaniem wszystkich kolejnych rezerwacji
  i blokadą możliwości robienia rezerwacji do czasu uregulowania należności za kort." [Miazga regulamin §6](https://www.miazgasquash.pl/regulamin/)
  — read 2026-10-08
- **[POLICY]** Atras: a no-show is "obciążony opłatą wynajmu kortu … O fakcie niestawienia się na korcie i powstałej
  zaległości pracownik recepcji klubu poinformuje klubowicza w danym dniu lub następnym." [Atras regulamin](https://www.atrassquash.pl/regulamin/)
  — read 2026-10-08
- **[POLICY]** Fame Sport: a late cancellation or "niestawienie się na kort" means the booker pays the full fee; "Prawo do
  dokonywania kolejnych rezerwacji może zostać ograniczone wobec osób posiadających wymagalne zaległości wobec Klubu do
  czasu ich uregulowania"; for a standing slot "W przypadku późniejszego odwołania lub niestawienia się Klub pobiera pełną
  opłatę za dany termin." [Fame Sport regulamin II.5, II.7, III.9](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf)
  — read 2026-10-08
- **[POLICY]** Garden Padel (bookings valid only once paid online or at the desk): "Niewykorzystanie rezerwacji nie
  zwalnia z obowiązku zapłaty." [Garden Padel regulamin §4–5](https://gardenpadel.pl/regulamin) — read 2026-10-08
- **[POLICY]** Squash4You: on a no-show "Klient nie może posłużyć się kartą partnerską i podlega pełnym opłatom za
  wynajem kortu." [Squash4You regulamin](https://www.squash4you.pl/regulamin) — read 2026-10-08
- **[ABSENT]** Any Kraków club that records a no-show on a booking already paid, keeps a count of them, or acts on one
  except to collect money: the five regulamins above, Playmore's eight Kraków club pages and PADO's Padel House listing
  were read. Miazga's "odwołanie wszystkich kolejnych rezerwacji" is the only sanction not worded as debt collection, and
  it is a "may". — read 2026-10-08
- *reading:* a Kraków desk treats a no-show as a money question. Once the hour is paid, nothing in these rules is left to
  do; the one club whose rule reaches further (Miazga) words it as discretion.

### Playtomic Manager knows of results but cannot touch them, and has no no-show screen

- **[POLICY]** "Modify results: You can't change results in Playtomic Manager. To update a result, the players need to fill
  in this form." [Club help: General Rules to modify a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20534894210833-General-Rules-to-modify-a-reservation)
  (updated 2026-09-23) — read 2026-10-08
- **[POLICY]** A result changes what the Manager allows: "This booking cannot be cancelled as it has confirmed results"
  [Manager locale `matches`](https://manager.playtomic.io/locales/en/matches.json); "Once a player uploads the match
  result in the app, their payment can no longer be marked as Paid" [club help: How to mark a booking as paid](https://helpmanager.playtomic.com/hc/en-gb/articles/46928469100817-How-to-mark-a-booking-or-activity-as-paid-in-Playtomic-Manager)
  (updated 2026-10-05) — read 2026-10-08
- **[POLICY]** A booking's history in the Manager is meant to show attendance: "Player attendance, booking changes,
  payments, and cancellations will appear here once available." [Manager locale `bookings`](https://manager.playtomic.io/locales/en/bookings.json)
  (`match_history.text.history_will_appear_here`) — read 2026-10-08
- **[POLICY]** No-shows go round the club: "Your club cannot submit this report on the player's behalf"; the club's part
  is wallet refunds only. [Club help: No-Show Policy for Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513-No-Show-Policy-for-Open-Matches-what-clubs-need-to-know)
  — read 2026-10-08
- **[ABSENT]** A Manager screen, report or notice that shows a club the score of a game on its courts, or a no-show report
  about it: the 157 club articles (the Players report counts unique and returning players, by product, gender, level and
  benefit, with no attendance figure — [Players Report](https://helpmanager.playtomic.com/hc/en-gb/articles/50250795406225-Players-Report))
  and the Manager's public locale files `common`, `bookings`, `matches`, `customers`, `reports`, `activities`, `admins`.
  — read 2026-10-08

## R-RESULT-15: can a Playtomic reporter withdraw a no-show report

### No withdrawal is published; a result added before the review stops the procedure

- **[ABSENT]** A way to withdraw or cancel a no-show report: the no-show articles, the Terms, and the app's strings (the
  report is a support chat, not an in-app form). — read 2026-10-08
- **[POLICY]** "If a final result has been recorded for the match, the no-show policy cannot be applied"; for a late
  player, "If a match result is added, the no-show will not be applied and full payment applies." [Player help: What
  happens if a player doesn't show up?](https://playerhelp.playtomic.com/hc/en-gb/articles/43240624037393-What-happens-if-a-player-doesn-t-show-up),
  [Playtomic Terms §4](https://playtomic.com/legal-conditions) — read 2026-10-08
- *reading:* the reporter's only lever after reporting is the same support chat, or the group entering a result before
  the review; Playtomic names neither as a withdrawal.

## R-RESULT-26, R-RESULT-7: does Playtomic push "a result waits for you" or "your result was confirmed"

### Playtomic documents one push, after the match ends, and keeps the rest inside the app

- **[POLICY]** "After your match ends, you'll receive a notification to confirm players and enter results." [Player
  help: How to Change Player Positions in an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/43819065293457-How-to-Change-Player-Positions-in-an-Open-Match)
  (updated 2026-07-13; the Spanish copy says the same) — read 2026-10-08
- **[POLICY]** Inside the app the home screen carries pending actions "Upload score" and "Confirm result"; a match being
  confirmed shows "Results under validation — One team adds the result, and the other team must confirm or amend it, or
  it will be automatically approved after 24 hours"; saving shows "New results have been added. The other team has to
  confirm them." [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download)
  (`home_pending_actions_*`, `match_detail_warning_validating_match_*`, `add_result_detail_result_saved_successfully`) —
  read 2026-10-08
- **[POLICY]** Emails go out only for a booking or match joined, a receipt, a cancellation and marketing; push settings
  list social and promotional types, none about results. [Player help: How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App)
  (updated 2026-09-29), [string table](https://apkpure.com/playtomic/com.playtomic/download) (`notification_settings_type_*`)
  — read 2026-10-08
- **[ABSENT]** A push when the other team enters or edits a score, or when a result is confirmed (by the other team or
  after 24 hours): help centres, Terms, the app's strings (push texts are sent by the server and are not in the app),
  and the App Store reviews (searched for result and notification words in English, Spanish, Italian and German). — read 2026-10-08

### Playmore sends a push after the game and shows the clock on the reservation

- **[POLICY]** The flag register describes the existing entry "push po meczu na /my-reservations" that opens the result
  sheet, and a pill on the booking tile ("Wpisz wynik" / "Potwierdź wynik"); the reservation shows "Wynik czeka na
  potwierdzenie drugiej strony" and "Potwierdzi się automatycznie {date}." [Playmore flag register](https://playmore.pl/assets/D_jVwDzs.js)
  (`open-game-postgame`), [strings](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-08
- **[ABSENT]** A Playmore notification-centre event for a result entered or confirmed: the Android 6.118.0 notification
  event map lists bookings, cancellations, freed hours and wallet refunds, none for results
  (`../shots/gaps-NOTIFY-playmore-android-6.118.0-push.txt`). — read 2026-10-08

## R-RESULT-10: does anyone penalise a booked, paid game nobody recorded, and do Kraków groups record casual results

### Playtomic and Playmore's open games let an unrecorded game lapse without a penalty

- **[POLICY]** Playtomic: "You have up to one week after playing to add a result. After that window closes, it is no
  longer possible to submit one"; a game with no score ends as "No score recorded — Sometimes it's not about the results,
  it's about having a good time together". [Player help: How to edit incorrect match results](https://playerhelp.playtomic.com/hc/en-gb/articles/19831850222609-How-to-edit-incorrect-match-results)
  (updated 2026-05-27), [string table](https://apkpure.com/playtomic/com.playtomic/download) (`match_score_celebration_no_result_*`)
  — read 2026-10-08
- **[POLICY]** *(code)* Playmore's open-game result states end in "null — nothing to show (window closed, no result)": the
  prompt disappears and nothing else happens. Android 6.118.0 source map `src/views/reservations/openGames/lib/openGameResult.js`
  — read 2026-10-08

### Playmore's ladder lets a club punish a missing result, and the Kraków league counts unplayed matches as walkovers

- **[POLICY]** In Playmore's Challenger ladder a club picks what happens if "przez {duration} po zaplanowanym starcie
  meczu żaden z Was nie wpisze wyniku": a reminder "Bez kary"; the match cancelled "Bez kary, ale drabina nie zmieni się";
  or "wyzywający dostanie walkower, a wyzwany — ostrzeżenie + spadek w drabinie. Najczęściej to wyzwany unika wpisania
  przegranej." Before that, players are warned "Za {hours} h recepcja zostanie powiadomiona o braku wyniku — wpisz go
  teraz." [Playmore challenger strings](https://playmore.pl/assets/CPLsdYdo.js) (`noResult.*`, `resultDeadline.*`) — read 2026-10-08
- **[POLICY]** The Padel Kraków League on kluby.org: "Players contact other pairs in their group to arrange matches via
  the whatsapp community dedicated to the League"; "Playing all matches is mandatory. Matches not played count as
  walkovers." [Padel Kraków League rules](https://kluby.org/liga/padel-krakow-league/regulamin) — read 2026-10-08

### Playmore's own count: three open-game results since June

- **[POLICY]** Playmore's team, explaining a new post-game sheet on 26 Sep 2026: "Pętla po meczu jest martwa (od 8.06:
  3 wyniki, 6 follow), a z potwierdzonej gry do kolejnej przechodzi 2/9 graczy." [Playmore flag register](https://playmore.pl/assets/D_jVwDzs.js)
  (`open-game-postgame`, `why`) — read 2026-10-08
- *reading:* where entering a casual result is optional and costs nothing to skip, almost nobody enters one; Playmore's
  open games across its clubs produced three in about sixteen weeks.

### Kraków chat groups

- **[ABSENT]** Whether a Kraków WhatsApp or Facebook group records casual results: no group could be read (they are
  closed), and no club page, regulamin or Playmore club page mentions one. The only Kraków record of results found is the
  league above, arranged on WhatsApp and recorded on kluby.org. — read 2026-10-08
- **[ABSENT]** Any platform or club that penalises a casual (non-league) booked and paid game nobody recorded: Playtomic,
  Playmore, MATCHi (319 help articles), the five Kraków regulamins. — read 2026-10-08

## R-RESULT-12: does Playtomic's result screen show how far each level moved

### The result screen shows the outcome only; the level moves are on the profile, the full list behind Premium

- **[POLICY]** The screen after a score names the outcome and no number: "Victory, match won", "Solid effort, match lost",
  "Close match, tied", "No score recorded", "Invalid score", with a "Match recap" button. [Playtomic Android 6.93.2 string table](https://apkpure.com/playtomic/com.playtomic/download)
  (`match_score_celebration_*`, `match_detail_score_recap_cta`) — read 2026-10-08
- **[POLICY]** The profile's match cards mark each level change "Up" or "Down"; the level graph's 10-match and all-match
  views are paywalled ("Unlock more results", "Unlock all results"); Premium's "Full Level Graphs … show match type …,
  date, results with links to the original match, and level changes. Filter by last 5 matches, last 10 matches, or all
  matches." [String table](https://apkpure.com/playtomic/com.playtomic/download) (`profile_match_detail_card_level_difference_*`,
  `paywall_profile_level_graph_banner_*`), [Player help: Premium Plan](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited)
  (updated 2026-09-30) — read 2026-10-08
- **[POLICY]** "You may notice that your level changes differently than your partner's after the same match. This is
  normal." [Player help: How the Playtomic level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works)
  (updated 2026-10-07) — read 2026-10-08
- **[COMPLAINT]** Players quote the step: "ogni volta il coefficiente che ti viene assegnato è di +0,02 … Non è così però
  per la persona che ha vinto insieme a te" (Italian storefront, 10 Jun 2023); "subes o bajas de 0,01 en 0,01" (Spanish
  storefront, 24 Jun 2024); "Llegan a restarte por empates jugando con jugadores superiores" (Spanish storefront, 5 Jan
  2026). [App Store IT](https://apps.apple.com/it/app/playtomic/id1242321076), [App Store ES](https://apps.apple.com/es/app/playtomic/id1242321076)
  — read 2026-10-08

## R-RESULT-9, R-RESULT-43: how long Playmore's result entry stays open

### Playmore's open-game window is set on the server and not published

- **[POLICY]** *(code)* Whether a game can still take a result comes from the server as `reportable`; the client lists
  the caller's open games over a "30-day lookback"; a late entry is refused with `OPEN_GAME_RESULT_DEADLINE_EXPIRED`,
  shown as "Minął termin na wpisanie wyniku tej gry." Android 6.118.0 source map `src/api/modules/league.js`,
  [web code](https://playmore.pl/assets/BcyMCC7n.js), [error map](https://playmore.pl/assets/5Yh7m0Pp.js) — read 2026-10-08
- **[POLICY]** The new post-game sheet (not yet live beyond Playmore's test club) shows the result buttons "od startu gry
  do startu + 72 h". [Playmore flag register](https://playmore.pl/assets/D_jVwDzs.js) (`open-game-postgame`) — read 2026-10-08
- **[POLICY]** In its ladder and leagues the club sets the hours: "Po zakończeniu zarezerwowanego terminu kortu masz
  {duration} na wpisanie wyniku. Jeśli nikt nie wpisze, mecz zostaje automatycznie anulowany"; "Gdy jeden z Was wpisze
  wynik, drugi ma {duration} na potwierdzenie." [Playmore challenger strings](https://playmore.pl/assets/CPLsdYdo.js) —
  read 2026-10-08
- **[ABSENT]** The length of the open-game entry window: Playmore's web strings and code, the Android 6.118.0 source maps,
  its terms of service, `join.playmore.pl` and its open-games page. — read 2026-10-08
- *reading:* the window is no longer than 30 days (the list it lives in), and Playmore's newest screen for it is built
  around 72 hours from the start.

## R-RESULT-4, R-RESULT-42: what counts when the clock ends a match level, such as one set all

### Playtomic: an unfinished third set is decided on its partial score, and a tie is a result

- **[POLICY]** "What if the match ended before all sets were completed? If one pair had already won two sets when the
  match ended, that pair is the winner regardless of the unfinished set. If each pair had won one set and the third
  couldn't be completed, the partial score of the third set is typically used to determine who had the advantage. In all
  cases, all players must agree on the final result"; "To consider a match finished, at least 2 sets must be completed."
  [Player help: How to edit incorrect match results](https://playerhelp.playtomic.com/hc/en-gb/articles/19831850222609-How-to-edit-incorrect-match-results)
  — read 2026-10-08
- **[POLICY]** A set counts only at 6 or 7 games with a two-game margin, or 7–6 ("6-5 is not" valid); "Even in tied
  matches, levels will change. The team with the higher combined level will lose points, while the team with the lower
  level will gain points." The result card has a "Tie" status, besides "Forfeit" and "Double forfeit". [Player help: How
  the Playtomic level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works),
  [string table](https://apkpure.com/playtomic/com.playtomic/download) (`result_card_status_*`) — read 2026-10-08
- **[POLICY]** In club leagues the system names the case: "Incomplete Match Score — Both teams have won 1 set; Both
  teams have won 1 set, but the 3rd set is incomplete …"; "Since ties are not allowed in padel and tennis matches, you
  can choose to award points based on partial results or by completed sets only." [Club help: Scoring system and set
  validation in Leagues](https://helpmanager.playtomic.com/hc/en-gb/articles/20535702278289-Scoring-system-and-set-validation-in-Leagues)
  (updated 2026-08-01) — read 2026-10-08
- **[COMPLAINT]** "Se si gioca 1h non ha senso valutare la partita valida solo se si raggiungono i 3 set. Se la partita
  finisce ad es tra giocatori A e B: 6-3 3-3 oppure 6-3 3-1 … in tutti questi casi la partita dovrebbe essere valida e il
  vincitore sarebbe sempre il giocatore A." (Italian storefront, 29 Mar 2024, 5 stars) [App Store IT](https://apps.apple.com/it/app/playtomic/id1242321076)
  — read 2026-10-08

### Playmore: someone must win; sets are optional and unchecked

- **[POLICY]** *(code)* The report asks "Kto wygrał?" with two choices only, team A or team B, and cannot be saved
  without one; sets are "opcjonalnie … bez rygoru formatu, maks. 7" — "explicit winner side + optional sets (max 7, ints
  0–99, no sport-format validation)", "sets are an optional annotation, not a scoring source". [Playmore web code](https://playmore.pl/assets/BqgRINoI.js),
  [strings](https://playmore.pl/assets/93jAIRDY.js), Android 6.118.0 source maps `src/api/modules/league.js`,
  `openGameResult.js` — read 2026-10-08
- *reading:* a one-set-all hour at Playmore is entered by naming a winner; a level match cannot be recorded as level.

### The Kraków league gives an unfinished match to the side ahead

- **[POLICY]** "If a match is interrupted, players must reschedule. If not completed, a walkover can be given to the team
  who is winning." [Padel Kraków League rules](https://kluby.org/liga/padel-krakow-league/regulamin) — read 2026-10-08

## R-RESULT-42: how Kraków indoor padel clubs handle a court that fails mid-game

### Fame Sport moves or cancels a booking for a fault, and gives the client the choice of credit or refund

- **[POLICY]** "Klub może zmienić lub odwołać rezerwację z uzasadnionych przyczyn organizacyjnych, technicznych … w
  szczególności w przypadku awarii, czasowego wyłączenia kortu z użytkowania …"; the club offers another court or time,
  and if neither works "wniesiona opłata zostanie — według wyboru klienta — zaliczona na poczet kolejnej rezerwacji albo
  zwrócona"; "Zmiana numeru kortu w ramach obiektu na kort o porównywalnych warunkach do gry nie stanowi odwołania
  rezerwacji." Fame Sport has one indoor and one outdoor padel court. [Fame Sport regulamin II.16–20](https://famesport.pl/wp-content/uploads/2026/08/Regulamin_Fame_Sport_Club_2026_Aktualny.pdf),
  [Playmore: Fame Sport Club](https://playmore.pl/klub/fame-sport-club-krakow/) — read 2026-10-08
- **[POLICY]** Garden Padel may close "w przypadku złych warunków atmosferycznych, technicznych lub epidemiologicznych";
  its refund rule names weather only ("opłata zostanie zwrócona, z potrąceniem opłaty serwisowej operatora płatności
  (2%)"). [Garden Padel regulamin §3, §5](https://gardenpadel.pl/regulamin) — read 2026-10-08
- **[POLICY]** SAO Sports Hub (two padel courts) runs without a desk: "brama i oświetlenie uruchamiają się przez
  aplikację Tenis4U, brak stałej recepcji." [Playmore: SAO Sports Hub](https://playmore.pl/klub/sao-sports-hub-piastowska-krakow/)
  — read 2026-10-08
- **[POLICY]** Playtomic tells clubs: "For court conditions, review and address the issue, and cancel bookings if
  necessary to process refunds if the courts were unusable"; its no-show rule never applies to "court and/or facility
  issues (including … broken lights …)". [Club help: How to Handle Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097-How-to-Handle-Common-Booking-Issues-A-Quick-Guide-for-Your-Club)
  (updated 2026-08-03), [Playtomic Terms §4](https://playtomic.com/legal-conditions) — read 2026-10-08
- **[ABSENT]** A Kraków padel club's rule for a fault once play has begun (a part refund, time made up, or nothing): Fame
  Sport's and Garden Padel's regulamins, Playmore's pages for Bajada, Fame Sport, Garden Padel, Libertów, Morelowa 34,
  Padel House, Padel Spot Modlniczka and SAO, and PADO's Padel House listing (which sends to tenis4U). — read 2026-10-08
- *reading:* the Kraków rules found treat a fault as a booking the club moves or cancels, settled whole (another court,
  credit or refund); none splits an hour that has started.

## R-RESULT-28: who funds the refund to the players who came after a Playtomic no-show

### Playtomic refunds the attendees and charges the absentee; who bears the refund is not stated

- **[POLICY]** "Fees paid online are refunded automatically. If an attending player paid their share online, we refund it
  once the report has been reviewed"; "Fees paid with club wallet credit are not refunded by Playtomic … the decision to
  return the used credit to a player's wallet is entirely up to your club"; "The absent player is charged the court fee.
  A debt is created in their account." [Club help: No-Show Policy for Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513-No-Show-Policy-for-Open-Matches-what-clubs-need-to-know)
  — read 2026-10-08
- **[POLICY]** Debts are Playtomic's: "A debt originates when Playtomic covers the payment of a reservation or match
  because the user(s) involved have not paid their corresponding part. This ensures that the club receives the total
  amount … and Playtomic assumes the responsibility of collecting the amount owed." [Playtomic Terms §8](https://playtomic.com/legal-conditions);
  "Playtomic assumes the players debt and not the Club." [Player help: What are debts](https://playerhelp.playtomic.com/hc/en-gb/articles/19831869050769-What-are-debts-and-pending-payments)
  (updated 2026-09-07) — read 2026-10-08
- **[POLICY]** Clubs paid twice a month after the game ("Distribution Model"): "If Playtomic refunds a player after you've
  already received payment … Playtomic may issue the refund directly without recovering funds from you"; such clubs may
  receive payments "When Playtomic covers registration fees in debt situations". [Club help: Payout Cycle for Clubs Using
  the Distribution Model](https://helpmanager.playtomic.com/hc/en-gb/articles/37355604106129-Payout-Cycle-for-Clubs-Using-the-Distribution-Model)
  (updated 2026-09-29) — read 2026-10-08
- **[POLICY]** Clubs on the New Billing Model are paid weekly through Stripe, and a refund of a booking "within your
  cancellation policy" is taken back from the next payout ("a negative payout"). [Club help: Why did I receive a negative
  payout?](https://helpmanager.playtomic.com/hc/en-gb/articles/50457368851729-Why-did-I-receive-a-negative-payout)
  (updated 2026-09-29) — read 2026-10-08
- **[ABSENT]** Whether a no-show refund is taken from the club's payout or paid by Playtomic: the no-show articles, the
  payout and billing articles and the Terms say neither. — read 2026-10-08
- *reading:* the published pieces point to Playtomic carrying it (it refunds, it owns the absentee's debt, and the club
  article lists only wallet credit as the club's business), but on the weekly Stripe model every other refund comes out
  of the club's payout, and no article says no-show refunds are different.

## R-RESULT-29, R-RESULT-28: does a score, a standing mark or a check-in time help a club win a "not received" dispute

### Stripe names check-in confirmations as proof that a service was received

- **[DOCS]** For Visa 13.1 "Merchandise or Services Not Received" Stripe lists: "Proof of service completion: Provide
  appointment records, work logs, or check-in confirmations"; "Customer communications: The customer is obligated to
  proactively communicate the issue before filing a dispute. Include any customer interactions confirming receipt …";
  "Terms and policies: Show refund, fulfillment, and delivery policies, including agreement at checkout." [Stripe:
  Dispute reason codes and defence requirements](https://docs.stripe.com/disputes/reason-codes-defense-requirements)
  — read 2026-10-08
- **[DOCS]** For services and digital goods generally: "include evidence such as an IP address or system log proving the
  customer … used your software or service", and a screenshot of the terms as shown at checkout. [Stripe: Dispute best
  practices](https://docs.stripe.com/disputes/best-practices) — read 2026-10-08
- **[DOCS]** The evidence object has fields `service_date`, `service_documentation`, `access_activity_log`,
  `customer_communication` and `uncategorized_text`. [Stripe API: dispute evidence](https://docs.stripe.com/api/disputes/evidence_object)
  — read 2026-10-08
- **[POLICY]** Playtomic, on card charges a club starts: "Disputes are handled manually by the operations team. The
  system maintains an audit trail of player consent and transaction history to help contest chargebacks." [Club help:
  Club Initiated Transactions](https://helpmanager.playtomic.com/hc/en-gb/articles/40645779207569-Club-Initiated-Transactions-How-to-charge-your-players-stored-credit-cards)
  (updated 2026-09-08) — read 2026-10-08
- **[ABSENT]** Any statement from Stripe, a card network page Stripe links, or a platform that a match score or a
  standing (attendance) mark counts as evidence of a service received. — read 2026-10-08
- *reading:* a check-in time is evidence Stripe names outright; a score the disputing player entered or confirmed is the
  kind of usage record Stripe accepts for services, but is not named; a standing mark the club set alone is its own
  statement, not a record of the customer's use.

## R-RESULT-24, R-RESULT-34: does a visible attendance record change how often players fail to come

### Platforms keep attendance out of sight

- **[POLICY]** Playtomic shows others a level and a "reliability" that measures confidence in the level, not attendance
  (`competitor-joiner.md#no-attendance-score`, `competitor-newcomer.md#reliability`).
- **[POLICY]** Playmore's league asks after a match for "Punktualność", "Atmosfera" and "Fair play", and says "Ocenę
  widzi tylko obsługa klubu. Druga osoba jej nie zobaczy." [Playmore league rating strings](https://playmore.pl/assets/1zI0w1-9.js)
  — read 2026-10-08
- **[POLICY]** Playmore's planned post-game sheet asks "Czy wszyscy dotarli?" as "tylko zdarzenie" (recorded as an
  analytics event only, shown to nobody). [Playmore flag register](https://playmore.pl/assets/D_jVwDzs.js)
  (`open-game-postgame`) — read 2026-10-08

### No measure of the effect was found

- **[ABSENT]** A figure, from a platform, a club or a study, on whether showing a player's attendance record changes how
  often players fail to come: Playtomic's 251 English help articles and Terms, MATCHi's 319 help articles, Playmore's
  shipped code and its feature-flag register (which carries the team's own numbers, none on attendance), Padel Mates'
  strings, the 1,710-review Playtomic App Store corpus, the Kraków regulamins, and the earlier research in this folder.
  A web search for studies could not be run this round (the session's search budget was spent). — read 2026-10-08
- *reading:* the platforms read keep attendance private or do not record it; the only published lever is money (a debt
  or a full fee), so the market offers no evidence either way on a visible record.
