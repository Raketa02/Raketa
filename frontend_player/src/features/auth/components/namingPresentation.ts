/**
 * **Every sentence the naming step says.**
 *
 * One deck, on the rule the whole app is written to: a screen is assembled from words that live
 * in one place, never from templates inlined in a component. The refusals the box can show are
 * not here — the form's own sentences live with the schema they belong to, the handle's rule
 * among them, and the server's `nickname_already_taken` with the other codes in
 * `authErrorMessage`.
 */

/** The eyebrow over the title: the same word the sign-up form and the sports picker open with. */
export const NAMING_EYEBROW = 'Raketa';

/**
 * The step's title, and **the question it is** — asked in the second person, because the
 * answer is how the player wants to be seen rather than a record the platform is filling in
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 */
export const NAMING_TITLE = 'How should people see you?';

/** The one box: the nickname is all the naming asks. */
export const NICKNAME_LABEL = 'Nickname';

/**
 * The one control, and what it promises. *Continue* rather than *Save*: the naming is the
 * first step of a walk, and the sentence under the button is where the walk goes next — the
 * profile steps, since a level is asked where play begins rather than here
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1, #730).
 */
export const CONTINUE = {
  label: 'Continue',
  busyLabel: 'Saving…',
  hint: 'Next, what kind of player you are',
} as const;

/**
 * **Under the title, for an account an Invitation opened** (ADR-0199 §3). Its club has known it by
 * the name the club typed, which stays the Administrator's; the line says what the nickname is
 * for, since it is the first thing the account is asked as a player.
 */
export const INVITED_LINE = "Pick a nickname — it's how players will see you.";
