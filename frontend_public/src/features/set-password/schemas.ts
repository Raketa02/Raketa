import type { FormState } from '@/ui/forms';

/**
 * **The checks a link's page makes on what arrives from outside**, for the invitation page and the
 * reset page alike: the token and the mark in its address, and the form's two boxes. A box is
 * refused with the backend's own code where it has one (`password_too_weak`), so a sentence is
 * written once whichever side refused; the site's own codes are `password_required`,
 * `repeat_required` and `passwords_differ`.
 */

export const PASSWORD_FIELDS = ['password', 'repeat'] as const;
export type PasswordField = (typeof PASSWORD_FIELDS)[number];

/** What the form shows after a submission: codes under the boxes, or one over the form. */
export type PasswordFormState = FormState<PasswordField>;

/** The longest a password may be, on every account (the backend's `RawPassword`). */
const PASSWORD_MAX = 128;

/**
 * **What a link's token could be**: the URL-safe letters the backend mints one from, within what
 * a request may carry. The token arrives in the address, so it is untrusted route input (ADR-0187
 * §7): anything else leads nowhere without asking the backend, and nothing else is ever put into
 * a link this site draws.
 */
const A_TOKEN = /^[A-Za-z0-9_-]{1,256}$/;

export function isAToken(value: unknown): value is string {
  return typeof value === 'string' && A_TOKEN.test(value);
}

/**
 * **Where a set lands**: back on the link's page, marked `?password=set`, so the page reads the
 * link again (spent now) and says what to do next rather than that it was used. A mark somebody
 * writes by hand on a link that still works changes nothing: the page trusts the link's state.
 */
export const JUST_SET = { param: 'password', value: 'set' } as const;

export function wasJustSet(value: string | string[] | undefined): boolean {
  return value === JUST_SET.value;
}

/**
 * A password being **chosen**, under the one rule every account shares: 8 to 128 characters,
 * with an ASCII letter and a digit, as the backend's regex counts them; and typed again the same.
 */
export function checkNewPassword(
  password: string,
  repeat: string,
): Partial<Record<PasswordField, string>> {
  if (password === '') return { password: 'password_required' };
  const fits = password.length >= 8 && password.length <= PASSWORD_MAX;
  if (!(fits && /[A-Za-z]/.test(password) && /\d/.test(password))) {
    return { password: 'password_too_weak' };
  }
  if (repeat === '') return { repeat: 'repeat_required' };
  return repeat === password ? {} : { repeat: 'passwords_differ' };
}
