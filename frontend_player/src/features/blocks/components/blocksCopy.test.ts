/**
 * The feature's words — the two that are composed rather than fixed: the count on You › Account,
 * and the name, said whole wherever a sentence says it (ADR-0171 §4).
 */

import {
  blockRowLabel,
  blockSheetBody,
  blockSheetTitle,
  blockedCountLine,
  unblockRowLabel,
} from './blocksCopy';

describe('the count on You › Account', () => {
  it.each([
    [0, 'Nobody'],
    [1, '1 player'],
    [2, '2 players'],
    [12, '12 players'],
  ])('says %i as %s', (count, line) => {
    expect(blockedCountLine(count)).toBe(line);
  });
});

describe('the name', () => {
  const NAME = 'Kuba Wiśniewski';

  it('is said whole on the row, on the sheet and in what it says', () => {
    expect(blockRowLabel(NAME)).toBe('Block Kuba Wiśniewski');
    expect(unblockRowLabel(NAME)).toBe('Unblock Kuba Wiśniewski');
    expect(blockSheetTitle(NAME)).toBe('Block Kuba Wiśniewski?');
    expect(blockSheetBody(NAME)).toBe(
      "You won't be put in games with Kuba Wiśniewski. They aren't told.",
    );
  });
});
