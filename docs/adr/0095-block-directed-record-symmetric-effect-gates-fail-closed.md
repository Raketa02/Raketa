# ADR-0095 — A block is a directed record with a symmetric effect, and a safety gate that cannot be evaluated excludes

- **Status:** Accepted
- **Date:** 2026-08-26
- **§2's event table, §3, §7 and §8 amended 2026-10-06 by [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)**: a block keeps two people
  off one court, and groups, Members lists, the record and chats already shared are untouched. It
  takes back the blocker's yeses where the other person is In until the club confirms, and never
  touches a confirmed booking. A response may carry the reader's own blocks, never anyone's block
  of the reader. No surface is recorded (`blocks.player_blocked` v2). §2's *neither party can ever
  discover which way it went* now holds of the blocked party only.
- **§7's *rankings … inherit this rule when they arrive* honoured 2026-11-07 by
  [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)** §8. Rankings arrive, and a blocked pair, either way round, never sees each other's
  row in either view; neither opens the other's record, anywhere. The prototype's *"you disappear
  from each other's … rankings"*, which ADR-0193 called false, holds of the ranking. A dated note
  marks §7.
- **§7 narrowed for the ranking 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)** §2: the ranking, Top 10 and a group
  sheet show a blocked pair to each other, because each is a fact about everybody, not a suggestion;
  a tap on the other reads *This record isn't available*. **Home's people rows** — the surfaces that
  suggest one player to another — keep the pair out of each other's view, and there the promise
  holds. A dated note marks §7.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** The searches, the deck and the candidate index are gone (#579, #580), so §4's two enforcement points — the block set carried in the `SearchContext`, and the re-verify before a search response leaves — and §5's and §6's refusals at the search entry no longer exist. A block is now asked of every pair the proposer, the fill and a rescue would seat (`proposals`' `PlayerFit`, over `blocked_pairs_among`). *A gate that cannot be evaluated excludes* holds there, and in the account gates the player record runs, where `NoHoldsExist` still answers the hold. §1–§3 and §8 stand as ADR-0193 amended them.

## Context

The matchmaking engine applies eight gates before anything is scored
(`docs/specs/matchmaking/matchmaking-engine.md` *(removed)* §9.1).
Two of them read contexts this repository does not have: **a block, either direction**, and
**a held account** — somebody with an open unsettled case. Charting the map
[The matchmaking engine: who sits down, and why](https://github.com/Rakieta02/Rakieta/issues/155)
ruled a minimal block **inside** the destination while the other absent contexts stayed
outside it, for one reason: shipping a system whose entire job is putting strangers in front
of each other, with no control that lets somebody say *not them*, is a safety gap and not a
phasing decision. This record settles
[#159](https://github.com/Rakieta02/Rakieta/issues/159).

**What the input material already says.** The design document makes both gates "verified
live" (§7.5), keeps blocks and passes out of every response shape (§21), and proposes that
the matcher hold *advisory copies of all three live facts so it can rank on them*. The
prototype has shipped the promise in user-facing copy already
(`social-prototype-v1.html:3520`):

> *"Blocking works both ways — you disappear from each other's matchmaking, decks, radar and
> rankings, immediately and silently."*

Its store is a flat one-directional list; its settings screen offers unblock; and its **hold
points the other way from §9.1's**. `blockNew()` freezes *the holder of the case* out of new
commitments for fourteen days and deliberately leaves the chat with the person owed open —
*"a hold that stops you settling up is a hold that never ends"* — where §9.1 gates the
*candidate*. Both are the same fact read from two sides, and the document only writes down
one of them.

**What the repository has.** No `Block` anywhere, and no vocabulary for one in
[`CONTEXT.md`](../../CONTEXT.md). Two storage precedents: `modules/auth` is a plain table,
and `users`, `rating` and `player_profile` are event-sourced. ADR-0093 put the matcher in the
backend and fixed the rule that decides between them — **storage is chosen by what it costs
to lose.**

The alternatives considered and rejected:

- **A block list on `PlayerProfile`,** as a sixth preference beside tags, photos, availability,
  location and radius. Rejected on two counts. It mis-models — a block is not something you
  *prefer*, it is something that exists between two people — and it breaks GDPR erasure:
  erasing B would have to reach into A's profile stream and rewrite it, and every profile
  stream would carry other people's identities.
- **A plain table, not event-sourced,** following `modules/auth`. Rejected: *blocked,
  unblocked, blocked again* is safety evidence, and the wider reporting story — explicitly out
  of scope here — is the reader that will want it. It is also the one thing in this design a
  human would miss if it silently vanished.
- **One symmetric edge** rather than a directed record. Rejected: it makes unblock ambiguous
  the moment both parties have blocked, which is not an exotic case.
- **An advisory copy of blocks in the candidate index,** as §7.5 proposes. Rejected — see the
  correction below.
- **The held-account gate written into the consumer-driven contract and left out of the code**
  until `cases` exists. Rejected: an absent gate is an open door, not a standing-down signal.

## Decision

### 1. The block is its own bounded context, event-sourced, one stream per ordered pair

`backend/app/modules/blocks/`. One aggregate, `Block`, with **one stream per ordered
`(blocker, blocked)` pair** and a deterministic stream id derived from that pair —
ADR-0019's scheme, one dimension shorter. It is a thin context; so is `auth`.

### 2. The record is directed; the effect is symmetric

| Event | Durable name / version | Carries |
| --- | --- | --- |
| **PlayerBlocked** | `blocks.player_blocked` / v1 | `blocker_id`, `blocked_id`, `surface` |
| **PlayerUnblocked** | `blocks.player_unblocked` / v1 | `blocker_id`, `blocked_id` |

The moment is the event's own `occurred_at`, as everywhere else. **There is no reason field
and no free text.** If a reason ever matters, that is a *Report*, not a Block, and reporting
is out of scope.

`A → B` and `B → A` are two independent streams. If both have blocked and A unblocks, **B's
block still stands** — which is exactly why the direction is recorded even though neither
party can ever discover which way it went.

### 3. What a block is allowed to be

Any player may block any other from any surface where that player is visible, with no prior
interaction required. Unblock is immediate. Blocking is idempotent — blocking an
already-blocked player appends nothing, in the shape of `users`' `disable()`. Blocking
yourself is a domain error, not a no-op. **No cap, no cooldown, no rate limit:** friction on
the one control a person has, paid to solve a problem nobody has at eleven players.

Erasing a player under GDPR erases every stream they appear in, on either side of the pair.

### 4. Enforced in two places, and the candidate index holds no block data at all

§7.5's *the matcher proposes, the backend disposes* is confirmed. Its advisory-copy clause is
**corrected for blocks**:

1. **Generation.** The searcher's live block set — both directions, resolved at request time —
   travels in the `SearchContext` as `exclude_player_ids`, a field the internal contract
   (§16) already carries. Tens of rows, not a scan.
2. **Disposal.** The backend re-verifies the returned rows against live state before the
   response leaves, closing the window between step 2 and step 4 and covering the
   asynchronous surfaces — the deck, a standing-search notification — where that window is
   real rather than microscopic.
3. **Nothing ranks on a block.**

§7.5's advisory-copy argument is right about *open challenges* — five pending challenges
should lower a candidate long before they withhold one — and wrong about blocks, because a
block is binary and there is nothing to lower. Dropping the copy deletes a projection, its
staleness and its rebuild path, and buys nothing.

### 5. A gate that cannot be evaluated excludes

The document has `NoEvidence`: a term with no evidence stands down and the weights
renormalise (§10). A gate has no equivalent, and the difference is the whole point:

> **A term that cannot be evaluated stands down. A gate that cannot be evaluated excludes.**

At the search level, if the live block set cannot be resolved at all, the search **refuses and
returns unavailable** — it does not return unverified rows. This is §18's *index lag > 24 h →
refuse* applied one level up, and it is the sentence that stops somebody later "fixing" a
flaky query by defaulting it to empty.

### 6. On day one nobody can be held, because nothing can hold anybody

The held-account gate ships **wired and correct**, not deferred and not skipped. There is no
`cases` context, therefore no mechanism can place a hold, therefore no account is held: the
gate passes everybody *because it is true over an empty set*. It is not a `NoEvidence` case
at all.

It reads an `AccountHoldQuery` port with exactly one adapter today, named **`NoHoldsExist`**
— deliberately not `NullAccountHoldQuery`, because *null* reads as *not wired yet* and this
adapter is asserting a fact. A test asserts the gate sits in the pipeline and that an adapter
which reports a hold actually excludes.

**The gate points both ways.** §9.1's candidate-side gate stands, and the prototype's
searcher-side hold is adopted with it: **a held searcher is refused at the search entry
point**, with an honest reason and a route to the case. Returning an empty city to somebody
the platform has stopped is the product lying about why they see nothing — the exact failure
the engine's three refusals exist to prevent, and running the search only to refuse the
challenge at send time wastes their time and then embarrasses them.

What `cases` must answer, and how fast, is written into
[What the matcher demands of `player_score`, `matches` and `cases`](https://github.com/Rakieta02/Rakieta/issues/163)
as a consumer-driven contract, not here.

### 7. How far the promise reaches

**Sideways — everywhere.** A block removes each from the other's view on **every surface where
the platform shows one player to another**: the ranked shortlist, the engine's line-up, the
deck, any standing-search notification, and the reciprocal-fit pass. One `BlockQuery` port is
the single place that question is asked, and every people-listing surface consults it. Radar
and rankings do not exist in this repository and are out of scope, but they inherit this rule
when they arrive rather than each re-deciding it — the prototype has already promised players
they will.

> **Note — 2026-11-07, [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) §8.** Rankings
> arrived and inherited it: a blocked pair never sees each other's row, in General or Friends, and
> places don't renumber.

> **Note — 2026-11-14, [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** The ranking stops inheriting it: the ranking is the true
> ranking, and a blocked pair sees each other's rows, with each other's record refused. Home's three
> people rows inherit it instead — a blocked pair never appears in each other's — and so do their See
> all screens.

**Backwards — not at all.** A block is forward-looking. It does not reach into a game already
agreed or a chat already open, because `matches` does not exist to define what cancelling one
would mean, and today no game can exist, so the question has no live consequence. The demand
goes to [#163](https://github.com/Rakieta02/Rakieta/issues/163) with the expected answer
recorded and not decided: a block should cancel an *unaccepted* challenge and leave an
*agreed* game to the humans, mirroring the prototype's reasoning about the chat it refuses to
close.

### 8. Silent to both parties, and unrepresentable in a response

Neither party is ever notified, and the other side sees no trace anywhere in any response.
§21's existing rule — *a test asserts no response shape can carry a decline* — is extended to
blocks and holds by the same test.

## Consequences

**Easier**

- The one control that makes the product safe to ship exists from the first search, rather
  than arriving with a moderation system nobody has scheduled.
- A whole projection, its staleness window and its rebuild path never get built. The matcher's
  index stays what ADR-0093 said it was — a rebuildable picture of the city with nothing
  safety-critical in it.
- The gate/term pair gives every later gate a default. #163, #166 and the relaxation ladder
  each inherit an answer to *what if we cannot tell* instead of re-deriving one.
- Swapping `NoHoldsExist` for a real adapter is the entire integration when `cases` lands.
  The gate, its test and its position in the pipeline are already right.

**Harder**

- **A fourth bounded context for one aggregate and two events.** Its own repository, catalog
  registrations, deterministic id function and wiring, all for a pair and a moment.
- **A safety gate on the live request path.** The search now has a dependency it refuses
  without, so a slow or flapping block query is a full outage of the feature rather than a
  quality degradation. That is the correct trade and it is still a cost.
- **A held searcher is refused at the entry point**, which means the entry point needs to know
  about holds — a coupling from the search surface to a context that does not exist yet, held
  open by a port with one adapter for as long as `cases` takes.
- **Two independent streams per blocked pair.** Reading *is anybody blocked here* is two
  lookups or one query over both columns, forever, and every new people-listing surface has to
  remember to ask.

**Neutral**

- §7.5 and §9.1 are amended rather than discarded: the resolution and the live re-verify
  survive intact; the advisory copy is dropped for blocks only, and the searcher-side hold is
  added. The map's standing rule applies — where an ADR conflicts with either document, the
  ADR wins.
- The prototype's user-facing copy is adopted as a specification rather than rewritten. It
  already described a two-directional, silent, immediate, product-wide block; that was right.
- Nothing here is event-sourced that was not already: the aggregate joins the same store, the
  same catalog and the same dispatcher as every other.
