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
settled in an accepted ADR and is being built, **Blocks** is settled in an accepted ADR and
is now built, and **Matchmaking** is settled in accepted ADRs and is not built at all. Their
terms are here because that is the order this file asks for, not because the code landed
first. **Player Score** is a further step out again: nothing about it is decided, and it
appears only because the matcher has contracted six words it will read, and the words are
the player's, not the matcher's. Every other section describes code that exists in
`backend/app/` today.

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
- **Adult attestation** — the player's own claim, given at sign-up, that they are an adult.
  **One boolean, and never a date of birth.** The platform is adults only, and that is a
  precondition of *holding an account* rather than a gate on who may be shown to whom
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md)) — *may you hold an
  account* and *may these two be shown to each other* are different questions belonging to
  different contexts. It is a value object that cannot be constructed from a missing or
  negative answer, so no registration exists without one.
  **It is not age verification** and claims nothing of the sort: it records that the question
  was asked and answered. Nothing downstream ever asks *how old* — only *may they be here* —
  so there is no age, band or date anywhere in the system to read, and the candidate index
  fails its build if a date of birth appears.
- **User events** (durable name / version):
  - **UserRegistered** — `users.user_registered` / v1 — first event of every stream. Carries
    the **Adult attestation** as an optional boolean appended after `occurred_at`: `true` is
    the attestation, and **absent means the account was registered before the question
    existed**, never a quieter *no*. There is no backfill — inventing a claim nobody made is
    the one thing an attestation must not do.
  - **UserDisabled** — `users.user_disabled` / v1.
  - **UserPromotedToAdmin** — `users.user_promoted_to_admin` / v1.

**Invariants**
- Email and nickname are **unique** — `RegisterUser` reads both before insert and
  raises `EmailAlreadyRegistered` / `NicknameAlreadyTaken` (a domain conflict, not a
  database constraint violation).
- **An account requires an Adult attestation, and a default is not one.** `RegisterUser`
  refuses without it — `AdultAttestationRequired`, a 400 — before it reads the email or the
  nickname, so a caller who answered nothing learns nothing about which of either is taken.
  The client writes the sentence; the backend only names the code
  ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)).
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
- **Mode** — *defined in the Matchmaking section below, where it belongs.* It is named here only
  because **Play intent** cannot be defined without it, and the two are the pair most easily
  confused: **Mode is the search's setting right now; Play intent is the player's standing
  declaration.**
- **Intent alignment** — what a searcher's live **Mode** is worth against a candidate's
  declared **Play intent**. Deliberately **asymmetric**: a social player in a competitive game
  is mildly bored, a competitive player in a game where nobody keeps score has been cheated of
  the only thing they came for. A **weight, never a gate** — and the one term that is never
  relaxed when the pool is thin.
- **Profile photo** — the first of a player's photos, and the one a player card shows. A
  player may hold up to three or none; none is not an absence but a **generated court
  poster**, derived from their identity so it is stable across devices.
- **Profile commit** — the single idempotent request that ends onboarding's second part,
  carrying all seven answers at once. Nothing is written before it, so leaving mid-part
  restarts at step 1 ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Keyed
  by a client-supplied **idempotency key**, which the creating event carries so a retry is
  recognised from the stream itself rather than from a table beside it.
- **Player profile events** (durable name / version):
  - **PlayerProfileCreated** — `player_profile.created` / v1 — the commit, carrying every
    preference and the idempotency key. **Not the opt-in.** It gained `gender` and
    `gender_preference` after profiles existed and **stayed v1**: both are appended with
    defaults so rows written before the question decode unchanged, and an absent `gender`
    means *committed before anybody was asked* — never a quieter `PREFER_NOT_TO_SAY`, which
    is an answer somebody chose. Nothing is backfilled.
  - **SocialTagsChanged** — `player_profile.social_tags_changed` / v1.
  - **PhotosChanged** — `player_profile.photos_changed` / v1.
  - **AvailabilityChanged** — `player_profile.availability_changed` / v1.
  - **LocationChanged** — `player_profile.location_changed` / v1.
  - **SearchRadiusChanged** — `player_profile.search_radius_changed` / v1.
  - **GenderChanged** — `player_profile.gender_changed` / v1 — gender is self-declared and
    freely changed, so the correction has an event from the day the field does.
  - **GenderPreferenceChanged** — `player_profile.gender_preference_changed` / v1.
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
- **A narrowed preference costs the player reach, and they are told at the moment of
  setting.** Mutuality means `WOMEN_ONLY` also makes its holder invisible to men entirely,
  including men who searched `ANY` — the half nobody would guess. The backend emits the
  reason; the client says the sentence, and learning it from an empty inbox is not
  acceptable ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **A profile is one per player, and asking whether one exists is a legitimate question.**
  See the narrowed *there is no onboarded player* invariant above, and
  [ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md).

