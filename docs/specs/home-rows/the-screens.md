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

> **Amended by [#820](https://github.com/Raketa02/Raketa/issues/820)**
> ([ADR-0205](../../adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
> §4, §5; home refactor 3–13): the five rows fold into **FOR YOU**'s five lines. What waits for an
> answer moved behind the envelope with #816 and #817 ([the games screens A8](../games-and-fill-in/the-screens.md#a8-home)).
>
> **Amended by [#822](https://github.com/Raketa02/Raketa/issues/822)** (ADR-0205 §5, §6; home
> refactor 3, 4, 7): every line but Top 10 draws its count, and the people lines read *See all N ›*.
>
> **Amended by [#823](https://github.com/Raketa02/Raketa/issues/823)** (ADR-0205 §7; home refactor
> 5): Groups heating up's footer reads *All groups ›*, to the Groups heating up page (§3.6).

- **The header, *Get your level* and *Your games***, as ADR-0205 §4 orders them.
- **Then FOR YOU** (home refactor 3, 4): the eyebrow *FOR YOU*, grey caps, letter-spaced, and five
  quiet lines in this order — **Groups heating up**, **Players at your level**, **New in Raketa**,
  **Players with your vibe**, **Top 10**. *Only the words on screen change*: the rows' own names
  (Hottest groups, Same competitive level players, Same vibe players) stay the glossary's and the
  code's.
- **A closed line is a white card** with its title on the left and, on the right, a small grey
  **count pill** and a chevron (›), and nothing else: no faces, no subtitles, no tiles. Top 10 has no
  count.
- **The count is how many there are to explore** ([#822](https://github.com/Raketa02/Raketa/issues/822);
  ADR-0205 §6; home refactor 3, 4): *Groups heating up · 6*, *Players at your level · 99+*, *New in
  Raketa · 6*, *Players with your vibe · 14*. It is the line's **pool**, never how many of them are a
  good match: every group of 3 or more; everybody holding a level in a sport the reader plays;
  everybody who joined in the last 30 days; everybody sharing a tag with the reader
  ([the mechanics](the-mechanics.md) §5.10, §6.9, §7.5, §8.8). So in a busy city the people lines
  read *99+*, and that is meant. **The server counts up to 100**, which reads *100 or more*, and the
  phone draws ***99+*** past 99. The pill is mono, grey on a paler grey, quieter than the title, and
  **it stays when the line opens**. It refreshes whenever the line's read does — coming back to Home
  after 30 seconds, foregrounding, the pull, or a push or a write that re-reads the row — and nothing
  polls for it. A friend tapped on a card leaves it as read, as it leaves the card in its place.
- **A tap anywhere on a closed line opens it, and one line is open at a time**: tapping another line
  folds the first, then unfolds the second. **Only the open line's header closes it** — a tap on a
  tile, a swipe along the rail, a footer link or Top 10's pill never does.
- **The open line** has an ink border, a soft shadow and the chevron pointing down. Under its header,
  **today's tiles**, sideways, **settling on tile edges**; at the bottom right of the open content,
  **its footer**: *See all N ›* on the three people lines, to their See all screens — N the line's
  count, *99+* included, though See all shows one sport at a time (#822; home refactor 7); on Top 10, the
  sport switcher, *Padel ›*, on the left, opening to the right, and *Open the rankings ›* on the
  right ([#821](https://github.com/Raketa02/Raketa/issues/821), §7.1; home refactor 12, 13); on
  Groups heating up, ***All groups ›***, to its page ([#823](https://github.com/Raketa02/Raketa/issues/823),
  §3.6; home refactor 5).
- **Motion** (designed, no mock): the content unfolds and fades in over about a quarter of a second,
  fast at first and settling; the lines below slide down rather than jump; closing is a little
  shorter; and if what opened would be cut off at the bottom, the page eases down just enough to show
  it. **Under Reduce motion, all of it is instant.**
- **Which line is open**: none at app start; the one open is kept across tab switches while the app
  lives, and never across a restart. **For a player in no group, Groups heating up starts open**, and
  *Your games* reads *Join a group to get games — see Groups heating up, just below.* where *⚡ Play
  finds you one.* stood.
- **A line shows only once its read has returned something.** While it loads, empty or failed, it is
  hidden, and the others stand; with all five hidden, FOR YOU goes too. A line that empties while open
  closes and goes. Top 10 is hidden only when nobody is ranked anywhere: *Nobody ranked in squash yet*
  stays inside it.
- **Every line still reads when Home opens**, open or not. **Pull-to-refresh** re-reads every line;
  **coming back to Home** re-reads them when the last read is older than 30 seconds. **Top 10's pill**
  re-reads that line alone.
- **Spoken**: each line is a button that says its title, its count as drawn and whether it is
  expanded or collapsed — *Players at your level, 14, collapsed*; the pill is not read a second time.
  Each footer link is a button of its own, and keeps its name: *See all players at your level*.
- **The Home tab stays lit** on every See all screen and sheet opened from Home (home rows 12, 19, 24).

### 2. The row frame, and the folding line

**One frame in shared UI**, built first and used by today's rows and the five new ones: the heading,
an optional *See all ›*, an optional slot for a control (Top 10's pill and *Rankings ›*), and the
sideways rail. Moving today's rows onto it changes nothing on screen
([#798](https://github.com/Raketa02/Raketa/issues/798)).

**Since [#820](https://github.com/Raketa02/Raketa/issues/820), the five rows are folding lines** (ADR-0205
§9.5): a line is a card holding its title and chevron, and, open, the frame's sideways rail — its
tiles a share of the line's content, cut at the line's own edge — and a **footer row** at the bottom
right carrying the links that stood on the heading. The frame's heading keeps no link or control; it
draws Needs your answer's sections and *Your games*.

### 3. Hottest groups

#### 3.1 The row (home rows 1, 21)

- **Up to 6 group cards**, HOTTEST first, then GROWING, then untagged ([the mechanics §5.4](the-mechanics.md#54-order-and-the-six-q10)).
- **At the open line's foot, on the right, *All groups ›*** ([#823](https://github.com/Raketa02/Raketa/issues/823);
  home refactor 5), to the Groups heating up page (§3.6). It had no *See all* before.

#### 3.2 The card (home rows 3, 3.2, 4, 5)

- **A white card on paper** with a light border.
- **A striped band across the top in the group's colour**, the group's badge — its monogram on a
  shield — overlapping the band and the body.
- **The tag top-right**, a dark pill: *▲ HOTTEST* (home rows 3) or *+ GROWING* (home rows 4), the mark
  in volt. **No tag** on the rest (home rows 5).
- **The name**, bold.
- **Two figures**, mono: *14* over *games this week* on the left, *11* over *players* on the right,
  held against the card's edge (home refactor 5.1).
- **No sport line, no *+N this month*, no heat bar** — the card is slimmer since
  [#821](https://github.com/Raketa02/Raketa/issues/821) (ADR-0205 §5, Q22; home refactor 5.1). It
  drew the sports as dots and names cut with an ellipsis, a green *+3 this month* beside the players,
  and a heat bar filled by the card's heat share (home rows 3, 4). **The group sheet keeps the sports
  and *new this month*** (§3.3); the heat still orders the cards and picks the tags
  ([the mechanics §5.5](the-mechanics.md#55-the-heat-bar)) and is drawn nowhere.
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

#### 3.6 The Groups heating up page (designed, no mock)

Built by [#823](https://github.com/Raketa02/Raketa/issues/823) (ADR-0205 §7, Q18, Q35, Q36): **no mock
draws it**, so it is made of the line's card and the people See all screens' frame (§4.4, §5.3).

- **Pushed over Home** by the line's *All groups ›*, the Home tab still lit. **Back** (‹) is Home, the
  line still open.
- **Header:** ‹ and *Groups heating up*, the screen's title. **No sport pill**: the page has no filter.
- **Body:** every group with 3 or more players, **in the row's order** — HOTTEST, then GROWING by heat,
  then the rest by heat ([the mechanics §5.10](the-mechanics.md#510-its-total-and-the-groups-heating-up-page-adr-0205-6-7)) —
  so its first six are the line's. One card to a line, **the line's card (§3.2) at the content's whole
  width**, 9 between cards. **The reader's own groups are listed too**, their chip *You're in*.
- **Paging:** 20 at a time, the next read as the list nears its end, as on See all. A group read again
  by a later page — its heat moved between the two reads — is drawn once, where it first stood.
- **Taps:** a card opens **the line's group sheet** (§3.5); the chips (§3.2's table) make the line's
  writes, drawn at once (§3.4), and **the card moves on the line under the page too**, so the two never
  disagree. *You're in* and *Open group* open the group page over this one.
- **Every state is See all's:** a spinner while the first page reads, *Reading groups heating up…* to a
  listener; a failure said with *Try again*; offline, the resume line; a later page refused, said
  under the list with its own *Try again*; the end, where nothing more is read; and the pull, which
  reads every page again. **An empty list** — every group dropped under 3 since the line was read —
  reads *No groups heating up right now* *(a call)*.
- **Spoken:** the title is the screen's header; each card is named as on the line (*Ogrody 33 Club,
  hottest, 14 games this week, 11 players*), and each chip by what it does (*Ogrody 33 Club: Ask to
  join*). Every target is 44 pt.

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
- **The footer:** *2 sports ›* in volt when they share more than one sport, and the round button.
  With one, the button alone. **No gap in words** since
  [#821](https://github.com/Raketa02/Raketa/issues/821) (ADR-0205 §5, Q22; home refactor 7): the card
  read *0,02 below you*, *0,09 above you* or *Same level* before *· 2 sports ›*; the comparison sheet's
  blocks still say it (§4.3), and the card's pairing no longer speaks it. Everything else stays.
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

- **The heading:** *TOP 10*, the sliding sport pill (*● Padel ‹*), and *Rankings ›* on the right —
  the row's, until FOR YOU's line (§1, #820). **Since [#821](https://github.com/Raketa02/Raketa/issues/821)**
  (ADR-0205 §5, Q19, Q37; home refactor 12, 13) **the open line's footer** holds them: **the sport
  switcher on the left**, *● Padel ›*, its chevron pointing the way it opens (§7.3), and ***Open the
  rankings ›*** on the right, in *Rankings ›*'s place, going where it went
  ([the mechanics §10.4](the-mechanics.md#104-taps)). **The closed line shows neither.**
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

- **The deck's sliding sport pill**, lifted to shared UI by #774. Opened, it slid over the heading:
  the other sports in the app's order, then the chosen one in ink with *›*. **Since
  [#821](https://github.com/Raketa02/Raketa/issues/821) it opens to the right** from the footer's left,
  with today's animation (designed, no mock): the chosen one first, in ink with *‹*, where the pill
  stood, then the other sports in the app's order, sliding out after it — the bar lies over the
  footer, *Open the rankings ›* included, and a tap anywhere on the footer folds it.
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
- **The group card**: the striped band, the overlapping shield badge, the tag pill, the heat bar
  (retired with the slimmer card, #821).
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
