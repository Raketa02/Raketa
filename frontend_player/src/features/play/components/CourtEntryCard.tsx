/**
 * **The way onto the court** — the control *Find a game* ends on, and the whole of the act.
 *
 * There is no *Search* button on that screen. The one thing a player can do there is run a
 * search, and where a completed search **goes** is the builder — so the control is a picture
 * of the court it is about to open rather than a verb naming the machinery underneath it
 * ([#268](https://github.com/Raketa02/Raketa/issues/268),
 * [#271](https://github.com/Raketa02/Raketa/issues/271)). It is the one way through for a
 * competitive game; the deck is the other half of `PlaySegment` and never a second copy of
 * this.
 *
 * ## What the picture is allowed to claim
 *
 * A court seating **you and nobody else**, at `theme.size.court.thumb`. Nothing on this
 * screen has asked the engine anything yet, so there is no line-up to draw and no faces to
 * put in the other seats — an empty seat on `CourtMini` is drawn as nothing at all, which is
 * exactly the honest picture. Your own seat draws its volt ring and **no face**: the searcher's
 * own player id is served by no route, so a faceless *you* is the state the read-only court
 * already has a word for.
 *
 * The sentence beside it carries the half a picture of four seats cannot say for itself —
 * *nobody is contacted until you send it* — because four seats with no such line reads as four
 * people about to be messaged.
 *
 * ## One element, one action
 *
 * `the-words.md` §20.1: *one accessibility element per action, and everything actionless
 * merges into the nearest action above it*. The card is one button, so the court inside it is
 * hidden from the tree — `Court` announces a summary of its own, and a listener navigating a
 * control has no use for a second name inside it. The three facts that summary would have
 * carried are in the card's own name instead (`courtEntryLabel`).
 *
 * ## The prototype's coral border is not drawn
 *
 * The web prototype outlined this card in 2pt coral to mark it as the way on. **Coral on a
 * card is the pressed state** ([5.1](../../../../docs/design-system.md#51-card--the-workhorse)),
 * and a resting border in the press colour would leave the one feedback a touch surface has
 * saying nothing. What carries the emphasis instead is the content: a heading, the hot tag
 * beside it, and a drawn court — none of which any other block on that screen has.
 */

import { StyleSheet, Text, View } from 'react-native';

import type { Sport } from '@/shared/vocabulary/sport';
import { PressableCard, Tag, theme } from '@/shared/ui';

import type { CourtFaceOccupant } from './court/seatFace';
import { CourtMini } from './court/CourtMini';
import { courtSummaryLabel } from './accessibilityPresentation';
import {
  courtEntryBody,
  courtEntrySeatLine,
  courtEntryTag,
  courtEntryTitle,
} from './findAGamePresentation';

/** The one seat that is filled before anything has been asked of the engine. */
const YOU: CourtFaceOccupant = { kind: 'you' };
const EMPTY: CourtFaceOccupant = { kind: 'empty' };

export interface CourtEntryCardProps {
  readonly sport: Sport;
  /** This app's word for that sport — the screen already drew it on a chip. */
  readonly sportName: string;
  /** The Sport's own seat count, read off `Court`'s coordinates by the screen. */
  readonly seats: number;
  /**
   * The card's spoken name — `searchControlLabel`'s, so a screen with something standing in
   * front of the search says *what* rather than presenting a court nobody can open yet.
   */
  readonly label: string;
  readonly disabled: boolean;
  readonly onPress: () => void;
}

export function CourtEntryCard({
  sport,
  sportName,
  seats,
  label,
  disabled,
  onPress,
}: CourtEntryCardProps) {
  return (
    <PressableCard style={s.card} accessibilityLabel={label} disabled={disabled} onPress={onPress}>
      <View style={s.head}>
        <Text style={s.title}>{courtEntryTitle(seats)}</Text>
        <Tag label={courtEntryTag({ seats, sportName })} variant="hot" />
      </View>

      <Text style={s.body}>{courtEntryBody(seats)}</Text>

      <View style={s.foot}>
        {/* §20.1 again: the court has no action of its own inside a button, so it merges
            into the one above it rather than announcing a summary a listener cannot act on. */}
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <CourtMini
            sport={sport}
            width={theme.size.court.thumb}
            summary={courtSummaryLabel({ sportName, filled: 1, seats })}
            seats={Array.from({ length: seats }, (_, at) => (at === 0 ? YOU : EMPTY))}
          />
        </View>

        <Text style={s.seatLine}>{courtEntrySeatLine(seats)}</Text>
      </View>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.xs },
  head: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: theme.space.xs,
  },
  title: { ...theme.type.h2, color: theme.color.ink, flexShrink: 1 },
  body: { ...theme.type.tiny, color: theme.color.ink },
  foot: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  /** `flex: 1`, so the sentence takes what the thumbnail leaves rather than the row growing. */
  seatLine: { ...theme.type.tiny, color: theme.color.muted, flex: 1 },
});
