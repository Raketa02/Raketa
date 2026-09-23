/**
 * The **deck** card — the photograph, or the poster, edge to edge, with a wash rising from the
 * bottom and one person's facts over it. The app's second dark surface, and it is a surface
 * ([ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7).
 *
 * The third of the three renderings of a candidate, and the only one that **floats**: it is
 * dragged, settles and flies under the thumb — a transient object being manipulated rather than
 * a surface a finger rests on, which is the whole of
 * [#219](https://github.com/Raketa02/Raketa/issues/219) B3's argument and the reason it is the
 * only user of `radius.deckCard` and the fourth shadow
 * ([4.3](../../../../../docs/design-system.md#43-elevation) is not bent here — a deck card is
 * not a card).
 *
 * ## What it draws, top to bottom, and where each comes from
 *
 * `PlayerPhoto` full-bleed — the photograph, or the poster when there is none, initials never
 * (ADR-0167 §3's fence). Over it, top-left, the **Level** in the existing 40pt figure with the
 * **Sport** under it, and top-right the **on-court mark** with its tick — both in `surface`
 * with the text shadow the app already has for text on media, and **no top wash**, because the
 * mock has none. Then the wash, and on it: the **name** in the card's one ~24pt role beside the
 * existing **Fit pill**; the **meta line** — *In your area · 1,9 km · around this week*, each
 * clause only where it is true; the **intro** in quotes, where they wrote one; up to six
 * **tags**, the shared ones first and volt with *· you too*; and **three tiles**, always three,
 * with a dash where a number is absent. **No** *They already said yes to you* and **no** *Wants
 * to play you* tag: the liker is unmarked and placed by the nudge (§4), and the count of them is
 * the chip's. **No hint line** under the tiles either, since 2026-09-15: the mock's *Drag the
 * card, or use the buttons · long-press for the full record* was a sentence of instructions on
 * every card, and the three buttons under the stage — the **i** among them — are the paths it
 * named, standing where a first-time thumb finds them.
 *
 * ## The wash is a ramp, and its worst case is stated at the name
 *
 * `photoScrim` is a flat tint pinned so that white over the worst photograph is computable.
 * This is a scrim over a picture a player is deciding about, and a face wants the whole card —
 * so the wash **ramps**: nothing at forty per cent of the card's height, `deckWash` (ink at
 * .94) at seventy, and held to the foot. The name's top edge sits at about sixty-two per cent
 * in the mocks, where the ramp is at seven tenths of its strength — ink at about .69 over any
 * ground, which is the panel's own pin within a rounding — and everything below the name sits
 * on the ramp's flat. The text shadow is on every label over the photograph, above and below
 * the wash. Drawn with the SVG the poster and the yes ground already use, in the card's own
 * bounding box, so the stops are shares of the card's height and nothing measures the phone.
 *
 * ## One element, and the long press is its action
 *
 * The body is one accessibility element named by `deckCardFacts` — the tiles, the tags, the
 * pill and the mark merge into it (§20.1) — and its **action is the long press**, which opens
 * the record sheet: the reading the card cannot fit, with the Fit's breakdown one row further
 * in. The three buttons below the stage are the other three elements. A card **behind** the
 * top one has no action and is no element — and is hidden from assistive technology by the
 * stage besides; it is drawn by the same component with no `onLongPress`, so a card behind and
 * the card in front are one drawing. **The same tree, too**: the stage promotes the card behind
 * in place when the top one has gone, and it takes on the action as the element it already was,
 * so its photograph is not decoded again over the person who was plainly there a frame ago.
 *
 * ## The gesture is the stage's, and the card knows nothing of it
 *
 * The drag, the stamps, the flight and the settle are `DeckStage`'s. The card is the thing under
 * the thumb and states no threshold, no direction and no answer; that is what lets the same
 * card stand behind the top one, still, at a smaller scale.
 */

import { useId, type RefObject } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { FitPill, OnCourtMark, PlayerPhoto, SocialTagRow, theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Term } from '../../domain/vocabulary';

import { DeckTileRow } from './DeckTile';
import { deckCardFacts } from './deckCardFacts';

/**
 * See {@link CandidateCard}'s set: exported by the component that draws these rows. The deck
 * card draws no reason line at all, so the set is what it **states** — as a figure, a tile or
 * the meta line — and it is here for the tests that hold every card to it.
 */
export const DECK_CARD_DRAWS: readonly Term[] = [
  'LEVEL_FIT',
  'PREDICTED_BALANCE',
  'AVAILABILITY_OVERLAP',
  'DISTANCE',
  'RELIABILITY',
];

/**
 * The wash's ramp, as shares of the card's height: nothing above `from`, full at `full`, held
 * to the foot. See the module note for the arithmetic at the name.
 */
const WASH = { from: 0.4, full: 0.7 } as const;

