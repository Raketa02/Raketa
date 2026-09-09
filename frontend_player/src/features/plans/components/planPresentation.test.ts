/**
 * The copy deck's own edges — the ones the card cannot show because they are about a value the
 * server would have to have sent.
 *
 * What is asserted here is the split between what a chip **draws** and what it **says**: they are
 * two registers over one value, and §20.4's rule is that the visible one may be shortened and the
 * spoken one never is.
 */

import type { Plan } from '../domain/slots';

import {
  NOT_AGREED_YET,
  SAVING,
  SLOT_NAME,
  dayChipLabel,
  dayChipName,
  slotChipLabel,
  slotChipName,
} from './planPresentation';

const GAME = '11111111-0000-4000-8000-000000000001';

function plan(over: Partial<Plan> = {}): Plan {
  return { gameId: GAME, ...over };
}

describe('an unfilled slot', () => {
  it('draws the slot’s own name and says it is not agreed yet', () => {
    expect(slotChipLabel(undefined, 'day')).toBe(SLOT_NAME.day);
    expect(slotChipName(undefined, 'day')).toBe(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`);
  });

  /** *No plan* and *nothing agreed* are one state, so both read the same. */
  it('reads a missing plan exactly as an empty one', () => {
    expect(slotChipLabel(plan(), 'where')).toBe(slotChipLabel(undefined, 'where'));
  });
});

describe('the place', () => {
  /** Drawn without its court and spoken whole — §20.4, and #335's *shorter value*. */
  it('is drawn short and spoken in full', () => {
    const agreed = plan({ place: 'Zabłocie Sport, court 3' });

    expect(slotChipLabel(agreed, 'where')).toBe('Zabłocie Sport');
    expect(slotChipName(agreed, 'where')).toBe(`${SLOT_NAME.where}: Zabłocie Sport, court 3`);
  });
});

describe('the day', () => {
  it('is a weekday in both registers, short on the row and whole in a sentence', () => {
    expect(dayChipLabel('2026-09-12')).toBe('Sat');
    expect(dayChipName('2026-09-12')).toBe('Saturday');
    expect(slotChipLabel(plan({ day: '2026-09-12' }), 'day')).toBe('Saturday');
  });

  /**
   * A value the mapper would have dropped cannot reach here, so this is the belt rather than the
   * braces: the date is printed as it stands rather than being named a weekday it is not.
   */
  it('prints a value it cannot read as a weekday rather than naming one', () => {
    expect(dayChipLabel('someday')).toBe('someday');
    expect(dayChipName('someday')).toBe('someday');
  });
});

describe('a slot still going out', () => {
  /**
   * *Pending, never optimistic* reaches the spoken name as well as the drawn one: the value being
   * written must not be read out as though it were agreed.
   */
  it('says it is saving rather than reading the value it holds', () => {
    const agreed = plan({ hour: '18:00' });

    expect(slotChipName(agreed, 'hour', { pending: true })).toBe(`${SLOT_NAME.hour}: ${SAVING}`);
    expect(slotChipName(agreed, 'hour')).toBe(`${SLOT_NAME.hour}: 18:00`);
  });
});
