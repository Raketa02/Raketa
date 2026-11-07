/**
 * **The link card** (PRD #500 story 127; club 11, 13): the link in mono, then the Administrator's
 * one job as the card's bright door — **Share link** — beside **Copy link**. Club 18's *posted 40 d
 * ago* tag and *Post again* are not drawn: PRD #500 overrides them by name, and nothing records a
 * post.
 *
 * **Share link opens the phone's share sheet** with *Join Ogrody 33 Club on Raketa: <link>* in it,
 * the group page's own sentence, so the link goes out through whatever the Administrator's crowd
 * gathers in — a WhatsApp group among them, and no longer only one (#529). It was *Post to
 * WhatsApp*, which opened WhatsApp by its scheme, under *Post this in the WhatsApp group. Everybody
 * who taps it lands here.*; the product owner retired both, the line with the button. **Copy link**
 * puts the bare link on the clipboard and says so in `ok`, or in `bad` that the phone would not
 * take it, as the group page's does.
 *
 * Volt then `onDark`, the link cards' pair: the one bright door on a dark card is the one that
 * reaches people.
 */

import { StyleSheet, Text, View } from 'react-native';

import { GROUPS_COPY, linkLabel, linkShown, shareMessage } from '@/features/groups/types';
import { useCopyAndSay, useShare } from '@/shared/lib/platform';
import { Button, DarkCard, theme } from '@/shared/ui';

import type { OfficialGroup } from '../domain/officialGroup';

import { ADMINISTRATOR_COPY } from './administratorCopy';

export function ShareLinkCard({ group }: { readonly group: Pick<OfficialGroup, 'name' | 'link'> }) {
  const COPY = ADMINISTRATOR_COPY.group;
  const sheet = useShare();
  const copyAndSay = useCopyAndSay();

  return (
    <DarkCard style={s.card}>
      <Text
        style={s.link}
        numberOfLines={1}
        ellipsizeMode="middle"
        accessibilityLabel={linkLabel(group.link)}
      >
        {linkShown(group.link)}
      </Text>
      <View style={s.doors}>
        <Button
          label={COPY.share}
          variant="volt"
          style={s.door}
          onPress={() => void sheet.shareText(shareMessage(group.name, group.link))}
        />
        <Button
          label={COPY.copy}
          variant="onDark"
          style={s.door}
          onPress={() => void copyAndSay(group.link, GROUPS_COPY.link)}
        />
      </View>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  // Info's link, drawn the same: mono, one line, cut in the middle so the code stays in view.
  link: { ...theme.num.s, color: theme.color.surface },
  doors: { flexDirection: 'row', gap: theme.space.xs },
  // Two doors of one width, as club 11 draws them across the card.
  door: { flex: 1 },
});
