/**
 * **What the Check in page posts, and what it refuses before asking the backend.** A code comes
 * one of two ways: what the camera read off a player's QR code, or the short code under it, typed
 * by hand.
 *
 * The local checks restate the backend's own reading of a code (`bookings/domain/check_in.py`):
 * a scan begins `RAKETA-CHECK-IN:`, and a typed code is six characters once spaces and dashes are
 * gone. The website's own codes: `check_in_code_required`, `code_wrong_length` and
 * `check_in_code_not_raketa` (a QR code that is somebody else's: a menu, a poster).
 */

import { formText } from '@/ui/forms';

/** Where the page is: under Bookings, which opens it. */
export const CHECK_IN_PATH = '/bookings/check-in';

/** A code's way in: the camera, or the box. */
export type Via = 'camera' | 'typed';

/** The box's one field. */
export type CodeField = 'code';

/** The characters a short code has, as the player's phone shows them. */
export const SHORT_CODE_LENGTH = 6;

/** Every scan of a Raketa check-in code begins so, whatever version follows. */
const SCAN_PREFIX = 'RAKETA-CHECK-IN:';

/** The longest code the backend reads: a scan is about a hundred characters. */
const LONGEST_CODE = 200;

/** A check-in as posted: its way in, and the code. */
export interface PostedCode {
  readonly via: Via;
  /** A scan as read; a typed code tidied: upper case, without spaces or dashes. */
  readonly code: string;
}

/** A typed code as the backend reads it: upper case, without the spaces and dashes put in it. */
export function tidyShortCode(typed: string): string {
  return typed.replace(/[\s-]/g, '').toUpperCase();
}

export function readCode(form: FormData): PostedCode {
  const via: Via = formText(form, 'via') === 'camera' ? 'camera' : 'typed';
  const code = formText(form, 'code');
  return { via, code: via === 'camera' ? code.trim() : tidyShortCode(code) };
}

/**
 * **Why the page will not ask about a code**, as a code, or `null` when it can go: a box left
 * blank, a typed code of the wrong length, a QR code that is not a Raketa check-in code.
 */
export function checkCode(posted: PostedCode): string | null {
  if (posted.via === 'camera') {
    const raketa =
      posted.code.toUpperCase().startsWith(SCAN_PREFIX) && posted.code.length <= LONGEST_CODE;
    return raketa ? null : 'check_in_code_not_raketa';
  }
  if (posted.code === '') return 'check_in_code_required';
  return posted.code.length === SHORT_CODE_LENGTH ? null : 'code_wrong_length';
}
