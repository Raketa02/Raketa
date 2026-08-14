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
 * Every value still comes from the theme: a placeholder is not an excuse for a literal.
 */

import { forwardRef, useState } from "react";
import { StyleSheet, Text, TextInput, View, type TextInputProps } from "react-native";

import { theme } from "@/shared/ui/theme";

export interface AuthFieldProps extends Omit<TextInputProps, "style"> {
  readonly label: string;
  /** Shown under the field and announced. Absent when the field is fine. */
  readonly error?: string;
}

/**
 * A labelled field.
 *
 * The label is a real `<Text>` bound to the input by `accessibilityLabel` rather than a
 * placeholder: a placeholder disappears the moment someone types, which leaves a screen
 * reader — and anyone who looked away — with an unlabelled box.
 */
export const AuthField = forwardRef<TextInput, AuthFieldProps>(function AuthField(
  { label, error, ...inputProps },
  ref,
) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={s.field}>
      <Text style={s.label}>{label}</Text>
      <TextInput
        ref={ref}
        {...inputProps}
        accessibilityLabel={label}
        // State is carried by the border colour AND by the message below, never by
        // colour alone.
        style={[s.input, focused && s.inputFocused, error !== undefined && s.inputError]}
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
    textTransform: "uppercase",
  },
  input: {
    ...theme.type.rlValue,
    color: theme.color.ink,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.btn,
    paddingHorizontal: theme.space.md,
    // Height, not a fixed font size: the box grows with the OS text setting instead of
    // clipping at large accessibility sizes.
    minHeight: theme.size.btnXl,
  },
  inputFocused: {
    borderColor: theme.color.ink,
  },
  inputError: {
    borderColor: theme.color.red,
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
