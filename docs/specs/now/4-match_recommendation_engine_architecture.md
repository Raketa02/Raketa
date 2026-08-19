# The Match Recommendation Engine

*The engine that builds "Best fit for you" and "Full, but worth waiting for" — and every lane that comes after them. An analysis of the proposed design, and the architecture I would build instead.*

---
---

# PART 0 — YOUR PROPOSAL, ASSESSED

## 0.1 What you proposed

One engine that:

- builds the suggested-match list under the enrolled strip
- divides it into best-fit **open** matches and best-fit **full** matches worth waitlisting
- scores by the seven weighted factors
- is extensible to future list types — friends' matches and others
- publishes the result to the player app

## 0.2 What is right about it

**The seven-factor score is the correct core, and it should not be replaced.** It is explainable, it is deterministic, and its three reasons are a product surface rather than a diagnostic. A learned ranker would score better on some metric and lose the thing that makes the badge trustworthy — see §9.4.

**Splitting open from full is the right first division**, and the reason is not cosmetic: they are different asks. *Join this* and *wait for this* need different floors, different copy, and different actions.

**Anticipating more list types is the most valuable thing in your proposal.** Most teams build two sections with an `if`, then discover that the third one needs its own retrieval, its own floor and its own empty state, and the `if` becomes a nest. Designing for the third lane before it exists is exactly right.

**"All the matches must have value for the user"** is the correct constraint, and it has a specific architectural consequence most recommendation systems get wrong: **the engine must be able to return nothing.** No relaxation fallback, no padding, no widening the criteria until something appears.

## 0.3 Three problems

### Problem 1 — "One engine" hides four different cost profiles

Retrieval, filtering, scoring and ranking have nothing in common operationally:

| Stage | Cost per candidate | Candidates | Scales with |
|---|---|---|---|
| Retrieval | ~0 (index) | all city matches | city size |
| Eligibility | ~1 µs | ~150 | retrieved |
| **Scoring** | **~500 µs cold** | ~100 | **survivors × player** |
| Ranking | ~1 µs | ~100 | survivors |

**Scoring is three orders of magnitude more expensive than everything else**, and it is the only stage that scales with *players × matches*. A single component that does all four will have its cheap stages written in the shape of its expensive one, and the expensive one will run on candidates that a two-field comparison would have removed.

At 500 open matches in a city, scoring everything is **250 ms per request**. Scoring the 100 that survive a cheap filter, with a shared context cache, is **2 ms**. That is the whole ballgame, and it comes from the stage boundary, not from optimisation.

### Problem 2 — "Publishes to the player app" imports the wrong delivery model

The enrolled-match strip is **pushed**: a materialized per-player list, patched reactively over a socket. It is natural to assume the feed below it works the same way.

**It must not, and the reason is fan-out.**

```
Enrolled strip:  one match changes → ≤ 4 players' lists change
Best-fit feed:   one match changes → EVERY player whose candidate set contains it
```

One match filling in Kraków at 18:00 on a Saturday changes the correct feed for potentially every padel player in the city. A push architecture would have to either recompute thousands of feeds per event or maintain a reverse index from match to interested player — and the second is a materialized cross product that grows as *players × matches*.

**And the player has no stake.** A stale enrolled card can be about money that has moved. A stale feed card is a suggestion that is forty seconds old. Those deserve different guarantees and different machinery.

### Problem 3 — "Divided in two" is a shape, not an abstraction

Two sections in code as *open* and *full* means the third lane — friends' matches — arrives as a third branch, and the fourth as a fourth. Each will want its own retrieval, floor, cap, copy and empty behaviour, and those will end up interleaved through one function.

The abstraction you want is not *two lists*. It is **a lane**: a named, independently retrieved, independently filtered, independently scored, independently capped section, declared as data.

## 0.4 The three corrections

| # | From | To |
|---|---|---|
| **1** | One engine | **A four-stage funnel** with a hard boundary before scoring |
| **2** | Published like the enrolled strip | **Computed on read, cached briefly, verified at tap** |
| **3** | Two hard-coded sections | **N declarative lanes**, composed |

---
---

# PART 1 — THE DECISION THAT SHAPES EVERYTHING

## 1.1 Push versus pull — and why this feature gets the opposite answer

| | Enrolled strip | Best-fit feed |
|---|---|---|
| Set size | ≤ 5 | ~3 shown, ~100 considered |
| Fan-out per change | ≤ 4 players | potentially every player in the city |
| Player's stake | **money, commitment** | none yet |
| Cost of being 60 s stale | **a wrong money position** | a suggestion is slightly out of date |
| Cost of being wrong at tap | confusion | **the match is gone — trust damage** |
| Correct model | **push, materialized** | **pull, cached, verified at tap** |

