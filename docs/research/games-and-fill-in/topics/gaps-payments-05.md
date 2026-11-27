# Payments gaps 05 — RESCUE, REQUEST and CLUBBOOK (market)

Answers to the market gaps the payments-pass Moderator left on **R-RESCUE-1, -5, -11, -19, -23**,
**R-REQUEST-57, -58, -59, -60, -61** and **R-CLUBBOOK-14, -17, -32, -37, -44, -45**. Written 2026-10-20. Each gap
is a `###` heading naming its rule ID. Answers already in this folder, from the earlier gaps rounds and from today's
sibling files (`gaps-payments-02.md` to `-04.md`), are cited by anchor, not repeated.

**Sources this round.**

- **Playtomic Manager's own text catalogs**, `https://manager.playtomic.io/locales/en/<namespace>.json`. 24
  namespaces are served, among them `schedule`, `reservations`, `transactions`, `bookings`, `club_payments`,
  `refunds`, `integrations` and `billing`. 40 more names were tried and refused (403).
- **Playtomic's club help centre**, through its Zendesk API: 15 searches and 15 articles (en-gb).
- **Playmore's club panel**: 499 script files served to the sign-in page of `https://manager.playmore.pl/`, with its
  Polish catalogs.
- **Playmore's player web app**: 1,490 script files from `https://playmore.pl/`, with its feature-flag registry
  (`BlUiZcxz.js`).
- **tenis4U's club panel**: `https://panel.tenis4u.pl/main.bf9c0f8a156c883a.js`.
- **Kraków clubs' terms**: KS Grzegórzecki (in force from 30 Aug 2026), Miazga, Atras, Squash4You and Garden
  Padel. Fame Sport's rules PDF now answers 404.
- **kluby.org**: its changelogs, feature list and help page, and its help videos' titles.
- **Google's Google Pay API documents**, and Recurly's Google Pay page.
- **Rakieta's code** in the copy at `9ab0ea5b`, for R-RESCUE-11 only.

Every quoted string and code line from the three products, and the terms quoted below, is saved in
[`../shots/gaps-payments-05-playtomic-playmore-tenis4u-2026-10-20.txt`](../shots/gaps-payments-05-playtomic-playmore-tenis4u-2026-10-20.txt).

Kinds:

- `[POLICY]`: a company's rule, its help page, or the text its own app or panel ships.
- `[DOCS]`: a provider's document.
- `[MEASURED]`: read from the product as it is served (its code), with the extract saved.
- `[ABSENT]`: looked for and not found, with where.

Lines marked *reading* are inference, not sources.

| Rule | Status |
|---|---|
| R-RESCUE-23, R-RESCUE-1 | **Partly**. Playmore's "Komplet" push goes out in every club. Its league server sends it, and whether a seat taken again sends it a second time is *not found*. Playmore's next answer for groups is a ready WhatsApp text, in a pilot at 0 %. Kraków group posts are still unreadable |
| R-RESCUE-19 | **Answered**. Every Playmore booking and payment request carries an idempotency key, the open-game join included. The key is new for each press and reused only for that press's own retries |
| R-RESCUE-5 | *Not found*. Today's R-LEAVE-14 answer is cited, with two more Kraków rules |
| R-RESCUE-11 | **Answered from the code**. There is no address on the rescue, and a club has none to show |
| R-REQUEST-60 | **Answered**. Playtomic marks the booking owner's fee "Authorized", with the total in a tooltip. Every other player's line shows a "Mark as paid" button or "Paid" |
| R-REQUEST-61 | **Answered**. No rival's cancel dialog names a card fee. Playtomic credits its own fee back on a refunded booking. Playmore names the commission it keeps only in a report |
| R-REQUEST-57, R-REQUEST-59 | **Partly**. Google lets a merchant keep either kind of Google Pay card for later charges of varying amounts. It has no rule written for an unscheduled charge, and says nothing about a new phone. A billing platform says the device token dies with the card's removal |
| R-REQUEST-58 | *Still not confirmed*. The changelog still names only the notice of a cancelled booking. A second help chapter on notices exists, but its words could not be read |
| R-CLUBBOOK-44 | **Answered**, today for R-PAY-53. Playtomic Manager's catalogs add no word for a refund that is waiting or failed |
| R-CLUBBOOK-17 | *Not found*: the words of Playtomic's change email |
| R-CLUBBOOK-32 | **Partly**. Playmore saves a block court by court, through the same call that refuses a taken hour, and lists the failures. tenis4U leaves it to its server. Playtomic's Blocking is a one-court beta. Nobody lists the bookings in the way |
| R-CLUBBOOK-37 | *Not found*: no rival sends players back to a closed hour. Playmore's "play again" leaves cancelled bookings out |
| R-CLUBBOOK-45 | **Partly**. No Kraków rule reprices a game the club moves. KSG keeps paid services as they were. Miazga makes a player's change of hour a new booking |
| R-CLUBBOOK-14 | *Not found* again. The earlier answers on R-CLUBMONEY-9 and R-CLUBMONEY-5/-8 are cited |

