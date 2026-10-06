# The copy deck's home

This directory holds one file: [`the-words.md`](the-words.md), **the player app's copy deck** —
every sentence and accessible name the app says, by section. It lives here for a historical
reason rather than a topical one: it was written beside the matchmaking specs, and about sixty
documents and docstrings cite it by this relative path and by section number, so it stays where
it is and its sections are never renumbered.

**The matchmaking specs that used to live here were deleted on 2026-10-06**, with the Classic play
loop they described ([#569](https://github.com/Raketa02/Raketa/issues/569)): the two verbatim input
documents (`matchmaking-engine.md`, `social-prototype-v1.html`), the engine's own spec set (the
pipeline, the ranking weights, the five numbers, the newcomer path, the availability term, the
group objective, the tag matrix, the two contracts, the consumer-driven contracts, the candidate
index, the search telemetry, the scale posture, the judged pairings and the replay harness), the
Play tab's screens and components, and the radar with its mocks. They are in the history at
`git show 9ea23dad:docs/specs/matchmaking/<file>`; nothing in them is a constraint on work today.
The [ADR index](../../adr/README.md#the-2026-10-06-classic-play-removal--the-second-gap) says what
went and why.

**What is left of matchmaking** is what the new games call, and its decisions are in records that
stand, each with a dated note on what was removed around it:

| What | Code | Decided by |
| --- | --- | --- |
| The **level window**, one tolerance per kind of game | `backend/app/modules/matchmaking/domain/level_window.py` | [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md) |
| The **newcomer window**, which tightens it for fourteen days | the same module | [ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md) |
| The **pair rule** every court asks — blocks, mutual gender preference, the level window | `backend/app/modules/proposals/infrastructure/matcher_player_fit.py` | [ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md), [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md), [ADR-0193](../../adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md) |
| The **balance forecast** and its **split** | `backend/app/modules/matchmaking/domain/balance.py`, `backend/app/engines/matchfit/v1/group.py` | [ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md), [ADR-0136](../../adr/0136-the-split-is-evidence-for-the-forecast-not-a-second-score.md), [ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md) |
| **Group availability**, which grades a Games card's overlap | `backend/app/engines/matchfit/v1/group.py` | [ADR-0102](../../adr/0102-silence-is-never-scored.md) |
| The **ruleset** those read | `backend/app/modules/matchmaking/infrastructure/rulesets/` | [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md), [ADR-0119](../../adr/0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md) |

How the new games use them is in
[`../games-and-fill-in/the-mechanics.md`](../games-and-fill-in/the-mechanics.md) §5.1.
