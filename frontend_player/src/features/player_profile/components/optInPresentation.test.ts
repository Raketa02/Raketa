/**
 * The consent copy, guarded as **evidence** rather than as words on a screen.
 *
 * What a player agreed to is the sentence they were shown, and the version identifier
 * stamped into the draft is the only thing that can name it afterwards. So this file pins
 * **the whole of what the screen says**, verbatim, beside the version that names it. A
 * reword is a new version with the old one retained, never an edit — and the way to make
 * that a decision rather than a drift is to make one impossible without the other.
 *
 * **Failing this test is the point.** An agent who improves a sentence gets a red suite
 * pointing at the version identifier, which is exactly the conversation that should happen.
 *
 * The step's title and the line under it come from `socialStepPresentation`, because the
 * chrome of all six steps is one table. They are pinned here anyway: a player reads them on
 * the same screen as the card, so they are part of what the answer was given against
 * whichever file happens to hold them.
 */

import { stepCopy } from './socialStepPresentation';
import {
  OPT_IN_ANSWERS,
  OPT_IN_EYEBROW,
  OPT_IN_FINISH_BLOCKED_HINT,
  OPT_IN_FINISH_LABEL,
  OPT_IN_NEVER_PRE_TICKED,
  OPT_IN_PROMISES,
  OPT_IN_PROMISE_HEADING,
  OPT_IN_SCOPE,
  PROPOSALS_OPT_IN_COPY_VERSION,
} from './optInPresentation';

/** Everything a player reads on this screen, in the order they read it. */
const theWholeScreen = [
  stepCopy('opt-in').title,
  OPT_IN_EYEBROW,
  stepCopy('opt-in').asks,
  OPT_IN_PROMISE_HEADING,
  ...OPT_IN_PROMISES.map((promise) => `${promise.term} — ${promise.detail}`),
  OPT_IN_SCOPE,
  OPT_IN_NEVER_PRE_TICKED,
  // In the order they are offered, so reversing them fails the pin as loudly as a reword.
  ...OPT_IN_ANSWERS.map((answer) => answer.label),
  OPT_IN_FINISH_LABEL,
  OPT_IN_FINISH_BLOCKED_HINT,
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
   * **The pin, and the whole reason this file exists.** Every sentence a player is shown,
   * against the identifier that names them. Changing a word here without changing the
   * identifier beside it would leave every already-recorded answer pointing at a wording
   * nobody was ever shown, which is a consent record that evidences nothing.
   */
  it('names exactly these words, so a reword cannot pass as an edit', () => {
    expect(PROPOSALS_OPT_IN_COPY_VERSION).toBe('proposals-opt-in.v1');
    expect(theWholeScreen).toBe(
      [
        'May we suggest games?',
        'The one thing we ask before finishing',
        'Whether the platform may put games in front of you.',
        'If you say yes',
        'You may receive — a game we think fits, when your week and theirs overlap',
        'You always answer — every game by hand — nothing is ever confirmed for you',
        'You can stop — any time, from your profile',
        'Saying no changes only this. You stay findable in search either way.',
        'Never pre-ticked. Skipping is not consent.',
        "No — don't suggest games",
        'Yes — suggest games',
        'Finish — show me players',
        'Choose yes or no above to finish',
      ].join('\n'),
    );
  });
});

describe('the two answers', () => {
  /**
   * **No is offered first**, because the option a screen puts first is the one it reads as
   * recommending — and this is the question where the product must not be seen to lean.
   * That makes the order a copy decision, guarded like the words themselves.
   */
  it('offers no before yes, and each names what it does', () => {
    expect(OPT_IN_ANSWERS).toEqual([
      { accepted: false, label: "No — don't suggest games" },
      { accepted: true, label: 'Yes — suggest games' },
    ]);
  });
});

describe('what the card promises', () => {
  /** Three, in this order: what arrives, what the player still does, and how it stops. */
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
   *
   * Kept as its own assertion beside the pin above, because the two fail differently: the
   * pin says *this wording changed*, and this says *the card has started promising
   * something this answer does not govern* — which is the failure worth naming out loud.
   */
  it('never promises appearing to anyone, because this answer does not govern that', () => {
    expect(theWholeScreen).not.toMatch(/you appear/i);
    expect(theWholeScreen).not.toMatch(/deck/i);
    expect(theWholeScreen).not.toMatch(/matchmaking/i);
  });
});
