# Friends — the mechanics

> **Status:** agreed in the friends grilling on 2026-11-05/06 (Q1–Q46 there), confirmed by the
> product owner on 2026-11-06, and specified as PRD [#743](https://github.com/Raketa02/Raketa/issues/743).
> Logged as **Q128** in the
> [games and fill-in decision log](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log), and
> recorded by [ADR-0202](../../adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md).
> **Refined on 2026-11-07** by the level-ask grilling, PRD [#762](https://github.com/Raketa02/Raketa/issues/762),
> logged as **Q129** and recorded by ADR-0202 §4's amendment: an ask waits on the friend's Home
> ([§5.1](#51-the-ask-waits-on-her-home-q129)), and its bell row with it ([§12](#12-notifications)).
> **Amended on 2026-11-07** by the rankings grilling, PRD [#766](https://github.com/Raketa02/Raketa/issues/766),
> logged as **Q130** and recorded by [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md): a request may also go to anybody listed on
> General ([§3.1](#31-who-can-be-a-friend)), reads *Found you in the padel ranking*
> ([§3.2](#32-asking)), and is capped at 10 a day to people outside your groups
> ([§13](#13-numbers-in-one-place)); a block closes the record both ways, so the record's Unblock goes
> ([§3.5](#35-blocks)).
>
> **Its companion** is [the-screens.md](the-screens.md), which says how each screen looks. Every
> sentence a player reads is in [the words §29](../matchmaking/the-words.md#29-friends). Where this
> document and the brief ([friends_feature.md](friends_feature.md)) disagree, this document wins.
>
> **What a friends game shares with every game** — the club's cut-off as the one deadline, holding
> and taking a share, the card check and the holding time, rescues, leaving after the cut-off, the
> record and the result — is the [games and fill-in mechanics](../games-and-fill-in/the-mechanics.md)'
> (§10, §12–§15), cited here and never restated. Only what is different is written here.
>
> **Calls marked *(a call)*** were made while specifying and writing PRD #743. Calls 1–6 were agreed
> by the product owner before it was published; calls 7–11 are open for the product owner to
> overrule ([§14](#14-calls-made-without-a-ruling)). The marks in [§5.1](#51-the-ask-waits-on-her-home-q129)
> are PRD #762's calls instead, listed in the decision log's Q129.

---

## 1. The whole thing in one page

**Tomek** plays padel at 2,71. He is in **Ogrody open play**, the official group of the club
**Ogrody 33**, where **Ewa** and **Magda** play, and in **Kazimierz crew**, a group players made,
where **Ania** and **Inés** play. **Zofia** plays with him every week and isn't on Raketa.

1. **Inés asks Tomek** from Kazimierz crew's Members. Her request is a card on his Home. He taps
   **Not now**: the card goes, the request stays open, and Inés still reads *request sent*. On
   Thursday he accepts from her record, and she is told *"Tomek said yes — you're friends"*.
2. **Tomek sends Zofia his link** on WhatsApp. She installs Raketa, signs up, and lands on Home with
   *"Tomek wants to be your friend · Invited you to Raketa"*. She accepts. She has no padel level, so
   on Tomek's picker she is greyed; he asks her to get one, and she does.
3. **On Monday at 19:00**, on Ogrody's **Friends** tab, Tomek picks **Competitive**, seats Ewa, Magda
   and Ania (Ania isn't in Ogrody: she plays as a **guest**), and taps **Done**. Raketa seats them in
   the evenest sides and builds the card: *YOU + EWA VS MAGDA + ANIA · 87% · Very even*, and
   **Saturday 10:00 · Ogrody 33 · Court 3 · 25 zł each**. The club's cut-off is **Friday 10:00**.
4. **He taps Send game and pay 25 zł**, chooses **Split the cost**, and confirms. His card holds
   **100 zł**: his 25 zł, and 25 zł for each of the other three seats. **The court is booked at
   once.** Ewa, Magda and Ania each get the invitation, and 24 hours to answer.
5. **Ewa and Magda accept**, each holding her own 25 zł. **Ania doesn't answer** by Tuesday 19:00, so
   Tomek is told *"Ania didn't answer"*. He leaves the seat for now.
6. **On Thursday at 10:00**, 24 hours before the cut-off, Tomek is warned: *"Saturday 10:00 · 1 seat
   still empty. At Fri 10:00 you pay 50 zł: your 25 zł and Ania's seat."*
7. **At Friday 10:00**, Tomek's 25 zł, Ewa's, Magda's and the cover for the empty seat are taken; the
   covers for Ewa's and Magda's seats are let go. The game is **not** called off: the empty seat
   opens to Ogrody as a rescue. **Kuba** takes it on Friday afternoon, pays 25 zł, and Tomek gets his
   25 zł back, less the fee kept on it.
8. **Saturday 10:00**, Ogrody 33 is full, so when Tomek builds another game for that hour, **Wisła
   Park**, 4 km away, is offered too, marked *Ogrody 33 is full at 10:00*. At Tuesday 21:00, where
   Ogrody 33 has a free court, only Ogrody 33 is offered.

---

## 2. Words used in this document

The terms are the root [`CONTEXT.md`](../../../CONTEXT.md)'s: **Friend**, **Friend request** (*set
aside*, *crossed*), **Friend link**, **Ask for a level** (Friends); **Friends game**, **Invited seat**,
**Guest**, **Pay mode** (*Split the cost* · *Whole court*), the **sender** and an **empty seat**
(Bookings); **Cover** (Payments); **Friends card** (Proposals). Here *Split* is short for *Split the
cost*, never a forecast's **Split**.

---

## 3. Becoming friends

### 3.1 Who can be a friend

- **A friend is someone from your groups whom you asked and who said yes**, or who opened your link
  and said yes ([§4](#4-the-friend-link)). Nobody outside your groups can be asked except through
  the link; there is no search for any player.

  > **Amended 2026-11-07** ([ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §9, Q130). **A request may go to anybody in your groups, or
  > anyone listed on General** in at least one sport and not hidden from it
  > ([the rankings mechanics §13](../rankings/the-mechanics.md#13-friend-requests)), and to anybody
  > through the link. **At most 10 a day** may go to people you share no group with; requests to
  > group-mates are never counted. There is still no search for a player by name.
- **Friendships are per pair, across all your groups.** One friendship between Tomek and Ania holds
  in Ogrody, in Kazimierz crew, and in any group either joins later.
- **A friendship survives either of them leaving a group**, and ends when either account is deleted.
- **No limit** on the number of friends.

### 3.2 Asking

A **friend request** is made from:

- **Members**: the **+ Add** pill on anybody who isn't your friend;
- **the player record**, which opens from any face: **Add friend**;
- **the result screen**: the **PLAYED WITH** card's pills;
- **a link** ([§4](#4-the-friend-link));
- **the ranking** *(since 2026-11-07, Q130)*: **Add friend** on a record opened from the Rankings
  page.

The request records **where it was made**: the group (Members, or a face on a game of that group),
the record, the result, or the link. The card on the other person's Home names **the group** where
the + Add was pressed, or the group of the game it was pressed from, and its sport. A request made by
link reads *Invited you to Raketa*. *(Since 2026-11-07, Q130:)* a request made from the ranking
records the ranking and its sport, and reads ***Found you in the padel ranking***, even to a
group-mate.

- **You can't ask yourself.**
- **You can't ask while a request of yours to that person is open**, set aside or not. Nobody can
  nag.

### 3.3 Answering

- **Accept** makes you friends. The requester is told *"Kuba said yes — you're friends"*, and the tag
  turns to *friend* everywhere at once.
- **Not now is not no** (Q1). The card leaves your Home, and the request **stays open**. The
  requester keeps reading *request sent*, is never told, and can't ask a second time. You can still
  accept later, from their Members row, their record, or You › Friends › *Asked you*.
- **Crossed requests make friends at once** (Q2). When two people ask each other before either
  answers, nobody has to accept. Both are told *you're friends*.
- **A request never expires.**

### 3.4 Cancelling and removing

- **Cancel**: the requester cancels a request from the person's record (**Request sent ▾ › Cancel
  request**) or from You › Friends › *You asked*. It leaves the other person's Home and bell.
- **Remove**: either friend removes the other from the record (**Friend ✓ ▾ › Remove friend**), behind
  a confirmation.
- **Neither is told** (Q3). **Removing a friend never touches a game** already sent or booked.

### 3.5 Blocks

A block ([ADR-0193](../../adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md))
reaches friendship too (Q5):

- **A block ends a friendship.** When Tomek blocks Michał, or Michał blocks Tomek, their friendship
  and any open request between them end, silently.
- **A request from a player the reader blocked is never shown to the reader.** Michał, whom Tomek
  blocked, can tap Add friend again; he reads *request sent* forever, and Tomek never sees it. The
  block stays undetectable: *request sent* forever is exactly what a request set aside reads.
  *(Since 2026-11-07 the request still is, but a refused record can be a tell between group-mates,
  a cost ADR-0203 names.)*
- **Somebody you blocked** shows only **Unblock** on their record; you are never offered to befriend
  them. *(Amended 2026-11-07, [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8, Q130: **a block closes the record both ways**,
  everywhere, group-mates included, so neither opens the other's record and the record has no
  Unblock. **Unblock lives in You › Blocked players.**)*
- **Unblocking brings nothing back**: no friendship, and no request.
- **A third person seating a blocked pair** in a friends game is refused with *"These four can't all
  play together. Swap someone."*, which never says which pair ([§7.5](#75-what-the-card-refuses)).

### 3.6 The *friend* tag

- **The tag is on every face**: deck tiles, game details, booked games, Fill in, the result card,
  Members and the record (Q68's FRIEND tag now applies).
- **Only for your own friends** (Q12). Kuba never learns that Tomek and Magda are friends. Every
  response carries only its reader's relations.

### 3.7 Where a player sees it

| Where | What |
| --- | --- |
| **Members** | **+ Add** (black) on anybody not your friend; *request sent* (amber); *friend* (green); **Accept** (black) on somebody who asked you. The pill acts; the rest of the row opens the record. Not on the administrator's view of an official group's Members |
| **The record** | **Add friend** and **Block** side by side at its foot. The left button: **Request sent ▾**, **Accept** (coral) or **Friend ✓ ▾**. ~~Only **Unblock**, full width, on somebody you blocked.~~ *(Since 2026-11-07, Q130: a blocked pair's record never opens; Unblock is in You › Blocked players. **Add friend** shows only when the record says a request may be sent, and **Block** stands alone otherwise.)* Neither on your own record |
| **The result screen** | **PLAYED WITH**, between the score and the sportsmanship card: the other players with Members' pills. Hidden once they are all your friends. Shown after a For fun game too |
| **Home** | **FRIEND REQUESTS · n**, under the friends game invitations and above Your games. The row and its title are gone once every request is answered |
| **You › Friends** | Tabs **Friends · Asked you · You asked**, a count on *Asked you* while requests wait, **Accept** and **Cancel** on the rows, **+ Add friends** top right |

---

## 4. The friend link

### 4.1 The code

- **Each player has one link**: `<public site>/f/<code>`, the code **random**, shaped like a group's
  code (letters and digits), so nobody can guess someone's link from their nickname (Q9).
- **It is made the first time its owner reads it**, and **never reused**.
- **New link** replaces it at once. The old code then reads as not found, on the web and in the app.

### 4.2 Opening it

**Opening it never makes friends by itself** (Q37). As a signed-in player, it puts the owner's
**friend request** on the opener's Home, *"Tomek wants to be your friend · Invited you to Raketa"*,
with **Accept** and **Not now**, like any request. This is the same for a new player like Zofia and for
Ania, who already has the app. Unless:

| When | What happens |
| --- | --- |
| The opener is the owner | Nothing |
| They are already friends | Nothing |
| The opener already asked the owner | The requests cross: they are friends at once ([§3.3](#33-answering)) |
| The owner blocked the opener | The request is swallowed, as in [§3.5](#35-blocks) |
| The code was replaced, or never existed | `friend_link_not_found`: *Nothing at that link* |

### 4.3 How it travels (Q38)

In production the link is a deep link, exactly like a group's `join/` link: a universal link on
iPhone and an app link on Android, through the public site's app-link files, which gain `/f/`.

- **App installed, signed in**: Raketa opens, and the request is at the top of Home.
- **App installed, signed out or no account**: Raketa opens on sign-up. The link waits through
  sign-up and onboarding, as a group link does, then lands on Home with the request.
- **App not installed**: the link opens the public site's page, *"Tomek invited you to play on
  Raketa"*, with his face, the store buttons, **Open in Raketa**, and a preview image for the chat it
  is pasted into.
  - **On iPhone**, the install forgets the link, so she taps **Open in Raketa** once more.
  - **On Android**, the store button carries the link through the install as the **install
    referrer**, which the app reads **once, on first launch**. This holds **for group links too**: the
    group page's Android store button carries its link the same way. Android keeps a referrer for 90
    days.

---

## 5. Asking a friend to get a level

- **A friend with no level in the picker's sport** is greyed, with *No padel level yet* and an **Ask
  Zofia to get a padel level** button (Q7, Q45).
- **The ask** sends her a notice, push and bell: *"Tomek wants to play padel with you. Get your padel
  level so Tomek can add you."* It opens the padel questionnaire.
- **When her first padel level arrives**, Tomek is told *"Zofia has a padel level — you can seat
  Zofia now."*
- **No sentence says *her* or *him* about another player**: a gender never crosses to another player
  (ADR-0096), so PRD #743's *her padel level*, *so he can add you* and *seat her now* are written
  without one.
- **Once per friend per sport.** After asking, the button reads *Asked*, and a second ask is refused.

### 5.1 The ask waits on her Home (Q129)

> Added 2026-11-07 from the level-ask grilling (Q1–Q8 there), PRD
> [#762](https://github.com/Raketa02/Raketa/issues/762), and ADR-0202 §4's amendment of that day. The push
> alone left an ask nowhere to be found: without push permission, or on a simulator, nothing arrives,
> and the bell's row is history once the list is opened. Built by the backend's
> [#764](https://github.com/Raketa02/Raketa/issues/764) and the player app's
> [#765](https://github.com/Raketa02/Raketa/issues/765).

- **An ask waiting on Zofia is a card on her Home**, in an **ASKED FOR A LEVEL · n** row after FRIEND
  REQUESTS and before Your games, until she has the level or says **Not now**. *n* is the number of
  sports with a card.
- **One card per sport**, naming every friend whose ask in it is waiting and not set aside: *tomek.k wants to play padel
  with you* / *A few questions, and tomek.k can add you to a game.* Two askers are *tomek.k and kuba.w*
  and *they*; three or more name two and count the rest. **The sport with the newest ask comes first,
  and its askers newest first**, with up to three faces *(a call)*. A face opens that friend's record.
  **The card names no group**, as the notice doesn't *(a call)*.
- **Get your padel level does what the notice does**: it starts the padel questionnaire from Home, and
  the pass returns to Home. With a padel questionnaire left halfway, the button reads **Carry on** and
  the line *You're on question 5.*
- **Not now sets aside the asks the card names at that moment** *(a call)*. The card is gone on every
  phone, its row leaves the bell, and **nobody is told**. A toast says *You can get your padel level any
  time, from You › Skill passport.*, where the *Rate Padel* chip is. **The card comes back only when a
  new friend asks her for padel**, and then names only the askers she hasn't set aside. A Not now on a
  card that has just gone does nothing visible *(a call)*.
- **A set-aside ask is still waiting.** Whenever she gets her padel level, every friend who asked is
  told *level got*, whether she set the ask aside or not.
- **The card ends by itself** when:
  - **she holds any level in the sport**, by any route (this card, a group's card, the passport), read
    live, so the card is gone before *level got* is delivered *(a call)*;
  - **no asker is still her friend**. A removal or a block ends the friendship and takes that friend
    off the card. **Her own block of an asker takes them off at once**, as a friend request from
    somebody she blocked is hidden at once; an asker's block of her, once its delivery has run *(a
    call)*. The card goes with the last asker.
- **It never expires.**
- **The bell follows the card.** A *level asked* row is listed in the bell, and counted in its number,
  only while its card is on Home ([§12](#12-notifications)). The row is matched to the card by asker and
  sport, which is unique, because an ask is once per friend per sport, ever *(a call)*.
- **A player rated in no sport** sees the ask card **instead of** Home's *Get your level* while it is
  drawn: the ask's row is drawn, and *Get your level* draws nothing. If she sets the ask aside and is still rated in nothing, *Get your level* comes back. Answering
  the ask's questionnaire gives her a rating, which removes both.
- **Unchanged:** an asker asks once per sport, ever, and the picker keeps reading *Asked*; the push, its
  words, and where tapping it opens (the questionnaire); *level got* to every asker; and Home's tab
  badge, which counts this row no more than it counts friend requests or invitations.

---

## 6. Official groups' courts, hour by hour

**This is the rule for every game in a group, not only for friends** (Q21). It replaces the games
and fill-in mechanics' [§4.3](../games-and-fill-in/the-mechanics.md#43-courts) official-group
bullet, and its Q29.

- **Official group**, at each hour:
  - where the **home club has a free court**, only the home club is offered;
  - where it has **none**, other Raketa clubs **within the club's distance** (10 km by default) are
    offered too, **listed after the home club** and marked ***Ogrody 33 is full at 10:00***.
- **The club's switch**, *"Offer our groups other clubs' courts when ours are full"*, is kept, and is
  now **on by default**, for existing clubs too *(call 3)*. Switched off, the group plays only at its
  club, as before.
- **Player group**: unchanged. Its home club first, then other clubs within 10 km.
- **One rule for every way a game is made**: the Games deck (its picks and the owed card), Post a
  game's grid and slot sheet, and the friends card with *Find a court*. A group never has two court
  rules.

**Why hour by hour, not a fill threshold.** At 70% booked, Saturday 10:00 at Ogrody 33 may still be
free, and a threshold would offer Wisła Park beside it, sending the club's own players away from an
hour it could sell. At 30% booked, the one hour four friends share may already be gone, and they
would get nothing. Raketa has no measure of a club's fullness today. Hour by hour, the club never
loses an hour it could have sold, and players are never left without a game at an hour it can't
serve.

---

## 7. Building a game with friends

### 7.1 The Friends tab

A group's **Friends** tab draws a court with you in one seat, as today, with a **+** on each empty
seat and **+ Friends** under it.

- **Above the court**, **Competitive** or **For fun**, for **this game only**. It never changes your
  Play intent. Competitive counts for the score; For fun doesn't.
- **Intent never excludes** (Q15). A friend whose intent is For fun only can be seated in a
  Competitive game; the invitation names the kind, and she decides.
- **Any friend can be seated** (Q14), from this group or any other. A friend who isn't a member plays
  as a **guest**: she sees the game on Home, in its chat and on its result, and never the group's deck
  or Fill in. The game belongs to the group.

### 7.2 The picker

- **+ Friends**, or a **+** on the court, opens the Friends page as a **picker** (mocks 3 and 6): no
  tabs, each friend's level and standing in the group's sport (*2,75 · established*) with a circle,
  and **Done** at the foot.
- **Sorted by level in this sport, highest first** *(call 4)*.
- **When the seats are full** — **three** friends in doubles, **one** in singles — the remaining rows
  grey out.
- **A friend with no level in this sport** is greyed with *No padel level yet* and the ask of
  [§5](#5-asking-a-friend-to-get-a-level).
- **No friends yet**: the picker's empty card (play 55) and **+ Add friends**.

### 7.3 Seating

- **On Done**, Raketa seats the picks into the **evenest sides** (Q10).
- **Swap** two people by tapping one face and then the other. **A face's ×** takes them off.
- **Until every seat is filled**, the court reads *Seat 1 more friend* (*Seat 2 more friends*, …), and
  there is **no card** (Q16).

### 7.4 The card

**The moment every seat is filled**, Raketa builds the **friends card** under the court, with a
loading state while it works. It is the deck's card **without the player tiles**:

- the sides, *YOU + EWA VS MAGDA + ANIA*, and the balance, *87% · Very even*, for the sides on the
  court;
- the **overlap grid** of the four's weeks, graded *High / Good / Slim overlap*;
- the **court panel**: *Court available · Sat 10:00 · Ogrody 33 · Court 3 · 25 zł each*, with the kind
  of court, and *Ogrody 33 is full at 10:00* on another club's court;
- **Send game and pay 25 zł** and **Pick a different court**.

**The proposed court** is the soonest hour **that can still be sold** (its book-by ahead), up to **14
days** ahead, where:

- **all four are free** for the whole hour (their weekly hours);
- **a court is free** under the group's court rule ([§6](#6-official-groups-courts-hour-by-hour));
- **none of the four already has a game** at that hour *(call 5)*.

Failing that, it is the soonest such hour where **most of them** are free. Failing that, the card says
there is no court in the next 14 days.

**A swap or a new court** rebuilds the card at once: what is sent is what was seen.

### 7.5 What the card refuses

| Refusal | When | What the player reads |
| --- | --- | --- |
| `cannot_play_together` | Two of the four blocked each other, either way round | *"These four can't all play together. Swap someone."* — never which pair (Q6) |
| `no_level` | A seated player has no level in the sport | The picker greys them first; a stale seat reads the picker's line |
| `not_a_friend` | A seated player is no longer the sender's friend | The seat is emptied |

**What doesn't apply** *(call 10)*: the level window, the kind's tolerance and gender preferences,
because friends choose each other. **What does**: blocks, a level in the sport, one game per hour and
the weekly limit.

### 7.6 Find a court

**Pick a different court** opens *Find a court* (mocks 10–11), a sheet over the Friends tab:

- **Every bookable club, hour and court** from the soonest sellable hour to **14 days** ahead, under the
  group's court rule, **grouped by day** (*TOMORROW*, *SATURDAY*, *SAT 26 SEP*).
- **Each row**: *19:00 · Bonarka Arena · Court 2 · 32 zł each*.
- **Tinted by how many of the four are free** then (Q36): brightest for all four, dimmer for three,
  two, one; labelled *Everybody free*, *Ania busy*, *Magda and Ania busy*. *Busy* means outside that
  player's weekly hours.
- **An hour where one of them already has a game is left out.**
- **Every row can be picked**, even one where a friend is usually busy: friends who arrange things
  themselves aren't stopped. Picking one updates the card.

---

## 8. Sending, and paying

### 8.1 The send sheet

**Send game and pay 25 zł** on the card opens a **send sheet** *(call 8)*, so the maximum is on screen
when the binding button is pressed. It asks how to pay (Q28, Q29):

| | **Split the cost** (first, chosen) | **Pay the whole court** |
| --- | --- | --- |
| Above the button | *"We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat still empty then."* | — |
| The button | **Send game and pay 25 zł** | **Send game and pay 100 zł** |
| Held on the sender's card at send | his 25 zł + a 25 zł **cover** for each other seat = **100 zł** | the same: **100 zł** |
| What a friend's **Accept** does | holds her own 25 zł until the cut-off | holds nothing |
| The friend's button | **Accept and pay 25 zł** | **Accept**, with *"Tomek paid the court"* |

The numbers are the court's price and the share: 100 zł and 25 zł in padel; in a singles sport the
court's price is split two ways, and the sender covers **one** seat.

### 8.2 Booked at send

**The court is booked the moment the sender sends** (Q28). The club has sold it, and no deck card
can take it.

- **The friends game is a booking born at send**: the sender **In**, an **invited seat** for each
  friend, the kind, the pay mode, the court and its number, the sides, the cut-off as the club set
  it, and the group's pool.
- **The chat opens at send.** Each friend joins it on accepting.
- **A court somebody took a second earlier** refuses the send with `court_just_taken`; the card is
  re-read.
- **Sending withdraws the sender's other yeses at that hour**, and accepting withdraws the friend's,
  as a fill does.
- **The money is authorised with the sender present** *(call 2)*: his share and the three covers
  together, all or nothing. If his bank wants to confirm, he confirms in the app; a refused card books
  nothing.
- **A far-off game** is held as any seat is: a card check at send, and the holds placed at the
  holding time, four days before the cut-off
  ([games and fill-in §12.2](../games-and-fill-in/the-mechanics.md#122-when-a-game-fills)).
- **The amount he agreed to** is recorded with his terms acceptance.

### 8.3 The cover

**A cover is the sender's hold for a seat that isn't his.** With Split, his card covers every other
seat until the cut-off; with Whole court, it pays every seat.

- **Every cover stays held until the cut-off** *(call 7)*. At the cut-off it is **taken only for a seat
  without its own payment**, and **let go** otherwise. Covers are never let go and held again in
  between: if Ewa accepted and later left, the seat would need a new hold on Tomek's card without him
  there, which his bank could refuse or ask him to confirm.
- **One hold per seat**, using today's hold, take and let-go steps *(call 1)*; nothing is captured in
  part.
- **While the sender covers the game** — Split with him In, or Whole court — **it is never called off
  at its cut-off** for an empty seat ([§10.3](#103-at-the-cut-off)).
- **This is the one place a player pays for another player's seat**, and only because he agreed to the
  maximum before pressing. The games and fill-in mechanics'
  [§12.1](../games-and-fill-in/the-mechanics.md#121-the-model) carries the exception.
- **Nobody takes the cover over** from the sender (Q46).

### 8.4 Limits

- **At most 2 friends games waiting for answers** per sender (Q34). A third send is refused.
- **Each friends game counts as one of each player's games that week**, sender and friends alike.
- **A friend's Accept is refused** when her week is full or she already has a game at that hour,
  with a sentence saying why *(call 5)*.
- **A sent game's court and hour never change** (Q19). To change them, the sender calls it off and
  sends a new one.

---

## 9. The invitation

- **Each friend gets** a push, a bell notice, and a card in the **FRIENDS GAME · n** row at the very
  top of Home (mock 12): *"Tomek's game"*, a clock with the time left, the four faces (✓ on those In,
  faded on those still to answer), *"Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive"*, and
  **Not this time** / **Accept and pay 25 zł** (Whole court: **Accept**, and *"Tomek paid the court"*).
- **24 hours to answer** (Q30), **never past the cut-off**. An invitation made after the cut-off, into
  a rescue seat, runs 24 hours **never past the game's start** *(call 9)*. **Not answering counts as
  Not this time.**
- **Accept** (Split) holds her 25 zł until the cut-off, like any Raketa seat, with her present: a bank
  confirmation happens in the app. The card moves to her **Your games**.
- **Not this time** takes the card off her Home.
- **Answering on Home clears the invitation from the bell.**
- **When the last seat is taken**, all four get the usual *It's a game!*.

**The sender's game** sits under **Your games** from the moment he sends it, reading *2 of 3 friends
in · waiting for Ania* (Q35), and the Friends tab goes back to an empty court. **Home reads, top to
bottom**: FRIENDS GAME, FRIEND REQUESTS, ASKED FOR A LEVEL, Your games (Q13, Q129), each row hidden
while empty.

---

## 10. A seat goes empty

### 10.1 Before the cut-off

When a friend says *Not this time*, or her 24 hours run out, the sender is told *"Ania can't make
it"* or *"Ania didn't answer"*, with two choices (Q31):

- **Invite a friend**: another friend gets the same kind of invitation, with its own 24 hours.
- **Open to Ogrody**: the seat becomes a **rescue**, like a booked game that lost a player: a *Seat
  open* card in the decks of members who fit, a row in Fill in's *Seats to fill*, and Fill in alerts
  (Q23). The first to take it pays 25 zł. **A guest is never offered a rescue.**

**Nothing happens automatically before the cut-off.**

- **Anyone still in the game** may invite one of their own friends into an empty seat (Q44).
  **Whoever accepts and pays first gets it**, friend or rescuer, and every other invitation into that
  seat ends with *seat taken* (a notice [#752](https://github.com/Raketa02/Raketa/issues/752) adds;
  the PRD's list doesn't name it).
- **Opening a seat to the group stays the sender's call** before the cut-off, because until then the
  seat costs him money.
- **A seat opened to the group** is offered as any rescue is: to members who fit, are free and aren't
  blocked. A rescuer's held share means the cover for that seat is let go at the cut-off.

### 10.2 The cover warning (Split only)

**24 hours before the cut-off** (Thursday 10:00 for a Friday 10:00 cut-off), if a seat still lacks its
own payment and the sender chose **Split**, he gets one polite warning, push and bell (Q42):

> *"Saturday 10:00 · 1 seat still empty. At Fri 10:00 you pay 50 zł: your 25 zł and Ania's seat."*

with **Invite a friend**, **Open to Ogrody** and **Call it off**. **Once per game.** If a seat empties
inside those 24 hours, the notice that tells him carries the same line. With Whole court there is no
warning: he already pays every seat.

### 10.3 At the cut-off

**At Friday 10:00**, in a covered game:

- each seat's own held share is **taken**;
- a cover is **taken** for each seat without its own payment, and **let go** for every other;
- **the game is not called off.** Each seat still empty **opens to the group automatically** as a
  rescue;
- **whoever takes it later** pays 25 zł, and the sender gets **his 25 zł back, less the fee kept on
  it**, as with any late leaver
  ([games and fill-in §12.3](../games-and-fill-in/the-mechanics.md#123-leaving-before-and-after-the-cut-off)).
  A seat nobody takes stays empty, and its cover stays paid.

**After the cut-off**, anyone still in may invite one of their friends into an empty seat, and the
first to accept and pay, or the first rescuer, takes it. Money moves at once, as after any cut-off.

---

## 11. Leaving

### 11.1 A friend who accepted

**She can leave free until the cut-off** (Q32), like any Raketa game: her hold is let go, her seat
goes empty as in [§10](#10-a-seat-goes-empty), and the sender is told. After the cut-off she is a late
leaver ([§11.3](#113-after-the-cut-off)).

### 11.2 The sender, before the cut-off

His leave sheet offers two choices (Q19, Q43):

- **Call it off for everyone**: everyone is told, **every hold is let go**, nobody pays, and the court
  goes back to the club. Free until the cut-off.
- **Leave · the others play on**:
  - **With Split**, his share and every cover are let go, and **he stops covering**: from then on it
    is an **ordinary Raketa game**. His seat, and any seat no friend has taken, become rescues at
    once. A seat still empty at the cut-off **calls the game off**, with nobody paying, as any game
    short at its cut-off.
  - **With Whole court**, he **still pays the court**. His covers stay, his own seat becomes a rescue
    that his own share still pays for, and **whoever takes it pays 25 zł back to him**.
  - **Nobody else ever pays his share**, and nobody takes over his cover (Q46).

### 11.3 After the cut-off

**Anyone who leaves, the sender included, is a late leaver** (Q33, Q44): the seat becomes a rescue at
once (deck and Fill in), anyone still in may invite a friend into it, and the first to accept and pay
takes it. The leaver's share comes back when somebody takes the seat, less the fee kept, as for any
late leaver.

### 11.4 A club's cancel

**A club's cancel moves a friends game as it moves any booked game**
([games and fill-in §16.9](../games-and-fill-in/the-mechanics.md#169-cancelling-a-booking)), and calls it
off when no court absorbs it, with the same refunds. The club sees an ordinary booking.

---

## 12. Notifications

**Every new kind is always on, pushed and kept in the bell** (Q24). None is emailed unless it is about
money, as the games and fill-in mechanics'
[§17.2](../games-and-fill-in/the-mechanics.md#172-notifications) already decides for the money ones.
The sentences are [the words §29](../matchmaking/the-words.md#29-friends)'s.

| Notice | To | Opens |
| --- | --- | --- |
| **Friend request** — once per request, never again for it | the person asked | Home |
| **You're friends** — *Kuba said yes — you're friends* | the requester; both, for a crossed request | the friend's record |
| **Friends game invitation** | each invited friend | Home, on the invitation |
| **Seat invitation** — into an empty seat | the friend invited | Home, on the invitation |
| ***Can't make it*** / ***didn't answer*** | the sender | the game, where the seat reads empty |
| ***Seat taken*** | an invitee whose seat somebody else took first | the game |
| ***Someone left your game*** — an accepted friend leaving; inside the last 24 hours, with the cover line | the sender and those In | the game |
| **Friends game called off** — *nobody paid* | everyone In and every invitee still waiting | the game |
| **The cover warning** — Split, 24 hours before the cut-off | the sender | the game, with its three actions |
| **Level asked** — a friend's ask, not the once-per-account *Get your level*. Listed in the bell, and counted in its number, **only while its card is on Home** ([§5.1](#51-the-ask-waits-on-her-home-q129)) | the friend asked | that sport's questionnaire, through the level pass and its usual return |
| **Level got** | the asker | the picker of the group the ask was made from |

*It's a game!* fires when the last seat is taken, to all four. **Answering a request or an invitation
on Home clears it from the bell too.** A *level asked* row leaves the bell as soon as its asker is no
longer on the card: the level got by any route, **Not now**, or the asker no longer a friend (Q129).

---

## 13. Numbers in one place

| What | Number |
| --- | --- |
| Friends seated besides the sender | 3 in doubles (padel, badminton) · 1 in singles (tennis, squash) |
| How far ahead the card and *Find a court* look | 14 days, from the soonest hour still sellable |
| Time to answer an invitation | 24 hours, never past the cut-off (made before it) or the start (made after it) |
| Friends games waiting for answers, per sender | at most 2 |
| Each friends game | 1 of each player's games per week |
| The cover warning | once, 24 hours before the cut-off, Split only |
| Held on a Split sender's card at send | the whole court: his share + a cover per other seat (100 zł for a 100 zł court) |
| Ask for a level | once per friend per sport |
| Requests to people outside your groups | at most 10 a Warsaw day; group-mates never counted (Q130, `daily_request_limit`) |
| A level ask on Home | one card per sport, up to three faces, no expiry |
| A friend request's push | once per request |
| Other clubs for an official group | within the club's distance, 10 km by default; switch on by default |
| Other clubs for a player group | within 10 km of the home club (unchanged) |
| Android install referrer | read once, on first launch; kept by Play for 90 days |
| A friend link's code | random, shaped like a group's code, never reused |

---

## 14. Calls made without a ruling

Calls 1–6 were agreed by the product owner before PRD #743 was published; **calls 7–11 are open for
the product owner to overrule**, each marked where it stands above.

1. The cover is one hold per seat, using today's hold, take and let-go steps, so partial capture isn't
   needed (refined by call 7).
2. Sending and accepting are made with the player present, so a bank confirmation happens in the app.
3. The other-clubs switch is on by default for every club, existing ones included. The club website
   keeps *"when ours are full"*.
4. The picker sorts friends by level, highest first, as in mock 3.
5. The card avoids any hour where one of the four has a game. A full week refuses Accept with a
   sentence.
6. One row, Q128, records the grilling.
7. **Covers stay held until the cut-off**, and only then is each taken (seat unpaid by its own
   player) or let go. Call 1 as agreed said a cover is let go when the seat's own player pays; but if
   that friend later left before the cut-off, the seat would need a new hold on the sender's card
   without him present. Keeping every cover held matches the agreed words, *"We hold 100 zł on your
   card until Fri 10:00"*.
8. **The Split / Whole choice and the final order button sit on a send sheet**, opened by the card's
   *Send game and pay 25 zł*, so the maximum is on screen when the binding button is pressed.
9. **An invitation made after the cut-off**, into a rescue seat, runs 24 hours but never past the
   game's start.
10. **Friends games ignore the level window, the kind's tolerance and gender preferences.** They still
    respect blocks, a level in the sport, one game per hour and the weekly limit. A seat opened to the
    group is offered as any rescue is.
11. **On You › Friends, friends are sorted alphabetically**, since that page has no single sport.
    Each row shows the sports they play, with their levels.

**PRD #762's ten calls** (2026-11-07, [§5.1](#51-the-ask-waits-on-her-home-q129)) are listed in the
decision log's Q129 row, and each that a rule rests on is marked *(a call)* where it stands. They are
open for the product owner to overrule.

**Defaults stated in the grilling and not objected to:** Info stays in the group header; the *friend*
tag on every face; the Friends tab's kind switch is per game, never intent; hours from the club's
book-by to 14 days where nobody has a game; the usual yes withdrawals; friendship survives leaving a
group and ends on deletion; the administrator's Members view has no pills; the chat opens at send; a
club's cancel moves the game; the club sees an ordinary booking.

---

## 15. Edge cases

- **A friend removed after a game was sent** stays in it: removing a friend touches no game.
- **A block between two players already in one friends game** touches no booking, as any block
  (ADR-0193 §4); it ends their friendship.
- **The sender seats a friend who then blocks another seated friend** before he sends: the card
  refuses with the neutral sentence.
- **Two invitees racing for one empty seat**: the first to accept and pay takes it; the other reads
  *seat taken*.
- **An invitee whose card is refused on Accept** keeps her seat to retry until her 24 hours end
  ([#751](https://github.com/Raketa02/Raketa/issues/751)'s rule, not the fill's 30-minute time to fix
  the card: the invitation's own clock is already running).
- **A friend's Accept when her week fills meanwhile** is refused with a sentence; her seat runs out as
  silence would.
- **An invitee who leaves a group** keeps her invitation: the game belongs to the group, and she
  plays as a guest.
- **A link opened by somebody its owner already asked**, or opened twice, makes no second request:
  the owner's is already open. Whether a request the opener set aside comes back to Home when the
  link is opened is left to [#748](https://github.com/Raketa02/Raketa/issues/748) and
  [#756](https://github.com/Raketa02/Raketa/issues/756) to settle.
- **A friend removed, then a friend again**, whose level ask was still waiting and not set aside, is
  back on the ask's card, because the card reads friendship live ([§5.1](#51-the-ask-waits-on-her-home-q129))
  *(a call: it follows from PRD #762's Home read, which no ruling names)*. This is no set-aside ask
  coming back: an ask she set aside stays aside. Unblocking alone brings nothing back, since a block
  ended the friendship.
- **A player asked in two sports** has two cards, one per sport, and the row reads
  *ASKED FOR A LEVEL · 2*. Getting one level takes only that sport's card.
- **A friends game at an hour Ogrody 33 is full** is at Wisła Park, marked as offered because Ogrody 33
  is full; the club's own players still see Ogrody 33 first at every hour it has a court.
- **A club that switches other clubs off** after a friends game was booked at another club changes
  nothing booked.

---

## 16. Out of scope

- Finding players outside your groups (a search for any player), friend suggestions, mutual friends,
  and a friends feed. *(Since 2026-11-07, Q130: the ranking finds players outside your groups, and
  any of them listed on General may be asked. A search for a player by name stays out.)*
- Chatting with a friend outside a game.
- **A friends-first head start on rescues.** It was removed before
  ([games and fill-in §22.1](../games-and-fill-in/the-mechanics.md#221-from-the-pdfs-removed-on-purpose))
  and stays removed: friends games don't bring it back.
- Changing a sent game's court or hour. You call it off and send again.
- A friend taking over the sender's cover (Q46).
- Any change to the Games deck's, Post a game's or rescues' money: friends games alone have a cover.
- iOS keeping the link through an install with no second tap (App Clips, reading the clipboard).
- A limit on the number of friends.
- The club website showing friends games differently from other bookings.
- What a club's cancel that no court absorbs owes a friends game's **guests**, who have no deck in
  its group to be dealt an owed card in. Its group members are owed one as in any group.
- Polish words and screen-reader support, which are app-wide decisions already made
  ([ADR-0198](../../adr/0198-the-player-app-is-not-built-for-screen-readers-for-now.md)).

---

## 17. Evidence

- **Rivals book at once and hold one person responsible.** Playtomic's split booking: *"the owner"*
  books, the others pay until 2 hours after the match, and the unpaid rest is charged to the owner.
  MATCHi holds the full court on the booker's card and charges unpaid seats at the regular price.
  Playmore's organiser pays the whole court. Playmore's challenge reserves the court at once, and
  *"you pay only when the rival accepts, at the latest a day before the match"*.
- **Declined requests are silent elsewhere too.** LinkedIn and Strava don't tell the sender, and
  MATCHi's shared profile link adds nobody as a friend by itself.
- **Law.** The Payment Services Act's art. 49b (PSD2 art. 75) allows blocking an amount only with the
  payer's consent to that exact amount. Under the Civil Code, the sender's cover is his own
  obligation, which he agrees to at send. The order button's words are reviewed
  ([games and fill-in §12.5](../games-and-fill-in/the-mechanics.md#125-saving-a-payment-method-and-the-terms), O3).
- **Platforms.** An iPhone has no install referrer, and Android's Play Install Referrer keeps it for 90
  days.
