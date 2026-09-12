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
 * derived from the one list this feature reads. **Nothing in the app pushes it today** — the
 * list that did is composed nowhere — so the route resolves and no control reaches it.
 */
export { GameScreen, type GameScreenProps } from './components/GameScreen';

/**
 * **The court's pairing, for the composition that fills the game screen's `court` slot.**
 *
 * The forecast block and the players card over one read of `GET /games/{game_id}/pairing`
 * ([ADR-0161](../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)). It crosses
 * because the faces the players card draws come off the room join `features/plans` holds for the
 * card above it, and the screen may not read that list — so the composition hands this the map and
 * the screen draws the slot it is handed, as it draws the other two.
 */
export { CourtPairing, type CourtPairingProps } from './components/CourtPairing';

/**
 * **The pairing's own words, exported for the suite that walks the plan lead from `plans`.**
 *
 * `gamePlan.test.tsx` asserts which lead draws the court's pairing, and a test spelling *Balance
 * forecast* as a literal is a red build for the ticket that rewords it — `findAGamePresentation`'s
 * rule, the one every copy deck in this app is read through. `IT_WAS_CALLED_OFF` crosses for the
 * same reason one feature over: `callOff.test.tsx` asserts the screen re-folds into the fourth
 * end. Nothing in `src/` outside this feature reads any of them.
 */
export {
  BALANCE_FORECAST,
  IT_WAS_CALLED_OFF,
  OPEN_SEAT,
  PLAYERS,
  recordLabel,
} from './components/gamePresentation';

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

/**
 * **What this evening is worth, in one sentence** — cited by the surface that draws the plan.
 *
 * The game screen's checklist is *what is true now, what is still to agree, what it moves*, and
 * the third line is **cited rather than written**
 * ([`the-loop-screens.md`](../../../../docs/specs/the-loop/the-loop-screens.md) §5.3): it is the
 * whole of what survives ADR-0143 §8's refusal of a forecast block there, and it is already built
 * and tested here. A second sentence about what a game is worth, written in the feature that draws
 * the plan, would be that feature's opinion about a fact this one owns.
 *
 * What crosses is the sentence and not the `GameKind` vocabulary: an absent kind is a clause
 * dropped, and the caller hands the answer down without reading a code.
 */
export { worthLine } from './components/gamePresentation';

/**
 * **What an entry arm leads with**, and the verb of the door that reaches its grid.
 *
 * `AWAITING_ENTRY` is one standing over two landings — *Planning* and *Game on* arrive at the plan,
 * *Today* and *Needs result* at the score grid — and the ladder that tells them apart reads a plan,
 * which this feature may never learn about. So the fold is `features/plans`' and what crosses back
 * is a word in **this** feature's vocabulary
 * ([`the-loop-components.md`](../../../../docs/specs/the-loop/the-loop-components.md) §3.3,
 * [`the-loop-screens.md`](../../../../docs/specs/the-loop/the-loop-screens.md) §5.2).
 *
 * The verb both of those doors carry is `shared/vocabulary/theActsWords.ts`', not this feature's:
 * two features name that one act, and a word read across this seam at module-evaluation time reads
 * a half-built module (`theActsWords.ts` says why).
 */
export type { EntryLead } from './domain/resultArgument';

/**
 * What a game is, for the feature that draws a plan beside one — and the two readings of its
 * seats that feature keys on: which are open, and who is in the rest. `seatedOthers` is what the
 * fill is told about the court it completes ([#419](https://github.com/Raketa02/Raketa/issues/419)):
 * the composition reads it off the game and hands it to `features/challenges`' control, so
 * neither of those features learns the other's court.
 */
export type { Game } from './domain/game';
export { openSeats, seatedOthers } from './domain/game';
