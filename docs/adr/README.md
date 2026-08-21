# Architecture Decision Records

Each ADR captures one significant architectural decision: the context and forces, the
decision, and its consequences. They are **immutable once accepted** — to change a
decision, add a new ADR that supersedes the old one. Don't rewrite history; the reason a
past decision looked right is itself information.

## Convention

- Files: `NNNN-short-kebab-title.md`, numbered sequentially from `0001`.
- Format: [Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — see [`TEMPLATE.md`](TEMPLATE.md).
- Status: `Proposed` → `Accepted` → (`Superseded by ADR-XXXX` | `Deprecated`).
- **One sequence for the whole repo.** There are no per-app ADR directories: a decision
  that appears to affect one app usually constrains the others, and one numbered
  sequence is easier to reason about than three.

ADRs **0001–0004** were captured **retroactively** from the existing backend
implementation, so the baseline is documented. **0005–0009** are the decisions made when
the repo became a three-app monorepo.

## When to write one

Write an ADR when a choice would be expensive to reverse, when you had to argue yourself
out of the obvious alternative, or when a future reader would otherwise assume the
current shape was accidental. Don't write one for a naming preference.

If your work **contradicts** an existing ADR, surface it rather than silently overriding:

> _Contradicts ADR-0006 (backend owns the contract) — but worth reopening because…_

## Index

- [0001 — Clean / hexagonal architecture on the backend](0001-clean-hexagonal-architecture.md)
- [0002 — Event-sourced User aggregate](0002-event-sourced-user-aggregate.md)
- [0003 — Transactional outbox for event delivery](0003-transactional-outbox-for-event-delivery.md)
- [0004 — JWT access tokens with rotating refresh tokens](0004-jwt-access-with-rotating-refresh-tokens.md)
- [0005 — Three-app monorepo with enforced ownership boundaries](0005-three-app-monorepo-ownership-boundaries.md) — *re-examined and upheld by 0021*
- [0006 — The backend owns the API contract](0006-backend-owns-api-contract.md) — *amended to two documents by 0016*
- [0007 — Club web: BFF with an httpOnly-cookie session](0007-club-web-bff-httponly-cookie-session.md)
- [0008 — Player mobile: secure-store tokens, direct to the API](0008-player-mobile-securestore-direct-api.md)
- [0009 — Feature-first Clean Architecture on both frontends](0009-feature-first-clean-architecture-frontends.md) — *narrowed to the player app by 0014*
- [0010 — Local-first development; AWS deployment deferred](0010-local-first-development-aws-deferred.md)
- [0011 — A locked design system for the club console](0011-club-console-design-system.md)
- [0012 — A locked design system for the player app](0012-player-app-design-system.md)
- [0013 — Player app: the production runtime architecture](0013-player-app-runtime-architecture.md)
- [0014 — The club console follows its production architecture standard](0014-club-console-production-architecture-standard.md)
- [0015 — Engines as a pure, versioned layer](0015-engines-as-a-pure-versioned-layer.md) — *the kernel's negative space and constant homes added by 0022*
- [0016 — A modular monolith with two API surfaces](0016-modular-monolith-two-api-surfaces.md)
- [0017 — Assessment and SkillRating are event-sourced](0017-rating-context-event-sourced.md) — *its irreversibility rule superseded by 0020*
- [0018 — Aggregate repositories over the event store](0018-aggregate-repositories-over-the-event-store.md)
- [0019 — Assessment stream ids are derived from (player, sport, attempt)](0019-deterministic-assessment-stream-ids.md)
- [0020 — Revising an assessment answer truncates the transcript and replays](0020-revisable-assessment-answers.md)
- [0021 — The kernel lives in the backend; clients derive only by comparison](0021-kernel-in-backend-clients-derive-by-comparison.md)
- [0022 — What the kernel is not, and where a constant lives](0022-kernel-negative-space-and-constant-homes.md)
- [0023 — Money is integer grosze, gross, and a court price is a whole number of złoty](0023-money-integer-grosze-gross-whole-zloty.md)
- [0024 — An Instant is an aware datetime; engines compute in integer minute coordinates](0024-instant-as-aware-datetime-minute-coordinates.md)
- [0025 — A counted match's pairing is elected before commitment and fixed after](0025-binding-pairing-for-counted-matches.md)
- [0026 — Two matchmaking engines, one snapshot input contract](0026-matchmaking-engines-snapshot-input-contract.md)
- [0027 — Fit and certainty are separate numbers, and ranking a list is policy](0027-fit-and-certainty-are-separate-ranking-is-policy.md)
- [0028 — Four environments, one typed configuration](0028-four-environment-model-and-typed-configuration.md) — *renames the dev compose file to `docker-compose-local.yml`; 0010 names the old filename and stands as written*
- [0029 — Seed data goes through aggregates, and never runs in production](0029-seed-data-through-aggregates-never-in-production.md)
- [0030 — A departure is an audience, not a state](0030-a-departure-is-an-audience-not-a-state.md) — *its filler rule amended by 0033*
- [0031 — The hold ladder is a floor at a given level of certainty](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)
- [0032 — Order is a property of the composed screen, not of the match](0032-order-is-a-property-of-the-composed-screen.md)
- [0033 — A departure's settlement and its vacancy are independent](0033-settlement-and-occupancy-are-independent.md) — *amends 0030*
- [0034 — The Matches context is a record and keeps no history](0034-matches-is-a-record-and-keeps-no-history.md) — *the first racket-sport context to answer 0002's per-context question the other way*
- [0035 — A reservation is the only claim on a court, and it claims an interval](0035-a-reservation-claims-a-court-over-an-interval.md)
- [0036 — A UI document is final on the screen, not on the arithmetic](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)
- [0037 — The fit badge shouts once, and only about a seat](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)
- [0038 — Now is polled; the push is specified and deferred](0038-now-is-polled-the-push-is-specified-and-deferred.md) — *answers 0008's premise: no long-lived connection exists to outlive a token*
- [0039 — The card projection rebuilds from the record, so its consumer needs no partition](0039-the-card-projection-rebuilds-from-the-record.md)
- [0040 — One ladder resolves a situation; every other vocabulary projects off it](0040-one-ladder-resolves-a-situation.md) — *narrows 0021's cross-application contract suite: clients hold no ladder, so the generated enum is the fence*
- [0041 — Tone is editorial, so the wire carries a situation and its facts](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
- [0042 — A paid share returns to the seat's last funder](0042-a-share-returns-to-the-seats-last-funder.md)
- [0043 — Opening a court to strangers is the private path's commitment](0043-opening-a-court-is-the-private-paths-commitment.md) — *narrows 0030: the private path has no commitment deadline, but it does have a commitment act*
- [0044 — A marketplace seat is a promise of a game, not a share of a court](0044-a-marketplace-seat-is-a-promise-of-a-game.md) — *bounds the "a guarantee only ever decreases" invariant to the match's lifetime*
- [0045 — The owner's guarantee is the whole court, and a share is provisional coverage](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md) — *supersedes 0030's shrinking `guarantee`; dissolves the invariant 0044 was bounding*
- [0046 — One reconciliation, two hours after the reservation ends](0046-one-reconciliation-two-hours-after-the-reservation-ends.md) — *moves 0044's money event off the T−2h checkpoint; a private court has no checkpoint at all*
- [0047 — We hold no money, and a failed collection becomes a debt](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md) — *answers 0030's hold lifecycle by removing the hold*
- [0048 — Silence confirms a result, and disagreement must carry a score](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md) — *reverses `3.1` §1.4: an unanswered result now stands rather than being discarded*
- [0049 — An unscored match is an evening, not evidence](0049-an-unscored-match-is-an-evening-not-evidence.md) — *withdraws every Player Score movement in the post-play group*
- [0050 — Below the strip, Now is shelves, and every shelf makes one claim](0050-now-below-the-strip-is-shelves.md) — *supersedes `1`'s Parts 5 and 6 as sections, and `4` §3.5's six-card cap*
- [0051 — Now is ordered, never drawn: the list-builder's contract](0051-now-is-ordered-not-drawn.md) — *leaves 0027's licence to draw randomness unexercised; discharges 0037's open floor*
- [0052 — A vacancy is offered, and how loudly depends on how soon the match is](0052-a-vacancy-is-offered-not-announced.md) — *supersedes 0038's deferral of push, against a requirement that expires inside a day*
- [0053 — The phone holds no rules; its only power is subtracting](0053-the-phone-holds-no-rules-and-only-subtracts.md) — *0021's first concrete instance; refuses doc 5 A6's transition list and dissolves `3` §4.2's three-layer render*
- [0054 — Now refreshes when it is asked, never on a timer](0054-now-refreshes-when-asked-never-on-a-timer.md) — *supersedes 0038's 30-second polling cadence; read the two together to know how Now is delivered*
- [0055 — The Money context is event-sourced, with one stream per player](0055-the-ledger-is-event-sourced-one-stream-per-player.md) — *discharges the ledger 0034 leaned on; answers 0002's per-context question the opposite way to 0034, in the same effort*
- [0056 — A movement has two parties, and custody follows what was sold](0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md) — *corrects 0042's "paid at booking"; narrows 0047's "we hold no money" to the owner's liability; retires §H.5's `held` field*
- [0057 — Every movement names the rule that caused it, and a mistake is compensated](0057-every-movement-names-the-rule-that-caused-it.md) — *extends 0034's four-cancellation-flags argument to money; the enum is knowingly incomplete and owed by the wire contract*
- [0058 — A player has one balance, and in v1 it never goes above zero](0058-one-balance-and-it-never-goes-above-zero.md) — *completes 0047's debt; refuses the wallet, and puts one money line on Now*
- [0059 — The club's cash is on the ledger, and a mark that arrives too late is refused](0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md) — *closes 0046's "no new machinery" hole, which would have paid an owner out of money a club is holding*
- [0060 — A result is entered on a route, and the card that prompts it names the act](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md) — *draws the screens 0048 declined; discharges `UI` §B6.3's `cta`/`left` `[GAP]` for the two post-play situations that now write them*
- [0061 — The invitation ladder is an order, and one open call replaces the exclusive offer](0061-the-invitation-ladder-is-an-order-and-one-open-call.md) — *amends 0052: no exclusive hold, no waves; settles who "everyone else eligible" is, and moves the permission ask to onboarding*
- [0062 — A notification is a prompt to look, and Now is the only surface that states what is true](0062-a-notification-is-a-prompt-to-look-not-a-record.md) — *amends 0052: silent removal has no mechanism, so the wording carries the retraction; one live message per player, and no Inbox line*
- [0063 — Where a player plays is declared, never observed, and a distance is only as precise as the anchor](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md) — *discharges 0061's missing player location; overrides `UI` §B18's minutes-not-kilometres rule, the first override of a UI authority on a value it states*
- [0064 — A travel radius orders Now and bounds only a search, and an unmeasurable distance is missing evidence](0064-a-radius-orders-now-and-bounds-only-a-search.md) — *narrows 0027's "distance is never an exclusion" to the one surface where the player asked for a bound; makes a club's distance optional*
- [0065 — A seat you asked for pierces a Focus, and we send only when the named seat changes](0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md) — *narrows 0062's platform-parity rule to retraction and replaces its silent-update fallback; narrows 0052's permission binary with a third, readable state*
- [0066 — A declaration is one set per sport with two readers, and the ask for it is never furniture on Now](0066-a-declaration-is-per-sport-and-the-ask-is-never-furniture-on-now.md) — *upholds 0050 against the completion card 0063 promised; corrects `CONTEXT.md`'s "one declaration"; makes a constraint term three-valued and drops `profilePct` from a published contract*
- [0067 — The quiet replacement is evidenced, and the extra message it buys waits for APNs](0067-the-quiet-replacement-is-evidenced-and-the-extra-message-waits.md) — *lifts 0062's provisional rule on a proxy measurement, states the bar that made the proxy sufficient, and keeps the iOS count-refresh off until the APNs hop is measured*
- [0068 — Now is one request, and the caches serve the screen's two clocks](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md) — *replaces `4` §6.1's cache table: deletes the player feed cache ADR-0054 stranded, adds a shared new-arrivals set, and cuts 0050's undefended depths from 53 cards to 29*
- [0069 — The budget is two budgets, and both fail the build](0069-the-budget-is-two-budgets-and-both-fail-the-build.md) — *replaces `4` §6.2's table and gate; adds a payload ceiling the specification set never had, and narrows §5.5's degrade to the shelves that have a scorer*
- [0070 — Now is three regions, and a card has two halves](0070-now-is-three-regions-and-a-card-has-two-halves.md) — *draws the envelope 0068 left open: an offers region 0052 needed and nothing had made room for, a spine/situation split that lets an old phone lose a sentence rather than a match, and shelf titles as codes so 0041's copy rule survives 0066's server-composed caption*
- [0071 — Two fields with no reader are not forwards compatibility](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md) — *drops `serverTime` and `nextTransition` from 0038's four; narrows its rule to a named future reader, on the finding that neither client validates the wire at runtime so adding a field is free*
- [0072 — Two sentences are two situations, and a leaver is a third audience](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md) — *takes 0070's enumeration from 33 to 36: names the offers region 0052/0061 had no situation for, splits `formingLate`'s two opposite court answers, gives `privateFull` a rung, and moves the alert strip off the wire into 0041's client table*
- [0073 — A card counts money, and counts down to what happens anyway](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md) — *fills 0070's situation half for all 36; narrows 0048's `keepUntil` off `matchEnd`, completes 0057's cause enum, corrects the private owner's false "every share reduces what you guarantee", and prints a score where no engine can print a level movement*
- [0074 — The result route reads four facts, and an action off Now hands Now its update](0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md) — *draws the second reader 0060 created: refuses the proposal history 0034 had already refused, shows 0048's acceptance grace rather than lying about settlement, and settles that an action off Now returns Now's update because a pop back is none of 0054's four asks*
