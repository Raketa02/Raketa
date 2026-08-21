# ADR-0060 — A result is entered on a route, and the card that prompts it names the act

- **Status:** Accepted
- **Date:** 2026-08-21
- **Resolves:** [`Raketa02/Raketa#24`](https://github.com/Raketa02/Raketa/issues/24)
- **Discharges:** `rakieta-now-section-ui-spec.md` §B6.3's `[GAP]` — `cta` and `left` read
  and never written — for the two post-play situations that now write them

## Context

[ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md) settled the
rules of the result conversation and deliberately declined to settle the screens. That left
the harder half: **with no chat, three interactions are the entire conversation between four
people who disagree about what happened.** Entering a score, being asked whether it is right,
and proposing a different one are all there is.

Three shapes were built on the real kit and compared, on branch
[`prototype/result-confirmation`](https://github.com/Raketa02/Raketa/tree/prototype/result-confirmation):
the conversation happening **in the Now card**, in **a sheet over Now**, and on **a route of
its own**. Building them surfaced two facts that decide it, neither of which is about taste.

**The state card's action row holds one action.** `UI` §B6.3 gives `stateCard` a single CTA
plus two icon buttons, and `confirmResult` needs two real actions — accept, and propose a
modification — because ADR-0048 forbids a bare rejection, so the second action is not
optional. The in-card variant can only find the room by spending the `⌘` access button that
the `post` flag already drops, which is the card's last spare slot for a situation that is
not the last one to want a second action.

**Entry is typing, and the card is for reading.** A guided per-sport pad inside a night card
runs the card past a 320pt screen on its own — and Now is *a status surface before a search
box*, where reading is the primary act. `deltas/native-kit.md` §3 already accepted that the
fullest card overflows; making the card the place a player types turns an accepted overflow
into the normal case.

Against those, the route's cost is real and was weighed: **a player is taken off Now to
answer a card that was on Now**, and the screen is empty for almost all of its existence.

## Decision

**The result conversation is a route.** The Now card prompts it and is a tap target; the
route is where a score is entered, confirmed, or modified.

**The card names the act, and is the first thing in the model to do so.** `needsResult` and
`confirmResult` set `cta`; the other 31 situations keep the `Open match` fallback. The label
distinguishes the two moments — *enter a score* against *answer one* — and the whole card and
its button resolve to the same route, so the tap target for these two situations is the
result route rather than the match screen. **The strings are placeholders**: copy is
client-owned and still in fog, and what is decided here is that a per-situation label exists
and that these two situations carry one.

**The route renders by situation, not by a screen identifier.** Entry, the two audience
renderings of a live proposal, the counter, and the unscored ending are one route resolving
the same situation the card resolved — which keeps
[ADR-0040](0040-one-ladder-resolves-a-situation.md)'s rule intact rather than introducing a
second vocabulary for screens.

**The state moves on the server.** At `matchEnd` the backend derives `needsResult`, and the
card shows it the next time Now is composed.
[ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) and
[ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md) are unchanged: no clock on the
phone, and nothing ticks the card into a new state.

**One side enters and the other side confirms, and that settles it.** This is sufficiency,
not necessity — ADR-0048's silence rule stands underneath it, so a confirmation ends the
window early and is never required for a result to count.

**A score crosses the wire per side, never as a display string.** The specification set
hardcodes `"6-4, 3-6, 6-2"` in every document and nowhere says whose 6 it is. With four
people and two sides an unlabelled string is unusable, so every surface that shows a score
names both sides, and the viewer's side is always first.

**The unscored ending gets the route too**, terminally: what the evening counted for
(history, how much a player has played, who they have now played with) and what it did not
(nobody's level moved, nobody was penalised, it was not a friendly), per
[ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md).

**On the confirm screen the countdown is the hero.** The remaining time is the largest figure
on the screen, next to the sentence that says nobody has to do anything. Silence is what
settles this result, so the screen that asks for a tap has to say what happens without one —
loudly enough that a player who taps nothing has still been told.

**The pad is per sport.** Padel and tennis get 0–7, squash 0–11, badminton 0–21 over four
rows. The instrument is a pad rather than a stepper or the system keyboard because §5's
constraint is a score typed standing on a court, one-handed, in the dark.

## Consequences

**The player app commits to its second screen.** Now was the only one this map had planned;
the result route is the first thing it adds, and it is the tap target for two of the 33
situations. Anything later that wants a result — a match detail screen, a history list — has
a route to send a player to rather than a mechanism to invent.

**`cta` stops being dead mechanism, and that opens a question that used to be closed.** While
no situation set it, "which contexts deserve a second action" was uniformly answered by the
fallback. Two situations now answer it differently, so the remaining 31 each carry an open
question they did not carry before. That stays in the map's fog; this ADR does not pre-empt
it, and the fallback remains correct until a situation argues its way out of it.

**Score-per-side propagates to the wire contract.** `GET /now`'s `facts` payload cannot carry
a formatted score, and neither can whatever the result route reads. The display string is a
client formatting of a structured value, in both clients, which is the copy duplication
[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md) already accepts.

**A player leaves Now to answer something Now asked.** Accepted, and recorded as the price:
the act is typing, not reading, and Now's job is to say what needs you rather than to be
where everything happens. If the return path is ever wrong — landing a player somewhere other
than the Now they left — that is a defect of this decision, not of the router.

**Badminton's pad is a different shape from the other three.** Four rows against two pushes
the actions down the screen on the sport with the widest range. Chosen over a uniform 0–11
pad with a `+` key because making a badminton player tap `+` ten times to record a 21 is a
worse instrument than a taller one, and over a second instrument because two ways to type a
score in one app is a support problem.

**The route is empty most of the time it exists.** It has a reason to open for at most 48
hours after a match and none at all before one. That is not a cost anybody pays at runtime,
but it is a screen with no other job, and a later effort that finds one for it should say so
rather than quietly widening this one.

**Not decided here.** The copy — client-owned, and the four sentences ADR-0048 §10 names
still carry unusual weight. What a result does to a level: the rating context's, and its
engine does not exist. Match chat: not required by this flow and deliberately not depended
on. And ADR-0048's own gap stands untouched — **nothing in the flow can say "no"**, so a side
that believes the match was abandoned rather than played has no move but silence.
