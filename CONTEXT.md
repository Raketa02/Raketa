# Rakieta — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. All three
apps obey this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Rakieta is a racket-sport platform. Players find and book courts through the
**player app**; clubs manage those courts through the **club web app**; both are served
by one **backend** built on Clean Architecture (hexagonal ports & adapters), DDD, and
event sourcing.

> This is a living document, grown deliberately. Terms are added as decisions are
> actually resolved — not invented ahead of the code. Don't drift to synonyms it avoids.

---

## Part 1 — Implemented bounded contexts

These exist in `backend/app/` today and are the authority for their terms — except
**Matchmaking**, whose words are settled and whose code is not yet written; its section
says so at the top.

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

#### Money

The words are settled ([ADR-0023](docs/adr/0023-money-integer-grosze-gross-whole-zloty.md))
and `backend/app/kernel/money.py` implements them. No priced context exists yet, so the
module has no production caller — the rounding order and the split are correct and finished
ahead of the first club, which is the whole reason they could be built now.

- **Grosze** — the unit every price is held in. Integer, never a float, never a decimal
  string. One hundred grosze to the złoty.
- **Every price in Rakieta is gross** — VAT-inclusive, the number the player sees. `38,00 zł`
  on a card is a gross figure. VAT decomposition is an invoicing concern, never a second kind
  of money.
- **CourtPrice** — what the whole court costs for one booked block, after every multiplier has
  been applied. Always a **whole number of złoty**.
- **SeatShare** — a `CourtPrice` divided by the sport's **sold** player count. The sold format,
  not the current occupancy: a padel match with three players still divides by four, because
  the court costs what it costs.
- **Payable** — what one player actually owes: their `SeatShare` less any club card offset.
  Never negative.
- **Card offset** — a club's allowance against a seat, per sport. Either none, a capped
  amount, or the whole share.

**Invariants**
- **A court price is a whole number of złoty.** This is marketplace law, not an observation.
  It is what makes a seat share exact — a whole złoty is a multiple of 100 grosze, and both
  100 ÷ 2 and 100 ÷ 4 are integers, so a split never rounds and never loses a grosz. A club
  rate that would break it is rejected where the rate is configured.
- **The rounding order is the rule, not a detail.** Multipliers compound, then one rounding to
  whole złoty at the court, then the split. Dividing first gives a different — wrong — answer.
- **A card can never produce a credit,** only reduce a payable to zero. A 15 zł allowance
  against a 13 zł share yields a 13 zł offset.
- **A seat share is written once, when the match is created, and is never re-priced.** It is
  what makes a price guaranteeable before a court is assigned.
- **The seat, not the court, is the unit of sale**, so nobody becomes financially responsible
  for anybody else's money by joining a match.

### Matchmaking (`backend/app/engines/pairing/`, `backend/app/engines/matchfit/`)

> **Words first, code second.** The **Pairing** half is built. `app/engines/pairing/`
> holds the **Balance forecast** at either arity for a full match *and a forming one* — the
> estimate, the margin, Certainty, the split bar, Beyond scale — over the shared snapshot
> vocabulary in `app/engines/matchmaking.py`, with **Pairing** and **Team strength**: four
> players are enumerated into the three splits, each is forecast, and all three come back
> ranked. **Seat target** and **Target band** are built, so a match one seat from full says
> what Level that seat is aimed at and any match with a rated player on a seat says what
> range it is aimed at. **Roster** and **Imputed seat** are built, so a half-formed match is
> forecast rather than hidden and says how much of the answer was stood in for; the two
> states that still decline are a court nobody has joined and one where nobody seated has a
> rating at that sport, because both leave nothing for a stand-in to be drawn from.
> **Match Fit** is half built. `app/engines/matchfit/` holds the framework whole — **Term**
> in both its kinds, the renormalisation, **Coverage** as its own number, **Reason**s ranked
> by contribution and one warning — with six of its ten terms: price, travel, match type and
> ladder qualification, all reading the **Player profile**, plus group reliability and
> familiarity, which are *present and absent* so that exclusion and Coverage are exercised by
> every score rather than being untested machinery. The four still owed are named with their
> weights in the engine's own constants: skill overlap and predicted balance, time fit, and
> **Match viability** — which is the term that closes *absence never flatters* for ranking,
> because it is the only evidence term that is always computable. Until it lands, an empty
> court that satisfies every declaration still scores above a well-formed match on Fit alone,
> at a third less Coverage, and a golden persona says so. **Match viability** and **At Stake**
> are still words without code. The terms are committed ahead of them because the decisions
> behind them are
> ([ADR-0025](docs/adr/0025-binding-pairing-for-counted-matches.md),
> [ADR-0026](docs/adr/0026-matchmaking-engines-snapshot-input-contract.md),
> [ADR-0027](docs/adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md)), and because
> the engines cannot be written in vocabulary that does not exist. A **seat's state** — paid,
> held, empty — is borrowed from the commitment rules and is read by the snapshot now, spelled
> as they spell it; a match's **phase** and its **join cutoff** are still only words. All
> three will be *defined* with Matches, not here — this section reads them, it does not own
> them. **Ladder qualification** is read the same way and by nobody yet: the snapshot carries
> whether a match counts towards the current player's ladder, in three states because *not in
> a ladder* and *in a ladder this does not count for* are different facts, and whichever
> context ends up owning ladders will define the word.

