/**
 * The deck's copy, held to the things about it that are decisions rather than wording.
 *
 * The chip is drawn from a count and never names anybody; the counter states the pool and waits
 * for the budget rather than inventing one; the stamps' words are the buttons' own; the ending
 * prints the life of a yes off the wire and never a number this app holds; the reset is offered
 * on one ending and named nowhere else; the two retired toasts survive only as spoken results;
 * and the one toast left is pinned verbatim, with the words banned that would turn it into a
 * report.
 */

import { DECK_ANSWER_WORDS } from './playerCardPresentation';
import { poolDescription } from './searchPresentation';
import {
  DEAL_AGAIN_LABEL,
  NOBODY_IN_RANGE_TITLE,
  PANE_LABEL,
  RADAR_LINE,
  SEEN_EVERYBODY_TITLE,
  SHOW_THEM_AGAIN_LABEL,
  STAMP_WORDS,
  TRY_THE_RADAR_LABEL,
  WIDEN_IN_YOU,
  deckCounter,
  interestAnnouncement,
  mutualToast,
  passedAnnouncement,
  seenEverybodyLine,
  wantToPlayYouChip,
  yesOutcome,
} from './deckPresentation';

describe('the toggle', () => {
  /**
   * Each half of the toggle is a **name**, so there is no function left that could put a
   * number back beside it. The count of cards is the counter pill's, which says what it counts.
   */
  it('names two panes and never a number', () => {
    expect(PANE_LABEL).toEqual({ deck: 'Deck', radar: 'Radar' });
    for (const label of Object.values(PANE_LABEL)) expect(label).not.toMatch(/\d/);
  });

  it('has no half called Match me — the word survives only in Matched!', () => {
    expect(Object.values(PANE_LABEL)).not.toContain('Match me');
  });
});

describe('the Radar pane', () => {
  it('says what it is and that it is not built, in a placeholder’s shape', () => {
    // The em dash is a dash and not a colon on purpose: *not built yet* is an aside about the
    // app, not a second clause of the sentence about the pane.
    expect(RADAR_LINE).toBe('Radar — not built yet');
    expect(RADAR_LINE).not.toMatch(/coming soon/i);
  });

  it('is where *Try the radar* goes', () => {
    expect(TRY_THE_RADAR_LABEL).toBe('Try the radar');
  });
});

describe('the chip', () => {
  it('counts people and agrees its verb with the count', () => {
    expect(wantToPlayYouChip(2)).toBe('2 want to play you');
    expect(wantToPlayYouChip(1)).toBe('1 wants to play you');
  });

  /** ADR-0109 §2's *not as a list* stands: a count, and no name anywhere in it. */
  it('names nobody', () => {
    expect(wantToPlayYouChip(3)).not.toMatch(/[A-Z][a-z]+ [A-Z]\./);
  });
});

describe('the counter', () => {
  it('states what is left and how many yeses there are to give', () => {
    expect(deckCounter({ left: 8, give: 12 })).toBe('8 left · 12 yeses to give');
    expect(deckCounter({ left: 1, give: 1 })).toBe('1 left · 1 yes to give');
  });

  it('prints a nought to give, because that is the ceiling and the toast acts on it', () => {
    expect(deckCounter({ left: 3, give: 0 })).toBe('3 left · 0 yeses to give');
  });

  /** A budget it has not read is not a nought: the pill says what it knows. */
  it('says what is left alone until the budget has landed', () => {
    expect(deckCounter({ left: 8 })).toBe('8 left');
  });
});

describe('the stamps', () => {
  it('say the two answers in the buttons’ own words', () => {
    expect(STAMP_WORDS).toEqual({ yes: DECK_ANSWER_WORDS.accept, no: DECK_ANSWER_WORDS.pass });
    expect(STAMP_WORDS.yes).toBe("Let's play");
    expect(STAMP_WORDS.no).toBe('Not today');
  });

  it('carry no glyph — the 🎾 is the button’s mark and never a word', () => {
    expect(STAMP_WORDS.yes).not.toMatch(/🎾/);
  });
});

