# Raketa — The Matchmaking Engine

**Architecture, algorithm and operations. Design document, not an implementation.**

Version 1.1 · 2026-08-25 · written against `rakieta-social-player-app-pipeline-v2.md`,
`rakieta-matchmaking-mechanics.md`, `rakietaSocialPrototype.html`, the Raketa backend as it
stands today, and `github.com/Yashh56/matchmakingEngine` as the reference implementation.

---

## 0. What this document decides, and what it does not

> **Changed in 1.1.** Two sequencing decisions moved, both in §22: the **search half of the
> telemetry chain** ships in Phase 1 rather than Phase 2, because it is unreconstructable and
> costs hours (§19.2); and **`player_score` is scheduled in Phase 0 and lands in Phase 2**
> rather than being left implicit in "ongoing", because it gates roughly a third of the
> engine's value and unscheduled work slips.

**It decides:** where the engine lives, what it is allowed to know, the algorithm it runs,
the contract it exposes, how it degrades, how it is tested, and how it is proven wrong.

**It does not decide:** the numbers. Every weight, floor and cap below is a **starting
position with a falsifying measurement attached** (§24). The mechanics document is explicit
that everything is a hypothesis until the return rate answers it, and this design's most
important structural property is that changing a weight is a *configuration release*, not a
code change (§11).

**It deliberately refuses three things** that a matchmaking engine is normally expected to do:

1. It never sends a challenge on a player's behalf. The engine proposes; the player decides.
2. It never returns a bad match to avoid returning nothing. The honest empty state ships.
3. It never produces a number it cannot explain in one sentence with the evidence named.

Those three are not garnish. They are the load-bearing constraints, and several architectural
choices below exist only to make them mechanically impossible to violate.

---

## 1. The problem, stated honestly

A player opens **Play → Find a game**, picks a sport, picks Competitive or For fun, adjusts
the 7×3 availability grid, and lands on an empty court. They press **⚡ Let the engine fill
the seats**. Something has to decide who sits down.

That is the request. Three properties of it determine the entire architecture:

**It is synchronous and interactive.** The player is looking at a search animation. The
answer must be complete in a few hundred milliseconds. There is no queue to wait in.

**The other players are not there.** Nobody else is online, waiting, pressing a button at the
same moment. The engine is ranking a mostly-dormant population and producing a *proposal*
that somebody answers within 24 hours — or does not.

**The pool is small.** A district on a Tuesday is tens to hundreds of candidates per sport,
not millions. Every naive algorithm below is fast enough. The hard problems are quality,
fairness and explanation, not throughput.

The single number that judges the result is the **return rate** — the share of first games
between two people that produce a second. A lopsided first game returns 34%; an even one
returns 71%. Everything in this document exists to move that number, and §19 says how it is
measured.

### 1.1 Two surfaces, one engine

| Surface | What it asks for | Shape of the answer |
|---|---|---|
| **Find a game → ranked candidates** | *Who could I play?* | An ordered shortlist, each with a Fit score and its reasons |
| **Find a game → ⚡ engine fills the seats** | *Give me the best line-up* | One line-up, seated and arranged, with a forecast |
| **Match me (the deck)** | *One person at a time* | A deck order, viewer's declared intent, variety spread |
| **Fill the seats (half-built game)** | *Complete this group* | A line-up optimised **for the existing group**, not for the searcher |

All four run the same pipeline with different terminal stages. There is one scoring engine
and one candidate index; there is not a second implementation anywhere, ever. Two
implementations of one question is named in ADR-0015 as *"the failure from which no amount of
good design recovers."*

---

## 2. The reference repository: what survives, what does not

`github.com/Yashh56/matchmakingEngine` is a **real-time session matchmaker**: players sit in a
Redis queue, a scanner pairs them on MMR proximity and ping, a match is published on Redis
pub/sub, a Kubernetes pod is spun up as a game server, and both players receive a WebSocket
URL for that pod.

It is a clean, legible piece of work and its *shape* is worth keeping. Its *algorithm and its
purpose* are not this product's, and lifting it wholesale would produce a matcher that looks
impressive and fails quietly. The honest accounting:

### 2.1 What survives

| From the repo | Where it lands here | Why |
|---|---|---|
| **Redis sorted-set queue + scanner loop + pub/sub fan-out** | The **asynchronous half** (§14): standing searches, exposure sweeps, expiry sweeps, index rebuild work | This is a good, boring, correct pattern for background work with a wait dimension |
| **`CanMatch`'s widening gap over wait time** (`maxGap = 100 + waitTime/30·10`) | The **relaxation ladder** (§9.8) | The single best idea in the repo, and the mechanics document independently asks for it. Rebuilt as a *stated, ordered, floored* ladder that is announced to the player rather than a silent slide |
| **`region` as a queue partition key** | The **geographic shard key** (§17) | Correct as a shard, wrong as a matching criterion. Reinterpreted, it earns its place |
| **The service split** (api / matchmaker / orchestrator as separate entrypoints) | `cmd/matcher`, `cmd/indexer`, `cmd/sweeper` (§15) | Sound separation of an interactive path from background loops |
| **Gin HTTP handler shape** | The internal API skeleton (§16) | Fine. Standard library routing is also fine; not worth an argument |

### 2.2 What does not survive

| From the repo | Verdict | Why |
|---|---|---|
| **The Kubernetes game orchestrator, pod lifecycle, port-forwarding, `GameSession`** | **Deleted entirely** | There is no game server. The players book a real court, outside the app. *The court is their problem* is the product's central honesty; there is nothing to orchestrate |
| **The WebSocket client manager** | **Deleted from the matcher** | The player app never connects to the matcher (§4.2). Push to the client is the backend's job, over the backend's one contract |
| **`Player{mmr, region, ping, game_mode}`** | **Replaced** | Ping is meaningless. Region is a shard, not a criterion. MMR becomes μ *and* σ — and σ is half the point (§9.3.2) |
| **Pairwise `CanMatch` as the matching rule** | **Replaced** | It answers *may these two be paired* with a boolean. This product asks *how good would this game be, how likely is it to happen, and can I say why* — three questions, two numbers, one sentence each |
| **The queue as the primary mechanism** | **Demoted to Phase 2** | Nobody is waiting. The primary path is synchronous ranked retrieval |

### 2.3 Defects in the reference code, so they are not copied

The repository states it is for educational purposes. These are the specific things not to
carry across:

1. **`FormMatch` publishes to `matchmaking:events` twice** (`elo.go:60` and `:64`). Every
   match is delivered to the orchestrator twice, which would create two pods per match.
2. **`RemoveFromQueue` shadows `err` three times and checks only the last** — the `ZREM`
   result and its error are silently discarded, so a failed queue removal looks like success.
3. **The queue is a ZSET keyed on the marshalled JSON of the player.** Removal requires
   byte-identical re-marshalling; any field-order or float-formatting change orphans entries.
   Queue members should be ids, with the record held separately.
4. **`RunMatchmaking` unmarshals every queue member inside an O(n²) inner loop**, on every
   3-second tick, for every region and mode.
5. **`cmd/matchmaker/run.go` has an infinite outer `for` around a function that never returns**,
   and a `time.Sleep` after it that is unreachable.
6. **`CanMatch` computes wait time from `p1.JoinedAt` only**, ignoring how long p2 has waited.
7. **No authentication, no rate limiting, no idempotency, no dead-lettering, no tests.**

**Net:** roughly the transport spine and the service decomposition survive — call it 15% of
the code and none of the algorithm. This is an *adaptation in shape*, not a fork. Saying so
plainly now prevents the far more expensive discovery later that the engine is a
first-person-shooter matchmaker wearing a racket-sport costume.

---

## 3. What the engine is trying to achieve

Three things have to be true, **in this order**:

1. **The game has to happen.** A perfect opponent who never answers is worth nothing.
2. **The game has to be good.** Even, well-matched, and with somebody whose reasons for being
   on court resemble yours.
3. **The two of you have to play again.** One game is a transaction; a standing Tuesday four
   is a product.

And two consequences that shape everything below:

- **A bad match is worse than no match.** This is the opposite of a marketplace instinct and
  it is enforced by the quality floor (§9.8).
- **Likelihood and quality are different questions and are never added together.** This is
  enforced by the type system (§12.2), not by discipline.

---

## 4. Where the engine lives

### 4.1 The decision

**A separate, independently deployable service, written in Go, in this monorepo at
`matcher/`, reachable only from the backend over internal HTTP.**

```
frontend_player/  ──HTTPS──▶  backend/  ──internal HTTP──▶  matcher/
   (React Native)              (FastAPI)      (mTLS)          (Go)
                                   │                             ▲
                                   └────── event feed ───────────┘
                                        (transactional outbox)
```

### 4.2 The rules that survive this, unbroken

**The client never talks to the matcher.** Not once, not for the deck, not for a "why 78?"
lookup. The backend owns the API contract, emits `openapi.player.json`, and the client
generates its wire types from it (ADR-0006). A second public surface would be a second
contract, a second auth story, and the first thing to drift. The matcher's API is
service-to-service and never public.

**The backend remains the authority on everything the matcher reads.** The matcher owns no
truth. It owns a *read model* it can rebuild from zero by replaying the backend's events
(§7.4). If the matcher and the backend ever disagree, the backend is right and the matcher
is rebuilt.

**Never import across apps.** Unchanged, and now trivially enforced: the matcher shares no
language with the backend. The only contract is HTTP and the event feed (ADR-0005).

**Engines stay pure.** ADR-0015's purity rules transfer intact — the *scoring core* is a pure,
versioned, clock-free, I/O-free package (§15.2), enforced by an import lint that is the direct
analogue of the backend's `.importlinter`. Only the *deployment location* changes.

### 4.3 The two ADR tensions, argued rather than skipped

This decision contradicts two accepted ADRs on their face. Both deserve a real answer, and
both answers belong in a new ADR (§25).

**ADR-0005 — three-app monorepo, ownership boundaries.** This makes a fourth deployable and a
second backend language. That is a genuine cost: another CI lane, another deploy pipeline,
another set of on-call runbooks, and a second idiom for a small team to hold. The case for
paying it is in §4.4. The ownership hook must learn a fourth app, and `matcher/.claude/`
gets its own settings, exactly as the other three have.

**ADR-0015 — engines are a pure layer, *not* a microservice.** ADR-0015 explicitly rejected
an engine microservice, and its reason was precise:

> *"A pure function behind a network call has no state to own and no independent lifecycle,
> so the hop buys no isolation that an import rule does not already give."*

That reason is correct, and it does not apply here, because **the matcher is not a pure
function.** It owns state that nothing else in the system owns:

- the **candidate index** — a denormalised projection over four contexts, rebuilt by replay;
- the **interest ledger** — every *Let's play* yes, with its expiry;
- the **exposure ledger** — who has been shown to whom, and how often, this week;
- the **suppression ledger** — declines and passes, with their decay;
- **standing searches**, if Phase 2 ships;
- **outcome telemetry** — the search → challenge → accept → played → *second game* chain that
  is the only evidence that can settle a single weight in this document.

And it has an independent lifecycle that is not a nice-to-have but the whole point: §24 says
every constant here is a hypothesis, which means the weights change often, which means a
weight change must not redeploy the authentication service.

RacketSkill remains exactly what ADR-0015 says it is. The matcher is a different animal, and
the honest move is to say so in a new ADR rather than to quietly stretch the old one.

### 4.4 Why Go, and why separate — the case, and the case against

**For:**

- **A different runtime profile.** Scoring is a tight CPU loop over a candidate set × eight
  terms, and the doubles path is combinatorial. It wants predictable latency under
  concurrency; goroutines and a compiled runtime give it. The backend is I/O-bound
  request handling and does not want to share a process with a CPU burner.
- **A different persistence shape.** No aggregates, no event sourcing, no migrations that
  matter — a rebuildable read model plus mutable ledgers. Forcing it into the backend's
  event-sourced idiom would be dressing a projection as a domain.
- **A different release cadence,** as above.
- **It is horizontally scalable and stateless,** because the index is a snapshot and the
  ledgers are in Redis. Adding capacity is adding a pod.
- **The user already has a Go reference and the appetite.** Team fit is a real engineering
  input, not a soft one.

**Against, stated fairly:**

- A second language in a small team is a permanent tax.
- A network hop adds latency (~1–3 ms in-cluster) and a failure mode the in-process
  alternative does not have. §18 says what happens when it fires.
- Two places now hold racket-sport vocabulary. Mitigated by §5 and by the rule that the
  matcher never *names* a new domain term — it consumes the glossary's.

**If this trade is judged not worth paying**, the fallback is a Python module at
`backend/app/modules/matchmaking/` with the pure scorer under `backend/app/engines/matchfit/`.
Every algorithm, term, gate and constant in §9 transfers unchanged; only §15 and §16 are
discarded. The design is deliberately portable on that axis, and the decision can be
deferred until §22's Phase 1 without rework.

---

## 5. The vocabulary the engine adds

Domain terms are defined once, in the root `CONTEXT.md`. These are the matcher's own, and
they go there — not into a second glossary.

