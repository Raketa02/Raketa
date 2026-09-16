/**
 * **The court the reader shares with one person** — the radar's sheet asking *do we already
 * have a game* (ADR-0174 §4). A live one where both are still on it; otherwise the ended one
 * that is still news, for exactly as long as the Chats list names it.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import { courtWith } from './courtWith';
import { ENDED_ROW_SHELF_LIFE_MS } from './challengeInbox';
import type { Standing } from './standing';

const ME = 'me';
const KAROL = 'karol';
const BEA = 'bea';

const READ_AT = '2026-09-16T12:00:00Z';
const AN_HOUR_AGO = '2026-09-16T11:00:00Z';
const TWO_DAYS_AGO = '2026-09-14T12:00:00Z';

function challenge(
  challengeId: string,
  standing: Standing,
  seats: readonly ChallengeSeat[],
  over: Partial<Challenge> = {},
): Challenge {
  return {
    challengeId,
    organiserId: ME,
    standing,
    sport: 'padel',
    openedAt: '2026-09-05T09:00:00Z',
    readAt: READ_AT,
    seats,
    ...over,
  };
}

const IN = (playerId: string): ChallengeSeat => ({ playerId, answer: 'ACCEPTED' });

describe('the court the reader shares with somebody', () => {
  it('is the live one both are still on — a game played, a court being filled', () => {
    const saturday = challenge('sat', 'ON', [IN(ME), IN(KAROL)]);
    const filling = challenge('fill', 'LINE_UP_INCOMPLETE', [IN(ME), IN(KAROL), {}, {}]);

    expect(courtWith([saturday], ME, KAROL)?.challengeId).toBe('sat');
    expect(courtWith([filling], ME, KAROL)?.challengeId).toBe('fill');
  });

  it('is nothing where they hold no seat, or gave theirs up on a court that still stands', () => {
    const others = challenge('c', 'ON', [IN(ME), IN(BEA)]);
    const declined = challenge('d', 'LINE_UP_INCOMPLETE', [
      IN(ME),
      IN(BEA),
      { playerId: KAROL, answer: 'DECLINED' },
      {},
    ]);

    expect(courtWith([others], ME, KAROL)).toBeUndefined();
    expect(courtWith([declined], ME, KAROL)).toBeUndefined();
  });

  /** The reader who left is a stranger to the court again, whoever is still on it. */
  it('is nothing where the reader left the court', () => {
    const left = challenge('l', 'LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'LEFT' },
      IN(KAROL),
      IN(BEA),
      {},
    ]);
    expect(courtWith([left], ME, KAROL)).toBeUndefined();
  });

  /**
   * *One behind them*: an ended court is named for as long as its row is news on the Chats
   * list, and no longer — the cool-off's own window never crosses the wire, and a court a year
   * behind two people is not a reason to refuse them a game.
   */
  it('is the ended court while its row is still news, and nothing once it has left the list', () => {
    const fresh = challenge('f', 'LAPSED', [IN(ME), { playerId: KAROL, answer: 'LAPSED' }], {
      endedAt: AN_HOUR_AGO,
      endedBy: KAROL,
    });
    const stale = challenge('s', 'LAPSED', [IN(ME), { playerId: KAROL, answer: 'LAPSED' }], {
      endedAt: TWO_DAYS_AGO,
      endedBy: KAROL,
    });

    expect(courtWith([fresh], ME, KAROL)?.challengeId).toBe('f');
    expect(courtWith([stale], ME, KAROL)).toBeUndefined();
    expect(Date.parse(READ_AT) - Date.parse(TWO_DAYS_AGO)).toBeGreaterThan(ENDED_ROW_SHELF_LIFE_MS);
  });

  /** A no of the reader's own leaves the list at once, and names no court here either. */
  it('is nothing for an ending that was the reader’s own act', () => {
    const myNo = challenge('n', 'DECLINED', [IN(KAROL), { playerId: ME, answer: 'DECLINED' }], {
      organiserId: KAROL,
      endedAt: AN_HOUR_AGO,
      endedBy: ME,
    });
    expect(courtWith([myNo], ME, KAROL)).toBeUndefined();
  });

  it('prefers a live court to an ended one, and the newest of each as the list orders them', () => {
    const ended = challenge('e', 'CALLED_OFF', [IN(ME), IN(KAROL)], {
      endedAt: AN_HOUR_AGO,
      endedBy: KAROL,
      gameId: 'g',
    });
    const live = challenge('live', 'ON', [IN(ME), IN(KAROL)]);
    const older = challenge('older', 'ON', [IN(ME), IN(KAROL)]);

    expect(courtWith([ended, live, older], ME, KAROL)?.challengeId).toBe('live');
    expect(courtWith([ended], ME, KAROL)?.challengeId).toBe('e');
  });
});
