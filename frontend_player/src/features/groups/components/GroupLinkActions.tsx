/**
 * **The link's two doors** — *Share the link* and *Copy link*, under every dark card on a group's
 * page and on the Friends screen (play 14–17, 39, 45, 54–55; PRD #500 stories 64–65).
 *
 * **Share** hands the phone's own sheet the group link inside one sentence, so it goes out through
 * whatever the player has installed; closing the sheet is an answer, not an error, and the page
 * stays as it was. **Copy** puts the bare link on the clipboard — it is what gets pasted into Join
 * a group — and says so in `ok`, or says in `bad` that the phone would not take it, so a tap never
 * passes silently. Both go through the platform ports, which is what lets a suite see them happen.
 *
 * Volt then `onDark`: the one bright door on a dark card is the one that reaches people, and the
 * copy beside it is the quieter of the two, as the mocks draw them.
 */

import { StyleSheet, View } from 'react-native';

import { useClipboard, useShare } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { Button, theme } from '@/shared/ui';

import type { Group } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import { shareMessage } from './groupsPresentation';

const COPY = GROUPS_COPY.link;

export function GroupLinkActions({ group }: { readonly group: Pick<Group, 'name' | 'link'> }) {
  const sheet = useShare();
  const clipboard = useClipboard();

  async function copy() {
    const copied = await clipboard.writeText(group.link);
    showToast(
      copied ? { message: COPY.copied, tone: 'ok' } : { message: COPY.notCopied, tone: 'bad' },
    );
  }

  return (
    <View style={s.row}>
      <Button
        label={COPY.share}
        variant="volt"
        onPress={() => void sheet.shareText(shareMessage(group.name, group.link))}
      />
      <Button label={COPY.copy} variant="onDark" onPress={() => void copy()} />
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'center', gap: theme.space.xs },
});