Two engines, neither of them a bounded context, both pure and versioned
([ADR-0015](docs/adr/0015-engines-as-a-pure-versioned-layer.md)). **Pairing** asks whether a
match is *balanced*; **Match Fit** asks whether it is *for you*. A perfectly balanced match
forty minutes away at twice your ceiling is a good match in the abstract and a bad one for you.

- **Pairing** — which players form which team. Four players admit exactly three splits, and
  the engine searches all three; there is no heuristic and no better split it could miss.
- **Team strength** — what a pair plays like, which is **not the average of the two**. It is
  weighted toward the **weaker partner**, because the weaker side is attacked. Singles has no
  pairing, and a team of one is that player.
- **Balance forecast** — the prediction of how close a match will be, for one roster. It is
  never a bare number: it is an **estimate and a margin**, and everything the player sees —
  the percentage, the split bar, the two team strengths — is one calculation viewed
  differently, so a card cannot contradict itself.
- **Balance margin** — how wrong the forecast could be, in the same units as the forecast. It
  is what makes *"49/51"* and *"49/51, and we barely know these people"* different claims.
- **Certainty** — the forecast's grade of its own margin. A statement about the platform's
  knowledge, never about the players.
- **Beyond scale** — the gap is past the point the scale still reports usefully. The honest
  answer there is *this is a mismatch*, not a small percentage, and the two are said
  differently.
- **Roster** — the people a forecast is about: the **paid** seats, plus **you** if you could
  still join. A **held** seat contributes its player's level but not their attendance. An
  **empty** seat is imputed. You join the seat you would actually take, so the forecast
  answers *what would this match be like if I joined* rather than what it is like without
  you — and a match with no empty seat has nowhere to put you, so a full match stays
  somebody else's.
- **Imputed seat** — an empty seat stood in for by a hypothetical player drawn from the
  **target band**. It is what lets a half-formed match be forecast at all, and it is why the
  margin widens as a match gets emptier rather than the forecast disappearing. A player with
  **no rating at that sport** is imputed the same way and for the same reason: what the
  platform lacks is a level, and whether somebody is sitting on the seat is a question for
  **match viability**. Imputation stands in for gaps in a roster and never for the whole
  roster — a stand-in is drawn from the target band, and a match with nobody rated on a seat
  has no band.
- **Seat target** — the level that would make a match with **exactly one** seat open as even
  as possible. With more seats open the question is under-determined and the engine refuses it.
  In doubles *three* levels each make the match exactly even, one for each seated player the
  joiner could partner; the platform advertises the **middle** of the three, because the outer
  two ask for somebody well below or well above everybody already in the match.
- **Target band** — the level range a forming match is aimed at: the mean of the seated levels,
  widened either side. Blunt by design, needs only one seated player, and is the fallback
  whenever a seat target cannot be answered.
- **Match Fit** — how good one specific match is for one specific player, as a single
  comparable score with its reasons attached. The score does the sorting; the reasons do the
  explaining.
- **Term** — one weighted component of Match Fit, and every signal is one; there are no
  bonuses applied outside the weighting. Each term is one of exactly two kinds, and the kind
  decides what its **absence** means. It is a fact about how a term was *built* rather than a
  label on it: a constraint has no path to an exclusion and an evidence term has no field an
  optimistic default could be written into.
  - **Constraint term** — a limit the player declared (price, distance, hours, match type).
    An undeclared limit is **no limit**: the term scores full marks and nothing is missing.
    A term at **nothing** is not the same as an absent one: the platform looked and the
    answer was bad, so the weight is still in the denominator and the quantities are still
    reported. Price and distance are conditions, never rejections.
  - **Evidence term** — something the platform observes (balance, reliability, skill overlap,
    familiarity). Absent evidence is **not** a good score; the term is dropped and the
    remaining weights carry the whole score between them.
- **Coverage** — how much of Match Fit's weight was actually computed. A thin score and a
  strong score are different facts and are reported as two numbers, never blended into one.
  Measured against the weight that **exists**: a term nobody has built yet is not evidence
  the platform is missing about a match, so Coverage reports on the match and never on the
  engine's completeness.
- **Reason** — a term's contribution stated in the player's terms, ranked by how much the term
  actually contributed — weight times value — rather than by how well it scored. A **warning**
  is the *lowest* contributor, and only when its own value is bad. That asymmetry is
  deliberate: a term can be last by contribution while being perfectly fine in itself, and
  warning about that would teach players to ignore warnings.
- **At Stake** — the rating movement a win or a loss would produce, quoted **before** joining.
  Deliberately not part of Match Fit: Fit ranks, At Stake warns, and only counted matches have
  any.
