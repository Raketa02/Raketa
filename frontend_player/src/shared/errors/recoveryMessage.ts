/**
 * A failure, as a sentence a player can act on — chosen by **recovery category**.
 *
 * Never by the backend's `message`. That is a diagnostic written for a log, and rendering
 * it ships English into every locale and lets a copy edit on the server change what an
 * already-installed app says.
 *
 * The categories were assigned precisely so that a failure could say something true about
 * what to do next — including one this build has never seen — which is why this is the
 * fallback under every feature's `code` table rather than a single "Something went wrong".
 *
 * **It lives in `shared/` because three features now need it.** Auth and onboarding each
 * held a copy of this table, and the second one recorded the rule: a third copy is the
 * signal to move it. The Player profile is the third. What stays local to a feature is the
 * `code` table above it — those sentences are about that feature's conflicts and belong
 * beside them.
 */

import type { AppError } from './AppError';

const BY_RECOVERY: Readonly<Record<AppError['recovery'], string>> = {
  'retryable-automatically': "We couldn't reach Rakieta. Check your connection and try again.",
  'retryable-by-user': "That didn't go through. Try again in a moment.",
  'requires-reauthentication': 'Your session has ended. Sign in again.',
  'requires-user-correction': 'Check the details above and try again.',
  'business-conflict': "That can't be done right now.",
  terminal: 'Something went wrong at our end. Try again later.',
};

export function recoveryMessage(error: AppError): string {
  return BY_RECOVERY[error.recovery];
}

/**
 * A feature's `code` table, read over that fallback — **the two halves in one call**.
 *
 * The table stays local to its feature: those sentences are about that feature's conflicts and
 * belong beside them. What is shared is the *lookup*, which was written identically three
 * times — `authErrorMessage`, the photo step's upload failures, and Play's refusals — and this
 * file's own rule is that the third copy is the signal to promote. Three copies of two lines is
 * three places for one to stop falling back.
 *
 * `noUncheckedIndexedAccess` is what makes the fallback reachable rather than remembered:
 * `table[code]` is already `string | undefined`, so a code this build has never seen cannot be
 * read as a sentence.
 */
export function codeMessage(table: Readonly<Record<string, string>>, error: AppError): string {
  const known = error.code === undefined ? undefined : table[error.code];
  return known ?? recoveryMessage(error);
}
