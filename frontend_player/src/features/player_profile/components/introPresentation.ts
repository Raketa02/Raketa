/**
 * The words the intro **step** says — the box, the counter, the two controls, the line of
 * small print — and the three sentences a refused line is answered with.
 *
 * ## The refusal says what to change, and never what was matched
 *
 * `intro_not_admitted` crosses with one coarse `reason` and no pattern
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
 * §2): the server never explains what it saw, so the client cannot either, and each sentence
 * below is an instruction rather than a diagnosis. The table is keyed by the domain's
 * `IntroRefusalReason` — a `Readonly<Record<…>>` — so a reason with no words does not
 * compile, and one sentence serves both the refusal the step pre-empts and the one the commit
 * brings back from the server.
 *
 * ## The rule is said up front, and that is the opposite of the photos step
 *
 * The photos step does not announce its check, because a check that is wrong about some
 * share of what it flags reads as a threat to the majority whose photo is fine. This one
 * announces the fence, for two reasons the photos step does not have: the rule is
 * deterministic and never wrong about a phone number, and the refusal lands **six screens
 * later**, at the commit — the one refusal the client cannot see coming is the one it costs
 * most to meet late. So the line under the box says who reads the intro and what to leave
 * out of it, once, in the same words the refusal would use.
 */

import { orOutOfDate } from '@/shared/vocabulary/outOfDate';

import { INTRO_CAP, type IntroRefusalReason } from '../domain/intro';

/** The drawn label over the box, and the box's accessible name. */
export const INTRO_FIELD_LABEL = 'Your intro';

/** One of the mocks' own lines, so the shape of an answer is legible before anything is typed. */
export const INTRO_PLACEHOLDER = 'Will travel for a hard game.';

/**
 * Who reads it and what to leave out — said once, under the box.
 *
 * The second sentence is the `contains_contact` refusal's, verbatim: a player who meets the
 * refusal at the commit is then reading a rule they were shown, not a new one.
 */
export const INTRO_RULE =
  'Other players read this on your card. Leave out phone numbers, emails, links and handles — people reach you in the chat.';

/** What the box is for, for whoever cannot see the counter or the small print. */
export const INTRO_FIELD_HINT = `One line, up to ${INTRO_CAP} characters. Optional.`;

/** The control that carries the line forward. */
export const INTRO_NEXT_LABEL = 'Next';

/**
 * The control that carries nothing forward.
 *
 * Visible whatever is in the box, because the step is optional and a player should learn
 * that by reading the screen rather than by finding *Next* open on an empty one. Pressing it
 * with a line half-written clears the line — *skip* means *no intro*, and a skip that sent
 * what happened to be in the box would be the one thing the word does not say.
 */
export const INTRO_SKIP_LABEL = 'Skip';

/** The way back to the step, offered beside a refusal the commit brought back. */
export const CHANGE_INTRO_LABEL = 'Change your intro';

/** What *Next* does, for whoever cannot see where it leads. */
export function introNextHint(nextTitle: string): string {
  return `Goes to ${nextTitle}`;
}

/** What *Skip* does — the same door, and the box left empty behind it. */
export function introSkipHint(nextTitle: string): string {
  return `Goes to ${nextTitle} with no intro`;
}

/**
 * The counter under the box: `42 / 100`.
 *
 * It counts **what the cap is read against** — the trimmed line, in code points — and not
 * the raw box, so it can never say `104 / 100` beside an open *Next*: the spaces around a
 * line are not part of it, and a counter that counted them would be arguing with the rule it
 * is there to show. It keeps counting past the cap rather than clamping — the box takes
 * everything and the sentence under it says what is wrong, so the overrun has to be visible
 * for the sentence to be actionable.
 */
export function introCounter(length: number): string {
  return `${length} / ${INTRO_CAP}`;
}

/** The same count, as a listener hears it. */
export function spokenIntroCounter(length: number): string {
  return `${length} of ${INTRO_CAP} characters`;
}

/** One sentence per reason. What to change; never what was matched. */
export const INTRO_REFUSAL_SENTENCE: Readonly<Record<IntroRefusalReason, string>> = {
  too_long: `Keep it under ${INTRO_CAP} characters.`,
  multiline: 'One line, no line breaks.',
  contains_contact:
    'Leave out phone numbers, emails, links and handles — people reach you in the chat.',
};

/**
 * The sentence for a reason, or the gap for a reason this build has no words for.
 *
 * A fourth reason added on the server arrives as a code the app recognises with a detail it
 * does not. The refusal is still drawn as the intro's, with the way back — and what it says
 * is the one sentence every surface says about a code it is too old to read.
 */
export function introRefusalSentence(reason: IntroRefusalReason | undefined): string {
  return orOutOfDate(reason === undefined ? undefined : INTRO_REFUSAL_SENTENCE[reason]);
}
