# Home rows — the screens

> **Status:** agreed in the Home rows grilling on 2026-11-13/14, specified as PRD
> [#789](https://github.com/Raketa02/Raketa/issues/789), recorded by
> [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md).
>
> **Its companion** is [the-mechanics.md](the-mechanics.md), which says what happens. This document
> says how each row, card, sheet and See all looks, in every state, and which mock draws it:
> *(home rows 7)* cites [the index](README.md#index). A state no mock draws is marked *(designed, no
> mock)*, and is made from the mocks' own parts and the player design system. The words are
> [§31](../matchmaking/the-words.md#31-home-rows)'s, cited by their place there.
>
> **The mocks lead on the look and on nothing else**, with the overrides in
> [the README](README.md#overrides). Every name, face, number and tag below is sample data.

---

## Part A — The player app

### 1. Home, top to bottom

- **The header and today's rows stay as they are** (designed, no mock): the title, the trophy and the
  bell; *Get your level*, **FRIENDS GAME**, *To confirm*, **FRIEND REQUESTS**, **ASKED FOR A LEVEL**,
  *Your games* ([the games screens A8](../games-and-fill-in/the-screens.md#a8-home)).
- **Then the five rows** (home rows 1, 2): *HOTTEST GROUPS*, *SAME COMPETITIVE LEVEL PLAYERS*, *NEW IN
  RAKETA*, *SAME VIBE PLAYERS*, *TOP 10*. Each heading is grey caps, letter-spaced, with *See all ›*
  in ink on the right where the row has one; *TOP 10* carries the sport pill and *Rankings ›*
  instead.
- **Each row is a sideways rail**, the last card cut at the right edge to show there is more.
- **A row with nothing to show is gone with its heading.** A row still loading keeps its place
  without blinking the others; a row that fails is left out *(a call)*.
- **The groupless line** (designed, no mock): with no group, *Your games* reads *Join a group to get
  games — the hottest ones are just below.* where *⚡ Play finds you one.* stood.
- **Pull-to-refresh** re-reads every row; **coming back to Home** re-reads them when the last read is
  older than 30 seconds. **Top 10's pill** re-reads that row alone.
- **The Home tab stays lit** on every See all screen and sheet opened from Home (home rows 12, 19, 24).

### 2. The row frame

**One frame in shared UI**, built first and used by today's rows and the five new ones: the heading,
an optional *See all ›*, an optional slot for a control (Top 10's pill and *Rankings ›*), and the
sideways rail. Moving today's rows onto it changes nothing on screen
([#798](https://github.com/Raketa02/Raketa/issues/798)).

### 3. Hottest groups

#### 3.1 The row (home rows 1, 21)

- **Up to 6 group cards**, HOTTEST first, then GROWING, then untagged ([the mechanics §5.4](the-mechanics.md#54-order-and-the-six-q10)).
- **No *See all***.

#### 3.2 The card (home rows 3, 3.2, 4, 5)

- **A white card on paper** with a light border.
- **A striped band across the top in the group's colour**, the group's badge — its monogram on a
  shield — overlapping the band and the body.
- **The tag top-right**, a dark pill: *▲ HOTTEST* (home rows 3) or *+ GROWING* (home rows 4), the mark
  in volt. **No tag** on the rest (home rows 5).
- **The name**, bold.
- **The sports** as coloured dots and names, cut with an ellipsis when they don't fit.
- **Two figures**, mono: *14* over *games this week*, *11* over *players*, and a green bold *+3 this
  month* beside the players when the group grew. With no growth the *+N this month* is left out
  (designed, no mock).
- **The heat bar**, full width, a gradient fill over a pale track, filled by the card's heat share.
- **Up to 4 overlapping faces**: the reader's friends first, then the longest-standing members. A
  3-member group shows the faces it has (designed, no mock).
- **The chip** at the foot:

| State | Look | Mock |
| --- | --- | --- |
| **Join** | black pill, white text | home rows 5 |
| **Ask to join** | black pill, white text | home rows 3 |
| **Asked** | white pill, light border, ink text | home rows 3.2 |
| **You're in** | outlined white pill | home rows 4 |

- **A tap on the chip** acts ([the mechanics §5.7](the-mechanics.md#57-the-chip-and-the-readers-relation)).
  **A tap anywhere else** opens the group sheet.

#### 3.3 The withdraw sheet (designed, no mock)

- **A small sheet over Home**, from *Asked* on a card or on the group sheet: *Waiting for Ogrody 33 to
  answer*, and **Withdraw request** under it, the design system's destructive-outline button.
- **Withdraw** closes the sheet and turns the chip to *Join* or *Ask to join*. No toast: withdrawing
  tells nobody, the reader included *(a call)*.

#### 3.4 Join and Ask to join

- **Join** turns the chip to *You're in* at once, and the reader is a member. Hottest groups, *Your
  games* and the groups read are read again.
- **Ask to join** turns the chip to *Asked* at once.
- **A failed write** puts the chip back and says the write's own error, as the record's buttons do.

#### 3.5 The group sheet (home rows 6)

**A bottom sheet over dimmed Home**, white, rounded top corners, a grabber, and a **× in a beige
circle** top-right.

- **Title row:** the name, bold, and the **one button** at its right end beside the ×:

| State | Look | Mock |
| --- | --- | --- |
| **Asked** | cream-amber, brown-gold text | home rows 6 |
| **Join** | black pill, white text | designed, no mock |
| **Ask to join** | black pill, white text | designed, no mock |
| **Open group** | outlined pill, ink text; opens the group page and closes the sheet | designed, no mock |

- **Identity row:** the rounded-square badge with its monogram; *Closed group · run by Ogrody 33 ·
  Ogrody 33* (home rows 6), or *Open group · …* and *run by tomek.k* for a Player group (designed, no
  mock); the sports as dots with every name written out.
- **Two outlined stat cards**, mono figures: *14* over *games this week*; *11* with a green *+3* over
  *players · new this month*.
- **People row:** up to 6 overlapping faces and *7 of your friends play here* (home rows 6), *1 of
  your friends plays here* or *11 players* (designed, no mock).
- **Nothing on the sheet but the button opens anything.** The faces are not buttons.

### 4. Same competitive level players

#### 4.1 The row (home rows 1, 7)

- **10 dark cards**, in [the mechanics §9](the-mechanics.md#9-keeping-the-rows-alive)'s order.
- **Hidden** while the reader has no level (designed, no mock).

#### 4.2 The card (home rows 7, 8, 10, 10.2, 10.3)

**A dark card.** Top to bottom:

- **The pairing:** on the left the reader's face, *You* and the reader's level, mono; on the right
  the other's face, nickname and level. **Between them** the % in its colour (green, amber or red;
  home rows 7, 16, 15), *EVEN* under it in grey caps, and the sport with its dot.
- **The comparison bar** on the Skill passport scale, 1,00–5,00: a track in four bands, each a dark
  tint of its own (home rows 10.3), with *New · Developing · Established · Advanced* underneath, the
  reader's own band in white bold; the bar **filled in volt from the left up to the other's level**;
  the reader as **a tall white mark labelled *YOU***. A fill short of the mark means they are below,
  one past it above (home rows 7, 8).
- **The footer:** the gap in words, *0,02 below you*, *0,09 above you* or *Same level* (designed, no
  mock), then *· 2 sports ›* in volt when they share more than one sport. With one, the footer is the
  gap alone (designed, no mock).
- **The round friend button** ([§8](#8-the-round-friend-button-and-its-sheets)).
- **Taps:** the other's face or nickname opens their record; *N sports ›* opens the comparison sheet;
  the button acts. Nothing else on the card is a button *(a call)*.

#### 4.3 The comparison sheet (home rows 9, 11)

**A bottom sheet**, white, a grabber and the ×.

- **Title:** *You vs zofia.b*, and the sheet's friend button at its right end: *✓ Friends* (mint,
  green text; home rows 9), *+ Add friend* (black pill; home rows 11), *Request sent* or *Accept*
  (designed, no mock; §8).
- **One block per shared sport, most even first**, divided by hairlines:
  - the sport with its dot, and *You 2,71 · zofia.b 2,69* on the right, mono;
  - **the same bar in the light theme**: a fill in the theme's `mint` (the mid green) over the pale
    band tints, an ink mark labelled *YOU*, the four band names with the reader's in bold;
  - the gap in words, and a tag ***91% even*** in the light version of its colour: mint with green
    text, cream with amber text, or a pale red with red text (home rows 9, 11 draw the first two;
    the colour follows the rule, not the mock).
- **Three or four blocks** stack the same way, and the sheet scrolls (designed, no mock).

#### 4.4 See all (home rows 12–16)

- **Header:** ‹ back to Home, *Same competitive level players* bold (two lines where it wraps), and
  the sliding sport pill on the right, *● All ‹* with a two-tone dot.
- **Body:** one full-width dark card per row, best % first, friends where they fall, loaded in pages
  of 20 as the list scrolls.
- **The pill** offers *All* and the sports the reader shares with somebody. Picking a sport
  re-compares every card in that sport (designed, no mock).
- **Every card keeps its *N sports ›***.

### 5. New in Raketa

#### 5.1 The row (home rows 1, 17, 17.2)

- **Up to 10 tall portrait tiles**, in [the mechanics §7.2](the-mechanics.md#72-the-row-of-10-q5-q22)'s order.

#### 5.2 The tile (home rows 18, 18.2, 18.3)

- **The photo or the court poster fills the tile edge to edge**, with a dark fade at the bottom.
- **A volt *NEW* tag** top-left.
- **The round friend button** top-right (§8).
- **Over the fade:** the nickname, bold; every sport they have a level in, each on its own line with
  its dot and level, mono; and *Joined 2 days ago*. **A player with no level** has no sport lines
  (designed, no mock).
- **A tap anywhere but the button** opens the record.

#### 5.3 See all (home rows 19, 19.2)

- **Header:** ‹, *New in Raketa*, and the pill, *● All ‹*. **Opened**, it slides over the title, the
  sports first and the chosen one last in ink with *›* (home rows 19.2).
- **Body:** the same tiles in a two-column grid, newest first, two sports to a line where they fit,
  loaded in pages of 20.
- **A sport that leaves nobody:** *Nobody new plays squash yet*, in place of the grid (designed, no
  mock).

### 6. Same vibe players

#### 6.1 The row (home rows 2, 20, 20.1)

- **10 pale tiles**, in [the mechanics §9](the-mechanics.md#9-keeping-the-rows-alive)'s order.

#### 6.2 The tile (home rows 22, 22.1, 22.2, 22.3)

- **A pale card tinted in the colour of the player's court poster** — the colour that never changes
  for them — washing in from the top-left, with a light border.
- **The vibe %** top-right in a white circle.
- **The face, the nickname, and *6 things in common*** (*1 thing in common*).
- **The shared tags as green chips** (mint, green bold text): as many whole chips as fit in **three
  lines**; when more remain, a dashed *+2 more* takes the last place. Three lines is the cap on the
  Home tile and in See all alike.
- **The round friend button** bottom-right (§8).
- **A tap anywhere but the button** opens the vibe sheet.

#### 6.3 The vibe sheet (home rows 23)

**A bottom sheet**, white, a grabber and the ×.

- **Title row:** *You and karol.t*, and the sheet's friend button (§8): *✓ Friends* (home rows 23),
  *+ Add friend*, *Request sent* or *Accept* (designed, no mock).
- **Identity row:** the face — **a tap opens the full record** — the nickname, and *6 things in
  common · In your area · 0,6 km*, or the kilometres alone, or nothing, as the record writes it.
- **The photos:** all of them, a sideways carousel of large rounded cards, starting at the sheet's left
  padding and snapping photo by photo. **With no photo**, the carousel is left out *(a call)*.
- **The intro**, in italic between curly quotes, as the record draws it. With none, it is left out.
- **The tags:** all of the player's tags as chips, the shared ones green and reading *· you too*, the
  others grey, as on the record.

#### 6.4 See all (home rows 24)

- **Header:** ‹, *Same vibe players*, and the pill.
- **Body:** the same tiles in a two-column grid, most in common first, friends where they fall, in pages
  of 20. Every tile opens the same sheet.

### 7. Top 10

#### 7.1 The row (home rows 2, 25, 25.1, 25.2, 25.3)

- **The heading:** *TOP 10*, the sliding sport pill (*● Padel ‹*), and *Rankings ›* on the right.
- **Up to 10 cards**, places 1 to 10, the row ending at the last ranked player.
- **A sport with nobody ranked:** *Nobody ranked in squash yet*, one line in the row's place under the
  heading (designed, no mock).
- **One or two ranked:** those cards alone (designed, no mock).

#### 7.2 The card (home rows 26, 26.1)

- **A huge numeral, 1 to 10**, in a night-to-teal gradient with a paper outline, tucked behind the
  card's left edge so the card overlaps it. *10* in two digits (home rows 25.3).
- **The portrait card:** the photo or the court poster with a dark fade, and over it the nickname,
  the level (mono) and the chip: a triangle and a bold italic number, **▲ in volt, ▼ in coral**, with
  no background. **No chip** for no change or *New* (designed, no mock).
- **The reader's own card** reads *You*, its numeral turns volt and the card gets a volt ring (home
  rows 26.1).
- **A tap** opens the record, or *This record isn't available* across a block.

#### 7.3 The pill (home rows 27)

- **The deck's sliding sport pill**, lifted to shared UI by #774. Opened, it slides over the heading:
  the other sports in the app's order, then the chosen one in ink with *›*.
- **All four sports**, always.
- **A pick swaps the ten cards** and changes nothing else on Home.

### 8. The round friend button and its sheets

#### 8.1 The round button (home rows 8, 10.3, 17, 18–18.3, 20, 22–22.3)

| State | Look | Mock |
| --- | --- | --- |
| **+** | white circle, ink plus, on every card and tile | home rows 8, 18.2 (on the pale tile, override 9) |
| **…** | brown circle, white dots | designed, no mock |
| **✓** | green circle, white tick | home rows 7, 18.3, 22.1 |
| **The envelope** | volt circle, ink envelope, a paler volt halo | home rows 10.3, 18, 22 |

- **+** turns to **…** at once; **the envelope** to **✓** at once. A failed write puts it back.
- **Each carries a spoken name** ([§31.9](../matchmaking/the-words.md#319-the-friend-button)), the
  button's name for tests: the app is not built for screen readers (ADR-0198).

#### 8.2 On a sheet

- **Worded**, at the title row's right end: *+ Add friend* (black pill, home rows 11), *Request sent*
  (outlined, brown text, designed), *✓ Friends* (mint, green text, home rows 9, 23), *Accept* (coral,
  designed, as the record's).

#### 8.3 Request sent (designed, no mock)

- **From …**: a small sheet, *Request sent*, and **Cancel request** under it. Cancelling turns the
  button to **+** and tells nobody.

#### 8.4 Remove a friend (designed, no mock)

- **From ✓**: the record's own confirmation, *Remove karol.t as a friend?*, its body, **Remove
  friend** and **Keep** ([the friends screens §2](../friends/the-screens.md#2-the-player-record--add-friend-beside-block-designed-no-mock)).
  Removing turns the button to **+**.

#### 8.5 One tap, everywhere

- **After any friend write**, every row, See all and sheet on Home that shows that person shows the
  new state, through the reads it re-reads ([the mechanics §13](the-mechanics.md#13-reading-again)).

### 9. Who sees whom, on screen (designed, no mock)

#### 9.1 You — *Show me to new people*

- **The ON YOUR CARD row** that was *Show me in General*, now ***Show me to new people***, with
  *Players you don't share a group or a game with can find you on Home, open your record and send you
  a request.* under it, and the switch on the right
  ([the You spec §3.14](../you/the-you-screen.md#314-show-me-in-general)).
- **It writes at once**, with no Save, and puts itself back with the write's error if the write fails.

#### 9.2 The Rankings page

- **No switch**, and no *Hidden from General* card: [the rankings screens §4.5](../rankings/the-screens.md#45-hidden-from-general-designed-no-mock) is retired.
- **Every row is shown**, blocked ones included. A tap on a blocked player's row reads *This record
  isn't available*.

#### 9.3 The record

- **All photos**, in the record's header, as the vibe sheet's carousel draws them *(a call: the record
  and the sheet draw one carousel)*.
- **Add friend** follows ADR-0204 §2's rule, and there is **no daily-limit sentence**.
- **Opened from a row**, it sends its request from that row.

#### 9.4 Home's request card

- **The friends screens' §6.2 card**, with [§31.10](../matchmaking/the-words.md#3110-request-lines)'s
  line in place of the group line.

### 10. Notices

**None.** No push, bell line or email about any row, nor about a withdrawn Join request.

### 11. Design-system work

New parts, each a row in the design system's Part 16 when its ticket builds it:

- **The row frame** (§2), in shared UI.
- **The group card**: the striped band, the overlapping shield badge, the tag pill, the heat bar.
- **The comparison bar**, dark and light: four tinted bands, a fill, a tall mark with *YOU*. It reads
  the Skill passport's scale and bands, never new ones.
- **The portrait tile** with its fade and a corner tag (New in Raketa, Top 10).
- **The tinted pale tile** (Same vibe), its tint taken from the court poster's hue.
- **The Top 10 numeral**, a gradient with a paper outline.
- **The round friend button**, four states, and its worded sheet version.
- **The sheet's ×** in a beige circle, where today's sheets close by the grabber alone *(a call: the
  mocks draw it on every sheet, so it is drawn on these four)*.

---

## Part B — The club website

**Its Join requests list drops a withdrawn request**, on its next read. Nothing else changes, and
nothing tells the club a request was withdrawn.

---

## Part C — The backend, inferred

[The mechanics §16](the-mechanics.md#16-where-it-lives-inferred) holds the proposed shapes, and the
tickets settle them: the five row reads, the three paged See all reads with an optional sport, the
on-screen reports, Withdraw, the switch, the record's photos, and the ranking without its hidden
state.