---

### R-RESCUE-23, R-RESCUE-1 — Playmore's "Komplet" push is its league server's to send; whether a retaken seat sends it again is not found

**The push.**

- **[POLICY]** Playmore's flag registry (its team's notes) has an active entry, `open-game-filled-moment`:
  - a tap on the league's push "Komplet w Waszej grze" or "Mecz potwierdzony" opens a sheet for the squad, with
    "Kontakty do składu", "Dodaj do kalendarza" and "Zaproś na kolejną";
  - "Bez payloadu klubów: push „Komplet” (PLA-4822) wychodzi we wszystkich klubach od 25.09";
  - the sheet has been "od 26.09.2026 na 100% (wszystkie kluby)";
  - a full game's card shows "Kontakty do składu" "od `filledAt`".

  `BlUiZcxz.js`, extract §C — read 2026-10-20
- **[MEASURED]** *(code)* The app treats a game as filled when it is confirmed, or when it is open and has a
  `filledAt` time, which is one timestamp per game. The squad's contacts sheet has three headings: "Gra
  potwierdzona.", "Skład jest pełny." and "Ktoś się wypisał — w składzie zwolniło się miejsce."
  `BXfZGVTf.js`, `C9ye8j_u.js`, extract §C — read 2026-10-20
- **[ABSENT]** Whether the league server sends "Komplet w Waszej grze" again when someone takes a seat freed in a
  full game. The push is written on Playmore's league server, which the app does not ship, and the registry says
  nothing of a second push. Searched the registry and the 1,490 app files for "ponown", "drugi", "dosadz", "znów"
  and "refill". — read 2026-10-20

**Telling the group.**

- **[POLICY]** Playmore's newest answer is the flag `whatsapp-group-moments`, "Daj znać grupie", added 2026-10-11.
  - After an action, the app opens a WhatsApp sheet with ready text for the squad. Two of its moments matter here:
    - a seat freed: "Zwolniło się miejsce. Napisz do grupy, może ktoś wskoczy." — text "Nie dam rady zagrać:
      {when}, {venue}, {court}. Zwolniło się miejsce — kto wskakuje?";
    - the squad full: "Macie komplet. Daj znać grupie, że gracie." — text "Mamy komplet ✅ Gramy: {when}, {venue}.
      Do zobaczenia na korcie!".
  - With the squad's group linked, the sheet offers "Otwórz grupę", then "Wyślij tekst".
  - The flag was set up "na 0% z payloadem pilota {"venueIds":[140,136,85,182,18]}". It stays at 0 % until the
    player app is released.

  `BlUiZcxz.js`, `CYtOXQ7t.js`, `C9ye8j_u.js`, `hyhAQNIM.js`, extract §C — read 2026-10-20
- **[ABSENT]** A Kraków group's own post. A web search on 2026-10-20 for "szukam czwartego", "brakuje jednej
  osoby" and "zwolniło się miejsce" with padel and Kraków found only news of the 2023 European Games. Facebook
  groups need a login (carried: `gaps-RESCUE.md#still-unreadable`,
  `gaps-S-02.md#kraków-group-posts-still-unreadable`).

*Reading:* at Playmore the people on a game learn the squad is full again from a push the league server sends.
Whether that push repeats after a refill is unknown. Playmore's next step leaves it to a member's own WhatsApp post,
which the app writes for them. In a Kraków group, the same post is typed by hand.

---

### R-RESCUE-19 — Playmore sends an idempotency key with every booking and payment, the open-game join included: a new one per press, the same one on its own retries

- **[MEASURED]** *(code)* Playmore's posting helper:
  - It adds `idempotency_key` to the request body: the caller's key, or else a new random UUID.
  - It repeats the same request, with the same key, while the server answers `REQUEST_IN_PROGRESS`: every 3 s, up
    to 45 times.
  - On a 429 it waits 1,2 s and tries twice more.

  `CAjrtWH8.js`, extract §C — read 2026-10-20
