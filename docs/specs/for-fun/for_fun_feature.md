# Feature: For-Fun Game Cards Refactor

## 0. Overview and Scope

**Goal:** Optimize how game cards are built when the player selects the **For fun** tab option inside the **Games** tab.

**Scope:** This work includes both **frontend** and **backend** work.

### 0.1 Frontend instructions

- Mock references with the designs are provided (see [Section 4](#4-design) and the [Mock Reference Index](#5-mock-reference-index)).
- **Design priority:** Follow the mock designs as they are. If you have to update or create a new ADR, do it using the mock reference designs.
- **Logic:** For the logic of all the layers on the frontend, you must infer the needed logic from the explanations in this document and from the mock references. The logic across all the different frontend layers is up to you.
- **Very important — mocked data:** The mocks come with mocked data.
  - Do **not** hardcode any data.
  - Do **not** make decisions based on the mocked data shown in the mock references.

### 0.2 Backend instructions

- No backend information is provided.
- You must infer the logic and behavior that needs to be implemented on the backend side, for every layer, based on the needs and behavior of the frontend.
- This also includes the **database architecture and structure**.
- It is entirely up to you to infer and determine the logic the backend requires to satisfy the frontend needs.

---

## 1. Main Purpose of the "For Fun" Games

The main purpose and goal of the For-fun game cards regarding the business, the club and the players is the following.

From the product side, the For-fun game cards exist to serve the players what the competitive deck quietly leaves out, and to do a job for the club that the competitive deck doesn't, which is **to match players by their social vibe**.

- **Competitive card:** a bet on a result — forecast, stakes, your level moving.
- **Who the For-fun deck is for:** Plenty of people in a padel group don't want that every time, or ever: beginners, people new in town, people who play to unwind, people who would rather have the coffee after than the counted score.
- **The problem without it:** Without a For-fun deck, those players either take competitive cards they don't enjoy or stop answering cards at all.
- **What the For-fun card offers:** A game where nothing is at stake and the only promise is good company — and it keeps them inside Rakieta instead of drifting to a WhatsApp group.
- **Social layer feeding the competitive layer:** The For-fun deck deliberately puts you with new faces who share your tags, so after a few friendlies you actually know the people in *a given club* — which is what makes someone come back on a Tuesday night, and what later makes them say yes to a competitive card with a name they recognise. It is the social layer that feeds the competitive layer.
- **For Rakieta — retention and trust:** People who play for fun play more often and churn less; people who have met their group are harder to lose.
- **Keeping both decks credible:** By keeping the For-fun card honest — no levels move, no stakes, the vibe number a plain fact about the four — the product keeps the competitive number credible too. Two decks with two clearly different promises are easier to trust than one deck that tries to be both.

### 1.1 Investigation task: separate competitive and for-fun

You have to investigate how the current logic builds the For-fun game cards and determine whether both competitive and For-fun follow the same approach. **The separation between competitive and fun games must be made clear.**

---

## 2. Best Approach to Build For-Fun Game Cards (Reliable and Consistent)

To achieve the goal from [Section 1](#1-main-purpose-of-the-for-fun-games) and build real For-fun game cards, the logic should use what the application already has: **the social tags that each player selects during onboarding**.

> **Important:** It is very important for you to evaluate, determine and elaborate the best logic and algorithm for building the For-fun game cards, starting from the initial ideas below. These initial ideas must **not** be taken as final. You must evaluate, refine, improve and adjust them so the resulting logic matches the main purpose described in [Section 1](#1-main-purpose-of-the-for-fun-games).

### 2.1 Initial ideas (to be refined)

#### Weighting: social tags vs. skill

- The **social vibe tags** are the most important ingredient, with the **highest weight** when building the games. *(How much weight the social tags take must be defined.)*
- **Skill** is no longer as important as it is in the competitive cards. Skill still has some weight, to control the build and avoid very unbalanced game cards, but the main component that carries most of the weight is the **social tags shared between the players**.

#### Deck ordering

- In the For-fun deck, the game cards where **more social tags are shared** among the players composing that card appear **at the top of the deck**.
- As you swipe through the cards, the overall shared tags gradually decrease, little by little, depending on the players.

#### What social tags mean

- Social tags describe **what a player is like to be around, not how they hit**.
- Example: when Rakieta builds a For-fun four, the tables where those tags overlap come first: people who'd stay for a drink after the match get put with people who'd stay for a coffee when possible; the ones who are here to meet players end up together when possible.
- **The more tags the players share, the better fit those players have together.**

#### Overall social vibe score

- Each For-fun game card comes with an **overall social vibe score** that is visible on the card itself (design is specified in [Section 4.1](#41-for-fun-game-card)).
- Example: an overall social vibe score of **67%** on the card, with its fill bar, indicates how much of what the four of them carry is shared, so that at a glance players can get an idea of what vibe is shared in that game card.

### 2.2 Constraint: do not change availability and court assignment

- The logic around **player overall availability** and **court assignment** for the For-fun game cards must **not** be changed.
- **Why:** When it comes to playing for fun, an important component is that cards are also built with players who share free slots, so that the actual For-fun game is possible and a court is assigned.
- The logic of matching players by availability and assigning a court must stay **the same as in the competitive game cards**.

---

## 3. Separation of Card Types — Summary

| Aspect | Competitive | For fun |
|---|---|---|
| Promise | A bet on a result — forecast, stakes, your level moving | Nothing at stake; the only promise is good company |
| Main matching ingredient | Skill | Shared social tags (highest weight); skill has some weight to avoid very unbalanced cards |
| Levels / stakes | Levels move, stakes apply | No levels move, no stakes |
| Headline indicator | Balance forecast | Social vibe score (%) + fill bar |
| Availability & court assignment | Current logic | Same as competitive (unchanged) |

*(This table summarizes Sections 1–2 and 4; it adds no new requirements.)*

---

## 4. Design

### 4.1 For-fun game card

The following mock reference shows how the For-fun game card looks in terms of design:

- **Mock reference:** `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\1_for_fun_card.png"`

Notes:

- This is a mocked reference to show how the elements are displayed inside the card.
- Most of the components inside the card are already built. **The only difference is the percentage score and the fill bar next to it.**
- **Ribbon:** The mocked For-fun game card is shown without a ribbon. This is just a mock, so the ribbon in its different states must follow the current logic and must still be kept when needed, as per the current logic.
- **The only design change is the percentage score and the fill bar.**

#### 4.1.1 Social vibe component (percentage + fill bar)

- **Mock reference:** `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\2_social_vibe_component.png"`
- The **color code** for the percentage number and the bar must be defined depending on the percentage.
- The percentage and the bar fill represent the same value. The bar goes from 0 to 100%, so 67% fills the bar by that amount.

### 4.2 Game details screen

The game details screen opens when the game card is clicked or when the **i** (information) icon at the bottom is clicked.

The details of a game card now also follow the intent of separating competitive and For-fun. The designs and explanations of each one are provided separately below.

#### 4.2.1 Competitive game card details (two minor changes)

1. **Balance forecast card moves to the top.** In addition to the forecast bar information, it will also show **what is at stake**.
2. **"Not this time" and "I'm in" buttons move inside the main card** in the details screen, instead of at the bottom.
   - Do **not** change the wording of the "I'm in" button. It must be written as it currently is, according to the card state — the only difference is its placement inside the main card.
   - The wording of the "I'm in" button must be kept depending on whether it is the last yes or not. This should already be defined: verify that it is defined and keep that text. If it is already defined, do **not** take the text from the mock reference into account.

Since the game details screen is scrollable, two mock references are provided:

- `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\3_competitive_game_card_details1.png"`
- `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\3_competitive_game_card_details2.png"`

#### 4.2.2 For-fun game card details

These mock references show how the main elements are placed in the For-fun game card details screen, so you understand how the layout is built:

- `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\4_forfun_game_details1.png"`
- `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\5_forfun_game_details2.png"`

##### Social vibe card

The **Social vibe card** is the first thing on the screen, in place of the competitive game's **Balance forecast**.

- **Mock reference of the social vibe card:** `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\6_social_vibe_card_details.png"`

**Top section**

- The same **[n]%** as on the game card, plus its word (for example **Good vibe**). *The words corresponding to each percentage range must be defined.*
- Next to the word, the same fill bar as on the card — so the number you swiped on is the number you're looking at.

**The grid**

- **Columns (players):** four or two players (depending on whether the swiped card was a doubles or a singles), shown as round photos with their nicknames below — the other players and you, as in the mock. If a nickname is long, ellipsize it.
- **Rows (your tags only):** Down the side, **your tags only**, one tag per row, in the order you chose them in your profile.
- **Dots:** A dot sits under every player who carries that tag and shares it with you. Your column therefore always has one dot on each row.
- **Row highlighting:**
  - A row that **at least one other player shares** is **highlighted** (pale volt band, dark text, olive dots).
  - A row that **only you have** stays grey with a grey dot.
- **Live updates from your profile:** If you change your social tags in the **You** tab, that change also takes effect in the game details: the social tags shown will change, and therefore so will how the For-fun game cards are built for you. The engine sees your social vibe at any time and adjusts to it, building game cards from your most up-to-date social vibe.

**How to read the card**

- Reading across a row tells you which of your tags is a common thread at this table.
- The **big number** says *how much this table shares overall* (it counts everyone's tags).
- The **grid** says *who shares yours* — the grid is deliberately your tags only, with no languages and none of the others' tags that you don't carry.

##### Player tiles and game details card

The card that shows the player tiles and the game details (**where, day, time, your share**) is kept as it currently is, including the two answer buttons inside the card itself, with the text corresponding to the game card state depending on whether a last yes lands or not, as it currently works.

---

## 5. Mock Reference Index

| # | Mock reference path | Used in |
|---|---|---|
| 1 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\1_for_fun_card.png"` | 4.1 For-fun game card |
| 2 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\2_social_vibe_component.png"` | 4.1.1 Social vibe component |
| 3 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\3_competitive_game_card_details1.png"` | 4.2.1 Competitive details (part 1) |
| 4 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\3_competitive_game_card_details2.png"` | 4.2.1 Competitive details (part 2) |
| 5 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\4_forfun_game_details1.png"` | 4.2.2 For-fun details (part 1) |
| 6 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\5_forfun_game_details2.png"` | 4.2.2 For-fun details (part 2) |
| 7 | `"C:\Users\rober\Desktop\rakieta_features\2.for_fun_refactor\6_social_vibe_card_details.png"` | 4.2.2 Social vibe card |

> Reminder: all mocks contain mocked data. Use them for layout and design only — do not hardcode their data or base logic on it.
