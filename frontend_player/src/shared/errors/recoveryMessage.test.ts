/**
 * The sentence under every feature's `code` table.
 *
 * What matters is not the wording — copy changes — but that **every category has one**.
 * This is the fallback a failure this build has never seen lands on, and the reason the
 * categories were assigned in the first place: a player should be told what to do next even
 * when nothing recognised the error.
 */

import { AppError } from './AppError';
import { codeMessage, recoveryMessage } from './recoveryMessage';

const EVERY_RECOVERY: readonly AppError['recovery'][] = [
  'retryable-automatically',
  'retryable-by-user',
  'requires-reauthentication',
  'requires-user-correction',
  'business-conflict',
  'terminal',
];

function failure(recovery: AppError['recovery']): AppError {
  return new AppError('server', recovery, 'a diagnostic nobody reads');
}

function coded(code: string): AppError {
  return new AppError('conflict', 'business-conflict', 'a diagnostic nobody reads', { code });
}

describe('the sentence a recovery category gets', () => {
  it('gives every category its own, so no failure falls through to nothing', () => {
    const said = EVERY_RECOVERY.map((recovery) => recoveryMessage(failure(recovery)));

    expect(said.every((sentence) => sentence.length > 0)).toBe(true);
    expect(new Set(said).size).toBe(EVERY_RECOVERY.length);
  });

  it('never renders the backend’s own message', () => {
    // Localization goes code → message, never message → message: the server's text is a
    // diagnostic written for a log, and rendering it ships English into every locale.
    expect(recoveryMessage(failure('terminal'))).not.toContain('a diagnostic nobody reads');
  });

  it('tells a player whose session ended what to do about it', () => {
    expect(recoveryMessage(failure('requires-reauthentication'))).toBe(
      'Your session has ended. Sign in again.',
    );
  });
});

describe('a feature’s code table over that fallback', () => {
  const TABLE = { a_known_code: 'The sentence that code owns.' };

  it('answers with the table when the code is one this build knows', () => {
    expect(codeMessage(TABLE, coded('a_known_code'))).toBe('The sentence that code owns.');
  });

  it('falls back by recovery category for a code added after this build shipped', () => {
    // Old app versions live on real phones for months, and the compiler cannot help here:
    // an error `code` is a wire string with no generated union behind it.
    expect(codeMessage(TABLE, coded('a_code_from_next_year'))).toBe(
      recoveryMessage(coded('a_code_from_next_year')),
    );
  });

  it('falls back for a failure that carried no code at all', () => {
    expect(codeMessage(TABLE, failure('terminal'))).toBe(recoveryMessage(failure('terminal')));
  });
});
