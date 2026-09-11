/**
 * **What the plan says** — §22.2's three slots and §22.4's four quick chips, and every word on the
 * surfaces that edit them.
 *
 * The plan's sentences are this file's by **vocabulary owner** rather than by screen
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22, which assigns it
 * §22.2 **and** §22.4): what happened in a room is `conversationPresentation.ts`', the tab's own
 * sentences are the shell's, and everything about the plan is here — the three slots, drawn as
 * chips in the room and read as tags on the game screen
 * ([#368](https://github.com/Raketa02/Raketa/issues/368)), the four questions the room asks about
 * them, and the panel and the checklist the game screen draws around them.
 *
 * ## §22.6 is split across two decks and the slot names are why
 *
 * The **gloss** is `nowPresentation.ts`' because it is a card's line; the **checklist** is here
 * because it is the plan's own fuller account and the game screen is where the plan is read. What
 * they share is the sentence register of the three slot names, so `SLOT_IN_A_SENTENCE` moved here
 * beside `SLOT_NAME` when the second reader arrived: two tables, one for a control and one for a
 * sentence, sitting together where the difference between them is visible.
 *
 * ## A chip reads its value or its name, and never a word about the state it is in
 *
 * §22.2's table is three rows and one column of names: `Where`, `Day`, `Hour`, replaced by the
 * value once there is one. **The lock is an act, and the words for it are a control and a
 * counter** ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
 * [#403](https://github.com/Raketa02/Raketa/issues/403)): `Lock the plan` on the button, always
 * and with no reason appended, and `N of 3 set` on the counter above it until it reads `Locked`.
 * **`locked by everybody` stays deleted** — nothing records assent from anyone but the one person
 * who tapped, so *by everybody* is a claim the data cannot support, and the word is one this
 * card can. The sentence the lock writes into the room is `conversationPresentation.ts`', by
 * §23's assignment.
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
import { sentenceList } from '@/shared/formatting/sentenceList';
import { dayLabel, dayName } from '@/shared/vocabulary/availabilityPresentation';

import { SLOTS, isLocked, slotCount } from '../domain/lock';
import type { QuickChip } from '../domain/quickChips';
import {
  PLACE_CAP,
  PLAN_SLOTS,
  slotValue,
  unfilledSlots,
  type Plan,
  type PlanSlot,
} from '../domain/slots';

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

  return `${SLOT_NAME[slot]}: ${spokenSlotValue(plan, slot)}`;
}

/**
 * **What one slot holds, said** — the value whole, and *not agreed yet* where there is none.
 *
 * The one place a slot's **spoken** value is spelled, read by the chip in the room and by the
 * read-only tags on the game screen. The two differ in their punctuation and in nothing else, and
 * a second copy of *the day is a weekday and the place is never shortened* is exactly the drift
 * `slots.ts` exists to prevent one layer down.
 */
