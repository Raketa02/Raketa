# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. All three
apps obey this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Raketa is a racket-sport platform. Today it does one thing end to end: a player signs up,
signs in, and answers a questionnaire that gives them a **Skill rating** per sport. That is
served by the **player app** and one **backend** built on Clean Architecture (hexagonal
ports & adapters), DDD, and event sourcing.

> This is a living document, grown deliberately. Terms are added as decisions are
> actually resolved — not invented ahead of the code. Don't drift to synonyms it avoids.
>
> **It was cut back on 2026-08-25.** The repository was reset to the finished features, and
> every term that named removed code went with it — the club console, the pairing and Match
> Fit engines, the kernel's money module, and the whole planned-context list (Clubs, Courts,
> Bookings, Matches, Money, Now). What remains is what the code actually says. See the
> [ADR index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps) for why
> the ADR numbers have gaps. Naming something new in the racket-sport domain is now an open
> question again, not a lookup: read [`docs/agents/domain.md`](docs/agents/domain.md) first.

---

## Part 1 — Implemented bounded contexts

These are the authority for their terms. There is no Part 2: after the reset, no term is
committed ahead of *a decision*, and a speculative list of context names is not one. A
context that does not appear below has no vocabulary yet — resolve its terms into this file
before writing it, which is what the last three sections below are: **Player profile** is
settled in an accepted ADR and is being built, and **Blocks** and **Matchmaking** are settled
in accepted ADRs and are not built at all. Their terms are here because that is the order
this file asks for, not because the code landed first. **Player Score** is a further step out
again: nothing about it is decided, and it appears only because the matcher has contracted six
words it will read, and the words are the player's, not the matcher's. Every other section describes code
that exists in `backend/app/` today.

### Skill rating (`backend/app/modules/rating/`)

What the platform believes about how well a player plays one sport, and how sure it is.
A rating is **never only a number**.

- **Skill rating** — an **event-sourced aggregate**, one per (player, sport).
- **Level (μ)** — the current best estimate on a fixed **1,0–5,0** scale. Public. **5,0 does
  not mean professional**; it means at or above the top of the competitive amateur
  population this marketplace exists to match.
- **Uncertainty (σ)** — how unsure the platform is. **Skill and certainty are separate
  variables**: two players both showing 3,0, at ±0,15 and ±0,90, are not the same player,
  and matchmaking reads the record rather than the headline.
- **Confidence** — σ restated as a percentage for the player, `100 × (1 − σ/1,20)`, capped
  at 99. **Never 100** — the platform cannot claim total certainty about anybody.
- **Likely range** — μ ± σ, clamped to the scale. The player's own range, and the only
  range shown to them; a band's numeric edges are not a second range to compare it against.
- **Band** — one of four named ranges, deliberately uneven in width, each with a
  plain-language meaning: **New** 1,0–1,5 · **Developing** 1,6–2,6 · **Established**
  2,7–3,8 · **Advanced** 3,9–5,0.
- **Rating status** — **Initial Estimate** (onboarding output, no counted matches) →
  **Calibrating** (real matches started, still moving) → **Stable**.
- **At stake** — what a counted win and a counted loss against one specific opponent would do
  to a player's Level, shown before they commit to the game. A **pair** of signed deltas, and a
  fact **this context owns**: it reads the rating engine's own update rule, so nobody else may
  compute it — not the client ([ADR-0021](docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md):
  a rule, not a comparison), and not the matcher, which reads what a player is shown and never
  re-derives it. It exists only for games that would be counted. **The rule it needs is not
  written yet**, so today the value is *absent* rather than zero.
- **Volatility** — how fast the estimate currently appears to be moving.
- **Assessment** — an **event-sourced aggregate**: one adaptive questionnaire run, for one
  player and one sport.
- **Transcript** — the answers a run has given, in order, each as a question and the option
  chosen for it. It is what the engine reads and the *only* thing it reads: given the same
  transcript the engine always returns the same next question and the same rating. It is a
  **projection over the assessment's stream**, not a second record beside it, which is why a
  run resumed on a fresh install or a second handset still has all of it.
- **Revision** — changing an answer already given. It **truncates** the transcript at that
  question: every answer after it is discarded, because each was pitched at a difficulty
  chosen from the estimate as it then stood, so an answer that outlived a change to an
  earlier one would mean something the player never said. Re-selecting the option already
  recorded is not a revision and changes nothing.
- **Stop** — the moment the engine judges that no remaining question would meaningfully
  tighten the estimate. The questionnaire ends there and *nothing is rated*: the run sits
  in progress with nothing outstanding, and every answer stays revisable. A stop is a fact
  about the transcript rather than a state anything records, so it is asked of the engine
  and never stored.
