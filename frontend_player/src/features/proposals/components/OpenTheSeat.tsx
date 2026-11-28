/**
 * ***Open to {group}*** — the sender's, on an empty seat of a friends game before the cut-off
 * ([#760](https://github.com/Rakieta02/Rakieta/issues/760), over #752's route; the friends mechanics
 * §10.1; the words §29.9), behind a confirmation **that a stranger can then take it**:
 *
 * ```
 * Open this seat to Ogrody?                            ✕
 * Anyone in Ogrody who fits can take it and pay 28 zł.
 * [ Open to Ogrody ]
 * [ Not yet        ]
 * ```
 *
 * **From then on the seat is a rescue**, offered as any rescue is — a *Seat open* card in the decks
 * of members who fit, a row in Fill in's *Seats to fill*, Fill in alerts — and the first to take it
 * pays the share. Done, the sheet closes, the toast says so and the details read *Seat open*. A
 * refusal that leaves nothing to open — the seat taken, the game off or under way, the cut-off come
 * and the seat opened on its own — closes the sheet with its sentence, and the game is read again;
 * any other is said in the sheet.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { showToast } from '@/shared/store/toast.store';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import type { DeckPerson } from '../domain/deck';
import { seatWriteRefusalOf } from '../domain/friendsGame';
import { useOpenASeat } from '../hooks/useFriendsGameWrites';

import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import {
  openRefusal,
  openTheSeatLine,
  openTheSeatTitle,
  openToGroup,
  seatActionSpoken,
  seatOpenedToast,
} from './friendsGamePresentation';

const COPY = FRIENDS_GAME_COPY.open;

export interface OpenTheSeatProps {
  readonly bookingId: string;
  /** The empty seat's name, which the opening is sent under. */
  readonly seatOf: string;
  /** Whose seat it was — the act is named aloud with it. */
  readonly person: DeckPerson;
  readonly group: string | undefined;
  readonly shareGrosze: number;
}

export function OpenTheSeat({ bookingId, seatOf, person, group, shareGrosze }: OpenTheSeatProps) {
  const [open, setOpen] = useState(false);
  const [refusal, setRefusal] = useState<string>();
  const opening = useOpenASeat(bookingId, seatOf);
  const label = openToGroup(group);

  const close = () => {
    if (opening.isPending) return;
    setOpen(false);
  };

  return (
    <>
      <Button
        label={label}
        accessibilityLabel={seatActionSpoken(label, person)}
        variant="onDark"
        size="sm"
        onPress={() => {
          setRefusal(undefined);
          setOpen(true);
        }}
      />
      <BottomSheet
        visible={open}
        onClose={close}
        title={openTheSeatTitle(group)}
        closeLabel={COPY.close}
      >
        <View style={s.body} testID="open-seat-sheet">
          <Text style={s.line}>{openTheSeatLine(group, shareGrosze)}</Text>
          {refusal === undefined ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {refusal}
            </Note>
          )}
          <Button
            label={label}
            variant="dark"
            size="lg"
            busy={opening.isPending}
            busyLabel={COPY.opening}
            onPress={() => {
              if (opening.isPending) return;
              setRefusal(undefined);
              opening.mutate(undefined, {
                onSuccess: () => {
                  setOpen(false);
                  showToast({ message: seatOpenedToast(group), tone: 'ok' });
                },
                onError: (error) => {
                  if (seatWriteRefusalOf(error.code) === 'gone') {
                    setOpen(false);
                    showToast({ message: openRefusal(error), tone: 'bad' });
                  } else {
                    setRefusal(openRefusal(error));
                  }
                },
              });
            }}
          />
          <Button label={COPY.notYet} variant="secondary" size="lg" onPress={close} />
        </View>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  line: { ...theme.type.rlLabel, color: theme.color.ink },
});
