# Spec delta — the state vocabulary

What [ADR-0040](../../../adr/0040-one-ladder-resolves-a-situation.md) and
[ADR-0041](../../../adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
change in the specification set. **No document in `docs/specs/` is edited** — 27 bare-filename
cross-citations and 486 `[SRC:]` citations resolve against their bytes, and
[ADR-0036](../../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)
requires amendment by delta.

## 1. Four vocabularies become one, plus projections

| Was | Now |
| --- | --- |
| 33 context keys (`matchState`) | **`Situation`** — the one enumeration, 33 members |
| 17 tags (`now-section-domain-spec.md` §E.2, `UI` §B6.2) | client copy, per app, in its own voice |
| 15 `be` values (`ST[key].be`) | **deleted** — zero readers in 7 334 lines |
| 9 LIFE9 states (`lifeOf`, §D.15) | **not blessed and not retired** — the club console's projection, written when a console screen asks |
| `MatchPhase` (`backend/app/engines/matchmaking.py`) | the **first projection** off `Situation`; three members unchanged |

`now-section-domain-spec.md` §D.15's description of `lifeOf` as *"the cross-application
contract"* is **withdrawn**. Its nine-rung ladder is a second derivation over the same record,
and the research file already shows it disagreeing with `matchState` on `m.forced`
([`research/state-table.md`](../research/state-table.md) §6.5).

## 2. The resolver takes a viewer

`matchState(m, viewer, now)` and `lifeOf(m, now)` collapse into
**`situation(match, viewer | None, now)`**. Called without a viewer it cannot yield
`waitlisted`; that is the whole of the difference.

**Rung 6 is the only rung that reads the viewer** (`!mySeat(m) && waitlists.includes(m.id)`,
§E.1). Everything else that varies by audience runs *after* the ladder and leaves the situation
alone:

- the non-member money rewrite (`UI` §B6.1, lines 3968–3973);
- [ADR-0030](../../../adr/0030-a-departure-is-an-audience-not-a-state.md)'s leaver card — the
  same situation rendered for somebody who used to hold a seat;
- the result affordance, suppressed for a leaver (ADR-0030) and for a standby player (doc 5 B2)
  without moving either off `needsResult`.

Adding a second viewer-reading rung is a decision, not a refactor.

## 3. The wire

**`{key, tone, facts}` (doc 5 A5) becomes `{situation, facts}`.**

- The **tag never crosses**. It is display text — `Court held`, `On standby` — in English, on a
  Polish product, and doc 5 A5's own argument puts it on the client.
- **`tone` never crosses.** `situation → tone` is total over the 33 rows the client already
  holds for copy, and the native-kit delta made tone→colour surface-aware, so a `tone` field
  would carry a token to be looked up twice.
- What `facts` contains is **not settled by these ADRs** — it belongs to the `GET /now` wire
  contract.

## 4. `inventoryLost`'s tone

[`native-kit.md`](native-kit.md) §4 states that ADR-0031 *"already moves `inventoryLost`'s tone
to `ended`"*. **It does not** — ADR-0031 concerns the hold ladder's floor and says nothing about
tone, and no other ADR retones it either. The agreement was reached on the ladder ticket and
never landed.

Under ADR-0041 it does not need to land in an ADR: with tone client-owned, the player app's
table maps `inventoryLost` to `ended`, like the other three cancellations, and the
`ST_TONE['bad'] is undefined` defect — flagged by `UI` §B6.3, `UI` §G6.1, `SPEC` §E2 and `DOM`
§E.2 `[GAP-E3]` — dies there. `native-kit.md`'s reasoning stands; only its citation was wrong,
and this section is the correction.

## 5. Consequences for the tone splits

After ADR-0031–0033 removed `protectedCourt` and `protectedLate`, and with `inventoryLost`
retoned, **two tags carry a tone split**, not the three `DOM` §E.2 bolds: `Forming`
(`idle`/`watch`) and `Court held` (`watch`/`good`). This is now inert — nothing renders tone
from a tag, because nothing ships a tag.

## 6. Obligations this delta places on code

Neither is performed here; both are app-scoped work.

- **`backend/`** — `MatchPhase`'s docstring says *"Borrowed vocabulary … Matches will define
  them"*. It is defined now: the docstring cites ADR-0040 and the enum becomes a declared
  projection with a module-load exhaustiveness assertion. `SeatState` and `CourtHold` remain
  borrowed; ADR-0040 does not reach them.
- **Each client** — a 33-row table of copy, tag and tone, over the generated union, in an
  exhaustive switch. A missing row is a compile error in that client's own build, which is the
  fence ADR-0040 substitutes for ADR-0021's promised cross-application suite.
