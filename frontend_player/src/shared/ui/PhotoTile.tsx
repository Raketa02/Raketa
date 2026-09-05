/**
 * The photo tile and the row it lives in, per design-system 6.9.
 *
 * The tile is the unit: it holds a photo, or it is the control that adds one, or it is the
 * space where a photo would go. **The row is always three tiles, and that is where the
 * ceiling lives** — a filled tile shows its photo, the first empty slot is the add control,
 * and any slot after it is undrawn space. At three there is no add control on screen at
 * all, which is the same argument [6.1] makes against drawing a pressable-looking control
 * that refuses.
 *
 * ## One foot strip, three occupants, and at most one of them
 *
 * A settled, non-profile photo carries nothing. That is the whole reason the strip is one
 * slot and not three stacked badges: the tile that needs no explanation gets no furniture.
 *
 * **The strip is a solid fill and not a floating pill, because the photo behind it is
 * unknown.** A translucent badge over an arbitrary image has an arbitrary contrast ratio —
 * `onDarkTag` is computed against `night` and means nothing over a bright sky — and a
 * `line2` progress track is invisible on a photograph. On `night` or `red` the ratio is
 * fixed whatever the player photographed. The progress fill is white rather than `coral`
 * for the same kind of reason: [1.2] names the five places coral appears and an upload is
 * not one of them.
 *
 * ## Two acts, two targets, and a menu behind a hold
 *
 * The remove square is anchored **inside** the tile and RN gives the overlap to the child,
 * so the tile's own press area is the tile minus its top-right 44pt square — still more
 * than four times the minimum on the narrowest phone. Pressing that remainder promotes the
 * photo; pressing the square removes it.
 *
 * **Anything past those two is reached by holding the tile**, never by a third square. A
 * 3:4 tile a third of the row wide has room for two 44pt targets and the second is spoken
 * for, so a third would either overlap the remove control or shrink one of them below the
 * floor — which is the same arithmetic that put the remove square's slop *inside* the tile.
 * What the hold opens is the caller's (`options`), and because a long press is invisible and
 * unperformable by a screen reader, the prop carries the standard `longpress` accessibility
 * action in the same object: there is no way to wire the gesture and forget the name.
 *
 * **The promote affordance is a sentence, not a glyph.** Nothing is drawn on a non-profile
 * tile to advertise what pressing it does — the step carries one line of copy under the row
 * and every tile carries the same thing as a hint. A per-tile label would be that sentence
 * printed three times over the photographs it describes.
 *
 * **Every word is the caller's.** This file holds no copy at all: the strip's occupants,
 * the add control's word and every accessible name arrive as props, because the step that
 * collects photos and the profile editor that will change them do not say the same things.
 */

import { Children, type ReactNode } from 'react';
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { CourtPoster, type CourtPosterLook } from './CourtPoster';
import { theme } from './theme';

const tile = theme.size.photoTile;

/**
 * What is in the foot strip. At most one thing, ever — see the module note.
 *
 * `none` is a real arm rather than an optional prop: *a settled photo that is not the
 * profile photo* is a state the design system is explicit about, and it is easier to see
 * that it draws nothing when it is written down.
 */
export type PhotoTileFoot =
  | { readonly kind: 'none' }
  | { readonly kind: 'profile'; readonly word: string }
  /** `progress` is a fraction from 0 to 1. The bar is the only moving thing on the row. */
  | { readonly kind: 'uploading'; readonly progress: number }
  | { readonly kind: 'failed'; readonly word: string };

/**
 * A second act on the tile, reachable by holding it — and by an assistive technology.
 *
 * **One prop carrying both halves**, because a long press is invisible: nothing on the tile
 * advertises it and a screen reader cannot perform one. The gesture and the action that
 * stands in for it are therefore not separable, and a caller who supplies the handler cannot
 * forget the name — which is the shape [6.9] already applies to the remove square.
 */
export interface PhotoTileOptions {
  readonly onLongPress: () => void;
  /**
   * Names the action in the rotor, and it says *which photo* — the remove control's rule.
   * "More options" alone is three identical entries on a row of three.
   */
  readonly accessibilityLabel: string;
}

export interface PhotoTileProps {
  /** What the tile draws — the device's own copy, not a URL fetched back from the store. */
  readonly uri: string;
  /**
   * Whether this is the profile photo, which changes **only the border colour**.
   *
   * Separate from `foot`, and not derived from it: a photo can be the profile photo while
   * it is still uploading, and the strip has room for one of those two facts.
   */
  readonly profile: boolean;
  readonly foot: PhotoTileFoot;
  /** The tile minus the remove square. Promotion, or a retry on a failed tile. */
  readonly onPress: () => void;
  /**
   * What holding the tile opens, if anything. Absent leaves the tile with its two acts.
   *
   * It is deliberately not a third target: the tile has room for two 44pt squares and the
   * second is spoken for (see the module note), so the way to reach anything beyond promote
   * and remove is the gesture — and, for whoever cannot make one, the accessibility action
   * this carries.
   */
  readonly options?: PhotoTileOptions;
  readonly onRemove: () => void;
  /** Names the position and whatever the strip is carrying — neither is legible otherwise. */
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
  /** Names *which* photo is removed. "Remove" alone says nothing out of visual context. */
  readonly removeAccessibilityLabel: string;
}

