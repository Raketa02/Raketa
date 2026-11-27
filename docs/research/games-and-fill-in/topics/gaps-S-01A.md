# Gaps round after the S-01A refresh

Answers to the three facts the S-01A refresh still lacked (`$W/stories/S-01A/rules-gaps.md`: R-HOME-39, R-HOME-11,
R-LEAVE-20). Read **2026-10-09**; web search worked throughout. Each `###` heading answers part of one gap and names
what it found, so it can be cited as `topics/gaps-S-01A.md#<heading>`.

Sources: Playmore's web app as served on 2026-10-09 (1,417 bundles reachable from playmore.pl, entry
`index-CFGzTarH.js`; the lines that decide each answer are quoted here, in place of an extract under `../shots/`);
Playtomic's player and club help centres (Zendesk API, English and Spanish); two OCU public complaints; Milanosport's
Playtomic guide; NBP's quarterly card report for 2025 Q3 (nbp.pl refuses an automated read, so it was read from the
Internet Archive's copy) and NBP's acquirer workbook, whose last column is 2026 Q1; Stripe's support page (carried).

Kinds: `[POLICY]` a rule, help text or text an operator ships · `[DOCS]` a provider's or regulator's document, or a
published report · `[MEASURED]` read from the product itself (here, the shipped web-app code) · `[COMPLAINT]` one
person's account · `[ABSENT]` looked for and not found, with where. *Reading* lines are this researcher's inference,
not a source.

---

## 1. R-HOME-39, R-HOME-11, R-LEAVE-20: the date in Playmore's "Bezpłatne odwołanie do {date}"

