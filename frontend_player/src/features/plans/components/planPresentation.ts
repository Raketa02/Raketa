/**
 * **What the plan card says** — §22.2, and every word on the three surfaces that edit it.
 *
 * The plan's sentences are this file's by **vocabulary owner** rather than by screen
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22): what happened in a
 * room is `conversationPresentation.ts`', the tab's own sentences are the shell's, and the three
 * slots are here — drawn in the room today and read on the game screen next
 * ([#368](https://github.com/Raketa02/Raketa/issues/368)).
 *
 * ## A chip reads its value or its name, and never a word about the state it is in
 *
 * §22.2's table is three rows and one column of names: `Where`, `Day`, `Hour`, replaced by the
 * value once there is one. **There is no lock, so there is nothing to word** — ADR-0144 deleted
 * *Lock it in*, the locked border and `locked by everybody`, and none of the three has a sentence
 * here because none of the three has a state.
 *
 * **The plan is drawn literally and never counted down** (ADR-0145 §7). Nothing here formats a
 * duration, nothing quotes an absolute instant, and nothing says how long is left: a card changing
 * is a card changing, not a door closing.
 *
 * ## Two of the three values are respelled and the third never is
 *
 * The **day** is drawn as a weekday, short on a chip in a row of seven and whole everywhere a
 * sentence names one — `dayLabel` and `dayName`, the tables the availability grid already spells,
 * rather than a fourth list of names. The **hour** is the clock face as the platform stores it.
 * The **place** is what somebody typed, which is why it is the only one that can overflow: it is
 * drawn through #335's *shorter value, not a second line* and **spoken whole**, which is §20.4 one
 * surface over. How many characters a chip may draw once the comma is gone is a measurement no
 * device has made, and this file does not invent one.
 *
 * ## The spoken name says which slot, because a row of three values says nothing on its own
 *
 * *Saturday* alone is not a control anybody can act on: §20's rule is one accessibility element
 * per action, and the action here is *change the day*. So every chip is spoken as its slot and
 * then its value — and an unfilled one says **not agreed yet** rather than reading its own drawn
 * label twice.
 */

import { weekdayOf } from '@/shared/date/platformZone';
import { placeWithoutTheCourt } from '@/shared/formatting/placeName';
import { dayLabel, dayName } from '@/shared/vocabulary/availabilityPresentation';

import { PLACE_CAP, slotValue, type Plan, type PlanSlot } from '../domain/slots';

/**
 * §22.2's three, keyed by the union — **so a slot with no name does not compile.**
 *
 * A `Record` rather than a function per slot, which is §1's split: not one of these quotes a
 * value. **The slots are labelled by what they are**, in ADR-0144's order and never renumbered.
 */
export const SLOT_NAME: Readonly<Record<PlanSlot, string>> = {
  where: 'Where',
  day: 'Day',
  hour: 'Hour',
};

/** The day, short — seven of these sit in one row and three letters tell Tuesday from Thursday. */
export function dayChipLabel(day: string): string {
  const weekday = weekdayOf(day);

  return weekday === undefined ? day : dayLabel(weekday);
}

/** The day, whole — what a listener hears, and what a filled slot draws. */
export function dayChipName(day: string): string {
  const weekday = weekdayOf(day);

  return weekday === undefined ? day : dayName(weekday);
}

/** What the chip **draws**: the value where there is one, and the slot's own name where not. */
export function slotChipLabel(plan: Plan | undefined, slot: PlanSlot): string {
  const value = slotValue(plan, slot);
  if (value === undefined) return SLOT_NAME[slot];

  if (slot === 'day') return dayChipName(value);
  if (slot === 'where') return placeWithoutTheCourt(value);

  return value;
}

/**
 * What the chip **says**: the slot, and then what it holds.
 *
 * The place is spoken **whole**, comma and court and all, which is the half of §20.4 the drawn
 * label cannot keep. A slot still going out says so rather than reading a value nobody has agreed
 * to yet — *pending, never optimistic* reaches the spoken name as well as the drawn one.
 */
export function slotChipName(
  plan: Plan | undefined,
  slot: PlanSlot,
  { pending = false }: { readonly pending?: boolean } = {},
): string {
  if (pending) return `${SLOT_NAME[slot]}: ${SAVING}`;

  const value = slotValue(plan, slot);
  if (value === undefined) return `${SLOT_NAME[slot]}: ${NOT_AGREED_YET}`;

  return `${SLOT_NAME[slot]}: ${slot === 'day' ? dayChipName(value) : value}`;
}

/** What an unfilled slot is, said rather than drawn. The drawn half is the slot's own name. */
export const NOT_AGREED_YET = 'not agreed yet';

/**
 * The chip's word while its write is going out — **6.1's busy shape, on 6.2's pill.**
 *
 * *Saving* rather than *Setting*, though §23's lines say *set the day*: the line is the record of
 * what happened and this is the one moment nothing has happened yet, so the verb that is true of
 * this instant is the one about the attempt.
 */
export const SAVING = 'Saving…';

/**
 * What each editor is called — a **statement of the act**, never the question the quick chips ask.
 *
 * *Which day works?* is a chip that posts words and changes nothing; this sheet records an
 * agreement. Wording the two the same way would blur the one distinction ADR-0144 draws hardest,
 * so these are the routes' own summaries: *set where you are meeting*, *the day you are playing*,
 * *the time you are playing*.
 */
export const SLOT_SHEET_TITLE: Readonly<Record<PlanSlot, string>> = {
  where: 'Where you are meeting',
  day: 'The day you are playing',
  hour: 'The time you are playing',
};

/** Never just *Close*: a name announced out of context has to say what is about to close. */
export const SLOT_SHEET_CLOSE: Readonly<Record<PlanSlot, string>> = {
  where: 'Close without changing where you are meeting',
  day: 'Close without changing the day',
  hour: 'Close without changing the time',
};

/** The box's own name. Drawn as well as spoken: it is the only control in that sheet. */
export const PLACE_FIELD_LABEL = 'Where';

/** A hint rather than a value — never a venue this app knows, because it knows none. */
export const PLACE_PLACEHOLDER = 'The club, or where to meet';

/** The one control that commits a typed value. The other two slots commit on the tap. */
export const RECORD_PLACE = 'Set the place';

/**
 * The box's own refusal, drawn under the field before anything is sent.
 *
 * **Refused, never truncated**, on the server's own words: *a shortened note is one the person who
 * typed it believes they wrote whole, in front of the other people on the court*. So the sentence
 * names the cap and hands the remedy back, and the control beside it is closed until it is met.
 */
export const PLACE_TOO_LONG = `That is longer than ${PLACE_CAP} characters. Shorten it and set it again.`;

/**
 * **The day row can be empty, and this is what stands under it.**
 *
 * Inside the entry grace the horizon has run out and no day may be set — a row of no chips is the
 * honest drawing of that, and a sentence beneath it is what stops the absence reading as a
 * failure to load. **These are this app's first words for it**: §22.2 wrote the refusal for a
 * moment that has passed and left this one to the ticket that draws the row.
 *
 * It names the act rather than a control, because the control is not on this screen: *we played*
 * is the game screen's, one door away in the header. ADR-0130's register — state the class of
 * problem, name nobody, grade nothing.
 */
export const NO_DAY_LEFT_TO_SET =
  'There is no day left to agree. All that is left is to say you played.';