### Blocks (`backend/app/modules/blocks/`)

One player deciding they do not want to be shown another, ever again. Settled by
[ADR-0095](docs/adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) and
**built**: the aggregate, its two events, the `BlockQuery` port and two routes. The surfaces
that will consult the port do not exist yet, which is why it is wired and has no caller.

- **Block** — an **event-sourced aggregate**, one stream per **ordered** `(blocker, blocked)`
  pair, with a deterministic stream id derived from that pair. **The record is directed; the
  effect is symmetric.** `A → B` and `B → A` are two independent blocks, so one being lifted
  never lifts the other.
- **Blocker** / **blocked** — the two sides of the ordered pair. The words name the *record*,
  never an experience: neither party can discover which way it went.
- **Block events** (durable name / version):
  - **PlayerBlocked** — `blocks.player_blocked` / v1 — the pair and the surface it was made
    from. **No reason, and no free text.**
    - **Block surface** — which of the four screens that show one player to another the block
      was made from: `SHORTLIST`, `LINEUP`, `FILL_SEATS`, `DECK` — the same roster
      [`search-telemetry.md`](docs/specs/matchmaking/search-telemetry.md) §2 calls **Surface**,
      and deliberately not extended. Client-asserted context recorded beside the fact; **no
      rule reads it**, in the shape of the Play intent surface. Unblocking records none,
      because it happens in one place.
  - **PlayerUnblocked** — `blocks.player_unblocked` / v1 — the pair.
- **BlockQuery** — the port that answers *is either of these two blocked by the other*. One
  port, consulted by every surface that shows one player to another, in two shapes: the
  searcher's whole **exclusion set** for generation, and the **pairwise** question for
  re-verifying a row before a response leaves. **It fails closed** — it raises rather than
  answering *nobody is blocked* when it cannot read the state, because an empty answer it
  cannot stand behind is a safety control switching itself off under load.
- **Hold** — the platform stopping a player from starting anything new while an unsettled case
  is open against them. A **held account** is an account under a Hold. Nothing can place one
  today, because the `cases` context does not exist.
- **AccountHoldQuery** — the port the Hold gate reads. Its only adapter today is
  **`NoHoldsExist`**, named for the fact it asserts rather than for being empty.
- **Disabled account** — an account that may no longer be used at all. **Not a Hold**: a Hold
  stops a player starting anything new while a case is open and they can still sign in and
  search; a disabled account cannot sign in. Two gates that sound alike, from two contexts, with
  different lifecycles and different remedies — so a rule about *account state* must always say
  which one it means
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
- **AccountStatusQuery** — the port the *account active* gate reads: the set of accounts that may
  not be shown, candidate-side only, because a disabled account cannot run a search in the first
  place.
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

Decided by [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md).
**The shortlist runs end to end**: `POST /api/v1/searches` gates, generates, scores, modifies,
floors, reorders and records. The **line-up**, the **deck**, the **relaxation ladder**, the
**interest ledger** and the **read-back** are designed and not yet built — every term below that
names one is settled and unimplemented, and says so where it matters. Thirty-three ADRs
(0093–0125) and the spec set at [`docs/specs/matchmaking/`](docs/specs/matchmaking/) settle it;
the pipeline is assembled in one place, with the precedence rule for reading them, in
[`the-engine.md`](docs/specs/matchmaking/the-engine.md). Only what a decision has actually settled
appears here.

- **Match Fit** — the **pure scorer**: the engine that turns one pairing into a **Fit** and its
  evidence. It has no clock, no randomness, no state and no database, and the type it is handed
  carries no protected characteristic, which is what makes the privacy line a build assertion
  rather than a review checklist. The stateful half of the matcher — the index, the ledgers, the
  telemetry — is the **module** beside it and is deliberately not an engine
  ([ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)).