**The two features look adjacent on screen and are opposite in every operational property.** Building them the same way is the single easiest architectural mistake to make here, and it is expensive in both directions: pushing the feed is a fan-out disaster, and pulling the enrolled strip loses the reactivity that makes the product feel alive.

## 1.2 Splitting the freshness contract

This is the insight that makes a cached feed trustworthy. **A feed card is two things with two different freshness requirements.**

| Part | Contents | Tolerable staleness | Why |
|---|---|---|---|
| **Ranking** | the score, the order, the reasons | **60 seconds** | A match that was the best option a minute ago is still a good option. Nobody is harmed |
| **Joinability** | seats left, state, price, cutoff | **zero at the moment of tap** | Tapping a match that filled 40 seconds ago is the failure that destroys trust |

**So: cache the ranking, verify the joinability.**

```
GET /now        → feed from cache (≤60 s old). Fast, cheap, good enough
TAP a card      → re-verify joinability against live state before opening
```

**The tap verification is the trust mechanism**, and it costs one indexed read on an action the player already expects to take a moment. It converts the one unacceptable failure into a graceful one: *"This one just filled — here are two others"*, with the two others already in hand.

## 1.3 What the engine is allowed to do when it finds nothing

> *"We do not invent players to make a city look busy."*

This is a hard architectural constraint, not copy. **No stage may relax a criterion to produce output.** No widening the radius when the list is short, no dropping the sport filter, no lowering a lane's floor to fill three slots.

**An empty list is a true answer**, and saying so is what makes a full list believable. The engine returns what qualifies, and if that is nothing, the lane renders its empty state.

---
---

# PART 2 — THE ARCHITECTURE

## 2.1 The funnel

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                          FEED REQUEST                                  │
  │              (playerId, sport filter, surface, now)                    │
  └───────────────────────────────┬────────────────────────────────────────┘
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ① RETRIEVAL          index only · no scoring · high recall            ║
  ║     "which matches could plausibly matter to this player at all?"      ║
  ║     500 city matches ──────────────────────────────▶ ~150              ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ② ELIGIBILITY        binary · cheap · REASON-CARRYING                 ║
  ║     "which of those could this player actually join?"                  ║
  ║     ~150 ──────────────────────────────────────────▶ ~100              ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ③ SCORING            expensive · pure · explainable                   ║
  ║     the seven weighted terms + three modifiers                         ║
  ║     ~100 scored, each with reasons and a warning                       ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ④ LANE ASSEMBLY      per-lane floor · sort · diversify · cap          ║
  ║     open lane: top 3 · full lane: ≥80, top 1                           ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ⑤ COMPOSITION        dedupe across lanes · global caps · order        ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
  ╔════════════════════════════════════════════════════════════════════════╗
  ║  ⑥ RENDERING          card view models · copy · empty states           ║
  ╚═══════════════════════════════╤════════════════════════════════════════╝
                                  ▼
                            FEED  +  TRACE
```

**The boundary between ② and ③ is the one that matters.** Everything above it is a comparison; everything below it is arithmetic over levels and forecasts. **Nothing expensive may run above the line, and nothing may reach the line that a cheap test could have removed.**

## 2.2 Where the lanes live

Lanes do not sit alongside the funnel. **Each lane declares its own ① and ②, shares ③, and owns its ④.**

```
                      ┌──────────────┐
                      │  FeedRequest │
                      └──────┬───────┘
                             │
      ┌──────────────────────┼──────────────────────┐
      ▼                      ▼                      ▼
 ┌─────────┐           ┌─────────┐            ┌─────────┐
 │ LANE:   │           │ LANE:   │            │ LANE:   │   ← future
 │ open    │           │ full-   │            │ friends │
 │ best fit│           │ worth   │            │ playing │
 └────┬────┘           └────┬────┘            └────┬────┘
      │ ① retrieval         │ ① retrieval          │ ① retrieval
      │ ② eligibility       │ ② eligibility        │ ② eligibility
      └──────────┬──────────┴──────────────────────┘
                 ▼
        ┌──────────────────┐
        │ ③ SCORER         │  ← ONE scorer, shared. One definition of fit
        │   (shared cache) │
        └────────┬─────────┘
                 │
      ┌──────────┼──────────────────────────────┐
      ▼          ▼                              ▼
 ④ floor 0   ④ floor 80                    ④ floor 60
   cap 3       cap 1                          cap 2
      └──────────┴──────────────┬──────────────┘
                                ▼
                        ⑤ COMPOSITION
