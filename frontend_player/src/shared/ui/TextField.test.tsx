/**
 * The text field — 6.13 — asserted through what a player and a screen reader can observe,
 * plus the arithmetic that has no query.
 *
 * Three things here are not reachable through a role or a name: the box's height at one line,
 * what it grows by, and the ceiling it stops at. That is the declared exception
 * `Switch.test.tsx` and `TickBox.test.tsx` both take — a control whose whole subject is a
 * number a screen cannot ask for.
 *
 * **The platform coverage here is the two Android properties, and nothing broader is claimed.**
 * The field takes no `Platform` branch — the facts it answers are style properties iOS ignores
 * — so running every case twice under a swapped `Platform.OS` would be the same run reported
 * twice. What Jest can assert is that the two properties are set, which is what makes the grown
 * box's arithmetic true on the platform that would otherwise break it. **A device is still
 * owed**: the keyboard, the focus and the grown box's scroll are settled on a simulator and an
 * emulator, and this file cannot stand in for them.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { createRef } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { inOrder } from '@/test-support/readingOrder';

import { TextField, type TextFieldProps } from './TextField';
import { theme } from './theme';

const LABEL = 'Where';
const LINE = theme.type.rlValue.lineHeight;
const ROW = theme.size.textField.row;

function draw(props: Partial<TextFieldProps> = {}) {
  render(<TextField label={LABEL} value="" onChangeText={() => undefined} {...props} />);
}

/** The input as React Native would draw it. */
function input(): TextStyle {
  return StyleSheet.flatten(screen.getByLabelText(LABEL).props.style as TextStyle);
}

/**
 * The box, found by the one property only it has.
 *
 * By shape rather than by index: the field wrapper and the box are both `View`s, and a
 * positional lookup starts measuring a different one the moment the tree gains a wrapper.
 */
function box(): ViewStyle {
  const styles = screen
    .UNSAFE_getAllByType(View)
    .map((node) => StyleSheet.flatten(node.props.style as ViewStyle));
  const found = styles.find((style) => style?.borderRadius === theme.radius.btn);
  if (found === undefined) throw new Error('no field box in the tree');
  return found;
}

/**
 * The whole field — label, box and message — which is the press surface.
 *
 * Found by its style and not by its position, for `box`'s reason and one more: the reveal
 * control is a second `Pressable` in this tree, so an index here would be answering a
 * question about whichever of the two React happened to render first.
 */
function field() {
  const found = screen
    .UNSAFE_getAllByType(Pressable)
    .find((node) => StyleSheet.flatten(node.props.style as ViewStyle)?.gap === theme.space.xxs);
  if (found === undefined) throw new Error('no field in the tree');
  return found;
}

/** Report a content height of `lines` lines, as the platform does after every keystroke. */
function types(lines: number) {
  fireEvent(screen.getByLabelText(LABEL), 'contentSizeChange', {
    nativeEvent: { contentSize: { width: 200, height: lines * LINE } },
  });
}

describe('what the field reports', () => {
  it('takes its accessible name from the label, and draws it', () => {
    draw();

    expect(screen.getByLabelText(LABEL)).toBeTruthy();
    expect(screen.getByText(LABEL)).toBeTruthy();
  });

  it('announces a failure and draws the refused border with it', () => {
    draw({ error: 'Say where' });

    expect(screen.getByRole('alert').props.children).toBe('Say where');
    expect(box().borderColor).toBe(theme.color.red);
  });

  it('draws no refused border when there is nothing wrong', () => {
    draw();

    expect(screen.queryByRole('alert')).toBeNull();
    expect(box().borderColor).toBe(theme.color.line);
  });
});

/**
 * **Where the sentence goes** — under the box, as every field in the app draws it, or on the
 * label's own row, which the sign-in stage asks for (#784, 6.13 as amended in Part 16). The row
 * is opt-in, so a field that does not ask keeps its message where it always was.
 *
 * Where a thing sits on the screen is not something a query can see, so this asks what can be
 * asked: whether the sentence is read before the box or after it.
 */