- **Match viability** — how likely the match is to actually happen, as distinct from how good
  it would be. A match nobody has paid into, at a club with no court left to give, is a worse
  recommendation than an identical one that is three-quarters paid.
- **Player profile** — what the player declared about how they want to play: days, hours,
  price ceiling, distance, appetite, competitive or social, and how far ahead they will
  commit. One declaration, read by every engine that needs it, never restated as a constant
  inside one. **Every part of it is optional and absence means undeclared** — which is what
  a constraint term reads as *no limit*. Distance is declared in **minutes**, because that is
  what a card shows and comparing a radius in kilometres against it would mean inventing a
  speed. Appetite and the commitment horizon are the ranking policy's; no term reads them.

**Invariants**
- **Fit and certainty are separate variables.** The same rule the rating context holds for
  skill and confidence, for the same reason: collapsing them makes an unknown match
  indistinguishable from a good one, and the platform would then recommend most confidently
  the matches it understands least.
- **Absence never flatters.** No match may score better because the platform knows less about
  it. This is what the constraint/evidence split exists to guarantee, and it is checkable: a
  term's exclusion must never raise a score.
- **A missing declaration is not a missing measurement.** A player who set no price ceiling
  has no price problem; a match with nobody in it has no reliability *reading*. Treating those
  two silences the same way is the mistake the split is named after.
- **The split bar is a rendering of the percentage, not a second opinion about it.** One
  quantity is clamped and everything else is derived from the clamped value, so the bar and
  the number cannot saturate at different moments and disagree in the gap.
- **The estimate ranks; the card decides whether to print it.** A forecast too uncertain to
  show is still the best guess available, and withholding it from the ranking would make an
  uncertain match unrankable rather than honest.
- **A counted match's pairing is elected before commitment and fixed after.** Otherwise At
  Stake quotes a promise against teams that can silently change, and a rating moves on a
  pairing nobody agreed to. Friendlies are free to rearrange
  ([ADR-0025](docs/adr/0025-binding-pairing-for-counted-matches.md)).
- **Rating movement has exactly one owner.** What a match is worth to a rating is the rating
  context's arithmetic, and the number quoted before the match and the number applied after it
  are the same function or the quote is not a promise.
- **A score carries every engine version that produced it.** A Match Fit score has two
  producers, and attributing it to one of them cannot falsify a constant belonging to the other.
- **Ranking a list is not scoring a match.** Which matches a player is shown — the exploration,
  the diversity, the impressions an unfilled match is owed — is policy, and it lives outside
  the engines so that the engines stay pure, deterministic and reproducible
  ([ADR-0027](docs/adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md)).

---

## Part 2 — Planned bounded contexts

The racket-sport domain proper. **These are not modeled yet** — no code, no events, no
committed terms. They are listed so that work lands in the right context from the first
commit, and so nobody invents a fourth name for the same idea.

| Context | Intent | Likely home |
| --- | --- | --- |
| **Clubs** | The tenant: a venue that owns courts, staff, opening hours, pricing. | `backend/app/modules/clubs/` |
| **Courts** | The bookable resource: surface, indoor/outdoor, sport, availability rules. | `backend/app/modules/courts/` |
| **Bookings** | A player's reservation of a court for a time slot. Cancellation, no-shows, payment state. | `backend/app/modules/bookings/` |
| **Matches** | Players organising play: open matches, joining, levels, results. | `backend/app/modules/matches/` |

> **Do not treat this table as settled design.** It records intent and naming, not
> aggregates, invariants, or ownership. Before writing code in one of these, resolve
> its terms into Part 1 above and record the shape in an ADR. In particular, whether a
> given context is **event-sourced** (like `User`) or **persisted-with-events** (like
> `RefreshToken`) is a real decision with real consequences — make it deliberately, per
> context, and write it down.

Open questions that must be answered before Bookings exists — flagged here so they are
not silently assumed away:

- Is a **Booking** owned by the Court, the Club, or standing alone with references?
- Is availability a **projection** over bookings, or its own stored concept?
- What is the **tenancy spine** — `Club → Court → Booking`? Where do players attach?
- Which side owns **cancellation windows and pricing** — Club config or Booking policy?

---

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

## Terms the clients must not reinvent

Both frontends describe the same nouns. A concept that exists in this glossary keeps
its name in TypeScript: a `Court` is a `Court`, not a `Venue`, `Facility`, or `Pitch`.
Client-only *technical* vocabulary (wire type, DTO, mapper, BFF route handler, secure
store) belongs in that app's own `CONTEXT.md`, never here.

Both frontends also **render** the same values. The backend sends numbers and machine codes
and never display text ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)),
so each client formats — and both implement one table, in
[`docs/value-formatting.md`](docs/value-formatting.md). That is not a design system and holds
no colour or size; it is the exact string a price, a level, a time or a duration becomes, so
the two apps cannot drift into rendering `38.00 zł` and `38,00 zł` for one booking. **Copy is
not formatting**: the sentence behind an unavailability code is each app's own.
