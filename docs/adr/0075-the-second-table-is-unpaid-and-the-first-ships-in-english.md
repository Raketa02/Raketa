# ADR-0075 — The second table is unpaid, and the first ships in English

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md) put the
sentence, the tag and the alarm on the client and carried `{situation, facts}` on the wire.
[ADR-0072](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md) took the
enumeration to **36** and added the alert strip as a fourth column of the same table. What was
never settled is where that table lives, what one entry looks like, which language it is written
in, and what makes a missing entry visible.

[#44](https://github.com/Raketa02/Raketa/issues/44) framed all of that around a duplication: *33
situations × copy, tag and tone — **on each client***, *"the largest single instance of
[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md)'s accepted duplication so far — two
tables kept in step by intent rather than by mechanism."* The hard question was therefore the drift
rule.

**There is no second table, so there is nothing to drift.**
[ADR-0040](0040-one-ladder-resolves-a-situation.md) already fixed that LIFE9 is *"neither blessed
nor retired… it will be written when a console screen asks for it, by the session building that
screen, off the 33"*, and that *"the console pays its 33-row table before it renders anything."*
The club console UI is out of scope on this map, and `frontend_club/src/features` holds nothing but
`_template`. ADR-0005's duplication here is **real but unpaid** — a cost a later effort meets, not
a mechanism this one owes.

**Four facts about the client that already exists.** `frontend_player/` has no i18n library, no
locale and no copy file; its ~30 shipped onboarding screens are English strings inline in JSX.
`ratingFormat.ts` writes comma decimals and calls them *"a house convention, not a localisation —
when the app is genuinely localised it becomes one, in one place, which is here."*
`bandPresentation.ts`, `sportPresentation.ts` and `difficultyTag.ts` are already
`Readonly<Record<Key, string>>` lookups with a documented *matched, not parsed* fallback — the same
tolerance [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) requires when an old
phone meets a 34th situation. And their key unions are **hand-written in `theme.ts`**, not taken
from `src/generated/schema.d.ts`, so nothing in this client can currently fail to build when the
contract grows.

**ADR-0041 says "Polish first."** Every other authority says English: both UI documents, the v37
prototype, the specification set's own quoted sentences (`Court held`, `Rescue active`, *"30 zł on
its way back to your card"*), and the shipped app. The clause sits inside a decision about copy's
*home* and was never argued.

## Decision

**One table, in the player app, and the console's is a later effort's cost.** We record ADR-0005's
duplication here as *unpaid* rather than as a mechanism to build. The only thing the player's table
owes a future console table is the `situation` enum itself, which is the wire contract and is owned
by the backend.

**The copy ships in English, and ADR-0041's "Polish first" is narrowed to nothing.** ADR-0041 is
right that copy is the client's and right about why; it is wrong only in an aside about which
language the client writes first, and the shipped app has contradicted that aside for its whole
life. ADR-0041 is **not edited** — accepted records are immutable, and the #38 precedent stands —
it gains a scope note pointing here.

**We take the honest cost with it: these 36 sentences will be *rewritten* in Polish, not
translated.** *"30 zł on its way back to your card"* against *"30 zł credit at {club}"*, the refusal
of **dispute** in favour of **propose a modification**, a counting noun that must say *seats paid*
against *shares paid* against *played* — these are editorial judgements, and whichever language we
do not pick, they are authored twice.

**No i18n mechanism and no library.** Not on cost: an i18n library's unit is a *string with
placeholders*, and the entry shape below rejects that unit for reasons that have nothing to do with
translation. Adopting the library now would bake in the shape we are rejecting.
`ratingFormat.ts`'s deferral is honoured as written — when the app is localised it becomes one
place, and the table is that place.

**Three tables, one per key space, colocated under `frontend_player/src/features/now/`.** They
share a shape and not a key:

| Table | Key | Entry |
| --- | --- | --- |
| Situations | 36 `situation` values | sentence, tag, tone, alert — × three audiences where the sentence differs |
| Fit reasons | 10 `TermCode`s | sentence, plus the withheld-badge line |
| Hold reasons | 5 named reasons | sentence, from a reason and its numbers |

They are **not** merged into one table over a union of unions, because that key type would be
assembled by hand — the very thing the completeness rule below exists to avoid. The result route's
screen copy ([ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md)) imports
from here rather than promoting the vocabulary to `shared/`: the situation vocabulary is Now's,
and one cross-feature import is cheaper than inviting the console's table to land beside it later.

**One entry is a function, not a template string.** `(facts, audience) => { sentence, tag, tone,
alert }`, typed against that situation's own fact payload; the tag and the tone stay plain values,
and only the sentence needs the function. A template string cannot be type-checked against its
payload, and [What a card carries](https://github.com/Raketa02/Raketa/issues/42) already found the
case that breaks it: *"a counting noun on every card — 3 of 4 stops meaning one thing across the
screen… It cannot be templated from one string."* The three audiences are ADR-0072's — in the
match, looking in, and the leaver, whose departure rides beside the situation as its own payload.

**Completeness is a typecheck, and tolerance is a runtime fallback. They are different mechanisms
for different moments.** Each table is `Record<ItsOwnGeneratedEnum, Entry>` keyed on the union
`openapi-typescript` emits from `backend/openapi.player.json`, so a value added to the contract
without its sentence **fails `pnpm typecheck` in CI** — no test to write, no lint to maintain, and
it rides the `make gen-api` machinery and the contract-drift check that already exist. The runtime
fallback stays anyway, because ADR-0070 is about an *installed* phone that cannot be forced to
update, which no typecheck reaches.

**This places a requirement on the backend**: `situation`, `TermCode` and the hold reason must be
emitted as **enums** in the OpenAPI document, not as bare strings. A bare string makes the key type
`string`, and the exhaustive `Record` degrades silently into an index signature that never fails.

**Copy the server composes is copy the player reads outside the app.** That is the one exception to
ADR-0041's *the sentence is the client's*, and it is stated **by class, not by count**. Today it is
exactly one sentence — ADR-0052's *a seat you asked for is free* — and that count is a consequence
of the push scope, not a rule. It is also the honest reading of ADR-0070's *"the server holds no
Polish"*: that rule is about the composed screen, where the server sends a shelf code and never a
caption, and it was never about a lock screen the server has to draw on its own.

**What this decision does not cover, named rather than dropped.** [#44](https://github.com/Raketa02/Raketa/issues/44)'s
corpus list was written before the push scope hardened and before its siblings were charted. The
`cta` labels belong to [The other thirty-one buttons](https://github.com/Raketa02/Raketa/issues/50).
Two of [#18](https://github.com/Raketa02/Raketa/issues/18)'s four owner messages — at the club's
cancellation deadline, and before the charge — reach an owner who is not in the app and have **no
delivery channel in v1**; the other two are private-court booking-flow screens. The result flow's
four sentences and one refusal are v1 copy, on ADR-0060's route.

## Consequences

**Easier**

- **The drift rule the ticket was written to find does not have to be built.** One table, and the
  mechanism keeping it honest is a typecheck that already runs.
- **A contract change cannot ship a blank status line into the repo.** Adding a situation without
  its sentence breaks CI, in the same pass that already regenerates and diffs the contract.
- **The entry shape is the repo's own.** `bandPresentation.ts` is the precedent for the lookup and
  for the fallback; nothing here is a new idiom for a build agent to learn.
- **Widening push later adds rows to a home that exists.** Stating the server-copy exception by
  class means #18's deadline message needs a channel, not an ADR.

**Harder**

- **We ship an English app for a Polish market**, and the 36 sentences are authored twice when
  Polish arrives. This is the deliberate cost, taken because v1 is pre-release — [#37](https://github.com/Raketa02/Raketa/issues/37)
  records the Apple membership as a store-release cost the product owner deferred, so no Polish
  player sees this build.
- **ADR-0041 now reads misleadingly on its own.** Its "Polish first" clause survives in the file and
  is only corrected by a scope note; a reader who greps for the language finds the wrong answer
  first. That is the price of immutability and it is the right price.
- **The typecheck is only as good as the backend's enum.** If `GET /now` emits `situation` as a
  string, the completeness rule silently stops working — and, exactly as `make test-hooks` says of a
  guardrail, a mechanism that quietly stops matching is worse than none.
- **One cross-feature import**, from the result route into `features/now`. ADR-0009's feature-first
  shape tolerates it; a third reader would be the signal to promote the tables to `shared/`.

**Neutral**

- **The club console's table is not deferred work, it is unstarted work.** ADR-0040 already fixed
  that it starts from a blank page off the 36. Nothing here changes what it will cost.
- Tone still resolves to a colour on the client against the surface it lands on (ADR-0041), and the
  alert strip is still a total function of the situation (ADR-0072). This record moves neither.
- The strings themselves remain build work. What a build agent no longer has to decide is the
  language, the home, the shape of an entry, and what fails when one is missing.
