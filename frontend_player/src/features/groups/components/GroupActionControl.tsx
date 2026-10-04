/**
 * **What a group row offers** — *Join*, *Ask to join*, or the word in their place:
 * *requested · waiting*, *you're in* (play 9, 10, 35–37; stories 41–44).
 *
 * *Join* is the coral primary, because it admits at once; *Ask to join* is the dark button,
 * because it only asks. The two are **one tap on the wire** — `POST /membership` — and the answer
 * decides what the row turns into, so the control never guesses. While the tap is in flight the
 * button is busy and takes no second press. The two words are tags in the semantics they carry:
 * a request waiting is `warn` (amber — reversible, not yet settled), being in is `ok`.
 */

import { StyleSheet, View } from 'react-native';

import { Button, Tag } from '@/shared/ui';

import type { GroupAtClub } from '../domain/group';
import { groupAction } from '../domain/groupRules';
import { useJoinGroup } from '../hooks/useGroupWrites';

import { ACTION_WORD, actionLabel } from './groupsPresentation';

export function GroupActionControl({ group }: { readonly group: GroupAtClub }) {
  const join = useJoinGroup();
  const action = groupAction(group);
  const label = actionLabel(action, group.name);

  switch (action) {
    case 'join':
    case 'ask':
      return (
        <Button
          label={ACTION_WORD[action]}
          accessibilityLabel={label}
          variant={action === 'join' ? 'primary' : 'dark'}
          size="sm"
          busy={join.isPending}
          onPress={() => join.mutate(group.id)}
        />
      );
    case 'requested':
      return (
        <View style={s.tag}>
          <Tag label={ACTION_WORD.requested} variant="warn" accessibilityLabel={label} />
        </View>
      );
    case 'in':
      return (
        <View style={s.tag}>
          <Tag label={ACTION_WORD.in} variant="ok" accessibilityLabel={label} />
        </View>
      );
  }
}

const s = StyleSheet.create({
  tag: { flexShrink: 0 },
});
