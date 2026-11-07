# Rakieta Player Application — v37 Complete Documentation

**Every screen, every state, every engine, every constant. What it is, how a player uses it, how it works underneath, and why it is worth building.**

Written against `rakieta-player-app-prototype-v37.html`. Every figure is computed by the prototype on the seeded Saturday, **8 August 2026 at 14:00**. Nothing is illustrative.

| | |
|---|---|
| **Screens** | 40 |
| **Side sheets** | 6 |
| **Match states** | 35 contexts resolving to 17 player-facing tags |
| **Canonical lifecycle** | 9 states, shared verbatim with the club console |
| **Actions** | 130 |
| **Engines** | ~230 functions |
| **Scenarios** | 90 in 14 groups |
| **Clubs / courts** | 9 clubs · 31 courts · 4 sports |
| **Cross-app assertions** | 40, all passing against Club Console v6 |

---

## How to read this document

Every feature is documented under the same eight headings:

| Heading | Answers |
|---|---|
| **What it is** | The feature in plain language |
| **Why it exists** | The problem it solves, and what happens without it |
| **How a player uses it** | A named person, walked end to end |
| **What they see** | Real figures from the prototype |
| **How it works underneath** | Engines, formulas, data |
| **Rules and edge cases** | The behaviour that is easy to get wrong |
| **Value to the player** | Why they would care |
| **What it deliberately does not do** | The refusals, which are as much a feature as the rest |

---

# PART 0 — FOUNDATIONS

## 0.1 The problem the product exists to solve

Racket sports have a coordination problem, not a booking problem.

A padel court needs four people. A squash court needs two. Finding a court is trivial — every club in Kraków has a website. Finding **three other people at roughly your level, free at the same hour, willing to pay their share** is not, and it is the reason most people who want to play twice a week play once a month.

The existing solutions all fail in the same place:

| Approach | Where it breaks |
|---|---|
| Club booking page | Sells you a court. Says nothing about who fills it |
| WhatsApp group | Works until the person holding the phone leaves. Invisible, unmeasurable, and half the demand evaporates |
| One person books, chases the money | The organiser becomes a debt collector, and stops organising |
| Open "social" listings | Nobody knows if the game will be any good, so nobody joins |

Rakieta's answer is that **a player buys a seat, not a court** — and everything else in the product follows from defending that sentence.

## 0.2 The six invariants

These are not features. They are the constraints every feature is built inside, and violating any one of them would break the product's reason to exist.

### Invariant 1 — A player pays for a seat, never a court

`share = court price ÷ players the sport is sold for`, written the moment the match is created and **never re-priced**.

**Why it is load-bearing.** The moment one person books and chases the others, that person is a debt collector — and they stop organising. Every competitor has this problem and calls it "split payments", which is the same problem with a friendlier name. Here the seat is the unit of sale, so nobody is ever owed anything by anybody.

**What it forbids.** A seat price that can be set independently of its court, because four seats would eventually cost more than hiring the whole thing.

### Invariant 2 — The clock alone never commits anybody

A booking becomes irrevocable at the **commitment deadline**, which is `min(start − club window, start − 12 h)` — the earlier of the two. Before it, leaving is free. After it, the outcome decides.

**Why it is load-bearing.** A player needs a floor they can rely on at every club. A club may commit *earlier* than the platform default, never later.

### Invariant 3 — A refund is decided by the outcome, not by the clock

The industry standard is a clock ladder: 24 hours 100%, 12 hours 50%, under 12 nothing. That is cost recovery for a court sold whole, and it is the wrong instrument for a seat.

**The seat rule:** full refund before commitment. After commitment, **full if the seat refills, nothing if it does not.**

**Why it is load-bearing.** If the seat refills the club has lost nothing, so charging the player is a fine rather than cost recovery. The player is never punished for a vacancy the market absorbed.

### Invariant 4 — A court is held in proportion to certainty, and the bar rises

The hold ladder, for a four-player match:

| Paid seats | Hold | For how long |
|---|---|---|
| 4 | **Hard** | Permanently. It is sold |
| 3 | **Soft** | While more than **4 hours** remain |
| 2 | **Soft** | While more than **12 hours** remain |
| 0–1 | **None** | The court stays on the market |

**Singles has no soft tier.** One of two paid seats holds nothing — half a booking is a much weaker signal than three quarters of one.

