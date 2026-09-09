/**
 * The `plans` feature's only public surface.
 *
 * **A plan is one game's, for ever** — three slots, `where · day · hour`, filled from the chat by
 * anybody on the court and changed as many times as they like
 * ([ADR-0144](../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)).
 * There is no lock: **filling the third slot is the lock**, and what remains of the prototype's
 * locked state — a border, a button and a `locked by everybody` pill — was deleted rather than
 * rebuilt.
 *
 * **What is exported is what has a caller**, which today is the room: the card it pins under its
 * header, and the plan itself, which the room's quick chips read to know which questions are still
 * worth asking. The three writes, the slot grids, the copy deck and the mapper stay internal.
 *
 * **This feature imports `features/games` and nothing imports it back from there.** ADR-0149 §1
 * fixes that arrow: the ladder and the Now card belong here because a card needs both halves, and
 * `features/games` never learns a plan exists. The read-only rendering the game screen composes is
 * [#368](https://github.com/Raketa02/Raketa/issues/368)'s and will be a second component here
 * rather than a flag on the card.
 */

/**
 * **The plan card, pinned under a room's header** — the three slot chips, and nothing else.
 *
 * Handed a game id and whether the account may write; it does the join over the two lists the app
 * already holds. A room whose line-up has not completed has no game and therefore no plan, so the
 * screen draws none rather than handing this an id it does not have.
 */
export { RoomPlan, type RoomPlanProps } from './components/RoomPlan';

/**
 * **One game's plan**, for a surface that reads what has been agreed without drawing the card.
 *
 * The room's quick chips are the one caller: *one chip per unfilled slot, in slot order, plus `On
 * my way` when the agreed day is today*, which is a question about the plan asked by a control
 * that is not part of it.
 */
export { usePlan } from './hooks/usePlans';

/** What a plan is: three slots and the moment they name. */
export type { Plan, PlanSlot } from './domain/slots';