- **Completion** — the separate, explicit act that ends an assessment and brings its Skill
  rating into existence. This is the irreversible moment, and the only one — which is what
  lets a player see every answer laid out, still changeable, before it becomes a number.
  Stopping and completing are deliberately two moments and not one.
- **Claim** / **demonstration** — every answer is one or the other. A claim is a statement
  about standing (how often you play, what you compete in, how you do against your usual
  group). A demonstration is a statement about what you do inside a point.
- **Contradiction** — a gap beyond tolerance between fused claims and fused demonstrations.
  *"I regularly compete in strong club matches"* against *"I almost never maintain a basic
  rally"* is one. A strong smash and a weak backhand is not — that is an **uneven profile**,
  and it widens the range without being called a contradiction.
- **Layoff** — declared time away from the sport, asked only of players with a history.
- **Evidence trail** — the account a rating gives of itself: what the platform concluded
  and why. It has two halves and they are deliberately kept apart, because they answer
  different questions. **What moved the level** — each kind of evidence the player gave,
  fused on its own, and where that sits relative to the estimate they were given. **What
  widened the range** — a layoff, a contradiction, an uneven profile, each reporting how
  much uncertainty it actually added. Something that widened the range did not move the
  level, and saying otherwise would describe a different rating than the one produced.
- **Calibration priority** — how urgently a rating wants real matches to settle it. Raised
  when the assessment ended on evidence the questionnaire could not resolve. It is a
  statement about the *estimate*, never about the player, and it changes who they are
  matched with, never where they sit.

**Invariants**
- **A level is proved, never declared.** Not by the player, not by staff, not by a club.
  Manual editing is refused by the domain itself, not guarded by a permission check.
- **Only the rating context writes μ, σ, volatility and status.** Every other engine
  contributes evidence, an information weight, or an anomaly signal — never a rating point.
- **Absence widens, it never lowers.** Layoff and inactivity add to σ and never touch μ. A
  player who was 3,20 two years ago has no obligation to still be 3,20 — and no obligation
  to have got worse. The honest position is *we are less sure*, not *we assume decline*.
- **A contradiction is never resolved by picking a side.** It widens the range and raises
  calibration priority; it never moves the player up or down, and it never accuses them.
  Resolution has no direction, which is what stops under-reporting being profitable.
- **Onboarding cannot produce confidence above 30%.** The questionnaire is the entire
  evidence surface and self-report has an irreducible ceiling, enforced as a floor on σ
  rather than as a display cap. Everyone leaves onboarding as an *Initial Estimate*.
- **A rating explains itself, and the explanation is computed, never authored.** Which way
  a kind of evidence pulled is decided by comparing it against the estimate, and which
  reason is given for the confidence is decided by whichever thing widened the range most.
  Nobody writes down that standing pulled a player up; the arithmetic says so, or it does
  not. Retuning a constant therefore moves the explanation with it, and an explanation
  cannot quietly drift out of step with the number it explains.
- **A rating carries the engine version that produced it.** Every constant in the engine is
  a hypothesis with a measurement that would falsify it — and you cannot falsify one you
  cannot attribute a rating back to.
- **A revision shortens the past; it never edits it.** The change is *appended* to the
  stream and nothing is deleted, so what a player answered first, and what they changed it
  to, are both permanently recoverable. Only the transcript — the projection — gets shorter.
  A player changing their mind is data to learn from rather than a gap
  ([ADR-0020](docs/adr/0020-revisable-assessment-answers.md)).
- **An answer is revisable for as long as its run is, and no longer.** Once a run has
  produced a Skill rating, its answers are settled: the account of a player stops moving at
  the moment the platform starts relying on it. This is the same invariant as *a level is
  proved, never declared*, read from the other end.
- **The questionnaire stopping is not the rating existing.** Stopping is the engine having
  heard enough; completion is a separate act that a player performs, and only completion
  creates a rating. Nothing that ends the questioning — the last answer, or a revision that
  reaches the beginner fast path — may create one as a side effect, because a player must
  be able to see what they said before it becomes a number.
- **There is no *onboarded player*.** Onboarding is not a state a player is in or out of;
  it is how a Skill rating comes to exist, and a rating is per sport. A player can be rated
  at padel and unrated at tennis at the same moment, indefinitely. Anything that needs to
  know "has this player been through onboarding" is really asking "does a rating exist for
  this sport", and must ask it that way — a per-player onboarding flag would be a second,
  coarser truth about the same fact.

  **What this bans is a per-player flag standing in for a per-sport fact** — not per-player
  facts as such. The test is the sentence above: *is this really asking whether a rating
  exists for this sport?* Where the answer is yes, ask it that way. Where the answer is no,
  the fact is genuinely the player's and belongs on the player. A **Player profile** is the
  first thing to return no — tags, photos, a week, a location and a consent are facts about
  a person and have no sport dimension at all — so *does a Player profile exist* is a
  legitimate per-player question, and onboarding's second part is checkpointed on it
  ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Everything the invariant
  was written about stands unchanged.

