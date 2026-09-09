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
 * result argument's fold, the score's shape, the copy deck and both writes stay internal: they are
 * the feature, and the only things outside it are the surface Now composes and the screen a row
 * pushes.
 */

/**
 * **Your games, on the Now tab.** Composed by the shell under the tab's own line, exactly as
 * the You tab composes the play intents — the tab owns its citation and nothing drawn under it.
 */
export { GamesSection } from './components/GamesSection';

/**
 * One game, on the screen a row pushes — and most of it is the result argument.
 *
 * The route validates its param and hands over a `gameId`; everything else on that screen is
 * derived from the one list this feature reads.
 */
export { GameScreen, type GameScreenProps } from './components/GameScreen';

/**
 * The route's own check on the id it is handed, because a route param is attacker-controlled and
 * this one becomes a path that appends a score to somebody's stream.
 */
export { parseGameRouteParams, type GameRouteParams } from './schemas/routeParams';

/**
 * **This feature's cache key**, crossed for the one act outside it that opens a game.
 *
 * An accept that fills the last seat mints a game and a conversation in the same transaction, in
 * caches that response says nothing about — so `challenges` invalidates `GET /games` and the row
 * appears on Now without anybody refreshing it
 * ([ADR-0143](../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
 *
 * The **key** crosses and the query does not: a challenge answering hook has no business reading
 * a game, and what it owes is the statement that this list is now out of date. That is the
 * narrowest thing that can be said, and the alternative — spelling `['games']` at the call
 * site — is the same coupling with nothing holding the two spellings equal.
 */
export { gameKeys } from './hooks/gameKeys';

/**
 * **One game, out of the list this feature reads** — for the one feature allowed to ask.
 *
 * `features/plans` composes a plan beside a game and needs both halves to draw anything: the
 * horizon a day row is clamped to is `planned_at + PLAN_HORIZON`, and the instant *today* is read
 * against is the list's own `read_at`, so the two have to come off one fold
 * ([ADR-0149](../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §1). **The arrow runs one way**: `plans` may import this feature and this feature never learns a
 * plan exists, which is the client half of ADR-0145 §4's clause and a grep rather than a
 * judgement — `eslint.config.mjs` refuses the import in the other direction.
 *
 * There is no `GET /games/{id}`, so this is a lookup inside one list rather than a read of its
 * own: `undefined` covers the list not having landed, the read having failed, and no game of
 * yours having that id.
 */
export { useGame } from './hooks/useGames';

/** What a game is, for the feature that draws a plan beside one. */
export type { Game } from './domain/game';