export function PhotoTile({
  uri,
  profile,
  foot,
  onPress,
  options,
  onRemove,
  accessibilityLabel,
  accessibilityHint,
  removeAccessibilityLabel,
}: PhotoTileProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      onLongPress={options?.onLongPress}
      // The standard `longpress` action, so the gesture is not the only way in: VoiceOver
      // and TalkBack both surface it, and neither can hold a control down.
      accessibilityActions={
        options === undefined
          ? undefined
          : [{ name: 'longpress', label: options.accessibilityLabel }]
      }
      onAccessibilityAction={
        options === undefined
          ? undefined
          : (event) => {
              if (event.nativeEvent.actionName === 'longpress') options.onLongPress();
            }
      }
      style={({ pressed }) => [
        s.tile,
        profile ? s.profileTile : s.photoTile,
        pressed ? s.pressed : undefined,
      ]}
    >
      <Image
        source={{ uri }}
        style={s.image}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />

      <FootStrip foot={foot} />

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={removeAccessibilityLabel}
        onPress={onRemove}
        // Anchored inside the tile rather than over its corner: at a 9pt gap an
        // overhanging target would reach 40,5pt, and the 4,5pt it took would be the next
        // tile's. The inset in `s.remove` is what keeps the whole square this tile's own.
        hitSlop={theme.hit.photoRemove}
        style={({ pressed }) => [s.remove, pressed ? s.pressed : undefined]}
      >
        <Text style={s.removeMark} accessibilityElementsHidden importantForAccessibility="no">
          {'×'}
        </Text>
      </Pressable>
    </Pressable>
  );
}

/**
 * The strip, or nothing at all.
 *
 * Hidden from assistive technology in every arm: the tile's own name carries what the strip
 * says, because a screen reader meeting a bar and a word inside a button would read the
 * button's name and then two fragments of it again.
 */
function FootStrip({ foot }: { readonly foot: PhotoTileFoot }) {
  if (foot.kind === 'none') return null;

  return (
    <View
      style={[s.strip, foot.kind === 'failed' ? s.stripFailed : s.stripSettled]}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      {foot.kind === 'uploading' ? (
        <View style={s.progressTrack}>
          <View style={[s.progressFill, { width: `${clamp(foot.progress) * 100}%` }]} />
        </View>
      ) : (
        <Text style={s.stripWord} numberOfLines={1}>
          {foot.word}
        </Text>
      )}
    </View>
  );
}

function clamp(fraction: number): number {
  return Math.min(Math.max(fraction, 0), 1);
}

export interface PhotoPosterTileProps {
  /**
   * `undefined` while whoever the poster is for is still being read.
   *
   * The slot is drawn either way, and that is the point: the poster's place in the row is
   * decided by there being no photograph, not by an answer having arrived, and a slot that
   * appeared a moment later would move the add control out from under a finger.
   */
  readonly poster: CourtPosterLook | undefined;
  /** Must say the picture is generated. `CourtPoster` explains why. */
  readonly accessibilityLabel: string;
}

/**
 * The generated poster, standing where the profile photo would be.
 *
 * A player who adds nothing is not left with an empty box, so the first slot of an empty
 * row is theirs rather than blank — and it is the *first* slot because that is where a
 * profile photo goes, which is the whole claim the poster makes. It disappears the moment
 * a real photo takes that place.
 *
 * **It is not pressable and carries no strip.** There is nothing to promote it above and
 * nothing to remove, and a control that looked like the two tiles beside it while doing
 * neither would be the worst kind of furniture. It takes the plain `line` border rather
 * than the profile tile's `ink` one for the same reason: `ink` marks the photo a player
 * chose to lead with, and nobody chose this.
 */
export function PhotoPosterTile({ poster, accessibilityLabel }: PhotoPosterTileProps) {
  return (
    <View style={[s.tile, s.photoTile, poster === undefined ? s.posterGround : undefined]}>
      {poster === undefined ? null : (
        <CourtPoster hue={poster.hue} pose={poster.pose} accessibilityLabel={accessibilityLabel} />
      )}
    </View>
  );
}

export interface PhotoAddTileProps {
  /** A `tag`-sized word under the glyph. The caller's, like everything else here. */
  readonly word: string;
  readonly onPress: () => void;
  /** Says how many slots remain — the row's own arithmetic is invisible otherwise. */
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
}

