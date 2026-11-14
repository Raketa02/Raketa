/**
 * **ASKED FOR A LEVEL · n** — Home's row of a friend's asks for a level, one card per sport, after
 * FRIEND REQUESTS and before Your games ([#765](https://github.com/Raketa02/Raketa/issues/765), PRD
 * #762; the friends screens §6.4; the mechanics §5.1; the words §29.5; Q129).
 *
 * ```
 * ASKED FOR A LEVEL · 1
 * ┌───────────────────────────────────────────────┐
 * │ ┌──┬──┬────┐ tomek.k, kuba.w and 2 more want   │
 * │ │fa│fa│face│ to play padel with you            │
 * │ └──┴──┴────┘ A few questions, and they can add │
 * │              you to a game.                    │
 * │ ┌──── Not now ────┐ ┌─ Get your padel level ─┐ │
 * └───────────────────────────────────────────────┘
 * ```
 *
 * ## A friend-request card
 *
 * **It is the request card** (friends 5; the screens §6.4's call): faces, two lines, **Not now**
 * (outline) and the coral button, bounded in `ink` — a card waiting on the reader. It is not the
 * dark *Get your level*, which it stands in place of for a player rated in nothing (`groups`' rule
 * leaves that one out while this row has a card). **No group is named.** One card takes the content
 * width; two or more are the peeking rail, as FRIEND REQUESTS' — both on Home's row frame (`HomeRow`,
 * #798). The row and its title are there only while Home's read holds a card: nothing while it is
 * in flight, refused or empty. The read is
 * Home's (`proposals`' `useHomeLevelAsks`), the sport with the newest ask first, and nothing
 * re-sorts it.
 *
 * ## The faces
 *
 * **Up to three, newest first, overlapping** a third of a face, each ringed in the card's white so
 * one reads as in front of the next (`groups`' `FaceStack`'s drawing), at the request card's 38. The
 * newest is at the back, as every stack in the app draws its first. **Each is its own press**, and
 * opens that friend's record: the face in front keeps its whole 38, and each behind it the 26 it
 * shows — under 6.5's 44 across, a call recorded in Part 16, since a stack whose faces each answer
 * cannot give each one 44 without ceasing to overlap.
 *
 * ## The coral button is the notice's act
 *
 * **Get your padel level** and **Carry on** both run what the *level asked* notice runs
 * (`useGetAskedLevel`, over `onboarding`'s `useAddASport` from Home): the sport's questionnaire, its
 * unfinished run handed back if there is one, the pass returning to Home. So the card draws its start
 * at once and turns to **Carry on** — *You're on question 5.* — as soon as a run left halfway in the
 * sport is read (`useQuestionLeftAt`): a press before that opens the same run. One start for the
 * whole row, and another card's button is disabled while it is in flight. **A start that fails**
 * shows the notice's own toast (`unstarted`, handed in) — *You have a padel level already.* for
 * `sport_already_rated`, on which the hook also re-reads Home and the bell.
 *
 * ## Not now
 *
 * **Sets the sport's asks aside**, then says where the level still is — *You can get your padel level
 * any time, from You › Skill passport.*, neutral and held to be read — and re-reads Home and the
 * bell (`useSetAsideLevelAsks`). It stays busy until Home no longer holds the card.
 *
 * ## The record and the bell are handed in
 *
 * A face opens `player_record`'s record sheet, which draws this feature's record button, and the
 * bell is `notifications'` — so the shell, which composes Home, hands both in (`onFace`,
 * `onAnswered`), as it does to FRIEND REQUESTS, and the notice's toast words with them.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { STARTING_LABEL, sportInLine, useQuestionLeftAt } from '@/features/onboarding/types';
import { useHomeLevelAsks, type HomeLevelAsk } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';
import { showToast, type ToastRequest } from '@/shared/store/toast.store';
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
import { useGetAskedLevel, type GetAskedLevel } from '../hooks/useGetAskedLevel';

import {
  FRIENDS_COPY,
  getYourLevelLabel,
  levelAskLine,
  levelAsksHeading,
  notNowLevelAskLabel,
  setAsideToast,
  wantToPlay,
  youReOnQuestion,
} from './friendsCopy';
import { ROW_FACE } from './PersonRow';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.levelAsks;

export interface LevelAsksRowProps {
  /** A tap on a face: that friend's record. */
  readonly onFace: (playerId: string) => void;
  /** **The bell's re-read**, handed in by the shell: the server takes the asks' rows off it. */
  readonly onAnswered: () => Promise<unknown>;
  /** **The *level asked* notice's own toast** for a start that failed — the shell hands it in. */
  readonly unstarted: (sport: Sport, error: AppError) => ToastRequest;
}

