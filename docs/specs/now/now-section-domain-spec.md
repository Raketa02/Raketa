# The Now Section — Domain Logic Specification

**Feature in scope:** the Now screen (`V.home`) and its complete transitive call graph.
**Target stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 (server, engine, schema) ·
TypeScript 5 (card contract, client derivation). Signatures below are Python unless the type is
a wire contract, which is given in TypeScript.

---

# A. ARCHITECTURAL POSITION

## A.0 Normative basis, and where the sources contradict each other

Four of the five sources describe the system that **should** be built; one — the prototype —
**is** the system that exists and produces every number in this document. They disagree in
places, and the disagreements are load-bearing.

| Question | Prototype (v37) | Documents 3 / 3.1 / 4 | Review (doc 5) | **Normative here** |
|---|---|---|---|---|
| Fit model | 7 terms + 3 modifiers, clamp 20–99 | same 7 terms | **superseded** — 10 terms, no modifiers, no clamp, `coverage` reported separately (A1) | **Prototype**, with every supersession flagged `[SUPERSEDED-A1]` |
| Who owns copy | client (all strings in `ST`) | server ("every string comes from the server") | **client** — server sends `{key, tone, facts}` (A5) | **Review** — the prototype already agrees |
| State count | **35** contexts | 33 | 33 + leaver group (B3) | **35**, and B1/B3 marked as GAPs |
| Transition hint | none | `nextTransition: {at, becomes}` | `transitions: [{at,key,tone,facts}]` (A6) | **Review** — a list, not a head |
| Client derivation | full recompute per render | client has the kernel | client holds **no** rules, only a transition list (A5/A6/E3) | **Review** |

`1-now_screen_production_spec.md` is cited throughout doc 5 but was **not supplied**. Every
reference to "Now §n" below is second-hand through doc 5. **[GAP-0]** Sections §2.2 (colour
semantics), §3.9 (`.fit.hi` rule), §5.2 (Match Fit), §6.5 (standby position), §7.4/§8.2/§8.3
(client derivation) are known only as quotations. Anything in this specification that depends
on them is marked.

## A.1 What the Now section is

Now is a **read-only projection over two engines it does not own**:

```
                    ┌────────────────────────────────────────────┐
                    │            GET /now  (composeNow)          │
                    └───────────────┬────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌──────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ ① ENROLLED STRIP │     │ ② BEST-FIT LANE    │     │ ③ FULL-WORTH LANE  │
│ my matches       │     │ open, not mine     │     │ full, not mine     │
│ sorted by start  │     │ sorted by fit desc │     │ cap 1              │
│ cap: none        │     │ cap 3              │     │                    │
└────────┬─────────┘     └─────────┬──────────┘     └─────────┬──────────┘
         │                         │                          │
         ▼                         ▼                          ▼
   matchState(m)              matchFit(m)                matchFit(m)
   [OWNED: derivation]        [OWNED: ranking]           [OWNED: ranking]
         │                         │
         ├──▶ courtHold(m, now) ───┴──▶ forecast(m) ──▶ bestPairing ──▶ teamStrength
         ├──▶ deadlines(m, policy)     seatTarget(m) / targetBand(m)
         ├──▶ committedNow / committedOnFill / filled / isFull / isProtected
         └──▶ payable(m) ──▶ shareAfterDisc ──▶ slotDisc ──▶ pol(club)
                          └──▶ cardOff ──▶ CLUBS[club].card[sport]
```

**Callers of this feature:** the mobile client's Now tab, on open and on pull-to-refresh.
**What depends on its output:** nothing else reads the composed screen; every consumer reads
the underlying engines directly. This is deliberate — the screen is a *view*, and the review's
finding E3 exists because the prototype blurred that.

## A.2 OWNED vs READ

| Computation | Owner | Failure mode when absent |
|---|---|---|
| `matchState` — which of 35 contexts | **OWNED** by the enrolled-match kernel, called here | none — pure function of record + clock |
| `courtHold` base ladder (rungs 1–10) | **OWNED** | none — pure |
| `courtHold` stale rung (`maxHoldAge`) | **READ** from `ClubPolicy.maxHoldAge` | absent ⇒ `maxHoldAge = null` ⇒ rung never fires ⇒ hold persists longer than the club wants. Fails **safe for the player**, unsafe for the club. |
| `courtHold` extended rung | **READ** — `m.clubExtended`, `m.clubFill`, `pol.probHold` | absent ⇒ no extension ⇒ court released at the ladder floor. **Fails safe.** This is Invariant 6: *this app never recomputes a club's model* [SRC: v37 doc §0.2] |
| `deadlines.commit` | **OWNED** — `min(start − window·h, start − 12h)` | `window` absent ⇒ default 24 [SRC: proto `pol()`] |
| `deadlines.joinCut` | **READ** `ClubPolicy.joinCut` | absent ⇒ default 30 min |
| checkpoint outcome (`rebook` vs `short`) | **READ** `CLUBS[club].rebooking` | absent ⇒ falsy ⇒ standard club ⇒ **no cancellation**. Fails toward keeping the match alive |
| `courtId` allocation | **READ** from club inventory (`pickCourt`) | none free ⇒ `inventoryLost` + `clubCancelled`, **terminal**, everybody refunded |
| fill probability (`clubFill`) | **READ ONLY — MUST NOT be computed locally** | shown as "high" instead of a percentage [SRC: proto `ST.heldExtended`] |
| player ratings (μ, σ, conf, n) | **READ** from the rating engine | `lv()` returns null ⇒ `matchFit` returns `{score: null}` ⇒ **the card is dropped from the feed entirely** (`.filter(x => x.f.score != null)`) |
| Player Score | **READ** | missing player ⇒ treated as score 100 in `passes()`, but `matchFit` uses `PLAYERS[id]` and **drops unknown ids** from `others` |

## A.3 The three architectural constraints the sources state as absolute

1. **No state is stored.** *"There is no `status` column. Nothing writes `state = 'CONFIRMED'`."*
   [SRC: 3.1 §1.1]. The state is recomputed from the record plus `now` on every read.
   Storing it *"creates a value that can disagree with its own inputs, and every failure mode
   becomes wrong instead of late"* [SRC: 3 §7.4].
2. **This app never recomputes a club's model.** Hold extension and fill probability are read
   as published facts. *"A player application running its own copy of a club's model will
   eventually show a court held that the club has already released. That is the worst failure
   this system can have, and it is silent"* [SRC: v37 §0.2 Invariant 6].
3. **Never relax a criterion to fill a lane.** *"We do not invent players to make a city look
   busy"* [SRC: 4 §1.3, and the literal empty-state string in `V.home`]. An empty lane is a
   true answer.

Two further constraints from doc 4 that the prototype does **not** implement:
`MatchScoringContext` must be keyed by `matchId:recordVersion` and is *"never stale"* (§6.1);
the player feed cache is TTL 60 s and **must** be dropped on the player's own join/create/
waitlist actions (§6.1).

---

# B. DATA MODEL

## B.1 Match — every field the Now section reads or writes

`S` = stored · `D` = **DERIVED, MUST NOT BE PERSISTED** · `A` = allocation (stored, not derivable)
· `R` = side-effect receipt (stored so an effect is not run twice; **also** derivable)

| Field | Type | Null | Unit | Range | Default | Writer | Kind |
|---|---|---|---|---|---|---|---|
| `id` | `str` | no | — | — | — | creator | S |
| `kind` | `'open'\|'private'` | no | — | — | `'open'` | creator | S |
| `sport` | enum(Padel,Tennis,Squash,Badminton) | no | — | — | — | creator | S |
| `fmt` | `'Singles'\|'Doubles'` | no | — | — | `SPORTS[sport].fmt[0]` | creator | S |
| `club` | club id | no | — | 9 seeded | — | creator | S |
| `category` | str (surface) | no | — | per club/sport | `defaultCategory()` | creator | S |
| `start` | instant | no | ms epoch | — | — | creator; **mutable via consented Stage 4 shift ±30/60/90 min** | S |
| `dur` | int | no | minutes | 30–120 | 90 | creator | S |
| `created` | instant | no | ms epoch | — | `start − 3d + 30min` | creator | S |
| `n` | int | no | seats | 2 or 4 | `SPORTS[sport].players` | creator | S |
| `price` | int | no | zł (whole) | — | `courtPriceOf()` | creator | S |
| `share` | decimal | no | zł | ≥0 | `round(price/n, 2)` | **creator, once, never re-priced** | S |
| `counts` | bool | no | — | — | `true` | creator | S |
| `seats[i].p` | player id | **yes** | — | — | `null` | join/leave/invite | S |
| `seats[i].paid` | bool | no | — | — | `false` | payment; **cleared only on an uncommitted leave** | S |
| `seats[i].at` | instant | yes | ms | — | `null` | payment | S |
| `courtId` | court id | yes | — | — | `null` | ladder | **A** |
| `protectedAt` | instant | yes | ms | — | `null` | ladder, on first assignment | S |
| `holdKind` | `'hard'\|'soft'\|null` | yes | — | — | `null` | ladder, **recomputed on every sync** | **D-as-S — see B.4** |
| `releasedAt` | instant | yes | ms | — | `null` | ladder, on release | S |
| `committedAt` | instant | yes | ms | — | `null` | commitment rule | **S — irreversible, never unwritten** |
| `vacated` | player id | yes | — | — | `null` | leave | S |
| `vacatedAt` | instant | yes | ms | — | `null` | leave | S |
| `rescueTaken` | bool | no | — | — | `false` | 50 % fill | S, irreversible |
| `transferring` | bool | no | — | — | `false` | leaver names a handover | S |
| `courtLocked` | bool | no | — | — | `false` | club manager | S |
| `clubExtended` | bool | no | — | — | `false` | **club publishes** | S (external) |
| `clubFill` | int | yes | % | 0–100 | `null` | **club publishes** | S (external) |
| `inventoryLost` | bool | no | — | — | `false` | ladder | **R** — terminal |
| `clubCancelled` | bool | no | — | — | `false` | club / inventory loss | **R** — terminal |
| `weather` | bool | no | — | — | `false` | club | S |
| `formCancelled` | bool | no | — | — | `false` | checkpoint | **R** — terminal |
| `checkpointCancelled` | bool | no | — | — | `false` | checkpoint | **R** — terminal |
| `sponsoredGuest` | bool | no | — | — | `false` | leaver's group | S |
| `noShow` | player id \| null | yes | — | — | `null` | check-in absence | S |
| `score` | str | yes | — | — | `null` | any of the four | S |
| `confirmed` | bool | no | — | — | `false` | opposing side | S |
| `waitlist` | player id[] | no | — | — | `[]` | waitlist join | S |
| `left` | bool | no | — | — | `false` | **my** leave (client-local flag) | S — see **[GAP-B3]** |
| `forced` | state key | yes | — | — | `null` | **demo only — must not survive** | — |

### Fields that are DERIVED and must never be columns

```
filled(m)          = count(s for s in seats if s.p and s.paid)
isFull(m)          = all(s.p and s.paid for s in seats)
everFull(m)        = committedAt is not None or isFull(m)
isProtected(m)     = courtHold(m, now).kind != 'none'      ← NOT courtId != null
isHardHold(m)      = courtHold(m, now).kind == 'hard'
committedNow(m)    = committedAt is not None or (now >= commit and isFull(m))
committedOnFill(m) = committedAt is not None and committedAt > commit + 60_000
seatsLeft(m)       = n - filled(m)
matchEnd(m)        = start + dur*60_000
resultWindow(m)    = matchEnd(m) + 30*60_000
keepUntil(m)       = matchEnd(m) + 24*3_600_000
state(m, now)      = the §E ladder            ← the loudest one. NEVER a column.
tag/tone/context/court/group/lines/alert      ← all derived from state + facts
```

> **`isProtected` is not `courtId != null`.** The prototype defines it as
> `courtHold(m).kind !== 'none'` [SRC: proto ln 523]. These disagree during the window between
> a threshold crossing and the next `syncMatch` write. Doc 3.1 §5 `protectedBack` says
> *"a court is still held"* and doc 5 C2 says a read of a lapsed hold *"says `protectedCourt`
> while the ladder says no court is held"*. **Use the ladder, never the column.**

## B.2 The three kinds of stored fact (review C3 — this distinction is load-bearing)

| Kind | Fields | Why stored | May a reader re-derive it? |
|---|---|---|---|
| **Allocation** | `courtId` | a court is a scarce resource, not a computation | **no** |
| **Irreversible crossing** | `committedAt`, `share`, `rescueTaken` | the inputs stop supporting the derivation afterwards | **no** |
| **Side-effect receipt** | `inventoryLost`, `clubCancelled`, `formCancelled`, `checkpointCancelled`, `releasedAt` | so the refund/notification is not run twice | **yes, and it must** — see C2 |

**Why `committedAt` cannot be derived** [SRC: 3.1 §1.2]: commitment requires *deadline passed
**and** match full*. If a player leaves after commitment the match is no longer full, so a
derived `committedNow` would compute **false** and retroactively release three people who were
already bound. *"Without it, one person dropping out at T−3h would retroactively release the
other three."*

## B.3 Identity, uniqueness, referential rules

```
PK   match.id
UQ   (match_id, seat_index)                     — exactly n rows, seat_index ∈ [0, n)
UQ   (match_id, player_id) WHERE player_id IS NOT NULL   — a player holds at most one seat
UQ   (court_id, slot_start, slot_end)           — ← DOES NOT EXIST in the prototype. See C1.
FK   match.club_id → club.id
FK   match.court_id → court.id                  — nullable
CK   share = round(price / n, 2)                — asserted at insert, never on update
CK   committedAt IS NULL OR committedAt >= created
CK   NOT (committedAt IS NOT NULL AND courtId IS NULL)    — invariant 3, §G
```

## B.4 `holdKind` is a stored copy of a derived value — and it is wrong

`syncMatch` writes `m.holdKind = hold.kind` on every pass [SRC: proto ln 3506], and
`matchState` then reads `courtHold(m).kind` rather than `m.holdKind`. The column is written
and never read by the derivation. **Do not port it as a column.** Keep it only as a
denormalised read-model field for the timekeeper index, recomputed on every write, and never
consult it in a guard. [DERIVED: two code paths, one writer, zero readers]

## B.5 Production schema (PostgreSQL 16)

```sql
CREATE TYPE hold_kind AS ENUM ('hard','soft','none');

CREATE TABLE matches (
  id                    text PRIMARY KEY,
  version               bigint      NOT NULL DEFAULT 1,   -- optimistic concurrency
  kind                  text        NOT NULL DEFAULT 'open',
  sport                 text        NOT NULL,
  fmt                   text        NOT NULL,
  club_id               text        NOT NULL REFERENCES clubs(id),
  category              text        NOT NULL,
  court_id              text        NULL REFERENCES courts(id),
  start_at              timestamptz NOT NULL,
  duration_min          smallint    NOT NULL,
  created_at            timestamptz NOT NULL,
  seat_count            smallint    NOT NULL CHECK (seat_count IN (2,4)),
  price_grosze          integer     NOT NULL,
  share_grosze          integer     NOT NULL,   -- WRITE ONCE. No UPDATE grant.
  counts                boolean     NOT NULL DEFAULT true,
  protected_at          timestamptz NULL,
  released_at           timestamptz NULL,
  committed_at          timestamptz NULL,       -- WRITE ONCE, NULL→value only
  vacated_player_id     text        NULL,
  vacated_at            timestamptz NULL,
  rescue_taken          boolean     NOT NULL DEFAULT false,
  transferring          boolean     NOT NULL DEFAULT false,
  court_locked          boolean     NOT NULL DEFAULT false,
  club_extended         boolean     NOT NULL DEFAULT false,
  club_fill_pct         smallint    NULL CHECK (club_fill_pct BETWEEN 0 AND 100),
  inventory_lost        boolean     NOT NULL DEFAULT false,
  club_cancelled        boolean     NOT NULL DEFAULT false,
  weather               boolean     NOT NULL DEFAULT false,
  form_cancelled        boolean     NOT NULL DEFAULT false,
  checkpoint_cancelled  boolean     NOT NULL DEFAULT false,
  sponsored_guest       boolean     NOT NULL DEFAULT false,
  no_show_player_id     text        NULL,
  score_text            text        NULL,
  result_confirmed      boolean     NOT NULL DEFAULT false,
  -- denormalised, maintained by the write path, never read by a guard
  seats_free            smallint    NOT NULL,
  terminal              boolean     NOT NULL DEFAULT false,
  next_wake_at          timestamptz NULL,
  wake_reason           text        NULL,
  CONSTRAINT committed_implies_court CHECK (committed_at IS NULL OR court_id IS NOT NULL)
);

CREATE TABLE seats (
  match_id   text     NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  seat_index smallint NOT NULL,
  player_id  text     NULL REFERENCES players(id),
  paid       boolean  NOT NULL DEFAULT false,
  paid_at    timestamptz NULL,
  PRIMARY KEY (match_id, seat_index)
);
CREATE UNIQUE INDEX seats_one_per_player
  ON seats (match_id, player_id) WHERE player_id IS NOT NULL;

-- the timekeeper's entire input (doc 3 §2.3)
CREATE INDEX idx_wake ON matches (next_wake_at)
  WHERE next_wake_at IS NOT NULL AND terminal = false;

-- the Now strip: "my matches, soonest first"
CREATE INDEX idx_my_matches ON seats (player_id) INCLUDE (match_id) WHERE player_id IS NOT NULL;
CREATE INDEX idx_strip ON matches (start_at) WHERE terminal = false;

-- lane retrieval (doc 4 §3.1)
CREATE INDEX idx_feed_open ON matches (club_id, start_at)
  WHERE kind='open' AND terminal=false AND seats_free > 0;
CREATE INDEX idx_feed_full ON matches (club_id, start_at)
  WHERE kind='open' AND terminal=false AND seats_free = 0;

-- the court hold as a reservation, NOT a field on the match (review C1)
CREATE TABLE court_holds (
  court_id   text        NOT NULL REFERENCES courts(id),
  slot_start timestamptz NOT NULL,
  slot_end   timestamptz NOT NULL,
  match_id   text        NOT NULL REFERENCES matches(id),
  kind       hold_kind   NOT NULL,
  EXCLUDE USING gist (court_id WITH =, tstzrange(slot_start, slot_end) WITH &&)
);
```

