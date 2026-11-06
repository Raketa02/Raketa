/**
 * The button, per design-system 6.1.
 *
 * Six variants, four heights, and one rule that is easy to miss: **the primary button
 * is filled `coralInk` and brightens to `coral` when pressed** — the inverse of the
 * prototype, which put white 12pt text on `coral` at 3.89:1. Coral still reads as the
 * accent; the label is legible (Rule C).
 *
 * Press feedback is immediate rather than animated, which is also why nothing here
 * branches on reduced motion: there is no motion to reduce.
 *
 * `theme.color.surface` is the app's one white (design-system correction #1), so it is
 * what a label on a saturated fill uses. There is no separate `white` token, deliberately.
 *
 * **`settled` is a fourth variant and an amendment to 6.1** (added for the location step).
 * It is the button whose *state* is the message: the thing it asked for has been obtained,
 * and pressing it again would only obtain it a second time. Mint is the system's word for
 * *settled, safe, covered* (1.3), so it is the one colour that could carry it — and it is
 * `mintInk` rather than `mint` because Rule C forbids white on `mint` at 4.07:1. It
 * brightens to `mint` on press exactly as `primary` brightens to `coral`, for the same
 * reason and with the same momentary exception. **The colour is never the whole fact:** a
 * control that turns green must also change its words, and the screen that uses this is
 * responsible for that half.
 *
 * **A settled button that is shut keeps its fill, and its arrival is the one thing here that
 * moves** (amended 2026-09-18, for the You tab's *Save*s). The 40% dim says *not now* about
 * an action; on a settled button the fill *is* the fact, and a fact at 40% reads as half a
 * fact — so `Saved` under a draft that is the profile's own is drawn whole, and the words
 * (past tense) and `accessibilityState.disabled` carry the *nothing to press* half between
 * them. Arriving at `settled` from any other variant cross-fades the fill it came from into
 * the mint over one `motion.fade`: the fill it arrived from is drawn over the new one and
 * fades out, and never on the way back or on first mount, where the state simply is. Under
 * reduced motion it simply is too — nothing is carried by the fade that the fill and the
 * label do not both say.
 *
 * **`on-dark` is the sixth variant, and it was specified in 6.1 and unbuilt** until Play's
 * one-tap declaration needed it. It is 5.2's repaint read as a control: `onDarkFill` over the
 * dark card, a white label, and `onDarkFillPressed` under the finger — the two tokens the
 * theme already names *the on-dark button*. It exists here rather than as a shape copied into
 * the one feature that draws it, which is `README.md`'s whole rule about a second card.
 *
 * **`gloss` is a second line under the label**, and it arrived with the same caller: a column
 * of three near-synonymous answers — *Competitive*, *For fun*, *Either suits me* — where the
 * label alone does not say what choosing one means. A glossed button **aligns its two lines to
 * the start** rather than centring them, because two centred lines of different lengths read
 * as a caption rather than as a row, and it grows past `HEIGHT[size]` for the reason the label
 * already does: `minHeight`, never `height`.
 *
 * The gloss ink is a table like the label's and **adds no colour** (15.2). Hierarchy is
 * carried by the type role — `tiny` under `btn` — rather than by a second opacity nobody has
 * computed: on the dark card it takes 5.2's own `onDarkTiny`, on `secondary` the paper's
 * `muted`, and on the three saturated fills it is the label's own white, which is the only
 * ink Rule C has measured against them.
 *
 * **`volt` is a fifth variant and the one that does not have the others' shape** (added for
 * Play's *they want you* signal). Volt is a **fill anywhere and a stroke only on dark** (2.2):
 * as a foreground on paper it is ~1.3:1 and invisible, but `ink` on it is 13.96:1, so the
 * fill inverts exactly the problem the stroke has. Its label is therefore `ink` and never
 * white. Its press is **`opacity: .7`** rather than a second fill — the system's answer for a
 * pressed surface with no darker companion (6.6: chip, segment, availability cell, photo
 * tile, tick-box row) — because volt is already the brightest value in the palette, and a
 * seventh hex invented to satisfy *the variant's pressed fill* would be a colour added to
 * describe a press.
 *
 * **`arranging` is a seventh variant, and it is volt's shape a second time** (added for the Now
 * card's *Fill the seat*, [#429](https://github.com/Raketa02/Raketa/issues/429) F1). The card's
 * tag carries a stage dot in `arranging` — *the game is still in the players' hands* — and the
 * door under it was the settled green, which said the opposite of the errand it named. The
 * theme's own note on the colour said *nothing writes on a 6pt dot*; a button is the first thing
 * that does, and the arithmetic is volt's: white on it is 2,48:1 and fails, `ink` on it is
 * 7,05:1, so the label is `ink` and never white. Its press is `opacity: .7` for volt's own
 * reason — the colour has no darker companion, and one invented to describe a press would be a
 * hex added for nothing. It is drawn on the dark card and nowhere else, where the theme fences
 * the colour.
 *
 * **`shape` is a seventh option and it is not a variant**
 * ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2). 4.2's rule is *the chip — the only true pill*, and every button is a 10pt rounded
 * rectangle; the yes screen's two doors are pills, and the record opens that one exception on
 * this screen rather than adding a second primitive. It is a shape and not a variant because
 * it changes the corner and nothing else: *Open the chat* is the `volt` button in a pill and
 * *Later* the `onDark` one, each with its own fill, label and press exactly as above. The
 * default is 4.2's corner, so nothing that exists changes, and the next surface that wants a
 * pill reopens the record rather than reaching for the prop.
 *
 * **Members' friend pills reopened it** ([#753](https://github.com/Raketa02/Raketa/issues/753),
 * friends 1–2; [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking),
 * 2026-11-06): **+ Add** and **Accept** are the `dark` button in a pill at `sm`, on the right of a
 * row, because the mock draws them so and the tags beside them on the next rows are pills too — a
 * 10pt corner among them would read as a different kind of thing. **The Friends page draws the same
 * pills** ([#754](https://github.com/Raketa02/Raketa/issues/754), friends 3; Part 16 2026-11-06):
 * *+ Add friends* in its header, and a request row's **Accept** and **Cancel**.
 *
 * **`marks` are two drawn glyphs after the label, and they are not words**
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); Part 16, 2026-11-06). The record's
 * *Friend ✓ ▾* and *Request sent ▾* need a tick and a down-chevron, and Archivo ships no ✓
 * (`CLAUDE.md`), so they are Feather's `check` and `chevron-down`, in the label's own ink and at its
 * size, after it. **Never spoken**: the name is the label (or the caller's `accessibilityLabel`), and
 * a mark says nothing a sighted reader would read aloud. Two only, because two are asked for.
 */