- **[MEASURED]** *(code)* The player app sends these through that helper: `/reservation`, `/reservation/batch`,
  `/payment/create`, `/payment/create_auth`, `/payment/reservation/bulk`, `/payment/settlements/bulk`,
  `/split/{id}/pay`, `/user_wallet/topup`, `/user_venue_carnet` and `/course_enrollment/{id}`.
  - An open-game join is paid through `createReservation`, which posts to `/reservation`.
  - It passes no key of its own, so the helper makes a new one on each call.

  `DKpNMi8e.js`, `CXX7vfQ6.js` — read 2026-10-20
- **[POLICY]** Where the same form can be sent twice, Playmore keeps one key per form. This covers standing-slot
  requests, accepting a standing slot (`standing_slot_accept:{id}`) and resigning from a series. Reusing a key
  that no longer fits reads "Coś się zmieniło w formularzu. Spróbuj jeszcze raz."
  `Gy6OhlNH.js`, `DIT633y4.js`, `BeMB0mtt.js`, `DyQUCw1g.js` — read 2026-10-20
- Carried: Playmore hides "pay" while a payment is processing and says "Nie płać ponownie"
  (`gaps-RESCUE.md#playmore-hides-pay-while-a-payment-is-processing-and-says-do-not-pay-again`).

*Reading:* Playmore's key stops a lost answer from booking twice. It does not stop a second press, because a second
press of the join gets a new key. What stops it is the hidden button, and whatever the server checks.

---

### R-RESCUE-5 — Whether a Kraków desk lets a late canceller book the same hour back himself: still not found

- Answered today with the same sources:
  `gaps-payments-02.md#r-leave-14--whether-a-kraków-club-lets-a-late-canceller-book-the-same-hour-back-not-found`.
- **[POLICY]** KS Grzegórzecki (Kraków, rules in force from 30 Aug 2026), II.5:
  - a one-off booking is given up at least 24 h ahead;
  - "W przypadku późniejszego odwołania albo niestawienia się na kort osoba dokonująca rezerwacji jest zobowiązana
    do uiszczenia pełnej opłaty za wstęp na kort."

  It waives nothing, neither for another client nor for the canceller.
  [KSG regulamin](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf) — read 2026-10-20
