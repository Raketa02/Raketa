# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. Every app
obeys this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
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
>
> **Courts, bookings and money return with [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)** (2026-09-29): decided and
> specified in [`docs/specs/games-and-fill-in/`](docs/specs/games-and-fill-in/), not yet built.
> Their terms are in **[Part 2](#part-2--decided-not-yet-built-games-and-fill-in)**; Part 1 still
> describes the code.

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
  a rule, not a comparison), and not the matcher, which reads what a player is shown and never
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
- **Tester** — a player whose account carries the **tester mark**: a real player who may be
  given a **Feature flag**'s feature before anyone else. **A mark on the account, not an
  `Authority`** — being shown something early grants no power over anyone, so `Authority` stays
  `USER` or `ADMIN`. Owned by the backend, set and cleared by an admin command and never by the
  player, and read by the player app as `is_tester` on its own account. The app sends it to the
  flag evaluation as `isTester`; **no datafile ever names a tester**, because the datafile is
  public ([ADR-0180](docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
  §9). _Avoid_: "beta user", "tester role".
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
  so there is no age, band or date anywhere in the system to read, and the candidate index
  fails its build if a date of birth appears.
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
  - **UserMarkedAsTester** — `users.user_marked_as_tester` / v1 — the **Tester** mark set.
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
  - **UserUnmarkedAsTester** — `users.user_unmarked_as_tester` / v1 — the mark cleared. Two
    events and not one carrying a boolean, so the stream says who was a tester and when in the
    words it was done in ([ADR-0180](docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
    §9). Both are projected onto the `users` row in the act's own transaction, beside
    `is_admin` and `is_active`, because every `User` a route is handed is read from that row.

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
- **The tester mark is idempotent both ways** — `mark_as_tester()` on a Tester and
  `unmark_as_tester()` on anybody else record nothing. It is set only by `SetTesterMark`, which
  `make tester PLAYER=<id|email> MARK=on|off` runs and no route reaches; a player it cannot find
  by id or email is refused with `UnknownPlayer`. A disabled account is not refused: the mark
  grants nothing.

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
- **Availability overlap** — how much of a player's own declared week another player covers.
  Deliberately **asymmetric**: the denominator is *your* hours, because the question it
  answers is *how much of my week does this person cover*.
- **Window** — the coarse shape of a searcher's declared week, as one of `TODAY`, `TOMORROW`,
  `WEEKEND`, `THIS_WEEK`, `ANY`. **Derived from the grid, never chosen** — there is no picker,
  because a picked window is a second availability declaration free to contradict the one the
  whole engine just matched on. It is derived from *the week the search actually ran on*, so a
  widened search can carry a different window from the profile. It is what the person answering
  a challenge is told they are agreeing to; it is **not a proposed time**, and the players agree
  the hour themselves ([ADR-0100](docs/adr/0100-challenge-window-derived-never-chosen.md)).
  **Derived once, at the moment of sending, and then recorded on the Challenge.** ADR-0100
  forbids *choosing* it, not storing it: the grid it was derived from is the searcher's own and
  they may edit it a minute later, so a window re-derived on read would quietly change what the
  invitee is answering. A proposal that moves after it is sent is not a proposal.
- **Location area** — where a player plays, held coarsely: a cell about a kilometre across,
  rounded to on the way in. The precise fix that produced it is never a shareable value. **It
  moves on a cold start**: the app re-reads the phone silently when it is launched, and after a
  day in the background, and the cell changes if the fix falls outside it — never merely on
  foreground, never with a prompt, and never when the permission has since been revoked
  ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §6).
- **Search radius** — the distance around a player's Location area within which they want to
  find other players. **A filter when the player searches, and a weight when the engine
  proposes** — the same number answering two questions, because who *you* asked to see and
  who the platform *offers* you are different acts. It is also the **Radar**'s **Reach**: the
  radar draws exactly as far as the deck deals, and there is no city ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §1).
- **Proposals opt-in** — the player's recorded answer to whether the recommendation engine
  may push games at them. It has **no default**: unanswered is neither yes nor no.
- **Gender** — `WOMAN`, `MAN` or `PREFER_NOT_TO_SAY`, held on the Player profile. **Per
  person, never per sport**, self-declared and freely changed. It is a statement about **which
  searches a player wishes to appear in**, not a ruling by the platform on who anybody is:
  `PREFER_NOT_TO_SAY` matches an unconstrained search only, and is an explicit answer rather
  than a null — the same shape as Play intent's `NO_PREFERENCE`. Required at profile creation.
  **Never rendered on a card and never carried by a response that describes one player to
  another** ([ADR-0096](docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md));
  **the one shape that carries it out is the owner's own profile read**, so the You tab can show
  a player what they set ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §4).
- **Gender preference** — who a player is willing to be matched with: `WOMEN_ONLY`, `MEN_ONLY`
  or `ANY`. Durable, optional, defaulting to `ANY`. **Mutual, never one-directional** — it
  governs both what a player sees and whether they can be seen, so it protects an inbox and not
  only a search. A **gate, never a weight, and never relaxed**. A search may narrow it for that
  search and may never widen it past another player's. **It does not reach whoever runs an
  Official group the player is in**: running their group is not being matched with them, and
  that account opens their record without it
  ([ADR-0159](docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md),
  amended 2026-10-02).
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
- **Intro** — **one line a player writes about themselves**: at most 100 characters, no line
  breaks, any language, one per player, and **optional** — a player who wrote none has none,
  not an empty one. The first player-authored free text the platform shows to a stranger, and
  the fence is at the write: a phone number, an email, a URL or a handle is **refused**, because
  the realistic abuse of a line shown before a game exists is contact leaving the app. It reaches
  a **Player card** and a player record and nowhere a person is merely named; it is never scored
  ([ADR-0170](docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)).
  **Edited from the You tab**, with the tags and the photos, as one piece of work — a search
  record already kept quotes the line as it stood at the deal
  ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §6). _Avoid_: "bio", "tagline", "about", "status".