**Why it is load-bearing.** Two paid seats four days out is a reasonable bet for a club. Two paid seats at nine in the evening for a match at ten tomorrow morning is a speculative hold on a court somebody would have bought. The bar rising as play approaches is what makes clubs willing to hold anything at all.

### Invariant 5 — Nobody types a level in

Not the player, not staff, not a club. A rating is produced by an adaptive questionnaire at onboarding and moved only by **counted, confirmed match results** and weighted coach calibration observations.

**Why it is load-bearing.** A rating a person can edit means nothing, so matches stop being balanced, so first-timers stop coming back. The documented gap is **71% return after a balanced first match against 34% after a lopsided one** — the single largest lever in the product.

### Invariant 6 — This app never recomputes a club's model *(new in v36)*

Where a decision belongs to the club — how likely a match is to fill, how a contested hour is ordered, whether a hold is extended past the ladder — this app **reads what the club published** and shows it, attributed.

**Why it is load-bearing.** A player application running its own copy of a club's model will eventually show a court held that the club has already released. That is the worst failure this system can have, and it is silent until somebody arrives at a court that is not theirs.

## 0.3 The domain model

| Entity | Fields that matter |
|---|---|
| **Club** | 9 seeded. Name, distance, commitment window (12 or 24 h), join cutoff (20 or 30 min), per-sport card value, published policy |
| **Court** | 31 seeded. Club, sport, category (surface), indoor/outdoor, price multiplier |
| **Category** | The unit the marketplace sells. Mondo · Wall · Glass back. **Every court in a category costs the same**, which is what makes a seat price guaranteeable before a court is assigned |
| **Match** | Sport, format, club, category, start, duration, seats[], price, share, created, committedAt, releasedAt, vacated |
| **Seat** | Player, paid, timestamp. Each seat is independently liable |
| **Player** | Ratings per sport-format (μ, σ, confidence), Player Score, attendance record, wallet, membership, intent declarations |
| **Declaration** | Standing intent: sport, level band, days, hours, frequency, ceiling, horizon, distance, competitiveness, clubs |

## 0.4 Money constants

```
RATE.Padel = { off: {60: 96, 90: 128, 120: 160},
               pk:  {60: 112, 90: 152, 120: 184} }

courtPrice = RATE[sport][peak|off][duration] × club.multiplier × court.multiplier
share      = courtPrice ÷ SPORTS[sport].players
payable    = share − cardOff(club, sport)
```

**Peak begins at 17:00** (`PEAK = 1020` minutes). A 90-minute peak padel court on a ×1.00 court is **152,00 zł**, so a seat is **38,00 zł**.

## 0.5 Time

One integer clock: `t = dayIndex × 1440 + minutes`, day 0 being Saturday 8 August 2026. **Everything derived from time recomputes on every render.** Move the clock and holds lapse, deadlines pass, states change. Nothing is cached, which is why no two screens can disagree.

## 0.6 Interface

A phone frame. **Five tabs**: Now · Find · [create] · Inbox · You. The middle tab is a raised circular create button rather than a label.

Detail opens as a **pushed screen** with a back affordance, never a modal. A small number of things open as **sheets** (6 of them) where the context behind them must stay visible.

**The scenario rail** holds 90 named states in 14 groups, each reseeding from `freshState()` before applying its own mutations, so scenarios never leak into each other.

---

# PART 1 — ONBOARDING AND THE RATING ENGINE

The most technically dense part of the product, and the one that decides whether everything downstream works.

## 1.1 The problem

A new player must be given a level before they have played a single match here. Get it wrong and their first match is lopsided; a lopsided first match is a 34% return rate against 71%.

But asking somebody to rate themselves produces garbage, in a predictable direction: beginners overrate, good players underrate, and everybody interprets "intermediate" differently.

## 1.2 What it is

An **adaptive questionnaire** — five to nine questions, chosen one at a time based on the answers so far — that produces a rating as a **distribution**, not a number: a mean (μ), an uncertainty (σ), a likely range, and a confidence percentage.

## 1.3 How a player uses it

1. Tomek creates an account and picks his sports. Each sport is rated **on its own** — a level is never borrowed from another.
2. He is asked how long he has played, how often, whether he has played competitively, and a series of tactical questions that get more specific as the engine narrows in.
3. Each answer moves μ and shrinks σ. The engine picks the next question to maximise information gained.
4. He finishes with **Padel 2,71 · likely 2,45–2,97 · 30% confident · Provisional**.
5. A screen shows him the record kept: not "question 3 = usually" but the **evidence class and weight** each answer contributed, so it can be learned from in a year.
6. A final, optional question asks whether he wants to receive match proposals.

