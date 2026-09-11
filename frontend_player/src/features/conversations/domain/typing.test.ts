/**
 * The typing roster — who is drawn, and when a heartbeat is due. Everything here is a rule a
 * component would otherwise carry, and every one of them is a rule somebody could be wrong about.
 */

import { TYPING_CADENCE_MS, beatIsDue, shownTypists, typists } from './typing';

const ME = 'aaaaaaaa-0000-4000-8000-000000000001';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';

describe('who is typing', () => {
  it('is the frame’s list, in the frame’s order', () => {
    expect(typists([TOMEK, OLA], ME)).toEqual([TOMEK, OLA]);
    expect(typists([OLA, TOMEK], ME)).toEqual([OLA, TOMEK]);
  });

  /**
   * The server filters the reader out of their own room's frame, and this is the second guard
   * the ticket asks for anyway: a composer drawing an indicator for the person using it is the
   * most visible possible bug, and one line here is what it costs to make it unreachable.
   */
  it('is never the reader, whatever the frame says', () => {
    expect(typists([ME], ME)).toEqual([]);
    expect(typists([TOMEK, ME, OLA], ME)).toEqual([TOMEK, OLA]);
  });

  it('names a person once, however many times a frame repeats them', () => {
    expect(typists([TOMEK, TOMEK], ME)).toEqual([TOMEK]);
  });

  /** A reader `users` has not answered for yet filters nobody, rather than everybody. */
  it('draws the whole frame while the reader is still unknown', () => {
    expect(typists([TOMEK], undefined)).toEqual([TOMEK]);
  });
});

describe('what is drawn', () => {
  /**
   * **A roster is only as live as the channel that carried it.** The server sends a frame when
   * the answer changes and never on a tick, so the only clear is the empty frame — and a channel
   * that is not live cannot deliver one. This is the client's own safety net, and it is the
   * channel rather than a clock, because a clock would clear the indicator on exactly the person
   * it exists for: somebody typing a long message gets one frame and then, correctly, silence.
   */
  it('is the roster on a live channel, and nobody on any other', () => {
    expect(shownTypists('live', [TOMEK])).toEqual([TOMEK]);
    expect(shownTypists('connecting', [TOMEK])).toEqual([]);
    expect(shownTypists('lost', [TOMEK])).toEqual([]);
    expect(shownTypists('closed', [TOMEK])).toEqual([]);
  });
});

describe('the heartbeat', () => {
  /** The route's own number: post about every 3 s while typing, under the server's 5 s expiry. */
  it('is due every three seconds and no more often', () => {
    expect(TYPING_CADENCE_MS).toBe(3000);
    expect(beatIsDue(undefined, 10_000)).toBe(true);
    expect(beatIsDue(10_000, 10_000)).toBe(false);
    expect(beatIsDue(10_000, 12_999)).toBe(false);
    expect(beatIsDue(10_000, 13_000)).toBe(true);
  });
});
