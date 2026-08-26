/**
 * The words on the Social tags step.
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
 * ## The numbers come from the server, and so do the sentences that quote them
 *
 * Nothing here writes 2 or 6. Both are served, the commit re-validates against the same
 * two, and a client that hardcoded either would eventually tell a player a rule the
 * backend has stopped enforcing.
 */

import type { SocialTagGroupId, SocialTagId } from '../domain/SocialTag';
import type {
  SocialTagSelectionBounds,
  SocialTagSelectionStanding,
} from '../domain/socialTagSelection';

import { stepEyebrow } from './socialStepPresentation';

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
 * app's layout rather than the choice on offer.
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
 * The step's eyebrow, carrying **the rule as well as the position**.
 *
 * The floor belongs here rather than only inside a disabled button's label: a player
 * should learn how many tags are wanted by reading the screen, not by being stopped by it
 * (story 18). The ceiling comes along because it is the same sentence and the alternative
 * is a player meeting it for the first time as a refusal.
 *
 * Before the bounds have arrived it is the plain step eyebrow — a range with a blank in it
 * would be a rule stated wrong rather than a rule not stated yet.
 */
export function socialTagsEyebrow(bounds: SocialTagSelectionBounds | undefined): string {
  const position = stepEyebrow('tags');
  if (bounds === undefined) return position;
  return `${position} · Pick ${bounds.minimum} to ${bounds.maximum}`;
}

/**
 * What the continue control says.
 *
 * A blocked control names what is missing rather than merely being grey (story 17), and it
 * counts down as tags are picked, so the rule is legible from the control itself.
 */
export function socialTagsContinueLabel(standing: SocialTagSelectionStanding): string {
  if (standing.kind === 'ready') return 'Continue';
  return standing.missing === 1
    ? 'Pick 1 more tag to continue'
    : `Pick ${standing.missing} tags to continue`;
}

/**
 * The **title** of what a refused seventh press says — the sentence under it is the
 * screen's, because it names a control the player is looking at.
 *
 * It states the ceiling as a number rather than as "too many": the player pressed a chip
 * and the screen did not move, and a refusal that does not say what the limit is leaves
 * them pressing it again.
 */
export function socialTagCeilingTitle(bounds: SocialTagSelectionBounds): string {
  return `${bounds.maximum} tags is the most`;
}
