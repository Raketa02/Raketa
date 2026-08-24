# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. All three
apps obey this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Raketa is a racket-sport platform. Players find and book courts through the
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
- **Every price in Raketa is gross** — VAT-inclusive, the number the player sees. `38,00 zł`
  on a card is a gross figure. VAT decomposition is an invoicing concern, never a second kind
  of money.
- **CourtPrice** — what the whole court costs for one booked block, after every multiplier has
  been applied. Always a **whole number of złoty**.
- **SeatShare** — a `CourtPrice` divided by the sport's **sold** player count. The sold format,
  not the current occupancy: a padel match with three players still divides by four, because
  the court costs what it costs. **Written when the match is made and never re-priced**: a club
  may discount a **court** and may never price a **seat**, and a discount published afterwards
  reaches the matches created after it and no others
  ([ADR-0080](docs/adr/0080-a-payable-is-a-share-and-the-card-ships-supplying-nothing.md)). So two
  matches on one court the same afternoon may carry different shares, and each is what its own
  players paid.
- **Payable** — what one player actually owes: their `SeatShare` less any club card offset.
  Never negative. **In v1 it is always equal to the `SeatShare`**, because nothing supplies a
  card ([ADR-0080](docs/adr/0080-a-payable-is-a-share-and-the-card-ships-supplying-nothing.md)).
  The two stay separate names because they are separate kinds of fact — a share is a property of
  the **match**, a payable of a **player against** it — and only one of them crosses the wire.
- **Card offset** — a club's allowance against a seat, per sport. Either none, a capped
  amount, or the whole share. **Ships with nothing supplying it**: the rule reads the club's half
  of a MultiSport card and never asks whether the player holds one, so v1 passes it no card at
  all. The kernel keeps the rule; no screen ever prints a reduced price.

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
> **Match Fit** is built, all ten terms of it. `app/engines/matchfit/` holds the framework
> whole — **Term** in both its kinds, the renormalisation, **Coverage** as its own number,
> **Reason**s ranked by contribution and one warning — and the table now sums to a hundred
> with nothing pending: **skill overlap** and **predicted balance**, which read the pairing
> analysis; **time fit**, price, travel, match type and ladder qualification, all reading the
> **Player profile**; **match viability**; and group reliability and familiarity, which are
> *present and absent* so that exclusion and Coverage are exercised by every score rather than
> being untested machinery. Time fit is the term the source design named and never computed: a
> match's start is read against the days and hours the player declared, through the club's zone
> and the kernel's coordinates, and a match outside them ranks lower without being hidden.
> **Match viability closes *absence never flatters* for a ranking**, which the mechanism alone
> could not: it is the only evidence term that is *always* computable, so a court nobody has
> joined is scored on being empty rather than excused from it, and an empty match that is
> counted, cheap and nearby now scores 88 against a well-formed match's 97 where it used to
> score 100 against 94. **Skill overlap and predicted balance did not widen that gap and could
> not have**, which is worth knowing rather than guessing at: both are evidence an empty court
> has none of, so both are excluded for it, and an excluded term cannot lower a score it is not
> in. What they widen is Coverage — 48% for the empty court against the well-formed match's
> 100% — which is the pair saying that less than half of the empty court's score was measured
> at all. Only a term that *cannot go missing* can close an ordering regression.
> **At Stake** is still a word without code. The terms are committed ahead of them because the
> decisions behind them are
> ([ADR-0025](docs/adr/0025-binding-pairing-for-counted-matches.md),
> [ADR-0026](docs/adr/0026-matchmaking-engines-snapshot-input-contract.md),
> [ADR-0027](docs/adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md)), and because
> the engines cannot be written in vocabulary that does not exist. A **seat's state** — paid,
> held, empty — is borrowed from the commitment rules and is read by the snapshot now, spelled
> as they spell it, and so are a match's **phase**, its **court hold** and its **join
> cutoff** — all four read by the snapshot now. They will be *defined* with Matches and
> Courts, not here: this section reads them, it does not own them. **The phase is defined**
> now — [ADR-0040](docs/adr/0040-one-ladder-resolves-a-situation.md) makes it a *projection*
> off a match's **Situation**, with the same three members; see the Matches block in Part 2.
> The other three are still borrowed. The phase is the one this
> section reads and never *scores*, because whether a match can be joined at all is a hard
> filter and not a low number. **Ladder qualification** is read the same way and by nobody yet: the snapshot carries
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
    reported. Price and distance are conditions, never rejections. **An undeclared limit and
    an unmeasurable match are two different absences**: the first is *no limit* and scores
    full marks, while a limit the platform cannot compare against anything — a Travel radius
    with no Distance anchor to measure from — is **dropped like missing evidence**, so its
    weight leaves the denominator and Coverage reports the shortfall. The term does not change
    kind; the rule about absence is about the player's side of the comparison, and this is the
    other side missing. **A declared limit is three-valued in the record and two-valued in the
    snapshot** — `undeclared | none | <value>`. *Declined* and *undeclared* score **identically**
    (both *no limit*, full marks, weight kept), so the snapshot collapses them; only the
    Declaration meter can tell them apart, which is what lets a player who genuinely has no
    ceiling be finished rather than permanently incomplete.
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
  recommendation than an identical one that is three-quarters paid. It is **evidence and yet
  never absent**: every match has a phase, a court hold, a seat count and a join cutoff, so it
  is the one term that can never be excluded — which is what makes *absence never flatters*
  true of a ranking and not only of the mechanism. It is a **probability**, and the platform
  is right or wrong about it in a way that can be counted: the share of joined matches that
  were actually played, by viability decile. A **hard** court hold retires the club's crowding
  entirely, because a court that has been booked cannot be taken by the club being busy; and
  an unpaid seat is worth less the closer the **join cutoff** gets, on a slope rather than at
  a cliff, because there is less time left for anybody to take it.
- **Skill overlap** — how close the player's own level is to the level the match is aimed at.
  The largest term in Match Fit, and **evidence**: with nobody seated there is nothing to
  overlap with, so it is excluded rather than scored against the player's own level — which
  is a distance of zero and therefore full marks, and is most of why the source design ranked
  an empty match above a well-formed one. A player the platform has never rated *at this
  sport* is the same silence from the other side and gets the same answer. The target is the
  **Seat target** where the match is one seat from full and the **Target band**'s midpoint
  otherwise, and the term never re-derives which: it reads whichever answer the pairing
  analysis gave. It decays over **a full band** — the widest plain-language band the rating
  context prints — and is **symmetric**, because a level too strong for a match and a level
  too weak are both *not the match you belong in*; which of the two it was is reported, and
  is not encoded in the score.
- **Predicted balance** — how even the match is forecast to be, read straight off the
  **Balance forecast**'s estimate. The one term with no constant of its own: a balance
  percentage is already a mark out of a hundred about the match, and fitting a curve to it
  would be a second opinion about what one means. It reads the **point estimate even when the
  margin is too wide to print**, because the best estimate remains the best estimate when it
  is unfit to show — *suppression is presentation, not ranking* — and it is excluded only when
  there is **no forecast at all**, never when there is merely an uncertain one. Uncertainty is
  not charged twice: the estimate is the *expected* gap, so it has already been made worse on
  the way in.
- **Player profile** — what the player declared about how they want to play: days, hours,
  price ceiling, distance, appetite, competitive or social, and how far ahead they will
  commit. **One declaration per sport the player picked** — a padel player's hours and price
  are not a tennis player's, and every surface that shows the profile is already filtered to
  one sport, so the eight are never averaged across sports. Read by every engine that needs
  it, never restated as a constant inside one. **One set, two readers**: Raketa's own ranking
  reads it unconditionally, and the club console's intent pool reads it only behind the
  Proposals opt-in. **Every part of it is optional, and every part can be explicitly
  declined** — absence means undeclared, which is what a constraint term reads as *no limit*,
  and a decline reads the same way to every engine while counting as an answer on the
  Declaration meter. Where a blank would make the platform **assume** rather than drop a
  limit — appetite and the commitment horizon — declining tells it to stop assuming. Days and
  hours are two declarations rather than one, so a player who named days and no hours has no
  hour problem. Distance is declared in
  **kilometres**, as a **Travel radius** around a **Distance anchor** the player named, and is
  compared against a club's distance in kilometres — never against a time, because that
  mixture is what would mean inventing a speed. **Days and hours are a clock face and never an
  instant**:
  *"I play after work"* is a claim about the wall in the club, so a match's start is compared
  against them in the club's own zone. A declared stretch of a day runs forwards, never wraps
  midnight — 22:00 to 01:00 is two declarations — and **excludes its end**, so two stretches
  declared back to back do not overlap. A match is inside a declared stretch when it
  **starts** inside it, however long it runs. Appetite and the commitment horizon are the
  ranking policy's; no term reads them.
