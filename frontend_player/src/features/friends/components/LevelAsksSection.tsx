/**
 * **ASKED FOR A LEVEL · n** — Needs your answer's section of a friend's asks for a level, one tile
 * per sport, after FRIEND REQUESTS ([#816](https://github.com/Rakieta02/Rakieta/issues/816),
 * ADR-0205 §1; the friends screens §6.4; the mechanics §5.1; the words §29.5). It was Home's row,
 * between FRIEND REQUESTS and Your games, from #765.
 *
 * ```
 * ASKED FOR A LEVEL · 1
 * ┌──────────────────────────────────────┐
 * │ ┌──┬──┬────┐ tomek.k, kuba.w and 2   │
 * │ │fa│fa│face│ more want to play padel │
 * │ └──┴──┴────┘ with you                │
 * │ ┌─ Not now ─┐ ┌─ Get your padel level ┐
 * └──────────────────────────────────────┘
 * ```
 *
 * ## A request tile
 *
 * **It is the request tile** (friends 5; the screens §6.4's call): faces, the title, **Not now**
 * (outline) and the coral button, bounded in `ink` — a tile waiting on the reader — on the same
 * wider rail (`wide`), as tall as the tallest, the buttons at the foot and the title held to two
 * lines (Q3). **No group is named, and no line runs under the title** (ADR-0205 §1): *A few
 * questions, and they can add you to a game.* and *You're on question 5.* are gone. The section and
 * its title are there only while Home's read holds a tile: nothing while it is in flight, refused or
 * empty. The read is Home's (`proposals`' `useHomeLevelAsks`), the sport with the newest ask first,
 * and nothing re-sorts it.
 *
 * ## The faces
 *
 * **Up to three, newest first, overlapping** a third of a face, each ringed in the tile's white so
 * one reads as in front of the next (`groups`' `FaceStack`'s drawing), at the request tile's 38. The
 * newest is at the back, as every stack in the app draws its first. **Each is its own press**, and
 * opens that friend's record: the face in front keeps its whole 38, and each behind it the 26 it
 * shows — under 6.5's 44 across, a call recorded in Part 16, since a stack whose faces each answer
 * cannot give each one 44 without ceasing to overlap.
 *
 * ## The coral button is the notice's act, started outside the sheet
 *
 * **Get your padel level** and **Carry on** both run what the *level asked* notice runs
 * (`useGetAskedLevel`): the sport's questionnaire, its unfinished run handed back if there is one,
 * the pass returning to Home. **The start is the shell's to run** (`onStart`, with `starting`
 * handed in): it navigates, and nothing inside a sheet does (`docs/architecture.md` Part 13), so
 * the shell calls the hook outside the sheet, closes the sheet for good and starts. The tile draws
 * **Carry on** as soon as a run left halfway in the sport is read (`useQuestionLeftAt`): a press
 * before that opens the same run. Another tile's button is disabled while a start is in flight.
 *
 * ## Not now
 *
 * **Sets the sport's asks aside**, then says where the level still is — *You can get your padel level
 * any time, from You › Skill passport.*, neutral and held to be read — and re-reads Home and the
 * bell (`useSetAsideLevelAsks`). It stays busy until Home no longer holds the tile.
 *
 * ## The record and the bell are handed in
 *
 * A face opens `player_record`'s record sheet, which draws this feature's record button, and the
 * bell is `notifications'` — so the shell, which composes the sheet, hands both in (`onFace`,
 * `onAnswered`), as it does to FRIEND REQUESTS.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { STARTING_LABEL, sportInLine, useQuestionLeftAt } from '@/features/onboarding/types';
import { useHomeLevelAsks, type HomeLevelAsk } from '@/features/proposals/types';
import { showToast } from '@/shared/store/toast.store';
import {
  Button,
  Card,
  HomeRow,
  HomeRowRail,
  PlayerPhoto,
  playerPhotoRadius,
  theme,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { facesOnTheCard } from '../domain/levelAsk';
import { useSetAsideLevelAsks } from '../hooks/useFriendWrites';

import {
  FRIENDS_COPY,
  getYourLevelLabel,
  levelAsksHeading,
  notNowLevelAskLabel,
  setAsideToast,
  wantToPlay,
} from './friendsCopy';
import { ROW_FACE } from './PersonRow';
import { REQUEST_TILE as tile, TITLE_LINES } from './requestTile';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.levelAsks;

export interface LevelAsksSectionProps {
  /** A tap on a face: that friend's record. */
  readonly onFace: (playerId: string) => void;
  /** **The bell's re-read**, handed in by the shell: the server takes the asks' rows off it. */
  readonly onAnswered: () => Promise<unknown>;
  /**
   * **The coral button: the sport's questionnaire**, run by the shell outside the sheet
   * (`useGetAskedLevel`), which closes the sheet for good as it starts.
   */
  readonly onStart: (sport: Sport) => void;
  /** The sport whose start is in flight — `useGetAskedLevel`'s `starting`. */
  readonly starting: Sport | undefined;
}

