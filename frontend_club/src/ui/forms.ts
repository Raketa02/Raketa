/**
 * **What a form shows after a submission**, shared by every form on the site.
 *
 * A server action answers with **codes, never sentences**: the refusal's code under the field it
 * names, or one code for the form as a whole. The backend's own codes and the website's local
 * checks speak the same vocabulary, so one table per feature turns either into the sentence the
 * desk reads (ADR-0187 §6: decisions branch on the code).
 */

import { COMMON_REFUSALS, FALLBACK_REFUSAL } from './copy';

export type Refusals<F extends string> = Partial<Record<F, string>>;

export interface FormState<F extends string> {
  /** Field → the code that field was refused with. */
  readonly refusals: Refusals<F>;
  /** A refusal that belongs to no field: the backend unreachable, a spent link. */
  readonly formRefusal: string | null;
}

export function blankForm<F extends string>(): FormState<F> {
  return { refusals: {}, formRefusal: null };
}

export function hasRefusals<F extends string>(refusals: Refusals<F>): boolean {
  return Object.keys(refusals).length > 0;
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

/** Every field's refusal as its sentence, from the feature's table. */
export function sentencesFor<F extends string>(
  refusals: Refusals<F>,
  table: Readonly<Record<string, string>>,
): Partial<Record<F, string>> {
  const sentences: Partial<Record<F, string>> = {};
  for (const [field, code] of Object.entries(refusals) as [F, string | undefined][]) {
    const sentence = sentenceFor(code, table);
    if (sentence !== null) sentences[field] = sentence;
  }
  return sentences;
}

/** A text box's value from a posted form: `''` when it is absent or a file. */
export function formText(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === 'string' ? value : '';
}
