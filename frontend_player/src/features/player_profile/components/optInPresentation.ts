/**
 * The words on the Proposals opt-in step — **frozen copy, and the version that names it**.
 *
 * This is the only file in the app whose sentences are evidence. Every other string here is
 * copy: re-word it, ship it, and nothing that was true yesterday becomes false. These
 * sentences are what a player agreed to, and `PROPOSALS_OPT_IN_COPY_VERSION` travels with
 * their answer into the consent record precisely so the agreement can be read back against
 * the words it was given against (`CONTEXT.md` — *Consent is evidenced, not asserted*).
 *
 * **Changing a sentence below is a new version, not an edit.** Bump the identifier, keep
 * the old one, and leave every answer already recorded pointing at the wording it was
 * actually shown. A silent re-word turns every standing yes into a record of something
 * nobody said. That has happened once: `v2` dropped the line under the title, so `v1` is
 * retired and retained below rather than overwritten.
 *
 * ## The two answers are buttons, and that changed no wording
 *
 * They were chips. A chip is a **filter** over content a player can already see (6.2), and
 * these are the two answers to the screen's only question — the one press that opens the
 * finish. Two full-width buttons say that; two pills in a row said *narrow this down*. The
 * labels, their order and the never-pre-ticked line are untouched, which is why the change
 * of control is not itself what bumped the version.
 *
 * ## The card was restructured from the source documents, and the reason is the rule
 *
 * The sources opened with a fourth promise — *you appear to compatible players in
 * matchmaking and the deck*. It is not here, and it must not come back: under this
 * product's rule **opting out stops the engine pushing, not the player existing**, so
 * appearing in search and matchmaking is not governed by this answer at all. A consent card
 * that promised it would be promising more than the switch delivers, and because the copy
 * is stamped into the record, the overclaim would be evidenced rather than merely shown.
 *
 * `OPT_IN_SCOPE` is the correction that keeps the card honest, and it is load-bearing: it
 * is the sentence that tells a player what saying no leaves untouched, so that no is a
 * decision about proposals rather than a decision about being seen at all.
 *
 * ## There is no third control
 *
 * Two answers and a finish. No skip, no dismiss, no close, no decide-later — a player who
 * left through one of those would be neither opted in nor opted out, and somebody
 * downstream would have to guess. The guess is the thing consent exists to remove.
 *
 * ## What the version names is the screen, not this file
 *
 * The step's title and the line under it come from `socialStepPresentation`, because the
 * chrome of all seven steps is one table and splitting it would give this step two spellings
 * of its own name. A player reads them on the same screen as the card, so
 * `optInPresentation.test.ts` pins them alongside everything below — what the version
 * identifier names is what was *shown*, wherever the string happened to be declared.
 *
 * The note that used to sit beside the finish, saying the commit was not built yet, was
 * deliberately outside the pin and has been deleted rather than re-worded, exactly as this
 * file said it would be. What replaced it lives in `commitPresentation` — what finishing
 * does, what is still wanted, and what a failed commit says — and it stays outside the pin
 * for the same reason: none of it is part of any agreement. It describes the state of a
 * setup flow, it is shown conditionally, and versioning it would be recording a build
 * detail as evidence.
 */

/**
 * The identifier stamped into the consent record beside the answer.
 *
 * Not the words themselves: the copy is the client's and is never stored server-side
 * (`copy_version` is a 1–64 character identifier on the wire).
 */
export const PROPOSALS_OPT_IN_COPY_VERSION = 'proposals-opt-in.v2';

/**
 * **Retired, and kept.** The first wording ever shown to anybody. It differed from `v2` in
 * one line: under the title it also read *Whether the platform may put games in front of
 * you*, which `v2` drops — the card below already says what a yes means, and a step whose
 * whole subject is one question does not need the question paraphrased above it.
 *
 * Nothing stamps this any more and nothing should. It is here because an answer already
 * recorded against it points at *these* words, and a version identifier with no record of
 * what it named is a consent record that evidences nothing. **Delete it and the earlier
 * agreements become unreadable.**
 */
export const PROPOSALS_OPT_IN_COPY_V1 = 'proposals-opt-in.v1';

/**
 * The chrome line, which replaces the plain *step 7 of 7* rather than joining it.
 *
 * The step's own position is already in the sentence — *before finishing* is where a player
 * is — and the line's job here is to say that this one question is the whole of what is
 * left, so that a consent question does not read as one more form to get through.
 */
export const OPT_IN_EYEBROW = 'The one thing we ask before finishing';

/** What the three promises below are conditional on, said before any of them. */
export const OPT_IN_PROMISE_HEADING = 'If you say yes';

/** One promise: what it is about, and what is actually being promised. */
export interface OptInPromise {
  readonly term: string;
  readonly detail: string;
}

/**
 * The three promises, in order — **what arrives, what the player still does, and how it
 * stops.**
 *
 * Three rather than the sources' four, and the missing one is the point (see above). What
 * is left is exactly the set this answer governs: a proposal may arrive, the player answers
 * every one of them by hand, and the whole thing is revocable from the profile — as
 * revocable as it was grantable.
 */
export const OPT_IN_PROMISES: readonly OptInPromise[] = [
  {
    term: 'You may receive',
    detail: 'a game we think fits, when your week and theirs overlap',
  },
  {
    term: 'You always answer',
    detail: 'every game by hand — nothing is ever confirmed for you',
  },
  {
    term: 'You can stop',
    detail: 'any time, from your profile',
  },
];

/** The correction. What saying no changes, and — the half that matters — what it does not. */
export const OPT_IN_SCOPE = 'Saying no changes only this. You stay findable in search either way.';

/** Said next to the two controls, because it is a claim about the controls themselves. */
export const OPT_IN_NEVER_PRE_TICKED = 'Never pre-ticked. Skipping is not consent.';

/**
 * What each answer calls itself.
 *
 * **Both name what they do**, rather than being a bare yes and no beside a question mark:
 * a control labelled *No* leaves the player working out what it is no to, and this is the
 * screen where that guess costs the most.
 */
export function optInAnswerLabel(accepted: boolean): string {
  return accepted ? 'Yes — suggest games' : "No — don't suggest games";
}

/** One answer, and the words on the control that gives it. */
export interface OptInAnswer {
  readonly accepted: boolean;
  readonly label: string;
}

/**
 * The two answers **in the order they are offered**, which is the approved copy's order and
 * not an incidental one.
 *
 * **No comes first.** The option a screen puts first is the one it reads as recommending,
 * and this is the question where the product must not be seen to lean. That makes the order
 * a copy decision rather than a layout one, which is why it is stated here beside the words
 * and pinned by the same test — a screen that mapped over a list of its own could reverse
 * it without anything noticing.
 */
export const OPT_IN_ANSWERS: readonly OptInAnswer[] = [
  { accepted: false, label: optInAnswerLabel(false) },
  { accepted: true, label: optInAnswerLabel(true) },
];

/** The finish, naming what is on the other side of it rather than the act of finishing. */
export const OPT_IN_FINISH_LABEL = 'Finish — show me players';

/**
 * Why the finish is closed, for whoever cannot see that it is.
 *
 * **This step's own reason, and only this one.** The finish is also closed for a part that
 * is short of an answer one of the five earlier steps asks for — an area, most of all — and
 * that sentence is `commitPresentation`'s, because it is about the commit rather than about
 * consent. Reaching for this one there would tell a player to choose yes or no when they
 * already have.
 */
export const OPT_IN_FINISH_BLOCKED_HINT = 'Choose yes or no above to finish';
