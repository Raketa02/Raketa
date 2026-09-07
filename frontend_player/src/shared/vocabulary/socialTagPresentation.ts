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
 * Nineteen chips of the same length in the same weight are a wall, and the emoji is what
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
 */

import type { SocialTagGroupId, SocialTagId } from './socialTags';

const LABEL: Readonly<Record<SocialTagId, string>> = {
  STAYS_FOR_A_DRINK: 'Stays for a drink',
  STRAIGHT_HOME_AFTER: 'Straight home after',
  TALKS_THROUGH_THE_MATCH: 'Talks through the match',
  SETTLES_UP_ON_THE_SPOT: 'Settles up on the spot',
  BOOKS_THE_NEXT_ONE: 'Books the next one',
  SHARES_A_LIFT: 'Shares a lift',
  PLAYS_TO_WIN: 'Plays to win',
  LAUGHS_OFF_MISTAKES: 'Laughs off mistakes',
  ENCOURAGES_A_PARTNER: 'Encourages a partner',
  GENEROUS_ON_LINE_CALLS: 'Generous on line calls',
  QUIET_AND_FOCUSED: 'Quiet and focused',
  WARMS_UP_PROPERLY: 'Warms up properly',
  HERE_TO_IMPROVE: 'Here to improve',
  HERE_TO_COMPETE: 'Here to compete',
  HERE_FOR_THE_EXERCISE: 'Here for the exercise',
  HERE_TO_MEET_PLAYERS: 'Here to meet players',
  HERE_FOR_A_REGULAR_GAME: 'Here for a regular game',
  HERE_TO_GET_BACK_INTO_IT: 'Here to get back into it',
  OPEN_TO_MEET_SOMEONE: 'Open to meet someone',
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
  PLAYS_TO_WIN: '🏆',
  LAUGHS_OFF_MISTAKES: '😄',
  ENCOURAGES_A_PARTNER: '👏',
  GENEROUS_ON_LINE_CALLS: '🤝',
  QUIET_AND_FOCUSED: '🎯',
  WARMS_UP_PROPERLY: '🤸',
  HERE_TO_IMPROVE: '📈',
  HERE_TO_COMPETE: '🔥',
  HERE_FOR_THE_EXERCISE: '💪',
  HERE_TO_MEET_PLAYERS: '👋',
  HERE_FOR_A_REGULAR_GAME: '🔁',
  HERE_TO_GET_BACK_INTO_IT: '🌱',
  OPEN_TO_MEET_SOMEONE: '💘',
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
