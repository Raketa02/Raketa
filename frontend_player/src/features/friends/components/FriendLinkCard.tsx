/**
 * **Not on Rakieta yet?** — the Add friends sheet's second card
 * ([#756](https://github.com/Rakieta02/Rakieta/issues/756); the friends screens §5; friends 4; the
 * words §29.3).
 *
 * ```
 * ┌───────────────────────────────────────────┐
 * │ Not on Rakieta yet?                       │
 * │ ┌───────────────────────────┐ ┌────────┐  │
 * │ │ rakieta.app/f/tk4m9q2z    │ │  Copy  │  │
 * │ └───────────────────────────┘ └────────┘  │
 * │ [New link]                                │
 * └───────────────────────────────────────────┘
 * ```
 *
 * **Your link in a field, without its scheme** (the mocks never print one), on one line in mono, cut
 * in the middle where it will not fit so its code stays in view — Info's link card's drawing. Spoken
 * whole, and copied whole.
 *
 * **Copy** (coral, the card's one action) puts the whole link on the clipboard and says *Link
 * copied* — or that the phone would not take it — `shared`'s `useCopyAndSay`, as a group page's Copy
 * link does.
 *
 * **New link** is small and under the field, and **asks first**: the link you have now stops working
 * the moment a new one is made, wherever it was sent (the mechanics §4.1). The question is a sheet
 * over this one — the record's take-back sheets' shape — with **New link** and **Keep this link**.
 * Once made, the field shows the new link and the card says the old one no longer works.
 *
 * **Read when the sheet opens**, beside the groups, and drawn in their three read states
 * (`ListReading`) until it is in.
 */

import { useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { linkWithoutScheme } from '@/shared/formatting/linkFormat';
import { useCopyAndSay } from '@/shared/lib/platform';
import { behindOverlay, BottomSheet, Button, Card, Note, theme } from '@/shared/ui';

import { useFriendLink, useNewFriendLink } from '../hooks/useFriendLink';

import { FRIENDS_COPY, friendLinkLabel } from './friendsCopy';
import { ListReading } from './ListReading';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.link;

export function FriendLinkCard({ reading }: { readonly reading: boolean }) {
  const read = useFriendLink({ enabled: reading });
  const newLink = useNewFriendLink();
  const copyAndSay = useCopyAndSay();
  const [asking, setAsking] = useState(false);
  const self = useRef<View>(null);
  const link = read.data;

  function ask() {
    newLink.reset();
    setAsking(true);
  }

  return (
    <>
      <Card style={s.card}>
        <View ref={self} style={s.body} {...behindOverlay(asking)}>
          <Text style={s.title} accessibilityRole="header">
            {COPY.title}
          </Text>
          {link === undefined ? (
            <ListReading read={read} reading={COPY.reading} />
          ) : (
            <>
              <View style={s.row}>
                <View style={s.field}>
                  <Text
                    style={s.link}
                    numberOfLines={1}
                    ellipsizeMode="middle"
                    accessibilityLabel={friendLinkLabel(link.link)}
                  >
                    {linkWithoutScheme(link.link)}
                  </Text>
                </View>
                <Button
                  label={COPY.copy}
                  accessibilityLabel={COPY.copyLabel}
                  size="lg"
                  onPress={() => void copyAndSay(link.link, COPY)}
                />
              </View>
              {newLink.isSuccess ? <Note variant="mint">{COPY.made}</Note> : null}
              <Button
                label={COPY.newLink}
                accessibilityLabel={COPY.newLinkLabel}
                variant="secondary"
                size="sm"
                onPress={ask}
                style={s.newLink}
              />
            </>
          )}
        </View>
      </Card>

      <BottomSheet
        visible={asking}
        onClose={() => setAsking(false)}
        title={COPY.confirm.title}
        closeLabel={COPY.confirm.close}
        returnFocusTo={self}
      >
        <Text style={s.confirmBody}>{COPY.confirm.body}</Text>

        <WriteNote writes={[newLink]} />

        <View style={s.actions}>
          <Button
            label={COPY.confirm.act}
            size="lg"
            busy={newLink.isPending}
            busyLabel={COPY.confirm.busy}
            onPress={() => newLink.mutate(undefined, { onSuccess: () => setAsking(false) })}
          />
          <Button
            label={COPY.confirm.keep}
            variant="secondary"
            size="lg"
            onPress={() => setAsking(false)}
          />
        </View>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  card: { paddingVertical: theme.space.md },
  body: { gap: theme.space.sm },
  // `h2` titles a card (design-system Part 7): friends 4 draws the question inside it.
  title: { ...theme.type.h2, color: theme.color.ink },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // A recessed well the height of the Copy beside it — the field the mock draws, read-only.
  field: {
    flex: 1,
    justifyContent: 'center',
    minHeight: theme.size.btnLg,
    paddingHorizontal: theme.space.md,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.paper2,
  },
  link: { ...theme.num.s, color: theme.color.ink },
  newLink: { alignSelf: 'flex-start' },
  confirmBody: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
