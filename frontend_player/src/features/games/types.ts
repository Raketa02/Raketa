/**
 * The `games` feature's only public surface.
 *
 * A game is what a completed line-up becomes, and **a result is the record that it happened**
 * ([ADR-0137](../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)): there
 * is no booking and no calendar behind any of it, so the platform learns a game was played
 * because somebody says so and the other side does not disagree. This feature is the screens
 * that make that producible — entering, correcting, agreeing and disagreeing — and the words
 * for the three ends a game can reach.
 *
 * **What is exported is what has a caller**, which is two components and nothing else. The
 * conversation rule, the score's shape, the copy deck and both writes stay internal: they are
 * the feature, and the only things outside it are the surface Now composes and the screen a row
 * pushes.
 */

/**
 * **Your games, on the Now tab.** Composed by the shell under the tab's own line, exactly as
 * the You tab composes the play intents — the tab owns its citation and nothing drawn under it.
 */
export { GamesSection } from './components/GamesSection';

/**
 * The result conversation, on the screen a row pushes.
 *
 * The route validates its param and hands over a `gameId`; everything else on that screen is
 * derived from the one list this feature reads.
 */
export { ResultScreen, type ResultScreenProps } from './components/ResultScreen';

/**
 * The route's own check on the id it is handed, because a route param is attacker-controlled and
 * this one becomes a path that appends a score to somebody's stream.
 */
export { parseGameRouteParams, type GameRouteParams } from './schemas/routeParams';
