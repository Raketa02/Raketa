/**
 * **Every sentence the naming step says.**
 *
 * One deck, on the rule the whole app is written to: a screen is assembled from words that live
 * in one place, never from templates inlined in a component. The two refusals a box can show
 * are not here — the form's own sentences live with the schema they belong to, and the
 * server's `nickname_already_taken` with the other codes in `authErrorMessage` — and the
 * nickname's rule is quoted from the schema rather than spelled twice.
 */

/** The eyebrow over the title: the same word the sign-up form and welcome open with. */
export const NAMING_EYEBROW = 'Raketa';

/**
 * The step's title, and **the question it is** — asked in the second person, because the
 * answer is how the player wants to be seen rather than a record the platform is filling in
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §1).
 */
export const NAMING_TITLE = 'How should people see you?';

/**
 * The two boxes, in the order the ADR asks them: the name first, because it is what everyone
 * sees, and the handle under it.
 */
export const NAME_LABEL = 'Name';
export const NICKNAME_LABEL = 'Nickname';

/**
 * The one control, and what it promises. *Continue* rather than *Save*: the naming is the
 * first step of a walk, and the sentence under the button is where the walk goes next.
 */
export const CONTINUE = {
  label: 'Continue',
  busyLabel: 'Saving…',
  hint: 'Next, a few questions to find your level',
} as const;