export function LevelAsksRow({ onFace, onAnswered, unstarted }: LevelAsksRowProps) {
  const asks = useHomeLevelAsks();
  const start = useGetAskedLevel(onAnswered);

  if (asks === undefined || asks.length === 0) return null;

  return (
    <HomeRow heading={levelAsksHeading(asks.length)} testID="level-asks">
      <HomeRowRail cards={asks}>
        {(ask, width) => (
          <LevelAskCard
            key={ask.sport}
            ask={ask}
            width={width}
            start={start}
            onStart={() => start.get(ask.sport, (error) => showToast(unstarted(ask.sport, error)))}
            onFace={onFace}
            onAnswered={onAnswered}
          />
        )}
      </HomeRowRail>
    </HomeRow>
  );
}

interface LevelAskCardProps {
  readonly ask: HomeLevelAsk;
  readonly width: number;
  readonly start: GetAskedLevel;
  readonly onStart: () => void;
  readonly onFace: (playerId: string) => void;
  readonly onAnswered: () => Promise<unknown>;
}

function LevelAskCard({ ask, width, start, onStart, onFace, onAnswered }: LevelAskCardProps) {
  const sport = sportInLine(ask.sport);
  const question = useQuestionLeftAt(ask.sport);
  // The toast rides in the write itself: the card unmounts once Home has re-read, and a press's own
  // callbacks would go with it.
  const settingAside = useSetAsideLevelAsks(ask.sport, onAnswered, () =>
    showToast({ message: setAsideToast(sport), hold: 'read' }),
  );
  const nicknames = ask.askers.map((asker) => asker.nickname);
  const starting = start.starting === ask.sport;
  // Another card's start is in flight: this one's press would do nothing, so it says so.
  const elsewhere = start.starting !== undefined && !starting;
  const busy = starting || settingAside.isPending;

  return (
    <Card style={[s.card, { width }]}>
      <View style={s.top} testID={`level-ask-${ask.sport}`}>
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
                pressed ? s.pressed : undefined,
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
        <View style={s.words}>
          <Text style={s.who}>{wantToPlay(nicknames, sport)}</Text>
          <Text style={s.line}>
            {question === undefined ? levelAskLine(nicknames) : youReOnQuestion(question)}
          </Text>
        </View>
      </View>

      <WriteNote writes={[settingAside]} />

      <View style={s.buttons}>
        <Button
          label={COPY.notNow}
          accessibilityLabel={notNowLevelAskLabel(sport)}
          variant="secondary"
          size="lg"
          disabled={busy && !settingAside.isPending}
          busy={settingAside.isPending}
          onPress={() => settingAside.mutate()}
          style={s.button}
        />
        <Button
          label={question === undefined ? getYourLevelLabel(sport) : COPY.carryOn}
          size="lg"
          disabled={elsewhere || (busy && !starting)}
          busy={starting}
          busyLabel={STARTING_LABEL}
          onPress={onStart}
          style={s.button}
        />
      </View>
    </Card>
  );
}

/** The card-coloured ring round each face — `FaceStack`'s, so an overlapping face reads in front. */
const RING = theme.size.groupPage.stackRing;

const s = StyleSheet.create({
  // Friends 5's request card, bounded in ink: something waiting on the reader.
  card: { borderColor: theme.color.ink, gap: theme.space.md },
  top: { flexDirection: 'row', gap: theme.space.sm, alignItems: 'flex-start' },
  faces: { flexDirection: 'row' },
  face: {
    borderWidth: RING,
    borderColor: theme.color.surface,
    borderRadius: playerPhotoRadius(ROW_FACE) + RING,
  },
  // A third of the face, as Info's stack slides each face under the one before.
  overlap: { marginLeft: -theme.space.md },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  who: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  buttons: { flexDirection: 'row', gap: theme.space.sm },
  button: { flex: 1 },
});
