/**
 * A candidate's face — **the photograph, or the poster that stands in for it** — in whichever
 * box the surface has for it.
 *
 * One component at three sizes, per
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §4: the ground of the competitive card's photo panel, the full-bleed media on the social and
 * deck cards, and the face in a court seat. It exists so that the photo-or-poster switch is
 * written once, and its radius rule has **one owner** — which is how §G2's *34 % against 33 %*
 * split was settled without picking a winner, and what deletes §G1's *"rewriting the photo's
 * declared width to a percentage by string substitution"* by making the substitution
 * unnecessary.
 *
 * **It is still that switch and nothing more.** The scrim, the Level and the Sport that turned
 * the first of the three boxes from a thumbnail into a panel are `PhotoPanel`'s: they are facts
 * about a candidate, and this component knows only about a picture.
 *
 * ## The URL, and why the id is not here
 *
 * `photo_url` is a short-lived signed link **minted per response and recorded nowhere**, and
 * it is the only address this photograph has: `GET /photos/{id}` signs your own photos and
 * refuses a stranger's id deliberately, so a client cannot sign one
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §9). The two fields are **omitted together**, and an expired link is not an error to report
 * — both fall back to the poster, which is what a player with no photo has in any case.
 *
 * ## The poster is a fact about the id and nothing else
 *
 * `courtPosterFor` is reached through `player_profile`'s public surface rather than copied:
 * the design system's contract is that **one player id always produces one poster**, and a
 * second implementation of the hash is two posters for one person the day either one changes.
 * A poster is shown and never read — the pose is not a fact, and the hue names no Sport.
 *
 * ## It announces nothing
 *
 * §20.1's rule is *one accessibility element per action, and everything with no action of its
 * own merges into the nearest action above it*. A face has no action, and every surface that
 * draws one has a named ancestor that does — the card body, or the seat. So the box is hidden
 * on both platforms, which is the explicit half of that rule rather than an omission of it.
 * The poster's own sentence is still carried, for the reason `CANDIDATE_POSTER_LABEL` states.
 */

import { Image, StyleSheet, View } from 'react-native';

import { courtPosterFor } from '@/features/player_profile/types';
import { CourtPoster, theme } from '@/shared/ui';

import { CANDIDATE_POSTER_LABEL } from '../playerCardPresentation';

/**
 * The radius, as a share of the box's **own** width.
 *
 * A ratio rather than three tokens, because the three boxes are three sizes of one object and
 * a token per size is three numbers to keep in proportion. 33 %, which is 6.9's avatar rule
 * read as the rule it always was.
 */
const RADIUS_RATIO = 0.33;

/**
 * That corner, for the one thing drawn **around** a face rather than inside it.
 *
 * A court seat rings its face and an empty seat draws the ring with no face behind it, so the
 * ratio has to be readable from outside — and a second `* 0.33` in the seat is the drift
 * having one owner was supposed to close. Exported as a function rather than as the number,
 * because what is owned is *a share of the box* and a caller handed `0.33` would have to know
 * what to do with it.
 */
export function candidatePhotoRadius(size: number): number {
  return size * RADIUS_RATIO;
}

/**
 * The competitive card's **panel**, in points — the one box whose dimensions are the card's
 * own rather than the caller's.
 *
 * It is here rather than in `theme.ts` for §1's reason: the design system holds drawn objects
 * and control vocabulary, and a candidate card is a composition that names a domain noun.
 *
 * **Exported, because it stopped being a thumbnail.**
 * [#309](https://github.com/Raketa02/Raketa/issues/309) turned the box into a panel with a
 * scrim, a Level and a Sport over it, and those overlays have to be clipped to exactly the
 * corner the photograph takes. `PhotoPanel` reads the two numbers from here rather than
 * restating them, which is the same *one owner* argument `candidatePhotoRadius` already makes
 * for the ratio: a second copy of `74` is two boxes the day either one moves.
 */
export const CANDIDATE_PANEL = { width: 74, height: 92 } as const;

/**
 * Which box this face is drawn in.
 *
 * A discriminated union rather than a `size` string with an optional number beside it: the
 * seat's face is sized by the court that places it — the court owns the geometry and hands
 * nothing back — and the other two carry no number at all.
 */
export type CandidatePhotoBox =
  /** {@link CANDIDATE_PANEL} — the ground of the competitive card's photo panel. */
  | { readonly kind: 'thumb' }
  /**
   * Full-bleed, filling whatever slot the card gives it.
   *
   * **No radius of its own**: media that bleeds to a card's edges takes the card's corners,
   * clipped by the card. A second radius here would be the same corner drawn twice, at two
   * values, one of which would eventually stop matching.
   */
  | { readonly kind: 'media' }
  /** A face in a seat, at the size `Court` decided from its own width. */
  | { readonly kind: 'face'; readonly size: number };

export interface CandidatePhotoProps {
  /** Whose face this is. The poster's whole input, and the reason it survives a reinstall. */
  readonly playerId: string;
  /** Omitted with `photo_id` when they have no photo, and on a link that has expired. */
  readonly photoUrl?: string;
  readonly box: CandidatePhotoBox;
}

export function CandidatePhoto({ playerId, photoUrl, box }: CandidatePhotoProps) {
  const shape = geometry(box);

  return (
    <View
      style={[s.box, shape]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {photoUrl === undefined ? (
        <CourtPoster {...courtPosterFor(playerId)} accessibilityLabel={CANDIDATE_POSTER_LABEL} />
      ) : (
        <Image source={{ uri: photoUrl }} style={s.image} />
      )}
    </View>
  );
}

/** The box's own dimensions and its own corner — the whole of what the three sizes differ by. */
function geometry(box: CandidatePhotoBox) {
  switch (box.kind) {
    case 'thumb':
      return { ...CANDIDATE_PANEL, borderRadius: candidatePhotoRadius(CANDIDATE_PANEL.width) };
    case 'media':
      return { flex: 1 };
    case 'face':
      return { width: box.size, height: box.size, borderRadius: candidatePhotoRadius(box.size) };
  }
}

const s = StyleSheet.create({
  // The poster is drawn to its own box and the photograph is cropped to it, so the clip is
  // the box's rather than either child's — one corner, whichever of the two is inside it.
  box: { overflow: 'hidden', backgroundColor: theme.color.paper2 },
  image: { width: '100%', height: '100%' },
});
