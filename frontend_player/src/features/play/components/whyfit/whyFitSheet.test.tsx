/**
 * `SH.whyfit` — the sheet whose whole job is that a number is checkable.
 *
 * What is asserted here is what a build session could quietly undo, and most of it is a
 * **shape** rather than a string: the row count is derived rather than seven, a stood-down
 * term is a line and never a greyed row, the platform's own gap is stated once and in the
 * footer, a concern replaces its row's reason rather than being gathered into a block, and the
 * printed column adds up to the printed sub-total on screen.
 *
 * `domain/whyFitColumn` holds the arithmetic and is tested over generated inputs; this suite
 * is about the arithmetic **reaching the screen**, which is the half a pure test cannot see.
 */

import { render, screen } from '@testing-library/react-native';

import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Evidence, ScoredTerm } from '../../domain/evidence';
import type { Term } from '../../domain/vocabulary';
import { NOT_ON_THIS_PLATFORM_FOOTER, degradedLine } from '../degradedPresentation';
import { WHAT_ELSE_MOVED_YOU_HERE, livenessLine } from '../livenessPresentation';
import { MODIFIERS_HEADING, TERM_SUBTOTAL_LABEL, modifierLine } from '../modifierPresentation';
import { whyFitHeader } from '../searchingPresentation';
import { termLabel } from '../termPresentation';
import { NOT_COUNTED_HEADING, WEIGHT_BASIS } from '../whyFitPresentation';

import { WhyFitSheet } from './WhyFitSheet';

/** The deck's envelope: **null mode**, which is the case the sheet must name no mode on. */
const DECK_ENVELOPE: SearchEnvelope = {
  searchId: '11111111-0000-4000-8000-000000000001',
  mode: null,
  pool: { radiusKmUsed: 12, playersInRange: 7, window: 'THIS_WEEK' },
  radiusClamp: false,
  sortsAvailable: [],
  rungOffers: null,
  rulesetVersion: 'ruleset-v1',
  engineVersion: 'matchfit-v1',
  optimisedFor: 'SEARCHER',
};

function scored(term: Term, contribution: number, evidence: Evidence, weight = 30): ScoredTerm {
  return { term, weight, value: 0.8, contribution, evidence };
}

const LEVEL = scored('LEVEL_FIT', 24.4, {
  kind: 'level_fit',
  myMu: 2.71,
  theirMu: 2.83,
  delta: 0.12,
  direction: 'ABOVE',
});

const DISTANCE = scored('DISTANCE', 17.4, {
  kind: 'distance',
  km: 4,
  areaCode: 'A+050612+0019938',
  outsideTheirRadius: false,
});

const OVERLAP = scored('AVAILABILITY_OVERLAP', 17.4, {
  kind: 'availability_overlap',
  sharedCount: 3,
  nextSlot: { day: 2, part: 'evening' },
});

