/**
 * **FRIEND REQUESTS · n** — Home's row of request cards, above Your games
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); the friends screens §6.2; friends 5; Q13).
 *
 * ```
 * FRIEND REQUESTS · 1
 * ┌───────────────────────────────────────────────┐
 * │ ┌────┐ ines.d wants to be your friend          │
 * │ │face│ With you in Kazimierz crew · Padel 3,40 · ✦ 98
 * │ └────┘                                         │
 * │ ┌──── Not now ────┐ ┌───── Accept ─────┐       │
 * └───────────────────────────────────────────────┘
 * ```
 *
 * ## Only while a request waits
 *
 * **The row and its title are there only while they hold a card** (the screens §6): nothing is drawn
 * while Home's read is in flight, refused or empty — Your games under it already says what Home is,
 * and a FRIEND REQUESTS · 0 would be a heading over nothing. The read is Home's (`proposals`'
 * `useHomeFriendRequests`), newest first, and nothing re-sorts it.
 *
 * ## A horizontal row
 *
 * One card takes the content width, as friends 5 draws it. Two or more are 7.7's **peeking** rail —
 * each `railCardRatio` of the content width, so the next card's edge is the affordance — over Part
 * 8's Strip, bleeding to the screen edge.
 *
 * ## Each card answers itself
 *
 * **Accept** makes the two friends and **Not now** sets the request aside — it stays open, untold,
 * and Accept still answers it from their Members row, their record or *Asked you* (Q1). Either
 * re-reads Home, and **stays busy until Home's read no longer holds the card**: the card leaves on the
 * server's answer. Accept also re-reads every face, which now carries *friend*.
 *
 * ## The chip, the record and the bell are handed in
 *
 * The reliability chip is `player_record`'s `PlayerScoreTag`, and a tap on the face opens that
 * feature's record sheet — which draws this feature's record button. So the shell, which composes
 * Home, hands both in (`scoreTag`, `onFace`) rather than this feature importing the one that draws
 * its button. **Answering re-reads the bell** too (`onAnswered`, `notifications`' re-read): the
 * server takes the request's row off it, and with push on the bell would otherwise say *1 new* until
 * the app next came to the foreground.
 */

import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { useHomeFriendRequests, type HomeFriendRequest } from '@/features/proposals/types';
import { Button, Card, PlayerPhoto, theme } from '@/shared/ui';

import { useAcceptFriendRequest, useSetAsideFriendRequest } from '../hooks/useFriendWrites';

import {
  FRIENDS_COPY,
  acceptLabel,
  notNowLabel,
  requestsHeading,
  wantsToBeYourFriend,
  whereLine,
} from './friendsCopy';
import { ROW_FACE } from './PersonRow';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.home;

export interface FriendRequestsRowProps {
  /** The requester's reliability chip — `player_record`'s, handed in by the shell. */
  readonly scoreTag: (request: HomeFriendRequest) => ReactNode;
  /** A tap on the face: their record. */
  readonly onFace: (playerId: string) => void;
  /**
   * **A card was answered** — the bell's re-read, handed in by the shell: answering takes the
   * request's row off the bell on the server (the mechanics §12), and the bell is `notifications`'.
   */
  readonly onAnswered: () => Promise<unknown>;
}

export function FriendRequestsRow({ scoreTag, onFace, onAnswered }: FriendRequestsRowProps) {
  const requests = useHomeFriendRequests();
  const { width: screen } = useWindowDimensions();

  if (requests === undefined || requests.length === 0) return null;

  const content = screen - 2 * theme.size.gutter;
  const width = requests.length === 1 ? content : content * theme.size.railCardRatio;

  return (
    <View style={s.section} testID="friend-requests">
      <Text style={s.heading} accessibilityRole="header">
        {requestsHeading(requests.length)}
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={s.strip}
        contentContainerStyle={s.stripContent}
      >
        {requests.map((request) => (
          <RequestCard
            key={request.playerId}
            request={request}
            width={width}
            scoreTag={scoreTag(request)}
            onFace={() => onFace(request.playerId)}
            onAnswered={onAnswered}
          />
        ))}
      </ScrollView>
    </View>
  );
}

interface RequestCardProps {
  readonly request: HomeFriendRequest;
  readonly width: number;
  readonly scoreTag: ReactNode;
  readonly onFace: () => void;
  readonly onAnswered: () => Promise<unknown>;
}

function RequestCard({ request, width, scoreTag, onFace, onAnswered }: RequestCardProps) {
  // The bell's re-read rides in the writes themselves: the card unmounts once Home has re-read, and
  // a press's own callbacks would go with it.
  const accepting = useAcceptFriendRequest(request.playerId, onAnswered);
  const settingAside = useSetAsideFriendRequest(request.playerId, onAnswered);
  const where = whereLine({
    byLink: request.byLink,
    ...(request.group === undefined ? {} : { group: request.group }),
    ...(request.sport === undefined ? {} : { sportName: sportLabel(request.sport) }),
    ...(request.level === undefined ? {} : { level: request.level }),
  });
  const busy = accepting.isPending || settingAside.isPending;

  return (
    <Card style={[s.card, { width }]}>
      <View style={s.top} testID={`friend-request-${request.playerId}`}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={request.nickname}
          onPress={onFace}
          hitSlop={theme.hit.peopleRow}
          style={({ pressed }) => (pressed ? s.pressed : undefined)}
        >
          <PlayerPhoto
            playerId={request.playerId}
            {...(request.photoUrl === undefined ? {} : { photoUrl: request.photoUrl })}
            box={{ kind: 'face', size: ROW_FACE }}
          />
        </Pressable>
        <View style={s.words}>
          <Text style={s.who}>{wantsToBeYourFriend(request.nickname)}</Text>
          <View style={s.whereRow}>
            {where === '' ? null : <Text style={s.where}>{where}</Text>}
            {scoreTag}
          </View>
        </View>
      </View>

      <WriteNote writes={[accepting, settingAside]} />

      <View style={s.buttons}>
        <Button
          label={COPY.notNow}
          accessibilityLabel={notNowLabel(request.nickname)}
          variant="secondary"
          size="lg"
          disabled={busy && !settingAside.isPending}
          busy={settingAside.isPending}
          onPress={() => settingAside.mutate()}
          style={s.button}
        />
        <Button
          label={COPY.accept}
          accessibilityLabel={acceptLabel(request.nickname)}
          size="lg"
          disabled={busy && !accepting.isPending}
          busy={accepting.isPending}
          busyLabel={COPY.accepting}
          onPress={() => accepting.mutate()}
          style={s.button}
        />
      </View>
    </Card>
  );
}

/** Part 8's Strip gap. */
const STRIP_GAP = theme.space.sm;

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, as Your games' is.
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  strip: { marginHorizontal: -theme.size.gutter },
  stripContent: { paddingHorizontal: theme.size.gutter, gap: STRIP_GAP },
  // Friends 5 bounds the card in ink: a request waiting on the reader, as 5.1's selected border.
  card: { borderColor: theme.color.ink, gap: theme.space.md },
  top: { flexDirection: 'row', gap: theme.space.sm, alignItems: 'flex-start' },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  who: { ...theme.type.cardTitle, color: theme.color.ink },
  whereRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: theme.space.xxs },
  where: { ...theme.type.tiny, color: theme.color.muted },
  buttons: { flexDirection: 'row', gap: theme.space.sm },
  button: { flex: 1 },
});
