/**
 * **The record's left button** — *Add friend*, *Request sent ▾*, *Accept* or *Friend ✓ ▾*
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); the friends screens §2; Q3, Q40).
 *
 * `player_record`'s sheet draws it beside `blocks`' **Block**, one row of two at the record's foot
 * (`recordFootOf` says which, and when **Block** stands alone instead: nothing between them, and the
 * record says no request may be sent). This is the left half:
 *
 * | Relation | Drawn | A press |
 * | --- | --- | --- |
 * | `NONE` | **Add friend**, black — where the record says a request may be sent | asks, at once |
 * | `SENT` | **Request sent ▾**, outlined | the cancel sheet |
 * | `ASKED_YOU` | **Accept**, coral | accepts, at once |
 * | `FRIEND` | **Friend ✓ ▾**, outlined | the remove sheet |
 *
 * ## The ▾ opens the one action, and it asks first
 *
 * The screens §2 draw the ▾ as *a small menu with the one action*, and #753 puts both actions
 * **behind a confirmation**. One sheet is both: its title is the question (*Remove kuba.w as a
 * friend?*), its first button the one action named once (*Remove friend*), and *Keep* under it —
 * `blocks`' confirm sheet, the same shape one row over. A menu of one item followed by a sheet
 * asking about it would be two presses saying the same thing. **Nobody is told** either way (Q3), and
 * the sheet says so; removing touches no game.
 *
 * Asking and accepting happen on the press: each is one more step towards somebody, which the other
 * person still answers or already asked for — and a cancel is one sheet away.
 *
 * ## Settled on the record's own answer
 *
 * Every press **re-reads the record** — handed in, as `BlockRow`'s is — and settles once it has, so
 * the button flips from *Add friend* to *Request sent ▾* on the server's next answer, and a sheet's
 * act stays busy until the record under it no longer needs the sheet.
 */

import { useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { behindOverlay, BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import type { AskedWhere, FriendButton as Shown } from '../domain/friendship';
import {
  useAcceptFriendRequest,
  useAskToBeFriends,
  useCancelFriendRequest,
  useRemoveFriend,
  type Reread,
} from '../hooks/useFriendWrites';

import { FRIENDS_COPY, cancelTitle, removeTitle } from './friendsCopy';
import { WriteNote, type WriteState } from './WriteNote';

const COPY = FRIENDS_COPY.record;

export interface FriendButtonProps {
  readonly playerId: string;
  /** Their whole nickname, for the sheets' titles. */
  readonly nickname: string;
  /** Which of the four, from the record's relation (`recordFootOf`). */
  readonly button: Shown;
  /** The record, and the group and sport it was opened from — which their Home card names. */
  readonly where: AskedWhere;
  /** **The record's own re-read**, which every press awaits before it settles. */
  readonly rereadRecord: Reread;
}

export function FriendButton({
  playerId,
  nickname,
  button,
  where,
  rereadRecord,
}: FriendButtonProps) {
  const asking = useAskToBeFriends(playerId, where, rereadRecord);
  const accepting = useAcceptFriendRequest(playerId, rereadRecord);
  const cancelling = useCancelFriendRequest(playerId, rereadRecord);
  const removing = useRemoveFriend(playerId, rereadRecord);
  const [sheet, setSheet] = useState<'cancel' | 'remove'>();
  const self = useRef<View>(null);

  function open(which: 'cancel' | 'remove') {
    cancelling.reset();
    removing.reset();
    setSheet(which);
  }

  return (
    <>
      <View ref={self} style={s.self} {...behindOverlay(sheet !== undefined)}>
        {button === 'ask' ? (
          <Button
            label={COPY.add}
            variant="dark"
            busy={asking.isPending}
            busyLabel={COPY.asking}
            onPress={() => asking.mutate()}
          />
        ) : button === 'accept' ? (
          <Button
            label={COPY.accept}
            busy={accepting.isPending}
            busyLabel={COPY.accepting}
            onPress={() => accepting.mutate()}
          />
        ) : button === 'sent' ? (
          <Button
            label={COPY.sent}
            variant="secondary"
            marks={['chevron']}
            onPress={() => open('cancel')}
          />
        ) : (
          <Button
            label={COPY.friend}
            variant="secondary"
            marks={['tick', 'chevron']}
            onPress={() => open('remove')}
          />
        )}
        <WriteNote writes={[asking, accepting]} />
      </View>

      <TakeBackSheet
        // Gone the moment the re-read record no longer draws the button that opened it.
        visible={sheet === 'cancel' && button === 'sent'}
        title={cancelTitle(nickname)}
        body={COPY.cancel.body}
        act={COPY.cancel.act}
        busyLabel={COPY.cancel.busy}
        write={cancelling}
        onAct={() => cancelling.mutate(undefined, { onSuccess: () => setSheet(undefined) })}
        onClose={() => setSheet(undefined)}
        returnFocusTo={self}
      />
      <TakeBackSheet
        visible={sheet === 'remove' && button === 'friend'}
        title={removeTitle(nickname)}
        body={COPY.remove.body}
        act={COPY.remove.act}
        busyLabel={COPY.remove.busy}
        write={removing}
        onAct={() => removing.mutate(undefined, { onSuccess: () => setSheet(undefined) })}
        onClose={() => setSheet(undefined)}
        returnFocusTo={self}
      />
    </>
  );
}

interface TakeBackSheetProps {
  readonly visible: boolean;
  readonly title: string;
  readonly body: string;
  readonly act: string;
  readonly busyLabel: string;
  readonly write: WriteState & { readonly isPending: boolean };
  readonly onAct: () => void;
  readonly onClose: () => void;
  readonly returnFocusTo: FocusTarget;
}

/** *Remove kuba.w as a friend?* — what it does, then the act and **Keep**. */
function TakeBackSheet({
  visible,
  title,
  body,
  act,
  busyLabel,
  write,
  onAct,
  onClose,
  returnFocusTo,
}: TakeBackSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={title}
      closeLabel={COPY.close}
      returnFocusTo={returnFocusTo}
    >
      <Text style={s.body}>{body}</Text>

      <WriteNote writes={[write]} />

      <View style={s.actions}>
        <Button
          label={act}
          size="lg"
          busy={write.isPending}
          busyLabel={busyLabel}
          onPress={onAct}
        />
        <Button label={COPY.keep} variant="secondary" size="lg" onPress={onClose} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  self: { gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