function candidate(over: Partial<Candidate> = {}): Candidate {
  return {
    playerId: 'aaaaaaaa-0000-4000-8000-000000000001',
    fit: 65,
    distanceKm: 4,
    card: {
      nickname: 'Marek Z.',
      areaCode: 'A+050612+0019938',
      socialTags: [],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    terms: [LEVEL, DISTANCE, OVERLAP],
    concerns: [],
    livenessReasons: [],
    degradedTerms: [],
    modifiers: [],
    ...over,
  };
}

function draw(over: Partial<Candidate> = {}, envelope = DECK_ENVELOPE) {
  render(
    <WhyFitSheet
      visible
      onClose={() => undefined}
      candidate={candidate(over)}
      envelope={envelope}
      name="Marek Z."
    />,
  );
}

describe('the header', () => {
  it('counts the terms that fired rather than claiming a fixed seven', () => {
    draw();

    expect(screen.getByText(whyFitHeader({ liveTerms: 3, mode: null }))).toBeTruthy();
  });

  /**
   * The deck has no mode, and deriving one from the declared intent would be the engine's own
   * resolution rule rewritten in TypeScript — refused by name (#233 §6).
   */
  it('names no mode where the envelope carries none', () => {
    draw();

    expect(screen.queryByText(/tuned for/)).toBeNull();
  });

  it('names the mode where the search had one', () => {
    draw({}, { ...DECK_ENVELOPE, mode: 'COMPETITIVE' });

    expect(screen.getByText(/tuned for a competitive game/)).toBeTruthy();
  });

  /** The ✦ is drawn and never spoken — the one place the two names differ (§20.6). */
  it('draws the glyph and announces the sheet without it', () => {
    draw();

    expect(screen.getByText('Why ✦ 65')).toBeTruthy();
    expect(screen.getByLabelText('Why fit 65')).toBeTruthy();
  });
});

describe('the term rows', () => {
  it('draws one row per term that fired, in the order they arrived', () => {
    draw();

    for (const term of ['LEVEL_FIT', 'DISTANCE', 'AVAILABILITY_OVERLAP'] as const) {
      expect(screen.getByText(termLabel(term))).toBeTruthy();
    }
  });

  /**
   * *"A breakdown that does not add up is the claim failing."* 24,4 + 17,4 + 17,4 is 59,2 —
   * three rows that each round down under a sub-total of 59, so the spare point is
   * apportioned rather than lost.
   */
  it('prints a column that sums to the printed sub-total', () => {
    draw();

    expect(screen.getByText('×30 → 25')).toBeTruthy();
    expect(screen.getByText(TERM_SUBTOTAL_LABEL)).toBeTruthy();
    expect(screen.getByText('59')).toBeTruthy();

    const printed = ['×30 → 25', '×30 → 17', '×30 → 17'];
    for (const figure of printed) expect(screen.getAllByText(figure).length).toBeGreaterThan(0);
  });

  it('states what a weight is a share of, once and beneath the rows', () => {
    draw();

    expect(screen.getAllByText(WEIGHT_BASIS)).toHaveLength(1);
  });

  /**
   * A concern is the engine's own graded claim, and it is marked **in place**: every concern's
   * term is guaranteed to be a row already drawn, so a summary block would restate a value the
   * sheet has just rendered — §10's rule broken on the one screen whose job is showing values.
   */
  it('marks a concern on its own row rather than gathering the concerns', () => {
    draw({ concerns: ['DISTANCE'] });

    expect(screen.getByText('A long way out')).toBeTruthy();
    // No second heading, no block: the row is where the warning is.
    expect(screen.queryByText(/concern/i)).toBeNull();
  });
});

describe('a term that stood down', () => {
  it('is a line saying whose gap it is, and never a term row', () => {
    draw({ degradedTerms: [{ term: 'SOCIAL_VIBE', reason: 'NOTHING_FROM_THEM' }] });

    expect(screen.getByText(NOT_COUNTED_HEADING)).toBeTruthy();
    expect(screen.getByText(degradedLine('SOCIAL_VIBE', 'NOTHING_FROM_THEM') ?? '')).toBeTruthy();
    // Four of a row's five cells would be empty, so there is no row at all.
    expect(screen.queryByText(termLabel('SOCIAL_VIBE'))).toBeNull();
  });

  /**
   * Two tiers: the per-person gaps are this pairing's, and the platform's own is a fact about
   * everybody — stated **once, in the footer**, or reliability's line prints identically on
   * twenty cards and reads as twenty separate shortfalls.
   */
  it('puts the platform’s own gap in the footer and nowhere else', () => {
    draw({
      degradedTerms: [
        { term: 'RELIABILITY', reason: 'NOT_YET_ON_THIS_PLATFORM' },
        { term: 'SOCIAL_VIBE', reason: 'NOTHING_FROM_THEM' },
      ],
    });

    expect(screen.getAllByText(NOT_ON_THIS_PLATFORM_FOOTER)).toHaveLength(1);
    // The not-counted block holds the per-person gap and only that one.
    expect(screen.getByText(degradedLine('SOCIAL_VIBE', 'NOTHING_FROM_THEM') ?? '')).toBeTruthy();
  });

  it('says the build is out of date rather than dropping a reason it cannot read', () => {
    draw({ degradedTerms: [{ term: 'SOCIAL_VIBE', reason: null }] });

    expect(screen.getByText(OUT_OF_DATE_GAP)).toBeTruthy();
  });

  it('draws no block at all when nothing stood down', () => {
    draw();

    expect(screen.queryByText(NOT_COUNTED_HEADING)).toBeNull();
    expect(screen.queryByText(NOT_ON_THIS_PLATFORM_FOOTER)).toBeNull();
  });
});

describe('the adjustments', () => {
  /**
   * `applied` is `fit − Σcontributions` and the rows are **never summed**: they carry
   * pre-budget entry points and `MODIFIER_BUDGET` clamps the stack, so re-adding them would
   * be a wrong number that looks like a plausible one (`record_rows.py`).
   */
  it('is headed by the derived figure, not by the rows added up', () => {
    draw({
      fit: 65,
      modifiers: [
        { code: 'CALIBRATION_VALUE', points: 4 },
        { code: 'WELCOMING_RECORD', points: 5 },
      ],
    });

    // 65 − 59 = 6, where the two rows sum to 9.
    expect(screen.getByText('+6 from adjustments')).toBeTruthy();
    expect(screen.queryByText('+9 from adjustments')).toBeNull();
    expect(screen.getByText(modifierLine('CALIBRATION_VALUE'))).toBeTruthy();
  });

  it('carries the sign, because an adjustment may take points away', () => {
    draw({ fit: 55, modifiers: [{ code: 'RELIABILITY_FLOOR_BREACH', points: -4 }] });

    expect(screen.getByText('-4 from adjustments')).toBeTruthy();
    expect(screen.getByText('-4')).toBeTruthy();
  });

  it('draws no block where the engine adjusted nothing', () => {
    draw({ fit: 59 });

    expect(screen.queryByText(MODIFIERS_HEADING)).toBeNull();
  });
});

describe('what else moved you here', () => {
  it('draws every liveness reason, where a card shows at most one', () => {
    draw({ livenessReasons: ['RECENT_ACTIVITY', 'ANSWER_RATE_AND_SPEED'] });

    expect(screen.getByText(WHAT_ELSE_MOVED_YOU_HERE)).toBeTruthy();
    expect(screen.getByText(livenessLine('RECENT_ACTIVITY'))).toBeTruthy();
    expect(screen.getByText(livenessLine('ANSWER_RATE_AND_SPEED'))).toBeTruthy();
  });

  it('draws the inclusion reason, which is why they are on the list at all', () => {
    draw({ inclusionReason: 'INTEREST_LIFT' });

    expect(screen.getByText('They already said yes to you')).toBeTruthy();
  });

  it('draws nothing where nothing moved them', () => {
    draw();

    expect(screen.queryByText(WHAT_ELSE_MOVED_YOU_HERE)).toBeNull();
  });
});

describe('the footer', () => {
  /**
   * Not decoration: `GET /searches/{id}` never recomputes, so a month-old read-back is today's
   * build drawing an older ruleset's arithmetic, and this pair is the only thing that says so.
   */
  it('stamps the ruleset and the engine the numbers came from', () => {
    draw();

    expect(screen.getByText('ruleset-v1 · matchfit-v1')).toBeTruthy();
  });
});

describe('a row this build could not read', () => {
  /**
   * ADR-0106 §6, **in place**: the numbers stand — *"those are numbers, not codes"* — and the
   * gap takes the name. The row staying is what keeps the column summing to the sub-total and
   * keeps its contribution out of the derived `applied`.
   */
  it('takes the gap as its label and keeps its three numbers', () => {
    draw({ terms: [{ ...LEVEL, term: null }, DISTANCE, OVERLAP] });

    expect(screen.getByText(OUT_OF_DATE_GAP)).toBeTruthy();
    expect(screen.getByText('×30 → 25')).toBeTruthy();
    expect(screen.getByText('59')).toBeTruthy();
  });

  /**
   * The reason the row is kept rather than dropped. Dropped, its 24,4 would leave the
   * sub-total at 35 and the derived `applied` at 30 — an adjustment the engine never made,
   * printed under a heading that says the engine made it.
   */
  it('keeps its contribution out of the adjustments it was never part of', () => {
    draw({ fit: 65, terms: [{ ...LEVEL, term: null }, DISTANCE, OVERLAP] });

    expect(screen.getByText('+6 from adjustments')).toBeTruthy();
    expect(screen.queryByText('+30 from adjustments')).toBeNull();
  });

  it('takes the gap where the reason line goes when the variant is the unreadable half', () => {
    draw({ terms: [{ ...LEVEL, evidence: null }, DISTANCE, OVERLAP] });

    expect(screen.getByText(termLabel('LEVEL_FIT'))).toBeTruthy();
    expect(screen.getByText(OUT_OF_DATE_GAP)).toBeTruthy();
  });

  it('is still one of the weighted terms the header counts', () => {
    draw({ terms: [{ ...LEVEL, term: null }, DISTANCE, OVERLAP] });

    expect(screen.getByText(whyFitHeader({ liveTerms: 3, mode: null }))).toBeTruthy();
  });
});
