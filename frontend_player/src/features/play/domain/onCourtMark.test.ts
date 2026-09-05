import { PHOTO_REVIEWS } from './vocabulary';
import { wearsOnCourtMark } from './onCourtMark';

describe('the on-court mark', () => {
  it('is worn by a photograph the check passed', () => {
    expect(wearsOnCourtMark({ photoUrl: 'https://photos.example/x', photoReview: 'allowed' })).toBe(
      true,
    );
  });

  it('is not worn by a flagged photograph, and not worn by an unchecked one', () => {
    // The whole of the ticket's second acceptance line, and it is one assertion rather than
    // two because the two answers have to be the same answer: a card that told a searcher
    // another player's photo had been doubted would be publishing a moderation outcome about
    // a third party.
    const flagged = wearsOnCourtMark({
      photoUrl: 'https://photos.example/x',
      photoReview: 'flagged',
    });
    const unchecked = wearsOnCourtMark({ photoUrl: 'https://photos.example/x' });

    expect(flagged).toBe(unchecked);
    expect(flagged).toBe(false);
  });

  it('is not worn by the generated poster, whatever the verdict says', () => {
    // A poster is not a photograph and has nothing to have passed. The pair is omitted
    // together on the wire, so a verdict with no photo beside it is a state the contract does
    // not produce — and the rule refuses it anyway rather than trusting that it cannot arrive.
    for (const review of PHOTO_REVIEWS) {
      expect(wearsOnCourtMark({ photoReview: review })).toBe(false);
    }
    expect(wearsOnCourtMark({})).toBe(false);
  });

  it('marks exactly one of the verdicts the contract has', () => {
    // Keyed off the vocabulary rather than off two literals, so a third verdict arrives here
    // as a failing count rather than as a value that quietly falls to `false`.
    const marked = PHOTO_REVIEWS.filter((review) =>
      wearsOnCourtMark({ photoUrl: 'https://photos.example/x', photoReview: review }),
    );

    expect(marked).toEqual(['allowed']);
  });
});
