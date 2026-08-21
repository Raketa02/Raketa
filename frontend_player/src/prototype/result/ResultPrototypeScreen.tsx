/**
 * THROWAWAY PROTOTYPE — issue #24. Not production.
 *
 * Three variants of the result conversation, on one screen, switched from the bar. The
 * variants disagree about WHERE the conversation happens — that is the question. The
 * frame reproduces #11's width knob because §5's constraint is a one-handed thumb at
 * 320pt in the dark, and every one of these screens is a target-size argument.
 *
 * `deltas/native-kit.md` §1 governs the frame: content width = screen width − 30, no cap
 * and no centring. The 30 is `2 × theme.space.lg` and nothing else.
 */

import { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { theme } from '@/shared/ui';

import { FIXTURES, SHAPE, type Leg } from './data';
import { PrototypeBar, VARIANT_NAME, type Knobs } from './PrototypeBar';
import { VariantA } from './VariantA';
import { VariantB } from './VariantB';
import { VariantC } from './VariantC';

const GUTTER = theme.space.lg;

export function ResultPrototypeScreen() {
  const device = useWindowDimensions();
  const [knobs, setKnobs] = useState<Knobs>({
    variant: 'A',
    screen: 'asked',
    sport: 'padel',
    width: 'device',
  });

  const fixture = FIXTURES[knobs.sport];
  const shape = SHAPE[fixture.sport];

  // One draft per sport, so flipping the sport knob does not carry a padel score into a
  // squash grid. The counter pre-loads with the other side's numbers, per §3: a counter
  // always carries a score, so it starts from theirs rather than from an empty grid.
  const [drafts, setDrafts] = useState<Record<'padel' | 'squash', readonly Leg[]>>({
    padel: blank(SHAPE.padel.legs),
    squash: blank(SHAPE.squash.legs),
  });
  const draft = knobs.screen === 'counter' ? fixture.counter : drafts[knobs.sport];

  const frameWidth = knobs.width === 'device' ? device.width : knobs.width;
  const content = frameWidth - 2 * GUTTER;
  const readout = useMemo(
    () =>
      `${knobs.variant} — ${VARIANT_NAME[knobs.variant]}  ·  frame ${frameWidth}  content ${content}  ·  ` +
      `${shape.legs}x2 grid, pad 0-${shape.padTo}  ·  device ${Math.round(device.width)}x${Math.round(device.height)}`,
    [knobs.variant, frameWidth, content, shape.legs, shape.padTo, device.width, device.height],
  );

  return (
    <SafeAreaView style={s.root} edges={['top', 'bottom']}>
      <View style={[s.frame, { width: frameWidth }]}>
        <Text style={s.crumb}>NOW · the post-play group</Text>
        {/* A is the only variant whose content can outgrow the screen — the pad inside the
            night card is the reason, and that overflow is one of the findings. B pins a
            sheet and C scrolls its own body. */}
        <Container scrolls={knobs.variant === 'A'}>
          {knobs.variant === 'A' ? (
            <VariantA
              fixture={fixture}
              screen={knobs.screen}
              draft={draft}
              setDraft={(next) => setDrafts((d) => ({ ...d, [knobs.sport]: next }))}
            />
          ) : null}
          {knobs.variant === 'B' ? (
            <VariantB
              fixture={fixture}
              screen={knobs.screen}
              draft={draft}
              setDraft={(next) => setDrafts((d) => ({ ...d, [knobs.sport]: next }))}
            />
          ) : null}
          {knobs.variant === 'C' ? (
            <VariantC
              fixture={fixture}
              screen={knobs.screen}
              draft={draft}
              setDraft={(next) => setDrafts((d) => ({ ...d, [knobs.sport]: next }))}
            />
          ) : null}
        </Container>
      </View>
      <PrototypeBar knobs={knobs} onChange={setKnobs} readout={readout} />
    </SafeAreaView>
  );
}

function Container({
  scrolls,
  children,
}: {
  readonly scrolls: boolean;
  readonly children: React.ReactNode;
}) {
  if (!scrolls) return <View style={[s.stage, s.stageInner]}>{children}</View>;
  return (
    <ScrollView style={s.stage} contentContainerStyle={s.stageInner} showsVerticalScrollIndicator>
      {children}
    </ScrollView>
  );
}

function blank(legs: number): readonly Leg[] {
  return Array.from({ length: legs }, () => [null, null] as Leg);
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.color.paper, alignItems: 'flex-start' },
  frame: { flex: 1, paddingHorizontal: GUTTER },
  crumb: { ...theme.type.eyebrow, color: theme.color.muted, paddingVertical: theme.space.sm },
  // 190 is the bar; it floats over the design in the real screen too, so the stage keeps
  // its own bottom clear rather than letting the bar hide an action row.
  stage: { flex: 1 },
  stageInner: { paddingBottom: 190 },
});
