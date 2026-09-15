/**
 * *You said yes* — the one fact the client reads off its own outgoing list, and the one patch it
 * makes to that list on a tap's own answer
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8).
 */

import { outgoingAfterYes, saidYesTo } from './outgoingInterest';

const ANIA = 'aaaaaaaa-0000-4000-8000-000000000001';
const MAREK = 'bbbbbbbb-0000-4000-8000-000000000002';

describe('whether you said yes to somebody', () => {
  it('is true exactly for a person in your outgoing list for that sport', () => {
    const outgoing = { padel: [ANIA] };

    expect(saidYesTo(outgoing, 'padel', ANIA)).toBe(true);
    expect(saidYesTo(outgoing, 'padel', MAREK)).toBe(false);
  });

  /** A yes is per sport: saying yes to somebody in padel says nothing about tennis. */
  it('reads the sport on screen and no other', () => {
    expect(saidYesTo({ padel: [ANIA] }, 'tennis', ANIA)).toBe(false);
  });

  /** The read may not have landed; before it has, nobody is tagged rather than everybody. */
  it('is false before the list has been read at all', () => {
    expect(saidYesTo(undefined, 'padel', ANIA)).toBe(false);
  });
});

describe('the list after a yes of your own', () => {
  it('gains the person on a one-sided yes, so the tag appears without a second read', () => {
    expect(outgoingAfterYes({ padel: [ANIA] }, { sport: 'padel', playerId: MAREK }, false)).toEqual(
      { padel: [ANIA, MAREK] },
    );
  });

  it('starts the sport’s list where there was none', () => {
    expect(outgoingAfterYes({}, { sport: 'tennis', playerId: MAREK }, false)).toEqual({
      tennis: [MAREK],
    });
  });

  /** A second tap changes nothing on the wire, and it changes nothing here. */
  it('lists nobody twice', () => {
    expect(outgoingAfterYes({ padel: [ANIA] }, { sport: 'padel', playerId: ANIA }, false)).toEqual({
      padel: [ANIA],
    });
  });

  /**
   * A mutual is answered the instant it is written and is no longer *outgoing* — the wire files
   * it under `mutual`, and the person is off the list here too, so *You said yes* is never drawn
   * on somebody the reader has already matched.
   */
  it('takes the person off on a mutual', () => {
    expect(
      outgoingAfterYes({ padel: [ANIA, MAREK] }, { sport: 'padel', playerId: MAREK }, true),
    ).toEqual({ padel: [ANIA] });
  });
});
