# Gaps, payments pass: story S-16 (market)

Written 2026-10-20 by the gaps researcher (payments pass, S-16 market). Eight gaps, each named by its rule ID.
Several were searched earlier today, in `gaps-payments-00.md`, `gaps-payments-01.md`, `gaps-payments-04.md` and
`stripe-gaps-s16.md`. Those are cited, and only new ground was searched.

**New sources in this folder:**

- Monzo's and Wealthsimple's payment *Undo*: Monzo's blog, help and community; Wealthsimple's help centre; FStech;
- W3C's *Understanding 3.3.4* and *4.1.3*, and technique G164;
- Visa Core Rules (18 April 2026): §5.7.2, §5.7.3.6, §5.8.11.1, §7.3.10 and the glossary;
- Stripe's *Set statement descriptors for connected accounts*, for the business details sent with each charge;
- the European Parliament's legislative train on the Digital Fairness Act;
- Playtomic for Android 6.94.0, the XAPK already used in `gaps-payments-00.md`, its open-matches list read with
  Android's `dexdump`.

The code compared is the run's copy at `9ab0ea5b`.

| Gap | Rule | Status |
|---|---|---|
| How players read *Booking in 10 s* | R-FILL-1 | **Partly.** Two banking apps hold a transfer behind a timed *Undo*. Monzo found 10 s too fast in its own testing, and its customers catch a mistake in about 9 s. Their users read the timer two ways. A study of Raketa's words: *not found* |
| Whether a free leave before the cut-off is the "alternative that does not rely on a timer" | R-FILL-1 | **Answered: W3C's test is found.** The test is "the same function" by other means. W3C's technique for purchases is a stated time to cancel. Whether Raketa's leave passes depends on what leaving undoes |
| An *Undo* confirmed in words or aloud | R-FILL-64 | **Partly.** Wealthsimple shows a cancellation confirmation screen. Gmail's web says "Sending undone" (third-party guide). WCAG 4.1.3 asks for such a result to reach a screen reader. A spoken confirmation: *not found* |
| A swipe, *I'm in*, or a price beside it as the control that binds | R-DECK-34, R-FILL-7 | ***Not found*** (carried, searched today). The EU's Digital Fairness Act is still not proposed |
| What a Polish bank app prints beside a pending hold on a direct charge | R-FILL-10 | ***Not found.*** New: Stripe sends the club's contact details with each charge, and says some banks show the name wrongly or not at all |
| Whether Visa's stored-card agreement list applies to terms accepted once on Raketa for every club | R-FILL-11 | **Answered from Visa's text.** The duty is each seller's, the list has no platform variant, and the seller's location and contact are on it. Stripe's view: *not found* |
| How soon a bank drops a full-share check; whether the networks treat it as an "erroneous amount" | R-FILL-59 | **Networks, partly:** Visa's 2026 Core Rules found, Mastercard's 60 minutes carried. **Banks' timing: *not found*** |
| How Playtomic's *Find a match* refreshes | R-DECK-42 | **Answered for Android 6.94.0, from its code.** The list is read when it opens and when the player changes it. There is no pull-to-refresh and no re-read on return |

---

### R-FILL-1 · How players read "Booking in 10 s": two banking apps hold money behind a timed Undo; no study of the words

**Carried.**

- No study or test was found
  (`gaps-payments-00.md#r-fill-1-to-r-fill-3--how-players-read-booking-in-10-s-and-whether-a-ten-second-undo-is-a-time-limit-wcag-221-wants-adjustable-the-standards-own-definition-says-it-is-the-reading-still-needs-players`,
  `gaps-payments-04.md#r-rescue-15--a-ten-second-undo-before-money-moves-what-android-does-for-people-who-need-longer-new-how-players-read-it-still-needs-players`).
- **Superseded:** `gaps-FILL.md#no-payment-app-found-that-waits-behind-an-undo-before-charging` (2026-10-08). Two
  money apps now do, for bank transfers.

**Monzo.**