- **Mode** — the *search's* setting: which of **Competitive** or **For fun** a player is
  searching in **right now**. **Two values, never three.** A player with no preference still picks
  a tab for tonight, which is exactly why it is not **Play intent**: an intent is a standing
  declaration per sport with three values, a Mode is one search's choice. They are separate types
  so confusing them is a compile error, and `NO_PREFERENCE` never selects a weight vector — it
  **inherits** one.
- **Fit** — how good the game would be, printed on the card as one number out of a hundred. A
  weighted sum of the **terms**, renormalised over whichever of them produced evidence.
- **Evidence** — what a **term** hands back beside its value: the fact it read, structured, in a
  **closed vocabulary** the API contract enumerates. Never a sentence — the engine emits codes and
  the client writes the words. Adding, removing or reshaping one is an **API change**, where
  moving a weight is free; and a kind a client cannot render is shown as a **named gap saying the
  app is out of date**, never dropped, because a breakdown that quietly stops adding up is the
  same class of lie as a recomputed score
  ([ADR-0106](docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).
- **Modifier** — a small, printed adjustment applied to a Fit after the **terms** are summed, for
  something true of the pairing that no term reads. The whole stack is clamped by the **modifier
  budget**, so modifiers may colour a match and can never decide one. A modifier that re-charges
  evidence a term already weighed is deleted rather than tuned: **the same fact may not move a
  score twice.**
- **Ruleset** — the frozen, named, dated set of **numbers** a search ran under: every weight,
  tolerance, bound and cap, plus the **tag relationship matrix**. **It is not a profile.** A
  Player profile is a person's own account of themselves; a Ruleset is the product's opinion about
  who should meet whom, and the two words must never be swapped — reusing *profile* here would be
  the first sentence of a confusing incident review. Immutable once released, so a new set is a
  new name and never an edit, and **never selected by the environment**: all four environments run
  the same numbers unless somebody deliberately releases a differently-named one.
- **Partition** — how the **candidate index** is divided so that a search scans a fraction of the
  city. **Derived, never stored and never a matching criterion**: it is computed from the area
  centroid, so there is no field a future filter could attach to and no metro boundary that can be
  wrong about a person. A search never spans two sports
  ([ADR-0101](docs/adr/0101-partition-derived-never-a-matching-criterion.md)).
- **Liveness** — how likely the game is to *happen*: whether they answer, whether they are
  around, whether they would want it. It **reorders** the list and never enters Fit, so the one
  number a player is asked to trust never quietly contains *"they open the app a lot"*.
- **Challenge load** — how many challenges are sitting unanswered in a candidate's inbox. It
  **sinks** them and never withholds them: an exclusion is a **Gate**, and the gate roster is
  enumerated and closed, so a full inbox joins **Liveness** instead
  ([ADR-0125](docs/adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md)). It crosses to
  a searcher as a **coarse code and never the number** — `SOME`, `BUSY`, `FULL` — because their
  inbox depth is theirs and *they have a lot on* is the whole of what a searcher is owed about a
  third party's unanswered mail. The deepest rung is anchored strictly below the interest lift,
  so somebody who said *Let's play* to you still surfaces however full their inbox is.
- **Term** — one question the engine asks about a pairing, returning a value in `[0,1]` and its
  evidence. **Playing style** and **social vibe** are the two that read **Social tags**, and they
  are split by *the claim a matrix entry makes*, never by which group a tag was printed in.
- **Gate** — a hard exclusion applied before anything is scored. Not a weight, and no
  relaxation ever reaches one. A gate that cannot be evaluated **excludes**, where a term that
  cannot be evaluated stands down. **Age is not a gate**: whether somebody may hold an account at
  all is a platform precondition in `users`, an attestation at sign-up and **never a date of
  birth**, so *may you hold an account* and *may these two be shown to each other* stay different
  questions in different contexts
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md)). **A full inbox is not
  a gate either** — it sinks a player in the ranking and never removes them, because withholding
  makes a thin pool thinner and no relaxation rung could reach them
  ([ADR-0125](docs/adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md)).
