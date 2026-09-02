/**
 * One seat of the interactive court — **a face, an identifier under it, and a tap.**
 *
 * [7.12](../../../../../docs/design-system.md#712-the-court) draws the line this file sits on:
 * *"the court owns geometry and knows nothing about players; a seat owns its label, its ring,
 * its badge and its taps."* So `Court` hands this component a box and a position, and
 * everything inside that box is here. The face and the ring are
 * [`seatFace.tsx`](./seatFace.tsx)'s, because the read-only court draws the same ones.
 *
 * ## The label is an identifier under a face, and it truncates
 *
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §5 settled the arithmetic that decides this. §15 killed first names — every sentence uses
 * the **whole handle**, 2 to 64 characters — and #219 B4 raised the floor to 9,5pt. Sixty-four
 * characters in a 46pt seat is about four, so the visible label is not the name and cannot be.
 *
 * > **It truncates to the seat's own width, one line, tail ellipsis. The whole handle is read
 * > off the lines already on screen.**
 *
 * Both screens the court appears on print the handles in full and unavoidably — the forecast
 * card's side rows and the pool header's seated-names line — so there is no legend to add and
 * no element to invent. **The spoken name is whole**: `seatLabel` composes the accessible one,
 * and a truncation of a *drawing* invents nothing, which is the only thing ADR-0107 forbids.
 * **No `allowFontScaling={false}`** either — Part 13 permits that escape only inside the level
 * bar's drawn geometry, and `the-words.md` §20.4 already refused it here.
 *
 * ## The level is drawn under the name, and that reverses §5
 *
 * §5 took it off on §10's rule — *a surface does not restate what it already renders* — and
 * that was right for a court under a card whose only figure was one percentage. The card now
 * prints **side strengths**, which is what a side is worth and not what anybody on it is
 * ([#290](https://github.com/Raketa02/Raketa/issues/290)): a player looking at `3,15` against
 * `3,15` cannot see which of the four is carrying it, and *who is strong here* is the question
 * a seat is the only place to answer. So there is nothing being restated — the two figures are
 * about different subjects — and the seat draws its own.
 *
 * It is **mono and tabular** because 1.4 is categorical about it: four levels are read down a
 * court against each other, which is exactly the comparison mono exists for. The name above it
 * stays `tag`, the design system's 9,5pt word, because a handle is a word.
 *
 * ## There is no hold on a seat, and the route it duplicated is now a face
 *
 * [#285](https://github.com/Raketa02/Raketa/issues/285) gave a seated player's Fit two ways
 * in: the forecast card's names row, and a **long press** on the seat as a shortcut to the
 * identical sheet. The shortcut is **gone**. The card's side rows now draw each player as
 * their own face and handle, which is a target nobody has to discover — where a hold is a
 * gesture with no affordance, no announcement, and no equivalent in the accessibility API at
 * all, so it was never reachable by the people who most needed the route.
 *
 * What replaced it is strictly larger: a 44pt control with a picture of the person on it.
 * Deleting the gesture rather than keeping it beside the face is the point — two ways to open
 * one sheet, one of them invisible, is a gesture nobody can be told about being kept because
 * it already exists.
 *
 * A tap on a seat is therefore **one act**: the pool, or a swap. Which of the two is
 * `tapSeat`'s, and it is unchanged.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';

import { Plus, theme } from '@/shared/ui';

import type { SeatPlace } from '../../domain/lineup';
import type { UnfilledReason } from '../../domain/vocabulary';
import { clearSeatLabel, seatLabel } from '../accessibilityPresentation';

import { SeatFace, seatBox } from './seatFace';
import { seatWho } from './seatWho';

/**
 * Who is in a seat, as the **interactive** court needs them.
 *
 * A superset of `domain/lineup`'s `BuildSeat` and of `seatFace.tsx`'s `CourtFaceOccupant`: the
 * rules read the kind and the acceptance, the drawing reads the id and the link, and the
 * sentences read the handle and the level. One type rather than three passed side by side,
 * because a seat that could be handed a `player` to draw and an `empty` to decide with is a
 * seat that eventually will be.
 */
