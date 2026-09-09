/**
 * Backend `code` → the sentence an act in this feature writes, over `recoveryMessage`'s fallback.
 *
 * It began as the send's alone and is now the feature's: the challenge screen's two answers write
 * their refusals through it too ([#361](https://github.com/Raketa02/Raketa/issues/361)), which is
 * what keeps *no new copy* true of that screen — an `account_held` is one fact with one remedy
 * whether it refused a send or an acceptance.
 *
 * The shape is `features/play/components/playErrorMessage.ts`' and the reason is the same:
 * localization goes **code → message, never message → message**, and the fallback under the
 * table is by *recovery category*, so a code this build has never seen still says something true
 * about what to do next.
 *
 * ## The two refusals are not in here, and that is the point
 *
 * `line_up_no_longer_sendable` and `open_challenge_stands` are followed by a **re-read** rather
 * than by a sentence chosen off the code, and what they end up saying depends on what that read
 * found — a marked seat, a name, or the dead end. They are `domain/sendRefusal.ts`'s arms, and
 * their words are `challengePresentation.ts`'. A row for either here would be a second place
 * for one refusal to have an answer.
 *
 * ## The 400 family is a caller's bug and gets no row
 *
 * `challenge_with_no_invitee`, `organiser_holds_a_seat`, `one_person_to_a_seat`,
 * `cannot_challenge_yourself` and `court_is_not_the_sports` are *"every one of them a caller's
 * bug"*, and this client cannot produce one: the court it sends is the court the builder drew,
 * with the organiser's own seat in it and the sport's own shape. Writing five sentences for
 * five states that would each be a defect here is copy nobody can reach, and it would read as
 * though the player had done something wrong. They fall through to
 * `requires-user-correction`'s sentence, which is the honest thing to say about a request this
 * app should not have made.
 */

import { codeMessage, offlineMessage, type AppError } from '@/shared/errors';

const BY_CODE: Readonly<Record<string, string>> = {
  /**
   * No search of yours showed all of those players — **one code for four cases, on purpose**.
   *
   * The same shape as `search_not_found` one context over, and the same remedy: the origin is
   * gone, so the way on is a new search rather than another press. Telling the four cases apart
   * *"would answer questions about strangers one probe at a time"*.
   */
  court_origin_not_found: 'That search is no longer available. Run a new one to keep going.',
  /**
   * A `403` about the account, refused **at the entry point**.
   *
   * The same sentence Play writes for the same code, because it is one fact with one remedy —
   * and a hold that stopped you searching but let you send invitations would be that hole with
   * the blast radius pointed at other people.
   */
  account_held: 'Your account is on hold. Get in touch with us.',
  /**
   * A safety gate could not be read, so **nothing was minted** — transient, and about the
   * platform rather than about anybody on the court.
   *
   * It names no mechanism: *a gate* is our word for our problem, and a player reading it learns
   * only that something they cannot see is broken. The same argument `playErrorMessage` makes
   * for its four 503s, arriving here as one because this route has one.
   */
  challenge_gates_unavailable: "We couldn't send it just now. Try again in a moment.",
};

export function challengeErrorMessage(error: AppError): string {
  // Before the table, because it is about the transport rather than about a refusal: nothing
  // reached the server, so there is no `code` for the table to read.
  if (error.kind === 'network-unavailable') return offlineMessage('does-not-resume');
  return codeMessage(BY_CODE, error);
}
