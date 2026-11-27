# For-fun game cards refactor — decision log

- **Date:** 2026-11-22
- **Source:** `for_fun_feature.md` (and the same text as `for_fun.pdf`) and the 7 mocks in this folder
- **Status:** every branch settled in a grilling session (Q1–Q22, with Q3b). This file is the input for `to-spec` / `to-tickets`. Nothing has been written to the repo yet (§17).
- **Ground rules (from the source document):**
  - The mocks lead on design. Where an ADR, a spec or the design system disagrees, the docs change to match the mocks, and each such case is recorded as a named exception.
  - Data in the mocks is only data. It is never hardcoded and decides nothing. The mocks' names, levels, tags, percentages, prices and the button text *"I'm in · books it · 27 zł"* are all illustration.
  - Availability matching and court assignment for For-fun cards stay exactly as they are for competitive cards (brief §2.2).

---

## 1. What changes, in one paragraph

Today a For-fun card is a competitive card with a looser level window. From now on, For-fun tables are **built and ranked by the social tags their players share**, and skill is only a guard. Every For-fun card carries a **Social vibe** percentage with a fill bar in the place where the balance forecast used to sit. No For-fun surface shows a forecast any more. The For-fun deck opens on the tables that share the most. The game details screen splits by kind:
- **Competitive** opens on the full **Balance forecast** card, which now includes **what is at stake** (*If you win / If you lose*).
- **For fun** opens on a **Social vibe** card: the %, its word, and a grid of *your* tags against the players at the table.

On both kinds, the answer buttons move inside the dark game card. The same per-kind information is shown everywhere a game of that kind is drawn. The social tag vocabulary grows from 19 to 27 tags, and a player may now pick 2–8.

---

## 2. What the investigation found (brief §1.1)

**Competitive and For fun were built by one algorithm.** The kind changes only four things:
- **Who is dealt it:** your Play intent must want the kind (`proposals/domain/proposer.py:199`; `NO_PREFERENCE` → both in `proposals/infrastructure/profile_wanted_kinds.py:34-42`).
- **The level window's tolerance:** 0.55 for Competitive, 0.90 for For fun, narrowed to 0.55 while either player is a Newcomer (`matchmaking/infrastructure/rulesets/r2026_09_15_a.py:38-39`, `matchmaking/domain/level_window.py:88-93`). The fit adapter says so in so many words: "the kinds differ only in the level window's tolerance" (`proposals/infrastructure/matcher_player_fit.py:133-134`).
- **Dealing order:** within an hour, Competitive is dealt before For fun (`proposer.py:585`). People, sets and courts are shared across kinds.
- **After the game:** a For-fun result never moves a level (`games/domain/standing.py:282-283`; `games/infrastructure/event_sourced_confirmed_results.py:78-79`). It asks no *How did it go?*, and stakes are computed only for counted games (`matchmaking/infrastructure/games_court_pairing.py:110-119`).

**Both kinds choose a four by the same score:** best forecast, then smallest level spread (`proposer.py:1186-1209`). **No social tag is read anywhere in building:** `Member` has no tag field, and the old tag matrix was removed in #580. **The player app draws both kinds with the same `GameCard`**, which has no branch on kind. **A For-fun card and the For-fun details screen both show the balance forecast today.**

So the separation the brief asks for doesn't exist today, and this feature creates it.

Other facts the decisions rest on:
- **Scale:**
  - at most 12 candidates are considered per court hour (the 12 holding the fewest cards), so at most 495 fours (`proposer.py:140, 1138-1147`);
  - a proposal has up to 3 versions and 3 next best fits per seat;
  - cards are dealt up to 14 days ahead.
- **Stored vs computed:**
  - a card's composition is stored in the `ProposalMade` / `VersionDealt` events and in `proposal_people`;
  - sides, forecast, overlap and deck order are worked out on every read.
- **What triggers a rebuild:** the triggers are listed in `proposals/application/handlers/mark_due_for_proposing.py`. `SocialTagsChanged` isn't one of them.
- **Tags:**
  - there are 19 tags in 3 groups;
  - a player holds 2–6;
  - the server re-sorts every selection into the vocabulary's order, so the order a player picked them in is lost;
  - tags are global, not per sport;
  - tags are already visible to other players on the player record;
  - languages don't exist anywhere;
  - there is no coffee tag and there are no tag relationships.