export function LevelAsksSection({ onFace, onAnswered, onStart, starting }: LevelAsksSectionProps) {
  const asks = useHomeLevelAsks();

  if (asks === undefined || asks.length === 0) return null;

  return (
    <HomeRow heading={levelAsksHeading(asks.length)} testID="level-asks">
      <HomeRowRail cards={asks} geometry="wide">
        {(ask, width) => (
          <LevelAskTile
            key={ask.sport}
            ask={ask}
            width={width}
            starting={starting}
            onStart={() => onStart(ask.sport)}
            onFace={onFace}
            onAnswered={onAnswered}
          />
        )}
      </HomeRowRail>
    </HomeRow>
  );
}

interface LevelAskTileProps {
  readonly ask: HomeLevelAsk;
  readonly width: number;
  readonly starting: Sport | undefined;
  readonly onStart: () => void;
  readonly onFace: (playerId: string) => void;
  readonly onAnswered: () => Promise<unknown>;
}

function LevelAskTile({ ask, width, starting, onStart, onFace, onAnswered }: LevelAskTileProps) {
  const sport = sportInLine(ask.sport);
  const question = useQuestionLeftAt(ask.sport);
  // The toast rides in the write itself: the tile unmounts once Home has re-read, and a press's own
  // callbacks would go with it.
  const settingAside = useSetAsideLevelAsks(ask.sport, onAnswered, () =>
    showToast({ message: setAsideToast(sport), hold: 'read' }),
  );
  const nicknames = ask.askers.map((asker) => asker.nickname);
  const startingHere = starting === ask.sport;
  // Another tile's start is in flight: this one's press would do nothing, so it says so.
  const elsewhere = starting !== undefined && !startingHere;
  const busy = startingHere || settingAside.isPending;

  return (
    <Card style={[tile.tile, { width }]}>
      <View style={tile.top} testID={`level-ask-${ask.sport}`}>
        <View style={s.faces}>
          {facesOnTheCard(ask.askers).map((asker, at) => (
            <Pressable
              key={asker.playerId}
              accessibilityRole="button"
              accessibilityLabel={asker.nickname}
              onPress={() => onFace(asker.playerId)}
              hitSlop={theme.hit.peopleRow}
              style={({ pressed }) => [
                s.face,
                at > 0 ? s.overlap : undefined,
                pressed ? tile.pressed : undefined,
              ]}
            >
              <PlayerPhoto
                playerId={asker.playerId}
                {...(asker.photoUrl === undefined ? {} : { photoUrl: asker.photoUrl })}
                box={{ kind: 'face', size: ROW_FACE }}
              />
            </Pressable>
          ))}
        </View>
        <Text style={[tile.title, s.who]} numberOfLines={TITLE_LINES}>
          {wantToPlay(nicknames, sport)}
        </Text>
      </View>

      <WriteNote writes={[settingAside]} />

      <View style={tile.buttons}>
        <Button
          label={COPY.notNow}
          accessibilityLabel={notNowLevelAskLabel(sport)}
          variant="secondary"
          size="lg"
          disabled={busy && !settingAside.isPending}
          busy={settingAside.isPending}
          onPress={() => settingAside.mutate()}
          style={tile.button}
        />
        <Button
          label={question === undefined ? getYourLevelLabel(sport) : COPY.carryOn}
          size="lg"
          disabled={elsewhere || (busy && !startingHere)}
          busy={startingHere}
          busyLabel={STARTING_LABEL}
          onPress={onStart}
          style={tile.button}
        />
      </View>
    </Card>
  );
}

/** The card-coloured ring round each face — `FaceStack`'s, so an overlapping face reads in front. */
const RING = theme.size.groupPage.stackRing;

// The tile's frame is `requestTile`'s, shared with FRIEND REQUESTS; these are the faces' own.
const s = StyleSheet.create({
  faces: { flexDirection: 'row' },
  face: {
    borderWidth: RING,
    borderColor: theme.color.surface,
    borderRadius: playerPhotoRadius(ROW_FACE) + RING,
  },
  // A third of the face, as Info's stack slides each face under the one before.
  overlap: { marginLeft: -theme.space.md },
  // The title takes what the faces leave of the row.
  who: { flex: 1 },
});
