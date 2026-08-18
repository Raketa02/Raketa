/**
 * A failure, as a sentence a player can act on.
 *
 * Chosen by **recovery category**, not by the backend's `message` — the message is a
 * diagnostic written for a log, and rendering it ships English into every locale and lets
 * a copy edit on the server change what an already-installed app says.
 *
 * No `code` table yet: nothing in this slice has an error worth its own sentence. The
 * reads either work or the player is offline, and the one mutation — starting an
 * assessment — fails for transport reasons or not at all. The codes that need their own
 * copy arrive with the question loop (#24), where a duplicate submission and a stale
 * question are two conflicts with opposite recoveries.
 *
 * This duplicates the auth feature's table, which is deliberate: a feature never
 * deep-imports another, and moving a file to `shared/` because two features use it is how
 * `shared/` becomes a junk drawer. **A third copy is the signal to move it.**
 */

import type { AppError } from '@/shared/errors';

const BY_RECOVERY: Readonly<Record<AppError['recovery'], string>> = {
  'retryable-automatically': "We couldn't reach Raketa. Check your connection and try again.",
  'retryable-by-user': "That didn't go through. Try again in a moment.",
  'requires-reauthentication': 'Your session has ended. Sign in again.',
  'requires-user-correction': 'Check the details above and try again.',
  'business-conflict': "That can't be done right now.",
  terminal: 'Something went wrong at our end. Try again later.',
};

export function onboardingErrorMessage(error: AppError): string {
  return BY_RECOVERY[error.recovery];
}
