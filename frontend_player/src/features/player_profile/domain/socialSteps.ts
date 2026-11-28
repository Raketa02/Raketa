/**
 * The six steps of onboarding's **second part**, and the two boundaries around them.
 *
 * The part is one sequence and nothing else: no queue the player chose, no branch, no
 * length that depends on an answer. So the whole of "where does this step lead" is a
 * lookup in one ordered list, and it lives here rather than in six screens for the reason
 * `onboardingPass` gives about part one — a rule spread over the screens that obey it is a
 * rule the next screen is added without.
 *
 * ## The two boundaries are rules, not layout
 *
 * **Nothing is behind the first step.** Behind it is a rated Assessment's review, and *an
 * answer is revisable for as long as its run is, and no longer* — walking back into a
 * settled rating would break that invariant. It is the same clamp part one already
 * carries: `questionNavigation.standingPosition` pins its floor at position one. Two rules
 * at two boundaries, both hard, both for reasons the player never has to be told.
 *
 * **Nothing is in front of the last step.** What follows it is the profile commit, and a
 * commit is not a screen — so this list ends at the last question rather than growing a
 * seventh entry to hold the thing that ends the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 *
 * Moving between two steps costs nothing and writes nothing: every answer is held in the
 * client-side draft (`ProfileDraft`) until the commit, so back and forward are free in both
 * directions and neither reaches the network.
 */

import type { ProfileDraft } from './ProfileDraft';

/**
 * One step of the part, named for the decision it asks for.
 *
 * These names are the route segments as well, which is deliberate: `/location` is the screen
 * that asks for a Location area, and a second spelling of the same six things is how a route
 * and a rule come to disagree about which screen is which.
 */
export type SocialStep = 'tags' | 'intro' | 'photos' | 'availability' | 'location' | 'gender';

/**
 * The order, and the only one.
 *
 * **The intro straight after the tags** — *you've picked your tags; now say it in your own
 * words*
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
 * §5). The tags say what kind of player somebody is in the platform's words and the line is
 * the same question in theirs, so it follows them; and it comes before the photos, which is
 * the one step that reaches the device.
 *
 * **Gender sits with the other matching constraints and not with the tags**, which is the
 * one ordering decision that is not arbitrary. The tags step asks what kind of player
 * somebody is; the week and the area narrow who the platform will put in front of them, and
 * a preference over who they play with is one of those rather than another description of
 * themselves
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 *
 * **It is also last, and carries the finish.** The radius and the proposals question used to
 * follow it, and both left the part with the old loop's ranking — the only thing that read
 * them ([#582](https://github.com/Rakieta02/Rakieta/issues/582)). So the part ends on a question
 * every proposed game still reads, and nothing may come after the step whose answer opens
 * the commit.
 */
export const SOCIAL_STEPS: readonly SocialStep[] = [
  'tags',
  'intro',
  'photos',
  'availability',
  'location',
  'gender',
];

/** The next step, or `undefined` at the end of the part — where the commit takes over. */
export function stepAfter(step: SocialStep): SocialStep | undefined {
  return SOCIAL_STEPS[SOCIAL_STEPS.indexOf(step) + 1];
}

/**
 * The previous step, or `undefined` on the first — which is what "no back control" means,
 * expressed as the rule rather than as a prop a screen remembers to leave off.
 */
export function stepBefore(step: SocialStep): SocialStep | undefined {
  const at = SOCIAL_STEPS.indexOf(step);
  return at <= 0 ? undefined : SOCIAL_STEPS[at - 1];
}

/** Which step of how many — what the chrome says so a player knows these screens end. */
export interface StepPosition {
  /** 1-based. */
  readonly index: number;
  readonly total: number;
}

export function stepPosition(step: SocialStep): StepPosition {
  return { index: SOCIAL_STEPS.indexOf(step) + 1, total: SOCIAL_STEPS.length };
}

export type StepAdmission =
  /** The player is inside the part and this step is theirs to be on. Render it. */
  | { readonly kind: 'admit' }
  /** The door: no part is running, and arriving at the first step starts one. */
  | { readonly kind: 'enter' }
  /** A step in the middle with no part running. The part begins at its beginning. */
  | { readonly kind: 'start-over' };

/**
 * Whether a player may be dropped straight onto this step.
 *
 * **The part has one door, and it is the first step.** The draft is client-held and starts
 * empty, so a link naming step six would let a player commit a Player profile built from
 * five screens they never saw — with the tag selection and the week both missing, and
 * nothing having asked them for either. So a step in the middle admits only
 * a player who is already inside the part.
 *
 * **The absence of a draft is what "inside the part" is read from**, which is why entering
 * is explicit rather than implied by an empty one: *not in the part* and *in the part,
 * having answered nothing* are different situations and only one of them may continue.
 *
 * The three answers mirror `onboardingPass.admissionTo`, and for the same reasons — a rule
 * about where a player belongs, decided without a store, a router or a renderer.
 */
export function admissionToStep(step: SocialStep, draft: ProfileDraft | undefined): StepAdmission {
  if (draft !== undefined) return { kind: 'admit' };
  return stepBefore(step) === undefined ? { kind: 'enter' } : { kind: 'start-over' };
}