- **Where you play** — the **city and country** a player declared, and the only part of their
  location any other player may see. **Compulsory and asked outside the Player profile**: it
  is which market they are in, not a preference, and no feed can be composed without it. It is
  what the Now header prints. A player who moves declares the move; it is never observed, and
  it is a field from the first day even while there is one market.
- **Distance anchor** — the finer place a player named — an **area** or a **postcode** — and
  the only thing a distance is ever measured from. Optional, part of the Player profile, and
  **never shown to another player**. A declaration about *where they play from*, never an
  observation of where they are: a phone at a desk on Monday morning is precise about the
  wrong moment. **Precision follows the anchor** — with only a city there is no distance at
  all, and with an area or a postcode a distance is rounded to the kilometre and marked
  approximate, never carrying a decimal a district's width cannot support.
- **Travel radius** — how far a player said they will travel from their Distance anchor, in
  kilometres. **It orders and never excludes** on any surface the platform composed — the
  home list, and the order a free seat is offered in. A radius the player types into a
  **search** is the one place it bounds, because narrowing is what they asked for there.
  `anywhere` is a real answer and means no limit.
- **Proposals opt-in** — the player's permission for the **club console's intent pool** to read
  their Player profile and name them. **Not a declaration and never part of the Declaration
  meter**: a completeness ring that rises when you consent is a ring that pays you to consent.
  Asked once, on its own screen, with a table of what changes either way; **skipping is not
  consent**, and an unanswered question resolves to off. Off, the player is still counted
  anonymously in a club's demand and can never be named or contacted.
- **Declaration meter** — how much of the Player profile a player has settled, for **one sport**.
  Its denominator is the **eight** declarations the profile step asks — never the compulsory
  sport, never the derived Level band, never the Proposals opt-in — and it counts a field
  **answered or explicitly declined**, which is what makes 100 % reachable by a player who
  genuinely has no limits. It is never averaged across sports. It is shown on **You**, one per
  declared sport, and **never on Now**: the home screen states what a shelf is missing to order
  well, or it says nothing.
- **A sport a player plays** — a sport a **Skill rating exists** for, and nothing else. There
  is no stored list of chosen sports: onboarding's sports picker orders that run's assessments
  and its selection is discarded, so "which sports does this player play" is the same question
  as "for which sports does a rating exist" — the reading the *Skill rating* invariants already
  require. It follows that the set is **ordered only by when each rating came to exist**, and
  that a player acquires a sport by being rated at it, never by naming it.

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

The racket-sport domain proper. **All five are now modeled** — Clubs, Courts, Bookings,
Matches and Money all have code, and their terms have moved into Part 1 of
[`backend/CONTEXT.md`](backend/CONTEXT.md) as they landed. What stays listed here is the
*domain* language they share; the section headings still say *committed ahead of the code*
where that was true when they were written, and each now names what the code answered.

| Context | Intent | Likely home |
| --- | --- | --- |
| **Clubs** | The tenant: a venue that owns courts, staff, opening hours, pricing. | `backend/app/modules/clubs/` |
| **Courts** | The bookable resource: surface, indoor/outdoor, sport, availability rules. | `backend/app/modules/courts/` |
| **Bookings** | A player's reservation of a court for a time slot. Cancellation, no-shows, payment state. | `backend/app/modules/courts/` — **built together with Courts**, see below |
| **Matches** | Players organising play: open matches, joining, levels, results. | `backend/app/modules/matches/` |
| **Money** | Every złoty that moves: who paid, who was paid, why, and what a player owes. | `backend/app/modules/money/` |

**The Courts row's *indoor/outdoor* is now the Clubs row's**, and that is the second departure
from the table. ADR-0079 put the court catalogue in Clubs and
[ADR-0090](docs/adr/0090-a-category-names-its-roof-and-a-court-that-gains-one-moves-category.md)
put the roof on a **category**, which is where the catalogue lives; `backend/app/modules/courts/`
owns reservations and nothing about what a court *is*. The table describes intent from before
the code, and this row is corrected rather than followed.

**Bookings shares a module with Courts**, which is a departure from the row above and is
recorded rather than left to be noticed. A Booking has one field the Reservation does not
imply — the price the buyer was quoted — and is otherwise defined entirely in terms of the
claim it holds; the two are written in **one transaction** by
[ADR-0035](docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md), which makes them
one consistency boundary in the write path. It stays cheap to reverse: `Booking` imports
nothing from `Reservation`, so splitting it out is a file move rather than a redesign.

> **Do not treat this table as settled design.** It records intent and naming, not
> aggregates, invariants, or ownership. Before writing code in one of these, resolve
> its terms into Part 1 above and record the shape in an ADR. In particular, whether a
> given context is **event-sourced** (like `User`) or **persisted-with-events** (like
> `RefreshToken`) is a real decision with real consequences — make it deliberately, per
> context, and write it down.

Open questions that must be answered before Bookings exists — flagged here so they are
not silently assumed away:

- ~~Is a **Booking** owned by the Court, the Club, or standing alone with references?~~
  **Answered by [ADR-0035](docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md):
  none of the three — a Booking *holds* a Reservation.**
- ~~Is availability a **projection** over bookings, or its own stored concept?~~
  **Answered by [ADR-0035](docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md):
  a projection over reservations, never a stored number.**
- ~~What is the **tenancy spine** — `Club → Court → Booking`?~~ **Answered by
  [ADR-0035](docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md): `Club → Court`,
  with a Reservation referencing a court and held by exactly one holder.** Where players
  attach is still open.
- ~~Which side owns **cancellation windows and pricing** — Club config or Booking policy?~~
  **Answered by [ADR-0078](docs/adr/0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md):
  the club, and they are two different kinds of club fact.** The cancellation window is
  `freeCancelHours`, one of the eight versioned policy fields; pricing (`pm`, `cardOffset[sport]`)
  is on the club record and is **not** versioned, because a price that must hold as quoted is
  copied onto the match at booking
  ([ADR-0077](docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md)) and
  nothing ever asks what it used to be.

Whether each context is **event-sourced** or **persisted-with-events** is answered for
Matches and Courts by
[ADR-0034](docs/adr/0034-matches-is-a-record-and-keeps-no-history.md): both are records
with a version and an outbox, and **no aggregate in either keeps event history**. **Money is
answered the other way** by
[ADR-0055](docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md) — event-sourced,
one stream per player — which is the mirror of ADR-0034's reasoning rather than an exception to
it: Matches stores almost nothing and derives the rest, Money derives nothing and stores only
what happened. **Clubs is answered a third way** by
[ADR-0077](docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md): a
record, like Matches and Courts — but three named facts on it are **never overwritten**, because
a change to one of them retroactively alters an outcome that no other record explains. **All five
contexts have now made ADR-0002's choice, and no two of them inherited it.**

### Clubs — terms committed ahead of the code

Committed by [ADR-0077](docs/adr/0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md)
and [ADR-0078](docs/adr/0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md).
There is no Clubs code at all yet; these names exist first.

- **Club policy** — **exactly eight fields**, and the test for membership is one sentence: *a club
  decision that changes what happens to a player inside a match.* `window`, `joinCut`,
  `maxHoldAge`, `probHold`, `rebookingCredit`, `freeCancelHours`, `turnaroundMin`, `countsCash`.
  Everything else a club declares is the **club record** and is not versioned. **A policy is
  changed as a whole, never a field at a time** — *what this club's policy was on Friday at 16:00*
  is one question with one answer, and it stays answerable, because a change opens a new policy and
  closes the old one rather than overwriting it.
- **Speculative holding is opt-out-able, and saying so is a value.** `maxHoldAge` is `null` (never
  stale), a positive number of hours (honoured, with no platform floor), or **`0` — this club does
  not hold a court speculatively at all**. There is no floor because Raketa cannot compel a club to
  lend inventory to a match that may never form.
- **Rebooking credit** — whether a club credits a committed-but-short match at the certainty
  checkpoint. One boolean, named for the sentence the player is shown. It decides whether the
  checkpoint cancels; what the credit *is* belongs to Money
  ([ADR-0058](docs/adr/0058-one-balance-and-it-never-goes-above-zero.md): a club card entry, never
  platform credit).
