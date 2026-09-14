/**
 * **Every word *Call it off* says** — the control, its busy label, and the sheet in front of it
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.9, on §22.3's shape;
 * [#419](https://github.com/Raketa02/Raketa/issues/419),
 * [ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).
 *
 * A deck of its own beside `leaveGamePresentation.ts`, for the same reason: the act is pressed on
 * the **game** screen, and copy lives beside the surface that says it. What differs from the leave
 * is that this act **is the withdraw** — the same route, the same sheet, reworded for a court that
 * has been a game: withdrawing a half-built court ends an arrangement, and calling a game off ends
 * a game the others had agreed to play.
 *
 * ## The withdraw's shape, and the two lines that change
 *
 * A title naming the **moment**, three body lines, the act named once on the control that carries
 * it out, a dismissal named by what it does. The second body line was the withdraw's own — *the
 * conversation goes with it* — and since [#428](https://github.com/Raketa02/Raketa/issues/428)
 * retired the withdraw's deck it lives here alone: ADR-0142's *destroyed, not delisted* holds on a
 * game's room, and a confirmation that did not say so would be hiding the only consequence nobody
 * can undo. The first line names what the act ends: not *this court*, which is the challenge's
 * word, but *this game*, because that is what the people still in it lose.
 *
 * **Nothing here says the pair rule releases**, on the withdraw's own line (`the-words.md` §22.3).
 */

/**
 * The control, on the game screen — **quiet, destructive, above *Leave this game***, behind the
 * sheet below — and the act on the sheet that confirms it, under one word.
 *
 * One label for both, on `SEND_CHALLENGE_LABEL`'s precedent: the act is named once, and the sheet
 * hides the screen behind it, so the first press can only reach the control and the second can
 * only reach the sheet's act. The visible label is the whole sentence, so it is the accessible
 * name too.
 */
export const CALL_IT_OFF = 'Call it off';

/** The call-off while it is in flight, on the control that carries it out. */
export const CALLING_IT_OFF = 'Calling it off…';

/** The title names the moment, so the act is named once — by {@link CALL_IT_OFF}. */
export const CALL_OFF_SHEET_TITLE = 'Before you call it off';

/**
 * The three bodies, in order: what everybody loses, what goes with it, and that it cannot be
 * undone. The second was the withdraw's own line, kept here because the room is destroyed in the
 * act exactly as it was for any withdrawal.
 */
export const CALL_OFF_SHEET_BODY = [
  'Everybody loses this game.',
  'The conversation goes with it, and what people wrote is deleted.',
  'This cannot be undone.',
] as const;

/** The sheet's dismissal, **named by what it does** — never just *Close*. */
export const CALL_OFF_SHEET_CLOSE_LABEL = 'Keep it';
