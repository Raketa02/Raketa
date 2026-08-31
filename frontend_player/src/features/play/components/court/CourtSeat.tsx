/**
 * One seat of the interactive court — **a face, an identifier under it, and a tap.**
 *
 * [7.12](../../../../../docs/design-system.md#712-the-court) draws the line this file sits on:
 * *"the court owns geometry and knows nothing about players; a seat owns its label, its ring,
 * its badge and its taps."* So `Court` hands this component a box and a position, and
 * everything inside that box is here.
 *
 * ## The label is an identifier under a face, and it truncates
 *
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §5 settled the arithmetic that decides this. §15 killed first names — every sentence uses
 * the **whole handle**, 2 to 64 characters — and #219 B4 raised the floor to 9,5pt. Sixty-four
 * characters in a 46pt seat is about four, so the visible label is not the name and cannot be.
 *
 * > **It truncates to the seat's own width, one line, tail ellipsis, and the level comes off
 * > it. The whole handle is read off the lines already on screen.**
 *
 * Both screens the court appears on print the handles in full and unavoidably — the forecast
 * card's figures row and the pool header's seated-names line — so there is no legend to add
 * and no element to invent. **The spoken name is whole**: `seatLabel` composes the accessible
 * one, and a truncation of a *drawing* invents nothing, which is the only thing ADR-0107
 * forbids. **No `allowFontScaling={false}`** either — Part 13 permits that escape only inside
 * the level bar's drawn geometry, and `the-words.md` §20.4 already refused it here.
 *
 * The level comes off the visible label on §10's rule — a surface does not restate what it
 * already renders — and it is still in the seat's spoken name, where nothing else says it.
 *
 * ## It is `tag` and not mono, now that the level has gone
 *
 * The prototype drew this 9pt mono, and 1.4's *numbers are monospaced, always* is what mono is
 * for: a figure compared vertically against another figure. What is left after §5 takes the
 * level off is a **handle** — a word — and `tag` is the design system's 9,5pt word.
 *
 * ## Three rings, and `CourtMini` draws two of them
 *
 * They are [`seatRing.ts`](./seatRing.ts)'s, because the read-only court wears the same two —
 * §4's *the two courts share everything that is a number*, and 7.12 refuses to put a seat's
 * ring in the theme. What is here is which of the three this seat is wearing.
 */

import { StyleSheet, Text, View, Pressable } from 'react-native';

import { playerName } from '@/shared/formatting/playerName';
import { Plus, theme } from '@/shared/ui';

import type { SeatPlace } from '../../domain/lineup';
import type { UnfilledReason } from '../../domain/vocabulary';
import { clearSeatLabel, seatLabel, type SeatOccupant } from '../accessibilityPresentation';
import { CandidatePhoto, candidatePhotoRadius } from '../candidate/CandidatePhoto';

import { seatName } from './seatName';
import { seatRing } from './seatRing';

/**
 * Who is in a seat, as the **component** needs them.
 *
 * A superset of `domain/lineup`'s `BuildSeat`: the rules read the kind and the acceptance, and
 * everything else here is drawn. One type rather than two passed side by side, because a seat
 * that could be handed a `player` to draw and an `empty` to decide with is a seat that will be.
 */
