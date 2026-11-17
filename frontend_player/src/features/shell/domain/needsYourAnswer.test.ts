import {
  CLOSED,
  envelopeShows,
  needsYourAnswer,
  readingRecordOf,
  sheetIsUp,
  type NeedsYourAnswerSheet,
} from './needsYourAnswer';

const OPEN: NeedsYourAnswerSheet = { kind: 'open' };
const READING_INES: NeedsYourAnswerSheet = { kind: 'aside', reading: 'ines' };

describe('the envelope', () => {
  it('shows while anything waits, and not while nothing does', () => {
    expect(envelopeShows([1, 0])).toBe(true);
    expect(envelopeShows([0, 2])).toBe(true);
    expect(envelopeShows([0, 0])).toBe(false);
  });

  /** A read in flight or refused says nothing waits — the sheet is never opened empty. */
  it('does not show for a section whose read has not answered', () => {
    expect(envelopeShows([undefined, undefined])).toBe(false);
    expect(envelopeShows([undefined, 1])).toBe(true);
  });
});

describe('Needs your answer', () => {
  it('opens on the envelope, and closes on ✕, a swipe or the backdrop', () => {
    const open = needsYourAnswer(CLOSED, { kind: 'envelopePressed' });
    expect(open).toEqual(OPEN);

    expect(needsYourAnswer(open, { kind: 'dismissed' })).toEqual(CLOSED);
  });

  it('is up only while open and something waits in it', () => {
    expect(sheetIsUp(OPEN, true)).toBe(true);
    expect(sheetIsUp(OPEN, false)).toBe(false);
    expect(sheetIsUp(CLOSED, true)).toBe(false);
  });

  /** The last answer closes it for good: a request arriving later shows the envelope, not the sheet. */
  it('closes itself once nothing waits', () => {
    expect(needsYourAnswer(OPEN, { kind: 'emptied' })).toEqual(CLOSED);
    expect(needsYourAnswer(CLOSED, { kind: 'emptied' })).toEqual(CLOSED);
  });

  describe('a face opens the record', () => {
    /**
     * Under it, not gone: iOS drops a native window opened while another is closing (#800), so the
     * record is drawn over the sheet, as the vibe sheet's is, and the sheet stands beneath it.
     */
    it('steps aside under the record', () => {
      const aside = needsYourAnswer(OPEN, { kind: 'faceTapped', playerId: 'ines' });

      expect(aside).toEqual(READING_INES);
      expect(readingRecordOf(aside)).toBe('ines');
      expect(sheetIsUp(aside, true)).toBe(true);
    });

    /** The last request accepted from her record: the sheet beneath holds the record until it closes. */
    it('stays beneath the record while it is read, though nothing waits any more', () => {
      expect(sheetIsUp(READING_INES, false)).toBe(true);
    });

    it('comes back when the record closes, if anything still waits', () => {
      expect(needsYourAnswer(READING_INES, { kind: 'recordClosed', stillWaits: true })).toEqual(
        OPEN,
      );
    });

    it('stays closed when the record closes on nothing waiting — answered from the record', () => {
      expect(needsYourAnswer(READING_INES, { kind: 'recordClosed', stillWaits: false })).toEqual(
        CLOSED,
      );
    });

    /** The last request accepted from her record: the record stays up until it is closed. */
    it('keeps the record up while it is read, though nothing waits any more', () => {
      expect(needsYourAnswer(READING_INES, { kind: 'emptied' })).toEqual(READING_INES);
    });

    it('reads no record while the sheet is open or closed', () => {
      expect(readingRecordOf(OPEN)).toBeUndefined();
      expect(readingRecordOf(CLOSED)).toBeUndefined();
    });
  });

  /** A screen cannot stand behind a sheet: the questionnaire closes it for good. */
  it('closes for good when it hands over to a screen', () => {
    expect(needsYourAnswer(OPEN, { kind: 'handedToScreen' })).toEqual(CLOSED);
  });

  it('ignores what cannot happen where it stands', () => {
    expect(needsYourAnswer(CLOSED, { kind: 'faceTapped', playerId: 'ines' })).toEqual(CLOSED);
    expect(needsYourAnswer(CLOSED, { kind: 'recordClosed', stillWaits: true })).toEqual(CLOSED);
    expect(needsYourAnswer(READING_INES, { kind: 'envelopePressed' })).toEqual(READING_INES);
  });
});