- **Level gate** — the gate on how far apart two levels may be: a candidate is not a candidate
  once Δμ reaches the searching mode's **own level tolerance**. There is one number per mode and
  it is the same number the level curve already uses, so the gate and the curve can never drift
  apart ([ADR-0103](docs/adr/0103-where-the-curve-saturates-the-gate-begins.md)).
- **NoEvidence** — what a term returns when it has nothing to weigh. It is dropped from the sum
  and the remaining weights renormalise; it is never `0`, and never a neutral `0.5`.
- **Quality floor** — the Fit below which a candidate is not shown at all. A **fixed** bar: no
  relaxation reaches it, and nothing lowers it in response to a thin pool
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)). One floor for both
  modes and every sport, and it is defined by the **judged pairings** it must satisfy rather
  than by a chosen number.
- **Judged pairing** — one of the named cases the quality floor must satisfy: **two people and a
  verdict**, never a profile of term values. It is held as the *inputs* that describe them — the
  levels, the grids, the distance, the tags, the declared intent — from which every term value is
  derived, so a change to a formula re-derives the case rather than stranding it. A case whose
  description names something mode-relative is **two** pairings; a case that describes two terms
  reading the same input is re-judged rather than pinned to the values somebody wanted
  ([ADR-0122](docs/adr/0122-a-judged-pairing-is-two-people-never-a-profile-of-scores.md)).
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
- **Silent movement** — a change to a candidate's **position** that prints no reason. It is
  bounded, per **player** and not per signal, at the same threshold above which a movement owes an
  explanation, so the promise is arithmetic rather than policy
  ([ADR-0123](docs/adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)). Only two
  signals are silent, and both are facts about that player. **Position moves on a fact about the
  player, never on a fact about the shape of the list** — which is what refuses a diversity spread:
  *you are fourth because the three above you resemble each other* is true of nobody on the screen
  ([ADR-0126](docs/adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)).
- **Guaranteed inclusion** — a candidate placed in the shortlist by something other than Fit.
  There is exactly one: an **interest lift**, a human's own *Let's play*, which may sit below the
  quality floor with its reason printed. The newcomer and zero-exposure lifts **reorder** and
  never **admit**, so neither is a guaranteed inclusion — the first is a printable liveness
  reason, the second is recorded and never told to anybody.
- **Newcomer** — a player before their first game, and never for longer than **14 days** from the
  profile commit that made them searchable. A **predicate over a date, never a stored flag**: a
  flag would need a loop to keep it true, and a date needs nothing. The games half is the
  definition and the days are a ceiling, so it terminates even while nothing counts games.
- **Newcomer window** — the period a Newcomer is in, and it has exactly one power: **minimum
  evidence does not apply**. It bends nothing else — not the quality floor, not a gate, not a
  Block. It also **tightens the level gate for both sides of the pairing**, and it lifts the
  Newcomer in other players' lists, printed. When it closes on somebody who never played, nothing
  happens: what catches them afterwards is the ordinary exposure lift, which never expires
  ([ADR-0113](docs/adr/0113-newness-changes-the-gate-never-the-weights.md)).
- **Welcoming record** — a candidate who has **played opponents whose rating was still settling**.
  One input and printed, because it is the only evidence that says somebody is *willing to play
  a stranger who might be bad*: sportsmanship says they are pleasant and opponent variety says
  they get around, and both are already scored elsewhere. **A player may never decline being
  matched to a Newcomer** — that is a preference over people that protects nobody, and the
  pressure it would relieve is bounded instead, by capping how often the engine volunteers
  anybody ([ADR-0114](docs/adr/0114-a-newcomer-may-not-be-declined.md)).
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

- **Tag relationship matrix** — product's claims about how two **Social tags** relate: **matching**,
  **complementary** or **clashing**, each entry naming which term it belongs to, which modes it
  holds in, and — in doubles — whether it is about partners or opponents. It is a claim about how
  people get on, not an implementation detail, so it is ruleset data and arguable without a code
  review. A **second and separate** map, over `WHY_YOU_ARE_HERE` alone, sets the familiarity sign.
- **Modifier budget** — the bound on everything the modifiers together may move a Fit, so no stack
  of small adjustments can override the substance of a match. The **reliability floor** sits
  outside it and is larger than all of it, deliberately.