import Feather from '@expo/vector-icons/Feather';
import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { useReducedMotion } from './overlay';
import { theme } from './theme';

export type ButtonVariant =
  'primary' | 'dark' | 'secondary' | 'settled' | 'volt' | 'arranging' | 'onDark';

/**
 * 32 tertiary-in-card · 34 default · 40 screen action · 42 the primary action on a
 * result screen. All four clear the 44pt reachable minimum once `hit.btn` is applied.
 */
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

/** 4.2's 10pt corner, or the chip's pill — the yes screen's exception. See the module note. */
export type ButtonShape = 'rounded' | 'pill';

/** A drawn mark after the label — see the module note. */
export type ButtonMark = 'tick' | 'chevron';

const MARK_GLYPH: Readonly<Record<ButtonMark, 'check' | 'chevron-down'>> = {
  tick: 'check',
  chevron: 'chevron-down',
};

export interface ButtonProps {
  readonly label: string;
  /**
   * A second line under the label, saying what choosing this one means.
   *
   * **Not part of the accessible name.** A glossed button is one element whose name is the
   * caller's `accessibilityLabel`, and the gloss is the sighted half of what that name already
   * says — reading it out as well would say the same thing twice.
   */
  readonly gloss?: string;
  readonly onPress: () => void;
  readonly variant?: ButtonVariant;
  readonly size?: ButtonSize;
  /** Defaults to the rounded rectangle every button is. `pill` is one screen's, by record. */
  readonly shape?: ButtonShape;
  /** Glyphs drawn after the label, never spoken — see the module note. */
  readonly marks?: readonly ButtonMark[];
  readonly disabled?: boolean;
  /** Blocks presses and swaps the label. A busy button is not a disabled button. */
  readonly busy?: boolean;
  readonly busyLabel?: string;
  /**
   * Announced as `accessibilityState.selected`, for a button that is one of a set of
   * answers rather than an action.
   *
   * **Omitted unless set**, because *not selected* and *not a choice* are different facts
   * and every other button in the app is the second one. The drawing is the caller's, as
   * the chip's is: pass a `variant` that shows it, and the state here is the half a screen
   * reader gets.
   */
  readonly selected?: boolean;
  /** Defaults to `label`. Set it when the visible label needs context to make sense. */
  readonly accessibilityLabel?: string;
  readonly accessibilityHint?: string;
  readonly style?: StyleProp<ViewStyle>;
}