```

**One scorer, many lanes.** This is the constraint that keeps the product coherent: an 84 in the friends lane means exactly what an 84 in the best-fit lane means. If lanes could score differently, the badge would stop meaning anything, and the badge is the product.

## 2.3 The seven governing rules

| # | Rule | Consequence |
|---|---|---|
| **I** | **Cheap before expensive, always** | Scoring never runs on a candidate a comparison could have removed |
| **II** | **One scorer, shared by every lane** | An 84 means one thing everywhere |
| **III** | **Never relax to fill** | Empty is a true answer. No padding, ever |
| **IV** | **Ranking may be stale; joinability may not** | Cache the order, verify at tap |
| **V** | **Deterministic and total** | Same inputs, same list, every time — including the tie-break |
| **VI** | **Every inclusion and every exclusion has a reason** | The three reasons ship to the UI; the exclusions ship to the trace |
| **VII** | **A lane is data, not a branch** | Adding one touches no pipeline code |

---
---

# PART 3 — THE STAGES

## 3.1 ① Retrieval — index only

**Purpose:** get from *every open match in the city* to *the plausible few*, using only predicates a database index can answer.

```ts
interface RetrievalStrategy {
  readonly id: string;
  retrieve(req: FeedRequest, store: MatchIndex): Promise<readonly MatchId[]>;
}
```

**Best-fit open lane:**

```sql
SELECT id FROM matches
WHERE city       = $city
  AND kind       = 'open'
  AND sport      = ANY($sports)          -- the player's sport filter
  AND start      > $now
  AND join_cut   > $now                  -- the club still accepts joins
  AND seats_free > 0
  AND terminal   = false
  AND club_id    = ANY($clubs_within_travel)
ORDER BY start
LIMIT 300
```

**Full-worth lane:** identical except `seats_free = 0`.

**Four properties this stage must have.**

**High recall, low precision.** Retrieval's job is to lose nothing that could rank; precision is stage ②'s job. A retrieval predicate that is *nearly* right and occasionally drops a good match is worse than one that returns 50 extra rows.

**No fit computation.** Not a level comparison, not a forecast. If a predicate needs a player's rating, it belongs in ② or ③.

**`seats_free` and `terminal` are denormalised columns**, maintained by the match write path. Computing them per row at retrieval time is the difference between an index scan and a table scan.

**The `LIMIT` is a safety valve, not a product decision.** 300 is far above what survives, and it exists so a misconfigured filter cannot pull a city.

## 3.2 ② Eligibility — binary, cheap, and it explains itself

**Purpose:** remove everything the player genuinely cannot or should not join, and **record why**.

```ts
interface EligibilityRule {
  readonly id: string;
  readonly exclusionReason: ExclusionReason;
  isSatisfiedBy(m: MatchSnapshot, ctx: PlayerContext): boolean;
}

const OPEN_LANE_RULES: readonly EligibilityRule[] = [
  new NotAlreadyMine(),        // I hold a seat → 'already-enrolled'
  new NotOnWaitlist(),         // I'm queued    → 'already-waitlisted'
  new StartsInFuture(),        // → 'started'
  new BeforeJoinCutoff(),      // → 'joining-closed'
  new HasFreeSeat(),           // → 'full'
  new NotCancelled(),          // → 'cancelled'
  new SportMatchesFilter(),    // → 'filtered-out'
  new WithinTravelCeiling(),   // → 'too-far'
  new NoScheduleConflict(),    // → 'clashes'      ← see below
  new NotSuppressed(),         // → 'suppressed'   ← v2 slot
];
```

**Evaluate all rules; do not short-circuit.** The trace needs the full exclusion histogram, and *"nine candidates, seven of them already full"* is a different operational story from *"nine candidates, seven of them too far."* One is supply; the other is a filter set badly.

**`NoScheduleConflict` is the rule your proposal is missing and players will notice immediately.** A match that overlaps one the player is already enrolled in is not a recommendation, it is a mistake — and the engine has the enrolled list right there.

**`NotSuppressed` is a v2 slot, deliberately empty at launch.** Impression capping, dismissals, and *"stop showing me this club"* all land here. Declaring the slot now means adding them later is one rule, not a refactor of the pipeline.

## 3.3 ③ Scoring — the expensive stage, and the shared cache that makes it cheap

The seven terms, unchanged:

| Term | Weight | Value |
|---|---|---|
| Skill overlap | **30** | `max(0, 1 − \|myLevel − target\| / 0.55)` |
| Predicted balance | **20** | `forecast.pct / 100` · default **0.70** |
| Group reliability | **15** | `(0.5·min + 0.5·mean) / 100` · default **0.80** |
| Time and travel | **15** | `max(0, 1 − max(0, dist − 20) / 18)` |
| Match type | **8** | counted 1.0 · friendly 0.72 |
| Price vs ceiling | **7** | `clamp(0, 1, 1 − (payable − 30) / 30)` |
| Preferences and side | **5** | 0.9 |

Modifiers after the sum, before the clamp: **+8** promotion · **+5** all-new opponents · **−8** the same four again. Clamp **20–99**.

### The split that makes this affordable

**Most of the work is player-independent.** Split the computation:

```ts
// Computed ONCE per match. Reused by every player who scores it.
type MatchScoringContext = {
  matchId: MatchId;
  seatTarget:   Level | null;      // ← the 401-candidate grid lives HERE
  targetBand:   [Level, Level] | null;
  seatedLevels: readonly Level[];
  seatedSigmas: readonly Sigma[];
  minReliability: number;
  meanReliability: number;
  counts: boolean;
  clubDistanceMin: number;
  share: SeatShare;
  builtAt: Instant;
  recordVersion: number;           // invalidates when the match changes
}

