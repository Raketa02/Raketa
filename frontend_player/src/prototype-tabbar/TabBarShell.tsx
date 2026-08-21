/**
 * PROTOTYPE — throwaway. See `tabs.ts`.
 *
 * The parts of the tab bar that are NOT under question, so every variant renders them
 * identically and the comparison is only ever about the glyph layer:
 *
 *   §B13  grid of 5, border-top 1px --line, background #fff, padding 7px 0 12px,
 *         column flex per tab, gap 4, label 8.5/600, selected colour --coral
 *   §D    `padding-bottom: 12` is hand-fitted with no safe-area — the spec's own
 *         recommendation is `12 + safeAreaBottom`, which is what this uses
 *   §B13  the Inbox badge is injected after the base render
 *
 * The badge is drawn EXACTLY as specified — white on `coral`, which is 3.89:1 and fails
 * AA. That is the spec's value, not a choice made here; it is left visible on purpose.
 */

import { type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui/theme';

import { TABS, TAB_LABEL_SIZE, type TabKey } from './tabs';

export type GlyphProps = { tabKey: TabKey; active: boolean; color: string };

export type TabBarShellProps = {
  active: TabKey;
  badge: number;
  onSelect: (t: TabKey) => void;
  /** Return null to render no glyph at all — that is variant B's whole argument. */
  renderGlyph: (p: GlyphProps) => ReactNode;
  /** The create tab is not a peer; each variant owns its treatment. */
  renderCreate: (p: { active: boolean }) => ReactNode;
  labelSize?: number;
};

export function TabBarShell({
  active,
  badge,
  onSelect,
  renderGlyph,
  renderCreate,
  labelSize = TAB_LABEL_SIZE,
}: TabBarShellProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[s.bar, { paddingBottom: 12 + insets.bottom }]}>
      {TABS.map((t) => {
        const isActive = active === t.key;
        const tint = isActive ? theme.color.coral : theme.color.muted;
        return (
          <Pressable
            key={t.key}
            style={s.tab}
            onPress={() => onSelect(t.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={
              t.key === 'msg' && badge > 0 ? `Inbox, ${badge} new` : (t.label ?? 'Create')
            }
          >
            <View>
              {t.key === 'create' ? renderCreate({ active: isActive }) : renderGlyph({ tabKey: t.key, active: isActive, color: tint })}
              {t.key === 'msg' && badge > 0 ? (
                <View style={s.badge}>
                  <Text style={s.badgeText}>{badge}</Text>
                </View>
              ) : null}
            </View>
            {t.label === null ? null : (
              <Text style={[s.label, { color: tint, fontSize: labelSize }]}>{t.label}</Text>
            )}
          </Pressable>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: theme.color.surface,
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    paddingTop: 7,
  },
  tab: { flex: 1, alignItems: 'center', gap: 4 },
  label: { fontFamily: theme.font.sans[600] },
  // §B13: `position:absolute; margin:-26px 0 0 13px` — anchored to the glyph box.
  badge: {
    position: 'absolute',
    top: -11,
    left: 13,
    minWidth: 15,
    height: 15,
    paddingHorizontal: 4,
    borderRadius: 8,
    backgroundColor: theme.color.coral,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeText: {
    fontFamily: theme.font.mono[400],
    fontSize: 9,
    lineHeight: 15,
    color: '#FFFFFF',
  },
});
