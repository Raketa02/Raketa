# ADR-0107 — The player card is assembled outside the engine, and its contents are a closed list

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) put a pure scorer
behind a package boundary, and [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)
made that boundary a privacy fence asserted by a build-failing test: a `ScorableCandidate`
has no name, no photo, no birthdate and no precise location, because *a term cannot read a
protected characteristic when the value is not in the process*. §7.2 of
[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) says the same of the
candidate index — **the fields do not exist**.

[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §4 then fixed what a
returned candidate carries: `player_id`, `fit`, the terms with their evidence,
`degraded_terms`, modifiers, liveness reason codes, an optional inclusion reason, `at_stake`
and `would_be_forecast`. Every one of those is about a **pairing**.

**So the response can name a player and say nothing whatever about who they are.** The
prototype's card — the only artefact showing what the screens actually do — leads with a
face, a name, a neighbourhood, a distance, a line of the player's own prose and a row of
tags, and then four numbers. Audited against what this platform holds, **five of its twelve
fields have no source**:

| On the prototype's card | Source in this backend |
| --- | --- |
| photo, area, distance, tags, level + band, counted games | exist |
| **name** | there is no name anywhere — `users` holds an Email and a **Nickname** |
| **bio** | no field, and Social tags are *"never free text, never player-authored"* |
| **active 2 hours ago** | no field — and it is row three of §9.5's **Liveness** table |
| **Player Score** | `NoPlayerScoresExist` ([ADR-0098](0098-matcher-demands-as-executable-contracts.md)) |
| **Last 5 form** | `matches`, which is out of scope on this map |
| **unsettled** | `cases`, which the matcher is forbidden to read |

Two of those five are not waiting on a context. They are refusals, and each collides with a
rule this repository already holds.

**The bio** would be the platform's **first player-authored free-text field.** The Player
profile glossary refuses free text for the tag vocabulary in those words, and the *reason* is
the same reason here: free text about oneself, shown to strangers, is a moderation surface,
and the full moderation story is out of scope beyond
[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s minimal block.

**`active 2 hours ago`** is *Recent activity*, worth −5…+4 of Liveness.
[ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 refuses to
let a Liveness *number* cross under any name, and §9.5 gives the argument: the moment the
printed Fit silently contains *"they open the app a lot"*, it stops meaning what it says.
Printing the raw input beside the Fit does not put it in the number — and it publishes a fact
about a stranger's phone that the stranger never offered.

The way the card gets its person was the other open question. Embedding a profile projection
in each row, fetching profiles from a batch route, or showing nothing until a challenge — and
the third is not a real option, because a shortlist of twenty numbered strangers is not a
screen.

## Decision

**We will have the backend attach a `player_card` to each returned candidate after the engine
returns, and we will fix its contents as a closed list.**

### 1. A different author, on a seam that already exists

`at_stake` is already a candidate field the matcher does not write: ADR-0021 forbids the
client computing it and [ADR-0098](0098-matcher-demands-as-executable-contracts.md) forbids
the matcher re-deriving it, so the backend attaches it after `matchfit` returns. The
`player_card` rides the same seam. The fence is untouched — nothing here enters
`ScorableCandidate`, and the two build-failing assertions at `app/engines/matchfit/` are
unaffected.

One round trip, one screen. A batch profile route would make the shortlist arrive as twenty
grey rectangles and would put a second request in front of *Why 78?*, which §8.3 requires to
open instantly.

### 2. The closed list

```
player_card: { nickname, photo_id?, area_code, distance_km,
               social_tags[], level, band, counted_games }
```

*(as it stood; the amendments below are what it is now)*

**Nothing else.**

> **Amended five times since, all under this ADR's own rule** — *a card says only what its
> subject published, and every field on it is a fact about that person alone.*
>
> - **`range` was added** — the likely range, μ ± σ as `rating` published it, travelling as
>   `{low, high}` ([#235](https://github.com/Raketa02/Raketa/issues/235),
>   [#243](https://github.com/Raketa02/Raketa/issues/243)). Printing μ while refusing μ ± σ
>   shows two players at the same Level with no way to tell that one of them is a guess. It
>   is **projected** onto the index row and copied onto the card, never derived at assembly.
>   The band's numeric **edges stay off**: their only consumer is the band bar, which is
>   drawn from the out-of-scope record sheet, and the glossary refuses them as a second
>   range in any case.
>
> - **`photo_url` was added beside `photo_id`** — a short-lived signed link, minted per
>   response and recorded nowhere ([#245](https://github.com/Raketa02/Raketa/issues/245)).
>   The paragraph below already described it; nothing minted one, and
>   `GET /photos/{id}` refuses another player's id on purpose — so as the contract stood
>   **no photograph could reach a Play screen at all**. The two fields are omitted
>   together, and the URL is the one field on a response the record deliberately cannot
>   reproduce.
>
> - **`distance_km` left the card**, for the same rule read the other way: a distance is a
>   fact about a **pair**, and it is the one field whose value would change depending on who
>   is looking. It sits on the *candidate*, beside the card
>   ([`the-play-screens.md`](../specs/matchmaking/the-play-screens.md) §1, which carries the
>   argument).
>
> - **`review` was added beside `photo_id`** — what the on-court check concluded about that
>   photograph, as a code, or **omitted** for *nobody looked*
>   ([ADR-0138](0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
>   It is the awkward one for this ADR's rule and it passes: a verdict is not something its
>   subject *published*, but it is a fact about **their photograph** rather than about the
>   pair, so it does not change with who is looking — which is the half of the rule
>   `distance_km` failed. It is **recorded** like `photo_id` and not minted like `photo_url`,
>   and the two paragraphs below are what decide that: a link is dead within the hour so it
>   cannot be stored, and a verdict is a store round trip so it must not be re-read per
>   response.
>
> - **The record block was added — `player_score`, `counted_games` and `last_five`**
>   ([#306](https://github.com/Raketa02/Raketa/issues/306)). `counted_games` was on the list
>   from the beginning and had never been assembled; the other two joined it when their
>   providers shipped
>   ([ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md),
>   [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)). All three pass this
>   ADR's test the way `review` does rather than the way `range` does: they are not something
>   their subject *published* — they are what the platform **watched them do** — but each is a
>   fact about that person alone and does not change with who is looking, which is the half of
>   the rule `distance_km` failed.
>
>   Two things about them are decided elsewhere and named here so the list stays readable.
>   **Every one is omitted rather than nought** where the platform has watched nothing, which
>   is `distance_km`'s two-spellings rule
>   ([ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §4) applied
>   to three more fields — and, for `counted_games`, the one place this card deliberately
>   disagrees with its provider, which measures a real zero for its own callers. And
>   **`last_five` carries outcomes in order and no dates**: a moment beside one of them would
>   be the activity recency this ADR refuses outright.
>
> The list is still closed; it is the two paragraphs below that say what closed means.

`distance_km` is an **integer** — the underlying area is a coarse centroid
and the profile's own radius is whole kilometres, so a decimal would claim a precision the
data does not hold and would let *"3 km"* sit under a 3 km radius while being excluded by it.

**`photo_id` in the record, `photo_url` on the response.**
[ADR-0091](0091-photo-storage-behind-a-port.md) serves photos through short-lived presigned
URLs, and [ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) keeps every
search row for ever: a presigned URL written into an unexpiring record is a dead link within
the hour. The record stores the id; the URL is minted per response, on the `POST` and again
on every `GET`. **The dead-link argument is about the record, and a URL that never enters it
does not touch that argument** — which is why both fields can be on one card. The link is
minted by the server rather than left to the client because `GET /photos/{id}` signs only
*your own* photos and refuses a stranger's id deliberately — the alternative is an endpoint
that confirms whether a stranger's id is real — and a card's photo is by definition another
player's. **Both fields are omitted rather than null** when a player has no photo — the
glossary already calls that *"not an absence but a generated court poster"*, so this is
[ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §4's *does not
apply* spelling, and the client draws the poster.

### 3. The two refusals, and they are permanent

- **No bio, and no free-text field of any kind on a card.** If a player is ever to write a
  sentence about themselves, that is its own decision with a moderation story attached, not a
  field this contract grew.
- **No activity recency, in any granularity** — not a timestamp, not *active today*, not a
  green dot. Liveness reaches the screen the one way it is sanctioned to: as a **reason code**,
  printed when it moves somebody more than `MOVE_NOTICE`. *"Usually answers within a day"* is a
  claim about the pairing's chances and is already in the vocabulary; *"last seen 2 hours ago"*
  is a presence indicator, and this product does not have one.

### 4. There is no name, so nothing may shorten one

> **Amended 2026-09-14 by [ADR-0166](0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
> §3: one drawing is exempt, and it is named in full.** The yes screen draws **two initials over a
> generated poster** — never over a photograph, never spoken, never in copy, and on no other
> surface; the tile's accessible name is the whole handle. The rule below stands for every
> sentence, every spoken name and every other drawing — `handleStem` and the seat's caption were
> admitted *inside* it, and the Chats rows keep [#338](https://github.com/Raketa02/Raketa/issues/338)
> §5's refusal of a monogram. The argument, and the fence, are ADR-0166's.

The card carries a **Nickname**. `users` holds no real name and no given name, and a nickname
is a single opaque handle — 2–64 characters of `[A-Za-z0-9_.-]`.

**The client may never derive a familiar form from it.** The prototype's idiom —
`p.n.split(' ')[0]`, producing *"Marek takes Ana's place"* across every Play screen — has
nothing behind it here. Every sentence naming somebody uses the whole handle or names nobody.
Inventing a first name is the product addressing a person by a name they never gave it.

## Consequences

**The privacy fence gets easier to defend, not harder.** The question *"why can't the scorer
see a name?"* now has a visible answer on the same screen: the name arrives from somewhere
else, later, by a different author. A reviewer looking at one candidate object sees two
provenances and has to ask which is which, which is the right question to be prompted to ask.

**Two of the prototype's card fields are deleted rather than deferred,** and somebody will
propose each of them again. The bio will come back as *"players want to say something about
themselves"*, which is true and is a different product decision. Recency will come back as
*"we already compute it"*, which is exactly the argument ADR-0106 §5 exists to refuse. Both
are written down here so the next proposal starts from the reason rather than from the field.

**Form and Player Score arrived on their own, through ports that already existed.** They were
**gaps, not refusals**, and both are closed
([#306](https://github.com/Raketa02/Raketa/issues/306)). The prediction was right about the
shape and wrong about one port name, which is worth recording because the correction is the
rule doing its work:

- **The Player Score reaches the card through `PlayerScoreQuery`**, exactly as written — the
  same port the reliability term reads, **read again** at assembly
  ([ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md) §6).
  Two reads rather than one because they are bounded by different things: the engine's prices a
  *term* over everybody who might be scored, and this one prints a *number* over the shortlist.
  Taking the card's figure off the engine's record would make what a player is shown a
  consequence of whatever that term happens to carry.
- **The form does not come from `MatchHistoryQuery`, and could not have.** That port answers
  *what have these two done together* — a bounded pairwise read, and a fact about a **pair**,
  which is the one thing this ADR keeps off a card. `counted_games` and `last_five` are facts
  about one person, so they arrive on a source of their own, `PlayerRecordSource`, beside
  `PlayerCardSource` at the assembly seam. `matches` never landed either: **`games` is the
  context that shipped** ([ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)), and
  it composes into `MatchHistoryQuery` for the pairwise half while answering the card's two
  fields through the other port.

This is still [ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s shape, applied to
presentation instead of to scoring — including its rule that **a provider signing half of two
contracts has signed all of neither**, which is why the split above is two ports and not one.

**Every photo becomes visible to strangers, and [ADR-0091](0091-photo-storage-behind-a-port.md)
deferred its content check on the argument that they could not be.** That ADR's words were
*"there is no matchmaking, no player card and no discovery, so a check today protects
nothing"*. This record creates the player card, so the deferral now rests on a false premise.
The `PhotoReview` port and its pass-through adapter already exist; what changes is that the
reason for the pass-through has expired, recorded as an amendment on 0091 and filed as its own
ticket rather than absorbed here — this map plans and does not build.

**The card is a permanent copy of a nickname and a photo id, in a record that never expires.**
ADR-0104 already made erasure the only deletion path there is and wrote it down as a demand;
this adds two columns to what that demand covers. It is a real cost of the unexpiring record
and it is paid in the same place.

**A nickname is worse copy than a first name and it is the honest one.** *"Ana takes Piotr's
place"* reads better than *"kowal_92 takes ana.p's place"*. The alternative was inventing a
familiar form from an identifier, which is worse than clumsy — it is wrong about a person, in
their own app, in a sentence they did not write.
