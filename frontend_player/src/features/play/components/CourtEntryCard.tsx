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
 * ## A centred column, and what stopped being drawn beside things
 *
 * A title, what the court is for, and the court — stacked and centred on the axis the picture
 * is drawn on. It was two rows of furniture around those three: a hot pill beside the title
 * and a sentence beside the court. The pill said *padel is doubles* next to a court already
 * drawing four seats, which is the picture read back as a label, and *you pick the sides* next
 * to one drawing two, which is not a fact about the sport at all. The sentence said the shape
 * — again the picture — and *nobody is contacted until you send it*, which is true and is said
 * where sending is actually offered: `ProposeSheet` draws it over the control that contacts
 * somebody, two screens on. Nothing on this screen reaches another player, and a court seating
 * only you is not a claim that needs a disclaimer under it.
 *
 * ## One element, one action
 *
 * `the-words.md` §20.1: *one accessibility element per action, and everything actionless
 * merges into the nearest action above it*. The card is one button, so the court inside it is
 * hidden from the tree — `Court` announces a summary of its own, and a listener navigating a
 * control has no use for a second name inside it. What that summary would have said is in
 * the card's own name instead (`courtEntryLabel`).
 *
 * ## The prototype's coral border is not drawn
 *
 * The web prototype outlined this card in 2pt coral to mark it as the way on. **Coral on a
 * card is the pressed state** ([5.1](../../../../docs/design-system.md#51-card--the-workhorse)),
 * and a resting border in the press colour would leave the one feedback a touch surface has
 * saying nothing. What carries the emphasis instead is the content: a heading, a
 * sentence and a drawn court — none of which any other block on that screen has.
 */

import { StyleSheet, Text, View } from 'react-native';

import type { Sport } from '@/shared/vocabulary/sport';
import { PressableCard, theme } from '@/shared/ui';

import type { CourtFaceOccupant } from './court/seatFace';
import { CourtMini } from './court/CourtMini';
import { courtSummaryLabel } from './accessibilityPresentation';
import { courtEntryBody, courtEntryTitle } from './findAGamePresentation';

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
      <Text style={s.title}>{courtEntryTitle(seats)}</Text>

      <Text style={s.body}>{courtEntryBody(seats)}</Text>

      {/* §20.1 again: the court has no action of its own inside a button, so it merges
          into the one above it rather than announcing a summary a listener cannot act on. */}
      <View
        style={s.court}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <CourtMini
          sport={sport}
          width={theme.size.court.thumb}
          summary={courtSummaryLabel({ sportName, filled: 1, seats })}
          seats={Array.from({ length: seats }, (_, at) => (at === 0 ? YOU : EMPTY))}
        />
      </View>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  /** One column, centred: nothing is drawn beside anything, so nothing is ranged left. */
  card: { gap: theme.space.xs, alignItems: 'center' },
  title: { ...theme.type.h2, color: theme.color.ink, textAlign: 'center' },
  body: { ...theme.type.tiny, color: theme.color.ink, textAlign: 'center' },
  /** The picture is the end of the card and takes the step the removed row used to give it. */
  court: { paddingTop: theme.space.xs },
});
