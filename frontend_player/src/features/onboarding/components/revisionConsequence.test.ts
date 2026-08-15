/**
 * The sentence a player reads before changing an answer.
 *
 * Pinned here rather than only through the screen because the plural and the zero case
 * are the two a screen test is least likely to reach: a run deep enough to lose several
 * answers, and a change to the most recent one.
 */

import { revisionConsequence } from './revisionConsequence';

describe('what a change costs, in words', () => {
  it('names how many later answers go', () => {
    expect(revisionConsequence(4)).toContain('4 later answers');
  });

  it('says one answer rather than one answers', () => {
    expect(revisionConsequence(1)).toContain('1 later answer.');
  });

  it('states the most recent answer as costing no others, and never as zero', () => {
    const sentence = revisionConsequence(0);

    expect(sentence).toContain('discards no others');
    expect(sentence).not.toContain('0');
    // And it still says the run may go somewhere else, because the next question is
    // chosen from the transcript this change produces.
    expect(sentence).toContain("what you're asked next may change");
  });
});
