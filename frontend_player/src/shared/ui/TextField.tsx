/**
 * The text field — [6.13](../../../docs/design-system.md#613-the-text-field).
 *
 * The app's control vocabulary has been missing this since sign-up: four boxes shipped on
 * the two auth screens and there was no primitive under them, so the geometry, the focus
 * border, the error rendering and the reveal all lived in a feature. Two more surfaces need
 * a field — the composer and the plan's *where* — and a third implementation is exactly the
 * drift a shared primitive exists to prevent.
 *
 * **Two shapes, one control.** A **one-line** field, capped by the caller's `maxLength`; and
 * a field that **grows a line at a time to a cap** and scrolls from there. They are the same
 * box, the same border, the same label and the same failure line — what differs is whether
 * the height is fixed at one line or counted from the value, which is a property of the
 * surface and not a second component.
 *
 * **The label is a real `<Text>` bound to the input by `accessibilityLabel`, never a
 * placeholder.** A placeholder disappears the moment somebody types, which leaves a screen
 * reader — and anyone who looked away — with an unlabelled box. It is always drawn: a field
 * whose surroundings already name it — a composer under a conversation header — wants the
 * name without the drawing, and that prop arrives with the surface that needs one.
 *
 * **The reveal control belongs to the field, not to the screen that uses it.** A password box
 * that cannot be read back is the one place where a typo costs a whole form: the player
 * retypes both halves and is told a third time that they do not match, with no way to see
 * which character is wrong. So `reveal` is a property of the field, the control lives inside
 * the box it operates on, and the accessible name says which field it is about — two of them
 * on one screen are otherwise two buttons both called *Show*.
 *
 * **The field is the control, not the input inside it.** 6.10, 6.11 and 6.12 all reach the
 * [44pt minimum](../../../docs/design-system.md#65-touch-targets) by making the whole row the
 * surface, and a field needs it twice over: the box alone is 42, and a grown box holds a value
 * 16 tall inside 13pt of padding, so half of what looks like the field would be dead to a
 * finger. Label, box and message are one target and pressing any of them moves the caret in —
 * which clears the minimum on **geometry** rather than on a `hitSlop`, exactly as the
 * availability cell and the tick box row do.
 *
 * **The cap is a number of lines and it is the caller's.** 6.10's posture: the radius slider
 * knows *"no step and no default, and no bound of its own"*. Neither surface that needs a
 * growing field has been drawn on a phone, and #338 §1 is that a number is written only for
 * what a device drew — so what is here is the arithmetic, and the ceiling arrives as a prop.
 * The ceiling is a **height**, `growTo` lines at the system text size, and the value is fitted
 * into it rather than counted into it: at a larger text setting fewer lines fit, which is the
 * right way round for a strip that must not grow until it has eaten the screen behind it.
 *
 * **Both platforms, and one of them needs telling.** Android draws font padding above and
 * below every line, so a line box is taller than `lineHeight` and the count below would grow
 * the box a line early; it also centres a multiline value where iOS tops it. Both fixes are
 * Android-only style properties that iOS ignores, so they are set outright rather than behind
 * a `Platform` branch with one live arm. `textContentType` (iOS) and `autoComplete` (Android)
 * are forwarded untouched and are both the caller's: neither platform reads the other's, so a
 * field that wants autofill passes both.
 */

