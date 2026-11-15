/**
 * **Taking a step back, asked first** — the sheet the record's ▾ opens (#753) and the round friend
 * button's **…** and **✓** open (#801): its title is the question or the state, a line under it where
 * there is one, the one act named once, and **Keep** under it where the sheet asks.
 *
 * | Opened from | Title | Body | Act | Keep |
 * | --- | --- | --- | --- | --- |
 * | the record's *Request sent ▾* | *Cancel your request to kuba.w?* | *Nobody is told.* | **Cancel request** | yes |
 * | the record's *Friend ✓ ▾*, the round **✓** | *Remove kuba.w as a friend?* | *Nobody is told, …* | **Remove friend** | yes |
 * | the round **…** | *Request sent* | — | **Cancel request** | — |
 *
 * The act stays busy until the read under it has settled (`useFriendWrites`), and a refusal that is
 * not the state moving is said above it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import { FRIENDS_COPY } from './friendsCopy';
import { WriteNote, type WriteState } from './WriteNote';

const COPY = FRIENDS_COPY.record;

export interface TakeBackSheetProps {
  readonly visible: boolean;
  readonly title: string;
  /** What the act does — absent where the title says enough (the round **…**'s *Request sent*). */
  readonly body?: string;
  readonly act: string;
  readonly busyLabel: string;
  readonly write: WriteState & { readonly isPending: boolean };
  readonly onAct: () => void;
  readonly onClose: () => void;
  /** **Keep** under the act — where the sheet asks a question. */
  readonly keep?: boolean;
  readonly returnFocusTo?: FocusTarget;
}

export function TakeBackSheet({
  visible,
  title,
  body,
  act,
  busyLabel,
  write,
  onAct,
  onClose,
  keep = true,
  returnFocusTo,
}: TakeBackSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={title}
      closeLabel={COPY.close}
      {...(returnFocusTo === undefined ? {} : { returnFocusTo })}
    >
      {body === undefined ? null : <Text style={s.body}>{body}</Text>}

      <WriteNote writes={[write]} />

      <View style={s.actions}>
        <Button
          label={act}
          size="lg"
          busy={write.isPending}
          busyLabel={busyLabel}
          onPress={onAct}
        />
        {keep ? <Button label={COPY.keep} variant="secondary" size="lg" onPress={onClose} /> : null}
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
