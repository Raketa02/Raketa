import {
  CLOSED,
  envelopeShows,
  needsYourAnswer,
  readingRecordOf,
  sheetIsShown,
  sheetIsUp,
  wentForGood,
  type NeedsYourAnswerSheet,
} from './needsYourAnswer';

const OPEN: NeedsYourAnswerSheet = { kind: 'open' };
const ASKED: NeedsYourAnswerSheet = { kind: 'asked' };
const READING_INES: NeedsYourAnswerSheet = { kind: 'aside', reading: 'ines' };
const UNDER_A_SHEET: NeedsYourAnswerSheet = { kind: 'underTheFill', itsAGame: false };
const UNDER_ITS_A_GAME: NeedsYourAnswerSheet = { kind: 'underTheFill', itsAGame: true };

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

  /** #817: a payment to confirm and a friends game invitation are two more sections. */
  it('shows for a payment to confirm or an invitation alone', () => {
    expect(envelopeShows([1, 0, 0, 0])).toBe(true);
    expect(envelopeShows([undefined, 1, 0, 0])).toBe(true);
    expect(envelopeShows([undefined, 0, 0, 0])).toBe(false);
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
      expect(readingRecordOf(UNDER_A_SHEET)).toBeUndefined();
    });
  });

  /**
   * #817: **Confirm**, **Fix** and an invitation's *Accept* open the fill's sheets — the payment
   * confirmation, the card setup — over the sheet, and *It's a game!* over everything.
   */
  describe('the fill opens a sheet from it', () => {
    it('steps aside under the confirmation or the card setup, and stays up beneath it', () => {
      const under = needsYourAnswer(OPEN, { kind: 'fillRaised', itsAGame: false });

      expect(under).toEqual(UNDER_A_SHEET);
      expect(sheetIsUp(under, true)).toBe(true);
      // The payment confirmed from it was the last thing waiting: the sheet holds the fill's up.
      expect(sheetIsUp(under, false)).toBe(true);
      expect(needsYourAnswer(under, { kind: 'emptied' })).toEqual(UNDER_A_SHEET);
    });

    it('hands back when that sheet closes, if anything still waits', () => {
      expect(needsYourAnswer(UNDER_A_SHEET, { kind: 'fillGone', stillWaits: true })).toEqual(OPEN);
    });

    it('closes with it when nothing waits any more', () => {
      expect(needsYourAnswer(UNDER_A_SHEET, { kind: 'fillGone', stillWaits: false })).toEqual(
        CLOSED,
      );
    });

    /** It's a game! closes the sheet for good, whatever still waits. */
    it('closes for good once It’s a game! was raised over it', () => {
      expect(needsYourAnswer(OPEN, { kind: 'fillRaised', itsAGame: true })).toEqual(
        UNDER_ITS_A_GAME,
      );
      // The confirmation's answer books the game: the sheet it was is followed by It's a game!.
      const booked = needsYourAnswer(UNDER_A_SHEET, { kind: 'fillRaised', itsAGame: true });
      expect(booked).toEqual(UNDER_ITS_A_GAME);
      expect(needsYourAnswer(booked, { kind: 'fillGone', stillWaits: true })).toEqual(CLOSED);
    });

    it('remembers It’s a game! though the fill raises a sheet after it', () => {
      expect(needsYourAnswer(UNDER_ITS_A_GAME, { kind: 'fillRaised', itsAGame: false })).toEqual(
        UNDER_ITS_A_GAME,
      );
    });

    /** A fill raised from the deck, or a game's details, is nothing to the sheet. */
    it('ignores the fill while the sheet is not open', () => {
      expect(needsYourAnswer(CLOSED, { kind: 'fillRaised', itsAGame: true })).toEqual(CLOSED);
      expect(needsYourAnswer(CLOSED, { kind: 'fillGone', stillWaits: true })).toEqual(CLOSED);
      expect(needsYourAnswer(OPEN, { kind: 'fillGone', stillWaits: false })).toEqual(OPEN);
      expect(needsYourAnswer(READING_INES, { kind: 'fillRaised', itsAGame: false })).toEqual(
        READING_INES,
      );
    });
  });

  /**
   * #817, ADR-0205 §1: a friend link or a friends game invitation's notice opens Home with the sheet
   * already up — once the reads it re-read have landed, and only if something waits by then.
   */
  describe('asked for by a link or a notice', () => {
    it('waits for the reads, drawn nowhere until they land', () => {
      const asked = needsYourAnswer(CLOSED, { kind: 'asked' });

      expect(asked).toEqual(ASKED);
      expect(sheetIsUp(asked, true)).toBe(false);
      // Nothing read yet is not nothing waiting.
      expect(needsYourAnswer(asked, { kind: 'emptied' })).toEqual(ASKED);
    });

    it('opens once they land with something waiting', () => {
      expect(needsYourAnswer(ASKED, { kind: 'settled', stillWaits: true })).toEqual(OPEN);
    });

    /** A crossing request made friends, or a block swallowed it: Home as it is, never an empty sheet. */
    it('stays closed when nothing waits by then', () => {
      expect(needsYourAnswer(ASKED, { kind: 'settled', stillWaits: false })).toEqual(CLOSED);
    });

    it('opens at once on the envelope while it waits', () => {
      expect(needsYourAnswer(ASKED, { kind: 'envelopePressed' })).toEqual(OPEN);
    });

    it('leaves a sheet already up where it is', () => {
      expect(needsYourAnswer(OPEN, { kind: 'asked' })).toEqual(OPEN);
      expect(needsYourAnswer(READING_INES, { kind: 'asked' })).toEqual(READING_INES);
      expect(needsYourAnswer(UNDER_A_SHEET, { kind: 'asked' })).toEqual(UNDER_A_SHEET);
      expect(needsYourAnswer(OPEN, { kind: 'settled', stillWaits: false })).toEqual(OPEN);
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
    expect(needsYourAnswer(UNDER_A_SHEET, { kind: 'faceTapped', playerId: 'ines' })).toEqual(
      UNDER_A_SHEET,
    );
    expect(needsYourAnswer(UNDER_A_SHEET, { kind: 'dismissed' })).toEqual(UNDER_A_SHEET);
  });
});

