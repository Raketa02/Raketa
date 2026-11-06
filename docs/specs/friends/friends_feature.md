# Friends Feature — End-to-End Specification

## 1. Overview

This document introduces the **Friends tab** functionality end to end.

The purpose of the Friends feature is to let players add the friends they have in Rakieta and create a game with them.

In Rakieta, a **friend** is someone from your group members whom you chose to add as a friend and who accepted your friend request.

Friendship exists for one reason: **it is the shortcut to building a game with people you already know, instead of letting the app pick your opponents.**

---

## 2. Scope and Instructions

### 2.1 Design priority

- Mock references are provided for the frontend design and theming.
- **The mocks have priority for the design.** If any ADR has to be modified or updated, the design from the mocks takes priority.

### 2.2 Frontend work

- This document describes how the Friends feature works end to end and provides mock references.
- You must extract and infer, from the description and the mock references, all the needed domain logic and the logic for every frontend layer.

### 2.3 Backend work

- You must infer all the backend work from the frontend requirements and from how the frontend will work.
- It is entirely up to you to infer everything needed on the backend side, including every detail: database architecture, structure, domain logic and the logic of every backend layer.

---

## 3. How You Become Friends

### 3.1 Group Members page (main entry point)

Friends are made where you meet people, which in Rakieta is inside your groups. The main place is a group's **Members** page:

- Every person who is not your friend yet has a **+ Add** button next to their name.
- People who already are your friends carry a green **friend** tag.

**About the mock:** it is only a mock. **The current design of the rows, as already implemented, has priority.** From the mock, extract only:

- the functionality and design of the **+ Add** button;
- the corresponding tags for **request waiting** and **friend**.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/1.members_friends_add.png`

### 3.2 Player record (tap anyone's face)

Tap anyone's face anywhere in the app — on a game card, in the deck, in a members list — and their **player record** opens with **Add as a friend** at the bottom.

- There is **no mock reference** for this button in the player record. You have to propose the design of this button and its layout within the player record.
- In a game card, if the card contains a friend, that player shows the **friend** tag. This is probably already implemented, but since the Friends feature did not exist yet, the tag was hidden.

### 3.3 Result page (after a game)

After a game, the result page offers to add the people you just played with.

- There is **no mock reference** for this. You must propose the design of this button and its layout within the result page.

### 3.4 Friends page (list of friends)

When the player is on the **Friends tab** and taps the **+** icons on the court graphic or the **+ Friends** button, the **Friends page** opens. It contains a list of all your friends.

- The page has a **"+ Add friends"** button in the top-right corner.
- Each row represents a friend, and a row can be selected when tapped.
- The mock below shows how the list of friends is presented and how it should look in terms of design and theming.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/3_Friends_screen.png`

### 3.5 "+ Add friends" bottom sheet

When **"+ Add friends"** is tapped, a bottom sheet dialog appears offering two ways of adding friends:

1. **From your groups** — it shows the groups you are in. Tapping a group navigates you to that group's **Members** page, where you can add players as friends.
2. **Invite link** — if your friend is not a Rakieta member yet, it provides you an invite link. When they sign up through it, you are friends automatically.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/4_add_friends_bottom_dislog.png`

### 3.6 Friend requests

Adding a friend is a **request**:

- Tap **Add** and the button becomes **request sent**.
- The other player is requested, and nothing changes until they answer.

**Friend requests on Home:**

- All friend requests are materialized on the Home screen as **friend request cards** in a horizontal list at the very top, above the **Your games** cards.
- When you answer all the requests — by pressing either **Accept** or **Not now** — the entire row, including its **"Friend Requests"** title, disappears, leaving the Games row alone in a clean UI.
- **The Friend Requests row must not be kept if it is empty.**

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/5_reqeust_card.png`

> **To evaluate — push notifications for friend requests:** evaluate whether a friend request should send a push notification, and whether the player can turn it on or off, or whether it belongs to the group of notifications that are on by default when the player opts in for notifications.

### 3.7 When the request is accepted

When they say yes:

- You are told (e.g. *"Kuba said yes — you are friends"*).
- The tag turns to **friend** everywhere at once.

> **To evaluate — push notification for acceptance:** evaluate whether a push notification is required to inform you that a player became your friend.

---

## 4. What Being Friends Gets You

### 4.1 The Friends tab inside a group

The payoff lives on the **Friends tab inside a group**: a court drawn on screen with you already in one seat.

- Tap **+ Friends** and the picker shows your friends from this group or from any other group.
- **Rakieta holds friends across all your groups.** Friends are not isolated to a single group. As stated above, Rakieta lets you add as friends players from any of the groups you have joined.

### 4.2 Seating players and choosing the game type

- On the court graphic in the Friends tab, tap a name to seat them; tap again to take them off.
- Above the court you pick **Competitive** or **For fun**.
  - **General rule:** a **Competitive** game counts for the score; a **For fun** game does not count, since it is just a friendly game.

### 4.3 Picking friends