## B.6 Where the prototype's in-memory shape must change to survive concurrency

| Prototype shape | Breaks because | Production |
|---|---|---|
| `S.matches` — a plain object mutated in place by `syncMatch` during **render** | a read path that writes; two concurrent renders lose writes | `evaluate()` is pure and returns a `FactDelta`; only the command handler applies it |
| `m.vacated` — a single player id | *"a second `vacated` overwrites the first"* [SRC: 3.1 §9.3]; with four seats and a four-hour window a second departure is *"a normal Saturday"* [SRC: 5 B8] | `vacancies: [{seat_index, player_id, at, outcome}]` |
| `m.left` — a boolean on the shared match | `left` is *my* fact stored on a shared object; with four viewers it is four different answers | move to the seat, or to a per-player enrolment row |
| `_bk` — a module-level memo of generated bookings | process-local cache of another system's data | read the club's real calendar; no memo |
| `m.courtId` as the exclusion mechanism | two matches at the same club/category/hour both read the free list and both take the same court [SRC: 5 C1] | the `court_holds` exclusion constraint above |

---

# C. CONSTANTS AND CONFIGURATION

## C.1 Platform-invariant constants — safe to hardcode

| Name | Value | Unit | Meaning | Used in | Who may change |
|---|---|---|---|---|---|
| `HOLD_FAR` | `12` | hours | 2-paid soft hold lapses here | `courtHold` rung 7/8 | platform |
| `HOLD_NEAR` | `4` | hours | (n−1)-paid soft hold lapses here | `courtHold` rung 5/6 | platform |
| commitment floor | `12` | hours | `commit = min(start − window, start − 12h)` | `deadlines` | platform |
| rescue window, doubles | `4` | hours | `rescue = start − 4h` | `deadlines` | platform |
| rescue window, singles | `6` | hours | `rescue = start − 6h` | `deadlines` | platform |
| checkpoint | `2` | hours | `check = start − 2h`, **cannot be switched off** | `deadlines` | platform |
| door-code lead | `15` | minutes | `full → ready` at `start − 15min` | ladder rung 10 | platform |
| `RESULT_MIN` | `30` | minutes | result window after `matchEnd` | `resultWindow` | platform |
| `KEEP_H` | `24` | hours | card leaves Now at `matchEnd + 24h` | strip filter | platform |
| late-fill tolerance | `60_000` | ms | `committedOnFill ⟺ committedAt > commit + 60s` | `committedOnFill` | platform |
| `HOLD_H` | `2` | hours | invited-seat hold, base | `holdUntil` | platform |
| short-notice hold | `30` | minutes | if `start − from < 4h` | `holdUntil` | platform |
| quiet hours | `22:00 → 08:00` | local | a hold expiring inside is pushed to 08:00 | `holdUntil` | platform |
| `SCORE_MIN` / `GATE_MIN` | `70` / `70` | points | browse filter / host join gate — *deliberately the same line* | `passes`, join gate | platform |
| `PEAK` | `1020` (17:00) | min-of-day | evening rate begins | `courtPriceOf` | platform |
| `OPEN` | `[420, 1320]` (07:00–22:00) | min-of-day | every club's hours in the seed | `courtFree` | **[GAP-C1]** per-club in production |
| `SPORTS[x].players` | Padel 4 · Tennis 2 · Squash 2 · Badminton 4 | seats | the divisor in `share` | `shareOf` | platform |
| slot grid | `30` | minutes | start-time granularity | `freeStarts` | platform (*"Changing to fifteen is one constant"*) |

## C.2 Match Fit constants — platform, versioned  `[SUPERSEDED-A1]`

| Name | Value | Unit | Meaning | Used in |
|---|---|---|---|---|
| weight, skill overlap | `30` | — | | `matchFit` term 0 |
| weight, predicted balance | `20` | — | | term 1 |
| weight, group reliability | `15` | — | | term 2 |
| weight, time and travel | `15` | — | | term 3 |
| weight, match type | `8` | — | | term 4 |
| weight, price vs ceiling | `7` | — | | term 5 |
| weight, preferences and side | `5` | — | | term 6 |
| **weights sum** | **`100`** | — | assert at module load | doc 4 §9.1 |
| overlap half-width | `0.55` | level | `max(0, 1 − |myLevel − target| / 0.55)` | term 0 |
| balance default | `0.70` | ratio | used when `forecast` is `null` | term 1 |
| reliability default | `0.80` | ratio | used when nobody else is seated | term 2 |
| reliability min/mean split | `0.5 / 0.5` | — | `(0.5·min + 0.5·mean) / 100` | term 2 |
| travel free allowance | `20` | minutes | distance below this scores 1.0 | term 3 |
| travel decay | `18` | minutes | `max(0, 1 − max(0, dist − 20)/18)` ⇒ 0 at 38 min | term 3 |
| counted / friendly | `1.0` / `0.72` | ratio | | term 4 |
| price ceiling | `30` and `30` | zł | `clamp(0,1, 1 − (payable − 30)/30)` ⇒ 0 at 60 zł | term 5 |
| preferences placeholder | `0.9` | ratio | **hard-coded stub** | term 6 |
| modifier, promotion | `+8` | points | `m.badge === 'Promotion'` | after sum |
| modifier, all-new opponents | `+5` | points | `known === 0 and others.length > 0` | after sum |
| modifier, same four again | `−8` | points | `others.length >= 3 and known === others.length` | after sum |
| `REGULARS` | `['kuba','ola']` | — | **hard-coded stub** for "people you play with" | modifiers |
| score clamp | `[20, 99]` | points | applied **after** modifiers, **after** rounding | `matchFit` |
| warning threshold | `0.55` | raw value | warn ⟺ lowest-**contribution** term's **raw** value < 0.55 | `matchFit` |
| reasons | top **3** by contribution | — | `weight × value`, not raw value | `matchFit` |
| `.fit.hi` badge | `>= 90` | points | coral badge **[GAP-0 · doc 5 A2/E2 say gate on coverage too]** | `matchCard` |

## C.3 Forecast constants — platform

| Name | Value | Meaning |
|---|---|---|
| gap coefficient | `145` | `pct = 100 − gap×145 − spread×32` |
| spread coefficient | `32` | as above |
| pct clamp | `[35, 96]` | `max(35, min(96, round(...)))` |
| favourite slope | `72.5` | `fav = min(86, 50 + gap×72.5)` — **exactly half of 145, by construction** |
| favourite cap | `86` | |
| team strength | `0.45 / 0.55` | `0.45·max(a,b) + 0.55·min(a,b)` — the **weaker** player weighs more |
| confidence bands | `<0.28 high`, `<0.42 medium`, else `low` | on `spread` |
| `unsure` flag | `spread > 0.42` | |
| seat-target grid | `1.00 → 5.00 step 0.01`, tie-break `gap < best − 1e-9` | `seatTarget` |
| target band | `avg ± 0.20`, rounded to 2 dp | `targetBand` |

## C.4 Now-screen composition constants

| Name | Value | Meaning | Source |
|---|---|---|---|
| strip cap | none | every enrolled match is shown | `V.home` |
| strip sort | `start` ascending | *"which never changes"* — **false, see B4/§F.5** | `V.home`, doc 3 §1.3 rule VI |
| best-fit cap | `3` | `feed.slice(0,3)` | `V.home` |
| best-fit floor | **none** | *"a player with nothing booked needs a suggestion more than a purity threshold"* | doc 4 §3.4 |
| full-worth cap | `1` | `full.slice(0,1)` | `V.home` |
| full-worth floor | **none in the prototype**; `80` in doc 4 | **discrepancy — see [GAP-C2]** | `V.home` vs doc 4 §3.4 |
| full-worth empty state | render nothing | not an empty card, not a reassurance | doc 4 §3.4 |
| best-fit empty state | *"Nothing open in {sport} right now / We do not invent players…"* | | `V.home` |
| global feed cap | `6` | across all lanes | doc 4 §3.5 |
| diversity | `MaxPerClubHour(2)` | open lane only | doc 4 §3.4 — **not in the prototype** |
| feed cache TTL | `60` s | plus explicit drop on own actions | doc 4 §6.1 |
| retrieval `LIMIT` | `300` | *"a safety valve, not a product decision"* | doc 4 §3.1 |

> **[GAP-C2] The full-worth floor.** `V.home` applies **no** floor and no fit sort to the full
> lane — it takes `full.slice(0,1)` in `Object.values` insertion order. `V.find` applies
> `>= 80` and sorts by fit. Doc 4 §3.4 specifies `floor: 80, cap: 1`. **Proposal: adopt
> `floor 80`, sort by `FEED_ORDER`, cap 1.** The prototype's behaviour is an oversight — with
> the seeded data it happens to pick `m2` at fit 94, which masks it.

## C.5 Configuration read at runtime — NOT safe to hardcode

Read from `ClubPolicy` (`pol(club)` = `POLICY_BASE` ⊕ `POLICY[club]` ⊕ `{window, joinCut}`):

| Key | Base default | Seeded range | Effect |
|---|---|---|---|
| `window` | `24` | `12` (Atlantic, Centrum) · `24` | `commit = min(start − window·h, start − 12h)` |
| `joinCut` | `30` | `20` · `30` | `joinCut = start − joinCut·min` |
| `maxHoldAge` | `null` | `null` · `24` · `48` · `72` | soft hold older than this → `heldStale` |
| `probHold` | `false` | `true` for `ps`,`as`,`cen` | enables the `heldExtended` rung |
| `checkpoint` | `'short'` | `'short'` · `'rebook'` | **[GAP-C3]** see below |
| `rebooking` (on `CLUBS`) | — | `true` · `false` | the field `syncMatch` **actually reads** at the checkpoint |
| `holdFar` / `holdNear` | `12` / `4` | never overridden | published but unused — **[GAP-C4]** |
| `softDoubles` | `true` | never overridden | published but unused |
| `alloc` | `'fcfs'` | `fair`·`member`·`lottery`·`fcfs` | contested-hour policy (not Now) |
| `checkinMin` | `15` | `10` · `15` | QR opens this early (not Now) |
| `slotDisc` | `{}` | `{}` | court-price discount by `club|dow|hh:mm` |
| `card[sport]` (on `CLUBS`) | — | `0` · `15` · `'full'` | `cardOff` |
| `dist` (on `CLUBS`) | — | `6`–`19` min | `matchFit` travel term |
| `pm` (club multiplier) | `1.0` | `0.86`–`1.10` | `courtPriceOf` |
| `court.pm` | `1.0` | `0.90` · `1.33` | `courtPriceOf` |

> **[GAP-C3] Two sources of truth for the checkpoint policy.** `POLICY[club].checkpoint`
> (`'rebook'`/`'short'`) and `CLUBS[club].rebooking` (boolean) encode the same fact and are
> **independently seeded**. `syncMatch` and `tlZones` read `CLUBS[...].rebooking`; the Club
> rules screen shows `pol().checkpoint`. They agree in the seed (`ps` rebook/true, `as`
> short/false, …) but nothing enforces it. **Proposal: delete `CLUBS.rebooking`; derive it as
> `pol(club).checkpoint == 'rebook'`.** A drift here cancels a match that should have lived,
> or keeps alive one that should have been credited — money in both directions.

> **[GAP-C4] `holdFar`/`holdNear` are published as club-configurable and read as platform
> constants.** `courtHold` uses the module constants `HOLD_FAR`/`HOLD_NEAR`, never
> `P.holdFar`/`P.holdNear`. Doc 3.1 rule 12 says *"the ladder is a floor"* — a club may hold
> **longer**, never shorter. **Proposal: keep the ladder thresholds platform-invariant
> (`HOLD_FAR`/`HOLD_NEAR`), delete the two keys from the published policy, and express club
> extension only through `probHold` + `clubExtended`, which is already the one-directional
> mechanism.** This also resolves doc 5 B5 (rules 11 and 12 contradicting).

---

# D. ENGINES AND ALGORITHMS

## D.0 The override chains — read this before any other entry

The prototype layers versions by capturing a name and reassigning it at top level. Four
functions in this call graph are affected. **The behaviour specified below is always the final
composed behaviour.**

| Name | Base declaration | Later assignment | Composition | Short-circuit |
|---|---|---|---|---|
| `deadlines` | `function deadlines(m)` ln 467 | `deadlines = function(m)` ln 5842 | **full replacement** — base is dead code | n/a |
| `courtHold` | `function courtHold(m)` ln 502 | `courtHold = function(m)` ln 5858, capturing `_courtHold` | **wrapper**: calls base, then may override | returns base **unchanged** if `kind==='private' \|\| courtLocked \|\| committedAt != null` |
| `matchState` | `function matchState(m)` ln 3561 | `matchState = function(m)` ln 5895, capturing `_matchState` | **wrapper**: calls base, then may rewrite the key | returns base **unchanged** if `m.forced \|\| kind==='private'` |
| `payable` | `function payable(m)` ln 871 | `payable = function(m)` ln 5947, capturing `_payable` | **full replacement** — `_payable` is captured and never called | n/a |
| `freshState` | ln 314 | ln 5976 (v36) **then** ln 6649 (v37) | **two wrappers, both call through** | none |
| `render` | ln 3901 | ln 6584 | wrapper: calls base, then appends the Inbox badge | returns early if no open requests |

Specifying `courtHold` from its `function` declaration alone yields a ladder with 10 rungs.
The real ladder has **12**. Specifying `matchState` from its declaration yields 33 states. The
real table has **35**.

---

## D.1 `composeNow` — the screen

**D1 · Signature**
```python
def compose_now(player_id: PlayerId, sport_filter: Sport | Literal['all'],
                now: Instant) -> NowScreen
```
`now`: ms epoch, UTC. Output:
```ts
type NowScreen = {
  header:   { greeting: string; city: string; dayName: string; hhmm: string };
  strip:    EnrolledCard[];          // sorted by start ascending; may be empty
  stripEmpty: EmptyState | null;     // present iff strip is empty
  cardBanner: { plan: string; used: int; allowed: int };
  lanes:    [ { id:'best-fit-open';   title:'Even matches for you'; cards: FeedCard[];   empty: EmptyState|null },
              { id:'full-worth-waiting'; title:'Full, but worth waiting for'; cards: FeedCard[]; empty: null } ];
}
```
**Side effects: none in production.** In the prototype `matchState` calls `syncMatch`, which
**mutates the match** during rendering. That must not survive — see §K.1.

**D2 · Purpose.** Answer *"is my match still on?"* before the player taps anything, then offer
what to do next.

**D3 · Algorithm**
```
 1  strip    ← selectMyMatches(player, now)          [D.2]
 2  if gallery mode: strip ← forced matches           (demo only, drop in production)
 3  else:     strip ← strip filtered by sport_filter
 4  feed     ← selectFeed(player, sport_filter, now)  [D.3]
 5  full     ← selectFullLane(player, sport_filter, now)  [D.4]
 6  render header, strip (or its empty state), card banner, lane 1, lane 2
```
Literal, from `V.home`:
```js
const ms = Object.values(S.matches)
  .filter(m => mySeat(m) && !m.left && matchEnd(m) + KEEP_H*HOUR > S.now)
  .sort((a,b) => a.start - b.start);
const shown = ms.filter(m => S.sport==='all' || m.sport===S.sport);
```

**D4 · Branches, in evaluation order**
1. `S.gallery` truthy → strip is every `m.forced` match, header becomes a tag/context count.
2. `shown.length` truthy → strip renders; else the *"No matches booked"* empty card.
3. `shown.length > 1` → dot indicators render.
4. `feed.length` falsy → *"Nothing open in {sport} right now"*; else top 3.
5. `full.length` truthy → the second lane header and one card; else **nothing at all** — no
   header, no empty state.

**D5 · Rounding/precision.** None here. Money formatting is `zl()` [D.13]; ratings `lvl()`.

**D6 · Boundaries.** `matchEnd + KEEP_H·HOUR > now` is **strict** — at exactly
`matchEnd + 24h` the card **leaves** Now. `m.start > now` in the feed is **strict** — a match
starting at exactly `now` is not offered.

**D7 · Degenerate inputs**
| Input | Behaviour |
|---|---|
| no enrolled matches | empty card, both lanes still render |
| no open matches | lane 1 empty state; **no relaxation, no padding** |
| no full matches | lane 2 renders nothing |
| `lv('me', sport)` is null (unrated sport) | every candidate in that sport scores `null` and is **filtered out of the feed** — the lane silently empties. **[GAP-D1]** the player is told *"nothing open"* when the truth is *"we cannot rank your sports yet"*. Proposal: a distinct empty state keyed on `rating_missing`. |
| a match with 0 seats | `isFull` = `[].every(...)` = **true** → lands in the full lane. Structurally impossible but reachable from a bad create; reject `n ∉ {2,4}` at write time |
| stale client sends a `sport` that no longer exists | filter matches nothing → both lanes empty. Validate against the enum |

**D8 · Determinism.** Pure given `(player, matches, now, ratings, policies)` **except**: the feed
sort is `b.f.score - a.f.score` only — **not total**. Two candidates with equal fit resolve by
`Object.values` insertion order, which in production is the query plan. **This violates doc 4
invariant 9.** Fix: adopt `FEED_ORDER` [D.3 · D8].

**D9 · Complexity.** `O(M)` over the player's matches plus `O(K·G)` where `K` is candidates and
`G` is the `seatTarget` grid (401 evaluations × 3 pairings). Called on every open and pull.
Budget: cold `GET /now` < 100 ms [doc 3 §8.3]; warm feed < 12 ms [doc 4 §6.2] — but see §K.4,
the budget is inherited from a computation that is not the real cost.

**D10 · Worked example** — seeded world, `now = Wed 5 Aug 2026 21:00` (`T.created + 2h`),
`sport = 'all'`, player `me` (Tomek K., Padel 2,71 σ0,16 conf 74 n14):

