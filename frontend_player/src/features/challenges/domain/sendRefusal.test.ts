/**
 * What a refused send costs the screen next.
 *
 * The claim under test is **the branch is the code and never the status**: all three refusals
 * below are `409`, and one of them is not about staleness at all.
 */

import { AppError } from '@/shared/errors';

import { sendRefusal } from './sendRefusal';

const conflict = (code: string) =>
  new AppError('conflict', 'business-conflict', 'a diagnostic', { code, status: 409 });

describe('what the court does about a refusal', () => {
  it('reads the origin search back when the line-up went out of date', () => {
    expect(sendRefusal(conflict('line_up_no_longer_sendable'))).toEqual({
      kind: 'READ_THE_ORIGIN_BACK',
    });
  });

  it('reads the player’s own challenges when the pair rule fired', () => {
    expect(sendRefusal(conflict('open_challenge_stands'))).toEqual({
      kind: 'READ_YOUR_CHALLENGES',
    });
  });

  /**
   * The same status as both of the above, and neither of them: an orphaned origin sent off to
   * re-read a search that is gone would be a request answering the question with itself.
   */
  it('reads nothing for a third 409 that is not about anybody’s state', () => {
    const orphaned = conflict('court_origin_not_found');

    expect(sendRefusal(orphaned)).toEqual({ kind: 'SAY_SO', error: orphaned });
  });

  it('reads nothing for a failure that carries no code at all', () => {
    const offline = new AppError('network-unavailable', 'retryable-automatically', 'no socket');

    expect(sendRefusal(offline)).toEqual({ kind: 'SAY_SO', error: offline });
  });
});
