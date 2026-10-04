/**
 * **Setting a password by a link: the words both pages share.** The rule is worded as the club
 * website words it, and the repeat as the app words it (`frontend_player`'s `authForms.ts`), by
 * copying them.
 */

export const PASSWORD_RULE = 'Use 8 to 128 characters, with at least one letter and one digit.';

/**
 * What a page's form is called and what its boxes and button say: each page has its own. A form
 * that is the page's whole point takes its title from the page instead.
 */
export interface PasswordFormWords {
  readonly title?: string;
  readonly lead?: string;
  readonly password: string;
  readonly repeat: string;
  readonly submit: string;
  readonly submitting: string;
}

/** The refusals under the two boxes, whichever side refused. */
export const PASSWORD_REFUSALS: Readonly<Record<string, string>> = {
  password_required: 'Type a password.',
  password_too_weak: PASSWORD_RULE,
  repeat_required: 'Repeat your password.',
  passwords_differ: "Those passwords don't match.",
};

/** Said only to a browser without JavaScript, which Next refuses a plain form post from. */
export const NEEDS_JAVASCRIPT =
  'Setting a password here needs JavaScript. Turn it on and reload this page, or set it in the app.';
