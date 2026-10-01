/**
 * **The proposals feature's only public surface** — a group's Games deck and a game's details
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2, A4.2; the mechanics
 * §6–§8), and the player's own two reads, Games & money and the live yeses
 * ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.1, A7.3) — over the
 * backend's Proposals context (#538, #539).
 *
 * The group page draws `GamesDeck` as its Games tab and reads the tab's badge with `useGamesBadge`;
 * the details screen is mounted by its route file under `play/group/`, which checks its params
 * here first. The dependency points one way — `groups` reads `proposals`, never the reverse — so
 * the page hands in what only it knows: the kind its switch stands on, and the starting cards a
 * group with nothing dealt still draws.
 *
 * The shell composes `GamesAndMoneyRow` into the You tab's ACCOUNT group, and a route file under
 * `you/` mounts its screen. `LiveYeses` is You › Payments' section, **handed to that screen by its
 * route file** rather than imported by `payments`: the deck will open the payment setup as a sheet
 * (A2.4), so the edge between the two features points from here to there.
 */

export { GamesDeck, type GamesDeckProps } from './components/GamesDeck';
export { GameDetailsScreen, type GameDetailsScreenProps } from './components/GameDetailsScreen';
export { GamesAndMoneyRow, type GamesAndMoneyRowProps } from './components/GamesAndMoneyRow';
export { GamesAndMoneyScreen } from './components/GamesAndMoneyScreen';
export { LiveYeses } from './components/LiveYeses';
export { PaymentsToConfirm } from './components/PaymentsToConfirm';
export { useGamesBadge } from './hooks/useGroupDeck';
export { parseGameDetailsParams } from './schemas/gameDetailsParams';
export type { GameKind } from './domain/vocabulary';
/** The words the group page's suites hold the tab to. */
export { PROPOSALS_COPY } from './components/proposalsCopy';

/**
 * **The moment a yes fills a game** (#555) — the ten seconds of *Undo*, the setup a first yes needs,
 * *It's a game!* and a refused share's confirmation. The shell mounts the provider around the tabs
 * for the session, because a yes said on the deck outlives the deck; the screens here reach it
 * through `useFill`, which does not cross. The words cross for the suites that walk it.
 */
export { FillProvider, type FillProviderProps } from './components/FillProvider';
export { FILL_COPY } from './components/fillCopy';
