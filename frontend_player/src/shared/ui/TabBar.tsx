/**
 * The tab bar, per design-system 10.2 and `UI` §B13, as
 * [ADR-0082](../../../../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)
 * settles it.
 *
 * **Five glyphs from one stock outline family.** Feather, out of
 * `@expo/vector-icons`, which ships inside `expo` — no install, no asset licence, no SVG
 * pipeline. The family is fixed and the inventory is these five; a sixth glyph on a sixth
 * surface is a fresh question, and this component is not a licence to sprinkle.
 *
 * **Selection is coral alone, and that is a known WCAG 1.4.1 failure.** `coral` against
 * `muted` is 1.39:1 — in greyscale, or to a player with a red-green deficiency, the
 * selected tab is not distinguishable from the other four. Feather is a font, so there is
 * no filled counterpart and no stroke weight to carry the state instead. The ADR takes the
 * failure knowingly, bounds it — assistive technology is unaffected, because every tab
 * announces `selected` — and pre-costs the remedy: a 3pt coral dot under the selected
 * label. Do not re-litigate it here, and do not ship the bar without the labels below that
 * make it usable without sight.
 *
 * **The white plus on coral is not a Rule C violation.** Rule C forbids white *text* on
 * `coral` (3.89:1 against 1.4.3's 4.5). A glyph is non-text content, governed by 1.4.11,
 * whose threshold is 3:1 — so the plus is white and the badge's numeral, which is read, is
 * `ink`. One rule, two answers, rather than two opinions.
 *
 * **Presentational, and it holds no navigation.** It takes the active key and hands back
 * the one that was pressed; `(app)/(tabs)/_layout.tsx` is what knows those keys are routes.
 * That is what keeps the bar renderable in a test with no router, and what stops a design
 * primitive importing `expo-router`.
 */

import { Feather } from '@expo/vector-icons';
import { StyleSheet, Text, View, Pressable } from 'react-native';
import type { ComponentProps } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from './theme';

/** The five destinations, in `UI` §B13's order and under its keys. */
export type TabKey = 'now' | 'find' | 'create' | 'msg' | 'you';

type Glyph = ComponentProps<typeof Feather>['name'];

interface TabSpec {
  readonly key: TabKey;
  readonly glyph: Glyph;
  /** Absent on `create` alone: the circle is the label. */
  readonly label?: string;
  /** What a screen reader says. The visible label is a word; this is the destination. */
  readonly announce: string;
}

/**
 * The bar's inventory and its order, written out once.
 *
 * The order is the tuple's order — there is no separate list to drift from it, and the
 * component maps this straight onto columns.
 */
const TABS: readonly TabSpec[] = [
  { key: 'now', glyph: 'home', label: 'Now', announce: 'Now' },
  { key: 'find', glyph: 'search', label: 'Find', announce: 'Find' },
  { key: 'create', glyph: 'plus', announce: 'Create a match' },
  { key: 'msg', glyph: 'inbox', label: 'Inbox', announce: 'Inbox' },
  { key: 'you', glyph: 'user', label: 'You', announce: 'You' },
] as const;

export const TAB_BAR_ID = 'tab-bar';
export const TAB_CIRCLE_ID = 'tab-create-circle';
export const TAB_BADGE_ID = 'tab-badge';

/** One per tab, so a test can read the glyph's own box and colour rather than a snapshot. */
export function tabIconId(key: TabKey): string {
  return `tab-icon-${key}`;
}

export function tabId(key: TabKey): string {
  return `tab-${key}`;
}

export interface TabBarProps {
  readonly active: TabKey;
  /**
   * Unread counts, per tab. Only `msg` has a source in the product's plan and none of
   * them has one yet, so nothing passes this today — the shape is `UI` §B13's and the
   * badge is drawn from it rather than from a second mechanism when Inbox lands.
   */
  readonly badges?: Partial<Record<TabKey, number>>;
  readonly onSelect: (tab: TabKey) => void;
}

export function TabBar({ active, badges, onSelect }: TabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View
      testID={TAB_BAR_ID}
      accessibilityRole="tablist"
      // The inset is added rather than replacing the padding: on a phone with no home
      // indicator the bar still needs 10.2's 12pt below the labels.
      style={[s.bar, { paddingBottom: theme.space.md + insets.bottom }]}
    >
      {TABS.map((tab) => (
        <Tab
          key={tab.key}
          spec={tab}
          selected={tab.key === active}
          count={badges?.[tab.key]}
          onPress={() => onSelect(tab.key)}
        />
      ))}
    </View>
  );
}

