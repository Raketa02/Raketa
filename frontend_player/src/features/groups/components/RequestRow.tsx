/**
 * **One person asking to join** — club 20's row, **everywhere**: an Owner's *Want to join* on a
 * player group's Info tab (#514) and an Administrator's on an official group's page (#516). The
 * face, the whole Name and every sport they are rated in with its Level (*Padel 2,44 · Tennis
 * 2,60*), in mono — Levels are figures (1.4) — wrapping rather than truncating, as club 20 draws
 * four sports over two lines; then **✕** and **Approve**.
 *
 * **It answers nothing itself.** Which route an answer goes to is the caller's — the Owner's
 * player-group routes or the Administrator's — so the row takes the two taps as props, and each
 * caller's hook decides what the answer does to its own cache. Each tap is spoken for whom it acts
 * (*Decline {name}*, *Approve {name}*), because two rows' *Approve*s are two people.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, CloseControl, PlayerPhoto, theme } from '@/shared/ui';

import type { JoinRequest } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import {
  approveLabel,
  declineLabel,
  personName,
  requestLabel,
  requestLevels,
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
        {request.levels.length > 0 ? (
          <Text style={s.levels}>{requestLevels(request.levels)}</Text>
        ) : null}
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
  levels: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
});
