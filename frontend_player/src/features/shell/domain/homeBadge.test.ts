import { homeBadge } from './homeBadge';

describe('homeBadge — Home’s count, both loops added (#556)', () => {
  it('adds the Classic games that need you to the booked ones', () => {
    expect(homeBadge(2, 1)).toBe(3);
    expect(homeBadge(undefined, 2)).toBe(2);
    expect(homeBadge(1, 0)).toBe(1);
  });

  it('draws nothing when nothing needs you', () => {
    expect(homeBadge(undefined, 0)).toBeUndefined();
  });
});
