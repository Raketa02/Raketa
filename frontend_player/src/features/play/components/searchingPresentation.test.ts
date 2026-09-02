/**
 * What a search says while it runs, and the sheet's header.
 *
 * The whole point is what is **absent**: the term inventory. §B14's seven-term list is stale
 * three ways, and #233 §5 ruled that any replacement summary is a weight claim in prose with
 * no gate behind it. So these assert that the count survives and the list does not.
 */

import { engineFillStatus, poolRankingStatus, whyFitHeader } from './searchingPresentation';

describe('the searching states', () => {
  /**
   * The count is a fact about an answer, and there is no answer yet — so there is no number
   * to invent and nowhere to invent one from (#269).
   */
  it('prints no count before the response exists', () => {
    expect(poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' })).toEqual({
      headline: 'Ranking everybody you could play…',
    });
    expect(engineFillStatus({ playersInRange: undefined, seats: 4 })).toEqual({
      headline: 'Looking for the evenest four…',
    });
  });

  it('keeps the count, and names the sport where the screen does not', () => {
    expect(poolRankingStatus({ playersInRange: 41, sportName: 'Padel' })).toEqual({
      headline: 'Ranking everybody you could play…',
      count: '41 in range for Padel',
    });

    expect(engineFillStatus({ playersInRange: 41, seats: 4 })).toEqual({
      headline: 'Looking for the evenest four…',
      count: '41 in range',
    });
  });

  /**
   * *The four* is a word about a Sport, and the fill's headline is the one place that rule
   * was not being applied: a squash player watched the engine look for the evenest four on a
   * court with two seats on it.
   */
  it('looks for a four or for a match, depending on the court', () => {
    expect(engineFillStatus({ playersInRange: 41, seats: 4 }).headline).toBe(
      'Looking for the evenest four…',
    );
    expect(engineFillStatus({ playersInRange: 41, seats: 2 }).headline).toBe(
      'Looking for the evenest match…',
    );
  });

  it('drops the inventory of terms', () => {
    // *fresh faces* is a modifier, `INTENT_ALIGNMENT` was missing, and "band width" is not a
    // term at all — a list that wrong is not repaired by rewriting it.
    const lines = [
      ...Object.values(poolRankingStatus({ playersInRange: 41, sportName: 'Padel' })),
      ...Object.values(engineFillStatus({ playersInRange: 41, seats: 4 })),
    ];

    for (const line of lines) {
      expect(line).not.toMatch(/level fit|reliability|fresh faces|band width|vibe/i);
    }
  });
});

describe('the why-fit header', () => {
  it('counts the live rows and names what they were tuned for', () => {
    expect(whyFitHeader({ liveTerms: 6, mode: 'COMPETITIVE' })).toBe(
      '6 weighted terms, tuned for a competitive game. Weights persuade; you decide.',
    );
    expect(whyFitHeader({ liveTerms: 5, mode: 'FOR_FUN' })).toBe(
      '5 weighted terms, tuned for a fun game. Weights persuade; you decide.',
    );
  });

  it('names no mode where the search has none', () => {
    // The deck's envelope carries no mode, and deriving one client-side would be the engine's
    // own resolution rule rewritten in TypeScript (#233 §6).
    const header = whyFitHeader({ liveTerms: 5, mode: null });

    expect(header).toBe('5 weighted terms. Weights persuade; you decide.');
    expect(header).not.toMatch(/tuned/);
  });

  it('hardcodes no plural', () => {
    expect(whyFitHeader({ liveTerms: 1, mode: null })).toMatch(/^1 weighted term\./);
  });

  it('keeps the sentence that says what the sheet is worth', () => {
    // §F1 rule 7, booked here by name.
    expect(whyFitHeader({ liveTerms: 8, mode: 'COMPETITIVE' })).toMatch(
      /Weights persuade; you decide\.$/,
    );
  });
});