export function Button({
  label,
  gloss,
  onPress,
  variant = 'primary',
  size = 'md',
  shape = 'rounded',
  marks = [],
  disabled = false,
  busy = false,
  busyLabel,
  selected,
  accessibilityLabel,
  accessibilityHint,
  style,
}: ButtonProps) {
  const blocked = disabled || busy;
  // The accessible name follows what is drawn. A button reading "Starting…" while it
  // announces "Rate 1 sport" hands two different apps to two different players.
  const shown = busy ? (busyLabel ?? label) : label;
  const arrival = useArrivalAtSettled(variant);
  const words = (
    <Text style={[s.label, LABEL[variant]]} numberOfLines={1}>
      {shown}
    </Text>
  );

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? shown}
      accessibilityHint={accessibilityHint}
      // Disabled and busy reach a screen reader as state. The 40% fill below is the
      // sighted half of the same fact, never the whole of it.
      accessibilityState={{ disabled: blocked, busy, selected }}
      disabled={blocked}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [
        s.base,
        HEIGHT[size],
        SHAPE[shape],
        FILL[variant],
        gloss !== undefined ? s.glossed : undefined,
        pressed && !blocked ? PRESSED[variant] : undefined,
        // Never on `settled`: the fill is the fact, and the words say why it is shut.
        blocked && variant !== 'settled' ? s.blocked : undefined,
        style,
      ]}
    >
      {arrival === undefined ? null : (
        // The fill it arrived from, over the new one and on its way out. Under the label,
        // so the words are never what fades; inert, so it is never what is pressed.
        <Animated.View
          testID="button-arrival"
          pointerEvents="none"
          style={[
            StyleSheet.absoluteFill,
            SHAPE[shape],
            { backgroundColor: arrival.from, opacity: arrival.fade },
          ]}
        />
      )}
      <View style={[s.labelBox, gloss !== undefined ? s.labelBoxGlossed : undefined]}>
        {marks.length === 0 ? (
          words
        ) : (
          <View style={s.marked}>
            {words}
            {marks.map((mark) => (
              <Feather
                key={mark}
                name={MARK_GLYPH[mark]}
                size={theme.type.btn.fontSize}
                color={LABEL[variant].color}
                accessibilityElementsHidden
                importantForAccessibility="no"
              />
            ))}
          </View>
        )}
        {/* No `numberOfLines`: a gloss is a sentence, and at large OS text sizes it wraps
            rather than being clipped — the rule `minHeight` above is written for. */}
        {gloss !== undefined ? <Text style={[s.gloss, GLOSS[variant]]}>{gloss}</Text> : null}
      </View>
    </Pressable>
  );
}

/**
 * The arrival at `settled` — the module note's one motion.
 *
 * What it returns is the fill the button came from and the value that fades it out, or nothing
 * while there is nothing on its way out: on first mount, on every variant that is not
 * `settled`, on `settled` reached from `settled`, under reduced motion, and once the fade
 * has finished. The variant is compared during render rather than in an effect so the old
 * fill is on the first frame of the new state instead of one frame late, which would draw
 * the mint whole for a frame and then put the coral back over it.
 *
 * The value rests at 1 between arrivals, so the layer is opaque on the frame it mounts and the
 * fade runs 1 → 0; a variant that leaves `settled` mid-fade unmounts the layer, stops the
 * timing and puts the value back to rest.
 */
