# Spec delta — Now's lower half, and the offered seat

**Governs over** `1-now_screen_production_spec.md` **Part 5** (§5.3's ranking and cut, §5.5's
empty state), **Part 6** (§6.2's qualification, §6.3's section), the Part 1 block table rows 4
and 5, and acceptance-gate rows 9 and 10; over `4-match_recommendation_engine_architecture.md`
§3.4's lane configs and §3.5's dedupe and six-card cap; and over
`now-section-domain-spec.md` §C.4's cap/floor table, §D.3 and §D.4; and — from §5 — over
`3.1-enrolled_match_states_and_transitions.md` §4.2's **Stages 1–2**, leaving its Stages 3–5
untouched. Everything else in those
documents stands unchanged, and the match card, the fit badge, the header, the sport bar and the
enrolled strip remain **final** in the two UI documents.

**Authority for this file:**
[ADR-0036](../../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md).
**The decisions:** [ADR-0050](../../../adr/0050-now-below-the-strip-is-shelves.md),
[ADR-0051](../../../adr/0051-now-is-ordered-not-drawn.md),
[ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md),
[ADR-0061](../../../adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md).
**The reasoning:** [`Raketa02/Raketa#20`](https://github.com/Raketa02/Raketa/issues/20),
[`#27`](https://github.com/Raketa02/Raketa/issues/27).

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

Not in any source document. Full decisions:
[ADR-0052](../../../adr/0052-a-vacancy-is-offered-not-announced.md), **amended by**
[ADR-0061](../../../adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md), which
**removes the exclusive offer** and settles who *"everyone else eligible"* is. Where the two
differ, 0061 governs. **Governs also over `3.1` §4.2's Stages 1–2**; its Stages 3–5 (widen the
band, shift the time, merge two matches) are untouched and stay unanimous-consent.

| | |
|---|---|
| **Where** | Its own block above the shelves **and above the enrolled strip** |
| **Mode** | **One mode: the open call.** *"A seat just opened, first to take it"*, at every distance from the match. The exclusive offer, its wording, its one-hour hold, the three-offer cap and the twelve-hour backstop **do not ship** |
| **Who** | Fact filters (sport · **a rating at that sport** · free seat · join cutoff · live inventory · no calendar conflict) **inside the match's level band**. Leaving the band is `3.1` Stage 3 and needs the remaining players' unanimous consent |
| **Floor** | **> 24 h to the match → fit ≥ 70. Inside 24 h → no floor** |
| **Order** | The **seven-rung invitation ladder** (§5.1), fit-ordered within a rung |
| **Dispatch** | **Two steps**: rung 1 immediately, rungs 2–7 together **+10 min**. An empty rung is skipped instantly |
| **Delivery** | Held to **08:00 local** unless the match starts within 12 h |
| **Price** | Full price from the vacancy; **50 %** from the rescue deadline. Same ladder in both phases |
| **Position** | **Not shown.** *"You are on the standby list"*, never a number |
| **Several at once** | Side-scrolling row, **soonest-to-expire first**, uncapped |
| **Accept** | **First to accept wins**, and accepting **locks the seat for a short payment window** (5 min, a placeholder the money chain owns). **The card disappears for everyone else** for the duration and **returns if the payment lapses** |
| **Withdrawal** | **Silent, and there is nothing to withdraw** ([ADR-0062](../../../adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)). The card disappears from Now; the delivered notification is **left alone** — no removal exists on any platform, and the past-tense wording means it never made a claim that goes stale. **No Inbox line.** The N−1 fan-out costs nothing because nothing is sent |
| **Push** | **One live message per player**, replacing the previous one rather than stacking — the collapse *is* the frequency control, since there is no cap in v1. **Past tense, never present**: *"A padel seat **just opened** — Tue 19:00, 20 min away. First to take it."* Sport, time and travel time; **never the venue**. The line names **a seat the player asked for over one we chose for them**, soonest-to-expire inside each group, the rest a count (*"+2 more"*); the **opening clause** (*the seat you asked about* · *a match you looked at* · *a seat near you*) belongs to the named seat. **Only a standby seat buzzes** — rungs 3–7 update the line silently, *provisional on one device measurement* (below) |
| **Permission** | Explained **during onboarding**, *Turn on* / *Not now*; **only *Turn on* fires the OS prompt**, and *Not now* is asked again at first standby join. Refusing costs only *exclusive* offers, which no longer exist — the card still appears on Now |

### 5.1 The invitation ladder

Drawn by the prototype's `V.search` — *"Who is invited, in order"*, a card the **leaver** sees.

| # | Rung | v1 |
|---|---|---|
| 1 | Standby — asked for **this** match | **Ships** |
| 2 | Standing rules / last-minute availability switched on | **Dark.** Its own effort; a standing rule **auto-joins waitlists**, so it feeds rung 1 |
| 3 | Asked for the seat before — offered an earlier vacancy on this match, did not get it | **Ships** |
| 4 | Viewed or followed the match | **Ships as viewed** (48 h). *Follow* does not exist |
| 5 | Compatible players who use this club often | **Ships** |
| 6 | Nearby **reliable** players inside the level range | **Ships degraded** — level band only. *Reliable* is recorded and unused; *nearby* has no source ([#30](https://github.com/Raketa02/Raketa/issues/30)) |
| 7 | Marked available at this hour | **Dark.** Same effort as rung 2 |

**Superseded by ADR-0061 in the prototype:** the ladder card's *"ten minutes to accept, five to
pay"* (the accept window is gone with the hold; the five minutes survive as the payment window's
placeholder), and `V.search`'s *"wave 3 · wider level and distance"*, which fires automatically
where `3.1` requires consent.

**This supersedes the push rulings** on [#12](https://github.com/Raketa02/Raketa/issues/12) and
[#19](https://github.com/Raketa02/Raketa/issues/19). What made deferral affordable was named
there — *"the 24-hour deadline, not a claim that anything is fast"* — and an offered seat is the
first thing on Now that expires inside a day and is contested. Both are new facts, not a change
of mind about the old ones.

### 5.2 The notification after the seat is gone

Full decision: [ADR-0062](../../../adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md).
Resolves [#28](https://github.com/Raketa02/Raketa/issues/28) and supersedes ADR-0052's
*"the delivered notification is removed from the lock screen"*, which has **no mechanism on any
platform** — Apple documents replacement and never documents removal; the one path that removes
is a silent push whose limits *"are disabled when testing your app from Xcode"*.

**The notification is a prompt to look. Now is the only surface that states what is true.**

| | |
|---|---|
| **The lock screen never claims** | Past tense — *"a padel seat **just opened**"* — true at 16:42, true at midnight, true after somebody else takes it. The retraction is carried by the **wording**, exactly as it is for the card |
| **Nothing is ever removed** | Not on iOS (no mechanism), not on Android (declined: cancelling needs the app to post the message itself, which kills it on force-quit and triggers a 7-day deprioritisation). **One behaviour on both platforms** |
| **Our messages accumulate** | Tuesday's line is still there on Wednesday, after the match. Known and accepted: sweeping it would cost one message per player per match. The collapse rule is the only cleanup |
| **The tap re-reads live state** | The notification carries no truth. The seat is joinable or it is not |
| **"That seat has gone"** | **One plain line at the top of Now, once** — not a card, no tap target, it fades. A card is what a takeable seat wears |
| **One rule, every arrival** | *The first time a player lands on Now after a match they were told about has no room for them.* Notification tap, cold open, and the card evaporating mid-scroll are the same rule at different moments. A seat they were never told about produces nothing |
| **Room, not a seat** | They were told the **match opened up**, not that Marek's particular seat did. If a second seat freed meanwhile they get the live card and **no line** — a disappointment stacked on a takeable seat is a lost fill |

**The one thing measured before it ships.** Apple documents `interruption-level: passive` and
documents `apns-collapse-id` and **never documents the two together**, so the silent update for
rungs 3–7 is a fact about devices. Send one message to one real iPhone with both set and watch.
**If it buzzes, the fallback is that every replacement buzzes.** Carried by
[#26](https://github.com/Raketa02/Raketa/issues/26).
