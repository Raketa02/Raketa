/**
 * **Every sentence *Start playing*'s first step says** — the Adult attestation, given by an account
 * that already exists ([#517](https://github.com/Raketa02/Raketa/issues/517), ADR-0185 §4–§5). No
 * mock draws it. The box's claim and its refusal are sign-up's own (`ADULT_LABEL`,
 * `ADULT_ATTESTATION_MISSING`), because it is the same claim; the eyebrow and the busy word are the
 * naming step's, the step after it; what is here is the rest of the step around them.
 */

import { CONTINUE, NAMING_EYEBROW } from './namingPresentation';

/** The eyebrow over the title: the naming step's and welcome's word. */
export const START_PLAYING_EYEBROW = NAMING_EYEBROW;

/** The step's title — the row's words on the administrator's You tab, so the tap lands where it said. */
export const START_PLAYING_TITLE = 'Start playing';

/** Under the title: why the one question is asked. */
export const START_PLAYING_SUBLINE = 'Playing on Raketa is for adults only.';

/** The naming step's *Continue*, promising this step's next one. */
export const START_PLAYING_CONTINUE = {
  label: CONTINUE.label,
  busyLabel: CONTINUE.busyLabel,
  hint: 'Next, how people see you',
} as const;