- **Turnaround** — minutes a club needs between reservations. It **widens the claimed interval** of
  a reservation Raketa creates; it is never a second concept checked beside the overlap rule, and
  the player is always shown the **played** interval.
- **Counter cash** — whether a club takes cash at its counter. Distinct from **whether Raketa
  offers** *pay at the club*, which is gated on a surface existing that can mark a share paid
  ([ADR-0059](docs/adr/0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md)). Two
  facts, because a default can be overridden into the failure and a gate cannot.
- **Card offset** — a club's standing per-sport allowance against a seat. **Pricing, not policy**,
  and **not the same thing as a club card that receives a credit** — that is a Money record, per
  player per club.
- **A club carries an address, a geocoded point and an IANA timezone.** The point is what a
  distance is measured to; `km` is derived at read time, never stored. Unlike a player's anchor
  ([ADR-0063](docs/adr/0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md)),
  a club has no reason for imprecision — it is a public venue with a front door. The **zone** is a
  field from day one rather than a constant, for ADR-0063's reason: nothing downstream may assume
  one market.
- **Raketa ops authors all of it in v1.** There is no console and no role concept on `User`, so
  every history entry reads *changed by: system*. The console takes authorship later and nothing in
  the model changes when it does.
- **Payout destination** — where a club is paid. Its own history, kept apart from the policy's,
  because ops tuning a hold cap and finance changing a bank account are different acts with
  different audiences.
- **Court catalogue** — which courts a club has and what category each is in. **A court is
  retired, never deleted**: availability is a question asked of reservations, and a court that
  vanished would make *nothing was free* unexplainable on the one day it mattered.
- **A club's policy is always read as it is now.** Nothing in the domain asks what it used to
  be; that question is a human's, asked after something went wrong. A value that must hold
  steady for a match already booked is copied onto the match instead.

**A club is only ever a payee, never a payer** — that rule belongs to Money and is unchanged
here ([ADR-0045](docs/adr/0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)).

### Courts and Bookings

Committed by [ADR-0035](docs/adr/0035-a-reservation-claims-a-court-over-an-interval.md), and
**built**: `backend/app/modules/courts/`. The exclusion constraint is real
(`ex_reservations_no_overlapping_claim`), availability is a query, and a court's booking
history is a query over reservations — see `backend/CONTEXT.md` for the technical terms the
implementation added.

- **Reservation** — one court, one time range, claimed. **The only thing that can make a court
  unavailable.** Two reservations may never overlap on one court; that is the rule, and it is
  about a *time range*, never a slot's start.
- **Booking** — a player buying a court outright. A Booking **holds** a Reservation; it is not
  one. On the private split-share path a Booking exists before any share is paid.
- **Court hold** — a match's *speculative* Reservation, granted by the hold ladder and
  withdrawn when the ladder is no longer satisfied. Nobody has bought anything.
- **Category** — what is bought and priced. **The court is assigned, never chosen**, and may be
  swapped for another of the same category until shortly before play; only then is a specific
  court named to the player. This is what lets a seat price be quoted before a court exists and
  stay fixed when one is assigned. **The club authors it**
  ([ADR-0079](docs/adr/0079-a-category-is-club-authored-and-it-is-the-priced-unit.md)): a category
  is a **club-scoped named group of courts**, constrained by the platform to exactly one sport,
  because interchangeability is a fact only the venue knows. **The price attaches to the category,
  never to a court** — a court that costs differently *is* a different category — and a category,
  like a court, is **retired, never deleted**. Categories are never compared across clubs.
- **Cover** — whether a court has a roof: **indoor** or **outdoor**, and there is no third value.
  It is a fact about the **category**, which is the second and last thing the platform constrains
  about one ([ADR-0090](docs/adr/0090-a-category-names-its-roof-and-a-court-that-gains-one-moves-category.md)) —
  a category spanning two roofs makes a card lie, exactly as one spanning two sports makes a
  seat share undefined, and a player swapped onto the other court in November has been sold
  something else. It is not on a court, because no court is named until shortly before play and
  a card is composed days earlier. **A roof is *indoor***: the question the card answers is
  *will I be rained on*, and a canopy answers it the way a wall does. **A category's cover never
  changes** — a club that roofs a court has changed the court, so the **court moves category**,
  and the court's own catalogue history is what records that it did.

**The private path starts with a Reservation and looks for players; the open path starts with
players and looks for a Reservation.** That is the whole of the difference between the two
match kinds, and it is why the private path has no commitment deadline
([ADR-0030](docs/adr/0030-a-departure-is-an-audience-not-a-state.md)).

### Matches — the vocabulary the aggregate was built with

**Matches is modeled** (`backend/app/modules/matches/`): one `Match` aggregate, a record with
a version and an outbox, no event history, and every change announced under its own name
([ADR-0034](docs/adr/0034-matches-is-a-record-and-keeps-no-history.md)). These terms were
committed ahead of the code and the code was built with them rather than around them; the
backend's own technical vocabulary for the aggregate — the five kinds, the policy snapshot,
the announcement obligation — is in
[`backend/CONTEXT.md`](backend/CONTEXT.md). What is **not** built yet is named where it is
named: **seat claims** (`#68`). The **hold ladder** that grants and reclaims a court is built
(`#71`): it runs inside the write that moved the match, and `heldSince` outlives the reclaim
that ends it ([ADR-0089](docs/adr/0089-held-since-outlives-the-reclaim-that-ends-it.md)). The
**timekeeper** is built (`#72`): the schedule is a column and a wake is a look. The
**departure record** is built (`#67`): a leaving writes a vacancy *and* a departure, a filler
closes the oldest **hole** while settling the oldest unsettled **departure**, and an outcome
has no way down.

Committed by [ADR-0030](docs/adr/0030-a-departure-is-an-audience-not-a-state.md),
[ADR-0031](docs/adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md),
[ADR-0032](docs/adr/0032-order-is-a-property-of-the-composed-screen.md),
[ADR-0033](docs/adr/0033-settlement-and-occupancy-are-independent.md),
[ADR-0034](docs/adr/0034-matches-is-a-record-and-keeps-no-history.md),
[ADR-0040](docs/adr/0040-one-ladder-resolves-a-situation.md) and
[ADR-0041](docs/adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md).

- **Paid · held · empty** — the three states of a seat, spelled as the commitment rules and
  `backend/app/engines/matchmaking.py` already spell them. **Held** means a name on a seat and
  no money — an invitation not yet paid — and **a held seat never holds a court**. Joining an
  open match means paying: there is no window in which a seat is taken and unpaid by the
  taker. *That sentence is why a payment window is a **seat claim** on the right to buy a seat,
  and never a fourth state of one*
  ([ADR-0081](docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)).
- **Announcement** — the named, specific record that one thing changed, published once through
  the outbox. Caches, refunds, notifications and the player's support timeline are all built
  from announcements and never written alongside them. **Every change a support agent would
  need to explain to a player is announced as its own named event**, never as a generic
  "match updated"
  ([ADR-0034](docs/adr/0034-matches-is-a-record-and-keeps-no-history.md)).

- **Departure** — a player vacating a seat they hold. It records the seat, the player, the time,
  **the amount they paid**, and its outcome. A departure is a record in its own right, not a flag
  on a seat.
- **Vacancy** — the unfilled seat a departure leaves, and the thing the rescue cascade works. A
  departure always exists; a vacancy exists only while the seat is unfilled — so a gifted seat
  creates a departure and no vacancy at all. **Two players leaving produce two departures and two
  vacancies**, which is the distinction a single scalar could not express. A vacancy's existence
  and its departure's **settlement** are independent facts and neither implies the other
  ([ADR-0033](docs/adr/0033-settlement-and-occupancy-are-independent.md)): the resolution ladder
  reads vacancy existence, the leaver's card reads settlement, and a filler closes the oldest
  **open vacancy** while settling the oldest **unsettled departure** — not always the same one.
