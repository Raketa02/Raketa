/**
 * The words on a Social tag — the label, the name and the emoji.
 *
 * **The ids are the platform's and the labels are this app's.** The contract serves ids
 * and grouping only, precisely so a label can be re-worded without touching a single
 * stored profile — a tag id is permanent and persisted, and copy is not.
 *
 * The three tables are exhaustive by type. A further tag reaches this build through
 * `pnpm gen:api` and the mapper's own table; here, the missing key is what stops it
 * shipping as a chip with no words on it.
 *
 * ## A chip is drawn with an emoji and announced without one
 *
 * Twenty-seven chips of the same length in the same weight are a wall, and the emoji is what
 * lets a player find the one they meant by shape rather than by reading all of them. It is
 * **decoration**: `socialTagLabel` is what is drawn and `socialTagName` is what is spoken,
 * because a screen reader announcing "beer mug, stays for a drink" is reading the app's
 * layout aloud rather than the choice. Nothing is ever carried by the emoji alone — the
 * words are on the chip either way.
 *
 * ## Two callers, two shapes, and why that is not a third table
 *
 * The tag picker draws a chip. Play draws a **sentence over a pair** — *Both of you: 🏆
 * Plays to win, 🎯 Quiet and focused* — and a reason line is prose, where a chip is an
 * object. Prose takes `socialTagName`; the chip takes `socialTagLabel`. Both read the one
 * `LABEL` table, which is the whole point of the promotion
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §6.2, §18).
 *
 * The step-specific copy — the eyebrow, the continue control, the ceiling refusal — stayed
 * in `player_profile`: those sentences are about that step's rules and quote numbers only
 * that step is served.
 *
 * ## The row's own three words came last, and came for the same reason
 *
 * `socialTagChip`, its `· you too` marker and `NO_TAGS_IN_COMMON` are at the foot of this
 * file. They began on the competitive candidate card, where the tag row was the only thing
 * that drew them; they are here because the record sheet draws that row too
 * ([#373](https://github.com/Raketa02/Raketa/issues/373)) and the row is now one component
 * in `shared/ui`. A second spelling of the marker is exactly the drift the twenty-seven labels
 * were promoted to stop, one register down. What each surface **says about** a row still
 * belongs to that surface: the clauses a listener gets on a candidate card are
 * `features/play/components/playerCardPresentation`'s.
 */

import type { SharedTag } from './socialTagOverlap';
import type { SocialTagGroupId, SocialTagId } from './socialTags';

const LABEL: Readonly<Record<SocialTagId, string>> = {
  STAYS_FOR_A_DRINK: 'Stays for a drink',
  STRAIGHT_HOME_AFTER: 'Straight home after',
  TALKS_THROUGH_THE_MATCH: 'Talks through the match',
  SETTLES_UP_ON_THE_SPOT: 'Settles up on the spot',
  BOOKS_THE_NEXT_ONE: 'Books the next one',
  SHARES_A_LIFT: 'Shares a lift',
  STAYS_FOR_A_COFFEE: 'Stays for a coffee',
  UP_FOR_A_BITE_AFTER: 'Up for a bite after',
  KEEPS_IN_TOUCH: 'Keeps in touch',
  PLAYS_TO_WIN: 'Plays to win',
  LAUGHS_OFF_MISTAKES: 'Laughs off mistakes',
  ENCOURAGES_A_PARTNER: 'Encourages a partner',
  GENEROUS_ON_LINE_CALLS: 'Generous on line calls',
  QUIET_AND_FOCUSED: 'Quiet and focused',
  WARMS_UP_PROPERLY: 'Warms up properly',
  HAPPY_TO_SWAP_PARTNERS: 'Happy to swap partners',
  PATIENT_WITH_BEGINNERS: 'Patient with beginners',
  HAPPY_TO_SHARE_TIPS: 'Happy to share tips',
  BRINGS_THE_ENERGY: 'Brings the energy',
  HERE_TO_IMPROVE: 'Here to improve',
  HERE_TO_COMPETE: 'Here to compete',
  HERE_FOR_THE_EXERCISE: 'Here for the exercise',
  HERE_TO_MEET_PLAYERS: 'Here to meet players',
  HERE_FOR_A_REGULAR_GAME: 'Here for a regular game',
  HERE_TO_GET_BACK_INTO_IT: 'Here to get back into it',
  OPEN_TO_MEET_SOMEONE: 'Open to meet someone',
  NEW_IN_TOWN: 'New in town',
};

/**
 * One emoji per tag, chosen for what the words say and nothing else.
 *
 * Never a face where a face could be read as a judgement about the player, and never two
 * ids sharing one — the whole value of the glyph is that it tells two chips apart at a
 * glance.
 */
