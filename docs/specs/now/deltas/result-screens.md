# Spec delta — the result is a route, and the card names the act

Resolves [#24 — Entering, countering and agreeing a score: the three screens that replace a
conversation](https://github.com/Raketa02/Raketa/issues/24).

Governed by [ADR-0060](../../../adr/0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md),
which draws the screens [ADR-0048](../../../adr/0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)
§10 deliberately declined to draw.

**The evidence:** the prototype on branch
[`prototype/result-confirmation`](https://github.com/Raketa02/Raketa/tree/prototype/result-confirmation) —
three variants of the conversation, built on the real kit and read at 320, 375, 393 and 430 pt.

Documents affected: `rakieta-now-section-ui-spec.md` §B6.3's `[GAP]` and §G Open Decision 8,
and `deltas/result-confirmation.md` §5, which specified what a player types and not where.
**No document is edited** — the 486 `[SRC:]` citations resolve against their bytes.

**This is the first delta that fills a `[GAP]` rather than correcting a statement.** The five
kinds in [`../README.md`](../README.md) all describe a document saying something that turns
out to be wrong, narrower than its placement implied, or an artifact of the harness. §B6.3
says nothing wrong; it records a mechanism nobody had ever used and points at §G for a
recommendation. What follows uses it.

---

## 1. The conversation is a route

| Considered | What governs |
|---|---|
| In the Now card — the state card grows a second action and opens the pad inside itself | **A route.** The card prompts it and is a tap target; the route is where a score is entered, confirmed or modified |
| A sheet over Now — the card is a prompt, the sheet is the room | |

Two facts decide it, and neither is about taste.

**The action row holds one action.** §B6.3 gives `stateCard` one CTA plus two 40pt icon
buttons. `confirmResult` needs two real actions, because ADR-0048 §3 forbids a bare
rejection — *a counter must carry a score* — so *propose a modification* is not an optional
second affordance, it is the only way to disagree. The in-card variant finds the room only by
spending the `⌘` access button that `st.post` already drops, which is the card's last spare
slot.

**Entry is typing, and the card is for reading.** A guided per-sport pad inside a night card
runs the card past a 320pt screen on its own, on a screen whose own delta
([`native-kit.md`](native-kit.md) §3) already accepted that the fullest card overflows. Making
the card the place a player types turns an accepted exception into the normal case.

**The cost, recorded:** a player is taken off Now to answer a card that was on Now, and the
route is empty for almost all of its existence. ADR-0060's Consequences carry both.

## 2. `cta` gets its first two writers — but not the four §G proposed

§B6.3's `[GAP]` — *"`cta` and `left` are read by `stateCard` but no state in the table ever
sets them"* — is discharged for two situations only.

| Situation | `cta.label` | `cta.target` |
|---|---|---|
| `needsResult` | *the act of entering* | the result route |
| `confirmResult` | *the act of answering* | the result route |
| the other 31 | unchanged — the `Open match` fallback | unchanged — the match screen |

**§G Open Decision 8 proposed four groups**, adding `ready` → *"Getting in"* and `cancelled*`
→ *"See alternatives"*. Those two are **not** decided here and stay open: this ticket drew the
post-play group and has no evidence about the other two. The recommendation stands as a
recommendation.

**One thing in §G's proposal is refused.** It suggests `confirmResult` → *"Confirm 6-4, 3-6,
6-2"*, putting the score in the button label. §4 below is the reason not to: a score with its
sides cut off is exactly what this delta stops shipping, and a button is the one place there
is no room to name them.

**The labels themselves are placeholders.** Copy is client-owned and still in the map's fog.
What is decided is that a per-situation label exists, that these two situations carry one, and
that the label distinguishes *enter a score* from *answer one*.

**`left`, the countdown suffix, stays unwritten.** The clock belongs on the route, at a size a
card cannot give it (§5), and a `' · 19 h'` suffix on a button label is not that.

## 3. The card is a tap target, and both taps go to the same place

`UI` §D9 sends the state card's press to the match screen for every situation
(`data-go="{st.cta.go ?? 'match'}"`, *"currently always the match screen"*). For `needsResult`
and `confirmResult` the whole card and its button both resolve to the **result route**.

**The state moves on the server.** At `matchEnd` the backend derives `needsResult` and the
card shows it the next time Now is composed. [ADR-0053](../../../adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)
and [ADR-0054](../../../adr/0054-now-refreshes-when-asked-never-on-a-timer.md) are unchanged:
nothing ticks the card into a new state, and the phone holds no rule that would let it.

## 4. A score crosses the wire per side

The specification set hardcodes `"6-4, 3-6, 6-2"` in every document that mentions a score and
**nowhere says whose 6 it is**. In a doubles match — four people, two sides — an unlabelled
string is unusable, and `deltas/result-confirmation.md` §5 makes it load-bearing: *the score
is the language of disagreement*, so a counter is a score, and two sides cannot disagree about
an unattributed one.

**What governs:** a score is a structured value carried per side, and every surface that shows
one names both sides with the viewer's first. The display string is a client formatting of it.
This binds the `GET /now` `facts` payload and whatever the result route reads, and it is one
more instance of the copy duplication [ADR-0005](../../../adr/0005-three-app-monorepo-ownership-boundaries.md)
accepts.

## 5. What the route draws

One route, resolving the same situation the card resolved — not a screen identifier, which
would be a second vocabulary [ADR-0040](../../../adr/0040-one-ladder-resolves-a-situation.md)
forbids.

| Situation | What it draws |
|---|---|
| `needsResult` | the grid and the pad; the sides named; the entry deadline stated |
| `confirmResult`, viewer on the **opposing** side | the proposed score as a named table, **the countdown as the hero**, *that's right* and *propose a modification* |
| `confirmResult`, viewer on the **proposing** side | the same score, the same clock read the other way, and one action: change what was sent |
| a live counter | the grid pre-loaded with the other side's numbers, theirs shown above as still on the table |
| `playedNoScore` | terminal: what the evening counted for, and what it did not |

**The countdown is the hero on the confirm screen.** The remaining time is the largest figure
there, beside the sentence saying nobody has to do anything. Silence is what settles this
result, so the screen that asks for a tap has to state what happens without one — loudly
enough that a player who taps nothing has still been told.

**The unscored ending gets the route**, terminally, and says both halves per
[ADR-0049](../../../adr/0049-an-unscored-match-is-an-evening-not-evidence.md): it is in your
history, in how much you have played, and in who you have now played with; it moved nobody's
level, nobody was penalised, and it was a counted match rather than a friendly.

## 6. The pad, per sport

`deltas/result-confirmation.md` §5 fixed *guided entry per sport, validated permissively* and
left the instrument open.

| Sport | Grid | Pad |
|---|---|---|
| padel, tennis | 3 × 2, `Set n` | 0–7 |
| squash | 5 × 2, `Game n` | 0–11 |
| badminton | 3 × 2, `Game n` | 0–21, over four rows |

A pad, not a stepper and not the system keyboard: §5's constraint is a score typed standing on
a court, one-handed, in the dark. A stepper is six taps to reach a 6; the system keyboard puts
a panel over the thing being typed and offers ten keys where the sport has eight legal values.
Keys are 44 × 44 with no `hitSlop`, which is the reachable-area rule met by the visual size
rather than around it.

**Badminton's pad is a different shape from the other three**, and that is chosen rather than
tolerated — see ADR-0060's Consequences for what was refused (a uniform 0–11 pad with a `+`
key, and a second instrument for badminton alone).

**Validation stays permissive.** A tie, an empty grid, a half-filled leg and a score with no
winner are declined; 7-6, 6-0, 15-13 and a timed 3-2 all pass, because they all happen.

## 7. Not settled here

- **The copy.** Client-owned. The four sentences ADR-0048 §10 names still carry unusual
  weight, and the two `cta` labels join them.
- **`cta` for `ready` and `cancelled*`** — §G Open Decision 8's other two groups, and now the
  open question the other 31 situations carry that they did not carry before.
- **What a result does to a level.** The rating context's, and its engine does not exist.
- **Nothing in the flow can say "no".** ADR-0048's own gap, untouched: a side that believes
  the match was abandoned rather than played has no move but silence.
- **Match chat.** Not required by this flow and deliberately not depended on.