### Users (`backend/app/modules/users/`)

Identity and account state.

- **User** — **event-sourced aggregate**: its state is rebuilt from a stream of domain
  events. Constructed only via `User.register(...)` or rehydrated via
  `User.from_history(events)`. Carries an `EventRecorder`; the application layer drains
  pending events with `pull_events()`.
- **Player** — a User acting in the player app. **Not a separate aggregate and not a
  separate id**: a player's identity *is* the `UserId`. `PlayerId` exists as a distinct
  type so the code reads in the domain's own vocabulary and so the two have one place to
  diverge, but today every `PlayerId` is a `UserId`. There is no `players` table.
  Revisit only if a person can be known to the system as a participant without holding an
  account, or if club staff share this accounts system — neither is true today.
- **Authority** — role enum, `USER` or `ADMIN`.
- **Email** — value object. Trimmed, lower-cased, RFC-ish validated, ≤ 320 chars.
- **Nickname** — value object. Trimmed, 2–64 chars, `[A-Za-z0-9_.-]`.
- **RawPassword** — the plaintext at the boundary; 8–128 chars with ≥1 letter and ≥1
  digit. Carrying it as a type is what prevents hashing an unchecked string.
- **HashedPassword** — non-empty bcrypt hash; the only password form ever persisted.
- **User events** (durable name / version):
  - **UserRegistered** — `users.user_registered` / v1 — first event of every stream.
  - **UserDisabled** — `users.user_disabled` / v1.
  - **UserPromotedToAdmin** — `users.user_promoted_to_admin` / v1.

**Invariants**
- Email and nickname are **unique** — `RegisterUser` reads both before insert and
  raises `EmailAlreadyRegistered` / `NicknameAlreadyTaken` (a domain conflict, not a
  database constraint violation).
- **`disable()` is idempotent** — a no-op on an already-inactive user.
- **An inactive user cannot be promoted** — raises `InactiveUserCannotBePromoted`.
- `promote_to_admin()` is a no-op if already `ADMIN`.

### Auth (`backend/app/modules/auth/`)

Authentication and session lifecycle.

- **RefreshToken** — a **persisted entity that emits events** (not event-sourced).
  Stores the bcrypt `token_hash` and `jti` — **never the plaintext** —
  plus `refresh_expires_at`, `is_valid`, `revoked_at`.
- **Access token** — short-lived JWT for API calls (`ACCESS_TOKEN_EXPIRE_SECONDS`).
- **Refresh token** — longer-lived, **rotating** credential
  (`REFRESH_TOKEN_EXPIRE_SECONDS`).
- **Rotation** — on refresh the old token is revoked and a new one issued atomically
  (`RefreshToken.rotate_to(...)`); reusing a rotated token is rejected (replay
  protection).
- **TokenService** — port for signing/decoding JWTs (`JwtTokenService` adapter).
- **PasswordHasher** — port for bcrypt hashing (`BcryptPasswordHasher` adapter).
- **Auth events** (durable name / version):
  - **RefreshTokenIssued** — `auth.refresh_token_issued` / v1.
  - **RefreshTokenRevoked** — `auth.refresh_token_revoked` / v1.
  - **RefreshTokenRotated** — `auth.refresh_token_rotated` / v1.

**Invariants**
- **Logout is idempotent** and never reveals whether a token existed.
- `revoke()` / `rotate_to()` are no-ops on an already-invalid token.
- Login returns **the same error** for unknown-email and wrong-password
  (`InvalidCredentials`) — no account enumeration.

### Shared kernel (`backend/app/kernel/`)

The dependency-free ring that every bounded context and every engine reads verbatim and
none may redefine ([ADR-0015](docs/adr/0015-engines-as-a-pure-versioned-layer.md)).

- **Sport** — a **closed enum** of exactly four values: `PADEL`, `TENNIS`, `SQUASH`,
  `BADMINTON`. Adding a sport is a code change and a release, never a row. A club's sport
  list *filters* this registry and never extends or overrides it.
- **SportSpec** — the frozen per-sport facts: `players` (how many the sport is played for)
  and `durations` (the bookable lengths in minutes). Served read-only over the player API at
  `GET /api/v1/sports` so neither client hardcodes it.
