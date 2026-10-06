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
 *
 * Since #556 it is Home's too: the booked games on the rail, a booked game's details, its chat and
 * its result — see the block below on Home.
 */

export { GamesDeck, type GamesDeckProps } from './components/GamesDeck';
export { GameDetailsScreen, type GameDetailsScreenProps } from './components/GameDetailsScreen';
export { GamesAndMoneyRow, type GamesAndMoneyRowProps } from './components/GamesAndMoneyRow';
export { GamesAndMoneyScreen } from './components/GamesAndMoneyScreen';
export { LiveYeses } from './components/LiveYeses';
export { PaymentsToConfirm } from './components/PaymentsToConfirm';
export { useGamesBadge } from './hooks/useGroupDeck';
/**
 * **A group's Fill in tab** (#557) — *Seats to fill* and *You're In*, drawn by the group page as its
 * Fill in tab, with the badge its tab reads; the page hands in the starting card for a tab with no
 * rows, as it does the Games tab's.
 */
export { FillInBoard, type FillInBoardProps } from './components/FillInBoard';
export { useFillInBadge } from './hooks/useFillIn';
export { FILL_IN_COPY } from './components/fillInCopy';
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

/**
 * ***Post a game*** (#558; the screens A5) — the screen, mounted over the group's page by `groups`,
 * which hands in the sports, the page's sport and its switch's kind; the route the page's two doors
 * push; and the draft's end, which the page calls when it goes. The words cross for the suites.
 */
export {
  PostAGameScreen,
  type PostAGameScreenProps,
  type PostingSport,
} from './components/PostAGameScreen';
export { postAGameRoute } from './components/proposalRoutes';
export { forgetPostDraft } from './store/postDraft.store';
export { POSTING_COPY } from './components/postingCopy';

/**
 * **Home's booked games, and a booked game in detail** (#556; the screens A4.1, A4.4, A8) — over
 * `GET /home` and `GET /bookings/{id}` (#542).
 *
 * Home is one rail of booked games (#576): the shell draws `HomeRail` under its own heading and
 * empty sentences, and puts `useHomeBadge`'s count on the bar. The details, the game's chat and its
 * result are each mounted by a route file under `booking/[bookingId]/`, which checks its param here
 * first; the routes themselves are this feature's to spell.
 */
export { HomeRail, type HomeRailProps } from './components/HomeRail';
export { useHomeBadge } from './hooks/useHome';
export { BookedGameScreen, type BookedGameScreenProps } from './components/BookedGameScreen';
export { BookedGameChat, type BookedGameChatProps } from './components/BookedGameChat';
export { BookedGameResult, type BookedGameResultProps } from './components/BookedGameResult';
export { parseBookingParams, parseRescueParams } from './schemas/bookingParams';
export { bookedGameRoute } from './components/proposalRoutes';
/** The words the Home and details suites hold the screens to. */
export { HOME_GAME_COPY } from './components/homeCopy';
/**
 * ***Leave the game*** — the departure's one word, on the door and on the sheet's act, for the
 * suites that press it. The sheet and its words are this feature's since
 * [#574](https://github.com/Raketa02/Raketa/issues/574), with the booked game's departure.
 */
export { LEAVE_THE_GAME } from './components/leaveSheetCopy';

/**
 * **Where a notice opens** ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens A9):
 * a game still filling's details, spelled here for the deck's own **i**, and a booked game's open
 * seat seen from outside — a booked game's own is `bookedGameRoute`, above — and the keys a tap re-reads, so the screen it opens draws what the notice
 * said rather than a read from before it, as `paymentKeys` crosses for the fill. A notice arriving
 * while the app is open re-reads Home's read, the bar's badge with it.
 */
export { gameRoute, rescueRoute } from './components/proposalRoutes';
export { proposalKeys } from './hooks/proposalKeys';
