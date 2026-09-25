'use client';

import { useState } from 'react';

import type { FormState, Refusals } from './forms';

/**
 * **What a form shows of its last answer while the desk carries on typing.** A field's refusal
 * goes the moment that field changes, and the form's own refusal goes at the first change of any
 * field: both were said about what was in the boxes then, not now. A new answer brings them all
 * back.
 */
export function useFormFeedback<F extends string>(state: FormState<F>) {
  const [answered, setAnswered] = useState(state);
  const [edited, setEdited] = useState<ReadonlySet<F>>(() => new Set());
  const [touched, setTouched] = useState(false);

  // A new answer: adjust during render, as React recommends over an effect.
  if (answered !== state) {
    setAnswered(state);
    setEdited(new Set());
    setTouched(false);
  }

  const refusals: Refusals<F> = {};
  for (const [field, code] of Object.entries(state.refusals) as [F, string | undefined][]) {
    if (code !== undefined && !edited.has(field)) refusals[field] = code;
  }

  return {
    refusals,
    formRefusal: touched ? null : state.formRefusal,
    /** Whether anything was typed since the last answer. */
    touched,
    edit(field: F) {
      setTouched(true);
      setEdited((previous) => (previous.has(field) ? previous : new Set(previous).add(field)));
    },
  };
}
