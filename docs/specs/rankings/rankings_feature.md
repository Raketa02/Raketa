# Rankings Feature

## Introduction

I want to introduce a new feature in rakieta player app called Rankings. The purpose of the rankings feature is to engage players to play and scale in a ranking. The ranking has two views, general and within your friends.

As a constraint for the design system and theming the design resultant from the mocks is what is prioritized. So if you have to update or create any ADR do it taking into account that the designs of the mocks is what the frontend_player application will have. You have to read and analyze all the mock references.

## Frontend work

Regarding the frontend work I will give you an overview of how the feature works in the player application. From the explanation and from the mocks you have to infer all the logic for all the frontend architecture layers.

## Backend work

Regarding the backend work, you have to infer all the logic for all layers in the backend from how the frontend works and its needs. You have to determine the logic of the backend and database architecture structure always following best practices and taking into account scalability and that the application will be used in production by thousands of players because the usage of the app is expected to grow fast. So scalability at any backend level is important.

---

## What the ranking is

Every player who plays competitive games has a place in a ranking, one per sport.

In the mock you will see that the ranking uses the player skill level. This is an initial idea but should not considered final. Your place in the mock is set by your level — the same number that sits on your Skill Passport and on every card the deck deals you Games marked For fun never touch it; that’s the whole difference between the two modes, and the page says so in three words under its title: Competitive games only.

Regarding how your place is set and by what a player is ranked is it very important for you to investigate how other competitors sets the ranking and determine what is the best option. Whether is it based only on the skill level or it has a separate system metric specific for the ranking so that also moves when player wins or loses after every game. So you have to determine by what metric the player is ranked and therefore what is it shown in the list ranking.

Some other ideas that you have to research and investigate the following: In racket and paddle sports (such as tennis, padel, or squash), ranking systems typically combine both concepts: a skill level number (like a functional rating) and a dynamic points or math number (like an Elo, MMR, or standings points total) that dictates that level

---

## How you get to navigate to Rankings screen

The way in is the button with the trophy in the top-right corner of Home, which always shows your current place in the ranking for example (🏆 **#7**). It’s a button and a number at once: a glance tells you where you are, a tap opens the ranking screen. From the game cards in home Home is also where you confirm results, so the number you see there is the one a win just changed.

->this is the mock reference for the button in the top-right corner of Home:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/1-ranking_button_home.png`

---

## The page and how Ranking works

At the top you choose between two views: **General**, everybody who plays that sport, and **Friends**, only the people you’ve added. The sport pill in the corner is the same one as on the games deck — it shows the current sport and slides open to the others when tapped.

The first thing you see is **Your place card**: your position and how many are ranked (for example: *7th of 13*), your rating, and whether you’ve moved this week (▲1) or not. Under it, one line turns the number into something to play for: *0,04 behind Karol · one win closes it · Zofia is 0,02 behind you* — who’s just above you, who’s breathing down your neck. At the top of the list it simply says *Top of the list*.

Then the podium for the top three, and the full list: position, face, nickname, the form dots of the last five games, how many places that person moved this week (up or down), and their rating. Your own row is tinted so you find it without reading. Tapping anyone opens their player record.

The Friends view is the one most people will keep coming back to: a league table of your friends , the same page with the noise removed. If you haven’t added anyone as friend who plays that sport yet, it says so and offers *Add friends*, which opens the usual add sheet.

---

## Here’s the Rankings screen, top to bottom, section by section.

This is the mock reference to show you how the overall ranking screen looks like. Since the screen can be scrollable depending on the number of rows I will give you more than one mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/4_rankings_screen1.png`

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/5_rankings_screen2.png`

### 1. Header

- ‹ chevron — returns to Home.
- Rankings — the page title.
- the sport pill, top-right, the same control as on the games deck.

### 2. View switch — General | Friends

A two-way toggle. General ranks everybody who plays that sport; Friends ranks only the people you’ve added as friends, plus you. Everything below the toggle — your place, the podium, the list — is recomputed for the view you pick, so “4th” in Friends and “7th” in General are two true answers to two different questions.

->mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/2-ranking_header.png`

### 3. Your place (dark card)

Your own summary, so you never have to hunt for your row.

- YOUR PLACE / 7th of 13 — your position in the chosen view and sport, and how many players are ranked in it.
- 2,71 — your rating: your level in that sport, the same number as on your Skill Passport and on game cards. This number can change after your evaluation of by what the player is ranked.
- ▲ 1 up this week — how many places you’ve moved this week (▲ up, ▼ down, — unchanged). After you confirm a result, this reflects the real move that result caused.
- The gap line — 0,04 behind Karol · one win closes it · Zofia is 0,02 behind you. The player directly above you and how far ahead they are, and the player directly below you and how close they are. It turns a position into a target. If you’re first it reads Top of the list. This line is intended to engage players

When this card can’t be shown, its place is taken by a message: Not ranked in squash yet — your first confirmed competitive game puts you on the list (General, a sport you haven’t played competitively), or Just you so far / Nobody rated in squash yet with an Add friends button (Friends view with fewer than two rated friends).

-> mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/3_your_place_card.png`

### 4. Podium

The top three of the current view on three steps: 1st in the middle on the tallest, bright step, 2nd on the left, 3rd on the right slightly smaller than 2nd. Each shows the player’s face, nickname (in the mock is shown the name but ignore it) and rating (the number can change depending on your evaluation by what the player is ranked). Tapping a player face from the podium opens their player record. It appears only when at least three players are ranked.

-> mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/6_rankings_podium.png`

### 5. The list

Every ranked player, best to worst, one row each:

- Position number — coral for the top three, grey for the rest.

  ->mock reference:

  `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/7_top_three.png`

- Face and name — tap to open the player’s record.
- Form dots — the last five competitive games, green for a win, grey for a loss, oldest to newest.
- Movement chip — places gained or lost this week: for example ▲2, ▼1, or — for no change.

  ->mock reference:

  `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/8_ranking_up.png`

  `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/9_ranking_down.png`

  `/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/10_ranking_same.png`

- Rating — the player’s rating that you determined in this sport, right-aligned, the number the list is sorted by.

Your own row is tinted and labelled You, so it stands out while scrolling.

->mock reference:

`/Users/Robert.Dinescu/Desktop/rkta_dev/raketa_v2.0/4-features/4-ranking/11_ranking_you.png`
