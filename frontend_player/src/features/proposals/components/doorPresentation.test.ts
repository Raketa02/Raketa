/**
 * The door's panel, word for word — the words §28, written once for each declared kind, each cost
 * line with a singular and a zero form.
 */

import {
  doorQuestion,
  doorSpoken,
  doorTitle,
  dropCost,
  eitherCost,
  keepLabel,
} from './doorPresentation';

const ANIA = { yours: 'competitive', tapped: 'forFun' } as const;
const KUBA = { yours: 'forFun', tapped: 'competitive' } as const;

describe('what the panel says the player declared', () => {
  it('names the sport inside the sentence, and the kind they play', () => {
    expect(doorTitle(ANIA, 'padel')).toBe(
      'You play padel competitively, so Raketa only puts you in competitive games.',
    );
    expect(doorQuestion(ANIA)).toBe('Want for-fun games too?');
  });

  it('is the mirror for a for-fun player', () => {
    expect(doorTitle(KUBA, 'tennis')).toBe(
      'You play tennis for fun, so Raketa only puts you in for-fun games.',
    );
    expect(doorQuestion(KUBA)).toBe('Want competitive games too?');
  });
});

describe('what each answer costs', () => {
  it('counts the cards Either suits me keeps', () => {
    expect(eitherCost({ ...ANIA, count: 7 })).toBe(
      'Keep your 7 competitive cards and get for-fun ones too.',
    );
    expect(eitherCost({ ...ANIA, count: 1 })).toBe(
      'Keep your 1 competitive card and get for-fun ones too.',
    );
    expect(eitherCost({ ...KUBA, count: 3 })).toBe(
      'Keep your 3 for-fun cards and get competitive ones too.',
    );
  });

  it('drops the number when there is nothing to keep', () => {
    expect(eitherCost({ ...ANIA, count: 0 })).toBe(
      'Get for-fun games as well as competitive ones.',
    );
    expect(eitherCost({ ...KUBA, count: 0 })).toBe(
      'Get competitive games as well as for-fun ones.',
    );
  });

  it('counts the cards the kind tapped lets go, and keeps the games you’re In on', () => {
    expect(dropCost({ ...ANIA, count: 7 })).toBe(
      'Your 7 competitive cards go. Games you’re In on stay.',
    );
    expect(dropCost({ ...ANIA, count: 1 })).toBe(
      'Your 1 competitive card goes. Games you’re In on stay.',
    );
    expect(dropCost({ ...KUBA, count: 2 })).toBe(
      'Your 2 for-fun cards go. Games you’re In on stay.',
    );
  });

  it('says Raketa stops dealing the kind when there is no card to let go', () => {
    expect(dropCost({ ...ANIA, count: 0 })).toBe(
      'Raketa stops dealing you competitive games. Games you’re In on stay.',
    );
    expect(dropCost({ ...KUBA, count: 0 })).toBe(
      'Raketa stops dealing you for-fun games. Games you’re In on stay.',
    );
  });
});

describe('the way out, and the door itself', () => {
  it('keeps the kind the player plays', () => {
    expect(keepLabel(ANIA)).toBe('Keep competitive');
    expect(keepLabel(KUBA)).toBe('Keep for fun');
  });

  it('names the door without a number', () => {
    expect(doorSpoken('forFun')).toBe('For fun, not a kind you play');
    expect(doorSpoken('competitive')).toBe('Competitive, not a kind you play');
  });
});
