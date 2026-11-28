# Rankings — the screens

> **Status:** from the rankings grilling of 2026-11-07 and PRD
> [#766](https://github.com/Rakieta02/Rakieta/issues/766), recorded by
> [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md).
>
> **What it is:** how each Rankings screen looks and behaves: the trophy, then the page section by
> section with every state. The rules are in [the-mechanics.md](the-mechanics.md); where the two
> disagree on a rule, the mechanics win, and on a look, this document does. Every sentence is
> [the words §30](../matchmaking/the-words.md#30-rankings)'s. A sentence quoted here only says where it
> stands; where a quote and §30 differ, §30 wins.
>
> **How to read the mocks:** they are under [`mocks/`](mocks/), cited as *rankings 4*, and
> [the README](README.md) says which parts of each lead and lists every override. **Every name,
> number, place and chip in a mock is sample data.** A screen no mock draws is marked **designed, no
> mock**: it is built from the mocks' own parts and the locked design system
> (`frontend_player/docs/design-system.md`), and any departure from the design system becomes a Part
> 16 row ([§10](#10-design-system-work)).
>
> **The people in every example:** **Tomek** is the reader, 7th of 13 in padel at 2,71. **Karol** sits
> just above at 2,75, **Zofia** just below at 2,69, and **Inés** at the top at 3,40.
>
> **Amended 2026-11-14** by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2 (Q131, PRD [#789](https://github.com/Rakieta02/Rakieta/issues/789)):
> every row is shown to every reader, blocked ones included, so [§4.5](#45-hidden-from-general-designed-no-mock)
> is retired, [§5.1](#51-the-podium-rankings-4-6)'s podium is simply the first three, a blocked row's
> tap reads *This record isn't available* ([§6](#6-the-record-from-the-ranking-designed-no-mock)), and
> [§8](#8-you--show-me-in-general-designed-no-mock)'s switch moves to *Show me to new people*. Home's
> **Top 10** is [the home rows screens §7](../home-rows/the-screens.md#7-top-10).

---

## Part A — The player app

### 1. Home — the trophy (rankings 1)

- **A dark pill on Home's header, just left of the bell** (Q13). The bell keeps the corner.
- **It reads the trophy and the place**, *🏆 #7*, as rankings 1 draws it. The trophy is drawn, never
  the character, and the number is mono.
- **The place is the trophy's sport and the remembered view's** ([the mechanics §8](the-mechanics.md#8-homes-trophy)).
- **No number**: the trophy alone, when the reader has no place there. It is still a button.
- **A tap opens Rankings** on that sport and view.

### 2. The header (rankings 2, 4)

- **‹** on the left, back to Home.
- **Rankings**, the page title, and ***Competitive games only*** under it, small and grey (Q11). No
  mock draws the subtitle.
- **The sport pill on the right**, the deck's own control, lifted to shared UI
  ([#774](https://github.com/Rakieta02/Rakieta/issues/774)): the sport's dot and name, opening to the
  others. **It offers all four sports**, the reader's rated sports first, then the rest in the app's
  sport order.
- **Switching sport re-reads the page.**
- **The Home tab stays lit** while Rankings is open (Q11).

### 3. General | Friends (rankings 2)

- **A two-way segmented control** under the header: **General** · **Friends**.
- **The view is remembered per account on the phone**, General the first time. Home's trophy reads
  the same choice.
- **Switching view re-reads the page.** Everything below is recomputed for the view.

### 4. Your place card

**The dark card under the switch.** When there is no place to show, the card is replaced by one of
the not-listed cards of §4.3–§4.6, in the same place.

#### 4.1 Listed (rankings 3)

- **Left**: the eyebrow *YOUR PLACE*, the place in volt and large, *7th*, and *of 13* beside it.
- **Right**: the level, *2,71*, and under it the chip with its words: *▲ 1 up this week*, *▼ 1 down
  this week*, *— no change this week* or *New this week*.
- **Under a fold line**: the gap line ([§4.2](#42-the-gap-line)).

#### 4.2 The gap line

The numbers in it are bold, as rankings 3 draws *0,04* and *0,02*. The cases are the mechanics
[§7](the-mechanics.md#7-the-gap-line)'s:

- *0,04 behind Karol · one win closes it · Zofia is 0,02 behind you*;
- *0,04 behind Karol · about 3 wins close it · Zofia is 0,02 behind you*;
- *0,31 behind Karol · Zofia is 0,02 behind you*;
- *Level with Ewa · one win puts you ahead · Zofia is 0,02 behind you*;
- … *· Zofia is level with you*, when the player below is level;
- *0,04 behind Karol · one win closes it*, in last place;
- *Top of the list*, in first place.

It names only rows the reader can see.

#### 4.3 Not listed in General (designed, no mock)

A light card in the dark card's place, one line, no button:

- **Fewer than 5 results**: *2 of 5 games — 3 more competitive padel games put you on the list*; with
  4, *4 of 5 games — 1 more competitive padel game puts you on the list* *(a call: the count stays)*.
- **Off the list**: *Off the list — no competitive padel game in 90 days. Your next one puts you
  back.*

#### 4.4 No level in this sport (designed, no mock)

- **General**: *No squash level yet — get one, then 5 competitive games put you on the list*.
- **Friends**: *No squash level yet — get one, then one competitive game puts you on the list*.
- **The button, in both**: **Get your squash level** (coral). It starts that sport's questionnaire,
  and the pass returns to Rankings, on the same sport and view.

#### 4.5 Hidden from General (designed, no mock)

- **The dark card, with the place**: *YOUR PLACE · 7th · of 13*, the level and the chip, as §4.1.
- **The gap line is replaced** by *Hidden from General* and the switch, on the fold line's right. The
  switch is You's own setting, written by the same route; turning it on brings the gap line back.

> **Retired 2026-11-14** (ADR-0204 §2). Nobody is hidden from General, so the card always has its gap
> line, and the page has no switch.

#### 4.6 The Friends view (designed, no mock)

| Reader | Friends listed | The card | Below it |
| --- | --- | --- | --- |
| Listed | at least one | §4.1, with the Friends place | the podium (with three visible rows) and the table |
| Listed | none | *Just you so far* and **Add friends** | nothing |
| Not listed | at least one | the reader's not-listed card: *Not ranked in padel yet — your first confirmed competitive game puts you on the list*, §4.4's Friends card, or §4.3's *Off the list* | the friends' podium and table (Q7) |
| Not listed | none | *None of your friends is ranked in padel yet* and **Add friends** | nothing |

- **Add friends** opens the existing Add friends sheet: your groups, and your friend link
  ([the friends screens §5](../friends/the-screens.md#5-the-add-friends-sheet-friends-4)).
- **Friends ignores *Show me in General***: a hidden friend is in the table. *(Since 2026-11-14 no switch
  hides anybody, in either view.)*

### 5. The podium and the list

#### 5.1 The podium (rankings 4, 6)

- **The first three rows the reader sees, on three steps.** First in the middle on the tallest step,
  volt; second on the left, white; third on the right, white and slightly lower than second.
- **Each shows** the face, the nickname and the level. **Each step is labelled with its true place**:
  with second hidden from the reader, the steps read 1, 3 and 4.
- **A tap opens the record.**
- **Only with at least three rows visible to the reader.** With one or two, the list shows alone.

> **Amended 2026-11-14** (ADR-0204 §2). Every row is visible, so the podium is **places 1, 2 and 3**,
> shown when at least three players are listed.

#### 5.2 A row (rankings 7–11)

One row per listed player the reader can see, best first, on one white card:

- **The place**: coral for places 1–3, grey for the rest (rankings 7). A true place, so a hidden or
  blocked row leaves a gap.
- **The face and the nickname.** The reader's own row reads **You** and is tinted (rankings 11).
- **The form**: the last five results in this sport, oldest first, a green square for a win and a
  grey one for a loss, fewer when fewer exist and never padded: the record's **Run of form**.
- **The chip** (rankings 8–10): *▲ 2* on mint, *▼ 1* on a red tint, *—* on grey, or *New*.
- **The level**, right-aligned, mono.
- **A tap on the face or the row opens the record** (§6). The reader's own row opens their own record.

#### 5.3 Paging and the jump button (designed, no mock)

- **General loads in pages of 50.** Scrolling to either end loads the next page that way.
- **A floating *You · 212th* button** shows whenever the reader's row is off screen, at the foot,
  above the tab bar.
- **A tap loads the page around the reader**, the row in the middle of the screen, and scrolling
  either way loads more.
- **It hides while the reader's row is visible**, and isn't shown when the reader isn't listed, or, in
  General, is hidden.
- **Friends is shown whole** and has the same button. Friends ignores the switch.

#### 5.4 An empty sport (designed, no mock)

- ***Nobody ranked in badminton yet*** where the podium and the list would be, under the reader's
  card.

### 6. The record from the ranking (designed, no mock)

- **Any face or row opens the full player record**, a stranger's too
  ([the mechanics §12](the-mechanics.md#12-records-q12)).
- **The foot** keeps the friends screens' [§2](../friends/the-screens.md#2-the-player-record--add-friend-beside-block-designed-no-mock)
  row, with two changes:
  - **Add friend shows only when a request may be sent**, which the record says. Otherwise **Block**
    stands alone *(a call)*.
  - **There is no Unblock**: a blocked pair's record never opens. Unblock is in You › Blocked
    players.
- **Add friend from a record opened on Rankings** sends the request from the ranking, with the
  page's sport.
- **The daily limit**: when it is reached, the request is refused and the record shows *You've sent
  10 requests to new people today. Try again tomorrow.* under the buttons. Nothing is sent.
- **Block** confirms as today, and **closes the sheet** once it is made, because the record no longer
  opens for either of them *(a call)*. The confirmation names You › Blocked players as the way back.
- **A refused record** reads the record's one line, *This record isn't available.*, as today.

> **Amended 2026-11-14** (ADR-0204 §2). **A blocked player's row is on the page**, and a tap on it
> reads *This record isn't available.* Add friend shows on every record that opens, and **the
> daily-limit line is gone**. The record shows all of the subject's photos.

### 7. Home's request card (designed, no mock)

The friends screens' [§6.2](../friends/the-screens.md#62-friend-requests--n-friends-5) card, with
***Found you in the padel ranking*** in place of the group line, as a link's *Invited you to Rakieta*
stands. The notice's body reads the same.

### 8. You — Show me in General (designed, no mock)

- **A row with a switch**, on by default, in **ON YOUR CARD**, after *Nickname*: ***Show me in
  General***, with *Players who don't know you can see your place, open your record and send you a
  request.* under it ([the You spec §3.14](../you/the-you-screen.md#314-show-me-in-general)).
- **It writes at once**, with no Save, and reverts with the write's own error if the write fails.

> **Replaced 2026-11-14** (ADR-0204 §2). The row is ***Show me to new people***
> ([the home rows screens §9.1](../home-rows/the-screens.md#91-you--show-me-to-new-people)), and it
> changes nothing on this page.

### 9. Notices

**None.** No push, bell line or email about the ranking (Q10).

### 10. Design-system work

The mocks lead on design, and the design system is locked. Where a mock departs from it, the build
records a Part 16 row in `frontend_player/docs/design-system.md` or picks the meaning, as for the
games and fill-in screens:

- **Coral places 1–3** (rankings 7) are a seventh use of coral against §1.2's closed list of six.
- **The chip's mint, red and grey tints** (rankings 8–10): mint means *settled* and red *ended badly*,
  and here they mean up and down.
- **The volt place and the volt first step** (rankings 3, 6): volt is a fill anywhere and a stroke
  only on dark, which both obey.
- **The tinted *You* row** (rankings 11).
- **The trophy pill** (rankings 1), a dark pill on Home's header beside the bell.

---

## Part B — The backend, inferred

[The mechanics §16](the-mechanics.md#16-where-it-lives-inferred) has the projection, its ports, the
routes and the seed. The tickets settle them.
