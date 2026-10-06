/**
 * The words on the gender step — including **the one sentence the record requires be said.**
 *
 * These are copy and not evidence: re-wording anything here makes nothing that was true
 * yesterday false, and no version identifier travels with the answer. What is not merely
 * copy is that *something* saying the mutuality cost is shown at the moment of setting — the
 * rule that decides when is `gender.reachOf`, and that is where the obligation lives.
 *
 * ## Why the warning exists at all
 *
 * The preference is a **mutual** gate
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 * Narrowing it does not only filter what a player sees; it also hides them from the
 * excluded side entirely, including from people who searched for anybody. That is the whole
 * difference between this and a dating filter, and it is the half a player would never
 * guess — the visible half is the one they asked for. **Learning it from an empty inbox is
 * not acceptable**, so the screen says it at the moment of the press.
 *
 * ## And why the label is not a euphemism
 *
 * The engine's third refusal is that it never produces something it cannot explain in one
 * sentence, and a softened label here would be the product being embarrassed about a
 * question it decided to ask. The words below are plain on purpose.
 */

import type { Gender, GenderPreference, PreferenceReach } from '../domain/gender';

/** Above the first control: whose answer this is. */
export const GENDER_HEADING = 'About you';

/** Above the second: what it is a preference *over*, said before any option is read. */
export const PREFERENCE_HEADING = 'Who we should match you with';

/**
 * What the platform does with both answers, said **before either is given**.
 *
 * It is the honest scope note this step needs: a player asked a question about themselves is
 * entitled to know what is done with the answer, and *never shown on your profile* is the
 * part that is least guessable.
 *
 * It sits at the top of the screen rather than between the two controls. A player deciding
 * whether to answer at all is deciding it **before** they press anything, so a reassurance
 * underneath the control they have already used is a reassurance that arrived late — and it
 * covers the preference below as much as the answer above, which it could not claim to do
 * from between them.
 */
export const GENDER_SCOPE =
  'We use this only to match you with other players. It is never shown on your profile or ' +
  'shared with other players.';

const GENDER_LABEL: Readonly<Record<Gender, string>> = {
  woman: 'Woman',
  man: 'Man',
  'prefer-not-to-say': 'Prefer not to say',
};

export function genderLabel(gender: Gender): string {
  return GENDER_LABEL[gender];
}

/**
 * What choosing *prefer not to say* costs, said where it is chosen.
 *
 * It is a real cost — that answer matches an unconstrained search and never a narrowed one —
 * and the record is explicit that framing it honestly is unsolved. So this says what
 * happens and does not editorialise about it: no *unfortunately*, no nudge back toward
 * answering, and nothing implying the answer is a lesser one.
 */
export const PREFER_NOT_TO_SAY_COST =
  'You will still be matched — but only with players who have not narrowed who they play with.';

const PREFERENCE_LABEL: Readonly<Record<GenderPreference, string>> = {
  any: 'Anyone',
  'women-only': 'Women only',
  'men-only': 'Men only',
};

export function preferenceLabel(preference: GenderPreference): string {
  return PREFERENCE_LABEL[preference];
}

/**
 * The mutuality cost, in the words of the side that stops being able to reach this player.
 *
 * **Both directions in one sentence**, because only saying the first half is what makes
 * these filters feel unsafe to the people they exist for: *you will not see men* is the
 * half a player asked for, and *men will not see you* is the half that decides whether
 * their inbox is quiet next week.
 *
 * `undefined` when nothing is narrowed — there is no cost to state, and a reassurance in
 * its place would be a screen talking about a consequence that does not exist.
 */
export function reachNote(reach: PreferenceReach): string | undefined {
  if (reach.kind === 'unconstrained') return undefined;
  return reach.hidden === 'man'
    ? 'You will not be matched with men — and men will not see you at all, even if they are open to anyone.'
    : 'You will not be matched with women — and women will not see you at all, even if they are open to anyone.';
}

/** Said under the preference control: this is a setting, not a one-off. */
export const PREFERENCE_IS_DURABLE =
  'You can change this later in your preferences. It applies to every search.';

/**
 * Why the finish will not move, for whoever cannot see that it will not — **this step's own
 * reason, and only this one.** The finish is also closed for a part short of an answer an
 * earlier step asks for, and that sentence is `commitPresentation`'s: reaching for this one
 * there would ask a player for an answer about themselves they have already given.
 */
export const GENDER_FINISH_BLOCKED_HINT = 'Choose an answer about you to finish';
