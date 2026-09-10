/**
 * The challenge screen's own sentences — **the ones no other surface writes.**
 *
 * §13's seventeen standing sentences are `challengePresentation.test.ts`' and are not re-asserted
 * here. What is asserted is the copy this screen added: the two answers, the segment that
 * disappears, and the two absences that must never collapse into one.
 */

import { PAIRING_ABSENCES } from '../domain/challengeDetail';

import {
  IM_IN,
  NOT_THIS_TIME,
  challengeCardLabel,
  identityRow,
  pairingAbsenceLine,
} from './challengeDetailPresentation';

const PERSON = {
  nickname: 'bea.k',
  areaCode: 'WAW-C',
  level: 2.71,
  band: 'Established',
  range: { low: 2.55, high: 2.87 },
} as const;

describe('the two answers', () => {
  /**
   * *Accept — game on* is false the moment it is tapped: accepting arranges nothing and draws
   * **Planning**, so the label is what the standing says back in the other person.
   */
  it('names no state the act cannot produce', () => {
    expect(IM_IN).toBe("I'm in");
    expect(NOT_THIS_TIME).toBe('Not this time');
  });
});

describe('the identity row', () => {
  it('states the level, the distance and the score, in that order', () => {
    expect(identityRow({ person: { ...PERSON, playerScore: 91 }, distanceKm: 3 })).toBe(
      '2,71 · Established · likely 2,55 – 2,87 · 3 km · Score 91',
    );
  });

  /**
   * ADR-0140: a nought printed for somebody nothing was watched of is a claim where there is a
   * gap, and most people on this platform have no Player Score at all today.
   */
  it('drops the score segment rather than printing a nought', () => {
    const row = identityRow({ person: PERSON, distanceKm: 3 });

    expect(row).toBe('2,71 · Established · likely 2,55 – 2,87 · 3 km');
    expect(row).not.toContain('Score');
  });

  /** Omitted and never zero: somebody whose distance could not be read is not next door. */
  it('drops the distance when the term stood down', () => {
    expect(identityRow({ person: PERSON })).toBe('2,71 · Established · likely 2,55 – 2,87');
  });
});

describe('a pairing that could not be computed', () => {
  /**
   * ADR-0143 §6: an outage drawing the **identical** absence as an unrated sport is
   * indistinguishable from four erased accounts, so the two codes keep two sentences.
   */
  it('says something different about each of the two codes', () => {
    const said = PAIRING_ABSENCES.map((absence) => pairingAbsenceLine(absence, 'Padel'));

    expect(new Set(said).size).toBe(PAIRING_ABSENCES.length);
  });

  /** *Being asked to play a sport you never declared for is how this works rather than a
   * corner of it* — so the sentence states the fact and apologises for nothing. */
  it('names the sport it has nothing to compare in, and does not apologise', () => {
    const line = pairingAbsenceLine('NOTHING_TO_COMPUTE', 'Padel');

    expect(line).toContain('Padel');
    expect(line.toLowerCase()).not.toContain('sorry');
  });

  /** An unrelated outage must never read as *you cannot answer your challenge*. */
  it('never tells the reader they cannot answer', () => {
    for (const absence of PAIRING_ABSENCES) {
      expect(pairingAbsenceLine(absence, 'Padel').toLowerCase()).not.toContain("can't answer");
    }
  });
});

describe("the card's spoken name", () => {
  const FACTS = {
    person: { ...PERSON, playerScore: 91 },
    fit: 78,
    distanceKm: 3,
    reasons: [
      'You both play evenings',
      'A close match on level',
      'You overlap on four slots this week',
    ],
    concerns: ['Their record is thin'],
  } as const;

  /**
   * §24.3: *a merged label that cannot state its subject inside the cap is evidence the seam is
   * wrong — here it states the handle first, which is the fact the whole screen is about.*
   */
  it('leads with the handle', () => {
    expect(challengeCardLabel(FACTS).startsWith('bea.k')).toBe(true);
  });

  /**
   * **No fact the card draws is silent.** The card's drawn terms are filtered out of its reason
   * lines, so a fact drawn and not spoken is a fact a listener is never told at all — which is
   * the failure the drawn set exists to make impossible in both registers.
   */
  it('states every fact the card draws', () => {
    const label = challengeCardLabel(FACTS);

    expect(label).toContain('78');
    expect(label).toContain('2,71');
    expect(label).toContain('3 km');
    expect(label).toContain('91');
  });

  it('keeps the argument, and keeps it last', () => {
    const label = challengeCardLabel(FACTS);

    expect(label).toContain('You overlap on four slots this week');
    expect(label.endsWith('Their record is thin.')).toBe(true);
  });

  it('says nothing about a score the platform has not watched', () => {
    const label = challengeCardLabel({ person: PERSON, fit: 78, reasons: [], concerns: [] });

    expect(label).not.toContain('Player Score');
  });
});
