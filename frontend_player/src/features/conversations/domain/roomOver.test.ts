/**
 * How a room that ended while it was on screen is read — from what it last said, and the
 * ending rule. The module note is the argument; these are its three arms and their edge.
 */

import { roomEnding } from './roomOver';

const ME = 'me';
const TOMEK = { playerId: 'tomek', nickname: 'tomek.p' };
const OLA = { playerId: 'ola', nickname: 'ola.k' };

describe('a room without a game', () => {
  it('ended because everybody else in it left', () => {
    expect(roomEnding({ members: [{ playerId: ME }, TOMEK] }, ME)).toEqual({
      kind: 'they-left',
      members: [TOMEK],
    });
  });

  /** Two at once is a phone that missed the first line's nudge and is catching up. */
  it('names everybody who left where the phone is catching up on two', () => {
    expect(roomEnding({ members: [{ playerId: ME }, TOMEK, OLA] }, ME)).toEqual({
      kind: 'they-left',
      members: [TOMEK, OLA],
    });
  });

  /** The reader was alone, so the last seat deciding must have said no or run out of time. */
  it('ended with nobody else coming where the reader was alone', () => {
    expect(roomEnding({ members: [{ playerId: ME }] }, ME)).toEqual({
      kind: 'nobody-else-coming',
    });
  });

  it('never names the reader', () => {
    const ending = roomEnding({ members: [TOMEK, { playerId: ME, nickname: 'me_' }] }, ME);

    expect(ending.kind).toBe('they-left');
    expect(ending.kind === 'they-left' ? ending.members : []).toEqual([TOMEK]);
  });
});

describe('a room with a game', () => {
  /** Over for a reason the game's card says — called off, or the grace after *we played*. */
  it('says only that it ended, whoever was in it', () => {
    expect(roomEnding({ gameId: 'g1', members: [{ playerId: ME }, TOMEK] }, ME)).toEqual({
      kind: 'ended',
    });
    expect(roomEnding({ gameId: 'g1', members: [{ playerId: ME }] }, ME)).toEqual({
      kind: 'ended',
    });
  });
});
