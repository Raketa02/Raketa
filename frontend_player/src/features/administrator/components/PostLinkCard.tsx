/**
 * **The link card — club 11's, always** (PRD #500 story 127; club 11, 13): *Post this in the
 * WhatsApp group. Everybody who taps it lands here.*, the link in mono, and the Administrator's one
 * job as the card's bright door — **Post to WhatsApp** — beside **Copy link**. Club 18's *posted 40 d
 * ago* tag and *Post again* are not drawn: PRD #500 overrides them by name, and nothing records a
 * post.
 *
 * **Post to WhatsApp** opens WhatsApp with *Join Ogrody 33 Club on Raketa: <link>* typed, for the
 * Administrator to pick the chat (story 128). **A phone without WhatsApp gets the share sheet** with
 * the same sentence, so the tap never dead-ends: the share port answers whether WhatsApp took it, and
 * the fallback is decided here, where a suite can watch it happen. **Copy link** puts the bare link
 * on the clipboard and says so in `ok`, or in `bad` that the phone would not take it, as the group
 * page's does.
 *
 * Volt then `onDark`, the link cards' pair: the one bright door on a dark card is the one that
 * reaches people.
 */

import { StyleSheet, Text, View } from 'react-native';

import { GROUPS_COPY, linkLabel, linkShown } from '@/features/groups/types';
import { useClipboard, useShare } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { Button, DarkCard, theme } from '@/shared/ui';

import type { OfficialGroup } from '../domain/officialGroup';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { postMessage } from './administratorPresentation';

export function PostLinkCard({ group }: { readonly group: Pick<OfficialGroup, 'name' | 'link'> }) {
  const COPY = ADMINISTRATOR_COPY.group;
  const share = useShare();
  const clipboard = useClipboard();

  async function post() {
    const message = postMessage(group);
    const opened = await share.openWhatsApp(message);
    if (!opened) await share.shareText(message);
  }

  async function copy() {
    const copied = await clipboard.writeText(group.link);
    showToast(
      copied
        ? { message: GROUPS_COPY.link.copied, tone: 'ok' }
        : { message: GROUPS_COPY.link.notCopied, tone: 'bad' },
    );
  }

  return (
    <DarkCard style={s.card}>
      <Text style={s.line}>{COPY.linkLine}</Text>
      <Text
        style={s.link}
        numberOfLines={1}
        ellipsizeMode="middle"
        accessibilityLabel={linkLabel(group.link)}
      >
        {linkShown(group.link)}
      </Text>
      <View style={s.doors}>
        <Button label={COPY.post} variant="volt" style={s.door} onPress={() => void post()} />
        <Button label={COPY.copy} variant="onDark" style={s.door} onPress={() => void copy()} />
      </View>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  // Info's link, drawn the same: mono, one line, cut in the middle so the code stays in view.
  link: { ...theme.num.s, color: theme.color.surface },
  doors: { flexDirection: 'row', gap: theme.space.xs },
  // Two doors of one width, as club 11 draws them across the card.
  door: { flex: 1 },
});
