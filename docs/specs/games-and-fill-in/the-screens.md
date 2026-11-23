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
>
> **A later ruling the mocks predate (Q124):** a yes that moves money says *Pay* — its stamp
> *PAY · 32 zł*, its buttons *Pay 27 zł*, a post's last seat included — and a vote's stamp carries
> the share, *I'M IN · 32 zł*. Wherever a mock prints *I'm in · 27 zł* on a button, read *Pay 27 zł*.
>
> **A later ruling the mocks predate (Q125):** a group page has three tabs, *Games · Fill in · Friends*, and the group's
> header opens *Info* as its own screen ([A1](#a1-where-things-live)). Wherever a mock draws a fourth
> tab, *Info*, read three. *(Four since PRD #844, below; Info is still not one of them.)*
>
> **A later ruling the mocks predate (Q126):** a player is named by their **nickname**, never with
> an @ ([ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)), so wherever a mock prints a name — *Karol T.*, *Oscar
> Bertran* — read a nickname. And a level is asked where play begins: a member rated in nothing
> meets one door on a player group's tabs, Post a game and Members, which no mock draws
> ([A1](#a1-where-things-live), [A2.1](#a21-states)).
>
> **A later ruling the mocks predate (Q127):** the Competitive / For fun switch always shows both
> kinds, and the kind the player's intent doesn't want is a dimmed door to changing it. No mock
> draws the door, its panel or the finding state ([A1](#a1-where-things-live), [A2.1](#a21-states)).
>
> **A later decision the mocks predate (PRD [#844](https://github.com/Raketa02/Raketa/issues/844),
> 2026-11-23; decided, built by [#847](https://github.com/Raketa02/Raketa/issues/847)–[#850](https://github.com/Raketa02/Raketa/issues/850)):**
> a group page has **four** tabs, *Games · Fill in · You’re in · Friends*. Fill in
> holds only the rescues, You’re in the player's own live yeses, neither has a section heading, and
> **+ Post a game** floats on You’re in. Wherever a mock draws Fill in's two sections or the button
> over Fill in (mocks 11 and 14), read two tabs ([A3](#a3-fill-in-and-youre-in)). **A tab's badge
> counts what the player hasn't seen, and the tab on screen draws none** ([A1](#a1-where-things-live),
> [ADR-0208](../../adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md)):
> wherever a mock draws a badge on the selected tab (mocks 1 and 11), read none.
> The split's own mocks, its decision log and its two overrides are in
> [`docs/specs/fill-in-split/`](../fill-in-split/README.md), cited as *split mock 1* to *3*.

---

# Part A — The player app

## A1. Where things live

- **Bottom bar:** **Home · ⚡ Play · You**. Home's badge counts games that need you (a result to
  enter or confirm on a Competitive game, a payment to confirm, a seat open in your game). **Players** and **Chats**
  were the older loop, hidden behind a *Classic play* flag and then removed on 2026-10-06
  ([#569](https://github.com/Raketa02/Raketa/issues/569)).
- **Group page** (mock 1): header (back, monogram, name, *n members · home club*, the sport pill
  on the right), then the tabs **Games · Fill in · You’re in · Friends** (#844, split mock 3; Q125's
  three until then, and the mocks' *Info* is not a tab). The page opens on Games, and which tab it
  was on isn't kept between visits:
  - **Games** badge — cards where somebody is already In with you, across both kinds, that you
    haven't seen (mock 1 draws *Games 4*, on the selected tab: see below).
  - **Fill in** badge — the rescues you haven't seen (mock 11 draws *Fill in 1*, on the selected
    tab).
  - **You’re in** badge — your live yeses in this group and sport that you haven't seen (split
    mock 3: *You’re in 3*). Friends has none.
  - **A badge counts what you haven't seen** (#844,
    [ADR-0208](../../adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md)).
    - **What a tab shows is seen while it is on screen**, and a row arriving while you're on it is
      seen at once. On Fill in and You’re in that is everything the tab counts. **On Games it is the
      cards of the kind the switch is on**, the whole deck of that kind, not only the top card; the
      other kind's cards stay unseen until the switch moves to it.
    - **The tab on screen draws no badge**, whatever it counts (mocks 1 and 11 and split mocks 1
      and 2 draw one: an override). So a player on Games never sees the Games badge, even while the
      other kind holds cards they haven't seen; once they leave Games, its badge counts those.
    - A row is known by its id: a rescue by its booking, a yes by its proposal, a Games card by
      its id. A row that only changes never counts again; only a row you haven't had on screen
      brings the badge back.
    - What was seen is kept on the phone, per account, and forgotten at sign-out. Until it is read
      no badge is drawn, and no badge holds anything up. The mark is the coral corner badge, as
      before; a count of 0 draws nothing. Spoken, a badged tab says its count is new: *Fill in, 2
      new seats to fill*.
  - **The header opens Info** (Q125). The monogram, the name with its official mark and *n members ·
    home club* are one button, which pushes **Info** over the page as its own screen. The back arrow
    and the sport pill keep their own taps; while the sport filter's bar is open it covers the
    monogram, and a tap there goes to the bar.
  - **The Owner's count of waiting requests** sits on the monogram's corner: the badge the Info tab
    carried, with the same count, and only the Owner sees it.
- **Info** is the group's own screen, with its content unchanged (play 57–60 in
  [the play-groups mocks](../play-groups/README.md#which-mocks-draw-which-area)): the link card with **Share** and
  **Copy**, the Owner's *Want to join · N*, the members row that opens **Members**, and the Owner's
  **Edit group**, with *Leave the group* / *Delete the group* at the screen's foot, outside what
  scrolls. Its header is the page's own without the sport pill, and it is not a button. Back returns
  to the tab the player left.
  - **Re-reads.** Info re-reads the group when it opens, on a pull, and on coming back from Members
    or Edit group. The page's pull on Games, Fill in and You’re in re-reads the group and its games; Friends has
    no pull. The page doesn't re-read on coming back from Info, because Edit group already writes the
    group into the page's read.
  - **A member who must add a sport** sees *Add a sport* on all four tabs. The header still opens
    Info, and the way out is there.
- **A member rated in nothing** (Q126, [ADR-0200](../../adr/0200-a-level-is-asked-where-play-begins.md) §2–§6). Sign-up asks no skill
  question, so this is the common first visit.
  - **In a player group**, **Games, Fill in, You’re in, Friends, Post a game and Members** each show one door
    in place of their content: ***Get your level — pick the sports you play, a few questions
    each***. It opens *Which sports do you play?* over every sport, with nothing ticked. After each
    sport, *Your rating* offers ***Rate {next sport}*** and ***Done for now***; the last offers
    ***Back to {group name}***, which returns to the tab the door was on. With a run left halfway,
    the door reads ***Carry on with your {sport} questions — you're on question {n}*** and opens
    that run. The app never opens on the questions by itself.
  - **In an official group**, rated in none of its sports, every tab keeps the group's own card,
    *This group plays padel · Add padel to your Skill passport to see its games. · [Rate padel]*,
    offering only its sports; its buttons now return to the group with the chip on the sport just
    rated, not to the Skill passport.
  - **Members** still lists only members rated in the sport, so an unrated member is absent from
    everybody's list. Her own Members screen in a player group shows the door in place of the list
    *(a call made in the spec, not grilled)*.
- **The sport pill** is drawn only once the member holds a rating, and lists only the sports she is
  rated in. While a sport is left to offer, it ends with ***+ Another sport***, which opens the same
  picker — over every sport she is unrated in, in a player group; over that group's sports she is
  unrated in, in an official one — and returns to the group. Rated in everything there is to offer,
  there is no *+ Another sport*.
- **The Competitive / For fun switch** (mock 9) sits under the tabs on **Games**:
  *Competitive · 7* / *For fun · 1* — the number is the cards of that kind in this group and
  sport. It stays where it is today on **Friends** too, where it sets one friends game's kind and
  never the intent ([the Friends spec set](../friends/README.md), Q128).
  - **Both kinds are always drawn** (Q127, [ADR-0201](../../adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
    §2). A player whose intent is one kind sees that kind live, with its number, and **the other
    dimmed, with no number**: Ania (Competitive) reads *Competitive · 7* and a dimmed *For fun*, and
    Kuba (For fun) the mirror. *Either suits me* sees both live, as before.
  - **The dimmed kind is a door**, not a disabled tab: the same size as the live one and just as
    easy to press. A tap opens its panel ([A2.1](#a21-states)) and doesn't move the switch.
  - **The deck never opens on the dimmed kind**, even when the phone last stood on that kind in
    another sport or group. The remembered position stays one for the app, as today, and is
    corrected to a live kind.

## A2. The Games tab

### A2.1 States

1. **Nothing to deal** — today's cards stay exactly as built: *Just you so far*, *3 of 4*,
   *Nothing picked right now*, with **Share the link** and **Copy link**. *Nothing picked right
   now* gains a third button, **Post a game** (Q96).
2. **Rated in nothing** (Q126) — in a player group, the door replaces the deck: *Get your level —
   pick the sports you play, a few questions each* ([A1](#a1-where-things-live)). The questions
   return here, and state 4 comes next. In an official group rated in none of its sports, the
   group's own card instead.
3. **A run left halfway** (Q126) — the same door, reading *Carry on with your padel questions —
   you're on question 5*, and opening that run. Nothing else asks her to finish it.
4. **No intent for this sport** — the one-time inline question *Competitive / For fun / Either*
   replaces the deck until answered; for a member who has just rated, straight after the door.
   Its answer is followed by state 5. The switch isn't drawn while the question is up.
5. **Finding** (Q127) — right after any intent answer on Games, on the first-time question or on
   the other kind's door. The phone sends `PUT /play-intents/{sport}` with the `DECK` surface, then
   `POST /pools/{id}/deal`, and while that request is in flight the deck's area names the kind it
   lands on: ***Finding for-fun games for you…*** or ***Finding competitive games for you…***. After
   *Either suits me* on the first-time question it reads ***Finding games for you…***. Then it
   re-reads the deck: the cards
   (state 7), or *Nothing picked right now* with **Post a game** (state 1). A failed deal request
   falls through to the re-read, and nothing is retried.
6. **Weekly cap reached** — a slim line above the deck: *"Your 2 games this week are booked —
   showing next week"* (Q73).
7. **The deck** (mock 1).

**The other kind's door** (Q127). A tap on the switch's dimmed kind opens a panel over the deck, inside
the deck's area so the cards' layout is not squeezed. It is an overlay on the group page, not a new
route:

> **You play padel competitively, so Raketa only puts you in competitive games.**
> Want for-fun games too?
>
> **Either suits me** — *Keep your 7 competitive cards and get for-fun ones too.*
> **For fun** — *Your 7 competitive cards go. Games you're In on stay.*
> **Keep competitive**

- *Either suits me* is first and highlighted. The three answers are the first-time question's and
  the You tab's words.
- The number is the member's own count of that kind in this group, the one the switch shows. One
  card reads *Your 1 competitive card goes.*; none drops the number: *Get for-fun games as well as
  competitive ones.* and *Raketa stops dealing you competitive games. Games you're In on stay.*
  ([the words §28](../matchmaking/the-words.md#28-the-games-tabs-door-and-finding)).
- An answer changes this sport only, lands on the kind tapped, and goes on to state 5.
- *Keep competitive* closes the panel and sends nothing.
- Kuba's panel is the mirror: *You play padel for fun, so Raketa only puts you in for-fun games.
  Want competitive games too?*, with *Keep for fun*.

### A2.2 The deck stage

Reuse the **`DeckStage`** the Players deck had — the pan gesture, the stamps, the fly-off,
the arrival animation, the haptic tick — and nothing else of that screen. One change: the two
cards peeking behind the top card **fade as well as shrink** (they used to only shrink) (Q90).
Both now live in `frontend_player/src/features/proposals/components/`, since the Players deck was
removed (#569). The three buttons under the card are `DeckAnswers`: **✕** (= swipe left), **i** (= the game
details), the coral ball (= swipe right). The ball's name stays **I'm in** on every card, even one
whose yes moves money (Q124): the stamp under the thumb is what says *PAY*.

- **Swipe right / the ball** — yes. **Swipe left / ✕** — no.
- **Tap a player tile** — that player's record (the existing `PlayerRecordSheet`).
- **Tap anywhere else on the card, or i** — the game details ([A4](#a4-game-details)).

### A2.3 The card (mocks 2–8, 10)

Dark card, top to bottom:

| Part | What it shows | Rules |
| --- | --- | --- |
| **Ribbon** | *Picked for you* (dark teal) · *Kuba challenged you* / *The group challenged you* (dark teal) · *Seat open · court booked* (**coral**) | No *· friendly* — the segment already says it. On the right, **⏱ 21 h 00** only when the deadline is under 24 h (book-by; for a rescue the cut-off, then the start); *45 min* under an hour, coral. At the deadline the card leaves silently. |
| **Tiles** | 2 × 2 for doubles, 1 × 2 for singles (mock 10): photo or generated poster, the player's **nickname**, never with an @ (cut short visually, never an invented form — ADR-0199, which superseded ADR-0171; the mocks' *Karol T.* is mock data), level | **IN** tag (green outline) on a player who said yes. **FRIEND** (volt) on the reader's own friends, and only theirs (Q68, applying since Q128). No other tag. On a rescue each player reads *2,75 · paid*. |
| **Your tile** | *You*, your level | When your yes would fill the game: **You complete it** in volt (mocks 3, 7). On a rescue your seat is the **dashed** tile: *You complete it · 27 zł · court booked* (mock 2), or *You? · 27 zł* when more than one seat is open. |
| **vs line** | *KAROL + YOU VS ANIA + KUBA* | The top row is one side, the bottom row the other (Q70). |
| **Balance forecast** — *competitive* | percentage (green / amber / red by today's tones) + the bar | The bar names **the same sides as the rows, your side on the left** (light half). Computed for this version. Existing `BalanceBar`, `onDark`. **Never on a For-fun card** (amended 2026-11-22, ADR-0207 §5, #830): the deck sends it `null` there. |
| **Social vibe** — *For fun* | in the forecast's place: the % beside a full-width 0–100 bar with *Social vibe* inside it (ADR-0207 mock 2) | How much everybody on your version shares — In, you and the names dealt; on a rescue, you with its players — worked out from everybody's tags now (the deck's `vibe.pct`; [the mechanics §8.1](the-mechanics.md#81-the-three-card-types)). The word and colour come from the app's four bands (ADR-0207 §8), never the forecast's green / amber / red. Never on a competitive card. |
| **Overlap grid** | *High / Good / Slim overlap* over 7 day columns × 3 range rows | Ranges **Morning 07–12 · Afternoon 12–17 · Evening 17–23**. Bright volt = everyone on the card free for at least one whole hour in the range; dim olive = all but one; dark = fewer. The game's range is ringed in coral. Today's column letter is white. Label colours: volt for High and Good, amber for Slim. |
| **Court block** | state tag · share (volt, mono) · *Saturday 16:00 · Ogrody 33* (+ *· Court 6 · indoor* once booked) · *Indoor* or *Outdoor* when every free court the card could be booked on is of that kind, nothing when they are mixed ([the mechanics §5.2](the-mechanics.md#52-what-a-card-promises), Q122) | Tag: **Court available** (grey — your yes is a free vote; dashed block border), **Book it now** (green — your yes fills it and holds everyone's share after the undo, at every club since Q121; solid green border), **Booked** (volt — a rescue; solid border). *Tomorrow* / *Today* for near days. **no free cancellation** in amber after the club's cut-off (mock 6). |
| **Stamps** | the yes stamp (right) / **NOT THIS TIME** (left), fading in while dragging | The yes stamp is one of two, each with the card's share, fixed when the card was made (Q124): **I'M IN · 32 zł** on a vote (*Court available*), and **PAY · 32 zł** when the yes books at once (*Book it now*) or takes a seat (*Seat open*). PAY holds the share until the club's cut-off, or takes it at once after the cut-off (Q113). The ball under the card stays *I'm in* and the pill stays *Booking in 10 s*. (Until Q124 a vote's stamp read *I'M IN* with no price and a booking's *I'M IN · 32 zł*, Q72.) |

**Per type:**

- **Picked for you** — fresh cards have no IN tags; tags appear as yeses land, and the card
  climbs the deck.
- **Challenge** — the poster always carries IN (posting was their yes). Otherwise it behaves like
  a pick, and outranks one at the same momentum.
- **Seat open** — players *paid*, the dashed seat with your share, the court number and its kind,
  **Booked**. A yes takes the seat at once: your share is held until the cut-off, or paid at once
  after it (Q113).

**An owed card** ([the mechanics §8.2](the-mechanics.md#82-the-order), Q123) — the card dealt first
to the players of a game a club's cancel called off — looks like any other card: **no mark**, no
ribbon of its own, for anybody. It is simply first in the deck of each player it is owed to, as the
server orders it.

**Singles** (mock 10) follow the same rules with two tall tiles and no *vs* line.

**A game dealt in versions** ([the mechanics §7](the-mechanics.md#7-one-game-several-versions))
is not a card type: the card is the same, plus one line under the tiles — *4 people are In on
this game* — counting the yeses on every version.

### A2.4 What happens when you swipe

| You swipe… | On… | What happens |
| --- | --- | --- |
| right | a card that won't fill | Your tile gains IN for the others; the card leaves your deck; the yes appears on **You’re in** (#844; *Fill in › You're In* until then), and that tab's badge counts it until you look. Nothing charged. |
| right | *Book it now* | Toast **"Booking in 10 s · Undo"** with a draining ring. At zero: everyone's share held together → **It's a game!** (taken at once only for a game booked after its cut-off), at every club ([the mechanics §11](the-mechanics.md#11-the-moment-a-game-fills), Q113, Q121). |
| right | a rescue | The same toast; at zero your share is held (taken at once after the cut-off) → **It's a game!**; the game is in **Home**. A refused card keeps the seat yours for 30 minutes ([the mechanics §10.1](the-mechanics.md#101-fill-in--the-rescue-board)). |
| right | without a saved method | The **payment setup** ([A7.3](#a73-payments)) opens as a sheet; the yes lands when it finishes, or is dropped if you close it. |
| left | anything | The card leaves; silent; never on your record. |

- **It's a game!** — today's yes screen (ADR-0167): full screen, the faces, the one word *It's a
  game!*, **Open game** and **Later**. It marks the players being matched, not only booked (Q103).
  Shown to the player whose action filled it — a yes or a rescue join — and to a player whose
  confirmed payment completes a game waiting for it (Q110). Under the word, one line when another
  player's payment failed: *Waiting for one payment · until 14:40 · Nobody pays until it's in*, its
  time written as in [A8](#a8-home). Its other line, *Kazimierz Padel answers by 21:15 · Nobody pays
  until it confirms* at a club that confirmed, went with *On request* (Q121).

  Its player gets no banner for it, and the bell doesn't count it; the row is still in their list
  (Q102, [A9](#a9-notifications-delivery)).
- **A card refused at the fill** — before the cut-off, toast *"Your card didn't go through — fix
  it to keep your seat. Nothing is paid now."* *(written in while recording Q113)* and the
  notice *Fix your card by 14:40 to keep
  your seat*, for the player's time to fix the card; after it, toast *"Your payment didn't go
  through — confirm it to keep your seat"* and the notice *Confirm your payment by 14:40 to keep
  your seat*, for their time to pay ([A9](#a9-notifications-delivery);
  [the mechanics §12.2](the-mechanics.md#122-when-a-game-fills), Q109, Q113). The seat is held for
  them either way.

## A3. Fill in and You’re in

> **Rewritten 2026-11-23 for PRD [#844](https://github.com/Raketa02/Raketa/issues/844).** Until
> then this was one tab, Fill in (mock 11), stacking two sections under the headings *SEATS TO
> FILL · N* and *YOU'RE IN · N*, with the FAB floating over it always. The split is drawn by
> [split mocks 1 and 2](../fill-in-split/README.md#which-mock-shows-what).

Two tabs, side by side in the bar, **each owning one list**. The rows are today's rows, drawn,
ordered and tapped exactly as before ([A3.1](#a31-the-rescue-row-mock-12),
[A3.2](#a32-the-yes-row-mock-13)). **Neither tab has a section heading**: the tab's name does that
job. Paper background on both.

**Fill in** (split mock 1) holds **only the rescues** you fit and are free for, soonest first, each
leaving at its deadline by itself.

- **No + Post a game** floats here (split mock 1 draws one: an override).
- **Empty** — the one line ***No seats to fill right now***, whether You’re in is empty or not.
  Fill in never draws the group's starting card, which tells you to post, because the button no
  longer lives here. (The level door and the *add a sport* card still stand in its place, as below.)
- **Its read is its own**: the muted spinner while nothing is drawn yet, the amber offline note that
  resumes, and the refusal with why and its retry. None of it touches You’re in.
- Its badge counts the rescues you haven't seen ([A1](#a1-where-things-live)).

**You’re in** (split mock 2) holds **only your live yeses in this group and sport**: picks,
challenges and your own posts still filling, never a rescue (a taken rescue goes to Home, Q76).
Soonest first.

- **The coral + Post a game FAB** (mock 14) **floats bottom-right here, and only here**. It floats
  over the level door too, and it isn't drawn while an official group's *add a sport* card stands
  in the tab.
- **Empty:**
  - **when both tabs are empty**, the group's starting card: *No games yet* (*No games yet — it’s
    just you* for the only member), *Post the first game…*, and the link's doors. It is drawn only
    once **both** reads, the rescues and your live yeses, have said there is nothing, never as a
    first frame;
  - **when only this tab is empty**, the one line ***You haven’t said yes to a game here yet***.
- **Withdraw** takes the yes back in place: the row leaves and the tab stays put. Withdrawing the
  last one leaves the tab on its empty state, without navigating.
- **Its read is its own**: the live yeses, then each row's game for its squares. The spinner reads
  *Reading You’re in*; the offline note and the refusal with its retry are as on Fill in.
- **The live yeses are read as the page opens**, not when the tab is drawn, because the tab's badge
  needs them. It is the read the tab makes anyway, shared with You › Payments, made earlier and in
  parallel: it never delays anything, and the tab usually opens already read. It is now made on
  every page open, including visits that never open You’re in (the log's
  [§12 call 2](../fill-in-split/decisions.md#12-calls-made-without-asking-flagged-to-the-user),
  accepted in PRD #844; its fallback, a badge drawn only once that read is already cached, was not
  taken).
- Its badge counts the yeses you haven't seen ([A1](#a1-where-things-live)): a yes you gave by
  swiping on the deck counts until you look; your own post doesn't, because you land on it.

**Both tabs:**

- **Rated in nothing**, in a player group, each tab is the door ([A1](#a1-where-things-live), Q126)
  in place of its list or its empty state. The FAB still floats on You’re in, and Post a game shows
  the same door. In an official group whose sports you aren't rated in, each tab is its *add a
  sport* card instead.
- **The pull** is the page's one control, as on Games: it re-reads everything, whichever tab you
  pull on.

### A3.1 The rescue row (mock 12)

Coral 1.5 pt border. On **Fill in**.

- **Title** — *Padel · Saturday 16:00* (+ *· friendly* for For fun). Tap the upper block → the
  rescue's details (non-member view, [A4.3](#a43-a-rescue-seen-from-outside-q96)).
- **Subtitle** — *Ogrody 33 · **fills by Fri 16:00*** before the cut-off; *Ogrody 33 · **offered
  until the start*** after it. Switches by itself at the cut-off.
- **Squares** — the booked players' small posters, then one dashed **?** per open seat. Long-press
  a poster → record.
- **Pay 27 zł** (volt, Q124) — takes the seat: the 10-second undo, the share held until the cut-off
  (taken at once after it), **It's a game!**, and the game is in Home. Its spoken name says which:
  *held until the cut-off* before it, *paid now* after it (Q113). Lost race → toast *"Someone just
  took it"*.

### A3.2 The yes row (mock 13)

Mint 1.5 pt border. On **You’re in**. Picks, challenges and posts — never rescues (Q76).

- **Title** — *Padel · Saturday 15:00*. Tap → the game's details (filling view).
- **Subtitle** — *Bonarka Arena · **book by Saturday 13:00***. (Until Q121, while an *On request*
  club decided, the bold part was amber ***waiting for the club***.)
- **Squares** — filled posters for everyone In (you included), dashed empties for the open seats.
- **Withdraw** (red text, outlined) — free and silent. On your own post: if others are In the
  game carries on without you; if not, the post disappears.

## A4. Game details

One screen (details 5–10, from Part 1), three readers.

### A4.1 A booked game you're in (details 5–10)

- **Top bar** (details 7) — back · the other players' faces overlapping (up to three) · their
  names as the title · *Padel · booked* · **Chat · 2** on the right (volt when unread) while
  the game isn't over.
- **The game card** (details 8) — status tag (dot + word), tiles with *paid*, the *vs* line, then
  the court facts on an accent line in the status colour: **WHERE** *Bonarka Arena · Court 2 ·
  indoor · 3,1 km* — the court's kind always shown (Q122) ·
  **DAY** *Sunday 20 Sep* (*· next week* beyond seven days) · **TIME** *10:00 until
  11:00* · the money row, which says when the share is held and when it is taken
  ([the mechanics §14.1](the-mechanics.md#141-home-and-the-statuses), Q113): held, *28 zł held on
  your card · taken Sat 10:00 · free to leave until then*; checked, *28 zł held from Tue 10:00 ·
  taken Sat 10:00*; after the cut-off, *PAID · 28 zł · your share · to the club*. A player whose
  card was refused at the holding time reads *Fix your card by 14:40 to keep your seat* there, with
  the confirmation one tap away. No card fee is printed.
- **Balance forecast** (details 9) — as built today; hidden while a seat is open.
- **At the court** ([the mechanics §15.1](the-mechanics.md#151-attendance-at-the-court), Q115) — from the
  hour's start to 30 minutes after it, the attendance block, built in the style of the details:
  - **isn't here yet**, one per courtmate who hasn't arrived — *Oscar isn't here yet* — and, once
    somebody has tapped it, **They're here** for when he walks in;
  - **I'm here**, for the player somebody is waiting for;
  - afterwards, **I was there** for a player who reads *Didn't come*, until 24 hours after the
    window, and **Yes, they were here** for the others while a claim waits;
  - every outcome and refusal as a plain sentence: on time (the line vanishes), *Came late*,
    *Didn't come*, *You can say so only from Ogrody 33*, location off (the phone asks for it and
    says why), and the window passed. Each tap reads the location once, through the app's existing
    location port, and sends it with the tap.
- **After the hour — the result screen** ([the mechanics §15.2](the-mechanics.md#152-results-and-sportsmanship),
  Q119) — on a Competitive game, **How did it go?** leads into putting the score up; the other side
  reads **Is that right?**, which says truthfully when the score becomes the result if nobody
  answers, and that saying nothing costs nothing, with **That's right**, which settles it at once.
  A For fun game asks nothing and reads *Played*. The endings *Played · no score* and *disputed* are
  said in words. Every notice of [the mechanics §17.2](the-mechanics.md#172-notifications)'s *game's own
  notices* opens this screen.
- **No *Show at the desk*.** The QR card and its short code were removed with desk check-in on
  2026-10-11 (Q116).
- **Leave the game** (details 10) — outlined, red text; the line under it states the cost for
  the moment ([the mechanics §13](the-mechanics.md#13-leaving-a-game)); the confirmation sheet is
  today's *Before you leave* sheet with the new words (Q113):
  - **before the cut-off** — the line says leaving is free and nothing is taken; the sheet says the
    hold on the card is let go and the seat is offered to others, with the record line as today; the
    toast reads *You left the game. Nothing was taken.*;
  - **after the cut-off** — the line and the sheet give the exact sum the server sends: *If someone
    takes your seat, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*. While
    the server sends none (the fee isn't known yet) there is no figure and no clause.

### A4.2 A game still filling (Q75)

**The top card is the kind's own** (amended 2026-11-23, ADR-0207 §6, #833; the details read
serves it, the player app draws it in #839 and #840):

- **Competitive** opens on the **Balance forecast card** a booked game draws: each side's level,
  *gap* and the signed gap (`forecast.your_side`, `their_side`, `gap`), the bar, the % and its
  word, *A counted game — a confirmed score moves everybody's level.*, and **If you win / If you
  lose** for you (`at_stake`). The stakes are priced **by the booked game's own function** on your
  version's evenest sides — the sides the tiles show — so they are the stakes that apply once the
  game is booked; **two tiles or none**, as on a booked game: none while a seat is open, none
  once the game is no longer yours to play (you said no, no longer fit, or it ended — and once
  it is booked, the booked game's screen draws them), none where you or everybody across the net
  holds no level. Singles too. Never on the deck card. No vibe.
- **For fun** opens on the **Social vibe card**: the card's own % (`vibe.pct`, the number swiped
  on) and its word, and the grid — a column per person on your version, you first, then the tiles'
  order; **a row per tag you hold** (`vibe.rows`), in the vocabulary's order, 💘 included; a dot
  under everybody who carries it (`carried_by`), so your column has a dot on every row. Live: it
  follows everybody's tags now. No forecast and no stakes.

Same layout. Status *Filling · 2 of 4 in* (and for a game that had filled, *Seat open* or *Waiting
for one payment*, as on [A8](#a8-home)); tiles with IN tags; WHERE shows the club and distance, no
court number, and *Indoor* or *Outdoor* when every free court it could be booked on is of that kind
(Q122); the money row reads *30 zł if it fills · book by Sat 13:00* (until Q121, while *waiting for
the club*, *nobody pays until Bonarka Arena confirms* with *Bonarka Arena answers by 20:45*); the
**overlap grid** follows the forecast; then one plain paragraph: *"Your yes
costs nothing until everybody is in. When the last yes lands, everyone's share is held and the
court is booked; it's taken at the club's cut-off."* (Q113) Actions at the bottom: **I'm in** / **Not this time** if you haven't
answered, or **Pay 30 zł** / **Not this time** on a *Book it now* game, whose last seat your yes
takes (Q124); **Withdraw** if you're In; and while it waits for one payment, **Leave the game** with
its sheet ([the mechanics §13](the-mechanics.md#13-leaving-a-game)). No Chat.

### A4.3 A rescue seen from outside (Q96)

The booked layout with the dashed *You?* tile, the court number, *Paid* players, and a volt
**Pay 27 zł** (Q124) at the bottom, spoken *held until the cut-off* before it and *paid now* after it
(Q113). No Chat, no Leave.

### A4.4 The chat

The conversation screen, which lost its plan card and Details button with the old loop, and has
no way into the details; the back chevron returns to where the chat was opened from — the
details, or Home from the bubble on its card ([A8](#a8-home), Q100). Opens when the game is
booked; members are the current line-up; system lines *"Kuba left — the seat is open"* and *"Ola
took the seat"*.

## A5. Post a game (mock 15)

Full screen over the group, scrolling; the bottom bar stays visible. It opens from two doors,
You’re in's **+ Post a game** and Games' *Nothing picked right now*, and **opening it doesn't turn
the page** (#844; until then it turned the page to Fill in as it opened). The tab the page stood on
is its origin. **Back** (the chevron, the hardware back or a swipe) returns to that tab, and the
back control names it: ***Back to You’re in*** / ***Back to Games*** (it was *Back to Fill in*).
The draft is kept while you stay in the group.

### A5.1 The controls (mocks 16–19)

| Section | Control | Behaviour |
| --- | --- | --- |
| **SPORT** | chip row, each with its sport colour dot and the count of group members rated in it (*Padel 10*) | Only sports you're rated in that the group plays. Selecting resets the level range and clears the pick. Rated in nothing, in a player group: the door ([A1](#a1-where-things-live), Q126). Rated in none of the group's sports: *"Get rated in padel to post here"* with its button per sport, as today, which now begins the questions (Q80, Q126). A pass begun here, from the door or this card, returns to **You’re in**, where the button lives (#844; it returned to Fill in). |
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
- **The fits** — horizontal cards (poster, level, name, *2,75 · 93*); tap → record. The second
  figure is the post's kind's own number (amended 2026-11-23, ADR-0207 §5, #834). On a competitive
  post it is the % even (`forecast.pct`). On a **For-fun** post it is **the Social vibe of the two
  of you** (`vibe.pct`), coloured by its band, never a forecast, and the cards come **best vibe
  first**, in the server's order.
- **FREE COURTS · HOME CLUB FIRST** — one row per free court hour: the hour (mono), the club,
  *2,4 km · 27 zł if it fills · book by Saturday 15:00*, its own *"4 free"* (Q77), and *27 zł
  each*. Tap → picks it (ring + ✓ on the cell); a new pick replaces the old.
- **ALREADY HAPPENING HERE** — first **rescues** you fit (*Padel · Sunday 20:00*, *Kuba · Centrum
  Ruchu · Court 2 · 30 zł each*, the squares, *any level ✓ · you are free ✓*, **Pay 30 zł**,
  spoken *held until the cut-off* before it and *paid now* after it, as on [A3.1](#a31-the-rescue-row-mock-12)
  — Q113, Q124); then **posts still filling** you fit (no court number, **I'm in**; **Pay 27 zł** on
  a post's last seat, because your yes fills it — Q124) (Q79, Q93).

### A5.4 Post — you're In (mock 33)

Full-width coral button, disabled (pale) until a court is picked, with the helper *"Pick an hour
with a court on the map first."* Tapping it: your yes is recorded, up to three versions are
dealt as *"[You] challenged you"* cards, their *Challenges for you* alert fires, and you land on
**You’re in**, whichever door you came through (#844; *Fill in › You're In* until then), with the
toast *Posted — N of your best fits have it.* Your post doesn't raise You’re in's badge: you are
looking at it. **Joining a post** from the slot sheet lands on You’re in too; **joining a rescue**
from it runs *It's a game!* and Home as before, and leaves the page on You’re in. Guards, each
shown under the button in place of the helper: no saved method (the setup opens), two live posts
already (*You already have 2 posts live — withdraw one in You’re in to post again.*), games per
week already booked that week.

## A6. The You tab: Your week (mock 36)

In *Your games* (*Finding players* until Q126), and the same component in onboarding (replacing today's 7 × 3 step).
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

- **ALWAYS ON** — sixteen inert rows with a green **on** tag, those of
  [the mechanics §17.2](the-mechanics.md#172-notifications): *It's a game! · held* · *Waiting for
  one payment* · *Fix your card by … to keep your seat* · *Confirm your payment by … to keep your
  seat* · *Game called off · nothing was taken, or with the refund* · *Game moved* · *Someone left
  your game · or it's filling again* · *You've been refunded* · *Your new game* · *A game you left* ·
  *Your post didn't fill* · *Isn't here yet* · *They're at the club* · *How did it go?* · *Is that
  right?* · *Were they there?* (Q113 adds *Fix your card*; the quiet row for the take at the
  cut-off is never pushed, so it isn't listed; Q120 adds the game's own five, written in as the
  list's words; Q121 removes *It's a game! · the club answers by …* and *The club confirmed / said
  no / didn't answer in time*; Q122 adds *Game moved*).
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
   **Accept and continue**. Since Q113 that text is a new version: held when a game fills (or
   checked, and held four days before the cut-off), taken at the club's cut-off, nothing taken for
   a leave before it, and after it the share back less what was kept on the payment if the seat is
   taken. A player who accepted the earlier version meets the same step again — the amber note,
   the terms and *Accept the terms* on state B, as for a changed brand — before their next game
   holds money.
4. **Confirm with your bank** (mock 44, moved down) — *"One-time 3-D Secure check — it lets the
   club hold and take your share later without you present."* (Q113; it said *charge*); **Open the
   bank app · confirm**. This step
   saves the method; when the bank asks nothing, it ticks by itself and the screen moves to state
   B.

**State B — saved** (mocks 46–49):

- **The method card** (dark) — brand badge (*VISA*, *GPay*, …), *Card •••• 4312*, *Held when a
  game fills · taken by the club at its cut-off* (Q113; *written in while recording it*), **Change** (reopens the setup; the old method keeps working until the
  new one is saved). Under it a small **Remove this method** link, refused with its reason while
  anything is live (Q83).
- **TO CONFIRM** — above the live yeses, and first in Home's *Needs your answer* too, a tile per
  payment there ([A8](#a8-home); #817 — it stood above Home's rail until then): a card refused when
  a game filled, at the holding time or on a rescue (and, until Q121, when its club accepted it),
  which the player can still
  confirm; tap → the confirmation. While the seat is held for them, the row names the end of their
  window by the one the server names: *Fix your card by 14:40* before the cut-off (with a line that
  nothing is paid now), *Confirm your payment by 14:40* after it, written as the times in
  [A8](#a8-home) are ([the mechanics §12.2](the-mechanics.md#122-when-a-game-fills), Q109, Q113).
- **LIVE YESES · 3** — every live yes, with no cap (the mechanics Q97); rows *Padel · Saturday 15:00 ·
  Bonarka Arena* with the share in grey; tap → the game's details. Hidden when empty.
- **RECEIPTS** — newest first, the **club's name** as the title, *Padel · Today · 16:00* under it
  (Q113):
  - a share taken — ✓ grey circle, *−40 zł · paid* (dark);
  - a refund — ↩ mint circle, *+38,24 zł · refunded* (mint), with *1,76 zł kept on your payment*
    under it, the exact fee the server sends;
  - a hold let go — a leave before the cut-off, a game short at the cut-off, a club's cancel before
    it — *40 zł held · released* in grey, with its date, so the hold the bank app showed is
    explained. The card check at a far-ahead fill never appears.

  Empty: *"Nothing yet — charges and refunds land here, with the club named as the seller."*
  Footer when there are rows: *"Refunds can take up to two weeks to reach your card."* — no BLIK
  line while BLIK isn't offered *(written in while recording Q113)*.

## A8. Home

The rail of game cards that was *Now*, renamed **Home**, showing the statuses of
[the mechanics §14.1](the-mechanics.md#141-home-and-the-statuses): **Waiting for one payment**
(amber), **Booked** (mint), **Seat open** (amber), the result
statuses — *Needs result*, *Confirm the result*, *Counted*, *Uncounted* with its reason, and
**Played · no score**, which replaced *Never played* (Q114) — **Called off** (red) — each with its
money line. A booked card names its court and the court's kind, *Court 3 · indoor* (Q122), and
carries no QR code and nothing to show at the desk (Q116). **Open game** →
[A4.1](#a41-a-booked-game-youre-in-details-510).
On a booked card the **speech bubble is the chat's door**: it opens the game's chat
([A4.4](#a44-the-chat)) straight over Home, and Back returns to Home
([the mechanics §14.3](the-mechanics.md#143-the-chat), Q100). It shows when the game's chat is
open — never before the game is booked, nor on *Called off*. It carries no count until the details'
*Chat · n* has its unread count; then it shows the same number. Games that filled since you last
looked are marked *new*; opening the details, or the chat from the bubble, clears it.

A **Booked** card's money line follows the share (Q113): *40 zł · free to leave until Wed 19:00*
while the cut-off is ahead, whether the share is held yet or only checked, and *Paid · 40 zł* once it
is taken. A game called off at its cut-off reads *nothing was taken* where it read *Refunded*.

**A time on Home is in Warsaw time, as every day and hour on Home is**: the hour alone when it falls
today (*until 14:40*), else the weekday and the hour (*until Sun 00:15*), in the form of *free to
leave until Sun 17:00*. (Until Q121 a game **waiting for the club** said when its *On request* club
must answer, *Bonarka Arena answers by 20:45 · Nobody pays until it confirms*, in that form, Q98.)

**A full game that falls back stays on Home as *Seat open*** for those still In (Q106): *1 seat
open · books when it's full · nobody paid*, mirroring a booked game's *Seat open*. It is booked when
it refills, and reads *Called off · nobody paid* if its book-by passes first. (At an *On request*
club, until Q121, it read *… is asked again when it's full*, and *Waiting for the club* on
refilling.) It is on *You’re in* too ([A3.2](#a32-the-yes-row-mock-13)).

**Waiting for one payment** (Q111) is on all four's Home while one player's time to fix the card
or time to pay runs: *Waiting for one payment · until 14:40 · Nobody pays until it's in*, the same
in both windows. The refused player's own card reads *Fix your card by 14:40* before the cut-off and
*Confirm your payment by 14:40* after it, as their *TO CONFIRM* tile in *Needs your answer* does
([A7.3](#a73-payments); Q113). At the end it becomes *Booked*, or *Seat open*. A card refused at the holding time leaves the
game *Booked*: only its player's card reads *Fix your card by 14:40*.

**Get your level** (Q126). While a player is a member of at least one group and holds no rating,
Home shows a card: ***Get your level — your groups can't deal you games until you
have one.*** It opens *Which sports do you play?*, and the questions return to Home. With a run
left halfway it offers to carry on — *Carry on with your padel questions — you're on question 5* —
and never to start again. Once she holds any rating, it is gone. The *Get your level* notice opens
Home on this card. *(Q129, 2026-11-07: while a friend's ask for a level is on her Home, the ask's
card is drawn instead of this one, in its own row, and this one comes back if she sets the ask aside still rated in nothing —
[the friends screens §6.4](../friends/the-screens.md#64-asked-for-a-level--n-designed-no-mock). Undone on
2026-11-17 by ADR-0205 §4: the ask waits in Needs your answer, and this card shows whether or not
anybody asked.)*

A **Called off** card says why, as the notice and the email do: short at the cut-off, the club's
cancel with its reason, a payment that didn't come in time. The club's answer, *Kazimierz Padel said
no* or *… didn't answer in time* (Q105), went with *On request* (Q121).

**The trophy** (Q130, 2026-11-07). Home's header carries a dark pill, ***🏆 #7***, **just left of the
bell**, which keeps the corner. It reads the reader's place in the sport of their latest result, in
the Rankings view they last looked at, and has no number when they have no place there. A tap opens
Rankings ([ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
[the rankings screens §1](../rankings/the-screens.md#1-home--the-trophy-rankings-1)). *(Q131, 2026-11-14: the trophy is always
there, a newcomer's included, with no number while there is no place.)*

**The five rows** (Q131, 2026-11-14, [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §1). Each new row reads on its own and is hidden
with its title when empty; pull-to-refresh re-reads them all, and coming back to Home re-reads them
when the last read is older than 30 seconds. **A player in no group** reads ***Join a group to get
games — the hottest ones are just below.*** under *Your games*, in place of *⚡ Play finds you one*
([the home rows screens §1](../home-rows/the-screens.md#1-home-top-to-bottom)).

**Home, top to bottom** (2026-11-17, [ADR-0205](../../adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
§1, §4; [#816](https://github.com/Raketa02/Raketa/issues/816), [#817](https://github.com/Raketa02/Raketa/issues/817)):
the header — the title, then the **envelope**, the bell and the trophy in the far-right corner;
*Get your level*; *Your games*; then the five rows. **What waits on the player is behind the
envelope**, in ***Needs your answer***, the sheet it opens, in this order: ***To confirm***, a tile per
payment, ***Friends game***, one invitation at a time on the paging rail, ***Friend requests*** and
***Asked for a level*** ([the home refactor](../home-refactor/README.md)). They stood on Home,
above *Your games*, from Q128 and Q129. **Home's tab badge still counts the payments to confirm**, and
a link or a notice that pointed at one of the four cards — the friend link, a friend request's, a
friends game invitation's — opens Home with the sheet already up, or Home as it is when nothing waits
by then. *(The rows' order from ADR-0204 — Hottest groups, Same competitive level players, New in
Raketa, Same vibe players, Top 10 — stands until FOR YOU folds them,
[#820](https://github.com/Raketa02/Raketa/issues/820)–[#823](https://github.com/Raketa02/Raketa/issues/823).)*

## A9. Notifications delivery

| Notice | Push | In-app banner + recent list | Email |
| --- | --- | --- | --- |
| It's a game! · 40 zł held (*you paid* after the cut-off; or *… is booked · 40 zł held* after one payment was missing) | ✓ | ✓ | ✓ (booking confirmation, saying when the share is taken) |
| Waiting for one payment | ✓ | ✓ | — |
| Fix your card by 14:40 to keep your seat (before the cut-off, Q113) | ✓ | ✓ | ✓ |
| Your time to fix your card ran out | ✓ | ✓ | — |
| Confirm your payment by 14:40 to keep your seat (after the cut-off) | ✓ | ✓ | ✓ |
| Your time to pay ran out | ✓ | ✓ | — |
| Your 40 zł for Thu 19:00 was taken — the take at the cut-off, quiet (Q113, a call) | — | the list only, never bannered | ✓ (the receipt) |
| Game called off · nothing was taken, or with the refund — after a club's cancel, with *We'll look for another game for you first* (Q123) | ✓ | ✓ | ✓ |
| Game called off · nobody paid (a full game that never booked: its book-by passed, or a payment had no time left) | ✓ | ✓ | — |
| You've been refunded · your seat was taken (the exact sum and the fee kept on your payment) | ✓ | ✓ | ✓ |
| Someone left your game · or it's filling again | ✓ | ✓ | — |
| Game moved — *Bonarka Arena moved your game to Court 3 · Thu 19:00* (Q122) | ✓ | ✓ | — |
| Your new game | ✓ | ✓ | — |
| You left the game · nothing was taken (your own leave, before the cut-off — Q113) | — | — | ✓ |
| You left the game · the exact refund if your seat is taken (your own leave, after the cut-off — Q113) | — | — | ✓ |
| A game you left — called off by your empty seat | ✓ | ✓ | — |
| A game you left — cancelled by the club, with your refund | ✓ | ✓ | ✓ |
| Your post didn't fill | ✓ | ✓ | — |
| Isn't here yet — *Ivan is at Ogrody 33 and you're not there yet* (to the absent player, Q115, Q120) | ✓ | ✓ | — |
| They're at the club (to whoever tapped) | ✓ | ✓ | — |
| How did it go? (a Competitive game's hour ended, Q119, Q120) | ✓ | ✓ | — |
| Is that right? (the other side put a score up) | ✓ | ✓ | — |
| Were they there? (an absent player claimed *I was there*) | ✓ | ✓ | — |
| Get your level — *Get your level so your groups can deal you games.*, once per account, ever, a day after a first group join while rated in nothing (Q126); opens Home | ✓ | ✓ | — |
| You complete it · Challenges for you · Fill in alerts | ✓ if on | ✓ if on | — |

Push goes through Expo's push service, switched on end to end on Android and iPhone since Q120: a
human sets up the Expo project, Firebase and the Apple Developer Program, and the app then turns it
on. Emails go through the existing mailer (ADR-0186). For fun games are told none of the game's
own five. (Q121 removed three rows: *It's a game! · Kazimierz Padel answers by 21:15*, *The club
confirmed*, and *The club said no · didn't answer in time*, the last two emailed.)

**Where a notice opens.** Tapping a notice — the banner, its row in the list or, later, a push —
opens the game it is about. Three open the group's Games deck with their card on top: *You
complete it*, *Challenges* and **Your new game** (Q107), which opens it on the owed card, first in
the deck anyway (Q123). **Game moved** opens the booked game (Q122). The game's own five — *Isn't
here yet*, *They're at the club*, *How did it go?*, *Is that right?* and *Were they there?* — open **the game's
result screen** ([A4.1](#a41-a-booked-game-youre-in-details-510), Q120). **Home is read again whenever a notice
arrives**, so a game a notice is about is there when it is tapped (Q103).

**The bell and its number** (Q101). The recent notices are a list, the newest 30, reached from a
bell on Home. The bell carries the number of notices given since the player last opened the list,
*99+* above 99. The server keeps it, so it is the same on every phone. Opening the list clears it,
and the rows that came since the last visit stand out on that visit. Nothing is marked read row by
row, and there is no *mark all*. The app icon carries no number until push is on.

**Banners** (Q101, Q102):

- **None at launch.** What was told while Raketa was closed is in the bell's number.
- **Coming back from the background** shows a banner for the newest notice only; the number counts
  the rest.
- **Never for your own act.** The player whose yes filled the game, or whose confirmed payment
  completed it, sees *It's a game!*; their own notice is in the list, already seen, never bannered
  and never counted. A notice about money held or taken by somebody else's act, such as *Your Tue
  19:00 is booked · 40 zł held* when another player's payment comes in, is bannered as usual.

## A10. Design-system work (Part 16 rows)

- **New colours** — the grid's two middle greens: `#A9DEC5` (*light green*) and `#5EC39B` (*mid
  green*), each with its Soft / Ink / Line and contrast per §15.2. `#E2F3EC` is `mintSoft`,
  `#0C8F6B` is `mint`.
- **New components** — the game card (dark, three types), the mini overlap grid, the court block
  with its three tags, the Undo toast with a draining ring, the rescue and You’re in rows, the
  posting grid cell (nine states), the slot sheet, the hour grid (7 × 16), the numbered setup
  checklist, the method card, the receipt row, the on/off chip.
- **Changed** — peeking deck cards fade; the group page's Competitive / For fun switch appears on
  Games, and since Q127 draws the kind the intent doesn't want dimmed, at full size and still
  pressable, as a door; the You tab gains *Account*; the bottom bar loses Players and Chats
  (removed, #569).
- **Sport colours** as today: padel coral, tennis mint, squash night2, badminton amber.

---

# Part B — The club website

Designed in this document (the product owner delegated it; confirmed in Q86, Q95). Built on the
existing frame: **the top bar**, `src/ui/tokens.css`, the `Form` primitive, the three server
doors. Clean and minimal: one task per page, one primary button per section.

## B1. The top bar

**Overview · Bookings · Courts & prices · Money · Groups · Administrators**, and on the right the
club's name opening a menu with **Details** and **Raketa settings**. (A coral count badge on
Bookings, for requests waiting for an answer, went with *On request*, Q121.)

## B2. Overview

- **Until the club is live — the setup checklist.** Four rows, each with its state (done ✓ /
  next / locked) and one button:
  1. **Connect payments** → *Connect with Stripe* (Stripe's hosted sign-up; back to Overview).
     States: *not started*, *Stripe needs more details* (with *Continue with Stripe*), *ready*.
  2. **Add your courts** → Courts & prices.
  3. **Set hours and prices** → Courts & prices, the week grid.
  4. **Check the settings** → Raketa settings, **Confirm settings**.
  When the fourth is done: a one-time line *"You're live — your courts can now be booked through
  Raketa"*, and the checklist is gone. (Until Q121 there were five: the second was **Choose how you
  work with Raketa**.)
- **After that** — a line that the club is live on Raketa and a link to **today's Bookings** (Q121,
  *a call*), and any *Stripe needs something from you* notice. Nothing waits for the club's answer
  any more: until Q121 this listed the *On request* bookings with their countdown and Accept /
  Refuse. (The statistics that will live here are out of scope.)

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

- **One day at a time**: *‹ Today ›* with a date picker; filters **All · Seat open · Called off**
  (*Waiting for you* went with *On request*, Q121). No *Check in* button (Q116).
- **Row** (per booking): time + court and its kind (*Court 3 · indoor*, Q122) + sport + kind ·
  the players (nickname — Q126, *A player* for an account that reads as nobody — and their share *held* or
  *taken* — Q113; no *checked in ✓*, and nothing about who came or the score) · status tag · money (court price, collected, refunded) ·
  the group it came from · actions:
  - **Booked / Seat open** → **Move** and **Cancel**. Not possible after the start.
    - **Move** — a dialog listing the free courts of that sport at that hour that keep the game's
      kind: the same kind, or an indoor court for an outdoor game, each with its kind (Q122, *a
      call*). Players see the new number and are told *Game moved*.
    - **Cancel** — a dialog that asks for the reason, *weather · repair · double booking · other*,
      and then shows what this cancel would do ([the mechanics §16.9](the-mechanics.md#169-cancelling-a-booking),
      Q122, *a call*):
      - *"This game moves to Court 3 · indoor · the players are told, nobody is refunded"*, with
        **Cancel the booking** and **Cancel the game anyway**, for a club closing the whole hour;
      - or *"This game is called off"*, with the consequence, which depends on the cut-off (Q113):
        before it, *"Every hold is let go and nobody pays a fee"*; after it, *"Everyone is refunded
        in full; the card fees are not returned"*; and **Cancel the booking**.

      The cancel decides afresh when the club confirms, and its answer says what happened: the
      game moved, to the court named or the next that qualifies, or was called off.
  - Until Q121, a **Waiting for you** row offered **Accept** / **Refuse** with a countdown, and an
    Accept that met a refused card read **Accepted · waiting for one player's payment until 21:20**
    (Q112). Both went with *On request*.
- **Empty day**: *"No Raketa bookings on this day."*

## B5. Raketa settings

One page, one form, **Save settings**:

- **Release lead** · **Free-cancellation cut-off** — number fields with their defaults.
- **Other clubs' courts for our groups** — on/off + distance (default **on**, 10 km, since Q128). Its
  help line says the club's groups are offered other clubs' courts *at an hour your courts are full*,
  and only then ([the mechanics §4.3](the-mechanics.md#43-courts)).
- **Pause Raketa bookings** — on/off with its consequence line.
- **Leave Raketa** — a text link at the bottom, refused while anything is booked or unpaid.

*We check players in* was removed with desk check-in on 2026-10-11 (Q116). **How you work with
Raketa** (three radio cards, Only Raketa / Instant / On request), the **Minimum notice** and the
**Time to confirm** were removed with *Instant* and *On request* on 2026-10-12 (Q121): every club
works Only Raketa.

## B6. Check in

**Removed on 2026-10-11** (Q116, [the mechanics §16.10](the-mechanics.md#1610-check-in)). The page opened
the device camera to scan a player's QR code, took a typed short code, and marked *checked in ✓*.
The page, its scanner, the typed-code form, the camera and QR dependencies and the Bookings button
that led to it are gone; players walk straight to the court, and whether somebody came is caught there.

## B7. Money

- **Bookings** — a table for a chosen month: date · court · collected · refunded · card fees ·
  net; totals at the top. **Collected counts a share only once it is taken** at the cut-off — a
  game whose shares are held shows nothing collected yet — and **card fees are the real ones**,
  or *not yet known* while Stripe hasn't reported them (a club on its own negotiated pricing). No
  estimate is shown (Q113).
- **Payouts** — date · amount · status, from Stripe.
- **Open your Stripe dashboard** — a button to the club's full Stripe dashboard (disputes,
  bank details, tax documents).

## B8. Groups (changed)

The *Games* column counts the games booked in each official group. A line above the table links
to the *other clubs' courts* setting, and says it is on and offers other clubs *at an hour your
courts are full* (Q128).

## B9. Emails to the club

Through the existing mailer (ADR-0186): *New bookings today* (a daily summary), *A game was called
off at the cut-off — the hour is free again* (at once), *A payout was sent*, *Stripe needs something
from you* (at once).

*A booking is waiting for your answer* and *A game didn't go ahead* (after an Accept that waited on
one payment, Q112, Q113) went with *On request* (Q121).

---

# Part C — The backend, inferred

The shape is ADR-0189 §5. What each app needs from it:

## C1. Aggregates and their events (all event-sourced)

- **Club courts** (Clubs, per club): `CourtAdded`, `CourtChanged`, `CourtSwitchedOff/On`,
  `RaketaHoursSet` (per court, weekly hours), `ExceptionAdded/Removed`, `PricesSet`,
  `RaketaSettingsChanged`, `StripeAccountLinked`, `StripeAccountStatusChanged`,
  `RaketaPaused/Resumed`. `WayOfWorkingChosen` and the settings' minimum notice and time to confirm
  go with Q121, with no decoder: the local store is reset (a clean cut, *a call*).
  *We check players in* left the settings with check-in (Q116); its field
  stays decodable on `RaketaSettingsChanged` and folds to nothing.
- **Proposal** (Proposals, per proposed game): `ProposalMade` (origin: pick | post; pool, sport,
  kind, who, level range, club, start, share, book-by), `VersionDealt`, `YesSaid`, `YesWithdrawn`,
  `NoSaid`, `ProposalFilled` (the people and sides), `ProposalExpired`, `ProposalWithdrawn`,
  `CourtHourLost` (the last court at that club and hour went; the people In are re-dealt first).
  Since Q123 the redeal after a club's cancel records **the players the new card is owed to**, and
  the deck orders by that (*a call*); the never-at-this-club-and-hour rule goes, and *turned down*
  leaves the endings.
- **Booking** (Bookings, per filled proposal): `BookingConfirmed` (court number,
  seats, cut-off) — born booked at every club since Q121, the request events
  (`BookingRequested`, `BookingAccepted`, `BookingRefused`, `BookingTimedOut`, `RequestWithdrawn`
  and the rest of the seven) gone with no decoder — `CourtMoved` (since Q122 also carrying the new
  court's kind and, after a move by cancel, the cancel's reason), `SeatLeft`,
  `SeatRescued`, `CalledOffAtCutOff`,
  `CancelledByClub`, `BookingPlayed`. `PlayerCheckedIn` retired with check-in (Q116); it stays
  decodable and folds to nothing. It opens the ordinary **Game** on confirmation — the only thing
  that opens one since the old loop was removed (#569). A new read gives a booking's club map
  point, for the attendance verdict below.
- **Game** (Games, grows — Q114, Q115, Q119): one event per attendance act — *note absent*, *note
  arrival*, *claim presence*, *confirm presence* — each carrying the verdict *at the club* and never
  the coordinates; the no-show report's two events retire, decodable and folding to nothing. An
  acceptance settles the result at once, and *Played · no score* and *disputed* are folded ends,
  never stored. The event names are the build's (#654, #655, #657).
- **Payment method** (Payments, per player): `MethodSaved` (Stripe customer and method ids, brand,
  last four, wallet), `TermsAccepted` (version, time, IP), `MethodChanged`, `MethodRemoved`,
  `BrandChanged` (asks again).
- **Seat charge** (Payments, per seat per booking): `Authorised`, `Captured`, `Failed`
  (`authentication_required` / declined), `Cancelled`, `Refunded` (amount, fee withheld),
  `Disputed` — each folded from a Stripe webhook, idempotently. **Since Q113** it tells apart a
  **checked** charge (held and let go at the fill, waiting for its holding time), a **held** one
  (held until the cut-off, with the hold's last moment), a **taken** one (captured, with the real
  fee once Stripe reports it), a **released** one (let go on a leave, a call-off or a club's cancel
  before the cut-off) and a **refunded** one (with the exact amount given back). A held charge is
  not paid, and the club's Collected counts taken ones only; a released charge is settled for
  payouts. The event names are the build's (#636–#641).
- **Notification preferences** (Notifications, per player): `ChoiceSwitched`,
  `DeviceTokenRegistered/Removed`.
- **Player profile** (grows): `WeeklyHoursSet` replaces the 7 × 3 availability.

## C2. Read models

Per reader, never stored as aggregates: the **group deck** (cards addressed to you, an owed card
first, ordered by [the mechanics §8.2](the-mechanics.md#82-the-order), filtered by games-per-week and
most-I'll-pay, each card carrying *indoor*, *outdoor* or neither, Q122–Q123),
**Fill in** (the rescues you fit and are free for; the **You’re in** tab is the live yeses below,
filtered on the phone to the group and sport, #844), **Home**, **Payments** (live
yeses across pools, receipts), the **posting grid** (per range: best-hour count, court
availability, happening-here), the **slot sheet**, the club's **Bookings** (each court with its
kind), the **cancel preview** (moves to a named court of a named kind, or called off — Q122),
**Money** and the **setup checklist** (four steps since Q121).
Court-hour availability is derived from Club courts + bookings + live
proposals' needs, per club and hour.

## C3. Jobs

- **The proposer** — continuously, per pool and sport: free court hours × free fitting members →
  proposals. *Fitting* is the pair rule (`PlayerFit`: blocks, mutual gender preference, the level
  window, and since Q118 the reliability filter), and the most even four is read off the balance forecast — no ranking or score
  ([the mechanics §5.1](the-mechanics.md#51-what-it-does)); distance only picks a group's clubs.
  Deals versions at half-In and after every no. Respects games-per-week, most-I'll-pay and one
  card per people-set per batch. Since Q123 an **owed card** is chosen closest to the cancelled
  game first: the same club, day and hour; another club at that day and hour, nearest first (for an
  official group, only under the hour-by-hour rule since Q128); then the closest hour, the home club
  first. Since Q127 a named player who is not
  In and whose intent no longer wants the card's kind is **gone**, as after a no, and their seat is
  dealt to next best fits; and one pool's batch also runs on a player's asking, through
  `POST /pools/{id}/deal`, which makes no card itself
  ([ADR-0201](../../adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
  §3, §5).
- **Book-by expiry** — expires unfilled proposals; tells posters.
- **Holding the shares** (Q113) — every 30 seconds, as time to pay and the cut-off: holds the
  share of every checked charge whose holding time — four days before the cut-off — has come. A
  refusal opens time to fix the card on the booked game; a holding whose last moment still falls
  short of the cut-off plus 6 hours is taken at its last safe moment (the fallback). The games test
  console's *Run it now* press for it is **hold the shares**, and its board shows the holding moment.
- **The cut-off** — at each booking's cut-off: full → **every held share taken** (the take), its
  real fee recorded once Stripe reports it; still short → called off and **every hold let go**,
  nobody refunded because nothing was taken; a share already taken by the fallback is refunded in
  full (Q113). Its console press, *cut-off*, does the same.
- **On request timeout** — expired unanswered requests. Removed with *On request* (Q121), with its
  switch, its interval and its row in the jobs register, and its console press.
- **Time to pay** — at the end of a refused card's 30 minutes, whichever window it is — time to fix
  the card before the cut-off, time to pay after it (Q113): lets the kept holds go and offers the
  seat, or calls the game off when its book-by has come; tells the players (Q109). Until Q121 it
  also told the desk, after an Accept (Q112).
  At a holding, it opens the player's seat as a rescue; on a rescue, it
  offers the seat again.
- **Rescue dealing** — on every `SeatLeft`: Fill in's rescues, Seat open cards, Fill in alerts.
- **How did it go?** (Q119, Q120) — every 30 seconds, as the other money and seat jobs: tells the
  players of every Competitive booked game whose hour has ended. For fun games are told nothing.
- **Levels** (Q119) — a result settled by an acceptance is settled for rating from the outbox, for
  that one game; results settled by a window closing (silence, or the closer score) are caught up
  every minute. The hourly cadence retired.
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
  `GET /bookings/{id}` (details; the check-in code went with Q116), `GET /home`, `PUT
  /players/me/weekly-hours`, `GET/PUT /players/me/games-and-money`, `GET/PUT
  /players/me/notifications`, `POST /players/me/devices`, `POST /players/me/payment-methods/setup`
  (a SetupIntent — its id, never its secret), `POST /players/me/payment-methods/terms` (answers
  the secret), `POST /players/me/payment-methods/confirmation`, `GET` and `DELETE
  /players/me/payment-methods/current` (settled by #536, ADR-0190), `GET /players/me/payments`
  (live yeses + receipts),
  `POST /seat-charges/{id}/confirmation` (recovery), and since Q127 `POST /pools/{id}/deal` (the
  finding state's deal, `204`) and `GET /players/me/deck-counts?sport=` (the You tab's cost lines,
  `{sport, competitive, for_fun}`). Since Q115 and Q118, four routes carry the
  attendance acts on a game, each with a location fix in its body, and one sets the reliability
  filter; the no-show routes are gone. The tickets settle the paths.
- **Club surface** — `GET/POST/PATCH /club/courts`, `PUT /club/courts/{id}/hours`,
  `GET/POST/DELETE /club/exceptions`, `PUT /club/prices`, `GET/PUT /club/raketa-settings`,
  `POST /club/stripe/onboarding-link`, `GET /club/setup`, `GET /club/bookings?date&filter`,
  `POST /club/bookings/{id}/move|cancellation` — the cancellation takes a reason and an *anyway*
  flag and answers *moved* (with the court and its kind) or *called off*, beside a **cancel
  preview** — (`…/acceptance|refusal` and the waiting read went with Q121; `POST /club/check-ins`
  with Q116),
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

- **Clubs**, every one **Only Raketa** since Q121 (*a call*: each with a release lead that keeps its
  seeded games fillable), none with a check-in switch (Q116), with courts per sport, weekly Raketa
  hours, one exception, price bands, a linked (fake) payments account; **at least one with indoor
  and outdoor courts of one sport at the same hours**, so that a move by cancel, the weather rule and
  a card's kind can be walked (Q122); one club **not live** (half its checklist done) and one
  **paused**.
- **Members** with hourly weekly hours, spread so the posting grid shows every cell state.
- **For a protagonist**, in one group and sport: fresh picks; picks with 1, 2 and 3 In (one *Book
  it now*); a challenge with momentum and one whose poster withdrew; rescues before and after the
  cut-off; a post of their own on You’re in; booked games
  (one before, one after the cut-off, one on the day, and since Q113 one filled far ahead with its
  seats checked); since Q114 the evening nobody recorded reads *Played · no score*, and the
  protagonist's Player reliability is in points (Q117); a called-off game; receipts and a refund; a week at the
  games-per-week cap; a card above a price ceiling (for the filter). Past seeded games are taken and
  settled; upcoming ones are held, or checked with a holding time, as the rules say (Q113).
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
| `player/11_fill_in_tap_general.png` | Fill in with both sections and the FAB — two tabs since #844 ([split mocks 1 and 2](../fill-in-split/README.md)) |
| `player/12_fill_in_sets_to_fill_row.png` | The rescue row |
| `player/13_fill_in_youre_in_row.png` | The yes row, now on You’re in |
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
