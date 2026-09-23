import { sentenceList } from './sentenceList';

describe('sentenceList', () => {
  it('says nothing about an empty list', () => {
    expect(sentenceList([])).toBe('');
  });

  it('is the item itself where there is one', () => {
    expect(sentenceList(['where'])).toBe('where');
  });

  /** §22.6's two worked examples, which is the whole of what the rule promises. */
  it('joins two with the conjunction and three with a comma before it', () => {
    expect(sentenceList(['where', 'the hour'])).toBe('where and the hour');
    expect(sentenceList(['where', 'the day', 'the hour'])).toBe('where, the day and the hour');
  });

  /** Nothing is dropped and nothing is shortened: that is the caller's business, never this. */
  it('keeps every item, however many there are', () => {
    expect(sentenceList(['a', 'b', 'c', 'd'])).toBe('a, b, c and d');
  });
});
