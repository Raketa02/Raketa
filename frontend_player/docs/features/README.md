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

| File                                         | Records                                                                                        |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| [`_shared.md`](_shared.md)                   | The platform ports, the HTTP client's verbs, the UI primitives                                 |
| [`administrator.md`](administrator.md)       | The administrator area, its settings and Start playing; the invitation sheet and the switcher  |
| [`auth.md`](auth.md)                         | Sign-up's attestation, the naming, the You tab, Forgot password, invitations, the last profile |
| [`blocks.md`](blocks.md)                     | Block at the foot of a record, the confirm sheet, You › Account › Blocked players and Unblock  |
| [`conversations.md`](conversations.md)       | A booked game's room, the optimistic send, the live layer, typing                              |
| [`discovery.md`](discovery.md)               | Home's people rows: New in Rakieta, its tiles and See all; one tap moves a person everywhere   |
| [`feature_flags.md`](feature_flags.md)       | The datafile, its saved copy and the fallback order, the gate read once, `explore`'s record    |
| [`friends.md`](friends.md)                   | Friend requests, Members' pills, the record's Add friend, Home; You › Friends; PLAYED WITH     |
| [`find_a_game_next.md`](find_a_game_next.md) | The empty screen that is Play › Explore, behind `explore`                                      |
| [`games.md`](games.md)                       | The result argument's eight states, the score pad, a booked game's result screen               |
| [`groups.md`](groups.md)                     | Play › Groups, New group, Join a group, a group's page, Friends                                |
| [`links.md`](links.md)                       | The four links into the app, the reader, the held link, the sheets, the install referrer       |
| [`notifications.md`](notifications.md)       | You › Account › Notifications, the phone's push, the in-app banner, the list behind the bell   |
| [`onboarding.md`](onboarding.md)             | The gate, the rating pass and its origins, the level door, the hardware back button            |
| [`payments.md`](payments.md)                 | You › Payments: the four-step setup, the method card, Change and Remove, the Stripe port       |
| [`proposals.md`](proposals.md)               | A group's Games deck and details; Games & money; the fill; Home's games; Fill in; posting      |
| [`player_profile.md`](player_profile.md)     | The flagged photo, the gender step that ends setting up, the commit                            |
| [`player_record.md`](player_record.md)       | The record sheet a face opens, reliability in points, counts and filter, what opponents said   |
| [`rankings.md`](rankings.md)                 | Home's trophy, the Rankings page: the sport pill, General and Friends, the card, podium, list  |
| [`shell.md`](shell.md)                       | Three tabs over one stack, the reset, Home, Play titled Groups or its switcher, the bar        |
| [`sportsmanship.md`](sportsmanship.md)       | The star card at the foot of a booked game's result screen                                     |

## The map

**On 2026-10-06 the old loop left** ([#576](https://github.com/Rakieta02/Rakieta/issues/576),
PRD [#569](https://github.com/Rakieta02/Rakieta/issues/569)): the Players deck and its radar, the
Chats tab, Find a game, challenges, plans, the old game screen at `/games/[id]` and the feature
flags that hid them were deleted, with their records here (`play.md`, `challenges.md`,
`plans.md`, `feature_flags.md`). The bar is **Home · ⚡Play · You**. What the new games shared
with the old loop was moved first ([#574](https://github.com/Rakieta02/Rakieta/issues/574)) and
lives in the features that use it. **The feature flags came back on 2026-11-21**
([#826](https://github.com/Rakieta02/Rakieta/issues/826)), restored from git with their record, to keep
Play's Explore off while it is unbuilt.

What exists, feature by feature:

`src/app/_layout.tsx` composes the providers and `src/shared/lib/bootstrap` runs the one ordered
startup sequence. Above that: the HTTP client with its 401 → refresh → retry rotation, the
`AppError` family, `shared/lib/auth` over the keychain, and the features:

- `shell` — the three tabs and the one stack under them; Home, Play — the groups under a _Groups_
  title, or its _Groups | Explore_ segment with `explore` on — and You are its compositions.
- `auth` — sign up (with the **adult attestation**), sign in, session restore, the naming,
  Forgot password and invitations.
- `onboarding` — the entry gate, the level door where play begins, the sports picker, the
  adaptive question loop and the explained result.
- `player_profile` — onboarding's **six steps**: a client-held draft and the
  one idempotent `POST /players/me/profile` that ends them, and the You tab's rows that edit the
  same facts afterwards.
- `groups` — Play › Groups: New group, Join a group, a group's page, Friends, Members.
- `proposals` — a group's Games deck and a game's details, the fill and _It's a game!_, Fill in
  and rescues, posting a game, Games & money and the live yeses, and Home's booked games with a
  booked game's details, chat and result.
- `conversations` — a booked game's room: the header, the stream, the composer, the live layer.
- `games` — the result argument: the screen a booked game's _We played_ pushes, and the
  entering, correcting, agreeing, disagreeing and no-shows that close it.
- `sportsmanship` — the card at the end of that screen asking how the other players were.
- `player_record` — the record sheet a face opens.
- `rankings` — Home's trophy and the Rankings page: a ranking per sport, sorted by the level.
- `blocks` — Block at the foot of that sheet, and You › Account › Blocked players, where Unblock is.
- `payments`, `notifications`, `links`, `administrator` and `find_a_game_next` (Explore's empty
  page) — each in its own record above.
- `feature_flags` — the feature flags: the datafile from `Rakieta02/rakieta-features`, its saved copy,
  the Featurevisor SDK behind one file, and the gate a screen reads once when it mounts. One key,
  `explore`, off.