- **There is no `Format`.** One rating per sport, one question bank per sport, worded for how
  that sport is actually played — padel and badminton as doubles, tennis and squash as
  singles. *Padel singles* and *tennis doubles* are not terms in this system.

| Sport | players | durations (min) |
| --- | --- | --- |
| PADEL | 4 | 60 / 90 / 120 |
| TENNIS | 2 | 60 / 90 |
| SQUASH | 2 | 45 / 60 / 90 |
| BADMINTON | 4 | 60 / 90 |

**Invariants**
- **A sport's player count is never club-configurable.** No field on any club or court may
  override it; the value is read from exactly one place, everywhere. A club cannot sell a
  two-player padel match because the registry forbids it structurally, not by convention.
- **Reintroducing `Format` would be a new decision, not a gap someone should fill in.**
  Its absence is deliberate and load-bearing: one rating per sport is what let onboarding
  drop cross-sport transfer and the singles/doubles link entirely.

### Player profile (`backend/app/modules/player_profile/`)

Everything a matchmaker needs about a player that a questionnaire cannot infer. Decided by
[ADR-0089](docs/adr/0089-player-profile-context-event-sourced.md); the terms are here ahead
of the code because this file asks for them in that order.

- **Player profile** — an **event-sourced aggregate**, one per player. **The first
  aggregate in the racket-sport domain that is not per sport**: skill is per sport, but
  tags, photos, a week, a location and a consent are facts about a person.
- **Social tag** — one of a **fixed, closed vocabulary** the platform owns, in three groups
  about the game: how a player is *after the match*, what they are like *on the court*, and
  *why they are here*. A player holds **2 to 6**. Never free text, never player-authored,
  never imported from another platform, and never about the person rather than the game —
  age, looks, body and "looking for" are a different product's vocabulary.
- **Availability grid** — a player's ordinary week as **7 days × 3 parts of the day**,
  Monday-first. It is the *only* way time preference is ever expressed, and it is a
  **preference, not a promise** — a ticked slot is never a commitment, a hold, or a bookable
  time.
- **Availability slot** — one cell of the grid: a day and one of **morning**, **afternoon**,
  **evening**. The finest precision the platform holds about when a player wants to play.
- **Availability overlap** — how much of a player's own declared week another player covers.
  Deliberately **asymmetric**: the denominator is *your* slots, because the question it
  answers is *how much of my week does this person cover*.
- **Window** — the coarse shape of a searcher's declared week, as one of `TODAY`, `TOMORROW`,
  `WEEKEND`, `THIS_WEEK`, `ANY`. **Derived from the grid, never chosen** — there is no picker,
  because a picked window is a second availability declaration free to contradict the one the
  whole engine just matched on. It is derived from *the grid the search actually ran on*, so a
  widened search can carry a different window from the profile. It is what the person answering
  a challenge is told they are agreeing to; it is **not a proposed time**, and the players agree
  the hour themselves ([ADR-0100](docs/adr/0100-challenge-window-derived-never-chosen.md)).
- **Location area** — where a player plays, held coarsely. The precise fix that produced it
  is never a shareable value.
- **Search radius** — the distance around a player's Location area within which they want to
  find other players. **A filter when the player searches, and a weight when the engine
  proposes** — the same number answering two questions, because who *you* asked to see and
  who the platform *offers* you are different acts.
- **Proposals opt-in** — the player's recorded answer to whether the recommendation engine
  may push games at them. It has **no default**: unanswered is neither yes nor no.
- **Gender** — `WOMAN`, `MAN` or `PREFER_NOT_TO_SAY`, held on the Player profile. **Per
  person, never per sport**, self-declared and freely changed. It is a statement about **which
  searches a player wishes to appear in**, not a ruling by the platform on who anybody is:
  `PREFER_NOT_TO_SAY` matches an unconstrained search only, and is an explicit answer rather
  than a null — the same shape as Play intent's `NO_PREFERENCE`. Required at profile creation.
  **Never rendered on a card and never carried by a response**
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **Gender preference** — who a player is willing to be matched with: `WOMEN_ONLY`, `MEN_ONLY`
  or `ANY`. Durable, optional, defaulting to `ANY`. **Mutual, never one-directional** — it
  governs both what a player sees and whether they can be seen, so it protects an inbox and not
  only a search. A **gate, never a weight, and never relaxed**. A search may narrow it for that
  search and may never widen it past another player's.
