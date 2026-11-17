/**
 * **FRIEND REQUESTS · n** — Needs your answer's section of friend requests, after FRIENDS GAME and
 * before ASKED FOR A LEVEL ([#816](https://github.com/Raketa02/Raketa/issues/816), ADR-0205 §1;
 * the friends screens §6.2; home refactor 2). It was Home's row, above Your games, from #753.
 *
 * ```
 * FRIEND REQUESTS · 2
 * ┌──────────────────────────────────────┐ ┌─────
 * │ ┌────┐ ines.d wants to be your friend│ │ ┌───
 * │ │face│ ✦ 98                          │ │ │fac
 * │ └────┘                               │ │ └───
 * │ ┌─── Not now ───┐ ┌──── Accept ────┐ │ │ ┌──
 * └──────────────────────────────────────┘ └─────
 * ```
 *
 * ## Only while a request waits
 *
 * **The section and its title are there only while they hold a card** (ADR-0205 §1): nothing is
 * drawn while Home's read is in flight, refused or empty, and a FRIEND REQUESTS · 0 would be a
 * heading over nothing. The read is Home's (`proposals`' `useHomeFriendRequests`), newest first,
 * and nothing re-sorts it.
 *
 * ## A wider peeking rail, every tile as tall as the tallest
 *
 * **The tile is wider than a Home card** (Q2): `requestCardRatio` of the content width, measured off
 * home refactor 2, on the row frame's `wide` rail, the next tile peeking. A lone tile takes the
 * content width. **Tiles stand as tall as the tallest, the buttons at the foot and the title held
 * to two lines** (Q3), so the buttons sit level across the rail.
 *
 * ## What a tile says, and what it no longer says
 *
 * The face, *ines.d wants to be your friend*, and the reliability chip under it. **The where-line
 * and every found-by line are gone** (Q2): *With you in Kazimierz crew · Padel 3,40*, *Invited you
 * to Raketa*, *Found you in the padel ranking*, and Home rows' three. Where a request was found is
 * still recorded and served; no tile draws it. #818 adds the sender's sport levels in their place.
 *
 * ## Each tile answers itself
 *
 * **Accept** makes the two friends and **Not now** sets the request aside — it stays open, untold,
 * and Accept still answers it from their Members row, their record or *Asked you* (Q1). Either
 * re-reads Home, and **stays busy until Home's read no longer holds the tile**: the tile leaves on
 * the server's answer. Accept also re-reads every face, which now carries *friend*.
 *
 * ## The chip, the record and the bell are handed in
 *
 * The reliability chip is `player_record`'s `PlayerScoreTag`, and a tap on the face opens that
 * feature's record sheet — which draws this feature's record button. So the shell, which composes
 * the sheet, hands both in (`scoreTag`, `onFace`) rather than this feature importing the one that
 * draws its button. **Answering re-reads the bell** too (`onAnswered`, `notifications`' re-read): the
 * server takes the request's row off it, and with push on the bell would otherwise say *1 new* until
 * the app next came to the foreground.
 */

import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useHomeFriendRequests, type HomeFriendRequest } from '@/features/proposals/types';
import { Button, Card, HomeRow, HomeRowRail, PlayerPhoto, theme } from '@/shared/ui';

import { useAcceptFriendRequest, useSetAsideFriendRequest } from '../hooks/useFriendWrites';

import {
  FRIENDS_COPY,
  acceptLabel,
  notNowLabel,
  requestsHeading,
  wantsToBeYourFriend,
} from './friendsCopy';
import { ROW_FACE } from './PersonRow';
import { REQUEST_TILE as tile, TITLE_LINES } from './requestTile';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.home;

export interface FriendRequestsSectionProps {
  /** The requester's reliability chip — `player_record`'s, handed in by the shell. */
  readonly scoreTag: (request: HomeFriendRequest) => ReactNode;
  /** A tap on the face: their record. */
  readonly onFace: (playerId: string) => void;
  /**
   * **A tile was answered** — the bell's re-read, handed in by the shell: answering takes the
   * request's row off the bell on the server (the mechanics §12), and the bell is `notifications`'.
   */
  readonly onAnswered: () => Promise<unknown>;
}

export function FriendRequestsSection({
  scoreTag,
  onFace,
  onAnswered,
}: FriendRequestsSectionProps) {
  const requests = useHomeFriendRequests();

  if (requests === undefined || requests.length === 0) return null;

  return (
    <HomeRow heading={requestsHeading(requests.length)} testID="friend-requests">
      <HomeRowRail cards={requests} geometry="wide">
        {(request, width) => (
          <RequestTile
            key={request.playerId}
            request={request}
            width={width}
            scoreTag={scoreTag(request)}
            onFace={() => onFace(request.playerId)}
            onAnswered={onAnswered}
          />
        )}
      </HomeRowRail>
    </HomeRow>
  );
}

interface RequestTileProps {
  readonly request: HomeFriendRequest;
  readonly width: number;
  readonly scoreTag: ReactNode;
  readonly onFace: () => void;
  readonly onAnswered: () => Promise<unknown>;
}

function RequestTile({ request, width, scoreTag, onFace, onAnswered }: RequestTileProps) {
  // The bell's re-read rides in the writes themselves: the tile unmounts once Home has re-read, and
  // a press's own callbacks would go with it.
  const accepting = useAcceptFriendRequest(request.playerId, onAnswered);
  const settingAside = useSetAsideFriendRequest(request.playerId, onAnswered);
  const busy = accepting.isPending || settingAside.isPending;

  return (
    <Card style={[tile.tile, { width }]}>
      <View style={tile.top} testID={`friend-request-${request.playerId}`}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={request.nickname}
          onPress={onFace}
          hitSlop={theme.hit.peopleRow}
          style={({ pressed }) => (pressed ? tile.pressed : undefined)}
        >
          <PlayerPhoto
            playerId={request.playerId}
            {...(request.photoUrl === undefined ? {} : { photoUrl: request.photoUrl })}
            box={{ kind: 'face', size: ROW_FACE }}
          />
        </Pressable>
        <View style={s.words}>
          <Text style={tile.title} numberOfLines={TITLE_LINES}>
            {wantsToBeYourFriend(request.nickname)}
          </Text>
          {/* On a line of its own, at its own width: the chip is a mark, not a column. */}
          <View style={s.chip}>{scoreTag}</View>
        </View>
      </View>

      <WriteNote writes={[accepting, settingAside]} />

      <View style={tile.buttons}>
        <Button
          label={COPY.notNow}
          accessibilityLabel={notNowLabel(request.nickname)}
          variant="secondary"
          size="lg"
          disabled={busy && !settingAside.isPending}
          busy={settingAside.isPending}
          onPress={() => settingAside.mutate()}
          style={tile.button}
        />
        <Button
          label={COPY.accept}
          accessibilityLabel={acceptLabel(request.nickname)}
          size="lg"
          disabled={busy && !accepting.isPending}
          busy={accepting.isPending}
          busyLabel={COPY.accepting}
          onPress={() => accepting.mutate()}
          style={tile.button}
        />
      </View>
    </Card>
  );
}

// The tile's frame is `requestTile`'s, shared with ASKED FOR A LEVEL; these are the words' own.
const s = StyleSheet.create({
  words: { flex: 1, gap: theme.space.xs },
  chip: { flexDirection: 'row' },
});
