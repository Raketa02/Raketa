/**
 * **A face on the stage's pictures** — the yes tile's drawing, redrawn in auth: a poster at a
 * third-of-the-box corner, and two letters over it in the heaviest weight with the on-media shadow,
 * set at a share of the poster ([#787](https://github.com/Raketa02/Raketa/issues/787),
 * [#788](https://github.com/Raketa02/Raketa/issues/788); design system 12.2). Sign-in's *It's a
 * game!* draws it bare; sign-up's podium draws it inside an edge — You's volt ring, the others'
 * translucent rim.
 *
 * **Always a poster, never a photograph**: nobody on the hero is a person with a photo, and ADR-0167
 * §3 lets letters sit over a poster only. Its note of 2026-11-08 extends that to sign-in's picture of
 * the yes screen, and its note of 2026-11-09 to sign-up's podium, and to nothing else.
 *
 * **The edge is drawn inside the tile** — `size` is outer edge to outer edge, as the mocks measure it
 * — and the poster fills what it leaves, its corner the tile's less the edge, so the edge reads as a
 * ring round the poster rather than a line over it.
 */

import { StyleSheet, Text, View } from 'react-native';

import {
  CourtPoster,
  POSTER_LABEL,
  playerPhotoRadius,
  theme,
  type CourtPosterLook,
} from '@/shared/ui';

const CAP = theme.size.stage.textMaxScale;

export interface StageFaceProps {
  readonly look: CourtPosterLook;
  /** The two letters over the poster; none, and it is bare. */
  readonly letters?: string;
  /** Outer edge to outer edge, the edge included. */
  readonly size: number;
  /** A ring round the poster, drawn inside the tile. */
  readonly edge?: { readonly width: number; readonly color: string };
  readonly testID?: string;
}

export function StageFace({ look, letters, size, edge, testID }: StageFaceProps) {
  const radius = playerPhotoRadius(size);
  const inset = edge?.width ?? 0;
  const poster = size - 2 * inset;

  return (
    <View
      testID={testID}
      style={[
        s.tile,
        { width: size, height: size, borderRadius: radius },
        edge === undefined ? undefined : { borderWidth: edge.width, borderColor: edge.color },
      ]}
    >
      <View style={[s.poster, { borderRadius: radius - inset }]}>
        <CourtPoster
          hue={look.hue}
          pose={look.pose}
          accessibilityLabel={POSTER_LABEL}
          style={StyleSheet.absoluteFill}
        />
        {letters === undefined ? null : (
          <View style={s.initials}>
            <Text
              style={[s.letters, { fontSize: poster * theme.size.yesTile.initials }]}
              numberOfLines={1}
              adjustsFontSizeToFit
              maxFontSizeMultiplier={CAP}
            >
              {letters}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  tile: { overflow: 'hidden' },
  poster: { flex: 1, overflow: 'hidden' },
  initials: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center' },
  // The yes tile's letters: white over the poster's light stop is 4,5:1 by the poster's own bound.
  letters: {
    fontFamily: theme.font.sans[800],
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
});
