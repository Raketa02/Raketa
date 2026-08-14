/**
 * The two controls the auth forms need.
 *
 * **These are deliberately local to this feature, and deliberately not named `Button` or
 * `Input`.** The design system (ADR-0012) specifies no text field, and its button, card
 * and header primitives are built to spec in `shared/ui/` by the onboarding slice (#23).
 * Naming a placeholder `Button` here would guarantee two of them — which is exactly how
 * the prototype's copies drifted. When #23 lands its primitives, these go.
 *
 * Every value still comes from the theme: a placeholder is not an excuse for a literal.
 */

import { forwardRef, useState } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

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

export interface AuthButtonProps {
  readonly label: string;
  readonly onPress: () => void;
  readonly disabled?: boolean;
  /** Renders the label as the busy label and blocks presses. */
  readonly busy?: boolean;
  readonly busyLabel?: string;
}

export function AuthButton({
  label,
  onPress,
  disabled = false,
  busy = false,
  busyLabel,
}: AuthButtonProps) {
  const blocked = disabled || busy;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      // Disabled state reaches a screen reader as state, not as a colour change.
      accessibilityState={{ disabled: blocked, busy }}
      disabled={blocked}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [
        s.button,
        blocked && s.buttonBlocked,
        // No animation: press feedback is immediate, which is also what makes it
        // correct under reduced motion with no branch.
        pressed && !blocked && s.buttonPressed,
      ]}
    >
      <Text style={s.buttonLabel}>{busy ? (busyLabel ?? label) : label}</Text>
    </Pressable>
  );
}

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
  button: {
    minHeight: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.ink,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: theme.space.lg,
  },
  buttonBlocked: {
    backgroundColor: theme.color.muted,
  },
  buttonPressed: {
    backgroundColor: theme.color.night,
  },
  buttonLabel: {
    ...theme.type.btn,
    color: theme.color.paper,
    textTransform: "uppercase",
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
