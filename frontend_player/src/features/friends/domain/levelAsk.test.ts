import { LEVEL_ASK_FACES, askersFormOf, facesOnTheCard } from './levelAsk';

describe('askersFormOf — which sentence a level ask’s card says (the words §29.5)', () => {
  it('names one asker, two, or two and counts the rest', () => {
    expect(askersFormOf(1)).toBe('one');
    expect(askersFormOf(2)).toBe('two');
    expect(askersFormOf(3)).toBe('more');
    expect(askersFormOf(7)).toBe('more');
  });
});

describe('facesOnTheCard — up to three faces, newest first (the screens §6.4)', () => {
  it('draws every asker up to three, in the order served', () => {
    expect(facesOnTheCard(['tomek', 'kuba'])).toEqual(['tomek', 'kuba']);
    expect(facesOnTheCard(['tomek', 'kuba', 'ania', 'ewa'])).toEqual(['tomek', 'kuba', 'ania']);
    expect(LEVEL_ASK_FACES).toBe(3);
  });
});