export type CourtSeatOccupant =
  | {
      readonly kind: 'you';
      /**
       * Your own id.
       *
       * Your seat draws the **poster** and never a photograph: `photo_url` is minted for
       * another player's card row, nothing in a line-up carries yours, and `GET /photos/{id}`
       * signs your own by an id this component was never handed. A poster is a fact about an
       * id, so your seat is the one face on the court drawn from an id alone.
       */
      readonly playerId: string;
    }
  | {
      readonly kind: 'player';
      /** The poster's whole input when there is no photograph. */
      readonly playerId: string;
      /** The handle, whole. This component is the box that truncates it. */
      readonly nickname: string;
      readonly level: number;
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
 * The clear badge, as a share of the face it sits on.
 *
 * [6.9](../../../../../docs/design-system.md#69-the-photo-tile-and-picker)'s remove control is
 * the drawing — a solid `night` square carrying a white mark at the `tag` radius — and §4 says
 * so: *"the seat-clear badge is not a new component"*, and the prototype's 18px circle at
 * radius 9 is dropped. What does **not** carry across is 6.9's 28pt, which is a share of a
 * tile a third of the screen wide: at a 46pt seat the same square is the seat. So it is a
 * share of its own box, exactly as `CandidatePhoto`'s corner is, and it scales with the court
 * rather than being a fourth fixed number.
 *
 * **The target is grown by slop and not by the visual** — 6.5's rule, and the arithmetic below
 * is what 44 costs at whatever size the face turned out to be.
 */
const CLEAR_RATIO = 1 / 3;

/** 6.5's floor, which every target in this app is grown to rather than drawn at. */
const TARGET = 44;

const clearSize = (face: number) => Math.round(face * CLEAR_RATIO);

/** What the badge's visual is short of 44, split evenly around it. */
function clearSlop(face: number) {
  const grow = Math.max(0, (TARGET - clearSize(face)) / 2);
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
}

export function CourtSeat({ size, place, occupant, selected, onPress, onClear }: CourtSeatProps) {
  const radius = candidatePhotoRadius(size);
  const face = { width: size, height: size, borderRadius: radius };

  return (
    <View style={face}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={seatLabel(place, spoken(occupant))}
        accessibilityState={{ selected }}
        onPress={onPress}
        style={face}
      >
        {occupant.kind === 'empty' ? (
          // 6.9's add glyph, which is `Tick.tsx`'s crossed pair — the same drawing rather than
          // a second copy of it, which is what that file exists to prevent. Volt as a stroke,
          // legal on the one kind of bed it may be one on, and this is the court's.
          <View style={[face, s.emptyFace]}>
            <Plus />
          </View>
        ) : (
          <CandidatePhoto
            playerId={occupant.playerId}
            photoUrl={occupant.kind === 'you' ? undefined : occupant.photoUrl}
            box={{ kind: 'face', size }}
          />
        )}

        {/* Over the face rather than around it: a border on the box below would move the
            photograph in by two points the moment a seat was selected. */}
        <View
          style={[
            StyleSheet.absoluteFill,
            { borderRadius: radius },
            occupant.kind === 'empty' ? seatRing.empty : seatRing.seated,
            selected ? seatRing.selected : undefined,
          ]}
          pointerEvents="none"
        />
      </Pressable>

      {/* Under the face and outside the court's own box for this seat, which is the face and
          nothing more. Hidden, because the seat's spoken name already carries the whole
          handle and this is the same word cut short. */}
      <Text
        style={[s.label, { top: size + theme.space.xxs }]}
        numberOfLines={1}
        ellipsizeMode="tail"
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {seatName(occupant)}
      </Text>

      {onClear === undefined ? null : (
        <Pressable
          accessibilityRole="button"
          // The drawn word and the spoken name are one `playerName()` — §15's whole handle.
          // The box truncates it and the formatter never does, which is the whole of why a
          // seat label may be cut short and a sentence may not.
          accessibilityLabel={clearSeatLabel({ name: seatName(occupant), place })}
          onPress={onClear}
          hitSlop={clearSlop(size)}
          style={[s.clear, { width: clearSize(size), height: clearSize(size) }]}
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

/** What the seat **says**, which is never what it draws: the handle whole, and the level with it. */
function spoken(occupant: CourtSeatOccupant): SeatOccupant {
  switch (occupant.kind) {
    case 'you':
      return { kind: 'you' };
    case 'player':
      return {
        kind: 'player',
        name: playerName({ kind: 'player', nickname: occupant.nickname }),
        level: occupant.level,
      };
    case 'empty':
      return { kind: 'empty', unfilled: occupant.unfilled };
  }
}

const s = StyleSheet.create({
  emptyFace: { alignItems: 'center', justifyContent: 'center' },
  label: {
    ...theme.type.tag,
    ...theme.shadow.textOnMedia,
    position: 'absolute',
    left: 0,
    right: 0,
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
