/**
 * **The discovery feature's only public surface** ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * ADR-0204; the Home rows spec set) — Home's **people rows** and their See all screens: New in Raketa,
 * Same competitive level ([#802](https://github.com/Raketa02/Raketa/issues/802)), and Same vibe
 * ([#803](https://github.com/Raketa02/Raketa/issues/803)).
 *
 * - **`SameLevelRow`** — the shell composes it into Home, the second of the five rows.
 * - **`SameLevelScreen`** — See all, the route `/same-level`, pushed over Home.
 * - **`NewInRaketaRow`** — the third of the five rows.
 * - **`NewInRaketaScreen`** — See all, the route `/new-in-raketa`, pushed over Home.
 * - **`SameVibeRow`** — the fourth of the five rows.
 * - **`SameVibeScreen`** — See all, the route `/same-vibe`, pushed over Home.
 * - **`rereadDiscovery`** — every Discovery read again: Home's pull. A friend write or a block needs
 *   nothing from here: these reads declare `LISTS_PEOPLE`, which every one of them re-reads (§13).
 *
 * **Same competitive level and Same vibe report the cards that came on screen**
 * ([#804](https://github.com/Raketa02/Raketa/issues/804)) on a page that watches — Home, whose
 * `ShellScreen` says so; nothing for the shell to hand them.
 *
 * The round friend button on every card and tile is `friends`'; the record a face opens, and the
 * record the vibe sheet reads, are `player_record`'s.
 */

export { NewInRaketaRow } from './components/NewInRaketaRow';
export { NewInRaketaScreen } from './components/NewInRaketaScreen';
export { SameLevelRow } from './components/SameLevelRow';
export { SameLevelScreen } from './components/SameLevelScreen';
export { SameVibeRow } from './components/SameVibeRow';
export { SameVibeScreen } from './components/SameVibeScreen';
export {
  NEW_IN_RAKETA_ROUTE,
  SAME_LEVEL_ROUTE,
  SAME_VIBE_ROUTE,
} from './components/discoveryRoutes';
export { DISCOVERY_COPY, joinedLine, nobodyNewPlays } from './components/discoveryCopy';
export { rereadDiscovery } from './hooks/useNewInRaketa';
