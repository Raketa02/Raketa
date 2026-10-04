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

import { codeMessage, type AppError } from '@/shared/errors';

import { ADULT_ATTESTATION_MISSING, PASSWORD_RULE, type FieldErrors } from '../schemas/authForms';

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
  /**
   * The server's copy of the one password rule, on `details.field: password` — the rule itself,
   * because the form already said which half was missing and this is the server disagreeing.
   */
  password_too_weak: PASSWORD_RULE,
  /**
   * A code that is not the one sent to that address — **or no code was sent to it**: the server
   * gives the two one answer, so this sentence cannot say which (ADR-0184 §5). Under the box.
   */
  code_incorrect: "That isn't the code we sent to that email. Check it and type it again.",
};

export function authErrorMessage(error: AppError): string {
  return codeMessage(BY_CODE, error);
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

/**
 * **What a box says under itself** — the form's own refusal first, else the server's where it
 * named this field, else nothing.
 *
 * One rule for the two forms that render a server conflict under a box: the form's message wins
 * because it was raised against what is in the box *now*, and a server refusal against the same
 * field is what the player reads once the form has nothing to say. A refusal against no field is
 * the banner's, and this answers nothing for it — `bannerMessage` is that half.
 */
export function errorUnderField(
  field: string,
  fieldErrors: FieldErrors,
  serverError: AppError | null,
  message: (error: AppError) => string = authErrorMessage,
): string | undefined {
  const own = fieldErrors[field];
  if (own !== undefined) return own;
  if (serverError !== null && authErrorField(serverError) === field) {
    return message(serverError);
  }
  return undefined;
}

/**
 * The banner's sentence: a server refusal that names **no** field. One that names a field is
 * rendered under that box by {@link errorUnderField} and must not be said twice.
 *
 * Both take the screen's own sentences where it has them — the recovery screens word a refusal
 * by how the person got there — and the auth-wide table otherwise.
 */
export function bannerMessage(
  serverError: AppError | null,
  message: (error: AppError) => string = authErrorMessage,
): string | undefined {
  if (serverError === null || authErrorField(serverError) !== undefined) return undefined;
  return message(serverError);
}
