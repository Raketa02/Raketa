/**
 * The two controls the auth forms need that the design system does not specify.
 *
 * The placeholder button that used to live here **is gone**: `@/shared/ui`'s `Button` is
 * the spec'd one, and the auth screens use it. Two implementations of one primitive is
 * exactly how the prototype's copies drifted.
 *
 * These two remain because the system genuinely has no equivalent. A **text field** is
 * unspecified (ADR-0012 covers no form control), and a form-level failure banner is not a
 * `Note`: the five note variants are base, mint, coral, amber and info, and none of them
 * means *ended badly*. Adding a red note is a design-system change, in its own commit,
 * with its computed contrast — not something a screen invents on the way past.
 *
 * **The reveal control belongs to the field, not to the screen that uses it.** A password
 * box that cannot be read back is the one place where a typo costs a whole form: the
 * player retypes both halves and is told a third time that they do not match, with no way
 * to see which character is wrong. So `reveal` is a property of the field, the control
 * lives inside the box it operates on, and the accessible name says which field it is
 * about — two of them on one screen are otherwise two buttons both called *Show*.
 *
 * Every value still comes from the theme: a placeholder is not an excuse for a literal.
 */

import { forwardRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { theme } from '@/shared/ui/theme';

export interface AuthFieldProps extends Omit<TextInputProps, 'style'> {
  readonly label: string;
  /** Shown under the field and announced. Absent when the field is fine. */
  readonly error?: string;
  /**
   * Offer a show / hide control inside the box.
   *
   * Only meaningful on a field that starts masked, so it is opt-in rather than derived
   * from `secureTextEntry`: an app is entitled to a masked field nobody may read back,
   * and deriving it would take that decision away from the screen.
   */
  readonly reveal?: boolean;
}

/**
 * A labelled field.
 *
 * The label is a real `<Text>` bound to the input by `accessibilityLabel` rather than a
 * placeholder: a placeholder disappears the moment someone types, which leaves a screen
 * reader — and anyone who looked away — with an unlabelled box.
 */
export const AuthField = forwardRef<TextInput, AuthFieldProps>(function AuthField(
  { label, error, reveal = false, ...inputProps },
  ref,
) {
  const [focused, setFocused] = useState(false);
  /**
   * Held per field, and it starts masked every time the field is mounted.
   *
   * Revealing is a deliberate act on one box, so it is neither remembered across screens
   * nor shared between the two password boxes on the sign-up form — a player who unmasked
   * one to check a typo has said nothing about the other.
   */
  const [revealed, setRevealed] = useState(false);
  const masked = inputProps.secureTextEntry === true && !revealed;

  return (
    <View style={s.field}>
      <Text style={s.label}>{label}</Text>

      {/* The border lives on the box rather than on the input, because the reveal control
          sits inside the same box and a border drawn around the input alone would cut it
          out of the field it belongs to. */}
      <View style={[s.box, focused && s.boxFocused, error !== undefined && s.boxError]}>
        <TextInput
          ref={ref}
          {...inputProps}
          secureTextEntry={masked}
          accessibilityLabel={label}
          // State is carried by the border colour AND by the message below, never by
          // colour alone.
          style={s.input}
          placeholderTextColor={theme.color.muted}
          onFocus={(event) => {
            setFocused(true);
            inputProps.onFocus?.(event);
          }}
          onBlur={(event) => {
            setFocused(false);
            inputProps.onBlur?.(event);
          }}
        />

        {reveal ? (
          <Pressable
            accessibilityRole="button"
            // Named for the field it operates on: *Show* alone is two identical buttons
            // on a form with a password and a repeat password.
            accessibilityLabel={`${revealed ? 'Hide' : 'Show'} ${label.toLowerCase()}`}
            accessibilityState={{ expanded: revealed }}
            onPress={() => setRevealed((shown) => !shown)}
            hitSlop={theme.hit.btn}
            style={({ pressed }) => [s.reveal, pressed ? s.revealPressed : undefined]}
          >
            <Text style={s.revealWord}>{revealed ? 'Hide' : 'Show'}</Text>
          </Pressable>
        ) : null}
      </View>

      {error !== undefined ? (
        <Text style={s.fieldError} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
    </View>
  );
});

export interface AuthNoticeProps {
  readonly message: string;
}

/** A form-level failure — the ones that belong to no single field. */
export function AuthNotice({ message }: AuthNoticeProps) {
  return (
    <View style={s.notice} accessibilityRole="alert">
      <Text style={s.noticeText}>{message}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  field: {
    gap: theme.space.xxs,
  },
  label: {
    ...theme.type.flab,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  box: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.btn,
    // Height, not a fixed font size: the box grows with the OS text setting instead of
    // clipping at large accessibility sizes.
    minHeight: theme.size.btnXl,
  },
  boxFocused: {
    borderColor: theme.color.ink,
  },
  boxError: {
    borderColor: theme.color.red,
  },
  input: {
    ...theme.type.rlValue,
    color: theme.color.ink,
    flex: 1,
    paddingHorizontal: theme.space.md,
    minHeight: theme.size.btnXl,
  },
  // No fill and no border: it is a word inside a box that already has both, and a second
  // bordered surface inside the field would read as a second field.
  reveal: {
    justifyContent: 'center',
    paddingHorizontal: theme.space.md,
    alignSelf: 'stretch',
  },
  revealPressed: { opacity: 0.6 },
  revealWord: {
    ...theme.type.btn,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  fieldError: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
  notice: {
    backgroundColor: theme.color.redSoft,
    borderRadius: theme.radius.note,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.sm,
  },
  noticeText: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
});
