# Payments gaps 04 — CLUBMONEY and RESCUE (market)

Answers to the market gaps the payments-pass Moderator left on **R-CLUBMONEY-5, -8, -26** and **R-RESCUE-2, -8, -9,
-14, -15, -20, -21, -24, -35, -42, -47, -50**. Written 2026-10-20. Each gap is a `###` heading naming its rule IDs.

**Sources this round.** Every gap had been looked for before, so this round went to sources not tried before:

- the code and text files Playmore's web app serves today (1 709 files read 2026-10-20, including its own register of
  feature switches with the team's notes);
- the text files and code Playtomic Manager's web app serves to a visitor (`manager.playtomic.io/locales/en/*.json`,
  822 code files);
- Playtomic's and MATCHi's help centres, read through their Zendesk APIs;
- PADO's site;
- Stripe's, Android's and Material's own documents and source;
- vendor payment data;
- web, Reddit and Polish tax-ruling searches.

Facts already in this folder are cited by anchor, not repeated.

Kinds:

- `[POLICY]` is the company's own rule, help or interface text. *(code)* marks text read from the code it serves.
- `[DOCS]` is a provider's or platform's document.
- `[LAW]` is a statute or ruling.
- `[ABSENT]` means looked for and not found, with where.

Lines marked *Reading* are interpretation, not sources.

