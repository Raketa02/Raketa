/**
 * The naming as a form: two boxes, one validation, one act — **without the screen around it.**
 *
 * Two screens drive it. The naming step asks *How should people see you?* once, at the
 * beginning, with empty boxes and a *Continue*; the You tab's *Name* row opens the same two
 * boxes pre-filled with a *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7 — *the same act, from a row*). Between the two, what the form does is identical: hold
 * what is typed, refuse a shape the schema refuses before a round trip, send the rest through
 * `useNamePlayer`, and put a refusal under the box it names. So it is here once, and each
 * screen owns its chrome, its button and where it goes afterwards.
 *
 * **The boxes are a draft over what the player holds**, the You tab's shape for every
 * control behind a row: each box shows what was typed into it, or the player's own answer
 * while nothing was. The draft is dropped the moment a save lands — after the re-read — so
 * the boxes then show **the server's re-read**, never what was typed, and *Save* is shut
 * behind `Saved` again with nothing to send.
 *
 * The server's `nickname_already_taken` is not special-cased: it arrives as a code with the
 * field it belongs to, and `NamingFields` puts it under that box through `errorUnderField`, as
 * sign-up's conflicts always were. The check is the server's on the press, never a lookup
 * while typing — a handle search is the enumeration ADR-0159 refuses.
 */

import { useState } from 'react';

import type { Naming } from '../domain/AuthenticatedUser';
import { namingSchema, validate, type FieldErrors } from '../schemas/authForms';

import { useNamePlayer } from './useAuthActions';

export interface NamingFormOptions {
  /** The boxes as they open. Empty on the step; the player's own on the tab. */
  readonly initial?: Naming;
  /**
   * The act landed and the player was re-read. Where to go next is the screen's: the step
   * leaves, and the tab's screen stays and says *Saved*.
   */
  readonly onSaved?: () => void;
}

export function useNamingForm({ initial, onSaved }: NamingFormOptions) {
  const held = { name: initial?.name ?? '', nickname: initial?.nickname ?? '' };
  /** What was typed into each box — `undefined` while it shows the player's own answer. */
  const [typedName, setName] = useState<string>();
  const [typedNickname, setNickname] = useState<string>();
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const name = typedName ?? held.name;
  const nickname = typedNickname ?? held.nickname;

  const naming = useNamePlayer();

  const submit = () => {
    const result = validate(namingSchema, { name, nickname });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    naming.mutate(result.values, {
      // The mutation has already written the recorded name into the cache and re-read the
      // player by the time this runs, so dropping the draft is what lets the boxes draw it.
      onSuccess: () => {
        setName(undefined);
        setNickname(undefined);
        onSaved?.();
      },
    });
  };

  return {
    name,
    setName,
    nickname,
    setNickname,
    /**
     * Whether either box differs from what it opened on — what the tab's *Save* is shut
     * behind, since a save of the boxes as they opened is a round trip for an answer in hand.
     * Always true on the step, whose boxes open empty and cannot be saved empty.
     */
    changed: name !== held.name || nickname !== held.nickname,
    /** The form's own refusals, raised against what is in the boxes now. */
    fieldErrors,
    /** The server's, where the press was refused. Which box it belongs under is the fields'. */
    error: naming.error,
    submit,
    pending: naming.isPending,
  };
}

export type NamingForm = ReturnType<typeof useNamingForm>;