// Player-relative, and cheap
score(ctx: MatchScoringContext, player: PlayerContext): Decision<FitScore>
```

**The measured effect:**

```
Without the context cache:  100 candidates × 500 µs  =  50 ms   ← per request
With it, warm:              100 candidates ×  20 µs  =   2 ms
```

**`seatTarget` is the whole cost** — a 401-candidate grid over three pairings — and it depends only on the *seated levels and the sport*, not on who is asking. Computing it once per match and reusing it across every player who sees that match is a 25× win and it is not a micro-optimisation; it is what makes the feature viable at city scale.

**Invalidation is by `recordVersion`**, which the match write path already maintains. A seat payment bumps the version, the context is rebuilt on next use. No TTL, no reverse index, no staleness — the key *is* the version.

### The reasons are a return value, not a log

```ts
type FitScore = {
  score: number;                        // 20..99
  terms: readonly Term[];               // seven, with weight, value, contribution, sentence
  mods:  readonly Modifier[];
  reasons: readonly [string, string, string];   // top 3 BY CONTRIBUTION
  warn: string | null;                  // lowest contribution IF its RAW value < 0.55
  target: Level;
  version: EngineVersion;
}
```

**Two quantities, deliberately different.** Reasons rank by **contribution** (`weight × value`); the warning fires on **raw value**. A term can be last by contribution and still be perfectly fine in itself, and in that case no warning is shown. That asymmetry is easy to lose in a rewrite and it is worth a test.

**The sentences are produced inside the term evaluation**, by the same call that produced the value — so the explanation and the arithmetic cannot drift apart.

### Determinism and the tie-break

Scores are integers 20–99 over ~100 candidates. **Ties are common, and an unstable sort means the list reshuffles between two identical requests.** That looks broken and it is broken.

```ts
const FEED_ORDER: Comparator<Scored>[] = [
  descending(byNumber(x => x.fit.score)),   // 1. fit
  ascending (byNumber(x => x.match.start)), // 2. sooner is better
  ascending (byNumber(x => x.club.dist)),   // 3. nearer is better
  ascending (byString(x => x.match.id)),    // 4. TOTAL — never returns 0
];
```

**The fourth comparator is not decoration.** Without a guaranteed-total final key, the order depends on retrieval order, which depends on the query plan. A development-mode assertion should fail if any two distinct candidates compare equal through the whole chain.

## 3.4 ④ Lane assembly — floor, sort, diversify, cap

```ts
type LaneConfig = {
  id: string;
  title: string;
  subtitle: string | null;
  retrieval: RetrievalStrategy;
  rules: readonly EligibilityRule[];
  floor: number | null;                 // minimum fit
  cap: number;                          // max cards
  diversity: DiversityPolicy | null;
  emptyState: EmptyState | null;        // null = render nothing at all
  enabled: (ctx: PlayerContext) => boolean;
}
```

### The two launch lanes

```ts
const BEST_FIT_OPEN: LaneConfig = {
  id: 'best-fit-open',
  title: 'Best fit for you',
  subtitle: 'Ranked on seven things, not just level',
  retrieval: new OpenMatchesNearby(),
  rules: OPEN_LANE_RULES,
  floor: null,                          // ← no floor on Now. See below
  cap: 3,
  diversity: new MaxPerClubHour(2),
  emptyState: NOTHING_OPEN,
};