const EMOJI: Readonly<Record<SocialTagId, string>> = {
  STAYS_FOR_A_DRINK: '🍻',
  STRAIGHT_HOME_AFTER: '🚪',
  TALKS_THROUGH_THE_MATCH: '💬',
  SETTLES_UP_ON_THE_SPOT: '💸',
  BOOKS_THE_NEXT_ONE: '📅',
  SHARES_A_LIFT: '🚗',
  STAYS_FOR_A_COFFEE: '☕',
  UP_FOR_A_BITE_AFTER: '🍽️',
  KEEPS_IN_TOUCH: '📲',
  PLAYS_TO_WIN: '🏆',
  LAUGHS_OFF_MISTAKES: '😄',
  ENCOURAGES_A_PARTNER: '👏',
  GENEROUS_ON_LINE_CALLS: '🤝',
  QUIET_AND_FOCUSED: '🎯',
  WARMS_UP_PROPERLY: '🤸',
  HAPPY_TO_SWAP_PARTNERS: '🔄',
  PATIENT_WITH_BEGINNERS: '🤲',
  HAPPY_TO_SHARE_TIPS: '💡',
  BRINGS_THE_ENERGY: '🎶',
  HERE_TO_IMPROVE: '📈',
  HERE_TO_COMPETE: '🔥',
  HERE_FOR_THE_EXERCISE: '💪',
  HERE_TO_MEET_PLAYERS: '👋',
  HERE_FOR_A_REGULAR_GAME: '🔁',
  HERE_TO_GET_BACK_INTO_IT: '🌱',
  OPEN_TO_MEET_SOMEONE: '💘',
  NEW_IN_TOWN: '🧳',
};

/** What the chip is **drawn** with. */
export function socialTagLabel(tagId: SocialTagId): string {
  return `${EMOJI[tagId]} ${LABEL[tagId]}`;
}

/**
 * What the chip is **announced** as — the words alone.
 *
 * The emoji is decoration, and a screen reader reading its name out would be describing the
 * app's layout rather than the choice on offer. It is also what a **sentence** takes: a
 * reason line naming two tags is prose, and prose does not carry glyphs.
 */
export function socialTagName(tagId: SocialTagId): string {
  return LABEL[tagId];
}

/** The three headings, each naming what its group is *about* — all three about the game. */
const GROUP_HEADING: Readonly<Record<SocialTagGroupId, string>> = {
  AFTER_THE_MATCH: 'After the match',
  ON_THE_COURT: 'On the court',
  WHY_YOU_ARE_HERE: "Why you're here",
};

export function socialTagGroupHeading(group: SocialTagGroupId): string {
  return GROUP_HEADING[group];
}

/**
 * **The Social tag row's words** — the chip, its *you too* marker, and the amber sentence.
 *
 * The row is `socialTagOverlap`'s four answers; these are the four things they say
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)). Nothing here decides which tags are
 * shared, and nothing here re-words a tag: `socialTagLabel` and `socialTagName` are the
 * promoted table's, and a second spelling of twenty-seven labels is what the promotion existed to
 * prevent ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1).
 *
 * ## The chip is drawn with a glyph and a marker, and spoken as neither
 *
 * `socialTagLabel` carries the emoji because a wall of same-length chips is found by shape;
 * `socialTagName` is what a listener gets, because *"beer mug, stays for a drink"* is the app
 * reading its own layout aloud. The **marker** goes the other way and is the more interesting
 * half: `· you too` is drawn on the chip because the tint alone would be colour as the only
 * cue ([Part 13](../../../docs/design-system.md#part-13--accessibility)), and it is *not*
 * repeated per tag in the spoken name — the label groups the shared ones under one clause
 * instead, because a listener hearing *you too* six times is being read a table.
 *
 * **A shared chip can truncate its marker at the largest text sizes.** `Tag` is
 * `numberOfLines={1}` by design ([6.4](../../../docs/design-system.md#64-tag--the-status-pill)
 * — *a long state tag truncates rather than breaking the row*), and the longest label plus the
 * marker exceeds the card at roughly double the system size. The tint survives it and the
 * spoken name always carries the whole clause, so the fact is never lost; what is lost is the
 * second cue, for the reader who has asked for the largest type. Recorded rather than papered
 * over — fixing it means a wrapping tag, which is a change to the primitive and to 6.4.
 *
 * What a chip in the row is **drawn** with: the tag, and the marker where it is shared.
 */
export function socialTagChip(tag: SharedTag): string {
  const label = socialTagLabel(tag.id);
  return tag.shared ? `${label} · ${YOU_TOO_MARKER}` : label;
}

/** The two words, once. Re-worded here and nowhere else — the clause has its own phrasing. */
const YOU_TOO_MARKER = 'you too';

/**
 * The amber sentence, which **stands in the row's place** rather than beside it.
 *
 * The one claim this row makes, and the only state in which the subject's own tags are not
 * drawn: six untinted chips under a line saying none of them matched would be the card
 * answering a question nobody asked twice over, and the ticket puts the sentence *in the row's
 * place* in as many words. The tags are still a fact about their owner alone — they are read
 * in full on the surface that draws tags as tags, and the row's job here is the comparison.
 */
export const NO_TAGS_IN_COMMON = 'No tags in common';

/**
 * **How many tags two players share** — *6 things in common*, *1 thing in common* (the words §31.8,
 * §31.10): on a Same vibe tile and its sheet, and on the request card of someone found there. One
 * spelling for both features, beside the row's own *you too*, for the reason the marker has one.
 */
export function thingsInCommon(count: number): string {
  return count === 1 ? '1 thing in common' : `${count} things in common`;
}
