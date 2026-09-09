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
  EVERYBODY_SAID_YES,
  NOTHING_IS_LEFT_TO_AGREE,
  NOT_AGREED_YET,
  PLAN_PANEL,
  PLAN_SPOKEN_LEAD,
  QUICK_CHIP,
  SAVING,
  SLOT_IN_A_SENTENCE,
  SLOT_NAME,
  STILL_TO_AGREE,
  checklistLines,
  dayChipLabel,
  dayChipName,
  planTagsName,
  slotChipLabel,
  slotChipName,
  slotsStillToAgree,
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

describe('the quick chips', () => {
  /**
   * §22.4. **Each chip asks the question its slot is about and names nothing** — the prototype's
   * three were a weekday, a part of day and one fixture venue, and *a chip naming Saturday is a
   * chip that is wrong six days a week*.
   */
  it('asks a question per slot and names no day, no part of a day and no venue', () => {
    expect(QUICK_CHIP.where).toBe('Where shall we play?');
    expect(QUICK_CHIP.day).toBe('Which day works?');
    expect(QUICK_CHIP.hour).toBe('What time?');
    expect(QUICK_CHIP['on-my-way']).toBe('On my way');

    const named = /monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|evening/i;
    for (const words of Object.values(QUICK_CHIP)) expect(words).not.toMatch(named);
  });
});

describe('the panel over the plan', () => {
  /**
   * §5.4's fourth correction. The design's *No clock time yet — on purpose* explains an absence
   * and goes away once somebody fills the slot; this one **names** one and is true of a complete
   * plan, which is the whole of ADR-0145 §6's inversion.
   */
  it('names an absence rather than explaining one', () => {
    expect(PLAN_PANEL.title).toBe('Agreed between you — nothing is booked');
    expect(PLAN_PANEL.body).toMatch(/does not hold courts/);
    expect(`${PLAN_PANEL.title} ${PLAN_PANEL.body}`).not.toMatch(/on purpose|no clock time/i);
  });
});

describe('what is still to agree', () => {
  /** §22.6's two worked examples, in slot order and joined the platform's one way. */
  it('is the unfilled slots in slot order, with a final and', () => {
    expect(slotsStillToAgree(plan({ day: '2026-09-13' }))).toBe(
      `${SLOT_IN_A_SENTENCE.where} and ${SLOT_IN_A_SENTENCE.hour}`,
    );
    expect(slotsStillToAgree(plan())).toBe('where, the day and the hour');
  });

  /** *No plan* and *nothing agreed* are one state here too. */
  it('reads a missing plan exactly as an empty one', () => {
    expect(slotsStillToAgree(undefined)).toBe(slotsStillToAgree(plan()));
  });
});

describe('the checklist', () => {
  const WORTH = 'This one counts, so an agreed score becomes part of your record.';

  const full = plan({ place: 'Zabłocie Sport', day: '2026-09-13', hour: '18:00' });

  /** Three lines, capped, in one order: what is true now, what is left, what it moves. */
  it('is three lines in one order', () => {
    expect(checklistLines(plan({ place: 'Zabłocie Sport' }), WORTH)).toEqual([
      EVERYBODY_SAID_YES,
      `${STILL_TO_AGREE}: the day and the hour.`,
      WORTH,
    ]);
  });

  /**
   * The whole list is printed here and only here, which is what lets the card's gloss name the
   * next slot alone and stay four words.
   */
  it('prints the whole list where the gloss prints one', () => {
    expect(checklistLines(undefined, WORTH)[1]).toBe(
      `${STILL_TO_AGREE}: where, the day and the hour.`,
    );
  });

  it('says nothing is left once all three are filled', () => {
    expect(checklistLines(full, WORTH)[1]).toBe(NOTHING_IS_LEFT_TO_AGREE);
  });

  /**
   * The third line is `worthLine`'s, cited rather than written — so a `GameKind` this build
   * cannot read drops it and the other two stand, which is §3's rule for a fact that keys no
   * total.
   */
  it('drops the third line rather than writing one when there is no worth to cite', () => {
    expect(checklistLines(full, undefined)).toEqual([EVERYBODY_SAID_YES, NOTHING_IS_LEFT_TO_AGREE]);
  });

  /** The first line is the same three words on every rung: the rungs differ by the clock. */
  it('says the same first line whatever is agreed', () => {
    expect(checklistLines(undefined, WORTH)[0]).toBe(EVERYBODY_SAID_YES);
    expect(checklistLines(full, WORTH)[0]).toBe(EVERYBODY_SAID_YES);
  });
});

describe('the read-only plan’s spoken name', () => {
  /** §24.5's own spelling, and the place whole — §20.4's half the drawn tag cannot keep. */
  it('names each slot and then what it holds', () => {
    expect(
      planTagsName(plan({ place: 'Zabłocie Sport, court 3', day: '2026-09-13', hour: '18:00' })),
    ).toBe(`${PLAN_SPOKEN_LEAD} Where, Zabłocie Sport, court 3. Day, Sunday. Hour, 18:00.`);
  });

  it('says an unfilled slot is not agreed yet rather than reading its drawn label twice', () => {
    expect(planTagsName(plan({ hour: '18:00' }))).toBe(
      `${PLAN_SPOKEN_LEAD} ${SLOT_NAME.where}, ${NOT_AGREED_YET}. ${SLOT_NAME.day}, ${NOT_AGREED_YET}. ${SLOT_NAME.hour}, 18:00.`,
    );
  });
});
