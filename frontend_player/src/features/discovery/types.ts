/**
 * **The discovery feature's only public surface** ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * ADR-0204; the Home rows spec set) — Home's **people rows** and their See all screens. New in Raketa
 * first; Same competitive level (#802) and Same vibe (#803) join it.
 *
 * - **`NewInRaketaRow`** — the shell composes it into Home, the third of the five rows.
 * - **`NewInRaketaScreen`** — See all, the route `/new-in-raketa`, pushed over Home.
 * - **`rereadDiscovery`** — every Discovery read again: Home's pull. A friend write or a block needs
 *   nothing from here: these reads declare `LISTS_PEOPLE`, which every one of them re-reads (§13).
 *
 * The round friend button on every tile is `friends`'; the record a tile opens is `player_record`'s.
 */

export { NewInRaketaRow } from './components/NewInRaketaRow';
export { NewInRaketaScreen } from './components/NewInRaketaScreen';
export { NEW_IN_RAKETA_ROUTE } from './components/discoveryRoutes';
export { DISCOVERY_COPY, joinedLine, nobodyNewPlays } from './components/discoveryCopy';
export { rereadDiscovery } from './hooks/useNewInRaketa';
