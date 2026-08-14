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
 * about what to do next — even one this build has never seen.
 */

import type { AppError } from "@/shared/errors";

const BY_CODE: Readonly<Record<string, string>> = {
  invalid_credentials: "That email and password don't match. Try again.",
  account_disabled: "This account has been disabled. Get in touch with us to reopen it.",
  email_already_registered: "That email already has an account. Sign in instead.",
  nickname_already_taken: "That nickname is taken. Pick another.",
};

const BY_RECOVERY: Readonly<Record<AppError["recovery"], string>> = {
  "retryable-automatically": "We couldn't reach Rakieta. Check your connection and try again.",
  "retryable-by-user": "That didn't go through. Try again in a moment.",
  "requires-reauthentication": "Your session has ended. Sign in again.",
  "requires-user-correction": "Check the details above and try again.",
  "business-conflict": "That can't be done right now.",
  terminal: "Something went wrong at our end. Try again later.",
};

export function authErrorMessage(error: AppError): string {
  const known = error.code === undefined ? undefined : BY_CODE[error.code];
  return known ?? BY_RECOVERY[error.recovery];
}

/**
 * Field-level messages the *server* produced, keyed to the form field they belong to.
 *
 * The two signup conflicts carry `details.field`, so the message lands under the box the
 * player has to change rather than in a banner above a form they must then re-scan.
 */
export function authErrorField(error: AppError): string | undefined {
  const field = error.details?.field;
  return typeof field === "string" ? field : undefined;
}