## 1.4 What he sees

| | |
|---|---|
| Starting level | **2,71** |
| Likely range | **2,45 – 2,97** |
| Confidence | **30%** |
| Status | **Provisional** |
| Questions asked | **7** |

Plus the sentence that makes the whole thing honest:

> *These are hypotheses, not verdicts. Nobody leaves onboarding above 42% confident, and most leave at 30%. The questionnaire only has to put you in the right neighbourhood so your first matches are worth playing. Those matches are what actually set your level.*

## 1.5 How it works underneath

**The confidence caps** are the core discipline:

```
CAPS.questionnaire = 30   /* a questionnaire alone can never exceed this */
CAPS.formatLink    = 42   /* unless the other format of the same sport is already rated */
```

**Evidence classes.** Every answer is stored as a class with a weight and a σ contribution, never as a raw answer. `observationSigma`, `projectedSigma` and `finalize` fuse them.

**Format linking.** Padel singles and padel doubles are different ratings. Once one exists, it is *evidence* for the other — `formatLinkEvidence` — but weaker than direct play, which is why the cap rises only to 42%.

**No cross-sport transfer.** Being 4,0 at tennis says nothing reliable about padel. This was deliberately removed.

**Contradiction detection.** `detectContradiction` catches answer patterns that cannot both be true (a self-described beginner answering advanced tactical questions correctly) and asks a disambiguating question rather than averaging.

## 1.6 Rules and edge cases

- **Nobody leaves onboarding confident.** 30% is the design target, not a failure.
- A rating is a **distribution**. The app shows the range everywhere, never a bare number pretending to precision.
- The engine asks the **minimum** questions to reach the cap. Answering consistently ends it sooner.
- `obReplay` lets a player see exactly which answers produced which movement.

## 1.7 Value to the player

Their first match is worth playing. That is the entire argument, and it is the difference between a product they use twice and one they use weekly.

## 1.8 What it deliberately does not do

No self-rating slider. No "select your level: beginner / intermediate / advanced". No importing a rating from another platform without treating it as weak evidence.

---

# PART 2 — THE FIVE TABS

## 2.1 Now (Home)

**What it is.** What is happening to you today and next, in the order you need it.

**Why it exists.** A player opens the app for one of three reasons: to check a match they are in, to find one, or because something changed. Now answers the first and third without a tap.

**How a player uses it.** Tomek opens the app at 14:00. The top card is Saturday's 18:30 padel match: three of four seats paid, court held until 14:30, and a deadline strip showing exactly where the clock sits between now and play. Below it, anything needing him — a request from a club, a score to confirm.

**What they see.** A live match card with its state tag, the seat count, the court state, and the deadline strip. Then upcoming matches, then anything outstanding.

**How it works underneath.** `matchState(m)` resolves one of 35 contexts; `deadlineStrip` renders the clock; `courtHold` decides the court line. The card is a pure function of state — nothing is stored about how it should look.

**Value to the player.** The single most common question — *is my match still on?* — is answered before they tap anything.

## 2.2 Find

**What it is.** Two things behind one tab: **open matches** to join, and **courts** to book whole.

**Why it exists.** These are genuinely different products. A seat in a match with three strangers at your level is not the same purchase as a court you have booked for your own four. Conflating them is the mistake every "social play" feature makes.

**How a player uses it.**
1. Tomek taps Find. Matches first, courts behind a segmented control.
2. He filters: sport, day, time of day, duration, court category, format, intensity, minimum Player Score.
3. Each card shows who is in, their levels, the **Match Fit** percentage, the **forecast**, the seat price after his card, and how long the match has left to fill.
4. He taps one to see the full disclosure before paying.

**What they see.** A match card carries: club and distance · start and duration · category · seats filled · the other players with their levels · **Match Fit** · **forecast** with a split bar · price after card · the deadline.

**How it works underneath.**

**`matchFit`** — seven weighted terms producing a single percentage:

| Term | What it measures |
|---|---|
| Level fit | How close the seat's target is to you |
| Balance | Whether the sides can be made even |
| Competitiveness | Social against competitive alignment |
| Reliability | Whether these people turn up |
| Convenience | Distance and time of day against your habits |
| Familiarity | Whether you have played with any of them |
| Certainty | How likely the match is to actually happen |

**`forecast`** — the identity that makes a match's quality legible:

```
pct = 100 − gap × 145 − spread × 32
```

