# The feature records

One file per directory under `src/features/`, plus one for `src/shared/`. Each is **the design
record** for that code: what the screens do, and the reasons the shape is what it is — the
refusals, the reversals, the one-line-not-two arguments — one paragraph per decision, citing the
ticket and the ADR it came from.

Until 2026-09-11 this text was the `## What exists` section of [`CLAUDE.md`](../../CLAUDE.md),
which loaded all 1,700 lines of it on every turn of every session. It moved here so that a
session loads the record for the feature it is changing and nothing else — the always-loaded file
holds only what is true in every session ([`CONTEXT-MAP.md`](../../../CONTEXT-MAP.md)).

**Read the file for the feature you are changing before you change it.** A feature's record
names the sentences it refused, the shapes it tried and struck, and the seams it shares with its
neighbours — the things a fresh session would otherwise re-derive or re-litigate.

**Append here, never to `CLAUDE.md`.** When a ticket changes what a feature does, the paragraph
that records the decision goes at the end of that feature's file, in the same register as the
ones above it: the bold lead states the decision, the body gives the reason, and the ticket and
ADR are linked. A paragraph that touches two features goes in the one whose code changed most and
is referenced from the other by a sentence, not copied.

| File                                         | Records                                                                  |
| -------------------------------------------- | ------------------------------------------------------------------------ |
| [`_shared.md`](_shared.md)                   | The platform ports, the HTTP client's three verbs, the UI primitives     |
| [`auth.md`](auth.md)                         | Sign-up's adult attestation, the naming step, the You tab's identity     |
| [`challenges.md`](challenges.md)             | The send, the challenge screen, the two answers, the fill, the withdraw  |
| [`conversations.md`](conversations.md)       | The Chats tab, the room, the optimistic send, the live layer, typing     |
| [`feature_flags.md`](feature_flags.md)       | The datafile, the fallback order, the SDK and cache fences, the gate     |
| [`find_a_game_next.md`](find_a_game_next.md) | The empty screen that is Play › Explore while `find_a_game` is off       |
| [`games.md`](games.md)                       | The result argument's eight states, the score pad, the game screen       |
| [`groups.md`](groups.md)                     | Play › Groups, New group, Join a group, a group's page, Friends          |
| [`onboarding.md`](onboarding.md)             | The two parts, the hardware back button, the ratings summary, the gate   |
| [`plans.md`](plans.md)                       | The plan card, the ladder, the Now rail and its nine card states         |
| [`play.md`](play.md)                         | The copy deck, the three cards, the court, the four screens, `SH.whyfit` |
| [`player_profile.md`](player_profile.md)     | The flagged photo, the gender step, the consent copy, the commit         |
| [`player_record.md`](player_record.md)       | The record sheet a face opens, the metered rows, what opponents said     |
| [`shell.md`](shell.md)                       | Five tabs over one stack, the reset, the bar standing down               |
| [`sportsmanship.md`](sportsmanship.md)       | The star card at the foot of the game screen                             |

## The map

What exists, feature by feature, as the record stood on 2026-09-11:

`src/app/_layout.tsx` composes the providers and `src/shared/lib/bootstrap` runs the one
ordered startup sequence. Above that: the HTTP client with its 401 → refresh → retry
rotation, the `AppError` family, `shared/lib/auth` over the keychain, and four features —
`shell` (the five tabs and the one stack under them, below), `auth` (sign up — including the
**adult attestation**, the one question on that form that is not about the account — sign in,
session restore), `onboarding` (the entry gate, welcome, the
sports picker, the adaptive question loop, the explained result, and the summary and data
screens a player leaves through) and `player_profile` (onboarding's **second part**, complete: eight
steps over a client-held draft, and the one write that ends them — the Social tags picker,
2 to 6 chips from a served vocabulary, the intro step, one line about yourself or nothing, with
a visible Skip and the contact fence said up front, the photos step, up to three court photos or none, each
one checked server-side against the on-court rule and **warned about rather than refused**,
the availability grid, seven days by three parts of the day, blank on arrival and requiring
one ticked cell of the twenty-one before it continues
([ADR-0102](../../../docs/adr/0102-silence-is-never-scored.md)), the location step, one foreground fix coarsened to about a kilometre before it is
held, the radius step, a slider over the served bounds that opens at the served default, the gender
step, one required answer about the player and one optional preference over who they are
matched with ([ADR-0096](../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)),
the Proposals opt-in, never pre-ticked and with a finish that stays closed until the player
answers either way, and the **profile commit**: every answer in one idempotent
`POST /players/me/profile` — plus the **Profile surface**, the one read of the week, the
radius and the per-sport declaration that Play's search screen is drawn from, with an unkeyed
`PUT` behind each of the three). `play` has its four screens and the sheet over them, below;
`challenges` is the send and the answer: `POST /challenges`, `SH.propose`, the two re-reads a
refusal is followed by, and **the screen a challenge is answered on** — below; `conversations` is
the room the first acceptance opens — the Chats tab's second section, and **the screen behind it**:
the header, the stream, the composer and the quick chips, below; `plans` is the three slots that
room fills in — the card pinned under its header, and the one place `where · day · hour` is an
order — **and the Now rail over both of them**, the ladder that names a card and the nine cards it
names, below; `games` is the result argument — the screen a card pushes, and the entering,
correcting, agreeing and disagreeing that close the loop, below; `sportsmanship` is the card at
the end of that screen asking how the other players were, below; and `player_record` is the
sheet a face on the forecast card opens, below.
