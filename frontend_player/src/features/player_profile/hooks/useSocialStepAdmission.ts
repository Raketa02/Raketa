/**
 * May this player be dropped straight onto this social step?
 *
 * **The decision is `admissionToStep`'s**, a pure rule with its own tests; this is the
 * wiring that acts on it. That is the same split the entry gate uses and the same one the
 * questionnaire's admission uses — a rule, a hook, and only the answer leaving the feature.
 *
 * **Entering happens here, and it happens in an effect** — unlike the questionnaire's
 * admission, which begins a pass during render because its chrome reads a position on the
 * very first one. Nothing on a step needs the draft to exist before it draws: the eyebrow
 * counts steps, and a part that has just been entered holds no answers anyway. So entering
 * waits for the render that decided to admit rather than happening inside it, which is what
 * keeps a redirect *into* step one from setting state while the step being left is still
 * rendering.
 *
 * **The answer is settled once per mount.** Entering changes the very thing the answer was
 * computed from, so re-deriving it every render would be reading the consequence of the
 * decision as though it were the input. Settling it also means the part ending elsewhere —
 * the commit, when it lands — cannot turn a mounted step into a redirect underneath the
 * player mid-tap.
 */

import { useEffect, useRef } from 'react';

import type { SocialStep } from '../domain/socialSteps';
import { admissionToStep } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

/** `start-over` means the first step — the part begins at its beginning or not at all. */
export type SocialStepAdmission = 'admit' | 'start-over';

export function useSocialStepAdmission(step: SocialStep): SocialStepAdmission {
  const draft = useProfileDraft((state) => state.draft);
  const enterIfAbsent = useProfileDraft((state) => state.enterIfAbsent);
  const settled = useRef<{ admission: SocialStepAdmission; entering: boolean }>();

  if (settled.current === undefined) {
    const admission = admissionToStep(step, draft);
    settled.current = {
      admission: admission.kind === 'start-over' ? 'start-over' : 'admit',
      entering: admission.kind === 'enter',
    };
  }
  const { admission, entering } = settled.current;

  useEffect(() => {
    if (!entering) return;
    // Conditional even here: two mounts of the door in one walk — a redirect landing on it
    // while a back navigation is arranging the same thing — must not produce two parts.
    enterIfAbsent();
  }, [entering, enterIfAbsent]);

  return admission;
}