- **Seat claim** — the exclusive right to buy **one** seat, held by one player for **five minutes**
  while they pay. Its own short-lived record — match, seat, player, expiry — and **never a state of
  a seat**: the seat stays `empty` throughout, absent from the fill count, holding no court, and
  imputed by the forecast rather than lending the claimant's level to it. *Deliberately not called
  a **lock** or a **hold**: both are taken, by the moment a private court stops being cancellable
  and by an unpaid invitation — and **claim** alone is half of the assessment's
  claim/demonstration pair, so the term is compounded the way **court hold** is.* Taking any seat opens one — offered or found — and a
  player may hold **one at a time**, may not re-claim the same seat for thirty seconds after
  lapsing, and is charged nothing else for a lapse. A running claim is honoured past the **join
  cutoff**; none may be started after it. While one runs, the vacancy's pending sends go quiet, and
  a lapse resumes them without telling anybody twice. It ends the same way whatever ended it — the
  five minutes, the player, or the match dying underneath them — and money that arrives afterwards
  is refunded under the cause `claimLapsed` — **recorded and reversed in one write**, so the
  ledger never says we kept her money
  ([ADR-0081](docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)). *Built (`#68`), and one
  word of it is worth reading twice: **live** is composed rather than stored — unended and not
  yet expired — so a claim is over at its own instant whether or not anything has written the
  receipt. Abandonment has no v1 surface (`#89` removes the exit control from a card under a
  live claim), so the player's own ending is not built; the other two are.*
- **Seat offer** — a vacancy put to the players the **invitation ladder** picks, with a clock on
  it. The thing the rescue cascade produces once it has searched; a vacancy exists without one.
  **One kind: the open call** ([ADR-0061](docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md),
  amending [ADR-0052](docs/adr/0052-a-vacancy-is-offered-not-announced.md)).
- **Open call** — a seat offer that reserves nothing and is a race: *a seat just opened, first to
  take it*. The **only** kind. **First to accept wins**, and accepting **locks** the seat for a
  short payment window during which the card disappears for everybody else — returning if the
  payment lapses. *The wording is the discipline: a card that never claimed to be exclusive can
  never be caught lying when the seat goes to somebody else.*
- **Exclusive offer** — a seat genuinely reserved for one named player while their clock runs.
  **Refused for v1** and named only so it is not reinvented: it needs a hold, a clock per
  candidate, a per-player cap and a backstop, where an open call keeps every piece of state on
  the **vacancy**. What buys it back is volume, not a change of mind.
- **Invitation ladder** — the **order** in which a vacancy's eligible players are ranked: seven
  rungs, standby first, fit-ordered within a rung. It is an ordering, not a queue — at launch
  volume rung 1 is told immediately and every other rung ten minutes later, and rungs whose
  feature does not exist yet are simply **empty**
  ([ADR-0061](docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md)). A player is
  never offered a seat in a sport they hold **no rating** in, and the match's **level band** is a
  wall: reaching outside it changes the game the players who stayed bought, and needs their
  unanimous consent.
- **Standing rule** — a player's declared conditions — sport, days, price, travel — that
  **auto-join them to every matching standby list**. Not a notification setting and not a second
  way into a vacancy: it is a machine that feeds **standby**, which is why it needs no consent
  path of its own. Not built.
- **Withdrawal** *(of an offer)* — an offer ending because the seat went elsewhere. **Silent**:
  the card disappears and nothing is sent to say so. *Never called an **expiry** — an offer
  expires when the vacancy's own clock runs out, which is a different fact.* A notification
  already **delivered** is **left alone** — no platform can remove one, and the past-tense
  wording means it never claimed anything that could go stale
  ([ADR-0062](docs/adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)). So telling
  everyone at once leaves one stale notification per person told, and it costs nothing.
- **Prompt to look** — what a notification is. It carries **no truth**: a tap re-reads the
  match's live state, and **Now** is the only surface that states what is currently the case.
  The distinction is why a lock screen can never break the rule that a gone seat must not look
  available — it is never allowed to say a seat *is* there, only that one *opened*
  ([ADR-0062](docs/adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)).
- **Standby** — the players who asked to be told if a seat frees on a particular match. It confers
  **priority, not a place**: the cascade offers to standby before anybody else, and orders within
  standby by fit, so a standby **position** is not a fact the platform will show — it can rise.
  A place is a **membership of a pair**, so asking twice is asking once and leaving is idempotent;
  it is the **fourth membership** that puts a match on the enrolled strip, and the only one that
  confers nothing. **Nothing joins a queue in v1** — the waitlist toggle was a match-screen control
  and that screen is out of scope — so a standby place arrives from seed, or from the standing rule
  when one is built.
  Priority is what standby **is**: told in the same breath as strangers, joining a list would buy
  nothing. The third thing it buys is **loudness**: a standby seat is the only message
  allowed to pierce a Focus, and on iOS it does
  ([ADR-0065](docs/adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)).
- **The line** — the **one live message** a player's lock screen holds from us, ever, and the
  thing a **named seat** is named on. A new seat's message *takes the previous one's place*
  rather than stacking beside it, and with no frequency cap in v1 that replacement **is** the
  frequency control. It belongs to **offers**: *one live message per player* was earned as a
  frequency control on seats rather than as a claim on her lock screen forever, so any future
  kind of message stacks beside it rather than evicting a live seat
  ([ADR-0062](docs/adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md),
  [ADR-0065](docs/adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)).
- **Named seat** — the one seat a lock-screen line actually names when several are live; the rest
  are a count. Which one is **ranked over the whole live set every time we send** — a seat the
  player asked for over one we chose, soonest-to-expire inside each group — so a lesser seat can
  never take the line from a better one. It is also the **send condition**: a message goes out when
  the named seat *changes*, and a change in the count alone is not worth an interruption
  ([ADR-0065](docs/adr/0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)).
- **Leaver** — the player who made a departure. Not a state: a leaver sees the match's own state
  rendered for somebody who used to hold a seat. Her card **keeps the match's own facts**,
  because whether her money comes back depends entirely on her seat refilling — a card that hid
  the match's progress would hide the only thing that decides her outcome — and her departure
  rides beside the situation in **two payload forms**, *she paid and it may come back* and
  *nothing was taken*, never one payload holding an amount that is sometimes absent.
- **Audience** — who a card is rendered *for*. Three, and only three: a player **in** the match, a
  player **looking in**, and a **leaver**. An audience changes a card's words and which money it
  names; it never changes the **situation**, and it never changes a movement's **cause**. One
  money line has **no audience at all**: `{price} settled to the club` names the **court's**
  total for everybody, because its subject is the court and what it tells the viewer is *this
  game is happening* — her own share answers a question she did not ask, and answers it worse,
  since her money left days ago
  ([ADR-0072](docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md)).
- **Outcome** — a departure's settled result: *reversed*, *refunded in full*, *refunded half*, or
  *forfeited*. On a private court only *refunded in full* and *forfeited* are reachable. **Absent
  until it settles** — *not yet decided* is a state a card renders and never a blank — and a
  leaver who put nothing in is *reversed* from the moment she leaves, because there is no money
  whose fate could still change.
- **Settlement** — the moment no further **seat** event can change an outcome. Monotonic upward
  thereafter: a club-side failure may improve a settled outcome, nothing may reduce one. A
  departure may be **born settled** — a pre-commitment reversal, a transfer, a gift — and still
  leave a vacancy behind it. Where nobody fills the seat, it lands at the **start**: that is the
  last instant a seat can move at all, and ADR-0030's own illustration — the join cutoff —
  stopped being that when [ADR-0081](docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)
  made a running seat claim outlive it.
