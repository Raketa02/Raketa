/**
 * The two tables this screen's words come out of.
 *
 * **Completeness is a typecheck, not a test** (`ADR-0075`): a contract value added
 * without its words fails `pnpm typecheck` on the `Record`, and the
 * `IsClosedUnion` pins beside each table are what keep that true if either union
 * ever widens to a bare `string`. So what a *test* can add is the other half —
 * writing the enumeration out, so that **growth is a decision somebody makes in a
 * diff** rather than a row that appears with a green suite. The three guards catch
 * three different edits; this is the third.
 */

import { OUTCOME_COPY, STANDING_COPY, outcomeCopy, standingCopy } from './outcomes';

describe('the four outcomes', () => {
  it('are these four and no others', () => {
    // A fifth outcome is a decision about money, and it arrives here as a failing
    // assertion rather than as a row somebody added while doing something else.
    expect(Object.keys(OUTCOME_COPY).sort()).toEqual([
      'forfeited',
      'refundedHalf',
      'refundedInFull',
      'reversed',
    ]);
  });

  it('name three renderings each, and none of them is empty', () => {
    // The same label is a row, a button and an acknowledgement. A blank in any of
    // the three is a control or a note with nothing in it.
    for (const copy of Object.values(OUTCOME_COPY)) {
      expect(copy.name.length).toBeGreaterThan(0);
      expect(copy.leaving.length).toBeGreaterThan(0);
      expect(copy.left.length).toBeGreaterThan(0);
    }
  });

  it('carry no amount in any rendering', () => {
    // `ADR-0033`: the quote is a label and never an amount. The phone holds what
    // she paid and not half of it, and halving is arithmetic it does not do — so
    // a figure here could only be a made-up one.
    for (const copy of Object.values(OUTCOME_COPY)) {
      for (const sentence of [copy.name, copy.leaving, copy.left]) {
        expect(sentence).not.toMatch(/\d/);
        expect(sentence).not.toContain('zł');
      }
    }
  });

  it('put the button in the imperative and the acknowledgement in the past', () => {
    // The one button carries the quote, so it says what pressing it does; the note
    // appears once it is done. Two renderings of one label that read the same way
    // would be one of them drawn in the wrong place.
    for (const copy of Object.values(OUTCOME_COPY)) {
      expect(copy.leaving.startsWith('Leave')).toBe(true);
      expect(copy.left.startsWith('You have left')).toBe(true);
    }
  });

  it('resolve a label this build has never heard of to nothing', () => {
    // The typecheck protects the repository; this protects an installed phone,
    // which cannot be forced to update. Losing the row loses exactly the row.
    expect(outcomeCopy('transferred')).toBeUndefined();
    expect(outcomeCopy('')).toBeUndefined();
  });

  it('does not resolve a label off Object.prototype', () => {
    // `Record` lookup by a bare string reaches the prototype chain. Without the
    // guard this returns a function and the row draws `[object Object]`.
    expect(outcomeCopy('toString')).toBeUndefined();
    expect(outcomeCopy('constructor')).toBeUndefined();
  });
});

describe('the four standings', () => {
  it('are these four and no others', () => {
    expect(Object.keys(STANDING_COPY).sort()).toEqual([
      'opens',
      'searching',
      'spent',
      'stillPossible',
    ]);
  });

  it('names a moment on exactly one of them', () => {
    // The whole distinction between *opens* and *still possible* is that one has a
    // moment to give and the other does not, because what stands between her and
    // it is an event rather than a clock. A second row that read the countdown
    // would erase that.
    const countdown = '2 h 14 min';

    expect(STANDING_COPY.opens.note(countdown)).toContain(countdown);
    expect(STANDING_COPY.searching.note(countdown)).not.toContain(countdown);
    expect(STANDING_COPY.stillPossible.note(countdown)).not.toContain(countdown);
    expect(STANDING_COPY.spent.note(countdown)).not.toContain(countdown);
  });

  it('says *once it fills* where there is no moment, and never a date', () => {
    // `stillPossible` is reached by an open match that has not committed: the three
    // money outcomes are a **fill** away rather than a moment away, and naming a
    // moment there would be the screen promising a turn that may never come.
    expect(STANDING_COPY.stillPossible.note(undefined)).toBe('Once the match fills');
  });

  it('falls back to the vaguest true thing when a moment does not parse', () => {
    // A moment that cannot be read is a contract failure rather than a state, and
    // the answer is not a figure in decades.
    expect(STANDING_COPY.opens.note(undefined)).toBe('Later on');
  });

  it('gives every standing a mark, and hands the state to the words', () => {
    // The marks are decoration and are hidden from assistive technology, so the
    // note is the whole of what a screen-reader user gets. Two standings sharing a
    // mark is fine; two sharing a note is a row that cannot be told apart.
    const notes = Object.values(STANDING_COPY).map((copy) => copy.note('2 h'));

    expect(new Set(notes).size).toBe(notes.length);
    for (const copy of Object.values(STANDING_COPY)) {
      expect(copy.mark.length).toBeGreaterThan(0);
    }
  });

  it('marks the three roles apart, and shares one mark on purpose', () => {
    // *Two sharing a mark is fine* is true of exactly one pair and not of the
    // table generally, and stated loosely it permits the collapse that empties the
    // heading: `What you have passed, and what is ahead` is three roles — behind
    // her, live now, ahead of her — and a `spent` row wearing `searching`'s mark
    // says she has not passed anything. Only the two *ahead* standings share,
    // because there the words are the cue: `In 2 h 14 min` and `Once the match
    // fills` are not close to each other.
    const { spent, searching, opens, stillPossible } = STANDING_COPY;

    expect(new Set([spent.mark, searching.mark, opens.mark]).size).toBe(3);
    // Pinned rather than merely allowed, so un-sharing them is also a decision
    // somebody makes in a diff — a third circle would be a distinction drawn
    // where the sentences already draw it.
    expect(stillPossible.mark).toBe(opens.mark);
  });

  it('resolves a standing this build has never heard of to nothing', () => {
    expect(standingCopy('reopened')).toBeUndefined();
    expect(standingCopy('toString')).toBeUndefined();
  });
});
