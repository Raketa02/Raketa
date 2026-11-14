# The player record — implementation

> **This is the plan the record was built from, and it is built** —
> `backend/app/modules/player_record` and `frontend_player/src/features/player_record`. Since
> the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)) a
> record is opened from a player's face on a game or a group — a Games card, a game's details, a
> booked game, Fill in, *Post a game*, a group's Members — or about yourself from You, and it is
> admitted by *played together*, *share a group* or *runs their group*, each a yes-or-no
> `PriorDisclosure`
> ([ADR-0159](../../adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)'s
> note; `player_record/application/admission.py`). Everything below about the Play tab, the
> builder, the pool header, `SH.whyfit`, the Fit breakdown, a `search_id` citation, the player
> card and search economics describes the removed loop and is kept as the plan's history.
>
> **Amended 2026-11-14** by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
> §2 (Q131): a record opens for **any reader**, except across a block either way or when the subject
> has *Show me to new people* off and shares no group, game or friendship with the reader, and it
> carries **all of the subject's photos**, where §§ below plan for the first alone. It opens from any
> face in Home's rows too ([the home rows mechanics §4.1](../home-rows/the-mechanics.md#41-records-q18-q27)).

**What replaces `SH.whyfit` when you tap a face on the forecast card, and everything the
backend has to grow for it to be drawable.**

- **Status:** built. This was the proposal.
- **Surface:** the bottom sheet opened from the balance-forecast card on *Build the four* /
  *Set up the match* (`BuilderScreen`), and from the same card on `PoolHeader`.
- **Spans:** `backend/` (one new context, one new route, three amended ports) and
  `frontend_player/` (one new feature, five new components, four design-system amendments).

---

## 0. The one sentence this changes

Today, tapping a seated player's face on the forecast card opens **`SH.whyfit`** — an
explanation of a *pairing*: eight terms, their weights, their evidence and a sub-total that
adds to the Fit. It answers **why 77**.

This work makes that tap open **`SH.player`**, the **player record** — a description of a
*person*: who they are, how well they play the sport you arrived from, and what the platform
has watched them do. It answers **who is this**.

> The two sheets are not versions of each other and neither replaces the other's job.
> `SH.whyfit` reads `(candidate, envelope)` — a pairing, which does not exist without a
> searcher. `SH.player` reads a player id — a person, who is the same person to everybody.
> §6.6 keeps both, and gives each its own gesture.

`SH.player` and `SH.playersocial` were ruled out of scope by **K-7**
([`the-words.md`](../matchmaking/the-words.md) §20.6). This document is the record that
brings the first of them back, and it brings back **one** sheet, not two.

---

## 1. The audit — what the design asks for, against what this platform holds

Every row was checked against the code, not against memory. `✅` exists and is reusable as
is; `⚠️` exists somewhere but not on any surface that reaches this sheet; `❌` does not exist
anywhere, or is an accepted refusal.

### 1.1 Section 1 · The header

