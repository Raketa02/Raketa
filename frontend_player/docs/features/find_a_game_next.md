# find_a_game_next — where the next Find a game will grow

> The design record for `src/features/find_a_game_next/` — what the feature does and the reasons
> the shape is what it is, one paragraph per decision. **Append here** when a ticket changes what
> this feature does. Index: [`README.md`](README.md).

**An empty screen, and a feature folder around it**
([#479](https://github.com/Raketa02/Raketa/issues/479),
ADR-0180
§7). Find a game was to be rebuilt, and the rebuild needed somewhere to live while the old one kept
working. `FindAGameNextScreen` was what the Play tab's root drew while `find_a_game` was
off: the app's `paper` ground and nothing else, under the shell's tab bar. **No copy** — nothing
says _coming soon_, because there is no promise to make yet and a sentence written now is one the
rebuild would inherit without anybody deciding it. It is its own feature rather than a file in the
old Play feature so the new version grows in a folder that never held the old one, and retiring the
old one was deleting a folder (#576); it carries the full layer set, empty, for that reason.
`FIND_A_GAME_NEXT_TEST_ID` is exported because a screen with nothing on it has nothing else a suite
could find it by. **Seen on a device on 2026-09-23.**

**The placeholder is Play › Explore now**
([#512](https://github.com/Raketa02/Raketa/issues/512), PRD #500 stories 2–3). With `find_a_game`
off — the code default since #512 — the Play tab opens on the shell's _Groups | Explore_ segment,
and **Explore is this screen**, drawn under the segment rather than as the whole tab: Explore is
where the rebuilt Find a game grows (play 2, background only), so the empty feature that was waiting
for it sits under the name it will have. Still no copy, for the reason above, and still
`FIND_A_GAME_NEXT_TEST_ID` — the walks in `shell/components/playSegment.test.tsx` find Explore by it.

**Behind `classic_play` now** ([#550](https://github.com/Raketa02/Raketa/issues/550)). The flag
that decides whether Play › Explore draws this screen or the old Find a game is the old loop's one
flag; nothing about the screen changed.

**No flag decides it any more** ([#576](https://github.com/Raketa02/Raketa/issues/576)). The old
Find a game and the flag that could bring it back are gone, so Play › Explore is this screen
always, still empty, until the rebuilt Find a game grows here.
