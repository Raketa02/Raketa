/**
 * The deck's copy, held to the four things about it that are decisions rather than wording.
 *
 * **There is no *Show them again*** — the prototype's button makes `PASS_SUPPRESS`
 * unmeasurable and the suppression a suggestion — the pass sentence states the **deck-only**
 * boundary ADR-0128 asks for, the footer promise names the gesture and its target rather than
 * the record sheets K-7 removed, and nothing here invents a familiar form of anybody's name.
 */

import { poolDescription } from './searchPresentation';
import {
  DECK_FOOTER,
  MATCH_ME_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  matchMeSegment,
  matchMeSegmentLabel,
  mutualToast,
  outgoingYeses,
  passedToast,
} from './deckPresentation';

const EVERY_SENTENCE = [
  ...DECK_FOOTER,
  WIDEN_IN_YOU,
  outgoingYeses(0),
  outgoingYeses(3),
  passedToast('Marek Z.'),
  interestToast('Marek Z.'),
  mutualToast('Marek Z.'),
];

describe('the segment', () => {
  it('draws no count at nought, rather than a zero', () => {
    expect(matchMeSegment(0)).toBe(MATCH_ME_TITLE);
  });

  it('draws the count beside the name once there is one', () => {
    expect(matchMeSegment(3)).toBe('Match me · 3');
  });

  it('says what the number is when it is read aloud out of context', () => {
    expect(matchMeSegmentLabel(3)).toBe('Match me, 3 yeses of yours still out');
    expect(matchMeSegmentLabel(1)).toBe('Match me, 1 yes of yours still out');
  });
});

describe('the footer', () => {
  it('states that a pass is silent and that it does not reach a search', () => {
    const [pass] = DECK_FOOTER;

    expect(pass).toMatch(/nobody is told/);
    // ADR-0128's named cost, said out loud: the suppression is the deck's and nothing else's.
    expect(pass).toMatch(/still turn up in a search/);
  });

  it('names the gesture and what it opens, rather than a record sheet', () => {
    const [, promise] = DECK_FOOTER;

    expect(promise).toMatch(/Hold a card/);
    expect(promise).toMatch(/Fit/);
    expect(promise).not.toMatch(/record/i);
  });
});

describe('the empty states', () => {
  /**
   * The pool description is the body of both, and it is the client's sentence over ADR-0099's
   * codes — the count post-gate, the radius the search ran on, and the window.
   */
  it('states the pool the deal came out of', () => {
    expect(poolDescription({ playersInRange: 7, radiusKmUsed: 12, sportName: 'Padel' })).toBe(
      '7 players in range for Padel, within 12 km.',
    );
  });

  it('counts one player without an s', () => {
    expect(poolDescription({ playersInRange: 1, radiusKmUsed: 8, sportName: 'Tennis' })).toBe(
      '1 player in range for Tennis, within 8 km.',
    );
  });

  /**
   * The window is **not** a clause here any more. It was appended as *· Whenever suits*, and it
   * is the one fact in the sentence a player cannot act on from where they read it: the pool's
   * ladder states the window per rung, and a deal has no window to move.
   */
  it('states the count and the radius, and never the window', () => {
    const line = poolDescription({ playersInRange: 0, radiusKmUsed: 8, sportName: 'Tennis' });

    expect(line).toBe('0 players in range for Tennis, within 8 km.');
    expect(line).not.toMatch(/week|Whenever/i);
  });

  it('points the widening at You and never at a control on this screen', () => {
    expect(WIDEN_IN_YOU).toMatch(/You/);
    expect(WIDEN_IN_YOU).not.toMatch(/tap|press|button/i);
  });

  it('states the outgoing yeses as a mechanism rather than as a promise', () => {
    expect(outgoingYeses(2)).toBe(
      '2 people you said yes to will see it the next time they look for a game.',
    );
    expect(outgoingYeses(1)).toMatch(/^1 person /);
  });

  it('says nothing is out rather than printing a nought', () => {
    expect(outgoingYeses(0)).not.toMatch(/\b0\b/);
  });
});

describe('the three toasts', () => {
  it('names the whole handle and never a familiar form', () => {
    for (const sentence of [passedToast, interestToast, mutualToast]) {
      expect(sentence('Marek Z.')).toContain('Marek Z.');
    }
  });

  it('tells a mutual to both sides and stops there', () => {
    const said = mutualToast('Marek Z.');

    expect(said).toMatch(/both said yes/);
    // The challenge belongs to `matches`, which is out of scope — so nothing here promises a
    // chat, a booking or a notification the platform cannot send.
    expect(said).not.toMatch(/chat|notif|book/i);
  });

  it('never promises that a one-sided yes was delivered', () => {
    expect(interestToast('Marek Z.')).not.toMatch(/told|sent|notified/i);
  });
});

describe('what the deck never says', () => {
  it('offers no way to undo a pass anywhere in its copy', () => {
    for (const sentence of EVERY_SENTENCE) {
      expect(sentence).not.toMatch(/show them again|undo|start over/i);
    }
  });
});