- **Play intent** — what kind of game a player wants in **one sport**: `COMPETITIVE`,
  `FOR_FUN` or `NO_PREFERENCE`. **Declared, per sport, and never inferred.** `NO_PREFERENCE`
  is an explicit answer and never a null — *either suits me* and *I never opened that screen*
  are different facts. Declared at the tail of every rating run that produced a rating, and
  changed from the search screen rather than a settings screen
  ([ADR-0094](docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)).
- **Play intent declaration** — the **event-sourced aggregate** that holds one, one stream per
  `(player, sport)`. Separate from the Player profile, which stays free of a sport dimension.
- **Mode** — the *search's* setting: which of **Competitive** or **For fun** a player is
  searching in **right now**. Two values, never three; a player with no preference still picks
  a tab for tonight. *Defined here because Play intent cannot be defined without it; it belongs
  to the matchmaking context and moves there when that context is written.*
- **Intent alignment** — what a searcher's live **Mode** is worth against a candidate's
  declared **Play intent**. Deliberately **asymmetric**: a social player in a competitive game
  is mildly bored, a competitive player in a game where nobody keeps score has been cheated of
  the only thing they came for. A **weight, never a gate** — and the one term that is never
  relaxed when the pool is thin.
- **Profile photo** — the first of a player's photos, and the one a player card shows. A
  player may hold up to three or none; none is not an absence but a **generated court
  poster**, derived from their identity so it is stable across devices.
- **Profile commit** — the single idempotent request that ends onboarding's second part,
  carrying all six answers at once. Nothing is written before it, so leaving mid-part
  restarts at step 1 ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Keyed
  by a client-supplied **idempotency key**, which the creating event carries so a retry is
  recognised from the stream itself rather than from a table beside it.
- **Player profile events** (durable name / version):
  - **PlayerProfileCreated** — `player_profile.created` / v1 — the commit, carrying every
    preference and the idempotency key. **Not the opt-in.**
  - **SocialTagsChanged** — `player_profile.social_tags_changed` / v1.
  - **PhotosChanged** — `player_profile.photos_changed` / v1.
  - **AvailabilityChanged** — `player_profile.availability_changed` / v1.
  - **LocationChanged** — `player_profile.location_changed` / v1.
  - **SearchRadiusChanged** — `player_profile.search_radius_changed` / v1.
  - **ProposalsOptInAnswered** — `player_profile.proposals_opt_in_answered` / v1 — the
    answer, the copy version shown and the surface; the moment is the event's own.
  - **PlayIntentDeclared** — `player_profile.play_intent_declared` / v1 — the sport, the value
    and the surface it was declared on. Obeys the preference rule, not the consent rule.

**Invariants**
- **A tag id is permanent.** Ids are persisted on accounts, so retiring a tag means hiding
  it from the picker while continuing to honour it — never reusing or renaming it.
- **At least one slot, and blank is absent rather than zero.** The availability grid is
  **required** at profile commit — one ticked cell of the twenty-one is a real answer, none is
  not an answer at all. Where a blank grid is nevertheless met — cleared afterwards, or
  committed before the rule — it means *we do not know*, and the availability term stands down;
  it is never scored as no overlap and never as any time
  ([ADR-0102](docs/adr/0102-silence-is-never-scored.md)). **An unanswered field is never a
  negative filter**, and requiring the field is how that invariant is kept rather than
  weighed.
- **The grid is never shown to anybody as a calendar.** Not to matched players, not as
  free/busy, not exported. Only the *count* of shared slots and the name of the next shared
  one are ever rendered — overlap is a fact about a pair, a calendar is a fact about a
  person.
- **Skipping is not consent.** The proposals opt-in is never pre-answered, and no other act
  in the product may be read as answering it — not a timeout, not a backgrounded app, not
  progress through any other step.
- **Opting out stops the engine pushing, not the player existing.** A player who declines
  receives no engine-generated proposals. They remain findable: search and matchmaking are
  unaffected, and they keep every other part of the product. Over-applying the flag makes a
  ghost account; under-applying it is a consent violation.
- **Consent is evidenced, not asserted.** Every answer is recorded with the moment it was
  given and **the exact copy the player was shown**, because consent gathered against one
  sentence is not consent to a different one. It is as revocable as it was grantable.
- **Every consent answer is recorded, re-affirmations included.** The five preferences
  record nothing when set to what they already hold; the opt-in always records. *Asked
  again, against these words, and said yes again* is a fact about consent, and a log that
  collapses it cannot say which wording a standing yes was given against. This is also why
  the creating commit appends the opt-in as its own event rather than folding it into
  `PlayerProfileCreated`: the consent history is one sequence with no special first case.
