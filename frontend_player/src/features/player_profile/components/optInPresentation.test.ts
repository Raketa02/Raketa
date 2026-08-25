/**
 * The consent copy, guarded as **evidence** rather than as words on a screen.
 *
 * What a player agreed to is the sentence they were shown, and the version identifier
 * stamped into the draft is the only thing that can name it afterwards. So the two
 * assertions that matter here are that the identifier does not drift by accident, and that
 * the card never promises more than the switch delivers.
 */

import {
  OPT_IN_FINISH_LABEL,
  OPT_IN_NEVER_PRE_TICKED,
  OPT_IN_PROMISES,
  OPT_IN_PROMISE_HEADING,
  OPT_IN_SCOPE,
  PROPOSALS_OPT_IN_COPY_VERSION,
  optInAnswerLabel,
} from './optInPresentation';

/** Everything the card puts in front of a player, as one body of text. */
const theCard = [
  OPT_IN_PROMISE_HEADING,
  ...OPT_IN_PROMISES.flatMap((promise) => [promise.term, promise.detail]),
  OPT_IN_SCOPE,
  OPT_IN_NEVER_PRE_TICKED,
  optInAnswerLabel(false),
  optInAnswerLabel(true),
  OPT_IN_FINISH_LABEL,
].join('\n');

describe('the copy version', () => {
  /**
   * Not a formatting rule — the contract's own bounds. `copy_version` is `minLength 1,
   * maxLength 64`, and a version the commit refuses is a consent record that never lands.
   */
  it('is a value the commit will accept', () => {
    expect(PROPOSALS_OPT_IN_COPY_VERSION.length).toBeGreaterThan(0);
    expect(PROPOSALS_OPT_IN_COPY_VERSION.length).toBeLessThanOrEqual(64);
  });

  /**
   * **Pinned on purpose, and failing this test is the point.** Re-wording the card is a new
   * version with the old one retained, never an edit — a standing yes that cannot name its
   * words evidences nothing. An agent that changes a sentence and then changes this string
   * to match has at least been made to decide.
   */
  it('is pinned, so re-wording the card cannot pass as an edit', () => {
    expect(PROPOSALS_OPT_IN_COPY_VERSION).toBe('proposals-opt-in.v1');
  });
});

describe('what the card promises', () => {
  it('makes exactly the three approved promises', () => {
    expect(OPT_IN_PROMISES.map((promise) => promise.term)).toEqual([
      'You may receive',
      'You always answer',
      'You can stop',
    ]);
  });

  /**
   * The row the source documents opened with, and the one this product's rule does not
   * govern: **opting out stops the engine pushing, not the player existing.** Search and
   * matchmaking are unaffected either way, so a card that promised a player they *appear*
   * to compatible players would make the consent record evidence of something the switch
   * does not do.
   */
  it('never promises appearing to anyone, because this answer does not govern that', () => {
    expect(theCard).not.toMatch(/you appear/i);
    expect(theCard).not.toMatch(/deck/i);
    expect(theCard).not.toMatch(/matchmaking/i);
  });

  /** The load-bearing correction: what saying no leaves untouched, said on the card. */
  it('says what saying no does not change', () => {
    expect(OPT_IN_SCOPE).toContain('findable in search');
  });

  /** Neither control may read as the one already taken. */
  it('offers two answers that each say what they do', () => {
    expect(optInAnswerLabel(true)).toBe('Yes — suggest games');
    expect(optInAnswerLabel(false)).toBe("No — don't suggest games");
  });
});