- **Search** — one invocation of the engine, with an id, permanently recorded before its answer
  is returned. **A returned search is a recorded search**: if the record cannot be written the
  search fails, because the id *is* the answer's identity — without it there is no *Why 78?*, no
  **Origin key**, and no way to say *Let's play*
  ([ADR-0104](docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)).
- **Surface** — which of the four things a search is: a ranked **shortlist**, a seated
  **line-up**, the **deck**, or **completing a half-built game**. One engine and one pipeline
  with different terminal stages; the last is optimised for the existing group and not for the
  searcher, and says so. Distinct from **initiation**, which is who asked.
- **Initiation** — whether a search was run by a person or pushed by the platform. It gates the
  push and never the person: a player who declined proposals still appears in a search another
  player deliberately ran. Orthogonal to **Surface** — the deck has both kinds.
- **Returned candidate** — somebody the response actually carried, with their Fit and its whole
  breakdown kept exactly as it was computed. The searcher may read their own; nobody else may
  read them at all.
- **Near miss** — the best candidates that were scored and did **not** clear the **quality
  floor**, kept with the same breakdown and a reason. *The best match we refused to show* is the
  only thing that can prove the floor wrong, and it exists only at scoring time. **Engine-internal
  and never returned to anybody**: a player may ask why somebody was shown, and nobody may ask who
  was withheld.
- **Line-up** — *who* the four (or two) are. **Arrangement** is *which side each of them plays
  on*: for any four there are exactly three, and the engine returns all three with a forecast
  each, so choosing between them is a selection and never a calculation. The two are separate
  words because the best-of-three forecast answers *are these the right people* while the
  arranged forecast answers *is this the right way round*, and conflating them is how a screen
  stops changing when somebody is moved across the net.
- **Group objective** — what the engine maximises when it seats four people, as against **Fit**,
  which is about one pairing. A four holds **six pairs and the searcher is in three**, so a term
  earns its place in the objective only by reading something no seat's Fit read: the **cross
  pairs**, the four-way availability, the arrangement, and the **seat delta**. It is never shown
  as a number and has no floor — nothing is seated because its objective cleared a bar, only
  because it beat every other combination — and one closed reason code names the term that
  decided it ([ADR-0117](docs/adr/0117-a-group-term-reads-only-what-fit-did-not.md)).
- **Cross pair** — a pair inside a **line-up** that contains no searcher: three of a four's six.
  Invisible to every **Fit** by construction, because Fit is always about the searcher and
  somebody. Read by the **group objective** through the same functions Fit uses, so *how do these
  two get on* has one implementation called six times — three printed, three scored.
- **Seat delta** — what a pair's reading gains when it stops being unseated. A pair on a
  shortlist reads the forgiving **opponent** entries of the **tag relationship matrix**; seating
  somebody as a partner is when the harsher partner entries apply. Zero for opponent seats by
  construction. **It never re-scores a Fit** — the card says the same number in the builder as in
  the list, because a Fit that moves when somebody crosses the net is *Why 78?* failing on the one
  screen that promises to show its working.
- **Interest** — a player's own *yes* to a specific person, cited to the **Search** that
  surfaced them. It is a human's judgement rather than the engine's, which is why it may lift
  somebody above the **quality floor** where nothing the engine computes may. It outlives the
  search it came from, and it is not a challenge — a challenge belongs to a context that does
  not exist yet. **A yes is a statement about *now*, so it expires** — at 21 days, flat until
  then and then absent, never tapering, because the age of the yes is already printed on the card
  and a fading lift would charge for it a second time invisibly
  ([ADR-0127](docs/adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md)). The expiry
  is **dated when the yes is made**, never announced when it lands.
- **Outstanding interest** — an **Interest** that is sent, **unexpired**, and **not yet
  mutual**. It is what the cap counts: a mutual has been answered and is no longer in flight, and
  an expired yes is not interest at all. Without the word, *how many yeses you may have out* is
  three different numbers. The cap is **per sport**, **hard** — the write is refused, never
  quietly aged away — and **shown before it bites**, because a cap the player cannot see is a
  refusal they cannot predict.
