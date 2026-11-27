# Competitor, club side — Playtomic Manager

Playtomic (the competitor the spec compares itself with) from a club's desk: what a club controls,
pays and is paid; requests, cancellations, check-in, no-shows, disputes, payouts, onboarding. It has
**no club in Kraków** (*Playtomic in Poland and Kraków*); Kraków's rivals are in `platforms` and
`local-market`.

**How it was read.** The club help centre (helpmanager.playtomic.com) refuses page fetches, so all 157
en-gb club articles and 93 player articles were pulled through its public Zendesk API (same body as the
linked public page) and searched in full on **2026-10-08**. Facts dated 2026-10-06/07 are carried from
`docs/research/games-and-fill-in-market.md` (§1.2, §1.3, §5, §7.1, §7.6); being two days old, none was
re-verified, but every article updated since 2026-10-06 was re-read and changes are noted.

**Kinds:** **[POLICY]** the company's own rule or statement · **[PRICE]** published price · **[DOCS]**
payment provider's document · **[MEASURED]** seen by using the product · **[COMPLAINT]** one party's
account, a rival vendor's claim included · **[ABSENT]** looked for, not found, with where.

---

## 1. What Playtomic is for a club, and where it is

### Manager is a web app and the club's only calendar

- Manager "is a web app you open at manager.playtomic.io. It is not a native app"; on a phone "Some features are limited on mobile". **[POLICY]** [Manager on mobile](https://helpmanager.playtomic.com/hc/en-gb/articles/46212092028561) — read 2026-10-08
- Desk bookings go into the same calendar the app sells from, so desk and app cannot double-sell. Linked "shared courts" block each other. **[POLICY]** [Playtomic Manager](https://playtomic.com/playtomic-manager), [Shared courts](https://helpmanager.playtomic.com/hc/en-gb/articles/45292498463633) — read 2026-10-06

### Playtomic in Poland and Kraków

- No official count of Polish clubs is published. **[ABSENT]** (sitemap, Manager, pricing, clubs pages; web) — read 2026-10-06
- An own count from public club pages found **33 Polish clubs**, all in PLN, nearly all padel: Warszawa 6, Poznań area 8, Silesia 8, others in the north and west. This is a lower bound; no screenshot was taken. **[MEASURED]** [sitemap](https://playtomic.com/sitemap.xml) — read 2026-10-06
- **No Kraków club.** The nearest-clubs lists of Katowice, Tychy and Bielsko-Biała reach Opole and Wrocław without one; guessed Kraków slugs return 404. **[ABSENT]** [One Padel Center](https://playtomic.com/clubs/one-padel-center) — read 2026-10-06

### Nothing for clubs in Polish

- Club help and support come in nine languages, none Polish; playtomic.com/pl and /pl/playtomic-manager return 404 (/de/playtomic-manager returns 200). **[POLICY]** [Club Support](https://helpmanager.playtomic.com/hc/en-gb/articles/20534845748881) + **[ABSENT]** (HTTP status of each URL) — read 2026-10-08

---

## 2. Onboarding

### Applying: a form, a demo, a single-use referral code

- The club fills in a form; the team "will … contact you by email … to guide you through the Playtomic Manager demo setup", which needs "a single-use code issued to your club after verification". **[POLICY]** [Complete the setup](https://helpmanager.playtomic.com/hc/en-gb/articles/20535510981137) — read 2026-10-08
- An alert then asks the club to "Confirm General Information": name, address, images, contact details, "Booking limits and cancellation policy", "Court list and pricing". Billing details and Stripe follow. **[POLICY]** [same](https://helpmanager.playtomic.com/hc/en-gb/articles/20535510981137) — read 2026-10-08

### The go-live checklist and the warning bar

- The club needs six things: a plan, a Stripe account, billing information, courts and prices, opening hours and images, and contact details. "If any of the above information is incomplete, a warning will appear at the top of your Playtomic Manager screen". **[POLICY]** [Go live](https://helpmanager.playtomic.com/hc/en-gb/articles/20535378377745) — read 2026-10-08

### A person makes the club visible

- "Once your onboarding coordinator confirms everything is complete, they will make your club visible in the Playtomic app and on the website". **[POLICY]** [Go live](https://helpmanager.playtomic.com/hc/en-gb/articles/20535378377745) — read 2026-10-08
- No self-serve go-live control is documented. **[ABSENT]** (157 articles: "go live", "club visible", "pending activation") — read 2026-10-08

### Stripe onboarding through Playtomic

- "It's mandatory for your club to create a Stripe account": SMS check, type "(Individual, Company, Non-Profit)", registration number and address, owners with "at least 25% ownership", an IBAN; "Stripe may request extra verification, such as an ID or utility bill." **[POLICY]** [Online payments with Stripe](https://helpmanager.playtomic.com/hc/en-gb/articles/20535417606161) — read 2026-10-08
- What Manager shows when a live club's Stripe account is restricted is not documented. **[ABSENT]** (searched "restricted", "verification", "Stripe account", "inactive") — read 2026-10-07

### The club's own terms, versioned at checkout

- A club can require its own "Waiver and or Terms & Conditions"; each edit makes a new version, and "players must accept it again the next time it is required". Acceptance is stored "with a timestamp". **[POLICY]** [Legal Documents](https://helpmanager.playtomic.com/hc/en-gb/articles/45838498871697) — read 2026-10-07
- What a new version does to bookings already made is not stated. **[ABSENT]** — read 2026-10-07

### Staff logins, roles, and who gets booking emails

- Each staff member is a separate admin, added by the "Tenant Owner", "the only person who can access Club Admins". Each admin chooses **email notifications for "Bookings created or cancelled by players, course enrollment cancellations"**. **[POLICY]** [Admin role](https://helpmanager.playtomic.com/hc/en-gb/articles/20535152812049) — read 2026-10-08
- Permissions are per menu, "view-only or view and edit". **[POLICY]** [Admin permissions](https://helpmanager.playtomic.com/hc/en-gb/articles/20534222446353) — read 2026-10-08
- No daily or digest email of new bookings is documented, only per-booking notices to each admin. **[ABSENT]** (searched "digest", "daily summary", "summary email") — read 2026-10-08

---

## 3. What the club controls

### Booking rules: book-ahead, cancellation hours, per-day and active limits

- Settings → Venue → Booking holds four rules: **Book Ahead Limit** (days), **Cancellation Time (hours)**, **Maximum Bookings/Day** and **Number of Active Bookings**. A category's own rules override them for its members. **[POLICY]** [Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297) — read 2026-10-06
- "Some clubs allow cancellation all the time, some with one day's notice, and some do not allow cancellation at all." No default number of hours is published. **[POLICY]** + **[ABSENT]** [same](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297) — read 2026-10-06

### No minimum notice

- No "book at least N hours before" rule for courts is documented; only classes have a "registration deadline". **[ABSENT]** (157 articles: minimum notice, last-minute, "before the start") — read 2026-10-06

### No booking that waits for the club to confirm

- Every online booking is confirmed at once, and nothing holds one for the club's approval. **[ABSENT]** (searched approve, pending confirmation, booking request) — read 2026-10-06. Searched again for "accept", "reject", "time to confirm" and "respond within": nothing for the club — 2026-10-08
- The only approvals documented are not the club's:
  - An off-level player's "Request your place" needs "approval from everyone in the match"; "If everyone accepts, the player will be able to pay", so nobody pays before approval. **[POLICY]** [Request a spot](https://helpmanager.playtomic.com/hc/en-gb/articles/20535718052241) — read 2026-10-08
  - For an unpaid recurring booking the club makes, players "need to accept the booking and move to check out screen to finalize their payment". **[POLICY]** [Recurring series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513) — read 2026-10-08

### Which courts are sold online

- Each court has an **Active Court** and a **Bookable Online** toggle; a court not bookable online stays in the calendar for the desk. **[POLICY]** [Courts](https://helpmanager.playtomic.com/hc/en-gb/articles/20535305323665) — read 2026-10-06
- A slot is bookable online only where a price rule covers it (60, 90 or 120 min). **[POLICY]** [Availability](https://helpmanager.playtomic.com/hc/en-gb/articles/20535323617425) — read 2026-10-06
- What switching Bookable Online off does to open matches already on the court is not documented. **[ABSENT]** — read 2026-10-07

### No timed release, and the "private club" workaround

- No automatic release of desk-held hours N days before is documented. **[ABSENT]** — read 2026-10-07
- The workaround is a Book Ahead Limit of 0 plus a members' benefit with its own window, but "setting it to 0 days will disable Open Match creation for everyone at your club". **[POLICY]** [Private club](https://helpmanager.playtomic.com/hc/en-gb/articles/50979728127889) — read 2026-10-07

### Prices: per court, day, time and length; dated; VAT included

- Price rules are per court, day, time range and length (overlaps refused); a **Timed Price** covers a date range. **[POLICY]** [Prices](https://helpmanager.playtomic.com/hc/en-gb/articles/20535589805585), [Timed Prices](https://helpmanager.playtomic.com/hc/en-gb/articles/20535348126353) — read 2026-10-07
- Prices "already include VAT". **[POLICY]** [Invoicing System](https://helpmanager.playtomic.com/hc/en-gb/articles/24829231088657) — read 2026-10-06
- A member **Benefit** carries its own prices and its own "Cancellation policy (in hours)". **[POLICY]** [Membership](https://helpmanager.playtomic.com/hc/en-gb/articles/20534703609745) — read 2026-10-06
- Only unpaid fees can be repriced: "Any fee already marked as paid cannot be modified." **[POLICY]** [Edit an unpaid price](https://helpmanager.playtomic.com/hc/en-gb/articles/20534797254289) — read 2026-10-08

### Holidays and blocks

- A Holiday has a start and end date and time, for "a specific court or the whole club", and "block[s] your schedule from online reservations". Blocks cover "Maintenance Management" and "Weather Closures" and are left out of occupancy. **[POLICY]** [Holidays](https://helpmanager.playtomic.com/hc/en-gb/articles/20535276328849), [Schedule basics](https://helpmanager.playtomic.com/hc/en-gb/articles/20560058451985) — read 2026-10-07
- What a Holiday does to bookings already in it is not stated. **[ABSENT]** — read 2026-10-07

### A changed setting and bookings already made

- No article says whether a changed Cancellation Time reaches existing bookings. **[ABSENT]** (157 club and 94 player articles: "already made", "existing booking", "retroactive", "new bookings only") — read 2026-10-07
- The terms tie the policy to the act of booking: "By making a reservation, the user accepts the cancellation policy of the corresponding club." **[POLICY]** [Legal Conditions §9](https://playtomic.com/legal-conditions) — read 2026-10-07
- Price changes "will not affect orders or purchases for which the User has already received an order confirmation". **[POLICY]** [Legal Conditions §7](https://playtomic.com/legal-conditions) — read 2026-10-07

### What players are told, in the club's words

- The club writes a "Booking confirmation email message" (per court or for all) and a "Public match registration message" (parking, lockers, rental), and picks their language. The email fills in the player, date, time, place and payment. **[POLICY]** [Communication](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145) — read 2026-10-08

---

## 4. Open matches from the club's side

### Switched on per sport, then made at every free hour

- Once switched on, Playtomic "automatically" creates open matches "at all available times in your club schedule". The club sets the level window around the first joiner for its own matches; the default length is 90 min. **[POLICY]** [Configure Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473) — read 2026-10-06
- Open matches "are designed to be created by players", but an admin can create one. With "Create match (recommended)" the system books the court; "Create match with court" books one at once. **[POLICY]** [Create an open match](https://helpmanager.playtomic.com/hc/en-gb/articles/48305440234129) — read 2026-10-08

### Pay to join; when the court is held

- "Payment must be completed online via the app or Club Wallet — payment at the club is not supported." A desk payment "will create a debt in the system". **[POLICY]** [Create an open match](https://helpmanager.playtomic.com/hc/en-gb/articles/48305440234129), [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08
- The court is booked never with 0–1 players, with 2 only if "more than 12 hours remain", with 3 only if "more than 4 hours remain", and with 4 "immediately". Below that the match "isn't canceled right away" while a court is free. **[POLICY]** [Cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) — read 2026-10-08
- In 20 listed countries one player holds the court "until 48 hours before" (UK, France, Netherlands, Belgium, Romania and others). Poland is not among them. **[POLICY]** [Occupy calendar slots](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929) — read 2026-10-08

### Automatic cancellation, signed "Anemone"

- A match is cancelled when no court is left ("private reservations always take priority over open matches that aren't full or don't have a court assigned yet"). It is also cancelled if it "still hasn't reached 4 players about 1 hour before the scheduled start time". Players get "a full automatic refund (including the Playtomic service fee)". **[POLICY]** [Cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) (updated 2026-10-08) — read 2026-10-08
- New in that update: "'Cancelled by Anemone' means the match was cancelled automatically", and a cancelled match "can't be restored". **[POLICY]** [same](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) — read 2026-10-08
- If the club forces a court onto a match ("+Add Court"), the match "won't be automatically cancelled" and the club carries it. **[POLICY]** [Manage Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353) — read 2026-10-06

### Leaving inside 24 hours goes through the club

- Players "can cancel their spot … up to 24 hours before". After that "they should contact the club directly, and the club will decide". A full match is "locked", and players "request removal through the match chat". A swap needs "at least 2 hours" before the start. **[POLICY]** [Cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601), [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08
- The player help adds that a **not-full** match can be left any time before it starts. **[POLICY]** [Open-match cancellation](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465) — read 2026-10-06
- The club cannot change this 24 h: the open-match settings are only sport, format and level. **[POLICY]** [Configure Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473) — read 2026-10-07

### Blocks between players reach bookings

- Blocking is the player's, in the app: "if someone in an Open Match has blocked a player, that blocked player will not be able to join", and the same goes for private bookings and "Community Matches". **[POLICY]** [Block a user (App only)](https://helpmanager.playtomic.com/hc/en-gb/articles/20535339424529) — read 2026-10-08
- The club cannot ban a player, as far as the help says. It is told "For player misconduct, consider blocking or restricting their access" with no how. **[ABSENT]** (searched block, restrict, ban) + **[POLICY]** [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08

---

## 5. The desk's day: bookings, moves, cancellations, payments

### What a manager may and may not change

- Staff book in the calendar, with single or split payment, for registered users or a "Guest user". **[POLICY]** [Add a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535410170769) — read 2026-10-06
- A manager may extend, reschedule, re-court or reprice a booking, record payments, add notes, chat, and add or remove players (not the owner); **not** swap teams or change results. "Users always receive emails and in-app notifications about any changes to their reservations." **[POLICY]** [Modify a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20534894210833) — read 2026-10-08
- Players cannot change a booking in the app: they "must cancel the original booking and make a new one". **[POLICY]** [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08

### Moving a booking

- Same day: drag and drop, also to another court. Another day: Reschedule. "Past reservations can also be rescheduled." Bookings move only to "another court of the same size" ("The change cannot be made due to the size of the court."). **[POLICY]** [Reschedule](https://helpmanager.playtomic.com/hc/en-gb/articles/20535241098257) — read 2026-10-08
- A price difference raises a pop-up with "Do not update players' prices". "Already paid fees are not affected — those transactions are final." "All customers in the reservation will get an email notification about the change." The player is not asked to agree. **[POLICY]** [same](https://helpmanager.playtomic.com/hc/en-gb/articles/20535241098257) — read 2026-10-08

### Adding or removing a player

- An added player gets "a confirmation email and an in-app notification". If a removed player "paid through the app, the refund is processed automatically"; if "at the club, you are responsible for issuing the refund". To remove the owner, "you must cancel the whole reservation". **[POLICY]** [Players in a private reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535398512657), [Modify a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20534894210833) — read 2026-10-08

### The club cancels: always a full refund

- "If the club cancels a booking via Playtomic Manager, the player will get a full refund, including the service fee, usually within 2–10 business days". **[POLICY]** [Cancel a reservation (club)](https://helpmanager.playtomic.com/hc/en-gb/articles/20535256445969) — read 2026-10-08
- A partial refund, a fee kept by the club, or a reason field on a club cancellation is not documented. **[ABSENT]** (searched "partial refund", "reason") — read 2026-10-08
- "Clubs can cancel unilaterally a reservation without prior notification to the user." **[POLICY]** [Legal Conditions §9](https://playtomic.com/legal-conditions) — read 2026-10-06
- A club on Professional or higher, on the New Billing Model, may refund to the player's **Club Wallet** instead. The money stays with the club, and no negative payout follows. **[POLICY]** [Refunds to Club Wallet](https://helpmanager.playtomic.com/hc/en-gb/articles/28213277715089) — read 2026-10-06

### Late cancellations, weather, closures

- After the deadline players "need to contact your Club directly". The decision is the club's, "but refunds are commonly given in cases like: Bad weather; Injury or illness". Playtomic "cannot override these rules". **[POLICY]** [Cancel a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535256445969), [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08
- A closing club should "Close the calendar and remove online bookings" and cancel existing bookings "promptly to enable player refunds". Courts left unusable: "cancel bookings if necessary to process refunds". **[POLICY]** [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-08

### Split payment: an unpaid share is charged after the game

- Only the owner pays at booking; shares still unpaid two hours after the end are taken from the owner, by a country-dependent mechanism (Poland is in neither list). **[POLICY]** [Split vs Single](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721) — read 2026-10-06
  - **Card on File:** if charging the owner's card fails, "Playtomic creates a debt for the booking owner", and "Playtomic hasn't advanced the money to the club". **[POLICY]** [Split vs Single](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721), [Card on File](https://helpmanager.playtomic.com/hc/en-gb/articles/46647891110673) — read 2026-10-08
  - **Pre-authorisation:** the full price is held on the owner's card and captured "capped at the full booking amount". **[POLICY]** [Pre-authorization](https://helpmanager.playtomic.com/hc/en-gb/articles/20534487294097), [Split statuses](https://helpmanager.playtomic.com/hc/en-gb/articles/50423411876881) — read 2026-10-06
  - **Debt system:** "Playtomic advances the outstanding share to the club", and the player is blocked until they pay. **[POLICY]** [Split vs Single](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721) — read 2026-10-06
- A desk payment not marked paid within 2 h of the end gets the owner charged. "Playtomic cannot remove such debts, only mark them as paid", and the club refunds. **[POLICY]** [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097), [Mark as paid](https://helpmanager.playtomic.com/hc/en-gb/articles/46928469100817) — read 2026-10-08
- In a club-made recurring series, payments "are not automatically enforced … The club will need to follow up", and "Participants can leave a recurring booking match at any time". **[POLICY]** [Recurring series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513) — read 2026-10-08

### Desk payments and the day's cash

- The **Cash Register** opens and closes a session a day, with "Expected Cash", "Actual Cash" and "Difference". It is "an informative tool". **[POLICY]** [Cash Register](https://helpmanager.playtomic.com/hc/en-gb/articles/22684483827857) — read 2026-10-08
- Benefit sports cards (MultiSport and others) appear nowhere in the club help. **[ABSENT]** (searched multisport, Benefit Systems, Medicover, FitProfit) — read 2026-10-08

### The booking list

- Filters: date or range (creation or **service** date), user, type and sport. Exports as JSONL or CSV. **[POLICY]** [Booking List](https://helpmanager.playtomic.com/hc/en-gb/articles/20534162168337) — read 2026-10-08

### Talking to players, and what the club sees of them

- Each booking and match has a chat: "managers can send messages to all players", and players get a push for each message. **[POLICY]** [Chat option](https://helpmanager.playtomic.com/hc/en-gb/articles/20535129899921) (updated 2026-10-07) — read 2026-10-08
- To reach a player, "the best way is the chat inside the reservation itself". Players see the club's phone, website and address, but "the app doesn't show a club email address". **[POLICY]** [How players contact your club](https://helpmanager.playtomic.com/hc/en-gb/articles/48993331219985) — read 2026-10-08
- A desk payment does not share the player's details with the club. That "only happens through an online payment or by the player accepting your club's Terms & Conditions". **[POLICY]** [Customers: common issues](https://helpmanager.playtomic.com/hc/en-gb/articles/46345235970833) — read 2026-10-08

---

## 6. Check-in

### No check-in feature; door codes instead

- Check-in appears once, in a list of what admins can do on a phone. No article explains a check-in or how to mark a player arrived. **[ABSENT]** (157 club articles: check-in, arrival, attend, QR) — read 2026-10-08
- "Playtomic doesn't provide a built-in QR code feature" (meaning a QR code for booking). **[POLICY]** [General FAQ](https://helpmanager.playtomic.com/hc/en-gb/articles/43539938393233) — read 2026-10-08
- With hardware (e.g. "QT System, Micro Solution, Smart Padel"), "Access codes are created automatically for each reservation and refresh 10 minutes before the match starts". The code shows in the match details, and "Players can go straight to the court … no need to stop at reception". **[POLICY]** [Hardware](https://helpmanager.playtomic.com/hc/en-gb/articles/20534244219665) — read 2026-10-08

---

## 7. No-shows, results, disputes

### No-shows: open matches only, reported to Playtomic by players

- "Only the affected players can report the no-show, and only through Playtomic." "Your club cannot submit this report on the player's behalf." Attendees should name the absent player in the match chat. **[POLICY]** [No-Show Policy](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513) — read 2026-10-08
- A report must come within 7 days and before the result is confirmed. The absentee owes the court fee as a debt that blocks the app, and the result is voided. **[POLICY]** [same](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513), [Player: no-show](https://playerhelp.playtomic.com/hc/en-gb/articles/43240624037393) — read 2026-10-06
- Attendees are refunded "once the report has been reviewed — this can take up to 10 days from review, plus 2–15 business days". Shares paid from a wallet are "entirely up to your club". **[POLICY]** [No-Show Policy](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513) — read 2026-10-08
- The terms count arriving ≥ 10 min late or leaving ≥ 10 min early as a no-show. **[POLICY]** [Legal Conditions](https://playtomic.com/legal-conditions) — read 2026-10-06
- No process exists for a no-show on a private booking. **[ABSENT]** — read 2026-10-06, searched again 2026-10-08

### Results belong to the players

- "You can't change results in Playtomic Manager. To update a result, the players need to fill in this form." **[POLICY]** [Modify a reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20534894210833) — read 2026-10-08

### Chargebacks: what the club is told

- A player's chargeback "may be recorded as an outstanding debt", and their bookings can be restricted. Failed payments "may be handled directly by the corresponding club". **[POLICY]** [Legal Conditions §8](https://playtomic.com/legal-conditions) — read 2026-10-06
- On the club side, chargebacks appear only in reconciliation: missing payout codes "might be … payments that later became chargebacks or refunds". Who bears the loss is not stated. **[POLICY]** [Payments List vs Self Invoice](https://helpmanager.playtomic.com/hc/en-gb/articles/20534392814737) — read 2026-10-07; **[ABSENT]** for liability (searched "chargeback", "dispute"), checked again 2026-10-08
- For card charges a US club starts itself: "Disputes are handled manually by the operations team … You may need to provide documentation." **[POLICY]** [Club Initiated Transactions](https://helpmanager.playtomic.com/hc/en-gb/articles/40645779207569) — read 2026-10-06

---

## 8. What the club pays

### Subscription plans, with no published prices

- The plans are Standard, Professional, Champion and Master, monthly or annual, with a two-week trial. **[POLICY]** [Subscription plans](https://helpmanager.playtomic.com/hc/en-gb/articles/20535458071313) — read 2026-10-06
- No amounts are published. **[ABSENT]** [Pricing](https://playtomic.com/pricing) — read 2026-10-06
- Every plan has payments, matches, schedule and reports. Wallet and POS start at Professional. Invoices, API, memberships, leagues and multiple legal entities start at Champion. Support answers within 48 h on Standard, 8 h on Professional and 4 h on Champion. **[POLICY]** [Pricing](https://playtomic.com/pricing) — read 2026-10-06
- If a renewal fails, the club has 5 days; then "your club will be automatically set to inactive", invisible, with no bookings. What happens to bookings already made is not stated. **[POLICY]** + **[ABSENT]** [Subscription plans](https://helpmanager.playtomic.com/hc/en-gb/articles/20535458071313) — read 2026-10-07

### A commission on every online payment, per contract

- "Every time a player pays for a booking online … our service fee is automatically deducted from that payment before the money reaches you." It is invoiced monthly to the billing email. On a refund, the fee "is corrected with a credit note, which may appear on a later invoice". **[POLICY]** [B2B Service Fees](https://helpmanager.playtomic.com/hc/en-gb/articles/50654517291537) (updated 2026-10-07) — read 2026-10-08
- The rate "is defined in your club's contract" and is not published. **[POLICY]** [OBM Guide](https://helpmanager.playtomic.com/hc/en-gb/articles/44898846238609) — read 2026-10-06; **[ABSENT]** for a rate
- **New: a worked example.** "An amount equal to the commission … is automatically withheld, with an additional 21% (Spanish VAT) if your club is not registered with VIES." On 10 € at "3.5% (example of your center's commission)", that is 0.35 € + 0.07 € VAT, so "9.58€ is the payment you will receive". 3.5 % is an example, not a published rate. **[POLICY]** [Check Payments in NBM](https://helpmanager.playtomic.com/hc/en-gb/articles/26470554139025) — read 2026-10-08
- No separate card fee is published. The commission is "the percentage Playtomic charges for managing, processing, and securing payments". **[POLICY]** [Auto-invoice](https://helpmanager.playtomic.com/hc/en-gb/articles/20564491523985) — read 2026-10-06

### Rival vendors' claims about the commission

- Book & Go's German page: "4% fee on every booking (deducted from club revenue)" plus "€59–€279/mo", unsourced. Its English page now says "Commission structure not published" and calls 4 % "hypothetical". **[COMPLAINT]** (rival vendor) [Book & Go DE](https://www.bookandgo.app/de/playtomic-alternative) — read 2026-10-06; [Book & Go EN](https://bookandgo.app/en/compare/playtomic) — read 2026-10-08
- Playbypoint: "Playtomic charges more for bookings made through their marketplace than direct ones", no figures. **[COMPLAINT]** (rival vendor) [Playbypoint](https://www.playbypoint.com/tools/comparison/vs-playtomic) — read 2026-10-08

### The player's service fee, which the club may take on

- The player pays Playtomic a separate fee. "The club may have decided not to apply a service fee directly to you … but have assumed the cost themselves". **[POLICY]** [Legal Conditions §7](https://playtomic.com/legal-conditions) — read 2026-10-06
- Poland: open matches **20 %, between 1,24 zł and 3,99 zł** a seat, and no fee on private bookings. There is a **4,32 zł** cancellation fee on private bookings. **[PRICE]** [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337), [Cancellation fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831791848721) — read 2026-10-06

---

## 9. How and when the club is paid

### Three billing models

- They are the New Billing Model (NBM, the current one), the Old Billing Model (OBM) and the Distribution Model (DM). **[POLICY]** [OBM Guide](https://helpmanager.playtomic.com/hc/en-gb/articles/44898846238609) — read 2026-10-06

### NBM: the club sells, and is paid weekly by payment date, before the game

- "Payments are now processed directly between the player and your club." The money lands in the club's Stripe account net of the fee, and it is paid out "based on the payment date rather than the match date". **[POLICY]** [New Billing Model](https://helpmanager.playtomic.com/hc/en-gb/articles/26436916409361) — read 2026-10-06
- Payouts are "triggered automatically by Stripe every Monday". Card payments take "around 2 business days to settle". **[POLICY]** [First NBM payouts](https://helpmanager.playtomic.com/hc/en-gb/articles/45366964593041) — read 2026-10-06
- The weekly transfer "includes all online bookings paid during those 7 days — even if the match itself takes place later"; refunds come off the next payout, which can go negative and be "withdrawn from your bank account". **[POLICY]** [Negative payout](https://helpmanager.playtomic.com/hc/en-gb/articles/50457368851729) — read 2026-10-06
- Split payments: a pre-authorisation lets "you still receive the full court price". With Card on File, "if it fails, the booking may remain partially unpaid … The club is responsible for following up with the players". **[POLICY]** [New Billing Model](https://helpmanager.playtomic.com/hc/en-gb/articles/26436916409361) — read 2026-10-08

### Distribution Model and OBM: paid twice a month

- In the DM, Playtomic collects the money and pays twice a month: activity of the 1st–15th "by around the 19th", the rest "by around the 3rd". Payment follows "when the activity took place", and matches are paid "after the match has been played". A refund after payout "may [be issued] directly without recovering funds from you". **[POLICY]** [Distribution Model](https://helpmanager.playtomic.com/hc/en-gb/articles/37355604106129) — read 2026-10-06
- In the OBM, payouts are "biweekly, on the 1st and 16th of each month". **[POLICY]** [OBM Guide](https://helpmanager.playtomic.com/hc/en-gb/articles/44898846238609) — read 2026-10-06

### What the club sees of its money

- **Payments** has Processed, Pending ("Voided" for cancelled bookings), Invoices and Payouts, filtered by payment or **service** date, status, method and customer, with CSV export. **[POLICY]** [Payments Section](https://helpmanager.playtomic.com/hc/en-gb/articles/20534669386641) — read 2026-10-08
- A **Payout Summary Report** (PDF) comes "every 7 days" under NBM. It shows transactions, fees, VAT and "the final amount transferred after deductions", with a monthly split. **[POLICY]** [Payout Summary](https://helpmanager.playtomic.com/hc/en-gb/articles/26444788035601) — read 2026-10-08
- The **Payment Collection** report goes by service date and includes "Pending and Preauthorized" amounts, per player. **[POLICY]** [Payment Collection](https://helpmanager.playtomic.com/hc/en-gb/articles/50251519067921) — read 2026-10-08
- "Reports update every hour — they are not real-time", and past figures "can change if you later modify or cancel bookings". **[POLICY]** [Reports](https://helpmanager.playtomic.com/hc/en-gb/articles/43127115602961) — read 2026-10-08

### A payout that fails

- "If the automatic payment fails, we process the payout manually to the bank account saved in Playtomic Manager." The details in Manager and in Stripe "must always match". A bounced payout "is returned to us. It is not lost": the club corrects its details and asks Customer Care to resend it. **[POLICY]** [Payout Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/51376628311441) — read 2026-10-08

### Payment methods: no BLIK, no Przelewy24

- Players can pay by card, prepaid card, Apple Pay (on by default), Google Pay (sometimes on request) and Club Wallet. Local methods exist only in SE, FI, BE/NL, DE and PT. Poland is in no country list. **[POLICY]** + **[ABSENT]** [Payment methods](https://helpmanager.playtomic.com/hc/en-gb/articles/49989481211281) — read 2026-10-06

---

## 10. Invoices and fiscal rules

### Who invoices whom

- Under NBM the club invoices the player for the court when asked. Playtomic invoices the player for its fee and the club for its commission, monthly. **[POLICY]** [New Billing Model](https://helpmanager.playtomic.com/hc/en-gb/articles/26436916409361) — read 2026-10-06
- The optional **Invoicing System** (Champion plan) issues simplified or full invoices and creates credit notes on refunds. "There is no integration with POS printers." **[POLICY]** [Invoicing System](https://helpmanager.playtomic.com/hc/en-gb/articles/24829231088657) (updated 2026-10-08, no change found) — read 2026-10-08

### Nothing for Poland

- Tax pages exist only for Portugal and Mexico. There is no kasa fiskalna export, no paragon fiskalny, no KSeF and no JPK. **[ABSENT]** (157 articles: poland, polish, PLN, zł, KSeF, fiscal) [Portuguese clubs](https://helpmanager.playtomic.com/hc/en-gb/articles/40674001404433) — read 2026-10-06, searched again 2026-10-08

---

## 11. Leaving and pausing

### Leaving takes 30 days and a person

- Cancelling the subscription "does not automatically take your club offline … you'll also need to contact our team", "at least 30 days before". Offline means "no longer visible in the app and won't receive new bookings", and "Your configuration is kept". **[POLICY]** [Cancel subscription](https://helpmanager.playtomic.com/hc/en-gb/articles/50864435573009) — read 2026-10-07
- What happens to bookings already sold, or to the club's Stripe account, is not stated. The closure advice is to cancel by hand. **[ABSENT]** + **[POLICY]** [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097) — read 2026-10-07

### No pause switch

- No club-wide pause is documented. The club has per-court Bookable Online, Holidays, a Book Ahead Limit of 0, and staff who take it offline. **[ABSENT]** (searched pause, temporar, disable online, stop accepting) — read 2026-10-07

---

## 12. What clubs say

### Clubs leaving over data and control

- Rocket Padel and Padium (UK) left "citing a lack of accessibility to their customers"; Padel Shed built its own software to "control our customer journey". **[COMPLAINT]** [Padel Paper 11 Dec 2025](https://thepadelpaper.com/playtomic-soul-padel-data/), [9 Dec 2025](https://thepadelpaper.com/padel-shed-huddersfield-data-on-the-court/) — read 2026-10-06
- A US owner: "I couldn't even get a hold of them." **[COMPLAINT]** (quoted by a rival) [Playbypoint](https://www.playbypoint.com/tools/comparison/vs-playtomic) — read 2026-10-08

### Payouts and double bookings: no first-hand complaint

- No club complaint was found about late or held payouts, negative payouts or double bookings. **[ABSENT]** (Capterra, GetApp, G2, Trustpilot, Spanish and Polish queries; Reddit unreadable) — read 2026-10-06, searched again 2026-10-08

---

## Against Rakieta's club side (summary, no new facts)

Rakieta's side as the spec and `state.json` state it; each line points to a heading above.

- **On request:** none at Playtomic, every booking is instant → *No booking that waits for the club to confirm*
- **Minimum notice, timed release:** neither → *No minimum notice*, *No timed release*
- **Cut-off 24 h default:** private bookings are the club's with no default; open matches fixed at 24 h → *Booking rules*, *Leaving inside 24 hours*
- **No platform fee, club pays the card fee:** subscription plus an unpublished commission that includes processing (example 3.5 %) → *A commission on every online payment*
- **Paid after the game:** NBM pays weekly by payment date, before play, with negative payouts → *NBM*, *Distribution Model and OBM*
- **Club is the seller on its own Stripe account:** same as NBM → *NBM*
- **QR / short-code check-in:** none; door codes skip the desk → *No check-in feature*
- **Club marks no-shows, 24 h dispute:** only players report, to Playtomic, open matches only → *No-shows*
- **Daily new-bookings email:** per-booking emails to each opted-in admin → *Staff logins, roles, and who gets booking emails*
- **Move / Cancel:** club cancel refunds in full; moves same-size only, paid fees fixed → *The club cancels*, *Moving a booking*
- **Instant with the desk selling too:** no double sale, Manager is the only calendar → *Manager is a web app and the club's only calendar*
- **BLIK:** no Polish method → *Payment methods*
