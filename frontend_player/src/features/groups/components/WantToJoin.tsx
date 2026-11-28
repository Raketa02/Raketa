/**
 * **Want to join · N** — the Owner's queue, between the link card and the members row (club 20;
 * [#514](https://github.com/Rakieta02/Rakieta/issues/514), PRD #500 stories 73–74).
 *
 * **Club 20's card, everywhere** — PRD #500 replaces play 62 by name: one card, a row per person
 * in the order they asked, each with their face, their whole nickname and **every sport they are
 * rated in with its Level** (*Padel 2,44 · Tennis 2,60*), no Player Score; **✕** declines and
 * **Approve** admits. The line wraps rather than truncating, as club 20 draws Tomek's four sports
 * over two lines, and is mono — Levels are figures (1.4), and club 20's sans gives way to it.
 *
 * **An answer takes its row at once** (`useAnswerRequest`): the tap ends the request whatever the
 * server does, so the row goes before the answer lands and comes back, with a toast, only if the
 * tap is refused. **Nothing is drawn while nobody is waiting** — no heading over an empty card —
 * and nothing while the queue is being read, so the members row does not jump down a card's height
 * a beat after the tab opens only to jump back.
 *
 * Each row is two elements to a listener after its words: the ✕ named *Decline {name}* and
 * *Approve {name}*, because two rows' *Approve*s are two people.
 */

import { StyleSheet, Text, View } from 'react-native';

import { codeMessage } from '@/shared/errors';
import { Card, theme } from '@/shared/ui';

import { useJoinRequests } from '../hooks/useGroups';
import { useAnswerRequest } from '../hooks/useGroupWrites';

import { REQUEST_REFUSALS, wantToJoin } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';
import { RequestRow } from './RequestRow';

export function WantToJoin({ groupId }: { readonly groupId: string }) {
  const read = useJoinRequests(groupId);
  const answer = useAnswerRequest(groupId, (error) => codeMessage(REQUEST_REFUSALS, error));
  const requests = read.data;

  if (requests === undefined) {
    return read.error === null ? null : (
      <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
    );
  }
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
