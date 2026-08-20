# Spec delta — silence confirms a result

Resolves [#19 — Silence must confirm a score, not discard it](https://github.com/Raketa02/Raketa/issues/19).

Governed by [ADR-0048](../../../adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)
and [ADR-0049](../../../adr/0049-an-unscored-match-is-an-evening-not-evidence.md).

Documents amended: `3.1-enrolled_match_states_and_transitions.md` §1.4 and GROUP 9,
`now-section-domain-spec.md` §5c–5f and the constants table, and
`rakieta-now-section-specification.md` §351–356. **No document is edited** — the 486 `[SRC:]`
citations resolve against their bytes.

---

## 1. The rule reverses

`3.1` sends both `needsResult` and `confirmResult` to `playedNoScore` at `matchEnd + 30 min`.
A result somebody entered and nobody answered was discarded.

**What governs:** a result nobody answers **stands**, and the match counts. The full reasoning is
[ADR-0048](../../../adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md); the
short form is that the old rule paid the losing player to ignore the prompt.

## 2. Two clocks replace `RESULT_MIN`

| Constant | Value | Measured from | Governs |
| --- | --- | --- | --- |
| *(withdrawn)* `RESULT_MIN` | `30` min | `matchEnd` | — |
| **entry deadline** | `24` h | `matchEnd` | after it, with no proposal made, the match is uncounted |
| **entry nudge** | `30` min | `matchEnd` | the card asks; it forbids nothing |
| **proposal deadline** | `24` h | the proposal being entered | a lone proposal unanswered at it **stands** |
| **acceptance grace** | `30` min | the proposal being entered | an acceptance cannot settle before it |

Both new deadlines are **platform** constants, as `RESULT_MIN` was. The outer bound on a result is
therefore **48 hours after the final point**, reached by entering at hour 23 and being answered at
hour 47.

The nudge is a card, not a rule. It is where the wanted behaviour lives — a score typed on court is
a score nobody argues about — but a score entered at 22:00 counts exactly as much.

## 3. Who may act

The **paid seats at `matchEnd`**. A leaver and a standby player are never offered any of it, which
is [ADR-0030](../../../adr/0030-a-departure-is-an-audience-not-a-state.md) already, and is doc 5's
**B2** already closed.

| Act | Who | How often |
| --- | --- | --- |
| Enter a result | anyone on either side | once per **side** |
| Revise a proposal | anyone on the **proposing** side | freely, until the other side responds |
| Accept | the **opposing** side; one person suffices | ends it |
| Counter | anyone who played, **including the proposing side** | consumes that side's proposal |

Two asymmetries, both deliberate. **Accepting is opponents-only and countering is not**, because
the reason a teammate's agreement is worthless — it is self-serving — is the reason a teammate's
objection is credible. And **a counter must carry a score**: there is no bare rejection anywhere in
the flow.

## 4. Settlement

```
enter ──▶ proposal live, 24 h
            │
            ├── opposing side accepts (after the 30 min grace)  ──▶ counted
            ├── nobody answers within 24 h                      ──▶ counted
            └── the other side counters                         ──▶ two proposals stand
                                                                     │
                                    ├── either side accepts the other's ──▶ counted
                                    └── neither accepts within 24 h     ──▶ uncounted
```

Once **both** sides have proposed, silence no longer confirms anything: only an explicit acceptance
settles it. A settled result is **final** — no support correction, no reversal.

Inside the acceptance grace a counter beats a pending acceptance. Without it, in a four-player
match a fast partner closes the door on the opponent who has not reached their phone.

## 5. What a player types

Undecided everywhere until now — the specification set carries a hardcoded `"6-4, 3-6, 6-2"` and
nothing behind it. It matters more under this delta than it did, because **the score is the language
of disagreement**: a counter is a score, so a player must be able to express one.

**Guided entry per sport, validated permissively.** Padel and tennis in sets and games; squash and
badminton in games and points. The app knows the shape and declines the obviously impossible; it
does **not** enforce the rulebook. Local variation — tie-breaks, golden point, timed formats — is
wide enough that a strict validator eventually calls a real match illegal, which is a support
problem with no answer.

Free text is refused: two people cannot meaningfully disagree about strings, and `6-4 3-6 6-2`
against `6:4, 3:6, 6:2` would read as a disagreement that is not one. Winner-only is refused: it
throws away the difference between 6-0 6-0 and 7-6 7-6 permanently, and **nothing in Raketa turns a
result into a level movement yet** — the match-update engine does not exist — so whatever it
eventually wants can only come from what was written down on the night.

## 6. The ladder: two rungs swap, no situation moves

`now-section-domain-spec.md` §5c–5f currently tests the deadline **above** the score:

| | Before | After |
| --- | --- | --- |
| 5c | `m.confirmed` → `completed` | unchanged |
| 5d | `now ≥ resultWindow` → `playedNoScore` | a **proposal is live** → `confirmResult` |
| 5e | `m.score` truthy → `confirmResult` | `now ≥ matchEnd + 24 h`, or both proposals stand unanswered → `playedNoScore` |
| 5f | otherwise → `needsResult` | unchanged |

`confirmResult` no longer falls to `playedNoScore` when a clock runs out; it resolves to
`completed`. **The model stays at 33 situations** — nothing is added, nothing is removed, and the
four post-play names all survive. Re-verified against the executed table on
[`research/state-table.md`](../research/state-table.md), rows 7–10.

`confirmResult` remains the one situation that reads the viewer, and stays *rendering* rather than
a second resolution: the proposing side sees that it is waiting, the opposing side sees that it is
asked. That is [ADR-0040](../../../adr/0040-one-ladder-resolves-a-situation.md)'s rule, not an
exception to it.

## 7. `keepUntil` is no longer a clock

`keepUntil = matchEnd + 24 h` puts the card off Now at the moment a result may still be live — and
a result can settle up to 48 hours after the final point.

**What governs:** a match awaiting entry, or carrying a live proposal, **stays on Now until it
settles**, and only then begins its 24 hours. The home screen's job is what needs you now, and a
result awaiting your tap is exactly that. Anything that walks matches to retire them must read
settlement, not the clock.

The Inbox is the wrong home for it — the Inbox holds what other people and clubs are asking of you,
and this is your own match still finishing.

## 8. Withdrawn: every sanction in the post-play group

| Document | Withdrawn |
| --- | --- |
| `3.1` GROUP 9 `playedNoScore` | *"All four lose a point of Player Score — it is a shared job."* |
| `3.1` §1.4 driver table | *"counts for nobody, all four lose a Player Score point"* |
| `rakieta-now-section-specification.md` §356 | the same sentence in the copy column |

Nobody is penalised for not entering or not agreeing a result — see
[ADR-0049](../../../adr/0049-an-unscored-match-is-an-evening-not-evidence.md). `completed`'s
*"Player Score +1 — turned up, paid, confirmed"* is withdrawn on the same grounds: the +1 is for
turning up and paying, and confirming is not a third thing Player Score measures.

**An unscored match is a counted match that produced no result, never a friendly.** It counts as an
evening — history, how much a player has played, who they have now played with — and never as
evidence. Nobody's level moves.

## 9. In-app only, for the first version

Nothing in this flow is delivered to a phone. No push, no scheduled local reminder. The prompt is a
card and a badge, and a player meets it when they next open Raketa.

This is affordable **only because the deadline is 24 hours**. Marta will open the app at some point
on Sunday; she would not reliably have opened it in a specific half hour on Saturday night.
Shortening either deadline without a notification channel reintroduces exactly the discarded-match
problem this delta removes.

## 10. Not settled here

- **The copy.** Client-owned. The product's word is **propose a modification**, never *dispute*.
  Four sentences carry unusual weight: the entry nudge, the *"Kuba entered this — is it right?"*
  card, the counter, and the sentence a player reads when their match ended up counting for nothing.
- **The screens.** Graduated to its own ticket: with no chat, these three interactions *are* the
  entire conversation between four people who disagree.
- **What a result does to a level.** The rating context's, and its engine does not exist. This delta
  fixes only what is captured, so that it is not boxed in.
- **Match chat.** Not required by this flow and deliberately not depended on.
