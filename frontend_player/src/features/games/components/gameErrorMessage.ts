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
 * screens' own reachable states: several of these are races rather than mistakes — the other side
 * put a score up while a correction was being typed, somebody said *That's right* while a counter
 * was open, the entry window closed between the list being read and the tap. A race has to say
 * what happened and never that the player did something wrong.
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
  /**
   * A `409`: the window for a first score closed, and a full game nobody recorded reads *Played · no
   * score* to everybody who has looked at it (#655).
   */
  the_entry_window_has_closed:
    'The time to put a score up has passed, so this game counts as played, with no score.',
  /**
   * A `409` on a correction once the entry window has closed, a day after the hour (#654). The score
   * still stands, and the other side's day to answer it still runs.
   */
  corrections_have_closed:
    'It’s too late to change this score — that closed a day after the game. It still stands as it is.',
  /**
   * A settled result is final — and since #654 *That's right* settles one at once, so this is also
   * the race in which somebody agreed while this screen was open.
   */
  the_result_is_settled: 'This game is settled now, so nothing more can be changed about it.',
  /**
   * The cap that bounds the argument to two rounds, and makes silence safe to read. A correction
   * after the other side put its own score up is the same refusal (#654). With both scores up this
   * screen offers neither a correction nor a counter, so it is reached only by a race — the other
   * side's score, or a partner's counter, landing while the grid was open.
   */
  your_side_has_already_answered:
    'Both sides have a score up now, and each side gets one — so this one can’t go in.',
  nobody_has_proposed_a_result: 'There is no score from the other side to agree with.',
  /** A teammate agreeing with a teammate proves nothing, so only the other side may. */
  accepting_your_own_sides_result: 'Only the other side can agree with a score.',
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
  /** No score before the hour (#654) — and no mark either, which `MARK_BY_CODE` says. */
  the_game_has_not_started:
    'This game hasn’t started yet, so there’s no score to put up. It can go in once the hour has begun.',
  a_result_is_entered:
    'A score went in while this screen was open, so the game happened — answer the score instead.',
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
  the_game_has_not_started: 'The game hasn’t started yet.',
  the_entry_window_has_closed: 'It’s too late to mark anybody else on this game.',
  the_result_is_settled: 'This game is settled now, so nobody else can be marked.',
};

export function markErrorMessage(error: AppError): string {
  if (error.kind === 'network-unavailable') return offlineMessage('resumes');
  return codeMessage({ ...BY_CODE, ...MARK_BY_CODE }, error);
}