export interface DeckCardProps {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** The sport the deck is on — the surface's, printed under the Level. */
  readonly sportName: string;
  /**
   * The body's own action — a long press opens the record sheet. **Absent on a card behind**,
   * which is then a drawing with no element in it.
   */
  readonly onLongPress?: () => void;
  /**
   * A handle on the body, so the deck can move accessibility focus **onto the card that
   * arrives**.
   *
   * §E3's first finding is that focus is destroyed on every render and nothing restores it,
   * so a listener who answers a card is dropped at the root with no idea what happened. The
   * announcement says what happened and this is where focus goes — and it is the *body*,
   * because the body is the element that says who this is (§20.5). The screen owns the
   * moving; the card owns which element is worth moving to, which is why this is a prop.
   */
  readonly bodyRef?: RefObject<View>;
}

export function DeckCard({ candidate, envelope, sportName, onLongPress, bodyRef }: DeckCardProps) {
  const facts = deckCardFacts(candidate, envelope);
  // Per instance, as the poster's is: two of these are on screen behind a third.
  const wash = `${useId()}-wash`;

  const drawing = (
    <>
      <View style={StyleSheet.absoluteFill}>
        <PlayerPhoto
          playerId={candidate.playerId}
          photoUrl={candidate.card.photoUrl}
          box={{ kind: 'media' }}
        />
      </View>

      {/* The wash: one gradient in the card's own box, so its stops are shares of the height.
          `preserveAspectRatio="none"` is what makes a 1 × 1 drawing fill whatever the card is. */}
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
          <Defs>
            <LinearGradient id={wash} x1="0" y1="0" x2="0" y2="1">
              <Stop offset={WASH.from} stopColor={theme.color.deckWash} stopOpacity={0} />
              <Stop offset={WASH.full} stopColor={theme.color.deckWash} stopOpacity={1} />
              <Stop offset={1} stopColor={theme.color.deckWash} stopOpacity={1} />
            </LinearGradient>
          </Defs>
          <Rect x={0} y={0} width={1} height={1} fill={`url(#${wash})`} />
        </Svg>
      </View>

      <View style={s.head}>
        <View style={s.rating}>
          <Text style={s.level}>{formatLevel(candidate.card.level)}</Text>
          <Text style={s.sport} numberOfLines={1}>
            {sportName}
          </Text>
        </View>
        {facts.onCourt ? <OnCourtMark on="deck" /> : null}
      </View>

      <View style={s.foot}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {facts.name}
          </Text>
          <FitPill fit={candidate.fit} />
        </View>

        {facts.meta === undefined ? null : <Text style={s.meta}>{facts.meta}</Text>}

        {/* Present only when the field is — a player who skipped has no line, and the card
            closes the gap rather than quoting nothing (ADR-0170). */}
        {facts.intro === undefined ? null : <Text style={s.intro}>{facts.intro}</Text>}

        <SocialTagRow row={facts.tags} onDark />

        <DeckTileRow tiles={facts.tiles} />
      </View>
    </>
  );

  const inFront = onLongPress !== undefined;

  return (
    <View style={s.card}>
      {/* The clip is a second view rather than a style on the card, because a shadow and an
          `overflow: hidden` on one layer are a shadow drawn against a clipped bound — the same
          reason the sheet and the toast keep their own. One pressable whether the card is in
          front or behind, and never a plain view for the card behind: a different element would
          throw the drawing away on the frame the card comes forward. Behind, it is inert and no
          element — not accessible, no role, nothing to press. */}
      <Pressable
        ref={bodyRef}
        style={s.clip}
        accessible={inFront}
        accessibilityLabel={facts.label}
        disabled={!inFront}
        {...(inFront ? { accessibilityRole: 'button' as const, onLongPress } : {})}
      >
        {drawing}
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: theme.radius.deckCard,
    backgroundColor: theme.color.paper2,
    ...theme.shadow.deckCard,
  },
  clip: {
    flex: 1,
    borderRadius: theme.radius.deckCard,
    overflow: 'hidden',
    justifyContent: 'space-between',
  },
  head: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: theme.space.sm,
    padding: theme.space.lg,
  },
  rating: { flexShrink: 1 },
  // The existing 40pt figure and the existing text shadow: over the un-washed top of a
  // photograph, the Level and the mark take what every label over generated media takes.
  level: {
    ...theme.num.levelHero,
    ...theme.tabular,
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
  // `eyebrow` rather than the panel's `tag`: the panel's tracking argument is about 74pt, and
  // the card has the width the mock's tracked capitals want.
  sport: {
    ...theme.type.eyebrow,
    textTransform: 'uppercase',
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
  foot: {
    gap: theme.space.sm,
    padding: theme.space.lg,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  name: {
    ...theme.type.deckName,
    color: theme.color.surface,
    flexShrink: 1,
    ...theme.shadow.textOnMedia,
  },
  meta: { ...theme.type.tiny, color: theme.color.onDarkTiny, ...theme.shadow.textOnMedia },
  // Upright, in the card's quotation marks. The mocks set the line in italics, and this app
  // loads no italic Archivo — a `fontStyle` on a custom family is ignored on Android and
  // synthesised on iOS, which is two drawings of one line — so the marks carry *their words*
  // and the ninth font file is the author's call at the look (Part 16).
  intro: {
    ...theme.type.rlLabel,
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
});
