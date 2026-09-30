/**
 * **The proposals feature's only public surface** — a group's Games deck and a game's details
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2, A4.2; the mechanics
 * §6–§8), over the backend's Proposals context (#538, #539).
 *
 * The group page draws `GamesDeck` as its Games tab and reads the tab's badge with `useGamesBadge`;
 * the details screen is mounted by its route file under `play/group/`, which checks its params
 * here first. The dependency points one way — `groups` reads `proposals`, never the reverse — so
 * the page hands in what only it knows: the kind its switch stands on, and the starting cards a
 * group with nothing dealt still draws.
 */

export { GamesDeck, type GamesDeckProps } from './components/GamesDeck';
export { GameDetailsScreen, type GameDetailsScreenProps } from './components/GameDetailsScreen';
export { useGamesBadge } from './hooks/useGroupDeck';
export { parseGameDetailsParams } from './schemas/gameDetailsParams';
export type { GameKind } from './domain/vocabulary';
/** The words the group page's suites hold the tab to. */
export { PROPOSALS_COPY } from './components/proposalsCopy';