const FULL_WORTH_WAITING: LaneConfig = {
  id: 'full-worth-waiting',
  title: 'Full, but worth waiting for',
  subtitle: 'These fit you as well as anything above, and seats do come free. ' +
            'Joining a waitlist costs nothing and commits to nothing.',
  retrieval: new FullMatchesNearby(),
  rules: FULL_LANE_RULES,
  floor: 80,                            // ← STRICTER. See below
  cap: 1,
  diversity: null,
  emptyState: null,                     // ← renders NOTHING when empty
};
```

**Why no floor on the open lane.** A player with nothing booked needs a suggestion more than they need a purity threshold. If the best available is a 62, that is the honest answer and the badge says 62. The Find screen, which is a browsing surface rather than a suggestion surface, splits at 80 into *best fit* and *above your band*.

**Why 80 on the waitlist lane.** Asking a player to *wait* for something is a bigger ask than asking them to *join* something. It has to be genuinely good, or the section teaches them to ignore it.

**Why the full lane's empty state is `null`.** It renders nothing at all — not an empty card, not a reassurance. A section that appears every time saying *"no full matches worth waiting for"* is a section players learn to scroll past.

### Diversification

```ts
class MaxPerClubHour implements DiversityPolicy {
  constructor(private readonly max: number) {}
  apply(ranked: readonly Scored[], cap: number): readonly Scored[] {
    const seen = new Map<string, number>();
    const out: Scored[] = [];
    for (const c of ranked) {
      const key = `${c.match.club}|${hourBucket(c.match.start)}`;
      if ((seen.get(key) ?? 0) >= this.max) continue;
      seen.set(key, (seen.get(key) ?? 0) + 1);
      out.push(c);
      if (out.length === cap) break;
    }
    return out;
  }
}
```

**Three cards at the same club at the same hour is a worse list than three cards at three times, even when the scores disagree.** The player's real question is *when can I play*, and three answers to one hour answers it once.

**This is a re-ranking rule, applied after scoring, never inside it.** Putting diversity into the score would corrupt the number the badge shows — an 84 would no longer mean *"this match fits you 84"* but *"this match fits you 84 and happens to be at a club we have not shown yet."*

## 3.5 ⑤ Composition — dedupe and global rules

```ts
compose(lanes: LaneResult[], policy: FeedPolicy): Feed
```

**Dedupe across lanes, first lane wins.** Open and full are disjoint today, so this is a no-op — but the friends lane will overlap best-fit immediately, and a match appearing twice in one scroll is the most obvious possible bug.

**Lane order is declared, not scored.** Best-fit first because it is the most actionable; full-worth second because it is the fallback.

**Global cap.** The whole feed on Now is capped at six cards regardless of how many lanes exist. **A recommendation surface that grows without bound stops being a recommendation.**

## 3.6 ⑥ Rendering

The `matchCard` view model per the Now specification. Every string server-side, so the two applications cannot disagree.

**The trace is built here too and is not shipped to the client:**

```ts
type FeedTrace = {
  requestId: string;
  retrieved: number;
  excluded: Record<ExclusionReason, number>;
  scored: number;
  perLane: { laneId: string; belowFloor: number; diversityDropped: number; shown: number }[];
  scorerVersion: EngineVersion;
  timings: Record<StageId, number>;
  cache: { contextHits: number; contextMisses: number };
}
```

**The exclusion histogram is the single most valuable operational artefact this engine produces.** *"Feed was empty for 400 players in Kraków last Tuesday"* is unactionable. *"Feed was empty because 91% of candidates were excluded as `too-far`"* is a filter default set wrong, and it is a one-line fix.

---
---

# PART 4 — ADDING A LANE

**The test of the architecture: how much code does a new lane require?**

## 4.1 Friends' matches — the lane you named

```ts
const FRIENDS_PLAYING: LaneConfig = {
  id: 'friends-playing',
  title: 'Your friends are playing',
  subtitle: null,
  retrieval: new MatchesContainingAnyOf(ctx => ctx.social.friendIds),
  rules: [...OPEN_LANE_RULES],            // identical eligibility
  floor: 60,                              // lower — the social pull is real value
  cap: 2,
  diversity: null,
  emptyState: null,                       // renders nothing
  enabled: ctx => ctx.social.friendIds.length > 0,
};
```

**One retrieval strategy and one config object.** No change to the funnel, the scorer, the composer or the renderer.

**Note the floor at 60 rather than the open lane's none.** A friends lane that showed a 34 would be recommending a bad match on social grounds, and the seven-factor score is what stops that. **The lane can weight *inclusion*; it cannot change what the score means.**

## 4.2 Four more, to prove the shape holds

| Lane | Retrieval | Floor | Cap | Notes |
|---|---|---|---|---|
| **Fill a gap in your week** | Matches in the player's declared free windows | 55 | 2 | Reads the intent-pool declarations |
| **New at your home club** | Matches created in the last 24 h at the club they play most | 65 | 2 | `createdAt > now − 24h` |
| **Your level, tomorrow morning** | Time-bucketed retrieval | 70 | 3 | Same everything, different window |
| **Nearly full — one seat left** | `seats_free = 1` | 75 | 2 | Urgency lane. Same score, higher floor |

**Every one of them is a config object plus at most one retrieval strategy.** If a proposed lane needs a change to the scorer, that is the signal to stop and ask whether it is really a lane or really a different product.

## 4.3 The rule that keeps this honest

> **A lane may choose *which* matches it considers and *how good* they must be. It may never change *what good means*.**

Break this and the badge dies. Two lanes scoring differently means an 84 in one place and an 84 in another are different claims, and the player has no way to know which is which.

---
---

# PART 5 — TRUST

*The requirement you stated most strongly, and the one with the most specific architecture behind it.*

## 5.1 The four ways this feature can lose trust

| Failure | Player experience | Defence |
|---|---|---|
| **A card that cannot be joined** | Taps, gets an error. **Worst case** | Tap-time verification (§5.2) |
| **A card that is a bad suggestion** | Learns to ignore the section | Floors, diversification, no padding |
| **A list that reshuffles for no reason** | Feels random, distrusts the badge | Total ordering (§3.3) |
| **A score that cannot be explained** | Badge becomes noise | Three reasons, always shipped |

## 5.2 Tap-time verification

```ts
async function openMatch(matchId: MatchId, ctx: PlayerContext) {
  const live = await matches.load(matchId);           // ONE indexed read
  const check = verifyJoinable(live, ctx, clock.now());

  if (check.ok) return openDetail(live);

  return openDetailWithNotice(live, {
    reason: check.reason,                             // 'full' | 'cancelled' | 'joining-closed'
    alternatives: cachedFeed.othersFrom(matchId, 2),  // already in hand
  });
}
```

**This converts the unacceptable failure into a graceful one.** *"This one just filled — here are two others"* with the two others already on screen is a recoverable moment. A generic error is not.

**The alternatives come from the cached feed the player is already holding**, which costs nothing and is exactly what a person would want next.

## 5.3 Output invariants — assert, do not assume

```
 1  every card is joinable AS OF BUILD TIME
 2  no card appears twice in the feed
 3  every card's fit ≥ its lane's floor
 4  every lane is sorted by the FEED_ORDER chain
 5  no lane exceeds its cap
 6  the diversity policy holds
 7  every card has exactly three reasons
 8  a warning is present ⟺ the lowest-contribution term's RAW value < 0.55
 9  the same request twice, same world → byte-identical feed