where `gap` is the difference between the two sides' strength and `spread` is the range of levels in the match. Rendered as a **split bar** so a player sees *why* a match is 88% rather than being told a number.

**`freeStarts` / `clubStarts`** — court availability, with a **flexibility** control (exact · ±30 min · ±1 h) that marks starts which avoid leaving an unsellable half hour.

**Rules and edge cases.**
- **`findPool` has four structural exclusions.** A Rescue Seat can never appear here — there is no code path from the rescue engine to the public search.
- A match you are already in never appears.
- Below the reliability gate (70), open matches are not joinable, and the app says so with what clears it.

**Value to the player.** They can tell, before paying, whether the game will be worth playing.

## 2.3 Create

**What it is.** The flow that produces an open match or a private court, built around a single obsession: **not creating a duplicate**.

**Why it exists.** The fastest way to kill a marketplace is to let four people each create a Thursday 19:00 padel match, none of which fills.

**How a player uses it.**
1. Tomek taps the create button. He picks sport, then day, then time.
2. **Before he can continue**, the app shows him `similarOpen` — matches already forming at a similar hour and level. Most of the time one of them is what he wanted, and he joins it instead.
3. If he continues, he chooses **open match** or **private court**, the category, the duration, and who may join (open · friends · invite only).
4. The price is shown as a court price *and* a seat share, so he can see both.
5. He pays his own seat. He is never liable for anybody else's.

**What they see.** A creation summary: category, court price, seat share after card, when the court would be held, when it commits, and when joining closes.

**How it works underneath.** `crDraft` holds the draft; `crSimilarByDay` and `similarOpen` find duplicates; `crLimits` enforces what the club allows; `crStarts` produces valid start times; `mkMatch` writes it.

**Rules and edge cases.**
- **A private court is a different product** and says so: the club's clock-based cancellation ladder applies, not the seat rule, and the flow shows that ladder before payment.
- Creating does not hold a court. **Paying does** — one seat is not enough, and the app explains the ladder at the moment it matters.

**Value to the player.** They get the match they wanted without becoming its banker.

## 2.4 Inbox

**What it is.** Two things kept deliberately apart: **requests** (which hold something and expire) and **announcements** (which do not).

**Why it exists.** An announcement can be ignored forever. A request holds a seat, an hour, or a decision three other people are waiting on. Mixing them trains a player to ignore both.

**How a player uses it.** The tab carries a live count of open requests. Requests lead; conversations and club announcements follow.

**Value to the player.** Nothing that matters is buried under something that does not.

## 2.5 You

**What it is.** Everything about the player, in three groups: **Playing** · **At your clubs** · **Money and account**.

**What they see.** A profile header with level, Player Score and a ring. If anything needs them, a card at the top. Then 17 rows across the three groups.

---

# PART 3 — THE MATCH STATE MACHINE

The technical heart of the player application.

## 3.1 What it is

**35 contexts resolving to 17 player-facing tags.** A match is never "booked" or "not booked" — it is in exactly one of 35 situations, each with its own tag, tone, explanation, and set of true statements about money and the court.

## 3.2 The 17 tags

`Forming` · `Court held` · `Court released` · `Court committed` · `Court protected` · `Full` · `Confirmed` · `Replacement pending` · `Rescue active` · `Ready to play` · `Needs result` · `Confirm the result` · `Completed` · `Played` · `On standby` · `Reserved` · `Cancelled`

## 3.3 The 35 contexts

| Group | Contexts |
|---|---|
| Forming | `forming` · `formingHeld` · `formingLate` · `formingBack` |
| Held | `heldSoft` · `heldReleased` · `heldStale` · `heldExtended` · `clubHeld` |
| Protected | `protectedCourt` · `protectedBack` · `protectedLate` |
| Full | `full` · `confirmed` · `confirmedOnFill` |
| Recovery | `replacement` · `replacementTransfer` · `rescue` · `rescueLate` |
| Play | `ready` · `needsResult` · `confirmResult` · `completed` · `playedShort` · `playedNoShow` · `playedNoScore` |
| Cancelled | `cancelledIncomplete` · `cancelledCheckpoint` · `cancelledClub` · `inventoryLost` |
| Other | `waitlisted` · `privateReserved` · `privatePartial` · `privateFull` · `privateOpen` |

## 3.4 Two contexts worth documenting in full

### `heldStale` — a hold released by the club's maximum hold age

