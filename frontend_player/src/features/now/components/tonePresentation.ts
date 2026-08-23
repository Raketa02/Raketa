/**
 * A tone, resolved to the two things that draw it.
 *
 * `UI` §A1.3: *"this is the only place tone becomes pixels."* The tone itself is
 * the client's — `ADR-0041` and `ADR-0072` put it in the copy table rather than on
 * the wire, so the server and the phone cannot disagree about whether a card is
 * urgent — and this is where it stops being a word.
 *
 * **`idle` is the delta's correction, applied.** `UI` writes it as
 * `rgba(255,255,255,.45)`, which is fine on the dark state card and ≈1,0:1 on the
 * light match card — so every `forming`, `played*` and `waitlisted` row drew a
 * blank dot. `deltas/native-kit.md` §4 makes it surface-aware; every card this
 * feature draws today is a light one, so `muted` is what it resolves to here, and
 * the dark surface gains its own row when a card lands on one.
 */

import { theme, type TagVariant } from '@/shared/ui';

import type { Tone } from '../domain/presentation';

export interface TonePresentation {
  /** The tag's fill and label colour. */
  readonly variant: TagVariant;
  /** The 6pt square beside the label. Decoration — the label always says it too. */
  readonly dot: string;
}

/** Total over the five tones. A sixth would fail to compile here first. */
export const TONE_PRESENTATION: Readonly<Record<Tone, TonePresentation>> = {
  good: { variant: 'ok', dot: theme.color.mint },
  watch: { variant: 'hot', dot: theme.color.coral },
  time: { variant: 'warn', dot: theme.color.amber },
  ended: { variant: 'bad', dot: theme.color.red },
  idle: { variant: 'base', dot: theme.color.muted },
};