function spokenSlotValue(plan: Plan | undefined, slot: PlanSlot): string {
  const value = slotValue(plan, slot);
  if (value === undefined) return NOT_AGREED_YET;

  return slot === 'day' ? dayChipName(value) : value;
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

// ---------------------------------------------------------------------------
// The eyebrow, the counter and the lock
// ---------------------------------------------------------------------------

/**
 * The card's eyebrow. Drawn uppercase by 3.3's section rule — `eyebrow` labels a region you are
 * reading, and is emphatically not `h2`, which titles a card and never a section.
 */
export const THE_PLAN = 'The plan';

/**
 * What the counter reads once the plan is locked — **one word, and never `locked by everybody`.**
 *
 * The word is the whole of what carries the fact once the button has gone (`domain/lock.ts`), so
 * it is what discharges Part 13's *never colour alone* for the locked state: the pill does not
 * change colour, and it would not be enough if it did.
 */
export const LOCKED = 'Locked';

/**
 * **The counter** — `N of 3 set`, and `Locked` once somebody has said so.
 *
 * The count is **derived here from the three fields** and never sent: the plan schema's own
 * docstring refuses a count on the wire as *the one derived value that could disagree with the
 * three fields beside it*. The lock replaces the count rather than sitting beside it, because a
 * locked plan is a complete one by the server's own guard and `3 of 3 set · Locked` would say the
 * guard twice.
 */
export function counterLabel(plan: Plan | undefined): string {
  return isLocked(plan) ? LOCKED : `${slotCount(plan)} of ${SLOTS} set`;
}

/**
 * **The eyebrow and the counter as one spoken name** — `The plan, 1 of 3 set`.
 *
 * One `header` element for the heading and its count, which is `YOUR GAMES · n`'s own shape
 * (§24.5), with a comma where the drawing has a pill: a listener has no reading for a layout,
 * which is §24.4's argument about the middle dot one surface over.
 */
export function planHeadingName(plan: Plan | undefined): string {
  return `${THE_PLAN}, ${counterLabel(plan)}`;
}

/**
 * The button's label, **always** — greyed, live or busy, and never with the reason appended.
 *
 * The mock read *Lock it in · set all three first*; the reason is struck because the counter
 * directly above already says `1 of 3 set`, and a second sentence would be the same count in a
 * second spelling. `domain/lock.ts` is where that is argued against #324's rule.
 */
export const LOCK_THE_PLAN = 'Lock the plan';

/**
 * The button's word while the lock is going out — 6.1's busy shape.
 *
 * Its own word rather than the chips' `Saving…`, because nothing is being saved: the value is the
 * three slots and they are already recorded, and what is going out is an act.
 */
export const LOCKING = 'Locking…';

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

/**
 * §22.4's four, keyed by the union — **so a chip with no words does not compile.**
 *
 * A `Record` rather than a function per code, which is §1's split read the other way: not one of
 * these quotes a value, and that is the rule rather than a coincidence. **Each chip asks the
 * question its slot is about and names nothing** — the prototype's three were a weekday, a part
 * of day and one fixture venue, and *a chip naming Saturday is a chip that is wrong six days a
 * week*.
 *
 * **A chip posts words and changes nothing** (ADR-0144): filling the slot it asks about would
 * record an agreement nobody had yet.
 */
export const QUICK_CHIP: Readonly<Record<QuickChip, string>> = {
  where: 'Where shall we play?',
  day: 'Which day works?',
  hour: 'What time?',
  'on-my-way': 'On my way',
};

// ---------------------------------------------------------------------------
// The panel over the plan, on the screen where it is read
// ---------------------------------------------------------------------------

/**
 * **The panel, inverted** — §22.2, and the fourth of #368's eight corrections to the details
 * design.
 *
 * The design drew *No clock time yet — on purpose*, which **explains an absence**: it is a note
 * about a slot nobody has filled yet, and it goes away the moment somebody fills one. ADR-0145 §6
 * turned it round, and the sentence it names is true of a **complete** plan and not of an empty
 * one — a player looking at *Zabłocie Sport · Saturday · 18:00* inside an app may reasonably
 * assume the app did something about it. It did not. So the panel names the absence rather than
 * explaining one, and it is drawn whatever the three slots hold.
 *
 * **Drawn on the game screen and never in the room**, which is #366's own split: above a composer
 * it would be permanent chrome, and one panel has one home.
 *
 * The second sentence is the whole of what a plan **is** on this platform: a note between the
 * people on the court, changeable by any of them, with every change visible to all of them. It is
 * the reason the slots are read-only here and the way to change one is the chat door beneath.
 */
export const PLAN_PANEL = {
  title: 'Agreed between you — nothing is booked',
  body: 'Raketa does not hold courts. This is the note you are keeping between you: anybody here can change any of it, and everybody sees who changed what.',
} as const;

// ---------------------------------------------------------------------------
// The slots, in the register a sentence uses
// ---------------------------------------------------------------------------

/**
 * The slots as a sentence names them — §22.6's three, and **not** the chip's three.
 *
 * `Where` labels a control; `where` is a word in a sentence, and *the day* and *the hour* carry
 * the article a list of them needs. Two tables rather than one because the two registers are
 * genuinely different, which is the same reason `SLOT_SHEET_TITLE` is not `SLOT_NAME` either.
 *
 * **It moved here from `nowPresentation.ts` when the checklist arrived**: the gloss names one slot
 * and the checklist names all three, so a table living with either of them would be the other
 * one's import — and this is the file that owns how a slot is spelled.
 */
export const SLOT_IN_A_SENTENCE: Readonly<Record<PlanSlot, string>> = {
  where: 'where',
  day: 'the day',
  hour: 'the hour',
};

/** The lead the gloss and the checklist share. One phrase, so the card and the screen agree. */
export const STILL_TO_AGREE = 'Still to agree';

/**
 * **What is still to agree, as a list** — the unfilled slots in slot order, joined §22.6's way.
 *
 * *`where and the hour`*, *`where, the day and the hour`*. **This is the one place the whole list
 * is printed**, which is what lets the card's gloss name only the next one and stay four words.
 *
 * The empty string for a plan with nothing left, which is a state this never draws: the checklist
 * picks the other sentence before it reaches here.
 */
export function slotsStillToAgree(plan: Plan | undefined): string {
  return sentenceList(unfilledSlots(plan).map((slot) => SLOT_IN_A_SENTENCE[slot]));
}

// ---------------------------------------------------------------------------
// The checklist — three lines, capped, in one order
// ---------------------------------------------------------------------------

/**
 * **What is true now.** The same three words on all four rungs, because *the rungs differ by the
 * clock and not by the arrangement* (§22.6).
 *
 * It is the line that explains why there is a plan on this screen at all: a challenge whose
 * line-up is still incomplete has an open conversation and **no plan**, so a plan existing is
 * itself the statement that every seat answered.
 */
export const EVERYBODY_SAID_YES = 'Everybody said yes.';

/** The second line where the three slots are full. Never the gloss's shorter phrase. */
export const NOTHING_IS_LEFT_TO_AGREE = 'Nothing is left to agree.';

/**
 * **The checklist — three lines, capped, in one order**: what is true now, what is still to agree,
 * what it moves (§22.6, [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §5.3).
 *
 * **The third line is cited rather than written**, and the citation is the point: `worthLine` is
 * `features/games`' built and tested sentence, and it is *the whole of what survives ADR-0143 §8's
 * refusal* of a forecast block on this screen. Writing a fourth sentence about what a game is
 * worth would be this deck's second opinion about a fact that feature owns — so the caller reads
 * it from there and hands it over, and a `GameKind` this build cannot read drops the line and
 * leaves the other two standing.
 *
 * **Capped at three** by there being exactly three: every line the design drew was about an owner,
 * a booking or a part of the day, and ADR-0144 and ADR-0145 §2 deleted all three.
 */
export function checklistLines(
  plan: Plan | undefined,
  worth: string | undefined,
): readonly string[] {
  const list = slotsStillToAgree(plan);

  return [
    EVERYBODY_SAID_YES,
    list === '' ? NOTHING_IS_LEFT_TO_AGREE : `${STILL_TO_AGREE}: ${list}.`,
    worth,
  ].filter((line): line is string => line !== undefined);
}

// ---------------------------------------------------------------------------
// What the read-only plan announces
// ---------------------------------------------------------------------------

/** The lead of the plan's one spoken name, so a listener knows what the three values are. */
export const PLAN_SPOKEN_LEAD = 'The plan.';

/**
 * **The three read-only tags as one accessibility element** — §24.5's own spelling:
 * *`The plan. Where, Zabłocie Sport. Day, Saturday. Hour, 18:00.`*
 *
 * One element because they are **one fact in three parts with no action**, which is §20.1
 * unchanged and the reason `Tag` was chosen over `Chip` for them in the first place. The chips in
 * the room are three elements because each of them is a way to change something; nothing here is.
 *
 * **Each slot is named even where its value is drawn instead**, because a listener hears three
 * values in a row and has nothing to attach them to — the same argument `slotChipName` makes one
 * surface over, with a comma rather than a colon: this is prose and the chip's is a control's
 * name. The place is spoken **whole**, comma and court and all (§20.4).
 */
export function planTagsName(plan: Plan | undefined): string {
  const said = PLAN_SLOTS.map((slot) => `${SLOT_NAME[slot]}, ${spokenSlotValue(plan, slot)}.`);

  return [PLAN_SPOKEN_LEAD, ...said].join(' ');
}
