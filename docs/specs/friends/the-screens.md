# Friends — the screens

> **Status:** from the friends grilling of 2026-11-05/06 and PRD
> [#743](https://github.com/Raketa02/Raketa/issues/743), recorded by
> [ADR-0202](../../adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md).
> Home's ASKED FOR A LEVEL row ([§6.4](#64-asked-for-a-level--n-designed-no-mock)) was added on
> 2026-11-07 by PRD [#762](https://github.com/Raketa02/Raketa/issues/762) (Q129). The same day, PRD
> [#766](https://github.com/Raketa02/Raketa/issues/766) (Q130, [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md)) took Unblock off the
> record ([§2](#2-the-player-record--add-friend-beside-block-designed-no-mock)) and gave the request
> card a ranking line ([§6.2](#62-friend-requests--n-friends-5)). On 2026-11-14, PRD
> [#789](https://github.com/Raketa02/Raketa/issues/789) (Q131, [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)) let anyone be asked, with no
> daily limit, gave the request card three lines from Home's rows, and put a round friend button on
> Home's people cards ([the home rows screens §8](../home-rows/the-screens.md#8-the-round-friend-button-and-its-sheets)).
>
> **What it is:** how each Friends screen looks and behaves. The rules are in
> [the-mechanics.md](the-mechanics.md); where the two disagree on a rule, the mechanics win, and on a
> look, this document does. Every sentence is [the words §29](../matchmaking/the-words.md#29-friends)'s.
> A sentence quoted here only says where it stands; where a quote and §29 differ, §29 wins.
>
> **How to read the mocks:** they are under [`mocks/`](mocks/), cited as *friends 7*, and
> [the README](README.md) says which parts of each lead and lists every override. **Every name,
> number, price and date in a mock is mock data.** A screen no mock draws is marked **designed, no
> mock**: it is built from the mocks' own parts and the locked design system
> (`frontend_player/docs/design-system.md`), and any departure from the design system becomes a Part
> 16 row, as for the games and fill-in screens.

---

## Part A — The player app

### 1. Members (friends 1, 2)

**The rows keep today's design.** Only the right-hand end of each row is new:

| Relation | On the right | Tap |
| --- | --- | --- |
| None | **+ Add**, a black pill (friends 1) | sends a request; the row turns *request sent* at once |
| You asked | *request sent*, an amber tag (friends 2) | — |
| They asked you | **Accept**, a black pill (designed, no mock) | accepts; the row turns *friend* at once |
| Friend | *friend*, a green tag (friends 1) | — |
| You | nothing | — |

- **The pill acts; the rest of the row opens the record**, so nobody sends a request by accident.
- **The administrator's view** of an official group's Members has no pills or tags.
- **A blocked person's row** shows nothing on the right for the blocker: the record carries *Unblock*.
  For the blocked person, the blocker's row reads *request sent* once they ask, as any. *(Amended
  2026-11-07, Q130: neither can open the other's record, so Unblock is in You › Blocked players.)*

### 2. The player record — Add friend beside Block (designed, no mock)

The record's foot today holds **Block** alone. It becomes **one row of two buttons, side by side**,
in the record's empty bottom slot:

| Relation | Left button | Right button |
| --- | --- | --- |
| None | **Add friend** | **Block** |
| You asked | **Request sent ▾** → *Cancel request* | **Block** |
| They asked you | **Accept** (coral) | **Block** |
| Friend | **Friend ✓ ▾** → *Remove friend*, behind a confirmation | **Block** |
| You blocked them | — | **Unblock**, full width |
| Your own record | — | — |

The ▾ opens a small menu with the one action. *Remove friend* confirms first. Cancelling and removing
show nothing to the other person.

> **Amended 2026-11-07** ([ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8–§9, Q130). **The *You blocked them* row is retired**: a
> block closes the record both ways, so a blocked pair's record never opens, and Unblock lives in You ›
> Blocked players. **A stranger the reader may not ask** (no shared group, and not listed on General)
> shows **Block** alone: the record says whether *Add friend* may be offered. A record opened from the
> Rankings page sends its request from the ranking
> ([the rankings screens §6](../rankings/the-screens.md#6-the-record-from-the-ranking-designed-no-mock)).

> **Amended 2026-11-14** ([ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2, Q131). **Add friend shows on any record that opens**:
> a record refused by *Show me to new people*'s rule never opens, so the *Block alone* case is gone
> wherever the reader can read the record. There is no daily-limit sentence. A record opened from a
> Home row sends its request from that row, and shows **all of the subject's photos**.

### 3. The result screen — PLAYED WITH (designed, no mock)

A **PLAYED WITH** card **between the score and the sportsmanship card**: one row per other player of
the game, Members' row layout with Members' pills and tags (§1). **Hidden once every one of them is
your friend.** Shown after a For fun game too.

### 4. The Friends page

**One page, two modes.**

#### 4.1 From You — three tabs (designed, no mock)

- **You › Friends**, a new row, opens it. The header is friends 3's: back, *Friends*, **+ Add friends**
  top right.
- **Tabs**: **Friends · Asked you · You asked**, the design system's segmented control. *Asked you*
  carries a count while requests wait.
- **Friends**: sorted alphabetically; each row shows the sports they play with their levels
  (*Padel 2,75 · Tennis 3,10*). A tap opens the record.
- **Asked you**: rows with **Accept**, requests set aside included. A tap elsewhere opens the record.
- **You asked**: rows with **Cancel**. A tap elsewhere opens the record.
- **Each tab has a one-line empty state** (the words §29).

#### 4.2 From a group's Friends tab — the picker (friends 3, 6)

- Opened by **+ Friends** or any **+** on the court. **No tabs.**
- **Rows**: face, nickname, *2,75 · established* (the level and the standing in the group's sport), a
  circle; ticked when picked (friends 6). Sorted by level, highest first.
- **Full**: three picked in doubles, one in singles, and the remaining rows grey out (friends 6).
- **No level in this sport**: the row greyed, *No padel level yet*, and an **Ask Zofia to get a padel
  level** button under it; *Asked* once sent.
- **Done** at the foot, coral, returns to the Friends tab with the picks seated.
- **No friends**: the group's empty picker card (play 55), with **+ Add friends**.

### 5. The Add friends sheet (friends 4)

**+ Add friends** opens a bottom sheet, *Add friends*, with a close button:

- **From your groups**: a card listing each of your groups, monogram, name and *8 members · 2 to add*,
  and a chevron. *To add* counts members who aren't your friends, have no open request either way,
  aren't you, and aren't blocked by you. A tap opens that group's Members.
- **Not on Raketa yet?**: the link in a field, **Copy** (coral), and a small **New link** under it,
  which turns the old link off and shows the new one.

### 6. Home — the three new rows

**Home reads, top to bottom: FRIENDS GAME, FRIEND REQUESTS, ASKED FOR A LEVEL, Your games.** A row and
its title are there only while they hold a card. ASKED FOR A LEVEL is §6.4, after the sender's game,
so that §6.3 keeps its number.

#### 6.1 FRIENDS GAME · n (friends 12)

A horizontal row of invitation cards, each with a coral border:

- **Top**: *Tomek's game* · a clock and the time left (*1 h 35*), coral under an hour.
- **Faces**: the four, ✓ on those In, faded on those still to answer, *You* for the reader.
- **Line**: *Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive*.
- **Buttons**: **Not this time** (outline) / **Accept and pay 25 zł** (coral). Whole court: **Accept**,
  with *Tomek paid the court* above the buttons.
- **Accept** may open the bank's confirmation in the app, and the payment setup first if she has no
  method. A refusal for a full week or a game at that hour shows its sentence on the card.

#### 6.2 FRIEND REQUESTS · n (friends 5)

A horizontal row of request cards: the face, *Inés D. wants to be your friend*, *With you in Kazimierz
crew · Padel 3,40 ·* and the reliability chip, **Not now** (outline) / **Accept** (coral). A link's
request reads *Invited you to Raketa* in place of the group line. A tap on the face opens the record.
*(Since 2026-11-07, Q130:)* a request from the ranking reads ***Found you in the padel ranking*** in
place of the group line, even from a group-mate. *(Since 2026-11-14, Q131:)* a request found on
Home's rows reads its row's line in the same place — *Your level in padel · 91% even*, *Found you
among new players*, *6 things in common*, or their fallbacks
([the words §31.10](../matchmaking/the-words.md#3110-request-lines)).

#### 6.3 The sender's game, in Your games (designed, no mock)

The ordinary booked game's row, with a status line for its seats: *2 of 3 friends in · waiting for
Ania*, then *1 seat empty*, *Seat open*, or the ordinary *Booked* once all are In.

#### 6.4 ASKED FOR A LEVEL · n (designed, no mock)

Added 2026-11-07 (Q129). The rules are [the mechanics §5.1](the-mechanics.md#51-the-ask-waits-on-her-home-q129)'s.
**A horizontal row of cards, one per sport**, between FRIEND REQUESTS and Your games; *n* is the
number of sports. **It is a friend-request card** (friends 5) *(a call)*: faces, two lines, **Not now**
(outline) and the coral button. It is not the dark *Get your level* card.

- **One asker**: one face, *tomek.k wants to play padel with you* / *A few questions, and tomek.k can
  add you to a game.* · **Not now** / **Get your padel level**.
- **Two askers**: two faces, newest first, *tomek.k and kuba.w want to play padel with you* / *A few
  questions, and they can add you to a game.*
- **Three or more**: three faces, *tomek.k, kuba.w and 2 more want to play padel with you*, and the
  same line as two.
- **Carry on**: with a padel questionnaire left halfway, the line reads *You're on question 5.* and the
  coral button **Carry on**. The title doesn't change.
- **A tap on a face** opens that friend's record. **No group** is named anywhere on the card.
- **Get your padel level** and **Carry on** start the padel questionnaire from Home, as the *level
  asked* notice does, and its pass returns to Home. Once she finishes, the card is already gone on the
  way back, since Home and the bell are read again when a level is completed. A start that fails
  shows the notice's own toast where she is (*You have a padel level already.*).
- **Not now** takes the card away and shows a neutral toast, held long enough to read: *You can get
  your padel level any time, from You › Skill passport.* Home and the bell are read again.
- **For a player rated in no sport**, Home's dark *Get your level* card isn't drawn while this row
  has a card, and is drawn again once the row is empty and she is still rated in nothing.
- **Home's tab badge** doesn't count the row.

### 7. The group's Friends tab (friends 7–11)

#### 7.1 The court

- **The switch** above the court, **Competitive / For fun**, sets this game's kind only (friends 7).
- **The court** (friends 7): *THEIR SIDE* above the net, *YOUR SIDE* below, faces with *nickname level*
  labels, a × on each seated friend. Empty seats draw a **+**; **+ Friends** sits under the court.
- **Seating**: Done seats the picks in the evenest sides. **Tap one face, then another** to swap
  them. The × takes a friend off.
- **Unfilled**: *Seat 1 more friend* under the court, and no card.

#### 7.2 The card (friends 8, 9)

- **Loading** (designed, no mock): the card's frame with a quiet placeholder while it is built, the
  buttons hidden.
- **The card**: the deck's card without its tiles (friends 9): the *vs* line, the percentage and its
  word, the balance bar with your side on the left, the overlap grid with its grade, and the court
  panel (*Court available*, the share in volt, *Sat 10:00 · Ogrody 33 · Court 3*, the kind of court,
  and *Ogrody 33 is full at 10:00* on another club's court).
- **Buttons**: **Send game and pay 25 zł** (volt), **Pick a different court** (dark).
- **The court and the card always name the same sides** ([README](README.md#overrides), note 3).
- **Refused**: *These four can't all play together. Swap someone.* in the card's place; no buttons.
- **No court in 14 days**: the card's place says so, with **Pick a different court** gone.

#### 7.3 Find a court (friends 10, 11)

A bottom sheet, *Find a court*, over the Friends tab, with a close button:

- **Day headings**: *TOMORROW*, *SATURDAY*, *SAT 26 SEP*, as the mocks draw them.
- **Rows**: the hour in mono, *Bonarka Arena · Court 2*, the free line, *32 zł each*.
- **Tint**: four steps, brightest (friends 10's green) for all four free, then dimmer for three, two
  and one; the free line reads *Everybody free*, *Ania busy*, *Magda and Ania busy*.
- **Another club at the home club's full hour** reads *Ogrody 33 is full at 10:00* under its name.
- **Every row is pressable**; a press closes the sheet and the card rebuilds.

### 8. The send sheet (designed, no mock)

Opened by **Send game and pay 25 zł**. A bottom sheet that asks how to pay:

- **Two choice cards**, the design system's radio cards: **Split the cost** (first, chosen) and **Pay
  the whole court**.
- **Split**: *We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat
  still empty then.* directly above **Send game and pay 25 zł**.
- **Whole court**: **Send game and pay 100 zł**.
- **The button is the order**: its words name the payment, and the maximum sits right above it.
- **Sending** may open the bank's confirmation in the app, and the payment setup first if he has no
  method. `court_just_taken` closes the sheet and re-reads the card with its sentence. A third
  waiting game is refused with its sentence.
- **Sent**: the Friends tab returns to an empty court, and the game is in Your games.

### 9. The booked friends game's details (designed, no mock)

The ordinary booked game's details, with:

- **Each seat's state**: *In*, *waiting · 21 h left*, *can't make it*, *didn't answer*, *empty*,
  *Seat open*.
- **For the sender, on an empty seat, before the cut-off**: **Invite a friend** and **Open to
  Ogrody** (*Open to {group}*), the second behind a confirmation that a stranger can then take it.
- **For anyone In, on an empty seat**: **Invite a friend**, which opens the picker with one seat.
- **The sender's leave sheet, before the cut-off**: **Call it off for everyone** and **Leave · the
  others play on**, each with its line (the words §29). After the cut-off it is the ordinary late
  leave.
- **A friend's leave**: the ordinary leave sheet.
- **The pay mode** reads under the price: *Split* or *Tomek paid the court*.

### 10. Notices

Each new notice's landing is [the mechanics §12](the-mechanics.md#12-notifications)'s. Every one is in
the bell; answering on Home clears the request's or the invitation's row there. **A *level asked* row
is in the bell only while its card is on Home** (Q129): getting the level, by the card or any other
route, or **Not now**, clears it from the list and from the bell's number, so a tap on it never ends
in *You have a padel level already.*

---

## Part B — The public site

### 11. The friend link's page, `/f/<code>` (designed, no mock)

Built like the group page: server-rendered from the public read, the public site's own look (paper,
the coral wordmark, a white card), phone first.

- **The card**: Tomek's face, *Tomek invited you to play on Raketa*, the store buttons, and **Open in
  Raketa**.
- **The Android store button carries the link as the install referrer**, on this page and on the
  group page.
- **A preview image** for the chat the link is pasted into.
- **A replaced or unknown code**: *Nothing at that link*.
- **The app-link files** gain `/f/`.

---

## Part C — The club website

### 12. Raketa settings and Groups

- **Raketa settings**: **Other clubs' courts for our groups** reads **on** by default (10 km). The help
  line under it says *at an hour your courts are full*.
- **Groups**: the line above the table that links to the setting says the same.

The games and fill-in screens' [B5](../games-and-fill-in/the-screens.md#b5-raketa-settings) and
[B8](../games-and-fill-in/the-screens.md#b8-groups-changed) carry it. Bookings shows a friends game as
any booking.

---

## Part D — The backend, inferred

The proposed shapes; the tickets settle them.

| Where | What |
| --- | --- |
| **Friends** (new context, event-sourced) | **Friendship**, one stream per pair: requested (and where), set aside, cancelled, crossed, friends made (accepted or crossed), ended (removed or blocked). **Friend link**, one stream per player: code made, code replaced. **Ask for a level**, refused when already asked for that sport, answered by the rating context's first level in it, and **set aside** by the friend asked (an event per ask the Home card names, [#764](https://github.com/Raketa02/Raketa/issues/764)). A subscription to blocks. The reader's relations lent through a demand port ([#745](https://github.com/Raketa02/Raketa/issues/745), [#748](https://github.com/Raketa02/Raketa/issues/748), [#749](https://github.com/Raketa02/Raketa/issues/749)) |
| **Clubs / the court source** | Answers per hour; the setting defaults to on, existing clubs read on ([#746](https://github.com/Raketa02/Raketa/issues/746)) |
| **Proposals** | The friends card and the court list, reads only; Home's three rows ([#750](https://github.com/Raketa02/Raketa/issues/750), [#751](https://github.com/Raketa02/Raketa/issues/751), [#764](https://github.com/Raketa02/Raketa/issues/764)) |
| **Bookings** | The birth *booked by a friend*, invited seats and their 24-hour job, the sender's choices, the covered booking's cut-off ([#751](https://github.com/Raketa02/Raketa/issues/751), [#752](https://github.com/Raketa02/Raketa/issues/752)) |
| **Payments** | The Cover: a seat charge whose payer is the sender; the amount agreed recorded with the terms acceptance |
| **Notifications** | The new kinds of [the mechanics §12](the-mechanics.md#12-notifications), all always on; a *level asked* row listed only while its card is on Home ([#764](https://github.com/Raketa02/Raketa/issues/764)) |
| **Player routes** | send (admitted to a group-mate, or to anybody listed on General and not hidden, at most 10 a Warsaw day to people outside your groups, `daily_request_limit` — Q130, [#773](https://github.com/Raketa02/Raketa/issues/773); since 2026-11-14 to anybody, with no limit, except across *Show me to new people*'s rule — Q131, [#791](https://github.com/Raketa02/Raketa/issues/791)), accept, set aside and cancel a request; remove a friend; list friends by sport; list requests by direction; read and replace the link; open a code; ask for a level; set aside a sport's level asks; the friends card and the court list; send, accept, decline, invite, open a seat, call off, leave |
| **Public route** | read a code: the owner's nickname and face, or `friend_link_not_found` |
| **Jobs** | the 24-hour run-out; the cover warning; the cut-off's cover |
| **Seed and the games test console** | friendships, open requests both ways, a set-aside request, a link, a Split and a Whole-court friends game, a seat waiting on an answer, a level ask waiting on the protagonist's Home; console actions to send, accept, decline, invite and open a seat as seed accounts |
