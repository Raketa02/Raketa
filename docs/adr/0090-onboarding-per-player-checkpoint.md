# ADR-0090 — Onboarding is two parts, and the second one is per player

- **Status:** Accepted
- **Date:** 2026-08-25

> **Narrows an invariant in [`CONTEXT.md`](../../CONTEXT.md).** The rating context states
> *"There is no **onboarded player**."* That invariant is upheld for everything it was
> written about and narrowed for one new fact. The reasoning is the whole of this ADR, and
> the glossary now carries the narrowed form.

## Context

Onboarding is being extended with a second part after the Skill rating: social tags, photos,
an availability grid, a location, a search radius and a proposals opt-in
([ADR-0089](0089-player-profile-context-event-sourced.md)). That extension collides with an
invariant the rating context wrote deliberately:

> **There is no *onboarded player*.** Onboarding is not a state a player is in or out of; it
> is how a Skill rating comes to exist, and a rating is per sport. […] Anything that needs to
> know "has this player been through onboarding" is really asking "does a rating exist for
> this sport", and must ask it that way — a per-player onboarding flag would be a second,
> coarser truth about the same fact.

Read closely, that invariant bans one specific thing: **a coarse per-player proxy for a fact
that is genuinely per sport.** It is right, and nothing here weakens it. But its premise —
that everything onboarding produces is per sport — stops being true the moment onboarding
produces a Player profile, which is one per player and has no sport dimension at all.

**The concrete failure if nothing changes.** The entry gate today
(`features/onboarding/domain/entryDecision.ts`) is: an unfinished run outranks everything →
resume it; **no ratings at all → welcome**; otherwise → the app. A player who rates padel,
reaches the social steps and then kills the app **has a rating**, so the gate sends them
straight into the app — past the social steps, permanently, with no route back to them. The
matcher then holds the partial input set the source specification describes: every candidate
scores zero on the heaviest for-fun term, availability overlap is zero against everybody, and
there is no recorded consent to propose to them at all.

The alternatives considered:

- **Derive it from field emptiness** — treat "tags are empty and opt-in is null" as *not
  done*. This is the `user === undefined` mistake that `frontend_player/docs/architecture.md`
  bans by name, moved one level down: a state expressed as the absence of a value, which
  cannot distinguish *not yet asked* from *asked and still loading*, and which silently
  changes meaning the first time a field becomes legitimately clearable.
- **Make the second part optional** — never route back to it, prompt from inside the app
  later. Honest, and it leaves the matcher with a partial input set for every player who
  closed the app once. It also makes the opt-in unanswerable-by-default, and an unanswered
  consent that never gets asked again is the failure the opt-in screen exists to prevent.
- **Store a per-player `onboarding_completed` flag.** The thing the invariant actually bans,
  and it earns the ban: it would be true for a player with one rating and false for the same
  player mid-second-sport, which is a claim about sports dressed up as a claim about a
  person.

## Decision

We will model onboarding as **two parts**, and make **the part the checkpoint unit**.

- **Part 1 — the Skill rating.** Unchanged. A run resumes at its outstanding question with
  the transcript intact, exactly as [ADR-0019](0019-deterministic-assessment-stream-ids.md)
  and [ADR-0020](0020-revisable-assessment-answers.md) already provide.
- **Part 2 — the social steps.** Six steps over a **client-held draft**, committed to the
  server in **one idempotent POST at the end of the part**. Nothing is written before that
  commit, so leaving mid-part restarts at step 1.
- **The entry gate gains a fourth destination.** It becomes: unfinished run → resume · no
  ratings → welcome · **ratings but no Player profile → the social steps, from step 1** ·
  otherwise → the app. The new branch reads *does a Player profile exist*, which is a
  genuinely per-player question with a per-player answer, served as a field on
  `GET /api/v1/users/me` rather than as a second round trip.
- **`CONTEXT.md`'s invariant is narrowed, not dropped.** The banned thing is a per-player
  flag standing in for a per-sport fact. A Player profile is not that: it is one per player
  because its contents are facts about a person, and asking whether it exists is asking
  exactly what it answers. The invariant's own test — *"is this really asking whether a
  rating exists for this sport?"* — returns no here, and that is the test that decides it.
- **Back and forward move freely inside each part and never cross between them.** Social step
  1 carries no back control, the same way question 1 carries none —
  `questionNavigation.standingPosition` already clamps its floor at position 1, so this is one
  rule applied at the next boundary rather than a new rule. Two things make the boundary
  hard: walking back past a commit makes an idempotency key meaningless, and walking back into
  a rated assessment's review would break *"an answer is revisable for as long as its run is,
  and no longer."*

The **asymmetry between the two parts is deliberate and is the point.** Part 1 resumes
mid-run because eight adaptive answers are expensive and the event-sourced transcript already
survives a reinstall. Part 2 restarts because six short steps are cheap, and buying resume
for them would mean a server-owned draft with a version token — a second aggregate, before a
single player exists, to protect work measured in seconds.

## Consequences

**Easier**

- The gate stops having a hole in it. There is no longer a sequence of taps that strands a
  player in the app with a rating and no profile, and no migration later to find the players
  it stranded.
- The rule that decides where a player belongs stays a pure function with one more branch —
  testable without mounting anything, which is the property `entryDecision` was built for.
- Part 2 needs no draft persistence, no version token and no two-device reconciliation,
  because there is nothing on the server to reconcile until the part ends.

**Harder**

- **The entry gate now depends on a second fact from the server**, so a cold launch that can
  read ratings but not the profile flag has to decide what to do. It must fail toward *not
  routing into the app*, which means a player on a bad connection can see a retry rather
  than their home screen.
- **A player can lose up to six steps of answers** by killing the app at step six. This is
  the accepted cost of the client-held draft, and it is the first thing to revisit if it
  turns out to bite — the fix is the server-owned draft this ADR declines to build now.
- **`CONTEXT.md` now carries a narrowed invariant**, which is strictly harder to apply than
  the flat one it replaces. A future context has to ask the test question rather than read a
  prohibition, and someone will get it wrong. The test is written into the glossary beside
  the invariant for exactly that reason.
- A profile with zero ratings is now representable. The flow cannot produce one — part 2 is
  only reachable after part 1 — but the gate must not assume it away, or it loops.

**Neutral**

- The onboarding pass (`features/onboarding/domain/onboardingPass.ts`) is untouched and stays
  client-only and in-memory. It measures a walk through part 1; part 2 has one step sequence
  and no queue, so it needs nothing from it.
- Nothing about this makes onboarding re-takeable. A player still cannot re-enter it from
  inside the app, and the profile is edited from the profile screen instead — which is why
  [ADR-0089](0089-player-profile-context-event-sourced.md) puts the rules in a feature both
  can reach rather than inside onboarding.
