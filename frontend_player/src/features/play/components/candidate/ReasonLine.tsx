/**
 * One line under the fit pill, saying **why this person**.
 *
 * The words are `reasonPresentation`'s and `livenessPresentation`'s, and which of them a card
 * gets is `reasonSelection`'s: this file draws a string and decides nothing. That split is the
 * point — *what a sentence may say* is a rule about the register (**a reason line states its
 * evidence's facts and never grades them**), and *which sentences survive* is a rule about
 * what the card already renders. Neither is a drawing question.
 *
 * **A concern is the same shape in the opposite tone.** §7's concerns are *"the opposite
 * claim about the same term"*, and §20.3 appends them to the same list of lines the reasons
 * are in — so they are one component with a variant rather than two files that would drift
 * apart on a line height. The colour is never the carrier: §7's sentences state their own
 * polarity — *A wide level gap — the game may be one-sided* — which is what
 * [Part 13](../../../../../docs/design-system.md#part-13--accessibility)'s *never colour
 * alone* requires, and the two tag terms that do not are a gap §20.12 books rather than one
 * this component papers over with a tint.
 *
 * **There is no empty row.** §G5 records the prototype *"rendering a blank line next to the
 * fit pill"*, and the fix is upstream: `selectReasons` returns `hidden` and the card draws
 * nothing at all. A component that rendered an empty string would put the bug back one layer
 * down, where the selection could no longer see it.
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

/** A reason, or the opposite claim about the same term. See the module note. */
export type ReasonLineVariant = 'reason' | 'concern';

export interface ReasonLineProps {
  readonly line: string;
  readonly variant?: ReasonLineVariant;
}

export function ReasonLine({ line, variant = 'reason' }: ReasonLineProps) {
  return (
    <Text style={[s.line, TONE[variant]]} numberOfLines={2}>
      {line}
    </Text>
  );
}

const s = StyleSheet.create({
  line: { ...theme.type.tiny },
});

/** Amber is *reversible, not yet wrong*, which is exactly what a concern claims. */
const TONE = StyleSheet.create({
  reason: { color: theme.color.muted },
  concern: { color: theme.color.amber },
});