function useArrivalAtSettled(
  variant: ButtonVariant,
): { readonly from: string; readonly fade: Animated.Value } | undefined {
  const reduced = useReducedMotion();
  const fade = useRef(new Animated.Value(1)).current;
  const [seen, setSeen] = useState(variant);
  const [from, setFrom] = useState<ButtonVariant>();

  if (variant !== seen) {
    setSeen(variant);
    setFrom(variant === 'settled' && !reduced ? seen : undefined);
  }

  useEffect(() => {
    if (from === undefined) return;

    const timing = Animated.timing(fade, {
      toValue: 0,
      duration: theme.motion.fade,
      useNativeDriver: true,
    });
    timing.start(({ finished }) => {
      if (finished) setFrom(undefined);
    });

    return () => {
      timing.stop();
      fade.setValue(1);
    };
  }, [from, fade]);

  return from === undefined ? undefined : { from: FILL[from].backgroundColor, fade };
}

const s = StyleSheet.create({
  base: {
    paddingHorizontal: theme.space.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // `minHeight`, never `height`: at large OS text sizes the label has to grow the button
  // rather than be clipped by it.
  labelBox: { paddingVertical: theme.space.xs },
  // The label and its marks on one line, the marks a hair apart — a label's own word gap.
  marked: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  label: { ...theme.type.btn },
  // Two lines read from the start, so the box stretches rather than centring each of them on
  // its own width. See the module note.
  glossed: { alignItems: 'stretch' },
  labelBoxGlossed: { gap: theme.space.xxs },
  gloss: { ...theme.type.tiny },
  blocked: { opacity: 0.4 },
});

const SHAPE = StyleSheet.create({
  rounded: { borderRadius: theme.radius.btn },
  pill: { borderRadius: theme.radius.pill },
});

const HEIGHT = StyleSheet.create({
  sm: { minHeight: theme.size.btnSm },
  md: { minHeight: theme.size.btn },
  lg: { minHeight: theme.size.btnLg },
  xl: { minHeight: theme.size.btnXl },
});

const FILL = StyleSheet.create({
  primary: { backgroundColor: theme.color.coralInk },
  onDark: { backgroundColor: theme.color.onDarkFill },
  dark: { backgroundColor: theme.color.night },
  secondary: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
  },
  settled: { backgroundColor: theme.color.mintInk },
  volt: { backgroundColor: theme.color.volt },
  arranging: { backgroundColor: theme.color.arranging },
});

const PRESSED = StyleSheet.create({
  primary: { backgroundColor: theme.color.coral },
  onDark: { backgroundColor: theme.color.onDarkFillPressed },
  dark: { backgroundColor: theme.color.night2 },
  secondary: { backgroundColor: theme.color.line2 },
  settled: { backgroundColor: theme.color.mint },
  // Not a fill. Volt has no darker companion and does not get one invented for a press.
  volt: { opacity: 0.7 },
  // Volt's rule, for the same reason.
  arranging: { opacity: 0.7 },
});

const LABEL = StyleSheet.create({
  primary: { color: theme.color.surface },
  onDark: { color: theme.color.surface },
  dark: { color: theme.color.surface },
  secondary: { color: theme.color.ink },
  settled: { color: theme.color.surface },
  volt: { color: theme.color.ink },
  // `ink` and never white: 2,48:1 against 7,05:1 — the module note.
  arranging: { color: theme.color.ink },
});

/**
 * The gloss's ink, per variant — **the label's own colour wherever the system has no measured
 * secondary against that fill**, which is five of the seven.
 *
 * A `Record` over the union rather than a partial table: a variant with no gloss ink would
 * draw a second line in whatever `theme.type.tiny` inherits, which is nothing, and the failure
 * would be an invisible sentence rather than a red build.
 */
const GLOSS = StyleSheet.create({
  primary: { color: theme.color.surface },
  // 5.2's repaint: `tiny` inside a dark card is white at .68, 6.97:1 on night.
  onDark: { color: theme.color.onDarkTiny },
  dark: { color: theme.color.surface },
  secondary: { color: theme.color.muted },
  settled: { color: theme.color.surface },
  volt: { color: theme.color.ink },
  arranging: { color: theme.color.ink },
});