export type CourtSeatOccupant =
  /** **The id is optional**, because no route serves a searcher their own — `seatFace.tsx`. */
  | { readonly kind: 'you'; readonly playerId?: string }
  | {
      readonly kind: 'player';
      /** The poster's whole input when there is no photograph. */
      readonly playerId: string;
      /**
       * The handle, whole. This component is the box that truncates it.
       *
       * **Absent, with the level and the photograph, when the search's record no longer holds
       * their row** — the withheld mark. The seat keeps its player and the forecast keeps its
       * number; what is gone is everything the card said about them, because a withheld row
       * carries one field and no card
       * ([`lineup.ts`](../../domain/lineup.ts)'s `withheldSeats`).
       */
      readonly nickname?: string;
      readonly level?: number;
      readonly photoUrl?: string;
      /** They already accepted: their seat is locked, and it draws no clear badge. */
      readonly accepted: boolean;
    }
  | {
      readonly kind: 'empty';
      /** §11's per-seat obstacle where the engine gave one; `null` where it was never filled. */
      readonly unfilled: UnfilledReason | null;
    };

/**
 * The clear badge, as a share of the face it sits on — **and the one target in this app that
 * cannot be grown to 44.**
 *
 * [6.9](../../../../../docs/design-system.md#69-the-photo-tile-and-picker)'s remove control is
 * the drawing, and §4 says so: *"the seat-clear badge is not a new component"* — a solid
 * `night` square carrying a white mark at the `tag` radius, and the prototype's 18px circle at
 * radius 9 dropped. What does **not** carry across is 6.9's 28pt and its 8pt slop, and the
 * arithmetic is why.
 *
 * > `theme.size.minTouch` is 44, and [6.5](../../../../../docs/design-system.md#65-touch-targets)
 * > anchors the photo tile's whole 44pt square **inside** the tile because a target may not
 * > take another control's area. On a court the control it would take from is the **seat
 * > underneath it**: React Native gives an overlap to the topmost sibling, so a 44pt square
 * > inset into a 46pt face leaves the seat a two-point border. Growing outward instead is
 * > worse than useless — a touch past a parent's bounds is never delivered, and `Court` sizes
 * > each seat's box to the face exactly.
 *
 * **So both targets cannot be 44 on one seat, and no arrangement makes them.** A face would
 * have to be at least `44 + 44` for a corner badge to leave the seat a clean square, and at
 * 23,5 % of the court's width that is a court 375pt wide — wider than the content width of the
 * phones this app runs on. The badge is therefore drawn at a third of the face and grown to
 * **half** of it: bounded by the seat rather than by the floor, which is 6.5's *"horizontal
 * slop is bounded by the neighbour"* read against the neighbour a court actually has. The seat
 * keeps everything else, which is most of it.
 *
 * **This is a design-system question rather than a component decision**, and it is recorded
 * here because §4 imported 6.9's numbers without running them against a 46pt box. The two ways
 * out are a wider court in the builder, and a badge that is not on the face at all.
 */
const CLEAR_RATIO = 1 / 3;

/** The badge's target as a share of the face: half, and the seat has the rest. */
const CLEAR_TARGET_RATIO = 1 / 2;

const clearSize = (face: number) => Math.round(face * CLEAR_RATIO);

/** What grows the visual to its target, split around it — 6.5's *visual small, target grown*. */
function clearSlop(face: number) {
  const grow = Math.max(0, (face * CLEAR_TARGET_RATIO - clearSize(face)) / 2);
  return { top: grow, bottom: grow, left: grow, right: grow };
}

export interface CourtSeatProps {
  /** The face, decided by the court from its own width. The seat never picks it. */
  readonly size: number;
  /** Side and role — `domain/lineup`'s `seatPlaces`, never an index. */
  readonly place: SeatPlace;
  readonly occupant: CourtSeatOccupant;
  /** Selected for a swap. §20.2's substitute for the `pressed` React Native does not ship. */
  readonly selected: boolean;
  readonly onPress: () => void;
  /**
   * Empty this seat.
   *
   * **Omitted is how a seat says it may not be emptied**, which is what keeps the refusals to
   * two: `seatIsClearable` decides, and the badge a player cannot use is never drawn.
   */
  readonly onClear?: () => void;
  /**
   * Explain the Fit of whoever is sitting here — the shortcut to `SH.whyfit`.
   *
   * **Omitted is how a seat says it has nothing to explain**, which is the clear badge's shape
   * for the same reason: a hold that opened an apology would be worse than a hold that does
   * nothing, and a gesture nothing advertises owes no sentence either way.
   */
}

