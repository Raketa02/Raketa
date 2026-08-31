/**
 * Which reasons a card says — the rule, without any words in it.
 *
 * Four things here are rules somebody could be **wrong** about, which is why they are in
 * `domain/` rather than beside the copy
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §7): the filter is per surface, it runs **before** the cap and not after, a concerned term
 * is not also a reason, and an empty result falls back to the liveness code rather than to
 * the fourth-ranked term.
 */

import {
  COMPETITIVE_CARD_DRAWS,
  DECK_CARD_DRAWS,
  REASON_CAP,
  SOCIAL_CARD_DRAWS,
  WHYFIT_DRAWS,
  selectReasons,
} from './reasonSelection';
import type { ScoredTerm } from './evidence';
import type { Term } from './vocabulary';

/** A ranked row. The arithmetic is not what is under test; the term is. */
function scored(term: Term): ScoredTerm {
  return {
    term,
    weight: 10,
    value: 0.8,
    contribution: 8,
    evidence: { kind: 'distance', km: 4, areaCode: 'A+050612+0019938', outsideTheirRadius: false },
  };
}

/** The ordinary case: every renderer has something to say about its evidence. */
const SAYS_SOMETHING = () => true;

/** Ranked by contribution, as the wire delivers them. Nothing on this side sorts. */
const RANKED: readonly ScoredTerm[] = [
  scored('LEVEL_FIT'),
  scored('PREDICTED_BALANCE'),
  scored('AVAILABILITY_OVERLAP'),
  scored('DISTANCE'),
  scored('INTENT_ALIGNMENT'),
  scored('PLAYING_STYLE'),
  scored('SOCIAL_VIBE'),
];

function reasons(selection: ReturnType<typeof selectReasons>): readonly Term[] {
  return selection.kind === 'terms' ? selection.terms.map((row) => row.term) : [];
}

describe('the order of the two operations', () => {
  it('filters first and takes three after, never the other way round', () => {
    // §B10 took the top three and then filtered, which is what made a card's "three reasons"
    // sometimes one — and is the direct cause of its `[GAP: no fallback string]`.
    const selection = selectReasons({
      drawn: DECK_CARD_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['INTENT_ALIGNMENT', 'PLAYING_STYLE', 'SOCIAL_VIBE']);
  });

  it('never says more than three', () => {
    const selection = selectReasons({
      drawn: WHYFIT_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toHaveLength(REASON_CAP);
  });
});

describe('the filter is the surface’s own', () => {
  it('drops what the competitive card already renders, and nothing else', () => {
    // The head-to-head row prints both levels and the bar draws the forecast. Reliability
    // joins them the day the Player Score block prints, and not before.
    const selection = selectReasons({
      drawn: COMPETITIVE_CARD_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['AVAILABILITY_OVERLAP', 'DISTANCE', 'INTENT_ALIGNMENT']);
  });

  it('drops the overlap row and the meta line’s distance on the social card', () => {
    const selection = selectReasons({
      drawn: SOCIAL_CARD_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['PREDICTED_BALANCE', 'INTENT_ALIGNMENT', 'PLAYING_STYLE']);
  });

  it('drops nothing on the sheet, whose job is showing values', () => {
    const selection = selectReasons({
      drawn: WHYFIT_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['LEVEL_FIT', 'PREDICTED_BALANCE', 'AVAILABILITY_OVERLAP']);
  });

  it('leaves the kind of evening standing on every surface', () => {
    // After the drops it *is* the first reason on the competitive card, and a dedicated row
    // would delete the sentence it duplicates (#230 §1).
    for (const drawn of [COMPETITIVE_CARD_DRAWS, SOCIAL_CARD_DRAWS, DECK_CARD_DRAWS]) {
      expect(drawn).not.toContain('INTENT_ALIGNMENT');
    }
  });
});

describe('a term the engine is concerned about', () => {
  it('is not also a reason, and the slot goes to the next survivor', () => {
    // One term saying "✓ X" and "! X" on one card is §10's rule broken at its own root.
    const selection = selectReasons({
      drawn: DECK_CARD_DRAWS,
      terms: RANKED,
      concerns: ['PLAYING_STYLE'],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['INTENT_ALIGNMENT', 'SOCIAL_VIBE']);
  });
});

describe('a term whose evidence is not a reason', () => {
  it('is not one of the three, because the card cannot draw the line', () => {
    // Three of the eight renderers legitimately decline — an intent mismatch, and a tag term
    // whose only firing pairs clash. Counting one prints two reasons where three were
    // promised.
    const selection = selectReasons({
      drawn: WHYFIT_DRAWS,
      terms: RANKED,
      concerns: [],
      livenessReasons: [],
      saysSomething: (row) => row.term !== 'PREDICTED_BALANCE',
    });

    expect(reasons(selection)).toEqual(['LEVEL_FIT', 'AVAILABILITY_OVERLAP', 'DISTANCE']);
  });

  it('falls back rather than drawing the blank row §G5 records', () => {
    // The engine ranked neither term into `concerns[]`, both renderers decline, and the row
    // would otherwise be empty next to the fit pill.
    const selection = selectReasons({
      drawn: DECK_CARD_DRAWS,
      terms: [scored('INTENT_ALIGNMENT'), scored('SOCIAL_VIBE')],
      concerns: [],
      livenessReasons: ['RECENT_ACTIVITY'],
      saysSomething: () => false,
    });

    expect(selection).toEqual({ kind: 'liveness', reason: 'RECENT_ACTIVITY' });
  });
});

describe('when nothing survives', () => {
  it('falls back to the top liveness reason, never to a filtered term', () => {
    // The row's question is *why this person*, and the liveness code answers exactly that.
    // Falling back to the fourth-ranked term would break §10 on purpose to fill a slot.
    const selection = selectReasons({
      drawn: DECK_CARD_DRAWS,
      terms: [scored('LEVEL_FIT'), scored('DISTANCE')],
      concerns: [],
      livenessReasons: ['NEWCOMER_LIFT', 'RECENT_ACTIVITY'],
      saysSomething: SAYS_SOMETHING,
    });

    expect(selection).toEqual({ kind: 'liveness', reason: 'NEWCOMER_LIFT' });
  });

  it('hides the row with no liveness reason either, rather than drawing a blank one', () => {
    // §G5's "renders a blank line next to the fit pill" is the bug being fixed; an absent row
    // is not an empty one.
    const selection = selectReasons({
      drawn: DECK_CARD_DRAWS,
      terms: [scored('DISTANCE')],
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(selection).toEqual({ kind: 'hidden' });
  });

  it('cannot happen on the competitive card, where distance never stands down', () => {
    // The card draws no distance row, so a survivor always exists.
    const selection = selectReasons({
      drawn: COMPETITIVE_CARD_DRAWS,
      terms: [scored('LEVEL_FIT'), scored('DISTANCE')],
      concerns: [],
      livenessReasons: [],
      saysSomething: SAYS_SOMETHING,
    });

    expect(reasons(selection)).toEqual(['DISTANCE']);
  });
});
