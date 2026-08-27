/**
 * Backend `code` -> the sentence a player reads.
 *
 * Localization goes **code -> message**, never message -> message. The backend's
 * `message` is a diagnostic written for a log; rendering it directly ships English into
 * every locale and lets a copy edit on the server change what an app already installed
 * says. So the copy lives here, chosen by the stable code.
 *
 * The fallback is by *recovery category* rather than a single "Something went wrong",
 * because the categories were assigned precisely so a failure could say something true
 * about what to do next — even one this build has never seen. That fallback table is
 * `shared/errors`' now: three features need it, and the copy of it that used to sit here
 * was the first of the three.
 */

import { recoveryMessage, type AppError } from '@/shared/errors';

import { ADULT_ATTESTATION_MISSING } from '../schemas/authForms';

const BY_CODE: Readonly<Record<string, string>> = {
  invalid_credentials: "That email and password don't match. Try again.",
  account_disabled: 'This account has been disabled. Get in touch with us to reopen it.',
  email_already_registered: 'That email already has an account. Sign in instead.',
  nickname_already_taken: 'That nickname is taken. Pick another.',
  /**
   * The server re-refusing what the tick box enforced — an older build, or a request
   * replayed after a rotation. It is **not** the generic *try again*, because the identical
   * body fails identically; it is the answer it names, in the same sentence the form
   * already uses for it, so the two cannot drift apart.
   */
  adult_attestation_required: ADULT_ATTESTATION_MISSING,
};

export function authErrorMessage(error: AppError): string {
  const known = error.code === undefined ? undefined : BY_CODE[error.code];
  return known ?? recoveryMessage(error);
}

/**
 * The wire's spelling of a field, translated to the form's.
 *
 * `email` and `nickname` are the same word on both sides, which is why nothing needed this
 * until a field arrived whose name is two words. The wire is snake_case because the API is;
 * the form is camelCase because the app is. Neither should bend to the other, so the
 * mapping is written down — an unlisted field falls through unchanged, which is exactly
 * what keeps the two identical ones working.
 */
const FORM_FIELD: Readonly<Record<string, string>> = {
  adult_attested: 'adultAttested',
};

/**
 * Field-level messages the *server* produced, keyed to the form field they belong to.
 *
 * The signup conflicts and the age refusal carry `details.field`, so the message lands
 * under the box the player has to change rather than in a banner above a form they must
 * then re-scan.
 */
export function authErrorField(error: AppError): string | undefined {
  const field = error.details?.field;
  if (typeof field !== 'string') return undefined;
  return FORM_FIELD[field] ?? field;
}
