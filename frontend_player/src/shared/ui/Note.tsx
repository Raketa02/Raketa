/**
 * The note, per design-system 5.4 — a card with a 3pt left bar carrying the semantic.
 *
 * The 3 is `size.semanticBar` rather than a literal, because 5.4 as amended draws that bar a
 * second way: the challenge row wears it full height beside its content without becoming a
 * note. Two drawings of one number is what a token is for.
 *
 * Notes carry the reasoning, and they are the one place in this app a paragraph is
 * acceptable.
 *
 * Colour is picked by MEANING: base states, mint is settled, coral is the accent, amber
 * is reversible-but-not-yet-wrong, info explains rather than states. **The info note is
 * the only one with a glyph** — the shared `InfoGlyph`, which the anchored popover's mark
 * is the same object as.
 */

import { StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { InfoGlyph } from './InfoGlyph';
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

const s = StyleSheet.create({
  note: {
    borderWidth: 1,
    borderLeftWidth: theme.size.semanticBar,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
    gap: theme.space.xxs,
  },
  head: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  title: { ...theme.type.inlineTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.ink },
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
