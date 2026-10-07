/**
 * *Blocked players* across the wire boundary — the list whole and in the server's order, and the
 * photograph only where there is one.
 */

import type { Wire } from '@/test-support/transport';

import { toBlockedPlayers } from './blockMappers';

function blocked(over: Partial<Wire['BlockedPlayerSchema']> = {}): Wire['BlockedPlayerSchema'] {
  return {
    player_id: 'e0000000-0000-4000-8000-000000000001',
    name: 'Kuba Wiśniewski',
    blocked_at: '2026-10-06T09:00:00Z',
    ...over,
  };
}

describe('Blocked players, off the wire', () => {
  it('keeps the server’s order — newest first — and every name whole', () => {
    const served = {
      players: [
        blocked({ player_id: 'e0000000-0000-4000-8000-000000000002', name: 'Zofia Bąk' }),
        blocked(),
      ],
    };

    expect(toBlockedPlayers(served).map((player) => [player.playerId, player.name])).toEqual([
      ['e0000000-0000-4000-8000-000000000002', 'Zofia Bąk'],
      ['e0000000-0000-4000-8000-000000000001', 'Kuba Wiśniewski'],
    ]);
  });

  it('carries the photograph where there is one, and nothing where there is none', () => {
    const [withPhoto, withNone] = toBlockedPlayers({
      players: [
        blocked({
          photo_id: 'f0000000-0000-4000-8000-000000000001',
          photo_url: 'https://photos.example/kuba.jpg',
        }),
        blocked(),
      ],
    });

    expect(withPhoto?.photoUrl).toBe('https://photos.example/kuba.jpg');
    expect(withNone !== undefined && 'photoUrl' in withNone).toBe(false);
  });

  it('answers an empty list with an empty list — nobody blocked, never a failure', () => {
    expect(toBlockedPlayers({ players: [] })).toEqual([]);
  });
});