| Rule | Status this round |
|---|---|
| R-CLUBMONEY-5, -8 | **Answered for Playtomic Manager**, plus Stripe's own banner; Przelewy24's and Tpay's panels still *not found* |
| R-CLUBMONEY-26 | *Not found*: no ruling names Stripe; the closest rulings are carried |
| R-RESCUE-20 | *Not found*: no ruling on a fee kept back from a refund |
| R-RESCUE-42 | **Answered for Playmore** (word for word, from its code). Playtomic: what an empty *Find a match* says is still *not found* |
| R-RESCUE-2 | *Not found*: only the clubs' own records hold it |
| R-RESCUE-14 | *Not found*: no new authority; the nearest rulings are carried |
| R-RESCUE-15 | **Partly answered**: how Android times an Undo for people who need longer. How players read it still needs players |
| R-RESCUE-21 | *Not found*: no published rate; one more provider's definition of failure |
| R-RESCUE-24 (how often a card is fixed in 30 min) | *Not found*. Two nearby figures |
| R-RESCUE-24, R-RESCUE-50 (Playmore's 10-minute held seat) | **Answered**: the pilot began 12 Oct 2026 at one club; the decision to go wider is due 9 Nov; its words to the others |
| R-RESCUE-47 | **Answered for Playmore** (a "refund failed" state) and **partly for MATCHi**; Playtomic still *not found* |
| R-RESCUE-35 | *Not found* |
| R-RESCUE-9 | *Not found*: PADO's page names the feature only |
| R-RESCUE-8 | *Not found* for Playtomic |

---

### R-CLUBMONEY-5, R-CLUBMONEY-8 — Playtomic Manager warns a live club before its payments stop and sends it to Stripe; nothing marks "Stripe is checking"

**Answer.** Playtomic Manager keeps no account status of its own.

- When Stripe still wants details from a club that is already live, Manager shows a warning banner and a dialog,
  *before* anything stops: "Your payments are about to be interrupted".
- Its button opens Stripe.
- Manager has no text for "Stripe is checking your documents", and none for an account that is blocked or restricted.
- Stripe's own banner component, which a platform may embed, does show items "in review".
- Przelewy24's and Tpay's panel screens are still *not found*.

**Playtomic Manager (Playtomic's club software, the main competitor).**

- **[POLICY]** *(code)* The warning's English text:
  - title: "Your payments are about to be interrupted";
  - body: "Your Stripe Connect Account has missing information. Solve this issue immediately, otherwise online
    payments and payouts will be interrupted.";
  - buttons: "Add missing information" and "Skip for now".

  The Stripe page's button reads "View on Stripe", and while it redirects: "Redirecting to Stripe Express platform".
  Before a club has filled in its billing details: "Please complete your billing information to connect with Stripe.
  You can do this in the onboarding or in the Billing section".
  [Manager strings: integrations](https://manager.playtomic.io/locales/en/integrations.json) — read 2026-10-20
- **[POLICY]** *(code)* When the warning shows, and what the buttons do:
  - The warning is a banner plus a dialog. It shows only when the club's Stripe record lists required fields
    (`requiredFields.length > 0`), and only for a club that has finished onboarding and is live (onboarding
    `FINISHED`, Playtomic and tenant status `ACTIVE`).
  - "Add missing information" asks Playtomic's server for a Stripe Account Link and sends the browser there
    (`window.location.replace`).
  - Manager's Stripe page does the same. It renders no status of its own: it fetches a link and redirects. If the
    server answers `STRIPE_ONBOARDING_NOT_COMPLETED`, it asks for an onboarding link instead.

  [stripeConnect-DAfYDQC7.js](https://manager.playtomic.io/assets/stripeConnect-DAfYDQC7.js),
  [StripeConnect-D8_sQ9mM.js](https://manager.playtomic.io/assets/StripeConnect-D8_sQ9mM.js) — read 2026-10-20
- **[POLICY]** *(code)* At sign-up, "Connect to Stripe" is an onboarding step: "To enable Playtomic to send you funds
  … you need to register your billing information at their system". Once onboarding is done, the review Manager names
  is Playtomic's own:
  - "Review in progress. Pending to go Live";
  - "Our Customer Team is reviewing it. You will receive an email from us with the date & time you will be LIVE."

  [Manager strings: onboarding](https://manager.playtomic.io/locales/en/onboarding.json) — read 2026-10-20
- **[ABSENT]** Manager has no string for a verification Stripe is still running, nor for an account Stripe has
  blocked or restricted. Searched every key and value in the integrations, billing and onboarding strings, and every
  Stripe- or verification-related key in the 822 code files, for "verif", "review", "pending", "restrict", "blocked",
  "suspend", "document", "kyc" and "payout". The only "blocked" is Playtomic's own subscription paywall ("Club blocked
  at Paywall", seen by Playtomic staff). Read 2026-10-20.
- **[ABSENT]** Whether Playtomic also emails the club when it shows this warning: no string or help article says so.
  Searched the Manager strings above and carried `gaps-CLUBMONEY.md#not-found-the-screens-a-club-sees-while-checked-or-restricted`.
  Read 2026-10-20.

*Reading:*

- Playtomic warns a live club while Stripe is still *asking*, in the app, before anything stops.
- Raketa's desk hears only once payments have stopped (R-CLUBMONEY-8).
- Playtomic sends the club to Stripe's Express pages for the rest; Raketa's clubs have the full Stripe Dashboard
  instead.
- Neither product gives a separate "Stripe is checking" state. On R-CLUBMONEY-5 the two are level.

**Stripe's own banner, which a platform may embed.**

- **[DOCS]** Stripe's notification banner "lists open tasks that can affect a connected account's status or
  capabilities".
  - It "renders only when the connected account must respond to risk interventions or provide currently due
    requirements after initial onboarding".
  - It "won't render any UI if the account is missing `details_submitted`".
  - Its callback reports `total` and `actionRequired`. Stripe's own example text for notices that need no action is
    "The items below are in review."

  [Notification banner](https://docs.stripe.com/connect/supported-embedded-components/notification-banner) — read
  2026-10-20; part of the page was served in Spanish, and the sentences quoted are its English ones.
- *Reading:* Stripe gives a platform a ready way to show a club "in review" without a status of its own. Neither
  Playtomic nor Raketa uses it. Stripe's own reading of a check in progress is carried in
  `stripe-gaps-04.md#r-clubmoney-5--what-the-v1-read-shows-while-the-accounts-v2-capabilities-are-pending`.

**Przelewy24 and Tpay (the status quo).**

- Carried: their terms and help are in `gaps-CLUBMONEY.md#8-while-documents-are-checked-or-the-account-is-blocked-r-clubmoney-5-r-clubmoney-8`.
  - Tpay takes no payments until verified, and confirms verification by email.
  - Przelewy24 requests documents by email, and blocks an account whose documents are out of date.
- **[ABSENT]** The screens either panel shows while verifying or blocked are still not found.
  - `panel.przelewy24.pl` serves only a server-rendered login page to a visitor.
  - `panel.tpay.com` and `register.tpay.com` answer 403 to a visitor.

  Neither ships interface text that can be read without an account. Read 2026-10-20.

---

### R-CLUBMONEY-26 — A tax ruling on the cash-register exemption for sales taken through Stripe Connect: still none

- Carried **[ABSENT]**: Eureka, full phrase "Stripe", returned 151 rulings, none on a service paid to the seller
  through Stripe; "Stripe Connect" returned 0 (`gaps-CLUBMONEY.md#not-found-a-tax-ruling-on-the-cash-register-exemption-for-sales-taken-by-stripe-connect`,
  read 2026-10-08).
- Carried, the closest rulings:
  - The exemption now sits at annex item 42 of Dz.U. 2024 poz. 1902.
  - KIS accepted it on 17 Sep 2026 for an app where a payment operator collects and pays out to the seller's bank
    account, each payment carrying booking identifiers.

  (`local-market.md#no-cash-register-for-sales-paid-fully-online`).
- **[ABSENT]** This round, web searches for a KIS ruling naming Stripe, a court booking, or a payment operator under
  the exemption (Polish queries, and `site:eureka.mf.gov.pl Stripe`) found nothing newer than the carried rulings.
  - A fresh query through Eureka's public API was tried, but its request format could not be set from its served
    code: plain GET and POST answer 405 and 500. The 2026-10-08 count is the latest.
  - Read 2026-10-20.
- *Reading:* this stays with the accountant or lawyer of the open receipts question. The carried 17 Sep 2026 ruling
  turns on the operator paying out to the club's bank account with booking identifiers. Whether a Stripe payout
  carries them is a question about the payout's description, not about Stripe as such.

---

### R-RESCUE-20 — Keeping back the 1,60 zł from a late leaver's refund under the personal-card surcharge ban: still no ruling

- Carried **[LAW]**:
  - Art. 37a ust. 3 UUP bans any charge for using a personal EU card.
  - Art. 383¹ KC caps other means-of-payment fees at cost.
  - The Commission reads the payment-fee rule as covering fees "regardless of how they are presented".
  - No judgment or decision on an amount kept back from a refund.

  (`gaps-S-01A-leave-fee.md#a-fee-for-using-a-personal-eu-card-is-banned-outright-other-cards-are-capped-at-cost`;
  Stripe's side in `stripe-gaps-05.md#r-rescue-20--keeping-back-exactly-the-cards-fee-from-a-refund-stripes-terms-and-its-psd2-note-and-no-ruling`).
- **[ABSENT]** This round searched again:
  - in English, for any regulator, court or commentary on deducting a card processing fee from a refund under
    PSD2 art. 62(4);
  - in Polish, for UOKiK decisions or register entries on a refund reduced by the payment operator's commission.

  Results were general surcharging guides, the Bundeskartellamt's 2022 PSD2 opinion (nothing on refunds), and UOKiK's
  2025 PayPal decision, which is on unilateral fee changes and not on refunds. Read 2026-10-20.
- Still a question for the lawyer reviewing the terms (spec O3).

---

### R-RESCUE-42 — What an empty open-games list says: Playmore's words, read from its code; Playtomic's still undocumented

**Answer.** Playmore never shows a bare "no games".

- **An empty board:** a short promise of how its open games work, "Create a game", a one-tap row to be told when
  someone posts a game, and three steps.
- **A shared link to a game that is gone:** what happened to that game, up to three other games at the club that
  week, and the alerts row.
- **A filtered list:** "Nothing in this range", with "Clear filters".
- Playtomic documents only that a club without open matches shows "No courts available". What its *Find a match*
  says when it finds nothing is still not found.

**Playmore (the local rival, Gry otwarte).**

- **[POLICY]** *(code)* An empty open-games page at a club with open games switched on, and no filters set, renders
  in order:
  - an icon;
  - "Na razie nie ma tu gier" (nothing here yet);
  - "Wybierasz termin, piszesz, kogo szukasz, a każdy płaci swoją część." (you pick a time, say whom you're looking
    for, and each pays their part);
  - a button "Załóż grę" (create a game);
  - the alerts entry, with source `empty_state`;
  - three steps:
    - "Wybierasz termin" / "Wskaż wolny kort i godzinę, która Ci pasuje.";
    - "Mówisz ilu graczy szukasz";
    - "Dzielicie koszt kortu po równo" / "Każdy płaci swoją część wpisowego z góry."

  With filters set, the page shows "Nic w tym zakresie" / "Poszerz zakres dat albo pokaż zajęcia, żeby zobaczyć
  więcej." and "Wyczyść filtry". With level, time-of-day or sport filters it shows "Brak gier dla tych filtrów" /
  "Zmień poziom, porę albo sport, żeby zobaczyć więcej gier." At a club without open games, one line: "Brak
  nadchodzących gier otwartych w tym klubie." The home page's teaser reads "Brak nadchodzących gier otwartych".
  [CXmGZkdR.js](https://playmore.pl/assets/CXmGZkdR.js) (`OpenGamesEmptyState`),
  [CfkAg_89.js](https://playmore.pl/assets/CfkAg_89.js) (`OpenGameHeroSteps`),
  [C9ye8j_u.js](https://playmore.pl/assets/C9ye8j_u.js) (Polish strings),
  [CuTXkj_H.js](https://playmore.pl/assets/CuTXkj_H.js) — read 2026-10-20
- **[POLICY]** *(code)* The alerts entry is "Daj znać o grach w {klub}", a one-tap subscription. Its register note
  places it as "karta na górze zakładki gier, wiersz w pustym stanie i landing `?alerts=1`". Since 10 Oct 2026 it shows
  only where the club has open games. Its strings:
  - "Szukam grania: damy znać, gdy ktoś założy grę";
  - the row: "Szukam grania w {venue}: damy znać, gdy ktoś założy grę", with "Włącz";
  - after: "Dostajesz powiadomienia o grach w {venue}".

  [BlUiZcxz.js](https://playmore.pl/assets/BlUiZcxz.js) (switch `looking-for-game-alerts`),
  [C9ye8j_u.js](https://playmore.pl/assets/C9ye8j_u.js) — read 2026-10-20
- **[POLICY]** *(code)* A shared link to a game that is full, cancelled, past or unreadable:
  - a banner over the club's games: "Ta gra już się zapełniła" / "Ta gra została odwołana" / "Ta gra już się
    odbyła" / "Nie udało się sprawdzić tej gry";
  - "Zobacz inne gry w {venue} w najbliższych dniach.";
  - up to three other games at the club within 7 days that have a free seat, under "Inne gry w {venue}";
  - the alerts row.

  When there are none: "W tym tygodniu nie ma innych gier. Włącz alerty, a damy znać, gdy ktoś założy grę."

  The team's reason, in its register: "88% gier nie odbywa się, a odbiorca linku trafiał na obcy feed bez
  wyjaśnienia" (88 % of games don't take place, and whoever opened the link landed on a strange feed with no
  explanation). Switched on for everyone on 26 Sep 2026.
  [BlUiZcxz.js](https://playmore.pl/assets/BlUiZcxz.js) (switch `open-game-landing-states`),
  [C9ye8j_u.js](https://playmore.pl/assets/C9ye8j_u.js) — read 2026-10-20

**Playtomic.**

- **[POLICY]** On a club's page, "if Open Matches are not enabled for this Club, the Open Matches tab will display a
  'No courts available' message instead of showing available slots". Where a slot has no suitable match, the player
  goes on to create one.
  [How to book a court or a spot in a match in your favourite Club](https://playerhelp.playtomic.com/hc/en-gb/articles/19831715222929)
  (updated 2026-09-01) — read 2026-10-20
- **[POLICY]** *Find a match* carries a "Start a match" button. The sign-up article says: "Scroll through the results,
  choose between joining an already open match, or opening one yourself".
  [Community Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481) (updated 2026-06-19),
  [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121) (updated
  2026-10-03) — read 2026-10-20
- **[ABSENT]** The words *Find a match* shows when it returns no match. Looked in:
  - Playtomic's player help (searches "match full", "refund", "alert", "update matches");
  - a web search for its empty screen;
  - its web app, which shows only "Continue in the app" (carried:
    `gaps-POST.md#a-playtomic-match-link-shows-a-stranger-only-continue-in-the-app`,
    `competitor-newcomer.md#the-web-app-sends-everyone-to-the-phone-app`).

  Read 2026-10-20.

*Reading:*

- Against Raketa's "No games yet" over "Post the first game", Playmore's empty board makes the same offer ("Załóż
  grę"). It adds two things: a one-tap way to be told when a game appears, and, for someone arriving by a link, what
  happened to the game they were sent and other games at the same place.
- Raketa's empty Fill in shows the group's starting card "whatever games the group holds". Playmore's team found that
  showing a link's recipient an unexplained feed lost them, and changed it.

---

### R-RESCUE-2 — How often a Kraków hour handed back a day ahead is sold again: still only in the clubs' records

- Carried:
  - two reads of five Kraków clubs' grids, 21 h apart, sold about one free weekend hour in ten;
  - three evening hours handed back at the busiest club were still unsold the next morning;
  - no published resale rate.

  `gaps-S-02.md#over-the-last-day-about-one-free-weekend-hour-in-ten-was-sold`,
  `gaps-S-02.md#hours-handed-back-at-the-busiest-club-were-still-unsold-the-next-morning`,
  `gaps-S-02.md#a-resale-rate-itself-still-not-published`,
  `gaps-RESCUE.md#kraków-desks-resell-a-late-cancelled-hour-nobody-publishes-how-often`.
- Carried: Playmore's "3 z 10" full games lost to an unrefilled leave (`gaps-RESCUE.md#playmores-own-numbers-on-full-games-that-dont-happen`).
- **[ABSENT]** This round, Playmore's current register of switches (1 709 files, 2026-10-20) adds no resale or
  late-fill rate. Its waitlist note still holds the "3 z 10" reason, and the first read of the share refilled is due
  23 Oct 2026 ([BlUiZcxz.js](https://playmore.pl/assets/BlUiZcxz.js), switch `open-game-waitlist`). A true rate needs
  each handed-back hour followed until play, or the clubs' own records.

---

### R-RESCUE-14 — Whether "I'm in · 40 zł" meets the order-button rule: no new authority

- Carried, the nearest rulings:
  - **CJEU *Fuhrmann-2* (C-249/21):** only the button's own words count
    (`gaps-POST.md#c-24921-only-the-buttons-own-words-count-not-the-text-around-it`).
  - **CJEU *Conny* (C-400/22):** the duty applies even when payment depends on a later condition
    (`local-market.md#the-order-button-and-a-yes-that-charges-later`).
  - **LG Berlin, 97 O 5/13:** "Jetzt verbindlich anmelden! (zahlungspflichtiger Reisevertrag)" was not enough
    (`gaps-POST.md#jetzt-verbindlich-anmelden-was-held-not-enough-in-germany`).
  - **LG München I:** "Jetzt Mitglied werden" failed; **LG Hildesheim:** "Mit PayPal bezahlen" failed
    (`gaps-RESCUE.md#the-nearest-rulings-membership-and-payment-method-labels-failed`).
  - **BGH, I ZR 159/24:** no contract without a compliant button
    (`gaps-REQUEST.md#german-courts-no-binding-order-no-contract-and-a-later-confirmation-does-not-repair-it`).
  - **UOKiK:** accepts "zapłać teraz" and rejected "Zamawiam" (`local-market.md#the-order-button-and-a-yes-that-charges-later`).
- Carried: Playmore pairs a pay verb with the amount ("Zapłać {amount}", "Gram · zapłać {amount}", "Dołącz i zapłać
  {amount}") (`gaps-RESCUE.md#what-playmore-prints-on-its-buttons`). Its current code still reads "Gram · zapłać
  {amount}" ([CtEmagZ3.js](https://playmore.pl/assets/CtEmagZ3.js), read 2026-10-20).
- **[ABSENT]** Searched again, in German for rulings on "verbindlich anmelden", "jetzt teilnehmen" and "beitreten"
  under § 312j(3) BGB, and in Polish for 2026 UOKiK decisions on "zamówienie z obowiązkiem zapłaty". Nothing beyond the
  carried rulings, and nothing on a hold-then-take button. Read 2026-10-20.
- Still a question for a Polish consumer lawyer before launch.

---

### R-RESCUE-15 — A ten-second Undo before money moves: what Android does for people who need longer (new); how players read it still needs players

**Answer.**

- The reading half (do players take "Booking" as money about to be held or taken) is still not found. Only testing
  with players can say (carried `gaps-RESCUE.md#needs-players-not-research`).
- The accessibility half now has the platform's own rule.
  - Android has a system setting, "Time to take action", that tells apps how long a message carrying a button must
    stay up.
  - Google's own Snackbar component, Material's pop-up message with an action, honours it.
  - Before Android 10, that component keeps a message with an action on screen until it is used, whenever a screen
    reader is on.

- **[DOCS]** Google: "You can choose how long to show messages that ask you to take action, but are visible only
  temporarily."
  - Path: Settings › Accessibility › "Time to take action (Accessibility timeout)".
  - Options: "Default, 10 seconds, 30 seconds, 1 minute, or 2 minutes".
  - Android 10 or later. "Not all apps support this setting."

  [Android Accessibility Help: Change time to take action](https://support.google.com/accessibility/android/answer/9426889?hl=en)
  — read 2026-10-20
- **[DOCS]** Android's `AccessibilityManager.getRecommendedTimeoutMillis` (API 29): "Get the recommended timeout for
  changes to the UI needed by this user. Controls should remain on the screen for at least this long to give users
  time to react. Some users may need extra time to review the controls, or to reach them, or to activate assistive
  technology". `FLAG_CONTENT_CONTROLS` marks a UI "that times out" and "contains interactive controls".
  [AOSP source, AccessibilityManager.java](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/core/java/android/view/accessibility/AccessibilityManager.java)
  — read 2026-10-20
- **[DOCS]** *(code)* Material Components' `Snackbar.getDuration()`:
  - On Android 10+, it returns `getRecommendedTimeoutMillis(duration, FLAG_CONTENT_CONTROLS | …)` when the snackbar
    has an action.
  - Below Android 10: "If touch exploration is enabled override duration to give people chance to interact", which
    means `LENGTH_INDEFINITE` when it has an action and TalkBack's touch exploration is on.
  - Jetpack Compose's Material 3 snackbar passes its 4 s or 10 s through
    `accessibilityManager.calculateRecommendedTimeoutMillis` the same way.

  [Snackbar.java](https://raw.githubusercontent.com/material-components/material-components-android/master/lib/java/com/google/android/material/snackbar/Snackbar.java),
  [SnackbarHost.kt](https://raw.githubusercontent.com/androidx/androidx/androidx-main/compose/material3/material3/src/commonMain/kotlin/androidx/compose/material3/SnackbarHost.kt)
  — read 2026-10-20
- Carried: WCAG 2.2 SC 2.2.1 (turn off, adjust to ten times, or extend with 20 s warning) and Gmail's user-chosen
  5–30 s Undo (`gaps-RESCUE.md#the-accessibility-rule-on-time-limits`, `gaps-RESCUE.md#where-a-timed-undo-is-familiar`).
- *Reading:*
  - Android's own answer to "is a timed Undo a time limit" is to stretch it to the user's chosen time.
  - Google's own Undo component does that automatically, and on older phones with a screen reader it never times out.
  - A custom ten-second Undo that ignores the setting falls short of that pattern on Android.
  - Nothing found says iOS has an equivalent setting.

---

### R-RESCUE-21 — How often taking a hold fails after the hold succeeded: still unpublished

- Carried **[ABSENT]**: Stripe and Adyen call an authorisation a guarantee and publish no failure rate
  (`gaps-RESCUE.md#providers-describe-an-authorisation-as-a-guarantee-and-publish-no-failure-rate`). Stripe's side is in
  `stripe-gaps-05.md#r-rescue-21--taking-a-hold-after-the-clubs-charges-are-disabled-undocumented`.
- **[DOCS]** Checkout.com defines its "Capture rate" as "the total count of payments you've captured out of the total
  count of accepted payments". It gives three example failure reasons:
  - "The customer has insufficient funds in their account to complete the transaction."
  - "The issuer rejected the payment capture."
  - "There are technical issues due to a network outage, or temporary issuer or acquirer issues."

  It gives no typical or benchmark rate.
  [Checkout.com: Captures and refunds analytics](https://www.checkout.com/docs/business-operations/monitor-payment-performance/captures-and-refunds-analytics)
  — read 2026-10-20
- **[ABSENT]** A network-wide or provider-published rate of captures failing after a successful authorisation. A web
  search found only providers' metric definitions (Checkout.com's capture and authorisation analytics) and a
  third-party dashboard guide. Read 2026-10-20.
- *Reading:* a provider counts a capture refused for want of money as possible, which is what R-RESCUE-21 plans for.
  How often it happens can only come from the provider's own data or a live account.

---

### R-RESCUE-24 — How often a refused rescuer fixes the card within 30 minutes: still only Raketa's data; two nearby figures

- Carried: Airbnb blocks the dates for 24 hours while a guest fixes a failed payment
  (`gaps-RESCUE.md#airbnb-blocks-the-dates-for-24-hours-while-the-guest-fixes-a-failed-payment`).
- **[DOCS]** Briqpay, a checkout provider, published 7 Aug 2026 a year of data, "more than 31,500 recorded retries".
  - "The median time between a failed first attempt and a successful completion was just under two minutes" (about
    100 s; invoice retries about 150 s).
  - After a failed card, the successful next attempt was made with: another card 20 %, mobile payment 24 %,
    invoice 22 %, wallet 19 %, BNPL 15 %.
  - Its own caveat: "this dataset only contains shoppers who came back and paid successfully", and it "says nothing
    about the (likely larger) group who failed once and simply left". It skews to Nordic merchants, and Poland is
    "an assumption".

  [Briqpay: What happens after a failed payment](https://briqpay.com/blog/what-happens-after-a-failed-payment-a-data-look-at-how-shoppers-retry-at-checkout)
  — read 2026-10-20
- **[DOCS]** PayPal's merchant article (23 May 2024) cites Checkout.com (Oct 2023): "44% of consumers give up on a
  purchase after experiencing a decline."
  [PayPal: What you should know about retrying a payment](https://www.paypal.com/us/brc/article/retry-payment-or-not-retry)
  — read 2026-10-20
- **[ABSENT]** A rate of a declined payer fixing the card within 30 minutes, at any app or provider. Only Raketa's own
  live data can give it. Read 2026-10-20.
- *Reading:*
  - Those who do recover at a checkout do it in about two minutes, and a fifth of them with another card.
  - Nearly half of declined shoppers never return.
  - A 30-minute kept seat is far longer than a recovery takes, and the figures say nothing about how many never come
    back.

---

### R-RESCUE-24, R-RESCUE-50 — Playmore's 10-minute held seat went live as a pilot at one club on 12 Oct 2026; going wider is decided after 9 Nov

**Answer.**

- Playmore's league feature "Kort po połowie" is the one that holds a seat 10 minutes for whoever pays first. It is no
  longer waiting for 10 November.
- It went live on 12 Oct 2026 at one club only, for a four-week pilot. Whether it goes wider is decided at its review
  on 9 Nov 2026.
- While the seat is held, the others are told someone is joining, when the seat returns if they don't pay, and to
  check back. No notice was found for the moment it returns.

- **[POLICY]** *(code)* Playmore's register of switches, entry `league-open-match`:
  - "Pilot w OTC włączony 12.10.2026 decyzją Mata …: flaga 100% z payloadem {"venueIds":[140]}, w lidze
    LEAGUE_OPEN_MATCH_VENUE_IDS=13,140 (13 = sandbox do QA na produkcji)".
  - Review: "2026-11-09 — po 4 tygodniach pilota w 140 (start 12.10.2026): jeśli mecze otwarte dochodzą do skutku i
    nie psują drabinki — zdjąć bramkę z kodu (sekcja i opcja w checkoucie zawsze, o dostępności decyduje liga) …; w
    przeciwnym razie zgasić flagę i usunąć src/modules/league/openMatch/".
  - Its survey switch was raised to 100 % the same day, for a three-week window.

  [BlUiZcxz.js](https://playmore.pl/assets/BlUiZcxz.js) (entries `league-open-match`, `survey-league-open-match`) — read
  2026-10-20
  - Club 140 is the club this folder's earlier reading names as Okęcie, Warsaw (`gaps-RESCUE.md#playmore-counts-a-game-called-off-at-its-cut-off-as-an-empty-court`).
  - This replaces the carried "na 0%, nie wcześniej niż 10.11" (`gaps-RESCUE.md#playmore-holds-a-league-seat-10-minutes-for-whoever-pays-first`).
- **[POLICY]** *(code)* The words today:
  - **The offer:** "Gram · zapłać {amount}" — "Gra ten, kto pierwszy opłaci miejsce. Na płatność masz 10 minut."
  - **The payer:** "Dokończ płatność — Trzymamy dla Ciebie miejsce do {time}.", with "Rezygnuję z miejsca"; then
    "Płatność jest już w toku — poczekaj na jej wynik."
  - **Anyone else opening the seat meanwhile:** "Ktoś właśnie dołącza — Jeśli nie zapłaci do {time}, miejsce wróci.
    Sprawdź za chwilę.", with a button "Odśwież".
  - **A join attempt refused meanwhile:** "Ktoś właśnie opłaca to miejsce. Sprawdź za chwilę."
  - **The author:** "Ktoś właśnie opłaca drugie miejsce."
  - **Once paid by someone else:** "Ten mecz ma już komplet — Ktoś był szybszy. Zobacz inne korty, które czekają na
    rywala."

  [CtEmagZ3.js](https://playmore.pl/assets/CtEmagZ3.js) — read 2026-10-20
- **[ABSENT]** A push or notice to the others when a held seat comes back. Searched Playmore's strings for "znów
  wolne", "znowu wolne", "wróciło", "miejsce wraca", "zwolniło się" and "ponownie wolne". The only freed-seat line is
  for open games ("Ktoś się wypisał — w składzie zwolniło się miejsce."), and none is for a held seat returning.
  Read 2026-10-20.
- *Reading:*
  - Against R-RESCUE-50, Playmore tells the others the seat is *held* and *until when*, not that it was taken. Raketa
    says "Someone just took this seat".
  - Like Raketa, Playmore was not found to alert anyone when the seat returns. It asks them to check back.
  - Its hold is 10 minutes, against Raketa's 30.

---

### R-RESCUE-47 — What a player is told when a refund shown as made then fails: Playmore has a state for it; MATCHi sends the player to the club; Playtomic says nothing

- **[POLICY]** *(code)* Playmore, on the page where a player pays their share of a court:
  - a refunded share reads "Rezerwacja została anulowana — Twoja wpłata wróciła do portfela.";
  - a share whose refund failed reads "Rezerwacja została anulowana, ale zwrot Twojej wpłaty się nie powiódł. Napisz do
    nas przez pomoc w aplikacji." (the booking was cancelled, but refunding your payment failed; write to us through
    in-app help). Its state is `refund_failed`.

  Playmore refunds to its own wallet, carried (`gaps-RESCUE.md#playmore-refunds-to-its-wallet-and-keeps-the-service-fee-the-commission-on-a-refund-is-unstated`).
  [D9q4OuNg.js](https://playmore.pl/assets/D9q4OuNg.js) — read 2026-10-20
- **[POLICY]** MATCHi:
  - It only reserves the amount at booking, so on a cancellation "there's usually nothing to 'refund' … the reserved
    amount is simply released back to you by your bank", "within 24 hours".
  - Where the full price was taken, "the venue controls whether a refund is given". "Venues can only issue refunds
    within a limited time window after a booking is paid. If that window has passed, the venue may no longer be able
    to process a refund through MATCHi and will need to arrange reimbursement with you directly".

  [MATCHi: Why haven't I received my refund?](https://matchiplayers.zendesk.com/hc/en-gb/articles/11452630118173)
  (updated 2026-09-30) — read 2026-10-20
- **[POLICY]** Playtomic: "Playtomic processes the refund immediately, however … it can take 2-15 business days to
  receive in your bank"; refunds are listed under *Your payments*.
  [Refunds and when you will receive your money](https://playerhelp.playtomic.com/hc/en-gb/articles/19832175736593)
  (updated 2026-09-10) — read 2026-10-20
- **[ABSENT]** What Playtomic tells a player whose refund failed after it was shown as made. Not in that article, nor
  in the help search results for "refund failed" (31 articles, none on a failed refund). Read 2026-10-20.
- *Reading:* the local rival names a failed refund to the payer in its own words and points to help. Raketa keeps
  saying "refunded" (R-RESCUE-47). Stripe's side of when a refund waits or fails is in
  `stripe-gaps-05.md#r-rescue-47--a-refund-made-before-the-clubs-money-is-available-stripes-refunds-page-says-it-waits-a-support-page-says-only-a-negative-balance-makes-it-wait-and-the-sandbox-nets-it`.

---

### R-RESCUE-35 — Whether Playtomic's priority alert fires for a seat freed in a full match: still not said

- Carried **[POLICY]**: "one priority alert to get push notifications for available matches"; Premium gives unlimited
  alerts "when matches become available"
  (`gaps-RESCUE.md#playtomics-alert-is-for-available-matches`). Complaints that alerts don't fire are in
  `gaps-RESCUE.md#players-say-the-alerts-dont-fire`.
- **[ABSENT]** This round:
  - The notifications article is unchanged (still updated 2026-09-29).
  - Help searches "alert" and "priority alert" return only it, Premium and Club Membership. "waitlist" returns 0.
  - A web search found no Reddit or forum post on an alert for a seat freed in a full match.
  - Apple's review feeds for GB, ES, IT, FR, PL, NL, SE and DE returned no entries today, except one older Spanish
    page with nothing on alerts.

  Read 2026-10-20.

---

### R-RESCUE-9 — How PADO's "Auto-Fill Matches" picks, and whether dealing a seat to the best fits fills faster: still not found

- **[POLICY]** PADO, a Warsaw-born padel platform (beta 1 Mar 2026; CRM launched 15 May 2026):
  - its club page lists "Auto-Fill Matches" as "Find players to fill open spots in games";
  - and "Waitlist" as "Queue for cancelled court slots or tournaments";
  - with no detail and no help or docs link.

  [PADO for clubs](https://pado.app/for-club), [PADO about](https://front.pado.app/about) — read 2026-10-20
- **[ABSENT]** How Auto-Fill chooses whom to offer a spot. Not on PADO's club page, home page or about page. The only
  contact it gives is a personal Telegram account, not a channel. No App Store listing was found. Read 2026-10-20.
- Carried: every other queue orders by time joined or tells everyone at once
  (`gaps-RESCUE.md#nobody-ranks-who-hears-of-a-seat-by-how-even-the-game-would-be`). No measured comparison of the
  two orders exists (`gaps-S-02.md#a-measured-comparison-of-the-two-orders-not-found`).
- **[POLICY]** *(code)* Update to the carried Playmore entry: its whole-waitlist-at-once switch is "Od 10.10.2026 na
  100% we wszystkich klubach z grami", to be made permanent after the read due 23 Oct 2026 "chyba że odczyt każe
  wycofać". [BlUiZcxz.js](https://playmore.pl/assets/BlUiZcxz.js) (entry `open-game-waitlist`) — read 2026-10-20
- The speed comparison can only come from Raketa's own data.

---

### R-RESCUE-8 — How Playtomic's *Find a match* refreshes: still undocumented

- Carried: Playmore's open-games list is read on opening and after the player's own actions; its native iOS pull
  arrived 25 Sep 2026 (`gaps-RESCUE.md#playmore-reads-its-open-games-list-when-the-page-opens-and-after-the-players-own-actions`,
  `gaps-RESCUE.md#playmores-pull-to-refresh`).
  - *(code, 2026-10-20)* Its current open-games loader still has no timer and no return-to-app trigger.
  - A background re-read runs when the date range changes ([pi5P982-.js](https://playmore.pl/assets/pi5P982-.js)).
- **[ABSENT]** Playtomic:
  - Its help search "refresh" still returns one article (Club Wallet), and "update matches" returns none on how a
    list updates.
  - Its web app shows only "Continue in the app" (`competitor-newcomer.md#the-web-app-sends-everyone-to-the-phone-app`).

  Read 2026-10-20.