- **Deal** — one invocation of the **deck**: a bounded, ordered batch of cards, shown one at a
  time. The deal is the unit, not the card, because the deck's ordering — people who already said
  yes, then liveness, then the rest — is a property of a whole deal and cannot be evaluated a card
  at a time. A **spent deal** is not an empty pool: it deals again, as a new **Search**, and only a
  fresh deal that comes back with nothing is the **pool description**.
- **Ruleset version** — the name of the frozen set of numbers a search used. **Engine version**
  is its sibling and means the *maths* changed. Stamped on every search, so a Fit stays
  interpretable after the numbers move
  ([ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)).
- **Ruleset release** — the act of moving from one **ruleset version** to the next. Two kinds,
  and which one it is decides what can answer for it: a **weight-only** release moves numbers
  that multiply what a term already reported, and every search ever recorded can be re-scored
  under it; a **shape-class** release changes what a term *reports* — a curve, a tolerance, a
  term turned on — and no past search can speak to it, because the values it would need were
  never stored. The kind is **derived, never declared**
  ([ADR-0118](docs/adr/0118-a-past-search-is-not-reproducible.md)), and a release is signed by
  the person accountable for the **quality floor**
  ([ADR-0119](docs/adr/0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md)).
- **Candidate index** — the matcher's picture of the city: one row per `(player, sport)`,
  rebuilt by replaying the events the owning contexts already record. It **owns no truth** — if
  it and the backend ever disagree, the backend is right and the index is rebuilt. It holds
  **only facts a player changes about themselves**; every fact that must be true at the moment
  it is read is deliberately not in it, which is why being stale costs quality and can never
  cost safety
  ([ADR-0111](docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)).
- **Snapshot** — one immutable copy of a partition of the **candidate index**, taken once at the
  start of a search and held for its whole life. It is what makes a search reproducible: the
  index cannot move underneath one that is already running
  ([ADR-0112](docs/adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md)).
- **Snapshot version** — how much of the world the engine had seen when a search ran. With the
  ruleset version and the moment, it names the world a Fit was computed against, which is what
  keeps an old breakdown **interpretable**. It does not make a past search **reproducible**:
  three of a search's four inputs — the live block set and pairwise history, the held account,
  and the ledgers — are deliberately not recorded, so a search is explainable forever and can
  never be re-run
  ([ADR-0118](docs/adr/0118-a-past-search-is-not-reproducible.md)). It means
  **everything up to and including this is applied** — a *contiguous*
  prefix of the event store's append order, never simply the highest number seen, because an
  append is assigned its position before it commits
  ([ADR-0110](docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)).
- **Player card** — who a candidate *is*, as against how well the game would go. A **closed
  list** — nickname, photo, area, Social tags, level and band, counted games — and it is assembled
  by the backend **after** the engine returns, on the seam **at stake** already rides, because the
  scorer is forbidden every field on it. There is no name in this platform, only a **Nickname**.
  **The distance is not on it**: a card says only what its subject published, and a distance is a
  fact about a *pair*, so it is the one field that would change depending on who was looking
  ([ADR-0107](docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
- **Forecast** — how the game would go, for a set of people. Three readings of one type and the
  words are not interchangeable: the **best-of-three** forecast answers *are these the right
  people*, the **arranged** forecast answers *is this the right way round*, and a
  **provisional** forecast answers the same question with a seat still empty, reading a
  half-empty side as if the missing player matched the one already there. Provisional is a
  property **of** the forecast and never a flag beside it, so the number cannot be rendered
  without its caveat. Filling the last seat makes the provisional figure and the arranged figure
  the same number, asserted rather than hoped
  ([ADR-0108](docs/adr/0108-a-forecast-is-a-route-not-a-search.md)).
- **Concern** — the engine's own statement that one term of a match is genuinely weak, keyed to
  that term. *What counts as weak* is a judgement about weights and curves and is made where they
  live; how many to show is the client's. A card shows one, the breakdown shows all of them.
- **Pass** — *not today*, on a deck card. **Write-only**: it is recorded, it suppresses, and no
  response ever carries one — not to the passer, not as a count. It carries its **Origin key**,
  because the only thing that could prove its suppression window wrong is the pass rate on
  re-shown profiles. **A pass is a statement about my deck, where a Block is a statement about a
  person** ([ADR-0128](docs/adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)), and
  every boundary follows from that: the suppression is **deck-only** and never reaches a search,
  which is a question about the city that a swipe may not edit; it is **one-directional**, so it
  costs the other person nothing, literally; and it **never escalates** — a second pass buys the
  same 30 days, because a pass that hardens toward permanence is a Block nobody consented to. The
  **suppression** lapses at 30 days; the **record** of the pass does not, because a lapsed
  suppression leaves no trace that a re-shown card is a re-show.
- **Exposure** — how often a player has been **shown** in somebody's answer, counted per sport
  per week. It exists so that the same ten people do not sit at the top of every list: a player
  shown to nobody this week is lifted, and one shown far more often than most is sunk. Both are
  **silent and both only reorder** — exposure fairness is not a reason to show somebody a bad
  evening, so it may never admit anybody below the **quality floor**
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)). *Shown more often than
  most* is the week's ninetieth percentile, republished hourly rather than computed per search.
  The same ledger will carry `NEWCOMER_ABSORPTION_CAP` — how often one player is volunteered
  into a **newcomer's** shortlist — which binds by dropping a lift and **never** by withholding
  anybody, and **nobody is told**, because nothing has happened to them. That count is not kept
  yet: the cap *keeps its rule and refuses its integer*, so there is nothing for it to bind on.
  _Avoid_: "impressions", "visibility".

