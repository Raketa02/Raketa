/**
 * **The checks the signed-out forms make before anything leaves**, refusing with the codes the
 * backend uses where it has one, so a sentence is written once whichever side refused.
 *
 * The website's own codes: `email_required`, `password_required`, `code_required` and
 * `code_wrong_length`. A code of the wrong length is refused here, before it spends one of the
 * five attempts the backend allows (ADR-0184 §3).
 */

import { z } from 'zod';

import { DETAILS_FIELDS } from '@/features/club-details/schemas';

export const SIGN_IN_FIELDS = ['email', 'password'] as const;
export type SignInField = (typeof SIGN_IN_FIELDS)[number];

export const SIGN_UP_FIELDS = [...DETAILS_FIELDS, 'email', 'password'] as const;
export type SignUpField = (typeof SIGN_UP_FIELDS)[number];

export const ASK_FIELDS = ['email'] as const;
export type AskField = (typeof ASK_FIELDS)[number];

export const CODE_FIELDS = ['email', 'code'] as const;
export type CodeField = (typeof CODE_FIELDS)[number];

export const NEW_PASSWORD_FIELDS = ['password'] as const;
export type NewPasswordField = (typeof NEW_PASSWORD_FIELDS)[number];

/** The longest a password may be, on every account (the backend's `RawPassword`). */
const PASSWORD_MAX = 128;
const CODE_LENGTH = 8;
/** A link's token, as the backend bounds what a request may carry. */
const TOKEN_MAX = 256;

const email = z.email();

export function checkEmail(value: string): 'email_required' | 'email_invalid' | null {
  if (value.trim() === '') return 'email_required';
  return email.safeParse(value.trim()).success ? null : 'email_invalid';
}

/** A password being signed in with: anything the desk types, within what a request may carry. */
export function checkTypedPassword(value: string): 'password_required' | null {
  return value === '' ? 'password_required' : null;
}

export function isSendablePassword(value: string): boolean {
  return value.length <= PASSWORD_MAX;
}

/**
 * A password being **chosen**, under the one rule every account shares: 8 to 128 characters,
 * with an ASCII letter and a digit, as the backend's regex counts them.
 */
export function checkChosenPassword(
  value: string,
): 'password_required' | 'password_too_weak' | null {
  if (value === '') return 'password_required';
  const fits = value.length >= 8 && value.length <= PASSWORD_MAX;
  return fits && /[A-Za-z]/.test(value) && /\d/.test(value) ? null : 'password_too_weak';
}

/** Read as the backend reads it: case, spaces and dashes are ignored. */
export function normaliseCode(value: string): string {
  return value.replace(/[\s-]+/g, '').toUpperCase();
}

export function checkCode(value: string): 'code_required' | 'code_wrong_length' | null {
  const code = normaliseCode(value);
  if (code === '') return 'code_required';
  return code.length === CODE_LENGTH ? null : 'code_wrong_length';
}

/** A token from a link: never empty, never longer than a request may carry. */
export function isPlausibleToken(value: string): boolean {
  return value.length > 0 && value.length <= TOKEN_MAX;
}
