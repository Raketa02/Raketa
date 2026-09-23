/**
 * A player's face — **the photograph, or the poster that stands in for it** — in whichever
 * box the surface has for it.
 *
 * One component at three sizes, per
 * [`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §4: the ground of the competitive card's photo panel, the full-bleed media on the social and
 * deck cards, and the face in a court seat. It exists so that the photo-or-poster switch is
 * written once, and its radius rule has **one owner** — which is how §G2's *34 % against 33 %*
 * split was settled without picking a winner, and what deletes §G1's *"rewriting the photo's
 * declared width to a percentage by string substitution"* by making the substitution
 * unnecessary.
 *
 * **It is still that switch and nothing more.** The scrim, the Level and the Sport that turned
 * the first of the three boxes from a thumbnail into a panel are `PhotoPanel`'s: they are facts
 * about a person, and this component knows only about a picture.
 *
 * ## Why it is `shared/ui` and named for a player rather than for a candidate
 *
 * It was `features/play/components/candidate/CandidatePhoto`, because a search result was the
 * only thing in the app that had a face. The **record sheet's header draws the same switch**
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)) and `player_record` may not import
 * `features/play/` — the arrow runs the other way, since Play is what opens the sheet — so the
 * switch came below both, exactly as the run of form and the Social tag row did
 * ([#375](https://github.com/Raketa02/Raketa/issues/375)). A *candidate* is Play's word for a
 * row a search returned; what this draws is a **player**, which is the word that survives the
 * move.
 *
 * ## The URL, and why the id is not here
 *
 * `photo_url` is a short-lived signed link **minted per response and recorded nowhere**, and
 * it is the only address this photograph has: `GET /photos/{id}` signs your own photos and
 * refuses a stranger's id deliberately, so a client cannot sign one
 * ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §9). The two fields are **omitted together**, and an expired link is not an error to report
 * — both fall back to the poster, which is what a player with no photo has in any case.
 *
 * ## The poster is a fact about the id and nothing else
 *
 * `courtPosterFor` is reached from `@/shared/ui` rather than copied: the design system's
 * contract is that **one player id always produces one poster**, and a second implementation of
 * the hash is two posters for one person the day either one changes.
 * A poster is shown and never read — the pose is not a fact, and the hue names no Sport.
 *
 * ## It announces nothing
 *
 * §20.1's rule is *one accessibility element per action, and everything with no action of its
 * own merges into the nearest action above it*. A face has no action, and every surface that
 * draws one has a named ancestor that does — the card body, or the seat. So the box is hidden
 * on both platforms, which is the explicit half of that rule rather than an omission of it.
 * The poster's own sentence is still carried, for the reason `POSTER_LABEL` states.
 */

import { Image, StyleSheet, View } from 'react-native';

import { CourtPoster } from './CourtPoster';
import { courtPosterFor } from './courtPosterFraming';
import { theme } from './theme';

/**
 * What a listener is told when the face is a **poster** rather than a photograph.
 *
 * It came here with the switch that decides between the two, from Play's own copy deck: the
 * sentence is about the *drawing* — nobody should have to see a poster to know they are not
 * looking at the player ([6.9](../../../docs/design-system.md#69-the-photo-tile-and-picker)) —
 * and every surface that draws one owes it. The photograph carries none, because a photograph
 * of somebody is not a fact this app is entitled to describe.
 */
export const POSTER_LABEL = 'A generated court poster, not a photograph';

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
export function playerPhotoRadius(size: number): number {
  return size * RADIUS_RATIO;
}

/** Which composition a photo panel is drawn for — see {@link PHOTO_PANEL}. */
export type PhotoPanelSize = 'card' | 'record';

/**
 * The **panel**, in points — the one box whose dimensions are the composition's rather than
 * the caller's, at each of the two sizes it is drawn at
 * ([7.16](../../../docs/design-system.md#716-the-photo-panel)).
 *
 * It is here rather than in `theme.ts` for §1's reason: the design system holds drawn objects
 * and control vocabulary, and this is one drawn object's own geometry.
 *
 * **Exported, because it stopped being a thumbnail.**
 * [#309](https://github.com/Raketa02/Raketa/issues/309) turned the box into a panel with a
 * scrim, a Level and a Sport over it, and those overlays have to be clipped to exactly the
 * corner the photograph takes. `PhotoPanel` reads the numbers from here rather than restating
 * them, which is the same *one owner* argument `playerPhotoRadius` already makes for the
 * ratio: a second copy of `74` is two boxes the day either one moves.
 *
 * **`record` is a second size and not a scale.** Every number on this panel is arithmetic
 * against its own width — the corner is a third of it, and what the corner leaves at the
 * mark's own top edge is what `ON_COURT_MAX_SCALE` is derived from — so the larger panel
 * **re-derives** rather than multiplying, and `onCourtMarkFit.test.ts` carries both cases.
 * 4:5 at both, and both on the 4pt step the card's 74 x 92 is nearest to.
 */
export const PHOTO_PANEL = {
  card: { width: 74, height: 92 },
  record: { width: 112, height: 140 },
} as const satisfies Readonly<Record<PhotoPanelSize, { width: number; height: number }>>;

/**
 * Which box this face is drawn in.
 *
 * A discriminated union rather than a `size` string with an optional number beside it: the
 * seat's face is sized by the court that places it — the court owns the geometry and hands
 * nothing back — and the other two carry no number at all.
 */
export type PlayerPhotoBox =
  /** {@link PHOTO_PANEL} — the ground of a photo panel, at whichever size it is drawn. */
  | { readonly kind: 'panel'; readonly size: PhotoPanelSize }
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

export interface PlayerPhotoProps {
  /** Whose face this is. The poster's whole input, and the reason it survives a reinstall. */
  readonly playerId: string;
  /** Omitted with `photo_id` when they have no photo, and on a link that has expired. */
  readonly photoUrl?: string;
  readonly box: PlayerPhotoBox;
}

export function PlayerPhoto({ playerId, photoUrl, box }: PlayerPhotoProps) {
  const shape = geometry(box);

  return (
    <View
      style={[s.box, shape]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {photoUrl === undefined ? (
        <CourtPoster {...courtPosterFor(playerId)} accessibilityLabel={POSTER_LABEL} />
      ) : (
        <Image source={{ uri: photoUrl }} style={s.image} />
      )}
    </View>
  );
}

/** The box's own dimensions and its own corner — the whole of what the three sizes differ by. */
function geometry(box: PlayerPhotoBox) {
  switch (box.kind) {
    case 'panel': {
      const panel = PHOTO_PANEL[box.size];
      return { ...panel, borderRadius: playerPhotoRadius(panel.width) };
    }
    case 'media':
      return { flex: 1 };
    case 'face':
      return { width: box.size, height: box.size, borderRadius: playerPhotoRadius(box.size) };
  }
}

const s = StyleSheet.create({
  // The poster is drawn to its own box and the photograph is cropped to it, so the clip is
  // the box's rather than either child's — one corner, whichever of the two is inside it.
  box: { overflow: 'hidden', backgroundColor: theme.color.paper2 },
  image: { width: '100%', height: '100%' },
});
