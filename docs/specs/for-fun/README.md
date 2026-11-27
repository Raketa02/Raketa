# For fun: the record and its mocks

**What PRD [#827](https://github.com/Raketa02/Raketa/issues/827) is drawn from.** The product
owner's brief *For-Fun Game Cards Refactor*, its 7 mocks, and the decision log of the grilling held
on it on 2026-11-22 (Q1–Q22 and Q3b). They are copied here from the product owner's own folder,
`2.for_fun_refactor`, so every session can read them. Landed by
[#828](https://github.com/Raketa02/Raketa/issues/828) on 2026-11-22.

| File | What it holds |
| --- | --- |
| [for_fun_feature.md](for_fun_feature.md) | The product owner's brief, verbatim. Its paths point at their own folder: read a path by the [index](#index)'s original name. The folder's `for_fun.pdf` is the same text and isn't copied |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim: every ruling with its reason, the facts it rests on, and the question index Q1–Q22. Its status line and its delivery section (§17) predate PRD #827 |
| [`mocks/`](mocks/) | The 7 mocks, renamed by what they show and keeping their number (the [index](#index) gives each original name) |

**The decision is [ADR-0207](../../adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md).**
Where the log and ADR-0207 or PRD #827 disagree, ADR-0207 and PRD #827 win.

**This folder holds the record, not the spec.** Each part is specified where it already lives, and
the ticket that ships it amends that place: the home-rows mechanics §8.2 and §8.7, the You spec
§3.11, the Games and Fill in mechanics and screens, the words
([`the-words.md`](../matchmaking/the-words.md)), the player record, the player app's design system
and feature docs, and the backend's context rules. Until a ticket amends them, they describe For fun
as it is today.

The terms are in the root [`CONTEXT.md`](../../../CONTEXT.md): **Social vibe** (Matchmaking, beside
the Forecast) and **Social tag** (Player profile).

## How to read the mocks

1. **The mocks lead on design.** The brief says *"Follow the mock designs as they are."* Where an
   ADR, a spec or the locked design system disagrees with a mock on a look, the document changes, by
   name (ADR-0207 §9). **On a rule, the decisions win.** Three named exceptions run the other way
   (ADR-0207 §10), and every place a mock is overridden is listed under [*Overrides*](#overrides).
2. **Their data is only data.** The brief says *"Do not hardcode any data. Do not make decisions
   based on the mocked data."* No rule is read off a mock's names, levels, tags, percentages, words,
   prices, dates or button text.
3. **Cite a mock by this folder's number**: *for fun 7*. The numbers are the brief's index, 1 to 7.
   **The decision log's prose and PRD #827 count by the files' original prefixes**, which run 1, 2,
   3, 3, 4, 5, 6, so translate them:

   | The log and PRD #827 say | This folder's number |
   | --- | --- |
   | mock 1, mock 2 | 1, 2 |
   | mock 3 (competitive details, both files) | 3 and 4 |
   | mocks 4/5 (For-fun details) | 5 and 6 |
   | mock 6 (the Social vibe card), *"mock 6 leads over mocks 4/5"* | **7**: *mock 7 leads over mocks 5 and 6* |
   | *"as in mocks 3–5"* (the answer pair side by side) | 4 and 6, the two that draw it |

   The log's own *Mock index* numbers the files 1 to 7 as here, though its row 7 still says *mocks
   4/5*. The player tickets, #836 on, cite this folder's numbers.
4. **A face is today's face**, the photo or the generated court poster, **with no letters**: the
   headers of mocks 3 and 5 draw initials over the faces.
5. **The brief's *Rakieta* is the brand as written**
   ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md)).

## Which mock shows what

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | The For-fun deck card | **The Social vibe row in the forecast row's place**: below the tiles and the *A + B vs C + D* line, above the week strip. The rest is today's card: the tiles with FRIEND, IN and levels, the vs line, the overlap strip and its grade, the court block | No ribbon is drawn: the ribbon keeps today's states (the brief §4.1). The data (note 1) |
| 2 | The Social vibe row | **The % on the left, beside a full-width 0–100 bar**, its fill the same value as the %, and ***Social vibe*** **in italics inside the bar**, readable over the fill and the track | *67%* and its colour: the colour follows the band (ADR-0207 §8) |
| 3 | Competitive details, top | **The BALANCE FORECAST card first**, on paper: each side's level, *gap* and the signed gap; the bar with the sides' names; the % and its word; *A counted game — a confirmed score moves everybody's level.*; ***If you win*** (green tint) and ***If you lose*** (beige). Then the dark game card | The header's *Padel · 3 of 4 in* (note 3); the faces' letters; the data |
| 4 | Competitive details, foot | The facts (WHERE, DAY, TIME, YOUR SHARE) with the coral rule, then **the answer pair inside the dark card's foot, side by side**: *Not this time* white and secondary on the left, the yes coral and primary on the right | The yes's *I'm in · books it · 27 zł* (note 2); the data |
| 5 | For-fun details, top | **The SOCIAL VIBE card first**, in the forecast's place, on paper: the eyebrow, the big % in olive with its word, the bar, the grid. Then the dark game card, unchanged | The grid's column order and its missing emoji (note 4); the header's *Padel · 2 of 4 in* (note 3); its tag names (note 5); the faces' letters |
| 6 | For-fun details, foot | The grid's last rows, then the dark card with **the answer pair in its foot**, as in 4 | As 5. *I'm in* only because this yes doesn't complete the game |
| 7 | The Social vibe card | **It leads over 5 and 6.** The eyebrow *SOCIAL VIBE*; the big % in olive ink with its word beside it; **the bar full width below**; the columns **You first**, then tile order, round photos with nicknames below; the rows **emoji and label**; olive dots under each carrier; **a shared row on a pale volt band with dark text; a row only you have in grey with a grey dot**, no band | *67%*, *Good vibe*, which tags, who carries them |

**No mock draws:** the other three bands and their colours; a singles grid of two columns; a long
nickname shortened; a 💘 row; the Social vibe card on the booked game screen and at the court; the
Friends card and Post a game's fits with the vibe; the action row's other states (*Pay {share}*,
*Booking…*, Withdraw, Leave the game, Confirm payment) and the offline note; *Who is free* below the
card; the ribbon on a For-fun card; and the picker with 27 tags. Each is designed by the ticket that
ships it, from the mocks' own parts, ADR-0207 and the design system, and named there as designed, not
drawn.

## Overrides

Each is a ruling of the grilling (its Q in [decisions.md](decisions.md#question-index)). The mock or
the brief is right everywhere else.

| Note | Where | What it says | What is built |
| --- | --- | --- | --- |
| 1 | every mock | Sample names, levels, %, words, prices, dates, *no answer yet*, *You complete it*, Home's badge *4* | **Sample only.** The backend sends every figure, and the band's word follows the % |
| 2 | 4 | The yes reads *I'm in · books it · 27 zł* | **Today's words**: *I'm in*, *Pay {share}* when your yes completes the game, *Booking…* while it books (Q15) |
| 3 | 3, 5 | The header's subline *Padel · 3 of 4 in* | ***Padel*** **or *Padel · For fun***; the count only in the status tag (Q16) |
| 4 | 5, 6 | The grid's columns *Magda, Filip, You, Kuba*, its rows with no emoji | **Mock 7's grid**: you first, then tile order; an emoji per tag (Q6) |
| 5 | 5, 6 | Rows such as *After-match beer*, *Always keeps score*, *Weekend player*, *Fair play first*, *Long rallies* | **The vocabulary's labels**: a row is one of the reader's tags, as in mock 7 |
| 6 | the brief §4.2.2 | The bar *"next to the word"* | **Full width below the % and its word**, as mock 7 draws it (Q6) |
| 7 | the brief §4.2.2 | Rows *"in the order you chose them in your profile"* | **The vocabulary's order.** The pick order is not stored (Q10) |
| 8 | the brief §2.1 | *"Skill still has some weight"* | **Skill is a guard, never a weight**: the level window, the evenest sides and a tie-break (Q13) |

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_for_fun_card.png`](mocks/01_for_fun_card.png) | `1_for_fun_card.png` |
| 2 | [`02_social_vibe_component.png`](mocks/02_social_vibe_component.png) | `2_social_vibe_component.png` |
| 3 | [`03_competitive_details_top.png`](mocks/03_competitive_details_top.png) | `3_competitive_game_card_details1.png` |
| 4 | [`04_competitive_details_foot.png`](mocks/04_competitive_details_foot.png) | `3_competitive_game_card_details2.png` |
| 5 | [`05_for_fun_details_top.png`](mocks/05_for_fun_details_top.png) | `4_forfun_game_details1.png` |
| 6 | [`06_for_fun_details_foot.png`](mocks/06_for_fun_details_foot.png) | `5_forfun_game_details2.png` |
| 7 | [`07_social_vibe_card.png`](mocks/07_social_vibe_card.png) | `6_social_vibe_card_details.png` |
