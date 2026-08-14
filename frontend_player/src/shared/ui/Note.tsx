/**
 * The note, per design-system 5.4 — a card with a 3pt left bar carrying the semantic.
 *
 * Notes carry the reasoning, and they are the one place in this app a paragraph is
 * acceptable.
 *
 * Colour is picked by MEANING: base states, mint is settled, coral is the accent, amber
 * is reversible-but-not-yet-wrong, info explains rather than states. **The info note is
 * the only one with a glyph** — a serif italic *i*, because the information mark is a
 * symbol rather than text and the serif form is the one people recognise. It is the only
 * non-app family in the system.
 */

import { Platform, StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export type NoteVariant = 'base' | 'mint' | 'coral' | 'amber' | 'info';

export interface NoteProps {
  readonly children: ReactNode;
  readonly variant?: NoteVariant;
  readonly title?: string;
  /**
   * `alert` for a failure a player has to act on, so it is announced when it appears.
   * The default is no role: an explanatory note is read in document order like any prose.
   */
  readonly accessibilityRole?: 'alert';
}

export function Note({ children, variant = 'base', title, accessibilityRole }: NoteProps) {
  return (
    <View
      style={[s.note, SURFACE[variant]]}
      accessibilityRole={accessibilityRole}
      // An alert has to be **one** accessibility element, or the role announces nothing:
      // a View is not an accessibility element by default, so its children would be read
      // as ordinary text in document order — which is precisely the announcement the role
      // exists to replace. The other variants stay as flowing text on purpose.
      accessible={accessibilityRole === 'alert' ? true : undefined}
    >
      <View style={s.head}>
        {variant === 'info' ? <InfoGlyph /> : null}
        {title !== undefined ? <Text style={s.title}>{title}</Text> : null}
      </View>
      {typeof children === 'string' ? <Text style={s.body}>{children}</Text> : children}
    </View>
  );
}

/**
 * Decorative: the sentence beside it says the same thing, and a screen reader announcing
 * "i" before every explanation is noise.
 */
function InfoGlyph() {
  return (
    <View style={s.glyph} accessibilityElementsHidden importantForAccessibility="no">
      <Text style={s.glyphMark}>i</Text>
    </View>
  );
}

const s = StyleSheet.create({
  note: {
    borderWidth: 1,
    borderLeftWidth: 3,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
    gap: theme.space.xxs,
  },
  head: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  title: { ...theme.type.inlineTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.ink },
  glyph: {
    width: theme.size.infoGlyph,
    height: theme.size.infoGlyph,
    borderRadius: theme.size.infoGlyph / 2,
    backgroundColor: theme.color.info,
    alignItems: 'center',
    justifyContent: 'center',
  },
  glyphMark: {
    ...theme.type.tag,
    fontFamily: Platform.select({
      ios: theme.font.serif.ios,
      default: theme.font.serif.android,
    }),
    fontStyle: 'italic',
    color: theme.color.surface,
  },
});

const SURFACE = StyleSheet.create({
  base: {
    backgroundColor: theme.color.surface,
    borderColor: theme.color.line,
    borderLeftColor: theme.color.night,
  },
  mint: {
    backgroundColor: theme.color.mintSoft,
    borderColor: theme.color.mintLine,
    borderLeftColor: theme.color.mint,
  },
  coral: {
    backgroundColor: theme.color.coralSoft,
    borderColor: theme.color.coralLine,
    borderLeftColor: theme.color.coral,
  },
  amber: {
    backgroundColor: theme.color.amberSoft,
    borderColor: theme.color.amberLine,
    borderLeftColor: theme.color.amber,
  },
  info: {
    backgroundColor: theme.color.infoSoft,
    borderColor: theme.color.infoLine,
    borderLeftColor: theme.color.info,
  },
});
