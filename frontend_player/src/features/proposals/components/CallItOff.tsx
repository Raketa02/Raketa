/**
 * ***Call it off*** — a friends game's sender's, on its details, before the club's cut-off
 * ([#759](https://github.com/Raketa02/Raketa/issues/759); the friends mechanics §11.2; the words
 * §29.10), behind a confirmation:
 *
 * ```
 * Call it off?                                         ✕
 * Everyone is told, nobody pays, and the court goes back to Ogrody 33.
 * [ Call it off for everyone ]
 * [ Keep the game            ]
 * ```
 *
 * **Every hold and cover is let go, nobody pays, and the court goes back to the club**; everybody In
 * and every friend still invited is told (#751). Done, the sheet closes, the toast says so and the
 * details read *Called off*. A refusal — the cut-off came, it is off already — is said in the
 * sheet. The two-way leave sheet, *Leave · the others play on* beside it, is #760's.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { showToast } from '@/shared/store/toast.store';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import { useCallOffFriendsGame } from '../hooks/useFriendsGameWrites';

import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { callOffLine, callOffRefusal } from './friendsGamePresentation';

const COPY = FRIENDS_GAME_COPY.callOff;

export interface CallItOffProps {
  readonly bookingId: string;
  /** The club the court goes back to — absent for one the read no longer names. */
  readonly club: string | undefined;
}

export function CallItOff({ bookingId, club }: CallItOffProps) {
  const [open, setOpen] = useState(false);
  const [refusal, setRefusal] = useState<string>();
  const callOff = useCallOffFriendsGame(bookingId);

  const close = () => {
    if (callOff.isPending) return;
    setOpen(false);
  };

  return (
    <>
      <Button
        label={COPY.action}
        variant="secondary"
        size="lg"
        onPress={() => {
          setRefusal(undefined);
          setOpen(true);
        }}
      />
      <BottomSheet visible={open} onClose={close} title={COPY.title} closeLabel={COPY.close}>
        <View style={s.body} testID="call-off-sheet">
          <Text style={s.line}>{callOffLine(club)}</Text>
          {refusal === undefined ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {refusal}
            </Note>
          )}
          <Button
            label={COPY.confirm}
            variant="dark"
            size="lg"
            busy={callOff.isPending}
            busyLabel={COPY.calling}
            onPress={() => {
              if (callOff.isPending) return;
              setRefusal(undefined);
              callOff.mutate(undefined, {
                onSuccess: () => {
                  setOpen(false);
                  showToast({ message: COPY.done, tone: 'ok' });
                },
                onError: (error) => setRefusal(callOffRefusal(error)),
              });
            }}
          />
          <Button label={COPY.keep} variant="secondary" size="lg" onPress={close} />
        </View>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  line: { ...theme.type.rlLabel, color: theme.color.ink },
});