- **The forecast card and the stakes already exist,** but only for booked games: `features/games/components/ForecastBlock.tsx` (side levels, gap, bar, %, word, the counted/friendly sentence, `StakeTiles`), fed by `GET /games/{id}/pairing` → `at_stake{win_delta, loss_delta}`.
- **The answer button's wording is already defined:** *I'm in*, *Pay {share}* when your yes completes the game, and *Booking…* while booking (`yesButtonLabel`, `deckPresentation.ts:411-413`; `fillCopy.ts:24`).

---

## 3. Domain language and the ADR (Q1, Q9)

- **A new ADR** (the next free number, likely 0207) **narrows ADR-0204 §6.** Social tags now also **build and rank For-fun proposals** and give them their **Social vibe**. They still never touch a competitive card, a forecast or a level.
  - The ADR narrows two specs that say "a tag is shown, never scored" in the same breath: the You spec §3.11 (`docs/specs/you/the-you-screen.md`) and home-rows mechanics §8.2/§8.7 (`docs/specs/home-rows/the-mechanics.md`).
  - It records the design-system exceptions from §9 and the new tags from §6.
- **New glossary term: Social vibe.** It is how much of what everyone on a For-fun card carries is shared at that table (the formula is in §4). It is a plain fact about the people on the card and is the same for each of them.
  - *Avoid:* vibe %, which is Same vibe's pairwise **1 − ½ⁿ** and stays as it is; match %; compatibility.
  - Two players can show a Same vibe *Vibe %* and a singles *Social vibe* that differ. That is expected: they are different measures with different names.
- **Glossary updates:**
  - **Social tag:** 27 tags; 2–8; builds For fun; the 💘 exception.
  - **Mode:** now picks the For-fun score as well as the window.
  - **Match Fit engine:** also computes Social vibe.
  - **Group deck:** the For-fun order.
  - **Rescue:** a For-fun rescue's best fits.
  - **Vibe %:** gains 99 and 100.

## 4. Social vibe — the number (Q2, Q7, Q8, Q11, Q12)

- **The formula**, option (c), *shared by the others*:
  - The table is everyone named on **your version** of the card: the people In, you, and the names dealt for the open seats. An empty seat isn't part of it. Call the number of people *n*.
  - For every tag each player carries, count how many of the *other* players at the table carry it too, out of *n − 1*.
  - Average that over every tag-carrying at the table, ×100, rounded half up (as Vibe % is today: `floor(100·x + 0.5)`).
  - In symbols: `round(100 × Σᵢ Σ_{t ∈ Tᵢ} (c_t − 1)/(n − 1) ÷ Σᵢ |Tᵢ|)`, where `c_t` is how many people at the table carry tag `t`.
  - **In singles it reduces to the plain overlap of the two players.**
- **Why (c):**
  - It can be said in one sentence: on average, each tag at this table is carried by that share of the others.
  - A tag carried by all four counts for more than one carried by two.
  - It can't flatter two cliques: two pairs who share everything with each other and nothing across the table score 33%, not 100%.
- **Worked examples (invented, not from the mocks):**
  - All four carry exactly the same tags → **100%**.
  - A and B carry {x, y, z}, C and D carry {p, q, r} → each carrying is shared by 1 of 3 → **33%**.
  - A {x, y, z}, B {x, y}, C {x, w}, D {v, u} → (1 + 1 + ⅔ + 0) ÷ 9 carryings → **30%**.
- **Which tags count:**
  - **Exact tags only**, every tag weighing the same (Q11). Similar tags get no partial credit.
  - **💘 `OPEN_TO_MEET_SOMEONE` is ignored** in the % and in building (Q12 b). It still shows in the details grid like any other tag, with dots for everyone who shares it. Ignoring it keeps the For-fun deck from seating people together *because* of that motive. The vocabulary's own docstring places this tag "at the edge" of its rule (`player_profile/domain/social_tags.py:47-60`).
  - **Only the tags in the vocabulary count:** today's 19 plus the 8 new ones in §6. Languages don't exist, so the brief's "no languages" needs nothing.
- **Worked out live** on every read, from everyone's **current** tags, and **stored nowhere**. That follows the backend's "derived, never stored" rule.
  - An edit in the You tab shows on the next read of any card or screen, including a booked or already-played game.
  - **A tag change pulls nobody off a card already dealt** (unlike a changed Play intent, ADR-0201). Only the number moves (Q8).
  - A tag change **marks the player's pools due**, so the next build uses the new tags (§14).
