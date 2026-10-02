/**
 * Backend `code` → the sentence these screens write, over `recoveryMessage`'s fallback.
 *
 * The shape is `features/challenges/components/challengeErrorMessage.ts`' and the reason is the
 * same: localization goes **code → message, never message → message**, and the fallback under
 * the table is by *recovery category*, so a code this build has never seen still says something
 * true about what to do next.
 *
 * ## Every refusal the aggregate makes has a sentence here
 *
 * That is the ticket's own acceptance criterion, and it is why this table is longer than the
 * screens' own reachable states: five of these are races rather than mistakes — the other side
 * answered while a correction was being typed, a partner accepted while a counter was open, the
 * entry window closed between the list being read and the tap. A race has to say what happened
 * and never that the player did something wrong.
 *
 * ## Three of them are refusals about a score this app already refuses
 *
 * `a_result_must_carry_a_score`, `a_score_must_name_a_winner` and `a_score_is_not_this_shape` are
 * checked by `domain/score.ts` before a round trip, so a current build cannot produce one. They
 * keep their sentences anyway, for the reason the adult attestation's refusal keeps its: an
 * older build or a replayed request can carry a body this grid would not have sent, and *try
 * again* would then be the one thing that is not true.
 *
 * ## `you_were_not_on_this_court` is one code for two cases, and it stays one
 *
 * *No game of yours has that id* — it does not exist, or you did not play in it. The server
 * refuses to separate them because separating them would answer *is this id real* about four
 * strangers' evening, and this sentence keeps the refusal rather than undoing it.
 */

import { codeMessage, offlineMessage, type AppError } from '@/shared/errors';

const BY_CODE: Readonly<Record<string, string>> = {
  you_were_not_on_this_court: 'No game of yours has this address.',
  /** A `409`: the game already reads as never played to everybody who has looked at it. */
  the_entry_window_has_closed:
    'The window for saying this one happened has closed, so it stays unrecorded. Nobody is marked for that.',
  /** A settled result is final — and *settled* includes the game that produced no result. */
  the_result_is_settled: 'This game is settled now, so nothing more can be changed about it.',
  /** The cap that bounds the argument to two rounds, and makes silence safe to read. */
  your_side_has_already_answered:
    'Your side has already put a score on the table, and each side gets one.',
  /**
   * A correction that arrived after the other side responded. It is a race, not a mistake — and
   * it can now **say when**, which it could not before the response carried an acceptance: the
   * answer may have landed a second ago or five hours ago inside the grace, and this sentence
   * had to be vague about which.
   *
   * What makes it sayable is not a field but the **control's own absence**. An agreement on the
   * response takes the correction away (`domain/resultArgument.ts`), so the only way to reach this
   * refusal is an answer that arrived after the list this screen is drawn from was read. The
   * acceptance's own `agreed_at` cannot be quoted here and never could be — at the moment of the
   * refusal there is no acceptance on this side to read it off.
   */
  the_other_side_has_answered:
    'The other side answered while this screen was open, so this score cannot be changed any more.',
  nobody_has_proposed_a_result: 'There is no score from the other side to agree with.',
  /** A teammate agreeing with a teammate proves nothing, so only the other side may. */
  accepting_your_own_sides_result: 'Only the other side can agree with a score.',
  the_result_is_already_accepted: 'Your side has already agreed to this score.',
  a_result_must_carry_a_score: 'A score has to go with this — there is no bare disagreement.',
  a_score_must_name_a_winner: 'A score has to name a winner.',
  a_score_is_not_this_shape: 'That is not the shape of a score.',
  /**
   * A `403` about the account, refused at the entry point — the same sentence Play and
   * `challenges` write for the same code, because it is one fact with one remedy.
   */
  account_held: 'Your account is on hold. Get in touch with us.',
  /** A score refused because somebody was marked as not coming while the screen was open (#560). */
  a_no_show_is_reported:
    'Somebody was marked as not coming, so this game doesn’t count and takes no score.',
  // Marking somebody as not coming (#560) — the route's refusals, most of them races.
  not_on_this_court: 'That player isn’t on this game.',
  you_cannot_report_yourself: 'You can’t mark yourself as not coming.',
  no_shows_are_for_booked_games: 'Only a game booked on a court can have somebody not come.',
  the_game_has_not_started: 'The game hasn’t started yet.',
  a_result_is_entered:
    'A score went in while this screen was open, so the game happened — answer the score instead.',
  checked_in_at_the_club: 'The club checked them in, so they were there.',
  you_were_reported_as_a_no_show:
    'You were marked as not coming yourself — say you were there instead.',
  // These two refuse a score as well as a mark, so their sentences say only what both share.
  the_game_was_called_off: 'This game was called off, so there is nothing to record.',
  the_game_started_short:
    'This game started with a seat empty, so nothing about it can be recorded.',
  // Disputing one (#560).
  nobody_reported_you: 'Nobody marked you as not coming.',
  the_dispute_window_has_closed: 'Your day to say you were there has passed, so the mark stands.',
};

export function gameErrorMessage(error: AppError): string {
  // Before the table, because it is about the transport rather than about a refusal: nothing
  // reached the server, so there is no `code` for the table to read. Both writes here pause
  // rather than failing, so the sentence is the one that promises they resume.
  if (error.kind === 'network-unavailable') return offlineMessage('resumes');
  return codeMessage(BY_CODE, error);
}

/**
 * **A refused mark** (#560) — the table above, except where its sentence is about a score: the
 * entry window closing, or the game settling, on a game somebody was marked on is a mark that came
 * too late, not an evening going unrecorded. The rows go on being offered while a report's day runs
 * (`domain/noShows.ts`), and the window behind them is not on the wire once a report is made.
 */
const MARK_BY_CODE: Readonly<Record<string, string>> = {
  the_entry_window_has_closed: 'It’s too late to mark anybody else on this game.',
  the_result_is_settled: 'This game is settled now, so nobody else can be marked.',
};

export function markErrorMessage(error: AppError): string {
  if (error.kind === 'network-unavailable') return offlineMessage('resumes');
  return codeMessage({ ...BY_CODE, ...MARK_BY_CODE }, error);
}
