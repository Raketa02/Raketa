/**
 * **Stacked faces and *+N*** — up to six faces, each over the one before it, and a count of
 * everybody not drawn (play 58–60; club 18, 19). Info's members row draws it (#514), so does an
 * official group's members card in the administrator area (#516), and so do a Hottest groups card
 * (four) and its group sheet (six, #800) — which is why it is one drawing.
 *
 * Each face is ringed in the card's white, so an overlapping face reads as in front rather than
 * merged — its corner the face's own, grown by the ring, so the two curves stay one distance apart.
 * The faces are pictures of people the element around them names, so the stack speaks nothing of its
 * own; the caller's element carries the words.
 */

import { StyleSheet, Text, View } from 'react-native';

import { PlayerPhoto, playerPhotoRadius, theme } from '@/shared/ui';

import type { GroupPerson } from '../domain/group';

import { moreFaces } from './groupsPresentation';

const FACE = theme.size.groupPage.stackFace;
const RING = theme.size.groupPage.stackRing;

export interface FaceStackProps {
  /** Drawn in this order, the first at the back. The caller has already cut them to its count. */
  readonly faces: readonly Pick<GroupPerson, 'playerId' | 'photoUrl'>[];
  /** Everybody not drawn — *+N* — and nothing at `0`. */
  readonly more: number;
  /** How a suite finds each face: `<prefix><playerId>`. */
  readonly testIDPrefix: string;
}

export function FaceStack({ faces, more, testIDPrefix }: FaceStackProps) {
  return (
    <View style={s.faces}>
      <View style={s.stack}>
        {faces.map((face, at) => (
          <View
            key={face.playerId}
            testID={`${testIDPrefix}${face.playerId}`}
            style={[s.stacked, at > 0 ? s.overlap : undefined]}
          >
            <PlayerPhoto
              playerId={face.playerId}
              {...(face.photoUrl === undefined ? {} : { photoUrl: face.photoUrl })}
              box={{ kind: 'face', size: FACE }}
            />
          </View>
        ))}
      </View>
      {more > 0 ? <Text style={s.more}>{moreFaces(more)}</Text> : null}
    </View>
  );
}

const s = StyleSheet.create({
  faces: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  stack: { flexDirection: 'row' },
  stacked: {
    borderWidth: RING,
    borderColor: theme.color.surface,
    borderRadius: playerPhotoRadius(FACE) + RING,
  },
  overlap: { marginLeft: -theme.size.groupPage.stackOverlap },
  more: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
});