- **A location is held coarsely, and the precise fix is never stored.** The coarsening
  happens on the way in, before an event is recorded, so there is no version of a profile's
  stream from which a device's own reading could be recovered — the same argument
  [ADR-0091](docs/adr/0091-photo-storage-behind-a-port.md) makes for re-encoding a photo
  rather than scrubbing its EXIF.
- **A level is proved; a preference may be declared.** The founding rule bans a self-declared
  *level*, and the reason is that misdeclaring one **pays** — a sandbagger farms wins against
  people promised a fair game, so the declaration harms someone else. Play intent has no true
  answer to check it against and misdeclaring it costs only the declarer an evening. That
  distinction is owed to the player **in the interface**, on the intent step and wherever the
  app refuses a self-declared level, not only in an ADR.
- **A tag is not an intent.** `HERE_TO_COMPETE` is *why you are here at all*; Play intent is
  *what tonight's game is*. Somebody tagged `HERE_TO_COMPETE` who declared `FOR_FUN` wants a
  hard-fought friendly, and nothing may quietly overrule them. Reading tags as intent would
  also count the same six strings in three different terms.
- **Behaviour never rewrites a declaration.** Searches that disagree with a declared intent
  raise a **prompt** and nothing else; the matcher never reads the disagreement and never
  writes the value. The platform watches, notices, and deliberately declines to act.
- **Intent is per sport, and never transfers between them.** The same person is plausibly a
  competitive padel player and a social tennis player — the same reason levels do not transfer.
- **A profile is one per player, and asking whether one exists is a legitimate question.**
  See the narrowed *there is no onboarded player* invariant above, and
  [ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md).

### Blocks (`backend/app/modules/blocks/`)

One player deciding they do not want to be shown another, ever again. Settled by
[ADR-0095](docs/adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md); not
yet built.

- **Block** — an **event-sourced aggregate**, one stream per **ordered** `(blocker, blocked)`
  pair, with a deterministic stream id derived from that pair. **The record is directed; the
  effect is symmetric.** `A → B` and `B → A` are two independent blocks, so one being lifted
  never lifts the other.
- **Blocker** / **blocked** — the two sides of the ordered pair. The words name the *record*,
  never an experience: neither party can discover which way it went.
- **Block events** (durable name / version):
  - **PlayerBlocked** — `blocks.player_blocked` / v1 — the pair and the surface it was made
    from. **No reason, and no free text.**
  - **PlayerUnblocked** — `blocks.player_unblocked` / v1 — the pair.
- **BlockQuery** — the port that answers *is either of these two blocked by the other*. One
  port, consulted by every surface that shows one player to another.
- **Hold** — the platform stopping a player from starting anything new while an unsettled case
  is open against them. A **held account** is an account under a Hold. Nothing can place one
  today, because the `cases` context does not exist.
- **AccountHoldQuery** — the port the Hold gate reads. Its only adapter today is
  **`NoHoldsExist`**, named for the fact it asserts rather than for being empty.
- **Report** — *not a term yet.* The wider reporting and moderation story is out of scope; if a
  reason for a block is ever wanted, it belongs to a Report and not to a Block.

**Invariants**
- **A block works both ways, immediately and silently.** Each disappears from the other's view
  on every surface where the platform shows one player to another. Neither is notified, and no
  response shape can carry a block or a decline — asserted by a test, not by review.
- **A block is forward-looking.** It removes each from the other's *future* proposals and
  listings. It does not reach into a game already agreed or a chat already open; what it does
  to an open challenge is a demand on the unbuilt `matches` context, not a decision this
  context makes.
- **Blocking is idempotent, and blocking yourself is an error.** A second block appends
  nothing, in the shape of `disable()`; a self-block raises rather than no-ops.
- **No cap, no cooldown, no rate limit.** Friction on the one control a person has is a tax
  paid to solve a problem the platform does not have.
- **Erasure reaches both sides.** Erasing a player erases every stream they appear in, on
  either side of the pair — which is why a block is never a field on somebody's profile.

### Matchmaking (`backend/app/modules/matchmaking/`)

Decided by [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md);
not yet built, and its vocabulary is still being resolved on the matchmaking map. Only what a
decision has actually settled appears here.

- **Gate** — a hard exclusion applied before anything is scored. Not a weight, and no
  relaxation ever reaches one.
- **NoEvidence** — what a term returns when it has nothing to weigh. It is dropped from the sum
  and the remaining weights renormalise; it is never `0`, and never a neutral `0.5`.
- **Quality floor** — the Fit below which a candidate is not shown at all. A **fixed** bar: no
  relaxation reaches it, and nothing lowers it in response to a thin pool
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)). One floor for both
  modes and every sport, and it is defined by the **judged pairings** it must satisfy rather
  than by a chosen number.
