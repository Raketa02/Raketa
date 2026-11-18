/**
 * **The discovery feature's only public surface** ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * ADR-0204; the Home rows spec set) — Home's **people rows** and their See all screens: New in Raketa,
 * Same competitive level ([#802](https://github.com/Raketa02/Raketa/issues/802)), and Same vibe
 * ([#803](https://github.com/Raketa02/Raketa/issues/803)).
 *
 * - **`useSameLevelLine`** — Players at your level, the second of FOR YOU's five lines on Home (#820),
 *   `undefined` while hidden; the shell folds it.
 * - **`SameLevelScreen`** — See all, the route `/same-level`, pushed over Home.
 * - **`useNewInRaketaLine`** — New in Raketa, the third of the five lines.
 * - **`NewInRaketaScreen`** — See all, the route `/new-in-raketa`, pushed over Home.
 * - **`useSameVibeLine`** — Players with your vibe, the fourth of the five lines.
 * - **`SameVibeScreen`** — See all, the route `/same-vibe`, pushed over Home.
 * - **`rereadDiscovery`** — every Discovery read again: Home's pull. A friend write or a block needs
 *   nothing from here: these reads declare `LISTS_PEOPLE`, which every one of them reaches (§13).
 *
 * **Same competitive level and Same vibe report the cards that came on screen**
 * ([#804](https://github.com/Raketa02/Raketa/issues/804)) on a page that watches — Home, whose
 * `ShellScreen` says so — and only while their line is open; nothing for the shell to hand them.
 *
 * The round friend button on every card and tile is `friends`'; the record a face opens, and the
 * record the vibe sheet reads, are `player_record`'s.
 */

export { useNewInRaketaLine } from './components/NewInRaketaLine';
export { NewInRaketaScreen } from './components/NewInRaketaScreen';
export { useSameLevelLine } from './components/SameLevelLine';
export { SameLevelScreen } from './components/SameLevelScreen';
export { useSameVibeLine } from './components/SameVibeLine';
export { SameVibeScreen } from './components/SameVibeScreen';
export {
  NEW_IN_RAKETA_ROUTE,
  SAME_LEVEL_ROUTE,
  SAME_VIBE_ROUTE,
} from './components/discoveryRoutes';
export { DISCOVERY_COPY, joinedLine, nobodyNewPlays } from './components/discoveryCopy';
export { rereadDiscovery } from './hooks/useNewInRaketa';