/**
 * **When the sheet went for good** (#819, ADR-0205 §3) — what records the visit. Every way it goes
 * away counts, from wherever it stood up; stepping aside for a record or a fill's sheet does not,
 * since it comes back; and a sheet a link asked for that never opened was never shown.
 */
describe('went for good', () => {
  const SHOWN = [OPEN, READING_INES, UNDER_A_SHEET, UNDER_ITS_A_GAME];

  it('is every close from a sheet that was up — ✕, a swipe, the backdrop, the last answer, a screen', () => {
    for (const event of [
      { kind: 'dismissed' },
      { kind: 'emptied' },
      { kind: 'handedToScreen' },
    ] as const) {
      expect(wentForGood(OPEN, needsYourAnswer(OPEN, event))).toBe(true);
    }
  });

  it('is a record or a fill closing with nothing left, and It’s a game! going', () => {
    expect(
      wentForGood(
        READING_INES,
        needsYourAnswer(READING_INES, { kind: 'recordClosed', stillWaits: false }),
      ),
    ).toBe(true);
    expect(
      wentForGood(
        UNDER_A_SHEET,
        needsYourAnswer(UNDER_A_SHEET, { kind: 'fillGone', stillWaits: false }),
      ),
    ).toBe(true);
    expect(
      wentForGood(
        UNDER_ITS_A_GAME,
        needsYourAnswer(UNDER_ITS_A_GAME, { kind: 'fillGone', stillWaits: true }),
      ),
    ).toBe(true);
  });

  /** A link or a notice asking for it in the same render as the close: still a close. */
  it('is a close a link asks for again in the same breath', () => {
    expect(wentForGood(OPEN, ASKED)).toBe(true);
  });

  it('is not stepping aside, nor coming back', () => {
    expect(wentForGood(OPEN, READING_INES)).toBe(false);
    expect(wentForGood(OPEN, UNDER_A_SHEET)).toBe(false);
    expect(wentForGood(READING_INES, OPEN)).toBe(false);
    expect(wentForGood(UNDER_A_SHEET, OPEN)).toBe(false);
    expect(wentForGood(UNDER_A_SHEET, UNDER_ITS_A_GAME)).toBe(false);
  });

  /** Nothing was shown: Home as it is, with no sheet, and no visit. */
  it('is not a sheet a link asked for that never opened', () => {
    expect(wentForGood(ASKED, needsYourAnswer(ASKED, { kind: 'settled', stillWaits: false }))).toBe(
      false,
    );
  });

  it('is not standing still', () => {
    for (const sheet of [CLOSED, ASKED, ...SHOWN]) expect(wentForGood(sheet, sheet)).toBe(false);
  });
});

/**
 * **When the sheet is shown** (#819) — what a read drawn into it must be, to count as seen: open with
 * something in it, never stepped aside under a record or a fill's sheet, whose scrim covers it.
 */
describe('shown', () => {
  it('is open with something waiting', () => {
    expect(sheetIsShown(OPEN, true)).toBe(true);
    expect(sheetIsShown(OPEN, false)).toBe(false);
  });

  it('is not up beneath a record or a fill’s sheet, though it is up', () => {
    for (const covered of [READING_INES, UNDER_A_SHEET, UNDER_ITS_A_GAME]) {
      expect(sheetIsUp(covered, true)).toBe(true);
      expect(sheetIsShown(covered, true)).toBe(false);
    }
  });

  it('is not closed, nor asked for', () => {
    expect(sheetIsShown(CLOSED, true)).toBe(false);
    expect(sheetIsShown(ASKED, true)).toBe(false);
  });
});
