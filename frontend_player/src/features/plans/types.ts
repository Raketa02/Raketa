/**
 * The `plans` feature's only public surface.
 *
 * **A plan is one challenge's, for ever** — three slots, `where · day · hour`, filled from the chat
 * by anybody on the court from the moment the room opens and changed as many times as they like
 * ([ADR-0144](../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md) as
 * re-keyed by
 * [ADR-0164](../../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md))
 * — and, once all three are set **and the court is whole**, **locked** by any of them, which is an
 * act rather than a fourth slot: it posts `{name} locked the plan` into the room and freezes
 * nothing
 * ([ADR-0155](../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
 * The game the challenge becomes inherits the plan by the id it was opened from, which is how Now
 * and the game screen find it. What remains of the prototype's locked state — a border and a
 * `locked by everybody` pill — stays deleted; the button came back with a destination.
 *
 * **What is exported is what has a caller**, which today is the room: the card it pins under its
 * header, the plan itself, which the room's quick chips read to know which questions are still
 * worth asking, and the refusals this feature's writes have met, which the room folds *held* from.
 * The four writes, the slot grids, the copy deck and the mapper stay internal.
 *
 * **This feature imports `features/games` and nothing imports it back from there.** ADR-0149 §1
 * fixes that arrow: the ladder and the Now card belong here because a card needs both halves, and
 * `features/games` never learns a plan exists. The read-only rendering the game screen composes is
 * `GamePlan`, a second component here rather than a flag on the card, and the screen receives it
 * as a child that knows nothing about it.
 */

/**
 * **The Home tab's rail** — `YOUR GAMES · n`, one card, swipe
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)).
 *
 * Composed by the shell under the tab's own sentences, which it is handed: the tab owns its words
 * and nothing that is drawn under them. The rail and the card are here rather than in
 * `features/games` because a card needs **both halves** — the ladder that names it reads a plan,
 * and ADR-0149 §1's arrow runs one way
 * ([`the-loop-components.md`](../../../../docs/specs/the-loop/the-loop-components.md) §3.4).
 */
export { GamesRail, type GamesRailProps } from './components/GamesRail';

/**
 * **The plan card, pinned under a room's header from its opening** — the counter, the three slot
 * chips, and the lock or, while the room has no game, the count line where the lock will be.
 *
 * Handed the room's challenge, its clock, whether the account may write and — exactly while the
 * room has no game — the court's count, members over seats; it finds the row in the list the app
 * already holds. Drawn in **every** room (ADR-0164 §2): the plan is the challenge's, and two of
 * four may plan before the others are in. What waits is the lock.
 */
export { RoomPlan, type RoomPlanProps } from './components/RoomPlan';

/**
 * **The game screen with its plan composed into it** — what both of that screen's two routes mount
 * ([#368](https://github.com/Raketa02/Raketa/issues/368)).
 *
 * `GameScreen` stays `features/games`' and takes the plan as a **child**: that feature owns the
 * frame, the court and the result arms, this one owns the three slots, and
 * [ADR-0149](../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §2 fixes it that way round — *neither type crosses*. This is the one place holding both halves,
 * so it does the join, folds which act the entry arm leads with, and fills the slot. The read-only
 * plan under it is a **second component here rather than a flag on the card**, on `CourtMini` and
 * `CourtBuild`'s reasoning: one takes three mutations and three editors and the other takes none.
 */
export { GameScreenWithPlan, type GameScreenWithPlanProps } from './components/GameScreenWithPlan';

/**
 * **One court's plan, by its challenge**, for a surface that reads what has been agreed without
 * drawing the card.
 *
 * The room's quick chips are the one caller: *one chip per unfilled slot, in slot order, plus `On
 * my way` when the agreed day is today*, which is a question about the plan asked by a control
 * that is not part of it.
 */
export { usePlan } from './hooks/usePlans';

/**
 * **Every refusal a plan write has met**, for the room's one fold over the account.
 *
 * A hold is a fact about the account rather than about the act that met it, and the room draws
 * **one** amber note for every write on its screen — the send, the three slot chips and the lock.
 * The room owns that fold and cannot see this feature's mutations, so what crosses is the list of
 * refusals, read off the mutation cache, and the code is read on the other side.
 */
export { usePlanWriteRefusals } from './hooks/usePlans';

/**
 * **The plan list's key**, for the one reader that has to re-read it on somebody else's account.
 *
 * The room's live channel is the caller: a nudge says *this room moved*, a slot another member set
 * moved it, and the card is read off `GET /plans` — so the nudge invalidates this key beside the
 * room's, and the card follows the line on every phone
 * ([#405](https://github.com/Raketa02/Raketa/issues/405)). The key and never the query: what
 * crosses is an address to invalidate, and nothing about how the list is read.
 */
export { planKeys } from './hooks/planKeys';

/**
 * **The questions the room still has to ask**, and the words for them.
 *
 * §22.4 is the plan's vocabulary by [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md)
 * §22's own assignment, and the rule reads the slot order, so both are here — while the row that
 * draws them stays `features/conversations`', because a quick chip **posts a message** and the send
 * is the room's. *A chip posts words and changes nothing*: filling the slot it asks about would
 * record an agreement nobody had yet, which is the one thing the card must not do.
 */
export { quickChips, type QuickChip } from './domain/quickChips';
export { QUICK_CHIP } from './components/planPresentation';

/** What a plan is: three slots, the moment they name, and the anchor its horizon runs from. */
export type { Plan, PlanSlot } from './domain/slots';

/**
 * **The court's line-up, as the card reads it** — complete, or still filling with its count. The
 * room folds one off its own read and hands it to the pinned card, which is the one caller: the
 * lock waits for the court (ADR-0164 §5), and the room is where who is in and whether the court
 * has its game are both known.
 */
export type { LineUp } from './domain/lock';

/**
 * **Which card a game is, and the word for it in the middle of a line**
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)).
 *
 * The conversation header's second line says where the game stands — *the same state as the card
 * in Now* — and both halves of that are this feature's: the fold is the ladder's, over the two
 * reads the rail already makes, and the lower-case word sits beside `CARD_TAG` because lowering a
 * name is a decision about words. What crosses here is a **card name** and never a standing, which
 * is the whole of why this is affordable where ADR-0148 §6 refused a state on a conversation row
 * ([ADR-0157](../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)).
 */
export { useGameCardName } from './hooks/useGameCardName';
export { cardStateWord } from './components/nowPresentation';

/**
 * **How many of your games need you** — the count on Home's column, which the shell reads for the
 * bar ([#550](https://github.com/Raketa02/Raketa/issues/550)). The rail's own cards, counted by
 * `needsYou`: a seat open, a result to enter, a score waiting on your agreement.
 */
export { useGamesNeedingYou } from './hooks/useGamesNeedingYou';
