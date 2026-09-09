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
 * **What is exported is what has a caller.** The result argument's fold, the score's shape, the
 * copy deck and both writes stay internal: they are the feature, and what leaves it is the screen
 * a card pushes, the list Now is drawn from and the one sentence that card draws.
 *
 * **Now's rail is not here** ([#367](https://github.com/Raketa02/Raketa/issues/367)). `GamesSection`
 * was this feature's while Now was a placeholder with a list under it; the rail that replaced it
 * needs a **plan** beside every game, and ADR-0149 §1's arrow runs one way — so the composition is
 * `features/plans`' and this feature still never learns a plan exists.
 */

/**
 * One game, on the screen a card pushes — and most of it is the result argument.
 *
 * The route validates its param and hands over a `gameId`; everything else on that screen is
 * derived from the one list this feature reads.
 */
export { GameScreen, type GameScreenProps } from './components/GameScreen';

/**
 * The route's own check on the id it is handed, because a route param is attacker-controlled and
 * this one becomes a path that appends a score to somebody's stream — and **where that route is**,
 * for the feature that pushes it.
 */
export { GAME_ROUTE, parseGameRouteParams, type GameRouteParams } from './schemas/routeParams';

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

/**
 * **Every game of yours, in one list** — for the feature that composes Now's rail over it.
 *
 * `useGame` is the lookup inside this same answer; the rail needs the whole of it, plus the read's
 * own pending and error states, because a section that vanished on a failed read would be
 * indistinguishable from a player with no games.
 */
export { useGames } from './hooks/useGames';

/**
 * **What a game is asking of you, in one sentence** — the card's gloss wherever the ladder has
 * nothing to add.
 *
 * The same line the screen behind the card says, so a player who reads a card, taps it and finds
 * a different deadline is not a state this can reach. What crosses is the sentence and not the
 * fold: `resultArgument` and `GameStanding` stay this feature's.
 */
export { gameStandingLine } from './components/gamePresentation';

/** What a game is, for the feature that draws a plan beside one. */
export type { Game } from './domain/game';
