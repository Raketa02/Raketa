/**
 * **The departure sheet's own words** — *Before you leave*, its default lines, the act, the act in
 * flight, and *Stay in* — for `LeaveSheet` beside it.
 *
 * They were the challenge's departure deck's (`features/challenges/components/leaveGamePresentation.ts`)
 * and came here with the sheet ([#574](https://github.com/Rakieta02/Rakieta/issues/574)): a booked
 * game's *Leave the game* is the sheet's caller that stays, and it hands the sheet its own body
 * (`leavingSheetBody`). What the Chats row's door says — the list's line, the ending line and the
 * refusals — stayed with that door, which is the old loop's.
 */

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

/**
 * The act, on the sheet that confirms it — and, since #427, the control a Chats row reveals and
 * the challenge screen draws before the court is whole. One label on the control and on the
 * sheet's act, on `Send the challenge`'s precedent: the act is named once, and what is under the
 * sheet is hidden while it is up.
 */
export const LEAVE_THE_GAME = 'Leave the game';

/** The sheet's dismissal, **named by what it does** — never just *Close*. */
export const LEAVE_SHEET_CLOSE_LABEL = 'Stay in';