- **Minimum shortlist** — how short a shortlist has to be before the response carries the
  relaxation rungs at all. It triggers nothing by itself; the engine still never widens on its
  own.
- **Reliability floor** — a flat dock, printed with its reason, on a candidate whose **published
  Player Score** is below the bar. Not part of the modifier budget and larger than all of it, so
  a stack of small positives can never erase a recent no-show. It is a **dock and not an
  exclusion**: an otherwise excellent match still appears, low, with the reason shown — where a
  player wants somebody gone entirely, that is a Block. The one place the matcher reads the
  blended score instead of the six strands, because it is the number the player can see.
- **Minimum evidence** — the least the engine must know about *one specific candidate* before
  showing them to anybody. A **gate**, never an adjustment to their score, and a fraction of the
  terms live for the platform rather than a count. It reads gaps particular to that person and
  never platform-wide absence, so a term nobody has yet gates nobody.
- **Relaxation rung** — an **offer** to relax one of the searcher's *own* asks — their times, or
  their radius — with the real count of candidates it would add. Three exist, times first. The
  player accepts; the engine never relaxes anything by itself, and an accepted widen is scoped to
  that one search ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **Pool description** — what the response carries when the shortlist is empty: how many players
  of that sport are in range, structured, **counted after every gate**. It is the product in a
  new market, and it is a number on a screen, so it counts real rows and never estimates.
- **Guaranteed inclusion** — a candidate placed in the shortlist by something other than Fit. An
  **interest lift** — a human's own *Let's play* — may sit below the quality floor with its
  reason printed. The newcomer-window and zero-exposure lifts may **reorder** and never
  **admit** below it.
- **SearchContext** — the facts about *the searcher* that travel with one search rather than
  living in the index: their block set, and their pairwise history. The index row is per player,
  so a fact about a **pair** has nowhere else to be
  ([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md)).
- **Pairwise history** — what happened between the searcher and one other player: **accepted**,
  **declined**, **played**, **planned-never-played**. Four outcomes the matcher keeps distinct,
  because a pair who ghosted each other is not a pair who played.
- **Origin key** — the `(search_id, position)` a challenge was sent from, carried by the
  challenge itself. Required, never optional: a search not joined to its outcome is evidence
  that no longer exists, and there is no backfill.
- **PlayerScoreQuery** / **MatchHistoryQuery** — the two ports naming what the matcher demands of
  `player_score` and `matches`, beside **AccountHoldQuery** for `cases` and **AtStakeQuery** for
  `rating`. One provider signs one contract. Their only adapters today are
  **`NoPlayerScoresExist`**, **`NoMatchHistoryExists`** and **`NoResultUpdateRuleExists`**, named
  for the facts they assert
  ([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md)). `AtStakeQuery` is the
  odd one out: its provider **exists** and the rule it needs does not.

**Terms this context refuses**
- **Game format** — *mixed doubles*, *women's doubles* and the like. Deliberately does not
  exist. A search carries a **Sport** and never a format; the sport fixes the seat count
  (`backend/app/kernel/sports.py`, which refuses a `Format` dimension for the same reason). Who
  may sit in a seat is answered by **Gender preference**, which is about people and says so
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).

**Invariants**
- **A term that cannot be evaluated stands down. A gate that cannot be evaluated excludes.**
  Absent evidence makes a term renounce its weight and the rest renormalise; absent evidence
  makes a gate *fail closed*. An absent gate is an open door, never a standing-down signal.
- **A safety gate is verified against live state, on the side that owns the truth.** The
  matcher proposes and the backend disposes: anything failing live verification is dropped from
  the answer before it reaches the client, and the shortlist is simply short by one.
- **A gate may be honestly empty; a term may never be honestly neutral.** The test for a fact
  whose context does not exist yet is whether a zero would be *measured* or *invented*. No
  challenge has ever been sent by anyone, so an open-challenge count of zero is real and the
  gate ships live and true-over-empty. Nobody has failed to turn up, because nobody has ever
  been due to — so a reliability strand of zero would be invented, and the term stands down
  instead ([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md)).
- **Relaxation may only relax what the searcher asked for.** Radius and their own availability
  grid are asks, and an ask may be widened — by the player, on offer. A term, a weight, a
  measurement and the quality floor are the engine's judgement about what makes a good game, and
  scarcity is never a reason to move one. Raising scores until candidates clear a fixed bar is
  lowering the bar, whatever the config file calls it
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **Availability overlap is evidence that a game can be arranged; it is never a proposed time.**
  The matcher matches players and stops. No court is booked and nobody can promise a slot before
  one exists, so the soonest shared slot is a reason on a card — *"you both play Saturday
  mornings"* — and never a booking. Who plays when is agreed by the players themselves.