**Tag:** Court released · **Tone:** watch · **Backend:** RELEASED

> *Zabłocie returns a soft hold that has sat unfilled for 48 hours. It is back on sale, your 38,00 zł is untouched, and one more paid seat brings a court back.*

The lines it shows:
- You paid 38,00 zł — untouched, and refundable in full
- The club returns a soft hold that has sat unfilled for 48 hours
- **This is a club setting, not a marketplace rule**, and it is on the club's rules screen
- It only ever releases a speculative hold — never a committed match
- One more paid seat brings a court back immediately

**Why it matters.** Before this existed, a court released at 48 hours was explained with the ladder's reasoning, which was not the reason. A player told the wrong reason once stops believing the right ones.

### `heldExtended` — a hold kept past what the ladder guarantees

**Tag:** Court held · **Tone:** good · **Backend:** HELD

> *The ladder would have returned this court at 12 hours. Zabłocie is holding it anyway because this match is likely to fill.*

- Their model puts this match at 97% to fill, and a club may extend a hold on that basis
- **It can never work the other way**: no model may release a court earlier than the ladder promised
- Leaving now still returns everything, in minutes

**The critical implementation detail.** This reads `m.clubExtended` and `m.clubFill` — **published facts**. The app does not run a fill model. That is Invariant 6, and it exists because the first implementation *did* recompute it, and the conformance suite caught the two apps disagreeing about whether a court was held.

## 3.5 The canonical lifecycle

Nine states, shared verbatim with the club console and asserted by the cross-application suite:

```
FORMING ──▶ HELD ──▶ FUNDED ──▶ CONFIRMED ──▶ PLAYED
   ▲         │                      │
   └── RELEASED                  AT_RISK ──▶ RECOVERING ──┐
                                    │                     │
                                    └──────────────────────▶ CANCELLED
```

The 17 tags are **derived** from these nine. The tag is the truth about the group; the context line says which situation produced it.

## 3.6 Resolution order

`matchState(m)` tests in a fixed order — cancellation states first, then played, then full/committed, then recovery, then hold states, then forming. **Order is the specification**: a cancelled match that was also full must read as cancelled.

---

# PART 4 — MONEY

## 4.1 Joining and paying

**Atomic.** Occupying a seat and paying for it are one act. There is no "reserve and pay later", because a reserved seat that is not paid holds nothing and blocks somebody who would have paid.

`payable(m) = share − cardOff(club, sport)`, and with a slot discount, `share = (price − discount) ÷ players`.

## 4.2 The cancellation screen

**What it is.** Before confirming, a player sees **every possible outcome**, not one number.

**How a player uses it.** Ola taps Leave on a committed match. The screen shows:

| Outcome | She gets back |
|---|---|
| Somebody joins at full price | **100%** |
| A Rescue player takes it at half price | **50%** |
| A guest her own group sponsors fills it | **0%** |
| Nobody comes | **0%** |

**Why all four.** The refund is not chosen and not announced — it is **whatever happens to the seat**. Showing one number would be a promise the engine cannot make.

**Rules and edge cases.**
- Before commitment: full reversal, seat becomes unpaid, match reforms. No outcomes to show.
- The seat is offered to replacements **immediately**, before the refund settles.
- **A club-sponsored guest cannot fill a vacated seat** — that would let a club decide a refund. Only the leaver's own group can sponsor.

## 4.3 The wallet

Stored value: a balance, the source of every credit, selectable at checkout, and the destination the checkpoint's rebooking credit pays into.

**The wallet and the club card never merge.** The card is a fixed, bounded benefit on a seat price. The wallet is money. **No automatic rule may ever put money in the wallet** — issuing credit is always deliberate.

## 4.4 Blocked states

- **Debt threshold:** *"Zabłocie is holding new bookings until 112,00 zł is settled."* Named as the club's setting, with what it does not affect.
- **Card authorisation:** *"Your card will be authorised, not charged."* It holds the money without taking it and releases after the scan.
- A failed recurring charge **retries after 24 hours** before any person is asked.

---

# PART 5 — THE FIVE NUMBERS AND THE SKILL PASSPORT

## 5.1 Skill Passport

Levels per sport and format, each with its band, likely range, confidence, and the evidence behind it. `bandBar` renders μ and σ as a distribution, never a point.

## 5.2 The Five Numbers

The five figures that describe a player's game: level, consistency, reliability, activity, and range. Each is explained rather than scored.

## 5.3 Player Score

Four strands, gate at **70**:

| Strand | |
|---|---|
| Attendance | Scans, not assertions |
| Late cancellations | |
| Payment failures | |
| Replacement success | |

**What it changes, shown live:** whether open matches are joinable · how long an invitation holds a seat (2 h normally, **45 min** when reliability is low) · whether card authorisation is required · standby priority · rank in a contested hour.

**What clears it:** turning up. Nothing else — no appeal, no payment, nothing staff can type.

---

# PART 6 — REQUESTS: WHAT A CLUB MAY ASK

## 6.1 The nine kinds

| Kind | What it asks | Declining costs |
|---|---|---|
| `formation_invite` | Join an hour the club opened from the intent pool | Nothing; feeds the matcher |
| `widen_band` | Accept a wider level band | Nothing; the rung ends |
| `time_shift` | Move the whole match | **Full refund** — you bought a time |
| `merge` | Merge with another short match | Nothing |
| `reschedule_offer` | Take a different court after an incident | Nothing; the refund was always yours |
| `queue_offer` | An allocated contested hour | Nothing; fairness counter untouched |
| `court_offer` | A whole court as a private hire | Nothing |
| `programme_place` | A place in a class at your level | Nothing |
| `payment_action` | Settle a debt or authorise a card | Nothing changes |

## 6.2 Rules

- **No request charges anybody on arrival.** Payment happens on acceptance, by the player's own act.
- Every request names the club and **who acted** — a person, a rule, or the engine. Nothing arrives anonymously.
- **The invitation hold:** 2 hours · **30 minutes** if the match is under four hours away · **never lapsing between 22:00 and 08:00** (pushed to 08:00) · never outliving the commitment deadline. *(Asserted identical to the club console.)*
- **A held seat neither fills the match nor holds a court. Only money does.**
- `widen_band`, `time_shift` and `merge` require **every player in the match**. One refusal ends that rung.
- **Declining a `time_shift` is not leaving a match** and is never charged as one.

## 6.3 Consent disclosure

`widen_band` shows the forecast **both ways** — 88% as sold against 81% if widened — computed by the same engine the match screen uses, so they cannot disagree. `merge` gives the same disclosure a Find card gives.

---

# PART 7 — INTENT: THE DEMAND NOBODY COULD SEE

## 7.1 What it is

A standing declaration that somebody at your level would play at these hours, at these clubs, up to this price. **It is not a booking and never becomes one by itself.**

## 7.2 The ten fields

| Field | Required | Blank means |
|---|---|---|
| Sport | **Yes** | — |
| Level band | **Yes** | Derived from the rating, never typed |
| **Opt in to proposals** | **Yes, explicit** | — |
| Preferred days | No | Any day is possible |
| Preferred hours | No | Any hour the club is open |
| Games a week | No | Assumed one |
| Most per seat | No | **No ceiling** — eligible at any price |
| Commitment horizon | No | Assumed a fortnight |
| Preferred distance | No | Distance is not a constraint |
| Competitive or social | No | A weight, not a filter |

**A blank field means "no preference", never "leave me out."** Every missing field is listed with what leaving it blank does.

## 7.3 The opt-in

Its own screen, with a table of exactly what changes either way:

| | Off | On |
|---|---|---|
| A club can see somebody wants Thursday evening | Yes | Yes |
| A club can see it is **you** | No | Only once you accept |
| A club can put a match to you | No | Yes |
| Anything held or charged without you | No | No |
| Other players see your declaration | No | No |

**Onboarding asks once**, after the assessment, and **skipping is not consent** — an unanswered question resolves to opt-in false. *(Asserted.)*

## 7.4 Completion

A ring per declaration and a percentage on You, with every blank field explained. The prompt states *why* — each field makes proposals closer to the game they actually want — and that none of it is required. **No blocking, no repeated prompting, no penalty for a partial profile.**

## 7.5 Value to the player

A game on a Thursday they would otherwise not have got, without holding anything, charging anything, or being contacted without consent.

---

# PART 8 — STANDBY, WAITLISTS AND QUEUES

Three different objects, deliberately kept apart.

| Object | Says | Ordered by |
|---|---|---|
| **Standby** (*I am free*) | "I will take a seat that frees up" | Rescue priority: level, proximity, reliability, availability, **minus** recent Rescues |
| **Match waitlist** | "I want into this specific full match" | **Level fit** — *"the seat needs about 2,54 and you are 2,71"* |
| **Hour queue** | "I want this contested hour" | The club's published allocation policy |

