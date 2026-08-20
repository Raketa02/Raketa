# Spec delta — Now's lower half, and the offered seat

**Governs over** `1-now_screen_production_spec.md` **Part 5** (§5.3's ranking and cut, §5.5's
empty state), **Part 6** (§6.2's qualification, §6.3's section), the Part 1 block table rows 4
and 5, and acceptance-gate rows 9 and 10; over `4-match_recommendation_engine_architecture.md`
§3.4's lane configs and §3.5's dedupe and six-card cap; and over
`now-section-domain-spec.md` §C.4's cap/floor table, §D.3 and §D.4. Everything else in those
documents stands unchanged, and the match card, the fit badge, the header, the sport bar and the
enrolled strip remain **final** in the two UI documents.

**Authority for this file:**
[ADR-0036](../../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md).
**The decisions:** [ADR-0050](../../../adr/0050-now-below-the-strip-is-shelves.md),
[ADR-0051](../../../adr/0051-now-is-ordered-not-drawn.md),
[ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md).
**The reasoning:** [`Raketa02/Raketa#20`](https://github.com/Raketa02/Raketa/issues/20).

The source documents are **not edited**. 486 `[SRC: line N]` citations and 27 bare-filename
cross-references resolve against their bytes.

> **This is the largest departure from the two UI documents in this effort**, and it is a
> supersede rather than an overrule. Parts 5 and 6 were sized against a six-card vertical
> budget that shelves abolish; neither document was deciding against shelves, and the component
> shelves are built from — `.sqrow` — is defined in `UI` §D5 and marked *"not used by Now"*.

---

## 1. The screen below the strip — Parts 5 and 6 are superseded as sections

| As written | What governs |
|---|---|
| **Part 5** — *Best fit for you*, three stacked cards, fit-descending | **A shelf**: a titled, horizontally-scrolling `.sqrow` |
| **Part 6** — *Full, but worth waiting for*, exactly one card | **A shelf** of its own |
| Block table rows 4 (`matchCard ×3`) and 5 (`matchCard ×1–2`) | Superseded. *(Row 5 already disagreed with `V.home`, doc 4 §3.4 and acceptance row 10, all of which said one card.)* |
| `4` §3.5 — global feed cap **6 cards** | **5 shelves**, each capped in §2 below. The ceiling now bounds the number of *questions* asked, not the number of cards |
| `4` §3.5 — *"dedupe across lanes, first lane wins"* | **Reversed.** A match may appear on several shelves; a **shelf is dropped** when it would be nothing but repeats of a shelf above it |

**The blocks, top to bottom:** offered seats *(only when the viewer holds one)* · the enrolled
strip · shelves 1–5 · tab bar. There is still no promo block.

## 2. The shelves

| # | Shelf | Contents | Floor | Cap |
|---|---|---|---|---|
| 1 | *Best fit for you* | open matches the viewer could join | **70** | 10 |
| 2 | *Full, but worth waiting for* | full future matches | **80** | **3** |
| 3 | *Recently viewed* | tapped within **48 h**, still joinable | **none** | 10 |
| 4 | *New on Raketa* | players who joined within **30 days** | — | **20** |
| 5 | *New clubs* | clubs that joined within **60 days** | — | 10 |

- Shelf **order is a server-owned list**, identical for every player, reorderable without a
  client release.
- **An empty shelf is absent** — no header, no empty card. Part 6's rule, generalised.
- **Shelf 1 never goes silent**: when nothing clears 70 its title becomes ***Same level*** and it
  shows matches closest to the viewer's Level, **with no floor**. §5.5's *"We do not invent
  players"* card therefore fires only when the city genuinely has nothing.
- Every shelf ends in a **tail card opening Find**, pre-filtered to that shelf's question.
- **The sport filter applies to every shelf**, including 4 and 5.
- **First run** — a just-onboarded player sees shelves 1, 4 and 5. Nothing is added to fill the
  gap: no first-run shelf, no banner.

### §5.3's cut, and the floor ADR-0037 asked for

| §5.3 as written | What governs |
|---|---|
| `sort = Match Fit descending; show = the top 3` | `floor 70` → `FEED_ORDER` → diversity → `cap 10` |
| *"No minimum score on Now… if the best available is a 62, that is the honest answer"* | **Superseded.** A floor is affordable now only because an unfillable shelf is **absent** rather than empty, so no card claims the city is empty. This discharges ADR-0037's open worry: a true 12 can no longer reach the screen, so the 20–99 display clamp never prints a number that is not the match's |

### [GAP-C2] — resolved

`V.home` applied no floor and no sort to the full lane; `V.find` applied `>= 80` and sorted by
fit; doc 4 §3.4 specified `floor: 80, cap: 1`. **`floor 80`, sort by `FEED_ORDER`, `cap 3`.** The
prototype's behaviour was the oversight it was called. The cap rises from 1 to 3 because the
constraint that forced *one* was vertical geometry; the **80** is kept because its reason never
was geometry — asking somebody to wait is a bigger ask than asking them to join.

## 3. Ordering, eligibility and emphasis

**Per shelf:** retrieve → eligibility → score → floor → **sort by `FEED_ORDER`** → diversity →
cap → tail card. **Then compose:** shelf order → repeat guard → emphasis.

- **`FEED_ORDER` survives as the total base order** (`[desc(fit), asc(start), asc(dist), asc(id)]`),
  not as a tie-break underneath other mechanisms. Every pass above it is a named delta, so
  *"why is this card third?"* is answerable in one sentence.
- **Eligibility, both match shelves** — evaluated exhaustively, never short-circuited:
  `NotAlreadyMine`, `StartsInFuture`, `BeforeJoinCutoff`, `NotCancelled`, `SportMatchesFilter`,
  `NoScheduleConflict`, `NotSuppressed`, **`NotOnStandby`**; plus `HasFreeSeat` (shelf 1) /
  `IsFull` (shelf 2). **`WithinTravelCeiling` is in neither.** `!m.forced` is **not** a rule —
  `forced` is the demo hatch, *"must not survive"*.
- **Diversity may reorder and may never shorten.** `4` §3.4's `MaxPerClubHour` returns fewer than
  `cap` when candidates are blocked and nothing remains; that is a defect. The **regular-group**
  variety cap is **not built** — `PlayHistory.played_recently` ships dark.
- **Emphasis: at most one card on the whole screen**, not one per shelf — the first in the final
  composed order that clears fit ≥ 90 · coverage ≥ 80 % · a seat open. **An offer on the screen
  silences it entirely.**
- **Nothing is random.** Exploration is dropped; discovery is shelves 4 and 5. No seed, no draw,
  nothing recorded for replay.

## 4. The shelves that are not matches

**Shelf 4 — people.** Photo (or the first two letters of the name), name, Level. Level shows
whether or not they have played; a questionnaire-derived rating carries **a quiet marker, not a
percentage** — onboarding cannot exceed 30 % confidence, and a second number on the card is the
gauge ADR-0037 refused. Ordered by **closeness to the viewer's Level**, never descending.
**Inert in v1 and styled so.** Appearing is **on by default with a switch to leave**.

**Shelf 5 — clubs.** **Tap opens Find, pre-filtered to that club.** No new screen.

## 5. The offered seat — new, above everything

Not in any source document. Full decision:
[ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md).

| | |
|---|---|
| **Where** | Its own block above the shelves **and above the enrolled strip** |
| **Mode** | Match > 24 h away → **exclusive**, one player at a time, *"a seat is being offered to you"*. Inside 24 h → **open call**, *"first to take it"*, in waves of 3 → +5 after 10 min → everyone |
| **Clock** | Exclusive hold **1 h from delivery**; released to all at the latest **12 h before start** |
| **Delivery** | Held to **08:00 local** unless the match starts within 12 h |
| **Order offered** | Standby first, **fit-ordered within standby**; then everyone else eligible, fit-ordered |
| **Position** | **Not shown.** *"You are on the standby list"*, never a number — a position that can rise reads as a broken promise |
| **Several at once** | Side-scrolling row, **soonest-to-expire first**, uncapped; a player holds at most **3 exclusive** offers |
| **Accept** | Accepting and paying are **two acts**: accept stops the offer clock, a short second window covers payment. Money mechanics are not settled here |
| **Withdrawal** | **Silent** — the delivered notification is removed and the card disappears. No second buzz. A line is written to Inbox |
| **Push** | In scope for **exactly one message**. Several offers → **one** notification. Says time and urgency, **never the venue**. Permission asked **in context** at first standby join; refused → **no offer at all**, the seat goes to the open pool |

**This supersedes the push rulings** on [#12](https://github.com/Raketa02/Raketa/issues/12) and
[#19](https://github.com/Raketa02/Raketa/issues/19). What made deferral affordable was named
there — *"the 24-hour deadline, not a claim that anything is fast"* — and an offered seat is the
first thing on Now that expires inside a day and is contested. Both are new facts, not a change
of mind about the old ones.