- **[POLICY]** Miazga:
  - "Zmiana terminu gry jest równoznaczna z anulowaniem dotychczasowej gry i rezerwacją nowego terminu";
  - the late fee is forgiven "jeżeli kort zostanie zarezerwowany i opłacony przez innego gracza".

  [Miazga regulamin](https://www.miazgasquash.pl/regulamin/) — read 2026-10-20
- **[ABSENT]** A rule letting the canceller book the hour back himself. Searched KSG, Miazga, Atras, Squash4You
  and Garden Padel for "ponownie", "ten sam", "sam" and "przywr". Fame Sport's PDF and its `/regulamin/` page now
  answer 404. — read 2026-10-20

*Reading:* in Kraków a late fee is forgiven only when someone else buys the hour. The canceller buying it back
himself is a case no rule names.

---

### R-RESCUE-11 — The rescue shows the club's name, the court and the distance, never an address; the club has no street address to show

- *(code, `9ab0ea5b`)* The rescue, as a member it is offered to sees it, is built in
  `ReadBookingDetails._from_outside`. It carries the club's name and the distance
  (`backend/app/modules/proposals/application/booking_details.py:188-232`, the two fields at `:231-232`). The read
  has no address field (`:100-116`).
- A club's details are its name, district, city, sports and a map point. There is no street and no postcode
  (`backend/app/modules/clubs/domain/value_objects.py:136-147`).
- The phone's WHERE line shows the club's name, with the court, its kind and the distance beside it:
  - `frontend_player/src/features/proposals/components/BookedGameScreen.tsx:218-224`;
  - `homePresentation.ts:279-288`;
  - `deckPresentation.ts:296-298`.
- Carried market:
  - **[LAW]** the seller's identity and address must be shown before the player is bound
    (`local-market.md#what-the-player-must-see-before-being-bound`);
  - Playmore's payment page names the "Obiekt sportowy" by its trade name only
    (`gaps-RESCUE.md#a-code-question-with-the-market-beside-it`).

*Reading:* the gap is not the rescue screen's alone. Rakieta holds no club address that any screen could show.

---

### R-REQUEST-60 — Playtomic marks only the booking owner's fee "Authorized"; every other player's line shows a "Mark as paid" button or "Paid"

- **[POLICY]** "In Playtomic Manager, you'll see this as Authorized on the booking owner fee (Schedule → booking
  details)." This applies to New Billing Model clubs in Italy, the United Kingdom, Portugal and Norway.
  [How a pre-authorization works](https://helpmanager.playtomic.com/hc/en-gb/articles/20534487294097-How-a-pre-authorization-works)
  (updated 2026-10-19) — read 2026-10-20
- **[POLICY]** The three statuses on a split-payment booking:
  - "Authorized: only ever shown on the booking owner's fee. It means the full booking amount is on hold on the
    owner's card as a guarantee, nothing has been charged yet. Hover the tooltip (ℹ️) next to it to see that total
    amount";
  - "Mark as paid: this participant hasn't paid yet. It's a button, not a status";
  - "Paid: this participant has already paid, with a tag next to it showing how".

  Two hours after the match, an unpaid share is taken from the hold, and it then "shows as Paid Online with a
  tooltip" saying the owner paid it.
  [Split payment bookings: statuses and charges in Playtomic Manager](https://helpmanager.playtomic.com/hc/en-gb/articles/50423411876881-Split-payment-bookings-statuses-and-charges-in-Playtomic-Manager)
  (updated 2026-10-19) — read 2026-10-20
- **[MEASURED]** Manager's catalogs say the same:
  - the transaction status "Authorized", with the tooltip "Total authorized amount is {amount}";
  - "The owner's card is authorized for the entire split-payment booking, and settlement takes place two hours after
    the booking. This covers the owner's portion as well as any pending payments from other participants."

  A participant's own statuses are "Pay in the App", "Unpaid", "Paid", "App: Paid", "Paid by Owner", "Paid at the
  club" and the like. None is for a share that is held or checked. `transactions.json`, `schedule.json`, extract §A
  — read 2026-10-20
- **[POLICY]** Where a club runs Card on File instead, nothing is held at all, and "each participant's fee shows a
  Paid or Mark as paid status". That covers Spain, France, Germany, Sweden, the Netherlands and others. Poland is
  in neither list.
  [Card on File (CoF)](https://helpmanager.playtomic.com/hc/en-gb/articles/46647891110673-Card-on-File-CoF-your-guarantee-for-split-payment-bookings)
  (updated 2026-10-19) — read 2026-10-20
- Carried: the Payment Collection Report lists "Pending and Preauthorized" amounts
  (`competitor-club.md#what-the-club-sees-of-its-money`; the article was updated 2026-09-25).

*Reading:* Playtomic's desk never sees a bare name. A hold shows as one word on the owner's line, and every share
not yet paid shows as an action. On Rakieta's day a name shows "held", "taken", or nothing at all.

---

### R-REQUEST-61 — No rival's cancel dialog names a card fee the club keeps; Playtomic credits its own fee back, and Playmore names its kept commission only in a report

- **[MEASURED] Playtomic Manager's cancel dialog.**
  - Its words: "Cancel booking?" — "When you cancel a paid booking, it will be removed from the schedule but it can
    still be found in the Bookings list. If the payment was made online it will be refunded automatically and if it
    was paid at the club you must refund it to the client."
  - Its choices: "Refund all participants to their original payment methods", "Refund all eligible participants to
    the club wallet" and "Let me choose how to refund each participant". "Additional refund options are only
    supported for products paid under the commission model."
  - Its notice: "Once cancelled, participants will be informed by email and notification to their Playtomic app."
  - The refund choices are "Full refund", "Partial refund" and "No refund". No cancel or refund string in the 24
    namespaces names a fee.

  `reservations.json`, `schedule.json`, `refunds.json`, extract §A — read 2026-10-20
- **[POLICY] Playtomic's help.**
  - When the club cancels, "the player will get a full refund, including the service fee, usually within 2–10
    business days" ([How to cancel a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535256445969-How-to-cancel-a-reservation),
    updated 2026-08-04).
  - "Will I still pay b2b commissions on a refunded booking? No — you shouldn't end up paying commission on money
    that was fully refunded to a player." It is corrected "with a credit note on a following invoice"
    ([Why did I receive a negative payout?](https://helpmanager.playtomic.com/hc/en-gb/articles/50457368851729-Why-did-I-receive-a-negative-payout);
    [B2B Service Fees](https://helpmanager.playtomic.com/hc/en-gb/articles/50654517291537), both updated 2026-10-19).
  - Neither page mentions the card processor's fee. Read 2026-10-20.
- **[MEASURED] tenis4U's panel.**
  - The cancel asks "Anulować rezerwację ze zwrotem?" — "Tak, anuluj ze zwrotem". Below it, it shows a warning
    only if the server sends one (`e.warning`, in orange).
  - Without a refund: "Anulować rezerwację BEZ zwrotu?", by default "Rezerwacja zostanie anulowana bez zwrotu
    środków".
  - The panel itself names no fee, and whether the server's warning does is not visible.
  - Carried: tenis4U keeps 2 % on any deleted online booking
    (`gaps-RESCUE.md#tenis4us-2--is-taken-on-any-deleted-online-booking`).

  `main.bf9c0f8a156c883a.js`, extract §D — read 2026-10-20
- **[MEASURED] Playmore's panel.**
  - After an on-time cancel, the booking says "Automatyczny zwrot przez Stripe: {amount} {currency}" — "Pieniądze
    zejdą z salda klubu w Stripe. Z tą kwotą recepcja nie musi nic robić." It names no fee.
  - Where the money went straight to the club, the booking says "Zwrot po stronie klubu: {amount}" — "zwrot robi klub
    — przelewem albo na miejscu … Opłata serwisowa nie podlega zwrotowi." That last line is about the player's own
    service fee.
  - Its report says: "Pozycje „Rezerwacja – anulowana, zwrot po stronie klubu” to rezerwacje opłacone online i
    odwołane w terminie. Klub oddaje klientowi pełną wpłatę sam. Prowizja Playmore została pobrana przy płatności i
    jest ujęta w sumach oraz na fakturze."

  `calendar-DawkByxO.js`, `reports-Ct22FugR.js`, extract §B — read 2026-10-20

*Reading:* the market says nothing about fees at the press. The cost shows later, on an invoice or in a report.
Rakieta's dialog says, at the press, that the card fees are not returned, which is more than any rival says. Its
fault is reading the cut-off from a page left open.

---

### R-REQUEST-57, R-REQUEST-59 — Google lets a merchant keep either kind of Google Pay card for later charges of varying amounts; it writes nothing for an unscheduled charge or a new phone

- **[DOCS]** Google Pay API FAQ:
  - "Support for recurring billing is tied to the payment method returned in the Google Pay API response."
  - "Both tokenized cards and cards on file can be used for recurring billing." "The payment credential is stored on
    the merchant side for recurring payments."
  - It is supported if "Merchants comply with network rules, such as merchant-initiated transactions" and "Terms of
    payment are disclosed and accepted by the user within the merchant's buyflow".
  - "We also support recurring billing with variable amounts."
  - "Currently, Merchant Initialized Transactions (MITs) do not support dynamic pricing. This is a known limitation."
  - "The encrypted Google Pay payload expires after exactly one week."

  [Google Pay API FAQ](https://developers.google.com/pay/api/faq) — read 2026-10-20
- **[DOCS]** Google's request objects name three ways to enrol a card for charges made without the user. Each
  "is for use with Merchant Initiated Transactions only" and takes a `tokenUpdateUrl`, "to which token lifecycle
  updates are sent":
  - `recurringTransactionInfo`, for being "billed at a fixed frequency";
  - `deferredTransactionInfo`, "a transaction to establish a deferred charge". It requires a `billingDateTime`, and
    its price "must be `null` if `priceStatus` is `NOT_CURRENTLY_KNOWN`";
  - `automaticReloadTransactionInfo`.

  None is for an unscheduled card on file.
  [Request objects (Android)](https://developers.google.com/pay/api/android/reference/request-objects) — read 2026-10-20
- **[DOCS]** A `merchantTokenId` comes back only when all three hold:
  - the merchant sends one of those objects;
  - the merchant sends a `tokenUpdateUrl`;
  - the user picks a device token.

  [Payment data cryptography](https://developers.google.com/pay/api/android/guides/resources/payment-data-cryptography)
  — read 2026-10-20
- **[ABSENT]** Google's word on a device token after the player changes phones. Not in the FAQ, the request
  objects or the cryptography page. — read 2026-10-20
- **[DOCS]** Recurly, a billing platform, on Google Pay:
  - "DPANs are invalidated when a consumer removes the card from their device and a new DPAN is created if they
    re-add the same card, or add a new card to their device."
  - "Subscriptions using a DPAN can fail due to this consumer-driven behavior and are non-recoverable."

  [Recurly: Google Pay](https://docs.recurly.com/recurly-subscriptions/v2.29/docs/google-pay) (updated 2025-10-20)
  — read 2026-10-20
- Carried:
  - Stripe's three kinds of Google Pay card: a device token, the card's own number, and e-commerce tokens
    (`stripe-saving-cards.md#google-pay-googles-terms-production-access-a-real-device`);
  - Visa's announced decline of standing-instruction charges on device tokens, now on hold;
  - Playtomic counts Google Pay as a card-on-file guarantee, yet asks for manual renewal of a membership paid with a
    wallet (`gaps-payments-03.md#r-pay-6--how-often-an-apple-pay-device-token-fails-a-later-charge-after-the-player-changes-phones`).

*Reading:* in principle Google allows Rakieta's later charge made without the player: a stored card, varying
amounts, and terms accepted in the flow. But none of its three ways to enrol a card is for an unscheduled charge.
A card saved on an Android phone is a device token, so it carries the same new-phone risk as Apple's. A card saved
from Chrome or a Google account is the card's own number, which no phone change touches.

---

### R-REQUEST-58 — Whether kluby.org still emails and texts the staff on each new online booking: still only the help video's word

- Carried: help chapter 2.5 "Powiadomienia" (machine captions), and the changelog
  (`gaps-REQUEST.md#klubyorg-emails-and-texts-the-staff-on-each-new-online-booking-and-lists-the-latest-bookings`).
- **[POLICY]** The changelogs for 2016–2023 were re-read. The years 2010–2015 and 2024–2026 serve no entries.
  - The only notice to staff they name is still "Powiadomienie dla pracownika o odwołanej rezerwacji" (2020).
  - 2019 adds automatic notices to the administrator: when a player asks to link an account, and when a worker
    who already has an account is added.
  - 2022 adds "Edycja powiadomień uczestnika przez administratora" and "Podgląd wysłanych powiadomień w historii
    klienta o rezerwacjach".
  - The feature list still says "Powiadomienia SMS/MAIL".

  [Co nowego](https://oferta.kluby.org/changelog?rok=2020), [Funkcje](https://oferta.kluby.org/funkcje), extract §F
  — read 2026-10-20
- **[POLICY]** The help page has a second chapter on notices: "9.11. Powiadomienia", under "9. Ustawienia". It is
  YouTube `n_V5Z4d9zeo`, whose title "Rozdział 9.11. Powiadomienia" was read through oEmbed.
  [kluby.org: Pomoc](https://oferta.kluby.org/pomoc) — read 2026-10-20
- **[ABSENT]** That chapter's contents. YouTube served no captions, the watch page was a consent wall, and the
  thumbnail is the logo. The video was not watched. — read 2026-10-20

*Reading:* nothing newer contradicts the 2.5 video. The grade does not rest on it.

---

### R-CLUBBOOK-44 — Neither Playmore's panel nor Playtomic Manager tells a club a refund is waiting or failed (answered today for R-PAY-53)

- Answered:
  `gaps-payments-02.md#r-pay-53--neither-playmores-panel-nor-playtomic-manager-shows-a-club-a-refund-pending-or-failed`.
  It covers:
  - Playmore's "Automatyczny zwrot przez Stripe … recepcja nie musi nic robić";
  - a refund Playmore's server records as failed, which the desk sees only as "kort został usunięty";
  - Playtomic taking refunds back from payouts.
- **[MEASURED]** Added this round, from Playtomic Manager's catalogs:
  - a payment reads "Paid", "Pending", "Refunded" or "Voided" (`club_payments`);
  - a transaction reads "Authorized", "Paid", "Pending", "Refund" or "Voided", with "Payment has assigned refund"
    (`transactions`);
  - a booking's payment reads "Paid", "Partially paid", "Pending", "Refunded", "Unpaid" or "N/A" (`bookings`).

  None of the 24 served namespaces has a word for a refund that is waiting or has failed. Extract §A — read 2026-10-20
- **[MEASURED]** Playmore's reports also say: "W klubie bez portfela Playmore zwroty oddaje klub poza systemem,
  więc rejestr ich nie zawiera." `reports-Ct22FugR.js` — read 2026-10-20
- The player's side is carried: Playmore tells the payer a refund failed
  (`gaps-payments-04.md#r-rescue-47--what-a-player-is-told-when-a-refund-shown-as-made-then-fails-playmore-has-a-state-for-it-matchi-sends-the-player-to-the-club-playtomic-says-nothing`).

---

### R-CLUBBOOK-17 — The words of Playtomic's change email, and whether it names the old court: still not found

- Carried: "All customers in the reservation will get an email notification about the change"
  (`gaps-CLUBBOOK.md#playtomic-an-email-and-an-in-app-notice-their-wording-is-not-published`).
- **[MEASURED]** Manager still logs a move as "Court updated from {oldResourceName} to {newResourceName}". Its
  reschedule dialog asks only about prices: "Do not update the players prices". `match_history_record.json`,
  `schedule.json` — read 2026-10-20
- **[POLICY]** Its "Communication and notifications" article covers only the club's own booking-confirmation
  message and its open-match registration message. Nothing covers a change.
  [Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145-Communication-and-notifications)
  (updated 2026-07-21) — read 2026-10-20
- **[ABSENT]** The email or push text. Looked in:
  - the club help, through its API: "reschedule email" (61 hits) and "notify players" (119), none with the text;
  - the 14 scripts of Playtomic's player web app (`app.playtomic.com`), which hold no booking-change words;
  - a web search for English and Spanish subject lines ("has been modified", "reserva ha sido modificada").

  Read 2026-10-20.

---

### R-CLUBBOOK-32 — What a block over several courts does to bookings already in it: Playmore saves it court by court through the call that refuses a taken hour; tenis4U leaves it to its server

- **[MEASURED]** *(code)* Playmore:
  - A block ("Niedostępność") is saved as `createReservation` with `type: "unavailable"`, one court and date at a
    time, 0,5 s apart.
  - Three failures in a row stop the run.
  - Whatever failed is listed: "Nie zapisało się {failed} z {total}" — "Dodano {done} z {total}. Te terminy dodaj
    ponownie:".
  - For a desk booking, the same call refuses an hour already taken: "Ten termin na tym korcie jest już zajęty. Nic
    nie zapisaliśmy — wybierz inną godzinę albo kort."
  - The block form has no "despite the clash" choice. Series and moves have one: "Utwórz mimo kolizji terminów",
    "przenieś ją mimo kolizji".

  `calendar-views-D40b467p.js`, `calendar-DawkByxO.js`, extract §B — read 2026-10-20
- **[ABSENT]** Whether Playmore's server refuses a block over a booked hour or saves it beside the booking. The
  form lists the failures but not why they failed. — read 2026-10-20
- **[MEASURED]** *(code)* tenis4U:
  - each ticked court's block is one `setBlockedPeriod` call, and any refusal is the server's own message, shown in
    a toast;
  - the panel shows no list of the bookings affected.

  `main.bf9c0f8a156c883a.js`, extract §D — read 2026-10-20
- **[MEASURED]** Playtomic Manager now has "Blocking" ("Block a court — Mark courts as unavailable"), marked
  "BETA feature", one court per block. Its feedback form asks whether clubs want an "Option to select multiple
  courts" and the "Ability to create recurring blockings". No string covers bookings inside a block.
  `schedule.json` — read 2026-10-20
- Carried: MATCHi refuses a block over a booked slot and lists the bookings to cancel first; CourtReserve makes the
  club choose (`../club-software/season-bookings-and-blocks.md#b7-bookings-already-inside-a-new-block`).

*Reading:* no rival shows the desk every booking in the way at once, except MATCHi's list and CourtReserve's table.
Playmore's failures arrive as dates and courts, not as bookings.

---

### R-CLUBBOOK-37 — Whether any rival sends players back to the club and hour after the club closed it: none found; Playmore's "play again" leaves cancelled bookings out

- Carried:
  - Playtomic, MATCHi and Playmore refund, and offer no other slot
    (`gaps-CLUBBOOK.md#playtomic-matchi-and-playmore-refund-none-offers-another-slot`);
  - Kraków rules offer another court or time.
- **[POLICY]** KSG II.12, re-read: "Klub zaproponuje w miarę dostępności inny kort lub termin. Jeżeli skorzystanie z
  rezerwacji w innym terminie nie będzie możliwe, wniesiona opłata zostanie, według wyboru klienta, zaliczona na
  poczet kolejnej rezerwacji albo zwrócona."
  [KSG regulamin](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf) — read 2026-10-20
- **[MEASURED]** *(code)* Playmore's home suggests a player's usual hour at a club, with "Jak zwykle", "zwykle
  {slot}" and "Zagraj znowu".
  - It is built from the last 60 days' bookings, and needs at least two at the same weekday and hour.
  - It counts only bookings with no `cancellation_status`.
  - A club marked closed shows "Tymczasowo nieczynny" or "Tymczasowo nieczynny do {date}" in place of that line.

  `CCIEGau6.js`, `CDUyWt1b.js`, `CaGsz1xj.js`, `CuTXkj_H.js`, extract §C — read 2026-10-20
- **[POLICY]** Playtomic tells a closing club: "Close the calendar and remove online bookings if the club is
  closing. For existing bookings, cancel them promptly to enable player refunds."
  [How to Handle Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097)
  (updated 2026-08-03) — read 2026-10-20
- **[ABSENT]** A rival that, after a club calls games off for a closure, offers the same players that club and hour
  again. — read 2026-10-20

*Reading:* rivals either refund, or offer another court or time by hand. Playmore's own suggestion steers players
away from cancelled hours and closed clubs.

---

### R-CLUBBOOK-45 — Whether a Kraków club keeps a booked game's price when the club moves it after a price change: no rule reprices it, and KSG keeps paid services as they were

- **[POLICY]** KS Grzegórzecki (Kraków, rules in force from 30 Aug 2026):
  - II.3 "Opłata za wstęp na kort ustalana jest według aktualnego cennika, chyba że dla danego rodzaju rezerwacji
    określono inne zasady."
  - II.10: the club may change or cancel a booking for organisational or technical reasons.
  - II.13 "Zmiana numeru kortu w ramach tego samego obiektu, na kort o porównywalnych warunkach do gry, nie stanowi
    odwołania rezerwacji i nie wymaga zgody osoby dokonującej rezerwacji."
  - VII.4: changes "nie naruszają praw nabytych ani warunków usług już opłaconych".

  [KSG regulamin](https://grzegorzecki.pl/wp-content/uploads/2026/08/Regulamin_KSG_2026_2027_Aktualny.pdf) — read 2026-10-20.
  Fame Sport's matching clauses are carried from 2026-10-12, since its PDF now answers 404
  (`../club-software/season-bookings-and-blocks.md#s3-price-changes-mid-season`).
- **[POLICY]** Miazga: "Zmiana terminu gry jest równoznaczna z anulowaniem dotychczasowej gry i rezerwacją nowego
  terminu." Atras: "Ceny mogą ulegać zmianom." — read 2026-10-20
- **[MEASURED]** Playmore lets a player move his own booking only "na termin w tej samej cenie, więc niczego nie
  dopłaca ani nie dostaje zwrotu — płatność zostaje przy rezerwacji". Its reschedule is refused when the fee has
  changed (`gaps-payments-02.md#r-leave-3--playmores-leave-press-carries-no-cost-to-check-its-reschedule-press-does-and-is-refused-when-the-fee-moved`).
  `venue-settings-OPJNS5u4.js` — read 2026-10-20
- **[MEASURED]** Playtomic Manager:
  - Moving a paid booking: "This booking has been paid and the price can't be updated. Would you like to change it
    anyway?" — "Move anyway".
  - Rescheduling offers "Do not update the players prices".
  - A move that would cost more than the amount held is refused: "Exceeding the preauthorized amount for the
    booking is not allowed".

  `schedule.json` — read 2026-10-20
- **[ABSENT]** A Kraków rule on a booked game the club moves after a price change. Searched KSG, Miazga, Atras,
  Squash4You and Garden Padel. — read 2026-10-20

*Reading:* by KSG's words, a club's move to a comparable court is not even a cancellation, so the game stands at the
price paid. Rakieta's "same price" test has the shape of Playmore's rule for a player moving his own booking, but
Rakieta applies it to a club's move. No Kraków rule, and no rival's desk, does that.

---

### R-CLUBBOOK-14 — A Playtomic help article on what a club with a restricted payments account can still do: still none

- Answered as far as the market goes:
  - `gaps-payments-03.md#r-clubmoney-9--what-playtomic-does-with-an-open-match-still-filling-and-with-bookings-already-made-when-its-clubs-stripe-account-is-restricted`;
  - `gaps-payments-04.md#r-clubmoney-5-r-clubmoney-8--playtomic-manager-warns-a-live-club-before-its-payments-stop-and-sends-it-to-stripe-nothing-marks-stripe-is-checking`.
- **[ABSENT]** Club help searched again through its API:
  - "restricted" gives 19 hits, about open matches, tournaments, wallets and leagues;
  - "missing information", "Stripe account" and "payments interrupted" give none on what a restricted account
    stops.

  "Online payments with Stripe" (updated 2026-10-19) says only that "Stripe may request extra verification".
  "Payout Issues" (updated 2026-10-19) covers rejected or returned payouts. Read 2026-10-20.
- **[MEASURED]** Manager's catalogs still hold only the integrations warning. The errors a move can give are about
  court size, sport, and "Exceeding the preauthorized amount for the booking is not allowed". None is about the
  club's payments account. `schedule.json`, `integrations.json` — read 2026-10-20

*Reading:* unchanged. At Playtomic a move goes ahead whatever Stripe says.