- Tap the **+** icon on the court graphic to add friends. This opens the **Friends** screen in picker mode.
- You select players. When the number of players needed to fill the game for that type of sport is reached, the rest of the players in the list are **greyed out**:
  - **Doubles:** 3 players (you are already seated on the court).
  - **Singles:** 1 player.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/6_freinds_grayed_out.png`

- After picking all the players required for the game, tap the **Done** button on the Friends page.
- Tapping **Done** navigates you back to the Friends tab with all the players seated on the court graphic.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/7_graphic_court_filled.png`

### 4.4 Building the game card

The moment every seat is taken, Rakieta builds the **game card** underneath the court graphic, in a similar way to the game card deck. If a loading state is needed to build the game, include it.

The idea is that once you select your friends and add them to the court graphic, Rakieta has everything it needs to build a game that can actually be played, since it can have a court assigned to the game in the same fashion as the game deck cards. Rakieta has:

- the information needed to build the forecast;
- your availability and your friends' availability;
- possibly available courts in the pool, so it can propose a game with a court assigned, ready to be booked.

In this case, Rakieta builds a game and shows a card with:

- how balanced the four players are;
- how well your and your friends' standing weeks overlap;
- a free court at the club, in a slot you all share, with the **price per person**.

If that court does not suit you, you can pick another available one from the calendar.

The mock below shows the Friends tab once your friends have been added to the court graphic and the game card is built. Since the screen is scrollable in this state (court graphic + game card), the mock does not show the top of the screen — only the court graphic and the game card.

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/8_friends_and_game.png`

> Mock reference with details about the game card: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/9_friends_game_card.png`

**Important:** the game card here shows exactly the same information and has exactly the same design as in the game deck, **except that the player tiles are not shown**.

### 4.5 "Pick a different court"

When the **"Pick a different court"** button is tapped, a bottom sheet with the available courts appears.

#### Official groups rule

- In **official groups with a home club**, the home club's courts appear **first**.
- This supports our business model: getting in touch with clubs and bringing their groups from WhatsApp, Facebook or any social media into Rakieta. We make a deal with the club, and one of the collaboration agreements is that, in their official groups, **their courts are used and published first**.
- Only when the home club runs out of courts can courts from other clubs become visible in the official group. This satisfies ongoing player demand for games and does not constrain players to the home club after the home club has filled its court hours.

#### The friction to solve

- If the home club gradually runs out of courts because they are being booked, or if the home club makes only a low number of courts available to Rakieta, it can become harder to match players' availability.
- As a result, we can end up in situations where games with courts can't be built, because those courts don't match the players' availability.
- To satisfy player demand and let Rakieta keep building game cards with courts assigned, it is necessary to also draw on courts from other clubs.
- Therefore it is important to establish a **threshold** from which courts from other clubs start being used inside official groups.
- This problem does not happen in **regular groups**, because they are not tied to a home club to such an extent.
- One possibility: when a certain percentage of the home club's courts is filled (e.g. **70%**), Rakieta also starts using courts from other clubs.

> **To evaluate:** evaluate this carefully and propose the best option that:
> - does not damage our business model;
> - does not harm the club that partnered with us and created the official group in Rakieta;
> - does not leave players without the possibility to keep booking, and does not leave potential demand unsatisfied — otherwise players will simply drop.

#### Design reference

The mocks below show how the overall design and layout should look. They are only for orientation on design and layout; the logic, and which courts should appear according to your evaluation of the rules for the business model, the clubs and the players, is up to you to determine.

> Mock references:
> - `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/10_find_court_1.png`
> - `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/11_find_court_2.png`

Once a court is selected, the game card is updated automatically.

### 4.6 Sending the game

When the **"Send game and pay [amount] zł"** button is tapped, the game is sent to your friends:

- They are notified, and the invitation is also available under the **bell** icon.
- The game invitation is also materialized on the Home screen with the following design:

> Mock reference: `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/12_game_friend_invitation.png`

### 4.7 Acceptance and payment

When all your friends accept the invitation, payment takes place when the last friend accepts — in the same fashion as when the last yes is given in the game deck.

---

## Appendix — Mock Reference Index

| # | Screen | Path |
|---|--------|------|
| 1 | Members page — + Add / request waiting / friend tags | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/1.members_friends_add.png` |
| 3 | Friends list screen | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/3_Friends_screen.png` |
| 4 | Add friends bottom sheet | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/4_add_friends_bottom_dislog.png` |
| 5 | Friend request card (Home) | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/5_reqeust_card.png` |
| 6 | Friends picker — greyed out | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/6_freinds_grayed_out.png` |
| 7 | Court graphic filled | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/7_graphic_court_filled.png` |
| 8 | Friends tab — court + game card | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/8_friends_and_game.png` |
| 9 | Friends game card details | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/9_friends_game_card.png` |
| 10 | Find court (1) | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/10_find_court_1.png` |
| 11 | Find court (2) | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/11_find_court_2.png` |
| 12 | Game friend invitation (Home) | `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/3-Friends/12_game_friend_invitation.png` |