**The four allocation policies:** rotating fairness · membership weighted · lottery · first come. The player sees the policy **by name** and the reason in the club's own words. Winning an allocation increments the fairness counter, and the screen says so — otherwise rotation does not rotate.

**A queue makes speed worthless**, which is the point: no alarms at midnight, no scripts, no advantage to the faster phone.

---

# PART 9 — PROGRAMMES, OPEN PLAY, COMPETITIONS, COMMUNITY

## 9.1 Programmes (Academy)

Browsable with coach, time, term, price per head and **level band**. Enrolment is gated by the engine on the rating, **never by the door**. The club's cancellation ladder is shown, labelled *the club sets this*, with the reason: a coach's hour is committed long before the class runs.

## 9.2 Open Play

Sessions with format, level band, capacity and **price per head**. Labelled a **different product**: sold per head at a session price, not a court divided by four — so nothing about it bends the seat rule.

**Rotations do not count towards the rating.** The pairings are engineered for balance, so the results are not independent evidence. Attendance and reliability count exactly as they do for a match.

## 9.3 Competitions

Leagues, ladders and americanos, with the level range enforced by the engine. **Entry without a partner** is supported — the single most common reason somebody looks at a league and does not join. **A competition round played on a booked court with a confirmed score is a counted match** and feeds the rating identically.

## 9.4 Community

Level-band groups maintain their own membership from the rating. **When a rating change would move a player between bands, they are told before the group changes, not after.**

---

# PART 10 — THE CLUB, AS THE PLAYER SEES IT

## 10.1 Club screen

Profile, amenities, hours, languages, the published rules, all four cancellation ladders, and legal documents accepted **per version** — a new version asks again rather than assuming the old answer still stands.

## 10.2 Published policy, read

The player app reads a `ClubPolicy` object rather than hardcoding constants:

```
window · joinCut · holdLadder{far, near, softDoubles} · maxHoldAge · probHold
checkpoint · allocation · checkinMin · cancellation{...} · card
entitlementsByTier · openingHours · languages · legalDocs[] · rescue{widen, shift, merge}
```

Every value is on a **Club rules** screen with what it means for the player and **whose rule it is**.

**What is not in the object and cannot be:** a player's level, a refund on one seat, who is in a match, a seat price separate from its court, the existence of the checkpoint.

## 10.3 Memberships and entitlements

Tiers with an entitlement list. **Early access is honoured in both flows** — private court and open match — identically, which is the trap this design exists to prevent. A benefit applying to only one is worthless to exactly the members who play most.

---

# PART 11 — ATTENDANCE AND RESULTS

## 11.1 Check-in

QR, from the club's `checkinMin` before. **Attendance is a scan and a no-show is the absence of one.** A staff-assisted scan is shown with who recorded it, so the record is never silent.

## 11.2 Results

Entered within the result window, **confirmed by another player** before it counts towards a rating. `resultWindow`, `entersscore`, `fixscore`, `confirmres`.

---

# PART 12 — SETTINGS, PRIVACY AND SAFETY

Defaults, channel preferences, payment methods, auto-find, and — separately — blocking, private notes, visibility, and data export. **A blocked player never appears in a match with you, and is never told.**

---

# PART 13 — ENGINE REFERENCE

| Engine | Answers | Shared with club |
|---|---|---|
| `courtPriceOf` · `catPrice` · `shareOf` | What a court and a seat cost | **Yes** |
| `deadlines` | Commit, rescue, checkpoint, join cutoff | **Yes** |
| `courtHold` | What hold is in force, and why | **Yes** |
| `holdUntil` | How long an invitation holds a seat | **Yes** |
| `lifeOf` | Which of nine canonical states | **Yes** |
| `bookings` | Deterministic private-hire occupancy | **Yes** |
| `matchState` | Which of 35 contexts | No |
| `matchFit` | Seven-term match quality | No |
| `forecast` · `arrangedForecast` | Balance, as a percentage and a bar | No |
| `seatTarget` · `targetBand` | What level the open seat needs | No |
| `rescueCore` | The six conditions for a Rescue Seat | No |
| `leaveOutcome` · `refundTable` | Every possible refund outcome | No |
| `findPool` | What is publicly listed, with four exclusions | No |
| `similarOpen` · `crSimilarByDay` | Duplicate prevention | No |
| `estimate` · `finalize` · `fuseAll` | The rating engine | No |
| `iComplete` · `profilePct` | Intent completeness | **Yes (contract)** |
| `pol` | The club's published policy | **Yes** |
| `reliability` · `attRate` · `record` | Player Score | No |

