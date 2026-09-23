/**
 * **You** — the viewer's tile at the radar's origin: a 34 pt square, your photograph or your
 * poster, a volt ring, and the word *you* beneath in `tiny`
 * ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.2).
 *
 * The face is `PlayerPhoto`'s `face` box — the photograph, or the poster that stands in for
 * it, one owner for the switch and the corner — inside a ring drawn by this component: volt is
 * *a stroke only on dark* and the ground is dark, 10,67 on the centre. The photograph is the
 * reader's own, read the way the yes screen reads it (`useOwnFace`, `player_record`'s one
 * export for the purpose); until the read lands the poster stands in, which is what a player
 * with no photograph has in any case.
 *
 * **Tapping it does nothing**, and it is no element: the rings measure from it and the footer
 * names the count. It sits inside the field's transform so it moves with a pan, and it is
 * counter-scaled like every tile so it is always 34 pt.
 */

import { StyleSheet, Text, View } from 'react-native';

import { PlayerPhoto, playerPhotoRadius, theme } from '@/shared/ui';

import { YOU_LABEL } from '../radarPresentation';

export interface YouTileProps {
  readonly playerId: string;
  readonly photoUrl?: string;
}

export function YouTile({ playerId, photoUrl }: YouTileProps) {
  return (
    <View
      style={s.tile}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View style={s.ring}>
        <PlayerPhoto playerId={playerId} photoUrl={photoUrl} box={FACE} />
      </View>
      <Text style={s.you}>{YOU_LABEL}</Text>
    </View>
  );
}

const SIZE = theme.size.radar.you;
const STROKE = theme.size.radar.stroke;
const FACE = { kind: 'face', size: SIZE } as const;

const s = StyleSheet.create({
  tile: { alignItems: 'center', gap: theme.space.xxs },
  // The ring hugs the face: the corner grows by the stroke so the two curves are concentric.
  ring: {
    borderWidth: STROKE,
    borderColor: theme.color.volt,
    borderRadius: playerPhotoRadius(SIZE) + STROKE,
  },
  you: { ...theme.type.tiny, color: theme.color.onDarkTiny },
});