import { forwardRef, useCallback, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { theme } from './theme';

/** One line of the value, and the step a growing field grows by. */
const LINE = theme.type.rlValue.lineHeight;

/**
 * The box at one line, and the padding that makes it so.
 *
 * Derived rather than declared: the growing shape carries its height on the input and its
 * breathing room on the box, and stating the padding as a fourth number is how the two
 * shapes end up different heights with nothing to notice it.
 */
const PAD_Y = (theme.size.textField.row - LINE) / 2;

export interface TextFieldProps extends Omit<
  TextInputProps,
  'style' | 'multiline' | 'onContentSizeChange'
> {
  /** The drawn label, and the accessible name. */
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
  /**
   * The most lines the field may grow to before it scrolls. `1` — the default — is a field
   * that never grows.
   */
  readonly growTo?: number;
}

export const TextField = forwardRef<TextInput, TextFieldProps>(function TextField(
  { label, error, reveal = false, growTo = 1, ...inputProps },
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
  /** The grown box's height in points, between one line and the ceiling. */
  const [grown, setGrown] = useState<number>(LINE);
  const masked = inputProps.secureTextEntry === true && !revealed;
  const grows = growTo > 1;

  /**
   * Held here as well as handed to the caller, because the box focuses it.
   *
   * A callback rather than `useImperativeHandle`, so the caller's ref is the input itself
   * and not a value this component has to promise exists. Memoised on the caller's ref:
   * React detaches and reattaches a ref callback whose identity changed, so a fresh one
   * every render would null this out and put it back on every keystroke.
   */
  const input = useRef<TextInput | null>(null);
  const holdInput = useCallback(
    (node: TextInput | null) => {
      input.current = node;
      if (typeof ref === 'function') ref(node);
      else if (ref !== null) ref.current = node;
    },
    [ref],
  );

  return (
    <Pressable
      style={s.field}
      // Not an element of its own: the input inside it already carries the name and the
      // role, and a button wrapped around a text box would be announced before it.
      accessible={false}
      onPress={() => input.current?.focus()}
    >
      <Text style={s.label}>{label}</Text>

      {/* The border lives on the box rather than on the input, because the reveal control
          sits inside the same box and a border drawn around the input alone would cut it
          out of the field it belongs to.

          No pressed appearance, and that is not an omission from 6.6: pressing this does not
          activate anything, it moves the caret here, and the answer to *did that land* is the
          focus border below and the keyboard coming up. */}
      <View
        style={[
          s.box,
          grows ? s.boxGrown : undefined,
          focused && s.boxFocused,
          error !== undefined && s.boxError,
        ]}
      >
        <TextInput
          ref={holdInput}
          {...inputProps}
          secureTextEntry={masked}
          accessibilityLabel={label}
          multiline={grows}
          // The value's own height, reported after every keystroke, taken as it comes and
          // held between one line and the ceiling. NOT divided into a line count and
          // rounded: a line is only `LINE` tall at the system text size, and at any other
          // one that division reads a wrapped second line as a third, or as none.
          onContentSizeChange={
            grows
              ? (event) => {
                  const measured = event.nativeEvent.contentSize.height;
                  setGrown(Math.min(Math.max(measured, LINE), growTo * LINE));
                }
              : undefined
          }
          // State is carried by the border colour AND by the message below, never by
          // colour alone.
          style={[s.input, grows ? [s.inputGrown, { height: grown }] : undefined]}
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
    </Pressable>
  );
});

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
    minHeight: theme.size.textField.row,
  },
  // The growing box holds the row's height as padding around a value that is one line tall
  // to start with, and top-aligns it: a value on its second line has a first line, and it
  // belongs at the top of the box rather than in the middle of it.
  boxGrown: {
    alignItems: 'flex-start',
    paddingVertical: PAD_Y,
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
    minHeight: theme.size.textField.row,
  },
  inputGrown: {
    minHeight: LINE,
    // Its own padding would be counted as content and grow the box a line early, and
    // Android's font padding would do the same on one platform only. Off, so a line
    // measures a line and the box's breathing room is the box's.
    paddingVertical: 0,
    includeFontPadding: false,
    textAlignVertical: 'top',
  },
  // No fill and no border: it is a word inside a box that already has both, and a second
  // bordered surface inside the field would read as a second field.
  reveal: {
    justifyContent: 'center',
    paddingHorizontal: theme.space.md,
    alignSelf: 'stretch',
  },
  // 6.6's value, not the .6 this control was drawn with in `features/auth/`: the system's
  // pressed dim is .7 everywhere, and a primitive is where a stray value stops being one
  // screen's and becomes the app's.
  revealPressed: { opacity: 0.7 },
  revealWord: {
    ...theme.type.btn,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  fieldError: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
});
