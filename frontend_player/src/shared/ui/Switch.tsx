/**
 * The switch — [6.12](../../../docs/design-system.md#612-the-switch).
 *
 * A mode a player turns on and off, and the only control in Part 6 that carries `checked`
 * on one. [6.11](../../../docs/design-system.md#611-the-tick-box) is explicitly *"a claim a
 * player either makes or does not"* and says in as many words that it is not a switch;
 * [6.3](../../../docs/design-system.md#63-segmented-control) picks one of several and
 * [6.2](../../../docs/design-system.md#62-chip--the-filter-pill) narrows what is already on
 * screen. None of the three is a setting that can be flipped back, which is what a swap mode
 * is, so this is a new section rather than a fourth spelling of an existing one.
 *
 * ```
 * row     height 44, control + words together — THE TOUCH SURFACE
 * track   40 x 23, radius pill · line2 off · ink on
 * knob    18 circle, inset 2,5 · night off · surface on
 * pressed opacity .7, over either state
 * ```
 *
 * **The knob changes colour and the reason is contrast, not decoration.** The prototype drew
 * a white knob at both ends of the travel, and against its unchecked `line` track that is
 * **1,30:1** — a control whose only moving part is invisible in half its states, which is the
 * failure [Part 13](../../../docs/design-system.md#part-13--accessibility) is a list about.
 * The knob takes the value that reads on the bed it is standing on: `night` on `line2` is
 * 11,36:1 and `surface` on `ink` is 17,50:1, both well clear of 1.4.11's 3:1 for a graphical
 * object. That is Rule C's argument applied to a mark rather than to text, and the ratios are
 * derived in `Switch.test.tsx` rather than typed here.
 *
 * **The state is carried by the knob's position before it is carried by anything else** —
 * a shape, which is what Part 13 asks for, and which is why the two fills are allowed to be
 * the fill inversion [6.8](../../../docs/design-system.md#68-the-availability-grid) already
 * uses rather than a second on-colour.
 *
 * **One consumer**: *Show me to new people* on the You tab ([#799](https://github.com/Rakieta02/Rakieta/issues/799),
 * which renamed #778's *Show me in General*). It asked for one thing the first spelling did not have,
 * a prop rather than a second control:
 *
 * - **`door`** — a switch standing in a card of door rows (5.5 as amended, the You tab) takes the
 *   door row's lead square with its glyph, its rhythm, its title and line, and its divider from the
 *   second row on — `DOOR_ROW`, the door row's own table — so its title starts at the edge every
 *   title above it does. The track stands where a door row's chevron would.
 *
 * **`onDark` and `accessibilityLabel` are unbuilt since #799** (6.12 keeps them specified): both were
 * for the Rankings card of a player hidden from General — the dark card's repaint, and *Show me in
 * General* named over the drawn *Hidden from General* — and that card went with the switch
 * (ADR-0204 §2). The next switch on dark builds them again from 6.12.
 *
 * **There is no disabled switch.** Nothing asks for one, and
 * [6.1](../../../docs/design-system.md#61-button)'s rule is that this app never draws a
 * pressable-looking control that refuses — the ceiling on the photo row is a fact of the
 * layout rather than a greyed button, and a mode with nothing to switch is a row that is not
 * on screen.
 *
 * **The words are the caller's and the accessible name is the label alone.** A switch
 * announces its state through `checked`, so a description repeated into the name would be
 * the double announcement 6.8 hides its column heads to avoid; the description is drawn and
 * merged into this one element, and what the mode *does* is said by the controls it changes.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { DOOR_ROW, RowLead, type DoorRowGlyph } from './DoorRow';
import { theme } from './theme';

const geometry = theme.size.switch;

/** The travel, and the inset that produces it — arithmetic, not a fourth measured number. */
const INSET = (geometry.height - geometry.knob) / 2;
const TRAVEL = geometry.track - geometry.knob - INSET * 2;

export interface SwitchProps {
  /** The mode, in the caller's words. This alone is the accessible name. */
  readonly label: string;
  /** One line under the label, drawn and never announced separately. */
  readonly description?: string;
  readonly checked: boolean;
  readonly onChange: (checked: boolean) => void;
  /**
   * In a card of door rows (5.5): the door row's lead, with this glyph, its rhythm, title and line,
   * and its divider where `divided` — 5.5's `index > 0`, the first row in a card undivided.
   */
  readonly door?: { readonly glyph: DoorRowGlyph; readonly divided: boolean };
}

export function Switch({ label, description, checked, onChange, door }: SwitchProps) {
  return (
    <Pressable
      // `switch` rather than `button`, for 6.8's reason: the state is the point and the role
      // is what carries it (`the-words.md` 20.2 — *prefer the role that carries the state*).
      accessibilityRole="switch"
      accessibilityLabel={label}
      accessibilityState={{ checked }}
      onPress={() => onChange(!checked)}
      // Touch has no hover, so the pressed appearance is declared rather than inherited (6.6).
      style={({ pressed }) => [
        s.row,
        door === undefined ? undefined : DOOR_ROW.rhythm,
        door?.divided === true ? DOOR_ROW.divided : undefined,
        pressed ? s.rowPressed : undefined,
      ]}
    >
      {door === undefined ? null : <RowLead glyph={door.glyph} />}

      <View style={s.words}>
        <Text style={door === undefined ? [s.label, PAPER.label] : DOOR_ROW.title}>{label}</Text>
        {description === undefined ? null : (
          <Text style={door === undefined ? [s.description, PAPER.description] : DOOR_ROW.line}>
            {description}
          </Text>
        )}
      </View>

      <View style={[s.track, checked ? PAPER.trackOn : PAPER.trackOff]}>
        <View
          style={[
            s.knob,
            checked ? PAPER.knobOn : PAPER.knobOff,
            { transform: [{ translateX: checked ? TRAVEL : 0 }] },
          ]}
        />
      </View>
    </Pressable>
  );
}

/**
 * **The ground** — the knob takes the value that reads on the bed it is standing on, at both ends;
 * `Switch.test.tsx` derives every ratio from these. Paper only, since #799 (see the module note).
 */
const PAPER = StyleSheet.create({
  label: { color: theme.color.ink },
  description: { color: theme.color.muted },
  trackOff: { backgroundColor: theme.color.line2 },
  knobOff: { backgroundColor: theme.color.night },
  trackOn: { backgroundColor: theme.color.ink },
  knobOn: { backgroundColor: theme.color.surface },
});

const s = StyleSheet.create({
  row: {
    minHeight: geometry.row,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
  },
  rowPressed: { opacity: 0.7 },
  // `flex: 1`, so a long mode line wraps inside the row rather than pushing the control off
  // the gutter — 6.11's rule for the same reason.
  words: { flex: 1 },
  label: theme.type.rlValue,
  description: { ...theme.type.tiny, marginTop: theme.space.xxs },
  track: {
    width: geometry.track,
    height: geometry.height,
    borderRadius: theme.radius.pill,
    padding: INSET,
    flexShrink: 0,
  },
  knob: {
    width: geometry.knob,
    height: geometry.knob,
    borderRadius: geometry.knob / 2,
  },
});
