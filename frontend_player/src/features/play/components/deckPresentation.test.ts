/**
 * The deck's copy, held to the four things about it that are decisions rather than wording.
 *
 * **There is no *Show them again*** — the prototype's button makes `PASS_SUPPRESS`
 * unmeasurable and the suppression a suggestion — the pass sentence states the **deck-only**
 * boundary ADR-0128 asks for, the footer promise names the gesture and its target rather than
 * the record sheets K-7 removed, and nothing here invents a familiar form of anybody's name.
 *
 * **And a mutual naming a chat has no sentence here any more** (ADR-0166 §1): it is the yes
 * screen, pushed by the mutation, and the two sentences a yes still raises are pinned verbatim.
 */

import { poolDescription } from './searchPresentation';
import {
  DECK_FOOTER,
  MATCH_ME_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  mutualToast,
  outgoingYeses,
  passedToast,
  yesToast,
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
  /**
   * The count is struck, and this is the shape of the refusal: the deck's half of the segment
   * is a **name**, so there is no function left that could put a number back beside it. The
   * figure it used to draw is the ending sentence's, which is asserted below.
   */
  it('is a name and never a number, because the deck publishes no count of cards', () => {
    expect(MATCH_ME_TITLE).toBe('Match me');
    expect(MATCH_ME_TITLE).not.toMatch(/\d/);
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
    expect(interestToast('Marek Z.')).toBe(
      'Noted — Marek Z. sees it the next time they look for a game',
    );
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

describe('a mutual with a game, and a mutual without one', () => {
  /**
   * ADR-0154. The tap answers with the game these two have, when there is one — so the mutual
   * that opened a game and the mutual that did not stopped being the same sentence; and since
   * ADR-0166 the first is not a sentence at all.
   */

  it('has no toast for a mutual that named a challenge, because that yes is a screen', () => {
    expect(yesToast('Marek Z.', { mutual: true, challengeId: 'c' })).toBeUndefined();
  });

  it('picks the two sentences that remain by the answer, and never by the press', () => {
    expect(yesToast('Marek Z.', { mutual: false, challengeId: null })).toEqual({
      message: interestToast('Marek Z.'),
      tone: 'base',
    });
    expect(yesToast('Marek Z.', { mutual: true, challengeId: null })).toEqual({
      message: mutualToast('Marek Z.'),
      tone: 'ok',
    });
  });

  it('keeps the older sentence exactly where no game was named', () => {
    expect(mutualToast('Marek Z.')).toBe(
      'You both said yes — Marek Z. sees it the next time they open Raketa',
    );
  });

  it('never draws the absence as a state of its own', () => {
    /**
     * §3 and §5: a missing `challenge_id` is **one answer covering two causes** — the pair
     * already have a game being arranged, or a gate refused — and which it is does not cross
     * the wire. A sentence that said *no game was opened* would turn the second into
     * something the sender could read about the other person, which ADR-0095 guarantees
     * leaves no trace anywhere in any response.
     */
    expect(mutualToast('Marek Z.')).not.toMatch(/no game|not opened|couldn|unable|failed|yet/i);
  });
});
