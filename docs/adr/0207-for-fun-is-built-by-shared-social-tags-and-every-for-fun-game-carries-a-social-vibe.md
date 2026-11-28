# ADR-0207 — For fun is built by shared social tags, and every For-fun game carries a Social vibe

- **Status:** Accepted
- **Date:** 2026-11-22
- **Narrows [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
  §6's *"Tags now order one row and score nothing else"***:
  - social tags now also **build and rank For-fun proposals** (§1), and give every For-fun game its
    **Social vibe** (§2);
  - they **still never touch a competitive card, a forecast or a level**, and *a tag is not an
    intent* stands;
  - Same vibe's rules all stand. Its **Vibe %** gains **99** and **100**, because a player may now
    hold 7 or 8 tags (§7).
- **Narrows, in the same breath, the two specs that say a tag scores nothing**:
  - the You spec's **§3.11**, *a tag is shown, never scored*, and its 2026-11-14 amendment's *no
    proposal, card, forecast or level reads one*
    ([`the-you-screen.md`](../specs/you/the-you-screen.md#311-tags));
  - the home-rows mechanics' **§8.2**, *six is the most*, with its table stopping at 98%, and
    **§8.7**, *tags … score nothing else*
    ([`the-mechanics.md`](../specs/home-rows/the-mechanics.md#8-same-vibe-players)).

  The tickets that ship each part amend them in place (§12).
- **Amends [ADR-0089](0089-player-profile-context-event-sourced.md)'s *2–6 tags drawn from the live
  vocabulary*.** A player holds **2 to 8** of **27** tags, still re-validated on every write (§7).
- **Narrows what [ADR-0161](0161-the-game-screen-draws-its-courts-pairing.md)'s game screen draws for
  a friendly.** A For-fun game draws the **Social vibe card** where it drew the forecast with *A
  friendly — nothing moves.* The pairing read stands, and still sends the forecast (§5, §11).
- **Names four exceptions to the locked design system**
  ([ADR-0012](0012-player-app-design-system.md)), because the mocks lead (§9).
- **Leaves standing:**
  - **competitive building and the competitive deck order**, apart from the details screen's top
    card and the moved buttons (§6);
  - **availability and court assignment**, for both kinds:
    - the court hours on sale;
    - free for the whole hour;
    - the candidates considered per hour (the 12 holding the fewest cards);
    - one pick per free court per hour;
    - courts, the club order, the price and share, and the book-by;
    - Competitive dealt before For fun within an hour;
  - **the pair rule and its level windows**: 0.55 for Competitive, 0.90 for For fun, and 0.55 around
    a **Newcomer** ([ADR-0113](0113-newness-changes-the-gate-never-the-weights.md));
  - **the Forecast and its one function**. It still arranges every card's sides, and it is still the
    only thing that does;
  - **a For-fun result never moves a level**, and asks nothing;
  - **[ADR-0201](0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)**:
    a changed Play intent leaves the cards you haven't answered. A changed tag does not (§2);
  - **tags travel as codes**
    ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md)). The app owns every label, emoji,
    word, colour and band;
  - **the ruleset**: no number moves, and no release is made (§11);
  - **Fill in's rows**, which carry no number on either kind, and the sign-in screen's illustrative
    mini card.
- **Does not decide:**
  - partial credit between related tags;
  - a skill weight or a forecast floor for For fun;
  - storing the order a player picked their tags in;
  - a one-time *New tags* nudge to existing players, a follow-up if adoption is low;
  - stakes on the deck card;
  - a stored projection of everyone's tags for the deck. If the read's statement count can't be held,
    it is argued in an ADR, not added silently (§11).
- **Settles PRD [#827](https://github.com/Rakieta02/Rakieta/issues/827).** It was decided in the
  For-fun refactor grilling on 2026-11-22 (Q1–Q22 and Q3b there), from the product owner's brief
  *For-Fun Game Cards Refactor* and its 7 mocks, and written by
  [#828](https://github.com/Rakieta02/Rakieta/issues/828).
  - **Specified by** [`docs/specs/for-fun/`](../specs/for-fun/README.md): the brief, the grilling's
    decision log and the mocks. Where the log and this record or PRD #827 disagree, this record and
    PRD #827 win.
  - **The mocks lead on design.** Where an ADR, a spec or the locked design system disagrees with a
    mock on a look, the document changes, by name. Three named exceptions run the other way (§10).
    **The mocks' data is only data**: no rule is read off a mock's names, levels, tags, percentages,
    prices or button text.
  - **Mocks are cited by the folder's numbers, 1 to 7.** The decision log's prose and PRD #827 count
    by the files' original prefixes, so their *mock 6* is this folder's **7** and their *mocks 4/5*
    are **5 and 6**. The folder's README translates them.
  - **Built by** the backend's [#829](https://github.com/Rakieta02/Rakieta/issues/829) (27 tags, 2–8),
    [#830](https://github.com/Rakieta02/Rakieta/issues/830) (the vibe on a card and the For-fun deck
    order), [#831](https://github.com/Rakieta02/Rakieta/issues/831) (building by shared tags),
    [#832](https://github.com/Rakieta02/Rakieta/issues/832) (a tag edit reaches the next build, and
    the seed), [#833](https://github.com/Rakieta02/Rakieta/issues/833) (the details read by kind),
    [#834](https://github.com/Rakieta02/Rakieta/issues/834) (the Friends card and Post a game's fits)
    and [#835](https://github.com/Rakieta02/Rakieta/issues/835) (a booked game's pairing); and the
    player app's [#836](https://github.com/Rakieta02/Rakieta/issues/836)–[#842](https://github.com/Rakieta02/Rakieta/issues/842).
    Walked by [#843](https://github.com/Rakieta02/Rakieta/issues/843).

## Context

**The For-fun deck promises good company, but it is built like the competitive one.** Ola is new in
town. She picked *Stays for a drink*, *Laughs off mistakes* and *Here to meet players* in
onboarding, and she set her padel intent to For fun because she wants friendlies, not a counted
score. The engine builds her For-fun cards with exactly the algorithm that builds competitive cards:
the evenest four by forecast, then the smallest level spread, inside a looser level window. **Her
tags are never read when a game is built**, so the people on her card are a skill match who may
share nothing she said about herself.

**The For-fun card says the wrong thing.** It shows the balance forecast, a percentage about who
would win, on a game where nothing is at stake and no level moves. Two decks with two different
promises draw the same headline number, which blurs the For-fun promise and makes the competitive
number less credible. Opening the details shows the forecast again, and nothing says which of
Ola's tags anybody at the table shares.

**On a competitive card, Piotr can't see what he is betting before he bets it.** The details screen
shows a bar and a percentage, but not the sides' levels, the gap, or what he stands to win or lose
in level. All of that is already drawn for a booked game, after the decision it should have
informed. The answer buttons sit at the bottom of the screen, under the forecast and *Who is free*,
away from the game they answer.

**The same game reads differently on different screens.** A booked For-fun game still shows a
forecast with *A friendly — nothing moves.* The Friends card and Post a game's best fits show a
forecast for a friendly too.

**The tags are too few to describe a social profile.** There are 19, a player picks at most 6, and
obvious signals are missing: a coffee rather than a drink, new in town, patient with beginners,
happy to swap partners.

**What the investigation found** (the brief's §1.1, the decision log's §2, on this branch's base):

- **Competitive and For fun are one algorithm.** The kind changes four things only:
  - who is dealt it: your Play intent must want the kind;
  - the level window's tolerance, 0.55 against 0.90, with 0.55 around a Newcomer. The fit adapter
    says so in so many words: *the kinds differ only in the level window's tolerance*;
  - the dealing order within an hour, Competitive first;
  - what happens after: a For-fun result never moves a level and has no stakes.
- **Both kinds choose a four by the same score**, best forecast then smallest spread
  (`proposals/domain/proposer.py`'s `_score`). `Member` carries no tag, and the old tag matrix went
  with #580. **No tag is read anywhere in building.**
- **The player app draws both kinds with one `GameCard`**, which has no branch on kind. A For-fun
  card and its details both show the forecast.
- **What is stored, and what is worked out:** a card's people are stored, in `ProposalMade` /
  `VersionDealt` and `proposal_people`. The sides, the forecast, the overlap and the deck order are
  worked out on every read.
- **What rebuilds a pool** is listed in `mark_due_for_proposing.py`, and `SocialTagsChanged` is not
  on the list.
- **Tags:** 19 in 3 groups, 2–6 a player, global rather than per sport, re-sorted into the
  vocabulary's order on every write, and already shown to other players on the record.
  **Discovery** already keeps one row per player and tag, `discovery_player_tags`, held equal to a
  rebuild (ADR-0204 §10).
- **The full forecast card and the stakes exist for booked games only**: the app's `ForecastBlock`
  and `StakeTiles`, fed by `GET /games/{id}/pairing`'s `at_stake`.
- **The yes button's words are already defined**: *I'm in*, *Pay {share}* when your yes completes the
  game, and *Booking…* while it books.
- **Scale:** at most 12 candidates per court hour, so at most 495 fours; up to 3 versions and 3 next
  best fits per seat; cards dealt up to 14 days ahead.

**The alternatives:**

- **Weigh tags and skill together**, as the brief first sketched. A weighted blend makes the deck's
  order disagree with the number printed on the card, and a player can't read either. Skill becomes
  a guard instead: the window, the sides and a tie-break (Q13).
- **Reuse Same vibe's Vibe %.** It is pairwise, 1 − ½ⁿ for two people, and a table has up to six
  pairs. The table needs its own figure and its own name, so the two are named apart (Q1).
- **A table score that asks only whether each pair shares something.** It reads two pairs who share
  everything with each other and nothing across the table as perfect. The chosen formula reads
  them as 33% (Q2).
- **Partial credit between related tags**, a drink and a coffee. Every point in the % would no longer
  be a dot a player can see in the grid, and somebody would have to own a table of relations (Q11).
- **Count 💘 *Open to meet someone* like any tag.** The For-fun deck would seat people together
  because of that motive. It is shown and never counted (Q12).
- **Store the vibe when a card is dealt.** It would go stale the moment anybody edits a tag, and the
  backend's rule is *derived, never stored* (Q8).
- **Pull a player off dealt cards when their tags change**, as ADR-0201 does for a changed intent.
  An intent decides whether you want the kind at all; a tag only moves the number (Q8).
- **A floor under which no For-fun card is dealt.** In a small group, a possible game beats no game
  (Q7).
- **Order rescues by vibe with every other card** (Q3b i). A rescue is a booked court with three
  people waiting, and rescues are rare, so pinning them under Owed cards barely dents the falling
  vibe.
- **Colour the vibe green, amber and red, as the forecast.** Red would say *bad game*, and nothing at
  a friendly is bad. A borrowed palette also blurs the two promises (Q5).
- **A new table for everyone's tags.** Discovery's tag rows already hold them, one row per player and
  tag. A batched port reads them, and a test holds the read's cost (Q19).

## Decision

### 1. Social tags build and rank For-fun tables; skill is a guard

**Mode now picks a scoring policy as well as the level window's tolerance.** The proposer holds **two
policies, named per Mode**, so the separation is visible in the code.

- **Competitive keeps today's score:** the best forecast, then the smallest level spread.
- **For fun** ranks the fours that pass the unchanged gates by:
  1. **Social vibe** (§2), highest first, compared exactly, before rounding;
  2. **new faces** (§3): the number of pairs at the table who are new faces to each other, most
     first;
  3. **the forecast**, evenest first;
  4. **the level spread**, smallest first.
- **Skill is a guard, never a weight.** It does three jobs:
  - the **level window**, which is what stops a For-fun game from being very unbalanced;
  - the **sides**, which stay the evenest arrangement for both kinds;
  - the **tie-break**, third and fourth above.

  So the deck's order always agrees with the number printed on the card.
- **Where the For-fun policy applies:** wherever the engine names somebody for a For-fun seat:
  - new picks;
  - the next best fits after a No;
  - a For-fun **Post**'s open seats, and the poster's list of best fits on Post a game;
  - a For-fun **Rescue**'s best fits, read against the three left plus the candidate.
- **Nothing in availability or court assignment changes**, and nothing in the gates (the header's
  *Leaves standing*).
- **💘 builds nothing** (§2).
- **No floor** (Q7). A 0% For-fun card is still dealt. It exists only when nothing better fits that
  court hour, and it sinks to the bottom of the deck.

### 2. The Social vibe

**Social vibe** is how much of what everyone at a For-fun table carries is shared there. It is a
plain fact about the table, the same number for each of them, and it reads as one sentence: *on
average, each tag at this table is carried by that share of the other players* (Q2, option (c),
*shared by the others*).

**The table** is everyone named on the reader's version of the card: the people In, the reader, and
the names dealt for the open seats. An empty seat isn't part of it.

```
n   = people at the table (n ≥ 2)
Tᵢ  = the counted tags player i carries
c_t = how many people at the table carry tag t
social_vibe = round_half_up( 100 × Σᵢ Σ_{t∈Tᵢ} (c_t − 1)/(n − 1)  ÷  Σᵢ |Tᵢ| )
```

- **Rounded half up**, `floor(100·x + 0.5)`, as the Vibe % is.
- **Sanity values:**

  | Table | Social vibe |
  | --- | --- |
  | All four carry exactly the same tags | **100** |
  | A and B carry {x, y, z}; C and D carry {p, q, r}: two pairs who share everything with each other and nothing across | **33** |
  | A {x, y, z}, B {x, y}, C {x, w}, D {v, u}: (1 + 1 + ⅔ + 0) ÷ 9 carryings | **30** |

- **In singles it reduces to the plain overlap of the two players**: twice the tags they share, over
  all the tags the two carry.
- **With fewer than two named people there is no Social vibe**, and nothing is drawn.
- **Every player carries at least one counted tag**, because a player holds at least two and only
  one tag is uncounted. So the sum below the line is never zero at a real table.

**Which tags count** (Q11, Q12):

- **Only identical tags**, each weighing the same. Related tags get no partial credit.
- **💘 *Open to meet someone* doesn't count**, in the formula or in building. It is still drawn in
  the grid like any other tag (§6). The vocabulary's own docstring places it *at the edge* of its
  rule, and counting it would seat people together because of that motive.
- **Which tags don't count is a domain constant beside the vocabulary**, in the Player profile's
  `social_tags.py`.

**Live, never stored** (Q8):

- the Social vibe is worked out **on every read** from everyone's **current** tags, on proposals and
  on booked and played games alike, so a played game's vibe moves when somebody later edits a tag;
- **a tag change pulls nobody off a card already dealt**. Only the number moves;
- **the Player profile's `SocialTagsChanged` joins the events that mark a player's pools due**,
  beside `WeeklyHoursSet` and `PlayIntentDeclared`, so the next build reads the new tags.

**Two vibe numbers, two names.** Same vibe's **Vibe %** (two people, 1 − ½ⁿ) and a singles **Social
vibe** can differ for the same two players. They are different measures, named apart on purpose.

### 3. A new face

**A new face is a pair who have never played a game together**, by Friends' *Played with*, **and are
not friends** (Q4, Q22).

- It is **a builder preference only**, second after the vibe. It never moves the number.
- Friends still appear on For-fun cards, with their FRIEND tag. They lose a tie to a new face, so For
  fun widens a player's circle instead of repeating it.

### 4. The For-fun deck order

Each rule decides only between cards that tie on every rule above it (Q3, Q3b):

1. **Owed cards**, unchanged;
2. **Rescues**, *Seat open · court booked*: an open seat in a **booked** game, ordered among
   themselves **by Social vibe**;
3. **every other card by the Social vibe the card shows**, highest first. The shown number is
   rounded, so two cards that show the same % tie;
4. **the fewest seats open after your yes**;
5. **Challenge › Picked for you**;
6. **the soonest deadline**.

- **A full game that went back to filling** before it was booked is *not* a rescue. It is ordered
  like any proposal, by its vibe.
- **"The same people only at their best hour" stays.** The rules after the vibe pick the hour.
- **The competitive deck keeps today's order**: Owed, the fewest seats open, Seat open › Challenge ›
  Picked for you, the deadline, the best forecast.

### 5. For fun never shows a forecast; competitive never shows a vibe

**No forecast is served or drawn for a For-fun proposal** (Q14). The forecast is still computed, to
arrange the sides, and isn't shown. **A compact surface shows the kind's headline number; a full
surface shows the kind's full card** (Q18):

| Surface | Competitive | For fun |
| --- | --- | --- |
| The deck card | the forecast's % and bar, unchanged | **the Social vibe row** (mock 2) in the forecast row's place |
| The game details | the **Balance forecast card** with the stakes (§6) | the **Social vibe card** with its grid (§6) |
| The booked game screen | the forecast card and the stakes, as today | the **Social vibe card**, where *A friendly — nothing moves.* stood |
| The game at the court | the forecast card and the stakes, as today | the **Social vibe card** |
| The Friends card | the forecast's % | **the Social vibe's %**. Flipping the kind switch flips the number |
| Post a game's best fits | level · % even, as today | level · **the Social vibe of the poster and that player**, and a For-fun post's fits are **ranked** by it |
| Fill in's rows | no number | no number |
| The sign-in screen's mini card | unchanged | unchanged |

- **The deck card.** The vibe row sits below the tiles and the *A + B vs C + D* line, above the week
  strip, its % at the forecast's figure size. Everything else stays: the ribbon in all its states
  (mock 1 simply draws none), the tiles with FRIEND, IN and levels, the vs line, the overlap strip
  and its grade, the court block. **The competitive card is unchanged.**
- **The vibe card is shown wherever, and to whoever, the forecast was shown before, and no wider.** A
  booked game's follows its `shows_forecast`.

### 6. The details screen splits by kind

**Top to bottom, on both kinds** (Q15):

1. **the kind's top card**;
2. **the dark game card**: the status tag, the tiles, the vs line, the facts (WHERE, DAY, TIME, YOUR
   SHARE), the offline note if any, then **the action row, in the card's own foot**;
3. ***Who is free***, still shown once two are In, **below** the card.

**The action row** holds every action the screen shows today: *Not this time* (secondary, left) and
the yes (primary, right) **side by side**, or **Withdraw**, **Leave the game** or **Confirm payment**
when that is the state's action. The yes keeps its words, its spinner and its hold (§10).

**Competitive opens on the Balance forecast card** (Q17), the block a booked game already draws:

- each side's level, *gap* and the signed gap;
- the bar with the sides' names;
- the % and its word;
- *A counted game — a confirmed score moves everybody's level.*;
- **If you win / If you lose**, for the reader:
  - computed **by the same function as a booked game's `at_stake`**, on the reader's version's
    evenest sides, so the stakes seen are the stakes that apply once booked;
  - **two tiles or none**, as on a booked game;
  - for doubles and singles alike, because a version always names everybody;
  - **on the details only**, never on the deck card.

The block moves to the app's shared UI so the proposals and games features both draw it.

**For fun opens on the Social vibe card** (Q6, Q10, Q12). Mock 7 leads.

- **The top:** the eyebrow *SOCIAL VIBE*; the big %, coloured by band, beside its word; and the same
  bar as the card's, **full width below them**. It is the card's number, so the % swiped on is the %
  looked at.
- **The columns:** **you first**, then the others in tile order, as round photos with the nickname
  below, shortened with an ellipsis; you are *You*. Everyone named on the version, In or not: four
  columns for doubles, two for singles.
- **The rows: your tags only**, one each, in **the vocabulary's order**, each with its emoji and
  label. None of the others' tags that you don't carry appears. A row may be 💘, drawn like any
  other.
- **The dots:** a dot under every player who carries that tag, so your column has a dot on every row.
- **The look:**
  - a row **at least one other player shares**: a pale volt band, dark text and olive dots;
  - a row **only you have**: grey text and a grey dot.
- **How it reads:** the big number says how much the **whole table** shares, counting everyone's
  tags; the grid says **who shares yours**.
- **It is static**: the grid has no taps of its own. It is live: your rows follow your current tags.
- **Spoken:** each row as *{tag}: you, {names}*, e.g. *Stays for a drink: you, Kuba*.

**The same card is drawn on the booked game screen and at the court** (§5).

### 7. The vocabulary grows to 27 tags, and a player picks 2 to 8

**Eight tags are appended**, each at the end of its group: the one change the vocabulary allows. Ids
are permanent, and nothing existing moves or retires (Q11).

| Group | Id | Label |
| --- | --- | --- |
| After the match | `STAYS_FOR_A_COFFEE` | ☕ Stays for a coffee |
| After the match | `UP_FOR_A_BITE_AFTER` | 🍽️ Up for a bite after |
| After the match | `KEEPS_IN_TOUCH` | 📲 Keeps in touch |
| On the court | `HAPPY_TO_SWAP_PARTNERS` | 🔄 Happy to swap partners |
| On the court | `PATIENT_WITH_BEGINNERS` | 🤲 Patient with beginners |
| On the court | `HAPPY_TO_SHARE_TIPS` | 💡 Happy to share tips |
| On the court | `BRINGS_THE_ENERGY` | 🎶 Brings the energy |
| Why you're here | `NEW_IN_TOWN` | 🧳 New in town |

- **27 in all:** After the match 9, On the court 10, Why you're here 8.
- **The vocabulary's tripwire against tags about the person is not widened.** Rejected on principle:
  a level claim (*Just starting out*: the Skill rating says how you hit), an intent (*Here for fun*:
  a tag is not an intent), a reliability claim (*Always on time*: Player Score measures it), and
  anything about age, family, job, looks, nationality or language. Struck in the session: *Sticks
  around to watch* and *Here to unwind*.
- **The bounds go from 2–6 to 2–8**, checked on every write as today. Old events holding up to 6 stay
  valid. The picker reads *Pick 2 to 8* and *8 tags is the most*, in onboarding and in the You tab.
- **The order a player picked their tags in stays unstored** (Q10). Every list of tags, the grid's
  included, is in the vocabulary's order.
- **No nudge** (Q21). The new tags and the cap of 8 simply appear in the picker.
- **What follows from 8:**
  - the player record shows up to 8 tags;
  - Same vibe's **Vibe %** gains **99** (7 shared) and **100** (8 shared). 100% is true: the two
    players' eight tags would be identical;
  - the details grid can reach 8 rows;
  - **an app that doesn't know a tag code skips it, and never crashes.** The backend sends codes only,
    so that is the app's job.

### 8. The bands: one word and one colour per range

One set of thresholds drives both the word and the colour, from one hue family (Q5, Q20). **The
forecast's green / amber / red is not reused.**

| Social vibe | Word | Fill | The number on the dark card | The number on paper |
| --- | --- | --- | --- | --- |
| 70–100% | **Great vibe** | volt | volt | olive ink |
| 45–69% | **Good vibe** | volt | volt | olive ink |
| 20–44% | **Some common ground** | dimmed volt | dimmed volt | olive ink, dimmed |
| 0–19% | **Fresh mix** | grey | grey | grey |

- **The thresholds are the app's presentation**, beside the forecast's bands. The backend sends only
  the %. They can be tuned once real numbers exist, with no ruleset release.
- **The bar always runs from 0 to 100**: the % and the fill are one value.
- The design system names the exact tokens for *dimmed volt* and the two greys, on dark and on paper.
- **Spoken:** the vibe row is read as *Social vibe, {n} percent, {word}*.

### 9. The design system's named exceptions

The design system is locked ([ADR-0012](0012-player-app-design-system.md)). The mocks lead, so where
they break a rule, the system changes to match. Each change is made with its theme value, its rule,
its audit and a Part 16 row, in the player ticket that first needs it:

1. **A pale volt token**, for a shared row's band in the grid, against *volt has no soft and needs
   none*.
2. **Olive ink**, today's `gameCellDim` (*the olive*), for the grid's dots and the big % on paper.
3. **A grey dot and grey text** for a row only you have.
4. **A new Social vibe component** (mock 2): the % beside a full-width 0–100 bar with *Social vibe*
   inside it in italics, on the track, keeping its contrast whether the fill is short or long. It is
   the deck card's and the Friends card's row and Post a game's figure, and the Social vibe card
   (mock 7) is built from it and the three above.

### 10. The named exceptions to the mocks

The mocks lead on design, and three exceptions run the other way:

1. **The yes button's words are unchanged** (Q15). *I'm in*, *Pay {share}* when your yes completes
   the game, *Booking…* while it books, a spinner while the yes is pending, and held while another
   booking counts down. **The mocks' *I'm in · books it · 27 zł* is not used.**
2. **The details header is unchanged** (Q16): the stacked faces, the comma-joined names, and *Padel*
   or *Padel · For fun*. The count stays only in the status tag (*Filling · 2 of 4 in*). **The mocks'
   *Padel · 3 of 4 in* is not used**: it would say the count twice and drop the *For fun* that says
   which deck you came from.
3. **Mock 7 leads over mocks 5 and 6** (Q6) — *mock 6 over mocks 4/5* in the decision log's prose
   and PRD #827. **You first** in the grid, **an emoji per tag**, and **the bar full width under the
   number and word**, where the brief said *next to the word*.

### 11. Where it lives

- **The formula is one pure function in the Match Fit engine** (`app/engines/matchfit/`), beside the
  forecast and the overlap. It takes the table's tag sets, the uncounted tags already removed, and
  returns the %. Proposals and Games both call it, so the deck, the details, the booked game and the
  Friends card can never disagree. The engine stays pure: no clock, no state, no database.
- **No ruleset release.** No ruleset number moves, and the bands are app presentation.
- **No new table:**
  - **Proposals declares its own batched port**, in its own words: *these players' tags*. Its adapter
    reads Discovery's `discovery_player_tags` in one query, rather than replaying profile streams on
    every read;
  - **Games declares its own tags port**, for the court's pairing read;
  - **Proposals declares a played-with port** for new faces, read off the games' record;
  - **each new port gets a row in its `tests/demands/` register.**
- **The deck read's statement count is held to a number by a test** (the `statements` fixture,
  #812). Every deck read now needs every named player's tags. If that can't be held, a projection is
  argued in an ADR, not added silently.
- **The dev seed** gives its seeded players tags spread so a For-fun deck shows all four bands,
  through the use cases and never SQL.

### 12. On the player surface

**This is a public API change**, called out as the backend's rules require. Old app versions live on
phones for months, so every change is additive where it can be:

- **the deck card** gains `vibe { pct }` on For fun, null on Competitive. Its already-nullable
  `forecast` becomes **null on For fun**, a case older apps already handle, because it is null today
  when somebody is unrated;
- **the proposal details**:
  - For fun gains `vibe { pct, rows [ { tag, carried_by [player_id] } ] }`, the rows being the
    reader's tags in the vocabulary's order, 💘 included;
  - Competitive gains the full forecast (each side's level, the signed gap, the %, provisional) and
    `at_stake { win_delta, loss_delta }` for the reader (§6);
- **the Friends card** gains `vibe` on For fun, and its nullable `forecast` becomes null on For fun;
- **Post a game's best fits** each gain `vibe` on a For-fun post, ranked by it, and their nullable
  `forecast` becomes null on For fun;
- **the game's pairing** (`GET /games/{id}/pairing`) gains `vibe`, with the same rows, on a For-fun
  game. Its `forecast` is **required today, so it keeps being sent** for older apps, and the new app
  ignores it on For fun;
- **the profile's tag write** accepts 2–8 and the 8 new codes, and the served vocabulary lists them.

**The specs are amended in place by the ticket that ships each part**: the home-rows mechanics §8.2
and §8.7, the You spec §3.11, the Games and Fill in mechanics and screens, the words
([`the-words.md`](../specs/matchmaking/the-words.md)), the player record, the player app's design
system and feature docs, and the backend's context rules. Until then, where they and this record
disagree, this record and PRD #827 win.

## Consequences

**Easier**

- **Two decks with two promises.** For fun is about the company and competitive about the result,
  and each says so with its own number on every surface. Neither number is diluted by the other.
- **Ola lands with people like her**: the ones who stay for a drink, or who are here to meet players,
  and more and more of them new faces. For fun feeds the competitive deck with names she knows.
- **Piotr sees his stakes before he answers**, computed by the function that will apply them.
- **The answer sits with the game**: the buttons are inside the card they answer, on both kinds.
- **The number can be trusted.** It is one formula, shared by every surface, worked out from current
  tags, and every point in it is a dot a player can see in the grid.
- **The tags can say more**: a coffee, a bite after, new in town, patient with beginners.
- **The separation is in the code**: one proposer, two named scoring policies.

**Harder**

- **Every deck read reads every named player's tags.** It is a batched port and a held statement
  count, and it may still need a stored projection one day, argued in its own ADR.
- **A For-fun table can be less even than today's.** Skill only guards the window, so the engine
  will seat a 0.80 gap that shares more over a 0.10 gap that shares less. The window is the only
  thing keeping a friendly from being lopsided.
- **Friends lose ties.** A new face beats a friend at the same vibe, so a player who wants friendlies
  with their friends sees them less often on For-fun cards. A friends game is the way to ask for
  them.
- **The number moves under the reader.** A tag edit changes the vibe of every card and game the
  player is on, booked and played ones too, and can reorder another player's deck between two reads.
  A played game's vibe is no longer what it was on the day, because nothing is stored.
- **💘 is the one exception to *every tag counts the same*.** A shared 💘 row is highlighted in the
  grid and adds nothing to the %, so a player can see a common thread the number didn't count. Every
  point in the % is a dot; not every dot is a point.
- **Two vibe numbers.** Same vibe's Vibe % and a singles Social vibe can differ for the same two
  players, and every surface and doc must keep the names apart.
- **The pairing sends a forecast the new app ignores** on a For-fun game, because the field is
  required and the apps already on phones read it. It is computed and sent for nothing, as far as
  the new app is concerned, for as long as those apps are about.
- **An older app shows a For-fun card with no headline figure.** Its forecast is null, and it doesn't
  know the vibe, until the player updates.
- **Tags now decide who a player meets.** A tag picked carelessly now costs good company, where
  before it only ordered one row on Home.
- **The design system takes four exceptions**, among them a soft for volt, which it said volt would
  never need.
- **Three more ports** — Proposals' tags and played-with, and Games' tags — each with a demands
  register row to keep.

**Neutral**

- **Competitive building, the competitive deck order and the competitive card are untouched.**
- **Availability, courts, prices and the book-by don't change**, for either kind.
- **No new table, no new event and no ruleset release.** `SocialTagsChanged` already exists; it
  only joins the events that mark a pool due.
- **Fill in's rows and the sign-in screen's mini card don't change.**
- **The club website and the public site don't change.**