describe('where the failure is drawn', () => {
  const SENTENCE = 'Enter your email address.';

  /** Where the sentence sits against the box, in the order a screen reader meets them. */
  const order = () => inOrder(screen.toJSON(), [`alert:${SENTENCE}`, `box:${LABEL}`]);

  it('is under the box unless the caller asks otherwise', () => {
    draw({ error: SENTENCE });

    expect(order()).toEqual([`box:${LABEL}`, `alert:${SENTENCE}`]);
  });

  it('is on the label’s row when the caller asks, before the box', () => {
    draw({ error: SENTENCE, errorOnLabelRow: true });

    expect(order()).toEqual([`alert:${SENTENCE}`, `box:${LABEL}`]);
  });

  it('still announces itself and still draws the refused border there', () => {
    draw({ error: SENTENCE, errorOnLabelRow: true });

    expect(screen.getByRole('alert')).toBeTruthy();
    expect(box().borderColor).toBe(theme.color.red);
  });

  /**
   * A sentence too long for the row takes its own column and wraps inside it, right-aligned,
   * rather than being cut off: no `numberOfLines`, and a column that can shrink.
   */
  it('wraps a long sentence in its own column, right-aligned, rather than cutting it off', () => {
    draw({ error: SENTENCE, errorOnLabelRow: true });

    const sentence = screen.getByRole('alert');
    const style = StyleSheet.flatten(sentence.props.style as TextStyle);
    expect(sentence.props.numberOfLines).toBeUndefined();
    expect(style.textAlign).toBe('right');
    expect(style.flex).toBe(1);
    expect(style.color).toBe(theme.color.red);
  });

  it('draws the label alone on its row while nothing is wrong', () => {
    draw({ errorOnLabelRow: true });

    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByText(LABEL)).toBeTruthy();
    expect(box().borderColor).toBe(theme.color.line);
  });
});

/**
 * The reveal is the field's and not the screen's: a password box that cannot be read back is
 * the one place a typo costs a whole form, and two of them on one screen are two buttons both
 * called *Show* unless the name says which field it is about.
 */
describe('the reveal', () => {
  it('is offered only where the caller asked for one', () => {
    draw({ secureTextEntry: true });

    expect(screen.queryByLabelText(`Show ${LABEL.toLowerCase()}`)).toBeNull();
  });

  it('unmasks and remasks the field it is named for', () => {
    draw({ secureTextEntry: true, reveal: true });

    expect(screen.getByLabelText(LABEL).props.secureTextEntry).toBe(true);

    fireEvent.press(screen.getByLabelText(`Show ${LABEL.toLowerCase()}`));
    expect(screen.getByLabelText(LABEL).props.secureTextEntry).toBe(false);

    fireEvent.press(screen.getByLabelText(`Hide ${LABEL.toLowerCase()}`));
    expect(screen.getByLabelText(LABEL).props.secureTextEntry).toBe(true);
  });

  /** 6.6's dim, which this control was drawn with a value of its own before it arrived here. */
  it("dims by the system's pressed value and no other", () => {
    draw({ secureTextEntry: true, reveal: true });

    const control = screen
      .UNSAFE_getAllByType(Pressable)
      .find((node) => node.props.accessibilityRole === 'button');
    if (control === undefined) throw new Error('no reveal control in the tree');
    const pressed = StyleSheet.flatten(control.props.style({ pressed: true }) as ViewStyle);

    expect(pressed.opacity).toBe(0.7);
  });
});

/**
 * The box alone is 42 against 6.5's 44, and half of a grown box is padding a finger would
 * find nothing in. The field is the surface instead — 6.10, 6.11 and 6.12's answer to the
 * same arithmetic — which clears the minimum on geometry rather than on a `hitSlop`.
 */
describe('the touch surface', () => {
  it('moves the caret into the field from anywhere on it', () => {
    const ref = createRef<TextInput>();
    render(<TextField ref={ref} label={LABEL} value="" onChangeText={() => undefined} />);
    if (ref.current === null) throw new Error('the field kept no input to focus');
    const focus = jest.spyOn(ref.current, 'focus');

    fireEvent.press(field());

    expect(focus).toHaveBeenCalled();
  });

  it('clears the minimum by its own geometry, with no slop granted', () => {
    draw();

    const reachable = theme.type.flab.lineHeight + theme.space.xxs + ROW;

    expect(reachable).toBeGreaterThanOrEqual(theme.size.minTouch);
    expect(field().props.hitSlop).toBeUndefined();
  });

  /**
   * A wrapper that announced itself would be read before the box it wraps, and the box
   * already carries the name, the value and the role.
   */
  it('is not an element of its own', () => {
    draw();

    expect(field().props.accessible).toBe(false);
  });
});

/** One line, capped by the caller's `maxLength` — the plan's *where*. */
describe('the one-line shape', () => {
  it('is one line, and is not asked to measure anything', () => {
    draw({ maxLength: 120 });

    expect(screen.getByLabelText(LABEL).props.multiline).toBeFalsy();
    expect(screen.getByLabelText(LABEL).props.onContentSizeChange).toBeUndefined();
    expect(screen.getByLabelText(LABEL).props.maxLength).toBe(120);
    expect(input().height).toBeUndefined();
    expect(box().minHeight).toBe(ROW);
  });
});

