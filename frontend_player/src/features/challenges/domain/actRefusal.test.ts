/**
 * **What a refused act on the challenge screen costs it** — three arms, and the whole point is
 * which codes reach which one.
 *
 * `sendRefusal.test.ts`'s shape one file over, and it is here for the property the module argues
 * for and nothing else could check: the re-read set is a `Set` of six literals *because the list
 * is now long enough that a missing `||` would read as deliberate*. A `Set` with a code missing
 * from it fails nothing at compile time — it quietly says the sentence instead of reading the
 * challenge again, on a screen whose whole discipline is that a stale tap is a re-read.
 */

import { AppError } from '@/shared/errors';

import { actRefusal } from './actRefusal';

/** The shape the code tables read — the `code`, never the backend's own message. */
const refused = (code: string): AppError =>
  new AppError('conflict', 'business-conflict', 'test failure', { code });

/**
 * Every code that means *this challenge is not what the screen thought it was*.
 *
 * Listed rather than imported, so the test states the set independently: a code deleted from the
 * module's own `Set` would otherwise delete itself from the assertion in the same edit.
 */
const READ_IT_BACK = [
  // The two answers': the window closed under the finger, and the two-devices case.
  'answer_window_has_passed',
  'seat_already_answered',
  // The withdraw's: this court has some other end already, and the reader is not the organiser.
  'not_a_half_built_line_up',
  'withdraw_is_the_organisers',
  // The fill's: the reader left the court while they were building on it, and it ended under
  // the builder.
  'fill_is_the_live_members',
  'challenge_is_over',
];

describe('a refused act', () => {
  it.each(READ_IT_BACK)('re-reads the challenge on %s', (code) => {
    expect(actRefusal(refused(code))).toEqual({ kind: 'READ_IT_BACK' });
  });

  /**
   * One code for two cases on purpose — it does not exist, or you are not on its court — so
   * there is nothing to tell apart and nowhere to stay.
   */
  it('leaves the screen when no challenge of yours has this id', () => {
    expect(actRefusal(refused('challenge_not_found'))).toEqual({ kind: 'LEAVE' });
  });

  it('says what it says, and reads nothing, for anything else', () => {
    const held = refused('account_held');

    expect(actRefusal(held)).toEqual({ kind: 'SAY_SO', error: held });
  });

  /**
   * **It is a code and never a status.** Two of the re-read arms are `409` and so is
   * `challenge_gates_unavailable`'s sibling family; branching on the status would send a
   * transient platform failure off to re-read a challenge that has not moved.
   */
  it('does not re-read a refusal that shares a status with one that does', () => {
    expect(actRefusal(refused('nobody_new_to_invite')).kind).toBe('SAY_SO');
    expect(actRefusal(refused('open_challenge_stands')).kind).toBe('SAY_SO');
  });

  /** A transport failure never reached the server, so there is no code and nothing to re-read. */
  it('says so about a request that never arrived', () => {
    const offline = new AppError('network-unavailable', 'retryable-automatically', 'no signal');

    expect(actRefusal(offline)).toEqual({ kind: 'SAY_SO', error: offline });
  });
});
