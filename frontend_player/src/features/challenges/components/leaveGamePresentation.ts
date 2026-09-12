/**
 * **Every word *Leave this game* says** — the control, its busy label, and the sheet in front of
 * it ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.8,
 * [#418](https://github.com/Raketa02/Raketa/issues/418)).
 *
 * A deck of its own rather than rows in `challengeDetailPresentation.ts`, because that deck is the
 * challenge screen's and this act is pressed on the **game** screen: copy lives beside the surface
 * that says it, and the control is composed onto that screen through `types.ts`.
 *
 * ## The withdraw's shape, and the difference that reworded it
 *
 * `WithdrawSheet`'s exact shape a third time — a title naming the **moment** rather than the act,
 * three body lines, the act named once on the control that carries it out, a dismissal named by
 * what it does. What differs is what the sheet has to say: the withdraw destroys the court and
 * the room, and its second line exists to say so; a departure destroys **nothing** — the others
 * keep the game, the plan and the room
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md))
 * — so the first line says what survives, and the second says the one thing the leaver gives up:
 * `already_asked_at` keeps them out of this court's pool for as long as it stands, and nobody is
 * asked twice on one challenge.
 *
 * **Nothing here says the pair rule releases**, on `WITHDRAW_SHEET_BODY`'s own line: that is a
 * fact about what becomes possible afterwards, and a confirmation is not the place to sell a
 * consequence.
 */

/**
 * The control, on the game screen — **quiet, destructive, and last**, behind the sheet below.
 *
 * The visible label is the whole sentence, so it is the accessible name too: unlike `Withdraw`,
 * which says one word and names what it withdraws to a listener, there is no shorter form that a
 * reader would want.
 */
export const LEAVE_THIS_GAME = 'Leave this game';

/** The departure while it is in flight, on the control that carries it out. */
export const LEAVING = 'Leaving…';

/** The title names the moment, so the act is named once — by {@link LEAVE_THE_GAME}. */
export const LEAVE_SHEET_TITLE = 'Before you leave';

/**
 * The three bodies, in order: what survives, what the leaver gives up, and that it cannot be
 * undone. The first line is the whole reason the act exists (#411: *the others keeping what they
 * agreed rather than starting over*), and the second is the one cost that is theirs alone.
 */
export const LEAVE_SHEET_BODY = [
  'The others keep the game and can fill your seat.',
  "You can't be asked back into this one.",
  'This cannot be undone.',
] as const;

/** The act, on the sheet that confirms it. */
export const LEAVE_THE_GAME = 'Leave the game';

/** The sheet's dismissal, **named by what it does** — never just *Close*. */
export const LEAVE_SHEET_CLOSE_LABEL = 'Stay in';
