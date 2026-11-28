/**
 * **Sign-up's podium** — the Rankings podium in the hero's room, with **You** on the first step
 * ([#788](https://github.com/Rakieta02/Rakieta/issues/788), PRD #783; design system 12.2, mock 5).
 *
 * ```
 *                   [ TK ]                 You's tile, larger, ringed in volt
 *       [ SW ]       You
 *       stas.w   ┌─────────┐   [ ID ]
 *     ┌────────┐ │    1    │   ines.d     the first step volt, the tallest, its number ink
 *     │   2    │ │         │ ┌────────┐   the outer two white at a seventh (stageStep)
 *     │        │ │         │ │   3    │
 * ────┴────────┴─┴─────────┴─┴────────┴── the room's foot, just over the headline
 * ```
 *
 * ## A picture of the podium, not the podium
 *
 * The live one is `rankings`' (`PodiumSteps`): a press on every step, the reader's real place, real
 * faces. It is not made public and not changed — auth may not import another feature, for the deck's
 * reason — so the steps, the faces and the names are **redrawn here** from shared UI's poster
 * (`StageFace`) and the theme, and a change to the live podium does not reach the picture by itself.
 * Where mock 5 draws it differently, the mock wins: no Levels, the steps on the night instead of a
 * paper recess, a ring round each face, and the third's face a step under the second's. **Except the
 * numbers**: mock 5 sets them in a bold sans, and they stay mono and tabular, as every number in the
 * app is — the place card's gap line made the same call (design system Part 16, #775). The first's is
 * a size up (`num.l`), as the mock draws it. Volt is a fill here, which it may be anywhere, with `ink`
 * on it (13,96), and a ring on the night, where it may be a stroke.
 *
 * ## It rises once
 *
 * Each step is drawn at its full height **inside a box of that height that clips it**, and rising is
 * the step sliding up out of the baseline into that box — the native driver's translate, never a
 * scale, which would squash its number and which iOS rasterises blurred. Each player arrives from a
 * little below (`space.md`) and fades in, the volt ring with You. **When is `usePodiumRise`'s**, handed
 * in as six values.
 *
 * ## The fit
 *
 * Drawn at `size.stage.podium`'s size and scaled whole into the room (`stageFit`), never up; **it
 * stands on the room's foot**, centred across it, so on a tall room the steps keep to the headline
 * and the room over You is night. Nothing is drawn until the room is measured.
 */

import { Animated, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { StageFace } from './StageFace';
import {
  FACE_TO_NAME,
  NAME_TO_STEP,
  PODIUM_BOX,
  STANDING_ORDER,
  podiumPlate,
  type PodiumPlace,
} from './stagePodiumGeometry';
import { STAGE_PODIUM } from './stagePodiumPresentation';
import { useMeasuredRoom } from './useMeasuredRoom';
import type { PodiumRise, StagePodiumMotion } from './usePodiumRise';

const PODIUM = theme.size.stage.podium;
const CAP = theme.size.stage.textMaxScale;

export function StagePodium(motion: StagePodiumMotion) {
  const { room, measured, onLayout } = useMeasuredRoom();
  const { scale, left, top } = podiumPlate(room);

  return (
    <View style={StyleSheet.absoluteFill} onLayout={onLayout} testID="stage-podium">
      {/* The box at its drawn size, fitted into the room and standing on its foot (`podiumPlate`). */}
      <View
        testID="stage-podium-plate"
        style={[s.plate, measured ? { left, top, transform: [{ scale }] } : s.unmeasured]}
      >
        {STANDING_ORDER.map((place) => (
          <Column key={place} place={place} rise={motion[place]} />
        ))}
      </View>
    </View>
  );
}

/**
 * How a place is drawn: the first is You's — a volt ring, a volt step, its number ink and a size up;
 * the other two are the night's — a white rim, a translucent step, their numbers white.
 */
const LOOK = {
  first: {
    edge: { width: PODIUM.ring, color: theme.color.volt },
    step: { backgroundColor: theme.color.volt },
    rank: { ...theme.num.l, ...theme.tabular, color: theme.color.ink },
  },
  other: {
    edge: { width: PODIUM.rim, color: theme.color.stageRim },
    step: { backgroundColor: theme.color.stageStep },
    rank: { ...theme.num.m, ...theme.tabular, color: theme.color.surface },
  },
} as const;

/** One place: its player over its step. */
function Column({ place, rise }: { readonly place: PodiumPlace; readonly rise: PodiumRise }) {
  const player = STAGE_PODIUM[place];
  const look = place === 'first' ? LOOK.first : LOOK.other;
  const height = PODIUM.step[place];

  return (
    <View testID={`stage-podium-${place}`} style={s.column}>
      <Animated.View
        testID={`stage-podium-player-${place}`}
        style={[
          s.player,
          {
            opacity: rise.player,
            transform: [
              {
                translateY: rise.player.interpolate({
                  inputRange: [0, 1],
                  outputRange: [theme.space.md, 0],
                }),
              },
            ],
          },
        ]}
      >
        <StageFace
          testID={`stage-podium-face-${place}`}
          look={player.look}
          letters={player.letters}
          size={PODIUM.face[place]}
          edge={look.edge}
        />
        <Text style={s.name} numberOfLines={1} maxFontSizeMultiplier={CAP}>
          {player.name}
        </Text>
      </Animated.View>
      {/* The step's own height, clipping it: rising is the step sliding up out of the baseline. */}
      <View style={[s.clip, { height }]}>
        <Animated.View
          testID={`stage-podium-step-${place}`}
          style={[
            s.step,
            look.step,
            {
              height,
              transform: [
                {
                  translateY: rise.step.interpolate({
                    inputRange: [0, 1],
                    outputRange: [height, 0],
                  }),
                },
              ],
            },
          ]}
        >
          <Text style={look.rank} numberOfLines={1} maxFontSizeMultiplier={CAP}>
            {player.rank}
          </Text>
        </Animated.View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // The three columns on one baseline, the box's foot.
  plate: {
    position: 'absolute',
    width: PODIUM_BOX.width,
    height: PODIUM_BOX.height,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
  },
  // Nothing until the room is known — a frame at the wrong size would be a jump.
  unmeasured: { opacity: 0 },
  column: { width: PODIUM.stepWidth, alignItems: 'center' },
  player: { alignItems: 'center', gap: FACE_TO_NAME, marginBottom: NAME_TO_STEP },
  // The live podium's name role, white on the night.
  name: { ...theme.type.cardTitle, color: theme.color.surface },
  clip: { alignSelf: 'stretch', overflow: 'hidden' },
  // Mock 5's corner is 8,6pt; `btn`'s 10 is the nearest the theme has.
  step: {
    alignItems: 'center',
    paddingTop: theme.space.sm,
    borderTopLeftRadius: theme.radius.btn,
    borderTopRightRadius: theme.radius.btn,
  },
});