| Element | Where the value lives today | Verdict |
| --- | --- | --- |
| Photo, or the generated poster | `PlayerCardSchema.photo_url` / `photo_id`; `CourtPoster` draws the fallback from the id alone (ADR-0134) | ✅ |
| Level printed on the photo, sport beneath | `PhotoPanel` (74 × 92) draws exactly this | ✅ — needs a **larger size variant** (§7.1) |
| Level falls back to their most-played sport when you did not arrive from one they play | nothing chooses a sport for a stranger — the card carries the *search's* sport and one Level | ⚠️ **new rule** (§4.4) |
| `ON COURT` shield | `OnCourtMark` + `PlayerCardSchema.review`; drawn on `allowed` only (ADR-0138) | ✅ |
| Nickname, `(you)` suffix, title flip to *How others see you* | `nickname` on the card; nothing serves you your own row | ⚠️ needs `/players/me/record` (§4.6) |
| Area | `area_code` | ✅ |
| Distance, omitted on your own record | `CandidateSchema.distance_km` — on the **candidate**, not the card, deliberately (ADR-0107) | ✅ — passed in beside the record, never fetched with it |
| **When they were last active** | nothing. **Refused** — ADR-0107, ADR-0106 §5 | ❌ **collision C1** (§2.1) |
| **Languages they speak** | nothing, anywhere. The `Language` modifier was *struck*, not deferred, as a nationality proxy under ADR-0096 | ❌ **collision C2** (§2.2) |
| Sport pills — one per rated sport, dot + abbreviation + level | `rating` holds one `SkillRating` per (player, sport); `GET /ratings` serves **your own only** | ⚠️ **new read** (§4.4) |
| Reliability pill out of 100, colour-coded | `PlayerCardSchema.player_score` (ADR-0140) | ⚠️ **moved (#384)** — it is 7.13's `Player Score` block under the level bar, and untinted; the ladder stays on the metered rows |

### 1.2 Section 2 · The skill card

| Element | Where the value lives today | Verdict |
| --- | --- | --- |
| Level | `mu` — on the card as `level`, on `RatingResponse` as `mu` | ✅ |
| `77% sure` | `SkillRating.confidence` — `100 × (1 − σ/1,20)`, capped at 99 (`CONTEXT.md`). **Not on the player card** | ⚠️ new field on this response |
| `21 counted` | `counted_games` | ⚠️ **moved (#384)** — out of the headline and into 7.13's `Counted` block |
| Four-segment band bar, current band full-strength | **`LevelBar` already draws exactly this** (design-system 7.5) | ✅ |
| Likely-range bracket with end ticks | **`LevelBar` draws it**; `range` is on the card (ADR-0107 amendment) | ✅ |
| Band name under the current segment | `band` on the card; `LevelBar` takes a `BandKey` | ✅ |
| Last 5, oldest → newest, never padded | `last_five`; `RecordBlocks` draws the squares | ✅ — and it is literally `RecordBlocks` now (#384), the sheet's own placer over the same `StatBox` |

**Section 2 is the cheapest section in the design.** `LevelBar` was built to this exact
specification and has never had a consumer that drew the bracket — it was written *for* the
record sheet K-7 removed. The only new wire field is `confidence`.

### 1.3 Section 3 · The record

| Element | Where the value lives today | Verdict |
| --- | --- | --- |
| *Shows up* — `9 of 9` | `StrandRatio{good, opportunities, value}` under `ReliabilityStrand.SHOWS_UP`. **Live.** Only the *blended* number crosses today | ⚠️ per-strand counts are new on the wire |
| *Answers challenges* — `11 of 11` | `ReliabilityStrand.ANSWERS_CHALLENGES`. **Stands down** since challenges stopped waiting for answers (#544); *Keeps plans*, read off booked games, is live in its place | — not drawn |
| **Confirms results** | **Struck, not deferred** — ADR-0137 / ADR-0140. `ReliabilityStrand.CONFIRMS_RESULTS` and its two ruleset weights were deleted with the provider | ❌ **collision C3** (§2.3) |
| **Sportsmanship, by opponents — 4,8 / 5** | `ReliabilityStrand.SPORTSMANSHIP` exists as a *name* and **stands down**: no surface on this platform lets anybody rate anybody | ❌ **collision C4** (§2.4) |
| **Opponent variety — 70 %** | `GameHistoryQuery.played_counterparts` returns one row per person. The *statistic* was withdrawn from `player_score`'s contract when both its consumers were struck (ADR-0098 amendment) | ⚠️ **returns with a consumer** (§2.5) |
| Green card / red card | out of scope by the request | — |

### 1.4 Section 4 · Social tags

| Element | Where the value lives today | Verdict |
| --- | --- | --- |
| Every tag they chose, in one row | `social_tags` on the card; the closed vocabulary is `player_profile`'s `social_tags.py` | ✅ |
| Green + `· you too` for a shared tag, grey otherwise | `domain/socialTagOverlap.ts` returns four answers; `SocialTagRow` draws them | ✅ — **reused whole** |

Section 4 needs **no backend work and no new component**. The one difference from the
candidate card is that the record sheet shows *every* tag rather than the card's cap of six,
which is a prop, not a rewrite (§6.4).

---

## 2. The five collisions, and what to do about each

Four of these are collisions with **accepted records**. Building the design as drawn would
silently overturn them. Each gets a recommendation; three of them narrow the sheet.

### 2.1 C1 — "active now" is a refusal, not a gap

> *"No activity recency, at any granularity — not a timestamp, not* active today*, not a
> green dot."* — `cards.py`, on ADR-0107.

ADR-0107 audited the prototype's card and found *active 2 hours ago* to be **row three of the
Liveness table**, which ADR-0106 §5 refuses to let cross the wire *under any name*. Liveness
reaches a screen exactly one way — as a **reason code** on a candidate, saying why somebody
was shown.

The refusal is not about the card in particular. It is about the fact: this product does not
have a presence indicator, and *"active now"* is one. A sheet is not a smaller surface than a
card; it is a bigger one.

**Recommendation — drop it, and say so in the identity line's shape.** The identity line
becomes `Area · distance · languages`, three parts rather than four. If the product wants a
recency signal, that is a new decision with its own record, and it has to answer the question
ADR-0106 asked and ADR-0107 upheld: *why is a stranger entitled to know when you last opened
the app?* This document does not answer it, and building it here would settle it by accident.

**If the product insists**, the *only* shape that does not reopen ADR-0106 is the one already
sanctioned: the **Liveness reason code** the search already returned for this candidate,
rendered as the words the client owns — never a timestamp, never a duration, never a dot. It
says *why the engine thought they were reachable*, which is a different claim from *when they
were here*. That is a narrowing, and it needs an ADR amendment to ADR-0107 that says so.

### 2.2 C2 — languages do not exist, and the last attempt at them was struck on privacy

Two separate problems, and the second is the serious one.

1. **There is no language field.** Not on `users`, not on `player_profile`, not in
   onboarding. Adding one is a profile field, a migration, an onboarding step, a vocabulary in
   `CONTEXT.md` and a place in `PlayerProfileResponse`. That is a work item of its own size,
   and none of it is matchmaking.
2. **The `Language` modifier was deleted rather than deferred**, and the deletion argument
   applies to *showing* it too:

   > *"`Language` read a field that exists nowhere in this backend and is the nearest
   > available proxy for the nationality the privacy line excludes by name — ADR-0096's rule
   > is that a protected characteristic may gate and may never score."* — `v1/modifiers.py`

   ADR-0096's rule is about **scoring**. Printing is not scoring, so publishing a spoken
   language on a record is not *automatically* forbidden by it — but it is the same proxy, and
   the record sheet is the surface where a stranger reads it about somebody they have not met.

**Recommendation — out of this scope, tracked as its own ticket.** The identity line ships as
`Area · distance` and grows a third part when a language field exists and an ADR has decided
that it may be shown. The client's `identityLine()` is written to take an **optional**
`languages` so the seam is there and the sheet does not have to be re-laid-out later.

### 2.3 C3 — "Confirms results" was struck, and it cannot be honestly published

> **Settled the other way, on a denominator this section did not consider.** The product
> owner was shown the collision below and reaffirmed the row, and
> [ADR-0160](../../adr/0160-a-results-strand-counts-answers-and-never-agreements.md) ships a
> **third meter** — as **Answers about results**, which counts *answers* to a score put in
> front of somebody rather than agreements, so a counter scores exactly as an acceptance does
> and only silence is a miss. *Confirms results* stays struck; what follows is the argument
> against the meter this file proposed, and it still holds against that one. See
> [`the-decisions.md`](the-decisions.md) §4, which is newer than this file.

This is the sharpest collision, because the design's third meter is a strand the platform
deliberately deleted:

> *"An unconfirmed result is a fact about a **pair** and a strand is a verdict about a
> **person**, and every denominator tried on it docks somebody the Games context refuses to
> penalise — both sides of an honest disagreement included."* — `CONTEXT.md`, on ADR-0137

The design's own denominator — *"results confirmed inside the 24-hour window, of results
awaiting them"* — is precisely one of the denominators ADR-0137 tabled and rejected: it docks
the player whose honest counter-claim the other side then ignored.

**Recommendation — two meters, not three, and the sheet says nothing about the third.** This
is not a gap to be drawn greyed-out or as *coming soon*: a strand that stands down is *not in
the answer at all*, which is `player_score`'s own invariant, and it is why the two live
strands renormalise to 100 % of the published blend without being credited for a record
nobody keeps.

The visual consequence is small — the record card has two metered rows instead of three — and
the honesty consequence is the whole point of the card's own title.

> **This also fixes a live inconsistency the design would have entrenched.** `RecordBlocks`'
> docstring still describes the Player Score as *"turning up, answering challenges, confirming
> results"*. The third clause is stale; it should be struck in the same commit.

### 2.4 C4 — sportsmanship has no input surface, and building one is a product, not a row

`ReliabilityStrand.SPORTSMANSHIP` exists as a *name* with `PUBLISHED_WEIGHTS[…] = 8`, and it
stands down for one reason: **nobody rates anybody on this platform.** Publishing `4,8 / 5`
needs, in order:

1. a post-game prompt on a surface that does not exist (the loop's game screen would host it);
2. a rating aggregate or a fold, with its own decay and its own minimum-observation floor;
3. an answer to *who may rate whom* — an opponent only, or a partner too;
4. an answer to the abuse question ADR-0095 and ADR-0128 both circle: a rating is a
   **directed** act against a named person, which is a Block's shape, and a mean over three
   answers is trivially poisoned by one;
5. its own place in `PUBLISHED_WEIGHTS`, which changes **every** existing player's published
   score the day it ships.

**Recommendation — out of scope, and it deserves its own map.** Item 5 is the one that makes
this non-negotiable as a sub-task: turning a stood-down strand live retunes the number printed
on every card in the product, and that is a decision with a rollout, not a row on a sheet.

The record card's two non-metered rows therefore become **one** — opponent variety — and the
card ships as *two meters and one figure*.

### 2.5 C5 — opponent variety returns, because this sheet is the consumer it lacked

Opponent variety is the one item in the design that is genuinely **available and merely
unowned**:

> *"Not demanded of `player_score` any more: it was contracted on behalf of two consumers and
> #164 and #175 struck both, so ADR-0098 was amended to withdraw it — a consumer-driven
> contract with no consumer is withdrawn, not carried. **The word survives as product language
> for the Player Score screen; if a later term wants the statistic, it returns as that term's
> demand and signs for it.**"* — `CONTEXT.md`

This sheet is that later consumer. `GameHistoryQuery.played_counterparts` already answers *one
row per person, newest first, bounded* — which is exactly the numerator's raw material.

**Recommendation — build it, in `player_record`, signed for by `player_record`.** It returns
as **this context's** demand rather than as a resurrected `player_score` field, because that
is what ADR-0098's amendment said would happen and because it is not a reliability strand: it
does not price a promise kept, it describes a habit. §4.5 defines it.

### 2.6 The sheet as it actually ships

| Section | As drawn | As shipped |
| --- | --- | --- |
| 1 · Header | photo · level · shield · name · **area · distance · last active · languages** · sport pills · score pill | photo · level · shield · name · **area · distance** · sport pills · score pill |
| 2 · Skill | unchanged | unchanged |
| 3 · Record | 3 meters + sportsmanship + variety | **2 meters + variety** |
| 4 · Social tags | unchanged | unchanged |

Four items leave, each with a record behind it. Everything the design asks for that this
platform can honestly say, ships.

---

## 3. The decision — a record is read through the thing that entitles you to it

### 3.1 Why not widen the player card

The obvious move is to add the missing fields to `player_card` and let the sheet draw from
the row the client already holds. It is wrong on three counts.

**It breaks the closed list on its own terms.** ADR-0107's rule for admitting a field is *a
card says only what its subject published, and every field on it is a fact about that person
alone.* Per-strand numerators and denominators, four sport pills and an opponent-variety
percentage all pass that test — and pass it is not the same as belong. The card's *size* rule
is the one they fail: it is attached **over the twenty rows that survived**, and the sheet's
extra payload would be paid twenty times per search to be read at most four times, usually
zero.

**It inverts ADR-0107's own economics.** The ADR chose one round trip because *"a batch
profile route would make the shortlist arrive as twenty grey rectangles and would put a second
request in front of* Why 78?*, which §8.3 requires to open instantly."* That argument is about
a **list**. A sheet opened by a deliberate tap on one person is the case where a second
request is correct: it has a legitimate place to show progress, it is one player rather than
twenty, and it is not on the path to the screen.

**It puts a profile read inside the matcher.** `matchmaking` owns *why these people*. A
description of one person is not that, and the sport-pill read in particular would make
`matchmaking` a reader of every rated sport of every candidate — for a fact no term may score.

### 3.2 The route, and the gate

> **`GET /api/v1/players/{player_id}/record?search_id={id}`** — the record of one player, read
> through a search of yours that showed them.
>
> **`GET /api/v1/players/me/record`** — your own, uncited.

The citation is the precedent `POST /forecasts` already set, and its schema already carries
the argument verbatim:

> *"`search_id` is **required**, and every player named must have appeared in that search's
> returned rows. **Unbounded, this would be a level lookup for any player in the city reachable
> by id; bounded, it tells you nothing the shortlist did not already show you.**"*

Every word of that applies here and applies harder — this response says *more* about a person
than a forecast does. Without the gate, `GET /players/{uuid}/record` is a player-enumeration
endpoint, and the fact that a UUID is hard to guess is not an authorisation model.

**Three properties make the citation the right credential rather than merely a convenient one:**

- **The search record is kept for ever** (ADR-0104), so the entitlement never expires and a
  sheet re-opened next week still opens.
- **The record holds the card as it was shown** (`search_workbench.py`: *"the whole row that
  was shown, not a summary"*), so *was this reader shown this player* is a fact already
  written down, not a permission to be computed.
- **A withheld row carries an id and no card** (ADR-0130), so the gate has a natural third
  answer: `403` is *you were never shown them*, and a withheld row is `404` on the record while
  the seat stays drawn — the gate is refused **and not named**, which is ADR-0130's rule.

**Extensibility, without changing the resource.** The credential is a query parameter and the
resource is the player's record, so `challenge_id` and `game_id` join as alternative
citations when the loop wants this sheet — a chat header, a game screen — without a second
route or a second response shape. Exactly one citation is required; two is a `422`.

### 3.3 The context — `player_record`, an assembler that stores nothing

`player_score` set the precedent and the argument transfers whole:

> *"We will add `app/modules/player_score/` with **no aggregate, no table and no migration.**
> Every fact it publishes is folded out of … streams at the moment somebody asks. … A score is
> derived from two records; it is not a third record."* — ADR-0140 §1

A player record is derived from **five** records — `player_profile`, `users`, `rating`,
`games`, `player_score` — and it is not a sixth. It keeps no state, owns no table, ships no
migration, and every fact it publishes it reads through the owning context's published port.

It is a **new module** rather than a widening of `matchmaking` for §3.1's third reason, and
its shape is `player_score`'s mirrored: **one route out, and every port inward.**

```
backend/app/modules/player_record/
├── domain/
│   ├── record.py        # PlayerRecord, SportPill, SkillPanel, RecordPanel, StrandRow
│   ├── variety.py       # opponent variety — the one statistic this context owns
│   ├── sport_choice.py  # which sport the header prints, and the fallback
│   └── ports.py         # the five demands, each a consumer-driven contract
├── application/
│   └── read_player_record.py
├── infrastructure/
│   ├── rating_sports.py           # RatedSportsQuery  -> rating
│   ├── games_variety.py           # OpponentVarietyQuery -> games
│   └── search_entitlement.py      # RecordEntitlement -> matchmaking
└── presentation/
    ├── routes.py
    ├── schemas.py
    └── dependencies.py
```

**The entitlement is a port, not an import.** `player_record` declares
`RecordEntitlement.may_read(reader, subject, citation)` in its own vocabulary;
`matchmaking` satisfies it from the search record. That is ADR-0098's consumer-driven shape
and it is what lets `challenges` and `games` satisfy the same demand later without
`player_record` learning what a challenge is.

---

## 4. Backend design

### 4.1 The domain types

```python
# domain/record.py

@final
@dataclass(frozen=True, slots=True)
class SportPill:
    """One sport this player is rated in — the dot, the abbreviation, the Level."""
    sport: Sport
    level: float          # μ, as rating published it
    band: BandName

@final
@dataclass(frozen=True, slots=True)
class SkillPanel:
    """The skill card. Present only where the player is rated in the printed sport.

    The three headline figures travel together and are never separable: a Level
    with no certainty beside it and no count under it is the claim ADR-0107's
    ``range`` amendment was added to stop.
    """
    sport: Sport
    level: float
    sigma: float
    confidence: int                     # rating's own, 100 x (1 - sigma/1,20), capped 99
    counted_games: int
    likely_range: LikelyRange           # mu +/- sigma, clamped to the scale
    band: BandName
    last_five: tuple[GameResult, ...]   # oldest to newest, never padded

@final
@dataclass(frozen=True, slots=True)
class StrandRow:
    """One metered row: the raw fraction and the figure derived from it.

    The two counts and the figure all cross, and the figure is **not** re-derived
    by the client. ``StrandRatio.value`` is derived in one place so that a card, a
    profile and the matcher's evidence cannot print three roundings of one record
    — and a client dividing ``good`` by ``opportunities`` itself would be the
    fourth.
    """
    strand: ReliabilityStrand
    good: int
    opportunities: int
    value: int          # StrandRatio.value, half rounding up

@final
@dataclass(frozen=True, slots=True)
class RecordPanel:
    """What the platform watched. **Counted by the system, not written by people.**

    ``strands`` holds only the strands this player actually has, in
    ``PUBLISHED_WEIGHTS`` order. A strand that stands down platform-wide and a
    strand this player has no opportunity for are the same absence here, and both
    are spelled by not being in the tuple.
    """
    player_score: int                    # PlayerScore.published
    strands: tuple[StrandRow, ...]
    opponent_variety: Percentage | None  # None where the bound is not met (4.5)

@final
@dataclass(frozen=True, slots=True)
class PlayerRecord:
    identity: CardIdentity               # matchmaking's type, reused (4.7)
    area_code: AreaCode
    sports: tuple[SportPill, ...]        # every rated sport, most-played first
    skill: SkillPanel | None             # 2.6 — absent where unrated in the printed sport
    record: RecordPanel | None           # absent where the platform has watched nothing
    social_tags: tuple[SocialTagId, ...]
    is_self: bool
```

**Every optional is an omission and never a nought**, which is the discipline
`distance_km`, `counted_games`, `player_score` and `last_five` all already take
(ADR-0106 §4). A brand-new player's record draws a header, four social tags and nothing else,
and that is a correct record.

### 4.2 The ports — five demands, each signed by its owner

| Port | Owner | Method | Status |
| --- | --- | --- | --- |
| `RecordEntitlement` | `matchmaking` | `may_read(reader, subject, citation) -> Entitlement` | **new** |
| `PlayerCardSource` | `player_profile` / `users` | `identities_for(ids)` | **reused as is** |
| `CardPhotoLinks` | `player_profile` | mints `photo_url` | **reused as is** |
| `RatedSportsQuery` | `rating` | `ratings_of(player_id) -> Mapping[Sport, SkillRating]` | **new** |
| `PublishedScoreQuery` | `player_score` | `scores_for(ids, now=)` | **reused as is** |
| `PlayerRecordSource` | `games` | `records_for(ids)` | **reused as is** |
| `OpponentVarietyQuery` | `games` | `variety_of(player_id, now=)` | **new** |

Three of the seven already exist and are read unchanged, which is the payoff of ADR-0098's
split. The three new ones are single-player rather than set reads — the sheet is one person,
and a set-shaped port here would be a contract nobody can honour cheaply for a caller that
never batches.

> **`RatedSportsQuery` is `rating`'s, and it is not `GET /ratings` widened.** That route is
> *"the Skill ratings **this player** holds"* — a self read, correctly. A port that answers
> about a third party is a different contract with a different authorisation story, and the
> gate for it is `RecordEntitlement`, checked before this port is called at all.

### 4.3 The assembler

```python
# application/read_player_record.py

async def read_player_record(
    *, reader: UUID, subject: UUID, citation: Citation | None, now: Instant, ...
) -> PlayerRecord:
```

Order matters and is asserted:

1. **Gate first.** `RecordEntitlement.may_read(...)`. A refusal raises before any provider is
   touched — a read that fetched a stranger's ratings and *then* refused would have done the
   lookup the gate exists to prevent.
2. **Identity, area, tags** — `PlayerCardSource`, then `CardPhotoLinks` mints the URL.
3. **Ratings** — `RatedSportsQuery`, once. This answers both the pills and, after §4.4 picks
   the sport, the skill panel. **One read, two consumers**: re-reading for the panel would be
   two places for *what is their padel level* to be true.
4. **Record** — `PublishedScoreQuery`, `PlayerRecordSource` and `OpponentVarietyQuery`,
   concurrently. All three answer *absent* for a player with nothing, and the panel is `None`
   only when **all three** are absent.
5. **Assemble.** No arithmetic anywhere in this function except §4.4's choice: every figure is
   its owner's, and `StrandRow.value` is copied from `StrandRatio.value` rather than divided.

**`now` is taken, never read.** `PublishedScoreQuery` and `OpponentVarietyQuery` both fold
against a clock, and a request that asked them at two instants could publish a score whose
strands disagree with its variety about which games exist. This is `PublishedScoreQuery`'s own
rule, applied to the second reader.

### 4.4 Which sport the header prints — the one rule this context owns

The design: *"The rating shown is for the sport you arrived from — if you opened this from a
padel context you see their padel level; if the sport you came from isn't one they play, it
falls back to their most-played sport."*

```python
# domain/sport_choice.py

def sport_to_print(
    arrived_from: Sport | None, rated: Mapping[Sport, SkillRating],
) -> Sport | None:
    """Which sport's Level the header prints, and the panel is about."""
```

Three answers, and the third is why this is a function rather than a `dict.get`:

- **The sport you arrived from**, where they are rated in it. The overwhelming case.
- **Otherwise their most-played** — *most counted games*, not highest Level and not most
  recent. A fallback on Level would make the header a boast; a fallback on recency would be
  activity recency wearing a sport's name, which is C1 returning through the side door.
- **`None`** where they are rated in nothing, which is a real state during onboarding. The
  header draws the poster with no Level on it and §2 is absent.

**Ties break on the sport's own enum order**, declared and tested. An unordered `max` over a
mapping is exactly the set-iteration non-determinism ADR-0105 exists about, and a header that
printed padel on one read and squash on the next would be the most visible possible instance
of it.

**`arrived_from` comes from the citation, never from the client.** The search knows its own
sport; a client-supplied sport would let a caller ask *what is their tennis level* about
somebody a padel search showed them, which is the citation gate being satisfied and then
ignored.

### 4.5 Opponent variety — the definition, and its floor

> **Opponent variety** — of this player's counted games, the share played against **distinct**
> people. `distinct_counterparts / counted_games`, out of a hundred, half rounding up.

```python
# domain/variety.py

MIN_GAMES_FOR_VARIETY: Final = 5

def opponent_variety(counterparts: int, counted_games: int) -> Percentage | None:
    """The share of their games played against different people, or None.

    **Absent under the floor rather than published as a small sample.** Somebody
    with two games against two people is at 100 %, and printing that beside
    somebody at 100 % over forty games is the exact defect ``counted_games``
    exists on the card to prevent — which is why the raw fraction is printed
    beside every other figure on this panel and why this one has a floor instead.
    """
```

Three things this definition deliberately is not:

- **It is not a strand**, and it is not in `PUBLISHED_WEIGHTS`. It prices no promise; it
  describes a habit, and it neither raises nor lowers the Player Score. It is on the panel
  because it is *context for a rating* — the design's own words: *"a low one means someone
  playing the same four faces every week, which is why their rating may be narrow but
  untested."*
- **It is not decayed, windowed or weighted.** `played_counterparts` is already bounded and
  newest-first, and a second window here would be a number that must not disagree with the
  matcher's `horizon_days` — which is exactly the rejection ADR-0140 §4 records.
- **It is not published where the platform watched nothing.** Absent, like everything else on
  this panel.

`OpponentVarietyQuery` is `games`' because both inputs are: it folds `played_counterparts`
and `counted_games_for` in one pass and answers a count pair, and this context divides.

### 4.6 Your own record — `GET /players/me/record`

Required by the design's own first section, and by a gap the client already documents:

> *"You have no candidate row because **no route serves a searcher their own**."*
> — `seatedHandles.ts`

You are one of the four on that court. Without this route your own face stays the one seat
that is not a button, and *How others see you* has nothing behind it.

**It is the same assembler with the gate short-circuited and `is_self` true.** Not a second
response shape, and not `GET /players/me/profile` widened — that route is the *editable*
surface, in `player_profile`'s vocabulary, and this one is *how a stranger sees you*, in this
context's. Two shapes, one subject, and the sheet's own title says which is which.

**`arrived_from` is optional here** and comes from a query parameter when the sheet is opened
from a court, because your own record has no citation to read a sport off.

### 4.7 What is reused verbatim, and one thing to move

`CardIdentity` (`nickname`, `photo_id`, `review`) is exactly this sheet's header identity, and
`PlayerCardSource` / `CardPhotoLinks` already answer it. They live in
`matchmaking/domain/cards.py` because the card was matchmaking's first.

**Do not import them across the module boundary.** `.importlinter` will refuse it and should.
The move is small and belongs in the first backend ticket:

> `CardIdentity`, `PlayerCardSource` and `CardPhotoLinks` move to
> `app/modules/player_profile/domain/identity.py` — the context that **owns** a nickname, a
> photo and its verdict — and `matchmaking` imports them from there. No behaviour changes, no
> wire field moves, and the contract-freshness check proves it.

This is ADR-0098's split applied to a type rather than to a method: it is filed by *who
supplies the fact*, and `matchmaking` was never the supplier.

### 4.8 Tests

| Level | What it pins |
| --- | --- |
| `tests/unit/test_sport_to_print.py` | the three answers, the tie-break, and that a tie is stable across two `PYTHONHASHSEED`s (ADR-0105) |
| `tests/unit/test_opponent_variety.py` | the floor, the rounding, and that the absence is not a zero |
| `tests/unit/test_player_record_assembly.py` | every optional omitted rather than noughted; panels absent as a whole; strand order is `PUBLISHED_WEIGHTS`' |
| `tests/unit/test_record_gate_runs_first.py` | **a refused read touches no provider** — spy ports, assert zero calls |
| `tests/api/test_player_record.py` | `200` cited · `403` uncited · `403` citing somebody else's search · `404` on a withheld row, with the gate unnamed (ADR-0130) · `422` on two citations · `me` needing none |
| `tests/demands/` | the three new ports have adapters, and no adapter signs half a contract |

**No migration, and a test says so.** `player_score` has the same assertion and the same
reason: the day this context grows a table is the day it stopped being an assembler, and that
should fail a build rather than pass a review.

---

## 5. The wire

```jsonc
// GET /api/v1/players/{player_id}/record?search_id=…
// GET /api/v1/players/me/record[?sport=…]
{
  "is_self": false,
  "nickname": "Karol T.",
  "photo_id": "…",                  // omitted together with photo_url
  "photo_url": "https://…",         // minted per response, stored nowhere
  "review": "ALLOWED",              // omitted for "nobody looked"
  "area_code": "KAZIMIERZ",
  "social_tags": ["STAYS_FOR_A_DRINK", "NEW_IN_TOWN", "KEEPS_SCORE", "HERE_TO_IMPROVE"],

  "sports": [                       // one per rated sport, most-played first
    { "sport": "PADEL",  "level": 2.75, "band": "ESTABLISHED" },
    { "sport": "SQUASH", "level": 2.90, "band": "ESTABLISHED" }
  ],

  "skill": {                        // omitted where unrated in the printed sport
    "sport": "PADEL",
    "level": 2.75,
    "sigma": 0.28,
    "confidence": 77,
    "counted_games": 21,
    "range": { "low": 2.47, "high": 3.03 },
    "band": "ESTABLISHED",
    "last_five": ["WIN", "WIN", "LOSS", "WIN", "WIN"]
  },

  "record": {                       // omitted where the platform watched nothing
    "player_score": 93,
    "strands": [                    // only the strands this player has
      { "strand": "SHOWS_UP",           "good": 9,  "opportunities": 9,  "value": 100 },
      { "strand": "ANSWERS_CHALLENGES", "good": 11, "opportunities": 11, "value": 100 }
    ],
    "opponent_variety": 70          // omitted under the floor
  }
}
```

**Four rules the schema docstrings must carry, because they are what a client would otherwise
get wrong:**

1. **`value` is served, never derived.** A client dividing `good` by `opportunities` produces
   a fourth rounding of one record. `out_of_a_hundred` rounds halves **up**; JavaScript's
   `Math.round` also rounds `.5` up but rounds negatives the other way, and the day a
   percentage is computed anywhere else the two will disagree by a point on exactly the values
   a player notices.
2. **`strands` is a list, not an object with fixed keys.** A strand that stands down is absent,
   and a client keying on `SHOWS_UP` would draw a zero-width bar for a player who has never
   been due anywhere.
3. **`sports` is ordered by the server** and the client must not re-sort it. The order is
   *most-played first*, which is a fact the client cannot see.
4. **No date appears anywhere in this response, at any granularity.** C1's refusal, restated
   where a schema author would be tempted — `last_five` carries outcomes in order and no
   moments, and a `last_at` on a strand would be the same violation one field further in.

`make gen-api` regenerates the client's types and the drift check enforces that they ship in
the same commit.

---

## 6. Frontend design

### 6.1 Where it lives

The sheet is **not** `features/play/`. It is opened from Play today and from the loop's chat
header and game screen tomorrow, and a component three features deep in a fourth is how a
feature stops being feature-first.

```
frontend_player/src/features/player_record/
├── api/playerRecordApi.ts
├── domain/
│   ├── playerRecord.ts        # the client's own type + the wire mapper's target
│   ├── ratioTone.ts           # 90/70 thresholds -> a tone. One place.
│   └── scoreTone.ts           # the pill's thresholds
├── components/
│   ├── PlayerRecordSheet.tsx  # SH.player — the sheet, and the only export
│   ├── RecordHeader.tsx       # section 1
│   ├── SkillCard.tsx          # section 2
│   ├── RecordCard.tsx         # section 3
│   ├── SportPills.tsx
│   ├── StrandMeterRow.tsx
│   └── recordPresentation.ts  # every string and every accessible name
├── hooks/
│   ├── playerRecordKeys.ts
│   └── usePlayerRecord.ts
├── mappers/playerRecordMappers.ts
└── types.ts                   # the feature's public surface, one barrel
```

`features/play/` imports **`PlayerRecordSheet` and nothing else**. That is the same seam
`challenges` already has with the builder's send.

### 6.2 What is reused, and what is genuinely new

| Section | Reused as is | New |
| --- | --- | --- |
| Chrome | `BottomSheet` (9.1) — grab, close, scrolling body, focus in and back | — |
| 1 · Header | `CandidatePhoto`, `CourtPoster`, `OnCourtMark`, `Tag`, `playerName()` | `RecordHeader`, `SportPills`, a **large** `PhotoPanel` variant |
| 2 · Skill | **`LevelBar`** — bands, bracket, band names, the lot | `SkillCard` (a headline row and a `LevelBar`), `RecordBlocks`' squares extracted |
| 3 · Record | `Meter` (+ a `tone`), `Card`, `Hairline`, `Row` | `RecordCard`, `StrandMeterRow` |
| 4 · Tags | **`SocialTagRow` whole**, `domain/socialTagOverlap` whole | — |

**Section 2 costs almost nothing and that is not luck.** `LevelBar` was specified at
design-system 7.5 with a likely-range bracket that no shipped screen draws, because the screen
it was drawn for is the one K-7 removed. It comes back and its consumer arrives with it.

**Two extractions, both small and both owed anyway:**

- `RecordBlocks`' five squares become `shared/ui/LastFive.tsx`. Two callers now — the
  competitive card and this sheet — and `recordSquares.test.ts` already tests the geometry
  independently of the block that draws it.
- `PhotoPanel` gains a `size` prop (`'card' | 'record'`). The 74 pt panel's whole design is
  arithmetic against its own width (`OnCourtMark`'s docstring is three paragraphs of it), so
  the second size **re-derives** rather than scales: at record size the shield fits top-left
  as the design draws it, and `onCourtMarkFit.test.ts` gains the second case. The pinned
  `photoScrim` and its worst-case 5,24:1 are unchanged and unchangeable.

### 6.3 The two sheets, and the gesture that separates them

§20.4.1 gave the seated player two routes to one sheet and admitted the duplication: *"a hold
on the seat is a shortcut duplicating it."* The duplication becomes a division of labour.

| Gesture | Opens | Answers |
| --- | --- | --- |
| **Tap a face on the forecast card** | `SH.player` | *who is this person* |
| **Hold the seat on the court** | `SH.whyfit` | *why this fit* |

Nothing is lost: every explanation `SH.whyfit` gives is still one gesture away from the same
screen, and the two gestures now open two different answers rather than the same one twice.

**Your own face becomes a button** — it is not one today, because nothing served your row.
It opens *How others see you*.

**A withheld seat stays plain text.** ADR-0130: a withheld row carries an id and no card, the
record `404`s, and a name that opened an apology is exactly what `seatedHandles`' rule already
refuses.

### 6.4 The four sections

**`RecordHeader`** — a `PhotoPanel` at record size, and a column beside it:
`playerName()` (+ `(you)` when `is_self`), the identity line, the sport pills, and the score
pill pushed right. The identity line is `recordPresentation.identityLine()`, joining with
`·` and **dropping absent parts rather than leaving a gap** — distance is absent on your own
record, and languages are absent until C2 is answered.

**`SportPills`** — one `Tag` per sport, each with a 6 pt `theme.size.sportDot` in
`theme.color.sport[key]`, an abbreviation and the level. `theme.ts` already anticipates this
consumer by name: *"the sport chips, **the sport tags on the player record**, and the court
gradient"*. Every one carries the sport's abbreviation in text, which is the condition that
comment attaches to drawing a sport dot at all.

**`SkillCard`** — the headline row (`PADEL · 2,75 · 77 % sure`) over a `LevelBar` with
`legend` omitted. Drawn only when `skill` is present.

> **Amended (#384).** The headline carried `· 21 counted` as a fourth clause, and the run of
> five sat inside this card under the bar. Both moved into **`RecordBlocks`**, 7.13's three
> boxes, drawn as the sheet's next row. The argument the headline was making is kept rather
> than dropped: *the count is what makes the other two honest*, and *three boxes is how one of
> them ends up conditionally hidden* — but the count's block is **never** conditional, because
> `counted_games` is measured and the wire always sends it beside a Level. What was a rule a
> string obeyed is now structural. Printing it in both places was refused: the two are inches
> apart in one card, so a reader would meet `21 counted` twice in two registers.

**`RecordBlocks`** — `Player reliability` · `Last 5` · `Counted`, in `shared/ui`'s `StatBox`, drawn
under the skill card and **not inside it**. The three absences are independent: a player who
has been ghosted on and holds no rating at all has a Player Score and no skill panel, so a
block nested in a card gated on `skill` would take their one figure down with the sport. The
Player Score block is **untinted** — see §7.4 and 7.13.

> **Amended again (#384).** Four changes, each a decision against something written above.
> **The block is titled *Player reliability*** — the domain term is untouched, but *Score*
> beside a Level, a band and a run of form is a fourth number a reader can take for a rating.
> **A won square is `mint` and a lost one `muted`**, which trades 7.13's lightness step for a
> hue one and spends the 3:1 between the two states; the ratio against the ground is kept, so a
> loss is still not the gap. **The Fit breakdown moves to `Player fit ✦ 78` under the sport
> pills** — the sheet's one action, out of the foot where a reader had to scroll past four zones
> to find it, and **not a button**: it is 7.10's own pill with a word in front of it, the same
> object the reader met on their shortlist, because coral on a filled control promises a submit
> and the thing to do on a record is read it. **The two
> sentences under the sportsmanship row are removed** — `WRITTEN_BY_PLAYERS`, which
> `the-words.md` asks for by name wherever the star figure is drawn beside the reliability
> figure, and `BAND_HAS_NO_COUNT`. The row's label still names its author; nothing now says that
> a low average costs nobody anything.

**`RecordCard`** — the title, then a `StrandMeterRow` per served strand, then the variety row.
The title is the rule the card enforces and it stays verbatim: **THE RECORD — COUNTED BY THE
SYSTEM, NOT WRITTEN BY PEOPLE.**

**`StrandMeterRow`** — label left, `9 of 9` right, `Meter` beneath, tinted by
`ratioTone(value)`. The strand's *name* is the client's copy, keyed off the served code —
ADR-0022, and the same reason `SocialTagRow` renders `STAYS_FOR_A_DRINK` in its own words.

### 6.5 The bar is a `Meter`, not a `Bar` — and that keeps a flat rule flat

`the-words.md` §20.8 states *"`progressbar` appears nowhere in the Play contract"*, and its
stated reason is that **`SH.player`'s three meters were the only others in the prototype and
K-7 ruled them out.** This sheet is those meters returning, so the rule's justification is
back in play and has to be re-decided rather than inherited.

**It is re-decided the same way, and the rule survives unchanged.** Every row prints `9 of 9`
in words two words from the bar. A `progressbar` announcing `9 of 9` is 6.8's double
announcement — *"without that, every cell is announced twice"* — and the row would reach a
listener as *Shows up, 9 of 9, progress indicator, 9 of 9*.

So: **`Meter`**, hidden on both platforms, taking no accessible name, exactly as it is
specified. What changes is one prop:

> `Meter` gains `tone?: 'good' | 'neutral' | 'poor'`, defaulting to today's `night`. The fill
> becomes `mint` · `night` · `red`.

`Bar` keeps its `progressbar` and its `accessibilityValue` and gains no caller here.

### 6.6 Fetching

```ts
export const playerRecordKeys = {
  all: ['player-record'] as const,
  detail: (subject: string, citation: Citation) =>
    [...playerRecordKeys.all, subject, citation] as const,
  me: () => [...playerRecordKeys.all, 'me'] as const,
};
```

**The citation is in the key.** The same player read through two different searches is two
entitlements to the same facts, and a key that dropped it would serve a cached record after
the entitlement that fetched it stopped applying.

- `enabled` on the sheet being open — nothing is prefetched, and a court of four does not
  fire four requests to show one.
- `staleTime` matches the search detail read's, so the sheet and the card underneath it cannot
  disagree about a Player Score within one session.
- **Three states, and the sheet is up for all three**: skeleton, the record, or
  `mapError`'s recovery message with a retry. The sheet opens instantly and fills — which is
  the whole reason §3.1's second round trip is affordable here and was not on the shortlist.
- `photo_url` is minted per response and dies within minutes. On an expired link
  `CandidatePhoto` already falls back to the poster, which is what a player with no photo
  gets — no error, no retry.

### 6.7 Accessibility

- **The sheet's accessible name is its visible title** — `Player record`, or
  `How others see you`. Unlike `SH.whyfit`, no glyph is doing work in the title, so §20.6's
  one exception does not apply and the two are the same string.
- **Focus lands on the title**, which is §20.6's flat rule for every sheet: *the title, not
  the first action*. This sheet has no action at all, which makes it the easiest case.
- **No `returnFocusTo`.** Up to four faces open this sheet from one card, so there is no one
  control to return to — the pool's own precedent, cited in `BuilderScreen` for `SH.whyfit`.
- **Four regions, four elements.** Header, skill card, record card and tag row each merge into
  one label under §20.1: the sheet has no interactive element inside it, so every group is
  actionless and merges to the nearest heading.
- **Never colour alone.** Every tinted figure is printed as a number beside its own words —
  `9 of 9` beside the meter, the score beside the pill, `· you too` inside the tag.
  Part 13, and the same order the shared-tag tint already takes.

---

## 7. Design-system amendments (Part 16 rows)

Part 15 is the mechanism and Part 16 is where a change lands. Five rows, and **only the last
one is a new number**:

| § | Amendment | Why it is not an ADR |
| --- | --- | --- |
| **7.3** Meter and bar | `Meter` gains `tone`, three values, existing semantic colours | 15.2 forbids inventing a colour; this invents none. The meter's *hidden* contract is untouched, and §6.5 re-argues it rather than inheriting it |
| **7.5** The level bar | the `legend`-less form gets its first shipped consumer | no change to the component |
| **7.13** The record block | the five squares become `shared/ui/LastFive`; the block's stale *"confirming results"* clause is struck (§2.3) | an extraction and a correction |
| **7.16** The photo panel | a second `size`, with the mark's fit **re-derived** at it | 2.5's pinned `photoScrim` and its worst case are unchanged |
| **New 7.18** The sport pill | dot + abbreviation + level, in the sport's own hue | a new component, and it satisfies `theme.ts`'s standing condition: *"every one carries the sport name on screen"* |

**No new colour, no new size step, no new radius.** Both threshold ladders — the ratio tones
and the score pill — are steps in an existing fill, which is exactly what 15.2 permits and
what `FitPill`'s own `FIT_HIGH = 90` already is. Each is declared as a named constant beside
its component and tested, so *90* and *70* exist once each.

---

## 8. The records this needs

| # | Record | What it settles |
| --- | --- | --- |
| **A** | **ADR — *A record is read through the thing that entitles you to it*** | The citation gate as a general shape: the credential is a query parameter, the resource is the person, and `challenge_id` / `game_id` join later without a second route. Cites ADR-0104 (the record never expires), ADR-0130 (a withheld row `404`s and the gate is not named), and `ForecastRequest`'s precedent |
| **B** | **ADR — *A record is assembled from five contexts and stored in none*** | `player_record` as `player_score`'s mirror: one route out, every port in, no table, no migration, and a test that fails if one appears. Also files §4.7's move of `CardIdentity` to `player_profile` |
| **C** | **Amend ADR-0107** | Two clauses. The card's list **stays closed** — nothing here is added to it. And the ADR's *"a batch profile route would make the shortlist arrive as twenty grey rectangles"* is narrowed to what it always argued: it is about a **list**, and a sheet opened by a deliberate tap is the case where a second request is right |
| **D** | **Amend ADR-0098** | Opponent variety returns as `player_record`'s demand and `player_record` signs for it, which is what the withdrawal said would happen |
| **E** | **Amend `the-words.md` §20.6 and §20.8** | The sheets are **four, not three**; §20.8's flat `progressbar` rule is re-argued at its own justification and **kept**; §20.4.1's two routes become two answers |
| **F** | **`CONTEXT.md`** | *Player record* enters the glossary as a **surface**, and *Opponent variety* moves from "no consumer" to "`player_record`'s, with a floor of 5" |

**Three refusals are recorded as refusals, not as gaps** — C1, C2 and C3 — each in the ADR
that already holds the argument, so that the next person who reads the design and reaches for
*active now* finds the answer instead of the temptation.

---

## 9. Copy — `the-words.md` §25

Every string lands in the one copy deck, in a new section beside §22–§24. Nothing below is a
component's:

```
Player record                     the sheet's title, and its accessible name
How others see you                the title when is_self
(you)                             after your own handle
THE RECORD — COUNTED BY THE
SYSTEM, NOT WRITTEN BY PEOPLE     the record card's title, verbatim, and the rule it enforces
Shows up                          SHOWS_UP
Answers challenges                ANSWERS_CHALLENGES
Opponent variety                  the variety row
{good} of {opportunities}         the raw fraction — one pluralisation-free form, deliberately
{n} % sure                        confidence, in the headline row
{n} counted                       counted games — through §J4's pluralisation helper
ON COURT                          reused; OnCourtMark owns it
· you too                         reused; socialTagChip owns it
```

**Two sentences are deliberately absent.** There is no *"no record yet"* and no *"not enough
games"*: an absent panel is **not drawn**, which is the same spelling absence has on the card,
in the record block and on the meta line. A sheet that explained its own gaps would be
teaching a stranger to read a stranger's silence.

---

## 10. Build order

Each ticket is independently mergeable and green on its own; the branch is green at the end.

| # | App | Ticket | Depends on |
| --- | --- | --- | --- |
| 1 | root | Records **A**, **B**, **C**, **D** and the `CONTEXT.md` rows | — |
| 2 | backend | Move `CardIdentity` / `PlayerCardSource` / `CardPhotoLinks` to `player_profile`; `matchmaking` imports from there. No behaviour change | 1 |
| 3 | backend | `RatedSportsQuery` on `rating`; `OpponentVarietyQuery` on `games`; `domain/variety.py` with its floor | 2 |
| 4 | backend | `RecordEntitlement` on `matchmaking`, off the search record. Gate tests **first** — including *a refused read touches no provider* | 2 |
| 5 | backend | `player_record`: domain, `sport_to_print`, assembler, both routes, schemas. `make gen-api` | 3, 4 |
| 6 | frontend | Design-system Part 16 rows: `Meter.tone`, `LastFive` extraction, `PhotoPanel` size, new 7.18 | — |
| 7 | frontend | `features/player_record/` — the four sections, the mapper, the hook, `recordPresentation` | 5, 6 |
| 8 | frontend | Wire it up: the forecast card's faces open `SH.player`, the seat hold keeps `SH.whyfit`, your own face becomes a button | 7 |
| 9 | root | `the-words.md` §25 and the §20.4.1 / §20.6 / §20.8 amendments | 8 |

**6 runs in parallel with 3–5**; it depends on no contract. **1 gates everything**, which is
the point: three of this document's five collisions are decisions, and building past a
decision is how a refusal quietly becomes a feature.

---

## 11. What this document does not decide

- **Whether languages ship at all**, or where a language field would live (C2).
- **Whether sportsmanship ever becomes a live strand**, what surface collects it, and what
  turning it on does to every published score in the product (C4).
- **The green card and the red card.** Excluded by the request. Both are *dated facts*, and a
  date on this sheet is C1's refusal — so whichever record admits them has to answer C1 first,
  for that shape.
- **Whether the loop's chat header and game screen open this sheet.** The route is built to
  accept their citations; nothing here draws their entry points.
- **`SH.playersocial`.** K-7 removed two sheets. This brings back one.