/** A single line that grows to a cap — the composer. */
describe('the growing shape', () => {
  it('starts at the height of the one-line box', () => {
    draw({ growTo: 4 });

    // The box is its padding plus one line, which is the one-line row and not a second
    // number: this arithmetic is what keeps the two shapes the same control.
    expect(input().height).toBe(LINE);
    expect((box().paddingVertical as number) * 2 + LINE).toBe(ROW);
  });

  it('grows one line at a time', () => {
    draw({ growTo: 4 });

    types(2);
    expect(input().height).toBe(2 * LINE);

    types(3);
    expect(input().height).toBe(3 * LINE);
  });

  it('stops at the cap the caller set and scrolls from there', () => {
    draw({ growTo: 4 });

    types(9);

    expect(input().height).toBe(4 * LINE);
  });

  it('comes back down when the value does', () => {
    draw({ growTo: 4 });

    types(3);
    types(1);

    expect(input().height).toBe(LINE);
  });

  /**
   * The value is fitted into the ceiling rather than counted into it, so a text setting that
   * makes a line taller than `LINE` costs a line of room instead of miscounting one. A count
   * would read this 40pt value — two lines at 125% — as two and a half, and round it to three.
   */
  it('takes the height it is given rather than guessing at a line count', () => {
    draw({ growTo: 4 });

    fireEvent(screen.getByLabelText(LABEL), 'contentSizeChange', {
      nativeEvent: { contentSize: { width: 200, height: 2.5 * LINE } },
    });

    expect(input().height).toBe(2.5 * LINE);
  });

  /**
   * Android draws font padding above and below every line, so a line box is taller than
   * `lineHeight` and the box would reach its ceiling early; it also centres a multiline value
   * where iOS tops it. Both properties are Android's and iOS ignores them, which is why they
   * are set unconditionally — a `Platform` branch here would be a branch with one live arm.
   */
  it('measures a line as a line on the platform that would not', () => {
    draw({ growTo: 4 });

    expect(input().includeFontPadding).toBe(false);
    expect(input().paddingVertical).toBe(0);
    expect(input().textAlignVertical).toBe('top');
  });
});

describe('the geometry', () => {
  /**
   * The field and the button under it are the same control height. Derived rather than typed
   * twice: 6.13 is entitled to state its own height, and the day the two disagree is the day
   * a form goes visibly crooked with nothing failing.
   */
  it('is a button tall at one line', () => {
    expect(theme.size.textField.row).toBe(theme.size.btnXl);
  });

  it('reads the label as a form label, because a field is a control you operate', () => {
    draw();

    const label = StyleSheet.flatten(
      screen.UNSAFE_getAllByType(Text).find((node) => node.props.children === LABEL)?.props
        .style as TextStyle,
    );

    expect(label.fontFamily).toBe(theme.type.flab.fontFamily);
    expect(label.fontSize).toBe(theme.type.flab.fontSize);
  });
});

/**
 * **The stage's look** (6.13 as amended 2026-11-08, #784): the sign-in stage's boxes as its mocks
 * draw them — a grey sentence-case label, a 48pt box holding a 14pt value a gutter in from each
 * side, and a sentence-case **Show** — opt-in, so every other field keeps 6.13's own look. What it
 * changes is the drawing; the name, the reveal and the refusal are the field's as ever.
 */
describe('the stage’s look', () => {
  function labelStyle(): TextStyle {
    return StyleSheet.flatten(
      screen.UNSAFE_getAllByType(Text).find((node) => node.props.children === LABEL)?.props
        .style as TextStyle,
    );
  }

  it('draws the label in muted sentence case, where 6.13 draws it uppercase in ink', () => {
    draw({ stage: true });

    const label = labelStyle();
    expect(label.fontFamily).toBe(theme.type.rlLabel.fontFamily);
    expect(label.fontSize).toBe(theme.type.rlLabel.fontSize);
    expect(label.color).toBe(theme.color.muted);
    expect(label.textTransform).toBeUndefined();
    expect(label.letterSpacing).toBeUndefined();
  });

  it('is the stage’s control height, with the value a gutter in from the box’s edge', () => {
    draw({ stage: true });

    expect(box().minHeight).toBe(theme.size.stage.control);
    expect(input().minHeight).toBe(theme.size.stage.control);
    expect(input().paddingHorizontal).toBe(theme.space.lg);
    expect(input().fontSize).toBe(theme.type.stageValue.fontSize);
    expect(input().fontFamily).toBe(theme.type.stageValue.fontFamily);
  });

  it('says Show and Hide in sentence case, and still names the field it reveals', () => {
    draw({ stage: true, secureTextEntry: true, reveal: true });

    const word = screen.getByText('Show');
    expect(StyleSheet.flatten(word.props.style as TextStyle).textTransform).toBeUndefined();
    fireEvent.press(screen.getByLabelText(`Show ${LABEL.toLowerCase()}`));
    expect(screen.getByText('Hide')).toBeTruthy();
  });

  it('keeps 6.13’s own look unless asked', () => {
    draw();

    expect(labelStyle().textTransform).toBe('uppercase');
    expect(box().minHeight).toBe(theme.size.textField.row);
  });
});