### Playmore's checkout prints a weekday, the day and month, and the hour
- **[MEASURED]** The booking checkout's policy line (`reservations.checkout.clean.policy.deadlineLine`, "Bezpłatne
  odwołanie do {date}") is drawn by the component `CheckoutCleanPolicyLine`. It fills `{date}` with the moment formatted
  as weekday, two-digit day, two-digit month, hour and minute, in the club's time zone (Warsaw unless the club has
  another), in the player's language, through `toLocaleDateString`. In Polish that reads **"Bezpłatne odwołanie do pt.,
  16.10, 18:00"**, and in English "Fri, 10/16, 06:00 PM". There is no year. (Rendered with Node 23's `Intl` for
  `pl-PL`, Friday 16 October 2026 at 18:00 Warsaw time.)
  ```
  Ya={weekday:"short",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"};
  function Xa(t,a,r){return t==null?"":$t(t,a,{...Ya,timeZone:bt(r)})}
  … g.value?a("reservations.checkout.clean.policy.deadlineLine",{date:_.value})
           :a("reservations.checkout.clean.policy.line",{h:k.value})
  ```
  and the formatter `$t`: `function o(t,r,n=m){… return new Date(t).toLocaleDateString(i(r),n) …}`.
  [Playmore web app: `DLds3ujg.js`](https://playmore.pl/assets/DLds3ujg.js), formatter
  [`CfNh__VX.js`](https://playmore.pl/assets/CfNh__VX.js), club time zone [`YOhsLvNW.js`](https://playmore.pl/assets/YOhsLvNW.js),
  strings [`93jAIRDY.js`](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-09

### The dated line appears only for a club whose free cancellation ends at a set hour the day before
- **[MEASURED]** The checkout uses the dated line only when the court's availability answer carries
  `free_cancellation_policy.mode` = `"deadline_day_before"` and a `free_cancellation_until` moment. Every other club
  gets "Bezpłatne odwołanie do {h} h przed" (for example "do 24 h przed"), which names no day at all. Once the deadline
  has passed, the line becomes "Rezerwacja bez bezpłatnego odwołania — termin już minął" (dated policy) or "Termin
  bezpłatnego odwołania minął — start za {h} h lub mniej" (hours policy).
  ```
  l=e?.free_cancellation_policy?.mode==="deadline_day_before";
  return{freeCancellationHours:…, freeCancellationUntil:l&&Number.isFinite(r)&&r>0?r:null, …}
  ```
  [Playmore web app: `CVPHfFio.js`](https://playmore.pl/assets/CVPHfFio.js), strings [`93jAIRDY.js`](https://playmore.pl/assets/93jAIRDY.js) — read 2026-10-09

### Playmore's reservation page writes the date out in full, with the year
- **[MEASURED]** After booking, the reservation page says "Bezpłatne anulowanie do {date}", where `{date}` is the long
  weekday, the day, the month written out and the year, then the hour: **"Bezpłatne anulowanie do piątek, 16
  października 2026, 18:00"**. Without a deadline moment it falls back to a count of hours
  (`cancellation.free.message`).
  ```
  formatDate:F=>vl(parseInt(F),a.value,{weekday:"long",day:"numeric",month:"long",year:"numeric",timeZone:d()}),
  formatTime:F=>zs(parseInt(F),d(),a.value)          // toLocaleTimeString, 2-digit hour and minute, 24 h
  … l("users.reservations.details.cancellation.freeUntil",{date:`${s(i)}, ${r(i)}`})
  ```
  [Playmore web app: `dAb3eQHm.js`](https://playmore.pl/assets/dAb3eQHm.js), [`Cf1R66x2.js`](https://playmore.pl/assets/Cf1R66x2.js),
  string in [`DTreLL0t.js`](https://playmore.pl/assets/DTreLL0t.js) — read 2026-10-09

### Playtomic's app names its fee-free cancel moment by a numeric date and hour
- **[COMPLAINT]** Two players quote Playtomic's cancel screen in Spain: "Comisión de cancelación: Podrás cancelar hasta
  la fecha 4/1/22 21:18 sin penalización (sujeto a las políticas de cancelación)" (complaint of 2022-01-04,
  [OCU CPTES01432661-68](https://www.ocu.org/reclamar/lista-reclamaciones-publicas/pol-C3-ADtica-de-cancelaci-C3-B3n-contra/CPTES01432661-68))
  and "Podrás cancelar hasta la fecha 29/11/24 18:18 sin penalización" (2024-11-29,
  [OCU 303df7141c9334e6f5](https://www.ocu.org/reclamar/lista-reclamaciones-publicas/pol-C3-ADtica-de-cancelaci-C3-B3n-err-C3-B3ne/303df7141c9334e6f5)).
  This line is the grace hour for Playtomic's own 0,50 € cancellation fee, not the club's cut-off — read 2026-10-09
- **[POLICY]** Carried: a private booking's checkout writes its deadline as "Before Friday 13 February | 11:30"
  (`competitor-organiser.md#cancelling-a-private-booking`).
- *Reading:* neither rival names a cancellation moment by its weekday alone. Playmore prints the day and month beside
  the weekday at checkout, but only for clubs whose deadline is a set hour the day before. Every other club gets a
  count of hours. After booking, Playmore writes the full date with the year. Playtomic writes a date on both
  screens. So a cut-off a week or more away, named only by its weekday, trails the local rival as well as Playtomic.

---

## 2. R-LEAVE-20: what Playtomic's match-confirmation email says about leaving

### Playtomic's help says what the booking email carries; leaving is not in the list
- **[POLICY]** Re-read: Playtomic emails a player on "Confirmation of new booking, match or activity joined", "Receipt
  of a transaction" and "Cancellation of a booking, match or activity"; "E-mail notifications cannot be disabled."
  [How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App)
  (updated 2026-09-29) — read 2026-10-09
- **[POLICY]** The booking confirmation email "will include automatically completed details like: Player name, Date
  and time of the match, Location, Payment information", plus a "Booking confirmation email message" the club writes
  for one court or all of them, in a language the club picks. [Playtomic club help: Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145-Communication-and-notifications)
  (updated 2026-07-21) — read 2026-10-09
- **[POLICY]** The email also carries the club's contact details: "You can find their contact details in your booking
  confirmation email or in the Playtomic app." [FAQ Players](https://playerhelp.playtomic.com/hc/en-gb/articles/19831519179281-FAQ-Players-Playtomic)
  (updated 2026-08-28); the same in [How to split the payment](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation)
  (updated 2026-07-20). Clubs are told to put their own rules into that message: "Mention it in the booking
  confirmation email in Settings > Venue > Communications > Booking confirmation" ([Split Payment vs Single payment](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721-Split-Payment-vs-Single-payment),
  updated 2026-10-08), and an extra email address or phone number can be added to it ([How players contact your club](https://helpmanager.playtomic.com/hc/en-gb/articles/48993331219985-How-players-contact-your-club),
  updated 2026-07-21) — read 2026-10-09
- **[POLICY]** Carried: an open-match joiner also gets a notification with the club's *Public match registration
  message* (parking, lockers, rental), and some clubs put a court PIN in the email
  (`competitor-joiner.md#on-joining-a-confirmation-email-and-the-clubs-message`, `competitor-joiner.md#the-court-pin-is-in-the-booking-and-its-email`).

### The email's own words on leaving: not found
- **[ABSENT]** A copy, screenshot or quotation of Playtomic's match or booking confirmation email, or any statement
  that it gives the leave-by time, the sum back or when a refund arrives. Searched:
  - Playtomic's player and club help centres through the Zendesk API, in English and Spanish ("confirmation email",
    "email cancel", "email match", "correo confirmación": 52, 52, 83 and 35 English hits and 12 to 31 Spanish), with
    every sentence that mentions the email read;
  - web search for the email's likely subject lines in English, Spanish, French and Italian;
  - Reddit, Trustpilot and email archives;
  - video walkthroughs;
  - OCU's public complaints, two of which quote the app's cancel screen but not the email;
  - a club's Playtomic guide, which says the confirmation comes "sia sulla schermata finale che via email" and gives
    no wording ([Milanosport, January 2025](https://milanosport.it/workspace/uploads/guida-utilizzo-piattaforma-playtomic-e-politiche-di-cancellazione-milanosport.pdf)).

  Only the email from a real booking settles it — read 2026-10-09
- *Reading:* Playtomic describes its confirmation email as a summary: who, when, where, what was paid and how to reach
  the club, plus whatever the club writes. Leaving words reach the email only if a club writes them into its own
  message. Nothing found shows Playtomic's email giving a leave-by time or a sum back. Rakieta's booking email names
  both, so on this evidence it is ahead. An inbox copy would turn this into a certainty.

---

## 3. R-HOME-11, R-LEAVE-20: company and non-EEA cards among card payers

### NBP: about one card in eleven issued in Poland is a business card
- **[DOCS]** NBP's quarterly card report, Table 1 ("Karty dla klientów indywidualnych" / "Karty dla klientów
  biznesowych"): at the end of September 2025, of 46 815 329 cards issued in Poland, 42 649 989 (91,1 %) were for
  individual customers and **4 165 340 (8,9 %) for business customers**, down from 4 606 023 (9,8 %) at the end of
  June. Earlier: 4 692 585 (10,1 %) at the end of 2024 and 4 643 134 (10,0 %) at the end of March 2025. The report
  counts cards; none of its transaction tables splits payments by individual or business card.
  [NBP: Informacja o kartach płatniczych w III kwartale 2025 r., Tabela 1](https://nbp.pl/wp-content/uploads/2026/01/Informacja-o-kartach-platniczych_2025-Q3.pdf)
  (December 2025), read from the [Internet Archive's copy](https://web.archive.org/web/20260112092059/https://nbp.pl/wp-content/uploads/2026/01/Informacja-o-kartach-platniczych_2025-Q3.pdf);
  the 2024 Q4 and 2025 Q1 reports' tables likewise — read 2026-10-09
- *Correction:* `gaps-LEAVE.md#no-published-share-of-business-or-foreign-cards-among-card-payments-in-poland` said the
  report does not split consumer and business. It does, for cards. It still does not split payments.
- **[DOCS]** Carried: at Stripe, "premium domestic cards are commercial, corporate, or business cards"; a consumer gold
  or platinum card is standard (`gaps-LEAVE.md#at-stripe-premium-means-business-cards-a-consumer-gold-or-platinum-card-is-standard`).

### NBP: cards issued outside Poland make under 5 per cent of card payments taken in Poland
- **[DOCS]** NBP's acquirer series splits the card transactions acquired in Poland by where the card was issued
  ("Karty wydane w Polsce" / "Karty wydane poza Polską"). In **2026 Q1**, 110 883 384 of 2 483 962 493 transactions
  (4,5 %) used a card issued outside Poland: **3,8 %** at shop terminals (90 598 709 of 2 366 347 312) and 18,2 %
  online (20 264 284 of 111 321 774). By value, the share was 8,0 % (14,54 of 180,95 bn zł). In the summer quarter,
  2025 Q3, the share was 5,2 % of transactions overall and 4,7 % at terminals. "Outside Poland" includes the other EEA
  countries, so the non-EEA share is smaller still, and the series has no EEA split.
  [NBP: akceptanci.xlsx](https://static.nbp.pl/systemy/platniczy/akceptanci.xlsx) (sheet "2015-2023", columns to
  2026 Q1) — read 2026-10-09

### A Kraków or sports-venue figure, or payments split by card type: not found
- **[ABSENT]** None of these was found:
  - the share of payments (not cards) made with business cards in Poland;
  - any figure for Kraków, or for sports venues and court bookings;
  - an EEA and non-EEA split of the foreign cards.

  NBP's report and workbook split cards by customer and payments by country of issue only. [Euromonitor's *Financial
  Cards and Payments in Poland*](https://www.euromonitor.com/financial-cards-and-payments-in-poland/report) has commercial-card tables behind a paywall. The European Commission's 2020
  [study of the Interchange Fee Regulation](https://copenhageneconomics.com/publication/study-on-the-application-of-the-interchange-fee-regulation/) (EY, Copenhagen Economics) covered Poland in depth, but no per-country share of
  commercial cards was found in its coverage. Stripe publishes no mix. Searched in Polish and English — read 2026-10-09
- *Reading (opinion):* about one card in eleven issued in Poland belongs to a business. A business card pays for a
  player's evening game only when the company pays, or the player uses it for leisure, so the share among Kraków
  players paying their 40 zł is likely well below 8,9 %. Foreign cards are 3,8 % of in-person card payments nationally,
  and tourists inflate that figure. A resident player with a card from outside the EEA (a British card, or a Ukrainian
  bank's card) is rarer still. So the 38,40 zł shown overstates the refund for a small minority, at most about one
  payer in ten. The gap is 0,16 zł on a company card (Stripe's premium 1,76 zł against 1,60 zł), 0,40 zł on a British
  card and 0,70 zł on another non-EEA card (prices in `gaps-LEAVE.md#at-stripe-premium-means-business-cards-a-consumer-gold-or-platinum-card-is-standard`).
