/**
 * The `games` feature's only public surface.
 *
 * A game is what a booked court becomes, and **a result is the record that it happened**
 * ([ADR-0137](../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)). This
 * feature is the screen that makes that producible — entering, correcting, agreeing and
 * disagreeing, and saying who turned up at the court — and the words for the ends a game can reach.
 *
 * **What is exported is what has a caller**, and since the old loop's game card, its rail and the
 * `/games/[id]` route were removed ([#576](https://github.com/Raketa02/Raketa/issues/576)) every
 * caller is a booked game's: its result screen, its forecast on the details, and the writes that
 * say the games list is out of date. The result argument's fold, the score's shape, the copy deck
 * and the writes stay internal.
 */

/**
 * One game, on the screen a booked game's *We played* pushes — and most of it is the result
 * argument. The booked game's result route hands over the Game's id and the booking's own facts
 * (`BookedFacts`); everything else on the screen is derived from the one list this feature reads.
 */
export { GameScreen, type BookedFacts, type GameScreenProps } from './components/GameScreen';

/**
 * **Whether a booked game's first half hour runs at an instant** (#658) — the window in which a
 * player at the court says who isn't here yet, crossed for the booked details' door, which reads
 * *Who's here* through it. The rule is this feature's; the clock is the caller's.
 */
export { tapsAreOpen } from './domain/attendance';

/**
 * **The forecast block alone**, for a surface that draws its own people — a booked game's details
 * (#556), whose tiles come from the booking with *paid* on each. One read of
 * `GET /games/{game_id}/pairing` ([ADR-0161](../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)),
 * absent when the pairing is refused.
 */
export { GameForecast, type GameForecastProps } from './components/GameForecast';

/**
 * **The forecast's own heading**, exported for the suite that walks a booked game's details: a test
 * spelling *Balance forecast* as a literal is a red build for the ticket that rewords it.
 */
export { BALANCE_FORECAST } from './components/gamePresentation';

/**
 * **This feature's cache key**, crossed for the acts outside it that change a game — a fill that
 * books one, a departure, a live nudge — which owe the statement that this list is now out of
 * date. The **key** crosses and the query does not: spelling `['games']` at the call site is the
 * same coupling with nothing holding the two spellings equal.
 */
export { gameKeys } from './hooks/gameKeys';
