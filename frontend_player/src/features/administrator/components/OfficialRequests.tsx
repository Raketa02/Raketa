/**
 * **Want to join · N** — an official group's queue, between the link card and the players (club 18,
 * 20; PRD #500 story 129). **Club 20's card, everywhere**: the same row an Owner answers on a player
 * group's Info (`groups`' `RequestRow`) — face, whole Name, every sport with its Level — with
 * **✕** and **Approve**, answered through the Administrator's own routes.
 *
 * **An answer takes its row at once** (`useAnswerAsAdministrator`): the tap ends the request
 * whatever the server does, so the row goes before the answer lands and comes back, with a toast,
 * only if the tap is refused. **Nothing is drawn while nobody is waiting** — no heading over an
 * empty card. The queue rides on the group's own read, so it never draws before the page does.
 */

import { StyleSheet, Text, View } from 'react-native';

import { RequestRow, wantToJoin, type JoinRequest } from '@/features/groups/types';
import { codeMessage } from '@/shared/errors';
import { Card, theme } from '@/shared/ui';

import { useAnswerAsAdministrator } from '../hooks/useOfficialGroupWrites';

import { REQUEST_REFUSALS } from './administratorPresentation';

export interface OfficialRequestsProps {
  readonly clubId: string;
  readonly groupId: string;
  readonly requests: readonly JoinRequest[];
}

export function OfficialRequests({ clubId, groupId, requests }: OfficialRequestsProps) {
  const answer = useAnswerAsAdministrator(clubId, groupId, (error) =>
    codeMessage(REQUEST_REFUSALS, error),
  );

  if (requests.length === 0) return null;

  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {wantToJoin(requests.length)}
      </Text>
      <Card style={s.card}>
        {requests.map((request, at) => (
          <RequestRow
            key={request.playerId}
            request={request}
            divided={at > 0}
            onDecline={() => answer.mutate({ playerId: request.playerId, answer: 'decline' })}
            onApprove={() => answer.mutate({ playerId: request.playerId, answer: 'approve' })}
          />
        ))}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  card: { gap: theme.space.sm },
});
