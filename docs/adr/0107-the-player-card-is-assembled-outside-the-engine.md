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

**Nothing else.** `distance_km` is an **integer** — the underlying area is a coarse centroid
and the profile's own radius is whole kilometres, so a decimal would claim a precision the
data does not hold and would let *"3 km"* sit under a 3 km radius while being excluded by it.

**`photo_id`, not a URL.** [ADR-0091](0091-photo-storage-behind-a-port.md) serves photos
through short-lived presigned URLs, and
[ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) keeps every search row
forever: a presigned URL written into an unexpiring record is a dead link within the hour.
The record stores the id; the URL is minted per response, on the `POST` and again on every
`GET`. **`photo_id` is omitted rather than null** when a player has no photo — the glossary
already calls that *"not an absence but a generated court poster"*, so this is
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

**Form and Player Score arrive on their own, through ports that already exist.** They are
gaps, not refusals: when `matches` and `player_score` land they attach to the card through
`MatchHistoryQuery` and `PlayerScoreQuery`, and until then the card is shorter and says
nothing false. This is [ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s shape,
applied to presentation instead of to scoring.

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