describe('the endings', () => {
  it('title the two states differently, in the mock’s words', () => {
    expect(SEEN_EVERYBODY_TITLE).toBe('You have seen everybody');
    expect(NOBODY_IN_RANGE_TITLE).toBe('Nobody in range yet');
  });

  /**
   * The radius is the deal's own and the days are the interest row's `ttl_days` — **21 and
   * not the mock's 14**, because the number is read from the wire (ADR-0169 §5).
   */
  it('prints the radius and how long a yes lives, both off the wire', () => {
    expect(seenEverybodyLine({ radiusKm: 8, ttlDays: 21 })).toBe(
      'Nobody new in 8 km today. Your yeses stay live for 21 days, so the ones you gave are still working.',
    );
  });

  it('holds no number of its own — without the read it says only what the deal said', () => {
    expect(seenEverybodyLine({ radiusKm: 8 })).toBe('Nobody new in 8 km today.');
    expect(seenEverybodyLine({ radiusKm: 8 })).not.toMatch(/14|21/);
  });

  /**
   * The pool description is the body of *Nobody in range*, and it is the client's sentence over
   * ADR-0099's codes — the count post-gate, the radius the search ran on, and never the window.
   */
  it('states the pool the deal came out of, and never the window', () => {
    const line = poolDescription({ playersInRange: 0, radiusKmUsed: 8, sportName: 'Tennis' });

    expect(line).toBe('0 players in range for Tennis, within 8 km.');
    expect(line).not.toMatch(/week|Whenever/i);
  });

  it('points the widening at You and never at a control on this screen', () => {
    expect(WIDEN_IN_YOU).toMatch(/You/);
    expect(WIDEN_IN_YOU).not.toMatch(/tap|press|button/i);
  });

  it('offers the reset by the mock’s name, and the retry by its own', () => {
    expect(SHOW_THEM_AGAIN_LABEL).toBe('Show them again');
    expect(DEAL_AGAIN_LABEL).toBe('Deal again');
  });
});

describe('what an answer says to a listener', () => {
  it('names the whole handle and never a familiar form', () => {
    for (const sentence of [passedAnnouncement, interestAnnouncement, mutualToast]) {
      expect(sentence('Marek Z.')).toContain('Marek Z.');
    }
  });

  it('speaks a pass in the retired toast’s words', () => {
    expect(passedAnnouncement('Marek Z.')).toBe('Not today, Marek Z.');
  });

  it('never promises that a one-sided yes was delivered', () => {
    expect(interestAnnouncement('Marek Z.')).toBe(
      'Noted — Marek Z. sees it the next time they look for a game',
    );
    expect(interestAnnouncement('Marek Z.')).not.toMatch(/told|sent|notified/i);
  });

  it('tells a mutual to both sides and stops there', () => {
    const said = mutualToast('Marek Z.');

    expect(said).toMatch(/both said yes/);
    // Nothing here promises a chat, a booking or a notification the platform cannot send.
    expect(said).not.toMatch(/chat|notif|book/i);
  });
});

describe('a one-sided yes, a mutual without a game, and a mutual with one', () => {
  /**
   * ADR-0154, then ADR-0169 §3: the tap answers with the game these two have, when there is
   * one — and the three answers are three different things, a spoken result, a toast and a
   * screen.
   */

  it('speaks a one-sided yes and shows nothing, because the stamp was the feedback', () => {
    expect(yesOutcome('Marek Z.', { mutual: false, challengeId: null })).toEqual({
      kind: 'announce',
      message: interestAnnouncement('Marek Z.'),
    });
  });

  it('keeps the older sentence exactly, as a toast, where no game was named', () => {
    expect(yesOutcome('Marek Z.', { mutual: true, challengeId: null })).toEqual({
      kind: 'toast',
      message: 'You both said yes — Marek Z. sees it the next time they open Raketa',
      tone: 'ok',
    });
  });

  it('has no sentence for a mutual that named a challenge, because that yes is a screen', () => {
    expect(yesOutcome('Marek Z.', { mutual: true, challengeId: 'c' })).toEqual({ kind: 'screen' });
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