- **A seat is never filled below the quality floor to complete a line-up.** The group is the
  objective, so one bad seat is a bad evening for all four. A partial line-up, and what is
  missing, is the honest answer.
- **The empty-result rate is a guardrail metric, never a target.** It is reported only paired
  with the return rate, and it is never on its own sufficient grounds to move the quality floor —
  which moves only in a record with a name on it.
- **A protected characteristic may gate; it may never score.** The value reaches candidate
  generation and gating and is **absent from the type handed to the scorer**, so no term can
  weigh it — the guarantee is a type boundary the build asserts, not a review checklist
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).

### Player Score — demanded, not designed

What the platform has watched a player *do*, as distinct from how well they play. **One number
in the UI, six strands underneath it**, and the matcher reads the strands separately because
*confirms results* is close to worthless for a friendly and close to essential for a counted
game ([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md)). Nothing about this
context is decided and nothing is built; the six words are here because the player reads all
six on their own screen, so they are the product's language before they are the matcher's.

- **Player Score** — the blended number a player sees. Computed from what happened, never from
  opinions and never from results: **losing costs nothing here.**
- **Strand** — one of the six things the score is made of. Each is a record of opportunities and
  what came of them, and each is published in its own right.
  - **Shows up** — whether the game gets played at all.
  - **Answers challenges** — whether a challenge gets an answer inside its window.
  - **Confirms results** — whether a counted game gets confirmed, so it *counts*.
  - **Keeps plans** — whether an agreed plan survives to its day without a late change.
  - **Settles up** — whether a court share that fell due was settled without a case.
  - **Sportsmanship** — what opponents said afterwards. A mean, not a ratio.
- **Opponent variety** — how widely a player spreads their games. Published beside the strands
  and **explicitly not one of them**; never blended into the Player Score.

**Invariants**
- **No record is not a bad record.** A player without a score is not bad and not average — the
  reliability term stands down and the other terms carry the match. The same principle the
  rating engine already applies to skill.
- **The score is a memory, and it fades with new evidence.** Decay belongs here, on the side
  that owns the record; a consumer that applies its own would be counting the same forgetting
  twice.

## Cross-cutting concepts

These are real and implemented; they apply across every context.

- **DomainEvent** — frozen dataclass with `occurred_at`; the unit of state change.
- **EventRecorder** — composed into aggregates/entities; collects events until drained.
- **DomainEventStore** — the append-only event log (`event_store` table). `append(...)`
  takes an `expected_version`; a mismatch raises **`EventStreamVersionConflict`**
  (optimistic concurrency).
- **Transactional outbox** — the `event_delivery_queue` table. Use cases enqueue events
  here **in the same transaction** as the state change, so side effects never run
  inline. See [ADR-0003](docs/adr/0003-transactional-outbox-for-event-delivery.md).
- **EventWorker** — the embedded poller that drains the outbox (`SELECT … FOR UPDATE
  SKIP LOCKED`) and dispatches to handlers after commit. Toggle:
  `EVENT_DELIVERY_WORKER_ENABLED`.
- **Event catalog** — registry mapping each event class to a stable durable **name** and
  **version**, so the JSON codec serializes by contract rather than by Python class
  name. Renaming a class must never change the wire format of stored history.
- **Port / adapter** — domain and application depend on `Protocol` ports; infrastructure
  implements them; wiring happens at the FastAPI boundary
  (`backend/app/api/dependencies.py`).
- **UnitOfWork** — the transaction boundary port (`AsyncSqlAlchemyUnitOfWork` adapter).
- **Read model** — the `users` table projection, written via `project_registered`, kept
  separate from the append-only event stream (CQRS-lite).

## Terms the client must not reinvent

The player app describes the same nouns this file does. A concept that exists in this
glossary keeps its name in TypeScript: an `Assessment` is an `Assessment`, not a `Quiz`,
`Survey`, or `Test`. Client-only *technical* vocabulary (wire type, DTO, mapper, secure
store) belongs in that app's own `CONTEXT.md`, never here.

The client also **renders** the values the backend sends. The backend sends numbers and
machine codes and never display text
([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so the client
formats — against one table, in [`docs/value-formatting.md`](docs/value-formatting.md).
That is not a design system and holds no colour or size; it is the exact string a level, a
time or a duration becomes. One client cannot drift from itself, so the table's immediate
value is smaller than it was — it is kept because it is the contract a *second* client
would be held to, and rewriting it from memory later is how two apps end up rendering the
same number two ways. **Copy is not formatting**: the sentence behind an unavailability
code is the app's own.
