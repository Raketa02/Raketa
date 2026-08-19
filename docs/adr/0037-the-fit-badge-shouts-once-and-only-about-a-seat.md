# ADR-0037 — The fit badge shouts once, and only about a seat you can take

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

Every match card on Now carries one small pill — `✦ 87` — and it is the most opinionated
element on the screen. `1-now_screen_production_spec.md` §2.2 states the rule the screen is
built on:

> **This is the rule the whole screen rests on.** A colour used for two things is a colour that
> means nothing. … **Coral is never decorative.** If coral appears on this screen and the player
> is not being pointed at a thing they own or an action they can take, that is a bug.

Four hundred lines later, §3.9 turns that pill coral at 90+, justified because *"a 90 is rare
and means drop what you are doing"* — and §2.2's own table of licensed coral uses lists
`.fit.hi` immediately before stating the rule that excludes it. The contradiction is inside one
document, which is why `now-section-domain-spec.md` §A.0's tie-breaker cannot resolve it, and
why doc 5's finding E2 could only name it.

Four measurements decide it. All are from `Raketa02/Raketa#6` and this ticket's own execution of
the shipped engine.

- **A 90 is not rare.** **4,3 %** of 80 000 realistic scores reach 90, and the top of the range
  is 100, not the specified 99.
- **A list selects for the maximum.** Cards are ordered by fit, so the top card holds the highest
  score on the board. Coral gated on the score alone would therefore appear on the first card in
  most sessions — repeating, in the screen's only loud colour, what position had already said.
- **One score in twelve above 90 is barely measured.** Of the draws reaching 90, **276 of 3 436
  (8,0 %)** sit at 48 % coverage — an empty court with four of ten terms excluded.
- **A full match outranks the joinable version of itself.** The same four players with one seat
  open score **91**; with every seat sold they score **94**, because being full is the strongest
  available evidence that the match will actually be played, and viability is the one term that
  can never be excluded. So `1-now_screen_production_spec.md` Part 6's *"full, but worth waiting
  for"* lane — a real product, because the Rescue cascade needs a standby pool — is where the
  **highest** scores live, and the loudest badge on the screen would land on a match with no
  seat to take.

Two further facts bound what may be decided. The badge's range as specified is violated at both
ends by the engine that feeds it (measured **8 to 100**, with 175 of 60 000 draws below 20).
And the UI specification's own open-decisions table, entry 9, does **not** decide the trigger:
it recommends *"trigger on fit × coverage, not score alone; if coverage is unavailable at
launch, drop `.hi` entirely rather than break the coral rule"* — so this decision was delegated,
not overruled ([ADR-0036](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)).

The alternatives considered:

- **Gate on the score alone, as specified, and amend §2.2 to license the badge.** Cheapest, and
  it spends the rule the whole screen rests on. An exception written into that rule is how the
  rule stops being one, and the thing bought is a pill that duplicates position.
- **Drop `.hi` entirely** — the UI document's own fallback. Honest, and it discards a real
  signal: *"the best of what is here"* and *"this is exceptional"* are different facts, and
  ordering can only ever say the first.
- **A third band**, between night and coral. Refused by `rakieta-now-section-ui-spec.md` §B9:
  *"Two bands only. There is no third."* — a value it is final on.
- **Show coverage to the player as a second number** so they can judge thinness themselves.
  ADR-0027 already priced this: *"two numbers are harder to explain than one, to a reader of the
  code and to a player."* A card must be decidable at a glance.
- **Three gates and a per-screen cap.**

## Decision

We will make the badge's emphasis mean **take this seat now**, and make that meaning
structurally hard to dilute.

- **The badge always prints a number, clamped to 20–99 at display time.** The engine keeps its
  0–100 range and the true value ranks the list; the pill never shows 8 or 100. This honours the
  specified range and relocates it from the arithmetic to the display, which is where its two
  product reasons always lived — *"a score of 3 is not more useful than a score of 20 — both
  mean no"*, and never 100 because certainty is never warranted. It is **the same rule the
  rating context already holds**, where Confidence is capped at 99 because *"the platform cannot
  claim total certainty about anybody."* One principle, second application.
- **Coverage is never shown to the player as a number.** It ranks, it gates emphasis, and it may
  become *words* in a reason line (*"early days for this match"*). It never becomes a second
  gauge on the card.
- **A card is emphatic only when all three hold:** fit **≥ 90**, coverage **≥ 80 %**, and **a
  seat is open**. The coverage floor removes exactly the thin population and nothing else; a
  floor above 86 % could not fire at all today, because two terms ship dark for lack of data,
  and a guard that cannot fire is one nobody should watch.
- **At most one card per screen is emphatic.** This is the structural guarantee, not the
  threshold: whatever the score distribution does as real data arrives, coral cannot become
  wallpaper.
- **The server decides which card is emphatic, and ships the flag.** Emphasis depends on the
  other cards, so it is a property of the composed screen and not of one card — the identical
  argument [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) already made for
  order. The client renders what it is told and never recomputes.
- **The badge is omitted for a viewer with no rating in that sport.** The specified rule keyed on
  a null score the engine never returns; the behaviour is kept and the key corrected to a fact
  about the player, which the client already holds. Skill overlap is the largest term at 24 of
  100 points and is the one thing missing for such a viewer, so printing 91 to a player the
  platform cannot place is the flattery-through-absence ADR-0027 exists to remove — arriving
  through presentation, since the player cannot see coverage. The score still ranks their list;
  only the claim is withheld.

With these, **§2.2 survives unamended**: an emphatic badge points at a seat the player can take,
which is an action they can take.

## Consequences

**Easier**

- The pill now says something ordering cannot. *"First"* and *"exceptional"* stop being the same
  claim, and the loud colour keeps one meaning across both of Now's lanes.
- The rule the screen rests on needed no exception, so the next designer inherits it intact.
- Part 6's waitlist lane can carry the identical card component with no second colour language:
  its cards score higher and are quieter, which is the honest ordering of what the player can do
  about them.
- Retuning the trigger is a server change. Neither client ships a release for it, and the two
  clients cannot disagree about which card is loud.

**Harder**

- **Three gates and a cap are four things to explain**, where the specification had one
  comparison. *"Why is this 94 not coral?"* has three possible answers, and support will be
  asked it.
- **The display clamp makes two scores indistinguishable at each end.** A 12 and a 19 both print
  20. This is deliberate and it is still a loss of information the player cannot recover — and it
  is only defensible while the ranking layer keeps a 12 off the screen, which is a floor not yet
  decided.
- **The coverage floor of 80 % is a hypothesis with no measurement behind it.** It was chosen
  because it removes the measured thin population and clears the reachable ceiling of 86 %; it is
  not a tuned number, and it will need one once reliability and familiarity have data.
- **The one-per-screen cap makes emphasis order-dependent**, so a card that was coral before a
  refresh may not be after it, with nothing about that match having changed. Under ADR-0032 this
  can only happen on open or refresh and never under the player's thumb, which is what makes it
  tolerable rather than what makes it invisible.
- **An unrated viewer loses the badge on every card**, which is the cohort with the least ability
  to judge a match for themselves. The compensation is copy the specification already wrote —
  *"Finish your rating and we can tell you which matches are even."*

**Neutral**

- No line of `backend/app/engines/` changes. Clamping, gating, capping and omission all live in
  the response shape, the ranking layer and the client.
- The badge's geometry, type, tones and two-band rule are untouched, and remain final in
  `rakieta-now-section-ui-spec.md` §B9.
