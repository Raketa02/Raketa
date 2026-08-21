/* eslint-disable no-restricted-syntax --
 * THROWAWAY PROTOTYPE. The rule is right and the literals below are the POINT: every one
 * is a value `theme.ts` cannot express yet, marked `MISSING TOKEN`, and the list of them
 * is part of this ticket's answer. A literal in a production component stays a bug.
 */
/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * The floating switcher, in #11's house style: deliberately ugly and high-contrast so it
 * never reads as part of the design being judged.
 */

import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { Screen } from './types';

export interface Knobs {
  readonly variant: 'A' | 'B' | 'C';
  readonly screen: Screen;
  readonly sport: 'padel' | 'squash';
  readonly width: 'device' | 320 | 375 | 393 | 430;
}

export const VARIANT_NAME: Record<Knobs['variant'], string> = {
  A: 'in the card',
  B: 'a sheet over Now',
  C: 'a result screen',
};

const SCREENS: Screen[] = ['enter', 'asked', 'waiting', 'counter', 'unscored'];
const WIDTHS: Knobs['width'][] = ['device', 320, 375, 393, 430];

export function PrototypeBar({
  knobs,
  onChange,
  readout,
}: {
  readonly knobs: Knobs;
  readonly onChange: (next: Knobs) => void;
  readonly readout: string;
}) {
  return (
    <View style={s.bar}>
      <Text style={s.readout}>{readout}</Text>
      <Row
        label="variant"
        options={['A', 'B', 'C']}
        current={knobs.variant}
        onPick={(v) => onChange({ ...knobs, variant: v as Knobs['variant'] })}
      />
      <Row
        label="screen"
        options={SCREENS}
        current={knobs.screen}
        onPick={(v) => onChange({ ...knobs, screen: v as Screen })}
      />
      <Row
        label="sport"
        options={['padel', 'squash']}
        current={knobs.sport}
        onPick={(v) => onChange({ ...knobs, sport: v as Knobs['sport'] })}
      />
      <Row
        label="width"
        options={WIDTHS.map(String)}
        current={String(knobs.width)}
        onPick={(v) =>
          onChange({ ...knobs, width: v === 'device' ? 'device' : (Number(v) as 320) })
        }
      />
    </View>
  );
}

function Row({
  label,
  options,
  current,
  onPick,
}: {
  readonly label: string;
  readonly options: readonly string[];
  readonly current: string;
  readonly onPick: (value: string) => void;
}) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.pills}>
        {options.map((option) => (
          <Pressable
            key={option}
            onPress={() => onPick(option)}
            style={[s.pill, current === option ? s.pillOn : null]}
          >
            <Text style={[s.pillLabel, current === option ? s.pillLabelOn : null]}>{option}</Text>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  bar: {
    position: 'absolute',
    left: 8,
    right: 8,
    bottom: 8,
    backgroundColor: 'rgba(8,20,26,0.94)',
    borderWidth: 1,
    borderColor: '#D9F24B',
    borderRadius: 12,
    padding: 8,
    gap: 5,
  },
  readout: { color: '#D9F24B', fontSize: 10, fontVariant: ['tabular-nums'] },
  row: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  rowLabel: { color: '#8AA3AD', fontSize: 10, width: 44 },
  pills: { gap: 4 },
  pill: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.12)',
  },
  pillOn: { backgroundColor: '#D9F24B' },
  pillLabel: { color: '#FFFFFF', fontSize: 11 },
  pillLabelOn: { color: '#08222B', fontWeight: '700' },
});