- **On-court check** — what the platform concluded about whether a photograph shows a racket
  sport, decided at the upload and stored with it
  ([ADR-0129](docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)). **It soft-warns
  and never blocks**: a flagged photo is stored, keeps its position and keeps the lead if it had
  it. Its outcome has **three** values, not two — **passed**, **flagged**, and **nobody looked**,
  which is its own answer and never a spelling of *flagged*
  ([ADR-0138](docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
  Two readers see it differently and that is deliberate: the **uploader** is warned about their
  own photograph, and a **player card** marks only the pass — a card must not tell one player
  that another player's photograph was doubted. **The confidence behind it never crosses on any
  route**, to either of them.
- **Profile commit** — the single idempotent request that ends onboarding's second part,
  carrying all seven answers at once. Nothing is written before it, so leaving mid-part
  restarts at step 1 ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Keyed
  by a client-supplied **idempotency key**, which the creating event carries so a retry is
  recognised from the stream itself rather than from a table beside it.
- **Player profile events** (durable name / version):
  - **PlayerProfileCreated** — `player_profile.created` / **v2** — the commit, carrying every
    preference and the idempotency key. **Not the opt-in.** It gained `gender` and
    `gender_preference` while it was v1, appended with defaults so the rows then in the store
    decoded unchanged, and an absent `gender` means *committed before anybody was asked* —
    never a quieter `PREFER_NOT_TO_SAY`, which is an answer somebody chose. Nothing is
    backfilled. **v2 is the week becoming hours** (`weekly_hours`, [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
    §5); v1, whose week was parts of the day, is deliberately unreadable — only `local` ever
    ran, and a row of the old shape is a decoding error rather than a week folded wrongly.
  - **SocialTagsChanged** — `player_profile.social_tags_changed` / v1.
  - **PhotosChanged** — `player_profile.photos_changed` / v1.
  - **WeeklyHoursSet** — `player_profile.weekly_hours_set` / v1 — the whole week, as the You
    tab's *Save your week* leaves it; empty is a cleared week. It replaced
    `player_profile.availability_changed`, which nothing reads.
  - **LocationChanged** — `player_profile.location_changed` / v1.
  - **SearchRadiusChanged** — `player_profile.search_radius_changed` / v1.
  - **GenderChanged** — `player_profile.gender_changed` / v1 — gender is self-declared and
    freely changed, so the correction has an event from the day the field does.
  - **GenderPreferenceChanged** — `player_profile.gender_preference_changed` / v1.
  - **ProposalsOptInAnswered** — `player_profile.proposals_opt_in_answered` / v1 — the
    answer, the copy version shown and the surface; the moment is the event's own.
  - **PlayIntentDeclared** — `player_profile.play_intent_declared` / v1 — the sport, the value
    and the surface it was declared on. Obeys the preference rule, not the consent rule.
  - **IntroChanged** — `player_profile.intro_changed` / v1 — the line as it now stands, or none:
    the You tab's edit, and the withdrawal of a line
    ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §6).
    `IntroWritten` stays the commit's.

**Invariants**
- **A tag id is permanent.** Ids are persisted on accounts, so retiring a tag means hiding
  it from the picker while continuing to honour it — never reusing or renaming it.
- **At least one hour, and blank is absent rather than zero.** Weekly hours are **required** at
  profile commit — one ticked hour of the 112 is a real answer, none is not an answer at all.
  Where a blank week is nevertheless met — cleared afterwards — it means *we do not know*, the
  availability term stands down, and the player is free for no court hour;
  it is never scored as no overlap and never as any time
  ([ADR-0102](docs/adr/0102-silence-is-never-scored.md)). **An unanswered field is never a
  negative filter**, and requiring the field is how that invariant is kept rather than
  weighed.
- **The grid is never shown to anybody as a calendar.** Not to matched players, not as
  free/busy, not exported. Only the *count* of shared hours and the name of the next shared
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

One player keeping another off their games. Settled by
[ADR-0095](docs/adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) and
amended by [ADR-0193](docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md):
**a block keeps two people off one court, and the blocker can see it.** **Built**: the aggregate,
its two events, the `BlockQuery` port and two routes, read by the new games' pair rule. **Still to
build** ([#586](https://github.com/Raketa02/Raketa/issues/586)): the request without a surface,
`blocks.player_blocked` v2, Blocked players, the record's own-block fact and the withdrawal of
filling yeses. Until then, the code also still hides a blocked pair in Members lists and refuses the
record on a block, which ADR-0193 §2 undoes.

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
  a player's whole **exclusion set**, and the **pairwise** question. From #586 a third, **directed**
  read answers own blocks, and is only ever asked with the reader as the blocker. **It fails
  closed**: it raises rather than answering *nobody is blocked* when it cannot read the state,
  because an empty answer it cannot stand behind is a safety control switching itself off under
  load.
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
**The shortlist runs end to end**: `POST /api/v1/searches` gates, generates, scores, modifies,
floors, reorders and records. So do the rest — the **line-up**, the **deck**, the **relaxation
ladder**, the **interest ledger** and the **read-back** were designed here ahead of their code
and are now served by `POST /api/v1/lineups`, `POST /api/v1/deck`, `POST /api/v1/forecasts`,
`POST`/`GET /api/v1/interest`, `POST /api/v1/passes` and
`GET /api/v1/searches/{search_id}`. Thirty-three ADRs
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
  blended score instead of the strands, because it is the number the player can see.
- **Minimum evidence** — the least the engine must know about *one specific candidate* before
  showing them to anybody. A **gate**, never an adjustment to their score, and a fraction of the
  terms live for the platform rather than a count. It reads gaps particular to that person and
  never platform-wide absence, so a term nobody has yet gates nobody.
- **Relaxation rung** — an **offer** to relax one of the searcher's *own* asks — their times, or
  their radius — with the real count of candidates it would add. Three exist, times first. The
  player accepts; the engine never relaxes anything by itself, and an accepted widen is scoped to
  that one search ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **Prompt** — a question the platform raises about a value it can see drifting, and **never a
  change to that value**. Four exist — keep the times you improvised for one search, keep a
  widening you keep taking, update a declaration your searches keep disagreeing with, and
  refresh a week you described months ago — and each ends at an offer on a screen. It is the
  one place the platform watches, notices, and deliberately declines to act
  ([ADR-0094](docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md),
  [ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)). It crosses as a
  **code** with the value already in play beside it; the client writes the sentence. It is
  **answered** by a write through the route that owns the value, never by the prompt itself, and
  it is **retired** by its own expiry or by its condition ceasing — never by a caller, so a
  question nobody answered cannot quietly stop being asked. It is **declined** on the sheet — the one
  answer that writes no value, and so the only one nothing else would record. A decline
  **suppresses** the prompt for thirty days and **retires** nothing: the standing question still
  expires on its own, so a caller still cannot make a question quietly stop being asked. Three of
  the four suppress; *keep these times* does not, because a grid legitimately differs per search
  where a radius, a declaration and a described week do not. A declined **prompt** is not a
  declined **seat**; the word is always qualified
  ([#237](https://github.com/Raketa02/Raketa/issues/237)).
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
- **Origin key** — the `(search_id, position)` a challenge was sent from. Carried **per
  invited seat**, never per challenge: a doubles send draws its three invitees from one search
  at three positions, so a challenge-level key would keep the search and lose every position —
  and the position is what the telemetry join reads. Required, never optional: a search not
  joined to its outcome is evidence that no longer exists, and there is no backfill.
- **PlayerScoreQuery** / **MatchHistoryQuery** — the two ports naming what the matcher demands of
  `player_score` and the record of who has played whom, beside **AccountHoldQuery** for `cases`
  and **AtStakeQuery** for `rating`. One provider signs one contract — with **one recorded
  exception**: `challenges` signs `MatchHistoryQuery` beside `games`, because the seam runs
  *through* the pairwise read and splitting the port would halve its 500-counterpart bound. Its
  adapter is **`ChallengesButNobodyHasPlayed`**, named for the fact that **played** was empty by
  construction rather than by luck, and `games` arrives as a **composing** adapter over it rather
  than as a second signature. **Every one of these ports has a real provider now**: the three null
  objects that stood in for them — `NoMatchHistoryExists`, `NoResultUpdateRuleExists` and
  `NoPlayerScoresExist` — each retired on the day its own stated fact stopped being true, which
  is what a null object **named for a fact** is for
  ([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md) as amended). The one that
  remains is **`NoHoldsExist`**, and it is a *gate* rather than a term.

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
- **Surface** — which of the five things a search is: a ranked **shortlist**, a seated
  **line-up**, the **deck**, **completing a half-built game**, or the **Radar**'s **Reading**.
  One engine and one pipeline with different terminal stages; the fourth is optimised for the
  existing group and not for the searcher, and says so; the fifth ranks nothing and says so.
  Distinct from **initiation**, which is who asked.
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
- **Split** — the two **side** strengths a **forecast** was read from, and the signed gap
  between them: *your side*, *their side*, and *your side minus theirs*. The evidence behind the
  percentage — the forecast says *how even*, the split says *between what and what*, on the same
  scale a **Skill** rating is read on. A side's strength is **not the mean of the two people on
  it** (the weaker partner sets more of it), which is why it is a number only the engine has and
  why a client may never compute one. It is **not the group objective** and must not become one:
  what crosses is an input to a figure already served, never a second score
  ([ADR-0136](docs/adr/0136-the-split-is-evidence-for-the-forecast-not-a-second-score.md)).
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
  search it came from, and it is not a **Challenge** — a challenge belongs to `challenges`,
  and a *mutual* yes is the one thing here that opens one. **A yes is a statement about *now*,
  so it expires** — at 21 days, flat until then and then absent, never tapering, because the
  age of the yes is already printed on the card and a fading lift would charge for it a second
  time invisibly
  ([ADR-0127](docs/adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md)). The expiry
  is **dated when the yes is made**, never announced when it lands.
- **Outstanding interest** — an **Interest** that is sent, **unexpired**, and **not yet
  mutual**. It is what the cap counts: a mutual has been answered and is no longer in flight, and
  an expired yes is not interest at all. Without the word, *how many yeses you may have out* is
  three different numbers. The cap is **per sport**, **hard** — the write is refused, never
  quietly aged away — and **shown before it bites**, because a cap the player cannot see is a
  refusal they cannot predict.
- **Want to play you** — a **count, never a list**: the number of people whose live **Interest**
  towards a player in a sport *would be dealt to them* — every gate passed, not passed on within
  the pass window, not in the **Cool-off**, not already mutual. It rides on a deal — and on a
  **Reading**'s envelope, computed by the deal's own rule so the two chips are one number — and
  names nobody; the chip prints it and is not drawn at zero. The one shape in which an incoming yes
  crosses to its recipient other than as a lift ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4, narrowing
  [ADR-0109](docs/adr/0109-a-read-back-names-what-it-withholds.md) §2 by this one integer).
- **Reading** — one invocation of the **Radar**: every player rated in the sport within the
  viewer's **Reach**, unranked, ordered only by drawn distance so an **Origin key** means
  something. A recorded **Search** and a prior disclosure, like a deal — and **not a deal**: it
  spends no hand, and a look never enters the deck's dealt memory; only an answer given on the
  radar reaches the deck ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §1, §4).
- **Radar** — the second pane of Players: the viewer at the centre, rings in kilometres, and
  every player a **Reading** returned drawn at their **Drawn spot**'s distance and **Bearing**
  — a face far out, a level closer, and the card for the one player tapped, at any width
  ([ADR-0176](docs/adr/0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md) §3).
  *Who is actually out there?* where the deck
  asks *who should I play?* **No judgement**: no level band, no fit floor, no pass memory, no
  Cool-off; it keeps only blocked, held, disabled, the gender preference and *rated in the
  sport*. It answers with the deck's own yes and pass, and hides nobody for either.
- **Reach** — how far the Radar draws: the viewer's **Search radius**, measured cell to cell
  like the deck's. *All of them* means everyone inside it. Not a city — the platform has no
  borders and would not use one.
- **Drawn spot** — where a player is drawn: one fixed point inside their **Location area**,
  offset from the cell's centre by a stable digest of who they are, the same for every viewer
  and never leaving the cell. *Neighbourhood-true, building-false.* The one-decimal distance
  every surface prints is measured between two drawn spots; the Fit is not, and does not move.
- **Bearing** — the direction from the viewer's drawn spot to another's, north 0, clockwise,
  served on a Reading's rows and never derived by a client. With the distance it is the whole of
  a position: *distance and bearing only — never an address, never a street.*
- **Deal** — one invocation of the **deck**: a bounded, ordered batch of cards, shown one at a
  time. The deal is the unit, not the card, because the deck's ordering — the lifted by rank key,
  the person who already said yes to you among them and unmarked, then the rest ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4) — is a
  property of a whole deal and cannot be evaluated a card at a time. A **spent deal** is not an empty pool: it deals again, as a new **Search**, and only a
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
  list** — name, photo, area, Social tags, level, band, **likely range**, the photograph's
  **on-court check** outcome, and the **record block** below — and it is assembled
  by the backend **after** the engine returns, on the seam **at stake** already rides, because the
  scorer is forbidden every field on it. The card carries the **Name** and never the nickname —
  a card is a place a person is *named*, and the `@nickname` is drawn on the record only
  ([ADR-0171](docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
  **The distance is not on it**: a card says only what its subject published, and a distance is a
  fact about a *pair*, so it is the one field that would change depending on who was looking
  ([ADR-0107](docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
  **Two entries in that list are not things their subject published** — the check's outcome, and
  every field of the record block — and they pass the same rule by its other half: each is a
  fact about **that person alone** and does not change with who is looking, which is where the
  distance failed. *A card says only what its subject published* is the shorthand; *nothing on a
  card is a fact about the pair looking at it* is the rule.
- **Record block** — the three fields of a Player card that say what the platform **watched this
  person do**, as against what they told it about themselves: their published **Player Score**,
  their count of **counted games**, and their **Run of form**. They come from contexts of their
  own rather than off the candidate index, which holds only what a player changes about
  themselves ([ADR-0111](docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)).
  **Every one of them is absent rather than nought** where the platform has watched nothing:
  *nought games* and *no record* would be one absence in two spellings, and a card spells absence
  once. A count includes a game nobody agreed a score for and a Run of form does not — *an
  unscored game is an evening, not evidence*
  ([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
- **Run of form** — a player's **last five counted results, oldest to newest**, each a win or a
  loss. **Outcomes in order and no dates, at any granularity**: a moment beside one of them would
  be activity recency, which no card carries in any shape
  ([ADR-0106](docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5).
  Fewer than five is a real answer and it is **never padded** — three results are drawn as three,
  and the gap is the client's to draw.
- **Forecast** — how the game would go, for a set of people. Three readings of one type and the
  words are not interchangeable: the **best-of-three** forecast answers *are these the right
  people*, the **arranged** forecast answers *is this the right way round*, and a
  **provisional** forecast answers the same question with a seat still empty, reading a
  half-empty side as if the missing player matched the one already there. Provisional is a
  property **of** the forecast and never a flag beside it, so the number cannot be rendered
  without its caveat. Filling the last seat makes the provisional figure and the arranged figure
  the same number, asserted rather than hoped
  ([ADR-0108](docs/adr/0108-a-forecast-is-a-route-not-a-search.md)). **A game's forecast is the
  arranged one, read beside the game for the reader** while the game has not happened, and it
  is the challenge card's own figure for the same court — one apparatus, never a second
  ([ADR-0161](docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
- **Concern** — the engine's own statement that one term of a match is genuinely weak, keyed to
  that term. *What counts as weak* is a judgement about weights and curves and is made where they
  live; how many to show is the client's. A card shows one, the breakdown shows all of them.
- **Pass** — *not today*, on a deck card or from the **Radar**'s record sheet — the same pass,
  about the same deck; the radar keeps drawing the person. **Write-only**: it is recorded, it suppresses, and no
  response ever carries one — not to the passer, not as a count. It carries its **Origin key**,
  because the only thing that could prove its suppression window wrong is the pass rate on
  re-shown profiles. **A pass is a statement about my deck, where a Block is a statement about a
  person** ([ADR-0128](docs/adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)), and
  every boundary follows from that: the suppression is **deck-only** and never reaches a search,
  which is a question about the city that a swipe may not edit; it is **one-directional**, so it
  costs the other person nothing, literally; and it **never escalates** — a second pass buys the
  same 30 days, because a pass that hardens toward permanence is a Block nobody consented to. The
  **suppression** lapses at 30 days; the **record** of the pass does not, because a lapsed
  suppression leaves no trace that a re-shown card is a re-show. **A reset clears the suppression** — *Show them
  again*, one route, one sport, together with the day's dealt memory and the Cool-off — and
  leaves the record ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §5).
- **Cool-off** — the deck's own window after a shared court: somebody a player has a live
  **Challenge** or **Game** with, and for 30 days after it is behind them, is **not dealt** to
  them. Deck only — a search keeps
  [ADR-0142](docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1's release, because a rematch is arranged in the chat the two already have and a deck is for
  meeting people. Equal to the pass window on purpose, and cleared with it ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §6).
- **Exposure** — how often a player has been **shown** in somebody's answer, counted per sport
  per week. It exists so that the same ten people do not sit at the top of every list: a player
  shown to nobody this week is lifted, and one shown far more often than most is sunk. Both are
  **silent and both only reorder** — exposure fairness is not a reason to show somebody a bad
  evening, so it may never admit anybody below the **quality floor**
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)). *Shown more often than
  most* is the week's ninetieth percentile, republished hourly rather than computed per search.
  The same ledger carries `NEWCOMER_ABSORPTION_CAP` — how often one player is volunteered
  into a **newcomer's** shortlist — as a second count in the same weekly bucket, which binds by
  dropping a lift and **never** by withholding anybody, and **nobody is told**, because nothing
  has happened to them. The count is kept; the cap *keeps its rule and refuses its integer*, so
  nothing binds on it yet. Counting it first is deliberate: the cap's falsifier is answer rate
  regressed on absorption, and an integer chosen against weeks of real tallies is one somebody
  can defend.
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
- **A bio.** Superseded 2026-09-14 by **Intro** ([ADR-0170](docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)): one line, fenced at the write, is the
  moderation story the refusal asked for. What is still refused is a paragraph, a second field,
  and any free text that is scored.
- **An interest inbox** — any **list or badge** of who has said *Let's play* to you. The signal
  exists only on the promise that it is silent, and a yes given under that promise is not consent
  to appear in somebody's inbox
  ([ADR-0109](docs/adr/0109-a-read-back-names-what-it-withholds.md)). **A count is the one
  exception** — **Want to play you**, above — and it names nobody ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4).
  A tag on a person already being shown is not an inbox — the builder's list draws it, and so
  does the record sheet reached from the **Radar** ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4).

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
- **Relaxation may only relax what the searcher asked for.** Radius and their own weekly
  hours are asks, and an ask may be widened — by the player, on offer. A term, a weight, a
  measurement and the quality floor are the engine's judgement about what makes a good game, and
  scarcity is never a reason to move one. Raising scores until candidates clear a fixed bar is
  lowering the bar, whatever the config file calls it
  ([ADR-0099](docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **Availability overlap is evidence that a game can be arranged; it is never a proposed time.**
  The matcher matches players and stops. No court is booked and nobody can promise a slot before
  one exists, so the soonest shared hour is a reason on a card — *"you're both free Saturday
  at ten"* — and never a booking. Who plays when is agreed by the players themselves.
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
- **Nothing on a card is a fact about the pair looking at it.** Every field of a **Player card**
  is a fact about **that person alone**, so no field changes value depending on who is looking —
  which is why the distance between two people sits on the *candidate* beside the card and never
  on it ([ADR-0107](docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
  Most of them are things the player themselves put there — a photo, an area, their tags, a
  level they proved — and **four are the platform's own observation of them**: the photograph's
  **on-court check**, and the **record block**'s Player Score, counted games and Run of form. *A card says only what its subject published* was the original spelling of this
  rule and it was narrower than the rule: each of those observations is still a fact about one
  person, and each arrives through a port at assembly time rather than off the candidate index.
  **What stays refused is refused for its own reason, not by that shorthand** — activity
  recency at any granularity, which the engine computes and may never show; a Liveness number;
  gender; free text; and any block, pass or decline.
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

### Challenges (`backend/app/modules/challenges/`)

> **Classic play** ([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)): this context is the challenge-and-plan loop, now behind the *Classic play* flag. A group's **Challenge card** (a member's **Post**) is a Proposal in Part 2, not a challenge here.

Settled by [#221](https://github.com/Raketa02/Raketa/issues/221), built first as an
**aggregate** ([#250](https://github.com/Raketa02/Raketa/issues/250)) — the model, its six
events, the derived Standing and the one-open-challenge-per-pair rule — and **served since**:
`GET`/`POST /api/v1/challenges` with its accept and decline. Beside the routes, a background job
lapses a seat past its answer window — not to change what a standing *is*, which is folded from
the seats and the clock either way, but so that *answers challenges* has a denominator. It is the
context the matcher has been citing since
ADR-0098 without being able to name: `matchmaking`
ends at a ranked list, and *asking somebody* begins here. It is deliberately **not** called
`matches` — that word promises results, history and a played game, none of which is in scope —
and it deliberately does not live inside `matchmaking`, because the matcher reads challenges
through a **port** precisely so it does not own them. Those three things now have a context of
their own, **Games** below, and this one hands over to it at exactly one instant: when a
line-up completes, through a port declared here and signed there
([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).

Its whole subject is the span between *send* and *everybody has answered*. Nothing about when,
where, money, results or the conversation itself belongs here.

- **Challenge** — one player's ask to play, sent to everybody on a built court at once, and
  answered by each of them separately. **One challenge, however many people are in it**: a
  doubles send is one thing containing four, not four things. Identity is its own, not the pair's
  — the same people may be challenged again later, and that is a new challenge. **It ends one of
  four ways** — declined, lapsed, withdrawn, or **called off**, the last for a court that has been
  a game and ends with it — **and every ending names whose act it was** (`ended_by`;
  [ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)).
- **Seat** — one position on the challenge's court: a **Side** and either an occupant or nothing.
  The seats are a fixed list of `2 × seats_per_side(sport)`, so *which side is short* is a fact
  the challenge holds rather than one a reader has to count. A seat is **open** when nobody is in
  it, or when its occupant declined, lapsed, or **left**
  ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md); before the
  court is whole too, since [ADR-0165](docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)).
  The occupant stays on the seat with the answer that emptied it, because the three are three
  different facts.
- **Departure** — a player **leaving a court they had agreed to**, before it is played
  ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md); before the
  court is whole too, since
  [ADR-0165](docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)).
  Lands on the challenge, as a fourth answer, `LEFT`, written over an accepted seat: the seat
  reopens, the **Standing** is *Line-up incomplete* again, and — where the court has become a
  game — the game is told in the same transaction. **The departure that leaves one player on a
  game ends the court**: it records the challenge's ending, *Called off*, with the leaver as the
  one whose act ended it, and calls the game off in the same act ([ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md); the rule is
  ADR-0165 §3's, narrowed by [ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §2: a court is over by its seats when **nobody is on it**,
  whoever is still deciding, or when one player is and no seat awaits — so the last seated
  player's departure ends it even with a fill still pending, and that invitation with it).
  Before a game the same rule ends the court as *Declined* — a departure is a no.
  Any player on the court may leave, the
  organiser included; on a game, while it awaits its entry and its agreed moment is ahead —
  after the moment it is refused, so a no-show cannot vacate a seat to
  block the result. Two may leave. The one who left is out of this court's own pool for good and
  a stranger to the others again on the instant. **Recorded and not yet scored.** After the moment,
  the exit that is still open is the room's — **Leaving the chat**, which moves no seat
  ([ADR-0168](docs/adr/0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md)).
  **Leaving is met in one place**: the conversation row's swipe on Chats ([ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §4).
- **Organiser** — the player who sent it. They hold a seat like anybody else, and it is
  **accepted from birth**, because they are the one proposing. That is what makes *"every seat
  accepted"* the whole of the completion rule, with no special case for singles.
- **Arrangement** — the sides the organiser built, recorded with the challenge and shown to the
  people answering it. The invitee answers *the arrangement proposed*, never a better one worked
  out afterwards. **Sides only**: the forecast percentage is not stored, because it follows from
  the sides and a stored copy goes stale the next time a ruleset ships.
- **Standing** — what a challenge *is* right now: `AWAITING_ANSWERS`, `ON`, `LINE_UP_INCOMPLETE`,
  `DECLINED`, `LAPSED`, `WITHDRAWN`, `CALLED_OFF`. **Derived from the seats and the clock, never
  stored** — with two exceptions, below. A status column would be wrong for the whole gap between
  a deadline passing and a sweep noticing, and it would be the copy that gets believed. *Challenge
  sent* and *Challenge for you* are not two standings — they are one standing read from two sides.
  `LINE_UP_INCOMPLETE` is reached **after `ON`** too, by a **Departure**: the court is half built
  again, the pair is held again, and the next completed line-up re-seats the same **Game**.
  **`CALLED_OFF` is the seventh, and the game's fourth end seen from the court**
  ([ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)): a court that has been a game ends **with its game**, by the **Departure**
  that deserts it or by **the hour** ([ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §3), and never by its seats alone or by a press.
  It is an ending like the other three — dated, on the inbox's shelf, never re-entered, the pair
  released — and **every ending names whose act ended it** (`ended_by`), with one exception that
  names nobody: the last leaver, the organiser who removed it, the seat whose *no* or departure
  completed the desertion, the seat whose window ran out last — and *nobody*, where the hour
  called it off.
- **Withdraw** — the organiser **removing** a challenge nobody else has joined
  ([ADR-0142](docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md),
  its *where* moved by
  [ADR-0165](docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)).
  Legal exactly while **nobody besides the organiser holds an accepted seat** — before anybody
  has answered, and again once everybody who joined has left — and refused while anybody else is
  in: a court somebody has joined is nobody's to end for the others, and it is **over by itself**
  when at most one player is on it and no seat is still deciding. The player-facing name is
  *Remove the challenge*. **Whole-challenge, and it removes nobody** — a withdraw that emptied one
  seat would be the organiser taking out somebody who already agreed. **Irreversible**: asking the
  same people again is a *new* Challenge, with fresh deadlines and its own record of who has
  answered — and that re-ask is the risk ADR-0142 refused and ADR-0165 accepts with a falsifier.
  **It does not reach a court that has been a game** ([ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md), superseding
  [ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)'s *it reaches one*; [ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §1): such a court is
  nobody's to end, and the route refuses it with `court_has_been_a_game`. *Withdrawn* is the
  ending of a court nobody had joined, and nothing else.
  The word is *withdraw* and not **stand down**, which this file owns platform-wide for a term
  that cannot be evaluated; *call off* is the **Game**'s ending and the court's word for it.
- **Call off** — ending a court that has been a game, **and its game with it**, in one
  transaction ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md), [ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md),
  [ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)). **Nobody presses it.** Two things reach it and no third: the **Departure** that
  deserts the game — the leaver as `ended_by` — and **the hour**: a court still short of a player
  when its agreed moment passes (the end of its horizon, where no day was agreed) is called off
  by the platform, with `ended_by` and `called_off_by` **nobody**, written by a sweep every
  minute because the court cannot read the plan whose hour it is. Each records the challenge's
  ending, `CALLED_OFF`, and hands *call off* to the **Game** in the same transaction, which
  reaches its fourth end, *Called off*, in neither tally — nobody is charged. Only while a seat
  is open — a full court that will not play lets its window lapse into *Never played*, as today.
  The room is destroyed in the act. A game whose window already closed on the open seat is a
  ghost, and stays one: the hour ends the challenge alone, and the ghost is not un-charged.
  **One word, everywhere** — the tag, the row, the screen; the row's sentence for the hour is
  *Nobody filled the seat*. _Avoid_: *cancel*, which appears nowhere; *Call it off*, which was
  a button and is not.
- **Answer window** — how long one invitee has to answer, **dated per seat when that seat was
  invited**. Seats filled later start their own day; they cannot inherit a deadline from a send
  they were not part of.
- **Lapse** — a seat whose answer window passed with no answer. **A lapse is not a decline.**
  They do the same thing to the line-up and they are different facts: *answers challenges* is a
  **Strand** over challenges that got an answer inside their window, and it is unmeasurable if
  silence and a no are one event.
- **Open challenge** — a Challenge that has not ended. What the matcher excludes a pair on. Read
  from the seats and the clock like the Standing itself, so a seat whose window has passed is not
  open whether or not anything swept it.
- **Challenge load** — how many seats are waiting on one player's answer: invited, unanswered and
  still inside their window, **across every sport**. Not what they organised and not what they have
  already accepted — the matcher sinks a player on load to predict *will this person answer me*,
  and somebody with eight sends out is over-committed but is not slow to answer.

**Invariants**

- **A challenge stands as long as somebody other than the organiser is still in it** — accepted,
  or yet to answer. A decline reopens that one seat and disturbs nothing else, because the people
  who already agreed did nothing wrong; but when the last of them is gone, there is nobody left to
  keep faith with and the challenge is over. Singles gets the right answer for free. **Unless the
  court has become a Game** ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)):
  the organiser alone on a court whose opponent left is a game with a seat to fill, not a send
  nobody answered, so such a court reaches neither ending by its seats — its exits are a re-seat
  and calling the game off.
- **Membership grows one acceptance at a time, and that is the point.** Each accept is
  consequential the moment it happens rather than a step toward a total: it admits one person to a
  conversation that starts as soon as the second player is in it, and grows as the others arrive.
  So `challenges` publishes **one event per acceptance** and never a single *the challenge is now
  on*. **Line-up incomplete is not a waiting room.**
- **An acceptance is to the game, not to the side.** An accepted player may be moved across the
  net afterwards and their acceptance stands: the membership is settled, the arrangement is still
  the organiser's to choose. They may never be removed or replaced.
- **Only the newly seated are invited.** Completing a half-built line-up asks the people who were
  not already in, and nobody else. Asking somebody twice reads as the platform having lost track
  of them, and it damages the very answer record the matcher reads as reliability.
- **Once the court is full, the sides are frozen.** The only door back into an arrangement is an
  open seat, and a send with nobody new to invite is refused rather than recorded — so there is no
  such thing as a rearrangement on its own.
- **One open challenge per pair, across every sport.** Two people are either arranging a game or
  they are not; asking for padel while your tennis challenge sits unanswered is pestering with a
  sport chip on it. **The rule stands on that argument alone.** The matcher's `OpenChallenge`
  carries no sport, but it is an internal port type that appears in no published document — so no
  shipped contract requires this rule, and none would stand in the way of narrowing it.
  **Sharing a line-up makes a pair**: every occupied seat but your own is somebody you have an open
  game with, co-invitees and organiser alike — and a seat that declined or lapsed is empty again, so
  that person is a stranger to you once more the moment they leave.
- **The rule asks whether two people are still *arranging*, and a completed line-up is not.** It is
  held while a **Standing** is *Awaiting answers* or *Line-up incomplete*, and released otherwise —
  which is **not** the same as *has this challenge ended*. A challenge every seat accepted has not
  ended: it produced a **Game**, the sides are frozen and the client still prints *On*. But the
  arranging is finished, so the pair is released, the two of them are back on each other's surfaces
  and they may arrange a second game. **An unplayed game carries no block of its own here, and that
  is decided rather than deferred**: the record that built a port onto `games` to bound the mutual
  mint declined to use it on this path, because a send is somebody deliberately choosing a court
  ([ADR-0142](docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1, settled by
  [ADR-0152](docs/adr/0152-a-mutual-mints-again-once-the-last-one-is-finished-with.md)).
- **A mutual yes asks its own question, and it is an *idempotence* question.** *Let's play* is a tap
  that costs nothing and the game is opened on the **mutual**, not on the tap — so a repeat tap has
  to be refused by something. A singles challenge born of two yeses is *On* the instant it exists,
  so the rule above lets those two go immediately, and what the mint asks instead is **one mutual
  mints one game**. It asks the rule above as well, and both must pass — so the mutual path is
  **strictly** stricter than a send rather than accidentally so. **The asymmetry is the point**: a
  send is somebody choosing a court, and a repeat tap is the same yes pressed twice.
- **A mutual mints again once the last one it minted is finished with**
  ([ADR-0152](docs/adr/0152-a-mutual-mints-again-once-the-last-one-is-finished-with.md)).
  *Finished with* means **still being arranged, or its game not yet settled** — so a doubles mutual
  holds the pair while its half-built court stands, a game holds them until nothing more can happen
  to it, and a mutual-born challenge that ended without ever producing a game holds nobody.
  **Settled is not played**: a ghost game is settled, and two people whose arranged game evaporated
  may try again. The question is asked **per sport and about mutual-born challenges only**, so a
  tennis game minted from a mutual no longer refuses a padel one — the permanence that survived on
  this path when the pair rule was released, and the reason it is now the mutual's *own* question
  rather than a borrowed one.
- **A mutual names the game it has, and names nothing when it has none**
  ([ADR-0154](docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md)).
  The mint answers with **the challenge this mutual has open** — minted by this tap, or by an
  earlier one and not yet finished with — so a repeat tap points at the game the first one made
  instead of saying nothing. It answers **nothing** when the two already have a game **being
  arranged** — a send, or this mutual's own half-built doubles court, since *being arranged* is
  the condition and not *whose* — and when a gate refused; and those two are folded on purpose:
  an absence covering one innocent cause and one withheld one is publishable, and an absence that meant only *a gate
  refused* would be the trace a **Block** is guaranteed never to leave. So *no game here* may be
  said and *why* may not — the same rule a **withheld** row is stated under
  ([ADR-0130](docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)). **`mutual`
  itself does not move**: it is what the two rows say, and reporting it false because a gate
  refused would tell the sender something about the other person no refusal may say.
- **No day, part of day, hour or place is ever attached.** The challenge carries a **Window**
  derived from the grid, and the players agree the hour themselves once a court can exist.
- **A late answer is refused.** Past your own answer window the seat already reads as lapsed and
  the organiser may have offered it to somebody else; an accept that resurrected it would be
  contradicting a card the platform already drew.
- **Nothing announces a conclusion the seats already imply.** There is no `GameOn`, no
  `ChallengeExpired`, no `ChallengeDeclined` — a **Standing** that is derived has exactly one place
  to be true, and an event saying otherwise would become the second.
- **An event may announce a conclusion only when no arrangement of the seats could reach it**, and
  exactly two do. A **Withdraw** is a decision a person took and there is nothing in the seats to
  fold it out of, so `challenges.withdrawn` is the fact's *only* home rather than a second one, and
  the fold reads it exactly as it reads an acceptance. A **Call off** is the second
  ([ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)): the seats can reach *deserted*, and cannot reach *the game this court became
  is called off* — a court deserted by a fill's newcomer's no is not called off — so
  `challenges.called_off` is that fact's only home too. The rule above is unchanged and these are
  its two exemptions; they are kept to two by a test that folds every arrangement of every court
  this context can hold and asserts that `WITHDRAWN` and `CALLED_OFF` are the only Standings none
  of them reaches.
- **A withdrawn invitation is not a lapse.** Somebody who was still deciding when the challenge
  stopped existing is neither answered nor lapsed and is absent from *answers challenges*'
  denominator, exactly as the organiser's own seat is. That Strand prices **silence**, and this
  is not silence.

### Games (`backend/app/modules/games/`)

> **Grows with [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: a **Booking** (Part 2) opens an ordinary Game when it reaches *booked*, exactly as a completed line-up does; the result, the stars and the record follow unchanged. *Nothing about where or money* stays true of this context — the Booking holds both.

Settled by [ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) on
[#303](https://github.com/Raketa02/Raketa/issues/303). **The context that knows a game was
played**, and before it nothing on this platform did: a Challenge carries a Window and never a
date, a time or a court, so four acceptances left no fact behind. Every empty block on the
redrawn competitive card traced back to that.

It is **event-sourced**, and that revises the deleted ADR-0034, which argued a record about a
product — courts, money, departures, four cancellation flags — that the 2026-08-25 reset
removed. What is left of a game is a plan, a moment, a score and a two-sided disagreement, and
the disagreement is the whole of it.

Its subject is the span between *everybody accepted* and *there is nothing more to say about
this evening*. Nothing about where, money, or the conversation belongs here, and neither does
anything about how good anybody is — that is the rating context reading this one.

- **Game** — one arranged game and its result. **Opened by a completed line-up**, in the
  transaction of the acceptance that filled the last seat, and never by a request: nothing a
  client sends can produce one, which is what makes *these people arranged this* a fact rather
  than a claim. One game per arrangement, for ever — and **re-seated** by the next completed
  line-up after a **Departure**, same id, same `planned_at`, same plan, same room
  ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)). It reaches
  **four ends**: three folded from the record and the clock, and a fourth — **Called off** — that
  is announced, told by the challenge while a seat is open — the **Departure** that deserts it,
  or the hour that finds it still short of a player — **and the fourth end says who**:
  `called_off_by`, the leaver and their name, or nobody for the hour
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md),
  [ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md),
  [ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)).
- **Line-up** — who is on the court and on which side, **frozen until somebody leaves it**
  ([ADR-0162](docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)). An
  acceptance is to the game and not to the side, so the membership is settled the moment the last
  seat accepts; nothing in this context moves anybody on its own. It moves in exactly two told
  ways: a **Departure** opens one seat, and the next completed line-up **re-seats** the whole
  court. **An open seat is a seat** — drawn empty, in its place, never dropped — and a result is
  refused while one is open.
- **Kind** — **counted** or a **friendly**, stamped when the game is arranged and never derived
  at the end. A friendly is a thing people *choose*: reclassifying a counted game because nobody
  typed a score would hand a player the exact evening they said they did not want, and would
  give one word two meanings. A game arranged from a surface that asks for no kind — the deck,
  a mutual yes — is **counted**, because counted is what the platform is for and a friendly is
  the opt-out — **unless either of a mutual's pair declared the sport *for fun***, in which case
  the challenge is minted `FOR_FUN` and the game honours that wish
  ([ADR-0169](docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §8). *No
  preference* and *never declared* choose nothing.
- **Result** — *we played, here is the score*. **The entry is the record that the game
  happened**, and it carries the moment: there is no booking, no calendar and no date field
  anywhere, so the moment a player says it is the moment it was.
- **Score** — the sets, absolute rather than from anybody's point of view. **A score names a
  winner**: a level set has not finished and none of the four sports produces a draw, so a level
  score is refused. *Set* is used for whatever the sport calls its unit.
- **Proposal** — a score on the table, **one per side**. The cap is what bounds an argument to
  two rounds, and it is what makes silence safe to read as agreement.
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
- **Standing** — what a game *is* right now: `AWAITING_ENTRY`, `NEVER_PLAYED`,
  `AWAITING_ANSWER`, `CONFIRMED`, `UNSCORED`, `CALLED_OFF`. **Derived from the record and the
  clock, never stored** — and never announced, with one exception: `CALLED_OFF` is a decision a
  person took, folded off `GameCalledOff` and read first, on the same exemption `WITHDRAWN` has
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). It is an end, and it is
  **neither an evening nor a ghost**: a ghost is silence and this was an act, so it is in no
  tally and moves no **Strand**. Spelled `GameStanding` in code and on the wire, because
  Challenges already publishes a `Standing` component and a second class of that name would
  *rename* it rather than shadow it — **the contract is one namespace, and the cost of a
  shared word is paid by whoever arrives second.** The same is true of `GameSide`.
- **Counted game** — a counted-kind game somebody said was played, **scored or not**. What
  `player_card.counted_games` prints and what §9.10's newcomer predicate reads.
- **Ghost game** — a plan whose entry window closed with nobody ever saying it happened. Kept
  distinguishable from a played game, because familiarity is about people who actually played.
  A **called-off** game is not one: the window did not close on silence, somebody ended it.
- **Dismissal** — a player clearing a **called-off** court from their own two lists: the
  game's card from Now and the challenge's row from Chats
  ([ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §5,
  [ADR-0173](docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)). The
  reader's own act, admitted on a game that is *Called off* and on no other standing — from the
  Now card's trash for somebody on the game's court, and from the Chats row's swipe for
  **everybody the court asked**, the invitee still deciding when it was called off included
  ([ADR-0175](docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §5); **recorded once per player on the game's stream, and its effect derived on every
  read** — the reader's Now omits a game they have dismissed and their Chats omits its row, both
  read off the one set, on the shape the room's *Leaving the chat* has. It
  removes a court from the reader's lists, not a fact: the game, its record and the challenge are
  untouched, nobody else's Now or Chats moves, and there is no undo. The player-facing name is
  *Remove this card* on the card and *Remove this row* on the row — one act, named by what goes
  where it is pressed. _Avoid_: *hide*, *archive*, *delete the game*, *remove the challenge* —
  the first two do not exist, the third is not what happens, and the fourth is the withdraw.

**Invariants**

- **Silence confirms.** A lone score nobody answers stands when its window closes, and the game
  counts. There is nothing anywhere in this context called *confirm*: a result is agreed when a
  clock passes, and a clock is nobody's request.
- **Two standing scores nobody accepts leave the game unscored — and an unscored game is an
  evening, not evidence.** It is in history, it is in `counted_games`, it establishes that these
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
  no `GameUnscored` and no `GameNeverPlayed` — the same rule `challenges` states about `GameOn`,
  and for the same reason: a derived standing has exactly one place to be true. `GameCalledOff`
  is the one event that announces an end, and it may because no arrangement of the record could
  reach it — `challenges`' exemption, argued again in
  [ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md).

### Conversation (`backend/app/modules/conversations/`)

> **Grows with [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: a game made in a group has **one chat**, opened when the game is booked rather than by a first acceptance, whose members are whoever is in the game now; it is reached only from the game's details, and the Chats tab is **Classic play**'s (Part 2).

Settled by [ADR-0146](docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) on
[#332](https://github.com/Raketa02/Raketa/issues/332), with its lifetime from
[ADR-0153](docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md),
which moved
[ADR-0142](docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)'s
— narrowed by ADR-0164 §6: a room **without a game** has ended exactly when its challenge is
over, and a room with one keeps the game's clock.
**Built.** The module exists, the four routes are on the player contract, a room is opened and
grown through the outbox by contexts that do not know it exists, and it is **destroyed** once the
episode it was opened for is over — derived on every read, and made real by an hourly sweep
([#359](https://github.com/Raketa02/Raketa/issues/359)).

**The place two people who have agreed to play talk about it.** It is deliberately **not** called
`Chat` — that word promises messaging between anybody, searchable and permanent, and this context
refuses all four; *Chats* is also the **tab**, which holds challenges as well as conversations, so
the word names the container rather than the thing in it. `games` used *conversation* in prose for
the result argument; that argument's terms are **Proposal**, **Correction**, **Counter** and
**Acceptance**, and the word belongs to the aggregate that needs it.

Its subject is the span between *the first acceptance* and *there is nothing left to arrange*.
Nothing about when, where, money or the result belongs here — it is **told** about all of them.

- **Conversation** — one purpose-bound thread, opened by the **first acceptance** and never by a
  request. **The purpose is the episode** — arrange the game, play it, find out what happened —
  rather than the arranging alone, which is what decides when it ends. It **grows with each
  acceptance** rather than opening complete
  ([#221](https://github.com/Raketa02/Raketa/issues/221)), which is why `challenges` publishes one
  event per acceptance and never a single *the challenge is now on*. A conversation opened by a
  mutual deck yes is the same thing and is listed the same way.
- **Member** — somebody who has agreed to be on this court **right now**. **Derived, never
  stored**, from whichever record the room is currently about: the challenge's accepted seats until
  the line-up completes, the game's frozen line-up after. One rule read against two records, not
  two rules. **Minus the members who have left the chat, for as long as the game is behind them**
  ([ADR-0168](docs/adr/0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md)) — the
  one membership fact a room stores, a subtraction only, whose effect is read against the game on
  every read: a room can never hold somebody the court does not. **Not a Group member**, who
  belongs to a Group and is on no court by belonging.
- **Leaving the chat** — a member's own exit from the room, **not a Departure**: no seat moves.
  Admitted exactly where the seat change is refused — the game's agreed moment has passed, or the
  game has happened or never will — and refused while the game is ahead, where leaving the chat
  still means leaving the game
  ([ADR-0168](docs/adr/0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md), narrowing
  [ADR-0165](docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)).
  Recorded once on the room's own stream, told to the others as *{name} left the chat*, and never
  undone by a message; a plan moved ahead again puts the leaver back, because a game that is ahead
  is a game they are in. The leaver's row goes by membership; the room is untouched for everybody
  else and ends on its own clock. _Avoid_: *leave the conversation*, *archive*, *hide*, *mute* —
  none of them is this, and the last three do not exist.
- **Message** — what a player typed. Content, crossing as-is, with an author in the ordinary
  sense.
- **System line** — what happened, as a **code and its values**, rendered by the client. **Not a
  Message with a kind**: the backend sends codes and never display text
  ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), and nobody typed
  *Tomek set the day*. The two share one stream and one sequence number and are two shapes in it.
- **Sequence number** — a conversation's own count of what has landed in it, minted on append and
  **gapless**, because a count that skips is not a count
  ([ADR-0147](docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)).
  The cursor for ordering, paging, de-duplication and reconnect, and the reason this context may
  subscribe to the outbox where the candidate index could not
  ([ADR-0110](docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md) —
  *two subscriptions, two guarantees*). **No reader may infer loss from a gap** — the promise is
  the server's, and nothing is permitted to depend on it.
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
  **destroyed, not delisted**. It ends at the earliest of: the entry window closing, so *we played*
  can no longer be said; a grace after somebody says they played; and, for a room that never
  produced a game, **the challenge being over** — exactly then, with no grace (ADR-0164 §6). A
  withdrawal destroys it in the same act
  ([ADR-0153](docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)),
  and so does a court that has been a game being **called off** — told by the challenge's own
  ending and by the game's, whichever arrives first, with no line written
  ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md), [ADR-0172](docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §6). **A member leaving the
  chat is not on this list**: their row goes by membership, and the room lives to its clock for
  everybody else
  ([ADR-0168](docs/adr/0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md)).

**Invariants**

- **A conversation is told, and tells nothing.** Its lines are written from events `challenges`,
  `games` and `plans` publish through the outbox, and **none of those contexts knows it exists**.
  It is a subscriber, never a participant in anybody's transaction.
- **There is no messaging between strangers**, and there is no conversation without an arrangement
  behind it. That refusal is the product: it is what keeps this a sports app rather than a place
  people are reached.
- **No system line announces a derived standing.** There is no *Game on* line — the same rule
  `challenges` and `games` each state, applied to a stream: a folded standing has exactly one
  place to be true, and it is not a sentence in the backlog.
- **No sentence is ever stored.** A rewritten line rewrites the whole history, which is what a
  stored string could not do.
- **Presence stops at *is somebody typing right now*.** There are no read receipts, no `seen_at`,
  no online and no last-seen, and each is refused on the same property: nothing about Typing is
  stored anywhere, so there is nothing here for one of them to be built out of
  ([ADR-0156](docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).

### Plan (`backend/app/modules/plans/`)

> **Classic play** ([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)): a game made in a group has no plan — its **Booking** names the club, the court and the hour.

Settled by [ADR-0144](docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md) and
[ADR-0145](docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md), named by
[ADR-0146](docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md), and given a
**Lock** by
[ADR-0155](docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
which supersedes ADR-0144's *There is no lock* and nothing else in it — and **re-keyed to the
challenge** by [ADR-0164](docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md), which supersedes ADR-0144's *a plan is the game's* and its *no plan before
the line-up completes*, and nothing else in it.

**Where and when these people are meeting.** It is **one challenge's**, identified by that
challenge's id — the one id its room and its game already share — and the game the challenge
becomes inherits it. It is **born by being used** — no record at birth, no opening event, and *no
plan* is what a court with nothing agreed draws — and it is drawn in the room **from the room's
opening**, with whoever is in: `challenges` ends at *everybody has answered* and `games` begins
at *played*; this sits beside the first and before the second, and belongs to neither.

The word will one day collide with Around's *plans*. It is taken anyway, on this file's own rule:
**the cost of a shared word is paid by whoever arrives second**.

- **Plan** — three slots, in the order people discuss them and of decreasing negotiability:
  **where · day · hour**. One plan per challenge, for ever; the game it becomes inherits it.
- **Where** — short free text, one line, capped. **Never a court**: no id, no lookup, no
  autocomplete, no reuse, no geocode, and nothing anywhere reads it. A note between the people on
  the court. **Nor a Club**, once clubs exist: linking a plan to one is its own later decision
  ([ADR-0182](docs/adr/0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §8).
- **Day** — a local date, chosen from **seven chips, today + 6**, clamped to a week past the
  plan's **anchor** — the challenge's send until the game exists, then the game's `planned_at`,
  only ever later — so a plan can never name a day past the game's entry window.
- **Hour** — a minute of the local day, in **30-minute steps, 06:00–23:00**. It is **the
  agreement itself**, not a guess at a booking: nothing on this platform will ever hold a booking,
  so nothing can contradict it (ADR-0145). *True of the **Classic play** loop only: a game made
  in a group is booked when it fills ([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md), Part 2).*
- **Agreed point** — the plan's moment, derived and never stored. The agreed **instant** when the
  day and the hour are both recorded; the **start of the following local day** when only the day
  is; nothing at all when no day is. Later rather than earlier, so nobody is asked for a result
  before they could have played.
- **Slot count** — how many of the three are filled. Derived. It says **how far along a plan
  is** and nothing more: three filled is a plan everybody *could* agree, which is not the same
  fact as somebody having agreed it.
- **Lock** — somebody agreed the plan. An **act**, with an actor and a moment, and it is
  **not the slot count under another name** (ADR-0155). It is the one fact here no arrangement
  of the three slots reaches, because nobody wrote it down — which is why it may announce
  itself where a completed plan may not. **It freezes nothing**: any member may still move any
  slot afterwards, the plan stays locked, and the move writes its own line. **There is no
  unlock**, for the same reason a slot is never emptied — the lock is a thing that happened.
  **And it waits for the court**: refused while the court is not whole (ADR-0164 §5), because
  *we are agreed* is said only once everybody who will have to keep it is in — the slots are
  proposals anybody on the court may make and move; the lock is the promise.

**Invariants**

- **Any member may fill or change any slot, any number of times**, and every change writes a
  system line naming who and what. **The line is the friction**; there is no rate limit and no
  history beyond the lines.
- **A slot may be changed but never emptied, and a plan is never unmade.** Nobody turns up and the
  game ghosts; there is no cancellation, because `games` opens one game per arrangement for ever.
- **The plan never writes to `games`.** `planned_at` keeps meaning *when it became a game*, and a
  planned moment and a played moment never reconcile — the entry is the record that the game
  happened, and it carries its own moment.
- **One platform zone**, recorded as a locale assumption rather than a constant to tune. Its
  falsifier is the first shard whose players are somewhere else.
- **The game leaving its entry window is the only thing that freezes the slots**, read through one
  port asking one question. **Locking is not a second freeze**, and there is no third.
- **Locking an already-locked plan records nothing.** The same act twice lands the same state,
  and the first lock's moment is the one that stands. **Locking an incomplete plan is refused**
  — the two shapes differ deliberately, because a silent no-op there would leave somebody
  believing they had agreed a plan.

### Player Score (`backend/app/modules/player_score/`)

What the platform has watched a player *do*, as distinct from how well they play. **One number
in the UI, six strands underneath it**, and the matcher reads the strands separately because
they are weighed oppositely in the two modes
([ADR-0098](docs/adr/0098-matcher-demands-as-executable-contracts.md)). The words are the
player's before they are the matcher's: they are read on the player's own screen.

**Three of the six have a source and three do not** — decided by
[ADR-0140](docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md),
which also settles the clause ADR-0137 opened about whether *shows up* survives at all, and by
[ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md), which adds
the third.

- **Player Score** — the blended number a player sees, out of a hundred. Computed from what
  happened, never from opinions and never from results: **losing costs nothing here.** The
  blend is over **the strands that are there**, renormalised, so a player the platform can see
  two things about is comparable to one it can see five about, and neither is credited for a
  record nobody keeps.
- **Strand** — one of the six things the score is made of. Each is a record of **opportunities**
  and what came of them, and each is published in its own right. An opportunity is something
  that **fell due**: a strand never counts a question still waiting for its answer.
  - **Shows up** — whether the game gets played at all. **Live.** The opportunity is a plan that
    settled — a game somebody said had happened, or a **Ghost game** whose entry window closed
    on silence — and the good outcome is the game. **A ghost is charged to everybody who was on
    that court**, because nobody proposed anything and nobody countered anything: what is priced
    is an arrangement that dissolved, and there is nobody in it to blame.
  - **Answers challenges** — whether a challenge gets an answer inside its window. **Live.** The
    opportunity is an **invitation** — a Seat somebody was actually asked to take, which is a
    seat with a deadline, so the organiser's own seat and both seats of a mutual-born challenge
    are not opportunities. **A decline is a good outcome**: one of the two strands where a no
    scores, because what it prices is silence and not judgement.
  - **Answers about results** — whether a score put in front of a player gets an answer inside
    its window. **Live** ([ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)).
    The opportunity is a **score put to you**: the entry that records *we played* records a
    score in the same act, so one side opens and the other is asked, and once both sides have
    put a score up nobody is asked anything further — the opener facing a counter may only give
    way, and pricing that would price surrender. **Accepting counts and countering counts**, so
    this is the second strand where a no scores; what it prices is silence until the window
    closed. **It is not *confirms results* under a new name** — see below — and it is the only
    strand that **forgets**: opportunities older than twelve months fall out of it.
  - **Keeps plans** — whether an agreed plan survives to its day without a late change. **Stands
    down:** no plan on this platform has a moment to be late for, which is why `games` publishes
    its late-change threshold as an honest absence.
  - **Settles up** — whether a court share that fell due was settled without a case. **Stands
    down:** court money is out of scope. It is the **historical record**, never the live case —
    the open case is the Hold.
  - **Sportsmanship** — what opponents said afterwards. A mean, not a ratio. **Stands down,
    and now permanently**
    ([ADR-0158](docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)). The
    surface it was waiting for exists — see **Sportsmanship** below — and the reason it stays
    down has changed rather than lapsed: **it is not a strand and never was.** A star average
    is not a ratio out of a hundred, so it cannot be a term in a weighted mean over ratios;
    and the matcher must not read it in any shape, because it is the one thing here a person
    can weaponise with no appeal route behind it. It is published as **its own figure**, on
    the player record, under its own heading.
- **Confirms results** — **struck, and it stays struck**
  ([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). It read *whether a
  counted game gets confirmed, so it counts*, and it cannot be published honestly: **an
  unconfirmed result is a fact about a pair and a strand is a verdict about a person**, and
  every denominator tried on it docks somebody the Games context refuses to penalise — both
  sides of an honest disagreement included. Withdrawing it rather than leaving it unbuilt is
  ADR-0098's own rule about a demand nobody can satisfy; the matcher absorbs the loss by
  construction, because a strand nobody publishes stands down and the survivors renormalise
  inside the reliability term. `ReliabilityStrand.CONFIRMS_RESULTS` and its two ruleset weights
  came out with the provider, in ADR-0140.
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
  are **absent from the answer**, the reliability term stands down and the other terms carry the
  match. The same principle the rating engine already applies to skill. A strand nobody can
  publish is absent the same way, and neither is ever a `0` or a `0.5`.
- **This context keeps no record of its own.** It has no aggregate, no table and no migration:
  every strand is folded out of `games`' and `challenges`' streams when somebody asks. A stored
  score would be a second place for *did that game happen* to be true, and the copy would be the
  one that got believed.
- **The score is a memory, and it fades with new evidence.** Decay belongs here, on the side
  that owns the record; a consumer that applies its own would be counting the same forgetting
  twice. **The ratio is the fading** — one no-show among forty games weighs almost nothing —
  and there is **one** window, on one strand, named rather than general: *answers about results*
  forgets after twelve months, because turning up is a commitment somebody made and answering a
  score is a habit of opening an app, which is cheap to fail by accident and must therefore be
  possible to work off. It equals the matcher's horizon by choice and the two spellings are held
  together by a test, since a provider may not read the matcher's ruleset.
- **The published number is the player's, not the matcher's.** Its weights are
  **35 / 20 / 15 / 12 / 10 / 8** and live in this context, never in a ruleset: a weight
  release must not change what somebody's own profile says about them. It has three readers — the reliability floor, which prices it, the player card,
  which prints it, and the player record, which prints it **beside the rows it is the mean
  of** — and **a card explaining a match with a figure the player's own profile disagrees with
  is worse than a card that says nothing.** The **strand ratios themselves** now cross on that
  third surface, as a raw pair and the figure derived from it; the weights never do.
- **It is the platform's observation of a player, so it may not go on the candidate index**
  ([ADR-0111](docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)).
  It reaches a card through a port at assembly time, on the seam the name and the photo
  already ride.

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
  there a plan nobody ever claimed is settled too, and there is nobody to rate for an evening
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
  zero, and the matcher never reading it.
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
- **The matcher never reads it — the floor and the term.** A reader seeing the figure and
  deciding for themselves is the product working; the app demoting somebody silently on the
  same evidence, with nothing they can answer, is not. An import contract enforces it, because
  a Match Fit term reading a star average would look like every term beside it.
- **Not rating costs nothing, and the omission is not recorded.** No strand, no obligation, no
  penalty, and nothing anywhere that says a card went unanswered.

### Player record (`backend/app/modules/player_record/`)

**What the platform will say about one person to one reader**, current at the moment the
sheet is opened — and the context that decides whether it says anything at all
([ADR-0159](docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)).
It is `player_score`'s shape with a second job: **no aggregate, no table and no migration**,
every fact read through the owning context's published port, and one rule of its own —
**admission**.

- **The player record** — a *person*, not a pairing. The Fit breakdown answers *why 77* about
  two people; this answers *who is this* about one. It is a **route and not a card field**: a
  card is recorded and frozen into a search kept for ever, and a record is live, about one
  person, and read at most a few times a day.
- **A disclosure** — the thing that entitles a reader to open a record. A search of theirs
  that **returned** the subject, a **live challenge** they are both seated in, a **game** they
  both played, a **Group** they are both in, an **Official group the reader runs** that the
  subject is in, or *being the subject*. **Nothing else, and nothing expires but a group**: a
  search record is kept for ever, so a shorter window could only refuse a face the app is
  currently showing, while a group discloses its members only while they are in it and only to
  whoever runs it now.
- **The metered rows** — what the platform *watched* this person do, under the card headed
  *counted by the system, not written by people*. Each is a **raw pair and its figure**: how
  many opportunities fell due, how many went the way the strand is named for, and the
  percentage out of a hundred. Beside them is **the reliability pill** — the published Player
  Score, which is exactly the number the matcher acts on, so a player working their record back
  up can watch the penalty lift. Two rows today, `player_score`'s two live strands, read
  through that context's published port and never recomputed here. **The weights are not on the
  wire**: they are a fact about how the number is made rather than about the person.
- **The disclosure's partition** — the sport a disclosure happened in. The fail-closed
  gates are re-run live on every open **in that sport's partition** and never in whichever
  sport the reader arrived from, because the mutual gender gate reads an index row and the
  index is keyed by sport. A subject rated only in squash has no padel row, and *a gate that
  cannot be evaluated excludes*. **Whoever runs the subject's group has no partition**: the
  gender preference is the one gate that reads one, and it is not asked of them.

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
  domain types, so a card's closed list does not reach the record by the back door.
- **A career statistic is unbounded, and its read takes one player.** *Opponent variety* is
  every counted game the platform has recorded, with no window and no decay — a second window
  would be a figure that must not disagree with the matcher's horizon. Because the fold behind
  it is unbounded, the port answers about **one person and never a collection**: the fence is
  the signature, and a set-shaped version would be an invitation to call it inside a search's
  walk over five hundred candidates.
- **A raw pair crosses, and the sheet divides it.** *Fourteen of twenty* and *seven of ten* are
  the same share and different claims, so the record publishes the two counts and no
  percentage — the same honesty the metered rows print their raw fractions for.
- **A figure the platform acts on is served, and one it does not is not.** That is why a
  metered row carries its percentage and opponent variety does not: a strand's figure is
  derived in exactly one place so that a card, a profile and the matcher's evidence cannot
  print three roundings of one record, and a client dividing the pair itself would be the
  fourth. Variety prices no promise and nothing rounds it, so the division is the client's.
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
is still to come (#537).

**A place where racket sports are played, known to the platform because it signed up.** Players
search clubs to set a group's home and to find groups; the club manages its own facts from the club
website, and lists there the courts, hours and prices it sells through Raketa.

- **Club** — an **event-sourced aggregate**: a name, a district, a city, **the sports it offers**
  (a non-empty subset of the four — they *filter* the `Sport` registry and never extend it) and
  **a precise point on the map**, stored as the club dropped it, because a club is a public place
  and not a person's whereabouts. Its details may change at any time, except that a sport one of
  its **Courts** plays, or an **Official group** declares, cannot be taken away — each refusal names
  the court or the group. **Not verified**: nothing checks that a club is who it says it is. **Not
  a court**: a club *has* Courts (below), and *"a court at [club] is free"* speaks of one of them —
  and **not a plan's venue**: a Plan's *Where* stays free text. _Avoid_: venue, centre, facility,
  location (that is a player's **Location area**).
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
  every player's search is built from.
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
per sport; a group is where that crowd lands when somebody taps its link. It picks no games yet,
posts none, and its games have no chat — [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
decides how they will (Part 2, and the note under **Conversation**).

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

### Payments

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4–§5 and
built by [#536](https://github.com/Raketa02/Raketa/issues/536)
([ADR-0190](docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)). The
**Seat charge** is still to come (#541), and so is connecting a club's account (#537).

**How a player pays: a card or a wallet saved once, charged later by the club.** Every charge is
made on the club's own account — **the club is the seller** — and a player's card is copied there
for each one.

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
player's Games & money by [#539](https://github.com/Raketa02/Raketa/issues/539). The engine that
builds proposals (#540), posting (#546) and the fill that books one (#541) are still to come.

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
  post back with nobody else In; *filled* arrives with the Booking. _Avoid_: challenge (Part
  1's aggregate), open game.
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
  at every read and stored nowhere. Distinct from the Players deck of **Classic play**.
- **Picked for you card · Challenge card · Seat open card** — the three card types: a pick, a
  **Post** dealt to you as a best fit (its ribbon reads *"Kuba challenged you"*, or *"The group
  challenged you"* once the poster withdrew), and a **Rescue** — dealt once rescues exist (#545).
  A *Challenge card* is a label, never **Challenge** (Classic play's aggregate).
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

## Part 2 — Decided, not yet built: Games and Fill in

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) and
specified in [`the-mechanics.md`](docs/specs/games-and-fill-in/the-mechanics.md) and
[`the-screens.md`](docs/specs/games-and-fill-in/the-screens.md). **None of this is in the code
yet**; when a term is built, it moves into Part 1 under its context.

### The pool and the court

**Pool** is built, and moved to **Proposals** in Part 1 with
[#538](https://github.com/Raketa02/Raketa/issues/538).

**Court**, **Court hour**, **Way of working**, **Cut-off**, **Book-by** and **Share** are built, and
moved to **Club** in Part 1 with [#535](https://github.com/Raketa02/Raketa/issues/535), beside the
**Club courts** that hold them.

### Proposals and the deck

**Proposal**, **Version**, **Yes**, **In**, **Withdraw** and **Live yes** are built, and moved to
**Proposals** in Part 1 with [#538](https://github.com/Raketa02/Raketa/issues/538).

**Group deck**, the three **card types**, the **IN tag** and the **Overlap grid** are built, and
moved to **Proposals** in Part 1 with [#539](https://github.com/Raketa02/Raketa/issues/539).

- **Post** — a proposal a member created by picking the hour and the court. Posting is the
  poster's yes. At most two live per player.
- **Fills** — the moment the last needed yes lands and a **Booking** opens. Every seat is then
  charged together, all or nothing — at an On request club only once the club confirms, the
  booking *waiting for the club* until it does.

### Bookings

- **Booking** — a filled proposal: the club, the court and its number, the hour, the seats and
  their sides, and its state — *waiting for the club*, *booked*, *seat open*, *called off*,
  *played*. It opens an ordinary **Game** for the result. _Avoid_: reservation, held.
- **Rescue** — an open seat in a **booked** game that lost a player. Shown in **Fill in** and dealt
  to the best fits as a Seat open card; taking it pays at once.
- **Fill in** — the group's rescue board (**Seats to fill**) plus **You're In**, your own yeses
  that have not filled or are *waiting for the club*. It never offers a proposal that is still
  filling. (Classic play's *fill*, completing a challenge, is a different thing.)
- **Leaver** — a player who left a booking. Before the cut-off, refunded at once minus the card
  fee; after it, refunded (minus the fee) only when the seat is taken.
- **Check-in** — a club scanning a player's code on the day. Evidence that the player was there,
  never a condition for money.
- **No-show report** — the players who came marking one who didn't, with 24 hours to dispute. Held
  by the Game.

### Money

**Payment method** and its **Payment terms** are built, and moved to **Payments** in Part 1 with
[#536](https://github.com/Raketa02/Raketa/issues/536). One is required before the first yes.
**Games per week** and **Most I'll pay** are built, as **Games & money** under **Proposals** in
Part 1, with [#539](https://github.com/Raketa02/Raketa/issues/539).

- **Seat charge** — one seat's money in one booking: authorised, captured, refunded or failed.
  Raketa's account of a Stripe payment; Stripe is the ledger of record.
- **The club is the seller** — every charge is made on the club's own Stripe account; the club
  pays the card fee. Raketa takes no fee.

### The player's side

- **Home** — the first tab of the bottom bar: your games from the moment they fill (Part 1's *Now*).
- **Classic play** — one feature flag, off by default, behind which the Players deck, the Chats
  tab, Challenges with their Plan, and Find a game stay as they are.
- **It's a game!** — the screen the player whose yes filled the game, or who took a rescue, sees.

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
- **Feature flag** — a named switch that answers *is this feature active* for one player, and can
  change without a build. Defined in a separate repository, `Raketa02/raketa-features`, turned
  on or off by a pull request there, and **decided in the player app only**, from a datafile
  built per environment ([ADR-0180](docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
  Every flag has a **code default** declared once in the client, used when no datafile has
  ever arrived. **Not environment configuration**: a flag may be *defaulted* per environment,
  never *derived* from it ([`docs/environments.md`](docs/environments.md)). A gated screen reads
  its flag once, when it mounts. The first is `find_a_game`. _Avoid_: "toggle" as a noun,
  "kill switch" — a flag here acts at the next launch or foreground, never instantly.
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
