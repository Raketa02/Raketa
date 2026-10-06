# Games and Fill in — the screens

> **Status:** locked 2026-09-29 in the second part of the grilling (Q68–Q96, logged in
> [the mechanics, Appendix C](the-mechanics.md#appendix-c--decision-log)). Recorded by
> [ADR-0189](../../adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md).
>
> **What it is:** how every screen of the feature looks and behaves — the **player app**
> (locked from the product owner's mocks), the **club website** (designed here, confirmed as a
> whole in Q86 and Q95) — and the **backend and seed data** inferred from both. The rules
> themselves are in [the-mechanics.md](the-mechanics.md); where the two disagree on a rule, the
> mechanics win; on a look, this document does.
>
> **How to read the mocks:** they are under [`mocks/player/`](mocks/player/) and
> [`mocks/game-details/`](mocks/game-details/), cited as *mock 12* or *details 8*.
> **The mocks win over the design system and over any earlier record** (the same rule as
> [ADR-0167](../../adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)):
> each departure from `frontend_player/docs/design-system.md` becomes a Part 16 row. **Every
> name, number, price and date in a mock is mock data** — nothing is hard-coded; all of it comes
> from the backend and, for testing, from the seeds ([Part D](#part-d--seed-data)).
>
> **Three corrections to the mocks, ruled in the grilling:** the *vs* line and the balance bar
> always name the same sides (mocks 3, 6, 7 disagree — Q70); a tile has no *asked / no answer
> yet* tag (mocks 4, 5, 6, 8, 10 — Q69); a post that is still filling shows no court number and
> its button reads *I'm in* (mock 35 — Q79).

---

# Part A — The player app

## A1. Where things live

- **Bottom bar:** **Home · ⚡ Play · You**. Home's badge counts games that need you (a result to
  enter or confirm, a payment to confirm, a seat open in your game). **Players** and **Chats**
  were the older loop, hidden behind a *Classic play* flag and then removed on 2026-10-06
  ([#569](https://github.com/Raketa02/Raketa/issues/569)).
- **Group page** (mock 1): header (back, monogram, name, *n members · home club*, the sport pill
  on the right), then the tabs **Games · Fill in · Friends · Info**:
  - **Games** badge — cards where somebody is already In with you (mock 1: *Games 4*).
  - **Fill in** badge — the number of *Seats to fill* rows (mock 11: *Fill in 1*).
- **The Competitive / For fun switch** (mock 9) sits under the tabs on **Games**:
  *Competitive · 7* / *For fun · 1* — the number is the cards of that kind in this group and
  sport. It stays where it is today on **Friends** too (out of scope). A player whose intent is
  one kind sees only that segment; *Either* sees both.

## A2. The Games tab

### A2.1 States

1. **Nothing to deal** — today's cards stay exactly as built: *Just you so far*, *3 of 4*,
   *Nothing picked right now*, with **Share the link** and **Copy link**. *Nothing picked right
   now* gains a third button, **Post a game** (Q96).
2. **No intent for this sport** — the one-time inline question *Competitive / For fun / Either*
   replaces the deck until answered.
3. **Weekly cap reached** — a slim line above the deck: *"Your 2 games this week are booked —
   showing next week"* (Q73).
4. **The deck** (mock 1).

### A2.2 The deck stage

Reuse the **`DeckStage`** the Players deck had — the pan gesture, the stamps, the fly-off,
the arrival animation, the haptic tick — and nothing else of that screen. One change: the two
cards peeking behind the top card **fade as well as shrink** (they used to only shrink) (Q90).
Both now live in `frontend_player/src/features/proposals/components/`, since the Players deck was
removed (#569). The three buttons under the card are `DeckAnswers`: **✕** (= swipe left), **i** (= the game
details), the coral ball (= swipe right).

- **Swipe right / the ball** — yes. **Swipe left / ✕** — no.
- **Tap a player tile** — that player's record (the existing `PlayerRecordSheet`).
- **Tap anywhere else on the card, or i** — the game details ([A4](#a4-game-details)).

### A2.3 The card (mocks 2–8, 10)

Dark card, top to bottom:

| Part | What it shows | Rules |
| --- | --- | --- |
| **Ribbon** | *Picked for you* (dark teal) · *Kuba challenged you* / *The group challenged you* (dark teal) · *Seat open · court booked* (**coral**) | No *· friendly* — the segment already says it. On the right, **⏱ 21 h 00** only when the deadline is under 24 h (book-by; for a rescue the cut-off, then the start); *45 min* under an hour, coral. At the deadline the card leaves silently. |
| **Tiles** | 2 × 2 for doubles, 1 × 2 for singles (mock 10): photo or generated poster, the player's **Name** (cut short visually, never an invented first name — ADR-0171; the mocks' *Karol T.* is mock data), level | **IN** tag (green outline) on a player who said yes. **FRIEND** (volt) only once a friends feature exists (Q68). No other tag. On a rescue each player reads *2,75 · paid*. |
| **Your tile** | *You*, your level | When your yes would fill the game: **You complete it** in volt (mocks 3, 7). On a rescue your seat is the **dashed** tile: *You complete it · 27 zł · court booked* (mock 2), or *You? · 27 zł* when more than one seat is open. |
| **vs line** | *KAROL + YOU VS ANIA + KUBA* | The top row is one side, the bottom row the other (Q70). |
| **Balance forecast** | percentage (green / amber / red by today's tones) + the bar | The bar names **the same sides as the rows, your side on the left** (light half). Computed for this version. Existing `BalanceBar`, `onDark`. |
| **Overlap grid** | *High / Good / Slim overlap* over 7 day columns × 3 range rows | Ranges **Morning 07–12 · Afternoon 12–17 · Evening 17–23**. Bright volt = everyone on the card free for at least one whole hour in the range; dim olive = all but one; dark = fewer. The game's range is ringed in coral. Today's column letter is white. Label colours: volt for High and Good, amber for Slim. |
| **Court block** | state tag · share (volt, mono) · *Saturday 16:00 · Ogrody 33* (+ *· Court 6* once booked) | Tag: **Court available** (grey — your yes is a free vote; dashed block border), **Book it now** (green — your yes fills it and charges everyone after the undo, or at an On request club once the club confirms; solid green border), **Booked** (volt — a rescue; solid border). *Tomorrow* / *Today* for near days. **no free cancellation** in amber after the club's cut-off (mock 6). |
| **Stamps** | **I'M IN** (right) / **NOT THIS TIME** (left), fading in while dragging | **I'M IN · 32 zł** whenever the yes charges at once: *Book it now* or a rescue (Q72). At an On request club the charge waits for the club, so its *Book it now* stamp carries no price. |

**Per type:**

- **Picked for you** — fresh cards have no IN tags; tags appear as yeses land, and the card
  climbs the deck.
- **Challenge** — the poster always carries IN (posting was their yes). Otherwise it behaves like
  a pick, and outranks one at the same momentum.
- **Seat open** — players *paid*, the dashed seat with your share, the court number, **Booked**.
  A yes pays at once.

**Singles** (mock 10) follow the same rules with two tall tiles and no *vs* line.

**A game dealt in versions** ([the mechanics §7](the-mechanics.md#7-one-game-several-versions))
is not a card type: the card is the same, plus one line under the tiles — *4 people are In on
this game* — counting the yeses on every version.

### A2.4 What happens when you swipe

| You swipe… | On… | What happens |
| --- | --- | --- |
| right | a card that won't fill | Your tile gains IN for the others; the card leaves your deck; the yes appears in **Fill in › You're In**. Nothing charged. |
| right | *Book it now* | Toast **"Booking in 10 s · Undo"** with a draining ring. At zero: everyone charged together → **It's a game!** At an On request club, at zero the game goes to the club (*waiting for the club*); the charge and **It's a game!** follow when it confirms ([the mechanics §11](the-mechanics.md#11-the-moment-a-game-fills)). |
| right | a rescue | The same toast; at zero your share is charged → **It's a game!**; the game is in **Home**. |
| right | without a saved method | The **payment setup** ([A7.3](#a73-payments)) opens as a sheet; the yes lands when it finishes, or is dropped if you close it. |
| left | anything | The card leaves; silent; never on your record. |

- **It's a game!** — today's yes screen (ADR-0167): full screen, the faces, the one word *It's a
  game!*, **Open game** and **Later**. Shown to the player whose action filled it.
- **A payment that fails at the fill** — toast *"Your payment didn't go through — confirm it to
  keep your seat"* and the notice of the same name ([A9](#a9-notifications-delivery)).

## A3. Fill in (mock 11)

Paper background; sections only when they have rows; the coral **+ Post a game** FAB (mock 14)
floats bottom-right, always.

### A3.1 SEATS TO FILL · N — the rescue row (mock 12)

Coral 1.5 pt border.

- **Title** — *Padel · Saturday 16:00* (+ *· friendly* for For fun). Tap the upper block → the
  rescue's details (non-member view, [A4.3](#a43-a-rescue-seen-from-outside-q96)).
- **Subtitle** — *Ogrody 33 · **fills by Fri 16:00*** before the cut-off; *Ogrody 33 · **offered
  until the start*** after it. Switches by itself at the cut-off.
- **Squares** — the booked players' small posters, then one dashed **?** per open seat. Long-press
  a poster → record.
- **I'm in · 27 zł** (volt) — takes the seat: the 10-second undo, the charge, **It's a game!**,
  and the game is in Home. Lost race → toast *"Someone just took it"*.

### A3.2 YOU'RE IN · N — your row (mock 13)

Mint 1.5 pt border. Picks, challenges and posts — never rescues (Q76).

- **Title** — *Padel · Saturday 15:00*. Tap → the game's details (filling view).
- **Subtitle** — *Bonarka Arena · **book by Saturday 13:00***; while an On request club decides,
  the bold part is amber ***waiting for the club***.
- **Squares** — filled posters for everyone In (you included), dashed empties for the open seats.
- **Withdraw** (red text, outlined) — free and silent. On your own post: if others are In the
  game carries on without you; if not, the post disappears. Hidden while *waiting for the club*.

## A4. Game details

One screen (details 5–10, from Part 1), three readers.

### A4.1 A booked game you're in (details 5–10)

- **Top bar** (details 7) — back · the other players' faces overlapping (up to three) · their
  names as the title · *Padel · booked* · **Chat · 2** on the right (volt when unread) while
  the game isn't over.
- **The game card** (details 8) — status tag (dot + word), tiles with *paid*, the *vs* line, then
  the court facts on an accent line in the status colour: **WHERE** *Bonarka Arena · Court 2 ·
  3,1 km* · **DAY** *Sunday 20 Sep* (*· next week* beyond seven days) · **TIME** *10:00 until
  11:00* · the money row (*PAID · 28 zł · your share · to the club*; before the cut-off:
  *· free to leave until Sat 10:00*).
- **Balance forecast** (details 9) — as built today; hidden while a seat is open.
- **Show at the desk** — on the day only: a QR code and a short code under it.
- **Leave the game** (details 10) — outlined, red text; the line under it states the cost for
  the moment ([the mechanics §13](the-mechanics.md#13-leaving-a-game)); the confirmation sheet is
  today's *Before you leave* sheet with the new words.

### A4.2 A game still filling (Q75)

Same layout. Status *Filling · 2 of 4 in* (or *Waiting for the club*, amber); tiles with IN tags;
WHERE shows the club and distance, no court number; the money row reads *30 zł if it fills · book
by Sat 13:00*; the **overlap grid** follows the forecast; then one plain paragraph: *"Your yes
costs nothing until everybody is in. When the last yes lands, everyone's share is charged together
and the court is booked."* Actions at the bottom: **I'm in** / **Not this time** if you haven't
answered, **Withdraw** if you're In — while *waiting for the club*, **Leave the game** with its
sheet ([the mechanics §13](the-mechanics.md#13-leaving-a-game)). No Chat.

### A4.3 A rescue seen from outside (Q96)

The booked layout with the dashed *You?* tile, the court number, *Paid* players, and a volt
**I'm in · 27 zł** at the bottom. No Chat, no Leave.

### A4.4 The chat

The conversation screen, which lost its plan card and Details button with the old loop; the back
chevron returns to the details. Opens when the game is booked; members are the current line-up;
system lines *"Kuba left — the seat is open"* and *"Ola took the seat"*.

## A5. Post a game (mock 15)

Full screen over the group, scrolling; the bottom bar stays visible. Back chevron → Fill in, the
draft kept while you stay in the group.

### A5.1 The controls (mocks 16–19)

| Section | Control | Behaviour |
| --- | --- | --- |
| **SPORT** | chip row, each with its sport colour dot and the count of group members rated in it (*Padel 10*) | Only sports you're rated in that the group plays. Selecting resets the level range and clears the pick. Rated in none: *"Get rated in padel to post here"* with a link to the questionnaire (Q80). |
| **KIND** | *Competitive* / *For fun · friendly* | Defaults to your intent. Re-filters the fits; the grid updates live. |
| **WHO** | *Anyone / Men / Women / Mixed pairs* | *Mixed pairs* only for padel and badminton. Men / Women / Mixed count only members with a gender set; nobody whose own preference excludes the game is ever dealt it. |
| **LEVEL** · *narrow it, not widen it* | two steppers | Seeded with **the engine's range for the kind** around your level (Q78). − / + move a bound 0,05 inward only; pushing outward bounces with *"You can narrow it, not widen it"*. |

### A5.2 WHEN — the grid (mocks 2-, 20–32)

- **Header** — *WHEN* · the **ⓘ** button (toggles the legend popover, mock 20) · **‹ This week ›**
  (mock 21): week one starts today; the back chevron is disabled on week one, forward on week two.
- **Columns** — seven days from today; *Today* in coral with its date.
- **Rows** — *Morning 07:00–12:00*, *Afternoon 12:00–17:00*, *Evening 17:00–23:00* (the mocks'
  08–12 and 17–22:30 are superseded by Q71).
- **The number in a cell** — how many of your best fits are free **together with you** at the
  **best hour** in that range that has a free court (Q92). *5+* caps it.

| Cell | Look | Means | Tap |
| --- | --- | --- | --- |
| **Dead** (mock 24) | warm grey, no number | Nobody who fits is free then | Sheet: *"Nobody who fits is free then"* |
| **Few, no court** (mock 25) | palest mint `#E2F3EC`, green number | Some fits, fewer than the open seats; no court | Sheet: every game needs a court |
| **Enough, no court** (mock 26) | light green `#A9DEC5`, white number | A full game's worth; no court | Same |
| **Court, thin** (mock 27) | mid green `#5EC39B`, white number + court glyph | A court; fewer fits than the open seats | Pickable; the sheet warns *"only 2 fit · may not fill"* |
| **Hot** (mocks 23, 28) | full mint `#0C8F6B`, volt ring, white number + court glyph | A court and a full game's worth | Pickable |
| **Outside your hours** (mock 29) | the same, dimmed, dashed border | Your own week doesn't cover it | Pickable if it has the glyph; headline adds *· outside your hours* |
| **Past** (mock 30) | 15 % opacity | Earlier today | Inert |
| **Your pick** (mock 31) | dark outline + white ✓ badge | The hour and court in the post | Reopens its sheet (change court, *Remove this pick*) |
| **Happening here** (mock 32) | red dot top-right | A post still filling **or** a booked game short of a player (Q93) | The sheet lists them first |

"Open seats" = the seats minus you: 3 in doubles, 1 in singles.

**The legend** (mock 20), with its red-dot line changed to *"A game already happening there —
posted, or a booked game missing a player. Tap to see it."*

### A5.3 The slot sheet (mocks 34, 35)

A bottom sheet (on `ModalStage`, never a React Native `Modal`):

- **Title** — *Saturday evening*.
- **Headline** — a mint count badge + *"5 of your best fits free then"* · *"only 2 fit · may not
  fill"* · *"Nobody who fits is free then"* (+ *· outside your hours*).
- **The fits** — horizontal cards (poster, level, name, *2,75 · 93*); tap → record.
- **FREE COURTS · HOME CLUB FIRST** — one row per free court hour: the hour (mono), the club,
  *2,4 km · 27 zł if it fills · book by Saturday 15:00*, its own *"4 free"* (Q77), and *27 zł
  each*. Tap → picks it (ring + ✓ on the cell); a new pick replaces the old.
- **ALREADY HAPPENING HERE** — first **rescues** you fit (*Padel · Sunday 20:00*, *Kuba · Centrum
  Ruchu · Court 2 · 30 zł each*, the squares, *any level ✓ · you are free ✓*, **I'm in · 30 zł**);
  then **posts still filling** you fit (no court number, **I'm in**) (Q79, Q93).

### A5.4 Post — you're In (mock 33)

Full-width coral button, disabled (pale) until a court is picked, with the helper *"Pick an hour
with a court on the map first."* Tapping it: your yes is recorded, up to three versions are
dealt as *"[You] challenged you"* cards, their *Challenges for you* alert fires, and you land on
**Fill in › You're In**. Guards, each shown under the button in place of the helper: no saved
method (the setup opens), two live posts already, games per week already booked that week.

## A6. The You tab: Your week (mock 36)

In *Finding players*, and the same component in onboarding (replacing today's 7 × 3 step).
**7 day columns (MON…SUN) × 16 hour rows (07:00…22:00)**, each cell one hour; mint = free. **Tap**
toggles; **press and drag** paints (or clears, if the first cell was on) a run. At least one hour
to continue in onboarding; *Save your week* on the You screen as today. No templates.

## A7. The You tab: the Account group

A new group, **ACCOUNT**, after *On your card* and before *Sign out* (mocks 37, 40, 50):

| Row | Subtitle |
| --- | --- |
| **Games & money** | *At most 4 games a week* (+ *· up to 180 zł* when a ceiling is set) |
| **Payments** | *Card •••• 4312* · *Google Pay* · *Not set up* |
| **Notifications** | the choices that are on: *You complete it · Challenges · Fill in alerts* |

### A7.1 Games & money (mocks 38, 39)

Back chevron + title; changes save as you tap.

- **Games per week** · *Mon–Sun · 1 to 7* — stepper **− 4 +**, clamped; the line *"Once they are
  booked, your other yeses that week pause — they come back if a game is called off."* (singular
  at 1).
- **Most I'll pay per game** · *Off by default* — chips **Off · 35 zł · 45 zł · 60 zł**; the line
  *"Every card is shown, whatever its share."* or *"Cards above 45 zł are never shown to you."*
- **The bound** — *"Your bound: at most **4 games** a week."*, or *"… at most **4 games** · up to
  **180 zł** a week."* with a ceiling.

### A7.2 Notifications (mocks 52, 53)

- **ALWAYS ON** — seven inert rows with a green **on** tag: *It's a game! · you paid* · *Confirm
  your payment to keep your seat* · *Game called off · with the refund* · *Someone left your
  game* · *You've been refunded* · *The club confirmed / couldn't take it* · *Your post didn't
  fill*.
- **YOUR CHOICE** — three rows with a working **On / Off** chip: *You complete it* (on; *A card
  needs only you · at most 1 a day, bundled*), *Challenges for you* (on; *A member's post names
  you · at most 3 a day, bundled*), *Fill in alerts* (off; *A booked game you fit needs one more ·
  at most 3 a day*).
- The first time the screen opens on a phone that hasn't granted notification permission, a
  line at the top offers **Allow notifications**.

### A7.3 Payments

**State A — nothing saved** (mocks 41–45): one card, a numbered checklist; the current step
open, finished steps collapsed to a green ✓ (step 1 keeps the method's name on the right), the
rest grey. **The order is changed from the mocks** (Q82):

1. **Choose how you pay** — chips *Card · BLIK · Apple Pay* (iPhone) or *Card · BLIK · Google
   Pay* (Android); **Continue**. BLIK selected: *"BLIK launches when Stripe confirms saved BLIK —
   pick a card or wallet for now."* and Continue stays disabled (mock 42).
2. **Card details** (mock 43) — Stripe's own card fields styled as the mock (number, MM/YY, CVC);
   **Save the card** continues. A wallet skips this step.
3. **Accept the terms** (mock 45, moved up) — the text of
   [the mechanics §12.5](the-mechanics.md#125-saving-a-payment-method-and-the-terms), compressed;
   **Accept and continue**.
4. **Confirm with your bank** (mock 44, moved down) — *"One-time 3-D Secure check — it lets the
   club charge your share later without you present."*; **Open the bank app · confirm**. This step
   saves the method; when the bank asks nothing, it ticks by itself and the screen moves to state
   B.

**State B — saved** (mocks 46–49):

- **The method card** (dark) — brand badge (*VISA*, *GPay*, …), *Card •••• 4312*, *Charged by the
  club when a game fills*, **Change** (reopens the setup; the old method keeps working until the
  new one is saved). Under it a small **Remove this method** link, refused with its reason while
  anything is live (Q83).
- **LIVE YESES · 3** — every live yes, with no cap (the mechanics Q97); rows *Padel · Saturday 15:00 ·
  Bonarka Arena* with the share in grey; tap → the game's details. Hidden when empty.
- **RECEIPTS** — newest first; ✓ grey circle for a charge (*−28 zł*, dark), ↩ mint circle for a
  refund (*+26,58 zł*, mint — the 28 zł less its 1,42 zł card fee); the **club's name** as the
  title, *Padel · Today · 16:00* under it.
  Empty: *"Nothing yet — charges and refunds land here, with the club named as the seller."*
  Footer when there are rows: *"Refunds: BLIK within hours · cards up to two weeks."*

## A8. Home

The rail of game cards that was *Now*, renamed **Home**, showing the statuses of
[the mechanics §14.1](the-mechanics.md#141-home-and-the-statuses): **Waiting for the club**
(amber), **Booked** (mint), **Seat open** (amber), the result statuses as today, **Called off**
(red) — each with its money line. **Open game** → [A4.1](#a41-a-booked-game-youre-in-details-510),
where the chat is reached — a Home card has no chat door
([the mechanics §14.3](the-mechanics.md#143-the-chat)). Games that filled since you last looked
are marked *new*.

## A9. Notifications delivery

| Notice | Push | In-app banner + recent list | Email |
| --- | --- | --- | --- |
| It's a game! · you paid | ✓ | ✓ | ✓ (booking confirmation) |
| Confirm your payment to keep your seat | ✓ | ✓ | ✓ |
| Game called off · with the refund | ✓ | ✓ | ✓ |
| You've been refunded | ✓ | ✓ | ✓ |
| Someone left your game | ✓ | ✓ | — |
| The club confirmed / couldn't take it | ✓ | ✓ | — |
| Your post didn't fill | ✓ | ✓ | — |
| You complete it · Challenges for you · Fill in alerts | ✓ if on | ✓ if on | — |

Push goes through Expo's push service. Tapping a notice opens the game it is about (the deck
opens with the card on top for *You complete it* and *Challenges*). The recent notices are a
list reached from a bell on Home. Emails go through the existing mailer (ADR-0186).

## A10. Design-system work (Part 16 rows)

- **New colours** — the grid's two middle greens: `#A9DEC5` (*light green*) and `#5EC39B` (*mid
  green*), each with its Soft / Ink / Line and contrast per §15.2. `#E2F3EC` is `mintSoft`,
  `#0C8F6B` is `mint`.
- **New components** — the game card (dark, three types), the mini overlap grid, the court block
  with its three tags, the Undo toast with a draining ring, the rescue and You're In rows, the
  posting grid cell (nine states), the slot sheet, the hour grid (7 × 16), the numbered setup
  checklist, the method card, the receipt row, the on/off chip.
- **Changed** — peeking deck cards fade; the group page's Competitive / For fun switch appears on
  Games; the You tab gains *Account*; the bottom bar loses Players and Chats (removed, #569).
- **Sport colours** as today: padel coral, tennis mint, squash night2, badminton amber.

---

# Part B — The club website

Designed in this document (the product owner delegated it; confirmed in Q86, Q95). Built on the
existing frame: **the top bar**, `src/ui/tokens.css`, the `Form` primitive, the three server
doors. Clean and minimal: one task per page, one primary button per section.

## B1. The top bar

**Overview · Bookings · Courts & prices · Money · Groups · Administrators**, and on the right the
club's name opening a menu with **Details** and **Raketa settings**. A coral count badge on
Bookings while something waits for an answer.

## B2. Overview

- **Until the club is live — the setup checklist.** Five rows, each with its state (done ✓ /
  next / locked) and one button:
  1. **Connect payments** → *Connect with Stripe* (Stripe's hosted sign-up; back to Overview).
     States: *not started*, *Stripe needs more details* (with *Continue with Stripe*), *ready*.
  2. **Choose how you work with Raketa** → the choice page ([B5](#b5-raketa-settings)).
  3. **Add your courts** → Courts & prices.
  4. **Set hours and prices** → Courts & prices, the week grid.
  5. **Check the settings** → Raketa settings, **Confirm settings**.
  When the fifth is done: a one-time line *"You're live — your courts can now be booked through
  Raketa"*, and the checklist is gone.
- **After that — waiting for your answer**: the On request bookings with their countdown and
  Accept / Refuse, and any *Stripe needs something from you* notice. When nothing waits: *"Nothing
  is waiting for you."* (The statistics that will live here are out of scope.)

## B3. Courts & prices

Three sections on one page.

- **Courts** — a table: name · sport · indoor/outdoor · on/off · edit. **Add a court** opens a
  small form (name, sport from the club's sports, indoor/outdoor). A court with future bookings
  can be switched off but not deleted; switching it off asks to confirm and lists what is booked.
- **Weekly hours for Raketa** — a court picker (tabs per court, or *All courts of a sport*), then
  the same **7 × 16 hour grid** as the player's week (07:00–23:00 — an hour outside it could
  never match a player), tap or drag to paint the hours offered to Raketa. **Copy to other courts** copies one court's
  pattern. Saved with **Save hours**.
- **Exceptions** — a list (*Tournament · 4–5 Oct · all courts*, *Repair · Court 2 · 12 Oct
  09:00–12:00*) with **Add an exception**: what (all courts or some), when (a date, a range, or
  hours on a date), a reason for the club's own records. An exception over an hour with cards on
  it is allowed (the cards move or disappear); over a booking it is refused with *"Court 2 is
  booked then — cancel the booking first"* and a link to it.
- **Prices** — per sport: a **standard price per court-hour**, plus optional **price bands**
  (weekday / weekend × a time range, e.g. *Weekdays 17:00–22:00 · 140 zł*). A preview line shows
  the share: *"140 zł ÷ 4 = 35 zł each"*. New prices apply to new cards only, and the page says so.

## B4. Bookings

- **One day at a time**: *‹ Today ›* with a date picker; filters **All · Waiting for you · Seat
  open · Called off**. **Check in** button at the top right when the club checks players in.
- **Row** (per booking): time + court + sport + kind · the players (name, *paid ✓*, *checked in
  ✓*) · status tag · money (court price, collected, refunded) · the group it came from · actions:
  - **Waiting for you** → **Accept** / **Refuse** with the countdown; Refuse asks for an optional
    reason.
  - **Booked / Seat open** → **Move** (a dialog listing the free courts of that sport at that
    hour; players see the new number) and **Cancel** (a dialog: reason *weather · repair · double
    booking · other*, the consequence spelled out — *"Everyone is refunded in full; the card fees
    are not returned"* — and **Cancel the booking**). Not possible after the start.
- **Empty day**: *"No Raketa bookings on this day."*

## B5. Raketa settings

One page, one form, **Save settings**:

- **How you work with Raketa** — three radio cards (Only Raketa / Instant / On request), each with
  two lines of what it means; changing it applies to hours not yet booked.
- **Release lead** (Only Raketa) · **Minimum notice** (Instant, On request) · **Time to confirm**
  (On request) · **Free-cancellation cut-off** — number fields with their defaults.
- **Other clubs' courts for our groups** — on/off + distance (default 10 km).
- **We check players in** — on/off.
- **Pause Raketa bookings** — on/off with its consequence line.
- **Leave Raketa** — a text link at the bottom, refused while anything is booked or unpaid.

## B6. Check in

Opens the device camera in the browser; a scanned code shows the booking (*19:00 · Court 2 ·
Padel*) and the player (*Piotr S. — checked in ✓*). A field below takes the **short code** by hand.
Wrong day or club: *"This code is for another day"* / *"… another club"*. Already scanned:
*"Checked in at 18:52"*.

## B7. Money

- **Bookings** — a table for a chosen month: date · court · collected · refunded · card fees ·
  net; totals at the top.
- **Payouts** — date · amount · status, from Stripe.
- **Open your Stripe dashboard** — a button to the club's full Stripe dashboard (disputes,
  bank details, tax documents).

## B8. Groups (changed)

The *Games* column counts the games booked in each official group. A line above the table links
to the *other clubs' courts* setting.

## B9. Emails to the club

Through the existing mailer (ADR-0186): *A booking is waiting for your answer* (at once, with the
countdown and a link), *New bookings today* (a daily summary), *A game was called off at the
cut-off — the hour is free again* (at once), *A payout was sent*, *Stripe needs something from
you* (at once).

---

# Part C — The backend, inferred

The shape is ADR-0189 §5. What each app needs from it:

## C1. Aggregates and their events (all event-sourced)

- **Club courts** (Clubs, per club): `CourtAdded`, `CourtChanged`, `CourtSwitchedOff/On`,
  `RaketaHoursSet` (per court, weekly hours), `ExceptionAdded/Removed`, `PricesSet`,
  `WayOfWorkingChosen`, `RaketaSettingsChanged`, `StripeAccountLinked`, `StripeAccountStatusChanged`,
  `RaketaPaused/Resumed`.
- **Proposal** (Proposals, per proposed game): `ProposalMade` (origin: pick | post; pool, sport,
  kind, who, level range, club, start, share, book-by), `VersionDealt`, `YesSaid`, `YesWithdrawn`,
  `NoSaid`, `ProposalFilled` (the people and sides), `ProposalExpired`, `ProposalWithdrawn`,
  `CourtHourLost` (the last court at that club and hour went; the people In are re-dealt first).
- **Booking** (Bookings, per filled proposal): `BookingRequested` (On request) /
  `BookingAccepted` / `BookingRefused` / `BookingTimedOut` / `RequestWithdrawn` (a player left
  while it waited), `BookingConfirmed` (court number,
  seats, cut-off), `CourtMoved`, `SeatLeft`, `SeatRescued`, `CalledOffAtCutOff`,
  `CancelledByClub`, `PlayerCheckedIn`, `BookingPlayed`. It opens the ordinary **Game** on
  confirmation — the only thing that opens one since the old loop was removed (#569); the
  no-show report lives on the Game.
- **Payment method** (Payments, per player): `MethodSaved` (Stripe customer and method ids, brand,
  last four, wallet), `TermsAccepted` (version, time, IP), `MethodChanged`, `MethodRemoved`,
  `BrandChanged` (asks again).
- **Seat charge** (Payments, per seat per booking): `Authorised`, `Captured`, `Failed`
  (`authentication_required` / declined), `Cancelled`, `Refunded` (amount, fee withheld),
  `Disputed` — each folded from a Stripe webhook, idempotently.
- **Notification preferences** (Notifications, per player): `ChoiceSwitched`,
  `DeviceTokenRegistered/Removed`.
- **Player profile** (grows): `WeeklyHoursSet` replaces the 7 × 3 availability.

## C2. Read models

Per reader, never stored as aggregates: the **group deck** (cards addressed to you, ordered by
[the mechanics §8.2](the-mechanics.md#82-the-order), filtered by games-per-week and most-I'll-pay),
**Fill in** (Seats to fill you fit and are free for; You're In), **Home**, **Payments** (live
yeses across pools, receipts), the **posting grid** (per range: best-hour count, court
availability, happening-here), the **slot sheet**, the club's **Bookings**, **Money** and the
**setup checklist**. Court-hour availability is derived from Club courts + bookings + live
proposals' needs, per club and hour.

## C3. Jobs

- **The proposer** — continuously, per pool and sport: free court hours × free fitting members →
  proposals. *Fitting* is the pair rule (`PlayerFit`: blocks, mutual gender preference, the level
  window), and the most even four is read off the balance forecast — no ranking or score
  ([the mechanics §5.1](the-mechanics.md#51-what-it-does)); distance only picks a group's clubs.
  Deals versions at half-In and after every no. Respects games-per-week, most-I'll-pay and one
  card per people-set per batch.
- **Book-by expiry** — expires unfilled proposals; tells posters.
- **The cut-off** — at each booking's cut-off: still short → called off, refunds; full → nothing
  (money already taken).
- **On request timeout** — expires unanswered requests.
- **Rescue dealing** — on every `SeatLeft`: Seats to fill, Seat open cards, Fill in alerts.
- **Notifications** — caps and bundling (1 / 3 / 3 a day), push through Expo, email through the
  mailer, in-app list.
- **Stripe webhooks** — one endpoint for the platform and one **Connected accounts** endpoint
  (direct-charge events arrive there only); deduplicated by event id.

## C4. The contract (proposed paths; the tickets settle them)

- **Player surface** — `GET /pools/{id}/deck?sport&kind`, `POST /proposals/{id}/yes`,
  `POST /proposals/{id}/no`, `DELETE /proposals/{id}/yes`, `GET /pools/{id}/fill-in?sport`,
  `POST /bookings/{id}/seats` (rescue join), `POST /bookings/{id}/departure` (leave),
  `GET /pools/{id}/posting-grid?sport&kind&who&level_min&level_max&week`,
  `GET /pools/{id}/posting-grid/slot?…`, `POST /pools/{id}/posts`, `GET /proposals/{id}`,
  `GET /bookings/{id}` (details incl. the check-in code), `GET /home`, `PUT
  /players/me/weekly-hours`, `GET/PUT /players/me/games-and-money`, `GET/PUT
  /players/me/notifications`, `POST /players/me/devices`, `POST /players/me/payment-methods/setup`
  (a SetupIntent — its id, never its secret), `POST /players/me/payment-methods/terms` (answers
  the secret), `POST /players/me/payment-methods/confirmation`, `GET` and `DELETE
  /players/me/payment-methods/current` (settled by #536, ADR-0190), `GET /players/me/payments`
  (live yeses + receipts),
  `POST /seat-charges/{id}/confirmation` (recovery).
- **Club surface** — `GET/POST/PATCH /club/courts`, `PUT /club/courts/{id}/hours`,
  `GET/POST/DELETE /club/exceptions`, `PUT /club/prices`, `GET/PUT /club/raketa-settings`,
  `POST /club/stripe/onboarding-link`, `GET /club/setup`, `GET /club/bookings?date&filter`,
  `POST /club/bookings/{id}/acceptance|refusal|move|cancellation`, `POST /club/check-ins`,
  `GET /club/money?month`, `GET /club/payouts`.
- **Webhooks** — `POST /api/v1/webhooks/stripe` (built by #536, on no client's contract —
  ADR-0190 §4), `POST /api/v1/webhooks/stripe-connect`.

## C5. Data that must scale to a city

A **pool** is a table of its own (kind: group now, city later) and every proposal, card and post
carries its pool id; nothing joins through a group. Court hours, proposals and bookings are indexed
by club and start time; clubs by point; players' weekly hours by weekday and hour. All times are
stored in UTC and shown in Europe/Warsaw.

---

# Part D — Seed data

Seeds drive the real use cases only (ADR-0029; `backend/app/seeds/`), with the **fake payments
adapter**, and **nothing a mock shows is hard-coded**. On top of today's cohort and groups:

- **Clubs** in all three ways of working, with courts per sport, weekly Raketa hours, one
  exception, price bands, a linked (fake) payments account; one club **not live** (half its
  checklist done) and one **paused**.
- **Members** with hourly weekly hours, spread so the posting grid shows every cell state.
- **For a protagonist**, in one group and sport: fresh picks; picks with 1, 2 and 3 In (one *Book
  it now*); a challenge with momentum and one whose poster withdrew; rescues before and after the
  cut-off; a post of their own in You're In; a game waiting for an On request club; booked games
  (one before, one after the cut-off, one on the day with a check-in code); a called-off game;
  receipts and a refund; a week at the games-per-week cap; a card above a price ceiling (for the
  filter).
- **Screens assertions** (`seeds/screens.py`) extended so the seed fails if the deck, Fill in, the
  posting grid, Payments or the club's Bookings would be empty for the protagonist.

---

# Part E — The mocks

| File | Shows |
| --- | --- |
| `player/1-games_tap_general_view.png` | The group page on Games: header, tabs with badges, switch, deck, buttons |
| `player/2_game_card_seat_open.png` | A rescue card |
| `player/3_game_card_picked_for you_1.png` | A pick you complete (*Book it now*) |
| `player/4_game_card_challenge.png` | A challenge (*Kuba challenged you*) |
| `player/5_game card_picked_for_you_2.png` | A pick with one In |
| `player/6_game_card_picked_for_you_no_friends.png` | A fresh pick, countdown, no free cancellation |
| `player/7_games_card_picked_for_you_no_friend_you_lat_in.png` | A pick you complete, no friends |
| `player/8_picked_for_you_no_friends_not_all_in.png` | A pick with one In, no friends |
| `player/9_competitive_forfun_tap.png` | The switch |
| `player/10_game_card_singles.png` | A singles pick |
| `player/11_fill_in_tap_general.png` | Fill in with both sections and the FAB |
| `player/12_fill_in_sets_to_fill_row.png` | The rescue row |
| `player/13_fill_in_youre_in_row.png` | The You're In row |
| `player/14_post_game_button.png` | The FAB |
| `player/15_post_a_game_screen_general.png` | The posting screen |
| `player/16`–`19` | Sport, kind, who, level |
| `player/2-_when_grid.png`, `20`–`22` | The grid, its legend, its pager |
| `player/23`–`32` | The cell states |
| `player/33_post_game_button.png` | *Post — you're In* |
| `player/34`, `35` | The slot sheet, without and with *Already happening here* |
| `player/36_you_grid_availability.png` | *Your week*, hours |
| `player/37`, `40`, `50` | The Account group's rows |
| `player/38`, `39` | Games & money |
| `player/41`–`45` | Payments, state A |
| `player/46`–`49` | Payments, state B |
| `player/52`, `53` | Notifications |
| `game-details/5`–`10` | The booked game's details (Part 1) |
