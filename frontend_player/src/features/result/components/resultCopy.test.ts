/**
 * The sentences no rendered test can reach.
 *
 * One of them is here for a reason worth stating: **the prototype-key half of the
 * failure table cannot be exercised end to end.** A backend code spelled `toString`
 * would have to survive `shared/errors/mapError.ts` to reach this table, and that
 * module indexes its own `Record<string, …>` with the same arbitrary string and
 * **throws** on the way — `classification is not iterable` — so the write fails with
 * a raw `TypeError` carrying no code at all, and this function is never asked.
 * Filed as `Raketa02/Raketa#121`, and asserted here on the function itself, which is
 * where the guard actually lives.
 */

import { AppError } from '@/shared/errors';

import { WRITE_FAILED, silenceLine, writeFailureLine } from './resultCopy';

function failedWith(code: string | undefined): AppError {
  return new AppError('validation', 'requires-user-correction', 'diagnostic', { code });
}

describe('what a failed write says', () => {
  it('names the one refusal that is about what she typed', () => {
    expect(writeFailureLine(failedWith('match_impossible_score'))).toMatch(
      /could not have been played/,
    );
  });

  it('falls back for a code this build has never heard of', () => {
    // A code, and no code at all: old app versions live on real phones for months,
    // and the backend will add codes this build has never seen.
    expect(writeFailureLine(failedWith('match_side_has_proposed'))).toBe(WRITE_FAILED);
    expect(writeFailureLine(failedWith(undefined))).toBe(WRITE_FAILED);
  });

  it('never resolves a code off Object.prototype', () => {
    // Without the own-property guard this returns `Object.prototype.toString` — a
    // function, handed to a `<Text>` as its child.
    expect(writeFailureLine(failedWith('toString'))).toBe(WRITE_FAILED);
    expect(writeFailureLine(failedWith('constructor'))).toBe(WRITE_FAILED);
    expect(writeFailureLine(failedWith('hasOwnProperty'))).toBe(WRITE_FAILED);
  });
});

describe('what silence does', () => {
  it('says the three outcomes apart, because they are three different outcomes', () => {
    // Nothing entered, one proposal standing, and two that cancel each other out.
    // Keyed on a number the **server** sent; the clock beside it is the server's too.
    const sentences = [silenceLine(0), silenceLine(1), silenceLine(2)];

    expect(new Set(sentences).size).toBe(3);
    expect(sentences[0]).toMatch(/the evening still counts/);
    expect(sentences[1]).toMatch(/it stands/);
    expect(sentences[2]).toMatch(/counts for nothing/);
  });

  it('treats a count above the contract’s cap as two, rather than inventing a fourth', () => {
    // The count is capped at two by the contract, so there is no third sentence for a
    // state the model cannot reach — and an unexpected number must not silence the
    // one line `ADR-0060` requires beside the hero clock.
    expect(silenceLine(3)).toBe(silenceLine(2));
  });
});
