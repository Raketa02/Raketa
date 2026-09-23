/**
 * **The intro's box, as the step draws it** — the label, the placeholder, the counter, the
 * hint, the rule, and the refusal under the box — for the two screens that take the line:
 * the onboarding step, and the You tab's *Intro*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §6).
 *
 * What the line does is the caller's: the step writes the draft as typed, the tab holds one.
 * What is refused is `intro`'s, read by the caller off its own line and handed here as the
 * sentence — the step hands the two shape refusals it pre-empts, the tab hands those and the
 * third the server answered with, drawn in the same place from the same table.
 *
 * ## The cap is drawn as a refusal rather than as a `maxLength`
 *
 * `WhereField`'s argument, one feature over, and it holds here: a `maxLength` swallows the
 * tail of a paste, and a shortened line is one the person who typed it believes they wrote
 * whole — in front of every stranger who reads it. So the box takes everything, the counter
 * keeps counting past a hundred, the sentence under the box says what is wrong, and the
 * caller's control stays shut until it is not. The box grows to a few lines so a hundred
 * characters can be read back whole, and the return key **dismisses the keyboard rather than
 * breaking the line** — a line break is the second shape refusal, and the ordinary way of
 * producing one should not produce it. A pasted one still can, and is refused under the box
 * the same way.
 */

import { StyleSheet, Text, View } from 'react-native';

import { TextField, theme } from '@/shared/ui';

import { introLength } from '../domain/intro';

import {
  INTRO_FIELD_HINT,
  INTRO_FIELD_LABEL,
  INTRO_PLACEHOLDER,
  INTRO_RULE,
  introCounter,
  spokenIntroCounter,
} from './introPresentation';

/**
 * How many lines the box may grow to before it scrolls.
 *
 * A hundred characters is two lines on the deck card at the mock's size and three in this
 * box at the value role, so three is where a line at the cap can be read back whole. One
 * more than that is room for the overrun the counter is there to show.
 */
const INTRO_LINES = 4;

export interface IntroFieldProps {
  /** The line as typed, untrimmed — what the box shows. */
  readonly written: string;
  readonly onChangeText: (text: string) => void;
  /** The sentence under the box, where the line is refused; nothing where it is not. */
  readonly refusal: string | undefined;
}

export function IntroField({ written, onChangeText, refusal }: IntroFieldProps) {
  // The count is of the line as the cap reads it — trimmed — and not of the box: the spaces
  // around a line are not part of it, and a counter that said `104 / 100` beside an open
  // control would be arguing with the rule it is there to show.
  const length = introLength(written.trim());

  return (
    <>
      <TextField
        label={INTRO_FIELD_LABEL}
        placeholder={INTRO_PLACEHOLDER}
        value={written}
        onChangeText={onChangeText}
        growTo={INTRO_LINES}
        // Return dismisses the keyboard. A line break is a refusal, and the key that would
        // ordinarily insert one should not be the key that produces it.
        submitBehavior="blurAndSubmit"
        // Prose a person writes, not an identifier: the platform's own correction and
        // capitalisation stay on, and there is nothing on a phone's saved-values list that
        // is a sentence about somebody.
        autoComplete="off"
        accessibilityHint={INTRO_FIELD_HINT}
        {...(refusal === undefined ? {} : { error: refusal })}
      />

      {/* Right-aligned under the box, in the number role — every figure is mono and
          tabular, which is what keeps `9 / 100` and `10 / 100` from shifting the line. Spoken
          as a count rather than as a fraction, because `/` is not a word. */}
      <Text style={s.counter} accessibilityLabel={spokenIntroCounter(length)}>
        {introCounter(length)}
      </Text>

      {/* The rule, once, before the refusal that enforces it. */}
      <View style={s.rule}>
        <Text style={s.smallPrint}>{INTRO_RULE}</Text>
      </View>
    </>
  );
}

const s = StyleSheet.create({
  counter: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.muted,
    textAlign: 'right',
  },
  rule: { paddingTop: theme.space.xs },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
});