export function CourtSeat({ size, place, occupant, selected, onPress, onClear }: CourtSeatProps) {
  const who = seatWho(occupant);
  const box = seatBox(size);

  return (
    <View style={box}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={seatLabel(place, who.spoken)}
        accessibilityState={{ selected }}
        onPress={onPress}
        // 6.6: touch has no hover, so the press is declared. The photo tile's `.7`, because
        // what dims is a photograph and this is the same rectangle at a quarter of the size.
        style={({ pressed }) => [box, pressed ? s.pressed : undefined]}
      >
        <SeatFace
          size={size}
          occupant={occupant}
          ring={selected ? 'selected' : occupant.kind === 'empty' ? 'empty' : 'seated'}
        >
          {/* 6.9's add glyph, which is `Tick.tsx`'s crossed pair — the same drawing rather than
              a second copy of it, which is what that file exists to prevent. Volt as a stroke,
              on the one kind of bed it may be one, and this is the court's.

              Drawn only for a seat that is **empty**: a face-less *you* is a seat nobody may
              fill, and a plus over it would be an invitation the truth table refuses. */}
          {occupant.kind === 'empty' ? <Plus /> : null}
        </SeatFace>
      </Pressable>

      {/* Under the face and outside the court's own box for this seat, which is the face and
          nothing more. Hidden, because the seat's spoken name already carries both the whole
          handle and the level — this is the same word cut short and the same figure. */}
      <View
        style={[s.caption, { top: size + theme.space.xxs }]}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Text style={s.label} numberOfLines={1} ellipsizeMode="tail">
          {who.name}
        </Text>
        {/* The Skill level, where the record still holds one. Absent on an empty seat, which
            has nobody to have one, and on a withheld one, whose card is gone with its handle. */}
        {who.level === undefined ? null : (
          <Text style={s.level} numberOfLines={1}>
            {formatLevel(who.level)}
          </Text>
        )}
      </View>

      {onClear === undefined ? null : (
        <Pressable
          accessibilityRole="button"
          // The drawn word and the spoken name are one `playerName()` — §15's whole handle.
          // The box truncates it and the formatter never does, which is the whole of why a
          // seat label may be cut short and a sentence may not.
          accessibilityLabel={clearSeatLabel({ ...(who.named ? { name: who.name } : {}), place })}
          onPress={onClear}
          hitSlop={clearSlop(size)}
          style={({ pressed }) => [
            s.clear,
            { width: clearSize(size), height: clearSize(size) },
            pressed ? s.pressed : undefined,
          ]}
        >
          {/* A multiplication sign, not a lowercase x — the x has a baseline and sits low. */}
          <Text style={s.clearMark} accessibilityElementsHidden importantForAccessibility="no">
            {'×'}
          </Text>
        </Pressable>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  // 6.6's photo-tile value, for both of this file's pressables.
  pressed: { opacity: 0.7 },
  caption: { position: 'absolute', left: 0, right: 0, alignItems: 'center' },
  label: {
    ...theme.type.tag,
    ...theme.shadow.textOnMedia,
    color: theme.color.surface,
    textAlign: 'center',
  },
  // Mono and tabular, because four of these are read down a court against each other — 1.4's
  // whole reason for mono, and the comparison the side strengths above cannot answer.
  level: {
    ...theme.num.xs,
    ...theme.tabular,
    ...theme.shadow.textOnMedia,
    color: theme.color.surface,
    textAlign: 'center',
  },
  clear: {
    position: 'absolute',
    top: 0,
    right: 0,
    borderRadius: theme.radius.tag,
    // Solid, for 6.9's reason: what is behind it is a photograph nobody has seen, and a
    // translucent control over one has an arbitrary contrast ratio.
    backgroundColor: theme.color.night,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clearMark: { ...theme.type.tag, color: theme.color.surface },
});
