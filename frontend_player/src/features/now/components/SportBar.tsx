/**
 * Five fixed chips: **All · Padel · Tennis · Squash · Badminton**.
 *
 * `ADR-0084`. Identical for every player, whatever she is rated at, in the UI
 * authorities' order. **Selection is `ink`, not `coral`** — *a filter is not an
 * action*, and the design system already says the same thing about a selected card
 * (6.2): selection is a state, and coral is the accent an action *wants* you to
 * take.
 *
 * A square swatch on the four sports and none on `All`, because `All` is not a
 * sport — which is the distinction the whole bar carries. The swatch is
 * decoration: the label beside it always says the same thing.
 *
 * It is a `radiogroup`, so a screen reader hears *one of these is chosen* rather
 * than five unrelated buttons, and every chip announces its own selected state.
 */

import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { SportFilter } from '../mappers/codes';
import { SPORT_BAR, SPORT_CHIP_COPY } from '../mappers/sportBar';

import { GUTTER } from './nowGeometry';

export interface SportBarProps {
  readonly selected: SportFilter;
  readonly onSelect: (sport: SportFilter) => void;
}

export function SportBar({ selected, onSelect }: SportBarProps) {
  return (
    <View style={s.bar}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={s.row}
        accessibilityRole="radiogroup"
        accessibilityLabel="Filter by sport"
      >
        {SPORT_BAR.map((sport) => (
          <SportChip key={sport} sport={sport} selected={sport === selected} onSelect={onSelect} />
        ))}
      </ScrollView>
    </View>
  );
}

interface SportChipProps {
  readonly sport: SportFilter;
  readonly selected: boolean;
  readonly onSelect: (sport: SportFilter) => void;
}

function SportChip({ sport, selected, onSelect }: SportChipProps) {
  const chip = SPORT_CHIP_COPY[sport];

  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityLabel={chip.label}
      accessibilityState={{ selected }}
      // The chip is 25pt tall; the reachable area is 44.
      hitSlop={theme.hit.chipSm}
      onPress={() => onSelect(sport)}
      style={({ pressed }) => [
        s.chip,
        selected ? s.chipSelected : undefined,
        pressed && !selected ? s.chipPressed : undefined,
      ]}
    >
      {chip.swatch !== undefined ? (
        <View
          style={[s.swatch, { backgroundColor: theme.sport[chip.swatch] }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      ) : null}
      <Text style={[s.label, selected ? s.labelSelected : undefined]}>{chip.label}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // Pinned beneath the header, so it keeps its own background when the greeting
  // scrolls away underneath it.
  bar: { backgroundColor: theme.color.paper, paddingBottom: theme.space.sm },
  row: { paddingHorizontal: GUTTER, gap: theme.space.xs },
  chip: {
    height: theme.size.chipSm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    paddingHorizontal: theme.space.sm,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
  },
  chipSelected: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  chipPressed: { borderColor: theme.color.muted },
  swatch: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.bar,
  },
  label: { ...theme.type.chip, color: theme.color.ink },
  labelSelected: { color: theme.color.paper },
});