---

# PART 14 — THE SCENARIO LIBRARY

**90 scenarios in 14 groups**, each reseeding cleanly:

| Group | Count |
|---|---|
| Onboarding · the rating engine | 13 |
| The court hold ladder | 6 |
| Creating without duplicating | 6 |
| Match states | 1 (gallery of all 35) |
| Court certainty and commitment | 6 |
| Your position on the clock | 4 |
| Walkthrough | 9 |
| Cancellation · nine scenarios | 9 |
| Edge cases | 3 |
| Waitlist and engine | 4 |
| Ratings and money | 7 |
| Ecosystem · club → player | 11 |
| Ecosystem · what you can now do | 7 |
| Intent · what the pool needs | 4 |

---

# PART 15 — TESTING

Three suites, run headlessly against a minimal DOM stub:

| Suite | Covers | Current |
|---|---|---|
| `harness.js` | Every scenario renders; every view renders; every state resolves; invariants hold | **89 scenarios · 40 views · 35 states** |
| `conformance.js` | Loads **both** applications in one process and asserts every shared rule | **40 assertions, 0 disagreements** |
| `harness-club.js` | The club side | 60 scenarios · 38 views |

**What conformance asserts:** the nine canonical states in the same order · the hold ladder at every tier · singles has no soft tier · a hand-commit beats everything · maximum hold age · demand-aware extension · `commit = min(window, 12 h)` · rescue at 4 h doubles and 6 h singles · checkpoint at 2 h universally · the invitation hold including the overnight rule · court prices per multiplier · `share = court ÷ players` · slot discounts landing identically · the four allocation policy names · every request kind having a surface · no rating in the published policy · publishing charging nobody · **the ten intent fields in the same order**.

---

# PART 16 — WHAT THE APPLICATION IS NOT

- **Not a booking engine with a social feature bolted on.** The seat is the unit of sale.
- **Not a social network.** No feed, no followers, no content to farm.
- ~~**Not a ranking ladder.** A rating exists to make matches balanced, not to be climbed.~~ **Retired 2026-11-07**: Raketa ranks players, one ranking per sport sorted by the level itself — see [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md).
- **Not a place a level can be typed.** By anybody.
- **Not a chat app.** Match chat exists; there is no general messaging between strangers.
- **Not a system that hides its reasoning.** Every state explains itself.

---

# PART 17 — KNOWN LIMITATIONS

1. **The two prototypes do not share a backend.** A consent request the club creates and a player's acceptance are simulated independently. In the real system both are reads and writes against one state.
2. **`fillLikely` was removed and replaced by published data**, which is correct — but it means a club with no fill model publishes nothing, and the app must fall back to the ladder and say so.
3. **Rescue priority is displayed, not computed.** The five factors and the score of 74 are static in the interface.
4. **No partial-group cancellation.** Two players leaving simultaneously is not modelled.
5. **Preference expiry is not implemented.** A declaration from four months ago is treated like one from yesterday.
6. **Observed patterns read only one club's matches**, by deliberate privacy choice.
7. **The wallet is stored value**, which is e-money in several jurisdictions above a threshold. Caps, expiry and refundability need a legal answer per market.

---

# PART 18 — GLOSSARY

| Term | Meaning |
|---|---|
| **Seat** | One player's place in a match, independently paid and independently liable |
| **Share** | Court price ÷ players. Written at creation, never re-priced |
| **Category** | A surface type sold as one product. Every court in it costs the same |
| **Soft hold** | A court held on partial payment, which may lapse |
| **Commitment** | The moment the deadline passes on a full match. The court never returns |
| **Checkpoint** | Two hours before play, universal. Decides what happens to a still-short committed match |
| **Rescue Seat** | A vacated seat at 50%, targeted only, never publicly listed |
| **Match Fit** | Seven-term measure of whether this match suits you |
| **Forecast** | `100 − gap×145 − spread×32`. How even the match will be |
| **Player Score** | Four-strand reliability. Applied, never displayed publicly |
| **Declaration** | Standing intent. Not a booking, and never becomes one by itself |
| **Published policy** | The club object this app reads so no rule is a surprise twice |

---

*Rakieta Player Application v37 · 40 screens · 6 sheets · 35 contexts · 17 tags · 9 canonical states · 130 actions · 90 scenarios · 40 cross-application assertions*
