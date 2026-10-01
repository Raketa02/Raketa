/**
 * **One person asking to join** — club 20's row, **everywhere**: an Owner's *Want to join* on a
 * player group's Info tab (#514) and an Administrator's on an official group's page (#516). The
 * face, the whole Name, and under it **the first two sports they are rated in** — the sport's
 * dot, its short name and the Level in mono (*● Pad 2,44*) — **and one *+N* for the rest** (#529,
 * the owner's mock of 2026-09-30): four sports over two lines, as club 20 drew them, made the row
 * untidy. **No tag around either** (the owner's ask, 2026-10-01): the dot and the text, and the
 * count as text alone. The row is still spoken with every sport by its whole name. Then **✕** and
 * **Approve**.
 *
 * **It answers nothing itself.** Which route an answer goes to is the caller's — the Owner's
 * player-group routes or the Administrator's — so the row takes the two taps as props, and each
 * caller's hook decides what the answer does to its own cache. Each tap is spoken for whom it acts
 * (*Decline {name}*, *Approve {name}*), because two rows' *Approve*s are two people.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportColour } from '@/features/onboarding/types';
import { Button, CloseControl, PlayerPhoto, theme } from '@/shared/ui';

import type { JoinRequest } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import {
  approveLabel,
  declineLabel,
  personName,
  requestLabel,
  requestTags,
} from './groupsPresentation';
import { ROW_FACE } from './peopleRow';

export interface RequestRowProps {
  readonly request: JoinRequest;
  readonly divided: boolean;
  readonly onDecline: () => void;
  readonly onApprove: () => void;
}

export function RequestRow({ request, divided, onDecline, onApprove }: RequestRowProps) {
  return (
    <View
      testID={`join-request-${request.playerId}`}
      style={[s.row, divided ? s.divided : undefined]}
    >
      <PlayerPhoto
        playerId={request.playerId}
        {...(request.photoUrl === undefined ? {} : { photoUrl: request.photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />

      <View style={s.words} accessible accessibilityLabel={requestLabel(request)}>
        <Text style={s.name} numberOfLines={1}>
          {personName(request.name)}
        </Text>
        {request.levels.length > 0 ? <LevelLine request={request} /> : null}
      </View>

      <CloseControl onPress={onDecline} accessibilityLabel={declineLabel(request.name)} />
      <Button
        label={GROUPS_COPY.info.approve}
        accessibilityLabel={approveLabel(request.name)}
        variant="dark"
        size="sm"
        onPress={onApprove}
      />
    </View>
  );
}

/**
 * The line under the name — each sport its own round dot and the Level in mono, because a Level is
 * a figure, then the *+N* as text. No box around any of them: the dot is what marks a sport, and a
 * fill around a dot and four characters was a tag drawn for no status. On one line; a phone too
 * narrow for two and a *+N* wraps the last onto a second rather than cutting a Level.
 */
function LevelLine({ request }: { readonly request: JoinRequest }) {
  const { shown, more } = requestTags(request.levels);

  return (
    <View style={s.levels}>
      {shown.map(({ sport, label }) => (
        <View key={sport} testID="request-sport" style={s.level}>
          <View
            testID="request-sport-dot"
            style={[s.dot, { backgroundColor: sportColour(sport) }]}
          />
          <Text testID="request-tag" style={s.levelLabel} numberOfLines={1}>
            {label}
          </Text>
        </View>
      ))}
      {more === undefined ? null : (
        <Text testID="request-tag-more" style={s.levelLabel} numberOfLines={1}>
          {more}
        </Text>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // 5.3: `line2` folds one card into rows.
  divided: {
    borderTopWidth: 1,
    borderTopColor: theme.color.line2,
    paddingTop: theme.space.sm,
  },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  // `space.sm` between sports, now no fill separates them, and `space.xxs` between two lines on
  // a phone too narrow for one; `space.xxs` from a dot to its text.
  levels: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    columnGap: theme.space.sm,
    rowGap: theme.space.xxs,
  },
  level: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  // Round: it is the sport's dot, as the group's own dots are (`SportDots`).
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  levelLabel: { ...theme.num.tag, ...theme.tabular, color: theme.color.muted },
});
