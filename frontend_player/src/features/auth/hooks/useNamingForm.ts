/**
 * The naming as a form: one box, one validation, one act — **without the screen around it.**
 *
 * Two screens drive it. The naming step asks *How should people see you?* once, at the
 * beginning, with an empty box and a *Continue*; the You tab's *Nickname* row opens the same box
 * pre-filled with a *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7 — *the same act, from a row*; [ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md)
 * §3). Between the two, what the form does is identical: hold what is typed, refuse a shape the
 * schema refuses before a round trip, send the rest through `useNamePlayer`, and put a refusal
 * under the box. So it is here once, and each screen owns its chrome, its button and where it
 * goes afterwards.
 *
 * **The box is a draft over what the player holds**, the You tab's shape for every control
 * behind a row: it shows what was typed into it, or the player's own nickname while nothing was.
 * The draft is dropped the moment a save lands — after the re-read — so the box then shows **the
 * server's re-read**, never what was typed, and *Save* is shut behind `Saved` again with nothing
 * to send.
 *
 * The server's `nickname_already_taken` is not special-cased: it arrives as a code with the
 * field it belongs to, and `NamingFields` puts it under the box through `errorUnderField`, as
 * sign-up's conflicts always were. The check is the server's on the press, never a lookup
 * while typing — a handle search is the enumeration ADR-0159 refuses.
 */

import { useState } from 'react';

import type { Naming } from '../domain/AuthenticatedUser';
import { namingSchema, validate, type FieldErrors } from '../schemas/authForms';

import { useNamePlayer } from './useAuthActions';

export interface NamingFormOptions {
  /** The box as it opens. Empty on the step; the player's own on the tab. */
  readonly initial?: Naming;
  /**
   * The act landed and the player was re-read. Where to go next is the screen's: the step
   * leaves, and the tab's screen stays and says *Saved*.
   */
  readonly onSaved?: () => void;
}

export function useNamingForm({ initial, onSaved }: NamingFormOptions) {
  const held = initial?.nickname ?? '';
  /** What was typed into the box — `undefined` while it shows the player's own nickname. */
  const [typed, setNickname] = useState<string>();
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const nickname = typed ?? held;

  const naming = useNamePlayer();

  const submit = () => {
    const result = validate(namingSchema, { nickname });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    naming.mutate(result.values, {
      // The mutation has already written the recorded nickname into the cache and re-read the
      // player by the time this runs, so dropping the draft is what lets the box draw it.
      onSuccess: () => {
        setNickname(undefined);
        onSaved?.();
      },
    });
  };

  return {
    nickname,
    setNickname,
    /**
     * Whether the box differs from what it opened on — what the tab's *Save* is shut behind,
     * since a save of the box as it opened is a round trip for an answer in hand. Always true on
     * the step, whose box opens empty and cannot be saved empty.
     */
    changed: nickname !== held,
    /** The form's own refusals, raised against what is in the box now. */
    fieldErrors,
    /** The server's, where the press was refused. Whether it goes under the box is the fields'. */
    error: naming.error,
    submit,
    pending: naming.isPending,
  };
}

export type NamingForm = ReturnType<typeof useNamingForm>;