```
strip (3 cards, start ascending)
  m7  Thu 6 Aug 19:00  Tennis Singles k33   → confirmedOnFill   [see K.2 — this is a seeding artefact]
  m1  Sat 8 Aug 18:30  Padel  Doubles ps    → heldSoft · "one player short"
  m8  Sun 9 Aug 11:00  Padel  Doubles pc    → full

lane 1 · best fit (27 candidates scored, top 3 shown)
  e6  97   Tennis Singles k33  Sun 9 Aug 19:30
  c3  95   Padel  Doubles ps   Sun 9 Aug 10:00
  m5  94   Badminton Doubles mos  Tue 11 Aug 18:30

lane 2 · full, worth waiting for (1 candidate)
  m2  94   Padel Doubles pc  Fri 7 Aug 19:00
```

---

## D.2 `selectMyMatches`

**D1** `def select_my_matches(player_id, now) -> list[Match]` · no side effects.
**D2** The enrolled strip: every match this player holds a seat in that has not yet aged out.
**D3**
```
keep(m) ⟺ mySeat(m) is not None  AND  not m.left  AND  matchEnd(m) + 24h > now
sort by m.start ascending
```
**D4** Three conjuncts, evaluated left to right; `mySeat` is `seats.find(s => s.p === 'me')`.
**D6** `matchEnd + 24h > now` **strict**: the card is present at `+23:59:59.999`, gone at `+24:00:00.000`.
**D7** A cancelled match **stays in the strip** — `clubCancelled` does not remove it, because
*"neither removes the card immediately, because the explanation is the point"* [SRC: 3.1 §0.2].
**D8** Pure. One clock read.

