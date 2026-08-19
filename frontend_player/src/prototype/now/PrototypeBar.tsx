/**
 * THROWAWAY PROTOTYPE — issue #11. Not production.
 *
 * The floating switcher. Deliberately ugly and high-contrast so it never reads as part of
 * the design being judged, and it carries a live geometry readout — the numbers are the
 * argument, and reading them off the screen beats trusting the arithmetic in a comment.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

export interface Knobs {
  readonly width: 'device' | 320 | 375 | 393 | 430;
  readonly strip: 'bleed' | 'ratio' | 'inset';
  readonly overlay: 'off' | 'touch';
  readonly fixContrast: boolean;
}

const WIDTHS: Knobs['width'][] = ['device', 320, 375, 393, 430];
const STRIPS: Knobs['strip'][] = ['bleed', 'ratio', 'inset'];

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
    <View style={s.bar} pointerEvents="box-none">
      <Text style={s.readout}>{readout}</Text>
      <Row
        label="width"
        options={WIDTHS.map(String)}
        current={String(knobs.width)}
        onPick={(v) =>
          onChange({ ...knobs, width: v === 'device' ? 'device' : (Number(v) as 320) })
        }
      />
      <Row
        label="strip"
        options={STRIPS}
        current={knobs.strip}
        onPick={(v) => onChange({ ...knobs, strip: v as Knobs['strip'] })}
      />
      <Row
        label="show"
        options={['off', 'touch', 'a11y fix']}
        current={knobs.fixContrast ? 'a11y fix' : knobs.overlay}
        onPick={(v) =>
          onChange({
            ...knobs,
            overlay: v === 'touch' ? 'touch' : 'off',
            fixContrast: v === 'a11y fix',
          })
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
      {options.map((option) => (
        <Pressable
          key={option}
          onPress={() => onPick(option)}
          style={[s.pill, current === option ? s.pillOn : null]}
        >
          <Text style={[s.pillLabel, current === option ? s.pillLabelOn : null]}>{option}</Text>
        </Pressable>
      ))}
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
    gap: 6,
  },
  readout: { color: '#D9F24B', fontSize: 10, fontVariant: ['tabular-nums'] },
  row: { flexDirection: 'row', alignItems: 'center', gap: 4, flexWrap: 'wrap' },
  rowLabel: { color: '#8AA3AD', fontSize: 10, width: 38 },
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