/**
 * The add control: the leftmost empty slot, and there is never more than one.
 *
 * It sits on `paper2` because `paper2` is the recessed surface — a hole you put something
 * into, not a card you press — and it takes the **card's** coral-border press state rather
 * than the chip's fade, because unlike a filled tile its border is not already saying
 * something else.
 */
export function PhotoAddTile({
  word,
  onPress,
  accessibilityLabel,
  accessibilityHint,
}: PhotoAddTileProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      style={({ pressed }) => [s.tile, s.addTile, pressed ? s.addPressed : undefined]}
    >
      <View style={s.glyph} accessibilityElementsHidden importantForAccessibility="no">
        <View style={s.glyphBar} />
        <View style={[s.glyphBar, s.glyphBarUpright]} />
      </View>
      <Text style={s.addWord} numberOfLines={1}>
        {word}
      </Text>
    </Pressable>
  );
}

/**
 * The row: whatever the caller drew, padded out to three slots with undrawn space.
 *
 * **A placeholder is not a second add control, and it is not a surface either.** It is
 * empty space of a tile's dimensions with the paper showing through: borderless, glyphless,
 * not pressable, and hidden from assistive technology. What it is for is the row's rhythm —
 * three slots that do not move as photos arrive — and space does that as well as a
 * rectangle would, while saying the honest thing, which is that nothing is there.
 *
 * The padding happens here rather than at the call site so that *always three* is a fact
 * about the row rather than a loop every caller writes again.
 */
export interface PhotoRowProps {
  readonly children: ReactNode;
  readonly style?: StyleProp<ViewStyle>;
}

export function PhotoRow({ children, style }: PhotoRowProps) {
  const drawn = Children.toArray(children);
  const missing = Math.max(tile.columns - drawn.length, 0);

  return (
    <View style={[s.row, style]}>
      {drawn}
      {Array.from({ length: missing }, (_unused, at) => (
        <View
          key={`slot-${at}`}
          style={s.tile}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', gap: tile.gap },
  tile: {
    flex: 1,
    aspectRatio: tile.aspectRatio,
    borderRadius: theme.radius.card,
    // The strip reaches the tile's edges and takes the tile's bottom corners with it.
    overflow: 'hidden',
  },
  photoTile: { borderWidth: 1, borderColor: theme.color.line },
  // The poster's ground, before there is a poster. Not a spinner: nothing is being waited
  // for that the player asked for, and a court appearing on a dark tile is the whole of
  // what happens next.
  posterGround: { backgroundColor: theme.color.night },
  // Promotion changes the border's COLOUR and never its width, so a photo does not resize
  // by a point when it starts leading.
  profileTile: { borderWidth: 1, borderColor: theme.color.ink },
  pressed: { opacity: 0.7 },
  // Fills the tile; RN's default resize mode is `cover`, so the photograph is cropped
  // rather than squashed into a 3:4 that is not its own.
  image: StyleSheet.absoluteFillObject,

  strip: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: tile.strip,
    paddingHorizontal: tile.progressInset,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stripSettled: { backgroundColor: theme.color.night },
  stripFailed: { backgroundColor: theme.color.red },
  stripWord: { ...theme.type.tag, color: theme.color.surface },

  progressTrack: {
    width: '100%',
    height: tile.progressBar,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.onDarkHair,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.surface,
  },

  remove: {
    position: 'absolute',
    // Inset by exactly its own slop, which is what puts the whole 44pt square inside the
    // tile: 8 + 28 + 8 = 44, and none of it crosses an edge into the 9pt gap (6.5).
    top: theme.hit.photoRemove.top,
    right: theme.hit.photoRemove.right,
    width: tile.remove,
    height: tile.remove,
    borderRadius: theme.radius.tag,
    // Solid, for the strip's reason: what is behind it is a photograph nobody has seen,
    // and a translucent mark over one has an arbitrary contrast ratio.
    backgroundColor: theme.color.night,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // A multiplication sign, not a lowercase x — the x has a baseline and sits low.
  removeMark: { ...theme.type.h2, color: theme.color.surface },

  addTile: {
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.space.xs,
  },
  addPressed: { borderColor: theme.color.coral },
  glyph: {
    width: tile.addGlyph,
    height: tile.addGlyph,
    alignItems: 'center',
    justifyContent: 'center',
  },
  glyphBar: {
    position: 'absolute',
    width: tile.addGlyph,
    height: tile.addGlyphStroke,
    backgroundColor: theme.color.muted,
  },
  glyphBarUpright: { width: tile.addGlyphStroke, height: tile.addGlyph },
  addWord: { ...theme.type.tag, color: theme.color.muted },
});
