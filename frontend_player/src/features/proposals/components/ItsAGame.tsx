/**
 * ***It's a game!*** — the yes screen's third face, for the player whose yes filled a game
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4; the mechanics §11.3;
 * [ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)).
 *
 * *Today's yes screen, with the new word*: the dark ground and its glow, your side sliding in from
 * the left and theirs from the right, `vs` between, the one lime word rising, two pills — **Open
 * game** and **Later**. Nothing else: the player knows the game, and everybody else is told by the
 * notice *It's a game! · you paid*, never this screen.
 *
 * ## The faces are the card's
 *
 * Drawn off the card the yes was said on — the reader's own version, the one the last yes filled,
 * whose rows are the sides the booking drew (`itsAGamePicture`) — with every photograph it carries,
 * the reader's own among them. Nothing is read: the screen is up the moment the answer is.
 *
 * ## An overlay over the phone, not a route
 *
 * The fill answers wherever the player is by then — the deck, a game's details, another tab, ten
 * seconds after the swipe — so the screen is raised by the fill's host, on `ModalStage`'s top layer
 * over the whole phone (the bar included), rather than pushed onto a stack it does not belong to.
 * **Open game** lays Home down and pushes the game over it, so back from the game is Home, where a
 * booked game lives (A2.4); **Later** and Android's back take it away and leave the player where
 * they were. It is one-shot: nothing re-shows it.
 *
 * A listener hears the picture once, as the header's sentence — *It's a game! You and Zofia
 * Bielecka against Ania Kowalska and Ewa Majewska* — built from whole Names (ADR-0167 §3).
 */

import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { YesEntrance, YesGround, YesTile, type YesSeat } from '@/features/challenges/types';
import { Button, ModalStage, theme, useLiveRegion } from '@/shared/ui';

import type { DeckCard } from '../domain/deck';
import { itsAGamePicture, type Face } from '../domain/fill';

import { FILL_COPY } from './fillCopy';
import { itsAGameSentence } from './fillPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

export interface ItsAGameProps {
  /** The card the filling yes was said on. */
  readonly card: Pick<DeckCard, 'sides'>;
  readonly onOpenGame: () => void;
  /** *Later*, and Android's back. */
  readonly onLater: () => void;
}

export function ItsAGame({ card, onOpenGame, onLater }: ItsAGameProps) {
  const picture = itsAGamePicture(card);
  const sentence = itsAGameSentence(picture);
  const size =
    picture.yours.length + picture.theirs.length > 2
      ? theme.size.yesTile.doubles
      : theme.size.yesTile.singles;

  useLiveRegion(sentence);

  return (
    <ModalStage visible onRequestClose={onLater} animationType="none" layer="popover">
      <View style={s.screen} testID="its-a-game">
        <StatusBar style="light" />
        <YesGround />
        <SafeAreaView style={s.frame} edges={['top', 'bottom']}>
          <YesEntrance
            ready
            label={sentence}
            left={<Side faces={picture.yours} size={size} />}
            between={<Text style={s.vs}>{PROPOSALS_COPY.versus}</Text>}
            right={<Side faces={picture.theirs} size={size} />}
            word={<Text style={s.word}>{FILL_COPY.itsAGame.word}</Text>}
            buttons={
              <View style={s.doors}>
                <Button
                  label={FILL_COPY.itsAGame.open}
                  variant="volt"
                  shape="pill"
                  size="lg"
                  onPress={onOpenGame}
                />
                <Button
                  label={FILL_COPY.itsAGame.later}
                  variant="onDark"
                  shape="pill"
                  size="lg"
                  onPress={onLater}
                />
              </View>
            }
          />
        </SafeAreaView>
      </View>
    </ModalStage>
  );
}

function seatOf(face: Face): YesSeat {
  return {
    kind: 'person',
    playerId: face.playerId,
    ...(face.name === undefined ? {} : { name: face.name }),
    ...(face.photoUrl === undefined ? {} : { photoUrl: face.photoUrl }),
  };
}

/** One side — one tile in singles, two a small step apart in doubles. */
function Side({ faces, size }: { readonly faces: readonly Face[]; readonly size: number }) {
  return (
    <View style={s.side}>
      {faces.map((face) => (
        <YesTile key={face.playerId} seat={seatOf(face)} size={size} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  // The whole phone: the overlay's stage is the screen.
  screen: { ...StyleSheet.absoluteFillObject },
  frame: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.size.gutter,
  },
  side: { flexDirection: 'row', gap: theme.space.xs },
  // The yes screen's own `vs` and word (ADR-0167): h2 in the on-dark eyebrow grey, and the lime word.
  vs: { ...theme.type.h2, color: theme.color.onDarkEyebrow },
  word: { ...theme.type.yesWord, color: theme.color.volt },
  doors: { flexDirection: 'row', gap: theme.space.xs },
});
