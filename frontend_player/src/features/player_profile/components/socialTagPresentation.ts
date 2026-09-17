/**
 * The words the tags **step** says — the rule it states, and the two refusals it makes — and
 * the one label the You tab's *Tags* adds, which is the step's floor wording with the verb
 * changed (ADR-0179 §2).
 *
 * The tags themselves are named in
 * [`@/shared/vocabulary/socialTagPresentation`](../../../shared/vocabulary/socialTagPresentation.ts):
 * Play draws the same nineteen labels inside a reason line, so the table is promoted and
 * this file holds what is genuinely this step's — sentences about a floor and a ceiling
 * this step is served and enforces
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1).
 *
 * ## The numbers come from the server, and so do the sentences that quote them
 *
 * Nothing here writes 2 or 6. Both are served, the commit re-validates against the same
 * two, and a client that hardcoded either would eventually tell a player a rule the
 * backend has stopped enforcing.
 */

import type {
  SocialTagSelectionBounds,
  SocialTagSelectionStanding,
} from '../domain/socialTagSelection';

import { stepEyebrow } from './socialStepPresentation';
import { SAVE, SAVED } from './youProfilePresentation';

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
  return `${position} · ${socialTagsRule(bounds)}`;
}

/** The rule alone — *Pick 2 to 6* — which the You tab cites under its own group title. */
export function socialTagsRule(bounds: SocialTagSelectionBounds): string {
  return `Pick ${bounds.minimum} to ${bounds.maximum}`;
}

/**
 * What a control shut under the floor says, counting down as tags are picked, so the rule is
 * legible from the control itself — and what it is shut *from*, as the verb.
 */
function shortLabel(missing: number, verb: string): string {
  return missing === 1 ? `Pick 1 more tag ${verb}` : `Pick ${missing} tags ${verb}`;
}

/**
 * What the continue control says.
 *
 * A blocked control names what is missing rather than merely being grey (story 17), and it
 * counts down as tags are picked, so the rule is legible from the control itself.
 */
export function socialTagsContinueLabel(standing: SocialTagSelectionStanding): string {
  if (standing.kind === 'ready') return 'Continue';
  return shortLabel(standing.missing, 'to continue');
}

/**
 * What the You tab's *Save* says — the step's floor wording with *to continue* become *to
 * save*, then *Save* while the draft differs from the profile and *Saved* while it does not.
 */
export function socialTagsSaveLabel(standing: SocialTagSelectionStanding, dirty: boolean): string {
  if (standing.kind === 'short') return shortLabel(standing.missing, 'to save');
  return dirty ? SAVE : SAVED;
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

/** The sentence under that title — it names a control the player is looking at. */
export const SOCIAL_TAG_CEILING_BODY =
  'Nothing changed. Remove one you have already picked to make room for another.';

/** The served vocabulary came back empty — a screen with nothing to pick from says so. */
export const NO_TAGS_AVAILABLE = 'No tags are available right now. Try again later.';
