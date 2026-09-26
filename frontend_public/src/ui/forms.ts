/**
 * **What a form shows after a submission.** A server action answers with **codes, never
 * sentences**: the refusal's code under the field it names, or one code for the form as a whole.
 * The backend's codes and the site's local checks speak the same vocabulary, so one table per
 * feature turns either into the sentence the page reads (ADR-0187 §6: decisions branch on the
 * code).
 */

import { COMMON_REFUSALS, FALLBACK_REFUSAL } from './copy';

export type Refusals<F extends string> = Partial<Record<F, string>>;

export interface FormState<F extends string> {
  /** Field → the code that field was refused with. */
  readonly refusals: Refusals<F>;
  /** A refusal that belongs to no field: the backend unreachable, an account already there. */
  readonly formRefusal: string | null;
}

export function blankForm<F extends string>(): FormState<F> {
  return { refusals: {}, formRefusal: null };
}

/** Place a refusal where it belongs: under the field it names when the form has one, or over it. */
export function placeRefusal<F extends string>(
  error: { readonly code: string; readonly field?: string },
  fields: readonly F[],
): FormState<F> {
  const named = fields.find((field) => field === error.field);
  return named === undefined
    ? { refusals: {}, formRefusal: error.code }
    : { refusals: { [named]: error.code } as Refusals<F>, formRefusal: null };
}

/** The sentence for a code: the feature's own, the common one, or the fallback. */
export function sentenceFor(
  code: string | null | undefined,
  table: Readonly<Record<string, string>>,
): string | null {
  if (code === null || code === undefined) return null;
  return table[code] ?? COMMON_REFUSALS[code] ?? FALLBACK_REFUSAL;
}

/** A text box's value from a posted form: `''` when it is absent or a file. */
export function formText(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === 'string' ? value : '';
}
