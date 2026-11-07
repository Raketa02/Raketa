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
 *
 * **Info's card draws them short** — *Share* and *Copy*, beside the link rather than under a
 * headline (play 57, 60) — and they are **spoken whole** there too: a listener meets the two
 * doors out of the card's context, where *Share* alone says nothing about what goes out.
 */

import { StyleSheet, View } from 'react-native';

import { useCopyAndSay, useShare } from '@/shared/lib/platform';
import { Button, theme } from '@/shared/ui';

import type { Group } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import { shareMessage } from './groupsPresentation';

const COPY = GROUPS_COPY.link;

export interface GroupLinkActionsProps {
  readonly group: Pick<Group, 'name' | 'link'>;
  /** Info's *Share* and *Copy* — drawn short, spoken whole. */
  readonly short?: boolean;
}

export function GroupLinkActions({ group, short = false }: GroupLinkActionsProps) {
  const sheet = useShare();
  const copyAndSay = useCopyAndSay();

  return (
    <View style={s.row}>
      <Button
        label={short ? COPY.shareShort : COPY.share}
        accessibilityLabel={COPY.share}
        variant="volt"
        onPress={() => void sheet.shareText(shareMessage(group.name, group.link))}
      />
      <Button
        label={short ? COPY.copyShort : COPY.copy}
        accessibilityLabel={COPY.copy}
        variant="onDark"
        onPress={() => void copyAndSay(group.link, COPY)}
      />
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'center', gap: theme.space.xs },
});
