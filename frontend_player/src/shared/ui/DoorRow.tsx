/**
 * The door row — a fact with a screen behind it, per design-system 5.5 as amended for the You
 * tab (Part 16, 2026-09-17; ADR-0179 §1).
 *
 * ```
 * lead      size.rowLead 28 × 28, paper2, radius.rowLead    a Feather glyph in night2 inside it
 * title     type.cardTitle, ink
 * line      type.tiny, muted — the LIVE line, drawn from a read and never a template
 * chevron   Feather chevron-right, muted, at the trailing edge
 * divider   1pt line2 top border, from the second row on — 5.5's `index > 0`
 * ```
 *
 * ## It is 5.5's row and not a menu item
 *
 * The You tab is a list of **facts** — what the platform holds about the player — and each
 * row is that fact's one-line summary with a door to the screen that shows or changes it. So it
 * takes 5.5's shape, the key-value line, rather than a settings menu's: the title is the key,
 * the live line is the value, and the chevron is the door. The lead square is the one new
 * element on that tab, and it is `paper2` rather than any accent so the accent stays with the
 * chevron's absence — nothing on the tab is coral.
 *
 * ## One element, spoken as *title, live line*
 *
 * The row is a `button`, and its name is the title and the line together, because a listener
 * who hears *Your week* and has to move once more to learn *10 slots ticked* has been handed
 * the key without its value. The glyph and the chevron are decoration: the title says what the
 * row is and the role says it opens something.
 *
 * ## The line may be absent, and the row still says what it is
 *
 * A live line is drawn from a read, and a read may not have landed yet — so the line is
 * optional, and a row without one is spoken as its title alone rather than as *title, nothing*.
 * What a row says while its read is on its way or has failed is `shared/errors`' `liveLine`,
 * the one answer for every row; this component draws what it is handed.
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/** A glyph name Feather actually ships. Not a `string`, and not behind a cast. */
export type DoorRowGlyph = keyof typeof Feather.glyphMap;

export interface DoorRowProps {
  readonly glyph: DoorRowGlyph;
  readonly title: string;
  /** The live line under the title — a fact off a read. Absent while there is none to draw. */
  readonly line?: string;
  readonly onPress: () => void;
  /** 5.5's `index > 0`. The first row in a card is undivided. */
  readonly divided?: boolean;
}

/** The spoken name: the title, and the live line where there is one. */
export function doorRowLabel(title: string, line: string | undefined): string {
  return line === undefined ? title : `${title}, ${line}`;
}

export function DoorRow({ glyph, title, line, onPress, divided = false }: DoorRowProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={doorRowLabel(title, line)}
      onPress={onPress}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <View style={s.lead}>
        <Feather
          name={glyph}
          size={theme.size.rowLeadGlyph}
          color={theme.color.night2}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      </View>

      <View style={s.words}>
        <Text style={s.title}>{title}</Text>
        {line === undefined ? null : <Text style={s.line}>{line}</Text>}
      </View>

      <Feather
        name="chevron-right"
        size={theme.size.tabIcon}
        color={theme.color.muted}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    // `space.sm` above and below a 28pt lead is 46pt, over 6.5's minimum by geometry.
    paddingVertical: theme.space.sm,
  },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  // 6.6: the press state for a row whose whole surface is the control.
  pressed: { opacity: 0.7 },
  lead: {
    width: theme.size.rowLead,
    height: theme.size.rowLead,
    borderRadius: theme.radius.rowLead,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Takes what the lead and the chevron leave, so a long live line wraps under the title
  // rather than pushing the chevron off the row.
  words: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
});
