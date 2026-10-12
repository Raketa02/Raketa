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

import { LocationAtTheTap, type AttendanceError } from '../hooks/useAttendance';

import { LOCATION_AT_THE_TAP } from './gamePresentation';

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
  /**
   * A score refused while somebody tapped *isn't here yet* is awaited (#658) — reached by a race:
   * somebody was tapped while the grid was open.
   */
  somebody_is_not_here_yet:
    'Somebody isn’t here yet, so the score waits until they arrive or the half hour is over.',
  /** A score refused on a game somebody didn't come to — the half hour ran out meanwhile. */
  somebody_did_not_come: 'Somebody didn’t come, so this game takes no score.',
  /** No score before the hour (#654) — and no tap either, which `ATTENDANCE_BY_CODE` says. */
  the_game_has_not_started:
    'This game hasn’t started yet, so there’s no score to put up. It can go in once the hour has begun.',
  // These two refuse a score as well as a tap, so their sentences say only what both share.
  the_game_was_called_off: 'This game was called off, so there is nothing to record.',
  the_game_started_short:
    'This game started with a seat empty, so nothing about it can be recorded.',
  not_on_this_court: 'That player isn’t on this game.',
};

export function gameErrorMessage(error: AppError): string {
  // Before the table, because it is about the transport rather than about a refusal: nothing
  // reached the server, so there is no `code` for the table to read. Both writes here pause
  // rather than failing, so the sentence is the one that promises they resume.
  if (error.kind === 'network-unavailable') return offlineMessage('resumes');
  return codeMessage(BY_CODE, error);
}

/** **Which of the four acts at the court was refused** — some codes mean something different on each. */
export type AttendanceAct = 'not-here-yet' | 'arrival' | 'claim' | 'confirmation';

/**
 * **A refused tap at the court, or a refused late claim** (#658) — the table above, except where its
 * sentence is about a score: a game that has not started refuses a tap as well as a score, and says
 * so as a tap. Most of these are races — the half hour running out between the read and the tap,
 * somebody arriving while their *they're here* was being pressed.
 */
const ATTENDANCE_BY_CODE: Readonly<Record<string, string>> = {
  the_game_has_not_started: 'The game hasn’t started yet — you can say who’s here from its start.',
  the_tap_window_has_closed:
    'The first half hour is over, so it’s too late to say who’s here. A later arrival can’t be noted.',
  not_about_yourself: 'You can’t say that about yourself.',
  attendance_is_for_booked_games: 'Only a game booked on a court has anybody to wait for.',
  the_result_is_settled: 'This game is settled now, so nobody can be noted as not here.',
  the_tap_window_is_open:
    'The first half hour isn’t over yet — if you’re at the club, tap I’m here instead.',
  the_late_claim_has_closed: 'The day to say you were there has passed, so Didn’t come stands.',
  /** A fix the phone produced that is not a place — an older or broken build; never this one's. */
  a_location_fix_is_off_the_map:
    'Your phone sent a position that isn’t on the map. Try again in a moment.',
};

/** The codes that mean one thing on one act and another on the next. */
const BY_ACT: Readonly<Record<AttendanceAct, Readonly<Record<string, string>>>> = {
  'not-here-yet': {
    already_arrived: 'They’re already here — their arrival is noted.',
    you_are_not_here_yourself: 'You’re awaited yourself, so you can’t say who else is here.',
  },
  arrival: {
    already_arrived: 'That arrival is already noted — the first one counts.',
    you_are_not_here_yourself: 'You’re awaited yourself, so you can’t say who else is here.',
    nobody_said_they_were_not_here:
      'Nobody said they weren’t here, so there’s no arrival to note — on time is nothing at all.',
  },
  claim: {
    already_arrived: 'Your arrival is already noted, so there’s nothing to claim.',
    nobody_said_they_were_not_here: 'Nobody said you weren’t here, so there’s nothing to claim.',
  },
  confirmation: {
    nothing_to_confirm: 'They haven’t said they were there, so there’s nothing to confirm.',
    already_arrived: 'Their arrival is already noted, so there’s nothing to confirm.',
    you_are_not_here_yourself: 'You didn’t come yourself, so you can’t confirm anybody.',
    nobody_said_they_were_not_here: 'Nobody said they weren’t here, so there’s nothing to confirm.',
    the_late_claim_has_closed:
      'The day to confirm they were there has passed, so Didn’t come stands.',
  },
};

/**
 * **The sentence for a refused act at the court.** `club` is the booking's club's name, for the one
 * refusal that names it — *You can say so only from Ogrody 33* — and the club in general where the
 * booking no longer names one. A tap with no connection fails now rather than waiting
 * (`useAttendance`), so the two at the club say they were not sent; a claim or a confirmation
 * pauses, and that is the footer's paused note, not a failure.
 */
export function attendanceErrorMessage(
  error: AttendanceError,
  act: AttendanceAct,
  club: string | undefined,
): string {
  if (error instanceof LocationAtTheTap) return LOCATION_AT_THE_TAP[error.refusal];
  if (error.kind === 'network-unavailable') {
    return offlineMessage(
      act === 'not-here-yet' || act === 'arrival' ? 'does-not-resume' : 'resumes',
    );
  }
  if (error.code === 'not_at_the_club') return `You can say so only from ${club ?? 'the club'}.`;
  return codeMessage({ ...BY_CODE, ...ATTENDANCE_BY_CODE, ...BY_ACT[act] }, error);
}
