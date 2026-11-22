# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. Every app
obeys this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Raketa is a racket-sport platform. Today a player signs up, picks a nickname, joins **Groups**,
answers a questionnaire for a **Skill rating** in a sport where a group first asks for one, and is
dealt games by their group's Games deck — the last yes books a club's court and charges every seat — while a **Club** runs its
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
> seat. Their terms are in Part 1 under **Proposals**, **Bookings**, **Payments**, **Notifications**
> and **Club**.
>
> **It was cut back again on 2026-10-06**, when the older way of making a game — *Classic play* —
> was removed with the feature flag that hid it ([#569](https://github.com/Raketa02/Raketa/issues/569)).
> Every term that named only that loop went with it: *Challenge*, *Plan*, the Players *Deck* and
> its *Deal*, *Radar*, *Search*, *Interest*, *Pass*, *Prompt*, *Cool-off*, *Exposure*, the
> candidate index, *Fit* and every term of the ranking, *Search radius*, *Proposals opt-in*,
> *Tester* and *Feature flag*. A word you remember from one of them is gone on purpose; see the
> [ADR index](docs/adr/README.md#the-2026-10-06-classic-play-removal--the-second-gap).
> **Feature flag came back on 2026-11-21**
> ([ADR-0206](docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md),
> [#826](https://github.com/Raketa02/Raketa/issues/826)) with one key, `explore`, decided in the
> player app, and is defined in [`frontend_player/CONTEXT.md`](frontend_player/CONTEXT.md): it
> names no domain concept. *Tester* did not come back.
>
> **On request and Instant were removed on 2026-10-12** ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
> §1). **Only Raketa** is the one way a club sells
> through Raketa until Raketa is the club's booking software. Their words went with them: *Way of
> working* as a choice, *Instant*, *On request*, *time to confirm*, *minimum notice*, *Waiting for the
> club*, *answers by*, *Waiting for you*, *Accepted · waiting for one player's payment*, *said no* and
> *didn't answer in time*, and the **request** with its acceptance, refusal and timeout. A full game is
> booked the moment it fills, at every club.

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

- **Skill rating** — an **event-sourced aggregate**, one per (player, sport). **Its Level is also
  what the player's Ranking in that sport sorts by** ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)): the same number, never a
  second one, and the ranking never changes it.
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
- **Rating status** — **Initial Estimate** (the questionnaire's output, no counted matches) →
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
  **No single evening moves a Level further than the ceiling** — a brake, because the questionnaire's
  uncertainty is a floor rather than a measurement and silence confirms a score nobody read.
  Decided by [ADR-0139](docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md).
- **Volatility** — how fast the estimate currently appears to be moving.
- **Assessment** — an **event-sourced aggregate**: one adaptive questionnaire run, for one
  player and one sport. **Started where play begins, never at sign-up** ([ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md)):
  a player group's door (*Get your level*) for a player rated in nothing, an official group's own
  card and Post a game's (*Rate padel*), *+ Another sport* at the end of a group's sport chip, the
  Home card, a friend's **Ask for a level** (its notice, and since 2026-11-07 its card, in **Needs
  your answer** since ADR-0205), and
  the **Skill passport**'s *Add a sport*, and since 2026-11-07 the Rankings page's *Get your {sport}
  level* ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §5). Its result returns to wherever it was
  started. A run left unfinished is never forced on anybody: the door and the Home card offer to
  carry it on (not yet built — [#729](https://github.com/Raketa02/Raketa/issues/729), [#730](https://github.com/Raketa02/Raketa/issues/730), [#731](https://github.com/Raketa02/Raketa/issues/731)).
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
  write**. *Add a sport* on it starts one questionnaire for an unrated sport, and the result
  returns to the passport, because a result returns to wherever its questions were started
  ([ADR-0179](docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §3,
  [ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md) §5).

**Invariants**
- **A level is proved, never declared.** Not by the player, not by staff, not by a club.
  Manual editing is refused by the domain itself, not guarded by a permission check.
- **Only the rating context writes μ, σ, volatility and status.** Every other engine
  contributes evidence, an information weight, or an anomaly signal — never a rating point.
- **A result moves a Level or it moves nothing, and there is no third outcome.** A game with no
  agreed score — *Disputed*, *Played · no score*, and before ADR-0195 *unscored* — is *an evening,
  not evidence*; a friendly was never evidence about anybody by the choice
  of the people who arranged it. Both are absent from what the rating context reads, so neither
  is a branch anybody could forget.
- **Absence widens, it never lowers.** Layoff and inactivity add to σ and never touch μ. A
  player who was 3,20 two years ago has no obligation to still be 3,20 — and no obligation
  to have got worse. The honest position is *we are less sure*, not *we assume decline*.
- **A contradiction is never resolved by picking a side.** It widens the range and raises
  calibration priority; it never moves the player up or down, and it never accuses them.
  Resolution has no direction, which is what stops under-reporting being profitable.
- **The questionnaire cannot produce confidence above 30%.** It is the entire evidence
  surface and self-report has an irreducible ceiling, enforced as a floor on σ rather than as a
  display cap. Every rating it produces is an *Initial Estimate*.
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
- **Name** — *retired 2026-11-03* ([ADR-0199](docs/adr/0199-a-player-is-known-by-their-nickname.md), superseding
  [ADR-0171](docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
  A player has no Name in Raketa, only a **Nickname** (the backend since
  [#724](https://github.com/Raketa02/Raketa/issues/724); the phone not yet —
  [#728](https://github.com/Raketa02/Raketa/issues/728)). The name a club types when it invites
  somebody is the **Administrator**'s (Administrators), never a player's. _Avoid_: a player's
  *name*, *real name*, *display name*.
- **Nickname** — value object. Trimmed, 2–64 chars, `[A-Za-z0-9_.-]`, **unique**. A handle, and
  **what every screen says**: every sentence, row, card, sheet, toast, notice, seat label, spoken
  name and email names a player by their whole nickname or names nobody, and **never with an @** —
  *ania.k put a score up*, *Hi ania.k*. The two initials over a generated poster stay the one
  derived form ([ADR-0167](docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §3),
  cut from it: its first character, then the first character after its first `.`, `_` or `-`,
  else its second (*ania.k* → `AK`, *kuba* → `KU`). **Changeable at any time** by the naming, for
  as long as nobody else holds the new one, and everybody reads the new one from their next read.
  Null until the naming ([ADR-0199](docs/adr/0199-a-player-is-known-by-their-nickname.md)).
- **The naming** — the one act that names a player: **a nickname, and nothing else**, asked in
  onboarding's first step (*How should people see you?*) and never at sign-up, **repeatable** (a
  later change from the You tab is the same act), refused with `NicknameAlreadyTaken` when
  another account holds it. Sign-up asks for credentials only — email, password, the Adult
  attestation — and a `User` is created without a nickname. Its step is reached while the account
  has **no nickname**, an account an Invitation opened included, which reads *Pick a nickname —
  it's how players will see you.*
  ([ADR-0185](docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §4,
  amended by [ADR-0199](docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). `/users/me` carries the nickname and no name.
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
  - **UserNamed** — `users.user_named` / **v2** — the naming, carrying the **Nickname** alone;
    the fold keeps the latest. v1 carried a Name beside it and is read with the name ignored
    ([ADR-0199](docs/adr/0199-a-player-is-known-by-their-nickname.md) §6, built by [#724](https://github.com/Raketa02/Raketa/issues/724) — `UserNamedV1` decodes it).
  - **UserDisabled** — `users.user_disabled` / v1.
  - **UserPromotedToAdmin** — `users.user_promoted_to_admin` / v1.
  - **AccountOpenedByInvitation** — `users.account_opened_by_invitation` / **v2** — the other
    way a stream begins: an account an **Invitation** opened when its person set a password,
    carrying the hash and **no player name, no Nickname and no attestation**. The name the club
    typed is the Administrator's. v1 carried it and is read with it ignored (ADR-0199 §4, built
    by [#724](https://github.com/Raketa02/Raketa/issues/724) — `AccountOpenedByInvitationV1`
    decodes it).
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
  constraint violation).
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
  *why they are here*. There are **27** — After the match 9, On the court 10, Why you're here 8 —
  and a player holds **2 to 8**
  ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §7, [#829](https://github.com/Raketa02/Raketa/issues/829): *Stays for a coffee*, *Up for a bite
  after*, *Keeps in touch*, *Happy to swap partners*, *Patient with beginners*, *Happy to share
  tips*, *Brings the energy* and *New in town* were appended to the nineteen, each at the end of its
  group, and the ceiling rose from 6; a selection of up to 6 recorded before still stands). An id is
  permanent: a new tag is appended to its group, and none is ever moved, renamed or reused. Never
  free text, never player-authored,
  never imported from another platform, and never about the person rather than the game —
  age, looks, body and "looking for" are a different product's vocabulary. **Tags order one row and
  score nothing else**: since [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §6 they put **Same vibe players** in order (Discovery),
  every tag counting the same, and no proposal, card, forecast or level reads one. **They will also
  build and rank For fun**
  ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §1 and §2, decided and not yet built —
  [#830](https://github.com/Raketa02/Raketa/issues/830),
  [#831](https://github.com/Raketa02/Raketa/issues/831),
  [#832](https://github.com/Raketa02/Raketa/issues/832)): among the fours that pass the gates, a
  For-fun table is the one with the highest **Social vibe**, every tag counting the same but 💘 *Open
  to meet someone*, which is shown and never counted; a tag edit reaches the next build and pulls
  nobody off a card already dealt. They will still touch no competitive card, forecast or level.
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
  reads it is the distance to a club, and the nearest-first order of a club search. **Required**:
  no Player profile exists without one. It is set by **a reading of the phone** or, when the
  player refuses the phone's permission, by **a Club they pick** (*Pick a club near where you
  play*): that club's point on the map, rounded to the same cell. An unknown club is refused
  ([ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md) §10, not yet built — [#726](https://github.com/Raketa02/Raketa/issues/726), [#733](https://github.com/Raketa02/Raketa/issues/733)). **It
  moves on a cold start**: the app re-reads the phone silently when it is launched, and after a
  day in the background, and the cell changes if the fix falls outside it — never merely on
  foreground, never with a prompt, and never when the permission has since been revoked
  ([ADR-0174](docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §6). So a
  club-picked area stays until the phone has permission, and the first reading then replaces it.
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
  are different facts. Declared on the group deck's declaration step — asked once, inline, the
  first time a player opens Games for a sport without one — and on the You tab
  ([ADR-0094](docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md), its ask at
  the tail of a rating run corrected by [ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md)) — and
  at the **other kind's door** on a group deck's switch: the kind the intent does not want is drawn dimmed, and a
  tap opens an in-place change, reported on the `DECK` surface
  ([ADR-0201](docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md) §2,
  not yet built — [#740](https://github.com/Raketa02/Raketa/issues/740)). It is both what a player is
  dealt and who they are dealt to, one fact, because a card is one game everybody on it sees
  (ADR-0201 §1). A group deck deals no card of a kind the player's intent does not want. **A changed
  intent leaves the cards not yet answered**: a name not yet In whose intent no longer wants a card's
  kind holds no seat on it, so its seat goes to the next best fits and a new yes there is refused
  `no_longer_fits`. It is read live and recorded nowhere, and it is not a no: the yeses already given
  stand, and if the intent wants the kind again before the seat is taken, the name is back on the
  card (ADR-0201 §3, not yet built — [#738](https://github.com/Raketa02/Raketa/issues/738)).
- **Play intent declaration** — the **event-sourced aggregate** that holds one, one stream per
  `(player, sport)`. Separate from the Player profile, which stays free of a sport dimension.
- **Mode** — *defined in the Matchmaking section below, where it belongs.* It is named here only
  because **Play intent** cannot be defined without it, and the two are the pair most easily
  confused: **Mode is one game's kind; Play intent is the player's standing declaration.**
- **Profile photo** — the first of a player's photos, and the one a face on a card shows. A
  player may hold up to three or none; none is not an absence but a **generated court
  poster**, derived from their identity so it is stable across devices. **The player record shows
  all of them**, in the player's order, to any reader it is admitted to ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2, built by
  [#791](https://github.com/Raketa02/Raketa/issues/791)); before that it showed only this one.
- **Intro** — **one line a player writes about themselves**: at most **250** characters
  ([ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md) §9, not yet built — [#726](https://github.com/Raketa02/Raketa/issues/726), [#733](https://github.com/Raketa02/Raketa/issues/733)), no line
  breaks, any language, one per player, and **optional** — a player who wrote none has none,
  not an empty one. The first player-authored free text the platform shows to a stranger, and
  the fence is at the write: a phone number, an email, a URL or a handle is **refused**, because
  the realistic abuse of a line shown before a game exists is contact leaving the app. It reaches
  the player record and nowhere a person is merely named; it is never scored
  ([ADR-0170](docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)). Since [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §6
  it is also drawn on the **vibe sheet** (Discovery), which reads the record: a place a person speaks.
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
- **Profile commit** — the single idempotent request that ends onboarding's profile steps,
  carrying every answer at once. Nothing is written before it, so leaving mid-part
  restarts at step 1 ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Keyed
  by a client-supplied **idempotency key**, which the creating event carries so a retry is
  recognised from the stream itself rather than from a table beside it.
- **Show me to new people** — a player's switch, **on by default**, held on this stream: whether
  players who share **no group, no game and no friendship** with them may meet them. **Turned off**,
  the player leaves the three **people rows** (Discovery) on everybody else's Home and their See all
  screens, and such a stranger reads *This record isn't available* and can't send a request. They
  **keep their true place** in the ranking and **Top 10**, and their face in group sheets, and still
  see the rows and send requests themselves. Changed at any time, as a new event on this stream, and
  returned by the profile read ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2, built by
  [#791](https://github.com/Raketa02/Raketa/issues/791), [#799](https://github.com/Raketa02/Raketa/issues/799)). **It replaces *Show me in General***: the
  `player_profile.ranking_visibility_set` events still fold, *hidden* as **off**, so a player who had
  hidden from General starts with it off. _Avoid_: Ranking visibility, Show me in General (both
  retired), private mode, invisible.
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
[#587](https://github.com/Raketa02/Raketa/issues/587). **Since 2026-11-07** ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8, built by
[#772](https://github.com/Raketa02/Raketa/issues/772), [#773](https://github.com/Raketa02/Raketa/issues/773),
[#779](https://github.com/Raketa02/Raketa/issues/779)) a block also hides the pair's rows from each
other in the **Ranking**, and **closes the record both ways**, so the record asks about blocks again,
in both directions, and Unblock lives only in You › Blocked players. **Since 2026-11-14** ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2,
built by [#791](https://github.com/Raketa02/Raketa/issues/791)) **the ranking shows the pair
to each other again**, and a block instead keeps them out of each other's **people rows**
(Discovery); the record stays closed both ways.

- **Block** — an **event-sourced aggregate**, one stream per **ordered** `(blocker, blocked)`
  pair, with a deterministic stream id derived from that pair. **The record is directed; the
  effect is symmetric.** `A → B` and `B → A` are two independent blocks, so one being lifted
  never lifts the other. What it reaches is **one court**: a blocked pair, either way, is never
  dealt a version together, never both **In**, never offered each other's **Rescue** and never
  joined onto each other's **Post** — nor seated in one **Friends game**. **It also ends a
  Friendship** ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §2, not yet built — [#745](https://github.com/Raketa02/Raketa/issues/745)):
  the friendship and any open request between the pair end silently, and a request the blocked
  person sends later is never shown to the blocker. **It closes the record in both directions,
  everywhere** ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8), and **keeps the pair out of each other's people rows** and
  their See all screens ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2). **It hides nobody in the Ranking, Top 10 or a group
  sheet**, where a tap on the other reads *This record isn't available* (ADR-0204 §2; from ADR-0203
  §8 until then, it hid ranking rows both ways). _Avoid_: hide, mute, ban — it hides nobody in a
  group or a ranking.
- **Blocker** / **blocked** — the two sides of the ordered pair. The blocker can see their own
  block. The blocked person can never discover it.
- **Own block** — a block the reader made: the only kind of block a response may carry. Two reads
  carry it, **Blocked players** (the caller's own blocks, each with the person's nickname, photo
  and when) and the **player record** (whether the reader blocked its subject). **Since
  [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8 one read does**: a blocked pair's record never opens, so its own-block fact
  leaves the contract, and Blocked players is the one place (not yet built — [#773](https://github.com/Raketa02/Raketa/issues/773)). _Avoid_: a field that
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
  today, because the `cases` context does not exist. **Never a card hold**: money reserved on a
  player's card (Payments) is never written *a Hold* — the **share is held**, and the hold is
  **let go** or the share **taken**.
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
- **A block keeps two people off one court, and reaches nothing else but a friendship.** Groups,
  Members lists, the player record, booked games and chats already shared are untouched. The one
  further reach is [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §2's: a block ends a friendship and swallows the blocked
  person's later requests, which the blocked person cannot tell from a silent removal or a request
  set aside. Both stay in the group, see
  each other in its Members list and can open each other's record. Hiding a member of a crowd
  everybody can see would itself be the tell. *(Amended 2026-11-07 by [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8, not yet
  built: a block also hides the pair's rows from each other in the Ranking, and closes the record
  both ways, everywhere, group-mates included. Members lists and shared chats are unchanged.
  Amended again 2026-11-14 by [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2: the ranking hides nobody, and a block keeps the pair
  out of each other's people rows instead.)*
- **Nobody is shown that they were blocked; you can see your own blocks.** A response may carry
  the reader's own blocks, never anyone's block of the reader, which a test over the emitted
  contract asserts. Nothing the blocked person reads names a block, and their read of the
  blocker's record is the same byte for byte whether or not they were blocked. A yes that would
  pair them is refused without saying why, and nobody is notified of a block or an unblock. *(Since
  ADR-0203 §8 the blocker's record is refused to them, with the record's one refusal, which names
  nothing and reads as a hold does.)*
- **A block takes back the blocker's yeses until the game is booked, and never touches a
  booking.** Where the blocked person is In, picks and posts alike, the blocker's yes goes by the
  ordinary **Withdraw**, from a proposal still filling. It is free, and nothing says why. The blocked
  person's yes stands. A booking stays as it is, and leaving it is the ordinary Leaver rule. (Until
  2026-10-12 a booking *waiting for the club* was taken back as if the blocker left it, telling the
  others In; On request's removal, ADR-0196 §1, leaves that case nothing to apply to.)
  **Unblocking brings no yes back.**
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
  (the **Forecast** and its **Split**), how much of the narrowest week a set of people share, and
  a For-fun table's **Social vibe** from the tags each person carries — handed only the tags that
  count, since which ones don't is the Player profile's, beside its vocabulary
  ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §11, [#830](https://github.com/Raketa02/Raketa/issues/830)). The stateful half — loading the ruleset, the gates, the reads off other contexts — is the
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
  nothing still stops being new. **Not to be confused with New in Raketa** (Discovery), which runs **30 days** from the
  same profile commit: the window bends a level gate, the row shows a person.
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
- **Social vibe** — how much of what everyone at a **For fun** table carries is shared there: on
  average, each **Social tag** at the table is carried by that share of the *other* players. The
  table is everyone named on the reader's version of a card — the people **In**, the reader and the
  names dealt, never an empty seat — and the figure is
  `round_half_up(100 × Σᵢ Σ_{t∈Tᵢ} (c_t − 1)/(n − 1) ÷ Σᵢ |Tᵢ|)`, *c_t* being how many at the table
  carry tag *t*. So a tag all four carry counts for more than one two carry, and two pairs who share
  everything with each other and nothing across the table read **33**, never 100. In singles it is the
  plain overlap of the two players; with fewer than two people there is none. **Only identical tags
  count, each the same, and 💘 *Open to meet someone* never does**, though the grid still draws it.
  A plain fact about the table, the same number for everybody at it, worked out **live from current
  tags** by one pure function in **Match Fit**, and stored nowhere. It builds and ranks For-fun
  tables and is drawn on every For-fun game where a competitive one draws its **Forecast**: For fun
  never shows a forecast, and a competitive game never shows a Social vibe. **Not Same vibe's Vibe
  %**, which is a pair's 1 − ½ⁿ and can differ for the same two players. Decided by
  [ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §2 and §5; on the **Group deck**'s cards since
  [#830](https://github.com/Raketa02/Raketa/issues/830), and not yet built elsewhere —
  [#831](https://github.com/Raketa02/Raketa/issues/831),
  [#833](https://github.com/Raketa02/Raketa/issues/833)–[#835](https://github.com/Raketa02/Raketa/issues/835),
  [#838](https://github.com/Raketa02/Raketa/issues/838),
  [#840](https://github.com/Raketa02/Raketa/issues/840)–[#842](https://github.com/Raketa02/Raketa/issues/842).
  _Avoid_: vibe %, match %, compatibility.

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
  ever. Its ends are **folded from the record and the clock** — **Confirmed**, **Disputed**,
  **Played · no score**, and a game somebody **Didn't come** to — except **Called off**, which is
  announced, and **Started short**, which the hour reads off a line-up with a seat still open.
  Since [ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) (2026-10-11; built by
  [#654](https://github.com/Raketa02/Raketa/issues/654),
  [#655](https://github.com/Raketa02/Raketa/issues/655) and
  [#657](https://github.com/Raketa02/Raketa/issues/657)) *Played · no score* replaces *Never
  played*, *Disputed* is where two scores naming different winners end, and *Didn't come*
  replaces the no-show report. **Called off says who**: `called_off_by`, or nobody when it
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
  happened**. It can be made inside the game's **entry window**: from the hour's start, **never
  before**, until 24 hours after the hour ends. When a **Competitive** game's hour ends, all of its
  players are asked ***How did it go?***; a **For fun** game asks nothing, and a score put up on
  one settles at once with no answer window. The edges, the question and For fun are ADR-0195's
  (§5), not yet built ([#654](https://github.com/Raketa02/Raketa/issues/654)).
- **Score** — the sets, absolute rather than from anybody's point of view. **A score names a
  winner**: a level set has not finished and none of the four sports produces a draw, so a level
  score is refused. *Set* is used for whatever the sport calls its unit.
- **Proposal** — a score on the table, **one per side**. The cap is what bounds an argument to
  two rounds, and it is what makes silence safe to read as agreement. The other side is asked
  ***Is that right?*** when it goes up. *Not* the **Proposal** of
  Proposals, which is a game still filling: this one is a score, and the word is always read in
  its context.
- **Correction** — the proposing side revising its own score while the other side has not
  answered, and never after the entry window has closed (ADR-0195 §5). **Not a second proposal**, and **any member of that side may make it** — the rule
  that makes a teammate's agreement worthless is the same rule that makes a teammate's objection
  credible.
- **Counter** — the other side's one turn, and **it carries a score**. There is no bare
  rejection: a rejection carrying nothing would be free and always optimal for the loser.
- **Acceptance** — agreement, **from the opposing side only**, because a teammate agreeing with
  a teammate proves nothing. **One opponent suffices.** Since ADR-0195 §5 (*That's right*, not yet
  built — [#654](https://github.com/Raketa02/Raketa/issues/654)) it **settles the result at once
  and closes the game**: no counter is taken after it, so in doubles the first agreement from the
  other side wins.
- **Acceptance grace** — *retired 2026-10-11* (ADR-0195 §5). An acceptance waited six hours from
  the score before it settled anything, and a counter inside that time won. An acceptance now
  settles at once.
- **Closer score** — of two standing scores that name **the same winner**, the one with the smaller
  difference in games won; on a tie, the first put up. The game is confirmed with it (ADR-0195 §5).
- **Disputed** — the end of a game whose two standing scores name **different winners** when the
  answer window closes. No Level moves, and each of the two players who put a score up is counted
  in **Results left in dispute** (Player Score). It takes the place *Unscored* held for two scores
  nobody accepted.
- **Played · no score** — the end of a **full** booked game whose entry window closed with no
  score and nobody *Didn't come*. Played, for all its players: each gains the points of a game
  **played through**, and no Level moves. It replaces *Never played*, which retires: every game is
  opened by a booking, so there is no unbooked plan left to dissolve (ADR-0195 §2, built by
  [#655](https://github.com/Raketa02/Raketa/issues/655) as `PLAYED_NO_SCORE`). A court whose
  window closes with a seat still open is never one: it went ahead short.
- **Tap window** — from a booked game's start to 30 minutes after it, the first half of a one-hour
  game: when attendance is caught at the court (ADR-0195 §3, built by
  [#657](https://github.com/Raketa02/Raketa/issues/657)).
- **Isn't here yet** — the tap a player on the court makes, **at the club**, in the tap window,
  about another player on the court who hasn't arrived. Never about yourself, never while you are
  yourself absent and not yet arrived; a partner may be tapped, and two absentees can each be.
  The absent player is pushed at once. It costs its maker nothing.
- **Arrival** — the moment an absent player is shown to be at the club: their own **I'm here**, or
  a courtmate's **They're here**, each made at the club. The first one counts.
- **On time · Came late · Didn't come** — the three attendance outcomes, read from the arrival:
  **on time** within 10 minutes of the start (nothing is recorded, and the tap vanishes), **Came
  late** 10 to 30 minutes after it, **Didn't come** with no arrival by 30 minutes after it. A
  *Came late* game carries on, score and Level included. A *Didn't come* game takes no score and
  never counts, and *Didn't come* is provisional until the late claim's 24 hours end. Folded per
  player against the server's clock, never the phone's.
- **I was there** — the absent player's late claim, within 24 hours of the tap window closing,
  for a phone that died. A courtmate confirms it with **Yes, they were here**, and *Didn't come*
  becomes *Came late*: the tap still proves they weren't there when it was made. Built by #657
  with two calls made without a ruling: **the claim and its confirmation carry no location**
  (they are made a day later, from wherever; the courtmate is the proof), and **a player who
  Didn't come can't confirm anybody** (two absentees can't vouch for each other).
- **At the club** — the verdict a tap in the **tap window** carries (*isn't here yet*, *I'm
  here*, *they're here*): the phone's one-shot fix, read only at the tap, within **300 m** of the
  club's map point, allowing for the fix's own stated accuracy up to 200 m. The Game is given
  only the verdict; **the coordinates are never stored**. The windows are half-open: an arrival
  at exactly 10 minutes is *Came late*, and a tap at exactly 30 minutes is refused (a call,
  #657). A score put up and still waiting for its answer stops no tap, and counts for nothing
  if the player tapped never comes (a call, #657).
- **No-show report** — *retired 2026-10-11* (ADR-0195 §3). The players who came marked one who
  did not, from anywhere, for a day after the hour; the reported player had a day to dispute it,
  and a player the club checked in could not be reported. It is replaced by **Isn't here yet** and
  the **Arrival**, made at the court. Its events stay decodable and fold to nothing, and a game
  that held one reads *Played · no score*.
- **Standing** — what a game *is* right now: `AWAITING_ENTRY`, `PLAYED_NO_SCORE`,
  `AWAITING_ANSWER`, `CONFIRMED`, `DISPUTED`, `CALLED_OFF`, `STARTED_SHORT`, `NOT_HERE_YET`,
  `DIDNT_COME`. ADR-0195 changed the list: `DISPUTED` came with #654, `PLAYED_NO_SCORE` took
  `NEVER_PLAYED`'s place with #655, and with #657 somebody **not here yet** (`NOT_HERE_YET`, a
  wait in the tap window) and **Didn't come** (`DIDNT_COME`, which a confirmed *I was there*
  can still undo for a day) took `NO_SHOW_REPORTED`'s and `NO_SHOW`'s places, and `UNSCORED`
  left with the no-show report, its last case. **Derived from
  the record and the clock, never stored** — and
  never announced, with one exception: `CALLED_OFF` is a decision, folded off `GameCalledOff` and
  read first ([ADR-0163](docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). It is an
  end, and it is **not an evening**: this was an act, so it is in no tally, and it earns nobody a
  game played through (its cost to a leaver is the record's, in points). Neither `STARTED_SHORT` nor
  *Didn't come* is in a tally either. (Before ADR-0195 this also said *nor a ghost* and *moves no
  Strand*; both terms are retired.) Spelled `GameStanding` in code and on the wire, a name kept from when Challenges
  published a `Standing` component of its own: renaming a component is a change to types a
  shipped app generated. The same is true of `GameSide`.
- **Counted game** — a counted-kind game that was played, **scored or not**. What *opponent
  variety* on the player record counts — not the skill card's `counted_games`, which is the
  results that moved the Level. A *Disputed* game is one, and so is a *Played · no score* game
  ([#655](https://github.com/Raketa02/Raketa/issues/655)): nobody said it was played, and it was —
  *played* has one meaning, so who somebody has played with counts it too.
- **Ghost game** — *retired 2026-10-11* (ADR-0195 §2). A booked game whose entry window closed
  with nobody ever saying it happened, charged to everybody on its court on *Shows up*. A full
  booked game nobody recorded is now **Played · no score**, and nothing is charged for silence.

**Invariants**

- **Silence confirms, and costs nothing.** A lone score nobody answers stands 24 hours after it
  went up or was last corrected, and the game counts. There is nothing anywhere in this context called *confirm*: a
  result is agreed when a clock passes or when the other side says *That's right*.
- **Two standing scores nobody accepts are settled by who they name.** The same winner: the game
  is confirmed with the **closer score**. Different winners: the game is **Disputed** (ADR-0195
  §5). **A disputed game, like a *Played · no score* one, is an evening, not evidence**: it is in
  history, it establishes that these people have played together, and **it moves nobody's
  Level.**
- **No player is penalised for not entering or not agreeing a result.** Not the silent loser,
  not the four who all went home — a full booked game nobody recorded is *Played · no score* and
  earns them their points — and not either side of a dispute. **This is why *confirms results*
  was struck**, and why since ADR-0195 nothing about answering a score is in the reliability
  figure at all: silence costs nothing, and *Results left in dispute* is a line on the record,
  never points.
- **Attendance is caught at the court and never stored as a place.** The attendance acts are made
  in the tap window, from the club, each carrying only the verdict *at the club*. Money never
  moves on them: everyone paid, and the club was paid for the hour.
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
([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6) and, since its
2026-10-09 amendment (Q100), from the bubble on the game's Home card, with Back to whichever
screen opened it; the player app builds that door in
[#619](https://github.com/Raketa02/Raketa/issues/619). There is no inbox of rooms.

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

What the platform has watched a player *do*, as distinct from how well they play: **Player
reliability**, one figure in **points**, with the counts it is read beside. The words are the
player's: they are read on the player's own screen, on a group's Members list, and by the
**Reliability filter**, which is the only thing that acts on the figure.

**The figure was a weighted blend of strands until 2026-10-11**
([ADR-0140](docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md),
[ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md), #544). It is
now **points** ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
§1, §6): the points, bands, *New* and counts are built
([#659](https://github.com/Raketa02/Raketa/issues/659)), and so is the **Reliability filter**
([#661](https://github.com/Raketa02/Raketa/issues/661)).

- **Player Score** — the figure a player sees as **Player reliability**, out of a hundred, one per
  player across all sports. Computed from what happened, never from opinions and never from
  results: **losing costs nothing here.**
- **Points** — the figure's unit. **Everyone starts at 100.** A failure takes a fixed price off;
  every game **played through** gives 5 back; the figure stays between 0 and 100. Each failure drops
  out **6 months** after it happened, and the window rolls, so nothing ever resets everything at
  once.

  | What happened | Part | Points |
  | --- | --- | --- |
  | **Didn't come** (Games) | *Shows up* | −25 |
  | **Came late** (Games) | *Shows up* | −10 |
  | Left after the cut-off, and the seat stayed empty, so the game was played short | *Keeps plans* | −15 |
  | Left before the cut-off, the seat stayed empty, and the game was called off for everyone — or a card not fixed in time lost the seat, with the same result | *Keeps plans* | −10 |
  | Each game **played through** | — | +5, up to 100 |

  A *Didn't come* is priced once, on *Shows up*, never also on *Keeps plans*. **Never counted**: a
  swipe, a withdrawn yes, a card that never filled, a card fixed in time, leaving when your seat is
  taken or the game still plays, a club's cancel, and silence on a score.
- **Played through** — a booked game that reached its hour **full**, with the player on its court,
  not *Came late*, not *Didn't come* and not called off; scored or *Played · no score*. It earns +5.
  A *Came late* game earns nothing back, and a game that started short earns the players who stayed
  nothing either way.
- **Reliability band** — the word under the figure: **Very high** 90–100 · **High** 75–89 ·
  **Medium** 50–74 · **Low** below 50 reliability. **Served by the backend**; a client draws the word
  from the band and holds no thresholds of its own. _Avoid_: *Reliable*, *Holding*, *Under the bar*
  — the three words of the retired tone ladder, which named a bar at 70 that nothing applies.
- **New** — a player with fewer than **3 games played through, ever**, across sports. They read
  *100 · New*, and pass every **Reliability filter**. A player who stops for six months doesn't
  become New again. _Avoid_: newcomer, which is the **Newcomer window**'s 14 days in the level
  window (Matchmaking), a different clock.
- **The counts** — what the record shows beside the figure, over the last 6 months, and no ledger:
  - **Shows up** — turned up, of the games that reached their hour with the player on the court
    (late counts as turned up): *turned up 12 of 13*;
  - **Keeps plans** — kept, of the games they were in at the hour: *kept 13 of 14*;
  - **Being late** — how many times they came late: *late 1 time*;
  - **Results left in dispute** — see below.
- **Results left in dispute** — how many **Disputed** games (Games) the player put one of the two
  scores up on, over the last 6 months. **Information only, and it costs no points**: saying a
  score is wrong when it is wrong must never hurt. Someone who disputes every game is visible to
  their groups, and nothing more.
- **Reliability filter** — a player's optional preference, **off by default**: *Play only with
  players of at least High reliability*, or *at least Medium*. It is **one more clause of the pair
  rule** (Proposals' **In**), asked exactly where a block is: a pair is unfit when either player's
  minimum band is above the other's band, in both directions, and **New passes every minimum**. It
  acts from the moment it is switched on, or someone drops below it; **yeses already given stand**,
  and booked games never change. The filtering player is told how many players in their groups it
  hides (*hides 2 of the 11*); a hidden player is told, **with nobody named**, the figure that
  brings them back to everyone: the floor of the highest minimum among the filters that hide
  them, which clears all of them at once (a call in
  [#661](https://github.com/Raketa02/Raketa/issues/661): *the lowest band floor* would not bring
  a player below both a Medium and a High filter back to everyone).
- **Strand** — *retired 2026-10-11* (ADR-0195 §1). One of the six things the blended figure was
  made of, each a ratio of **opportunities** that fell due and what came of them, weighted
  35 / 20 / 15 / 12 / 10 / 8 and renormalised over the strands present. **Shows up** and **Keeps
  plans** live on as two **counts** and as the parts a price is filed under. **Answers about
  results** ([ADR-0160](docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md))
  leaves the figure, so silence on a score costs nothing. **Answers challenges** and **Settles up**
  had stood down with nothing to count. **Sportsmanship** was never a strand: it is its own figure,
  on the player record, under its own heading
  ([ADR-0158](docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)). _Avoid_:
  the strand weights, and a ratio for the figure.
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
  *Answers about results* itself left the figure on 2026-10-11
  ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)):
  silence on a score now costs nothing at all.
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
- **A new player is not a bad player.** Everyone starts at 100, and *New* says the 100 hasn't been
  tested yet. The figure is never absent and never a nought for want of a record: the absence that
  stood for *nothing has fallen due* retires with the strands.
- **This context keeps no record of its own.** It has no aggregate, no table and no migration: the
  figure and the counts are folded out of `games`' and `bookings`' records when somebody asks,
  through each one's published port, and the 6-month window bounds the read. A stored score would
  be a second place for *did that game happen* to be true, and the copy would be the one that got
  believed. If one read per deal for the filter grows too costly, a projection needs its own ADR.
- **A failure fades on a clock, the same for everyone.** Each one drops out 6 months after it
  happened, and the same failure costs the same for a newcomer and a veteran. A consumer that
  applied its own forgetting would be counting the same fading twice.
- **The prices, the window, the bands and *New* are this context's constants**, domain and never
  configuration, and never a ruleset: a release must not change what somebody's own record says
  about them.
- **Nobody is ever named by the filter.** Neither the filtering player nor the filtered one is told
  who, the same principle as a block.

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
  agree what the score was were still on a court together for two hours. Since
  [ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  a game nobody claimed is **Played · no score** — played — and two disagreeing sides end
  **Disputed**; both are in, as *played, and over* (#654, #655). Nobody said when a *Played · no
  score* game was played, so its card runs from its booked hour.

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
  Games card, a game's details, Fill in, Post a game or a group's Members list — and, since
  [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md), from the Rankings page; since [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md), from any face in
  Home's rows, and read by the **vibe sheet**. **It shows all of the subject's photos** (ADR-0204 §2).
- **A disclosure** — the thing that entitles a reader to open a record. Three strands, and
  *being the subject*: the pair **played together** — were both on one game's court — they
  **share a Group**, or the reader **runs an Official group** the subject is in (#575). **Nothing
  else, and nothing expires but a group**: a game the pair were both on discloses for as long as
  they are both on it, played or not, while a group discloses its members only while they are in
  it and only to whoever runs it now. **A fourth strand since 2026-11-07** ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §9,
  built by [#773](https://github.com/Raketa02/Raketa/issues/773)): the subject is **Listed** on **General** in at least one sport and hasn't turned
  **Show me in General** off, for **any reader**, with or without a level. It ends when they leave
  the list or turn the switch off. **Since 2026-11-14 the strands are exceptions, not the way in**
  ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2, built by [#791](https://github.com/Raketa02/Raketa/issues/791)): a record
  opens for **any reader**, except (a) across a block made by either side, or (b) when the subject has
  **Show me to new people** off and the reader shares no group, no game and no friendship with them.
  Under (b) the subject's group-mates, the people on one court with them, their friends and whoever
  runs their group still open it. The ranking's strand folds into that one rule.
- **The metered rows** — what the platform *watched* this person do, under the card headed
  *counted by the system, not written by people*. Each is a **raw pair and its figure**: how
  many opportunities fell due, how many went the way the strand is named for, and the
  percentage out of a hundred. Beside them is **the reliability pill** — the published Player
  Score, so a player working their record back up can watch it lift. One row per live strand of
  `player_score`'s, read through that context's published port and never recomputed here. **The weights are not on the
  wire**: they are a fact about how the number is made rather than about the person.
  **Retired 2026-10-11** ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §8, built by [#659](https://github.com/Raketa02/Raketa/issues/659)): the record's
  reliability block is the **points**, the **band**, **New** and the four **counts** (Player
  Score) — and, on the subject's own record alone, their **Reliability filter**, how many
  players in their groups it hides, and the figure that brings them back
  ([#661](https://github.com/Raketa02/Raketa/issues/661)). No row, pair or ratio per strand
  crosses.
- **Run of form** — a player's **last five counted results, oldest to newest**, each a win or a
  loss, in the record's skill panel beside their **counted games**. **Outcomes in order and no
  dates, at any granularity**: a moment beside one of them would be activity recency, which no
  surface carries in any shape. Fewer than five is a real answer and it is **never padded** —
  three results are drawn as three. A count includes a game nobody agreed a score for and a Run
  of form does not — *an unscored game, now a Disputed one, is an evening, not evidence*
  ([ADR-0137](docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
- **The gates** — re-run live on every open, because a disclosure made in August is not a
  permission to show somebody in December: the disclosure entitles a reader to *ask*, and the
  gates decide. They are the gates about **accounts** — a Hold, an account that may not be shown
  — and the reader's own Hold, and **no preference**: every strand is a court or a group that already put the pair
  in front of each other, so the gender preference is asked of nobody here. **Since 2026-11-07 a
  block made by either side is a gate again** ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8), on every strand,
  group-mates included. **Since 2026-11-14 so is Show me to new people's rule** (ADR-0204 §2), refused
  with the same one refusal.

**Invariants**
- **A record is read through a prior disclosure, never about a person.** Otherwise a route
  taking a player id is a player-enumeration endpoint, and a UUID being hard to guess is not
  an authorization model. *(Amended 2026-11-14 by [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2: a record opens for any reader
  unless a block or **Show me to new people**'s rule refuses it. The product owner ruled that the
  record holds nothing sensitive and that this is a social app; the refusal still names nothing.)*
- **The refusals are one refusal, byte for byte.** *Never disclosed*, *held* and *no such
  player* answer with the same status and the same body. Naming the gate tells a reader
  something about a person they may not be shown; separating *never disclosed* from *no such
  player* answers *is this id real* about a stranger. **A block is not among them**, in either
  direction ([ADR-0193](docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2, from #586): the blocker opens the record to unblock, and the blocked person's read is the
  same whether or not they were blocked. *(Superseded 2026-11-07 by [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §8, not yet built:
  a block either way is among them again, everywhere, and Unblock lives in You › Blocked players.)*
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
  empty list to head a card with. (Since ADR-0195 everyone has a figure, *100 · New* to start, so
  this absence retired with #659; the other three stand.) The three absences on this sheet are
  three different questions: rated in nothing, no counted game ever played, and nobody having
  said anything.
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
  id**: its Courts and their Raketa hours, its Exceptions, its Prices, its Raketa settings, and
  whether it is Paused. **Born by being used** — nothing is written at sign-up, and a club that has
  set nothing reads no courts and the default settings. Its *way of working* left it on 2026-10-12
  with the choice itself (**Only Raketa**, below; not yet built — [#670](https://github.com/Raketa02/Raketa/issues/670)).
  A stream of its own rather than more events on the Club's, because the Club's is what
  every player's home-club search is built from.
- **Court** — one physical court at a Club: a **name** the club uses (*Court 2*, *Kort centralny*;
  1–40 characters, unique at the club ignoring case), **one sport** from the club's own, and its
  **Kind of court**, indoor or outdoor. **Offered** to Raketa, or **switched off** — kept,
  with its hours, selling nothing new, whatever is booked on it. **Deleted**, or given another
  sport, only while no booking is ahead of it. Players never pick its **number**: a card or a post
  names a court hour at a club, and the number is given at booking. _Avoid_: pitch, field.
- **Kind of court** — **indoor** or **outdoor**, recorded on each Court by its club. **Players see
  it** since [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §4 (not yet built — [#671](https://github.com/Raketa02/Raketa/issues/671), [#677](https://github.com/Raketa02/Raketa/issues/677)): a booked game always shows its court's kind
  (*Court 3 · indoor*), and a card shows *Indoor* or *Outdoor* only when every free court it could be
  booked on is of that kind, because the court is picked at booking. It decides where a game may be
  moved: a **Move by cancel** and the club's own move go to the same kind, or indoor for an outdoor
  game, and never outdoors from indoors. A player sees it and never chooses by it: it is no
  preference and no filter. _Avoid_: surface, covered, court type.
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
- **Only Raketa** — how every club sells through Raketa: it hands Raketa a block of hours, its
  Courts' Raketa hours, and **Raketa sells them alone** until the **release lead** before each game,
  after which an unsold hour goes back to the club. **The one way, until Raketa is the club's booking
  software** ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1; decided, and not yet built — [#670](https://github.com/Raketa02/Raketa/issues/670), [#674](https://github.com/Raketa02/Raketa/issues/674)). Until
  2026-10-12 it was one of three **ways of working** a club chose, beside **Instant** (both sold, and
  the desk closed by hand what it sold elsewhere) and **On request** (the club confirmed each full game
  within its *time to confirm*). Both were removed, with the choice: no court platform makes a club
  confirm a booking, and none relies on a desk closing hours by hand. _Avoid_: way of working (there
  is no choice), allotment, Instant, On request.
- **Raketa settings** — the terms a club **confirms**, its first save doing so defaults included:
  the **release lead** (1–13 days, default 3), the **Cut-off**, **other clubs' courts** for its
  groups (within 10 km; **on by default** since [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7, existing clubs included, and
  read hour by hour, as **Official group** says — not yet built,
  [#746](https://github.com/Raketa02/Raketa/issues/746), [#747](https://github.com/Raketa02/Raketa/issues/747); it was off) and **Paused** (off). Each bound is domain, never
  configuration. The *minimum notice* and the *time to confirm* left them on 2026-10-12 with *Instant*
  and *On request* ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1, not yet built — [#670](https://github.com/Raketa02/Raketa/issues/670)). *We check players in* left them on 2026-10-11 with **Check-in** ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §4, not yet built — [#651](https://github.com/Raketa02/Raketa/issues/651)); the field stays
  decodable on the settings event and folds to nothing. Until #670 lands they can be confirmed only
  once a way of working is chosen.
- **Cut-off** — the club's free-cancellation deadline, a Raketa setting (0–72 h, default 24 h
  before), and **the one deadline in a game, the same for everyone in it**. Leaving before it is
  free: nothing is taken, and the share's hold is let go. At it, a full game's shares are
  **taken**, and a game still short is called off with every hold let go, nobody paying anything.
  Decided by ADR-0189's 2026-10-10 amendment (the mechanics Q113) and not yet built
  ([#637](https://github.com/Raketa02/Raketa/issues/637)); until then a leave before it is
  refunded at once, less the card fee.
- **Book-by** — the latest moment a proposal can still fill: **always the release time**, the
  game's start minus the club's release lead ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1; until [#670](https://github.com/Raketa02/Raketa/issues/670) lands, the start minus the
  minimum notice at an Instant or On request club). So no game fills later than a day before its
  start, and by default three. **Derived, never chosen** — once, from the club's terms, and carried
  on every sellable court hour. No other clock runs on a proposal.
- **Paused** — a club taking no new cards on its courts. Booked games are played as booked, and
  cards already dealt keep their court until their book-by, so its hours stay sellable. A paused
  club is still **Live**.
- **Setup checklist** — the **four** steps before a club's courts reach any deck: connect payments,
  add Courts, set Raketa hours and Prices, confirm the Raketa settings. *Choose a way of working*
  left it on 2026-10-12 ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1, not yet built — [#670](https://github.com/Raketa02/Raketa/issues/670), [#674](https://github.com/Raketa02/Raketa/issues/674)). Each is **done**, **to do**,
  **locked** behind the step it needs (hours and prices behind a court) or **pending** — payments,
  until connecting Stripe is built. Read off the Club courts, never stored. **Live** — every step
  but a pending one done.
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
  Group members hold a Skill rating; for an Official group, the ones it declares. **Any player
  sees any group's card, sheet, member faces and activity** — in **Hottest groups** — whether a
  member or not; **the group page stays members-only**, and a non-member asking for it reads
  `group_not_found` ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §3, built by [#792](https://github.com/Raketa02/Raketa/issues/792), [#800](https://github.com/Raketa02/Raketa/issues/800)). _Avoid_: team,
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
  **Its courts are its club's, hour by hour** ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7, not yet built —
  [#746](https://github.com/Raketa02/Raketa/issues/746)): at an hour its club has a free court, only
  the club's are offered; at an hour it has none, other clubs within the club's distance are offered
  too, after it and marked as offered because the club is full, unless the club switched **other
  clubs' courts** off. Until then another club was used only when the players shared no hour at the
  club in 14 days, and the switch was off by default.
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
  **declined** removes the request **silently**, and they may ask again. **Withdrawn** — by the
  player who asked, from *Asked* in Hottest groups — removes it at once from the Owner's, the
  Administrator's and the club website's lists, **tells nobody**, and they may ask again; withdrawing
  a request already answered changes nothing and still succeeds. A new event on the group's stream
  ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §3, built by [#792](https://github.com/Raketa02/Raketa/issues/792)). The same word as a
  yes's **Withdraw** (Proposals), and the same shape — taken back, free and silent — on a different
  thing: always *withdraw a Join request* in prose. _Avoid_: application, invitation (an
  **Invitation** is a club naming an Administrator); cancel or retract for withdraw.
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
- **Hottest groups** — Home's first new row: up to **6** groups with **3 or more players**, Player
  and Official alike, the reader's own included, by **Heat**: **HOTTEST** first, then **GROWING**,
  then the rest. Each card carries what its **group sheet** shows: games this week, players and new
  this month, up to 6 member faces (4 on the card; the reader's friends first, then the
  longest-standing members), and the reader's chip (*Join*, *Ask to join*, *Asked*, *You're in*). **The faces can't be tapped**: they are
  a picture of the group ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §3, built by [#792](https://github.com/Raketa02/Raketa/issues/792), [#800](https://github.com/Raketa02/Raketa/issues/800)). _Avoid_: trending,
  popular, top groups.
- **Heat** — how much is going on in a group: **2 × *games this week* + 3 × *new players this month*
  + *players*, counted up to 20**. *Games this week* are games booked in the group whose court time
  falls in the last 7 days and weren't called off, scored or not, friends games included; *new players
  this month* joined in the last 30 days and are still members; *players* are members today. Both
  windows roll. A card's **heat bar** is its heat over the HOTTEST card's, or over the highest in the
  row when there is none. Read on each request, never stored. _Avoid_: score, activity score,
  popularity.
- **HOTTEST** — the tag, *▲ HOTTEST*, on **exactly one** Hottest groups card: the highest Heat, and
  only if that group had at least one game this week. Never a property of a group outside the row.
- **GROWING** — the tag, *+ GROWING*, on any other Hottest groups card with **+4 or more** new
  players in 30 days **and** new players at least **a quarter** of today's players, so a 120-player
  group needs +30. _Avoid_: new, rising.

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
  (ADR-0191 §4). **It carries the name the club typed**, which the club's own pages and the
  Administrator's own emails use, and which *… runs this group* says until the person has a
  **Nickname** ([ADR-0199](docs/adr/0199-a-player-is-known-by-their-nickname.md) §4); no player surface says it otherwise.
  **Collisions, recorded:** an Administrator is **not the `ADMIN` Authority** and holds no power
  over the platform or any account; the **admin** tag on a Members list is **copy** for *runs this
  group*, not a role; and *Administrator* in the app's profile switcher is **UI vocabulary** for
  this side of the account (see **Player**). _Avoid_: admin (as the noun), manager, moderator,
  staff, group admin.
- **Invitation** — the club naming a person as Administrator, **by name and email and nothing
  else**: the club never sets, sees or handles a password or a code. Delivered by email as a
  button and an **8-character code**, valid **72 hours** and resendable. A **new person** sets a password through it and gets an account that holds
  **no player name** — the name the club typed stays on the Administrator (ADR-0199 §4) — and no
  Nickname and no Adult attestation; an **existing account** accepts
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
[#543](https://github.com/Raketa02/Raketa/issues/543) (On request, removed by
[ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) — [#669](https://github.com/Raketa02/Raketa/issues/669)),
[#544](https://github.com/Raketa02/Raketa/issues/544) (leaving and the cut-off),
[#545](https://github.com/Raketa02/Raketa/issues/545) (rescues) and
[#547](https://github.com/Raketa02/Raketa/issues/547) (the club runs it). A club's cancel that moves the
game is decided by ADR-0196 §2 and built by [#672](https://github.com/Raketa02/Raketa/issues/672).

**A booking is the game a full card became**, and its id is the card's. Its money is the Seat
charges' (**Payments**), its result the Game's (**Games**).

- **Booking** — a filled proposal: the club, the court and its number, the hour, the seats and
  their sides, the cut-off as the club set it, and its state — *booked*, *seat open*, *called off*,
  *played*. An **event-sourced aggregate, one stream per filled proposal**. **Born *booked***, at
  every club; *played* is read off the clock and never recorded. It opens the ordinary **Game**
  when it is booked. *Waiting for the club* — an On request club's request, which it accepted,
  refused or let time out — and the wait on a payment after the club's yes retired on 2026-10-12
  ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1; not yet built — [#669](https://github.com/Raketa02/Raketa/issues/669)). _Avoid_: reservation, and *held* for a booking (a
  **Seat charge**'s share is held — Payments).
- **Leaver** — a player who left a booking. **Before the cut-off, nothing is taken**: the share's
  hold is let go, nobody is refunded, and no fee arises for the leaver or the club. **After it**,
  the share was taken, and comes back only when the seat is taken, **less exactly the fee kept on
  the leaver's own payment** — never an estimate. Told to the Game as a **Departure**. Decided by
  ADR-0189's 2026-10-10 amendment (the mechanics Q113) and not yet built
  ([#637](https://github.com/Raketa02/Raketa/issues/637),
  [#641](https://github.com/Raketa02/Raketa/issues/641)); until then a leaver before the cut-off is
  refunded at once less the estimated card fee. _Avoid_: a refund for a leave before the cut-off
  (only the **Holding time**'s fallback, a share taken early, is refunded).
- **Rescue** — an open seat in a **booked** game that lost a player. Shown in **Fill in** and dealt
  to the best fits as a Seat open card; taking it books at once, and the rescuer sits where the
  leaver sat. The seat that opened first is taken first. Since ADR-0189's 2026-10-10 amendment
  (Q113, not yet built — [#640](https://github.com/Raketa02/Raketa/issues/640)) the rescuer's money
  follows the game's: held until the cut-off, or taken at once after it; and a rescuer whose card
  is refused keeps the seat for 30 minutes, never past the start.
- **Fill in** — the group's rescue board (**Seats to fill**) plus **You're In**, your own yeses
  that have not filled. It never offers a proposal that is still filling.
- **Check-in** — *retired 2026-10-11* ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §4, not yet built —
  [#651](https://github.com/Raketa02/Raketa/issues/651)–[#653](https://github.com/Raketa02/Raketa/issues/653)).
  A club scanning a player's QR code, or typing its short code, at the desk on the day; optional
  per club, off by default, and never a condition for money. It shielded a player from a no-show
  report and proved only that somebody came. It is removed from the player app, the club website
  and the backend; whether somebody came is now caught **at the court** (Games: **Isn't here
  yet**, **Arrival**). `PlayerCheckedIn` stays decodable and folds to nothing. _Avoid_: check-in
  for an **Arrival**.
- **Seat open** — a game missing a player, as the people still in it read it on Home: a
  **booked** game that lost one, whose seat is a **Rescue**; and, since ADR-0189's 2026-10-09
  amendment (the mechanics Q106), a full game that **went back to filling before it was booked**
  while it waited on one payment: a player left it, a yes was taken back, or the **Time to pay**
  (since Q113, also the **Time to fix the card**) ran out. (Until 2026-10-12 a full game could also
  fall back while it waited for its On request club, [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md).) That second
  kind is not a rescue: its seat is offered only in decks, as any proposal still filling, and it
  is in *You're In* as well. It is booked when it refills, and is called off, nobody paid, if its
  book-by passes first.
  The second kind is decided and not yet built ([#624](https://github.com/Raketa02/Raketa/issues/624)).
  _Avoid_: called off for a game that is only filling again.
- **Waiting for one payment** — a full game while one player's **Time to fix the card** (before
  the cut-off) or **Time to pay** (after it) runs: nobody has paid, the others' holds are kept,
  and the court is not held. It is on all four's Home as
  *Waiting for one payment · until 14:40 · Nobody pays until it's in* in both windows. The refused
  player's own card reads *Fix your card by 14:40* before the cut-off (Q113) and *Confirm your
  payment by 14:40* after it. The club sees nothing of it: the booking-level wait after a club's yes,
  *Accepted · waiting for one player's payment*, retired with On request ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1). It ends booked
  when the payment is in, *Seat open* when the time runs out, or called off when no time is left
  before the book-by. Decided by ADR-0189's 2026-10-09 amendment (the mechanics Q109–Q112) and
  built by [#625](https://github.com/Raketa02/Raketa/issues/625) and
  [#626](https://github.com/Raketa02/Raketa/issues/626); the time to fix the card is
  [#638](https://github.com/Raketa02/Raketa/issues/638)'s.
- **Move by cancel** — a club's cancel that a free court **of the same club** absorbs, when nothing
  about the game changes: the same sport, day, hour and price, and the same **Kind of court**, or
  indoor for an outdoor game — indoor only for a *weather* cancel. The same kind is picked first,
  then indoor, each in the club's own court order. The booking moves to that court and **is never
  called off**: every hold, or every share already taken, stays as it was, nothing is refunded or
  let go, nobody is owed a card, and every player is told **Game moved** (Notifications). The club's
  cancel dialog previews it, and *Cancel the game anyway* skips it. The cancel decides afresh when
  the club confirms. Decided by [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §2, not yet built ([#672](https://github.com/Raketa02/Raketa/issues/672)). _Avoid_: reschedule, transfer, and *move* for anything
  that changes the club, the day, the hour or the price — that is a new card.
- **Friends game** — a Booking **born at its send**, booked by a friend: one player, the **sender**,
  seats friends (**Friends**) on a group's Friends tab, picks the kind for this game only, and
  sending it books the court at once — on the court-hour's unique index, with an id of its own, since
  no proposal precedes it. It records the sender (In), an **Invited seat** for each other player, the
  kind, the **Pay mode** (*Split the cost* or *Whole court*), the court and its number, the sides, the
  cut-off and the pool, and opens the Game and its chat at send. **While its sender covers it — Split
  the cost with the sender In, or Whole court — it is never called off at its cut-off**: each seat
  without its own payment is paid by the sender's **Cover** (Payments) and, if empty, opened as a
  Rescue. A sender has **at most 2 waiting for answers**, each counts in every player's games per
  week, and its court and hour never change once sent: the sender calls it off, free until the
  cut-off, or **leaves · the others play on**, which with Split the cost turns it into an ordinary
  booking. Its card before sending, built from the fixed
  line-up, is the **friends card** (Proposals), a read. Decided by [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §5–§6, not yet built
  ([#751](https://github.com/Raketa02/Raketa/issues/751),
  [#752](https://github.com/Raketa02/Raketa/issues/752)). _Avoid_: private game, invite game, and
  *friendly* (For fun is a kind, and a friends game may be either).
- **Invited seat** — a friends game's seat held for one invited friend for **24 hours**, never past
  the cut-off when the invitation is made before it, nor past the start when made after it.
  **Accepted** (the friend is In), **declined** with *Not this time*, or **run out** (silence is *Not
  this time*). The screens call it an *invitation*, never an **Invitation** (a club naming an
  Administrator). An **empty seat** is a friends game's seat with nobody In and no invitation
  running. It is **not a Rescue** until its sender opens it to the group, or the cut-off arrives.
  Anybody In may invite one of their own friends into it, before or after the cut-off; the first to
  accept and pay takes it, or, once it is a Rescue, the first rescuer. _Avoid_: reserved seat, and
  *held* for a seat (a share is held).
- **Guest** — a friend seated in a friends game in a group they aren't a member of. The game is on
  their Home, in its chat and on its result; the group's deck and Fill in are not theirs, and a
  Rescue is never offered to one. _Avoid_: visitor, outsider, non-member (as a role).
- **Pay mode** — how a friends game is paid, chosen on the send sheet: **Split the cost** or **Whole
  court**. **Split the cost** (first): each seat's own player pays their share on accepting, and the
  sender's card holds the sender's share plus a Cover for every other seat until the cut-off (*We hold
  100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat still empty then.*).
  **Whole court**: the sender pays every seat, and friends accept without paying (*Tomek paid the
  court*). The specs shorten the first to *Split*, which is never the forecast's **Split** (Games).
  _Avoid_: *Split* alone in the glossary, split payment, host pays, treat.

**Invariants**
- **A game plays full or not at all.** A seat that opened before the club's cut-off and is still
  open at it calls the game off, and the court is the club's again; a seat that opened after the
  cut-off leaves the game going ahead short. **One exception: a friends game its sender covers**
  ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §6). Its empty seats at the cut-off are paid by the Cover and opened as Rescues,
  and a seat nobody takes stays empty, as after the cut-off.
- **The club may move or cancel a game until it starts.** A move is to another court of the sport
  at the same hour — since ADR-0196 §2, of the same Kind of court or indoor for an outdoor game, and
  told to the players (not yet built — [#671](https://github.com/Raketa02/Raketa/issues/671)).
  **A cancel is a Move by cancel whenever a court absorbs it**, unless the club cancels it anyway;
  otherwise it calls the game off, its players still in are owed a card (Proposals: **Owed card**),
  and it is on nobody's record. A cancel that calls a game off refunds everybody still in, in
  full. Since Q113 that holds after the cut-off, where the club bears the fees; before
  it, the cancellation lets every hold go and nobody pays a fee — decided, and not yet built
  ([#637](https://github.com/Raketa02/Raketa/issues/637)).

### Payments

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4–§5 and
built by [#536](https://github.com/Raketa02/Raketa/issues/536)
([ADR-0190](docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)); the
**Seat charge** by [#541](https://github.com/Raketa02/Raketa/issues/541), and connecting a club's
account by [#537](https://github.com/Raketa02/Raketa/issues/537).

**How a player pays: a card or a wallet saved once, charged later by the club.** Every charge is
made on the club's own account — **the club is the seller** — and a player's card is copied there
for each one. Money goes from players to the club, never from one player to another, and **a player
pays only their own share, except a friends game's sender, whose Cover pays for seats that aren't
theirs** (below). Since ADR-0189's 2026-10-10 amendment (the mechanics Q113) a share is **held** when
its game fills and **taken** at the club's **Cut-off**; nothing is taken before it, and no
estimated card fee is printed anywhere — decided, and not yet built
([#636](https://github.com/Raketa02/Raketa/issues/636)–[#641](https://github.com/Raketa02/Raketa/issues/641)).

- **The club is the seller** — every charge is made on the club's own Stripe account, and the club
  pays the card fee. Raketa takes no fee.
- **Seat charge** — one seat's money in one booking: an **event-sourced aggregate, one stream per
  payment**, born at the fill and never before — a yes moves no money. Raketa's account of a
  payment; Stripe is the ledger of record, and a notice from it moves a charge only forward. Since
  ADR-0189's 2026-10-10 amendment (Q113; not yet built — [#636](https://github.com/Raketa02/Raketa/issues/636), [#637](https://github.com/Raketa02/Raketa/issues/637), [#639](https://github.com/Raketa02/Raketa/issues/639),
  [#641](https://github.com/Raketa02/Raketa/issues/641)) it is:
  - **checked** — held for seconds and let go at the fill, its hold not reaching the cut-off, and
    waiting for its **Holding time**;
  - **held** — until the cut-off, with the hold's **last moment**;
  - **taken** — at the cut-off, or at once after it, with the **real fee** once the provider
    reports it;
  - **released** — let go on a leave, a call-off or a club's cancel before the cut-off: settled,
    and nothing moved;
  - **refunded** — by an **exact amount**, the share or the share less the fee kept;
  - or **refused**, and then confirmed by the player when their bank wanted them present or the
    card was declined.

  **A held charge is not paid**: *paid*, and a club's *Collected*, mean taken. _Avoid_: *charged*
  for a share that is only held.
- **Cover** — a Seat charge **paid by the sender of a friends game for a seat that isn't theirs**: the
  one place a player pays for another player's seat ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §6, not yet built —
  [#751](https://github.com/Raketa02/Raketa/issues/751), [#752](https://github.com/Raketa02/Raketa/issues/752)). At send the sender's own share and one Cover per
  other seat are authorised together, all or nothing, **with the sender present**, and the amount
  agreed to — stated above the button — is recorded with the sender's terms acceptance. **Every
  Cover stays held until the cut-off**, or is checked and held at the Holding time like any seat charge, and is never let go and
  held again in between. **At the cut-off it is taken only for a seat without its own payment**, and
  let go otherwise. A later rescuer's share refunds it, less exactly the fee kept on it, as a late
  leaver is refunded. Only friends games have one; nobody takes a Cover over from the sender.
  _Avoid_: guarantee, deposit, *paying for a friend*.
- **Time to pay** — the **30 minutes** a player whose share was refused **after the cut-off**,
  where money is taken at once — when a game filled, or taking a **Rescue** — has to pay, never past
  the game's book-by (a rescue: never past its start). An On request club's yes started one too
  until that way was removed ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1, not yet built — [#669](https://github.com/Raketa02/Raketa/issues/669)).
  Their seat is theirs alone meanwhile, and the other seats' holds are kept, so paying in time
  books the game without asking anybody's bank again; when it runs out the holds are
  let go and the seat is offered as any open seat of a game still filling (on a rescue, the seat is
  offered again). Nothing retries a card
  by itself. It is one player's clock, never a card's: the book-by stays the only deadline on a
  proposal. Decided by ADR-0189's 2026-10-09 amendment (the mechanics Q109) and built by
  [#625](https://github.com/Raketa02/Raketa/issues/625) and
  [#626](https://github.com/Raketa02/Raketa/issues/626); since the 2026-10-10 amendment (Q113)
  only after the cut-off, before which it is **Time to fix the card**
  ([#638](https://github.com/Raketa02/Raketa/issues/638)). _Avoid_: grace period, payment window.
- **Time to fix the card** — the **30 minutes** a player whose card was refused **before the
  cut-off** has to fix it — at the fill, at the **Holding time**, or taking a **Rescue** — never past
  the cut-off or the book-by. (An On request club's yes no longer starts one: ADR-0196 §1.)
  Nothing is being taken, so nothing
  is paid in it: the player confirms with their bank or changes card, and the same **Card check**
  or hold runs again at their press. Their seat is kept for them alone, and the others' holds are
  kept. Not fixed, the seat goes to others and nothing is owed: at a holding it opens as a Rescue,
  counted on the record as a leave before the cut-off. Time to pay's machinery serves it. Decided
  by ADR-0189's 2026-10-10 amendment (the mechanics Q113) and not yet built
  ([#638](https://github.com/Raketa02/Raketa/issues/638),
  [#639](https://github.com/Raketa02/Raketa/issues/639),
  [#640](https://github.com/Raketa02/Raketa/issues/640)). _Avoid_: *pay by* for it, retry.
- **Card check** — at the fill, a seat whose hold would not reach the cut-off: its share is held for
  a few seconds and let go, all or nothing with the others, which proves the money is there that
  day. A hold **reaches** the cut-off when its last moment is at least **6 hours** after it — a
  domain constant, as is the Holding time's four days. The share is then held at its **Holding
  time**. Never a receipt. Decided by ADR-0189's 2026-10-10 amendment (Q113) and not yet built
  ([#639](https://github.com/Raketa02/Raketa/issues/639)). _Avoid_: pre-authorisation, verification.
- **Holding time** — when a seat's share is held to stay until the cut-off: at the fill or at the
  Rescue, when that hold reaches the cut-off (never at a club's yes since ADR-0196 §1);
  otherwise **four days
  before the cut-off**, when a periodic job holds every checked share. If even that hold would not
  reach, the share is taken at the hold's last safe moment — its last moment less 6 hours — and a
  later leave before the cut-off is refunded in full. Decided by ADR-0189's 2026-10-10 amendment
  (Q113) and not yet built ([#639](https://github.com/Raketa02/Raketa/issues/639)).
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
  to fills, the club holds your share, and takes it at its cut-off; leave before then and nothing
  is taken* (the mechanics §12.5, a new version since Q113, owed by
  [#637](https://github.com/Raketa02/Raketa/issues/637) and
  [#642](https://github.com/Raketa02/Raketa/issues/642) — a player who accepted the earlier words
  accepts these before their next game holds money). **Accepted before anything is
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
  **Group** is the first kind of pool; a city (Explore) will be the next. **Its clubs are read per
  hour**: a Player group's home club first, then other clubs within 10 km; an **Official group**'s by
  the hour-by-hour rule under that term ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7). One source serves the deck, Post a game
  and the **Friends card** alike. Every proposal carries
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
- **Yes** — a swipe right, or *I'm in*: *"if everybody is in, book it and take my share at the
  club's cut-off"* (Q113, decided and not yet built — [#637](https://github.com/Raketa02/Raketa/issues/637); it was *charge my share*). Silent,
  free, and it holds no court and no money. **Yeses are the game's, never a version's**: a yes on any version
  counts toward the one game. A yes needs a saved **Payment method**. A **No** is a swipe left, equally silent, and **final**: the card never comes back.
  _Avoid_: vote, like.
- **In** — a player who said yes to a proposal that has not filled. **Everybody In fits everybody
  else In**: a version is dealt only to people who fit the people In and each other, and a yes
  lands only from somebody who fits everybody In — *fits* being today's pair rule for one
  court (no block either way, mutual gender preference, Levels within the kind's window). Since
  [ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §6 the rule gains one more clause, the **Reliability filter**
  (Player Score), asked where a block is; unlike a block it takes no yes back, so a yes given
  before the filter was switched on, or before somebody dropped below it, stands (built by
  [#661](https://github.com/Raketa02/Raketa/issues/661)).
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
- **Fills** — the moment the last needed yes lands and a **Booking** opens. Every seat's share is
  then **held** together, all or nothing — a **Card check** where a seat's hold would not reach the
  cut-off — and **taken at the club's Cut-off**, or at once for a game that fills after it. **At
  every club**: no club confirms a game since [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1 (not yet built — [#669](https://github.com/Raketa02/Raketa/issues/669)), which retired an
  On request club's *waiting for the club*.
  Holding in place of charging is decided by ADR-0189's 2026-10-10 amendment (Q113) and not yet
  built ([#637](https://github.com/Raketa02/Raketa/issues/637)).
- **It's a game!** — the screen the player whose yes filled the game, or who took a rescue, sees.
  It marks the players being **matched**, not only booked: since ADR-0189's 2026-10-09 amendment
  (the mechanics Q103, Q110), it also shows when one payment is still missing, and the player whose
  confirmed payment completes a game sees it too. The missing payment coming in never brings a
  second one ([#622](https://github.com/Raketa02/Raketa/issues/622), [#625](https://github.com/Raketa02/Raketa/issues/625)). Its *answers by · Nobody pays until
  it confirms*, at an On request club, retired with that way ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1, [#676](https://github.com/Raketa02/Raketa/issues/676)).
- **Home** — the first tab of the bottom bar. **Since [ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §4 it reads, top to bottom** (not yet built — [#816](https://github.com/Raketa02/Raketa/issues/816)–[#823](https://github.com/Raketa02/Raketa/issues/823)):
  - **the header: the envelope, the bell and the trophy**, right-aligned in that order, the trophy in
    the corner. **The envelope** opens **Needs your answer**, and is there only while something waits
    in it. **The trophy**, *🏆 #7*, is the reader's **Place** in the sport of their latest result, in
    the view they last looked at, with no number when they have none, and opens Rankings
    ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §5, built by
    [#768](https://github.com/Raketa02/Raketa/issues/768), [#775](https://github.com/Raketa02/Raketa/issues/775));
  - ***Get your level***, while the player is in a group and rated in nothing, **whether or not
    somebody asked them** ([ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md) §7);
  - ***Your games***: your games from the moment they fill, and the games waiting for one payment,
    or full once and filling again (*Seat open*). A friends game you sent is among them from its
    send. A booked game's row names its court's **Kind of court** (ADR-0196 §4). A player in no group
    reads *Join a group to get games — see Groups heating up, just below.*;
  - **FOR YOU**: the five rows of [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
    §1, in that order (built by [#798](https://github.com/Raketa02/Raketa/issues/798)–[#805](https://github.com/Raketa02/Raketa/issues/805)):
    **Hottest groups** (Groups), **Same competitive level players**, **New in Raketa**, **Same vibe
    players** (Discovery) and **Top 10** (Rankings). Each is **folded into one line**, a title with a
    count of how many there are to explore (*99+* past 99; none on Top 10), **one open at a time**,
    each read on its own and hidden while it has nothing to show. On screen they are titled *Groups
    heating up*, *Players at your level*, *New in Raketa*, *Players with your vibe* and *Top 10*;
    the terms keep their names. For a player in no group, *Groups heating up* starts open.

  **The four cards that waited on the player are no longer on Home.** *To confirm*, the friends game
  invitations, the friend requests and the asks for a level wait in **Needs your answer**. Until
  ADR-0205 they were rows above *Your games*: **FRIENDS GAME**, **TO CONFIRM**, **FRIEND REQUESTS**
  and **ASKED FOR A LEVEL** ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
  and its 2026-11-07 amendment). **Home's badge** counts only the games that need you, a payment to
  confirm among them, wherever it waits. Proposals assembles Home.
- **Needs your answer** — **the sheet the header's envelope opens on Home, and everything waiting in
  it** for the player's answer ([ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §1–§3, built by [#815](https://github.com/Raketa02/Raketa/issues/815)–[#819](https://github.com/Raketa02/Raketa/issues/819)).
  - **Four sections, always in this order, each a sideways rail and each hidden while empty:**
    **To confirm** (a payment to confirm or a card to fix, with its deadline while it has one, read
    by Proposals), **Friends game** (an invitation into a **Friends game**, one at a time), **Friend
    requests** (Friends) and **Asked for a level** (Friends' **Ask for a level**).
  - **The envelope is there only while something waits.** Its badge counts what is **new**: what
    arrived since the player last closed the sheet, kept on the server so every phone agrees.
    Closing the sheet records a **visit** whose watermark is the newest item it showed, owned by
    Proposals, and the count travels on Home's read.
  - **An item arrives once.** A new friend asking for the same sport's level arrives; a payment
    moving from *Fix your card* to *Confirm* does not.
  - **Answering** takes the item out, and the last answer closes the sheet and takes the envelope
    away. A link or a notice that pointed at one of the four opens Home with the sheet up.

  _Avoid_: inbox, pending, requests (a **Friend request** is only one kind), envelope (the envelope
  is only the button), and the bell's **new**, which counts notices, not what waits.
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
  for that version on a competitive card and the **Social vibe** of that version's table on a
  For-fun one, never both, an overlap grid and the court block, which names the **Kind of court** when every
  free court it could be booked on is one kind. **An Owed card comes first** for each player it is
  owed to, soonest first among owed cards (ADR-0196 §3, [#673](https://github.com/Raketa02/Raketa/issues/673)).
  **The competitive deck** is then ordered by the seats that would be open
  after your yes (fewest first), then **Seat open › Challenge › Picked for you**, then the
  soonest deadline, then the best forecast. **The For-fun deck opens on the best company**: the
  **Rescues** next, by Social vibe, then every other card by the Social vibe it shows (rounded, so
  cards that look alike tie), then the seats open after your yes, then **Challenge › Picked for
  you**, then the soonest deadline — a full game gone back to filling is no rescue
  ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §4, [#830](https://github.com/Raketa02/Raketa/issues/830)). In both, the same people only at
  their best hour. A card you
  said no to never returns; one you are In on is in *You're In*; one you took your yes back from
  is dealt again. Never dealt: a kind your Play intent does not want, a share above **Most I'll
  pay**, a week at your **Games per week**, an hour you already have a game at, a club no longer
  selling, or a card with somebody In you may not share a court with. **The switch shows both
  kinds**: the one your Play intent does not want is a dimmed door with no number, which opens an
  in-place change of intent and is never where the deck opens. **A name whose intent no longer wants
  a card's kind is left off it** unless they are In
  ([ADR-0201](docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
  §2–§3, not yet built — [#738](https://github.com/Raketa02/Raketa/issues/738),
  [#740](https://github.com/Raketa02/Raketa/issues/740)). A projection, recomputed
  at every read and stored nowhere. (The Players deck of people went with Classic play.)
- **Owed card** — the new card dealt first to the players still in a game that a club's cancel
  called off: the one **Move by cancel** (Bookings) couldn't save. It is chosen **closest to the
  cancelled game first**: the same club, day and hour, on a court of the other kind or at a new
  price; then another club at the same day and hour, nearest first;
  then the closest hour in time, the home club first. An **Official group** reads its courts hour by
  hour, as every card does ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7). (Until 2026-11-06 it stayed at its home club
  unless its courts had no hour its players shared in 14 days.)
  It is an ordinary pick — its players free and fit, and each swipes it — that **records the
  players it is owed to**, and it is **first in each of their group decks** whenever they open it,
  until they answer it or it is gone, **with no mark**. A game no hour is found for stays owed until
  its old hour passes. Its notice is *Your new game*. Decided by [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §3, not yet built
  ([#673](https://github.com/Raketa02/Raketa/issues/673), [#677](https://github.com/Raketa02/Raketa/issues/677)).
  A card a no or a club's silence owed went with On request, and so did the rule that
  never dealt the owed players that club and hour again. _Avoid_: priority card, replacement game,
  and any mark or ribbon for it.
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
- **Friends card** — the card a fixed line-up of friends gets on a group's Friends tab before it is
  sent: the deck's card without its tiles — the evenest sides (or the sides the sender swapped to),
  the forecast, the overlap grid, and a court with the share. Its court is **the soonest hour still
  sellable, up to 14 days ahead, where all are free, a court is free under the pool's court rule and
  none has a game**; failing that, where most are free. *Find a court* lists every such court in the
  window, by how many of them are free. Blocks and a level in the sport apply; **the level window,
  the kind's tolerance and gender preferences don't**, because friends choose each other. **A read**:
  it makes no proposal and books nothing — sending it books a **Friends game** (Bookings).
  Decided by [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §5, not yet built ([#750](https://github.com/Raketa02/Raketa/issues/750)).
  _Avoid_: a proposal or a card *dealt* for it (nothing is dealt).
- **Games & money** — a player's two limits, across sports and pools: **Games per week** (1–7,
  default 2, counted Monday to Sunday: a week with that many games booked deals nothing more) and
  **Most I'll pay** (off, 35, 45 or 60 zł: a card whose share is above it is never dealt). An
  **event-sourced aggregate, one stream per player** under their own id, born by being used; the
  same answer records nothing.

### Notifications (`backend/app/modules/notifications/`)

Settled by [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5–§6 and
built by [#549](https://github.com/Raketa02/Raketa/issues/549) (the notices, the recent list, the
three choices, push) and [#559](https://github.com/Raketa02/Raketa/issues/559) (the phone). The
bell's number was decided by ADR-0189's 2026-10-09 amendment (the mechanics Q101, Q102); the server
keeps it since [#621](https://github.com/Raketa02/Raketa/issues/621), and the phone draws it from
[#627](https://github.com/Raketa02/Raketa/issues/627).

**What a player is told about their games, and where they find it again.** Notifications is
told by the other contexts and tells none of them.

- **Notice** — one thing a player was told about their games — a game booked, a payment to
  confirm, a game called off, a seat left, a card that needs only them, a level they need before
  any game can be dealt to them (*Get your level*, below) — or about their friends (*Friends'
  notices*, below), in the server's words, at the moment it
  happened. It is shown as a **banner** while the app is open, pushed once push is
  on, emailed when it is about money, and kept in the **recent notices**: the
  list behind the bell on Home, the newest 30. Most kinds are **always on**; three are the player's
  choice (*You complete it*, *Challenges for you*, *Fill in alerts*), capped per day and bundled.
  Nothing is told twice about the same thing, and nothing for a single swipe. A card that never
  filled ends untold. The kinds that told of an On request club's answer — *It's a game! · … answers
  by …*, *… confirmed your game* and *… couldn't take your game*, said no or didn't answer in time,
  the last two emailed — retired on 2026-10-12 ([ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1, not yet built — [#669](https://github.com/Raketa02/Raketa/issues/669), [#676](https://github.com/Raketa02/Raketa/issues/676)). A club's
  cancel notice says *We'll look for another game for you first*, as its email does, except to a
  leaver it refunds. _Avoid_: notification for the record (a notification is a delivery: a push,
  a banner, an email); and the payments provider's **notice** (Payments: an event Stripe sends,
  read once — ADR-0190), which is no player's.
- **Game moved** — an always-on notice to every player on a booking whose court changed, opening the
  booked game, never emailed. After a **Move by cancel** (Bookings): *Bonarka Arena moved your game
  to Court 3 · Thu 19:00* / *Court 2 can't be played · Padel · indoor · nothing else changes*, the
  reason worded per the cancel's reason. After the club's own move: the same title, with *Padel ·
  indoor · nothing else changes*. Decided by [ADR-0196](docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §2, not yet built ([#671](https://github.com/Raketa02/Raketa/issues/671), [#672](https://github.com/Raketa02/Raketa/issues/672), [#677](https://github.com/Raketa02/Raketa/issues/677)).
- **The bell's number** — the notices given since the player last opened the recent notices,
  shown as *99+* above 99. **Kept by the server, per player**, so it is the same on every phone;
  opening the list clears it, and the rows that came since the last visit stand out on that visit.
  Nothing is marked read row by row. **A player's own act is never counted back to them**, nor
  bannered: the notice that the yes they said filled a game, that they took a seat on one, or
  that a payment they confirmed completed one, is born seen. Nothing comes down at launch; what
  was told while the app was closed is in the number. _Avoid_: unread count; badge (Home's badge
  counts the games that need you).
- **The games' notices** — five always-on kinds told from the **Games** context, the first that
  Notifications hears from it ([ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §7, not yet built —
  [#663](https://github.com/Raketa02/Raketa/issues/663)): ***Isn't here yet*** to the absent
  player (*Ivan is at Ogrody 33 and you're not there yet — tap I'm here when you arrive*), ***They're
  at the club*** to whoever tapped, ***How did it go?*** to all of a Competitive booked game's
  players when its hour ends (a job tells it, every 30 seconds), ***Is that right?*** to the other
  side when a score goes up, and ***Were they there?*** to the courtmates when an absent player
  claims *I was there*. Each opens the game's **result screen**. Always on, because each decides
  somebody's record or result; **a For fun game is told none of them**. They are worth little
  until push reaches both phones, which a human sets up
  ([#665](https://github.com/Raketa02/Raketa/issues/665)) and the player app switches on
  ([#666](https://github.com/Raketa02/Raketa/issues/666)).
- **Get your level** — an always-on notice, *Get your level so your groups can deal you games.*,
  told **once per account, ever**: to an account that is a **Group member** of at least one group
  (player or official), whose first group join was at least 24 hours ago, and which holds no Skill
  rating. It names no group and no sport, opens **Home**, and is never emailed. A timed job tells
  it under a per-account key, so no process tells it twice; Groups answers when the account first
  joined a group. Decided by [ADR-0200](docs/adr/0200-a-level-is-asked-where-play-begins.md) §7, not yet built
  ([#727](https://github.com/Raketa02/Raketa/issues/727), [#731](https://github.com/Raketa02/Raketa/issues/731)).
- **Friends' notices** — the kinds **Friends** and a **Friends game** tell, **all always on, pushed and
  kept in the bell**, never emailed unless they are about money: a **friend request** (pushed once per
  request, never again for it), ***you're friends***, a **friends game invitation**, ***can't make
  it*** and ***didn't answer*** (to the sender), a **seat invitation** into an empty seat, ***seat
  taken***, a **friends game called off**, the **cover warning** (once, 24 hours before the cut-off,
  to a sender paying by *Split the cost* while a seat lacks its own payment: *At Fri 10:00 you pay 50 zł: your 25 zł and
  Ania's seat.*), and ***level asked*** — a friend asking for a level in a sport, not the
  once-per-account **Get your level** — with its answer, ***level got***.
  Answering a request or an invitation clears it from the bell, and a *level asked* row is listed
  only while its card waits (ADR-0202 §4's 2026-11-07 amendment) — on Home until
  [ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §1, then in **Needs your answer** (Proposals). Decided by [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
  §1, §4–§6, and built by [#745](https://github.com/Raketa02/Raketa/issues/745),
  [#749](https://github.com/Raketa02/Raketa/issues/749), [#751](https://github.com/Raketa02/Raketa/issues/751) and [#752](https://github.com/Raketa02/Raketa/issues/752).

### Friends

Settled by [ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) on
[#744](https://github.com/Raketa02/Raketa/issues/744), and specified in
[`docs/specs/friends/`](docs/specs/friends/README.md). **Built**: friendships by
[#745](https://github.com/Raketa02/Raketa/issues/745), the link by
[#748](https://github.com/Raketa02/Raketa/issues/748) and asking for a level by
[#749](https://github.com/Raketa02/Raketa/issues/749), with the player app's and the public site's
[#753](https://github.com/Raketa02/Raketa/issues/753)–[#760](https://github.com/Raketa02/Raketa/issues/760). The game friends send each other is a
**Friends game** (Bookings), and its sender's money a **Cover** (Payments).

**The people you play with, kept.** A friend is the shortcut to a game with people you already know,
instead of letting the deck pick them. Friends are made where people meet, in their groups, and held
across all of them. Since [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) a player found in the **Ranking** may be asked too, and since
[ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2 **anybody may be asked**, found anywhere — Home's people rows (Discovery) above all.

- **Friend** — somebody you asked who said yes, or who asked you and you said yes: one **Friendship**
  per pair of players, an **event-sourced aggregate**, held **across all their groups**. It survives
  either of them leaving a group and ends when either account is deleted. **Removing** a friend, from
  their record behind a confirmation, is silent and touches no game already sent or booked. **A block
  ends it**, either way round, silently ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §2). **Only your own friends are
  ever shown to you**: a response carries the reader's own relation to each player it names —
  *none*, *sent*, *asked you* or *friend* — and a face carries only *friend*, so Kuba never learns
  that Tomek and Magda are friends. _Avoid_: contact, connection, follower, buddy.
- **Friend request** — one player asking another to be friends, recording **where it was made**: a
  group, the record, a result, a link, **the ranking** with its sport (*Found you in the padel
  ranking*), or since ADR-0204 §9 one of Home's people rows — **Same competitive level** with its
  sport (*Your level in padel · 91% even*), **New in Raketa** (*Found you among new players*) or
  **Same vibe** (*6 things in common*), the line worked out when the card is read. **Anybody may be asked, with no daily
  limit** ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2, built by [#791](https://github.com/Raketa02/Raketa/issues/791)), except somebody whose **Show me to new
  people** is off and who shares no group, game or friendship with the requester, which is refused
  with one unnamed code. (From ADR-0203 §9 until #791: a shared group or the ranking, at most 10 a
  Warsaw day outside your groups.) Nobody asks themselves, and nobody asks while a request of
  theirs to that person is open. **Accept** makes them friends, and the requester is told. **Not
  now** **sets it aside**: the request stays open and can still be accepted, and the requester is
  never told and can't ask again. Two requests that **cross** — each asked the other before either
  answered — make them friends at once. **Cancelling** your own request is silent. **A request from a
  player the reader blocked is never shown to the reader**, read live, so the requester reads
  *request sent* forever, exactly as after a request set aside. _Avoid_: invitation for a request
  (an **Invitation** is a club naming an Administrator), friend invite, declined (nothing declines a
  request).
- **Friend link** — a player's own address on the public site, `/f/` and a **code**: random, shaped
  like a group's code, made on its owner's first read of it, never reused, one per player. **New
  link** replaces it, and the old code reads as not found. **Opening it never makes friends by
  itself**: it puts the owner's **Friend request** in the opener's **Needs your answer**, opening Home
  with the sheet up, through sign-up and onboarding when the opener has no account (since
  [ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §1, not yet built — [#817](https://github.com/Raketa02/Raketa/issues/817); until then at the top of
  Home, *Invited you to Raketa*). Nothing happens for the owner, or
  for somebody already a friend; a request the opener already sent crosses it; and when the owner
  blocked the opener, the owner's request is swallowed and nothing reaches the opener's Home. _Avoid_: invite link, referral link, and **Group link**,
  which joins a group.
- **Ask for a level** — a player asking a friend with no level in a sport to get one, so they can be
  seated: a notice that opens that sport's questionnaire, and a notice back when the friend's first
  level in it arrives. **Once per friend per sport.** **While it waits, it is a card in the friend's
  Needs your answer**, one per sport in its **ASKED FOR A LEVEL** section, naming every friend whose
  ask in it waits and isn't set aside,
  until the friend holds a level in the sport, by any route, or no asker is still their friend. **Not
  now** **sets aside** the asks the card named, as a **Friend request** is set aside: nobody is told,
  the card comes back only when a new friend asks in that sport and then names only the askers not set
  aside,
  and a set-aside ask is still answered, every asker told, when the level arrives. The *level asked*
  row is in the bell only while its card waits in Needs your answer. Decided by ADR-0202 §4's
  2026-11-07 amendment (the mechanics Q129) and built by
  [#764](https://github.com/Raketa02/Raketa/issues/764) and
  [#765](https://github.com/Raketa02/Raketa/issues/765) as a card on Home, drawn instead of Home's
  *Get your level* for a player rated in nothing. **Since
  [ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §1 and §4 it waits in Needs your answer, not on Home**, with no subtitle, and **is never drawn
  instead of *Get your level***, which shows whenever the player is in a group and rated in nothing,
  asked or not (not yet built — [#816](https://github.com/Raketa02/Raketa/issues/816)). A new
  friend's ask on a card already there is **new** in Needs your answer. _Avoid_: rating request,
  nudge; declined (nothing declines an ask).

### Rankings

Settled by [ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) on [#767](https://github.com/Raketa02/Raketa/issues/767), and specified in
[`docs/specs/rankings/`](docs/specs/rankings/README.md). **Built** by the backend's
[#768](https://github.com/Raketa02/Raketa/issues/768)–[#773](https://github.com/Raketa02/Raketa/issues/773)
and the player app's [#774](https://github.com/Raketa02/Raketa/issues/774)–[#779](https://github.com/Raketa02/Raketa/issues/779).
**Amended 2026-11-14** by [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2 (built by [#791](https://github.com/Raketa02/Raketa/issues/791),
[#797](https://github.com/Raketa02/Raketa/issues/797), [#799](https://github.com/Raketa02/Raketa/issues/799), [#805](https://github.com/Raketa02/Raketa/issues/805)): **the ranking shows everybody**.
*Show me in General* is retired, blocks no longer hide rows, and *of N* counts everyone. Home gains
**Top 10**.

**Where a player stands in a sport, against everybody or against their friends.** It ranks by the
**Level** and owns nothing else about a player. It keeps a **stored copy** of the level and of its
history, written only from the rating's `rating.moved_on_result`: the stated exception to the
backend's *derived, never stored*, because a page of 50,000 players and a level as it stood 7 days
ago can't be folded on every read (ADR-0203 §10).

- **Ranking** — the players of one sport, ordered by their **Level**, in one of two views,
  **General** or **Friends**. **The ranked number is the level itself**, never a second number, and
  the ranking never changes a level. Only a **result** counts — a confirmed competitive result with a
  winner, one that moved a level — so For fun, *Played · no score* and *Disputed* never do. One
  ranking per sport, for all four; men and women in one list; no cities. Read on the Rankings page,
  opened from Home's trophy. _Avoid_: leaderboard, ladder, standings, points, league; *rank* for the
  number, which is a **Place**.
- **General** — the view of everybody in Raketa **Listed** in a sport, from their 5th result. It is
  loaded in pages of 50. _Avoid_: global, overall, everyone.
- **Friends** (the view) — the reader and the reader's **Friends**, each **Listed** from their first
  result, shown whole. In prose, *the Friends view*: not the **Friends** context, and not a
  **Friend**.
- **Listed** — on a view's list: **5 results** in the sport for General, **1** for Friends, the last
  of them settled within **90 days**. A player **off the list** after 90 days is listed again by their
  next result, at their level then, with no new wait. Listing never touches the level. _Avoid_:
  ranked (as a state) in prose and code, qualified, active; the players' own words say *ranked*
  (*Not ranked in padel yet*, the words §30), and that is copy, not a term.
- **Place** — a listed player's position in one view and sport: level, highest first; then more
  results; then who reached that level first; then the player id. **Every place is unique.** ***Of
  N*** counts every listed player in the view. **Since ADR-0204 §2 every row is shown to every
  reader** — no switch and no block hides one — so a place, *of N*, the podium and the gap line count
  everyone. Shown on the page's place card, with a **gap line** to the players just above and below,
  on Home's trophy (*🏆 #7*) and in **Top 10**. _Avoid_: rank (for the number).
- **The chip** — the places a player moved in the last 7 days, rolling: *▲ n*, *▼ n*, *—* or
  ***New***. It compares the place now with where **today's same players** stood by their levels
  exactly 7 days earlier, so an arrival, a departure or a new friend moves nobody, and an overtake
  does. *New* is the 7 days after a first entry into that view's list; a comeback gets a real chip.
  It reads a **level history** kept as each level moves, and no job. Not a group's sport chip, nor
  the reliability chip on a card. _Avoid_: movement, trend, delta.
- **Top 10** — Home's last row: **places 1 to 10 of General** in one sport, the true top of the
  Rankings page, with a sport pill offering all four sports and ***Nobody ranked in squash yet*** for
  a sport nobody is listed in. It appears once anybody is listed in any sport, and opens on the
  trophy's sport, else the next sport in the app's order where somebody is listed. A pick lasts while
  the reader is on Home. A card opens the record; **Rankings ›** opens the page
  ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §8, built by [#797](https://github.com/Raketa02/Raketa/issues/797), [#805](https://github.com/Raketa02/Raketa/issues/805)). _Avoid_: leaderboard, top
  players, See all.
- **Show me in General** — *retired 2026-11-14* by ADR-0204 §2. It was a switch, on by default, that
  took a player's row out of everybody else's General and closed their record to strangers found
  there. **Show me to new people** (Player profile) replaces it, and closes nothing in the ranking:
  a player who had this off starts with that off. _Avoid_: the term, for anything current.

**Invariants**
- **The level is the one number.** The ranking sorts by it and never writes it: only the rating
  context writes μ. The stored level and its history are written only from the rating's events, and
  a rebuild from the event store equals live delivery.
- **A place means the same on every phone.** Since ADR-0204 §2 no row is hidden from anybody, by a
  switch or a block, so there is no gap to leave.
- **A chip moves only when a level moved.**
- **A block hides no row**, since ADR-0204 §2, and **closes the record both ways** (Blocks): a tap on
  a blocked player's row reads *This record isn't available*.
- **Any player may open any record and ask anyone** (Player record, Friends), with no daily limit,
  except across a block or **Show me to new people**'s rule.
- **The ranking tells nobody anything.** No push, no bell line, no email.

### Discovery

Settled by [ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) on [#790](https://github.com/Raketa02/Raketa/issues/790), and
specified in [`docs/specs/home-rows/`](docs/specs/home-rows/README.md). **Built** by the backend's
[#793](https://github.com/Raketa02/Raketa/issues/793)–[#796](https://github.com/Raketa02/Raketa/issues/796)
and the player app's [#801](https://github.com/Raketa02/Raketa/issues/801)–[#804](https://github.com/Raketa02/Raketa/issues/804).

**Who is around you, on Home.** The three **people rows** suggest players to the reader: at their
level, new to Raketa, or like them. It owns nothing about a player. It keeps **stored copies** — a
**player directory** fed by the profile's and the user's events, and every player's **current level
per sport** fed by the rating's events, questionnaire and results alike — and the per-viewer **rest
count**: the stated exceptions to the backend's *derived, never stored*, because a Home read can't
replay every player's streams (ADR-0204 §10). Hottest groups belongs to **Groups** and Top 10 to
**Rankings**.

- **People rows** — *Same competitive level players*, *New in Raketa* and *Same vibe players*, and
  their See all screens. **Never** the reader, a blocked pair either way, a player with **Show me to
  new people** off, an account that doesn't play, or a deleted account. Each person carries the
  reader's own relation and the **round friend button**: **+** sends a request, **…** opens *Cancel
  request*, **✓** opens *Remove friend*, **the envelope** accepts. _Avoid_: suggestions, people you
  may know, recommendations.
- **Same competitive level players** — the players whose level in a sport the reader also plays is
  closest, **each in the sport where the two are evenest**, by **% even**. Shown only once the reader
  has a level in any sport. _Avoid_: similar level, matches, opponents.
- **% even** — the **Forecast** for one player against another, one a side (opposite sides in padel),
  read by the one forecast function: it falls with the gap **and** with either level's doubt, and tops
  out at 96%. Coloured as game cards: green 70% and above, amber 55–69%, red below 55%. Nothing else
  computes it. _Avoid_: match %, compatibility, balance (for this number).
- **New in Raketa** — the players who **joined** — the profile commit that ends onboarding — in the
  **last 30 days**, strictly, unrated included, newest first. Not the **Newcomer**'s 14 days, which
  bend a level gate. _Avoid_: newcomers (the **Newcomer** term), new players (except in copy).
- **Same vibe players** — anyone sharing **at least one Social tag** with the reader, more shared tags
  first, ties to fewer tags not shared. Every tag counts the same, and skill plays no part. _Avoid_:
  similar players, interests.
- **Vibe %** — **1 − ½ⁿ** for n shared tags, rounded: 50, 75, 88, 94, 97, 98, and since a player
  may hold 8 ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §7) 99 for 7 and **100** for 8 — true, since 8 shared are both players' 8. _Avoid_: match %,
  similarity.
- **Connected** — the reader is friends with a player, or has a request to them still open. Somebody
  who asked the reader is **not** connected. **Unconnected** is neither. New in Raketa orders its 10
  by it: unconnected, then sent, then friends.
- **Good match** — at or above a row's line: **70% even** in Same competitive level, **2 shared
  tags** in Same vibe.
- **Fresh** — a **good match** the reader isn't friends with, hasn't sent a request to, and who hasn't
  **rested**; somebody who asked the reader counts. Fresh players fill a row of 10 first, best first.
- **Gap** — a place in a row of 10 left after the **fresh** ones: a friend, somebody the reader sent a
  request to, a rested player, a weaker match, best first. Every read works the row out again, so a new
  fresh match takes the weakest gap. Not the ranking's **gap line**, nor a level gap.
- **Rest** — a player **rests** in one of the reader's rows once their card has been **on screen** on
  5 different days without the reader adding them, while the pair is still unconnected. A rested
  player is a gap, never hidden. **Each row keeps its own count.** Only Same competitive level and Same
  vibe rest anybody. _Avoid_: snooze, dismiss, hide.
- **On screen** — a card at least half visible, as the phone reports it: **one count per card, row
  and Warsaw day**. Opening Home without scrolling to the row counts nothing. _Avoid_: impression,
  view.

**Invariants**
- **The rows are worked out on each read**, no nightly job. The stored copies are written only from
  the owning contexts' events, and each rebuild from the event store equals live delivery.
- **The rating owns the level, the profile the tags and the switch.** Discovery copies them and
  writes neither.
- **A block keeps a pair out of each other's people rows, and nothing else here.** The ranking, Top
  10 and group sheets show them (Blocks).
- **The rows tell nobody anything.** No push, no bell line, no email.

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