| Term | Means | Avoid |
|---|---|---|
| **Matcher** | The service. One of them, for the whole platform | engine (ambiguous — RacketSkill is an engine), matchmaker, MM |
| **Candidate** | One (player, sport) row considered for one search | opponent, user, profile |
| **Fit** | *How good would this game be?* 0–100. **The only number ever printed** | score, compatibility, rating (taken), MMR |
| **Liveness** | *How likely is this to actually happen?* **Never printed as a number**; changes position only | probability, activity, heat |
| **Term** | One weighted component of Fit. Eight of them | factor, feature, signal |
| **Evidence** | What a term produces alongside its value: a machine reason code and its payload. **Never a sentence** (§12.1) | explanation, reason text, message |
| **Modifier** | A capped adjustment applied after the terms | bonus, penalty, boost |
| **Gate** | A hard exclusion applied before anything is scored. No relaxation reaches one | filter, block (taken), rule |
| **Ruleset** | A versioned bundle of weights, floors, caps and the relaxation ladder | profile (collides with Player profile), config, weights |
| **Relaxation rung** | One announced step down the ladder when the pool is thin | fallback, widening, degradation |
| **Quality floor** | The Fit below which a candidate is not shown at all | threshold, cutoff |
| **Shortlist** | What one search returns | results, matches (taken by the product's own meaning) |
| **Line-up** | Who sits in which seat. The product's own word already | team, squad, group |
| **Seat** / **Side** / **Arrangement** | One position · one half of the court · which side each seat is on | slot (taken by Availability slot) |
| **Interest** | A *Let's play* yes: silent, one-directional, sport-scoped, expiring | wave, like, swipe |
| **Exposure** | How often a player has been shown in anybody's shortlist | impressions, visibility |
| **Play intent** | Competitive · For fun · No preference, **declared** per sport (§6) | mode (that is the search's word), lean, preference |
| **Search** / **Search result** | One run of the pipeline · its stored, replayable answer | query, request |

Two collisions worth naming explicitly:

- **Mode** is the *search's* setting (which tab you are on, right now). **Play intent** is the
  *player's* declaration. They are different facts and the whole of §6 turns on the
  difference.
- **Ruleset**, not "profile". `PlayerProfile` is an aggregate in the backend and reusing the
  word for a bundle of weights would be the first sentence of a confusing incident review.

---

## 6. Play intent — the cheapest strong term, and it does not exist yet

**This is the design's one hard dependency on new backend work, and it is worth flagging
before anything else, because the engine's strongest term per unit of cost reads a field the
platform does not currently store.**

Today, choosing *Competitive* or *For fun* changes only which weights *your* search uses. It
reshuffles the same pool and never asks the question that matters most: *does this person
also want that kind of game?* The failure only reveals itself on court — you brought a
scorecard, they brought a beer — and neither of you comes back.

**The fix:** Play intent is an attribute of the *player*, per sport, declared and never
inferred.

| Value | Means |
|---|---|
| `COMPETITIVE` | The score is the point. Count it, rank it, move my level |
| `FOR_FUN` | The evening is the point. A game, and probably a coffee after |
| `NO_PREFERENCE` | Either suits me — the honest middle, and a first-class answer |

**`NO_PREFERENCE` must be an explicit value, never a null.** The matcher cannot distinguish
*"I'm easy either way"* from *"I never opened that screen"*, and those are different facts.
Blank is a gap; `NO_PREFERENCE` is a statement. Model it as an enum with no nullable
alternative on the wire.

**Held per sport,** because the same person is plausibly a competitive padel player and a
social tennis player. Levels never transfer between sports in this product; intent should not
either.

### 6.1 Why declaring intent is legitimate where declaring a level is not

The platform's founding rule is **a level is proved, never declared** (`CONTEXT.md`). Handing
players a self-declared field one screen later needs an argument, and there is a clean one:

- **A level is a claim about a fact.** There is a true answer, reality checks it every
  Saturday, and misdeclaring it *pays* — a sandbagger farms wins against people who were
  promised a fair game. The declaration harms someone else, so the platform refuses it.
- **Intent is a preference.** There is no true answer to check it against, and misdeclaring it
  pays nothing. The only person who loses is the one who gets an evening they did not want.

A field that cannot be gamed to anyone else's cost is safe to hand over. That distinction
belongs in the interface, not only in this document — it is what makes the product look
consistent rather than arbitrary.

### 6.2 What the backend has to add

This is a `player_profile` change, and it fits the existing shapes exactly:

- A new value object `PlayIntent` in `app/modules/player_profile/domain/`, closed enum, three
  values, no null.
- Held **per sport**, so the profile carries a `Mapping[Sport, PlayIntent]`. This is the first
  per-sport fact on an aggregate that is deliberately not per sport — worth an explicit note
  in the ADR rather than a silent precedent.
- A new durable event: **`PlayIntentDeclared` — `player_profile.play_intent_declared` / v1**,
  carrying the sport, the value, and whether it came from onboarding or an edit.
- Carried in the **Profile commit** if it is asked at onboarding (recommended — §23.2).
- Served on the player API so the client can render it, and consumed by the matcher's
  indexer (§7.3).

### 6.3 Where behaviour gets a say — and it is not in the matcher

Declarations go stale. The fix is not to overrule them silently; it is to ask.

The product already has the right mechanic: **Keep these times?** appears at the exact moment
the player has done the work, shows a diff, and offers to save it. Intent gets the same
treatment. Five competitive padel searches against a `FOR_FUN` padel profile raises one
prompt — *"Your last five padel searches were competitive. Update your profile?"* — with
*Update it* and *Just for this search*.

**The matcher never acts on that drift.** It is the one place the platform watches, notices,
and deliberately declines to act: it asks, and it accepts whatever answer comes back. The
drift detector lives in the sweeper (§14.5) and its only output is a prompt.

The temptation to "correct" a stale declaration will be strong the moment there is data.
Deciding this deliberately now is cheaper than discovering it by drift later (§23.14).

### 6.4 What alignment does to a match

The comparison is between **the mode you are searching in right now** and **what they have
declared**. Your own profile setting is not part of it — your live search is a better
statement of what you want tonight.

| You are searching | They declared `COMPETITIVE` | They declared `FOR_FUN` | They declared `NO_PREFERENCE` |
|---|---|---|---|
| **Competitive** | 1.00 | **0.00** + modifier penalty | 0.85 |
| **For fun** | 0.35 | 1.00 | 0.85 |

Three things this encodes:

- **The penalty is asymmetric.** A social player in a competitive game is mildly bored. A
  competitive player in a game where nobody keeps score has been cheated of the only thing
  they came for, and the game does not even move their rating.
- **`NO_PREFERENCE` is nearly as good as a match.** These players are the glue. Punishing
  someone for being easygoing would be unfair and bad for a thin pool.
- **It is a weight, not a gate.** A directly opposite declaration scores zero and takes a
  modifier penalty, which buries the candidate in practice — but if everything else is
  exceptional they can still surface, low, with the card saying plainly why. *The weights
  persuade, the player decides.* The one hard line is in the relaxation ladder: **intent
  alignment is never relaxed** (§9.8).

### 6.5 The trap this vocabulary sets

The platform's real tag vocabulary contains `HERE_TO_COMPETE` and `HERE_TO_IMPROVE` in the
`WHY_YOU_ARE_HERE` group. They look exactly like intent. **They are not, and reading them as
intent is the specific error this section exists to prevent.**

A tag is *why you are here at all*. Play intent is *what tonight's game is*. Somebody tagged
`HERE_TO_COMPETE` who has declared `FOR_FUN` wants a hard-fought friendly, and the matcher
must read them exactly that way rather than quietly overruling them.

Reading the tags as intent would also **double-count**: the same six strings would move
Playing style, Social vibe *and* Intent alignment — three terms, one piece of evidence,
which is precisely the error §9.3.6 rules out elsewhere.

> **Engineering rule.** The `WHY_YOU_ARE_HERE` group is read in exactly two places: the
> familiarity sign (§9.4) and group coherence (§9.9). It is **never** an input to the
> Intent alignment term. A test asserts this by construction: the intent term's function
> signature does not receive tags at all.

---

## 7. What the engine knows, and how it learns it

### 7.1 The signals

| Group | Signals | Source | Freshness | Live today? |
|---|---|---|---|---|
| **Skill** | μ (level), σ (uncertainty), confidence, counted games, calibration priority, per sport | `rating` context | Moves with every counted game | ✅ **yes** |
| **Play intent** | Competitive · For fun · No preference, per sport | `player_profile` (§6) | Editable any time | ❌ needs §6.2 |
| **Social identity** | 2–6 tags across three groups | `player_profile` | Editable; stale tags weaker | ✅ **yes** |
| **Time** | The 7×3 availability grid, and when it was last touched | `player_profile` | Kept fresh by *Keep these times?* | ✅ **yes** |
| **Place** | Location area, search radius | `player_profile` | Slow-moving | ✅ **yes** |
| **Consent** | Proposals opt-in | `player_profile` | Explicit, no default | ✅ **yes** |
| **Reliability** | Player Score and its six strands **separately**: shows up, settles up, answers challenges, confirms results, keeps plans, sportsmanship. Plus opponent variety | `player_score` context | Continuous | ⏳ **scheduled — Phase 2** (§22) |
| **Interest** | *Let's play* yeses both ways; passes | Matcher's own ledger | Expires (§9.5.1) | ❌ needs the deck |
| **History together** | Games played, when, how they went, previous declines and accepts | future `matches` context | Permanent, decaying in weight | ❌ not built |
| **Load & holds** | Open challenges, open unsettled cases, blocks | future `matches` / `cases` | Must be **live** (§7.5) | ❌ not built |
| **Language** | Languages on the profile | `player_profile` | Static | ❌ not modelled |

One distinction runs through all of it: **things a player says about themselves** versus
**things the platform watched them do.** Where both exist, the watched thing wins. This is
the same claims-versus-demonstrations tie-breaker the rating engine already runs, and it
applies to tags (§9.3.6) as much as to skill.

**Half of this does not exist yet.** That is not a blocker — §10 is the design property that
makes it not a blocker — but it must be stated before anyone reads §9 and assumes the
engine ships with eight working terms on day one. It ships with five.

### 7.2 The candidate index

The matcher maintains a denormalised row per **(player, sport)**. This is the whole of what
the scoring core ever sees:

```
CandidateRow
  player_id            uuid
  sport                PADEL | TENNIS | SQUASH | BADMINTON

  # skill — from the rating context
  mu                   float32          # 1.0–5.0
  sigma                float32
  confidence           int8             # 0–100
  counted_games        int16
  calibration_priority enum
  rating_status        enum
  rating_updated_at    timestamp

  # profile — from the player_profile context
  play_intent          COMPETITIVE | FOR_FUN | NO_PREFERENCE
  tags                 [18]bit          # the closed vocabulary as a bitset
  tags_updated_at      timestamp
  grid                 [21]bit          # 7 days × 3 parts, Monday-first
  grid_updated_at      timestamp
  area_cell            uint32           # coarse geo cell, never a precise fix
  area_lat, area_lng   float32          # cell centroid, for distance only
  search_radius_km     uint8
  proposals_opt_in     bool | null      # null is neither yes nor no
  profile_updated_at   timestamp

  # reliability — from the future player_score context; neutral prior until then
  player_score         uint8 | null
  strand_shows_up      uint8 | null
  strand_settles_up    uint8 | null
  strand_answers       uint8 | null
  strand_confirms      uint8 | null
  strand_keeps_plans   uint8 | null
  strand_sportsmanship uint8 | null
  opponent_variety     uint8 | null

  # activity — for liveness only
  last_active_at       timestamp | null
  open_challenges      uint8            # advisory copy; the live check is §7.5
  first_seen_at        timestamp        # drives the newcomer window

  # market health
  shard_key            string           # city / metro. A shard, never a criterion
```

Approximately **160 bytes per row**. A city of 50 000 players across four sports is roughly
32 MB. This number is the reason §17 recommends holding the whole index in memory and never
touching a database during a search — and the reason nothing in this design needs to be
clever about scale.

**What the index deliberately does not contain — and this is an engineering rule, not a copy
rule:**

> **No name. No photo. No email. No date of birth. No gender. No nationality. No precise
> location.** The fields do not exist. A learned or hand-written term *cannot* read a
> protected characteristic because the value is not in the process. A schema test asserts the
> forbidden field names are absent, and it fails the build.
>
> This is the line between this product and the one it refuses to be, and putting it in the
> schema rather than in a review checklist is what makes it real.

### 7.3 How the index is built: events, not queries

The backend already has the machinery — an event-sourced write side, a **transactional
outbox**, and an `EventWorker` that delivers after commit (ADR-0003). The matcher is one more
subscriber.

```
  aggregate.save()  ──▶  domain_event_store  ──▶  event_delivery (outbox)
                                                        │
                                                 EventWorker
                                                        │
                                              ┌─────────┴─────────┐
                                       existing handlers    matcher feed
                                                                  │
                                                        matcher/cmd/indexer
                                                                  │
                                                          candidate index
```

Events consumed, with their durable names:

| Event | Updates |
|---|---|
| `player_profile.created` / v1 | Creates the rows: tags, grid, area, radius, opt-in, intent |
| `player_profile.social_tags_changed` / v1 | `tags`, `tags_updated_at` |
| `player_profile.availability_changed` / v1 | `grid`, `grid_updated_at` |
| `player_profile.location_changed` / v1 | `area_cell`, centroid, `shard_key` |
| `player_profile.search_radius_changed` / v1 | `search_radius_km` |
| `player_profile.proposals_opt_in_answered` / v1 | `proposals_opt_in` |
| `player_profile.play_intent_declared` / v1 **(new, §6.2)** | `play_intent` |
| `rating.*` (rating created / updated) | μ, σ, confidence, counted, priority, status |
| future `player_score.*` | The six strands, variety |
| future `matches.*` | History, open challenge counts, ghost games |
| future `cases.*`, `blocks.*` | Holds and blocks — **and see §7.5** |

**The feed is a transport decision, not an architectural one.** Three options, in order of
preference: (a) the `EventWorker` POSTs batches to the matcher's `/ingest` endpoint — no new
infrastructure, at-least-once, retries and dead-lettering already solved; (b) the worker
writes to a Redis Stream with a consumer group — better back-pressure, one more dependency;
(c) the matcher polls the outbox directly — rejected, because it makes the matcher a reader
of the backend's private tables and breaks the *only-HTTP* rule.

**Recommendation: (a) for Phase 1, (b) when a second consumer appears.**

**Delivery is at-least-once, so every projection is idempotent.** Each row carries the
`(event_type, schema_version, occurred_at, event_id)` of the last event that moved it; an
event older than what a field already reflects is dropped, and a repeat of the same
`event_id` is a no-op. The envelope the backend already serialises
(`SerializedEventEnvelope{id, event_type, schema_version, payload, occurred_at}`) carries
everything this needs.

### 7.4 Rebuild is the safety property

**The index is disposable.** If it is corrupt, wrong, or a projection had a bug, the recovery
is: drop it, replay the event store from the beginning, done. No reconciliation script, no
manual patching, no "which one is right" meeting.

This is worth an operational commitment: **a full rebuild is exercised in CI on a
production-sized fixture, and its wall-clock time is a tracked metric.** A rebuild path that
is never run is a rebuild path that does not work, and the day it is needed is not the day to
find out. Target: a 50 000-player city rebuilds in under five minutes.

### 7.5 The three facts that must never be stale

The index is eventually consistent, which is fine for μ, tags and grids — a rating four
seconds out of date changes nothing a player would notice.

It is **not** fine for three facts, because being wrong about them is a safety failure, not a
quality one:

| Fact | Being wrong means |
|---|---|
| **A block, either direction** | Somebody who blocked you is put in front of you |
| **A held account** (open unsettled case) | Somebody the platform has stopped from starting games is offered one |
| **An open challenge between you** | The app proposes what is already pending |

**The resolution: the matcher proposes, the backend disposes.**

The matcher scores against its index and returns a shortlist. **The backend re-verifies these
three gates against live state on the returned shortlist before it reaches the client** —
typically 10 to 25 rows, a single indexed query, sub-millisecond. Anything that fails is
dropped and the shortlist is short by one.

This puts the safety-critical check on the side that owns the truth, costs almost nothing,
and means a lagging index can degrade quality but can never breach a block. The matcher still
holds its own advisory copies so it can *rank* on them (a player with five open challenges is
lowered long before they are withheld) — but it is never the last word.

---

## 8. The request path, end to end

### 8.1 ⚡ Let the engine fill the seats

The button the whole feature turns on. Padel, doubles, competitive:

```
 1. CLIENT   POST /api/v1/matchmaking/lineups
             { sport, mode, availability_override?, locked_seats[], meetup_id? }

 2. BACKEND  authenticate → resolve the searcher:
               · profile (tags, grid, area, radius, opt-in, intent)
               · rating for that sport  → 404-equivalent if absent (§9.1 gate)
               · live gate facts: blocks, holds, open challenges
             → assemble a SearchContext, stamp `at`
             → POST matcher /v1/lineups          (internal, mTLS)

 3. MATCHER  Gate → Generate → Score(Fit) → Modify → Liveness
             → Shortlist → Group-optimise → Arrange → Explain
             → returns { search_id, lineup, forecast, per-seat breakdowns,
                         relaxation, ruleset_version }

 4. BACKEND  re-verify the three live gates on the returned seats (§7.5)
             persist the SearchResult (TTL 30 min)
             map to the public DTO   → response

 5. CLIENT   run the search animation over the completed answer;
             seat players one at a time; render the forecast and the reasons
```

**Step 5 matters more than it looks.** The *"reading 11 players in range · level, band width,
reliability, overlap"* animation is presentation over an answer that already arrived. The
server is never slow on purpose, the response is never streamed to fake progress, and the
line the animation prints is populated from the response's real candidate count. Honest
theatre. A server that stalls to make a search feel substantial is the first small lie in a
product whose entire pitch is that it shows its working.

### 8.2 The ranked list — *Pick players myself*

Identical through step 3, with `/v1/searches` instead of `/v1/lineups` and no group
optimisation: the shortlist is returned in rank order with each candidate's full breakdown.
Sorting by *Best fit · Evenest · Closest · Most reliable* happens **client-side over the
returned shortlist** — every field those sorts need is already in the response, and a
round-trip per sort tap would be latency spent on nothing.

One exception: **Evenest** with one seat left needs the arranged forecast per candidate. The
matcher precomputes it for each shortlist row when `open_seats == 1` and returns it as
`would_be_forecast`. Nothing is recomputed on the client — a second implementation of the
forecast maths on the client would be the ADR-0015 failure, in TypeScript.

### 8.3 "Why 78?" — and a bug worth designing out

The player taps *Why 78?* a minute after the search. **The breakdown must read the stored
`SearchResult`, never recompute.**

Recomputing means re-scoring against an index that has moved — a rating updated, a grid
edited, a player who went active. The number in the sheet then disagrees with the number on
the card, in a product whose one promise is that its numbers are checkable. That is not a
cosmetic bug; it is the product's credibility failing in the exact place it is being
demonstrated.

So: **a search result is immutable and self-contained.** Every term, weight, contribution,
evidence code, modifier and liveness reason for every shortlisted candidate is stored with
the search, under a 30-minute TTL, keyed to the searcher. `Why 78?` is a lookup. Sending a
challenge references `search_id`, which also gives the telemetry chain (§19) its join key.

### 8.4 Completing a half-built game

When two seats are filled and locked, **the matcher is no longer optimising for the
searcher** — it is optimising for the existing group. The two new players must fit the four.
The person searching may end up with a worse individual match than an empty builder would
have given them.

The screen must say so plainly, in the same voice the product already uses to say a forecast
is provisional. The response carries `optimised_for: "group"` so the client can, and a test
asserts the client renders it.

---

## 9. The algorithm

```
 SearchContext ──▶ ┌──────────┐
                   │  1 GATE  │  hard exclusions. no relaxation reaches these
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ 2 GENER- │  shard → sport → radius box → eligible set
                   │   ATE    │  plus guaranteed inclusions
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ 3  FIT   │  eight terms, renormalised weights, evidence each
                   └────┬─────┘   ── THE NUMBER ON THE CARD ──
                        ▼
                   ┌──────────┐
                   │ 4 MODIFY │  capped, each prints a line when it fires
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ 5 QUALITY│  below the floor → not shown at all
                   │   FLOOR  │  too few above it → relax one rung, GOTO 2
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ 6 LIVE-  │  reciprocal fit, interest, load, exposure, history
                   │   NESS   │  ── ORDERING ONLY. NEVER THE PRINTED NUMBER ──
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ 7 DIVERS-│  greedy spread over the top of the list
                   │   IFY    │
                   └────┬─────┘
                        ▼
                   ┌──────────┐        singles ─▶ shortlist
                   │ 8 TERMI- │
                   │   NAL    │        doubles ─▶ group objective ─▶ arrange
                   └────┬─────┘        deck    ─▶ deck order
                        ▼
                   ┌──────────┐
                   │ 9 EXPLAIN│  evidence codes, top three, one warning
                   └──────────┘
```

Stages 1–7 are shared by every surface. Only stage 8 differs. That is the whole reason there
is one engine rather than four.

### 9.1 Stage 1 — the gates

Applied before anything is scored. **These are not weights, and no relaxation rung reaches
one.**

| Gate | Why | Live today |
|---|---|---|
| **A block, either direction** | Both ways, invisible to both. Verified live (§7.5) | needs `blocks` |
| **A held account** — an open unsettled case | The hold stops them starting games; it must stop them being offered one. Verified live | needs `cases` |
| **No rating for that sport** | There is nothing to match on | ✅ |
| **Candidate outside the searcher's radius** | The searcher's radius is *their ask*, and a filter (`CONTEXT.md`) | ✅ |
| **An open challenge already exists between you** | Never propose what is already pending. Verified live | needs `matches` |
| **Missing or unapproved photo** | The on-court photo rule is only real if it gates something | ✅ |
| **Proposals opt-in explicitly `false`** *(engine-proposed surfaces only)* | Opting out stops the engine pushing. It does **not** remove them from a search a human ran — see below | ✅ |
| **Below the age or eligibility threshold** | Whatever that policy turns out to be | policy |

Two of these need care:

**The empty availability grid is *not* a gate.** The mechanics document proposes it; the
glossary overrules it, and the glossary is right: *"Blank means no preference, never leave me
out."* An empty grid scores no overlap (the term returns `NoEvidence` and stands down, §10)
and excludes the player from nothing. Prompting them to fill it is a product surface, not a
gate.

**Proposals opt-in gates the push, not the person.** *"Opting out stops the engine pushing,
not the player existing"* (`CONTEXT.md`). A player who declined proposals still appears in a
search another player deliberately ran; they are excluded only from surfaces where the
platform initiates — auto-proposals, standing-search notifications, the deck's outbound half.
The `SearchContext` carries `surface: HUMAN_INITIATED | ENGINE_INITIATED` and the gate reads
it. Getting this backwards would either break a consent promise or empty the pool; it is
worth one field to get right.

### 9.2 Stage 2 — candidate generation

```
shard_key == searcher.shard_key            # a metro. Not a matching criterion
  ∧ sport == searcher.sport
  ∧ within a bounding box of searcher.radius_km × relaxation_multiplier
  ∧ passes every gate
```

Over an in-memory snapshot this is a linear scan with an early-out on the box — microseconds
for a metro-sized index (§17). No spatial index is needed at these sizes, and adding one now
would be complexity bought against a problem nobody has. If a shard ever exceeds ~200 000
rows, a coarse geo-cell bucket map is the cheap next step; nothing above changes.

**Guaranteed inclusions** bypass the fit cut (not the gates), because the whole point of the
loop is that games get played:

1. **Anyone who has said *Let's play* to the searcher**, within the interest TTL. A certain
   yes from a decent match beats an uncertain yes from a marginally better one. (§9.5.1)
2. **Newcomers inside their exposure window** (§14.3).
3. **Zero-exposure players** — anyone shown to nobody this week (§14.2).

Each inclusion is flagged in the response with its reason, so the card can say why somebody
is there who otherwise would not be.

### 9.3 Stage 3 — the eight terms of Fit

Each term answers one question, produces one **Evidence**, and carries a weight that changes
with mode. Weights sum to 100 within a mode — **after renormalisation** (§10).

| # | Term | The question | Comp | Fun |
|---|---|---|---:|---:|
| 1 | **Level fit** | Are we close enough that this is a contest? | **26** | 11 |
| 2 | **Predicted balance** | Given both band widths, how even is it likely to be? | **17** | 6 |
| 3 | **Intent alignment** | Do we want the same kind of evening? | 14 | 14 |
| 4 | **Reliability** | Will this actually get played properly? | 13 | 9 |
| 5 | **Availability overlap** | Can we both play, and how soon? | 11 | **16** |
| 6 | **Playing style** | Will the hour on court suit us both? | 9 | 11 |
| 7 | **Distance** | Is it a reasonable journey? | 6 | 11 |
| 8 | **Social vibe** | Will the hour around the game suit us both? | 4 | **22** |

Every term returns `(value ∈ [0,1], Evidence)` or `NoEvidence`.

#### 9.3.1 Level fit

The distance between two ratings on the sport's own 1,0–5,0 scale. It falls away sharply — a
tenth of a point is a different game, half a point is a different sport.

```
Δμ = |μ_searcher − μ_candidate|

competitive:  level = clamp(1 − Δμ / LEVEL_TOL_COMP, 0, 1)          LEVEL_TOL_COMP = 0.55

for fun:      level = clamp(1 − max(0, Δμ − FUN_FREE_BAND)
                                 / (LEVEL_TOL_FUN − FUN_FREE_BAND), 0, 1)
                                                                     FUN_FREE_BAND  = 0.25
                                                                     LEVEL_TOL_FUN  = 0.90
```

**The for-fun form is a deliberate change from the prototype, which uses one curve for both
modes and only lowers the weight.** For fun, the floor is *"nobody spends the evening
watching"*; beyond that floor, closeness stops adding value. A friendly against someone a
quarter-point above you is no worse than one against your exact twin, and might be better.
The free band expresses that; a lower weight on the same steep curve does not — it still
ranks the twin first, just more quietly.

**A display note that is not a weight.** The for-fun deck card still leads with level, and
should: level is the single most honest thing you can say about a stranger, and burying it
would be coy. The card's *ordering of information* and the matcher's *weighting of evidence*
are separate decisions, made differently on purpose.

Evidence: `{kind: "level_fit", their_mu, my_mu, delta, direction: "above"|"below"|"level"}`

#### 9.3.2 Predicted balance

Not the same term as level fit, and the difference is the point. **Level fit compares two
anchors; balance asks how confident those anchors are.** Two players 0,03 apart with wide
bands may play a lopsided game; two players 0,15 apart with fifty counted matches each will
not.

The forecast identity is the product's own, carried over unchanged from v37:

```
σ_pair = √(σ_a² + σ_b²)
pct    = clamp(100 − Δμ·145 − σ_pair·32, 35, 96)
value  = (pct − 35) / (96 − 35)
```

Two notes:

- **The prototype uses `pct/100` as the term value, which wastes the bottom 35 points of the
  range.** Since `pct` is clamped at 35, no candidate can ever score below 0.35 on the term,
  so a lopsided pairing and a merely-poor one are compressed together. Normalising over the
  live range restores the discrimination. The *displayed* percentage is unchanged — it is
  still `pct`, still the number the balance bar draws.
- In for-fun the weight drops to a floor value: enough to stop a genuinely lopsided pairing,
  not enough to drive the list.

This is also why a wide band ranks below a proven one — the same argument the Rankings
honesty card already makes to players, made by the matcher.

Evidence: `{kind: "predicted_balance", pct, my_sigma, their_sigma, confidence: "high"|"medium"|"low"}`

#### 9.3.3 Intent alignment

A table lookup: your live search mode against their declared intent for that sport (§6.4).
No inference, no lean, no decay curve.

It matters in **both** modes at equal weight, which is unusual and deliberate: whichever kind
of game you want, the failure mode is the same — being matched with somebody who wants the
other one.

Because it reads a declaration rather than a guess, it is the **cheapest strong term in the
engine**. It costs one tap at onboarding, needs no history, works perfectly on launch day
with eleven users, and produces the clearest evidence on the card. Nothing else in §9.3 has
that profile — which is why §6 leads the document.

Evidence: `{kind: "intent_alignment", their_intent, my_mode, aligned: bool}`

#### 9.3.4 Reliability, decomposed by mode

The Player Score is one number in the UI, but the matcher reads its **strands separately**,
because different strands predict different failures:

| Strand | Predicts | Comp | Fun |
|---|---|---:|---:|
| **Shows up** | Whether the game gets played at all | 25 | **32** |
| **Answers challenges** | Whether you get an answer this week | 22 | 22 |
| **Confirms results** | Whether the game *counts* | **24** | 4 |
| **Keeps plans** | Whether the plan survives to Saturday | 14 | 14 |
| **Settles up** | Whether the court money causes a row | 10 | 12 |
| **Sportsmanship** | Whether you want to see them again | 5 | 16 |

```
reliability = Σ strand_weight_mode(s) · strand_value(s) / 100
```

That table is the whole argument for decomposing: *confirms results* is close to worthless for
a friendly and close to essential for a counted game, and a single blended score cannot
express that.

**A hard floor sits underneath, in both modes**, and it is not part of the modifier budget:
below `SCORE_MIN = 70`, a flat −12 and the reason is printed. The prototype already does this
and it should stay.

**Until the `player_score` context lands** — scheduled for Phase 2 (§22) — every strand is `null`, the term returns
`NoEvidence`, and its weight renormalises away (§10). It does not return 0.5 and it does not
return 0 — **no record is not a bad record**, which is the same principle the rating engine
applies to skill.

Evidence: `{kind: "reliability", score, strands: {...}, floor_breached: bool}`

#### 9.3.5 Availability overlap

The glossary defines **Availability overlap** precisely and asymmetrically: *"the denominator
is your slots, because the question it answers is how much of my week does this person
cover."* That definition stands. Two further factors sit **beside** it in the term rather
than redefining it:

```
overlap      = |shared| / |mine|                        # the glossary's term, unchanged
significance = |shared| / min(|mine|, |theirs|)         # scarcity: a shared slot from
                                                        # somebody with two is worth more
proximity    = exp(−days_to_next_shared / PROX_TAU)     # PROX_TAU = 5 days
staleness    = clamp(1 − (grid_age_days − 60)/240, 0.6, 1)

availability = (0.55·overlap + 0.25·significance + 0.20·proximity) · staleness
```

Three fixes over the prototype's bare `shared ÷ mine`:

- **Scarcity counts.** A player who has flagged two slots all week and shares both with you
  has told you something. One who flagged all twenty-one and happens to include yours has
  told you nothing.
- **Soonest matters.** An overlap tomorrow evening converts; an overlap in nine days
  evaporates. It also gives the card its best sentence.
- **Stale grids are weaker evidence.** *Keep these times?* exists to keep grids honest; a grid
  untouched for a year should count for less rather than be trusted blindly. It never falls
  below 0.6 — an old grid is weak evidence, not no evidence.

**Either grid empty → `NoEvidence`.** Blank means no preference (§9.1), and scoring a blank
grid as zero overlap would punish exactly the answer the glossary calls legitimate.

For fun, this becomes the second-heaviest term. Social games happen because two people were
both free, not because they were well matched.

Evidence: `{kind: "availability_overlap", shared_count, next_slot: {day, part}, days_away, grid_stale: bool}`

#### 9.3.6 Playing style — the `ON_THE_COURT` group

The answer to *"can tags matter in a competitive match?"* — yes, and this is the group that
does it. Six tags describing the hour on court:

`PLAYS_TO_WIN · LAUGHS_OFF_MISTAKES · ENCOURAGES_A_PARTNER · GENEROUS_ON_LINE_CALLS ·
QUIET_AND_FOCUSED · WARMS_UP_PROPERLY`

These are not vibe. `PLAYS_TO_WIN` on both sides is a substantive statement about how a
competitive game will run. `GENEROUS_ON_LINE_CALLS` on both sides predicts sportsmanship,
which is one of the reliability strands. `WARMS_UP_PROPERLY` alongside `HERE_TO_IMPROVE` is a
genuinely complementary pair.

**Tags relate in three ways, not one.** Counting shared tags treats every non-match as a zero,
and it is not:

**Matching** — the same tag both sides. Straightforwardly good, and the only relationship the
prototype recognises.

**Complementary** — different tags that fit together, sometimes better than a match:

| Pair | Why |
|---|---|
| `HERE_TO_IMPROVE` + `WARMS_UP_PROPERLY` | One wants to get better; the other runs the half hour that does it |
| `HERE_TO_GET_BACK_INTO_IT` + `ENCOURAGES_A_PARTNER` | The returning player and the person who makes returning bearable |
| `HERE_TO_GET_BACK_INTO_IT` + `GENEROUS_ON_LINE_CALLS` | A first game back should not be litigated |
| `HERE_FOR_A_REGULAR_GAME` + `BOOKS_THE_NEXT_ONE` | The standing four, and the person who actually makes it standing |
| `HERE_TO_MEET_PLAYERS` + `SHARES_A_LIFT` | One needs a way in; the other is already going |
| `HERE_TO_MEET_PLAYERS` + `STAYS_FOR_A_DRINK` | The same, an hour later |
| `HERE_TO_IMPROVE` + a stronger, focused opponent | Competitive only. This is how improving works |

**Clashing** — actively negative, and the reason overlap-counting fails:

| Pair | Severity | Notes |
|---|---|---|
| `TALKS_THROUGH_THE_MATCH` ↔ `QUIET_AND_FOCUSED` | **Real** | Ruins the hour for both. **Far worse as partners than as opponents** (§9.9) |
| `STAYS_FOR_A_DRINK` ↔ `STRAIGHT_HOME_AFTER` | Mild | For-fun only. In a competitive game nobody promised an evening |
| `PLAYS_TO_WIN` ↔ `HERE_FOR_THE_EXERCISE` | Mild | For-fun only |
| `PLAYS_TO_WIN` ↔ `LAUGHS_OFF_MISTAKES` | Mild | Partner relationship only |

**`PLAYS_TO_WIN` ↔ `HERE_TO_IMPROVE` is deliberately not a clash in competitive.** That is
precisely how you improve. It is a mild one in a friendly.

The general rule behind the omissions: **wherever a tag restates something the matcher already
measures, the measurement wins and the tag stands down.** Anything the availability grid,
the rating or the reliability strands already know is not scored a second time as a tag.

The combination, with diminishing returns:

```
dr(n) = 1 − φⁿ            φ = 0.45   →  1 tag 0.55 · 2 tags 0.80 · 3 tags 0.91

style = clamp( dr(matches) + 0.7·dr(complements)
               − min(CLASH_CAP, Σ clash_severity), 0, 1 )        CLASH_CAP = 0.25
```

Four rules that keep tags honest:

1. **Tags never exclude anybody.** They move position; they are not a filter.
2. **Diminishing returns.** Six well-chosen tags must not outrank a good level match. Without
   this, tag-stuffing becomes the dominant strategy — and the platform caps selection at 6
   precisely because it expects people to try.
3. **Clash penalties are capped and smaller than match bonuses.** Being wrong about a match
   costs a slightly duller evening; being wrong about a clash unfairly buries a person.
   Asymmetric costs, asymmetric magnitudes.
4. **Tags decay.** Set at onboarding a year ago and never revisited is weaker evidence than
   edited last month. Same staleness curve as the grid.

A fifth, for later: **corroborated tags count more.** `SETTLES_UP_ON_THE_SPOT` is checkable
against the settle-up record. `BOOKS_THE_NEXT_ONE` is checkable against court ownership.
`STAYS_FOR_A_DRINK` is checkable against *Around*. This is the same
claims-versus-demonstrations logic the rating engine already runs, applied to the social half
of the product — and it is the single highest-value term upgrade available once those
contexts exist. Not Phase 1.

Evidence: `{kind: "playing_style", matched: [tag_id], complementary: [[a,b]], clashing: [[a,b]]}`

#### 9.3.7 Social vibe — `AFTER_THE_MATCH` + `WHY_YOU_ARE_HERE`

Same machinery, different pair table. `AFTER_THE_MATCH` describes the hours around the game;
`WHY_YOU_ARE_HERE` describes why you are here at all.

In for-fun this is the **largest term in the match — larger than level.** That is the correct
expression of what *for fun* means, and it is a bigger shift than the prototype's weights
make.

Evidence: same shape as §9.3.6, `kind: "social_vibe"`.

#### 9.3.8 Distance

True distance between area centroids, against the **searcher's** declared radius, with a soft
edge rather than a cliff — somebody 200 m outside your ring is not a different kind of person.

```
distance = clamp( (1.15·r − km) / (1.15·r − 0.70·r), 0, 1 )      r = searcher radius
```

Full marks inside 70% of the ring, decaying to zero at 115% of it. The 15% overshoot is what
makes it a soft edge; the hard cut at the ring itself is the gate in §9.1.

Higher in for-fun than competitive, and the reason is worth stating: **people travel for a
good game and they do not travel for a coffee.** A competitive player will cross Kraków for
the right opponent; nobody crosses Kraków for a beer with a stranger.

**Whose radius applies — a refinement over the mechanics document.** The mechanics document
proposes a two-sided *gate*: you must be inside their ring and they inside yours. The
intuition is right — treating radius as one-sided manufactures declines — but the mechanism
is in the wrong column, and the glossary says why: the radius is *"a filter when the player
searches, and a weight when the engine proposes."*

So:

- **Candidate outside the searcher's radius → gate.** That is the searcher's own ask, and an
  ask is a filter.
- **Searcher outside the candidate's radius → a heavy Liveness dock, not a gate** (§9.5).
  It predicts a *decline*, not a bad game — and Liveness is precisely the column for *how
  likely is this to happen*. Gating it would also silently delete good matches from thin
  pools with no announcement, which is what the relaxation ladder exists to avoid.

This lands the signal where §9.5's own list already puts it (*"Radius is one-directional"*),
honours the glossary's two-jobs definition, and reaches the same outcome — those candidates
sink — without a silent hard cut.

Evidence: `{kind: "distance", km, area_code, outside_their_radius: bool}`

### 9.4 Stage 4 — the modifiers

Applied after the eight terms. **Each is capped, each prints a line when it fires, and their
total is bounded** so no stack of modifiers can override the substance of a match.

```
MODIFIER_BUDGET = ±10 points of the 100
```

| Modifier | Range | When it fires | Evidence |
|---|---:|---|---|
| **Calibration value** | 0 … +4 | Their band is wide and yours is narrow (or the reverse), **and the game would be counted** | `calibration_value` |
| **Familiarity** | −4 … +5 | You have played before. **Sign depends on tags and variety** — below | `familiarity` |
| **Language** | 0 … +2 | A shared language beyond the local default | `shared_language` |
| **Welcoming record** | 0 … +4 | The searcher is new; the candidate has high sportsmanship, high opponent variety, and a history of wide-band opponents | `welcoming_record` |
| **Reliability floor breach** | −12 | Player Score below `SCORE_MIN` | `reliability_floor` |
| **Intent opposition** | −6 | Directly opposite declarations (§6.4) | `intent_opposed` |

**The reliability floor sits outside the modifier budget, deliberately.** It is a floor, not
an adjustment, and it is allowed to dominate. A stack of small positives must never lift
somebody over a recent no-show.

#### Familiarity, and the sign flip the current design gets backwards

The prototype's *fresh faces* term rewards novelty flatly: somebody you have played before
scores about a third of somebody you have not.

That is right for one kind of player and exactly wrong for another. **`HERE_FOR_A_REGULAR_GAME`
is a tag in the product.** A player carrying it is telling you their goal is repetition — and
the matcher currently penalises every candidate who would help them achieve it.

So familiarity is **signed**, and the sign comes from the two players' `WHY_YOU_ARE_HERE`
tags and their behaviour:

| Reading | Sign | From |
|---|---|---|
| **Repetition-seeking** | repeat matches score **positively**, diminishing slowly | `HERE_FOR_A_REGULAR_GAME`, or an opponent-variety score showing a settled group |
| **Variety-seeking** | novelty scores positively, as today | `HERE_TO_MEET_PLAYERS`, `HERE_TO_GET_BACK_INTO_IT`, or a competitive player whose rating confidence needs varied opponents |
| **Everybody else** | mildly novelty-preferring, decaying with time since you last played | default |

Somebody you played once eight months ago is effectively fresh again.

This is a product call as much as an engineering one, because it changes what the app feels
like for a subset of users (§23.9).

#### Calibration value

A player with few counted games has a wide band. Games against well-established opponents
narrow it fastest, which is what the calibration plan in the Skill Passport already promises
them. The matcher should act on that promise: **occasionally prefer the match that produces
*information* over the match that produces the evenest scoreline.**

It is capped, it applies only to games that would be counted (so: never in for-fun), and it
is **printed** — because a player is entitled to know when they are being matched partly for
someone else's benefit, and most people are happy to be.

The backend already computes `calibration_priority` on the rating aggregate. The matcher reads
it rather than deriving a second opinion about the same fact.

### 9.5 Stage 6 — Liveness

**Liveness never enters the Fit score.** It reorders the list, it is bounded, and it explains
itself whenever it moves somebody into view.

```
rank_key = fit + liveness_offset            liveness_offset ∈ [−25, +25]
```

`rank_key` is never shown. `fit` is what the card prints. Anything moved more than
`MOVE_NOTICE = 6` points must print its dominant liveness reason.

| Signal | Effect | Why |
|---|---:|---|
| **They said *Let's play* to you** | +14 | Acceptance is close to certain (§9.5.1) |
| **Answer rate and speed** | −6 … +6 | Somebody who answers within a day is a different proposition from somebody with five expired challenges |
| **Recent activity** | −5 … +4 | *Active now* vs *3 days ago*. A dormant account is a slow no |
| **Current challenge load** | −8 … 0 | A player sitting on five unanswered challenges will not answer a sixth well (§14.4) |
| **Overlap proximity** | 0 … +4 | A shared slot inside five days converts; one in three weeks evaporates |
| **Previous accept between you** | +6 | The strongest positive available |
| **Previous decline between you** | −10, decaying | Quietly and temporarily. **Never shown to either side** |
| **Reciprocal asymmetry** | −12 … 0 | §9.5.2 — the most important and least obvious one |
| **Radius asymmetry** | −8 … 0 | You are outside *their* ring (§9.3.8) |
| **Exposure adjustment** | −6 … +8 | §14.2 |

**Why the separation is non-negotiable:** the Fit score is the only number the player is asked
to trust. The moment it silently contains *"they open the app a lot"*, it stops meaning what
it says, and *Why 78?* becomes a lie by omission. Keeping the two apart is what lets the app
print its reasoning without embarrassment.

The pipeline already established this discipline for one signal — the *Let's play* yes was
pulled out of the fit score and moved to ordering, with the reason stated. **This design
generalises that decision to every likelihood signal**, and §12.2 makes it a compile error to
break it.

#### 9.5.1 *Let's play* — the interest signal, in full

A **silent, one-directional, sport-scoped yes.** Nobody is notified. Nothing is scored. It
becomes visible only when one of you goes looking for a game.

| State | What happens |
|---|---|
| **You → them** | You are lifted in *their* list, with the reason printed to them |
| **They → you** | They are lifted in *your* list, with the reason printed to you |
| **Mutual** | An instant match. No 24-hour challenge, no waiting |

**Four mechanics the current design is missing, and all four are the matcher's to own:**

1. **Expiry.** A yes is a statement about *now*. `INTEREST_TTL = 21 days`, with the lift
   decaying linearly over the last 7 before it drops off entirely. Without expiry the deck
   becomes an archive of stale interest, the lift stops predicting anything, and the printed
   reason becomes untrue.
2. **A cap.** If saying yes to everybody is free, somebody will, and the signal is worth
   nothing. `OUTSTANDING_INTEREST_CAP = 20` per sport, soft: past it the oldest decays
   faster. The deck's natural exhaustion (*"You have seen everybody compatible today"*)
   already does part of this work.
3. **Passes suppress, they do not erase.** A *Not today* is silent and costs the other person
   nothing, and that must stay true. It keeps that profile out of your deck for
   `PASS_SUPPRESS = 30 days` rather than forever, and repeated passes on the same person are
   a soft signal respected quietly. **It is never, under any circumstance, shown to them.**
4. **A yes guarantees inclusion** (§9.2), subject to the gates. A certain yes from a decent
   match beats an uncertain yes from a marginally better one.

#### 9.5.2 Reciprocal fit — a match is a proposal, and a proposal needs a yes

Fit as computed so far is one-directional: *how good is this player for me*. But every match
requires the other person to want it too, and **fit is not symmetric**.

Level fit and distance are roughly mutual. Almost nothing else is:

- **Reliability is one-directional.** A player with a Player Score of 99 is excellent for you.
  You, with 74, are a worse proposition for them.
- **Familiarity is one-directional.** They might have played you before and be looking for
  variety.
- **Intent is one-directional** when one of you leans harder than the other.
- **Radius is one-directional** (§9.3.8).

Left uncorrected, the top of your list fills with people who would score you 41 — the very
best candidates who will never say yes. That produces a list that looks superb and converts
terribly, and the player learns to distrust the whole screen.

It is also the kind thing to do. **Repeatedly surfacing somebody who will always decline you
is a small cruelty performed at scale.**

**Where this goes in the pipeline matters for cost.** Computing both directions over the whole
pool doubles the work. Computing it over the **shortlist only** — after the quality floor,
typically 20–40 rows — costs almost nothing:

```
fit_ba = Fit(candidate → searcher), scored under the candidate's *declared* intent
         as the mode, since that is the search they would be running

asym   = max(0, fit_ab − fit_ba − ASYM_TOLERANCE)          ASYM_TOLERANCE = 12
dock   = −min(12, asym · 0.5)
```

Evidence, when it fires: `{kind: "reciprocal_asymmetry", their_fit_for_you, delta}`. Printed
in the *Why 78?* breakdown, not on the card — it is a statement about somebody else's likely
opinion and the card is not the place to editorialise about it.

### 9.6 Stage 7 — diversity

The top five should not be five copies of the same profile. Some variety across level,
distance and intent makes the screen feel like a pool rather than a leaderboard — and it is
also how a player discovers that the interesting match was the fourth one.

Greedy maximal-marginal-relevance over the **top 12 only**; below that the list keeps pure
`rank_key` order.

```
pick = argmax over remaining of ( rank_key(c) − λ · max_similarity(c, already_picked) )
λ = 8

similarity(a,b) = 0.35·level_bucket_match + 0.25·distance_ring_match
                + 0.20·intent_match       + 0.20·tag_jaccard
```

**Constrained by the quality floor:** diversification may reorder, never promote a candidate
below the floor. Variety is a presentation good; a bad match is still a bad match.

### 9.7 The quality floor

**Below `QUALITY_FLOOR` Fit, a candidate is not shown at all.** The pool is described instead:
*"Four padel players within 8 km this week."*

This will feel wrong to anybody with marketplace instincts, and it is the most important
paragraph in this section. **A confident bad match halves the chance of a second game and
costs you the player.** The honest empty state is a feature. It is also the same voice the
rest of the product already uses: the app that says *the court is your problem* can say *the
pool is thin tonight*.

`QUALITY_FLOOR` needs an accountable owner and a number (§23.10). Starting position: **52**,
with `MIN_SHORTLIST = 3` before relaxation triggers.

### 9.8 Relaxation — announced, ordered, floored

When fewer than `MIN_SHORTLIST` candidates clear the floor, relax **one rung at a time, in a
fixed order**, re-run generation and scoring, and **tell the player what was relaxed and what
it costs**:

| Rung | Relaxes | Multiplier / effect | The response says |
|---:|---|---|---|
| 1 | **Familiarity** | Drop the novelty preference; show people you have played | `relaxed: ["familiarity"]` |
| 2 | **Distance** | radius × 1.5, then × 2.0 | `relaxed: ["distance"], radius_km_used` |
| 3 | **Availability** | Score candidates with no overlap, clearly labelled | `relaxed: ["availability"]` |
| 4 | **Level** | `LEVEL_TOL` × 1.4, balance forecast shown **honestly, not flattered** | `relaxed: ["level"]` |

**Never relaxed, at any rung:**

- every gate in §9.1;
- the reliability floor;
- **intent alignment below its floor.**

Those are the four where relaxing produces exactly the evening the product exists to prevent.

**Past rung 4, the engine stops and says the pool is thin.** It returns an empty shortlist
with a `pool_description` — how many players of that sport are in range this week, and what
would have to change. `MAX_RELAXATION_RUNG = 4`, and how far it may go before the app should
stop relaxing and start describing is a product decision (§23.13).

This is the reference repository's `maxGap = 100 + (waitTime/30)·10` — the same idea, made
ordered, floored, bounded and *announced*. The repo widens silently and forever; this widens
in a stated order, stops, and says so.

### 9.9 Doubles — the group is the objective

For padel and badminton the matcher is not choosing a person. It is choosing **a group of
four**, and the searcher occupies two different relationships inside it at once.

**Partner and opponents are not the same relationship:**

- **Your partner** shares a side with you for ninety minutes. Playing style and social vibe
  matter *more* here than with your opponents — `TALKS_THROUGH_THE_MATCH` next to
  `QUIET_AND_FOCUSED` is far worse as a partnership than as an opposition. Skill
  complementarity also works differently: the weaker player in a pair carries more of the
  outcome, which the forecast maths already reflects.
- **Your opponents** matter mostly through balance. Style matters less; you spend the evening
  opposite them, not beside them.

```
PARTNER_STYLE_MULTIPLIER = 1.6      applied to style and vibe for the partner seat
OPPONENT_STYLE_MULTIPLIER = 0.7     applied for the two opposing seats
```

**The objective is the group, not the sum.** The engine does not seat the four best individual
fits. It evaluates combinations and picks the one that plays out evenest, then arranges it.
*Four excellent individual matches can produce a lopsided four; three good ones and a modest
one can produce a perfect evening.*

**σ_group is on the two-player basis, and that is load-bearing.** `pct` is one function read by
two populations, and its `sigma_coefficient` is calibrated against *a typical σ_pair of 0.495*
(§9.3.2, `ranking-weights.md`, ADR-0103). A four's `gap` is re-based — it is between two side
strengths rather than two players — and its σ has to be re-based with it, or the same constant
prices two different quantities. A plain `√(Σσᵢ²)` grows with `√n`, so a four paid 1.41× what an
identical pair paid for the identical per-player doubt: a level four of unsettled players read
46 % with a gap of exactly zero, and above σ 2.03 the clamp swallowed the gap and the forecast
stopped answering its own question. `√2·rms` reduces to `√(σ₁²+σ₂²)` at n = 2, so singles and
every pairwise reading are unchanged by construction, and at n = 4 it is the spread of a
representative pair — which is what a match is played between.

```
teamStrength(a, b) = 0.45·max(a,b) + 0.55·min(a,b)          # the weaker player carries more

arrange(four):  enumerate the 3 pairings, pick min |strength_A − strength_B|

forecast(four): σ_group = √(2·Σ σᵢ² / n)      # √2·rms — the TWO-PLAYER basis
                pct     = clamp(100 − gap·145 − σ_group·32, 35, 96)

G(lineup) = w_bal      · balance_norm(arrange(lineup))
          + w_seatfit  · mean(fit of the three non-viewer seats)
          + w_minfit   · min(fit of the three non-viewer seats)
          + w_intent   · group_intent_coherence
          + w_tag      · group_tag_coherence
          − partner_clash_penalty(viewer, partner)

           comp:  w_bal 40 · w_seatfit 22 · w_minfit 18 · w_intent 12 · w_tag 8
           fun:   w_bal 20 · w_seatfit 20 · w_minfit 14 · w_intent 18 · w_tag 28

hard rule: any seat below QUALITY_FLOOR disqualifies the whole combination.
```

Three things this extends beyond balance:

- **Group social coherence.** A tag shared by three of the four is worth more than a tag
  shared by one pair. The builder already shows *what this group has in common* — that panel
  reflects a real group measure, not a pairwise one.

  ```
  group_tag_coherence = Σ over tags held by ≥ ⌈3·n/4⌉ seats of  dr(count) / normaliser
  ```

- **Intent alignment matters more in doubles, not less.** One person keeping score in a four
  where three want a beer spoils it for three people. **The penalty scales with how many
  people are on the wrong side of it:**

  ```
  group_intent_coherence = 1 − (misaligned_seats / (n − 1))^0.8
  ```

- **Completing a half-built game is a different problem** — §8.4.

**Cost.** Take the top `K = 16` candidates after liveness. Enumerate `C(15, 3) = 455`
combinations (the viewer's seat is fixed); for each, 3 pairings. That is ~1 400 cheap
arithmetic evaluations — tens of microseconds. **No optimiser, no beam search, no heuristic
is needed, and adding one would be complexity bought against a problem nobody has.**

`K` is a ruleset constant with a stated reason: beyond the top 16, a candidate's individual
fit is low enough that no group bonus recovers it. If that turns out to be false, `K` moves —
it is a config change, not a rewrite.

**Provisional forecasts.** A four's balance is not computable until all four are known. Rather
than inventing a number or showing nothing, `partialForecast` reads a half-empty side **as if
the missing player matched the one already there**, and everything built on it is labelled
**provisional** — in the header, on each candidate's preview line, and in a sentence stating
the assumption outright. The moment the last seat is taken it stops being provisional and
agrees exactly with the arranged forecast. **A test asserts that equality**, because the two
functions drifting apart is how a screen starts lying quietly.

**Two forecasts, not one, and the bug that made them necessary.** `fourForecast` searches all
three pairings and reports the best — the right question when choosing *people*, the wrong one
once choosing *sides*, because it never changes when you move somebody across the net.
`arrangedForecast` scores the line-up actually on screen. The builder shows the second and
offers *Even it out* to restore the first, telling you what you are giving up. Both functions
live in the matcher and neither is reimplemented on the client.

**Singles** use the same machinery with two seats and no pairing to arrange.

### 9.10 The newcomer path

A brand-new player has a wide band, no behaviour record, no corroborated tags and no history.
Almost every term is uncertain — and this is **the most consequential game they will ever
play**, because the return-rate figure applies most brutally to first games.

A distinct ruleset, selected when `counted_games == 0 ∧ rating_status == INITIAL_ESTIMATE`:

| Rule | Effect |
|---|---|
| **Bias hard toward evenness and reliability** | Level 30 · balance 22 · reliability 20 · intent 14 · availability 8 · style 4 · vibe 2 · distance 0 |
| **A first game is worth a longer journey** | Distance weight → 0; the radius gate still holds |
| **Match with a welcoming record** | High sportsmanship, high opponent variety, `GENEROUS_ON_LINE_CALLS` / `ENCOURAGES_A_PARTNER` / `HERE_TO_IMPROVE`, and a history of playing wide-band opponents. **A real, computable property that nobody is currently using** |
| **Never the most competitive player in the pool** | Even when the ratings line up. A 3,40 with fifty counted games is the wrong first opponent for a 3,35 with none. Cap the candidate's `counted_games` percentile |
| **Be honest about the band** | The forecast for a wide-band newcomer is a guess. The product already knows how to say *provisional*. Say it |
| **Do not zero their Player Score** | No record is not a bad record. Neutral prior, exactly as the rating engine does with skill (§10) |

**And make it worth the veteran's while.** Playing a newcomer should not feel like community
service. The calibration modifier and the variety strand both reward it, and the card says
what is happening: *"They're new — this game does most of its work for them."* Most people are
glad to be asked; nobody likes finding out afterwards.

### 9.11 The deck — *Match me*

The deck has no search mode to read, so it is scored against **the viewer's own declared
intent** for that sport (§6). This is one of the places a declaration is strictly better than
an inference: without a stored answer the deck has nothing at all to go on. A player whose
padel profile says `COMPETITIVE` should be seeing competitive players in the padel deck.

**The deck's ordering policy is its own, and it is not the list's:**

1. **People who have already said yes to you** — an instant match is one tap away.
2. **High-liveness candidates** above the quality floor.
3. **The rest, spread for variety** — λ raised to 14, because a deck of eleven near-identical
   profiles feels broken even when every card is well matched.

Plus the deck's own exclusions: already passed within `PASS_SUPPRESS`, already asked, already
has an open game with you.

---

## 10. Graceful term degradation — the property that lets this ship

**This is the most important structural idea in the document.**

Half the signals in §7.1 do not exist yet. Player Score is not built. There is no match
history, no case system, no blocks, no language field. A design that needs all eight terms
cannot ship until four more bounded contexts do.

So: **a term with no evidence returns `NoEvidence`, is dropped from the sum, and the remaining
weights renormalise to 100.**

```go
type Term interface {
    Name()   TermName
    Weight(r Ruleset, m Mode) int
    Score(ctx SearchContext, c Candidate) (value float64, ev Evidence, ok bool)
}

// ok == false  →  NoEvidence: the term is dropped and its weight redistributed
//                 proportionally across the terms that did produce evidence.
```

Consequences, and they are all good:

- **The engine works on launch day with eleven users and five terms**, and gets better as
  contexts land — without a rewrite, a migration, or a flag.
- **Absent evidence never becomes a fabricated 0.5.** A player with no Player Score is not
  scored as average and not scored as bad. **No record is not a bad record** — the same
  principle the rating engine already applies to skill, and the same one §9.10 insists on for
  newcomers.
- **The card prints fewer reasons rather than fake ones.** A term that did not fire produces no
  sentence, which is the honest output.
- **Every term is independently shippable.** Reliability turning on is a projection change and
  a weight release, not a coordinated deploy.

**What ships on day one, given the backend as it stands:**

| Term | Day 1 | Needs |
|---|---|---|
| Level fit | ✅ live | — |
| Predicted balance | ✅ live | — |
| Availability overlap | ✅ live | — |
| Playing style | ✅ live | — |
| Social vibe | ✅ live | — |
| **Intent alignment** | ⚠️ **live if §6.2 ships** | one profile field + one event |
| Reliability | ❌ stands down | `player_score` — **scheduled, Phase 2** (§22) |
| Distance | ⚠️ partial | area centroid resolution |

Five terms live, six with intent. Renormalised, the competitive weights become roughly
`level 36 · balance 24 · intent 19 · availability 15 · style 12 · vibe 5 · distance 8` — which
is close to the prototype's shipped weights and demonstrably good enough to demo. That is the
point: **the engine degrades to something sensible rather than to something broken.**

The same mechanism covers per-player gaps, not just platform-wide ones: a specific player with
an empty grid simply loses the availability term for that comparison, and the other terms
carry the score.

---

## 11. Rulesets — the weights are configuration, not code

Every number in §9 is a hypothesis (§24). The single most consequential architectural decision
in this document is therefore not about scoring at all:

> **A Ruleset is versioned data. Changing a weight is a configuration release. Every search
> records the ruleset version that produced it.**

```
Ruleset
  version              "2026.08.25-a"        # immutable once released
  modes
    competitive        { weights{8}, strand_weights{6}, level_tol, fun_free_band, ... }
    for_fun            { ... }
    newcomer           { ... }
  modifiers            { caps and ranges }
  liveness             { signal bounds }
  group                { w_bal, w_seatfit, w_minfit, w_intent, w_tag, K }
  floors               { quality_floor, score_min, min_shortlist }
  relaxation           { ordered rungs, multipliers, max_rung }
  diversity            { lambda, window, similarity_weights }
  interest             { ttl_days, cap, pass_suppress_days }
```

- **Embedded as the default**, so the binary is self-sufficient and testable with no external
  dependency.
- **Overridable at runtime** from a config store, hot-reloadable, with the loaded version
  reported on `/healthz` and on every response.
- **Immutable once released.** A change is a new version, never an edit — because a search
  result from last Tuesday must remain explainable, and *"why did this card say 78 then and 74
  now"* has to have an answer.
- **Validated on load**: weights sum to 100 per mode, every cap positive, every rung ordered,
  no unknown key. A malformed ruleset refuses to load and the previous one keeps serving. A
  matcher that silently falls back to defaults on a typo is a matcher that quietly A/B tests
  against itself.

This is what makes §19's replay harness possible, and it is what turns *"I think vibe should
be 24"* from an argument into an experiment.

**A/B and shadow** fall out of it for free: a search can be assigned a ruleset by a stable
hash of the searcher id, and the version on the response makes every downstream outcome
attributable.

---

## 12. The explainability contract

Five rules, half-adopted by the product already, adopted completely here:

1. **Every term produces one sentence naming its evidence.** Not a category — the evidence.
   *"4 shared slots · next Tuesday evening"*, not *"good availability"*.
2. **The card shows the top three reasons and, when a term is genuinely weak, one warning
   line.** *Why 78?* opens the full breakdown: every term, its weight, its contribution.
3. **The card never says in words what it has already drawn.** There is already a test
   asserting this and it stays.
4. **The printed score is Fit only.** Liveness never enters it.
5. **When Liveness moves somebody, the reason is printed.**

**If a proposed signal cannot satisfy all five, it does not go in the matcher.** That
constraint is not a limitation — it is the reason this app can show its working when its
competitors cannot.

### 12.1 Evidence crosses the wire as codes, never sentences

**This is the point at which the mechanics document and the codebase's own rules disagree, and
the codebase wins.**

The mechanics document talks in sentences — *"4 shared slots · next Tuesday evening"*,
*"Marek wants competitive padel too."* Those are the right sentences. They are **not** what the
engine emits.

ADR-0022 is unambiguous: **the backend emits machine codes and never display text.** The
clients own the words, in the client's own language. A Go service emitting Polish and English
strings would be a second copy of the product's copy, in a third language, in the least
reviewable place in the system — and it would make internationalisation a matcher deploy.

So Evidence is structured:

```json
{ "kind": "availability_overlap",
  "shared_count": 4,
  "next_slot": { "day": "TUESDAY", "part": "EVENING" },
  "days_away": 5,
  "grid_stale": false }
```

and the client renders *"4 shared slots · next Tuesday evening."*

The same applies to every warning line, every relaxation notice, every liveness reason and
every pool description. **The engine never returns a string a human reads.**

The one field that crosses as a number and is *meant* to be read as one is `fit` — because it
is a number, and the whole contract is that it means what it says.

### 12.2 The two numbers, enforced by the type system

§9.5's separation is too important to leave to discipline. It is a type:

```go
type Fit struct      { points float64 }      // 0–100. printed.
type Liveness struct { offset float64 }      // ±25. never printed.

// there is no operator, method, or constructor that combines them.
// ranking is the ONLY place they meet, and it produces a third,
// unexported, never-serialised type:

type rankKey float64
func order(f Fit, l Liveness) rankKey { ... }   // package-private
```

`Fit` has no `Add(Liveness)`. `rankKey` has no JSON tag. Serialisation of a candidate emits
`fit` and a list of liveness *reasons*, never a liveness *number*. **Somebody adding "they open
the app a lot" to the printed score has to defeat the compiler to do it**, which is roughly
the level of resistance that decision deserves.

The same trick guards §7.2's privacy rule: `Candidate` has no name, photo or birthdate field,
so a term physically cannot read one.

---

## 13. Determinism and reproducibility

*"A scenario replayed at a fixed clock must produce the same world; a demo is not a slot
machine"* — ADR-0015. It applies here with more force, because this engine's output is
argued with by users.

**Rules:**

- **No ambient time in the core.** `SearchContext` carries `at`. The scoring packages do not
  import `time` for reading the clock, and an import lint enforces it — the direct analogue of
  the backend's `.importlinter`.
- **No randomness anywhere.** Not in tie-breaking, not in diversification, not in exposure
  lifts. Ties break on a stable total order: `(rank_key desc, fit desc, player_id asc)`. A
  matcher that shuffles is a matcher that cannot be debugged, and *"it showed me somebody
  different when I went back"* is a support ticket with no possible answer.
- **No map-iteration order dependence.** Go randomises map iteration; every ordered traversal
  goes through a sorted slice.
- **The index snapshot is versioned.** A search records `(ruleset_version, snapshot_version,
  at)`. Those three plus the request reproduce the answer exactly, forever.
- **Same request + same snapshot + same ruleset ⇒ byte-identical response.** This is a
  property test, not an aspiration.

What this buys: the replay harness (§20.3), reproducible *Why 78?*, credible incident
investigation, and honest A/B measurement.

---

## 14. Fairness, exposure and load — the part nobody has written down

If everybody is ranked by the same function, the same ten people sit at the top of everybody's
list. They are flooded with challenges. They stop answering. Their answer rate falls, their
Player Score falls, and **the matcher punishes them for having been popular.** Meanwhile a
hundred perfectly good players are never shown to anybody and quietly leave.

That is not hypothetical; it is the default behaviour of a scored list, and it is how small
matching markets die.

**The framing that makes all of this obvious: the matcher is running a small market, and a
market where the top of the list never changes is a market that has stopped working.**

This is also the half of the engine that is genuinely asynchronous — and therefore the half
where the reference repository's queue-and-sweep design actually earns its keep.

### 14.1 The ledgers

Redis, because these are mutable, shared across matcher instances, and cheap to lose:

| Ledger | Key | Holds | TTL |
|---|---|---|---|
| **Interest** | `interest:{sport}:{to}` | sorted set of `from → at` | 21 d |
| **Suppression** | `suppress:{from}:{to}` | pass / decline marker | 30 d / 45 d |
| **Exposure** | `expo:{sport}:{week}` | hash `player → shown_count` | 3 w |
| **Challenge load** | `load:{player}` | counter, mirrored from `matches.*` | live |
| **Search results** | `search:{id}` | the immutable answer (§8.3) | 30 min |
| **Standing searches** | `standing:{sport}:{shard}` | sorted set by `created_at` | Phase 2 |

Losing Redis degrades the engine to *no interest lift, no exposure correction, no Why-78
lookup* — bad, not catastrophic (§18).

### 14.2 The exposure floor

**Every eligible player should appear in *somebody's* list.** A player shown zero times in a
week gets a bounded liveness lift until they have been.

```
shown_this_week == 0        →  +8
shown_this_week ∈ [1, 3]    →  +3
shown_this_week > P90       →  −4
```

Bounded, and printed when it moves somebody into view. The sweeper computes the weekly P90 per
shard and sport once an hour; the search path reads a cached scalar.

**The metric that says whether this is working is the exposure Gini coefficient** (§19). A
Gini above 0.6 means the market is concentrating and the constants above are too weak.

### 14.3 The newcomer exposure window

Guaranteed inclusion for the first **14 days**, while a player has no record to rank on. A
newcomer with five terms standing down and no behaviour history will otherwise sit below
everybody permanently — and never accumulate the evidence that would lift them. This is a
cold-start trap and the window is the standard, boring escape from it.

### 14.4 Challenge load

A player sitting on several unanswered challenges is temporarily lowered in liveness and
eventually withheld from lists entirely.

```
open_challenges ≥ 3   →  liveness −4
open_challenges ≥ 5   →  liveness −8
open_challenges ≥ 8   →  withheld from generation for 24 h
```

**They are told — *"You have five challenges waiting"* — and the searcher is not.** The
searcher does not need to know somebody else's inbox is full; the person whose inbox is full
does.

This protects the popular player from the exact death spiral described above: they are
throttled *before* their answer rate falls, rather than punished *after*.

### 14.5 The sweeper

One process, several loops, all idempotent, all safe to run twice:

| Loop | Cadence | Does |
|---|---|---|
| **Expiry** | 5 min | Interest past TTL, suppression past TTL, standing searches past their window |
| **Exposure roll** | hourly | Recompute per-shard P90, roll the weekly bucket |
| **Newcomer window** | hourly | Open and close 14-day windows |
| **Intent drift** | daily | Detect N consecutive searches disagreeing with a declaration → **raise a prompt, never change the value** (§6.3) |
| **Outcome join** | 15 min | Walk `matches.*` events, join to `search_id`, write the telemetry chain (§19) |
| **Index health** | 1 min | Lag, staleness, row counts; alarm past thresholds |

This is where the reference repo's scanner-loop shape lands, correctly: background work with a
wait dimension, driven by a Redis-backed queue, published on pub/sub. Rebuilt with the defects
in §2.3 fixed — ids in the queue rather than marshalled JSON, one publish per event, errors
checked, and a dead-letter path.

### 14.6 What the matcher learns, and what it must never learn

**Learns:**

- **Declines.** *"The matcher learns from it"* is a promise the product already makes; this is
  what it should mean. A decline suppresses that person for that searcher for a period and
  lowers liveness. A *pattern* of declines (always over 5 km, always wide-band) adjusts that
  searcher's implicit preferences. **The other person is never told, ever.**
- **Accepts.** The strongest positive available, and stronger still if the game got played.
- **Forecast error.** A game forecast at 91% even that ends 6-0 6-0 is evidence — first about
  the two ratings, second about the forecast itself. Tracking how well the forecast predicts
  reality is **the only way to know whether the weights in §9.3 are any good.**
- **Ghost games.** Matched, planned, never played. The most damaging outcome in the product and
  currently the least measured.
- **Return rate by match profile.** The ground truth. Which combinations of terms actually
  produce second games? Everything in this document is a hypothesis until that has an answer.
- **Tag corroboration**, from behaviour and from *Around*.
- **Drift between declaration and behaviour** — far enough to raise the prompt in §6.3 and no
  further.

**Must never learn:**

- **Anything from photos or appearance.** The field is not in the index (§7.2). This is the
  line between this product and a dating app, and it holds in the machinery, not the copy.
- **Anything correlated with protected characteristics** — name, language as a proxy for
  nationality, area as a proxy for anything at all.
- **Anything it cannot explain.** Every term must remain sayable in one sentence with the
  evidence named. **A learned model that improves the return rate by two points but cannot
  produce *"Almost exactly your level — 2,71 against your 2,68"* is a bad trade, because that
  sentence is the product.** If a signal cannot be printed, it does not ship.

That last rule is why this document contains no machine learning, and why the phrase
"ranking model" does not appear anywhere in it. The ceiling on a hand-weighted, fully
explainable scorer is high enough for a pool of this size, and the floor under an
unexplainable one is the product's whole differentiator.

---

## 15. The service

### 15.1 Layout

```
matcher/
├── cmd/
│   ├── matcher/           # the interactive HTTP service
│   ├── indexer/           # event feed → candidate index
│   └── sweeper/           # the loops of §14.5
├── internal/
│   ├── core/              # ── PURE. no clock, no I/O, no logging, no randomness ──
│   │   ├── candidate/     #    Candidate, SearchContext, Shortlist
│   │   ├── ruleset/       #    versioned weights (embedded JSON) + validation
│   │   ├── gate/          #    §9.1
│   │   ├── fit/           #    the Term interface and the eight terms
│   │   ├── modifier/      #    §9.4
│   │   ├── liveness/      #    §9.5
│   │   ├── lineup/        #    group objective, arrangement, forecasts (§9.9)
│   │   ├── evidence/      #    the reason-code vocabulary (§12.1)
│   │   └── rank/          #    the pipeline, relaxation loop, diversity
│   ├── index/             # port + postgres adapter + in-memory snapshot
│   ├── ledger/            # port + redis adapter (interest, exposure, suppression)
│   ├── ingest/            # envelope decoding, projections, idempotency
│   ├── api/               # internal HTTP handlers, auth, validation
│   └── obs/               # metrics, tracing, structured logging
├── testdata/
│   ├── scenarios/         # §20.1 — the walkthroughs, as golden files
│   └── fixtures/          # generated populations for load and rebuild tests
├── .claude/               # this app's settings and permissions (CLAUDE.md rule)
├── CONTEXT.md             # this app's *technical* vocabulary only
├── Makefile
└── go.mod
```

**`internal/core` imports nothing outside itself and the standard library's pure parts.**
Enforced in CI by a `depguard` rule forbidding `time` (clock reads), `math/rand`, `net`, `os`,
`database/sql` and any project package outside `core`. This is ADR-0015's purity rule,
transplanted, and it is what makes every test in §20 possible without a database.

### 15.2 The ports

Small, few, and named after what they answer:

```go
type CandidateSource interface {
    // one consistent snapshot, held for the life of one search
    Snapshot(shard ShardKey, sport Sport) Snapshot
}

type InterestLedger interface {
    ReceivedBy(playerID, sport) []Interest       // who said yes to me
    SentBy(playerID, sport)     []Interest
    Suppressed(from, to)        bool
}

type ExposureLedger interface {
    ShownThisWeek(playerID, sport) int
    P90(shard, sport)              int
    RecordShown(shortlist)                        // fire and forget
}

type SearchResults interface {
    Put(SearchResult) error
    Get(SearchID) (SearchResult, bool)
}

type EventFeed interface {
    Consume(ctx) <-chan Envelope
    Ack(Envelope) error
}
```

Ports and adapters, the same discipline the backend already runs. Every one of them has an
in-memory fake, and the scenario tests use only fakes.

### 15.3 Storage, and why each store is there

| Store | Holds | Why that store |
|---|---|---|
| **PostgreSQL** (matcher's own database — never shares a table with the backend) | The durable candidate index, the ingest cursor | Rebuildable, queryable, boring. Owned by the matcher and nothing else reads it |
| **In-process snapshot** | A copy of the whole index for the shard(s) this instance serves | **A search never touches a database.** 32 MB for a 50 000-player city (§7.2). This is what makes the p99 predictable |
| **Redis** | The mutable ledgers of §14.1 | Shared across instances, TTL-native, cheap to lose |

**The snapshot is the design's one clever moment, and it is not very clever:** the indexer
applies events to Postgres and to a delta buffer; the matcher swaps an `atomic.Pointer` to a
fresh immutable snapshot every few seconds. Readers never lock. A search holds one snapshot
pointer for its whole life, which is also what gives §13's determinism its meaning — the
index cannot move underneath a running search.

Rejected alternatives, briefly: **Redis-only** (not rebuildable, no relational queries for the
rebuild path); **query Postgres per search** (a p99 hostage to connection pools for no
benefit at this data size); **Elasticsearch** (a whole operational surface bought to solve a
32 MB problem).

---

## 16. The internal contract

`POST /v1/searches` · `POST /v1/lineups` · `POST /v1/deck` · `GET /v1/searches/{id}` ·
`POST /v1/interest` · `POST /v1/ingest` · `GET /healthz` · `GET /metrics`

Sketch of the two that matter:

```jsonc
// POST /v1/lineups   (request — assembled by the backend, never by the client)
{
  "at": "2026-08-25T19:00:00Z",
  "searcher": {
    "player_id": "…", "sport": "PADEL",
    "mu": 2.71, "sigma": 0.16, "counted_games": 14, "rating_status": "INITIAL_ESTIMATE",
    "play_intent": "COMPETITIVE",
    "tags": ["PLAYS_TO_WIN", "HERE_TO_IMPROVE", "STAYS_FOR_A_DRINK"],
    "grid": "001001001000011111011",
    "grid_updated_at": "2026-08-20T…",
    "area": { "lat": 50.048, "lng": 19.944 }, "search_radius_km": 8,
    "proposals_opt_in": true
  },
  "mode": "COMPETITIVE",
  "surface": "HUMAN_INITIATED",
  "availability_override": "001001001000011111011",
  "locked_seats": [],
  "exclude_player_ids": ["…"],          // live blocks/holds/open challenges from §7.5
  "seats": 4
}

// 200 response
{
  "search_id": "…",
  "ruleset_version": "2026.08.25-a",
  "snapshot_version": 918233,
  "optimised_for": "searcher",           // or "group" — §8.4
  "relaxation": { "rungs_applied": [], "radius_km_used": 8 },
  "pool": { "in_range": 11, "gated_out": 3, "below_floor": 2 },
  "lineup": {
    "sides": { "A": ["me", "kuba"], "B": ["marek", "ania"] },
    "forecast": { "pct": 91, "gap": 0.01, "a": 2.76, "b": 2.77,
                  "confidence": "HIGH", "provisional": false },
    "seats": [
      { "player_id": "kuba", "relationship": "PARTNER",
        "fit": 84,
        "terms": [
          { "term": "LEVEL_FIT", "weight": 26, "value": 0.84, "contribution": 21.8,
            "evidence": { "kind": "level_fit", "their_mu": 2.80, "my_mu": 2.71,
                          "delta": 0.09, "direction": "above" } },
          { "term": "RELIABILITY", "weight": 0, "value": null, "evidence": null,
            "no_evidence_reason": "PLAYER_SCORE_UNAVAILABLE" }
        ],
        "modifiers": [
          { "modifier": "CALIBRATION_VALUE", "points": 3,
            "evidence": { "kind": "calibration_value", "their_sigma": 0.08,
                          "my_sigma": 0.16 } }
        ],
        "liveness_reasons": [
          { "kind": "interest_received", "days_ago": 2 }
        ],
        "inclusion_reason": null
      }
    ]
  }
}
```

**Contract rules:**

- **No display strings, anywhere.** Reason codes and payloads only (§12.1).
- **No liveness number.** Reasons only (§12.2).
- **Sports, tags, day parts and intents cross the wire as the platform's machine codes** —
  the same `Sport`, `SocialTagId`, `DayPart` vocabularies the backend already serves at
  `GET /api/v1/sports` and the tag endpoint. A second spelling of a closed vocabulary is how
  two systems start disagreeing about the same word.
- **The searcher's data is passed in, not looked up.** The matcher's index copy might lag; the
  searcher's own facts must be exactly what the backend just read. It costs a few hundred
  bytes and removes an entire class of *"the app showed me my old rating"* bug.
- **Errors are `{kind, payload}` reasons**, matching the backend's `Unavailable` idiom —
  never a sentence.
- **Idempotency:** `POST /v1/searches` with the same `Idempotency-Key` returns the same
  `search_id` and the same answer.
- **Auth:** mTLS between backend and matcher, plus a network policy. No public route, ever.

---

## 17. Scale, capacity and SLOs

**Establish the size of the problem before designing for it, because the honest number kills
several tempting architectures.**

| Quantity | Realistic value |
|---|---|
| Players in a launch city | 10³ – 10⁴ |
| Candidate rows (player × sport) | ~2.5 × players |
| Candidates in range for one search | 10 – 500 |
| Bytes per candidate row | ~160 |
| Whole index, 50 000-player city | **~32 MB** |
| Searches at peak (Thursday evening) | 1 – 20 / s |

**Everything fits in memory on one instance, and the whole platform's traffic fits on two.**

Costs per search:

| Stage | Work | Time |
|---|---|---:|
| Generate | linear scan + box test over the shard | ~50 µs |
| Fit | 8 terms × ≤500 candidates | ~200 µs |
| Reciprocal fit | 8 terms × ≤40 shortlisted | ~20 µs |
| Group objective | 455 combos × 3 pairings | ~40 µs |
| Serialise | ~20 rows with full breakdowns | ~300 µs |
| **Total, in-process** | | **< 1 ms** |

**SLOs:**

| | p50 | p99 | Error budget |
|---|---:|---:|---|
| `POST /v1/searches` (matcher, server-side) | 8 ms | **60 ms** | 99.9% |
| `POST /v1/lineups` (matcher, server-side) | 12 ms | **90 ms** | 99.9% |
| End to end, client tap → answer | 120 ms | **400 ms** | 99.5% |
| Index staleness (event committed → visible) | 2 s | **15 s** | — |
| Full index rebuild, 50 000 players | — | **5 min** | exercised in CI (§7.4) |

**The scale ceiling, stated so nobody has to guess:** the in-memory snapshot holds roughly
10⁶ rows per instance (~200 MB). Beyond that, shard by `shard_key` — a metro — and route on
it at the backend. That is the reference repository's `region` idea, finally in the right
job: **a shard key, not a matching criterion.** No code above changes when it happens.

**Do not build for this in advance.** A distributed scoring cluster for a 32 MB problem is the
kind of engineering that looks like foresight and is actually a permanent tax.

---

## 18. Failure modes and degradation

Every one of these has the same first principle: **degrade honestly, never fabricate.** A
confident bad list is the one outcome worse than an error.

| Failure | Behaviour | Player sees |
|---|---|---|
| **Matcher unreachable / timing out** | Backend circuit-breaks after 800 ms, returns an `Unavailable` reason | *"The matcher is having a moment."* **Never a fallback list.** A hand-rolled backend fallback ranker would be the ADR-0015 two-implementations failure, arriving as a hotfix |
| **Redis down** | Serve without interest lift, exposure correction or *Why 78?* lookup. Metric fires | A complete, correctly-scored list with fewer liveness reasons — and *Why 78?* recomputes with a stated caveat |
| **Index lag < 15 min** | Serve normally | Nothing. A rating 12 minutes stale changes nothing anybody notices |
| **Index lag 15 min – 24 h** | Serve, flag `index_stale: true` on the response, alarm | Nothing, unless product chooses a banner. Recommend not |
| **Index lag > 24 h** | **Refuse.** Return unavailable | The honest empty state. A day-old index can put a held or blocked player in front of somebody |
| **Ruleset fails validation** | Refuse the new one, keep serving the previous, alarm loudly | Nothing |
| **A term panics** | Recovered per term; that term returns `NoEvidence` (§10) and the search completes with one fewer reason | One fewer sentence on the card. Metric fires |
| **A shard has no candidates** | Empty shortlist + `pool_description` | *"Four padel players within 8 km this week"* — §9.7 |
| **Ingest dead-letters** | Envelope to DLQ, cursor advances, alarm | Nothing immediately; the affected rows go stale and trip the staleness alarm |

Two of these are the design's convictions rather than its mechanics, and both bear repeating:

**No fallback ranker.** When the matcher is down, the feature is down. The temptation to
"just show the nearest ten players" during an incident is exactly how a second, worse,
unexplainable ranking implementation enters the system permanently.

**No fabricated confidence.** Anywhere a number would have to be guessed, the answer is
`provisional`, `NoEvidence`, or nothing at all.

---

## 19. Observability — the metrics that judge the engine

The engine is not judged by latency. It is judged by whether people play twice.

### 19.1 The report card

| Metric | Definition | Target |
|---|---|---|
| **Return rate** ⭐ | Share of first games between two people producing a second within 60 days | The number. Baseline from the pipeline: 34% lopsided / 71% even |
| **Challenge acceptance rate** | Challenges sent from a search that are accepted | > 45% |
| **Answer rate** | Challenges answered at all within 24 h | > 80% |
| **Ghost rate** | Matched → planned → never played | < 8% |
| **Forecast error** | Brier score of the balance forecast against confirmed results | Falling |
| **Search → challenge rate** | Searches that produce at least one challenge | > 35% |
| **Empty-result rate** | Searches returning nothing | Watched, not minimised — see below |
| **Exposure Gini** | Concentration of who gets shown | < 0.55 |
| **Relaxation distribution** | Share of searches per rung | Rung 4 < 5% |

**The empty-result rate is a diagnostic, not a target.** Driving it to zero means the quality
floor has been lowered, which means bad matches are being shown, which will show up in the
return rate three months later — long after whoever lowered it has moved on. It is watched
*alongside* the return rate and never optimised alone.

### 19.2 The telemetry chain, and the half of it that cannot wait

The join key that makes all of the above computable:

```
├────────── the SEARCH half ──────────┤├──────── the OUTCOME half ────────┤

search_id ─▶ candidate shown ─▶ challenge sent ─▶ accepted ─▶ planned
                                                 ─▶ played ─▶ confirmed ─▶ SECOND GAME

  Phase 1 · costs hours · UNRECONSTRUCTABLE     Phase 2 · needs the matches context
```

Every step carries `(search_id, ruleset_version, fit, terms, liveness_reasons)`.

**The two halves have completely different costs and completely different deadlines, and
treating them as one deliverable is how the whole chain slips.**

**The search half is three append-only tables and one foreign key**, and none of it depends on
a context that does not exist:

| Recorded | Holds |
|---|---|
| `search` | `search_id`, searcher, sport, mode, `ruleset_version`, `snapshot_version`, `at`, pool sizes at each stage, rungs applied, shortlist size |
| `search_candidate` | `search_id`, player, position, `fit`, every term with its contribution, liveness reasons, inclusion reason |
| `search_outcome_link` | the `search_id` and position a challenge was sent from — **the join key** |

**A search that was not recorded is evidence that no longer exists.** There is no backfill, no
reconstruction, no clever join that recovers it later. Every day this is not shipped is a day
of permanently missing denominator — which is why it lands in **Phase 1** (§22) rather than
waiting for the half that genuinely has a dependency.

**The outcome half** needs the `matches` context and lands in Phase 2, closed by the sweeper's
outcome-join loop (§14.5). Because the search half is by then already months old, the first
joins produce answers immediately rather than starting the clock.

**Without both, every number in §9 is permanently unfalsifiable**, and this document becomes a
set of opinions with good prose.

### 19.3 Operational metrics

Latency histograms per stage; index lag and row counts; ingest rate, DLQ depth and cursor
position; per-term `NoEvidence` rate (a term quietly dying is invisible otherwise); relaxation
rung histogram; ruleset version in use; snapshot age and swap rate; cache hit rate on search
results.

**Every search is logged structurally**: `search_id`, searcher, sport, mode, ruleset, snapshot,
pool sizes at each stage, rungs applied, shortlist size, latency per stage. **No PII, ever** —
ids only, which is the only thing the index holds anyway (§7.2).

---

## 20. Testing

### 20.1 Scenario tests — the walkthroughs, as executable fixtures

The mechanics document's three walkthroughs are not illustrations. They are the acceptance
suite:

**A — Competitive singles.** Tomek, 2,71 padel, narrow band, Player Score 92, Kazimierz,
declared `COMPETITIVE`.

| Candidate | Must produce |
|---|---|
| **Marek** 2,92, 57 counted, declared `COMPETITIVE` | **High fit.** Full intent marks, strong balance, mild vibe clash at weight 4 barely registering |
| **Karol** 2,75, has said *Let's play* | **Lifted to the top, with the reason printed. Fit unchanged by the lift** — asserted explicitly |
| **Bartek** 2,35, score 74, wide band, 4 expired challenges | **Shown low or not shown.** Reliability floor prints; liveness drags for the expired challenges |
| **Michał**, open unsettled case | **Absent.** Gated |
| **Inés** 3,40, 48 counted | **Docked for asymmetry.** She would score Tomek poorly; surfacing her manufactures a decline |

**B — For fun, building a four.** Weights invert; vibe leads; the group objective picks the
combination rather than the top three individuals. **Piotr, declared `COMPETITIVE`, scores
zero on intent, takes the modifier penalty, and the card says exactly that** — and his
`PLAYS_TO_WIN` tag moves the playing-style term **and nothing else** (§6.5). A test asserts
the intent term received no tag input.

**C — A newcomer's first search.** 2,50 padel, ±0,34, no counted games. Evenness and
reliability carry; vibe and distance stand down; the forecast is labelled provisional; and
**Zofia** — 27 games, no absences, 4,9 sportsmanship, a record of filling short-notice gaps —
ranks first, where the current weights would put her behind three worse choices.

Each is a golden file: a fixed population, a fixed clock, a fixed ruleset, and the complete
expected response. **A diff is a design change and must be argued for in the PR**, which is
precisely the point — it makes weight changes visible instead of quiet.

### 20.2 Property tests

- Same input + same snapshot + same ruleset ⇒ **byte-identical** output (§13).
- **Liveness never changes the printed Fit.** Generated: score a population, permute every
  liveness signal, assert every `fit` is unchanged.
- **No gated player ever appears in any shortlist**, under any relaxation rung.
- **Relaxation is monotone**: rung *n+1*'s candidate set is a superset of rung *n*'s.
- **Renormalised weights always sum to 100**, for every subset of available terms (§10).
- **`partialForecast` == `arrangedForecast`** the moment the last seat is filled.
- **Modifier totals stay inside the budget**, for every generated combination.
- **Diversity never promotes a below-floor candidate.**
- **`arrange()` returns the minimum-gap pairing** — brute-forced against all three.

### 20.3 The replay harness

**The single most valuable test asset in the system.** Record production searches (request +
snapshot version); replay them against a candidate ruleset; diff the shortlists.

```
$ matcher replay --from 2026-08-01 --ruleset 2026.09.01-b --baseline 2026.08.25-a

  12 481 searches replayed
  shortlist composition changed:      18.2%
  top-1 changed:                       7.4%
  mean fit of top-1:               76.3 → 77.1
  empty results:                    4.1% →  3.6%
  exposure Gini:                    0.51 →  0.47
  rung-4 relaxations:               2.8% →  2.2%
```

This is what turns *"vibe should be 24"* from an argument into an experiment, and it is the
reason §11 exists. **No ruleset ships without a replay diff in its PR.**

### 20.4 Load and soak

10× peak sustained for an hour with a production-sized index; assert p99 and zero allocation
growth. Plus the CI rebuild test of §7.4.

---

## 21. Security and privacy

| Concern | Control |
|---|---|
| **Public exposure** | The matcher has no public route. mTLS + network policy. The client never has its address |
| **PII** | The index holds no name, photo, email, DOB, gender or precise location. **The fields do not exist**, and a schema test asserts it (§7.2) |
| **Location precision** | Area centroids only. *"The precise fix that produced it is never a shareable value"* (`CONTEXT.md`) |
| **Logs** | Player ids only. No payload dumps |
| **Search results** | 30-minute TTL, keyed to the searcher, not readable by anybody else |
| **Passes and declines** | Never surfaced to the other party, in any response, ever. A test asserts no response shape can carry them |
| **Blocks** | Both directions, verified live by the backend (§7.5), invisible to both |
| **Held accounts** | Gated at generation, verified live |
| **The engine's own outputs** | No free text, so no injection surface and no accidental disclosure through a generated sentence |
| **GDPR erasure** | A player's rows are deleted from the index and the ledgers on the backend's erasure event. Rebuild-from-replay honours the same deletion, because the source events are the ones erased |

---

## 22. Delivery

Four phases. **Each ends in something demonstrable**, and none of them requires the next.

Two of the sequencing decisions below are load-bearing and easy to get wrong, so they are
stated before the phases rather than buried inside them:

- **The search-side telemetry ships in Phase 1, not Phase 2.** The outcome half of the chain
  (§19.2) genuinely needs the `matches` context, but the search half —
  `search_id → candidate shown → challenge sent` — costs almost nothing and **cannot be
  reconstructed retroactively**. A search that was not recorded is evidence that no longer
  exists. Half a chain from day one is worth far more than a whole chain three months late.
- **`player_score` is scheduled here, not left to Phase 3.** It is currently unscheduled work
  in another context, and it gates roughly a third of this design's value: the reliability
  term, the reliability floor, the welcoming record, the strand decomposition, and — most
  importantly — **every signal the engine has about goal #1, whether the game happens at all.**
  Left implicit, it slips. Named as a Phase 2 dependency with an owner, it does not.

### Phase 0 — Decide (days)

1. **The ADR** (§25.1): a fourth deployable, in Go, and the argument past ADR-0015.
2. **The Play intent ADR + backend field** (§6.2). It is the cheapest strong term and it
   gates the engine's best sentence. **Highest return per unit of work in the whole plan.**
3. **Schedule `player_score`.** Not build it — schedule it, with an owner and a target inside
   Phase 2. See the note above.
4. Confirm the open product decisions that change the algorithm's shape: §23.4 (whose
   radius), §23.9 (familiarity sign), §23.10 (who owns the floor).

### Phase 1 — The synchronous engine (2–3 weeks)

The whole of §9 for the five-to-six terms that have data (§10). Postgres index + in-memory
snapshot, indexer on the outbox feed, `/v1/searches` and `/v1/lineups`, singles and doubles,
relaxation, quality floor, the explainability contract, the three scenario tests, the
property tests.

**Plus the search-side telemetry**, which is small and must not wait:

| Recorded from day one | Why it cannot wait |
|---|---|
| Every search: `search_id`, searcher, sport, mode, `ruleset_version`, `snapshot_version`, pool sizes at each stage, rungs applied, shortlist size | The denominator of every rate in §19.1. Unreconstructable |
| Every candidate shown: `search_id`, player, position, `fit`, terms with contributions, liveness reasons, inclusion reason | Without it, *"which term profiles convert"* has no data, forever |
| Every challenge sent: the `search_id` it came from and the position it was sent from | The join key. **The one field that turns a search into evidence** |
| Every empty result and its `pool_description` | The only way to tell a thin pool from a broken floor |

That is three append-only tables and one foreign key on the challenge. It is hours of work,
and it is the difference between an engine that can be improved and one that can only be
argued about.

**No Redis, no ledgers, no liveness beyond what the index carries, no deck.** Liveness
degrades to a no-op (§18's Redis-down path is the day-one path), which is a legitimate,
already-designed state rather than a shortcut.

**Ships:** ⚡ *Let the engine fill the seats* and the ranked pool, working, explained, honest —
and every search from the first one is already evidence.

### Phase 2 — The market, and the evidence closing (3–4 weeks)

Redis ledgers. Interest (*Let's play*) with expiry, cap and guaranteed inclusion. The deck.
Suppression. Exposure floor, newcomer window, challenge load. The sweeper. The replay harness.

**And the two dependencies that make the engine whole:**

- **`player_score`**, scheduled in Phase 0, landing here. It turns on the reliability term, the
  reliability floor, the strand decomposition and the welcoming record — and it gives the
  engine its first evidence about whether a game will actually happen, which is goal #1 and
  currently unmeasured.
- **The outcome half of the telemetry chain** — the sweeper's outcome-join loop walking
  `matches.*` events and closing `search_id → accepted → planned → played → confirmed →
  second game`. The search half is already three months old by now, so the first joins produce
  answers immediately rather than starting a three-month wait.

**Ships:** the deck, the interest lift, reliability, and **the first evidence that any weight
in this document is right** — measured against searches that go back to launch day.

### Phase 3 — Refinement (ongoing)

History, familiarity sign and ghost tracking as `matches` matures. Tag corroboration from
*Around* and the settle-up record. Forecast-error calibration. Return rate by match profile —
and **the first weight change justified by data rather than argument**, which is the moment
this document stops being a proposal.

**Optional, and deliberately last: standing search.** *"Nobody good tonight — keep looking."*
This is where the reference repository's queue design lands in full: a player parks a search
intent, the sweeper scans as new candidates appear, and a hit becomes a **notification**, never
an automatic challenge. The engine proposes; the player decides. That rule does not bend
because the search was asynchronous.

### Rollout, for every phase

**Shadow** (matcher runs, logs its answers, serves nothing — diff against the prototype's
scores) → **canary** (5% of searches, watch acceptance and empty rate) → **full**. Ruleset
changes always go through §20.3 first.

---

## 23. Open decisions — product, not engineering

Fourteen from the mechanics document, plus four this design surfaces. Each has a
recommendation; none of them is the engine's to make alone.

| # | Question | Recommendation |
|---:|---|---|
| 1 | **Is another player's declared intent shown on their card?** | **Yes, plainly.** It is their own word about themselves, there is nothing to protect, and it makes a low score legible: *"Marek plays padel for fun"* explains it better than any euphemism. The only risk is it becoming a status label, which `NO_PREFERENCE` is designed to prevent |
| 2 | **Is the intent declaration required at onboarding, or skippable?** | **Required**, with `NO_PREFERENCE` as a first-class answer. One tap, full coverage on day one, and skippable means a chunk of the early population is unreadable at exactly the moment the pool is smallest |
| 3 | **What happens when the live search mode and the declaration disagree?** | The search governs the search; after N consecutive disagreements the app offers once to update the profile (§6.3). **Confirm N. Starting position: 5** |
| 4 | **Whose radius governs?** | **Searcher's radius is a gate; the candidate's is a liveness dock** (§9.3.8). A refinement of the mechanics document's both-sided gate — same outcome, right column, honours the glossary |
| 5 | **Do *Let's play* yeses expire, and after how long?** | **21 days**, decaying over the last 7 |
| 6 | **Is there a cap on outstanding yeses, and is it visible?** | **20 per sport, soft, invisible.** A visible cap turns a cheap gesture into a budget to manage |
| 7 | **Does the deck follow the tab you came from, or the declaration?** | **The declaration** (§9.11). The deck has no search mode of its own to read |
| 8 | **Gender and format preferences** | Support **only as a format declaration attached to a game** (*mixed doubles*, *women's doubles*), **never as a browse filter over individuals**. Handle the real safety concern separately and better — first-game-at-a-public-Spot options, and the existing block and report machinery. Handled badly this becomes the dating filter the whole product is built to avoid. It deserves a proper discussion, not a default |
| 9 | **Should familiarity flip sign for `HERE_FOR_A_REGULAR_GAME`?** | **Yes** (§9.4). It changes what the app feels like for a subset of users, so it is a product call, but penalising a player for pursuing the goal they declared is indefensible |
| 10 | **What is the quality floor, and who owns the number?** | Starting position **52**. **Somebody must be accountable for it by name** — it is the number that decides when the product says nothing rather than something |
| 11 | **Are for-fun games ever counted?** | If *never*, several terms simplify: calibration value disappears from for-fun, *confirms results* drops out of the strand weights, and the at-stake deltas vanish from the for-fun card. **Recommend: never.** The simplification is worth more than the flexibility |
| 12 | **Can a player express a partner preference — *"give me a stronger partner"*?** | **Not in v1.** It is a real want, and it conflicts with the evenness objective in a way that needs its own design. Ship the evenness default; measure how often people swap seats afterwards; that number is the answer |
| 13 | **How far may relaxation go before the app stops and says the pool is thin?** | **Rung 4 is the last** (§9.8). Beyond that, describe the pool |
| 14 | **Post-MVP: when behaviour and declaration disagree, what happens?** | **Keep it out of the matcher permanently** and route it into the refresh prompt (§6.3). The temptation to "correct" a stale declaration will be strong the moment the data exists; decide it deliberately now rather than by drift |
| **15** | **Does the matcher get its own app directory and hooks?** | **Yes.** `matcher/.claude/settings.json`, and the ownership hook learns a fourth app. Otherwise a session started in `matcher/` owns everything |
| **16** | **Where does `Play intent` live on an aggregate that is deliberately not per sport?** | It is the first per-sport fact on `PlayerProfile`. Worth an explicit note in the ADR rather than a silent precedent |
| **17** | **Does the deck's outbound half respect proposals opt-in?** | **Yes** — `surface: ENGINE_INITIATED` (§9.1). Being shown *in* the deck is a human's browse; being *notified* is a push |
| **18** | **Who owns the tag relationship matrix** (§9.3.6) — product or engineering? | **Product**, served as ruleset data. It is a claim about how people get on, not an implementation detail, and it should be arguable without a code review |

---

## 24. Constants, and the measurement that would falsify each

Every constant here is an **admitted hypothesis**. This table is the discipline ADR-0015
already requires of engine constants, applied to the matcher's.

| Constant | Start | Falsified by |
|---|---:|---|
| `LEVEL_TOL_COMP` | 0.55 | Return rate by level gap. If pairs at Δμ 0.4 return as well as 0.1, the curve is too steep |
| `FUN_FREE_BAND` | 0.25 | Satisfaction and return rate for for-fun games inside vs outside the band |
| `BALANCE` coefficients (145, 32) | v37 | Brier score of the forecast against confirmed results (§19.1). **The most directly falsifiable numbers here** |
| Competitive weights | §9.3 | Return rate by match profile. The ground truth for all eight |
| For-fun weights | §9.3 | Same, split by mode |
| Intent weight (14, both modes) | §6.4 | Return rate for aligned vs misaligned first games. **If this is not among the strongest predictors, §6 is wrong** |
| Strand weights | §9.3.4 | Ghost rate and answer rate regressed on each strand separately |
| `QUALITY_FLOOR` | 52 | Return rate of games from candidates just above vs just below it |
| `MIN_SHORTLIST` | 3 | Search → challenge rate by shortlist size |
| Relaxation multipliers | §9.8 | Acceptance rate per rung. A rung whose matches never convert should be removed, not tuned |
| `INTEREST_TTL` | 21 d | Acceptance rate of interest-lifted candidates by age of the yes |
| `PASS_SUPPRESS` | 30 d | Pass rate on re-shown profiles |
| `ASYM_TOLERANCE` | 12 | Decline rate by asymmetry bucket |
| Diversity λ | 8 | Challenge rate on positions 2–5 with and without |
| Exposure lifts | §14.2 | Exposure Gini, and 30-day retention of low-exposure players |
| Challenge-load thresholds | §14.4 | Answer rate by open-challenge count |
| `K` (group candidate cap) | 16 | Whether the winning combination ever contains a candidate ranked > 16 |
| Tag `φ` (0.45) | §9.3.6 | Return rate by shared-tag count. If flat, diminishing returns is too weak |
| `CLASH_CAP` | 0.25 | Return rate of games with a scored clash |
| Partner/opponent multipliers | 1.6 / 0.7 | Post-game sportsmanship and return rate, partner vs opponent |

**None of these is measurable before §19.2's telemetry chain exists.** That is why the chain
is Phase 2 and not Phase 4.

---

## 25. The ADRs this requires

| # | Records | Notes |
|---|---|---|
| **1** | **A matchmaking service as a fourth deployable, in Go** | Amends **ADR-0005** (three-app monorepo); argues explicitly past **ADR-0015**'s rejection of an engine microservice, on the grounds the matcher owns state and a lifecycle (§4.3). Must also cover the ownership hook, `matcher/.claude/`, and the CI lane |
| **2** | **The matcher is a read model built from the backend's event feed** | CQRS across a service boundary. The index is disposable and rebuildable; the backend is always right; the three live-verified gates (§7.5) |
| **3** | **Fit and Liveness are separate and never summed** | The explainability contract, enforced by types (§12.2). The one the product cannot afford to lose |
| **4** | **Play intent is a declared, per-sport profile field** | New domain term, new event, and the argument for why declaring intent is legitimate where declaring a level is not (§6.1). Also the first per-sport fact on a deliberately not-per-sport aggregate |
| **5** | **Rulesets are versioned configuration; every search records its version** | What makes §20.3 and any honest A/B possible (§11) |
| **6** | **Evidence crosses the wire as reason codes, never sentences** | Extends **ADR-0022** to the matcher. The clients own the words (§12.1) |

Plus glossary work: §5's vocabulary goes into the root `CONTEXT.md`, `Play intent` into the
player-profile section, and `CONTEXT-MAP.md` learns a fourth app.

---

## 26. The shape of it, in one page

**The engine's job, in priority order:** make the game happen · make it good · make them play
again. The report card is the **return rate**.

**Two numbers, never added.** **Fit** is quality and is printed. **Liveness** is likelihood
and only moves position. The type system enforces it.

**Eight terms, renormalising.** A term with no evidence stands down and its weight
redistributes — which is what lets five terms ship on Monday and eight ship next year without
a rewrite.

**Gates are absolute; weights persuade; the player decides.** Eight gates, four relaxation
rungs in a stated order, four things never relaxed, and an honest empty state underneath
everything, because **a bad match is worse than no match**.

**Doubles optimises the group,** not the sum of pairs, and it distinguishes the partner
relationship from the opposing one.

**The matcher runs a small market,** so it spends exposure deliberately: a floor for the
unseen, a window for newcomers, a throttle for the flooded, and variety in the top five.

**Everything is a hypothesis.** The weights are versioned configuration, every search records
which version produced it, every outcome joins back to the search that started it, and no
ruleset ships without a replay diff.

**From the reference repository** the design keeps the service decomposition, the Redis
queue-and-sweep spine for background work, region-as-a-shard, and the one genuinely good
idea — relaxation over time, rebuilt as a stated ladder with floors and an announcement. It
drops the pairing algorithm, the WebSocket layer, and the entire Kubernetes game orchestrator,
because **there is no game server: the court is the players' problem, and saying so is the
product's honesty.**

---

*Weights and thresholds here are starting positions, not conclusions. §19.2 describes the only
evidence that can settle them, and §24 says what each one dies of.*
