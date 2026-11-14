import { joinedAgo } from './joiner';

describe('joinedAgo — the Joined ladder, in Warsaw days (the mechanics §7.3)', () => {
  it.each<[number, ReturnType<typeof joinedAgo>]>([
    [0, { kind: 'today' }],
    [1, { kind: 'yesterday' }],
    [2, { kind: 'days', days: 2 }],
    [6, { kind: 'days', days: 6 }],
    [7, { kind: 'lastWeek' }],
    [13, { kind: 'lastWeek' }],
    [14, { kind: 'weeks', weeks: 2 }],
    [20, { kind: 'weeks', weeks: 2 }],
    [21, { kind: 'weeks', weeks: 3 }],
    [27, { kind: 'weeks', weeks: 3 }],
    [28, { kind: 'weeks', weeks: 4 }],
    [30, { kind: 'weeks', weeks: 4 }],
  ])('%i days', (days, ago) => {
    expect(joinedAgo(days)).toEqual(ago);
  });

  it('never says more than four weeks, nor less than today', () => {
    expect(joinedAgo(45)).toEqual({ kind: 'weeks', weeks: 4 });
    expect(joinedAgo(-1)).toEqual({ kind: 'today' });
  });
});