10  the scorer NEVER runs on a candidate that failed eligibility
11  no stage relaxed a criterion to produce output
12  weights sum to exactly 100
13  every score ∈ [20, 99]
14  no card overlaps a match the player is already enrolled in
```

**Invariants 9 and 11 are the ones that would silently degrade.** Non-determinism looks like a redesign nobody asked for; relaxation looks like generosity and is a lie.

**Run 1–8 as an output assertion in development and as a sampled check in production.** A feed that violates one should be logged with its full trace, not silently served.

## 5.4 Changing the scorer safely

The weights will move — the price ceiling is unresolved, preferences is a placeholder, and `REGULARS` is a stub.

**The procedure, every time:**

1. New weights ship behind a new `EngineVersion`, **disabled**.
2. **Shadow mode:** score every real request with both, log both feeds, serve the old one.
3. Compare over a week: how often does the top card change? How often does the top-3 set change? Where do the biggest movements come from?
4. Ship when the diff is understood — **not when it is small.**

**Step 3 is the one that gets skipped.** *"Changing the price weight from 7 to 10"* sounds small; the shadow log says exactly how many players' top recommendation changes, and which term is doing it.

**Stamp the version on every shown card.** A recommendation shown as a promise must be reproducible later, and the same mechanism gives free A/B.

## 5.5 Kill switches

```ts
type FeedPolicy = {
  lanes: LaneConfig[];
  globalCap: number;
  scorerVersion: EngineVersion;
  killed: Set<LaneId>;              // ← operational, per lane
  degradeMode: 'off' | 'recency';   // ← if the scorer fails
}
```

**Per-lane kill switch.** A misbehaving friends lane is turned off without a deploy and without touching best-fit.

**Degrade mode.** If the scorer throws or exceeds its budget, the lane serves **soonest-first with no badge** rather than nothing. Cards without a fit score are honest — the badge is simply absent — and a feed with no ranking is better than no feed.

---
---

# PART 6 — CACHING AND PERFORMANCE

## 6.1 Two caches, two invalidation strategies

| Cache | Key | Invalidated by | Lifetime |
|---|---|---|---|
| **Match scoring context** | `matchId : recordVersion` | **The version key itself** — never stale | until evicted |
| **Player feed** | `playerId : sportFilter : surface` | **TTL 60 s**, plus explicit on the player's own actions | 60 s |

**The context cache is version-keyed, so it cannot be stale.** A seat payment bumps `recordVersion`, the old key is simply never read again. No invalidation message, no reverse index, no race.

**The feed cache is TTL'd, and that is a deliberate choice over targeted invalidation.** Targeted invalidation would need a reverse index from every match to every player whose cached feed contains it — a materialized cross product that grows as *players × matches* and must be maintained transactionally. **The tap verification already covers the only dangerous staleness**, so the index would buy freshness nobody can perceive at a cost that scales badly.

**Explicit invalidation on the player's own actions**, because those they *will* perceive:

```
player joins a match      → drop their feed cache  (it must vanish from the list)
player creates a match    → drop
player joins a waitlist   → drop
player changes sport      → different key, no drop needed
```

## 6.2 The budget

| Stage | Cold | Warm |
|---|---|---|
| Retrieval (2 lanes) | 8 ms | 8 ms |
| Eligibility, ~150 candidates | 0.5 ms | 0.5 ms |
| **Context build**, ~100 matches | **50 ms** | **0 ms** |
| **Scoring**, ~100 candidates | 2 ms | 2 ms |
| Assembly + composition | 0.5 ms | 0.5 ms |
| Rendering, 4 cards | 1 ms | 1 ms |
| **Total** | **~62 ms** | **~12 ms** |
| **Served from feed cache** | — | **< 2 ms** |

**Context build is the only expensive thing**, it is shared across every player, and it warms within seconds of a match being created. On a busy evening the hit rate is effectively 100%.

**Budgets fail the build when exceeded**, measured at p99 with 500 live city matches.

## 6.3 What happens at ten cities

| Quantity | One city | Ten cities |
|---|---|---|
| Live open matches | ~500 | ~5,000 |
| Retrieved per request | ~150 | ~150 — *city-scoped, unchanged* |
| Scored per request | ~100 | ~100 — *unchanged* |
| Context cache entries | ~500 | ~5,000 |
| Feed requests / min, peak | ~2,000 | ~20,000 |

**The per-request cost does not grow with the platform**, because retrieval is city-scoped and everything downstream is bounded by what retrieval returns. Growth is absorbed by the context cache, which is small and shared, and by horizontal replicas of a stateless pipeline.

**The first thing to change at scale is not the algorithm; it is sharding the context cache by city.**

---
---

# PART 7 — DESIGN PATTERNS

## 7.1 Applied

| Pattern | Where | The problem it solves |
|---|---|---|
| **Pipeline / Chain of stages** | The funnel | Cost isolation. Cheap work cannot accidentally sit below expensive work |
| **Strategy** | `RetrievalStrategy` | A new lane brings a query, not a branch |
| **Specification with reasons** | `EligibilityRule` | Composable, testable, and the exclusion histogram falls out |
| **Composite of weighted terms** | The seven factors | Each is one class. The four placeholder terms are replaceable in isolation |
| **Flyweight** | `MatchScoringContext` | Player-independent state computed once, shared by every player. **The 25× win** |
| **Declarative configuration** | `LaneConfig` | A lane is data. Adding one touches no pipeline code |
| **Decision envelope** | `FitScore` with reasons | The explanation cannot drift from the arithmetic |
| **Version stamping** | `EngineVersion` | Reproducible recommendations, free A/B, safe weight changes |
| **Total comparator chain** | `FEED_ORDER` | Determinism. Identical requests give identical lists |
| **Circuit breaker + degrade** | Scorer failure | Recency-ordered feed beats no feed |
| **Post-ranking policy** | `DiversityPolicy` | Diversity without corrupting the score's meaning |

## 7.2 Deliberately refused

| Pattern | Where tempting | Why not |
|---|---|---|
| **Learned ranker (LTR / embeddings)** | "Better relevance" | **The reasons are the product.** A model that scores 3% better and cannot say *"the open seat needs 2,54 and you are 2,71"* is a worse product. See §9.4 |
| **Push/materialize like the enrolled strip** | Symmetry | Fan-out is *every player in the city* per match event. §1.1 |
| **Precomputed player × match scores** | "Fast reads" | A cross product that must be invalidated on both axes. The context cache gets most of the win at none of the cost |
| **Targeted feed invalidation** | "Always fresh" | A reverse index growing as players × matches, to fix staleness the tap-verify already covers |
| **A separate scorer per lane** | Lane-specific tuning | Kills the badge's meaning. Lanes tune inclusion, never definition |
| **Relaxation fallback when empty** | "Never show an empty list" | *"We do not invent players to make a city look busy."* Empty is a true answer |
| **Microservice per stage** | "Scalable" | The stages share a hot cache and run in microseconds. A network hop between ② and ③ costs more than ③ |
| **Rules engine / DSL for eligibility** | Ten rules feels like a lot | Ten typed classes are readable, testable and greppable. A DSL is a second language to learn and debug |

---
---

# PART 8 — ALTERNATIVES CONSIDERED

## 8.1 Precompute every player's feed on a schedule

**Design:** a nightly or 5-minute job builds every player's feed.

**Why tempting:** reads become a single lookup.

**Why not:** matches are created and filled continuously, so a 5-minute-old feed contains matches that are gone and misses matches that are new. And it computes feeds for every player who will not open the app — at a 20% daily-active rate, 80% of the work is discarded. **The funnel computes on demand in 12 ms warm**, which is faster than the read this would replace once you account for cache misses.

## 8.2 Materialize and push, like the enrolled strip

**Why not:** §1.1. One match filling changes the correct feed for every player in the city.

**What is worth borrowing:** the enrolled strip's **version-and-heartbeat** delivery. If the feed ever becomes push-driven for a subset — a *"one seat left"* urgency lane, say — that lane can push while the rest stays pull. **The lane abstraction makes that a per-lane delivery policy rather than an architecture change**, which is a good argument for the lane abstraction independent of everything else.

## 8.3 Score everything, filter afterwards

**Why tempting:** one pass, simpler code.

**Why not:** 500 × 500 µs = 250 ms per request, of which 80% is spent scoring matches that fail a two-field comparison. **The stage boundary is the optimisation**, and it is a design decision, not a tuning one.

## 8.4 Learn the ranking from behaviour

**Why tempting:** the weights are hand-picked. A model trained on joins would likely rank better on join-rate.

**Why not, and this is the clearest refusal in the document:**

**The reasons are the product.** *"The open seat needs about 2,54 · you are 2,71"* is why the player trusts the 93. A gradient-boosted score cannot produce that sentence, and post-hoc attribution produces a *plausible* sentence rather than a *true* one — which is worse than none.

**Join-rate is the wrong target.** It rewards recommending matches that are easy to join, not matches that are good to play. The product's actual goal — an even game the player enjoys — is measured after the match, sparsely, and with a long delay.

**The weights are a product statement, not a hyperparameter.** *Skill overlap is worth thirty and price is worth seven* is a claim about what makes a good game. It should be argued about and changed deliberately, not fitted.

**Where learning genuinely belongs**, and the architecture already has slots for all three:

| Slot | What learning could supply |
|---|---|
| `PreferencesAndSide` term | Currently a hard-coded 0.9. Real preference inference belongs here |
| `NotSuppressed` rule | Impression fatigue and dismissal signals |
| `DiversityPolicy` | Learned diversity, post-ranking, without touching the score |

**Each is a bounded, replaceable component whose output stays explainable.** That is the shape a learned component should take here.

---
---

# PART 9 — BUILD ORDER

| # | Deliverable | Gate |
|---|---|---|
| **1** | `MatchSnapshot`, `PlayerContext`, `MatchIndex` with denormalised `seats_free` / `terminal` | Retrieval returns correct sets on fixtures |
| **2** | `RetrievalStrategy` + the two launch strategies | Recall check: no qualifying match is ever missed |
| **3** | `EligibilityRule` ×10, evaluated exhaustively | Exclusion histogram sums to `retrieved − survivors` |
| **4** | `MatchScoringContext` + version-keyed cache | Context is byte-identical to computing inline |
| **5** | The seven terms as a composite, sum-to-100 asserted at module load | The canonical match scores **84**, terms exact |
| **6** | Modifiers, reasons, warning — with the contribution/raw-value asymmetry | A constructed case where the last term by contribution has raw value ≥ 0.55 → **no warning** |
| **7** | `FEED_ORDER` total comparator + determinism assertion | 1,000 identical requests → byte-identical feeds |
| **8** | `LaneConfig`, `DiversityPolicy`, lane assembly | Floors, caps and diversity all enforced |
| **9** | Composition, dedupe, global cap | No card twice; lane order stable |
| **10** | Rendering + `FeedTrace` | Trace accounts for every retrieved candidate |
| **11** | Feed cache, TTL, explicit invalidation on player actions | Joining a match removes it from the feed within one request |
| **12** | **Tap-time verification + alternatives** | A match that filled between build and tap degrades gracefully |
| **13** | Shadow mode, kill switches, degrade mode | A killed lane vanishes with no deploy |
| **14** | **The friends lane** — built by someone who has not read the pipeline | **If it takes more than one config object plus one retrieval strategy, the abstraction failed** |

## 9.1 The acceptance gate

- [ ] The scorer **never** runs on a candidate that failed eligibility — asserted with a call counter
- [ ] All 14 output invariants hold
- [ ] Weights sum to 100, asserted at module load
- [ ] Identical requests produce byte-identical feeds, 1,000 times
- [ ] The tie-break chain is total — no two distinct candidates compare equal
- [ ] No stage can relax a criterion; the empty state is reachable and correct
- [ ] `MatchScoringContext` is version-keyed and provably never stale
- [ ] Warm p99 under 15 ms with 500 live city matches
- [ ] Tap verification catches a match that filled after the feed was built
- [ ] Every card ships exactly three reasons
- [ ] The `FeedTrace` accounts for every retrieved candidate — retrieved = excluded + scored
- [ ] **A new lane requires one `LaneConfig` and at most one `RetrievalStrategy`**

---

*Six stages · one scorer · N lanes · seven factors · fourteen invariants · ranking may be stale, joinability may not.*
