# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. Every app
obeys this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Raketa is a racket-sport platform. Today a player signs up, answers a questionnaire that gives
them a **Skill rating** per sport, joins **Groups**, and is dealt games by their group's Games
deck — the last yes books a club's court and charges every seat — while a **Club** runs its
courts, bookings and money on its website. That is served by the **player app**, the **club
website**, the **public site** and one **backend** built on Clean Architecture (hexagonal ports &
adapters), DDD, and event sourcing.

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
>
> **Courts, bookings and money returned with [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)** (2026-09-29),
> specified in [`docs/specs/games-and-fill-in/`](docs/specs/games-and-fill-in/), and are built: a
> group's Games deck proposes a game, the last yes books the club's court, and Fill in rescues a
> seat. Their terms are in Part 1 under **Proposals**, **Bookings**, **Payments** and **Club**.
>
> **It was cut back again on 2026-10-06**, when the older way of making a game — *Classic play* —
> was removed with the feature flag that hid it ([#569](https://github.com/Raketa02/Raketa/issues/569)).
> Every term that named only that loop went with it: *Challenge*, *Plan*, the Players *Deck* and
> its *Deal*, *Radar*, *Search*, *Interest*, *Pass*, *Prompt*, *Cool-off*, *Exposure*, the
> candidate index, *Fit* and every term of the ranking, *Search radius*, *Proposals opt-in*,
> *Tester* and *Feature flag*. A word you remember from one of them is gone on purpose; see the
> [ADR index](docs/adr/README.md#the-2026-10-06-classic-play-removal--the-second-gap).

---

## Part 1 — Implemented bounded contexts

These are the authority for their terms. After the reset, no term is committed ahead of *a
decision*, and a speculative list of context names is not one. A
context that does not appear below has no vocabulary yet — resolve its terms into this file
before writing it, which is what every section from **Player profile** down was: settled in an
accepted ADR and written here first, then built. Their terms are here because that is the order
this file asks for, not because the code landed first — so **whether a context is built is stated
in its own section and nowhere else**, which is what the paragraph below has always asked for and
what the last three sections here — **Club**, **Groups** and **Administrators**, each built
ticket by ticket — depend on.

> **A verdict narrower than that belongs to the section it is about.** This paragraph carried a
> clause per context and went stale twice, because a per-context verdict at the top is a second
> place for *is this built* to be true. What a context can and cannot see — a strand that stands
> down, a modifier wired and never binding, a term settled and unbuilt — is stated in its own
> section, where the reason for it is.

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
- **Likely range** — μ ± σ, clamped to the scale. **A fact about one player**, so it travels
  on any card that names them — printing μ while refusing μ ± σ would show a level and hide
  how sure of it anybody is. A band's numeric edges are **not** a second range to compare it
  against, and a screen printing a range prints the published values rather than a second set
  of drawing constants.
- **Band** — one of four named ranges, deliberately uneven in width, each with a
  plain-language meaning: **New** 1,0–1,5 · **Developing** 1,6–2,6 · **Established**
  2,7–3,8 · **Advanced** 3,9–5,0.
- **Rating status** — **Initial Estimate** (onboarding output, no counted matches) →
  **Calibrating** (real matches started, still moving) → **Stable**. **A count opens the
  door and certainty closes it** ([ADR-0139](docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)):
  the *first* confirmed counted result leaves Initial Estimate, and Stable is reached when
  the uncertainty does — not when a game count does, because twenty games against people
  nobody has watched is not certainty.
- **At stake** — what a counted win and a counted loss against one specific opponent would do
  to a player's Level, shown before they commit to the game. A **pair** of signed deltas, and a
  fact **this context owns**: it reads the rating engine's own update rule, so nobody else may
  compute it — not the client ([ADR-0021](docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md):
  a rule, not a comparison), and not `matchmaking`, which reads it for a game's pairing and never
  re-derives it. It exists only for games that would be counted. **It is not a preview of the
  rule; it is the rule**, read forward — the same function that moves the Level if the game is
  played, so the card cannot promise a figure the result then contradicts. *Absent* rather than
  zero when either party holds no rating in that sport. **On a game it is read for the reader,
  side against side** — every seat is known once a line-up is frozen, so the pair is the one
  the result will deliver, and a four's figure is not the card's head-to-head one
  ([ADR-0161](docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
- **Result update** — what a **confirmed counted result** does to the two or four Levels that
  played it. A result is **evidence about the gap between two people**, fused by inverse
  variance like every other kind, so *how surprising it was* moves the Level and the certainty
  tightens out of the same arithmetic rather than out of a second rule. Each side is one player
  at the average of its Levels, so **everybody on a side moves by the same amount** — a partner
  is not somebody you are rated against — while each of them keeps the certainty they had. And
  **a four is half the evidence about any one of the four**.
  **No single evening moves a Level further than the ceiling** — a brake, because onboarding's
  uncertainty is a floor rather than a measurement and silence confirms a score nobody read.
  Decided by [ADR-0139](docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md).
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
- **Skill passport** — the You tab's screen listing every Skill rating a player holds, one
  result card per sport with the record's blocks under it: a document a player **reads and cannot
  write**. *Add a sport* on it starts one questionnaire for an unrated sport and ends back on it
  ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §3).

**Invariants**
- **A level is proved, never declared.** Not by the player, not by staff, not by a club.
  Manual editing is refused by the domain itself, not guarded by a permission check.
- **Only the rating context writes μ, σ, volatility and status.** Every other engine
  contributes evidence, an information weight, or an anomaly signal — never a rating point.
- **A result moves a Level or it moves nothing, and there is no third outcome.** An unscored
  game is *an evening, not evidence*; a friendly was never evidence about anybody by the choice
  of the people who arranged it. Both are absent from what the rating context reads, so neither
  is a branch anybody could forget.
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
  first thing to return no — tags, photos, a week, a location and a gender are facts about
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
- **Player** — a User acting **as a player**: named, rated, with a Player profile. **Not a
  separate aggregate and not a separate id**: a player's identity *is* the `UserId`. `PlayerId`
  exists as a distinct type so the code reads in the domain's own vocabulary and so the two have
  one place to diverge, but today every `PlayerId` is a `UserId`. There is no `players` table.
  **Revisited 2026-09-25, because a settled decision meets its condition:** club staff are to
  share this accounts system as **Administrators**
  ([ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)).
  The model holds: one User may act as a player, as an Administrator for each club that named
  it, or both — **one email, one password** — and neither side is a second identity. Revisit
  again only if a person can be known to the system as a participant without holding an account.
  *Profile*, as the app's switcher says it (*Player* / *Administrator*), is **UI vocabulary, not a
  domain term**, because **Player profile** already names an aggregate. _Avoid_: "player
  account", "admin account" — there is one account.
- **Authority** — role enum, `USER` or `ADMIN`. **Not an Administrator**: an Administrator runs a
  club's official groups and holds no power over the platform or over any account, and becoming
  one changes no `Authority`.
- **Email** — value object. Trimmed, lower-cased, RFC-ish validated, ≤ 320 chars.
- **Name** — value object. *What a player is called.* Free text: trimmed, runs of whitespace
  collapsed to one space, 2–64 chars, **never unique** — two players may share one,
  and it is checked against nobody. **The name is what every screen says**: every sentence, row,
  card, sheet, toast, seat label and spoken name uses the whole name or names nobody; the two
  initials over a generated poster stay the one derived form
  ([ADR-0167](docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §3),
  cut from it. Null until the **naming**
  ([ADR-0171](docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)) —
  except on an account an **Invitation** created, which carries **the name the club typed** from
  the start and no Nickname
  ([ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §4).
- **Nickname** — value object. Trimmed, 2–64 chars, `[A-Za-z0-9_.-]`, **unique**. A **handle**:
  shown as `@nickname` under the name on a player's record and on their own You tab, and **said
  nowhere** — never in a sentence, on a row, a card, a sheet, a toast, a seat label or a spoken
  name. Null until the naming.
- **The naming** — the one act that names a player: name and nickname together, asked in
  onboarding's first step (*How should people see you?*) and never at sign-up, **repeatable** (a
  later change is the same act), refused with `NicknameAlreadyTaken` when the handle is another
  player's. Sign-up asks for credentials only — email, password, the Adult attestation — and a
  `User` is created unnamed. Its step is reached while the account is **not named in full** and
  asks only for what is missing: an account an Invitation created is asked for the nickname
  alone, and the act still carries both (ADR-0185 §4). `/users/me` carries the name and the
  nickname each on its own, so the step can tell which is missing.
- **RawPassword** — the plaintext at the boundary; 8–128 chars with ≥1 letter and ≥1
  digit. Carrying it as a type is what prevents hashing an unchecked string.
- **HashedPassword** — non-empty bcrypt hash; the only password form ever persisted.
- **Adult attestation** — the player's own claim, given at sign-up, that they are an adult.
  **One boolean, and never a date of birth.** The platform is adults only, and that is a
  precondition of **playing** rather than a gate on who may be shown to whom
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md), narrowed by
  [ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §5) — *may you play here* and *may these two be shown to each other* are different questions
  belonging to different contexts. It is a value object that cannot be constructed from a missing
  or negative answer, so no sign-up exists without one. **An account an Invitation created holds
  none** — running a club's groups asks nobody's age — and gives it at **Start playing**, before
  anything player-side: no Skill rating, Player profile or place in a pool exists without one.
  Given later by `POST /users/me/adult-attestation`, once; and **refused where a player-side
  record begins** — an assessment's start and a Player profile's commit meet
  `adult_attestation_missing` until it is given. An account registered before the question
  existed is read as **not attested** — nobody was asked — and never as a claim it did not make.
  **It is not age verification** and claims nothing of the sort: it records that the question
  was asked and answered. Nothing downstream ever asks *how old* — only *may they be here* —
  so there is no age, band or date anywhere in the system to read.
- **User events** (durable name / version):
  - **UserRegistered** — `users.user_registered` / v1 — first event of every stream. Carries
    the **Adult attestation** as an optional boolean appended after `occurred_at`: `true` is
    the attestation, and **absent means the account was registered before the question
    existed**, never a quieter *no*. There is no backfill — inventing a claim nobody made is
    the one thing an attestation must not do. **Carries no nickname** since ADR-0171: the
    account is registered unnamed, and the version did not move because no store outlives the
    branch that changed the shape.
  - **UserNamed** — `users.user_named` / v1 — the naming, carrying the **Name** and the
    **Nickname** together; the fold keeps the latest.
  - **UserDisabled** — `users.user_disabled` / v1.
  - **UserPromotedToAdmin** — `users.user_promoted_to_admin` / v1.
  - **AccountOpenedByInvitation** — `users.account_opened_by_invitation` / v1 — the other way
    a stream begins: an account an **Invitation** opened when its person set a password,
    carrying **the name the club typed**, the hash, and **no Nickname and no attestation**.
  - **AdultAttested** — `users.adult_attested` / v1 — the Adult attestation given after the
    account was opened, at *Start playing*. Recorded once.
  - **PasswordChanged** — `users.password_changed` / v1 — a new password and the instant every
    older session stopped counting; carries the new hash.
  - **PasswordCleared** — `users.password_cleared` / v1 — the club's *Reset password* of an
    administrator-only account: no password at all, signed out everywhere; nothing signs in
    until one is set.

**Invariants**
- Email and nickname are **unique**, and each is read by the act that carries it —
  `RegisterUser` reads the email before insert and raises `EmailAlreadyRegistered`; the naming
  reads the nickname and raises `NicknameAlreadyTaken` (a domain conflict, not a database
  constraint violation). **The name is never checked against anybody.**
- **Signing up requires an Adult attestation, and a default is not one.** `RegisterUser`
  refuses without it — `AdultAttestationRequired`, a 400 — before it reads the email, so a
  caller who answered nothing learns nothing about whether it is taken. An account an Invitation
  created is the one account without it, until it starts playing (ADR-0185 §5).
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
- **Audience** — which surface a token is for: the **player app** or the **club** website. A
  token for one is refused on the other. The Administrator profile runs under the player app's
  audience — switching profiles is not a new token
  ([ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §6). Built by [#503](https://github.com/Raketa02/Raketa/issues/503).
- **Signing out everywhere** — what a password change does: the account's **credentials-changed
  instant** moves, every access token issued before it is refused, and every refresh token it
  holds is revoked. Set by *Forgot password?*, by the club's *Reset password* and by any other
  password change, for a User and a Club account alike (ADR-0185 §7). Built by
  [#507](https://github.com/Raketa02/Raketa/issues/507); the club's reset by
  [#508](https://github.com/Raketa02/Raketa/issues/508).
  _Avoid_: "logout all", "kill sessions".
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

Everything a game needs to know about a player that a questionnaire cannot infer. Decided by
[ADR-0089](docs/adr/0089-player-profile-context-event-sourced.md); the terms are here ahead
of the code because this file asks for them in that order.

- **Player profile** — an **event-sourced aggregate**, one per player. **The first
  aggregate in the racket-sport domain that is not per sport**: skill is per sport, but
  tags, photos, a week, a location and a gender are facts about a person.
- **Social tag** — one of a **fixed, closed vocabulary** the platform owns, in three groups
  about the game: how a player is *after the match*, what they are like *on the court*, and
  *why they are here*. A player holds **2 to 6**. Never free text, never player-authored,
  never imported from another platform, and never about the person rather than the game —
  age, looks, body and "looking for" are a different product's vocabulary.
- **Weekly hours** — a player's ordinary week as **hours per weekday, 07:00–23:00**: a grid of
  7 days × 16 one-hour cells, Monday-first. It replaced the 7 days × 3 parts of the day with
  [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5, because a court
  is booked by the hour. It is the *only* way time preference is ever expressed, and it is a
  **preference, not a promise** — a ticked hour is never a commitment or a hold. What it now
  also is, is the thing a court hour is read against: a player counts as **free for a game only
  when its whole hour is inside their weekly hours**, never merely its start — one rule, in one
  function, that every context asks. _Avoid_: availability grid, availability slot, part of the
  day.
- **Weekly hour** — one cell: a day and the hour it starts at, wall clock — Tuesday 19:00 is
  19:00–20:00. The finest precision the platform holds about when a player wants to play.
- **Location area** — where a player plays, held coarsely: a cell about a kilometre across,
  rounded to on the way in. The precise fix that produced it is never a shareable value; what
  reads it is the distance to a club. **It
  moves on a cold start**: the app re-reads the phone silently when it is launched, and after a
  day in the background, and the cell changes if the fix falls outside it — never merely on
  foreground, never with a prompt, and never when the permission has since been revoked
  ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §6).
- **Gender** — `WOMAN`, `MAN` or `PREFER_NOT_TO_SAY`, held on the Player profile. **Per
  person, never per sport**, self-declared and freely changed. It is a statement about **which
  courts a player wishes to share**, not a ruling by the platform on who anybody is:
  `PREFER_NOT_TO_SAY` meets only a preference of `ANY`, and is an explicit answer rather
  than a null — the same shape as Play intent's `NO_PREFERENCE`. Required at profile creation,
  and asked on its last step, *Who you play with*.
  **Never rendered on a card and never carried by a response that describes one player to
  another** ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md));
  **the one shape that carries it out is the owner's own profile read**, so the You tab can show
  a player what they set ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §4).
- **Gender preference** — who a player is willing to share a court with: `WOMEN_ONLY`, `MEN_ONLY`
  or `ANY`. Durable, optional, defaulting to `ANY`. **Mutual, never one-directional** — a pair is
  admissible only if each passes the other's, so it governs both who a player is dealt and who
  they are dealt to. A **gate, never a weight, and never relaxed**: it is one of the three things
  **PlayerFit** asks of every pair on a court (Proposals). **It does not reach whoever runs an
  Official group the player is in**: running their group is not being matched with them, and
  that account opens their record without it
  ([ADR-0159](docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md),
  amended 2026-10-02).
- **Play intent** — what kind of game a player wants in **one sport**: `COMPETITIVE`,
  `FOR_FUN` or `NO_PREFERENCE`. **Declared, per sport, and never inferred.** `NO_PREFERENCE`
  is an explicit answer and never a null — *either suits me* and *I never opened that screen*
  are different facts. Declared at the tail of every rating run that produced a rating, on the
  group deck's declaration step and on the You tab
  ([ADR-0094](docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)). A group
  deck deals no card of a kind the player's intent does not want.
- **Play intent declaration** — the **event-sourced aggregate** that holds one, one stream per
  `(player, sport)`. Separate from the Player profile, which stays free of a sport dimension.
- **Mode** — *defined in the Matchmaking section below, where it belongs.* It is named here only
  because **Play intent** cannot be defined without it, and the two are the pair most easily
  confused: **Mode is one game's kind; Play intent is the player's standing declaration.**
- **Profile photo** — the first of a player's photos, and the one a face on a card shows. A
  player may hold up to three or none; none is not an absence but a **generated court
  poster**, derived from their identity so it is stable across devices.
- **Intro** — **one line a player writes about themselves**: at most 100 characters, no line
  breaks, any language, one per player, and **optional** — a player who wrote none has none,
  not an empty one. The first player-authored free text the platform shows to a stranger, and
  the fence is at the write: a phone number, an email, a URL or a handle is **refused**, because
  the realistic abuse of a line shown before a game exists is contact leaving the app. It reaches
  the player record and nowhere a person is merely named; it is never scored
  ([ADR-0170](docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)).
  **Edited from the You tab**, with the tags and the photos, as one piece of work
  ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §6). _Avoid_: "bio", "tagline", "about", "status".
- **On-court check** — what the platform concluded about whether a photograph shows a racket
  sport, decided at the upload and stored with it
  ([ADR-0129](docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)). **It soft-warns
  and never blocks**: a flagged photo is stored, keeps its position and keeps the lead if it had
  it. Its outcome has **three** values, not two — **passed**, **flagged**, and **nobody looked**,
  which is its own answer and never a spelling of *flagged*
  ([ADR-0138](docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
  Two readers see it differently and that is deliberate: the **uploader** is warned about their
  own photograph, and **another player** is shown only the pass — nothing may tell one player
  that another player's photograph was doubted. **The confidence behind it never crosses on any
  route**, to either of them.
- **Profile commit** — the single idempotent request that ends onboarding's second part,
  carrying every answer at once. Nothing is written before it, so leaving mid-part
  restarts at step 1 ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Keyed
  by a client-supplied **idempotency key**, which the creating event carries so a retry is
  recognised from the stream itself rather than from a table beside it.
- **Player profile events** (durable name / version):
  - **PlayerProfileCreated** — `player_profile.created` / **v3** — the commit, carrying every
    preference and the idempotency key. It gained `gender` and
    `gender_preference` while it was v1, appended with defaults so the rows then in the store
    decoded unchanged, and an absent `gender` means *committed before anybody was asked* —
    never a quieter `PREFER_NOT_TO_SAY`, which is an answer somebody chose. Nothing is
    backfilled. **v2 was the week becoming hours** (`weekly_hours`, [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
    §5); **v3 dropped the search radius** with the Classic play removal (#581). v1 and v2 are
    deliberately unreadable — only `local` ever ran, and a row of an old shape is a decoding
    error rather than a profile folded wrongly.
  - **SocialTagsChanged** — `player_profile.social_tags_changed` / v1.
  - **PhotosChanged** — `player_profile.photos_changed` / v1.
  - **WeeklyHoursSet** — `player_profile.weekly_hours_set` / v1 — the whole week, as the You
    tab's *Save your week* leaves it; empty is a cleared week. It replaced
    `player_profile.availability_changed`, which nothing reads.
  - **LocationChanged** — `player_profile.location_changed` / v1.
  - **GenderChanged** — `player_profile.gender_changed` / v1 — gender is self-declared and
    freely changed, so the correction has an event from the day the field does.
  - **GenderPreferenceChanged** — `player_profile.gender_preference_changed` / v1.
  - **PlayIntentDeclared** — `player_profile.play_intent_declared` / v1 — the sport, the value
    and the surface it was declared on.
  - **IntroChanged** — `player_profile.intro_changed` / v1 — the line as it now stands, or none:
    the You tab's edit, and the withdrawal of a line
    ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §6).
    `IntroWritten` stays the commit's.

**Invariants**
- **A tag id is permanent.** Ids are persisted on accounts, so retiring a tag means hiding
  it from the picker while continuing to honour it — never reusing or renaming it.
- **At least one hour, and blank is absent rather than zero.** Weekly hours are **required** at
  profile commit — one ticked hour of the 112 is a real answer, none is not an answer at all.
  Where a blank week is nevertheless met — cleared afterwards — it means *we do not know*, and
  the player is free for no court hour; it is never read as no overlap and never as any time
  ([ADR-0102](docs/adr/0102-silence-is-never-scored.md)). **An unanswered field is never a
  negative filter**, and requiring the field is how that invariant is kept rather than
  weighed.
- **The grid is never shown to anybody as a calendar.** Not to the people on a card, not as
  free/busy, not exported. Only the hours **everybody** on a card shares are ever drawn — an
  overlap is a fact about the people together, a calendar is a fact about a person.
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
- **Behaviour never rewrites a declaration.** Only the player changes their Play intent; nothing
  the platform watches them do writes it.
- **Intent is per sport, and never transfers between them.** The same person is plausibly a
  competitive padel player and a social tennis player — the same reason levels do not transfer.
- **A narrowed preference costs the player reach, and they are told at the moment of
  setting.** Mutuality means `WOMEN_ONLY` also keeps its holder off every court with a man,
  including men whose own preference is `ANY` — the half nobody would guess. The backend emits
  the reason; the client says the sentence, and learning it from an empty deck is not
  acceptable ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **A profile is one per player, and asking whether one exists is a legitimate question.**
  See the narrowed *there is no onboarded player* invariant above, and
  [ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md).

### Blocks (`backend/app/modules/blocks/`)

One player keeping another off their games. Settled by
[ADR-0095](docs/adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) and
amended by [ADR-0193](docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md):
**a block keeps two people off one court, and the blocker can see it.** **Built**
([#586](https://github.com/Raketa02/Raketa/issues/586)): the aggregate and its two events
(`blocks.player_blocked` v2, no surface), the `BlockQuery` port the new games' pair rule reads,
three routes — block, unblock and **Blocked players** — the record's own-block fact, and the
withdrawal of the blocker's yeses where the blocked person is In. Members lists no longer ask
about blocks, and the record asks only about the reader's own. The player app's Block and Unblock are
[#587](https://github.com/Raketa02/Raketa/issues/587).

- **Block** — an **event-sourced aggregate**, one stream per **ordered** `(blocker, blocked)`
  pair, with a deterministic stream id derived from that pair. **The record is directed; the
  effect is symmetric.** `A → B` and `B → A` are two independent blocks, so one being lifted
  never lifts the other. What it reaches is **one court**: a blocked pair, either way, is never
  dealt a version together, never both **In**, never offered each other's **Rescue** and never
  joined onto each other's **Post**. _Avoid_: hide, mute, ban — it hides nobody.
- **Blocker** / **blocked** — the two sides of the ordered pair. The blocker can see their own
  block. The blocked person can never discover it.
- **Own block** — a block the reader made: the only kind of block a response may carry. Two reads
  carry it, **Blocked players** (the caller's own blocks, each with the person's name, photo and
  when) and the **player record** (whether the reader blocked its subject). _Avoid_: a field that
  answers *either way round*, which would tell the blocked person.
- **Block events** (durable name / version):
  - **PlayerBlocked** — `blocks.player_blocked` / v2 — the pair. **No reason, no free text, and no
    screen.** v1 also named which of the old loop's four screens the block was made from. It still
    folds: that field is read and dropped, and nothing in the store is rewritten.
  - **PlayerUnblocked** — `blocks.player_unblocked` / v1 — the pair.
- **BlockQuery** — the port that answers *is either of these two blocked by the other*, read by the
  one pair rule every route onto a court asks (Proposals' **PlayerFit**). It answers in two shapes:
  a player's whole **exclusion set**, and the **pairwise** question. A third, **directed** read
  answers own blocks, and is only ever asked with the reader as the blocker. **It fails
  closed**: it raises rather than answering *nobody is blocked* when it cannot read the state,
  because an empty answer it cannot stand behind is a safety control switching itself off under
  load.
- **Hold** — the platform stopping a player from starting anything new while an unsettled case
  is open against them. A **held account** is an account under a Hold. Nothing can place one
  today, because the `cases` context does not exist.
- **AccountHoldQuery** — the port the Hold gate reads. Its only adapter today is
  **`NoHoldsExist`**, named for the fact it asserts rather than for being empty.
- **Disabled account** — an account that may no longer be used at all. **Not a Hold**: a Hold
  stops a player starting anything new while a case is open and they can still sign in; a
  disabled account cannot sign in. Two gates that sound alike, from two contexts, with
  different lifecycles and different remedies — so a rule about *account state* must always say
  which one it means
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
- **AccountStatusQuery** — the port the *account active* gate reads: the set of accounts that may
  not be shown. Asked about the subject only, because a disabled reader cannot sign in to ask.
  It and **AccountHoldQuery** are the two gates of `matchmaking`'s **AccountGates**, which the
  player record runs before it reads anything.
- **Report** — *not a term yet.* The wider reporting and moderation story is out of scope; if a
  reason for a block is ever wanted, it belongs to a Report and not to a Block.

**Invariants**
- **A block keeps two people off one court, and reaches nothing else.** Groups, Members lists, the
  player record, booked games and chats already shared are untouched. Both stay in the group, see
  each other in its Members list and can open each other's record. Hiding a member of a crowd
  everybody can see would itself be the tell.
- **Nobody is shown that they were blocked; you can see your own blocks.** A response may carry
  the reader's own blocks, never anyone's block of the reader, which a test over the emitted
  contract asserts. Nothing the blocked person reads names a block, and their read of the
  blocker's record is the same byte for byte whether or not they were blocked. A yes that would
  pair them is refused without saying why, and nobody is notified of a block or an unblock.
- **A block takes back the blocker's yeses until the club confirms, and never touches a
  confirmed booking.** Where the blocked person is In, picks and posts alike, the blocker's yes
  goes: on a proposal still filling by the ordinary **Withdraw**, silently, and on a booking
  waiting for the club as if they left it, so the others In are told they left. Either way it is
  free, and nothing says why. The blocked person's yes stands. A booking the club confirmed stays
  as it is, and leaving it is the ordinary Leaver rule. **Unblocking brings no yes back.**
- **Blocking is idempotent, and blocking yourself is an error.** A second block appends
  nothing, in the shape of `disable()`; a self-block raises rather than no-ops. Unblocking lifts
  only the caller's own block and never 404s.
- **No cap, no cooldown, no rate limit.** Friction on the one control a person has is a tax
  paid to solve a problem the platform does not have.
- **Erasure reaches both sides.** Erasing a player erases every stream they appear in, on
  either side of the pair — which is why a block is never a field on somebody's profile.

### Matchmaking (`backend/app/modules/matchmaking/`)

Decided by [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md).
**Cut back on 2026-10-06** with the Classic play removal
([#569](https://github.com/Raketa02/Raketa/issues/569)): the searches, the line-up route, the deck,
the radar, interest, passes, prompts, the candidate index and the "who fits whom" ranking are gone
([#579](https://github.com/Raketa02/Raketa/issues/579),
[#580](https://github.com/Raketa02/Raketa/issues/580)), and every term that named only them went
with them. **What is left is what the new games call**: the **level window** and the **newcomer
window**, which `proposals`' **PlayerFit** asks of every pair on a court; the **forecast**, which a
Games card and a booked game's screen both print; the hours everybody on a card shares, which its
**Overlap grid** is graded by; the distance from a player's **Location area** to a club; and the two
**account gates** the player record runs. **Nothing here scores one person against another any
more.**

- **Match Fit** — the **pure engine** beside RacketSkill (`app/engines/matchfit/`). It has no
  clock, no randomness, no state and no database, and the types it is handed carry no protected
  characteristic. It no longer scores a pairing: what it computes is how even two sides would be
  (the **Forecast** and its **Split**) and how much of the narrowest week a set of people share.
  The stateful half — loading the ruleset, the gates, the reads off other contexts — is the
  **module** beside it and is deliberately not an engine
  ([ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)).
- **Mode** — a game's **kind**: **Competitive** or **For fun**. **Two values, never three** —
  spelled `SearchMode` in code, a name that outlived the searches. A player with no preference
  still plays a game of one kind, which is exactly why it is not **Play intent**: an intent is a
  standing declaration per sport with three values, a Mode is one game's. They are separate types
  so confusing them is a compile error. It picks the **level window**'s tolerance, and a
  competitive game is the one whose result is counted.
- **Ruleset** — the named, dated set of **numbers** the level window and the forecast read: each
  Mode's **level tolerance**, and the **balance rules**. **It is not a profile.** A Player profile
  is a person's own account of themselves; a Ruleset is the product's opinion about how even a game
  must be, and the two words must never be swapped. It ships with the code and is validated on
  load, so a malformed one stops the process from starting; it is **never selected by the
  environment**. One is released, `2026.09.15-a`. When the ranking went, its other sections were
  deleted from that ruleset in place rather than released under a new name, because no number the
  new games read moved, and the two older rulesets were deleted
  ([#580](https://github.com/Raketa02/Raketa/issues/580)). The next number that moves is a new
  name.
- **Level window** — how far apart two Levels may be for their holders to share a court:
  `|Δμ|` below the Mode's **level tolerance**. One number per Mode, the same number the
  forecast's curve saturates at, so the window and the forecast can never drift apart
  ([ADR-0103](docs/adr/0103-where-the-curve-saturates-the-gate-begins.md)). It is asked of
  **every pair** a court would seat — by the proposer, the fill and a rescue, through
  **PlayerFit** — and a **Post**'s level range around its poster starts from it. _Avoid_:
  "level gate", the searches' name for it.
- **Newcomer** — a player within **14 days** of the profile commit that made them playable. A
  **predicate over a date, never a stored flag**: a flag would need a loop to keep it true, and a
  date needs nothing. The days are a ceiling and not a definition, so a player who has played
  nothing still stops being new.
- **Newcomer window** — the period a Newcomer is in, and it has exactly one power: it **tightens
  the level window for both sides of a pairing** to the competitive tolerance, whatever the game's
  kind, so a bad first game cannot arrive through the veteran's side of it. It bends nothing else
  ([ADR-0113](docs/adr/0113-newness-changes-the-gate-never-the-weights.md)).
- **Gate** — a hard exclusion, never a weight. **A gate that cannot be evaluated excludes.** Two
  sets are left: the **pair rule** every court asks — no block either way, mutual **Gender
  preference**, Levels within the **level window** (Proposals' **PlayerFit**) — and the two
  **account gates**, a **Hold** and an account that may not be shown, which `AccountGates` runs for
  the player record. **Age is not a gate**: whether somebody may hold an account at all is a
  platform precondition in `users`, an attestation at sign-up and **never a date of birth**, so
  *may you hold an account* and *may these two share a court* stay different questions in
  different contexts
  ([ADR-0124](docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
- **Forecast** — how even a game between two sides would be, as a percentage, read side against
  side from the people's Levels and Uncertainties. **One function reads it** —
  `forecast_the_sides` — for a Games card and for a booked game's screen alike, so one court has
  one figure. A **provisional** forecast answers with a seat still empty, reading a half-empty
  side as if the missing player matched the one already there. Provisional is a property **of**
  the forecast and never a flag beside it, so the number cannot be rendered without its caveat
  ([ADR-0108](docs/adr/0108-a-forecast-is-a-route-not-a-search.md)). The proposer draws a card's
  sides as the evenest arrangement it forecasts; a booked game's sides are the ones the fill
  drew, and its forecast is read for the reader, *your side* first
  ([ADR-0161](docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)). Anybody with no Level
  in the sport leaves it absent, never guessed.
- **Split** — the two **side** strengths a **forecast** was read from, and the signed gap
  between them: *your side*, *their side*, and *your side minus theirs*. The evidence behind the
  percentage — the forecast says *how even*, the split says *between what and what*, on the same
  scale a **Skill** rating is read on. A side's strength is **not the mean of the two people on
  it** (the weaker partner sets more of it), which is why it is a number only the engine has and
  why a client may never compute one. What crosses is an input to a figure already served, never
  a second score
  ([ADR-0136](docs/adr/0136-the-split-is-evidence-for-the-forecast-not-a-second-score.md)).

**Terms this context refuses**
- **Game format** — *mixed doubles*, *women's doubles* and the like, as a dimension of a game.
  Deliberately does not exist: a game carries a **Sport**, and the sport fixes the seat count
  (`backend/app/kernel/sports.py`, which refuses a `Format` dimension for the same reason). Who
  may sit in a seat is answered by **Gender preference**, which is about people and says so
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)). A
  *Mixed pairs* **Post** is a poster's choice of who may join one game, not a format.
- **Activity recency** — *active 2 hours ago*, a green dot, *active today*. Deliberately does not
  exist on any surface. This product has no presence indicator beyond **Typing** in a room.
- **A bio.** Superseded 2026-09-14 by **Intro** ([ADR-0170](docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)): one line, fenced at the write, is the
  moderation story the refusal asked for. What is still refused is a paragraph, a second field,
  and any free text that is scored.

**Invariants**
- **A gate that cannot be evaluated excludes.** Absent evidence makes a gate *fail closed*; an
  absent gate is an open door, never a standing-down signal. A person with no profile or no Level
  in the sport fits nobody.
- **A safety gate is read live, on the side that owns the truth.** The pair rule reads the blocks
  off the log, each person's gender and preference off their own profile, and their Level off
  rating's published read — never a projection that may be a tick behind a block.
- **In a four, every gate binds all six pairs.** A block, a **gender preference** and the level
  window are checked between every two people who would share the court — a player shares ninety
  minutes with all three, and a gate that only asked about one of them would protect nobody else
  in the game ([ADR-0116](docs/adr/0116-in-a-four-every-gate-binds-all-six-pairs.md)).
- **A protected characteristic may gate; it may never score.** Gender reaches the pair rule and
  nothing else, and the engine's types carry none
  ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
- **Absence has two spellings and they mean different things.** *Omitted* is *this does not
  apply here*; *null* is *this applies and the answer is a measured nothing*. It is the
  measured-versus-invented test carried to the wire, and the two generate as different types so
  a client cannot treat them alike.
- **A forecast is recomputed, never recorded.** Its inputs are its arguments and a released
  ruleset, so asking twice gives the same answer and no record is needed to prove it
  ([ADR-0108](docs/adr/0108-a-forecast-is-a-route-not-a-search.md)).

### Games (`backend/app/modules/games/`)

Settled by [ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) on
[#303](https://github.com/Raketa02/Raketa/issues/303). **The context that knows a game was
played.** It is **event-sourced**, and that revises the deleted ADR-0034, which argued a record
about a product — courts, money, departures, four cancellation flags — that the 2026-08-25 reset
removed. **A Game is opened by a Booking** when it reaches *booked*
([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md), built by
[#541](https://github.com/Raketa02/Raketa/issues/541)): the Booking holds where, when and the
money, and the Game holds what happened on the court. Since the Classic play removal
([#569](https://github.com/Raketa02/Raketa/issues/569)) a Booking is the only thing that opens one.

Its subject is the span between *it is booked* and *there is nothing more to say about this
evening*. Nothing about where, money, or the conversation belongs here, and neither does anything
about how good anybody is — that is the rating context reading this one.

- **Game** — one booked game and its result. **Opened by its Booking**, in the transaction that
  made it *booked*, and never by a request: nothing a client sends can produce one, which is what
  makes *these people are playing this* a fact rather than a claim. One game per booking, for
  ever. It reaches **five ends**: three folded from the record and the clock, a fourth —
  **Called off** — that is announced, and a fifth — **Started short** — that the hour reads off a
  line-up with a seat still open. **The fourth end says who**: `called_off_by`, or nobody when it
  is the club's cut-off or the club taking the court back
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md),
  [ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md),
  [ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)): no
  player can call a game off.
- **Line-up** — who is on the court and on which side, **frozen until somebody leaves it**
  ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)). The sides
  are the ones the fill drew; nothing in this context moves anybody on its own. It moves in
  exactly two told ways, both told by `bookings` in the transaction of the act that caused them:
  a **Departure** opens one seat, and a **Rescue** taken fills it, the rescuer sitting where the
  leaver sat. **An open seat is a seat** — drawn empty, in its place, never dropped — and a result
  is refused while one is open.
- **Departure** — a player **leaving a booked game** before it is played: the Booking's **Leaver**,
  told here as one open seat. It never moves `planned_at`, which keeps meaning *when it became a
  game*.
- **Kind** — **counted** or a **friendly**, the game's **Mode** as its proposal carried it:
  competitive is counted, for fun is a friendly. Stamped when the game is booked and never derived
  at the end. A friendly is a thing people *choose*: reclassifying a counted game because nobody
  typed a score would hand a player the exact evening they said they did not want, and would give
  one word two meanings.
- **Result** — *we played, here is the score*. **The entry is the record that the game
  happened**, and it can be made until the game's **entry window**, which runs from the end of
  its hour, closes.
- **Score** — the sets, absolute rather than from anybody's point of view. **A score names a
  winner**: a level set has not finished and none of the four sports produces a draw, so a level
  score is refused. *Set* is used for whatever the sport calls its unit.
- **Proposal** — a score on the table, **one per side**. The cap is what bounds an argument to
  two rounds, and it is what makes silence safe to read as agreement. *Not* the **Proposal** of
  Proposals, which is a game still filling: this one is a score, and the word is always read in
  its context.
- **Correction** — the proposing side revising its own score while the other side has not
  answered. **Not a second proposal**, and **any member of that side may make it** — the rule
  that makes a teammate's agreement worthless is the same rule that makes a teammate's objection
  credible.
- **Counter** — the other side's one turn, and **it carries a score**. There is no bare
  rejection: a rejection carrying nothing would be free and always optimal for the loser.
- **Acceptance** — agreement, **from the opposing side only**, because a teammate agreeing with
  a teammate proves nothing. **One opponent suffices.**
- **Acceptance grace** — how long an acceptance waits before it settles anything, measured from
  the *score* and not from the tap. Inside it a counter still wins, so a partner who is quick to
  their phone cannot close the door on an opponent who has not read the score yet.
- **No-show report** — the players who came marking one who did not, where they would enter the
  result. The reported player has **a day to dispute it**, and a player the club **checked in**
  cannot be reported. A report is the entry for that game — no score stands beside one — and
  whatever it comes to, **the game does not count**. One that stands its day is the strongest
  mark a record carries.
- **Standing** — what a game *is* right now: `AWAITING_ENTRY`, `NEVER_PLAYED`,
  `AWAITING_ANSWER`, `CONFIRMED`, `UNSCORED`, `CALLED_OFF`, `STARTED_SHORT`,
  `NO_SHOW_REPORTED`, `NO_SHOW`. **Derived from the record and the clock, never stored** — and
  never announced, with one exception: `CALLED_OFF` is a decision, folded off `GameCalledOff` and
  read first ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). It is an
  end, and it is **neither an evening nor a ghost**: a ghost is silence and this was an act, so
  it is in no tally and moves no **Strand**. Neither `STARTED_SHORT` nor `NO_SHOW` is in a tally
  either. Spelled `GameStanding` in code and on the wire, a name kept from when Challenges
  published a `Standing` component of its own: renaming a component is a change to types a
  shipped app generated. The same is true of `GameSide`.
- **Counted game** — a counted-kind game somebody said was played, **scored or not**. What the
  player record's skill panel counts.
- **Ghost game** — a booked game whose entry window closed with nobody ever saying it happened.
  Kept distinguishable from a played game, because familiarity is about people who actually
  played. A **called-off** game is not one: the window did not close on silence, somebody ended
  it.

**Invariants**

- **Silence confirms.** A lone score nobody answers stands when its window closes, and the game
  counts. There is nothing anywhere in this context called *confirm*: a result is agreed when a
  clock passes, and a clock is nobody's request.
- **Two standing scores nobody accepts leave the game unscored — and an unscored game is an
  evening, not evidence.** It is in history, it is a counted game, it establishes that these
  people have played together, and **it moves nobody's Level.**
- **No player is penalised for not entering or not agreeing a result.** Not the silent loser,
  not the four who all went home, not the side whose counter went unaccepted. **This is why
  *confirms results* is not a Player Score strand** — and why the strand that does read this
  context's records counts **answers**, where a counter scores exactly as an acceptance does,
  so disagreeing still costs nothing. See below.
- **We will not arbitrate.** Two people who were both on court and cannot agree what happened is
  not a result, and Raketa will not invent one. A settled result is final: no support correction
  path and no reversal.
- **The people who may act are the people who were on the court**, and nobody else, ever.
- **Nothing announces a conclusion the record already implies.** There is no `ResultConfirmed`,
  no `GameUnscored` and no `GameNeverPlayed`: a derived standing has exactly one place to be
  true. `GameCalledOff` is the one event that announces an end, and it may because no arrangement
  of the record could reach it
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).

### Conversation (`backend/app/modules/conversations/`)

Settled by [ADR-0146](docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) on
[#332](https://github.com/Raketa02/Raketa/issues/332), with its lifetime from
[ADR-0153](docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md).
**Built.** Six routes are on the player contract, a room is opened and told through the outbox by
a context that does not know it exists, and it is **destroyed** once the episode it was opened for is
over — derived on every read, and made real by an hourly sweep
([#359](https://github.com/Raketa02/Raketa/issues/359)). **Since
[#575](https://github.com/Raketa02/Raketa/issues/575) a room is opened only by a booked game**:
every chat belongs to one game, opens when it is booked, and is reached from that game's details
([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6). There is no
inbox of rooms.

**The place the people booked on one game talk about it.** It is deliberately **not** called
`Chat` — that word promises messaging between anybody, searchable and permanent, and this context
refuses all four. `games` used *conversation* in prose for the result argument; that argument's
terms are **Proposal**, **Correction**, **Counter** and **Acceptance**, and the word belongs to the
aggregate that needs it.

Its subject is the span between *the game is booked* and *there is nothing left to say about it*.
Nothing about when, where, money or the result belongs here — it is **told** about all of them.

- **Conversation** — one purpose-bound thread, opened by its **booked game** and never by a
  request. **The purpose is the episode** — play the game and find out what happened — which is
  what decides when it ends. Named on the wire by its booking: `booking_id`.
- **Member** — somebody on this game's court **right now**. **Derived, never stored**, from the
  game's current line-up, so a room moves with its court: a **Departure** takes the leaver out and
  a taken **Rescue** brings the rescuer in. A room stores no membership fact at all, so it can
  never hold somebody the court does not. **Not a Group member**, who belongs to a Group and is on
  no court by belonging.
- **Message** — what a player typed. Content, crossing as-is, with an author in the ordinary
  sense.
- **System line** — what happened, as a **code and its values**, rendered by the client. **Not a
  Message with a kind**: the backend sends codes and never display text
  ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), and nobody typed
  *We played*. The two share one stream and one sequence number and are two shapes in it. One code
  is written today, `GAME_PLAYED`; the others were written into rooms a challenge opened, and stay
  only so that a stored line still folds.
- **Sequence number** — a conversation's own count of what has landed in it, minted on append and
  **gapless**, because a count that skips is not a count
  ([ADR-0147](docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)).
  The cursor for ordering, paging, de-duplication and reconnect. **No reader may infer loss from a
  gap** — the promise is the server's, and nothing is permitted to depend on it.
- **Typing** — *somebody is typing in this room, right now*, and the whole of the presence this
  product has
  ([ADR-0156](docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  A **heartbeat and never a state**: a client says it while somebody types and stops saying it when
  they stop, and there is deliberately no *stopped* — every way an app can vanish is a way a
  *stopped* fails to arrive, and each of them would leave a room saying somebody is typing for ever.
  **A short expiry is what clears it**, which makes the failure mode the indicator *vanishing*
  rather than sticking. It is **not an entry**: it moves no Sequence number, is stored nowhere, and
  is gone within seconds of the last keystroke. _Avoid_: reading it as *online*, as *last seen*, or
  as evidence of anything — there is no *who stopped*, no *since when*, and no way to ask about a
  moment other than this one.
- **Lifetime** — a conversation lasts as long as the **episode** it was opened for, and is then
  **destroyed, not delisted**. It ends at the earliest of the game's **entry window** closing,
  measured from its booked hour, and a grace after somebody says they played
  ([ADR-0153](docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
  A game **called off** destroys its room in the same act, with no line written
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). **A room with no game
  has ended**: nothing opens one any more, so one left from before #575 answers
  `conversation_not_found` and the sweep destroys it.

**Invariants**

- **A conversation is told, and tells nothing.** Its lines are written from events `games`
  publishes through the outbox, and **`games` does not know it exists**. It is a subscriber, never
  a participant in anybody's transaction.
- **There is no messaging between strangers**, and there is no conversation without a booked game
  behind it. That refusal is the product: it is what keeps this a sports app rather than a place
  people are reached.
- **No system line announces a derived standing.** There is no *Game on* line — the same rule
  `games` states, applied to a stream: a folded standing has exactly one place to be true, and it
  is not a sentence in the backlog.
- **No sentence is ever stored.** A rewritten line rewrites the whole history, which is what a
  stored string could not do.
- **Presence stops at *is somebody typing right now*.** There are no read receipts, no `seen_at`,
  no online and no last-seen, and each is refused on the same property: nothing about Typing is
  stored anywhere, so there is nothing here for one of them to be built out of
  ([ADR-0156](docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).

### Player Score (`backend/app/modules/player_score/`)

What the platform has watched a player *do*, as distinct from how well they play. **One number
in the UI, six strands underneath it**, each published in its own right on the player record. The
words are the player's: they are read on the player's own screen, and nothing that decides who
plays with whom reads them.

**Three of the six have a source and three do not** — decided by
[ADR-0140](docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md),
which also settles the clause ADR-0137 opened about whether *shows up* survives at all, and by
[ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md), which adds
the third. **The three changed once without the count changing**
([#544](https://github.com/Raketa02/Raketa/issues/544)): *answers challenges* stood down and
*keeps plans* came up on booked games, and the published weights were not touched.

- **Player Score** — the blended number a player sees, out of a hundred. Computed from what
  happened, never from opinions and never from results: **losing costs nothing here.** The
  blend is over **the strands that are there**, renormalised, so a player the platform can see
  two things about is comparable to one it can see five about, and neither is credited for a
  record nobody keeps.
- **Strand** — one of the six things the score is made of. Each is a record of **opportunities**
  and what came of them, and each is published in its own right. An opportunity is something
  that **fell due**: a strand never counts a question still waiting for its answer.
  - **Shows up** — whether the game gets played at all. **Live.** The opportunity is a game that
    settled — one somebody said had happened, or a **Ghost game** whose entry window closed on
    silence — and the good outcome is the game. **A ghost is charged to everybody who was on
    that court**, because nobody proposed anything and nobody countered anything: what is priced
    is an arrangement that dissolved, and there is nobody in it to blame.
  - **Answers challenges** — whether an invitation to a game got an answer inside its window.
    **Stands down**, and has nothing to count since challenges went: a yes on a Games card is
    silent and waits for nobody, so there is no silence to price.
  - **Answers about results** — whether a score put in front of a player gets an answer inside
    its window. **Live** ([ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)).
    The opportunity is a **score put to you**: the entry that records *we played* records a
    score in the same act, so one side opens and the other is asked, and once both sides have
    put a score up nobody is asked anything further — the opener facing a counter may only give
    way, and pricing that would price surrender. **Accepting counts and countering counts**, so
    this is the second strand where a no scores; what it prices is silence until the window
    closed. **It is not *confirms results* under a new name** — see below — and it is the only
    strand that **forgets**: opportunities older than twelve months fall out of it.
  - **Keeps plans** — whether a booked game the player held a seat on reached its hour with them
    in it. **Live** ([#544](https://github.com/Raketa02/Raketa/issues/544)), read off `bookings`:
    the strand keeps its name, and a booked game is the plan: *kept* when its hour comes with
    every seat held, and *broken* by leaving it so that it is called off at the cut-off, or after
    the cut-off with nobody taking the seat.
  - **Settles up** — whether a court share that fell due was settled without a case. **Stands
    down:** there is no record of its own to read — a seat's money is taken before the game
    exists. It is the **historical record**, never the live case — the open case is the Hold.
  - **Sportsmanship** — what opponents said afterwards. A mean, not a ratio. **Stands down,
    and now permanently**
    ([ADR-0158](docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)). The
    surface it was waiting for exists — see **Sportsmanship** below — and the reason it stays
    down has changed rather than lapsed: **it is not a strand and never was.** A star average
    is not a ratio out of a hundred, so it cannot be a term in a weighted mean over ratios;
    and nothing that decides who plays with whom may read it in any shape, because it is the one
    thing here a person can weaponise with no appeal route behind it. It is published as **its own figure**, on
    the player record, under its own heading.
- **Confirms results** — **struck, and it stays struck**
  ([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). It read *whether a
  counted game gets confirmed, so it counts*, and it cannot be published honestly: **an
  unconfirmed result is a fact about a pair and a strand is a verdict about a person**, and
  every denominator tried on it docks somebody the Games context refuses to penalise — both
  sides of an honest disagreement included. Withdrawing it rather than leaving it unbuilt is
  ADR-0098's own rule about a demand nobody can satisfy; a strand nobody publishes stands down and
  the survivors renormalise. `ReliabilityStrand.CONFIRMS_RESULTS` came out with the provider, in
  ADR-0140.
  **Answers about results is not this row coming back**
  ([ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)). Silence
  already *confirms* a lone score, so a row counting confirmations finds ignoring and agreeing
  indistinguishable and the only unconfirmed games are the ones two people disagreed about — it
  would be a row counting **disagreements** under a word that sounds like diligence. The
  replacement counts **answers**, where a counter is as good as an acceptance, so the
  who-was-wrong problem is dissolved rather than solved. The 15 ADR-0140 set aside rather than
  redistributed is what it enters at.
- **Opponent variety** — how widely a player spreads their games: how many **different
  people** over how many **counted games**, across their whole record. **Not
  `player_score`'s, and it now has a consumer:** it was contracted here on behalf of two
  consumers and [#164](https://github.com/Raketa02/Raketa/issues/164) and
  [#175](https://github.com/Raketa02/Raketa/issues/175) struck both, so ADR-0098 was amended to
  withdraw it — *a consumer-driven contract with no consumer is withdrawn, not carried*. It
  returned in [#380](https://github.com/Raketa02/Raketa/issues/380) exactly as that amendment
  said it would: as **the player record's** demand, signed for by `player_record`, answered by
  `games` and never by this context. It is **not a strand** — it prices no promise and is in no
  weighted score; it is context for a Level, because a low figure is somebody playing the same
  few faces every week, whose rating may be narrow but untested. See *Player record* below.

**Invariants**
- **No record is not a bad record.** A player without a score is not bad and not average — they
  are **absent from the answer**. The same principle the rating engine already applies to skill. A strand nobody can
  publish is absent the same way, and neither is ever a `0` or a `0.5`.
- **This context keeps no record of its own.** It has no aggregate, no table and no migration:
  every strand is folded out of `games`' and `bookings`' records when somebody asks, through each
  one's published port. A stored
  score would be a second place for *did that game happen* to be true, and the copy would be the
  one that got believed.
- **The score is a memory, and it fades with new evidence.** Decay belongs here, on the side
  that owns the record; a consumer that applies its own would be counting the same forgetting
  twice. **The ratio is the fading** — one no-show among forty games weighs almost nothing —
  and there is **one** window, on one strand, named rather than general: *answers about results*
  forgets after twelve months, because turning up is a commitment somebody made and answering a
  score is a habit of opening an app, which is cheap to fail by accident and must therefore be
  possible to work off.
- **The published number is the player's.** Its weights are **35 / 20 / 15 / 12 / 10 / 8** and
  live in this context, never in a ruleset: a release must not change what somebody's own profile
  says about them. The player record prints it **beside the rows it is the mean of**, and a
  group's members list reads it too. The **strand ratios themselves** cross on the record, as a
  raw pair and the figure derived from it; the weights never do.

### Sportsmanship (`backend/app/modules/sportsmanship/`)

What the *other players* said about being on a court with somebody — the one thing on the
player record the platform cannot count for itself, and the first part of that sheet that
**stores** anything rather than deriving it
([ADR-0158](docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).

**The word *rating* is Skill rating's**, and this context pays the cost of arriving second:
everything here is spelled **stars** or **the card**, and a bare *rating* on this platform
still means the μ/σ a player holds in a sport.

- **The card** — one court, one rater, answered once. Everybody from one game is on it
  together, which is what keeps a busy month from becoming a chore list. **Submitting closes
  it for ever**: a blank stays blank, there is no correction path, and a card answered with
  everybody blank is closed too — an explicit *I am not rating anyone* is an answer somebody
  decided.
- **Stars** — one to five, whole. **No zero**, because a rating that reads as *worthless* is a
  weapon out of proportion to a tap and one star already dents an average about as hard; **no
  halves**, because five taps is one number.
- **Blank** — somebody on the card who was given no stars. It is spelled by **absence** and
  nothing else: not a zero, not a null, not a row. Leaving somebody blank tonight keeps
  whatever you last said about them, because a blank is the absence of an opinion and never
  the withdrawal of one.
- **Settled court** — the courts a card may be drawn for. `games`' word, **narrowed**: over
  there a booked game nobody ever claimed is settled too, and there is nobody to rate for an evening
  that did not happen. Here it means **played, and over** — confirmed, or unscored because two
  sides disagreed and both windows closed. **An unscored game is in**: two people who cannot
  agree what the score was were still on a court together for two hours.

**Invariants**
- **You rate everybody else who was on the court.** In doubles both opponents **and your
  partner** — the person who saw you play closest was on your own side of the net — and in
  singles the one opponent. There is therefore **no *side* in this context at all**, and
  rating yourself is refused by the same rule that refuses a stranger.
- **Only a rater's most recent stars about a person count, and the collapse is the primary
  key.** Two friends who partner every week would otherwise supply ten of each other's twelve
  ratings, and the average would drift towards what one regular partner thinks. Collapsed, that
  history gives **three** ratings, and the count printed beside the figure means *how many
  different people have an opinion*.
- **No individual rating is returned to anybody, on any route, in any shape.** Not to the
  subject, not to the rater who gave it. What is published is an **average** beside the
  count of distinct people behind it — **to every reader, the subject included**, since
  [ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §5.
  It used to be a coarse band and no count for the subject, because an average plus a count is a
  subtraction that names each new rating and they know who they played; that cost is accepted by
  name, and what blunts it is what this context keeps — the collapse, the fifty-rater window, no
  zero, and matchmaking never reading it.
- **The published figure** — the mean of what other players said, out of five to one decimal,
  beside how many different people it rests on. **From the very first rating**, because the
  count does a minimum's work honestly: `3,0 / 5 · 1 player` visibly reads as one person's
  opinion. **Over the fifty most recent raters**, each contributing the one answer that
  stands — fifty *people* and not fifty ratings, or a weekly partner would eat twenty of the
  slots and hand the farming problem back through a side door. **Nothing is trimmed at either
  end**: trimming is the platform deciding which raters were wrong, a larger claim than
  publishing the number.
- **The band** — *retired* ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §5).
  It was the three steps the subject was told instead of the figure — **good** from 4,0,
  **mixed** from 3,0, **poor** below, coarsened from the published figure. The subject now reads
  the figure; the band is one amendment away if honest answering falls off.
- **Matchmaking never reads it.** A reader seeing the figure and deciding for themselves is the
  product working; the app demoting somebody silently on the same evidence, with nothing they can
  answer, is not. An import contract enforces it, because nothing else would go red the day a
  rule about who plays with whom started reading a star average.
- **Not rating costs nothing, and the omission is not recorded.** No strand, no obligation, no
  penalty, and nothing anywhere that says a card went unanswered.

### Player record (`backend/app/modules/player_record/`)

**What the platform will say about one person to one reader**, current at the moment the
sheet is opened — and the context that decides whether it says anything at all
([ADR-0159](docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)).
It is `player_score`'s shape with a second job: **no aggregate, no table and no migration**,
every fact read through the owning context's published port, and one rule of its own —
**admission**.

- **The player record** — a *person*, not a pairing: it answers *who is this* about one. It is a
  **route**, live, about one person, and read at most a few times a day — opened from a face on a
  Games card, a game's details, Fill in, Post a game or a group's Members list.
- **A disclosure** — the thing that entitles a reader to open a record. Three strands, and
  *being the subject*: the pair **played together** — were both on one game's court — they
  **share a Group**, or the reader **runs an Official group** the subject is in (#575). **Nothing
  else, and nothing expires but a group**: a game the pair were both on discloses for as long as
  they are both on it, played or not, while a group discloses its members only while they are in
  it and only to whoever runs it now.
- **The metered rows** — what the platform *watched* this person do, under the card headed
  *counted by the system, not written by people*. Each is a **raw pair and its figure**: how
  many opportunities fell due, how many went the way the strand is named for, and the
  percentage out of a hundred. Beside them is **the reliability pill** — the published Player
  Score, so a player working their record back up can watch it lift. One row per live strand of
  `player_score`'s, read through that context's published port and never recomputed here. **The weights are not on the
  wire**: they are a fact about how the number is made rather than about the person.
- **Run of form** — a player's **last five counted results, oldest to newest**, each a win or a
  loss, in the record's skill panel beside their **counted games**. **Outcomes in order and no
  dates, at any granularity**: a moment beside one of them would be activity recency, which no
  surface carries in any shape. Fewer than five is a real answer and it is **never padded** —
  three results are drawn as three. A count includes a game nobody agreed a score for and a Run
  of form does not — *an unscored game is an evening, not evidence*
  ([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
- **The gates** — re-run live on every open, because a disclosure made in August is not a
  permission to show somebody in December: the disclosure entitles a reader to *ask*, and the
  gates decide. They are the gates about **accounts** — a Hold, an account that may not be shown
  — and the reader's own Hold, and **no preference**: every strand is a court or a group that already put the pair
  in front of each other, so the gender preference is asked of nobody here.

**Invariants**
- **A record is read through a prior disclosure, never about a person.** Otherwise a route
  taking a player id is a player-enumeration endpoint, and a UUID being hard to guess is not
  an authorization model.
- **The refusals are one refusal, byte for byte.** *Never disclosed*, *held* and *no such
  player* answer with the same status and the same body. Naming the gate tells a reader
  something about a person they may not be shown; separating *never disclosed* from *no such
  player* answers *is this id real* about a stranger. **A block is not among them**, in either
  direction ([ADR-0193](docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2, from #586): the blocker opens the record to unblock, and the blocked person's read is the
  same whether or not they were blocked.
- **The gate runs before any provider is touched.** A read that fetched a stranger's handle
  and photograph and *then* refused would have done the lookup the rule exists to prevent.
- **The server says whether a record is the reader's own.** The client never derives it by
  comparing identifiers, and the subject's id is not on the response for it to compare.
- **This context declares its own ports and its own types.** It borrows no other context's
  domain types, so another context's shape does not reach the record by the back door.
- **A career statistic is unbounded, and its read takes one player.** *Opponent variety* is
  every counted game the platform has recorded, with no window and no decay. Because the fold
  behind it is unbounded, the port answers about **one person and never a collection**: the fence
  is the signature, and a set-shaped version would be an invitation to call it over a list.
- **A raw pair crosses, and the sheet divides it.** *Fourteen of twenty* and *seven of ten* are
  the same share and different claims, so the record publishes the two counts and no
  percentage — the same honesty the metered rows print their raw fractions for.
- **A figure the platform acts on is served, and one it does not is not.** That is why a
  metered row carries its percentage and opponent variety does not: a strand's figure is
  derived in exactly one place so that two surfaces cannot print two roundings of one record,
  and a client dividing the pair itself would be the third. Variety prices no promise and nothing rounds it, so the division is the client's.
- **A missing zone is omitted whole, never nulled or emptied.** A player with no publishable
  strand has no reliability section at all — no `player_score` to draw a red pill from and no
  empty list to head a card with. The four absences on this sheet are four different
  questions: rated in nothing, no counted game ever played, nothing ever fallen due, and
  nobody having said anything.
- **No zone depends on who is reading.** *What other players said* crossed as a band to its
  subject until [ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §5;
  it is now the figure and its count for every reader, and the sheet about you is one answer
  retitled like every other zone. `is_self` still retitles the sheet and drops the distance.
- **What people typed sits under its own heading.** The record card promises *counted by the
  system, not written by people*, which is what every metered row under it rests on; the
  sportsmanship figure is the one thing here somebody typed, so it is a second zone rather
  than a fourth row. Two headings, no lie.


### Club

Settled by
[ADR-0182](docs/adr/0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md)
on [#501](https://github.com/Raketa02/Raketa/issues/501), and built by
[#503](https://github.com/Raketa02/Raketa/issues/503). Its **Courts** and how it sells them through
Raketa were settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
§3, §5 and built by [#535](https://github.com/Raketa02/Raketa/issues/535); connecting its payments
by [#537](https://github.com/Raketa02/Raketa/issues/537).

**A place where racket sports are played, known to the platform because it signed up.** Players
search clubs to set a group's home and to find groups; the club manages its own facts from the club
website, and lists there the courts, hours and prices it sells through Raketa.

- **Club** — an **event-sourced aggregate**: a name, a district, a city, **the sports it offers**
  (a non-empty subset of the four — they *filter* the `Sport` registry and never extend it) and
  **a precise point on the map**, stored as the club dropped it, because a club is a public place
  and not a person's whereabouts. Its details may change at any time, except that a sport one of
  its **Courts** plays, or an **Official group** declares, cannot be taken away — each refusal names
  the court or the group. **Not verified**: nothing checks that a club is who it says it is. **Not
  a court**: a club *has* Courts (below), and *"a court at [club] is free"* speaks of one of them.
  _Avoid_: venue, centre, facility, location (that is a player's **Location area**).
- **Club account** — the club's sign-in: **one email and one password, shared by the desk**,
  created with the club. **A separate identity from every User**: its email is unique among club
  accounts and may also be an unrelated User's, with a different password. It signs in **only on
  the club website**, never in the player app, and is never matched, rated or shown to a player.
  _Avoid_: club user, club login (as a noun), club admin.
- **Home club** — the Club a **Group** belongs to. **Required.** A Player group's is chosen at
  creation and never changes; an Official group's is its club. Distances to it are measured from
  the reader's Location area and printed as everywhere else. _Avoid_: base, venue, home court.
- **Club courts** — an **event-sourced aggregate, one stream per club, filed under the club's own
  id**: its Courts and their Raketa hours, its Exceptions, its Prices, its Way of working and
  Raketa settings, and whether it is Paused. **Born by being used** — nothing is written at
  sign-up, and a club that has set nothing reads no courts, no way of working and the default
  settings. A stream of its own rather than more events on the Club's, because the Club's is what
  every player's home-club search is built from.
- **Court** — one physical court at a Club: a **name** the club uses (*Court 2*, *Kort centralny*;
  1–40 characters, unique at the club ignoring case), **one sport** from the club's own, and
  **indoor or outdoor**, which a card shows. **Offered** to Raketa, or **switched off** — kept,
  with its hours, selling nothing new, whatever is booked on it. **Deleted**, or given another
  sport, only while no booking is ahead of it. Players never pick its **number**: a card or a post
  names a court hour at a club, and the number is given at booking. _Avoid_: pitch, field.
- **Raketa hours** — the hours of an ordinary week a Court is offered to Raketa: **the player's
  own Weekly hours grid**, seven days by sixteen one-hour cells from 07:00 to 23:00 — an hour
  outside it could never match anybody — with **no floor**: a court with none offers nothing yet.
  One save may give the same week to several courts.
- **Exception** — hours a club closes **without touching its Raketa hours**: a local day or a run
  of days, whole or between two hours, on **every court** — one added later included — or some,
  with a **reason** for the club's own records that no player reads. **Refused over a booking**,
  which the club cancels instead, and allowed over hours that only have cards on them; the cards
  move to another court or disappear. _Avoid_: closure, block (a Block is between two players).
- **Price** — what a court-hour costs, **per sport**: a standard price, and optional **price bands**
  — weekdays or the weekend, between two hours — that price the hours they cover differently;
  bands of the same days never overlap. **Integer grosze**, from 10 to 1 000 zł, and it **splits**:
  a price that does not divide into whole grosze among the sport's seats is refused rather than
  rounded. A new price reaches **new cards only**.
- **Share** — the court hour's price divided by the seats — four for padel and badminton, two for
  tennis and squash — exact to the grosz, fixed on the card and never changed by a later price.
- **Court hour** — one court at one club for **one hour**. Every game lasts exactly one hour. The
  **sellable court hours** of a club are what it can sell through Raketa: its Raketa hours, less
  its Exceptions, less what bookings hold, less every hour past its Book-by, each priced by its
  band or the standard price — **derived, never stored hour by hour**, only for a club that is
  **Live**, and published to other contexts through a port.
- **Way of working** — how a club sells through Raketa, **one for the whole club**, chosen on its
  own and changeable, the change applying to hours not yet booked: **Only Raketa** (Raketa sells
  alone until the **release lead**), **Instant** (both sell; a Raketa booking is final) or **On
  request** (the club confirms each full game within its **time to confirm**).
- **Raketa settings** — the terms a club **confirms**, its first save doing so defaults included:
  the release lead (Only Raketa; 1–13 days, default 3), the **Cut-off**, the **minimum notice**
  (Instant and On request; 1–48 h, default 2), the time to confirm (On request; 5–60 min, default
  30 — never more than the shortest minimum notice), **other clubs' courts** for its groups (off
  by default, within 10 km), **check-in** (off) and **Paused** (off). Each bound is domain, never
  configuration. Confirmed only once a Way of working is chosen, since which of them matter
  depends on it.
- **Cut-off** — the club's free-cancellation deadline, a Raketa setting (0–72 h, default 24 h
  before). Leaving before it is free; a game still short at it is called off.
- **Book-by** — the latest moment a proposal can still fill: the release time (Only Raketa) or the
  start minus the club's minimum notice (Instant, On request). **Derived, never chosen** — once,
  from the club's terms, and carried on every sellable court hour. No other clock runs on a
  proposal.
- **Paused** — a club taking no new cards on its courts. Booked games are played as booked, and
  cards already dealt keep their court until their book-by, so its hours stay sellable. A paused
  club is still **Live**.
- **Setup checklist** — the five steps before a club's courts reach any deck: connect payments,
  choose a Way of working, add Courts, set Raketa hours and Prices, confirm the Raketa settings.
  Each is **done**, **to do**, **locked** behind the step it needs (hours and prices behind a
  court, the settings behind a way of working) or **pending** — payments, until connecting Stripe
  is built. Read off the Club courts, never stored. **Live** — every step but a pending one done.
  _Avoid_: onboarded, active (of a club).

### Groups

Settled by [ADR-0183](docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
on [#501](https://github.com/Raketa02/Raketa/issues/501). **Partly built** —
[#504](https://github.com/Raketa02/Raketa/issues/504) built a Player group's creation, the Groups
list, the group page, home-club search and joining an *Anyone* group;
[#505](https://github.com/Raketa02/Raketa/issues/505) built join search and Join requests — asking,
and the Owner approving or declining; [#506](https://github.com/Raketa02/Raketa/issues/506) built
Members by sport, editing, leaving with ownership passing, and deleting;
[#509](https://github.com/Raketa02/Raketa/issues/509) built Official groups — created and run by
an Administrator from the app, declared sports and a WhatsApp group size, an Administrator who
plays joining directly, and the club's refusal to untick a declared sport; and
[#510](https://github.com/Raketa02/Raketa/issues/510) built the club's side — its Groups table and
the Handover — which completes the backend half.

**The crowd that already plays together, brought into the app.** Clubs keep WhatsApp groups, one
per sport; a group is where that crowd lands when somebody taps its link. Its Games tab deals it
games and its members post them (**Proposals**), a filled game books a court (**Bookings**), and a
booked game has its chat (**Conversation**) —
[ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md).

- **Group** — an **event-sourced aggregate** of two kinds, **Player group** and **Official group**,
  sharing the **Group link**, the **Join policy**, **Join requests**, the searches and the page. A
  name of 1–40 characters, trimmed, **never unique**. Its **monogram** — two letters cut from its
  name, on a colour fixed by its id — is served by the backend so that every client draws the same
  tile. Its **sports** are read, never stored: for a Player group, those in which at least two
  Group members hold a Skill rating; for an Official group, the ones it declares. _Avoid_: team,
  community, circle, league, *club* (a Club is the place).
- **Player group** — a Group a player created and runs as its **Owner**, at a Home club they chose.
  It may be deleted only while its Owner is its only member.
- **Official group** — a Group an **Administrator** created for their club, one per WhatsApp group
  the club keeps. **It has no Owner**: one Administrator runs it, or none while it **needs an
  administrator** — then it reads *"[club] approves joins"*, and the club answers its requests
  until a **Handover**. **Its club answers its Join requests at any time**, beside whoever runs it
  ([ADR-0191](docs/adr/0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)
  §1), and edits nothing in it. It **declares its sports** (a non-empty subset of the club's) and its **WhatsApp
  group size**. Whoever runs it can neither delete it nor stop running it; only the club moves it.
  _Avoid_: club group, verified group, public group.
- **Owner** — the player who runs a Player group: answers its Join requests and edits its name and
  Join policy. The creator is the first; **an Owner who leaves a group that has other members
  passes ownership to the longest-standing member**. An Official group has none. _Avoid_: admin,
  creator (ownership passes), moderator.
- **Group member** — a player who belongs to a Group. **Named apart from the Conversation's
  Member** — somebody on a court right now — which it is not, and must never be shortened to where
  the two could meet. Counted in *N members*, including an Administrator who joined as a player; a
  club's *Players* figure is the same count. **Nobody removes a Group member** — a member leaves,
  and may rejoin under the group's rule. **A Block hides nobody from a Members list**
  ([ADR-0193](docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2, from #586), and counts never change. _Avoid_: bare *member* wherever a conversation could
  be meant, follower, participant.
- **Join policy** — who gets in: **Anyone** (the default: joining admits at once) or **People I
  approve** (joining creates a Join request). **Switching to Anyone admits everyone waiting.** An
  Administrator acting as a player joins the groups they run directly, whatever the policy.
  _Avoid_: private / public, privacy, visibility.
- **Join request** — a player's ask to join a *People I approve* group, waiting for its Owner — or,
  on an Official group, for its Administrator **or its club**, whichever answers first. At most one
  pending per player per group. **Approved** makes them a Group member;
  **declined** removes the request **silently**, and they may ask again. _Avoid_: application,
  invitation (an **Invitation** is a club naming an Administrator).
- **Group link** — the public site's address, `/join/`, and the group's **code**: eight characters
  from an alphabet with no look-alikes, unique, and **never changing** — not on a rename, a policy
  change or a Handover. Any text containing `/join/<code>` is recognised. The way into a group from
  outside the app, and what an Administrator posts into the WhatsApp group. _Avoid_: invite link,
  share link, group URL.
- **WhatsApp group size** — how many people the WhatsApp group an Official group mirrors has, as
  its Administrator typed it: a whole number from 2 to 1024. It limits nothing; it is the
  denominator of the club's *From original group* figure (*From WhatsApp* until #529), which may
  pass 100% and says so. The app's form calls it *Group size*. Only Official
  groups have one. _Avoid_: capacity, limit, max members.
- **Handover** — the club giving an Official group to another **active** Administrator of the club
  — any group, including one that needs an administrator. The group keeps its link, Join policy,
  WhatsApp group size, members and waiting requests; only which Administrator answers them
  changes, and the club answers them throughout. **The Administrator it was handed to is told,
  once**, on a sheet in the app
  ([ADR-0192](docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)).
  _Avoid_: transfer, reassignment.

### Administrators

Settled by
[ADR-0184](docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
and
[ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
on [#501](https://github.com/Raketa02/Raketa/issues/501), and built by
[#507](https://github.com/Raketa02/Raketa/issues/507) (the one-time credentials) and
[#508](https://github.com/Raketa02/Raketa/issues/508) (the Administrator, the Invitation and the
guard). Official groups are built by [#509](https://github.com/Raketa02/Raketa/issues/509), and
the Handover by [#510](https://github.com/Raketa02/Raketa/issues/510).

**The person a club names to run its WhatsApp groups inside Raketa.** Their one job is to make an
Official group per WhatsApp group and post its link there.

- **Administrator** — a User acting **for one club**: an **event-sourced aggregate**, one per
  **(club, email)**, so a person running two clubs' groups is two Administrators. **Invited**
  (shown as *expired* once its credential lapses), **active** (linked to an account) or
  **removed**; a removed person may be invited again. Creates the club's Official groups, answers
  their Join requests and edits their settings; reads their **Members** list and opens the record
  of anybody on it without being a Group member; can neither delete one nor stop running one.
  Removal ends it on the next request, leaves the person's player side untouched, and is
  **emailed** to them — *removed*, or *invitation withdrawn* for somebody who never took it up
  (ADR-0191 §4).
  **Collisions, recorded:** an Administrator is **not the `ADMIN` Authority** and holds no power
  over the platform or any account; the **admin** tag on a Members list is **copy** for *runs this
  group*, not a role; and *Administrator* in the app's profile switcher is **UI vocabulary** for
  this side of the account (see **Player**). _Avoid_: admin (as the noun), manager, moderator,
  staff, group admin.
- **Invitation** — the club naming a person as Administrator, **by name and email and nothing
  else**: the club never sets, sees or handles a password or a code. Delivered by email as a
  button and an **8-character code**, valid **72 hours** and resendable. A **new person** sets a password through it and gets an account under the
  name the club typed, with no Nickname and no Adult attestation; an **existing account** accepts
  it from the app, with no password step. _Avoid_: invite code (the code is one half of it),
  *join request* (that is a player asking a group), onboarding.
- **Administrator events** (durable name / version) — never a link, a code or a ticket:
  - **AdministratorInvited** — `administrators.administrator_invited` / v1 — the club named a
    person; the first event of the stream, and again when a removed person is invited again.
  - **InvitationResent** — `administrators.invitation_resent` / v1 — a fresh 72 hours.
  - **InvitationAccepted** — `administrators.invitation_accepted` / v1 — taken up, by setting a
    password through it or by accepting in the app; *active*, linked to that account.
  - **AdministratorPasswordReset** — `administrators.administrator_password_reset` / v1 — the
    club's *Reset password*: back to *invited*, the account still linked.
  - **AdministratorRemoved** — `administrators.administrator_removed` / v1.

**Invariants**
- **One Administrator per (club, email)**: inviting an address already *invited* — *expired*
  included — or *active* at the club is refused on the spot (`administrator_already_invited`,
  `administrator_already_active`); a removed one is invited again on the same stream.
- **Expired is derived, never recorded**: from the last time the invitation went out plus the
  invitation credential's 72 hours, so an existing account's invitation — which carries no code —
  lapses when a new person's would.
- **The club's *Reset password* is refused for an account that acts as a player**
  (`administrator_also_plays`) — attested, or holding a Player profile — and for somebody who
  never set a password (`administrator_has_no_account`).
- **Every administrator operation asks again**: an active administratorship of this account at
  the club the request names, or `not_an_administrator` — the request after a removal. The
  person's player side and its sessions are untouched.

### Bookings (`backend/app/modules/bookings/`)

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5 and built
by [#541](https://github.com/Raketa02/Raketa/issues/541) (the fill),
[#543](https://github.com/Raketa02/Raketa/issues/543) (On request),
[#544](https://github.com/Raketa02/Raketa/issues/544) (leaving and the cut-off),
[#545](https://github.com/Raketa02/Raketa/issues/545) (rescues) and
[#547](https://github.com/Raketa02/Raketa/issues/547) (the club runs it).

**A booking is the game a full card became**, and its id is the card's. Its money is the Seat
charges' (**Payments**), its result the Game's (**Games**).

- **Booking** — a filled proposal: the club, the court and its number, the hour, the seats and
  their sides, the cut-off as the club set it, and its state — *waiting for the club*, *booked*,
  *seat open*, *called off*, *played*. An **event-sourced aggregate, one stream per filled
  proposal**. Born *booked*, or *waiting for the club* at an On request club, which accepts,
  refuses or lets its time run out; *played* is read off the clock and never recorded. It opens
  the ordinary **Game** when it is booked. _Avoid_: reservation, held.
- **Leaver** — a player who left a booking. Before the cut-off, refunded at once minus the card
  fee; after it, refunded (minus the fee) only when the seat is taken. Told to the Game as a
  **Departure**.
- **Rescue** — an open seat in a **booked** game that lost a player. Shown in **Fill in** and dealt
  to the best fits as a Seat open card; taking it pays at once, and the rescuer sits where the
  leaver sat. The seat that opened first is taken first.
- **Fill in** — the group's rescue board (**Seats to fill**) plus **You're In**, your own yeses
  that have not filled or are *waiting for the club*. It never offers a proposal that is still
  filling.
- **Check-in** — a club scanning a player's code, or typing its short code, on the day. Evidence
  that the player was there, never a condition for money; a player checked in cannot be reported
  as a no-show.

**Invariants**
- **A game plays full or not at all.** A seat that opened before the club's cut-off and is still
  open at it calls the game off, and the court is the club's again; a seat that opened after the
  cut-off leaves the game going ahead short.
- **The club may move or cancel a game until it starts.** A move is to another court of the sport
  at the same hour; a cancellation refunds everybody still in, in full, and is on nobody's record.

### Payments

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4–§5 and
built by [#536](https://github.com/Raketa02/Raketa/issues/536)
([ADR-0190](docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)); the
**Seat charge** by [#541](https://github.com/Raketa02/Raketa/issues/541), and connecting a club's
account by [#537](https://github.com/Raketa02/Raketa/issues/537).

**How a player pays: a card or a wallet saved once, charged later by the club.** Every charge is
made on the club's own account — **the club is the seller** — and a player's card is copied there
for each one.

- **The club is the seller** — every charge is made on the club's own Stripe account, and the club
  pays the card fee. Raketa takes no fee.
- **Seat charge** — one seat's money in one booking: an **event-sourced aggregate, one stream per
  payment**, born at the fill and never before — a yes moves no money. Held on the player's card
  or refused; then taken, released, or confirmed by the player when their bank wanted them present.
  Raketa's account of a payment; Stripe is the ledger of record, and a notice from it moves a
  charge only forward.
- **Payment method** — a player's saved card or wallet: its **brand** (the network, as the
  provider names it), its **last four digits** and the **wallet** it came through (Apple Pay,
  Google Pay, or none). An **event-sourced aggregate, one stream per player**, born by being
  used: a player who never opened the setup has none — *Not set up*. **Change** keeps the old
  method working until the new one is saved; **remove** is refused while anything could still be
  charged to it — a live yes, or a booked game ahead. A card number never reaches Raketa.
  _Avoid_: card for the method as a whole (it may be a wallet — though a wallet saves a card, and
  *card* is right for what the provider holds: its brand and last four), payment details, billing
  info.
- **Setup** — saving a method: the player chooses how to pay, types a card into the provider's
  own fields, **accepts the payment terms**, and confirms with their bank — the step that saves.
  One saves a card for **off-session** use, charged later without the player present. At most
  **five a day** per player. _Avoid_: onboarding (that is the player's first run, and a club's
  Stripe account).
- **Payment terms** — the words that name the club as the one charging: *when a game you said yes
  to fills, the club charges your share* (the mechanics §12.5). **Accepted before anything is
  saved**: the setup's secret — the only way a phone can save a card — is the answer to accepting
  them. The acceptance is recorded with **the version shown, the moment and the address**; the
  words are the client's, the version in force the backend's. **A card whose bank moved it to
  another brand asks for them again** before it can be charged. _Avoid_: consent screen, T&Cs.
- **Payment provider** — where money actually moves: **Stripe**, or on a laptop and in every test
  an in-process **fake** held to the same demands. A deployed environment refuses the fake.
- **Payment method events** (durable name / version) — never a card number or a setup's secret:
  - **PaymentSetupStarted** — `payments.setup_started` / v1 — a setup opened, under the player's
    one customer at the provider; names the setup it replaced, which is then cancelled there.
  - **PaymentTermsAccepted** — `payments.terms_accepted` / v1 — for the open setup, or again for
    the saved method after a brand change.
  - **PaymentMethodSaved** — `payments.method_saved` / v1 — the first method.
  - **PaymentMethodChanged** — `payments.method_changed` / v1 — a new method over the old, which
    is then released at the provider.
  - **PaymentMethodRemoved** — `payments.method_removed` / v1 — released at the provider after.
  - **PaymentMethodUpdated** — `payments.method_updated` / v1 — the bank updated the card: a new
    number, or a new brand — as read from the provider, never off its notice.

### Proposals

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §1–§2, §5
and built by [#538](https://github.com/Raketa02/Raketa/issues/538); the group deck and a
player's Games & money by [#539](https://github.com/Raketa02/Raketa/issues/539), the engine that
builds proposals by [#540](https://github.com/Raketa02/Raketa/issues/540), the fill that books one
by [#541](https://github.com/Raketa02/Raketa/issues/541), rescues by
[#545](https://github.com/Raketa02/Raketa/issues/545) and posting by
[#546](https://github.com/Raketa02/Raketa/issues/546). **Since the Classic play removal
([#569](https://github.com/Raketa02/Raketa/issues/569)) this is the one way a game is made.**

**How a game fills: dealt to a pool, answered with a silent yes.**

- **Pool** — the players who may be dealt a game plus the clubs whose courts they may use. A
  **Group** is the first kind of pool; a city (Explore) will be the next. Every proposal carries
  its pool, and nothing names a group where it means a pool. A group's pool is filed under the
  group's own id, and its players are the group's members **now** — somebody who left the group
  has left its pool. _Avoid_: audience (that is an Official group's).
- **Proposal** — a game that is still filling: a pool, a sport, a **kind** (competitive, or for
  fun), a **court hour** at a club (never a court number, which is given at booking), the
  **share** fixed on it, the versions it was dealt in, the yeses, and the **book-by** — read off
  what the club sells at that hour, never chosen. **Picked for you** when the engine built it; a
  **Post** when a member did, which is born with its poster In. An **event-sourced aggregate, one
  stream per proposed game**. It is *filling*, then *expired* from its book-by on — read off the
  clock, whether or not anything has recorded it — or *withdrawn*, when a poster takes their
  post back with nobody else In; *filled* arrives with the Booking. _Avoid_: open game; and
  *challenge*, which is only the label on a posted game's card.
- **Version** — one of **up to three** views of the same proposal, each dealt to different people:
  the people In, and the names dealt for the seats still open. **Each person is dealt one.** A
  seat a **No** left is dealt again into the same version, to at most three next best fits.
- **Yes** — a swipe right, or *I'm in*: *"if everybody is in, book it and charge my share."*
  Silent, free, holds nothing. **Yeses are the game's, never a version's**: a yes on any version
  counts toward the one game. A yes needs a saved **Payment method**. A **No** is a swipe left, equally silent, and **final**: the card never comes back.
  _Avoid_: vote, like.
- **In** — a player who said yes to a proposal that has not filled. **Everybody In fits everybody
  else In**: a version is dealt only to people who fit the people In and each other, and a yes
  lands only from somebody who fits everybody In — *fits* being today's pair rule for one
  court (no block either way, mutual gender preference, Levels within the kind's window).
- **Withdraw** — taking a yes back before the game fills: free and silent, and the seat is open
  again. Unlike a **No** it is no verdict on the card: the player may say yes again while the
  game fills.
- **Live yes** — a yes on a game that has not filled, across pools; a post counts as one. **No
  cap** on how many (removed 2026-10-05): games per week and one game per hour bound what they
  can book.
- **Post** — a proposal a member created by picking the hour and the court; posting is the
  poster's yes. At most two live per player. It is dealt to whom it is for — its *Who* and a level
  range that starts from the poster's **level window** — and to other players it reads as a
  **Challenge** card.
- **Fills** — the moment the last needed yes lands and a **Booking** opens. Every seat is then
  charged together, all or nothing — at an On request club only once the club confirms, the
  booking *waiting for the club* until it does.
- **It's a game!** — the screen the player whose yes filled the game, or who took a rescue, sees.
- **Home** — the first tab of the bottom bar: your games from the moment they fill, and the games
  waiting for a club. Its badge counts only the games that need you. Proposals assembles it.
- **Proposal events** (durable name / version) — none of them is told to anybody:
  - **ProposalMade** — `proposals.proposal_made` / v1 — the pool and its kind, the origin and
    poster, the sport and kind, the club and start, the share and the book-by.
  - **VersionDealt** — `proposals.version_dealt` / v1 — its number and the people named.
  - **YesSaid** — `proposals.yes_said` / v1.
  - **NoSaid** — `proposals.no_said` / v1.
  - **YesWithdrawn** — `proposals.yes_withdrawn` / v1.
  - **ProposalWithdrawn** — `proposals.proposal_withdrawn` / v1 — a post whose poster withdrew
    with nobody else In.
  - **ProposalExpired** — `proposals.proposal_expired` / v1 — the record, written by the book-by
    sweep, of an expiry that was already true.
  - **GamesAndMoneySet** — `proposals.games_and_money_set` / v1 — a player's games per week and
    most I'll pay, both, on their Games & money stream.

**What a player is dealt: their group deck, within their Games & money.**

- **Group deck** — a group's Games tab: the proposals dealt to you in one sport and one
  **kind**, each drawn as **your own version** — everybody In, you, and the rest of your version
  — with its sides (the evenest arrangement the engine forecasts, you on your own), the forecast
  for that version, an overlap grid and the court block. Ordered by the seats that would be open
  after your yes (fewest first), then **Seat open › Challenge › Picked for you**, then the
  soonest deadline, then the best forecast; the same people only at their best hour. A card you
  said no to never returns; one you are In on is in *You're In*; one you took your yes back from
  is dealt again. Never dealt: a kind your Play intent does not want, a share above **Most I'll
  pay**, a week at your **Games per week**, an hour you already have a game at, a club no longer
  selling, or a card with somebody In you may not share a court with. A projection, recomputed
  at every read and stored nowhere. (The Players deck of people went with Classic play.)
- **Picked for you card · Challenge card · Seat open card** — the three card types: a pick, a
  **Post** dealt to you as a best fit (its ribbon reads *"Kuba challenged you"*, or *"The group
  challenged you"* once the poster withdrew), and a **Rescue**. *Challenge* is the card's label and
  nothing else: the aggregate of that name went with Classic play.
- **IN tag** — the tag on the tile of a player who is **In**: the only tag that signals momentum.
  A card dealt in versions also says how many are In on the whole proposal.
- **Overlap grid** — the people on a card's week as 7 days × Morning 07–12 / Afternoon 12–17 /
  Evening 17–23: *bright* where everybody is free together for one whole hour of the range, *dim*
  where all but one are (on a card of three or more), the game's cell ringed; graded **High /
  Good / Slim** by the hours everybody shares over the narrowest week. Never one person's week.
- **Games & money** — a player's two limits, across sports and pools: **Games per week** (1–7,
  default 2, counted Monday to Sunday: a week with that many games booked deals nothing more) and
  **Most I'll pay** (off, 35, 45 or 60 zł: a card whose share is above it is never dealt). An
  **event-sourced aggregate, one stream per player** under their own id, born by being used; the
  same answer records nothing.

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

Every client describes the same nouns this file does. A concept that exists in this
glossary keeps its name in TypeScript: an `Assessment` is an `Assessment`, not a `Quiz`,
`Survey`, or `Test`. Client-only *technical* vocabulary (wire type, DTO, mapper, secure
store) belongs in that app's own `CONTEXT.md`, never here.

The client also **renders** the values the backend sends. The backend sends numbers and
machine codes and never display text
([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)) — to a client; an
**email** has no client, so the backend writes its words
([ADR-0186](docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §4) — so the client
formats — against one table, in [`docs/value-formatting.md`](docs/value-formatting.md).
That is not a design system and holds no colour or size; it is the exact string a level, a
time or a duration becomes. One client cannot drift from itself, so the table's immediate
value is smaller than it was — it is kept because it is the contract a *second* client
would be held to, and rewriting it from memory later is how two apps end up rendering the
same number two ways. **Copy is not formatting**: the sentence behind an unavailability
code is the app's own.