- **No floor** (Q7). A 0% For-fun card is still dealt. It only exists when nothing better fits that court hour, and it sinks to the bottom of the deck.
- **Spec note:** with fewer than two named people at the table there is no Social vibe and no row is drawn.

## 5. How a For-fun table is built (brief §2, Q4, Q13, Q22, Q3b)

- **Unchanged, the same as competitive (brief §2.2):**
  - the court hours on sale;
  - free for the **whole** hour inside weekly hours;
  - the 12 candidates considered per hour;
  - one pick per free court per hour;
  - courts, club order, price and share;
  - the book-by;
  - Competitive dealt before For fun within an hour.
- **Unchanged gates (skill's job as a guard, Q13 a):**
  - the pair rule: no block either way, the reliability filter, mutual gender preference;
  - the **level window**: 0.90 for For fun, 0.55 while either player is a Newcomer.

  The window caps how far apart levels may be, which is what keeps a For-fun card from being "very unbalanced".
- **Among the fours that pass, For fun ranks by, in order:**
  1. **Social vibe**, highest first (compared exactly, before rounding);
  2. **new faces**: more pairs at the table who are new faces to each other (below);
  3. **forecast**, evenest first;
  4. **level spread**, smallest first.

  Skill does three jobs: the gate, the sides, and the tie-break. It is never a weight, so the order of the deck always agrees with the number printed on the card.
- **A new face** (Q4 b, Q22) is someone you have **never played a game with** (Friends' existing *Played with*) **and who is not your friend**. It is a builder preference only: it never moves the number. Friends still appear on cards with their FRIEND tag; they just don't win ties.
- **The sides** stay the **evenest arrangement**, as today, and the tiles keep showing levels.
- **Where the For-fun score applies:** everywhere the engine names someone for a For-fun seat:
  - new picks;
  - a seat re-dealt after a No (the up to 3 next best fits);
  - the open seats of a For-fun **Post**, and the poster's list of best fits on Post a game (§13);
  - a For-fun **Rescue**'s best fits (the three left plus the candidate).
- **Competitive building is untouched.**
- **The separation is visible in code:** one proposer with **two scoring policies named per Mode**. The competitive score stays (forecast, then −spread); the For-fun score is the one above.

## 6. The social tags vocabulary (Q10, Q11, Q21)

- **Eight new tags**, each **appended to the end of its group**. That is the one kind of change the vocabulary allows: ids are permanent, and nothing existing moves or retires.

  | Group | Id (proposed) | Label |
  |---|---|---|
  | After the match | `STAYS_FOR_A_COFFEE` | ☕ Stays for a coffee |
  | After the match | `UP_FOR_A_BITE_AFTER` | 🍽️ Up for a bite after |
  | After the match | `KEEPS_IN_TOUCH` | 📲 Keeps in touch |
  | On the court | `HAPPY_TO_SWAP_PARTNERS` | 🔄 Happy to swap partners |
  | On the court | `PATIENT_WITH_BEGINNERS` | 🤲 Patient with beginners |
  | On the court | `HAPPY_TO_SHARE_TIPS` | 💡 Happy to share tips |
  | On the court | `BRINGS_THE_ENERGY` | 🎶 Brings the energy |
  | Why you're here | `NEW_IN_TOWN` | 🧳 New in town |

- **Struck in the session:** 👀 *Sticks around to watch* and 🧘 *Here to unwind*.
- **Rejected on principle:**
  - *Just starting out*: a level claim; the Skill rating says how you hit.
  - *Here for fun*: duplicates Play intent, and a tag is not an intent.
  - *Always on time*: a reliability claim, which Player Score measures.
  - Anything about age, family, job, looks, nationality or language: about the person, not the game. The vocabulary's tripwire test stays as strict as it is.
- **The vocabulary goes from 19 to 27 tags:** After the match 9, On the court 10, Why you're here 8.
- **Bounds: 2 to 8** (was 2–6).
  - **Backend:** the value object's bounds and their test.
  - **App:** the picker's copy becomes *Pick 2 to 8* and *8 tags is the most*, in both onboarding and the You tab.
  - Old events holding up to 6 tags stay valid.
- **Knock-on changes:**
  - **Player record:** shows up to 8 tags (`SOCIAL_TAG_ROW_CAP` 6 → 8).
  - **Same vibe's Vibe %:** gains **99** (7 shared) and **100** (8 shared). 100% is true, because the two players' eight tags would be identical.
  - **The details grid:** can reach 8 rows.
  - **Older installed app versions** must **skip a tag code they don't know**, never crash. The backend sends codes only (ADR-0022).
- **Grid and display order:** the vocabulary's order (group by group), not the order a player picked in (Q10 b). The pick order stays unstored, and every tag counts the same.
- **No nudge to existing players** (Q21 a). The new tags and the cap of 8 simply appear in the picker. A one-time *New tags* notice can be a follow-up if adoption is low.

## 7. The For-fun deck order (Q3 a, Q3b ii)

Each rule only decides between cards that tie on every rule above it:

1. **Owed cards** (a club's cancel that Move by cancel couldn't save), unchanged.
2. **Rescues** (*Seat open · court booked*: an open seat in a **booked** game), ordered **by Social vibe** among themselves. Like Owed cards, these are already-booked games with real people waiting, and they are rare, so pinning them barely dents the falling vibe.
3. **Every other card by Social vibe, highest first.** The deck compares the **number the card shows**, so two cards showing the same % tie and fall to the next rule.
4. **Fewest seats open after your yes.**
5. **Challenge › Picked for you.**
6. **Soonest deadline.**

Notes:
- The *other* kind of Seat open, a full game that **went back to filling** before it was booked, is **not a rescue**. It is ordered like any proposal.
- "The same people only at their best hour" stays; the rules after vibe pick the hour.
- **The competitive deck keeps today's order:** Owed → fewest seats open → Seat open › Challenge › Picked for you → deadline → best forecast.
- **Fill in** (the rescue board) rows stay without a number, as competitive rows have none today.

## 8. Bands — words and colours (Q5, Q20)

One set of thresholds drives both the word and the colour. The forecast's green / amber / red is **not** reused: red would say "bad game", and a borrowed forecast palette blurs the two promises.

| Social vibe | Word | Fill | Number on the dark card | Number on paper |
|---|---|---|---|---|
| 70–100% | **Great vibe** | volt | volt | olive ink |
| 45–69% | **Good vibe** | volt | volt | olive ink |
| 20–44% | **Some common ground** | dimmed volt | dimmed volt | olive ink, dimmed |
| 0–19% | **Fresh mix** | grey | grey | grey |

- The thresholds live in the app's presentation, beside the forecast's (`shared/vocabulary/balancePresentation.ts` is the model). The backend sends only the %. They can be tuned once real numbers exist.
- The design system names the exact tokens for "dimmed volt" and the two greys (on dark and on paper).
- The bar always goes from 0 to 100: the % and the fill are the same value.

## 9. Design-system exceptions (Q20)

These are recorded in the ADR and in `frontend_player/docs/design-system.md`:
- **A new pale volt token** for a shared row's band in the grid, against the design system's "volt has no soft and needs none".
- **Olive ink** (`gameCellDim #546A36`, "the olive") for the grid's dots and the big % on paper.
- **A grey dot and grey text** for a row only you have.
- **A new Social vibe component** (mock 2): the % beside a full-width bar, with the label *Social vibe* inside the bar in italics. The label sits on the track and keeps contrast whether the fill is short or long.

## 10. The For-fun deck card (brief §4.1, Q14)

- **The Social vibe row** (mock 2) **takes the forecast row's place**: below the tiles and the *A + B vs C + D* line, above the week strip. The % is in the forecast's figure size and colour-coded by band (§8).
- **No forecast is drawn on a For-fun card.**
- Everything else is unchanged:
  - the **ribbon** in all its states (*Picked for you*, *{name} challenged you*, *Seat open · court booked*, the countdown). Mock 1 just doesn't show one;
  - the tiles with their FRIEND and IN tags and levels;
  - the vs line;
  - the overlap strip and its grade title;
  - the court block.
- **The competitive deck card is unchanged.**
- **Spoken label:** *Social vibe, 67 percent, Good vibe*, with the number and the word for that card.

## 11. The game details screen — both kinds (brief §4.2, Q15, Q16)

- **Order, top to bottom:**
  1. the kind's **top card**: Balance forecast (§12) or Social vibe (§13);
  2. the **dark game card**: status tag, tiles, vs line, and the facts (WHERE / DAY / TIME / YOUR SHARE), then **the offline note** if any, then **the action row in the card's own foot**;
  3. **Who is free** (the overlap grid), still shown once two are In, **below** the dark card. The mocks end before it, but the brief doesn't remove it.
- **Every action the screen shows today moves into the dark card's foot:**
  - the answer pair **side by side**, as in mocks 3–5: *Not this time* on the left (secondary) and the yes on the right (primary);
  - or **Withdraw / Leave the game / Confirm payment**, when that is the state's action.
- **The yes button's wording is unchanged** and verified as already defined:
  - *I'm in*, or *Pay {share}* when your yes completes the game (`courtOfDetails` → `BOOK_IT_NOW`);
  - *Booking…* while it books, a spinner while the yes is pending, and disabled while another booking is counting down.
  - **The mocks' *I'm in · books it · 27 zł* is not used.**
- **The header is unchanged** (Q16, a named exception to the mocks):
  - stacked faces, the comma-joined names, and the subline *Padel* / *Padel · For fun*;
  - the count stays only in the status tag (*Filling · 2 of 4 in*);
  - the mocks' *Padel · 3 of 4 in* is not used. It would say the count twice and drop the *For fun* that tells you which deck you came from.

## 12. Competitive details — the Balance forecast card (brief §4.2.1, Q17)

- **The full block that booked games already draw** (`ForecastBlock`):
  - the side levels with *gap* and the signed gap;
  - the bar with the sides' names;
  - the % with its word;
  - the sentence *A counted game — a confirmed score moves everybody's level.*;
  - **If you win / If you lose** for you.
- `ForecastBlock` and its `StakeTiles` **move to `shared/ui`** so the proposals and games features both draw them.
- **The stakes:**
  - computed **for you**, for **your version's evenest sides**, by **the same function** as a booked game's `at_stake` (`matchmaking/infrastructure/games_court_pairing.py:110-119`);
  - shown as **two tiles or none**, as on a booked game;
  - on the **details screen only**, never on the deck card;
  - this works for doubles and singles, because the version always names everybody.
- The deck card's forecast row is unchanged.

## 13. For-fun details — the Social vibe card (brief §4.2.2, Q6, Q10, Q12)

Mock 6 leads.
- **Top:** the eyebrow *SOCIAL VIBE*, then the **big %** (olive ink on paper, coloured by band) beside its **word** (§8), then **the same fill bar** as on the card, full width below them as in mock 6.
  - The brief's "next to the word" yields to mock 6's layout.
  - The number is the card's number, so the % you swiped on is the % you're looking at.
- **Columns:** **You first**, then the other players in tile order (Q6, mock 6 over mocks 4/5).
  - Each column shows a round photo and the nickname below it, shortened with an ellipsis when long; you are *You*.
  - There are 4 columns for doubles and 2 for singles: everyone named on the version, In or not.
- **Rows: your tags only**, one per row, in the **vocabulary's order**, each with its **emoji** and label. No other player's tag that you don't carry appears.
- **Dots:**
  - a dot under every player who carries that tag;
  - **your column has a dot on every row**;
  - 💘 is drawn like any other row.
- **Row look:**
  - a row **at least one other player shares**: pale volt band, dark text, olive dots;
  - a row **only you have**: grey text and a grey dot.
- **How to read it:** the big number says how much the **whole table** shares, counting everyone's tags. The grid says **who shares yours**.
- **Live:** your rows follow your current tags (§4).
- **The grid has no taps of its own.**
- **Spoken:** each row is read as *Stays for a drink: you, Kuba*, naming the tag and who carries it.
- **The dark game card below is unchanged** apart from the action row moving into it (§11).

## 14. One kind, the same information everywhere (Q18)

**Compact surfaces** (cards, rows) show the kind's headline number. **Full surfaces** (screens) show the kind's full card.

| Surface | Competitive | For fun |
|---|---|---|
| Deck card | forecast % + bar | **Social vibe % + bar** |
| Game details (`GameDetailsScreen`) | Balance forecast card + stakes (§12) | **Social vibe card + grid** (§13) |
| Booked game screen (`BookedGameScreen` → `GameForecast`) | forecast card + stakes (already) | **Social vibe card + grid**, in place of *A friendly — nothing moves.* |
| The game at the court (games' `GameScreen`, the court's pairing) | forecast card + stakes (already) | **Social vibe card + grid** |
| Friends card (the sender builds a friends game) | forecast % | **Social vibe %**; flipping the kind switch flips the number |
| Post a game's best fits (*2,75 · 93*) | level · % even | level · **Social vibe for the two of you**, and a For-fun post's fits are **ranked** by it (§5) |
| Fill in rows | no number | no number |
| The sign-in screen's illustrative mini card (`MiniGameCard`) | unchanged | unchanged |

- **The Social vibe card is shown wherever, and to whoever, the forecast was shown before**, and no wider. For example, a booked game's follows `shows_forecast`.
- **A played For-fun game's vibe stays live:** it moves if someone later edits their tags, because nothing is stored (§4).

## 15. Backend — data, ports and contract (Q19, Q8)

- **The formula is one pure function in the Match Fit engine** (`app/engines/matchfit`), next to the forecast and the overlap. It takes the table's tag sets and returns the %.
  - **Which tags don't count** (💘) is a domain constant **beside the vocabulary** in `player_profile/domain/social_tags.py`.
  - **No ruleset release:** no ruleset number moves. The bands are app presentation (§8).
- **No new table:**
  - **Proposals** declares its own port in its own words, *these players' tags*: a batch version of today's `TagsInCommon`. Its adapter reads Discovery's existing `discovery_player_tags` (one row per player and tag, already held equal to a rebuild) in one query, instead of replaying every profile stream on each deck read.
  - **Games** declares its own tags port for the pairing read.
  - **Each new port gets its row in a `tests/demands/` register.**
  - **Proposals also reads *played with***, the new-faces input, through a port of its own.
  - The deck read's cost is held to a number with the `statements` fixture (#812). If it is too costly, a projection is argued in the ADR, not added silently.
- **`SocialTagsChanged` joins the events that mark a player's pools due**, alongside `WeeklyHoursSet`, `PlayIntentDeclared` and the rest.
- **Contract changes:** prefer additive; this is a public API change, called out in the plan.
  - **Deck card** (`DeckCardSchema`):
    - gains `vibe{pct}` on For fun, null on Competitive;
    - `forecast`, already nullable, becomes **null on For fun**.
  - **Proposal details** (`ProposalDetailsResponse`):
    - For fun gains `vibe{pct, rows[{tag, carried_by[player_id]}]}`, with rows in the reader's tag order;
    - Competitive gains `forecast{levels per side, gap, pct, provisional}` and `at_stake{win_delta, loss_delta}`.
  - **Friends card** (`FriendsCardResponse`) and **Post a game's fits** (`SlotFitSchema`) gain `vibe`. Their nullable `forecast` becomes null on For fun.
  - **Games pairing** (`GET /games/{id}/pairing`) gains `vibe` on For fun. Its `forecast` is **required** today, so it **keeps being sent for older installed apps**, and the new app ignores it on a For-fun game.
  - **Tags travel as codes.** The app owns labels, emoji, words, colours and bands.
- **Seeds:** the dev seed gives its seeded players tags spread so that a For-fun deck shows all four bands, through the use cases and never SQL.

## 16. Calls made without asking (confirmed in the session)

1. **One formula, two callers.** The Social vibe formula is one pure function in the Match Fit engine, called by proposals and games. The list of tags that don't count sits beside the vocabulary.
2. **No new ruleset release.** The band thresholds are app presentation.
3. **Same audience as the forecast.** The vibe card is shown wherever, and to whoever, the forecast was before, and no wider.
4. **Seeds spread tags.** Seeded players' tags are spread so a For-fun deck shows all four bands.
5. **Spoken labels.** *Social vibe, 67 percent, Good vibe*; each grid row as *Stays for a drink: you, Kuba*.
6. **A static grid.** The grid has no taps of its own.

## 17. Delivery (Q9 a)

- **This session wrote only this file.** Nothing was written to the repo, and no issue was opened.
- **The ADR lives in this repo's `docs/adr/`**, written by a **first root-docs ticket**, as #811 did for Home with ADR-0205. That ticket also:
  - copies the brief, this log and the 7 mocks into `docs/specs/for-fun/`, with an index of the mocks' original names;
  - amends `CONTEXT.md` and the specs the ADR narrows (§18).
- **Not on `feat/RKTA-09_home_refactor`.** The repo was on that branch during this session; the For-fun work gets its own branch.
- The spec and the tickets come from `to-spec` / `to-tickets`, and the build from `implement`.

## 18. Docs to amend

- `CONTEXT.md`: Social tag, **Social vibe** (new), Vibe %, Mode, Match Fit engine, Group deck, Rescue (§3).
- `docs/adr/0204-…` §6: narrowed by the new ADR, with a note at the section.
- `docs/specs/home-rows/the-mechanics.md` §8.2, §8.7 · `docs/specs/you/the-you-screen.md` §3.11.
- `docs/specs/games-and-fill-in/the-mechanics.md` and `the-screens.md`: For-fun building, deck order, card and details.
- `docs/specs/matchmaking/the-words.md`:
  - the band words;
  - *Social vibe*;
  - the 8 new tag labels;
  - *Pick 2 to 8* and *8 tags is the most*.
- `docs/specs/player-record/…`: up to 8 tags.
- `frontend_player/docs/design-system.md`: §9's exceptions, the Social vibe component, and the card and details spec (7.22).
- `frontend_player/docs/features/proposals.md`, `games.md`, `player_profile.md`, `discovery.md` (99/100).
- `backend/.claude/rules/proposals.md`, `games.md`, `matchmaking.md`, `player-profile-and-photos.md`, `demands.md`.
- `backend/app/modules/player_profile/domain/social_tags.py`: the docstring records the eight additions, like the nineteenth.

## 19. Out of scope, or rejected

- **Rejected:**
  - storing the order a player picked their tags in (Q10);
  - partial credit for related tags (Q11);
  - a forecast floor or a skill weight for For fun (Q13);
  - pinning nothing above vibe, i.e. rescues ordered by vibe like any card (Q3b i).
- **Follow-up if wanted:** a one-time *New tags* nudge (Q21 b).
- **Unchanged:** competitive building and the competitive deck order; the sign-in screen's mini card; Fill in rows.

---

## Mock index

| # | File | Used in |
|---|---|---|
| 1 | `1_for_fun_card.png` | §10 For-fun deck card |
| 2 | `2_social_vibe_component.png` | §9, §10 the Social vibe row |
| 3 | `3_competitive_game_card_details1.png` | §11, §12 competitive details (top) |
| 4 | `3_competitive_game_card_details2.png` | §11 competitive details (foot, buttons in the card) |
| 5 | `4_forfun_game_details1.png` | §11, §13 For-fun details (top) |
| 6 | `5_forfun_game_details2.png` | §11 For-fun details (foot) |
| 7 | `6_social_vibe_card_details.png` | §13 the Social vibe card. **It leads over mocks 4/5 on column order and emoji.** |

## Question index

| Q | Decision | § |
|---|---|---|
| Q1 | New ADR narrowing ADR-0204 §6; the term **Social vibe** | 3 |
| Q2 | Formula (c), *shared by the others* | 4 |
| Q3 | For-fun deck: Social vibe above seats open | 7 |
| Q3b | Rescues pinned under Owed cards, by vibe | 7 |
| Q4 | New faces is a builder tie-break, never the number | 5 |
| Q5 | Four bands: Great · Good · Some common ground · Fresh mix | 8 |
| Q6 | The grid follows mock 6: You first, emoji | 13 |
| Q7 | No floor | 4 |
| Q8 | Live from current tags; a tag edit pulls nobody off a card | 4 |
| Q9 | This log only; the ADR by a first root-docs ticket | 17 |
| Q10 | The vocabulary's order; pick order not stored | 6 |
| Q11 | Exact tags only; 8 new tags; 2–8 | 4, 6 |
| Q12 | 💘 shown in the grid, ignored in building and the % | 4 |
| Q13 | Skill is a guard: window, sides, tie-break | 5 |
| Q14 | No forecast anywhere on For fun | 10 |
| Q15 | Actions in the dark card's foot; *Who is free* stays below | 11 |
| Q16 | Header unchanged (exception to the mocks) | 11 |
| Q17 | Stakes on competitive details, from the booked game's function | 12 |
| Q18 | Same per-kind information on every surface | 14 |
| Q19 | No new table; ports; contract | 15 |
| Q20 | Design-system exceptions | 9 |
| Q21 | No nudge; cap of 8 | 6 |
| Q22 | New face = never played with and not a friend | 5 |
