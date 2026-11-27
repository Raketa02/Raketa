/**
 * **Top 10's own rules** ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home rows
 * mechanics §10) — which read the row asks for, and what it draws for an answer. Every place, level
 * and chip is the server's.
 */

import {
  topTenAsk,
  topTenFace,
  topTenReadFinished,
  type TopTen,
  type TopTenPlayer,
} from './topTen';

const ines: TopTenPlayer = {
  place: 1,
  playerId: 'p-ines',
  nickname: 'ines.d',
  level: 3.4,
  chip: { kind: 'DOWN', places: 1 },
  isYou: false,
};

const read = (over: Partial<TopTen> = {}): TopTen => ({
  sport: 'padel',
  anyoneListed: true,
  players: [ines],
  ...over,
});

describe('which read the row asks for', () => {
  it('prefers the opening sport, so the server falls through to one where somebody is ranked', () => {
    expect(topTenAsk(undefined, 'tennis')).toEqual({ kind: 'prefer', sport: 'tennis' });
  });

  it('asks for a picked sport exactly — empty, if nobody is ranked there', () => {
    expect(topTenAsk('squash', 'tennis')).toEqual({ kind: 'sport', sport: 'squash' });
    expect(topTenAsk('squash', undefined)).toEqual({ kind: 'sport', sport: 'squash' });
  });

  it('asks for nothing while the opening sport is still being worked out', () => {
    expect(topTenAsk(undefined, undefined)).toBeUndefined();
  });
});

describe('what the row draws', () => {
  it('is hidden while there is no answer, or one this build cannot read', () => {
    expect(topTenFace(undefined)).toEqual({ kind: 'hidden' });
    expect(topTenFace(null)).toEqual({ kind: 'hidden' });
  });

  it('is hidden while nobody is ranked in any sport', () => {
    expect(topTenFace(read({ anyoneListed: false, players: [] }))).toEqual({ kind: 'hidden' });
  });

  it('draws the cards the read holds — one or two as well as ten', () => {
    expect(topTenFace(read())).toEqual({ kind: 'cards', sport: 'padel', players: [ines] });
  });

  it('says nobody is ranked in a sport with nobody in it, while somebody is elsewhere', () => {
    expect(topTenFace(read({ sport: 'badminton', players: [] }))).toEqual({
      kind: 'nobody',
      sport: 'badminton',
    });
  });
});

// #871: what Home's reveal waits on for Top 10.
describe('whether Top 10’s read has finished, for Home', () => {
  const T = true;
  const F = false;

  it.each<[string, boolean, boolean, boolean, boolean]>([
    ['asked, and still out', T, F, F, F],
    ['asked, and finished', T, T, F, T],
    ['asked, still out, though a read behind it failed earlier', T, F, T, F],
    ['not asked yet, waiting for its sport', F, F, F, F],
    ['not asked yet, behind a read that failed with nothing read', F, F, T, T],
  ])('%s', (_case, asked, askedFinished, behindAFailure, finished) => {
    expect(topTenReadFinished({ asked, askedFinished, behindAFailure })).toBe(finished);
  });
});