> **[GAP-D2 · doc 5 B3] The leaver has no card.** `!m.left` removes the card at exactly the
> moment the player has an open question about money — and their outcome is not yet known
> (100 % / 50 % / 0 % / 0 %). Doc 3 §3.2 assumes the card exists (*"Ola's card → the leaver's
> view"*). **Proposal: predicate becomes `I hold a seat, OR I held one and the outcome is not
> yet settled`, keeping the card for the same 24 hours, with five new states
> `leftReversed`, `leftSearching`, `leftRefunded100`, `leftRefunded50`, `leftForfeited`.**
> This is the money-bearing gap in the model.

---

## D.3 `selectFeed` — lane 1

**D1** `def select_feed(player_id, sport_filter, now) -> list[Scored]` · no side effects.
**D2** The best open matches this player could join.
**D3**
```js
Object.values(S.matches)
  .filter(m => !mySeat(m) && !m.forced && m.start > S.now && filled(m) < m.n
               && (S.sport==='all' || m.sport===S.sport))
  .map(m => ({m, f: matchFit(m)}))
  .filter(x => x.f.score != null)
  .sort((a,b) => b.f.score - a.f.score)
  .slice(0, 3)
```
**D4** Five filter conjuncts, then a null-score filter, then a sort, then a cap.
**D6** `m.start > now` strict; `filled(m) < m.n` strict (a full match is excluded here and
picked up by lane 2).
**D7** Empty → the *"We do not invent players"* card. **No widening, ever.**
**D8** **Not deterministic under ties.** Replace with the total chain [SRC: doc 4 §3.3]:
```python
FEED_ORDER = [desc(lambda x: x.fit.score),      # 1. fit
              asc (lambda x: x.match.start),    # 2. sooner is better
              asc (lambda x: x.club.dist),      # 3. nearer is better
              asc (lambda x: x.match.id)]       # 4. TOTAL — never returns 0
```
*"Without a guaranteed-total final key, the order depends on retrieval order, which depends on
the query plan."*

**Eligibility rules the prototype does not have** [SRC: doc 4 §3.2] — ten rules, **evaluated
exhaustively, never short-circuited**, so the exclusion histogram is complete:
`NotAlreadyMine`, `NotOnWaitlist`, `StartsInFuture`, `BeforeJoinCutoff`, `HasFreeSeat`,
`NotCancelled`, `SportMatchesFilter`, `NoScheduleConflict`, `NotSuppressed`.
**`WithinTravelCeiling` must NOT be included** — doc 5 A3: *"Distance, price and level are
never exclusions"*; the travel term at weight 15 exists to grade exactly this, and a match
removed before scoring cannot be graded. Bound retrieval by city and a generous geographic
ceiling instead, at the same standing as `LIMIT 300`.

**D9** `O(K)` scoring calls, `K ≈ 100` after eligibility. **D10** see D.1 D10.

---

## D.4 `selectFullLane` — lane 2

**D1** `def select_full_lane(player_id, sport_filter, now) -> list[Match]` · no side effects.
**D3** literal: `filter(m => !mySeat(m) && !m.forced && m.start > now && isFull(m) && sportOk)`
then `.slice(0,1)`. **No fit filter, no sort** — see **[GAP-C2]**.
**D6** `isFull` requires **every** seat `p AND paid`; an invited-but-unpaid seat makes the match
not-full and it falls to lane 1 instead.
**D7** Empty → **render nothing**: no header, no empty card. *"A section that appears every
time saying 'no full matches worth waiting for' is a section players learn to scroll past."*
**D10** `m2` — Padel at Bonarka, Fri 7 Aug 19:00, 4/4 paid (kuba, zofia, ania, ola), fit **94**.

---

## D.5 `deadlines` — FINAL (base replaced wholesale)

**D1**
```python
def deadlines(m: Match) -> Deadlines   # Deadlines = {commit, rescue, check, joinCut, play, solo}
```
All fields ms epoch; `solo: bool`. No side effects. **No clock read** — every field is relative
to `m.start`.
**D2** The five instants every downstream rule compares `now` against.
**D3**
```js
const P      = pol(m.club);                                   // ← the override: policy, not CLUBS
const commit = Math.min(m.start - P.window*HOUR, m.start - 12*HOUR);
const solo   = SPORTS[m.sport].players === 2;
return { commit,
         rescue : m.start - (solo ? 6 : 4)*HOUR,
         check  : m.start - 2*HOUR,
         joinCut: m.start - P.joinCut*60e3,
         play   : m.start, solo };
```
**D4** One branch: `solo` (`players === 2`) selects 6 h over 4 h. `min` selects whichever of the
two commitment candidates is **earlier**.
**D5** Exact integer arithmetic on ms. No rounding.
**D6** All five are **instants**, and every consumer tests `now >= X` — **inclusive at the
boundary**, i.e. *at* `commit` the deadline has passed. The one exception is the hold ladder,
which tests remaining **hours** with `>` — **exclusive** [D.6 D6].
**D7** `window` missing → `pol` defaults to 24. `joinCut` missing → 30. `start` in the past →
every deadline is in the past; the ladder and the state machine handle it.
**D8** Pure. **D9** `O(1)`, called several times per card — memoise per `(match, policy)`.

**D10** m1 · Padel · Zabłocie (`window` 24, `joinCut` 30) · start Sat 8 Aug 18:30
```
clubDl  = 18:30 Sat − 24h = Fri 7 Aug 18:30
12h     = 18:30 Sat − 12h = Sat 8 Aug 06:30
commit  = min(Fri 18:30, Sat 06:30) = Fri 7 Aug 18:30      ← the club's window is earlier
rescue  = 18:30 − 4h  = Sat 14:30      (doubles)
check   = 18:30 − 2h  = Sat 16:30
joinCut = 18:30 − 30m = Sat 18:00
play    = Sat 18:30
```
**Contrast — Atlantic Sports (`window` 12):** `commit = min(start − 12h, start − 12h)` = both,
so `commit` and the 2-seat hold lapse fire **at the same instant**. Any test exercising only a
24 h club misses it [SRC: 3.1 §2.4].

---

## D.6 `courtHold` — FINAL COMPOSED (base + wrapper)

**D1**
```python
def court_hold(m: Match, now: Instant, policy: ClubPolicy) -> Hold
# Hold = {kind: 'hard'|'soft'|'none', why: str, need?: int, until?: int,
#         releaseAt?: Instant, label: str, note?: str, age?: int, p?: int}
```
No side effects. **Reads the clock** (via `S.now` in the prototype; must become a parameter).

**D2** *Right now, is a physical court being kept aside for this match?*

**D3 · The composed algorithm, in exact evaluation order**

*Layer 1 — the base ladder (`_courtHold`)*
```js
const n = m.n, f = filled(m), left = (m.start - now) / HOUR;   // left is FRACTIONAL HOURS
 1  if (m.kind === 'private')      → {hard, 'private'}
 2  if (m.courtLocked)             → {hard, 'club'}
 3  if (m.committedAt != null)     → {hard, 'committed'}
 4  if (f >= n)                    → {hard, 'full'}
 5  if (n > 2) {
 5a   if (f >= n-1) return left > HOLD_NEAR ? {soft,'near', releaseAt: start-4h}
                                            : {none,'nearLapsed'}
 5b   if (f >= 2)   return left > HOLD_FAR  ? {soft,'far',  releaseAt: start-12h}
                                            : {none,'farLapsed'}
    }
 6  → {none, 'thin', need: n>2 ? 2 : n}
```
*Layer 2 — the wrapper*
```js
const h = _courtHold(m), P = pol(m.club);
W0  if (m.kind==='private' || m.courtLocked || m.committedAt != null) return h;   // SHORT-CIRCUIT
W1  if (h.kind === 'soft' && P.maxHoldAge
        && (now - m.created)/HOUR > P.maxHoldAge
        && filled(m) < m.n - 1)
      return {kind:'none', why:'stale', need:n-1, age:P.maxHoldAge};
W2  if (h.kind === 'none' && (h.why==='nearLapsed' || h.why==='farLapsed')
        && clubExtended(m))                       // = m.clubExtended && pol.probHold
      return {kind:'soft', why:'extended', need:n, until:0, p:clubFill(m)};
W3  return h;
```

**D4 · Every branch and its exact condition** — rungs 1→4 are unconditional early returns in
order. Rung 5 applies **only when `n > 2`**: two-player sports skip the soft tiers entirely
(Rule 10), which is why singles goes `thin → full` with nothing between. W0 is the wrapper's
short-circuit: a private, hand-locked or committed match is **never** stale and **never**
extended. W1 requires **three** conditions — soft, older than the cap, **and strictly fewer
than `n−1` paid seats**, so a three-of-four hold is never staled. W2 fires only on a hold the
ladder has just lapsed, and only from published club facts.

**D5 · Precision.** `left` is a **fractional hour float**: `(start − now) / 3_600_000`. The
comparison `left > 4` at `now = start − 4h` evaluates `4.0 > 4` = **false**. Do not round
`left`; do not compare integers. In Python use integer milliseconds:
`(m.start_ms - now_ms) > HOLD_NEAR_MS` — same semantics, no float.

**D6 · Boundary behaviour — this is the oscillation guard**

| Threshold | Test | At exactly the boundary |
|---|---|---|
| `start − 4h`, `f = n−1` | `left > 4` | **hold LAPSES** — `nearLapsed`. Strictly one-directional. |
| `start − 12h`, `f = 2` | `left > 12` | **hold LAPSES** — `farLapsed` |
| `maxHoldAge` | `(now − created)/h > maxHoldAge` | at exactly 48 h the hold **survives**; it goes stale one ms later |
| `f >= n` | inclusive | 4 of 4 → hard |
| `f >= n-1` | inclusive | 3 of 4 → soft/near |
| `f >= 2` | inclusive | 2 of 4 → soft/far |

> *"A match sitting exactly on T−12h with two paid seats will flap between `heldSoft` and
> `heldReleased` on every recomputation if the comparison is not strictly one-directional. Use
> `>` on the remaining time, never `>=`, and never re-notify on the same transition twice."*
> [SRC: 3.1 §5 `heldReleased`]

**D7 · Degenerate inputs**
| Input | Result |
|---|---|
| `filled = 0` | `{none, 'thin'}` |
| `filled = 1`, n=4 | `{none, 'thin', need: 2}` |
| `filled = 1`, n=2 | `{none, 'thin', need: 2}` — singles holds nothing at half |
| `now > start` (match in the past) | `left` negative → both `>` tests false → lapsed. Correct: the ladder has nothing to say after play |
| `n = 2` and `f = 2` | rung 4 → `{hard, 'full'}`; rung 5 never reached |
| `created > now` (clock scrubbed back) | `(now − created)` negative → W1 false → no stale. Safe |
| `committedAt` set **and** `filled < n` | rung 3 → **hard, forever**. This is Rule 3 and it is what stops a committed match losing its court at T−4h |

**D8 · Determinism.** Pure given `(record, now, policy)`. Reads the clock once per call in the
prototype; must take `now` as a parameter so a scrub is reproducible.

**D9** `O(n)` for `filled`. Called ~4× per card render — memoise per `(match, now-minute)`.
Budget < 10 µs.

**D10 · Worked example — the override chain changing the answer**

m1, 2 paid seats (me + kuba), `created` Wed 5 Aug 19:00, club `ps` (`maxHoldAge` 48).
Evaluate at `now = Sat 8 Aug 06:29` (T−12h minus one minute):

```
Layer 1:  f = 2, n = 4, left = (Sat 18:30 − Sat 06:29)/3600000 = 12.0167 h
          rung 5a: f >= 3?  no
          rung 5b: f >= 2?  yes → left > 12 → TRUE → {soft, 'far', releaseAt Sat 06:30}
Layer 2:  W0: not private/locked/committed → continue
          W1: kind==='soft' ✓ · maxHoldAge = 48 ✓
              (now − created)/h = (Sat 06:29 − Wed 19:00)/h = 59.4833 > 48  ✓
              filled(2) < n−1 (3)  ✓
              → {kind:'none', why:'stale', need:3, age:48}
FINAL:    none / stale      →  state = heldStale     (NOT heldSoft)
```
The base ladder says the court is held. The composed function says it went back two days ago
because Zabłocie caps a speculative hold at 48 hours. **A specification written from the base
declaration alone is silently and confidently wrong here.**

Same match, same seats, at `now = Sat 08:30` (T−10h): layer 1 gives
`left = 10 > 12` false → `{none, 'farLapsed'}`; W1 does not apply (`kind` is not soft); W2
applies only if `m.clubExtended && pol('ps').probHold` — `probHold` is `true` for `ps`, so a
club that published an extension turns this back into `{soft, 'extended'}` and the card reads
`heldExtended` with *"Their model puts this match at {clubFill}% to fill."*

---

## D.7 `syncMatch` — the writer (and the thing that must not run on a read)

**D1**
```python
def evaluate(m: Match, now: Instant, policy: ClubPolicy) -> Evaluation
# Evaluation = {facts: FactDelta, events: list[DomainEvent], next_wake_at: Instant | None}
```
In the prototype this is `syncMatch(m)`, which **mutates `m` in place and emits notifications**
as a side effect of rendering. In production it must be split: `evaluate` is pure and returns
what a writer *would* write; `apply` writes it, inside one transaction with the outbox
[SRC: doc 3 §2.1–2.2].

**D2** Bring the record's stored facts into agreement with the ladder, the commitment rule and
the checkpoint.

**D3 · Algorithm, in exact order** (`d = deadlines(m)`; `wasCourt = m.courtId`)
```
 0  if (m.forced) return m                                  ← demo escape hatch
 1  if (m.kind === 'private') { assign first club court if none; return }
 2  hold = courtHold(m)                                     ← the COMPOSED one
 3  if hold.kind !== 'none':
 3a     if no courtId:  cid = pickCourt(m)
                        if cid:   courtId = cid; protectedAt = now; holdKind = hold.kind
                        elif hold.kind === 'hard' and not inventoryLost:
                                  inventoryLost = true; clubCancelled = true    ← TERMINAL
 3b     else: holdKind = hold.kind
 4  elif committedAt == null:
        courtId = null; protectedAt = null; holdKind = null
        if wasCourt: releasedAt = now
 5  if (!courtId && committedAt==null && !inventoryLost && !clubCancelled
        && now >= start − 12h && now < d.check && openCourtsFor(m).length === 0):
        inventoryLost = true; clubCancelled = true          ← TERMINAL
 6  if (committedAt == null && now >= d.commit && isFull(m)):
        committedAt = (now > d.commit + 60_000) ? now : d.commit
 7  if (now >= d.check):
 7a     if (committedAt == null && !isFull(m))          formCancelled = true
 7b     elif (committedAt != null && filled < n
              && !sponsoredGuest && CLUBS[club].rebooking) checkpointCancelled = true
 8  emit notifications for each newly-true flag (rescueOpen, formCancelled, checkpointCancelled,
    soft hold assigned, court released, inventoryLost, clubCancelled)
```

**D4 · The branches that matter**
- **3a vs 5** are two different inventory-loss paths. 3a fires when a **hard** hold (a full or
  committed match) can find no court — *"a complete match with nowhere to go."* 5 fires for an
  **unsecured, uncommitted** match inside the last twelve hours whose category has sold out.
  The 12-hour guard on 5 is deliberate: *"declaring it dead on a Wednesday for a Sunday morning
  would kill every ordinary forming match on the board."*
- **4** carries the guard `committedAt == null`. *"A committed match never releases. The
  `else if (committedAt == null)` on the release branch is Rule 3 in code."*
- **6** is the commitment rule: **both** conditions, and the value written is `d.commit`
  itself unless the fill is more than 60 s late, in which case it is `now`.
- **7** is the checkpoint, and it has **three** outcomes, the third being *the absence of an
  event*: a committed, short match at a standard club is **not cancelled** — it stays alive to
  `joinCut`.

**D5 · Precision.** `committedAt` is written to **ms precision**, either exactly `d.commit` or
exactly `now`. Never rounded.

**D6 · Boundaries**
| Test | Inclusive? | At the boundary |
|---|---|---|
| `now >= d.commit` | **inclusive** | at exactly `commit`, a full match **commits** |
| `now > d.commit + 60_000` | **exclusive** | at exactly `commit + 60 s`, `committedAt = d.commit` and the state is `confirmed`, **not** `confirmedOnFill`. One ms later it flips |
| `now >= d.check` | **inclusive** | at exactly `check`, the checkpoint fires |
| `now >= start − 12h` (rung 5) | **inclusive** | inventory loss becomes possible at exactly T−12h |
| `now < d.check` (rung 5) | **exclusive** | inventory loss stops being possible at exactly `check` — the checkpoint owns the outcome from there |

**D7 · Degenerate and structurally-impossible inputs**
| Input | Behaviour | Verdict |
|---|---|---|
| `pickCourt` returns null with a **soft** hold | nothing written, no court, no cancellation | correct — a speculative hold that cannot be placed is simply not placed |
| clock scrubbed **backwards** across `check` | `formCancelled` **stays true** → the card still reads `cancelledIncomplete` | **BUG — violates invariant 14.** Verified: scrubbing back from 16:31 to 14:30 leaves `cancelledIncomplete`. See [GAP-D3] |
| clock scrubbed backwards across T−4h | court is **re-assigned**, hold returns, state returns to `heldSoft`; `releasedAt` keeps its value | correct for the state, sticky for the receipt |
| `committedAt` set, `courtId` null | rung 3 gives a hard hold, rung 3a tries to assign, may set `inventoryLost` | this is invariant 3's unreachable cell; assert it |
| two players leave in the same second | second `vacated` **overwrites** the first | **unhandled** [SRC: 3.1 §9.3] — see §K |

> **[GAP-D3 · doc 5 C2] The four terminal flags are stored, so a downed writer makes a read
> *wrong*, not *late*.** With the timekeeper down through T−2h, a read of an incomplete
> uncommitted match derives `protectedLate` (*"past the deadline, still free to leave"*) when
> the truth is `cancelledIncomplete`. **Proposal: derive the state from the condition and keep
> the flag only as a receipt that the side effects ran.**
> `cancelledIncomplete ⟺ now >= check ∧ committedAt is None ∧ not isFull` is fully derivable;
> so is the checkpoint branch. Then a downed timekeeper delays the **money** and never the
> **truth**.

**D8 · Determinism.** Not pure — it writes. In the prototype it is called from `matchState`,
i.e. **from a read**, which is the single most important thing to fix (§K.1). It also captures
`S.now` several times; the command handler must read the clock **once** and pass it down.

**D9** `O(n + C)` where `C` = courts in the category. Called once per command and once per
scheduled wake, ~10 times per match lifetime.

**D10 · Worked example — the commitment write.** m1 with all four seats paid,
`d.commit = Fri 7 Aug 18:30`.
```
now = Fri 18:29:00 → rung 6: now >= commit? no  → committedAt stays null → state `full`
now = Fri 18:30:00 → rung 6: now >= commit ✓, isFull ✓
                     now > commit+60s? 18:30:00 > 18:31:00 → false
                     committedAt = d.commit = Fri 18:30:00.000
                     committedOnFill = 18:30:00 > 18:31:00 → false → state `confirmed`
now = Fri 18:31:00 → (fresh match) committedAt = commit → still `confirmed`
now = Fri 18:31:00.001 → committedAt = now → committedOnFill true → state `confirmedOnFill`
scrub back to Fri 13:30 → committedAt still set → state `confirmed`  ✓ invariant 1 holds
```

---

## D.8 `matchState` — FINAL COMPOSED (base ladder + wrapper)

**D1**
```python
def match_state(m: Match, viewer: PlayerId, now: Instant, policy: ClubPolicy) -> StateKey
```
Pure in production. In the prototype it **calls `syncMatch` first**, so it writes — see §K.1.

**D2** Resolve the match, from this viewer's position, to exactly one of 35 contexts.

**D3 · The composed ladder.** *The order is the specification.* First match wins.
Full rung table, guards and orderings: **§E.1**. The wrapper runs **after** the base returns:
```js
const st = _matchState(m);
if (m.forced || m.kind === 'private') return st;            // SHORT-CIRCUIT
const h = courtHold(m);
if (h.why === 'stale'    && st.key ∈ {heldReleased, forming, formingLate})            → heldStale
if (h.why === 'extended' && st.key ∈ {heldReleased, forming, formingLate, heldSoft})  → heldExtended
return st;
```
Note the asymmetry: `heldSoft` is in the **extended** set but not the **stale** set — because a
stale hold has already been turned into `kind: 'none'` by the wrapper on `courtHold`, so the
base ladder can never have produced `heldSoft` in that case. The two sets are exactly the keys
reachable given what the wrapper did upstream. [DERIVED: cross-checking W1/W2 against rungs 11–15]

**D4** See §E.1 — 15 base rungs with sub-branches, then the two wrapper rewrites.
**D5** No numeric rounding. **D6** Every threshold is stated inclusive/exclusive in §E.1.
**D7** See §E.4. **D8** Pure once `syncMatch` is removed; otherwise it mutates on read.
**D9** *"A handful of integer comparisons per match"* — cheaper than the lookup it replaces.
Budget: `evaluate` one match < 50 µs [doc 3 §8.3].

**D10 · Worked example — the viewer rewrite.** The last step of the base function:
```js
if (!mySeat(m) && k !== 'waitlisted')
  lines = lines.map(l => /^You paid/.test(l[1])
    ? [0, 'Your share would be ' + zl(payable(m)) + ' · booking fee 0,00 zł']
    : l);
```
So the **same match at the same instant** produces different card text for an enrolled player
and a browsing one — the state is a property of the match, the wording is a property of your
relationship to it. This is a **string rewrite driven by a regular expression on generated
copy**, which cannot survive the move to client-side copy. **Proposal: the server emits
`{key, tone, facts, viewer_role: 'seated' | 'browsing' | 'waitlisted' | 'left'}` and the client
picks the sentence.** [SRC: doc 5 A5]

---

## D.9 `matchFit` — the seven-term score  `[SUPERSEDED-A1 — see A.0]`

**D1**
```python
def match_fit(m: Match, viewer: Player, now: Instant) -> FitScore
# FitScore = {score: int | None, terms: list[Term], mods: list[Mod],
#             reasons: tuple[str,str,str], warn: str | None, target: float}
# Term = (label: str, weight: int, value: float, sentence: str)
```
No side effects. Reads `now` transitively through `payable → slotDisc` and through
`forecast → rosterFor` (not time-dependent) — **the score itself is time-independent except
through `payable`**. [DERIVED: no deadline or clock comparison appears in any term]

**D2** How well this match suits this player, as one number with three reasons.

**D3 · Algorithm with the literal expression for every term**
```js
 0  myL = lv('me', m.sport);  if (!myL) return {score: null, terms: [], reasons: []};
 1  tgt = seatTarget(m) || (targetBand(m) ? (targetBand(m)[0] + targetBand(m)[1]) / 2 : myL[0]);
 2  others = m.seats.filter(s => s.p && s.p !== 'me').map(s => PLAYERS[s.p]).filter(Boolean);
    scores = others.map(p => p.score);
 3  overlap = Math.max(0, 1 - Math.abs(myL[0] - tgt) / 0.55);
 4  proj    = forecast(m);      bal = proj ? proj.pct / 100 : 0.7;
 5  rel     = scores.length ? (0.5*Math.min(...scores) + 0.5*(sum(scores)/scores.length)) / 100 : 0.8;
 6  travel  = Math.max(0, 1 - Math.max(0, club.dist - 20) / 18);
 7  inten   = m.counts ? 1 : 0.72;
 8  price   = Math.max(0, Math.min(1, 1 - (payable(m) - 30) / 30));
 9  pref    = 0.9;
10  sc = Σ (weight_i × value_i)                       // 30,20,15,15,8,7,5
11  if (m.badge === 'Promotion')                              sc += 8
12  known = others.filter(p => REGULARS.includes(p.id)).length
    if (known === 0 && others.length)                         sc += 5
    else if (others.length >= 3 && known === others.length)   sc -= 8
13  sc = Math.max(20, Math.min(99, Math.round(sc)))            // ROUND, THEN CLAMP
14  rank    = terms sorted by (weight × value) DESCENDING
15  reasons = rank.slice(0,3).map(t => t.sentence)
16  warn    = rank[rank.length-1].value < 0.55 ? rank[last].sentence : null
```

**D4 · Branch conditions, in evaluation order**
1. `!myL` → the whole score is `null` and **the card is dropped from the feed**.
2. `seatTarget(m)` non-null (exactly one seat open, doubles) → use it; else the **midpoint of
   the target band**; else my own level (which makes overlap = 1.0 and is the optimistic
   default doc 5 A1 objects to).
3. `proj` null (fewer than `n` in the roster) → `bal = 0.70`.
4. `scores.length` zero (nobody else seated) → `rel = 0.80`.
5. Modifier chain: `+8` is **independent**; `+5` and `−8` are **mutually exclusive** (`else if`).
6. `warn` fires on the **raw value** of the term that is **last by contribution** — two
   different quantities, deliberately.

**D5 · Rounding, clamping, precision, in order**
```
value_i         : float64, unclamped except where the formula clamps (terms 0,3,5)
contribution    : weight × value, float64, NOT rounded
sum             : float64
modifiers       : integer additions to the float sum
Math.round      : half-up on .5 (JS: Math.round(-0.5) = -0; irrelevant here, sum ≥ 0)
clamp           : max(20, min(99, rounded))       ← ROUND FIRST, THEN CLAMP
```
**Currency precision is a separate rule** [D.12]: money is `round(x*100)/100` — two decimals,
half-up — and rendered `zl()` with a comma. **Rating precision is a third rule**: levels are
carried at full float and rendered `toFixed(2)` with a comma and a Unicode minus (U+2212).
Never conflate the three.

**D6 · Boundary behaviour**
| Threshold | Test | At the boundary |
|---|---|---|
| overlap | `1 − |Δ|/0.55` | `|Δ| = 0.55` → **exactly 0**; beyond, clamped to 0 |
| travel | `dist − 20` | `dist = 20` → **1.0**; `dist = 38` → **0.0**; beyond → 0 |
| price | `(payable − 30)/30` | `payable = 30` → **1.0**; `payable = 60` → **0.0** |
| warn | `raw < 0.55` | at exactly 0.55 → **no warning** |
| clamp | `[20, 99]` | 99 is attainable; **100 is not** |
| `.fit.hi` | `score >= 90` | at exactly 90 the badge turns **coral** |

**D7 · Degenerate inputs**
| Input | Result |
|---|---|
| viewer unrated in this sport | `{score: null}` → dropped from the feed |
| no seated players at all | `tgt = myL[0]` ⇒ overlap **1.0**; `bal` 0.70; `rel` 0.80 ⇒ a near-empty match scores **90.5** before modifiers. This is exactly ADR-0027's finding: *"the score is monotonically decreasing in information"* |
| a seated player id not in `PLAYERS` | silently dropped by `.filter(Boolean)` — `rel` computed over the rest, or defaulted |
| `payable = 0` (full card cover) | price term = 1.0 (clamped) |
| `dist` missing | `NaN` propagates through the whole score. **Validate `dist` is present** |
| `others.length === 0` | `+5` cannot fire (`&& others.length`), `−8` cannot fire |
| exactly 3 others, all regulars | `−8` |

**D8 · Determinism.** Pure given `(match, viewer, ratings, policy, payable)`. `payable` reads
`S.slotDisc`, so a slot discount changes the score — version the score with the match's
`recordVersion` and the `EngineVersion`.

**D9** `O(n + G)`, dominated by `seatTarget`'s 401-point grid × 3 pairings. Doc 4 claims
500 µs cold / 20 µs warm; doc 5 D1 shows the premise is wrong — `_seat_target` in the shipped
engine is closed-form, and `PairingAnalysis` is **player-relative** (it seats the asker), so a
per-match cache of the analysis would be **silently wrong**. What *is* shareable is
`seatTarget(seated)` and `targetBand(seated)` only.

**D10 · Two worked examples, every intermediate value**

**(a) m1 — the canonical enrolled match.** me 2,71 · kuba 2,80 · ola 2,64 · one seat open.
Zabłocie `dist` 14. `payable` 38,00. `counts` true. `badge` `'Promotion'`.
```
seatTarget(m1) = 2.57                (grid search, D.11)
overlap = max(0, 1 − |2.71 − 2.57| / 0.55) = 1 − 0.14/0.55 = 1 − 0.2545454… = 0.745454…
forecast(m1) = null                  (3 seated, I am one of them, roster 3 < n 4)
bal     = 0.70                       (default)
scores  = [96 (kuba), 89 (ola)];  min 89, mean 92.5
rel     = (0.5×89 + 0.5×92.5)/100 = (44.5 + 46.25)/100 = 90.75/100 = 0.9075
travel  = max(0, 1 − max(0, 14 − 20)/18) = 1 − 0 = 1.0
inten   = 1.0
price   = clamp(0,1, 1 − (38 − 30)/30) = 1 − 0.2666… = 0.733333…
pref    = 0.9

contributions
  skill overlap      30 × 0.745455 = 22.3636
  predicted balance  20 × 0.700000 = 14.0000
  group reliability  15 × 0.907500 = 13.6125
  time and travel    15 × 1.000000 = 15.0000
  match type          8 × 1.000000 =  8.0000
  price vs ceiling    7 × 0.733333 =  5.1333
  preferences         5 × 0.900000 =  4.5000
                       sum         = 82.6094
modifiers   +8 (Promotion badge).  known = 2 (kuba, ola ∈ REGULARS) → no +5;
            others.length = 2 < 3 → no −8
            → 90.6094
round → 91 ;  clamp [20,99] → 91                            FIT = 91
reasons (top 3 by contribution): travel 15.00, "14 minutes away"
                                 predicted balance 14.00, "Not enough players in yet to forecast"
                                 group reliability 13.61, "Lowest Player Score here is 89"
   — note skill overlap at 22.36 IS the top contribution; the printed order is
     [22.36 skill, 15.00 travel, 14.00 balance]
warn: lowest contribution is preferences (4.50), raw 0.9 ≥ 0.55 → **null**
```

**(b) m2 — the full lane, and the contribution/raw asymmetry.** kuba 2,80 · zofia 2,69 ·
ania 2,68 · ola 2,64. Bonarka `dist` 11, `payable` 38,00, counts true, no badge.
```
seatTarget = null (no seat open) → targetBand = [2.50, 2.90] → tgt = 2.70
overlap = 1 − |2.71 − 2.70|/0.55 = 1 − 0.0181818… = 0.981818…
forecast: roster = 4 seated + me? NO — mySeat is null and ps.length(4) is NOT < n(4),
          so 'me' is NOT added; the forecast is over the four seated players
          bestPairing → A = 2.7120, B = 2.6845, gap = 0.0275
          spread = √(0.08² + 0.11² + 0.09² + 0.16²) = 0.2284731…
          pct = max(35, min(96, round(100 − 0.0275×145 − 0.2284731×32)))
              = round(100 − 3.9875 − 7.3111) = round(88.7014) = 89
bal   = 0.89
rel   = min 89 (ola), mean (96+95+99+89)/4 = 94.75 → (44.5 + 47.375)/100 = 0.91875
travel= 1 − max(0, 11−20)/18 = 1.0
inten = 1.0 ; price = 1 − 8/30 = 0.733333… ; pref = 0.9

  30 × 0.981818 = 29.4545
  20 × 0.890000 = 17.8000
  15 × 0.918750 = 13.7813
  15 × 1.000000 = 15.0000
   8 × 1.000000 =  8.0000
   7 × 0.733333 =  5.1333
   5 × 0.900000 =  4.5000
                  93.6691
no modifiers (known = 2 of 4 others → not 0, not all)
round → 94 ; clamp → 94                                     FIT = 94
lowest contribution: preferences 4.50, raw 0.9 → **no warning**   ← the asymmetry test
badge: 94 ≥ 90 → `.fit.hi` → CORAL
```
The coral badge here is exactly what doc 5 A2/E2 object to: nothing has been checked about
coverage, and *"a computed recommendation score is neither a thing the player owns nor an
action they can take."*

---

## D.10 `forecast`, `bestPairing`, `teamStrength`

**D1**
```python
def team_strength(a: float, b: float | None) -> float          # pure
def best_pairing(vals: list[float]) -> Pairing                  # pure
def forecast(m: Match, viewer: PlayerId) -> Forecast | None     # pure
```
`Forecast = {youShare:int, A:float, B:float, gap:float, pct:int, opts:list, unsure:bool,
n:int, sideA:list, sideB:list, spread:float, conf:str, minCounted:int}`

**D2** How even this match will be, and which side is ahead.

**D3**
```js
teamStrength(a,b) = b == null ? a : 0.45*Math.max(a,b) + 0.55*Math.min(a,b)

bestPairing(vals):                                   // vals.length must be 4
  idx = [[[0,1],[2,3]], [[0,2],[1,3]], [[0,3],[1,2]]]        // the only 3 splits of 4
  opts = idx.map(pr => ({pair:pr, A:teamStrength(v[pr0a],v[pr0b]),
                                  B:teamStrength(v[pr1a],v[pr1b]),
                                  gap:|A−B|}))
         .sort((x,y) => x.gap − y.gap)               // ← NOT a total order; ties by input order
  return {a:opts[0].A, b:opts[0].B, gap:opts[0].gap, opts}

rosterFor(m) = seats with p, PLUS 'me' if I hold no seat AND seated < n
canForecast(m) = rosterFor(m).length >= m.n

forecast(m):
  if !canForecast(m) return null
  vals = roster levels (nulls dropped);  sig = roster sigmas (default 0.25 if unrated)
  if vals.length < 2 return null
  bp  = bestPairing(vals)
  sp  = Math.sqrt(Σ σ_i²)                            // NOT a mean — a Euclidean norm, so it
                                                     // GROWS with the number of players
  pct = Math.max(35, Math.min(96, Math.round(100 − bp.gap*145 − sp*32)))
  fav = Math.min(86, 50 + bp.gap*72.5)
  youShare = Math.round(sB > sA ? 100 − fav : fav)
```
**Side selection:** with ≥4 rated players the best split's first pair is side A, **swapped if
`me` is on side B** so the viewer is always on side A. With 2, `sideA=[ids[0]]`, swapped if
`ids[1] === 'me'`.

**D4** `b == null` in `teamStrength` (singles). `vals.length < 4` in `bestPairing` returns a
degenerate `{a:vals[0], b:vals[1], gap:|v0−v1|, opts:[]}`. `vals.length < 2` → `null`.

**D5** `pct` is `round` **then** clamped to `[35, 96]`. `youShare` is `round` after
`min(86, …)`. `A` and `B` are unrounded floats. The identity
`pct = 100 − 2×(fav − 50) − spread×32` holds **by construction** because `72.5 = 145/2` — the
bar and the percentage beside it cannot contradict each other.

**D6** `pct` clamp: a perfectly even, perfectly certain match scores `100 − 0 − 0 = 100` →
clamped to **96**. A hopeless one clamps up to **35**. `fav` caps at **86**, reached when
`gap = 0.4966`. `conf`: `sp < 0.28` high (**exclusive**), `sp < 0.42` medium, else low.
`unsure` ⟺ `sp > 0.42` (**exclusive** — at exactly 0.42, `conf` is `low` but `unsure` is false;
an off-by-one seam worth a test).

**D7** Unrated player in the roster → their level is dropped from `vals` but their σ default
**0.25 is still counted** in `sig`, so a 4-seat match with one unrated player computes a pairing
over 3 levels (`bestPairing` returns the degenerate branch) while the spread reflects 4. This
is a real inconsistency. **[GAP-D4] Proposal: exclude unrated players from both, or treat them
as `(band midpoint, σ 0.30)` as `arrangedForecast` does for its link seat.**

**D8** Pure. **D9** `O(1)` — three pairings, constant work.

**D10** m2, four seated: kuba 2,80 (σ0,08) · zofia 2,69 (σ0,11) · ania 2,68 (σ0,09) · ola 2,64 (σ0,16)
```
splits:  (kuba,zofia) vs (ania,ola) → A = 0.45×2.80 + 0.55×2.69 = 1.2600 + 1.4795 = 2.7395
                                      B = 0.45×2.68 + 0.55×2.64 = 1.2060 + 1.4520 = 2.6580  gap 0.0815
         (kuba,ania)  vs (zofia,ola)→ A = 0.45×2.80 + 0.55×2.68 = 1.2600 + 1.4740 = 2.7340
                                      B = 0.45×2.69 + 0.55×2.64 = 1.2105 + 1.4520 = 2.6625  gap 0.0715
         (kuba,ola)   vs (zofia,ania)→A = 0.45×2.80 + 0.55×2.64 = 1.2600 + 1.4520 = 2.7120
                                      B = 0.45×2.69 + 0.55×2.68 = 1.2105 + 1.4740 = 2.6845  gap 0.0275  ← best
spread = √(0.0064 + 0.0121 + 0.0081 + 0.0256) = √0.0522 = 0.22847319…
pct    = round(100 − 0.0275×145 − 0.22847319×32)
       = round(100 − 3.98750 − 7.31114) = round(88.70136) = 89
fav    = min(86, 50 + 0.0275×72.5) = min(86, 51.99375) = 51.99375
sB(2.6845) > sA(2.7120)? no → youShare = round(51.99375) = 52
conf: 0.2285 < 0.28 → high;  unsure: 0.2285 > 0.42 → false
```

---

## D.11 `seatTarget` and `targetBand`

**D1** `def seat_target(m) -> float | None` · `def target_band(m) -> tuple[float,float] | None` · pure.
**D2** What level the open seat needs, and what band a still-forming match is aimed at.
**D3**
```js
seatTarget(m):
  seated = levels of seats with p (nulls dropped)
  if (seated.length !== m.n - 1) return null              // ONLY when exactly one seat is open
  if (SPORTS[m.sport].players === 2) return seated[0]     // singles: mirror the opponent
  best = null; bg = 99
  for (v = 1.0; v <= 5.0; v += 0.01)
    f = bestPairing(seated.concat([v]))
    if (f.gap < bg - 1e-9) { bg = f.gap; best = v }       // strict improvement, epsilon 1e-9
  return Math.round(best * 100) / 100

targetBand(m):
  seated = as above
  if (!seated.length) return null
  avg = mean(seated)
  return [round((avg − 0.2)*100)/100, round((avg + 0.2)*100)/100]
```
**D4** Three exits in `seatTarget`: wrong seat count → null; singles → the opponent's level;
doubles → grid search. `targetBand` returns null only for an empty match.
**D5** Both round to **2 dp, half-up**, at the very end. The grid accumulates float error
(`v += 0.01` 401 times) — in Python iterate integers: `for k in range(100, 501): v = k/100`.
**D6** The `< bg − 1e-9` test means the **first** value achieving the minimum wins, so the
result is the **lowest** balancing level when several tie. Grid endpoints are inclusive at 1.00
and, floating point permitting, 5.00 — pin them with the integer loop.
**D7** Two or more seats open → `null` (*"the problem is under-determined"*). Zero seats open →
`null` (`seated.length === n ≠ n−1`). All seated players unrated → `seated` is empty, length ≠
n−1 → null.
**D8** Pure and **player-independent** — this and `targetBand` are the *only* correct flyweight
[SRC: doc 5 D1]. **D9** 401 × 3 `teamStrength` calls ≈ 1200 float ops.
**D10** m1 seated = [2.71 (me), 2.80 (kuba), 2.64 (ola)]:
```
try v: the split minimising |A − B| over {me,kuba,ola,v}
best gap found at v = 2.57  → seatTarget = 2.57
targetBand: avg = (2.71 + 2.80 + 2.64)/3 = 2.716666… → [2.52, 2.92]
```
Rendered as *"The open seat needs about 2,57 · you are 2,71"* — the sentence doc 4 §8.4 says a
learned ranker could never produce, and the reason the badge is trusted.

---

## D.12 The money chain — `payable`, `shareAfterDisc`, `slotDisc`, `cardOff`, `shareOf`, `courtPriceOf`

**D1**
```python
def court_price_of(court, dur_min, start_min) -> int          # whole zł
def share_of(sport, price) -> Decimal                          # 2 dp
def slot_disc(m) -> int                                        # whole zł
def share_after_disc(m) -> Decimal                             # 2 dp
def card_off(club, sport, share) -> Decimal
def payable(m) -> Decimal                                      # FINAL, overridden
```
No side effects. `payable` reads `S.slotDisc` — process state that must become a policy read.

**D2** What a court costs, what a seat costs, and what this player actually pays.

**D3 · The composed chain (final `payable`, base is dead code)**
```js
courtPriceOf(court, dur, start) =
   Math.round( RATE[court.sport][start >= PEAK ? 'pk' : 'off'][dur]
               × (CLUBS[court.club].pm || 1)
               × (court.pm || 1) )                    // ROUNDED TO WHOLE ZŁOTY

shareOf(sport, price) = Math.round(price / SPORTS[sport].players * 100) / 100

slotDisc(m)        = Math.min( pol(m.club).slotDisc[club|dow|hh:mm] || S.slotDisc[m.id] || 0,
                               m.price )
shareAfterDisc(m)  = slotDisc(m) === 0 ? m.share
                                       : Math.round((m.price − slotDisc(m)) / m.n * 100) / 100
cardOff(club,sport,sh) = v = CLUBS[club].card[sport];
                         v == null ? 0 : v === 'full' ? sh : Math.min(sh, v)
payable(m)         = Math.max(0, shareAfterDisc(m) − cardOff(m.club, m.sport, shareAfterDisc(m)))
```
**The invariant this protects:** `share = court price ÷ players`, always. A club may discount
the **court**; it may never set a seat price, *"or four seats would eventually cost more than
the whole court"* [SRC: proto §5 comment, v37 §0.2 Invariant 1].

**D4** `start >= PEAK` (17:00) selects the peak table — **inclusive**, so a 17:00 start is
peak. `RATE[sport][tier][dur]` missing → falls back to the **first key** of the table, which is
a silent wrong price. **[GAP-D5] Proposal: reject an unsupported duration at creation; never
fall back.** `card[sport]`: `null`/absent → 0; `'full'` → the whole share; a number → capped at
the share.

**D5 · Currency precision — the separate rule**
```
court price : integer złoty (Math.round at the multiplier step)
share       : round(x × 100) / 100      — 2 dp, half-up
payable     : max(0, …) after the same 2 dp rounding
display     : toFixed(2), '.' → ',', suffix ' zł'      → "38,00 zł"
```
**In production, hold money as integer grosze** and divide with an explicit remainder policy.
`round(152/4 × 100)/100 = 38.00` is exact, but `round(112/3 …)` is not — and `n` is only ever
2 or 4, so no share is currently inexact. That is luck, not design. **[GAP-D6] Proposal:
`share_grosze = price_grosze // n`, with the remainder (0–3 grosze) absorbed by the platform,
asserted at creation as `n × share_grosze <= price_grosze`.**

**D6** `Math.min(sh, v)` caps a partial card at the share, so a 15 zł card on a 12 zł share
gives 12, not 15 — `payable` floors at 0 and never goes negative. `slotDisc` is capped at
`m.price`, so `shareAfterDisc` floors at 0.
**D7** `price = 0` → share 0 → payable 0 → price term = 1.0. A negative `slotDisc` from bad
config would **raise** the share; validate `0 <= slotDisc <= price`.
**D8** Pure given `(match, club policy, card)`. **D9** `O(1)`.
**D10** m1, Padel, Zabłocie, 90 min, 18:30 start, court `pm` 1.00, club `pm` absent (1.00):
```
18:30 = 1110 min ≥ PEAK 1020        → peak table
RATE.Padel.pk[90] = 152
courtPrice = round(152 × 1.00 × 1.00) = 152
share      = round(152 / 4 × 100)/100 = round(3800)/100 = 38.00
slotDisc   = 0 → shareAfterDisc = 38.00
CLUBS.ps.card.Padel = 0 → cardOff = 0
payable    = max(0, 38.00 − 0) = 38.00                      → "38,00 zł"
```
And the same match at Atlantic for squash (`card.Squash = 'full'`): `cardOff = share`,
`payable = 0,00 zł`, and the card renders a struck-through original with `card −all`.

---

## D.13 Formatting leaves — domain logic, because they change a displayed amount

| Function | Expression | Notes |
|---|---|---|
| `zl(v)` | `(v \|\| 0).toFixed(2).replace('.', ',') + ' zł'` | **`\|\|` means `zl(0)` and `zl(null)` both give `"0,00 zł"`** — a real zero and a missing value are indistinguishable. **[GAP-D7] use an explicit null check** |
| `lvl(v)` | `v == null ? '—' : v.toFixed(2).replace('.', ',').replace('-', '−')` | 2 dp, comma decimal, **U+2212 minus** |
| `hm(t)` | `HH:MM`, zero-padded, **device local time** | |
| `dow(t)` / `dowl(t)` | `['Sun'…]` indexed by `getDay()` | English only — **the product is Polish** [SRC: doc 5 A5] |
| `when(t, now)` | day difference on **calendar dates**, not elapsed hours → `Today · HH:MM`, `Tomorrow`, `Yesterday`, else `Dow · HH:MM` | 23:00 → 01:00 is *"Tomorrow"*, correctly |
| `dur(ms)` | `≥24h → "Nd Hh"` · `≥1h → "H h MM"` · else `"M min"` | `Math.round(ms/60e3)`, floored at 0 |
| `hhmm(min)` | minutes-of-day → `HH:MM` | |

`toFixed` uses **round-half-away-from-zero on the decimal string**, which is not IEEE
round-half-even. Python's `format(x, '.2f')` uses banker's rounding on ties and **will disagree
on values like 2.675**. Use `Decimal(str(v)).quantize(Decimal('0.01'), ROUND_HALF_UP)`.

---

## D.14 `stateCard` and `matchCard` — the two card contracts

**D1** `def build_enrolled_card(m, viewer, now) -> EnrolledCard` ·
`def build_feed_card(m, viewer, now) -> FeedCard` · no side effects.

**D3 · `stateCard` (the strip) reads, in order:** `matchState(m)` → `{tag, tone, court, group,
alert, lines[], cta, post}`; `filled(m)`; `hm(m.start)`; `when(m.start)`; `CLUBS[club].n`;
`CLUBS[club].court` **(the club's *example* court string, not this match's court)**;
`m.dur`; `glyph(sport, seatSyms(m), 58, dark)`; `ST_TONE[tone]`.

> **[GAP-D8] The strip card shows `CLUBS[club].court` — a hard-coded sample court name — for
> every state except `ready`.** `ST.ready` alone resolves the real `m.courtId`. The subtitle
> line therefore displays *"Court 2 · Mondo"* for a match that holds `ct1`. In production the
> line must show the **category**, never a court name, until `ready` [SRC: 3.1 §5 `ready`:
> *"The only state that names a specific court"*].

**`matchCard` (the lanes) reads:** `matchFit(m)` → `{score}`; `filled`; `cardOff`; `payable`;
`when(start)`; `m.badge`; `CLUBS[club].{n,dist}`; sport/format/counts tags;
`glyph(sport, seatSyms(m), 46)`; `matchState(m).{tag,tone}`; the struck-through `m.share` when
a card discount applies.

**D5** `.fit.hi` at `score >= 90` → coral. **[SUPERSEDED — doc 5 A2]** gate on
`fit >= 90 AND coverage >= coverage_floor`; below the floor render in `--night` with no coral.

**D6** `seatSyms(m)` maps each seat to `'me' | 'g' | 'x' | null`; a **paid-or-not distinction
does not exist in the glyph** — an invited unpaid seat renders identically to a paid one.
**[GAP-D9]** the glyph contradicts `filled`, which counts only paid. Add a fourth symbol.

**D7** `st.cta` is read as `(st.cta || {}).label || 'Open match'` — **no state in the table
defines `cta`**, so every card falls back to *"Open match"*. The `cta` field in the doc 3.1
§10.2 payload is unimplemented. **[GAP-D10]**

---

## D.15 `lifeOf` — the nine canonical states shared with the club console

**D1** `def life_of(m, now) -> Life9` · pure. **D2** The cross-application contract.
**D3**
```js
 1 inventoryLost || clubCancelled || formCancelled || checkpointCancelled → 'CANCELLED'
 2 now >= matchEnd(m)                                                     → 'PLAYED'
 3 vacated && committedAt != null                                         → 'RECOVERING'
 4 isFull(m)  → (now >= d.commit || committedAt != null) ? 'CONFIRMED' : 'FUNDED'
 5 filled > 0 && (start − now) < 48h && hold.kind !== 'none'              → 'AT_RISK'
 6 hold.kind === 'soft' || hold.why === 'club'                            → 'HELD'
 7 hold.why ∈ {stale, nearLapsed, farLapsed} || releasedAt != null        → 'RELEASED'
 8 otherwise                                                              → 'FORMING'
```
**D6** Rung 5's `< 48h` is **exclusive**; `filled > 0` strict. Rung 4 uses
`now >= d.commit || committedAt != null` — **not** `committedNow(m)`, though they coincide when
`isFull`. **D7** A hard hold from rung 6 of the ladder (`full`) is caught by rung 4 first.
**[GAP-D11]** rung 6 tests `hold.why === 'club'` but a club-locked court returns
`kind: 'hard'`, so `HELD` is reported for a hand-committed court — correct, but it means
`AT_RISK` (rung 5) claims it first inside 48 h. Order is the specification; assert it.

---

## D.16 `holdUntil` — the invitation hold (drives `formingHeld`)

**D1** `def hold_until(from_: Instant, start: Instant, commit: Instant) -> Instant` · pure.
**D3**
```js
let t = from + 2*HOUR;
if (start − from < 4*HOUR) t = from + 30*60e3;      // short notice
const h = new Date(t).getHours();
if (h >= 22 || h < 8) {                             // never lapse overnight
  const d = new Date(t); if (h >= 22) d.setDate(d.getDate() + 1);
  d.setHours(8, 0, 0, 0); t = d.getTime();
}
return Math.min(t, commit);                         // never past commitment
```
**D4** Three rules in strict order: base 2 h → 30 min if inside 4 h → push out of quiet hours →
**truncate to `commit`**. *"Commitment is a hard constraint and civility is a soft one."*
**D6** `start − from < 4h` **exclusive**: at exactly 4 h the hold is 2 hours. `h >= 22` and
`h < 8` — 22:00 pushes to 08:00 **next day**; 07:59 pushes to 08:00 **same day**; 08:00 is
untouched.
**D7** If `commit` is already past, `min` returns `commit` — a hold that has **already expired**.
Correct and intended. **DST: `setHours(8,0,0,0)` on a spring-forward day where 02:00–03:00 does
not exist is still well defined (08:00 exists), but the elapsed hold is 1 h shorter or longer
than nominal. See §F.4.**
**D10** Invite at 21:00 Friday for Saturday 18:30, `commit` Friday 18:30 (already passed):
`t = 23:00` → quiet hours → `08:00 Saturday` → `min(Sat 08:00, Fri 18:30)` = **Fri 18:30** —
the hold is dead on arrival, which is exactly Rule "never past commitment" [SRC: 3.1 §9.2].

---

## D.17 `nextWakeAt` — not in the prototype, required in production

**D1** `def next_wake_at(m, now) -> Instant | None` · pure, no side effects [SRC: doc 3 §2.1].
**D3**
```ts
if (isTerminal(m)) return null;
candidates = []
if (m.committedAt == null)              candidates.push(d.commit)
if (filled(m) === 2 && n > 2)           candidates.push(m.start − 12h)     // Rule 8
if (filled(m) === n − 1 && n > 2)       candidates.push(m.start −  4h)     // Rule 6
if (m.vacated && m.committedAt != null) candidates.push(d.rescue)
candidates.push(d.check, d.joinCut, m.start − 15min, m.start,
                matchEnd(m), resultWindow(m), keepUntil(m))
return min(candidates.filter(t => t > now))
```
**Two candidates the prototype's ladder needs and doc 3's list omits:**
`m.created + policy.maxHoldAge` (the stale rung) and, if `clubExtended` can be withdrawn, the
withdrawal instant. **[GAP-D12]** without the first, a `heldStale` transition never wakes
anybody and the card is late by up to the next scheduled wake.
**D6** `t > now` **strict** — a candidate exactly at `now` is not a future wake, which is what
makes the `EvaluateAt` idempotency key terminate.
**D7** All candidates in the past → `min([])` → must return `None`, not `+Inf`.
**D8** Pure. **Recomputed on every write**, because the candidate set depends on the seat
count: *"A match on two paid seats wakes at T−12h; the same match after a third payment wakes
at T−4h instead."*

---

# E. STATE MACHINES

## E.1 The resolution ladder — the order IS the specification

**35 contexts.** 15 base rungs plus 2 wrapper rewrites. Tested top to bottom; **first match
wins**. Reordering changes behaviour.

| # | Guard (exact) | → | Inclusive/exclusive |
|---|---|---|---|
| 1 | `m.inventoryLost` | `inventoryLost` | — |
| 2 | `m.clubCancelled \|\| m.weather` | `cancelledClub` | — |
| 3 | `m.formCancelled` | `cancelledIncomplete` | — |
| 4 | `m.checkpointCancelled` | `cancelledCheckpoint` | — |
| 5 | `now >= matchEnd(m)` | post-play group ▼ | **inclusive** |
| 5a | `m.noShow` | `playedNoShow` | — |
| 5b | `filled(m) < m.n` | `playedShort` | strict |
| 5c | `m.confirmed` | `completed` | — |
| 5d | `now >= resultWindow(m)` | `playedNoScore` | **inclusive** |
| 5e | `m.score` truthy | `confirmResult` | — |
| 5f | otherwise | `needsResult` | — |
| 6 | `!mySeat(m) && waitlists.includes(m.id)` | `waitlisted` | — |
| 7 | `m.kind === 'private'` | private group ▼ (`privateOpen` if `openSeats>0`, else `privatePartial` if `payModel==='split'`, else `privateReserved`) | — |
| 8 | `m.vacated && m.committedAt != null` | recovery group ▼ | — |
| 8a | `m.transferring` | `replacementTransfer` | — |
| 8b | `now >= d.check` | `rescueLate` | **inclusive** |
| 8c | `now >= d.rescue` | `rescue` | **inclusive** |
| 8d | otherwise | `replacement` | — |
| 9 | `m.vacated` (⇒ `committedAt == null`) | `isProtected(m) ? protectedBack : formingBack` | — |
| 10 | `isFull(m)` | full group ▼ | — |
| 10a | `now >= m.start − 15min` | `ready` | **inclusive** |
| 10b | `m.committedAt != null` | `committedOnFill(m) ? confirmedOnFill : confirmed` | — |
| 10c | otherwise | `full` | — |
| 11 | `isProtected(m)` (= `courtHold(m).kind !== 'none'`) | court group ▼ | — |
| 11a | `hold.why === 'club'` | `clubHeld` | — |
| 11b | `hold.kind === 'soft'` | `heldSoft` | — |
| 11c | `now >= d.commit` | `protectedLate` | **inclusive** |
| 11d | otherwise | `protectedCourt` | — |
| 12 | `m.releasedAt != null && filled(m) >= 2 && now < d.check` | `heldReleased` | `>=` inclusive, `<` **exclusive** |
| 13 | `m.seats.some(s => s.p && !s.paid)` | `formingHeld` | — |
| 14 | `now >= d.commit` | `formingLate` | **inclusive** |
| 15 | otherwise | `forming` | — |
| **W1** | after 1–15: `hold.why === 'stale'` **and** key ∈ {`heldReleased`,`forming`,`formingLate`} | `heldStale` | — |
| **W2** | after 1–15: `hold.why === 'extended'` **and** key ∈ {`heldReleased`,`forming`,`formingLate`,`heldSoft`} | `heldExtended` | — |

### The orderings that carry weight, each with the case that proves it

1. **Cancellation beats play (1–4 before 5).** A club cancelling at 19:00 for an 18:30 match
   must read *cancelled*, not *played*. The player did not play.
2. **Inventory loss beats club cancellation (1 before 2).** `inventoryLost` **also sets**
   `clubCancelled`, so without the earlier test *every* inventory loss would render as a
   weather cancellation — and the player would never learn the one risk they were carrying.
3. **Recovery beats full and beats forming (8 before 10–11).** A committed match that lost a
   player has `filled = n−1`, which would otherwise fall to the court group and read
   *"Court protected · one player needed"* — indistinguishable from an ordinary forming match,
   *"a catastrophic thing to tell somebody whose money is at stake."*
4. **Full beats protected (10 before 11).** A full match is also protected; reporting the court
   state on a complete group is the less useful of the two facts.
5. **Wrappers run last** (W1/W2 after 1–15) so a cancelled or played match is never relabelled
   as a court state — a stale hold on a cancelled match must still read `cancelledClub`.

### Two ordering defects, both from doc 5, both reproducible

> **[GAP-E1 · B2] Rung 5 has no test for whether the viewer is in the match.** A waitlisted
> player whose match has been played falls into rung 5 (`now >= matchEnd`) **before** rung 6
> and is told *"Needs result · thirty minutes, any of the four"* for a match they did not play.
> **Proposal: move rung 6 above rung 5 — above the cancellation rungs too**, since a standby
> entry on a cancelled match should read as a standby entry that ended, not as a cancellation
> of the viewer's booking. *"Am I in this match at all"* is a coarser question than *"what
> happened to it"* and belongs higher.

> **[GAP-E2 · B1] Rung 9 cannot fire, so `formingBack` and `protectedBack` are unreachable.**
> `vacated` is written **only when a committed player leaves** [SRC: 3.1 §1.2 fact table, and
> `leaveMatch` sets `vacated` on every leave but `syncMatch` never clears it]. Rung 8 catches
> `vacated ∧ committedAt ≠ null`; rung 9 needs `vacated ∧ committedAt = null` — which the
> documented fact table cannot produce. Yet §3.2, §6.2 and §7.3 all route an uncommitted leave
> there. There is a second problem in the same rung: `vacated` is **never cleared** and rung 9
> sits **above** rung 10, so once it can fire, a refilled match would read `protectedBack`
> forever. The documented 24-hour decay has no mechanism.
> **Proposal:**
> ```
>  9  vacated AND committedAt = null
>     AND not isFull(m)
>     AND now < vacatedAt + 24h        → isProtected ? protectedBack : formingBack
> ```
> This makes both states reachable, makes the decay mechanical, and stops a recovered match
> being pinned in a recovery state.

## E.2 State set — 35 contexts → 17 tags (both directions)

| Group | Context keys | Tag | Tone | Backend (LIFE9-adjacent) |
|---|---|---|---|---|
| Forming | `forming`, `formingHeld`, `formingLate`, `formingBack` | Forming | idle · idle · idle · **watch** | FORMING |
| Held | `heldSoft` | Court held | watch | COURT_HELD |
| Held | `heldExtended` | Court held | **good** | HELD |
| Released | `heldReleased`, `heldStale` | Court released | watch | COURT_RELEASED / RELEASED |
| Club | `clubHeld` | Court committed | good | COURT_PROTECTED |
| Protected | `protectedCourt`, `protectedBack`, `protectedLate` | Court protected | good | COURT_PROTECTED |
| Full | `full` | Full | good | FULL_UNCOMMITTED |
| Confirmed | `confirmed`, `confirmedOnFill` | Confirmed | good | CONFIRMED |
| Recovery | `replacement`, `replacementTransfer` | Replacement pending | watch | REPLACEMENT_PENDING |
| Recovery | `rescue`, `rescueLate` | Rescue active | **time** | RESCUE_ACTIVE |
| Ready | `ready` | Ready to play | good | CONFIRMED |
| Post-play | `needsResult` | Needs result | watch | COMPLETED |
| Post-play | `confirmResult` | Confirm the result | watch | COMPLETED |
| Post-play | `completed` | Completed | good | COMPLETED |
| Post-play | `playedShort`, `playedNoShow`, `playedNoScore` | Played | idle | COMPLETED |
| Cancelled | `cancelledIncomplete`, `cancelledCheckpoint`, `cancelledClub` | Cancelled | ended | CANCELLED |
| Cancelled | `inventoryLost` | Cancelled | **`bad`** | CANCELLED |
| Standby | `waitlisted` | On standby | idle | — |
| Private | `privateReserved`, `privatePartial`, `privateFull`, `privateOpen` | Reserved | good | RESERVED / PARTIALLY_PAID / FULLY_PAID / PUBLIC_SEATS_OPEN |

> **[GAP-E3] `inventoryLost` declares `tone: 'bad'`, which is not a key of `ST_TONE`**
> (`good`, `watch`, `time`, `ended`, `idle`). `ST_TONE['bad']` is `undefined`, so the tag dot
> renders with `background: undefined` — the browser falls back to transparent. The only
> state describing the one risk the product names from the first screen has **no colour**.
> **Proposal: `tone: 'ended'`, matching the other three cancellations.** Add an exhaustiveness
> assertion over the tone enum at module load.

**Tag → contexts (the reverse map)** is one-to-many for 8 of the 17 tags; the tag is the truth
about the group, the context line says which situation produced it. A client rendering only the
tag loses the distinction between *"the court went back because two seats are not enough inside
12 hours"* and *"the club returned a hold that had sat 48 hours"* — which is precisely the
failure `heldStale` was added to fix: *"A player told the wrong reason once stops believing the
right ones."*

## E.3 Terminal states and illegal transitions

**Terminal (irreversible, card stays 24 h, then history):** `inventoryLost`, `cancelledClub`,
`cancelledIncomplete`, `cancelledCheckpoint`. Post-play states are terminal for the match but
`needsResult → confirmResult → completed` still moves.

**Structurally unreachable — assert, do not assume** [SRC: 3.1 §9.1 inv. 3–4, doc 3 §5.2 inv. 4–5]:
```
committed AND no court        — Rule 3 pins the court hard
committed AND soft hold       — Rule 3 promotes it to hard
```
*"A bug producing either would be invisible on screen and catastrophic in effect: a committed
match whose court quietly went back."*

**Illegal:** any terminal → non-terminal; `committedAt` non-null → null; `confirmed` → `full`;
`completed` → `needsResult`.

## E.4 Degenerate and structurally-impossible inputs to the ladder

| Input | Result | Correct? |
|---|---|---|
| `seats = []` | `isFull` = **true** (vacuous `every`) → rung 10 → `ready`/`full` | **no** — reject `n ∉ {2,4}` at creation |
| `vacated` set on a match with all seats filled | rung 8 fires, card says *"3 of 4 · the seat stays funded"* while 4 are seated | **no** — clear `vacated` on refill (`fillSeat` does; `syncMatch` does not) |
| `noShow` set on a future match | rung 5 not reached (`now < matchEnd`), so no effect until the end | correct |
| `score` set before `matchEnd` | ignored until rung 5 | correct |
| `waitlisted` **and** holding a seat | rung 6 requires `!mySeat`, so the seat wins | correct |
| both `formCancelled` and `checkpointCancelled` | rung 3 wins → `cancelledIncomplete` | correct — they are mutually exclusive by construction (7a vs 7b) |
| stale client posts a state key | commands carry **intent**, never conclusions; reject | correct by contract |

---

# F. TEMPORAL SEMANTICS

## F.1 Every deadline, its formula, and what it is relative to

| Name | Formula | Relative to | Recomputed on read? |
|---|---|---|---|
| `commit` | `min(start − policy.window·h, start − 12h)` | `start` | **yes** |
| `rescue` | `start − (solo ? 6 : 4)·h` | `start` | yes |
| `check` | `start − 2h` | `start` | yes |
| `joinCut` | `start − policy.joinCut·min` | `start` | yes |
| `play` | `start` | — | yes |
| hold far lapse | `start − 12h` | `start` | yes |
| hold near lapse | `start − 4h` | `start` | yes |
| door code | `start − 15min` | `start` | yes |
| `matchEnd` | `start + dur·min` | `start` | yes |
| `resultWindow` | `matchEnd + 30min` | `matchEnd` | yes |
| `keepUntil` | `matchEnd + 24h` | `matchEnd` | yes |
| stale hold | `created + policy.maxHoldAge·h` | **`created`** | yes — the only one anchored to creation |
| invitation hold | `holdUntil(from, start, commit)` | the **invite instant** | **written once** at invite time |

**Everything except the invitation hold is a pure function of `start` (or `created`) and is
recomputed on every read. Nothing is frozen.**

## F.2 Written once and frozen

| Value | Why it cannot be recomputed |
|---|---|
| `share` | *"Written at creation, once. Never re-priced."* Re-deriving it after a rate change would re-price a seat somebody already bought |
| `committedAt` | the inputs stop supporting the derivation the moment somebody leaves |
| `protectedAt` | records **when** a court was first assigned; the ladder can re-satisfy but the first crossing is history |
| `releasedAt` | a receipt: the notification was sent |
| `rescueTaken` | prevents a second full-price refund |
| the four terminal flags | receipts that the refund ran — **but the state must be derived, not read from them** [GAP-D3] |

## F.3 Precedence when several deadlines apply at one instant

Two documented coincidences, both real, both requiring a test:

1. **T−12h is two rules.** The commitment floor (`min(window, 12h)`) **and** the 2-seat hold
   lapse. At a 12-hour club they fire **at the same instant**: the match commits if full, and
   loses its court if on two seats. At a 24-hour club they are twelve hours apart. Order:
   `syncMatch` runs the **ladder first** (steps 2–5), **then** commitment (step 6), **then**
   the checkpoint (step 7). So on a full match the court is assigned hard by rung 4 *before*
   `committedAt` is written — which is why invariant 3 (`committed ⇒ hard`) holds even in the
   same tick.
2. **T−4h is two rules.** The 3-seat hold lapse **and** the doubles rescue window opening.
   They do not interact, but they land together and a player watching sees one change.

At exactly `check` (T−2h) three things could apply: rung 5's inventory-loss window **closes**
(`now < d.check` is exclusive), the checkpoint **fires**, and `heldReleased` **stops being
reachable** (rung 12's `now < d.check`). Evaluation order in `syncMatch` resolves it: inventory
loss is tested before the checkpoint, so a match that lost its category at 16:29:59.999 reads
`inventoryLost`, and one that survived to 16:30:00.000 reads `cancelledIncomplete`.

## F.4 Timezone and DST

The prototype uses `new Date(...)` throughout — **device local time**, with `getHours()`,
`setHours(8,0,0,0)` and `getDay()`. Every club is in Kraków.

**Production rules:**
- Store every instant as `timestamptz` (UTC). Compute every deadline in UTC.
- **Every wall-clock rule is club-local:** `PEAK` at 17:00, `OPEN` 07:00–22:00, the 22:00–08:00
  quiet window, `podOfMin`, `partOfDay`, and the `dow|hh:mm` slot-discount key. Evaluate these
  in `Europe/Warsaw`, not UTC and not the device's zone.
- **Spring forward (last Sunday in March, 02:00→03:00):** a match at 02:30 does not exist —
  reject at creation. `start − 12h` across the transition is **11 wall-clock hours**; use true
  elapsed duration (UTC arithmetic), which is what a 12-hour promise means.
- **Fall back (last Sunday in October, 03:00→02:00):** a 02:30 start is **ambiguous**; resolve
  to the first occurrence and store the UTC instant. `holdUntil` pushing to 08:00 is
  unambiguous either way.
- The client renders in its **own** zone but computes against `serverTime` — never
  `Date.now()` directly.

## F.5 What recomputes on read vs what is frozen — and the one thing that reorders

`V.home` sorts the strip by `m.start` and doc 3 §1.3 rule VI, §4.3 and invariants 10–11 all
rest on *"cards are sorted by match start, which never changes."*

> **[GAP-F1 · doc 5 B4] `start` is not immutable.** Rescue Stage 4 shifts the match by
> ±30/60/90 minutes with unanimous consent, and doc 3.1 §6.4 treats it as the interesting case:
> *"A successful Stage 4 moves the entire match half an hour later — a real, consequential
> change — and the state does not move. What changed is a field, not a state."* A field the
> sort key is derived from. **Proposal: a fourth wire frame `{"t":"resort", listVersion,
> order:[matchId]}`, or force a full `sync` on the one event that can change `start`.** A
> consented shift is rare, is preceded by a notification the player answered, and is the one
> moment where a reordering animation is *informative*. Restate the invariant as *"only a
> consented time shift reorders, and it announces itself."*

## F.6 Clock skew and in-flight boundary crossings

- **One clock read per command.** `const now = clock.now()` captured once and passed to
  everything. *"Two reads inside one command can disagree, and the money engine already depends
  on them not doing so."*
- **The client never uses absolute device time.** Every frame carries `serverTime`; the client
  holds an offset and ticks with a **monotonic** source. A wrong device clock produces a
  drifting countdown, never a wrong state.
- **A boundary crossed mid-request:** the request is evaluated at its single captured `now`.
  If the threshold has since passed, the timekeeper's `EvaluateAt` picks it up within the poll
  interval (2 s), and its idempotency key `{matchId}:{threshold}:{scheduledFor}` makes a
  duplicate a no-op.
- **Precision is the poll interval.** *"At 2 seconds, a state flips within two seconds of its
  threshold. Nothing in this product needs better."* Threshold-to-pixel budget: **< 2 s at p99**.
- **Clock scrubbed backwards** must reproduce every derived value **except `committedAt`**
  (and, in production, except the side-effect receipts, which is [GAP-D3]).

---

# G. INVARIANTS AND CONTRACTS

## G.1 Assertions that must hold after every operation

```python
# --- money -------------------------------------------------------------
assert m.share_grosze * m.n <= m.price_grosze                       # G1.1
assert m.share_grosze == old_share_grosze                           # G1.2 write-once
assert 0 <= payable(m) <= share_after_disc(m)                       # G1.3
assert 0 <= slot_disc(m) <= m.price                                 # G1.4

# --- commitment --------------------------------------------------------
assert not (was_committed and m.committed_at is None)               # G1.5 never unwritten
assert (m.committed_at is None) or (m.committed_at >= m.created)    # G1.6
assert not (committed_now(m) and court_hold(m,now).kind != 'hard')  # G1.7 Rule 3
assert not (committed_now(m) and m.court_id is None)                # G1.8 UNREACHABLE
assert not (committed_now(m) and court_hold(m,now).kind == 'soft')  # G1.9 UNREACHABLE
assert filled(m) == sum(1 for s in m.seats if s.player_id and s.paid)  # G1.10

# --- leaving -----------------------------------------------------------
assert not (leave_was_committed and seat.paid is False)             # G1.11
assert not (leave_was_uncommitted and seat.paid is True)            # G1.12

# --- state -------------------------------------------------------------
assert state(m, now) in STATE_KEYS                                  # G1.13 no fall-through
assert tone_of(state) in {'good','watch','time','ended','idle'}     # G1.14  (catches GAP-E3)
assert terminal_before implies terminal_after                       # G1.15
assert singles(m) implies state(m,now) != 'heldSoft'                # G1.16 Rule 10
assert next_wake_at(m,now) is None) == is_terminal(m)               # G1.17
assert next_wake_at recomputed on EVERY write                       # G1.18

# --- the feed ----------------------------------------------------------
assert sum(t.weight for t in FIT_TERMS) == 100                      # G1.19 at module load
assert 20 <= fit.score <= 99                                        # G1.20
assert len(fit.reasons) == 3                                        # G1.21
assert (fit.warn is not None) == (lowest_by_contribution.value < 0.55)   # G1.22
assert no card appears twice across lanes                           # G1.23
assert every card's fit >= its lane's floor                         # G1.24
assert no lane exceeds its cap; global cap 6                        # G1.25
assert scorer never ran on a candidate that failed eligibility      # G1.26 call counter
assert no stage relaxed a criterion to produce output               # G1.27
assert no card overlaps a match the player is already enrolled in   # G1.28
assert feed reproducible from (player, minute-bucket, exploration seed)  # G1.29

# --- the screen --------------------------------------------------------
assert strip == sorted(strip, key=lambda c: c.start)                # G1.30
assert a state change alone never reorders the strip                # G1.31 (see GAP-F1)
assert list_version is monotonically non-decreasing                 # G1.32
```

## G.2 Written once, never recomputed — and why

Covered in §F.2. The one worth repeating: **`committedAt` is the single persisted crossing**,
and *"everything downstream depends on this one boolean not lying: whether the leaver gets 100 %
or an outcome-based refund, whether the court stays hard-held, whether the rescue cascade may
run, and what the checkpoint does at T−2h."*

## G.3 Cross-application contracts

The player app and the **club console** consume one lifecycle. The prototype asserts **40
cross-application rules in `conformance.js`, currently 0 disagreements**. Each is a contract.

| Contract | The exact rule | Player app's obligation | Club console's obligation | Assertion |
|---|---|---|---|---|
| Canonical lifecycle | the **nine** states in **the same order**: FORMING, HELD, RELEASED, FUNDED, CONFIRMED, AT_RISK, RECOVERING, PLAYED, CANCELLED | derive via `lifeOf` | derive identically | `LIFE9` list equality, index by index |
| Hold ladder | every tier: 4→hard, n−1→soft while `left > 4`, 2→soft while `left > 12`, ≤1→none | `courtHold` | same | evaluate both at every tier × every `left` |
| Singles | **no soft tier, ever** | Rule 10 (`n > 2` guard) | same | `n=2 ⇒ kind ∈ {hard, none}` |
| Hand-commit | *a hand-commit beats everything* | rung 2 above rungs 3–9 | same | ordering test |
| Max hold age | a soft hold older than `maxHoldAge` goes back | wrapper W1 | publisher | both agree on the released instant |
| Demand-aware extension | may only ever **extend**, never release early | wrapper W2 | the club **owns** the model; the player app **reads** `clubExtended`/`clubFill` | assert the player app contains no fill model |
| Commitment | `commit = min(window, 12h)` | `deadlines` | same | equality at both club windows |
| Rescue window | 4 h doubles, 6 h singles | `deadlines` | same | equality |
| Checkpoint | 2 h, **universal, cannot be switched off** | `deadlines` | same | assert no policy key can disable it |
| Invitation hold | 2 h · 30 min inside 4 h · **never lapses 22:00–08:00** · never past commitment | `holdUntil` | same | equality across the overnight case |
| Court price | `RATE × club.pm × court.pm`, rounded | `courtPriceOf` | same | equality per multiplier |
| Seat price | **`share = court ÷ players`** | `shareOf` | same | equality; and assert the console cannot set a seat price |
| Slot discount | lands identically on both sides | `slotDisc`/`shareAfterDisc` | same | equality |
| Allocation policies | the four names: rotating fairness · membership weighted · lottery · first come | display only | owns the policy | name equality |
| Published policy | **contains no player rating** | must not send one | must not request one | schema assertion |
| Publishing | charges nobody | — | — | ledger assertion |
| Intent | the **ten fields in the same order** | `IFIELDS` | engine field order | list equality |

**Where this belongs in production.** The backend is Python and cannot run in Expo, so a
shared TypeScript kernel per client was **considered and rejected** (ADR-0021), as was a kernel
behind a network hop. Doc 3 §4.1's *"the kernel ships to the server and both clients — that is
already established"* is **established as rejected** [SRC: doc 5 A6].

The replacement, and it is strictly better:

- **The rules live in one place: the server.** One Python package, `matchfit/v1` and
  `pairing/v1` style — pure, mypy-strict, tested against hand-built snapshots with no database.
- **The contract is a published schema plus a shared fixture corpus**, not shared code. Both
  applications are tested against the *same* fixture file; conformance is a CI job that loads
  both and asserts every rule above.
- **Time-varying answers ship with their transition schedule.** A resource whose state changes
  at instants known in advance carries the current value, an **explicit list** of
  `{at, key, tone, facts}` transitions, and a `computed_at`. The client renders by comparing
  `now` against instants it was handed, and holds **no rules at all**.
  `nextWakeAt` already enumerates the candidates, so producing the list is free and it is
  bounded at about five entries.

**Consequence of drift.** If the two sides' ladders diverge, *"a player and a manager are on
the phone about the same booking"* and the app shows a court held that the club has already
released — *"the worst failure this system can have, and it is silent until somebody arrives at
a court that is not theirs."*

## G.4 What the sources forbid computing locally

| Forbidden | Where stated | Failure it prevents |
|---|---|---|
| **A club's fill model** (`clubFill`, `clubExtended`) | v37 §0.2 Invariant 6; `ST.heldExtended` | *"The first implementation did recompute it, and the conformance suite caught the two apps disagreeing about whether a court was held"* |
| **The state key, as a stored column** | 3.1 §1.1; doc 3 §7.4 | *"Storing it creates a value that can disagree with its own inputs, and every failure mode becomes wrong instead of late"* |
| **A second implementation of the state table on the client** | 3.1 §10.1 | *"Two implementations guarantee they eventually disagree about what one match is doing"* |
| **Client-side conclusions** | doc 3 §4.1 | *"Commands carry intent — join this match — never conclusions — this match is committed"* |
| **Any relaxation to fill a lane** | doc 4 §1.3; `V.home` copy | *"We do not invent players to make a city look busy"* |
| **Caching `PairingAnalysis` per match** | doc 5 D1 | it reads `snapshot.current_player` to seat the asker — a per-match cache would be **silently wrong** |
| **The device clock, used directly** | doc 3 §5.1; doc 5 E3 | a wrong device clock becoming a wrong state instead of a drifting countdown |

---

# H. TRANSACTIONS, CONCURRENCY AND MONEY

## H.1 Atomic boundaries

| Operation | Must be atomic over | Boundary |
|---|---|---|
| **Join and pay** | seat occupancy **+** payment **+** ladder re-evaluation **+** commitment write **+** outbox | one transaction. *"Occupying a seat and paying for it are one act. There is no reserve-and-pay-later, because a reserved seat that is not paid holds nothing and blocks somebody who would have paid"* |
| **Court assignment** | `court_holds` insert **+** `matches.court_id` update | one transaction; the `EXCLUDE` constraint is the mutual exclusion |
| **Leave** | seat clear **+** `paid` flag **+** `vacated`/`vacatedAt` **+** refund intent **+** outbox | one transaction |
| **Checkpoint** | the terminal flag **+** every refund or credit **+** court release **+** outbox | one transaction |
| **Any write** | the fact delta **+** `next_wake_at` **+** the outbox row | *"one transaction, includes the outbox"* — no dual write between the database and the bus |

## H.2 Race conditions and the strategy for each

| Race | Actors | Strategy |
|---|---|---|
| **Threshold vs player action on one match** | timekeeper + player | **One writer, optimistic concurrency.** Both load version v11; the player appends v11→v12; the timekeeper's append fails the version check and **retries by re-loading and re-evaluating** — not by replaying a stale decision. *"Both effects land, in a defined order, with no lost write."* The retry re-runs `evaluate` so the rescue threshold is applied to a match that already has a vacancy |
| **Two matches taking the same court** | two command handlers | **Not solvable at the match layer.** Optimistic concurrency on `m1` says nothing about `m2`. *"Two open matches, same club, category and hour, both crossing their ladder threshold in the same second, both load the free-court list and both take the same court"* — and `inventoryLost` is **terminal and refunds everybody**. **The hold must be a reservation on a Courts aggregate with a uniqueness constraint on `(court, slot)`**, acquired first, then recorded on the match. This also settles whether `inventoryLost` is a *query result* (nothing was free) or a *race outcome* (something was free and somebody took it) — different stories to tell the player |
| **Two players taking the last seat** | two joins | the seat unique index plus the version check; the loser gets *"This match is full"*, which is the message they should see anyway |
| **Two simultaneous leaves** | two players | **UNHANDLED.** *"A second `vacated` overwrites the first."* With four seats, a four-hour rescue window and a group that often knows each other, this is *"a normal Saturday, not an edge case."* Overwriting loses the first leaver's refund position entirely. **Proposal: `vacancies: [{seat, player, at, outcome}]`, one rescue process per vacancy** |
| **Two of a player's matches changing at once** | projection consumer | **Partition the projection by `playerId`, not `matchId`** — *"that is the one non-obvious choice, and it is not optional"*; otherwise a player's list version can go backwards and a valid card is rejected |
| **Timekeeper firing twice** | two workers | deterministic idempotency key `{matchId}:{threshold}:{scheduledFor}`; `FOR UPDATE SKIP LOCKED` on the poll |

## H.3 Idempotency keys for anything that moves money

| Command | Source | Key |
|---|---|---|
| `JoinMatch` | player | client-generated UUID |
| `LeaveMatch` | player | client-generated UUID |
| `InviteToSeat` / `AcceptInvite` | player | client-generated UUID |
| **`PayForSeat`** | payment webhook | **payment intent id** |
| `EvaluateAt` | timekeeper | **`{matchId}:{threshold}:{scheduledFor}`** — deterministic |
| `ClubCancel` / `LockCourt` | club console | club action id |
| `ConsentResponse` | player | consent id + player id |

*"`EvaluateAt`'s deterministic key is what makes at-least-once scheduling safe, and it is why
the timekeeper needs no exactly-once guarantee, no leader election, and no distributed lock."*

## H.4 Retry and backoff

- Version conflict: **retry once** with a fresh load and a fresh `evaluate`. On the second
  failure, report honestly — *"This match is full"*.
- Timekeeper: no backoff needed; a missed wake is simply late and `next_wake_at <= now` is
  still true on the next poll (2 s).
- Sweep every 5 minutes for `next_wake_at IS NULL OR next_wake_at < now() − 1 minute`.
  *"If the sweep ever finds anything, that is a bug and should page somebody — but it means the
  bug produces a late card, not a wrong one."*
- Payment webhook: exponential backoff; the intent id makes replay free.
- **A failed recurring charge retries after 24 hours before any person is asked.**

## H.5 Authorised vs captured vs settled — who holds the funds

| Stage | Trigger | Who holds it | Player-facing |
|---|---|---|---|
| **Authorised** | card authorisation on a low-reliability player | the player's bank; *"Your card will be authorised, not charged"* — released after the scan | shown as a hold |
| **Captured / held by the platform** | the seat payment lands | **the platform**, `held: true` on the ledger line | *"Nothing has reached the club yet"* — the `full` state's fourth line |
| **Settled to the club** | `settledNow(m)` ⟺ `m.settledAmount != null OR committedNow(m)` | **the club** | *"{price} settled to the club"* — the `confirmed` court facet |
| **Refunded** | the outcome resolves | back to the player | *"Wallet money is immediate; a card refund appears once your bank posts it"* |

**The refund is decided by the outcome, never by the clock** — Invariant 3. `leaveOutcome`:
```js
if (m.clubCancelled)      → {kind:'club',     pc:100}
if (!committedNow(m))     → {kind:'reversal', pc:100}   // full reversal, seat becomes UNPAID
if (now < d.rescue)       → {kind:'full',     pc:100}   // if a player pays full price
otherwise                 → {kind:'rescue',   pc:50}    // if a Rescue player pays
```
and the four outcomes shown **before** the player confirms: full price **100 %** · Rescue
**50 %** · a sponsored guest **0 %** · nobody **0 %**. *"Showing one number would be a promise
the engine cannot make."*

Two money rules that constrain the engine:
- **A club-sponsored guest cannot fill a vacated seat** — that would let a club decide a
  refund. Only the leaver's own group may sponsor.
- **No automatic rule may ever put money in the wallet.** Issuing credit is always deliberate.
  The wallet and the club card never merge.

## H.6 Reconciliation and audit

- Every money movement writes a ledger line with a reference (`PAY-…`, `REF-…`, `REV-…`) and a
  `held` flag; the ledger is **event-sourced** even though the match is *"a record with an
  outbox"*.
- The projection is a **cache**: *"it can be rebuilt from the match records at any time, and
  the rebuild is the disaster-recovery story."* Assert byte-identity on a schedule, not once.
- Reconcile daily: for every match, `Σ paid seats × share` against captured funds, and
  `settled` against club payouts.
- **The one asymmetry to audit:** on `inventoryLost` and `cancelledClub`, *"everybody is
  refunded in full, including anybody who had already left"* — so a player who left at T−20h
  and took a 50 % outcome gets the other 50 % back. A reconciliation that assumes refunds are
  monotone will flag these as duplicates.

---

# I. API SURFACE

| Method | Purpose | Request | Response | Codes | Auth | Idempotent | Cacheable |
|---|---|---|---|---|---|---|---|
| `GET /now` | the whole screen | `?sport=all\|Padel\|…` | `NowScreen` + `serverTime` + `listVersion` | 200 · 401 | the bearer's own player id only | n/a | **strip: must be fresh** (money position). **lanes: ≤ 60 s** (a suggestion a minute old harms nobody) |
| `GET /now/strip` | cold start, one indexed read | — | `PlayerCardList` | 200 · 401 | own | n/a | must be fresh |
| `GET /feed` | lanes only, for pull-to-refresh | `?sport=` | `Feed` + `FeedTrace` id | 200 | own | n/a | ≤ 60 s, keyed `playerId:sportFilter:surface` |
| `POST /matches/{id}/verify-joinable` | **tap-time verification** | — | `{ok}` or `{reason, alternatives[2]}` | 200 · 404 | any authed | yes | **must be fresh, always** |
| `POST /commands` | every write | `{type, matchId, id: uuid, …}` | `{events[]}` | 202 · 409 · 422 | own seat / own action | **yes, by `id`** | never |
| `WS /stream` | `sync` · `patch` · `drop` · `ping` · **`resort`** | held `listVersion` | frames | — | own | monotonic accept | n/a |

**Error codes and their user-facing meaning**

| Code | Meaning | Copy key |
|---|---|---|
| `409 version_conflict` | retried once, then surfaced | `match_changed` |
| `422 match_full` | the last seat went | `just_filled` — **and two alternatives ship with it** |
| `422 joining_closed` | past `joinCut` | `joining_closed` |
| `422 cancelled` | terminal | the specific terminal key, never a generic one |
| `422 below_reliability_gate` | Player Score < 70 | `gate_below_70`, **with what clears it: turning up. Nothing else** |
| `409 schedule_conflict` | overlaps something the player holds | `clashes` |

**The tap verification is the trust mechanism.** It costs one indexed read on an action the
player already expects to take a moment, and it converts the one unacceptable failure —
*"a card that cannot be joined"* — into a graceful one: *"This one just filled — here are two
others"*, with the two others already in hand from the cached feed.

> **[GAP-I1 · doc 5 D2] `verifyJoinable` checks the match, not the player.** A player who
> booked something overlapping from another device between feed build and tap gets a clean join
> into a clash. **Proposal: resolve `NoScheduleConflict` against the player's *bookings* — not
> only their enrolled matches, since four private-court states sit outside the enrolled
> lifecycle — and re-run the same predicate inside `verifyJoinable`. Both are the same
> predicate called twice.**

**Cache invalidation, explicit, on the player's own actions** (because those they *will*
perceive): joins a match → drop · creates a match → drop · joins a waitlist → drop · changes
sport → different key, no drop needed.

---

# J. TEST SPECIFICATION

## J.1 Every invariant from §G as an executable assertion

Each of G1.1–G1.32 becomes a property assertion run after **every** mutating operation in the
test suite, plus a sampled check in production. G1.8 and G1.9 (`committed AND no court`,
`committed AND soft`) are asserted **unreachable** — they *"deserve the most testing, because a
violation is invisible on screen and catastrophic in effect."*

## J.2 Fixtures from the worked examples

| Fixture | Input | Expected |
|---|---|---|
| `deadlines_ps_24h` | m1, club `ps` | `commit` Fri 18:30 · `rescue` Sat 14:30 · `check` Sat 16:30 · `joinCut` Sat 18:00 |
| `deadlines_as_12h` | same start, club `as` | `commit == start − 12h == Sat 06:30`, **equal to the far-hold lapse** |
| `hold_stale_override` | m1, 2 paid, `now` Sat 06:29, `maxHoldAge` 48 | base `{soft, far}` → composed **`{none, stale}`** → state `heldStale` |
| `hold_boundary_near` | m1, 3 paid | `now = start−4h−1ms` → `heldSoft`; `now = start−4h` → **`heldReleased`** |
| `commit_exact` | m1, 4 paid, `now = commit` | `committedAt == commit` · state `confirmed` · `committedOnFill` **false** |
| `commit_plus_60s` | same, `now = commit + 60_000` | `committedAt == commit` · `confirmed` |
| `commit_plus_60s_1ms` | same, `now = commit + 60_001` | `committedAt == now` · **`confirmedOnFill`** |
| `fit_m1` | m1, viewer `me` | terms 22.3636 / 14.0000 / 13.6125 / 15.0000 / 8.0000 / 5.1333 / 4.5000 · sum **82.6094** · +8 · **91** · warn `None` |
| `fit_m2` | m2, viewer `me` | sum **93.6691** · no mods · **94** · warn `None` · `.fit.hi` true |
| `forecast_m2` | m2 roster | A **2.7120** · B **2.6845** · gap **0.0275** · spread **0.22847319** · pct **89** · youShare **52** · conf `high` |
| `seat_target_m1` | m1 seated | **2.57**; `targetBand` **[2.52, 2.92]** |
| `payable_m1` | m1 | courtPrice **152** · share **38.00** · cardOff **0** · payable **38.00** · `"38,00 zł"` |
| `now_screen_seed` | seeded world, `now` Wed 21:00 | strip `[m7, m1, m8]` · lane 1 `[e6=97, c3=95, m5=94]` · lane 2 `[m2=94]` |
| `hold_until_overnight` | invite 21:00 Fri, start Sat 18:30, `commit` Fri 18:30 | **Fri 18:30** (truncated by commitment) |

## J.3 Boundary tests — at, just below, just above, for every threshold in §C

| Threshold | just below | at | just above |
|---|---|---|---|
| `start − 4h`, 3 paid | `heldSoft` | **`heldReleased`** | `heldReleased` |
| `start − 12h`, 2 paid | `heldSoft` | **`heldReleased`** (or `formingLate` if no court was ever held) | same |
| `commit`, full | `full` | **`confirmed`** | `confirmed` |
| `commit + 60s`, full | `confirmed` | `confirmed` | **`confirmedOnFill`** |
| `commit`, not full | `forming`/`protectedCourt` | **`formingLate`/`protectedLate`** | same |
| `check`, uncommitted & short | `heldReleased` | **`cancelledIncomplete`** | same |
| `check`, committed & short, rebooking club | `rescue` | **`cancelledCheckpoint`** | same |
| `check`, committed & short, standard club | `rescue` | **`rescueLate`** — *nothing happens*, and the card must say so | same |
| `rescue` (T−4h/−6h) | `replacement` | **`rescue`** | `rescue` |
| `start − 15min`, full | `confirmed` | **`ready`** | `ready` |
| `matchEnd` | `ready` | **`needsResult`** | same |
| `resultWindow` | `needsResult` | **`playedNoScore`** | same |
| `matchEnd + 24h` | card present | **card gone** | gone |
| `maxHoldAge` | `heldSoft` | `heldSoft` | **`heldStale`** |
| fit 90 | plain badge | **coral** | coral |
| warn raw 0.55 | **warning** | no warning | no warning |
| travel `dist` 20 / 38 | 1.0 / >0 | 1.0 / **0.0** | <1.0 / 0.0 |
| price `payable` 30 / 60 | 1.0 / >0 | 1.0 / **0.0** | <1.0 / 0.0 |
| overlap `|Δ|` 0.55 | >0 | **0.0** | 0.0 |
| forecast pct clamps | — | **35** and **96** | — |
| `fav` cap | — | **86** at gap 0.4966 | — |
| Player Score gate | 69 blocked | **70 allowed** | allowed |
| `PEAK` 17:00 | off-peak | **peak** | peak |

**The test matrix** [SRC: 3.1 §10.4] — every combination of: club window `24 · 12` × join
cutoff `30 · 20` × rebooking `true · false` × sport `doubles(n=4) · singles(n=2)` × seats paid
`1 · 2 · 3 · 4` × **every threshold hit exactly, plus ±1 min** × leave timing `before commit ·
after commit before rescue · after rescue · after check · after joinCut` × cascade outcome
`full-price · 50 % · consent accepted · consent declined · nobody`.
*"A generator that samples uniformly across the week misses `commit`, T−12h, T−4h, `check` and
`joinCut` — which is every branch point in the model."*

## J.4 Cross-system conformance tests

Every row of §G.3 as an executable equality between the two applications loaded in one process,
run in CI. The prototype's `conformance.js` currently asserts **40 rules, 0 disagreements** —
enumerate them individually rather than as a suite, because each is a specification of
correctness written by the author:

the nine canonical states in the same order · the hold ladder at every tier · singles has no
soft tier · a hand-commit beats everything · maximum hold age · demand-aware extension ·
`commit = min(window, 12h)` · rescue at 4 h doubles and 6 h singles · checkpoint at 2 h
universally · the invitation hold including the overnight rule · court prices per multiplier ·
`share = court ÷ players` · slot discounts landing identically · the four allocation policy
names · every request kind having a surface · no rating in the published policy · publishing
charging nobody · the ten intent fields in the same order.

## J.5 Property-based candidates

```
∀ m, now:  state(m, now) ∈ the 35                                  (no fall-through)
∀ m, now:  committed_now(m,now) ⇒ court_hold(m,now).kind == 'hard'
∀ m, t1<t2: committed_at after t2 is not None ⇒ it was not None after t1  (monotone)
∀ m, seq of clock scrubs forward then back: every derived value returns,
           EXCEPT committed_at and (currently) the four receipts        (see GAP-D3)
∀ m:       singles(m) ⇒ 'heldSoft' unreachable
∀ m:       terminal(m) ⇒ next_wake_at(m) is None, and conversely
∀ req:     identical request twice, same world ⇒ byte-identical feed
           (restated as: reproducible from (player, minute-bucket, seed) — see below)
∀ feed:    retrieved == excluded + scored          (the trace accounts for every candidate)
∀ m, now:  0 <= payable(m) and payable(m) <= share_after_disc(m)
∀ m:       n × share <= price
∀ scores:  fit ∈ [20,99] and |reasons| == 3
∀ two lanes: no match id appears in both
```

> **[GAP-J1 · doc 5 A4] The determinism invariant as written forbids exploration.**
> *"The same request twice, same world → byte-identical feed"*, demanded a thousand times over
> by the acceptance gate, conflicts with the ranker's need for exploration: *"a newly created
> match has little evidence, ranks low, gets no impressions, does not fill, and confirms its
> own score."* Both properties are wanted; they conflict only because the document treats
> determinism as **byte-identity** rather than **reproducibility**. **Proposal: restate as
> *reproducible from stored inputs* — the feed is a pure function of `(player, minute-bucket,
> exploration seed)`, and the seed ships in the `FeedTrace`.** Rounding `now` to the minute
> makes every score reproducible from its stored inputs and makes the result cacheable for a
> minute instead of never — from which the 60-second feed cache falls straight out.

## J.6 Chaos drills — run deliberately, on a schedule

Kill the timekeeper for an hour, restart, assert convergence · duplicate `EvaluateAt` · two
workers grabbing one match · concurrent leave + threshold, deliberately interleaved · drop
every third push, assert convergence within 20 s · rebuild the projection from records, assert
byte-identical · scrub the demo week forwards and backwards · kill the process mid-write (no
ghost event, no lost event) · **Atlantic Sports (window 12 h, so `commit` = T−12h exactly)** ·
**singles (n=2, no soft tier)** · **both checkpoint policies, including *nothing happens***.

---

# K. PORTING NOTES AND RISKS

## K.1 Prototype shortcuts that must not survive

| Shortcut | What it stands in for | Production must |
|---|---|---|
| **`matchState` calls `syncMatch`, so a read writes** | the command handler | `evaluate()` is pure and returns a `FactDelta`; only `apply()` writes, in one transaction with the outbox. A `GET /now` must not mutate a match |
| **`render()` calls `syncAll()` over every match** | the timekeeper | an indexed poll over `next_wake_at` every 2 s, `FOR UPDATE SKIP LOCKED`, plus a 5-minute sweep as the safety net |
| **`S.now` — a global mutable clock** | the real clock | `now` is a parameter, read **once** per command, passed to everything. This is also what makes scrubbing a test rather than a hack |
| **`S.matches` — an in-memory object mutated in place** | the aggregate store | rows with a `version` column and optimistic concurrency |
| **`lcg`/`h32` seeded `bookings()`** | the club's real calendar | read the club's published availability. The `_bk` memo is a process-local cache of another system's data |
| **`pickCourt` returns the first free court from a scan** | inventory allocation | a reservation on a Courts aggregate with `EXCLUDE USING gist (court_id, tstzrange)`. **This is the strongest argument for modelling Courts before Matches** |
| **`m.forced` and `buildGallery()`** | nothing — a demo gallery of all 35 states | delete. The `forced` escape hatch bypasses every guard, including `syncMatch` |
| **`m.demoEnd`/`demoCut`/`demoFar`/`demoNear` mutate `S.now` inside `matchState` and restore it** | a fixture clock | fixtures with an explicit `now` |
| **`REGULARS = ['kuba','ola']`** | *"people you have played with"* | a real familiarity signal. Doc 5 A1 notes the shipped engine makes **familiarity a term at weight 3**, not a modifier, *"precisely because a bonus outside the weighting has no meaning once weights renormalise"* |
| **`pref = 0.9`, hard-coded** | preference inference | a real term. Doc 4 §8.4 names this as one of exactly three places learning belongs |
| **`ST.formingHeld` hard-codes *"You invited Ewa at 19:41"* and *"held until 21:41"*** | `holdUntil` output | interpolate the real invitee and the real computed instant |
| **`ST.protectedBack`/`replacement` interpolate `PLAYERS[m.vacated].n`; `rescue`, `replacementTransfer`, `playedShort`, `cancelledCheckpoint` hard-code *"Ola"*** | the actual leaver | interpolate from `vacancies[]` |
| **`ST.confirmResult` hard-codes *"Kuba entered 6-4, 3-6, 6-2"*; `completed` hard-codes the score and *"+0,08 to 2,79"*** | the real result and the real rating movement | read from the result and the rating engine |
| **`ST.cancelledClub` hard-codes *"cancelled at 08:12 — standing water"*** | the club's reason | a reason code plus a free-text note |
| **`waitlisted` says *"you are 2nd on the standby list"*** | a computed position | **do not compute it.** See K.3 |
| **`stateCard` shows `CLUBS[club].court`, a sample string** | the category | show the category until `ready`, then the assigned court |
| **`CARD` — a hard-coded MultiSport banner (`used: 1, allowed: 2`)** | the entitlement engine | read real usage |
| **Every string in `ST` is English** | copy | **this is a Polish product.** Copy is per-client and per-locale; server-side copy makes every wording change a backend release |
| **`m.left` — a boolean on a shared match object** | per-player enrolment | move to the seat or an enrolment row |
| **`S.waitlists` — an array of match ids on the viewer** | a waitlist aggregate | a table with position semantics |

## K.2 Values displayed but never computed, or computed wrongly

- **`m7` reads `confirmedOnFill` in the seeded world.** Its `commit` (Wed 19:00) is already in
  the past at boot, so the **first** `syncMatch` writes `committedAt = S.now` rather than the
  instant the condition actually became true. The card then tells the player *"the deadline had
  already passed, so the final payment committed everybody at once"* — which is false; the
  match filled long before. **In production, `committedAt` must be written by the timekeeper at
  the crossing, not by whoever happens to read the record first.** This is the clearest
  illustration of why a read must not write.
- **Rescue priority** — the five factors and the score of 74 are **static in the interface**.
- **Merge takes the first compatible match**, not the best of several.
- **Standby targeting is described, not executed** — the pool's level range is never checked
  against the seat's target.
- **The stage interval is a timer, not a schedule** — the prototype advances after a fixed
  offset rather than waiting for a real decline or timeout. Production must be event-driven:
  accept, decline, or a hard timeout.
- **`fillLikely` was removed and replaced by published data**, which is correct — but a club
  with no fill model publishes nothing, and the app must fall back to the ladder **and say so**.

## K.3 The known limitations the sources admit, each with its production consequence

| Admitted limitation | Consequence |
|---|---|
| **Two players leaving simultaneously is not modelled** | the first leaver's refund position is silently lost; the group facet reports one vacancy while two exist |
| **The two prototypes do not share a backend** | a consent request the club creates and a player's acceptance are simulated independently. In the real system both are reads and writes against one state |
| **Preference expiry is not implemented** | a declaration from four months ago is treated like one from yesterday |
| **Observed patterns read only one club's matches**, by deliberate privacy choice | familiarity and reliability signals are partial at launch |
| **The wallet is stored value** | e-money in several jurisdictions above a threshold; caps, expiry and refundability need a legal answer per market |
| **Soft-hold max age (Rule 11) and club extension (Rule 12) are specified, not implemented** | and as written they contradict — Rule 11 shortens a hold the ladder would have kept, Rule 12 says the ladder is a floor. **The coherent reading: Rule 12 constrains the ladder's thresholds (a club cannot release earlier than T−12h or T−4h); Rule 11 caps how long a single hold may sit before being re-derived, an operational limit, not a marketplace promise. Rule 11's cap must never release a court before the ladder's own threshold, and that ordering needs a test** |
| **The standby position is a precise number for an unobserved event** | *"computed against a vacancy that has not happened, ranks on level fit against a seat that does not exist yet, and can move without anybody doing anything wrong."* A number that is precise, prominent and free to change for reasons the player cannot see is *"a fabricated observation wearing the clothes of a measurement."* **Proposal: state the pool — *"you and five others are on standby"* — or say only what is certain, which the next line already does well: *"if a seat frees the top candidates are told at the same moment."*** |
| **Parts 2–3 of the Now spec are CSS for an HTML prototype** | the target is Expo with a locked design system; `scroll-snap-type`, `::-webkit-scrollbar`, `border-radius: 34px` on a 392×788 frame and `@media (prefers-reduced-motion)` do not exist there. Keep the **intent** — the colour semantics, the two-family type rule, the elevation refusal, the seven accessibility requirements — and re-express the values against the theme. The rule worth carrying verbatim: **a colour used for two things is a colour that means nothing** |

## K.4 Risks ranked by what they cost

| # | Risk | Cost if wrong |
|---|---|---|
| 1 | **Two matches take the same court** (no `(court, slot)` constraint) | `inventoryLost` is terminal and refunds everybody — not a display bug |
| 2 | **The four terminal flags are read, not derived** [GAP-D3] | a downed writer makes a read *wrong* in the reassuring direction, on exactly the four transitions the product exists to be trusted about |
| 3 | **No leaver card** [GAP-D2] | the card vanishes at the moment the player has an open question about money, and their outcome is one of four |
| 4 | **Two simultaneous leaves overwrite** | a lost refund position, silently |
| 5 | **`start` is mutable but the sort key assumes it is not** [GAP-F1] | patch-not-list is unsound after a consented shift; the strip reorders without announcing it |
| 6 | **Feed sort is not total** | the list reshuffles between identical requests — *"that looks broken and it is broken"* |
| 7 | **Fit is monotonically decreasing in information** [SUPERSEDED-A1] | the highest scores belong to the matches the platform knows least about, and Now paints a coral badge on them |
| 8 | **Rung 5 above rung 6** [GAP-E1] | a waitlisted player is asked for the score of a match they did not play |
| 9 | **Rung 9 unreachable** [GAP-E2] | two states never render; a recovered match would pin in a recovery state once it can |
| 10 | **`tone: 'bad'` is not in the tone enum** [GAP-E3] | the one state naming the product's only real risk renders with no colour |
| 11 | **Two sources of truth for the checkpoint policy** [GAP-C3] | a match cancelled that should have lived, or kept alive that should have been credited — money in both directions |
| 12 | **Money as float** [GAP-D6] | grosze drift; `n` is only ever 2 or 4 today, which is luck, not design |

## K.5 Build order, from the sources, reconciled

1. **The Matches aggregate ADR** — settle event-sourced versus persisted-with-events, and
   resolve §B.2's three kinds of stored fact while you are in it.
2. **Courts and the hold, before the match lifecycle** — risk 1 is unsolvable at the match
   layer, and `inventoryLost` is terminal.
3. **The derivation kernel as a pure module** — the ladder, the twelve hold rules, the seven
   commitment rules and `nextWakeAt`, taking `now` as an input, tested by scrubbing a demo week
   forwards and backwards. *"The cheapest and highest-value piece, and it needs nothing else to
   exist."*
4. **Command handler and timekeeper on the existing worker** — one writer, optimistic
   concurrency, deterministic idempotency key, `next_wake_at` as a column.
5. **The feed, pull-only** — no new infrastructure; the funnel, the lanes and the two engines.
   Shippable today against hand-built snapshots.
6. **Now, read-only over both** — the strip and the two lanes, refreshed on open and on pull.
   Correct, if not yet alive.
7. **Delivery last** — WebSockets, patches, the heartbeat. Everything above works without it,
   which is the whole point of *the push is an optimisation; the read is the truth* and the
   best reason to defer it.

---

# SELF-CHECK

1. **Late reassignment:** searched every name in the call graph for later assignment; found and
   documented five (`deadlines`, `courtHold`, `matchState`, `payable`, `freshState` ×2, plus
   `render`), specified the final composed behaviour for each, and gave a worked example
   (D.6 D10) where base and composed disagree — 12 ladder rungs, not 10; 35 states, not 33.
2. **Constants:** every threshold, weight, cap, floor, multiplier, rate table and embedded
   magic number is in §C with value, unit and owner, including ones inside expressions
   (`0.55`, `18`, `30/30`, `145`, `32`, `72.5`, `86`, `0.45/0.55`, `1e-9`, `60_000`).
3. **Re-implementable digit for digit:** yes for everything with a D10 — all worked examples
   were executed against the prototype's own engine, not hand-computed, and intermediate values
   are printed to six decimals.
4. **Inclusive/exclusive:** stated for every threshold in D5/D6 of each engine and tabulated in
   §J.3. The two that decide behaviour are the hold ladder's `left > 4`/`left > 12`
   (**exclusive** — the hold lapses *at* the boundary) and `committedAt > commit + 60s`
   (**exclusive** — at exactly +60 s it is `confirmed`, not `confirmedOnFill`).
5. **Stored vs derived:** every field in §B.1 is marked S/D/A/R, and §B.2 separates allocations
   from irreversible crossings from side-effect receipts. `holdKind` is called out as a stored
   copy of a derived value with zero readers.
6. **Gaps, and which risk money or state:** twelve marked. The money-and-state ones are
   **GAP-D3** (terminal flags read rather than derived — a downed writer lies reassuringly),
   **GAP-D2** (no leaver card at the moment the refund is unresolved), **GAP-C3** (two sources
   of truth for the checkpoint policy — cancels or fails to cancel), **GAP-D6** (float money),
   **GAP-F1** (`start` mutable under a sort key assumed immutable), and the unhandled double
   leave. The remainder — **GAP-0, C1, C2, C4, D1, D4, D5, D7–D12, E1, E2, E3, I1, J1** —
   affect correctness of display, ranking or reachability rather than money directly.