**Terms this context refuses**
- **Game format** — *mixed doubles*, *women's doubles* and the like. Deliberately does not
  exist. A search carries a **Sport** and never a format; the sport fixes the seat count
  (`backend/app/kernel/sports.py`, which refuses a `Format` dimension for the same reason). Who
  may sit in a seat is answered by **Gender preference**, which is about people and says so
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **Activity recency** — *active 2 hours ago*, a green dot, *active today*. Deliberately does not
  exist on any surface. It is a Liveness input, so it reaches a screen the one way Liveness is
  allowed to: as a **reason** about the pairing's chances — *usually answers within a day* — never
  as a fact about a stranger's phone. This product has no presence indicator
  ([ADR-0107](docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
- **A bio.** No player-authored free text reaches a card. The Social tag vocabulary is closed for
  the same reason, and the sentence a player might write about themselves is a moderation surface
  before it is a feature.
- **An interest inbox** — any list, count or badge of who has said *Let's play* to you. The signal
  exists only on the promise that it is silent, and a yes given under that promise is not consent
  to appear in somebody's inbox
  ([ADR-0109](docs/adr/0109-a-read-back-names-what-it-withholds.md)).

**Invariants**
- **A term that cannot be evaluated stands down. A gate that cannot be evaluated excludes.**
  Absent evidence makes a term renounce its weight and the rest renormalise; absent evidence
  makes a gate *fail closed*. An absent gate is an open door, never a standing-down signal.
- **A safety gate is verified against live state, on the side that owns the truth.** The
  matcher proposes and the backend disposes: anything failing live verification is dropped from
  the answer before it reaches the client, and the shortlist is simply short by one.
- **A term must never be blind over the range it is asked to score.** Where a term's curve
  saturates — the same value for every input past a point — the engine has stopped having an
  opinion, and a bar over a score cannot discriminate what the score cannot see. **Where the curve
  saturates, the gate begins**
  ([ADR-0103](docs/adr/0103-where-the-curve-saturates-the-gate-begins.md)). The mirror of the
  invariant below, and found the same way: by a case the weights could not decide.
- **A term's zero is its worst outcome, never its most common one.** A term whose typical
  pairing scores nothing is not weighing what its weight claims — and a penalty that disappears
  into a clamp at zero is a penalty that was never charged.
- **A silent movement never exceeds the movement that owes an explanation — per player, not per
  signal.** Liveness explains itself whenever it moves somebody into view, so the signals that may
  never be shown to either side share **one budget**, equal to that same threshold, clamped on
  their signed net. A bound on each signal separately is not a guarantee about a person, who is
  moved by the sum; and the bound is *at* the threshold rather than under it, because movement of
  exactly that size is what the promise already excuses. The engine may move somebody quietly only
  by no more than it would owe a reason for — which makes the reason **exist** whenever it is owed,
  rather than making it a rule to be policed
  ([ADR-0123](docs/adr/0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)).
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
- **In a four, every gate binds all six pairs.** A block, a **gender preference** and a level
  tolerance are checked between every two people who would share the court, not only between the
  searcher and each of them — a player shares ninety minutes with all three, and a gate that
  only ever asks about the person who happened to run the search is not protecting anybody else
  in the game. Eligibility for a *seat* is a property of a combination rather than of a
  candidate, so it cannot be spent when candidates are generated; the price is that a four can be
  impossible where candidates are plentiful, which is a partial line-up with a reason
  ([ADR-0116](docs/adr/0116-in-a-four-every-gate-binds-all-six-pairs.md)).
- **The empty-result rate is a guardrail metric, never a target.** It is reported only paired
  with the return rate, and it is never on its own sufficient grounds to move the quality floor —
  which moves only in a record with a name on it.
- **A weight is configuration; an evidence shape is contract.** A released ruleset may move
  every number the engine holds without touching the API. Adding, removing or reshaping the
  **evidence** a term reports is an API change, because the client generates its renderers from
  it — and a reason the client cannot render is shown as a **named gap saying the app is out of
  date**, never dropped silently. A breakdown that quietly stops adding up is the same class of
  lie as a recomputed score, and worse for being invisible
  ([ADR-0106](docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).
- **Absence has two spellings and they mean different things.** *Omitted* is *this does not
  apply here*; *null* is *this applies and the answer is a measured nothing*. It is the
  measured-versus-invented test carried to the wire, and the two generate as different types so
  a client cannot treat them alike.
- **A protected characteristic may gate; it may never score.** The value reaches candidate
  generation and gating and is **absent from the type handed to the scorer**, so no term can
  weigh it — the guarantee is a type boundary the build asserts, not a review checklist
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **A card says only what its subject published.** Everything on a **Player card** is something
  the player themselves put there — a photo, an area, their tags, a level they proved. Nothing
  the platform merely *observed* about them reaches a stranger's screen. That is what rules out
  activity recency, which the engine does compute and may not show, and it is the line that
  separates a fact a player offered from a fact a system noticed
  ([ADR-0107](docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
- **A silent signal never becomes an inbox.** *Let's play* was collected on the promise that
  nobody is notified and it becomes visible only when one of you goes looking for a game. So a
  one-sided yes reaches its recipient exactly one way — as an **interest lift** on a card, in a
  search *they* chose to run, with the reason printed. Re-reading banked yeses as consent to a
  screen that lists them is changing the terms after the fact
  ([ADR-0109](docs/adr/0109-a-read-back-names-what-it-withholds.md)).
- **A withheld row is stated, never vanished.** Reading a stored search back re-checks the gates
  that fail closed, so a person who has since blocked you is not rendered — and the response
  *says* a row was withheld rather than returning nineteen where twenty were recorded. The record
  stays immutable; what is live is the gate. A list that quietly gets shorter is the same class of
  lie as a breakdown that quietly stops adding up
  ([ADR-0109](docs/adr/0109-a-read-back-names-what-it-withholds.md)).
- **A forecast may be recomputed; a search may only be read.** A forecast's inputs are its
  arguments and a frozen ruleset, so asking twice gives the same answer and no record is needed to
  prove it. A search's inputs include an index that has moved, so only the stored row can say what
  it saw. That asymmetry is the whole reason a search is permanently recorded and a forecast is
  not — and the day a forecast stops being deterministic it becomes a search
  ([ADR-0108](docs/adr/0108-a-forecast-is-a-route-not-a-search.md)).
- **A fact the product promised not to surface is asserted absent from every response shape,
  once.** Passes, declines, blocks, incoming-and-not-mutual interest, Liveness numbers, pre-gate
  pool counts. A test per route passes forever and then somebody adds a route; the assertion is
  central, over every response type the contract publishes.

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
- **Opponent variety** — how widely a player spreads their games. **Not demanded of
  `player_score` any more:** it was contracted on behalf of two consumers and
  [#164](https://github.com/Raketa02/Raketa/issues/164) and
  [#175](https://github.com/Raketa02/Raketa/issues/175) struck both, so ADR-0098 was amended to
  withdraw it — *a consumer-driven contract with no consumer is withdrawn, not carried*. The word
  survives as product language for the Player Score screen; if a later term wants the statistic,
  it returns as that term's demand and signs for it.

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