function Tab({
  spec,
  selected,
  count,
  onPress,
}: {
  readonly spec: TabSpec;
  readonly selected: boolean;
  readonly count?: number;
  readonly onPress: () => void;
}) {
  const tint = selected ? theme.color.coral : theme.color.muted;
  const create = spec.key === 'create';

  return (
    <Pressable
      testID={tabId(spec.key)}
      accessibilityRole="tab"
      // The count rides in the label — a badge drawn beside a glyph is invisible to a
      // screen reader, and *Inbox, 2 new* is the whole of what it adds.
      accessibilityLabel={announce(spec, count)}
      // How the selected tab reaches assistive technology, and the reason ADR-0082 can
      // call its colour failure sighted-only. It is `accessibilityState` rather than a
      // word appended to the label above, because the platform already speaks that word
      // and a second copy is announced twice.
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [s.tab, pressed ? s.pressed : undefined]}
    >
      {create ? (
        <View testID={TAB_CIRCLE_ID} style={s.fab}>
          <Feather
            name={spec.glyph}
            size={theme.size.tabIcon}
            color={theme.color.surface}
            testID={tabIconId(spec.key)}
          />
        </View>
      ) : (
        <View style={s.iconBox}>
          <Feather
            name={spec.glyph}
            size={theme.size.tabIcon}
            color={tint}
            testID={tabIconId(spec.key)}
          />
          {count !== undefined && count > 0 ? <Badge count={count} /> : null}
        </View>
      )}

      {spec.label !== undefined ? (
        <Text style={[s.label, { color: tint }]} numberOfLines={1}>
          {spec.label}
        </Text>
      ) : null}
    </Pressable>
  );
}

/**
 * The unread pill.
 *
 * `ink` on `coral`, overriding `UI` §B13's white: a numeral is read, so it is text under
 * 1.4.3 and white on coral is 3.89:1. `ink` is 4.50:1 and is the one dark Rule C permits
 * there.
 *
 * Hidden from assistive technology because the count is already in the tab's own label —
 * a bare "2" announced after "Inbox" is a number with no noun.
 */
function Badge({ count }: { readonly count: number }) {
  return (
    <View
      testID={TAB_BADGE_ID}
      style={s.badge}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      <Text style={s.badgeCount}>{String(count)}</Text>
    </View>
  );
}

function announce(spec: TabSpec, count: number | undefined): string {
  if (count === undefined || count <= 0) return spec.announce;
  return `${spec.announce}, ${count} new`;
}

const s = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    // Five equal columns. `flex: 1` on the child is what makes them equal; the bar only
    // has to refuse to wrap.
    alignItems: 'flex-start',
    backgroundColor: theme.color.surface,
    // `line`, not `line2`: this bounds the screen rather than folding one card.
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    paddingTop: theme.space.xs,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    gap: theme.space.xxs,
  },
  // Touch has no hover, so the pressed state is declared. The whole column dims: there is
  // no fill to darken and the glyph is the only mark.
  pressed: { opacity: 0.7 },
  // A box of its own so the badge can sit against the glyph's corner rather than against
  // the column, which is centred and would move the badge as the label's width changed.
  iconBox: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
  },
  /**
   * The create control: a flat coral circle, level with the other four.
   *
   * ADR-0082 ratifies §A5.2's filled circle over §B13's `radius: 10` — a 28pt square with
   * a 10pt radius is the placeholder, not a design — and declines both the prototype's
   * `margin-bottom:-4px` and 10.2's *lifted 3 above the row*. Being nearly twice the size
   * and the only filled shape on the bar already says *this is not a fifth destination*;
   * raising it would break the bar's top line to say it twice.
   */
  fab: {
    width: theme.size.fab,
    height: theme.size.fab,
    borderRadius: theme.size.fab / 2,
    backgroundColor: theme.color.coral,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: { ...theme.type.tabLabel },
  badge: {
    position: 'absolute',
    // Against the glyph's top-right corner, which is `UI` §B13's own 13pt offset from the
    // icon's left edge, reached from the tokens rather than copied as a number.
    left: theme.size.tabIcon - theme.space.xxs,
    top: -theme.space.xs,
    minWidth: theme.size.tabBadge,
    height: theme.size.tabBadge,
    paddingHorizontal: theme.space.xxs,
    borderRadius: theme.size.tabBadge / 2,
    backgroundColor: theme.color.coral,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeCount: {
    ...theme.num.tabBadge,
    ...theme.tabular,
    color: theme.color.ink,
  },
});