- **[POLICY]** *You can now undo payments*, published 13 May 2025:
  - "We'll give you 15 seconds to undo a payment by default." A customer can choose "10 seconds, 15 seconds, 30
    seconds or 60 seconds", or turn it on or off under Settings › Privacy & Security.
  - There is "a timer at the top of the payment confirmation screen" and a button, "Undo payment".
  - "The money never leaves your account."
  - [Monzo blog: Undo payments](https://monzo.com/blog/undo-payments) — read 2026-10-20
- **[POLICY]** How Monzo chose the time. Catherine Berda, product manager, 14 May 2025: "We guessed. Sort of." Gmail's
  *Undo Send* was the reference. In staff testing 10 seconds "felt too fast", so it was raised to 15, "to give you just
  a smidge more time".
  [Monzo Community: You can now undo payments](https://community.monzo.com/t/you-can-now-undo-payments/178983) — read 2026-10-20
- **[POLICY]** Monzo's help:
  - "This works for Monzo-to-Monzo payments only."
  - "The timer is set to 15 seconds by default, but you can change it to up to 60 seconds in Settings > Privacy and
    security > Undo payments."
  - [Monzo Help (IE): Troubleshooting payment issues](https://monzo.com/ie/help/using-monzo/help-payment-issues) — read 2026-10-20
- **[DOCS]** (press) FStech, 18 March 2026:
  - 1.6 million payments undone since May 2025, worth £323 million.
  - "When it comes to noticing and stopping a mistaken payment, Monzo said its customers typically do so in nine
    seconds."
  - [FStech: Monzo's Undo Payments tool has prevented £323m of accidental payments](https://fstech.co.uk/fst/Monzo_Undo_Payments_Tool_323m_Accidental_Payments.php) — read 2026-10-20

**Wealthsimple.**

- **[POLICY]** *Undo an Interac e-Transfer*, updated 2026-10-13:
  - "You may see a 15-second countdown after you send an Interac e-Transfer®. During this time, you can tap Undo to
    cancel the transfer before it completes."
  - The countdown and *Undo* sit at the top of the "All set!" screen.
  - "you can adjust or disable the cool down timer in your e-Transfer settings on both the web and app".
  - A "Send Now" button that skips the countdown is being built.
  - [Wealthsimple Help: Undo an Interac e-Transfer](https://help.wealthsimple.com/hc/en-ca/articles/49925420385307-Undo-an-Interac-e-Transfer),
    read through its help-centre API (`/api/v2/help_center/en-ca/articles/49925420385307.json`), because the page
    answers 403 to a direct fetch — read 2026-10-20

**How Monzo's users read the timer.**

- **[COMPLAINT]** Monzo Community, each line one person's account:
  - As money held: "the money doesn't go anywhere - it's held" (Ordog, 30 Jun 2025); "the payment isn't sent until after
    the 15-60 seconds" (stephenjames, same day).
  - As a recall after paying: "'recall' within 10 seconds?" (Revels, 17 Feb 2025, before launch).
  - On the length: "it says 10 seconds. That's probably quite a small window" (Orinoco, 17 Feb 2025, of a pre-launch
    teardown).
  - From a payee's side: someone who "shows you they have made a payment" may undo it, so "check back after 60 seconds
    to make sure they haven't taken it back" (Bhxjoe, 30 Jun 2025).
  - [Undoing Monzo Payments – Beware!](https://community.monzo.com/t/undoing-monzo-payments-beware/180850),
    [Undo Payments](https://community.monzo.com/t/undo-payments/175351) — read 2026-10-20

**Not found.**

- **[ABSENT]** A study or test of how players read "Booking in 10 s": as money about to be held, or as a request being
  sent. Searched:
  - UX research on payment *Undo* timers and delayed send;
  - Monzo's blog, help and community, and Wealthsimple's help, none of which says how people read the timer.

  Read 2026-10-20.

**Code, for comparison.** The toast reads `Booking in ${seconds} s`. A screen reader hears "Booking in 10 seconds. You
can undo it." once, as the toast arrives (`frontend_player/src/features/proposals/components/fillPresentation.ts:37-44`,
`FillProvider.tsx:150-156`). The window is a fixed 10 s (`frontend_player/src/features/proposals/domain/fill.ts:42`).

**Reading.**

- In both money apps the timer comes after the press, on a screen that says the payment is made ("All set!", or Monzo's
  confirmation screen). Both say that nothing has left yet. Their users still read it two ways: held, or taken back.
- Both start at 15 s, and both let the person choose 10 to 60 s or turn the timer off.
- Monzo found 10 s too fast in its own testing. Its customers' typical catch, nine seconds, sits just inside ten.
- Only testing with players can say how Raketa's word, "Booking", reads.

### R-FILL-1 · Whether a free leave before the cut-off is W3C's "alternative that does not rely on a timer": the test is the same function by other means, and W3C's technique for purchases is a stated time to cancel

**Carried.**

- W3C's definition of a time limit, and the mail-toast example
  (`gaps-payments-00.md#r-fill-1-to-r-fill-3--how-players-read-booking-in-10-s-and-whether-a-ten-second-undo-is-a-time-limit-wcag-221-wants-adjustable-the-standards-own-definition-says-it-is-the-reading-still-needs-players`).
- Android's *Time to take action* setting, which Material's Snackbar honours
  (`gaps-payments-04.md#r-rescue-15--a-ten-second-undo-before-money-moves-what-android-does-for-people-who-need-longer-new-how-players-read-it-still-needs-players`).

**What W3C says.**

- **[DOCS]** *Understanding 2.2.1*, the test:
  - "Content that operates on a timer does not need to be time adjustable if there is an alternative that does not
    rely on a timer".
  - In the example, users "are able to identify the arrival of email through other means, such as viewing the Inbox".
  - The limit stands "If the user has no other means of discovering the same information (or performing the same
    function)".
  - The exceptions: "The time limit is essential and extending it would invalidate the activity"; "The time limit is a
    required part of a real-time event".
  - Its money example is a time limit to confirm, not to undo: "An on-line ticket-purchasing site gives the user two
    minutes to confirm a purchase" "before the seats are returned to the general pool".
  - [W3C: Understanding SC 2.2.1 Timing Adjustable (WCAG 2.2)](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html) — read 2026-10-20
- **[DOCS]** SC 3.3.4, *Error Prevention (Legal, Financial, Data)*:
  - "For web pages that cause legal commitments or financial transactions for the user to occur", at least one of
    three holds.
  - "Reversible: Submissions are reversible."
  - "Checked": input errors are found and the user can correct them.
  - "Confirmed: A mechanism is available for reviewing, confirming, and correcting information before finalizing the
    submission."
  - Its Intent: "Providing the ability to reverse actions allows users to correct a mistake that could result in
    serious consequences."
  - Sufficient for purchases: G164, G98 and G155.
  - [W3C: Understanding SC 3.3.4](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html) — read 2026-10-20
- **[DOCS]** Technique G164, "Providing a stated time within which an online request (or transaction) may be amended or
  canceled by the user after making the request". It relates to 3.3.4.
  - Its aim is to let users "recover from errors made when placing an order".
  - The site states how long the window lasts and how to cancel.
  - Online cancelling is preferred, so that cancelling is as easy as submitting. Any other way must be equally
    accessible.
  - Example 1: a retailer allows cancelling for 24 hours, explains it on the site, and repeats it in the emailed
    receipt.
  - The test checks two things: the page states the time period, and it says how to cancel.
  - [W3C: Technique G164](https://www.w3.org/WAI/WCAG22/Techniques/general/G164) — read 2026-10-20

**The market's route.**

- **[POLICY]** Monzo and Wealthsimple let the person lengthen the *Undo* (to 30 or 60 s) or turn it off (above).
  Android's own Snackbar stretches to the user's chosen time (carried).

**Not found.**

- **[ABSENT]** A W3C note, an EN 301 549 note or a published audit applying 2.2.1's "alternative" to a booking or
  payment *Undo*. Searched W3C's *Understanding* 2.2.1 and 3.3.4 and technique G164. Read 2026-10-20.

**What the leave is, in Raketa's own terms.** "Leave before the cut-off and nothing is taken."
(`gaps-payments-01.md#r-fill-11-r-fill-60--the-terms-in-force-since-2026-10-10-say-held-at-the-fill-checked-when-a-hold-wouldnt-last-held-four-days-before-the-cut-off-taken-at-the-cut-off`).

**Reading.**

- W3C's test is whether the person can do "the same function" without the timer. A free leave before the club's
  cut-off is the nearest thing Raketa has. It is G164's stated time to cancel, the sufficient technique for 3.3.4 on a
  purchase.
- It counts as 2.2.1's alternative only if it undoes the same thing, at no cost, just as easily:
  - Before the ten seconds end, *Undo* leaves no trace.
  - A leave comes after the yes was sent. If that yes filled the game, it also comes after the court was booked, the
    shares were held, and the others were told it's a game.
  - For the leaver, the result can be the same: nothing taken, the hold let go. What the others saw cannot be taken
    back.
- The safe reading is the market's: let the time be lengthened or turned off, as Android's Snackbar and both money
  apps do.

### R-FILL-64 · An Undo confirmed in words after the timer: Wealthsimple shows a confirmation screen, Gmail's web says "Sending undone"; none documents it aloud

**In words.**

- **[POLICY]** Wealthsimple:
  - "If you tap Undo before the timer expires, the transfer is cancelled immediately. You'll see a cancellation
    confirmation screen, and the money is returned to your account."
  - Its step 5: "Review the cancellation confirmation".
  - [Wealthsimple Help: Undo an Interac e-Transfer](https://help.wealthsimple.com/hc/en-ca/articles/49925420385307-Undo-an-Interac-e-Transfer) — read 2026-10-20
- **[DOCS]** (a third-party how-to, 14 January 2021) Gmail on the web: "You'll see a Sending undone confirmation on your
  screen." On mobile it says only "You'll see a message appear confirming your email cancelation."
  [Online Tech Tips: How to Unsend an Email in Gmail](https://www.online-tech-tips.com/how-to-unsend-an-email-in-gmail/) — read 2026-10-20
- **[ABSENT]** Google's and Monzo's own words after the press:
  - Google's Android help describes only "Sent" and *Undo*, and nothing after the press
    ([Google: Unsend Gmail messages, Android](https://support.google.com/mail/answer/2819488?hl=en&co=GENIE.Platform%3DAndroid)).
  - Monzo says only "we stop the payment from being sent" and "The money never leaves your account", with no words on
    the screen (blog, help and community above).
  - Read 2026-10-20.

**Aloud.**

- **[DOCS]** WCAG 2.2, SC 4.1.3 *Status Messages*:
  - "status messages can be programmatically determined" "such that they can be presented to the user by assistive
    technologies without receiving focus."
  - A status message is a "change in content that is not a change of context, and that provides information to the
    user" "on the success or results of an action".
  - Example: a photo app shows "Saved in 'Wedding' album", "which is also read by a screen reader".
  - [W3C: Understanding SC 4.1.3 Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) — read 2026-10-20
- **[DOCS]** React Native 0.87, `AccessibilityInfo`:
  - `announceForAccessibility`: "Post a string to be announced by the screen reader".
  - `announceForAccessibilityWithOptions` can queue an announcement behind current speech on iOS.
  - [React Native docs: AccessibilityInfo](https://reactnative.dev/docs/accessibilityinfo) — read 2026-10-20
- **[ABSENT]** Any app's document or screenshot of a timed *Undo* confirmed aloud with VoiceOver or TalkBack. Searched:
  - Monzo's blog, help and community, and Wealthsimple's help;
  - Google's Gmail help, and Apple's Mail guide, which gives only the window and the button;
  - Material snackbar guidance.

  Read 2026-10-20.

**Code, for comparison.**

- Pressing *Undo* only removes the count (`onAction={() => setCounting(null)}`,
  `frontend_player/src/features/proposals/components/FillProvider.tsx:310-317`).
- No words appear and nothing is announced. `UndoToast` leaves announcing to its caller
  (`frontend_player/src/shared/ui/UndoToast.tsx:25`, `:122-124`).
- The button is spoken "Undo the booking" (`fillCopy.ts:20-22`).
- The start is announced: "Booking in 10 seconds. You can undo it." (`fillPresentation.ts:42-43`, `FillProvider.tsx:155`).

**Reading.**

- Wealthsimple's confirmation screen is the market's one documented case of an *Undo* confirmed in words.
- WCAG 4.1.3 makes such a result a status message that a screen reader must hear without moving focus.
- A toast that simply disappears leaves a screen-reader user to read the undo from silence.

### R-DECK-34, R-FILL-7 · A swipe, "I'm in" or a price beside it as the control that binds a consumer to pay: still no authority

**Carried, searched today.**

- No ruling or lawyer's opinion on a swipe or a priced "I'm in". In 2026 German appeal courts split on a non-compliant
  "Bestellen" (KG 1 U 25/25, appeal to the BGH allowed). No Polish 2026 decision on the order button
  (`gaps-payments-00.md#r-fill-1-r-fill-7-r-fill-26-r-fill-58--a-ruling-or-a-lawyers-opinion-on-a-swipe-or-on-im-in--40-zł-as-the-order-control-still-none-german-appeal-courts-split-in-2026-on-what-a-bad-button-costs`).
- Earlier rounds:
  - `gaps-FILL.md#no-authority-on-a-swipe-or-a-priced-im-in-as-the-order-control`;
  - `gaps-DECK.md#no-polish-ruling-or-uokik-statement-on-a-swipe-dołączam-or-a-price-on-the-button`;
  - `gaps-SWIPE.md#still-no-authority-on-a-swipe-the-dutch-supreme-court-rejects-generic-order-labels`.

**New this round.**

- **[LAW]** (status) The EU's Digital Fairness Act has not been proposed. It is the expected home for new rules on
  interface design.
  - The European Parliament's legislative train lists it as "Announced", with no COM number, at the Commission work
    programme's indicative "Q4 2026".
  - The page names "deceptive or addictive interface design" and "dark patterns". It says nothing of order buttons or
    confirming a payment duty.
  - [European Parliament: Legislative Train, Digital Fairness Act](https://www.europarl.europa.eu/legislative-train/theme-a-new-plan-for-europe-s-sustainable-prosperity-and-competitiveness/file-digital-fairness-act),
    information updated 20/09/2026 — read 2026-10-20

**Not found.**

- **[ABSENT]** Any authority, Polish, EU or other, on a swipe, a control naming joining, or a price printed on or
  beside the control. This round's search added only the Digital Fairness Act's status. Read 2026-10-20.

**Reading.** Unchanged: a Polish lawyer's opinion is still the only way to settle it before a court or UOKiK does.

### R-FILL-10 · The name a Polish bank app prints beside a pending hold made as a direct charge on the club's account: still not found

**Carried.**

- Visa requires the same merchant name on the hold as on the payment. A direct charge carries the club's descriptor
  (`gaps-S-01A-hold.md#visa-requires-the-same-merchant-name-on-the-hold-as-on-the-payment`).
- PKO BP marks a hold "Blokada" with a padlock. Banks map a friendlier name themselves, and Stripe can't control it
  (`gaps-payments-00.md#r-platform-7-r-platform-65--how-soon-a-released-hold-leaves-a-polish-bank-app-and-the-name-beside-it-the-network-rule-is-found-the-banks-practice-is-not`).
- PKO uses Visa's name-and-logo scheme. Whether mBank, ING, Pekao or Erste use Visa's or Mastercard's is unknown
  (`gaps-payments-03.md#r-pay-34--what-mbank-ing-pekao-and-erste-formerly-santander-show-in-place-of-the-clubs-statement-name`).
- No bank's row for a pending card hold is described
  (`gaps-payments-01.md#r-fill-13---the-name-beside-a-pending-card-hold-still-not-found-for-any-of-the-five-banks`).
- From the Stripe lens, today:
  - the test club's charges read `calculated_statement_descriptor: "ROBER CLUB"`, and Raketa sends no suffix;
  - whether a suffix sent with the hold shows on the pending line is unknown
  - (`stripe-gaps-s16.md#8--r-fill-11--statement_descriptor_suffix-on-a-direct-charge-on-an-accounts-v2-club-with-its-own-full-dashboard`).

**New this round.**

- **[DOCS]** Stripe sends more than the name with each charge:
  - "Along with a statement descriptor, additional information about the business is sent to display on the
    customer's statement (for example, address, email, phone, and URL)."
  - "The additional information defaults to the support properties of the account's business_profile. If a support
    field isn't provided, the platform support field is used."
  - On a direct charge, "The customer's statement uses the connected account's static component".
  - [Stripe: Set statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors?locale=en-GB) — read 2026-10-20
- **[DOCS]** Stripe, on how banks show it:
  - "Most banks display this information consistently, but some might display it incorrectly or not at all."
  - Stripe's only line on what shows before a take concerns Japanese descriptors. They are "sent to issuers at time of
    payment capture", and in the meantime Visa and Mastercard cardholders may see "The English-language statement
    descriptor".
  - [Stripe: Statement descriptors](https://docs.stripe.com/get-started/account/statement-descriptors?locale=en-GB) — read 2026-10-20

**Not found.**

- **[ABSENT]** A Polish bank's pending-hold row.
  - This round searched in Polish: "blokada" with "nazwa sprzedawcy" or "nazwa akceptanta", and "transakcja
    oczekująca". It found only mBank's pages on blocking a card.
  - What would answer it is unchanged: a live hold on a card from each bank, with the app's row captured.
  - Read 2026-10-20.

**Reading.**

- On a Visa card the pending line carries the same merchant data as the payment. On a direct charge that is the club's
  descriptor ("ROBER CLUB" on the test club). Where a bank shows them, it is also the club's support contacts, or
  Raketa's where the club set none.
- Whether that raw name or a name the bank maps shows is each bank's own choice. Raketa's name appears only through
  the contacts Stripe falls back to.

### R-FILL-11 · Visa's stored-card agreement and terms a player accepts once on Raketa for every club: the duty is each seller's, and Visa has no platform variant

**Carried.**

- Visa's list and its exception for unscheduled charges, which ask for the event that prompts a charge
  (`gaps-payments-01.md#r-fill-11-r-fill-60--visa-for-unscheduled-charges-the-terms-name-the-event-that-prompts-them-not-a-frequency`).
- The terms' words, which name the seller as "the club it is played at"
  (`gaps-payments-01.md#r-fill-11-r-fill-60--the-terms-in-force-since-2026-10-10-say-held-at-the-fill-checked-when-a-hold-wouldnt-last-held-four-days-before-the-cut-off-taken-at-the-cut-off`).
- Stripe: sharing a card with a club shares the customer's permission
  (`stripe-saving-cards.md#sharing-a-card-with-a-connected-account-shares-the-customers-permission`).

**Who Visa's list binds.**

- **[POLICY]** Visa Core Rules §5.8.11.1 and Table 5-20 (ID# 0029267, last updated Oct 2025), pp. 458–460:
  - "A Merchant or Digital Wallet Operator (DWO) that processes Partial Payments, Advance Payments, and Transactions
    using a Stored Credential must comply with Table 5-20".
  - "Before a Merchant or DWO either stores a Payment Credential for a future Transaction or completes an Advance
    Payment or Partial Payment, it must obtain the Cardholder's express informed consent to an agreement that contains
    all of the following".
  - Under "Information about the Merchant": "The location of the Merchant Outlet" and "Address, email address, and
    phone number to use to contact the Merchant in relation to the Transactions".
  - "The Merchant must retain this information for the duration of the agreement and provide it to the Cardholder or
    Issuer upon written request."
- **[POLICY]** Same section, the exceptions. The table does not apply "when the Merchant or DWO uses the Stored
  Credential for a single Transaction or a single purchase":
  - "A No-Show Transaction";
  - "A Transaction involving an amended amount or a delayed charge";
  - an incremental authorisation, a new authorisation for the same transaction, and a resubmission after a decline.
- **[POLICY]** Glossary:
  - A Stored Credential is information "stored by either: A Merchant or its agent, a Payment Facilitator, or a Digital
    Wallet Operator to process future Transactions" (ID# 0029547).
  - A Digital Wallet Operator "operates a Staged Digital Wallet or Stored Value Digital Wallet" (ID# 0029530).
  - A Marketplace "brings together Cardholders and retailers on an electronic commerce website or mobile application
    and processes Transactions and receives Settlement on behalf of those retailers" (ID# 0030075).
  - A Merchant Outlet is "The Merchant location at which a Transaction is completed", for example an "Electronic
    Commerce Merchant's website" (ID# 0024842).
- [Visa Core Rules and Visa Product and Service Rules, 18 April 2026](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf),
  pp. 458–460, 828–897 — read 2026-10-20

**Not found.**

- **[ABSENT]** A Visa rule that lets one platform agreement stand for several merchants, or that puts the platform in
  place of the merchant under "Information about the Merchant". Searched:
  - the Core Rules for "Marketplace", "Payment Facilitator", "on behalf of" and "multiple merchants" around the
    stored-credential rules;
  - Stripe's *Share payment methods across accounts*, which has no word on consent
    ([Stripe](https://docs.stripe.com/connect/direct-charges-multiple-accounts)).

  Whether Stripe, as the clubs' acquirer, accepts Raketa's one agreement is a question for Stripe support. Read
  2026-10-20.

**Reading.**

- On a direct charge the club is the seller and Raketa keeps the card for it. By Visa's wording Raketa stores it as
  the clubs' agent, and the agreement is each club's. Raketa is not a Visa Marketplace, because the money settles to
  the club and not through Raketa. It runs no wallet either.
- The whole list applies. Only "timing and frequency" gives way, to the event, for unscheduled charges.
- The merchant items, the club's location and its contact details, can't be filled when the card is saved, because the
  club isn't known yet. "The club it is played at" names the event, not the merchant.
- The exceptions cover one purchase, such as a hotel's no-show charge. Raketa uses the card for every future game at
  any club, so they don't apply.
- Stripe's word that permission travels with the copy answers the bank's check (SCA). It doesn't answer what Visa
  wants the agreement to say.

### R-FILL-59 · A full-share check let go at once: Visa's own 2026 rules on checking a card, and the banks' timing still unpublished

**Carried.**

- How soon each Polish bank's app drops a cancelled hold is published by none of them
  (`gaps-payments-01.md#r-fill-13---how-soon-each-of-the-five-banks-drops-a-cancelled-hold-still-not-published`).
- Mastercard binds an issuer to release a hold "within 60 minutes of matching the reversal message". Visa says
  "upon receipt", with no time
  (`gaps-payments-00.md#r-platform-7-r-platform-65--how-soon-a-released-hold-leaves-a-polish-bank-app-and-the-name-beside-it-the-network-rule-is-found-the-banks-practice-is-not`).
- Visa's 2019 notice asks merchants to "use account verification instead of authorizations for erroneous amounts"
  (`gaps-payments-01.md#r-leave-44--visa-wants-a-zero-amount-account-verification-not-a-small-amount-to-check-a-card-being-stored`).
- Stripe says "Card networks may also restrict 1 USD authorizations you don't intend to capture".
- S-16's two checks were let go within 1 to 3 s, with no fee booked
  (`stripe-gaps-s16.md#2--r-fill-59--a-full-share-authorisation-let-go-at-once-only-to-check-the-money`).

**Visa's 2026 rules, new this round.** All from
[Visa Core Rules, 18 April 2026](https://usa.visa.com/content/dam/VCOM/download/about-visa/visa-rules-public.pdf),
read 2026-10-20.

- **[POLICY]** §5.7.2.1 *Account Verification Requirements* (ID# 0030934, last updated Oct 2022), p. 410: "A Merchant
  that chooses to verify the validity of an account must use an Account Verification. An Account Verification must
  both: Be for a currency unit of zero; Not be used to initiate a purchase Transaction".
- **[POLICY]** §5.7.2.2 *Authorization Requirements* (ID# 0030933, last updated Apr 2026), p. 410. "An Authorization
  Request must be one of the following":
  - "An Authorization for a final Transaction amount";
  - "An Estimated Authorization";
  - "An extended Authorization";
  - "An Incremental Authorization";
  - "An initial Authorization for certain MCCs";
  - an initial authorisation at an automated fuel dispenser.
- **[POLICY]** §7.3.10.2, the acquirer's duties (ID# 0031048, last updated Apr 2026), p. 549: "Ensure that its Merchant
  uses Account Verification when storing a Payment Credential or validating an account separately from a purchase".
- **[POLICY]** §7.3.10.1, the bank's answer to such a check (ID# 0031047), p. 548: "00 – Approval (when the Account has
  balance greater than zero)", or "85 – No reason to decline (when the Issuer has not checked the Account balance)".
- **[POLICY]** §5.7.3.6 and Table 5-14 (ID# 0025597, last updated Oct 2023), pp. 418–419. For an approval whose
  transaction is not completed, the merchant reverses the "Authorized amount or amounts" "Within 24 hours of the
  earlier of either":
  - "When the Transaction was cancelled or the Cardholder decided to pay by other means";
  - "The end of the Approval Response validity period".

**Not found.**

- **[ABSENT]** Each of these is still missing:
  - a Visa or Mastercard ruling, or a fee, aimed at a full-amount authorisation made only to check the money and let go
    at once;
  - Mastercard's Europe rule on checking a card (carried);
  - a Polish bank's time to drop such a check.

  Read 2026-10-20.

**Reading.**

- Visa's 2026 rules are firmer than its 2019 notice. Checking "the validity of an account" must be a zero-amount
  Account Verification that starts no purchase, and every authorisation must be one of six kinds.
- A full-share authorisation made only to check, and let go at once, is none of the six in substance. It is a check
  made with an amount.
- Raketa's check asks more than validity: whether the share's money is there. A zero-amount check can't answer that,
  because the bank says only "balance greater than zero", or nothing.
- Visa's text never names a check of funds. So the nearest rule is against it, but it is not a ruling on it.
- The reversal itself sits well inside Visa's 24 hours, since the check is let go within seconds (measured). On
  Mastercard, the hold must then leave within 60 minutes of a matching reversal. When the bank's app shows it gone is
  still unpublished.

### R-DECK-42 · How Playtomic's *Find a match* list refreshes: read when it opens and when the player changes it, with no pull and no re-read on return (Android 6.94.0)

**Carried.**

- The help centre is silent, and one player says the list "needs killing"
  (`gaps-DECK.md#playtomic-does-not-document-how-its-match-list-refreshes-one-player-says-it-needs-a-restart`).
- Still undocumented this morning
  (`gaps-payments-04.md#r-rescue-8--how-playtomics-find-a-match-refreshes-still-undocumented`).
- Playtomic's Home re-reads on every return (`ON_RESUME`). A match's own screen shows the card's copy at once,
  re-reads by id each time it is shown, and keeps the shown match when a read fails
  (`gaps-payments-00.md#r-platform-50-r-platform-51--playtomics-home-and-match-screen-a-spinner-first-a-re-read-on-every-return-and-offline-the-game-vanishes-from-home`).

**What the code shows.**

- **[POLICY]** *(code)* Playtomic for Android 6.94.0 (`com.playtomic`, versionCode 37947), read with Android's
  `dexdump` (build-tools 36.0.0) on 2026-10-20:
  - **The list.** The open-matches list is the match wizard's "marketplace": `MatchWizardMarketplaceFragment` and
    `MatchWizardMarketplacePresenter`. Its strings are `match_wizard_marketplace_empty_matches_*` and
    `open_matches_marketplace_*`.
  - **No refresh action.** The list has 30 user actions (`MatchWizardMarketplaceAction$…`), and none is a refresh or
    a reload. They cover:
    - filters, dates, times, sport and location;
    - list or map;
    - four kinds of load-more (`LoadMoreFlexible`, `LoadMoreMatchesForYourLevel`, `LoadMoreProposals`,
      `LoadMoreRequestToJoin`);
    - opening or selecting a match, subscribing to alerts, and creating a match.
  - **No pull-to-refresh on it.** The app ships Android's `SwipeRefreshLayout` and Compose's pull-refresh. Only two
    screens use them: the social feed (`social/feed/feedList`) and the profile's groups grid
    (`ProfileGroupsGridViewKt`).
  - **No re-read on return.** The screen's class chain (`MatchWizardMarketplaceFragment` → `ComposeFragment` →
    `MVIFragment` → `MozartFragment`) overrides no `onResume` or `onStart`. The list is read through the presenter's
    `open` when the screen is built, and again when results are re-filtered (`ResultsUpdated`).
  - **No timer.** The screen's bytecode references no timer or delay class.
- **[POLICY]** The App Store notes for 6.94.1 (15 October 2026) mention only how dates and players are picked for
  experiences, and bug fixes. [App Store lookup](https://itunes.apple.com/lookup?id=1242321076&country=pl) — read 2026-10-20

**Not found.**

- **[ABSENT]** The iPhone build was not read, and the app was not run, so this is a static read only.
- Whether a refresh keeps the match being read doesn't arise: nothing refreshes the list. Opening a match keeps the
  match shown, even when its re-read fails (carried).

**Reading.**

- A Playtomic player sees matches that are new, or that have filled, only by opening the list again or changing a
  filter.
- Nothing redraws the list under them, so the match they are reading stays where it is.
- Playmore's open-games page behaves the same way
  (`gaps-DECK.md#playmores-open-games-page-does-not-re-read-on-return-and-has-no-pull-to-refresh`).