- **Quote** — the outcome **label** a player was shown before they chose to leave, carried on the
  leave command. If the outcome recomputed at apply time is strictly worse than the quote, the
  command is refused and the player is re-presented. The ordering is *refunded in full* >
  *refunded half* > *forfeited* = *nothing returned*; forfeit ranks **equal** to a zero refund,
  because the quote protects money and the money is identical. **It quotes the one outcome shown as
  live, never the set of possibilities** — *reversed* before commitment, *refunded in full* while
  the full-price search runs, *refunded half* once Rescue has opened. The other outcomes are shown
  beside it as possibilities and are not quoted, because the ordering above is defined over single
  labels ([ADR-0086](docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
- **Outcome standing** — where each of a departure's four outcomes stands for one player at one
  instant: **searching** (the outcome leaving now is quoted at, and the price the cascade goes
  looking at), **opens** (it becomes the quote at a moment already fixed, and the row carries the
  moment), **still possible** (reachable, with no moment to name), **spent** (behind her, and it
  cannot happen again whatever the match does). The departure screen prints **all four always** —
  *"a table that quietly drops forfeited once it is unreachable is also a table that never showed
  it while it was"* — and two on a private court, where only two are reachable. Composed by the
  server; the phone derives none of it, and there is deliberately **no phase name** beside them,
  because the standings already answer the question a phase would
  ([ADR-0086](docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
- **Still possible, against opens** — the distinction the standings turn on. Commitment is an
  **event and never a clock**: a match past its own deadline and still short has bought nothing, so
  on a match that has not filled the three money outcomes are a *fill* away rather than a moment
  away, and naming a moment there would promise a turn that may never come.
- **The private-court lock** — once a **converted** court is **full** and past the club's
  cancellation deadline, nobody may leave and no refunds are issued: a stranger joining is buying a
  court that definitely exists, which an open match cannot sell, and that is what makes the
  commitment fair ([ADR-0046](docs/adr/0046-one-reconciliation-two-hours-after-the-reservation-ends.md)).
  It is the club's **own** window and not the platform's commitment backstop, which is a rule about
  an open match and would close the lock early.
- **Now's update** — what an action off Now hands back so the screen corrects itself off the
  player's own tap: **the one card that changed**, plus any of the two viewer-owned regions whose
  contents or order changed, whole. The shelves are never in it. A departure returns the card
  *changed, in place* — same match, same region, new rendering — which is the product's **first
  mid-session audience change**, and the reason no client may cache a card keyed on the audience
  that composed it. It has **two forms**, and the second is *this card is gone*: leaving standby
  removes a card, because a queue place is the whole of what put that match on the strip
  ([ADR-0091](docs/adr/0091-a-queue-place-is-a-card-and-leaving-one-is-the-first-card-that-goes.md)).
  A discriminated union rather than a card that may be missing — *it is gone* and *this build sent
  none* are opposite sentences. **The region half arrived with taking a seat**, which is the first
  act that moves a card *between* two regions — the offer is gone and the match belongs in the
  strip — and both come back **whole** rather than as a list of removals, which the phone would
  have to interpret. They ride only on the answer that can move one, and only when the tap
  applied: a refusal moved nothing, and leaving the corrected card exactly where it is is what
  lets the client draw its own line over a seat that has gone.
- **Invitation ladder** — the order a freed seat is offered in: **seven rungs**, fit-ordered
  within a rung, over one eligible pool
  ([ADR-0061](docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md)). The **rung
  dominates the fit**, and that is what standby is worth: told in the same instant as strangers,
  joining a waitlist buys nothing. Three rungs ship **dark** — a standing-rules feature, a
  *recently viewed* signal and an availability calendar, none of which exists — and a dark rung
  is declared and empty rather than renumbered away, so a rung turns on when its feature ships
  and adding one is a re-sort rather than a new stage.
- **Open call** — the one mode a vacancy is offered in. There is no exclusive offer, no hold, no
  cap of three and no twelve-hour backstop; everyone eligible is told in the **race wording** — *a
  seat just opened, first to take it* — so no card ever claimed to be exclusive and none has to be
  retracted into a lie. What is left of exclusivity is the **seat claim**, which is five minutes
  of the right to buy and belongs to the money chain
  ([ADR-0081](docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)).
- **Level band** — the range a forming match is aimed at: the **mean of the seated Levels**
  either side of one constant half-width. It is *the band the players who stayed signed up for*,
  and it is a **hard wall** on the cascade — reaching outside it takes unanimous consent from
  those players and does not ship. Derived from the roster and never stored, so it moves when the
  seats do; a match with no seated Level has **no band**, which is not a band nobody clears.
- **Offer** — a seat put in front of one player, at one instant, at the price she would have paid
  then. A **fact about the past and never a state**: nothing is withdrawn and nothing is deleted,
  because the wording is what keeps a taken seat honest and nothing is ever removed from a lock
  screen ([ADR-0062](docs/adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)). Whether
  the seat is still there is a question about the **match**, asked live.
- **Offers region** — the region **above everything** on Now: seats put in front of this viewer,
  **soonest-to-expire first**, with no floor, no cap and no caption. *The thing with a clock is
  first.* What expires is the **seat** and not the offer — the open call has no clock of its own —
  so the moment is the **join cutoff**, which is the one instant a claim may still be started at.
  Ordering by the hour of the game would sort her chances by when the evening is rather than by
  when they die.
- **Taking a seat** — the act an offer card names, and what it opens is the **seat claim** rather
  than the seat. Anybody may take any free seat: an offered seat and one she found herself are the
  same race when it is the last one, and *offered seats behave differently* is a rule nobody would
  remember. A player who is **not fastest finds out from the screen** — the card comes back
  corrected, saying the seat is gone, rather than an error saying so — and the two refusals that
  answer differently are the two that are about *her* rather than about the seat: she is already
  buying a seat somewhere else, or she let this one go seconds ago.
- **Dispatch** — one of the two sends a freed seat produces: the standby queue **immediately**,
  everybody else **ten minutes later**. An empty queue costs nothing — the second dispatch comes
  forward rather than waiting on a head start nobody earned. Delivery is **held to 08:00 local**
  unless the match starts within twelve hours, because a free seat does not wake anybody at 03:00.
- **Rescue price** — what a player taking a freed seat pays: the **full share** from the vacancy,
  **half** from the rescue deadline, and no discount at all on a private court. The exact mirror
  of what the leaver recovers — the money that arrives is the money that goes back — and there is
  no checkpoint tier: a seat sold past the checkpoint is still sold at the rescue price.
- **Guarantee** — a private-court owner's exposure on a split-payment reservation: **the whole
  court price**, constant from booking until the reservation is reconciled. It is not a
  remainder and it does not shrink as seats fund
  ([ADR-0045](docs/adr/0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)) —
  what varies is how much of it somebody else's money is currently covering. An **invited**
  player's share releases it permanently the moment it is paid, because those payers are never
  refunded; a **marketplace** share is *provisional coverage* and releases nothing until
  reconciliation, because until then the game may fail to fill and the money goes back. Raketa
  holds no money behind it — the owner's card is saved with consent to charge unpaid shares
  later ([ADR-0047](docs/adr/0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)).
- **Provisional coverage** — a marketplace share that has been paid through to the club but has
  not released any of the owner's guarantee, because it is still refundable. The distinction
  that lets the number a card prints be the number Raketa stands behind.
- **Refund destination** — where a cancellation's money went, and it is the destination that
  fixes the sentence's tense: *on its way back to your card* against *credit at Sport Club
  Kraków*. **A card refund is never claimed to have landed** — a card lives 24 hours and a
  refund rarely arrives inside one — and a club credit is definite because it genuinely is
  instant. Three of the four cancellations return money to the method it came from and the
  checkpoint ending issues credit; four names, three arithmetics, because they are four
  different sentences to the player.
- **The owner's two figures** — a private court's card carries **what has been recovered** and
  **the whole court still guaranteed**, and they disagree on purpose. It is the most surprising
  thing in the private-court model: she watches money come back while owing exactly what she
  owed at the start, because every marketplace payer is refunded in full if the sold format is
  never met. Showing the guarantee alone reads as broken — thirty złoty just landed and the
  card acts as though nothing happened — and showing the recovery alone tells her she is
  covered when she is not. **The gap between them is the fact.**
- **Reconciliation** — the single moment a split-payment reservation settles: **two hours after
  the reservation ends**. Not to be confused with a departure's **Settlement**, which is about
  one player's outcome; reconciliation is about one booking's money. The two hours are a stated
  window in which a share may still be paid online or marked paid by the club, and at its close
  exactly two movements are possible: every marketplace joiner is refunded in full if the sold
  format was never met, and the owner is charged whatever is still outstanding
  ([ADR-0046](docs/adr/0046-one-reconciliation-two-hours-after-the-reservation-ends.md)).
  Nothing crystallises earlier — no pre-match cutoff kills a converted match, and the seat keeps
  selling until match time.
- **Debt** — what an owner owes Raketa when the charge at reconciliation fails. The club has been
  paid throughout and is never at risk; Raketa carries the receivable. A debt blocks only acts
  that create **new** liability — booking a court, starting a split — and never blocks paying
  for a seat in someone else's match, which is money up front and carries no risk
  ([ADR-0047](docs/adr/0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)).
- **Booking horizon** — at most **two weeks** ahead, uniformly: solo bookings, split bookings and
  open-match creation alike. The credit argument justifies only the split case; the horizon is
  uniform so a player never has to learn it twice.
- **Funder** *(of a seat)* — whoever last put money behind it. Exactly three are possible:
  **nobody** (the owner's guarantee stands for it), **a departed player**, or **the owner**,
  where the court was bought outright or where reconciliation has already charged them for the
  seat. A paid share returns to the seat's funder — releasing part of a guarantee, settling a
  departure at 100 %, or reimbursing an owner — which is one rule rather than three special
  cases, and it is why a solo booking needs no separate money model
  ([ADR-0042](docs/adr/0042-a-share-returns-to-the-seats-last-funder.md)). A seat's price is
  always the court price divided by the sport's **sold** format and is never named by its owner.
- **Opening** *(a court)* — the owner's act of letting anyone on Raketa buy a seat on a court
  that was their own people's. It changes **who may buy in**, never **how the court was
  obtained** — those are two axes and only the first can ever move, which is why an opened court
  is still a private court when four strangers hold every seat, and why the open path's
  commitment deadline and half-price rescue fill never follow it across. **Irreversible**: an
  opened court can never be closed, a remaining vacancy can never be withdrawn, and a joiner can
  never be removed. It is the private path's **commitment** — an act rather than a clock — and
  from the first stranger's payment the owner is liable for the court whatever happens next
  ([ADR-0043](docs/adr/0043-opening-a-court-is-the-private-paths-commitment.md)). Before a court
  may be opened every seat is either paid or empty; a friend joining commits nobody, a stranger
  commits the owner permanently.
- **Marketplace seat** — a seat bought by somebody the owner did not bring. It is **a promise of
  a game, not a share of a court**: if the sport's sold format cannot be met at the checkpoint it
  is refunded in full and the owner carries the court, where a share paid before the court was
  opened is not
  ([ADR-0044](docs/adr/0044-a-marketplace-seat-is-a-promise-of-a-game.md)). Two payers may sit on
  one court with different rights, and what separates them is which door they came through.

- **Hold age** — how long a court has been **held**, measured from `heldSince` (written when a
  hold is granted) — never from when the match was created. A club cap on hold age may reclaim a
  low-certainty hold and may never touch one a seat short, and a hold that regains certainty
  stops being stale
  ([ADR-0031](docs/adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)).
  **`heldSince` outlives the reclaim that ends it**, so a reclaimed hold keeps ageing and its
  card keeps saying how long it really sat; *is a court being kept aside* is `heldSince` and
  `releasedAt` read together, never either alone
  ([ADR-0089](docs/adr/0089-held-since-outlives-the-reclaim-that-ends-it.md)).
- **Composed order** — the sequence of the enrolled strip. It belongs to the **composed screen**,
  not to the matches in it: sorted by start time at composition, tie-broken on match id, shipped
  in the payload, and recomputed only when the screen is composed — on open and on explicit
  refresh, never on a live update
  ([ADR-0032](docs/adr/0032-order-is-a-property-of-the-composed-screen.md)). A match's start time
  stays mutable; a moved match is the same match.

- **Card lifetime** — a card stays on Now for **24 hours from the moment its match closed**,
  and never from when the match would have ended
  ([ADR-0073](docs/adr/0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md),
  narrowing [ADR-0048](docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)).
  Cancelled Thursday 09:00, gone Friday 09:00; played Tuesday 20:30, gone Wednesday 20:30. The
  two moments coincide for every played ending, and for a cancellation they do not — which is
  why the rule it replaces left the corpse of a match booked far ahead on a home screen for
  longer the further ahead it was booked.
- **The card's clock** — a card has **exactly one** countdown, and which moment fills it is a
  rule rather than a judgement per situation: *the next moment at which something happens to
  the viewer whether they act or not*. A forming match counts to the court locking in, a full
  one to settlement, a match about to start to the start, one wanting a score to the 24 hours,
  an offer to its expiry — and **a card that is over or cancelled counts to nothing**.
  *Always the start time* was refused because it ticks five hundred hours down to a game
  nobody is worried about while the hold expires in silence; *the next moment you can still
  act* was refused for the opposite reason, because a seat being rescued is precisely when a
  player can do nothing and most needs to see the deadline. **The clock is the app's warning,
  not its to-do list.**
- **Counting is by money** — every card counts seats that are **paid**, and a **held** seat is
  its own number beside that count, never folded into it: a seat somebody holds and nobody has
  paid for can lapse, so counting people says *full* about a match that is not. **Every number
  a sentence prints is sent as that number** — the sentences reading one less than the seats
  carry three and four, never *four, now take one off*, because it is only minus one until a
  doubles match loses two people. The cost, stated: *3 of 4* no longer means one thing across
  the screen, so the copy names what it counts — **seats paid**, **shares paid**, **played**.
- **Situation** — what a match is, said once: one of a single closed set of names, resolved by
  one ordered ladder in which **the order is the specification** and the first matching rung
  wins. The resolver takes an **optional viewer**; without one it yields the match's own
  situation, and **`waitlisted` is the one situation only a viewer can be in**. Every other
  difference an audience makes — a non-member's money line, a leaver's card, who is asked for a
  score — is *rendering*, and leaves the situation alone
  ([ADR-0040](docs/adr/0040-one-ladder-resolves-a-situation.md)). *Deliberately not called a
  **context**: this repo spends that word on bounded contexts and cannot afford a second
  meaning.*
- **Projection** *(of a situation)* — a smaller vocabulary derived from Situation by a total
  table, owned by the consumer that needs it and exhaustive over every situation. **Never a
  second ladder over the record**: two derivations of one match are what let two apps describe
  it differently at the same instant. **Match phase** — *forming · locked · cancelled* — is the
  first, read by matchmaking as a hard filter, where *locked* covers a match being played and one
  already played because matchmaking can join neither.
- **Result** — the score of a match that was played, held as **one** score on the record with the
  side that put it there, whether it is agreed, and how many proposals have been made. Not a list:
  superseded scores are **Announcements**, never history on the match
  ([ADR-0034](docs/adr/0034-matches-is-a-record-and-keeps-no-history.md)). *Never called an
  **outcome** — that word belongs to a departure.* On a card it prints as **sets of two
  integers with both sides named and the viewer's first**, never as a display string and with
  **no tiebreak field** in v1. A bare *6-4, 3-6, 6-2* was refused: with four cards from four
  evenings on one screen it prints a number that is true of **somebody**, which is the same
  defect as deriving *n − 1*. The cost is that a card carries a **person**, which is the first
  time one does. **No level movement rides beside it** — no engine updates a rating from a
  result, and a card must not invent a number nothing produced.
- **Proposal** *(of a result)* — one side putting a score forward. **Each side may propose once**,
  and a proposal always carries a score: there is no way to reject a result without stating what it
  was. A proposal its opposing side leaves unanswered for 24 hours **stands** — silence confirms —
  but once both sides have proposed, only an explicit acceptance settles it
  ([ADR-0048](docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)).
  **Accepting is opposing-side-only and one person suffices; countering is open to anyone who
  played**, including the proposing side, because what makes a teammate's agreement worthless is
  what makes their objection credible.
- **Correction** *(of a proposal)* — a side replacing its **own** live score before the other
  side has answered. **Not a second proposal** and it does not move the count: the two attempts
  bound an argument between two sides, and a player fixing his own typing before anyone has read
  it is not one of them
  ([ADR-0048](docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)). It
  follows that a teammate objecting to a teammate's score corrects it rather than countering —
  the freer of the two acts, and the same rule read the other way round.
- **Entry deadline** — **24 hours after the last point**, and the last moment *any* score may be
  put on the table: a first entry, a correction and a counter alike. It is what makes the outer
  bound of 48 hours arithmetic rather than a second rule, and it carries a named cost — an
  opponent's window to *counter* a proposal made at hour 23 is one hour, where her window to
  *accept* it runs the full day. A match whose table is still bare when it passes is **counted
  and unscored**, with no penalty to anybody.
- **Settlement deadline** — **24 hours after the live proposal was entered**, and therefore a
  property of the proposal rather than of the match: a correction replaces it along with the
  score. ADR-0048 replaced one constant with these two, and the two are what make *a score
  entered late outlives the entry deadline* true. What happens when it passes depends on how
  many sides have spoken — one proposal **stands**, two leave the match uncounted — and
  **neither answer waits on a write**: the state is derived, and the flag recording it is a
  receipt.
- **Acceptance grace** — the **30 minutes after a proposal was entered**, inside which a counter
  beats a pending acceptance. An accepted result is not settled until it closes: in a four-player
  match somebody is always slower to their phone, and without it a partner's fast tap shuts the
  door on an opponent still in the shower
  ([ADR-0048](docs/adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)). It is
  **shown to the player** while it runs
  ([ADR-0074](docs/adr/0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md)),
  because a screen that says *settled* thirty minutes before it is true is the app lying about the
  one thing it exists to state. *Not to be confused with a departure's **Settlement**, nor with
  **Reconciliation**.*
- **Counted · unscored** — a match is created **counted** or a **friendly**, and that is what the
  players chose. A counted match whose result never settles is **unscored**: it stays counted, is
  never reclassified as a friendly, and **counts as an evening and never as evidence** — it is in
  history and in how much somebody has played, and it moves nobody's level
  ([ADR-0049](docs/adr/0049-an-unscored-match-is-an-evening-not-evidence.md)). **Nobody is
  penalised for it**; playing and proving are separate facts about the same match.
- **The tag and the tone are not domain terms.** The short label above a match's card and how
  alarmed it looks are **copy and editorial judgement**, owned by each client in its own voice
  and never crossing the wire; a console watching forty matches is entitled to a different alarm
  from a player watching one. What crosses is the situation and the quantities behind it
  ([ADR-0041](docs/adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)).
  Listed here so nobody helpfully adds them back.

**A seat vacated after commitment is still *funded*.** That one sentence is why the club is safe,
why the other players' payments never change, and why a private-court owner is never re-exposed
by somebody else leaving. **An owner may give up their seat; an owner may never give up the
court** — handing a playing spot to a named person is the mechanism every participant already
has, and it is the whole of what
[ADR-0030](docs/adr/0030-a-departure-is-an-audience-not-a-state.md)'s refusal of an owner
departure was ever protecting.

---

### Now — the composed screen (`backend/app/modules/now/`)

The one request that returns the player's home screen, and the words all three apps use
about it. Decided by [ADR-0070](docs/adr/0070-now-is-three-regions-and-a-card-has-two-halves.md),
[ADR-0072](docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md),
[ADR-0073](docs/adr/0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md),
[ADR-0083](docs/adr/0083-a-card-names-one-act-and-twenty-seven-name-none.md) and
[ADR-0087](docs/adr/0087-leaving-standby-is-the-seventh-act.md).

- **Region** — one of Now's three ordered lists of cards: **offers**, **your matches**,
  **shelves**, in that order and always all three. A region **with nothing in it is present
  and empty**, because a region makes no claim, and because *not there* and *there and
  empty* handled in one place and not the other is the most productive bug in this class.
- **Shelf** — one titled row inside the shelves region, making exactly **one claim**. A
  shelf **with nothing in it is absent**: a row appearing every week to say *nothing worth
  waiting for* is a row players learn to scroll past. It crosses as a **shelf code** and an
  optional **caption code**, never a title — the words were never the part that needed to
  move without a client release; shelf *presence* and shelf *order* were.
- **Block** — one entry in the shelves region: a **shelf**, or **the door**. Each carries a
  block type, because the list stopped being homogeneous the day the door went into it — the
  same rule a card follows, where a thing is identified by what it *is* and never by where
  it sits.
- **The door** — the way into a sport's questionnaire, composed into the shelves region **in
  the position the ranked shelves would occupy** for a player who holds no rating at the sport
  she asked for. It answers *how do I get squash matches* where the alternative was a blank
  screen, and it is a **block the server put there** rather than an inference the phone draws
  from absent shelves — an inference would fire wrongly on any day the city genuinely has
  nothing in a sport she *is* rated at. It **takes those shelves' position rather than sitting
  above them**: unrated means they are absent, because she cannot be ranked against matches in
  a sport nobody holds a Level for her at. **New on Raketa and New clubs still compose beneath
  it** — the clubs are the argument for spending the two minutes, so they belong under the ask.
  The block carries **which sentence** it shows — *you have not started this* against *pick up
  where you left off* — as one block type with two codes, so the client never learns the
  difference. It carries neither the sport nor a destination: she named the sport in the ask
  and still holds it, and the code determines where the tap goes. Only a **named sport** can
  produce one; *all* means the sports she is rated at, so it names none she is not.
- **Parked run** — a questionnaire left unfinished by a player who **already holds a rating
  at some sport**. It is not a stored state and nothing expires: it is what an unfinished run
  *is*, now that a run in progress takes the screen at launch only for a player holding no
  rating at all. Four squash questions answered on a tram must never stand between her and the
  padel match she has paid for, so the run parks and **the door is the way back into it**,
  continuing where it stopped **however old** — the transcript is the server's and no age is
  read anywhere. Taking the door is one **start**, which is idempotent per player and sport and
  answers with the parked run's outstanding question, so *start* and *resume* are one act with
  two sentences.
- **Card** — one thing on the screen, of exactly three kinds: **match**, **person**, **club**.
  **Identified by the thing it is about**, never by its position or by the shelf it sits in —
  one match may appear on more than one shelf, and under thing identity one answer corrects
  every copy of it.
- **Best fit for you** / **Same level** — the shelf of **open matches the viewer could
  join**, ranked. Floor **70**, cap **6**. It **never goes silent**: when nothing clears the
  floor it keeps its cards, drops the floor and is retitled *Same level*, which is what makes
  a floor affordable at all — an unfillable shelf is *absent* rather than empty, so no card
  claims the city is empty. The two are one shelf with two codes, and the client's table turns
  each into its title.
- **Full, but worth waiting for** — the shelf of **full future matches**. Floor **80**, cap
  **3**, and **absent** whenever nothing clears the floor, because *wait for this* is a claim
  that cannot be softened: asking somebody to wait is a bigger ask than asking her to join.
  It can never be merged with the shelf above into one ordered list — being full is the
  strongest available evidence a match will be played, so a full match **outranks the joinable
  version of itself** and the merged list would be topped by matches nobody can join.
- **Eligibility** — the rules a match must pass to be *suggested* to one player: not already
  hers, in the future, before the join cutoff, not cancelled, in the sport she asked for, not
  clashing with a match she already holds, not suppressed, not one she is queued for, plus the
  shelf's own seat rule. **Every rule is evaluated for every candidate** and the answer is the
  set that failed — *seven of them were already full* and *seven of them clash with her
  Thursday* are different stories about a thin screen, and a chain that stopped at the first
  failure would throw the difference away. **How far away it is, is not one of them**: travel
  is a term that scores, never a wall.
- **Feed order** — the total base order every ranked shelf is in before any other pass:
  **best fit, then soonest, then nearest, then by identifier**. The last is not decoration —
  without an order that can never tie, two identical asks come back in whatever order the
  database happened to answer, and the shelf reshuffles under her thumb. Every pass above it
  is a **named delta**, so *why is this card third* has one answer.
- **Diversity** — the pass that stops one club's Tuesday evening filling a shelf: at most two
  of its cards sit together and the rest go to the **back of the shelf**, never out of it. A
  variety rule that also shortened the shelf would be taking a card away twice.
- **Repeat guard** — the pass that drops a shelf when **every** card on it is already on
  the shelf above. Partial overlap is allowed and one match may appear on more than one
  shelf: two shelves make two different claims about it, and hiding a good match for having
  been mentioned is a worse screen than mentioning it twice. What it exists to stop is the
  row that adds *nothing* — six cards under a second title, which teaches a player that
  scrolling is not worth it.
- **Emphasis** — **at most one card on the whole screen** is loud, and it is the first she
  would reach that clears all three of a fit of 90, coverage of 80 % and a seat open. **Any
  offer on the screen silences it entirely**: an offer is a seat with a clock on it, and a
  suggestion shouting underneath would be two things competing to be the one thing she does
  next. The cap is the guarantee rather than the thresholds — the one loud colour cannot
  become wallpaper whatever real scores turn out to do — and a card she is already in, a
  person, a club, or any card on a screen the scorer could not answer for is never the one.
- **Fit badge** — the number on a suggested card, always printed, **clamped to 20–99** at
  display: a 3 is not more useful than a 20 — both mean no — and never 100, because certainty
  is never warranted. Up to **three reasons** ride behind it as machine codes with the
  **quantities** each was scored from, never sentences and never weights, so the words are the
  client's. An unsure estimate becomes a **warning and never a percentage**. **Coverage is
  never a number the player sees.** The badge is **withheld entirely** from a viewer the
  platform cannot place at that sport — her list is still ranked by the score, and only the
  claim is withheld.
- **Aimed at** — the Level a match is looking for, printed on a card **only when it is
  precise**: the exact Level that would even the match, which exists only while one seat is
  open. The blunter answer — a band — is nearly always the viewer's own band restated, and
  printing it is the app telling her what she already knows in the voice of a measurement.
- **New on Raketa** — the shelf of **people** who joined in the last 30 days and hold a rating
  at the selected sport. Ordered by **closeness to the viewer's own Level, never descending**:
  descending makes it a leaderboard, telling every new player where they rank on the home
  screen of every stranger in the city, and puts the players the viewer can least enjoy a game
  with at the front. **No floor** — there is no such thing as a player who is insufficiently
  new — so a viewer the platform cannot rank anybody against still gets the shelf. A player
  whose Level is still **questionnaire-derived carries a quiet marker, not a second number**:
  onboarding cannot produce Confidence above 30 %, and a 3,2 from six questions is visually
  identical to a 3,4 from eleven matches.
- **New clubs** — the shelf of **clubs** that joined in the last 60 days and sell the selected
  sport. Ordered **newest first, with distance breaking ties**, because a shelf whose title
  says *this is new* must not answer *this is near*; a club with no distance sorts after one
  with a distance, since **absent is not nearest**. No floor either. Both shelves are the
  editorial answer to a thin city — a match from a new district is on the screen because the
  district is new, which is a sentence.
- **Spine** — the half of a card every phone can draw: which thing, the one moment, where,
  how much, the fit badge, the emphasis flag, the act code, whether she may leave, the seat
  claim, the card stamp. *Avoid: calling it the header — the screen has one of those and it
  is somewhere else.*
- **Situation half** — the other half, `{situation, facts}`, read **only by a client that
  knows the name**. A phone meeting an unknown situation draws the spine and drops the status
  line; it never skips the card, because an app hiding a match the player has paid for reads
  as *your app lost my booking*.
- **Act** — the single thing a card invites, from a **closed set of seven**: `takeSeat ·
  finishPaying · enterResult · answerResult · seeAlternatives · gettingIn · leaveStandby`.
  **Twenty-six of the thirty-six situations name none**, and such a card has no button and no
  tappable body. A card names an act **when the viewer can take it now and a v1 surface can
  receive it**, so an eighth arrives *with* the surface that receives it and never ahead of it —
  and the card has to be somewhere a player can see: `waitlisted` shipped its act one ticket
  before it had a region to render in
  ([ADR-0091](docs/adr/0091-a-queue-place-is-a-card-and-leaving-one-is-the-first-card-that-goes.md)).
- **Clock slot** — the card's one moment, and which moment fills it is a rule rather than
  thirty-six judgements: **the next moment at which something happens to the viewer whether
  they act or not**. A card that is over or cancelled counts to nothing and the slot is empty.
  *The clock is the app's warning, not its to-do list.*
- **Emphasis** — the at-most-one card on the whole screen that shouts. A property of the
  **composed screen** and never of a card, so the server ships the flag and the client never
  recomputes it; any offer on screen silences it entirely.
- **Stamp** — the monotonically increasing integer carried once per region and once per card,
  so a late compose racing an action can be ordered against it. There is **no screen-level
  stamp**.
- **Compose vs update** — a **compose** is the whole screen; an **update** is the one card
  that changed plus any of the two viewer-owned regions whose contents or order changed,
  **whole**. The shelves are never in an update. **A refusal returns what a success returns**:
  tapping an offer somebody already took comes back as what is true now, and the player *sees*
  the seat is gone rather than being told by a dialog.
- **Debt line** — the one fact about the viewer that rides on the envelope: an amount, a
  currency, and **one boolean** meaning *this player may not create a match or book a court*.
  Not the amount alone, which would make the phone conclude the rule; not a list of blocked
  acts, which invents a vocabulary nothing else would read.

---

### Money — terms, now with code behind them

Committed by [ADR-0055](docs/adr/0055-the-ledger-is-event-sourced-one-stream-per-player.md),
[ADR-0056](docs/adr/0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md),
[ADR-0057](docs/adr/0057-every-movement-names-the-rule-that-caused-it.md),
[ADR-0058](docs/adr/0058-one-balance-and-it-never-goes-above-zero.md) and
[ADR-0059](docs/adr/0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md).

- **Movement** — one money event: a **payer**, a **payee**, an amount, a seat, a reservation, a
  reference and a **cause**. Immutable. It is never edited and never deleted; a wrong one is
  corrected by a **compensating movement**. **The direction is the parties and never the sign**:
  the amount is strictly positive, and a refund is `Raketa → player` rather than a negative
  `player → Raketa`. A movement names **at most one** player and lives on exactly one player's
  ledger — which is what ADR-0055's *"exactly one player party"* is for, and it is read that way
  because an online share's `Raketa → club` half names none and ADR-0056 requires it.
- **Party** — who a movement is between, from a closed set: **player · club · Raketa**. A
  movement names **at most one** player party and never two — see **Movement** above for why the
  *exactly* in ADR-0055 is read as *at most*, and what is enforced instead. **A club is only ever
  a payee, never a payer** — that is a rule, and the nightly reconciliation asserts it.
- **Cause** — the *rule that fired*, from a closed enumeration. Not a description of the movement
  but the reason it was owed. Every terminal situation that moves money contributes exactly one.
  **It is two enumerations, one inside the other, and the split is deliberate.** The five a
  *card* may carry — `inventoryLost · clubCancelled · formCancelled · checkpointCancelled ·
  settlementReopened` — are `kernel.Cause`, in the shared kernel because Matches produces one,
  Money records it and Now renders it, and a second implementation in any of the three would be
  a defect. `settlementReopened` is among them and reaches no card, because by the time a
  settled departure is reopened no card exists. The **ledger's** enumeration is wider —
  eighteen, adding `shareOnline · shareAtCounter · claimLapsed · withdrawnBeforeLock ·
  formatUnmetRefund · ownerReimbursed · leaverReversed · leaverFull · leaverRescue ·
  leaverForfeit · reconciliationOwnerCharge · collectionFailed · debtCleared` — and embeds the
  kernel's five **by value**, with the inclusion asserted at module load. It is wider rather
  than the kernel's being grown because `Cause` crosses the wire as an OpenAPI enum both
  clients build an exhaustive table over, and thirteen ledger-only names would be thirteen
  sentences no card can ever print.
- **Ledger** — the fold over a player's movements. One event-sourced stream per player.
- **Balance** — a player's derived position on the ledger. In v1 it is zero or negative; **there
  is no wallet**, because stored value is a regulated product Raketa is not buying. It is the
  fold of the two causes that bear on it — a failed collection creates a debt, clearing one
  discharges it — and **not** a net of every movement: paying for a court is not owing for one,
  and a half-refunded leaver lost half rather than owing it.
- **Debt** — a balance below zero, created when a collection fails. It blocks booking a court and
  starting a split reservation, never paying for somebody else's seat. It has **no line items**:
  it is a number, and its provenance is read from the causes behind it.
- **Held** — money Raketa has received and not yet passed on. **Derived, never stored** — a flag
  on an immutable event would be a second version of the truth. Per seat it is
  `Σ(player→Raketa) − Σ(Raketa→club) − Σ(Raketa→player)`, and it goes **negative** between a
  refund Raketa advanced on the private path and the owner charge that recovers it — the
  working-capital position, readable rather than estimated.
- **Counter-paid share** — cash an invited player handed to a club, marked paid by the club. The
  one movement that is `player → club` with Raketa as neither party. Available to invited players
  only; a marketplace seat is always bought from Raketa, online.

**Custody follows what was sold.** An open match's seat money is **held by Raketa** until the
match commits, because no court exists yet and the money may have to come back whole. A private
court is already bought, so a share is **paid through to the club** on arrival and Raketa holds
nothing. Same 30 zł, two regimes, and the difference is invisible on the screen. **Which regime
applies is the match's answer, never the payer's** — the channel a payment came through (bought
online, or cash across a counter) is a different fact and decides nothing about custody. *Built
(`#70`): a seat payment gives the player her seat and the court that seat earns in **one**
write, and records the money in a second, because a movement is never written inside a match
transaction.*

**The ledger is downstream and one-way: Money reads Matches; Matches never reads Money.** Which
door a payer came through lives on the *match record*, not the ledger, because it is an input to
a rule the derivation kernel evaluates from the record and the clock alone. The ledger
**references** a seat; it does not define one. The fence is checked rather than trusted: an
import contract forbids Matches to reach Money at all, directly or through anything else.

**Erasure is a read-time substitution.** A ledger's movements survive an erasure request —
accounting records carry a legal-obligation basis — so what changes is the **party every reader
sees**, not what is stored. Rewriting the events is the one thing an append-only store cannot
do. What identifies a person lives in the account, and is erased there.

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
